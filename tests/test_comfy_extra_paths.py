"""ComfyUI con los modelos fuera de su carpeta (extra_model_paths.yaml).

25-sep-2026: el equipo del autor tenía los modelos en D:\\ComfyUI declarados en
extra_model_paths.yaml, y C:\\IA\\ComfyUI\\models no tenía ni `checkpoints`. El
escaneo encontraba CERO modelos y la app vivía de una caché antigua: los
modelos nuevos no aparecían nunca. Solo lo decía un WARNING en el log.
"""
from pathlib import Path

import config

# El formato real del fichero del usuario (recortado).
YAML = r"""
#Rename this to extra_model_paths.yaml and ComfyUI will load it
comfyui:
     base_path: D:\ComfyUI\
     is_default: true
     checkpoints: models/checkpoints/
     loras: models/loras/
     diffusion_models: |
          models/unet/
          models/diffusion_models/
     clip_vision: models/clip_vision/

a111:
    base_path: path/to/stable-diffusion-webui/
    checkpoints: models/Stable-diffusion
"""


class TestLeerElYaml:

    def test_secciones_base_y_claves(self):
        secciones = config._leer_extra_model_paths(YAML)
        assert len(secciones) == 2
        comfy = secciones[0]
        assert comfy["base_path"] == "D:\\ComfyUI\\"
        assert comfy["claves"]["checkpoints"] == ["models/checkpoints/"]
        # El bloque «|» con una ruta por línea.
        assert comfy["claves"]["diffusion_models"] == ["models/unet/", "models/diffusion_models/"]
        # Lo que sigue al bloque vuelve a ser una clave normal.
        assert comfy["claves"]["clip_vision"] == ["models/clip_vision/"]

    def test_un_yaml_vacio_o_raro_no_rompe(self):
        assert config._leer_extra_model_paths("") == []
        assert config._leer_extra_model_paths("esto no es yaml\n  : :\n") == []


class TestCarpetasYEscaneo:

    def test_las_carpetas_que_declara(self, tmp_path):
        (tmp_path / "extra_model_paths.yaml").write_text(YAML, encoding="utf-8")
        carpetas = [str(p) for p in config._carpetas_extra_comfy(tmp_path)]
        assert str(Path("D:/ComfyUI/models/checkpoints")) in carpetas
        assert str(Path("D:/ComfyUI/models/unet")) in carpetas
        # Solo las que escanea la app: loras y clip_vision no son modelos base.
        assert not any("loras" in c or "clip_vision" in c for c in carpetas)

    def test_sin_fichero_no_hay_extras(self, tmp_path):
        assert config._carpetas_extra_comfy(tmp_path) == []

    def test_encuentra_los_modelos_de_la_otra_carpeta(self, tmp_path):
        comfy = tmp_path / "ComfyUI"
        (comfy / "models").mkdir(parents=True)
        otra = tmp_path / "Disco2" / "models" / "checkpoints"
        otra.mkdir(parents=True)
        (otra / "juggernautXL_v9.safetensors").write_bytes(b"x")
        base = str(tmp_path / "Disco2")
        (comfy / "extra_model_paths.yaml").write_text(
            f"comfyui:\n    base_path: {base}\n    checkpoints: models/checkpoints/\n",
            encoding="utf-8")
        hallados = config._escanear_comfy_root(comfy)
        assert "juggernautXL_v9" in hallados["imagen"]

    def test_la_misma_carpeta_no_se_cuenta_dos_veces(self, tmp_path):
        comfy = tmp_path / "ComfyUI"
        ckpt = comfy / "models" / "checkpoints"
        ckpt.mkdir(parents=True)
        (ckpt / "modelo.safetensors").write_bytes(b"x")
        (comfy / "extra_model_paths.yaml").write_text(
            "comfyui:\n    checkpoints: models/checkpoints/\n", encoding="utf-8")
        hallados = config._escanear_comfy_root(comfy)
        assert hallados["imagen"] == ["modelo"]
