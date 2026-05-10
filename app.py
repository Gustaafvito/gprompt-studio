"""
G-Prompt Studio v1.0 — Aplicación principal.
Clase ArquitectoApp encapsula toda la interfaz y lógica.

Cambios v1.0 vs v8.x:
- FIX: ventanas hijas (Toplevel) ahora aparecen siempre al frente.
- FIX: eliminado _build_header duplicado entre app.py y UIBuildersMixin.
- NEW: indicador visual del proveedor LLM activo (✅ verde / ⚠️ amarillo).
- NEW: helper open_child_window() para crear Toplevel correctamente.
- NEW: sistema de toast in-app no bloqueante (self.show_toast()).
- NEW: atajo Ctrl+Enter desde el textarea de idea = generar prompt.
- NEW: backup automático semanal de ~/.gpromptstudio/.
- NEW: cierre limpio de threads al cerrar la app.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image
import pyperclip
import threading
import datetime
import random
import re
from pathlib import Path

# Importación segura de Tooltips
try:
    from CTkToolTip import CTkToolTip
except ImportError:
    class CTkToolTip:
        def __init__(self, *args, **kwargs): pass

from config import (
    APP_TITLE, VERSION, PUBLIC_VERSION,
    MODELOS_IMAGEN_FLAT, MODELOS_VIDEO_FLAT, MODELOS_AUDIO_FLAT,
    MODELOS_IMAGEN_COMFYUI_FLAT, MODELOS_VIDEO_COMFYUI_FLAT,
    MODELOS_POR_PLATAFORMA_IMAGEN,
    RATIOS_IMAGEN, RATIOS_VIDEO,
    ESTILOS_IMAGEN, ESTILOS_VIDEO, ESTILOS_AUDIO,
    NEGATIVE_PRESETS, PRESET_COLORES, es_separador,
    PLATAFORMAS_IMAGEN, PLATAFORMAS_IMAGEN_LISTA,
    PLATAFORMAS_VIDEO, PLATAFORMAS_VIDEO_LISTA,
    PLATAFORMAS_AUDIO, PLATAFORMAS_AUDIO_LISTA,
    MOTORES_VIDEO, MOTORES_AUDIO, MOTOR_DEFAULT,
    AUTHOR, ESTILO_NEGATIVO_AUTO,
    TOKEN_LIMITS, MODEL_SPECS, MODEL_SPECS_IMAGEN, MODEL_SPECS_AUDIO,
    get_model_specs, get_image_model_specs, get_audio_model_specs,
    get_prompt_template,
    get_theme_colors,
    DESTINOS, EMOCIONES_AUDIO, VOCES_AUDIO, IDIOMAS_AUDIO,
    PROMPT_TEMPLATES, BIBLIOTECA_EJEMPLOS,
)
from prompts import (
    SYSTEM_IMAGEN_SFW, SYSTEM_IMAGEN_NSFW, SYSTEM_VIDEO,
    SYSTEM_VIDEO_NSFW,
    SYSTEM_NATURAL_SFW, SYSTEM_NATURAL_NSFW, SYSTEM_NATURAL_VIDEO,
    SYSTEM_NATURAL_VIDEO_NSFW,
    SYSTEM_AUDIO_SUNO, SYSTEM_AUDIO_SEAART,
    NEGATIVE_BASE_SFW, NEGATIVE_BASE_NSFW, NEGATIVE_BASE_VIDEO,
    BRIEF_MODIFIER, REGLAS_APROVECHAR_BUDGET,
)
from persistence import DataStore
from api_clients import APIClients
from workers import (
    DeepSeekWorker, VisionChain, contar_tokens_aprox,
    limpiar_marcadores, parsear_ideas, detectar_idioma_es,
)
from windows import abrir_personajes, abrir_loras, abrir_batch, abrir_lista


# ══════════════════════════════════════════════════════════════
# Parche global v1.0.4 — Ventanas hijas: AL FRENTE + MAXIMIZABLES
#
# Historial:
# - v8.x: ventanas hijas salían DETRÁS (bug original)
# - v1.0:  fix con transient(master) → ventanas al frente PERO no se podían
#          maximizar (Windows oculta los botones cuando hay transient)
# - v1.0.4: SIN transient + lift() + topmost momentáneo → al frente Y
#          maximizables Y con barra completa de Windows
#
# La clave: después de crear la Toplevel, hacemos un truco visual de
# "topmost momentáneo" (200ms) que la fuerza al frente sin bloquearla
# permanentemente. La ventana NO es transient → tiene minimize/maximize
# completos. Cuando el usuario hace alt+tab a otra app, la ventana queda
# atrás como cualquier ventana normal.
# ══════════════════════════════════════════════════════════════
_original_ctk_toplevel_init = ctk.CTkToplevel.__init__
_original_ctk_toplevel_transient = ctk.CTkToplevel.transient

def _patched_ctk_toplevel_init(self, *args, **kwargs):
    _original_ctk_toplevel_init(self, *args, **kwargs)
    # Asegurar redimensionable y barra completa de Windows
    try:
        self.resizable(True, True)
    except Exception:
        pass
    # Forzar al frente justo después del init
    try:
        self.after(50, lambda: _bring_to_front(self))
    except Exception:
        pass
    # v1.0.5 — atajos GLOBALES de pantalla completa para CUALQUIER Toplevel
    # (antes solo estaban en open_child_window que no se usa en todas las ventanas)
    def _toggle_fs(event=None, w=self):
        try:
            actual = bool(w.attributes("-fullscreen"))
            w.attributes("-fullscreen", not actual)
        except Exception:
            pass
        return "break"

    def _exit_fs(event=None, w=self):
        try:
            if bool(w.attributes("-fullscreen")):
                w.attributes("-fullscreen", False)
                return "break"
        except Exception:
            pass

    try:
        self.bind("<F11>", _toggle_fs)
        self.bind("<Escape>", _exit_fs)
    except Exception:
        pass

def _bring_to_front(top):
    """Traer ventana al frente sin bloquearla con -topmost permanente."""
    try:
        if not top.winfo_exists():
            return
        top.lift()
        top.attributes("-topmost", True)
        # Quitar topmost después de 250ms — tiempo suficiente para que el
        # WM la ponga delante, pero no tanto que moleste cuando el usuario
        # quiere cambiar a otra app
        top.after(250, lambda: top.attributes("-topmost", False) if top.winfo_exists() else None)
        try:
            top.focus_force()
        except Exception:
            pass
    except Exception:
        pass

def _patched_ctk_toplevel_transient(self, master=None):
    """v1.0.4: NO llamamos al transient original.

    Razón: con transient activo, Windows oculta los botones de
    minimize/maximize de la ventana. Sin transient, la ventana mantiene
    los 3 botones (minimize, maximize, close) y se puede poner en
    pantalla completa con doble-click en la barra de título.

    A cambio, perdemos la asociación automática al padre. Lo compensamos
    con _bring_to_front() que la fuerza al frente al crearse.
    """
    # NO llamamos al original transient — eso quitaría minimize/maximize
    # En Windows, asegurar que NO se trate como tool window
    try:
        self.attributes("-toolwindow", False)
    except Exception:
        pass
    # Forzar al frente otra vez tras el transient (que no hace nada ahora)
    try:
        self.after(60, lambda: _bring_to_front(self))
    except Exception:
        pass

ctk.CTkToplevel.__init__ = _patched_ctk_toplevel_init
ctk.CTkToplevel.transient = _patched_ctk_toplevel_transient


from modules import (
    UIBuildersMixin, ToolsCreativeMixin, ToolsWorkflowMixin,
    ToolsAnalysisMixin, DataMgmtMixin, BackupExportMixin,
    DialogsMixin, CoreMixin
)


class ArquitectoApp(
    ctk.CTk,
    UIBuildersMixin,
    ToolsCreativeMixin,
    ToolsWorkflowMixin,
    ToolsAnalysisMixin,
    DataMgmtMixin,
    BackupExportMixin,
    DialogsMixin,
    CoreMixin,
):

    def __init__(self):
        super().__init__()

        # v1.0.5 — splash inicial usando withdraw() de la ventana principal.
        # En v1.0 metimos un splash con root temporal que generaba errores
        # 'invalid command name'. Ahora ocultamos la ventana principal y
        # mostramos un Toplevel splash mientras construimos la UI.
        try:
            self.withdraw()
            self._splash = self._crear_splash()
        except Exception:
            self._splash = None

        # Silenciar errores inofensivos de CTkToolTip con widgets destruidos
        def _silenciar_errores_tooltip(exc, val, tb):
            msg = str(val)
            if "bad window path" in msg or "ctktooltip" in msg.lower():
                return  # Ignorar errores de tooltip
            import traceback
            traceback.print_exception(exc, val, tb)
        self.report_callback_exception = _silenciar_errores_tooltip

        self._splash_estado("Inicializando proveedores...")

        # ── Dependencias ──────────────────────────────────────────
        self.clients = APIClients()
        if self.clients.error:
            self._cerrar_splash()
            self.deiconify()
            # En vez de cerrar, mostrar wizard de configuración
            if not self._setup_wizard():
                self.destroy()
                return
            # Reintentar con las claves nuevas
            self.clients = APIClients()
            if self.clients.error:
                messagebox.showerror("Error de configuración", self.clients.error)
                self.destroy()
                return

        self._splash_estado("Cargando datos...")
        self.store    = DataStore()
        self.deepseek = DeepSeekWorker(self.clients)
        self.vision   = VisionChain(self.clients)

        # ── Estado ────────────────────────────────────────────────
        self.imagen_cargada         = None
        self._progreso_activo       = False
        self._token_pending         = None
        self._ultimo_anclaje_visual = None  
        self._anclaje_visual = None  # ADN visual (rasgos inmutables)

        # ── Ventana ───────────────────────────────────────────────
        self.title(APP_TITLE)
        self._aplicar_geometria_adaptativa()
        # minsize bajo para que la app SIEMPRE entre en pantallas HD (1366x768)
        self.minsize(820, 620)
        self._splash_estado("Construyendo interfaz...")

        # ── Variables Tk ──────────────────────────────────────────
        self.llm_var             = ctk.StringVar(value="DeepSeek V3")
        self.modo_var            = ctk.StringVar(value="imagen")
        self.plataforma_var      = ctk.StringVar(value="SeaArt / Tensor.Art")
        self.switch_nsfw_var     = ctk.BooleanVar(value=False)
        self.duracion_var        = ctk.StringVar(value="10s")
        self.ratio_var           = ctk.StringVar(value="1:1")
        self.switch_traduccion_var = ctk.BooleanVar(value=True)
        self.destino_var         = ctk.StringVar(value="— Personal —")
        self.brief_var           = ctk.BooleanVar(value=False)
        self.estilo_checks       = {}
        self.preset_vars         = {}
        self.preset_btns         = {}

        # ── Mejora 14: traces para sesión grabada (ratio/destino/NSFW/brief) ──
        try:
            self.ratio_var.trace_add("write", lambda *a: self._sesion_log(f"📐 Cambió ratio → {self.ratio_var.get()}") if hasattr(self, "_sesion_eventos") else None)
            self.destino_var.trace_add("write", lambda *a: self._sesion_log(f"🎯 Cambió destino → {self.destino_var.get()}") if hasattr(self, "_sesion_eventos") else None)
            self.switch_nsfw_var.trace_add("write", lambda *a: self._sesion_log(f"🔞 NSFW → {'ON' if self.switch_nsfw_var.get() else 'OFF'}") if hasattr(self, "_sesion_eventos") else None)
            self.switch_traduccion_var.trace_add("write", lambda *a: self._sesion_log(f"🌐 Auto-trad → {'ON' if self.switch_traduccion_var.get() else 'OFF'}") if hasattr(self, "_sesion_eventos") else None)
            self.brief_var.trace_add("write", lambda *a: self._sesion_log(f"📋 Modo Brief → {'ON' if self.brief_var.get() else 'OFF'}") if hasattr(self, "_sesion_eventos") else None)
        except Exception:
            pass

        # ── Construir UI Organizada ───────────────────────────────
        self._build_author()
        self._build_footer()

        # Zona 1: Contexto Global
        self._build_header()
        self._build_modo()

        self._build_video_panel()
        self._build_audio_panel()
        self._build_modelo_imagen_panel()
        self._build_destino_panel()

        self.lbl_img_model_info = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=10),
                                                text_color="#3498db",
                                                corner_radius=6, wraplength=1800,
                                                justify="left", anchor="w")

        # Zona 2: Modificadores y Ajustes (Pestañas Centrales)
        self._build_tabs_centrales()

        # Zona 3: Ideación y Acción
        self._build_imagen_ref()
        self._build_entrada()
        self._build_acciones()
        self._build_estado()
        self._build_salida()

        # ── Atajos ────────────────────────────────────────────────
        self._bind_shortcuts()

        # ── Inicializar ───────────────────────────────────────────
        self.actualizar_combo_personajes()
        self.actualizar_combo_loras()
        self.actualizar_combo_plantillas()

        # Cargar estado y forzar pintado correcto
        self._cargar_preferencias()
        self._on_modo_cambio()
        self.reiniciar_memoria()

        # v1.0.5 — Aplicar tema actual a TODOS los widgets construidos.
        # Sin esto, si el usuario arranca con tema claro guardado, los
        # widgets que tienen colores hardcodeados de modo dark salen
        # con texto blanco sobre fondo claro = invisibles.
        try:
            self._apply_theme_colors()
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).warning(f"_apply_theme_colors inicial falló: {e}")

        # Restaurar borrador no guardado de sesión anterior si existe
        self._restaurar_borrador()
        # Iniciar auto-guardado cada 30s
        self.after(30000, self._auto_guardar_borrador)

        # Backup automático semanal (v1.0)
        self.after(5000, self._backup_semanal_check)

        # Atajo global Ctrl+Enter para generar prompt (v1.0)
        try:
            self.bind_all("<Control-Return>", self._atajo_generar_prompt, add="+")
        except Exception:
            pass

        # v1.0.5 — F11 en la ventana principal para pantalla completa
        try:
            self.bind("<F11>", self._toggle_fullscreen_principal)
            self.bind("<Escape>", self._exit_fullscreen_principal)
        except Exception:
            pass

        # Indicador de proveedor activo (v1.0)
        self.after(800, self._actualizar_indicador_proveedor)

        self.protocol("WM_DELETE_WINDOW", self._on_cerrar)

        # v1.0.5 — Cerrar splash y mostrar la ventana principal
        try:
            self._splash_estado("¡Listo!")
            self.after(150, self._cerrar_splash)
            self.after(180, self.deiconify)
            self.after(220, lambda: self.lift())
            self.after(250, lambda: self.focus_force())
        except Exception:
            try:
                self.deiconify()
            except Exception:
                pass

        # ── v1.0.8 — Marcar fin de inicialización ────────────────────
        # Este flag lo lee _get_real_is_light() en ui_builders.py para
        # decidir si fiarse de ctk.get_appearance_mode() (post-init,
        # cuando el toggle de tema en caliente debe respetarse) o leer
        # preferencias.json (durante init, cuando hay race condition con
        # set_appearance_mode diferido). Lo seteamos con un delay
        # generoso (800ms) para asegurarnos de que el set_appearance_mode
        # diferido (200ms) ya disparó.
        def _marcar_init_completo():
            try:
                import sys
                app_mod = sys.modules.get('app')
                if app_mod is not None:
                    setattr(app_mod, '_gprompt_init_done', True)
                main_mod = sys.modules.get('__main__')
                if main_mod is not None:
                    setattr(main_mod, '_gprompt_init_done', True)
            except Exception:
                pass
        self.after(900, _marcar_init_completo)

        # v1.0.8 — Si NO hay nombre guardado, mostrar mini-wizard al cabo
        # de 1.2s (cuando todo está cargado y la ventana visible).
        try:
            prefs_actuales = self.store.cargar_preferencias() or {}
            if not prefs_actuales.get("nombre"):
                self.after(1200, self._wizard_nombre)
        except Exception:
            pass

    def _wizard_nombre(self):
        """Mini-wizard que pregunta el nombre del usuario para personalizar saludos.
        Solo se muestra si no hay nombre guardado en preferences.json.
        """
        try:
            prefs = self.store.cargar_preferencias() or {}
            if prefs.get("nombre"):
                return  # Ya tiene nombre, no molestar
        except Exception:
            pass

        try:
            is_lt = ctk.get_appearance_mode().lower() == "light"
            from config import get_theme_colors
            c = get_theme_colors(is_lt)
        except Exception:
            c = {"muted_text": "#888", "panel_text": "#e5e7eb", "panel_bg": "#0a0e14"}

        win = ctk.CTkToplevel(self)
        win.title("👋 Bienvenida")
        win.geometry("440x230")
        win.transient(self)
        try: win.grab_set()
        except Exception: pass

        ctk.CTkLabel(win, text="👋 ¡Hola!",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(win, text="¿Cómo quieres que te llamemos?",
                     font=ctk.CTkFont(size=12),
                     text_color=c.get("muted_text")).pack(pady=(0, 4))
        ctk.CTkLabel(win, text="Aparecerá en el saludo del Dashboard.",
                     font=ctk.CTkFont(size=10),
                     text_color=c.get("muted_text")).pack(pady=(0, 12))

        entry = ctk.CTkEntry(win, width=300, height=34,
                              placeholder_text="Tu nombre o apodo",
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
            except Exception:
                pass
            win.destroy()

        entry.bind("<Return>", _guardar)

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=14)
        ctk.CTkButton(btn_frame, text="✅ Guardar", width=130, height=32,
                      fg_color="#2ecc71", hover_color="#27ae60",
                      command=_guardar).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Saltar", width=80, height=32,
                      fg_color="#6b7280", hover_color="#4b5563",
                      command=_guardar).pack(side="left", padx=4)

    # ══════════════════════════════════════════════════════════════
    # v1.0.5 — Splash screen integrado
    # ══════════════════════════════════════════════════════════════

    def _crear_splash(self):
        """Crea splash screen como Toplevel SIN parent root temporal."""
        try:
            splash = ctk.CTkToplevel(self)
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
            ctk.CTkLabel(frame, text="G-Prompt Studio",
                         font=ctk.CTkFont(size=20, weight="bold"),
                         text_color="#e5e7eb").pack()

            # Versión
            from config import PUBLIC_VERSION
            ctk.CTkLabel(frame, text=f"v{PUBLIC_VERSION}",
                         font=ctk.CTkFont(size=11),
                         text_color="#3b82f6").pack()

            # Estado
            splash._lbl_estado = ctk.CTkLabel(
                frame, text="Iniciando...",
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
        except Exception:
            pass

    def _cerrar_splash(self):
        """Cierra el splash screen."""
        try:
            if self._splash and self._splash.winfo_exists():
                try:
                    self._splash._pb.stop()
                except Exception:
                    pass
                self._splash.destroy()
                self._splash = None
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════
    # NEW v1.0 — Helpers para ventanas hijas, toasts, atajos
    # ══════════════════════════════════════════════════════════════

    def _aplicar_geometria_adaptativa(self):
        """v1.0.3: calcula tamaño y posición inicial según el monitor.

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
            except Exception:
                pass

        except Exception as e:
            # Fallback a tamaño tradicional si algo falla
            try:
                import logging as _log
                _log.getLogger(__name__).warning(f"Geometría adaptativa falló: {e}")
            except Exception:
                pass
            self.geometry("1060x900")

    def open_child_window(self, title: str = "", size: str = "800x600",
                          transient: bool = True, modal: bool = False) -> ctk.CTkToplevel:
        """
        Crea un CTkToplevel correctamente configurado:
        - Título y tamaño
        - Transient(self) si transient=True (lo asocia a la ventana principal)
        - grab_set() si modal=True (bloquea la principal)
        - Garantiza que aparece AL FRENTE (gracias al patch global)
        - v1.0.4: F11 = toggle pantalla completa, Escape = salir de fullscreen

        Use:
            v = self.open_child_window("Mi ventana", "600x400")
            ctk.CTkLabel(v, text="hola").pack()
        """
        v = ctk.CTkToplevel(self)
        if title:
            v.title(title)
        if size:
            v.geometry(size)
        if transient:
            v.transient(self)  # Patched para no ocultar minimize/maximize
        if modal:
            try:
                v.grab_set()
            except Exception:
                pass

        # v1.0.4 — atajos de pantalla completa para CUALQUIER ventana hija
        def _toggle_fullscreen(event=None):
            try:
                actual = bool(v.attributes("-fullscreen"))
                v.attributes("-fullscreen", not actual)
            except Exception:
                pass
            return "break"

        def _exit_fullscreen(event=None):
            try:
                if bool(v.attributes("-fullscreen")):
                    v.attributes("-fullscreen", False)
                    return "break"
            except Exception:
                pass

        try:
            v.bind("<F11>", _toggle_fullscreen)
            v.bind("<Escape>", _exit_fullscreen)
        except Exception:
            pass

        # El patch global ya hace lift+focus, pero lo reforzamos
        try:
            v.after(80, lambda: v.lift() if v.winfo_exists() else None)
            v.after(120, lambda: v.focus_force() if v.winfo_exists() else None)
        except Exception:
            pass
        return v

    def show_toast(self, mensaje: str, color: str = "#2563eb", duracion_ms: int = 2500):
        """Toast in-app no bloqueante (esquina inferior derecha)."""
        try:
            # Cerrar toast previo si existe
            prev = getattr(self, "_toast_actual", None)
            if prev:
                try:
                    prev.destroy()
                except Exception:
                    pass

            toast = ctk.CTkToplevel(self)
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
            except Exception:
                pass

            self._toast_actual = toast
            toast.after(duracion_ms, lambda: toast.destroy() if toast.winfo_exists() else None)
        except Exception:
            pass

    def _toggle_fullscreen_principal(self, event=None):
        """v1.0.5: F11 en ventana principal = toggle pantalla completa."""
        try:
            actual = bool(self.attributes("-fullscreen"))
            self.attributes("-fullscreen", not actual)
            if hasattr(self, "show_toast"):
                msg = "📺 Pantalla completa (F11/Esc para salir)" if not actual else "↩️ Salida pantalla completa"
                try: self.show_toast(msg, "#3b82f6", 1500)
                except Exception: pass
        except Exception:
            pass
        return "break"

    def _exit_fullscreen_principal(self, event=None):
        """v1.0.5: Escape sale de pantalla completa si está activo."""
        try:
            if bool(self.attributes("-fullscreen")):
                self.attributes("-fullscreen", False)
                return "break"
        except Exception:
            pass

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
        except Exception:
            pass

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
            except Exception:
                pass
        except Exception:
            pass

    def _backup_semanal_check(self):
        """Si han pasado >7 días desde el último backup, crea uno automático."""
        try:
            import time
            base = Path.home() / ".gpromptstudio"
            if not base.exists():
                return
            marker = base / "_last_autobackup.txt"
            ahora = time.time()
            necesario = True
            if marker.exists():
                try:
                    last = float(marker.read_text(encoding="utf-8").strip())
                    if ahora - last < 7 * 24 * 3600:
                        necesario = False
                except Exception:
                    pass
            if necesario:
                self._crear_backup_automatico(base, marker, ahora)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).warning(f"Backup semanal falló: {e}")

    def _crear_backup_automatico(self, base: Path, marker: Path, ahora: float):
        """Crea un zip de ~/.gpromptstudio/ en backups/auto-AAAAMMDD.zip"""
        import zipfile
        import datetime as _dt
        backups_dir = base / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        nombre = f"auto-{_dt.datetime.now().strftime('%Y%m%d')}.zip"
        path = backups_dir / nombre
        try:
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in base.glob("*.json"):
                    zf.write(f, f.name)
            marker.write_text(str(ahora), encoding="utf-8")
            # Toast informativo
            self.after(2000, lambda: self.show_toast(
                f"💼 Backup auto creado: {nombre}", "#0891b2", 3500
            ))
            # Limpiar backups viejos (>10)
            backups = sorted(backups_dir.glob("auto-*.zip"))
            for old in backups[:-10]:
                try:
                    old.unlink()
                except Exception:
                    pass
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
            self.set_estado("⚠️ Escribe una idea primero", "#e67e22")
            return
        # Guardar resultado actual en pila ANTES de regenerar
        actual = self.txt_salida.get("1.0", "end").strip()
        if actual and (not self._regen_stack or self._regen_stack[-1] != actual):
            self._regen_push(actual)
        try: self._sesion_log("🔄 Regeneró prompt (misma idea)")
        except Exception: pass
        # Llamar a la generación normal
        self.cmd_prompt()

    def _cmd_regenerar_atras(self):
        """Navega a la versión anterior de la regeneración."""
        self._regen_init()
        if not self._regen_stack:
            self.set_estado("⚠️ No hay versiones anteriores", "#e67e22")
            return
        # Si estamos en el último, primero guardamos el actual
        actual = self.txt_salida.get("1.0", "end").strip()
        if self._regen_idx == len(self._regen_stack) - 1 and actual and \
                (not self._regen_stack or self._regen_stack[-1] != actual):
            self._regen_push(actual)
            self._regen_idx -= 1
        if self._regen_idx <= 0:
            self.set_estado("⚠️ Ya estás en la versión más antigua", "#e67e22")
            return
        self._regen_idx -= 1
        self.actualizar_salida(self._regen_stack[self._regen_idx])
        self.set_estado(f"← Versión {self._regen_idx + 1}/{len(self._regen_stack)}", "#3498db")

    def _cmd_regenerar_adelante(self):
        """Navega a la versión siguiente de la regeneración."""
        self._regen_init()
        if not self._regen_stack or self._regen_idx >= len(self._regen_stack) - 1:
            self.set_estado("⚠️ Ya estás en la versión más reciente", "#e67e22")
            return
        self._regen_idx += 1
        self.actualizar_salida(self._regen_stack[self._regen_idx])
        self.set_estado(f"→ Versión {self._regen_idx + 1}/{len(self._regen_stack)}", "#3498db")

    def _cmd_diff_versiones(self):
        """Muestra ventana con diff coloreado entre versión actual y anterior de la pila de regeneración."""
        self._regen_init()
        actual_txt = self.txt_salida.get("1.0", "end").strip()
        if not actual_txt:
            self.set_estado("⚠️ No hay prompt actual para comparar", "#e67e22")
            return
        # Buscar la versión anterior
        if not self._regen_stack:
            self.set_estado("⚠️ No hay versiones anteriores. Pulsa 🔄 Regenerar para crear historial.", "#e67e22")
            return
        # Si el actual es el último, comparamos con el penúltimo
        if self._regen_idx == len(self._regen_stack) - 1:
            if len(self._regen_stack) < 2:
                self.set_estado("⚠️ Necesitas al menos 2 versiones para comparar", "#e67e22")
                return
            anterior_txt = self._regen_stack[self._regen_idx - 1]
            etiqueta_actual = f"Versión {self._regen_idx + 1} (actual)"
            etiqueta_anterior = f"Versión {self._regen_idx} (anterior)"
        else:
            # Estamos navegando atrás, comparar con la siguiente
            if self._regen_idx + 1 >= len(self._regen_stack):
                self.set_estado("⚠️ No hay versión siguiente para comparar", "#e67e22")
                return
            anterior_txt = self._regen_stack[self._regen_idx]
            actual_txt = self._regen_stack[self._regen_idx + 1]
            etiqueta_actual = f"Versión {self._regen_idx + 2}"
            etiqueta_anterior = f"Versión {self._regen_idx + 1}"

        self._abrir_ventana_diff(anterior_txt, actual_txt, etiqueta_anterior, etiqueta_actual)

    def _abrir_ventana_diff(self, texto_a, texto_b, label_a="Anterior", label_b="Actual"):
        """Abre ventana con diff coloreado de dos textos lado a lado."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        import difflib
        v = ctk.CTkToplevel(self)
        v.title("📊 Diff visual entre versiones")
        v.geometry("1100x680")
        v.transient(self)

        ctk.CTkLabel(v, text="📊 Comparar versiones",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4))

        # Banda de leyenda
        leyenda = ctk.CTkFrame(v, fg_color=c["fg_dark"], corner_radius=6)
        leyenda.pack(fill="x", padx=15, pady=(0, 8))
        ctk.CTkLabel(leyenda, text="🟢 Verde = añadido en actual    🔴 Rojo = quitado del anterior    ⚪ Sin color = igual",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=6)

        # Container con dos columnas
        cols = ctk.CTkFrame(v, fg_color="transparent")
        cols.pack(fill="both", expand=True, padx=10, pady=4)
        cols.grid_columnconfigure(0, weight=1)
        cols.grid_rowconfigure(0, weight=1)

        # Columna izquierda (anterior)
        col_a = ctk.CTkFrame(cols, fg_color=c["fg_dark"], corner_radius=8)
        col_a.grid(row=0, column=0, padx=4, sticky="nsew")
        ctk.CTkLabel(col_a, text=f"📄 {label_a}", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=c["muted_text"]).pack(anchor="w", padx=10, pady=(8, 4))

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
        except Exception:
            pass

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
                     text=f"  📊 {ratio:.0f}% similar  ·  🟢 +{n_add} palabras  ·  🔴 −{n_del} palabras  ·  ⚪ {n_eq} sin cambios",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=6)

        ctk.CTkButton(v, text="Cerrar", width=110, command=v.destroy,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"]).pack(pady=(0, 12))

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
                subprocess.run(['osascript', '-e', f'display notification "{mensaje}" with title "{titulo}"'])
            elif sistema == "Linux":
                import subprocess
                subprocess.run(['notify-send', titulo, mensaje])
        except Exception:
            pass  # Si falla, no es crítico

    def _parsear_bloques_numerados(self, texto, prefijos_validos=None):
        """Parser ROBUSTO de respuestas con bloques tipo 'PROMPT 1:', 'SHOT 2:', 'FRAME 3:', '1.', etc."""
        if not texto: return []
        import re
        # Probar varios patrones (de más estricto a más permisivo)
        patrones = [
            r'(?:^|\n)\s*(?:PROMPT|SHOT|FRAME|VARIANTE|VERSION)\s*\d+\s*[:\-—\(]',  # "PROMPT 1:", "SHOT 2 (Wide):"
            r'(?:^|\n)\s*\d+\s*[\.\)]\s+',                                            # "1.", "1)"
            r'\n---+\n',                                                              # separadores ---
            r'(?:^|\n)\s*###\s*[^#\n]+\s*###\s*\n',                                   # ### Título ###
        ]
        for patron in patrones:
            partes = re.split(patron, '\n' + texto, flags=re.IGNORECASE)
            partes_limpias = [p.strip().strip("-").strip() for p in partes if p.strip() and len(p.strip()) > 30]
            if len(partes_limpias) >= 2:
                return partes_limpias
        # Fallback: si el texto tiene varios "POSITIVE PROMPT:" lo divide
        coincidencias = list(re.finditer(r'POSITIVE\s+PROMPT\s*:', texto, re.IGNORECASE))
        if len(coincidencias) >= 2:
            bloques = []
            for i, m in enumerate(coincidencias):
                inicio = m.start()
                fin = coincidencias[i+1].start() if i+1 < len(coincidencias) else len(texto)
                bloques.append(texto[inicio:fin].strip())
            return bloques
        # Último fallback: devolver como un solo bloque
        return [texto.strip()] if len(texto.strip()) > 30 else []

    def _cmd_plantillas_populares(self):
        """Biblioteca de plantillas probadas con variables {} para rellenar."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        plantillas = [
            # ═══ PLANTILLAS OFICIALES SEAART (de docs.seaart.ai) ═══
            ("🏜 SeaArt · Desert Wasteland",
             "Masterpiece, {angulo}, transitioning to a desert landscape at {hora_dia}, {sujeto}, wearing {ropa}. Layers of tattered fabric, unconventional accessories, and a weathered look create an aura of survival and resilience, 16K, ultra high resolution, photorealistic, UHD, RAW, DSLR, post-apocalyptic landscape with ruins and debris, Mad Max vibes",
             "(low quality, blurry:1.4), modern clothing, clean environment, urban setting"),
            ("🌙 SeaArt · Moonlit Scenery",
             "{sujeto} standing in a sunlight landscape, (best quality, 4k, 8k, highres, masterpiece:1.2), ultra-detailed, (realistic, photorealistic, photo-realistic:1.37), detailed facial features, {expresion}, {ropa}, elegant pose, dramatic moonlit backdrop, mystical atmosphere, (fantasy, cinematic:1.2), ethereal lighting, cool toned color palette, chiaroscuro lighting",
             "(low quality, worst quality:1.4), warm tones, daytime, harsh lighting, deformed"),
            ("🦊 SeaArt · Anthropomorphic Animal",
             "Anthropomorphic {animal}, {ropa}, {expresion}, standing pose, detailed fur texture, {entorno}, soft cinematic lighting, (best quality, masterpiece:1.2), highly detailed, character art, professional illustration",
             "(realistic photo:1.3), human features, deformed anatomy, low quality, blurry"),
            ("👗 SeaArt · Fashion Magazine",
             "(high fashion editorial:1.3), {sujeto} wearing {prenda}, {pose}, {locacion}, professional studio lighting, magazine cover quality, (best quality, masterpiece:1.2), 8K, sharp focus, vogue style, dramatic composition",
             "(low quality, amateur:1.4), bad anatomy, plain background, casual clothes, blurry"),
            # ═══ PLANTILLAS PROPIAS ═══
            ("📸 Portrait Pro",
             "(close-up portrait:1.3), {sujeto}, (detailed eyes:1.2), (detailed skin texture:1.2), {expresion}, professional studio lighting, shallow DOF, 85mm lens, bokeh background, {color_pelo} hair, photorealistic, 8K, masterpiece",
             "(worst quality, low quality:1.4), (deformed face, bad anatomy:1.3), (anime, cartoon:1.3), text, watermark"),
            ("🌅 Cinematic Landscape",
             "({lugar}:1.3), {hora_dia}, dramatic clouds, golden hour lighting, volumetric light, atmospheric haze, ultra wide shot, cinematic composition, photorealistic, 8K masterpiece",
             "(low quality:1.4), distorted perspective, oversaturated, hdr nuclear"),
            ("🛍 Product Photography",
             "(professional product photo:1.3), {producto} on {superficie}, studio lighting, soft shadows, {fondo_color} background, macro detail, sharp focus, commercial quality, 8K",
             "(deformed product:1.3), distorted, blurry, hands, person, watermark"),
            ("🎨 Anime Character",
             "(1girl:1.2), {sujeto}, {color_pelo} hair, {color_ojos} eyes, {ropa}, {pose}, detailed face, sharp lines, vibrant colors, anime illustration, cel-shading, masterpiece",
             "(realistic, photorealistic:1.4), (worst quality, low quality:1.3), bad anatomy, deformed, text, watermark"),
            ("🌃 Cyberpunk Street",
             "(cyberpunk city street:1.3), {hora_dia}, neon signs in {idiomas}, holographic ads, rain reflections, atmospheric haze, {sujeto} walking, cinematic composition, 8K masterpiece",
             "(daytime:1.2), boring composition, low quality, distorted"),
            ("✨ Magical Forest",
             "(enchanted forest:1.3), {hora_dia}, {sujeto}, bioluminescent {elemento}, magical particles in air, mist between trees, soft atmospheric lighting, mystical atmosphere, 8K masterpiece",
             "(low quality, blurry:1.3), modern objects, urban, distorted nature"),
            ("🍔 Food Photography",
             "(food photography:1.3), {plato} on {plato_superficie}, top-down or 45-degree angle, soft natural light, vibrant colors, fresh ingredients visible, shallow DOF, professional commercial quality, 8K",
             "(deformed food:1.3), unappealing, dark lighting, blurry"),
            ("👗 Fashion Editorial",
             "(high fashion editorial:1.3), {sujeto} wearing {prenda}, {pose}, {locacion}, dramatic lighting, professional photography, magazine quality, 8K masterpiece",
             "(low quality, amateur:1.3), bad anatomy, plain composition"),
            ("🚀 Sci-Fi Concept",
             "({tema_sci_fi}:1.3), futuristic {elemento}, {sujeto}, advanced technology details, atmospheric lighting, depth of field, concept art quality, 8K masterpiece",
             "(modern day, contemporary:1.2), low quality, simple, plain"),
            ("🏛 Architecture",
             "({estilo_arq}:1.3) architecture, {edificio}, {hora_dia} lighting, dramatic perspective, atmospheric, professional architecture photography, ultra detailed, 8K",
             "(low quality, blurry:1.3), distorted perspective, people, cars"),
            # ═══ PLANTILLAS COMUNIDAD GPT-IMAGE ═══
            ("📷 Comunidad · RAW iPhone authentic",
             "Create a completely RAW quality, unprocessed, unedited image with full iPhone camera quality. {escena}, {sujeto}. The image should look like an authentic momentary capture, not staged.",
             "(staged, posed:1.3), professional retouching, oversaturated, glossy filter"),
            ("🎮 Comunidad · GTA in-game footage",
             "{tema} in-game footage, very detailed, very realistic. Close-up shot taken from a stationary 4k monitor. (There's a slight blurriness in the image, as it feels like it was taken handheld). A wide, bright environment. Realistic details. {sujeto}",
             "(low quality, anime, cartoon:1.4), painted, illustration"),
            ("🌃 Comunidad · Convenience store night",
             "Create an ultra-realistic urban street scene at {entorno} {hora} night. {sujeto}, characters wearing everyday clothes, faces and postures look like real pedestrians, not overly polished. Bright white light streaming through glass doors and windows, warm yellow street lights and distant car headlights. The image should look like an authentic life slice captured by a photographer.",
             "(staged photoshoot:1.3), models, fashion clothes, internet celebrity styling, perfect makeup"),
            ("🎭 Comunidad · 16-panel expressions grid",
             "Create a 16-panel expression grid of {personaje}. The face shape, hairstyle, and clothing must remain highly consistent across all panels. The 16 expressions: happy, sad, angry, surprised, shy, speechless, evil grin, contemplative, curious, proud, wronged, disdainful, confused, scared, crying, heart eyes.",
             "(inconsistent character:1.4), different faces, varied clothing, low quality"),
            ("📺 Comunidad · YouTube screenshot",
             "Screenshot of a YouTube video showing {tema}. UI must include: video timeline, title, view count, like/dislike buttons, channel name, subscribe button. Realistic interface design.",
             "(low quality, distorted UI:1.3), unrealistic interface, text artifacts"),
            ("🎨 Comunidad · Movie collage one-shot",
             "Entire {pelicula} movie image collage one shot in one output. Multiple iconic scenes arranged dynamically, characters, locations, key moments combined seamlessly into a unified composition.",
             "(blurry, low detail:1.3), inconsistent style, broken composition"),
        ]

        vent = ctk.CTkToplevel(self)
        vent.title("📑 Plantillas de prompt")
        vent.geometry("700x600")
        vent.transient(self)
        ctk.CTkLabel(vent, text="📑 Plantillas probadas", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text="Click en una plantilla → rellena las variables {variable} en el campo idea",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=5)

        for nombre, pos, neg in plantillas:
            card = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=8)
            card.pack(fill="x", pady=4)
            ctk.CTkLabel(card, text=nombre, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=c["hdr_text"]).pack(anchor="w", padx=10, pady=(6, 2))
            # Mostrar variables detectadas
            import re
            vars_pos = re.findall(r'\{(\w+)\}', pos)
            vars_neg = re.findall(r'\{(\w+)\}', neg)
            todas_vars = sorted(set(vars_pos + vars_neg))
            if todas_vars:
                ctk.CTkLabel(card, text=f"  Variables: {', '.join(todas_vars)}",
                             font=ctk.CTkFont(size=10, slant="italic"), text_color=c["muted_text"]).pack(anchor="w", padx=10)
            preview = pos[:120]
            ctk.CTkLabel(card, text=f"  POS: {preview}...", font=ctk.CTkFont(size=10),
                         text_color=c["muted_text"], wraplength=620, justify="left", anchor="w").pack(fill="x", padx=10, pady=(0, 4))
            def _aplicar(p=pos, n=neg, name=nombre):
                txt = f"POSITIVE PROMPT: {p}\nNEGATIVE PROMPT: {n}"
                self.actualizar_salida(txt)
                vent.destroy()
                self.set_estado(f"📑 Plantilla '{name}' cargada — rellena las {{variables}}", "#2ecc71")
            ctk.CTkButton(card, text="✅ Cargar plantilla", width=140, height=24, fg_color="#1a7a3c",
                          font=ctk.CTkFont(size=10), command=_aplicar).pack(anchor="e", padx=10, pady=(0, 6))

    def _abrir_comparador(self, variaciones):
        vent = ctk.CTkToplevel(self)
        vent.title("👁 Comparar Variaciones")
        n = len(variaciones)

        # Limitar a tamaño de pantalla — columnas más estrechas para que quepan más
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        col_width = 380  # más estrecho que antes (510)
        ancho = min(col_width * min(n, 4) + 80, screen_w - 100)  # max 4 columnas visibles
        alto = min(750, screen_h - 100)
        vent.geometry(f"{ancho}x{alto}")
        vent.transient(self)

        ctk.CTkLabel(vent, text=f"👁 Comparador de Variaciones ({n})  —  Scroll horizontal para ver todas",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(8, 3))

        # Scroll horizontal para columnas
        scroll_frame = ctk.CTkScrollableFrame(vent, fg_color="transparent", orientation="horizontal")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        frame_cols = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        frame_cols.pack(fill="both", expand=True)

        colores_header = ["#1a4a7a", "#1a7a3c", "#4a1a7a", "#7a3c1a", "#3a5a1a", "#7a1a4a", "#5a3c1a", "#1a5a5a"]
        tiene_neg = self._debe_mostrar_negatives()

        for i, var in enumerate(variaciones):
            col = ctk.CTkFrame(frame_cols, fg_color=c["fg_frame"], corner_radius=8, width=col_width)
            col.pack(side="left", fill="y", padx=3, pady=2)
            col.pack_propagate(False)
            col.configure(width=col_width, height=alto - 100)

            hdr = ctk.CTkFrame(col, fg_color=colores_header[i % len(colores_header)], corner_radius=6, height=28)
            hdr.pack(fill="x", padx=5, pady=(5, 3))
            hdr.pack_propagate(False)
            ctk.CTkLabel(hdr, text=f"  Variación #{i+1}", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=8)

            # Separar POSITIVE y NEGATIVE visualmente
            pos_text = self._extraer_pos_de_bloque(var) or var
            neg_text = self._extraer_neg_de_bloque(var) or ""

            scroll = ctk.CTkScrollableFrame(col, fg_color="transparent")
            scroll.pack(fill="both", expand=True, padx=5, pady=(0, 3))

            ctk.CTkLabel(scroll, text="🟢 POSITIVE:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#2ecc71").pack(anchor="w")
            lbl_pos = ctk.CTkLabel(scroll, text=pos_text, wraplength=col_width - 60, justify="left", font=ctk.CTkFont(size=10), text_color=c["muted_text"], anchor="w")
            lbl_pos.pack(fill="x", pady=(0, 6))

            if neg_text and tiene_neg:
                ctk.CTkLabel(scroll, text="🔴 NEGATIVE:", font=ctk.CTkFont(size=10, weight="bold"), text_color="#e74c3c").pack(anchor="w")
                ctk.CTkLabel(scroll, text=neg_text, wraplength=col_width - 60, justify="left", font=ctk.CTkFont(size=10), text_color="#999999", anchor="w").pack(fill="x", pady=(0, 4))

            # Label para traducción (inicialmente vacío)
            lbl_trad = ctk.CTkLabel(scroll, text="", wraplength=col_width - 60, justify="left", font=ctk.CTkFont(size=10, slant="italic"), text_color="#8bb4d4", anchor="w")

            # Botones
            btn_row = ctk.CTkFrame(col, fg_color="transparent")
            btn_row.pack(fill="x", padx=5, pady=(0, 5))

            def _copiar_completo(v=var, n=i+1):
                pyperclip.copy(v)
                self.set_estado(f"✅ Variación #{n} copiada", "#2ecc71")

            def _copiar_pos(p=pos_text, n=i+1):
                pyperclip.copy(p)
                self.set_estado(f"✅ POSITIVE #{n} copiado", "#2ecc71")

            def _copiar_neg(ng=neg_text, n=i+1):
                if ng:
                    pyperclip.copy(ng)
                    self.set_estado(f"✅ NEGATIVE #{n} copiado", "#2ecc71")

            def _usar(v=var, n=i+1):
                self.actualizar_salida(v)
                vent.destroy()
                self.set_estado(f"✅ Variación #{n} cargada", "#2ecc71")

            def _traducir(p=pos_text, lbl=lbl_trad):
                lbl.pack(fill="x", pady=(6, 4))
                lbl.configure(text="🌐 Traduciendo...")
                def _worker():
                    try:
                        trad = self.deepseek.traducir_a_espanol(p)
                        vent.after(0, lambda: lbl.configure(text=f"🇪🇸 {trad}"))
                    except Exception:
                        vent.after(0, lambda: lbl.configure(text="❌ Error al traducir"))
                threading.Thread(target=_worker, daemon=True).start()

            ctk.CTkButton(btn_row, text="📋", width=30, height=24, fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"], command=_copiar_completo).pack(side="left", padx=1)
            ctk.CTkButton(btn_row, text="🟢", width=30, height=24, fg_color="#1a5a2a", hover_color="#0f3a1a", command=_copiar_pos).pack(side="left", padx=1)
            if tiene_neg:
                ctk.CTkButton(btn_row, text="🔴", width=30, height=24, fg_color="#5a1a1a", hover_color="#3a0f0f", command=_copiar_neg).pack(side="left", padx=1)
            ctk.CTkButton(btn_row, text="🇪🇸", width=30, height=24, fg_color="#8e44ad", hover_color="#6a2a8a", command=_traducir).pack(side="left", padx=1)
            ctk.CTkButton(btn_row, text="✅ Usar", width=60, height=24, fg_color="#1a7a3c", hover_color="#145e2d", font=ctk.CTkFont(size=10, weight="bold"), command=_usar).pack(side="right", padx=2)

    def _setup_wizard(self):
        """Wizard de primera vez cuando faltan API keys. Devuelve True si se configuraron.

        v1.0: validación de formato, botón de test de conexión real."""
        import os
        from dotenv import set_key
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        wizard = ctk.CTkToplevel(self)
        wizard.title("🧠 G-Prompt Studio — Configuración Inicial")
        wizard.geometry("580x560")
        wizard.transient(self)
        wizard.grab_set()

        resultado = [False]

        ctk.CTkLabel(wizard, text="🧠 ¡Bienvenido a G-Prompt Studio!",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 5))
        ctk.CTkLabel(wizard, text="Para empezar necesitas al menos una API key.\nPuedes empezar gratis con Gemini (Google) o DeepSeek (~€0.14/1M tokens).",
                     font=ctk.CTkFont(size=11), text_color=c["muted_text"], justify="center").pack(pady=(0, 12))

        frame = ctk.CTkFrame(wizard)
        frame.pack(fill="x", padx=30, pady=5)

        # v1.0.8 — Campo nombre (lo usamos en el saludo del dashboard)
        ctk.CTkLabel(frame, text="👤 ¿Cómo quieres que te llamemos?",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
        entry_nombre = ctk.CTkEntry(frame, width=480, placeholder_text="Tu nombre o apodo (ej: Gustaafvito)")
        entry_nombre.pack(padx=10)
        ctk.CTkLabel(frame, text="Aparecerá en el saludo del dashboard. Puedes dejarlo vacío.",
                     font=ctk.CTkFont(size=10), text_color="#3498db").pack(anchor="w", padx=10, pady=(0, 8))

        ctk.CTkLabel(frame, text="🔑 DeepSeek API Key:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
        entry_ds = ctk.CTkEntry(frame, width=480, placeholder_text="sk-...", show="*")
        entry_ds.pack(padx=10)
        ctk.CTkLabel(frame, text="Consíguela en: platform.deepseek.com  ·  formato: sk-XXXXXX...", font=ctk.CTkFont(size=10), text_color="#3498db").pack(anchor="w", padx=10, pady=(0, 8))

        ctk.CTkLabel(frame, text="🔑 Gemini API Key:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5, 2))
        entry_gm = ctk.CTkEntry(frame, width=480, placeholder_text="AIza...", show="*")
        entry_gm.pack(padx=10)
        ctk.CTkLabel(frame, text="Consíguela en: aistudio.google.com/apikey  ·  formato: AIzaXXXXXX...", font=ctk.CTkFont(size=10), text_color="#3498db").pack(anchor="w", padx=10, pady=(0, 8))

        ctk.CTkLabel(frame, text="🔑 OpenRouter API Key (opcional):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5, 2))
        entry_or = ctk.CTkEntry(frame, width=480, placeholder_text="sk-or-...", show="*")
        entry_or.pack(padx=10)
        ctk.CTkLabel(frame, text="Consíguela en: openrouter.ai/keys  ·  100+ modelos con una sola key", font=ctk.CTkFont(size=10), text_color="#3498db").pack(anchor="w", padx=10, pady=(0, 10))

        lbl_estado = ctk.CTkLabel(wizard, text="", font=ctk.CTkFont(size=11), text_color=c["muted_text"])
        lbl_estado.pack(pady=4)

        def _validar_formato(ds: str, gm: str, or_k: str) -> tuple[bool, str]:
            """Validación básica de formato de keys (no contacto a la API)."""
            if not ds and not gm and not or_k:
                return False, "⚠️ Introduce al menos una API key."
            if ds and not (ds.startswith("sk-") and len(ds) > 12):
                return False, "❌ La key de DeepSeek parece incorrecta (debe empezar por 'sk-')."
            if gm and not (gm.startswith("AIza") and len(gm) > 20):
                return False, "❌ La key de Gemini parece incorrecta (debe empezar por 'AIza')."
            if or_k and not (or_k.startswith("sk-or-") and len(or_k) > 12):
                return False, "❌ La key de OpenRouter parece incorrecta (debe empezar por 'sk-or-')."
            return True, ""

        def _test_keys():
            """Hace una mini-llamada a la API con la key de DeepSeek para verificar."""
            ds = entry_ds.get().strip()
            if not ds:
                lbl_estado.configure(text="⚠️ Introduce al menos la key de DeepSeek para testear.", text_color="#e67e22")
                return
            ok, msg = _validar_formato(ds, entry_gm.get().strip(), entry_or.get().strip())
            if not ok:
                lbl_estado.configure(text=msg, text_color="#e74c3c")
                return

            lbl_estado.configure(text="⏳ Probando conexión a DeepSeek...", text_color="#3498db")
            wizard.update_idletasks()

            def _worker():
                try:
                    from openai import OpenAI
                    cli = OpenAI(api_key=ds, base_url="https://api.deepseek.com")
                    res = cli.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": "Responde solo 'ok'"}],
                        max_tokens=5,
                    )
                    txt = (res.choices[0].message.content or "").strip().lower()
                    if "ok" in txt or txt:
                        wizard.after(0, lambda: lbl_estado.configure(
                            text="✅ Conexión OK — la key funciona.", text_color="#2ecc71"))
                    else:
                        wizard.after(0, lambda: lbl_estado.configure(
                            text="⚠️ Respuesta inesperada — pero la key parece válida.", text_color="#e67e22"))
                except Exception as e:
                    err = str(e)[:80]
                    wizard.after(0, lambda: lbl_estado.configure(
                        text=f"❌ Falló: {err}", text_color="#e74c3c"))

            threading.Thread(target=_worker, daemon=True).start()

        def guardar():
            ds = entry_ds.get().strip()
            gm = entry_gm.get().strip()
            or_key = entry_or.get().strip()

            ok, msg = _validar_formato(ds, gm, or_key)
            if not ok:
                lbl_estado.configure(text=msg, text_color="#e74c3c")
                return

            env_path = ".env"
            if not os.path.exists(env_path):
                with open(env_path, "w") as f:
                    f.write("")

            try:
                if ds:
                    set_key(env_path, "DEEPSEEK_API_KEY", ds)
                if gm:
                    set_key(env_path, "GEMINI_API_KEY", gm)
                if or_key:
                    set_key(env_path, "OPENROUTER_API_KEY", or_key)
            except Exception as e:
                lbl_estado.configure(text=f"❌ Error guardando: {e}", text_color="#e74c3c")
                return

            # v1.0.8 — Guardar nombre en preferences.json
            try:
                nombre = entry_nombre.get().strip()
                if nombre:
                    prefs = self.store.cargar_preferencias() or {}
                    prefs["nombre"] = nombre
                    self.store.guardar_preferencias(prefs)
            except Exception:
                pass

            resultado[0] = True
            wizard.destroy()

        def cancelar():
            wizard.destroy()

        btn_frame = ctk.CTkFrame(wizard, fg_color="transparent")
        btn_frame.pack(pady=10)
        ctk.CTkButton(btn_frame, text="🧪 Test conexión", width=140, height=36,
                      fg_color="#3498db", hover_color="#2980b9", command=_test_keys).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="✅ Guardar y Empezar", width=200, height=36,
                      fg_color="#2ecc71", hover_color="#27ae60", command=guardar).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="❌ Cancelar", width=110, height=36,
                      fg_color="#555", hover_color="#333", command=cancelar).pack(side="left", padx=6)

        wizard.wait_window()
        return resultado[0]

    def cmd_preferencias(self):
        ventana = ctk.CTkToplevel(self)
        ventana.title("⚙️ Ajustes del Sistema")
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
            _prefs_llm_labels = ["DeepSeek V3", "Google Gemini", "OpenAI GPT-4o", "Local (Ollama)"]

        # v1.0.8 — Campo Nombre del usuario (para saludo del dashboard)
        ctk.CTkLabel(tab_gen, text="👤 Tu nombre (saludo del Dashboard):",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 2), padx=20)
        self.entry_nombre_pref = ctk.CTkEntry(tab_gen, width=250,
                                                placeholder_text="Tu nombre o apodo")
        try:
            _prefs_existentes = self.store.cargar_preferencias() or {}
            _nombre_actual = _prefs_existentes.get("nombre", "")
            if _nombre_actual:
                self.entry_nombre_pref.insert(0, _nombre_actual)
        except Exception: pass
        self.entry_nombre_pref.pack(anchor="w", padx=20)

        ctk.CTkLabel(tab_gen, text="🧠 Cerebro por defecto al iniciar:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 2), padx=20)
        self.combo_default_llm = ctk.CTkComboBox(tab_gen, values=_prefs_llm_labels, width=250)
        self.combo_default_llm.set(self.llm_var.get())
        self.combo_default_llm.pack(anchor="w", padx=20)

        ctk.CTkLabel(tab_gen, text="▶️ Modo por defecto al iniciar:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 2), padx=20)
        _modos_display = ["Audio", "Imagen", "Vídeo"]
        _modo_to_display = {"audio": "Audio", "imagen": "Imagen", "video": "Vídeo"}
        _modo_from_display = {"Audio": "audio", "Imagen": "imagen", "Vídeo": "video"}
        self._modo_from_display = _modo_from_display
        self.combo_default_modo = ctk.CTkComboBox(tab_gen, values=_modos_display, width=250)
        self.combo_default_modo.set(_modo_to_display.get(self.modo_var.get(), "Imagen"))
        self.combo_default_modo.pack(anchor="w", padx=20)

        ctk.CTkLabel(tab_gen, text="🎨 Tema de interfaz:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 2), padx=20)
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
        ctk.CTkSwitch(tab_gen, text="🔔 Sonido al completar generación",
                      variable=self.switch_sonido_var,
                      progress_color="#3498db",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      height=26, width=50, corner_radius=13,
                      button_hover_color="#f3f4f6",
                      border_width=2).pack(anchor="w", padx=10, pady=(15, 5))

        # ── Toggle: grabar vídeo de la sesión ──
        self.switch_video_sesion_var = ctk.BooleanVar(value=self._sesion_grabar_video if hasattr(self, '_sesion_grabar_video') else False)
        ctk.CTkSwitch(tab_gen, text="🎥 Grabar vídeo (MP4) al usar 🎬 Sesión grabada",
                      variable=self.switch_video_sesion_var,
                      progress_color="#e74c3c",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      height=26, width=50, corner_radius=13,
                      button_hover_color="#f3f4f6",
                      border_width=2).pack(anchor="w", padx=10, pady=(5, 2))
        ctk.CTkLabel(tab_gen,
                     text="    Captura toda la pantalla a 5 FPS (MP4 H.264). Requiere: pip install mss imageio[ffmpeg]",
                     font=ctk.CTkFont(size=9, slant="italic"), text_color="#888").pack(anchor="w", padx=10)

        # Botón Guardar Abajo
        btn_guardar = ctk.CTkButton(ventana, text="💾 Guardar Preferencias", fg_color="#2ecc71", hover_color="#27ae60", command=lambda: self._guardar_y_cerrar_preferencias(ventana))
        btn_guardar.pack(pady=(0, 20))

    def _guardar_y_cerrar_preferencias(self, ventana):
        nuevo_llm = self.combo_default_llm.get()

        # Aplicar cerebro
        self.llm_var.set(nuevo_llm)
        self._on_llm_cambio(label=nuevo_llm)

        # Aplicar modo (mapear display → internal)
        _modo_from_display = getattr(self, '_modo_from_display', {"Audio": "audio", "Imagen": "imagen", "Vídeo": "video"})
        nuevo_modo = _modo_from_display.get(self.combo_default_modo.get(), "imagen")
        if self.modo_var.get() != nuevo_modo:
            self.modo_var.set(nuevo_modo)
            self._on_modo_cambio()

        # Aplicar tema (mapear display → internal)
        if hasattr(self, 'combo_tema'):
            _tema_from_display = getattr(self, '_tema_from_display', {"Dark": "dark", "Light": "light", "System": "system"})
            nuevo_tema = _tema_from_display.get(self.combo_tema.get(), "dark")
            ctk.set_appearance_mode(nuevo_tema)
            # v1.0.8 — Repintar frames adaptativos tras cambio de tema desde Preferencias
            try:
                self.after(50, self._apply_theme_colors)
            except Exception:
                pass

        # Aplicar sonido
        if hasattr(self, 'switch_sonido_var'):
            self._sonido_activo = self.switch_sonido_var.get()

        # Aplicar grabación de vídeo de sesión
        if hasattr(self, 'switch_video_sesion_var'):
            self._sesion_grabar_video = self.switch_video_sesion_var.get()

        # v1.0.8 — Guardar nombre del usuario si lo cambió
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
        except Exception:
            pass

        # 3. Guardar las preferencias usando tu sistema de persistence.py
        self._guardar_preferencias()

        self.set_estado("⚙️ Preferencias guardadas correctamente. (API Keys → botón 🔑 del header)", "#2ecc71")
        ventana.destroy()

    def cmd_previsualizar(self):
        prompt_actual = self.txt_salida.get("1.0", "end").strip()

        if not prompt_actual:
            return self.set_estado("⚠️ Genera un prompt primero para poder previsualizarlo.", "#e67e22")

        if self.modo_var.get() == "audio":
            return self.set_estado("⚠️ La previsualización solo está disponible para Imágenes y Vídeos.", "#e67e22")
        try: self._sesion_log("🎨 Previsualizó (boceto rápido)")
        except Exception: pass

        self.set_estado("🎨 Previsualizando... Esto puede tardar unos 10-15 segundos.", "#9b59b6")
        self.toggle_botones(False)

        def _worker():
            try:
                import urllib.parse
                import urllib.request
                import io
                import time
                from PIL import Image

                # 2. Limpieza EXTREMA del prompt para evitar que rompa la URL
                texto_limpio = prompt_actual.split("NEGATIVE PROMPT:")[0]
                texto_limpio = texto_limpio.replace("PROMPT:", "").replace("POSITIVE PROMPT:", "")

                # Quitamos saltos de línea, retornos y asteriscos
                texto_limpio = texto_limpio.replace("\n", " ").replace("\r", " ").replace("*", "")

                # Quitamos espacios dobles
                texto_limpio = " ".join(texto_limpio.split())

                # Recortamos drásticamente a 400 caracteres. Para un boceto es más que suficiente 
                # y evitamos que los servidores web colapsen por enlaces muy largos.
                if len(texto_limpio) > 400:
                    texto_limpio = texto_limpio[:400]

                semilla = int(time.time())
                prompt_codificado = urllib.parse.quote(texto_limpio)

                url_imagen = f"https://image.pollinations.ai/prompt/{prompt_codificado}?width=512&height=512&nologo=true&seed={semilla}"

                # Usamos un User-Agent estándar para que no nos bloqueen
                req = urllib.request.Request(url_imagen, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=30) as response:
                    image_data = response.read()

                # Verificamos que realmente sea una imagen y no una página de error
                content_type = response.info().get_content_type()
                if content_type not in ["image/jpeg", "image/png", "image/webp"]:
                    raise Exception("La API devolvió un formato incorrecto o está saturada.")

                image_pil = Image.open(io.BytesIO(image_data))
                img_ctk = ctk.CTkImage(light_image=image_pil, dark_image=image_pil, size=(512, 512))

                def _mostrar_imagen():
                    vent_previa = ctk.CTkToplevel(self)
                    vent_previa.title("🎨 Previsualización Rápida")
                    vent_previa.geometry("540x600")
                    vent_previa.transient(self)

                    lbl_img = ctk.CTkLabel(vent_previa, text="", image=img_ctk)
                    lbl_img.pack(pady=(15, 10))

                    btn_guardar = ctk.CTkButton(vent_previa, text="💾 Guardar Boceto", fg_color="#2ecc71", hover_color="#27ae60", 
                                                command=lambda: self._guardar_boceto(image_pil))
                    btn_guardar.pack(pady=5)

                    self.set_estado("✅ Previsualización generada con éxito.", "#2ecc71")
                    self.toggle_botones(True)

                self.after(0, _mostrar_imagen)

            except Exception as e:
                mensaje_error = str(e) if str(e) else "Error de conexión o timeout."
                def _mostrar_error():
                    self.set_estado(f"❌ Error al generar imagen: {mensaje_error}", "#e74c3c")
                    self.toggle_botones(True)
                self.after(0, _mostrar_error)

        threading.Thread(target=_worker, daemon=True).start()

    def _guardar_boceto(self, image_pil):
        ruta = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png")], title="Guardar boceto")
        if ruta:
            try:
                if image_pil.mode in ("RGBA", "P"): image_pil = image_pil.convert("RGB")
                image_pil.save(ruta)
                self.set_estado(f"✅ Boceto guardado en: {ruta}", "#2ecc71")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la imagen:\n{e}")
