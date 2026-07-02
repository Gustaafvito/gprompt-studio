"""Creative Tools Mixin - Moodboard, Client Mode, ADN Visual, Negative Builder, etc."""
import concurrent.futures
import datetime
import logging
import threading

import customtkinter as ctk
import pyperclip

from config import (
    MODELOS_AUDIO_FLAT,
    MODELOS_IMAGEN_FLAT,
    MODELOS_VIDEO_FLAT,
    get_audio_model_specs,
    get_image_model_specs,
    get_model_specs,
    get_theme_colors,
)
from modules.i18n import get_idioma, tr
from workers import limpiar_marcadores, log_future_exc

logger = logging.getLogger(__name__)
from typing import TYPE_CHECKING

from modules.gprompt_window import GPromptWindow

if TYPE_CHECKING:
    pass

# Catálogo del NEGATIVE builder: {tab: [(nombre_es, tags_negative), ...]}.
# Los nombres ES son la CLAVE interna (presets guardados, _marcar); la UI
# muestra tr(nombre). A nivel de módulo para el test de cobertura i18n.
NEGATIVE_BUILDER_CATEGORIAS = {
    "🔥 Anatomía": [
        ("Manos malas", "(bad hands:1.4), (deformed hands:1.3), (extra fingers:1.4), missing fingers, fused fingers"),
        ("Cara mal", "(deformed face:1.3), (asymmetric face:1.2), bad anatomy, ugly face"),
        ("Ojos raros", "(crossed eyes:1.3), (dead eyes:1.2), unaligned eyes, lazy eye"),
        ("Boca / dientes", "(bad teeth:1.3), crooked teeth, deformed mouth, ugly smile"),
        ("Múltiples cabezas", "(multiple heads:1.4), conjoined twins, cloned face"),
        ("Cuerpo deforme", "(bad anatomy:1.4), (mutation:1.3), extra limbs, deformed body"),
        ("Pies malos", "(bad feet:1.3), deformed toes, fused toes, missing legs"),
        ("Proporciones malas", "(bad proportions:1.3), gigantic head, tiny body, long neck"),
    ],
    "📷 Calidad": [
        ("Baja calidad", "(low quality:1.4), (worst quality:1.4), lowres, blurry, jpeg artifacts"),
        ("Pixelado", "(pixelated:1.3), aliasing, compression artifacts"),
        ("Sobreexpuesto", "(overexposed:1.3), washed out colors, blown highlights"),
        ("Subexpuesto", "(underexposed:1.2), too dark, crushed shadows"),
        ("Ruido", "(noisy:1.3), grainy, film grain"),
        ("Desenfoque", "(out of focus:1.3), motion blur, soft focus"),
        ("Color saturado mal", "oversaturated, neon vomit, ugly color cast"),
        ("Tinte amarillo", "(yellow tint:1.2), color cast, white balance off"),
    ],
    "📝 Texto": [
        ("Texto / letras", "(text:1.4), (watermark:1.4), letters, words, signature"),
        ("Logos / firmas", "logo, brand, copyright, username, artist signature"),
        ("Marca de agua", "(watermark:1.5), stamps, labels"),
        ("Bordes / frame", "(border:1.3), frame, picture frame, vignette"),
        ("Caption / subtítulo", "caption, subtitle, dialog text, speech bubble"),
    ],
    "🎨 Estilo": [
        ("Sin anime", "(anime:1.3), (cartoon:1.3), (illustration:1.3), unrealistic"),
        ("Sin foto", "(photorealistic:1.3), (photograph:1.3), realistic skin"),
        ("Sin 3D", "(3d render:1.3), CGI, plastic look, video game graphics"),
        ("Sin pintura", "(painting:1.2), (drawing:1.2), brush strokes, oil painting"),
        ("Sin sketch", "(sketch:1.3), pencil drawing, line art, lineart"),
        ("Sin abstracto", "(abstract:1.2), abstract art, non-representational"),
    ],
    "🚫 Composición": [
        ("Recortado", "(cropped:1.3), out of frame, cut off"),
        ("Multi-sujeto", "(multiple subjects:1.3), too many people, group, crowd"),
        ("Plano", "flat lighting, no depth, boring composition"),
        ("Simétrico forzado", "(perfect symmetry:1.2), too symmetrical"),
        ("Plano centrado", "centered subject, plain background, dead center"),
        ("Fondo desordenado", "cluttered background, busy background, distracting"),
    ],
    "✨ Realismo": [
        ("Piel plástica", "(plastic skin:1.3), waxy skin, smooth skin, doll-like"),
        ("Sin uncanny", "(uncanny valley:1.3), creepy, soulless"),
        ("Sin filtro IG", "(instagram filter:1.2), heavy makeup, beauty filter"),
        ("Errores luz", "(unnatural lighting:1.2), unrealistic shadows, no shadow"),
    ],
}

