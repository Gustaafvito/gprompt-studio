"""OpenAI retiró `max_tokens` y `temperature` en sus modelos modernos.

08-sep-2026, primera verificación con key real de OpenAI (la familia 5.x se
había añadido el 06-sep desde la documentación, a ciegas). Dos fallos:

1. `gpt-5.6` A SECAS NO EXISTE. La familia es -sol, -terra y -luna. Y era el
   `model_default`, así que "Probar keys" declaraba inválida una key buena —
   el mismo síntoma que ya tuvieron Groq, OpenRouter y x.ai.

2. Toda la familia GPT-5.x y GPT-6 responde 400 a los dos parámetros de
   siempre:

       "Unsupported parameter: 'max_tokens' is not supported with this
        model. Use 'max_completion_tokens' instead."
       "Unsupported value: 'temperature' does not support 0.75..."

   Elegir cualquiera de ellos reventaba con un 400 en la cara. De la lista
   curada solo gpt-4o y gpt-4o-mini seguían aceptando los clásicos.

Las manías se APRENDEN del propio error y se recuerdan por modelo, no por
proveedor, porque conviven en el mismo: `gpt-5.4-mini` exige
max_completion_tokens pero SÍ acepta temperature, así que una regla del tipo
"los modernos no aceptan ninguno de los dos" habría sido falsa. Y por modelo
en vez de por lista escrita a mano porque es justo el tipo de lista que se
pudre — ver MODELOS_CLAUDE_SIN_SAMPLING, que hubo que descubrir igual para la
familia Claude 5.
"""
import pytest

import api_clients as A


class _ClienteFalso:
    """Imita a OpenAI rechazando los parámetros que el modelo no soporte."""

    def __init__(self, sin_max_tokens=False, sin_temperature=False):
        self.sin_max_tokens = sin_max_tokens
        self.sin_temperature = sin_temperature
        self.llamadas = []
        self.chat = self

    @property
    def completions(self):
        return self

    def create(self, **kw):
        self.llamadas.append(kw)
        if self.sin_max_tokens and "max_tokens" in kw:
            raise Exception("Unsupported parameter: 'max_tokens' is not "
                            "supported with this model. Use "
                            "'max_completion_tokens' instead.")
        if self.sin_temperature and "temperature" in kw:
            raise Exception("Unsupported value: 'temperature' does not "
                            "support 0.75 with this model")
        return _Respuesta()


class _Respuesta:
    class _Choice:
        finish_reason = "stop"

        class message:
            content = "OK"

    choices = [_Choice()]
    usage = None


def _proveedor(cliente, modelo):
    p = A.OpenAICompatibleProvider("key", base_url="https://api.openai.com/v1")
    p._cliente = cliente
    p.model = modelo
    return p


@pytest.fixture(autouse=True)
def _sin_memoria_previa():
    A.OpenAICompatibleProvider._SIN_MAX_TOKENS.clear()
    A.OpenAICompatibleProvider._SIN_TEMPERATURE.clear()
    yield
    A.OpenAICompatibleProvider._SIN_MAX_TOKENS.clear()
    A.OpenAICompatibleProvider._SIN_TEMPERATURE.clear()


class TestSeAdaptaAlModeloModerno:

    def test_reintenta_con_max_completion_tokens(self):
        c = _ClienteFalso(sin_max_tokens=True)
        texto, _ = _proveedor(c, "gpt-6-astra")._llamar(
            [{"role": "user", "content": "x"}], 0.75, 300, "gpt-6-astra")
        assert texto == "OK"
        assert "max_completion_tokens" in c.llamadas[-1]
        assert "max_tokens" not in c.llamadas[-1]

    def test_reintenta_sin_temperature(self):
        c = _ClienteFalso(sin_temperature=True)
        texto, _ = _proveedor(c, "o3")._llamar(
            [{"role": "user", "content": "x"}], 0.75, 300, "o3")
        assert texto == "OK"
        assert "temperature" not in c.llamadas[-1]

    def test_aguanta_las_dos_manias_a_la_vez(self):
        c = _ClienteFalso(sin_max_tokens=True, sin_temperature=True)
        texto, _ = _proveedor(c, "gpt-5.6-sol")._llamar(
            [{"role": "user", "content": "x"}], 0.75, 300, "gpt-5.6-sol")
        assert texto == "OK"
        ultima = c.llamadas[-1]
        assert "max_completion_tokens" in ultima and "temperature" not in ultima

    def test_las_manias_son_INDEPENDIENTES(self):
        # gpt-5.4-mini exige max_completion_tokens pero SÍ acepta temperature:
        # tratarlas como un bloque le quitaría el sampling sin motivo.
        c = _ClienteFalso(sin_max_tokens=True)
        _proveedor(c, "gpt-5.4-mini")._llamar(
            [{"role": "user", "content": "x"}], 0.75, 300, "gpt-5.4-mini")
        assert "temperature" in c.llamadas[-1]
        assert "gpt-5.4-mini" not in A.OpenAICompatibleProvider._SIN_TEMPERATURE


class TestNoSePagaElErrorDosVeces:

    def test_recuerda_la_mania_del_modelo(self):
        c = _ClienteFalso(sin_max_tokens=True)
        p = _proveedor(c, "gpt-6-astra")
        for _ in range(3):
            p._llamar([{"role": "user", "content": "x"}], 0.75, 300, "gpt-6-astra")
        # 2 en la primera (falla + reintento) y 1 en cada una de las otras dos.
        assert len(c.llamadas) == 4, (
            "sin memoria se paga un 400 en CADA llamada")

    def test_un_modelo_clasico_no_paga_nada(self):
        c = _ClienteFalso()
        _proveedor(c, "gpt-4o-mini")._llamar(
            [{"role": "user", "content": "x"}], 0.75, 300, "gpt-4o-mini")
        assert len(c.llamadas) == 1
        assert "max_tokens" in c.llamadas[0] and "temperature" in c.llamadas[0]


class TestUnErrorDeVerdadSigueSubiendo:

    def test_no_se_traga_otros_fallos(self):
        class _Roto(_ClienteFalso):
            def create(self, **kw):
                raise Exception("insufficient_quota: sin saldo")
        with pytest.raises(Exception, match="insufficient_quota"):
            _proveedor(_Roto(), "gpt-4o")._llamar(
                [{"role": "user", "content": "x"}], 0.75, 300, "gpt-4o")


class TestLaListaDeOpenAIEstaViva:

    def test_gpt_5_6_a_secas_no_existe(self):
        assert "gpt-5.6" not in A.LLM_PROVIDERS["openai"]["modelos"], (
            "la familia es -sol, -terra y -luna; 'gpt-5.6' da 404")

    def test_el_default_esta_en_la_lista(self):
        info = A.LLM_PROVIDERS["openai"]
        assert info["model_default"] in info["modelos"]

    def test_el_default_tiene_precio_conocido(self):
        # Sin precio propio, el contador de gasto le aplica el respaldo del
        # proveedor. Para el modelo por defecto eso no vale: es el que más se
        # usa y el que sale en el wizard.
        d = A.LLM_PROVIDERS["openai"]["model_default"]
        assert A.PRECIOS_USD_1M_MODELO.get(d), f"{d} sin precio en la tabla"
