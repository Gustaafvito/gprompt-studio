"""Tests del auto-discovery de ComfyUI: clasificador por nombre + escaneo
recursivo de checkpoints/diffusion_models/unet.

Casos basados en un inventario real del usuario (carpetas checkpoints +
diffusion_models con modelos de imagen, vídeo y audio mezclados, más una
subcarpeta FLUX2/).
"""
import config


# ──────────────────────────────────────────────────────────────────
# clasificar_modelo_comfy
# ──────────────────────────────────────────────────────────────────
class TestClasificarModeloComfy:

    def test_imagen_sdxl(self):
        assert config.clasificar_modelo_comfy("Juggernaut-XL_v9_RunDiffusionPhoto_v2") == "imagen"
        assert config.clasificar_modelo_comfy("RealVisXL_V5.0_fp16") == "imagen"
        assert config.clasificar_modelo_comfy("juggernautXL_ragnarokBy") == "imagen"

    def test_imagen_flux_zimage_qwen_ideogram(self):
        assert config.clasificar_modelo_comfy("flux-2-klein-9b-fp8") == "imagen"
        assert config.clasificar_modelo_comfy("z_image_bf16") == "imagen"
        assert config.clasificar_modelo_comfy("z_image_turbo_bf16") == "imagen"
        assert config.clasificar_modelo_comfy("qwen_image_edit_2509_fp8_e4m3fn") == "imagen"
        assert config.clasificar_modelo_comfy("ideogram4_fp8_transformer") == "imagen"
        assert config.clasificar_modelo_comfy("512-inpainting-ema") == "imagen"

    def test_video(self):
        assert config.clasificar_modelo_comfy("wan2.2_i2v_high_noise_14B_fp8_scaled") == "video"
        assert config.clasificar_modelo_comfy("wan2.2_i2v_low_noise_14B_fp8_scaled") == "video"
        assert config.clasificar_modelo_comfy("ltx-2.3-22b-dev-fp8") == "video"
        assert config.clasificar_modelo_comfy("svd") == "video"

    def test_audio(self):
        # MusicGen/Stable Audio siguen siendo audio; ACE-Step va excluido del
        # escaneo (ver test_ace_excluido), no clasifica en la app.
        assert config.clasificar_modelo_comfy("musicgen_medium") == "audio"
        assert config.clasificar_modelo_comfy("stable_audio_open") == "audio"

    def test_ace_excluido(self, tmp_path):
        # ACE-Step (audio, el usuario no lo usa desde la herramienta) se
        # excluye del escaneo: ni imagen ni audio.
        root = _crear_install_comfy(tmp_path)
        hallados = config._escanear_comfy_root(root)
        todos = hallados["imagen"] + hallados["video"] + hallados["audio"]
        assert not any("acestep" in m for m in todos)

    def test_vacio_y_none(self):
        assert config.clasificar_modelo_comfy("") == "imagen"
        assert config.clasificar_modelo_comfy(None) == "imagen"

    def test_tokens_ambiguos_no_casan_dentro_de_palabras(self):
        # "wan"/"mochi"/"svd" pegados a otra letra NO son vídeo:
        # wanostyle (LoRA Wano/One Piece), swan, mochi en nombres anime.
        assert config.clasificar_modelo_comfy("wanostyle_offset") == "imagen"
        assert config.clasificar_modelo_comfy("blackSwan_mix_v3") == "imagen"
        assert config.clasificar_modelo_comfy("mochimix_anime_v2") == "imagen"

    def test_tokens_ambiguos_casan_con_digitos_y_separadores(self):
        # Dígitos y separadores sí son límite válido (convención real).
        assert config.clasificar_modelo_comfy("wan21_t2v_1.3B") == "video"
        assert config.clasificar_modelo_comfy("Wan2_1-I2V-14B") == "video"
        assert config.clasificar_modelo_comfy("svd_xt_1_1") == "video"


