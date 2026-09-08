"""El escaneo de ComfyUI: fuera lo que no genera imágenes, y la carpeta cuenta.

Auditadas las fichas de los 350 modelos de la plataforma el 08-sep-2026. De los
19 de imagen que se quedaban sin ficha, seis no eran "falta catalogar":

  · hunyuan_3d_v2.1 (6,9 GB) y triposplat_fp16 (707 MB) generan mallas y
    splats 3D, no imágenes. `hunyuan3d` ya estaba en la lista de exclusión pero
    NO cazaba `hunyuan_3d_v2.1`, que lleva guion bajo.
  · `model` (235 MB) salía de unet/flux_unchained/text_encoder/: es un
    codificador de texto, no un checkpoint. El formato HuggingFace reparte un
    modelo en transformer/ + text_encoder/ + vae/ y el escaneo recursivo se
    tragaba las piezas sueltas.
  · playground-v2.5 y realismByStableYogi_v60DMD2ALT viven en
    checkpoints/SDXL/, y diffusion_pytorch_model en unet/flux_unchained/: la
    carpeta decía la familia y se estaba tirando esa información.
"""
import config


class TestLos3DNoSonGeneradoresDeImagen:

    NOMBRES = ("hunyuan_3d_v2.1", "hunyuan-3d-v2", "triposplat_fp16",
               "TripoSR_v1", "trellis_image_large", "sf3d_base",
               "instantmesh_large", "zero123_xl")

    def test_se_excluyen_del_escaneo(self):
        for n in self.NOMBRES:
            low = n.lower()
            excluido = any(config._token_en_nombre(t, low)
                           for t in config._COMFY_EXCLUIR_TOKENS)
            assert excluido, f"{n} genera 3D; no puede salir en el combo de imagen"

    def test_un_generador_de_imagen_normal_no_se_excluye(self):
        for n in ("juggernautXL_v9", "flux1-dev", "z_image_turbo_bf16",
                  "playground-v2.5-1024px-aesthetic.fp16"):
            low = n.lower()
            excluido = any(config._token_en_nombre(t, low)
                           for t in config._COMFY_EXCLUIR_TOKENS)
            assert not excluido, f"{n} sí es un generador de imagen"


class TestLasPiezasDelPipelineNoSonModelos:

    def test_las_carpetas_del_formato_huggingface_estan_excluidas(self):
        for c in ("text_encoder", "tokenizer", "vae", "clip", "clip_vision"):
            assert c in config._COMFY_CARPETAS_EXCLUIDAS, (
                f"{c}/ contiene piezas de un modelo, no modelos")

    def test_transformer_no_se_excluye(self):
        # transformer/ SÍ es el modelo en el formato HuggingFace: es lo único
        # de esas carpetas que se puede generar.
        assert "transformer" not in config._COMFY_CARPETAS_EXCLUIDAS


class TestLaCarpetaComoPistaDeFamilia:

    def test_el_nombre_manda_sobre_la_carpeta(self, monkeypatch):
        # Un flux dentro de una carpeta SDXL sigue siendo flux.
        monkeypatch.setitem(config._COMFY_FAMILIA_CARPETA,
                            config._norm_nombre_comfy("flux1-dev"), "sdxl")
        assert config.detectar_familia_comfy("flux1-dev") == "flux"

    def test_la_carpeta_entra_cuando_el_nombre_calla(self, monkeypatch):
        raro = "modelo_sin_familia_reconocible_v1"
        assert config.detectar_familia_comfy(raro) == ""
        monkeypatch.setitem(config._COMFY_FAMILIA_CARPETA,
                            config._norm_nombre_comfy(raro), "sdxl")
        assert config.detectar_familia_comfy(raro) == "sdxl"

    def test_las_carpetas_del_usuario_estan_mapeadas(self):
        # Las que existen de verdad en C:/IA/ComfyUI/models/checkpoints.
        for carpeta in ("sdxl", "sd15", "flux", "krea2", "zimage"):
            assert carpeta in config._COMFY_CARPETA_FAMILIA, (
                f"la carpeta {carpeta}/ nombra una familia conocida")

    def test_sin_pista_devuelve_cadena_vacia(self):
        assert config.detectar_familia_comfy("zzz_no_existe_nada") == ""
