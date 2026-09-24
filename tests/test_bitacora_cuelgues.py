"""La bitácora de cuelgues se queda SÓLO cuando hubo cuelgue.

Antes era un único fichero en modo "a" en la carpeta del usuario, con una
línea por test: 687 KB tras unas pocas tiradas y ningún volcado dentro. Ver
tests/_bitacora_cuelgues.py.

Se puede fallar por los dos lados, y los dos se vigilan:
  • de MÁS: que vuelva a acumular migas de tiradas que acabaron bien;
  • de MENOS: que la limpieza se lleve también el volcado de un cuelgue, que
    es lo único para lo que existe el fichero.
"""
import faulthandler
import os
import subprocess
import sys
import textwrap
from pathlib import Path

from tests import _bitacora_cuelgues as bitacora

RAIZ = Path(__file__).resolve().parent.parent


def _bitacoras(carpeta):
    return sorted(Path(carpeta).glob("tests_colgados-*.log"))


class TestCerrar:

    def test_sin_volcado_se_borra(self, tmp_path):
        ruta = bitacora.ruta_nueva(tmp_path)
        fh = open(ruta, "w", encoding="utf-8")
        fh.write("\n=== tests/test_x.py::test_a ===\n")
        assert bitacora.cerrar(fh, ruta) is False
        assert not os.path.exists(ruta)

    def test_con_un_volcado_de_verdad_se_conserva(self, tmp_path):
        # Un volcado AUTÉNTICO de faulthandler, no una cadena escrita a mano:
        # si su formato cambia, este test lo dice.
        ruta = bitacora.ruta_nueva(tmp_path)
        fh = open(ruta, "w", encoding="utf-8")
        fh.write("\n=== tests/test_x.py::test_a ===\n")
        fh.flush()
        faulthandler.dump_traceback(file=fh)
        assert bitacora.cerrar(fh, ruta) is True
        assert bitacora.FIRMA_DE_VOLCADO in Path(ruta).read_text(encoding="utf-8")

    def test_cerrar_nunca_lanza(self, tmp_path):
        ruta = bitacora.ruta_nueva(tmp_path)
        fh = open(ruta, "w", encoding="utf-8")
        fh.close()
        os.remove(ruta)
        assert bitacora.cerrar(fh, ruta) is False


class TestUnaPorProceso:

    def test_dos_procesos_no_comparten_fichero(self, tmp_path):
        # Hay sesiones en paralelo en worktrees: con un único fichero, una
        # tirada truncaría o intercalaría las migas de la otra.
        a = bitacora.ruta_nueva(tmp_path, pid=111, ahora=0)
        b = bitacora.ruta_nueva(tmp_path, pid=222, ahora=0)
        assert a != b
        assert Path(a).parent == Path(b).parent == tmp_path


def _pytest_aparte(tmp_path, cuerpo_del_test, limite):
    """Corre pytest en otro proceso, con el conftest de verdad y otra casa.

    `-p tests.conftest` carga los ganchos reales del cortafuegos; la casa del
    usuario apunta a tmp_path para no escribir en la de verdad.
    """
    (tmp_path / "test_suelto.py").write_text(
        textwrap.dedent(cuerpo_del_test), encoding="utf-8")
    entorno = dict(os.environ, USERPROFILE=str(tmp_path), HOME=str(tmp_path),
                   GPROMPT_LIMITE_TEST=str(limite))
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
         "-p", "tests.conftest", "--rootdir", str(tmp_path),
         str(tmp_path / "test_suelto.py")],
        cwd=RAIZ, env=entorno, capture_output=True, text=True, timeout=120)


class TestDeExtremoAExtremo:

    def test_una_tirada_que_acaba_bien_no_deja_nada(self, tmp_path):
        r = _pytest_aparte(tmp_path, """
            def test_rapido():
                assert True
        """, limite=30)
        assert r.returncode == 0, r.stdout + r.stderr
        assert _bitacoras(tmp_path / ".arquitecto_prompts") == []

    def test_un_cuelgue_aborta_y_deja_su_volcado(self, tmp_path):
        r = _pytest_aparte(tmp_path, """
            import time
            def test_colgado():
                time.sleep(60)
        """, limite=1)
        # La salida del subproceso va en cada mensaje: sin ella, un fallo
        # aquí no dice nada de lo que pasó al otro lado.
        salida = f"\n--- rc={r.returncode}\n--- stdout:\n{r.stdout[-2000:]}\n--- stderr:\n{r.stderr[-2000:]}"
        assert r.returncode != 0, "el cortafuegos no abortó el proceso" + salida
        quedan = _bitacoras(tmp_path / ".arquitecto_prompts")
        assert len(quedan) == 1, f"bitácoras: {quedan}" + salida
        texto = quedan[0].read_text(encoding="utf-8", errors="replace")
        # Qué test era y dónde estaba parado: lo que hace legible un cuelgue.
        for esperado in ("test_suelto.py::test_colgado", bitacora.FIRMA_DE_VOLCADO,
                         "in test_colgado"):
            assert esperado in texto, f"falta {esperado!r} en la bitácora:\n{texto[-2000:]}" + salida
