"""Core Mixin - Workers, Commands, Main Logic, Theme, Focus Mode, etc.

NOTA ARQUITECTÓNICA (sesión 17): CoreMixin es la FOUNDATION definitiva
de ArquitectoApp. A1 fase 2 (sesiones 9-14) migró los otros 20 mixins a
Services aislados, pero CoreMixin permanece en el MRO por diseño:

- Crea widgets directamente sobre `self` (Modo Focus, theme apply).
- Hereda métodos llamados desde TODO el código como si fueran del app:
  reiniciar_memoria, _recortar_si_excede, extraer_positive/negative,
  get_current_model_specs, is_natural_mode, _contexto_loras_personaje.
- Migrarlo a Service requeriría reescribir ~127 call sites externos sin
  beneficio arquitectónico real (la app SÍ necesita un esqueleto base).

Si en el futuro se quiere romper esta foundation, conviene extraer
primero los helpers puros (_parsear_variaciones, _recortar_si_excede,
_extraer_*) a un módulo standalone tipo `prompt_helpers.py`.

v1.0:
- Eliminadas 9 referencias muertas al parámetro modelo_llm en llamadas a
  self.deepseek.generar() / .traducir(). El parámetro ya no se usa porque
  el provider activo se obtiene desde self.clients.get_active_provider().
- Llamada a _actualizar_indicador_proveedor() tras cambio de LLM.
"""
import logging

import pyperclip

from modules.i18n import get_idioma, tr

logger = logging.getLogger("gprompt")
from typing import TYPE_CHECKING

import customtkinter as ctk

import modules.prompt_logic as _pl
from config import (
    get_audio_model_specs,
    get_image_model_specs,
    get_model_specs,
)
from modules.gprompt_window import GPromptWindow
from modules.prompt_helpers import (
    extraer_negative_de_texto as _h_extraer_negative,
)
from modules.prompt_helpers import (
    extraer_pos_de_bloque as _h_extraer_pos_de_bloque,
)
from modules.prompt_helpers import (
    extraer_positive_de_texto as _h_extraer_positive,
)
from modules.prompt_helpers import (
    parsear_variaciones as _h_parsear_variaciones,
)
from modules.prompt_helpers import (
    recortar_si_excede as _h_recortar_si_excede,
)
from modules.theme import apply_theme_colors
from modules.windows import abrir_batch, abrir_batch_variables
from prompts import (
    BRIEF_MODIFIER,
    NEGATIVE_BASE_NSFW,
    NEGATIVE_BASE_SFW,
    NEGATIVE_BASE_VIDEO,
    SYSTEM_AUDIO_SEAART,
    SYSTEM_AUDIO_SUNO,
    SYSTEM_IMAGEN_NSFW,
    SYSTEM_IMAGEN_SFW,
    SYSTEM_NATURAL_NSFW,
    SYSTEM_NATURAL_SFW,
    SYSTEM_NATURAL_VIDEO,
    SYSTEM_NATURAL_VIDEO_NSFW,
    SYSTEM_VIDEO,
    SYSTEM_VIDEO_NSFW,
)
from workers import limpiar_marcadores, log_future_exc

if TYPE_CHECKING:
    pass


