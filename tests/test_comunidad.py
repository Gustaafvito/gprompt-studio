"""Los ficheros que GitHub espera de un repo público.

09-sep-2026, con el repo ya público: la pestaña *Community Standards* daba
cinco en amarillo. Dos importan de verdad y tres son ceremonia barata:

  · SECURITY.md — el autor es pentester certificado. Un repo suyo sin
    política de seguridad es la única de las cinco que un ojo técnico nota.
    Y sin el fichero GitHub no muestra el botón de reporte privado, así que
    la frase del README «no lo abras como issue público» no tenía dónde
    llevar a nadie.
  · Plantillas de issue — el README pide el log para diagnosticar; con una
    plantilla te lo dan siempre, en vez de pedirlo hilo a hilo.

Los candados vigilan lo que se estropea solo: que el Código de Conducta no
se quede con el marcador de contacto sin rellenar (peor que no tenerlo:
dice que se puede reportar y no dice dónde) y que ninguno de estos ficheros
públicos filtre el correo personal.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


class TestEstanLosFicherosQueGitHubPide:

    def test_politica_de_seguridad(self):
        assert (RAIZ / "SECURITY.md").is_file()

    def test_guia_de_contribucion(self):
        assert (RAIZ / "CONTRIBUTING.md").is_file()

    def test_codigo_de_conducta(self):
        assert (RAIZ / "CODE_OF_CONDUCT.md").is_file()

    def test_plantillas_de_issue(self):
        d = RAIZ / ".github" / "ISSUE_TEMPLATE"
        assert (d / "fallo.yml").is_file()
        assert (d / "modelo.yml").is_file()
        assert (d / "config.yml").is_file()

    def test_plantilla_de_pull_request(self):
        assert (RAIZ / ".github" / "pull_request_template.md").is_file()


class TestNingunoTraeMarcadoresSinRellenar:

    FICHEROS = ("SECURITY.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",
                ".github/pull_request_template.md")

    def test_sin_plantilla_a_medias(self):
        # El Contributor Covenant trae "[INSERT CONTACT METHOD]". Publicarlo
        # sin rellenar dice que se puede reportar y no dice dónde.
        for n in self.FICHEROS:
            txt = (RAIZ / n).read_text(encoding="utf-8")
            for marcador in ("[INSERT", "TODO", "XXX", "FIXME"):
                assert marcador not in txt, f"{n} lleva «{marcador}» sin rellenar"

    def test_el_codigo_de_conducta_dice_donde_reportar(self):
        txt = (RAIZ / "CODE_OF_CONDUCT.md").read_text(encoding="utf-8")
        assert "gustaafvito.com" in txt


class TestNoSeFiltraElCorreoPersonal:
    """Los 577 commits se reescribieron a noreply el 06-sep para sacar el
    correo del repo. Estos ficheros son públicos y no pueden deshacerlo:
    los bots cosechan direcciones de páginas públicas en días, y eso no se
    revierte. El contacto va por el formulario de la web."""

    def test_ninguno_lleva_una_direccion(self):
        for n in ("SECURITY.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",
                  "README.md", "README.en.md",
                  ".github/pull_request_template.md"):
            txt = (RAIZ / n).read_text(encoding="utf-8")
            assert "@gmail" not in txt, f"{n} expone un correo personal"


class TestLasPlantillasPidenLoQueHaceFalta:

    def test_la_de_fallos_pide_el_log(self):
        # Sin log toca adivinar; es la mitad del tiempo de diagnóstico.
        txt = (RAIZ / ".github" / "ISSUE_TEMPLATE" / "fallo.yml").read_text(
            encoding="utf-8")
        assert "gprompt.log" in txt
        assert "clave" in txt.lower(), (
            "hay que avisar de borrar las claves antes de pegar el log")

    def test_la_de_modelos_pide_datos_MEDIDOS(self):
        # De once listas escritas desde documentación oficial, once estaban
        # podridas. Lo que vale es lo que sale de generar.
        txt = (RAIZ / ".github" / "ISSUE_TEMPLATE" / "modelo.yml").read_text(
            encoding="utf-8")
        assert "generando" in txt

    def test_las_dudas_van_a_discussions(self):
        txt = (RAIZ / ".github" / "ISSUE_TEMPLATE" / "config.yml").read_text(
            encoding="utf-8")
        assert "discussions" in txt
        assert "blank_issues_enabled: false" in txt
