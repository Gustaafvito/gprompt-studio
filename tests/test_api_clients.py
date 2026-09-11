"""Tests para api_clients.py — proveedores y fábrica."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import api_clients
from api_clients import (
    LLM_PROVIDERS,
    BaseLLMProvider,
    ClaudeProvider,
    GeminiProvider,
    OpenAICompatibleProvider,
    get_provider,
)


class TestLLMProviders:
    def test_all_providers_have_required_keys(self):
        required = {"name", "label", "tipo", "model_default"}
        for pid, info in LLM_PROVIDERS.items():
            for key in required:
                assert key in info, f"Provider {pid} missing key: {key}"

    def test_provider_types_are_valid(self):
        valid_types = {"openai_compatible", "google", "anthropic"}
        for pid, info in LLM_PROVIDERS.items():
            assert info["tipo"] in valid_types, f"Provider {pid} has invalid type: {info['tipo']}"


class TestGetProvider:
    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError):
            get_provider("nonexistent", "fake-key")

    def test_openai_compatible_provider(self):
        p = get_provider("deepseek", "test-key")
        assert isinstance(p, OpenAICompatibleProvider)
        assert p.disponible() is True

    def test_gemini_provider(self):
        p = get_provider("gemini", "test-key")
        assert isinstance(p, GeminiProvider)

    def test_ollama_provider_no_key(self):
        p = get_provider("ollama", None)
        assert isinstance(p, OpenAICompatibleProvider)

    def test_claude_provider_without_anthropic_installed(self):
        p = get_provider("claude", "test-key")
        assert isinstance(p, ClaudeProvider)


class TestOpenAICompatibleProvider:
    def test_no_api_key_not_available(self):
        p = OpenAICompatibleProvider(api_key=None, model="test")
        assert p.disponible() is False

    def test_with_api_key_available(self):
        p = OpenAICompatibleProvider(api_key="sk-test", model="test")
        assert p.disponible() is True

    def test_completar_raises_without_key(self):
        p = OpenAICompatibleProvider(api_key=None, model="test")
        with pytest.raises(Exception, match="Proveedor no configurado"):
            p.completar([{"role": "user", "content": "hello"}])

    def _provider_con_respuesta(self, content, finish_reason="stop"):
        """Provider con el cliente OpenAI mockeado devolviendo `content`."""
        from unittest.mock import MagicMock
        p = OpenAICompatibleProvider(api_key="sk-test", model="test")
        choice = MagicMock()
        choice.message.content = content
        choice.finish_reason = finish_reason
        res = MagicMock()
        res.choices = [choice]
        res.usage = None
        p._cliente = MagicMock()
        p._cliente.chat.completions.create.return_value = res
        return p

    def test_completar_raises_si_razonamiento_agota_tokens(self):
        # CANDADO auditoría 14-jul-2026: DeepSeek V4 (razonador) quemaba TODO
        # el max_tokens "pensando" (finish_reason='length') y devolvía content
        # vacío con HTTP 200; el "" silencioso producía datasets sin identidad.
        p = self._provider_con_respuesta("", finish_reason="length")
        # 06-sep-2026: el texto pasó a "se quedó sin tokens razonando" al
        # dejar de recomendar flash (que también razona). Se comprueba el
        # síntoma, no la frase exacta.
        with pytest.raises(Exception, match="sin tokens razonando"):
            p.completar([{"role": "user", "content": "hola"}])

    def test_completar_raises_si_respuesta_vacia(self):
        p = self._provider_con_respuesta(None, finish_reason="stop")
        with pytest.raises(Exception, match="respuesta vacía"):
            p.completar([{"role": "user", "content": "hola"}])

    def test_completar_devuelve_contenido_normal(self):
        p = self._provider_con_respuesta("un prompt estupendo")
        out = p.completar([{"role": "user", "content": "hola"}])
        assert out == "un prompt estupendo"

    def test_completar_acepta_truncado_con_contenido(self):
        # finish_reason='length' con contenido PARCIAL sigue siendo útil:
        # solo se rechaza cuando además viene vacío.
        p = self._provider_con_respuesta("texto truncado", finish_reason="length")
        assert p.completar([{"role": "user", "content": "hola"}]) == "texto truncado"


class TestGeminiProvider:
    def test_no_api_key_not_available(self):
        p = GeminiProvider(api_key=None)
        assert p.disponible() is False

    def test_completar_raises_without_key(self):
        p = GeminiProvider(api_key=None)
        with pytest.raises(Exception, match="Gemini no configurado"):
            p.completar([{"role": "user", "content": "hello"}])


class TestLimpiarRespuestaGemini:
    """El scrubbing elimina SOLO tags <system-reminder>, nunca frases legítimas."""

    def test_elimina_bloque_system_reminder(self):
        from api_clients import _limpiar_respuesta_gemini
        raw = "prompt bueno <system-reminder>eco del harness</system-reminder> final"
        assert _limpiar_respuesta_gemini(raw) == "prompt bueno  final".strip()

    def test_elimina_tag_suelto_sin_cierre(self):
        from api_clients import _limpiar_respuesta_gemini
        assert _limpiar_respuesta_gemini("<system-reminder>texto") == "texto"

    def test_no_toca_frases_legitimas(self):
        # Regresión: el scrubbing viejo borraba estas frases del prompt.
        from api_clients import _limpiar_respuesta_gemini
        raw = ('A robot saying "You are Claude, an AI assistant" on a screen, '
               "cinematic lighting, You are a helpful assistant written in neon")
        assert _limpiar_respuesta_gemini(raw) == raw

    def test_texto_limpio_pasa_intacto(self):
        from api_clients import _limpiar_respuesta_gemini
        assert _limpiar_respuesta_gemini("  prompt normal  ") == "prompt normal"


class TestBaseLLMProvider:
    def test_abstract_completar_raises(self):
        p = BaseLLMProvider(api_key="test")
        with pytest.raises(NotImplementedError):
            p.completar([])


class TestKeysFallbackCifrado:
    """keys.json: DPAPI (v2, Windows) con lectura retrocompatible del AES v1."""

    def _usar_ruta_tmp(self, monkeypatch, tmp_path):
        import config
        monkeypatch.setitem(config.ARCHIVOS, "keys", tmp_path / "keys.json")
        return tmp_path / "keys.json"

    def test_roundtrip_guardar_cargar(self, monkeypatch, tmp_path):
        from api_clients import _cargar_keys_fallback, _guardar_keys_fallback
        self._usar_ruta_tmp(monkeypatch, tmp_path)
        _guardar_keys_fallback("deepseek", "sk-test-123456789")
        assert _cargar_keys_fallback("deepseek") == "sk-test-123456789"

    def test_la_key_no_queda_en_claro_en_disco(self, monkeypatch, tmp_path):
        import json as _json

        from api_clients import _guardar_keys_fallback
        ruta = self._usar_ruta_tmp(monkeypatch, tmp_path)
        _guardar_keys_fallback("groq", "gsk_super_secreta_987654")
        contenido = ruta.read_text(encoding="utf-8")
        assert "gsk_super_secreta_987654" not in contenido
        datos = _json.loads(contenido)
        assert datos.get("encrypted") in ("dpapi", True)

    def test_en_windows_usa_dpapi_v2(self, monkeypatch, tmp_path):
        import json as _json
        import os as _os

        from api_clients import _guardar_keys_fallback
        if _os.name != "nt":
            pytest.skip("DPAPI solo en Windows")
        ruta = self._usar_ruta_tmp(monkeypatch, tmp_path)
        _guardar_keys_fallback("openai", "sk-proj-abcdef123456")
        datos = _json.loads(ruta.read_text(encoding="utf-8"))
        assert datos["version"] == 2
        assert datos["encrypted"] == "dpapi"

    def test_legacy_aes_v1_se_sigue_leyendo(self, monkeypatch, tmp_path):
        # Un keys.json v1 (AES MAC+usuario) escrito por versiones anteriores
        # debe seguir siendo legible tras la migración a DPAPI.
        import json as _json

        from api_clients import (
            _cargar_keys_fallback,
            _cifrar_aes,
            _obtener_clave_cifrado,
        )
        ruta = self._usar_ruta_tmp(monkeypatch, tmp_path)
        clave = _obtener_clave_cifrado()
        datos = {"version": 1, "encrypted": True,
                 "keys": {"mistral": _cifrar_aes("legacy_key_00112233", clave)}}
        ruta.write_text(_json.dumps(datos), encoding="utf-8")
        assert _cargar_keys_fallback("mistral") == "legacy_key_00112233"

    def test_borrar_key_del_fallback(self, monkeypatch, tmp_path):
        from api_clients import (
            _borrar_keys_fallback,
            _cargar_keys_fallback,
            _guardar_keys_fallback,
        )
        self._usar_ruta_tmp(monkeypatch, tmp_path)
        _guardar_keys_fallback("xai", "xai-key-1234567890")
        _borrar_keys_fallback("xai")
        assert _cargar_keys_fallback("xai") == ""


# ── Tracking de uso y costes (sesión 19) ──────────────────────────

from api_clients import (  # noqa: E402
    PRECIOS_USD_1M,
    UsageTracker,
    calcular_coste_usd,
)


class TestPreciosUsd1M:
    def test_todos_los_providers_tienen_precio(self):
        # Cada provider LLM debe estar en la tabla (aunque sea None=variable)
        for pid in LLM_PROVIDERS:
            assert pid in PRECIOS_USD_1M, f"Falta precio para {pid}"

    def test_sin_precios_huerfanos(self):
        # La tabla no debe tener providers que ya no existen
        for pid in PRECIOS_USD_1M:
            assert pid in LLM_PROVIDERS, f"Precio huérfano: {pid}"

    def test_providers_gratuitos_cuestan_cero(self):
        for pid, info in LLM_PROVIDERS.items():
            precios = PRECIOS_USD_1M.get(pid)
            if not info.get("is_paid") and precios is not None:
                assert precios == (0.0, 0.0), f"{pid} es gratis pero tiene precio {precios}"


class TestCalcularCosteUsd:
    def test_coste_basico(self):
        # La tarifa se saca de la tabla, no se escribe aquí: lo que este test
        # comprueba es la ARITMÉTICA. Con la cifra a mano, renombrar un modelo
        # —deepseek-v4-flash pasó a deepseek-flash el 11-sep-2026, y con él su
        # precio— rompía un test que no tenía nada que ver con el cambio.
        entrada, salida = PRECIOS_USD_1M["deepseek"]
        assert calcular_coste_usd("deepseek", 1_000_000, 1_000_000) == (
            pytest.approx(entrada + salida))

    def test_provider_gratuito_cero(self):
        assert calcular_coste_usd("ollama", 500_000, 500_000) == 0.0

    def test_precio_desconocido_devuelve_none(self):
        assert calcular_coste_usd("openrouter", 1000, 1000) is None

    def test_provider_inexistente_devuelve_none(self):
        assert calcular_coste_usd("no-existe", 1000, 1000) is None

    def test_cero_tokens_cero_coste(self):
        assert calcular_coste_usd("openai", 0, 0) == 0.0


class TestUsageTracker:
    def test_registrar_acumula(self):
        t = UsageTracker()
        t.registrar("deepseek", 100, 50)
        t.registrar("deepseek", 200, 80)
        r = t.resumen()
        assert r["deepseek"]["llamadas"] == 2
        assert r["deepseek"]["tokens_entrada"] == 300
        assert r["deepseek"]["tokens_salida"] == 130

    def test_resumen_calcula_coste(self):
        t = UsageTracker()
        t.registrar("openai", 1_000_000, 0)  # 2.50 $
        assert t.resumen()["openai"]["coste_usd"] == pytest.approx(2.50)

    def test_total_ignora_costes_desconocidos(self):
        t = UsageTracker()
        t.registrar("openai", 1_000_000, 0)      # 2.50
        t.registrar("openrouter", 999_999, 999)  # None → no suma
        assert t.total_usd() == pytest.approx(2.50)
        assert t.resumen()["openrouter"]["coste_usd"] is None

    def test_provider_vacio_va_a_desconocido(self):
        t = UsageTracker()
        t.registrar("", 10, 10)
        assert "desconocido" in t.resumen()

    def test_tokens_negativos_o_none_no_rompen(self):
        t = UsageTracker()
        t.registrar("deepseek", None, -5)
        r = t.resumen()["deepseek"]
        assert r["tokens_entrada"] == 0
        assert r["tokens_salida"] == 0
        assert r["llamadas"] == 1

    def test_reset_limpia(self):
        t = UsageTracker()
        t.registrar("openai", 100, 100)
        t.reset()
        assert t.resumen() == {}
        assert t.total_usd() == 0

    def test_thread_safety_basica(self):
        import threading as _th
        t = UsageTracker()

        def _hammer():
            for _ in range(200):
                t.registrar("groq", 10, 5)

        hilos = [_th.Thread(target=_hammer) for _ in range(8)]
        for h in hilos: h.start()
        for h in hilos: h.join()
        r = t.resumen()["groq"]
        assert r["llamadas"] == 1600
        assert r["tokens_entrada"] == 16000
        assert r["tokens_salida"] == 8000


class TestProviderIdAsignado:
    def test_get_provider_asigna_provider_id(self):
        p = get_provider("deepseek", "test-key")
        assert p.provider_id == "deepseek"

    def test_registrar_uso_no_rompe_sin_id(self):
        p = BaseLLMProvider(api_key="x")
        p._registrar_uso(10, 10)  # no debe lanzar


# ── Histórico persistente de uso (sesión 19, mejora 2) ────────────

from api_clients import acumular_historico, coste_dia_usd  # noqa: E402


class TestPendientePersistir:
    def test_primera_llamada_devuelve_todo(self):
        t = UsageTracker()
        t.registrar("deepseek", 100, 50)
        delta = t.pendiente_persistir()
        assert delta == {"deepseek": {"llamadas": 1, "tokens_entrada": 100,
                                      "tokens_salida": 50}}

    def test_segunda_llamada_sin_uso_nuevo_devuelve_vacio(self):
        t = UsageTracker()
        t.registrar("deepseek", 100, 50)
        t.pendiente_persistir()
        assert t.pendiente_persistir() == {}

    def test_solo_devuelve_el_delta(self):
        t = UsageTracker()
        t.registrar("deepseek", 100, 50)
        t.pendiente_persistir()
        t.registrar("deepseek", 30, 10)
        delta = t.pendiente_persistir()
        assert delta == {"deepseek": {"llamadas": 1, "tokens_entrada": 30,
                                      "tokens_salida": 10}}

    def test_no_afecta_al_resumen_de_sesion(self):
        t = UsageTracker()
        t.registrar("deepseek", 100, 50)
        t.pendiente_persistir()
        # El resumen de sesión sigue mostrando el total
        assert t.resumen()["deepseek"]["tokens_entrada"] == 100

    def test_reset_limpia_tambien_el_drenado(self):
        t = UsageTracker()
        t.registrar("deepseek", 100, 50)
        t.pendiente_persistir()
        t.reset()
        t.registrar("deepseek", 20, 5)
        delta = t.pendiente_persistir()
        assert delta["deepseek"]["tokens_entrada"] == 20


class TestAcumularHistorico:
    def test_crea_dia_y_acumula(self):
        h = {}
        acumular_historico(h, {"deepseek": {"llamadas": 2, "tokens_entrada": 100,
                                            "tokens_salida": 50}}, "2026-06-10")
        acumular_historico(h, {"deepseek": {"llamadas": 1, "tokens_entrada": 30,
                                            "tokens_salida": 10}}, "2026-06-10")
        d = h["2026-06-10"]["deepseek"]
        assert d == {"llamadas": 3, "tokens_entrada": 130, "tokens_salida": 60}

    def test_dias_distintos_no_se_mezclan(self):
        h = {}
        acumular_historico(h, {"openai": {"llamadas": 1, "tokens_entrada": 10,
                                          "tokens_salida": 5}}, "2026-06-09")
        acumular_historico(h, {"openai": {"llamadas": 1, "tokens_entrada": 20,
                                          "tokens_salida": 8}}, "2026-06-10")
        assert h["2026-06-09"]["openai"]["tokens_entrada"] == 10
        assert h["2026-06-10"]["openai"]["tokens_entrada"] == 20

    def test_poda_dias_antiguos(self):
        h = {}
        for i in range(1, 71):
            acumular_historico(h, {"groq": {"llamadas": 1, "tokens_entrada": 1,
                                            "tokens_salida": 1}},
                               f"2026-03-{i:02d}" if i <= 31 else f"2026-04-{i-31:02d}",
                               max_dias=60)
        assert len(h) == 60
        # Se conservan las fechas más recientes
        assert "2026-03-01" not in h

    def test_valores_negativos_no_restan(self):
        h = {}
        acumular_historico(h, {"deepseek": {"llamadas": -5, "tokens_entrada": -10,
                                            "tokens_salida": 3}}, "2026-06-10")
        d = h["2026-06-10"]["deepseek"]
        assert d["llamadas"] == 0 and d["tokens_entrada"] == 0
        assert d["tokens_salida"] == 3


class TestCosteDiaUsd:
    def test_suma_costes_conocidos(self):
        dia = {"openai": {"tokens_entrada": 1_000_000, "tokens_salida": 0},
               "deepseek": {"tokens_entrada": 0, "tokens_salida": 1_000_000}}
        esperado = PRECIOS_USD_1M["openai"][0] + PRECIOS_USD_1M["deepseek"][1]
        assert coste_dia_usd(dia) == pytest.approx(esperado)

    def test_ignora_costes_desconocidos(self):
        dia = {"openrouter": {"tokens_entrada": 999, "tokens_salida": 999}}
        assert coste_dia_usd(dia) == 0.0


# ── Selector de modelo por proveedor (sesión 19 round 13) ─────────

from api_clients import (  # noqa: E402
    MODELOS_CLAUDE_SIN_SAMPLING,
    PRECIOS_USD_1M_MODELO,
    modelo_acepta_temperature,
)


class TestModelosClaude:
    def test_ids_oficiales_en_lista_seleccionable(self):
        modelos = LLM_PROVIDERS["claude"]["modelos"]
        for mid in ("claude-fable-5-1", "claude-opus-5",
                    "claude-sonnet-5", "claude-haiku-4-5"):
            assert mid in modelos

    def test_fable_restaurado_con_precio(self):
        # claude-fable-5 restaurado el 1-jul-2026 (suspendido 12-jun-2026)
        assert PRECIOS_USD_1M_MODELO["claude-fable-5"] == (10.00, 50.00)

    def test_default_claude_es_sonnet_5(self):
        assert LLM_PROVIDERS["claude"]["model_default"] == "claude-sonnet-5"

    def test_la_familia_5_no_acepta_temperature(self):
        """Sonnet 5 / Opus 5 / Fable 5.1 devuelven 400 si se envía temperature.

        Candado añadido el 06-sep-2026: al poner claude-sonnet-5 como default
        faltaba meterlo en MODELOS_CLAUDE_SIN_SAMPLING, y eso habría hecho
        fallar TODAS las llamadas a Claude con un 400.
        """
        for mid in ("claude-sonnet-5", "claude-opus-5", "claude-fable-5-1"):
            assert modelo_acepta_temperature(mid) is False, mid

    def test_opus_no_acepta_temperature(self):
        # Opus 4.8 / 4.7 devuelven 400 si se envía temperature
        for mid in MODELOS_CLAUDE_SIN_SAMPLING:
            assert modelo_acepta_temperature(mid) is False
        assert modelo_acepta_temperature("claude-opus-4-8") is False

    def test_fable_no_acepta_temperature(self):
        # Fable 5 rechaza temperature igual que Opus 4.8/4.7
        assert modelo_acepta_temperature("claude-fable-5") is False

    def test_sonnet_y_haiku_si_aceptan_temperature(self):
        assert modelo_acepta_temperature("claude-sonnet-4-6") is True
        assert modelo_acepta_temperature("claude-haiku-4-5") is True
        assert modelo_acepta_temperature("claude-sonnet-4-5-20250929") is True
        assert modelo_acepta_temperature("") is True

    def test_precios_oficiales_anthropic(self):
        assert PRECIOS_USD_1M_MODELO["claude-opus-4-8"] == (5.00, 25.00)
        assert PRECIOS_USD_1M_MODELO["claude-sonnet-4-6"] == (3.00, 15.00)
        assert PRECIOS_USD_1M_MODELO["claude-haiku-4-5"] == (1.00, 5.00)

    def test_modelos_seleccionables_tienen_precio(self):
        for mid in LLM_PROVIDERS["claude"]["modelos"]:
            assert mid in PRECIOS_USD_1M_MODELO, f"Sin precio: {mid}"


class TestCostePorModelo:
    def test_precio_de_modelo_prioriza_sobre_provider(self):
        # Provider claude = (3, 15) pero opus-4-8 = (5, 25)
        assert calcular_coste_usd("claude", 1_000_000, 0,
                                  modelo="claude-opus-4-8") == pytest.approx(5.0)
        assert calcular_coste_usd("claude", 1_000_000, 0) == pytest.approx(3.0)

    def test_modelo_desconocido_cae_al_precio_del_provider(self):
        assert calcular_coste_usd("claude", 1_000_000, 0,
                                  modelo="claude-futuro-9") == pytest.approx(3.0)

    def test_tracker_desglosa_coste_por_modelo(self):
        t = UsageTracker()
        t.registrar("claude", 1_000_000, 0, modelo="claude-opus-4-8")   # 5.0
        t.registrar("claude", 1_000_000, 0, modelo="claude-haiku-4-5")  # 1.0
        r = t.resumen()["claude"]
        assert r["coste_usd"] == pytest.approx(6.0)
        assert r["tokens_entrada"] == 2_000_000

    def test_tracker_sin_modelo_usa_precio_del_provider(self):
        t = UsageTracker()
        t.registrar("openai", 1_000_000, 0)
        assert t.resumen()["openai"]["coste_usd"] == pytest.approx(2.50)


class TestSetModel:
    def test_get_provider_respeta_modelo_elegido(self):
        p = get_provider("claude", "test-key", model="claude-opus-4-8")
        assert p.model == "claude-opus-4-8"

    def test_get_provider_sin_modelo_usa_default(self):
        p = get_provider("claude", "test-key")
        assert p.model == "claude-sonnet-5"

class TestMigracionDPAPI:
    """Las API keys en formato viejo (v0 en claro / v1 AES con clave MAC+usuario)
    se reescriben con DPAPI al leerlas. Se migra en vez de borrar el formato
    viejo para no dejar a nadie sin claves.
    """

    def test_migra_si_dpapi_disponible(self, monkeypatch):
        escrito = {}
        monkeypatch.setattr(api_clients, "_dpapi_disponible", lambda: True)
        monkeypatch.setattr(api_clients, "_escribir_dict_fallback",
                            lambda d: escrito.update(d))
        api_clients._migrar_a_dpapi({"openai": "sk-vieja"})
        assert escrito == {"openai": "sk-vieja"}

    def test_no_migra_sin_dpapi(self, monkeypatch):
        llamadas = []
        monkeypatch.setattr(api_clients, "_dpapi_disponible", lambda: False)
        monkeypatch.setattr(api_clients, "_escribir_dict_fallback",
                            lambda d: llamadas.append(d))
        api_clients._migrar_a_dpapi({"openai": "sk-vieja"})
        assert llamadas == []

    def test_migracion_fallida_no_rompe(self, monkeypatch):
        def _boom(_d):
            raise OSError("disco lleno")
        monkeypatch.setattr(api_clients, "_dpapi_disponible", lambda: True)
        monkeypatch.setattr(api_clients, "_escribir_dict_fallback", _boom)
        api_clients._migrar_a_dpapi({"openai": "sk"})  # no debe lanzar

class TestLMStudioProvider:
    """LM Studio es local como Ollama: el modelo NO se elige a mano, se usa el
    que el usuario tenga cargado. Antes se enviaba el literal "local-model" de
    model_default, que las versiones recientes rechazan con "model not found".
    """

    def test_la_fabrica_usa_la_clase_dedicada(self):
        prov = api_clients.get_provider("lm_studio", api_key="")
        assert isinstance(prov, api_clients.LMStudioProvider)
        # 127.0.0.1 y no localhost: en Windows localhost resuelve ::1 primero
        # y ese puerto se cuelga 1s antes de caer a IPv4 (07-sep-2026).
        assert prov.base_url == "http://127.0.0.1:1234/v1"

    def test_lista_los_modelos_cargados(self, monkeypatch):
        api_clients._CACHE_LOCAL.clear()
        prov = api_clients.LMStudioProvider()
        monkeypatch.setattr(prov, "listar_modelos", lambda: ["qwen2.5-7b", "otro"])
        # disponible() ya NO pasa por listar_modelos: sondea el puerto. Sin
        # simularlo, este test dependia de que LM Studio estuviera abierto en
        # la maquina que corre la suite — pasaba o fallaba segun la hora.
        monkeypatch.setattr(api_clients, "_puerto_abierto", lambda *a, **k: True)
        assert prov.disponible() is True
        assert prov._obtener_modelo_disponible() == "qwen2.5-7b"

    def test_sin_servidor_no_esta_disponible(self, monkeypatch):
        api_clients._CACHE_LOCAL.clear()   # el sondeo local se cachea 20s
        # disponible() ya no lista modelos: mira si el puerto esta abierto.
        # Se apunta a un puerto muerto en vez de simular, porque en la maquina
        # de desarrollo LM Studio puede estar corriendo de verdad.
        prov = api_clients.LMStudioProvider(base_url="http://127.0.0.1:1/v1")
        monkeypatch.setattr(prov, "listar_modelos", lambda: [])
        assert prov.disponible() is False
        assert prov._obtener_modelo_disponible() is None

    def test_error_claro_si_no_hay_nada_cargado(self, monkeypatch):
        prov = api_clients.LMStudioProvider()
        monkeypatch.setattr(prov, "listar_modelos", lambda: [])
        with pytest.raises(Exception) as exc:
            prov.completar([{"role": "user", "content": "hola"}])
        msg = str(exc.value)
        assert "LM Studio" in msg and "1234" in msg

    def test_el_placeholder_se_resuelve_al_modelo_real(self, monkeypatch):
        """model_default es "local-model": no es un modelo, hay que resolverlo."""
        prov = api_clients.LMStudioProvider(model="local-model")
        monkeypatch.setattr(prov, "listar_modelos", lambda: ["mistral-7b"])
        usado = {}

        def _fake(self, messages, temperature=0.75, max_tokens=900, model=None):
            usado["model"] = model
            return "ok"

        monkeypatch.setattr(api_clients.OpenAICompatibleProvider, "completar", _fake)
        assert prov.completar([{"role": "user", "content": "hola"}]) == "ok"
        assert usado["model"] == "mistral-7b"

class TestElegirModeloChat:
    """Los servidores locales listan TODO lo descargado. Coger "el primero"
    puede caer en un modelo de embeddings y fallar de forma incomprensible.
    """

    def test_descarta_embeddings(self):
        elegido = api_clients.elegir_modelo_chat(
            ["text-embedding-nomic-embed-text-v1.5", "qwen2.5-32b-instruct"])
        assert elegido == "qwen2.5-32b-instruct"

    def test_none_si_solo_hay_embeddings(self):
        assert api_clients.elegir_modelo_chat(
            ["text-embedding-nomic-embed-text-v1.5"]) is None

    def test_descarta_rerankers(self):
        assert api_clients.elegir_modelo_chat(["bge-reranker-v2", "mistral"]) == "mistral"

    def test_vision_va_al_final_pero_no_se_descarta(self):
        assert api_clients.elegir_modelo_chat(["llava:latest", "mistral"]) == "mistral"
        # Si es lo unico instalado, se usa igualmente.
        assert api_clients.elegir_modelo_chat(["llava:latest"]) == "llava:latest"

    def test_lista_vacia(self):
        assert api_clients.elegir_modelo_chat([]) is None

    def test_respeta_el_orden_entre_modelos_validos(self):
        assert api_clients.elegir_modelo_chat(["a-instruct", "b-instruct"]) == "a-instruct"

class TestModelosDisponibles:
    """El desplegable de modelos: los proveedores LOCALES se consultan en vivo
    (su lista es lo que el usuario tenga cargado), los de nube son estáticos.
    """

    def test_los_de_nube_usan_su_lista_estatica(self):
        from api_clients import LLM_PROVIDERS
        assert (api_clients.modelos_disponibles("deepseek")
                == list(LLM_PROVIDERS["deepseek"]["modelos"]))

    def test_los_locales_se_consultan_en_vivo(self, monkeypatch):
        class _Fake:
            def listar_modelos(self):
                return ["qwen2.5-32b", "nomic-embed-text", "llava"]
        monkeypatch.setattr(api_clients, "get_provider", lambda *a, **k: _Fake())
        got = api_clients.modelos_disponibles("lm_studio")
        assert "nomic-embed-text" not in got      # embeddings fuera
        assert got == ["qwen2.5-32b", "llava"]    # visión al final

    def test_si_el_servidor_local_no_responde_devuelve_vacio(self, monkeypatch):
        def _boom(*a, **k):
            raise OSError("connection refused")
        monkeypatch.setattr(api_clients, "get_provider", _boom)
        assert api_clients.modelos_disponibles("lm_studio") == []

    def test_ordenar_quita_embeddings_y_deja_vision_al_final(self):
        got = api_clients.ordenar_modelos_chat(
            ["llava", "text-embedding-3", "mistral", "qwen2.5vl", "phi-4"])
        assert got == ["mistral", "phi-4", "llava", "qwen2.5vl"]

    def test_lm_studio_y_ollama_son_los_locales(self):
        assert set(api_clients.PROVEEDORES_LOCALES) == {"lm_studio", "ollama"}
