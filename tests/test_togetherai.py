"""Together AI: su /v1/models devuelve una lista pelada, y lista de más.

Verificado el 08-sep-2026 con key real. Together exige un depósito de 5 $
para salir del modo solo-lectura; no tiene tier gratuito.

DOS FALLOS ENCADENADOS.

1. `listar_modelos()` hacía `data.get("data", [])`, la forma de OpenAI. Pero
   Together devuelve una LISTA pelada en el nivel superior, así que el
   resultado era SIEMPRE `[]` y su lista curada no se depuraba jamás. Así
   sobrevivieron ahí cuatro modelos que ya no se pueden llamar.

2. Y aun arreglando eso, aparecer en el catálogo NO basta. De los cinco
   curados, `deepseek-ai/DeepSeek-R1` ya no existe, pero
   `Qwen/Qwen2.5-72B-Instruct-Turbo`, `mistralai/Mistral-7B-Instruct-v0.3` y
   `google/gemma-2-27b-it` SIGUEN LISTADOS y responden 400:

       "Unable to access non-serverless model ... Please visit ... to create
        and start a new dedicated endpoint"

   Hay que levantar hardware dedicado para usarlos. Es la misma trampa que
   ya tuvo Fireworks, y por eso esta lista se prueba llamando, no listando.

De 275 entradas, 172 son de tipo chat y solo 74 tienen precio (serverless).
Medidos en segunda pasada, porque la primera llamada a un modelo frío puede
tardar 25 s: gpt-oss-20b y 120b 1,3 s, Llama-3.3-70B-Turbo 1,1 s,
DeepSeek-V4-Flash 1,5 s, GLM-5.3-Flash 2,0 s.
"""
import json

import api_clients as A


def _con_respuesta(monkeypatch, payload):
    class _Resp:
        def read(self):
            return json.dumps(payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(A.urllib.request, "urlopen", lambda *a, **k: _Resp())


class TestElCatalogoEnListaPelada:

    def _prov(self):
        return A.OpenAICompatibleProvider("key", base_url="https://api.together.xyz/v1")

    def test_una_lista_pelada_se_entiende(self, monkeypatch):
        # La forma de Together: array en el nivel superior.
        _con_respuesta(monkeypatch, [{"id": "openai/gpt-oss-20b"},
                                     {"id": "zai-org/GLM-5.3-Flash"}])
        assert self._prov().listar_modelos() == ["openai/gpt-oss-20b",
                                                 "zai-org/GLM-5.3-Flash"]

    def test_la_forma_de_openai_sigue_funcionando(self, monkeypatch):
        _con_respuesta(monkeypatch, {"data": [{"id": "gpt-4o"}]})
        assert self._prov().listar_modelos() == ["gpt-4o"]

    def test_una_respuesta_rara_no_revienta(self, monkeypatch):
        _con_respuesta(monkeypatch, {"algo": "inesperado"})
        assert self._prov().listar_modelos() == []


class TestLaListaSePruebaLlamando:

    MUERTOS = ("deepseek-ai/DeepSeek-R1",                 # ya no existe
               "Qwen/Qwen2.5-72B-Instruct-Turbo",         # non-serverless
               "mistralai/Mistral-7B-Instruct-v0.3",      # non-serverless
               "google/gemma-2-27b-it")                   # non-serverless

    def test_no_vuelven_los_que_no_se_pueden_llamar(self):
        for m in self.MUERTOS:
            assert m not in A.LLM_PROVIDERS["togetherai"]["modelos"], (
                f"{m} aparece en /v1/models pero da 400 al llamarlo")

    def test_el_unico_superviviente_sigue(self):
        assert ("meta-llama/Llama-3.3-70B-Instruct-Turbo"
                in A.LLM_PROVIDERS["togetherai"]["modelos"])

    def test_el_default_esta_en_la_lista(self):
        info = A.LLM_PROVIDERS["togetherai"]
        assert info["model_default"] in info["modelos"]

    def test_el_default_es_el_mas_barato(self):
        entrada = {m: A.PRECIOS_USD_1M_MODELO[m][0]
                   for m in A.LLM_PROVIDERS["togetherai"]["modelos"]}
        d = A.LLM_PROVIDERS["togetherai"]["model_default"]
        assert entrada[d] == min(entrada.values())

    def test_todos_tienen_precio(self):
        sin = [m for m in A.LLM_PROVIDERS["togetherai"]["modelos"]
               if not A.PRECIOS_USD_1M_MODELO.get(m)]
        assert not sin, f"sin precio: {sin}"

    def test_el_respaldo_del_proveedor_es_el_del_default(self):
        d = A.LLM_PROVIDERS["togetherai"]["model_default"]
        assert A.PRECIOS_USD_1M["togetherai"] == A.PRECIOS_USD_1M_MODELO[d]
