"""El instalador puede llevar el onefile, y limpia lo que dejó el onedir.

18-sep-2026. Windows Defender BORRABA la aplicación tras instalarla. Medido en
VirusTotal sobre los tres artefactos de la 1.0.2, de los tres Microsoft solo
marca uno:

    Setup-1.0.2.exe       1/66   Microsoft limpio
    Portable-Onefile.exe  2/67   Microsoft limpio
    GPromptStudio.exe     5/69   Microsoft: Trojan:Win32/Wacatac.B!ml

El marcado es el ejecutable del **onedir**: 14 MB de los cuales casi todo es
el bootloader de PyInstaller, el mismo binario precompilado que llevan las
muestras de XWorm —Zillya lo dice literalmente: `Backdoor.XWorm.Win32`—. En el
onefile de 178 MB ese mismo bootloader se diluye y Microsoft lo da por limpio.

Y ese onedir era justo lo que instalaba el Setup: el instalador pasaba los
análisis y luego dejaba en disco el único fichero que Defender borra.

De ahí el modo onefile del instalador. El precio son 3-5 segundos de arranque
porque el onefile se descomprime en una carpeta temporal cada vez.

Dos cosas que estos candados protegen:

1. Que el modo se elija **explícitamente** (`/DModoOnefile` desde build.py) y
   no adivinando qué hay en `dist/`, donde pueden convivir los dos builds.
2. Que se siga borrando `_internal` al actualizar. Quien venga de la 1.0.1
   tiene esa carpeta con ~180 MB de dependencias del build viejo, e Inno solo
   retira lo que él mismo instaló: sin `[InstallDelete]` se queda ahí para
   siempre, y dentro va el VCRUNTIME140.dll que el 07-sep hizo que el
   instalador pidiera cerrar Chrome.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ISS = (RAIZ / "installer.iss").read_text(encoding="utf-8", errors="replace")
BUILD = (RAIZ / "build.py").read_text(encoding="utf-8")


class TestElInstaladorPuedeLlevarElOnefile:

    def test_hay_rama_para_el_onefile(self):
        assert "#ifdef ModoOnefile" in ISS
        assert r'Source: "dist\GPromptStudio.exe"' in ISS, (
            "falta la rama que empaqueta el onefile")

    def test_sigue_existiendo_la_rama_onedir(self):
        # No se borra: el onedir arranca al instante y sigue siendo lo
        # deseable el día que se pueda firmar el ejecutable.
        assert "#else" in ISS
        assert r'Source: "dist\GPromptStudio\*"' in ISS

    def test_build_py_pasa_el_define(self):
        assert '"/DModoOnefile"' in BUILD, (
            "build.py no pasa /DModoOnefile a ISCC: el instalador seguiría "
            "empaquetando el onedir por mucho que se pida --onefile")
        assert "defines" in BUILD

    def test_el_modo_no_se_adivina_mirando_dist(self):
        # FileExists() en el preprocesador elegiría por casualidad cuando
        # están los dos builds en dist/.
        assert "FileExists" not in ISS


class TestSeLimpiaLoQueDejoElOnedir:

    def test_borra_internal_al_actualizar(self):
        assert "[InstallDelete]" in ISS, (
            "sin [InstallDelete], quien venga de la 1.0.1 se queda con "
            "_internal colgando para siempre")
        assert r'Name: "{app}\_internal"' in ISS

    def test_borra_la_carpeta_entera_no_solo_ficheros(self):
        # 'files' dejaría el árbol de directorios vacío detrás.
        bloque = ISS[ISS.index("[InstallDelete]"):]
        bloque = bloque[:bloque.index("[Icons]")]
        assert "filesandordirs" in bloque
