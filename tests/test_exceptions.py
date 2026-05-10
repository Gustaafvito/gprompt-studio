"""Tests para exceptions.py y types.py."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from exceptions import (
    GPromptError, LLMUnavailableError, APIKeyMissingError,
    ModelNotFoundError, VisionChainError, PersistenceError, ValidationError,
)


class TestExceptions:
    def test_gprompt_error_with_details(self):
        err = GPromptError("algo salió mal", details="más info")
        assert err.message == "algo salió mal"
        assert err.details == "más info"
        assert str(err) == "algo salió mal"

    def test_llm_unavailable(self):
        err = LLMUnavailableError("DeepSeek no disponible")
        assert isinstance(err, GPromptError)
        assert isinstance(err, Exception)

    def test_api_key_missing(self):
        err = APIKeyMissingError("Falta la key de OpenAI")
        assert isinstance(err, GPromptError)

    def test_model_not_found(self):
        err = ModelNotFoundError("Modelo xyz no existe")
        assert isinstance(err, GPromptError)

    def test_vision_chain_error(self):
        err = VisionChainError("Todos los proveedores fallaron")
        assert isinstance(err, GPromptError)

    def test_persistence_error(self):
        err = PersistenceError("No se pudo guardar")
        assert isinstance(err, GPromptError)

    def test_validation_error(self):
        err = ValidationError("Dato inválido")
        assert isinstance(err, GPromptError)
