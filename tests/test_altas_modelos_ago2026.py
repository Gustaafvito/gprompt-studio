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


class TestWan30:
    """Wan 3.0 y Wan 3.0 Prime — vídeo multimodal de Alibaba vía SeaArt."""

    def test_wan_30_y_prime_visibles(self):
        assert "Wan 3.0" in config.MODELOS_VIDEO_FLAT
        assert "Wan 3.0 Prime" in config.MODELOS_VIDEO_FLAT

    def test_wan_30_en_grupo_wan(self):
        # Ambos cuelgan de la familia "── Wan ──", no de "Otros Motores".
        wan = next(ms for cab, ms in config.GRUPOS_VIDEO if cab.strip("─ ") == "Wan")
        assert "Wan 3.0" in wan and "Wan 3.0 Prime" in wan

    def test_wan_30_specs_audio_y_negativo(self):
        # Verificado contra el panel real de SeaArt (get_model_params):
        # ambos tienen audio nativo Y prompt negativo.
        for n in ("Wan 3.0", "Wan 3.0 Prime"):
            s = config.get_model_specs(n)
            assert s is not None and s.get("vigente") is True
            assert s.get("has_audio") is True
            assert s.get("has_negative") is True

    def test_wan_30_tope_1080p_prime_sube_a_4k(self):
        # Panel real: Wan 3.0 estándar tope 1080P; Prime añade 2K/4K.
        base = config.get_model_specs("Wan 3.0")
        assert "1080p" in base["modos_gen"]
        assert not any(m in ("2K", "4K") for m in base["modos_gen"])
        prime = config.get_model_specs("Wan 3.0 Prime")
        assert "4K" in prime["modos_gen"] and "2K" in prime["modos_gen"]

    def test_wan_30_duraciones_rango_completo(self):
        # Panel real: 5–15s (paso 1) + 20/25/30s = 14 opciones.
        s = config.get_model_specs("Wan 3.0")
        assert s["duraciones"][0] == "5s" and s["duraciones"][-1] == "30s"
        assert len(s["duraciones"]) == 14


class TestAltasVideoSep2026:
    """Modelos de vídeo SeaArt añadidos desde las capturas del catálogo del
    usuario (sep-2026): 19 fichas nuevas en 5 grupos.
    """

    NUEVOS = [
        "StarDream 2.5", "Character Reference", "Vidu Q3 Reference",
        "SeaArt Sono W3", "SeaArt Sono W3 Prime", "SeaArt Sparkle H3",
        "SeaArt Sparkle H3 Max", "SeaArt SonoVision 2.0", "SeaArt Opera Refer",
        "SeaArt Spark Refer", "SeaArt Clip Refer", "SeaArt Clip Remake",
        "SeaArt Ultra Remix Video", "SeaArt Spicy Video 22", "SeaArt Spicy Video 27",
        "MiniMax H3", "MiniMax H3 Max", "MiniMax H3 Open", "Kling O1",
    ]

    def test_todos_visibles_y_con_spec(self):
        for n in self.NUEVOS:
            assert n in config.MODELOS_VIDEO_FLAT, n
            assert config.get_model_specs(n) is not None, n

    def test_familia_minimax_existe(self):
        cabs = [c.strip("─ ") for c, _ in config.GRUPOS_VIDEO]
        assert "MiniMax" in cabs

    def test_familia_sono_w3_lleva_audio(self):
        for n in ("SeaArt Sono W3", "SeaArt Sono W3 Prime", "MiniMax H3"):
            assert config.get_model_specs(n)["has_audio"] is True, n
