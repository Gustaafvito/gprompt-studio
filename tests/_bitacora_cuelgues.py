"""Dónde deja su rastro el cortafuegos de tiempo de conftest.py.

ANTES: un único `tests_colgados.log` en la carpeta del usuario, abierto en
modo "a" y con una línea por test. Medido el 24-sep-2026: 687 KB y 6807
líneas tras unas pocas tiradas, y NINGÚN volcado dentro. Sólo migas, unas
1660 por tirada y sin techo: la misma basura en casa del usuario que el
arreglo de los borradores acababa de quitar.

AHORA cada proceso escribe su propio fichero y lo BORRA al terminar si no
guarda ningún volcado. Un cuelgue aborta el proceso (`dump_traceback_later`
con `exit=True`), así que la limpieza no llega a ejecutarse y el fichero se
queda justo cuando hace falta. Que sea uno por proceso evita además que dos
tiradas simultáneas —hay sesiones en paralelo en worktrees— se pisen.
"""
import os
import time

CARPETA = os.path.join(os.path.expanduser("~"), ".arquitecto_prompts")

# Todos los volcados de faulthandler la llevan, por tiempo o por fallo fatal:
#   Timeout (0:05:00)!
#   Thread 0x00002f40 (most recent call first):
FIRMA_DE_VOLCADO = "most recent call first"


def ruta_nueva(carpeta=CARPETA, pid=None, ahora=None):
    """Un fichero por proceso, con fecha para saber de qué tirada es."""
    marca = time.strftime("%Y%m%d-%H%M%S", time.localtime(ahora))
    return os.path.join(
        carpeta, f"tests_colgados-{marca}-{pid or os.getpid()}.log")


def hay_volcado(ruta):
    try:
        with open(ruta, encoding="utf-8", errors="replace") as fh:
            return FIRMA_DE_VOLCADO in fh.read()
    except OSError:
        return False


def cerrar(fh, ruta):
    """Cierra la bitácora y la borra si no guarda nada que leer.

    Devuelve True si la conserva. Nunca lanza: limpiar no puede convertirse
    en un fallo de la suite.
    """
    try:
        fh.close()
    except Exception:
        pass
    if hay_volcado(ruta):
        return True
    try:
        os.remove(ruta)
    except OSError:
        pass
    return False
