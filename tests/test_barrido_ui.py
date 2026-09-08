"""Barrido de UI: que TODAS las ventanas abran y ningún botón quede muerto.

Arranca la aplicación real y abre una a una todas las ventanas secundarias,
comprobando que se construyen y que cada CTkButton conserva su callback. Es lo
que de verdad se rompe al refactorizar: un botón que se queda sin `command`
sigue pintándose igual, pero al pulsarlo no pasa nada y nadie se entera.

NO se pulsa nada: hacerlo dispararía llamadas a la API (créditos del usuario) y
escrituras en disco. Aquí se verifica construcción y cableado.

Como crea ventanas reales, se salta entero si el entorno no tiene display.
"""
import tkinter
from tkinter import filedialog, messagebox

import pytest

ctk = pytest.importorskip("customtkinter")

# Ventanas de la app: (módulo, función, argumentos extra además de `app`)
VENTANAS = [
    ("avatar_ui", "abrir_avatar_window", ()),
    ("bienvenida", "abrir_bienvenida", ()),
    ("command_palette", "abrir_command_palette", ()),
    ("glosario", "abrir_glosario", ()),
    ("style_guide", "abrir_guia_estilos", ()),
    ("tutorial", "abrir_tutorial", ()),
    ("windows", "abrir_personajes", ()),
    ("windows", "abrir_loras", ()),
    ("windows", "abrir_batch_variables", ()),
    ("windows", "abrir_batch", ()),
    ("windows", "abrir_lista", ("favoritos", "Favoritos", "#3b82f6")),
]


@pytest.fixture(scope="module")
def app(monkeypatch_module, exige_tk):
    """La aplicación real, con todo lo que puede BLOQUEAR neutralizado."""
    from app import ArquitectoApp
    # Se salta SOLO si el entorno no tiene Tk (CI headless). Si Tk funciona,
    # que la app no arranque es un FALLO y tiene que verse: cazarlo aqui
    # convertia una regresion de arranque en un salto silencioso.
    a = ArquitectoApp()
    a.update()
    a.update_idletasks()
    yield a
    try:
        a.destroy()
    except Exception:
        pass


@pytest.fixture(scope="module")
def monkeypatch_module():
    """Silencia diálogos modales: sin esto el barrido se queda colgado."""
    mp = pytest.MonkeyPatch()
    for nombre, valor in (("showinfo", None), ("showwarning", None),
                          ("showerror", None), ("askyesno", False),
                          ("askokcancel", False), ("askquestion", "no")):
        mp.setattr(messagebox, nombre, lambda *a, _v=valor, **k: _v)
    for nombre in ("askopenfilename", "asksaveasfilename", "askdirectory"):
        mp.setattr(filedialog, nombre, lambda *a, **k: "")
    mp.setattr(tkinter.Misc, "wait_window", lambda self, w=None: None)
    mp.setattr(tkinter.Misc, "grab_set", lambda self: None)
    mp.setattr(tkinter.Misc, "grab_release", lambda self: None)
    yield mp
    mp.undo()


def _descendientes(widget):
    acc = []

    def _rec(w):
        for h in w.winfo_children():
            acc.append(h)
            _rec(h)

    _rec(widget)
    return acc


def _botones_sin_accion(widget):
    """Textos de los CTkButton que se quedaron sin callback."""
    sin = []
    for b in _descendientes(widget):
        if not isinstance(b, ctk.CTkButton):
            continue
        if not callable(getattr(b, "_command", None)):
            try:
                sin.append(b.cget("text"))
            except Exception:
                sin.append("?")
    return sin


def _abrir(app, modname, fname, extra):
    """Abre una ventana y devuelve las Toplevel nuevas que haya creado."""
    antes = {id(w) for w in app.winfo_children()
             if isinstance(w, tkinter.Toplevel)}
    mod = __import__(f"modules.{modname}", fromlist=[fname])
    getattr(mod, fname)(app, *extra)
    app.update()
    app.update_idletasks()
    return [w for w in app.winfo_children()
            if isinstance(w, tkinter.Toplevel) and id(w) not in antes]


@pytest.mark.slow
class TestVentanas:

    @pytest.mark.parametrize("modname,fname,extra", VENTANAS,
                             ids=[v[1] for v in VENTANAS])
    def test_la_ventana_abre_sin_romperse(self, app, modname, fname, extra):
        nuevas = _abrir(app, modname, fname, extra)
        try:
            assert nuevas, f"{fname} no creó ninguna ventana"
        finally:
            for w in nuevas:
                try:
                    w.destroy()
                except Exception:
                    pass
            app.update()

    @pytest.mark.parametrize("modname,fname,extra", VENTANAS,
                             ids=[v[1] for v in VENTANAS])
    def test_la_ventana_no_tiene_botones_muertos(self, app, modname, fname, extra):
        nuevas = _abrir(app, modname, fname, extra)
        try:
            sin = [t for w in nuevas for t in _botones_sin_accion(w)]
            assert not sin, f"{fname}: botones sin acción -> {sin}"
        finally:
            for w in nuevas:
                try:
                    w.destroy()
                except Exception:
                    pass
            app.update()


@pytest.mark.slow
class TestVentanaPrincipal:

    def test_no_hay_botones_muertos(self, app):
        sin = _botones_sin_accion(app)
        assert not sin, f"botones sin acción en la ventana principal: {sin}"

    def test_tiene_una_cantidad_razonable_de_botones(self, app):
        """Si esto cae en picado es que media UI dejó de construirse."""
        botones = [w for w in _descendientes(app)
                   if isinstance(w, ctk.CTkButton)]
        assert len(botones) >= 50, f"solo {len(botones)} botones"
