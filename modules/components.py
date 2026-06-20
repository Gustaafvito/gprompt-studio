"""Componentes de ArquitectoApp.

Capa de namespace sobre los mixins existentes. Permite usar
`self.creative.cmd_moodboard()` además del `self.cmd_moodboard()`
heredado del mixin. La migración hacia composición real puede
hacerse archivo por archivo sin romper nada.

Cada componente delega a la app vía __getattr__. Una llamada
`self.creative.X` se resuelve como `getattr(self.app, "X")`,
lo que devuelve el método bound al app (donde el mixin vive).

Uso desde ArquitectoApp:

    class ArquitectoApp(ctk.CTk, *MIXINS):
        def __init__(self):
            super().__init__()
            install_components(self)
            # Ahora puedes usar self.creative, self.workflow, etc.
"""
import logging

logger = logging.getLogger(__name__)


class _Component:
    """Base: delega cualquier atributo no encontrado a self.app.

    A1 completo: __getattr__ delega TANTO métodos públicos (cmd_X)
    como privados (_método). Esto permite que cualquier mixin sea
    accesible vía su componente, no solo los entry points
    declarados explícitamente como métodos del componente.

    Convención:
      - `self.X.metodo()` → llama al método público del componente
        si está declarado, sino delega a `self.app.metodo` (o
        `self.app._metodo` si el nombre empieza con _)
      - Los métodos público sin underscore declarados explícitamente
        sirven de API documentada del servicio.
    """

    __slots__ = ("app",)
    _name = "component"

    def __init__(self, app):
        self.app = app

    def __getattr__(self, name):
        if name == "app":
            raise AttributeError(name)
        try:
            return getattr(self.app, name)
        except AttributeError:
            raise AttributeError(
                f"{self._name!r} no tiene atributo {name!r} "
                f"(buscado en ArquitectoApp)"
            ) from None

    def __repr__(self):
        return f"<{self.__class__.__name__} app={self.app!r}>"


class CoreComponent(_Component):
    """Workers, comandos principales, estado (CoreMixin).

    Entry points del CoreMixin: cmd_ideas, cmd_prompt, cmd_prompt_quick,
    cmd_variaciones, cmd_vision, cmd_imagen_a_prompt, cmd_refinar,
    cmd_batch, cmd_reset, cmd_copiloto, cmd_previsualizar. Accesibles
    vía __getattr__ delegando al app (todos sin underscore en el mixin).
    """
    _name = "core"


class UIComponent(_Component):
    """Construcción de UI: _build_* y helpers.

    A1 fase 2 (sesión 14): UIBuildersMixin → UIBuildersService aislado.

    UI no tiene "entry points" cmd_* (son helpers internos del
    constructor). El __getattr__ del componente delega cualquier
    atributo no encontrado al service (que a su vez accede a self.app).
    """
    _name = "ui"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.ui_builders import UIBuildersService
        self._service = UIBuildersService(app)

    def __getattr__(self, name):
        # Primero busca en el servicio (para _build_* y helpers)
        if name in ("app", "_service"):
            raise AttributeError(name)
        if hasattr(self._service, name):
            return getattr(self._service, name)
        # Si no, delega al app (compatibilidad)
        return super().__getattr__(name)


class CreativeComponent(_Component):
    """Moodboard, ADN, Negative Builder, Paleta, etc.

    A1 fase 2 (sesión 14): ToolsCreativeMixin → ToolsCreativeService aislado.
    """
    _name = "creative"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.tools_creative import ToolsCreativeService
        self._service = ToolsCreativeService(app)

    def cmd_negative_builder(self) -> None:
        return self._service._cmd_negative_builder()

    def cmd_color_palette(self) -> None:
        return self._service._cmd_color_palette()

    def cmd_anclaje_visual(self) -> None:
        return self._service._cmd_anclaje_visual()

    def cmd_negative_optimo(self) -> None:
        return self._service._cmd_negative_optimo()

    def cmd_sugerir_negative_tab(self) -> None:
        return self._service._cmd_sugerir_negative_tab()

    def cmd_sugerir_tags(self) -> None:
        return self._service._cmd_sugerir_tags()

    def cmd_solo_negative(self) -> None:
        return self._service._cmd_solo_negative()

    # cmd_modo_focus vive en app.py, no en ToolsCreativeService
    def cmd_modo_focus(self) -> None:
        return self.app._cmd_modo_focus()

    def cmd_grupo_personajes(self) -> None:
        return self._service._cmd_grupo_personajes()


