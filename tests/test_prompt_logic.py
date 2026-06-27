"""Tests unitarios para modules/prompt_logic.py.

Todas las funciones son puras (sin widgets Tk).  Los tests que necesitan
que `get_image_model_specs` / `get_model_specs` devuelvan valores concretos
usan `unittest.mock.patch` para no depender del estado de los JSONs.
"""
import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.prompt_logic import (
    contexto_loras_personaje,
    contexto_modelo_para_ideas,
    debe_mostrar_negatives,
    es_comfyui_turbo,
    is_natural_mode,
)

# ══════════════════════════════════════════════════════════════════
# is_natural_mode
# ══════════════════════════════════════════════════════════════════

class TestIsNaturalMode:

    # ── modo audio ─────────────────────────────────────────────────
    def test_audio_siempre_natural(self):
        assert is_natural_mode("audio", "Suno", "") is True

    def test_audio_ignora_plataforma(self):
        assert is_natural_mode("audio", "SeaArt / Tensor.Art", "Z Image Turbo") is True

    # ── modo video ─────────────────────────────────────────────────
    def test_video_plataforma_natural(self):
        # Kling AI → "natural" en PLATAFORMAS_VIDEO
        assert is_natural_mode("video", "Kling AI", "") is True

    def test_video_plataforma_sd(self):
        # SeaArt Video → "sd" en PLATAFORMAS_VIDEO
        assert is_natural_mode("video", "SeaArt Video", "") is False

    def test_video_plataforma_desconocida_default_natural(self):
        # Plataforma no registrada: default "natural"
        assert is_natural_mode("video", "PlataformaFake", "") is True

    # ── modo imagen — plataformas sin modelos (natural / sd) ───────
    def test_imagen_dola_es_natural(self):
        assert is_natural_mode("imagen", "Dola", "") is True

    def test_imagen_chatgpt_es_natural(self):
        assert is_natural_mode("imagen", "ChatGPT / GPT Image", "") is True

    def test_imagen_seaart_segun_modelo(self):
        # SeaArt / Tensor.Art está en _PLAT_CON_MODELOS, consulta el spec del modelo
        # Sin modelo → cae al default de la plataforma ("sd" → False)
        assert is_natural_mode("imagen", "SeaArt / Tensor.Art", "") is False

    def test_imagen_plataforma_desconocida_default_sd(self):
        # Plataforma no registrada: default "sd"
        assert is_natural_mode("imagen", "PlataformaFake", "") is False

    # ── modo imagen — plataforma con modelos, spec is_natural ──────
    def test_imagen_seaart_modelo_is_natural_true(self):
        # SeaArt Infinity tiene is_natural=True en el JSON real
        result = is_natural_mode("imagen", "SeaArt / Tensor.Art", "SeaArt Infinity")
        assert result is True

    def test_imagen_seaart_modelo_is_natural_false(self):
        # Z Image Turbo tiene is_natural=False en el JSON real
        result = is_natural_mode("imagen", "SeaArt / Tensor.Art", "Z Image Turbo")
        assert result is False

    def test_imagen_plat_con_modelos_modelo_vacio(self):
        # ComfyUI con modelo vacío → cae al default de la plataforma ("sd")
        assert is_natural_mode("imagen", "ComfyUI / A1111 / Forge", "") is False

    def test_imagen_plat_con_modelos_separador(self):
        # Si modelo es un separador ("── ...") se trata como sin modelo
        assert is_natural_mode("imagen", "ComfyUI / A1111 / Forge", "── FLUX ──") is False

    def test_imagen_plat_con_modelos_spec_none_cae_a_plataforma(self):
        # Modelo inexistente → specs=None → cae al default de la plataforma
        with patch("modules.prompt_logic.get_image_model_specs", return_value=None):
            result = is_natural_mode("imagen", "SeaArt / Tensor.Art", "ModeloFake")
        # SeaArt / Tensor.Art → "sd" → False
        assert result is False

    def test_imagen_plat_con_modelos_spec_sin_is_natural_cae_a_plataforma(self):
        # Spec existe pero no tiene la clave "is_natural"
        with patch("modules.prompt_logic.get_image_model_specs", return_value={"has_negative": True}):
            result = is_natural_mode("imagen", "SeaArt / Tensor.Art", "ModeloSinFlag")
        assert result is False


# ══════════════════════════════════════════════════════════════════
# es_comfyui_turbo
# ══════════════════════════════════════════════════════════════════

