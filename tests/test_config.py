"""Tests para config — helpers y funciones utility."""
import pytest
import sys
import os

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
