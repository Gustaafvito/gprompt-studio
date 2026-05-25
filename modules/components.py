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
    """Instala los 9 componentes como atributos del app."""
    app.core = CoreComponent(app)
    app.ui = UIComponent(app)
    app.creative = CreativeComponent(app)
    app.workflow = WorkflowComponent(app)
    app.analysis = AnalysisComponent(app)
    app.data = DataComponent(app)
    app.backup = BackupComponent(app)
    app.dialogs = DialogsComponent(app)
    app.prompts = PromptsComponent(app)
    logger.debug("Componentes instalados: core, ui, creative, workflow, analysis, data, backup, dialogs, prompts")
