"""Parser de GUIA_ESTILOS.md + ventana de consulta.

Convierte el Markdown en un dict {nombre: {grupo, descripcion, ejemplo}}
y lo expone tanto para tooltips (modules.ui_builders) como para una
ventana de búsqueda con buscador (abrir_guia_estilos).
"""
import logging
import re
from pathlib import Path

import customtkinter as ctk

from modules.gprompt_window import GPromptWindow

logger = logging.getLogger(__name__)

_MD_PATH = Path(__file__).resolve().parent.parent / "GUIA_ESTILOS.md"
_cache: dict | None = None
_modos_cache: dict | None = None  # {nombre_estilo: frozenset({"imagen","video","audio"})}


def cargar_guia() -> dict[str, dict]:
    """Lee GUIA_ESTILOS.md y devuelve {nombre_estilo: {grupo, descripcion, ejemplo}}.

    Cachea el resultado tras la primera llamada. Si el archivo no existe
    o no se puede parsear devuelve dict vacío y loggea warning.
    """
    global _cache
    if _cache is not None:
        return _cache

    if not _MD_PATH.exists():
        logger.warning(f"GUIA_ESTILOS.md no encontrado en {_MD_PATH}")
        _cache = {}
        return _cache

    try:
        md = _MD_PATH.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"GUIA_ESTILOS.md no se pudo leer: {e}")
        _cache = {}
        return _cache

    guia: dict[str, dict] = {}
    grupo_actual: str | None = None
    for line in md.split("\n"):
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            grupo_actual = m.group(1).strip()
            continue
        if line.startswith("|") and grupo_actual:
            if line.startswith("|---") or "| Estilo |" in line:
                continue
            parts = [c.strip() for c in line.split("|")]
            if len(parts) >= 4 and parts[1] and not parts[1].startswith("-"):
                nombre = parts[1]
                guia[nombre] = {
                    "grupo": grupo_actual,
                    "descripcion": parts[2] if len(parts) > 2 else "",
                    "ejemplo": parts[3] if len(parts) > 3 else "",
                }

    logger.debug(f"Guía de estilos cargada: {len(guia)} estilos en {len(set(v['grupo'] for v in guia.values()))} grupos")
    _cache = guia
    return _cache


def _construir_modos_cache() -> dict[str, frozenset]:
    """Devuelve {nombre_guia: {modos en los que aparece}}.

    Mira ESTILOS_IMAGEN, ESTILOS_VIDEO, ESTILOS_AUDIO de config y
    busca cada entrada de la guía con `buscar_estilo` reverse — es
    decir, para cada estilo del catálogo de un modo, comprueba si
    está en la guía y le añade ese modo al set.
    """
    global _modos_cache
    if _modos_cache is not None:
        return _modos_cache

    try:
        import config
    except Exception as e:
        logger.warning(f"No se pudo importar config para clasificar modos: {e}")
        _modos_cache = {}
        return _modos_cache

    guia = cargar_guia()
    modos_de: dict[str, set] = {nombre: set() for nombre in guia}

    fuentes = (
        ("imagen", getattr(config, "ESTILOS_IMAGEN", [])),
        ("video",  getattr(config, "ESTILOS_VIDEO", [])),
        ("audio",  getattr(config, "ESTILOS_AUDIO", [])),
    )
    for modo, lista in fuentes:
        for estilo in lista:
            d = buscar_estilo(estilo)
            if d is None:
                continue
            # Encontrar la clave canónica del MD para este estilo
            # (buscar_estilo nos da el dict, no el nombre; hacemos lookup inverso)
            for k, v in guia.items():
                if v is d:
                    modos_de[k].add(modo)
                    break

    _modos_cache = {k: frozenset(v) for k, v in modos_de.items()}
    return _modos_cache


def modos_de_estilo(nombre: str) -> frozenset:
    """Devuelve los modos ({'imagen','video','audio'}) en los que aparece
    un estilo. Frozen-set vacío si no se encuentra o si la guía no
    cubre ese modo para ese estilo.
    """
    cache = _construir_modos_cache()
    if nombre in cache:
        return cache[nombre]
    # Match permisivo: buscar por similitud
    d = buscar_estilo(nombre)
    if d is None:
        return frozenset()
    for k, v in cargar_guia().items():
        if v is d:
            return cache.get(k, frozenset())
    return frozenset()


