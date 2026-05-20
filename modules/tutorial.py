"""Tutorial interactivo con índice lateral, progreso persistente y "Probar ahora".

El contenido vive en data/tutorial.json (26 pasos). El progreso ("pasos
completados" + "último paso visto") se guarda en preferencias.json bajo
las claves `tutorial_completados` y `tutorial_ultimo_paso`.
"""
import json
import logging
from pathlib import Path

import customtkinter as ctk

from modules.gprompt_window import GPromptWindow

logger = logging.getLogger(__name__)

_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "tutorial.json"
_cache: dict | None = None


def cargar_tutorial() -> dict:
    """Lee data/tutorial.json (con caché)."""
    global _cache
    if _cache is not None:
        return _cache
    if not _JSON_PATH.exists():
        logger.warning(f"tutorial.json no encontrado en {_JSON_PATH}")
        _cache = {"pasos": []}
        return _cache
    try:
        with open(_JSON_PATH, "r", encoding="utf-8") as f:
            _cache = json.load(f)
    except Exception as e:
        logger.warning(f"tutorial.json no se pudo leer: {e}")
        _cache = {"pasos": []}
    return _cache


def _cargar_progreso(app) -> tuple[set[int], int]:
    """Devuelve (set de pasos completados, último paso visto). 1-indexed."""
    try:
        prefs = app.store.cargar_preferencias() or {}
        completados = set(int(x) for x in prefs.get("tutorial_completados", []))
        ultimo = int(prefs.get("tutorial_ultimo_paso", 1))
        return completados, ultimo
    except Exception as e:
        logger.debug(f"_cargar_progreso falló: {e}")
        return set(), 1


def _guardar_progreso(app, completados: set[int], ultimo: int):
    try:
        prefs = app.store.cargar_preferencias() or {}
        prefs["tutorial_completados"] = sorted(completados)
        prefs["tutorial_ultimo_paso"] = ultimo
        app.store.guardar_preferencias(prefs)
    except Exception as e:
        logger.debug(f"_guardar_progreso falló: {e}")


