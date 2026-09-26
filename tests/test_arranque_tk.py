"""El reintento del arranque de Tcl: qué reintenta y qué NO.

Estos candados existen porque el reintento es la parte peligrosa del arreglo,
y se puede fallar por los dos lados:

  • de MENOS: el primer intento enumeraba la firma de un mensaje concreto y
    el fallo volvió a tumbar la suite con otro mensaje de la misma avería;
  • de MÁS: esto envuelve también a `ArquitectoApp()`, que monta media
    aplicación. Si un TclError de uno de sus widgets contara, se repetiría
    la inicialización entera cuatro veces y una regresión de verdad saldría
    disfrazada de avería de Tcl.

Los dos casos con traza AUTÉNTICA están en TestSoloElNacimientoDelInterprete:
una excepción fabricada a mano no puede demostrar por sí sola nada sobre un
filtro que precisamente mira la traza.
"""
import tkinter
import warnings

import pytest

from tests._arranque_tk import (
    crear_con_reintentos,
    es_arranque_reintentable,
    es_falta_de_entorno,
    nace_el_interprete,
)

# Los DOS mensajes reales vistos el 24-sep-2026, los dos "init.tcl no cargó".
NO_SE_PUDO_LEER = (
    "Can't find a usable init.tcl in the following directories: \n"
    r"    {C:\Python310\tcl\tcl8.6}"
    "\n\n"
    'couldn\'t read file "C:/Python310/tcl/tcl8.6/init.tcl": No error\n'
)
FALTA_EL_PROC = 'invalid command name "tcl_findLibrary"'
# Lo que sale en CI headless. NO se debe reintentar.
SIN_DISPLAY = "no display name and no $DISPLAY environment variable"

# Marco con el MISMO fichero y función que el fallo real. En el fallo de
# verdad la hoja de la traza es `tkinter/__init__.py::__init__` porque quien
# revienta es `_tkinter.create`, que es C y no deja marco propio.
#
# Subclasear Tk aquí NO vale: la hoja saldría en este fichero de tests y la
# prueba pasaría por el motivo equivocado (se intentó, y no reproducía la
# traza real). Por eso se compila el marco con el nombre de fichero y de
# función auténticos.
_FUENTE_DEL_MARCO = (
    "def __init__(self, mensaje):\n"
    "    raise tkinter.TclError(mensaje)\n"
)


def _fallo_naciendo_el_interprete(mensaje):
    """Una TclError con la MISMA forma de traza que el fallo de verdad."""
    espacio = {"tkinter": tkinter}
    exec(compile(_FUENTE_DEL_MARCO, tkinter.__file__, "exec"), espacio)
    # `__new__` da una instancia de Tk sin arrancar ningún intérprete.
    try:
        espacio["__init__"](tkinter.Tk.__new__(tkinter.Tk), mensaje)
    except tkinter.TclError as exc:
        return exc
    raise AssertionError("no lanzó")


class TestElMarcoDePruebaSeParaceAlReal:

    def test_la_hoja_cae_en_tkinter_init(self):
        # Si este andamio deja de parecerse al fallo real, los tests de
        # abajo dejarían de probar lo que dicen probar.
        exc = _fallo_naciendo_el_interprete("lo que sea")
        tb = exc.__traceback__
        hoja = None
        while tb is not None:
            hoja = tb.tb_frame
            tb = tb.tb_next
        assert hoja.f_code.co_filename == tkinter.__file__
        assert hoja.f_code.co_name == "__init__"
        assert isinstance(hoja.f_locals.get("self"), tkinter.Tk)


class TestQueSeReintenta:

    @pytest.mark.parametrize("mensaje", [NO_SE_PUDO_LEER, FALTA_EL_PROC],
                             ids=["no_se_pudo_leer", "falta_tcl_findLibrary"])
    def test_los_dos_fallos_reales_se_reintentan(self, mensaje):
        # Si alguno deja de reintentarse, vuelven los 62 errores.
        assert es_arranque_reintentable(_fallo_naciendo_el_interprete(mensaje))

    def test_un_tclerror_desconocido_del_arranque_se_reintenta(self):
        # Lista NEGRA a propósito: la misma avería ya salió con dos mensajes,
        # así que lo desconocido se reintenta en vez de darse por perdido.
        assert es_arranque_reintentable(
            _fallo_naciendo_el_interprete("algo raro de Tcl"))

    def test_la_falta_de_display_no_se_reintenta(self):
        exc = _fallo_naciendo_el_interprete(SIN_DISPLAY)
        assert es_falta_de_entorno(exc)
        assert not es_arranque_reintentable(exc)


class TestSoloElNacimientoDelInterprete:
    """La propiedad que hace seguro envolver ArquitectoApp(). Trazas reales."""

    def test_el_arranque_fallido_de_verdad_cuenta(self, exige_tk, monkeypatch):
        # Con TCL_LIBRARY en un sitio que no existe, Tcl no encuentra su
        # init.tcl y revienta CREANDO el intérprete: traza auténtica.
        monkeypatch.setenv("TCL_LIBRARY", r"C:\no\existe\tcl8.6")
        with pytest.raises(tkinter.TclError) as info:
            tkinter.Tk()
        assert nace_el_interprete(info.value)

    def test_un_tclerror_de_widget_no_cuenta(self, tk_root):
        # Mismo fichero y misma función que el de arriba; lo que cambia es
        # que `self` no es un Tk.
        with pytest.raises(tkinter.TclError) as info:
            tkinter.Label(tk_root, bg="#zzzzzz")
        assert not nace_el_interprete(info.value)
        assert not es_arranque_reintentable(info.value)

    def test_un_widget_roto_no_repite_la_inicializacion(self, tk_root):
        # Lo que de verdad se protege: que ArquitectoApp no se monte entera
        # cuatro veces porque un widget suyo lance TclError.
        intentos = []

        def fabrica():
            intentos.append(1)
            tkinter.Label(tk_root, bg="#zzzzzz")

        with pytest.raises(tkinter.TclError):
            crear_con_reintentos(fabrica, dormir=lambda _s: None)
        assert len(intentos) == 1, "un widget roto gastó reintentos"

    @pytest.mark.parametrize("exc", [
        AttributeError("'ArquitectoApp' object has no attribute 'store'"),
        ImportError("No module named 'modules.loquesea'"),
        RuntimeError("el worker no levanto"),
    ], ids=["atributo", "import", "runtime"])
    def test_una_regresion_de_la_app_no_se_reintenta(self, exc):
        assert not es_arranque_reintentable(exc)


class TestElReintento:

    def test_se_recupera_si_el_segundo_intento_va(self):
        intentos = []

        def fabrica():
            intentos.append(1)
            if len(intentos) < 2:
                raise _fallo_naciendo_el_interprete(NO_SE_PUDO_LEER)
            return "root"

        with pytest.warns(RuntimeWarning, match="no arrancó"):
            assert crear_con_reintentos(
                fabrica, dormir=lambda _s: None) == "root"
        assert len(intentos) == 2

    def test_si_va_a_la_primera_no_avisa_de_nada(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # cualquier aviso sería un fallo
            assert crear_con_reintentos(lambda: "root") == "root"

    def test_la_falta_de_display_falla_al_primer_intento(self):
        intentos = []

        def fabrica():
            intentos.append(1)
            raise _fallo_naciendo_el_interprete(SIN_DISPLAY)

        with pytest.raises(tkinter.TclError, match="DISPLAY"):
            crear_con_reintentos(fabrica, dormir=lambda _s: None)
        assert len(intentos) == 1, "la falta de display gastó reintentos"

    def test_si_falla_siempre_acaba_relanzando_el_error_real(self):
        intentos = []

        def fabrica():
            intentos.append(1)
            raise _fallo_naciendo_el_interprete(FALTA_EL_PROC)

        with pytest.warns(RuntimeWarning):
            with pytest.raises(tkinter.TclError, match="tcl_findLibrary"):
                crear_con_reintentos(
                    fabrica, intentos=3, dormir=lambda _s: None)
        assert len(intentos) == 3, "no agotó los intentos, o hizo de más"

    def test_espera_mas_en_cada_intento(self):
        esperas = []

        def fabrica():
            raise _fallo_naciendo_el_interprete(FALTA_EL_PROC)

        with pytest.warns(RuntimeWarning):
            with pytest.raises(tkinter.TclError):
                crear_con_reintentos(fabrica, intentos=3, espera_base=0.5,
                                     dormir=esperas.append)
        assert esperas == [0.5, 1.0], esperas
