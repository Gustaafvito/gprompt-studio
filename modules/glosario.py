"""Glosario de términos AI — ventana con categorías y acciones clicables.

El contenido vive en data/glosario.json (47 entradas con: titulo, desc,
categoría, acción opcional). Renderiza agrupado por categoría con
buscador, filtro y botón "▶ Probar" en las que mapean a funciones reales
de la app.
"""
import json
import logging
from pathlib import Path

import customtkinter as ctk

from modules.gprompt_window import GPromptWindow
from modules.i18n import tr

logger = logging.getLogger(__name__)

_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "glosario.json"
_cache: dict | None = None


def cargar_glosario() -> dict:
    """Lee data/glosario.json (con caché). Devuelve {'categorias': [...], 'entradas': [...]}."""
    global _cache
    if _cache is not None:
        return _cache
    if not _JSON_PATH.exists():
        logger.warning(f"glosario.json no encontrado en {_JSON_PATH}")
        _cache = {"categorias": [], "entradas": []}
        return _cache
    try:
        with open(_JSON_PATH, "r", encoding="utf-8") as f:
            _cache = json.load(f)
    except Exception as e:
        logger.warning(f"glosario.json no se pudo leer: {e}")
        _cache = {"categorias": [], "entradas": []}
    return _cache


def abrir_glosario(app):
    """Abre la ventana del glosario con buscador, categorías y botón Probar.

    Args:
        app: ArquitectoApp (para resolver acciones con getattr).
    """
    glos = cargar_glosario()
    entradas = glos.get("entradas", [])
    categorias = glos.get("categorias", [])

    if not entradas:
        try:
            app.show_toast("⚠️ data/glosario.json no disponible", "#e67e22")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        return

    is_lt = ctk.get_appearance_mode().lower() == "light"
    bg_card = "#ffffff" if is_lt else "#1a1a2e"
    text_main = "#111827" if is_lt else "#e5e7eb"
    text_muted = "#4b5563" if is_lt else "#9ca3af"
    accent = "#2563eb" if is_lt else "#60a5fa"

    win = GPromptWindow(app)
    win.title(f"📚 Glosario — {len(entradas)} términos")
    win.geometry("880x680")

    # ── Cabecera ──
    header = ctk.CTkFrame(win, height=110, corner_radius=0)
    header.pack(fill="x")
    header.pack_propagate(False)

    fila1 = ctk.CTkFrame(header, fg_color="transparent")
    fila1.pack(fill="x", padx=20, pady=(12, 6))
    ctk.CTkLabel(fila1, text=tr("📚 Glosario de términos AI"),
                 font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
    contador_var = ctk.StringVar(value=f"{len(entradas)} términos")
    ctk.CTkLabel(fila1, textvariable=contador_var, text_color=text_muted).pack(side="left", padx=(10, 0))
    ent_buscar = ctk.CTkEntry(fila1, width=300, placeholder_text=tr("🔍 Buscar término…"))
    ent_buscar.pack(side="right")

    # Fila 2: filtro por categoría
    fila2 = ctk.CTkFrame(header, fg_color="transparent")
    fila2.pack(fill="x", padx=20, pady=(0, 12))
    ctk.CTkLabel(fila2, text=tr("Categoría:"), text_color=text_muted).pack(side="left", padx=(0, 10))

    opciones_cat = ["📚 Todas"] + categorias
    filtro_var = ctk.StringVar(value="📚 Todas")
    seg = ctk.CTkSegmentedButton(
        fila2,
        values=opciones_cat,
        variable=filtro_var,
        command=lambda _v: on_filtro(),
    )
    seg.pack(side="left")

    # ── Scroll de resultados ──
    scroll = ctk.CTkScrollableFrame(win, fg_color=("#f3f4f6" if is_lt else "#0d1117"))
    scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # Estado para debounce
    estado = {"after_id": None}

    # Funciones libres (no son métodos del app) que viven en modules.windows
    _FREE_FUNCS = {"abrir_personajes", "abrir_loras", "abrir_batch", "abrir_lista"}

    def _ejecutar_accion(metodo_nombre: str):
        """Cierra la ventana e invoca la acción asociada al glosario.

        Prueba primero como función libre de modules.windows (pasando app
        como argumento), después como método del app.
        """
        win.destroy()
        try:
            if metodo_nombre in _FREE_FUNCS:
                from modules import windows as _w
                fn = getattr(_w, metodo_nombre, None)
                if not callable(fn):
                    raise AttributeError(f"{metodo_nombre} no existe en modules.windows")
                fn(app)
                return
            fn = getattr(app, metodo_nombre, None)
            if not callable(fn):
                raise AttributeError(f"{metodo_nombre} no es método de ArquitectoApp")
            fn()
        except Exception as e:
            logger.warning(f"Error ejecutando {metodo_nombre}: {e}")
            try:
                app.show_toast(f"❌ '{metodo_nombre}' no disponible: {e}", "#e74c3c")
            except Exception as _e:
                logger.debug(f"[silent] {_e}")

    def _render_card(parent, entrada):
        card = ctk.CTkFrame(parent, fg_color=bg_card, corner_radius=6)
        card.pack(fill="x", padx=4, pady=3)

        fila_top = ctk.CTkFrame(card, fg_color="transparent")
        fila_top.pack(fill="x", padx=12, pady=(8, 0))
        ctk.CTkLabel(
            fila_top, text=entrada["titulo"],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=text_main, anchor="w",
        ).pack(side="left")

        # Botón Probar si hay acción
        accion = entrada.get("accion")
        if accion:
            ctk.CTkButton(
                fila_top, text=tr("▶ Probar"), width=80, height=24,
                fg_color=accent,
                hover_color=("#1d4ed8" if is_lt else "#3b82f6"),
                font=ctk.CTkFont(size=10),
                command=lambda a=accion: _ejecutar_accion(a),
            ).pack(side="right")

        ctk.CTkLabel(
            card, text=entrada["descripcion"],
            text_color=text_muted, anchor="w",
            wraplength=800, justify="left",
            font=ctk.CTkFont(size=10),
        ).pack(fill="x", padx=12, pady=(2, 10))

    import re as _re

    def _clave_orden(titulo: str) -> str:
        """Ignora el emoji inicial al ordenar alfabéticamente."""
        sin_emoji = _re.sub(r"^[^\w]+", "", titulo).strip()
        return sin_emoji.lower()

    def render(filtro_texto: str = ""):
        for w in scroll.winfo_children():
            w.destroy()
        f = filtro_texto.strip().lower()
        cat_sel = filtro_var.get()
        cat_sel_real = None if cat_sel == "📚 Todas" else cat_sel

        # Filtrar
        filtradas: list[dict] = []
        for e in entradas:
            if cat_sel_real and e["categoria"] != cat_sel_real:
                continue
            if f and not (f in e["titulo"].lower() or f in e["descripcion"].lower()):
                continue
            filtradas.append(e)
        n = len(filtradas)

        if cat_sel_real:
            contador_var.set(f"{n} en {cat_sel_real}")
        else:
            contador_var.set(f"{n} de {len(entradas)}" if f else f"{len(entradas)} términos")

        if n == 0:
            ctk.CTkLabel(scroll, text=tr("Sin resultados."), text_color=text_muted,
                         font=ctk.CTkFont(size=14)).pack(pady=40)
            return

        if cat_sel_real:
            # Vista categoría única → solo esa categoría
            ctk.CTkLabel(
                scroll, text=cat_sel_real,
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=accent, anchor="w",
            ).pack(fill="x", padx=4, pady=(14, 4))
            for entrada in sorted(filtradas, key=lambda e: _clave_orden(e["titulo"])):
                _render_card(scroll, entrada)
        else:
            # Vista "Todas" → agrupado por categoría (en orden alfabético del JSON)
            # con cada categoría ordenada alfabéticamente por título.
            por_cat: dict[str, list[dict]] = {}
            for e in filtradas:
                por_cat.setdefault(e["categoria"], []).append(e)
            for cat in categorias:
                if not por_cat.get(cat):
                    continue
                ctk.CTkLabel(
                    scroll, text=cat,
                    font=ctk.CTkFont(size=15, weight="bold"),
                    text_color=accent, anchor="w",
                ).pack(fill="x", padx=4, pady=(14, 4))
                for entrada in sorted(por_cat[cat], key=lambda e: _clave_orden(e["titulo"])):
                    _render_card(scroll, entrada)

    def on_buscar(*_):
        if estado["after_id"]:
            try:
                win.after_cancel(estado["after_id"])
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        estado["after_id"] = win.after(200, lambda: render(ent_buscar.get()))

    def on_filtro():
        render(ent_buscar.get())

    ent_buscar.bind("<KeyRelease>", on_buscar)
    render()
    ent_buscar.focus_set()