class UiFooterComponent(_Component):
    """Footer/barra inferior + helpers de selección (estilos, ratio,
    personaje, lora, negative, idioma).

    A1 fase 2 (sesión 14): UiFooterMixin → UiFooterService aislado.
    __getattr__ delega al servicio (necesario porque hay 29 métodos y
    muchos se usan desde decenas de sitios).
    """
    _name = "footer"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.ui_footer import UiFooterService
        self._service = UiFooterService(app)

    def __getattr__(self, name):
        if name in ("app", "_service"):
            raise AttributeError(name)
        if hasattr(self._service, name):
            return getattr(self._service, name)
        return super().__getattr__(name)


class WorkflowComponent(_Component):
    """Macros, Cron, Proyectos, Versiones, Búsqueda global, etc.

    A1 fase 2 (sesión 14): ToolsWorkflowMixin → ToolsWorkflowService aislado.
    """
    _name = "workflow"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.tools_workflow import ToolsWorkflowService
        self._service = ToolsWorkflowService(app)

    def cmd_cron_prompts(self) -> None:
        return self._service._cmd_cron_prompts()

    def cmd_proyectos(self) -> None:
        return self._service._cmd_proyectos()

    def cmd_versiones_prompt(self) -> None:
        return self._service._cmd_versiones_prompt()

    def cmd_adaptar_modelo(self) -> None:
        return self._service._cmd_adaptar_modelo()

    def abrir_macros(self) -> None:
        return self._service._abrir_macros()

    # NOTA: cmd_convertir_a_video y cmd_previsualizar viven en CoreMixin/app.py,
    # no en ToolsWorkflowService, así que siguen delegando al app.
    def cmd_convertir_a_video(self) -> None:
        return self.app._cmd_convertir_a_video()

    def cmd_previsualizar(self) -> None:
        return self.app.cmd_previsualizar()


class AnalysisComponent(_Component):
    """Estadísticas, Scoring, Auto-improve, Critique.

    A1 fase 2 (sesión 14): ToolsAnalysisMixin → ToolsAnalysisService aislado.
    """
    _name = "analysis"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.tools_analysis import ToolsAnalysisService
        self._service = ToolsAnalysisService(app)

    def cmd_modo_educativo(self) -> None:
        return self._service._cmd_modo_educativo()

    def cmd_critica_historial(self) -> None:
        return self._service._cmd_critica_historial()

    def cmd_automejora_periodica(self) -> None:
        return self._service._cmd_automejora_periodica()

    def abrir_estadisticas(self) -> None:
        return self._service._abrir_estadisticas()

    def cmd_scoring(self) -> None:
        return self._service._cmd_scoring()

    def cmd_optimizar_loop(self) -> None:
        return self._service._cmd_optimizar_loop()

    def cmd_coste_sesion(self) -> None:
        return self._service._cmd_coste_sesion()

    def detectar_nsfw_auto(self, idea: str | None = None) -> bool:
        return self._service._detectar_nsfw_auto(idea)

    def guardar_seed_favorito(self) -> None:
        return self._service._guardar_seed_favorito()

    def abrir_seeds_favoritos(self) -> None:
        return self._service._abrir_seeds_favoritos()

    def autocompletar_tags(self, event=None) -> None:
        return self._service._autocompletar_tags(event)

    def abrir_atajos_tags(self) -> None:
        return self._service._abrir_atajos_tags()

    def copiar_comfyui_json(self) -> None:
        return self._service._copiar_comfyui_json()

    def traducir_salida(self) -> None:
        return self._service._traducir_salida()

    def mostrar_consejo_contextual(self, modelo_name: str, specs: dict) -> None:
        return self._service._mostrar_consejo_contextual(modelo_name, specs)

    def cmd_modal_compatibilidad(self) -> None:
        return self._service._cmd_modal_compatibilidad()


