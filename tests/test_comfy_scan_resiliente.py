"""Una carpeta problemática no debe dejar al usuario sin NINGÚN modelo local.

En el log del usuario aparecía 16 veces (jul-sep 2026):

  OSError: [WinError 448] La ruta no se puede recorrer porque contiene un
  punto de montaje no confiable: 'C:\\IA\\ComfyUI\\models\\checkpoints'
    File "config.py", in _escanear_comfy_root
    File "pathlib.py", in exists

`Path.exists()` devuelve False ante los errores de "no encontrado", pero
CUALQUIER otro OSError lo propaga — y ese propagarse tumbaba el escaneo entero:
si fallaba checkpoints, tampoco se leían diffusion_models ni unet.

Curiosamente la carpeta se lee sin problema desde una consola normal, así que
el fallo depende del contexto del proceso. Por eso se hace tolerante en vez de
perseguir la causa: lo que importa es no quedarse sin inventario.
"""
from pathlib import Path

import config


class TestCarpetaQueFallaAlComprobar:
    """exists() revienta (el caso real del WinError 448)."""

    def test_las_demas_carpetas_se_siguen_leyendo(self, tmp_path, monkeypatch):
        modelos = tmp_path / "models"
        (modelos / "checkpoints").mkdir(parents=True)
        (modelos / "unet").mkdir()
        (modelos / "unet" / "flux1-dev.safetensors").write_text("x")

        exists_real = Path.exists

        def _exists(self):
            if self.name == "checkpoints":
                raise OSError(448, "punto de montaje no confiable")
            return exists_real(self)

        monkeypatch.setattr(Path, "exists", _exists)
        hallados = config._escanear_comfy_root(tmp_path)
        assert "flux1-dev" in hallados["imagen"], \
            "una carpeta rota no puede impedir leer las demás"

    def test_no_lanza_la_excepcion_hacia_arriba(self, tmp_path, monkeypatch):
        (tmp_path / "models" / "checkpoints").mkdir(parents=True)
        monkeypatch.setattr(
            Path, "exists",
            lambda self: (_ for _ in ()).throw(OSError(448, "no confiable")))
        config._escanear_comfy_root(tmp_path)  # no debe lanzar


class TestRecorridoQueFallaAMedias:
    """rglob revienta después de haber encontrado cosas."""

    def test_se_conserva_lo_ya_encontrado(self, tmp_path, monkeypatch):
        ckpt = tmp_path / "models" / "checkpoints"
        ckpt.mkdir(parents=True)
        (ckpt / "bueno.safetensors").write_text("x")

        def _rglob_roto(self, patron):
            yield ckpt / "bueno.safetensors"
            raise OSError(448, "punto de montaje no confiable")

        monkeypatch.setattr(Path, "rglob", _rglob_roto)
        hallados = config._escanear_comfy_root(tmp_path)
        assert "bueno" in hallados["imagen"], \
            "lo leído antes del fallo no debe perderse"

    def test_un_fichero_inaccesible_no_corta_el_resto(self, tmp_path, monkeypatch):
        ckpt = tmp_path / "models" / "checkpoints"
        ckpt.mkdir(parents=True)
        (ckpt / "malo.safetensors").write_text("x")
        (ckpt / "bueno.safetensors").write_text("x")

        is_file_real = Path.is_file

        def _is_file(self):
            if self.stem == "malo":
                raise OSError(448, "no confiable")
            return is_file_real(self)

        monkeypatch.setattr(Path, "is_file", _is_file)
        hallados = config._escanear_comfy_root(tmp_path)
        assert "bueno" in hallados["imagen"]
        assert "malo" not in hallados["imagen"]


class TestSinFallosSigueIgual:

    def test_escaneo_normal_intacto(self, tmp_path):
        ckpt = tmp_path / "models" / "checkpoints"
        ckpt.mkdir(parents=True)
        (ckpt / "flux1-dev.safetensors").write_text("x")
        (ckpt / "wan2.2_t2v_14B.safetensors").write_text("x")
        hallados = config._escanear_comfy_root(tmp_path)
        assert "flux1-dev" in hallados["imagen"]
        assert "wan2.2_t2v_14B" in hallados["video"]
