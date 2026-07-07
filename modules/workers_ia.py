"""Workers IA — threads de generación, visión, traducción.

Métodos:
  • _worker_ia                 — worker principal: deepseek.generar +
                                 historial + apertura de comparador
                                 (variaciones) o diff (refinamiento).
  • _worker_vision             — visión: describir imagen.
  • _worker_prompt_traduccion  — traducción ES→EN del prompt.
  • _worker_prompt_quick       — quick generate (modelo más barato).
  • _worker_imagen_a_prompt    — imagen→prompt completo (visión + LLM).

Todos se lanzan vía threading.Thread(target=..., daemon=True).start()
desde sus comandos respectivos en CoreMixin / ToolsAnalysisMixin.

Dependencias self (provistas por ArquitectoApp):
  deepseek, vision, after, set_estado, toggle_botones,
  actualizar_salida, guardar_en_historial, _sonar_completado,
  _detener_progreso, _iniciar_progreso, _parsear_variaciones,
  _mostrar_variaciones, _mostrar_diff_refinamiento, llm_var,
  modo_var, get_current_model_specs, _es_comfyui_turbo,
  _recortar_si_excede, _ocultar_ideas, _mostrar_ideas, txt_idea,
  imagen_cargada, _ultimo_anclaje_visual, _on_modo_cambio,
  is_natural_mode, _construir_peticion, _inyectar_specs_*.
"""
import logging
import re

from modules import paleta as P
from modules.i18n import tr
from modules.prompt_helpers import mover_trigger_al_inicio
from workers import limpiar_marcadores, parsear_ideas

logger = logging.getLogger("gprompt")


