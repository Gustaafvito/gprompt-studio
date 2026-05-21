"""Tests para persistence.py con escrituras atómicas."""
import pytest
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestAtomicWrites:
    """Verifica que _guardar use escritura atómica (tmp + rename)."""

    def test_no_tmp_files_after_save(self, tmp_path, monkeypatch):
        store = _setup_store(tmp_path, monkeypatch)
        store.agregar_historial({"contenido": "test", "fecha": "2026-01-01"})
        hist_path = tmp_path / "historial.json"
        assert hist_path.exists()
        assert not (tmp_path / "historial.json.tmp").exists()
        data = json.loads(hist_path.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["contenido"] == "test"

    def test_corrupt_json_returns_empty(self, tmp_path, monkeypatch):
        (tmp_path / "historial.json").write_text("{corrupto", encoding="utf-8")
        store = _setup_store(tmp_path, monkeypatch)
        assert store.historial == []


class TestDataStoreCRUD:
    @pytest.fixture
    def store(self, tmp_path, monkeypatch):
        return _setup_store(tmp_path, monkeypatch)

    def test_agregar_y_limpiar_historial(self, store):
        store.limpiar_historial()
        store.agregar_historial({"contenido": "prompt1", "fecha": "2026-01-01"})
        store.agregar_historial({"contenido": "prompt2", "fecha": "2026-01-02"})
        assert len(store.historial) == 2
        assert store.historial[0]["contenido"] == "prompt2"
        store.limpiar_historial()
        assert len(store.historial) == 0

    def test_personajes(self, store):
        store.guardar_personaje("Luna", "silver hair, blue eyes")
        assert store.descripcion_personaje("Luna") == "silver hair, blue eyes"
        assert "Luna" in store.nombres_personajes()
        store.guardar_personaje("Luna", "updated desc")
        assert store.descripcion_personaje("Luna") == "updated desc"
        store.borrar_personaje(0)
        assert store.descripcion_personaje("Luna") == ""

    def test_loras(self, store):
        store.guardar_lora("Detail", "add_detail", "enhances details", "SDXL")
        assert store.trigger_lora("Detail") == "add_detail"
        assert "Detail" in store.nombres_loras()

    def test_plantillas(self, store):
        store.plantillas.clear()
        plantilla = {"nombre": "Test", "modo": "imagen", "ratio": "1:1"}
        store.guardar_plantilla(plantilla)
        assert store.obtener_plantilla("Test") is not None
        assert store.obtener_plantilla("Test")["ratio"] == "1:1"
        store.borrar_plantilla("Test")
        assert store.obtener_plantilla("Test") is None

    def test_historial_max_100(self, store):
        store.limpiar_historial()
        for i in range(150):
            store.agregar_historial({"contenido": f"prompt {i}", "fecha": "2026-01-01"})
        assert len(store.historial) <= 100


class TestPreferences:
    def test_save_load_preferences(self, tmp_path, monkeypatch):
        s = _setup_store(tmp_path, monkeypatch)
        prefs = {"tema": "dark", "llm": "deepseek"}
        s.guardar_preferencias(prefs)
        loaded = s.cargar_preferencias()
        assert loaded["tema"] == "dark"
        assert loaded["llm"] == "deepseek"

    def test_corrupt_preferences_returns_empty(self, tmp_path, monkeypatch):
        (tmp_path / "preferencias.json").write_text("not json", encoding="utf-8")
        s = _setup_store(tmp_path, monkeypatch)
        assert s.cargar_preferencias() == {}


# ── Helpers ───────────────────────────────────────────────────────

_NAMES = ["historial", "favoritos", "personajes", "plantillas",
          "loras", "preferencias", "estrellas", "paletas"]


def _setup_store(tmp_path, monkeypatch):
    """Crea DataStore con paths temporales parcheando ARCHIVOS en ambos módulos."""
    from pathlib import Path
    import config
    tmp_files = {name: tmp_path / f"{name}.json" for name in _NAMES}

    # Parchear en config
    for k, v in tmp_files.items():
        monkeypatch.setitem(config.ARCHIVOS, k, v)

    # Parchear también en persistence (que tiene su propia referencia por el 'from config import ARCHIVOS')
    import persistence
    monkeypatch.setattr(persistence, "ARCHIVOS", tmp_files)

    from persistence import DataStore
    return DataStore()
