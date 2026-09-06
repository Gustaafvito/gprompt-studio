"""Reintento cuando un modelo de RAZONAMIENTO agota max_tokens pensando.

Los razonadores (deepseek-v4-pro, o3, deepseek-r1...) "piensan" antes de
responder y esos tokens salen del mismo max_tokens. Si se lo funden razonando
devuelven content VACÍO con HTTP 200 y finish_reason='length'.

Reportado por el usuario (sep-2026) al pulsar Storyboard/Board/Corto con
deepseek-v4-pro: "❌ Error: deepseek-v4-pro: el razonamiento agotó max_tokens
sin producir respuesta". Antes se fallaba directamente y el mensaje pedía
"sube max_tokens", algo que no se puede hacer desde la interfaz.

No se mantiene una lista de "modelos razonadores": envejece mal en cuanto sale
uno nuevo. Se reacciona al SÍNTOMA (vacío + length), que es inequívoco.
"""
from types import SimpleNamespace

import pytest

import api_clients


def _respuesta(content, finish_reason="stop"):
    """Imita lo que devuelve el SDK de OpenAI."""
    return SimpleNamespace(
        choices=[SimpleNamespace(
            message=SimpleNamespace(content=content),
            finish_reason=finish_reason,
        )],
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=20),
    )


class _ClienteFalso:
    """Cliente que responde según un guion, apuntando los max_tokens usados."""

    def __init__(self, guion):
        self._guion = list(guion)
        self.presupuestos = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, model, messages, temperature, max_tokens):
        self.presupuestos.append(max_tokens)
        return self._guion.pop(0)


def _proveedor(guion):
    prov = api_clients.OpenAICompatibleProvider.__new__(
        api_clients.OpenAICompatibleProvider)
    prov.api_key = "x"
    prov.model = "deepseek-v4-pro"
    prov.base_url = "https://api.deepseek.com"
    prov._cliente = _ClienteFalso(guion)
    prov._registrar_uso = lambda *a, **k: None
    return prov


class TestReintentoAutomatico:

    def test_reintenta_con_mas_presupuesto_y_acaba_bien(self):
        """Caso del usuario: 1ª vacía por length, 2ª responde."""
        prov = _proveedor([
            _respuesta("", "length"),
            _respuesta("POSITIVE PROMPT: un gato", "stop"),
        ])
        res = prov.completar([{"role": "user", "content": "hola"}], max_tokens=900)
        assert "un gato" in res
        usados = prov._cliente.presupuestos
        assert usados[0] == 900
        assert usados[1] > usados[0], "el reintento debe ampliar el presupuesto"

    def test_no_reintenta_si_la_primera_responde(self):
        """Sin síntoma no hay reintento: no se gasta de más."""
        prov = _proveedor([_respuesta("ya está", "stop")])
        assert prov.completar([{"role": "user", "content": "hola"}]) == "ya está"
        assert len(prov._cliente.presupuestos) == 1

    def test_el_reintento_respeta_el_techo(self):
        prov = _proveedor([_respuesta("", "length"), _respuesta("ok", "stop")])
        prov.completar([{"role": "user", "content": "hola"}], max_tokens=9000)
        assert prov._cliente.presupuestos[1] <= prov._TECHO_REINTENTO


class TestCuandoSigueFallando:

    def test_error_util_si_ni_con_reintento(self):
        """El mensaje debe decir QUÉ hacer, no 'sube max_tokens'."""
        prov = _proveedor([_respuesta("", "length"), _respuesta("", "length")])
        with pytest.raises(Exception) as exc:
            prov.completar([{"role": "user", "content": "hola"}], max_tokens=900)
        msg = str(exc.value)
        assert "menos cantidad" in msg or "proveedor" in msg
        assert "max_tokens" not in msg.split("—")[-1], \
            "no debe pedir subir algo que no se toca desde la UI"

    def test_vacio_por_otro_motivo_no_reintenta(self):
        """Si no es por 'length' no es el bug del razonador: no gastar otra vez."""
        prov = _proveedor([_respuesta("", "content_filter")])
        with pytest.raises(Exception) as exc:
            prov.completar([{"role": "user", "content": "hola"}])
        assert "content_filter" in str(exc.value)
        assert len(prov._cliente.presupuestos) == 1

    def test_sin_choices_falla_claro(self):
        prov = _proveedor([SimpleNamespace(choices=[], usage=None)])
        with pytest.raises(Exception) as exc:
            prov.completar([{"role": "user", "content": "hola"}])
        assert "choices" in str(exc.value)


class TestNoRecomendarFlash:
    """El mensaje llegó a decir "usa deepseek-v4-flash, que no razona".

    Medido contra la API el 06-sep-2026: flash razona igual que pro — con
    max_tokens=500 gasta los 500 razonando y devuelve vacío, exactamente como
    pro. El consejo mandaba al usuario al mismo muro del que venía.
    """

    def test_el_error_no_recomienda_flash(self):
        prov = _proveedor([_respuesta("", "length"), _respuesta("", "length")])
        with pytest.raises(Exception) as exc:
            prov.completar([{"role": "user", "content": "hola"}], max_tokens=900)
        assert "flash" not in str(exc.value).lower()


class TestSueloDelReintento:
    """Con presupuestos pequeños, multiplicar por 3 no basta.

    "Sugerir negative" pide 500 tokens; ×3 son 1500, y DeepSeek V4 gasta entre
    263 y 780 solo razonando. Unas veces entra y otras no — el usuario lo
    reportó como "me SUELE dar error al escoger negativo".
    """

    def test_presupuesto_pequeno_sube_hasta_el_piso(self):
        prov = _proveedor([_respuesta("", "length"), _respuesta("ok", "stop")])
        prov.completar([{"role": "user", "content": "hola"}], max_tokens=500)
        assert prov._cliente.presupuestos[1] >= prov._PISO_REINTENTO, \
            "500x3=1500 es justo el margen que falla a veces"

    def test_presupuesto_grande_no_baja_al_piso(self):
        prov = _proveedor([_respuesta("", "length"), _respuesta("ok", "stop")])
        prov.completar([{"role": "user", "content": "hola"}], max_tokens=7500)
        assert prov._cliente.presupuestos[1] > prov._PISO_REINTENTO

    def test_el_techo_sigue_mandando(self):
        prov = _proveedor([_respuesta("", "length"), _respuesta("ok", "stop")])
        prov.completar([{"role": "user", "content": "hola"}], max_tokens=9000)
        assert prov._cliente.presupuestos[1] <= prov._TECHO_REINTENTO
