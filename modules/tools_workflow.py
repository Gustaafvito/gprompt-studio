"""Workflow Tools Mixin - Setup management, Macros, A/B Testing, Cron, Projects, Session Recording, etc."""
import datetime
import logging
import threading

import pyperclip

logger = logging.getLogger(__name__)
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk

from config import get_theme_colors as _get_tc
from modules.gprompt_window import GPromptWindow
from workers import limpiar_marcadores

if TYPE_CHECKING:
    pass

class ToolsWorkflowService:
    """14 herramientas de workflow: setups, cron, versiones, macros,
    scoring auto, proyectos, atajos de tags.

    A1 fase 2 (sesión 14): servicio aislado con app por composición.
    """

    def __init__(self, app):
        self.app = app

    def _capturar_setup_actual(self):
        """Devuelve un dict con la configuración actual (modelo, plataforma, ratio, estilos, negatives, etc.)."""
        try:
            estilos_sel = []
            if hasattr(self.app, "estilo_checks"):
                for nombre, var in self.app.estilo_checks.items():
                    try:
                        if var.get(): estilos_sel.append(nombre)
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            negatives_sel = []
            if hasattr(self.app, "preset_vars"):
                for nombre, var in self.app.preset_vars.items():
                    try:
                        if var.get(): negatives_sel.append(nombre)
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            modelo = ""
            modo = self.app.modo_var.get() if hasattr(self.app, "modo_var") else "imagen"
            if modo == "imagen" and hasattr(self.app, "combo_modelo_imagen"):
                modelo = self.app.combo_modelo_imagen.get() or ""
            elif modo == "video" and hasattr(self.app, "combo_modelo_video"):
                modelo = self.app.combo_modelo_video.get() or ""
            elif modo == "audio" and hasattr(self.app, "combo_modelo_audio"):
                modelo = self.app.combo_modelo_audio.get() or ""
            setup = {
                "modo": modo,
                "modelo": modelo,
                "plataforma": self.app.plataforma_var.get() if hasattr(self.app, "plataforma_var") else "",
                "ratio": self.app.ratio_var.get() if hasattr(self.app, "ratio_var") else "",
                "destino": self.app.destino_var.get() if hasattr(self.app, "destino_var") else "",
                "personaje": self.app.combo_personaje.get() if hasattr(self.app, "combo_personaje") else "",
                "lora": self.app.combo_lora.get() if hasattr(self.app, "combo_lora") else "",
                "estilos": estilos_sel,
                "negatives": negatives_sel,
                "nsfw": bool(self.app.switch_nsfw_var.get()) if hasattr(self.app, "switch_nsfw_var") else False,
                "auto_trad": bool(self.app.switch_traduccion_var.get()) if hasattr(self.app, "switch_traduccion_var") else False,
            }
            return setup
        except Exception:
            return {}

    def _aplicar_setup(self, setup):
        """Aplica un setup guardado a la UI actual."""
        if not setup or not isinstance(setup, dict): return
        try: self.app._sesion_log(f"🔄 Aplicó setup ({setup.get('modo', '?')} · {setup.get('plataforma', '—')} · {setup.get('modelo', '—')})")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        try:
            # Modo primero (cambia paneles disponibles)
            if setup.get("modo") and hasattr(self.app, "modo_var"):
                self.app.modo_var.set(setup["modo"])
                if hasattr(self.app, "_on_modo_cambio"):
                    try: self.app._on_modo_cambio()
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            # Plataforma
            if setup.get("plataforma") and hasattr(self.app, "plataforma_var"):
                self.app.plataforma_var.set(setup["plataforma"])
                if hasattr(self.app, "_on_plataforma_cambio"):
                    try: self.app._on_plataforma_cambio()
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            # Modelo (según modo)
            modo = setup.get("modo", "imagen")
            modelo = setup.get("modelo", "")
            if modelo:
                if modo == "imagen" and hasattr(self.app, "combo_modelo_imagen"):
                    self.app.combo_modelo_imagen.set(modelo)
                    if hasattr(self.app, "_on_modelo_imagen_cambio"):
                        try: self.app._on_modelo_imagen_cambio()
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
                elif modo == "video" and hasattr(self.app, "combo_modelo_video"):
                    self.app.combo_modelo_video.set(modelo)
                    if hasattr(self.app, "_on_motor_cambio"):
                        try: self.app._on_motor_cambio()
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
                elif modo == "audio" and hasattr(self.app, "combo_modelo_audio"):
                    self.app.combo_modelo_audio.set(modelo)
                    if hasattr(self.app, "_on_motor_audio_cambio"):
                        try: self.app._on_motor_audio_cambio()
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
            # Ratio, destino
            for key, attr in [("ratio", "ratio_var"), ("destino", "destino_var")]:
                v = setup.get(key)
                if v and hasattr(self.app, attr):
                    try: getattr(self.app, attr).set(v)
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            # Personaje y LoRA (son combos directos)
            if setup.get("personaje") and hasattr(self.app, "combo_personaje"):
                try: self.app.combo_personaje.set(setup["personaje"])
                except Exception as e:
                    logger.debug(f"[silent] {e}")
            if setup.get("lora") and hasattr(self.app, "combo_lora"):
                try: self.app.combo_lora.set(setup["lora"])
                except Exception as e:
                    logger.debug(f"[silent] {e}")
            if "nsfw" in setup and hasattr(self.app, "switch_nsfw_var"):
                try: self.app.switch_nsfw_var.set(bool(setup["nsfw"]))
                except Exception as e:
                    logger.debug(f"[silent] {e}")
            if "auto_trad" in setup and hasattr(self.app, "switch_traduccion_var"):
                try:
                    self.app.switch_traduccion_var.set(bool(setup["auto_trad"]))
                    if hasattr(self.app, "_sw_trad_callback"):
                        try: self.app._sw_trad_callback()
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
                except Exception as e:
                    logger.debug(f"[silent] {e}")
            # Estilos
            estilos_sel = set(setup.get("estilos", []))
            if hasattr(self.app, "estilo_checks"):
                for nombre, var in self.app.estilo_checks.items():
                    try: var.set(nombre in estilos_sel)
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            # Negatives
            negatives_sel = set(setup.get("negatives", []))
            if hasattr(self.app, "preset_vars"):
                for nombre, var in self.app.preset_vars.items():
                    try: var.set(nombre in negatives_sel)
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            # Refrescar negative textbox
            if hasattr(self.app, "_rebuild_negative_text"):
                try: self.app.footer._rebuild_negative_text()
                except Exception as e:
                    logger.debug(f"[silent] {e}")
        except Exception as e:
            self.app.set_estado(f"⚠️ Error aplicando setup: {e}", "#e74c3c")

    def _cmd_guardar_setup(self):
        """Abre diálogo para nombrar y guardar el setup actual."""
        from tkinter import simpledialog
        setup = self._capturar_setup_actual()
        if not setup:
            self.app.set_estado("⚠️ No se pudo capturar la configuración", "#e67e22")
            return
        nombre = simpledialog.askstring("💾 Guardar setup",
                                          "Nombre para este setup:\n(modelo, plataforma, ratio, estilos, negatives…)",
                                          parent=self.app)
        if not nombre or not nombre.strip(): return
        nombre = nombre.strip()[:60]
        # Cargar setups existentes
        prefs = self.app.store.cargar_preferencias()
        setups = prefs.get("setups", {}) or {}
        # Confirmación si ya existe
        if nombre in setups:
            from tkinter import messagebox
            if not messagebox.askyesno("Sobrescribir",
                                         f"Ya existe un setup llamado '{nombre}'. ¿Sobrescribirlo?",
                                         parent=self.app):
                return
        setup["_fecha_guardado"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        setups[nombre] = setup
        prefs["setups"] = setups
        self.app.store.guardar_preferencias(prefs)
        self.app.set_estado(f"💾 Setup '{nombre}' guardado", "#2ecc71")
        try: self.app._sesion_log(f"💾 Guardó setup: {nombre}")
        except Exception as e:
            logger.debug(f"[silent] {e}")

    def _cmd_cargar_setup(self):
        """Abre ventana con la lista de setups guardados para elegir uno."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        prefs = self.app.store.cargar_preferencias()
        setups = prefs.get("setups", {}) or {}
        if not setups:
            self.app.set_estado("⚠️ No hay setups guardados todavía. Pulsa '💾 Setup' para guardar el actual.", "#e67e22")
            return
        v = GPromptWindow(self.app)
        v.title("📋 Cargar setup")
        v.geometry("560x520")
        v.transient(self.app)
        ctk.CTkLabel(v, text="📋 Setups guardados", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 8))
        scroll = ctk.CTkScrollableFrame(v, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        def _refrescar_lista():
            for w in scroll.winfo_children(): w.destroy()
            setups_act = self.app.store.cargar_preferencias().get("setups", {}) or {}
            if not setups_act:
                ctk.CTkLabel(scroll, text="(sin setups)", text_color="#666").pack(pady=20)
                return
            for nombre, setup in sorted(setups_act.items()):
                card = ctk.CTkFrame(scroll, fg_color=c["fg_dark"], corner_radius=8)
                card.pack(fill="x", pady=4)
                # Header del card
                ctk.CTkLabel(card, text=f"📋 {nombre}", font=ctk.CTkFont(size=12, weight="bold"),
                             anchor="w").pack(fill="x", padx=10, pady=(8, 2))
                # Resumen
                modelo = setup.get("modelo", "—")
                plat = setup.get("plataforma", "—")
                ratio = setup.get("ratio", "")
                modo = setup.get("modo", "imagen")
                fecha = setup.get("_fecha_guardado", "")
                estilos = setup.get("estilos", [])
                negatives = setup.get("negatives", [])
                resumen = f"{modo} · {plat} · {modelo}"
                if ratio: resumen += f" · {ratio}"
                if estilos: resumen += f" · 🎨 {len(estilos)} estilos"
                if negatives: resumen += f" · 🚫 {len(negatives)} negs"
                ctk.CTkLabel(card, text=resumen, font=ctk.CTkFont(size=10),
                             text_color="#888", anchor="w").pack(fill="x", padx=10)
                if fecha:
                    ctk.CTkLabel(card, text=f"  guardado: {fecha}", font=ctk.CTkFont(size=9),
                                 text_color="#555", anchor="w").pack(fill="x", padx=10)
                # Botones
                btn_row = ctk.CTkFrame(card, fg_color="transparent")
                btn_row.pack(fill="x", padx=10, pady=(4, 8))

                def _aplicar(s=setup, n=nombre):
                    self._aplicar_setup(s)
                    self.app.set_estado(f"📋 Setup '{n}' aplicado", "#2ecc71")
                    v.destroy()

                def _borrar(n=nombre):
                    from tkinter import messagebox
                    if messagebox.askyesno("Borrar setup", f"¿Borrar el setup '{n}'?", parent=v):
                        prefs2 = self.app.store.cargar_preferencias()
                        setups2 = prefs2.get("setups", {}) or {}
                        setups2.pop(n, None)
                        prefs2["setups"] = setups2
                        self.app.store.guardar_preferencias(prefs2)
                        _refrescar_lista()

                ctk.CTkButton(btn_row, text="Aplicar", width=90, height=26,
                              fg_color="#1e5f3a", hover_color="#16492d", command=_aplicar).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text="🗑 Borrar", width=90, height=26,
                              fg_color="#6a1a1a", hover_color="#4a0f0f", command=_borrar).pack(side="left", padx=2)

        _refrescar_lista()
        ctk.CTkButton(v, text="Cerrar", width=110, command=v.destroy,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"]).pack(pady=(0, 12))

    def _cmd_cron_prompts(self):
        """Genera N variantes del prompt actual espaciadas en el tiempo."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        idea = self.app.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            self.app.set_estado("⚠️ Escribe una idea base primero.", "#e67e22")
            return

        vent = GPromptWindow(self.app)
        vent.title("⏲ Cron de variantes")
        vent.geometry("520x620")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text="⏲ Cron — Variantes programadas", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 3))
        ctk.CTkLabel(vent, text="Genera N VARIANTES distintas espaciadas en el tiempo.\nCada una añade variación (encuadre, iluminación, paleta...) automáticamente.",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"], justify="center").pack(pady=(0, 12))

        ctk.CTkLabel(vent, text=f"Idea base:\n{idea[:120]}{'...' if len(idea) > 120 else ''}",
                     font=ctk.CTkFont(size=10), text_color=c["hdr_text"], wraplength=460,
                     fg_color=c["fg_dark"], corner_radius=6).pack(fill="x", padx=15, pady=(0, 12))

        # Cantidad
        f1 = ctk.CTkFrame(vent, fg_color="transparent")
        f1.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f1, text="Cantidad de variantes:", width=160, anchor="w").pack(side="left")
        ent_cantidad = ctk.CTkEntry(f1, width=80)
        ent_cantidad.insert(0, "5")
        ent_cantidad.pack(side="left")

        # Intervalo
        f2 = ctk.CTkFrame(vent, fg_color="transparent")
        f2.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f2, text="Cada cuántos minutos:", width=160, anchor="w").pack(side="left")
        ent_intervalo = ctk.CTkEntry(f2, width=80)
        ent_intervalo.insert(0, "10")
        ent_intervalo.pack(side="left")

        # Qué variar
        ctk.CTkLabel(vent, text="Qué cambiar entre variantes:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=20, pady=(12, 3))
        var_aspecto = ctk.StringVar(value="Variar todo aleatoriamente")
        opciones = [
            "Variar todo aleatoriamente",
            "Solo iluminación",
            "Solo encuadre/cámara",
            "Solo paleta de colores",
            "Solo atmósfera/mood",
            "Solo estilo artístico",
            "🎯 Personalizado (ver abajo)",
        ]
        cb_aspecto = ctk.CTkComboBox(vent, values=opciones, variable=var_aspecto, width=320, height=28)
        cb_aspecto.pack(anchor="w", padx=20)

        # Campo personalizado
        ctk.CTkLabel(vent, text="Instrucción personalizada (opcional):",
                     font=ctk.CTkFont(size=10, weight="bold"), text_color=c["muted_text"]).pack(anchor="w", padx=20, pady=(8, 2))
        ent_personalizado = ctk.CTkEntry(vent,
                                          placeholder_text='ej: "cambia el animal en cada variante" o "varía el color del coche"',
                                          width=460, height=28)
        ent_personalizado.pack(anchor="w", padx=20)
        ctk.CTkLabel(vent, text="Si rellenas esto, se usa SIEMPRE (independientemente del selector de arriba).",
                     font=ctk.CTkFont(size=9, slant="italic"), text_color="#666666").pack(anchor="w", padx=20, pady=(2, 0))

        lbl_progreso = ctk.CTkLabel(vent, text="", font=ctk.CTkFont(size=11), text_color=c["muted_text"])
        lbl_progreso.pack(pady=15)

        cron_state = {"activo": False, "actuales": 0, "generados": [],
                      "after_id": None, "cerrada": False}

        def _safe_configure(widget, **kw):
            """Actualiza el widget solo si la ventana sigue viva."""
            if cron_state["cerrada"]:
                return
            try:
                widget.configure(**kw)
            except Exception as _e:
                logger.debug(f"[silent cron _safe_configure] {_e}")

        def _on_cerrar():
            """Cierre limpio: para el cron, cancela el after pendiente."""
            cron_state["activo"] = False
            cron_state["cerrada"] = True
            if cron_state["after_id"]:
                try: vent.after_cancel(cron_state["after_id"])
                except Exception as _e: logger.debug(f"[silent] {_e}")
                cron_state["after_id"] = None
            vent.destroy()
        vent.protocol("WM_DELETE_WINDOW", _on_cerrar)

        def _ejecutar_cron():
            try:
                cantidad = int(ent_cantidad.get())
                intervalo = float(ent_intervalo.get())
                if cantidad < 1 or cantidad > 50: raise ValueError("cantidad fuera de rango")
                if intervalo < 0.1 or intervalo > 120: raise ValueError("intervalo fuera de rango")
            except Exception:
                self.app.set_estado("⚠️ Cantidad (1-50) e intervalo (0.1-120 min)", "#e67e22")
                return

            cron_state["activo"] = True
            cron_state["actuales"] = 0
            cron_state["generados"] = []
            aspecto = var_aspecto.get()
            personalizado = ent_personalizado.get().strip()
            modo = self.app.modo_var.get()
            estilos = self.app.footer.estilos_texto()

            mapeo_aspecto = {
                "Solo iluminación": "iluminación (tipo, dirección, intensidad, color)",
                "Solo encuadre/cámara": "encuadre, plano y movimiento de cámara",
                "Solo paleta de colores": "paleta de colores y tonalidades",
                "Solo atmósfera/mood": "atmósfera, mood y sensación general",
                "Solo estilo artístico": "estilo artístico / género / estética",
                "Variar todo aleatoriamente": "todos los aspectos visuales: iluminación, encuadre, paleta, atmósfera",
                "🎯 Personalizado (ver abajo)": personalizado if personalizado else "todos los aspectos visuales",
            }
            # Si hay instrucción personalizada, prevalece sobre el selector
            if personalizado:
                elemento = personalizado
                instruccion_extra = (
                    f"INSTRUCCIÓN ESPECÍFICA DEL USUARIO:\n{personalizado}\n\n"
                    f"Aplica esta instrucción de forma CLARA Y NOTABLE en cada variante. "
                    f"Cada variante debe seguir esta indicación pero con un cambio diferente "
                    f"(ej: si dice 'cambia el animal', variante 1=perro, variante 2=gato, "
                    f"variante 3=águila, etc. — sé creativo y diverso).\n"
                )
            else:
                elemento = mapeo_aspecto.get(aspecto, "todos los aspectos")
                instruccion_extra = ""

            def _generar_variante(num):
                """Genera UNA variante específica con el LLM."""
                try:
                    peticion = (
                        f"Genera UNA variante de un prompt de {modo} basado en esta idea:\n\n"
                        f"IDEA BASE: {idea}\n\n"
                        f"{instruccion_extra}"
                        f"INSTRUCCIONES:\n"
                        f"- Esta es la variante #{num} de {cantidad} — debe ser DIFERENTE a las anteriores.\n"
                        f"- Cambia principalmente: {elemento}\n"
                        f"- Mantén la idea central (composición, sujeto principal si no es el cambio).\n"
                        f"- Estilos a aplicar: {estilos}\n"
                        f"- Sé creativo y diverso: cada llamada debe dar resultado distinto.\n\n"
                        f"FORMATO:\nPOSITIVE PROMPT: [prompt completo]\nNEGATIVE PROMPT: [si el modelo lo soporta]\n"
                    )
                    resp = self.app.deepseek.generar(peticion, temperature=0.9, max_tokens=1500)
                    resp = limpiar_marcadores(resp)

                    # Eliminar negative si el modelo no lo soporta
                    specs = self.app.get_current_model_specs()
                    if specs and not specs.get("has_negative", True):
                        import re
                        resp = re.sub(r'\n?\s*NEGATIVE\s+PROMPT\s*:.*?$', '', resp, flags=re.DOTALL | re.IGNORECASE).strip()

                    cron_state["generados"].append(resp)
                    self.app.guardar_en_historial(resp)

                    def _aplicar():
                        if cron_state["cerrada"]:
                            return
                        self.app.actualizar_salida(resp)
                        progreso = f"⏲ Variante {num}/{cantidad} generada · próxima en {int(intervalo)}min"
                        if num >= cantidad:
                            progreso = f"✅ Cron completado: {cantidad} variantes generadas"
                        _safe_configure(lbl_progreso, text=progreso,
                                        text_color="#2ecc71" if num >= cantidad else "#3498db")
                        self.app.set_estado(f"⏲ Variante {num}/{cantidad} lista", "#3498db")
                    self.app.after(0, _aplicar)
                except Exception as e:
                    self.app.after(0, lambda e=e: _safe_configure(lbl_progreso,
                                                          text=f"❌ Error variante {num}: {e}",
                                                          text_color="#e74c3c"))

            def _siguiente():
                if cron_state["cerrada"] or not cron_state["activo"]:
                    return
                cron_state["actuales"] += 1
                num = cron_state["actuales"]
                _safe_configure(lbl_progreso,
                                text=f"⏲ Generando variante {num}/{cantidad}...",
                                text_color="#f39c12")

                threading.Thread(target=lambda n=num: _generar_variante(n), daemon=True).start()

                if num < cantidad and cron_state["activo"]:
                    cron_state["after_id"] = vent.after(
                        int(intervalo * 60 * 1000), _siguiente)
                else:
                    cron_state["activo"] = False
                    cron_state["after_id"] = None

            _siguiente()
            self.app.set_estado(f"⏲ Cron iniciado: {cantidad} variantes cada {intervalo}min", "#2ecc71")

        def _detener():
            cron_state["activo"] = False
            if cron_state["after_id"]:
                try: vent.after_cancel(cron_state["after_id"])
                except Exception as _e: logger.debug(f"[silent] {_e}")
                cron_state["after_id"] = None
            _safe_configure(lbl_progreso,
                            text=f"⏹ Cron detenido en variante {cron_state['actuales']}/{ent_cantidad.get()}",
                            text_color="#e67e22")

        def _ver_todas():
            if cron_state["generados"]:
                self.app._abrir_comparador(cron_state["generados"])
            else:
                self.app.set_estado("⚠️ Aún no hay variantes generadas", "#e67e22")

        btn_row = ctk.CTkFrame(vent, fg_color="transparent")
        btn_row.pack(pady=10)
        ctk.CTkButton(btn_row, text="▶ Iniciar cron", width=130, height=32, fg_color="#1a7a3c",
                      command=_ejecutar_cron).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="⏹ Detener", width=100, height=32, fg_color="#5a1a1a",
                      command=_detener).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="👁 Ver todas", width=110, height=32, fg_color="#1a4a7a",
                      command=_ver_todas).pack(side="left", padx=4)

    def _guardar_version_prompt(self):
        """Guarda la versión actual del prompt antes de modificarlo (sistema tipo Git)."""
        actual = self.app.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20: return
        if not hasattr(self.app, '_versiones_prompt'):
            self.app._versiones_prompt = []
        # Evitar duplicados consecutivos
        if self.app._versiones_prompt and self.app._versiones_prompt[-1]["texto"] == actual:
            return
        self.app._versiones_prompt.append({
            "texto": actual,
            "fecha": datetime.datetime.now().strftime("%H:%M:%S"),
            "etiqueta": f"v{len(self.app._versiones_prompt) + 1}",
        })
        # Limitar historial a 30 versiones por sesión
        if len(self.app._versiones_prompt) > 30:
            self.app._versiones_prompt = self.app._versiones_prompt[-30:]

    def _cmd_versiones_prompt(self):
        """Muestra el historial de versiones del prompt actual (rollback)."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        if not hasattr(self.app, '_versiones_prompt') or not self.app._versiones_prompt:
            return self.app.set_estado("⚠️ No hay versiones aún. Genera/refina prompts para crear versiones.", "#e67e22")

        vent = GPromptWindow(self.app)
        vent.title("📜 Historial de versiones del prompt")
        vent.geometry("700x500")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=f"📜 {len(self.app._versiones_prompt)} versiones en esta sesión",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text="Click en una versión para restaurarla",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=5)

        # Mostrar de más reciente a más antiguo
        for i, ver in enumerate(reversed(self.app._versiones_prompt)):
            num = len(self.app._versiones_prompt) - i
            card = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=6)
            card.pack(fill="x", pady=3)
            # Color del header según origen (Walk · azul-verdoso, pre-refinamiento · ámbar)
            etiq = ver.get("etiqueta", "") or ""
            hdr_color = "#1a3a5a"
            origen_txt = ""
            if "Walk" in etiq:
                hdr_color = "#1a4a7a"
                # Extrae el "Walk Raíz → D2 · nodo X" del paréntesis
                import re as _re
                m = _re.search(r"\((Walk[^)]+)\)", etiq)
                origen_txt = f"  ·  🌀 {m.group(1)}" if m else "  ·  🌀 Walk"
            elif "pre-refinamiento" in etiq:
                hdr_color = "#7a5a1a"
                origen_txt = "  ·  🔁 pre-refinamiento"
            hdr = ctk.CTkFrame(card, fg_color=hdr_color, corner_radius=4, height=24)
            hdr.pack(fill="x", padx=4, pady=(3, 0))
            hdr.pack_propagate(False)
            ctk.CTkLabel(hdr,
                         text=f"  📜 Versión #{num}  ·  {ver.get('fecha', '')}{origen_txt}",
                         font=ctk.CTkFont(size=11, weight="bold"), text_color=c["hdr_text"]).pack(side="left", padx=4)

            preview = ver["texto"][:200]
            ctk.CTkLabel(card, text=preview + ("..." if len(ver["texto"]) > 200 else ""),
                         font=ctk.CTkFont(size=10), text_color=c["muted_text"],
                         wraplength=640, justify="left", anchor="w").pack(fill="x", padx=8, pady=(2, 4))

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=5, pady=(0, 4))

            def _restaurar(t=ver["texto"]):
                self.app.actualizar_salida(t)
                vent.destroy()
                self.app.set_estado(f"⏪ Versión restaurada", "#2ecc71")
            ctk.CTkButton(btn_row, text="⏪ Restaurar esta", width=130, height=22, fg_color="#1a7a3c",
                          font=ctk.CTkFont(size=10), command=_restaurar).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text="📋 Copiar", width=80, height=22, fg_color=c["fg_dark"],
                          font=ctk.CTkFont(size=10),
                          command=lambda t=ver["texto"]: pyperclip.copy(t)).pack(side="left", padx=2)

    def _abrir_macros(self):
        """Macros: secuencias de acciones automatizadas."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        prefs = self.app.store.cargar_preferencias()
        macros = prefs.get("macros", [])

        vent = GPromptWindow(self.app)
        vent.title("⚡ Macros — Secuencias automatizadas")
        vent.geometry("700x600")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text="⚡ Macros — Secuencias de acciones automatizadas",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text="Combina acciones (ej: Generar → Refinar cinematográfico → Guardar estrella)",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

        # Acciones disponibles para construir macros (solo automáticas)
        acciones_disponibles = {
            "✨ Generar prompt": "generar",
            "⚡ Generar idea directa": "idea_auto",
            "🔄 Generar 1 variación": "variacion_auto",
            "🛡 Generar negative óptimo": "negative_optimo",
            "🚫 Negative builder": "negative_builder",
            "🎨 Previsualizar": "previsualizar",
            "🔁 Refinar (estándar)": "refinar",
            "🎬 Refinar más cinematográfico": "refinar_cinematografico",
            "👤 Refinar más detalle facial": "refinar_facial",
            "💡 Refinar mejor iluminación": "refinar_iluminacion",
            "🎯 Refinar mejorado": "refinar_mejorado",
            "✂️ Refinar simplificar": "refinar_simplificar",
            "📊 Scoring auto": "scoring_auto",
            "🎨 Sugerir estilos": "sugerir_estilos",
            "⭐ Guardar Favorito": "guardar_favorito",
            "🌟 Guardar Estrella": "guardar_estrella",
            "🧹 Limpiar salida": "limpiar",
            "📋 Copiar negative": "copiar_neg",
            "📋 Copiar positive": "copiar_pos",
            "🇪🇸 Traducir al español": "traducir",
        }

        # Form crear/editar macro
        # Estado: si `editing_idx` != None, estamos editando una macro
        # existente; el botón principal cambia a "Guardar cambios".
        edit_state = {"idx": None}

        form = ctk.CTkFrame(vent, fg_color=c["fg_dark"], corner_radius=6)
        form.pack(fill="x", padx=10, pady=5)
        lbl_form_titulo = ctk.CTkLabel(form, text="➕ Nueva macro",
                                        font=ctk.CTkFont(size=11, weight="bold"))
        lbl_form_titulo.pack(anchor="w", padx=10, pady=(8, 2))

        ent_nombre_m = ctk.CTkEntry(form,
                                     placeholder_text="Nombre (ej: 'Pulir prompt cinematográfico')",
                                     width=580)
        ent_nombre_m.pack(padx=10, pady=2)

        # Lista de pasos como cards con ↑ ↓ ✕ por paso
        pasos_state = {"lista": []}
        pasos_box = ctk.CTkFrame(form, fg_color="transparent")
        pasos_box.pack(fill="x", padx=10, pady=(4, 2))

        def _refrescar_pasos():
            for w in pasos_box.winfo_children():
                w.destroy()
            if not pasos_state["lista"]:
                ctk.CTkLabel(pasos_box, text="(añade pasos abajo)",
                             font=ctk.CTkFont(size=10, slant="italic"),
                             text_color=c["muted_text"]).pack(anchor="w")
                return
            for idx_p, label in enumerate(pasos_state["lista"]):
                row = ctk.CTkFrame(pasos_box, fg_color=c["fg_frame"],
                                    corner_radius=4)
                row.pack(fill="x", pady=1)
                ctk.CTkLabel(row, text=f"  {idx_p + 1}. {label}",
                             font=ctk.CTkFont(size=10),
                             text_color=c["hdr_text"],
                             anchor="w").pack(side="left", fill="x",
                                              expand=True, padx=4, pady=2)

                def _subir(i=idx_p):
                    if i > 0:
                        lst = pasos_state["lista"]
                        lst[i - 1], lst[i] = lst[i], lst[i - 1]
                        _refrescar_pasos()

                def _bajar(i=idx_p):
                    lst = pasos_state["lista"]
                    if i < len(lst) - 1:
                        lst[i + 1], lst[i] = lst[i], lst[i + 1]
                        _refrescar_pasos()

                def _quitar(i=idx_p):
                    if 0 <= i < len(pasos_state["lista"]):
                        pasos_state["lista"].pop(i)
                        _refrescar_pasos()

                ctk.CTkButton(row, text="↑", width=24, height=20,
                              fg_color=c["fg_dark"],
                              font=ctk.CTkFont(size=10),
                              state="normal" if idx_p > 0 else "disabled",
                              command=_subir).pack(side="left", padx=1)
                ctk.CTkButton(row, text="↓", width=24, height=20,
                              fg_color=c["fg_dark"],
                              font=ctk.CTkFont(size=10),
                              state="normal" if idx_p < len(pasos_state["lista"]) - 1 else "disabled",
                              command=_bajar).pack(side="left", padx=1)
                ctk.CTkButton(row, text="✕", width=24, height=20,
                              fg_color="#5a1a1a", hover_color="#3a0f0f",
                              font=ctk.CTkFont(size=10, weight="bold"),
                              command=_quitar).pack(side="left", padx=1)

        # Selector de acción a añadir
        f_add = ctk.CTkFrame(form, fg_color="transparent")
        f_add.pack(fill="x", padx=10, pady=2)
        var_accion = ctk.StringVar(value=list(acciones_disponibles.keys())[0])
        cb_acc = ctk.CTkComboBox(f_add, values=list(acciones_disponibles.keys()),
                                  variable=var_accion, width=400, height=24)
        cb_acc.pack(side="left", padx=(0, 5))

        def _add_paso():
            label = var_accion.get()
            pasos_state["lista"].append(label)
            _refrescar_pasos()

        ctk.CTkButton(f_add, text="➕ Añadir paso", width=120, height=24,
                      command=_add_paso).pack(side="left", padx=2)

        def _cancelar_edicion():
            edit_state["idx"] = None
            ent_nombre_m.delete(0, "end")
            pasos_state["lista"] = []
            _refrescar_pasos()
            lbl_form_titulo.configure(text="➕ Nueva macro")
            btn_crear.configure(text="✅ Crear macro", fg_color="#1a7a3c")
            btn_cancelar.pack_forget()

        btn_cancelar = ctk.CTkButton(f_add, text="❌ Cancelar edición",
                                      width=160, height=24,
                                      fg_color="#5a1a1a",
                                      font=ctk.CTkFont(size=10),
                                      command=_cancelar_edicion)
        # btn_cancelar.pack(...)  ← se empaca solo cuando edit_state["idx"] != None

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        def refrescar():
            for w in scroll.winfo_children(): w.destroy()
            actual = prefs.get("macros", [])
            if not actual:
                ctk.CTkLabel(scroll, text="Aún no tienes macros. Crea la primera arriba.",
                             font=ctk.CTkFont(size=11), text_color="#666666").pack(pady=20)
                return
            for i, m in enumerate(actual):
                card = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=6)
                card.pack(fill="x", pady=3)
                ctk.CTkLabel(card, text=f"  ⚡ {m.get('nombre', '?')}",
                             font=ctk.CTkFont(size=11, weight="bold"), text_color=c["hdr_text"]).pack(anchor="w", padx=8, pady=(4, 0))
                pasos_str = " → ".join(m.get("pasos", []))
                ctk.CTkLabel(card, text=f"  {pasos_str}", font=ctk.CTkFont(size=10),
                             text_color=c["muted_text"], wraplength=620, justify="left", anchor="w").pack(fill="x", padx=8, pady=(0, 2))
                btn_row = ctk.CTkFrame(card, fg_color="transparent")
                btn_row.pack(fill="x", padx=5, pady=(0, 4))
                def _ejecutar(macro=m):
                    self._ejecutar_macro(macro, acciones_disponibles)
                    vent.destroy()

                def _editar(idx=i, macro=m):
                    # Cargar la macro en el form de arriba para editarla
                    edit_state["idx"] = idx
                    ent_nombre_m.delete(0, "end")
                    ent_nombre_m.insert(0, macro.get("nombre", ""))
                    pasos_state["lista"] = list(macro.get("pasos", []))
                    _refrescar_pasos()
                    lbl_form_titulo.configure(
                        text=f"✏️ Editando: {macro.get('nombre', '?')}")
                    btn_crear.configure(text="💾 Guardar cambios",
                                         fg_color="#1a5a8a")
                    btn_cancelar.pack(side="left", padx=2)
                    # Scroll al form
                    try:
                        ent_nombre_m.focus_set()
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")

                def _borrar(idx=i, nombre=m.get("nombre", "?")):
                    if not messagebox.askyesno(
                        "Borrar macro",
                        f"¿Borrar la macro '{nombre}'?",
                        parent=vent,
                    ):
                        return
                    actual2 = prefs.get("macros", [])
                    if idx < len(actual2):
                        actual2.pop(idx)
                        prefs["macros"] = actual2
                        self.app.store.guardar_preferencias(prefs)
                        # Si estábamos editando esta macro, salir del modo edición
                        if edit_state["idx"] == idx:
                            _cancelar_edicion()
                        refrescar()

                ctk.CTkButton(btn_row, text="▶ Ejecutar", width=100, height=22, fg_color="#1a7a3c",
                              font=ctk.CTkFont(size=10), command=_ejecutar).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text="✏️ Editar", width=90, height=22, fg_color="#1a4a7a",
                              font=ctk.CTkFont(size=10), command=_editar).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text="🗑", width=30, height=22, fg_color="#5a1a1a",
                              font=ctk.CTkFont(size=10), command=_borrar).pack(side="right", padx=2)

        def crear_o_guardar():
            nombre = ent_nombre_m.get().strip()
            if not nombre or not pasos_state["lista"]:
                self.app.set_estado("⚠️ Rellena nombre y añade al menos un paso.", "#e67e22")
                return
            actual = prefs.get("macros", [])
            nueva = {"nombre": nombre, "pasos": list(pasos_state["lista"])}
            if edit_state["idx"] is not None:
                # Modo editar: reemplazar la macro existente
                idx = edit_state["idx"]
                if 0 <= idx < len(actual):
                    actual[idx] = nueva
                self.app.set_estado(f"💾 Macro '{nombre}' actualizada", "#2ecc71")
            else:
                # Modo crear: añadir nueva al final
                actual.append(nueva)
                self.app.set_estado(f"✅ Macro '{nombre}' creada", "#2ecc71")
            prefs["macros"] = actual
            self.app.store.guardar_preferencias(prefs)
            _cancelar_edicion()
            refrescar()

        btn_crear = ctk.CTkButton(form, text="✅ Crear macro", width=160, height=28,
                                   fg_color="#1a7a3c",
                                   font=ctk.CTkFont(size=10, weight="bold"),
                                   command=crear_o_guardar)
        btn_crear.pack(pady=(4, 8))

        _refrescar_pasos()
        refrescar()

    def _ejecutar_macro(self, macro, acciones_disponibles):
        """Ejecuta una macro paso a paso."""
        pasos = macro.get("pasos", [])
        if not pasos: return

        self.app.set_estado(f"⚡ Ejecutando macro '{macro.get('nombre', '?')}' ({len(pasos)} pasos)...", "#f39c12")

        def _ejecutar_paso(idx):
            if idx >= len(pasos):
                self.app.set_estado(f"✅ Macro '{macro.get('nombre', '?')}' completada", "#2ecc71")
                self.app._sonar_completado()
                return
            label = pasos[idx]
            accion_id = acciones_disponibles.get(label, "")
            self.app.set_estado(f"⚡ Paso {idx+1}/{len(pasos)}: {label}", "#3498db")
            try:
                if accion_id == "generar":
                    self.app.cmd_prompt()
                elif accion_id == "idea_auto":
                    self._cmd_idea_auto_en_macro()
                elif accion_id == "variacion_auto":
                    self._cmd_variacion_auto_en_macro()
                elif accion_id == "refinar":
                    self.app.refinar.cmd_refinar()
                elif accion_id == "refinar_cinematografico":
                    self.app.refinar.refinar_con_instruccion("más cinematográfico, con encuadre épico, movimientos de cámara dramáticos, iluminación de película")
                elif accion_id == "refinar_facial":
                    self.app.refinar.refinar_con_instruccion("más detalle facial, ojos detallados, textura de piel realista, expresión emotiva")
                elif accion_id == "refinar_iluminacion":
                    self.app.refinar.refinar_con_instruccion("iluminación más profesional, luces volumétricas, ambiente atmosférico, dirección de luz definida")
                elif accion_id == "refinar_simplificar":
                    self.app.refinar.refinar_con_instruccion("más simple y conciso. Elimina redundancias, tags innecesarios.")
                elif accion_id == "refinar_mejorado":
                    self.app.refinar.refinar_con_instruccion("mejorar calidad general, añadir más detalle, optimizar estructura del prompt")
                elif accion_id == "negative_optimo":
                    self.app._cmd_negative_optimo()
                elif accion_id == "negative_builder":
                    self.app._cmd_negative_builder()
                elif accion_id == "scoring_auto":
                    self._cmd_scoring_auto_en_macro()
                elif accion_id == "sugerir_estilos":
                    self.app._cmd_sugerir_estilos()
                elif accion_id == "guardar_favorito":
                    self.app._guardar_favorito()
                elif accion_id == "guardar_estrella":
                    self.app._guardar_estrella()
                elif accion_id == "traducir":
                    self.app.analysis.traducir_salida()
                elif accion_id == "copiar_pos":
                    self.app._copiar("positivo")
                elif accion_id == "copiar_neg":
                    self.app._copiar("negativo")
                elif accion_id == "limpiar":
                    self.app.actualizar_salida("")
                elif accion_id == "previsualizar":
                    self.app.cmd_previsualizar()
                    self.app.after(18000, lambda: _ejecutar_paso(idx + 1))
                    return
            except Exception as e:
                self.app.set_estado(f"⚠️ Paso falló: {e}", "#e74c3c")
            self.app.after(6000, lambda: _ejecutar_paso(idx + 1))

        _ejecutar_paso(0)

    def _cmd_scoring_auto_en_macro(self):
        """Scoring automático sin abrir ventana - aplica el mejor prompt directamente."""
        actual = self.app.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.app.set_estado("⚠️ Genera un prompt primero para scoring.", "#e67e22")

        # Guardar versión antes de modificar (por seguridad)
        try:
            if not hasattr(self.app, '_versiones_prompt'):
                self.app._versiones_prompt = []
            if not (self.app._versiones_prompt and self.app._versiones_prompt[-1]["texto"] == actual):
                self.app._versiones_prompt.append({
                    "texto": actual,
                    "etiqueta": f"v{len(self.app._versiones_prompt) + 1} (pre-scoring)",
                    "timestamp": datetime.datetime.now().isoformat(),
                })
                if len(self.app._versiones_prompt) > 30:
                    self.app._versiones_prompt = self.app._versiones_prompt[-30:]
        except Exception as _e:
            logger.debug(f"[silent] {_e}")

        peticion = (
            f"Analiza este prompt y mejora la versión automáticamente.\n\n"
            f"PROMPT:\n{actual}\n\n"
            f"Responde SOLO con el prompt mejorado, en el mismo formato (tags o natural)."
        )

        def _worker():
            try:
                resp = self.app.deepseek.generar(peticion, temperature=0.3, max_tokens=2000)
                resp = limpiar_marcadores(resp)
                self.app.after(0, lambda: self.app.actualizar_salida(resp))
                self.app.after(0, lambda: self.app.set_estado("📊 Scoring aplicado: prompt mejorado (versión anterior guardada)", "#2ecc71"))
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.set_estado(f"⚠️ Error en scoring: {e}", "#e74c3c"))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_idea_auto_en_macro(self):
        """Genera 1 idea directamente sin popup - para macros."""
        idea = self.app.txt_idea.get("1.0", "end").strip()
        tipo = "canción" if self.app.modo_var.get() == "audio" else "vídeo" if self.app.modo_var.get() == "video" else "imagen"
        estilos = self.app.footer.estilos_texto()
        peticion = f"Genera UNA sola idea para {tipo}. Estilos: {estilos}"
        if idea:
            peticion += f" Tema: {idea}"
        peticion += "\nResponde SOLO con la idea, sin numeración ni explicaciones."

        def _worker():
            try:
                resp = self.app.deepseek.generar(peticion, temperature=0.7, max_tokens=200)
                resp = limpiar_marcadores(resp).strip()
                self.app.after(0, lambda: self.app.txt_idea.insert("1.0", resp + "\n\n"))
                self.app.after(0, lambda: self.app.set_estado("💡 Idea generada (macro)", "#2ecc71"))
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.set_estado(f"⚠️ Error: {e}", "#e74c3c"))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_variacion_auto_en_macro(self):
        """Genera 1 variación directamente sin popup - para macros."""
        actual = self.app.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.app.set_estado("⚠️ Genera un prompt primero.", "#e67e22")

        peticion = (
            f"Crea una variación de este prompt manteniendo la esencia pero cambiando estilo/enfoque:\n\n"
            f"{actual}\n\n"
            f"Responde SOLO con el nuevo prompt variado, en el mismo formato."
        )

        def _worker():
            try:
                resp = self.app.deepseek.generar(peticion, temperature=0.7, max_tokens=1500)
                resp = limpiar_marcadores(resp)
                self.app.after(0, lambda: self.app.actualizar_salida(resp))
                self.app.after(0, lambda: self.app.set_estado("🔄 Variación generada (macro)", "#2ecc71"))
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.set_estado(f"⚠️ Error: {e}", "#e74c3c"))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_proyectos(self):
        """Sistema de proyectos con setup propio: organiza prompts y guarda configuración por proyecto."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        prefs = self.app.store.cargar_preferencias()
        # ── Migración automática: strings → dicts ──
        proyectos_raw = prefs.get("proyectos", [])
        proyectos = {}
        if isinstance(proyectos_raw, list):
            # Formato antiguo: lista de strings
            for nombre in proyectos_raw:
                if isinstance(nombre, str):
                    proyectos[nombre] = {"setup": None, "_creado": ""}
        elif isinstance(proyectos_raw, dict):
            proyectos = proyectos_raw
        # Guardar en formato nuevo si hubo migración
        if proyectos != proyectos_raw:
            prefs["proyectos"] = proyectos
            self.app.store.guardar_preferencias(prefs)

        vent = GPromptWindow(self.app)
        vent.title("🏷 Proyectos")
        vent.geometry("680x600")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text="🏷 Sistema de proyectos",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text="Organiza tus prompts en proyectos. Cada proyecto puede tener su propio setup.",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 10))

        # Indicador del proyecto activo
        activo = prefs.get("proyecto_activo", "")
        lbl_activo = ctk.CTkLabel(vent, text=f"📌 Proyecto activo: {activo or '(ninguno)'}",
                                    font=ctk.CTkFont(size=12, weight="bold"),
                                    text_color="#2ecc71" if activo else c["muted_text"])
        lbl_activo.pack(pady=5)

        # Form crear proyecto
        f_crear = ctk.CTkFrame(vent, fg_color=c["fg_dark"])
        f_crear.pack(fill="x", padx=10, pady=5)
        ent_proy = ctk.CTkEntry(f_crear, placeholder_text="Nombre del proyecto (ej: 'Campaña café orgánico')", width=420)
        ent_proy.pack(side="left", padx=10, pady=8)

        def _crear_proy():
            nombre = ent_proy.get().strip()
            if not nombre: return
            prefs2 = self.app.store.cargar_preferencias()
            proys = prefs2.get("proyectos", {}) or {}
            if not isinstance(proys, dict): proys = {}
            if nombre not in proys:
                proys[nombre] = {
                    "setup": None,
                    "_creado": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                prefs2["proyectos"] = proys
                self.app.store.guardar_preferencias(prefs2)
            ent_proy.delete(0, "end")
            refrescar()

        ctk.CTkButton(f_crear, text="➕ Crear", width=80, height=28, fg_color="#1a7a3c",
                      command=_crear_proy).pack(side="left", padx=4)

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        def refrescar():
            for w in scroll.winfo_children(): w.destroy()
            prefs_act = self.app.store.cargar_preferencias()
            proys = prefs_act.get("proyectos", {}) or {}
            if not isinstance(proys, dict): proys = {}
            activo_a = prefs_act.get("proyecto_activo", "")
            if not proys:
                ctk.CTkLabel(scroll, text="Aún no tienes proyectos. Crea el primero arriba.",
                             font=ctk.CTkFont(size=11), text_color="#666666").pack(pady=20)
                return

            # Opción "Sin proyecto"
            card = ctk.CTkFrame(scroll, fg_color=c["fg_dark"] if not activo_a else c["fg_frame"], corner_radius=6)
            card.pack(fill="x", pady=2)
            ctk.CTkLabel(card, text="📌 (Sin proyecto activo)", font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=c["muted_text"]).pack(side="left", padx=10, pady=6)

            def _activar_ninguno():
                p2 = self.app.store.cargar_preferencias()
                p2["proyecto_activo"] = ""
                self.app.store.guardar_preferencias(p2)
                lbl_activo.configure(text="📌 Proyecto activo: (ninguno)", text_color=c["muted_text"])
                refrescar()
                self.app.set_estado("📌 Sin proyecto activo")

            ctk.CTkButton(card, text="✅ Activar", width=80, height=22, fg_color="#1a4a5a",
                          font=ctk.CTkFont(size=10), command=_activar_ninguno).pack(side="right", padx=8, pady=4)

            for nombre_p in sorted(proys.keys()):
                proy_data = proys.get(nombre_p) or {}
                if not isinstance(proy_data, dict): proy_data = {}
                es_activo = (nombre_p == activo_a)
                tiene_setup = bool(proy_data.get("setup"))
                card = ctk.CTkFrame(scroll, fg_color=c["fg_dark"] if es_activo else c["fg_frame"], corner_radius=6)
                card.pack(fill="x", pady=2)

                # Cabecera con nombre
                hdr = ctk.CTkFrame(card, fg_color="transparent")
                hdr.pack(fill="x", padx=10, pady=(6, 2))
                badge_setup = "  💾" if tiene_setup else ""
                ctk.CTkLabel(hdr, text=f"🏷 {nombre_p}{badge_setup}{'  ← ACTIVO' if es_activo else ''}",
                             font=ctk.CTkFont(size=11, weight="bold" if es_activo else "normal"),
                             text_color="#2ecc71" if es_activo else c["hdr_text"]).pack(side="left")

                # Resumen del setup si existe
                if tiene_setup:
                    s = proy_data.get("setup", {})
                    resumen = f"  · {s.get('modo', '?')} · {s.get('plataforma', '—')} · {s.get('modelo', '—')}"
                    if s.get("ratio"): resumen += f" · {s.get('ratio')}"
                    n_est = len(s.get("estilos") or [])
                    n_neg = len(s.get("negatives") or [])
                    if n_est: resumen += f" · 🎨 {n_est}"
                    if n_neg: resumen += f" · 🚫 {n_neg}"
                    ctk.CTkLabel(card, text=resumen, font=ctk.CTkFont(size=9),
                                 text_color="#888", anchor="w").pack(fill="x", padx=14, pady=(0, 2))

                # Botones de acción
                btn_row = ctk.CTkFrame(card, fg_color="transparent")
                btn_row.pack(fill="x", padx=10, pady=(2, 6))

                def _activar(n=nombre_p):
                    p2 = self.app.store.cargar_preferencias()
                    p2["proyecto_activo"] = n
                    self.app.store.guardar_preferencias(p2)
                    lbl_activo.configure(text=f"📌 Proyecto activo: {n}", text_color="#2ecc71")
                    refrescar()
                    self.app.set_estado(f"🏷 Proyecto '{n}' activado", "#2ecc71")

                def _guardar_setup_proy(n=nombre_p):
                    """Guarda el setup actual en este proyecto."""
                    setup = self._capturar_setup_actual()
                    if not setup:
                        self.app.set_estado("⚠️ No se pudo capturar la configuración", "#e67e22")
                        return
                    p2 = self.app.store.cargar_preferencias()
                    proys2 = p2.get("proyectos", {}) or {}
                    if not isinstance(proys2, dict): proys2 = {}
                    if n not in proys2: proys2[n] = {}
                    proys2[n]["setup"] = setup
                    proys2[n]["_setup_fecha"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    p2["proyectos"] = proys2
                    self.app.store.guardar_preferencias(p2)
                    self.app.set_estado(f"💾 Setup guardado en '{n}'", "#2ecc71")
                    refrescar()

                def _aplicar_setup_proy(n=nombre_p):
                    """Aplica el setup de este proyecto a la UI actual."""
                    p2 = self.app.store.cargar_preferencias()
                    proys2 = p2.get("proyectos", {}) or {}
                    proy = proys2.get(n) or {}
                    setup = proy.get("setup") if isinstance(proy, dict) else None
                    if not setup:
                        self.app.set_estado(f"⚠️ El proyecto '{n}' no tiene setup guardado", "#e67e22")
                        return
                    self._aplicar_setup(setup)
                    self.app.set_estado(f"🔄 Setup de '{n}' aplicado", "#2ecc71")
                    vent.destroy()

                def _borrar_setup_proy(n=nombre_p):
                    p2 = self.app.store.cargar_preferencias()
                    proys2 = p2.get("proyectos", {}) or {}
                    if n in proys2 and isinstance(proys2[n], dict):
                        proys2[n]["setup"] = None
                        proys2[n].pop("_setup_fecha", None)
                        p2["proyectos"] = proys2
                        self.app.store.guardar_preferencias(p2)
                        refrescar()

                def _borrar(n=nombre_p):
                    if not messagebox.askyesno("Borrar proyecto", f"¿Borrar el proyecto '{n}'?\nLa acción no se puede deshacer.", parent=vent): return
                    p2 = self.app.store.cargar_preferencias()
                    proys2 = p2.get("proyectos", {}) or {}
                    proys2.pop(n, None)
                    if p2.get("proyecto_activo") == n:
                        p2["proyecto_activo"] = ""
                        lbl_activo.configure(text="📌 Proyecto activo: (ninguno)", text_color=c["muted_text"])
                    p2["proyectos"] = proys2
                    self.app.store.guardar_preferencias(p2)
                    refrescar()

                if not es_activo:
                    ctk.CTkButton(btn_row, text="✅ Activar", width=70, height=24, fg_color="#1a7a3c",
                                  font=ctk.CTkFont(size=10), command=_activar).pack(side="left", padx=2)
                if tiene_setup:
                    ctk.CTkButton(btn_row, text="🔄 Aplicar setup", width=110, height=24, fg_color="#1e5f3a",
                                  hover_color="#16492d",
                                  font=ctk.CTkFont(size=10), command=_aplicar_setup_proy).pack(side="left", padx=2)
                    ctk.CTkButton(btn_row, text="🗑 setup", width=70, height=24, fg_color="#5a4a1a",
                                  font=ctk.CTkFont(size=10), command=_borrar_setup_proy).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text="💾 Guardar setup actual", width=160, height=24, fg_color="#1a4a5a",
                              font=ctk.CTkFont(size=10), command=_guardar_setup_proy).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text="🗑", width=28, height=24, fg_color="#5a1a1a",
                              font=ctk.CTkFont(size=10), command=_borrar).pack(side="right", padx=2)

        refrescar()

    # A/B Testing 2x2 + Comparador de modelos:
    # extraídos a AbTestingMixin (modules/ab_testing.py).

    def _aplicar_atajo_tags(self, tags_a_anadir):
        """Añade tags al final del POSITIVE del resultado actual."""
        texto = self.app.txt_salida.get("1.0", "end").strip()
        if not texto:
            return self.app.set_estado("⚠️ Genera un prompt primero.", "#e67e22")
        pos = self.app.extraer_positive() or texto
        neg = self.app.extraer_negative()

        # Añadir al final del positive
        nuevo_pos = pos.rstrip(", \n")
        nuevo_pos = f"{nuevo_pos}, {tags_a_anadir}"

        nuevo = f"POSITIVE PROMPT: {nuevo_pos}"
        if neg:
            nuevo += f"\nNEGATIVE PROMPT: {neg}"
        self.app.actualizar_salida(nuevo)
        self.app.set_estado(f"✨ Tags añadidos: {tags_a_anadir[:50]}...", "#2ecc71")
