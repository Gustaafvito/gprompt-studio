"""UI Builders Mixin — métodos _build_* y helpers de UI.

_build_header() pinta indicador de proveedor LLM activo (✅/⚠) y es
responsive: en ventanas <1200px se compacta el texto de los botones
de menú a solo emoji.

_get_real_is_light() lee el tema persistido en preferencias.json en
lugar de depender de ctk.get_appearance_mode() para evitar el race
condition donde los _build_*_panel() se ejecutan ANTES de que
set_appearance_mode("light") haya disparado (diferido 200ms). Sin
esto, los labels se construían con color de tema dark y quedaban
invisibles sobre el fondo light tras cambiar tema.
"""
import customtkinter as ctk
import tkinter as tk
import re
import random
import datetime
import logging
import os
import json
import pyperclip
from modules.gprompt_window import GPromptWindow

logger = logging.getLogger(__name__)


def _get_real_is_light() -> bool:
    """Devuelve si el tema activo es light.

    Estrategia robusta — priorizar SIEMPRE ctk.get_appearance_mode() salvo
    durante el caso muy concreto del race condition de arranque, donde:
    - CTk reporta "dark" (su valor por defecto antes del set diferido)
    - preferencias.json dice "light" (el valor real)
    - el flag _gprompt_init_done aún no se ha activado

    En ese caso muy específico devolvemos True (light).
    En cualquier otro caso → fiarse de CTk.

    Esto evita que, si el usuario tiene prefs="light" pero arranca con
    el toggle ya cambiado a dark, el helper le devuelva light durante
    la construcción.
    """
    try:
        ctk_mode = ctk.get_appearance_mode().lower()
    except Exception:
        ctk_mode = "dark"

    # Comprobar si la inicialización ya terminó
    init_done = False
    try:
        import sys
        for mod_name in ('app', '__main__'):
            mod = sys.modules.get(mod_name)
            if mod is not None and getattr(mod, '_gprompt_init_done', False):
                init_done = True
                break
    except Exception as _e:
        logger.debug(f"[silent] {_e}")
    # Después de init, fiarse 100% de CTk (respeta toggle en caliente)
    if init_done:
        return ctk_mode == "light"

    # Durante init: si CTk dice "light", confiar (es lo que se quería)
    if ctk_mode == "light":
        return True

    # CTk dice "dark" durante init — puede ser:
    # (a) el default de CTk antes del set diferido a "light"
    # (b) que el usuario realmente tiene "dark" guardado
    # Discriminar leyendo preferencias.json
    try:
        from config import ARCHIVOS
        path = ARCHIVOS.get("preferencias")
        if path and os.path.exists(str(path)):
            with open(str(path), "r", encoding="utf-8") as f:
                prefs = json.load(f)
            tema = prefs.get("tema", "dark")
            if tema == "light":
                return True  # caso (a) — race condition
            # tema == "dark" o "system" → caso (b) — respetar dark
            return False
    except Exception as _e:
        logger.debug(f"[silent] {_e}")
    # Fallback: CTk dice dark, no se pudo leer prefs → dark
    return False


try:
    from CTkToolTip import CTkToolTip
    # (se aplica al inicio para que cualquier importador lo aproveche).
except ImportError:
    class CTkToolTip:
        def __init__(self, *args, **kwargs): pass
from config import (
    PUBLIC_VERSION, VERSION,
    ESTILOS_IMAGEN, ESTILOS_VIDEO, ESTILOS_AUDIO,
    NEGATIVE_PRESETS, PRESET_COLORES, es_separador,
    MODEL_SPECS_IMAGEN, MODEL_SPECS, get_image_model_specs,
    RATIOS_IMAGEN, RATIOS_VIDEO,
    PLATAFORMAS_IMAGEN, PLATAFORMAS_IMAGEN_LISTA,
    PLATAFORMAS_VIDEO, PLATAFORMAS_VIDEO_LISTA,
    PLATAFORMAS_AUDIO, PLATAFORMAS_AUDIO_LISTA,
    MODELOS_IMAGEN_FLAT, MODELOS_VIDEO_FLAT, MODELOS_AUDIO_FLAT,
    MODELOS_POR_PLATAFORMA_IMAGEN,
    MOTORES_VIDEO, MOTORES_AUDIO, MOTOR_DEFAULT,
    DESTINOS, EMOCIONES_AUDIO, VOCES_AUDIO, IDIOMAS_AUDIO,
    ESTILO_NEGATIVO_AUTO, get_theme_colors,
)
from workers import detectar_idioma_es
from modules.windows import abrir_personajes, abrir_loras, abrir_lista
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app import ArquitectoApp

