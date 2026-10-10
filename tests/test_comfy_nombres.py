"""Los workflows exportados llevan el nombre exacto con que ComfyUI lista cada modelo.

10-oct-2026: en el equipo del autor, Anima estaba en
models/diffusion_models/LoraLab-D/ (un junction a D:) y ComfyUI lo llamaba
«LoraLab-D\\anima-base-v1.0.safetensors». El workflow individual de la toma
01 de Einar, con «anima-base-v1.0.safetensors», falló con «Value not in list»
para el modelo y para el CLIP, y hubo que elegirlos a mano.
"""
import json
import os

import config
from modules.avatar_generator import (
    exportar_dataset,
    exportar_workflows_comfy,
    generar_dataset_avatar,
)
from modules.comfy_export import ajustar_nombres_comfy

SUB = "LoraLab-D"


def _fichero(ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(b"x")


def _nodo(tipo, nombre):
    return {"type": tipo, "widgets_values": [nombre, "default"]}


class TestNombresModelosComfy:

    def test_rutas_dentro_de_cada_carpeta_como_las_lista_comfyui(self, tmp_path):
        modelos = tmp_path / "models"
        _fichero(modelos / "diffusion_models" / SUB / "anima-base-v1.0.safetensors")
        _fichero(modelos / "text_encoders" / SUB / "qwen_3_06b_base.safetensors")
        _fichero(modelos / "vae" / "qwen_image_vae.safetensors")
        _fichero(modelos / "loras" / "Einar_anima.safetensors")
        _fichero(modelos / "loras" / "notas.txt")          # no es un modelo
        config._cache_nombres_comfy.clear()
        n = config.nombres_modelos_comfy(str(tmp_path))
        assert n["diffusion_models"] == [os.path.join(SUB, "anima-base-v1.0.safetensors")]
        assert n["text_encoders"] == [os.path.join(SUB, "qwen_3_06b_base.safetensors")]
        assert n["vae"] == ["qwen_image_vae.safetensors"]
        assert n["loras"] == ["Einar_anima.safetensors"]
        assert n["checkpoints"] == []

    def test_tambien_las_carpetas_de_extra_model_paths(self, tmp_path):
        otro = tmp_path / "otro_disco"
        _fichero(otro / "mis_loras" / "Lyra_anima_FINAL.safetensors")
        (tmp_path / "models").mkdir()
        (tmp_path / "extra_model_paths.yaml").write_text(
            f"comfyui:\n    base_path: {otro}\n    loras: mis_loras/\n", encoding="utf-8")
        config._cache_nombres_comfy.clear()
        assert config.nombres_modelos_comfy(str(tmp_path))["loras"] == [
            "Lyra_anima_FINAL.safetensors"]

    def test_sin_comfyui_no_hay_nombres(self):
        assert config.nombres_modelos_comfy() == {}    # en los tests, sin ruta


class TestAjustarNombres:

    NOMBRES = {
        "diffusion_models": [SUB + "\\anima-base-v1.0.safetensors",
                             SUB + "\\viejos\\anima-base-v1.0.safetensors"],
        "text_encoders": [SUB + "\\qwen_3_06b_base.safetensors"],
        "vae": [SUB + "\\qwen_image_vae.safetensors", "qwen_image_vae.safetensors"],
        "loras": ["Einar_anima.safetensors"],
    }

    def _ajustar(self, *nodos):
        wf = {"nodes": [dict(n, widgets_values=list(n["widgets_values"])) for n in nodos]}
        ajustar_nombres_comfy(wf, self.NOMBRES)
        return [n["widgets_values"][0] for n in wf["nodes"]]

    def test_el_de_la_subcarpeta_y_el_menos_anidado(self):
        assert self._ajustar(_nodo("UNETLoader", "anima-base-v1.0.safetensors")) == [
            SUB + "\\anima-base-v1.0.safetensors"]

    def test_el_clip_se_busca_en_text_encoders(self):
        assert self._ajustar(_nodo("CLIPLoader", "qwen_3_06b_base.safetensors")) == [
            SUB + "\\qwen_3_06b_base.safetensors"]

    def test_si_ya_esta_tal_cual_no_se_toca(self):
        assert self._ajustar(_nodo("VAELoader", "qwen_image_vae.safetensors"),
                             _nodo("LoraLoader", "Einar_anima.safetensors")) == [
            "qwen_image_vae.safetensors", "Einar_anima.safetensors"]

    def test_si_no_esta_instalado_se_deja(self):
        assert self._ajustar(_nodo("UNETLoader", "flux1-dev.safetensors"),
                             _nodo("CLIPTextEncode", "anima-base-v1.0.safetensors")) == [
            "flux1-dev.safetensors", "anima-base-v1.0.safetensors"]


class TestEnElDatasetDeComfyUI:

    def test_los_workflows_del_generador_salen_con_los_nombres_exactos(
            self, tmp_path, monkeypatch):
        nombres = TestAjustarNombres.NOMBRES
        monkeypatch.setattr(config, "nombres_modelos_comfy", lambda ruta_comfyui="": nombres)
        r = generar_dataset_avatar(lambda s, u: "a man", {}, "ohwx_einar",
                                   ["face_front", "full_front"], "anime style", "bg")
        base = exportar_dataset(r, str(tmp_path))
        exportar_workflows_comfy(r, base, "anima-base-v1.0")
        for nombre in ("DATASET_COMPLETO.json", os.path.join("individuales", "01_face_front.json")):
            with open(os.path.join(base, "workflows", nombre), encoding="utf-8") as f:
                wf = json.load(f)
            cargadores = {n["type"]: n["widgets_values"][0] for n in wf["nodes"]
                          if n["type"] in ("UNETLoader", "CLIPLoader", "VAELoader")}
            assert cargadores == {
                "UNETLoader": SUB + "\\anima-base-v1.0.safetensors",
                "CLIPLoader": SUB + "\\qwen_3_06b_base.safetensors",
                "VAELoader": "qwen_image_vae.safetensors",
            }, nombre
