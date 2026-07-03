"""Theme helpers — recoloreado de widgets al cambiar de tema claro/oscuro.

Extraído de modules/core.py. Agrupa las funciones puras de recoloreado
(_recolor_labels, _recolor_widgets) y la función de orquestación
apply_theme_colors(app) que reemplaza al método _apply_theme_colors(self)
de CoreMixin.

Uso desde CoreMixin:
    from modules.theme import apply_theme_colors
    def _apply_theme_colors(self):
        apply_theme_colors(self)
"""
import logging

import customtkinter as ctk

from modules.i18n import tr

logger = logging.getLogger("gprompt")


def _recolor_labels(container, primary_color, secondary_color, muted_color):
    """Recursivamente recolorea todos los CTkLabel dentro de un contenedor.

    Usado por apply_theme_colors para que al cambiar de tema todos los
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


def apply_theme_colors(app):
    """Actualiza colores de header, barra de modo, checkboxes y labels
    sin destruir widgets. Incluye checkboxes de estilos (sin esto
    mantenían el color del tema antiguo al cambiar de tema).

    Recibe la instancia de la app (ArquitectoApp) en lugar de self.
    Llamado desde CoreMixin._apply_theme_colors(self).
    """
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
    if hasattr(app, '_header_frame'):
        app._header_frame.configure(fg_color=hdr_bg)
    if hasattr(app, '_lbl_cerebro'):
        app._lbl_cerebro.configure(text_color=hdr_label)
    if hasattr(app, 'combo_llm'):
        app.combo_llm.configure(fg_color=combo_bg, border_color=combo_border, button_color=combo_btn, text_color=hdr_text)
    if hasattr(app, '_btn_key'):
        app._btn_key.configure(fg_color=key_bg, hover_color=key_hover)
    # Menús del header: relleno con el color semántico de cada grupo
    # (no el neutro btn_bg — machacaría el estilo de ui_builders).
    if hasattr(app, '_header_menus'):
        from modules import paleta as P
        for btn, _label, color_grupo, _items in app._header_menus:
            btn.configure(**P.estilo_boton(color_grupo, primario=True),
                          text_color="#ffffff")

    # Modo bar
    if hasattr(app, '_modo_frame'):
        app._modo_frame.configure(fg_color=modo_bg)
    if hasattr(app, '_lbl_plataforma'):
        app._lbl_plataforma.configure(text_color=modo_label)

    # Switches
    sw_button = "#374151" if is_light else "#ffffff"
    sw_button_hover = "#1f2937" if is_light else "#f3f4f6"
    if hasattr(app, 'switch_nsfw'):
        is_nsfw_on = app.switch_nsfw_var.get()
        app.switch_nsfw.configure(
            fg_color=sw_fg, border_color=nsfw_border_on if is_nsfw_on else sw_border_off,
            text_color=nsfw_text_on if is_nsfw_on else sw_text_off,
            button_color=sw_button, button_hover_color=sw_button_hover)
    if hasattr(app, '_sw_trad'):
        is_trad_on = app.switch_traduccion_var.get()
        app._sw_trad.configure(
            fg_color=sw_fg, border_color=trad_border_on if is_trad_on else sw_border_off,
            text_color=trad_text_on if is_trad_on else sw_text_off,
            button_color=sw_button, button_hover_color=sw_button_hover)
    # switch_brief y switch_instrumental también
    for sw_attr in ('switch_brief', 'switch_instrumental'):
        try:
            sw = getattr(app, sw_attr, None)
            if sw and sw.winfo_exists():
                sw.configure(button_color=sw_button, button_hover_color=sw_button_hover)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    # Refrescar checkboxes de estilos: sin esto, al cambiar tema en
    # caliente los checkboxes mantenían colores antiguos (gris/gris).
    if hasattr(app, "estilo_checks") and hasattr(app, "frame_checks") and c:
        try:
            for w in app.frame_checks.winfo_children():
                if isinstance(w, ctk.CTkCheckBox):
                    w.configure(
                        text_color=c["chk_text"],
                        border_color=c["chk_border"],
                        fg_color=c["accent_text"],
                        hover_color=c["accent_text"],
                    )
            # Fondo del scrollable
            app.frame_checks.configure(fg_color=c["chk_bg"])
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    # Label de estilos seleccionados (verde) y contador
    if hasattr(app, "lbl_estilos_sel"):
        try:
            verde = "#059669" if is_light else "#2ecc71"
            app.lbl_estilos_sel.configure(text_color=verde)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    if hasattr(app, "lbl_estilos_count") and c:
        try:
            app.lbl_estilos_count.configure(text_color=c["muted_text"])
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    # Refrescar contador (ajusta color según hay selección o no)
    try:
        if hasattr(app, "_actualizar_contador_estilos"):
            app.ui._actualizar_contador_estilos()
    except Exception as _e:
        logger.debug(f"[silent] {_e}")
    # Refrescar tabview central (Ajustes/Estilos/Negativos): el
    # tabview de CustomTkinter no se repinta al cambiar tema sin
    # forzar los colores explícitamente.
    if hasattr(app, "tabview") and c:
        try:
            tab_bg = c["panel_bg"]
            seg_bg = "#e5e7eb" if is_light else "#1f2937"
            seg_sel = "#2563eb" if is_light else "#3b82f6"
            seg_hov = "#dbeafe" if is_light else "#374151"
            app.tabview.configure(
                fg_color=tab_bg, bg_color=tab_bg,
                segmented_button_fg_color=seg_bg,
                segmented_button_selected_color=seg_sel,
                segmented_button_selected_hover_color=seg_sel,
                segmented_button_unselected_color=seg_bg,
                segmented_button_unselected_hover_color=seg_hov,
                text_color=c["panel_text"],
            )
            for tab_name in (tr("⚙️ Ajustes Extra"), tr("🎨 Estilos"), tr("🚫 Negativos")):
                try:
                    app.tabview.tab(tab_name).configure(fg_color=tab_bg, bg_color=tab_bg)
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
            _f = getattr(app, _fname, None)
            if _f is not None and _f.winfo_exists():
                _f.configure(fg_color=tab_bg)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    # Reconfigurar tabs internos del tabview: gestionan sus tabs
    # como CTkFrame que necesitan ser repintados explícitamente al
    # cambiar tema, sino el contenido interno (Ajustes Extra,
    # Estilos, Negativos) queda con el fg_color del tema anterior.
    if hasattr(app, "tabview"):
        try:
            app.tabview.configure(fg_color=tab_bg, bg_color=tab_bg)
            for tab_name in (tr("⚙️ Ajustes Extra"), tr("🎨 Estilos"), tr("🚫 Negativos")):
                try:
                    t = app.tabview.tab(tab_name)
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
        app.configure(fg_color=root_bg)
    except Exception as _e:
        logger.debug(f"[silent] {_e}")
    # Repintar botones rápidos de ratio: los iconos ⬜📱🖥📸🖼 al lado
    # del combo Ratio se quedaban con fondo oscuro al pasar a tema
    # claro porque su fg_color se fija en construcción.
    if hasattr(app, "ratio_btns") and app.ratio_btns:
        ratio_btn_bg = "#ffffff" if is_light else "#1a2030"
        ratio_btn_hover = "#dbeafe" if is_light else "#2a3a50"
        ratio_btn_text = c["panel_text"] if c else ("#111827" if is_light else "#e5e7eb")
        try:
            for btn in app.ratio_btns.values():
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
                fr = getattr(app, fname, None)
                if fr is None or not fr.winfo_exists():
                    continue
                _recolor_labels(fr, lbl_color, lbl_secondary, muted_color)
            # También refrescar TODAS las pestañas del tabview directamente
            if hasattr(app, "tabview"):
                for tab_name in (tr("⚙️ Ajustes Extra"), tr("🎨 Estilos"), tr("🚫 Negativos")):
                    try:
                        tab_frame = app.tabview.tab(tab_name)
                        _recolor_labels(tab_frame, lbl_color, lbl_secondary, muted_color)
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    # Recolorear combos, opciones, segmentados
    try:
        _recolor_widgets(app, is_light)
    except Exception as _e:
        logger.debug(f"[silent] {_e}")
    # Recolorear labels específicos de entrada/estado/footer
    mt = c["muted_text"] if c else ("#4b5563" if is_light else "#9ca3af")
    pl = c["panel_label"] if c else ("#1f2937" if is_light else "#9ca3af")
    pt = c["panel_text"] if c else ("#111827" if is_light else "#e5e7eb")
    for attr in ("lbl_estado", "lbl_tokens", "lbl_idea_counter", "lbl_compat_inline"):
        try:
            w = getattr(app, attr, None)
            if w and w.winfo_exists():
                w.configure(text_color=mt)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    for attr in ("lbl_autocomplete",):
        try:
            w = getattr(app, attr, None)
            if w and w.winfo_exists():
                w.configure(text_color="#2563eb" if is_light else "#5a8aaa")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    # Recolorear frame_entrada y frame_salida headers via _recolor_labels
    for attr in ("frame_entrada",):
        try:
            fr = getattr(app, attr, None)
            if fr and fr.winfo_exists():
                _recolor_labels(fr, pt, pl, mt)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")

    # Recolorear los CTkCheckBox de estilos en TODOS los sub_frames
    # cacheados. Los checkboxes se construyen UNA vez por modo (cache)
    # con el color del tema activo en ese momento; al cambiar de tema
    # hay que aplicarles los colores nuevos manualmente o quedan
    # blancos sobre blanco en light (o negros sobre negro en dark).
    if hasattr(app, "_checks_subframes_cache") and c:
        chk_text_color = c.get("chk_text", pt)
        chk_border_color = c.get("chk_border", "#6b7280" if is_light else "#374151")
        chk_hover_color = c.get("chk_hover", "#bfdbfe" if is_light else "#1f2937")
        chk_fg_color = c.get("accent_text", "#3b82f6")
        for sub in app._checks_subframes_cache.values():
            try:
                if not sub.winfo_exists():
                    continue
                for child in sub.winfo_children():
                    if isinstance(child, ctk.CTkCheckBox):
                        try:
                            child.configure(
                                text_color=chk_text_color,
                                border_color=chk_border_color,
                                hover_color=chk_hover_color,
                                fg_color=chk_fg_color,
                            )
                        except Exception as _e:
                            logger.debug(f"[silent chk recolor] {_e}")
            except Exception as _e:
                logger.debug(f"[silent subframe recolor] {_e}")

    # También el fg_color del propio frame_checks (fondo del scroll)
    if hasattr(app, "frame_checks") and c:
        try:
            if app.frame_checks.winfo_exists():
                app.frame_checks.configure(fg_color=c.get("chk_bg",
                                            "#ffffff" if is_light else "#0d1117"))
        except Exception as _e:
            logger.debug(f"[silent frame_checks] {_e}")
