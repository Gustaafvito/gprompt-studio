"""Tests de integridad del contenido del tutorial (data/tutorial.json).

Tras expandirlo a 42 pasos (sesión 20), conviene blindar que el JSON sigue
bien formado: ids secuenciales (el índice lateral navega por id-1) y campos
obligatorios presentes.
"""
from modules.tutorial import cargar_tutorial


def test_carga_y_tiene_pasos():
    t = cargar_tutorial()
    pasos = t.get("pasos", [])
    assert len(pasos) >= 42


def test_ids_secuenciales_desde_1():
    pasos = cargar_tutorial()["pasos"]
    ids = [p["id"] for p in pasos]
    assert ids == list(range(1, len(pasos) + 1)), (
        "los ids deben ser 1..N sin huecos: el índice lateral navega por id-1"
    )


def test_campos_obligatorios_y_no_vacios():
    for p in cargar_tutorial()["pasos"]:
        assert p.get("titulo"), f"paso {p.get('id')} sin título"
        assert p.get("descripcion"), f"paso {p.get('id')} sin descripción"
        assert "accion" in p, f"paso {p.get('id')} sin clave 'accion'"


def test_titulos_unicos():
    titulos = [p["titulo"] for p in cargar_tutorial()["pasos"]]
    assert len(titulos) == len(set(titulos))
