"""Tests para los helpers puros de modules/json_prompt.py.

Cubre las 3 funciones de reparación de JSON copiado de webs:
  • _limpiar_json_de_newlines
  • _limpiar_json_trailing_commas
  • _intentar_reparar_json (orquestador con 4 estrategias)
"""
import json

import pytest

from modules.json_prompt import (
    CAMPOS_AVANZADOS,
    CAMPOS_NUCLEO,
    CAMPOS_TECNICOS,
    _intentar_reparar_json,
    _limpiar_json_de_newlines,
    _limpiar_json_trailing_commas,
)


class TestLimpiarJsonDeNewlines:

    def test_texto_sin_strings_no_cambia(self):
        # Texto fuera de comillas: newlines/tabs preservados
        original = "{\n  \"a\": 1\n}"
        assert _limpiar_json_de_newlines(original) == original

    def test_newline_dentro_de_string_se_convierte_en_espacio(self):
        original = '{"desc": "linea1\nlinea2"}'
        esperado = '{"desc": "linea1 linea2"}'
        assert _limpiar_json_de_newlines(original) == esperado

    def test_tab_dentro_de_string_se_convierte_en_espacio(self):
        original = '{"desc": "col1\tcol2"}'
        esperado = '{"desc": "col1 col2"}'
        assert _limpiar_json_de_newlines(original) == esperado

    def test_carriage_return_dentro_de_string_se_convierte_en_espacio(self):
        original = '{"desc": "linea1\rlinea2"}'
        esperado = '{"desc": "linea1 linea2"}'
        assert _limpiar_json_de_newlines(original) == esperado

    def test_indentacion_externa_se_preserva(self):
        # Solo los newlines DENTRO de strings deben tocarse
        original = '{\n  "a": "valor",\n  "b": "otro"\n}'
        # No hay newlines dentro de strings, así que el resultado debe ser idéntico
        assert _limpiar_json_de_newlines(original) == original

    def test_comilla_escapada_no_rompe_state_machine(self):
        # La comilla escapada \" no debe cerrar el string
        # Entonces el newline después de \" sigue estando DENTRO del string
        original = '{"a": "dice \\"hola\\"\nfin"}'
        esperado = '{"a": "dice \\"hola\\" fin"}'
        assert _limpiar_json_de_newlines(original) == esperado

    def test_string_vacio_no_falla(self):
        assert _limpiar_json_de_newlines("") == ""

    def test_multiple_newlines_consecutivos_dentro_string(self):
        original = '{"x": "a\n\n\nb"}'
        esperado = '{"x": "a   b"}'
        assert _limpiar_json_de_newlines(original) == esperado

    def test_resultado_es_parseable_tras_limpiar(self):
        # Caso real: copiar de una web con newlines literales
        crudo = '{"prompt": "una chica\nen un bosque\nmagico"}'
        limpio = _limpiar_json_de_newlines(crudo)
        data = json.loads(limpio)
        assert data["prompt"] == "una chica en un bosque magico"


class TestLimpiarJsonTrailingCommas:

    def test_sin_trailing_commas_no_cambia(self):
        original = '{"a": 1, "b": 2}'
        assert _limpiar_json_trailing_commas(original) == original

    def test_trailing_coma_en_array(self):
        original = '[1, 2, 3,]'
        assert _limpiar_json_trailing_commas(original) == '[1, 2, 3]'

    def test_trailing_coma_en_objeto(self):
        original = '{"a": 1, "b": 2,}'
        assert _limpiar_json_trailing_commas(original) == '{"a": 1, "b": 2}'

    def test_coma_seguida_de_espacios_y_cierre(self):
        # Trailing coma con whitespace antes del ]
        original = '[1, 2, 3,  \n  ]'
        # El cleaner salta hasta el ] y produce un cierre limpio
        resultado = _limpiar_json_trailing_commas(original)
        assert resultado == '[1, 2, 3]'

    def test_coma_dentro_de_string_se_preserva(self):
        original = '{"texto": "hola, mundo,"}'
        # La coma final está dentro del string, no es trailing
        assert _limpiar_json_trailing_commas(original) == original

    def test_objeto_anidado_con_trailing(self):
        original = '{"a": {"b": 1,}, "c": [1, 2,]}'
        esperado = '{"a": {"b": 1}, "c": [1, 2]}'
        assert _limpiar_json_trailing_commas(original) == esperado

    def test_string_vacio_no_falla(self):
        assert _limpiar_json_trailing_commas("") == ""

    def test_resultado_es_parseable_tras_limpiar(self):
        crudo = '{"items": [1, 2, 3,], "total": 3,}'
        limpio = _limpiar_json_trailing_commas(crudo)
        data = json.loads(limpio)
        assert data == {"items": [1, 2, 3], "total": 3}


