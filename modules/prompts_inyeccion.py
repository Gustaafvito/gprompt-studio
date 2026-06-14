"""Inyección de specs del modelo y reglas de destino en el system prompt.

Construye el system_prompt enriquecido que se pasa al LLM, combinando:
  • Reglas base por modo (vídeo / imagen / audio)
  • Specs del modelo concreto (max_chars, sampler, formato tag vs natural,
    soporte de audio/negative, trigger words, plantillas)
  • Reglas adaptadas al destino (Instagram, TikTok, YouTube, Anthum…)

Métodos:
  • _inyectar_specs_modelo   — dispatcher por modo (video / imagen)
  • _inyectar_specs_video    — reglas específicas del motor de vídeo
  • _inyectar_specs_imagen   — reglas específicas del modelo de imagen
  • _inyectar_specs_formato  — tag-based vs natural + ComfyUI Turbo + pesos
  • _inyectar_template       — plantilla base si el motor la tiene definida
  • _inyectar_specs_audio    — reglas específicas del motor de audio
  • _inyectar_destino        — adapta el prompt según red/destino final
  • construir_modelo_info    — texto resumen del modelo activo (con caché)

Dependencias self (provistas por ArquitectoApp):
  modo_var, combo_modelo_video, combo_modelo_imagen, combo_modelo_audio,
  switch_instrumental_var, emocion_var, voz_var, idioma_audio_var,
  destino_var, plataforma_var, duracion_var, ratio_actual,
  personaje_activo, lora_activo, modelo_imagen_valido, modelo_video_valido,
  _es_comfyui_turbo.
"""
from config import (
    es_separador,
    get_audio_model_specs,
    get_image_model_specs,
    get_model_specs,
    get_prompt_template,
)
from prompts import REGLAS_APROVECHAR_BUDGET


