"""
EventBus: Sistema Pub/Sub para desacoplar componentes de G-Prompt Studio.

En lugar de que los mixins se llamen directamente entre sí (acoplamiento),
usan eventos para comunicarse. Esto facilita el mantenimiento y testing.

Uso:
    from modules.event_bus import EventBus
    bus = EventBus()

    # Suscribirse a un evento
    def on_llm_changed(data):
        print(f"LLM cambió a: {data['llm']}")

    bus.on("LLM_CHANGED", on_llm_changed)

    # Emitir un evento
    bus.emit("LLM_CHANGED", {"llm": "deepseek"})

    # Desuscribirse
    bus.off("LLM_CHANGED", on_llm_changed)
"""
import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)


class EventBus:
    """Sistema Pub/Sub para comunicación desacoplada entre componentes."""

    _instance = None

    def __new__(cls):
        """Singleton para tener un solo bus global."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._listeners: dict[str, list[Callable]] = defaultdict(list)
        self._event_history: list[dict] = []
        self._max_history = 100

    def on(self, event: str, callback: Callable) -> None:
        """Suscribe un callback a un evento."""
        if callback not in self._listeners[event]:
            self._listeners[event].append(callback)
            logger.debug(f"[EventBus] Suscrito: {event} -> {callback.__name__}")

    def off(self, event: str, callback: Callable) -> None:
        """Desuscribe un callback de un evento."""
        if callback in self._listeners[event]:
            self._listeners[event].remove(callback)
            logger.debug(f"[EventBus] Desuscrito: {event} -> {callback.__name__}")

    def emit(self, event: str, data: Any = None) -> None:
        """Emite un evento a todos los suscriptores."""
        entry = {"event": event, "data": data, "timestamp": time.time()}
        self._event_history.append(entry)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        logger.debug(f"[EventBus] Emit: {event}")
        for callback in self._listeners.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"[EventBus] Error en {event}->{callback.__name__}: {e}")

    def once(self, event: str, callback: Callable) -> None:
        """Suscribe un callback que se ejecuta solo una vez."""
        def wrapper(data):
            callback(data)
            self.off(event, wrapper)
        self.on(event, wrapper)

    def clear(self, event: str = None) -> None:
        """Limpia suscriptores de un evento o de todos."""
        if event:
            self._listeners[event] = []
        else:
            self._listeners.clear()

    def get_listeners(self, event: str) -> list[Callable]:
        """Devuelve la lista de callbacks suscritos a un evento."""
        return list(self._listeners.get(event, []))

    def get_history(self, limit: int = 10) -> list[dict]:
        """Devuelve el historial de eventos recientes."""
        return self._event_history[-limit:]


import time
