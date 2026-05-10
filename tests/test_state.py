"""Tests para state.py y logging_utils.py."""
import pytest
import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestAppState:
    def test_initial_values(self):
        from state import AppState
        state = AppState()
        assert state.modo.get() == "imagen"
        assert state.plataforma.get() == "SeaArt / Tensor.Art"
        assert state.nsfw.get() is False
        assert state.traduccion.get() is True
        assert state.brief.get() is False
        assert state.ratio.get() == "1:1"
        assert state.destino.get() == "— Personal —"

    def test_cache_invalidation(self):
        from state import AppState
        state = AppState()
        state._cache_natural = True
        state.invalidate_natural_cache()
        assert state._cache_natural is None

    def test_reset(self):
        from state import AppState
        state = AppState()
        state.estilo_checks["test"] = True
        state.reset()
        assert state.estilo_checks == {}
        assert state._cache_natural is None


class TestLogOperation:
    def test_log_operation_success(self, caplog):
        from logging_utils import log_operation
        with caplog.at_level(logging.INFO):
            @log_operation("test op")
            def dummy_fn(x):
                return x * 2
            result = dummy_fn(5)
        assert result == 10
        records = [r.message for r in caplog.records if "test op" in r.message]
        assert len(records) >= 1

    def test_log_operation_error(self, caplog):
        from logging_utils import log_operation
        with caplog.at_level(logging.ERROR):
            @log_operation("falling op", level=logging.ERROR)
            def failing_fn():
                raise ValueError("boom")
            with pytest.raises(ValueError):
                failing_fn()
