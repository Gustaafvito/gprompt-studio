"""Tests para gtypes.py — TypedDicts."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gtypes import (
    HistorialEntry, FavoritoEntry, PersonajeEntry,
    LoRAEntry, PlantillaEntry, Preferencias,
)


class TestTypedDicts:
    def test_historial_entry(self):
        entry: HistorialEntry = {
            "contenido": "un prompt",
            "fecha": "2026-01-01",
            "modo": "imagen",
            "modelo": "SeaArt",
            "plataforma": "SeaArt / Tensor.Art",
        }
        assert entry["contenido"] == "un prompt"
        assert entry["modo"] == "imagen"

    def test_favorito_entry(self):
        entry: FavoritoEntry = {
            "contenido": "test prompt",
            "fecha": "2026-01-01",
            "titulo": "Mi prompt",
        }
        assert entry["titulo"] == "Mi prompt"

    def test_personaje_entry(self):
        entry: PersonajeEntry = {
            "nombre": "Luna",
            "descripcion": "silver hair, blue eyes",
        }
        assert entry["nombre"] == "Luna"

    def test_lora_entry(self):
        entry: LoRAEntry = {
            "nombre": "Detail",
            "trigger": "add_detail",
            "descripcion": "enhances details",
            "familia": "SDXL",
        }
        assert entry["familia"] == "SDXL"

    def test_plantilla_entry(self):
        entry: PlantillaEntry = {
            "nombre": "Test",
            "modo": "imagen",
            "plataforma": "SeaArt",
            "modelo_img": "SeaArt Infinity",
            "modelo_vid": "",
            "modelo_aud": "",
            "ratio": "1:1",
            "estilos": ["Fotografía"],
            "nsfw": False,
            "destino": "Instagram",
            "brief": True,
        }
        assert entry["brief"] is True
        assert entry["ratio"] == "1:1"

    def test_preferencias(self):
        prefs: Preferencias = {
            "tema": "dark",
            "llm": "deepseek",
        }
        assert prefs["tema"] == "dark"
