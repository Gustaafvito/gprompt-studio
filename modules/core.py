"""Core Mixin - Workers, Commands, Main Logic, Theme, Focus Mode, etc.

v1.0:
- Eliminadas 9 referencias muertas al parámetro modelo_llm en llamadas a
  self.deepseek.generar() / .traducir(). El parámetro ya no se usa porque
  el provider activo se obtiene desde self.clients.get_active_provider().
- Llamada a _actualizar_indicador_proveedor() tras cambio de LLM.
"""
import os
import re
import json
import logging
import threading
import datetime
import random
import pyperclip

logger = logging.getLogger("gprompt")
import tkinter as tk
import customtkinter as ctk
from config import (
    ESTILOS_IMAGEN, ESTILOS_VIDEO, ESTILOS_AUDIO,
    es_separador,
    get_model_specs, get_image_model_specs, get_audio_model_specs,
    get_prompt_template,
    MODEL_SPECS_IMAGEN, MODEL_SPECS,
    MODELOS_POR_PLATAFORMA_IMAGEN, MODELOS_IMAGEN_FLAT,
    PLATAFORMAS_IMAGEN, PLATAFORMAS_IMAGEN_LISTA,
    PLATAFORMAS_VIDEO, PLATAFORMAS_VIDEO_LISTA,
    PLATAFORMAS_AUDIO_LISTA,
    MOTORES_VIDEO, MOTORES_AUDIO, MOTOR_DEFAULT,
    RATIOS_IMAGEN, RATIOS_VIDEO,
)
from prompts import (
    SYSTEM_IMAGEN_SFW, SYSTEM_IMAGEN_NSFW, SYSTEM_VIDEO,
    SYSTEM_VIDEO_NSFW, SYSTEM_NATURAL_SFW, SYSTEM_NATURAL_NSFW,
    SYSTEM_NATURAL_VIDEO, SYSTEM_NATURAL_VIDEO_NSFW,
    SYSTEM_AUDIO_SUNO, SYSTEM_AUDIO_SEAART,
    NEGATIVE_BASE_SFW, NEGATIVE_BASE_NSFW, NEGATIVE_BASE_VIDEO,
    BRIEF_MODIFIER, REGLAS_APROVECHAR_BUDGET,
)
from workers import parsear_ideas, contar_tokens_aprox, limpiar_marcadores
from modules.windows import abrir_batch
from typing import TYPE_CHECKING
from modules.gprompt_window import GPromptWindow

if TYPE_CHECKING:
    from app import ArquitectoApp


def _recolor_labels(container, primary_color, secondary_color, muted_color):
    """Recursivamente recolorea todos los CTkLabel dentro de un contenedor.

    Usado por _apply_theme_colors para que al cambiar de tema todos los
    labels (Personaje, LoRA, Plantilla, Modelo, Ratio, Destino, Emoción,
    Voz…) se actualicen sin reiniciar la app.

    Heurística: el primer label de cada fila suele ser un título tipo
    "Modelo:" o "Ratio:" — esos van con primary_color. Los grises pequeños
    (size 9-10) normalmente son labels de ayuda — esos van con muted_color.
    """
    try:
        for child in container.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                txt = child.cget("text") or ""
                # No tocar labels vacíos o que tengan colores especiales
                # (verde de "estilos seleccionados", azul de URL...)
                current_color = str(child.cget("text_color"))
                # Skip colores especiales (verde, rojo, azul, púrpura, etc.)
                colores_especiales = (
                    "#2ecc71", "#059669", "#34d399",  # verdes
                    "#e74c3c", "#dc2626", "#f87171",  # rojos
                    "#3498db", "#2563eb", "#60a5fa",  # azules
                    "#9b59b6", "#7c3aed", "#a855f7",  # púrpuras
                    "#f39c12", "#d97706", "#fcd34d",  # amarillos
                )
                if any(esp.lower() in current_color.lower() for esp in colores_especiales):
                    continue
                # Determinar color según fuente/contenido
                try:
                    font_obj = child.cget("font")
                    font_size = font_obj.cget("size") if hasattr(font_obj, "cget") else 11
                except Exception:
                    font_size = 11
                # Texto pequeño (≤10) → muted; resto → primary
                if font_size <= 10 and not txt.endswith(":"):
                    child.configure(text_color=muted_color)
                else:
                    child.configure(text_color=primary_color)
            # Recursar en frames hijos
            elif hasattr(child, "winfo_children"):
                try:
                    _recolor_labels(child, primary_color, secondary_color, muted_color)
                except Exception as _e:
                    logger.debug(f"[silent] {_e}")
    except Exception as _e:
        logger.debug(f"[silent] {_e}")
