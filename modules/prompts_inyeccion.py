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
        if specs.get("is_natural"):
            extra += "• TIPO: lenguaje natural descriptivo. NO uses tags sueltos separados por comas.\n"
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
            self.app.modelo_imagen_valido() if self.app.modo_var.get() == "imagen" else "",
            self.app.modelo_video_valido() if self.app.modo_var.get() == "video" else "",
            self.app.combo_modelo_audio.get() if self.app.modo_var.get() == "audio" and hasattr(self.app, "combo_modelo_audio") else "",
            self.app.ratio_actual(),
            self.app.personaje_activo(),
            self.app.lora_activo(),
            self.app.destino_var.get(),
        )

        # Si no ha cambiado, devolver cache
        if hasattr(self, "_cache_modelo_info") and getattr(self, "_cache_modelo_clave", None) == clave_cache:
            return self._cache_modelo_info

        info = ""
        modo = self.app.modo_var.get()
        if modo == "video":
            info = f" Motor: {self.app.modelo_video_valido()}. Duración: {self.app.duracion_var.get()}."
        elif modo == "audio":
            motor_a = self.app.combo_modelo_audio.get() if hasattr(self.app, "combo_modelo_audio") else ""
            if motor_a and not es_separador(motor_a):
                info = f" Motor audio: {motor_a}."
        else:
            m = self.app.modelo_imagen_valido()
            if m:
                info = f" Modelo: {m}."

        ratio = self.app.ratio_actual()
        if ratio:
            info += f" Ratio: {ratio}."
        pers = self.app.personaje_activo()
        if pers:
            info += f" Personaje: {pers}."
        lora = self.app.lora_activo()
        if lora:
            info += f" LoRA: {lora}."
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
