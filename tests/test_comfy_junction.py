"""El desplegable de ComfyUI se quedó vacío, y no fue por falta de modelos.

08-sep-2026. El usuario configura C:/IA/ComfyUI y el combo de imagen sigue
mostrando "GPT Image 2": ni un modelo local. En su log, 16 veces:

    [WinError 448] La ruta no se puede recorrer porque contiene un punto de
    montaje no confiable: 'C:\\IA\\ComfyUI\\models\\checkpoints'

`C:/IA/ComfyUI/models` es un JUNCTION a `D:/ComfyUI/models`, y Windows 11 no
deja recorrer un junction creado por un usuario sin permisos de administrador
(Redirection Guard). La misma carpeta se lee sin problema desde una consola,
lo que hacía el diagnóstico especialmente engañoso.

Había dos fallos encadenados, y el segundo era el grave:

  1. El escaneo cazaba el OSError y SALTABA la carpeta. No había crash, pero
     el usuario se quedaba con cero modelos — para él, lo mismo que un crash.
  2. Ese cero se creía a pies juntillas: `_poblar_comfy([], [])` vaciaba los
     desplegables Y `_guardar_cache_comfy` escribía la caché vacía. El
     arranque siguiente ya nacía sin modelos, con la caché envenenada y sin
     forma de recuperarlos salvo borrando el JSON a mano. Así quedó su
     comfy_cache.json: {"path": "C:/IA/ComfyUI", "imagen": [], "video": []}.
"""
import logging
from pathlib import Path

import config


class TestSeEntraPorLaRutaRealDelJunction:

    def test_resuelve_un_junction(self, tmp_path, monkeypatch):
        destino = tmp_path / "real"
        destino.mkdir()
        enlace = tmp_path / "enlace"
        monkeypatch.setattr(config.os.path, "realpath",
                            lambda p: str(destino), raising=False)
        assert config._resolver_junction(enlace) == destino

    def test_una_carpeta_normal_no_es_junction(self):
        # realpath devuelve la misma ruta -> no hay nada que resolver, y el
        # fallo es otro (permisos, disco). No se debe enmascarar.
        assert config._resolver_junction(Path(config.__file__).parent) is None

    def test_si_la_ruta_real_tampoco_existe_devuelve_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config.os.path, "realpath",
                            lambda p: str(tmp_path / "no_existe"), raising=False)
        assert config._resolver_junction(tmp_path / "enlace") is None

    def test_el_escaneo_reintenta_tras_el_winerror_448(self, tmp_path, monkeypatch):
        # models/ bloqueado como lo bloquea Windows; el mismo contenido
        # accesible por la ruta "real".
        real = tmp_path / "D" / "models"
        (real / "checkpoints").mkdir(parents=True)
        (real / "checkpoints" / "juggernautXL_v9.safetensors").write_bytes(b"x")

        bloqueada = tmp_path / "C" / "models"
        exists_original = Path.exists

        def exists(self):
            if str(bloqueada) in str(self):
                raise OSError(13, "punto de montaje no confiable", str(self), 448)
            return exists_original(self)

        monkeypatch.setattr(Path, "exists", exists)
        monkeypatch.setattr(
            config.os.path, "realpath",
            lambda p: str(real / Path(p).name) if str(bloqueada) in str(p) else str(p),
            raising=False)

        hallados = config._escanear_comfy_root(tmp_path / "C")
        assert "juggernautXL_v9" in hallados["imagen"], (
            "el junction estaba bloqueado pero la ruta real se leía: "
            "rendirse deja al usuario sin ningún modelo local")


class TestUnEscaneoEnBlancoNoPisaLaCache:

    def _preparar(self, monkeypatch, hallados):
        monkeypatch.setattr(config, "_autodiscovery_hecho", False)
        monkeypatch.setattr(config, "_ruta_comfy_configurada", lambda: "C:/IA/ComfyUI")
        monkeypatch.setattr(config, "_ruta_comfy_detectada", None)
        monkeypatch.setattr(config, "_escanear_comfy_root", lambda r: hallados)
        guardadas, poblados = [], []
        monkeypatch.setattr(config, "_guardar_cache_comfy",
                            lambda r, i, v: guardadas.append((i, v)))
        monkeypatch.setattr(config, "_poblar_comfy",
                            lambda i, v: poblados.append((i, v)))
        return guardadas, poblados

    def test_no_vacia_los_desplegables_ni_guarda_el_cero(self, monkeypatch):
        monkeypatch.setitem(config._COMFY_CACHE_APLICADA, "imagen", ["juggernautXL_v9"])
        monkeypatch.setitem(config._COMFY_CACHE_APLICADA, "video", ["wan2.2_i2v"])
        guardadas, poblados = self._preparar(
            monkeypatch, {"imagen": [], "video": [], "audio": set()})

        config.aplicar_autodiscovery_comfy()

        assert not poblados, "vaciar el combo con la caché llena es perder modelos"
        assert not guardadas, "guardar la caché vacía envenena el arranque siguiente"

    def test_avisa_en_el_log(self, monkeypatch, caplog):
        monkeypatch.setitem(config._COMFY_CACHE_APLICADA, "imagen", ["juggernautXL_v9"])
        monkeypatch.setitem(config._COMFY_CACHE_APLICADA, "video", [])
        self._preparar(monkeypatch, {"imagen": [], "video": [], "audio": set()})
        with caplog.at_level(logging.WARNING, logger="config"):
            config.aplicar_autodiscovery_comfy()
        assert any("no encontro nada" in r.message for r in caplog.records), (
            "conservar la caché en silencio esconde una carpeta inaccesible")

    def test_con_la_cache_vacia_no_hay_nada_que_conservar(self, monkeypatch):
        # Primera instalación sin ComfyUI: el cero es legítimo y no se avisa.
        monkeypatch.setitem(config._COMFY_CACHE_APLICADA, "imagen", [])
        monkeypatch.setitem(config._COMFY_CACHE_APLICADA, "video", [])
        guardadas, poblados = self._preparar(
            monkeypatch, {"imagen": [], "video": [], "audio": set()})
        assert config.aplicar_autodiscovery_comfy() == 0
        assert not poblados and not guardadas

    def test_un_escaneo_con_modelos_si_actualiza(self, monkeypatch):
        monkeypatch.setitem(config._COMFY_CACHE_APLICADA, "imagen", ["viejo"])
        monkeypatch.setitem(config._COMFY_CACHE_APLICADA, "video", [])
        guardadas, poblados = self._preparar(
            monkeypatch, {"imagen": ["nuevo"], "video": [], "audio": set()})
        config.aplicar_autodiscovery_comfy()
        assert poblados == [(["nuevo"], [])]
        assert guardadas == [(["nuevo"], [])]
