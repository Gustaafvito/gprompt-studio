"""El desplegable de modelos se depura contra el catálogo real del proveedor.

Las listas escritas a mano se pudren. El 06-sep-2026, los SEIS modelos ":free"
de OpenRouter devolvían 404 — y era el SEGUNDO rescate de esa misma lista, que
ya había perdido antes a `deepseek/deepseek-chat`. Gemini, en paralelo, iba dos
generaciones por detrás.

Todos los proveedores OpenAI-compatible publican `GET /v1/models`, así que
groq, mistral, together, fireworks, openrouter, xai, deepseek y openai heredan
la comprobación de golpe.

Se FILTRA la lista curada en vez de sustituirla: OpenRouter publica 430
modelos y eso no es un desplegable, es un listín.
"""
import api_clients


class _ProvFalso:
    def __init__(self, vivos):
        self._vivos = vivos
    def listar_modelos(self):
        return self._vivos


def _con_catalogo(monkeypatch, vivos):
    api_clients._CACHE_CATALOGO.clear()
    monkeypatch.setattr(api_clients, "get_provider",
                        lambda pid, key, model=None: _ProvFalso(vivos))


class TestDepuraLaListaCurada:

    def test_oculta_los_que_el_proveedor_ya_no_sirve(self, monkeypatch):
        vivos = ["openai/gpt-4o", "google/gemini-2.5-pro"]
        _con_catalogo(monkeypatch, vivos)
        got = api_clients.modelos_disponibles("openrouter", "key")
        assert "openai/gpt-4o" in got
        assert all(m in vivos for m in got), f"se cuela un modelo muerto: {got}"

    def test_no_vuelca_el_catalogo_entero_si_hay_supervivientes(self, monkeypatch):
        """OpenRouter publica 430 modelos; el desplegable debe seguir curado."""
        vivos = ["openai/gpt-4o"] + [f"relleno/modelo-{i}" for i in range(400)]
        _con_catalogo(monkeypatch, vivos)
        got = api_clients.modelos_disponibles("openrouter", "key")
        assert len(got) < 10, f"el desplegable se convirtió en un listín: {len(got)}"

    def test_si_no_sobrevive_ninguno_cae_al_catalogo_del_proveedor(self, monkeypatch):
        """Peor un listín largo que un desplegable vacío."""
        _con_catalogo(monkeypatch, ["algo/nuevo-1", "algo/nuevo-2"])
        got = api_clients.modelos_disponibles("openrouter", "key")
        assert got, "sin esto el usuario se queda sin modelos que elegir"
        assert "algo/nuevo-1" in got


class TestNuncaEmpeoraLoQueYaHabia:

    def test_sin_key_devuelve_la_lista_estatica(self, monkeypatch):
        api_clients._CACHE_CATALOGO.clear()
        got = api_clients.modelos_disponibles("groq", None)
        assert got == api_clients.LLM_PROVIDERS["groq"]["modelos"]

    def test_si_el_proveedor_no_responde_devuelve_la_estatica(self, monkeypatch):
        _con_catalogo(monkeypatch, [])          # catálogo vacío = no se sabe
        got = api_clients.modelos_disponibles("openrouter", "key")
        assert got == api_clients.LLM_PROVIDERS["openrouter"]["modelos"]

    def test_un_proveedor_no_openai_compatible_no_se_toca(self, monkeypatch):
        _con_catalogo(monkeypatch, ["lo-que-sea"])
        got = api_clients.modelos_disponibles("gemini", "key")
        assert got == api_clients.LLM_PROVIDERS["gemini"]["modelos"]


class TestCache:

    def test_no_pregunta_dos_veces_seguidas(self, monkeypatch):
        api_clients._CACHE_CATALOGO.clear()
        llamadas = []
        def _fake(pid, key, model=None):
            llamadas.append(pid)
            return _ProvFalso(["openai/gpt-4o"])
        monkeypatch.setattr(api_clients, "get_provider", _fake)
        api_clients.modelos_disponibles("openrouter", "key")
        api_clients.modelos_disponibles("openrouter", "key")
        assert len(llamadas) == 1, "el desplegable se abre muchas veces; hay caché"


class TestElProveedorSabePreguntar:

    def test_openai_compatible_tiene_listar_modelos(self):
        assert hasattr(api_clients.OpenAICompatibleProvider, "listar_modelos")

    def test_timeout_corto_para_no_bloquear_la_ui(self):
        assert api_clients.TIMEOUT_CATALOGO_S <= 10, \
            "esto solo llena un desplegable, no puede congelar la interfaz"
