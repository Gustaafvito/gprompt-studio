"""FLUX 3 Image Klein (SeaArt y ComfyUI) y Krea 3 (SeaArt), 17-oct-2026.

Black Forest Labs publicó FLUX 3 Image Klein con un aviso: no usarlo nunca
sin su «prompt upsampler», un Qwen3.5-9B afinado que convierte la petición
corta en el caption largo con el que se entrenó el modelo. La app no lleva
ese modelo, pero sí sus instrucciones: con el formato 'flux3' el LLM de la
app hace de upsampler con los dos system prompts oficiales, literales.

En local, FLUX 3 no es Flux 2: otro encoder (Qwen3-VL 4B con CLIPLoader de
tipo flux3), sin guía en el destilado. Antes caía en la familia «flux» y
el workflow salía con el CLIP y el tipo de Flux 2. El autor tiene la Base
con el nombre viejo (flux3_image_klein_int8_convrot) y el destilado con el
nuevo (flux3-image-klein-int8-convrot), y cada uno lleva su muestreo.
"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import config
import prompts
from modules.comfy_export import construir_workflow_comfy
from modules.prompts_inyeccion import PromptsInyeccionService

RAIZ = Path(__file__).resolve().parent.parent
DESTILADO = "flux3-image-klein-int8-convrot"
BASE_VIEJA = "flux3_image_klein_int8_convrot"


def _var(valor):
    return SimpleNamespace(get=lambda: valor)


def _inyectar(modelo):
    app = SimpleNamespace(combo_modelo_imagen=_var(modelo),
                          familia_estilo_var=_var("Auto"))
    app.footer = app
    return PromptsInyeccionService(app)._inyectar_specs_imagen("SYS")


class TestFamiliaLocal:

    @pytest.mark.parametrize("nombre", [
        DESTILADO, BASE_VIEJA, "flux3-image-klein-base-bf16",
        "flux3_image_klein_sd_int8_convrot", "flux-3-image-klein-Q4_K_M",
    ])
    def test_los_ficheros_de_flux3_tienen_familia_propia(self, nombre):
        assert config.detectar_familia_comfy(nombre) == "flux3"

    def test_flux2_sigue_en_flux(self):
        assert config.detectar_familia_comfy("flux-2-klein-9b-fp8") == "flux"
        assert config.detectar_familia_comfy("flux1-dev") == "flux"

    @pytest.mark.parametrize("nombre, base", [
        (DESTILADO, False),
        ("flux3-image-klein-bf16", False),
        ("flux3-image-klein-base-int8-convrot", True),
        # Con guion bajo, la Base no llevaba «base» y el destilado llevaba «sd».
        (BASE_VIEJA, True),
        ("flux3_image_klein_sd_int8_convrot", False),
    ])
    def test_distingue_la_base_del_destilado(self, nombre, base):
        assert config.flux3_es_base(nombre) is base

    def test_muestreo_de_cada_variante(self):
        d = config.comfy_workflow_params(DESTILADO)
        b = config.comfy_workflow_params(BASE_VIEJA)
        assert (d["steps"], d["cfg"]) == (16, 1.0)
        assert (b["steps"], b["cfg"]) == (50, 3.5)
        for p in (d, b):
            assert (p["sampler"], p["scheduler"]) == ("er_sde", "simple")

    def test_el_workflow_carga_su_encoder_y_su_vae(self):
        wf = construir_workflow_comfy("A caption", "", DESTILADO)
        nodos = {n["type"]: n["widgets_values"] for n in wf["nodes"]}
        assert nodos["UNETLoader"][0] == DESTILADO + ".safetensors"
        assert nodos["CLIPLoader"] == ["qwen3vl_4b_int8_convrot.safetensors", "flux3"]
        assert nodos["VAELoader"] == ["flux2-vae.safetensors"]

    def test_ficha_sin_negative_y_con_el_formato_del_upsampler(self):
        s = config.comfy_image_specs(DESTILADO)
        assert s["formato_bloques"] == "flux3" and not s["has_negative"]
        assert s["best_for"].startswith("Klein destilado")
        assert config.comfy_image_specs(BASE_VIEJA)["best_for"].startswith("Klein Base")

    def test_la_familia_tiene_cabecera(self):
        assert config._COMFY_FAMILIA_LABELS["flux3"] == "FLUX 3"


class TestFichasSeaArt:

    def _ficha(self, nombre):
        return config.get_image_model_specs(nombre)

    def test_flux3_con_el_panel_de_seaart(self):
        s = self._ficha("Flux.3 Image Klein")
        assert s["formato_bloques"] == "flux3" and not s["has_negative"]
        assert s["max_chars"] == 2000
        assert (s["max_imagenes"], s["max_imagenes_referencia"]) == (8, 3)
        assert (s["pasos"], s["cfg"]) == (15, 1.0)

    def test_krea3_con_el_panel_de_seaart(self):
        s = self._ficha("Krea 3")
        assert s["is_natural"] and not s["has_negative"]
        assert s["max_chars"] == 2000
        assert (s["max_imagenes"], s["max_imagenes_referencia"]) == (8, 6)
        # Los 11 formatos del panel; 4:5, 5:4 y 9:21 no son canónicos y van
        # al final, en orden lexicográfico (candado de test_config).
        assert len(s["ratios"]) == 11
        assert s["ratios"][-3:] == ["4:5", "5:4", "9:21"]

    @pytest.mark.parametrize("modelo, grupo", [
        ("Flux.3 Image Klein", "── Familia FLUX ──"),
        ("Krea 3", "── Krea (en SeaArt) ──"),
    ])
    def test_en_su_grupo_y_en_orden(self, modelo, grupo):
        grupos = dict(json.loads((RAIZ / "data" / "modelos_grupos.json")
                                 .read_text(encoding="utf-8"))["imagen"])
        assert modelo in grupos[grupo]
        assert grupos[grupo] == sorted(grupos[grupo], key=str.lower)


class TestElUpsamplerOficial:

    def test_los_textos_son_los_de_bfl(self):
        # Se copiaron tal cual de system_prompts.json; si alguien los
        # «mejora», deja de ser lo que BFL entrenó.
        assert prompts.REGLAS_FLUX3_T2I.strip().startswith(
            "You are the prompt upsampler of a text-to-image model.")
        assert prompts.REGLAS_FLUX3_I2I.strip().startswith(
            "You are the prompt upsampler of an image-editing model.")
        # El \n del texto de edición es literal (barra y ene), no un salto.
        assert "with line breaks as \\n," in prompts.REGLAS_FLUX3_I2I

    @pytest.mark.parametrize("modelo", ["Flux.3 Image Klein", DESTILADO])
    def test_el_llm_recibe_las_dos_instrucciones_y_sin_negative(self, modelo):
        out = _inyectar(modelo)
        assert prompts.REGLAS_FLUX3_T2I in out
        assert prompts.REGLAS_FLUX3_I2I in out
        assert "PROMPT: [" in out
        assert "NEGATIVE PROMPT: [" not in out

    def test_longitud_de_la_guia_oficial(self):
        assert "OBJETIVO DE LONGITUD: 100-300 palabras" in _inyectar("Flux.3 Image Klein")
        assert "OBJETIVO DE LONGITUD: 100-350 palabras" in _inyectar(DESTILADO)

    @pytest.mark.parametrize("modelo", ["Flux.3 Image Klein", "Krea 3", "Qwen Image 2.1"])
    def test_el_texto_del_cartel_no_se_traduce(self, modelo):
        # Primera prueba real (17-oct-2026): «un cartel en la puerta que dice
        # ABERTO» salió como "OPEN". El refuerzo «SIEMPRE en INGLÉS» va el
        # último y ganaba a la regla de BFL; ahora lleva la excepción.
        out = _inyectar(modelo)
        idioma = out.index("IDIOMA DEL PROMPT")
        excepcion = out.index("EXCEPCIÓN: el texto que debe salir ESCRITO en la imagen")
        assert excepcion > idioma
        assert 'el prompt dice "ABIERTO", no "OPEN"' in out

    def test_otros_modelos_no_lo_reciben(self):
        assert prompts.REGLAS_FLUX3_T2I not in _inyectar("Krea 3")
        assert prompts.REGLAS_FLUX3_T2I not in _inyectar("Flux.2 Klein")

    def test_el_aviso_de_licencia_esta_en_notice(self):
        notice = (RAIZ / "NOTICE").read_text(encoding="utf-8")
        assert "flux-3-image-klein-pup" in notice and "Black Forest Labs" in notice
