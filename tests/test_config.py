"""Tests para config — helpers y funciones utility."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestConfigHelpers:
    def test_es_separador_true(self):
        from config import es_separador
        assert es_separador("── SeaArt ──") is True
        assert es_separador("──") is True

    def test_es_separador_false(self):
        from config import es_separador
        assert es_separador("SeaArt Infinity") is False
        assert es_separador("Z Image Turbo") is False

    def test_get_model_specs(self):
        from config import get_model_specs
        specs = get_model_specs("Kling 3.0")
        assert specs is not None
        assert specs["nota"] == 4.5
        assert specs["has_negative"] is True
        assert specs["has_audio"] is True
        assert specs["max_chars"] == 2500

    def test_get_model_specs_unknown(self):
        from config import get_model_specs
        assert get_model_specs("Modelo Inexistente") is None

    def test_get_image_model_specs(self):
        from config import get_image_model_specs
        specs = get_image_model_specs("SeaArt Infinity")
        assert specs is not None
        assert specs["is_natural"] is True
        assert specs["has_negative"] is False

    def test_get_image_model_specs_unknown(self):
        from config import get_image_model_specs
        assert get_image_model_specs("Modelo Fake") is None

    def test_get_prompt_template(self):
        from config import get_prompt_template
        tmpl = get_prompt_template("Z Image Turbo")
        assert tmpl is not None
        assert "positive_base" in tmpl
        assert "negative_base" in tmpl

    def test_get_prompt_template_unknown(self):
        from config import get_prompt_template
        assert get_prompt_template("Modelo SinTemplate") is None


class TestModelosVigentes:
    """Filtro de modelos de imagen: solo se muestran los 'vigente': true."""

    def test_es_modelo_imagen_vigente(self):
        from config import es_modelo_imagen_vigente
        # Vigentes marcados en el JSON
        assert es_modelo_imagen_vigente("Z-Image-Base") is True
        assert es_modelo_imagen_vigente("Nano Banana") is True
        assert es_modelo_imagen_vigente("Reve 2.0") is True
        # Un modelo NO vigente
        assert es_modelo_imagen_vigente("SD 3.5 Large Turbo") is False
        # Inexistente
        assert es_modelo_imagen_vigente("Modelo Fake") is False

    def test_flat_solo_contiene_vigentes(self):
        from config import MODELOS_IMAGEN_FLAT, es_modelo_imagen_vigente, es_separador
        modelos = [m for m in MODELOS_IMAGEN_FLAT if not es_separador(m)]
        assert modelos, "no debería quedar vacío"
        assert all(es_modelo_imagen_vigente(m) for m in modelos)
        # El no-vigente no aparece; el vigente sí
        assert "SD 3.5 Large Turbo" not in modelos
        assert "Z-Image-Base" in modelos

    def test_master_conserva_todos(self):
        from config import MODELOS_IMAGEN_FLAT, MODELOS_IMAGEN_FLAT_TODOS, es_separador
        todos = [m for m in MODELOS_IMAGEN_FLAT_TODOS if not es_separador(m)]
        vis = [m for m in MODELOS_IMAGEN_FLAT if not es_separador(m)]
        assert len(todos) > len(vis)         # el master sigue completo
        assert "SD 3.5 Large Turbo" in todos    # el no-vigente sigue en el master

    def test_no_quedan_grupos_vacios(self):
        from config import GRUPOS_IMAGEN_VIGENTES
        for cabecera, modelos in GRUPOS_IMAGEN_VIGENTES:
            assert modelos, f"grupo vacío: {cabecera}"

    def test_familia_flux_tiene_estilos(self):
        # La familia FLUX debe ofrecer el toggle "Estilo" como las demás.
        from config import ESTILOS_POR_FAMILIA, detectar_familia
        assert "flux" in ESTILOS_POR_FAMILIA
        assert ESTILOS_POR_FAMILIA["flux"][0] == "Auto"
        # Detección por nombre y por pertenencia al grupo (Mimic Neo sin 'flux')
        assert detectar_familia("CyberRealistic Flux") == "flux"
        assert detectar_familia("Midjourney Mimic Neo") == "flux"
        assert detectar_familia("Z-Image-Base") == "z_image"

    def test_grupos_orden_alfabetico_case_insensitive(self):
        # Todos los grupos de imagen deben quedar en orden alfabético sin
        # distinguir mayúsculas (los nombres en minúscula no caen al final).
        from config import GRUPOS_IMAGEN
        for cabecera, modelos in GRUPOS_IMAGEN:
            assert modelos == sorted(modelos, key=str.lower), f"desordenado: {cabecera}"
        # Caso concreto: lyh_anime_Flux antes de Midjourney/XE en Familia FLUX
        flux = next(ms for cab, ms in GRUPOS_IMAGEN if "FLUX" in cab.upper())
        assert flux.index("lyh_anime_Flux") < flux.index("Midjourney Mimic Neo")

    def test_modelo_sin_nota_no_rompe(self):
        # Real Vision - FLUX no tiene nota (None). Debe seguir vigente y los
        # puntos que usan nota deben tolerarlo (label 's/n', sort -> 0).
        from config import es_modelo_imagen_vigente, get_image_model_specs
        s = get_image_model_specs("Real Vision - FLUX")
        assert s["nota"] is None
        assert es_modelo_imagen_vigente("Real Vision - FLUX") is True
        # patrones de consumo que antes petaban / mostraban "None"
        assert (s.get("nota") or "s/n") == "s/n"
        assert float(s.get("nota") or 0) == 0.0
