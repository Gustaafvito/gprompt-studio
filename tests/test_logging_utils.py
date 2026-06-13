"""Tests de logging_utils — red anti-bugs del modo estricto (GPROMPT_DEBUG)."""
import io
import logging

import pytest

import logging_utils as lu


@pytest.fixture
def strict_off(monkeypatch):
    monkeypatch.delenv(lu.STRICT_ENV, raising=False)


@pytest.fixture
def strict_on(monkeypatch):
    monkeypatch.setenv(lu.STRICT_ENV, "1")


# ─── strict_mode() ─────────────────────────────────────────────

def test_strict_mode_off_por_defecto(strict_off):
    assert lu.strict_mode() is False


@pytest.mark.parametrize("valor", ["1", "true", "TRUE", "yes", "on", "si", "sí"])
def test_strict_mode_valores_truthy(monkeypatch, valor):
    monkeypatch.setenv(lu.STRICT_ENV, valor)
    assert lu.strict_mode() is True


@pytest.mark.parametrize("valor", ["0", "false", "no", "", "  "])
def test_strict_mode_valores_falsy(monkeypatch, valor):
    monkeypatch.setenv(lu.STRICT_ENV, valor)
    assert lu.strict_mode() is False


# ─── helpers: tragan en normal, re-lanzan en estricto ──────────

def test_silent_cm_traga_en_modo_normal(strict_off):
    with lu.silent("op"):
        raise ValueError("boom")  # no debe propagar


def test_silent_cm_relanza_en_modo_estricto(strict_on):
    with pytest.raises(ValueError):
        with lu.silent("op"):
            raise ValueError("boom")


def test__silent_traga_y_devuelve_none(strict_off):
    def f():
        raise RuntimeError("x")
    assert lu._silent(f, "op") is None


def test__silent_relanza_en_estricto(strict_on):
    def f():
        raise RuntimeError("x")
    with pytest.raises(RuntimeError):
        lu._silent(f, "op")


def test_silent_call_devuelve_default_en_normal(strict_off):
    @lu.silent_call("op", default="fallback")
    def f():
        raise KeyError("x")
    assert f() == "fallback"


def test_silent_call_relanza_en_estricto(strict_on):
    @lu.silent_call("op", default="fallback")
    def f():
        raise KeyError("x")
    with pytest.raises(KeyError):
        f()


# ─── ReRaiseSilentFilter: cubre los catches inline ─────────────

def test_filtro_relanza_excepcion_viva_al_ver_silent():
    filt = lu.ReRaiseSilentFilter()
    log = logging.getLogger("gprompt.test_filter")
    handler = logging.StreamHandler(io.StringIO())  # real: ejecuta filtros
    handler.addFilter(filt)
    log.handlers = [handler]
    log.setLevel(logging.DEBUG)
    log.propagate = False

    # Reproduce el patrón inline real: debug("[silent] ...") dentro del except.
    with pytest.raises(ValueError):
        try:
            raise ValueError("inline boom")
        except Exception as e:
            log.debug(f"[silent] {e}")


def test_filtro_no_toca_logs_normales():
    filt = lu.ReRaiseSilentFilter()
    rec = logging.LogRecord("x", logging.INFO, __file__, 1, "mensaje normal", None, None)
    assert filt.filter(rec) is True


def test_filtro_sin_excepcion_activa_no_rompe():
    filt = lu.ReRaiseSilentFilter()
    rec = logging.LogRecord("x", logging.DEBUG, __file__, 1, "[silent] sin except", None, None)
    # Fuera de un except sys.exc_info() es (None, None, None) → no debe lanzar.
    assert filt.filter(rec) is True


# ─── install_strict_silent_guard() ────────────────────────────

def test_guard_no_instala_en_modo_normal(strict_off):
    assert lu.install_strict_silent_guard("gprompt.test_guard_off") is False


def test_guard_instala_filtro_en_estricto(strict_on):
    name = "gprompt.test_guard_on"
    log = logging.getLogger(name)
    log.handlers = [logging.NullHandler()]
    try:
        assert lu.install_strict_silent_guard(name) is True
        assert any(
            isinstance(f, lu.ReRaiseSilentFilter) for f in log.handlers[0].filters
        )
        # Idempotente: no duplica el filtro.
        lu.install_strict_silent_guard(name)
        n = sum(
            isinstance(f, lu.ReRaiseSilentFilter) for f in log.handlers[0].filters
        )
        assert n == 1
    finally:
        log.handlers = []
