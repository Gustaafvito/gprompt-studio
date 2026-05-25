"""Event handlers de la UI principal (cambio de modo, plataforma, motor, modelo).

Extraído de modules/core.py para reducir tamaño y agrupar responsabilidades.

Contiene los callbacks que reaccionan a cambios en los combos/segmented
buttons del panel superior:

  • _on_modo_cambio          — imagen / vídeo / audio.
  • _on_plataforma_cambio    — recalcula motores disponibles.
  • _actualizar_motores_video — refresca el combo de motor según plataforma.
  • _on_motor_cambio          — motor de vídeo seleccionado (tooltip + ratios).
  • _on_modelo_imagen_cambio  — modelo de imagen seleccionado (tooltip + badges).
  • _on_motor_audio_cambio    — motor de audio seleccionado.
  • _on_audio_filtro_cambio   — emoción / voz / idioma de audio.
  • _on_brief_cambio          — toggle modo Brief.
"""
import logging

import customtkinter as ctk

try:
    from CTkToolTip import CTkToolTip
except ImportError:
    class CTkToolTip:
        def __init__(self, *args, **kwargs): pass
        def hide(self): pass

from config import (
    ESTILOS_AUDIO,
    ESTILOS_IMAGEN,
    ESTILOS_VIDEO,
    MODELOS_IMAGEN_FLAT,
    MODELOS_POR_PLATAFORMA_IMAGEN,
    MOTOR_DEFAULT,
    MOTORES_AUDIO,
    MOTORES_VIDEO,
    PLATAFORMAS_AUDIO_LISTA,
    PLATAFORMAS_IMAGEN_LISTA,
    PLATAFORMAS_VIDEO_LISTA,
    RATIOS_IMAGEN,
    RATIOS_VIDEO,
    es_separador,
    get_audio_model_specs,
    get_image_model_specs,
    get_model_specs,
)

logger = logging.getLogger("gprompt")


