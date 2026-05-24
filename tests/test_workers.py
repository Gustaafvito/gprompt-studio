"""Tests para helpers y funciones de workers.py."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from workers import contar_tokens_aprox, detectar_idioma_es, limpiar_marcadores, parsear_ideas


class TestContarTokens:
    def test_texto_vacio(self):
        assert contar_tokens_aprox("") == 0
        assert contar_tokens_aprox(None) == 0

    def test_texto_corto(self):
        assert contar_tokens_aprox("hola") == 1

    def test_estimacion(self):
        texto = "a" * 400
        assert contar_tokens_aprox(texto) == 100

    def test_minimo_uno(self):
        assert contar_tokens_aprox("x") == 1


class TestLimpiarMarcadores:
    def test_sin_marcadores(self):
        assert limpiar_marcadores("hola mundo") == "hola mundo"

    def test_doble_asterisco(self):
        assert limpiar_marcadores("**hola**") == "hola"

    def test_asterisco_simple(self):
        assert limpiar_marcadores("*hola*") == "*hola*"

    def test_doble_guion(self):
        assert limpiar_marcadores("__hola__") == "hola"

    def test_multiple(self):
        assert limpiar_marcadores("**bold** and __italic__") == "bold and italic"


class TestParsearIdeas:
    def test_tres_ideas(self):
        texto = "1. idea uno\n2. idea dos\n3. idea tres"
        assert parsear_ideas(texto) == ["idea uno", "idea dos", "idea tres"]

    def test_formato_paren(self):
        texto = "1) idea uno\n2) idea dos\n3) idea tres"
        assert parsear_ideas(texto) == ["idea uno", "idea dos", "idea tres"]

    def test_menos_de_tres(self):
        texto = "1. solo una idea"
        assert parsear_ideas(texto) == ["solo una idea"]

    def test_ignora_lineas_no_numeradas(self):
        texto = "intro\n1. idea\nextra\n2. otra"
        assert parsear_ideas(texto) == ["idea", "otra"]

    def test_vacio(self):
        assert parsear_ideas("") == []


class TestDetectarIdiomaEs:
    def test_espanol_claro(self):
        assert detectar_idioma_es("una chica con pelo oscuro") is True

    def test_espanol_minimo(self):
        assert detectar_idioma_es("chica en estilo anime") is True

    def test_ingles(self):
        assert detectar_idioma_es("a girl with dark hair in anime style") is False

    def test_ingles_con_pocas_palabras_es(self):
        assert detectar_idioma_es("anime style") is False
