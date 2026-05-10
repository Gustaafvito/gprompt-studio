"""G-Prompt Studio - Módulos extraídos.

Cada módulo define una mixin class que GPromptApp hereda.
"""

from .ui_builders import UIBuildersMixin
from .tools_creative import ToolsCreativeMixin
from .tools_workflow import ToolsWorkflowMixin
from .tools_analysis import ToolsAnalysisMixin
from .data_mgmt import DataMgmtMixin
from .backup_export import BackupExportMixin
from .dialogs import DialogsMixin
from .core import CoreMixin

__all__ = [
    "UIBuildersMixin",
    "ToolsCreativeMixin",
    "ToolsWorkflowMixin",
    "ToolsAnalysisMixin",
    "DataMgmtMixin",
    "BackupExportMixin",
    "DialogsMixin",
    "CoreMixin",
]
