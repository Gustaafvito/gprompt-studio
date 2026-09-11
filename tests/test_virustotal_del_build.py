"""Los informes de VirusTotal tienen que ser los del .exe que se publica.

11-sep-2026, preparando la 1.0.1. Al regenerar los binarios, los enlaces de
VirusTotal de la documentación seguían apuntando a los informes de los
**binarios de la 1.0.0**. Son ficheros distintos: un instalador nuevo tiene
otro hash y otro análisis. Enseñar el informe viejo como si fuera el del
fichero que te acabas de bajar es exactamente lo que `SECURITY.md` promete no
hacer — y lo descubre cualquiera en treinta segundos, porque el hash lo
publicamos nosotros mismos al lado.

El fallo se repitió dos veces en el mismo día: primero en las notas de la
versión y después, al arreglarlo, en las dos páginas de descarga. El motivo
es que la misma afirmación vivía copiada en **cinco ficheros** sin nada que
los atara, y uno de ellos —`LEEME-PRIMERO.txt`— viaja dentro del distribuible,
donde ya no se puede corregir.

Al quitar aquellos enlaces apareció un segundo fallo encadenado: los hashes
de las páginas de descarga **vivían dentro de las URLs de VirusTotal**, así
que se quedaron sin ninguna huella mientras el texto seguía prometiendo «cada
descarga publica su huella SHA-256».

Se excluyen a propósito las notas de versiones ANTERIORES: sus enlaces
apuntan a sus propios binarios y eso es correcto, son un documento histórico.
"""
import re
from pathlib import Path

import config

RAIZ = Path(__file__).resolve().parent.parent
NOTAS_REL = f"docs/RELEASE-v{config.PUBLIC_VERSION}.md"

PUBLICOS = ("SECURITY.md", "README.md", "README.en.md",
            "docs/LEEME-PRIMERO.txt", "docs/RELEASE-CUERPO.md",
            "docs/WEB-descarga.md", "docs/WEB-descarga.en.md",
            NOTAS_REL)

# Anclado por los dos lados: sin esto, una ventana de 64 que empiece un
# carácter antes del hash real también casaría.
HEX64 = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")

# Une una línea que TERMINA en hex con la siguiente que EMPIEZA en hex. El
# LEEME parte las URLs largas en dos para no pasarse del ancho y el hash
# llega cortado.
#
# El umbral de 8 no es adorno: juntar todos los espacios del fichero pegaba
# «…Setup-1.0.1.exe» al hash de la línea siguiente, y la «e» de «exe» —que es
# un dígito hexadecimal válido— corría la ventana un carácter y fabricaba un
# hash inexistente. Este test se estrenó dando ese falso positivo.
_PARTIDO = re.compile(r"([0-9a-f]{8,})[ \t]*\r?\n[ \t]*([0-9a-f]{8,})")


def _texto(nombre):
    return _PARTIDO.sub(r"\1\2",
                        (RAIZ / nombre).read_text(encoding="utf-8"))


def _del_release():
    return set(HEX64.findall(_texto(NOTAS_REL)))


class TestNingunDocumentoEnlazaOtroBuild:

    def test_las_notas_publican_dos_hashes(self):
        assert len(_del_release()) == 2, (
            "las notas deben publicar el SHA-256 de los dos artefactos")

    def test_ningun_hash_ajeno_en_los_publicos(self):
        buenos = _del_release()
        for nombre in PUBLICOS:
            for h in HEX64.findall(_texto(nombre)):
                assert h in buenos, (
                    f"{nombre} menciona el hash {h[:12]}…, que no es de "
                    f"ninguno de los dos ficheros de esta versión. Si acabas "
                    f"de regenerar los .exe, hay que resubirlos a VirusTotal "
                    f"y cambiar TODOS los enlaces, no solo los del release")


class TestLasPaginasDeDescargaPublicanLaHuella:
    """Prometen «cada descarga publica su huella»; tienen que cumplirlo."""

    def test_las_dos_llevan_los_dos_hashes(self):
        for nombre in ("docs/WEB-descarga.md", "docs/WEB-descarga.en.md"):
            assert set(HEX64.findall(_texto(nombre))) == _del_release(), (
                f"{nombre} no publica los dos hashes del build actual")

    def test_el_leeme_del_distribuible_tambien(self):
        # Este viaja DENTRO del .exe: si sale mal, ya no se corrige.
        assert set(HEX64.findall(_texto("docs/LEEME-PRIMERO.txt"))) == _del_release()