# ──────────────────────────────────────────────────────────────────
# _escanear_comfy_root / escanear_modelos_comfyui
# ──────────────────────────────────────────────────────────────────
def _crear_install_comfy(tmp_path):
    """Crea una estructura ComfyUI falsa con el inventario real del usuario."""
    ckpt = tmp_path / "models" / "checkpoints"
    diff = tmp_path / "models" / "diffusion_models"
    flux2 = diff / "FLUX2"
    for d in (ckpt, diff, flux2):
        d.mkdir(parents=True, exist_ok=True)

    checkpoints = [
        "512-inpainting-ema", "Juggernaut-XL_v9_RunDiffusionPhoto_v2",
        "RealVisXL_V5.0_fp16", "ideogram4_fp8_transformer",
        "juggernautXL_ragnarokBy", "ltx-2.3-22b-dev-fp8", "svd",
        "wan2.2_i2v_high_noise_14B_fp8_scaled", "zImageBase_base",
    ]
    diffusion = [
        "acestep_v1.5_base", "acestep_v1.5_xl_sft_bf16", "flux-2-klein-9b-fp8",
        "flux-2-klein-9b-kv-fp8", "flux-2-klein-base-4b-fp8",
        "ideogram4_fp8_transformer", "qwen_image_edit_2509_fp8_e4m3fn",
        "wan2.2_i2v_high_noise_14B_fp8_scaled",
        "wan2.2_i2v_low_noise_14B_fp8_scaled", "z_image_bf16", "z_image_turbo_bf16",
    ]
    for n in checkpoints:
        (ckpt / f"{n}.safetensors").write_text("x")
    for n in diffusion:
        (diff / f"{n}.safetensors").write_text("x")
    # Subcarpeta: duplica un flux que ya está arriba (debe deduplicarse).
    (flux2 / "flux-2-klein-9b-fp8.safetensors").write_text("x")
    return tmp_path


class TestEscanearComfyRoot:

    def test_captura_imagen_de_diffusion_models(self, tmp_path):
        # El bug original: estos modelos vivían en diffusion_models y se perdían.
        root = _crear_install_comfy(tmp_path)
        hallados = config._escanear_comfy_root(root)
        for m in ("flux-2-klein-base-4b-fp8", "z_image_bf16",
                  "z_image_turbo_bf16", "qwen_image_edit_2509_fp8_e4m3fn"):
            assert m in hallados["imagen"]

    def test_clasifica_video_sin_audio_ni_ace(self, tmp_path):
        root = _crear_install_comfy(tmp_path)
        hallados = config._escanear_comfy_root(root)
        assert "ltx-2.3-22b-dev-fp8" in hallados["video"]
        # ACE-Step excluido: no aparece en ninguna categoría.
        assert not hallados["audio"]
        assert not any("acestep" in m for m in hallados["imagen"])

    def test_excluye_ficheros_sin_prompt(self, tmp_path):
        # refiner (2ª pasada), SVD (ignora el texto), transformer_only (pieza
        # de pipeline) e inpainting (necesita máscara+imagen, no genera desde
        # texto) no sirven en un generador de prompts.
        root = _crear_install_comfy(tmp_path)
        ckpt = root / "models" / "checkpoints"
        (ckpt / "sd_xl_refiner_1.0_0.9vae.safetensors").write_text("x")
        (ckpt / "ltx-2.3-22b-dev_transformer_only_mxfp8.safetensors").write_text("x")
        hallados = config._escanear_comfy_root(root)
        todos = hallados["imagen"] + hallados["video"] + hallados["audio"]
        assert "svd" not in todos
        assert "sd_xl_refiner_1.0_0.9vae" not in todos
        assert "ltx-2.3-22b-dev_transformer_only_mxfp8" not in todos
        # 512-inpainting-ema está en el fixture y debe quedar excluido.
        assert "512-inpainting-ema" not in todos

    def test_subcarpeta_se_escanea_y_deduplica(self, tmp_path):
        # FLUX2/flux-2-klein-9b-fp8 duplica el de diffusion_models → 1 sola vez.
        root = _crear_install_comfy(tmp_path)
        hallados = config._escanear_comfy_root(root)
        assert hallados["imagen"].count("flux-2-klein-9b-fp8") == 1

    def test_orden_case_insensitive(self, tmp_path):
        root = _crear_install_comfy(tmp_path)
        hallados = config._escanear_comfy_root(root)
        assert hallados["imagen"] == sorted(hallados["imagen"], key=str.lower)

    def test_descripcion_local_en_specs(self):
        # Los checkpoints del inventario anteponen su descripción curada
        # al best_for genérico de la familia (ES y EN).
        s = config.comfy_image_specs("RealVisXL_V5.0_fp16")
        assert s["best_for"].startswith("Fotorrealismo extremo")
        assert s["best_for_en"].startswith("Extreme photorealism")
        v = config.comfy_video_specs("wan2.2_i2v_high_noise_14B_fp8_scaled")
        assert v["best_for"].startswith("Wan 2.2 i2v 14B")
        # Un checkpoint desconocido mantiene el best_for de familia intacto.
        s2 = config.comfy_image_specs("juggernautXL_inventado_v99")
        assert not s2["best_for"].startswith("Retratos")


class TestEscanearModelosComfyui:

    def test_ruta_inexistente_devuelve_none(self):
        assert config.escanear_modelos_comfyui("/ruta/que/no/existe") == (None, None)

    def test_devuelve_grupos_img_y_vid(self, tmp_path):
        root = _crear_install_comfy(tmp_path)
        grupos_img, grupos_vid = config.escanear_modelos_comfyui(str(root))
        assert grupos_img and grupos_img[0][0] == "── ComfyUI Local ──"
        assert grupos_vid and grupos_vid[0][0] == "── ComfyUI Video ──"
        # Los FLUX.2 de diffusion_models están ahora en imagen.
        assert any("flux-2-klein" in m for m in grupos_img[0][1])


