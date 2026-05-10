"""Configuración compartida para pytest."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def cleanup_config():
    """Reset configuración global entre tests."""
    yield
    pass
