"""Tests para api_clients.py — proveedores y fábrica."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api_clients import (
    LLM_PROVIDERS,
    BaseLLMProvider,
    OpenAICompatibleProvider,
    GeminiProvider,
    ClaudeProvider,
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