class DataComponent(_Component):
    """Historial, Favoritos, Estrellas, Plantillas, Snippets, Imagen.

    A1 fase 2 (sesión 14): DataMgmtMixin → DataMgmtService aislado.
    __getattr__ extendido para delegar al servicio (necesario porque
    guardar_en_historial, actualizar_combo_*, _cargar_plantilla, etc.
    se usan desde MUCHOS sitios y no merece la pena listar todos como
    properties).
    """
    _name = "data"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.data_mgmt import DataMgmtService
        self._service = DataMgmtService(app)

    def __getattr__(self, name):
        if name in ("app", "_service"):
            raise AttributeError(name)
        if hasattr(self._service, name):
            return getattr(self._service, name)
        return super().__getattr__(name)

    def cmd_guardar_plantilla(self) -> None:
        return self._service._cmd_guardar_plantilla()

    def cmd_borrar_plantilla(self) -> None:
        return self._service._cmd_borrar_plantilla()

    def guardar_favorito(self) -> None:
        return self._service._guardar_favorito()

    def guardar_estrella(self) -> None:
        return self._service._guardar_estrella()

    def repetir_ultima_config(self) -> None:
        return self._service._repetir_ultima_config()

    def cmd_gestionar_snippets(self) -> None:
        return self._service._cmd_gestionar_snippets()

    def abrir_snippets(self) -> None:
        return self._service._abrir_snippets()

    def abrir_formulas(self) -> None:
        return self._service._abrir_formulas()

    def abrir_biblioteca(self) -> None:
        return self._service._abrir_biblioteca()

    def cmd_duplicar_a_historial(self, event=None) -> None:
        return self._service._cmd_duplicar_a_historial(event)

    def idea_aleatoria_historial(self) -> None:
        return self._service._idea_aleatoria_historial()


class BackupComponent(_Component):
    """Backup, Restore, CSV, Export CLI, Búsqueda global.

    A1 fase 2 (sesión 14): BackupExportMixin → BackupExportService aislado.
    """
    _name = "backup"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.backup_export import BackupExportService
        self._service = BackupExportService(app)

    def cmd_backup_completo(self) -> None:
        return self._service._cmd_backup_completo()

    def cmd_restore_completo(self) -> None:
        return self._service._cmd_restore_completo()

    def cmd_exportar_csv(self) -> None:
        return self._service._cmd_exportar_csv()

    def cmd_export_cli(self) -> None:
        return self._service._cmd_export_cli()

    def cmd_busqueda_global(self) -> None:
        return self._service._cmd_busqueda_global()


class DialogsComponent(_Component):
    """API Keys, Tema, Preferencias, Acerca de, Tokens + UI base
    (set_estado, actualizar_salida, toggle_botones, progreso, sonido).

    A1 fase 2 (sesión 14): DialogsMixin → DialogsService aislado.
    __getattr__ delega TODO al servicio (necesario porque set_estado,
    actualizar_salida, toggle_botones, etc. se usan desde CIENTOS de
    sitios y sería contraproducente listarlos todos como métodos).
    """
    _name = "dialogs"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.dialogs import DialogsService
        self._service = DialogsService(app)

    def __getattr__(self, name):
        if name in ("app", "_service"):
            raise AttributeError(name)
        if hasattr(self._service, name):
            return getattr(self._service, name)
        return super().__getattr__(name)

    def cmd_configurar_api_keys(self, provider_focus=None) -> None:
        return self._service._cmd_configurar_api_keys(provider_focus)

    def cmd_toggle_tema(self) -> None:
        return self._service._cmd_toggle_tema()

    def cmd_acerca_de(self) -> None:
        return self._service._cmd_acerca_de()

    def cmd_preferencias(self) -> None:
        return self.app.cmd_preferencias()


class AdnVisualComponent(_Component):
    """ADN Visual + biblioteca de rasgos.

    A1 fase 2 (sesión 14): AdnVisualMixin → AdnVisualService aislado.
    El componente instancia el service y delega los 2 comandos.
    """
    _name = "adn"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.adn_visual import AdnVisualService
        self._service = AdnVisualService(app)

    def cmd_adn_visual(self) -> None:
        return self._service._cmd_adn_visual()

    def cmd_ver_biblioteca(self) -> None:
        return self._service._cmd_ver_biblioteca_adn()


class SesionVideoComponent(_Component):
    """Grabación de sesión + tutorial vídeo.

    A1 fase 2 (sesión 14): SesionVideoMixin → SesionVideoService aislado.
    El __getattr__ del componente delega CUALQUIER atributo al servicio
    (que a su vez delega al app), así `self.sesion._sesion_log(...)` y
    `self.sesion._cmd_sesion_grabar_toggle()` funcionan ambos.
    """
    _name = "sesion"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.sesion_video import SesionVideoService
        self._service = SesionVideoService(app)

    def __getattr__(self, name):
        if name in ("app", "_service"):
            raise AttributeError(name)
        if hasattr(self._service, name):
            return getattr(self._service, name)
        return super().__getattr__(name)

    def cmd_grabar_toggle(self) -> None:
        return self._service._cmd_sesion_grabar_toggle()


