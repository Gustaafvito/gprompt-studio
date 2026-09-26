r"""Crear el intérprete de Tcl/Tk aguantando un arranque que falla de paso.

QUÉ SE OBSERVÓ (24-sep-2026, midiendo en bucle la suite completa)
La suite se cayó dos veces con 62 errores de setup —todos el MISMO error,
porque de la fixture de sesión `tk_root` cuelgan 62 tests y pytest cachea su
excepción y la relanza en cada uno—. Las dos veces falló al crear el
intérprete de Tcl, y el mensaje NO fue el mismo:

    1) Can't find a usable init.tcl in the following directories:
       {...\Python310\tcl\tcl8.6}
       couldn't read file "...\tcl8.6\init.tcl": No error

    2) invalid command name "tcl_findLibrary"

Son la misma avería vista por dos lados: el `init.tcl` de Tcl no se cargó.
En el primer caso ni se pudo leer —el `No error` es errno 0, con el fichero
intacto y legible después—; en el segundo se cargó a medias y faltó
`tcl_findLibrary`, que es un proc que define ese mismo fichero.

QUÉ NO SE SABE
No está demostrado QUÉ impide la lectura. Hay indicios de que es transitorio
y no un Tcl mal instalado —el fichero está en su sitio y se lee bien antes y
después, y en la tirada 1 otro intérprete del mismo proceso lo había leído
sin problema segundos antes—, pero la causa de fondo sigue sin identificar.
No se atribuye a ningún culpable concreto: lo que haya escrito aquí sobre
antivirus o disco en versiones anteriores de este fichero era una suposición
sin medir, y se ha quitado.

QUÉ ARREGLA ESTO Y QUÉ NO
Reintentar mitiga los arranques que FALLAN con una excepción. NO arregla el
caso en que el arranque se QUEDA COLGADO, que también se ha observado (una
tirada bloqueada 22 minutos en este mismo punto, con 45 s de CPU: esperando
E/S, no girando). Para eso está el cortafuegos de tiempo de `conftest.py`,
que vuelca la pila y aborta; el cuelgue en sí sigue sin resolver.

REINTENTAR NO ES TAPAR
  • la falta de display se relanza en el PRIMER intento, así que CI headless
    sigue saltando igual y al momento;
  • sólo cuenta el fallo que ocurre NACIENDO el intérprete (ver
    `nace_el_interprete`), no cualquier TclError: esto envuelve también a
    `ArquitectoApp()`, y un TclError de uno de sus widgets no puede provocar
    que se repita la inicialización entera de la aplicación;
  • si la avería es real, los cuatro intentos fallan y la suite lo dice, con
    el error de verdad y un log aparte;
  • cuando un reintento SALVA la tirada se emite un warning, para que no se
    vuelva invisible.
"""
import os
import time
import tkinter
import warnings

# Falta de entorno gráfico: permanente. En CI headless es lo normal y tiene
# que saltar YA, sin gastar reintentos.
_SIN_ENTORNO = (
    "no display name",
    "display environment variable",
    "couldn't connect to display",
    "could not open display",
)

INTENTOS = 4
ESPERA_BASE = 0.4


def es_falta_de_entorno(exc):
    """¿Es "aquí no hay ventanas"? Eso no se reintenta nunca."""
    texto = str(exc).lower()
    return any(senal in texto for senal in _SIN_ENTORNO)


def nace_el_interprete(exc):
    r"""¿Reventó CREANDO el intérprete, o más adentro, montando widgets?

    Se mira la TRAZA y no el mensaje, por dos razones. La primera es que la
    misma avería ya salió con dos mensajes distintos, así que enumerar
    mensajes es perseguir variantes. La segunda, y más importante, es que
    esto envuelve también a `ArquitectoApp()`, que no es un root pelado:
    monta la aplicación entera. Si un TclError de cualquiera de sus widgets
    contara como reintentable, se repetiría TODA la inicialización de la app
    cuatro veces y una regresión de verdad saldría disfrazada de avería de
    Tcl —justo lo contrario de lo que promete test_barrido_ui.py.

    Medido con las dos trazas de VERDAD (TCL_LIBRARY apuntando a un sitio
    que no existe, contra un color mal escrito en un Label):

        arranque  hoja=tkinter/__init__.py::__init__  self es Tk  -> sí
        widget    hoja=tkinter/__init__.py::__init__  self NO Tk  -> no

    Las dos acaban en la MISMA función; lo que las separa es quién se está
    construyendo. (`self.tk` no sirve para distinguirlas: ya está asignado
    cuando falla el `source` del init.tcl.)
    """
    tb = exc.__traceback__
    hoja = None
    while tb is not None:
        hoja = tb.tb_frame
        tb = tb.tb_next
    if hoja is None:
        return False
    ruta = os.path.normcase(hoja.f_code.co_filename)
    if hoja.f_code.co_name != "__init__":
        return False
    if os.path.basename(ruta) != "__init__.py":
        return False
    if os.path.basename(os.path.dirname(ruta)) != "tkinter":
        return False
    return isinstance(hoja.f_locals.get("self"), tkinter.Tk)


def es_arranque_reintentable(exc):
    """Sólo el nacimiento del intérprete, y nunca la falta de entorno."""
    return (isinstance(exc, tkinter.TclError)
            and nace_el_interprete(exc)
            and not es_falta_de_entorno(exc))


def crear_con_reintentos(fabrica, intentos=INTENTOS, espera_base=ESPERA_BASE,
                         dormir=time.sleep):
    """Llama a `fabrica()` reintentando si el arranque de Tcl falla de paso.

    `dormir` es inyectable para poder probar esto sin esperas reales.
    """
    for intento in range(1, intentos + 1):
        try:
            return fabrica()
        except Exception as exc:
            if not es_arranque_reintentable(exc) or intento == intentos:
                raise
            warnings.warn(
                f"El intérprete de Tcl no arrancó (intento {intento} de "
                f"{intentos}); se reintenta. Si esto sale a menudo, conviene "
                f"averiguar qué impide leer la instalación de Tcl mientras "
                f"corren los tests. {type(exc).__name__}: {exc}"
                .replace("\n", " ")[:300],
                RuntimeWarning, stacklevel=2,
            )
            dormir(espera_base * intento)
    # Inalcanzable: el último intento relanza.
    raise AssertionError("crear_con_reintentos salió del bucle sin resultado")
