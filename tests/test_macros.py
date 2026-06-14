"""Tests de las macros (recetas) de tools_workflow.

Cubren la consistencia entre las macros de ejemplo y el catálogo de acciones
(sesión 20): un label mal escrito en un ejemplo sería un paso no-op silencioso,
así que lo cazamos aquí.
"""
from modules.tools_workflow import (
    ACCIONES_MACRO,
    MACROS_EJEMPLO,
    macro_valida,
    parsear_macros_importadas,
)


def test_acciones_macro_no_vacio():
    assert isinstance(ACCIONES_MACRO, dict) and ACCIONES_MACRO


def test_incluye_la_accion_adaptar_modelo():
    assert ACCIONES_MACRO.get("🎯 Adaptar al modelo activo") == "adaptar_modelo"


def test_incluye_la_accion_optimizar_1pasada():
    assert ACCIONES_MACRO.get("⚡ Optimizar (1 pasada)") == "optimizar_1pasada"
    from modules.tools_workflow import ToolsWorkflowService
    assert hasattr(ToolsWorkflowService, "_cmd_optimizar_1pasada")


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


# ── import/export de macros (Skills portables) ───────────────────

def test_macro_valida_acepta_macro_correcta():
    m = {"nombre": "Test", "pasos": ["✨ Generar prompt", "📊 Scoring auto"]}
    assert macro_valida(m) == m


def test_macro_valida_filtra_pasos_invalidos():
    m = {"nombre": "Test", "pasos": ["✨ Generar prompt", "paso inventado", 123]}
    r = macro_valida(m)
    assert r == {"nombre": "Test", "pasos": ["✨ Generar prompt"]}


def test_macro_valida_rechaza_sin_nombre_o_sin_pasos_validos():
    assert macro_valida({"nombre": "", "pasos": ["✨ Generar prompt"]}) is None
    assert macro_valida({"nombre": "X", "pasos": ["nada válido"]}) is None
    assert macro_valida({"nombre": "X", "pasos": "no es lista"}) is None
    assert macro_valida("ni siquiera un dict") is None


def test_parsear_acepta_dict_lista_y_envoltorio():
    una = {"nombre": "A", "pasos": ["✨ Generar prompt"]}
    assert parsear_macros_importadas(una) == [una]                 # dict suelto
    assert parsear_macros_importadas([una, una]) == [una, una]     # lista
    assert parsear_macros_importadas({"macros": [una]}) == [una]   # envoltorio


def test_parsear_descarta_invalidas_y_tipos_raros():
    data = [{"nombre": "Ok", "pasos": ["📊 Scoring auto"]}, {"basura": 1}, 42]
    assert parsear_macros_importadas(data) == [{"nombre": "Ok", "pasos": ["📊 Scoring auto"]}]
    assert parsear_macros_importadas("texto") == []


def test_export_import_methods_existen():
    from modules.tools_workflow import ToolsWorkflowService
    assert hasattr(ToolsWorkflowService, "_exportar_macros_a_archivo")
    assert hasattr(ToolsWorkflowService, "_importar_macros_de_archivo")