class WorkersIaService:
    """5 workers IA que se lanzan en threads.

    A1 fase 2 (sesión 14): servicio aislado con app por composición.
    Acceso: `app.workers.worker_*` (vía WorkersIaComponent).
    """

    def __init__(self, app):
        self.app = app

    def _garantizar_lora_trigger(self, texto, es_ideas=False):
        """Post-procesado: garantiza que el trigger del LoRA aparece UNA
        SOLA VEZ en el output, en su posición correcta.

        Algunos modelos con system prompt estricto (Z-Image-Base, modelos
        natural con plantillas fijas) o bien ignoran la instrucción y NO
        ponen el trigger, o bien la cumplen demasiado y lo ponen en
        MÚLTIPLES sitios (preámbulo + bloque dedicado).

        Lógica:
          1. Si hay bloque `[LoRA Activation & Style]` Y el trigger ya
             está allí → eliminar TODAS las demás apariciones fuera del
             bloque (limpieza de duplicados).
          2. Si hay bloque pero el trigger no está allí → insertarlo allí
             (y limpiar duplicados fuera).
          3. Si NO hay bloque y el trigger ya aparece → no tocar.
          4. Si NO hay bloque y el trigger no aparece → fallback:
             insertar tras "POSITIVE PROMPT:" como tag suelto.

        No se aplica a ideas (son sugerencias creativas, no prompts).
        """
        if es_ideas or not texto:
            return texto
        # Multi-LoRA: garantizar TODOS los triggers activos (primario + extras
        # del modal), no solo el primario — si el LLM se deja alguno, el
        # safety-net lo recupera. triggers_loras_activos() los da sin duplicar.
        try:
            triggers = self.app.footer.triggers_loras_activos() or []
        except Exception:
            triggers = []
        for trigger in triggers:
            if trigger and trigger.strip():
                texto = self._garantizar_un_trigger(texto, trigger.strip())
        return texto

    def _garantizar_un_trigger(self, texto, trigger):
        """Garantiza que UN trigger concreto aparece una sola vez en su sitio
        (bloque [LoRA Activation & Style] si existe, o tras POSITIVE PROMPT)."""
        # Para triggers multi-término (ej: "Nyra, Amber Eyes, Undercut"), el
        # safety-net usa solo el primer término como clave de búsqueda, ya que
        # la regex de palabra-completa no funciona con cadenas que incluyen comas.
        trigger_key = trigger.split(",")[0].strip()

        m_bloque = re.search(
            r"\[LoRA Activation & Style\]\s*",
            texto, re.IGNORECASE,
        )

        # CON bloque dedicado: garantizar que está dentro Y solo dentro.
        if m_bloque:
            bloque_inicio = m_bloque.end()
            # Buscar el final del bloque (siguiente [Xxx] o NEGATIVE PROMPT)
            m_next = re.search(
                r"\n\s*(\[[A-Z][^\]]*\]|NEGATIVE\s+PROMPT\s*:)",
                texto[bloque_inicio:],
            )
            bloque_fin = bloque_inicio + (m_next.start()
                                          if m_next else len(texto) - bloque_inicio)
            bloque_contenido = texto[bloque_inicio:bloque_fin]
            ya_en_bloque = trigger_key.lower() in bloque_contenido.lower()

            # 1. Asegurar el trigger DENTRO del bloque
            if not ya_en_bloque:
                insert_str = f"{trigger}, " if "," in trigger else f"{trigger} style, "
                texto = (texto[:bloque_inicio] + insert_str
                         + texto[bloque_inicio:].lstrip())
                bloque_fin += len(insert_str)

            # 2. Eliminar TODAS las apariciones del trigger_key FUERA del bloque.
            antes = texto[:bloque_inicio]
            despues = texto[bloque_fin:]
            patron = re.compile(
                rf"(?:,\s*)?\b{re.escape(trigger_key)}\b(?:\s*,)?",
                re.IGNORECASE,
            )
            antes_limpio = patron.sub("", antes)
            despues_limpio = patron.sub("", despues)
            # Re-componer
            texto = (antes_limpio
                     + texto[bloque_inicio:bloque_fin]
                     + despues_limpio)
            # Limpiar comas dobles que pudieran quedar tras la eliminación
            texto = re.sub(r",\s*,", ",", texto)
            texto = re.sub(r"^\s*,\s*", "", texto, flags=re.MULTILINE)
            # Limpiar espacios sobrantes al inicio de cada línea (típico
            # tras quitar "trigger, " al principio del preámbulo).
            texto = re.sub(r"^[ \t]+", "", texto, flags=re.MULTILINE)
            return texto

        # SIN bloque dedicado: comportamiento clásico (solo inserción).
        if trigger.lower() in texto.lower():
            return texto
        m = re.search(r"(POSITIVE\s+PROMPT\s*:|^PROMPT\s*:)", texto,
                      re.IGNORECASE | re.MULTILINE)
        if m:
            insert_pos = m.end()
            return texto[:insert_pos] + f" {trigger}, " + texto[insert_pos:].lstrip()
        return f"POSITIVE PROMPT: {trigger}, {texto.lstrip()}"

    def _mover_lora_al_inicio_si_pref(self, texto, es_ideas=False):
        """Si la pref 'LoRA al inicio' está activa, mueve los triggers de
        TODOS los LoRAs activos (primario + extras del multi-LoRA) al
        principio del POSITIVE (convención SeaArt). No aplica a ideas ni si
        no hay LoRA/trigger."""
        if es_ideas or not texto:
            return texto
        try:
            if not (hasattr(self.app, "lora_inicio_var")
                    and self.app.lora_inicio_var.get()):
                return texto
            triggers = self.app.footer.triggers_loras_activos() or []
        except Exception:
            return texto
        # mover_trigger_al_inicio inserta cada trigger justo tras la etiqueta
        # POSITIVE, así que iteramos en ORDEN INVERSO para que el orden final
        # sea el de triggers_loras_activos (primario primero, luego extras).
        for trigger in reversed(triggers):
            if trigger and trigger.strip():
                texto = mover_trigger_al_inicio(texto, trigger.strip())
        return texto

    def _worker_ia(self, peticion, es_ideas=False, es_variaciones=False, n_variaciones=None,
                   es_refinamiento=False, texto_previo=None):
        try:
            self.app.after(0, self.app.dialogs._iniciar_progreso)
            specs = self.app.get_current_model_specs()
            max_c = specs.get("max_chars") or specs.get("max_chars_letra") or 0 if specs else 0
            max_c_neg = specs.get("max_chars_negative") if specs else None
            max_tok = 2500 if max_c >= 4000 else 2000 if max_c >= 2000 else 1800

            cerebro_elegido = self.app.llm_var.get()
            texto = self.app.deepseek.generar(peticion, max_tokens=max_tok)
            texto = limpiar_marcadores(texto)  # Eliminar ** y __ del resultado
            # Safety-net: garantizar trigger del LoRA en el output
            texto = self._garantizar_lora_trigger(texto, es_ideas=es_ideas)
            # Opcional (pref "LoRA al inicio"): mover el trigger al principio
            # del POSITIVE (convención SeaArt: los LoRAs van primero).
            texto = self._mover_lora_al_inicio_si_pref(texto, es_ideas=es_ideas)

            # CORTADOR DE SEGURIDAD: si el prompt excede el límite del modelo, lo recorta
            if max_c and not es_ideas and not es_variaciones:
                texto_original_len = len(texto)
                texto = self.app._recortar_si_excede(texto, max_c, max_chars_negative=max_c_neg)
                if len(texto) < texto_original_len:
                    self.app.after(0, lambda: self.app.dialogs.set_estado(tr('✂️ Prompt recortado a {0} chars (máximo del modelo)').format(max_c), P.TXT_ACENTO))

            # ELIMINAR NEGATIVE si el modelo no lo soporta (Nano Banana, Gemini, Turbo en ComfyUI)
            es_comfyui_turbo = False
            if self.app.modo_var.get() == "imagen":
                es_comfyui_turbo = self.app._es_comfyui_turbo()
            quitar_negative = (specs and not specs.get("has_negative", True)) or es_comfyui_turbo
            if quitar_negative and not es_ideas:
                if re.search(r'NEGATIVE\s+PROMPT', texto, re.IGNORECASE):
                    texto = re.sub(r'\n?\s*NEGATIVE\s+PROMPT\s*:.*?(?=\n\s*(?:POSITIVE|─|$)|\Z)', '', texto, flags=re.DOTALL | re.IGNORECASE)
                    texto = texto.strip()
                    razon = "ComfyUI + Turbo" if es_comfyui_turbo else "este modelo"
                    self.app.after(0, lambda r=razon: self.app.dialogs.set_estado(tr('⚠️ NEGATIVE eliminado ({0} no lo soporta)').format(r), P.TXT_ACENTO))

            # ELIMINAR PESOS NUMÉRICOS solo en ComfyUI con modelos Turbo
            if es_comfyui_turbo and not es_ideas:
                if re.search(r'\([^)]+:[0-9.]+\)', texto):
                    # (word:1.2) → word   |   (word word:0.8) → word word
                    texto = re.sub(r'\(([^()]+?):\s*[0-9.]+\s*\)', r'\1', texto)
                    self.app.after(0, lambda: self.app.dialogs.set_estado(tr('⚠️ Pesos numéricos eliminados (ComfyUI + Turbo)'), P.TXT_ACENTO))

            # guardar_en_historial lee variables Tk (modo_var, combos, footer)
            # → SIEMPRE en el hilo principal vía after (leerlas desde el
            # worker arriesga "main thread is not in main loop" al cerrar).
            self.app.after(0, lambda t=texto: self.app.guardar_en_historial(t))
            # No sobrescribir el resultado con el texto crudo de las
            # variaciones — esas se muestran en un modal con cards.
            # En refinamiento, abrimos el modal de diff con
            # Aplicar/Cancelar en vez de sobrescribir txt_salida directamente.
            if es_refinamiento:
                self.app.after(0, lambda: self.app.refinar.mostrar_diff_refinamiento(texto_previo or "", texto))
            elif not es_ideas and not es_variaciones:
                self.app.after(0, lambda: self.app.dialogs.actualizar_salida(texto))
            estado_msg = (tr("🔍 Refinamiento listo — revisa el diff ({0}).").format(cerebro_elegido)
                          if es_refinamiento
                          else tr("✅ Completado ({0}).").format(cerebro_elegido))
            self.app.after(0, lambda m=estado_msg: self.app.dialogs.set_estado(m, P.TXT_OK))
            self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))
            self.app.after(0, self.app.dialogs._sonar_completado)
            self.app.after(0, self.app.dialogs._detener_progreso)
            if es_ideas:
                ideas = parsear_ideas(texto)
                # Fallback: si el LLM no usó formato "1. 2. 3.", dividir por bloques
                if not ideas:
                    bloques = [b.strip() for b in texto.split("\n\n") if len(b.strip()) > 30]
                    if bloques:
                        ideas = bloques[:3]
                self.app.after(0, lambda ideas=ideas: self.app._mostrar_ideas(ideas))
            elif es_variaciones: self.app.after(0, lambda: self.app._mostrar_variaciones(self.app._parsear_variaciones(texto, n_esperado=n_variaciones)))
        except Exception as e:
            self.app.after(0, lambda e=e: self.app.dialogs.actualizar_salida(f"❌ Error {self.app.llm_var.get()}: {e}"))
            self.app.after(0, lambda: self.app.dialogs.set_estado(tr("Error de conexión."), P.TXT_ERROR))
            self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))
            self.app.after(0, self.app.dialogs._detener_progreso)

    def _worker_vision(self):
        try:
            self.app.after(0, lambda: self.app.dialogs.set_estado(tr("👁 Analizando imagen..."), P.TXT_ACENTO))
            def on_status(msg): self.app.after(0, lambda: self.app.dialogs.set_estado(msg, P.TXT_ACENTO))
            desc, motor = self.app.vision.describir(self.app.imagen_cargada, self.app.modo_var.get(), on_status)

            def _mostrar_resultado():
                idea_previa = self.app.txt_idea.get("1.0", "end").strip()
                self.app.txt_idea.delete("1.0", "end")
                self.app.txt_idea.insert("1.0", f"{desc}\n\n{idea_previa}" if idea_previa else desc)
                self.app.dialogs.actualizar_salida(tr("👁 [{0}] analizó la imagen...\nRevisa y pulsa Generar Prompt.").format(motor))
                self.app.dialogs.set_estado(tr('👁 [{0}] — Edita la descripción y pulsa Generar Prompt').format(motor), P.TXT_OK)
                self.app.dialogs.toggle_botones(True)
                self.app.txt_idea.focus_set()
            self.app.after(0, _mostrar_resultado)
        except Exception as e:
            self.app.after(0, lambda: self.app.dialogs.set_estado(tr("❌ Error visión."), P.TXT_ERROR))
            self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

    def _worker_prompt_traduccion(self, idea_original):
        idea = idea_original
        if self.app.switch_traduccion_var.get() and self.app.footer.detectar_idioma(idea_original):
            self.app.after(0, lambda: self.app.dialogs.set_estado(tr("🌐 Traduciendo al inglés..."), P.TXT_ACENTO))
            idea = self.app.deepseek.traducir(idea_original)
            self.app.after(0, lambda: self.app.dialogs.set_estado(tr("🌐 Traducido..."), P.TXT_INFO))
        self._worker_ia(self.app._construir_peticion(idea, "B"))
    # ──────────────────────────────────────────────────────────────
    def _worker_prompt_quick(self, idea):
        """Worker para Quick Generate. Versión simplificada de _worker_prompt_traduccion."""
        try:
            modo = self.app.modo_var.get()
            specs = self.app.get_current_model_specs()
            limite_chars = specs.get("max_chars", 2000) if specs else 2000
            has_neg = specs.get("has_negative", True) if specs else True
            is_natural = self.app.is_natural_mode()

            # Construir petición reducida
            formato = ("FORMATO: lenguaje natural descriptivo." if is_natural
                       else "FORMATO: tags separados por comas con pesos (tag:1.2). NO prosa fluida.")
            neg_rule = ("Genera POSITIVE y NEGATIVE." if has_neg
                        else "Solo POSITIVE (este modelo no usa NEGATIVE).")

            # Personaje y LoRA si aplican
            extras = ""
            try:
                pers_nombre = self.app.combo_personaje.get() if hasattr(self.app, 'combo_personaje') else ""
                if pers_nombre and pers_nombre != tr("— Sin personaje —"):
                    desc = self.app.store.descripcion_personaje(pers_nombre)
                    if desc:
                        extras += f"\nPERSONAJE: {desc}"
                lora_nombre = self.app.combo_lora.get() if hasattr(self.app, 'combo_lora') else ""
                if lora_nombre and lora_nombre != tr("— Sin LoRA —"):
                    trigger = self.app.store.trigger_lora(lora_nombre)
                    if trigger:
                        extras += f"\nLORA TRIGGER (incluir literal): {trigger}"
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            ratio = self.app.ratio_var.get() if hasattr(self.app, 'ratio_var') else ""
            ratio_str = f"\nRATIO: {ratio}" if ratio else ""

            peticion = (
                f"⚡ QUICK MODE: prompt rápido y directo para {modo}.\n"
                f"IDEA: {idea}\n"
                f"ESTILOS: {self.app.footer.estilos_texto()}{ratio_str}{extras}\n"
                f"{formato}\n"
                f"{neg_rule}\n"
                f"⛔ Máx {limite_chars} caracteres. Sé conciso, no añadas explicaciones."
            )
            # Contexto de LoRAs/personaje activos (sesión 16)
            try:
                peticion += self.app._contexto_loras_personaje("el prompt")
            except Exception as _e:
                logger.debug(f"[silent ctx loras] {_e}")

            # Inyección mínima del modelo (sin construir_modelo_info completo)
            modelo_actual = ""
            try:
                if modo == "imagen" and hasattr(self.app, 'combo_modelo_imagen'):
                    modelo_actual = self.app.combo_modelo_imagen.get()
                elif modo == "video" and hasattr(self.app, 'combo_modelo_video'):
                    modelo_actual = self.app.combo_modelo_video.get()
                elif modo == "audio" and hasattr(self.app, 'combo_modelo_audio'):
                    modelo_actual = self.app.combo_modelo_audio.get()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            if modelo_actual:
                peticion += f"\nMODELO: {modelo_actual}"

            # Generación rápida
            texto = self.app.deepseek.generar(peticion, temperature=0.4, max_tokens=1200)
            texto = limpiar_marcadores(texto)
            # Safety-net: garantizar trigger del LoRA en el output
            texto = self._garantizar_lora_trigger(texto)
            texto = self._mover_lora_al_inicio_si_pref(texto)

            # Limpiar NEGATIVE si el modelo no lo soporta
            if not has_neg:
                texto = re.sub(r'\n?\s*NEGATIVE\s+PROMPT\s*:.*?$', '', texto,
                                flags=re.DOTALL | re.IGNORECASE).strip()

            # guardar_en_historial lee variables Tk (modo_var, combos, footer)
            # → SIEMPRE en el hilo principal vía after (leerlas desde el
            # worker arriesga "main thread is not in main loop" al cerrar).
            self.app.after(0, lambda t=texto: self.app.guardar_en_historial(t))

            def _aplicar():
                self.app.dialogs.actualizar_salida(texto)
                self.app.dialogs.set_estado(tr("⚡ Quick listo"), P.TXT_OK)
                self.app.dialogs.toggle_botones(True)
                try: self.app.dialogs._sonar_completado()
                except Exception as e:
                    logger.debug(f"[silent] {e}")
            self.app.after(0, _aplicar)
        except Exception as e:
            self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error Quick: {0}').format(e), P.TXT_ERROR))
            self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

    # ──────────────────────────────────────────────────────────────
    def _worker_imagen_a_prompt(self):
        try:
            # ¿Tratar imagen como referencia visual (storyboard/moodboard)?
            es_referencia = bool(self.app.switch_ref_visual_var.get())
            modo_etiqueta = "🖼 REFERENCIA" if es_referencia else "👁 FIEL"

            self.app.after(0, lambda: self.app.dialogs.set_estado(tr('{0} Analizando imagen...').format(modo_etiqueta), P.TXT_ACENTO))
            def on_status(msg): self.app.after(0, lambda: self.app.dialogs.set_estado(msg, P.TXT_ACENTO))
            desc, motor = self.app.vision.describir(self.app.imagen_cargada, self.app.modo_var.get(), on_status)
            self.app._ultimo_anclaje_visual = desc
            idea_manual = self.app.txt_idea.get("1.0", "end").strip()
            prompt_existente = self.app.txt_salida.get("1.0", "end").strip()

            # Detectar si hay un prompt existente para mejorar
            tiene_prompt = prompt_existente and ("PROMPT:" in limpiar_marcadores(prompt_existente) or len(prompt_existente) > 100)

            def _poner_desc():
                self.app.txt_idea.delete("1.0", "end")
                self.app.txt_idea.insert("1.0", f"{desc}\n\nAdiciones del usuario: {idea_manual}" if idea_manual else desc)
                if es_referencia:
                    self.app.dialogs.set_estado(tr('🖼 [{0}] → generando prompt con guía visual (estilo/paleta/personajes)...').format(motor), P.BTN_ACENTO)
                elif tiene_prompt:
                    self.app.dialogs.set_estado(tr('👁 [{0}] → mejorando prompt existente con análisis visual...').format(motor), P.TXT_ACENTO)
                else:
                    self.app.dialogs.set_estado(tr('👁 [{0}] → generando prompt con contexto visual anclado...').format(motor), P.TXT_ACENTO)
            self.app.after(0, _poner_desc)

            idea_final = desc if not idea_manual else f"{desc}\n\nAdiciones: {idea_manual}"
            if self.app.switch_traduccion_var.get() and self.app.footer.detectar_idioma(idea_final):
                idea_final = self.app.deepseek.traducir(idea_final)

            specs = self.app.get_current_model_specs()
            limite_chars = specs.get("max_chars") if specs else 2000
            es_tag_based = not self.app.is_natural_mode()

            if es_referencia:
                # MODO REFERENCIA: la imagen es una guía visual (storyboard/
                # moodboard/style guide), NO contenido literal. Extraer solo
                # paleta/iluminación/personajes/estilo, y generar prompt
                # original con esa guía visual.
                formato = " FORMATO OBLIGATORIO: tags separados por comas con pesos (tag:1.2). NO prosa fluida." if es_tag_based else ""
                regla_longitud = f" ⛔ REGLA ESTRICTA: El prompt FINAL no debe superar los {limite_chars} caracteres en total."
                idea_del_usuario = idea_manual if idea_manual else "(usa la propia descripción de la imagen como base, pero generando una escena original)"
                peticion = (
                    f"La imagen subida es una REFERENCIA VISUAL (probablemente un storyboard, "
                    f"moodboard, page de cómic o style guide). NO la describas literalmente.\n\n"
                    f"ANÁLISIS de la imagen (solo para extraer guía visual):\n{idea_final}\n\n"
                    f"INSTRUCCIONES:\n"
                    f"1. De la imagen, EXTRAE únicamente estos elementos como guía:\n"
                    f"   - Paleta de colores dominante\n"
                    f"   - Estilo de iluminación (hora del día, dirección, contraste)\n"
                    f"   - Apariencia de los personajes (vestuario, rasgos, época)\n"
                    f"   - Estilo gráfico/medio (pencil sketch, comic, pintura, foto)\n"
                    f"   - Atmósfera / mood emocional\n"
                    f"2. IGNORA: composición de paneles, layout de grid, viñetas, "
                    f"distribución espacial — esos detalles NO deben aparecer en el prompt.\n"
                    f"3. GENERA un prompt para esta escena/idea: '{idea_del_usuario}'.\n"
                    f"4. El prompt debe representar UNA SOLA imagen (no un storyboard ni "
                    f"un grid), pero mantener la paleta/iluminación/personajes/estilo "
                    f"identificados en el paso 1.\n"
                    f"Estilos extra del usuario: {self.app.footer.estilos_texto()}.{formato}{regla_longitud}"
                ) + self.app.prompts.construir_modelo_info()
            elif tiene_prompt:
                # MODO MEJORAR: analizar imagen + corregir prompt existente
                formato = "FORMATO: tags separados por comas con pesos (tag:1.2). NO prosa fluida." if es_tag_based else ""
                peticion = (
                    f"Eres un corrector visual de prompts. Tienes DOS entradas:\n\n"
                    f"1. ANÁLISIS VISUAL de la imagen de referencia:\n{idea_final}\n\n"
                    f"2. PROMPT EXISTENTE del usuario:\n{prompt_existente}\n\n"
                    f"Tu tarea: MEJORA el prompt existente comparándolo con lo que realmente se ve en la imagen. "
                    f"Corrige detalles incorrectos, añade elementos que falten, ajusta iluminación/colores/composición "
                    f"para que el prompt reproduzca FIELMENTE lo que se ve en la imagen. "
                    f"MANTÉN la estructura y estilo del prompt original. {formato}\n"
                    f"⛔ Límite: {limite_chars} caracteres.\n"
                    f"Estilos: {self.app.footer.estilos_texto()}." + self.app.prompts.construir_modelo_info()
                )
            else:
                # MODO GENERAR: crear prompt nuevo desde imagen
                formato = " FORMATO OBLIGATORIO: tags separados por comas con pesos (tag:1.2). NO prosa fluida." if es_tag_based else ""
                regla_longitud = f" ⛔ REGLA ESTRICTA: El prompt FINAL no debe superar los {limite_chars} caracteres en total."
                peticion = f"MODO B: Genera el prompt MÁS METICULOSO POSIBLE dentro de los límites. ANCLAJE VISUAL definitivo: '{idea_final}'. Estilos: {self.app.footer.estilos_texto()}.{formato}{regla_longitud}" + self.app.prompts.construir_modelo_info()

            texto = self.app.deepseek.generar(peticion, temperature=0.4, max_tokens=1500)
            texto = limpiar_marcadores(texto)
            # guardar_en_historial lee variables Tk (modo_var, combos, footer)
            # → SIEMPRE en el hilo principal vía after (leerlas desde el
            # worker arriesga "main thread is not in main loop" al cerrar).
            self.app.after(0, lambda t=texto: self.app.guardar_en_historial(t))

            def _mostrar_final():
                self.app.dialogs.actualizar_salida(texto)
                if es_referencia:
                    modo_txt = tr("Prompt generado con imagen como referencia visual")
                elif tiene_prompt:
                    modo_txt = tr("Prompt mejorado con análisis visual")
                else:
                    modo_txt = tr("Prompt anclado generado")
                self.app.dialogs.set_estado(tr('✅ Visión: [{0}] · LLM: {1} · {2}').format((motor), (self.app.llm_var.get()), (modo_txt)), P.TXT_OK)
                self.app.dialogs.toggle_botones(True)
            self.app.after(0, _mostrar_final)
        except Exception as e:
            self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr("❌ Error en Img→Prompt"), P.TXT_ERROR))
            self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))