class ToolsCreativeService:
    """18 herramientas creativas: sorpréndeme, pulse, sugerir modelo,
    análisis inverso, sugerir estilos, anclaje visual, color palette,
    negative builder/óptimo/solo, grupo personajes, etc.

    A1 fase 2 (sesión 14): servicio aislado con app por composición.
    """

    def __init__(self, app):
        self.app = app

    def _cmd_sorprendeme(self):
        """Genera una idea aleatoria interesante para inspirarse."""
        modo = self.app.modo_var.get()
        try: self.app._sesion_log("🎲 Sorpréndeme: pidió idea aleatoria")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        self.app.dialogs.set_estado(tr("🎲 Pensando algo creativo..."), "#f39c12")
        self.app.dialogs.toggle_botones(False)

        # Contexto del modelo activo para generar ideas acordes a sus fortalezas
        contexto_modelo = ""
        try:
            if modo == "imagen":
                modelo = self.app.combo_modelo_imagen.get()
                specs = get_image_model_specs(modelo) if modelo else None
                if specs and specs.get("best_for"):
                    best = specs["best_for"][:200]
                    tipo = "prosa natural" if specs.get("is_natural") else "tags SD/SDXL"
                    contexto_modelo = (
                        f" El modelo activo es '{modelo}', ideal para: {best}. "
                        f"Genera una idea especialmente adecuada para ese modelo (formato {tipo})."
                    )
            elif modo == "video":
                modelo = self.app.combo_modelo_video.get()
                specs = get_model_specs(modelo) if modelo else None
                if specs and specs.get("best_for"):
                    contexto_modelo = f" El modelo activo es '{modelo}', ideal para: {specs['best_for'][:200]}. Genera una idea de vídeo que aproveche sus puntos fuertes."
            elif modo == "audio":
                modelo = self.app.combo_modelo_audio.get() if hasattr(self.app, "combo_modelo_audio") else ""
                specs = get_audio_model_specs(modelo) if modelo else None
                if specs and specs.get("best_for"):
                    contexto_modelo = f" El modelo activo es '{modelo}', ideal para: {specs['best_for'][:200]}. Genera una idea musical acorde."
        except Exception as e:
            logger.debug(f"[silent sorprendeme ctx] {e}")

        peticion = (
            f"Genera UNA SOLA idea creativa, original y visualmente interesante para un prompt de {modo}. "
            f"Debe ser una escena con: sujeto específico + acción/situación + atmósfera + un toque de originalidad. "
            f"Estilo: ni demasiado cliché ni demasiado abstracta. Algo que dé ganas de generarla. "
            f"Evita conceptos sobreusados (cyberpunk genérico, dragones simples, etc).{contexto_modelo} "
            f"Responde con UNA SOLA frase en {'inglés' if get_idioma() == 'en' else 'español'}, máximo 30 palabras, sin explicaciones."
        )

        def _worker():
            try:
                resp = self.app.deepseek.generar(peticion, temperature=1.0, max_tokens=200)
                resp = limpiar_marcadores(resp).strip().strip('"').strip("'")
                def _aplicar():
                    self.app.txt_idea.delete("1.0", "end")
                    self.app.txt_idea.insert("1.0", resp)
                    self.app.dialogs.set_estado(tr("🎲 Idea sorpresa generada — pulsa ✨ Generar para crear el prompt"), "#2ecc71")
                    self.app.dialogs.toggle_botones(True)
                self.app.after(0, _aplicar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    PULSE_PRESET_3 = [
        (0.3, "🎯 Conservador (T=0.3)"),
        (0.6, "⚖️ Equilibrado (T=0.6)"),
        (0.9, "🎨 Creativo (T=0.9)"),
    ]
    PULSE_PRESET_5 = [
        (0.2, "🧊 Ultra estable (T=0.2)"),
        (0.4, "🎯 Conservador (T=0.4)"),
        (0.6, "⚖️ Equilibrado (T=0.6)"),
        (0.8, "🎨 Creativo (T=0.8)"),
        (1.0, "🔥 Máximo riesgo (T=1.0)"),
    ]

    def _cmd_pulse(self):
        """Modo Pulse: configura N versiones con temperaturas distintas.

        Mejoras v2:
        - 3 modos: 3 niveles (default), 5 niveles, Personalizado (sliders).
        - Recuerda la última configuración usada en preferencias.
        """
        idea = self.app.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.app.dialogs.set_estado(tr("⚠️ Escribe una idea base primero."), "#e67e22")

        # Cargar última configuración
        prefs = self.app.store.cargar_preferencias()
        ultima = prefs.get("pulse_config", {"modo": "3", "custom_temps": [0.3, 0.6, 0.9]})

        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        cfg = GPromptWindow(self.app)
        cfg.title(tr("⚡ Pulse — Configuración"))
        cfg.geometry("440x520")
        cfg.transient(self.app)
        cfg.grab_set()

        ctk.CTkLabel(cfg, text=tr("⚡ Pulse — Configuración"),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 4))
        ctk.CTkLabel(cfg,
                     text=tr("Cada nivel = un prompt con distinta temperatura.\nMenor T = más consistente, mayor T = más creativo."),
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"],
                     justify="center").pack(pady=(0, 12))

        modo_var = ctk.StringVar(value=ultima.get("modo", "3"))

        # Frame para sliders custom (visible solo si modo=custom)
        custom_frame = ctk.CTkFrame(cfg, fg_color=c["fg_dark"], corner_radius=6)
        custom_sliders = []

        def _toggle_custom():
            if modo_var.get() == "custom":
                custom_frame.pack(fill="x", padx=20, pady=8)
            else:
                custom_frame.pack_forget()

        for valor, label in [("3", "3 niveles (rápido): 0.3 · 0.6 · 0.9"),
                              ("5", "5 niveles (completo): 0.2 → 1.0"),
                              ("custom", "🎚 Personalizado (sliders abajo)")]:
            ctk.CTkRadioButton(cfg, text=label, variable=modo_var, value=valor,
                               command=_toggle_custom,
                               font=ctk.CTkFont(size=11)
                               ).pack(anchor="w", padx=30, pady=4)

        # Sliders custom (3 sliders)
        ctk.CTkLabel(custom_frame, text=tr("Temperaturas custom (3 niveles):"),
                     font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))
        temps_init = ultima.get("custom_temps", [0.3, 0.6, 0.9])
        for i in range(3):
            row = ctk.CTkFrame(custom_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)
            lbl_val = ctk.CTkLabel(row, text=tr('T{0}: {1:.2f}').format((i+1), (temps_init[i])),
                                    width=70, font=ctk.CTkFont(family="Consolas", size=10))
            lbl_val.pack(side="left", padx=(0, 6))
            sl = ctk.CTkSlider(row, from_=0.1, to=1.5, number_of_steps=28)
            sl.set(temps_init[i])
            sl.configure(command=lambda v, l=lbl_val, idx=i:
                          l.configure(text=tr('T{0}: {1:.2f}').format((idx+1), (float(v)))))
            sl.pack(side="left", fill="x", expand=True)
            custom_sliders.append(sl)

        _toggle_custom()

        def _ejecutar():
            modo_sel = modo_var.get()
            if modo_sel == "3":
                temperaturas = list(self.app.PULSE_PRESET_3)
            elif modo_sel == "5":
                temperaturas = list(self.app.PULSE_PRESET_5)
            else:
                temps_custom = [round(sl.get(), 2) for sl in custom_sliders]
                temperaturas = [(t, f"🎚 Custom (T={t:.2f})") for t in temps_custom]
            # Guardar config
            prefs_g = self.app.store.cargar_preferencias()
            prefs_g["pulse_config"] = {
                "modo": modo_sel,
                "custom_temps": [round(sl.get(), 2) for sl in custom_sliders],
            }
            self.app.store.guardar_preferencias(prefs_g)
            cfg.destroy()
            self._lanzar_pulse(idea, temperaturas)

        btn_row = ctk.CTkFrame(cfg, fg_color="transparent")
        btn_row.pack(side="bottom", pady=(0, 15))
        ctk.CTkButton(btn_row, text=tr("▶ Generar"), width=140, height=34,
                      fg_color="#1a8a3c", hover_color="#127a30",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=_ejecutar).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=tr("Cancelar"), width=100, height=34,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                      command=cfg.destroy).pack(side="left", padx=4)

        # Enter dispara generar
        cfg.bind("<Return>", lambda _e: _ejecutar())

    def _lanzar_pulse(self, idea, temperaturas):
        """Ejecuta Pulse con la lista de (temp, label) elegida."""
        try: self.app._sesion_log(f"⚡ Pulse: generó {len(temperaturas)} versiones")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.app.dialogs.set_estado(tr('⚡ Pulse: generando {0} versiones (T={1:.1f} → T={2:.1f})...').format((len(temperaturas)), (temperaturas[0][0]), (temperaturas[-1][0])),
                        "#f39c12")
        self.app.dialogs.toggle_botones(False)

        resultados = {}

        def _generar(temp, label):
            try:
                modo = self.app.modo_var.get()
                specs = self.app.get_current_model_specs()
                max_c = specs.get("max_chars", 1500) if specs else 1500
                has_neg = specs.get("has_negative", True) if specs else True
                is_natural = specs.get("is_natural", False) if specs else False
                fmt = "lenguaje natural descriptivo" if is_natural else "tags con pesos (tag:1.2)"
                neg_str = "Genera POSITIVE y NEGATIVE." if has_neg else "Solo POSITIVE (sin NEGATIVE)."

                peticion = (
                    f"Genera un prompt de {modo} basado en: {idea}\n"
                    f"Formato: {fmt}. Límite: {max_c} chars. {neg_str}\n"
                    f"Estilos: {self.app.footer.estilos_texto()}.\n"
                    f"Responde SOLO con el prompt, sin explicaciones."
                )
                resp = self.app.deepseek.generar(peticion, temperature=temp, max_tokens=2000)
                resp = limpiar_marcadores(resp)
                if not has_neg:
                    import re
                    resp = re.sub(r'\n?\s*NEGATIVE\s+PROMPT\s*:.*?$', '', resp, flags=re.DOTALL | re.IGNORECASE).strip()
                resultados[label] = resp
            except Exception as e:
                resultados[label] = f"❌ Error: {e}"

        def _worker_all():
            try:
                futs = [self.app._executor.submit(_generar, temp, label) for temp, label in temperaturas]
                concurrent.futures.wait(futs)

                def _mostrar():
                    # Construir lista para el comparador con label como "header"
                    variantes = []
                    for _, label in temperaturas:
                        if label in resultados:
                            variantes.append(f"### {label} ###\n{resultados[label]}")
                    self.app._abrir_comparador(variantes)
                    n = len(temperaturas)
                    self.app.dialogs.set_estado(tr('⚡ Pulse: {0} versiones listas — compara y elige').format(n), "#2ecc71")
                    self.app.dialogs.toggle_botones(True)
                    self.app.dialogs._sonar_completado()
                    self.app._notificar_sistema(tr("⚡ Pulse completado"),
                                             tr("{0} versiones del prompt listas para comparar").format(n))
                self.app.after(0, _mostrar)
            except Exception as e:
                logger.error(f"[Pulse] _worker_all falló: {e}")
                def _err(e=e):
                    self.app.dialogs.set_estado(tr('❌ Error en Pulse: {0}').format(e), "#e74c3c")
                    self.app.dialogs.toggle_botones(True)
                self.app.after(0, _err)

        threading.Thread(target=_worker_all, daemon=True).start()

    def _cmd_sugerir_negative_tab(self):
        """Variante para el botón en la pestaña Negativos: inserta el resultado
        en txt_negative (campo manual) en vez de actualizar el output principal."""
        if not self.app._debe_mostrar_negatives():
            return self.app.dialogs.set_estado(tr("⚠️ El modelo actual no usa NEGATIVE PROMPT."), "#e67e22")

        modelo = self.app.footer.modelo_imagen_valido() if self.app.modo_var.get() == "imagen" else (
            self.app.footer.modelo_video_valido() if self.app.modo_var.get() == "video" else "")
        pos = self.app.extraer_positive() or self.app.txt_idea.get("1.0", "end").strip() or "imagen general"

        self.app.dialogs.set_estado(tr("🛡 Generando negative sugerido..."), "#f39c12")
        self.app.dialogs.toggle_botones(False)

        peticion = (
            f"Genera el NEGATIVE PROMPT MÁS COMPLETO Y ÓPTIMO para este modelo y contenido.\n\n"
            f"MODELO: {modelo}\n"
            f"POSITIVE PROMPT (contexto):\n{pos[:500]}\n\n"
            f"REGLAS:\n"
            f"- Usa pesos (tag:1.4) para las protecciones más críticas.\n"
            f"- Cubre: baja calidad, deformaciones, artefactos JPEG, anatomía mala, manos/dedos malformados.\n"
            f"- Si el positive es realista, añade tags contra anime/cartoon/3D/painting.\n"
            f"- Si el positive es anime, añade tags contra photorealistic/photograph.\n"
            f"- Si hay personas: refuerza anatomía, ojos, dedos.\n"
            f"- Adapta a las debilidades conocidas del modelo {modelo}.\n\n"
            f"Responde SOLO con los tags negativos separados por comas, sin prefijos ni explicaciones."
        )

        def _worker():
            try:
                import re as _re
                resp = self.app.deepseek.generar_batch(
                    "Eres un experto en negative prompts para imagen IA. "
                    "Responde SOLO con los tags negativos separados por comas, sin explicaciones ni prefijos.",
                    peticion, temperature=0.2, max_tokens=500,
                )
                resp = limpiar_marcadores(resp).strip()
                m = _re.search(r'NEGATIVE\s+PROMPT\s*:?\s*(.+?)$', resp, _re.DOTALL | _re.IGNORECASE)
                negative = (m.group(1) if m else resp).strip()

                def _aplicar():
                    # Insertar como porción manual; _rebuild_negative_text añade los presets activos encima
                    self.app.txt_negative.delete("1.0", "end")
                    self.app.txt_negative.insert("1.0", negative)
                    self.app.footer._rebuild_negative_text()
                    self.app.dialogs.set_estado(tr("🛡 Negative sugerido aplicado"), "#2ecc71")
                    self.app.dialogs.toggle_botones(True)
                self.app.after(0, _aplicar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _cmd_negative_optimo(self):
        """Genera el NEGATIVE ÓPTIMO según el modelo y tipo de prompt actual."""
        if not self.app._debe_mostrar_negatives():
            return self.app.dialogs.set_estado(tr("⚠️ El modelo actual no usa NEGATIVE PROMPT."), "#e67e22")

        modelo = self.app.footer.modelo_imagen_valido() if self.app.modo_var.get() == "imagen" else (
            self.app.footer.modelo_video_valido() if self.app.modo_var.get() == "video" else "")
        pos = self.app.extraer_positive() or self.app.txt_idea.get("1.0", "end").strip() or "imagen general"

        self.app.dialogs.set_estado(tr("🛡 Generando NEGATIVE óptimo para este modelo..."), "#f39c12")
        self.app.dialogs.toggle_botones(False)

        peticion = (
            f"Genera el NEGATIVE PROMPT MÁS COMPLETO Y ÓPTIMO para este modelo y contenido.\n\n"
            f"MODELO: {modelo}\n"
            f"POSITIVE PROMPT (contexto):\n{pos[:500]}\n\n"
            f"REGLAS:\n"
            f"- Usa pesos (tag:1.4) para las protecciones más críticas.\n"
            f"- Cubre: baja calidad, deformaciones, artefactos JPEG, anatomía mala, manos/dedos malformados.\n"
            f"- Si el positive es realista, añade tags contra anime/cartoon/3D/painting.\n"
            f"- Si el positive es anime, añade tags contra photorealistic/photograph.\n"
            f"- Si hay personas: refuerza anatomía, ojos, dedos.\n"
            f"- Si hay paisaje: protege contra distorsión y bordes pixelados.\n"
            f"- Adapta a las debilidades conocidas del modelo {modelo}.\n\n"
            f"Responde SOLO con la línea NEGATIVE PROMPT en una sola línea, sin explicaciones."
        )

        def _worker():
            try:
                resp = self.app.deepseek.generar(peticion, temperature=0.2, max_tokens=400)
                resp = limpiar_marcadores(resp)
                import re
                m = re.search(r'NEGATIVE\s+PROMPT\s*:?\s*(.+?)$', resp, re.DOTALL | re.IGNORECASE)
                negative = (m.group(1) if m else resp).strip()

                def _aplicar():
                    pos_actual = self.app.extraer_positive()
                    if pos_actual:
                        nuevo = f"POSITIVE PROMPT: {pos_actual}\nNEGATIVE PROMPT: {negative}"
                        self.app.dialogs.actualizar_salida(nuevo)
                        self.app.dialogs.set_estado(tr("🛡 NEGATIVE óptimo aplicado"), "#2ecc71")
                    else:
                        # Solo poner negative si no hay positive
                        pyperclip.copy(negative)
                        self.app.dialogs.set_estado(tr("🛡 NEGATIVE óptimo copiado al portapapeles"), "#2ecc71")
                    self.app.dialogs.toggle_botones(True)
                self.app.after(0, _aplicar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _cmd_sugerir_modelo(self):
        """Analiza la idea y sugiere TOP 3 modelos.

        v2:
        - Pide al LLM TOP 3 modelos rankeados (no solo 1).
        - Muestra cada uno como card clicable con razón individual.
        - Botón "✅ Usar este modelo" por card.
        - Botón global "🚀 Probar los 3" → genera el prompt con cada
          uno y abre el comparador.
        """
        idea = self.app.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 10:
            return self.app.dialogs.set_estado(tr("⚠️ Escribe una idea más detallada."), "#e67e22")
        try: self.app._sesion_log("🤖 Sugerir modelo: analizó idea")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.app.dialogs.set_estado(tr("🤖 Analizando idea para top 3 modelos..."), "#f39c12")

        modo = self.app.modo_var.get()
        if modo == "imagen":
            modelos_lista = [m for m in MODELOS_IMAGEN_FLAT if not m.startswith("──")]
        elif modo == "video":
            modelos_lista = [m for m in MODELOS_VIDEO_FLAT if not m.startswith("──")]
        else:
            modelos_lista = [m for m in MODELOS_AUDIO_FLAT if not m.startswith("──")]

        # Resumen de specs para el LLM — TODOS los modelos del modo activo.
        # (Antes se enviaban solo los 20 primeros de la lista → el LLM siempre
        #  sugería los mismos modelos, sesgados al inicio alfabético; los ~100
        #  restantes nunca podían salir. Ver fix sesión 34.)
        specs_resumen = []
        for m in modelos_lista:
            s = get_image_model_specs(m) or get_model_specs(m) or get_audio_model_specs(m) or {}
            # 180 chars (antes 120): no cortar los descriptores de ESTILO del
            # best_for (p.ej. "estética punk-ink", "anime", "fotorrealista"),
            # que el LLM necesita para no elegir un modelo estilizado para una
            # idea realista. Ver fix sesión 34.
            specs_resumen.append(f"- {m}: {s.get('best_for', '')[:180]}")

        peticion = (
            f"Analiza esta idea y sugiere los 3 MEJORES modelos de {modo} rankeados.\n\n"
            f"IDEA: {idea}\n\n"
            f"MODELOS DISPONIBLES:\n" + "\n".join(specs_resumen) + "\n\n"
            f"IMPORTANTE — el ESTILO VISUAL del modelo debe encajar con lo que pide la idea:\n"
            f"- Si la idea busca una escena realista, visceral o fotográfica, prioriza modelos "
            f"FOTORREALISTAS o cinematográficos y EVITA los muy estilizados (anime, cómic, "
            f"ink/punk, cartoon, 3D) salvo que la idea pida ese estilo explícitamente.\n"
            f"- Si la idea pide un estilo concreto (anime, cómic, acuarela…), elige modelos de ESE estilo.\n"
            f"No te dejes llevar solo por palabras del tema (p.ej. 'horror') si el modelo no encaja en estilo.\n\n"
            f"Responde EN ESPAÑOL con este formato EXACTO (importante mantener \"#1:\", \"#2:\", \"#3:\"):\n\n"
            f"#1: [nombre exacto del modelo]\n"
            f"RAZÓN: [1 frase concreta]\n\n"
            f"#2: [nombre exacto del modelo]\n"
            f"RAZÓN: [1 frase concreta]\n\n"
            f"#3: [nombre exacto del modelo]\n"
            f"RAZÓN: [1 frase concreta]"
        )

        def _worker():
            try:
                resp = self.app.deepseek.generar(peticion, temperature=0.5, max_tokens=600)
                resp = limpiar_marcadores(resp)

                # Parsear las 3 sugerencias
                import re
                # Pattern: "#1: nombre\nRAZÓN: razón"
                pattern = r'#(\d)\s*:\s*([^\n]+)\n+\s*RAZ[ÓO]N\s*:\s*([^\n#]+(?:\n(?!#\d)[^\n]+)*)'
                matches = re.findall(pattern, resp, re.IGNORECASE)

                # Filtrar a modelos que existen realmente en la lista
                sugerencias = []
                for _rank, nombre, razon in matches[:3]:
                    nombre_limpio = nombre.strip().strip("[").strip("]").strip()
                    razon_limpia = razon.strip()
                    # Match exacto o por contenedor
                    coincidencia = None
                    if nombre_limpio in modelos_lista:
                        coincidencia = nombre_limpio
                    else:
                        # Búsqueda case-insensitive
                        nl_lower = nombre_limpio.lower()
                        for m_real in modelos_lista:
                            if nl_lower == m_real.lower() or nl_lower in m_real.lower():
                                coincidencia = m_real
                                break
                    if coincidencia:
                        sugerencias.append((coincidencia, razon_limpia))

                if not sugerencias:
                    self.app.after(0, lambda: self.app.dialogs.set_estado(
                        tr("⚠️ No se pudieron parsear las sugerencias del LLM"),
                        "#e67e22"))
                    return

                def _mostrar():
                    self._mostrar_sugerencias_modelo(idea, sugerencias, modo)
                self.app.after(0, _mostrar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _mostrar_sugerencias_modelo(self, idea, sugerencias, modo):
        """Modal con las 3 sugerencias de modelo + botón para probar los 3."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self.app)
        vent.title(tr("🤖 Top 3 modelos sugeridos"))
        vent.geometry("680x520")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("🤖 Top 3 modelos para tu idea"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4))
        ctk.CTkLabel(vent, text=tr('Idea: {0}{1}').format((idea[:80]), ('…' if len(idea) > 80 else '')),
                     font=ctk.CTkFont(size=10, slant="italic"),
                     text_color=c["muted_text"]).pack(pady=(0, 10))

        # Colores y rankings
        rank_data = [
            ("🥇", "#fbbf24", "#1a1a2e"),  # oro
            ("🥈", "#94a3b8", "#1a1a2e"),  # plata
            ("🥉", "#cd7f32", "#1a1a2e"),  # bronce
        ]

        def _aplicar_modelo(nombre):
            if modo == "imagen" and hasattr(self.app, 'combo_modelo_imagen'):
                self.app.combo_modelo_imagen.set(nombre)
                self.app.events.on_modelo_imagen_cambio()
            elif modo == "video" and hasattr(self.app, 'combo_modelo_video'):
                self.app.combo_modelo_video.set(nombre)
            elif modo == "audio" and hasattr(self.app, 'combo_modelo_audio'):
                self.app.combo_modelo_audio.set(nombre)
            vent.destroy()
            self.app.dialogs.set_estado(tr("✅ Modelo '{0}' aplicado").format(nombre), "#2ecc71")

        for idx, (nombre_mod, razon) in enumerate(sugerencias):
            medalla, bg_medalla, fg_medalla = rank_data[idx] if idx < 3 else ("#", c["fg_dark"], c["hdr_text"])
            card = ctk.CTkFrame(vent, fg_color=c["fg_frame"], corner_radius=8,
                                 border_color=bg_medalla, border_width=2)
            card.pack(fill="x", pady=6, padx=12)

            hdr = ctk.CTkFrame(card, fg_color="transparent")
            hdr.pack(fill="x", padx=10, pady=(8, 2))
            ctk.CTkLabel(hdr, text=f"  {medalla} {nombre_mod}",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=bg_medalla).pack(side="left")

            ctk.CTkLabel(card, text=f"  💡 {razon}",
                         font=ctk.CTkFont(size=10),
                         text_color=c["muted_text"],
                         wraplength=620, justify="left",
                         anchor="w").pack(fill="x", padx=10, pady=(0, 6))

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=10, pady=(0, 8))
            ctk.CTkButton(btn_row, text=tr('✅ Usar este modelo'),
                          width=180, height=28,
                          fg_color="#1a8a3c", hover_color="#127a30",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          command=lambda n=nombre_mod: _aplicar_modelo(n)
                          ).pack(side="left", padx=2)

        # Botón "Probar los 3" — genera el prompt con cada modelo y compara
        def _probar_los_3():
            vent.destroy()
            modelos_a_probar = [n for n, _ in sugerencias]
            self._probar_modelos_y_comparar(idea, modelos_a_probar, modo)

        accion_row = ctk.CTkFrame(vent, fg_color="transparent")
        accion_row.pack(side="bottom", pady=(8, 12))
        ctk.CTkButton(accion_row, text=tr('🚀 Probar los {0} en paralelo').format(len(sugerencias)),
                      width=240, height=34,
                      fg_color="#7c3aed", hover_color="#5d2ab5",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=_probar_los_3).pack(side="left", padx=4)
        ctk.CTkButton(accion_row, text=tr("Cerrar"), width=100, height=34,
                      fg_color=c["fg_dark"],
                      command=vent.destroy).pack(side="left", padx=4)

    def _probar_modelos_y_comparar(self, idea, modelos, modo):
        """Genera el prompt con cada modelo en paralelo y abre el comparador."""
        self.app.dialogs.set_estado(tr('🚀 Generando con {0} modelos en paralelo...').format(len(modelos)),
                        "#f39c12")
        self.app.dialogs.toggle_botones(False)

        resultados = {}

        def _gen_modelo(nombre_mod):
            try:
                from config import get_image_model_specs as _gim
                from config import get_model_specs as _gms
                specs = _gim(nombre_mod) or _gms(nombre_mod) or {}
                max_c = specs.get("max_chars", 1500)
                has_neg = specs.get("has_negative", True)
                is_natural = specs.get("is_natural", False)
                best_for = specs.get("best_for", "")[:200] if specs else ""

                fmt = "lenguaje natural descriptivo en una sola línea" if is_natural else "tags separados por comas con pesos opcionales (tag:1.2)"
                # Petición ESTRICTA — el bug anterior era que el LLM
                # devolvía POSITIVE+NEGATIVE+prosa+POSITIVE concatenados.
                # Aquí forzamos UNA sola sección sin texto adicional.
                if has_neg:
                    estructura = (
                        "DEVUELVE EXACTAMENTE 2 LÍNEAS y nada más:\n"
                        "Línea 1: POSITIVE PROMPT: <prompt en una línea>\n"
                        "Línea 2: NEGATIVE PROMPT: <negative en una línea>"
                    )
                else:
                    estructura = (
                        "DEVUELVE EXACTAMENTE 1 LÍNEA y nada más:\n"
                        "Línea 1: POSITIVE PROMPT: <prompt en una línea>"
                    )
                peticion = (
                    f"Genera UN prompt de {modo} optimizado para este modelo concreto:\n\n"
                    f"MODELO: {nombre_mod}\n"
                    f"FORTALEZAS: {best_for}\n\n"
                    f"IDEA: {idea}\n"
                    f"ESTILOS A INCLUIR: {self.app.footer.estilos_texto()}\n\n"
                    f"REGLAS ESTRICTAS:\n"
                    f"- Formato: {fmt}\n"
                    f"- Límite POSITIVE: {max_c} caracteres\n"
                    f"- Aprovecha las fortalezas del modelo {nombre_mod}\n"
                    f"- NO añadas explicaciones, NO añadas prosa descriptiva\n"
                    f"- NO repitas la sección POSITIVE/NEGATIVE\n\n"
                    f"{estructura}"
                )
                resp = self.app.deepseek.generar(peticion, temperature=0.55, max_tokens=1500)
                resp = limpiar_marcadores(resp)

                # Defensa contra LLMs que devuelven texto extra:
                # cortar SOLO al primer bloque POSITIVE [+ NEGATIVE].
                import re
                m_pos = re.search(r'POSITIVE\s+PROMPT\s*:\s*(.+?)(?=\n\s*NEGATIVE\s+PROMPT\s*:|\n\s*POSITIVE\s+PROMPT\s*:|\Z)',
                                  resp, flags=re.DOTALL | re.IGNORECASE)
                m_neg = re.search(r'NEGATIVE\s+PROMPT\s*:\s*(.+?)(?=\n\s*POSITIVE\s+PROMPT\s*:|\n\s*NEGATIVE\s+PROMPT\s*:|\Z)',
                                  resp, flags=re.DOTALL | re.IGNORECASE)
                if m_pos:
                    pos_clean = " ".join(m_pos.group(1).split())[:max_c * 2]  # margen de seguridad
                    if has_neg and m_neg:
                        neg_clean = " ".join(m_neg.group(1).split())
                        resp_limpio = f"POSITIVE PROMPT: {pos_clean}\nNEGATIVE PROMPT: {neg_clean}"
                    else:
                        resp_limpio = f"POSITIVE PROMPT: {pos_clean}"
                else:
                    # Fallback: respuesta sin etiquetas claras — asumir todo es POSITIVE
                    pos_clean = " ".join(resp.split())[:max_c * 2]
                    resp_limpio = f"POSITIVE PROMPT: {pos_clean}"

                resultados[nombre_mod] = resp_limpio
            except Exception as e:
                resultados[nombre_mod] = f"❌ Error: {e}"

        def _worker_all():
            try:
                futs = [self.app._executor.submit(_gen_modelo, nombre) for nombre in modelos]
                concurrent.futures.wait(futs)

                def _mostrar():
                    variantes = []
                    labels = []
                    for nombre in modelos:
                        if nombre in resultados:
                            variantes.append(resultados[nombre])
                            labels.append(f"🏆 {nombre}")
                    # Detectar si las respuestas son sospechosamente idénticas
                    # (mismo POSITIVE → LLM no diferenció entre modelos)
                    if len(set(resultados.values())) == 1 and len(resultados) > 1:
                        self.app.dialogs.set_estado(
                            tr("⚠️ El LLM devolvió la misma respuesta para todos los modelos. Prueba con una idea más específica."),
                            "#e67e22")
                    self.app._abrir_comparador(variantes, labels=labels)
                    self.app.dialogs.set_estado(tr('🚀 {0} versiones listas — elige tu favorita').format(len(modelos)),
                                    "#2ecc71")
                    self.app.dialogs.toggle_botones(True)
                    self.app.dialogs._sonar_completado()
                self.app.after(0, _mostrar)
            except Exception as e:
                logger.error(f"[MultiModelo] _worker_all falló: {e}")
                def _err(e=e):
                    self.app.dialogs.set_estado(tr('❌ Error en MultiModelo: {0}').format(e), "#e74c3c")
                    self.app.dialogs.toggle_botones(True)
                self.app.after(0, _err)

        threading.Thread(target=_worker_all, daemon=True).start()

    def _cmd_solo_negative(self):
        """Genera solo el NEGATIVE PROMPT optimizado."""
        if not self.app._debe_mostrar_negatives():
            return self.app.dialogs.set_estado(tr("⚠️ Este modelo no usa NEGATIVE."), "#e67e22")

        idea = self.app.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.app.dialogs.set_estado(tr("⚠️ Escribe una idea base primero."), "#e67e22")

        self.app.dialogs.set_estado(tr("🛡 Generando NEGATIVE optimizado..."), "#f39c12")
        self.app.dialogs.toggle_botones(False)

        modelo = self.app.footer.modelo_imagen_valido() if self.app.modo_var.get() == "imagen" else (
            self.app.footer.modelo_video_valido() if self.app.modo_var.get() == "video" else "")

        peticion = (
            f"Genera un NEGATIVE PROMPT optimizado para este modelo y contenido.\n\n"
            f"MODELO: {modelo}\n"
            f"IDEA BASE: {idea}\n\n"
            f"REGLAS:\n"
            f"- Usa pesos (tag:1.4) para las protecciones más importantes.\n"
            f"- Cubre: calidad baja, deformaciones, anatomía, manos, dedos, cara.\n"
            f"- Adapta según el modelo y tipo de contenido.\n\n"
            f"Responde SOLO con el NEGATIVE PROMPT, sin explicaciones."
        )

        def _worker():
            try:
                resp = self.app.deepseek.generar(peticion, temperature=0.3, max_tokens=400)
                resp = limpiar_marcadores(resp)
                import re
                m = re.search(r'NEGATIVE\s+PROMPT\s*:?\s*(.+?)$', resp, re.DOTALL | re.IGNORECASE)
                negative = (m.group(1) if m else resp).strip()

                def _aplicar():
                    pyperclip.copy(negative)
                    self.app.dialogs.set_estado(tr("🛡 NEGATIVE copiado al portapapeles"), "#2ecc71")
                    self.app.dialogs.toggle_botones(True)
                self.app.after(0, _aplicar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _cmd_grupo_personajes(self):
        """Define una escena con varios personajes y sus relaciones."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        vent = GPromptWindow(self.app)
        vent.title(tr("👥 Grupo de personajes"))
        vent.geometry("600x500")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("👥 Definir grupo de personajes"), font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text=tr("Define hasta 3 personajes que aparecerán juntos en la escena"),
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 10))

        personajes_data = []
        # Cargar personajes existentes
        personajes_lista = ["— Personaje nuevo —"] + [p.get("nombre", "?") for p in (self.app.store.personajes or [])]

        for i in range(3):
            f = ctk.CTkFrame(vent, fg_color=c["fg_frame"], corner_radius=6)
            f.pack(fill="x", padx=15, pady=4)

            ctk.CTkLabel(f, text=tr('Personaje #{0}:').format(i+1), font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(5, 2))

            row = ctk.CTkFrame(f, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)
            cb = ctk.CTkComboBox(row, values=personajes_lista, width=200, height=26)
            cb.set(personajes_lista[0])
            cb.pack(side="left", padx=(0, 5))

            ent_desc = ctk.CTkEntry(row, placeholder_text=tr("Posición/acción (ej: 'a la izquierda, mirando al frente')"), width=350, height=26)
            ent_desc.pack(side="left")

            personajes_data.append({"combo": cb, "desc": ent_desc})

        # Relación entre ellos — CTkTextbox no tiene placeholder_text nativo
        # así que simulamos uno: texto inicial gris, se borra al hacer focus.
        # Antes el placeholder se colaba en la idea generada si el usuario
        # no lo borraba manualmente.
        ctk.CTkLabel(vent, text=tr("Relación / contexto entre ellos:"),
                     font=ctk.CTkFont(size=11, weight="bold")
                     ).pack(anchor="w", padx=15, pady=(10, 2))
        txt_relacion = ctk.CTkTextbox(vent, height=60,
                                       font=ctk.CTkFont(size=11))
        txt_relacion.pack(fill="x", padx=15, pady=(0, 8))

        _placeholder_relacion = "ej: están negociando un contrato, primero plano de uno, los otros al fondo desenfocados"
        _relacion_state = {"placeholder_visible": True}
        _color_normal = txt_relacion.cget("text_color")

        def _mostrar_placeholder():
            txt_relacion.delete("1.0", "end")
            txt_relacion.insert("1.0", _placeholder_relacion)
            txt_relacion.configure(text_color="#6b7280")
            _relacion_state["placeholder_visible"] = True

        def _on_focus_in(_e=None):
            if _relacion_state["placeholder_visible"]:
                txt_relacion.delete("1.0", "end")
                txt_relacion.configure(text_color=_color_normal)
                _relacion_state["placeholder_visible"] = False

        def _on_focus_out(_e=None):
            if not txt_relacion.get("1.0", "end").strip():
                _mostrar_placeholder()

        _mostrar_placeholder()
        txt_relacion.bind("<FocusIn>", _on_focus_in)
        txt_relacion.bind("<FocusOut>", _on_focus_out)

        def _generar_grupo():
            personajes_def = []
            for i, p in enumerate(personajes_data):
                nombre_p = p["combo"].get()
                desc_p = p["desc"].get().strip()
                if nombre_p and nombre_p != "— Personaje nuevo —":
                    # Buscar el personaje en la base de datos
                    pers = next((x for x in (self.app.store.personajes or []) if x.get("nombre") == nombre_p), None)
                    if pers:
                        personajes_def.append({
                            "nombre": nombre_p,
                            "rasgos": pers.get("rasgos", ""),
                            "posicion": desc_p,
                        })
                    else:
                        personajes_def.append({"nombre": nombre_p, "rasgos": "", "posicion": desc_p})
                elif desc_p:
                    personajes_def.append({"nombre": f"Personaje #{i+1}", "rasgos": "", "posicion": desc_p})

            if len(personajes_def) < 2:
                self.app.dialogs.set_estado(tr("⚠️ Define al menos 2 personajes para hacer un grupo."), "#e67e22")
                return

            # Si el placeholder sigue visible, la relación se considera vacía
            relacion = "" if _relacion_state["placeholder_visible"] else txt_relacion.get("1.0", "end").strip()

            # Construir idea para el campo de idea
            idea_compuesta = f"Escena con {len(personajes_def)} personajes. "
            for p in personajes_def:
                idea_compuesta += f"{p['nombre']}"
                if p.get("rasgos"):
                    idea_compuesta += f" ({p['rasgos']})"
                idea_compuesta += f" {p.get('posicion', '')}. "
            if relacion:
                idea_compuesta += f"Contexto: {relacion}"

            self.app.txt_idea.delete("1.0", "end")
            self.app.txt_idea.insert("1.0", idea_compuesta)
            vent.destroy()
            self.app.dialogs.set_estado(tr('👥 {0} personajes preparados — pulsa ✨ Generar').format(len(personajes_def)), "#2ecc71")

        ctk.CTkButton(vent, text=tr("✅ Aplicar a la idea"), width=200, height=32,
                      fg_color="#1a7a3c", hover_color="#145e2d",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=_generar_grupo).pack(pady=10)

    def _cmd_analisis_inverso(self):
        """Compara una imagen con el prompt actual: ¿el prompt describe esa imagen?"""
        if not self.app.imagen_cargada:
            self.app.dialogs.set_estado(tr("⚠️ Carga una imagen primero (panel imagen ref)."), "#e67e22")
            return
        prompt_actual = self.app.txt_salida.get("1.0", "end").strip()
        if not prompt_actual or len(prompt_actual) < 20:
            self.app.dialogs.set_estado(tr("⚠️ Necesitas un prompt en el resultado para comparar."), "#e67e22")
            return
        try: self.app._sesion_log("🔍 Análisis inverso: comparó imagen con prompt actual")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.app.dialogs.set_estado(tr("🔍 Análisis inverso: comparando imagen y prompt..."), "#f39c12")
        self.app.dialogs.toggle_botones(False)

        def _worker():
            try:
                # 1. Describir la imagen primero
                def on_status(msg): self.app.after(0, lambda: self.app.dialogs.set_estado(msg, "#f39c12"))
                desc, motor = self.app.vision.describir(self.app.imagen_cargada, "imagen", on_status)

                # 2. Pedir al LLM comparar prompt con descripción
                peticion = (
                    f"Tienes DOS entradas: el análisis visual de una imagen y un prompt que supuestamente la describe.\n\n"
                    f"📷 ANÁLISIS VISUAL DE LA IMAGEN:\n{desc}\n\n"
                    f"📝 PROMPT QUE SUPUESTAMENTE LA DESCRIBE:\n{prompt_actual}\n\n"
                    f"Tu tarea: ANALIZAR si el prompt realmente describe lo que se ve en la imagen.\n\n"
                    f"FORMATO DE RESPUESTA en español:\n"
                    f"COINCIDENCIA: X/100% (porcentaje de coincidencia)\n\n"
                    f"✅ ELEMENTOS QUE COINCIDEN (3-5 puntos):\n"
                    f"   - Lista los elementos del prompt que SÍ se ven en la imagen\n\n"
                    f"❌ ELEMENTOS QUE FALTAN EN EL PROMPT (3-5 puntos):\n"
                    f"   - Lista cosas visibles en la imagen pero NO mencionadas en el prompt\n\n"
                    f"⚠️ ELEMENTOS DEL PROMPT QUE NO ESTÁN EN LA IMAGEN (3-5 puntos):\n"
                    f"   - Lista cosas que el prompt menciona pero NO se ven en la imagen\n\n"
                    f"🔧 PROMPT CORREGIDO:\n"
                    f"   - Reescribe el prompt para que describa fielmente la imagen real\n"
                    f"   - Mantén el formato original (tags/natural)\n"
                )
                resp = self.app.deepseek.generar(peticion, temperature=0.3, max_tokens=2500)
                resp = limpiar_marcadores(resp)

                def _mostrar():
                    is_lt = ctk.get_appearance_mode().lower() == "light"
                    c = get_theme_colors(is_lt)
                    vent = GPromptWindow(self.app)
                    vent.title(tr("🔍 Análisis inverso"))
                    vent.geometry("700x600")
                    vent.transient(self.app)
                    ctk.CTkLabel(vent, text=tr("🔍 Análisis inverso: imagen vs prompt"), font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
                    ctk.CTkLabel(vent, text=tr('Visión: {0}').format(motor), font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

                    txt = ctk.CTkTextbox(vent, font=ctk.CTkFont(size=11), wrap="word")
                    txt.pack(fill="both", expand=True, padx=15, pady=(0, 5))
                    txt.insert("1.0", resp)
                    txt.configure(state="disabled")

                    btn_frame = ctk.CTkFrame(vent, fg_color="transparent")
                    btn_frame.pack(pady=10)

                    # Helper: extraer el PROMPT CORREGIDO del análisis
                    def _extraer_corregido():
                        import re
                        m = re.search(r'PROMPT\s+CORREGIDO[:\s]*\n(.+?)(?=\Z)',
                                       resp, re.DOTALL | re.IGNORECASE)
                        return m.group(1).strip() if m else None

                    def _copiar_analisis_completo():
                        pyperclip.copy(resp)
                        self.app.dialogs.set_estado(tr("📋 Análisis completo copiado"), "#2ecc71")

                    def _copiar_solo_corregido():
                        corregido = _extraer_corregido()
                        if corregido:
                            pyperclip.copy(corregido)
                            self.app.dialogs.set_estado(tr("📋 PROMPT CORREGIDO copiado al portapapeles"), "#2ecc71")
                        else:
                            self.app.dialogs.set_estado(tr("⚠️ El análisis no incluye 'PROMPT CORREGIDO' parseable"), "#e67e22")

                    def _aplicar_corregido():
                        # Pasa por el diff modal en lugar de sobreescribir
                        # directo: el usuario decide aplicar/cancelar tras
                        # ver los cambios.
                        corregido = _extraer_corregido()
                        if not corregido:
                            self.app.dialogs.set_estado(tr("⚠️ El análisis no incluye 'PROMPT CORREGIDO' parseable"), "#e67e22")
                            return
                        texto_previo = self.app.txt_salida.get("1.0", "end").strip()
                        if not texto_previo:
                            # No hay nada que comparar — aplicar directo
                            self.app.dialogs.actualizar_salida(corregido)
                            vent.destroy()
                            self.app.dialogs.set_estado(tr("✅ Prompt corregido aplicado"), "#2ecc71")
                            return
                        # Pasamos por refinar.mostrar_diff_refinamiento → Aplicar/Cancelar
                        if hasattr(self.app, '_mostrar_diff_refinamiento'):
                            vent.destroy()
                            self.app.refinar.mostrar_diff_refinamiento(texto_previo, corregido)
                        else:
                            # Fallback si el método no existe
                            self.app.dialogs.actualizar_salida(corregido)
                            vent.destroy()
                            self.app.dialogs.set_estado(tr("✅ Prompt corregido aplicado"), "#2ecc71")

                    ctk.CTkButton(btn_frame, text=tr("📋 Copiar análisis"), width=140, height=28,
                                  fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                                  command=_copiar_analisis_completo).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text=tr("📋 Solo corregido"), width=130, height=28,
                                  fg_color="#475569", hover_color="#374151",
                                  command=_copiar_solo_corregido).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text=tr("✅ Aplicar (con diff)"), width=160, height=28,
                                  fg_color="#1a7a3c", hover_color="#15633a",
                                  command=_aplicar_corregido).pack(side="left", padx=4)

                    self.app.dialogs.toggle_botones(True)
                    self.app.dialogs.set_estado(tr('🔍 Análisis inverso completado (visión: {0})').format(motor), "#2ecc71")
                self.app.after(0, _mostrar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _cmd_sugerir_estilos(self):
        """Analiza la idea y marca automáticamente los estilos más apropiados."""
        idea = self.app.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.app.dialogs.set_estado(tr("⚠️ Escribe una idea primero."), "#e67e22")
        try: self.app._sesion_log("🎨 Sugerir estilos: pidió sugerencia automática")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        # Imagen, vídeo Y audio tienen estilo_checks poblados (audio con
        # ESTILOS_AUDIO). Antes audio estaba bloqueado por descuido.
        estilos_dispo = list(self.app.estilo_checks.keys())
        if not estilos_dispo:
            return self.app.dialogs.set_estado(tr("⚠️ No hay estilos disponibles."), "#e67e22")

        self.app.dialogs.set_estado(tr("🎨 Analizando idea para sugerir estilos..."), "#f39c12")
        self.app.dialogs.toggle_botones(False)

        peticion = (
            f"Analiza esta idea y sugiere LOS 3-6 ESTILOS MÁS APROPIADOS de la lista disponible.\n\n"
            f"IDEA: {idea}\n\n"
            f"ESTILOS DISPONIBLES:\n{', '.join(estilos_dispo[:200])}\n\n"
            f"REGLAS:\n"
            f"- Devuelve SOLO los nombres EXACTOS de la lista (no inventes nuevos).\n"
            f"- Sugiere entre 3 y 6 estilos que combinen bien.\n"
            f"- Prioriza coherencia (ej: no mezcles 'Anime' con 'Fotografía Realista').\n\n"
            f"FORMATO: Lista separada por COMAS, una sola línea, sin números ni explicaciones.\n"
            f"EJEMPLO: Cinematográfico 4K, Cinematic Noir, Drama Cinematográfico"
        )

        def _worker():
            try:
                # generar_batch: stateless, sin historial — evita contaminación
                # de contexto con Gemini y otros LLMs multi-turno.
                resp = self.app.deepseek.generar_batch(
                    "Eres un asistente experto en estilos de imagen IA. "
                    "Responde SOLO con los nombres exactos de la lista, separados por comas. "
                    "Sin explicaciones, sin numeración, sin puntos al final.",
                    peticion,
                    temperature=0.3, max_tokens=300,
                )
                resp = limpiar_marcadores(resp).strip()

                # Parsear CSV o bullet-list (Gemini devuelve * estilo a veces)
                if "," in resp:
                    sugeridos = [s.strip(" *-•.\n") for s in resp.split(",") if s.strip(" *-•.\n")]
                else:
                    sugeridos = [s.strip(" *-•.\n") for s in resp.splitlines() if s.strip(" *-•.\n")]

                validos = [s for s in sugeridos if s in estilos_dispo]

                # Fallback fuzzy
                if not validos:
                    for s in sugeridos:
                        for est in estilos_dispo:
                            if s.lower() in est.lower() or est.lower() in s.lower():
                                validos.append(est)
                                break

                if not validos:
                    self.app.after(0, lambda: self.app.dialogs.set_estado(tr("⚠️ No se pudieron extraer estilos. Intenta de nuevo."), "#e67e22"))
                    self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))
                    return

                def _aplicar():
                    for n, v in self.app.estilo_checks.items():
                        v.set(False)
                    for est in validos:
                        if est in self.app.estilo_checks:
                            self.app.estilo_checks[est].set(True)
                    self.app.dialogs.set_estado(tr('🎨 Estilos aplicados: {0}').format(', '.join(validos)), "#2ecc71")
                    self.app.dialogs.toggle_botones(True)
                self.app.after(0, _aplicar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _cmd_sugerir_tags(self):
        """Analiza la idea y añade al campo idea los tags técnicos más apropiados."""
        from config import TAG_PICKER_CATEGORIES
        idea = self.app.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.app.dialogs.set_estado(tr("⚠️ Escribe una idea primero."), "#e67e22")

        todos_tags_en = [val_en for tags in TAG_PICKER_CATEGORIES.values() for _, val_en, _ in tags]
        if not todos_tags_en:
            return self.app.dialogs.set_estado(tr("⚠️ No hay tags disponibles."), "#e67e22")

        self.app.dialogs.set_estado(tr("🏷️ Analizando idea para sugerir tags..."), "#f39c12")
        self.app.dialogs.toggle_botones(False)

        peticion = (
            f"Analiza esta idea y sugiere 3-5 TAGS TÉCNICOS de la lista que la mejorarían visualmente.\n\n"
            f"IDEA: {idea}\n\n"
            f"TAGS DISPONIBLES:\n{', '.join(todos_tags_en)}\n\n"
            f"REGLAS:\n"
            f"- Devuelve SOLO los valores EXACTOS de la lista (no inventes nuevos).\n"
            f"- Elige tags que complementen la idea sin contradecirse.\n\n"
            f"FORMATO: Lista separada por COMAS, una sola línea.\n"
            f"EJEMPLO: cinematic lighting, shallow depth of field, golden hour"
        )

        def _worker():
            try:
                resp = self.app.deepseek.generar_batch(
                    "Eres un experto en prompts de imagen IA. Sugiere tags técnicos visuales. "
                    "Responde SOLO con los valores exactos de la lista separados por comas.",
                    peticion,
                    temperature=0.3, max_tokens=200,
                )
                resp = limpiar_marcadores(resp).strip()

                if "," in resp:
                    sugeridos = [t.strip(" *-•.\n") for t in resp.split(",") if t.strip(" *-•.\n")]
                else:
                    sugeridos = [t.strip(" *-•.\n") for t in resp.splitlines() if t.strip(" *-•.\n")]

                validos = [t for t in sugeridos if t in todos_tags_en]

                if not validos:
                    for t in sugeridos:
                        for tag in todos_tags_en:
                            if t.lower() in tag.lower() or tag.lower() in t.lower():
                                validos.append(tag)
                                break

                if not validos:
                    self.app.after(0, lambda: self.app.dialogs.set_estado(tr("⚠️ No se encontraron tags válidos. Intenta de nuevo."), "#e67e22"))
                    self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))
                    return

                def _aplicar():
                    current = self.app.txt_idea.get("1.0", "end-1c").strip()
                    sep = ", " if current else ""
                    self.app.txt_idea.insert("end", sep + ", ".join(validos))
                    self.app.txt_idea.see("end")
                    self.app.dialogs.set_estado(tr('🏷️ Tags añadidos: {0}').format(', '.join(validos)), "#2ecc71")
                    self.app.dialogs.toggle_botones(True)
                self.app.after(0, _aplicar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _cmd_anclaje_visual(self):
        """ADN visual: extrae rasgos detallados de imagen ref y los guarda como anclaje inmutable.

        v1.1: progreso visual, preview imagen, guardar en biblioteca ADN,
        mostrar rasgos activos, barra de estado.
        """
        if not self.app.imagen_cargada:
            self.app.dialogs.set_estado(tr("⚠️ Carga una imagen de referencia primero."), "#e67e22")
            return

        self.app.dialogs.set_estado(tr("🧬 Extrayendo ADN visual (rasgos exactos)..."), "#f39c12")
        self.app.dialogs.toggle_botones(False)

        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self.app)
        vent.title(tr("🧬 ADN visual — Extracción"))
        vent.geometry("720x580")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("🧬 Extracción de ADN visual"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 2))
        ctk.CTkLabel(vent, text=tr("Analizando imagen de referencia para extraer rasgos inmutables"),
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 6))

        # Preview de la imagen cargada
        prev_frame = ctk.CTkFrame(vent, fg_color=c["fg_dark"], corner_radius=8)
        prev_frame.pack(fill="x", padx=15, pady=(0, 6))
        ctk.CTkLabel(prev_frame, text=tr("🖼 Imagen de referencia"),
                     font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(6, 2))
        img_preview = ctk.CTkLabel(prev_frame, text="")
        img_preview.pack(padx=10, pady=(0, 4))
        try:
            img_copy = self.app.imagen_cargada.copy()
            img_copy.thumbnail((160, 120))
            img_tk = ctk.CTkImage(img_copy, size=(img_copy.width, img_copy.height))
            img_preview.configure(image=img_tk)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # Estado / progreso
        lbl_estado = ctk.CTkLabel(vent, text=tr("⏳ Iniciando extracción..."),
                                   font=ctk.CTkFont(size=11), text_color="#f39c12")
        lbl_estado.pack(anchor="w", padx=15, pady=(0, 4))
        prog_bar = ctk.CTkProgressBar(vent, height=8)
        prog_bar.pack(fill="x", padx=15, pady=(0, 8))
        prog_bar.set(0)

        def _actualizar_progreso(pct, msg):
            prog_bar.set(pct)
            lbl_estado.configure(text=msg, text_color="#f39c12")

        def _trabajar():
            try:
                self.app.after(0, lambda: _actualizar_progreso(0.1, "🔍 Describiendo imagen..."))
                def on_status(msg): self.app.after(0, lambda m=msg: _actualizar_progreso(0.2, m))
                desc, motor = self.app.vision.describir(self.app.imagen_cargada, "imagen", on_status)

                self.app.after(0, lambda: _actualizar_progreso(0.5, "🧬 Extrayendo rasgos visuales..."))
                peticion = (
                    f"De esta descripción visual de una imagen, EXTRAE el ADN visual: rasgos físicos EXACTOS y constantes que deben mantenerse en cualquier variante futura.\n\n"
                    f"DESCRIPCIÓN VISUAL:\n{desc}\n\n"
                    f"FORMATO DE RESPUESTA — usa exactamente este formato (en inglés, separado por comas, lista de tags):\n\n"
                    f"PERSONAJE: [color exacto pelo, color exacto ojos, edad aproximada, género, rasgos faciales únicos, complexión]\n"
                    f"ROPA: [prendas específicas con colores y materiales]\n"
                    f"ACCESORIOS: [joyas, gafas, sombrero, etc.]\n"
                    f"MARCAS DISTINTIVAS: [tatuajes, cicatrices, lunares específicos]\n"
                    f"DETALLES CLAVE: [3-5 elementos que NO deben cambiar nunca]\n\n"
                    f"Sé MUY específico. 'pelo plateado plata-azulado' es mejor que 'pelo gris'. 'ojos verdes esmeralda con manchas doradas' es mejor que 'ojos verdes'."
                )
                adn = self.app.deepseek.generar(peticion, temperature=0.2, max_tokens=800)
                adn = limpiar_marcadores(adn).strip()
                self.app._anclaje_visual = adn
                if hasattr(self.app, "_actualizar_indicador_adn"):
                    self.app.after(0, self.app._actualizar_indicador_adn)
                self.app.after(0, lambda: _actualizar_progreso(0.9, tr("✅ Extracción completada")))

                def _mostrar():
                    prog_bar.pack_forget()
                    lbl_estado.pack_forget()
                    prev_frame.pack_forget()

                    vent2 = GPromptWindow(self.app)
                    vent2.title(tr("🧬 ADN visual extraído"))
                    vent2.geometry("700x500")
                    vent2.transient(self.app)
                    ctk.CTkLabel(vent2, text=tr("🧬 ADN visual — Rasgos inmutables"),
                                 font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
                    estado_activo = "🟢 ACTIVO" if self.app._anclaje_visual else "⚪ Inactivo"
                    ctk.CTkLabel(vent2, text=tr('Vision: {0}  ·  Estado: {1}').format((motor), (estado_activo)),
                                  font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

                    txt = ctk.CTkTextbox(vent2, font=ctk.CTkFont(size=11), wrap="word", height=320)
                    txt.pack(fill="both", expand=True, padx=15, pady=(0, 5))
                    txt.insert("1.0", adn)

                    btn_frame = ctk.CTkFrame(vent2, fg_color="transparent")
                    btn_frame.pack(pady=10)

                    def _guardar_editado():
                        self.app._anclaje_visual = txt.get("1.0", "end").strip()
                        if hasattr(self.app, "_actualizar_indicador_adn"):
                            self.app._actualizar_indicador_adn()
                        vent2.destroy()
                        self.app.dialogs.set_estado(tr("🧬 ADN visual guardado y activo en próximas generaciones"), "#2ecc71")

                    def _desactivar():
                        self.app._anclaje_visual = None
                        if hasattr(self.app, "_actualizar_indicador_adn"):
                            self.app._actualizar_indicador_adn()
                        vent2.destroy()
                        self.app.dialogs.set_estado(tr("🧬 ADN visual desactivado"))

                    def _guardar_biblioteca():
                        # Persiste el ADN-texto en preferencias bajo
                        # `adns_guardados` con marcador texto_libre, para que
                        # la biblioteca pueda renderizarlo.
                        from tkinter import simpledialog
                        prefs_b = self.app.store.cargar_preferencias()
                        adns_b = prefs_b.get("adns_guardados", []) or []
                        if not isinstance(adns_b, list):
                            adns_b = []
                        sugerencia = f"ADN rasgos {len(adns_b) + 1}"
                        nombre = simpledialog.askstring(
                            tr("💾 Guardar ADN"),
                            tr("Nombre para este ADN:"),
                            initialvalue=sugerencia,
                            parent=vent2,
                        )
                        if not nombre:
                            return
                        adn_text = txt.get("1.0", "end").strip()
                        adns_b.append({
                            "nombre": nombre.strip(),
                            "adn": {"texto_libre": adn_text},
                            "motor": motor,
                            "fecha": datetime.datetime.now().strftime("%Y-%m-%d"),
                        })
                        prefs_b["adns_guardados"] = adns_b
                        self.app.store.guardar_preferencias(prefs_b)
                        self.app.dialogs.set_estado(tr("💾 ADN '{0}' guardado en biblioteca").format(nombre), "#2ecc71")

                    ctk.CTkButton(btn_frame, text=tr("✅ Guardar y activar"), width=150, height=30, fg_color="#1a7a3c",
                                  command=_guardar_editado).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text=tr("💾 Guardar en biblioteca"), width=160, height=30, fg_color="#4a1a6a",
                                  command=_guardar_biblioteca).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text=tr("📚 Ver biblioteca"), width=130, height=30,
                                  fg_color="#6a4a8a", hover_color="#503870",
                                  command=self.app.adn.cmd_ver_biblioteca
                                  ).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text=tr("🚫 Desactivar"), width=100, height=30, fg_color="#5a1a1a",
                                  command=_desactivar).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text=tr("📋 Copiar"), width=80, height=30,
                                  command=lambda: pyperclip.copy(adn)).pack(side="left", padx=4)

                    self.app.dialogs.toggle_botones(True)
                    self.app.dialogs.set_estado(tr("🧬 ADN visual extraído — guarda para activarlo"), "#2ecc71")
                self.app.after(0, _mostrar)
            except Exception as e:
                self.app.after(0, lambda: prog_bar.pack_forget())
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        ctk.CTkButton(vent, text=tr("🧬 Iniciar extracción"), width=200, height=34, fg_color="#7c3aed",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      text_color="#ffffff", command=lambda: self.app._executor.submit(_trabajar).add_done_callback(log_future_exc)
                      ).pack(pady=8)

    def _cmd_variar_con_anclaje(self):
        """Genera variantes manteniendo el ADN visual como rasgos fijos."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        if not getattr(self.app, '_anclaje_visual', None):
            self.app.dialogs.set_estado(tr("⚠️ Primero extrae el ADN visual con 🧬 ADN."), "#e67e22")
            return
        idea = self.app.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            self.app.dialogs.set_estado(tr("⚠️ Escribe una idea base (qué quieres variar)."), "#e67e22")
            return

        # Ventana selección
        sel = GPromptWindow(self.app)
        sel.title(tr("🧬 Variar con ADN"))
        sel.geometry("520x520")
        sel.transient(self.app)
        ctk.CTkLabel(sel, text=tr("🧬 Variar con ADN visual"), font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 3))
        ctk.CTkLabel(sel, text=tr("El sujeto mantendrá sus rasgos exactos. Solo cambia el contexto:"),
                     font=ctk.CTkFont(size=11), text_color=c["muted_text"]).pack(pady=(0, 12))

        # Cantidad
        f = ctk.CTkFrame(sel, fg_color="transparent")
        f.pack(pady=5)
        ctk.CTkLabel(f, text=tr("Cantidad de variantes:")).pack(side="left", padx=8)
        ent_n = ctk.CTkEntry(f, width=60); ent_n.insert(0, "5"); ent_n.pack(side="left")

        # Qué variar (10 opciones)
        ctk.CTkLabel(sel, text=tr("Qué cambiar (ADN se mantiene):"), font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(15, 3))
        opciones = [
            "Localización / fondo",
            "Ropa diferente (cambiar prendas)",
            "Pose y expresión",
            "Iluminación y atmósfera",
            "Acción que está realizando",
            "Estilo artístico",
            "Hora del día / clima",
            "Ángulo de cámara y plano",
            "Paleta de color dominante",
            "Época o ambientación temporal",
        ]
        var_op = ctk.StringVar(value=opciones[0])
        cb = ctk.CTkComboBox(sel, values=opciones, variable=var_op, width=340, height=28)
        cb.pack()

        ent_extra = ctk.CTkEntry(sel, placeholder_text=tr("Detalle adicional (opcional)"), width=350, height=28)
        ent_extra.pack(pady=(15, 5))

        def _ejecutar():
            try: cantidad = int(ent_n.get())
            except Exception: cantidad = 5
            cantidad = max(1, min(cantidad, 20))
            elemento = var_op.get()
            extra = ent_extra.get().strip()
            sel.destroy()
            self._generar_variantes_con_anclaje(idea, elemento, extra, cantidad)

        ctk.CTkButton(sel, text=tr("🧬 Generar variantes"), width=200, height=32,
                      fg_color="#1a7a3c", command=_ejecutar).pack(pady=15)

    def _generar_variantes_con_anclaje(self, idea, elemento, extra, cantidad):
        """Worker para generar N variantes manteniendo ADN."""
        self.app.dialogs.set_estado(tr('🧬 Generando {0} variantes con ADN anclado...').format(cantidad), "#f39c12")
        self.app.dialogs.toggle_botones(False)
        adn = self.app._anclaje_visual
        modo = self.app.modo_var.get()
        resultados = []

        def _generar_una(num):
            try:
                specs = self.app.get_current_model_specs()
                has_neg = specs.get("has_negative", True) if specs else True
                is_natural = specs.get("is_natural", False) if specs else False
                fmt = "lenguaje natural descriptivo" if is_natural else "tags con pesos"
                neg_str = "Genera POSITIVE y NEGATIVE." if has_neg else "Solo POSITIVE (sin NEGATIVE)."

                peticion = (
                    f"Genera la variante #{num} de {cantidad} de un prompt de {modo}.\n\n"
                    f"⚓ ADN VISUAL INMUTABLE (estos rasgos NO PUEDEN cambiar nunca):\n{adn}\n\n"
                    f"IDEA BASE: {idea}\n"
                    f"QUÉ CAMBIAR EN ESTA VARIANTE: {elemento}{f' — {extra}' if extra else ''}\n\n"
                    f"REGLAS:\n"
                    f"- TODOS los rasgos del ADN deben aparecer literalmente en el POSITIVE.\n"
                    f"- SOLO cambia: {elemento}\n"
                    f"- Esta variante debe ser DIFERENTE a las anteriores en lo que cambia.\n"
                    f"- Formato: {fmt}\n"
                    f"- {neg_str}\n\n"
                    f"FORMATO:\nPOSITIVE PROMPT: [prompt completo con ADN intacto]\nNEGATIVE PROMPT: [si aplica]\n"
                )
                resp = self.app.deepseek.generar(peticion, temperature=0.7, max_tokens=2000)
                resp = limpiar_marcadores(resp)
                if not has_neg:
                    import re
                    resp = re.sub(r'\n?\s*NEGATIVE\s+PROMPT\s*:.*?$', '', resp, flags=re.DOTALL | re.IGNORECASE).strip()
                resultados.append(resp)
                self.app.guardar_en_historial(resp)
            except Exception as e:
                resultados.append(f"❌ Error en variante {num}: {e}")

        def _worker_all():
            for i in range(1, cantidad + 1):
                _generar_una(i)
                self.app.after(0, lambda i=i: self.app.dialogs.set_estado(tr('🧬 Variante {0}/{1} lista').format(i, cantidad), "#3498db"))
            def _mostrar():
                self.app._abrir_comparador(resultados)
                self.app.dialogs.set_estado(tr('🧬 {0} variantes con ADN listas').format(len(resultados)), "#2ecc71")
                self.app.dialogs.toggle_botones(True)
                self.app.dialogs._sonar_completado()
            self.app.after(0, _mostrar)

        self.app._executor.submit(_worker_all)

    def _cmd_comparar_consistencia(self):
        """Compara dos prompts e indica qué difiere y qué coincide."""
        actual = self.app.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.app.dialogs.set_estado(tr("⚠️ Necesitas un prompt en el resultado."), "#e67e22")

        # Pedir el segundo prompt
        from tkinter import simpledialog
        otro = simpledialog.askstring(tr("🔍 Comparar consistencia"),
                                        tr("Pega aquí el otro prompt a comparar (el actual es el del resultado):"),
                                        parent=self.app)
        if not otro or len(otro) < 20:
            return self.app.dialogs.set_estado(tr("⚠️ Pega un prompt válido para comparar."), "#e67e22")

        self.app.dialogs.set_estado(tr("🔍 Analizando consistencia entre prompts..."), "#f39c12")
        self.app.dialogs.toggle_botones(False)

        peticion = (
            f"Compara estos dos prompts y analiza la CONSISTENCIA entre ellos.\n\n"
            f"PROMPT A:\n{actual}\n\n"
            f"PROMPT B:\n{otro}\n\n"
            f"RESPONDE en español con este formato exacto:\n\n"
            f"📊 CONSISTENCIA: X/100% (qué tan similares son)\n\n"
            f"✅ ELEMENTOS QUE COINCIDEN (rasgos compartidos importantes):\n"
            f"   - Lista de elementos clave que aparecen en ambos\n\n"
            f"⚠️ DIFERENCIAS PRINCIPALES:\n"
            f"   - Lista de qué cambia entre A y B\n\n"
            f"🚨 INCONSISTENCIAS DETECTADAS (si los prompts deberían describir al MISMO sujeto/escena):\n"
            f"   - Lista de elementos que deberían ser iguales pero difieren\n\n"
            f"💡 SUGERENCIA: \n"
            f"   - 1-2 frases sobre cómo armonizar ambos prompts si fueran serie/secuencia\n"
        )

        def _worker():
            try:
                resp = self.app.deepseek.generar(peticion, temperature=0.3, max_tokens=2000)
                resp = limpiar_marcadores(resp)

                def _mostrar():
                    vent = GPromptWindow(self.app)
                    vent.title(tr("🔍 Análisis de consistencia"))
                    vent.geometry("700x550")
                    vent.transient(self.app)
                    ctk.CTkLabel(vent, text=tr("🔍 Consistencia entre prompts"), font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 5))
                    txt = ctk.CTkTextbox(vent, font=ctk.CTkFont(size=11), wrap="word")
                    txt.pack(fill="both", expand=True, padx=15, pady=(0, 5))
                    txt.insert("1.0", resp)
                    txt.configure(state="disabled")
                    ctk.CTkButton(vent, text=tr("📋 Copiar"), width=100, height=28,
                                  command=lambda: pyperclip.copy(resp)).pack(pady=10)
                    self.app.dialogs.toggle_botones(True)
                    self.app.dialogs.set_estado(tr("🔍 Consistencia analizada"), "#2ecc71")
                self.app.after(0, _mostrar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _cmd_negative_builder(self):
        """Constructor visual de NEGATIVE PROMPT con checkboxes temáticos.

        v1.1: búsqueda/filtrar, guardar preset, mostrar activos, tabs por categoría.
        """
        if not self.app._debe_mostrar_negatives():
            return self.app.dialogs.set_estado(tr("⚠️ Este modelo no usa NEGATIVE."), "#e67e22")

        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        vent = GPromptWindow(self.app)
        vent.title(tr("🧰 Constructor de NEGATIVE"))
        vent.geometry("700x720")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("🧰 Constructor de NEGATIVE"), font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 2))
        lbl_activos = ctk.CTkLabel(vent, text="", font=ctk.CTkFont(size=9), text_color="#2ecc71")
        lbl_activos.pack(pady=(0, 4))

        # Búsqueda
        search_row = ctk.CTkFrame(vent, fg_color="transparent")
        search_row.pack(fill="x", padx=15, pady=(0, 4))
        search_entry = ctk.CTkEntry(search_row, placeholder_text=tr("🔍 Busca un elemento..."),
                                      height=28, font=ctk.CTkFont(size=11))
        search_entry.pack(fill="x")

        tabs = ctk.CTkTabview(vent, height=460)
        tabs.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        categorias = NEGATIVE_BUILDER_CATEGORIAS

        # check_vars[nombre] = (BooleanVar, tags, checkbox_widget)
        # Los checkboxes se crean UNA SOLA VEZ al inicio. El filtro
        # solo hace pack_forget()/pack() para no perder estado visual.
        check_vars = {}

        def _actualizar_lbl():
            n = sum(1 for tup in check_vars.values() if tup[0].get())
            activos = [tr(nom) for nom, tup in check_vars.items() if tup[0].get()]
            extra = f"… (+{len(activos) - 5})" if len(activos) > 5 else ""
            lbl_activos.configure(
                text=tr('✅ {0} activos: {1}{2}').format((n), (', '.join(activos[:5])), (extra))
            )

        def _crear_checkbox(tab_frame, nombre, tags):
            v = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(tab_frame, text=tr(nombre), variable=v,
                                 font=ctk.CTkFont(size=10),
                                 onvalue=True, offvalue=False)
            cb.pack(anchor="w", padx=16, pady=1)
            check_vars[nombre] = (v, tags, cb)
            v.trace_add("write", lambda *a: _actualizar_lbl())

        # Crear todos los checkboxes UNA SOLA VEZ
        for cat_nombre, cat_items in categorias.items():
            tab = tabs.add(tr(cat_nombre))
            for nombre, tags in cat_items:
                _crear_checkbox(tab, nombre, tags)

        def _filtrar(e=None):
            """Filtra mostrando/ocultando con pack_forget/pack — NO destruye
            los checkboxes, así el estado marcado/desmarcado se conserva."""
            filtro = search_entry.get().lower().strip()
            for nombre, (v, tags, cb) in check_vars.items():
                if (not filtro or filtro in nombre.lower()
                        or filtro in tr(nombre).lower() or filtro in tags.lower()):
                    if not cb.winfo_ismapped():
                        cb.pack(anchor="w", padx=16, pady=1)
                else:
                    if cb.winfo_ismapped():
                        cb.pack_forget()

        search_entry.bind("<KeyRelease>", _filtrar)

        # Presets + guardar/guardados
        preset_row = ctk.CTkFrame(vent, fg_color="transparent")
        preset_row.pack(pady=(2, 0))

        def _marcar(nombres, exclusivo=False):
            if exclusivo:
                for tup in check_vars.values():
                    tup[0].set(False)
            for nombre in nombres:
                if nombre in check_vars:
                    check_vars[nombre][0].set(True)

        def _cargar_presets() -> list:
            """Lee los presets persistidos desde preferencias.json."""
            try:
                prefs = self.app.store.cargar_preferencias() or {}
                return list(prefs.get("negative_presets", []))
            except Exception as e:
                logger.debug(f"_cargar_presets: {e}")
                return []

        def _persistir_presets(presets: list) -> None:
            try:
                prefs = self.app.store.cargar_preferencias() or {}
                prefs["negative_presets"] = presets
                self.app.store.guardar_preferencias(prefs)
            except Exception as e:
                logger.warning(f"_persistir_presets falló: {e}")

        def _guardar_preset():
            activos = [nom for nom, tup in check_vars.items() if tup[0].get()]
            if not activos:
                return self.app.dialogs.set_estado(tr("⚠️ Marca elementos antes de guardar preset."), "#e67e22")
            # Pedir nombre al usuario
            from tkinter import simpledialog
            presets = _cargar_presets()
            sugerencia = f"Preset {len(presets) + 1}"
            nombre = simpledialog.askstring(tr("Guardar preset NEGATIVE"),
                                            tr("Nombre del preset:"),
                                            initialvalue=sugerencia,
                                            parent=vent)
            if not nombre:
                return
            nombre = nombre.strip()
            # Si ya existe ese nombre, preguntar si sobreescribir
            if any(p.get("nombre") == nombre for p in presets):
                from tkinter import messagebox as _mb
                if not _mb.askyesno(tr("Ya existe"),
                                    tr("Ya existe un preset llamado '{0}'. "
                                       "¿Sobrescribir?").format(nombre),
                                    parent=vent):
                    return
                presets = [p for p in presets if p.get("nombre") != nombre]
            presets.append({"nombre": nombre, "items": activos})
            _persistir_presets(presets)
            self.app.dialogs.set_estado(tr("💾 Preset '{0}' guardado ({1} items)").format((nombre), (len(activos))), "#2ecc71")
            _actualizar_lbl()

        def _mostrar_presets():
            presets = _cargar_presets()
            if not presets:
                self.app.dialogs.set_estado(tr("⚠️ No hay presets guardados todavía."), "#e67e22")
                return
            win = GPromptWindow(vent)
            win.title(tr("💾 Presets de NEGATIVE"))
            win.geometry("440x400")
            win.transient(vent)
            ctk.CTkLabel(win, text=tr("💾 Presets guardados"),
                         font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 4))
            scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
            scroll.pack(fill="both", expand=True, padx=15, pady=5)

            def _refrescar_presets():
                for w in scroll.winfo_children():
                    w.destroy()
                presets_act = _cargar_presets()
                if not presets_act:
                    ctk.CTkLabel(scroll, text=tr("(sin presets)")).pack(pady=20)
                    return
                for preset in presets_act:
                    row = ctk.CTkFrame(scroll, fg_color="#111820", corner_radius=6)
                    row.pack(fill="x", pady=3)
                    hdr = ctk.CTkFrame(row, fg_color="transparent")
                    hdr.pack(fill="x", padx=10, pady=(5, 0))
                    ctk.CTkLabel(hdr,
                                 text=tr('📁 {0} ({1} items)').format((preset['nombre']), (len(preset['items']))),
                                 font=ctk.CTkFont(size=11, weight="bold")
                                 ).pack(side="left")

                    def _aplicar(p=preset):
                        _marcar(p["items"])
                        win.destroy()
                        _actualizar_lbl()

                    def _borrar(p=preset):
                        from tkinter import messagebox as _mb
                        if not _mb.askyesno(tr("Confirmar"),
                                            tr("¿Borrar preset '{0}'?").format(p['nombre']),
                                            parent=win):
                            return
                        nuevos = [x for x in _cargar_presets()
                                  if x.get("nombre") != p["nombre"]]
                        _persistir_presets(nuevos)
                        _refrescar_presets()

                    ctk.CTkButton(hdr, text=tr("Aplicar"), width=70, height=22,
                                  fg_color="#1a7a3c",
                                  command=_aplicar).pack(side="right", padx=2)
                    ctk.CTkButton(hdr, text="🗑", width=32, height=22,
                                  fg_color="#7a1a1a", hover_color="#5a0f0f",
                                  command=_borrar).pack(side="right", padx=2)
                    ctk.CTkLabel(
                        row,
                        text=f"{', '.join(tr(i) for i in preset['items'][:8])}"
                             f"{'…' if len(preset['items']) > 8 else ''}",
                        font=ctk.CTkFont(size=9), text_color="#888888",
                        wraplength=380,
                    ).pack(anchor="w", padx=10, pady=(0, 5))
            _refrescar_presets()

        ctk.CTkButton(preset_row, text=tr("✓ Básicos"), width=85, height=24, fg_color="#1a4a5a",
                      command=lambda: _marcar(["Manos malas", "Baja calidad", "Texto / letras", "Marca de agua"])
                      ).pack(side="left", padx=2)
        ctk.CTkButton(preset_row, text=tr("👤 Retrato"), width=85, height=24, fg_color="#1a4a5a",
                      command=lambda: _marcar(["Manos malas", "Cara mal", "Ojos raros", "Boca / dientes",
                                                "Proporciones malas", "Piel plástica", "Baja calidad",
                                                "Texto / letras", "Marca de agua"])
                      ).pack(side="left", padx=2)
        ctk.CTkButton(preset_row, text=tr("🏆 Calidad"), width=100, height=24, fg_color="#1a4a5a",
                      command=lambda: _marcar(["Baja calidad", "Pixelado", "Ruido", "Desenfoque",
                                                "Tinte amarillo", "Texto / letras", "Marca de agua", "Logos / firmas"])
                      ).pack(side="left", padx=2)
        ctk.CTkButton(preset_row, text=tr("🧹 Limpiar"), width=75, height=24, fg_color="#5a3a1a",
                      command=lambda: [tup[0].set(False) for tup in check_vars.values()]
                      ).pack(side="left", padx=2)
        ctk.CTkButton(preset_row, text=tr("💾 Guardar"), width=90, height=24, fg_color="#4a1a6a",
                      command=_guardar_preset).pack(side="left", padx=2)
        ctk.CTkButton(preset_row, text=tr("📂 Presets"), width=80, height=24, fg_color="#1a4a5a",
                      command=_mostrar_presets).pack(side="left", padx=2)

        btn_row = ctk.CTkFrame(vent, fg_color="transparent")
        btn_row.pack(pady=6)

        def _tags_seleccionados() -> list[str]:
            return [tup[1] for tup in check_vars.values() if tup[0].get()]

        def _aplicar():
            tags_sel = _tags_seleccionados()
            if not tags_sel:
                return self.app.dialogs.set_estado(tr("⚠️ Marca al menos un elemento."), "#e67e22")
            negativo = ", ".join(tags_sel)
            pos = self.app.extraer_positive()
            if pos:
                self.app.dialogs.actualizar_salida(f"POSITIVE PROMPT: {pos}\nNEGATIVE PROMPT: {negativo}")
                self.app.dialogs.set_estado(tr('🧰 NEGATIVE construido ({0} items)').format(len(tags_sel)), "#2ecc71")
            else:
                pyperclip.copy(negativo)
                self.app.dialogs.set_estado(tr('🧰 NEGATIVE copiado ({0} items)').format(len(tags_sel)), "#2ecc71")
            vent.destroy()

        def _copiar():
            tags_sel = _tags_seleccionados()
            if not tags_sel:
                return self.app.dialogs.set_estado(tr("⚠️ Marca al menos un elemento."), "#e67e22")
            pyperclip.copy(", ".join(tags_sel))
            self.app.dialogs.set_estado(tr('📋 NEGATIVE copiado ({0} items)').format(len(tags_sel)), "#2ecc71")
            vent.destroy()

        ctk.CTkButton(btn_row, text=tr("✅ Aplicar al prompt"), width=170, height=30, fg_color="#1a7a3c",
                      command=_aplicar).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=tr("📋 Solo copiar"), width=130, height=30, fg_color="#475569",
                      command=_copiar).pack(side="left", padx=4)


    def _cmd_color_palette(self):
        """Extrae paleta de colores de la imagen cargada.

        v1.1: copia color individual, genera complementarios/analogos,
        guarda paleta, muestra valores RGB/HSL.
        """
        if not self.app.imagen_cargada:
            return self.app.dialogs.set_estado(tr("⚠️ Carga una imagen de referencia primero."), "#e67e22")

        self.app.dialogs.set_estado(tr("🎨 Extrayendo paleta de colores..."), "#f39c12")

        def _worker():
            try:


                img = self.app.imagen_cargada.copy()
                img.thumbnail((200, 200))
                img = img.convert("RGB")

                quantized = img.quantize(colors=8)
                palette_raw = quantized.getpalette()[:24]
                colores_raw = []
                for i in range(0, 24, 3):
                    r, g, b = palette_raw[i], palette_raw[i+1], palette_raw[i+2]
                    colores_raw.append((r, g, b))

                def rgb_to_hex(r, g, b):
                    return f"#{r:02X}{g:02X}{b:02X}"

                def rgb_to_hsl(r, g, b):
                    r, g, b = r/255.0, g/255.0, b/255.0
                    mx, mn = max(r, g, b), min(r, g, b)
                    l = (mx + mn) / 2
                    if mx == mn:
                        h = s = 0
                    else:
                        d = mx - mn
                        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
                        if mx == r: h = (g - b) / d + (6 if g < b else 0)
                        elif mx == g: h = (b - r) / d + 2
                        else: h = (r - g) / d + 4
                        h /= 6
                    return f"HSL({int(h*360)}, {int(s*100)}%, {int(l*100)}%)"

                def complementary(r, g, b):
                    return f"#{255-r:02X}{255-g:02X}{255-b:02X}"

                def analog_colors(r, g, b):
                    h = max(r, g, b) / 255.0
                    s = (max(r, g, b) - min(r, g, b)) / 255.0
                    adj = 30
                    results = []
                    for offset in [-2, -1, 1, 2]:
                        h2 = (h + offset * adj / 360) % 1.0
                        val = int(h2 * 255)
                        if offset == -2:
                            results.append(f"#{min(r+30,255):02X}{min(g+10,255):02X}{min(b+30,255):02X}")
                        elif offset == -1:
                            results.append(f"#{max(r-20,0):02X}{max(g-10,0):02X}{max(b-20,0):02X}")
                        elif offset == 1:
                            results.append(f"#{max(r-30,0):02X}{min(g+20,255):02X}{max(b-10,0):02X}")
                        else:
                            results.append(f"#{min(r+10,255):02X}{max(g-20,0):02X}{min(b+30,255):02X}")
                    return results

                def _mostrar():
                    vent = GPromptWindow(self.app)
                    vent.title(tr("🎨 Paleta de colores extraída"))
                    vent.geometry("580x600")
                    vent.transient(self.app)
                    ctk.CTkLabel(vent, text=tr("🎨 Paleta extraída de la imagen"),
                                 font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 4))
                    ctk.CTkLabel(vent, text=tr("Haz clic en un color para copiarlo. Añade al prompt para aplicar la paleta."),
                                 font=ctk.CTkFont(size=9), text_color="#888888").pack(pady=(0, 8))

                    # Colores principales
                    sw_frame = ctk.CTkFrame(vent, fg_color="transparent")
                    sw_frame.pack(pady=4)
                    hex_codes = []
                    for i, (r, g, b) in enumerate(colores_raw[:5]):
                        hex_c = rgb_to_hex(r, g, b)
                        hex_codes.append(hex_c)
                        col_f = ctk.CTkFrame(sw_frame, fg_color=hex_c, width=80, height=80, corner_radius=10,
                                              border_color="#3a3a4a", border_width=1)
                        col_f.pack(side="left", padx=5)
                        col_f.pack_propagate(False)

                        def _copy_color(h=hex_c):
                            pyperclip.copy(h)
                            self.app.dialogs.set_estado(tr('📋 {0} copiado').format(h), "#2ecc71")

                        def _on_enter(e, f, orig):
                            f.configure(border_color="#ffffff", border_width=2)

                        def _on_leave(e, f, orig):
                            f.configure(border_color="#3a3a4a", border_width=1)

                        col_f.bind("<Button-1>", lambda e, h=hex_c: _copy_color(h))
                        col_f.bind("<Enter>", lambda e, f=col_f, o=hex_c: _on_enter(e, f, o))
                        col_f.bind("<Leave>", lambda e, f=col_f, o=hex_c: _on_leave(e, f, o))

                        lbl = ctk.CTkLabel(col_f, text=hex_c, font=ctk.CTkFont(size=7),
                                            text_color="white" if (r+g+b)/3 < 128 else "black",
                                            fg_color="transparent")
                        lbl.place(relx=0.5, rely=1.0, anchor="s", y=-2)

                    # Tabla de valores
                    val_frame = ctk.CTkFrame(vent, fg_color="#111820", corner_radius=8)
                    val_frame.pack(fill="x", padx=15, pady=4)
                    ctk.CTkLabel(val_frame, text=tr("Valores detallados"), font=ctk.CTkFont(size=11, weight="bold")
                                 ).pack(anchor="w", padx=10, pady=(6, 2))
                    for i, (r, g, b) in enumerate(colores_raw[:5]):
                        hex_c = rgb_to_hex(r, g, b)
                        row = ctk.CTkFrame(val_frame, fg_color="transparent")
                        row.pack(fill="x", padx=10, pady=1)
                        sw_small = ctk.CTkFrame(row, fg_color=hex_c, width=24, height=24, corner_radius=4)
                        sw_small.pack(side="left", padx=(0, 6))
                        sw_small.pack_propagate(False)
                        ctk.CTkLabel(row, text=f"#{i+1}", font=ctk.CTkFont(size=9, weight="bold"),
                                     width=30).pack(side="left")
                        ctk.CTkLabel(row, text=hex_c, font=ctk.CTkFont(family="Consolas", size=10),
                                     text_color="#aaccee").pack(side="left", padx=(0, 4))

                        def _cp(h):
                            return lambda: pyperclip.copy(h)
                        ctk.CTkButton(row, text=hex_c, width=90, height=20, fg_color="#1a4a5a",
                                      font=ctk.CTkFont(size=9), command=_cp(hex_c)).pack(side="left", padx=1)
                        ctk.CTkLabel(row, text=tr('RGB({0},{1},{2})').format((r), (g), (b)), font=ctk.CTkFont(size=9),
                                     text_color="#888888").pack(side="left", padx=(4, 0))
                        ctk.CTkLabel(row, text=rgb_to_hsl(r, g, b), font=ctk.CTkFont(size=8),
                                     text_color="#666666").pack(side="left", padx=(4, 0))
                        comp = complementary(r, g, b)
                        ctk.CTkLabel(row, text=tr('Comp: {0}').format(comp), font=ctk.CTkFont(size=8),
                                     text_color="#f59e0b").pack(side="left", padx=(4, 0))

                    # Complementarios del primer color
                    r0, g0, b0 = colores_raw[0]
                    analogo = analog_colors(r0, g0, b0)
                    comp_frame = ctk.CTkFrame(vent, fg_color="#111820", corner_radius=8)
                    comp_frame.pack(fill="x", padx=15, pady=4)
                    ctk.CTkLabel(comp_frame, text=tr("Colores complementarios y análogos"),
                                 font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(6, 2))
                    analogs_row = ctk.CTkFrame(comp_frame, fg_color="transparent")
                    analogs_row.pack(padx=10, pady=(0, 6))
                    comp_c = complementary(r0, g0, b0)
                    for lab, col in [("Complementario", comp_c)] + list(zip(["A-1", "A-2", "A+1", "A+2"], analogo)):
                        f2 = ctk.CTkFrame(analogs_row, fg_color=col, width=50, height=40, corner_radius=6)
                        f2.pack(side="left", padx=3)
                        f2.pack_propagate(False)
                        ctk.CTkLabel(f2, text=lab, font=ctk.CTkFont(size=8),
                                     text_color="white" if sum(int(col[i*2+1:i*2+3], 16) for i in range(3))/3 < 128 else "black",
                                     fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")
                        f2.bind("<Button-1>", lambda e, h=col: (pyperclip.copy(h), self.app.dialogs.set_estado(tr('📋 {0} copiado').format(h), "#2ecc71")))

                    btn_row = ctk.CTkFrame(vent, fg_color="transparent")
                    btn_row.pack(pady=10)
                    hex_str = ", ".join(hex_codes)

                    def _guardar_paleta():
                        # Pedir nombre al usuario en vez de auto-numerar
                        from tkinter import simpledialog
                        nombre = simpledialog.askstring(
                            tr("Guardar paleta"),
                            tr("Nombre de la paleta:"),
                            initialvalue=tr("Paleta {0}").format(len(self.app.store.paletas or []) + 1),
                            parent=vent,
                        )
                        if not nombre:
                            return
                        paleta = {
                            "nombre": nombre.strip(),
                            "hex": hex_codes,
                            "rgb": [list(c) for c in colores_raw[:5]],
                            "timestamp": str(datetime.datetime.now())[:19],
                        }
                        self.app.store.paletas.append(paleta)
                        self.app.store._guardar("paletas")  # FIX: era store.guardar() inexistente
                        self.app.dialogs.set_estado(tr("💾 Paleta '{0}' guardada").format(paleta['nombre']), "#2ecc71")

                    ctk.CTkButton(btn_row, text=tr("📋 Copiar HEX"), width=120, height=28,
                                  command=lambda: pyperclip.copy(hex_str)).pack(side="left", padx=4)
                    ctk.CTkButton(btn_row, text=tr("🎨 Añadir al prompt"), width=140, height=28, fg_color="#1a7a3c",
                                  command=lambda: (self.app._aplicar_atajo_tags(f"color palette: {hex_str}"),
                                                    vent.destroy())).pack(side="left", padx=4)
                    ctk.CTkButton(btn_row, text=tr("💾 Guardar paleta"), width=130, height=28, fg_color="#4a1a6a",
                                  command=_guardar_paleta).pack(side="left", padx=4)
                    ctk.CTkButton(btn_row, text=tr("📚 Biblioteca"), width=110, height=28, fg_color="#1a4a5a",
                                  command=lambda: self._abrir_biblioteca_paletas(vent)).pack(side="left", padx=4)

                    self.app.dialogs.set_estado(tr("🎨 Paleta extraída"), "#2ecc71")
                self.app.after(0, _mostrar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _abrir_biblioteca_paletas(self, parent_window=None):
        """Biblioteca de paletas guardadas con búsqueda, aplicar y borrar."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        bg_card = "#ffffff" if is_lt else "#1a1a2e"
        text_main = "#111827" if is_lt else "#e5e7eb"
        text_muted = "#4b5563" if is_lt else "#9ca3af"

        win = GPromptWindow(parent_window or self.app)
        win.title(tr("📚 Biblioteca de paletas"))
        win.geometry("560x600")
        win.transient(parent_window or self.app)

        ctk.CTkLabel(win, text=tr("📚 Biblioteca de paletas"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4))

        # Cabecera con contador
        cont_var = ctk.StringVar(value="")
        ctk.CTkLabel(win, textvariable=cont_var, font=ctk.CTkFont(size=10),
                     text_color=text_muted).pack(pady=(0, 6))

        scroll = ctk.CTkScrollableFrame(win,
                                        fg_color=("#f3f4f6" if is_lt else "#0d1117"))
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        def _refrescar():
            for w in scroll.winfo_children():
                w.destroy()
            paletas = self.app.store.paletas or []
            cont_var.set(f"{len(paletas)} paletas guardadas")
            if not paletas:
                ctk.CTkLabel(scroll, text=tr("No hay paletas guardadas todavía.\n"
                             "Extrae una imagen y pulsa '💾 Guardar paleta'."),
                             text_color=text_muted, justify="center"
                             ).pack(pady=30)
                return

            for idx, p in enumerate(paletas):
                card = ctk.CTkFrame(scroll, fg_color=bg_card, corner_radius=8)
                card.pack(fill="x", padx=4, pady=4)

                # Cabecera con nombre + timestamp + botones
                hdr = ctk.CTkFrame(card, fg_color="transparent")
                hdr.pack(fill="x", padx=12, pady=(8, 4))
                ctk.CTkLabel(hdr, text=p.get("nombre", f"Paleta {idx+1}"),
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=text_main).pack(side="left")
                if p.get("timestamp"):
                    ctk.CTkLabel(hdr, text=p["timestamp"][:10],
                                 font=ctk.CTkFont(size=9),
                                 text_color=text_muted).pack(side="left", padx=10)

                def _aplicar(pal=p):
                    hex_str = ", ".join(pal.get("hex", []))
                    self.app._aplicar_atajo_tags(f"color palette: {hex_str}")
                    self.app.dialogs.set_estado(tr("🎨 Paleta '{0}' añadida al prompt").format(pal.get('nombre','')),
                                    "#2ecc71")

                def _copiar(pal=p):
                    pyperclip.copy(", ".join(pal.get("hex", [])))
                    self.app.dialogs.set_estado(tr("📋 Hex de '{0}' copiados").format(pal.get('nombre','')),
                                    "#2ecc71")

                def _borrar(i=idx, nombre=p.get("nombre", "?")):
                    from tkinter import messagebox as _mb
                    if not _mb.askyesno(tr("Confirmar"),
                                        tr("¿Borrar paleta '{0}'?").format(nombre),
                                        parent=win):
                        return
                    try:
                        self.app.store.paletas.pop(i)
                        self.app.store._guardar("paletas")
                        _refrescar()
                    except Exception as e:
                        logger.warning(f"Borrar paleta: {e}")

                ctk.CTkButton(hdr, text=tr("🎨 Aplicar"), width=80, height=24,
                              fg_color="#1a7a3c",
                              command=_aplicar).pack(side="right", padx=2)
                ctk.CTkButton(hdr, text="📋", width=32, height=24,
                              command=_copiar).pack(side="right", padx=2)
                ctk.CTkButton(hdr, text="🗑", width=32, height=24,
                              fg_color="#7a1a1a", hover_color="#5a0f0f",
                              command=_borrar).pack(side="right", padx=2)

                # Swatches de colores
                sw_row = ctk.CTkFrame(card, fg_color="transparent")
                sw_row.pack(fill="x", padx=12, pady=(0, 10))
                for hex_c in p.get("hex", []):
                    f = ctk.CTkFrame(sw_row, fg_color=hex_c, width=58, height=40,
                                     corner_radius=6)
                    f.pack(side="left", padx=3)
                    f.pack_propagate(False)
                    # Color del label legible según oscuridad del swatch
                    try:
                        r, g, b = int(hex_c[1:3], 16), int(hex_c[3:5], 16), int(hex_c[5:7], 16)
                        text_c = "white" if (r+g+b)/3 < 128 else "black"
                    except Exception:
                        text_c = "white"
                    ctk.CTkLabel(f, text=hex_c, font=ctk.CTkFont(size=8),
                                 text_color=text_c, fg_color="transparent"
                                 ).place(relx=0.5, rely=0.5, anchor="center")
                    # Click para copiar el color individual
                    def _cp_color(h=hex_c):
                        pyperclip.copy(h)
                        self.app.dialogs.set_estado(tr('📋 {0} copiado').format(h), "#2ecc71")
                    f.bind("<Button-1>", lambda _e, h=hex_c: _cp_color(h))

        _refrescar()

        ctk.CTkButton(win, text=tr("Cerrar"), width=100, height=30,
                      fg_color="#444", hover_color="#555",
                      command=win.destroy).pack(pady=8)
