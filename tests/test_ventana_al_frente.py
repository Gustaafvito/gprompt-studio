"""Las ventanas hijas tienen que salir DELANTE de la principal.

Reportado el 06-sep-2026: "cuando abro configurar api keys no me sale delante
del programa principal".

GPromptWindow ya programaba `after(50, _bring_to_front)` en __init__, pero
CustomTkinter hace su propio withdraw()+deiconify() para pintar la barra de
título de Windows, y ese deiconify llega DESPUÉS. Cronología medida sobre el
diálogo de API keys:

    2816 ms  _bring_to_front                  <- nuestro lift()
    3628 ms  _revert_withdraw_...             <- el deiconify de CTk, 800 ms después

Un deiconify posterior al lift deja la ventana detrás de la que tiene el foco.
La solución es volver a subirla después de CADA deiconify, que es el único
momento en que se sabe que CTk terminó de mostrarla.
"""
import inspect

from modules.gprompt_window import GPromptWindow


class TestSeSubeTrasElDeiconifyDeCTk:

    def test_el_revert_withdraw_vuelve_a_subir(self):
        fuente = inspect.getsource(
            GPromptWindow._revert_withdraw_after_windows_set_titlebar_color)
        assert "_bring_to_front" in fuente, (
            "sin esto el deiconify de CTk deja la ventana detrás de la principal")

    def test_sigue_llamando_al_de_customtkinter(self):
        """Saltarse el super() rompería el pintado de la barra de título."""
        fuente = inspect.getsource(
            GPromptWindow._revert_withdraw_after_windows_set_titlebar_color)
        assert "super()._revert_withdraw_after_windows_set_titlebar_color" in fuente

    def test_no_toca_las_duplicadas(self):
        """Una ventana duplicada se autodestruye: subirla petaría."""
        fuente = inspect.getsource(
            GPromptWindow._revert_withdraw_after_windows_set_titlebar_color)
        i_guarda = fuente.find("_es_duplicado")
        i_subir = fuente.find("_bring_to_front")
        assert i_guarda != -1 and i_guarda < i_subir


class TestElArranqueSigueSubiendola:

    def test_init_programa_el_primer_bring_to_front(self):
        fuente = inspect.getsource(GPromptWindow.__init__)
        assert "_bring_to_front" in fuente

    def test_bring_to_front_no_deja_la_ventana_siempre_encima(self):
        """-topmost permanente taparía todo lo demás; debe revertirse."""
        fuente = inspect.getsource(GPromptWindow._bring_to_front)
        assert "topmost" in fuente
        assert "False" in fuente, "el topmost tiene que quitarse después"
