"""Dos proveedores de nube cuya lista NUNCA se auto-depuraba.

Auditados los catálogos en vivo de los 8 proveedores con key el 08-sep-2026,
antes de lanzar. Seis estaban limpios; los otros dos no contestaban, y por
motivos distintos:

  · GROQ devolvía 403 "error code: 1010" — el código de bloqueo por cliente de
    Cloudflare, no un problema de key. Rechaza el User-Agent por defecto de
    urllib ("Python-urllib/3.10"). Con CUALQUIER User-Agent: 200 y 14 modelos.
    La generación no se enteraba nunca porque va por el SDK de OpenAI, que
    manda el suyo; el que se quedaba mudo era solo el catálogo.

  · GEMINI contestaba perfectamente (54 modelos, 40 con generateContent) pero
    nadie se lo preguntaba: el filtro en vivo solo admitía "openai_compatible"
    y "anthropic", así que la lista de Google era la única de nube sin
    auto-depurar — y ya se había quedado dos generaciones por detrás una vez.
"""
import inspect

import api_clients as A


class TestElCatalogoSeIdentifica:

    def test_hay_un_user_agent_definido(self):
        assert A.UA_CATALOGO and "urllib" not in A.UA_CATALOGO.lower()

    def test_el_endpoint_openai_compatible_lo_manda(self):
        fuente = inspect.getsource(A.OpenAICompatibleProvider.listar_modelos)
        assert "UA_CATALOGO" in fuente, (
            "sin User-Agent, Groq responde 403 (Cloudflare 1010) y su lista "
            "curada no se depura nunca")

    def test_el_de_anthropic_tambien(self):
        fuente = inspect.getsource(A.ClaudeProvider.listar_modelos)
        assert "UA_CATALOGO" in fuente

    def test_el_de_google_tambien(self):
        fuente = inspect.getsource(A.GeminiProvider.listar_modelos)
        assert "UA_CATALOGO" in fuente


class TestGoogleEntraEnElFiltroEnVivo:

    def test_gemini_tiene_listar_modelos(self):
        assert callable(getattr(A.GeminiProvider, "listar_modelos", None))

    def test_el_filtro_admite_el_tipo_google(self):
        fuente = inspect.getsource(A.modelos_disponibles)
        assert '"google"' in fuente, (
            "el tipo de Gemini es 'google': si no entra en el filtro, su "
            "lista no se auto-depura")

    def test_solo_los_que_generan_texto(self):
        fuente = inspect.getsource(A.GeminiProvider.listar_modelos)
        assert "generateContent" in fuente, (
            "de los 54 que devuelve Google, 14 son embeddings/TTS/imagen y no "
            "pintan nada en el desplegable de cerebros")

    def test_quita_el_prefijo_models(self, monkeypatch):
        # Google devuelve "models/gemini-2.5-flash"; el catálogo curado guarda
        # el id desnudo. Sin recortar, TODOS parecerían muertos.
        prov = A.GeminiProvider("key-de-prueba")
        respuesta = {"models": [
            {"name": "models/gemini-2.5-flash",
             "supportedGenerationMethods": ["generateContent"]},
            {"name": "models/text-embedding-004",
             "supportedGenerationMethods": ["embedContent"]},
        ]}
        _fingir_respuesta_json(monkeypatch, respuesta)
        assert prov.listar_modelos() == ["gemini-2.5-flash"]

    def test_si_google_no_responde_devuelve_lista_vacia(self, monkeypatch):
        # Nunca puede propagar: esto alimenta un desplegable.
        def revienta(*a, **k):
            raise OSError("sin red")
        monkeypatch.setattr(A.urllib.request, "urlopen", revienta)
        assert A.GeminiProvider("key-de-prueba").listar_modelos() == []

    def test_sin_key_no_llama(self, monkeypatch):
        def revienta(*a, **k):
            raise AssertionError("no debía llamar sin key")
        monkeypatch.setattr(A.urllib.request, "urlopen", revienta)
        assert A.GeminiProvider("").listar_modelos() == []


def _fingir_respuesta_json(monkeypatch, payload):
    import json

    class _Resp:
        def read(self):
            return json.dumps(payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(A.urllib.request, "urlopen", lambda *a, **k: _Resp())
