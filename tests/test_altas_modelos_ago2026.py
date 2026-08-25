"""Candados de las altas de modelos de ago-2026 (petición del usuario):
LTX 2.5, MiniMax H3, Krea (grupo propio) — ComfyUI local — y Grok (xAI) +
Seedance 2.5 — nube.
"""
import config


class TestDeteccionComfyVideo:

    def test_ltxv_se_detecta_como_ltx(self):
        # Los ficheros LTX-Video suelen llamarse 'ltxv-…'; el token 'ltx'
        # (límite de palabra) no casaba con 'ltxv' → antes caían en imagen.
        assert config.clasificar_modelo_comfy("ltxv-2.5-19b") == "video"
        assert config.detectar_familia_comfy_video("ltxv-2.5-19b") == "ltx"

    def test_minimax_h3_es_video(self):
        n = "minimax_h3_fl2va_pruned_int8_convrot"
        assert config.clasificar_modelo_comfy(n) == "video"
        assert config.detectar_familia_comfy_video(n) == "minimax"
        assert config.get_model_specs(n) is not None

    def test_hailuo_es_video_minimax(self):
        assert config.detectar_familia_comfy_video("hailuo_h3_local") == "minimax"

    def test_text_projection_se_excluye(self):
        # Pieza suelta del pipeline LTX, no un modelo generable.
        assert "text_projection" in config._COMFY_EXCLUIR_TOKENS

    def test_swan_no_es_wan(self):
        # No romper el límite de palabra al añadir tokens nuevos.
        assert config.clasificar_modelo_comfy("swan_lake_style") == "imagen"


class TestLTX25Curado:

    def test_ltx_25_visible_en_comfyui_video(self):
        assert "LTX 2.5" in config.MODELOS_VIDEO_COMFYUI_FLAT

    def test_ltx_25_resuelve_specs_ltx(self):
        s = config.get_model_specs("LTX 2.5")
        assert s is not None and s.get("_comfy_familia") == "ltx"

    def test_ltx_25_en_base_protegida(self):
        # Va antes de _COMFY_BASE_VID → el auto-discovery no lo borra.
        base = config.GRUPOS_VIDEO_COMFYUI[: config._COMFY_BASE_VID]
        assert any("LTX 2.5" in ms for _, ms in base)


class TestGrokPlataforma:

    def test_grok_es_plataforma_propia(self):
        assert "Grok (xAI)" in config.PLATAFORMAS_IMAGEN
        assert "Grok (xAI)" in config.PLATAFORMAS_IMAGEN_LISTA
        assert "Grok (xAI)" in config.MODELOS_POR_PLATAFORMA_IMAGEN

    def test_grok_es_natural(self):
        assert config.PLATAFORMAS_IMAGEN["Grok (xAI)"] == "natural"

    def test_grok_imagen_resuelve_specs(self):
        s = config.get_image_model_specs("Grok Imagen")
        assert s is not None and s.get("is_natural") is True
        assert s.get("has_negative") is False

    def test_grok_imagen_en_el_combo(self):
        assert "Grok Imagen" in config.MODELOS_POR_PLATAFORMA_IMAGEN["Grok (xAI)"]


class TestSeedance25:

    def test_seedance_25_visible(self):
        assert "Seedance 2.5" in config.MODELOS_VIDEO_FLAT

    def test_seedance_25_specs(self):
        s = config.get_model_specs("Seedance 2.5")
        assert s is not None and s.get("vigente") is True
        assert s.get("has_audio") is True
