"""Configuración compartida para pytest."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests._arranque_tk import crear_con_reintentos  # noqa: E402

# ── Cortafuegos de tiempo: un test colgado no puede comerse la tarde ───
# El 24-sep-2026 una tirada se quedó BLOQUEADA 22 minutos creando el
# intérprete de Tcl (45 s de CPU en 22 minutos de reloj: esperando E/S, no
# girando). No falló: se quedó ahí. Un cuelgue así no aparece en ningún
# informe, no deja traza y sólo se nota porque el bucle no avanza.
#
# Volcar la pila NO basta: `dump_traceback_later` sin `exit` imprime y deja
# el proceso colgado igual. Por eso van las dos cosas juntas —volcado Y
# abortar—, y el reloj se rearma test a test para que el límite sea por
# EJECUCIÓN y no para la sesión entera.
#
# Esto no arregla el cuelgue, que sigue sin causa identificada: lo convierte
# en una traza que se puede leer.
_LIMITE_POR_TEST = float(os.environ.get("GPROMPT_LIMITE_TEST", "300"))
_BITACORA_CUELGUES = os.path.join(
    os.path.expanduser("~"), ".arquitecto_prompts", "tests_colgados.log")
_VOLCADO = {"fh": None}


def _fichero_de_volcado():
    """Abierto y SIN cerrar: faulthandler escribe en él desde el temporizador."""
    if _VOLCADO["fh"] is None:
        try:
            os.makedirs(os.path.dirname(_BITACORA_CUELGUES), exist_ok=True)
            _VOLCADO["fh"] = open(_BITACORA_CUELGUES, "a", encoding="utf-8")
        except Exception:
            _VOLCADO["fh"] = sys.stderr
    return _VOLCADO["fh"]


def pytest_configure(config):
    if _LIMITE_POR_TEST <= 0:
        return
    import faulthandler
    faulthandler.enable(file=_fichero_de_volcado())


def pytest_runtest_protocol(item, nextitem):
    """Rearma el reloj antes de cada test. Devuelve None: no secuestra nada."""
    if _LIMITE_POR_TEST <= 0:
        return None
    import faulthandler
    fh = _fichero_de_volcado()
    try:
        fh.write(f"\n=== {item.nodeid} ===\n")
        fh.flush()
    except Exception:
        pass
    # exit=True aborta el proceso tras volcar: es lo que convierte el
    # cuelgue en un fallo visible en vez de una espera infinita.
    faulthandler.dump_traceback_later(_LIMITE_POR_TEST, exit=True, file=fh)
    return None


def pytest_runtest_teardown(item, nextitem):
    if _LIMITE_POR_TEST <= 0:
        return
    import faulthandler
    faulthandler.cancel_dump_traceback_later()


@pytest.fixture(autouse=True)
def cleanup_config():
    """Reset configuración global entre tests."""
    yield
    pass


# ── Los borradores de los tests NO van a la carpeta del usuario ───────
# `VisualHistory()` sin argumentos guarda en ~/.arquitecto_prompts/
# visual_drafts, y `VisualStudio.__init__` crea uno por panel. Como los
# tests abren cientos de paneles y el autoguardado salta cada 15 s, cada
# tirada de la suite dejaba carpetas de sesión con proyectos reales dentro
# mezcladas con las del usuario: medido el 24-sep-2026, 369 carpetas y
# 181 MB antes de empezar a medir, y 860 carpetas después de un rato de
# bucles.
#
# Esto NO borra nada de lo que ya hay: sólo manda lo que escriban los tests
# a un temporal que pytest limpia solo.
_RAIZ_BORRADORES = {"ruta": None}


@pytest.fixture(autouse=True)
def borradores_en_temporal(tmp_path_factory, monkeypatch):
    """Redirige SÓLO el destino por defecto; quien pasa `root` manda."""
    from modules.visual_history import VisualHistory
    if _RAIZ_BORRADORES["ruta"] is None:
        _RAIZ_BORRADORES["ruta"] = tmp_path_factory.mktemp("visual_drafts")
    original = VisualHistory.__init__

    def init(self, root=None, keep=12):
        original(self, _RAIZ_BORRADORES["ruta"] if root is None else root,
                 keep)

    monkeypatch.setattr(VisualHistory, "__init__", init)


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
            # Con reintentos por lo mismo que tk_root: si la lectura de
            # init.tcl falla de paso, este sondeo lo interpretaría como
            # "entorno sin Tk" y se SALTARÍAN los 62 tests de interfaz. Un
            # fallo transitorio no puede acabar en 62 saltos silenciosos:
            # eso es exactamente lo que el bloque de arriba dice haber
            # quitado.
            r = crear_con_reintentos(tkinter.Tk)
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


# Dónde se deja la prueba cuando el root no se puede crear. Fuera de la
# carpeta del repo a propósito: sobrevive a un `git clean` y no ensucia el
# árbol de trabajo.
_DIAGNOSTICO = os.path.join(
    os.path.expanduser("~"), ".arquitecto_prompts", "tk_root_fallido.log")


def _dejar_prueba_del_fallo():
    """Escribe POR QUÉ no se pudo crear el root compartido.

    pytest CACHEA la excepción de una fixture de sesión y la vuelve a lanzar
    en cada test que dependa de ella. Como de `tk_root` cuelgan 62 tests, un
    único fallo al crear el root sale en el informe como 62 errores de setup
    idénticos, y ninguno dice qué pasó: el `TclError` de verdad queda
    enterrado bajo la misma traza repetida 62 veces.

    Ese fallo es INTERMITENTE: tardó 18 tiradas completas en aparecer, y fue
    justo este volcado el que dio el texto del TclError y permitió
    identificarlo (ver tests/_arranque_tk.py). Se queda puesto porque la
    avería no está cerrada —el reintento cubre los arranques que fallan con
    excepción, pero el CUELGUE sigue sin causa identificada— y porque sin el
    texto real no se distingue un fallo nuevo de los dos ya conocidos.
    """
    import platform
    import tkinter
    import traceback
    from datetime import datetime

    try:
        os.makedirs(os.path.dirname(_DIAGNOSTICO), exist_ok=True)
        with open(_DIAGNOSTICO, "a", encoding="utf-8") as fh:
            fh.write(f"\n{'=' * 70}\n{datetime.now().isoformat()}\n")
            fh.write(f"python={sys.version.split()[0]} {platform.platform()}\n")
            try:
                import customtkinter as ctk
                fh.write(f"customtkinter={ctk.__version__}\n")
            except Exception as exc:
                fh.write(f"customtkinter=??? ({exc})\n")
            fh.write(f"tcl={tkinter.TclVersion} tk={tkinter.TkVersion}\n")
            # Un root vivo aquí significa que alguien dejó el suyo sin
            # destruir: es la primera sospecha que hay que descartar.
            fh.write(f"_default_root={tkinter._default_root!r}\n")
            fh.write(traceback.format_exc())
    except Exception:
        # Dejar prueba nunca puede ser la causa de un fallo nuevo.
        pass


@pytest.fixture(scope="session")
def tk_root():
    """El único root de la sesión. Compartido por todos los tests de UI."""
    exigir_tk()
    import customtkinter as ctk
    try:
        # El fallo que tumbaba la suite (62 errores, todos el mismo) era Tcl
        # sin poder LEER su init.tcl, con el fichero intacto y errno 0. Ver
        # tests/_arranque_tk.py: sólo se reintenta esa firma.
        r = crear_con_reintentos(ctk.CTk)
    except Exception as exc:
        _dejar_prueba_del_fallo()
        # El mensaje va en la excepción y no solo en el log porque es lo que
        # se ve en el informe: sin esto, los 62 errores no explican nada.
        raise RuntimeError(
            f"No se pudo crear el root compartido de Tk: {type(exc).__name__}: {exc}\n"
            f"Los demás errores de setup de tests de UI son ESTE MISMO fallo "
            f"repetido —pytest cachea la excepción de la fixture de sesión y "
            f"la relanza en cada test que dependa de ella—, no un problema "
            f"distinto por test.\nDetalle del entorno en: {_DIAGNOSTICO}"
        ) from exc
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass
