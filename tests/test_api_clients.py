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


class TestBaseLLMProvider:
    def test_abstract_completar_raises(self):
        p = BaseLLMProvider(api_key="test")
        with pytest.raises(NotImplementedError):
            p.completar([])


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
        # deepseek: 0.28/0.42 por 1M → 1M entrada + 1M salida = 0.70
        assert calcular_coste_usd("deepseek", 1_000_000, 1_000_000) == pytest.approx(0.70)

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