def abrir_tutorial(app):
    """Abre el tutorial interactivo con índice lateral + progreso + Probar."""
    tut = cargar_tutorial()
    pasos = tut.get("pasos", [])
    if not pasos:
        try:
            app.show_toast("⚠️ data/tutorial.json no disponible", "#e67e22")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        return

    total = len(pasos)
    completados, ultimo = _cargar_progreso(app)
    # 0-indexed
    idx = max(0, min(ultimo - 1, total - 1))

    is_lt = ctk.get_appearance_mode().lower() == "light"
    bg_card = "#ffffff" if is_lt else "#1a1a2e"
    bg_idx_inactive = "#f3f4f6" if is_lt else "#0f1318"
    bg_idx_active = ("#dbeafe" if is_lt else "#1e3a5f")
    bg_idx_done = ("#dcfce7" if is_lt else "#14532d")
    text_main = "#111827" if is_lt else "#e5e7eb"
    text_muted = "#4b5563" if is_lt else "#9ca3af"
    accent = "#2563eb" if is_lt else "#60a5fa"
    success = "#16a34a" if is_lt else "#22c55e"

    win = GPromptWindow(app)
    win.title(f"📚 Tutorial — {len(completados)}/{total} pasos")
    win.geometry("980x600")

    # ── Layout: índice lateral + contenido ──
    contenedor = ctk.CTkFrame(win, fg_color="transparent")
    contenedor.pack(fill="both", expand=True, padx=10, pady=10)

    # Índice lateral
    idx_frame = ctk.CTkScrollableFrame(contenedor, fg_color=bg_idx_inactive,
                                       corner_radius=8, width=280)
    idx_frame.pack(side="left", fill="y", padx=(0, 10))

    ctk.CTkLabel(idx_frame, text="📋 Pasos",
                 font=ctk.CTkFont(size=14, weight="bold"),
                 text_color=text_main).pack(anchor="w", padx=10, pady=(8, 4))

    # Progress general
    progreso_global = ctk.CTkProgressBar(idx_frame, height=8, progress_color=success)
    progreso_global.pack(fill="x", padx=10, pady=(0, 4))
    progreso_global.set(len(completados) / total if total else 0)
    lbl_progreso = ctk.CTkLabel(idx_frame, text=f"{len(completados)}/{total} completados",
                                font=ctk.CTkFont(size=10), text_color=text_muted)
    lbl_progreso.pack(anchor="w", padx=10, pady=(0, 8))

    btns_idx: list[ctk.CTkButton] = []

    # Contenido principal
    main = ctk.CTkFrame(contenedor, fg_color="transparent")
    main.pack(side="left", fill="both", expand=True)

    # Cabecera con barra de progreso del paso actual
    head = ctk.CTkFrame(main, fg_color="transparent")
    head.pack(fill="x")
    lbl_paso = ctk.CTkLabel(head, text="", font=ctk.CTkFont(size=12),
                            text_color=text_muted)
    lbl_paso.pack(side="left")
    bar_paso = ctk.CTkProgressBar(head, width=200, height=6, progress_color=accent)
    bar_paso.pack(side="right", padx=10)

    # Card del paso
    card = ctk.CTkFrame(main, fg_color=bg_card, corner_radius=8)
    card.pack(fill="both", expand=True, pady=(8, 0))

    lbl_titulo = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=16, weight="bold"),
                              text_color=text_main, anchor="w", wraplength=600,
                              justify="left")
    lbl_titulo.pack(anchor="w", padx=14, pady=(12, 4))

    txt_desc = ctk.CTkTextbox(card, wrap="word", font=ctk.CTkFont(size=11),
                              fg_color=bg_card, text_color=text_muted,
                              border_width=0, height=300)
    txt_desc.pack(fill="both", expand=True, padx=14, pady=(0, 8))

    # Botones de acción
    acciones = ctk.CTkFrame(main, fg_color="transparent")
    acciones.pack(fill="x", pady=(8, 0))

    btn_probar = ctk.CTkButton(acciones, text="▶ Probar ahora", width=140, height=32,
                               fg_color=accent,
                               hover_color=("#1d4ed8" if is_lt else "#3b82f6"))
    btn_probar.pack(side="left")

    btn_completado_var = ctk.BooleanVar(value=False)
    chk_completado = ctk.CTkCheckBox(acciones, text="✅ Marcar como completado",
                                     variable=btn_completado_var,
                                     command=lambda: on_toggle_completado())
    chk_completado.pack(side="left", padx=14)

    # Navegación
    nav = ctk.CTkFrame(acciones, fg_color="transparent")
    nav.pack(side="right")
    btn_ant = ctk.CTkButton(nav, text="⬅ Anterior", width=100, height=32)
    btn_ant.pack(side="left", padx=4)
    btn_sig = ctk.CTkButton(nav, text="Siguiente ➡", width=100, height=32)
    btn_sig.pack(side="left", padx=4)
    btn_close = ctk.CTkButton(nav, text="Cerrar", width=80, height=32,
                              fg_color="#444", hover_color="#555",
                              command=win.destroy)
    btn_close.pack(side="left", padx=4)

    def actualizar_indice():
        # Re-pintar todos los botones del índice según estado
        for i, btn in enumerate(btns_idx):
            paso_n = i + 1
            if paso_n == idx + 1:
                btn.configure(fg_color=bg_idx_active, text_color=accent)
            elif paso_n in completados:
                btn.configure(fg_color=bg_idx_done, text_color=success)
            else:
                btn.configure(fg_color=bg_idx_inactive, text_color=text_main)

        # Progreso global
        progreso_global.set(len(completados) / total if total else 0)
        lbl_progreso.configure(text=f"{len(completados)}/{total} completados")
        win.title(f"📚 Tutorial — {len(completados)}/{total} pasos")

    def mostrar_paso():
        paso = pasos[idx]
        lbl_paso.configure(text=f"Paso {paso['id']}/{total}  ·  "
                                f"{int((idx + 1) / total * 100)}%")
        bar_paso.set((idx + 1) / total)
        lbl_titulo.configure(text=paso["titulo"])
        txt_desc.configure(state="normal")
        txt_desc.delete("1.0", "end")
        txt_desc.insert("1.0", paso["descripcion"])
        txt_desc.configure(state="disabled")

        # Probar
        accion = paso.get("accion")
        if accion:
            btn_probar.configure(state="normal", text="▶ Probar ahora",
                                 command=lambda a=accion: _probar(a))
        else:
            btn_probar.configure(state="disabled", text="—")

        # Completado
        btn_completado_var.set((idx + 1) in completados)

        # Nav
        btn_ant.configure(state="normal" if idx > 0 else "disabled")
        btn_sig.configure(state="normal" if idx < total - 1 else "disabled")

        actualizar_indice()

        # Persistir último paso visto
        _guardar_progreso(app, completados, idx + 1)

    _FREE_FUNCS = {"abrir_personajes", "abrir_loras", "abrir_batch", "abrir_lista"}

    def _probar(metodo_nombre: str):
        """Ejecuta la acción del paso actual.

        Prueba primero como función libre de modules.windows (pasando app),
        después como método del app.
        """
        try:
            if metodo_nombre in _FREE_FUNCS:
                from modules import windows as _w
                fn = getattr(_w, metodo_nombre, None)
                if not callable(fn):
                    raise AttributeError(f"{metodo_nombre} no existe en modules.windows")
                fn(app)
            else:
                fn = getattr(app, metodo_nombre, None)
                if not callable(fn):
                    raise AttributeError(f"{metodo_nombre} no es método de ArquitectoApp")
                fn()
            # Marcar el paso como completado al probarlo con éxito
            completados.add(idx + 1)
            btn_completado_var.set(True)
            actualizar_indice()
            _guardar_progreso(app, completados, idx + 1)
        except Exception as e:
            logger.warning(f"Error ejecutando {metodo_nombre}: {e}")
            try:
                app.show_toast(f"❌ '{metodo_nombre}' no disponible: {e}", "#e74c3c")
            except Exception as _e:
                logger.debug(f"[silent] {_e}")

    def on_toggle_completado():
        if btn_completado_var.get():
            completados.add(idx + 1)
        else:
            completados.discard(idx + 1)
        _guardar_progreso(app, completados, idx + 1)
        actualizar_indice()

    def ir_a(nuevo_idx: int):
        nonlocal idx
        idx = max(0, min(nuevo_idx, total - 1))
        mostrar_paso()

    btn_ant.configure(command=lambda: ir_a(idx - 1))
    btn_sig.configure(command=lambda: ir_a(idx + 1))

    # Botones del índice
    for paso in pasos:
        # Truncar título largo
        t = paso["titulo"]
        if len(t) > 40:
            t = t[:38] + "…"
        btn = ctk.CTkButton(
            idx_frame, text=t, height=28, anchor="w",
            fg_color=bg_idx_inactive, text_color=text_main,
            hover_color=bg_idx_active,
            font=ctk.CTkFont(size=10),
            command=lambda p=paso["id"]: ir_a(p - 1),
        )
        btn.pack(fill="x", padx=6, pady=1)
        btns_idx.append(btn)

    mostrar_paso()
