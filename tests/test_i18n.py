"""Tests para modules/i18n.py — interfaz bilingüe ES/EN."""
import ast
from pathlib import Path

from modules import i18n

ROOT = Path(__file__).resolve().parent.parent


def _reset():
    i18n.set_idioma("es")


def test_es_devuelve_el_texto_original():
    _reset()
    assert i18n.tr("Modelo") == "Modelo"
    assert i18n.tr("Cualquier cosa sin traducir") == "Cualquier cosa sin traducir"


def test_en_traduce_lo_conocido():
    i18n.set_idioma("en")
    try:
        assert i18n.tr("Modelo") == "Model"
        assert i18n.tr("Estilo") == "Style"
        assert i18n.tr("Cerrar") == "Close"
        assert i18n.tr("▶ Generar") == "▶ Generate"
    finally:
        _reset()


def test_en_fallback_al_espanol_si_no_hay_traduccion():
    i18n.set_idioma("en")
    try:
        # Texto que NO está en TRADUCCIONES → devuelve el español tal cual.
        assert i18n.tr("Texto inventado xyz") == "Texto inventado xyz"
    finally:
        _reset()


def test_set_idioma_normaliza():
    i18n.set_idioma("english")
    assert i18n.get_idioma() == "en"
    i18n.set_idioma("ES")
    assert i18n.get_idioma() == "es"
    i18n.set_idioma(None)
    assert i18n.get_idioma() == "es"
    _reset()


def test_traducciones_no_vacias_y_sin_claves_vacias():
    assert len(i18n.TRADUCCIONES) > 10
    assert all(k and v for k, v in i18n.TRADUCCIONES.items())


def test_cobertura_todo_tr_literal_esta_traducido():
    """Todo tr('literal') del código debe tener entrada en TRADUCCIONES.

    Si este test falla, el texto nuevo se mostraría en español en la UI
    inglesa (el fallback lo hace invisible en desarrollo). Los tr(variable)
    dinámicos no se pueden comprobar aquí; sus valores se añaden a mano.
    """
    faltan = {}
    for py in list(ROOT.glob("*.py")) + list((ROOT / "modules").glob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and node.args):
                continue
            f = node.func
            name = f.id if isinstance(f, ast.Name) else (
                f.attr if isinstance(f, ast.Attribute) else None)
            arg = node.args[0]
            if (name == "tr" and isinstance(arg, ast.Constant)
                    and isinstance(arg.value, str)
                    and arg.value not in i18n.TRADUCCIONES):
                faltan.setdefault(arg.value, f"{py.name}:{node.lineno}")
    assert not faltan, (
        f"{len(faltan)} textos tr() sin traducción EN: "
        + "; ".join(f"{t!r} ({loc})" for t, loc in list(faltan.items())[:10]))
