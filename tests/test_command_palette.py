"""Tests del command palette (Ctrl+K) — lógica de filtrado."""
from modules.command_palette import MAX_RESULTADOS, filtrar_comandos

CMDS = [
    ("🛠 Herramientas", "🧰 Negative builder", "cmd1"),
    ("📁 Datos", "📋 Historial", "cmd2"),
    ("⚙️ Workflow", "🆚 A/B Testing", "cmd3"),
    ("📁 Datos", "🌟 Estrellas", "cmd4"),
]


def test_sin_filtro_devuelve_todo():
    assert filtrar_comandos(CMDS, "") == CMDS
    assert filtrar_comandos(CMDS, None) == CMDS


def test_filtra_por_label_case_insensitive():
    res = filtrar_comandos(CMDS, "NEGATIVE")
    assert len(res) == 1 and res[0][2] == "cmd1"


def test_filtra_por_grupo():
    res = filtrar_comandos(CMDS, "datos")
    assert [c[2] for c in res] == ["cmd2", "cmd4"]


def test_multi_palabra_combina_grupo_y_label():
    res = filtrar_comandos(CMDS, "datos historial")
    assert len(res) == 1 and res[0][2] == "cmd2"


def test_sin_coincidencias():
    assert filtrar_comandos(CMDS, "xyzzy") == []


def test_max_resultados_razonable():
    assert 5 <= MAX_RESULTADOS <= 30