class DashboardComponent(_Component):
    """Dashboard panel — pantalla de bienvenida.

    A1 fase 2 (sesión 11): DashboardMixin → DashboardService aislado.
    El componente instancia el service y delega los comandos.
    """
    _name = "dashboard"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.dashboard import DashboardService
        self._service = DashboardService(app)

    def cmd_abrir(self) -> None:
        return self._service._cmd_dashboard()


class UiEventsComponent(_Component):
    """Event handlers UI — _on_modo_cambio, etc.

    A1 fase 2 (sesión 14): UiEventsMixin → UiEventsService aislado.
    """
    _name = "events"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.ui_events import UiEventsService
        self._service = UiEventsService(app)

    def on_modo_cambio(self) -> None:
        return self._service._on_modo_cambio()

    def on_plataforma_cambio(self, valor=None) -> None:
        return self._service._on_plataforma_cambio(valor)

    def on_motor_cambio(self, motor_name=None) -> None:
        return self._service._on_motor_cambio(motor_name)

    def on_modelo_imagen_cambio(self, modelo_name=None) -> None:
        return self._service._on_modelo_imagen_cambio(modelo_name)

    def on_motor_audio_cambio(self, motor_name=None) -> None:
        return self._service._on_motor_audio_cambio(motor_name)

    def on_audio_filtro_cambio(self, valor=None) -> None:
        return self._service._on_audio_filtro_cambio(valor)

    def on_brief_cambio(self) -> None:
        return self._service._on_brief_cambio()

    def actualizar_motores_video(self) -> None:
        return self._service._actualizar_motores_video()


class MultiPromptComponent(_Component):
    """Mood/Story/Board/Walk — generadores multi-prompt.

    A1 fase 2 (sesión 14): MultiPromptMixin → MultiPromptService aislado.
    """
    _name = "multi"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.multiprompt import MultiPromptService
        self._service = MultiPromptService(app)

    def cmd_moodboard(self) -> None:
        return self._service._cmd_moodboard()

    def cmd_story_sequence(self) -> None:
        return self._service._cmd_story_sequence()

    def cmd_storyboard_video(self) -> None:
        return self._service._cmd_storyboard_video()

    def cmd_storyboard_imagen(self) -> None:
        return self._service._cmd_storyboard_imagen()

    def cmd_random_walk(self) -> None:
        return self._service._cmd_random_walk()


class ModoClienteComponent(_Component):
    """Modo Cliente (brief + 5 propuestas) + Compañero Moodboard.

    A1 fase 2 (sesión 14): ModoClienteMixin → ModoClienteService aislado.
    """
    _name = "cliente"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.modo_cliente import ModoClienteService
        self._service = ModoClienteService(app)

    def cmd_modo_cliente(self) -> None:
        return self._service._cmd_modo_cliente()

    def cmd_companero_moodboard(self) -> None:
        return self._service._cmd_companero_moodboard()


class RefinamientoComponent(_Component):
    """Refinamiento + iteración + diff.

    A1 fase 2 (sesión 14): RefinamientoMixin → RefinamientoService aislado.
    """
    _name = "refinar"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.refinamiento import RefinamientoService
        self._service = RefinamientoService(app)

    def cmd_refinar(self) -> None:
        return self._service.cmd_refinar()

    def cmd_iterar(self) -> None:
        return self._service._cmd_iteracion()

    def refinar_con_instruccion(self, instruccion: str) -> None:
        return self._service._refinar_con_instruccion(instruccion)

    def menu_refinar_especifico(self, event=None) -> None:
        return self._service._menu_refinar_especifico(event)

    def mostrar_diff_refinamiento(self, texto_previo: str, texto_nuevo: str) -> None:
        return self._service._mostrar_diff_refinamiento(texto_previo, texto_nuevo)


class WorkersIaComponent(_Component):
    """Workers IA en threads.

    A1 fase 2 (sesión 14): WorkersIaMixin → WorkersIaService aislado.
    Las @property devuelven referencias a los métodos del service para
    que el caller pueda hacer `threading.Thread(target=self.workers.
    worker_ia, ...)`.
    """
    _name = "workers"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.workers_ia import WorkersIaService
        self._service = WorkersIaService(app)

    @property
    def worker_ia(self):
        return self._service._worker_ia

    @property
    def worker_vision(self):
        return self._service._worker_vision

    @property
    def worker_prompt_traduccion(self):
        return self._service._worker_prompt_traduccion

    @property
    def worker_prompt_quick(self):
        return self._service._worker_prompt_quick

    @property
    def worker_imagen_a_prompt(self):
        return self._service._worker_imagen_a_prompt