class PromptsInyeccionService:
    """Servicio aislado de inyección de specs (A1 fase 2).

    Convertido de mixin a clase con app por composición.
    """

    def __init__(self, app):
        self.app = app
        self._cache_modelo_info = None
        self._cache_modelo_clave = None

    # ─── Helpers de duración / shots ───────────────────────────────
    def _duracion_a_segundos(self, dur_str: str) -> float:
        """Convierte '10s', '12s', '4-6s' a float (toma el primer número)."""
        if not dur_str:
            return 10.0
        s = dur_str.strip().lower().replace("s", "").split("-")[0]
        try:
            return float(s)
        except (ValueError, TypeError):
            return 10.0

    def _calcular_n_shots(self) -> int:
        """Devuelve el N de shots para el prompt de vídeo.

        - Si `shots_var` es "Auto" o no existe: regla por duración.
          4s→1, 5s→2, 10s→3, 15s→4 (y >15s → ceil(duracion/4)).
        - Si `shots_var` es un número 1-6: ese valor exacto.
        """
        shots_str = (
            self.app.shots_var.get()
            if hasattr(self.app, "shots_var")
            else "Auto"
        )
        if shots_str and shots_str != "Auto":
            try:
                return max(1, min(6, int(shots_str)))
            except (ValueError, TypeError):
                pass  # cae al cálculo automático
        # Auto
        dur = self._duracion_a_segundos(
            self.app.duracion_var.get()
            if hasattr(self.app, "duracion_var") else "10s"
        )
        if dur <= 4:   return 1
        if dur <= 5:   return 2
        if dur <= 10:  return 3
        if dur <= 15:  return 4
        # Para duraciones largas: ~1 shot cada 4s, máximo 6.
        return min(6, max(1, round(dur / 4)))

    def _inyectar_specs_modelo(self, system_prompt: str) -> str:
        modo = self.app.modo_var.get()
        if modo == "video":
            return self._inyectar_specs_video(system_prompt)
        if modo == "imagen":
            return self._inyectar_specs_imagen(system_prompt)
        return system_prompt

    def _inyectar_specs_video(self, system_prompt: str) -> str:
        specs = get_model_specs(self.app.combo_modelo_video.get())
        if not specs:
            return system_prompt
        motor = self.app.combo_modelo_video.get()
        max_c = specs["max_chars"]

        if max_c >= 4000:
            palabras_obj, detalle = "400-700", "EXTREMADAMENTE DETALLADO: múltiples shots con las 7 capas visuales"
        elif max_c >= 2000:
            palabras_obj, detalle = "220-360", "MUY DETALLADO: describe con precisión cada shot"
        else:
            palabras_obj, detalle = "130-210", "DETALLADO Y CONCISO: sujeto+acción"

        # Cálculo de número de shots: manual override o regla por duración
        n_shots = self._calcular_n_shots()
        duracion_str = self.app.duracion_var.get() if hasattr(self.app, "duracion_var") else "10s"
        seg_por_shot = self._duracion_a_segundos(duracion_str) / max(n_shots, 1)

        extra = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        extra += f"REGLAS ESPECÍFICAS PARA {motor.upper()}:\n"
        extra += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        extra += f"• Estructura de prompt: {specs['prompt_formula']}\n"
        extra += f"• Ejemplo de referencia: {specs['prompt_ejemplo']}\n"
        extra += f"• OBJETIVO DE LONGITUD: {palabras_obj} palabras (~{max_c} caracteres máximo). {detalle}.\n"
        extra += f"• ⛔ LÍMITE ABSOLUTO INNEGOCIABLE: {max_c} caracteres totales.\n"
        extra += (
            f"• 🎬 NÚMERO DE SHOTS: EXACTAMENTE {n_shots} shot{'s' if n_shots != 1 else ''} "
            f"para una duración total de {duracion_str} "
            f"(~{seg_por_shot:.1f}s por shot). NO añadas más ni menos. "
            f"Distribuye el arco narrativo en {n_shots} momentos clave.\n"
        )
        extra += f"• Mejor para: {specs['best_for']}\n"

        if specs["has_audio"] and specs["audio_desc"]:
            extra += f"• ✅ Este modelo SOPORTA audio. Capacidades: {specs['audio_desc']}.\n"
            extra += "• AÑADE línea 'Audio:' al final. Diálogos/voz-over EN CASTELLANO por defecto.\n"
        else:
            extra += "• ❌ Este modelo NO tiene audio nativo. NO incluyas descripciones de audio.\n"

        if not specs["has_negative"]:
            extra += "• ❌ Este modelo NO usa prompt negativo. NO generes NEGATIVE PROMPT.\n"
        else:
            extra += "• ✅ Este modelo SÍ usa prompt negativo. Genera POSITIVE y NEGATIVE PROMPT.\n"

        if specs.get("limitaciones"):
            extra += f"• Limitaciones a respetar: {specs['limitaciones']}\n"

        extra = self._inyectar_template(motor, extra)
        extra += REGLAS_APROVECHAR_BUDGET
        return system_prompt + extra

    def _inyectar_specs_imagen(self, system_prompt: str) -> str:
        modelo = self.app.combo_modelo_imagen.get()
        if es_separador(modelo):
            return system_prompt
        specs = get_image_model_specs(modelo)
        if not specs:
            return system_prompt

        max_c = specs["max_chars"]
        if max_c >= 1000:
            palabras_obj, detalle = "80-150", "MUY DETALLADO"
        else:
            palabras_obj, detalle = "50-90", "DETALLADO"

        extra = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        extra += f"REGLAS ESPECÍFICAS PARA {modelo.upper()}:\n"
        extra += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        if specs.get('nota'):
            extra += f"• Rating del modelo: ⭐ {specs['nota']}/5\n"
        extra += f"• Mejor para: {specs['best_for']}\n"
        extra += f"• Estructura del prompt: {specs['prompt_formula']}\n"
        extra += f"• Ejemplo de referencia: {specs['prompt_ejemplo']}\n"
        extra += f"• OBJETIVO DE LONGITUD: {palabras_obj} palabras (~{max_c} caracteres). {detalle}.\n"
        extra += f"• ⛔ LÍMITE ABSOLUTO INNEGOCIABLE: {max_c} caracteres totales.\n"

        extra = self._inyectar_specs_formato(modelo, specs, extra)
        if specs.get("limitaciones"):
            extra += f"• Limitaciones: {specs['limitaciones']}\n"

        extra = self._inyectar_template(modelo, extra)
        extra += REGLAS_APROVECHAR_BUDGET
        return system_prompt + extra

    def _inyectar_specs_formato(self, modelo: str, specs: dict, extra: str) -> str:
        # Formato especial Z-Image-Base: bloques narrativos + negative dinámico
        if specs.get("formato_bloques") == "z_image":
            return self._inyectar_formato_z_image(modelo, specs, extra)
        # Formato especial GPT Image: 7 bloques en inglés, sin NEGATIVE
        if specs.get("formato_bloques") == "gpt_image":
            return self._inyectar_formato_gpt_image(modelo, specs, extra)
        # Formato especial Nano Banana (Gemini): 6 bloques checklist + edit
        if specs.get("formato_bloques") == "nano_banana":
            return self._inyectar_formato_nano_banana(modelo, specs, extra)

        if specs.get("is_natural"):
            extra += "• TIPO: lenguaje natural descriptivo. NO uses tags sueltos separados por comas.\n"
            extra = self._inyectar_estilo_flux(modelo, extra)
            if specs["has_negative"]:
                extra += "\n⚠️ FORMATO DE SALIDA OBLIGATORIO ⚠️\nPROMPT: [descripción fluida]\nNEGATIVE PROMPT: [tags a evitar]\n"
            else:
                extra += "\n⚠️ FORMATO DE SALIDA OBLIGATORIO ⚠️\nPROMPT: [descripción fluida]\n(No generes NEGATIVE PROMPT — este modelo no lo soporta)\n"
        else:
            extra += "• TIPO: tag-based Danbooru/SD. Usa comas, orden de tags SD.\n"
            es_comfyui_turbo = self.app._es_comfyui_turbo(self.app.plataforma_var.get(), modelo)
            if es_comfyui_turbo:
                extra += "• ⛔ PLATAFORMA ComfyUI + MODELO TURBO: NO USES PESOS NUMÉRICOS tipo (tag:1.2). Solo tags limpios separados por comas. El CFG bajo (~1.0) hace que los pesos sean IGNORADOS o produzcan ruido. Ejemplo CORRECTO: 'close-up portrait, silver hair, detailed skin' | INCORRECTO: '(close-up portrait:1.3), (silver hair:1.2)'.\n"
                extra += "• ⛔ NO generes NEGATIVE PROMPT. En ComfyUI los modelos Turbo lo ignoran.\n"
            else:
                extra += "• Puedes usar pesos (tag:1.2) cuando sea útil para enfatizar elementos clave.\n"
            if specs.get("trigger_words"):
                extra += f"• TRIGGER WORDS OBLIGATORIOS al inicio: {specs['trigger_words']}\n"
            if specs.get("sampler_recomendado"):
                extra += f"• Sampler recomendado: {specs['sampler_recomendado']}\n"
            if es_comfyui_turbo:
                extra += "\n⚠️ FORMATO DE SALIDA OBLIGATORIO ⚠️\nPOSITIVE PROMPT: [tags en inglés SIN pesos]\n(No generes NEGATIVE PROMPT)\n"
            elif specs["has_negative"]:
                extra += "\n⚠️ FORMATO DE SALIDA OBLIGATORIO ⚠️\nPOSITIVE PROMPT: [tags en inglés]\nNEGATIVE PROMPT: [tags negativos]\n"
            else:
                extra += "• ⛔ Este modelo NO SOPORTA NEGATIVE PROMPT. Solo genera POSITIVE PROMPT.\n"
        return extra

    # Mapa estilo → orientación para la familia FLUX (toggle "Estilo").
    _FLUX_ESTILO_HINT = {
        "Photoreal": "fotorrealismo puro: piel, materiales y luz realistas, estética de fotografía (no ilustración)",
        "Anime": "estilo anime / ilustración japonesa: lineart limpio, cel-shading, colores vivos",
        "Creative": "ilustración creativa / arte conceptual estilizado (no foto)",
        "Fantasy": "fantasía épica/mística: criaturas, magia, atmósfera de leyenda",
        "SciFi": "ciencia ficción / cyberpunk: tecnología, neón, robots, naves, futurista",
    }

    def _inyectar_estilo_flux(self, modelo: str, extra: str) -> str:
        """Si el modelo es de la familia FLUX y el usuario forzó un estilo en el
        toggle 'Estilo' (Photoreal/Anime/...), orienta la descripción a esa
        categoría. 'Auto' o familia no-FLUX → no toca nada."""
        try:
            from config import detectar_familia
            if detectar_familia(modelo) != "flux":
                return extra
            estilo = "Auto"
            if hasattr(self.app, "familia_estilo_var"):
                estilo = self.app.familia_estilo_var.get() or "Auto"
            if estilo == "Auto":
                return extra
            hint = self._FLUX_ESTILO_HINT.get(estilo, estilo)
            extra += (
                f"\n🎯 ESTILO FORZADO POR EL USUARIO: {estilo}.\n"
                f"  • Orienta TODA la descripción a: {hint}.\n"
                f"  • No mezcles con otras estéticas; el usuario eligió '{estilo}'.\n"
            )
        except Exception:
            pass
        return extra

    def _inyectar_formato_z_image(self, modelo: str, specs: dict, extra: str) -> str:
        """Reglas específicas Z-Image-Base (S3-DiT, 6B params, formato híbrido).

        Estructura forzada:
        1. Preámbulo de quality tags con pesos: (masterpiece, top quality...).
        2. 4 bloques narrativos: [Sujeto y Composición] [Acción] [Entorno] [Lighting & Mood].
        3. NEGATIVE PROMPT dinámico = bloque fijo universal + bloque variable por
           categoría (Fotorrealismo / Fantasía Mística / Ciencia Ficción).

        El LLM debe ELEGIR la categoría según la idea del usuario.
        """
        extra += (
            "• TIPO: Z-Image-Base — arquitectura S3-DiT (Single-Stream Diffusion "
            "Transformer, 6B params). HÍBRIDO: tag preamble con pesos + bloques "
            "narrativos en lenguaje natural.\n"
            "• El modelo concatena tokens de texto + visuales en flujo unificado: "
            "usa la estructura por BLOQUES claros para que procese instrucciones "
            "en orden.\n"
            "• Bilingüe EN/ZH. Strong en typography y high-frequency details.\n"
            "• Settings óptimos: 28-50 steps, CFG 3-5.\n"
        )

        # Detectar LoRA(s) activo(s) para insertar bloque dedicado.
        # Multi-LoRA: el bloque [LoRA Activation & Style] lista todos los
        # triggers (primario + extras del modal) en formato
        # "trig1 style + trig2 style + ...".
        triggers_lora: list = []
        rasgos_lora: list = []
        try:
            if hasattr(self.app, "footer"):
                triggers_lora = self.app.footer.triggers_loras_activos() or []
                rasgos_lora = self.app.footer.rasgos_loras_activos() or []
        except Exception:
            triggers_lora = []
            rasgos_lora = []
        lora_trigger = triggers_lora[0] if triggers_lora else ""
        # String para mostrar en el bloque [LoRA Activation & Style]
        # Ej con 1: "lmnlhrr style"
        # Ej con 2: "lmnlhrr style + flux_anime style"
        triggers_bloque = " + ".join(f"{t} style" for t in triggers_lora) if triggers_lora else ""
        # Rasgos visuales combinados (si hay)
        rasgos_combinados = " | ".join(rasgos_lora) if rasgos_lora else ""

        # Toggle "Estilo" — el usuario fuerza una categoría en lugar de
        # dejar que el LLM elija a ciegas. Hint el bloque ESTILÍSTICO del
        # NEGATIVE (categoría 📷/🐉/🤖) además de orientar el POSITIVE.
        estilo_z = "Auto"
        try:
            if hasattr(self.app, "familia_estilo_var"):
                estilo_z = self.app.familia_estilo_var.get() or "Auto"
        except Exception:
            estilo_z = "Auto"
        if estilo_z != "Auto":
            categoria_map = {
                "Photoreal": "📷 FOTORREALISMO PURO (retratos, comida, productos, gente real)",
                "Creative":  "🎨 CREATIVO / ILUSTRACIÓN / ARTE CONCEPTUAL (estilizado, no foto)",
                "Fantasy":   "🐉 FANTASÍA MÍSTICA / ÉPICA (dragones, fénix, magia, dioses)",
                "SciFi":     "🤖 CIENCIA FICCIÓN / CYBERPUNK (robots, tech, naves, AI)",
            }
            extra += (
                f"\n🎯 ESTILO Z FORZADO POR EL USUARIO: {estilo_z}.\n"
                f"  • En el POSITIVE, orienta TODA la descripción a esta categoría.\n"
                f"  • En el NEGATIVE, usa OBLIGATORIAMENTE el bloque "
                f"estilístico de: {categoria_map.get(estilo_z, estilo_z)}.\n"
                f"  • NO mezcles con otras categorías. El usuario eligió "
                f"explícitamente '{estilo_z}'.\n"
            )

        if lora_trigger:
            bloques_positivos = (
                "[Subject & Composition] <SHOT type (close-up / medium / wide) + "
                "ANGLE + POSE/action + composition. "
                "IMPORTANT: if the user's idea OR an active character profile "
                "specifies physical traits (hair color, eye color, distinctive "
                "features, wardrobe), include them HERE EXPLICITLY — they "
                "reinforce the LoRA weights. Example: 'Medium shot of Nyra, "
                "her vivid red hair with sharp left-side undercut and piercing "
                "amber eyes catching the light, leather jacket collar turned up'. "
                "If the user gives NO specific traits, keep it minimal (just "
                "framing + pose) and let the LoRA handle the appearance.>\n"
                f"[LoRA Activation & Style] {triggers_bloque}, <One line "
                f"describing the visual style/aesthetic these LoRAs "
                f"contribute (e.g. 'cinematic cyberpunk noir', "
                f"'liminal horror atmosphere'). Do NOT repeat the physical "
                f"description here — that belongs in [Subject & Composition].>\n"
                "[Lighting & Environment] <Specific lighting (golden hour, "
                "volumetric, dappled shadows, rim light, fluorescent, neon) + "
                "environment/background details, era, props. Color grading. "
                "Atmospheric elements (rain, fog, dust motes).>\n"
                "[Mood] <Emotional atmosphere — tense, peaceful, epic, "
                "melancholic, haunting, etc. Plus one line about temporal/"
                "geometric coherence and realism level.>\n"
            )
            preambulo = (
                "(masterpiece, top quality, best quality, raw photo:1.2), 8k, "
                "ultra-detailed, sharp focus, cinematic composition, "
                "depth of field, <lente sugerida: 35mm lens shot, wide-angle "
                "drone, macro>.\n"
            )
            triggers_list_str = ", ".join(f"`{t}`" for t in triggers_lora)
            plural_palabra = "trigger" if len(triggers_lora) == 1 else "triggers"
            # Bloque opcional con rasgos visuales de los LoRAs (sesión 16)
            bloque_rasgos = ""
            if rasgos_combinados:
                bloque_rasgos = (
                    f"\n🎭 RASGOS VISUALES DEL/LOS LORA(S) — INCLÚYELOS "
                    f"EXPLÍCITAMENTE en [Subject & Composition]:\n"
                    f"  {rasgos_combinados}\n"
                    f"  • Estos rasgos son los que el LoRA tiene entrenados; "
                    f"mencionarlos en el prompt los REFUERZA y asegura que "
                    f"salgan en la imagen.\n"
                    f"  • Adáptalos al contexto de la escena (puedes "
                    f"reformular pero NO contradigas).\n"
                )
            nota_lora = (
                f"{bloque_rasgos}"
                f"\n🔗 LORA(S) ACTIVO(S) — REGLAS ESTRICTAS:\n"
                f"  • {plural_palabra.capitalize()}: {triggers_list_str}.\n"
                f"  • Inclúyelos UNA SOLA VEZ cada uno, EXCLUSIVAMENTE "
                f"al inicio del bloque [LoRA Activation & Style] "
                f"(formato: `{triggers_bloque}, ...`).\n"
                f"  • ❌ NO los pongas en el preámbulo de quality tags.\n"
                f"  • ❌ NO los pongas en [Subject & Composition].\n"
                f"  • ❌ NO los pongas en [Lighting & Environment] ni [Mood].\n"
                f"  • ❌ NO repitas ningún trigger en otros bloques.\n"
                f"  • NO los traduzcas ni modifiques (son literales).\n"
                f"\n"
                f"🎭 RASGOS DEL PERSONAJE — REFUERZO VERBAL:\n"
                f"  • El LoRA aporta los pesos entrenados, pero para que la "
                f"apariencia salga con FUERZA y CONSISTENCIA, el LLM debe "
                f"reforzar verbalmente los rasgos distintivos en "
                f"[Subject & Composition].\n"
                f"  • ✅ Si el usuario da rasgos en la idea o tiene un "
                f"Personaje activo, MENCIÓNALOS EXPLÍCITAMENTE en "
                f"[Subject & Composition] (pelo color X, ojos color Y, "
                f"undercut, etc.).\n"
                f"  • ✅ Si NO hay rasgos del usuario y NO sabes los del "
                f"LoRA, deja [Subject & Composition] enfocado en plano + "
                f"pose + escena (sin inventar rasgos).\n"
                f"  • ❌ NO inventes rasgos contradictorios con lo que "
                f"sabes del LoRA (si el LoRA es 'Nyra pelirroja', no la "
                f"describas como rubia).\n"
                f"  • Los TRIGGERS van solo en [LoRA Activation & Style], "
                f"no los repitas en otros bloques.\n"
            )
        else:
            bloques_positivos = (
                "[Sujeto y Composición] <Sujeto principal + plano "
                "(close-up/wide/etc) + pose/composición. Describe rasgos "
                "físicos concretos: textura piel, color ojos/pelo, vestuario.>\n"
                "[Acción] <Qué está haciendo. Gestos, expresión, interacción. "
                "Si hay destrucción/efectos: describe física (gotas, astillas, "
                "vetas de energía, no solo 'magia').>\n"
                "[Entorno] <Fondo, escenografía, época, props. Si es DOF: "
                "bokeh + elementos secundarios desenfocados.>\n"
                "[Lighting & Mood] <Iluminación específica (golden hour, "
                "volumetric, dappled shadows, rim light) + atmósfera "
                "emocional (tense, peaceful, epic, melancholic).>\n"
            )
            preambulo = (
                "(masterpiece, top quality, best quality, raw photo:1.2), 8k, "
                "ultra-detailed, sharp focus, cinematic composition, "
                "<lente sugerida: ej 35mm lens shot, wide-angle drone, macro>.\n"
            )
            nota_lora = ""

        extra += (
            "\n⚠️ FORMATO DE SALIDA OBLIGATORIO ⚠️\n"
            "\n"
            "POSITIVE PROMPT:\n"
            + preambulo
            + bloques_positivos
            + nota_lora
            + "\n"
            "NEGATIVE PROMPT:\n"
            "<Bloque base> + <Bloque condicional según contenido> + <Bloque estilístico por categoría>\n"
            "\n"
            "━━━ REGLAS NEGATIVE ADAPTATIVO (3 bloques) ━━━\n"
            "1️⃣ BLOQUE BASE — calidad técnica universal (SIEMPRE incluir):\n"
            "   blurry, low-res, watermark, signature, cropped, out of frame, "
            "digital noise, jpeg artifacts\n"
            "\n"
            "2️⃣ BLOQUE CONDICIONAL — añade SOLO lo relevante según la escena:\n"
            "   ▸ Si hay PERSONAS / CRIATURAS con manos:\n"
            "       extra fingers, bad anatomy, deformed hands, bad proportions, "
            "extra limbs\n"
            "   ▸ Si hay CARAS / RETRATOS:\n"
            "       asymmetric eyes, misaligned teeth, distorted face, "
            "uncanny valley\n"
            "   ▸ Si NO hay texto intencional (poster/libro/cartel):\n"
            "       distorted text, garbled text, gibberish text\n"
            "       (Si SÍ hay texto intencional: OMITE estas tags)\n"
            "   ▸ Si se busca detalle alto (close-ups, macro):\n"
            "       low detail, smooth, simplified, lack of texture\n"
            "   ▸ Si es PAISAJE/ESCENARIO sin humanos:\n"
            "       (NO añadas las tags de anatomía/caras — son ruido)\n"
            "   ▸ Si la escena debe ser ESTÁTICA / quieta:\n"
            "       motion blur, motion lines\n"
            "   ▸ Si la escena debe tener MOVIMIENTO dramático:\n"
            "       static, frozen pose, stiff\n"
            "\n"
            "3️⃣ BLOQUE ESTILÍSTICO — UNA categoría según el sujeto/género:\n"
            "   📷 FOTORREALISMO PURO (retratos, comida, productos, gente real):\n"
            "       cartoon, illustration, painting, anime, 3d render, "
            "smooth airbrushed skin, plastic skin, heavy makeup, "
            "studio lighting, artificial reflections, oversaturated\n"
            "   🐉 FANTASÍA MÍSTICA / ÉPICA (dragones, fénix, magia, dioses):\n"
            "       cute creature, friendly, mundane background, modern "
            "elements, boring lighting, flat colors, photorealistic city\n"
            "   🤖 CIENCIA FICCIÓN / CYBERPUNK (robots, tech, naves, AI):\n"
            "       fantasy magic, medieval armor, organic monster, "
            "rustic textures, historical setting, antique props\n"
            "\n"
            "📝 Ejemplo 1 — idea: 'retrato de mujer en cocina vintage':\n"
            "   blurry, low-res, watermark, signature, cropped, out of frame, "
            "digital noise, jpeg artifacts, extra fingers, bad anatomy, "
            "deformed hands, bad proportions, asymmetric eyes, misaligned "
            "teeth, distorted text, garbled text, cartoon, illustration, "
            "painting, anime, 3d render, smooth airbrushed skin, plastic "
            "skin, oversaturated\n"
            "\n"
            "📝 Ejemplo 2 — idea: 'paisaje de montañas nevadas al atardecer':\n"
            "   blurry, low-res, watermark, signature, cropped, out of frame, "
            "digital noise, jpeg artifacts, distorted text, garbled text, "
            "low detail, simplified, cartoon, illustration, painting, anime, "
            "3d render, oversaturated\n"
            "   (Sin tags de anatomía — no hay personas; sin tags de "
            "movimiento — paisaje estático)\n"
        )
        return extra

    def _inyectar_formato_gpt_image(self, modelo: str, specs: dict, extra: str) -> str:
        """Reglas específicas GPT Image (1.5 / 2) en SeaArt.

        Lenguaje natural en prosa fluida estructurada por 7 bloques en
        inglés. SIN NEGATIVE PROMPT (modelo natural). SIN pesos numéricos
        ni sintaxis SD.

        Si hay LoRA con "Rasgos visuales" rellenado (multi-LoRA o
        primario), los rasgos se inyectan en [Subject] como REFUERZO
        verbal — NO como bloque dedicado [LoRA Activation & Style]
        porque GPT Image no usa triggers SD.
        """
        # Detectar si hay rasgos visuales para reforzar el sujeto
        rasgos_lora: list = []
        try:
            if hasattr(self.app, "footer"):
                rasgos_lora = self.app.footer.rasgos_loras_activos() or []
        except Exception:
            rasgos_lora = []
        rasgos_combinados = " | ".join(rasgos_lora) if rasgos_lora else ""

        # Toggle "Estilo" del usuario para GPT Image. Cuando != Auto,
        # se inyecta un hint que orienta TODA la salida hacia esa
        # categoría (photoreal, editorial, illustration, UI, poster).
        estilo_gpt = "Auto"
        try:
            if hasattr(self.app, "familia_estilo_var"):
                estilo_gpt = self.app.familia_estilo_var.get() or "Auto"
        except Exception:
            estilo_gpt = "Auto"

        extra += (
            "• TIPO: GPT Image (modelo OpenAI multimodal en SeaArt). "
            "Lenguaje NATURAL en prosa fluida, NO tags separados por "
            "comas, NO pesos numéricos, NO sintaxis SD.\n"
            "• Excelente con TEXTO DENTRO DE LA IMAGEN: si el usuario "
            "menciona texto literal, usa comillas ('with the words "
            "\"...\"').\n"
            "• Instruction following ESTRICTO: pide composiciones y "
            "spatial arrangements complejos sin temer reinterpretaciones.\n"
            "• Razonamiento: el modelo lee el prompt entero, así que "
            "el orden y la coherencia importan.\n"
        )
        extra += (
            "\n⚠️ FORMATO DE SALIDA OBLIGATORIO ⚠️\n"
            "\n"
            "PROMPT:\n"
            "[Subject] <Main subject + detailed physical traits (face, "
            "hair, eyes, build, ethnicity if relevant) + clothing/"
            "wardrobe + pose/expression. Concrete and specific.>\n"
            "[Setting] <Location + environment + background elements + "
            "era/period + key props. Where the subject is and what "
            "surrounds them.>\n"
            "[Lighting] <Light source (sun, neon, candle, fluorescent) + "
            "direction (from the left, backlit, top-down) + quality "
            "(soft, harsh, volumetric, rim light) + mood it creates.>\n"
            "[Style] <Visual style: photorealistic / illustration / "
            "cinematic / editorial / vector / oil painting. Reference "
            "specifics: lens (35mm, 85mm, macro), film stock (Portra 400, "
            "Cinestill), art reference if relevant.>\n"
            "[Composition] <Shot type (close-up / medium / wide / "
            "extreme wide / over-the-shoulder) + angle (eye-level, low, "
            "high, dutch) + framing (centered, rule of thirds, symmetric).>\n"
            "[Mood] <Emotional atmosphere + overall feeling (epic, "
            "intimate, melancholic, energetic, contemplative, mysterious).>\n"
            "[Text in image] <ONLY if the user's idea mentions text in "
            "the image: with the words \"EXACT WORDS\" in [font style, "
            "color, placement]. If no text: OMIT this block entirely.>\n"
            "\n"
            "━━━ REGLAS GENERALES GPT IMAGE ━━━\n"
            "  • NO incluyas NEGATIVE PROMPT — este modelo no lo soporta.\n"
            "  • NO uses pesos numéricos (tag:1.2). No aplica.\n"
            "  • NO inventes triggers SD (lmnlhrr, etc.) — el modelo "
            "no los reconoce.\n"
            "  • Sé ESPECÍFICO con lighting, composition y mood — "
            "GPT Image los respeta al pie de la letra.\n"
            "  • Para texto en la imagen: usa comillas dobles con la "
            "palabra exacta. Indica font/color/placement si importa.\n"
            "  • El bloque [Text in image] SOLO va si el usuario lo "
            "pide. Si no lo menciona, OMÍTELO completamente.\n"
        )
        if rasgos_combinados:
            extra += (
                f"\n🎭 RASGOS VISUALES DEL/LOS LORA(S) — INCLÚYELOS "
                f"EXPLÍCITAMENTE en [Subject]:\n"
                f"  {rasgos_combinados}\n"
                f"  • Adáptalos al contexto de la escena sin contradecir.\n"
                f"  • Refuerzan los pesos del LoRA cuando el output se "
                f"abre en SeaArt con LoRA activo.\n"
            )

        # Hint de estilo forzado por el usuario (toggle "Estilo")
        if estilo_gpt != "Auto":
            estilo_map_gpt = {
                "Photoreal": (
                    "📷 FOTORREALISMO. El [Style] DEBE pedir: photorealistic, "
                    "natural skin texture, real photography, no AI shine, "
                    "specify lens (50mm/85mm) and film stock (Portra 400, "
                    "Cinestill, Kodak Gold). El [Mood] grounded y natural. "
                    "EVITA términos de ilustración."
                ),
                "Editorial": (
                    "📰 EDITORIAL / MARKETING. El [Style] DEBE pedir: "
                    "editorial photography, fashion magazine aesthetic, "
                    "Vogue/Harper's Bazaar quality, professional lighting, "
                    "clean composition. [Composition] con énfasis en rule "
                    "of thirds y leading lines. [Mood] sofisticado y "
                    "aspiracional. Ideal para banners, ads, social media."
                ),
                "Illustration": (
                    "🎨 ILUSTRACIÓN / ARTE CONCEPTUAL. El [Style] DEBE "
                    "pedir: digital illustration, stylized, hand-drawn "
                    "feel, vibrant colors. Especifica medium (watercolor, "
                    "vector, gouache, oil painting) y artist reference si "
                    "ayuda. [Composition] más creativa. EVITA pedir "
                    "photorealistic."
                ),
                "UI-Mockup": (
                    "🖥 UI / MOCKUP. El [Subject] es la INTERFAZ (app "
                    "screen, dashboard, browser window, product page). "
                    "[Setting] específico (iOS, web, desktop). [Style] "
                    "clean, modern UI, flat design, realistic device "
                    "frame. Incluye elementos de UI (buttons, cards, "
                    "navigation, status bar). [Text in image] activo "
                    "OBLIGATORIO con etiquetas reales en comillas."
                ),
                "Poster-Typography": (
                    "📰 POSTER / TYPOGRAPHY DENSA. La imagen tiene "
                    "TEXTO COMO PROTAGONISTA. [Subject] es el conjunto "
                    "tipográfico + visuales de apoyo. [Composition] tipo "
                    "poster (hierarchy clara, headline + body + footer). "
                    "[Text in image] OBLIGATORIO con texto detallado entre "
                    "comillas, font style, color, placement, jerarquía. "
                    "Especifica formato (movie poster, book cover, "
                    "infographic, magazine cover, propaganda)."
                ),
            }
            hint = estilo_map_gpt.get(estilo_gpt, "")
            if hint:
                extra += (
                    f"\n🎯 ESTILO FORZADO POR EL USUARIO: {estilo_gpt}.\n"
                    f"  {hint}\n"
                    f"  • Orienta TODA la salida (Subject/Setting/Style/"
                    f"Composition/Mood) a esta categoría.\n"
                    f"  • NO mezcles con otras categorías.\n"
                )
        return extra

    def _inyectar_formato_nano_banana(self, modelo: str, specs: dict, extra: str) -> str:
        """Reglas específicas familia Nano Banana (Gemini) en SeaArt.

        Aplica a: Nano Banana (Gemini 2.5 Flash), Nano Banana Pro Image
        (Gemini 3 Pro), Nano Banana 2 (Gemini 3.1 Flash).

        Estructura derivada del consenso SeaArt (marketing NB2) + Google
        Gemini docs: 6 bloques checklist en inglés + bloque condicional
        [Edit Instructions] que el LLM activa SOLO si la idea es de
        edición. SIN NEGATIVE PROMPT (Gemini no lo soporta). SIN pesos
        numéricos ni sintaxis SD.

        Si hay LoRA con "Rasgos visuales" rellenado, los rasgos se
        inyectan en [Subject] como REFUERZO verbal — NO como bloque
        dedicado [LoRA Activation & Style] porque Gemini no usa
        triggers SD.
        """
        # Rasgos de LoRA activos (multi-LoRA o primario)
        rasgos_lora: list = []
        try:
            if hasattr(self.app, "footer"):
                rasgos_lora = self.app.footer.rasgos_loras_activos() or []
        except Exception:
            rasgos_lora = []
        rasgos_combinados = " | ".join(rasgos_lora) if rasgos_lora else ""

        # Toggle "Estilo" del usuario
        estilo_nb = "Auto"
        try:
            if hasattr(self.app, "familia_estilo_var"):
                estilo_nb = self.app.familia_estilo_var.get() or "Auto"
        except Exception:
            estilo_nb = "Auto"

        extra += (
            "• TIPO: Nano Banana (motor Gemini en SeaArt). Lenguaje "
            "NATURAL en prosa fluida con bloques estructurados. NO tags "
            "separados por comas, NO pesos numéricos (tag:1.2), NO "
            "corchetes [tag], NO sintaxis SD, NO triggers SD.\n"
            "• Fortalezas: character consistency entre ediciones, "
            "multi-turn editing sin pérdida de contexto, multi-image "
            "fusion, style transfer, instruction following preciso.\n"
            "• Especialmente bueno para: edición ('Replace background "
            "with...', 'Make her wear...'), preservación de identidad "
            "('Keep face identity, only change...'), outpainting "
            "('Extend canvas to show...').\n"
        )
        extra += (
            "\n⚠️ FORMATO DE SALIDA OBLIGATORIO ⚠️\n"
            "\n"
            "PROMPT:\n"
            "[Subject] <Main subject + detailed physical traits (face, "
            "hair, eyes, build, age, ethnicity if relevant) + clothing/"
            "wardrobe + pose/expression. Be concrete and specific. For "
            "non-human subjects (creature/robot/object) describe form, "
            "materials and distinguishing features.>\n"
            "[Scene] <Location + environment + background elements + "
            "key props + era/period. Where the subject is and what "
            "surrounds them.>\n"
            "[Composition] <Shot type (close-up / medium / wide / "
            "extreme wide / over-the-shoulder / POV) + angle (eye-level, "
            "low, high, dutch, overhead) + framing (centered, rule of "
            "thirds, symmetric, off-center).>\n"
            "[Lighting] <Light source (sun, neon, candle, fluorescent, "
            "softbox) + direction (from the left, backlit, top-down, "
            "rim) + quality (soft, harsh, volumetric, golden hour) + "
            "mood it creates.>\n"
            "[Materials] <Textures and surfaces with specificity: "
            "polished metal, frosted glass, weathered leather, fine "
            "fabric weave, skin texture with natural imperfections, "
            "wood grain, etc. Critical for photorealism.>\n"
            "[Style] <Visual style: photorealistic / cinematic / "
            "illustration / watercolor / oil painting / cartoon. "
            "Reference specifics if relevant: lens (35mm, 85mm, macro), "
            "film stock (Portra 400, Cinestill), art reference.>\n"
            "[Output] <ONE single short sentence (max 15 words). "
            "Only: aspect ratio + 'professional grade, no artifacts'. "
            "NO film stock, NO ISO, NO lens specs here (those go in "
            "[Style] / [Composition]). NO storytelling. Just the tech "
            "wrap-up.>\n"
            "[Edit Instructions] <ONLY if the user's idea is an EDIT "
            "(replace/change/add/remove/extend over an existing image). "
            "Otherwise OMIT this block entirely. Format: 'Replace X "
            "with Y' / 'Make her/him wear Z' / 'Extend canvas upward "
            "to show W' followed by 'Keep face identity, keep pose, "
            "keep color palette, only change [outfit/background/...]'.>\n"
            "\n"
            "━━━ REGLAS GENERALES NANO BANANA / GEMINI ━━━\n"
            "  • NO incluyas NEGATIVE PROMPT — Gemini no lo soporta.\n"
            "  • NO uses pesos numéricos (tag:1.2). El modelo los "
            "ignora o degrada.\n"
            "  • NO uses corchetes [tag] estilo SD/A1111.\n"
            "  • NO inventes triggers SD (lmnlhrr, etc.) — Gemini no "
            "los reconoce.\n"
            "  • Sé ESPECÍFICO con lighting, materials y composition — "
            "Gemini los respeta literalmente.\n"
            "  • Para editing: combina '[Edit Instructions]' con '[Keep "
            "X, only change Y]' para preservar identidad.\n"
            "  • El bloque [Edit Instructions] SOLO va si la idea es de "
            "edición. Si la idea es text-to-image puro, OMÍTELO.\n"
            "  • El bloque [Output] DEBE ser 1 sola frase corta (≤15 "
            "palabras). NO detalles de lens/film/ISO ahí — esos van "
            "en [Style] o [Composition].\n"
        )
        if rasgos_combinados:
            extra += (
                f"\n🎭 RASGOS VISUALES DEL/LOS LORA(S) — INCLÚYELOS "
                f"EXPLÍCITAMENTE en [Subject]:\n"
                f"  {rasgos_combinados}\n"
                f"  • Adáptalos al contexto sin contradecir la escena.\n"
                f"  • Refuerzan los pesos del LoRA cuando el output se "
                f"abre en SeaArt con LoRA activo.\n"
            )

        # Hint de estilo forzado por el usuario (toggle "Estilo")
        if estilo_nb != "Auto":
            estilo_map_nb = {
                "Photoreal": (
                    "📷 FOTORREALISMO. [Style] DEBE pedir: photorealistic, "
                    "natural skin texture, real photography, no AI shine. "
                    "Especifica lens (50mm/85mm) y film stock (Portra 400, "
                    "Cinestill, Kodak Gold). [Materials] con detalle alto "
                    "(piel, telas, superficies). [Lighting] natural y "
                    "creíble (golden hour, softbox, backlight). EVITA "
                    "términos de ilustración."
                ),
                "Editorial": (
                    "📰 EDITORIAL / MARKETING. [Style] DEBE pedir: "
                    "editorial photography, fashion magazine aesthetic, "
                    "Vogue/Harper's Bazaar quality, professional lighting, "
                    "clean composition. [Composition] con énfasis en rule "
                    "of thirds y leading lines. [Lighting] sofisticada "
                    "(studio strobes, ring light, accent lights). Ideal "
                    "para banners, ads, social media, e-commerce."
                ),
                "Character-Consistent": (
                    "🎭 CHARACTER CONSISTENCY. La fortaleza principal del "
                    "modelo. [Subject] EXTREMADAMENTE detallado (rostro, "
                    "rasgos únicos, vestimenta característica, age, "
                    "ethnicity) para que pueda mantenerse entre "
                    "ediciones. Pensado para series de imágenes del "
                    "mismo personaje: AI influencer, comic multi-panel, "
                    "branded mascot, photo series. Incluye al final del "
                    "[Subject]: 'consistent character identity for "
                    "multi-image series'."
                ),
                "Artistic": (
                    "🎨 STYLE TRANSFER ARTÍSTICO. [Style] DEBE pedir un "
                    "medium artístico específico: watercolor painting "
                    "with visible brush strokes / oil painting impasto "
                    "texture / pen and ink illustration / gouache "
                    "illustration / cel-shaded cartoon / abstract "
                    "expressionism. [Materials] describe la SUPERFICIE "
                    "del medium (paper texture, canvas grain, paint "
                    "thickness). EVITA pedir photorealistic."
                ),
                "Edit-Focus": (
                    "✏️ EDICIÓN PURA. La idea del usuario es modificar "
                    "una imagen existente. El bloque [Edit Instructions] "
                    "ES OBLIGATORIO con formato 'Replace X with Y' / "
                    "'Make her/him wear Z' / 'Extend canvas upward to "
                    "show W'. Siempre añade 'Keep face identity, keep "
                    "pose, keep color palette, only change [específico]'. "
                    "Los otros bloques describen el RESULTADO esperado "
                    "tras la edición, no la imagen original."
                ),
            }
            hint = estilo_map_nb.get(estilo_nb, "")
            if hint:
                extra += (
                    f"\n🎯 ESTILO FORZADO POR EL USUARIO: {estilo_nb}.\n"
                    f"  {hint}\n"
                    f"  • Orienta TODA la salida a esta categoría.\n"
                    f"  • NO mezcles con otras categorías.\n"
                )
        return extra

    def _inyectar_template(self, motor: str, extra: str) -> str:
        tmpl = get_prompt_template(motor)
        if tmpl:
            extra += "\n📋 PLANTILLA BASE RECOMENDADA:\n"
            extra += f"POSITIVE: {tmpl['positive_base']}\n"
            if tmpl.get("negative_base"):
                extra += f"NEGATIVE: {tmpl['negative_base']}\n"
            extra += "Usa esta plantilla como ESQUELETO. Rellena los campos {{entre llaves}} con los detalles.\n"
        return extra

    def _inyectar_specs_audio(self, system_prompt: str) -> str:
        if not hasattr(self.app, "combo_modelo_audio"):
            return system_prompt
        motor = self.app.combo_modelo_audio.get()
        if es_separador(motor):
            return system_prompt
        specs = get_audio_model_specs(motor)
        if not specs:
            return system_prompt

        instrumental = self.app.switch_instrumental_var.get() if hasattr(self.app, "switch_instrumental_var") else False

        extra = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        extra += f"REGLAS ESPECÍFICAS PARA {motor.upper()}:\n"
        extra += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        extra += f"• Rating del motor: ⭐ {specs['nota']}/5\n"
        extra += f"• Mejor para: {specs['best_for']}\n"
        extra += f"• Duración máxima: {specs['duracion_max_min']} minutos\n"

        if specs.get("usa_tags_estructurales"):
            extra += "• ✅ USA tags estructurales obligatorios: [Intro] [Verse 1] [Chorus] etc.\n"
        else:
            extra += "• ❌ NO usa tags estructurales. Letra directa.\n"

        if specs.get("has_instrumental_toggle"):
            extra += f"• Tiene toggle Vocal/Instrumental. Estado actual: {'INSTRUMENTAL' if instrumental else 'VOCAL'}.\n"
        if instrumental:
            extra += "• ⚠️ MODO INSTRUMENTAL ACTIVO: NO generes letra.\n"

        extra += f"• Ejemplo de estilo: {specs['prompt_ejemplo_estilo']}\n"
        if specs.get("limitaciones"):
            extra += f"• Limitaciones: {specs['limitaciones']}\n"

        # Inyectar preferencias de emoción, voz e idioma del usuario
        emocion = self.app.emocion_var.get() if hasattr(self.app, "emocion_var") else ""
        if emocion and emocion != "— Emoción —":
            extra += f"• 🎭 EMOCIÓN SOLICITADA: {emocion}. Adapta el mood, tempo y tonalidad a esta emoción.\n"
        voz = self.app.voz_var.get() if hasattr(self.app, "voz_var") else ""
        if voz and voz != "— Voz —":
            extra += f"• 🎤 VOZ SOLICITADA: {voz}. Especifica este tipo de voz en el campo de estilo.\n"
        idioma = self.app.idioma_audio_var.get() if hasattr(self.app, "idioma_audio_var") else ""
        if idioma and idioma != "— Idioma —":
            extra += f"• 🌐 IDIOMA DE LA LETRA: {idioma}. Escribe TODA la letra en este idioma.\n"

        extra += REGLAS_APROVECHAR_BUDGET
        return system_prompt + extra

    # Reglas por destino final (Instagram, TikTok, YouTube, concursos, etc.)
    REGLAS_POR_DESTINO = {
        "Instagram": "DESTINO INSTAGRAM: Formato vertical 9:16 o 4:5 preferido. Visualmente impactante desde el primer segundo. Colores vibrantes, composición centrada, estilo editorial/lifestyle.",
        "TikTok": "DESTINO TIKTOK: Formato vertical 9:16 obligatorio. Gancho visual inmediato, energía alta, movimiento dinámico. Estilo trending, juvenil, llamativo.",
        "YouTube": "DESTINO YOUTUBE: Formato horizontal 16:9. Composición cinematográfica, thumbnail-friendly (sujeto claro, contraste alto). Calidad profesional.",
        "YouTube Shorts": "DESTINO YOUTUBE SHORTS: Formato vertical 9:16. Similar a TikTok: gancho rápido, movimiento, energía. Corto e impactante.",
        "Twitter / X": "DESTINO TWITTER/X: Formato 16:9 o 1:1. Imagen que destaque en el feed. Alto contraste, composición limpia, mensaje visual claro.",
        "Anthum (concurso)": "DESTINO CONCURSO ANTHUM: Formato 9:16 vertical. PRIORIDADES DE UN JUEZ DE CONCURSO: 1) ORIGINALIDAD — concepto único que nadie haya visto, evita clichés. 2) CALIDAD TÉCNICA — composición de galería, iluminación de estudio fotográfico. 3) IMPACTO EMOCIONAL — la imagen debe provocar una reacción inmediata. 4) COHERENCIA VISUAL — todos los elementos deben encajar perfectamente. 5) DETALLE — texturas, materiales, reflejos ultra-detallados. NO hagas: paisajes genéricos, retratos simples, escenas cliché. SÍ haz: conceptos surrealistas, composiciones inusuales, mezcla de estilos inesperada.",
        "Freepik community": "DESTINO FREEPIK: Imagen versátil para stock. Composición limpia con espacio para texto. Colores equilibrados, uso comercial, sin marcas.",
        "Reddit": "DESTINO REDDIT: Calidad técnica alta, detalle extremo. La comunidad valora originalidad y ejecución impecable.",
        "LinkedIn": "DESTINO LINKEDIN: Profesional y corporativo. Composición limpia, tonos sobrios, estilo editorial de negocios. Formato 1:1 o 16:9.",
        "Web / Blog": "DESTINO WEB/BLOG: Formato horizontal 16:9 preferido. Imagen hero/banner. Espacio para overlay de texto. Composición equilibrada.",
        "Cliente": "DESTINO CLIENTE: Máxima calidad técnica y profesionalismo. Composición versátil. Adaptable a múltiples usos.",
    }

    def _inyectar_destino(self, system_prompt: str) -> str:
        dest = self.app.destino_var.get() if hasattr(self.app, "destino_var") else ""
        if not dest or dest == "— Personal —":
            return system_prompt

        regla = self.REGLAS_POR_DESTINO.get(dest, "")
        if regla:
            return system_prompt + f"\n\n📢 {regla}\n"
        return system_prompt

    def construir_modelo_info(self) -> str:
        # Cacheo simple: si no cambió la config, devolver cache
        clave_cache = (
            self.app.modo_var.get(),
            self.app.footer.modelo_imagen_valido() if self.app.modo_var.get() == "imagen" else "",
            self.app.footer.modelo_video_valido() if self.app.modo_var.get() == "video" else "",
            self.app.combo_modelo_audio.get() if self.app.modo_var.get() == "audio" and hasattr(self.app, "combo_modelo_audio") else "",
            self.app.footer.ratio_actual(),
            self.app.footer.personaje_activo(),
            self.app.footer.lora_activo(),
            self.app.destino_var.get(),
        )

        # Si no ha cambiado, devolver cache
        if hasattr(self, "_cache_modelo_info") and getattr(self, "_cache_modelo_clave", None) == clave_cache:
            return self._cache_modelo_info

        info = ""
        modo = self.app.modo_var.get()
        if modo == "video":
            info = f" Motor: {self.app.footer.modelo_video_valido()}. Duración: {self.app.duracion_var.get()}."
        elif modo == "audio":
            motor_a = self.app.combo_modelo_audio.get() if hasattr(self.app, "combo_modelo_audio") else ""
            if motor_a and not es_separador(motor_a):
                info = f" Motor audio: {motor_a}."
        else:
            m = self.app.footer.modelo_imagen_valido()
            if m:
                info = f" Modelo: {m}."

        ratio = self.app.footer.ratio_actual()
        if ratio:
            info += f" Ratio: {ratio}."
        pers = self.app.footer.personaje_activo()
        if pers:
            info += f" Personaje: {pers}."
        # Multi-LoRA: combinar primario + extras del modal
        try:
            triggers = self.app.footer.triggers_loras_activos() or []
        except Exception:
            triggers = []
            tp = self.app.footer.lora_activo()
            if tp:
                triggers = [tp]
        if triggers:
            if len(triggers) == 1:
                triggers_str = f"`{triggers[0]}`"
                plural_nota = ""
            else:
                triggers_str = ", ".join(f"`{t}`" for t in triggers)
                plural_nota = (
                    f" Son {len(triggers)} triggers de LoRAs distintos — "
                    f"inclúyelos TODOS, no omitas ninguno."
                )
            info += (
                f"\n🔗 LORA(S) ACTIVO(S) — TRIGGER WORDS OBLIGATORIOS: "
                f"{triggers_str}. Inclúyelos LITERALMENTE UNA SOLA VEZ "
                f"cada uno en el POSITIVE PROMPT. NO los traduzcas ni "
                f"modifiques. NO los repitas en varias secciones.{plural_nota}"
            )
        dest = self.app.destino_var.get()
        if dest and dest != "— Personal —":
            info += f" Destino: {dest}."

        # Audio: añadir emoción, voz, idioma si están seleccionados
        if modo == "audio":
            em = self.app.emocion_var.get() if hasattr(self.app, "emocion_var") else ""
            if em and em != "— Emoción —":
                info += f" Emoción: {em}."
            vz = self.app.voz_var.get() if hasattr(self.app, "voz_var") else ""
            if vz and vz != "— Voz —":
                info += f" Voz: {vz}."
            id_a = self.app.idioma_audio_var.get() if hasattr(self.app, "idioma_audio_var") else ""
            if id_a and id_a != "— Idioma —":
                info += f" Idioma letra: {id_a}."

        # Guardar en cache
        self._cache_modelo_info = info
        self._cache_modelo_clave = clave_cache
        return info
