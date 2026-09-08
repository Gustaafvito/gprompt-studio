"""Perplexity: dos productos en rutas distintas, y una tarifa por petición.

Verificado el 08-sep-2026 con key real. (Al darse de alta regalan 10 $ de
crédito de API, así que no hizo falta pagar.)

LA TRAMPA. Perplexity sirve dos cosas por rutas diferentes:

    /chat/completions   la API Sonar, que es la que usa la app. Solo acepta
                        nombres pelados: sonar, sonar-pro, sonar-reasoning-pro
    /v1/models          un catálogo-pasarela de 49 modelos AJENOS
                        (anthropic/claude-opus-5, openai/gpt-6-astra,
                        xai/grok-4.6, google/gemini-3.8-flash) con precios

El endpoint de chat RECHAZA los ids de la pasarela con "Invalid model". Como
`listar_modelos()` pide `base_url + "/models"` y aquí eso da 404, devuelve []
y la lista curada queda intacta — que es justo lo correcto. Apuntar ese 404
al `/v1` para "arreglarlo" daría por MUERTOS a todos los Sonar, porque
ninguno aparece en la lista de la pasarela. De ahí este candado.

LA TARIFA. Además de los tokens, cobra un fijo POR PETICIÓN, medido en
`usage.cost` de las respuestas reales: 0,0050 $ en sonar y 0,0060 $ en los
dos "pro", se gasten los tokens que se gasten. Para esta app, que hace
muchas llamadas cortas, ese fijo es el coste DOMINANTE: mil prompts son unos
6 $ de tarifas frente a céntimos de tokens. Es el único de los once
proveedores que cobra así, porque cada respuesta lleva búsqueda web.
"""
import inspect

import api_clients as A


class TestLaListaDeSonarEstaViva:

    def test_sonar_reasoning_fuera(self):
        # Responde 400 "The 'sonar-reasoning' model has been deprecated".
        assert "sonar-reasoning" not in A.LLM_PROVIDERS["perplexity"]["modelos"]

    def test_los_tres_que_responden(self):
        assert A.LLM_PROVIDERS["perplexity"]["modelos"] == [
            "sonar-pro", "sonar", "sonar-reasoning-pro"]

    def test_el_default_esta_en_la_lista(self):
        info = A.LLM_PROVIDERS["perplexity"]
        assert info["model_default"] in info["modelos"]

    def test_sin_deep_research(self):
        # Tarda 47s y devuelve un informe con secciones en vez de una
        # respuesta: es un agente de investigación, no un cerebro.
        assert "sonar-deep-research" not in A.LLM_PROVIDERS["perplexity"]["modelos"]

    def test_todos_tienen_precio(self):
        for m in A.LLM_PROVIDERS["perplexity"]["modelos"]:
            assert A.PRECIOS_USD_1M_MODELO.get(m), f"{m} sin precio"


class TestNoSeMezclanLasDosRutas:

    def test_el_base_url_es_el_del_chat(self):
        # Sin /v1: el endpoint de chat vive en la raíz. Añadírselo rompe la
        # generación entera (404).
        assert A.LLM_PROVIDERS["perplexity"]["base_url"] == "https://api.perplexity.ai"

    def test_ningun_modelo_lleva_prefijo_de_pasarela(self):
        # 'perplexity/sonar', 'openai/gpt-6-astra'... los rechaza el chat.
        for m in A.LLM_PROVIDERS["perplexity"]["modelos"]:
            assert "/" not in m, (
                f"{m} tiene forma de id de la pasarela /v1/models, que el "
                f"endpoint de chat rechaza con 'Invalid model'")

    def test_la_trampa_queda_avisada_en_el_codigo(self):
        fuente = inspect.getsource(A)
        i = fuente.find('"perplexity": {')
        bloque = fuente[i:i + 2600]
        assert "/v1/models" in bloque and "Invalid model" in bloque, (
            "sin el aviso, el 404 de listar_modelos() parece un bug y "
            "alguien lo 'arregla' apuntándolo al /v1, matando los Sonar")


class TestLaTarifaPorPeticionEstaDocumentada:

    def test_el_aviso_esta_junto_a_los_precios(self):
        fuente = inspect.getsource(A)
        i = fuente.find('    "sonar-pro":     ')
        assert i != -1, "no encuentro la fila de precios de sonar-pro"
        # El aviso va en el comentario que precede al bloque de Perplexity
        # dentro de la tabla de precios.
        bloque = fuente[max(0, i - 1500):i]
        assert "TARIFA FIJA POR" in bloque, (
            "la tabla solo modela precio por token; sin el aviso, el "
            "contador infravalora el gasto de Perplexity de largo")
