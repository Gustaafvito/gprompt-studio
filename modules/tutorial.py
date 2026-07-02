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
from modules.i18n import get_idioma, tr

logger = logging.getLogger(__name__)

_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "tutorial.json"
_cache: dict | None = None


def _ruta_idioma() -> Path:
    """data/tutorial.en.json si idioma=='en' y existe; si no, el ES."""
    if get_idioma() == "en":
        en = _JSON_PATH.with_name("tutorial.en.json")
        if en.exists():
            return en
    return _JSON_PATH


def cargar_tutorial() -> dict:
    """Lee data/tutorial(.en).json (con caché)."""
    global _cache
    if _cache is not None:
        return _cache
    ruta = _ruta_idioma()
    if not ruta.exists():
        logger.warning(f"tutorial.json no encontrado en {ruta}")
        _cache = {"pasos": []}
        return _cache
    try:
        with open(ruta, "r", encoding="utf-8") as f:
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
    win.title(tr('📚 Tutorial — {0}/{1} pasos').format((len(completados)), (total)))
    win.geometry("980x600")

    # ── Layout: índice lateral + contenido ──
    contenedor = ctk.CTkFrame(win, fg_color="transparent")
    contenedor.pack(fill="both", expand=True, padx=10, pady=10)

    # Índice lateral
    idx_frame = ctk.CTkScrollableFrame(contenedor, fg_color=bg_idx_inactive,
                                       corner_radius=8, width=280)
    idx_frame.pack(side="left", fill="y", padx=(0, 10))

    ctk.CTkLabel(idx_frame, text=tr("📋 Pasos"),
                 font=ctk.CTkFont(size=14, weight="bold"),
                 text_color=text_main).pack(anchor="w", padx=10, pady=(8, 4))

    # Progress general
    progreso_global = ctk.CTkProgressBar(idx_frame, height=8, progress_color=success)
    progreso_global.pack(fill="x", padx=10, pady=(0, 4))
    progreso_global.set(len(completados) / total if total else 0)
    lbl_progreso = ctk.CTkLabel(idx_frame, text=tr('{0}/{1} completados').format((len(completados)), (total)),
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

    btn_probar = ctk.CTkButton(acciones, text=tr("▶ Probar ahora"), width=140, height=32,
                               fg_color=accent,
                               hover_color=("#1d4ed8" if is_lt else "#3b82f6"))
    btn_probar.pack(side="left")

    btn_completado_var = ctk.BooleanVar(value=False)
    chk_completado = ctk.CTkCheckBox(acciones, text=tr("✅ Marcar como completado"),
                                     variable=btn_completado_var,
                                     command=lambda: on_toggle_completado())
    chk_completado.pack(side="left", padx=14)

    # Navegación
    nav = ctk.CTkFrame(acciones, fg_color="transparent")
    nav.pack(side="right")
    btn_ant = ctk.CTkButton(nav, text=tr("⬅ Anterior"), width=100, height=32)
    btn_ant.pack(side="left", padx=4)
    btn_sig = ctk.CTkButton(nav, text=tr("Siguiente ➡"), width=100, height=32)
    btn_sig.pack(side="left", padx=4)
    btn_close = ctk.CTkButton(nav, text=tr("Cerrar"), width=80, height=32,
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
        lbl_progreso.configure(text=tr('{0}/{1} completados').format((len(completados)), (total)))
        win.title(tr('📚 Tutorial — {0}/{1} pasos').format((len(completados)), (total)))

    def mostrar_paso():
        paso = pasos[idx]
        lbl_paso.configure(text=tr('Paso {0}/{1}  ·  {2}%').format((paso['id']), (total), (int((idx + 1) / total * 100))))
        bar_paso.set((idx + 1) / total)
        lbl_titulo.configure(text=paso["titulo"])
        txt_desc.configure(state="normal")
        txt_desc.delete("1.0", "end")
        txt_desc.insert("1.0", paso["descripcion"])
        txt_desc.configure(state="disabled")

        # Probar
        accion = paso.get("accion")
        if accion:
            btn_probar.configure(state="normal", text=tr("▶ Probar ahora"),
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

    def _flash_widget(w):
        """Resalta un widget con borde azul durante 1.5s. Ultra-defensivo:
        cada operación en su propio try/except, no propaga errores."""
        orig_color = None
        orig_width = None
        try:
            orig_color = w.cget("border_color")
        except Exception as _e:
            logger.debug(f"[silent] cget border_color: {_e}")
        try:
            orig_width = w.cget("border_width")
        except Exception as _e:
            logger.debug(f"[silent] cget border_width: {_e}")
        try:
            w.configure(border_color="#3b82f6", border_width=3)
        except Exception as _e:
            logger.debug(f"[silent] configure flash: {_e}")
            return  # Si no podemos configurar, no programamos restore

        def _restore():
            try:
                if not w.winfo_exists():
                    return
                kwargs = {}
                if orig_color is not None:
                    kwargs["border_color"] = orig_color
                if orig_width is not None:
                    kwargs["border_width"] = orig_width
                if kwargs:
                    w.configure(**kwargs)
            except Exception as _e:
                logger.debug(f"[silent] restore: {_e}")
        try:
            app.after(1500, _restore)
        except Exception as _e:
            logger.debug(f"[silent] schedule restore: {_e}")

    def _focus_widget(widget_name: str) -> str:
        """Hace focus + flash al widget. Devuelve mensaje. NO cierra la ventana
        del tutorial — el caller (dispatcher) lo decide tras éxito."""
        if not hasattr(app, widget_name):
            # Lista alternativos (mismo prefijo) para mensaje útil
            alternativos = [a for a in dir(app)
                            if widget_name.lower() in a.lower() and not a.startswith("__")][:5]
            sug = f" — ¿Quizás: {', '.join(alternativos)}?" if alternativos else ""
            raise AttributeError(f"Widget '{widget_name}' no existe en ArquitectoApp{sug}")
        w = getattr(app, widget_name)
        if w is None:
            raise AttributeError(f"Widget '{widget_name}' es None")
        try:
            w.focus_set()
        except Exception as _e:
            logger.debug(f"[silent] focus_set: {_e}")
        _flash_widget(w)
        return tr("✏️ Foco en {0} — busca el borde azul").format(widget_name)

    def _focus_modelo() -> str:
        """Resuelve el combo de modelo según el modo activo y le hace focus."""
        modo = "imagen"
        try:
            modo = app.modo_var.get()
        except Exception as _e:
            logger.debug(f"[silent] modo_var: {_e}")
        nombre = {
            "imagen": "combo_modelo_imagen",
            "video":  "combo_modelo_video",
            "audio":  "combo_modelo_audio",
        }.get(modo, "combo_modelo_imagen")
        return _focus_widget(nombre)

    def _set_modo(valor: str) -> str:
        """Cambia el modo activo (imagen / video / audio)."""
        mapa_label = {"imagen": tr("Imagen"), "video": tr("Vídeo"), "audio": tr("Audio")}
        label = mapa_label.get(valor.lower(), tr("Imagen"))
        if not hasattr(app, "_seg_modo"):
            raise AttributeError("app._seg_modo no existe")
        try:
            app._seg_modo.set(label)
            if hasattr(app, "_on_segmento_modo"):
                app._on_segmento_modo(label)
        except Exception as e:
            raise RuntimeError(f"No se pudo cambiar modo: {e}") from e
        return f"📱 Modo cambiado a {label}"

    def _set_tab(nombre_tab: str) -> str:
        """Cambia la tab activa del tabview central."""
        if not hasattr(app, "tabview"):
            raise AttributeError("app.tabview no existe")
        # Probar nombre exacto, luego sin emojis/espacios
        try:
            app.tabview.set(tr(nombre_tab))
            return f"📑 Tab cambiada: {nombre_tab}"
        except Exception as e:
            logger.debug(f"tabview.set exacto falló: {e}")
        nombres_disponibles = getattr(app.tabview, "_name_list", [])
        norm = lambda s: "".join(c.lower() for c in s if c.isalnum())
        for nombre in nombres_disponibles:
            if norm(nombre) == norm(nombre_tab):
                app.tabview.set(nombre)
                return f"📑 Tab cambiada: {nombre}"
        raise AttributeError(
            f"Tab '{nombre_tab}' no encontrada. Disponibles: {nombres_disponibles}"
        )

    # Acciones que requieren cerrar la ventana del tutorial para verse bien
    # (porque el tutorial taparía el widget destacado o la tab nueva).
    _ACCIONES_CERRAR_VENTANA = ("focus:", "mode:", "tab:", "focus_modelo")

    # Acciones que NO hacen nada visible si txt_salida está vacío.
    # Las pre-validamos para mostrar un error útil en vez de silencio.
    _ACCIONES_NECESITAN_SALIDA = {
        "_guardar_favorito", "_guardar_estrella",
        "cmd_refinar", "_cmd_scoring", "_cmd_export_cli",
        "_cmd_versiones_prompt",
    }

    def _probar(accion: str):
        """Ejecuta la acción del paso actual.

        Acciones soportadas:
          - "focus:WIDGET"      → focus + flash al widget
          - "mode:imagen|video|audio" → cambia el modo
          - "tab:NOMBRE_TAB"    → cambia la pestaña del tabview central
          - "focus_modelo"      → focus al combo según modo activo
          - "abrir_X" (libre en modules.windows) → invocar con app
          - cualquier otro      → método de ArquitectoApp

        En caso de error: NO cierra la ventana del tutorial (para que el
        usuario lea el mensaje en el toast) y NO marca como completado.
        """
        mensaje = None
        cerrar = any(accion.startswith(p) for p in _ACCIONES_CERRAR_VENTANA)
        try:
            # Pre-validación: ¿hay prompt en la salida para acciones que lo necesitan?
            if accion in _ACCIONES_NECESITAN_SALIDA:
                txt_sal = getattr(app, "txt_salida", None)
                contenido_salida = ""
                if txt_sal is not None:
                    try:
                        contenido_salida = txt_sal.get("1.0", "end").strip()
                    except Exception as _e:
                        logger.debug(f"[silent] txt_salida.get: {_e}")
                if not contenido_salida:
                    raise RuntimeError(tr(
                        "Necesitas generar un prompt primero (Ctrl+Enter en la app). "
                        "Esa acción usa el contenido del área de salida."
                    ))

            if accion.startswith("focus:"):
                mensaje = _focus_widget(accion.split(":", 1)[1])
            elif accion.startswith("mode:"):
                mensaje = _set_modo(accion.split(":", 1)[1])
            elif accion.startswith("tab:"):
                mensaje = _set_tab(accion.split(":", 1)[1])
            elif accion == "focus_modelo":
                mensaje = _focus_modelo()
            elif accion in _FREE_FUNCS:
                from modules import windows as _w
                fn = getattr(_w, accion, None)
                if not callable(fn):
                    raise AttributeError(f"{accion} no existe en modules.windows")
                fn(app)
            else:
                fn = getattr(app, accion, None)
                if not callable(fn):
                    raise AttributeError(f"{accion} no es método de ArquitectoApp")
                fn()
            # ── Éxito ──
            completados.add(idx + 1)
            btn_completado_var.set(True)
            actualizar_indice()
            _guardar_progreso(app, completados, idx + 1)
            if mensaje:
                try:
                    app.show_toast(mensaje, "#3b82f6", 2500)
                except Exception as _e:
                    logger.debug(f"[silent] {_e}")
            if cerrar:
                try:
                    win.destroy()
                except Exception as _e:
                    logger.debug(f"[silent] win.destroy: {_e}")
        except Exception as e:
            # NO cerramos la ventana — el usuario verá el toast y podrá leer
            logger.warning(f"Tutorial: acción '{accion}' falló: {e}")
            try:
                app.show_toast(f"❌ {accion}: {e}", "#e74c3c", 5000)
            except Exception as _e:
                logger.debug(f"[silent] show_toast: {_e}")

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
