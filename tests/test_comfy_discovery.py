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

    def test_imagen_flux_zimage_qwen(self):
        assert config.clasificar_modelo_comfy("flux-2-klein-9b-fp8") == "imagen"
        assert config.clasificar_modelo_comfy("z_image_bf16") == "imagen"
        assert config.clasificar_modelo_comfy("z_image_turbo_bf16") == "imagen"
        assert config.clasificar_modelo_comfy("qwen_image_edit_2509_fp8_e4m3fn") == "imagen"
        assert config.clasificar_modelo_comfy("512-inpainting-ema") == "imagen"

    def test_ideogram_es_imagen_local(self, tmp_path):
        # Ideogram 4 pasó a ser un modelo de imagen local real (jul-2026):
        # ya NO se excluye del escaneo y tiene familia + specs propias.
        root = _crear_install_comfy(tmp_path)
        hallados = config._escanear_comfy_root(root)
        assert any("ideogram" in m for m in hallados["imagen"])
        assert config.detectar_familia_comfy("ideogram4_fp8_transformer") == "ideogram"
        specs = config.comfy_image_specs("ideogram4_fp8_transformer")
        assert specs and specs["_comfy_familia"] == "ideogram"

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

    def test_qwen_con_negative(self):
        # A CFG 4 responde a negative (testing usuario).
        s = config.comfy_image_specs("qwen_image_edit_2509_fp8_e4m3fn")
        assert s["has_negative"] is True
        assert s.get("negative_sugerido")

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


class TestComfyWorkflowParams:
    """Parámetros del exportador 'Workflow ComfyUI' por familia."""

    def test_flux_es_unet(self):
        p = config.comfy_workflow_params("flux-2-klein-9b-fp8")
        assert p["arch"] == "unet"
        assert p["cfg"] == 3.5 and p["steps"] == 20
        assert p["scheduler"] == "simple"

    def test_sdxl_es_checkpoint(self):
        p = config.comfy_workflow_params("Juggernaut-XL_v9_RunDiffusionPhoto_v2")
        assert p["arch"] == "checkpoint"
        assert p["cfg"] == 6.5
        assert p["scheduler"] == "karras"

    def test_qwen_unet_con_clip_y_vae(self):
        p = config.comfy_workflow_params("qwen_image_edit_2509_fp8_e4m3fn")
        assert p["arch"] == "unet"
        assert p["clip"] and p["vae"]

    def test_turbo_reduce_pasos_y_cfg(self):
        p = config.comfy_workflow_params("z_image_turbo_bf16")
        assert p["steps"] <= 8
        assert p["cfg"] == 2.0

    def test_desconocido_usa_default_checkpoint(self):
        p = config.comfy_workflow_params("modelo_raro_xyz")
        assert p["arch"] == "checkpoint"
        assert "cfg" in p and "sampler" in p

    def test_override_familia_pony_por_nombre_no_evidente(self):
        # uberRealisticPornMerge es un merge PonyXL cuyo nombre (v23Final)
        # perdió el token 'pony' → override de familia. Debe salir con los
        # params de Pony (CFG 5, karras), no los genéricos de 'Otros'.
        assert config.detectar_familia_comfy("uberRealisticPornMerge_v23Final") == "pony"
        p = config.comfy_workflow_params("uberRealisticPornMerge_v23Final")
        assert p["cfg"] == 5.0 and p["scheduler"] == "karras"
        # Y comfy_image_specs deja de ser None → se registra como modelo destino.
        assert config.comfy_image_specs("uberRealisticPornMerge_v23Final") is not None

    def test_override_sd15_por_nombre_no_evidente(self):
        # Modelos SD 1.5 del inventario del usuario cuyo nombre no lleva token
        # de familia (auditoría 14-jul-2026): sin override caían en "Otros"
        # con params genéricos; deben salir como SD 1.5 (arch checkpoint,
        # dpmpp_2m/karras).
        for nombre in ("analogMadness_v70", "lazymixRealAmateur_v40",
                       "revAnimated_v2Pruned"):
            assert config.detectar_familia_comfy(nombre) == "sd15", nombre
            p = config.comfy_workflow_params(nombre)
            assert p["arch"] == "checkpoint" and p["sampler"] == "dpmpp_2m"

    def test_override_zimage_distilled_usa_unet(self):
        # zibBadmilkDistilled = Z-Image Base destilado. Sin override se cableaba
        # como CheckpointLoaderSimple; Z-Image necesita UNETLoader + CLIP/VAE.
        assert config.detectar_familia_comfy("zibBadmilkDistilled_v10") == "z_image"
        p = config.comfy_workflow_params("zibBadmilkDistilled_v10")
        assert p["arch"] == "unet" and p.get("clip") and p.get("vae")


