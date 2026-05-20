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


def abrir_guia_estilos(app):
    """Abre una ventana con la guía completa + buscador.

    Args:
        app: ArquitectoApp (para parentar la ventana correctamente).
    """
    guia = cargar_guia()
    if not guia:
        try:
            app.show_toast("⚠️ GUIA_ESTILOS.md no disponible", "#e67e22")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        return

    is_lt = ctk.get_appearance_mode().lower() == "light"
    bg_card = "#ffffff" if is_lt else "#1a1a2e"
    text_main = "#111827" if is_lt else "#e5e7eb"
    text_muted = "#4b5563" if is_lt else "#9ca3af"
    accent = "#2563eb" if is_lt else "#60a5fa"

    win = GPromptWindow(app)
    win.title(f"📖 Guía de estilos ({len(guia)} estilos)")
    win.geometry("900x650")

    # Cabecera con buscador
    header = ctk.CTkFrame(win, height=60, corner_radius=0)
    header.pack(fill="x")
    header.pack_propagate(False)

    ctk.CTkLabel(
        header,
        text="📖 Guía de estilos",
        font=ctk.CTkFont(size=18, weight="bold"),
    ).pack(side="left", padx=(20, 10), pady=15)

    contador_var = ctk.StringVar(value=f"{len(guia)} estilos")
    ctk.CTkLabel(header, textvariable=contador_var, text_color=text_muted).pack(side="left", pady=15)

    ent_buscar = ctk.CTkEntry(header, width=300, placeholder_text="🔍 Buscar por nombre, grupo, descripción…")
    ent_buscar.pack(side="right", padx=20, pady=15)

    # Área scrollable con resultados
    scroll = ctk.CTkScrollableFrame(win, fg_color=("#f3f4f6" if is_lt else "#0d1117"))
    scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def render(filtro: str = ""):
        for w in scroll.winfo_children():
            w.destroy()
        f = filtro.strip().lower()
        # Agrupar por grupo
        por_grupo: dict[str, list[tuple[str, dict]]] = {}
        n = 0
        for nombre, d in guia.items():
            if f and not (
                f in nombre.lower()
                or f in d["grupo"].lower()
                or f in d["descripcion"].lower()
                or f in d["ejemplo"].lower()
            ):
                continue
            por_grupo.setdefault(d["grupo"], []).append((nombre, d))
            n += 1
        contador_var.set(f"{n} estilos" if not f else f"{n} de {len(guia)}")

        if n == 0:
            ctk.CTkLabel(scroll, text="Sin resultados.", text_color=text_muted, font=ctk.CTkFont(size=14)).pack(pady=40)
            return

        for grupo in por_grupo:
            ctk.CTkLabel(
                scroll,
                text=grupo,
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=accent,
                anchor="w",
            ).pack(fill="x", padx=4, pady=(14, 4))

            for nombre, d in por_grupo[grupo]:
                card = ctk.CTkFrame(scroll, fg_color=bg_card, corner_radius=6)
                card.pack(fill="x", padx=4, pady=2)
                ctk.CTkLabel(
                    card,
                    text=nombre,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=text_main,
                    anchor="w",
                ).pack(fill="x", padx=10, pady=(6, 0))
                if d["descripcion"]:
                    ctk.CTkLabel(
                        card,
                        text=d["descripcion"],
                        text_color=text_muted,
                        anchor="w",
                        wraplength=820,
                        justify="left",
                    ).pack(fill="x", padx=10)
                if d["ejemplo"]:
                    ctk.CTkLabel(
                        card,
                        text=f"📷 {d['ejemplo']}",
                        text_color=accent,
                        font=ctk.CTkFont(size=10, slant="italic"),
                        anchor="w",
                        wraplength=820,
                        justify="left",
                    ).pack(fill="x", padx=10, pady=(0, 6))

    def on_buscar(*_):
        render(ent_buscar.get())

    ent_buscar.bind("<KeyRelease>", on_buscar)
    render()
    ent_buscar.focus_set()
