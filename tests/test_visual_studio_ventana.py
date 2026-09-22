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
