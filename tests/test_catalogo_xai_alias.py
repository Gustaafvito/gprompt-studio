"""x.ai: la lista iba tres generaciones por detrás y los alias se tiraban.

08-sep-2026, con la key del usuario recién creada. La lista curada era
`grok-3`, `grok-3-mini`, `grok-2-1212` y NINGUNO de los tres existe ya —
incluido el `model_default`, así que el botón "Probar keys" fallaba con una
key perfectamente válida (el mismo síntoma que ya tuvo Groq).

Y un fallo de fondo que solo se ve con x.ai: publica el id CON fecha
("grok-4.20-0309-reasoning") y el estable como ALIAS ("grok-4.20"). Lo que
interesa curar es el estable, porque el fechado se rompe cuando rota la
fecha — pero `listar_modelos()` solo leía `m["id"]`, así que un alias curado
aparecía MUERTO aunque el modelo responda. Los alias son nombres que el
proveedor acepta igual en /chat/completions: probado, `grok-4.20` y
`grok-code-fast` contestan los dos.

De paso, todos los Grok razonan menos la variante non-reasoning (tokens
quemados pensando antes de escribir "OK": 4.20-non-reasoning 0, 4.5 30,
4.6 132, 4.3 165, 4.20 174, build-0.1 366). Es la trampa de DeepSeek V4 otra
vez, así que el default es el non-reasoning y no el flagship.
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


class TestLosAliasCuentanComoVivos:

    def _prov(self):
        return A.OpenAICompatibleProvider("una-key", base_url="https://api.x.ai/v1")

    def test_el_alias_estable_sale_en_el_catalogo(self, monkeypatch):
        _con_respuesta(monkeypatch, {"data": [
            {"id": "grok-4.20-0309-reasoning",
             "aliases": ["grok-4.20", "grok-4.20-reasoning"]},
        ]})
        vivos = self._prov().listar_modelos()
        assert "grok-4.20" in vivos, (
            "curar el id fechado se rompe al rotar la fecha; el estable es el "
            "alias, y sin contarlo la lista curada parece muerta")
        assert "grok-4.20-0309-reasoning" in vivos, "el id tambien sigue valiendo"

    def test_sin_alias_no_cambia_nada(self, monkeypatch):
        _con_respuesta(monkeypatch, {"data": [{"id": "gpt-4o"}]})
        assert self._prov().listar_modelos() == ["gpt-4o"]

    def test_alias_vacios_o_nulos_no_ensucian(self, monkeypatch):
        _con_respuesta(monkeypatch, {"data": [
            {"id": "m1", "aliases": None},
            {"id": "m2", "aliases": []},
            {"id": "m3", "aliases": ["", "bueno"]},
        ]})
        assert self._prov().listar_modelos() == ["m1", "m2", "m3", "bueno"]

    def test_una_entrada_sin_id_se_ignora(self, monkeypatch):
        _con_respuesta(monkeypatch, {"data": [{"aliases": ["huerfano"]}, {"id": "m1"}]})
        assert self._prov().listar_modelos() == ["m1"]


class TestLaListaDeGrokEstaViva:

    def test_ninguno_de_la_generacion_muerta(self):
        for muerto in ("grok-3", "grok-3-mini", "grok-2-1212"):
            assert muerto not in A.LLM_PROVIDERS["xai"]["modelos"], (
                f"{muerto} ya no existe en la API de x.ai")

    def test_el_default_esta_en_la_lista(self):
        info = A.LLM_PROVIDERS["xai"]
        assert info["model_default"] in info["modelos"], (
            "el wizard prueba la key con el model_default: si no esta "
            "curado, una key valida se declara invalida")

    def test_el_default_no_razona(self):
        # Los razonadores se funden max_tokens pensando y devuelven vacio con
        # los presupuestos pequenos que pide la app (200-500 en varios sitios).
        assert A.LLM_PROVIDERS["xai"]["model_default"] == "grok-4.20-non-reasoning"

    def test_todos_tienen_precio(self):
        for m in A.LLM_PROVIDERS["xai"]["modelos"]:
            assert A.PRECIOS_USD_1M_MODELO.get(m), (
                f"{m} sin precio: el contador de gasto lo daria por gratis")

    def test_los_precios_de_grok_3_ya_no_estan(self):
        for muerto in ("grok-3", "grok-3-mini"):
            assert muerto not in A.PRECIOS_USD_1M_MODELO

    def test_el_precio_de_respaldo_es_el_del_default(self):
        assert A.PRECIOS_USD_1M["xai"] == A.PRECIOS_USD_1M_MODELO["grok-4.20-non-reasoning"]
