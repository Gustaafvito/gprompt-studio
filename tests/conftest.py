"""Configuración compartida para pytest."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def cleanup_config():
    """Reset configuración global entre tests."""
    yield
    pass


# ── Tk: un solo root para toda la sesión ──────────────────────────────
# Tk NO admite varios roots por proceso. Tres módulos creaban el suyo
# (test_gprompt_window, test_panel_lateral, test_barrido_ui) y el segundo
# reventaba según el orden y según si el anterior se había destruido del
# todo. Como cada uno cazaba el fallo con un `pytest.skip("sin display")`
# pensado para CI headless, la contención se veía como saltos
# INTERMITENTES: la misma máquina daba 1260 en una tirada y 1256 en la
# siguiente, y una regresión real de interfaz podía pasar por "es que no
# hay display".
#
# Con un root compartido desaparece la contención, y la disponibilidad de
# Tk se decide UNA vez: si el entorno no lo tiene se salta (CI de verdad),
# y si lo tiene, cualquier fallo posterior es un fallo y se ve.
_TK_ESTADO = {"probado": False, "motivo": ""}


def tk_disponible():
    """¿Se puede crear una ventana? Se comprueba una vez por sesión."""
    if not _TK_ESTADO["probado"]:
        _TK_ESTADO["probado"] = True
        try:
            import tkinter
            r = tkinter.Tk()
            r.withdraw()
            r.destroy()
        except Exception as e:
            _TK_ESTADO["motivo"] = str(e)
    return not _TK_ESTADO["motivo"]


def exigir_tk():
    """Salta SOLO si el entorno no tiene Tk. Nunca por un fallo del código."""
    if not tk_disponible():
        pytest.skip(f"entorno sin Tk: {_TK_ESTADO['motivo']}")


@pytest.fixture(scope="session")
def exige_tk():
    """Fixture equivalente a exigir_tk(), para quien no crea el root.

    Como fixture y no como import: `from conftest import ...` no funciona,
    conftest.py no es un modulo importable.
    """
    exigir_tk()


@pytest.fixture(scope="session")
def tk_root():
    """El único root de la sesión. Compartido por todos los tests de UI."""
    exigir_tk()
    import customtkinter as ctk
    r = ctk.CTk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass
