"""Workflow Tools Mixin - Setup management, Macros, A/B Testing, Cron, Projects, Session Recording, etc."""
import datetime
import logging
import re

import pyperclip

from modules.i18n import tr, tr_es

logger = logging.getLogger(__name__)
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk

from config import get_theme_colors as _get_tc
from modules.gprompt_window import GPromptWindow
from workers import limpiar_marcadores, log_future_exc

if TYPE_CHECKING:
    pass

# Acciones automáticas que una macro puede encadenar: label visible → id
# interno despachado en _ejecutar_macro. A nivel de módulo para ser testeable.
ACCIONES_MACRO = {
    "✨ Generar prompt": "generar",
    "🎯 Adaptar al modelo activo": "adaptar_modelo",
    "⚡ Optimizar (1 pasada)": "optimizar_1pasada",
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

# Macros de ejemplo (botón "Cargar ejemplos" en la ventana de Macros). Los
# labels de cada paso DEBEN coincidir exactamente con las claves de
# ACCIONES_MACRO.
MACROS_EJEMPLO = [
    {"nombre": "🎯 Pulir para el modelo",
     "pasos": ["✨ Generar prompt", "🎯 Adaptar al modelo activo",
               "📊 Scoring auto", "🌟 Guardar Estrella"]},
    {"nombre": "🎬 Cinematográfico premium",
     "pasos": ["✨ Generar prompt", "🎬 Refinar más cinematográfico",
               "💡 Refinar mejor iluminación", "⭐ Guardar Favorito"]},
    {"nombre": "🧹 Adaptar prompt pegado",
     "pasos": ["🎯 Adaptar al modelo activo", "📊 Scoring auto"]},
]


def macro_valida(obj) -> dict | None:
    """Valida y limpia una macro importada. Devuelve {'nombre','pasos'} o None.

    Filtra los pasos cuyo label no exista en ACCIONES_MACRO (p.ej. de otra
    versión de la app) para que no queden pasos no-op silenciosos. Requiere
    un nombre no vacío y al menos un paso válido."""
    if not isinstance(obj, dict):
        return None
    nombre = str(obj.get("nombre", "")).strip()
    pasos = obj.get("pasos")
    if not nombre or not isinstance(pasos, list):
        return None
    pasos_validos = [p for p in pasos if isinstance(p, str) and p in ACCIONES_MACRO]
    if not pasos_validos:
        return None
    return {"nombre": nombre, "pasos": pasos_validos}


def parsear_macros_importadas(data) -> list:
    """Normaliza el contenido importado a una lista de macros válidas.

    Acepta una macro suelta (dict), una lista de macros, o {'macros': [...]}.
    Ignora silenciosamente lo que no valide."""
    if isinstance(data, dict) and "macros" in data:
        data = data.get("macros")
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return []
    return [m for m in (macro_valida(o) for o in data) if m]


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
                    try: self.app.events.on_modo_cambio()
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            # Plataforma
            if setup.get("plataforma") and hasattr(self.app, "plataforma_var"):
                self.app.plataforma_var.set(setup["plataforma"])
                if hasattr(self.app, "_on_plataforma_cambio"):
                    try: self.app.events.on_plataforma_cambio()
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
            # Modelo (según modo)
            modo = setup.get("modo", "imagen")
            modelo = setup.get("modelo", "")
            if modelo:
                if modo == "imagen" and hasattr(self.app, "combo_modelo_imagen"):
                    self.app.combo_modelo_imagen.set(modelo)
                    if hasattr(self.app, "_on_modelo_imagen_cambio"):
                        try: self.app.events.on_modelo_imagen_cambio()
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
                elif modo == "video" and hasattr(self.app, "combo_modelo_video"):
                    self.app.combo_modelo_video.set(modelo)
                    if hasattr(self.app, "_on_motor_cambio"):
                        try: self.app.events.on_motor_cambio()
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
                elif modo == "audio" and hasattr(self.app, "combo_modelo_audio"):
                    self.app.combo_modelo_audio.set(modelo)
                    if hasattr(self.app, "_on_motor_audio_cambio"):
                        try: self.app.events.on_motor_audio_cambio()
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
            self.app.dialogs.set_estado(tr('⚠️ Error aplicando setup: {0}').format(e), "#e74c3c")

    def _cmd_guardar_setup(self):
        """Abre diálogo para nombrar y guardar el setup actual."""
        from tkinter import simpledialog
        setup = self._capturar_setup_actual()
        if not setup:
            self.app.dialogs.set_estado(tr("⚠️ No se pudo capturar la configuración"), "#e67e22")
            return
        nombre = simpledialog.askstring(tr("💾 Guardar setup"),
                                          tr("Nombre para este setup:\n(modelo, plataforma, ratio, estilos, negatives…)"),
                                          parent=self.app)
        if not nombre or not nombre.strip(): return
        nombre = nombre.strip()[:60]
        # Cargar setups existentes
        prefs = self.app.store.cargar_preferencias()
        setups = prefs.get("setups", {}) or {}
        # Confirmación si ya existe
        if nombre in setups:
            from tkinter import messagebox
            if not messagebox.askyesno(tr("Sobrescribir"),
                                         tr("Ya existe un setup llamado '{0}'. ¿Sobrescribirlo?").format(nombre),
                                         parent=self.app):
                return
        setup["_fecha_guardado"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        setups[nombre] = setup
        prefs["setups"] = setups
        self.app.store.guardar_preferencias(prefs)
        self.app.dialogs.set_estado(tr("💾 Setup '{0}' guardado").format(nombre), "#2ecc71")
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
            self.app.dialogs.set_estado(tr("⚠️ No hay setups guardados todavía. Pulsa '💾 Setup' para guardar el actual."), "#e67e22")
            return
        v = GPromptWindow(self.app)
        v.title(tr("📋 Cargar setup"))
        v.geometry("560x520")
        v.transient(self.app)
        ctk.CTkLabel(v, text=tr("📋 Setups guardados"), font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 8))
        scroll = ctk.CTkScrollableFrame(v, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        def _refrescar_lista():
            for w in scroll.winfo_children(): w.destroy()
            setups_act = self.app.store.cargar_preferencias().get("setups", {}) or {}
            if not setups_act:
                ctk.CTkLabel(scroll, text=tr("(sin setups)"), text_color="#666").pack(pady=20)
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
                    ctk.CTkLabel(card, text=tr('  guardado: {0}').format(fecha), font=ctk.CTkFont(size=9),
                                 text_color="#555", anchor="w").pack(fill="x", padx=10)
                # Botones
                btn_row = ctk.CTkFrame(card, fg_color="transparent")
                btn_row.pack(fill="x", padx=10, pady=(4, 8))

                def _aplicar(s=setup, n=nombre):
                    self._aplicar_setup(s)
                    self.app.dialogs.set_estado(tr("📋 Setup '{0}' aplicado").format(n), "#2ecc71")
                    v.destroy()

                def _borrar(n=nombre):
                    from tkinter import messagebox
                    if messagebox.askyesno(tr("Borrar setup"), tr("¿Borrar el setup '{0}'?").format(n), parent=v):
                        prefs2 = self.app.store.cargar_preferencias()
                        setups2 = prefs2.get("setups", {}) or {}
                        setups2.pop(n, None)
                        prefs2["setups"] = setups2
                        self.app.store.guardar_preferencias(prefs2)
                        _refrescar_lista()

                ctk.CTkButton(btn_row, text=tr("Aplicar"), width=90, height=26,
                              fg_color="#1e5f3a", hover_color="#16492d", command=_aplicar).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text=tr("🗑 Borrar"), width=90, height=26,
                              fg_color="#6a1a1a", hover_color="#4a0f0f", command=_borrar).pack(side="left", padx=2)

        _refrescar_lista()
        ctk.CTkButton(v, text=tr("Cerrar"), width=110, command=v.destroy,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"]).pack(pady=(0, 12))

    def _cmd_cron_prompts(self):
        """Genera N variantes del prompt actual espaciadas en el tiempo."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        idea = self.app.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            self.app.dialogs.set_estado(tr("⚠️ Escribe una idea base primero."), "#e67e22")
            return

        vent = GPromptWindow(self.app)
        vent.title(tr("⏲ Cron de variantes"))
        vent.geometry("520x620")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("⏲ Cron — Variantes programadas"), font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 3))
        ctk.CTkLabel(vent, text=tr("Genera N VARIANTES distintas espaciadas en el tiempo.\nCada una añade variación (encuadre, iluminación, paleta...) automáticamente."),
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"], justify="center").pack(pady=(0, 12))

        ctk.CTkLabel(vent, text=tr('Idea base:\n{0}{1}').format((idea[:120]), ('...' if len(idea) > 120 else '')),
                     font=ctk.CTkFont(size=10), text_color=c["hdr_text"], wraplength=460,
                     fg_color=c["fg_dark"], corner_radius=6).pack(fill="x", padx=15, pady=(0, 12))

        # Cantidad
        f1 = ctk.CTkFrame(vent, fg_color="transparent")
        f1.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f1, text=tr("Cantidad de variantes:"), width=160, anchor="w").pack(side="left")
        ent_cantidad = ctk.CTkEntry(f1, width=80)
        ent_cantidad.insert(0, "5")
        ent_cantidad.pack(side="left")

        # Intervalo
        f2 = ctk.CTkFrame(vent, fg_color="transparent")
        f2.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f2, text=tr("Cada cuántos minutos:"), width=160, anchor="w").pack(side="left")
        ent_intervalo = ctk.CTkEntry(f2, width=80)
        ent_intervalo.insert(0, "10")
        ent_intervalo.pack(side="left")

        # Qué variar
        ctk.CTkLabel(vent, text=tr("Qué cambiar entre variantes:"), font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=20, pady=(12, 3))
        var_aspecto = ctk.StringVar(value=tr("Variar todo aleatoriamente"))
        # El combo muestra la traducción; el lookup en mapeo_aspecto
        # des-traduce con tr_es() (claves ES).
        opciones = [tr(o) for o in (
            "Variar todo aleatoriamente",
            "Solo iluminación",
            "Solo encuadre/cámara",
            "Solo paleta de colores",
            "Solo atmósfera/mood",
            "Solo estilo artístico",
            "🎯 Personalizado (ver abajo)",
        )]
        cb_aspecto = ctk.CTkComboBox(vent, values=opciones, variable=var_aspecto, width=320, height=28)
        cb_aspecto.pack(anchor="w", padx=20)

        # Campo personalizado
        ctk.CTkLabel(vent, text=tr("Instrucción personalizada (opcional):"),
                     font=ctk.CTkFont(size=10, weight="bold"), text_color=c["muted_text"]).pack(anchor="w", padx=20, pady=(8, 2))
        ent_personalizado = ctk.CTkEntry(vent,
                                          placeholder_text=tr('ej: "cambia el animal en cada variante" o "varía el color del coche"'),
                                          width=460, height=28)
        ent_personalizado.pack(anchor="w", padx=20)
        ctk.CTkLabel(vent, text=tr("Si rellenas esto, se usa SIEMPRE (independientemente del selector de arriba)."),
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
                self.app.dialogs.set_estado(tr("⚠️ Cantidad (1-50) e intervalo (0.1-120 min)"), "#e67e22")
                return

            cron_state["activo"] = True
            cron_state["actuales"] = 0
            cron_state["generados"] = []
            aspecto = tr_es(var_aspecto.get())
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
                        self.app.dialogs.actualizar_salida(resp)
                        progreso = tr("⏲ Variante {0}/{1} generada · próxima en {2}min").format(
                            num, cantidad, int(intervalo))
                        if num >= cantidad:
                            progreso = tr("✅ Cron completado: {0} variantes generadas").format(cantidad)
                        _safe_configure(lbl_progreso, text=progreso,
                                        text_color="#2ecc71" if num >= cantidad else "#3498db")
                        self.app.dialogs.set_estado(tr('⏲ Variante {0}/{1} lista').format((num), (cantidad)), "#3498db")
                    self.app.after(0, _aplicar)
                except Exception as e:
                    self.app.after(0, lambda e=e: _safe_configure(lbl_progreso,
                                                          text=tr('❌ Error variante {0}: {1}').format((num), (e)),
                                                          text_color="#e74c3c"))

            def _siguiente():
                if cron_state["cerrada"] or not cron_state["activo"]:
                    return
                cron_state["actuales"] += 1
                num = cron_state["actuales"]
                _safe_configure(lbl_progreso,
                                text=tr('⏲ Generando variante {0}/{1}...').format((num), (cantidad)),
                                text_color="#f39c12")

                self.app._executor.submit(_generar_variante, num).add_done_callback(log_future_exc)

                if num < cantidad and cron_state["activo"]:
                    cron_state["after_id"] = vent.after(
                        int(intervalo * 60 * 1000), _siguiente)
                else:
                    cron_state["activo"] = False
                    cron_state["after_id"] = None

            _siguiente()
            self.app.dialogs.set_estado(tr('⏲ Cron iniciado: {0} variantes cada {1}min').format((cantidad), (intervalo)), "#2ecc71")

        def _detener():
            cron_state["activo"] = False
            if cron_state["after_id"]:
                try: vent.after_cancel(cron_state["after_id"])
                except Exception as _e: logger.debug(f"[silent] {_e}")
                cron_state["after_id"] = None
            _safe_configure(lbl_progreso,
                            text=tr('⏹ Cron detenido en variante {0}/{1}').format((cron_state['actuales']), (ent_cantidad.get())),
                            text_color="#e67e22")

        def _ver_todas():
            if cron_state["generados"]:
                self.app._abrir_comparador(cron_state["generados"])
            else:
                self.app.dialogs.set_estado(tr("⚠️ Aún no hay variantes generadas"), "#e67e22")

        btn_row = ctk.CTkFrame(vent, fg_color="transparent")
        btn_row.pack(pady=10)
        ctk.CTkButton(btn_row, text=tr("▶ Iniciar cron"), width=130, height=32, fg_color="#1a7a3c",
                      command=_ejecutar_cron).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=tr("⏹ Detener"), width=100, height=32, fg_color="#5a1a1a",
                      command=_detener).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=tr("👁 Ver todas"), width=110, height=32, fg_color="#1a4a7a",
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
            return self.app.dialogs.set_estado(tr("⚠️ No hay versiones aún. Genera/refina prompts para crear versiones."), "#e67e22")

        vent = GPromptWindow(self.app)
        vent.title(tr("📜 Historial de versiones del prompt"))
        vent.geometry("700x500")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr('📜 {0} versiones en esta sesión').format(len(self.app._versiones_prompt)),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text=tr("Click en una versión para restaurarla"),
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
                         text=tr('  📜 Versión #{0}  ·  {1}{2}').format((num), (ver.get('fecha', '')), (origen_txt)),
                         font=ctk.CTkFont(size=11, weight="bold"), text_color=c["hdr_text"]).pack(side="left", padx=4)

            preview = ver["texto"][:200]
            ctk.CTkLabel(card, text=preview + ("..." if len(ver["texto"]) > 200 else ""),
                         font=ctk.CTkFont(size=10), text_color=c["muted_text"],
                         wraplength=640, justify="left", anchor="w").pack(fill="x", padx=8, pady=(2, 4))

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=5, pady=(0, 4))

            def _restaurar(t=ver["texto"]):
                self.app.dialogs.actualizar_salida(t)
                vent.destroy()
                self.app.dialogs.set_estado(tr('⏪ Versión restaurada'), "#2ecc71")
            ctk.CTkButton(btn_row, text=tr("⏪ Restaurar esta"), width=130, height=22, fg_color="#1a7a3c",
                          font=ctk.CTkFont(size=10), command=_restaurar).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text=tr("📋 Copiar"), width=80, height=22, fg_color=c["fg_dark"],
                          font=ctk.CTkFont(size=10),
                          command=lambda t=ver["texto"]: pyperclip.copy(t)).pack(side="left", padx=2)

    def _abrir_macros(self):
        """Macros: secuencias de acciones automatizadas."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        prefs = self.app.store.cargar_preferencias()
        macros = prefs.get("macros", [])

        vent = GPromptWindow(self.app)
        vent.title(tr("⚡ Macros — Secuencias automatizadas"))
        vent.geometry("700x600")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("⚡ Macros — Secuencias de acciones automatizadas"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text=tr("Combina acciones (ej: Generar → Refinar cinematográfico → Guardar estrella)"),
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

        # Acciones disponibles para construir macros (solo automáticas).
        # Definidas a nivel de módulo (ACCIONES_MACRO) para poder testear que
        # las macros de ejemplo solo referencian labels válidos.
        acciones_disponibles = ACCIONES_MACRO

        # Form crear/editar macro
        # Estado: si `editing_idx` != None, estamos editando una macro
        # existente; el botón principal cambia a "Guardar cambios".
        edit_state = {"idx": None}

        form = ctk.CTkFrame(vent, fg_color=c["fg_dark"], corner_radius=6)
        form.pack(fill="x", padx=10, pady=5)
        lbl_form_titulo = ctk.CTkLabel(form, text=tr("➕ Nueva macro"),
                                        font=ctk.CTkFont(size=11, weight="bold"))
        lbl_form_titulo.pack(anchor="w", padx=10, pady=(8, 2))

        ent_nombre_m = ctk.CTkEntry(form,
                                     placeholder_text=tr("Nombre (ej: 'Pulir prompt cinematográfico')"),
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
                ctk.CTkLabel(pasos_box, text=tr("(añade pasos abajo)"),
                             font=ctk.CTkFont(size=10, slant="italic"),
                             text_color=c["muted_text"]).pack(anchor="w")
                return
            for idx_p, label in enumerate(pasos_state["lista"]):
                row = ctk.CTkFrame(pasos_box, fg_color=c["fg_frame"],
                                    corner_radius=4)
                row.pack(fill="x", pady=1)
                ctk.CTkLabel(row, text=f"  {idx_p + 1}. {tr(label)}",
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
        # El combo muestra la traducción; el paso se guarda con la clave ES
        # (las macros persistidas y ACCIONES_MACRO están keyed en ES).
        var_accion = ctk.StringVar(value=tr(list(acciones_disponibles.keys())[0]))
        cb_acc = ctk.CTkComboBox(f_add, values=[tr(k) for k in acciones_disponibles],
                                  variable=var_accion, width=400, height=24)
        cb_acc.pack(side="left", padx=(0, 5))

        def _add_paso():
            label = tr_es(var_accion.get())
            pasos_state["lista"].append(label)
            _refrescar_pasos()

        ctk.CTkButton(f_add, text=tr("➕ Añadir paso"), width=120, height=24,
                      command=_add_paso).pack(side="left", padx=2)

        def _cancelar_edicion():
            edit_state["idx"] = None
            ent_nombre_m.delete(0, "end")
            pasos_state["lista"] = []
            _refrescar_pasos()
            lbl_form_titulo.configure(text=tr("➕ Nueva macro"))
            btn_crear.configure(text=tr("✅ Crear macro"), fg_color="#1a7a3c")
            btn_cancelar.pack_forget()

        btn_cancelar = ctk.CTkButton(f_add, text=tr("❌ Cancelar edición"),
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
                ctk.CTkLabel(scroll, text=tr("Aún no tienes macros. Crea la primera arriba."),
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
                        text=tr('✏️ Editando: {0}').format(macro.get('nombre', '?')))
                    btn_crear.configure(text=tr("💾 Guardar cambios"),
                                         fg_color="#1a5a8a")
                    btn_cancelar.pack(side="left", padx=2)
                    # Scroll al form
                    try:
                        ent_nombre_m.focus_set()
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")

                def _borrar(idx=i, nombre=m.get("nombre", "?")):
                    if not messagebox.askyesno(
                        tr("Borrar macro"),
                        tr("¿Borrar la macro '{0}'?").format(nombre),
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

                ctk.CTkButton(btn_row, text=tr("▶ Ejecutar"), width=100, height=22, fg_color="#1a7a3c",
                              font=ctk.CTkFont(size=10), command=_ejecutar).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text=tr("✏️ Editar"), width=90, height=22, fg_color="#1a4a7a",
                              font=ctk.CTkFont(size=10), command=_editar).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text="📤", width=30, height=22, fg_color="#5a3a7a",
                              hover_color="#46295f", font=ctk.CTkFont(size=10),
                              command=lambda mm=m: self._exportar_macros_a_archivo(mm)
                              ).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text="🗑", width=30, height=22, fg_color="#5a1a1a",
                              font=ctk.CTkFont(size=10), command=_borrar).pack(side="right", padx=2)

        def crear_o_guardar():
            nombre = ent_nombre_m.get().strip()
            if not nombre or not pasos_state["lista"]:
                self.app.dialogs.set_estado(tr("⚠️ Rellena nombre y añade al menos un paso."), "#e67e22")
                return
            actual = prefs.get("macros", [])
            nueva = {"nombre": nombre, "pasos": list(pasos_state["lista"])}
            if edit_state["idx"] is not None:
                # Modo editar: reemplazar la macro existente
                idx = edit_state["idx"]
                if 0 <= idx < len(actual):
                    actual[idx] = nueva
                self.app.dialogs.set_estado(tr("💾 Macro '{0}' actualizada").format(nombre), "#2ecc71")
            else:
                # Modo crear: añadir nueva al final
                actual.append(nueva)
                self.app.dialogs.set_estado(tr("✅ Macro '{0}' creada").format(nombre), "#2ecc71")
            prefs["macros"] = actual
            self.app.store.guardar_preferencias(prefs)
            _cancelar_edicion()
            refrescar()

        def cargar_ejemplos():
            """Siembra macros de ejemplo curadas (omite las que ya existan por
            nombre). Útil porque Macros arranca vacío y la feature pasa
            desapercibida sin un punto de partida."""
            actual = prefs.get("macros", [])
            existentes = {m.get("nombre", "") for m in actual}
            nuevas = [m for m in MACROS_EJEMPLO if m["nombre"] not in existentes]
            if not nuevas:
                self.app.dialogs.set_estado(
                    tr("ℹ️ Los ejemplos ya están cargados."), "#e67e22")
                return
            actual.extend(nuevas)
            prefs["macros"] = actual
            self.app.store.guardar_preferencias(prefs)
            self.app.dialogs.set_estado(
                tr('📥 {0} macro(s) de ejemplo cargada(s)').format(len(nuevas)), "#2ecc71")
            refrescar()

        botones = ctk.CTkFrame(form, fg_color="transparent")
        botones.pack(pady=(4, 8))
        btn_crear = ctk.CTkButton(botones, text=tr("✅ Crear macro"), width=160, height=28,
                                   fg_color="#1a7a3c",
                                   font=ctk.CTkFont(size=10, weight="bold"),
                                   command=crear_o_guardar)
        btn_crear.pack(side="left", padx=4)
        ctk.CTkButton(botones, text=tr("📥 Cargar ejemplos"), width=150, height=28,
                      fg_color="#1a4a7a", hover_color="#143a5f",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      command=cargar_ejemplos).pack(side="left", padx=4)

        def importar():
            n = self._importar_macros_de_archivo()
            if n > 0:
                # Sincronizar el prefs local de la ventana tras importar+guardar.
                prefs["macros"] = (self.app.store.cargar_preferencias() or {}).get("macros", [])
                refrescar()

        # Compartir macros entre máquinas/usuarios (las "Skills" portables).
        botones2 = ctk.CTkFrame(form, fg_color="transparent")
        botones2.pack(pady=(0, 8))
        ctk.CTkButton(botones2, text=tr("📥 Importar (.json)"), width=150, height=26,
                      fg_color="#5a3a7a", hover_color="#46295f",
                      font=ctk.CTkFont(size=10), command=importar).pack(side="left", padx=4)
        ctk.CTkButton(botones2, text=tr("📤 Exportar todas"), width=150, height=26,
                      fg_color="#5a3a7a", hover_color="#46295f",
                      font=ctk.CTkFont(size=10),
                      command=lambda: self._exportar_macros_a_archivo(
                          prefs.get("macros", []))).pack(side="left", padx=4)

        _refrescar_pasos()
        refrescar()

    def _exportar_macros_a_archivo(self, macros) -> None:
        """Exporta una macro (dict) o varias (lista) a un .json compartible."""
        from tkinter import filedialog
        if isinstance(macros, dict):
            macros = [macros]
        macros = [m for m in (macros or []) if isinstance(m, dict)]
        if not macros:
            return self.app.dialogs.set_estado(tr("⚠️ No hay macros para exportar."), "#e67e22")
        base = macros[0].get("nombre", "macro") if len(macros) == 1 else "macros_gprompt"
        base = re.sub(r"[^\w\-]+", "_", base).strip("_") or "macros"
        ruta = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json")],
            initialfile=f"{base}.json")
        if not ruta:
            return
        try:
            import json as _json
            with open(ruta, "w", encoding="utf-8") as f:
                _json.dump(macros, f, ensure_ascii=False, indent=2)
            self.app.dialogs.set_estado(
                tr('📤 {0} macro(s) exportada(s)').format(len(macros)), "#2ecc71")
        except Exception as e:
            self.app.dialogs.set_estado(tr('❌ Error exportando: {0}').format(e), "#e74c3c")

    def _importar_macros_de_archivo(self) -> int:
        """Importa macros desde un .json y las fusiona (omite duplicados por
        nombre). Devuelve nº de macros nuevas añadidas; -1 si cancelado/error."""
        from tkinter import filedialog
        ruta = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), (tr("Todos"), "*.*")])
        if not ruta:
            return -1
        try:
            import json as _json
            with open(ruta, encoding="utf-8") as f:
                data = _json.load(f)
        except Exception as e:
            self.app.dialogs.set_estado(tr('❌ JSON inválido: {0}').format(e), "#e74c3c")
            return -1
        macros_imp = parsear_macros_importadas(data)
        if not macros_imp:
            self.app.dialogs.set_estado(
                tr("⚠️ El archivo no contiene macros válidas."), "#e67e22")
            return 0
        prefs = self.app.store.cargar_preferencias() or {}
        actual = prefs.get("macros", [])
        existentes = {m.get("nombre", "") for m in actual}
        nuevas = [m for m in macros_imp if m["nombre"] not in existentes]
        actual.extend(nuevas)
        prefs["macros"] = actual
        self.app.store.guardar_preferencias(prefs)
        omitidas = len(macros_imp) - len(nuevas)
        self.app.dialogs.set_estado(
            tr("📥 {0} macro(s) importada(s)").format(len(nuevas))
            + (tr(" · {0} ya existían").format(omitidas) if omitidas else ""), "#2ecc71")
        return len(nuevas)

    def _ejecutar_macro(self, macro, acciones_disponibles):
        """Ejecuta una macro paso a paso."""
        pasos = macro.get("pasos", [])
        if not pasos: return

        self.app.dialogs.set_estado(tr("⚡ Ejecutando macro '{0}' ({1} pasos)...").format((macro.get('nombre', '?')), (len(pasos))), "#f39c12")

        def _ejecutar_paso(idx):
            if idx >= len(pasos):
                self.app.dialogs.set_estado(tr("✅ Macro '{0}' completada").format(macro.get('nombre', '?')), "#2ecc71")
                self.app.dialogs._sonar_completado()
                return
            label = pasos[idx]
            accion_id = acciones_disponibles.get(label, "")
            self.app.dialogs.set_estado(tr('⚡ Paso {0}/{1}: {2}').format((idx+1), (len(pasos)), tr(label)), "#3498db")
            try:
                if accion_id == "generar":
                    self.app.cmd_prompt()
                elif accion_id == "adaptar_modelo":
                    self._cmd_adaptar_modelo()
                    self.app.after(8000, lambda: _ejecutar_paso(idx + 1))
                    return
                elif accion_id == "optimizar_1pasada":
                    self._cmd_optimizar_1pasada()
                    self.app.after(14000, lambda: _ejecutar_paso(idx + 1))
                    return
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
                    self.app.dialogs.actualizar_salida("")
                elif accion_id == "previsualizar":
                    self.app.cmd_previsualizar()
                    self.app.after(18000, lambda: _ejecutar_paso(idx + 1))
                    return
            except Exception as e:
                self.app.dialogs.set_estado(tr('⚠️ Paso falló: {0}').format(e), "#e74c3c")
            self.app.after(6000, lambda: _ejecutar_paso(idx + 1))

        _ejecutar_paso(0)

    def _cmd_scoring_auto_en_macro(self):
        """Scoring automático sin abrir ventana - aplica el mejor prompt directamente."""
        actual = self.app.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.app.dialogs.set_estado(tr("⚠️ Genera un prompt primero para scoring."), "#e67e22")

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
                self.app.after(0, lambda: self.app.dialogs.actualizar_salida(resp))
                self.app.after(0, lambda: self.app.dialogs.set_estado(tr("📊 Scoring aplicado: prompt mejorado (versión anterior guardada)"), "#2ecc71"))
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('⚠️ Error en scoring: {0}').format(e), "#e74c3c"))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _cmd_adaptar_modelo(self):
        """Reescribe el prompt actual para el MODELO ACTIVO (formato, max_chars,
        pesos, negativos) sin alterar la idea. Headless — sirve como comando
        directo (menú 🛠 Herramientas) y como paso de Macro. Reutiliza las specs
        del modelo (inyectar_specs_modelo) y los helpers puros del optimizador."""
        from modules.tools_analysis import (
            asegurar_etiquetas_prompt,
            construir_peticion_adaptar,
        )

        actual = self.app.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.app.dialogs.set_estado(
                tr("⚠️ Genera un prompt primero para adaptarlo."), "#e67e22")

        # Specs del modelo activo (mismo bloque que ve el generador), capado.
        modelo_info = ""
        try:
            modelo_info = (self.app.prompts.inyectar_specs_modelo("") or "")[:1800]
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        if not modelo_info.strip():
            return self.app.dialogs.set_estado(
                tr("ℹ️ El modelo activo no expone specs; nada que adaptar."), "#e67e22")

        def _worker():
            try:
                resp = self.app.deepseek.generar_batch(
                    "Eres un ingeniero de prompts. Adaptas prompts al formato "
                    "exacto de cada modelo de IA sin alterar la idea creativa.",
                    construir_peticion_adaptar(actual, modelo_info),
                    temperature=0.4, max_tokens=2000)
                texto = asegurar_etiquetas_prompt(actual, limpiar_marcadores(resp))
                self.app.after(0, lambda: self.app.dialogs.actualizar_salida(texto))
                self.app.after(0, lambda: self.app.dialogs.set_estado(
                    tr("🎯 Prompt adaptado al modelo activo"), "#2ecc71"))
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(
                    tr('⚠️ Error adaptando: {0}').format(e), "#e74c3c"))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _cmd_optimizar_1pasada(self):
        """Una pasada de optimización (puntuar→mejorar) headless, para macros.
        No abre la ventana del Optimizador en bucle. Tiene en cuenta el modelo
        activo y reutiliza los helpers puros del optimizador."""
        from modules.tools_analysis import (
            asegurar_etiquetas_prompt,
            construir_peticion_mejora,
            construir_peticion_scoring,
            parsear_scoring,
        )

        actual = self.app.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.app.dialogs.set_estado(
                tr("⚠️ Genera un prompt primero para optimizar."), "#e67e22")

        modelo_info = ""
        try:
            modelo_info = (self.app.prompts.inyectar_specs_modelo("") or "")[:1800]
        except Exception as _e:
            logger.debug(f"[silent] {_e}")

        def _worker():
            try:
                resp_s = self.app.deepseek.generar_batch(
                    "Eres un crítico experto de prompts de IA generativa. "
                    "Devuelves SOLO el formato de puntuación solicitado.",
                    construir_peticion_scoring(actual, modelo_info),
                    temperature=0.3, max_tokens=2000)
                parsed = parsear_scoring(limpiar_marcadores(resp_s))
                resp_m = self.app.deepseek.generar_batch(
                    "Eres un ingeniero de prompts experto. Mejoras el prompt "
                    "respetando el formato exacto que se te pide.",
                    construir_peticion_mejora(
                        actual, parsed.get("debiles", ""),
                        parsed.get("sugerencia", ""), modelo_info),
                    temperature=0.5, max_tokens=2000)
                texto = asegurar_etiquetas_prompt(actual, limpiar_marcadores(resp_m))
                score_txt = ""
                if parsed.get("total"):
                    v, mx = parsed["total"]
                    if mx:
                        score_txt = tr(" (partía de {0}/100)").format(int(v / mx * 100))
                self.app.after(0, lambda: self.app.dialogs.actualizar_salida(texto))
                self.app.after(0, lambda: self.app.dialogs.set_estado(
                    tr('⚡ Optimizado en 1 pasada{0}').format(score_txt), "#2ecc71"))
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(
                    tr('⚠️ Error optimizando: {0}').format(e), "#e74c3c"))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

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
                self.app.after(0, lambda: self.app.dialogs.set_estado(tr("💡 Idea generada (macro)"), "#2ecc71"))
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('⚠️ Error: {0}').format(e), "#e74c3c"))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _cmd_variacion_auto_en_macro(self):
        """Genera 1 variación directamente sin popup - para macros."""
        actual = self.app.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.app.dialogs.set_estado(tr("⚠️ Genera un prompt primero."), "#e67e22")

        peticion = (
            f"Crea una variación de este prompt manteniendo la esencia pero cambiando estilo/enfoque:\n\n"
            f"{actual}\n\n"
            f"Responde SOLO con el nuevo prompt variado, en el mismo formato."
        )

        def _worker():
            try:
                resp = self.app.deepseek.generar(peticion, temperature=0.7, max_tokens=1500)
                resp = limpiar_marcadores(resp)
                self.app.after(0, lambda: self.app.dialogs.actualizar_salida(resp))
                self.app.after(0, lambda: self.app.dialogs.set_estado(tr("🔄 Variación generada (macro)"), "#2ecc71"))
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('⚠️ Error: {0}').format(e), "#e74c3c"))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

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
        vent.title(tr("🏷 Proyectos"))
        vent.geometry("680x600")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("🏷 Sistema de proyectos"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text=tr("Organiza tus prompts en proyectos. Cada proyecto puede tener su propio setup."),
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 10))

        # Indicador del proyecto activo
        activo = prefs.get("proyecto_activo", "")
        lbl_activo = ctk.CTkLabel(vent, text=tr('📌 Proyecto activo: {0}').format(activo or '(ninguno)'),
                                    font=ctk.CTkFont(size=12, weight="bold"),
                                    text_color="#2ecc71" if activo else c["muted_text"])
        lbl_activo.pack(pady=5)

        # Form crear proyecto
        f_crear = ctk.CTkFrame(vent, fg_color=c["fg_dark"])
        f_crear.pack(fill="x", padx=10, pady=5)
        ent_proy = ctk.CTkEntry(f_crear, placeholder_text=tr("Nombre del proyecto (ej: 'Campaña café orgánico')"), width=420)
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

        ctk.CTkButton(f_crear, text=tr("➕ Crear"), width=80, height=28, fg_color="#1a7a3c",
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
                ctk.CTkLabel(scroll, text=tr("Aún no tienes proyectos. Crea el primero arriba."),
                             font=ctk.CTkFont(size=11), text_color="#666666").pack(pady=20)
                return

            # Opción "Sin proyecto"
            card = ctk.CTkFrame(scroll, fg_color=c["fg_dark"] if not activo_a else c["fg_frame"], corner_radius=6)
            card.pack(fill="x", pady=2)
            ctk.CTkLabel(card, text=tr("📌 (Sin proyecto activo)"), font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=c["muted_text"]).pack(side="left", padx=10, pady=6)

            def _activar_ninguno():
                p2 = self.app.store.cargar_preferencias()
                p2["proyecto_activo"] = ""
                self.app.store.guardar_preferencias(p2)
                lbl_activo.configure(text=tr("📌 Proyecto activo: (ninguno)"), text_color=c["muted_text"])
                refrescar()
                self.app.dialogs.set_estado(tr("📌 Sin proyecto activo"))

            ctk.CTkButton(card, text=tr("✅ Activar"), width=80, height=22, fg_color="#1a4a5a",
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
                    lbl_activo.configure(text=tr('📌 Proyecto activo: {0}').format(n), text_color="#2ecc71")
                    refrescar()
                    self.app.dialogs.set_estado(tr("🏷 Proyecto '{0}' activado").format(n), "#2ecc71")

                def _guardar_setup_proy(n=nombre_p):
                    """Guarda el setup actual en este proyecto."""
                    setup = self._capturar_setup_actual()
                    if not setup:
                        self.app.dialogs.set_estado(tr("⚠️ No se pudo capturar la configuración"), "#e67e22")
                        return
                    p2 = self.app.store.cargar_preferencias()
                    proys2 = p2.get("proyectos", {}) or {}
                    if not isinstance(proys2, dict): proys2 = {}
                    if n not in proys2: proys2[n] = {}
                    proys2[n]["setup"] = setup
                    proys2[n]["_setup_fecha"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    p2["proyectos"] = proys2
                    self.app.store.guardar_preferencias(p2)
                    self.app.dialogs.set_estado(tr("💾 Setup guardado en '{0}'").format(n), "#2ecc71")
                    refrescar()

                def _aplicar_setup_proy(n=nombre_p):
                    """Aplica el setup de este proyecto a la UI actual."""
                    p2 = self.app.store.cargar_preferencias()
                    proys2 = p2.get("proyectos", {}) or {}
                    proy = proys2.get(n) or {}
                    setup = proy.get("setup") if isinstance(proy, dict) else None
                    if not setup:
                        self.app.dialogs.set_estado(tr("⚠️ El proyecto '{0}' no tiene setup guardado").format(n), "#e67e22")
                        return
                    self._aplicar_setup(setup)
                    self.app.dialogs.set_estado(tr("🔄 Setup de '{0}' aplicado").format(n), "#2ecc71")
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
                    if not messagebox.askyesno(tr("Borrar proyecto"), tr("¿Borrar el proyecto '{0}'?\nLa acción no se puede deshacer.").format(n), parent=vent): return
                    p2 = self.app.store.cargar_preferencias()
                    proys2 = p2.get("proyectos", {}) or {}
                    proys2.pop(n, None)
                    if p2.get("proyecto_activo") == n:
                        p2["proyecto_activo"] = ""
                        lbl_activo.configure(text=tr("📌 Proyecto activo: (ninguno)"), text_color=c["muted_text"])
                    p2["proyectos"] = proys2
                    self.app.store.guardar_preferencias(p2)
                    refrescar()

                if not es_activo:
                    ctk.CTkButton(btn_row, text=tr("✅ Activar"), width=70, height=24, fg_color="#1a7a3c",
                                  font=ctk.CTkFont(size=10), command=_activar).pack(side="left", padx=2)
                if tiene_setup:
                    ctk.CTkButton(btn_row, text=tr("🔄 Aplicar setup"), width=110, height=24, fg_color="#1e5f3a",
                                  hover_color="#16492d",
                                  font=ctk.CTkFont(size=10), command=_aplicar_setup_proy).pack(side="left", padx=2)
                    ctk.CTkButton(btn_row, text=tr("🗑 setup"), width=70, height=24, fg_color="#5a4a1a",
                                  font=ctk.CTkFont(size=10), command=_borrar_setup_proy).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text=tr("💾 Guardar setup actual"), width=160, height=24, fg_color="#1a4a5a",
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
            return self.app.dialogs.set_estado(tr("⚠️ Genera un prompt primero."), "#e67e22")
        pos = self.app.extraer_positive() or texto
        neg = self.app.extraer_negative()

        # Añadir al final del positive
        nuevo_pos = pos.rstrip(", \n")
        nuevo_pos = f"{nuevo_pos}, {tags_a_anadir}"

        nuevo = f"POSITIVE PROMPT: {nuevo_pos}"
        if neg:
            nuevo += f"\nNEGATIVE PROMPT: {neg}"
        self.app.dialogs.actualizar_salida(nuevo)
        self.app.dialogs.set_estado(tr('✨ Tags añadidos: {0}...').format(tags_a_anadir[:50]), "#2ecc71")