class TestIntentarRepararJson:

    def test_json_valido_no_aplica_estrategias(self):
        texto = '{"a": 1, "b": "hola"}'
        data, estrategias = _intentar_reparar_json(texto)
        assert data == {"a": 1, "b": "hola"}
        assert estrategias == []

    def test_json_con_newlines_aplica_estrategia_newlines(self):
        texto = '{"prompt": "linea1\nlinea2"}'
        data, estrategias = _intentar_reparar_json(texto)
        assert data == {"prompt": "linea1 linea2"}
        assert "newlines en strings → espacios" in estrategias
        assert len(estrategias) == 1

    def test_json_con_trailing_aplica_estrategia_trailing(self):
        texto = '{"a": 1, "b": 2,}'
        data, estrategias = _intentar_reparar_json(texto)
        assert data == {"a": 1, "b": 2}
        assert "comas finales eliminadas" in estrategias
        assert len(estrategias) == 1

    def test_json_con_ambos_problemas_aplica_estrategia_combinada(self):
        texto = '{"prompt": "una\nfrase", "tags": [1, 2,],}'
        data, estrategias = _intentar_reparar_json(texto)
        assert data == {"prompt": "una frase", "tags": [1, 2]}
        # La estrategia combinada añade 2 entradas
        assert "newlines en strings → espacios" in estrategias
        assert "comas finales eliminadas" in estrategias

    def test_json_irreparable_devuelve_none_con_error(self):
        # Sintaxis fundamentalmente rota — no es solo newlines/commas
        texto = '{"a": esto_no_es_valido}'
        data, error = _intentar_reparar_json(texto)
        assert data is None
        assert isinstance(error, str)
        assert len(error) > 0

    def test_json_vacio_devuelve_none(self):
        data, error = _intentar_reparar_json("")
        assert data is None

    def test_solo_trailing_no_intenta_estrategia_newlines_innecesaria(self):
        texto = '[1, 2, 3,]'
        data, estrategias = _intentar_reparar_json(texto)
        assert data == [1, 2, 3]
        # Debería haber aplicado SOLO trailing commas, no la combinada
        assert estrategias == ["comas finales eliminadas"]

    def test_array_top_level_funciona(self):
        texto = '[{"a": 1}, {"b": 2}]'
        data, estrategias = _intentar_reparar_json(texto)
        assert data == [{"a": 1}, {"b": 2}]
        assert estrategias == []


class TestCamposCanonicos:
    """Sanity check sobre las constantes de campos canónicos exportadas."""

    def test_campos_nucleo_contiene_prompt(self):
        assert "prompt" in CAMPOS_NUCLEO
        assert "negative_prompt" in CAMPOS_NUCLEO
        assert "positive_prompt" in CAMPOS_NUCLEO

    def test_campos_tecnicos_contiene_aspect_ratio(self):
        assert "aspect_ratio" in CAMPOS_TECNICOS
        assert "duration" in CAMPOS_TECNICOS

    def test_campos_avanzados_contiene_camera(self):
        assert "camera" in CAMPOS_AVANZADOS
        assert "audio" in CAMPOS_AVANZADOS
        assert "lighting" in CAMPOS_AVANZADOS

    def test_conjuntos_disjuntos(self):
        # Un campo no debería estar en dos categorías a la vez
        assert CAMPOS_NUCLEO.isdisjoint(CAMPOS_TECNICOS)
        assert CAMPOS_NUCLEO.isdisjoint(CAMPOS_AVANZADOS)
        assert CAMPOS_TECNICOS.isdisjoint(CAMPOS_AVANZADOS)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
