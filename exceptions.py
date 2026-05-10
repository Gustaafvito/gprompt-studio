"""Excepciones custom para G-Prompt Studio."""
from typing import Optional


class GPromptError(Exception):
    """Excepción base para todos los errores de G-Prompt Studio."""
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(message)


class LLMUnavailableError(GPromptError):
    """Lanzada cuando no hay proveedor LLM disponible o configurado."""


class APIKeyMissingError(GPromptError):
    """Lanzada cuando falta la API key de un proveedor."""


class ModelNotFoundError(GPromptError):
    """Lanzada cuando un modelo especificado no existe."""


class VisionChainError(GPromptError):
    """Lanzada cuando falla toda la cadena de proveedores de visión."""


class PersistenceError(GPromptError):
    """Lanzada cuando hay un error al guardar/cargar datos."""


class ValidationError(GPromptError):
    """Lanzada cuando datos de entrada no pasan validación."""