def buscar_estilo(nombre: str) -> dict | None:
    """Devuelve el dict de un estilo, o None si no está.

    Hace match exacto y, si no, intenta match permisivo (sin / ni espacios).
    """
    g = cargar_guia()
    if nombre in g:
        return g[nombre]
    # Match permisivo: normalizar
    norm = _normalizar(nombre)
    for k, v in g.items():
        if _normalizar(k) == norm:
            return v
    # Match parcial: si el nombre del estilo en la app es un sub-string
    # del nombre del MD (p.ej. "Polaroid" vs "Polaroid / Vintage Photo")
    for k, v in g.items():
        partes_md = [p.strip() for p in re.split(r"[/]", k)]
        for p in partes_md:
            if _normalizar(p) == norm:
                return v
    return None


def _normalizar(s: str) -> str:
    return re.sub(r"[\s/\-_]+", "", s).lower()


def tooltip_para(nombre: str) -> str:
    """Texto compacto para mostrar en tooltip. '' si no hay info."""
    d = buscar_estilo(nombre)
    if not d:
        return ""
    desc = d.get("descripcion") or ""
    ej = d.get("ejemplo") or ""
    if desc and ej:
        return f"{desc}\n📷 {ej}"
    return desc or ej


_FILTRO_LABELS = {
    "todos":  "📖 Todos",
    "imagen": "🖼 Imagen",
    "video":  "🎬 Vídeo",
    "audio":  "🎵 Audio",
}


