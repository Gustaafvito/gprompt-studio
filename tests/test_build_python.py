"""El .exe lleva el Python con el que se probó y se auditó.

24-oct-2026: para quitar los 37 CVE de Pillow 12.3.0 el build pasó al
Python 3.12 del .venv (Pillow 13 ya no admite el 3.10). Los tests y pip-audit
corrieron con el 3.12, pero build.py llamaba a «pyinstaller» por nombre, el
PATH daba el del Python 3.10 global y el .exe salió con Pillow 12.3.0 sin
que nada avisara. Se descubrió arrancando el .exe.
"""
import inspect
import sys
import types

import pytest

import build
import build_release


def test_pyinstaller_corre_con_el_python_del_build():
    fuente = inspect.getsource(build.build_pyinstaller)
    assert '[sys.executable, "-m", "PyInstaller"' in fuente
    assert 'cmd = ["pyinstaller"' not in fuente


@pytest.fixture
def exe_con(monkeypatch):
    """Simula el .exe de PyInstaller con las DLL que se le pasen."""
    def preparar(*dlls):
        lector = types.ModuleType("PyInstaller.archive.readers")
        lector.CArchiveReader = lambda ruta: types.SimpleNamespace(
            toc={**{d: None for d in dlls}, "PIL/__init__.pyc": None, "python3.dll": None})
        monkeypatch.setitem(sys.modules, "PyInstaller", types.ModuleType("PyInstaller"))
        monkeypatch.setitem(sys.modules, "PyInstaller.archive",
                            types.ModuleType("PyInstaller.archive"))
        monkeypatch.setitem(sys.modules, "PyInstaller.archive.readers", lector)
    return preparar


def test_con_el_mismo_python_sigue(exe_con, tmp_path):
    exe_con(f"python{sys.version_info.major}{sys.version_info.minor}.dll")
    build_release.comprobar_python_del_exe(tmp_path / "GPromptStudio.exe")


def test_con_otro_python_para_el_build(exe_con, tmp_path):
    otro = "python310.dll" if sys.version_info[:2] != (3, 10) else "python312.dll"
    exe_con(otro)
    with pytest.raises(SystemExit, match=otro):
        build_release.comprobar_python_del_exe(tmp_path / "GPromptStudio.exe")