class CoreMixin:
    """Mixin containing all core methods: workers, commands, state management."""

    # ON DESTINO CAMBIO

    def _on_destino_cambio(self, valor=None):
        """Auto-ajustar ratio según destino seleccionado y sincronizar todos los combos."""
        dest = self.destino_var.get()
        # Sincronizar todos los combos destino (img/vid/aud)
        for attr in ['combo_destino_img', 'combo_destino_vid', 'combo_destino_aud']:
            if hasattr(self, attr):
                try: getattr(self, attr).set(dest)
                except: pass

        auto_ratios = {
            "Instagram":        "9:16",
            "TikTok":           "9:16",
            "YouTube":          "16:9",
            "YouTube Shorts":   "9:16",
            "Twitter / X":      "16:9",
            "Anthum (concurso)":"9:16",
            "LinkedIn":         "1:1",
            "Web / Blog":       "16:9",
        }
        ratio = auto_ratios.get(dest)
        if ratio:
            self.ratio_var.set(ratio)
            if hasattr(self, 'combo_ratio'):
                self.combo_ratio.set(ratio)
            if hasattr(self, 'combo_ratio_v'):
                self.combo_ratio_v.set(ratio)
            self.set_estado(tr('📐 Destino {0} → Ratio auto: {1}').format(dest, ratio), "#3498db")

        # Modo concurso: activar Brief automáticamente
        if dest == "Anthum (concurso)":
            self.brief_var.set(True)
            self.events._on_brief_cambio()
            self.set_estado(tr("🏆 Modo Concurso Anthum — Brief activado, ratio 9:16, máxima calidad"), "#f39c12")

        self.reiniciar_memoria()

    # MODO FOCUS

    def _cmd_modo_focus(self):
        """Modo Focus: oculta paneles secundarios. Botón flotante para salir."""
        if not hasattr(self, '_modo_focus_activo'):
            self._modo_focus_activo = False
            self._focus_pack_order = []

        if not self._modo_focus_activo:
            # ACTIVAR: ocultar todo excepto entrada, acciones, estado, salida
            ocultar = [
                '_header_frame', '_modo_frame',
                'frame_modelo_imagen', 'frame_video', 'frame_audio',
                'frame_destino', 'tabview',
                'lbl_img_model_info', 'frame_img_ref',
            ]
            self._focus_pack_order = []
            for attr in ocultar:
                widget = getattr(self, attr, None)
                if widget is None:
                    continue
                try:
                    if widget.winfo_ismapped():
                        info = widget.pack_info()
                        self._focus_pack_order.append((attr, dict(info)))
                        widget.pack_forget()
                except Exception as _e:
                    logger.debug(f"[silent] {_e}")
            # Botón flotante para salir
            self._focus_exit_btn = ctk.CTkButton(self, text=tr("✕ Salir de Focus"), width=140, height=28,
                                                  fg_color="#7c3aed", hover_color="#6d28d9",
                                                  font=ctk.CTkFont(size=11, weight="bold"),
                                                  corner_radius=14,
                                                  command=self._cmd_modo_focus)
            self._focus_exit_btn.place(relx=0.5, rely=0.01, anchor="n")

            self._modo_focus_activo = True
            self.set_estado(tr("🎯 Modo Focus ACTIVO — pulsa ✕ para salir"), "#7c3aed")
        else:
            # DESACTIVAR: quitar botón flotante
            if self._focus_exit_btn:
                self._focus_exit_btn.destroy()
                self._focus_exit_btn = None

            # Restaurar widgets respetando el orden original.
            #
            # Fix sesión 15: el código previo usaba pack(after=prev) en
            # cadena, pero como los frames ocultos van TODOS antes de
            # frame_entrada, esto rompía el orden y dejaba un hueco
            # negro arriba (el primer widget iba `before=ancla` y los
            # demás `after=prev` → al final pasaban a estar detrás de
            # frame_entrada en el pack stack, dejando vacío el espacio
            # superior).
            #
            # Estrategia robusta: usar pack(before=frame_entrada) para
            # TODOS los widgets, en orden. Tk respeta el orden de
            # `pack(before=X)` y los apila justo antes de X manteniendo
            # el orden de las llamadas.
            ancla = getattr(self, 'frame_entrada', None)
            for attr, info in self._focus_pack_order:
                widget = getattr(self, attr, None)
                if widget is None:
                    continue
                try:
                    info.pop('in', None)
                    info.pop('before', None)
                    info.pop('after', None)
                    if ancla:
                        widget.pack(before=ancla, **info)
                    else:
                        widget.pack(**info)
                except Exception:
                    try:
                        if ancla:
                            widget.pack(before=ancla, fill="x", padx=16, pady=2)
                        else:
                            widget.pack(fill="x", padx=16, pady=2)
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")
            self._focus_pack_order = []
            self._modo_focus_activo = False
            # Forzar recálculo del layout para que se vea de inmediato
            try:
                self.update_idletasks()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")

            # Repintar colores del tema
            try:
                self._apply_theme_colors()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            self.set_estado(tr("🎯 Modo Focus desactivado"))

    # ON LLM CAMBIO

    def _on_llm_cambio(self, label=None):
        """Cuando el usuario cambia de proveedor LLM en el dropdown."""
        from api_clients import LLM_PROVIDERS

        if label is None:
            label = self.llm_var.get()
        # Mapear label → provider_id
        pid = getattr(self, "_llm_label_to_id", {}).get(label)
        if not pid:
            # Compatibilidad con etiquetas antiguas. Mantener "V3" para
            # usuarios con preferencias guardadas de versiones previas
            # antes de que DeepSeek lanzara V4.
            mapeo_legado = {
                "DeepSeek V3": "deepseek",
                "DeepSeek V4": "deepseek",
                "DeepSeek": "deepseek",
                "Google Gemini": "gemini",
                "OpenAI GPT-4o": "openai",
                "Local (Ollama)": "ollama",
            }
            pid = mapeo_legado.get(label)
        if not pid:
            return
        # Verificar si tiene key configurada
        if hasattr(self.clients, "providers"):
            provider = self.clients.providers.get(pid)
            if not provider or not provider.disponible():
                # Sin key — abrir wizard automáticamente
                info = LLM_PROVIDERS.get(pid, {})
                self.set_estado(tr('⚠️ {0} no tiene API key — abre 🔑 para configurar').format(info.get('name', pid)), "#e67e22")
                self._cmd_configurar_api_keys(provider_focus=pid)
                return
            # Cambiar el provider activo
            self.clients.cambiar_provider(pid)
            info = LLM_PROVIDERS.get(pid, {})
            self.set_estado(tr('🧠 Cerebro: {0}').format(info.get('name', pid)), "#2ecc71")
            try: self.sesion._sesion_log(f"🧠 Cambió cerebro → {pid}")
            except Exception as e:
                logger.debug(f"[silent] {e}")
            try:
                if hasattr(self, "_actualizar_indicador_proveedor"):
                    self._actualizar_indicador_proveedor()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            try:
                if hasattr(self, "_refrescar_indicadores_llm"):
                    self.ui._refrescar_indicadores_llm()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            # Repoblar el selector de modelo con los del proveedor nuevo
            try:
                if hasattr(self, "_refrescar_combo_modelo_llm"):
                    self._refrescar_combo_modelo_llm()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
    # TOGGLE TEMA CLARO/OSCURO

    def _apply_theme_colors(self):
        """Actualiza colores de header, barra de modo, checkboxes y labels
        sin destruir widgets. Incluye checkboxes de estilos (sin esto
        mantenían el color del tema antiguo al cambiar de tema).

        Delega en modules.theme.apply_theme_colors para mantener la lógica
        en un módulo dedicado, preservando la interfaz original."""
        apply_theme_colors(self)
    # EXTRAER POSITIVE / NEGATIVE
    # Nota: _cmd_toggle_tema vive en DialogsMixin — esta clase no la sobrescribe.

    def extraer_positive(self):
        return _h_extraer_positive(limpiar_marcadores(self.txt_salida.get("1.0", "end")))

    def extraer_negative(self):
        return _h_extraer_negative(limpiar_marcadores(self.txt_salida.get("1.0", "end")))

    def _copiar(self, tipo):
        try:
            try: self.sesion._sesion_log(f"📋 Copió: {tipo}")
            except Exception as e:
                logger.debug(f"[silent] {e}")
            tiene_neg = self._debe_mostrar_negatives()
            if tipo == "positivo":
                r = self.extraer_positive()
                if r:
                    pyperclip.copy(r)
                    label = "Prompt" if not tiene_neg else "Prompt Positivo"
                    self.set_estado(tr('✅ {0} copiado.').format(label), "#2ecc71")
                else: self.set_estado(tr("⚠️ No hay prompt generado."), "#e67e22")
            elif tipo == "negativo":
                if not tiene_neg:
                    self.set_estado(tr("ℹ️ Este modelo no usa negative prompt."), "#3498db")
                    return
                r = self.extraer_negative()
                if r:
                    pyperclip.copy(r)
                    self.set_estado(tr("✅ Prompt Negativo copiado."), "#2ecc71")
                else: self.set_estado(tr("⚠️ No hay NEGATIVE PROMPT."), "#e67e22")
            elif tipo == "todo":
                t = self.txt_salida.get("1.0", "end").strip()
                if t:
                    pyperclip.copy(t)
                    self.set_estado(tr("✅ Todo copiado."), "#2ecc71")
        except Exception as e:
            self.set_estado(tr('⚠️ Error: {0}').format(e), "#e74c3c")

    # LÓGICA CORE

    def reiniciar_memoria(self):
        modo    = self.modo_var.get()
        es_nsfw = self.switch_nsfw_var.get()
        natural = self.is_natural_mode()
        brief   = hasattr(self, 'brief_var') and self.brief_var.get()
        neg_custom = self.txt_negative.get("1.0", "end").strip() if hasattr(self, 'txt_negative') else ""

        if modo == "audio":
            motor = self.combo_modelo_audio.get() if hasattr(self, 'combo_modelo_audio') else "Suno v5"
            sys_p = SYSTEM_AUDIO_SUNO if motor.startswith("Suno") else SYSTEM_AUDIO_SEAART
            sys_p = self.prompts.inyectar_specs_audio(sys_p)
            if brief: sys_p = sys_p + BRIEF_MODIFIER
            sys_p = self.prompts.inyectar_destino(sys_p)
            self.deepseek.reiniciar(sys_p)
            return

        if natural:
            if modo == "video":
                sys_p = SYSTEM_NATURAL_VIDEO_NSFW if es_nsfw else SYSTEM_NATURAL_VIDEO
            elif es_nsfw:
                sys_p = SYSTEM_NATURAL_NSFW
            else:
                sys_p = SYSTEM_NATURAL_SFW
            sys_p = self.prompts.inyectar_specs_modelo(sys_p)
            if brief: sys_p = sys_p + BRIEF_MODIFIER
            sys_p = self.prompts.inyectar_destino(sys_p)
            self.deepseek.reiniciar(sys_p)
        else:
            if modo == "video":
                sys_p = SYSTEM_VIDEO_NSFW if es_nsfw else SYSTEM_VIDEO
                neg_base = NEGATIVE_BASE_NSFW if es_nsfw else NEGATIVE_BASE_VIDEO
            elif es_nsfw:
                sys_p = SYSTEM_IMAGEN_NSFW
                neg_base = NEGATIVE_BASE_NSFW
            else:
                sys_p = SYSTEM_IMAGEN_SFW
                neg_base = NEGATIVE_BASE_SFW

            neg_final = neg_base + (", " + neg_custom if neg_custom else "")
            sys_p = sys_p.replace("[negative tags]", neg_final)
            sys_p = self.prompts.inyectar_specs_modelo(sys_p)
            if brief: sys_p = sys_p + BRIEF_MODIFIER
            sys_p = self.prompts.inyectar_destino(sys_p)
            self.deepseek.reiniciar(sys_p)

    # Inyección de specs por modo, plantillas y construcción de modelo info:
    # extraídos a PromptsInyeccionMixin (modules/prompts_inyeccion.py).

    def _construir_peticion(self, idea, modo_letra):
        base = f"MODO {modo_letra}: Genera prompt para: '{idea}'. Estilos: {self.footer.estilos_texto()}."

        # Forzar formato según modo tag-based o natural
        if self.modo_var.get() == "imagen" and not self.is_natural_mode():
            base += " FORMATO OBLIGATORIO: tags separados por comas con pesos (tag:1.2). NO prosa fluida. Tags densos de 2-5 palabras. 5-10 pesos en POSITIVE, 3-6 en NEGATIVE."

        # ADN visual activo: inyectar como rasgos inmutables
        if getattr(self, '_anclaje_visual', None):
            base += (f"\n\n⚓ ADN VISUAL INMUTABLE — INCLUYE LITERALMENTE estos rasgos en el POSITIVE PROMPT (no los modifiques):\n"
                     f"{self._anclaje_visual}\n"
                     f"⚠️ Estos rasgos son OBLIGATORIOS y deben aparecer en el output.")

        return base + self.prompts.construir_modelo_info()

    def _safe_pack(self, widget, **kwargs):
        """Empaqueta widget con 'before' solo si la referencia no está oculta por Focus."""
        if 'before' in kwargs:
            ref = kwargs['before']
            try:
                # Solo quitar 'before' si el widget fue oculto explícitamente (Focus mode)
                hidden = getattr(self, '_focus_pack_info', {})
                for attr, info in hidden.items():
                    w = getattr(self, attr, None)
                    if w == ref:
                        kwargs = {k: v for k, v in kwargs.items() if k != 'before'}
                        break
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        widget.pack(**kwargs)

    # MODEL SPECS / NATURAL MODE HELPERS

    def get_current_model_specs(self):
        modo = self.modo_var.get()
        if modo == "video": return get_model_specs(self.combo_modelo_video.get())
        if modo == "audio" and hasattr(self, 'combo_modelo_audio'): return get_audio_model_specs(self.combo_modelo_audio.get())
        if modo == "imagen": return get_image_model_specs(self.combo_modelo_imagen.get())
        return None

    def is_natural_mode(self):
        return _pl.is_natural_mode(
            self.modo_var.get(),
            self.plataforma_var.get(),
            self.combo_modelo_imagen.get() if hasattr(self, 'combo_modelo_imagen') else "",
        )

    def _packear_negative_y_imgref(self):
        modo = self.modo_var.get()

        if self._debe_mostrar_negatives():
            self.lbl_neg_disabled.pack_forget()
            self.frame_neg_outer.pack(fill="both", expand=True, padx=5, pady=5)
        else:
            self.frame_neg_outer.pack_forget()
            self.lbl_neg_disabled.pack(fill="both", expand=True, padx=5, pady=20)

        if modo == "audio":
            try: self.frame_pers_lora.pack_forget()
            except Exception as e:
                logger.debug(f"[silent] {e}")
        else:
            try: self.frame_pers_lora.pack(fill="x", pady=(2, 1), before=self.frame_plantilla_brief)
            except Exception as e:
                logger.debug(f"[silent] {e}")

        # Imagen ref: visible en imagen y vídeo, oculto en audio.
        # IMPORTANTE: usamos before=self._spacer_ajustes para que el
        # imgref se mantenga en su posición original (antes del spacer)
        # y no salte al final del tab Ajustes Extra al cambiar de modo.
        if hasattr(self, 'frame_imgref_inner'):
            if modo != "audio":
                try:
                    if hasattr(self, '_spacer_ajustes') and self._spacer_ajustes.winfo_exists():
                        self.frame_imgref_inner.pack(fill="x", pady=(1, 2),
                                                     before=self._spacer_ajustes)
                    else:
                        self.frame_imgref_inner.pack(fill="x", pady=(1, 2))
                except Exception as e:
                    logger.debug(f"[silent] {e}")
            else:
                try: self.frame_imgref_inner.pack_forget()
                except Exception as e:
                    logger.debug(f"[silent] {e}")

        # Frame placeholder externo siempre oculto (legacy)
        try: self.frame_img_ref.pack_forget()
        except Exception as e:
            logger.debug(f"[silent] {e}")

    def _debe_mostrar_negatives(self):
        return _pl.debe_mostrar_negatives(
            self.modo_var.get(),
            self.plataforma_var.get(),
            self.combo_modelo_imagen.get() if hasattr(self, 'combo_modelo_imagen') else "",
            self.combo_modelo_video.get() if hasattr(self, 'combo_modelo_video') else "",
        )

    def _es_comfyui_turbo(self, plataforma=None, modelo=None):
        if plataforma is None:
            plataforma = self.plataforma_var.get() if hasattr(self, 'plataforma_var') else ""
        if modelo is None:
            modelo = self.combo_modelo_imagen.get() if hasattr(self, 'combo_modelo_imagen') else ""
        return _pl.es_comfyui_turbo(plataforma, modelo)

    # IDEAS / VARIACIONES / COMPARADOR

    def _ocultar_ideas(self):
        for attr in ['_ideas_frame', '_variaciones_frame']:
            frame = getattr(self, attr, None)
            if frame:
                try:
                    frame.pack_forget()
                    for w in frame.winfo_children(): w.destroy()
                    frame.destroy()
                except: pass
                setattr(self, attr, None)

    def _mostrar_ideas(self, ideas):
        """Muestra las ideas como cards clicables.

        Mejoras v2:
        - Click en cualquier parte de la card = Apply (acción más esperada).
        - Botón "🔁 Más" en el header → genera otras 3 ideas distintas.
        - Botón "✨ Más como esta" por card → 3 ideas similares a esa.
        """
        self._ocultar_ideas()
        if not ideas:
            return
        is_lt = ctk.get_appearance_mode().lower() == "light"
        ideas_frame = ctk.CTkFrame(self, fg_color="#e8e8e8" if is_lt else "#0f1318")
        ideas_frame.pack(pady=(6, 0), padx=16, fill="x", before=self.frame_entrada)

        hdr = ctk.CTkFrame(ideas_frame, fg_color="#e0e0e0" if is_lt else "#1a2a1a",
                            corner_radius=6, height=30)
        hdr.pack(fill="x", pady=(0, 4), padx=4)
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=tr("💡 Ideas — click en una para aplicarla"),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#f39c12").pack(side="left", padx=8)

        # Botón "🔁 Más" — regenera otras 3 ideas distintas
        ctk.CTkButton(hdr, text=tr("🔁 Más"), width=70, height=22,
                      fg_color="#2a6a4a", hover_color="#1f5037",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      command=self.cmd_ideas).pack(side="right", padx=4)

        btn_cerrar = ctk.CTkButton(hdr, text="✕", width=24, height=22,
                                     fg_color="transparent",
                                     hover_color="#dc2626" if is_lt else "#3a1a1a",
                                     text_color="#6b7280" if is_lt else "#888888",
                                     font=ctk.CTkFont(size=11),
                                     command=self._ocultar_ideas)
        btn_cerrar.pack(side="right", padx=4)

        for i, idea in enumerate(ideas):
            idea_texto = idea.strip()
            card_bg = "#f0f0f0" if is_lt else "#0f1620"
            card_hover = "#e0e8f0" if is_lt else "#1a2438"
            card = ctk.CTkFrame(ideas_frame, fg_color=card_bg, corner_radius=6,
                                 cursor="hand2")
            card.pack(fill="x", pady=2, padx=4)

            lbl = ctk.CTkLabel(card, text=f"#{i+1}: {idea_texto}",
                                font=ctk.CTkFont(size=11),
                                anchor="w", justify="left", wraplength=900,
                                text_color="#1f2937" if is_lt else "#e5e7eb",
                                cursor="hand2")
            lbl.pack(side="left", fill="x", expand=True, padx=8, pady=6)
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=4, pady=4)

            def _aplicar(t=idea_texto, n=i+1):
                self.txt_idea.delete("1.0", "end")
                self.txt_idea.insert("1.0", t)
                self._ocultar_ideas()
                self.set_estado(tr('💡 Idea #{0} aplicada — pulsa ✨ Generar').format(n), "#3498db")

            def _copiar(t=idea_texto, n=i+1):
                pyperclip.copy(t)
                self.set_estado(tr('📋 Idea #{0} copiada').format(n), "#2ecc71")

            def _mas_como_esta(t=idea_texto):
                """Pide 3 ideas SIMILARES a esta."""
                self.set_estado(tr("✨ Generando 3 ideas similares..."), "#f39c12")
                self.toggle_botones(False)
                modo = self.modo_var.get()
                tipo = "canción" if modo == "audio" else "vídeo" if modo == "video" else "imagen"
                peticion = (
                    f"Genera 3 IDEAS NUEVAS para {tipo} que sean SIMILARES en mood/temática a esta:\n\n"
                    f"IDEA BASE: {t}\n\n"
                    f"REGLAS:\n"
                    f"- Mantén el mismo género/atmósfera/temática.\n"
                    f"- Cambia detalles (sujeto exacto, escena, hora, paleta, encuadre).\n"
                    f"- Estilos activos: {self.footer.estilos_texto()}\n\n"
                    f"FORMATO: '1. Idea', '2. Idea', '3. Idea' (una por línea, sin explicaciones)."
                )
                if get_idioma() == "en":
                    peticion += "\n- IMPORTANT: write the 3 ideas in ENGLISH."
                self.sesion._sesion_log(f"✨ Más como esta: \"{t[:40]}\"")
                self._executor.submit(self.workers.worker_ia, peticion, True).add_done_callback(log_future_exc)

            def _generar(t=idea_texto):
                self.txt_idea.delete("1.0", "end")
                self.txt_idea.insert("1.0", t)
                self._ocultar_ideas()
                self.cmd_prompt()

            # Click en la card (label o frame) = Apply directo
            for w in (card, lbl):
                w.bind("<Button-1>",
                       lambda _e, t=idea_texto, n=i+1: _aplicar(t, n))
                # Hover sutil para indicar clickable
                w.bind("<Enter>",
                       lambda _e, cd=card: cd.configure(fg_color=card_hover))
                w.bind("<Leave>",
                       lambda _e, cd=card: cd.configure(fg_color=card_bg))

            ctk.CTkButton(btn_frame, text=tr("✨ Similares"), width=85, height=26,
                          fg_color="#7c3aed", hover_color="#5d2ab5",
                          font=ctk.CTkFont(size=10),
                          command=_mas_como_esta).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="📋", width=32, height=26,
                          fg_color="#2563eb" if is_lt else "#1e3a8a",
                          hover_color="#1d4ed8" if is_lt else "#162d49",
                          font=ctk.CTkFont(size=10),
                          command=_copiar).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text=tr("🚀 Generar"), width=85, height=26,
                          fg_color="#15803d",
                          hover_color="#166534" if is_lt else "#0d5026",
                          font=ctk.CTkFont(size=10, weight="bold"),
                          command=_generar).pack(side="left", padx=2)

        self._ideas_frame = ideas_frame
        self.update()

    def _parsear_variaciones(self, texto, n_esperado=None):
        """Wrapper sobre prompt_helpers.parsear_variaciones (sesión 18).

        Lógica pura extraída a modules/prompt_helpers.py. Este método
        se mantiene para compat con call sites legacy `self._parsear_variaciones()`.
        """
        return _h_parsear_variaciones(texto, n_esperado=n_esperado)

    def _mostrar_variaciones(self, variaciones):
        """Muestra las variaciones en un modal con cards visibles.

        v2 — antes era un panel inline que comprimía `txt_salida` a 1 línea
        ("se ve solo '1'") porque empujaba el layout. Ahora es un Toplevel
        independiente con preview del contenido de cada variación + botones
        Aplicar al resultado / Copiar todo / Copiar POS / Copiar NEG.
        """
        if not variaciones:
            return
        # Limpiar legacy panel inline si quedaba colgado de una versión anterior
        if hasattr(self, '_variaciones_frame') and self._variaciones_frame:
            try:
                self._variaciones_frame.destroy()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            self._variaciones_frame = None

        is_lt = ctk.get_appearance_mode().lower() == "light"
        from config import get_theme_colors
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self)
        vent.title(tr("🔀 Variaciones — elige cuál usar"))
        vent.geometry("900x720")
        vent.transient(self)

        ctk.CTkLabel(vent, text=tr('🔀 {0} variaciones generadas').format(len(variaciones)),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 3))
        n_total = len(variaciones)
        ctk.CTkLabel(vent,
                     text=tr('Compara las {0} versiones · Pulsa ✅ Aplicar al resultado en la que más te guste').format(n_total),
                     font=ctk.CTkFont(size=10),
                     text_color=c["muted_text"]).pack(pady=(0, 8))

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=5)

        # Colores para distinguir las cards
        accent_colors = (
            ["#2563eb", "#15803d", "#7c3aed"] if is_lt else
            ["#3b82f6", "#22c55e", "#a855f7"]
        )

        debe_mostrar_neg = self._debe_mostrar_negatives()

        # Refs compartidas para que aplicar una desmarque las demás visualmente
        cards_refs = []

        for i, var in enumerate(variaciones):
            accent = accent_colors[i % len(accent_colors)]
            card = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=8,
                                 border_color=accent, border_width=2)
            card.pack(fill="x", pady=6, padx=2)
            cards_refs.append((card, accent))

            hdr = ctk.CTkFrame(card, fg_color="transparent")
            hdr.pack(fill="x", padx=10, pady=(8, 2))
            ctk.CTkLabel(hdr, text=tr('  Variación #{0}').format(i+1),
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=accent).pack(side="left")

            # Stats: longitud y si tiene POSITIVE/NEGATIVE
            pos_text = self._extraer_pos_de_bloque(var) or ""
            neg_text = self._extraer_neg_de_bloque(var) or ""
            stats = f"POS: {len(pos_text)} chars"
            if neg_text:
                stats += f" · NEG: {len(neg_text)} chars"
            ctk.CTkLabel(hdr, text=stats,
                         font=ctk.CTkFont(size=9, slant="italic"),
                         text_color=c["muted_text"]).pack(side="left", padx=(10, 0))

            # Preview del contenido (textbox con scroll propio)
            preview = ctk.CTkTextbox(card,
                                      font=ctk.CTkFont(family="Consolas", size=10),
                                      wrap="word", height=120)
            preview.pack(fill="x", padx=10, pady=(2, 6))
            preview.insert("1.0", var)
            preview.configure(state="disabled")

            # Botones de acción por card
            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=10, pady=(0, 8))

            def _aplicar(v=var, n=i+1, card_ref=card):
                """Aplica al editor SIN cerrar la ventana — coherente con el
                resto de comparadores (commit 5451292). Highlight dorado en
                la card aplicada, las demás vuelven a su color de acento."""
                self.actualizar_salida(v)
                # Desmarcar todas, marcar solo la aplicada
                for prev_card, prev_accent in cards_refs:
                    try:
                        if prev_card is card_ref:
                            prev_card.configure(border_color="#fbbf24", border_width=3)
                        else:
                            prev_card.configure(border_color=prev_accent, border_width=2)
                    except Exception as _e:
                        logger.debug(f"[silent highlight] {_e}")
                self.set_estado(
                    tr('✅ Variación #{0} aplicada — la ventana sigue abierta para probar otras').format(n),
                    "#2ecc71")

            def _copiar_todo(v=var, n=i+1):
                pyperclip.copy(v)
                self.set_estado(tr('📋 Variación #{0} copiada completa').format(n), "#2ecc71")

            def _copiar_pos(v=var, n=i+1):
                p = self._extraer_pos_de_bloque(v)
                if p:
                    pyperclip.copy(p)
                    self.set_estado(tr('📋 POSITIVE #{0} copiado').format(n), "#2ecc71")
                else:
                    self.set_estado(tr('⚠️ No se encontró POSITIVE en #{0}').format(n), "#e74c3c")

            def _copiar_neg(v=var, n=i+1):
                n_text = self._extraer_neg_de_bloque(v)
                if n_text:
                    pyperclip.copy(n_text)
                    self.set_estado(tr('📋 NEGATIVE #{0} copiado').format(n), "#2ecc71")
                else:
                    self.set_estado(tr('⚠️ No se encontró NEGATIVE en #{0}').format(n), "#e74c3c")

            ctk.CTkButton(btn_row, text=tr("✅ Aplicar al resultado"),
                          width=170, height=28,
                          fg_color="#1a8a3c", hover_color="#127a30",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          command=_aplicar).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text=tr("📋 Todo"), width=80, height=28,
                          fg_color=accent, hover_color=self._darker(accent),
                          font=ctk.CTkFont(size=10),
                          command=_copiar_todo).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text=tr("📋 POS"), width=80, height=28,
                          fg_color="#15803d", hover_color="#0f5f29",
                          font=ctk.CTkFont(size=10),
                          command=_copiar_pos).pack(side="left", padx=2)
            if debe_mostrar_neg:
                ctk.CTkButton(btn_row, text=tr("📋 NEG"), width=80, height=28,
                              fg_color="#dc2626", hover_color="#b91c1c",
                              font=ctk.CTkFont(size=10),
                              command=_copiar_neg).pack(side="left", padx=2)

        # Cerrar
        ctk.CTkButton(vent, text=tr("Cerrar"), width=120, height=30,
                      command=vent.destroy).pack(pady=(0, 12))

    def _extraer_pos_de_bloque(self, bloque):
        """Wrapper sobre prompt_helpers.extraer_pos_de_bloque (sesión 18)."""
        return _h_extraer_pos_de_bloque(bloque)

    def _extraer_neg_de_bloque(self, bloque):
        limpio = limpiar_marcadores(bloque)
        if "NEGATIVE PROMPT:" in limpio: return limpio.split("NEGATIVE PROMPT:")[1].strip(" \n*")
        if "NEGATIVE:" in limpio: return limpio.split("NEGATIVE:")[1].strip(" \n*")

        global_neg = self.extraer_negative()
        if global_neg:
            return global_neg
        return None

    # COMANDOS & WORKERS

    def _recortar_si_excede(self, texto, max_chars, max_chars_negative=None):
        """Wrapper sobre prompt_helpers.recortar_si_excede (sesión 18)."""
        return _h_recortar_si_excede(texto, max_chars, max_chars_negative=max_chars_negative)


    def _contexto_loras_personaje(self, sufijo_intro: str = "") -> str:
        """Bloque de contexto LoRA/Personaje para el LLM. Delega la lógica a prompt_logic."""
        try:
            rasgos_loras = self.footer.rasgos_loras_activos() or []
        except Exception:
            rasgos_loras = []
        nombres_loras: list = []
        try:
            _primario = self.combo_lora.get() if hasattr(self, "combo_lora") else ""
            if _primario and _primario != "— Sin LoRA —":
                nombres_loras.append(_primario)
        except Exception:
            pass
        for _n in getattr(self, "loras_multi", []) or []:
            if _n not in nombres_loras:
                nombres_loras.append(_n)
        pers_activo = ""
        try:
            pers_activo = self.footer.personaje_activo() or ""
        except Exception:
            pass
        return _pl.contexto_loras_personaje(rasgos_loras, nombres_loras, pers_activo, sufijo_intro)

    def _contexto_modelo_para_ideas(self):
        """Contexto del modelo activo para ideas. Delega la lógica a prompt_logic."""
        try:
            modo = self.modo_var.get()
            if modo == "imagen":
                modelo = self.combo_modelo_imagen.get()
                specs = get_image_model_specs(modelo)
            elif modo == "video":
                modelo = self.combo_modelo_video.get()
                specs = get_model_specs(modelo)
            else:
                modelo = self.combo_modelo_audio.get()
                specs = get_audio_model_specs(modelo)
            return _pl.contexto_modelo_para_ideas(modo, modelo, specs)
        except Exception as e:
            logger.debug(f"[silent] {e}")
            return ""

    def cmd_ideas(self):
        try:
            self._ocultar_ideas()
            self.reiniciar_memoria()  # Evitar contaminación del historial previo
            idea = self.txt_idea.get("1.0", "end").strip()
            tipo = "canción" if self.modo_var.get() == "audio" else "vídeo" if self.modo_var.get() == "video" else "imagen"
            peticion = f"MODO A: Devuelve SOLO 3 ideas, una por línea con formato '1. Idea', '2. Idea', '3. Idea'. Tema: {tipo} con estilos: '{self.footer.estilos_texto()}'."

            # Contexto del MODELO activo → ideas a medida de su estilo
            peticion += self._contexto_modelo_para_ideas()

            # Contexto LoRAs/personaje activos
            peticion += self._contexto_loras_personaje("las 3 ideas")

            if idea: peticion += f"\n\nTema añadido por el usuario: {idea}."

            # Las ideas son contenido para el usuario → en el idioma de la UI.
            if get_idioma() == "en":
                peticion += " IMPORTANT: write the 3 ideas in ENGLISH."

            self.set_estado(tr("⏳ Generando ideas..."), "#f39c12")
            self.sesion._sesion_log(f"💡 Pidió ideas · tema: \"{(idea or 'sin tema')[:40]}\"")
            self.toggle_botones(False)
            self._executor.submit(self.workers.worker_ia, peticion, True).add_done_callback(log_future_exc)
        except Exception as e:
            logger.exception("cmd_ideas falló")
            self.set_estado(tr('❌ Error al preparar ideas: {0}').format(e), "#e74c3c")

    def cmd_prompt(self):
        self._ocultar_ideas()
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea:
            self.set_estado(tr("⚠️ Escribe o selecciona una idea primero."), "#e67e22")
            return
        # Detectar NSFW automáticamente
        self.analysis.detectar_nsfw_auto(idea)
        # Mejora 14: log sesión
        try:
            modelo = (self.combo_modelo_imagen.get() if self.modo_var.get() == "imagen" else
                      self.combo_modelo_video.get() if self.modo_var.get() == "video" else
                      self.combo_modelo_audio.get())
            self.sesion._sesion_log(f"✨ Generó prompt · idea: \"{idea[:60]}{'…' if len(idea) > 60 else ''}\" · modelo: {modelo}")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        self.set_estado(tr("⏳ Compilando prompt..."), "#f39c12")
        self.toggle_botones(False)
        self._executor.submit(self.workers.worker_prompt_traduccion, idea).add_done_callback(log_future_exc)

    # ⚡ QUICK GENERATE

    def cmd_prompt_quick(self):
        """⚡ Quick Generate — versión rápida del cmd_prompt.

        Diferencias vs cmd_prompt normal:
        - Sin traducción ES→EN (los LLMs entienden español igual)
        - Sin detección NSFW
        - temperature 0.4 (más consistente, menos variación)
        - max_tokens 1200 fijo (suficiente para prompts normales)
        - System prompt reducido: solo modelo + ratio + estilos clave
        - Mantiene: plataforma, modelo, ratio, estilos, personaje, LoRA, negative
        - Salta: ADN visual, refinamientos opcionales

        Tiempo aproximado: 3-6s vs 8-15s del Generar normal.
        Atajo: Alt+Enter
        """
        self._ocultar_ideas()
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea:
            self.set_estado(tr("⚠️ Escribe o selecciona una idea primero."), "#e67e22")
            return
        try:
            modelo = (self.combo_modelo_imagen.get() if self.modo_var.get() == "imagen" else
                      self.combo_modelo_video.get() if self.modo_var.get() == "video" else
                      self.combo_modelo_audio.get())
            self.sesion._sesion_log(f"⚡ Quick: idea: \"{idea[:60]}{'…' if len(idea) > 60 else ''}\" · modelo: {modelo}")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        self.set_estado(tr("⚡ Quick generate..."), "#d97706")
        self.toggle_botones(False)
        self._executor.submit(self.workers.worker_prompt_quick, idea).add_done_callback(log_future_exc)

    def _pedir_n_modal(self, titulo, descripcion, n_min, n_max, default,
                        key_pref=None):
        """Modal pequeño con slider para elegir N. Devuelve int o None
        si el usuario cancela.

        - `key_pref`: si se pasa, recuerda la última N usada en
          `preferencias[key_pref]`.
        - El método bloquea con `wait_window()` para devolver el valor
          sincrónicamente, permitiendo usar `if n is None: return`.
        """
        # Cargar última N de preferencias si key_pref existe
        if key_pref:
            try:
                prefs = self.store.cargar_preferencias()
                default = int(prefs.get(key_pref, default))
            except Exception as _e:
                logger.debug(f"[silent _pedir_n cargar] {_e}")
        default = max(n_min, min(n_max, default))

        sel = GPromptWindow(self)
        sel.title(titulo)
        sel.geometry("440x240")
        sel.transient(self)
        sel.grab_set()

        ctk.CTkLabel(sel, text=titulo,
                     font=ctk.CTkFont(size=14, weight="bold")
                     ).pack(pady=(15, 4))
        ctk.CTkLabel(sel, text=descripcion,
                     font=ctk.CTkFont(size=10), text_color="#888",
                     justify="center", wraplength=400
                     ).pack(pady=(0, 10))

        n_var = ctk.IntVar(value=default)
        lbl_n = ctk.CTkLabel(sel, text=tr('N = {0}').format(default),
                              font=ctk.CTkFont(size=22, weight="bold"),
                              text_color="#2ecc71")
        lbl_n.pack(pady=(0, 6))

        def _on_slide(v):
            n = int(round(float(v)))
            n_var.set(n)
            lbl_n.configure(text=tr('N = {0}').format(n))

        slider = ctk.CTkSlider(sel, from_=n_min, to=n_max,
                                number_of_steps=n_max - n_min,
                                command=_on_slide, width=320)
        slider.set(default)
        slider.pack(pady=(0, 4))
        ctk.CTkLabel(sel, text=tr('Rango: {0}–{1}').format((n_min), (n_max)),
                     font=ctk.CTkFont(size=9),
                     text_color="#666").pack(pady=(0, 8))

        resultado = {"n": None}

        def _aceptar():
            n = n_var.get()
            if key_pref:
                try:
                    prefs_g = self.store.cargar_preferencias()
                    prefs_g[key_pref] = n
                    self.store.guardar_preferencias(prefs_g)
                except Exception as _e:
                    logger.debug(f"[silent _pedir_n guardar] {_e}")
            resultado["n"] = n
            sel.destroy()

        btn_row = ctk.CTkFrame(sel, fg_color="transparent")
        btn_row.pack(pady=(0, 12))
        ctk.CTkButton(btn_row, text=tr("▶ Generar"), width=140, height=32,
                      fg_color="#1a7a3c", hover_color="#145e2d",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=_aceptar).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=tr("Cancelar"), width=100, height=32,
                      fg_color="#444444", hover_color="#222222",
                      command=sel.destroy).pack(side="left", padx=4)

        sel.bind("<Return>", lambda _e: _aceptar())
        sel.wait_window()
        return resultado["n"]

    def cmd_variaciones(self):
        self._ocultar_ideas()
        idea, pos = self.txt_idea.get("1.0", "end").strip(), self.extraer_positive()

        if not (pos and len(pos) > 10) and not idea:
            return self.set_estado(tr("⚠️ Necesitas una idea o prompt previo."), "#e67e22")

        # Slider N (antes hardcoded a 3)
        n = self._pedir_n_modal(
            "🔀 Variaciones",
            "¿Cuántas variaciones quieres generar?\n"
            "Menor = más rápido · Mayor = más variedad",
            n_min=2, n_max=6, default=3,
            key_pref="variaciones_n",
        )
        if n is None:
            return

        formato_extra = " OBLIGATORIO: En CADA variación escribe 'POSITIVE PROMPT:' y luego 'NEGATIVE PROMPT:'." if self._debe_mostrar_negatives() else ""

        # Forzar formato tag-based si aplica
        if self.modo_var.get() == "imagen" and not self.is_natural_mode():
            formato_extra += f" FORMATO: tags separados por comas con pesos (tag:1.2). NO prosa fluida. Las {n} variaciones deben usar el MISMO formato de tags."

        if pos and len(pos) > 10:
            peticion = f"MODO C: Genera {n} variaciones de este prompt. Base: '{pos}'. Estilos: {self.footer.estilos_texto()}." + formato_extra
            if idea: peticion += f" Incorpora también: {idea}."
        else:
            peticion = self._construir_peticion(idea, "C") + f" Genera {n} variaciones." + formato_extra

        self.set_estado(tr('🔀 Generando {0} variaciones...').format(n), "#f39c12")
        self.sesion._sesion_log(f"🔀 Generó {n} variaciones · base: \"{(pos or idea)[:50]}…\"")
        self.toggle_botones(False)
        self._executor.submit(self.workers.worker_ia, peticion, False, True, n).add_done_callback(log_future_exc)

    def cmd_vision(self):
        if self.modo_var.get() == "audio": return self.set_estado(tr("ℹ️ El análisis de imagen no aplica en modo audio."), "#3498db")
        if not self.imagen_cargada: return self.set_estado(tr("⚠️ Carga una imagen primero."), "#e67e22")
        self._ocultar_ideas()
        self.sesion._sesion_log("👁 Analizó imagen de referencia")
        self.toggle_botones(False)
        self._executor.submit(self.workers.worker_vision).add_done_callback(log_future_exc)

    def cmd_imagen_a_prompt(self):
        if self.modo_var.get() == "audio" or not self.imagen_cargada: return
        self._ocultar_ideas()
        try: self.sesion._sesion_log("🎯 Img→Prompt: generó prompt desde imagen")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        self.toggle_botones(False)
        self._executor.submit(self.workers.worker_imagen_a_prompt).add_done_callback(log_future_exc)

    def _cmd_convertir_a_video(self):
        """Convierte un prompt de imagen a formato de vídeo."""
        texto = self.txt_salida.get("1.0", "end").strip()
        if not texto or len(texto) < 20:
            return self.set_estado(tr("⚠️ Genera un prompt de imagen primero."), "#e67e22")
        try: self.sesion._sesion_log("🔄 Convirtió prompt imagen → vídeo")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        pos = self.extraer_positive() or texto
        self.set_estado(tr("🔄 Convirtiendo prompt de imagen a vídeo..."), "#f39c12")
        self.toggle_botones(False)

        def _worker():
            try:
                # Obtener specs del modelo de vídeo actual
                motor_vid = self.combo_modelo_video.get() if hasattr(self, 'combo_modelo_video') else "Kling 3.0"
                specs_vid = get_model_specs(motor_vid)
                max_c = specs_vid.get("max_chars", 1500) if specs_vid else 1500
                has_neg = specs_vid.get("has_negative", False) if specs_vid else False

                peticion = (
                    f"Convierte este prompt de IMAGEN a un prompt de VÍDEO para {motor_vid}.\n\n"
                    f"PROMPT IMAGEN ORIGINAL:\n{pos}\n\n"
                    f"INSTRUCCIONES:\n"
                    f"- Transforma la descripción estática en una escena con MOVIMIENTO y ACCIÓN.\n"
                    f"- Añade: movimiento del sujeto, movimiento de cámara (pan, zoom, dolly, tracking), transiciones de luz.\n"
                    f"- Mantén la estética, iluminación y estilo visual del prompt original.\n"
                    f"- Escribe en LENGUAJE NATURAL descriptivo (no tags con pesos).\n"
                    f"- Límite: {max_c} caracteres.\n"
                )
                if has_neg:
                    peticion += "- Genera POSITIVE PROMPT y NEGATIVE PROMPT separados.\n"
                else:
                    peticion += "- Solo genera POSITIVE PROMPT (este modelo no usa negativo).\n"

                resultado = self.deepseek.generar(peticion, temperature=0.5, max_tokens=1500)
                resultado = limpiar_marcadores(resultado)

                def _mostrar():
                    # Cambiar a modo vídeo
                    self.modo_var.set("video")
                    self.events._on_modo_cambio()
                    self.actualizar_salida(resultado)
                    self.data.guardar_en_historial(resultado)
                    self.set_estado(tr('🔄 Prompt convertido a vídeo ({0})').format(motor_vid), "#2ecc71")
                    self.toggle_botones(True)
                    self._sonar_completado()
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda e=e: self.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        self._executor.submit(_worker).add_done_callback(log_future_exc)

    def cmd_batch(self):
        try: self.sesion._sesion_log("📦 Abrió Batch (generación masiva)")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        abrir_batch(self)

    def cmd_batch_variables(self):
        try: self.sesion._sesion_log("⚡ Abrió Batch Variables")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        abrir_batch_variables(self)

    def cmd_reset(self):
        # Comprobar si hay trabajo no guardado
        idea = self.txt_idea.get("1.0", "end").strip()
        salida = self.txt_salida.get("1.0", "end").strip()
        if idea or salida:
            from tkinter import messagebox
            if not messagebox.askyesno(tr("Confirmar reset"),
                                     "¿Seguro? Perderás:\n"
                                     f"{'  • Idea actual' if idea else ''}\n"
                                     f"{'  • Prompt generado' if salida else ''}\n"
                                     "  • Imagen de referencia\n"
                                     "  • Estilos marcados\n\n"
                                     "Esta acción no se puede deshacer.",
                                     parent=self):
                return

        self.reiniciar_memoria()
        self.data._limpiar_imagen()
        self._ultimo_anclaje_visual = None
        self._anclaje_visual = None  # Limpiar ADN visual
        self.txt_idea.delete("1.0", "end")
        self.combo_lora.set("— Sin LoRA —")
        # Limpiar personaje
        if hasattr(self, 'combo_personaje'):
            self.combo_personaje.set("— Sin personaje —")
        # Limpiar estilos marcados
        for n, v in self.estilo_checks.items():
            v.set(False)
        self.ui._actualizar_contador_estilos()
        # Limpiar negativos
        self.footer._limpiar_negatives()
        self.actualizar_salida("")
        self._ocultar_ideas()
        self.set_estado(tr("🔄 Sistema reseteado."), "#3498db")
        try: self.sesion._sesion_log("🗑 Reset completo del sistema")
        except Exception as e:
            logger.debug(f"[silent] {e}")

    # CHAT COPILOTO NARRADOR

    def cmd_copiloto(self):
        texto_actual = self.txt_salida.get("1.0", "end").strip()
        if not texto_actual or len(texto_actual) < 20:
            return self.set_estado(tr("⚠️ Genera un prompt primero para poder usar el Copiloto."), "#e67e22")
        try: self.sesion._sesion_log("💬 Abrió Copiloto de prompt")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        vent_copiloto = GPromptWindow(self)
        vent_copiloto.title(tr("💬 Copiloto de Prompt"))
        vent_copiloto.geometry("450x600")
        vent_copiloto.transient(self)

        chat_frame = ctk.CTkScrollableFrame(vent_copiloto, fg_color="transparent")
        chat_frame.pack(fill="both", expand=True, padx=10, pady=10)

        input_frame = ctk.CTkFrame(vent_copiloto, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=(0, 10))

        txt_input = ctk.CTkEntry(input_frame, placeholder_text=tr("Ej: Haz que sea de noche..."))
        txt_input.pack(side="left", fill="x", expand=True, padx=(0, 5))

        def _add_msg(rol, texto, color):
            lbl = ctk.CTkLabel(chat_frame, text=texto, text_color=color, wraplength=400, justify="left", anchor="w")
            lbl.pack(fill="x", pady=4)
            chat_frame._parent_canvas.yview_moveto(1.0)

        _add_msg("Sistema", "🤖 Copiloto conectado.\nEscribe qué quieres cambiar o añadir al prompt que tienes en pantalla.", "#3498db")

        def _enviar(event=None):
            instruccion = txt_input.get().strip()
            if not instruccion: return

            txt_input.delete(0, "end")
            _add_msg("Usuario", f"👤 Tú: {instruccion}", "#ffffff")

            prompt_base = self.txt_salida.get("1.0", "end").strip()

            txt_input.configure(state="disabled")
            btn_send.configure(state="disabled")
            self.set_estado(tr("💬 Copiloto aplicando cambios..."), "#3498db")

            def _worker():
                try:
                    specs = self.get_current_model_specs()
                    limite_chars = specs.get("max_chars") if specs else 2000

                    peticion = (
                        f"Actúa como un editor experto de prompts. Tu tarea es MODIFICAR el prompt base siguiendo EXCLUSIVAMENTE la instrucción del usuario.\n"
                        f"MANTÉN la misma estructura y tags que el original.\n"
                        f"INVARIANTES: preserva SIEMPRE los elementos que el usuario no menciona explícitamente — cara, iluminación, outfit, composición, estilo. "
                        f"Si el usuario solo pide cambiar el fondo, el resto permanece idéntico. "
                        f"Si el prompt tiene texto literal entre comillas, manténlo verbatim salvo instrucción contraria.\n"
                    )
                    modo = self.modo_var.get()
                    # Forzar formato según modo
                    if modo == "imagen" and not self.is_natural_mode():
                        peticion += "FORMATO: el prompt usa tags separados por comas con pesos (tag:1.2). MANTÉN este formato. NO conviertas a prosa fluida.\n"
                    elif modo == "video":
                        peticion += "FORMATO: prompt de VÍDEO. Mantén estructura de shots, movimientos de cámara y descripción de acciones.\n"
                    elif modo == "audio":
                        peticion += "FORMATO: prompt de AUDIO/MÚSICA. Mantén estructura de estilo, letra y tags estructurales si los hay.\n"
                    peticion += (
                        f"⛔ REGLA ESTRICTA: El prompt final no debe superar los {limite_chars} caracteres.\n\n"
                        f"PROMPT BASE ACTUAL:\n{prompt_base}\n\n"
                        f"INSTRUCCIÓN DEL USUARIO: {instruccion}\n\n"
                        f"⚠️ FORMATO DE RESPUESTA OBLIGATORIO:\n"
                        f"Primero, escribe una frase muy breve en ESPAÑOL explicando de forma amigable qué has cambiado.\n"
                        f"Luego, escribe EXACTAMENTE este separador: |||\n"
                        f"Finalmente, escribe el nuevo prompt modificado completo en el idioma original (suele ser INGLÉS)."
                    )

                    respuesta = self.deepseek.generar(peticion, temperature=0.5, max_tokens=1500)

                    # Cortamos la respuesta usando la palabra mágica |||
                    if "|||" in respuesta:
                        explicacion, nuevo_prompt = respuesta.split("|||", 1)
                    else:
                        explicacion = "¡Hecho! Aquí tienes la versión actualizada:"
                        nuevo_prompt = respuesta

                    explicacion = explicacion.strip()
                    nuevo_prompt = nuevo_prompt.strip()

                    def _update_ui():
                        self.actualizar_salida(nuevo_prompt) # Actualiza el texto grande en inglés
                        _add_msg("Sistema", f"🤖 {explicacion}", "#2ecc71") # Te narra lo que hizo en español
                        txt_input.configure(state="normal")
                        btn_send.configure(state="normal")
                        txt_input.focus_set()
                        self.set_estado(tr("✅ Copiloto terminó la edición."), "#2ecc71")

                    self.after(0, _update_ui)
                except Exception as e:
                    err = e
                    def _err():
                        _add_msg("Sistema", f"❌ Error: {err}", "#e74c3c")
                        txt_input.configure(state="normal")
                        btn_send.configure(state="normal")
                        self.set_estado(tr("❌ Error en el Copiloto."), "#e74c3c")
                    self.after(0, _err)

            self._executor.submit(_worker).add_done_callback(log_future_exc)

        btn_send = ctk.CTkButton(input_frame, text=tr("Enviar"), width=60, fg_color="#2980b9", hover_color="#1f608a", command=_enviar)
        btn_send.pack(side="right")
        txt_input.bind("<Return>", _enviar)
