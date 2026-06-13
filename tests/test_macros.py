"""Tests de las macros (recetas) de tools_workflow.

Cubren la consistencia entre las macros de ejemplo y el catálogo de acciones
(sesión 20): un label mal escrito en un ejemplo sería un paso no-op silencioso,
así que lo cazamos aquí.
"""
from modules.tools_workflow import ACCIONES_MACRO, MACROS_EJEMPLO


def test_acciones_macro_no_vacio():
    assert isinstance(ACCIONES_MACRO, dict) and ACCIONES_MACRO


def test_incluye_la_accion_adaptar_modelo():
    assert ACCIONES_MACRO.get("🎯 Adaptar al modelo activo") == "adaptar_modelo"


def test_adaptar_modelo_expuesto_como_comando_directo():
    """adaptar_modelo debe ser invocable fuera de las macros (menú Herramientas):
    método en el servicio + delegación en el componente."""
    from modules.components import WorkflowComponent
    from modules.tools_workflow import ToolsWorkflowService
    assert hasattr(ToolsWorkflowService, "_cmd_adaptar_modelo")
    assert callable(getattr(WorkflowComponent, "cmd_adaptar_modelo", None))


def test_ejemplos_bien_formados():
    assert MACROS_EJEMPLO, "debe haber al menos una macro de ejemplo"
    for m in MACROS_EJEMPLO:
        assert m.get("nombre"), "cada macro de ejemplo necesita nombre"
        assert m.get("pasos"), f"la macro '{m.get('nombre')}' no tiene pasos"


def test_todos_los_pasos_de_ejemplo_son_acciones_validas():
    """Cada paso de cada macro de ejemplo debe existir en ACCIONES_MACRO."""
    for m in MACROS_EJEMPLO:
        for paso in m["pasos"]:
            assert paso in ACCIONES_MACRO, (
                f"la macro '{m['nombre']}' referencia un label inexistente: {paso!r}"
            )


def test_nombres_de_ejemplo_unicos():
    nombres = [m["nombre"] for m in MACROS_EJEMPLO]
    assert len(nombres) == len(set(nombres))
