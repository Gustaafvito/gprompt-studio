"""Familias del gestor de LoRAs y su compatibilidad con el modelo activo.

09-oct-2026: el usuario entrena sus LoRAs con G-Entrena Studio, que trabaja
con Anima, Krea 2, LTX, MiniMax H3, Qwen Image y Z Image. El gestor solo
tenía Z Image: un LoRA de Anima (Lyra, trigger lyr4) solo cabía como «Otra»
y salía siempre con «⚠️ familia distinta», porque la app tampoco sabía
reconocer un modelo Anima.

Los nombres de modelo de estos tests son los REALES: los del catálogo y los
checkpoints locales de ComfyUI del usuario.
"""
import pytest

from modules.ui_footer import familia_modelo_para_lora, lora_compatible


class TestLasFamiliasDelGestor:

    def test_estan_las_de_g_entrena(self):
        from modules.windows import FAMILIAS_LORA
        for familia in ("Anima", "Krea 2", "LTX", "MiniMax H3", "Qwen Image",
                        "Z Image"):
            assert familia in FAMILIAS_LORA

    def test_en_orden_alfabetico(self):
        from modules.windows import FAMILIAS_LORA
        assert list(FAMILIAS_LORA) == sorted(FAMILIAS_LORA, key=str.lower)

    def test_cada_familia_reconoce_algun_modelo(self):
        # Una familia que ningún modelo devuelve sale SIEMPRE con «familia
        # distinta»: es justo el fallo que tenía Anima.
        from modules.windows import FAMILIAS_LORA
        un_modelo = {
            "Anima": "Anima", "Flux": "FLUX.1 [dev]",
            "Illustrious": "Illustrious XL V3.6", "Krea 2": "Krea-2",
            "LTX": "ltx-2.3-22b-distilled-Q4_0", "MiniMax H3": "MiniMax H3",
            "Pony": "ponyDiffusionV6XL", "Qwen Image": "Qwen Image 2.1",
            "SD15": "sd15_base", "SD3.5": "SD 3.5 Large", "SDXL": "Juggernaut XL",
            "Z Image": "Z Image Turbo",
        }
        for familia in FAMILIAS_LORA:
            assert lora_compatible(familia, un_modelo[familia],
                                   "video" if familia in ("LTX", "MiniMax H3")
                                   else "imagen") is True, familia


class TestSeReconoceElModelo:

    @pytest.mark.parametrize("modelo,familia", [
        ("Anima", "anima"),
        ("anima-base-v1.0", "anima"),
        ("anima-preview3-base", "anima"),
        ("Krea-2", "krea 2"),
        ("krea2_turbo_fp8_scaled", "krea 2"),
        ("Krea-2-Turbo-Q4_K_M", "krea 2"),
        ("snofs_krea2_raw_v13", "krea 2"),
        ("Qwen Image 2.1", "qwen image"),
        ("qwen_image_2.1_int8_convrot", "qwen image"),
        ("LTX-2.5-Distilled-Q3_K_M", "ltx"),
        ("MiniMax H3 Max", "minimax h3"),
        ("minimax_h3_ref2va_pruned_int8_convrot", "minimax h3"),
        ("Minimax-h3_Singularity_ref2va_Pruned_v1.3_int8", "minimax h3"),
        ("Z-Image-Base", "z image"),
    ])
    def test_las_familias_de_g_entrena(self, modelo, familia):
        assert familia_modelo_para_lora(modelo) == familia

    @pytest.mark.parametrize("modelo,familia", [
        # Llevan «anima» o «krea» en el nombre y NO son de esas familias.
        ("anima_pencil-XL", None),            # SDXL sin token reconocible
        ("Wan2.2-Animate-14B-Q5_K_M", None),
        ("FLUX.1 Krea dev", "flux"),
        ("flux1-krea-dev_fp8_scaled", "flux"),
        # Sparkle H3 es de SeaArt: no consta que comparta base con MiniMax H3.
        ("SeaArt Sparkle H3", None),
    ])
    def test_sin_falsos_positivos(self, modelo, familia):
        assert familia_modelo_para_lora(modelo) == familia


class TestLaCompatibilidad:

    def test_lyra_con_anima_es_compatible(self):
        assert lora_compatible("Anima", "anima-base-v1.0", "imagen") is True
        assert lora_compatible("Anima", "Anima", "imagen") is True

    def test_lyra_con_otro_modelo_no(self):
        assert lora_compatible("Anima", "Illustrious XL V3.6", "imagen") is False

    def test_las_de_siempre_no_cambian(self):
        assert lora_compatible("Pony", "Juggernaut XL", "imagen") is True
        assert lora_compatible("Z Image", "Z Image Turbo", "imagen") is True
        assert lora_compatible("Flux", "Z Image Turbo", "imagen") is False

    def test_sin_familia_no_se_juzga(self):
        assert lora_compatible("", "Anima", "imagen") is None
        assert lora_compatible("—", "Anima", "imagen") is None

    def test_en_video_se_juzgan_los_lora_de_video(self):
        assert lora_compatible("MiniMax H3", "MiniMax H3 Open", "video") is True
        assert lora_compatible("LTX", "MiniMax H3", "video") is False

    def test_en_video_un_lora_de_imagen_sigue_sin_veredicto(self):
        # Antes, en vídeo no se juzgaba nada; con los de imagen sigue así.
        assert lora_compatible("Anima", "MiniMax H3", "video") is None

    def test_en_audio_nada(self):
        assert lora_compatible("LTX", "Suno v5.5", "audio") is None
