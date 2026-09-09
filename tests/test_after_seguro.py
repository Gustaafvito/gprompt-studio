"""`app.after()` no debe reventar si la ventana ya se cerró.

Hay ~175 llamadas a `app.after(0, ...)` desde hilos de fondo: así vuelve el
trabajo pesado al hilo de Tk para pintar el resultado. Si el usuario cierra la
ventana ANTES de que ese trabajo termine, Tk lanza "main thread is not in main
loop" y el log se llena de un traceback inútil — no hay nada que pintar porque
ya no hay ventana.

Visto en el log del usuario (04-sep-2026) tras fallar una generación, y
reproducido al cortar a mitad un moodboard largo con LM Studio.
"""
import tkinter

import pytest

ctk = pytest.importorskip("customtkinter")


class _AppFalsa:
    """Reproduce el patrón sin arrancar la app entera (que tarda ~10s)."""

    def __init__(self, excepcion):
        self._excepcion = excepcion
        self.llamadas = 0

    # Imita el after() de Tk, que revienta con la ventana destruida
    def _after_original(self, ms, func=None, *args):
        self.llamadas += 1
        if self._excepcion:
            raise self._excepcion
        return "id-programado"


def _after_seguro(self, ms, func=None, *args):
    """Copia de la lógica de ArquitectoApp.after para probarla aislada."""
    try:
        return self._after_original(ms, func, *args)
    except (RuntimeError, tkinter.TclError):
        return None


class TestAfterSeguro:

    def test_funciona_normal_si_la_ventana_vive(self):
        app = _AppFalsa(None)
        assert _after_seguro(app, 0, lambda: None) == "id-programado"
        assert app.llamadas == 1

    def test_no_revienta_si_la_ventana_ya_no_esta(self):
        """El caso real: 'main thread is not in main loop'."""
        app = _AppFalsa(RuntimeError("main thread is not in main loop"))
        assert _after_seguro(app, 0, lambda: None) is None

    def test_tambien_traga_el_TclError(self):
        app = _AppFalsa(tkinter.TclError("application has been destroyed"))
        assert _after_seguro(app, 0, lambda: None) is None

    def test_no_se_traga_otros_errores(self):
        """Un fallo distinto SÍ debe salir: no queremos ocultar bugs."""
        app = _AppFalsa(ValueError("algo raro de verdad"))
        with pytest.raises(ValueError):
            _after_seguro(app, 0, lambda: None)


class TestLaAppLoImplementa:

    def test_arquitecto_app_define_su_propio_after(self):
        """Candado: si alguien quita el override, el log vuelve a ensuciarse."""
        from app import ArquitectoApp
        assert "after" in vars(ArquitectoApp), \
            "ArquitectoApp debe sobrescribir after() para tragarse el cierre"

    def test_el_override_documenta_por_que(self):
        from app import ArquitectoApp
        doc = (ArquitectoApp.after.__doc__ or "").lower()
        assert "cerr" in doc or "ventana" in doc


class TestDistingueVentanaVivaDeCerrada:
    """Tragarse el error a secas deja fallos MUDOS.

    Tk lanza el mismo "main thread is not in main loop" cuando la ventana ya
    no existe (rutina al cerrar) y cuando sigue viva y el callback se pierde
    (fallo de verdad: la interfaz deja de actualizarse). El 05-sep-2026 el
    segundo caso costó media hora de diagnóstico porque iba a logger.debug.
    """

    def _widget(self, viva):
        class _W:
            def winfo_exists(self):
                if viva is None:
                    raise RuntimeError("ni eso responde")
                return 1 if viva else 0
        return _W()

    def test_ventana_viva_avisa_en_warning(self, caplog):
        import logging

        from app import _log_after_descartado
        with caplog.at_level(logging.WARNING):
            _log_after_descartado(self._widget(True), RuntimeError("boom"))
        assert any(r.levelno == logging.WARNING for r in caplog.records), \
            "una actualización perdida con la ventana viva NO puede ser muda"
        assert "perdido" in caplog.text.lower()

    def test_ventana_cerrada_se_queda_en_debug(self, caplog):
        import logging

        from app import _log_after_descartado
        with caplog.at_level(logging.DEBUG):
            _log_after_descartado(self._widget(False), RuntimeError("boom"))
        assert not any(r.levelno >= logging.WARNING for r in caplog.records), \
            "cerrar la ventana es rutina: no debe ensuciar el log"

    def test_si_winfo_exists_revienta_se_asume_cerrada(self, caplog):
        import logging

        from app import _log_after_descartado
        with caplog.at_level(logging.DEBUG):
            _log_after_descartado(self._widget(None), RuntimeError("boom"))
        assert not any(r.levelno >= logging.WARNING for r in caplog.records)
