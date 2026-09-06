"""Sora fuera de los selectores.

OpenAI apaga la API de Sora 2 el 24-sep-2026 y NO publica modelo sucesor
(la columna de reemplazo recomendado está vacía en su tabla de deprecación).
Se retira de los catálogos seleccionables por decisión del usuario el
06-sep-2026, y la plataforma "Sora / Veo" pasa a llamarse "Veo / Gemini",
que es lo que realmente contiene.

Las specs siguen en data/model_specs_*.json a propósito: el historial del
usuario contiene prompts generados con Sora y deben seguir resolviéndose.
"""
import json
from pathlib import Path

import config


class TestSoraNoSeleccionable:

    def test_ninguna_plataforma_ofrece_sora(self):
        for catalogo in (config.MOTORES_VIDEO, config.MODELOS_POR_PLATAFORMA_IMAGEN):
            for plataforma, modelos in catalogo.items():
                assert "Sora" not in plataforma, plataforma
                for m in modelos:
                    assert "Sora" not in m, f"{plataforma} → {m}"

    def test_la_plataforma_se_llama_veo_gemini(self):
        assert "Veo / Gemini" in config.MOTORES_VIDEO
        assert "Sora / Veo" not in config.MOTORES_VIDEO

    def test_veo_gemini_conserva_sus_dos_modelos(self):
        """Quitar Sora no puede haberse llevado por delante a sus compañeros."""
        modelos = config.MOTORES_VIDEO["Veo / Gemini"]
        assert "Veo 3.1" in modelos
        assert "Gemini Omni Flash" in modelos

    def test_el_catalogo_json_tampoco(self):
        p = Path(config.__file__).parent / "data" / "modelos_grupos.json"
        crudo = p.read_text(encoding="utf-8")
        assert "Sora" not in crudo


class TestElHistorialSigueResolviendo:
    """Las specs se conservan aunque el modelo ya no se pueda elegir."""

    def test_las_specs_de_sora_siguen_ahi(self):
        base = Path(config.__file__).parent / "data"
        vid = json.loads((base / "model_specs_video.json").read_text(encoding="utf-8"))
        img = json.loads((base / "model_specs_imagen.json").read_text(encoding="utf-8"))
        assert "Sora2 Video" in vid, "el historial antiguo dejaría de resolverse"
        assert "Sora2 Image" in img
