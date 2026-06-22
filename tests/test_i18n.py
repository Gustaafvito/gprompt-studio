"""Tests para modules/i18n.py — interfaz bilingüe ES/EN."""
from modules import i18n


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