class TestEsComfyuiTurbo:

    def test_comfyui_con_flux_schnell(self):
        assert es_comfyui_turbo("ComfyUI / A1111 / Forge", "FLUX.1 Schnell") is True

    def test_comfyui_con_z_image_turbo(self):
        assert es_comfyui_turbo("ComfyUI / A1111 / Forge", "Z Image Turbo") is True

    def test_comfyui_con_sdxl_turbo(self):
        assert es_comfyui_turbo("ComfyUI / A1111 / Forge", "SDXL Turbo") is True

    def test_comfyui_con_realities_edge(self):
        assert es_comfyui_turbo("ComfyUI / A1111 / Forge", "Realities Edge XL Turbo V7") is True

    def test_a1111_con_modelo_turbo(self):
        # "A1111" también está en la detección
        assert es_comfyui_turbo("A1111", "FLUX.1 Schnell") is True

    def test_forge_con_modelo_turbo(self):
        assert es_comfyui_turbo("Forge", "SDXL Turbo") is True

    def test_seaart_con_modelo_turbo_es_false(self):
        # SeaArt no es ComfyUI/A1111/Forge
        assert es_comfyui_turbo("SeaArt / Tensor.Art", "Z Image Turbo") is False

    def test_comfyui_con_modelo_normal_es_false(self):
        # ComfyUI pero sin modelo Turbo
        assert es_comfyui_turbo("ComfyUI / A1111 / Forge", "CyberRealistic Flux") is False

    def test_plataforma_vacia_es_false(self):
        assert es_comfyui_turbo("", "FLUX.1 Schnell") is False

    def test_modelo_vacio_es_false(self):
        assert es_comfyui_turbo("ComfyUI / A1111 / Forge", "") is False

    def test_ambos_vacios_es_false(self):
        assert es_comfyui_turbo("", "") is False

    # Nombres de fichero reales del auto-discovery local (lo que rompía antes:
    # no coincidían con los strings exactos del catálogo).
    def test_filename_z_image_turbo_bf16(self):
        assert es_comfyui_turbo("ComfyUI / A1111 / Forge", "z_image_turbo_bf16 (Turbo)") is True

    def test_filename_flux_schnell(self):
        assert es_comfyui_turbo("ComfyUI / A1111 / Forge", "flux1-schnell") is True

    def test_filename_sdxl_turbo(self):
        assert es_comfyui_turbo("ComfyUI / A1111 / Forge", "sd_xl_turbo_1.0_fp16") is True

    def test_filename_lightning(self):
        assert es_comfyui_turbo("ComfyUI / A1111 / Forge", "dreamshaperXL_lightning") is True

    def test_filename_lcm(self):
        assert es_comfyui_turbo("Forge", "dreamshaper_v7_lcm") is True

    def test_filename_hyper_sd(self):
        assert es_comfyui_turbo("ComfyUI / A1111 / Forge", "Hyper-SDXL-1step") is True

    def test_filename_modelo_normal_full_steps_es_false(self):
        # Checkpoint normal de muchos pasos → SÍ soporta negative/pesos.
        assert es_comfyui_turbo("ComfyUI / A1111 / Forge", "juggernautXL_v9") is False
        assert es_comfyui_turbo("ComfyUI / A1111 / Forge", "realvisxlV50_fp16") is False


# ══════════════════════════════════════════════════════════════════
# debe_mostrar_negatives
# ══════════════════════════════════════════════════════════════════

