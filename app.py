"""G-Prompt Studio — Aplicación principal.

Generador de prompts para creadores de imágenes con IA.
Las ventanas secundarias usan GPromptWindow (modules.gprompt_window).
"""
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import customtkinter as ctk

from modules.i18n import tr

logger = logging.getLogger(__name__)

from tkinter import messagebox

import pyperclip

from modules.gprompt_window import GPromptWindow
from modules.preview_pollinations import PreviewPollinationsService

# Importación segura de Tooltips
try:
    from CTkToolTip import CTkToolTip
except ImportError:
    class CTkToolTip:
        def __init__(self, *args, **kwargs): pass

from api_clients import APIClients
from config import (
    APP_TITLE,
    get_theme_colors,
)
from modules import (
    CoreMixin,
    EventBus,
    install_components,
)
from persistence import DataStore
from workers import (
    DeepSeekWorker,
    VisionChain,
)

# Inicializar EventBus singleton
bus = EventBus()


class ArquitectoApp(
    ctk.CTk,
    # UIBuildersMixin removido (A1 fase 2, sesión 14) → self.ui.* (UIBuildersService)
    # ToolsCreativeMixin removido (A1 fase 2, sesión 14) → self.creative.* (ToolsCreativeService)
    # ToolsWorkflowMixin removido (A1 fase 2, sesión 14) → self.workflow.* (ToolsWorkflowService)
    # DataMgmtMixin removido (A1 fase 2, sesión 14) → self.data.* (DataMgmtService)
    # BackupExportMixin removido (A1 fase 2, sesión 14) → self.backup.* (BackupExportService)
    # DialogsMixin removido (A1 fase 2, sesión 14) → self.dialogs.* (DialogsService)
    # CoreMixin: FOUNDATION definitiva (sesión 17). Permanece en el MRO
    # por diseño — A1 fase 2 cerrado con 1 mixin foundation. Ver docstring
    # de modules/core.py para razones técnicas.
    CoreMixin,
    # AdnVisualMixin removido (A1 fase 2, sesión 14) → self.adn.* (AdnVisualService)
    # MultiPromptMixin removido (A1 fase 2, sesión 14) → self.multi.* (MultiPromptService)
    # SesionVideoMixin removido (A1 fase 2, sesión 14) → self.sesion.* (SesionVideoService)
    # WorkersIaMixin removido (A1 fase 2, sesión 14) → self.workers.* (WorkersIaService)
    # ModoClienteMixin removido (A1 fase 2, sesión 14) → self.cliente.* (ModoClienteService)
    # JsonPromptMixin removido del MRO (A1 fase 2): ahora es JsonPromptService
    # accesible via self.json.cmd_importar() / self.json.cmd_exportar()
    # PromptsInyeccionMixin removido (A1 fase 2): ahora PromptsInyeccionService
    # accesible via self.prompts.inyectar_specs_modelo() / .construir_modelo_info()
    # AbTestingMixin removido (A1 fase 2, sesión 14) → self.ab.* (AbTestingService)
    # AtajosAyudaMixin removido (A1 fase 2) → self.atajos.* (AtajosAyudaService)
    # UiEventsMixin removido (A1 fase 2, sesión 14) → self.events.* (UiEventsService)
    # RefinamientoMixin removido (A1 fase 2, sesión 14) → self.refinar.* (RefinamientoService)
    # DashboardMixin removido (A1 fase 2, sesión 11) → self.dashboard.cmd_abrir()
    # (DashboardService)
    # UiFooterMixin removido (A1 fase 2, sesión 14) → self.footer.* (UiFooterService)
):

    # Mapa nombre-de-método → componente que lo expone. Se usa en
    # __getattr__ como fallback para resolver call sites legacy del tipo
    # `self.app._método` que sobrevivieron a la migración A1 fase 2.
    # NO incluye el "_" inicial — la búsqueda lo añade automáticamente.
    _LEGACY_SERVICE_ATTR = (
        "dialogs", "footer", "ui", "events", "data", "sesion", "creative",
        "workflow", "analysis", "backup", "atajos", "multi", "adn",
        "cliente", "ab", "json", "refinar", "workers", "prompts",
        "dashboard",
    )

    def __getattr__(self, name):
        """Fallback: busca el atributo en los services registrados.

        Resuelve call sites legacy `self.app._método()` que tras la
        migración A1 fase 2 (sesión 14) ya no existen como métodos
        directos del app porque los mixins se removieron del MRO.

        Solo se llama si el atributo NO se encontró por la vía normal
        (atributo de instancia, atributo de clase, herencia). Si tampoco
        está en ningún service, delegamos a tkinter (comportamiento
        original de CTk).
        """
        if name.startswith("__") or name == "_LEGACY_SERVICE_ATTR":
            raise AttributeError(name)
        for comp_attr in type(self)._LEGACY_SERVICE_ATTR:
            comp = self.__dict__.get(comp_attr)
            if comp is None:
                continue
            # Buscar en el _service interno del componente (donde viven
            # los métodos reales con underscore)
            service = getattr(comp, "_service", None)
            if service is not None and hasattr(service, name):
                return getattr(service, name)
            # Si el componente no tiene service (solo delegación
            # __getattr__), no probamos más para evitar recursión.
        # Fallback al comportamiento original de tkinter
        try:
            tk = self.__dict__.get("tk")
            if tk is not None:
                return getattr(tk, name)
        except AttributeError:
            pass
        raise AttributeError(
            f"{type(self).__name__!r} object has no attribute {name!r}"
        )

    def __init__(self):
        super().__init__()
        self._setup_services()
        if not self._setup_api_clients():
            return
        self._setup_state()
        self._setup_window()
        self._setup_tk_vars()
        self._build_ui()
        self._setup_post_init()

    # ── Fases de inicialización ───────────────────────────────────────

    def _setup_services(self):
        """Locks de Pollinations, preview service y componentes instalados."""
        self._pollinations_lock = threading.Lock()
        self._pollinations_queue_lock = threading.Lock()
        self._pollinations_queue_size = 0
        self.preview = PreviewPollinationsService(self)
        install_components(self)
        try:
            self.withdraw()
            self._splash = self._crear_splash()
        except Exception:
            self._splash = None
        def _silenciar_errores_tooltip(exc, val, tb):
            msg = str(val)
            if "bad window path" in msg or "ctktooltip" in msg.lower():
                return
            import traceback
            traceback.print_exception(exc, val, tb)
        self.report_callback_exception = _silenciar_errores_tooltip

    def _setup_api_clients(self) -> bool:
        """APIClients con wizard de fallback, DataStore, workers y executor.
        Devuelve False si la inicialización debe abortar.
        """
        self._splash_estado("Inicializando proveedores...")
        self.clients = APIClients()
        if self.clients.error:
            self._cerrar_splash()
            if not self._setup_wizard():
                self.destroy()
                return False
            self.clients = APIClients()
            if self.clients.error:
                messagebox.showerror(tr("Error de configuración"), self.clients.error)
                self.destroy()
                return False
        self._splash_estado("Cargando datos...")
        self.store    = DataStore()
        self.deepseek = DeepSeekWorker(self.clients)
        self.vision   = VisionChain(self.clients)
        self._executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="gprompt")
        return True

    def _setup_state(self):
        """Variables de estado interno de la aplicación."""
        self.imagen_cargada         = None
        self._progreso_activo       = False
        self._token_pending         = None
        self._ultimo_anclaje_visual = None
        try:
            _prefs = self.store.cargar_preferencias() or {}
            self._anclaje_visual = _prefs.get("anclaje_visual") or None
        except Exception as _e:
            logger.debug(f"[silent] cargar anclaje: {_e}")
            self._anclaje_visual = None

    def _setup_window(self):
        """Título y geometría de la ventana principal."""
        self.title(APP_TITLE)
        self._aplicar_geometria_adaptativa()
        self.minsize(820, 620)
        self._splash_estado("Construyendo interfaz...")

    def _setup_tk_vars(self):
        """Variables Tk con sus valores iniciales y traces de persistencia."""
        try:
            _prefs = self.store.cargar_preferencias() or {}
        except Exception as _e:
            logger.debug(f"[silent] cargar switches prefs: {_e}")
            _prefs = {}

        # Idioma de la UI: fijarlo ANTES de construir la interfaz para que tr()
        # devuelva el idioma correcto durante el build. El cambio se aplica al
        # reiniciar (ver modules/i18n.py y dialogs.cmd_toggle_idioma).
        try:
            from modules.i18n import idioma_inicial, set_idioma
            # 1er arranque (sin pref): detecta el idioma del SO; si ya hay pref, la usa.
            self._idioma_inicial = idioma_inicial(_prefs.get("idioma"))
            set_idioma(self._idioma_inicial)
        except Exception as _e:
            self._idioma_inicial = _prefs.get("idioma") or "es"
            logger.debug(f"[silent] set_idioma: {_e}")

        self.llm_var               = ctk.StringVar(value="DeepSeek V4")
        self.modo_var              = ctk.StringVar(value="imagen")
        self.plataforma_var        = ctk.StringVar(value="SeaArt / Tensor.Art")
        self.switch_nsfw_var       = ctk.BooleanVar(value=_prefs.get("switch_nsfw", False))
        self.duracion_var          = ctk.StringVar(value="10s")
        self.shots_var             = ctk.StringVar(value="Auto")
        self.ratio_var             = ctk.StringVar(value="1:1")
        # Auto-translate (idea → inglés): por defecto ON en español, OFF si la UI
        # está en inglés (el usuario angloparlante ya escribe en inglés). La pref
        # guardada manda si existe.
        self.switch_traduccion_var = ctk.BooleanVar(
            value=_prefs.get("switch_traduccion", getattr(self, "_idioma_inicial", "es") != "en"))
        self.destino_var           = ctk.StringVar(value="— Personal —")
        self.brief_var             = ctk.BooleanVar(value=_prefs.get("brief", False))
        self.switch_ref_visual_var = ctk.BooleanVar(value=_prefs.get("switch_ref_visual", False))
        self.lora_inicio_var       = ctk.BooleanVar(value=_prefs.get("lora_inicio", True))
        _estilo_inicial = (
            _prefs.get("familia_estilo") or _prefs.get("z_image_estilo") or "Auto"
        )
        self.familia_estilo_var    = ctk.StringVar(value=_estilo_inicial)
        self.estilo_video_var      = ctk.StringVar(value=_prefs.get("estilo_video") or "Auto")
        self.idioma_var            = ctk.StringVar(value=getattr(self, "_idioma_inicial", _prefs.get("idioma") or "es"))
        try:
            _multi_loras = _prefs.get("loras_multi", [])
            if not isinstance(_multi_loras, list):
                _multi_loras = []
        except Exception:
            _multi_loras = []
        self.loras_multi: list = list(_multi_loras)
        self.estilo_checks  = {}
        self.preset_vars    = {}
        self.preset_btns    = {}
        self._bind_switch_persistence()
        self._bind_switch_sesion_traces()

    def _bind_switch_persistence(self):
        """Traces que persisten el estado de los switches en preferences.json."""
        def _persistir(key, getter):
            def _trace(*_a):
                try:
                    p = self.store.cargar_preferencias() or {}
                    p[key] = getter()
                    self.store.guardar_preferencias(p)
                except Exception as _e:
                    logger.debug(f"[silent] persistir {key}: {_e}")
            return _trace
        try:
            self.switch_nsfw_var.trace_add(
                "write", _persistir("switch_nsfw", self.switch_nsfw_var.get))
            self.switch_traduccion_var.trace_add(
                "write", _persistir("switch_traduccion", self.switch_traduccion_var.get))
            self.brief_var.trace_add(
                "write", _persistir("brief", self.brief_var.get))
            self.switch_ref_visual_var.trace_add(
                "write", _persistir("switch_ref_visual", self.switch_ref_visual_var.get))
            self.lora_inicio_var.trace_add(
                "write", _persistir("lora_inicio", self.lora_inicio_var.get))
            self.familia_estilo_var.trace_add(
                "write", _persistir("familia_estilo", self.familia_estilo_var.get))
            self.estilo_video_var.trace_add(
                "write", _persistir("estilo_video", self.estilo_video_var.get))
            self.idioma_var.trace_add(
                "write", _persistir("idioma", self.idioma_var.get))
        except Exception as _e:
            logger.debug(f"[silent] trace switches: {_e}")

    def _bind_switch_sesion_traces(self):
        """Traces que registran cambios de ratio/destino/switches en la sesión grabada."""
        try:
            self.ratio_var.trace_add("write", lambda *a: self.sesion._sesion_log(f"📐 Cambió ratio → {self.ratio_var.get()}") if hasattr(self, "_sesion_eventos") else None)
            self.destino_var.trace_add("write", lambda *a: self.sesion._sesion_log(f"🎯 Cambió destino → {self.destino_var.get()}") if hasattr(self, "_sesion_eventos") else None)
            self.switch_nsfw_var.trace_add("write", lambda *a: self.sesion._sesion_log(f"🔞 NSFW → {'ON' if self.switch_nsfw_var.get() else 'OFF'}") if hasattr(self, "_sesion_eventos") else None)
            self.switch_traduccion_var.trace_add("write", lambda *a: self.sesion._sesion_log(f"🌐 Auto-trad → {'ON' if self.switch_traduccion_var.get() else 'OFF'}") if hasattr(self, "_sesion_eventos") else None)
            self.brief_var.trace_add("write", lambda *a: self.sesion._sesion_log(f"📋 Modo Brief → {'ON' if self.brief_var.get() else 'OFF'}") if hasattr(self, "_sesion_eventos") else None)
            self.switch_ref_visual_var.trace_add("write", lambda *a: self.sesion._sesion_log(f"🖼 Ref visual → {'ON' if self.switch_ref_visual_var.get() else 'OFF'}") if hasattr(self, "_sesion_eventos") else None)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")

    def _build_ui(self):
        """Construye todos los widgets de la interfaz en orden."""
        self.dialogs._build_author()
        self.footer._build_footer()
        self.ui._build_header()
        self.ui._build_modo()
        self.ui._build_video_panel()
        self.ui._build_audio_panel()
        self.ui._build_modelo_imagen_panel()
        self.ui._build_destino_panel()
        self.lbl_img_model_info = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=10), text_color="#3498db",
            corner_radius=6, wraplength=1800, justify="left", anchor="w")
        self.ui._build_tabs_centrales()
        self.ui._build_imagen_ref()
        self.ui._build_entrada()
        self.ui._build_acciones()
        self.ui._build_estado()
        self.ui._build_salida()
        self.atajos.bind_shortcuts()

    def _setup_post_init(self):
        """Datos iniciales, preferencias, atajos, timers y cierre del splash."""
        self.data.actualizar_combo_personajes()
        self.data.actualizar_combo_loras()
        self.data.actualizar_combo_plantillas()
        try:
            self.footer.actualizar_fuentes_activas()
        except Exception as _e:
            logger.debug(f"[silent fuentes init] {_e}")
        self.data._cargar_preferencias()
        self.events._on_modo_cambio()
        self.reiniciar_memoria()
        try:
            self._apply_theme_colors()
        except Exception as e:
            logger.warning(f"_apply_theme_colors inicial falló: {e}")
        self.data._restaurar_borrador()
        self.after(30000, self.data._auto_guardar_borrador)
        self.after(5000, self._backup_semanal_check)
        try:
            self.bind_all("<Control-Return>", self._atajo_generar_prompt, add="+")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        try:
            self.bind("<F11>", self._toggle_fullscreen_principal)
            self.bind("<Escape>", self._exit_fullscreen_principal)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        self.after(800, self._actualizar_indicador_proveedor)
        self.after(900, self._actualizar_indicador_adn)
        self.protocol("WM_DELETE_WINDOW", self.dialogs._on_cerrar)
        try:
            self._splash_estado(tr("¡Listo!"))
            self.after(150, self._cerrar_splash)
            self.after(180, self.deiconify)
            self.after(220, lambda: self.lift())
            self.after(250, lambda: self.focus_force())
            self.after(300, lambda: self.txt_idea.focus_set() if hasattr(self, "txt_idea") else None)
        except Exception:
            try:
                self.deiconify()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        self.after(900, self._marcar_init_completo)
        # Auto-discovery ComfyUI en hilo de fondo: el rglob recursivo sobre
        # models/ puede tardar segundos con carpetas grandes y antes corría
        # en el import de config.py (frenaba el arranque). Al terminar,
        # repoblar el combo de modelos en el hilo Tk.
        self.after(400, self._lanzar_autodiscovery_comfy)
        try:
            prefs = self.store.cargar_preferencias() or {}
            if not prefs.get("nombre"):
                self.after(1200, self._wizard_nombre)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")

    def _lanzar_autodiscovery_comfy(self):
        """Escanea ComfyUI en un hilo y refresca los combos si halló modelos."""
        import threading

        def _worker():
            try:
                from config import aplicar_autodiscovery_comfy
                total = aplicar_autodiscovery_comfy()
                if total > 0:
                    # Repoblar combos en el hilo de Tk (los dicts por
                    # plataforma comparten las listas mutadas in place).
                    self.after(0, self.events._on_plataforma_cambio)
            except Exception as e:
                logger.debug(f"[silent] autodiscovery comfy: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _marcar_init_completo(self):
        """Activa el flag _gprompt_init_done en sys.modules (post-init)."""
        try:
            import sys
            for mod_name in ('app', '__main__'):
                mod = sys.modules.get(mod_name)
                if mod is not None:
                    setattr(mod, '_gprompt_init_done', True)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    def _wizard_nombre(self):
        """Mini-wizard que pregunta el nombre del usuario para personalizar saludos.
        Solo se muestra si no hay nombre guardado en preferences.json.
        """
        try:
            prefs = self.store.cargar_preferencias() or {}
            if prefs.get("nombre"):
                return  # Ya tiene nombre, no molestar
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        try:
            is_lt = ctk.get_appearance_mode().lower() == "light"
            from config import get_theme_colors
            c = get_theme_colors(is_lt)
        except Exception:
            c = {"muted_text": "#888", "panel_text": "#e5e7eb", "panel_bg": "#0a0e14"}

        win = GPromptWindow(self)
        win.title(tr("👋 Bienvenida"))
        win.geometry("440x230")
        win.transient(self)
        try: win.grab_set()
        except Exception as e:
            logger.debug(f"[silent] {e}")

        ctk.CTkLabel(win, text=tr("👋 ¡Hola!"),
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(win, text=tr("¿Cómo quieres que te llamemos?"),
                     font=ctk.CTkFont(size=12),
                     text_color=c.get("muted_text")).pack(pady=(0, 4))
        ctk.CTkLabel(win, text=tr("Aparecerá en el saludo del Dashboard."),
                     font=ctk.CTkFont(size=10),
                     text_color=c.get("muted_text")).pack(pady=(0, 12))

        entry = ctk.CTkEntry(win, width=300, height=34,
                              placeholder_text=tr("Tu nombre o apodo"),
                              font=ctk.CTkFont(size=12))
        entry.pack(pady=4)
        entry.focus_set()

        def _guardar(_evt=None):
            nombre = entry.get().strip()
            try:
                prefs = self.store.cargar_preferencias() or {}
                if nombre:
                    prefs["nombre"] = nombre
                else:
                    # Si lo deja vacío, marcar como "skip" para no preguntar más
                    prefs["nombre"] = "Creador"
                self.store.guardar_preferencias(prefs)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            win.destroy()

        entry.bind("<Return>", _guardar)

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=14)
        ctk.CTkButton(btn_frame, text=tr("✅ Guardar"), width=130, height=32,
                      fg_color="#2ecc71", hover_color="#27ae60",
                      command=_guardar).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text=tr("Saltar"), width=80, height=32,
                      fg_color="#6b7280", hover_color="#4b5563",
                      command=_guardar).pack(side="left", padx=4)


    def _crear_splash(self):
        """Crea splash screen como Toplevel SIN parent root temporal."""
        try:
            splash = GPromptWindow(self)
            splash.overrideredirect(True)  # Sin barra de título
            splash.attributes("-topmost", True)

            # Tamaño y centrado
            w, h = 380, 200
            screen_w = splash.winfo_screenwidth()
            screen_h = splash.winfo_screenheight()
            x = (screen_w - w) // 2
            y = (screen_h - h) // 2
            splash.geometry(f"{w}x{h}+{x}+{y}")
            splash.configure(fg_color="#0d1117")

            # Borde sutil
            frame = ctk.CTkFrame(splash, fg_color="#1a1f2e",
                                 border_color="#2563eb", border_width=2,
                                 corner_radius=12)
            frame.pack(fill="both", expand=True, padx=2, pady=2)

            # Logo
            ctk.CTkLabel(frame, text="🧠",
                         font=ctk.CTkFont(size=48)).pack(pady=(20, 0))

            # Título
            ctk.CTkLabel(frame, text=tr("G-Prompt Studio"),
                         font=ctk.CTkFont(size=20, weight="bold"),
                         text_color="#e5e7eb").pack()

            # Versión
            from config import PUBLIC_VERSION
            ctk.CTkLabel(frame, text=tr('v{0}').format(PUBLIC_VERSION),
                         font=ctk.CTkFont(size=11),
                         text_color="#3b82f6").pack()

            # Estado
            splash._lbl_estado = ctk.CTkLabel(
                frame, text=tr("Iniciando..."),
                font=ctk.CTkFont(size=10),
                text_color="#9ca3af"
            )
            splash._lbl_estado.pack(pady=(10, 0))

            # Progress bar indeterminada
            splash._pb = ctk.CTkProgressBar(frame, width=240, height=6,
                                              mode="indeterminate")
            splash._pb.pack(pady=(8, 0))
            splash._pb.start()

            splash.update()
            return splash
        except Exception:
            return None

    def _splash_estado(self, txt: str):
        """Actualiza el texto del splash si existe."""
        try:
            if self._splash and self._splash.winfo_exists():
                self._splash._lbl_estado.configure(text=txt)
                self._splash.update()
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    def _cerrar_splash(self):
        """Cierra el splash screen."""
        try:
            if self._splash and self._splash.winfo_exists():
                try:
                    self._splash._pb.stop()
                except Exception as _e:
                    logger.debug(f"[silent] {_e}")
                self._splash.destroy()
                self._splash = None
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    # NEW v1.0 — Helpers para ventanas hijas, toasts, atajos

    def _aplicar_geometria_adaptativa(self):
        """Calcula tamaño y posición inicial según el monitor.

        - En monitores pequeños (1366x768): la app ocupa ~95% del ancho
          y ~92% del alto disponible (margen para taskbar).
        - En monitores normales (1920x1080): ~70% × ~85%.
        - En monitores 4K (3840x2160): cap a 1600×1200 para que no
          se vea ridículamente grande.
        - Centra la ventana en la pantalla.
        """
        try:
            # Tamaño bruto del monitor PRIMARIO
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()

            # Restar barra de tareas estimada (Windows: ~40px abajo)
            usable_h = max(screen_h - 60, 600)

            # Tamaño objetivo según resolución
            if screen_w <= 1400:           # HD pequeñas (1366x768, 1280x720)
                w = int(screen_w * 0.95)
                h = int(usable_h * 0.92)
            elif screen_w <= 1920:         # Full HD estándar
                w = int(screen_w * 0.72)
                h = int(usable_h * 0.88)
            elif screen_w <= 2560:         # QHD / 2K
                w = int(screen_w * 0.62)
                h = int(usable_h * 0.82)
            else:                          # 4K+
                w = min(int(screen_w * 0.50), 1600)
                h = min(int(usable_h * 0.78), 1200)

            # Clamp para garantizar mínimos sensatos
            w = max(820, w)
            h = max(620, h)

            # Centrar en la pantalla
            x = max(0, (screen_w - w) // 2)
            y = max(0, (usable_h - h) // 2)

            self.geometry(f"{w}x{h}+{x}+{y}")

            # Log informativo (útil para soporte)
            try:
                import logging as _log
                _log.getLogger(__name__).info(
                    f"Ventana adaptada: {w}x{h} en pantalla {screen_w}x{screen_h}"
                )
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        except Exception as e:
            # Fallback a tamaño tradicional si algo falla
            try:
                import logging as _log
                _log.getLogger(__name__).warning(f"Geometría adaptativa falló: {e}")
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            self.geometry("1060x900")

    def open_child_window(self, title: str = "", size: str = "800x600",
                          transient: bool = True, modal: bool = False) -> GPromptWindow:
        """
        Crea una GPromptWindow correctamente configurada:
        - Título y tamaño
        - Transient(self) si transient=True (no-op en GPromptWindow para
          preservar minimize/maximize en Windows; sí lift+focus)
        - grab_set() si modal=True (bloquea la principal)
        - Garantiza que aparece AL FRENTE (gracias a GPromptWindow)
        - F11 = toggle pantalla completa, Escape = salir de fullscreen

        Use:
            v = self.open_child_window("Mi ventana", "600x400")
            ctk.CTkLabel(v, text=tr("hola")).pack()
        """
        v = GPromptWindow(self)
        if title:
            v.title(title)
        if size:
            v.geometry(size)
        if transient:
            v.transient(self)
        if modal:
            try:
                v.grab_set()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        def _toggle_fullscreen(event=None):
            try:
                actual = bool(v.attributes("-fullscreen"))
                v.attributes("-fullscreen", not actual)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            return "break"

        def _exit_fullscreen(event=None):
            try:
                if bool(v.attributes("-fullscreen")):
                    v.attributes("-fullscreen", False)
                    return "break"
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        try:
            v.bind("<F11>", _toggle_fullscreen)
            v.bind("<Escape>", _exit_fullscreen)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # El patch global ya hace lift+focus, pero lo reforzamos
        try:
            v.after(80, lambda: v.lift() if v.winfo_exists() else None)
            v.after(120, lambda: v.focus_force() if v.winfo_exists() else None)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        return v

    def show_toast(self, mensaje: str, color: str = "#2563eb", duracion_ms: int = 2500):
        """Toast in-app no bloqueante (esquina inferior derecha)."""
        try:
            # Cerrar toast previo si existe
            prev = getattr(self, "_toast_actual", None)
            if prev:
                try:
                    prev.destroy()
                except Exception as _e:
                    logger.debug(f"[silent] {_e}")
            toast = GPromptWindow(self)
            toast.overrideredirect(True)
            toast.attributes("-topmost", True)
            toast.configure(fg_color=color)

            ctk.CTkLabel(
                toast, text=mensaje, font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#ffffff", padx=14, pady=8
            ).pack()
            toast.update_idletasks()

            # Posicionar abajo-derecha de la ventana principal
            try:
                tw, th = toast.winfo_width(), toast.winfo_height()
                px = self.winfo_rootx() + self.winfo_width() - tw - 24
                py = self.winfo_rooty() + self.winfo_height() - th - 60
                toast.geometry(f"+{px}+{py}")
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            self._toast_actual = toast
            toast.after(duracion_ms, lambda: toast.destroy() if toast.winfo_exists() else None)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    def _toggle_fullscreen_principal(self, event=None):
        """F11 en ventana principal = toggle pantalla completa."""
        try:
            actual = bool(self.attributes("-fullscreen"))
            self.attributes("-fullscreen", not actual)
            if hasattr(self, "show_toast"):
                msg = "📺 Pantalla completa (F11/Esc para salir)" if not actual else "↩️ Salida pantalla completa"
                try: self.show_toast(msg, "#3b82f6", 1500)
                except Exception as e:
                    logger.debug(f"[silent] {e}")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        return "break"

    def _exit_fullscreen_principal(self, event=None):
        """Escape sale de pantalla completa si está activo."""
        try:
            if bool(self.attributes("-fullscreen")):
                self.attributes("-fullscreen", False)
                return "break"
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    def _atajo_generar_prompt(self, event=None):
        """Ctrl+Enter desde el textarea = generar prompt."""
        try:
            # Solo activar si el foco está en el textarea de idea
            focused = self.focus_get()
            if focused is None:
                return
            # Detectar si es nuestro textarea (compara con _textbox interno)
            if hasattr(self, "txt_idea") and (
                focused == self.txt_idea or focused == self.txt_idea._textbox
            ):
                self.cmd_prompt()
                return "break"  # impedir nueva línea
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    def _actualizar_indicador_proveedor(self):
        """Muestra ✅ verde si el LLM activo está disponible, ⚠️ amarillo si no."""
        try:
            if not hasattr(self, "_btn_key"):
                return
            provider = None
            if hasattr(self.clients, "get_active_provider"):
                provider = self.clients.get_active_provider()
            disponible = bool(provider and provider.disponible())

            # Cambiar el texto del botón 🔑 a 🔑✅ o 🔑⚠
            try:
                if disponible:
                    self._btn_key.configure(text="🔑", fg_color="#059669", hover_color="#047857")
                else:
                    self._btn_key.configure(text="⚠", fg_color="#d97706", hover_color="#b45309")
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")

    def _actualizar_indicador_adn(self):
        """Muestra/oculta el botón 🧬 ADN en el header + persiste estado."""
        try:
            # Persistir en preferencias para que sobreviva al reinicio
            try:
                prefs = self.store.cargar_preferencias() or {}
                prefs["anclaje_visual"] = self._anclaje_visual or ""
                self.store.guardar_preferencias(prefs)
            except Exception as _e:
                logger.debug(f"[silent] persistir adn: {_e}")

            if not hasattr(self, "_btn_adn"):
                return
            if self._anclaje_visual:
                if not self._btn_adn.winfo_ismapped():
                    self._btn_adn.pack(side="left", padx=(8, 0))
            else:
                if self._btn_adn.winfo_ismapped():
                    self._btn_adn.pack_forget()
        except Exception as _e:
            logger.debug(f"[silent] {_e}")

    def _cmd_indicador_adn(self):
        """Menú al pulsar el indicador 🧬 ADN: ver / desactivar."""
        if not self._anclaje_visual:
            self._actualizar_indicador_adn()
            return
        from modules.gprompt_window import GPromptWindow
        win = GPromptWindow(self)
        win.title(tr("🧬 ADN visual activo"))
        win.geometry("520x400")
        win.transient(self)

        ctk.CTkLabel(win, text=tr("🧬 ADN visual activo en próximas generaciones"),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 4))

        txt = ctk.CTkTextbox(win, font=ctk.CTkFont(size=11), wrap="word")
        txt.pack(fill="both", expand=True, padx=15, pady=(0, 8))
        txt.insert("1.0", self._anclaje_visual)
        txt.configure(state="disabled")

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(pady=10)

        def _desactivar():
            self._anclaje_visual = None
            self._actualizar_indicador_adn()
            try:
                self.show_toast("🧬 ADN visual desactivado", "#888")
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            win.destroy()

        ctk.CTkButton(btn_row, text=tr("🚫 Desactivar ADN"), width=160, height=30,
                      fg_color="#7a1a1a", hover_color="#5a0f0f",
                      command=_desactivar).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=tr("Cerrar"), width=100, height=30,
                      fg_color="#444", hover_color="#555",
                      command=win.destroy).pack(side="left", padx=4)
    def _backup_semanal_check(self):
        """Si han pasado >7 días desde el último backup, crea uno automático.

        Respalda TODA la carpeta de datos (~/.arquitecto_prompts/), incluyendo
        historial, favoritos, plantillas, personajes, loras, estrellas y prefs.
        """
        try:
            import time

            from config import ARCHIVOS, CARPETA_APP
            base = CARPETA_APP
            if not base.exists():
                return
            marker = ARCHIVOS["autobackup_marker"]
            ahora = time.time()
            necesario = True
            if marker.exists():
                try:
                    last = float(marker.read_text(encoding="utf-8").strip())
                    if ahora - last < 7 * 24 * 3600:
                        necesario = False
                except Exception as _e:
                    logger.debug(f"[silent] {_e}")
            if necesario:
                self._crear_backup_automatico(base, marker, ahora)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).warning(f"Backup semanal falló: {e}")

    def _crear_backup_automatico(self, base: Path, marker: Path, ahora: float):
        """Crea un zip de la carpeta de datos en backups/auto-AAAAMMDD.zip.

        Incluye TODOS los .json de la carpeta (historial, favoritos, plantillas,
        personajes, loras, estrellas, preferencias, keys). Excluye la propia
        subcarpeta backups/ y logs/ para no recursivar.
        """
        import datetime as _dt
        import zipfile

        from config import BACKUPS_DIR
        backups_dir = BACKUPS_DIR
        backups_dir.mkdir(parents=True, exist_ok=True)
        nombre = f"auto-{_dt.datetime.now().strftime('%Y%m%d')}.zip"
        path = backups_dir / nombre
        try:
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in base.glob("*.json"):
                    zf.write(f, f.name)
                # active_provider.txt también merece respaldo
                ap = base / "active_provider.txt"
                if ap.exists():
                    zf.write(ap, ap.name)
            marker.write_text(str(ahora), encoding="utf-8")
            # Toast informativo
            self.after(2000, lambda: self.show_toast(
                tr('💼 Backup auto creado: {0}').format(nombre), "#0891b2", 3500
            ))
            # Limpiar backups viejos (>10)
            backups = sorted(backups_dir.glob("auto-*.zip"))
            for old in backups[:-10]:
                try:
                    old.unlink()
                except Exception as _e:
                    logger.debug(f"[silent] {_e}")
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).warning(f"Error creando backup auto: {e}")

    # _build_header() vive en UIBuildersMixin (modules/ui_builders.py).
    # Eliminado de app.py en v1.0 para cumplir la regla del refactor:
    # los métodos _build_* viven en sus mixins, no aquí.

    def _regen_init(self):
        """Inicializa la pila de regeneraciones si no existe."""
        if not hasattr(self, "_regen_stack"):
            self._regen_stack = []   # lista de strings (resultados consecutivos)
            self._regen_idx = -1     # índice actual (-1 = ninguno)

    def _regen_push(self, texto):
        """Añade un resultado a la pila de regeneraciones (max 10)."""
        self._regen_init()
        if not texto: return
        # Si estamos navegando atrás y ahora se genera nuevo, descartamos los siguientes
        if self._regen_idx < len(self._regen_stack) - 1:
            self._regen_stack = self._regen_stack[:self._regen_idx + 1]
        self._regen_stack.append(texto)
        # Limitar a 10
        if len(self._regen_stack) > 10:
            self._regen_stack = self._regen_stack[-10:]
        self._regen_idx = len(self._regen_stack) - 1

    def _cmd_regenerar(self):
        """Regenera el prompt con la misma idea, guardando el resultado actual en la pila."""
        self._regen_init()
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea:
            self.dialogs.set_estado(tr("⚠️ Escribe una idea primero"), "#e67e22")
            return
        # Guardar resultado actual en pila ANTES de regenerar
        actual = self.txt_salida.get("1.0", "end").strip()
        if actual and (not self._regen_stack or self._regen_stack[-1] != actual):
            self._regen_push(actual)
        try: self.sesion._sesion_log("🔄 Regeneró prompt (misma idea)")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        # Llamar a la generación normal
        self.cmd_prompt()

    def _cmd_regenerar_atras(self):
        """Navega a la versión anterior de la regeneración."""
        self._regen_init()
        if not self._regen_stack:
            self.dialogs.set_estado(tr("⚠️ No hay versiones anteriores"), "#e67e22")
            return
        # Si estamos en el último, primero guardamos el actual
        actual = self.txt_salida.get("1.0", "end").strip()
        if self._regen_idx == len(self._regen_stack) - 1 and actual and \
                (not self._regen_stack or self._regen_stack[-1] != actual):
            self._regen_push(actual)
            self._regen_idx -= 1
        if self._regen_idx <= 0:
            self.dialogs.set_estado(tr("⚠️ Ya estás en la versión más antigua"), "#e67e22")
            return
        self._regen_idx -= 1
        self.dialogs.actualizar_salida(self._regen_stack[self._regen_idx])
        self.dialogs.set_estado(tr('← Versión {0}/{1}').format((self._regen_idx + 1), (len(self._regen_stack))), "#3498db")

    def _cmd_regenerar_adelante(self):
        """Navega a la versión siguiente de la regeneración."""
        self._regen_init()
        if not self._regen_stack or self._regen_idx >= len(self._regen_stack) - 1:
            self.dialogs.set_estado(tr("⚠️ Ya estás en la versión más reciente"), "#e67e22")
            return
        self._regen_idx += 1
        self.dialogs.actualizar_salida(self._regen_stack[self._regen_idx])
        self.dialogs.set_estado(tr('→ Versión {0}/{1}').format((self._regen_idx + 1), (len(self._regen_stack))), "#3498db")

    def _cmd_diff_versiones(self):
        """Muestra ventana con diff coloreado entre versión actual y anterior de la pila de regeneración."""
        self._regen_init()
        actual_txt = self.txt_salida.get("1.0", "end").strip()
        if not actual_txt:
            self.dialogs.set_estado(tr("⚠️ No hay prompt actual para comparar"), "#e67e22")
            return
        # Buscar la versión anterior
        if not self._regen_stack:
            self.dialogs.set_estado(tr("⚠️ No hay versiones anteriores. Pulsa 🔄 Regenerar para crear historial."), "#e67e22")
            return
        # Si el actual es el último, comparamos con el penúltimo
        if self._regen_idx == len(self._regen_stack) - 1:
            if len(self._regen_stack) < 2:
                self.dialogs.set_estado(tr("⚠️ Necesitas al menos 2 versiones para comparar"), "#e67e22")
                return
            anterior_txt = self._regen_stack[self._regen_idx - 1]
            etiqueta_actual = f"Versión {self._regen_idx + 1} (actual)"
            etiqueta_anterior = f"Versión {self._regen_idx} (anterior)"
        else:
            # Estamos navegando atrás, comparar con la siguiente
            if self._regen_idx + 1 >= len(self._regen_stack):
                self.dialogs.set_estado(tr("⚠️ No hay versión siguiente para comparar"), "#e67e22")
                return
            anterior_txt = self._regen_stack[self._regen_idx]
            actual_txt = self._regen_stack[self._regen_idx + 1]
            etiqueta_actual = f"Versión {self._regen_idx + 2}"
            etiqueta_anterior = f"Versión {self._regen_idx + 1}"

        self._abrir_ventana_diff(anterior_txt, actual_txt, etiqueta_anterior, etiqueta_actual)

    def _abrir_ventana_diff(self, texto_a, texto_b, label_a="Anterior", label_b="Actual",
                              on_apply=None, on_cancel=None, on_undo=None,
                              titulo=None, hint=None):
        """Abre ventana con diff coloreado de dos textos lado a lado.

        Si se pasan callbacks `on_apply`/`on_cancel`/`on_undo`, la ventana
        se comporta como modal de confirmación (uso desde 🔁 Refinar):
        muestra botones Aplicar/Cancelar/Deshacer en lugar de solo Cerrar.
        """
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        import difflib
        v = GPromptWindow(self)
        v.title(titulo or "📊 Diff visual entre versiones")
        v.geometry("1100x680")
        v.transient(self)

        ctk.CTkLabel(v, text=titulo or "📊 Comparar versiones",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4))

        # Banda de leyenda
        leyenda = ctk.CTkFrame(v, fg_color=c["fg_dark"], corner_radius=6)
        leyenda.pack(fill="x", padx=15, pady=(0, 8))
        leyenda_txt = hint or "🟢 Verde = añadido en actual    🔴 Rojo = quitado del anterior    ⚪ Sin color = igual"
        ctk.CTkLabel(leyenda, text=leyenda_txt,
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=6)

        # Container con dos columnas
        cols = ctk.CTkFrame(v, fg_color="transparent")
        cols.pack(fill="both", expand=True, padx=10, pady=4)
        cols.grid_columnconfigure(0, weight=1)
        cols.grid_columnconfigure(1, weight=1)
        cols.grid_rowconfigure(0, weight=1)

        # Columna izquierda (anterior)
        col_a = ctk.CTkFrame(cols, fg_color=c["fg_dark"], corner_radius=8)
        col_a.grid(row=0, column=0, padx=4, sticky="nsew")
        ctk.CTkLabel(col_a, text=f"📄 {label_a}", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=c["muted_text"]).pack(anchor="w", padx=10, pady=(8, 4))
        txt_a = ctk.CTkTextbox(col_a, wrap="word", font=ctk.CTkFont(family="Consolas", size=11))
        txt_a.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Columna derecha (actual)
        col_b = ctk.CTkFrame(cols, fg_color=c["fg_dark"], corner_radius=8)
        col_b.grid(row=0, column=1, padx=4, sticky="nsew")
        ctk.CTkLabel(col_b, text=f"📄 {label_b}", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=c["hdr_text"]).pack(anchor="w", padx=10, pady=(8, 4))
        txt_b = ctk.CTkTextbox(col_b, wrap="word", font=ctk.CTkFont(family="Consolas", size=11))
        txt_b.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # Tags de color (acceso al tk widget interno via _textbox)
        try:
            txt_a._textbox.tag_configure("removed", background="#5a1a1a", foreground="#ffffff")
            txt_a._textbox.tag_configure("equal", foreground=c["muted_text"])
            txt_b._textbox.tag_configure("added", background="#1a5a1a", foreground="#ffffff")
            txt_b._textbox.tag_configure("equal", foreground=c["muted_text"])
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # Calcular diff palabra a palabra
        palabras_a = texto_a.split()
        palabras_b = texto_b.split()
        sm = difflib.SequenceMatcher(None, palabras_a, palabras_b)

        # Insertar con tags
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                # Ambos lados: gris
                fragmento = " ".join(palabras_a[i1:i2]) + " "
                txt_a.insert("end", fragmento, "equal")
                txt_b.insert("end", fragmento, "equal")
            elif op == "delete":
                # Solo en A: rojo
                fragmento = " ".join(palabras_a[i1:i2]) + " "
                txt_a.insert("end", fragmento, "removed")
            elif op == "insert":
                # Solo en B: verde
                fragmento = " ".join(palabras_b[j1:j2]) + " "
                txt_b.insert("end", fragmento, "added")
            elif op == "replace":
                # Sustitución: rojo en A, verde en B
                frag_a = " ".join(palabras_a[i1:i2]) + " "
                frag_b = " ".join(palabras_b[j1:j2]) + " "
                txt_a.insert("end", frag_a, "removed")
                txt_b.insert("end", frag_b, "added")

        # Solo lectura
        txt_a.configure(state="disabled")
        txt_b.configure(state="disabled")

        # Stats abajo
        stats = ctk.CTkFrame(v, fg_color=c["fg_dark"], corner_radius=6)
        stats.pack(fill="x", padx=15, pady=(0, 8))
        n_eq = sum(i2 - i1 for op, i1, i2, j1, j2 in sm.get_opcodes() if op == "equal")
        n_add = sum(j2 - j1 for op, i1, i2, j1, j2 in sm.get_opcodes() if op in ("insert", "replace"))
        n_del = sum(i2 - i1 for op, i1, i2, j1, j2 in sm.get_opcodes() if op in ("delete", "replace"))
        ratio = sm.ratio() * 100
        ctk.CTkLabel(stats,
                     text=tr('  📊 {0:.0f}% similar  ·  🟢 +{1} palabras  ·  🔴 −{2} palabras  ·  ⚪ {3} sin cambios').format((ratio), (n_add), (n_del), (n_eq)),
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=6)

        # Botones: modo confirmación (on_apply) vs modo solo-lectura
        btn_row = ctk.CTkFrame(v, fg_color="transparent")
        btn_row.pack(pady=(0, 12))
        if on_apply is not None:
            def _aplicar():
                try: on_apply()
                finally: v.destroy()
            def _cancelar():
                try:
                    if on_cancel: on_cancel()
                finally: v.destroy()
            ctk.CTkButton(btn_row, text=tr("✅ Aplicar refinamiento"), width=200, height=34,
                          fg_color="#1a7a3c", hover_color="#15633a",
                          font=ctk.CTkFont(size=12, weight="bold"),
                          command=_aplicar).pack(side="left", padx=5)
            if on_undo is not None:
                def _deshacer():
                    try: on_undo()
                    finally: v.destroy()
                ctk.CTkButton(btn_row, text=tr("↩️ Deshacer refinamiento previo"), width=230, height=34,
                              fg_color="#8a5a1a", hover_color="#6a4515",
                              font=ctk.CTkFont(size=11),
                              command=_deshacer).pack(side="left", padx=5)
            ctk.CTkButton(btn_row, text=tr("❌ Cancelar (mantener original)"), width=220, height=34,
                          fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                          font=ctk.CTkFont(size=11),
                          command=_cancelar).pack(side="left", padx=5)
            # Esc → cancelar
            v.bind("<Escape>", lambda _e: _cancelar())
        else:
            # Modo lectura: además de Cerrar, permite aplicar cualquiera de
            # las dos versiones a la salida (feedback usuario sesión 19:
            # "solo tenemos cerrar en la ventana de diff").
            def _usar(texto, etiqueta):
                self.dialogs.actualizar_salida(texto)
                v.destroy()
                self.dialogs.set_estado(tr('⏪ Aplicada: {0}').format(etiqueta), "#2ecc71")
            ctk.CTkButton(btn_row, text=tr('⏪ Usar {0}').format(label_a), width=200, height=32,
                          fg_color="#8a5a1a", hover_color="#6a4515",
                          font=ctk.CTkFont(size=11),
                          command=lambda: _usar(texto_a, label_a)).pack(side="left", padx=5)
            ctk.CTkButton(btn_row, text=tr('✅ Usar {0}').format(label_b), width=200, height=32,
                          fg_color="#1a7a3c", hover_color="#15633a",
                          font=ctk.CTkFont(size=11),
                          command=lambda: _usar(texto_b, label_b)).pack(side="left", padx=5)
            ctk.CTkButton(btn_row, text=tr("Cerrar"), width=110, height=32, command=v.destroy,
                          fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"]).pack(side="left", padx=5)

    def _notificar_sistema(self, titulo, mensaje):
        """Notificación del sistema operativo (Windows / macOS / Linux)."""
        try:
            import platform
            sistema = platform.system()
            if sistema == "Windows":
                try:
                    from plyer import notification
                    notification.notify(title=titulo, message=mensaje, timeout=3, app_name="G-Prompt Studio")
                except ImportError:
                    # Fallback: usar bell
                    self.bell()
            elif sistema == "Darwin":  # macOS
                import subprocess
                _msg = mensaje.replace("\\", "").replace('"', "'")
                _tit = titulo.replace("\\", "").replace('"', "'")
                subprocess.run(['osascript', '-e', f'display notification "{_msg}" with title "{_tit}"'])
            elif sistema == "Linux":
                import subprocess
                subprocess.run(['notify-send', titulo, mensaje])
        except Exception as _e:
            logger.debug(f"[silent] {_e}")

    def _parsear_bloques_numerados(self, texto, prefijos_validos=None, n_esperado=None):
        """Parser ROBUSTO de respuestas con bloques tipo 'PROMPT 1:', 'SHOT 2:', 'FRAME 3:', '1.', etc.

        `n_esperado`: si se pasa y el parser devuelve más bloques de los
        esperados, filtra preámbulos del LLM (títulos, descripciones de
        mood, etc.) priorizando bloques que contienen "POSITIVE PROMPT:"
        o "POSITIVE:". Esto evita que un texto como
        "MOODBOARD: 10 PROMPTS CON ATMÓSFERA COHERENTE..." salga como
        bloque #1 antes del primer prompt real.
        """
        if not texto: return []
        import re
        # Probar varios patrones (de más estricto a más permisivo)
        patrones = [
            r'(?:^|\n)\s*(?:PROMPT|SHOT|FRAME|VARIANTE|VERSION|PANEL)\s*\d+\s*[:\-—\(\n]',  # "PROMPT 1:", "SHOT 2 (Wide):", "PANEL 1\n..."
            r'(?:^|\n)\s*\d+\s*[\.\)]\s+',                                            # "1.", "1)"
            r'\n---+\n',                                                              # separadores ---
            r'(?:^|\n)\s*###\s*[^#\n]+\s*###\s*\n',                                   # ### Título ###
        ]
        partes_limpias = []
        for patron in patrones:
            partes = re.split(patron, '\n' + texto, flags=re.IGNORECASE)
            partes_limpias = [p.strip().strip("-").strip() for p in partes if p.strip() and len(p.strip()) > 30]
            if len(partes_limpias) >= 2:
                break

        if not partes_limpias or len(partes_limpias) < 2:
            # Fallback: si el texto tiene varios "POSITIVE PROMPT:" lo divide
            coincidencias = list(re.finditer(r'POSITIVE\s+PROMPT\s*:', texto, re.IGNORECASE))
            if len(coincidencias) >= 2:
                bloques = []
                for i, m in enumerate(coincidencias):
                    inicio = m.start()
                    fin = coincidencias[i+1].start() if i+1 < len(coincidencias) else len(texto)
                    bloques.append(texto[inicio:fin].strip())
                partes_limpias = bloques
            else:
                # Último fallback: devolver como un solo bloque
                return [texto.strip()] if len(texto.strip()) > 30 else []

        # Filtrar preámbulos cuando el LLM devuelve más bloques de los pedidos.
        # Estrategia: si hay >= n_esperado bloques con marker de prompt
        # ("POSITIVE PROMPT:", "POSITIVE:"), preferir esos. Si no, quedarse
        # con los últimos n_esperado (asumiendo que el preámbulo va primero).
        if n_esperado is not None and len(partes_limpias) > n_esperado:
            con_marker = [
                p for p in partes_limpias
                if re.search(r'POSITIVE\s+PROMPT|POSITIVE\s*:', p, re.IGNORECASE)
            ]
            if len(con_marker) >= n_esperado:
                partes_limpias = con_marker[:n_esperado]
            else:
                # Heurística: el preámbulo del LLM suele ir al principio
                partes_limpias = partes_limpias[-n_esperado:]
        return partes_limpias

    def _cargar_plantillas_desde_json(self) -> list:
        """Carga plantillas desde data/plantillas_default.json.

        Devuelve lista de tuplas (nombre, positive, negative, categoria).
        La categoría puede ser "" si la plantilla no la define.
        """
        import json
        import os
        try:
            ruta_json = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "data", "plantillas_default.json")
            if not os.path.exists(ruta_json):
                logger.warning(f"Plantillas JSON no encontrado: {ruta_json}")
                return []
            with open(ruta_json, "r", encoding="utf-8") as f:
                datos = json.load(f)
            plantillas = datos.get("plantillas", [])
            return [
                (p["nombre"], p["positive"], p.get("negative", ""),
                 p.get("categoria", ""))
                for p in plantillas
            ]
        except Exception as e:
            logger.error(f"Error cargando plantillas JSON: {e}")
            return []

    def _cmd_plantillas_populares(self):
        """Biblioteca de plantillas con buscador y wizard de variables.

        Mejoras:
        - Buscador en cabecera (filtra por nombre, contenido o variable).
        - "Cargar plantilla" abre un wizard que rellena las {variables} y
          previsualiza el prompt final antes de aplicarlo.
        - El form siempre arriba ahora sale solo si hay variables.
        """
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        plantillas = self._cargar_plantillas_desde_json()
        if not plantillas:
            self.dialogs.set_estado(tr("⚠️ No se pudieron cargar las plantillas"), "#e74c3c")
            return

        plantillas_sorted = sorted(plantillas, key=lambda x: x[0])

        # Estado mutable que `_recargar_estado()` actualiza in-place para
        # evitar cerrar/reabrir la ventana al borrar o restaurar.
        estado = {
            "visibles": [],
            "total_borradas": 0,
            "cats": [],
        }

        def _recargar_estado():
            prefs_act = self.store.cargar_preferencias()
            ocultas_set = set(prefs_act.get("plantillas_predef_ocultas", []))
            estado["visibles"] = [p for p in plantillas_sorted if p[0] not in ocultas_set]
            estado["total_borradas"] = len(ocultas_set)
            estado["cats"] = sorted({
                p[3] for p in estado["visibles"]
                if len(p) > 3 and p[3]
            })

        _recargar_estado()

        vent = GPromptWindow(self)
        vent.title(tr("📑 Plantillas de prompt"))
        vent.geometry("860x700")
        vent.transient(self)

        # ── Cabecera ──
        hdr_frame = ctk.CTkFrame(vent, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(10, 3), padx=12)
        ctk.CTkLabel(hdr_frame, text=tr("📑 Plantillas probadas"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        contador_var = ctk.StringVar(value="")
        ctk.CTkLabel(hdr_frame, textvariable=contador_var,
                     font=ctk.CTkFont(size=10),
                     text_color=c["muted_text"]).pack(side="left", padx=10)

        # Slot para el botón de restaurar — recreado por _refrescar_restaurar_btn
        restaurar_slot = ctk.CTkFrame(hdr_frame, fg_color="transparent")
        restaurar_slot.pack(side="right")

        def _restaurar_borradas():
            n = estado["total_borradas"]
            prefs_act = self.store.cargar_preferencias()
            prefs_act["plantillas_predef_ocultas"] = []
            self.store.guardar_preferencias(prefs_act)
            _recargar_estado()
            _refrescar_restaurar_btn()
            _refrescar()
            self.dialogs.set_estado(tr('↩ {0} plantillas predefinidas restauradas').format(n), "#2ecc71")

        def _refrescar_restaurar_btn():
            for w in restaurar_slot.winfo_children():
                w.destroy()
            if estado["total_borradas"] > 0:
                ctk.CTkButton(restaurar_slot,
                              text=tr('↩ Restaurar {0} borradas').format(estado['total_borradas']),
                              width=180, height=24,
                              fg_color="#8b6914", hover_color="#6e5310",
                              font=ctk.CTkFont(size=10),
                              command=_restaurar_borradas).pack()

        _refrescar_restaurar_btn()

        # ── Buscador ──
        search_row = ctk.CTkFrame(vent, fg_color="transparent")
        search_row.pack(fill="x", padx=12, pady=(0, 6))
        ctk.CTkLabel(search_row, text="🔍").pack(side="left", padx=(0, 6))
        entry_buscar = ctk.CTkEntry(
            search_row, placeholder_text=tr("Buscar por nombre, contenido o variable…"),
            height=30,
        )
        entry_buscar.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(search_row, text="✕", width=32, height=30,
                      fg_color="#444", hover_color="#222",
                      command=lambda: (entry_buscar.delete(0, "end"), _refrescar())
                      ).pack(side="left", padx=(6, 0))

        # Filtro por categoría (si hay categorías en las plantillas)
        cat_var = ctk.StringVar(value="Todas")
        if estado["cats"]:
            cat_row = ctk.CTkFrame(vent, fg_color="transparent")
            cat_row.pack(fill="x", padx=12, pady=(0, 4))
            ctk.CTkLabel(cat_row, text=tr("Categoría:"),
                         font=ctk.CTkFont(size=10)).pack(side="left", padx=(0, 6))
            ctk.CTkComboBox(
                cat_row, width=180, variable=cat_var,
                values=["Todas"] + [c.capitalize() for c in estado["cats"]],
                command=lambda _v: _refrescar(),
            ).pack(side="left")

        ctk.CTkLabel(vent,
                     text=tr("Click en 'Cargar' → wizard para rellenar las {variables} → previsualizas el prompt final."),
                     font=ctk.CTkFont(size=10),
                     text_color=c["muted_text"]).pack(pady=(0, 4), padx=12, anchor="w")

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=5)

        # Debounce del buscador
        busqueda_pending = {"after_id": None}

        def _on_buscar(_e=None):
            if busqueda_pending["after_id"]:
                try:
                    vent.after_cancel(busqueda_pending["after_id"])
                except Exception as _e2:
                    logger.debug(f"[silent] {_e2}")
            busqueda_pending["after_id"] = vent.after(200, _refrescar)
        entry_buscar.bind("<KeyRelease>", _on_buscar)

        def _refrescar():
            for w in scroll.winfo_children():
                w.destroy()
            termino = entry_buscar.get().strip().lower()
            cat_sel = cat_var.get().lower() if cat_var.get() != "Todas" else None
            import re
            visibles = []
            for p in estado["visibles"]:
                # Compat: tupla de 3 o 4 elementos
                if len(p) == 4:
                    nombre, pos, neg, categoria = p
                else:
                    nombre, pos, neg = p[:3]
                    categoria = ""
                if cat_sel and categoria.lower() != cat_sel:
                    continue
                if termino:
                    text = f"{nombre} {pos} {neg} {categoria}".lower()
                    if termino not in text:
                        continue
                visibles.append((nombre, pos, neg, categoria))

            sufijo_cat = f" · {cat_var.get()}" if cat_sel else ""
            contador_var.set(
                f"({len(visibles)} de {len(estado['visibles'])}{sufijo_cat})"
                if (termino or cat_sel) else f"({len(estado['visibles'])})"
            )
            if not visibles:
                # Sin estado["visibles"] = todas borradas (caso especial)
                if not estado["visibles"]:
                    ctk.CTkLabel(scroll,
                                 text=tr("📭 No hay plantillas visibles.\n\n"
                                      "Has borrado todas las plantillas predefinidas."),
                                 font=ctk.CTkFont(size=12),
                                 text_color=c["muted_text"],
                                 justify="center").pack(pady=30)
                else:
                    msg = (tr("Sin resultados para '{0}'").format(termino) if termino
                           else tr("Sin plantillas en {0}").format(cat_var.get()))
                    ctk.CTkLabel(scroll, text=msg,
                                 text_color=c["muted_text"]).pack(pady=30)
                return

            for nombre, pos, neg, categoria in visibles:
                card = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=8)
                card.pack(fill="x", pady=4)
                hdr_card = ctk.CTkFrame(card, fg_color="transparent")
                hdr_card.pack(fill="x", padx=10, pady=(6, 2))
                ctk.CTkLabel(hdr_card, text=nombre,
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=c["hdr_text"]).pack(side="left")
                if categoria:
                    ctk.CTkLabel(hdr_card,
                                 text=f"  · {categoria}",
                                 font=ctk.CTkFont(size=9),
                                 text_color=c["accent_text"]).pack(side="left")
                vars_pos = re.findall(r'\{(\w+)\}', pos)
                vars_neg = re.findall(r'\{(\w+)\}', neg)
                todas_vars = sorted(set(vars_pos + vars_neg))
                if todas_vars:
                    ctk.CTkLabel(card, text=tr('  Variables: {0}').format(', '.join(todas_vars)),
                                 font=ctk.CTkFont(size=10, slant="italic"),
                                 text_color=c["muted_text"]
                                 ).pack(anchor="w", padx=10)
                preview = pos[:120]
                ctk.CTkLabel(card, text=tr('  POS: {0}…').format(preview),
                             font=ctk.CTkFont(size=10),
                             text_color=c["muted_text"],
                             wraplength=760, justify="left", anchor="w"
                             ).pack(fill="x", padx=10, pady=(0, 4))

                btns_frame = ctk.CTkFrame(card, fg_color="transparent")
                btns_frame.pack(fill="x", padx=10, pady=(0, 6))

                def _aplicar(p=pos, n=neg, name=nombre, variables=todas_vars):
                    if variables:
                        # Abrir wizard de variables
                        self._wizard_variables_plantilla(name, p, n, variables, vent)
                    else:
                        # Sin variables: aplicar directo
                        txt = f"POSITIVE PROMPT: {p}"
                        if n:
                            txt += f"\nNEGATIVE PROMPT: {n}"
                        self.dialogs.actualizar_salida(txt)
                        vent.destroy()
                        self.dialogs.set_estado(tr("📑 Plantilla '{0}' aplicada").format(name), "#2ecc71")

                def _borrar(name=nombre):
                    from tkinter import messagebox as _mb
                    if not _mb.askyesno(tr("Confirmar"),
                                        tr("¿Borrar plantilla '{0}'?\n"
                                           "(usa '↩ Restaurar' arriba para recuperarla)").format(name),
                                        parent=vent):
                        return
                    prefs_act = self.store.cargar_preferencias()
                    ocultas_set = set(prefs_act.get("plantillas_predef_ocultas", []))
                    ocultas_set.add(name)
                    prefs_act["plantillas_predef_ocultas"] = sorted(ocultas_set)
                    self.store.guardar_preferencias(prefs_act)
                    _recargar_estado()
                    _refrescar_restaurar_btn()
                    _refrescar()
                    self.dialogs.set_estado(tr("🗑 '{0}' borrada").format(name), "#e67e22")

                ctk.CTkButton(btns_frame, text=tr("🗑 Borrar"), width=90, height=24,
                              fg_color="#8b2c2c", hover_color="#6e2020",
                              font=ctk.CTkFont(size=10),
                              command=_borrar).pack(side="left")
                ctk.CTkButton(btns_frame, text=tr("✅ Cargar plantilla"), width=160, height=24,
                              fg_color="#1a7a3c", hover_color="#15642f",
                              font=ctk.CTkFont(size=10),
                              command=_aplicar).pack(side="right")

        _refrescar()
        entry_buscar.focus_set()

    def _wizard_variables_plantilla(self, nombre, pos, neg, variables, ventana_padre):
        """Wizard interactivo: pide valores para las {variables} y previsualiza
        el prompt final antes de aplicar.

        Recuerda los últimos valores introducidos por plantilla en
        preferencias.json bajo "plantilla_variables_ultimas" para que
        al reabrir la misma plantilla los campos vengan pre-rellenados.
        """
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        # Cargar últimos valores guardados para ESTA plantilla
        try:
            _prefs_w = self.store.cargar_preferencias() or {}
            _ult = _prefs_w.get("plantilla_variables_ultimas", {}) or {}
            ultimos = _ult.get(nombre, {}) if isinstance(_ult, dict) else {}
            if not isinstance(ultimos, dict):
                ultimos = {}
        except Exception as _e:
            logger.debug(f"[silent] cargar últimos del wizard: {_e}")
            ultimos = {}

        wiz = GPromptWindow(ventana_padre)
        wiz.title(tr('📝 Rellenar variables — {0}').format(nombre))
        wiz.geometry("680x640")
        wiz.transient(ventana_padre)

        ctk.CTkLabel(wiz, text=tr("📝 Rellenar variables de '{0}'").format(nombre),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 4))
        subtitulo = (f"Esta plantilla tiene {len(variables)} variable(s). "
                     f"Rellénalas y verás la previsualización abajo.")
        if ultimos:
            subtitulo += "  💾 (recordando tus últimos valores)"
        ctk.CTkLabel(wiz, text=subtitulo,
                     font=ctk.CTkFont(size=10),
                     text_color=c["muted_text"]).pack(pady=(0, 10))

        # Frame con los campos
        form = ctk.CTkScrollableFrame(wiz, fg_color="transparent", height=180)
        form.pack(fill="x", padx=15, pady=(0, 8))

        entries = {}
        for v in variables:
            row = ctk.CTkFrame(form, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=f"{{{v}}}:",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         width=140, anchor="w").pack(side="left", padx=(0, 6))
            ent = ctk.CTkEntry(row,
                               placeholder_text=tr('valor para {0}…').format(v),
                               height=28)
            ent.pack(side="left", fill="x", expand=True)
            # Pre-rellenar con el último valor guardado para esta variable
            if ultimos.get(v):
                ent.insert(0, ultimos[v])
            entries[v] = ent

        def _limpiar_memoria():
            try:
                _p = self.store.cargar_preferencias() or {}
                _u = _p.get("plantilla_variables_ultimas", {}) or {}
                if not isinstance(_u, dict):
                    _u = {}
                _u.pop(nombre, None)
                _p["plantilla_variables_ultimas"] = _u
                self.store.guardar_preferencias(_p)
                for ent in entries.values():
                    ent.delete(0, "end")
                _actualizar_preview()
                self.dialogs.set_estado(tr("🧹 Memoria de '{0}' borrada").format(nombre), "#888")
            except Exception as e:
                logger.warning(f"_limpiar_memoria wizard: {e}")

        # Previsualización
        ctk.CTkLabel(wiz, text=tr("👁 Previsualización del prompt final:"),
                     font=ctk.CTkFont(size=11, weight="bold")
                     ).pack(anchor="w", padx=15, pady=(8, 2))
        preview_txt = ctk.CTkTextbox(wiz,
                                     font=ctk.CTkFont(family="Consolas", size=10),
                                     wrap="word", height=200,
                                     fg_color=("#f9fafb" if is_lt else "#0f172a"))
        preview_txt.pack(fill="both", expand=True, padx=15, pady=(0, 8))

        def _actualizar_preview(*_):
            valores = {v: (entries[v].get().strip() or f"{{{v}}}") for v in variables}
            pos_r = pos
            neg_r = neg
            for k, val in valores.items():
                pos_r = pos_r.replace(f"{{{k}}}", val)
                neg_r = neg_r.replace(f"{{{k}}}", val)
            preview_txt.configure(state="normal")
            preview_txt.delete("1.0", "end")
            preview_txt.insert("1.0", f"POSITIVE PROMPT: {pos_r}")
            if neg_r.strip():
                preview_txt.insert("end", f"\n\nNEGATIVE PROMPT: {neg_r}")
            preview_txt.configure(state="disabled")

        for ent in entries.values():
            ent.bind("<KeyRelease>", _actualizar_preview)
        _actualizar_preview()

        # Botones
        btn_row = ctk.CTkFrame(wiz, fg_color="transparent")
        btn_row.pack(pady=8)

        def _persistir_valores():
            """Guarda los valores actuales como últimos para esta plantilla."""
            try:
                valores = {v: ent.get().strip()
                           for v, ent in entries.items()
                           if ent.get().strip()}
                _p = self.store.cargar_preferencias() or {}
                _u = _p.get("plantilla_variables_ultimas", {}) or {}
                if not isinstance(_u, dict):
                    _u = {}
                if valores:
                    _u[nombre] = valores
                else:
                    _u.pop(nombre, None)
                _p["plantilla_variables_ultimas"] = _u
                self.store.guardar_preferencias(_p)
            except Exception as e:
                logger.debug(f"_persistir_valores wizard: {e}")

        def _aplicar_final():
            faltan = [v for v, ent in entries.items() if not ent.get().strip()]
            if faltan:
                from tkinter import messagebox as _mb
                if not _mb.askyesno(
                    tr("Variables sin rellenar"),
                    tr("No has rellenado: {0}.\n\n"
                       "Si continúas, los valores quedarán como {{{{nombre}}}} literales.\n\n"
                       "¿Aplicar de todas formas?").format(", ".join(faltan)),
                    parent=wiz,
                ):
                    return
            _persistir_valores()
            txt_final = preview_txt.get("1.0", "end").strip()
            self.dialogs.actualizar_salida(txt_final)
            wiz.destroy()
            ventana_padre.destroy()
            self.dialogs.set_estado(tr("📑 Plantilla '{0}' aplicada con variables").format(nombre), "#2ecc71")

        ctk.CTkButton(btn_row, text=tr("✅ Aplicar al prompt"), width=170, height=32,
                      fg_color="#1a7a3c", hover_color="#15642f",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=_aplicar_final).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=tr("📋 Copiar"), width=90, height=32,
                      fg_color="#1a4a5a",
                      command=lambda: (_persistir_valores(),
                                       pyperclip.copy(preview_txt.get("1.0", "end").strip()),
                                       self.dialogs.set_estado(tr("📋 Copiado"), "#2ecc71"))
                      ).pack(side="left", padx=4)
        if ultimos:
            ctk.CTkButton(btn_row, text=tr("🧹 Olvidar valores"), width=130, height=32,
                          fg_color="#8b6914", hover_color="#6e5310",
                          font=ctk.CTkFont(size=10),
                          command=_limpiar_memoria).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=tr("Cancelar"), width=80, height=32,
                      fg_color="#444", hover_color="#555",
                      command=wiz.destroy).pack(side="left", padx=4)

        # Focus al primer campo
        if entries:
            list(entries.values())[0].focus_set()

    def _abrir_comparador(self, variaciones, labels=None, extra_botones=None):
        """Comparador genérico de variantes.

        `labels`: lista opcional de etiquetas (uno por variante). Si se pasa,
        sustituye al "Variación #N" en cada columna. Útil para mostrar el
        nombre del modelo / temperatura / etc. cuando se compara entre
        distintos contextos (no solo variaciones del mismo prompt).

        Si una variante empieza con `### algo ###\\n`, esa cabecera se
        extrae automáticamente como label (compat con llamadores legacy).

        `extra_botones`: lista opcional de `(label, fg_color, callback)`.
        Cada uno se renderiza al pie de la ventana, junto al botón
        Cerrar. El callback recibe (variaciones, ventana) y decide si
        cerrar o no. Usado por Board→Vídeo para encadenar el
        storyboard como prompt de vídeo.
        """
        vent = GPromptWindow(self)
        vent.title(tr("👁 Comparar Variaciones"))
        n = len(variaciones)

        # Extraer labels desde `### nombre ###\n` si no se pasaron explícitas
        if labels is None:
            labels = []
            limpias = []
            import re as _re
            for v in variaciones:
                m = _re.match(r'###\s*(.+?)\s*###\s*\n', v)
                if m:
                    labels.append(m.group(1))
                    limpias.append(v[m.end():])
                else:
                    labels.append(None)
                    limpias.append(v)
            variaciones = limpias

        # Colores del tema
        is_lt = ctk.get_appearance_mode().lower() == "light"
        from config import get_theme_colors
        c = get_theme_colors(is_lt)

        # Limitar a tamaño de pantalla — columnas más estrechas para que quepan más
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        col_width = 380  # más estrecho que antes (510)
        ancho = min(col_width * min(n, 4) + 80, screen_w - 100)  # max 4 columnas visibles
        alto = min(750, screen_h - 100)
        vent.geometry(f"{ancho}x{alto}")
        vent.transient(self)

        ctk.CTkLabel(vent, text=tr('👁 Comparador ({0})  —  Scroll horizontal para ver todas').format(n),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(8, 3))

        # Scroll horizontal para columnas
        scroll_frame = ctk.CTkScrollableFrame(vent, fg_color="transparent", orientation="horizontal")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        frame_cols = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        frame_cols.pack(fill="both", expand=True)

        colores_header = ["#1a4a7a", "#1a7a3c", "#4a1a7a", "#7a3c1a", "#3a5a1a", "#7a1a4a", "#5a3c1a", "#1a5a5a"]
        tiene_neg = self._debe_mostrar_negatives()

        # Refs compartidas entre todas las cards: cuando se aplica una,
        # las demás se desmarcan visualmente.
        cols_aplicadas_refs = {"all": []}

        # Estado para "comparar 2 lado-a-lado": map col_index → BooleanVar
        compare_vars = {}
        compare_btn_ref = {"btn": None}

        def _on_compare_toggle():
            """Limita a max 2 selecciones simultáneas y actualiza el botón."""
            seleccionadas = [i for i, v in compare_vars.items() if v.get()]
            if len(seleccionadas) > 2:
                # Desmarcar la PRIMERA (FIFO) para mantener solo las 2 más recientes
                compare_vars[seleccionadas[0]].set(False)
                seleccionadas = seleccionadas[1:]
            btn = compare_btn_ref["btn"]
            if btn is not None:
                try:
                    if len(seleccionadas) == 2:
                        btn.configure(
                            state="normal", fg_color="#7c3aed",
                            text=tr("🆚 Comparar 2 lado-a-lado"),
                        )
                    else:
                        btn.configure(
                            state="disabled", fg_color="#4b5563",
                            text=tr("🆚 Selecciona 2 cards para comparar"),
                        )
                except Exception as _e:
                    logger.debug(f"[silent] compare btn: {_e}")

        for i, var in enumerate(variaciones):
            col = ctk.CTkFrame(frame_cols, fg_color=c["fg_frame"], corner_radius=8, width=col_width)
            col.pack(side="left", fill="y", padx=3, pady=2)
            col.pack_propagate(False)
            col.configure(width=col_width, height=alto - 100)

            hdr = ctk.CTkFrame(col, fg_color=colores_header[i % len(colores_header)], corner_radius=6, height=28)
            hdr.pack(fill="x", padx=5, pady=(5, 3))
            hdr.pack_propagate(False)
            label_txt = labels[i] if labels and i < len(labels) and labels[i] else f"Variación #{i+1}"
            ctk.CTkLabel(hdr, text=f"  {label_txt}",
                         font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=8)
            # Checkbox 🆚 para seleccionar esta variante para comparación lado-a-lado
            compare_vars[i] = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(hdr, text="🆚", variable=compare_vars[i],
                             command=_on_compare_toggle,
                             width=22, checkbox_width=14, checkbox_height=14,
                             font=ctk.CTkFont(size=10),
                             fg_color="#7c3aed", hover_color="#5b21b6",
                             border_width=1).pack(side="right", padx=6)

            # Separar POSITIVE y NEGATIVE visualmente
            pos_text = self._extraer_pos_de_bloque(var) or var
            neg_text = self._extraer_neg_de_bloque(var) or ""

            scroll = ctk.CTkScrollableFrame(col, fg_color="transparent")
            scroll.pack(fill="both", expand=True, padx=5, pady=(0, 3))

            ctk.CTkLabel(scroll, text=tr("🟢 POSITIVE:"), font=ctk.CTkFont(size=10, weight="bold"), text_color="#2ecc71").pack(anchor="w")
            lbl_pos = ctk.CTkLabel(scroll, text=pos_text, wraplength=col_width - 60, justify="left", font=ctk.CTkFont(size=10), text_color=c["muted_text"], anchor="w")
            lbl_pos.pack(fill="x", pady=(0, 6))

            if neg_text and tiene_neg:
                ctk.CTkLabel(scroll, text=tr("🔴 NEGATIVE:"), font=ctk.CTkFont(size=10, weight="bold"), text_color="#e74c3c").pack(anchor="w")
                ctk.CTkLabel(scroll, text=neg_text, wraplength=col_width - 60, justify="left", font=ctk.CTkFont(size=10), text_color="#999999", anchor="w").pack(fill="x", pady=(0, 4))

            # Label para traducción (inicialmente vacío)
            lbl_trad = ctk.CTkLabel(scroll, text="", wraplength=col_width - 60, justify="left", font=ctk.CTkFont(size=10, slant="italic"), text_color="#8bb4d4", anchor="w")

            # Botones
            btn_row = ctk.CTkFrame(col, fg_color="transparent")
            btn_row.pack(fill="x", padx=5, pady=(0, 5))

            def _copiar_completo(v=var, n=i+1):
                pyperclip.copy(v)
                self.dialogs.set_estado(tr('✅ Variación #{0} copiada').format(n), "#2ecc71")

            def _copiar_pos(p=pos_text, n=i+1):
                pyperclip.copy(p)
                self.dialogs.set_estado(tr('✅ POSITIVE #{0} copiado').format(n), "#2ecc71")

            def _copiar_neg(ng=neg_text, n=i+1):
                if ng:
                    pyperclip.copy(ng)
                    self.dialogs.set_estado(tr('✅ NEGATIVE #{0} copiado').format(n), "#2ecc71")

            # Registrar esta card en el set compartido
            cols_aplicadas_refs["all"].append((col, hdr, colores_header[i % len(colores_header)]))

            def _usar(v=var, n=i+1, label=label_txt, col_ref=col, hdr_ref=hdr,
                      hdr_color=colores_header[i % len(colores_header)],
                      pos=pos_text, neg=neg_text):
                """Aplica al editor SIN cerrar la ventana del comparador.

                - Cambia el combo del modelo activo si el label trae el
                  nombre (formato "🏆 nombre" o el propio nombre limpio).
                - Sobrescribe el resultado con el prompt de esta variante.
                - Marca visualmente la card como "aplicada" y desmarca las
                  demás. La ventana sigue abierta para que el usuario
                  pueda probar otros modelos sin perder las opciones.
                """
                # Cambiar modelo activo si label es de tipo "🏆 ModeloX"
                nombre_modelo = label
                for prefijo in ("🏆 ", "🥇 ", "🥈 ", "🥉 "):
                    if nombre_modelo.startswith(prefijo):
                        nombre_modelo = nombre_modelo[len(prefijo):]
                        break
                modelo_aplicado = self._intentar_cambiar_modelo(nombre_modelo)

                # Reconstruir formato POSITIVE/NEGATIVE si la variante venía
                # "pelada" (sin etiquetas). Sin esto, al pulsar Usar el
                # txt_salida pierde el formato esperado por el resto de la app.
                if "POSITIVE PROMPT:" in v.upper() or "POSITIVE:" in v.upper():
                    # Ya viene formateado, aplicar tal cual
                    texto_aplicar = v
                elif pos and neg and tiene_neg:
                    texto_aplicar = f"POSITIVE PROMPT: {pos}\n\nNEGATIVE PROMPT: {neg}"
                elif pos:
                    texto_aplicar = f"POSITIVE PROMPT: {pos}"
                else:
                    texto_aplicar = v

                # Aplicar prompt al resultado
                self.dialogs.actualizar_salida(texto_aplicar)

                # Marcar visualmente: cabecera dorada en la card aplicada
                for prev_col, prev_hdr, prev_color in cols_aplicadas_refs.get("all", []):
                    try:
                        prev_col.configure(border_width=0)
                        prev_hdr.configure(fg_color=prev_color)
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")
                try:
                    col_ref.configure(border_color="#fbbf24", border_width=3)
                    hdr_ref.configure(fg_color="#fbbf24")
                except Exception as _e:
                    logger.debug(f"[silent] {_e}")

                # Mensaje según si cambió el modelo o no
                if modelo_aplicado:
                    self.dialogs.set_estado(
                        tr("🏆 Modelo '{0}' + prompt cargados — la ventana sigue abierta").format(modelo_aplicado),
                        "#2ecc71")
                else:
                    self.dialogs.set_estado(
                        tr("✅ '{0}' cargada — la ventana sigue abierta").format(label),
                        "#2ecc71")

            def _traducir(p=pos_text, lbl=lbl_trad):
                lbl.pack(fill="x", pady=(6, 4))
                lbl.configure(text=tr("🌐 Traduciendo..."))
                def _worker():
                    try:
                        trad = self.deepseek.traducir_a_espanol(p)
                        vent.after(0, lambda: lbl.configure(text=f"🇪🇸 {trad}"))
                    except Exception:
                        vent.after(0, lambda: lbl.configure(text=tr("❌ Error al traducir")))
                threading.Thread(target=_worker, daemon=True).start()

            # Placeholder donde irá la preview Pollinations (oculto hasta click)
            preview_lbl = ctk.CTkLabel(scroll, text="", fg_color="transparent")
            preview_lbl.pack(fill="x", pady=(4, 0))

            def _preview_pollinations(p=pos_text, lbl=preview_lbl):
                lbl.configure(text=tr("⏳ Preparando..."), text_color="#888")
                def _on_img(img):
                    try:
                        from PIL import Image as _Image
                        thumb = img.copy()
                        thumb.thumbnail((col_width - 30, 280), _Image.Resampling.LANCZOS)
                        ctk_img = ctk.CTkImage(light_image=thumb, dark_image=thumb,
                                                size=(thumb.width, thumb.height))
                        lbl.configure(image=ctk_img, text="")
                        lbl.image = ctk_img  # evitar GC
                    except Exception as _e:
                        logger.debug(f"[silent] preview thumb: {_e}")
                        lbl.configure(text=tr("❌ Error mostrando"), text_color="#e74c3c")

                def _on_err(msg):
                    lbl.configure(text=f"❌ {msg[:60]}", text_color="#e74c3c")

                def _on_progress(msg):
                    lbl.configure(text=msg, text_color="#888")

                self.preview.generar(p, _on_img, _on_err, vent,
                                     on_progress=_on_progress)

            ctk.CTkButton(btn_row, text="📋", width=28, height=24, fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"], command=_copiar_completo).pack(side="left", padx=1)
            ctk.CTkButton(btn_row, text="🟢", width=28, height=24, fg_color="#1a5a2a", hover_color="#0f3a1a", command=_copiar_pos).pack(side="left", padx=1)
            if tiene_neg:
                ctk.CTkButton(btn_row, text="🔴", width=28, height=24, fg_color="#5a1a1a", hover_color="#3a0f0f", command=_copiar_neg).pack(side="left", padx=1)
            ctk.CTkButton(btn_row, text="🇪🇸", width=28, height=24, fg_color="#8e44ad", hover_color="#6a2a8a", command=_traducir).pack(side="left", padx=1)
            ctk.CTkButton(btn_row, text="👁", width=28, height=24, fg_color="#0891b2", hover_color="#0e7490", command=_preview_pollinations).pack(side="left", padx=1)
            ctk.CTkButton(btn_row, text=tr("✅ Usar"), width=56, height=24, fg_color="#1a7a3c", hover_color="#145e2d", font=ctk.CTkFont(size=10, weight="bold"), command=_usar).pack(side="right", padx=2)

        # Pie de ventana: botones extras (encadenar Board→Vídeo)
        # + Comparar 2 lado-a-lado + Cerrar comparador
        pie = ctk.CTkFrame(vent, fg_color="transparent")
        pie.pack(pady=(0, 10))
        if extra_botones:
            for label_btn, fg, cb in extra_botones:
                def _wrap(_cb=cb, _v=variaciones, _vent=vent):
                    try: _cb(_v, _vent)
                    except Exception as _e:
                        logger.exception(f"extra_boton {_e}")
                ctk.CTkButton(pie, text=label_btn, width=240, height=32,
                              fg_color=fg, hover_color=fg,
                              font=ctk.CTkFont(size=11, weight="bold"),
                              command=_wrap).pack(side="left", padx=6)

        # Botón "🆚 Comparar 2" — solo activo cuando hay 2 seleccionadas
        def _abrir_lado_a_lado():
            seleccionadas = [i for i, v in compare_vars.items() if v.get()]
            if len(seleccionadas) != 2:
                return
            i_a, i_b = seleccionadas
            label_a = labels[i_a] if labels and i_a < len(labels) and labels[i_a] else f"Variación #{i_a + 1}"
            label_b = labels[i_b] if labels and i_b < len(labels) and labels[i_b] else f"Variación #{i_b + 1}"
            self._abrir_diff_lado_a_lado(
                variaciones[i_a], variaciones[i_b], label_a, label_b
            )

        # Botón "🆚 Comparar 2": empieza disabled hasta marcar 2 cards.
        # Texto-pista en estado disabled + text_color_disabled explícito para
        # que el botón sea VISIBLE incluso disabled (antes el text_color
        # default + fg_color #4b5563 hacían que el botón se fundiera con
        # el fondo del pie del comparador — bug detectado sesión 18).
        compare_btn_ref["btn"] = ctk.CTkButton(
            pie, text=tr("🆚 Selecciona 2 cards para comparar"), width=240, height=32,
            fg_color="#4b5563", hover_color="#7c3aed",
            text_color="#e5e7eb",
            text_color_disabled="#cbd5e1",
            font=ctk.CTkFont(size=11, weight="bold"),
            state="disabled",
            command=_abrir_lado_a_lado,
        )
        compare_btn_ref["btn"].pack(side="left", padx=6)

        # Botón "👁 Grid Pollinations" — abre ventana con previews de TODOS
        def _abrir_grid():
            self.preview.abrir_grid(variaciones, labels)

        ctk.CTkButton(pie, text=tr("👁 Grid Pollinations"), width=180, height=32,
                      fg_color="#0891b2", hover_color="#0e7490",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=_abrir_grid).pack(side="left", padx=6)

        ctk.CTkButton(pie, text=tr("Cerrar comparador"), width=180, height=32,
                      fg_color="#6b7280", hover_color="#4b5563",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=vent.destroy).pack(side="left", padx=6)

        # ── Atajos del comparador (sesión 18 round 3 + fix round 4) ──
        # Ctrl+G  = abrir Grid Pollinations
        # Alt+C   = Comparar 2 lado-a-lado (solo si hay 2 marcadas).
        # Antes usaba Ctrl+Enter pero colisionaba con el atajo global
        # "Generar prompt" → duplicado en ventana de ayuda Ctrl+?
        vent.bind("<Control-g>", lambda e: _abrir_grid())
        def _atajo_comparar(_e=None):
            seleccionadas = [i for i, v in compare_vars.items() if v.get()]
            if len(seleccionadas) == 2:
                _abrir_lado_a_lado()
            else:
                self.set_estado(
                    tr('⚠️ Selecciona EXACTAMENTE 2 cards para comparar (hay {0} marcadas)').format(len(seleccionadas)),
                    "#e67e22",
                )
        vent.bind("<Alt-c>", _atajo_comparar)
        # Hint visual debajo del pie sobre los atajos disponibles
        ctk.CTkLabel(
            vent,
            text=tr("⌨️ Atajos: Ctrl+G = Grid · Alt+C = Comparar 2 · Esc = Cerrar"),
            font=ctk.CTkFont(size=9, slant="italic"),
            text_color=c["muted_text"],
        ).pack(pady=(2, 6))

    def _abrir_diff_lado_a_lado(self, texto_a, texto_b, label_a, label_b):
        """Ventana 50/50 con diff palabra-por-palabra entre 2 variantes.

        - Verde: tokens que están en B pero no en A (añadidos por B).
        - Rojo: tokens que están en A pero no en B (quitados en B).
        - Color normal: tokens comunes.

        Usa difflib.SequenceMatcher con tokenización por palabras +
        separadores conservados.
        """
        import re as _re
        from difflib import SequenceMatcher

        is_lt = ctk.get_appearance_mode().lower() == "light"
        from config import get_theme_colors
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self)
        vent.title(tr('🆚 {0}  vs  {1}').format((label_a), (label_b)))
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        ancho = min(1400, screen_w - 100)
        alto = min(800, screen_h - 100)
        vent.geometry(f"{ancho}x{alto}")
        vent.transient(self)

        ctk.CTkLabel(vent,
                     text=tr('🆚 Comparación lado a lado  ·  🟢 añadido en derecha  ·  🔴 quitado en derecha'),
                     font=ctk.CTkFont(size=12, weight="bold")
                     ).pack(pady=(8, 4))

        # Container 50/50
        cont = ctk.CTkFrame(vent, fg_color="transparent")
        cont.pack(fill="both", expand=True, padx=10, pady=5)

        # Tokenizar conservando espacios/saltos
        def _tokenize(t):
            return _re.findall(r"\S+|\s+", t or "")

        toks_a = _tokenize(texto_a)
        toks_b = _tokenize(texto_b)
        sm = SequenceMatcher(a=toks_a, b=toks_b, autojunk=False)
        ops = sm.get_opcodes()

        def _make_panel(parent, titulo, color_titulo):
            frame = ctk.CTkFrame(parent, fg_color=c["fg_frame"], corner_radius=8)
            frame.pack(side="left", fill="both", expand=True, padx=4)
            hdr = ctk.CTkFrame(frame, fg_color=color_titulo, corner_radius=6, height=28)
            hdr.pack(fill="x", padx=5, pady=(5, 3))
            hdr.pack_propagate(False)
            ctk.CTkLabel(hdr, text=f"  {titulo}",
                         font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=8)
            tb = ctk.CTkTextbox(frame, fg_color=c["fg_frame"],
                                 font=ctk.CTkFont(family="Consolas", size=11),
                                 wrap="word")
            tb.pack(fill="both", expand=True, padx=5, pady=(0, 5))
            tb._textbox.tag_config("eq",  foreground=c.get("muted_text", "#aaa"))
            tb._textbox.tag_config("del", foreground="#ffffff", background="#7f1d1d")
            tb._textbox.tag_config("ins", foreground="#ffffff", background="#166534")
            return tb

        tb_a = _make_panel(cont, label_a, "#1a4a7a")
        tb_b = _make_panel(cont, label_b, "#1a7a3c")

        for tag, i1, i2, j1, j2 in ops:
            seg_a = "".join(toks_a[i1:i2])
            seg_b = "".join(toks_b[j1:j2])
            if tag == "equal":
                tb_a._textbox.insert("end", seg_a, "eq")
                tb_b._textbox.insert("end", seg_b, "eq")
            elif tag == "delete":
                tb_a._textbox.insert("end", seg_a, "del")
                # nada en B
            elif tag == "insert":
                # nada en A
                tb_b._textbox.insert("end", seg_b, "ins")
            else:  # replace
                tb_a._textbox.insert("end", seg_a, "del")
                tb_b._textbox.insert("end", seg_b, "ins")

        tb_a.configure(state="disabled")
        tb_b.configure(state="disabled")

        # Botones pie
        pie = ctk.CTkFrame(vent, fg_color="transparent")
        pie.pack(pady=(0, 10))

        def _copiar_a():
            pyperclip.copy(texto_a)
            self.dialogs.set_estado(tr("✅ '{0}' copiada").format(label_a), "#2ecc71")

        def _copiar_b():
            pyperclip.copy(texto_b)
            self.dialogs.set_estado(tr("✅ '{0}' copiada").format(label_b), "#2ecc71")

        ctk.CTkButton(pie, text=tr('📋 Copiar {0}').format(label_a), width=200, height=30,
                      fg_color="#1a4a7a", hover_color="#0f2e4d",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      command=_copiar_a).pack(side="left", padx=4)
        ctk.CTkButton(pie, text=tr('📋 Copiar {0}').format(label_b), width=200, height=30,
                      fg_color="#1a7a3c", hover_color="#0f4a22",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      command=_copiar_b).pack(side="left", padx=4)
        ctk.CTkButton(pie, text=tr("Cerrar"), width=120, height=30,
                      fg_color="#6b7280", hover_color="#4b5563",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      command=vent.destroy).pack(side="left", padx=4)

    def _intentar_cambiar_modelo(self, nombre_modelo):
        """Cambia el combo del modelo activo si `nombre_modelo` existe en
        la lista del modo actual. Devuelve el nombre aplicado o None.
        Usado por el comparador para sincronizar modelo + prompt al pulsar
        "Usar" en una card que pertenezca a un modelo específico.
        """
        if not nombre_modelo:
            return None
        nombre = nombre_modelo.strip()
        modo = self.modo_var.get()
        try:
            if modo == "imagen" and hasattr(self, 'combo_modelo_imagen'):
                valores = list(self.combo_modelo_imagen.cget("values") or [])
                if nombre in valores:
                    self.combo_modelo_imagen.set(nombre)
                    if hasattr(self, '_on_modelo_imagen_cambio'):
                        self.events._on_modelo_imagen_cambio()
                    return nombre
            elif modo == "video" and hasattr(self, 'combo_modelo_video'):
                valores = list(self.combo_modelo_video.cget("values") or [])
                if nombre in valores:
                    self.combo_modelo_video.set(nombre)
                    return nombre
            elif modo == "audio" and hasattr(self, 'combo_modelo_audio'):
                valores = list(self.combo_modelo_audio.cget("values") or [])
                if nombre in valores:
                    self.combo_modelo_audio.set(nombre)
                    return nombre
        except Exception as _e:
            logger.debug(f"[silent _intentar_cambiar_modelo] {_e}")
        return None

    def _setup_wizard(self):
        """Wizard de primera vez cuando faltan API keys. Devuelve True si se configuraron.

        Pide cualquiera de los 5 proveedores soportados de entrada:
          • Gemini, Groq, GitHub Models — GRATIS
          • DeepSeek (~€0.14/1M), OpenRouter (100+ modelos)

        Con que el usuario rellene UNA, la app puede arrancar. El resto
        se pueden añadir luego desde el botón 🔑 del header.

        Las keys se guardan vía guardar_api_key() (api_clients.py):
        keyring del SO si está disponible, sino keys.json cifrado AES-256
        en ~/.arquitecto_prompts/. NO usamos .env porque el cwd del .exe
        es impredecible (especialmente en sandboxes / VMs).
        """
        from api_clients import guardar_api_key
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        wizard = GPromptWindow(self)
        wizard.title(tr("🧠 G-Prompt Studio — Configuración Inicial"))
        wizard.geometry("620x720")
        wizard.transient(self)
        wizard.grab_set()

        resultado = [False]

        ctk.CTkLabel(
            wizard,
            text=tr("🧠 ¡Bienvenido a G-Prompt Studio!"),
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(18, 4))
        ctk.CTkLabel(
            wizard,
            text=tr("Necesitas SOLO 1 API key para empezar.\n"
                 "Las marcadas 🏆 son completamente GRATIS."),
            font=ctk.CTkFont(size=11),
            text_color=c["muted_text"],
            justify="center",
        ).pack(pady=(0, 10))

        # Scroll: 5 proveedores + nombre = mucho contenido vertical
        scroll = ctk.CTkScrollableFrame(wizard, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=4)

        frame = ctk.CTkFrame(scroll)
        frame.pack(fill="x", padx=4, pady=4)

        ctk.CTkLabel(frame, text=tr("👤 ¿Cómo quieres que te llamemos?"),
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
        entry_nombre = ctk.CTkEntry(frame, width=520, placeholder_text=tr("Tu nombre o apodo (ej: Gustaafvito)"))
        entry_nombre.pack(padx=10)
        ctk.CTkLabel(frame, text=tr("Aparecerá en el saludo del dashboard. Puedes dejarlo vacío."),
                     font=ctk.CTkFont(size=10), text_color="#3498db").pack(anchor="w", padx=10, pady=(0, 8))

        # ── Definición declarativa de los 5 proveedores del wizard ──
        # (provider_id, label, placeholder, ayuda, formato_check_fn, nombre_legible)
        # provider_id se usa para guardar vía guardar_api_key() y luego
        # leer vía cargar_api_key() — mismo mecanismo que el botón 🔑 del
        # header, no dependiente de .env.
        PROVEEDORES_WIZARD = [
            (
                "gemini",
                "🏆 Gemini API Key (Google — GRATIS, 15 req/min):",
                "AIza...",
                "Consíguela en: aistudio.google.com/apikey  ·  formato: AIzaXXXXXX...",
                lambda k: k.startswith("AIza") and len(k) > 20,
                "Gemini",
            ),
            (
                "groq",
                "🏆 Groq API Key (GRATIS, 14.400 req/día):",
                "gsk_...",
                "Consíguela en: console.groq.com/keys  ·  Llama 3.3 70B muy rápido",
                lambda k: len(k) > 20,
                "Groq",
            ),
            (
                "github_models",
                "🏆 GitHub Token (GRATIS con cuenta GitHub):",
                "ghp_... o github_pat_...",
                "Consíguelo en: github.com/settings/tokens  ·  Acceso a OpenAI/Claude/Llama",
                lambda k: len(k) > 20,
                "GitHub Models",
            ),
            (
                "deepseek",
                "🥈 DeepSeek API Key (~€0.14/1M tokens):",
                "sk-...",
                "Consíguela en: platform.deepseek.com  ·  formato: sk-XXXXXX...",
                lambda k: k.startswith("sk-") and len(k) > 12,
                "DeepSeek",
            ),
            (
                "openrouter",
                "💎 OpenRouter API Key (opcional, 100+ modelos):",
                "sk-or-...",
                "Consíguela en: openrouter.ai/keys  ·  100+ modelos con una sola key",
                lambda k: k.startswith("sk-or-") and len(k) > 12,
                "OpenRouter",
            ),
        ]

        # Crear un Entry por proveedor y guardar referencia
        entries = {}  # provider_id -> (entry, check_fn, name)
        for provider_id, label, placeholder, ayuda, check_fn, nombre in PROVEEDORES_WIZARD:
            ctk.CTkLabel(frame, text=label,
                         font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(8, 2))
            entry = ctk.CTkEntry(frame, width=520, placeholder_text=placeholder, show="*")
            entry.pack(padx=10)
            ctk.CTkLabel(frame, text=ayuda,
                         font=ctk.CTkFont(size=10),
                         text_color="#3498db").pack(anchor="w", padx=10, pady=(0, 4))
            entries[provider_id] = (entry, check_fn, nombre)

        lbl_estado = ctk.CTkLabel(wizard, text="", font=ctk.CTkFont(size=11), text_color=c["muted_text"])
        lbl_estado.pack(pady=4)

        def _recoger_keys() -> dict[str, str]:
            """Devuelve {provider_id: valor} solo con las keys no vacías."""
            return {pid: e.get().strip() for pid, (e, _, _) in entries.items() if e.get().strip()}

        def _validar_formato(keys: dict[str, str]) -> tuple[bool, str]:
            """Valida que al menos haya una key y que las introducidas tengan formato razonable."""
            if not keys:
                return False, "⚠️ Introduce al menos una API key."
            for pid, valor in keys.items():
                _, check_fn, nombre = entries[pid]
                if not check_fn(valor):
                    return False, f"❌ La key de {nombre} parece incorrecta. Revisa el formato."
            return True, ""

        def _test_keys():
            """Test rápido contra la PRIMERA key que el usuario haya rellenado.

            Por orden: Gemini → Groq → GitHub → DeepSeek → OpenRouter. Si la
            primera key funciona, el usuario sabe que tiene al menos un
            proveedor operativo.
            """
            keys = _recoger_keys()
            ok, msg = _validar_formato(keys)
            if not ok:
                lbl_estado.configure(text=msg, text_color="#e74c3c")
                return

            # Toma la primera key del orden declarado
            primer_pid = next((pid for pid, *_ in PROVEEDORES_WIZARD if pid in keys), None)
            if not primer_pid:
                return
            primer_valor = keys[primer_pid]
            _, _, primer_nombre = entries[primer_pid]

            lbl_estado.configure(text=tr('⏳ Probando conexión a {0}...').format(primer_nombre), text_color="#3498db")
            wizard.update_idletasks()

            def _worker():
                # Timeout corto (15s) en todas las llamadas — si la sandbox/VM
                # o la red están lentas, el usuario no quiere esperar 10 min
                # (default del SDK de OpenAI).
                TEST_TIMEOUT = 15.0
                try:
                    if primer_pid == "gemini":
                        from google import genai as _genai
                        cli = _genai.Client(api_key=primer_valor)
                        cli.models.generate_content(model="gemini-2.0-flash-exp",
                                                    contents="Responde solo 'ok'")
                    elif primer_pid == "deepseek":
                        from openai import OpenAI
                        cli = OpenAI(api_key=primer_valor,
                                     base_url="https://api.deepseek.com",
                                     timeout=TEST_TIMEOUT)
                        cli.chat.completions.create(model="deepseek-chat",
                                                    messages=[{"role": "user", "content": "ok"}],
                                                    max_tokens=5)
                    elif primer_pid == "groq":
                        from openai import OpenAI
                        cli = OpenAI(api_key=primer_valor,
                                     base_url="https://api.groq.com/openai/v1",
                                     timeout=TEST_TIMEOUT)
                        cli.chat.completions.create(model="llama-3.3-70b-versatile",
                                                    messages=[{"role": "user", "content": "ok"}],
                                                    max_tokens=5)
                    elif primer_pid == "github_models":
                        from openai import OpenAI
                        cli = OpenAI(api_key=primer_valor,
                                     base_url="https://models.inference.ai.azure.com",
                                     timeout=TEST_TIMEOUT)
                        cli.chat.completions.create(model="gpt-4o-mini",
                                                    messages=[{"role": "user", "content": "ok"}],
                                                    max_tokens=5)
                    elif primer_pid == "openrouter":
                        from openai import OpenAI
                        cli = OpenAI(api_key=primer_valor,
                                     base_url="https://openrouter.ai/api/v1",
                                     timeout=TEST_TIMEOUT)
                        cli.chat.completions.create(model="meta-llama/llama-3.1-8b-instruct:free",
                                                    messages=[{"role": "user", "content": "ok"}],
                                                    max_tokens=5)

                    wizard.after(0, lambda: lbl_estado.configure(
                        text=tr('✅ Conexión OK con {0} — la key funciona.').format(primer_nombre),
                        text_color="#2ecc71"))
                except Exception as e:
                    err = str(e)[:100]
                    wizard.after(0, lambda: lbl_estado.configure(
                        text=tr('❌ Falló {0}: {1}').format((primer_nombre), (err)),
                        text_color="#e74c3c"))

            threading.Thread(target=_worker, daemon=True).start()

        def guardar():
            keys = _recoger_keys()
            ok, msg = _validar_formato(keys)
            if not ok:
                lbl_estado.configure(text=msg, text_color="#e74c3c")
                return

            # Guarda en keyring del SO (si está) o en keys.json cifrado
            # AES-256 en ~/.arquitecto_prompts/. Ubicación FIJA, no
            # depende del cwd del proceso (importante para .exe en
            # sandbox / VM donde el cwd es impredecible).
            guardadas = []
            for pid, valor in keys.items():
                _, _, nombre = entries[pid]
                try:
                    if guardar_api_key(pid, valor):
                        guardadas.append(nombre)
                except Exception as e:
                    lbl_estado.configure(text=tr('❌ Error guardando {0}: {1}').format((nombre), (e)), text_color="#e74c3c")
                    return

            if not guardadas:
                lbl_estado.configure(text=tr("❌ No se pudo guardar ninguna key."), text_color="#e74c3c")
                return

            try:
                nombre = entry_nombre.get().strip()
                if nombre:
                    prefs = self.store.cargar_preferencias() or {}
                    prefs["nombre"] = nombre
                    self.store.guardar_preferencias(prefs)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            resultado[0] = True
            wizard.destroy()

        def cancelar():
            wizard.destroy()

        btn_frame = ctk.CTkFrame(wizard, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text=tr("🧪 Test conexión"), width=140, height=36,
                      fg_color="#3498db", hover_color="#2980b9", command=_test_keys).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text=tr("✅ Guardar y Empezar"), width=200, height=36,
                      fg_color="#2ecc71", hover_color="#27ae60", command=guardar).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text=tr("❌ Cancelar"), width=110, height=36,
                      fg_color="#555", hover_color="#333", command=cancelar).pack(side="left", padx=6)

        wizard.wait_window()
        return resultado[0]

    def cmd_preferencias(self):
        ventana = GPromptWindow(self)
        ventana.title(tr("⚙️ Ajustes del Sistema"))
        ventana.geometry("500x400")
        ventana.transient(self)
        ventana.grab_set()

        # --- Sin tabs, solo un panel directo (API Keys ya están en 🔑 del header) ---
        tab_gen = ventana

        # Cerebro por defecto (dinámico desde LLM_PROVIDERS)
        try:
            from api_clients import LLM_PROVIDERS as _prefs_llm_providers
            _prefs_llm_labels = [info["label"] for info in _prefs_llm_providers.values()]
        except Exception:
            _prefs_llm_labels = ["DeepSeek V4", "Google Gemini", "OpenAI GPT-4o", "Local (Ollama)"]

        ctk.CTkLabel(tab_gen, text=tr("👤 Tu nombre (saludo del Dashboard):"),
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 2), padx=20)
        self.entry_nombre_pref = ctk.CTkEntry(tab_gen, width=250,
                                                placeholder_text=tr("Tu nombre o apodo"))
        try:
            _prefs_existentes = self.store.cargar_preferencias() or {}
            _nombre_actual = _prefs_existentes.get("nombre", "")
            if _nombre_actual:
                self.entry_nombre_pref.insert(0, _nombre_actual)
        except Exception as e:
            logger.debug(f"[silent] {e}")
        self.entry_nombre_pref.pack(anchor="w", padx=20)

        ctk.CTkLabel(tab_gen, text=tr("🧠 Cerebro por defecto al iniciar:"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 2), padx=20)
        self.combo_default_llm = ctk.CTkComboBox(tab_gen, values=_prefs_llm_labels, width=250)
        self.combo_default_llm.set(self.llm_var.get())
        self.combo_default_llm.pack(anchor="w", padx=20)

        ctk.CTkLabel(tab_gen, text=tr("▶️ Modo por defecto al iniciar:"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 2), padx=20)
        _modos_display = [tr("Audio"), tr("Imagen"), tr("Vídeo")]
        _modo_to_display = {"audio": tr("Audio"), "imagen": tr("Imagen"), "video": tr("Vídeo")}
        _modo_from_display = {tr("Audio"): "audio", tr("Imagen"): "imagen", tr("Vídeo"): "video"}
        self._modo_from_display = _modo_from_display
        self.combo_default_modo = ctk.CTkComboBox(tab_gen, values=_modos_display, width=250)
        self.combo_default_modo.set(_modo_to_display.get(self.modo_var.get(), tr("Imagen")))
        self.combo_default_modo.pack(anchor="w", padx=20)

        ctk.CTkLabel(tab_gen, text=tr("🎨 Tema de interfaz:"), font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 2), padx=20)
        _temas_display = ["Dark", "Light", "System"]
        _tema_to_display = {"dark": "Dark", "light": "Light", "system": "System"}
        _tema_from_display = {"Dark": "dark", "Light": "light", "System": "system"}
        self._tema_from_display = _tema_from_display
        self.combo_tema = ctk.CTkComboBox(tab_gen, values=_temas_display, width=250)
        tema_actual = ctk.get_appearance_mode().lower()
        self.combo_tema.set(_tema_to_display.get(tema_actual, "Dark"))
        self.combo_tema.pack(anchor="w", padx=20)

        # Estilo unificado con los switches del header (colores por tema)
        self.switch_sonido_var = ctk.BooleanVar(value=self._sonido_activo if hasattr(self, '_sonido_activo') else False)
        ctk.CTkSwitch(tab_gen, text=tr("🔔 Sonido al completar generación"),
                      variable=self.switch_sonido_var,
                      progress_color="#3498db",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      height=20, width=42, corner_radius=10,
                      button_length=8,
                      button_color="#e5e7eb",
                      button_hover_color="#f3f4f6",
                      border_width=1).pack(anchor="w", padx=10, pady=(15, 5))

        # ── Toggle: grabar vídeo de la sesión ──
        self.switch_video_sesion_var = ctk.BooleanVar(value=self._sesion_grabar_video if hasattr(self, '_sesion_grabar_video') else False)
        ctk.CTkSwitch(tab_gen, text=tr("🎥 Grabar vídeo (MP4) al usar 🎬 Sesión grabada"),
                      variable=self.switch_video_sesion_var,
                      progress_color="#e74c3c",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      height=20, width=42, corner_radius=10,
                      button_length=8,
                      button_color="#e5e7eb",
                      button_hover_color="#f3f4f6",
                      border_width=1).pack(anchor="w", padx=10, pady=(5, 2))
        ctk.CTkLabel(tab_gen,
                     text=tr("    Captura toda la pantalla a 5 FPS (MP4 H.264). Requiere: pip install mss imageio[ffmpeg]"),
                     font=ctk.CTkFont(size=9, slant="italic"), text_color="#888").pack(anchor="w", padx=10)

        ctk.CTkLabel(tab_gen, text=tr("📁 Ruta de ComfyUI (opcional, para auto-discovery):"),
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 2), padx=20)

        frame_ruta = ctk.CTkFrame(tab_gen, fg_color="transparent")
        frame_ruta.pack(anchor="w", padx=20, fill="x")

        self.entry_comfyui_path = ctk.CTkEntry(frame_ruta, width=300, placeholder_text=tr("C:\\ComfyUI o vacío si no usas"))
        prefs_exist = self.store.cargar_preferencias() or {}
        ruta_actual = prefs_exist.get("comfyui_path", "") or ""
        if ruta_actual:
            self.entry_comfyui_path.insert(0, ruta_actual)
        self.entry_comfyui_path.pack(side="left", fill="x", expand=True)

        def _seleccionar_carpeta():
            from tkinter import filedialog
            carpeta = filedialog.askdirectory(title=tr("Selecciona carpeta de ComfyUI"))
            if carpeta:
                self.entry_comfyui_path.delete(0, "end")
                self.entry_comfyui_path.insert(0, carpeta)

        ctk.CTkButton(frame_ruta, text="📂", width=35, command=_seleccionar_carpeta).pack(side="left", padx=(5, 0))

        ctk.CTkLabel(tab_gen,
                     text=tr("    Si seleccionas tu carpeta de ComfyUI, los modelos se detectan automáticamente."),
                     font=ctk.CTkFont(size=9, slant="italic"), text_color="#888").pack(anchor="w", padx=10)

        # Botón Guardar Abajo
        btn_guardar = ctk.CTkButton(ventana, text=tr("💾 Guardar Preferencias"), fg_color="#2ecc71", hover_color="#27ae60", command=lambda: self._guardar_y_cerrar_preferencias(ventana))
        btn_guardar.pack(pady=(0, 20))

    def _guardar_y_cerrar_preferencias(self, ventana):
        nuevo_llm = self.combo_default_llm.get()

        # Aplicar cerebro
        self.llm_var.set(nuevo_llm)
        self._on_llm_cambio(label=nuevo_llm)

        # Aplicar modo (mapear display → internal)
        _modo_from_display = getattr(self, '_modo_from_display',
                                     {tr("Audio"): "audio", tr("Imagen"): "imagen", tr("Vídeo"): "video"})
        nuevo_modo = _modo_from_display.get(self.combo_default_modo.get(), "imagen")
        if self.modo_var.get() != nuevo_modo:
            self.modo_var.set(nuevo_modo)
            self.events._on_modo_cambio()

        # Aplicar tema (mapear display → internal)
        if hasattr(self, 'combo_tema'):
            _tema_from_display = getattr(self, '_tema_from_display', {"Dark": "dark", "Light": "light", "System": "system"})
            nuevo_tema = _tema_from_display.get(self.combo_tema.get(), "dark")
            ctk.set_appearance_mode(nuevo_tema)
            try:
                self.after(50, self._apply_theme_colors)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        # Aplicar sonido
        if hasattr(self, 'switch_sonido_var'):
            self._sonido_activo = self.switch_sonido_var.get()

        # Aplicar grabación de vídeo de sesión
        if hasattr(self, 'switch_video_sesion_var'):
            self._sesion_grabar_video = self.switch_video_sesion_var.get()

        # Aplicar ruta de ComfyUI y auto-discovery (un solo escaneo)
        total_modelos = 0
        if hasattr(self, 'entry_comfyui_path'):
            ruta_comfy = self.entry_comfyui_path.get().strip()
            prefs_n = self.store.cargar_preferencias() or {}
            prefs_n["comfyui_path"] = ruta_comfy
            self.store.guardar_preferencias(prefs_n)

            if ruta_comfy:
                from config import escanear_modelos_comfyui
                grupos_img, grupos_vid = escanear_modelos_comfyui(ruta_comfy, prefs_n)
                if grupos_img:
                    total_modelos += sum(len(m) for _, m in grupos_img)
                if grupos_vid:
                    total_modelos += sum(len(m) for _, m in grupos_vid)

        try:
            if hasattr(self, 'entry_nombre_pref'):
                nuevo_nombre = self.entry_nombre_pref.get().strip()
                prefs_n = self.store.cargar_preferencias() or {}
                if nuevo_nombre:
                    prefs_n["nombre"] = nuevo_nombre
                else:
                    # Si lo deja vacío, marcar como "Creador" para no preguntar más
                    prefs_n["nombre"] = "Creador"
                self.store.guardar_preferencias(prefs_n)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # Guardar las preferencias usando el sistema de persistence.py
        self.data._guardar_preferencias()

        if total_modelos > 0:
            self.dialogs.set_estado(tr('⚙️ Preferencias guardadas. ComfyUI: {0} modelos detectados. (API Keys → 🔑)').format(total_modelos), "#2ecc71")
        else:
            self.dialogs.set_estado(tr("⚙️ Preferencias guardadas correctamente. (API Keys → botón 🔑 del header)"), "#2ecc71")
        ventana.destroy()

    def cmd_previsualizar(self):
        """Preview con caché en memoria, URL Pollinations copiable y
        botón para abrir en navegador.

        Mejoras v2:
        - Caché in-memory (max 20 entradas). Misma prompt → respuesta
          instantánea sin llamar a la API.
        - Ventana de preview muestra la URL Pollinations.
        - Botones "🔗 Copiar URL" y "🌐 Abrir en navegador".
        - Indica si viene de caché.
        """
        prompt_actual = self.txt_salida.get("1.0", "end").strip()

        if not prompt_actual:
            return self.dialogs.set_estado(tr("⚠️ Genera un prompt primero para poder previsualizarlo."), "#e67e22")

        if self.modo_var.get() == "audio":
            return self.dialogs.set_estado(tr("⚠️ La previsualización solo está disponible para Imágenes y Vídeos."), "#e67e22")
        try: self.sesion._sesion_log("🎨 Previsualizó (boceto rápido)")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        # Inicializar caché si no existe
        if not hasattr(self, "_preview_cache"):
            self._preview_cache = {}  # key=hash → (image_pil, url, ts)

        import hashlib

        # Limpieza del prompt (idéntica a la original, necesaria también
        # para el cache-key y la URL)
        texto_limpio = prompt_actual.split("NEGATIVE PROMPT:")[0]
        texto_limpio = texto_limpio.replace("PROMPT:", "").replace("POSITIVE PROMPT:", "")
        texto_limpio = texto_limpio.replace("\n", " ").replace("\r", " ").replace("*", "")
        texto_limpio = " ".join(texto_limpio.split())
        if len(texto_limpio) > 400:
            texto_limpio = texto_limpio[:400]
        cache_key = hashlib.md5(texto_limpio.encode("utf-8")).hexdigest()

        # Cache hit → mostrar instantáneamente (TTL 30 min)
        _PREVIEW_CACHE_TTL = 1800  # segundos
        if cache_key in self._preview_cache:
            image_pil, url_imagen, ts = self._preview_cache[cache_key]
            import time as _time_ttl
            if _time_ttl.time() - ts <= _PREVIEW_CACHE_TTL:
                img_ctk = ctk.CTkImage(light_image=image_pil, dark_image=image_pil, size=(512, 512))
                self.preview.mostrar_window(image_pil, img_ctk, url_imagen, desde_cache=True)
                self.dialogs.set_estado(tr("📥 Preview desde caché (sin llamada a API)"), "#2ecc71")
                return
            else:
                # Entrada expirada: eliminar y regenerar
                del self._preview_cache[cache_key]

        self.dialogs.set_estado(tr("🎨 Previsualizando... Esto puede tardar unos 10-15 segundos."), "#9b59b6")
        self.dialogs.toggle_botones(False)

        # Usa el helper unificado (semáforo + retry con backoff).
        # URL para mostrar al usuario se reconstruye después con el modelo
        # adecuado al endpoint (legacy: turbo, autenticado: flux).
        import time
        import urllib.parse as _up
        try:
            from api_clients import cargar_api_key
            _tiene_key = bool(cargar_api_key("pollinations"))
        except Exception:
            _tiene_key = False
        semilla = int(time.time())
        if _tiene_key:
            url_imagen = (
                f"https://gen.pollinations.ai/image/{_up.quote(texto_limpio)}"
                f"?width=512&height=512&nologo=true&model=flux&seed={semilla}"
                f"&referrer=gprompt-studio"
            )
        else:
            url_imagen = (
                f"https://image.pollinations.ai/prompt/{_up.quote(texto_limpio)}"
                f"?width=512&height=512&nologo=true&model=turbo&seed={semilla}"
                f"&referrer=gprompt-studio"
            )

        def _on_img(image_pil):
            try:
                img_ctk = ctk.CTkImage(light_image=image_pil, dark_image=image_pil, size=(512, 512))
                # Cache LRU 20 entradas
                if len(self._preview_cache) >= 20:
                    oldest = min(self._preview_cache.items(), key=lambda kv: kv[1][2])
                    del self._preview_cache[oldest[0]]
                self._preview_cache[cache_key] = (image_pil, url_imagen, time.time())
                self.preview.mostrar_window(image_pil, img_ctk, url_imagen,
                                            desde_cache=False)
                self.dialogs.set_estado(tr("✅ Previsualización generada con éxito."), "#2ecc71")
            except Exception as e:
                self.dialogs.set_estado(tr('❌ Error mostrando preview: {0}').format(e), "#e74c3c")
            finally:
                self.dialogs.toggle_botones(True)

        def _on_err(msg):
            self.dialogs.set_estado(tr('❌ Error al generar imagen: {0}').format(msg), "#e74c3c")
            self.dialogs.toggle_botones(True)

        # `texto_limpio` ya viene normalizado: lo pasamos a self.preview.generar
        # (su extracción de POSITIVE no es necesaria porque limpiamos arriba).
        self.preview.generar(
            texto_limpio, _on_img, _on_err, self, size=512
        )
