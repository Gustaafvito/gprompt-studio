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
    """Construcción de UI: _build_* y helpers (UIBuildersMixin).

    Métodos del mixin: _build_header, _build_modo, _build_video_panel,
    _build_audio_panel, _build_modelo_imagen_panel, _build_destino_panel,
    _build_tabs_centrales, _build_ajustes_extra, _build_estilos,
    _build_negative, _build_entrada, _build_acciones, _build_estado,
    _build_salida. Todos delegados vía __getattr__.

    UI no tiene "entry points" propiamente (son helpers internos del
    constructor de la app). El componente existe para consistencia.
    """
    _name = "ui"


class CreativeComponent(_Component):
    """Moodboard, ADN, Negative Builder, Paleta (ToolsCreativeMixin).
    Decimotercer servicio del refactor A1.
    """
    _name = "creative"

    def cmd_negative_builder(self) -> None:
        return self.app._cmd_negative_builder()

    def cmd_color_palette(self) -> None:
        return self.app._cmd_color_palette()

    def cmd_anclaje_visual(self) -> None:
        return self.app._cmd_anclaje_visual()

    def cmd_negative_optimo(self) -> None:
        return self.app._cmd_negative_optimo()

    def cmd_solo_negative(self) -> None:
        return self.app._cmd_solo_negative()

    def cmd_modo_focus(self) -> None:
        return self.app._cmd_modo_focus()

    def cmd_grupo_personajes(self) -> None:
        return self.app._cmd_grupo_personajes()


class WorkflowComponent(_Component):
    """Macros, Cron, Proyectos, Versiones, Búsqueda global, etc.
    (ToolsWorkflowMixin). Decimocuarto servicio del refactor A1.
    """
    _name = "workflow"

    def cmd_cron_prompts(self) -> None:
        return self.app._cmd_cron_prompts()

    def cmd_proyectos(self) -> None:
        return self.app._cmd_proyectos()

    def cmd_versiones_prompt(self) -> None:
        return self.app._cmd_versiones_prompt()

    def abrir_macros(self) -> None:
        return self.app._abrir_macros()

    def cmd_convertir_a_video(self) -> None:
        return self.app._cmd_convertir_a_video()

    def cmd_previsualizar(self) -> None:
        return self.app.cmd_previsualizar()


class AnalysisComponent(_Component):
    """Estadísticas, Scoring, Auto-improve, Critique (ToolsAnalysisMixin).
    Decimoquinto servicio del refactor A1.
    """
    _name = "analysis"

    def cmd_modo_educativo(self) -> None:
        return self.app._cmd_modo_educativo()

    def cmd_critica_historial(self) -> None:
        return self.app._cmd_critica_historial()

    def cmd_automejora_periodica(self) -> None:
        return self.app._cmd_automejora_periodica()

    def abrir_estadisticas(self) -> None:
        return self.app._abrir_estadisticas()

    def cmd_scoring(self) -> None:
        return self.app._cmd_scoring()

    def detectar_nsfw_auto(self, idea: str | None = None) -> bool:
        return self.app._detectar_nsfw_auto(idea)

    def guardar_seed_favorito(self) -> None:
        return self.app._guardar_seed_favorito()

    def abrir_seeds_favoritos(self) -> None:
        return self.app._abrir_seeds_favoritos()

    def autocompletar_tags(self, event=None) -> None:
        return self.app._autocompletar_tags(event)

    def abrir_atajos_tags(self) -> None:
        return self.app._abrir_atajos_tags()

    def copiar_comfyui_json(self) -> None:
        return self.app._copiar_comfyui_json()

    def traducir_salida(self) -> None:
        return self.app._traducir_salida()

    def mostrar_consejo_contextual(self, modelo_name: str, specs: dict) -> None:
        return self.app._mostrar_consejo_contextual(modelo_name, specs)

    def cmd_modal_compatibilidad(self) -> None:
        return self.app._cmd_modal_compatibilidad()


