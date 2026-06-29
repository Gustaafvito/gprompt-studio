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
import json
import logging
import os

import customtkinter as ctk

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
from typing import TYPE_CHECKING

from config import (
    DESTINOS,
    EMOCIONES_AUDIO,
    ESTILOS_IMAGEN,
    ESTILOS_VISUAL_VIDEO,
    IDIOMAS_AUDIO,
    MODELOS_AUDIO_FLAT,
    MODELOS_IMAGEN_FLAT,
    MODELOS_VIDEO_FLAT,
    NEGATIVE_PAQUETES,
    NEGATIVE_PRESETS,
    PLATAFORMAS_IMAGEN_LISTA,
    PRESET_COLORES,
    RATIOS_IMAGEN,
    RATIOS_VIDEO,
    TAG_PICKER_CATEGORIES,
    VOCES_AUDIO,
    get_theme_colors,
)
from modules.avatar_ui import abrir_avatar_window
from modules.i18n import get_idioma, tr
from modules.style_guide import abrir_guia_estilos
from modules.windows import abrir_lista, abrir_loras, abrir_personajes

if TYPE_CHECKING:
    pass

class UIBuildersService:
    """26 métodos de construcción UI: header, paneles de modo/video/
    audio/imagen, tabs centrales, ajustes, estilos, negative, entrada,
    acciones, estado, salida, etc.

    A1 fase 2 (sesión 14): servicio aislado con app por composición.
    """

    def __init__(self, app):
        self.app = app

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

        frame = ctk.CTkFrame(self.app, fg_color=hdr_bg, corner_radius=0)
        frame.pack(fill="x")
        self.app._header_frame = frame
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(pady=6, padx=16, fill="x")

        # Cerebro (selector multi-LLM) — lado izquierdo
        frame_llm = ctk.CTkFrame(inner, fg_color="transparent")
        frame_llm.pack(side="left", padx=20)
        self.app._lbl_cerebro = ctk.CTkLabel(frame_llm, text=tr("Cerebro:"), font=ctk.CTkFont(size=11), fg_color="transparent", text_color=hdr_label)
        self.app._lbl_cerebro.pack(side="left", padx=(0, 4))
        # Importar dinámicamente la lista de providers
        try:
            from api_clients import LLM_PROVIDERS
            self.app._llm_providers_dict = LLM_PROVIDERS

            # Construir labels con indicador visual de estado:
            # ✅ = key configurada (provider disponible)
            # 🔒 = sin key (al pulsarlo se abre el wizard automáticamente)
            def _label_con_estado(pid: str, label: str) -> str:
                try:
                    prov = self.app.clients.providers.get(pid) if hasattr(self.app.clients, "providers") else None
                    ok = bool(prov and prov.disponible())
                except Exception:
                    ok = False
                icon = "✅" if ok else "🔒"
                return f"{icon} {tr(label)}"

            lista_llms = [_label_con_estado(pid, info["label"]) for pid, info in LLM_PROVIDERS.items()]
            # Mapeo label-con-icono → provider_id para poder identificar
            self.app._llm_label_to_id = {
                _label_con_estado(pid, info["label"]): pid
                for pid, info in LLM_PROVIDERS.items()
            }
            # Guardar referencia para refrescar luego (al cambiar de cerebro o al guardar key)
            self.app._llm_lista_llms = lista_llms
            self.app._llm_label_con_estado_fn = _label_con_estado

            # Determinar valor inicial según provider activo
            try:
                pid_activo = self.app.clients.provider_activo_id if hasattr(self.app.clients, 'provider_activo_id') else "deepseek"
                info_activa = LLM_PROVIDERS.get(pid_activo, {})
                label_inicial = _label_con_estado(pid_activo, info_activa.get("label", ""))
                if label_inicial in lista_llms:
                    self.app.llm_var.set(label_inicial)
                else:
                    self.app.llm_var.set(lista_llms[0])
            except Exception as e:
                logger.debug(f"[silent] {e}")
        except Exception:
            # Fallback al sistema antiguo si falla algo
            lista_llms = ["DeepSeek V4", "Google Gemini", "OpenAI GPT-4o", "Local (Ollama)"]
            self.app._llm_label_to_id = {}
        self.app.combo_llm = ctk.CTkComboBox(frame_llm, values=lista_llms, variable=self.app.llm_var, width=240, height=28,
                                          fg_color=combo_bg, border_color=combo_border, button_color=combo_btn,
                                          text_color=hdr_text, font=ctk.CTkFont(size=11),
                                          command=self.app._on_llm_cambio)
        self.app.combo_llm.pack(side="left")
        # Botón 🔑 para configurar API keys
        # NOTA v1.0: el color de este botón actúa también como indicador del
        # estado del proveedor — verde si está disponible, ámbar si no. Lo
        # actualiza self.app._actualizar_indicador_proveedor() (en app.py).
        self.app._btn_key = ctk.CTkButton(frame_llm, text="🔑", width=30, height=28,
                      fg_color=key_bg, hover_color=key_hover,
                      font=ctk.CTkFont(size=12),
                      command=self.app.dialogs._cmd_configurar_api_keys)
        self.app._btn_key.pack(side="left", padx=(4, 0))
        # Tooltip si CTkToolTip está instalado
        try:
            CTkToolTip(self.app._btn_key, message=tr("Click: configurar API keys\n(verde = disponible, ámbar = sin configurar)"))
        except Exception as _e:
            logger.debug(f"[silent] {_e}")

        # ── Selector de MODELO del cerebro activo (sesión 19) ──
        # Editable: la lista trae los modelos conocidos del proveedor
        # (p.ej. Claude: opus-4-8, sonnet-4-6, haiku-4-5) pero
        # se puede escribir cualquier ID a mano y pulsar Enter.
        def _on_modelo_llm_cambio(valor=None):
            try:
                modelo = (valor or self.app.combo_modelo_llm.get() or "").strip()
                pid = self.app.clients.provider_activo_id
                if modelo and self.app.clients.set_model(pid, modelo):
                    self.app.dialogs.set_estado(
                        tr('🧠 Modelo de {0}: {1}').format(pid, modelo), "#2ecc71")
            except Exception as _e:
                logger.debug(f"[silent] modelo llm: {_e}")

        def _refrescar_combo_modelo_llm():
            """Repuebla el combo con los modelos del proveedor activo."""
            try:
                from api_clients import LLM_PROVIDERS as _PROVS
                pid = self.app.clients.provider_activo_id
                info = _PROVS.get(pid, {})
                modelos = list(info.get("modelos", []) or
                               ([info.get("model_default")] if info.get("model_default") else []))
                actual = self.app.clients.get_model(pid)
                if actual and actual not in modelos:
                    modelos.insert(0, actual)
                self.app.combo_modelo_llm.configure(values=modelos)
                self.app.combo_modelo_llm.set(actual or (modelos[0] if modelos else ""))
            except Exception as _e:
                logger.debug(f"[silent] refresco modelo llm: {_e}")

        self.app.combo_modelo_llm = ctk.CTkComboBox(
            frame_llm, values=[""], width=185, height=28,
            fg_color=combo_bg, border_color=combo_border, button_color=combo_btn,
            text_color=hdr_text, font=ctk.CTkFont(size=10),
            command=_on_modelo_llm_cambio)
        self.app.combo_modelo_llm.pack(side="left", padx=(4, 0))
        self.app.combo_modelo_llm.bind(
            "<Return>", lambda _e: _on_modelo_llm_cambio())
        self.app._refrescar_combo_modelo_llm = _refrescar_combo_modelo_llm
        _refrescar_combo_modelo_llm()
        try:
            CTkToolTip(self.app.combo_modelo_llm,
                       message=tr("Modelo del cerebro activo.\nElige de la lista o escribe un ID y pulsa Enter."))
        except Exception as _e:
            logger.debug(f"[silent] {_e}")

        # ── Indicador de ADN visual activo ──
        # Se muestra solo cuando hay self.app._anclaje_visual. Es un botón
        # clicable que abre un menú con: ver / desactivar.
        self.app._btn_adn = ctk.CTkButton(
            frame_llm, text=tr("🧬 ADN"), width=70, height=28,
            fg_color="#1a7a3c", hover_color="#145e2d",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.app._cmd_indicador_adn,
        )
        # No empaquetar todavía: solo se muestra si hay ADN activo
        try:
            CTkToolTip(self.app._btn_adn,
                       message=tr("ADN visual activo en próximas generaciones.\nClick para ver / desactivar."))
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
            (tr("📊 Análisis"), "#8e4ab0", [
                (tr("🚀  Auto-mejora"), self.app.analysis.cmd_automejora_periodica),
                (tr("💰  Coste de sesión"), self.app.analysis.cmd_coste_sesion),
                (tr("📝  Crítica historial"), self.app.analysis.cmd_critica_historial),
                (tr("📈  Estadísticas"), self.app.analysis.abrir_estadisticas),
                (tr("🎯  Optimizador en bucle"), self.app.analysis.cmd_optimizar_loop),
            ]),
            (tr("📚 Aprender"), "#2e8a9e", [
                (tr("ℹ️  Acerca de G-Prompt"), self.app.dialogs.cmd_acerca_de),
                (tr("⌨️  Atajos teclado"), self.app.atajos.cmd_mostrar_atajos),
                (tr("📖  Guía de estilos"), lambda: abrir_guia_estilos(self.app, self.app.modo_var.get() if hasattr(self.app, "modo_var") else None)),
                (tr("📖  Modo educativo"), self.app.analysis.cmd_modo_educativo),
                (tr("📚  Tutorial completo"), self.app.atajos.abrir_tutorial),
            ]),
            (tr("💾 Backup"), "#a04545", [
                (tr("💼  Backup completo"), self.app.backup.cmd_backup_completo),
                (tr("📊  Exportar CSV"), self.app.backup.cmd_exportar_csv),
                (tr("📂  Restaurar backup"), self.app.backup.cmd_restore_completo),
            ]),
            (tr("📁 Datos"), "#3d7a9c", [
                (tr("🌟  Estrellas"), lambda: abrir_lista(self.app, "estrellas", "🌟 Prompts Estrella", "#4a2800")),
                (tr("📤  Exportar como JSON pro (Veo/Sora/Kling)"), self.app.json.cmd_exportar),
                (tr("⭐  Favoritos"), lambda: abrir_lista(self.app, "favoritos", "⭐ Prompts Favoritos", "#3a3000")),
                (tr("📋  Historial"), lambda: abrir_lista(self.app, "historial", "📋 Historial de Prompts", "#1a2a3a")),
                (tr("📥  Importar prompt JSON pro"), self.app.json.cmd_importar),
                (tr("🔗  LoRAs"), lambda: abrir_loras(self.app)),
                (tr("🧑  Personajes"), lambda: abrir_personajes(self.app)),
            ]),
            (tr("🛠 Herramientas"), "#c97a2e", [
                (tr("🎯  Adaptar al modelo activo"), self.app.workflow.cmd_adaptar_modelo),
                (tr("🔒  Anclaje rasgos (consistencia)"), self.app.creative.cmd_anclaje_visual),
                (tr("🧑‍🎨  Avatar dataset (LoRA)"), lambda: abrir_avatar_window(self.app)),
                (tr("🎭  Detectar estilo (3 imágenes)"), self.app.cliente.cmd_companero_moodboard),
                (tr("📤  Export CLI"), self.app.backup.cmd_export_cli),
                (tr("💼  Modo Cliente"), self.app.cliente.cmd_modo_cliente),
                (tr("🧰  Negative builder"), self.app.creative.cmd_negative_builder),
                (tr("🎨  Paleta colores"), self.app.creative.cmd_color_palette),
            ]),
            (tr("📝 Plantillas"), "#2ea866", [
                (tr("⚡  Auto-expansión (en idea)"), self.app.data.cmd_gestionar_snippets),
                (tr("🧬  Biblioteca ADN"), self.app.adn.cmd_ver_biblioteca),
                (tr("📐  Fórmulas"), self.app.data.abrir_formulas),
                (tr("📋  Plantillas"), self.app._cmd_plantillas_populares),
                (tr("💎  Seeds favoritos"), self.app.analysis.abrir_seeds_favoritos),
                (tr("🏷  Tags reutilizables (al prompt)"), self.app.data.abrir_snippets),
            ]),
            (tr("🎨 UI"), "#7a7a8a", [
                (tr("⚙️  Ajustes"), self.app.dialogs.cmd_preferencias),
                (tr("📚  Biblioteca"), self.app.data.abrir_biblioteca),
                (tr("🌗  Cambiar tema"), self.app.dialogs.cmd_toggle_tema),
                (tr("🏠  Dashboard"), self.app.dashboard.cmd_abrir),
                (tr("🌐  Idioma (EN/ES)"), self.app.dialogs.cmd_toggle_idioma),
                (tr("🎯  Modo Focus"), self.app.creative.cmd_modo_focus),
            ]),
            (tr("⚙️ Workflow"), "#c9b32e", [
                (tr("🆚  A/B Testing"), self.app.ab.cmd_ab_testing),
                (tr("🔎  Búsqueda global"), self.app.backup.cmd_busqueda_global),
                (tr("⏰  Cron prompts"), self.app.workflow.cmd_cron_prompts),
                (tr("🎙 Grabar sesión"), self.app.sesion.cmd_grabar_toggle),
                (tr("👥  Grupo personajes"), self.app.creative.cmd_grupo_personajes),
                (tr("🔄  Macros"), self.app.workflow.abrir_macros),
                (tr("📁  Proyectos"), self.app.workflow.cmd_proyectos),
                (tr("📑  Versiones prompt"), self.app.workflow.cmd_versiones_prompt),
            ]),
        ]

        self.app._header_menus = []
        self.app._header_btns = []
        self.app._active_menu_popup = None
        self.app._active_menu_label = None

        def _close_menu():
            try:
                popup = getattr(self.app, '_active_menu_popup', None)
                if popup and popup.winfo_exists():
                    popup.destroy()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            self.app._active_menu_popup = None
            self.app._active_menu_label = None

        def _on_global_click(event):
            popup = getattr(self.app, '_active_menu_popup', None)
            if not popup or not popup.winfo_exists():
                return
            try:
                px, py = popup.winfo_rootx(), popup.winfo_rooty()
                pw, ph = popup.winfo_width(), popup.winfo_height()
                if px <= event.x_root <= px + pw and py <= event.y_root <= py + ph:
                    return
                for bb, _, _, _ in self.app._header_menus:
                    bx, by, bw, bh = bb.winfo_rootx(), bb.winfo_rooty(), bb.winfo_width(), bb.winfo_height()
                    if bx <= event.x_root <= bx + bw and by <= event.y_root <= by + bh:
                        return
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            _close_menu()

        self.app.bind("<Button-1>", _on_global_click, add="+")

        def _make_toggle(lg, il, cb):
            def _toggle():
                popup = getattr(self.app, '_active_menu_popup', None)
                if self.app._active_menu_label == lg and popup and popup.winfo_exists():
                    _close_menu()
                    return
                _close_menu()
                btn_real = None
                for bb, lg2, _, _ in self.app._header_menus:
                    if lg2 == lg:
                        btn_real = bb
                        break
                if btn_real is None:
                    return
                # Toplevel PLANO de tkinter (no GPromptWindow/CTkToplevel):
                # un popup overrideredirect con CTkToplevel en Windows puede
                # quedar invisible/detrás de la ventana principal — además
                # GPromptWindow._bring_to_front quita el topmost a los 250ms
                # y la ventana sin gestión cae al fondo del z-order.
                # Bug sesión 19: "clic en el menú y no se abre nada".
                import tkinter as tk
                is_lt = ctk.get_appearance_mode().lower() == "light"
                new_popup = tk.Toplevel(self.app)
                self.app._active_menu_popup = new_popup
                self.app._active_menu_label = lg
                new_popup.overrideredirect(True)
                new_popup.configure(bg="#ffffff" if is_lt else "#1f2937")
                try:
                    abs_x = btn_real.winfo_rootx()
                    abs_y = btn_real.winfo_rooty() + btn_real.winfo_height() + 4
                    # El menú es más ancho que el botón (~240px). Si abierto a la
                    # izquierda del botón se saldría por la derecha de la ventana
                    # (caso del botón "Workflow", el más a la derecha), anclarlo
                    # para que su borde derecho quede dentro, creciendo a la
                    # izquierda. Se calcula ANTES del geometry inicial porque mover
                    # un Toplevel overrideredirect ya mapeado no surte efecto.
                    menu_w = 240
                    margen = 40   # hueco respecto al borde derecho de la ventana
                    win_left = self.app.winfo_rootx()
                    win_right = win_left + self.app.winfo_width()
                    if abs_x + menu_w > win_right - margen:
                        abs_x = max(win_left + 12, win_right - menu_w - margen)
                except Exception:
                    abs_x, abs_y = 200, 100
                new_popup.geometry(f"+{abs_x}+{abs_y}")

                bg_frame = ctk.CTkFrame(new_popup, fg_color="#ffffff" if is_lt else "#1f2937", border_color=cb, border_width=2, corner_radius=8)
                bg_frame.pack(fill="both", expand=True, padx=2, pady=2)

                for item_label, item_cmd in il:
                    btn_item = ctk.CTkButton(bg_frame, text=item_label, width=220, height=30,
                                              fg_color="transparent", hover_color="#e5e7eb" if is_lt else "#374151",
                                              text_color="#111827" if is_lt else "#e5e7eb", font=ctk.CTkFont(size=11),
                                              anchor="w", corner_radius=4,
                                              command=lambda c=item_cmd: (c(), _close_menu()))
                    btn_item.pack(fill="x", padx=4, pady=2)

                # Mantener el popup por encima MIENTRAS está abierto (se
                # cierra al hacer clic fuera, así que no molesta).
                new_popup.attributes("-topmost", True)
                new_popup.lift()
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

            self.app._header_menus.append((btn, label_grupo, color_borde, items))
            self.app._header_btns.append(btn)

        # ── Modo compacto responsivo (v1.0) ──
        # Si la ventana es estrecha (<1180px), reducir labels a solo emoji
        # para que quepan los 7 menús del header.
        self.app._header_compacto = False
        self.app._header_labels_originales = {btn: btn.cget("text") for btn in self.app._header_btns}

        def _on_resize(event=None):
            try:
                # Fix A1 fase 2: el widget es self.app (ArquitectoApp),
                # no self (UIBuildersService). Antes el guard siempre era
                # True → el handler retornaba sin actualizar → los botones
                # se quedaban en modo compacto (cuadrados) tras el primer
                # tick del after(200) que dispara con ancho parcial.
                if event is not None and event.widget is not self.app:
                    return
                ancho = self.app.winfo_width()
                debe_compactar = ancho < 1180
                if debe_compactar == self.app._header_compacto:
                    return
                self.app._header_compacto = debe_compactar
                for btn in self.app._header_btns:
                    label_orig = self.app._header_labels_originales.get(btn, "")
                    if debe_compactar:
                        # Solo emoji (la primera "palabra" antes del espacio)
                        emoji = label_orig.split(" ")[0] if " " in label_orig else label_orig
                        btn.configure(text=emoji, width=42)
                    else:
                        btn.configure(text=label_orig, width=120)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        self.app.bind("<Configure>", _on_resize, add="+")
        self.app.after(200, _on_resize)

    def _refrescar_indicadores_llm(self):
        """Recalcula los iconos ✅/🔒 del desplegable de cerebro.

        Se llama tras cambiar de proveedor o guardar una key nueva, para que
        el desplegable refleje el estado real sin reiniciar la app.
        """
        try:
            if not hasattr(self.app, "_llm_label_con_estado_fn"):
                return
            from api_clients import LLM_PROVIDERS
            label_fn = self.app._llm_label_con_estado_fn

            nueva_lista = [label_fn(pid, info["label"]) for pid, info in LLM_PROVIDERS.items()]
            self.app._llm_label_to_id = {
                label_fn(pid, info["label"]): pid for pid, info in LLM_PROVIDERS.items()
            }

            # Recordar selección actual (mapeada a pid para reasignar tras refresh)
            pid_actual = None
            try:
                if hasattr(self.app.clients, "provider_activo_id"):
                    pid_actual = self.app.clients.provider_activo_id
            except Exception:
                pid_actual = None

            if hasattr(self.app, "combo_llm"):
                self.app.combo_llm.configure(values=nueva_lista)
                if pid_actual:
                    info_act = LLM_PROVIDERS.get(pid_actual, {})
                    nuevo_label = label_fn(pid_actual, info_act.get("label", ""))
                    if nuevo_label in nueva_lista:
                        self.app.llm_var.set(nuevo_label)
        except Exception as e:
            logger.debug(f"[silent] refrescar indicadores llm: {e}")

    def _build_modo(self):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        modo_bg = c["modo_bg"]
        modo_label = c["modo_label"]

        frame = ctk.CTkFrame(self.app, fg_color=modo_bg, corner_radius=0)
        frame.pack(fill="x", padx=16, pady=(6, 2))
        self.app._modo_frame = frame
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=8, pady=6)

        seg = ctk.CTkSegmentedButton(inner, values=[tr("Imagen"), tr("Vídeo"), tr("Audio")],
                                      command=self._on_segmento_modo, height=28,
                                      font=ctk.CTkFont(size=11))
        seg.set(tr("Imagen"))
        seg.pack(side="left", padx=(0, 12))
        self.app._seg_modo = seg

        self.app._lbl_plataforma = ctk.CTkLabel(inner, text=tr("Plataforma:"), font=ctk.CTkFont(size=11), fg_color="transparent", text_color=modo_label)
        self.app._lbl_plataforma.pack(side="left", padx=(0, 4))
        self.app.combo_plataforma = ctk.CTkComboBox(inner, values=PLATAFORMAS_IMAGEN_LISTA, variable=self.app.plataforma_var,
                                                 width=180, height=28, font=ctk.CTkFont(size=11),
                                                 command=self.app.events.on_plataforma_cambio)
        self.app.combo_plataforma.pack(side="left", padx=(0, 10))

        # Dimensiones tipo "iOS pill" — pelota más pequeña que el body para
        # que se vea claramente la diferencia entre encendido/apagado.
        sw_style = {
            "font": ctk.CTkFont(size=11, weight="bold"),
            "height": 20, "width": 42, "corner_radius": 10,
            "button_length": 8,
            "button_color": "#374151" if is_light else "#e5e7eb",
            "button_hover_color": "#1f2937" if is_light else "#f3f4f6",
            "border_width": 1,
        }

        # Switches NSFW y Auto-trad — colores originales para mantener el
        # aspecto consistente con el resto de la UI (estilo "imagen 3"
        # solicitado por el usuario).
        nsfw_text_on = c["nsfw_text_on"]
        nsfw_text_off = c["nsfw_text_off"]
        nsfw_border_on = c["nsfw_border_on"]
        nsfw_border_off = c["nsfw_border_off"]
        nsfw_fg = c["nsfw_fg"]

        def _toggle_nsfw_visual():
            self.app.reiniciar_memoria()
            if self.app.switch_nsfw_var.get():
                self.app.switch_nsfw.configure(text_color=nsfw_text_on, border_color=nsfw_border_on)
            else:
                self.app.switch_nsfw.configure(text_color=nsfw_text_off, border_color=nsfw_border_off)

        self.app.switch_nsfw = ctk.CTkSwitch(inner, text=tr("🔞 NSFW"), variable=self.app.switch_nsfw_var,
                                          command=_toggle_nsfw_visual,
                                          progress_color="#dc2626",
                                          fg_color=nsfw_fg,
                                          border_color=nsfw_border_off,
                                          text_color=nsfw_text_off,
                                          **sw_style)
        self.app.switch_nsfw.pack(side="right", padx=6)
        CTkToolTip(self.app.switch_nsfw, message=tr("Activa contenido adulto en los prompts."), delay=0.5)

        def _toggle_trad_visual():
            if self.app.switch_traduccion_var.get():
                self.app.switch_trad.configure(text_color=c["trad_text_on"], border_color=c["trad_border_on"])
            else:
                self.app.switch_trad.configure(text_color=c["fg_dark_text"], border_color=c["fg_dark_border"])

        self.app.switch_trad = ctk.CTkSwitch(inner, text=tr("🌐 Auto-trad"), variable=self.app.switch_traduccion_var,
                                          command=_toggle_trad_visual,
                                          progress_color="#2563eb",
                                          fg_color=c["fg_dark"],
                                          border_color=c["fg_dark_border"],
                                          text_color=c["fg_dark_text"],
                                          **sw_style)
        self.app.switch_trad.pack(side="right", padx=6)
        CTkToolTip(self.app.switch_trad, message=tr("Traduce tu idea al inglés antes de procesarla."), delay=0.5)
        self.app._sw_trad = self.app.switch_trad
        self.app._sw_trad_callback = _toggle_trad_visual

        # Switch "🖼 Ref" — la imagen subida en Img→Prompt se tratará como
        # referencia visual (storyboard/moodboard/style guide), NO se
        # describirá literalmente. Extrae solo paleta/iluminación/personajes
        # /estilo gráfico para que el prompt resultante mantenga ese aspecto
        # visual pero genere contenido original.
        def _toggle_ref_visual():
            if self.app.switch_ref_visual_var.get():
                self.app.switch_ref.configure(text_color=c["trad_text_on"], border_color=c["trad_border_on"])
                # Aviso: en plataformas de vídeo (Seedance, Kling 2.x) si
                # subes la MISMA imagen otra vez con el prompt, el motor
                # la interpreta como image-to-video y el frame 1 acaba
                # siendo la imagen literal (no la guía visual).
                try:
                    self.app.dialogs.set_estado(
                        tr("🖼 Ref ON: pega SOLO el prompt en la plataforma de vídeo destino — NO subas otra vez la imagen ahí."),
                        "#7c3aed",
                    )
                except Exception as _e:
                    logger.debug(f"[silent ref toast] {_e}")
            else:
                self.app.switch_ref.configure(text_color=c["fg_dark_text"], border_color=c["fg_dark_border"])

        self.app.switch_ref = ctk.CTkSwitch(inner, text=tr("🖼 Ref"), variable=self.app.switch_ref_visual_var,
                                         command=_toggle_ref_visual,
                                         progress_color="#7c3aed",
                                         fg_color=c["fg_dark"],
                                         border_color=c["fg_dark_border"],
                                         text_color=c["fg_dark_text"],
                                         **sw_style)
        self.app.switch_ref.pack(side="right", padx=6)
        CTkToolTip(self.app.switch_ref,
                    message=(tr("Img→Prompt: trata la imagen como REFERENCIA VISUAL "
                             "(storyboard, moodboard, style guide).\n"
                             "OFF (defecto): el prompt reproduce fielmente la imagen.\n"
                             "ON: extrae solo paleta/iluminación/personajes/estilo "
                             "y genera prompt original con esa guía visual.")),
                    delay=0.5)

        # Aplicar estilo inicial coherente con el estado del var (importante
        # cuando se restauran desde prefs). NO usamos _toggle_nsfw_visual()
        # directamente porque llama a reiniciar_memoria() que asume que la
        # app está completamente construida.
        if self.app.switch_nsfw_var.get():
            self.app.switch_nsfw.configure(text_color=nsfw_text_on, border_color=nsfw_border_on)
        if self.app.switch_traduccion_var.get():
            self.app.switch_trad.configure(text_color=c["trad_text_on"], border_color=c["trad_border_on"])
        if self.app.switch_ref_visual_var.get():
            self.app.switch_ref.configure(text_color=c["trad_text_on"], border_color=c["trad_border_on"])

    def _on_segmento_modo(self, valor):
        mapa = {tr("Imagen"): "imagen", tr("Vídeo"): "video", tr("Audio"): "audio"}
        self.app.modo_var.set(mapa.get(valor, "imagen"))
        self.app.events.on_modo_cambio()

    def _build_video_panel(self):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        lbl_color = c["panel_text"]

        self.app.frame_video = ctk.CTkFrame(self.app, height=42, fg_color=c["panel_bg"])
        self.app.frame_video.pack_propagate(False)

        ctk.CTkLabel(self.app.frame_video, text=tr("Modelo:"),
                     font=ctk.CTkFont(weight="bold"),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=15)
        self.app.combo_modelo_video = ctk.CTkComboBox(self.app.frame_video, values=MODELOS_VIDEO_FLAT, width=215, command=self.app.events.on_motor_cambio)
        self.app.combo_modelo_video.set("Kling 3.0")
        self.app.combo_modelo_video.pack(side="left", padx=5)
        from modules.searchable_dropdown import attach_searchable_dropdown
        attach_searchable_dropdown(self.app.combo_modelo_video,
                                   command=self.app.events.on_motor_cambio)

        ctk.CTkLabel(self.app.frame_video, text=tr("Duración:"),
                     font=ctk.CTkFont(weight="bold"),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(15, 5))
        ctk.CTkEntry(self.app.frame_video, textvariable=self.app.duracion_var, width=70).pack(side="left", padx=5)
        # Selector de shots: Auto (regla por duración) o manual 1-6.
        ctk.CTkLabel(self.app.frame_video, text=tr("Shots:"),
                     font=ctk.CTkFont(weight="bold"),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(10, 5))
        self.app.combo_shots = ctk.CTkComboBox(self.app.frame_video,
                                            values=["Auto", "1", "2", "3", "4", "5", "6"],
                                            variable=self.app.shots_var, width=70,
                                            command=lambda v: self.app.shots_var.set(v))
        self.app.combo_shots.set("Auto")
        self.app.combo_shots.pack(side="left", padx=5)
        try:
            CTkToolTip(self.app.combo_shots,
                        message=(tr("Número de shots/planos en el prompt de vídeo.\n"
                                 "Auto: deduce según duración (4s=1, 5s=2, 10s=3, 15s=4).\n"
                                 "Manual (1-6): fuerza ese número exacto.")),
                        delay=0.5)
        except Exception as _e:
            logger.debug(f"[silent] tooltip shots: {_e}")
        # Combo "Estilo" (look visual): complementa los géneros narrativos del
        # footer (ESTILOS_VIDEO). La selección se inyecta como hint en el system
        # prompt vía prompts_inyeccion._inyectar_estilo_video.
        ctk.CTkLabel(self.app.frame_video, text=tr("Estilo:"),
                     font=ctk.CTkFont(weight="bold"),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(10, 5))
        self.app._estilo_vid_disp2key = {tr(v): v for v in ESTILOS_VISUAL_VIDEO}
        self.app.combo_estilo_video = ctk.CTkComboBox(
            self.app.frame_video, values=[tr(v) for v in ESTILOS_VISUAL_VIDEO],
            width=140,
            font=ctk.CTkFont(size=11),
            command=lambda disp: self.app.estilo_video_var.set(
                self.app._estilo_vid_disp2key.get(disp, disp)))
        self.app.combo_estilo_video.set("Auto")
        self.app.combo_estilo_video.pack(side="left", padx=5)
        try:
            CTkToolTip(self.app.combo_estilo_video, delay=0.4,
                       message=tr("Look visual del vídeo (estética de render). "
                               "Complementa los géneros del footer. Auto = no fuerza nada."))
        except Exception as _e:
            logger.debug(f"[silent] tooltip estilo video: {_e}")

        ctk.CTkLabel(self.app.frame_video, text=tr("Ratio:"),
                     font=ctk.CTkFont(weight="bold"),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(10, 5))
        self.app.combo_ratio_v = ctk.CTkComboBox(self.app.frame_video, values=RATIOS_VIDEO, variable=self.app.ratio_var, width=85, command=lambda v: self.app.ratio_var.set(v))
        self.app.combo_ratio_v.set("16:9")
        self.app.combo_ratio_v.pack(side="left", padx=5)

        # Destino al lado del ratio
        ctk.CTkLabel(self.app.frame_video, text=tr("Destino:"),
                     font=ctk.CTkFont(weight="bold"),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(15, 5))
        self.app.combo_destino_vid = ctk.CTkComboBox(self.app.frame_video, values=[tr(d) for d in DESTINOS], variable=self.app.destino_var, width=140,
                                                   font=ctk.CTkFont(size=11), command=self._on_destino_cambio)
        self.app.combo_destino_vid.pack(side="left", padx=5)

    def _build_audio_panel(self):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        lbl_color = c["panel_text"]

        self.app.frame_audio = ctk.CTkFrame(self.app, fg_color=c["panel_bg"])

        # Fila 1: Modelo + Destino + Instrumental
        row1 = ctk.CTkFrame(self.app.frame_audio, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(5, 2))

        ctk.CTkLabel(row1, text=tr("Modelo:"), font=ctk.CTkFont(weight="bold"),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(5, 5))
        self.app.combo_modelo_audio = ctk.CTkComboBox(row1, values=MODELOS_AUDIO_FLAT, width=215, command=self.app.events.on_motor_audio_cambio)
        self.app.combo_modelo_audio.set("Suno v5")
        self.app.combo_modelo_audio.pack(side="left", padx=5)
        from modules.searchable_dropdown import attach_searchable_dropdown
        attach_searchable_dropdown(self.app.combo_modelo_audio,
                                   command=self.app.events.on_motor_audio_cambio)

        # Destino al lado del modelo
        ctk.CTkLabel(row1, text=tr("Destino:"), font=ctk.CTkFont(weight="bold"),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(15, 5))
        self.app.combo_destino_aud = ctk.CTkComboBox(row1, values=[tr(d) for d in DESTINOS], variable=self.app.destino_var, width=140,
                                                   font=ctk.CTkFont(size=11), command=self._on_destino_cambio)
        self.app.combo_destino_aud.pack(side="left", padx=5)

        self.app.switch_instrumental_var = ctk.BooleanVar(value=False)

        def _toggle_instr_visual():
            self.app.reiniciar_memoria()
            if self.app.switch_instrumental_var.get():
                self.app.switch_instrumental.configure(text_color=c["instr_active_text"], border_color=c["instr_active_border"])
            else:
                self.app.switch_instrumental.configure(text_color=c["fg_dark_text"], border_color=c["fg_dark_border"])

        self.app.switch_instrumental = ctk.CTkSwitch(row1, text=tr("🎹 Instrumental"),
                                                   variable=self.app.switch_instrumental_var,
                                                   command=_toggle_instr_visual,
                                                   progress_color="#7c3aed",
                                                   fg_color=c["fg_dark"],
                                                   border_color=c["fg_dark_border"],
                                                   border_width=1,
                                                   text_color=c["fg_dark_text"],
                                                   font=ctk.CTkFont(size=11, weight="bold"),
                                                   height=20, width=42, corner_radius=10,
                                                   button_length=8,
                                                   button_color="#374151" if is_light else "#e5e7eb",
                                                   button_hover_color="#1f2937" if is_light else "#f3f4f6")
        self.app.switch_instrumental.pack(side="left", padx=15)

        # Fila 2: Emoción + Voz + Idioma
        row2 = ctk.CTkFrame(self.app.frame_audio, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(0, 5))

        self.app.emocion_var = ctk.StringVar(value=tr("— Emoción —"))
        ctk.CTkLabel(row2, text=tr("Emoción:"), font=ctk.CTkFont(weight="bold", size=11),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(5, 3))
        self.app.combo_emocion = ctk.CTkComboBox(row2, values=[tr("— Emoción —")] + [tr(e) for e in EMOCIONES_AUDIO], variable=self.app.emocion_var, width=130, command=self.app.events.on_audio_filtro_cambio)
        self.app.combo_emocion.pack(side="left", padx=(0, 10))

        self.app.voz_var = ctk.StringVar(value=tr("— Voz —"))
        ctk.CTkLabel(row2, text=tr("Voz:"), font=ctk.CTkFont(weight="bold", size=11),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(0, 3))
        self.app.combo_voz = ctk.CTkComboBox(row2, values=[tr("— Voz —")] + [tr(v) for v in VOCES_AUDIO], variable=self.app.voz_var, width=155, command=self.app.events.on_audio_filtro_cambio)
        self.app.combo_voz.pack(side="left", padx=(0, 10))

        self.app.idioma_audio_var = ctk.StringVar(value=tr("— Idioma —"))
        ctk.CTkLabel(row2, text=tr("Idioma:"), font=ctk.CTkFont(weight="bold", size=11),
                     fg_color="transparent",
                     text_color=lbl_color).pack(side="left", padx=(0, 3))
        self.app.combo_idioma_audio = ctk.CTkComboBox(row2, values=[tr("— Idioma —")] + [tr(i) for i in IDIOMAS_AUDIO], variable=self.app.idioma_audio_var, width=160, command=self.app.events.on_audio_filtro_cambio)
        self.app.combo_idioma_audio.pack(side="left", padx=(0, 5))

    def _build_modelo_imagen_panel(self):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        lbl_color = c["panel_label"]
        ratio_btn_bg = "#ffffff" if is_light else "#1a2030"
        ratio_btn_hover = "#dbeafe" if is_light else "#2a3a50"

        self.app.frame_modelo_imagen = ctk.CTkFrame(self.app, fg_color="transparent")

        inner = ctk.CTkFrame(self.app.frame_modelo_imagen, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=2)

        # Modelo
        f1 = ctk.CTkFrame(inner, fg_color="transparent")
        f1.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(f1, text=tr("Modelo"), font=ctk.CTkFont(size=10),
                     fg_color="transparent", text_color=lbl_color).pack(anchor="w")
        self.app.combo_modelo_imagen = ctk.CTkComboBox(f1, values=MODELOS_IMAGEN_FLAT, width=220, height=28,
                                                    font=ctk.CTkFont(size=11), command=self.app.events.on_modelo_imagen_cambio)
        self.app.combo_modelo_imagen.set("Z Image Turbo")
        self.app.combo_modelo_imagen.pack()
        # Desplegable con buscador + scroll (la lista de modelos crece mucho).
        from modules.searchable_dropdown import attach_searchable_dropdown
        attach_searchable_dropdown(
            self.app.combo_modelo_imagen,
            command=self.app.events.on_modelo_imagen_cambio)
        self.app._tooltip_modelo_actual = CTkToolTip(self.app.combo_modelo_imagen, delay=0.6, message=tr("Pasa el cursor para info del modelo"))

        # Combo "Estilo" — visible solo cuando el modelo es de una familia
        # con estilos definidos en config.ESTILOS_POR_FAMILIA. Los valores
        # se repueblan dinámicamente desde on_modelo_imagen_cambio.
        # Hint de categoría al LLM que se inyecta en la plantilla específica.
        self.app.frame_familia_estilo = ctk.CTkFrame(inner, fg_color="transparent")
        # No se hace pack() inicial — _on_modelo_imagen_cambio decide.
        ctk.CTkLabel(self.app.frame_familia_estilo, text=tr("Estilo"),
                     font=ctk.CTkFont(size=10),
                     fg_color="transparent", text_color=lbl_color).pack(anchor="w")
        # i18n: el combo MUESTRA el estilo traducido pero la var guarda SIEMPRE
        # la clave ES (la inyección busca el hint por esa clave). Mapeo
        # display→clave reconstruido en cada repoblación (_on_modelo_imagen_cambio).
        self.app._estilo_img_disp2key = {}
        self.app.combo_familia_estilo = ctk.CTkComboBox(
            self.app.frame_familia_estilo,
            values=["Auto"],   # placeholder — _on_modelo_imagen_cambio lo repuebla
            width=140, height=28,
            font=ctk.CTkFont(size=11),
            command=lambda disp: self.app.familia_estilo_var.set(
                self.app._estilo_img_disp2key.get(disp, disp)),
        )
        self.app.combo_familia_estilo.set("Auto")
        self.app.combo_familia_estilo.pack()
        self.app._tooltip_familia_estilo = CTkToolTip(
            self.app.combo_familia_estilo, delay=0.4,
            message=tr("Hint de estilo para la familia del modelo activo."),
        )

        # Ratio
        f2 = ctk.CTkFrame(inner, fg_color="transparent")
        f2.pack(side="left", padx=8)
        ctk.CTkLabel(f2, text=tr("Ratio"), font=ctk.CTkFont(size=10),
                     fg_color="transparent", text_color=lbl_color).pack(anchor="w")
        f2_inner = ctk.CTkFrame(f2, fg_color="transparent")
        f2_inner.pack()
        self.app.combo_ratio = ctk.CTkComboBox(f2_inner, values=[tr(r) for r in RATIOS_IMAGEN], variable=self.app.ratio_var, width=80, height=28,
                                            font=ctk.CTkFont(size=11), command=lambda v: self.app.ratio_var.set(v))
        self.app.combo_ratio.set("1:1")
        self.app.combo_ratio.pack(side="left")

        # Botones rápidos de ratio (visuales)
        self.app.ratio_btns = {}
        ratios_quick = [
            ("⬜", "1:1",  tr("Cuadrado (Instagram post)")),
            ("📱", "9:16", tr("Vertical (Stories/TikTok/Reels)")),
            ("🖥", "16:9", tr("Horizontal (YouTube/Web)")),
            ("📸", "2:3",  tr("Foto vertical (retrato)")),
            ("🖼", "3:2",  tr("Foto horizontal (paisaje)")),
        ]
        for icono, ratio_val, tip in ratios_quick:
            btn = ctk.CTkButton(f2_inner, text=icono, width=24, height=28,
                                  fg_color=ratio_btn_bg, hover_color=ratio_btn_hover,
                                  text_color=c["panel_text"],
                                  font=ctk.CTkFont(size=11),
                                  command=lambda r=ratio_val: self._aplicar_ratio_rapido(r))
            btn.pack(side="left", padx=1)
            CTkToolTip(btn, delay=0.3, message=f"{ratio_val} — {tip}")
            self.app.ratio_btns[ratio_val] = btn

        # Destino — al final de la fila
        f0 = ctk.CTkFrame(inner, fg_color="transparent")
        f0.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(f0, text=tr("Destino"), font=ctk.CTkFont(size=10),
                     fg_color="transparent", text_color=lbl_color).pack(anchor="w")
        self.app.combo_destino_img = ctk.CTkComboBox(f0, values=[tr(d) for d in DESTINOS], variable=self.app.destino_var, width=140, height=28,
                                                   font=ctk.CTkFont(size=11), command=self._on_destino_cambio)
        self.app.combo_destino_img.pack()

    def _aplicar_ratio_rapido(self, ratio):
        """Aplica un ratio rápido si está disponible para el modelo actual."""
        ratios_dispo = self.app.combo_ratio.cget("values")
        if ratio in ratios_dispo:
            self.app.ratio_var.set(ratio)
            self.app.combo_ratio.set(ratio)
            self.app.dialogs.set_estado(tr('📐 Ratio {0} aplicado').format(ratio), "#3498db")
        else:
            self.app.dialogs.set_estado(tr('⚠️ Ratio {0} no disponible para este modelo').format(ratio), "#e67e22")

    def _build_destino_panel(self):
        """Panel Destino — ahora oculto, los combos están integrados en cada panel de modo."""
        self.app.frame_destino = ctk.CTkFrame(self.app, fg_color="transparent", height=1)
        # Frame vacío, solo para mantener compatibilidad
        # El combo destino real está dentro de cada panel de modo (imagen/video/audio)
        self.app.combo_destino = self.app.combo_destino_img if hasattr(self.app, 'combo_destino_img') else None

    def _on_destino_cambio(self, valor=None):
        """Auto-ajustar ratio según destino seleccionado y sincronizar todos los combos."""
        dest = self.app.destino_var.get()
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
            self.app.ratio_var.set(ratio)
            if hasattr(self.app, 'combo_ratio'):
                self.app.combo_ratio.set(ratio)
            if hasattr(self.app, 'combo_ratio_v'):
                self.app.combo_ratio_v.set(ratio)
            self.app.dialogs.set_estado(tr('📐 Destino {0} → Ratio auto: {1}').format(dest, ratio), "#3498db")

        # Modo concurso: activar Brief automáticamente
        if dest == "Anthum (concurso)":
            self.app.brief_var.set(True)
            self.app.events.on_brief_cambio()
            self.app.dialogs.set_estado(tr("🏆 Modo Concurso Anthum — Brief activado, ratio 9:16, máxima calidad"), "#f39c12")

        self.app.reiniciar_memoria()

    def _build_tabs_centrales(self):
        # no lo pinta bien en modo light si lo dejamos sin especificar
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        tab_bg = c["panel_bg"]              # gris muy claro / azul oscuro
        seg_bg = "#e5e7eb" if is_light else "#1f2937"
        seg_sel = "#2563eb" if is_light else "#3b82f6"
        seg_hov = "#dbeafe" if is_light else "#374151"

        # CTkTabview no respeta `pack(fill="x")` y crece libremente
        # según el contenido del tab activo (con o sin expand=True
        # interno). Para forzar una altura máxima predecible, lo
        # envolvemos en un CTkFrame con height fijo + pack_propagate(False).
        # Así el tabview NUNCA se sale de los 230px reservados, y el
        # "Resultado editable" abajo siempre tiene el resto de la ventana.
        self.app._tabview_container = ctk.CTkFrame(self.app, fg_color=tab_bg,
                                                height=230)
        self.app._tabview_container.pack(pady=2, padx=20, fill="x")
        # pack_propagate(False) impide que el frame se ajuste a su
        # contenido — fuerza el height=230 aunque dentro haya widgets
        # que pidan más. Sin esto, el frame crece con el tabview.
        self.app._tabview_container.pack_propagate(False)

        self.app.tabview = ctk.CTkTabview(
            self.app._tabview_container,
            fg_color=tab_bg, bg_color=tab_bg,
            segmented_button_fg_color=seg_bg,
            segmented_button_selected_color=seg_sel,
            segmented_button_selected_hover_color=seg_sel,
            segmented_button_unselected_color=seg_bg,
            segmented_button_unselected_hover_color=seg_hov,
            text_color=c["panel_text"],
        )
        # fill="both" + expand=True para que el tabview llene el
        # container (que ya tiene la altura limitada).
        self.app.tabview.pack(fill="both", expand=True)

        self.app.tabview.add(tr("⚙️ Ajustes Extra"))
        self.app.tabview.add(tr("🎨 Estilos"))
        self.app.tabview.add(tr("🚫 Negativos"))
        self.app.tabview.add(tr("🏷️ Tags"))

        # Forzar el color del contenido de cada tab
        for tab_name in (tr("⚙️ Ajustes Extra"), tr("🎨 Estilos"), tr("🚫 Negativos"), tr("🏷️ Tags")):
            try:
                self.app.tabview.tab(tab_name).configure(fg_color=tab_bg, bg_color=tab_bg)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        # Tab 1: Ajustes Extra
        self._build_ajustes_extra(self.app.tabview.tab(tr("⚙️ Ajustes Extra")))

        # Tab 2: Estilos
        self._build_estilos(self.app.tabview.tab(tr("🎨 Estilos")))

        # Tab 3: Negativos (Permanece para no destruir widgets)
        tab_neg = self.app.tabview.tab(tr("🚫 Negativos"))
        self.app.frame_neg_outer = ctk.CTkFrame(tab_neg, fg_color=tab_bg)
        self._build_negative(self.app.frame_neg_outer)

        self.app.lbl_neg_disabled = ctk.CTkLabel(
            tab_neg, text=tr("🚫 El modelo o plataforma actual NO utiliza Negative Prompts."),
            fg_color="transparent",
            text_color=c["muted_text"], font=ctk.CTkFont(size=12, slant="italic"))

        # Tab 4: Tags picker — lazy: se construye la primera vez que el usuario
        # abre la pestaña para no bloquear el startup con 83 botones + tooltips.
        self._tags_tab_built = False

        def _on_tab_change():
            if self.app.tabview.get() == tr("🏷️ Tags") and not self._tags_tab_built:
                self._tags_tab_built = True
                self._build_tags_tab(self.app.tabview.tab(tr("🏷️ Tags")))

        self.app.tabview.configure(command=_on_tab_change)

    def _build_ajustes_extra(self, parent):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        tab_bg = c["panel_bg"]

        self.app.frame_pers_lora = ctk.CTkFrame(parent, fg_color=tab_bg)
        self.app.frame_pers_lora.pack(fill="x", pady=(2, 1))

        ctk.CTkLabel(self.app.frame_pers_lora, text=tr("🧑 Personaje:"),
                     font=ctk.CTkFont(weight="bold", size=11),
                     fg_color="transparent",
                     text_color=c["panel_text"]).pack(side="left", padx=(5, 5))
        self.app.combo_personaje = ctk.CTkComboBox(self.app.frame_pers_lora, values=[tr("— Sin personaje —")], width=160,
                                                fg_color=c["combo_bg"], border_color=c["combo_border"],
                                                text_color=c["hdr_text"],
                                                command=self.app.footer._on_personaje_selected)
        self.app.combo_personaje.pack(side="left", padx=5)

        ctk.CTkLabel(self.app.frame_pers_lora, text=tr("🔗 LoRA:"),
                     font=ctk.CTkFont(weight="bold", size=11),
                     fg_color="transparent",
                     text_color=c["panel_text"]).pack(side="left", padx=(15, 5))
        self.app.combo_lora = ctk.CTkComboBox(self.app.frame_pers_lora, values=[tr("— Sin LoRA —")], width=160,
                                            fg_color=c["combo_bg"], border_color=c["combo_border"],
                                            text_color=c["hdr_text"],
                                            command=lambda v: (
                                                self.app._sesion_log(f"🔗 LoRA → {v}") if hasattr(self.app, "_sesion_eventos") else None,
                                                self.app.footer._actualizar_lora_trigger_visible()
                                            ))
        self.app.combo_lora.pack(side="left", padx=5)

        # Botón "🔗+" — abre modal de multi-LoRA con checkboxes para
        # combinar varios LoRAs en el mismo prompt (sesión 16). El combo
        # principal sigue siendo el LoRA "primario"; los extras se guardan
        # en self.app.loras_multi (set de nombres).
        ctk.CTkButton(
            self.app.frame_pers_lora, text="🔗+", width=36, height=26,
            fg_color="#5b2c8e", hover_color="#3d1a6a",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.app.footer._abrir_multi_lora_modal,
        ).pack(side="left", padx=(2, 0))

        # Checkbox "⬆ al inicio" — coloca el trigger del LoRA al principio del
        # POSITIVE (convención SeaArt). Persistido en preferencias.
        chk_lora_inicio = ctk.CTkCheckBox(
            self.app.frame_pers_lora, text=tr("⬆ al inicio"), width=20,
            variable=self.app.lora_inicio_var, font=ctk.CTkFont(size=10),
            checkbox_width=16, checkbox_height=16)
        chk_lora_inicio.pack(side="left", padx=(6, 0))
        CTkToolTip(chk_lora_inicio, message=tr(
            "Coloca el trigger del LoRA al PRINCIPIO del prompt (como SeaArt). "
            "Si lo desactivas, va en su bloque/posición normal."))

        # Label trigger visible (Mejora bonus LoRAs)
        lora_color = "#7c3aed" if is_light else "#9b59b6"
        self.app.lbl_lora_trigger = ctk.CTkLabel(self.app.frame_pers_lora, text="",
                                               font=ctk.CTkFont(family="Consolas", size=9),
                                               fg_color="transparent",
                                               text_color=lora_color)
        self.app.lbl_lora_trigger.pack(side="left", padx=(6, 0))

        # ── Panel "Fuentes activas" — chips clickables que muestran qué
        # está inyectándose en el prompt y permiten limpiar cada fuente
        # (LoRAs, Personaje, Anclaje visual, ADN visual). Visibles solo
        # cuando hay al menos una activa.
        self.app.frame_fuentes_activas = ctk.CTkFrame(parent, fg_color=tab_bg)
        # No empaquetado inicial — _actualizar_fuentes_activas lo pack si hay algo.
        ctk.CTkLabel(
            self.app.frame_fuentes_activas, text=tr("🎯 Fuentes activas:"),
            font=ctk.CTkFont(weight="bold", size=10),
            fg_color="transparent", text_color=c["panel_text"],
        ).pack(side="left", padx=(8, 6))
        # Sub-frame donde se renderizan los chips dinámicamente
        self.app.frame_fuentes_chips = ctk.CTkFrame(
            self.app.frame_fuentes_activas, fg_color="transparent",
        )
        self.app.frame_fuentes_chips.pack(side="left", fill="x", expand=True)

        self.app.frame_plantilla_brief = ctk.CTkFrame(parent, fg_color=tab_bg)
        self.app.frame_plantilla_brief.pack(fill="x", pady=1)

        ctk.CTkLabel(self.app.frame_plantilla_brief, text=tr("📐 Plantilla:"),
                     font=ctk.CTkFont(weight="bold", size=11),
                     fg_color="transparent",
                     text_color=c["panel_text"]).pack(side="left", padx=(5, 5))
        self.app.combo_plantilla = ctk.CTkComboBox(self.app.frame_plantilla_brief, values=[tr("— Sin plantilla —")], width=180,
                                                fg_color=c["combo_bg"], border_color=c["combo_border"],
                                                text_color=c["hdr_text"], command=self.app._cargar_plantilla)
        self.app.combo_plantilla.pack(side="left", padx=5)
        ctk.CTkButton(self.app.frame_plantilla_brief, text=tr("💾 Guardar actual"), width=120, height=28,
                      fg_color="#5b2c8e", hover_color="#3d1a6a", text_color="#ffffff",
                      command=self.app._cmd_guardar_plantilla).pack(side="left", padx=(10, 4))
        ctk.CTkButton(self.app.frame_plantilla_brief, text=tr("🗑 Borrar"), width=80, height=28,
                      fg_color="#6a1a1a", hover_color="#4a0f0f", text_color="#ffffff",
                      command=self.app._cmd_borrar_plantilla).pack(side="left", padx=2)

        def _toggle_brief_visual():
            self.app.events.on_brief_cambio()
            if self.app.brief_var.get():
                self.app.switch_brief.configure(text_color="#fcd34d", border_color="#f59e0b")
            else:
                col_off = "#6b7280" if is_light else "#9ca3af"
                bord_off = "#d1d5db" if is_light else "#374151"
                self.app.switch_brief.configure(text_color=col_off, border_color=bord_off)

        sw_text_off = "#6b7280" if is_light else "#9ca3af"
        sw_bord_off = "#d1d5db" if is_light else "#374151"
        sw_fg_off = "#f3f4f6" if is_light else "#1f2937"
        self.app.switch_brief = ctk.CTkSwitch(
            self.app.frame_plantilla_brief, text=tr("⚡ Modo Brief"), variable=self.app.brief_var,
            command=_toggle_brief_visual,
            progress_color="#d97706",
            fg_color=sw_fg_off,
            border_color=sw_bord_off,
            text_color=sw_text_off,
            border_width=1,
            font=ctk.CTkFont(size=11, weight="bold"),
            height=20, width=42, corner_radius=10,
            button_length=8,
            button_color="#374151" if is_light else "#e5e7eb",
            button_hover_color="#1f2937" if is_light else "#f3f4f6")
        self.app.switch_brief.pack(side="right", padx=15)
        CTkToolTip(self.app.switch_brief, message=tr("Activa reglas de ANUNCIO PUBLICITARIO: gancho 2s, vertical 9:16, 3 beats narrativos."), delay=0.5)
        self.app._sw_brief_callback = _toggle_brief_visual

        # ─── Imagen referencia DENTRO de Ajustes Extra (debajo de Plantilla) ───
        self.app.frame_imgref_inner = ctk.CTkFrame(parent, fg_color=tab_bg)
        self.app.frame_imgref_inner.pack(fill="x", pady=(1, 2))

        ctk.CTkLabel(self.app.frame_imgref_inner, text=tr("🖼 Imagen ref:"),
                     font=ctk.CTkFont(weight="bold", size=11),
                     fg_color="transparent",
                     text_color=c["panel_text"]).pack(side="left", padx=(5, 5))
        self.app.btn_cargar_img = ctk.CTkButton(self.app.frame_imgref_inner, text=tr("📂 Cargar"), width=80, height=28,
                                             text_color="#ffffff",
                                             command=self.app._cargar_imagen)
        self.app.btn_cargar_img.pack(side="left", padx=3)
        ctk.CTkButton(self.app.frame_imgref_inner, text="🗑", width=30, height=28,
                      fg_color="#6a1a1a" if is_light else "#444",
                      hover_color="#4a0f0f" if is_light else "#333",
                      text_color="#ffffff",
                      command=self.app._limpiar_imagen).pack(side="left", padx=2)
        self.app.lbl_img_preview = ctk.CTkLabel(self.app.frame_imgref_inner, text="", width=34, height=34)
        self.app.lbl_img_preview.pack(side="left", padx=4)
        self.app.lbl_img_nombre = ctk.CTkLabel(self.app.frame_imgref_inner, text=tr("Sin imagen"),
                                            font=ctk.CTkFont(size=10),
                                            fg_color="transparent",
                                            text_color=c["muted_text"])
        self.app.lbl_img_nombre.pack(side="left", padx=2)

        # Historial de imágenes (recientes)
        sep_color = "#9ca3af" if is_light else "#333333"
        ctk.CTkLabel(self.app.frame_imgref_inner, text="│",
                     fg_color="transparent",
                     text_color=sep_color).pack(side="left", padx=4)
        ctk.CTkLabel(self.app.frame_imgref_inner, text=tr("Recientes:"),
                     font=ctk.CTkFont(size=9),
                     fg_color="transparent",
                     text_color=c["muted_text"]).pack(side="left", padx=2)
        self.app._img_history_frame = ctk.CTkFrame(self.app.frame_imgref_inner, fg_color=tab_bg)
        self.app._img_history_frame.pack(side="left", padx=2)
        self.app._img_history = []
        self.app._MAX_IMG_HISTORY = 6

        # Spacer al final: el tabview tiene altura fija (170px) y el
        # contenido de Ajustes Extra es solo ~75px. Sin este spacer,
        # los widgets quedan separados por un hueco grande en el medio.
        # Con expand=True absorbe el sobrante y empuja todo arriba.
        # IMPORTANTE: guardamos referencia para que _on_modo_cambio en
        # core.py pueda usar `before=self.app._spacer_ajustes` al re-packar
        # frame_imgref_inner (sino el imgref va al final y el spacer
        # queda EN EL MEDIO, recreando el hueco que queríamos evitar).
        self.app._spacer_ajustes = ctk.CTkFrame(parent, fg_color="transparent", height=1)
        self.app._spacer_ajustes.pack(fill="both", expand=True)

    def _build_estilos(self, parent):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        tab_bg = c["panel_bg"]

        self.app._frame_estilos_header = ctk.CTkFrame(parent, fg_color=tab_bg)
        self.app._frame_estilos_header.pack(fill="x", padx=5, pady=(0, 2))
        header_estilos = self.app._frame_estilos_header  # alias para legibilidad

        self.app.entry_busqueda = ctk.CTkEntry(header_estilos, placeholder_text=tr("🔍 Buscar estilo..."), width=180, height=24, font=ctk.CTkFont(size=11))
        self.app.entry_busqueda.pack(side="left")
        self.app.entry_busqueda.bind("<KeyRelease>", self.app.footer._filtrar_estilos)

        btn_sugerir = ctk.CTkButton(header_estilos, text=tr("🎨 Sugerir estilos"), width=130, height=24,
                                       fg_color="#3a1a5a", hover_color="#2a0f3a",
                                       text_color="#ffffff",
                                       font=ctk.CTkFont(size=10),
                                       command=self.app._cmd_sugerir_estilos)
        btn_sugerir.pack(side="left", padx=(8, 0))
        CTkToolTip(btn_sugerir, delay=0.4, message=tr("LLM analiza tu idea y marca 3-6 estilos apropiados automáticamente"))

        # Contador y botón limpiar
        self.app.lbl_estilos_count = ctk.CTkLabel(header_estilos, text="",
                                               font=ctk.CTkFont(size=10),
                                               fg_color="transparent",
                                               text_color=c["muted_text"])
        self.app.lbl_estilos_count.pack(side="left", padx=(10, 0))

        btn_limpiar_est = ctk.CTkButton(header_estilos, text="🗑", width=28, height=24,
                                          fg_color="transparent",
                                          hover_color="#fee2e2" if is_light else "#3a1a1a",
                                          text_color=c["muted_text"],
                                          font=ctk.CTkFont(size=11),
                                          command=self._limpiar_estilos)
        btn_limpiar_est.pack(side="right", padx=(0, 5))
        CTkToolTip(btn_limpiar_est, delay=0.3, message=tr("Limpiar todos los estilos seleccionados"))

        # CTkTabview reserva la altura del tab MÁS grande. height=160
        # → ~5 filas × 3 columnas = 15 estilos visibles. Suficiente
        # para un vistazo rápido, el scroll del CTkScrollableFrame
        # gestiona los 257 estilos restantes. Manteniendo el tab
        # compacto le dejamos mucho más espacio al "Resultado editable".
        self.app.frame_checks = ctk.CTkScrollableFrame(parent, fg_color=c["chk_bg"],
                                                    height=160)
        self.app.frame_checks.pack(fill="x", padx=5, pady=2)

        # Label verde con nombres de estilos seleccionados
        # Usar verde más oscuro en light para que se lea sobre fondo claro
        verde = "#059669" if is_light else "#2ecc71"
        self.app.lbl_estilos_sel = ctk.CTkLabel(parent, text="",
                                             font=ctk.CTkFont(size=11, weight="bold"),
                                             fg_color="transparent",
                                             text_color=verde,
                                             anchor="w", justify="left")
        self.app.lbl_estilos_sel.pack(fill="x", padx=8, pady=(0, 4))

        self.app.footer._construir_checkboxes(ESTILOS_IMAGEN)

    def _limpiar_estilos(self):
        """Desmarca todos los estilos seleccionados."""
        if not hasattr(self.app, 'estilo_checks'): return
        for n, v in self.app.estilo_checks.items():
            v.set(False)
        self._actualizar_contador_estilos()
        self.app.dialogs.set_estado(tr("🗑 Estilos limpiados"))

    def _actualizar_contador_estilos(self):
        """Actualiza el contador y label verde de estilos seleccionados."""
        if not hasattr(self.app, 'lbl_estilos_count') or not hasattr(self.app, 'estilo_checks'): return
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        sel = self.app.footer.estilos_seleccionados()
        n = len(sel)
        if n == 0:
            self.app.lbl_estilos_count.configure(text=tr("(ninguno)"), text_color=c["muted_text"])
            if hasattr(self.app, 'lbl_estilos_sel'):
                self.app.lbl_estilos_sel.configure(text="")
        else:
            color_count = "#1d4ed8" if is_light else "#5a8aaa"
            self.app.lbl_estilos_count.configure(text=tr('({0} seleccionado{1})').format((n), ('s' if n != 1 else '')),
                                              text_color=color_count)
            if hasattr(self.app, 'lbl_estilos_sel'):
                self.app.lbl_estilos_sel.configure(text=f"✦ {' + '.join(sel)}")

    def _build_tags_tab(self, parent):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        tab_bg = c["panel_bg"]

        # Header con hint y botón Sugerir
        hdr = ctk.CTkFrame(parent, fg_color=tab_bg)
        hdr.pack(fill="x", padx=4, pady=(2, 0))
        ctk.CTkLabel(hdr, text=tr("Clic para añadir al final de la idea"),
                     font=ctk.CTkFont(size=9), fg_color="transparent",
                     text_color=c["muted_text"]).pack(side="left")
        btn_sug_tags = ctk.CTkButton(
            hdr, text=tr("✨ Sugerir"), width=80, height=20,
            font=ctk.CTkFont(size=9),
            fg_color="#1a5a8a", hover_color="#154a72",
            command=self.app.creative.cmd_sugerir_tags,
        )
        btn_sug_tags.pack(side="right", padx=2)
        CTkToolTip(btn_sug_tags, message=tr("LLM analiza tu idea y añade 3-5 tags técnicos apropiados"), delay=0.4)

        scroll = ctk.CTkScrollableFrame(parent, fg_color=tab_bg, scrollbar_button_color=c["combo_border"])
        scroll.pack(fill="both", expand=True, padx=2, pady=(2, 0))

        btn_tag_s = {"height": 20, "corner_radius": 4, "font": ctk.CTkFont(size=9),
                     "fg_color": c.get("fg_dark", "#1e2533"),
                     "hover_color": c.get("combo_border", "#374151"),
                     "text_color": c["panel_text"]}

        for cat_name, tags in TAG_PICKER_CATEGORIES.items():
            ctk.CTkLabel(scroll, text=tr(cat_name),
                         font=ctk.CTkFont(size=9, weight="bold"),
                         fg_color="transparent",
                         text_color=c["muted_text"], anchor="w").pack(
                         fill="x", padx=2, pady=(5, 1))

            COLS = 3
            for i, tag_pair in enumerate(tags):
                label_es, val_en, descripcion = tag_pair
                if i % COLS == 0:
                    row_f = ctk.CTkFrame(scroll, fg_color="transparent")
                    row_f.pack(fill="x", pady=1)

                def _insert_tag(t=val_en):
                    try:
                        current = self.app.txt_idea.get("1.0", "end-1c")
                        sep = ", " if current.strip() else ""
                        self.app.txt_idea.insert("end", sep + t)
                        self.app.txt_idea.see("end")
                    except Exception:
                        pass

                _label_tag = val_en.title() if get_idioma() == "en" else label_es
                btn = ctk.CTkButton(row_f, text=_label_tag, width=120, command=_insert_tag,
                                    **btn_tag_s)
                btn.pack(side="left", padx=2)
                _tip_tag = val_en if get_idioma() == "en" else f"{val_en}\n{descripcion}"
                CTkToolTip(btn, message=_tip_tag, delay=0.4)

    def _build_negative(self, parent):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        tab_bg = c["panel_bg"]

        self.app._frame_neg_header = ctk.CTkFrame(parent, fg_color=tab_bg)
        self.app._frame_neg_header.pack(fill="x", pady=(0, 2))
        hdr = self.app._frame_neg_header  # alias
        ctk.CTkLabel(hdr, text=tr("➕ Negative extra (se añade al base):"),
                     font=ctk.CTkFont(weight="bold", size=12),
                     fg_color="transparent",
                     text_color=c["panel_text"]).pack(side="left")
        ctk.CTkButton(hdr, text=tr("🗑 Limpiar"), width=80, height=24,
                      fg_color="#dc2626" if is_light else "#444",
                      hover_color="#b91c1c" if is_light else "#222",
                      text_color="#ffffff",
                      command=self.app.footer._limpiar_negatives).pack(side="right", padx=4)
        btn_sug_neg = ctk.CTkButton(hdr, text=tr("🛡 Sugerir"), width=80, height=24,
                      fg_color="#1a5a8a", hover_color="#154a72",
                      text_color="#ffffff",
                      command=self.app.creative.cmd_sugerir_negative_tab)
        btn_sug_neg.pack(side="right", padx=2)
        CTkToolTip(btn_sug_neg, message=tr("LLM genera el negative óptimo e inserta en el campo"), delay=0.4)

        # Paquetes predefinidos (activan múltiples presets a la vez)
        frame_paquetes = ctk.CTkFrame(parent, fg_color=tab_bg)
        frame_paquetes.pack(fill="x", pady=(0, 3))
        ctk.CTkLabel(frame_paquetes, text=tr("Paquetes:"),
                     font=ctk.CTkFont(size=9, weight="bold"),
                     fg_color="transparent",
                     text_color=c["muted_text"]).pack(side="left", padx=(2, 4))

        def _aplicar_paquete(nombres_presets):
            for n in nombres_presets:
                if n in self.app.preset_vars:
                    self.app.preset_vars[n].set(True)
                    fg_off = PRESET_COLORES.get(n, ("#333", "#555"))[0]
                    if n in self.app.preset_btns:
                        self.app.preset_btns[n].configure(fg_color="#2ecc71", text=f"✓ {n}")
            self.app.footer._rebuild_negative_text()

        for paq_nombre, paq_presets in NEGATIVE_PAQUETES.items():
            ctk.CTkButton(frame_paquetes, text=tr(paq_nombre), height=22, width=100,
                          fg_color="#1e3a5f", hover_color="#162d49",
                          text_color="#ffffff", font=ctk.CTkFont(size=9),
                          command=lambda p=paq_presets: _aplicar_paquete(p)).pack(
                          side="left", padx=2)

        self.app._frame_neg_presets = ctk.CTkFrame(parent, fg_color=tab_bg)
        self.app._frame_neg_presets.pack(fill="x", pady=(2, 2))

        presets_list = list(NEGATIVE_PRESETS.keys())
        mitad = (len(presets_list) + 1) // 2
        filas = [presets_list[:mitad], presets_list[mitad:]]

        for fila in filas:
            row_f = ctk.CTkFrame(self.app._frame_neg_presets, fg_color="transparent")
            row_f.pack(fill="x", pady=1)
            for nombre_p in fila:
                var = ctk.BooleanVar(value=False)
                self.app.preset_vars[nombre_p] = var
                fg, hv = PRESET_COLORES.get(nombre_p, ("#333", "#555"))

                def _toggle(n=nombre_p, fg_off=fg):
                    self.app.preset_vars[n].set(not self.app.preset_vars[n].get())
                    activo = self.app.preset_vars[n].get()
                    self.app.preset_btns[n].configure(fg_color="#2ecc71" if activo else fg_off, text=f"✓ {tr(n)}" if activo else tr(n))
                    self.app.footer._rebuild_negative_text()

                btn = ctk.CTkButton(row_f, text=tr(nombre_p), height=22, width=90,
                                    fg_color=fg, hover_color=hv, text_color="#ffffff",
                                    font=ctk.CTkFont(size=10), command=_toggle)
                btn.pack(side="left", padx=2)
                self.app.preset_btns[nombre_p] = btn

        self.app.txt_negative = ctk.CTkTextbox(parent, height=36, font=ctk.CTkFont(size=12))
        self.app.txt_negative.pack(fill="x")
        self.app.txt_negative.bind("<KeyRelease>", self.app.footer._validar_negative_length)
        self.app.txt_negative.bind("<FocusOut>", lambda e: self.app.reiniciar_memoria())

        # Warning de límite negative
        self.app.lbl_negative_warning = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=10, weight="bold"),
                                                   fg_color="transparent",
                                                   text_color=c["danger_text"], anchor="w")

        # Spacer al final del tab Negativos (mismo motivo que Ajustes Extra).
        ctk.CTkFrame(parent, fg_color="transparent", height=1).pack(fill="both", expand=True)

    def _toggle(self, n, fg_off):
        """Toggle helper for negative presets."""
        self.app.preset_vars[n].set(not self.app.preset_vars[n].get())
        activo = self.app.preset_vars[n].get()
        self.app.preset_btns[n].configure(fg_color="#2ecc71" if activo else fg_off, text=f"✓ {n}" if activo else n)
        self.app.footer._rebuild_negative_text()

    def _build_imagen_ref(self):
        # Frame placeholder (los widgets reales están dentro de la tab "Ajustes Extra")
        self.app.frame_img_ref = ctk.CTkFrame(self.app, height=1, fg_color="transparent")
        self.app.frame_img_ref.pack_propagate(False)
        # No se renderiza nada aquí — los widgets viven en self.app.frame_imgref_inner
        # dentro de la pestaña "⚙️ Ajustes Extra"
        return

    def _build_entrada(self):
        is_light = _get_real_is_light()
        from config import get_theme_colors
        c = get_theme_colors(is_light)
        self.app.frame_entrada = ctk.CTkFrame(self.app, fg_color="transparent")
        self.app.frame_entrada.pack(pady=(2, 1), padx=16, fill="x")

        # Header con label + botón limpiar
        hdr = ctk.CTkFrame(self.app.frame_entrada, fg_color="transparent")
        hdr.pack(fill="x", padx=2, pady=(0, 2))
        ctk.CTkLabel(hdr, text=tr("Describe tu idea"), font=ctk.CTkFont(size=10), fg_color="transparent", text_color=c["muted_text"]).pack(side="left")
        # Label de autocompletar
        self.app.lbl_autocomplete = ctk.CTkLabel(hdr, text="", font=ctk.CTkFont(size=9, slant="italic"), fg_color="transparent", text_color="#2563eb" if is_light else "#5a8aaa")
        self.app.lbl_autocomplete.pack(side="left", padx=(10, 0))
        # ── MEJORA 1: contador en vivo de chars y tokens estimados ──
        self.app.lbl_idea_counter = ctk.CTkLabel(hdr, text="", font=ctk.CTkFont(size=9), fg_color="transparent", text_color=c["muted_text"])
        self.app.lbl_idea_counter.pack(side="left", padx=(10, 0))
        # ── MEJORA 2: aviso de idioma detectado ──
        self.app.lbl_idioma_aviso = ctk.CTkLabel(hdr, text="", font=ctk.CTkFont(size=9, slant="italic"),
                                              fg_color="transparent",
                                              text_color="#f39c12", cursor="hand2")
        self.app.lbl_idioma_aviso.pack(side="left", padx=(10, 0))
        # Click en el aviso de idioma → toggle auto-trad
        self.app.lbl_idioma_aviso.bind("<Button-1>", lambda e: self._toggle_auto_trad_desde_aviso())
        # ── MEJORA 18 (sesión 18): aviso de palabras polisémicas españolas ──
        # Detecta términos ambiguos (pulso, muñeca, vela, pluma...) que el
        # LLM podría interpretar mal. Click → modal con sugerencias.
        self.app.lbl_claridad_aviso = ctk.CTkLabel(
            hdr, text="", font=ctk.CTkFont(size=9, slant="italic"),
            fg_color="transparent", text_color="#7c3aed", cursor="hand2",
        )
        self.app.lbl_claridad_aviso.pack(side="left", padx=(10, 0))
        self.app.lbl_claridad_aviso.bind(
            "<Button-1>", lambda e: self._mostrar_sugerencias_claridad()
        )
        btn_clear = ctk.CTkButton(hdr, text="🗑", width=22, height=18, fg_color="transparent",
                                    hover_color="#dc2626" if is_light else "#3a1a1a", font=ctk.CTkFont(size=10),
                                    text_color=c["muted_text"],
                                    command=lambda: self.app.txt_idea.delete("1.0", "end"))
        btn_clear.pack(side="right")
        CTkToolTip(btn_clear, delay=0.3, message=tr("Limpiar campo idea"))

        self.app.txt_idea = ctk.CTkTextbox(self.app.frame_entrada, height=90, font=ctk.CTkFont(size=13),
                                        border_width=2, border_color=c["combo_border"] if "combo_border" in c else "#9ca3af", corner_radius=8)
        self.app.txt_idea.pack(fill="x")
        # Tooltip explicando la expansión rápida (;trigger + Espacio)
        try:
            CTkToolTip(
                self.app.txt_idea, delay=0.6,
                message=(
                    tr("💡 Tip: escribe ';trigger' + Espacio para expandir automáticamente.\n"
                    "Ej: ';cine ' → 'cinematic lighting, film grain'.\n"
                    "Configura tus triggers en menú Plantillas → Expansión rápida.")
                ),
            )
        except Exception as _e:
            logger.debug(f"[silent] tooltip txt_idea: {_e}")
        # Bind para autocompletar
        self.app.txt_idea.bind("<KeyRelease>", self._on_idea_keyrelease)
        # Menú contextual click derecho (Cortar/Copiar/Pegar/Seleccionar todo)
        self.app.txt_idea.bind("<Button-3>", self.app.footer._mostrar_menu_contextual_idea)

        # Barra visual de chars
        self.app.chars_bar_frame = ctk.CTkFrame(self.app.frame_entrada, fg_color="#d1d5db" if is_light else "#0a0a14", height=4, corner_radius=2)
        self.app.chars_bar_frame.pack(fill="x", pady=(2, 0))
        self.app.chars_bar = ctk.CTkFrame(self.app.chars_bar_frame, fg_color="#2ecc71", height=4, corner_radius=2)
        self.app.chars_bar.place(x=0, y=0, relwidth=0, relheight=1)

    def _on_idea_keyrelease(self, event=None):
        """Llamado cuando el usuario teclea en el campo idea."""
        # Snippet expansion (Mejora 7): si pulsa Espacio tras ;palabra, expande
        try:
            if event and event.keysym == "space":
                self.app._snippet_expand()
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # Autocompletar
        try:
            self.app.analysis.autocompletar_tags(event)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # Actualizar barra visual de chars
        try:
            self._actualizar_barra_chars()
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    def _actualizar_barra_chars(self):
        """Actualiza la barra de caracteres y el contador de tokens según el texto del campo idea."""
        if not hasattr(self.app, 'chars_bar'): return
        texto = self.app.txt_idea.get("1.0", "end").strip()
        chars = len(texto)
        # Considerar como "max" la mitad del límite del modelo (la idea no es el prompt final)
        specs = self.app.get_current_model_specs()
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
            self.app.chars_bar.configure(fg_color=color)
            self.app.chars_bar.place_configure(relwidth=ratio)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # ── MEJORA 1: actualizar contador numérico ──
        try:
            if chars == 0:
                self.app.lbl_idea_counter.configure(text="")
            else:
                # Estimación tokens ≈ chars / 4 (regla típica para inglés)
                tokens_est = max(1, chars // 4)
                self.app.lbl_idea_counter.configure(
                    text=tr('· {0} chars · ~{1} tokens · max idea {2}').format((chars), (tokens_est), (max_c)),
                    text_color=color
                )
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # ── MEJORA 2: detectar idioma y avisar si auto-trad no concuerda ──
        try:
            self._detectar_idioma_y_avisar(texto)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # ── MEJORA 18: detectar palabras polisémicas y avisar ──
        try:
            self._detectar_claridad_y_avisar(texto)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")

    def _detectar_claridad_y_avisar(self, texto):
        """Detecta palabras españolas polisémicas y muestra chip clickable."""
        try:
            from modules.clarity_hints import detect_ambiguous
            hallazgos = detect_ambiguous(texto)
            if not hallazgos:
                self.app.lbl_claridad_aviso.configure(text="")
                self.app._claridad_hallazgos = []
                return
            # Almacenar para el modal
            self.app._claridad_hallazgos = hallazgos
            # Chip resumen
            n = len(hallazgos)
            palabras = ", ".join(f"'{h['word']}'" for h in hallazgos[:2])
            sufijo = f" y {n-2} más" if n > 2 else ""
            self.app.lbl_claridad_aviso.configure(
                text=tr('💡 Claridad: {0}{1} — click para ver').format((palabras), (sufijo))
            )
        except Exception as _e:
            logger.debug(f"[silent] claridad: {_e}")

    def _mostrar_sugerencias_claridad(self):
        """Modal con las sugerencias de claridad para las palabras detectadas."""
        try:
            hallazgos = getattr(self.app, "_claridad_hallazgos", [])
            if not hallazgos:
                return
            from modules.gprompt_window import GPromptWindow
            is_light = _get_real_is_light()
            from config import get_theme_colors
            c = get_theme_colors(is_light)
            vent = GPromptWindow(self.app)
            vent.title(tr("💡 Sugerencias de claridad"))
            vent.geometry("520x420")
            vent.transient(self.app)
            ctk.CTkLabel(
                vent,
                text=tr("💡 Palabras polisémicas detectadas en tu idea"),
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(pady=(12, 4), padx=12)
            ctk.CTkLabel(
                vent,
                text=(
                    tr("El LLM puede interpretarlas de varias formas. "
                    "Reformula tu idea con la versión específica para "
                    "evitar resultados inesperados.")
                ),
                font=ctk.CTkFont(size=10),
                text_color=c["muted_text"],
                wraplength=480,
                justify="left",
            ).pack(pady=(0, 8), padx=12)
            scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
            scroll.pack(fill="both", expand=True, padx=12, pady=4)
            for h in hallazgos:
                card = ctk.CTkFrame(
                    scroll, fg_color=c["fg_frame"], corner_radius=8,
                )
                card.pack(fill="x", pady=4, padx=2)
                ctk.CTkLabel(
                    card,
                    text=f"🔤 '{h['word']}'",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#7c3aed",
                ).pack(anchor="w", padx=10, pady=(6, 2))
                ctk.CTkLabel(
                    card,
                    text=tr("Interpretaciones posibles: ") + " / ".join(h["meanings"]),
                    font=ctk.CTkFont(size=10),
                    text_color=c["muted_text"],
                    wraplength=460, justify="left",
                ).pack(anchor="w", padx=10, pady=(0, 4))
                ctk.CTkLabel(
                    card,
                    text=h["hint"],
                    font=ctk.CTkFont(size=10, slant="italic"),
                    wraplength=460, justify="left",
                ).pack(anchor="w", padx=10, pady=(0, 8))
            ctk.CTkButton(
                vent, text=tr("Cerrar"), width=120, height=30,
                fg_color="#6b7280", hover_color="#4b5563",
                command=vent.destroy,
            ).pack(pady=10)
        except Exception as _e:
            logger.debug(f"[silent] modal claridad: {_e}")

    def _detectar_idioma_y_avisar(self, texto):
        """Detecta heurísticamente si el texto está en ES o EN y avisa si auto-trad no concuerda."""
        if not hasattr(self.app, 'lbl_idioma_aviso'): return
        if len(texto) < 25:
            self.app.lbl_idioma_aviso.configure(text="")
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
            self.app.lbl_idioma_aviso.configure(text="")
            return
        es_dominante = es_count > en_count * 1.5
        en_dominante = en_count > es_count * 1.5
        # Estado actual del auto-trad
        auto_trad_on = bool(getattr(self.app, "switch_traduccion_var", None) and self.app.switch_traduccion_var.get())
        if en_dominante and auto_trad_on:
            self.app.lbl_idioma_aviso.configure(text=tr("🇬🇧 inglés detectado · click para desactivar Auto-trad"))
        elif es_dominante and not auto_trad_on:
            self.app.lbl_idioma_aviso.configure(text=tr("🇪🇸 español detectado · click para activar Auto-trad"))
        else:
            self.app.lbl_idioma_aviso.configure(text="")

    def _toggle_auto_trad_desde_aviso(self):
        """Cambia el estado de auto-trad cuando el usuario clica en el aviso de idioma."""
        try:
            if hasattr(self.app, "switch_traduccion_var"):
                self.app.switch_traduccion_var.set(not self.app.switch_traduccion_var.get())
                # Refrescar visual del switch
                if hasattr(self.app, "_sw_trad_callback"):
                    try: self.app._sw_trad_callback()
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
                self._actualizar_barra_chars()  # refresca aviso
                estado = "activado" if self.app.switch_traduccion_var.get() else "desactivado"
                self.app.dialogs.set_estado(tr('🌐 Auto-trad {0}').format(estado), "#3498db")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    def _build_acciones(self):
        from config import get_theme_colors
        is_light = ctk.get_appearance_mode().lower() == "light"
        c_theme = get_theme_colors(is_light)
        sep_color = "#d1d5db" if is_light else "#374151"

        outer = ctk.CTkFrame(self.app, fg_color="transparent")
        outer.pack(pady=2, padx=16, fill="x")

        # Fila 1: generación + análisis
        row1 = ctk.CTkFrame(outer, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 3))

        btn_s = {"height": 32, "corner_radius": 6, "font": ctk.CTkFont(size=11)}

        def _sep(parent):
            """Mini separador vertical entre grupos de botones."""
            wrap = ctk.CTkFrame(parent, fg_color="transparent",
                                width=14, height=32)
            wrap.pack(side="left", padx=2)
            wrap.pack_propagate(False)
            line = ctk.CTkFrame(wrap, fg_color=sep_color,
                                width=1, height=22)
            line.place(relx=0.5, rely=0.5, anchor="center")

        # ═══ SISTEMA DE COLORES SEMÁNTICOS ═══
        # 🟢 Verde:   genera output (Ideas, Generar, Quick, Variaciones, Regenerar)
        # 🔵 Azul:    analiza input (Analizar, Img→Prompt, Análisis Inv)
        # 🟣 Morado:  ADN visual (caso único, color propio)
        # 🟣 Violeta: edita el output actual (Refinar, Copiloto)
        # 🟠 Naranja: variantes múltiples del mismo prompt (Iterar, Pulse, Sugerir)
        # 💗 Rosa:    multi-prompt narrativo (Mood, Story, Board, Walk)
        # 🌐 Cyan:    conversiones entre formatos (→Vídeo, Compar modelos)
        # ⚫ Gris:    outputs masivos / utilidades (Batch, Preview)
        VERDE_INSP   = "#2a6a4a"   # Inspiración (variante apagada)
        VERDE_FUERTE = "#1a8a3c"   # Generar principal
        VERDE_SUB    = "#1a5a3c"   # Sub-acciones de Generar (←, →, etc.)
        VERDE_CLARO  = "#2a8a4a"   # Variantes de Generar (Quick, Variaciones)
        AZUL_ANAL    = "#1e3a8a"   # Análisis
        AZUL_ANAL_2  = "#1e3a5f"   # Análisis Inverso (variante)
        MORADO_ADN   = "#7c3aed"   # ADN Visual y edición
        NARANJA_VAR  = "#d97706"   # Variantes naranja
        ROSA_NARR    = "#be185d"   # Multi-prompt narrativo
        CYAN_CONV    = "#0891b2"   # Conversiones
        GRIS_UTIL    = "#475569"   # Utilidades

        # ═══ FILA 1 — grupos con título visible ═══
        # Estructura: (titulo_grupo, color_titulo, [botones])
        grupos_r1 = [
            ("💡 INSPIRACIÓN", VERDE_INSP, [
                ("💡 Ideas",          100, VERDE_INSP,   self.app.cmd_ideas,             "3 ideas creativas · Ctrl+I"),
                ("🎲",                40,  VERDE_INSP,   self.app._cmd_sorprendeme,      "Sorpréndeme con una idea aleatoria"),
            ]),
            ("✨ GENERACIÓN", VERDE_FUERTE, [
                ("✨ Generar",         110, VERDE_FUERTE, self.app.cmd_prompt,            "Genera prompt · Ctrl+Enter"),
                ("🔄",                40,  VERDE_FUERTE, self.app._cmd_regenerar,        "Regenerar con la misma idea (mantiene historial)"),
                ("←",                30,  VERDE_SUB,    self.app._cmd_regenerar_atras,  "← Versión anterior de la regeneración"),
                ("→",                30,  VERDE_SUB,    self.app._cmd_regenerar_adelante,"→ Versión siguiente de la regeneración"),
                ("📊",               36,  VERDE_SUB,    self.app._cmd_diff_versiones,   "Diff visual entre versiones (verde=añadido, rojo=quitado)"),
                ("🔀 Variaciones",    115, VERDE_CLARO,  self.app.cmd_variaciones,       "3 versiones · Ctrl+Shift+Enter"),
                ("🚀 Quick",           80, VERDE_CLARO,  self.app.cmd_prompt_quick,      "Quick Generate: prompt rápido y barato · Alt+Enter"),
            ]),
            ("🔍 ANÁLISIS", AZUL_ANAL, [
                ("👁 Analizar",       100, AZUL_ANAL,    self.app.cmd_vision,            "Describe imagen · Ctrl+Shift+A"),
                ("🎯 Img→Prompt",     110, AZUL_ANAL,    self.app.cmd_imagen_a_prompt,   "Prompt desde imagen"),
                ("🔍 Análisis Inv",   115, AZUL_ANAL_2,  self.app._cmd_analisis_inverso, "Compara imagen con prompt actual"),
            ]),
            ("🧬 ADN", MORADO_ADN, [
                ("🧬 ADN Visual",     100, MORADO_ADN,   self.app.adn.cmd_adn_visual,    "Análisis JSON estructurado"),
            ]),
        ]

        # ═══ FILA 2 — grupos con título visible ═══
        grupos_r2 = [
            ("🔁 EDICIÓN", MORADO_ADN, [
                ("🔁 Refinar",         90, MORADO_ADN,   self.app.refinar.cmd_refinar,    "Mejora el prompt (click der: opciones específicas)"),
                ("💬 Copiloto",        95, MORADO_ADN,   self.app.cmd_copiloto,           "Chat para editar"),
            ]),
            ("🔂 VARIANTES", NARANJA_VAR, [
                ("🔂 Iterar",          80, NARANJA_VAR,  self.app.refinar.cmd_iterar,     "5 variantes cambiando 1 elemento"),
                ("⚡ Pulse",           75, NARANJA_VAR,  self.app._cmd_pulse,             "3 versiones: conservador/equilibrado/creativo"),
                ("🤖 Sugerir",         85, NARANJA_VAR,  self.app._cmd_sugerir_modelo,    "Sugiere el mejor modelo según tu idea"),
            ]),
            ("🎬 NARRATIVA", ROSA_NARR, [
                ("🎭 Mood",            70, ROSA_NARR,    self.app.multi.cmd_moodboard,         "Moodboard: 6 prompts mismo mood, distintos sujetos"),
                ("🎞 Story",           70, ROSA_NARR,    self.app.multi.cmd_story_sequence,    "Story Sequence (solo IMAGEN): 3 shots Wide/Medium/Close"),
                ("🖼 Storyboard",      85, ROSA_NARR,    self.app.multi.cmd_storyboard_imagen, "Storyboard cinematográfico (solo IMAGEN): N paneles. Auto-detecta formato: natural (GPT Image/DALL-E/MJ) o tag-based (SD/Comfy)"),
                ("📽 Board",           70, ROSA_NARR,    self.app.multi.cmd_storyboard_video,  "Storyboard (solo VÍDEO): 4 frames apertura/mid/climax/cierre"),
                ("🌀 Walk",            70, ROSA_NARR,    self.app.multi.cmd_random_walk,       "Random walk: 5 derivaciones evolutivas"),
            ]),
            ("🎬 CONVERSIÓN", CYAN_CONV, [
                ("🎬 →Vídeo",          85, CYAN_CONV,    self.app._cmd_convertir_a_video, "Convierte prompt de imagen a vídeo"),
                ("🆚 Compar",          80, CYAN_CONV,    self.app.ab.cmd_comparar_modelos,  "Compara prompt en 3 modelos"),
            ]),
            ("📦 UTILIDADES", GRIS_UTIL, [
                ("📦 Batch",           80, GRIS_UTIL,    self.app.cmd_batch,              "Generación masiva"),
                ("🎛 Vars",            75, GRIS_UTIL,    self.app.cmd_batch_variables,    "Batch de variables: sustituye {var} con múltiples valores"),
                ("🖼 Preview",         90, GRIS_UTIL,    self.app.cmd_previsualizar,      "Boceto rápido"),
            ]),
        ]

        self.app.action_btns = []

        def _render_grupos(parent, grupos):
            """Render con título visible arriba + botones abajo en cada grupo."""
            for g_idx, item in enumerate(grupos):
                titulo, color_tit, grupo = item
                if g_idx > 0:
                    _sep(parent)
                # Mini-frame vertical por grupo: título + botones
                grp_frame = ctk.CTkFrame(parent, fg_color="transparent")
                grp_frame.pack(side="left", padx=0)
                # Label del título — pequeño, en color del grupo
                ctk.CTkLabel(grp_frame, text=tr(titulo),
                              font=ctk.CTkFont(size=8, weight="bold"),
                              text_color=color_tit, anchor="w").pack(
                              anchor="w", padx=4, pady=(0, 1))
                btn_row = ctk.CTkFrame(grp_frame, fg_color="transparent")
                btn_row.pack(side="top", anchor="w")
                for text, w, fg, cmd, tooltip in grupo:
                    kw = {"fg_color": fg, "hover_color": self.app.dialogs._darker(fg)} if fg else {}
                    btn = ctk.CTkButton(btn_row, text=tr(text), width=w,
                                        command=cmd, **btn_s, **kw)
                    btn.pack(side="left", padx=2)
                    CTkToolTip(btn, delay=0.5, message=tr(tooltip))
                    self.app.action_btns.append(btn)
                    if text == "🔁 Refinar":
                        btn.bind("<Button-3>", self.app.refinar.menu_refinar_especifico)
                    elif text == "🎞 Story":
                        self.app.btn_story = btn
                    elif text == "📽 Board":
                        self.app.btn_board = btn

        _render_grupos(row1, grupos_r1)

        # ═══ BADGE DE COSTE (al final de fila 1) ═══
        self.app.lbl_coste = ctk.CTkLabel(row1, text="", font=ctk.CTkFont(size=10, weight="bold"),
                                       text_color="#22c55e", fg_color="transparent")
        self.app.lbl_coste.pack(side="left", padx=(4, 0))

        # Índices reales tras añadir Quick a fila 1:
        # [0]💡 Ideas, [1]🎲, [2]✨ Generar, [3]🔄, [4]←, [5]→, [6]📊,
        # [7]🔀 Variaciones, [8]🚀 Quick, [9]👁 Analizar, [10]🎯 Img→Prompt,
        # [11]🔍 Análisis Inv, [12]🧬 ADN Visual
        self.app.btn_vision = self.app.action_btns[9]
        self.app.btn_img_prompt = self.app.action_btns[10]

        # Registrar callback para actualizar coste cuando cambie la idea
        self.app.txt_idea.bind("<<Modified>>", self.app.footer._actualizar_coste_estimado)

        row2 = ctk.CTkFrame(outer, fg_color="transparent")
        row2.pack(fill="x")
        _render_grupos(row2, grupos_r2)

        btn_reset = ctk.CTkButton(row2, text=tr("🗑 Reset"), width=80, height=32, corner_radius=6,
                                   fg_color="#7f1d1d", hover_color="#5a1414",
                                   font=ctk.CTkFont(size=11), command=self.app.cmd_reset)
        btn_reset.pack(side="right", padx=2)
        CTkToolTip(btn_reset, delay=0.5, message=tr("Limpia todo y borra la memoria."))

        btn_repeat = ctk.CTkButton(row2, text=tr("🔁 Última"), width=85, height=32, corner_radius=6,
                                       fg_color="#1e3a5f", hover_color="#162d49",
                                       font=ctk.CTkFont(size=10), command=self.app._repetir_ultima_config)
        btn_repeat.pack(side="right", padx=2)
        CTkToolTip(btn_repeat, delay=0.5, message=tr("Repetir configuración del último prompt generado"))

        # ── MEJORA 8: Guardar/Cargar setup (configuración sin idea ni prompt) ──
        btn_load_setup = ctk.CTkButton(row2, text=tr("📋 Cargar setup"), width=110, height=32, corner_radius=6,
                                        fg_color="#1e5f3a", hover_color="#16492d",
                                        font=ctk.CTkFont(size=10), command=self.app._cmd_cargar_setup)
        btn_load_setup.pack(side="right", padx=2)
        CTkToolTip(btn_load_setup, delay=0.5, message=tr("Cargar una configuración guardada (modelo, ratio, estilos…)"))

        btn_save_setup = ctk.CTkButton(row2, text=tr("💾 Setup"), width=85, height=32, corner_radius=6,
                                        fg_color="#1e5f3a", hover_color="#16492d",
                                        font=ctk.CTkFont(size=10), command=self.app._cmd_guardar_setup)
        btn_save_setup.pack(side="right", padx=2)
        CTkToolTip(btn_save_setup, delay=0.5,
                   message=tr("Guarda la configuración actual (modelo, plataforma, ratio, estilos, negatives, personaje, LoRA, destino) sin idea ni prompt"))

        self.app.frame_ideas = ctk.CTkFrame(self.app, fg_color="transparent")

    def _build_estado(self):
        is_light = _get_real_is_light()
        from config import get_theme_colors
        c = get_theme_colors(is_light)
        self.app.frame_estado = ctk.CTkFrame(self.app, fg_color="transparent")
        self.app.frame_estado.pack(pady=(1, 0), fill="x", padx=16)

        self.app.lbl_estado = ctk.CTkLabel(
            self.app.frame_estado,
            text=tr('Listo · Ctrl+Enter: Prompt · Ctrl+1/2: Copiar'),
            font=ctk.CTkFont(size=10), fg_color="transparent", text_color=c["muted_text"])
        self.app.lbl_estado.pack(side="left", fill="x", expand=True)

        self.app.progress = ctk.CTkProgressBar(self.app.frame_estado, width=160, height=10,
                                                   mode="indeterminate", progress_color="#3498db")

    def _build_salida(self):
        is_light = _get_real_is_light()
        from config import get_theme_colors
        c = get_theme_colors(is_light)
        frame = ctk.CTkFrame(self.app, fg_color="transparent")
        frame.pack(pady=2, padx=16, fill="both", expand=True)
        hdr = ctk.CTkFrame(frame, fg_color="transparent")
        hdr.pack(fill="x", padx=2, pady=(0, 2))
        ctk.CTkLabel(hdr, text=tr("Resultado"), font=ctk.CTkFont(size=10), fg_color="transparent", text_color=c["muted_text"]).pack(side="left")
        ctk.CTkLabel(hdr, text=tr("editable"), font=ctk.CTkFont(size=9), fg_color="transparent", text_color=c["panel_label"]).pack(side="left", padx=4)

        # ── Validador Flux/SD3.5: aviso ARRIBA del textbox con fondo destacado ──
        # (Va antes del textbox para no quedar tapado por la barra de botones inferior)
        self.app.lbl_flux_warning = ctk.CTkLabel(frame, text="",
                                              font=ctk.CTkFont(size=11, weight="bold"),
                                              text_color="#1a1a1a",
                                              fg_color="#f39c12",
                                              corner_radius=6,
                                              anchor="w", justify="left",
                                              height=24)
        # No se hace pack inicialmente — se mostrará/ocultará dinámicamente

        # height=240 da una altura mínima decente al "Resultado editable"
        # cuando se carga la app. expand=True le da TODO el sobrante vertical
        # de la ventana, pero el mínimo evita que se quede minúsculo si la
        # zona superior (tabview, descripción del modelo) crece.
        # border + corner_radius para que tenga el mismo marco que txt_idea
        # (especialmente visible en modo light).
        border_col = c["combo_border"] if "combo_border" in c else "#9ca3af"
        self.app.txt_salida = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Consolas", size=12),
                                          wrap="word", height=240,
                                          border_width=2, border_color=border_col,
                                          corner_radius=8)
        self.app.txt_salida.pack(fill="both", expand=True)
        # F3 — Undo/Redo nativo de Tk en el editor de salida.
        # CTkTextbox envuelve un tk.Text interno (_textbox) que sí soporta
        # undo/redo. Activamos undo + bindings explícitos por compatibilidad
        # (Ctrl+Z, Ctrl+Y y Ctrl+Shift+Z para redo).
        try:
            self.app.txt_salida._textbox.configure(undo=True, autoseparators=True, maxundo=-1)
            def _undo(_e=None):
                try: self.app.txt_salida._textbox.edit_undo()
                except Exception: pass
                return "break"
            def _redo(_e=None):
                try: self.app.txt_salida._textbox.edit_redo()
                except Exception: pass
                return "break"
            for seq in ("<Control-z>", "<Control-Z>"):
                self.app.txt_salida.bind(seq, _undo)
            for seq in ("<Control-y>", "<Control-Y>",
                        "<Control-Shift-z>", "<Control-Shift-Z>"):
                self.app.txt_salida.bind(seq, _redo)
        except Exception as _e:
            pass
        self.app.txt_salida.bind("<KeyRelease>", self.app.dialogs._on_salida_editada)
        self.app.txt_salida.bind("<Double-Button-1>", self.app.dialogs._on_doble_click_salida)
        self.app.txt_salida.bind("<Button-3>", self.app.footer._mostrar_menu_contextual)

        # ── MEJORA 9 (inline): franja de compatibilidad rápida con plataformas top ──
        self.app.lbl_compat_inline = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(family="Consolas", size=9),
                                               fg_color="transparent",
                                               text_color=c["muted_text"], anchor="w", justify="left",
                                               cursor="hand2")
        self.app.lbl_compat_inline.pack(fill="x", pady=(2, 0))
        self.app.lbl_compat_inline.bind("<Button-1>", lambda e: self.app.analysis.cmd_modal_compatibilidad())