class AtajosAyudaComponent(_Component):
    """Atajos de teclado + ventana de ayuda + búsqueda global + tutorial.

    A1 fase 2: convertido a servicio aislado (AtajosAyudaService).
    """
    _name = "atajos"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.atajos_ayuda import AtajosAyudaService
        self._service = AtajosAyudaService(app)

    def bind_shortcuts(self) -> None:
        return self._service._bind_shortcuts()

    def cmd_mostrar_atajos(self) -> str:
        return self._service._cmd_mostrar_atajos()

    def abrir_tutorial(self) -> None:
        return self._service._abrir_tutorial()


class JsonPromptComponent(_Component):
    """Import/export JSON profesional Veo/Sora/Kling.

    A1 fase 2 (sesión 9): el mixin se ha convertido en JsonPromptService,
    una clase aislada que recibe app por composición. Este componente
    instancia el service en su __init__ y delega al él, NO al app.

    Primera demostración del refactor "verdadero A1" — el mixin ya NO
    está heredado en ArquitectoApp, sino que vive como servicio
    independiente accesible vía self.json.
    """
    _name = "json"

    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        # Importación tardía para evitar ciclos
        from modules.json_prompt import JsonPromptService
        self._service = JsonPromptService(app)

    def cmd_importar(self) -> None:
        return self._service._cmd_importar_json_prompt()

    def cmd_exportar(self) -> None:
        return self._service._cmd_exportar_json_prompt()


class AbTestingComponent(_Component):
    """A/B testing 2x2 + comparador de modelos.

    A1 fase 2 (sesión 14): AbTestingMixin → AbTestingService aislado.
    El componente instancia el service y delega los 2 comandos.
    """
    _name = "ab"
    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.ab_testing import AbTestingService
        self._service = AbTestingService(app)

    def cmd_ab_testing(self) -> None:
        return self._service._cmd_ab_testing()

    def cmd_comparar_modelos(self) -> None:
        return self._service._cmd_comparar_modelos()


class PromptsComponent(_Component):
    """Inyección de specs del modelo en system prompts.

    A1 fase 2 (sesión 9): convertido a servicio aislado. PromptsInyeccionMixin
    ya NO heredado en ArquitectoApp; el código vive en PromptsInyeccionService.
    """
    _name = "prompts"

    __slots__ = ("app", "_service")

    def __init__(self, app):
        super().__init__(app)
        from modules.prompts_inyeccion import PromptsInyeccionService
        self._service = PromptsInyeccionService(app)

    def inyectar_specs_modelo(self, system_prompt: str) -> str:
        return self._service._inyectar_specs_modelo(system_prompt)

    def inyectar_specs_video(self, system_prompt: str) -> str:
        return self._service._inyectar_specs_video(system_prompt)

    def inyectar_specs_imagen(self, system_prompt: str) -> str:
        return self._service._inyectar_specs_imagen(system_prompt)

    def inyectar_specs_audio(self, system_prompt: str) -> str:
        return self._service._inyectar_specs_audio(system_prompt)

    def inyectar_destino(self, system_prompt: str) -> str:
        return self._service._inyectar_destino(system_prompt)

    def construir_modelo_info(self) -> str:
        return self._service.construir_modelo_info()


def install_components(app) -> None:
    """Instala los 10 componentes como atributos del app."""
    app.core = CoreComponent(app)
    app.ui = UIComponent(app)
    app.creative = CreativeComponent(app)
    app.workflow = WorkflowComponent(app)
    app.analysis = AnalysisComponent(app)
    app.data = DataComponent(app)
    app.backup = BackupComponent(app)
    app.dialogs = DialogsComponent(app)
    app.prompts = PromptsComponent(app)
    app.ab = AbTestingComponent(app)
    app.json = JsonPromptComponent(app)
    app.refinar = RefinamientoComponent(app)
    app.workers = WorkersIaComponent(app)
    app.atajos = AtajosAyudaComponent(app)
    app.cliente = ModoClienteComponent(app)
    app.multi = MultiPromptComponent(app)
    app.adn = AdnVisualComponent(app)
    app.sesion = SesionVideoComponent(app)
    app.dashboard = DashboardComponent(app)
    app.events = UiEventsComponent(app)
    app.footer = UiFooterComponent(app)
    logger.debug(
        "Componentes instalados: core, ui, creative, workflow, analysis, data, "
        "backup, dialogs, prompts, ab, json, refinar, workers, atajos, cliente, "
        "multi, adn, sesion, dashboard, events, footer"
    )