class TestDebeMostrarNegatives:

    # ── modo audio ─────────────────────────────────────────────────
    def test_audio_siempre_false(self):
        assert debe_mostrar_negatives("audio", "Suno", "", "Suno v5.5") is False

    def test_audio_ignora_plataforma_y_modelos(self):
        assert debe_mostrar_negatives("audio", "SeaArt / Tensor.Art", "Z Image Turbo", "x") is False

    # ── modo video ─────────────────────────────────────────────────
    def test_video_modelo_con_negative_true(self):
        # Happy Horse tiene has_negative=True en el JSON (Kling 3.0 NO usa negativo)
        result = debe_mostrar_negatives("video", "SeaArt Video", "", "Happy Horse")
        assert result is True

    def test_video_modelo_con_negative_false(self):
        # Kling 01 Video Model tiene has_negative=False en el JSON
        result = debe_mostrar_negatives("video", "Kling AI", "", "Kling 01 Video Model")
        assert result is False

    def test_video_modelo_desconocido_cae_a_plataforma_sd(self):
        # Modelo no registrado → cae a PLATAFORMAS_VIDEO default
        # SeaArt Video → "sd" → True
        result = debe_mostrar_negatives("video", "SeaArt Video", "", "ModeloFake")
        assert result is True

    def test_video_modelo_desconocido_plataforma_natural(self):
        # Modelo no registrado → Kling AI → "natural" (pero PLATAFORMAS_VIDEO["Kling AI"] = "natural")
        # Devuelve: PLATAFORMAS_VIDEO.get("Kling AI","sd") == "sd" → False
        result = debe_mostrar_negatives("video", "Kling AI", "", "ModeloFake")
        assert result is False

    def test_video_modelo_vacio_cae_a_plataforma(self):
        with patch("modules.prompt_logic.get_model_specs", return_value=None):
            result = debe_mostrar_negatives("video", "SeaArt Video", "", "")
        assert result is True

    # ── modo imagen ────────────────────────────────────────────────
    def test_imagen_plataforma_natural_sin_modelos(self):
        # Dola → "natural" → False
        assert debe_mostrar_negatives("imagen", "Dola", "", "") is False

    def test_imagen_plataforma_sd_sin_modelos(self):
        # SeaArt / Tensor.Art con modelo vacío → cae a default "sd" → True
        assert debe_mostrar_negatives("imagen", "SeaArt / Tensor.Art", "", "") is True

    def test_imagen_comfyui_turbo_siempre_false(self):
        # ComfyUI + FLUX.1 Schnell → es_comfyui_turbo → False
        result = debe_mostrar_negatives(
            "imagen", "ComfyUI / A1111 / Forge", "FLUX.1 Schnell", ""
        )
        assert result is False

    def test_imagen_comfyui_turbo_z_image_false(self):
        result = debe_mostrar_negatives(
            "imagen", "ComfyUI / A1111 / Forge", "Z Image Turbo", ""
        )
        assert result is False

    def test_imagen_seaart_modelo_con_negative_true(self):
        # Z Image Turbo en SeaArt (no es turbo en SeaArt) → has_negative=True
        result = debe_mostrar_negatives(
            "imagen", "SeaArt / Tensor.Art", "Z Image Turbo", ""
        )
        assert result is True

    def test_imagen_seaart_modelo_is_natural_no_negative(self):
        # SeaArt Infinity → has_negative=False en el JSON
        result = debe_mostrar_negatives(
            "imagen", "SeaArt / Tensor.Art", "SeaArt Infinity", ""
        )
        assert result is False

    def test_imagen_plat_con_modelos_separador_cae_a_plataforma(self):
        # Separador tratado como sin modelo → cae a default de la plataforma
        result = debe_mostrar_negatives(
            "imagen", "SeaArt / Tensor.Art", "── FLUX ──", ""
        )
        assert result is True  # SeaArt → "sd" → True

    def test_imagen_plat_con_modelos_spec_none_cae_a_plataforma(self):
        with patch("modules.prompt_logic.get_image_model_specs", return_value=None):
            result = debe_mostrar_negatives(
                "imagen", "SeaArt / Tensor.Art", "ModeloFake", ""
            )
        assert result is True  # default "sd"

    def test_imagen_plataforma_desconocida_default_sd(self):
        result = debe_mostrar_negatives("imagen", "PlataformaFake", "", "")
        assert result is True


# ══════════════════════════════════════════════════════════════════
# contexto_loras_personaje
# ══════════════════════════════════════════════════════════════════