def abrir_guia_estilos(app, modo_inicial: str | None = None):
    """Abre una ventana con la guía completa + buscador + filtro por modo.

    Args:
        app: ArquitectoApp (para parentar la ventana correctamente).
        modo_inicial: si es "imagen"/"video"/"audio", el filtro se
            preselecciona en ese modo. Si es None o "todos", muestra todo.
    """
    guia = cargar_guia()
    if not guia:
        try:
            app.show_toast("⚠️ GUIA_ESTILOS.md no disponible", "#e67e22")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        return

    # Pre-construir el cache de modos (puede tardar un instante la primera vez)
    _construir_modos_cache()

    is_lt = ctk.get_appearance_mode().lower() == "light"
    bg_card = "#ffffff" if is_lt else "#1a1a2e"
    text_main = "#111827" if is_lt else "#e5e7eb"
    text_muted = "#4b5563" if is_lt else "#9ca3af"
    accent = "#2563eb" if is_lt else "#60a5fa"

    win = GPromptWindow(app)
    win.title(f"📖 Guía de estilos ({len(guia)} estilos)")
    win.geometry("900x680")

    # ── Cabecera ─────────────────────────────────────────────
    header = ctk.CTkFrame(win, height=110, corner_radius=0)
    header.pack(fill="x")
    header.pack_propagate(False)

    # Fila 1: título + buscador
    fila1 = ctk.CTkFrame(header, fg_color="transparent")
    fila1.pack(fill="x", padx=20, pady=(12, 6))
    ctk.CTkLabel(
        fila1,
        text="📖 Guía de estilos",
        font=ctk.CTkFont(size=18, weight="bold"),
    ).pack(side="left")
    contador_var = ctk.StringVar(value=f"{len(guia)} estilos")
    ctk.CTkLabel(fila1, textvariable=contador_var, text_color=text_muted).pack(side="left", padx=(10, 0))
    ent_buscar = ctk.CTkEntry(fila1, width=300, placeholder_text="🔍 Buscar por nombre, grupo, descripción…")
    ent_buscar.pack(side="right")

    # Fila 2: filtro por modo (segmented button)
    fila2 = ctk.CTkFrame(header, fg_color="transparent")
    fila2.pack(fill="x", padx=20, pady=(0, 12))
    ctk.CTkLabel(fila2, text="Filtrar por modo:", text_color=text_muted).pack(side="left", padx=(0, 10))

    # Normalizar modo_inicial
    modo_seleccionado = (modo_inicial or "todos").lower()
    if modo_seleccionado not in _FILTRO_LABELS:
        modo_seleccionado = "todos"

    filtro_var = ctk.StringVar(value=_FILTRO_LABELS[modo_seleccionado])
    seg = ctk.CTkSegmentedButton(
        fila2,
        values=list(_FILTRO_LABELS.values()),
        variable=filtro_var,
        command=lambda _v: on_filtro(),
    )
    seg.pack(side="left")

    # ── Scroll con resultados ───────────────────────────────
    scroll = ctk.CTkScrollableFrame(win, fg_color=("#f3f4f6" if is_lt else "#0d1117"))
    scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _modo_actual() -> str:
        label = filtro_var.get()
        for k, v in _FILTRO_LABELS.items():
            if v == label:
                return k
        return "todos"

    # Estado para paginación y debounce del buscador
    PAGE_SIZE = 60
    estado = {"visible": PAGE_SIZE, "after_id": None}

    def _render_card(parent, nombre, d, modos_cache):
        modos_estilo = modos_cache.get(nombre, frozenset())
        badge_text = " ".join(
            {"imagen": "🖼", "video": "🎬", "audio": "🎵"}[m]
            for m in ("imagen", "video", "audio") if m in modos_estilo
        )
        card = ctk.CTkFrame(parent, fg_color=bg_card, corner_radius=6)
        card.pack(fill="x", padx=4, pady=2)

        fila_top = ctk.CTkFrame(card, fg_color="transparent")
        fila_top.pack(fill="x", padx=10, pady=(6, 0))
        ctk.CTkLabel(
            fila_top, text=nombre, font=ctk.CTkFont(size=12, weight="bold"),
            text_color=text_main, anchor="w",
        ).pack(side="left")
        if badge_text:
            ctk.CTkLabel(
                fila_top, text=badge_text, text_color=text_muted,
                font=ctk.CTkFont(size=11),
            ).pack(side="right")

        if d["descripcion"]:
            ctk.CTkLabel(
                card, text=d["descripcion"], text_color=text_muted,
                anchor="w", wraplength=820, justify="left",
            ).pack(fill="x", padx=10)
        if d["ejemplo"]:
            ctk.CTkLabel(
                card, text=f"📷 {d['ejemplo']}", text_color=accent,
                font=ctk.CTkFont(size=10, slant="italic"),
                anchor="w", wraplength=820, justify="left",
            ).pack(fill="x", padx=10, pady=(0, 6))

    def render(filtro: str = "", reset_paginacion: bool = True):
        if reset_paginacion:
            estado["visible"] = PAGE_SIZE
        for w in scroll.winfo_children():
            w.destroy()
        f = filtro.strip().lower()
        modo = _modo_actual()
        modos_cache = _construir_modos_cache()

        # Filtrado completo (rápido, solo iteración sobre dict)
        resultados: list[tuple[str, dict]] = []
        total_modo = 0
        for nombre, d in guia.items():
            if modo != "todos":
                if modo not in modos_cache.get(nombre, frozenset()):
                    continue
            total_modo += 1
            if f and not (
                f in nombre.lower()
                or f in d["grupo"].lower()
                or f in d["descripcion"].lower()
                or f in d["ejemplo"].lower()
            ):
                continue
            resultados.append((nombre, d))

        total = len(resultados)
        if modo == "todos":
            contador_var.set(f"{total} de {len(guia)}" if f else f"{len(guia)} estilos")
        else:
            etiqueta = _FILTRO_LABELS[modo]
            contador_var.set(
                f"{total} de {total_modo} en {etiqueta}" if f else f"{total_modo} en {etiqueta}"
            )

        if total == 0:
            msg = "Sin resultados." if f else f"No hay estilos en la guía para {_FILTRO_LABELS[modo]}."
            ctk.CTkLabel(scroll, text=msg, text_color=text_muted, font=ctk.CTkFont(size=14)).pack(pady=40)
            return

        # Página visible
        visibles = min(estado["visible"], total)
        sublista = resultados[:visibles]

        # Renderizar agrupado por grupo
        por_grupo: dict[str, list[tuple[str, dict]]] = {}
        for nombre, d in sublista:
            por_grupo.setdefault(d["grupo"], []).append((nombre, d))

        for grupo in por_grupo:
            ctk.CTkLabel(
                scroll, text=grupo, font=ctk.CTkFont(size=15, weight="bold"),
                text_color=accent, anchor="w",
            ).pack(fill="x", padx=4, pady=(14, 4))
            for nombre, d in por_grupo[grupo]:
                _render_card(scroll, nombre, d, modos_cache)

        # Botón "Mostrar más" si quedan resultados sin pintar
        restantes = total - visibles
        if restantes > 0:
            def _mostrar_mas():
                estado["visible"] += PAGE_SIZE
                render(ent_buscar.get(), reset_paginacion=False)
            ctk.CTkButton(
                scroll,
                text=f"▼ Mostrar {min(PAGE_SIZE, restantes)} más  ({restantes} restantes)",
                command=_mostrar_mas,
                height=34,
                fg_color=accent,
                hover_color=("#1d4ed8" if is_lt else "#3b82f6"),
            ).pack(fill="x", padx=4, pady=(14, 6))

    # ── Debounce del buscador ──────────────────────────────
    def on_buscar(*_):
        # Cancelar render pendiente y reprogramar (200ms tras dejar de escribir)
        if estado["after_id"]:
            try:
                win.after_cancel(estado["after_id"])
            except Exception as _e:
                logger.debug(f"[silent] after_cancel: {_e}")
        estado["after_id"] = win.after(200, lambda: render(ent_buscar.get()))

    def on_filtro():
        render(ent_buscar.get())

    ent_buscar.bind("<KeyRelease>", on_buscar)
    render()
    ent_buscar.focus_set()