def _recolor_widgets(container, is_light):
    """Recursivamente recolorea CTkComboBox, CTkSegmentedButton, CTkOptionMenu."""
    combo_bg = "#ffffff" if is_light else "#1a2030"
    combo_border = "#d1d5db" if is_light else "#2a3a50"
    combo_btn = "#2563eb" if is_light else "#2a3a50"
    combo_text = "#111827" if is_light else "#e5e7eb"
    dd_fg = "#ffffff" if is_light else "#1f2937"
    dd_hov = "#e5e7eb" if is_light else "#374151"
    dd_text = "#111827" if is_light else "#e5e7eb"
    seg_bg = "#e5e7eb" if is_light else "#1f2937"
    seg_sel = "#2563eb" if is_light else "#3b82f6"
    seg_hov = "#dbeafe" if is_light else "#374151"
    try:
        for child in container.winfo_children():
            try:
                if isinstance(child, ctk.CTkComboBox):
                    child.configure(fg_color=combo_bg, border_color=combo_border,
                                    button_color=combo_btn, text_color=combo_text,
                                    dropdown_fg_color=dd_fg, dropdown_hover_color=dd_hov,
                                    dropdown_text_color=dd_text)
                elif isinstance(child, ctk.CTkSegmentedButton):
                    child.configure(fg_color=seg_bg, selected_color=seg_sel,
                                    selected_hover_color=seg_sel, unselected_color=seg_bg,
                                    unselected_hover_color=seg_hov, text_color=combo_text)
                elif isinstance(child, ctk.CTkOptionMenu):
                    child.configure(fg_color=combo_bg, button_color=combo_btn,
                                    text_color=combo_text, dropdown_fg_color=dd_fg,
                                    dropdown_hover_color=dd_hov, dropdown_text_color=dd_text)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            if hasattr(child, "winfo_children"):
                _recolor_widgets(child, is_light)
    except Exception as _e:
        logger.debug(f"[silent] {_e}")
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
            self.set_estado(f"📐 Destino {dest} → Ratio auto: {ratio}", "#3498db")

        # Modo concurso: activar Brief automáticamente
        if dest == "Anthum (concurso)":
            self.brief_var.set(True)
            self._on_brief_cambio()
            self.set_estado("🏆 Modo Concurso Anthum — Brief activado, ratio 9:16, máxima calidad", "#f39c12")

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
            self._focus_exit_btn = ctk.CTkButton(self, text="✕ Salir de Focus", width=140, height=28,
                                                  fg_color="#7c3aed", hover_color="#6d28d9",
                                                  font=ctk.CTkFont(size=11, weight="bold"),
                                                  corner_radius=14,
                                                  command=self._cmd_modo_focus)
            self._focus_exit_btn.place(relx=0.5, rely=0.01, anchor="n")

            self._modo_focus_activo = True
            self.set_estado("🎯 Modo Focus ACTIVO — pulsa ✕ para salir", "#7c3aed")
        else:
            # DESACTIVAR: quitar botón flotante
            if self._focus_exit_btn:
                self._focus_exit_btn.destroy()
                self._focus_exit_btn = None

            # Restaurar widgets en el mismo orden con after= encadenado
            # Header va primero (antes de frame_entrada), luego cada uno after el anterior
            prev = None
            ancla = getattr(self, 'frame_entrada', None)
            for attr, info in self._focus_pack_order:
                widget = getattr(self, attr, None)
                if widget is None:
                    continue
                try:
                    info.pop('in', None)
                    info.pop('before', None)
                    info.pop('after', None)
                    if prev is not None:
                        widget.pack(after=prev, **info)
                    elif ancla:
                        widget.pack(before=ancla, **info)
                    else:
                        widget.pack(**info)
                    prev = widget
                except Exception:
                    try:
                        if ancla:
                            widget.pack(before=ancla, fill="x", padx=16, pady=2)
                        else:
                            widget.pack(fill="x", padx=16, pady=2)
                        prev = widget
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")
            self._focus_pack_order = []
            self._modo_focus_activo = False

            # Repintar colores del tema
            try:
                self._apply_theme_colors()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            self.set_estado("🎯 Modo Focus desactivado")

    # ON LLM CAMBIO

    def _on_llm_cambio(self, label=None):
        """Cuando el usuario cambia de proveedor LLM en el dropdown."""
        from api_clients import LLM_PROVIDERS

        if label is None:
            label = self.llm_var.get()
        # Mapear label → provider_id
        pid = getattr(self, "_llm_label_to_id", {}).get(label)
        if not pid:
            # Compatibilidad con etiquetas antiguas
            mapeo_legado = {
                "DeepSeek V3": "deepseek",
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
                self.set_estado(f"⚠️ {info.get('name', pid)} no tiene API key — abre 🔑 para configurar", "#e67e22")
                self._cmd_configurar_api_keys(provider_focus=pid)
                return
            # Cambiar el provider activo
            self.clients.cambiar_provider(pid)
            info = LLM_PROVIDERS.get(pid, {})
            self.set_estado(f"🧠 Cerebro: {info.get('name', pid)}", "#2ecc71")
            try: self._sesion_log(f"🧠 Cambió cerebro → {pid}")
            except Exception as e:
                logger.debug(f"[silent] {e}")
            try:
                if hasattr(self, "_actualizar_indicador_proveedor"):
                    self._actualizar_indicador_proveedor()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            try:
                if hasattr(self, "_refrescar_indicadores_llm"):
                    self._refrescar_indicadores_llm()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
    # TOGGLE TEMA CLARO/OSCURO

    def _apply_theme_colors(self):
        """Actualiza colores de header, barra de modo, checkboxes y labels
        sin destruir widgets. Incluye checkboxes de estilos (sin esto
        mantenían el color del tema antiguo al cambiar de tema)."""
        is_light = ctk.get_appearance_mode().lower() == "light"
        try:
            from config import get_theme_colors
            c = get_theme_colors(is_light)
        except Exception:
            c = {}

        hdr_bg = "#e8e8e8" if is_light else "#0d1117"
        hdr_text = "#111827" if is_light else "#e5e7eb"
        hdr_label = "#4b5563" if is_light else "#888888"
        combo_bg = "#ffffff" if is_light else "#1a2030"
        combo_border = "#d1d5db" if is_light else "#2a3a50"
        combo_btn = "#2563eb" if is_light else "#2a3a50"
        badge_bg = "#dbeafe" if is_light else "#1a2a3a"
        btn_bg = "#ffffff" if is_light else "#1a1a2a"
        btn_hover = "#f3f4f6" if is_light else "#2a2a3a"
        key_bg = "#7c3aed" if is_light else "#3a2a4a"
        key_hover = "#6d28d9" if is_light else "#4a3a5a"
        modo_bg = "#e8e8e8" if is_light else "#0f1318"
        modo_label = "#4b5563" if is_light else "#888888"
        sw_fg = "#d1d5db" if is_light else "#1f2937"
        sw_text_off = "#6b7280" if is_light else "#9ca3af"
        sw_border_off = "#d1d5db" if is_light else "#374151"
        nsfw_text_on = "#dc2626" if is_light else "#fca5a5"
        nsfw_border_on = "#dc2626" if is_light else "#ef4444"
        trad_text_on = "#2563eb" if is_light else "#93c5fd"
        trad_border_on = "#2563eb" if is_light else "#3b82f6"

        # Header
        if hasattr(self, '_header_frame'):
            self._header_frame.configure(fg_color=hdr_bg)
        if hasattr(self, '_lbl_cerebro'):
            self._lbl_cerebro.configure(text_color=hdr_label)
        if hasattr(self, 'combo_llm'):
            self.combo_llm.configure(fg_color=combo_bg, border_color=combo_border, button_color=combo_btn, text_color=hdr_text)
        if hasattr(self, '_btn_key'):
            self._btn_key.configure(fg_color=key_bg, hover_color=key_hover)
        # Botones de iconos del header
        if hasattr(self, '_header_btns'):
            for btn in self._header_btns:
                btn.configure(fg_color=btn_bg, hover_color=btn_hover)

        # Modo bar
        if hasattr(self, '_modo_frame'):
            self._modo_frame.configure(fg_color=modo_bg)
        if hasattr(self, '_lbl_plataforma'):
            self._lbl_plataforma.configure(text_color=modo_label)

        # Switches
        sw_button = "#374151" if is_light else "#ffffff"
        sw_button_hover = "#1f2937" if is_light else "#f3f4f6"
        if hasattr(self, 'switch_nsfw'):
            is_nsfw_on = self.switch_nsfw_var.get()
            self.switch_nsfw.configure(
                fg_color=sw_fg, border_color=nsfw_border_on if is_nsfw_on else sw_border_off,
                text_color=nsfw_text_on if is_nsfw_on else sw_text_off,
                button_color=sw_button, button_hover_color=sw_button_hover)
        if hasattr(self, '_sw_trad'):
            is_trad_on = self.switch_traduccion_var.get()
            self._sw_trad.configure(
                fg_color=sw_fg, border_color=trad_border_on if is_trad_on else sw_border_off,
                text_color=trad_text_on if is_trad_on else sw_text_off,
                button_color=sw_button, button_hover_color=sw_button_hover)
        # switch_brief y switch_instrumental también
        for sw_attr in ('switch_brief', 'switch_instrumental'):
            try:
                sw = getattr(self, sw_attr, None)
                if sw and sw.winfo_exists():
                    sw.configure(button_color=sw_button, button_hover_color=sw_button_hover)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        # Refrescar checkboxes de estilos: sin esto, al cambiar tema en
        # caliente los checkboxes mantenían colores antiguos (gris/gris).
        if hasattr(self, "estilo_checks") and hasattr(self, "frame_checks") and c:
            try:
                for w in self.frame_checks.winfo_children():
                    if isinstance(w, ctk.CTkCheckBox):
                        w.configure(
                            text_color=c["chk_text"],
                            border_color=c["chk_border"],
                            fg_color=c["accent_text"],
                            hover_color=c["accent_text"],
                        )
                # Fondo del scrollable
                self.frame_checks.configure(fg_color=c["chk_bg"])
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        # Label de estilos seleccionados (verde) y contador
        if hasattr(self, "lbl_estilos_sel"):
            try:
                verde = "#059669" if is_light else "#2ecc71"
                self.lbl_estilos_sel.configure(text_color=verde)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        if hasattr(self, "lbl_estilos_count") and c:
            try:
                self.lbl_estilos_count.configure(text_color=c["muted_text"])
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        # Refrescar contador (ajusta color según hay selección o no)
        try:
            if hasattr(self, "_actualizar_contador_estilos"):
                self._actualizar_contador_estilos()
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # Refrescar tabview central (Ajustes/Estilos/Negativos): el
        # tabview de CustomTkinter no se repinta al cambiar tema sin
        # forzar los colores explícitamente.
        if hasattr(self, "tabview") and c:
            try:
                tab_bg = c["panel_bg"]
                seg_bg = "#e5e7eb" if is_light else "#1f2937"
                seg_sel = "#2563eb" if is_light else "#3b82f6"
                seg_hov = "#dbeafe" if is_light else "#374151"
                self.tabview.configure(
                    fg_color=tab_bg, bg_color=tab_bg,
                    segmented_button_fg_color=seg_bg,
                    segmented_button_selected_color=seg_sel,
                    segmented_button_selected_hover_color=seg_sel,
                    segmented_button_unselected_color=seg_bg,
                    segmented_button_unselected_hover_color=seg_hov,
                    text_color=c["panel_text"],
                )
                for tab_name in ("⚙️ Ajustes Extra", "🎨 Estilos", "🚫 Negativos"):
                    try:
                        self.tabview.tab(tab_name).configure(fg_color=tab_bg, bg_color=tab_bg)
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        # Refrescar fondos de frames principales: sin esto al cambiar
        # tema las inner frames mantienen el fg_color del tema anterior.
        tab_bg = c["panel_bg"]
        # Frames con fondo "panel_bg" (claro/oscuro según tema)
        for _fname in ("frame_pers_lora", "frame_plantilla_brief", "frame_imgref_inner",
                       "frame_neg_outer", "frame_video", "frame_audio",
                       "_img_history_frame",
                       "_frame_estilos_header", "_frame_neg_header", "_frame_neg_presets"):
            try:
                _f = getattr(self, _fname, None)
                if _f is not None and _f.winfo_exists():
                    _f.configure(fg_color=tab_bg)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        # Reconfigurar tabs internos del tabview: gestionan sus tabs
        # como CTkFrame que necesitan ser repintados explícitamente al
        # cambiar tema, sino el contenido interno (Ajustes Extra,
        # Estilos, Negativos) queda con el fg_color del tema anterior.
        if hasattr(self, "tabview"):
            try:
                self.tabview.configure(fg_color=tab_bg, bg_color=tab_bg)
                for tab_name in ("⚙️ Ajustes Extra", "🎨 Estilos", "🚫 Negativos"):
                    try:
                        t = self.tabview.tab(tab_name)
                        if t is not None:
                            t.configure(fg_color=tab_bg, bg_color=tab_bg)
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        # Forzar fg_color de la ventana raíz: sin esto, el área entre
        # tabs y el footer se queda gris medio del tema anterior.
        try:
            root_bg = "#f5f5f5" if is_light else "#0d1117"
            self.configure(fg_color=root_bg)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # Repintar botones rápidos de ratio: los iconos ⬜📱🖥📸🖼 al lado
        # del combo Ratio se quedaban con fondo oscuro al pasar a tema
        # claro porque su fg_color se fija en construcción.
        if hasattr(self, "ratio_btns") and self.ratio_btns:
            ratio_btn_bg = "#ffffff" if is_light else "#1a2030"
            ratio_btn_hover = "#dbeafe" if is_light else "#2a3a50"
            ratio_btn_text = c["panel_text"] if c else ("#111827" if is_light else "#e5e7eb")
            try:
                for btn in self.ratio_btns.values():
                    try:
                        if btn.winfo_exists():
                            btn.configure(fg_color=ratio_btn_bg,
                                          hover_color=ratio_btn_hover,
                                          text_color=ratio_btn_text)
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        # Refrescar TODOS los labels en paneles
        # Recorremos todos los frames superiores y actualizamos los CTkLabel
        # que tengan texto pero no color forzado.
        if c:
            try:
                lbl_color = c["panel_text"]
                lbl_secondary = c["panel_label"]
                muted_color = c["muted_text"]
                # Frames a recorrer: video, audio, modelo_imagen, ajustes_extra, plantilla_brief, imgref
                frames_a_refrescar = [
                    "frame_video", "frame_audio", "frame_modelo_imagen",
                    "frame_pers_lora", "frame_plantilla_brief", "frame_imgref_inner",
                    "frame_neg_outer"
                ]
                for fname in frames_a_refrescar:
                    fr = getattr(self, fname, None)
                    if fr is None or not fr.winfo_exists():
                        continue
                    _recolor_labels(fr, lbl_color, lbl_secondary, muted_color)
                # También refrescar TODAS las pestañas del tabview directamente
                if hasattr(self, "tabview"):
                    for tab_name in ("⚙️ Ajustes Extra", "🎨 Estilos", "🚫 Negativos"):
                        try:
                            tab_frame = self.tabview.tab(tab_name)
                            _recolor_labels(tab_frame, lbl_color, lbl_secondary, muted_color)
                        except Exception as _e:
                            logger.debug(f"[silent] {_e}")
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        # Recolorear combos, opciones, segmentados
        try:
            _recolor_widgets(self, is_light)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # Recolorear labels específicos de entrada/estado/footer
        mt = c["muted_text"] if c else ("#4b5563" if is_light else "#9ca3af")
        pl = c["panel_label"] if c else ("#1f2937" if is_light else "#9ca3af")
        pt = c["panel_text"] if c else ("#111827" if is_light else "#e5e7eb")
        for attr in ("lbl_estado", "lbl_tokens", "lbl_idea_counter", "lbl_compat_inline"):
            try:
                w = getattr(self, attr, None)
                if w and w.winfo_exists():
                    w.configure(text_color=mt)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        for attr in ("lbl_autocomplete",):
            try:
                w = getattr(self, attr, None)
                if w and w.winfo_exists():
                    w.configure(text_color="#2563eb" if is_light else "#5a8aaa")
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        # Recolorear frame_entrada y frame_salida headers via _recolor_labels
        for attr in ("frame_entrada",):
            try:
                fr = getattr(self, attr, None)
                if fr and fr.winfo_exists():
                    _recolor_labels(fr, pt, pl, mt)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
    def _cmd_toggle_tema(self):
        """Alterna entre tema claro y oscuro.
        Nota: el theme.json custom puede no soportar light; en ese caso usamos blue por defecto."""
        try:
            actual = ctk.get_appearance_mode().lower()
            nuevo = "light" if actual == "dark" else "dark"
            try:
                ctk.set_appearance_mode(nuevo)
                self.set_estado(f"🌗 Tema {'claro' if nuevo == 'light' else 'oscuro'} (reinicia la app si se ve mal)",
                                "#3498db")
            except Exception as e:
                # Si falla, restaurar dark
                ctk.set_appearance_mode("dark")
                self.set_estado(f"⚠️ Tema light no compatible con theme.json actual ({e})", "#e67e22")
                nuevo = "dark"
            try: self._sesion_log(f"🌗 Cambió tema → {nuevo}")
            except Exception as e:
                logger.debug(f"[silent] {e}")
            # Persistir en preferencias
            try:
                prefs = self.store.cargar_preferencias()
                prefs["tema"] = nuevo
                self.store.guardar_preferencias(prefs)
            except Exception as e:
                logger.debug(f"[silent] {e}")
            # Aplicar colores adaptativos sin destruir layout
            try:
                self._apply_theme_colors()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        except Exception as e:
            self.set_estado(f"⚠️ Error cambiando tema: {e}", "#e74c3c")

    # EXTRAER POSITIVE / NEGATIVE

    def extraer_positive(self):
        texto = limpiar_marcadores(self.txt_salida.get("1.0", "end"))
        
        # Buscar marcador POSITIVE PROMPT:
        if "POSITIVE PROMPT:" in texto:
            bloque = texto.split("POSITIVE PROMPT:")[1]
            if "NEGATIVE PROMPT:" in bloque:
                return bloque.split("NEGATIVE PROMPT:")[0].strip(" \n*")
            return bloque.strip(" \n*")
        
        # Buscar marcador PROMPT: (sin POSITIVE)
        if "PROMPT:" in texto:
            bloque = texto.split("PROMPT:")[1]
            for marca in ["\nNEGATIVE\n", "\nNEGATIVE ", "\nNEGATIVE:", "\nNEGATIVE PROMPT:"]:
                if marca in bloque: bloque = bloque.split(marca)[0]
            for sep in ["\n1.", "\n2.", "\n3.", "\n──"]:
                if sep in bloque: bloque = bloque.split(sep)[0]
            return bloque.strip(" \n*")
        
        # Sin marcadores: buscar bloque NEGATIVE y devolver lo anterior
        # Marcas que indican inicio del negative
        marcas_neg = ["NEGATIVE PROMPT:", "NEGATIVE:", "\nNEGATIVE\n", "\nNEGATIVE ", "\nNEGATIVE:"]
        limpia = texto
        for marca in marcas_neg:
            if marca in limpia:
                limpia = limpia.split(marca, 1)[0]
                break
        
        # Si hay separadores de variantes al final, quitarlos
        for sep in ["\n1.", "\n2.", "\n3.", "\n──", "\n══"]:
            if sep in limpia:
                limpia = limpia.split(sep)[0]
        
        limpia = limpia.strip(" \n*:")
        if limpia and len(limpia.strip()) > 5:
            return limpia
        
        return None

    def extraer_negative(self):
        texto = limpiar_marcadores(self.txt_salida.get("1.0", "end"))
        for marca in ["NEGATIVE PROMPT:", "\nNEGATIVE\n", "\nNEGATIVE:", "\nNEGATIVE "]:
            if marca in texto:
                bloque = texto.split(marca, 1)[1]
                for sep in ["\n1.", "\n2.", "\n3.", "\n──"]:
                    if sep in bloque: bloque = bloque.split(sep)[0]
                return bloque.strip(" \n*:")
        return None

    def _copiar(self, tipo):
        try:
            try: self._sesion_log(f"📋 Copió: {tipo}")
            except Exception as e:
                logger.debug(f"[silent] {e}")
            tiene_neg = self._debe_mostrar_negatives()
            if tipo == "positivo":
                r = self.extraer_positive()
                if r:
                    pyperclip.copy(r)
                    label = "Prompt" if not tiene_neg else "Prompt Positivo"
                    self.set_estado(f"✅ {label} copiado.", "#2ecc71")
                else: self.set_estado("⚠️ No hay prompt generado.", "#e67e22")
            elif tipo == "negativo":
                if not tiene_neg:
                    self.set_estado("ℹ️ Este modelo no usa negative prompt.", "#3498db")
                    return
                r = self.extraer_negative()
                if r:
                    pyperclip.copy(r)
                    self.set_estado("✅ Prompt Negativo copiado.", "#2ecc71")
                else: self.set_estado("⚠️ No hay NEGATIVE PROMPT.", "#e67e22")
            elif tipo == "todo":
                t = self.txt_salida.get("1.0", "end").strip()
                if t:
                    pyperclip.copy(t)
                    self.set_estado("✅ Todo copiado.", "#2ecc71")
        except Exception as e:
            self.set_estado(f"⚠️ Error: {e}", "#e74c3c")

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
            sys_p = self._inyectar_specs_audio(sys_p)
            if brief: sys_p = sys_p + BRIEF_MODIFIER
            sys_p = self._inyectar_destino(sys_p)
            self.deepseek.reiniciar(sys_p)
            return

        if natural:
            if modo == "video":
                sys_p = SYSTEM_NATURAL_VIDEO_NSFW if es_nsfw else SYSTEM_NATURAL_VIDEO
            elif es_nsfw:
                sys_p = SYSTEM_NATURAL_NSFW
            else:
                sys_p = SYSTEM_NATURAL_SFW
            sys_p = self._inyectar_specs_modelo(sys_p)
            if brief: sys_p = sys_p + BRIEF_MODIFIER
            sys_p = self._inyectar_destino(sys_p)
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
            sys_p = self._inyectar_specs_modelo(sys_p)
            if brief: sys_p = sys_p + BRIEF_MODIFIER
            sys_p = self._inyectar_destino(sys_p)
            self.deepseek.reiniciar(sys_p)

    # HELPERS: Inyección de specs por modo

    def _inyectar_specs_modelo(self, system_prompt):
        modo = self.modo_var.get()
        if modo == "video":
            return self._inyectar_specs_video(system_prompt)
        if modo == "imagen":
            return self._inyectar_specs_imagen(system_prompt)
        return system_prompt

    def _inyectar_specs_video(self, system_prompt):
        specs = get_model_specs(self.combo_modelo_video.get())
        if not specs:
            return system_prompt
        motor = self.combo_modelo_video.get()
        max_c = specs["max_chars"]

        if max_c >= 4000:
            palabras_obj, detalle = "400-700", "EXTREMADAMENTE DETALLADO: múltiples shots con las 7 capas visuales"
        elif max_c >= 2000:
            palabras_obj, detalle = "220-360", "MUY DETALLADO: describe con precisión cada shot"
        else:
            palabras_obj, detalle = "130-210", "DETALLADO Y CONCISO: sujeto+acción"

        extra = f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        extra += f"REGLAS ESPECÍFICAS PARA {motor.upper()}:\n"
        extra += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        extra += f"• Estructura de prompt: {specs['prompt_formula']}\n"
        extra += f"• Ejemplo de referencia: {specs['prompt_ejemplo']}\n"
        extra += f"• OBJETIVO DE LONGITUD: {palabras_obj} palabras (~{max_c} caracteres máximo). {detalle}.\n"
        extra += f"• ⛔ LÍMITE ABSOLUTO INNEGOCIABLE: {max_c} caracteres totales.\n"
        extra += f"• Mejor para: {specs['best_for']}\n"

        if specs["has_audio"] and specs["audio_desc"]:
            extra += f"• ✅ Este modelo SOPORTA audio. Capacidades: {specs['audio_desc']}.\n"
            extra += f"• AÑADE línea 'Audio:' al final. Diálogos/voz-over EN CASTELLANO por defecto.\n"
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

    def _inyectar_specs_imagen(self, system_prompt):
        modelo = self.combo_modelo_imagen.get()
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

        extra = f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        extra += f"REGLAS ESPECÍFICAS PARA {modelo.upper()}:\n"
        extra += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
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

    def _inyectar_specs_formato(self, modelo, specs, extra):
        if specs.get("is_natural"):
            extra += "• TIPO: lenguaje natural descriptivo. NO uses tags sueltos separados por comas.\n"
            if specs["has_negative"]:
                extra += "\n⚠️ FORMATO DE SALIDA OBLIGATORIO ⚠️\nPROMPT: [descripción fluida]\nNEGATIVE PROMPT: [tags a evitar]\n"
            else:
                extra += "• Solo formato PROMPT: (sin negative)\n"
        else:
            extra += "• TIPO: tag-based Danbooru/SD. Usa comas, orden de tags SD.\n"
            es_comfyui_turbo = self._es_comfyui_turbo(self.plataforma_var.get(), modelo)
            if es_comfyui_turbo:
                extra += f"• ⛔ PLATAFORMA ComfyUI + MODELO TURBO: NO USES PESOS NUMÉRICOS tipo (tag:1.2). Solo tags limpios separados por comas. El CFG bajo (~1.0) hace que los pesos sean IGNORADOS o produzcan ruido. Ejemplo CORRECTO: 'close-up portrait, silver hair, detailed skin' | INCORRECTO: '(close-up portrait:1.3), (silver hair:1.2)'.\n"
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

    def _inyectar_template(self, motor, extra):
        tmpl = get_prompt_template(motor)
        if tmpl:
            extra += f"\n📋 PLANTILLA BASE RECOMENDADA:\n"
            extra += f"POSITIVE: {tmpl['positive_base']}\n"
            if tmpl.get("negative_base"):
                extra += f"NEGATIVE: {tmpl['negative_base']}\n"
            extra += "Usa esta plantilla como ESQUELETO. Rellena los campos {{entre llaves}} con los detalles.\n"
        return extra

    def _inyectar_specs_audio(self, system_prompt):
        if not hasattr(self, 'combo_modelo_audio'): return system_prompt
        motor = self.combo_modelo_audio.get()
        if es_separador(motor): return system_prompt
        specs = get_audio_model_specs(motor)
        if not specs: return system_prompt

        instrumental = self.switch_instrumental_var.get() if hasattr(self, 'switch_instrumental_var') else False

        extra = f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        extra += f"REGLAS ESPECÍFICAS PARA {motor.upper()}:\n"
        extra += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        extra += f"• Rating del motor: ⭐ {specs['nota']}/5\n"
        extra += f"• Mejor para: {specs['best_for']}\n"
        extra += f"• Duración máxima: {specs['duracion_max_min']} minutos\n"

        if specs.get("usa_tags_estructurales"): extra += "• ✅ USA tags estructurales obligatorios: [Intro] [Verse 1] [Chorus] etc.\n"
        else: extra += "• ❌ NO usa tags estructurales. Letra directa.\n"

        if specs.get("has_instrumental_toggle"): extra += f"• Tiene toggle Vocal/Instrumental. Estado actual: {'INSTRUMENTAL' if instrumental else 'VOCAL'}.\n"
        if instrumental: extra += "• ⚠️ MODO INSTRUMENTAL ACTIVO: NO generes letra.\n"

        extra += f"• Ejemplo de estilo: {specs['prompt_ejemplo_estilo']}\n"
        if specs.get("limitaciones"): extra += f"• Limitaciones: {specs['limitaciones']}\n"

        # Inyectar preferencias de emoción, voz e idioma del usuario
        emocion = self.emocion_var.get() if hasattr(self, 'emocion_var') else ""
        if emocion and emocion != "— Emoción —":
            extra += f"• 🎭 EMOCIÓN SOLICITADA: {emocion}. Adapta el mood, tempo y tonalidad a esta emoción.\n"
        voz = self.voz_var.get() if hasattr(self, 'voz_var') else ""
        if voz and voz != "— Voz —":
            extra += f"• 🎤 VOZ SOLICITADA: {voz}. Especifica este tipo de voz en el campo de estilo.\n"
        idioma = self.idioma_audio_var.get() if hasattr(self, 'idioma_audio_var') else ""
        if idioma and idioma != "— Idioma —":
            extra += f"• 🌐 IDIOMA DE LA LETRA: {idioma}. Escribe TODA la letra en este idioma.\n"

        extra += REGLAS_APROVECHAR_BUDGET
        return system_prompt + extra

    def _inyectar_destino(self, system_prompt):
        dest = self.destino_var.get() if hasattr(self, 'destino_var') else ""
        if not dest or dest == "— Personal —":
            return system_prompt

        reglas_destino = {
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

        regla = reglas_destino.get(dest, "")
        if regla:
            return system_prompt + f"\n\n📢 {regla}\n"
        return system_prompt

    # CONSTRUIR MODELO INFO / PETICION

    def construir_modelo_info(self):
        # Cacheo simple: si no cambió la config, devolver cache
        clave_cache = (
            self.modo_var.get(),
            self.modelo_imagen_valido() if self.modo_var.get() == "imagen" else "",
            self.modelo_video_valido() if self.modo_var.get() == "video" else "",
            self.combo_modelo_audio.get() if self.modo_var.get() == "audio" and hasattr(self, 'combo_modelo_audio') else "",
            self.ratio_actual(),
            self.personaje_activo(),
            self.lora_activo(),
            self.destino_var.get(),
        )

        # Si no ha cambiado, devolver cache
        if hasattr(self, '_cache_modelo_info') and getattr(self, '_cache_modelo_clave', None) == clave_cache:
            return self._cache_modelo_info

        info = ""
        modo = self.modo_var.get()
        if modo == "video": info = f" Motor: {self.modelo_video_valido()}. Duración: {self.duracion_var.get()}."
        elif modo == "audio":
            motor_a = self.combo_modelo_audio.get() if hasattr(self, 'combo_modelo_audio') else ""
            if motor_a and not es_separador(motor_a): info = f" Motor audio: {motor_a}."
        else:
            m = self.modelo_imagen_valido()
            if m: info = f" Modelo: {m}."

        ratio = self.ratio_actual()
        if ratio: info += f" Ratio: {ratio}."
        pers = self.personaje_activo()
        if pers: info += f" Personaje: {pers}."
        lora = self.lora_activo()
        if lora: info += f" LoRA: {lora}."
        dest = self.destino_var.get()
        if dest and dest != "— Personal —": info += f" Destino: {dest}."

        # Audio: añadir emoción, voz, idioma si están seleccionados
        if modo == "audio":
            em = self.emocion_var.get() if hasattr(self, 'emocion_var') else ""
            if em and em != "— Emoción —": info += f" Emoción: {em}."
            vz = self.voz_var.get() if hasattr(self, 'voz_var') else ""
            if vz and vz != "— Voz —": info += f" Voz: {vz}."
            id_a = self.idioma_audio_var.get() if hasattr(self, 'idioma_audio_var') else ""
            if id_a and id_a != "— Idioma —": info += f" Idioma letra: {id_a}."

        # Guardar en cache
        self._cache_modelo_info = info
        self._cache_modelo_clave = clave_cache
        return info

    def _construir_peticion(self, idea, modo_letra):
        base = f"MODO {modo_letra}: Genera prompt para: '{idea}'. Estilos: {self.estilos_texto()}."

        # Forzar formato según modo tag-based o natural
        if self.modo_var.get() == "imagen" and not self.is_natural_mode():
            base += " FORMATO OBLIGATORIO: tags separados por comas con pesos (tag:1.2). NO prosa fluida. Tags densos de 2-5 palabras. 5-10 pesos en POSITIVE, 3-6 en NEGATIVE."

        # ADN visual activo: inyectar como rasgos inmutables
        if getattr(self, '_anclaje_visual', None):
            base += (f"\n\n⚓ ADN VISUAL INMUTABLE — INCLUYE LITERALMENTE estos rasgos en el POSITIVE PROMPT (no los modifiques):\n"
                     f"{self._anclaje_visual}\n"
                     f"⚠️ Estos rasgos son OBLIGATORIOS y deben aparecer en el output.")

        return base + self.construir_modelo_info()

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

    # MODO CAMBIO

    def _on_modo_cambio(self):
        """Cambia la UI según modo (imagen/video/audio). No opera si Focus está activo."""
        # Si Focus está activo, no tocar layout (tabview está oculto)
        if getattr(self, '_modo_focus_activo', False):
            return
        modo = self.modo_var.get()
        try: self._sesion_log(f"🎛 Cambió modo → {modo.upper()}")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        self.lbl_img_model_info.pack_forget()

        # Limpiar resultado y memoria — los prompts del modo anterior no aplican
        try:
            if hasattr(self, 'txt_salida') and self.txt_salida.get("1.0", "end").strip():
                self.actualizar_salida("")
            self.reiniciar_memoria()
            # Limpiar ADN visual si estaba activo (suele ser específico de imagen)
            if getattr(self, '_anclaje_visual', None) and modo != "imagen":
                self._anclaje_visual = None
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # Sincronizar SegmentedButton si existe
        if hasattr(self, '_seg_modo'):
            mapa_inv = {"imagen": "Imagen", "video": "Vídeo", "audio": "Audio"}
            try: self._seg_modo.set(mapa_inv.get(modo, "Imagen"))
            except: pass

        if modo == "video":
            self.combo_plataforma.configure(values=PLATAFORMAS_VIDEO_LISTA)
            self.plataforma_var.set("SeaArt Video")

            self._safe_pack(self.frame_video, pady=3, padx=20, fill="x", before=self.tabview)
            if hasattr(self, 'frame_audio'): self.frame_audio.pack_forget()
            self.frame_modelo_imagen.pack_forget()
            self.frame_destino.pack_forget()  # Ya integrado en frame_video

            self.switch_nsfw.pack(side="right", padx=20)
            self.btn_vision.configure(text="👁 Analizar", state="normal")
            self.btn_img_prompt.configure(text="🎯 Img→Prompt", state="normal")
            self._construir_checkboxes(ESTILOS_VIDEO)
            self._actualizar_motores_video()

        elif modo == "audio":
            self.combo_plataforma.configure(values=PLATAFORMAS_AUDIO_LISTA)
            self.plataforma_var.set("Suno")

            self._safe_pack(self.frame_audio, pady=3, padx=20, fill="x", before=self.tabview)
            self.frame_video.pack_forget()
            self.frame_modelo_imagen.pack_forget()
            self.frame_destino.pack_forget()  # Ya integrado en frame_audio

            self.switch_nsfw.pack_forget()
            self.btn_vision.configure(text="👁 (no aplica)", state="disabled")
            self.btn_img_prompt.configure(text="🎯 (no aplica)", state="disabled")
            self._construir_checkboxes(ESTILOS_AUDIO)
            self._on_motor_audio_cambio()

        else: # Imagen
            self.combo_plataforma.configure(values=PLATAFORMAS_IMAGEN_LISTA)
            self.plataforma_var.set("SeaArt / Tensor.Art")

            self.frame_video.pack_forget()
            if hasattr(self, 'frame_audio'): self.frame_audio.pack_forget()
            self._safe_pack(self.frame_modelo_imagen, pady=3, padx=20, fill="x", before=self.tabview)
            self.frame_destino.pack_forget()  # Ya integrado en frame_modelo_imagen

            self.switch_nsfw.pack(side="right", padx=20)
            self.btn_vision.configure(text="👁 Analizar", state="normal")
            self.btn_img_prompt.configure(text="🎯 Img→Prompt", state="normal")
            self.combo_ratio.set("1:1")
            self.ratio_var.set("1:1")
            self._construir_checkboxes(ESTILOS_IMAGEN)
            self._on_modelo_imagen_cambio()

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

        # Modo imagen: ocultar/mostrar selector de modelo según plataforma
        plat_con_modelos = tuple(MODELOS_POR_PLATAFORMA_IMAGEN.keys())
        if plat in plat_con_modelos:
            # Lista de modelos según plataforma (cada plataforma su lista)
            modelos_de_plat = MODELOS_POR_PLATAFORMA_IMAGEN.get(plat, MODELOS_IMAGEN_FLAT)
            self.combo_modelo_imagen.configure(values=modelos_de_plat)
            actual = self.combo_modelo_imagen.get()
            if actual not in modelos_de_plat or actual.startswith("──"):
                primer_modelo = next((m for m in modelos_de_plat if not m.startswith("──")), "")
                if primer_modelo:
                    self.combo_modelo_imagen.set(primer_modelo)

            self._safe_pack(self.frame_modelo_imagen, pady=3, padx=20, fill="x", before=self.tabview)
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
            self._safe_pack(self.lbl_img_model_info, fill="x", padx=30, pady=(0, 2), before=self.tabview)
            self.set_estado(f"🎬 {motor_name}", "#3498db")

            # Tooltip rico para modelos de vídeo (similar a imagen)
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
        # Mejora 14: log sesión
        try: self._sesion_log(f"🎨 Cambió modelo imagen → {modelo_name}")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        # Refrescar aviso de compatibilidad LoRA
        try: self._actualizar_lora_trigger_visible()
        except Exception as e:
            logger.debug(f"[silent] {e}")
        # Refrescar validador Flux/SD3.5 (puede haber prompt previo con pesos)
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

            # Tooltip rico — destruir el anterior y crear uno nuevo
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
            # Badges visuales según características del modelo
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
            self._safe_pack(self.lbl_img_model_info, fill="x", padx=30, pady=(0, 2), before=self.tabview)

            # Generar consejo contextual según situación actual
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
        # Recomendador LoRAs al FINAL (con delay 500ms para que no lo sobrescriba consejo contextual)
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
            self._safe_pack(self.lbl_img_model_info, fill="x", padx=30, pady=(0, 2), before=self.tabview)
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

    # MODEL SPECS / NATURAL MODE HELPERS

    def get_current_model_specs(self):
        modo = self.modo_var.get()
        if modo == "video": return get_model_specs(self.combo_modelo_video.get())
        if modo == "audio" and hasattr(self, 'combo_modelo_audio'): return get_audio_model_specs(self.combo_modelo_audio.get())
        if modo == "imagen": return get_image_model_specs(self.combo_modelo_imagen.get())
        return None

    def is_natural_mode(self):
        modo = self.modo_var.get()
        plat = self.plataforma_var.get()
        if modo == "audio": return True
        if modo == "video": return PLATAFORMAS_VIDEO.get(plat, "natural") == "natural"
        # Solo consultar modelo imagen si la plataforma tiene selector de modelos
        plat_con_modelos = ("SeaArt / Tensor.Art", "ComfyUI / A1111 / Forge")
        if plat in plat_con_modelos:
            modelo = self.combo_modelo_imagen.get() if hasattr(self, 'combo_modelo_imagen') else ""
            if modelo and not es_separador(modelo):
                specs_img = get_image_model_specs(modelo)
                if specs_img and specs_img.get("is_natural"): return True
        return PLATAFORMAS_IMAGEN.get(plat, "sd") == "natural"

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

        # Imagen ref: visible en imagen y vídeo, oculto en audio
        if hasattr(self, 'frame_imgref_inner'):
            if modo != "audio":
                try: self.frame_imgref_inner.pack(fill="x", pady=(1, 2))
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
        modo = self.modo_var.get()
        if modo == "audio": return False
        if modo == "video":
            specs = get_model_specs(self.combo_modelo_video.get())
            if specs: return specs.get("has_negative", False)
            return PLATAFORMAS_VIDEO.get(self.plataforma_var.get(), "sd") == "sd"

        plat = self.plataforma_var.get()
        plat_con_modelos = ("SeaArt / Tensor.Art", "ComfyUI / A1111 / Forge")
        if plat in plat_con_modelos:
            modelo = self.combo_modelo_imagen.get() if hasattr(self, 'combo_modelo_imagen') else ""
            if modelo and not es_separador(modelo):
                # Caso especial: modelos Turbo en ComfyUI NO aceptan negative ni pesos
                if self._es_comfyui_turbo(plat, modelo):
                    return False
                specs_img = get_image_model_specs(modelo)
                if specs_img: return specs_img.get("has_negative", False)
        return PLATAFORMAS_IMAGEN.get(plat, "sd") == "sd"

    def _es_comfyui_turbo(self, plataforma=None, modelo=None):
        """Detecta si estamos en ComfyUI con un modelo Turbo (CFG~1.0, sin negative ni pesos)."""
        if plataforma is None:
            plataforma = self.plataforma_var.get() if hasattr(self, 'plataforma_var') else ""
        if modelo is None:
            modelo = self.combo_modelo_imagen.get() if hasattr(self, 'combo_modelo_imagen') else ""
        es_comfyui = "ComfyUI" in plataforma or "A1111" in plataforma or "Forge" in plataforma
        # Modelos Turbo que en modo raw (ComfyUI) no aceptan negative ni pesos
        modelos_turbo = ("Z Image Turbo", "Realities Edge XL Turbo V7", "SDXL Turbo", "FLUX.1 Schnell")
        es_turbo = any(m in modelo for m in modelos_turbo)
        return es_comfyui and es_turbo

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
        self._ocultar_ideas()
        if not ideas:
            return
        is_lt = ctk.get_appearance_mode().lower() == "light"
        ideas_frame = ctk.CTkFrame(self, fg_color="#e8e8e8" if is_lt else "#0f1318")
        ideas_frame.pack(pady=(6, 0), padx=16, fill="x", before=self.frame_entrada)

        hdr = ctk.CTkFrame(ideas_frame, fg_color="#e0e0e0" if is_lt else "#1a2a1a", corner_radius=6, height=26)
        hdr.pack(fill="x", pady=(0, 4), padx=4)
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Ideas — pulsa para copiar o generar:",
                     font=ctk.CTkFont(size=11, weight="bold"), text_color="#f39c12").pack(side="left", padx=8)
        btn_cerrar = ctk.CTkButton(hdr, text="X", width=22, height=20, fg_color="transparent",
                                     hover_color="#dc2626" if is_lt else "#3a1a1a",
                                     text_color="#6b7280" if is_lt else "#888888",
                                     font=ctk.CTkFont(size=11), command=self._ocultar_ideas)
        btn_cerrar.pack(side="right", padx=4)
        btn_cerrar.bind("<Button-1>", lambda e: self._ocultar_ideas())

        for i, idea in enumerate(ideas):
            idea_texto = idea.strip()
            card = ctk.CTkFrame(ideas_frame, fg_color="#f0f0f0" if is_lt else "#0f1620", corner_radius=6)
            card.pack(fill="x", pady=2, padx=4)
            lbl = ctk.CTkLabel(card, text=f"#{i+1}: {idea_texto}", font=ctk.CTkFont(size=11),
                                anchor="w", justify="left", wraplength=900,
                                text_color="#1f2937" if is_lt else "#e5e7eb")
            lbl.pack(side="left", fill="x", expand=True, padx=8, pady=6)
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(side="right", padx=4, pady=4)

            def _copiar(t=idea_texto, n=i+1):
                pyperclip.copy(t)
                self.set_estado(f" Idea #{n} copiada", "#2ecc71")

            def _aplicar(t=idea_texto, n=i+1):
                self.txt_idea.delete("1.0", "end")
                self.txt_idea.insert("1.0", t)
                self._ocultar_ideas()
                self.set_estado(f" Idea #{n} aplicada", "#3498db")

            def _generar(t=idea_texto):
                self.txt_idea.delete("1.0", "end")
                self.txt_idea.insert("1.0", t)
                self._ocultar_ideas()
                self.cmd_prompt()

            ctk.CTkButton(btn_frame, text="Copy", width=55, height=28, fg_color="#2563eb" if is_lt else "#1e3a8a",
                          hover_color="#1d4ed8" if is_lt else "#162d49", font=ctk.CTkFont(size=10),
                          command=_copiar).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Apply", width=55, height=28, fg_color="#7c3aed",
                          hover_color="#5d2ab5", font=ctk.CTkFont(size=10),
                          command=_aplicar).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Generate", width=70, height=28, fg_color="#15803d",
                          hover_color="#166534" if is_lt else "#0d5026", font=ctk.CTkFont(size=10, weight="bold"),
                          command=_generar).pack(side="left", padx=2)

        self._ideas_frame = ideas_frame
        self.update()

    def _parsear_variaciones(self, texto):
        texto_limpio = re.sub(r'[\*#]', '', texto)
        patron = r'\n\s*(?:Variaci[oó]n|Prompt)?\s*\d+[\.\)\-:]\s*|\n\s*---\s*\n'
        bloques = re.split(patron, '\n' + texto_limpio, flags=re.IGNORECASE)

        resultado = []
        for b in bloques:
            b = b.strip()
            if b and ("PROMPT:" in b.upper() or "ESTILO:" in b.upper() or len(b) > 60):
                resultado.append(b)

        if len(resultado) <= 1:
            bloques_alt = re.split(r'\n(?=(?:POSITIVE )?PROMPT:)', texto_limpio, flags=re.IGNORECASE)
            resultado = [b.strip() for b in bloques_alt if len(b.strip()) > 50]

        return resultado if len(resultado) > 1 else []

    def _mostrar_variaciones(self, variaciones):
        if hasattr(self, '_variaciones_frame'):
            try:
                self._variaciones_frame.pack_forget()
                for w in self._variaciones_frame.winfo_children(): w.destroy()
                self._variaciones_frame.destroy()
            except: pass
            self._variaciones_frame = None

        if not variaciones:
            return
        is_lt = ctk.get_appearance_mode().lower() == "light"
        vf = ctk.CTkFrame(self, fg_color="#e8e8e8" if is_lt else "#0f1318")
        vf.pack(pady=(6, 0), padx=16, fill="x", before=self.frame_entrada)

        hdr = ctk.CTkFrame(vf, fg_color="#e0e0e0" if is_lt else "#1a2a1a", corner_radius=6, height=26)
        hdr.pack(fill="x", pady=(0, 4), padx=4)
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Variaciones — copia completo, solo POS o solo NEG:",
                     font=ctk.CTkFont(size=11, weight="bold"), text_color="#f39c12").pack(side="left", padx=8)
        btn_cerrar = ctk.CTkButton(hdr, text="X", width=22, height=20, fg_color="transparent",
                                     hover_color="#dc2626" if is_lt else "#3a1a1a",
                                     text_color="#6b7280" if is_lt else "#888888",
                                     font=ctk.CTkFont(size=11), command=self._ocultar_ideas)
        btn_cerrar.pack(side="right", padx=4)

        row1 = ctk.CTkFrame(vf, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 2), padx=4)
        ctk.CTkLabel(row1, text="Copiar completo:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#f39c12").pack(side="left", padx=(4, 6))
        colores = (
            ["#2563eb", "#15803d", "#7c3aed"] if is_lt else
            ["#1a4a7a", "#1a7a3c", "#4a1a7a"]
        )
        for i, var in enumerate(variaciones):
            def ct(v=var, n=i+1):
                pyperclip.copy(v)
                self.set_estado(f" Variacion #{n} copiada", "#2ecc71")
            ctk.CTkButton(row1, text=f"#{i+1}", width=50, height=24, fg_color=colores[i % len(colores)],
                          hover_color="#d1d5db" if is_lt else "#333333", font=ctk.CTkFont(size=11, weight="bold"), command=ct).pack(side="left", padx=2)

        row2 = ctk.CTkFrame(vf, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 2), padx=4)
        ctk.CTkLabel(row2, text="Solo POSITIVE:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#2ecc71").pack(side="left", padx=(4, 6))
        for i, var in enumerate(variaciones):
            def cp(v=var, n=i+1):
                p = self._extraer_pos_de_bloque(v)
                if p:
                    pyperclip.copy(p)
                    self.set_estado(f" POSITIVE #{n} copiado", "#2ecc71")
                else:
                    self.set_estado(f" No se encontro POSITIVE en #{n}", "#e74c3c")
            ctk.CTkButton(row2, text=f"#{i+1}", width=50, height=24, fg_color="#15803d" if is_lt else "#1a5a2a",
                          hover_color="#166534" if is_lt else "#0f3a1a", font=ctk.CTkFont(size=11, weight="bold"), command=cp).pack(side="left", padx=2)

        if self._debe_mostrar_negatives():
            row3 = ctk.CTkFrame(vf, fg_color="transparent")
            row3.pack(fill="x", padx=4)
            ctk.CTkLabel(row3, text="Solo NEGATIVE:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#e74c3c").pack(side="left", padx=(4, 6))
            for i, var in enumerate(variaciones):
                def cn(v=var, n=i+1):
                    n_text = self._extraer_neg_de_bloque(v)
                    if n_text:
                        pyperclip.copy(n_text)
                        self.set_estado(f" NEGATIVE #{n} copiado", "#2ecc71")
                    else:
                        self.set_estado(f" No se encontro NEGATIVE en #{n}", "#e74c3c")
                ctk.CTkButton(row3, text=f"#{i+1}", width=50, height=24, fg_color="#dc2626" if is_lt else "#5a1a1a",
                              hover_color="#b91c1c" if is_lt else "#3a0f0f", font=ctk.CTkFont(size=11, weight="bold"), command=cn).pack(side="left", padx=2)

        self._variaciones_frame = vf
        self.update()

    def _extraer_pos_de_bloque(self, bloque):
        limpio = limpiar_marcadores(bloque)
        p = limpio
        if "NEGATIVE PROMPT:" in p: p = p.split("NEGATIVE PROMPT:")[0]
        elif "NEGATIVE:" in p: p = p.split("NEGATIVE:")[0]

        if "POSITIVE PROMPT:" in p: return p.split("POSITIVE PROMPT:")[1].strip(" \n*")
        if "PROMPT:" in p: return p.split("PROMPT:")[1].strip(" \n*")
        return p.strip(" \n*")

    def _extraer_neg_de_bloque(self, bloque):
        limpio = limpiar_marcadores(bloque)
        if "NEGATIVE PROMPT:" in limpio: return limpio.split("NEGATIVE PROMPT:")[1].strip(" \n*")
        if "NEGATIVE:" in limpio: return limpio.split("NEGATIVE:")[1].strip(" \n*")

        global_neg = self.extraer_negative()
        if global_neg:
            return global_neg
        return None

    # COMANDOS & WORKERS

    def _recortar_si_excede(self, texto, max_chars):
        """Recorta el POSITIVE y NEGATIVE del prompt si excede el límite, preservando estructura."""
        if not max_chars or not texto:
            return texto
        # Extraer POSITIVE y NEGATIVE
        try:
            import re
            m_pos = re.search(r'(?:POSITIVE\s+)?PROMPT\s*:\s*(.+?)(?=\n\s*NEGATIVE|$)', texto, re.DOTALL | re.IGNORECASE)
            m_neg = re.search(r'NEGATIVE\s+PROMPT\s*:\s*(.+?)$', texto, re.DOTALL | re.IGNORECASE)
            if not m_pos:
                return texto
            pos = m_pos.group(1).strip()
            neg = m_neg.group(1).strip() if m_neg else ""

            # Límite NEGATIVE: SeaArt ~1500 chars
            NEGATIVE_MAX = 1500
            neg_recortado = False
            if len(neg) > NEGATIVE_MAX:
                partes_neg = neg.split(",")
                neg = ""
                for p in partes_neg:
                    p_stripped = p.strip()
                    if len(neg) + len(p_stripped) + 2 > NEGATIVE_MAX:
                        break
                    neg += (", " if neg else "") + p_stripped
                neg_recortado = True

            if len(pos) <= max_chars and not neg_recortado:
                return texto

            # Recortar pos preservando tags completos (separados por comas)
            pos_recortado = pos
            if len(pos) > max_chars:
                partes = pos.split(",")
                pos_recortado = ""
                for p in partes:
                    p_stripped = p.strip()
                    if len(pos_recortado) + len(p_stripped) + 2 > max_chars:
                        break
                    pos_recortado += (", " if pos_recortado else "") + p_stripped

            nuevo = f"POSITIVE PROMPT: {pos_recortado}"
            if neg:
                nuevo += f"\nNEGATIVE PROMPT: {neg}"
            return nuevo
        except Exception:
            return texto

    def _worker_ia(self, peticion, es_ideas=False, es_variaciones=False):
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
            if not es_ideas:
                self.after(0, lambda: self.actualizar_salida(texto))
            self.after(0, lambda: self.set_estado(f"✅ Completado ({cerebro_elegido}).", "#2ecc71"))
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
            elif es_variaciones: self.after(0, lambda: self._mostrar_variaciones(self._parsear_variaciones(texto)))
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

    def cmd_ideas(self):
        self._ocultar_ideas()
        self.reiniciar_memoria()  # Evitar contaminación del historial previo
        idea = self.txt_idea.get("1.0", "end").strip()
        tipo = "canción" if self.modo_var.get() == "audio" else "vídeo" if self.modo_var.get() == "video" else "imagen"
        peticion = f"MODO A: Devuelve SOLO 3 ideas, una por línea con formato '1. Idea', '2. Idea', '3. Idea'. Tema: {tipo} con estilos: '{self.estilos_texto()}'."
        if idea: peticion += f" Tema: {idea}."

        self.set_estado("⏳ Generando ideas...", "#f39c12")
        self._sesion_log(f"💡 Pidió ideas · tema: \"{(idea or 'sin tema')[:40]}\"")
        self.toggle_botones(False)
        threading.Thread(target=self._worker_ia, args=(peticion, True), daemon=True).start()

    def cmd_prompt(self):
        self._ocultar_ideas()
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea:
            self.set_estado("⚠️ Escribe o selecciona una idea primero.", "#e67e22")
            return
        # Detectar NSFW automáticamente
        self._detectar_nsfw_auto(idea)
        # Mejora 14: log sesión
        try:
            modelo = (self.combo_modelo_imagen.get() if self.modo_var.get() == "imagen" else
                      self.combo_modelo_video.get() if self.modo_var.get() == "video" else
                      self.combo_modelo_audio.get())
            self._sesion_log(f"✨ Generó prompt · idea: \"{idea[:60]}{'…' if len(idea) > 60 else ''}\" · modelo: {modelo}")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        self.set_estado("⏳ Compilando prompt...", "#f39c12")
        self.toggle_botones(False)
        threading.Thread(target=self._worker_prompt_traduccion, args=(idea,), daemon=True).start()

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
            self.set_estado("⚠️ Escribe o selecciona una idea primero.", "#e67e22")
            return
        try:
            modelo = (self.combo_modelo_imagen.get() if self.modo_var.get() == "imagen" else
                      self.combo_modelo_video.get() if self.modo_var.get() == "video" else
                      self.combo_modelo_audio.get())
            self._sesion_log(f"⚡ Quick: idea: \"{idea[:60]}{'…' if len(idea) > 60 else ''}\" · modelo: {modelo}")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        self.set_estado("⚡ Quick generate...", "#d97706")
        self.toggle_botones(False)
        threading.Thread(target=self._worker_prompt_quick, args=(idea,), daemon=True).start()

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

    def cmd_variaciones(self):
        self._ocultar_ideas()
        idea, pos = self.txt_idea.get("1.0", "end").strip(), self.extraer_positive()

        formato_extra = " OBLIGATORIO: En CADA variación escribe 'POSITIVE PROMPT:' y luego 'NEGATIVE PROMPT:'." if self._debe_mostrar_negatives() else ""

        # Forzar formato tag-based si aplica
        if self.modo_var.get() == "imagen" and not self.is_natural_mode():
            formato_extra += " FORMATO: tags separados por comas con pesos (tag:1.2). NO prosa fluida. Las 3 variaciones deben usar el MISMO formato de tags."

        if pos and len(pos) > 10:
            peticion = f"MODO C: Genera 3 variaciones de este prompt. Base: '{pos}'. Estilos: {self.estilos_texto()}." + formato_extra
            if idea: peticion += f" Incorpora también: {idea}."
        elif idea:
            peticion = self._construir_peticion(idea, "C") + formato_extra
        else:
            self.set_estado("⚠️ Necesitas una idea o prompt previo.", "#e67e22")
            return

        self.set_estado("🔀 Generando 3 variaciones...", "#f39c12")
        self._sesion_log(f"🔀 Generó 3 variaciones · base: \"{(pos or idea)[:50]}…\"")
        self.toggle_botones(False)
        threading.Thread(target=self._worker_ia, args=(peticion, False, True), daemon=True).start()

    def cmd_vision(self):
        if self.modo_var.get() == "audio": return self.set_estado("ℹ️ El análisis de imagen no aplica en modo audio.", "#3498db")
        if not self.imagen_cargada: return self.set_estado("⚠️ Carga una imagen primero.", "#e67e22")
        self._ocultar_ideas()
        self._sesion_log("👁 Analizó imagen de referencia")
        self.toggle_botones(False)
        threading.Thread(target=self._worker_vision, daemon=True).start()

    def cmd_imagen_a_prompt(self):
        if self.modo_var.get() == "audio" or not self.imagen_cargada: return
        self._ocultar_ideas()
        try: self._sesion_log("🎯 Img→Prompt: generó prompt desde imagen")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        self.toggle_botones(False)
        threading.Thread(target=self._worker_imagen_a_prompt, daemon=True).start()

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

    def _cmd_convertir_a_video(self):
        """Convierte un prompt de imagen a formato de vídeo."""
        texto = self.txt_salida.get("1.0", "end").strip()
        if not texto or len(texto) < 20:
            return self.set_estado("⚠️ Genera un prompt de imagen primero.", "#e67e22")
        try: self._sesion_log("🔄 Convirtió prompt imagen → vídeo")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        pos = self.extraer_positive() or texto
        self.set_estado("🔄 Convirtiendo prompt de imagen a vídeo...", "#f39c12")
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
                    self._on_modo_cambio()
                    self.actualizar_salida(resultado)
                    self.guardar_en_historial(resultado)
                    self.set_estado(f"🔄 Prompt convertido a vídeo ({motor_vid})", "#2ecc71")
                    self.toggle_botones(True)
                    self._sonar_completado()
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _menu_refinar_especifico(self, event=None):
        """Menú con 5 opciones de refinamiento específico."""
        texto = self.txt_salida.get("1.0", "end").strip()
        if not texto or len(texto) < 20:
            return self.set_estado("⚠️ Genera un prompt primero.", "#e67e22")

        import tkinter as tk
        is_lt = ctk.get_appearance_mode().lower() == "light"
        menu = tk.Menu(self, tearoff=0,
                       bg="#f0f0f0" if is_lt else "#1a1a2a",
                       fg="#111827" if is_lt else "white",
                       activebackground="#dbeafe" if is_lt else "#2a4a6a",
                       activeforeground="#111827" if is_lt else "white",
                       font=("Segoe UI", 10), borderwidth=1)

        opciones = [
            ("🎬 Más cinematográfico",   "más cinematográfico, con encuadre épico, movimientos de cámara dramáticos, iluminación de película"),
            ("👤 Más detalle facial",    "más detalle facial, ojos detallados, textura de piel realista, expresión emotiva, pelo individual"),
            ("💡 Mejor iluminación",     "iluminación más profesional, luces volumétricas, ambiente atmosférico, dirección de luz definida, sombras dramáticas"),
            ("⚡ Más impacto visual",    "más impacto visual, composición más fuerte, elementos contrastantes, paleta de colores definida, foco visual claro"),
            ("✂️ Simplificar",           "más simple y conciso. Elimina redundancias, tags innecesarios. Mantén solo lo esencial."),
            ("🌈 Cambiar paleta",        "con una paleta de colores diferente y más interesante. Sugiere una combinación cromática específica"),
            ("🔍 Más detalle técnico",   "con detalles técnicos: sampler, lente, distancia focal, tipo de cámara, resolución específica"),
        ]
        for label, instruccion in opciones:
            menu.add_command(label=label, command=lambda i=instruccion: self._refinar_con_instruccion(i))

        try:
            x = event.x_root if event else self.winfo_pointerx()
            y = event.y_root if event else self.winfo_pointery()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _refinar_con_instruccion(self, instruccion_extra):
        """Refina el prompt con una instrucción específica."""
        texto = self.txt_salida.get("1.0", "end").strip()
        if not texto: return

        self.set_estado(f"🔁 Refinando: {instruccion_extra[:40]}...", "#f39c12")
        self.toggle_botones(False)

        es_tag_based = not self.is_natural_mode()
        formato = "Mantén formato tags con pesos (tag:1.2)." if es_tag_based else "Mantén formato lenguaje natural descriptivo."

        peticion = (
            f"Refina este prompt aplicando esta instrucción específica: {instruccion_extra}\n\n"
            f"PROMPT ORIGINAL:\n{texto}\n\n"
            f"REGLAS:\n"
            f"- {formato}\n"
            f"- NO cambies el sujeto principal ni la idea central.\n"
            f"- Aplica la instrucción de forma específica y notable.\n"
            f"- Responde SOLO con el prompt refinado, sin explicaciones.\n"
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.5, max_tokens=2000)
                resp = limpiar_marcadores(resp)
                def _aplicar():
                    self.actualizar_salida(resp)
                    self.guardar_en_historial(resp)
                    self.set_estado("✅ Prompt refinado con instrucción específica", "#2ecc71")
                    self.toggle_botones(True)
                    self._sonar_completado()
                self.after(0, _aplicar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_iteracion(self):
        """Genera 5 variantes del prompt cambiando solo 1 elemento (iluminación, encuadre, etc)."""
        texto = self.txt_salida.get("1.0", "end").strip()
        if not texto or len(texto) < 20:
            return self.set_estado("⚠️ Genera un prompt primero para iterar.", "#e67e22")
        try: self._sesion_log("🔂 Iterar: abrió ventana de variación 1 elemento")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        # Ventana selección elemento a variar
        sel = GPromptWindow(self)
        sel.title("🔂 Iteración")
        sel.geometry("400x300")
        sel.transient(self)

        is_lt = ctk.get_appearance_mode().lower() == "light"
        ctk.CTkLabel(sel, text="🔂 Modo Iteración", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 3))
        ctk.CTkLabel(sel, text="Genera 5 variantes cambiando SOLO un elemento:",
                     font=ctk.CTkFont(size=11), text_color="#6b7280" if is_lt else "#888888").pack(pady=(0, 12))

        opciones = [
            ("💡 Iluminación", "iluminación (tipo, dirección, color)"),
            ("📐 Encuadre", "encuadre y plano de cámara"),
            ("🎨 Paleta de colores", "paleta de colores"),
            ("🌫 Atmósfera/mood", "atmósfera y mood"),
            ("🎬 Estilo/género", "estilo artístico / género"),
        ]
        for label, descripcion in opciones:
            btn = ctk.CTkButton(sel, text=label, width=300, height=32,
                                fg_color="#2563eb" if is_lt else "#1a3a5a",
                                hover_color="#1d4ed8" if is_lt else "#2a4a6a",
                                font=ctk.CTkFont(size=11),
                                command=lambda d=descripcion: (sel.destroy(), self._iterar_elemento(d)))
            btn.pack(pady=3)

    def _iterar_elemento(self, elemento):
        """Genera 5 variantes cambiando un elemento específico."""
        texto = self.txt_salida.get("1.0", "end").strip()
        self.set_estado(f"🔂 Generando 5 variantes ({elemento})...", "#f39c12")
        self.toggle_botones(False)

        peticion = (
            f"Genera 5 VARIANTES de este prompt, cambiando ÚNICAMENTE el elemento: {elemento}.\n"
            f"Todo lo demás (sujeto, composición, formato) debe permanecer IDÉNTICO.\n\n"
            f"PROMPT ORIGINAL:\n{texto}\n\n"
            f"FORMATO DE RESPUESTA:\n"
            f"VARIANTE 1: [prompt completo con cambio]\n---\n"
            f"VARIANTE 2: [prompt completo con cambio]\n---\n"
            f"VARIANTE 3: [prompt completo con cambio]\n---\n"
            f"VARIANTE 4: [prompt completo con cambio]\n---\n"
            f"VARIANTE 5: [prompt completo con cambio]"
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.7, max_tokens=4000)
                resp = limpiar_marcadores(resp)

                # Parsear las 5 variantes
                import re
                variantes = re.split(r'VARIANTE\s*\d+\s*:?\s*', resp, flags=re.IGNORECASE)
                variantes = [v.strip().strip("-").strip() for v in variantes if v.strip() and len(v.strip()) > 30]

                if len(variantes) < 2:
                    self.after(0, lambda: self.set_estado("⚠️ Solo se generó 1 variante, intenta de nuevo", "#e67e22"))
                    self.after(0, lambda: self.toggle_botones(True))
                    return

                def _mostrar():
                    self._abrir_comparador(variantes[:5])
                    self.set_estado(f"🔂 {len(variantes)} variantes de '{elemento}' listas", "#2ecc71")
                    self.toggle_botones(True)
                    self._sonar_completado()
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def cmd_refinar(self):
        texto = self.txt_salida.get("1.0", "end").strip()
        if not texto or not (("PROMPT:" in limpiar_marcadores(texto)) or ("ESTILO:" in limpiar_marcadores(texto))):
            return self.set_estado("⚠️ Genera un prompt primero para refinarlo.", "#e67e22")

        self._ocultar_ideas()
        idea, pers, lora, modo = self.txt_idea.get("1.0", "end").strip(), self.personaje_activo(), self.lora_activo(), self.modo_var.get()
        try: self._sesion_log("🔁 Refinó prompt")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        # Detectar formato del prompt original para mantenerlo
        es_tag_based = not self.is_natural_mode()

        peticion = f"Refina y mejora ESTE prompt:\n\n{texto}\n\n"
        if modo == "imagen":
            if es_tag_based:
                peticion += (
                    "REGLAS CRÍTICAS DE REFINAMIENTO:\n"
                    "1. FORMATO: Tags separados por comas, CON pesos (tag:1.2). PROHIBIDO escribir prosa fluida o párrafos.\n"
                    "2. DENSIDAD: Un tag bueno = 2-5 palabras máximo. '(cinematic god rays:1.3)' SÍ. 'The lighting is a masterpiece of soft diffusion emanating from a heavy overcast sky' NO.\n"
                    "3. MEJORA: Añade tags de composición, iluminación, texturas, materiales, atmósfera que falten.\n"
                    "4. COMPACTA: Si el prompt ya es largo, ELIMINA redundancias antes de añadir. Mejor 60 tags densos que 20 frases largas.\n"
                    "5. PESOS: Usa 5-10 pesos estratégicos en POSITIVE y 3-6 en NEGATIVE.\n"
                    "EJEMPLO DE TAG BUENO: 'extreme macro shot, (translucent crystalline egg:1.4), cross-section view, (bioluminescent mushrooms:1.3), (subsurface scattering:1.3), 8K, sharp focus, HDR'\n"
                    "EJEMPLO DE TAG MALO: 'A hyper-detailed photograph showing an egg that appears to be made of crystal with light passing through it in a beautiful way'"
                )
            else:
                peticion += "Es UNA imagen fija en formato NATURAL (prosa descriptiva). Expande composición, luz, texturas, atmósfera. Mantén la prosa concisa."
        elif modo == "video": peticion += "Es un vídeo. Usa lenguaje cinematográfico, iluminación, textura y movimiento de cámara."
        else: peticion += "Es audio. Especifica género, instrumentación, tempo, voces y mood."

        if idea: peticion += f"\nIncorpora: {idea}"
        if pers: peticion += f"\nManteniendo personaje: {pers}"
        if lora: peticion += f"\nManteniendo LoRA: {lora}"
        if self._ultimo_anclaje_visual: peticion += f"\nMANTÉN ESTRICTAMENTE LA GEOMETRÍA VISUAL: {self._ultimo_anclaje_visual}"

        specs = self.get_current_model_specs()
        limite_chars = specs.get("max_chars") or specs.get("max_chars_letra") or 2000 if specs else 2000
        peticion += f"\n\n⛔ REGLA ESTRICTA DE LONGITUD: El POSITIVE PROMPT final no debe superar los {limite_chars} caracteres. Si el prompt original ya está cerca del límite, COMPACTA en vez de expandir: usa tags más densos, elimina redundancias, prioriza calidad sobre cantidad."

        self.set_estado("🔁 Refinando con meticulosidad máxima...", "#f39c12")
        self.toggle_botones(False)
        threading.Thread(target=self._worker_ia, args=(peticion,), daemon=True).start()

    def cmd_batch(self):
        try: self._sesion_log("📦 Abrió Batch (generación masiva)")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        abrir_batch(self)

    def cmd_reset(self):
        # Comprobar si hay trabajo no guardado
        idea = self.txt_idea.get("1.0", "end").strip()
        salida = self.txt_salida.get("1.0", "end").strip()
        if idea or salida:
            from tkinter import messagebox
            if not messagebox.askyesno("Confirmar reset",
                                     "¿Seguro? Perderás:\n"
                                     f"{'  • Idea actual' if idea else ''}\n"
                                     f"{'  • Prompt generado' if salida else ''}\n"
                                     "  • Imagen de referencia\n"
                                     "  • Estilos marcados\n\n"
                                     "Esta acción no se puede deshacer.",
                                     parent=self):
                return

        self.reiniciar_memoria()
        self._limpiar_imagen()
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
        self._actualizar_contador_estilos()
        # Limpiar negativos
        self._limpiar_negatives()
        self.actualizar_salida("")
        self._ocultar_ideas()
        self.reiniciar_memoria()
        self.set_estado("🔄 Sistema reseteado.", "#3498db")
        try: self._sesion_log("🗑 Reset completo del sistema")
        except Exception as e:
            logger.debug(f"[silent] {e}")

    # CHAT COPILOTO NARRADOR

    def cmd_copiloto(self):
        texto_actual = self.txt_salida.get("1.0", "end").strip()
        if not texto_actual or len(texto_actual) < 20:
            return self.set_estado("⚠️ Genera un prompt primero para poder usar el Copiloto.", "#e67e22")
        try: self._sesion_log("💬 Abrió Copiloto de prompt")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        vent_copiloto = GPromptWindow(self)
        vent_copiloto.title("💬 Copiloto de Prompt")
        vent_copiloto.geometry("450x600")
        vent_copiloto.transient(self)

        chat_frame = ctk.CTkScrollableFrame(vent_copiloto, fg_color="transparent")
        chat_frame.pack(fill="both", expand=True, padx=10, pady=10)

        input_frame = ctk.CTkFrame(vent_copiloto, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=(0, 10))

        txt_input = ctk.CTkEntry(input_frame, placeholder_text="Ej: Haz que sea de noche...")
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
            self.set_estado("💬 Copiloto aplicando cambios...", "#3498db")

            def _worker():
                try:
                    specs = self.get_current_model_specs()
                    limite_chars = specs.get("max_chars") if specs else 2000

                    peticion = (
                        f"Actúa como un editor experto de prompts. Tu tarea es MODIFICAR el prompt base siguiendo EXCLUSIVAMENTE la instrucción del usuario.\n"
                        f"MANTÉN la misma estructura y tags que el original.\n"
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
                        self.set_estado("✅ Copiloto terminó la edición.", "#2ecc71")

                    self.after(0, _update_ui)
                except Exception as e:
                    def _err():
                        _add_msg("Sistema", f"❌ Error: {e}", "#e74c3c")
                        txt_input.configure(state="normal")
                        btn_send.configure(state="normal")
                        self.set_estado("❌ Error en el Copiloto.", "#e74c3c")
                    self.after(0, _err)

            threading.Thread(target=_worker, daemon=True).start()

        btn_send = ctk.CTkButton(input_frame, text="Enviar", width=60, fg_color="#2980b9", hover_color="#1f608a", command=_enviar)
        btn_send.pack(side="right")
        txt_input.bind("<Return>", _enviar)

    # BIND SHORTCUTS / CAMBIAR MODO

    def _bind_shortcuts(self):
        for widget in [self, self.txt_idea]:
            widget.bind("<Control-Return>",       lambda e: self.cmd_prompt())
            widget.bind("<Control-Shift-Return>", lambda e: self.cmd_variaciones())
            # ⚡ Quick Generate · Alt+Enter
            widget.bind("<Alt-Return>",           lambda e: self.cmd_prompt_quick())
            widget.bind("<Control-i>",            lambda e: self.cmd_ideas())
            widget.bind("<Control-1>",            lambda e: self._copiar("positivo"))
            widget.bind("<Control-2>",            lambda e: self._copiar("negativo"))
            widget.bind("<Control-Shift-a>",      lambda e: self.cmd_vision())
            widget.bind("<Control-r>",            lambda e: self._idea_aleatoria_historial())
            # ── MEJORA 4: Ctrl+D = duplicar prompt actual al historial ──
            widget.bind("<Control-d>",            lambda e: self._cmd_duplicar_a_historial())
            # ── TANDA 5: Atajos nuevos ──
            widget.bind("<Control-s>",            lambda e: (self._guardar_favorito(), "break")[1])
            widget.bind("<Control-Shift-S>",      lambda e: self._atajo_guardar_estrella())
            # Alt+1/2/3: cambiar modo
            widget.bind("<Alt-Key-1>",            lambda e: self._cmd_cambiar_modo("imagen"))
            widget.bind("<Alt-Key-2>",            lambda e: self._cmd_cambiar_modo("video"))
            widget.bind("<Alt-Key-3>",            lambda e: self._cmd_cambiar_modo("audio"))
            # Nuevos atajos (MEJORA #14) - con return "break" para evitar duplicados
            widget.bind("<Control-Shift-P>",      lambda e: (self.cmd_previsualizar(), "break")[1])
            widget.bind("<Control-e>",            lambda e: (self._cmd_exportar_rapido(), "break")[1])
            widget.bind("<Control-f>",            lambda e: self._atajo_buscar_global())
            widget.bind("<Control-l>",            lambda e: (self._cmd_abrir_loras(), "break")[1])
            widget.bind("<Control-p>",            lambda e: (self._cmd_grupo_personajes(), "break")[1])
            widget.bind("<Control-t>",            lambda e: (self._abrir_tutorial(), "break")[1])
            widget.bind("<Control-Shift-N>",      lambda e: (self._cmd_negative_builder(), "break")[1])
            widget.bind("<Control-h>",            lambda e: (self._cmd_modo_focus(), "break")[1])
            widget.bind("<Control-Shift-L>",      lambda e: (self._cmd_toggle_tema(), "break")[1])
            widget.bind("<Control-Shift-T>",      lambda e: (self._atajo_traducir_idea(), "break")[1])
        # Ctrl+V inteligente (detecta prompt o imagen en clipboard)
        self.bind("<Control-v>", self._pegar_inteligente_clipboard)
        # Ctrl+? = mostrar atajos
        self.bind("<Control-question>", lambda e: self._cmd_mostrar_atajos())
        # F11 y Escape para pantalla completa
        self.bind("<F11>", lambda e: self._toggle_fullscreen())
        self.bind("<Escape>", lambda e: self._cerrar_popup_activo())

    def _cmd_cambiar_modo(self, modo_destino):
        """Cambia el modo (imagen/video/audio) por atajo Alt+1/2/3."""
        if modo_destino not in ("imagen", "video", "audio"): return "break"
        try:
            self.modo_var.set(modo_destino)
            self._on_modo_cambio()
            etiqueta = {"imagen": "🎨 IMAGEN", "video": "🎬 VÍDEO", "audio": "🎵 AUDIO"}[modo_destino]
            self.set_estado(f"{etiqueta} (Alt+{1 if modo_destino == 'imagen' else 2 if modo_destino == 'video' else 3})", "#3498db")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        return "break"

    def _cmd_exportar_rapido(self):
        """Atajo Ctrl+E - Exportar rápidamente el prompt actual."""
        if hasattr(self, '_exportar'):
            self._exportar()
        elif hasattr(self, 'cmd_exportar'):
            self.cmd_exportar()
        else:
            self.set_estado("⚠️ Función de exportar no disponible", "#e67e22")
        return "break"

    def _atajo_guardar_estrella(self):
        """Atajo Ctrl+Shift+S - Guardar como estrella."""
        try:
            if hasattr(self, '_guardar_estrella'):
                self._guardar_estrella()
            else:
                self.set_estado("⚠️ Función no disponible", "#e74c3c")
        except Exception as e:
            self.set_estado(f"⚠️ Error: {e}", "#e74c3c")
        return "break"

    def _cmd_buscar_global(self):
        """Atajo Ctrl+F - Buscar en historial, favoritos, estrellas."""
        try:
            self._abrir_busqueda_global()
        except Exception as e:
            self.set_estado(f"⚠️ Error: {e}", "#e74c3c")
        return "break"

    def _atajo_buscar_global(self):
        """Helper para Ctrl+F con manejo de errores."""
        try:
            self._cmd_buscar_global()
        except Exception as e:
            self.set_estado(f"⚠️ Error búsqueda: {e}", "#e74c3c")
        return "break"

    def _atajo_traducir_idea(self):
        """Ctrl+Shift+T - Traduce el campo idea al inglés."""
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea:
            self.set_estado("⚠️ Escribe algo en la idea primero", "#e67e22")
            return "break"
        try:
            texto_traducido = self.deepseek.traducir(idea)
            if texto_traducido and texto_traducido != idea:
                self.txt_idea.delete("1.0", "end")
                self.txt_idea.insert("1.0", texto_traducido)
                self.set_estado("🌐 Idea traducida al inglés", "#3498db")
            else:
                self.set_estado("⚠️ No se pudo traducir", "#e67e22")
        except Exception as e:
            self.set_estado(f"⚠️ Error: {e}", "#e74c3c")
        return "break"

    def _toggle_fullscreen(self):
        """F11 - Alternar pantalla completa."""
        if hasattr(self, '_toggle_fullscreen_principal'):
            self._toggle_fullscreen_principal()
        else:
            current = self.attributes('-fullscreen')
            self.attributes('-fullscreen', not current)
        return "break"

    def _cerrar_popup_activo(self):
        """Escape - Cerrar popup activo (Toplevel más reciente)."""
        try:
            # Buscar popups abiertos
            popups = [w for w in self.winfo_children() if isinstance(w, ctk.CTkToplevel)]
            if popups:
                popups[-1].destroy()
                return "break"
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # Si hay ventana de pantalla completa, salir
        if self.attributes('-fullscreen'):
            self.attributes('-fullscreen', False)
            return "break"
        return "break"

    def _cmd_abrir_loras(self):
        """Atajo Ctrl+L - Abrir gestión de LoRAs."""
        from modules.windows import abrir_loras
        try:
            abrir_loras(self)
        except Exception as e:
            self.set_estado(f"⚠️ Error al abrir LoRAs: {e}", "#e74c3c")
        return "break"

    def _cmd_mostrar_atajos(self):
        """Ctrl+? - Muestra ventana con todos los atajos de teclado."""
        from config import get_theme_colors
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self)
        vent.title("⌨️ Atajos de teclado")
        vent.geometry("620x600")
        vent.transient(self)

        ctk.CTkLabel(vent, text="⌨️ Atajos de teclado", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(12, 5))
        ctk.CTkLabel(vent, text="Usa estos atajos para trabajar más rápido", font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=5)

        atajos = [
            ("⚡ Generación", [
                ("Ctrl+Enter", "Generar prompt"),
                ("Ctrl+Shift+Enter", "Generar variaciones (x3)"),
                ("Alt+Enter", "Generación rápida (Quick)"),
                ("Ctrl+I", "Generar 3 ideas"),
            ]),
            ("✏️  Edición", [
                ("Ctrl+S", "Guardar como favorito"),
                ("Ctrl+Shift+S", "Guardar como estrella"),
                ("Ctrl+D", "Duplicar al historial"),
                ("Ctrl+Shift+P", "Previsualizar (Pollinations)"),
                ("Ctrl+Shift+T", "Traducir idea al inglés"),
                ("Ctrl+V", "Pegar inteligente"),
            ]),
            ("📋 Portapapeles", [
                ("Ctrl+1", "Copiar POSITIVE"),
                ("Ctrl+2", "Copiar NEGATIVE"),
                ("Ctrl+Shift+A", "Analizar imagen (Vision)"),
            ]),
            ("🎬 Navegación", [
                ("Alt+1", "Modo imagen"),
                ("Alt+2", "Modo vídeo"),
                ("Alt+3", "Modo audio"),
                ("Ctrl+R", "Idea aleatoria del historial"),
                ("Ctrl+T", "Abrir tutorial"),
            ]),
            ("🛠 Herramientas", [
                ("Ctrl+E", "Exportar rápido"),
                ("Ctrl+F", "Búsqueda global"),
                ("Ctrl+L", "Abrir LoRAs"),
                ("Ctrl+P", "Grupo de personajes"),
                ("Ctrl+Shift+N", "Constructor de negative"),
                ("Ctrl+H", "Modo Focus"),
                ("Ctrl+Shift+L", "Cambiar tema claro/oscuro"),
            ]),
            ("❓ Extra", [
                ("F11", "Pantalla completa"),
                ("Escape", "Cerrar popup / Salir de pantalla completa"),
            ]),
            ("❓ Ayuda", [
                ("Ctrl+?", "Mostrar atajos"),
            ]),
        ]

        for categoria, lista in atajos:
            frame_cat = ctk.CTkFrame(scroll, fg_color=c["fg_dark"], corner_radius=6)
            frame_cat.pack(fill="x", pady=4)
            ctk.CTkLabel(frame_cat, text=categoria, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=c["hdr_text"]).pack(anchor="w", padx=10, pady=(6, 4))
            for tecla, accion in lista:
                row = ctk.CTkFrame(frame_cat, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=1)
                ctk.CTkLabel(row, text=tecla, font=ctk.CTkFont(size=10, weight="bold"),
                             width=160, anchor="w", text_color="#3498db").pack(side="left")
                ctk.CTkLabel(row, text=accion, font=ctk.CTkFont(size=10),
                             anchor="w", text_color=c["panel_text"]).pack(side="left")

        ctk.CTkButton(vent, text="Cerrar", width=120, height=30, command=vent.destroy).pack(pady=12)
        return "break"

    def _abrir_busqueda_global(self):
        """Abre ventana de búsqueda global en historial, favoritos, estrellas."""
        from config import get_theme_colors
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self)
        vent.title("🔍 Búsqueda global")
        vent.geometry("550x450")
        vent.transient(self)

        ctk.CTkLabel(vent, text="🔍 Búsqueda global", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(vent, text="Busca en historial, favoritos y estrellas", font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

        ent_buscar = ctk.CTkEntry(vent, placeholder_text="Escribe para buscar...", width=480, height=32)
        ent_buscar.pack(pady=5)

        resultados_frame = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        resultados_frame.pack(fill="both", expand=True, padx=15, pady=5)

        def _buscar(*args):
            termino = ent_buscar.get().strip().lower()
            for w in resultados_frame.winfo_children(): w.destroy()

            if not termino:
                ctk.CTkLabel(resultados_frame, text="Escribe algo para buscar", text_color=c["muted_text"]).pack(pady=20)
                return

            resultados = []

            # Buscar en historial
            for item in (self.store.historial or [])[:50]:
                if isinstance(item, dict):
                    contenido = item.get("contenido", "")
                    if termino in contenido.lower():
                        resultados.append(("📋 Historial", contenido[:100]))

            # Buscar en favoritos
            for item in (self.store.favoritos or []):
                if isinstance(item, dict):
                    contenido = item.get("contenido", "")
                    if termino in contenido.lower():
                        resultados.append(("⭐ Favorito", contenido[:100]))

            # Buscar en estrellas
            for item in (self.store.estrellas or []):
                if isinstance(item, dict):
                    contenido = item.get("contenido", "")
                    if termino in contenido.lower():
                        resultados.append(("🌟 Estrella", contenido[:100]))

            if not resultados:
                ctk.CTkLabel(resultados_frame, text="No se encontraron resultados", text_color=c["muted_text"]).pack(pady=20)
                return

            for tipo, texto in resultados[:20]:
                card = ctk.CTkFrame(resultados_frame, fg_color=c["fg_frame"], corner_radius=4)
                card.pack(fill="x", pady=2)
                color = {"📋": "#3498db", "⭐": "#f39c12", "🌟": "#9b59b6"}.get(tipo[:2], "#888")
                ctk.CTkLabel(card, text=tipo, font=ctk.CTkFont(size=9, weight="bold"),
                             text_color=color, width=60, anchor="w").pack(side="left", padx=6, pady=4)
                ctk.CTkLabel(card, text=texto + "..." if len(texto) > 90 else texto,
                             font=ctk.CTkFont(size=9), text_color=c["muted_text"],
                             anchor="w").pack(side="left", padx=4, fill="x", expand=True)

        ent_buscar.bind("<KeyRelease>", _buscar)
        _buscar()

        ctk.CTkButton(vent, text="Cerrar", width=100, height=28, command=vent.destroy).pack(pady=8)

    def _abrir_tutorial(self):
        """Tutorial interactivo completo con navegación por pasos."""
        from config import get_theme_colors
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        pasos = [
            ("🎯 1. IDEA — El punto de partida",
             "Escribe tu idea en el campo superior. Puede ser simple ('un gato') o detallada ('un gato persa dorado durmiendo en un sofá de terciopelo azul con luz cálida de atardecer').\n\n💡 Cuanto más específica, mejor el resultado. Incluye: sujeto, acción, entorno, estilo."),
            ("📱 2. MODO — Imagen, Vídeo o Audio",
             "Cambia con Alt+1 (Imagen), Alt+2 (Vídeo), Alt+3 (Audio) o el selector superior.\n\n• Imagen: fotos, ilustraciones, arte\n• Vídeo: clips, animaciones, motion graphics\n• Audio: canciones, música, efectos\n\nCada modo tiene modelos específicos y ajustes distintos."),
            ("🤖 3. MODELO — El motor de generación",
             "Selecciona el modelo desde el desplegable. Los más populares:\n\n• FLUX — excelente para cualquier cosa, rápido\n• Midjourney — estilo artístico, colores vibrantes\n• Kling / Seedance — para vídeo realista\n• Suno — para música y audio\n• Stable Diffusion — control total, técnico\n\nCada modelo tiene 'personalidad' diferente. Experimenta."),
            ("🌐 4. PLATAFORMA — A dónde subirás",
             "Elige la plataforma destino: SeaArt, Tensor.Art, ComfyUI, Kling, Suno, etc.\n\nEsto adapta el formato del prompt: algunas usan tags con pesos, otras lenguaje natural. La plataforma también afecta qué modelos están disponibles."),
            ("🎨 5. ESTILOS — La estética visual",
             "Marca 1-3 estilos que quieras aplicar. Opciones:\n\n• Fotografía Realista • Cine • Animé/Manga\n• Arte Digital • Concept Art • Ilustración\n• Vintage • Cyberpunk • Fantasy • Horror\n\n💡 Combinar más de 3 puede generar resultados inesperados. Menos es más."),
            ("⚙️ 6. RATIO — Proporción de la imagen",
             "Elige formato según用途:\n\n• 1:1 — Cuadrado (Instagram posts)\n• 16:9 — Horizontal (YouTube, web)\n• 9:16 — Vertical (Stories, Reels, TikTok)\n• 4:3 — Clásico (fotografía)\n• 21:9 — Ultra wide (cinemático)\n\nEl ratio afecta composición y enfoque. Un 9:16 focus en primer plano; 16:9 permite más contexto."),
            ("👤 7. PERSONAJE — Personajes recurrentes",
             "Si generas el mismo personaje frecuentemente, guardalo aquí.\n\nDefine: nombre, descripción física, rasgos distintivos, ropa habitual.\n\nCuando actives un personaje, su descripción se añade automáticamente al prompt.ideal para series, cómics, historias."),
            ("🔗 8. LoRA — Modelos adicionales",
             "Los LoRAs son pequeños modelos que añaden estilos o sujetos específicos.\n\nActívalos desde el panel LoRA. Algunos populares:\n• Estilos artísticos (anime, watercolor)\n• Efectos (glow, glitch)\n• Sujetos específicos (personajes, objetos)\n\n💡 Cada LoRA consume parte del 'presupuesto' del prompt."),
            ("🛡️ 9. NEGATIVE — Lo que NO quieres",
             "El negative prompt dice lo que NO debe aparecer en la imagen.\n\nNegatives típicos: low quality, blurry, distorted, ugly, deformed, watermark, text.\n\nUsa '🛡 Generar negative óptimo' para uno automático según tu modelo."),
            ("✨ 10. GENERAR — Crear el prompt",
             "Presiona Ctrl+Enter o el botón '✨ Generar'.\n\nEl LLM toma tu idea + configuración y crea un prompt optimizado.\n\nOpciones:\n• Ctrl+Enter = Generar completo (8-15s)\n• Alt+Enter = Quick Generate (3-6s, menos elaborado)"),
            ("🔁 11. REFINAR — Mejora el resultado",
             "Si el resultado no te gusta, usa Refinar:\n\n• Refinar estándar — mejora general\n• Refinar más cinematográfico — encuadre épico, cámara dramámatica\n• Refinar más detalle facial — ojos, piel, texturas\n• Refinar mejor iluminación — luces, sombras, atmósfera\n• Refinar simplificar — elimina redundancias\n\n💡 Prueba primero Refinar antes de regenerar desde cero."),
            ("📊 12. SCORING — Análisis y mejora automática",
             "El scoring analiza tu prompt y propone mejoras automáticas.\n\nUsa '📊 Scoring auto' en macros para aplicar directamente, o el scoring normal para ver la comparativa.\n\nEl scoring detecta: calidad técnica, balance, coherencia, detalle."),
            ("⭐ 13. GUARDAR — Favoritos y Estrellas",
             "Guarda lo que te gusta para reutilizarlo:\n\n• Ctrl+S = Favorito (acceso rápido)\n• Ctrl+Shift+S = Estrella (destacado premium)\n\nLos favoritos aparecen en el panel lateral. Las estrellas son tus mejores trabajos."),
            ("📑 14. PLANTILLAS — Estructuras probadas",
             "34 plantillas con estructuras profesionales. Acceso: Menú Plantillas.\n\nCategorías: Retratos, Paisajes, Cine, Moda, Anime, Producto, Arquitectura, Gaming, Arte, Foto.\n\n💡 Reemplaza las variables {sujeto}, {lugar}, {hora_dia}, etc. con tus datos."),
            ("🧪 15. MACROS — Automatización",
             "Crea secuencias que se ejecutan automáticamente:\n\n1. Guarda tus acciones favoritas como macro\n2. Añade pasos: Generar → Refinar → Scoring → Guardar\n3. Ejecuta todo en un click\n\nUsa las macros predefinidas o crea las tuyas. Ideal para flujos repetitivos."),
            ("💎 16. SEEDS — Configuraciones rápidas",
             "Guarda configuraciones: modelo + plataforma + ratio + estilos.\n\nUsa cuando tienes una combinación que funciona bien y quieres recuperarla rápido.\n\nDiferencia con plantillas: Seeds guardan solo config, plantillas guardan el setup completo."),
            ("🎬 17. A/B TESTING — Compara variantes",
             "Genera 4 versiones con variaciones diferentes:\n\n• Cambia solo estilo → compara aesthetics\n• Cambia solo iluminación → compara mood\n• Cambia ratio → compara composición\n• Combina cambios → encuentra lo optimal\n\nSelecciona 1-2 dimensiones a variar. Las 4 opciones se muestran en grid para comparar."),
            ("🎥 18. GRABAR SESIÓN — Tutoriales y回忆",
             "Activa desde el botón 🎬 en la barra.\n\nRegistra: prompts, clics, errores, flujos completos.\n\nLuego puedes:\n• Exportar como tutorial paso a paso\n• Revisar qué hiciste mal\n• Crear documentación de tu proceso\n\nOpciones de grabación: solo app, pantalla completa, o solo texto."),
            ("📈 19. VERSIONES — Historial de cambios",
             "Cada vez que generas/refinas, se guarda una versión (hasta 30).\n\nAccede desde '📜 Versiones prompt' en el menú.\n\nútil para:\n• Comparar versiones anteriores\n• Recuperar una que era mejor\n• Ver la evolución de tu prompt"),
            ("🔍 20. BUSCAR — Encuentra lo que necesitas",
             "Ctrl+F abre búsqueda global en:\n\n• Historial — todos los prompts生成ados\n• Favoritos — tus guardados rápidos\n• Estrellas — tus mejores trabajos\n\nBusca por palabras clave en el contenido."),
            ("⌨️ 21. ATAJOS DE TECLADO — Trabaja más rápido",
             "Los más útiles:\n\n• Ctrl+Enter — Generar prompt\n• Ctrl+S — Guardar favorito\n• Ctrl+Shift+S — Guardar estrella\n• Ctrl+I — Ideas creativas\n• Ctrl+F — Búsqueda global\n• Ctrl+T — Este tutorial\n• Ctrl+L — Abrir LoRAs\n• Ctrl+P — Grupo personajes\n• Ctrl+Shift+N — Negative builder\n• Ctrl+Shift+P — Previsualizar\n• F11 — Pantalla completa\n• Alt+1/2/3 — Cambiar modo"),
            ("📤 22. EXPORTAR — Comparte tu trabajo",
             "Desde el menú Exportar, puedes:\n\n• Copiar al portapapeles\n• Guardar como .txt / .json\n• Exportar para CLI (ComfyUI, A1111)\n• Exportar proyecto completo\n\nEl formato depende del destino: tags, natural, JSON."),
            ("🎛️ 23. AJUSTES EXTRAS — Configuración avanzada",
             "En el panel de ajustes extras:\n\n• Weight (1-30) — Intensidad del LoRA\n• Seed — Reproducibilidad\n• Repeats — Repetir elementos\n• CFG Scale — Fidelidad al prompt\n• Steps — Calidad vs velocidad\n\n💡 Estos afectan significativamente el resultado. Experimenta con cuidado."),
            ("📊 24. ESTADÍSTICAS — Tu uso de la app",
             "Accede desde '📈 Estadísticas' en Análisis.\n\nMuestra:\n• Prompts generados\n• Modelos más usados\n• Estilos favoritos\n• Tiempo de uso\n• Logros desbloqueados\n\nútil para entender tu flujo y optimizarlo."),
            ("🧬 25. ADN VISUAL — Análisis de imagen",
             "Carga una imagen y extrae su 'ADN': sujeto, iluminación, estilo, cámara, composición.\n\nLuego puedes:\n• Convertir a prompt estructurado\n• Mantener algunos elementos (ej: estilo) y cambiar otros\n• Guardar el ADN para reutilizar\n\n Potente para análisis y variaciones controladas."),
            ("💡 26. CONSEJOS FINALES",
             "1. Sé específico en la idea — 'gato' vs 'gato persa dorado durmiendo'\n2. Limita estilos a 2-3 — más genera caos\n3. Usa negativos — evita lo que no quieres\n4. Prueba variaciones — A/B testing es tu amigo\n5. Guarda lo bueno — favoritos y estrellas\n6. Iteración > Regenerar — refina antes de empezar de nuevo\n7. Experimenta — los mejores prompts vienen de pruebas\n\n🎓 ¡Con práctica dominarás todas las herramientas. Mucho éxito!"),
        ]

        idx_actual = {"valor": 0}

        vent = GPromptWindow(self)
        vent.title("📖 Tutorial - G-Prompt Studio")
        vent.geometry("650x480")
        vent.transient(self)

        total_pasos = len(pasos)

        ctk.CTkLabel(vent, text="📖 Tutorial completo de G-Prompt Studio",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))

        # Progress bar
        progress = ctk.CTkProgressBar(vent, width=450, height=10)
        progress.pack(pady=(0, 8))
        progress.set(1 / total_pasos)

        # Indicador de paso
        lbl_paso = ctk.CTkLabel(vent, text="Paso 1/26", font=ctk.CTkFont(size=12), text_color=c["muted_text"])
        lbl_paso.pack(pady=(0, 8))

        # Contenido del paso
        contenido_frame = ctk.CTkScrollableFrame(vent, fg_color=c["fg_frame"], corner_radius=8)
        contenido_frame.pack(fill="both", expand=True, padx=15, pady=10)

        lbl_titulo = ctk.CTkLabel(contenido_frame, text="", font=ctk.CTkFont(size=13, weight="bold"),
                                  text_color=c["hdr_text"])
        lbl_titulo.pack(anchor="w", pady=(0, 8), padx=10)

        lbl_desc = ctk.CTkLabel(contenido_frame, text="", font=ctk.CTkFont(size=11),
                               text_color=c["muted_text"], wraplength=570, justify="left")
        lbl_desc.pack(anchor="w", padx=10)

        def actualizar_paso():
            i = idx_actual["valor"]
            titulo, desc = pasos[i]
            lbl_titulo.configure(text=titulo)
            lbl_desc.configure(text=desc)
            lbl_paso.configure(text=f"Paso {i+1}/{total_pasos} ({int((i+1)/total_pasos*100)}%)")
            progress.set((i + 1) / total_pasos)

            btn_ant.configure(state="normal" if i > 0 else "disabled")
            btn_sig.configure(state="normal" if i < total_pasos - 1 else "disabled")

        def siguiente():
            if idx_actual["valor"] < total_pasos - 1:
                idx_actual["valor"] += 1
                actualizar_paso()

        def anterior():
            if idx_actual["valor"] > 0:
                idx_actual["valor"] -= 1
                actualizar_paso()

        def ir_inicio():
            idx_actual["valor"] = 0
            actualizar_paso()

        def ir_final():
            idx_actual["valor"] = total_pasos - 1
            actualizar_paso()

        # Botones de navegación
        nav_frame = ctk.CTkFrame(vent, fg_color="transparent")
        nav_frame.pack(pady=(12, 15))

        btn_inicio = ctk.CTkButton(nav_frame, text="⏮️ Inicio", width=70, height=30, command=ir_inicio)
        btn_inicio.pack(side="left", padx=3)

        btn_ant = ctk.CTkButton(nav_frame, text="◀ Anterior", width=100, height=30, command=anterior)
        btn_ant.pack(side="left", padx=5)

        btn_sig = ctk.CTkButton(nav_frame, text="Siguiente ▶", width=100, height=30, command=siguiente)
        btn_sig.pack(side="left", padx=5)

        btn_final = ctk.CTkButton(nav_frame, text="Fin ⏭️", width=70, height=30, command=ir_final)
        btn_final.pack(side="left", padx=3)

        ctk.CTkButton(vent, text="¡Vamos a probar!", width=180, height=32, fg_color="#1a7a3c",
                      command=vent.destroy).pack(pady=(8, 12))

        actualizar_paso()
