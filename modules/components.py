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
    """Base: delega cualquier atributo no encontrado a self.app."""

    __slots__ = ("app",)
    _name = "component"

    def __init__(self, app):
        self.app = app

    def __getattr__(self, name):
        if name.startswith("_") or name == "app":
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
    """Workers, comandos principales, estado (CoreMixin)."""
    _name = "core"


class UIComponent(_Component):
    """Construcción de UI: _build_* y helpers (UIBuildersMixin)."""
    _name = "ui"


class CreativeComponent(_Component):
    """Moodboard, ADN, Negative Builder, Paleta (ToolsCreativeMixin)."""
    _name = "creative"


class WorkflowComponent(_Component):
    """Macros, A/B Testing, Cron, Proyectos, Sesión (ToolsWorkflowMixin)."""
    _name = "workflow"


class AnalysisComponent(_Component):
    """Estadísticas, Scoring, Auto-improve, Critique (ToolsAnalysisMixin)."""
    _name = "analysis"


class DataComponent(_Component):
    """Historial, Favoritos, Estrellas, Plantillas (DataMgmtMixin)."""
    _name = "data"


class BackupComponent(_Component):
    """Backup, Restore, CSV, Export CLI, Search (BackupExportMixin)."""
    _name = "backup"


class DialogsComponent(_Component):
    """API Keys, Dashboard, Theme, Wizard (DialogsMixin)."""
    _name = "dialogs"


class AdnVisualComponent(_Component):
    """ADN Visual + biblioteca de rasgos (AdnVisualMixin).
    Noveno servicio del refactor A1.
    """
    _name = "adn"

    def cmd_adn_visual(self) -> None:
        return self.app._cmd_adn_visual()

    def cmd_ver_biblioteca(self) -> None:
        return self.app._cmd_ver_biblioteca_adn()


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
    """Dashboard panel — pantalla de bienvenida (DashboardMixin).
    Decimoprimer servicio del refactor A1.
    """
    _name = "dashboard"

    def cmd_abrir(self) -> None:
        return self.app._cmd_dashboard()


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
    """Mood/Story/Board/Walk — generadores multi-prompt (MultiPromptMixin).
    Octavo servicio del refactor A1.
    """
    _name = "multi"

    def cmd_moodboard(self) -> None:
        return self.app._cmd_moodboard()

    def cmd_story_sequence(self) -> None:
        return self.app._cmd_story_sequence()

    def cmd_storyboard_video(self) -> None:
        return self.app._cmd_storyboard_video()

    def cmd_random_walk(self) -> None:
        return self.app._cmd_random_walk()


class ModoClienteComponent(_Component):
    """Modo Cliente (brief + 5 propuestas) + Compañero Moodboard
    (ModoClienteMixin). Séptimo servicio del refactor A1.
    """
    _name = "cliente"

    def cmd_modo_cliente(self) -> None:
        return self.app._cmd_modo_cliente()

    def cmd_companero_moodboard(self) -> None:
        return self.app._cmd_companero_moodboard()


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
    """Workers IA en threads (WorkersIaMixin).

    Quinto servicio del refactor A1. Los workers se invocan via
    threading.Thread(target=...); exponemos referencias a los métodos
    para que el caller use self.workers.worker_ia en vez de
    self._worker_ia.
    """
    _name = "workers"

    @property
    def worker_ia(self):
        return self.app._worker_ia

    @property
    def worker_vision(self):
        return self.app._worker_vision

    @property
    def worker_prompt_traduccion(self):
        return self.app._worker_prompt_traduccion

    @property
    def worker_prompt_quick(self):
        return self.app._worker_prompt_quick

    @property
    def worker_imagen_a_prompt(self):
        return self.app._worker_imagen_a_prompt


class AtajosAyudaComponent(_Component):
    """Atajos de teclado + ventana de ayuda + búsqueda global + tutorial
    (AtajosAyudaMixin).

    Sexto servicio del refactor A1. Solo exponemos los 3 entry points
    externos (bind, mostrar_atajos, abrir_tutorial). Los handlers
    individuales de atajos se invocan internamente desde lambdas
    registradas en bind_shortcuts.
    """
    _name = "atajos"

    def bind_shortcuts(self) -> None:
        return self.app._bind_shortcuts()

    def cmd_mostrar_atajos(self) -> str:
        return self.app._cmd_mostrar_atajos()

    def abrir_tutorial(self) -> None:
        return self.app._abrir_tutorial()


class JsonPromptComponent(_Component):
    """Import/export JSON profesional Veo/Sora/Kling (JsonPromptMixin).

    Tercer servicio del refactor A1. Solo expone los 2 entry points
    (los 3 métodos internos _aplicar_json_a_app / _mostrar_resumen_import
    / _mostrar_modal_export son privados del mixin).
    """
    _name = "json"

    def cmd_importar(self) -> None:
        return self.app._cmd_importar_json_prompt()

    def cmd_exportar(self) -> None:
        return self.app._cmd_exportar_json_prompt()


class AbTestingComponent(_Component):
    """A/B testing 2x2 + comparador de modelos (AbTestingMixin).

    Segundo servicio del refactor A1. Solo expone los 2 puntos de
    entrada (los métodos internos _ab_lanzar / _mostrar_ab_grid /
    _abrir_ventana_comparacion siguen llamándose vía self.X desde
    dentro del mixin).
    """
    _name = "ab"

    def cmd_ab_testing(self) -> None:
        return self.app._cmd_ab_testing()

    def cmd_comparar_modelos(self) -> None:
        return self.app._cmd_comparar_modelos()


class PromptsComponent(_Component):
    """Inyección de specs del modelo en system prompts (PromptsInyeccionMixin).

    Primer servicio "real" con API pública explícita (nombres sin underscore).
    Patrón piloto para A1 (Mixins → Composición pura). El mixin sigue
    heredado en ArquitectoApp por compatibilidad, pero los call sites se
    pueden migrar gradualmente a `self.prompts.X()`. Cuando todos estén
    migrados, se puede quitar el mixin del MRO.
    """
    _name = "prompts"

    def inyectar_specs_modelo(self, system_prompt: str) -> str:
        return self.app._inyectar_specs_modelo(system_prompt)

    def inyectar_specs_video(self, system_prompt: str) -> str:
        return self.app._inyectar_specs_video(system_prompt)

    def inyectar_specs_imagen(self, system_prompt: str) -> str:
        return self.app._inyectar_specs_imagen(system_prompt)

    def inyectar_specs_audio(self, system_prompt: str) -> str:
        return self.app._inyectar_specs_audio(system_prompt)

    def inyectar_destino(self, system_prompt: str) -> str:
        return self.app._inyectar_destino(system_prompt)

    def construir_modelo_info(self) -> str:
        return self.app.construir_modelo_info()


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
