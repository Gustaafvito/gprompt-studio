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

    def test_un_tipo_que_no_sabemos_consultar_no_se_toca(self, monkeypatch):
        # Este test probaba con "gemini" hasta el 08-sep-2026, cuando el tipo
        # "google" pasó a consultarse (su lista era la única de nube que no se
        # auto-depuraba nunca). Ya no queda ningún proveedor real sin
        # consultar, así que se usa uno sintético: la garantía es que un tipo
        # cuyo catálogo no sabemos leer conserva su lista curada intacta, en
        # vez de quedarse vacío o recibir lo que devuelva otro endpoint.
        monkeypatch.setitem(api_clients.LLM_PROVIDERS, "inventado", {
            "name": "Inventado", "tipo": "protocolo_desconocido",
            "modelos": ["mi-modelo-a", "mi-modelo-b"],
        })
        _con_catalogo(monkeypatch, ["lo-que-sea"])
        got = api_clients.modelos_disponibles("inventado", "key")
        assert got == ["mi-modelo-a", "mi-modelo-b"]

    def test_gemini_SI_se_consulta(self, monkeypatch):
        # El complemento del anterior: el tipo "google" tiene que entrar.
        api_clients._CACHE_CATALOGO.clear()
        _con_catalogo(monkeypatch, ["gemini-2.5-flash"])
        got = api_clients.modelos_disponibles("gemini", "key")
        assert got == ["gemini-2.5-flash"], (
            "la lista de Google ya se depura contra su catálogo en vivo")


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


class TestAliasConFecha:
    """Anthropic publica los modelos viejos CON fecha y acepta el alias sin ella.

    Verificado el 06-sep-2026 contra la API real: `GET /v1/models` devuelve
    `claude-haiku-4-5-20251001`, pero `claude-haiku-4-5` —que es lo que guarda
    el catálogo curado, porque hay un candado que prohíbe las fechas en los
    IDs— responde en 0,6s. Sin normalizar, el filtro daba por muerto un modelo
    que funciona y lo borraba del desplegable.
    """

    def test_el_alias_sobrevive_aunque_el_catalogo_lleve_fecha(self, monkeypatch):
        _con_catalogo(monkeypatch, ["claude-sonnet-5", "claude-haiku-4-5-20251001"])
        got = api_clients.modelos_disponibles("claude", "key")
        assert "claude-haiku-4-5" in got, \
            "el alias sin fecha funciona; no se puede ocultar"

    def test_sin_fecha_solo_quita_ocho_digitos_al_final(self):
        assert api_clients._sin_fecha("claude-haiku-4-5-20251001") == "claude-haiku-4-5"
        assert api_clients._sin_fecha("claude-sonnet-5") == "claude-sonnet-5"
        assert api_clients._sin_fecha("gpt-5.6") == "gpt-5.6"
        # No debe morder un número que no sea fecha ni uno en medio del ID.
        assert api_clients._sin_fecha("llama-v3p3-70b") == "llama-v3p3-70b"
        assert api_clients._sin_fecha("modelo-20251001-turbo") == "modelo-20251001-turbo"

    def test_anthropic_entra_en_el_filtro_pese_a_no_ser_openai_compatible(self, monkeypatch):
        _con_catalogo(monkeypatch, ["claude-sonnet-5"])
        got = api_clients.modelos_disponibles("claude", "key")
        assert got == ["claude-sonnet-5"], \
            "Anthropic tiene su propio listar_modelos(); debe depurarse igual"

    def test_claude_provider_sabe_listarse(self):
        assert hasattr(api_clients.ClaudeProvider, "listar_modelos")


class TestFireworksRehecha:
    """Los 4 modelos que tenía Fireworks estaban muertos, 4 de 4 (06-sep-2026).

    Al no sobrevivir ninguno saltaba el último recurso —volcar el catálogo del
    proveedor— y el desplegable pasaba a tener 25 entradas, dos de ellas de
    embeddings. Los ocho actuales se probaron uno a uno contra la API.
    """

    MUERTOS = ("llama-v3p3-70b-instruct", "qwen2p5-72b-instruct",
               "deepseek-r1", "mixtral-8x22b-instruct")
    # Listados por /v1/models pero SIN serverless: dan 404 al llamarlos.
    NO_SERVERLESS = ("models/deepseek-v4-pro", "models/minimax-m2p7")

    def test_no_vuelven_los_ids_muertos(self):
        modelos = api_clients.LLM_PROVIDERS["fireworks"]["modelos"]
        for m in self.MUERTOS:
            assert not any(m in x for x in modelos), \
                f"{m} ya no lo sirve Fireworks (comprobado con key real)"

    def test_no_se_cuela_uno_que_exige_gpu_dedicada(self):
        modelos = api_clients.LLM_PROVIDERS["fireworks"]["modelos"]
        for m in self.NO_SERVERLESS:
            assert not any(x.endswith(m) for x in modelos), \
                f"{m} no es serverless: devuelve 404"

    def test_el_default_esta_en_la_lista(self):
        info = api_clients.LLM_PROVIDERS["fireworks"]
        assert info["model_default"] in info["modelos"]

    def test_ningun_modelo_de_embeddings_en_la_lista_curada(self):
        for m in api_clients.LLM_PROVIDERS["fireworks"]["modelos"]:
            assert not any(t in m.lower() for t in ("embedding", "reranker")), \
                f"{m} no genera texto; como cerebro solo sirve para fallar"


class TestElBotonProbarKeysNoUsaModelosAFuego:
    """El wizard probaba la key llamando a un modelo escrito a mano.

    El 07-sep-2026 TRES de los cinco apuntaban a modelos muertos: groq a
    llama-3.3-70b-versatile (404 con key válida), openrouter a un ":free"
    retirado y gemini a 2.0-flash-exp. Resultado: el botón declaraba inválida
    una key que funcionaba. Ahora el modelo sale de LLM_PROVIDERS.
    """
    import pathlib
    FUENTE = pathlib.Path(__file__).resolve().parent.parent / "app.py"

    def _bloque(self):
        txt = self.FUENTE.read_text(encoding="utf-8")
        i = txt.find("TEST_TIMEOUT = 15.0")
        assert i != -1, "no encuentro el test de keys del wizard"
        return txt[i:i + 3000]

    def test_el_modelo_sale_del_catalogo(self):
        assert "modelo_test" in self._bloque()

    def test_no_queda_ningun_id_escrito_a_mano(self):
        # El comentario que documenta el bug CITA los IDs muertos; aqui
        # solo interesa que no sigan siendo el argumento model= real.
        sin_comentarios = [x for x in self._bloque().splitlines()
                           if not x.strip().startswith('#')]
        bloque = chr(10).join(sin_comentarios)
        for muerto in ("llama-3.3-70b-versatile", "gemini-2.0-flash-exp",
                       "meta-llama/llama-3.1-8b-instruct:free"):
            assert muerto not in bloque, f"{muerto} ya no responde"

    def test_todos_los_defaults_del_wizard_estan_en_su_lista(self):
        for pid in ("gemini", "deepseek", "groq", "github_models", "openrouter"):
            info = api_clients.LLM_PROVIDERS[pid]
            assert info["model_default"] in info["modelos"], \
                f"{pid}: el default no está en su propia lista"