class DataComponent(_Component):
    """Historial, Favoritos, Estrellas, Plantillas, Snippets, Imagen
    (DataMgmtMixin). Decimosexto servicio del refactor A1.
    """
    _name = "data"

    def cmd_guardar_plantilla(self) -> None:
        return self.app._cmd_guardar_plantilla()

    def cmd_borrar_plantilla(self) -> None:
        return self.app._cmd_borrar_plantilla()

    def guardar_favorito(self) -> None:
        return self.app._guardar_favorito()

    def guardar_estrella(self) -> None:
        return self.app._guardar_estrella()

    def repetir_ultima_config(self) -> None:
        return self.app._repetir_ultima_config()

    def cmd_gestionar_snippets(self) -> None:
        return self.app._cmd_gestionar_snippets()

    def abrir_snippets(self) -> None:
        return self.app._abrir_snippets()

    def abrir_formulas(self) -> None:
        return self.app._abrir_formulas()

    def abrir_biblioteca(self) -> None:
        return self.app._abrir_biblioteca()

    def cmd_duplicar_a_historial(self, event=None) -> None:
        return self.app._cmd_duplicar_a_historial(event)

    def idea_aleatoria_historial(self) -> None:
        return self.app._idea_aleatoria_historial()


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
    """API Keys, Tema, Preferencias, Acerca de, Tokens
    (DialogsMixin). Decimoctavo servicio del refactor A1.

    NOTA: _cmd_dashboard ya migrado a DashboardComponent (sesión 6).
    """
    _name = "dialogs"

    def cmd_configurar_api_keys(self, provider_focus=None) -> None:
        return self.app._cmd_configurar_api_keys(provider_focus)

    def cmd_toggle_tema(self) -> None:
        return self.app._cmd_toggle_tema()

    def cmd_acerca_de(self) -> None:
        return self.app._cmd_acerca_de()

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
    """Grabación de sesión + tutorial vídeo (SesionVideoMixin).
    Décimo servicio del refactor A1.

    NOTA: _sesion_log se usa desde decenas de mixins como helper de
    logging. NO migrado a este componente para evitar refactor masivo.
    Solo expone el entry point principal (toggle de grabación).
    """
    _name = "sesion"

    def cmd_grabar_toggle(self) -> None:
        return self.app._cmd_sesion_grabar_toggle()


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
    """Event handlers UI (UiEventsMixin) — _on_modo_cambio, etc.
    Decimosegundo servicio del refactor A1.

    Estos handlers se invocan desde MUY muchos sitios (>30 call sites
    en 8+ archivos). El componente se expone para CÓDIGO NUEVO pero
    los call sites existentes se mantienen con `self._on_*` (migración
    incremental cuando se toque cada archivo).
    """
    _name = "events"

    def on_modo_cambio(self) -> None:
        return self.app._on_modo_cambio()

    def on_plataforma_cambio(self, valor=None) -> None:
        return self.app._on_plataforma_cambio(valor)

    def on_motor_cambio(self, motor_name=None) -> None:
        return self.app._on_motor_cambio(motor_name)

    def on_modelo_imagen_cambio(self, modelo_name=None) -> None:
        return self.app._on_modelo_imagen_cambio(modelo_name)

    def on_motor_audio_cambio(self, motor_name=None) -> None:
        return self.app._on_motor_audio_cambio(motor_name)

    def on_audio_filtro_cambio(self, valor=None) -> None:
        return self.app._on_audio_filtro_cambio(valor)

    def on_brief_cambio(self) -> None:
        return self.app._on_brief_cambio()

    def actualizar_motores_video(self) -> None:
        return self.app._actualizar_motores_video()


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
    """Refinamiento de prompts + iteración + diff (RefinamientoMixin).

    Cuarto servicio del refactor A1. Expone los entry points usados
    desde otros mixins/UI:
      - cmd_refinar
      - cmd_iterar
      - refinar_con_instruccion(instruccion)
      - menu_refinar_especifico(event=None)
      - mostrar_diff_refinamiento(previo, nuevo)
    """
    _name = "refinar"

    def cmd_refinar(self) -> None:
        return self.app.cmd_refinar()

    def cmd_iterar(self) -> None:
        return self.app._cmd_iteracion()

    def refinar_con_instruccion(self, instruccion: str) -> None:
        return self.app._refinar_con_instruccion(instruccion)

    def menu_refinar_especifico(self, event=None) -> None:
        return self.app._menu_refinar_especifico(event)

    def mostrar_diff_refinamiento(self, texto_previo: str, texto_nuevo: str) -> None:
        return self.app._mostrar_diff_refinamiento(texto_previo, texto_nuevo)


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
    logger.debug(
        "Componentes instalados: core, ui, creative, workflow, analysis, data, "
        "backup, dialogs, prompts, ab, json, refinar, workers, atajos, cliente, "
        "multi, adn, sesion, dashboard, events"
    )