class TestContextoLorasPersonaje:

    def test_sin_loras_ni_personaje_devuelve_vacio(self):
        result = contexto_loras_personaje([], [], "", "")
        assert result == ""

    def test_sin_loras_ni_personaje_nombres_vacios(self):
        result = contexto_loras_personaje([], [], "")
        assert result == ""

    def test_solo_nombres_loras_sin_rasgos(self):
        result = contexto_loras_personaje([], ["Asuka Evangelion"], "")
        assert "Asuka Evangelion" in result
        assert "LoRA" in result or "LoRa" in result or "lora" in result.lower()

    def test_rasgos_loras_presentes(self):
        result = contexto_loras_personaje(
            ["1girl, red plug suit, anime"], ["Asuka Evangelion"], ""
        )
        assert "1girl, red plug suit, anime" in result
        assert "PERSONAJE/ESTÉTICA del LoRA" in result

    def test_rasgos_multiples_unidos_por_pipe(self):
        rasgos = ["1girl, red suit", "blue eyes, short hair"]
        result = contexto_loras_personaje(rasgos, ["Asuka", "Rei"], "")
        assert "1girl, red suit | blue eyes, short hair" in result

    def test_solo_personaje_activo(self):
        result = contexto_loras_personaje([], [], "Rei Ayanami")
        assert "Rei Ayanami" in result
        assert "PERSONAJE adicional" in result

    def test_loras_y_personaje_juntos(self):
        result = contexto_loras_personaje(
            ["1girl, white hair"], ["SomeLoRA"], "Rei Ayanami"
        )
        assert "1girl, white hair" in result
        assert "Rei Ayanami" in result

    def test_sufijo_intro_personalizado(self):
        result = contexto_loras_personaje([], ["MiLoRA"], "", sufijo_intro="el prompt")
        assert "el prompt" in result

    def test_sufijo_intro_default_es_el_resultado(self):
        result = contexto_loras_personaje([], ["MiLoRA"], "")
        assert "el resultado" in result

    def test_contiene_bloque_escenas_sugeridas(self):
        result = contexto_loras_personaje([], ["MiLoRA"], "")
        assert "ESCENAS/ESCENARIOS/ACCIONES" in result

    def test_nombres_loras_multiples_en_lista(self):
        result = contexto_loras_personaje([], ["LoRA_A", "LoRA_B", "LoRA_C"], "")
        assert "LoRA_A" in result
        assert "LoRA_B" in result
        assert "LoRA_C" in result

    def test_rasgos_tienen_prioridad_sobre_nombres(self):
        # Con rasgos, la rama de nombres no debe aparecer
        result = contexto_loras_personaje(
            ["red hair, blue eyes"], ["SomeLoRA"], ""
        )
        assert "PERSONAJE/ESTÉTICA del LoRA" in result
        # La rama de "LoRA(s) activo(s):" (sin rasgos) NO debe aparecer
        assert "LoRA(s) activo(s):" not in result


# ══════════════════════════════════════════════════════════════════
# contexto_modelo_para_ideas
# ══════════════════════════════════════════════════════════════════

class TestContextoModeloParaIdeas:

    def test_modelo_vacio_devuelve_vacio(self):
        assert contexto_modelo_para_ideas("imagen", "", None) == ""
        assert contexto_modelo_para_ideas("imagen", "", {}) == ""

    def test_modelo_separador_devuelve_vacio(self):
        assert contexto_modelo_para_ideas("imagen", "── FLUX ──", None) == ""

    def test_modelo_sin_specs_contiene_nombre(self):
        result = contexto_modelo_para_ideas("imagen", "CyberRealistic Flux", None)
        assert "CyberRealistic Flux" in result

    def test_modelo_con_best_for_incluye_texto(self):
        specs = {"best_for": "Ideal para fotorrealismo profesional"}
        result = contexto_modelo_para_ideas("imagen", "CyberRealistic Flux", specs)
        assert "Ideal para fotorrealismo profesional" in result

    def test_best_for_se_trunca_a_220_chars(self):
        specs = {"best_for": "X" * 300}
        result = contexto_modelo_para_ideas("imagen", "AlgunModelo", specs)
        # 220 X's deben aparecer, pero no 300
        assert "X" * 220 in result
        assert "X" * 221 not in result

    def test_modo_imagen_incluye_aviso_estilo(self):
        result = contexto_modelo_para_ideas("imagen", "AlgunModelo", {})
        assert "anime" in result or "fotorrealista" in result or "3D" in result

    def test_modo_audio_incluye_aviso_musical(self):
        result = contexto_modelo_para_ideas("audio", "Suno v5.5", {})
        assert "musical" in result or "género" in result or "canción" in result

    def test_modo_audio_no_contiene_texto_imagen(self):
        result = contexto_modelo_para_ideas("audio", "Suno v5.5", {})
        # El aviso de imagen habla de "anime" o "fotográficas"; el de audio no
        assert "anime" not in result

    def test_modo_video_incluye_aviso_estilo(self):
        result = contexto_modelo_para_ideas("video", "Kling 3.0", {})
        assert "anime" in result or "fotorrealista" in result or "3D" in result

    def test_specs_none_no_rompe(self):
        result = contexto_modelo_para_ideas("imagen", "ModeloX", None)
        assert "ModeloX" in result
        # Sin best_for, no debe aparecer "Ideal para"
        assert "Ideal para" not in result

    def test_specs_sin_best_for_no_rompe(self):
        result = contexto_modelo_para_ideas("imagen", "ModeloX", {"has_negative": True})
        assert "ModeloX" in result

    def test_best_for_vacio_no_aparece(self):
        specs = {"best_for": ""}
        result = contexto_modelo_para_ideas("imagen", "ModeloX", specs)
        assert "Ideal para:" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
