"""Tests para CoreMixin._parsear_variaciones.

Es un método de instancia pero no usa atributos de self — es una
función pura disfrazada. Se testea pasando un objeto vacío como self.
"""
import pytest

from modules.core import CoreMixin


class _DummyApp:
    """Stand-in para self. CoreMixin._parsear_variaciones no toca atributos."""
    pass


def _parsear(texto, n=None):
    return CoreMixin._parsear_variaciones(_DummyApp(), texto, n_esperado=n)


class TestParsearVariaciones:

    def test_tres_bloques_numerados(self):
        texto = (
            "Variación 1.\nPOSITIVE PROMPT: una chica en bosque\n"
            "Variación 2.\nPOSITIVE PROMPT: una chica en ciudad\n"
            "Variación 3.\nPOSITIVE PROMPT: una chica en playa"
        )
        result = _parsear(texto, n=3)
        assert len(result) == 3
        assert "bosque" in result[0]
        assert "ciudad" in result[1]
        assert "playa" in result[2]

    def test_separadores_con_guiones(self):
        texto = (
            "POSITIVE PROMPT: primer prompt con suficiente longitud para pasar el filtro\n"
            "---\n"
            "POSITIVE PROMPT: segundo prompt también con longitud adecuada\n"
            "---\n"
            "POSITIVE PROMPT: tercer prompt completo y detallado"
        )
        result = _parsear(texto, n=3)
        assert len(result) >= 2

    def test_texto_corto_devuelve_vacio(self):
        # Sin bloques claros y demasiado corto
        assert _parsear("hola") == []

    def test_string_vacio(self):
        assert _parsear("") == []

    def test_filtra_preambulo_cuando_hay_mas_bloques_que_n(self):
        # El LLM mete un preámbulo + 3 prompts; con n=3 debe filtrar
        # el preámbulo y quedarse con los 3 con POSITIVE PROMPT
        texto = (
            "Aquí tienes las tres variaciones que pediste para tu prompt\n"
            "Variación 1.\nPOSITIVE PROMPT: primero detallado de la idea\n"
            "Variación 2.\nPOSITIVE PROMPT: segundo detallado de la idea\n"
            "Variación 3.\nPOSITIVE PROMPT: tercero detallado de la idea"
        )
        result = _parsear(texto, n=3)
        assert len(result) == 3
        # El preámbulo NO debería estar
        for r in result:
            assert "Aquí tienes" not in r

    def test_acepta_formato_prompt_n(self):
        # Formato alternativo "Prompt N." en lugar de "Variación N."
        texto = (
            "Prompt 1.\nPOSITIVE PROMPT: idea uno con suficiente texto\n"
            "Prompt 2.\nPOSITIVE PROMPT: idea dos con suficiente texto"
        )
        result = _parsear(texto, n=2)
        assert len(result) == 2

    def test_limpia_asteriscos_y_almohadillas(self):
        # El parser limpia ** y # antes de procesar
        texto = (
            "**Variación 1.**\nPOSITIVE PROMPT: prompt con marcadores markdown que se eliminan\n"
            "**Variación 2.**\nPOSITIVE PROMPT: segundo prompt también con texto suficiente"
        )
        result = _parsear(texto, n=2)
        # Ningún resultado debería contener **
        for r in result:
            assert "**" not in r
            assert "#" not in r


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
