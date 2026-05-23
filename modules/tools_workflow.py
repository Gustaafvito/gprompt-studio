"""Workflow Tools Mixin - Setup management, Macros, A/B Testing, Cron, Projects, Session Recording, etc."""
import os
import re
import json
import logging
import threading
import datetime
import random
import pyperclip

logger = logging.getLogger(__name__)
from collections import Counter
from tkinter import messagebox, filedialog
import customtkinter as ctk
import tkinter as tk
from config import MODELOS_IMAGEN_FLAT, MODELOS_VIDEO_FLAT, MODELOS_AUDIO_FLAT, get_image_model_specs, get_model_specs, get_audio_model_specs
from config import get_theme_colors as _get_tc
from workers import limpiar_marcadores
from typing import TYPE_CHECKING
from modules.gprompt_window import GPromptWindow

if TYPE_CHECKING:
    from app import ArquitectoApp

class ToolsWorkflowMixin:
    """Mixin containing all workflow tool methods."""

    def _capturar_setup_actual(self):
        """Devuelve un dict con la configuración actual (modelo, plataforma, ratio, estilos, negatives, etc.)."""
        try:
            estilos_sel = []
            if hasattr(self, "estilo_checks"):
                for nombre, var in self.estilo_checks.items():
                    try:
                        if var.get(): estilos_sel.append(nombre)
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            negatives_sel = []
            if hasattr(self, "preset_vars"):
                for nombre, var in self.preset_vars.items():
                    try:
                        if var.get(): negatives_sel.append(nombre)
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            modelo = ""
            modo = self.modo_var.get() if hasattr(self, "modo_var") else "imagen"
            if modo == "imagen" and hasattr(self, "combo_modelo_imagen"):
                modelo = self.combo_modelo_imagen.get() or ""
            elif modo == "video" and hasattr(self, "combo_modelo_video"):
                modelo = self.combo_modelo_video.get() or ""
            elif modo == "audio" and hasattr(self, "combo_modelo_audio"):
                modelo = self.combo_modelo_audio.get() or ""
            setup = {
                "modo": modo,
                "modelo": modelo,
                "plataforma": self.plataforma_var.get() if hasattr(self, "plataforma_var") else "",
                "ratio": self.ratio_var.get() if hasattr(self, "ratio_var") else "",
                "destino": self.destino_var.get() if hasattr(self, "destino_var") else "",
                "personaje": self.combo_personaje.get() if hasattr(self, "combo_personaje") else "",
                "lora": self.combo_lora.get() if hasattr(self, "combo_lora") else "",
                "estilos": estilos_sel,
                "negatives": negatives_sel,
                "nsfw": bool(self.switch_nsfw_var.get()) if hasattr(self, "switch_nsfw_var") else False,
                "auto_trad": bool(self.switch_traduccion_var.get()) if hasattr(self, "switch_traduccion_var") else False,
            }
            return setup
        except Exception:
            return {}

    def _aplicar_setup(self, setup):
        """Aplica un setup guardado a la UI actual."""
        if not setup or not isinstance(setup, dict): return
        try: self._sesion_log(f"🔄 Aplicó setup ({setup.get('modo', '?')} · {setup.get('plataforma', '—')} · {setup.get('modelo', '—')})")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        try:
            # Modo primero (cambia paneles disponibles)
            if setup.get("modo") and hasattr(self, "modo_var"):
                self.modo_var.set(setup["modo"])
                if hasattr(self, "_on_modo_cambio"):
                    try: self._on_modo_cambio()
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            # Plataforma
            if setup.get("plataforma") and hasattr(self, "plataforma_var"):
                self.plataforma_var.set(setup["plataforma"])
                if hasattr(self, "_on_plataforma_cambio"):
                    try: self._on_plataforma_cambio()
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            # Modelo (según modo)
            modo = setup.get("modo", "imagen")
            modelo = setup.get("modelo", "")
            if modelo:
                if modo == "imagen" and hasattr(self, "combo_modelo_imagen"):
                    self.combo_modelo_imagen.set(modelo)
                    if hasattr(self, "_on_modelo_imagen_cambio"):
                        try: self._on_modelo_imagen_cambio()
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
                elif modo == "video" and hasattr(self, "combo_modelo_video"):
                    self.combo_modelo_video.set(modelo)
                    if hasattr(self, "_on_motor_cambio"):
                        try: self._on_motor_cambio()
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
                elif modo == "audio" and hasattr(self, "combo_modelo_audio"):
                    self.combo_modelo_audio.set(modelo)
                    if hasattr(self, "_on_motor_audio_cambio"):
                        try: self._on_motor_audio_cambio()
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
            # Ratio, destino
            for key, attr in [("ratio", "ratio_var"), ("destino", "destino_var")]:
                v = setup.get(key)
                if v and hasattr(self, attr):
                    try: getattr(self, attr).set(v)
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            # Personaje y LoRA (son combos directos)
            if setup.get("personaje") and hasattr(self, "combo_personaje"):
                try: self.combo_personaje.set(setup["personaje"])
                except Exception as e:
                    logger.debug(f"[silent] {e}")
            if setup.get("lora") and hasattr(self, "combo_lora"):
                try: self.combo_lora.set(setup["lora"])
                except Exception as e:
                    logger.debug(f"[silent] {e}")
            if "nsfw" in setup and hasattr(self, "switch_nsfw_var"):
                try: self.switch_nsfw_var.set(bool(setup["nsfw"]))
                except Exception as e:
                    logger.debug(f"[silent] {e}")
            if "auto_trad" in setup and hasattr(self, "switch_traduccion_var"):
                try:
                    self.switch_traduccion_var.set(bool(setup["auto_trad"]))
                    if hasattr(self, "_sw_trad_callback"):
                        try: self._sw_trad_callback()
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
                except Exception as e:
                    logger.debug(f"[silent] {e}")
            # Estilos
            estilos_sel = set(setup.get("estilos", []))
            if hasattr(self, "estilo_checks"):
                for nombre, var in self.estilo_checks.items():
                    try: var.set(nombre in estilos_sel)
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            # Negatives
            negatives_sel = set(setup.get("negatives", []))
            if hasattr(self, "preset_vars"):
                for nombre, var in self.preset_vars.items():
                    try: var.set(nombre in negatives_sel)
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            # Refrescar negative textbox
            if hasattr(self, "_rebuild_negative_text"):
                try: self._rebuild_negative_text()
                except Exception as e:
                    logger.debug(f"[silent] {e}")
        except Exception as e:
            self.set_estado(f"⚠️ Error aplicando setup: {e}", "#e74c3c")

    def _cmd_guardar_setup(self):
        """Abre diálogo para nombrar y guardar el setup actual."""
        from tkinter import simpledialog
        setup = self._capturar_setup_actual()
        if not setup:
            self.set_estado("⚠️ No se pudo capturar la configuración", "#e67e22")
            return
        nombre = simpledialog.askstring("💾 Guardar setup",
                                          "Nombre para este setup:\n(modelo, plataforma, ratio, estilos, negatives…)",
                                          parent=self)
        if not nombre or not nombre.strip(): return
        nombre = nombre.strip()[:60]
        # Cargar setups existentes
        prefs = self.store.cargar_preferencias()
        setups = prefs.get("setups", {}) or {}
        # Confirmación si ya existe
        if nombre in setups:
            from tkinter import messagebox
            if not messagebox.askyesno("Sobrescribir",
                                         f"Ya existe un setup llamado '{nombre}'. ¿Sobrescribirlo?",
                                         parent=self):
                return
        setup["_fecha_guardado"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        setups[nombre] = setup
        prefs["setups"] = setups
        self.store.guardar_preferencias(prefs)
        self.set_estado(f"💾 Setup '{nombre}' guardado", "#2ecc71")
        try: self._sesion_log(f"💾 Guardó setup: {nombre}")
        except Exception as e:
            logger.debug(f"[silent] {e}")

    def _cmd_cargar_setup(self):
        """Abre ventana con la lista de setups guardados para elegir uno."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        prefs = self.store.cargar_preferencias()
        setups = prefs.get("setups", {}) or {}
        if not setups:
            self.set_estado("⚠️ No hay setups guardados todavía. Pulsa '💾 Setup' para guardar el actual.", "#e67e22")
            return
        v = GPromptWindow(self)
        v.title("📋 Cargar setup")
        v.geometry("560x520")
        v.transient(self)
        ctk.CTkLabel(v, text="📋 Setups guardados", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 8))
        scroll = ctk.CTkScrollableFrame(v, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        def _refrescar_lista():
            for w in scroll.winfo_children(): w.destroy()
            setups_act = self.store.cargar_preferencias().get("setups", {}) or {}
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
                    self.set_estado(f"📋 Setup '{n}' aplicado", "#2ecc71")
                    v.destroy()

                def _borrar(n=nombre):
                    from tkinter import messagebox
                    if messagebox.askyesno("Borrar setup", f"¿Borrar el setup '{n}'?", parent=v):
                        prefs2 = self.store.cargar_preferencias()
                        setups2 = prefs2.get("setups", {}) or {}
                        setups2.pop(n, None)
                        prefs2["setups"] = setups2
                        self.store.guardar_preferencias(prefs2)
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
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            self.set_estado("⚠️ Escribe una idea base primero.", "#e67e22")
            return

        vent = GPromptWindow(self)
        vent.title("⏲ Cron de variantes")
        vent.geometry("520x620")
        vent.transient(self)

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
                self.set_estado("⚠️ Cantidad (1-50) e intervalo (0.1-120 min)", "#e67e22")
                return

            cron_state["activo"] = True
            cron_state["actuales"] = 0
            cron_state["generados"] = []
            aspecto = var_aspecto.get()
            personalizado = ent_personalizado.get().strip()
            modo = self.modo_var.get()
            estilos = self.estilos_texto()

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
                    resp = self.deepseek.generar(peticion, temperature=0.9, max_tokens=1500)
                    resp = limpiar_marcadores(resp)

                    # Eliminar negative si el modelo no lo soporta
                    specs = self.get_current_model_specs()
                    if specs and not specs.get("has_negative", True):
                        import re
                        resp = re.sub(r'\n?\s*NEGATIVE\s+PROMPT\s*:.*?$', '', resp, flags=re.DOTALL | re.IGNORECASE).strip()

                    cron_state["generados"].append(resp)
                    self.guardar_en_historial(resp)

                    def _aplicar():
                        if cron_state["cerrada"]:
                            return
                        self.actualizar_salida(resp)
                        progreso = f"⏲ Variante {num}/{cantidad} generada · próxima en {int(intervalo)}min"
                        if num >= cantidad:
                            progreso = f"✅ Cron completado: {cantidad} variantes generadas"
                        _safe_configure(lbl_progreso, text=progreso,
                                        text_color="#2ecc71" if num >= cantidad else "#3498db")
                        self.set_estado(f"⏲ Variante {num}/{cantidad} lista", "#3498db")
                    self.after(0, _aplicar)
                except Exception as e:
                    self.after(0, lambda: _safe_configure(lbl_progreso,
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
            self.set_estado(f"⏲ Cron iniciado: {cantidad} variantes cada {intervalo}min", "#2ecc71")

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
                self._abrir_comparador(cron_state["generados"])
            else:
                self.set_estado("⚠️ Aún no hay variantes generadas", "#e67e22")

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
        actual = self.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20: return
        if not hasattr(self, '_versiones_prompt'):
            self._versiones_prompt = []
        # Evitar duplicados consecutivos
        if self._versiones_prompt and self._versiones_prompt[-1]["texto"] == actual:
            return
        self._versiones_prompt.append({
            "texto": actual,
            "fecha": datetime.datetime.now().strftime("%H:%M:%S"),
            "etiqueta": f"v{len(self._versiones_prompt) + 1}",
        })
        # Limitar historial a 30 versiones por sesión
        if len(self._versiones_prompt) > 30:
            self._versiones_prompt = self._versiones_prompt[-30:]

    def _cmd_versiones_prompt(self):
        """Muestra el historial de versiones del prompt actual (rollback)."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        if not hasattr(self, '_versiones_prompt') or not self._versiones_prompt:
            return self.set_estado("⚠️ No hay versiones aún. Genera/refina prompts para crear versiones.", "#e67e22")

        vent = GPromptWindow(self)
        vent.title("📜 Historial de versiones del prompt")
        vent.geometry("700x500")
        vent.transient(self)

        ctk.CTkLabel(vent, text=f"📜 {len(self._versiones_prompt)} versiones en esta sesión",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text="Click en una versión para restaurarla",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=5)

        # Mostrar de más reciente a más antiguo
        for i, ver in enumerate(reversed(self._versiones_prompt)):
            num = len(self._versiones_prompt) - i
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
                self.actualizar_salida(t)
                vent.destroy()
                self.set_estado(f"⏪ Versión restaurada", "#2ecc71")
            ctk.CTkButton(btn_row, text="⏪ Restaurar esta", width=130, height=22, fg_color="#1a7a3c",
                          font=ctk.CTkFont(size=10), command=_restaurar).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text="📋 Copiar", width=80, height=22, fg_color=c["fg_dark"],
                          font=ctk.CTkFont(size=10),
                          command=lambda t=ver["texto"]: pyperclip.copy(t)).pack(side="left", padx=2)

    def _abrir_macros(self):
        """Macros: secuencias de acciones automatizadas."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        prefs = self.store.cargar_preferencias()
        macros = prefs.get("macros", [])

        vent = GPromptWindow(self)
        vent.title("⚡ Macros — Secuencias automatizadas")
        vent.geometry("700x600")
        vent.transient(self)

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
                        self.store.guardar_preferencias(prefs)
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
                self.set_estado("⚠️ Rellena nombre y añade al menos un paso.", "#e67e22")
                return
            actual = prefs.get("macros", [])
            nueva = {"nombre": nombre, "pasos": list(pasos_state["lista"])}
            if edit_state["idx"] is not None:
                # Modo editar: reemplazar la macro existente
                idx = edit_state["idx"]
                if 0 <= idx < len(actual):
                    actual[idx] = nueva
                self.set_estado(f"💾 Macro '{nombre}' actualizada", "#2ecc71")
            else:
                # Modo crear: añadir nueva al final
                actual.append(nueva)
                self.set_estado(f"✅ Macro '{nombre}' creada", "#2ecc71")
            prefs["macros"] = actual
            self.store.guardar_preferencias(prefs)
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

        self.set_estado(f"⚡ Ejecutando macro '{macro.get('nombre', '?')}' ({len(pasos)} pasos)...", "#f39c12")

        def _ejecutar_paso(idx):
            if idx >= len(pasos):
                self.set_estado(f"✅ Macro '{macro.get('nombre', '?')}' completada", "#2ecc71")
                self._sonar_completado()
                return
            label = pasos[idx]
            accion_id = acciones_disponibles.get(label, "")
            self.set_estado(f"⚡ Paso {idx+1}/{len(pasos)}: {label}", "#3498db")
            try:
                if accion_id == "generar":
                    self.cmd_prompt()
                elif accion_id == "idea_auto":
                    self._cmd_idea_auto_en_macro()
                elif accion_id == "variacion_auto":
                    self._cmd_variacion_auto_en_macro()
                elif accion_id == "refinar":
                    self.cmd_refinar()
                elif accion_id == "refinar_cinematografico":
                    self._refinar_con_instruccion("más cinematográfico, con encuadre épico, movimientos de cámara dramáticos, iluminación de película")
                elif accion_id == "refinar_facial":
                    self._refinar_con_instruccion("más detalle facial, ojos detallados, textura de piel realista, expresión emotiva")
                elif accion_id == "refinar_iluminacion":
                    self._refinar_con_instruccion("iluminación más profesional, luces volumétricas, ambiente atmosférico, dirección de luz definida")
                elif accion_id == "refinar_simplificar":
                    self._refinar_con_instruccion("más simple y conciso. Elimina redundancias, tags innecesarios.")
                elif accion_id == "refinar_mejorado":
                    self._refinar_con_instruccion("mejorar calidad general, añadir más detalle, optimizar estructura del prompt")
                elif accion_id == "negative_optimo":
                    self._cmd_negative_optimo()
                elif accion_id == "negative_builder":
                    self._cmd_negative_builder()
                elif accion_id == "scoring_auto":
                    self._cmd_scoring_auto_en_macro()
                elif accion_id == "sugerir_estilos":
                    self._cmd_sugerir_estilos()
                elif accion_id == "guardar_favorito":
                    self._guardar_favorito()
                elif accion_id == "guardar_estrella":
                    self._guardar_estrella()
                elif accion_id == "traducir":
                    self._traducir_salida()
                elif accion_id == "copiar_pos":
                    self._copiar("positivo")
                elif accion_id == "copiar_neg":
                    self._copiar("negativo")
                elif accion_id == "limpiar":
                    self.actualizar_salida("")
                elif accion_id == "previsualizar":
                    self.cmd_previsualizar()
                    self.after(18000, lambda: _ejecutar_paso(idx + 1))
                    return
            except Exception as e:
                self.set_estado(f"⚠️ Paso falló: {e}", "#e74c3c")
            self.after(6000, lambda: _ejecutar_paso(idx + 1))

        _ejecutar_paso(0)

    def _cmd_scoring_auto_en_macro(self):
        """Scoring automático sin abrir ventana - aplica el mejor prompt directamente."""
        actual = self.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.set_estado("⚠️ Genera un prompt primero para scoring.", "#e67e22")

        # Guardar versión antes de modificar (por seguridad)
        try:
            if not hasattr(self, '_versiones_prompt'):
                self._versiones_prompt = []
            if not (self._versiones_prompt and self._versiones_prompt[-1]["texto"] == actual):
                self._versiones_prompt.append({
                    "texto": actual,
                    "etiqueta": f"v{len(self._versiones_prompt) + 1} (pre-scoring)",
                    "timestamp": datetime.datetime.now().isoformat(),
                })
                if len(self._versiones_prompt) > 30:
                    self._versiones_prompt = self._versiones_prompt[-30:]
        except Exception as _e:
            logger.debug(f"[silent] {_e}")

        peticion = (
            f"Analiza este prompt y mejora la versión automáticamente.\n\n"
            f"PROMPT:\n{actual}\n\n"
            f"Responde SOLO con el prompt mejorado, en el mismo formato (tags o natural)."
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.3, max_tokens=2000)
                resp = limpiar_marcadores(resp)
                self.after(0, lambda: self.actualizar_salida(resp))
                self.after(0, lambda: self.set_estado("📊 Scoring aplicado: prompt mejorado (versión anterior guardada)", "#2ecc71"))
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"⚠️ Error en scoring: {e}", "#e74c3c"))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_idea_auto_en_macro(self):
        """Genera 1 idea directamente sin popup - para macros."""
        idea = self.txt_idea.get("1.0", "end").strip()
        tipo = "canción" if self.modo_var.get() == "audio" else "vídeo" if self.modo_var.get() == "video" else "imagen"
        estilos = self.estilos_texto()
        peticion = f"Genera UNA sola idea para {tipo}. Estilos: {estilos}"
        if idea:
            peticion += f" Tema: {idea}"
        peticion += "\nResponde SOLO con la idea, sin numeración ni explicaciones."

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.7, max_tokens=200)
                resp = limpiar_marcadores(resp).strip()
                self.after(0, lambda: self.txt_idea.insert("1.0", resp + "\n\n"))
                self.after(0, lambda: self.set_estado("💡 Idea generada (macro)", "#2ecc71"))
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"⚠️ Error: {e}", "#e74c3c"))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_variacion_auto_en_macro(self):
        """Genera 1 variación directamente sin popup - para macros."""
        actual = self.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.set_estado("⚠️ Genera un prompt primero.", "#e67e22")

        peticion = (
            f"Crea una variación de este prompt manteniendo la esencia pero cambiando estilo/enfoque:\n\n"
            f"{actual}\n\n"
            f"Responde SOLO con el nuevo prompt variado, en el mismo formato."
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.7, max_tokens=1500)
                resp = limpiar_marcadores(resp)
                self.after(0, lambda: self.actualizar_salida(resp))
                self.after(0, lambda: self.set_estado("🔄 Variación generada (macro)", "#2ecc71"))
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"⚠️ Error: {e}", "#e74c3c"))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_proyectos(self):
        """Sistema de proyectos con setup propio: organiza prompts y guarda configuración por proyecto."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        prefs = self.store.cargar_preferencias()
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
            self.store.guardar_preferencias(prefs)

        vent = GPromptWindow(self)
        vent.title("🏷 Proyectos")
        vent.geometry("680x600")
        vent.transient(self)

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
            prefs2 = self.store.cargar_preferencias()
            proys = prefs2.get("proyectos", {}) or {}
            if not isinstance(proys, dict): proys = {}
            if nombre not in proys:
                proys[nombre] = {
                    "setup": None,
                    "_creado": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                prefs2["proyectos"] = proys
                self.store.guardar_preferencias(prefs2)
            ent_proy.delete(0, "end")
            refrescar()

        ctk.CTkButton(f_crear, text="➕ Crear", width=80, height=28, fg_color="#1a7a3c",
                      command=_crear_proy).pack(side="left", padx=4)

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        def refrescar():
            for w in scroll.winfo_children(): w.destroy()
            prefs_act = self.store.cargar_preferencias()
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
                p2 = self.store.cargar_preferencias()
                p2["proyecto_activo"] = ""
                self.store.guardar_preferencias(p2)
                lbl_activo.configure(text="📌 Proyecto activo: (ninguno)", text_color=c["muted_text"])
                refrescar()
                self.set_estado("📌 Sin proyecto activo")

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
                    p2 = self.store.cargar_preferencias()
                    p2["proyecto_activo"] = n
                    self.store.guardar_preferencias(p2)
                    lbl_activo.configure(text=f"📌 Proyecto activo: {n}", text_color="#2ecc71")
                    refrescar()
                    self.set_estado(f"🏷 Proyecto '{n}' activado", "#2ecc71")

                def _guardar_setup_proy(n=nombre_p):
                    """Guarda el setup actual en este proyecto."""
                    setup = self._capturar_setup_actual()
                    if not setup:
                        self.set_estado("⚠️ No se pudo capturar la configuración", "#e67e22")
                        return
                    p2 = self.store.cargar_preferencias()
                    proys2 = p2.get("proyectos", {}) or {}
                    if not isinstance(proys2, dict): proys2 = {}
                    if n not in proys2: proys2[n] = {}
                    proys2[n]["setup"] = setup
                    proys2[n]["_setup_fecha"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    p2["proyectos"] = proys2
                    self.store.guardar_preferencias(p2)
                    self.set_estado(f"💾 Setup guardado en '{n}'", "#2ecc71")
                    refrescar()

                def _aplicar_setup_proy(n=nombre_p):
                    """Aplica el setup de este proyecto a la UI actual."""
                    p2 = self.store.cargar_preferencias()
                    proys2 = p2.get("proyectos", {}) or {}
                    proy = proys2.get(n) or {}
                    setup = proy.get("setup") if isinstance(proy, dict) else None
                    if not setup:
                        self.set_estado(f"⚠️ El proyecto '{n}' no tiene setup guardado", "#e67e22")
                        return
                    self._aplicar_setup(setup)
                    self.set_estado(f"🔄 Setup de '{n}' aplicado", "#2ecc71")
                    vent.destroy()

                def _borrar_setup_proy(n=nombre_p):
                    p2 = self.store.cargar_preferencias()
                    proys2 = p2.get("proyectos", {}) or {}
                    if n in proys2 and isinstance(proys2[n], dict):
                        proys2[n]["setup"] = None
                        proys2[n].pop("_setup_fecha", None)
                        p2["proyectos"] = proys2
                        self.store.guardar_preferencias(p2)
                        refrescar()

                def _borrar(n=nombre_p):
                    if not messagebox.askyesno("Borrar proyecto", f"¿Borrar el proyecto '{n}'?\nLa acción no se puede deshacer.", parent=vent): return
                    p2 = self.store.cargar_preferencias()
                    proys2 = p2.get("proyectos", {}) or {}
                    proys2.pop(n, None)
                    if p2.get("proyecto_activo") == n:
                        p2["proyecto_activo"] = ""
                        lbl_activo.configure(text="📌 Proyecto activo: (ninguno)", text_color=c["muted_text"])
                    p2["proyectos"] = proys2
                    self.store.guardar_preferencias(p2)
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

    def _sesion_init(self):
        """Inicializa el registro de sesión si no existe."""
        if not hasattr(self, "_sesion_eventos"):
            self._sesion_eventos = []
            self._sesion_grabando = False
            self._sesion_inicio = None
            self._sesion_video_thread = None
            self._sesion_video_path = None
            self._sesion_video_writer = None
            self._sesion_video_running = False

    def _sesion_log(self, evento):
        """Añade un evento al registro si está grabando."""
        self._sesion_init()
        if not self._sesion_grabando: return
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._sesion_eventos.append((ts, evento))

    def _sesion_video_disponible(self):
        """Comprueba si las dependencias para grabar vídeo están instaladas."""
        try:
            import mss  # noqa
            import imageio  # noqa
            return True
        except ImportError:
            return False

    def _sesion_video_iniciar(self, solo_app=False):
        """Arranca la grabación de vídeo en thread separado. solo_app=True captura solo la ventana."""
        if not self._sesion_video_disponible():
            return False
        self._sesion_solo_app = solo_app
        try:
            import mss
            import imageio
            import os
            # Crear directorio de salida si no existe
            output_dir = os.path.join(os.path.expanduser("~"), "GPromptStudio_videos")
            os.makedirs(output_dir, exist_ok=True)
            # Path del vídeo
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self._sesion_video_path = os.path.join(output_dir, f"sesion_{ts}.mp4")
            # Configurar writer (5 FPS, codec H.264)
            self._sesion_video_writer = imageio.get_writer(
                self._sesion_video_path,
                fps=5,
                codec="libx264",
                quality=7,
                pixelformat="yuv420p",
                macro_block_size=1,
            )
            self._sesion_video_running = True
            self._sesion_video_thread = threading.Thread(
                target=self._sesion_video_worker, daemon=True
            )
            self._sesion_video_thread.start()
            return True
        except Exception as e:
            self._sesion_video_writer = None
            self._sesion_video_running = False
            self.set_estado(f"⚠️ Error iniciando vídeo: {e}", "#e74c3c")
            return False

    def _sesion_video_worker(self):
        """Thread worker: captura pantalla a 5 FPS y la pasa al writer."""
        try:
            import mss
            import time
            import numpy as np

            solo_app = getattr(self, '_sesion_solo_app', False)

            with mss.mss() as sct:
                interval = 0.2  # 5 FPS
                next_t = time.time()
                while self._sesion_video_running:
                    if solo_app:
                        # Capturar solo la región de la ventana de la app
                        try:
                            # Obtener posición y tamaño de la ventana
                            x = self.winfo_x()
                            y = self.winfo_y()
                            w = self.winfo_width()
                            h = self.winfo_height()

                            # Ajustar a múltiplo de 2 (H.264 requiere dimensiones pares)
                            w = w if w % 2 == 0 else w - 1
                            h = h if h % 2 == 0 else h - 1

                            # Capturar región
                            monitor = {"left": x, "top": y, "width": w, "height": h}
                            img = sct.grab(monitor)
                        except Exception:
                            # Si falla, capturar toda la pantalla
                            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                            # Ajustar también
                            monitor = dict(monitor)
                            if monitor["width"] % 2 != 0:
                                monitor["width"] -= 1
                            if monitor["height"] % 2 != 0:
                                monitor["height"] -= 1
                            img = sct.grab(monitor)
                    else:
                        # Capturar toda la pantalla
                        monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                        img = sct.grab(monitor)

                    # Convertir BGRA → RGB
                    frame = np.array(img)[:, :, [2, 1, 0]]  # BGRA→RGB
                    try:
                        self._sesion_video_writer.append_data(frame)
                    except Exception:
                        break
                    # Mantener cadencia 5 FPS
                    next_t += interval
                    delta = next_t - time.time()
                    if delta > 0:
                        time.sleep(delta)
                    else:
                        next_t = time.time()
        except Exception as e:
            self.after(0, lambda: self.set_estado(f"⚠️ Vídeo se detuvo: {e}", "#e74c3c"))

    def _sesion_video_detener(self):
        """Detiene grabación y cierra el archivo. Devuelve la ruta del MP4 o None."""
        self._sesion_video_running = False
        # Esperar al thread (max 1.5s)
        if self._sesion_video_thread:
            try: self._sesion_video_thread.join(timeout=1.5)
            except Exception as e:
                logger.debug(f"[silent] {e}")
        # Cerrar writer
        if self._sesion_video_writer:
            try: self._sesion_video_writer.close()
            except Exception as e:
                logger.debug(f"[silent] {e}")
        path = self._sesion_video_path
        self._sesion_video_writer = None
        self._sesion_video_path = None
        self._sesion_video_thread = None
        return path

    def _cmd_sesion_grabar_toggle(self):
        """Inicia / detiene la grabación de sesión (con o sin vídeo según preferencia)."""
        self._sesion_init()
        if not self._sesion_grabando:
            # Preguntar tipo de grabación de vídeo si el switch está ON
            if getattr(self, '_sesion_grabar_video', False):
                if self._sesion_video_disponible():
                    # Ventana de selección
                    sel = GPromptWindow(self)
                    sel.title("🎬 Tipo de grabación")
                    sel.geometry("350x180")
                    sel.transient(self)
                    sel.grab_set()

                    ctk.CTkLabel(sel, text="¿Qué quieres grabar en vídeo?", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(15, 10))
                    ctk.CTkLabel(sel, text="(La grabación de texto siempre está activa)", font=ctk.CTkFont(size=10), text_color="#888").pack(pady=(0, 15))

                    def _iniciar(tipo):
                        self._sesion_tipo_video = tipo
                        sel.destroy()
                        self._iniciar_grabacion(tipo)

                    ctk.CTkButton(sel, text="📱 Solo ventana de la app", width=250, height=35, fg_color="#1a6a3a",
                                  command=lambda: _iniciar("app")).pack(pady=5)
                    ctk.CTkButton(sel, text="🖥️ Toda la pantalla", width=250, height=35, fg_color="#1a4a7a",
                                  command=lambda: _iniciar("pantalla")).pack(pady=5)
                    ctk.CTkButton(sel, text="❌ Sin vídeo (solo texto)", width=250, height=30, fg_color="#5a1a1a",
                                  command=lambda: _iniciar("nada")).pack(pady=5)
                    return
                else:
                    self._sesion_log("⚠️ Vídeo no disponible: instala 'mss' e 'imageio[ffmpeg]'")

            # Sin vídeo o no disponible
            self._iniciar_grabacion("nada")
        else:
            # Parar
            self._sesion_log("⏹ GRABACIÓN DETENIDA")
            self._sesion_grabando = False
            video_path = None
            if self._sesion_video_running or self._sesion_video_writer:
                self.set_estado("⏹ Cerrando vídeo...")
                video_path = self._sesion_video_detener()
            self._cmd_sesion_exportar(video_path=video_path)

    def _iniciar_grabacion(self, tipo_video):
        """Inicia la grabación con el tipo de vídeo especificado.

        `tipo_video`: "nada" | "app" | "pantalla". (La rama `else` previa
        replicaba el código de "parar" del toggle pero era dead code —
        esta función solo se llama desde el flujo de inicio).
        """
        self._sesion_eventos = []
        self._sesion_grabando = True
        self._sesion_inicio = datetime.datetime.now()
        self._sesion_log("🔴 GRABACIÓN INICIADA")

        if tipo_video == "nada":
            self.set_estado("🔴 Grabando sesión (sin vídeo)... Click 🎬 para parar", "#e74c3c")
        elif tipo_video == "app":
            if self._sesion_video_iniciar(solo_app=True):
                self._sesion_log("🎥 Grabación de vídeo (solo app, 5 FPS)")
                self.set_estado("🔴 Grabando sesión + 🎥 app... Click 🎬 para parar", "#e74c3c")
            else:
                self.set_estado("🔴 Grabando solo texto. Click 🎬 para parar", "#e67e22")
        elif tipo_video == "pantalla":
            if self._sesion_video_iniciar(solo_app=False):
                self._sesion_log("🎥 Grabación de vídeo (pantalla completa, 5 FPS)")
                self.set_estado("🔴 Grabando sesión + 🎥 pantalla... Click 🎬 para parar", "#e74c3c")
            else:
                self.set_estado("🔴 Grabando solo texto. Click 🎬 para parar", "#e67e22")

    def _cmd_sesion_exportar(self, video_path=None):
        """Abre ventana con el log de la sesión y opciones de exportación.
        Si video_path está dado, también muestra info del MP4 y botón para abrirlo."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        self._sesion_init()
        if not self._sesion_eventos:
            self.set_estado("⚠️ No hay eventos grabados", "#e67e22")
            return

        v = GPromptWindow(self)
        v.title("🎬 Sesión grabada")
        v.geometry("780x640")
        v.transient(self)

        ctk.CTkLabel(v, text="🎬 Registro de sesión",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4))
        dur = ""
        if self._sesion_inicio:
            delta = datetime.datetime.now() - self._sesion_inicio
            mins = int(delta.total_seconds() // 60)
            secs = int(delta.total_seconds() % 60)
            dur = f"  ·  duración: {mins}m {secs}s"
        ctk.CTkLabel(v, text=f"{len(self._sesion_eventos)} eventos{dur}",
                     font=ctk.CTkFont(size=11), text_color="#888").pack(pady=(0, 4))

        # ── Banner con info del vídeo si se grabó ──
        if video_path:
            import os as _os
            try:
                tam_mb = _os.path.getsize(video_path) / (1024 * 1024)
                video_info = f"🎥 Vídeo guardado: {_os.path.basename(video_path)}  ·  {tam_mb:.1f} MB"
            except Exception:
                video_info = f"🎥 Vídeo guardado: {_os.path.basename(video_path)}"
            video_banner = ctk.CTkFrame(v, fg_color="#1a3a5a", corner_radius=6)
            video_banner.pack(fill="x", padx=15, pady=(0, 8))
            ctk.CTkLabel(video_banner, text=video_info, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=c["hdr_text"]).pack(side="left", padx=12, pady=8)

            def _abrir_carpeta():
                try:
                    import subprocess
                    import sys
                    folder = _os.path.dirname(video_path)
                    if sys.platform == "win32":
                        _os.startfile(folder)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", folder])
                    else:
                        subprocess.run(["xdg-open", folder])
                except Exception as e:
                    self.set_estado(f"⚠️ No se pudo abrir: {e}", "#e74c3c")

            def _abrir_video():
                try:
                    import subprocess
                    import sys
                    if sys.platform == "win32":
                        _os.startfile(video_path)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", video_path])
                    else:
                        subprocess.run(["xdg-open", video_path])
                except Exception as e:
                    self.set_estado(f"⚠️ Error: {e}", "#e74c3c")

            ctk.CTkButton(video_banner, text="📁 Abrir carpeta", width=120, height=24,
                          fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                          command=_abrir_carpeta).pack(side="right", padx=4, pady=6)
            ctk.CTkButton(video_banner, text="▶ Reproducir", width=110, height=24,
                          fg_color="#1e5f3a", hover_color="#16492d",
                          command=_abrir_video).pack(side="right", padx=4, pady=6)

        # Construir texto
        lines_md = ["# Registro de sesión",
                    f"_Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}_",
                    "",
                    "| Hora | Evento |",
                    "| --- | --- |"]
        lines_txt = [f"REGISTRO DE SESIÓN",
                     f"Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
                     "=" * 60, ""]
        for ts, evento in self._sesion_eventos:
            lines_md.append(f"| {ts} | {evento} |")
            lines_txt.append(f"[{ts}]  {evento}")

        texto_md = "\n".join(lines_md)
        texto_txt = "\n".join(lines_txt)

        # Preview
        txt = ctk.CTkTextbox(v, wrap="none", font=ctk.CTkFont(family="Consolas", size=11))
        txt.pack(fill="both", expand=True, padx=15, pady=5)
        txt.insert("1.0", texto_txt)

        btn_row = ctk.CTkFrame(v, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 12))

        def _exp_md():
            ruta = filedialog.asksaveasfilename(
                defaultextension=".md",
                filetypes=[("Markdown", "*.md"), ("Todos", "*.*")],
                initialfile=f"sesion_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.md",
                parent=v)
            if ruta:
                try:
                    with open(ruta, "w", encoding="utf-8") as fp: fp.write(texto_md)
                    self.set_estado(f"📄 Exportado: {ruta}", "#2ecc71")
                except Exception as e:
                    self.set_estado(f"⚠️ Error: {e}", "#e74c3c")

        def _exp_txt():
            ruta = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
                initialfile=f"sesion_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                parent=v)
            if ruta:
                try:
                    with open(ruta, "w", encoding="utf-8") as fp: fp.write(texto_txt)
                    self.set_estado(f"📄 Exportado: {ruta}", "#2ecc71")
                except Exception as e:
                    self.set_estado(f"⚠️ Error: {e}", "#e74c3c")

        def _limpiar():
            if messagebox.askyesno("Limpiar registro", "¿Borrar todos los eventos grabados?", parent=v):
                self._sesion_eventos = []
                self._sesion_inicio = None
                v.destroy()
                self.set_estado("🗑 Registro de sesión limpiado")

        ctk.CTkButton(btn_row, text="📄 Exportar .md", width=130, command=_exp_md,
                      fg_color="#1e5f3a", hover_color="#16492d").pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="📄 Exportar .txt", width=130, command=_exp_txt,
                      fg_color="#1e5f3a", hover_color="#16492d").pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="📚 Modo Tutorial", width=140,
                      command=lambda: self._cmd_sesion_modo_tutorial(),
                      fg_color="#5b2c8e", hover_color="#3d1a6a").pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="🗑 Limpiar", width=110, command=_limpiar,
                      fg_color="#6a1a1a", hover_color="#4a0f0f").pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="Cerrar", width=110, command=v.destroy,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"]).pack(side="right", padx=2)

    def _cmd_sesion_modo_tutorial(self):
        """Modo Tutorial: convierte el log en un guion paso a paso para tutoriales de YouTube."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        if not self._sesion_eventos:
            self.set_estado("⚠️ No hay eventos grabados", "#e67e22")
            return

        # Agrupar eventos en pasos lógicos según los tipos
        pasos = self._sesion_agrupar_pasos(self._sesion_eventos)

        v = GPromptWindow(self)
        v.title("📚 Modo Tutorial — Guion para YouTube")
        v.geometry("900x700")
        v.transient(self)

        ctk.CTkLabel(v, text="📚 Guion de tutorial",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4))
        ctk.CTkLabel(v, text=f"{len(pasos)} pasos · {len(self._sesion_eventos)} acciones",
                     font=ctk.CTkFont(size=11), text_color="#888").pack(pady=(0, 10))

        # Construir el guion
        lines = ["# 📚 Tutorial: " + datetime.datetime.now().strftime("%d/%m/%Y"),
                 "",
                 "_Generado automáticamente desde la sesión grabada de G-Prompt Studio_",
                 ""]
        for i, (titulo, eventos) in enumerate(pasos, 1):
            ts_inicio = eventos[0][0] if eventos else ""
            lines.append(f"## Paso {i}: {titulo}")
            lines.append(f"_{ts_inicio}_")
            lines.append("")
            # Narración explicativa según tipo de paso
            narracion = self._sesion_narrar_paso(titulo, eventos)
            if narracion:
                lines.append(narracion)
                lines.append("")
            # Detalle de acciones
            lines.append("**Acciones detalladas:**")
            for ts, evento in eventos:
                lines.append(f"- `{ts}` {evento}")
            lines.append("")

        guion = "\n".join(lines)

        txt = ctk.CTkTextbox(v, wrap="word", font=ctk.CTkFont(size=11))
        txt.pack(fill="both", expand=True, padx=15, pady=5)
        txt.insert("1.0", guion)

        btn_row = ctk.CTkFrame(v, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 12))

        def _exportar_md():
            ruta = filedialog.asksaveasfilename(
                defaultextension=".md",
                filetypes=[("Markdown", "*.md"), ("Todos", "*.*")],
                initialfile=f"tutorial_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.md",
                parent=v)
            if ruta:
                try:
                    with open(ruta, "w", encoding="utf-8") as fp: fp.write(guion)
                    self.set_estado(f"📄 Tutorial exportado: {ruta}", "#2ecc71")
                except Exception as e:
                    self.set_estado(f"⚠️ Error: {e}", "#e74c3c")

        def _copiar():
            try:
                pyperclip.copy(guion)
                self.set_estado("📋 Guion copiado al portapapeles", "#2ecc71")
            except Exception as e:
                logger.debug(f"[silent] {e}")

        ctk.CTkButton(btn_row, text="📄 Exportar .md", width=130,
                      fg_color="#1e5f3a", hover_color="#16492d",
                      command=_exportar_md).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="📋 Copiar todo", width=130,
                      fg_color="#1e3a5f", hover_color="#162d49",
                      command=_copiar).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="Cerrar", width=110, command=v.destroy,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"]).pack(side="right", padx=2)

    def _sesion_agrupar_pasos(self, eventos):
        """Agrupa eventos consecutivos en pasos lógicos según el tipo de acción.
        Devuelve [(titulo_paso, [eventos]), ...]"""
        pasos = []
        actual_titulo = None
        actual_eventos = []

        # Mapeo: emoji prefijo → categoría de paso
        def categoria(evento):
            e = evento[1] if isinstance(evento, tuple) else evento
            if "🔴 GRABACIÓN" in e or "⏹ GRABACIÓN" in e or "🎥" in e: return None  # ignorar
            if "Cambió modo" in e: return "Configurar modo de trabajo"
            if "Cambió plataforma" in e or "Cambió modelo" in e: return "Seleccionar plataforma y modelo"
            if "Cambió ratio" in e or "Cambió destino" in e or "NSFW" in e or "Brief" in e or "Auto-trad" in e: return "Ajustar parámetros"
            if "Personaje" in e or "LoRA" in e: return "Aplicar personaje/LoRA"
            if "Cargó plantilla" in e: return "Cargar plantilla base"
            if "Cargó imagen" in e: return "Cargar imagen de referencia"
            if "Analizó imagen" in e or "Img→Prompt" in e or "Análisis inverso" in e: return "Analizar imagen"
            if "Pidió ideas" in e or "Sorpréndeme" in e: return "Generar ideas"
            if "Sugerir" in e: return "Pedir sugerencias"
            if "Generó prompt" in e: return "Generar el prompt principal"
            if "Regeneró" in e: return "Regenerar variantes"
            if "Refinó" in e: return "Refinar el prompt"
            if "Variaciones" in e: return "Crear variaciones"
            if "Pulse" in e or "Mood" in e or "Story" in e or "Board" in e or "Walk" in e or "Iterar" in e: return "Exploración creativa"
            if "A/B Testing" in e: return "Probar A/B"
            if "Convirtió prompt" in e: return "Convertir formato"
            if "Comparar" in e: return "Comparar opciones"
            if "Copió" in e or "Ctrl+D" in e: return "Exportar resultado"
            if "Expandió snippet" in e: return "Usar snippet de expansión"
            if "Aplicó setup" in e or "Guardó setup" in e: return "Gestionar setup"
            if "Copiloto" in e: return "Usar Copiloto"
            if "Preview" in e or "Previsualizó" in e: return "Previsualizar"
            if "Reset" in e: return "Reset"
            if "Dashboard" in e: return "Inicio"
            return "Otras acciones"

        for ev in eventos:
            cat = categoria(ev)
            if cat is None: continue  # ignorar inicio/fin de grabación
            if cat != actual_titulo:
                if actual_eventos:
                    pasos.append((actual_titulo, actual_eventos))
                actual_titulo = cat
                actual_eventos = [ev]
            else:
                actual_eventos.append(ev)
        if actual_eventos:
            pasos.append((actual_titulo, actual_eventos))
        return pasos

    def _sesion_narrar_paso(self, titulo, eventos):
        """Genera una narración corta tipo guion para cada tipo de paso."""
        narrativas = {
            "Configurar modo de trabajo": "Empezamos eligiendo el modo de trabajo (imagen, vídeo o audio).",
            "Seleccionar plataforma y modelo": "A continuación seleccionamos la plataforma destino y el modelo que vamos a usar.",
            "Ajustar parámetros": "Ahora ajustamos los parámetros básicos: ratio, destino, NSFW si aplica, etc.",
            "Aplicar personaje/LoRA": "Aplicamos un personaje guardado o un LoRA específico para personalizar el output.",
            "Cargar plantilla base": "Cargamos una plantilla guardada que ya tiene la estructura del prompt.",
            "Cargar imagen de referencia": "Cargamos una imagen de referencia para guiar la generación.",
            "Analizar imagen": "Pedimos a la IA que analice la imagen y nos dé información visual de ella.",
            "Generar ideas": "Pedimos al sistema ideas creativas para arrancar.",
            "Pedir sugerencias": "Pedimos sugerencias automáticas para optimizar el prompt.",
            "Generar el prompt principal": "Aquí es cuando generamos el prompt principal a partir de nuestra idea.",
            "Regenerar variantes": "Si no nos convence, regeneramos manteniendo la idea pero cambiando los detalles.",
            "Refinar el prompt": "Refinamos el prompt para mejorarlo (más detallado, más conciso, etc).",
            "Crear variaciones": "Generamos varias versiones del prompt para tener opciones.",
            "Exploración creativa": "Exploramos creativamente con técnicas avanzadas (Pulse, Mood, Story, etc).",
            "Probar A/B": "Hacemos A/B testing para comparar 4 variantes con dimensiones distintas.",
            "Convertir formato": "Convertimos el prompt entre formatos (imagen → vídeo, etc).",
            "Comparar opciones": "Comparamos resultados de distintos modelos o versiones.",
            "Exportar resultado": "Copiamos el prompt final al portapapeles para usarlo.",
            "Usar snippet de expansión": "Usamos un snippet (`;palabra` + Espacio) para expandir frases comunes.",
            "Gestionar setup": "Guardamos o aplicamos un setup completo para reutilizarlo.",
            "Usar Copiloto": "Abrimos el Copiloto narrativo para conversar con la IA sobre el prompt.",
            "Previsualizar": "Generamos una previsualización rápida para ver el resultado.",
            "Reset": "Limpiamos todo para empezar de cero.",
            "Inicio": "Volvemos a la pantalla de inicio.",
            "Otras acciones": "Realizamos varias acciones sueltas.",
        }
        return narrativas.get(titulo, "")

    AB_DIMENSIONES = {
        "iluminación": ["soft natural light", "harsh dramatic lighting", "neon glow", "golden hour sunset"],
        "mood": ["serene and peaceful", "tense and ominous", "joyful and energetic", "melancholic and quiet"],
        "ángulo": ["close-up portrait", "wide establishing shot", "low-angle hero shot", "overhead bird's-eye"],
        "estilo artístico": ["photorealistic", "oil painting style", "cyberpunk aesthetic", "watercolor illustration"],
        "paleta de color": ["warm orange and red tones", "cool blue and teal palette", "monochrome black and white", "pastel pink and lavender"],
        "detalle": ["minimalist clean composition", "highly detailed intricate", "abstract impressionist", "hyperrealistic ultra-detail"],
    }

    def _cmd_ab_testing(self):
        """A/B testing 2x2: configura dimensiones a variar y genera 4 variantes."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea:
            self.set_estado("⚠️ Escribe una idea primero", "#e67e22")
            return
        try: self._sesion_log("🧪 A/B Testing: abrió configuración 2x2")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        # Ventana de configuración
        cfg = GPromptWindow(self)
        cfg.title("🧪 A/B Testing 2x2")
        cfg.geometry("520x520")
        cfg.transient(self)
        cfg.grab_set()

        ctk.CTkLabel(cfg, text="🧪 A/B Testing 2x2",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 4))
        ctk.CTkLabel(cfg,
                     text="Marca 1 o 2 dimensiones a variar.\nSe generarán 4 prompts variando solo esas.",
                     font=ctk.CTkFont(size=10), text_color="#888",
                     justify="center").pack(pady=(0, 10))

        # Checkboxes para cada dimensión
        dim_vars = {}
        scroll = ctk.CTkScrollableFrame(cfg, fg_color="transparent", height=300)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        # Contador y función para actualizar estado
        lbl_contador = ctk.CTkLabel(cfg, text="Seleccionadas: 0 (máx 2)",
                                    font=ctk.CTkFont(size=10), text_color="#888")
        lbl_contador.pack(pady=(0, 5))

        # Refs a los checkboxes para deshabilitar visualmente los no
        # seleccionados cuando ya hay 2 marcados.
        dim_checks = {}

        def _actualizar_checkboxes():
            total = sum(1 for v in dim_vars.values() if v.get())
            lbl_contador.configure(
                text=f"Seleccionadas: {total} (máx 2)",
                text_color="#2ecc71" if 1 <= total <= 2 else "#e67e22",
            )
            # Deshabilitar visualmente los no seleccionados si ya hay 2
            for nombre, var in dim_vars.items():
                cb = dim_checks.get(nombre)
                if not cb:
                    continue
                if total >= 2 and not var.get():
                    cb.configure(state="disabled")
                else:
                    cb.configure(state="normal")

        for nombre, valores in self.AB_DIMENSIONES.items():
            var = ctk.BooleanVar(value=False)
            dim_vars[nombre] = var
            var.trace_add("write", lambda *a: _actualizar_checkboxes())
            row = ctk.CTkFrame(scroll, fg_color=c["fg_dark"], corner_radius=6)
            row.pack(fill="x", pady=2)
            cb = ctk.CTkCheckBox(row, text=f"  {nombre}", variable=var,
                                  font=ctk.CTkFont(size=11))
            cb.pack(side="left", padx=10, pady=6)
            dim_checks[nombre] = cb
            ctk.CTkLabel(row, text=f"  ej: {valores[0]}",
                         font=ctk.CTkFont(size=9, slant="italic"),
                         text_color="#666").pack(side="left", padx=4)

        def _generar():
            sel = [n for n, v in dim_vars.items() if v.get()]
            if not sel:
                messagebox.showwarning("Sin selección", "Marca al menos 1 dimensión a variar.", parent=cfg)
                return
            if len(sel) > 2:
                messagebox.showwarning("Demasiadas", "Marca como mucho 2 dimensiones (4 combinaciones).", parent=cfg)
                return
            cfg.destroy()
            self._ab_lanzar(idea, sel)

        btn_row = ctk.CTkFrame(cfg, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(5, 15))
        ctk.CTkButton(btn_row, text="🧪 Generar 4 variantes", width=200, height=36,
                      fg_color="#1a8a3c", hover_color="#127a30",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=_generar).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Cancelar", width=100, height=36,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                      command=cfg.destroy).pack(side="right", padx=4)

    def _ab_lanzar(self, idea_base, dimensiones):
        """Genera las 4 combinaciones con el LLM y las muestra en grid 2x2."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)

        # Combinar valores de las dimensiones seleccionadas
        if len(dimensiones) == 1:
            valores = self.AB_DIMENSIONES[dimensiones[0]]
            combos = [(dimensiones[0], v) for v in valores[:4]]
        else:
            d1, d2 = dimensiones
            v1 = self.AB_DIMENSIONES[d1][:2]
            v2 = self.AB_DIMENSIONES[d2][:2]
            combos = []
            for a in v1:
                for b in v2:
                    combos.append([(d1, a), (d2, b)])

        # Obtener specs del modelo actual
        specs = self.get_current_model_specs() or {}
        max_chars = specs.get("max_chars", 1500)
        has_neg = specs.get("has_negative", True)
        is_natural = specs.get("is_natural", False)
        fmt = "lenguaje natural descriptivo" if is_natural else "tags con pesos (tag:1.2)"
        neg_str = "Genera POSITIVE y NEGATIVE." if has_neg else "No generes NEGATIVE."

        self.set_estado("🧪 Generando 4 variantes con IA...", "#3498db")
        self.toggle_botones(False)

        def _generar():
            prompts_generados = []
            for idx, combo in enumerate(combos[:4]):
                if isinstance(combo, tuple):
                    dim_name, dim_val = combo
                    variacion = f"Cambia {dim_name} a: {dim_val}"
                    etiqueta = f"{dim_name}: {dim_val}"
                else:
                    cambios = ", ".join(f"{d}: {v}" for d, v in combo)
                    variacion = f"Cambia: {cambios}"
                    etiqueta = "  ·  ".join(f"{d}: {v}" for d, v in combo)

                peticion = (
                    f"Genera un prompt profesional para esta idea:\n\n"
                    f"IDEA ORIGINAL: {idea_base}\n"
                    f"VARIACIÓN APLICAR: {variacion}\n\n"
                    f"REGLAS:\n"
                    f"- Mantén la idea original pero aplica la variación especificada\n"
                    f"- Formato: {fmt}\n"
                    f"- Añade estilos y calidad profesional\n"
                    f"- Límite: {max_chars} caracteres\n"
                    f"- {neg_str}\n\n"
                    f"Estilos activos: {self.estilos_texto()}\n\n"
                    f"Responde SOLO con el prompt."
                )

                try:
                    resp = self.deepseek.generar(peticion, temperature=0.7, max_tokens=1500)
                    resp = limpiar_marcadores(resp)
                    if not has_neg:
                        import re
                        resp = re.sub(r'\n?\s*NEGATIVE\s+PROMPT\s*:.*?$', '', resp, flags=re.DOTALL | re.IGNORECASE).strip()
                    prompts_generados.append((etiqueta, resp))
                except Exception as e:
                    prompts_generados.append((etiqueta, f"❌ Error: {e}"))

            self.after(0, lambda: self._mostrar_ab_grid(idea_base, dimensiones, prompts_generados, is_lt, c))

        threading.Thread(target=_generar, daemon=True).start()

    def _mostrar_ab_grid(self, idea_base, dimensiones, prompts_generados, is_lt, c):
        """Muestra la grid de resultados."""
        v = GPromptWindow(self)
        v.title(f"🧪 A/B Testing — {' + '.join(dimensiones)}")
        v.geometry("1100x720")
        v.transient(self)

        ctk.CTkLabel(v, text=f"🧪 4 variantes de: {idea_base[:60]}{'…' if len(idea_base) > 60 else ''}",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(12, 4))
        ctk.CTkLabel(v, text=f"Variando: {' + '.join(dimensiones)}",
                     font=ctk.CTkFont(size=10), text_color="#888").pack(pady=(0, 10))

        grid = ctk.CTkFrame(v, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=10, pady=5)
        grid.grid_columnconfigure((0, 1), weight=1)
        grid.grid_rowconfigure((0, 1), weight=1)

        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for idx, ((etiqueta, prompt), (r, col)) in enumerate(zip(prompts_generados, positions)):
            cell = ctk.CTkFrame(grid, fg_color=c["fg_dark"], corner_radius=8)
            cell.grid(row=r, column=col, padx=5, pady=5, sticky="nsew")
            ctk.CTkLabel(cell, text=f"📌 Variante {idx + 1}", font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=c["hdr_text"]).pack(anchor="w", padx=10, pady=(8, 0))
            ctk.CTkLabel(cell, text=etiqueta, font=ctk.CTkFont(size=9, slant="italic"),
                         text_color="#888", wraplength=440, justify="left", anchor="w").pack(fill="x", padx=10, pady=(0, 4))
            txt = ctk.CTkTextbox(cell, wrap="word", height=180, font=ctk.CTkFont(family="Consolas", size=10))
            txt.pack(fill="both", expand=True, padx=10, pady=(0, 5))
            txt.insert("1.0", prompt)

            def _usar(p=prompt):
                self.actualizar_salida(p)
                self.set_estado("🧪 Variante aplicada al editor", "#2ecc71")
                # No cerramos la ventana para poder ver las otras opciones

            btn = ctk.CTkButton(cell, text="✅ Usar este", height=28, fg_color="#1a8a3c", hover_color="#127a30",
                          command=_usar)
            btn.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkButton(v, text="Cerrar", width=110, command=v.destroy, fg_color=c["fg_dark"]).pack(pady=(5, 12))
        self.set_estado("🧪 Elige la variante que más te guste", "#3498db")
        self.toggle_botones(True)

    def _cmd_comparar_modelos(self):
        """Genera el prompt actual adaptado a 3 modelos a elegir por el usuario."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.set_estado("⚠️ Escribe una idea primero para comparar modelos.", "#e67e22")
        try: self._sesion_log("🆚 Comparar: abrió comparador de modelos")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        modo = self.modo_var.get()

        # Lista de modelos disponibles según modo
        if modo == "imagen":
            modelos_disponibles = [m for m in MODELOS_IMAGEN_FLAT if not m.startswith("──")]
            sugeridos = ["Z Image Turbo", "FLUX.1 [dev]", "Nano Banana Pro Image"]
        elif modo == "video":
            modelos_disponibles = [m for m in MODELOS_VIDEO_FLAT if not m.startswith("──")]
            sugeridos = ["Kling 3.0", "Seedance 2.0", "Veo 3.1"]
        else:
            modelos_disponibles = [m for m in MODELOS_AUDIO_FLAT if not m.startswith("──")]
            sugeridos = ["Suno v5", "Suno v4.5", "Minimax Music 2.5"]

        # Asegurar que los sugeridos estén disponibles
        sugeridos = [m for m in sugeridos if m in modelos_disponibles]
        while len(sugeridos) < 5 and modelos_disponibles:
            for m in modelos_disponibles:
                if m not in sugeridos:
                    sugeridos.append(m)
                    if len(sugeridos) >= 5:
                        break

        sel_vent = GPromptWindow(self)
        sel_vent.title("🆚 Elige modelos para comparar")
        sel_vent.geometry("520x500")
        sel_vent.transient(self)

        ctk.CTkLabel(sel_vent, text="🆚 Comparador de modelos",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 3))
        ctk.CTkLabel(sel_vent, text=f"Idea: {idea[:60]}{'...' if len(idea) > 60 else ''}",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"],
                     wraplength=470).pack(pady=(0, 5))

        # Selector de N modelos (2-5)
        n_frame = ctk.CTkFrame(sel_vent, fg_color="transparent")
        n_frame.pack(fill="x", padx=20, pady=(8, 4))
        ctk.CTkLabel(n_frame, text="¿Cuántos modelos comparar?",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     anchor="w").pack(side="left", padx=(0, 8))
        n_var = ctk.IntVar(value=3)
        n_lbl = ctk.CTkLabel(n_frame, text="3 modelos",
                              font=ctk.CTkFont(size=11, weight="bold"),
                              text_color="#2ecc71", width=90)
        n_lbl.pack(side="right")

        frame_combos = ctk.CTkFrame(sel_vent, fg_color="transparent")
        frame_combos.pack(fill="x", padx=20, pady=5)

        combos = []
        combo_rows = []
        for i in range(5):
            f = ctk.CTkFrame(frame_combos, fg_color="transparent")
            f.pack(fill="x", pady=3)
            ctk.CTkLabel(f, text=f"#{i+1}:",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         width=40, anchor="w").pack(side="left", padx=(0, 8))
            cb = ctk.CTkComboBox(f, values=modelos_disponibles, width=380,
                                  height=28, font=ctk.CTkFont(size=11))
            cb.set(sugeridos[i] if i < len(sugeridos) else modelos_disponibles[0])
            cb.pack(side="left")
            combos.append(cb)
            combo_rows.append(f)

        def _actualizar_n(v):
            n = int(round(float(v)))
            n_var.set(n)
            n_lbl.configure(text=f"{n} modelos")
            for i, row in enumerate(combo_rows):
                if i < n:
                    row.pack(fill="x", pady=3)
                else:
                    row.pack_forget()

        slider = ctk.CTkSlider(n_frame, from_=2, to=5, number_of_steps=3,
                                width=130, command=_actualizar_n)
        slider.set(3)
        slider.pack(side="right", padx=(0, 8))

        # Inicialmente mostrar 3 filas
        _actualizar_n(3)

        # Botones
        btn_frame = ctk.CTkFrame(sel_vent, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=(0, 20))

        def _comparar():
            n = n_var.get()
            seleccionados = [combos[i].get() for i in range(n)]
            # Validar que sean diferentes
            if len(set(seleccionados)) < n:
                self.set_estado(f"⚠️ Elige {n} modelos diferentes.", "#e67e22")
                return
            sel_vent.destroy()
            self._abrir_ventana_comparacion(idea, modo, seleccionados)

        ctk.CTkButton(btn_frame, text="🆚 Comparar", width=140, height=34,
                      fg_color="#1a7a3c", hover_color="#145e2d",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=_comparar).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Cancelar", width=100, height=34,
                      fg_color="#444444", hover_color="#222222",
                      command=sel_vent.destroy).pack(side="left", padx=4)

    def _abrir_ventana_comparacion(self, idea, modo, modelos_compare):
        """Ventana donde se muestran los N prompts generados (N=2..5)."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        n_modelos = len(modelos_compare)
        vent = GPromptWindow(self)
        vent.title(f"🆚 Comparativa de modelos ({n_modelos})")
        # Tamaño dinámico: más alto si hay más modelos (cards apiladas)
        alto = min(620 + max(0, n_modelos - 3) * 120, 950)
        vent.geometry(f"820x{alto}")
        vent.transient(self)

        ctk.CTkLabel(vent, text=f"🆚 Comparativa de {n_modelos} modelos",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text=f"Idea: {idea[:80]}{'...' if len(idea) > 80 else ''}",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"], wraplength=780).pack(pady=(0, 8))

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 5))

        lbl_status = ctk.CTkLabel(vent, text=f"🔄 Generando para {n_modelos} modelos...",
                                   font=ctk.CTkFont(size=11), text_color="#f39c12")
        lbl_status.pack(pady=(0, 4))

        # Botón "Cerrar comparativa" — la ventana ya no se cierra al pulsar
        # "Usar este (modelo+prompt)" en una card, así que el usuario
        # necesita un botón explícito para cerrar cuando termine.
        ctk.CTkButton(vent, text="Cerrar comparativa", width=180, height=30,
                      fg_color="#6b7280", hover_color="#4b5563",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=vent.destroy).pack(pady=(0, 8))

        cards = {}
        # 5 colores cíclicos para soportar hasta 5 cards sin IndexError.
        # Antes la lista era solo de 3 → IndexError al elegir 4-5 modelos.
        colores_hdr = ["#1a3a5a", "#1a5a3a", "#5a1a3a", "#5a3a1a", "#3a1a5a"]
        for i, m in enumerate(modelos_compare):
            card = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=8)
            card.pack(fill="x", pady=4, padx=2)
            hdr_color = colores_hdr[i % len(colores_hdr)]
            hdr = ctk.CTkFrame(card, fg_color=hdr_color, corner_radius=6, height=28)
            hdr.pack(fill="x", padx=5, pady=(5, 3))
            hdr.pack_propagate(False)

            # Mostrar info del modelo en el header
            specs = get_image_model_specs(m) or get_model_specs(m) or get_audio_model_specs(m) or {}
            chars_max = specs.get("max_chars", "?")
            has_neg = "✅ Neg" if specs.get("has_negative", False) else "❌ Sin neg"
            ctk.CTkLabel(hdr, text=f"  #{i+1}  {m}  ·  {chars_max} chars  ·  {has_neg}",
                         font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=8)

            txt = ctk.CTkTextbox(card, font=ctk.CTkFont(family="Consolas", size=10), height=130, wrap="word")
            txt.pack(fill="x", padx=8, pady=(0, 4))
            txt.insert("1.0", "⏳ Generando...")
            txt.configure(state="disabled")

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=8, pady=(0, 6))
            btn_usar = ctk.CTkButton(btn_row, text="✅ Usar este", width=100, height=22, fg_color="#1a7a3c",
                                       state="disabled", font=ctk.CTkFont(size=10))
            btn_usar.pack(side="left", padx=2)
            btn_copiar = ctk.CTkButton(btn_row, text="📋 Copiar", width=80, height=22, fg_color=c["fg_dark"],
                                          state="disabled", font=ctk.CTkFont(size=10))
            btn_copiar.pack(side="left", padx=2)
            lbl_chars = ctk.CTkLabel(btn_row, text="", font=ctk.CTkFont(size=9), text_color=c["muted_text"])
            lbl_chars.pack(side="right", padx=4)
            cards[m] = {"txt": txt, "btn_usar": btn_usar, "btn_copiar": btn_copiar,
                        "lbl_chars": lbl_chars, "card": card, "hdr": hdr,
                        "hdr_color": hdr_color}

            def _generar(modelo):
                try:
                    specs = get_image_model_specs(modelo) or get_model_specs(modelo) or get_audio_model_specs(modelo) or {}
                    max_c = specs.get("max_chars", 1500)
                    has_neg = specs.get("has_negative", True)
                    is_natural = specs.get("is_natural", False)
                    no_weights = specs.get("no_weights", False)
                    best_for = specs.get("best_for", "")[:200] if specs else ""

                    if is_natural:
                        tipo_format = "lenguaje natural descriptivo en una sola línea, sin saltos de línea"
                    elif no_weights:
                        tipo_format = "tags separados por comas, sin pesos numéricos"
                    else:
                        tipo_format = "tags separados por comas con pesos opcionales (tag:1.2)"

                    # Petición ESTRICTA — antes el LLM mezclaba contenido entre
                    # respuestas y a veces devolvía "Aquí tienes prompts para
                    # varios modelos" o concatenaba múltiples bloques.
                    if has_neg:
                        estructura = (
                            "DEVUELVE EXACTAMENTE 2 LÍNEAS, nada más:\n"
                            "POSITIVE PROMPT: <prompt en una sola línea>\n"
                            "NEGATIVE PROMPT: <negative en una sola línea>"
                        )
                    else:
                        estructura = (
                            "DEVUELVE EXACTAMENTE 1 LÍNEA, nada más:\n"
                            "POSITIVE PROMPT: <prompt en una sola línea>"
                        )

                    peticion = (
                        f"Genera UN prompt de {modo} optimizado para este modelo concreto:\n\n"
                        f"MODELO: {modelo}\n"
                        f"FORTALEZAS: {best_for}\n\n"
                        f"IDEA: {idea}\n"
                        f"ESTILOS A INCLUIR: {self.estilos_texto()}\n\n"
                        f"REGLAS ESTRICTAS:\n"
                        f"- Formato: {tipo_format}\n"
                        f"- Límite POSITIVE: {max_c} caracteres\n"
                        f"- NO menciones otros modelos en la respuesta\n"
                        f"- NO añadas explicaciones tipo 'Aquí tienes...'\n"
                        f"- NO añadas prosa descriptiva extra\n"
                        f"- NO repitas la sección POSITIVE/NEGATIVE\n"
                        f"- Aprovecha las fortalezas del modelo {modelo}\n\n"
                        f"{estructura}"
                    )
                    resp = self.deepseek.generar(peticion, temperature=0.45, max_tokens=1500)
                    resp = limpiar_marcadores(resp)

                    # Defensa client-side: extraer SOLO el primer bloque
                    # POSITIVE [+ NEGATIVE], descartando todo lo demás.
                    import re as _re
                    m_pos = _re.search(
                        r'(?:POSITIVE\s+)?PROMPT\s*:\s*(.+?)(?=\n\s*NEGATIVE\s+PROMPT\s*:|\n\s*POSITIVE\s+PROMPT\s*:|\n\s*###|\n\s*\*\*\*|\Z)',
                        resp, flags=_re.DOTALL | _re.IGNORECASE)
                    m_neg = _re.search(
                        r'NEGATIVE\s+PROMPT\s*:\s*(.+?)(?=\n\s*POSITIVE\s+PROMPT\s*:|\n\s*NEGATIVE\s+PROMPT\s*:|\n\s*###|\n\s*\*\*\*|\Z)',
                        resp, flags=_re.DOTALL | _re.IGNORECASE)
                    if m_pos:
                        pos_clean = " ".join(m_pos.group(1).split())
                        # Truncar suave al límite del modelo (con margen)
                        if isinstance(max_c, int) and len(pos_clean) > max_c + 200:
                            pos_clean = pos_clean[:max_c + 200].rsplit(",", 1)[0]
                        if has_neg and m_neg:
                            neg_clean = " ".join(m_neg.group(1).split())
                            resp = f"POSITIVE PROMPT: {pos_clean}\nNEGATIVE PROMPT: {neg_clean}"
                        else:
                            resp = f"POSITIVE PROMPT: {pos_clean}"
                    else:
                        # Sin marcador detectable: asumir todo es POSITIVE
                        pos_clean = " ".join(resp.split())
                        if isinstance(max_c, int) and len(pos_clean) > max_c + 200:
                            pos_clean = pos_clean[:max_c + 200].rsplit(",", 1)[0]
                        resp = f"POSITIVE PROMPT: {pos_clean}"

                    # Eliminar pesos si el modelo no los soporta
                    if no_weights:
                        resp = _re.sub(r'\(([^()]+?):\s*[0-9.]+\s*\)', r'\1', resp)

                    def _mostrar(r=resp, m=modelo, mc=max_c):
                        try:
                            if not vent.winfo_exists():
                                return
                            cards[m]["txt"].configure(state="normal")
                            cards[m]["txt"].delete("1.0", "end")
                            cards[m]["txt"].insert("1.0", r)
                            cards[m]["txt"].configure(state="disabled")
                            cards[m]["lbl_chars"].configure(text=f"{len(r)} / {mc} chars")

                            def _aplicar_y_cambiar_modelo(r2=r, m2=m):
                                # Aplica el prompt al resultado Y cambia el
                                # modelo activo en el combo correspondiente.
                                # La ventana NO se cierra: el usuario puede
                                # seguir probando otros modelos del set sin
                                # perder las opciones.
                                modo_act = self.modo_var.get()
                                try:
                                    if modo_act == "imagen" and hasattr(self, 'combo_modelo_imagen'):
                                        valores = list(self.combo_modelo_imagen.cget("values") or [])
                                        if m2 in valores:
                                            self.combo_modelo_imagen.set(m2)
                                            if hasattr(self, '_on_modelo_imagen_cambio'):
                                                self._on_modelo_imagen_cambio()
                                    elif modo_act == "video" and hasattr(self, 'combo_modelo_video'):
                                        valores = list(self.combo_modelo_video.cget("values") or [])
                                        if m2 in valores:
                                            self.combo_modelo_video.set(m2)
                                    elif modo_act == "audio" and hasattr(self, 'combo_modelo_audio'):
                                        valores = list(self.combo_modelo_audio.cget("values") or [])
                                        if m2 in valores:
                                            self.combo_modelo_audio.set(m2)
                                except Exception as _e:
                                    logger.debug(f"[silent compar usar] {_e}")
                                self.actualizar_salida(r2)

                                # Highlight visual: borde dorado en la card aplicada,
                                # las demás vuelven a su color original.
                                for _m_key, _info in cards.items():
                                    try:
                                        if _m_key == m2:
                                            _info["card"].configure(border_color="#fbbf24",
                                                                     border_width=3)
                                            _info["hdr"].configure(fg_color="#fbbf24")
                                        else:
                                            _info["card"].configure(border_width=0)
                                            _info["hdr"].configure(fg_color=_info["hdr_color"])
                                    except Exception as _e:
                                        logger.debug(f"[silent highlight] {_e}")

                                self.set_estado(
                                    f"🏆 '{m2}' aplicado — la ventana sigue abierta para probar otros",
                                    "#2ecc71")

                            cards[m]["btn_usar"].configure(
                                state="normal",
                                text="🏆 Usar este (modelo+prompt)",
                                width=200,
                                command=_aplicar_y_cambiar_modelo,
                            )
                            cards[m]["btn_copiar"].configure(
                                state="normal",
                                command=lambda r=r, m=m: (
                                    pyperclip.copy(r),
                                    self.set_estado(f"📋 Copiado prompt de {m}", "#2ecc71")))
                        except Exception as _e:
                            logger.debug(f"[silent] {_e}")
                    self.after(0, _mostrar)
                except Exception as e:
                    def _err(m=modelo, exc=e):
                        try:
                            if not vent.winfo_exists():
                                return
                            cards[m]["txt"].configure(state="normal")
                            cards[m]["txt"].delete("1.0", "end")
                            cards[m]["txt"].insert("1.0", f"❌ Error: {exc}")
                            cards[m]["txt"].configure(state="disabled")
                        except Exception as _e:
                            logger.debug(f"[silent] {_e}")
                    self.after(0, lambda: _err(m=modelo, exc=e))

            def _todos():
                for m in modelos_compare:
                    threading.Thread(target=_generar, args=(m,), daemon=True).start()

            threading.Thread(target=_todos, daemon=True).start()

    def _aplicar_atajo_tags(self, tags_a_anadir):
        """Añade tags al final del POSITIVE del resultado actual."""
        texto = self.txt_salida.get("1.0", "end").strip()
        if not texto:
            return self.set_estado("⚠️ Genera un prompt primero.", "#e67e22")
        pos = self.extraer_positive() or texto
        neg = self.extraer_negative()

        # Añadir al final del positive
        nuevo_pos = pos.rstrip(", \n")
        nuevo_pos = f"{nuevo_pos}, {tags_a_anadir}"

        nuevo = f"POSITIVE PROMPT: {nuevo_pos}"
        if neg:
            nuevo += f"\nNEGATIVE PROMPT: {neg}"
        self.actualizar_salida(nuevo)
        self.set_estado(f"✨ Tags añadidos: {tags_a_anadir[:50]}...", "#2ecc71")
