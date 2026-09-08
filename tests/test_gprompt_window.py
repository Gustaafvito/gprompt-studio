"""Single-instance por título en GPromptWindow.

Crea ventanas reales de CustomTkinter; si el entorno no tiene display
(TclError al iniciar Tk), los tests se saltan.
"""
import pytest

ctk = pytest.importorskip("customtkinter")
from modules.gprompt_window import GPromptWindow


@pytest.fixture(scope="module")
def _root(tk_root):
    # Tk no admite varios roots por proceso, asi que se usa el UNICO de la
    # sesion (conftest). Crear uno aqui chocaba con el de test_panel_lateral
    # y test_barrido_ui segun el orden, y el choque se veia como un salto
    # "sin display" en vez de como el fallo que era.
    tk_root.title("G-Prompt Studio v1.0")
    yield tk_root


@pytest.fixture()
def root(_root):
    # Estado limpio por test: registro vacío y sin toplevels colgando.
    GPromptWindow._por_titulo.clear()
    for w in list(_root.winfo_children()):
        if isinstance(w, GPromptWindow):
            try:
                w.destroy()
            except Exception:
                pass
    return _root


def _bombear(root, ms=120):
    """Deja correr los callbacks diferidos (incluido el autocierre a 60ms)."""
    root.after(ms, root.quit)
    root.mainloop()


def test_segunda_ventana_mismo_titulo_se_cierra(root):
    w1 = GPromptWindow(root); w1.title("Copiloto")
    w2 = GPromptWindow(root); w2.title("Copiloto")
    _bombear(root)
    assert w1.winfo_exists()
    assert not w2.winfo_exists()
    assert GPromptWindow._por_titulo.get("Copiloto") is w1


def test_titulos_distintos_coexisten(root):
    a = GPromptWindow(root); a.title("Dashboard")
    b = GPromptWindow(root); b.title("Glosario")
    _bombear(root)
    assert a.winfo_exists() and b.winfo_exists()


def test_ventanas_sin_titulo_no_deduplican(root):
    # Toasts/splash: sin title() propio → heredan el del root → NO dedup.
    t1 = GPromptWindow(root)
    t2 = GPromptWindow(root)
    t3 = GPromptWindow(root)
    _bombear(root)
    assert all(w.winfo_exists() for w in (t1, t2, t3))


def test_reabrir_tras_cerrar(root):
    w1 = GPromptWindow(root); w1.title("Datos")
    _bombear(root, 80)
    w1.destroy()
    _bombear(root, 40)
    assert GPromptWindow._por_titulo.get("Datos") is None
    w2 = GPromptWindow(root); w2.title("Datos")
    _bombear(root)
    assert w2.winfo_exists()
