"""Tests para el desplegable buscador+scroll (modules/searchable_dropdown)."""
from modules.searchable_dropdown import _es_separador


class TestEsSeparador:
    def test_cabeceras_de_grupo(self):
        assert _es_separador("── Familia FLUX ──") is True
        assert _es_separador("──") is True
        assert _es_separador("  ── Nano Banana ──") is True

    def test_modelos_normales(self):
        assert _es_separador("FLUX.1 [dev]") is False
        assert _es_separador("Nepotism") is False
        assert _es_separador("Z-Image-Base") is False

    def test_no_string(self):
        assert _es_separador(None) is False
        assert _es_separador(123) is False
