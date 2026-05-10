"""Logging utilities — decoradores y helpers para logging estructurado."""
import functools
import logging
import time

logger = logging.getLogger("gprompt")


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