# ──────────────────────────────────────────────────────────────────
# detectar_familia_comfy / comfy_image_specs / fallback en getter
# ──────────────────────────────────────────────────────────────────
class TestDetectarFamiliaComfy:

    def test_familias_de_los_modelos_reales(self):
        casos = {
            "flux-2-klein-9b-fp8": "flux",
            "z_image_bf16": "z_image",
            "z_image_turbo_bf16": "z_image",
            "qwen_image_edit_2509_fp8_e4m3fn": "qwen",
            "ideogram4_fp8_transformer": "ideogram",
            "Juggernaut-XL_v9_RunDiffusionPhoto_v2": "sdxl",
            "RealVisXL_V5.0_fp16": "sdxl",
            "juggernautXL_ragnarokBy": "sdxl",
            "512-inpainting-ema": "sd15",
        }
        for nombre, fam in casos.items():
            assert config.detectar_familia_comfy(nombre) == fam, nombre

    def test_pony_e_illustrious(self):
        assert config.detectar_familia_comfy("ponyDiffusionV6XL") == "pony"
        assert config.detectar_familia_comfy("Illustrious-XL-v2") == "illustrious"
        assert config.detectar_familia_comfy("noobaiXL_vpred10") == "illustrious"

    def test_desconocido_vacio(self):
        assert config.detectar_familia_comfy("modelo_raro_inventado") == ""
        assert config.detectar_familia_comfy("") == ""


class TestComfyImageSpecs:

    def test_flux2_es_natural_con_negative(self):
        # Flux 2 Klein (local): CFG real ~3.5, SÍ usa negative (testing usuario).
        s = config.comfy_image_specs("flux-2-klein-base-4b-fp8")
        assert s["is_natural"] is True
        assert s["has_negative"] is True
        assert s.get("negative_sugerido")

    def test_qwen_e_ideogram_con_negative(self):
        # A CFG 4 responden a negative (testing usuario).
        for m in ("qwen_image_edit_2509_fp8_e4m3fn", "ideogram4_fp8_transformer"):
            s = config.comfy_image_specs(m)
            assert s["has_negative"] is True, m
            assert s.get("negative_sugerido"), m

    def test_zimage_local_es_natural_puro_sin_formato_hibrido(self):
        # LOCAL: lenguaje natural puro, sin el formato híbrido con tag-preamble
        # (el híbrido queda solo en la spec curada de SeaArt Z-Image-Base).
        s = config.comfy_image_specs("z_image_bf16")
        assert s["is_natural"] is True
        assert s["has_negative"] is True
        assert "formato_bloques" not in s

    def test_sdxl_es_tagbased_con_negative(self):
        s = config.comfy_image_specs("Juggernaut-XL_v9_RunDiffusionPhoto_v2")
        assert s["is_natural"] is False
        assert s["has_negative"] is True
        assert "dpmpp_2m" in s["sampler_recomendado"]
        assert s.get("negative_sugerido")

    def test_zimage_turbo_fuerza_sin_negative(self):
        base = config.comfy_image_specs("z_image_bf16")
        turbo = config.comfy_image_specs("z_image_turbo_bf16")
        # Z-Image base es natural; ambos sin negative, pero turbo lo fuerza.
        assert turbo["has_negative"] is False
        assert turbo["is_natural"] is True
        assert base["is_natural"] is True

    def test_pony_lleva_trigger_words(self):
        s = config.comfy_image_specs("ponyRealism_v22")
        assert "score_9" in s["trigger_words"]

    def test_has_negative_siempre_presente(self):
        # _inyectar_specs_formato indexa specs["has_negative"] directamente.
        for n in ("flux1-dev", "Juggernaut-XL_v9", "ponyV6", "512-inpainting-ema"):
            assert "has_negative" in config.comfy_image_specs(n)

    def test_max_chars_por_tipo(self):
        assert config.comfy_image_specs("flux1-dev")["max_chars"] == 1500
        assert config.comfy_image_specs("Juggernaut-XL_v9")["max_chars"] == 500

    def test_desconocido_devuelve_none(self):
        assert config.comfy_image_specs("modelo_raro_inventado") is None


