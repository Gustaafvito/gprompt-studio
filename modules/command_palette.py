"""Command palette (Ctrl+K) — buscador universal de acciones de la app.

Con ~100 funciones repartidas en 8 menús, encontrar una herramienta
concreta exige memoria. El palette indexa automáticamente TODOS los items
de los menús del header (app._paleta_comandos, registrado al construirlos
en ui_builders) más las acciones principales, y los filtra al teclear.

Interacción: Ctrl+K abre · teclear filtra · ↑/↓ selecciona · Enter
ejecuta · Escape o clic fuera cierra.

Implementación: Toplevel PLANO de tkinter con widgets CTk dentro y
grab_set modal (mismo patrón robusto que searchable_dropdown — un
CTkToplevel con overrideredirect en Windows a veces no renderiza).
"""
import logging
import tkinter

import customtkinter as ctk

from modules import paleta as P
from modules.i18n import tr

logger = logging.getLogger("gprompt")

MAX_RESULTADOS = 14


def filtrar_comandos(comandos, filtro):
    """Filtra (grupo, label, cmd) — todas las palabras del filtro deben
    aparecer en el label o en el grupo (case-insensitive, sin orden)."""
    f = (filtro or "").strip().lower()
    if not f:
        return list(comandos)
    palabras = f.split()
    return [c for c in comandos
            if all(p in f"{c[0]} {c[1]}".lower() for p in palabras)]


def abrir_command_palette(app):
    """Abre el palette centrado sobre la ventana principal."""
    comandos = list(getattr(app, "_paleta_comandos", []))
    if not comandos:
        return
    # Toggle: si ya hay uno abierto, cerrarlo.
    previo = getattr(app, "_palette_popup", None)
    if previo is not None:
        try:
            if previo.winfo_exists():
                previo.destroy()
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        app._palette_popup = None
        return

    is_lt = ctk.get_appearance_mode().lower() == "light"
    ancho, alto = 560, 460
    try:
        x = app.winfo_rootx() + (app.winfo_width() - ancho) // 2
        y = app.winfo_rooty() + 100
    except Exception:
        x, y = 200, 150

    top = tkinter.Toplevel(app)
    app._palette_popup = top
    top.wm_overrideredirect(True)
    try:
        top.transient(app)
        top.attributes("-topmost", True)
    except Exception as _e:
        logger.debug(f"[silent] {_e}")
    top.geometry(f"{ancho}x{alto}+{x}+{y}")
    top.configure(bg="#2b2b2b")

    cont = ctk.CTkFrame(top, corner_radius=10,
                        border_width=2, border_color=P.BTN_PRIMARIO)
    cont.pack(fill="both", expand=True)

    estado = {"sel": 0, "visibles": []}

    def _cerrar():
        app._palette_popup = None
        try:
            top.grab_release()
        except Exception:
            pass
        try:
            top.destroy()
        except Exception:
            pass

    def _ejecutar(cmd):
        _cerrar()
        # Diferido: que el popup termine de cerrarse antes de abrir ventanas.
        try:
            app.after(60, cmd)
        except Exception as e:
            logger.debug(f"[silent palette exec] {e}")

    buscar_var = tkinter.StringVar()
    entry = ctk.CTkEntry(cont, textvariable=buscar_var, height=36,
                         font=ctk.CTkFont(size=P.FUENTE_SECCION),
                         placeholder_text=tr("Escribe una acción…  (↑↓ navegar · Enter ejecutar · Esc cerrar)"))
    entry.pack(fill="x", padx=10, pady=(10, 6))

    lista = ctk.CTkScrollableFrame(cont, fg_color="transparent")
    lista.pack(fill="both", expand=True, padx=6, pady=(0, 8))

    color_sel = "#dbeafe" if is_lt else "#1a3a5a"
    color_grupo = P.TXT_MUTED_OSCURO if is_lt else P.TXT_MUTED

    def _repintar(*_):
        for w in lista.winfo_children():
            w.destroy()
        visibles = filtrar_comandos(comandos, buscar_var.get())[:MAX_RESULTADOS]
        estado["visibles"] = visibles
        estado["sel"] = min(estado["sel"], max(len(visibles) - 1, 0))
        if not visibles:
            ctk.CTkLabel(lista, text=tr("(sin coincidencias)"),
                         font=ctk.CTkFont(size=P.FUENTE_CUERPO),
                         text_color=color_grupo).pack(pady=14)
            return
        for i, (grupo, label, cmd) in enumerate(visibles):
            fila = ctk.CTkFrame(
                lista, corner_radius=6,
                fg_color=color_sel if i == estado["sel"] else "transparent")
            fila.pack(fill="x", padx=2, pady=1)
            ctk.CTkLabel(fila, text=f"  {label}",
                         font=ctk.CTkFont(size=P.FUENTE_CUERPO),
                         anchor="w").pack(side="left", fill="x",
                                          expand=True, padx=4, pady=4)
            ctk.CTkLabel(fila, text=f"{grupo}  ",
                         font=ctk.CTkFont(size=P.FUENTE_HINT),
                         text_color=color_grupo,
                         anchor="e").pack(side="right", padx=4)
            for w in (fila, *fila.winfo_children()):
                w.bind("<Button-1>", lambda e, c=cmd: _ejecutar(c))

    def _mover(delta):
        n = len(estado["visibles"])
        if n:
            estado["sel"] = (estado["sel"] + delta) % n
            _repintar()
        return "break"

    def _enter(_e=None):
        vis = estado["visibles"]
        if vis:
            _ejecutar(vis[estado["sel"]][2])
        return "break"

    def _al_teclear(*_):
        estado["sel"] = 0
        _repintar()

    buscar_var.trace_add("write", _al_teclear)
    entry.bind("<Down>", lambda e: _mover(1))
    entry.bind("<Up>", lambda e: _mover(-1))
    entry.bind("<Return>", _enter)
    top.bind("<Escape>", lambda e: _cerrar())

    def _on_click(e):
        # Con grab_set los clics de toda la pantalla llegan aquí: si el
        # clic cae fuera del popup, cerrar.
        rx, ry = top.winfo_rootx(), top.winfo_rooty()
        if not (rx <= e.x_root <= rx + top.winfo_width()
                and ry <= e.y_root <= ry + top.winfo_height()):
            _cerrar()

    top.bind("<Button-1>", _on_click, add="+")

    _repintar()
    top.update_idletasks()
    top.lift()
    entry.focus_set()
    try:
        top.grab_set()
    except Exception as _e:
        logger.debug(f"[silent] {_e}")
