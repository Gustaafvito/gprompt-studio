"""Abrir el navegador no puede prestarle nuestro directorio de trabajo.

Reportado el 07-sep-2026: el instalador moría con "DeleteFile falló; código 5.
Acceso denegado" sobre _internal\\VCRUNTIME140.dll. Comprobado con Get-Process:
chrome.exe y chrome-native-host.exe tenían CARGADO ese DLL nuestro, nacidos en
el mismo segundo de un padre ya desaparecido, y la carpeta de instalación NO
estaba en el PATH.

`webbrowser.open()` arranca el navegador como proceso hijo, y el hijo hereda
el directorio de trabajo del padre — la carpeta de la app. Windows resolvió
VCRUNTIME140.dll ahí antes que en el sistema, y el navegador se quedó con el
archivo abierto. Al usuario le pasó tras pulsar "🌐 Obtener key" tres veces.
"""
import inspect
import os
from pathlib import Path

import pytest

from modules import navegador


class TestElNavegadorArrancaEnUnDirectorioNeutro:

    def test_no_arranca_en_nuestro_directorio(self, monkeypatch, tmp_path):
        visto = {}
        monkeypatch.setattr(navegador.webbrowser, "open",
                            lambda u: visto.setdefault("cwd", os.getcwd()))
        casa = tmp_path / "casa"
        casa.mkdir()
        monkeypatch.setattr(navegador, "_directorio_neutro", lambda: str(casa))
        nuestro = tmp_path / "instalacion"
        nuestro.mkdir()
        previo = os.getcwd()
        os.chdir(nuestro)
        try:
            navegador.abrir_url("https://example.com")
        finally:
            os.chdir(previo)
        assert Path(visto["cwd"]).resolve() == casa.resolve(), \
            "el navegador heredaría nuestra carpeta y bloquearía sus DLLs"

    def test_restaura_el_directorio_aunque_falle(self, monkeypatch, tmp_path):
        def _explota(_u):
            raise RuntimeError("no hay navegador")
        monkeypatch.setattr(navegador.webbrowser, "open", _explota)
        monkeypatch.setattr(navegador, "_directorio_neutro", lambda: str(tmp_path))
        previo = os.getcwd()
        assert navegador.abrir_url("https://example.com") is False
        assert os.getcwd() == previo, \
            "el resto de la app usa rutas relativas; no puede quedarse fuera"

    def test_url_vacia_no_abre_nada(self, monkeypatch):
        monkeypatch.setattr(navegador.webbrowser, "open",
                            lambda u: pytest.fail("no debería abrir nada"))
        assert navegador.abrir_url("") is False

    def test_el_directorio_neutro_existe(self):
        d = navegador._directorio_neutro()
        assert d and Path(d).is_dir()


class TestNadieLlamaDirectamenteAWebbrowser:
    """Candado: la única puerta al navegador es abrir_url()."""

    MODULOS = ("bienvenida", "dialogs", "preview_pollinations")

    def test_los_modulos_de_ui_usan_el_helper(self):
        import importlib
        for nombre in self.MODULOS:
            mod = importlib.import_module(f"modules.{nombre}")
            fuente = inspect.getsource(mod)
            assert "webbrowser.open(" not in fuente, (
                f"modules/{nombre}.py llama a webbrowser directamente: el "
                f"navegador heredaría nuestro directorio y bloquearía las DLLs")
            assert "abrir_url" in fuente
