"""El botón de descarga del README tiene que apuntar a un fichero que exista.

10-sep-2026, día uno después de publicar. La API del repo daba **2 estrellas
y 0 descargas**: la gente llegaba, miraba y se iba sin llevarse nada. El
motivo estaba a la vista al abrir el README — la sección «Instalación» está
en la línea 169 de 366, o sea a media pantalla de scroll. Quien entra ve el
título, las insignias, por qué existe y los premios, y en ningún momento ve
*cómo descargarlo*.

La solución fue un enlace directo al instalador justo debajo del selector de
idioma. Pero un enlace directo lleva la versión escrita a mano en la URL
(`releases/download/v1.0.0/GPromptStudio-Setup-1.0.0.exe`), y eso se pudre
en cuanto se publique la 1.1.0: el botón seguiría apuntando a la 1.0.0 y,
peor, a un fichero que la nueva release ya no tiene → 404 en el primer clic
del visitante, que es exactamente el clic que no te puedes permitir fallar.

Estos candados atan la URL a `config.PUBLIC_VERSION` y al nombre que
realmente produce Inno Setup (`OutputBaseFilename=GPromptStudio-Setup-{#MyAppVersion}`
en `installer.iss`), para que subir la versión rompa el test en vez de
romper la descarga.
"""
from pathlib import Path

import config

RAIZ = Path(__file__).resolve().parent.parent
READMES = ("README.md", "README.en.md")

BASE = "https://github.com/Gustaafvito/gprompt-studio/releases/download"
INSTALADOR = f"GPromptStudio-Setup-{config.PUBLIC_VERSION}.exe"
URL_DIRECTA = f"{BASE}/v{config.PUBLIC_VERSION}/{INSTALADOR}"


def _texto(nombre):
    return (RAIZ / nombre).read_text(encoding="utf-8")


class TestLaDescargaSeVeSinHacerScroll:

    def test_los_dos_readmes_llevan_el_enlace_directo(self):
        for n in READMES:
            assert URL_DIRECTA in _texto(n), (
                f"{n} no tiene el enlace directo al instalador de la versión "
                f"{config.PUBLIC_VERSION}. Si acabas de subir la versión, "
                f"actualiza el botón: la URL correcta es {URL_DIRECTA}")

    def test_esta_arriba_del_todo(self):
        # Antes había que bajar a la línea 169 de 366 para encontrarlo. El
        # umbral es generoso a propósito: lo que se vigila es que no vuelva
        # a caerse al fondo, no la maquetación exacta.
        for n in READMES:
            lineas = _texto(n).splitlines()
            i = next(i for i, l in enumerate(lineas) if URL_DIRECTA in l)
            assert i < 30, (
                f"{n}: el botón de descarga está en la línea {i + 1}; "
                f"tiene que verse sin hacer scroll")

    def test_no_queda_ninguna_version_vieja_en_un_enlace_de_descarga(self):
        # Un botón que apunta a una release anterior da 404 y parece
        # abandono. Cualquier `releases/download/...` que no sea el vigente
        # sobra.
        for n in READMES:
            for linea in _texto(n).splitlines():
                if f"{BASE}/" in linea:
                    assert URL_DIRECTA in linea, (
                        f"{n} enlaza una descarga que no es la versión "
                        f"vigente:\n  {linea.strip()}")


class TestElNombreDelFicheroEsElQueSeConstruye:

    def test_coincide_con_lo_que_genera_inno_setup(self):
        iss = (RAIZ / "installer.iss").read_text(encoding="utf-8",
                                                 errors="replace")
        assert "OutputBaseFilename=GPromptStudio-Setup-{#MyAppVersion}" in iss, (
            "installer.iss ya no nombra así al instalador; el enlace del "
            "README apunta a un fichero que nadie construye")

    def test_la_version_del_instalador_sale_de_config(self):
        assert config.PUBLIC_VERSION in INSTALADOR
