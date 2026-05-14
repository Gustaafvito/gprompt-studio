"""Logging utilities — decoradores y helpers para logging estructurado."""
import contextlib
import functools
import logging
import time

logger = logging.getLogger("gprompt")


@contextlib.contextmanager
def silent(operation: str, level: int = logging.DEBUG):
    """Context manager: captura excepción, la loggea pero NO la propaga."""
    try:
        yield
    except Exception as e:
        logger.log(level, f"[silent] {operation}: {e}")


def _silent(callable_fn, operation: str, level: int = logging.DEBUG):
    """Ejecuta callable_fn y captura excepciones silenciosamente. Retorna None si falla."""
    try:
        return callable_fn()
    except Exception as e:
        logger.log(level, f"[silent] {operation}: {e}")
        return None


def silent_call(operation: str, default=None, level: int = logging.DEBUG):
    """Decorador: captura excepción, la loggea pero NO la propaga, retorna default."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.log(level, f"[silent] {operation}: {e}")
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
