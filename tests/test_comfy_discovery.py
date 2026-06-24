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
        assert config.clasificar_modelo_comfy("acestep_v1.5_base") == "audio"
        assert config.clasificar_modelo_comfy("acestep_v1.5_xl_sft_bf16") == "audio"

    def test_vacio_y_none(self):
        assert config.clasificar_modelo_comfy("") == "imagen"
        assert config.clasificar_modelo_comfy(None) == "imagen"


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

    def test_clasifica_video_y_audio(self, tmp_path):
        root = _crear_install_comfy(tmp_path)
        hallados = config._escanear_comfy_root(root)
        assert "svd" in hallados["video"]
        assert "ltx-2.3-22b-dev-fp8" in hallados["video"]
        assert "acestep_v1.5_base" in hallados["audio"]

    def test_subcarpeta_se_escanea_y_deduplica(self, tmp_path):
        # FLUX2/flux-2-klein-9b-fp8 duplica el de diffusion_models → 1 sola vez.
        root = _crear_install_comfy(tmp_path)
        hallados = config._escanear_comfy_root(root)
        assert hallados["imagen"].count("flux-2-klein-9b-fp8") == 1

    def test_orden_case_insensitive(self, tmp_path):
        root = _crear_install_comfy(tmp_path)
        hallados = config._escanear_comfy_root(root)
        assert hallados["imagen"] == sorted(hallados["imagen"], key=str.lower)


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
