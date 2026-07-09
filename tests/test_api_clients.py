"""Tests para api_clients.py — proveedores y fábrica."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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
        # deepseek (v4-flash): 0.14/0.28 por 1M → 1M entrada + 1M salida = 0.42
        assert calcular_coste_usd("deepseek", 1_000_000, 1_000_000) == pytest.approx(0.42)

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
        dia = {"openai": {"tokens_entrada": 1_000_000, "tokens_salida": 0},   # 2.50
               "deepseek": {"tokens_entrada": 0, "tokens_salida": 1_000_000}}  # 0.28 (v4-flash)
        assert coste_dia_usd(dia) == pytest.approx(2.78)

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
        for mid in ("claude-fable-5", "claude-opus-4-8",
                    "claude-sonnet-4-6", "claude-haiku-4-5"):
            assert mid in modelos

    def test_fable_restaurado_con_precio(self):
        # claude-fable-5 restaurado el 1-jul-2026 (suspendido 12-jun-2026)
        assert PRECIOS_USD_1M_MODELO["claude-fable-5"] == (10.00, 50.00)

    def test_default_claude_es_sonnet_46(self):
        assert LLM_PROVIDERS["claude"]["model_default"] == "claude-sonnet-4-6"

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
        assert p.model == "claude-sonnet-4-6"
