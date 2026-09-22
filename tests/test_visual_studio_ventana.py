"""La ventana de «Crear desde imágenes» se construye y se cierra sin romperse.

La beta visual 9.1 llegó con 61 tests, pero todos apuntan a
`modules/visual_brief` —la lógica del brief— y ninguno construye la ventana.
Eso deja sin vigilar justo la parte que más se rompe en este proyecto: un
widget mal parametrizado, un `tr()` que no existe o un color escrito a mano
no fallan al importar, fallan al abrir, y para entonces ya está publicado.

Estos candados son deliberadamente superficiales: no prueban qué hace la
ventana, prueban que ABRE. Es el equivalente a encenderla una vez. Si mañana
alguien toca `visual_studio.py` y deja una llamada rota en el constructor,
esto lo dice en dos segundos en vez de en un issue.

`open_visual_studio` además promete no duplicar ventanas: si ya hay una, la
trae al frente en vez de abrir otra. Eso sí es comportamiento, y va aquí
porque no se puede comprobar sin una ventana real.
"""
import inspect

import pytest

ctk = pytest.importorskip("customtkinter")

from modules.visual_studio import VisualStudio, open_visual_studio


def _bombear(root, ms=120):
    """Deja correr los callbacks diferidos antes de mirar el resultado."""
    root.after(ms, root.quit)
    root.mainloop()


@pytest.fixture()
def root(tk_root):
    # Estado limpio: sin ventanas visuales colgando de un test anterior.
    for w in list(tk_root.winfo_children()):
        if isinstance(w, VisualStudio):
            try:
                w.destroy()
            except Exception:
                pass
    if hasattr(tk_root, "_visual_studio"):
        delattr(tk_root, "_visual_studio")
    return tk_root


class TestLaVentanaSeAbre:

    def test_se_construye_sin_error(self, root):
        v = VisualStudio(root)
        _bombear(root)
        assert v.winfo_exists()
        v.destroy()

    def test_tiene_contenido(self, root):
        # Una ventana que se construye pero sale vacía pasaría el test de
        # arriba y seria igual de inútil.
        v = VisualStudio(root)
        _bombear(root)
        assert len(v.winfo_children()) > 0, "la ventana se abre vacía"
        v.destroy()

    def test_se_cierra_sin_dejar_rastro(self, root):
        v = VisualStudio(root)
        _bombear(root)
        v.destroy()
        _bombear(root)
        assert not v.winfo_exists()


class TestNoSeDuplica:
    """`open_visual_studio` guarda la ventana en `app._visual_studio` y la
    reutiliza. Sin esto, cada clic en el botón abriría una ventana más."""

    def test_el_segundo_open_devuelve_la_misma(self, root):
        primera = open_visual_studio(root)
        _bombear(root)
        segunda = open_visual_studio(root)
        _bombear(root)
        assert primera is segunda
        primera.destroy()

    def test_tras_cerrarla_se_abre_una_nueva(self, root):
        primera = open_visual_studio(root)
        _bombear(root)
        primera.destroy()
        _bombear(root)
        segunda = open_visual_studio(root)
        _bombear(root)
        assert segunda is not primera
        assert segunda.winfo_exists()
        segunda.destroy()


class TestLaVistaPreviaSaleDelante:
    """22-sep-2026, punto 1 del repaso de ChatGPT sobre `fd9df53`.

    `preview_reference()` abría un `ctk.CTkToplevel` pelado y lo subía con un
    `lift()` suelto. Eso NO basta en Windows, y está medido en
    `tests/test_ventana_al_frente.py`: CustomTkinter hace withdraw()+deiconify()
    para pintar la barra de título, y ese deiconify llega ~800 ms DESPUÉS del
    lift, así que la ventana acaba detrás de la que tiene el foco.

    La cura del proyecto es `GPromptWindow`, que vuelve a subirla tras cada
    deiconify, pone el topmost 250 ms y lo suelta —prioridad temporal, no
    permanente— y deja intactos los botones de minimizar y maximizar: su
    `transient()` es un no-op a propósito, porque en Windows transient los
    esconde.
    """

    def test_la_vista_previa_usa_la_ventana_del_proyecto(self):
        """Hereda el foco de GPromptWindow, pero no su deduplicación por título.

        La segunda mitad importa tanto como la primera: usar GPromptWindow tal
        cual hacía que dos imágenes llamadas igual compartieran ventana. La
        identidad de una vista previa es su referencia, no su título.
        """
        from modules.gprompt_window import GPromptWindow as GW
        from modules.visual_studio import _VentanaPrevia

        fuente = inspect.getsource(VisualStudio.preview_reference)
        assert "_VentanaPrevia(" in fuente, (
            "con un CTkToplevel pelado la vista previa se abre DETRÁS")
        assert "ctk.CTkToplevel(" not in fuente
        assert issubclass(_VentanaPrevia, GW), (
            "sin heredar de GPromptWindow se pierde el arreglo del foco")
        assert _VentanaPrevia.title is not GW.title, (
            "si no sobrescribe title(), vuelve la deduplicación por título")

    def test_ya_no_se_apoya_en_un_lift_suelto(self):
        fuente = inspect.getsource(VisualStudio.preview_reference)
        assert "window.lift()" not in fuente, (
            "el lift() suelto llega antes que el deiconify de CTk y no sirve")

    def test_el_topmost_es_temporal(self):
        # Una ventana clavada encima de todo es peor que una detrás: no puedes
        # trabajar con la app mientras la miras.
        from modules.gprompt_window import GPromptWindow as GW
        fuente = inspect.getsource(GW._bring_to_front)
        assert '"-topmost", True' in fuente
        assert "after(250" in fuente and '"-topmost", False' in fuente

    def test_conserva_minimizar_y_maximizar(self):
        # transient() en Windows esconde esos botones; GPromptWindow lo
        # neutraliza a propósito.
        from modules.gprompt_window import GPromptWindow as GW
        fuente = inspect.getsource(GW.transient)
        assert '"-toolwindow", False' in fuente


class TestLaVistaPreviaEnUnaVentanaDeVerdad:

    def test_se_abre_y_es_una_gprompt_window(self, root, tmp_path):
        from PIL import Image

        from modules.gprompt_window import GPromptWindow as GW
        from modules.visual_brief import MODES, ROLES, Reference

        v = VisualStudio(root)
        _bombear(root)
        v.refs.append(Reference(Image.new("RGB", (40, 30), "blue"),
                                ROLES[0], "prueba.png"))
        v.preview_reference(0)
        _bombear(root, 200)

        previas = [w for w in v.winfo_children() if isinstance(w, GW)]
        assert previas, "no se abrió ninguna ventana de vista previa"
        assert previas[0].winfo_exists()
        assert MODES  # el módulo sigue exponiendo sus identificadores
        for w in previas:
            w.destroy()
        v.destroy()
