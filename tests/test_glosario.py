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
                  "COSTE", "MAX_CHARS", "MODELO ACTIVO", "CREAR DESDE IMÁGENES",
                  "CORTOMETRAJE", "VÍDEO POR REFERENCIA"):
        assert clave in titulos, f"falta entrada de glosario para: {clave}"


def test_espanol_e_ingles_van_a_la_par():
    """Mismas entradas, en el mismo orden, categoría y acción, y traducidas.

    El glosario inglés es otro fichero: una entrada añadida solo en español
    no existiría para quien use la interfaz en inglés.
    """
    es = _cargar()
    with open(_PATH.replace("glosario.json", "glosario.en.json"), encoding="utf-8") as f:
        en = json.load(f)
    assert len(es["categorias"]) == len(en["categorias"])
    assert len(es["entradas"]) == len(en["entradas"])
    for a, b in zip(es["entradas"], en["entradas"]):
        assert a["accion"] == b["accion"], a["titulo"]
        assert (es["categorias"].index(a["categoria"])
                == en["categorias"].index(b["categoria"])), a["titulo"]
        # Título O descripción pueden coincidir por separado: «CONTROLNET» se
        # llama igual, y la descripción de los estilos artísticos es una
        # lista de nombres en inglés. Las dos cosas a la vez, no.
        assert (a["titulo"], a["descripcion"]) != (b["titulo"], b["descripcion"]), \
            f"sin traducir: {a['titulo']}"
