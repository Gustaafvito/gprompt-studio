"""Las etiquetas en cursiva llevan margen para la inclinación de su última letra.

Barrido del 25-sep-2026: «Versión 1.1.C», «persona rea», «luz natura»…
CTkLabel crea su etiqueta de Tk con padx=0 y la cursiva se sale por la derecha.
"""
import pytest

ctk = pytest.importorskip("customtkinter")

from modules.cursiva import MARGEN_CURSIVA, es_cursiva, instalar_margen_cursiva  # noqa: E402


@pytest.fixture(autouse=True)
def parche():
    original = ctk.CTkLabel.__init__
    instalar_margen_cursiva()
    yield
    ctk.CTkLabel.__init__ = original


def test_detecta_la_cursiva(tk_root):
    assert es_cursiva(ctk.CTkFont(size=10, slant="italic"))
    assert not es_cursiva(ctk.CTkFont(size=10))
    assert es_cursiva(("Arial", 10, "italic"))
    assert not es_cursiva(None)


def test_la_cursiva_gana_margen_y_lo_demas_no(tk_root):
    cursiva = ctk.CTkLabel(tk_root, text="persona real", font=ctk.CTkFont(size=10, slant="italic"))
    normal = ctk.CTkLabel(tk_root, text="persona real", font=ctk.CTkFont(size=10))
    try:
        assert int(str(cursiva._label.cget("padx"))) >= MARGEN_CURSIVA
        assert int(str(normal._label.cget("padx"))) == 0
    finally:
        cursiva.destroy()
        normal.destroy()


def test_un_padx_explicito_se_respeta(tk_root):
    etiqueta = ctk.CTkLabel(tk_root, text="x", padx=10, font=ctk.CTkFont(size=10, slant="italic"))
    try:
        assert int(str(etiqueta._label.cget("padx"))) == 10
    finally:
        etiqueta.destroy()


def test_se_instala_al_arrancar():
    from pathlib import Path
    main = (Path(__file__).resolve().parent.parent / "main.py").read_text(encoding="utf-8")
    assert "instalar_margen_cursiva()" in main
