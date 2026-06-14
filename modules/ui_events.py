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


class UiEventsService:
    """8 event handlers de cambio en combos del header (modo, plataforma,
    motor video/audio, modelo imagen, etc.).

    A1 fase 2 (sesión 14): servicio aislado con app por composición.
    """

    def __init__(self, app):
        self.app = app

    def _on_modo_cambio(self) -> None:
        """Cambia la UI según modo (imagen/video/audio). No opera si Focus está activo."""
        if getattr(self.app, '_modo_focus_activo', False):
            return
        modo = self.app.modo_var.get()
        try: self.app._sesion_log(f"🎛 Cambió modo → {modo.upper()}")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        self.app.lbl_img_model_info.pack_forget()

        try:
            if hasattr(self.app, 'txt_salida') and self.app.txt_salida.get("1.0", "end").strip():
                self.app.dialogs.actualizar_salida("")
            self.app.reiniciar_memoria()
            if getattr(self.app, '_anclaje_visual', None) and modo != "imagen":
                self.app._anclaje_visual = None
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        if hasattr(self.app, '_seg_modo'):
            mapa_inv = {"imagen": "Imagen", "video": "Vídeo", "audio": "Audio"}
            try: self.app._seg_modo.set(mapa_inv.get(modo, "Imagen"))
            except: pass

        if modo == "video":
            self.app.combo_plataforma.configure(values=PLATAFORMAS_VIDEO_LISTA)
            self.app.plataforma_var.set("SeaArt Video")

            self.app._safe_pack(self.app.frame_video, pady=3, padx=20, fill="x", before=self.app._tabview_container)
            if hasattr(self.app, 'frame_audio'): self.app.frame_audio.pack_forget()
            self.app.frame_modelo_imagen.pack_forget()
            self.app.frame_destino.pack_forget()

            self.app.switch_nsfw.pack(side="right", padx=20)
            self.app.btn_vision.configure(text="👁 Analizar", state="normal")
            self.app.btn_img_prompt.configure(text="🎯 Img→Prompt", state="normal")
            self.app.footer._construir_checkboxes(ESTILOS_VIDEO)
            self._actualizar_motores_video()

        elif modo == "audio":
            self.app.combo_plataforma.configure(values=PLATAFORMAS_AUDIO_LISTA)
            self.app.plataforma_var.set("Suno")

            self.app._safe_pack(self.app.frame_audio, pady=3, padx=20, fill="x", before=self.app._tabview_container)
            self.app.frame_video.pack_forget()
            self.app.frame_modelo_imagen.pack_forget()
            self.app.frame_destino.pack_forget()

            self.app.switch_nsfw.pack_forget()
            self.app.btn_vision.configure(text="👁 (no aplica)", state="disabled")
            self.app.btn_img_prompt.configure(text="🎯 (no aplica)", state="disabled")
            self.app.footer._construir_checkboxes(ESTILOS_AUDIO)
            self._on_motor_audio_cambio()

        else:
            self.app.combo_plataforma.configure(values=PLATAFORMAS_IMAGEN_LISTA)
            self.app.plataforma_var.set("SeaArt / Tensor.Art")

            self.app.frame_video.pack_forget()
            if hasattr(self.app, 'frame_audio'): self.app.frame_audio.pack_forget()
            self.app._safe_pack(self.app.frame_modelo_imagen, pady=3, padx=20, fill="x", before=self.app._tabview_container)
            self.app.frame_destino.pack_forget()

            self.app.switch_nsfw.pack(side="right", padx=20)
            self.app.btn_vision.configure(text="👁 Analizar", state="normal")
            self.app.btn_img_prompt.configure(text="🎯 Img→Prompt", state="normal")
            self.app.combo_ratio.set("1:1")
            self.app.ratio_var.set("1:1")
            self.app.footer._construir_checkboxes(ESTILOS_IMAGEN)
            self._on_modelo_imagen_cambio()

        try:
            if hasattr(self.app, 'btn_story'):
                if modo == "imagen":
                    self.app.btn_story.configure(state="normal", fg_color="#be185d",
                                              text="🎞 Story")
                else:
                    self.app.btn_story.configure(state="disabled", fg_color="#3a3a3a",
                                              text="🎞 Story")
            if hasattr(self.app, 'btn_board'):
                if modo == "video":
                    self.app.btn_board.configure(state="normal", fg_color="#be185d",
                                              text="📽 Board")
                else:
                    self.app.btn_board.configure(state="disabled", fg_color="#3a3a3a",
                                              text="📽 Board")
        except Exception as _e:
            logger.debug(f"[silent on_modo_cambio btns] {_e}")

        self._on_plataforma_cambio()
        self.app._ocultar_ideas()
        self.app.reiniciar_memoria()

    def _on_plataforma_cambio(self, valor: str | None = None) -> None:
        modo = self.app.modo_var.get()
        plat = self.app.plataforma_var.get()
        try: self.app._sesion_log(f"🌐 Cambió plataforma → {plat}")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        if modo == "audio":
            motores = MOTORES_AUDIO.get(plat, [])
            default = MOTOR_DEFAULT.get(plat, "")
            if motores:
                self.app.combo_modelo_audio.configure(values=motores)
                self.app.combo_modelo_audio.set(default if default else motores[0])
            self._on_motor_audio_cambio()
            self.app._packear_negative_y_imgref()
            self.app.reiniciar_memoria()
            return

        if modo == "video":
            self._actualizar_motores_video()
            self.app._packear_negative_y_imgref()
            self.app.reiniciar_memoria()
            return

        plat_con_modelos = tuple(MODELOS_POR_PLATAFORMA_IMAGEN.keys())
        if plat in plat_con_modelos:
            modelos_de_plat = MODELOS_POR_PLATAFORMA_IMAGEN.get(plat, MODELOS_IMAGEN_FLAT)
            self.app.combo_modelo_imagen.configure(values=modelos_de_plat)
            actual = self.app.combo_modelo_imagen.get()
            if actual not in modelos_de_plat or actual.startswith("──"):
                primer_modelo = next((m for m in modelos_de_plat if not m.startswith("──")), "")
                if primer_modelo:
                    self.app.combo_modelo_imagen.set(primer_modelo)

            self.app._safe_pack(self.app.frame_modelo_imagen, pady=3, padx=20, fill="x", before=self.app._tabview_container)
            self._on_modelo_imagen_cambio()
        else:
            self.app.frame_modelo_imagen.pack_forget()
            self.app.lbl_img_model_info.pack_forget()

        self.app._packear_negative_y_imgref()

        natural = self.app.is_natural_mode()
        if natural: self.app.dialogs.set_estado(f"🌐 {self.app.plataforma_var.get()} — prompts descriptivos", "#3498db")
        else: self.app.dialogs.set_estado(f"🎯 {self.app.plataforma_var.get()} — tags + pesos + negatives", "#3498db")
        self.app.reiniciar_memoria()

    def _actualizar_motores_video(self) -> None:
        plat = self.app.plataforma_var.get()
        motores = MOTORES_VIDEO.get(plat, [])
        default = MOTOR_DEFAULT.get(plat, "")

        if motores:
            self.app.combo_modelo_video.configure(values=motores)
            self.app.combo_modelo_video.set(default if default else motores[0])
        else:
            self.app.combo_modelo_video.set(plat)
            self.app.combo_modelo_video.configure(values=[plat])
        self._on_motor_cambio(self.app.combo_modelo_video.get())

    def _on_motor_cambio(self, motor_name: str | None = None) -> None:
        if not motor_name: motor_name = self.app.combo_modelo_video.get()
        try: self.app._sesion_log(f"🎬 Cambió modelo vídeo → {motor_name}")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        specs = get_model_specs(motor_name)

        if specs:
            self.app.combo_ratio_v.configure(values=specs["ratios"])
            if self.app.ratio_var.get() not in specs["ratios"]: self.app.ratio_var.set(specs["ratios"][0])
            self.app.lbl_img_model_info.configure(text=f"⭐ {specs['nota']} | 🎬 {specs['best_for']}", text_color="#8bb4d4")
            self.app._safe_pack(self.app.lbl_img_model_info, fill="x", padx=30, pady=(0, 2), before=self.app._tabview_container)
            self.app.dialogs.set_estado(f"🎬 {motor_name}", "#3498db")

            try:
                if hasattr(self.app, '_tooltip_motor_video') and self.app._tooltip_motor_video is not None:
                    try:
                        self.app._tooltip_motor_video.hide()
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

                self.app._tooltip_motor_video = CTkToolTip(self.app.combo_modelo_video, delay=0.6, message=tip_rico,
                                                      wraplength=450, justify="left")
            except Exception as e:
                logger.debug(f"Tooltip video error: {e}")
        else:
            self.app.combo_ratio_v.configure(values=RATIOS_VIDEO)
            self.app.lbl_img_model_info.pack_forget()
            self.app.dialogs.set_estado(f"🎬 {motor_name}")

        self.app._packear_negative_y_imgref()
        self.app.reiniciar_memoria()
        try: self.app.dialogs._actualizar_tokens()
        except: pass

    def _on_modelo_imagen_cambio(self, modelo_name: str | None = None) -> None:
        if not modelo_name: modelo_name = self.app.combo_modelo_imagen.get()
        try: self.app._sesion_log(f"🎨 Cambió modelo imagen → {modelo_name}")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        try: self.app.footer._actualizar_lora_trigger_visible()
        except Exception as e:
            logger.debug(f"[silent] {e}")
        try: self.app.dialogs._actualizar_tokens()
        except Exception as e:
            logger.debug(f"[silent] {e}")
        # Mostrar/ocultar combo "Estilo" según familia del modelo.
        # Repoblar valores y resetear si la familia cambia.
        try:
            from config import ESTILOS_POR_FAMILIA, detectar_familia
            familia = detectar_familia(modelo_name)
            estilos = ESTILOS_POR_FAMILIA.get(familia, []) if familia else []
            if hasattr(self.app, "frame_familia_estilo"):
                if estilos:
                    # Repoblar el combo con los estilos de la familia
                    try:
                        self.app.combo_familia_estilo.configure(values=estilos)
                    except Exception as _e:
                        logger.debug(f"[silent estilo values] {_e}")
                    # Si el valor actual no encaja en la nueva familia,
                    # reset a "Auto"
                    try:
                        if self.app.familia_estilo_var.get() not in estilos:
                            self.app.familia_estilo_var.set("Auto")
                    except Exception as _e:
                        logger.debug(f"[silent estilo reset] {_e}")
                    # Mostrar el combo si no está visible
                    if not self.app.frame_familia_estilo.winfo_ismapped():
                        self.app.frame_familia_estilo.pack(
                            side="left", padx=(4, 8),
                            after=self.app.combo_modelo_imagen.master,
                        )
                else:
                    # Familia sin estilos definidos → ocultar
                    if self.app.frame_familia_estilo.winfo_ismapped():
                        self.app.frame_familia_estilo.pack_forget()
        except Exception as _e:
            logger.debug(f"[silent familia_estilo toggle] {_e}")
        if self.app.modo_var.get() != "imagen":
            self.app.lbl_img_model_info.pack_forget()
            return

        if es_separador(modelo_name):
            self.app.lbl_img_model_info.pack_forget()
            return

        specs = get_image_model_specs(modelo_name)
        if specs:
            self.app.combo_ratio.configure(values=specs["ratios"])
            if self.app.ratio_var.get() not in specs["ratios"]: self.app.ratio_var.set(specs["ratios"][0])

            try:
                if hasattr(self.app, '_tooltip_modelo_actual') and self.app._tooltip_modelo_actual is not None:
                    try:
                        self.app._tooltip_modelo_actual.hide()
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")
                tip_rico = (
                    f"⭐ Nota: {specs.get('nota', '?')}/5\n"
                    f"📝 Max: {specs.get('max_chars', '?')} chars\n\n"
                    f"🎯 Ideal para:\n{specs.get('best_for', '')[:300]}\n\n"
                    f"📐 Fórmula:\n{specs.get('prompt_formula', '?')[:200]}\n\n"
                    f"💡 Ejemplo:\n{specs.get('prompt_ejemplo', '?')[:250]}"
                )
                self.app._tooltip_modelo_actual = CTkToolTip(self.app.combo_modelo_imagen, delay=0.6, message=tip_rico,
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
            self.app.lbl_img_model_info.configure(
                text=f"⭐ {specs.get('nota') or 's/n'}  ·  📝 {specs['max_chars']} chars  ·  {badges_str}  —  {specs['best_for']}",
                text_color="#8bb4d4")
            self.app._safe_pack(self.app.lbl_img_model_info, fill="x", padx=30, pady=(0, 2), before=self.app._tabview_container)

            try:
                self.app.analysis.mostrar_consejo_contextual(modelo_name, specs)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        else:
            self.app.lbl_img_model_info.pack_forget()
            self.app.combo_ratio.configure(values=RATIOS_IMAGEN)

        self.app._packear_negative_y_imgref()
        self.app.reiniciar_memoria()
        try: self.app.dialogs._actualizar_tokens()
        except: pass
        try:
            self.app.after(500, lambda: self.app.footer._recomendar_loras_para_modelo(modelo_name))
        except Exception as e:
            logger.debug(f"[silent] {e}")

    def _on_motor_audio_cambio(self, motor_name: str | None = None) -> None:
        if not motor_name: motor_name = self.app.combo_modelo_audio.get()
        try: self.app._sesion_log(f"🎵 Cambió modelo audio → {motor_name}")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        if es_separador(motor_name):
            self.app.lbl_img_model_info.pack_forget()
            return

        specs = get_audio_model_specs(motor_name)
        if specs:
            self.app.lbl_img_model_info.configure(text=f"⭐ {specs['nota']} | ⏱ {specs['duracion_max_min']} min — {specs['best_for']}", text_color="#8bb4d4")
            self.app._safe_pack(self.app.lbl_img_model_info, fill="x", padx=30, pady=(0, 2), before=self.app._tabview_container)
            self.app.dialogs.set_estado(f"🎵 {motor_name}", "#9b59b6")
        else:
            self.app.lbl_img_model_info.pack_forget()
        self.app.reiniciar_memoria()

    def _on_audio_filtro_cambio(self, valor: str | None = None) -> None:
        """Feedback visual cuando cambian emoción, voz o idioma en audio."""
        partes = []
        em = self.app.emocion_var.get() if hasattr(self.app, 'emocion_var') else ""
        if em and em != "— Emoción —": partes.append(f"🎭 {em}")
        vz = self.app.voz_var.get() if hasattr(self.app, 'voz_var') else ""
        if vz and vz != "— Voz —": partes.append(f"🎤 {vz}")
        id_a = self.app.idioma_audio_var.get() if hasattr(self.app, 'idioma_audio_var') else ""
        if id_a and id_a != "— Idioma —": partes.append(f"🌐 {id_a}")

        if partes:
            self.app.dialogs.set_estado(f"🎵 Filtros audio: {' · '.join(partes)}", "#9b59b6")
        else:
            self.app.dialogs.set_estado("🎵 Sin filtros de audio adicionales")
        self.app.reiniciar_memoria()

    def _on_brief_cambio(self) -> None:
        if self.app.brief_var.get():
            self.app.dialogs.set_estado("⚡ Modo Brief ACTIVO — prompts optimizados para anuncios", "#f39c12")
        else:
            self.app.dialogs.set_estado("Modo Brief desactivado — prompts artísticos libres")
        self.app.reiniciar_memoria()