class TestGetImageModelSpecsFallback:

    def test_modelo_comfy_usa_synthetic(self):
        # No está en el JSON curado → cae al sintético por familia.
        s = config.get_image_model_specs("flux-2-klein-9b-fp8")
        assert s is not None
        assert s["_comfy_familia"] == "flux"

    def test_modelo_desconocido_no_comfy_devuelve_none(self):
        assert config.get_image_model_specs("xyz_modelo_inexistente_123") is None

    def test_curado_tiene_prioridad(self):
        # Un modelo del JSON curado no debe quedar marcado como sintético.
        ds = config._get_dataset("MODEL_SPECS_IMAGEN")
        if ds:
            nombre = next(iter(ds))
            s = config.get_image_model_specs(nombre)
            assert "_comfy_familia" not in s


class TestComfyImageSpecsBilingue:

    def test_todas_las_familias_tienen_best_for_en(self):
        for fam, spec in config._COMFY_SPECS_FAMILIA.items():
            assert spec.get("best_for_en"), fam
            assert spec.get("best_for"), fam


# ──────────────────────────────────────────────────────────────────
# comfy_video_specs (LTX / Wan / SVD / Hunyuan / CogVideo / Mochi)
# ──────────────────────────────────────────────────────────────────
# Claves que _inyectar_specs_video indexa directamente: deben existir SIEMPRE.
_VIDEO_REQUIRED = (
    "max_chars", "prompt_formula", "prompt_ejemplo", "best_for",
    "has_audio", "audio_desc", "has_negative",
)


class TestDetectarFamiliaComfyVideo:

    def test_familias_de_los_modelos_reales(self):
        casos = {
            "ltx-2.3-22b-dev-fp8": "ltx",
            "wan2.2_i2v_high_noise_14B_fp8_scaled": "wan",
            "wan2.2_i2v_low_noise_14B_fp8_scaled": "wan",
            "svd": "svd",
            "svd_xt_1_1": "svd",
        }
        for nombre, fam in casos.items():
            assert config.detectar_familia_comfy_video(nombre) == fam, nombre

    def test_extras(self):
        assert config.detectar_familia_comfy_video("hunyuanvideo_720_fp8") == "hunyuan"
        assert config.detectar_familia_comfy_video("CogVideoX-5b") == "cogvideo"
        assert config.detectar_familia_comfy_video("mochi_preview_bf16") == "mochi"

    def test_desconocido_vacio(self):
        assert config.detectar_familia_comfy_video("juggernautXL_v9") == ""
        assert config.detectar_familia_comfy_video("") == ""

    def test_tokens_ambiguos_no_casan_dentro_de_palabras(self):
        assert config.detectar_familia_comfy_video("wanostyle_offset") == ""
        assert config.detectar_familia_comfy_video("blackSwan_mix") == ""
        assert config.detectar_familia_comfy_video("mochimix_anime") == ""


class TestComfyVideoSpecs:

    def test_todas_las_familias_completas_y_bilingues(self):
        for fam, spec in config._COMFY_SPECS_FAMILIA_VIDEO.items():
            for k in _VIDEO_REQUIRED:
                assert k in spec, f"{fam} sin {k}"
            assert spec.get("best_for_en"), fam

    def test_ltx_video_audio_negative(self):
        s = config.comfy_video_specs("ltx-2.3-22b-dev-fp8")
        assert s["has_audio"] is True and s["audio_desc"]
        assert s["has_negative"] is True
        assert s["_comfy_familia"] == "ltx"

    def test_wan_sin_audio_con_negative(self):
        s = config.comfy_video_specs("wan2.2_i2v_high_noise_14B_fp8_scaled")
        assert s["has_audio"] is False
        assert s["has_negative"] is True

    def test_svd_sin_texto_sin_negative(self):
        s = config.comfy_video_specs("svd")
        assert s["has_negative"] is False and s["has_audio"] is False
        assert "image-to-video" in s["best_for"].lower() or "image-to-video" in s["prompt_formula"].lower()

    def test_audio_desc_vacio_si_no_audio(self):
        # _inyectar_specs_video hace `if has_audio and audio_desc` — coherencia.
        for fam, spec in config._COMFY_SPECS_FAMILIA_VIDEO.items():
            if not spec["has_audio"]:
                assert spec["audio_desc"] == "", fam

    def test_desconocido_devuelve_none(self):
        assert config.comfy_video_specs("modelo_raro_inventado") is None


class TestGetModelSpecsVideoFallback:

    def test_ltx_usa_synthetic(self):
        s = config.get_model_specs("ltx-2.3-22b-dev-fp8")
        assert s is not None and s.get("_comfy_familia") == "ltx"

    def test_curado_tiene_prioridad(self):
        ds = config._get_dataset("MODEL_SPECS")
        if ds:
            nombre = next(iter(ds))
            s = config.get_model_specs(nombre)
            assert "_comfy_familia" not in s

    def test_desconocido_no_video_devuelve_none(self):
        assert config.get_model_specs("xyz_inexistente_999") is None
