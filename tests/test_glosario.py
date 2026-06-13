"""Tests de integridad del glosario (data/glosario.json — Modo educativo).

Ampliado a 56 entradas (sesión 20) con las features nuevas. Blindamos que
el JSON sigue bien formado y que cada entrada usa una categoría válida.
"""
import json
import os

_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "glosario.json")


def _cargar():
    with open(_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_estructura_basica():
    g = _cargar()
    assert "categorias" in g and "entradas" in g
    assert g["categorias"] and g["entradas"]


def test_entradas_campos_obligatorios():
    for e in _cargar()["entradas"]:
        assert e.get("titulo"), f"entrada sin título: {e}"
        assert e.get("descripcion"), f"{e.get('titulo')} sin descripción"
        assert "categoria" in e and "accion" in e


def test_categorias_validas():
    g = _cargar()
    cats = set(g["categorias"])
    for e in g["entradas"]:
        assert e["categoria"] in cats, (
            f"'{e['titulo']}' usa categoría inexistente: {e['categoria']!r}"
        )


def test_titulos_unicos():
    titulos = [e["titulo"] for e in _cargar()["entradas"]]
    assert len(titulos) == len(set(titulos))


def test_cubre_features_nuevas():
    """Las features recientes deben tener entrada en el glosario."""
    titulos = " | ".join(e["titulo"] for e in _cargar()["entradas"]).upper()
    for clave in ("OPTIMIZADOR", "COPILOTO", "STORYBOARD", "AVATAR", "DASHBOARD",
                  "COSTE", "MAX_CHARS", "MODELO ACTIVO"):
        assert clave in titulos, f"falta entrada de glosario para: {clave}"