class TestInventarioAgo2026:
    """Ampliación del inventario del usuario (ago-2026): checkpoints que caían
    en 'Otros' (prompt genérico) por no llevar token de familia en el nombre,
    más exclusión de modelos no-generativos. Familias confirmadas por el usuario.
    """

    def test_sd15_clasicos_sin_token(self):
        # Merges SD 1.5 famosos cuyo nombre no lleva '1.5'/'sd15'/'512'.
        for nombre in ("chilloutmix_NiPrunedFp32Fix", "epicrealism_naturalSin",
                       "majicmixRealistic_v1", "meinamix_v12Final",
                       "realisticVisionV60B1_v51HyperVAE",
                       "revAnimated_v2Rebirth", "cyberrealistic_v90"):
            assert config.detectar_familia_comfy(nombre) == "sd15", nombre
            assert config.comfy_image_specs(nombre)["is_natural"] is False

    def test_krea_es_familia_propia(self):
        # Krea (ago-2026): grupo propio 'krea', separado de Flux, aunque el
        # fichero lleve el token 'flux' ('flux1KreaDev…') — krea gana por orden.
        for nombre in ("krea2MuseByStable_v10TurboFp8",
                       "darkBeastINT8Convrot2_darkBeastKREA2FP8",
                       "krea2TurboNSFWAIO_v10", "flux1KreaDevFp8_v10"):
            assert config.detectar_familia_comfy(nombre) == "krea", nombre
            assert config.comfy_image_specs(nombre)["is_natural"] is True

    def test_chroma_sigue_en_flux(self):
        # 'chroma' permanece en Flux (des-destilado de Flux.1 schnell).
        assert config.detectar_familia_comfy("Chroma1-HD-fp8mixed") == "flux"

    def test_krea_turbo_pierde_negative(self):
        # Las variantes turbo/destiladas fuerzan has_negative=False.
        s = config.comfy_image_specs("krea2_turbo_fp8_scaled")
        assert s["_comfy_familia"] == "krea" and s["has_negative"] is False

    def test_krea_workflow_deja_clip_vae_en_blanco(self):
        # Los ficheros Krea son heterogéneos: el workflow no fuerza el CLIP/VAE
        # de Flux 2 (que no son los suyos); ComfyUI deja los dropdowns.
        p = config.comfy_workflow_params("krea2MuseByStable_v10TurboFp8")
        assert p["_comfy_familia"] == "krea"
        assert p.get("clip") == "" and p.get("vae") == ""

    def test_unstable_serie_es_flux_no_sdxl(self):
        # unstableEvolution corrige un falso positivo: 'xl' casaba dentro de
        # 't5xxl' → salía sdxl; el override lo devuelve a flux (T5xxl+Clip).
        assert config.detectar_familia_comfy("unstableEvolution_NF4VAEClipT5xxl") == "flux"
        assert config.detectar_familia_comfy("unstableDissolution_Fp8E4m3") == "flux"

    def test_snofs_flux_e_illust_illustrious(self):
        assert config.detectar_familia_comfy(
            "snofsSexNudesAndOtherFunStuff_v14Distilled") == "flux"
        assert config.detectar_familia_comfy("illustOccultSemi_v2") == "illustrious"

    def test_no_generativos_excluidos(self, tmp_path):
        # SUPIR (upscaler), hunyuan3d (malla 3D) y stable_cascade_stage_b/c
        # (piezas de pipeline) no sirven como destino de prompts.
        ckpt = tmp_path / "models" / "checkpoints"
        ckpt.mkdir(parents=True)
        for n in ("SUPIR-v0Q", "hunyuan3d-dit-v2-mv-turbo_fp16",
                  "stable_cascade_stage_b", "stable_cascade_stage_c",
                  "flux1-dev"):
            (ckpt / f"{n}.safetensors").write_text("x")
        hallados = config._escanear_comfy_root(tmp_path)
        todos = hallados["imagen"] + hallados["video"] + hallados["audio"]
        assert "flux1-dev" in todos  # los normales siguen apareciendo
        for excluido in ("SUPIR-v0Q", "hunyuan3d-dit-v2-mv-turbo_fp16",
                         "stable_cascade_stage_b", "stable_cascade_stage_c"):
            assert excluido not in todos, excluido


