"""Abrir URLs en el navegador SIN prestarle nuestro directorio de trabajo.

Reportado por el usuario el 07-sep-2026: al instalar una actualización, el
instalador moría con

    C:\\...\\G-Prompt Studio\\_internal\\VCRUNTIME140.dll
    Ocurrió un error al intentar reemplazar el archivo existente:
    DeleteFile falló; código 5. Acceso denegado.

Diagnóstico (comprobado con Get-Process, no supuesto): chrome.exe y
chrome-native-host.exe tenían CARGADO ese DLL nuestro. Nacieron en el mismo
segundo, hijos de un padre ya desaparecido, y la carpeta de instalación NO
está en el PATH. Solo queda un camino: los lanzó la propia app.

`webbrowser.open()` arranca el navegador como PROCESO HIJO, y un hijo hereda
el directorio de trabajo del padre — que en una instalación normal es la
carpeta de la app. Cuando el navegador necesitó VCRUNTIME140.dll, Windows la
buscó por su orden habitual y la encontró ahí antes que en el sistema. Desde
ese momento el navegador mantiene el archivo abierto y ninguna actualización
puede reemplazarlo.

Le pasó al usuario tras pulsar "🌐 Obtener key" tres veces (Fireworks, Groq,
Mistral). Le pasaría a cualquiera: usa ese botón y la siguiente actualización
le falla con un error incomprensible.

Arreglo: lanzar el navegador desde un directorio neutro. La carpeta personal
del usuario siempre existe y no contiene DLLs nuestras.
"""
import logging
import os
import webbrowser
from pathlib import Path

logger = logging.getLogger("gprompt")


def _directorio_neutro() -> str | None:
    """Una carpeta que exista y donde no vivan DLLs de la app."""
    for candidata in (Path.home(), Path(os.environ.get("TEMP", "")) if os.environ.get("TEMP") else None):
        try:
            if candidata and candidata.is_dir():
                return str(candidata)
        except Exception as e:
            logger.debug(f"[silent] directorio neutro: {e}")
    return None


def abrir_url(url: str) -> bool:
    """Abre `url` en el navegador. Devuelve False si no se pudo.

    Se cambia el directorio de trabajo SOLO durante el arranque del navegador
    y se restaura siempre, incluso si algo falla: el resto de la app usa rutas
    relativas y no puede quedarse en otra carpeta.
    """
    if not url:
        return False
    previo = None
    neutro = _directorio_neutro()
    try:
        if neutro:
            previo = os.getcwd()
            os.chdir(neutro)
    except Exception as e:
        logger.debug(f"[silent] no se pudo cambiar de directorio: {e}")
        previo = None
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        logger.warning(f"No se pudo abrir {url}: {e}")
        return False
    finally:
        if previo:
            try:
                os.chdir(previo)
            except Exception as e:
                logger.debug(f"[silent] no se pudo restaurar el directorio: {e}")
