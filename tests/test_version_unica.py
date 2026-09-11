"""La versión se declara en cuatro ficheros y ninguno vigilaba a los otros.

11-sep-2026, preparando el v1.0.1. El número de versión vive en:

    config.py        VERSION y PUBLIC_VERSION (dos líneas)
    pyproject.toml   version
    installer.iss    #define MyAppVersion

Cuatro copias independientes. Y la de `installer.iss` es la peligrosa, porque
**da nombre al fichero que se publica**: `OutputBaseFilename` la interpola, así
que si se queda atrás, Inno Setup genera `GPromptStudio-Setup-1.0.0.exe`
mientras el resto del proyecto se cree la 1.0.1. El build no falla —falla
después, cuando `build_release.py` busca un fichero que nadie generó, o peor,
cuando se sube al release un instalador con el nombre de la versión anterior.

`VERSION` y `PUBLIC_VERSION` están separadas a propósito: la primera es la
interna y la segunda la que se enseña. Hoy coinciden, y mientras coincidan el
candado lo exige — el día que se quieran separar, este test es el sitio donde
tomar esa decisión a conciencia en vez de por descuido.

Trampa al editar estas líneas con búsqueda y reemplazo: `VERSION = "1.0.0"` es
**subcadena** de `PUBLIC_VERSION = "1.0.0"`. Un replace sin anclar al principio
de línea toca la equivocada y deja las dos iguales por accidente.
"""
import re
from pathlib import Path

import config

RAIZ = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def _de_pyproject():
    txt = (RAIZ / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'(?m)^version = "([^"]+)"', txt)
    assert m, "pyproject.toml no declara version"
    return m.group(1)


def _de_installer():
    txt = (RAIZ / "installer.iss").read_text(encoding="utf-8", errors="replace")
    m = re.search(r'#define MyAppVersion "([^"]+)"', txt)
    assert m, "installer.iss no declara MyAppVersion"
    return m.group(1)


class TestTodosDicenLoMismo:

    def test_pyproject_coincide_con_config(self):
        assert _de_pyproject() == config.VERSION, (
            f"pyproject.toml dice {_de_pyproject()} y config.py "
            f"{config.VERSION}")

    def test_el_instalador_coincide_con_config(self):
        assert _de_installer() == config.PUBLIC_VERSION, (
            f"installer.iss dice {_de_installer()} y config.py "
            f"{config.PUBLIC_VERSION}. Inno Setup pondría ese número en el "
            f"NOMBRE del .exe que se publica")

    def test_la_interna_y_la_publica_coinciden(self):
        assert config.VERSION == config.PUBLIC_VERSION


class TestElFormatoEsSemver:

    def test_config(self):
        assert SEMVER.match(config.PUBLIC_VERSION)

    def test_pyproject(self):
        assert SEMVER.match(_de_pyproject())

    def test_installer(self):
        assert SEMVER.match(_de_installer())


class TestLasNotasDeLaVersionExisten:

    def test_hay_fichero_de_notas_para_esta_version(self):
        # build_release.py las busca por nombre para comparar los hashes; si
        # no existen, el aviso de "hashes de otro build" no salta nunca.
        notas = RAIZ / "docs" / f"RELEASE-v{config.PUBLIC_VERSION}.md"
        assert notas.is_file(), (
            f"falta {notas.name}: al subir de versión hay que escribir sus "
            f"notas, no reutilizar las de la anterior")
