"""La licencia existe, es la que dice el README, y VIAJA con el .exe.

Hasta el 08-sep-2026 el README lucía una insignia de MIT y una línea
"Licencia MIT." pero NO había fichero LICENSE: el proyecto prometía una
licencia que nunca se había concedido. Elegida Apache 2.0 sobre MIT porque
el valor de la herramienta no es el código Python sino `data/` — 350 fichas
de modelos medidas contra las plataformas reales — y Apache obliga a
declarar los cambios y a conservar el NOTICE, cosa que MIT no hace.

Lo que más fácil se olvida: Apache 2.0 §4(a) OBLIGA a entregar una copia de
la licencia a quien reciba el software, y §4(d) a propagar el NOTICE. Los
.spec empaquetaban README.md y nada más, así que cada .exe distribuido
habría incumplido la licencia del propio proyecto.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


class TestLosFicherosExisten:

    def test_hay_licencia(self):
        assert (RAIZ / "LICENSE").is_file()

    def test_es_apache_2(self):
        txt = (RAIZ / "LICENSE").read_text(encoding="utf-8")
        assert "Apache License" in txt and "Version 2.0" in txt
        # El texto completo, no un resumen: sin el cuerpo no hay licencia.
        assert "APPENDIX: How to apply the Apache License" in txt
        assert len(txt.splitlines()) > 190

    def test_lleva_el_copyright_puesto(self):
        # El titular es la PERSONA, no el pseudonimo: una obra bajo
        # pseudonimo esta igual de protegida, pero el nombre legal es mas
        # solido si algun dia hay que reclamar la autoria. Decision del
        # autor el 08-sep-2026.
        txt = (RAIZ / "LICENSE").read_text(encoding="utf-8")
        assert "Copyright 2026 Gustavo Luis Sánchez Escobar" in txt
        assert "[yyyy]" not in txt, "quedó la plantilla sin rellenar"

    def test_el_notice_conserva_la_identidad_publica(self):
        # El proyecto se conoce como «Gustaafvito» y asi firma la web: el
        # titular legal no debe borrar la marca con la que se distribuye.
        txt = (RAIZ / "NOTICE").read_text(encoding="utf-8")
        assert "Gustavo Luis Sánchez Escobar" in txt
        assert "Gustaafvito" in txt

    def test_hay_notice(self):
        txt = (RAIZ / "NOTICE").read_text(encoding="utf-8")
        assert "G-Prompt Studio" in txt and "Apache" in txt


class TestElReadmeNoPrometeOtraCosa:

    def _readme(self):
        return (RAIZ / "README.md").read_text(encoding="utf-8")

    def test_ni_rastro_de_mit(self):
        assert "MIT" not in self._readme(), (
            "el README prometía MIT sin fichero; si vuelve a nombrarlo, "
            "vuelve a prometer una licencia que no se ha concedido")

    def test_la_insignia_apunta_al_fichero(self):
        txt = self._readme()
        assert "license-Apache" in txt
        assert "](LICENSE)" in txt, "la insignia tiene que llevar al fichero"


class TestLaLicenciaViajaConElExe:
    """Apache 2.0 §4(a) y §4(d): el que recibe el software recibe la licencia."""

    def test_los_dos_spec_la_empaquetan(self):
        for spec in ("gprompt-studio.spec", "gprompt-studio-onefile.spec"):
            txt = (RAIZ / spec).read_text(encoding="utf-8")
            assert "('LICENSE'," in txt, f"{spec} no empaqueta la licencia"
            assert "('NOTICE'," in txt, f"{spec} no empaqueta el NOTICE"

    def test_el_instalador_la_ensena(self):
        txt = (RAIZ / "installer.iss").read_text(encoding="utf-8")
        assert "LicenseFile=LICENSE" in txt, (
            "el instalador tenía LicenseFile vacío: nadie veía la licencia")


class TestElTitularSeVeSinBucear:
    """En el LICENSE el copyright cae en la linea 190 de 202.

    Es donde Apache dice que va (el APPENDIX), y ahi se queda: el detector
    de licencias de GitHub casa contra el cuerpo literal, y meterle una
    linea delante arriesga que el repo muestre "Other" en vez de
    "Apache-2.0". Pero quien abre la pestana de licencia ve texto generico y
    no sabe de quien es la obra, asi que el titular va tambien en los dos
    README, que es donde la gente mira.
    """

    def test_los_dos_readme_nombran_al_titular(self):
        for n in ("README.md", "README.en.md"):
            txt = (RAIZ / n).read_text(encoding="utf-8")
            assert "Gustavo Luis Sánchez Escobar" in txt, f"{n} no nombra al titular"

    def test_el_license_sigue_siendo_el_texto_literal(self):
        # Si alguien mete el copyright ARRIBA, GitHub puede dejar de
        # reconocer la licencia.
        txt = (RAIZ / "LICENSE").read_text(encoding="utf-8")
        assert txt.lstrip().startswith("Apache License"), (
            "el LICENSE tiene que empezar por el texto de Apache")
