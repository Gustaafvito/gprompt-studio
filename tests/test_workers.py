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

    def test_corta_a_tres_si_hay_mas(self):
        # Solo soporta 1-3, los siguientes no matchean ^[1-3]
        texto = "1. una\n2. dos\n3. tres\n4. cuatro"
        result = parsear_ideas(texto)
        assert len(result) == 3
        assert result == ["una", "dos", "tres"]

    def test_formato_prompt_n_dos_puntos(self):
        # Modo alternativo: "PROMPT 1: ...", "PROMPT 2: ..."
        texto = "PROMPT 1: idea uno\nPROMPT 2: idea dos\nPROMPT 3: idea tres"
        result = parsear_ideas(texto)
        assert result == ["idea uno", "idea dos", "idea tres"]

    def test_caracteres_unicode_y_emojis(self):
        texto = "1. una chica con 🌸 flores\n2. mañana en el café\n3. niño jugando"
        assert parsear_ideas(texto) == [
            "una chica con 🌸 flores",
            "mañana en el café",
            "niño jugando",
        ]

    def test_espacios_y_tabs_alrededor(self):
        texto = "  1.   idea con espacios  \n  2. otra  "
        result = parsear_ideas(texto)
        assert result == ["idea con espacios", "otra"]


class TestDeepSeekWorker:
    """Tests para la clase DeepSeekWorker (parte API pública sin red)."""

    def test_reiniciar_pone_system_prompt(self):
        from workers import DeepSeekWorker

        w = DeepSeekWorker(clients=None)
        w.reiniciar("Eres un asistente.")
        assert w.historial == [{"role": "system", "content": "Eres un asistente."}]

    def test_historial_inicial_vacio(self):
        from workers import DeepSeekWorker

        w = DeepSeekWorker(clients=None)
        assert w.historial == []

    def test_reiniciar_borra_historial_previo(self):
        from workers import DeepSeekWorker

        w = DeepSeekWorker(clients=None)
        w.historial = [
            {"role": "system", "content": "viejo"},
            {"role": "user", "content": "hola"},
        ]
        w.reiniciar("nuevo system")
        assert w.historial == [{"role": "system", "content": "nuevo system"}]

    def _worker_con_respuesta(self, respuesta):
        """DeepSeekWorker cuyo provider devuelve `respuesta` en completar()."""
        from types import SimpleNamespace

        from workers import DeepSeekWorker
        prov = SimpleNamespace(
            disponible=lambda: True,
            completar=lambda *a, **k: respuesta,
        )
        clients = SimpleNamespace(get_active_provider=lambda: prov)
        return DeepSeekWorker(clients=clients)

    def test_traducir_respuesta_vacia_devuelve_original(self):
        # Bug DeepSeek V4 Pro: el razonamiento se comía los tokens y la
        # traducción volvía vacía → la idea se perdía. Debe caer al original.
        w = self._worker_con_respuesta("")
        assert w.traducir("un gato en la playa") == "un gato en la playa"
        w2 = self._worker_con_respuesta("   \n  ")
        assert w2.traducir("un gato") == "un gato"

    def test_traducir_respuesta_valida_se_usa(self):
        w = self._worker_con_respuesta("a cat on the beach")
        assert w.traducir("un gato en la playa") == "a cat on the beach"

    def test_traducir_a_espanol_vacia_devuelve_original(self):
        w = self._worker_con_respuesta("")
        assert w.traducir_a_espanol("a cat") == "a cat"


class TestDetectarIdiomaEs:
    def test_espanol_claro(self):
        assert detectar_idioma_es("una chica con pelo oscuro") is True

    def test_espanol_minimo(self):
        assert detectar_idioma_es("chica en estilo anime") is True

    def test_ingles(self):
        assert detectar_idioma_es("a girl with dark hair in anime style") is False

    def test_ingles_con_pocas_palabras_es(self):
        assert detectar_idioma_es("anime style") is False