class UiEventsMixin:
    def _on_modo_cambio(self):
        """Cambia la UI según modo (imagen/video/audio). No opera si Focus está activo."""
        if getattr(self, '_modo_focus_activo', False):
            return
        modo = self.modo_var.get()
        try: self._sesion_log(f"🎛 Cambió modo → {modo.upper()}")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        self.lbl_img_model_info.pack_forget()

        try:
            if hasattr(self, 'txt_salida') and self.txt_salida.get("1.0", "end").strip():
                self.actualizar_salida("")
            self.reiniciar_memoria()
            if getattr(self, '_anclaje_visual', None) and modo != "imagen":
                self._anclaje_visual = None
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        if hasattr(self, '_seg_modo'):
            mapa_inv = {"imagen": "Imagen", "video": "Vídeo", "audio": "Audio"}
            try: self._seg_modo.set(mapa_inv.get(modo, "Imagen"))
            except: pass

        if modo == "video":
            self.combo_plataforma.configure(values=PLATAFORMAS_VIDEO_LISTA)
            self.plataforma_var.set("SeaArt Video")

            self._safe_pack(self.frame_video, pady=3, padx=20, fill="x", before=self._tabview_container)
            if hasattr(self, 'frame_audio'): self.frame_audio.pack_forget()
            self.frame_modelo_imagen.pack_forget()
            self.frame_destino.pack_forget()

            self.switch_nsfw.pack(side="right", padx=20)
            self.btn_vision.configure(text="👁 Analizar", state="normal")
            self.btn_img_prompt.configure(text="🎯 Img→Prompt", state="normal")
            self._construir_checkboxes(ESTILOS_VIDEO)
            self._actualizar_motores_video()

        elif modo == "audio":
            self.combo_plataforma.configure(values=PLATAFORMAS_AUDIO_LISTA)
            self.plataforma_var.set("Suno")

            self._safe_pack(self.frame_audio, pady=3, padx=20, fill="x", before=self._tabview_container)
            self.frame_video.pack_forget()
            self.frame_modelo_imagen.pack_forget()
            self.frame_destino.pack_forget()

            self.switch_nsfw.pack_forget()
            self.btn_vision.configure(text="👁 (no aplica)", state="disabled")
            self.btn_img_prompt.configure(text="🎯 (no aplica)", state="disabled")
            self._construir_checkboxes(ESTILOS_AUDIO)
            self._on_motor_audio_cambio()

        else:
            self.combo_plataforma.configure(values=PLATAFORMAS_IMAGEN_LISTA)
            self.plataforma_var.set("SeaArt / Tensor.Art")

            self.frame_video.pack_forget()
            if hasattr(self, 'frame_audio'): self.frame_audio.pack_forget()
            self._safe_pack(self.frame_modelo_imagen, pady=3, padx=20, fill="x", before=self._tabview_container)
            self.frame_destino.pack_forget()

            self.switch_nsfw.pack(side="right", padx=20)
            self.btn_vision.configure(text="👁 Analizar", state="normal")
            self.btn_img_prompt.configure(text="🎯 Img→Prompt", state="normal")
            self.combo_ratio.set("1:1")
            self.ratio_var.set("1:1")
            self._construir_checkboxes(ESTILOS_IMAGEN)
            self._on_modelo_imagen_cambio()

        try:
            if hasattr(self, 'btn_story'):
                if modo == "imagen":
                    self.btn_story.configure(state="normal", fg_color="#be185d",
                                              text="🎞 Story")
                else:
                    self.btn_story.configure(state="disabled", fg_color="#3a3a3a",
                                              text="🎞 Story")
            if hasattr(self, 'btn_board'):
                if modo == "video":
                    self.btn_board.configure(state="normal", fg_color="#be185d",
                                              text="📽 Board")
                else:
                    self.btn_board.configure(state="disabled", fg_color="#3a3a3a",
                                              text="📽 Board")
        except Exception as _e:
            logger.debug(f"[silent on_modo_cambio btns] {_e}")

        self._on_plataforma_cambio()
        self._ocultar_ideas()
        self.reiniciar_memoria()

    def _on_plataforma_cambio(self, valor=None):
        modo = self.modo_var.get()
        plat = self.plataforma_var.get()
        try: self._sesion_log(f"🌐 Cambió plataforma → {plat}")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        if modo == "audio":
            motores = MOTORES_AUDIO.get(plat, [])
            default = MOTOR_DEFAULT.get(plat, "")
            if motores:
                self.combo_modelo_audio.configure(values=motores)
                self.combo_modelo_audio.set(default if default else motores[0])
            self._on_motor_audio_cambio()
            self._packear_negative_y_imgref()
            self.reiniciar_memoria()
            return

        if modo == "video":
            self._actualizar_motores_video()
            self._packear_negative_y_imgref()
            self.reiniciar_memoria()
            return

        plat_con_modelos = tuple(MODELOS_POR_PLATAFORMA_IMAGEN.keys())
        if plat in plat_con_modelos:
            modelos_de_plat = MODELOS_POR_PLATAFORMA_IMAGEN.get(plat, MODELOS_IMAGEN_FLAT)
            self.combo_modelo_imagen.configure(values=modelos_de_plat)
            actual = self.combo_modelo_imagen.get()
            if actual not in modelos_de_plat or actual.startswith("──"):
                primer_modelo = next((m for m in modelos_de_plat if not m.startswith("──")), "")
                if primer_modelo:
                    self.combo_modelo_imagen.set(primer_modelo)

            self._safe_pack(self.frame_modelo_imagen, pady=3, padx=20, fill="x", before=self._tabview_container)
            self._on_modelo_imagen_cambio()
        else:
            self.frame_modelo_imagen.pack_forget()
            self.lbl_img_model_info.pack_forget()

        self._packear_negative_y_imgref()

        natural = self.is_natural_mode()
        if natural: self.set_estado(f"🌐 {self.plataforma_var.get()} — prompts descriptivos", "#3498db")
        else: self.set_estado(f"🎯 {self.plataforma_var.get()} — tags + pesos + negatives", "#3498db")
        self.reiniciar_memoria()

    def _actualizar_motores_video(self):
        plat = self.plataforma_var.get()
        motores = MOTORES_VIDEO.get(plat, [])
        default = MOTOR_DEFAULT.get(plat, "")

        if motores:
            self.combo_modelo_video.configure(values=motores)
            self.combo_modelo_video.set(default if default else motores[0])
        else:
            self.combo_modelo_video.set(plat)
            self.combo_modelo_video.configure(values=[plat])
        self._on_motor_cambio(self.combo_modelo_video.get())

    def _on_motor_cambio(self, motor_name=None):
        if not motor_name: motor_name = self.combo_modelo_video.get()
        try: self._sesion_log(f"🎬 Cambió modelo vídeo → {motor_name}")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        specs = get_model_specs(motor_name)

        if specs:
            self.combo_ratio_v.configure(values=specs["ratios"])
            if self.ratio_var.get() not in specs["ratios"]: self.ratio_var.set(specs["ratios"][0])
            self.lbl_img_model_info.configure(text=f"⭐ {specs['nota']} | 🎬 {specs['best_for']}", text_color="#8bb4d4")
            self._safe_pack(self.lbl_img_model_info, fill="x", padx=30, pady=(0, 2), before=self._tabview_container)
            self.set_estado(f"🎬 {motor_name}", "#3498db")

            try:
                if hasattr(self, '_tooltip_motor_video') and self._tooltip_motor_video is not None:
                    try:
                        self._tooltip_motor_video.hide()
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")
                tip_rico = (
                    f"⭐ Nota: {specs.get('nota', '?')}/5\n"
                    f"📝 Max: {specs.get('max_chars', '?')} chars\n"
                    f"⏱ Duraciones: {', '.join(specs.get('duraciones', []))}\n"
                    f"📐 Ratios: {', '.join(specs.get('ratios', []))}\n\n"
                    f"🎯 Ideal para:\n{specs.get('best_for', '')[:300]}\n\n"
                    f"📐 Fórmula:\n{specs.get('prompt_formula', '?')[:200]}\n\n"
                    f"💡 Ejemplo:\n{specs.get('prompt_ejemplo', '?')[:250]}"
                )

                tips = specs.get('prompt_tips', [])
                if tips:
                    tip_rico += "\n\n💡 PROMPT TIPS:"
                    for i, tip in enumerate(tips[:5], 1):
                        if len(tip) <= 80:
                            tip_rico += f"\n  {i}. {tip}"
                        else:
                            tip_rico += f"\n  {i}. {tip[:77]}..."

                if specs.get('has_audio'):
                    tip_rico += f"\n\n🔊 Audio: {specs.get('audio_desc', 'Sí')}"

                self._tooltip_motor_video = CTkToolTip(self.combo_modelo_video, delay=0.6, message=tip_rico,
                                                      wraplength=450, justify="left")
            except Exception as e:
                logger.debug(f"Tooltip video error: {e}")
        else:
            self.combo_ratio_v.configure(values=RATIOS_VIDEO)
            self.lbl_img_model_info.pack_forget()
            self.set_estado(f"🎬 {motor_name}")

        self._packear_negative_y_imgref()
        self.reiniciar_memoria()
        try: self._actualizar_tokens()
        except: pass

    def _on_modelo_imagen_cambio(self, modelo_name=None):
        if not modelo_name: modelo_name = self.combo_modelo_imagen.get()
        try: self._sesion_log(f"🎨 Cambió modelo imagen → {modelo_name}")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        try: self._actualizar_lora_trigger_visible()
        except Exception as e:
            logger.debug(f"[silent] {e}")
        try: self._actualizar_tokens()
        except Exception as e:
            logger.debug(f"[silent] {e}")
        if self.modo_var.get() != "imagen":
            self.lbl_img_model_info.pack_forget()
            return

        if es_separador(modelo_name):
            self.lbl_img_model_info.pack_forget()
            return

        specs = get_image_model_specs(modelo_name)
        if specs:
            self.combo_ratio.configure(values=specs["ratios"])
            if self.ratio_var.get() not in specs["ratios"]: self.ratio_var.set(specs["ratios"][0])

            try:
                if hasattr(self, '_tooltip_modelo_actual') and self._tooltip_modelo_actual is not None:
                    try:
                        self._tooltip_modelo_actual.hide()
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")
                tip_rico = (
                    f"⭐ Nota: {specs.get('nota', '?')}/5\n"
                    f"📝 Max: {specs.get('max_chars', '?')} chars\n\n"
                    f"🎯 Ideal para:\n{specs.get('best_for', '')[:300]}\n\n"
                    f"📐 Fórmula:\n{specs.get('prompt_formula', '?')[:200]}\n\n"
                    f"💡 Ejemplo:\n{specs.get('prompt_ejemplo', '?')[:250]}"
                )
                self._tooltip_modelo_actual = CTkToolTip(self.combo_modelo_imagen, delay=0.6, message=tip_rico,
                                                          wraplength=400, justify="left")
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            badges = []
            if specs.get("is_natural"):
                badges.append("🌐 Natural")
            elif specs.get("no_weights"):
                badges.append("⚡ Turbo")
            else:
                badges.append("🏷 Tags")
            if specs.get("has_negative"):
                badges.append("🔴 Neg ✓")
            else:
                badges.append("🚫 Sin neg")
            if specs.get("max_imagenes", 0) > 1:
                badges.append(f"🖼×{specs['max_imagenes']}")

            badges_str = "  ·  ".join(badges)
            self.lbl_img_model_info.configure(
                text=f"⭐ {specs['nota']}  ·  📝 {specs['max_chars']} chars  ·  {badges_str}  —  {specs['best_for']}",
                text_color="#8bb4d4")
            self._safe_pack(self.lbl_img_model_info, fill="x", padx=30, pady=(0, 2), before=self._tabview_container)

            try:
                self._mostrar_consejo_contextual(modelo_name, specs)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        else:
            self.lbl_img_model_info.pack_forget()
            self.combo_ratio.configure(values=RATIOS_IMAGEN)

        self._packear_negative_y_imgref()
        self.reiniciar_memoria()
        try: self._actualizar_tokens()
        except: pass
        try:
            self.after(500, lambda: self._recomendar_loras_para_modelo(modelo_name))
        except Exception as e:
            logger.debug(f"[silent] {e}")

    def _on_motor_audio_cambio(self, motor_name=None):
        if not motor_name: motor_name = self.combo_modelo_audio.get()
        try: self._sesion_log(f"🎵 Cambió modelo audio → {motor_name}")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        if es_separador(motor_name):
            self.lbl_img_model_info.pack_forget()
            return

        specs = get_audio_model_specs(motor_name)
        if specs:
            self.lbl_img_model_info.configure(text=f"⭐ {specs['nota']} | ⏱ {specs['duracion_max_min']} min — {specs['best_for']}", text_color="#8bb4d4")
            self._safe_pack(self.lbl_img_model_info, fill="x", padx=30, pady=(0, 2), before=self._tabview_container)
            self.set_estado(f"🎵 {motor_name}", "#9b59b6")
        else:
            self.lbl_img_model_info.pack_forget()
        self.reiniciar_memoria()

    def _on_audio_filtro_cambio(self, valor=None):
        """Feedback visual cuando cambian emoción, voz o idioma en audio."""
        partes = []
        em = self.emocion_var.get() if hasattr(self, 'emocion_var') else ""
        if em and em != "— Emoción —": partes.append(f"🎭 {em}")
        vz = self.voz_var.get() if hasattr(self, 'voz_var') else ""
        if vz and vz != "— Voz —": partes.append(f"🎤 {vz}")
        id_a = self.idioma_audio_var.get() if hasattr(self, 'idioma_audio_var') else ""
        if id_a and id_a != "— Idioma —": partes.append(f"🌐 {id_a}")

        if partes:
            self.set_estado(f"🎵 Filtros audio: {' · '.join(partes)}", "#9b59b6")
        else:
            self.set_estado("🎵 Sin filtros de audio adicionales")
        self.reiniciar_memoria()

    def _on_brief_cambio(self):
        if self.brief_var.get():
            self.set_estado("⚡ Modo Brief ACTIVO — prompts optimizados para anuncios", "#f39c12")
        else:
            self.set_estado("Modo Brief desactivado — prompts artísticos libres")
        self.reiniciar_memoria()
