"""Tests de integridad del contenido del tutorial (data/tutorial.json).

Tras expandirlo a 42 pasos (sesión 20), conviene blindar que el JSON sigue
bien formado: ids secuenciales (el índice lateral navega por id-1) y campos
obligatorios presentes.
"""
import json
from pathlib import Path

from modules.tutorial import cargar_tutorial

DATA = Path(__file__).resolve().parent.parent / "data"


def _pasos(nombre):
    # Directamente del fichero: cargar_tutorial() tiene caché y sirve un
    # solo idioma, el de la interfaz.
    return json.loads((DATA / nombre).read_text(encoding="utf-8"))["pasos"]


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


def test_espanol_e_ingles_van_a_la_par():
    """Mismos pasos, en el mismo orden y con las mismas acciones.

    El tutorial inglés es otro fichero. Un paso añadido solo en español
    dejaría la interfaz inglesa con un índice más corto, y el progreso
    guardado —que va por número de paso— apuntaría a pasos distintos.
    """
    es, en = _pasos("tutorial.json"), _pasos("tutorial.en.json")
    assert [p["id"] for p in es] == [p["id"] for p in en]
    assert [p["accion"] for p in es] == [p["accion"] for p in en]
    sin_traducir = [p["id"] for p, q in zip(es, en)
                    if p["descripcion"] == q["descripcion"]]
    assert not sin_traducir, f"pasos sin traducir al inglés: {sin_traducir}"


def test_las_herramientas_nuevas_estan_en_el_tutorial():
    # Crear desde imágenes y el Cortometraje llegaron sin paso propio, y el
    # paso de narrativa describía cuatro botones de cinco.
    for nombre, textos in (("tutorial.json", ("CREAR DESDE IMÁGENES", "CORTOMETRAJE")),
                           ("tutorial.en.json", ("CREATE FROM IMAGES", "SHORT FILM"))):
        titulos = " ".join(p["titulo"] for p in _pasos(nombre))
        for texto in textos:
            assert texto in titulos, f"{nombre}: falta el paso de {texto}"
    narrativa = next(p for p in _pasos("tutorial.json") if p["id"] == 32)
    assert "Corto" in narrativa["descripcion"]


def test_la_casilla_de_completado_no_lleva_otra_casilla_en_el_texto():
    # «✅ Marcar como completado» junto a la casilla real se veía como dos
    # casillas, la segunda siempre marcada.
    import ast
    from pathlib import Path
    fuente = (Path(__file__).resolve().parent.parent / "modules" / "tutorial.py").read_text(encoding="utf-8")
    for nodo in ast.walk(ast.parse(fuente)):
        if (isinstance(nodo, ast.Call) and getattr(nodo.func, "attr", "") == "CTkCheckBox"):
            for kw in nodo.keywords:
                if kw.arg == "text" and isinstance(kw.value, ast.Call):
                    texto = kw.value.args[0].value
                    assert not texto.startswith(("✅", "☑", "✔")), texto
