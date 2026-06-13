"""Logging utilities — decoradores y helpers para logging estructurado.

Modo estricto (red anti-bugs):
    Exportar GPROMPT_DEBUG=1 antes de arrancar hace que TODA excepción
    capturada silenciosamente (los ~336 `logger.debug("[silent] ...")`
    repartidos por el código + los helpers de este módulo) se RE-LANCE
    en lugar de tragarse. Sirve para cazar bugs nuevos que de otro modo
    quedarían ocultos. Es ruidoso por diseño: en modo estricto hasta un
    `w.destroy()` fallido durante el cierre crashea. Solo para depurar.
"""
import contextlib
import functools
import logging
import os
import sys
import time

logger = logging.getLogger("gprompt")

STRICT_ENV = "GPROMPT_DEBUG"
_TRUTHY = {"1", "true", "yes", "on", "si", "sí"}


def strict_mode() -> bool:
    """True si el modo estricto está activado vía GPROMPT_DEBUG.

    Se consulta en caliente (no se cachea) para que los tests puedan
    activarlo/desactivarlo con monkeypatch sobre os.environ.
    """
    return os.getenv(STRICT_ENV, "").strip().lower() in _TRUTHY


@contextlib.contextmanager
def silent(operation: str, level: int = logging.DEBUG):
    """Context manager: captura excepción, la loggea pero NO la propaga.

    En modo estricto (GPROMPT_DEBUG) la re-lanza tras loggearla.
    """
    try:
        yield
    except Exception as e:
        logger.log(level, f"[silent] {operation}: {e}")
        if strict_mode():
            raise


def _silent(callable_fn, operation: str, level: int = logging.DEBUG):
    """Ejecuta callable_fn y captura excepciones silenciosamente. Retorna None si falla.

    En modo estricto (GPROMPT_DEBUG) la re-lanza tras loggearla.
    """
    try:
        return callable_fn()
    except Exception as e:
        logger.log(level, f"[silent] {operation}: {e}")
        if strict_mode():
            raise
        return None


def silent_call(operation: str, default=None, level: int = logging.DEBUG):
    """Decorador: captura excepción, la loggea pero NO la propaga, retorna default.

    En modo estricto (GPROMPT_DEBUG) la re-lanza tras loggearla.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.log(level, f"[silent] {operation}: {e}")
                if strict_mode():
                    raise
                return default
        return wrapper
    return decorator


def log_operation(operation: str, level: int = logging.INFO):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.log(level, f"[OP] {operation} → inicio")
            t0 = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - t0
                logger.log(level, f"[OP] {operation} → ok ({elapsed:.2f}s)")
                return result
            except Exception as e:
                elapsed = time.time() - t0
                logger.error(f"[OP] {operation} → error ({elapsed:.2f}s): {e}")
                raise
        return wrapper
    return decorator


class ReRaiseSilentFilter(logging.Filter):
    """Filtro de logging que re-lanza la excepción viva al ver un `[silent]`.

    Los ~336 catches inline del proyecto hacen `logger.debug(f"[silent] {e}")`
    DENTRO del bloque `except`. Cuando ese log se procesa, la excepción sigue
    activa en `sys.exc_info()`, así que un filtro instalado en los handlers
    puede re-lanzarla — sin tocar ninguno de los 336 call sites.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:
            return True
        if "[silent]" in msg:
            exc_type, exc, _tb = sys.exc_info()
            if exc is not None:
                raise exc
        return True


def install_strict_silent_guard(logger_name: str = "gprompt") -> bool:
    """Activa la red anti-bugs si GPROMPT_DEBUG está puesto.

    Baja el nivel a DEBUG (para que los `logger.debug("[silent] ...")` lleguen
    a los handlers) e instala `ReRaiseSilentFilter` en los handlers del root
    y del logger del proyecto. Idempotente. Devuelve True si quedó instalada.
    """
    if not strict_mode():
        return False

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    logging.getLogger(logger_name).setLevel(logging.DEBUG)

    handlers = list(root.handlers) + list(logging.getLogger(logger_name).handlers)
    for h in handlers:
        if not any(isinstance(f, ReRaiseSilentFilter) for f in h.filters):
            h.addFilter(ReRaiseSilentFilter())
    return True
