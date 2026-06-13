"""Tests de PreviewPollinationsService — cableado app↔servicio sin red.

El camino cache-hit ejercita las referencias self.app.* del servicio
(extracción de POSITIVE, locks no, pero sí _extraer_pos_de_bloque y la
gestión de caché) sin tocar la red — que es justo donde un self vs
self.app mal convertido al extraer de app.py reventaría.
"""
import sys
from types import SimpleNamespace

import pytest
from PIL import Image

from modules.preview_pollinations import PreviewPollinationsService


@pytest.fixture
def fake_app(monkeypatch, tmp_path):
    """App mínima + HOME redirigido para que el cache viva en tmp."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))  # Windows
    # Path.home() en algunas plataformas usa USERPROFILE; forzamos ambos.
    import pathlib
    monkeypatch.setattr(pathlib.Path, "home", classmethod(lambda cls: tmp_path))
    app = SimpleNamespace(
        _extraer_pos_de_bloque=lambda t: t,
    )
    return app


def test_servicio_se_instancia_con_app():
    app = SimpleNamespace()
    svc = PreviewPollinationsService(app)
    assert svc.app is app


def test_generar_prompt_vacio_llama_on_error(fake_app):
    svc = PreviewPollinationsService(fake_app)
    errores = []
    svc.generar("", on_imagen=lambda img: None, on_error=errores.append)
    assert errores and "vac" in errores[0].lower()


def test_generar_cache_hit_devuelve_imagen_sin_red(fake_app, tmp_path):
    """Si el PNG ya está cacheado, generar() lo sirve sin hilo ni red."""
    import hashlib

    svc = PreviewPollinationsService(fake_app)

    # Reproduce la clave de caché que usa el servicio.
    pos = "un gato astronauta"
    size = 512
    modelo = "auto"
    cache_dir = tmp_path / ".arquitecto_prompts" / "preview_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5(f"{pos}|{size}|{modelo}".encode()).hexdigest()[:16]
    Image.new("RGB", (8, 8), "blue").save(cache_dir / f"{key}.png")

    recibidas = []
    # Sin parent_widget el callback es síncrono → no hay hilo de red.
    svc.generar(pos, on_imagen=recibidas.append, on_error=lambda m: recibidas.append(None))

    assert len(recibidas) == 1
    assert isinstance(recibidas[0], Image.Image)


def test_metodos_publicos_existen():
    svc = PreviewPollinationsService(SimpleNamespace())
    for nombre in ("generar", "abrir_grid", "mostrar_window", "guardar_boceto"):
        assert callable(getattr(svc, nombre))