class UIBuildersMixin:
    """Mixin containing all UI construction methods."""

    def _build_header(self):
        # Colores adaptativos según tema
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        hdr_bg = c["hdr_bg"]
        hdr_text = c["hdr_text"]
        hdr_label = c["hdr_label"]
        combo_bg = c["combo_bg"]
        combo_border = c["combo_border"]
        combo_btn = c["combo_btn"]
        btn_bg = c["btn_bg"]
        btn_hover = c["btn_hover"]
        key_bg = c["key_bg"]
        key_hover = c["key_hover"]

        frame = ctk.CTkFrame(self, fg_color=hdr_bg, corner_radius=0)
        frame.pack(fill="x")
        self._header_frame = frame
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(pady=6, padx=16, fill="x")

        # Cerebro (selector multi-LLM) — lado izquierdo
        frame_llm = ctk.CTkFrame(inner, fg_color="transparent")
        frame_llm.pack(side="left", padx=20)
        self._lbl_cerebro = ctk.CTkLabel(frame_llm, text="Cerebro:", font=ctk.CTkFont(size=11), fg_color="transparent", text_color=hdr_label)
        self._lbl_cerebro.pack(side="left", padx=(0, 4))
        # Importar dinámicamente la lista de providers
        try:
            from api_clients import LLM_PROVIDERS
            self._llm_providers_dict = LLM_PROVIDERS

            # Construir labels con indicador visual de estado:
            # ✅ = key configurada (provider disponible)
            # 🔒 = sin key (al pulsarlo se abre el wizard automáticamente)
            def _label_con_estado(pid: str, label: str) -> str:
                try:
                    prov = self.clients.providers.get(pid) if hasattr(self.clients, "providers") else None
                    ok = bool(prov and prov.disponible())
                except Exception:
                    ok = False
                icon = "✅" if ok else "🔒"
                return f"{icon} {label}"

            lista_llms = [_label_con_estado(pid, info["label"]) for pid, info in LLM_PROVIDERS.items()]
            # Mapeo label-con-icono → provider_id para poder identificar
            self._llm_label_to_id = {
                _label_con_estado(pid, info["label"]): pid
                for pid, info in LLM_PROVIDERS.items()
            }
            # Guardar referencia para refrescar luego (al cambiar de cerebro o al guardar key)
            self._llm_lista_llms = lista_llms
            self._llm_label_con_estado_fn = _label_con_estado

            # Determinar valor inicial según provider activo
            try:
                pid_activo = self.clients.provider_activo_id if hasattr(self.clients, 'provider_activo_id') else "deepseek"
                info_activa = LLM_PROVIDERS.get(pid_activo, {})
                label_inicial = _label_con_estado(pid_activo, info_activa.get("label", ""))
                if label_inicial in lista_llms:
                    self.llm_var.set(label_inicial)
                else:
                    self.llm_var.set(lista_llms[0])
            except Exception as e:
                logger.debug(f"[silent] {e}")
        except Exception:
            # Fallback al sistema antiguo si falla algo
            lista_llms = ["DeepSeek V3", "Google Gemini", "OpenAI GPT-4o", "Local (Ollama)"]
            self._llm_label_to_id = {}
        self.combo_llm = ctk.CTkComboBox(frame_llm, values=lista_llms, variable=self.llm_var, width=240, height=28,
                                          fg_color=combo_bg, border_color=combo_border, button_color=combo_btn,
                                          text_color=hdr_text, font=ctk.CTkFont(size=11),
                                          command=self._on_llm_cambio)
        self.combo_llm.pack(side="left")
        # Botón 🔑 para configurar API keys
        # NOTA v1.0: el color de este botón actúa también como indicador del
        # estado del proveedor — verde si está disponible, ámbar si no. Lo
        # actualiza self._actualizar_indicador_proveedor() (en app.py).
        self._btn_key = ctk.CTkButton(frame_llm, text="🔑", width=30, height=28,
                      fg_color=key_bg, hover_color=key_hover,
                      font=ctk.CTkFont(size=12),
                      command=self._cmd_configurar_api_keys)
        self._btn_key.pack(side="left", padx=(4, 0))
        # Tooltip si CTkToolTip está instalado
        try:
            CTkToolTip(self._btn_key, message="Click: configurar API keys\n(verde = disponible, ámbar = sin configurar)")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # Botones gestión (derecha) — MENÚS DESPLEGABLES por grupo
        menu_style = {"height": 28, "font": ctk.CTkFont(size=11, weight="bold"), "corner_radius": 6,
                      "fg_color": btn_bg, "button_color": btn_bg, "button_hover_color": btn_hover,
                      "text_color": hdr_text}

        # GRUPOS: (label, color_borde, items[(label, command)])
        # Headers ordenados alfabéticamente (Análisis → Backup → Datos → Herramientas → Plantillas → UI → Workflow).
        # Items dentro de cada menú también ordenados alfabéticamente (ignorando el emoji inicial).
        # NOTA: ADN Visual y Análisis Inverso NO se duplican aquí: ya están como botones grandes en la barra del medio.
        grupos_menus = [
            ("📊 Análisis", "#8e4ab0", [
                ("🚀  Auto-mejora", self._cmd_automejora_periodica),
                ("📝  Crítica historial", self._cmd_critica_historial),
                ("📈  Estadísticas", self._abrir_estadisticas),
                ("📖  Modo educativo", self._cmd_modo_educativo),
                ("📚  Tutorial completo", self._abrir_tutorial),
            ]),
            ("💾 Backup", "#a04545", [
                ("💼  Backup completo", self._cmd_backup_completo),
                ("📊  Exportar CSV", self._cmd_exportar_csv),
                ("📂  Restaurar backup", self._cmd_restore_completo),
            ]),
            ("📁 Datos", "#3d7a9c", [
                ("🌟  Estrellas", lambda: abrir_lista(self, "estrellas", "🌟 Prompts Estrella", "#4a2800")),
                ("⭐  Favoritos", lambda: abrir_lista(self, "favoritos", "⭐ Prompts Favoritos", "#3a3000")),
                ("📋  Historial", lambda: abrir_lista(self, "historial", "📋 Historial de Prompts", "#1a2a3a")),
                ("🔗  LoRAs", lambda: abrir_loras(self)),
                ("🧑  Personajes", lambda: abrir_personajes(self)),
            ]),
            ("🛠 Herramientas", "#c97a2e", [
                ("🔒  Anclaje rasgos (consistencia)", self._cmd_anclaje_visual),
                ("🎭  Detectar estilo (3 imágenes)", self._cmd_companero_moodboard),
                ("📤  Export CLI", self._cmd_export_cli),
                ("💼  Modo Cliente", self._cmd_modo_cliente),
                ("🧰  Negative builder", self._cmd_negative_builder),
                ("🎨  Paleta colores", self._cmd_color_palette),
            ]),
            ("📝 Plantillas", "#2ea866", [
                ("🏷 Añadir tags (al prompt)", self._abrir_snippets),
                ("🧬  Biblioteca ADN", self._cmd_ver_biblioteca_adn),
                ("⚡  Expansión rápida (en idea)", self._cmd_gestionar_snippets),
                ("📐  Fórmulas", self._abrir_formulas),
                ("📋  Plantillas", self._cmd_plantillas_populares),
                ("💎  Seeds favoritos", self._abrir_seeds_favoritos),
            ]),
            ("🎨 UI", "#7a7a8a", [
                ("⚙️  Ajustes", self.cmd_preferencias),
                ("⌨️  Atajos teclado", self._cmd_mostrar_atajos),
                ("📚  Biblioteca", self._abrir_biblioteca),
                ("🌗  Cambiar tema", self._cmd_toggle_tema),
                ("🏠  Dashboard", self._cmd_dashboard),
                ("🎯  Modo Focus", self._cmd_modo_focus),
            ]),
            ("⚙️ Workflow", "#c9b32e", [
                ("🆚  A/B Testing", self._cmd_ab_testing),
                ("🔎  Búsqueda global", self._cmd_busqueda_global),
                ("⏰  Cron prompts", self._cmd_cron_prompts),
                ("🎙 Grabar sesión", self._cmd_sesion_grabar_toggle),
                ("👥  Grupo personajes", self._cmd_grupo_personajes),
                ("🔄  Macros", self._abrir_macros),
                ("📁  Proyectos", self._cmd_proyectos),
                ("📑  Versiones prompt", self._cmd_versiones_prompt),
            ]),
        ]

        self._header_menus = []
        self._header_btns = []
        self._active_menu_popup = None
        self._active_menu_label = None

        def _close_menu():
            try:
                popup = getattr(self, '_active_menu_popup', None)
                if popup and popup.winfo_exists():
                    popup.destroy()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            self._active_menu_popup = None
            self._active_menu_label = None

        def _on_global_click(event):
            popup = getattr(self, '_active_menu_popup', None)
            if not popup or not popup.winfo_exists():
                return
            try:
                px, py = popup.winfo_rootx(), popup.winfo_rooty()
                pw, ph = popup.winfo_width(), popup.winfo_height()
                if px <= event.x_root <= px + pw and py <= event.y_root <= py + ph:
                    return
                for bb, _, _, _ in self._header_menus:
                    bx, by, bw, bh = bb.winfo_rootx(), bb.winfo_rooty(), bb.winfo_width(), bb.winfo_height()
                    if bx <= event.x_root <= bx + bw and by <= event.y_root <= by + bh:
                        return
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            _close_menu()

        self.bind("<Button-1>", _on_global_click, add="+")

        def _make_toggle(lg, il, cb):
            def _toggle():
                popup = getattr(self, '_active_menu_popup', None)
                if self._active_menu_label == lg and popup and popup.winfo_exists():
                    _close_menu()
                    return
                _close_menu()
                btn_real = None
                for bb, lg2, _, _ in self._header_menus:
                    if lg2 == lg:
                        btn_real = bb
                        break
                if btn_real is None:
                    return
                new_popup = GPromptWindow(self)
                self._active_menu_popup = new_popup
                self._active_menu_label = lg
                new_popup.title(lg)
                new_popup.overrideredirect(True)
                new_popup.attributes("-topmost", True)
                try:
                    abs_x = btn_real.winfo_rootx()
                    abs_y = btn_real.winfo_rooty() + btn_real.winfo_height() + 4
                except Exception:
                    abs_x, abs_y = 200, 100
                new_popup.geometry(f"+{abs_x}+{abs_y}")

                is_lt = ctk.get_appearance_mode().lower() == "light"
                bg_frame = ctk.CTkFrame(new_popup, fg_color="#ffffff" if is_lt else "#1f2937", border_color=cb, border_width=2, corner_radius=8)
                bg_frame.pack(fill="both", expand=True, padx=2, pady=2)

                for item_label, item_cmd in il:
                    btn_item = ctk.CTkButton(bg_frame, text=item_label, width=220, height=30,
                                              fg_color="transparent", hover_color="#e5e7eb" if is_lt else "#374151",
                                              text_color="#111827" if is_lt else "#e5e7eb", font=ctk.CTkFont(size=11),
                                              anchor="w", corner_radius=4,
                                              command=lambda c=item_cmd: (c(), _close_menu()))
                    btn_item.pack(fill="x", padx=4, pady=2)

                new_popup.bind("<Escape>", lambda e: _close_menu())
                new_popup.focus_set()
            return _toggle

        # Frame para menus — alineado a la derecha del header
        frame_menus = ctk.CTkFrame(inner, fg_color="transparent")
        frame_menus.pack(side="right", padx=(16, 0))

        for label_grupo, color_borde, items in grupos_menus:
            btn = ctk.CTkButton(frame_menus, text=label_grupo, width=120, height=28,
                                fg_color=btn_bg, hover_color=btn_hover,
                                border_color=color_borde, border_width=2,
                                corner_radius=6, font=ctk.CTkFont(size=11, weight="bold"),
                                text_color=color_borde,
                                command=_make_toggle(label_grupo, items, color_borde),
                                anchor="w")
            btn.pack(side="left", padx=2)

            self._header_menus.append((btn, label_grupo, color_borde, items))
            self._header_btns.append(btn)

        # ── Modo compacto responsivo (v1.0) ──
        # Si la ventana es estrecha (<1180px), reducir labels a solo emoji
        # para que quepan los 7 menús del header.
        self._header_compacto = False
        self._header_labels_originales = {btn: btn.cget("text") for btn in self._header_btns}

        def _on_resize(event=None):
            try:
                if event is not None and event.widget is not self:
                    return
                ancho = self.winfo_width()
                debe_compactar = ancho < 1180
                if debe_compactar == self._header_compacto:
                    return
                self._header_compacto = debe_compactar
                for btn in self._header_btns:
                    label_orig = self._header_labels_originales.get(btn, "")
                    if debe_compactar:
                        # Solo emoji (la primera "palabra" antes del espacio)
                        emoji = label_orig.split(" ")[0] if " " in label_orig else label_orig
                        btn.configure(text=emoji, width=42)
                    else:
                        btn.configure(text=label_orig, width=120)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        self.bind("<Configure>", _on_resize, add="+")
        self.after(200, _on_resize)

    def _refrescar_indicadores_llm(self):
        """Recalcula los iconos ✅/🔒 del desplegable de cerebro.

        Se llama tras cambiar de proveedor o guardar una key nueva, para que
        el desplegable refleje el estado real sin reiniciar la app.
        """
        try:
            if not hasattr(self, "_llm_label_con_estado_fn"):
                return
            from api_clients import LLM_PROVIDERS
            label_fn = self._llm_label_con_estado_fn

            nueva_lista = [label_fn(pid, info["label"]) for pid, info in LLM_PROVIDERS.items()]
            self._llm_label_to_id = {
                label_fn(pid, info["label"]): pid for pid, info in LLM_PROVIDERS.items()
            }

            # Recordar selección actual (mapeada a pid para reasignar tras refresh)
            pid_actual = None
            try:
                if hasattr(self.clients, "provider_activo_id"):
                    pid_actual = self.clients.provider_activo_id
            except Exception:
                pid_actual = None

            if hasattr(self, "combo_llm"):
                self.combo_llm.configure(values=nueva_lista)
                if pid_actual:
                    info_act = LLM_PROVIDERS.get(pid_actual, {})
                    nuevo_label = label_fn(pid_actual, info_act.get("label", ""))
                    if nuevo_label in nueva_lista:
                        self.llm_var.set(nuevo_label)
        except Exception as e:
            logger.debug(f"[silent] refrescar indicadores llm: {e}")

    def _build_modo(self):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        modo_bg = c["modo_bg"]
        modo_label = c["modo_label"]

        frame = ctk.CTkFrame(self, fg_color=modo_bg, corner_radius=0)
        frame.pack(fill="x", padx=16, pady=(6, 2))
        self._modo_frame = frame
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=8, pady=6)

        seg = ctk.CTkSegmentedButton(inner, values=["Imagen", "Vídeo", "Audio"],
                                      command=self._on_segmento_modo, height=28,
                                      font=ctk.CTkFont(size=11))
        seg.set("Imagen")
        seg.pack(side="left", padx=(0, 12))
        self._seg_modo = seg

        self._lbl_plataforma = ctk.CTkLabel(inner, text="Plataforma:", font=ctk.CTkFont(size=11), fg_color="transparent", text_color=modo_label)
        self._lbl_plataforma.pack(side="left", padx=(0, 4))
        self.combo_plataforma = ctk.CTkComboBox(inner, values=PLATAFORMAS_IMAGEN_LISTA, variable=self.plataforma_var,
                                                 width=180, height=28, font=ctk.CTkFont(size=11),
                                                 command=self._on_plataforma_cambio)
        self.combo_plataforma.pack(side="left", padx=(0, 10))

        sw_style = {
            "font": ctk.CTkFont(size=11, weight="bold"),
            "height": 26, "width": 50, "corner_radius": 13,
            "button_color": "#374151" if is_light else "#ffffff",
            "button_hover_color": "#1f2937" if is_light else "#f3f4f6",
            "border_width": 2,
        }

        nsfw_text_on = c["nsfw_text_on"]
        nsfw_text_off = c["nsfw_text_off"]
        nsfw_border_on = c["nsfw_border_on"]
        nsfw_border_off = c["nsfw_border_off"]
        nsfw_fg = c["nsfw_fg"]

        def _toggle_nsfw_visual():
            self.reiniciar_memoria()
            if self.switch_nsfw_var.get():
                self.switch_nsfw.configure(text_color=nsfw_text_on, border_color=nsfw_border_on)
            else:
                self.switch_nsfw.configure(text_color=nsfw_text_off, border_color=nsfw_border_off)

        self.switch_nsfw = ctk.CTkSwitch(inner, text="🔞 NSFW", variable=self.switch_nsfw_var,
                                          command=_toggle_nsfw_visual,
                                          progress_color="#dc2626",
                                          fg_color=nsfw_fg,
                                          border_color=nsfw_border_off,
                                          text_color=nsfw_text_off,
                                          **sw_style)
        self.switch_nsfw.pack(side="right", padx=6)
        CTkToolTip(self.switch_nsfw, message="Activa contenido adulto en los prompts.", delay=0.5)

        def _toggle_trad_visual():
            if self.switch_traduccion_var.get():
                self.switch_trad.configure(text_color=c["trad_text_on"], border_color=c["trad_border_on"])
            else:
                self.switch_trad.configure(text_color=c["fg_dark_text"], border_color=c["fg_dark_border"])

        self.switch_trad = ctk.CTkSwitch(inner, text="🌐 Auto-trad", variable=self.switch_traduccion_var,
                                          command=_toggle_trad_visual,
                                          progress_color="#2563eb",
                                          fg_color=c["fg_dark"],
                                          border_color=c["fg_dark_border"],
                                          text_color=c["fg_dark_text"],
                                          **sw_style)
        self.switch_trad.pack(side="right", padx=6)
        CTkToolTip(self.switch_trad, message="Traduce tu idea al inglés antes de procesarla.", delay=0.5)
        self._sw_trad = self.switch_trad
        self._sw_trad_callback = _toggle_trad_visual

    def _on_segmento_modo(self, valor):
        mapa = {"Imagen": "imagen", "Vídeo": "video", "Audio": "audio"}
        self.modo_var.set(mapa.get(valor, "imagen"))
        self._on_modo_cambio()

    def _build_video_panel(self):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        lbl_color = c["panel_text"]

        self.frame_video = ctk.CTkFrame(self, height=42, fg_color=c["panel_bg"])
        self.frame_video.pack_propagate(False)

        ctk.CTkLabel(self.frame_video, text="Modelo:",
                     font=ctk.CTkFont(weight="bold"),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=15)
        self.combo_modelo_video = ctk.CTkComboBox(self.frame_video, values=MODELOS_VIDEO_FLAT, width=215, command=self._on_motor_cambio)
        self.combo_modelo_video.set("Kling 3.0")
        self.combo_modelo_video.pack(side="left", padx=5)

        ctk.CTkLabel(self.frame_video, text="Duración:",
                     font=ctk.CTkFont(weight="bold"),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(15, 5))
        ctk.CTkEntry(self.frame_video, textvariable=self.duracion_var, width=70).pack(side="left", padx=5)
        ctk.CTkLabel(self.frame_video, text="Ratio:",
                     font=ctk.CTkFont(weight="bold"),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(10, 5))
        self.combo_ratio_v = ctk.CTkComboBox(self.frame_video, values=RATIOS_VIDEO, variable=self.ratio_var, width=85, command=lambda v: self.ratio_var.set(v))
        self.combo_ratio_v.set("16:9")
        self.combo_ratio_v.pack(side="left", padx=5)

        # Destino al lado del ratio
        ctk.CTkLabel(self.frame_video, text="Destino:",
                     font=ctk.CTkFont(weight="bold"),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(15, 5))
        self.combo_destino_vid = ctk.CTkComboBox(self.frame_video, values=DESTINOS, variable=self.destino_var, width=140,
                                                   font=ctk.CTkFont(size=11), command=self._on_destino_cambio)
        self.combo_destino_vid.pack(side="left", padx=5)

    def _build_audio_panel(self):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        lbl_color = c["panel_text"]

        self.frame_audio = ctk.CTkFrame(self, fg_color=c["panel_bg"])

        # Fila 1: Modelo + Destino + Instrumental
        row1 = ctk.CTkFrame(self.frame_audio, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(5, 2))

        ctk.CTkLabel(row1, text="Modelo:", font=ctk.CTkFont(weight="bold"),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(5, 5))
        self.combo_modelo_audio = ctk.CTkComboBox(row1, values=MODELOS_AUDIO_FLAT, width=215, command=self._on_motor_audio_cambio)
        self.combo_modelo_audio.set("Suno v5")
        self.combo_modelo_audio.pack(side="left", padx=5)

        # Destino al lado del modelo
        ctk.CTkLabel(row1, text="Destino:", font=ctk.CTkFont(weight="bold"),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(15, 5))
        self.combo_destino_aud = ctk.CTkComboBox(row1, values=DESTINOS, variable=self.destino_var, width=140,
                                                   font=ctk.CTkFont(size=11), command=self._on_destino_cambio)
        self.combo_destino_aud.pack(side="left", padx=5)

        self.switch_instrumental_var = ctk.BooleanVar(value=False)

        def _toggle_instr_visual():
            self.reiniciar_memoria()
            if self.switch_instrumental_var.get():
                self.switch_instrumental.configure(text_color=c["instr_active_text"], border_color=c["instr_active_border"])
            else:
                self.switch_instrumental.configure(text_color=c["fg_dark_text"], border_color=c["fg_dark_border"])

        self.switch_instrumental = ctk.CTkSwitch(row1, text="🎹 Instrumental",
                                                   variable=self.switch_instrumental_var,
                                                   command=_toggle_instr_visual,
                                                   progress_color="#7c3aed",
                                                   fg_color=c["fg_dark"],
                                                   border_color=c["fg_dark_border"],
                                                   border_width=2,
                                                   text_color=c["fg_dark_text"],
                                                   font=ctk.CTkFont(size=11, weight="bold"),
                                                   height=26, width=50, corner_radius=13,
                                                   button_color="#374151" if is_light else "#ffffff",
                                                   button_hover_color="#1f2937" if is_light else "#f3f4f6")
        self.switch_instrumental.pack(side="left", padx=15)

        # Fila 2: Emoción + Voz + Idioma
        row2 = ctk.CTkFrame(self.frame_audio, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(0, 5))

        self.emocion_var = ctk.StringVar(value="— Emoción —")
        ctk.CTkLabel(row2, text="Emoción:", font=ctk.CTkFont(weight="bold", size=11),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(5, 3))
        self.combo_emocion = ctk.CTkComboBox(row2, values=["— Emoción —"] + EMOCIONES_AUDIO, variable=self.emocion_var, width=130, command=self._on_audio_filtro_cambio)
        self.combo_emocion.pack(side="left", padx=(0, 10))

        self.voz_var = ctk.StringVar(value="— Voz —")
        ctk.CTkLabel(row2, text="Voz:", font=ctk.CTkFont(weight="bold", size=11),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(0, 3))
        self.combo_voz = ctk.CTkComboBox(row2, values=["— Voz —"] + VOCES_AUDIO, variable=self.voz_var, width=155, command=self._on_audio_filtro_cambio)
        self.combo_voz.pack(side="left", padx=(0, 10))

        self.idioma_audio_var = ctk.StringVar(value="— Idioma —")
        ctk.CTkLabel(row2, text="Idioma:", font=ctk.CTkFont(weight="bold", size=11),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(0, 3))
        self.combo_idioma_audio = ctk.CTkComboBox(row2, values=["— Idioma —"] + IDIOMAS_AUDIO, variable=self.idioma_audio_var, width=160, command=self._on_audio_filtro_cambio)
        self.combo_idioma_audio.pack(side="left", padx=(0, 5))

    def _build_modelo_imagen_panel(self):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        lbl_color = c["panel_label"]
        ratio_btn_bg = "#ffffff" if is_light else "#1a2030"
        ratio_btn_hover = "#dbeafe" if is_light else "#2a3a50"

        self.frame_modelo_imagen = ctk.CTkFrame(self, fg_color="transparent")

        inner = ctk.CTkFrame(self.frame_modelo_imagen, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=2)

        # Modelo
        f1 = ctk.CTkFrame(inner, fg_color="transparent")
        f1.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(f1, text="Modelo", font=ctk.CTkFont(size=10),
                     fg_color="transparent", text_color=lbl_color).pack(anchor="w")
        self.combo_modelo_imagen = ctk.CTkComboBox(f1, values=MODELOS_IMAGEN_FLAT, width=220, height=28,
                                                    font=ctk.CTkFont(size=11), command=self._on_modelo_imagen_cambio)
        self.combo_modelo_imagen.set("Z Image Turbo")
        self.combo_modelo_imagen.pack()
        self._tooltip_modelo_actual = CTkToolTip(self.combo_modelo_imagen, delay=0.6, message="Pasa el cursor para info del modelo")

        # Ratio
        f2 = ctk.CTkFrame(inner, fg_color="transparent")
        f2.pack(side="left", padx=8)
        ctk.CTkLabel(f2, text="Ratio", font=ctk.CTkFont(size=10),
                     fg_color="transparent", text_color=lbl_color).pack(anchor="w")
        f2_inner = ctk.CTkFrame(f2, fg_color="transparent")
        f2_inner.pack()
        self.combo_ratio = ctk.CTkComboBox(f2_inner, values=RATIOS_IMAGEN, variable=self.ratio_var, width=80, height=28,
                                            font=ctk.CTkFont(size=11), command=lambda v: self.ratio_var.set(v))
        self.combo_ratio.set("1:1")
        self.combo_ratio.pack(side="left")

        # Botones rápidos de ratio (visuales)
        self.ratio_btns = {}
        ratios_quick = [
            ("⬜", "1:1",  "Cuadrado (Instagram post)"),
            ("📱", "9:16", "Vertical (Stories/TikTok/Reels)"),
            ("🖥", "16:9", "Horizontal (YouTube/Web)"),
            ("📸", "2:3",  "Foto vertical (retrato)"),
            ("🖼", "3:2",  "Foto horizontal (paisaje)"),
        ]
        for icono, ratio_val, tip in ratios_quick:
            btn = ctk.CTkButton(f2_inner, text=icono, width=24, height=28,
                                  fg_color=ratio_btn_bg, hover_color=ratio_btn_hover,
                                  text_color=c["panel_text"],
                                  font=ctk.CTkFont(size=11),
                                  command=lambda r=ratio_val: self._aplicar_ratio_rapido(r))
            btn.pack(side="left", padx=1)
            CTkToolTip(btn, delay=0.3, message=f"{ratio_val} — {tip}")
            self.ratio_btns[ratio_val] = btn

        # Destino — al final de la fila
        f0 = ctk.CTkFrame(inner, fg_color="transparent")
        f0.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(f0, text="Destino", font=ctk.CTkFont(size=10),
                     fg_color="transparent", text_color=lbl_color).pack(anchor="w")
        self.combo_destino_img = ctk.CTkComboBox(f0, values=DESTINOS, variable=self.destino_var, width=140, height=28,
                                                   font=ctk.CTkFont(size=11), command=self._on_destino_cambio)
        self.combo_destino_img.pack()

    def _aplicar_ratio_rapido(self, ratio):
        """Aplica un ratio rápido si está disponible para el modelo actual."""
        ratios_dispo = self.combo_ratio.cget("values")
        if ratio in ratios_dispo:
            self.ratio_var.set(ratio)
            self.combo_ratio.set(ratio)
            self.set_estado(f"📐 Ratio {ratio} aplicado", "#3498db")
        else:
            self.set_estado(f"⚠️ Ratio {ratio} no disponible para este modelo", "#e67e22")

    def _build_destino_panel(self):
        """Panel Destino — ahora oculto, los combos están integrados en cada panel de modo."""
        self.frame_destino = ctk.CTkFrame(self, fg_color="transparent", height=1)
        # Frame vacío, solo para mantener compatibilidad
        # El combo destino real está dentro de cada panel de modo (imagen/video/audio)
        self.combo_destino = self.combo_destino_img if hasattr(self, 'combo_destino_img') else None

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

    def _build_tabs_centrales(self):
        # no lo pinta bien en modo light si lo dejamos sin especificar
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        tab_bg = c["panel_bg"]              # gris muy claro / azul oscuro
        seg_bg = "#e5e7eb" if is_light else "#1f2937"
        seg_sel = "#2563eb" if is_light else "#3b82f6"
        seg_hov = "#dbeafe" if is_light else "#374151"

        self.tabview = ctk.CTkTabview(
            self, height=140,
            fg_color=tab_bg, bg_color=tab_bg,
            segmented_button_fg_color=seg_bg,
            segmented_button_selected_color=seg_sel,
            segmented_button_selected_hover_color=seg_sel,
            segmented_button_unselected_color=seg_bg,
            segmented_button_unselected_hover_color=seg_hov,
            text_color=c["panel_text"],
        )
        self.tabview.pack(pady=2, padx=20, fill="x")

        self.tabview.add("⚙️ Ajustes Extra")
        self.tabview.add("🎨 Estilos")
        self.tabview.add("🚫 Negativos")

        # Forzar el color del contenido de cada tab
        for tab_name in ("⚙️ Ajustes Extra", "🎨 Estilos", "🚫 Negativos"):
            try:
                self.tabview.tab(tab_name).configure(fg_color=tab_bg, bg_color=tab_bg)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        # Tab 1: Ajustes Extra
        self._build_ajustes_extra(self.tabview.tab("⚙️ Ajustes Extra"))

        # Tab 2: Estilos
        self._build_estilos(self.tabview.tab("🎨 Estilos"))

        # Tab 3: Negativos (Permanece para no destruir widgets)
        tab_neg = self.tabview.tab("🚫 Negativos")
        self.frame_neg_outer = ctk.CTkFrame(tab_neg, fg_color=tab_bg)
        self._build_negative(self.frame_neg_outer)

        self.lbl_neg_disabled = ctk.CTkLabel(
            tab_neg, text="🚫 El modelo o plataforma actual NO utiliza Negative Prompts.",
            fg_color="transparent",
            text_color=c["muted_text"], font=ctk.CTkFont(size=12, slant="italic"))

    def _build_ajustes_extra(self, parent):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        tab_bg = c["panel_bg"]

        self.frame_pers_lora = ctk.CTkFrame(parent, fg_color=tab_bg)
        self.frame_pers_lora.pack(fill="x", pady=(2, 1))

        ctk.CTkLabel(self.frame_pers_lora, text="🧑 Personaje:",
                     font=ctk.CTkFont(weight="bold", size=11),
                     fg_color="transparent",
                     text_color=c["panel_text"]).pack(side="left", padx=(5, 5))
        self.combo_personaje = ctk.CTkComboBox(self.frame_pers_lora, values=["— Sin personaje —"], width=160,
                                                fg_color=c["combo_bg"], border_color=c["combo_border"],
                                                text_color=c["hdr_text"],
                                                command=self._on_personaje_selected)
        self.combo_personaje.pack(side="left", padx=5)

        ctk.CTkLabel(self.frame_pers_lora, text="🔗 LoRA:",
                     font=ctk.CTkFont(weight="bold", size=11),
                     fg_color="transparent",
                     text_color=c["panel_text"]).pack(side="left", padx=(15, 5))
        self.combo_lora = ctk.CTkComboBox(self.frame_pers_lora, values=["— Sin LoRA —"], width=160,
                                            fg_color=c["combo_bg"], border_color=c["combo_border"],
                                            text_color=c["hdr_text"],
                                            command=lambda v: (
                                                self._sesion_log(f"🔗 LoRA → {v}") if hasattr(self, "_sesion_eventos") else None,
                                                self._actualizar_lora_trigger_visible()
                                            ))
        self.combo_lora.pack(side="left", padx=5)
        # Label trigger visible (Mejora bonus LoRAs)
        lora_color = "#7c3aed" if is_light else "#9b59b6"
        self.lbl_lora_trigger = ctk.CTkLabel(self.frame_pers_lora, text="",
                                               font=ctk.CTkFont(family="Consolas", size=9),
                                               fg_color="transparent",
                                               text_color=lora_color)
        self.lbl_lora_trigger.pack(side="left", padx=(6, 0))

        self.frame_plantilla_brief = ctk.CTkFrame(parent, fg_color=tab_bg)
        self.frame_plantilla_brief.pack(fill="x", pady=1)

        ctk.CTkLabel(self.frame_plantilla_brief, text="📐 Plantilla:",
                     font=ctk.CTkFont(weight="bold", size=11),
                     fg_color="transparent",
                     text_color=c["panel_text"]).pack(side="left", padx=(5, 5))
        self.combo_plantilla = ctk.CTkComboBox(self.frame_plantilla_brief, values=["— Sin plantilla —"], width=180,
                                                fg_color=c["combo_bg"], border_color=c["combo_border"],
                                                text_color=c["hdr_text"], command=self._cargar_plantilla)
        self.combo_plantilla.pack(side="left", padx=5)
        ctk.CTkButton(self.frame_plantilla_brief, text="💾 Guardar actual", width=120, height=28,
                      fg_color="#5b2c8e", hover_color="#3d1a6a", text_color="#ffffff",
                      command=self._cmd_guardar_plantilla).pack(side="left", padx=(10, 4))
        ctk.CTkButton(self.frame_plantilla_brief, text="🗑 Borrar", width=80, height=28,
                      fg_color="#6a1a1a", hover_color="#4a0f0f", text_color="#ffffff",
                      command=self._cmd_borrar_plantilla).pack(side="left", padx=2)

        def _toggle_brief_visual():
            self._on_brief_cambio()
            if self.brief_var.get():
                self.switch_brief.configure(text_color="#fcd34d", border_color="#f59e0b")
            else:
                col_off = "#6b7280" if is_light else "#9ca3af"
                bord_off = "#d1d5db" if is_light else "#374151"
                self.switch_brief.configure(text_color=col_off, border_color=bord_off)

        sw_text_off = "#6b7280" if is_light else "#9ca3af"
        sw_bord_off = "#d1d5db" if is_light else "#374151"
        sw_fg_off = "#f3f4f6" if is_light else "#1f2937"
        self.switch_brief = ctk.CTkSwitch(
            self.frame_plantilla_brief, text="⚡ Modo Brief", variable=self.brief_var,
            command=_toggle_brief_visual,
            progress_color="#d97706",
            fg_color=sw_fg_off,
            border_color=sw_bord_off,
            text_color=sw_text_off,
            border_width=2,
            font=ctk.CTkFont(size=11, weight="bold"),
            height=26, width=50, corner_radius=13,
            button_color="#374151" if is_light else "#ffffff",
            button_hover_color="#1f2937" if is_light else "#f3f4f6")
        self.switch_brief.pack(side="right", padx=15)
        CTkToolTip(self.switch_brief, message="Activa reglas de ANUNCIO PUBLICITARIO: gancho 2s, vertical 9:16, 3 beats narrativos.", delay=0.5)
        self._sw_brief_callback = _toggle_brief_visual

        # ─── Imagen referencia DENTRO de Ajustes Extra (debajo de Plantilla) ───
        self.frame_imgref_inner = ctk.CTkFrame(parent, fg_color=tab_bg)
        self.frame_imgref_inner.pack(fill="x", pady=(1, 2))

        ctk.CTkLabel(self.frame_imgref_inner, text="🖼 Imagen ref:",
                     font=ctk.CTkFont(weight="bold", size=11),
                     fg_color="transparent",
                     text_color=c["panel_text"]).pack(side="left", padx=(5, 5))
        self.btn_cargar_img = ctk.CTkButton(self.frame_imgref_inner, text="📂 Cargar", width=80, height=28,
                                             text_color="#ffffff",
                                             command=self._cargar_imagen)
        self.btn_cargar_img.pack(side="left", padx=3)
        ctk.CTkButton(self.frame_imgref_inner, text="🗑", width=30, height=28,
                      fg_color="#6a1a1a" if is_light else "#444",
                      hover_color="#4a0f0f" if is_light else "#333",
                      text_color="#ffffff",
                      command=self._limpiar_imagen).pack(side="left", padx=2)
        self.lbl_img_preview = ctk.CTkLabel(self.frame_imgref_inner, text="", width=34, height=34)
        self.lbl_img_preview.pack(side="left", padx=4)
        self.lbl_img_nombre = ctk.CTkLabel(self.frame_imgref_inner, text="Sin imagen",
                                            font=ctk.CTkFont(size=10),
                                            fg_color="transparent",
                                            text_color=c["muted_text"])
        self.lbl_img_nombre.pack(side="left", padx=2)

        # Historial de imágenes (recientes)
        sep_color = "#9ca3af" if is_light else "#333333"
        ctk.CTkLabel(self.frame_imgref_inner, text="│",
                     fg_color="transparent",
                     text_color=sep_color).pack(side="left", padx=4)
        ctk.CTkLabel(self.frame_imgref_inner, text="Recientes:",
                     font=ctk.CTkFont(size=9),
                     fg_color="transparent",
                     text_color=c["muted_text"]).pack(side="left", padx=2)
        self._img_history_frame = ctk.CTkFrame(self.frame_imgref_inner, fg_color=tab_bg)
        self._img_history_frame.pack(side="left", padx=2)
        self._img_history = []
        self._MAX_IMG_HISTORY = 6

    def _build_estilos(self, parent):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        tab_bg = c["panel_bg"]

        self._frame_estilos_header = ctk.CTkFrame(parent, fg_color=tab_bg)
        self._frame_estilos_header.pack(fill="x", padx=5, pady=(0, 2))
        header_estilos = self._frame_estilos_header  # alias para legibilidad

        self.entry_busqueda = ctk.CTkEntry(header_estilos, placeholder_text="🔍 Buscar estilo...", width=180, height=24, font=ctk.CTkFont(size=11))
        self.entry_busqueda.pack(side="left")
        self.entry_busqueda.bind("<KeyRelease>", self._filtrar_estilos)

        btn_sugerir = ctk.CTkButton(header_estilos, text="🎨 Sugerir estilos", width=130, height=24,
                                       fg_color="#3a1a5a", hover_color="#2a0f3a",
                                       text_color="#ffffff",
                                       font=ctk.CTkFont(size=10),
                                       command=self._cmd_sugerir_estilos)
        btn_sugerir.pack(side="left", padx=(8, 0))
        CTkToolTip(btn_sugerir, delay=0.4, message="LLM analiza tu idea y marca 3-6 estilos apropiados automáticamente")

        # Contador y botón limpiar
        self.lbl_estilos_count = ctk.CTkLabel(header_estilos, text="",
                                               font=ctk.CTkFont(size=10),
                                               fg_color="transparent",
                                               text_color=c["muted_text"])
        self.lbl_estilos_count.pack(side="left", padx=(10, 0))

        btn_limpiar_est = ctk.CTkButton(header_estilos, text="🗑", width=28, height=24,
                                          fg_color="transparent",
                                          hover_color="#fee2e2" if is_light else "#3a1a1a",
                                          text_color=c["muted_text"],
                                          font=ctk.CTkFont(size=11),
                                          command=self._limpiar_estilos)
        btn_limpiar_est.pack(side="right", padx=(0, 5))
        CTkToolTip(btn_limpiar_est, delay=0.3, message="Limpiar todos los estilos seleccionados")

        # que en modo light termine pintando blanco-sobre-blanco.
        self.frame_checks = ctk.CTkScrollableFrame(parent, fg_color=c["chk_bg"])
        self.frame_checks.pack(fill="both", expand=True, padx=5, pady=2)

        # Label verde con nombres de estilos seleccionados
        # Usar verde más oscuro en light para que se lea sobre fondo claro
        verde = "#059669" if is_light else "#2ecc71"
        self.lbl_estilos_sel = ctk.CTkLabel(parent, text="",
                                             font=ctk.CTkFont(size=11, weight="bold"),
                                             fg_color="transparent",
                                             text_color=verde,
                                             anchor="w", justify="left")
        self.lbl_estilos_sel.pack(fill="x", padx=8, pady=(0, 4))

        self._construir_checkboxes(ESTILOS_IMAGEN)

    def _limpiar_estilos(self):
        """Desmarca todos los estilos seleccionados."""
        if not hasattr(self, 'estilo_checks'): return
        for n, v in self.estilo_checks.items():
            v.set(False)
        self._actualizar_contador_estilos()
        self.set_estado("🗑 Estilos limpiados")

    def _actualizar_contador_estilos(self):
        """Actualiza el contador y label verde de estilos seleccionados."""
        if not hasattr(self, 'lbl_estilos_count') or not hasattr(self, 'estilo_checks'): return
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        sel = self.estilos_seleccionados()
        n = len(sel)
        if n == 0:
            self.lbl_estilos_count.configure(text="(ninguno)", text_color=c["muted_text"])
            if hasattr(self, 'lbl_estilos_sel'):
                self.lbl_estilos_sel.configure(text="")
        else:
            color_count = "#1d4ed8" if is_light else "#5a8aaa"
            self.lbl_estilos_count.configure(text=f"({n} seleccionado{'s' if n != 1 else ''})",
                                              text_color=color_count)
            if hasattr(self, 'lbl_estilos_sel'):
                self.lbl_estilos_sel.configure(text=f"✦ {' + '.join(sel)}")

    def _build_negative(self, parent):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        tab_bg = c["panel_bg"]

        self._frame_neg_header = ctk.CTkFrame(parent, fg_color=tab_bg)
        self._frame_neg_header.pack(fill="x", pady=(0, 2))
        hdr = self._frame_neg_header  # alias
        ctk.CTkLabel(hdr, text="➕ Negative extra (se añade al base):",
                     font=ctk.CTkFont(weight="bold", size=12),
                     fg_color="transparent",
                     text_color=c["panel_text"]).pack(side="left")
        ctk.CTkButton(hdr, text="🗑 Limpiar", width=80, height=24,
                      fg_color="#dc2626" if is_light else "#444",
                      hover_color="#b91c1c" if is_light else "#222",
                      text_color="#ffffff",
                      command=self._limpiar_negatives).pack(side="right", padx=4)

        self._frame_neg_presets = ctk.CTkFrame(parent, fg_color=tab_bg)
        self._frame_neg_presets.pack(fill="x", pady=(2, 4))
        frame_presets = self._frame_neg_presets  # alias

        for nombre_p in NEGATIVE_PRESETS:
            var = ctk.BooleanVar(value=False)
            self.preset_vars[nombre_p] = var
            fg, hv = PRESET_COLORES.get(nombre_p, ("#333", "#555"))

            def _toggle(n=nombre_p, fg_off=fg):
                self.preset_vars[n].set(not self.preset_vars[n].get())
                activo = self.preset_vars[n].get()
                self.preset_btns[n].configure(fg_color="#2ecc71" if activo else fg_off, text=f"✓ {n}" if activo else n)
                self._rebuild_negative_text()

            btn = ctk.CTkButton(frame_presets, text=nombre_p, height=24, width=100,
                                fg_color=fg, hover_color=hv, text_color="#ffffff",
                                font=ctk.CTkFont(size=10), command=_toggle)
            btn.pack(side="left", padx=2)
            self.preset_btns[nombre_p] = btn

        self.txt_negative = ctk.CTkTextbox(parent, height=36, font=ctk.CTkFont(size=12))
        self.txt_negative.pack(fill="x")
        self.txt_negative.bind("<KeyRelease>", self._validar_negative_length)
        self.txt_negative.bind("<FocusOut>", lambda e: self.reiniciar_memoria())

        # Warning de límite negative
        self.lbl_negative_warning = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=10, weight="bold"),
                                                   fg_color="transparent",
                                                   text_color=c["danger_text"], anchor="w")

    def _toggle(self, n, fg_off):
        """Toggle helper for negative presets."""
        self.preset_vars[n].set(not self.preset_vars[n].get())
        activo = self.preset_vars[n].get()
        self.preset_btns[n].configure(fg_color="#2ecc71" if activo else fg_off, text=f"✓ {n}" if activo else n)
        self._rebuild_negative_text()

    def _build_imagen_ref(self):
        # Frame placeholder (los widgets reales están dentro de la tab "Ajustes Extra")
        self.frame_img_ref = ctk.CTkFrame(self, height=1, fg_color="transparent")
        self.frame_img_ref.pack_propagate(False)
        # No se renderiza nada aquí — los widgets viven en self.frame_imgref_inner
        # dentro de la pestaña "⚙️ Ajustes Extra"
        return

    def _build_entrada(self):
        is_light = _get_real_is_light()
        from config import get_theme_colors
        c = get_theme_colors(is_light)
        self.frame_entrada = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_entrada.pack(pady=(2, 1), padx=16, fill="x")

        # Header con label + botón limpiar
        hdr = ctk.CTkFrame(self.frame_entrada, fg_color="transparent")
        hdr.pack(fill="x", padx=2, pady=(0, 2))
        ctk.CTkLabel(hdr, text="Describe tu idea", font=ctk.CTkFont(size=10), fg_color="transparent", text_color=c["muted_text"]).pack(side="left")
        # Label de autocompletar
        self.lbl_autocomplete = ctk.CTkLabel(hdr, text="", font=ctk.CTkFont(size=9, slant="italic"), fg_color="transparent", text_color="#2563eb" if is_light else "#5a8aaa")
        self.lbl_autocomplete.pack(side="left", padx=(10, 0))
        # ── MEJORA 1: contador en vivo de chars y tokens estimados ──
        self.lbl_idea_counter = ctk.CTkLabel(hdr, text="", font=ctk.CTkFont(size=9), fg_color="transparent", text_color=c["muted_text"])
        self.lbl_idea_counter.pack(side="left", padx=(10, 0))
        # ── MEJORA 2: aviso de idioma detectado ──
        self.lbl_idioma_aviso = ctk.CTkLabel(hdr, text="", font=ctk.CTkFont(size=9, slant="italic"),
                                              fg_color="transparent",
                                              text_color="#f39c12", cursor="hand2")
        self.lbl_idioma_aviso.pack(side="left", padx=(10, 0))
        # Click en el aviso de idioma → toggle auto-trad
        self.lbl_idioma_aviso.bind("<Button-1>", lambda e: self._toggle_auto_trad_desde_aviso())
        btn_clear = ctk.CTkButton(hdr, text="🗑", width=22, height=18, fg_color="transparent",
                                    hover_color="#dc2626" if is_light else "#3a1a1a", font=ctk.CTkFont(size=10),
                                    text_color=c["muted_text"],
                                    command=lambda: self.txt_idea.delete("1.0", "end"))
        btn_clear.pack(side="right")
        CTkToolTip(btn_clear, delay=0.3, message="Limpiar campo idea")

        self.txt_idea = ctk.CTkTextbox(self.frame_entrada, height=90, font=ctk.CTkFont(size=13),
                                        border_width=2, border_color=c["combo_border"] if "combo_border" in c else "#9ca3af", corner_radius=8)
        self.txt_idea.pack(fill="x")
        # Bind para autocompletar
        self.txt_idea.bind("<KeyRelease>", self._on_idea_keyrelease)
        # Menú contextual click derecho (Cortar/Copiar/Pegar/Seleccionar todo)
        self.txt_idea.bind("<Button-3>", self._mostrar_menu_contextual_idea)

        # Barra visual de chars
        self.chars_bar_frame = ctk.CTkFrame(self.frame_entrada, fg_color="#d1d5db" if is_light else "#0a0a14", height=4, corner_radius=2)
        self.chars_bar_frame.pack(fill="x", pady=(2, 0))
        self.chars_bar = ctk.CTkFrame(self.chars_bar_frame, fg_color="#2ecc71", height=4, corner_radius=2)
        self.chars_bar.place(x=0, y=0, relwidth=0, relheight=1)

    def _on_idea_keyrelease(self, event=None):
        """Llamado cuando el usuario teclea en el campo idea."""
        # Snippet expansion (Mejora 7): si pulsa Espacio tras ;palabra, expande
        try:
            if event and event.keysym == "space":
                self._snippet_expand()
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # Autocompletar
        try:
            self._autocompletar_tags(event)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # Actualizar barra visual de chars
        try:
            self._actualizar_barra_chars()
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    def _actualizar_barra_chars(self):
        """Actualiza la barra de caracteres y el contador de tokens según el texto del campo idea."""
        if not hasattr(self, 'chars_bar'): return
        texto = self.txt_idea.get("1.0", "end").strip()
        chars = len(texto)
        # Considerar como "max" la mitad del límite del modelo (la idea no es el prompt final)
        specs = self.get_current_model_specs()
        max_c = (specs.get("max_chars", 1500) if specs else 1500) // 2

        ratio = min(chars / max_c, 1.0) if max_c > 0 else 0
        # Color según ratio
        if ratio < 0.5:
            color = "#2ecc71"  # verde
        elif ratio < 0.8:
            color = "#f39c12"  # amarillo
        else:
            color = "#e74c3c"  # rojo

        try:
            self.chars_bar.configure(fg_color=color)
            self.chars_bar.place_configure(relwidth=ratio)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # ── MEJORA 1: actualizar contador numérico ──
        try:
            if chars == 0:
                self.lbl_idea_counter.configure(text="")
            else:
                # Estimación tokens ≈ chars / 4 (regla típica para inglés)
                tokens_est = max(1, chars // 4)
                self.lbl_idea_counter.configure(
                    text=f"· {chars} chars · ~{tokens_est} tokens · max idea {max_c}",
                    text_color=color
                )
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # ── MEJORA 2: detectar idioma y avisar si auto-trad no concuerda ──
        try:
            self._detectar_idioma_y_avisar(texto)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    def _detectar_idioma_y_avisar(self, texto):
        """Detecta heurísticamente si el texto está en ES o EN y avisa si auto-trad no concuerda."""
        if not hasattr(self, 'lbl_idioma_aviso'): return
        if len(texto) < 25:
            self.lbl_idioma_aviso.configure(text="")
            return
        # Heurística simple: contar palabras-clave de cada idioma
        t = " " + texto.lower() + " "
        es_words = [" el ", " la ", " los ", " las ", " un ", " una ", " de ", " del ", " que ", " es ", " con ", " por ",
                    " para ", " esta ", " este ", " sin ", " pero ", " muy ", " más ", " hay ", " son ", " soy ",
                    " tiene ", " hace ", " mientras ", " sobre ", " hacia ", " desde ", " entre "]
        en_words = [" the ", " a ", " an ", " of ", " to ", " in ", " is ", " are ", " and ", " or ", " for ", " with ",
                    " on ", " at ", " by ", " as ", " from ", " this ", " that ", " these ", " those ", " be ", " was ",
                    " were ", " has ", " have ", " had ", " can ", " will ", " would ", " should "]
        es_count = sum(1 for w in es_words if w in t)
        en_count = sum(1 for w in en_words if w in t)
        # Si ninguno claramente domina, no decimos nada
        if max(es_count, en_count) < 2:
            self.lbl_idioma_aviso.configure(text="")
            return
        es_dominante = es_count > en_count * 1.5
        en_dominante = en_count > es_count * 1.5
        # Estado actual del auto-trad
        auto_trad_on = bool(getattr(self, "switch_traduccion_var", None) and self.switch_traduccion_var.get())
        if en_dominante and auto_trad_on:
            self.lbl_idioma_aviso.configure(text="🇬🇧 inglés detectado · click para desactivar Auto-trad")
        elif es_dominante and not auto_trad_on:
            self.lbl_idioma_aviso.configure(text="🇪🇸 español detectado · click para activar Auto-trad")
        else:
            self.lbl_idioma_aviso.configure(text="")

    def _toggle_auto_trad_desde_aviso(self):
        """Cambia el estado de auto-trad cuando el usuario clica en el aviso de idioma."""
        try:
            if hasattr(self, "switch_traduccion_var"):
                self.switch_traduccion_var.set(not self.switch_traduccion_var.get())
                # Refrescar visual del switch
                if hasattr(self, "_sw_trad_callback"):
                    try: self._sw_trad_callback()
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
                self._actualizar_barra_chars()  # refresca aviso
                estado = "activado" if self.switch_traduccion_var.get() else "desactivado"
                self.set_estado(f"🌐 Auto-trad {estado}", "#3498db")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    def _build_acciones(self):
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(pady=2, padx=16, fill="x")

        # Fila 1: generación
        row1 = ctk.CTkFrame(outer, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 3))

        btn_s = {"height": 32, "corner_radius": 6, "font": ctk.CTkFont(size=11)}

        # ═══ FILA 1: Generación principal (verde-azul - acciones positivas) ═══
        # Orden: Ideas → Sorprende → Generar (la principal) → Regenerar → Variaciones → Analizar → Img→Prompt → Análisis Inv
        botones_r1 = [
            # GRUPO: Inspiración (verde claro)
            ("💡 Ideas",          100, "#2a6a4a", self.cmd_ideas,             "3 ideas creativas · Ctrl+I"),
            ("🎲",                40,  "#3a6a4a", self._cmd_sorprendeme,      "Sorpréndeme con una idea aleatoria"),
            # GRUPO: Generar (verde fuerte = acción principal)
            ("✨ Generar",         110, "#1a8a3c", self.cmd_prompt,            "Genera prompt · Ctrl+Enter"),
            # ── MEJORA 3: Regenerar + flechas para navegar entre regeneraciones ──
            ("🔄",                40,  "#1a8a3c", self._cmd_regenerar,        "Regenerar con la misma idea (mantiene historial)"),
            ("←",                30,  "#1a5a3c", self._cmd_regenerar_atras,  "← Versión anterior de la regeneración"),
            ("→",                30,  "#1a5a3c", self._cmd_regenerar_adelante,"→ Versión siguiente de la regeneración"),
            ("📊",               36,  "#1a5a3c", self._cmd_diff_versiones,   "Diff visual entre versiones (verde=añadido, rojo=quitado)"),
            ("🔀 Variaciones",    115, "#2563eb", self.cmd_variaciones,       "3 versiones · Ctrl+Shift+Enter"),
            # GRUPO: Análisis de imagen (azul oscuro)
            ("👁 Analizar",       100, "#1e3a8a", self.cmd_vision,            "Describe imagen · Ctrl+Shift+A"),
            ("🎯 Img→Prompt",     110, "#1e3a8a", self.cmd_imagen_a_prompt,   "Prompt desde imagen"),
            ("🔍 Análisis Inv",   115, "#1e3a5f", self._cmd_analisis_inverso, "Compara imagen con prompt actual"),
            # GRUPO: ADN Visual (morado - único)
            ("🧬 ADN Visual",     100, "#7c3aed", self._cmd_adn_visual,      "Análisis JSON estructurado"),
        ]

        # ═══ FILA 2: Edición y herramientas (naranja-violeta) ═══
        # Orden: Refinar/Copiloto (edición) → Batch/Preview (output) → →Vídeo/Compar (transformación) → Iterar/Pulse/Sugerir (variación) → Mood/Story/Board/Walk (creativos)
        botones_r2 = [
            # GRUPO: Edición del prompt (violeta)
            ("🔁 Refinar",         90, "#7c3aed", self.cmd_refinar,            "Mejora el prompt (click der: opciones específicas)"),
            ("💬 Copiloto",        95, "#7c3aed", self.cmd_copiloto,           "Chat para editar"),
            # GRUPO: Outputs masivos (azul-gris)
            ("📦 Batch",           80, "#475569", self.cmd_batch,              "Generación masiva"),
            ("👁️ Preview",        90, "#475569", self.cmd_previsualizar,      "Boceto rápido"),
            # GRUPO: Conversiones (cyan)
            ("🎬 →Vídeo",          85, "#0891b2", self._cmd_convertir_a_video, "Convierte prompt de imagen a vídeo"),
            ("🆚 Compar",          80, "#0891b2", self._cmd_comparar_modelos,  "Compara prompt en 3 modelos"),
            # GRUPO: Variaciones rápidas (naranja)
            ("🔂 Iterar",          80, "#d97706", self._cmd_iteracion,         "5 variantes cambiando 1 elemento"),
            ("🚀 Quick",           80, "#d97706", self.cmd_prompt_quick,      "Quick Generate: prompt rápido y barato · Alt+Enter"),
            ("⚡ Pulse",           75, "#d97706", self._cmd_pulse,             "3 versiones: conservador/equilibrado/creativo"),
            ("🤖 Sugerir",         85, "#d97706", self._cmd_sugerir_modelo,    "Sugiere el mejor modelo según tu idea"),
            # GRUPO: Multi-prompt creativo (rosa-fucsia)
            ("🎭 Mood",            70, "#be185d", self._cmd_moodboard,         "Moodboard: 6 prompts mismo mood, distintos sujetos"),
            ("🎬 Story",           70, "#be185d", self._cmd_story_sequence,    "Story Sequence (solo IMAGEN): 3 shots Wide/Medium/Close"),
            ("📽 Board",           70, "#be185d", self._cmd_storyboard_video,  "Storyboard (solo VÍDEO): 4 frames apertura/mid/climax/cierre"),
            ("🌀 Walk",            70, "#be185d", self._cmd_random_walk,       "Random walk: 5 derivaciones evolutivas"),
        ]

        self.action_btns = []
        for text, w, fg, cmd, tooltip in botones_r1:
            kw = {"fg_color": fg, "hover_color": self._darker(fg)} if fg else {}
            btn = ctk.CTkButton(row1, text=text, width=w, command=cmd, **btn_s, **kw)
            btn.pack(side="left", padx=2)
            CTkToolTip(btn, delay=0.5, message=tooltip)
            self.action_btns.append(btn)

        # ═══ BADGE DE COSTE (junto a Generar) ═══
        self.lbl_coste = ctk.CTkLabel(row1, text="", font=ctk.CTkFont(size=10, weight="bold"),
                                       text_color="#22c55e", fg_color="transparent")
        self.lbl_coste.pack(side="left", padx=(4, 0))

        # Índices reales de botones_r1:
        # [0]💡 Ideas, [1]🎲, [2]✨ Generar, [3]🔄 Regenerar, [4]←, [5]→, [6]📊 Diff,
        # [7]🔀 Variaciones, [8]👁 Analizar, [9]🎯 Img→Prompt, [10]🔍 Análisis Inv, [11]🧬 ADN Visual
        self.btn_vision = self.action_btns[8]
        self.btn_img_prompt = self.action_btns[9]

        # Registrar callback para actualizar coste cuando cambie la idea
        self.txt_idea.bind("<<Modified>>", self._actualizar_coste_estimado)

        row2 = ctk.CTkFrame(outer, fg_color="transparent")
        row2.pack(fill="x")
        for text, w, fg, cmd, tooltip in botones_r2:
            kw = {"fg_color": fg, "hover_color": self._darker(fg)} if fg else {}
            btn = ctk.CTkButton(row2, text=text, width=w, command=cmd, **btn_s, **kw)
            btn.pack(side="left", padx=2)
            CTkToolTip(btn, delay=0.5, message=tooltip)
            self.action_btns.append(btn)
            # Click derecho en Refinar → menú específico
            if text == "🔁 Refinar":
                btn.bind("<Button-3>", self._menu_refinar_especifico)

        btn_reset = ctk.CTkButton(row2, text="🗑 Reset", width=80, height=32, corner_radius=6,
                                   fg_color="#7f1d1d", hover_color="#5a1414",
                                   font=ctk.CTkFont(size=11), command=self.cmd_reset)
        btn_reset.pack(side="right", padx=2)
        CTkToolTip(btn_reset, delay=0.5, message="Limpia todo y borra la memoria.")

        btn_repeat = ctk.CTkButton(row2, text="🔁 Última", width=85, height=32, corner_radius=6,
                                       fg_color="#1e3a5f", hover_color="#162d49",
                                       font=ctk.CTkFont(size=10), command=self._repetir_ultima_config)
        btn_repeat.pack(side="right", padx=2)
        CTkToolTip(btn_repeat, delay=0.5, message="Repetir configuración del último prompt generado")

        # ── MEJORA 8: Guardar/Cargar setup (configuración sin idea ni prompt) ──
        btn_load_setup = ctk.CTkButton(row2, text="📋 Cargar setup", width=110, height=32, corner_radius=6,
                                        fg_color="#1e5f3a", hover_color="#16492d",
                                        font=ctk.CTkFont(size=10), command=self._cmd_cargar_setup)
        btn_load_setup.pack(side="right", padx=2)
        CTkToolTip(btn_load_setup, delay=0.5, message="Cargar una configuración guardada (modelo, ratio, estilos…)")

        btn_save_setup = ctk.CTkButton(row2, text="💾 Setup", width=85, height=32, corner_radius=6,
                                        fg_color="#1e5f3a", hover_color="#16492d",
                                        font=ctk.CTkFont(size=10), command=self._cmd_guardar_setup)
        btn_save_setup.pack(side="right", padx=2)
        CTkToolTip(btn_save_setup, delay=0.5,
                   message="Guarda la configuración actual (modelo, plataforma, ratio, estilos, negatives, personaje, LoRA, destino) sin idea ni prompt")

        self.frame_ideas = ctk.CTkFrame(self, fg_color="transparent")

    def _build_estado(self):
        is_light = _get_real_is_light()
        from config import get_theme_colors
        c = get_theme_colors(is_light)
        self.frame_estado = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_estado.pack(pady=(1, 0), fill="x", padx=16)

        self.lbl_estado = ctk.CTkLabel(
            self.frame_estado,
            text=f"Listo · Ctrl+Enter: Prompt · Ctrl+1/2: Copiar",
            font=ctk.CTkFont(size=10), fg_color="transparent", text_color=c["muted_text"])
        self.lbl_estado.pack(side="left", fill="x", expand=True)

        self.progress = ctk.CTkProgressBar(self.frame_estado, width=160, height=10,
                                                   mode="indeterminate", progress_color="#3498db")

    def _build_salida(self):
        is_light = _get_real_is_light()
        from config import get_theme_colors
        c = get_theme_colors(is_light)
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(pady=2, padx=16, fill="both", expand=True)
        hdr = ctk.CTkFrame(frame, fg_color="transparent")
        hdr.pack(fill="x", padx=2, pady=(0, 2))
        ctk.CTkLabel(hdr, text="Resultado", font=ctk.CTkFont(size=10), fg_color="transparent", text_color=c["muted_text"]).pack(side="left")
        ctk.CTkLabel(hdr, text="editable", font=ctk.CTkFont(size=9), fg_color="transparent", text_color=c["panel_label"]).pack(side="left", padx=4)

        # ── Validador Flux/SD3.5: aviso ARRIBA del textbox con fondo destacado ──
        # (Va antes del textbox para no quedar tapado por la barra de botones inferior)
        self.lbl_flux_warning = ctk.CTkLabel(frame, text="",
                                              font=ctk.CTkFont(size=11, weight="bold"),
                                              text_color="#1a1a1a",
                                              fg_color="#f39c12",
                                              corner_radius=6,
                                              anchor="w", justify="left",
                                              height=24)
        # No se hace pack inicialmente — se mostrará/ocultará dinámicamente

        self.txt_salida = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Consolas", size=12),
                                          wrap="word", height=140)
        self.txt_salida.pack(fill="both", expand=True)
        self.txt_salida.bind("<KeyRelease>", self._on_salida_editada)
        self.txt_salida.bind("<Double-Button-1>", self._on_doble_click_salida)
        self.txt_salida.bind("<Button-3>", self._mostrar_menu_contextual)

        # ── MEJORA 9 (inline): franja de compatibilidad rápida con plataformas top ──
        self.lbl_compat_inline = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(family="Consolas", size=9),
                                               fg_color="transparent",
                                               text_color=c["muted_text"], anchor="w", justify="left",
                                               cursor="hand2")
        self.lbl_compat_inline.pack(fill="x", pady=(2, 0))
        self.lbl_compat_inline.bind("<Button-1>", lambda e: self._cmd_modal_compatibilidad())

    def _build_footer(self):
        is_light = _get_real_is_light()
        from config import get_theme_colors
        c = get_theme_colors(is_light)
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(side="bottom", fill="x", padx=16, pady=(1, 2))

        self.lbl_tokens = ctk.CTkLabel(outer, text="", font=ctk.CTkFont(family="Consolas", size=10),
                                        fg_color="transparent",
                                        text_color=c["muted_text"])
        self.lbl_tokens.pack(fill="x", pady=(0, 2))

        frame = ctk.CTkFrame(outer, fg_color="transparent")
        frame.pack(fill="x")

        pill = {"height": 28, "corner_radius": 6, "font": ctk.CTkFont(size=10)}

        # ═══ FILA INFERIOR: agrupada por función ═══
        # GRUPO 1: Copiar (verde-rojo-azul) — acciones primarias
        # GRUPO 2: Tools rápidas (azul) — análisis/utilidades
        # GRUPO 3: Negative (rojo) — generación negativos
        # GRUPO 4: Guardar (amarillo dorado) — colecciones
        # GRUPO 5: Export (verde oscuro)
        botones_inf = [
            # GRUPO COPIAR
            ("🟢 POS",     60, "#15803d",  lambda: self._copiar("positivo"),     "Copiar POSITIVE · Ctrl+1"),
            ("🔴 NEG",     60, "#991b1b",  lambda: self._copiar("negativo"),     "Copiar NEGATIVE · Ctrl+2"),
            ("📋 Todo",    55, "#475569",  lambda: self._copiar("todo"),          "Copiar todo el prompt"),
            # GRUPO HERRAMIENTAS
            ("🔧 Comfy",   60, "#1e3a8a",  self._copiar_comfyui_json,             "Exportar/Importar ComfyUI JSON"),
            ("🇪🇸 Trad",    55, "#1e3a8a",  self._traducir_salida,                  "Traducir al español"),
            ("📊",         30, "#1e3a8a",  self._cmd_scoring,                      "Scoring del prompt"),
            ("✨",         30, "#1e3a8a",  self._abrir_atajos_tags,                "Atajos de tags rápidos"),
            # GRUPO NEGATIVE (rojo)
            ("🔴+",        35, "#991b1b",  self._cmd_solo_negative,                "Regenerar SOLO el NEGATIVE"),
            ("🛡",         30, "#991b1b",  self._cmd_negative_optimo,              "Generar NEGATIVE óptimo según modelo"),
            # GRUPO GUARDAR (dorado/amarillo)
            ("⭐",         30, "#a16207",  self._guardar_favorito,                 "Guardar en Favoritos"),
            ("🌟",         30, "#b45309",  self._guardar_estrella,                 "Guardar como Estrella"),
            ("💎",         30, "#854d0e",  self._guardar_seed_favorito,            "Guardar config como Seed favorito"),
            # GRUPO EXPORT (verde oscuro)
            ("💾",         30, "#15803d",  self._exportar,                         "Exportar como .txt"),
        ]

        for text, w, fg, cmd, tip in botones_inf:
            btn = ctk.CTkButton(frame, text=text, width=w, fg_color=fg, hover_color=self._darker(fg), command=cmd, **pill)
            btn.pack(side="left", padx=2)
            is_lt = ctk.get_appearance_mode().lower() == "light"
            CTkToolTip(btn, delay=0.3, message=tip, fg_color="#f0f0f0" if is_lt else "#1a1a2e", text_color="#111827" if is_lt else "#e5e7eb", font=("Segoe UI", 11))

    def _mostrar_menu_contextual(self, event):
        """Menú contextual con click derecho en el resultado."""
        import tkinter as tk
        menu = tk.Menu(self, tearoff=0, bg="#1a1a2a", fg="white",
                       activebackground="#2a4a6a", activeforeground="white",
                       font=("Segoe UI", 10), borderwidth=1)

        menu.add_command(label="🟢 Copiar POSITIVE", command=lambda: self._copiar("positivo"))
        menu.add_command(label="🔴 Copiar NEGATIVE", command=lambda: self._copiar("negativo"))
        menu.add_command(label="📋 Copiar todo", command=lambda: self._copiar("todo"))
        menu.add_separator()

        # Submenú: pegar último prompt del historial
        if self.store.historial:
            submenu_hist = tk.Menu(menu, tearoff=0, bg="#1a1a2a", fg="white",
                                    activebackground="#2a4a6a", font=("Segoe UI", 10))
            for i, item in enumerate(self.store.historial[:5]):
                if isinstance(item, dict):
                    txt = item.get("texto", "")
                else:
                    txt = item
                if txt:
                    label = f"#{i+1} {txt[:50]}{'...' if len(txt) > 50 else ''}"
                    submenu_hist.add_command(label=label, command=lambda t=txt: self.actualizar_salida(t))
            menu.add_cascade(label="📋 Pegar de historial reciente", menu=submenu_hist)

        # Submenú: pegar de favoritos
        if self.store.favoritos:
            submenu_fav = tk.Menu(menu, tearoff=0, bg="#1a1a2a", fg="white",
                                   activebackground="#2a4a6a", font=("Segoe UI", 10))
            for i, item in enumerate(self.store.favoritos[:5]):
                if isinstance(item, dict):
                    txt = item.get("texto", "")
                    nombre = item.get("nombre", "")
                else:
                    txt = item
                    nombre = ""
                if txt:
                    label = f"⭐ {nombre or txt[:50]}"
                    submenu_fav.add_command(label=label[:60], command=lambda t=txt: self.actualizar_salida(t))
            menu.add_cascade(label="⭐ Pegar de favoritos", menu=submenu_fav)

        menu.add_separator()
        menu.add_command(label="📊 Analizar calidad", command=self._cmd_scoring)
        menu.add_command(label="✨ Atajos de tags", command=self._abrir_atajos_tags)
        menu.add_command(label="🇪🇸 Traducir al español", command=self._traducir_salida)
        menu.add_command(label="🧬 Variar con ADN visual", command=self._cmd_variar_con_anclaje)
        menu.add_command(label="🔍 Comparar consistencia", command=self._cmd_comparar_consistencia)
        menu.add_separator()
        menu.add_command(label="🗑 Limpiar resultado", command=lambda: self.txt_salida.delete("1.0", "end"))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _mostrar_menu_contextual_idea(self, event):
        """Menú contextual click derecho en el textbox de idea (Cortar/Copiar/Pegar/Seleccionar todo)."""
        import tkinter as tk
        menu = tk.Menu(self, tearoff=0, bg="#1a1a2a", fg="white",
                       activebackground="#2a4a6a", activeforeground="white",
                       font=("Segoe UI", 10), borderwidth=1)

        # Comprobar si hay selección
        try:
            tiene_seleccion = bool(self.txt_idea.tag_ranges("sel"))
        except Exception:
            tiene_seleccion = False

        def _cortar():
            try:
                if tiene_seleccion:
                    sel = self.txt_idea.get("sel.first", "sel.last")
                    pyperclip.copy(sel)
                    self.txt_idea.delete("sel.first", "sel.last")
                    self.set_estado("✂️ Cortado al portapapeles", "#3498db")
            except Exception as e:
                logger.debug(f"[silent] {e}")

        def _copiar_sel():
            try:
                if tiene_seleccion:
                    sel = self.txt_idea.get("sel.first", "sel.last")
                else:
                    # Si no hay selección, copiar todo
                    sel = self.txt_idea.get("1.0", "end").strip()
                if sel:
                    pyperclip.copy(sel)
                    self.set_estado("📋 Copiado al portapapeles", "#3498db")
            except Exception as e:
                logger.debug(f"[silent] {e}")

        def _pegar():
            try:
                texto = pyperclip.paste()
                if texto:
                    if tiene_seleccion:
                        self.txt_idea.delete("sel.first", "sel.last")
                    self.txt_idea.insert("insert", texto)
                    self._actualizar_barra_chars()
            except Exception as e:
                logger.debug(f"[silent] {e}")

        def _seleccionar_todo():
            try:
                self.txt_idea.tag_add("sel", "1.0", "end")
                self.txt_idea.mark_set("insert", "1.0")
                self.txt_idea.see("insert")
            except Exception as e:
                logger.debug(f"[silent] {e}")

        def _limpiar():
            self.txt_idea.delete("1.0", "end")
            self._actualizar_barra_chars()

        menu.add_command(label="✂️ Cortar" + ("" if tiene_seleccion else "  (sin selección)"),
                         command=_cortar, state="normal" if tiene_seleccion else "disabled")
        menu.add_command(label="📋 Copiar" + ("" if tiene_seleccion else "  (todo)"),
                         command=_copiar_sel)
        menu.add_command(label="📥 Pegar", command=_pegar)
        menu.add_separator()
        menu.add_command(label="🔘 Seleccionar todo", command=_seleccionar_todo)
        menu.add_separator()
        menu.add_command(label="🗑 Limpiar idea", command=_limpiar)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _construir_checkboxes(self, lista):
        # Optimización v1.1: si los checkboxes para esta misma lista ya existen,
        # no se destruyen ni se recrean — solo se restablecen a desmarcados.
        # Esto evita el lag al cambiar entre modos Imagen/Vídeo/Audio cuando hay
        # cientos de estilos.
        if hasattr(self, "_estilos_lista_actual") and self._estilos_lista_actual == lista \
           and hasattr(self, "estilo_checks") and self.estilo_checks:
            # Reset rápido: solo desmarcar todo, sin destruir nada
            for var in self.estilo_checks.values():
                try:
                    var.set(False)
                except Exception as _e:
                    logger.debug(f"[silent] {_e}")
            if hasattr(self, 'lbl_estilos_sel'):
                self.lbl_estilos_sel.configure(text="")
            self._auto_sugerir_negativos()
            self._actualizar_contador_estilos()
            return

        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)

        for w in self.frame_checks.winfo_children():
            w.destroy()
        self.estilo_checks = {}
        if hasattr(self, 'lbl_estilos_sel'):
            self.lbl_estilos_sel.configure(text="")
        cols = 3

        for i, nombre in enumerate(lista):
            # Ningún estilo marcado por defecto — el usuario debe elegir
            var = ctk.BooleanVar(value=False)
            self.estilo_checks[nombre] = var
            cb = ctk.CTkCheckBox(self.frame_checks, text=nombre, variable=var,
                                 command=self._on_estilo_cambio,
                                 font=ctk.CTkFont(size=10),
                                 checkbox_width=16, checkbox_height=16,
                                 text_color=c["chk_text"],
                                 hover_color=c["accent_text"],
                                 border_color=c["chk_border"],
                                 fg_color=c["accent_text"])
            cb.grid(row=i // cols, column=i % cols, sticky="w", padx=5, pady=1)

        for c_i in range(cols):
            self.frame_checks.columnconfigure(c_i, weight=1)

        # Recordar qué lista construimos para evitar recrear al volver al mismo modo
        self._estilos_lista_actual = lista

        self._auto_sugerir_negativos()
        self._actualizar_contador_estilos()

    def _filtrar_estilos(self, event=None):
        termino = self.entry_busqueda.get().lower()
        for child in self.frame_checks.winfo_children():
            if isinstance(child, ctk.CTkCheckBox):
                if termino in child.cget("text").lower():
                    child.grid()
                else:
                    child.grid_remove()

    def _validar_estilos(self, maximo):
        marcados = [n for n, v in self.estilo_checks.items() if v.get()]
        if len(marcados) > maximo:
            self.estilo_checks[marcados[0]].set(False)

    def _on_estilo_cambio(self):
        self._validar_estilos(6)
        self._auto_sugerir_negativos()
        self._actualizar_contador_estilos()
        sel = self.estilos_seleccionados()
        if sel:
            self.set_estado(f"🎨 Estilos: {' + '.join(sel)}", "#2ecc71")
        else:
            self.set_estado("🎨 Estilos: General (ninguno seleccionado)")

    def _on_personaje_selected(self, nombre: str):
        if not nombre or nombre == "— Sin personaje —":
            return
        desc = self.store.descripcion_personaje(nombre) if hasattr(self, 'store') else ""
        if desc:
            self.txt_idea.delete("1.0", "end")
            self.txt_idea.insert("1.0", desc)
            if hasattr(self, "_sesion_eventos"):
                self._sesion_log(f"🧑 Personaje → {nombre}")

    def _actualizar_coste_estimado(self, event=None):
        """Calcula y muestra el coste estimado de la generación."""
        try:
            texto = self.txt_idea.get("1.0", "end").strip()
            if not texto or len(texto) < 5:
                self.lbl_coste.configure(text="")
                return

            tokens = max(1, len(texto) // 4)
            proveedor = self.llm_var.get().lower() if hasattr(self, 'llm_var') else ""

            precios = {
                "deepseek": 0.27,
                "openai": 1.5,
                "gpt": 1.5,
                "claude": 3.0,
                "gemini": 0.075,
                "ollama": 0.0,
                "mistral": 0.8,
                "groq": 0.2,
                "fireworks": 0.5,
            }

            precio_base = 0.27
            for clave, valor in precios.items():
                if clave in proveedor:
                    precio_base = valor
                    break

            coste = (tokens / 1000) * precio_base

            if precio_base == 0:
                self.lbl_coste.configure(text=f"🆓 gratis")
            elif coste < 0.001:
                self.lbl_coste.configure(text=f"$0.00{coste:.0f}")
            elif coste < 0.01:
                self.lbl_coste.configure(text=f"${coste:.3f}")
            else:
                self.lbl_coste.configure(text=f"${coste:.2f}")

        except Exception:
            self.lbl_coste.configure(text="")

    def _auto_sugerir_negativos(self):
        if not self._debe_mostrar_negatives():
            return

        presets_sugeridos = set()
        for estilo, var in self.estilo_checks.items():
            if var.get() and estilo in ESTILO_NEGATIVO_AUTO:
                for preset in ESTILO_NEGATIVO_AUTO[estilo]:
                    presets_sugeridos.add(preset)

        cambio = False
        for pname, pvar in self.preset_vars.items():
            deberia_estar = pname in presets_sugeridos
            if deberia_estar != pvar.get():
                pvar.set(deberia_estar)
                if pname in self.preset_btns:
                    fg = PRESET_COLORES.get(pname, ("#333", "#555"))[0]
                    self.preset_btns[pname].configure(fg_color="#2ecc71" if deberia_estar else fg, text=f"✓ {pname}" if deberia_estar else pname)
                cambio = True

        if cambio:
            self._rebuild_negative_text()

    def actualizar_combo_personajes(self):
        nombres = self.store.nombres_personajes()
        self.combo_personaje.configure(values=nombres)
        if self.combo_personaje.get() not in nombres:
            self.combo_personaje.set("— Sin personaje —")

    def actualizar_combo_loras(self):
        nombres = self.store.nombres_loras()
        self.combo_lora.configure(values=nombres)
        if self.combo_lora.get() not in nombres:
            self.combo_lora.set("— Sin LoRA —")
        # Refrescar trigger visible y aviso de compatibilidad
        try: self._actualizar_lora_trigger_visible()
        except Exception as e:
            logger.debug(f"[silent] {e}")

    def actualizar_combo_plantillas(self):
        nombres = self.store.nombres_plantillas()
        self.combo_plantilla.configure(values=nombres)
        if self.combo_plantilla.get() not in nombres:
            self.combo_plantilla.set("— Sin plantilla —")

    def estilos_seleccionados(self):
        return [n for n, v in self.estilo_checks.items() if v.get()]

    def estilos_texto(self):
        sel = self.estilos_seleccionados()
        return " + ".join(sel) if sel else "General"

    def ratio_actual(self):
        return self.ratio_var.get() if self.ratio_var.get() != "Libre" else ""

    def personaje_activo(self):
        nombre = self.combo_personaje.get()
        if nombre and nombre != "— Sin personaje —":
            return self.store.descripcion_personaje(nombre)
        return ""

    def lora_activo(self):
        nombre = self.combo_lora.get()
        if nombre and nombre != "— Sin LoRA —":
            return self.store.trigger_lora(nombre)
        return ""

    def _actualizar_lora_trigger_visible(self):
        """Muestra el trigger del LoRA seleccionado al lado del combo (Mejora LoRAs)."""
        if not hasattr(self, "lbl_lora_trigger"): return
        nombre = self.combo_lora.get() if hasattr(self, "combo_lora") else ""
        if not nombre or nombre == "— Sin LoRA —":
            self.lbl_lora_trigger.configure(text="")
            return
        trigger = self.store.trigger_lora(nombre)
        # Encontrar familia
        familia = ""
        for l in self.store.loras:
            if l.get("nombre") == nombre:
                familia = l.get("familia", "")
                break
        # Verificar compatibilidad con modelo actual
        compatible = self._es_lora_compatible(familia)
        if compatible is False:
            warning = "  ⚠️ familia distinta"
            color = "#f39c12"
        elif compatible is True:
            warning = "  ✓"
            color = "#2ecc71"
        else:
            # None: sin info, color neutral
            warning = ""
            color = "#9b59b6"
        # Mostrar también hint si el LoRA no tiene familia configurada
        if not familia:
            warning = "  (sin familia · edítalo en 🔗)"
            color = "#4b5563" if ctk.get_appearance_mode().lower() == "light" else "#888888"
        texto = f'→ "{trigger}"'
        if familia: texto += f"  [{familia}]"
        texto += warning
        self.lbl_lora_trigger.configure(text=texto, text_color=color)

    def _es_lora_compatible(self, familia_lora):
        """Devuelve True/False si el LoRA es compatible con el modelo activo. None si no se puede determinar."""
        if not familia_lora or familia_lora == "—":
            return None  # sin info, no juzgamos
        modo = self.modo_var.get() if hasattr(self, "modo_var") else "imagen"
        if modo != "imagen":
            return None  # LoRAs son cosa de imagen mayormente
        modelo = self.combo_modelo_imagen.get() if hasattr(self, "combo_modelo_imagen") else ""
        modelo_l = modelo.lower()
        f = familia_lora.lower()
        # Detectar familia del modelo (más casos)
        modelo_familia = None
        if "flux" in modelo_l: modelo_familia = "flux"
        elif "sd3.5" in modelo_l or "sd 3.5" in modelo_l: modelo_familia = "sd3.5"
        elif "pony" in modelo_l: modelo_familia = "pony"
        elif "illustrious" in modelo_l or "noob" in modelo_l or "wai " in modelo_l: modelo_familia = "illustrious"
        elif "sdxl" in modelo_l or "juggernaut" in modelo_l or "realvis" in modelo_l: modelo_familia = "sdxl"
        elif "1.5" in modelo_l or "sd15" in modelo_l or "epic" in modelo_l: modelo_familia = "sd15"

        # Compatibilidades cruzadas: Pony e Illustrious son SDXL-based
        compatible_pares = {
            ("pony", "sdxl"), ("sdxl", "pony"),
            ("illustrious", "sdxl"), ("sdxl", "illustrious"),
            ("pony", "illustrious"), ("illustrious", "pony"),
        }
        if modelo_familia is None:
            return False  # familia del modelo desconocida → no garantizamos compatibilidad
        if (f, modelo_familia) in compatible_pares:
            return True
        return f == modelo_familia

    def _recomendar_loras_para_modelo(self, modelo_name):
        """Cuando cambia el modelo, busca LoRAs guardados compatibles y avisa al usuario."""
        if not hasattr(self, "store") or not self.store.loras:
            return
        # Si ya hay un LoRA seleccionado, no molestar
        try:
            actual = self.combo_lora.get()
            if actual and actual != "— Sin LoRA —":
                return
        except Exception as e:
            logger.debug(f"[silent] {e}")

        # Filtrar LoRAs con familia compatible con el nuevo modelo
        compatibles = []
        for lora in self.store.loras:
            familia = lora.get("familia", "")
            if not familia or familia == "—": continue
            if self._es_lora_compatible(familia) is True:
                compatibles.append(lora)

        if not compatibles:
            return

        # Mostrar mensaje amigable en el estado (en color violeta para que destaque)
        nombres = [l["nombre"] for l in compatibles[:3]]
        if len(compatibles) == 1:
            msg = f"💡 LoRA compatible disponible: '{nombres[0]}' — selecciónalo en el combo 🔗 LoRA"
        elif len(compatibles) <= 3:
            msg = f"💡 {len(compatibles)} LoRAs compatibles disponibles: {', '.join(nombres)}"
        else:
            msg = f"💡 {len(compatibles)} LoRAs compatibles ({', '.join(nombres)} +{len(compatibles) - 3} más)"
        self.set_estado(msg, "#a78bfa")

    def modelo_video_valido(self):
        v = self.combo_modelo_video.get()
        plat = self.plataforma_var.get()
        if not v or es_separador(v):
            return MOTOR_DEFAULT.get(plat, plat)
        return v

    def modelo_imagen_valido(self):
        v = self.combo_modelo_imagen.get()
        return v if not es_separador(v) else ""

    def detectar_idioma(self, texto):
        return detectar_idioma_es(texto)

    def _validar_negative_length(self, event=None):
        """Limita el negative extra manual a 1500 chars y muestra advertencia."""
        NEGATIVE_MAX = 1500
        texto = self.txt_negative.get("1.0", "end").strip()
        if len(texto) > NEGATIVE_MAX:
            recortado = texto[:NEGATIVE_MAX].rsplit(",", 1)[0].rstrip(", ")
            self.txt_negative.delete("1.0", "end")
            self.txt_negative.insert("1.0", recortado)
            self.txt_negative.mark_set("insert", "end")
        if hasattr(self, 'lbl_negative_warning'):
            if len(texto) > NEGATIVE_MAX * 0.8:
                self.lbl_negative_warning.configure(
                    text=f"⚠️ Negative: {len(texto)}/{NEGATIVE_MAX} chars" + (" (recortado)" if len(texto) >= NEGATIVE_MAX else ""),
                    text_color="#e74c3c" if len(texto) >= NEGATIVE_MAX else "#f39c12")
                self.lbl_negative_warning.pack(fill="x", padx=2, pady=(2, 0))
            else:
                self.lbl_negative_warning.configure(text="")
                if self.lbl_negative_warning.winfo_ismapped():
                    self.lbl_negative_warning.pack_forget()

    def _rebuild_negative_text(self):
        partes = [NEGATIVE_PRESETS[n] for n, v in self.preset_vars.items() if v.get()]
        manual = self._get_negative_manual()
        if manual: partes.append(manual)
        texto = ", ".join(partes)
        NEGATIVE_MAX = 1500
        if len(texto) > NEGATIVE_MAX:
            texto = texto[:NEGATIVE_MAX].rsplit(",", 1)[0].rstrip(", ")
            if hasattr(self, 'lbl_negative_warning'):
                self.lbl_negative_warning.configure(
                    text=f"⚠️ Negative recortado a {NEGATIVE_MAX} chars (límite SeaArt)",
                    text_color="#e74c3c")
                self.lbl_negative_warning.pack(fill="x", padx=2, pady=(2, 0))
        else:
            if hasattr(self, 'lbl_negative_warning'):
                self.lbl_negative_warning.configure(text="")
                if self.lbl_negative_warning.winfo_ismapped():
                    self.lbl_negative_warning.pack_forget()
        self.txt_negative.delete("1.0", "end")
        if texto: self.txt_negative.insert("1.0", texto)
        self.reiniciar_memoria()

    def _get_negative_manual(self):
        texto = self.txt_negative.get("1.0", "end").strip()
        if not texto: return ""
        for pname in self.preset_vars:
            texto = texto.replace(NEGATIVE_PRESETS[pname], "")
        return re.sub(r',\s*,', ',', texto).strip(", \n")

    def _limpiar_negatives(self):
        self.txt_negative.delete("1.0", "end")
        for pname, pvar in self.preset_vars.items():
            pvar.set(False)
            if pname in self.preset_btns:
                fg = PRESET_COLORES.get(pname, ("#333", "#555"))[0]
                self.preset_btns[pname].configure(fg_color=fg, text=pname)
        self.reiniciar_memoria()

    def _resetear_presets_visual(self):
        for pname, pvar in self.preset_vars.items():
            pvar.set(False)
            if pname in self.preset_btns:
                fg = PRESET_COLORES.get(pname, ("#333", "#555"))[0]
                self.preset_btns[pname].configure(fg_color=fg, text=pname)
