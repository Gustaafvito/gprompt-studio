"""El .exe tiene que llevar metadatos, y UPX tiene que seguir apagado.

18-sep-2026, el peor fallo que ha tenido este proyecto. Windows Defender no
estaba avisando de nada: estaba **borrando la aplicación instalada**, junto
con su acceso directo y su clave de desinstalación, marcándola como
`Trojan:Win32/Wacatac.C!ml`. Cualquiera que instalara la v1.0.1 se quedaba
sin programa y sin explicación.

Lo que lo hizo invisible durante una semana: el **instalador** pasaba los
análisis —VirusTotal daba 1/67 y Microsoft ni lo miraba— pero el `.exe` que
dejaba en disco, que es otro fichero distinto y nunca se había analizado,
era el que se comía Defender. La documentación llegó a recomendar «si
Defender se queja del portable, usa el instalador», que era el consejo
exactamente equivocado.

La hipótesis, y por qué estos candados: el sufijo `!ml` significa que el
veredicto viene de un modelo estadístico, no de una firma. No hay código que
reconocer, hay un perfil que encaja — y un ejecutable de Windows **sin firmar
y sin ningún metadato** (sin producto, sin empresa, sin versión, sin
copyright) es ese perfil. PyInstaller no los pone si no se los das.

Tras añadirlos, el build sobrevive a un análisis explícito de Defender que
antes lo borraba. No es una demostración —una máquina, un motor— pero es la
única variable que estaba en nuestra mano sin pagar un certificado.

Estos candados vigilan que no se pierdan por el camino, porque
desaparecerían en silencio: el build no falla si faltan, solo vuelve a
generar un ejecutable anónimo.
"""
import re
from pathlib import Path

import config

RAIZ = Path(__file__).resolve().parent.parent
SPECS = ("gprompt-studio.spec", "gprompt-studio-onefile.spec")


def _spec(nombre):
    return (RAIZ / nombre).read_text(encoding="utf-8")


class TestLosSpecsPidenLosMetadatos:

    def test_los_dos_pasan_version_a_pyinstaller(self):
        for n in SPECS:
            assert "version=pyinstaller_version.escribir(" in _spec(n), (
                f"{n} no pasa `version=` a EXE(): el .exe saldría sin "
                f"producto, sin empresa y sin versión, que es el perfil que "
                f"Defender estaba borrando")

    def test_los_dos_importan_el_generador(self):
        for n in SPECS:
            assert "import pyinstaller_version" in _spec(n)

    def test_arreglan_el_sys_path(self):
        # PyInstaller ejecuta el spec sin su propia carpeta en sys.path, así
        # que sin esto el import falla y el build se cae entero.
        for n in SPECS:
            assert "SPECPATH" in _spec(n), (
                f"{n} importa el generador pero no mete SPECPATH en sys.path")


class TestUpxSigueApagado:
    """Comprimir con UPX es de los disparadores más conocidos de falso
    positivo. Estaba a True sin efecto (UPX no está instalado), que es la
    peor combinación: no aporta nada y se activa sola el día que alguien lo
    instale."""

    def test_ningun_spec_activa_upx(self):
        for n in SPECS:
            for linea in _spec(n).splitlines():
                limpia = linea.split("#")[0]
                assert "upx=True" not in limpia, (
                    f"{n} vuelve a activar UPX: «{linea.strip()}»")


class TestElRecursoGeneradoEsCoherente:

    def test_la_version_sale_de_config(self):
        import pyinstaller_version as pv
        txt = pv.contenido(config.PUBLIC_VERSION, "GPromptStudio.exe")
        assert f"StringStruct('FileVersion', '{config.PUBLIC_VERSION}')" in txt
        assert f"StringStruct('ProductVersion', '{config.PUBLIC_VERSION}')" in txt

    def test_windows_exige_cuatro_numeros(self):
        import pyinstaller_version as pv
        assert pv._cuatro_numeros("1.0.2") == (1, 0, 2, 0)
        assert pv._cuatro_numeros("2.10.3") == (2, 10, 3, 0)

    def test_lleva_empresa_producto_y_copyright(self):
        import pyinstaller_version as pv
        txt = pv.contenido(config.PUBLIC_VERSION, "GPromptStudio.exe")
        for campo in ("CompanyName", "ProductName", "LegalCopyright",
                      "FileDescription", "OriginalFilename"):
            assert f"StringStruct('{campo}'" in txt, f"falta {campo}"

    def test_el_nombre_del_fichero_es_el_real(self):
        # OriginalFilename mintiendo es peor que no ponerlo: es uno de los
        # campos que miran los motores heurísticos.
        import pyinstaller_version as pv
        txt = pv.contenido(config.PUBLIC_VERSION, "GPromptStudio-Portable-Onefile.exe")
        assert "StringStruct('OriginalFilename', 'GPromptStudio-Portable-Onefile.exe')" in txt

    def test_es_evaluable_como_python(self):
        # PyInstaller hace eval() de este fichero. Un fallo de sintaxis
        # —una comilla en un nombre, por ejemplo— rompería el build.
        import pyinstaller_version as pv
        txt = pv.contenido(config.PUBLIC_VERSION, "GPromptStudio.exe")
        cuerpo = "\n".join(l for l in txt.splitlines()
                           if not l.lstrip().startswith("#"))
        compile(cuerpo, "<version>", "eval")

    def test_el_idioma_y_la_pagina_cuadran_con_la_clave(self):
        # La clave de la StringTable es idioma+página en hexadecimal. Si no
        # cuadran, Windows no enseña ninguno de los campos.
        import pyinstaller_version as pv
        esperada = f"{pv._IDIOMA:04x}{pv._PAGINA:04x}"
        txt = pv.contenido("1.0.2", "GPromptStudio.exe")
        assert re.search(rf"StringTable\(\s*'{esperada}'", txt)