class TestAltasSep2026:
    """Altas guiadas una a una por el usuario (sep-2026): HiDream (familia
    propia), snofs Klein → Flux, Anima → Illustrious, FireRed/JoyAI → edición.
    """

    def test_hidream_familia_propia(self):
        s = config.comfy_image_specs("hidream_o1_image_dev_fp8_scaled")
        assert s is not None and s["_comfy_familia"] == "hidream"
        assert s["is_natural"] is True and s["has_negative"] is True
        # unet + CLIP/VAE en blanco (encoders propios, el usuario los elige).
        p = config.comfy_workflow_params("hidream_o1_image_dev_fp8_scaled")
        assert p["arch"] == "unet" and p.get("clip") == "" and p.get("vae") == ""

    def test_snofs_klein_es_flux(self):
        # snofs ya es Flux; 'klein' delata Flux.2 → flux. 'distilled' NO está en
        # los turbo-tokens, así que conserva negative (Flux.2 Klein lo acepta).
        s = config.comfy_image_specs("snofs_klein_9b_distilled_fp8")
        assert s["_comfy_familia"] == "flux" and s["has_negative"] is True

    def test_anima_es_illustrious_por_override(self):
        # Va por override, NO por token: 'anima' colisionaría con anima_pencil-XL.
        for n in ("anima-base-v1.0", "anima-preview3-base"):
            assert config.detectar_familia_comfy(n) == "illustrious", n

    def test_anima_no_rompe_anima_pencil_xl(self):
        # El SDXL anima_pencil sigue siendo SDXL (no lo captura el override).
        assert config.detectar_familia_comfy("anima_pencil-XL") == "sdxl"
        assert config.detectar_familia_comfy("animaPencilXL_v500") == "sdxl"

    def test_firered_y_joyai_son_edicion(self):
        for n in ("FireRed-Image-Edit-1.1-Q3_K_M",
                  "FireRed-Image-Edit-1.1-transformer",
                  "joyai_image_edit_int8_convrot"):
            s = config.comfy_image_specs(n)
            assert s["_comfy_familia"] == "edit", n
            # Edición por instrucciones: prosa natural, SIN negative.
            assert s["is_natural"] is True and s["has_negative"] is False

    def test_edit_no_captura_qwen_image_edit(self):
        # El edit local va por override específico → qwen_image_edit sigue qwen.
        assert config.detectar_familia_comfy("qwen_image_edit_2509_fp8_e4m3fn") == "qwen"


