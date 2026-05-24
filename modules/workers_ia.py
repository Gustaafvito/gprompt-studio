"""Workers IA — threads de generación, visión, traducción.

Particionado desde core.py (~240 líneas).

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
import datetime
import logging
import threading

import customtkinter as ctk

from workers import limpiar_marcadores, parsear_ideas

logger = logging.getLogger("gprompt")


class WorkersIaMixin:
    """Mixin con los 5 workers IA que se lanzan en threads."""

    def _worker_ia(self, peticion, es_ideas=False, es_variaciones=False, n_variaciones=None,
                   es_refinamiento=False, texto_previo=None):
        try:
            self.after(0, self._iniciar_progreso)
            specs = self.get_current_model_specs()
            max_c = specs.get("max_chars") or specs.get("max_chars_letra") or 0 if specs else 0
            max_tok = 2500 if max_c >= 4000 else 2000 if max_c >= 2000 else 1800

            cerebro_elegido = self.llm_var.get()
            texto = self.deepseek.generar(peticion, max_tokens=max_tok)
            texto = limpiar_marcadores(texto)  # Eliminar ** y __ del resultado

            # CORTADOR DE SEGURIDAD: si el prompt excede el límite del modelo, lo recorta
            if max_c and not es_ideas and not es_variaciones:
                texto_original_len = len(texto)
                texto = self._recortar_si_excede(texto, max_c)
                if len(texto) < texto_original_len:
                    self.after(0, lambda: self.set_estado(f"✂️ Prompt recortado a {max_c} chars (máximo del modelo)", "#f39c12"))

            # ELIMINAR NEGATIVE si el modelo no lo soporta (Nano Banana, Gemini, Turbo en ComfyUI)
            es_comfyui_turbo = False
            if self.modo_var.get() == "imagen":
                es_comfyui_turbo = self._es_comfyui_turbo()
            quitar_negative = (specs and not specs.get("has_negative", True)) or es_comfyui_turbo
            if quitar_negative and not es_ideas:
                import re
                if re.search(r'NEGATIVE\s+PROMPT', texto, re.IGNORECASE):
                    texto = re.sub(r'\n?\s*NEGATIVE\s+PROMPT\s*:.*?(?=\n\s*(?:POSITIVE|─|$)|\Z)', '', texto, flags=re.DOTALL | re.IGNORECASE)
                    texto = texto.strip()
                    razon = "ComfyUI + Turbo" if es_comfyui_turbo else "este modelo"
                    self.after(0, lambda r=razon: self.set_estado(f"⚠️ NEGATIVE eliminado ({r} no lo soporta)", "#f39c12"))

            # ELIMINAR PESOS NUMÉRICOS solo en ComfyUI con modelos Turbo
            if es_comfyui_turbo and not es_ideas:
                import re
                if re.search(r'\([^)]+:[0-9.]+\)', texto):
                    # (word:1.2) → word   |   (word word:0.8) → word word
                    texto = re.sub(r'\(([^()]+?):\s*[0-9.]+\s*\)', r'\1', texto)
                    self.after(0, lambda: self.set_estado(f"⚠️ Pesos numéricos eliminados (ComfyUI + Turbo)", "#f39c12"))

            self.guardar_en_historial(texto)
            # No sobrescribir el resultado con el texto crudo de las
            # variaciones — esas se muestran en un modal con cards.
            # En refinamiento, abrimos el modal de diff con Aplicar/Cancelar
            # (Bloque 4) en vez de sobrescribir txt_salida directamente.
            if es_refinamiento:
                self.after(0, lambda: self._mostrar_diff_refinamiento(texto_previo or "", texto))
            elif not es_ideas and not es_variaciones:
                self.after(0, lambda: self.actualizar_salida(texto))
            estado_msg = (f"🔍 Refinamiento listo — revisa el diff ({cerebro_elegido})."
                          if es_refinamiento
                          else f"✅ Completado ({cerebro_elegido}).")
            self.after(0, lambda m=estado_msg: self.set_estado(m, "#2ecc71"))
            self.after(0, lambda: self.toggle_botones(True))
            self.after(0, self._sonar_completado)
            self.after(0, self._detener_progreso)
            if es_ideas:
                ideas = parsear_ideas(texto)
                # Fallback: si el LLM no usó formato "1. 2. 3.", dividir por bloques
                if not ideas:
                    bloques = [b.strip() for b in texto.split("\n\n") if len(b.strip()) > 30]
                    if bloques:
                        ideas = bloques[:3]
                self.after(0, lambda ideas=ideas: self._mostrar_ideas(ideas))
            elif es_variaciones: self.after(0, lambda: self._mostrar_variaciones(self._parsear_variaciones(texto, n_esperado=n_variaciones)))
        except Exception as e:
            self.after(0, lambda: self.actualizar_salida(f"❌ Error {self.llm_var.get()}: {e}"))
            self.after(0, lambda: self.set_estado("Error de conexión.", "#e74c3c"))
            self.after(0, lambda: self.toggle_botones(True))
            self.after(0, self._detener_progreso)

    def _worker_vision(self):
        try:
            self.after(0, lambda: self.set_estado("👁 Analizando imagen...", "#f39c12"))
            def on_status(msg): self.after(0, lambda: self.set_estado(msg, "#f39c12"))
            desc, motor = self.vision.describir(self.imagen_cargada, self.modo_var.get(), on_status)

            def _mostrar_resultado():
                idea_previa = self.txt_idea.get("1.0", "end").strip()
                self.txt_idea.delete("1.0", "end")
                self.txt_idea.insert("1.0", f"{desc}\n\n{idea_previa}" if idea_previa else desc)
                self.actualizar_salida(f"👁 [{motor}] analizó la imagen...\nRevisa y pulsa Generar Prompt.")
                self.set_estado(f"👁 [{motor}] — Edita la descripción y pulsa Generar Prompt", "#2ecc71")
                self.toggle_botones(True)
                self.txt_idea.focus_set()
            self.after(0, _mostrar_resultado)
        except Exception as e:
            self.after(0, lambda: self.set_estado("❌ Error visión.", "#e74c3c"))
            self.after(0, lambda: self.toggle_botones(True))

    def _worker_prompt_traduccion(self, idea_original):
        idea = idea_original
        if self.switch_traduccion_var.get() and self.detectar_idioma(idea_original):
            self.after(0, lambda: self.set_estado("🌐 Traduciendo al inglés...", "#f39c12"))
            idea = self.deepseek.traducir(idea_original)
            self.after(0, lambda: self.set_estado("🌐 Traducido...", "#3498db"))
        self._worker_ia(self._construir_peticion(idea, "B"))
    # ──────────────────────────────────────────────────────────────
    def _worker_prompt_quick(self, idea):
        """Worker para Quick Generate. Versión simplificada de _worker_prompt_traduccion."""
        try:
            modo = self.modo_var.get()
            specs = self.get_current_model_specs()
            limite_chars = specs.get("max_chars", 2000) if specs else 2000
            has_neg = specs.get("has_negative", True) if specs else True
            is_natural = self.is_natural_mode()

            # Construir petición reducida
            formato = ("FORMATO: lenguaje natural descriptivo." if is_natural
                       else "FORMATO: tags separados por comas con pesos (tag:1.2). NO prosa fluida.")
            neg_rule = ("Genera POSITIVE y NEGATIVE." if has_neg
                        else "Solo POSITIVE (este modelo no usa NEGATIVE).")

            # Personaje y LoRA si aplican
            extras = ""
            try:
                pers_nombre = self.combo_personaje.get() if hasattr(self, 'combo_personaje') else ""
                if pers_nombre and pers_nombre != "— Sin personaje —":
                    desc = self.store.descripcion_personaje(pers_nombre)
                    if desc:
                        extras += f"\nPERSONAJE: {desc}"
                lora_nombre = self.combo_lora.get() if hasattr(self, 'combo_lora') else ""
                if lora_nombre and lora_nombre != "— Sin LoRA —":
                    trigger = self.store.trigger_lora(lora_nombre)
                    if trigger:
                        extras += f"\nLORA TRIGGER (incluir literal): {trigger}"
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            ratio = self.ratio_var.get() if hasattr(self, 'ratio_var') else ""
            ratio_str = f"\nRATIO: {ratio}" if ratio else ""

            peticion = (
                f"⚡ QUICK MODE: prompt rápido y directo para {modo}.\n"
                f"IDEA: {idea}\n"
                f"ESTILOS: {self.estilos_texto()}{ratio_str}{extras}\n"
                f"{formato}\n"
                f"{neg_rule}\n"
                f"⛔ Máx {limite_chars} caracteres. Sé conciso, no añadas explicaciones."
            )

            # Inyección mínima del modelo (sin construir_modelo_info completo)
            modelo_actual = ""
            try:
                if modo == "imagen" and hasattr(self, 'combo_modelo_imagen'):
                    modelo_actual = self.combo_modelo_imagen.get()
                elif modo == "video" and hasattr(self, 'combo_modelo_video'):
                    modelo_actual = self.combo_modelo_video.get()
                elif modo == "audio" and hasattr(self, 'combo_modelo_audio'):
                    modelo_actual = self.combo_modelo_audio.get()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            if modelo_actual:
                peticion += f"\nMODELO: {modelo_actual}"

            # Generación rápida
            texto = self.deepseek.generar(peticion, temperature=0.4, max_tokens=1200)
            texto = limpiar_marcadores(texto)

            # Limpiar NEGATIVE si el modelo no lo soporta
            if not has_neg:
                texto = re.sub(r'\n?\s*NEGATIVE\s+PROMPT\s*:.*?$', '', texto,
                                flags=re.DOTALL | re.IGNORECASE).strip()

            self.guardar_en_historial(texto)

            def _aplicar():
                self.actualizar_salida(texto)
                self.set_estado("⚡ Quick listo", "#2ecc71")
                self.toggle_botones(True)
                try: self._sonar_completado()
                except Exception as e:
                    logger.debug(f"[silent] {e}")
            self.after(0, _aplicar)
        except Exception as e:
            self.after(0, lambda: self.set_estado(f"❌ Error Quick: {e}", "#e74c3c"))
            self.after(0, lambda: self.toggle_botones(True))

    # ──────────────────────────────────────────────────────────────
    def _worker_imagen_a_prompt(self):
        try:
            self.after(0, lambda: self.set_estado("👁 Analizando imagen...", "#f39c12"))
            def on_status(msg): self.after(0, lambda: self.set_estado(msg, "#f39c12"))
            desc, motor = self.vision.describir(self.imagen_cargada, self.modo_var.get(), on_status)
            self._ultimo_anclaje_visual = desc
            idea_manual = self.txt_idea.get("1.0", "end").strip()
            prompt_existente = self.txt_salida.get("1.0", "end").strip()

            # Detectar si hay un prompt existente para mejorar
            tiene_prompt = prompt_existente and ("PROMPT:" in limpiar_marcadores(prompt_existente) or len(prompt_existente) > 100)

            def _poner_desc():
                self.txt_idea.delete("1.0", "end")
                self.txt_idea.insert("1.0", f"{desc}\n\nAdiciones del usuario: {idea_manual}" if idea_manual else desc)
                if tiene_prompt:
                    self.set_estado(f"👁 [{motor}] → mejorando prompt existente con análisis visual...", "#f39c12")
                else:
                    self.set_estado(f"👁 [{motor}] → generando prompt con contexto visual anclado...", "#f39c12")
            self.after(0, _poner_desc)

            idea_final = desc if not idea_manual else f"{desc}\n\nAdiciones: {idea_manual}"
            if self.switch_traduccion_var.get() and self.detectar_idioma(idea_final):
                idea_final = self.deepseek.traducir(idea_final)

            specs = self.get_current_model_specs()
            limite_chars = specs.get("max_chars") if specs else 2000
            es_tag_based = not self.is_natural_mode()

            if tiene_prompt:
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
                    f"Estilos: {self.estilos_texto()}." + self.construir_modelo_info()
                )
            else:
                # MODO GENERAR: crear prompt nuevo desde imagen
                formato = " FORMATO OBLIGATORIO: tags separados por comas con pesos (tag:1.2). NO prosa fluida." if es_tag_based else ""
                regla_longitud = f" ⛔ REGLA ESTRICTA: El prompt FINAL no debe superar los {limite_chars} caracteres en total."
                peticion = f"MODO B: Genera el prompt MÁS METICULOSO POSIBLE dentro de los límites. ANCLAJE VISUAL definitivo: '{idea_final}'. Estilos: {self.estilos_texto()}.{formato}{regla_longitud}" + self.construir_modelo_info()

            texto = self.deepseek.generar(peticion, temperature=0.4, max_tokens=1500)
            texto = limpiar_marcadores(texto)
            self.guardar_en_historial(texto)

            def _mostrar_final():
                self.actualizar_salida(texto)
                modo_txt = "Prompt mejorado con análisis visual" if tiene_prompt else "Prompt anclado generado"
                self.set_estado(f"✅ Visión: [{motor}] · LLM: {self.llm_var.get()} · {modo_txt}", "#2ecc71")
                self.toggle_botones(True)
            self.after(0, _mostrar_final)
        except Exception as e:
            self.after(0, lambda: self.set_estado("❌ Error en Img→Prompt", "#e74c3c"))
            self.after(0, lambda: self.toggle_botones(True))