class TestConstruirWorkflowComfy:
    """El workflow sale en formato UI de ComfyUI (nodes[] + links[]) con el
    loader correcto por arquitectura."""

    @staticmethod
    def _build(modelo, lora=""):
        from modules.tools_analysis import ToolsAnalysisService
        return ToolsAnalysisService._construir_workflow_comfy("a cat", "blurry", modelo, lora)

    @staticmethod
    def _tipos(wf):
        return {n["type"] for n in wf["nodes"]}

    def test_formato_ui_valido(self):
        # Estructura que ComfyUI acepta al hacer Load/Paste en el canvas.
        wf = self._build("flux-2-klein-9b-fp8")
        for k in ("last_node_id", "last_link_id", "nodes", "links", "version"):
            assert k in wf
        assert isinstance(wf["nodes"], list) and isinstance(wf["links"], list)
        # Todo link referencia nodos existentes.
        ids = {n["id"] for n in wf["nodes"]}
        for lk in wf["links"]:
            assert lk[1] in ids and lk[3] in ids

    def test_sdxl_usa_checkpoint_loader(self):
        t = self._tipos(self._build("Juggernaut-XL_v9_RunDiffusionPhoto_v2"))
        assert "CheckpointLoaderSimple" in t and "UNETLoader" not in t

    def test_flux_usa_unet_loader(self):
        t = self._tipos(self._build("flux-2-klein-9b-fp8"))
        assert {"UNETLoader", "CLIPLoader", "VAELoader"} <= t
        assert "CheckpointLoaderSimple" not in t

    def test_ksampler_usa_cfg_de_familia(self):
        wf = self._build("flux-2-klein-9b-fp8")
        ks = next(n for n in wf["nodes"] if n["type"] == "KSampler")
        # widgets_values: [seed, control, steps, cfg, sampler, scheduler, denoise]
        assert ks["widgets_values"][3] == 3.5
        assert ks["widgets_values"][5] == "simple"

    def test_prompt_va_en_clip_encode(self):
        wf = self._build("Juggernaut-XL_v9_RunDiffusionPhoto_v2")
        textos = [n["widgets_values"][0] for n in wf["nodes"]
                  if n["type"] == "CLIPTextEncode"]
        assert "a cat" in textos and "blurry" in textos


class TestWorkflowConLora:
    """El workflow inserta un LoraLoader (formato UI) cuando hay LoRA activo."""

    @staticmethod
    def _build(modelo, lora=""):
        from modules.tools_analysis import ToolsAnalysisService
        return ToolsAnalysisService._construir_workflow_comfy("a cat", "blurry", modelo, lora)

    def test_sin_lora_no_hay_loraloader(self):
        wf = self._build("Juggernaut-XL_v9_RunDiffusionPhoto_v2")
        assert "LoraLoader" not in {n["type"] for n in wf["nodes"]}

    def test_con_lora_checkpoint_encadena(self):
        wf = self._build("Juggernaut-XL_v9_RunDiffusionPhoto_v2", "MiLora")
        lora = next(n for n in wf["nodes"] if n["type"] == "LoraLoader")
        assert lora["widgets_values"][0] == "MiLora.safetensors"
        # Existe un link Checkpoint(MODEL) -> LoraLoader.model
        chk = next(n for n in wf["nodes"] if n["type"] == "CheckpointLoaderSimple")
        assert any(lk[1] == chk["id"] and lk[3] == lora["id"] for lk in wf["links"])
        # Y un link LoraLoader(MODEL) -> KSampler.model
        ks = next(n for n in wf["nodes"] if n["type"] == "KSampler")
        assert any(lk[1] == lora["id"] and lk[3] == ks["id"] for lk in wf["links"])

    def test_con_lora_unet_encadena_desde_unetloader(self):
        wf = self._build("flux-2-klein-9b-fp8", "FluxLora")
        t = {n["type"] for n in wf["nodes"]}
        assert "LoraLoader" in t and "UNETLoader" in t
        unet = next(n for n in wf["nodes"] if n["type"] == "UNETLoader")
        lora = next(n for n in wf["nodes"] if n["type"] == "LoraLoader")
        assert any(lk[1] == unet["id"] and lk[3] == lora["id"] for lk in wf["links"])
