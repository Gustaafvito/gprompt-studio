"""Tests del panel lateral (Ctrl+B): filtrado puro + smoke de construcción."""

from types import SimpleNamespace

import pytest

from modules.panel_lateral import _COLECCIONES, filtrar_entradas, toggle_panel


class TestFiltrarEntradas:

    DATOS = [
        {"contenido": "a cat in the rain", "modo": "imagen",
         "fecha": "2026-07-01", "estilos": "Photoreal", "plataforma": "SeaArt / Tensor.Art"},
        {"contenido": "cinematic drone shot", "modo": "video",
         "fecha": "2026-07-02", "nota": "mi favorito épico"},
        {"contenido": "synthwave song", "modo": "audio", "fecha": "2026-07-03"},
    ]

    def test_sin_termino_devuelve_todo_con_indices(self):
        r = filtrar_entradas(self.DATOS, "")
        assert [i for i, _ in r] == [0, 1, 2]

    def test_busca_en_contenido_case_insensitive(self):
        r = filtrar_entradas(self.DATOS, "CAT")
        assert [i for i, _ in r] == [0]

    def test_busca_en_nota_y_fecha_y_plataforma(self):
        assert [i for i, _ in filtrar_entradas(self.DATOS, "épico")] == [1]
        assert [i for i, _ in filtrar_entradas(self.DATOS, "2026-07-03")] == [2]
        assert [i for i, _ in filtrar_entradas(self.DATOS, "tensor")] == [0]

    def test_sin_resultados(self):
        assert filtrar_entradas(self.DATOS, "nomatch_xyz") == []

    def test_datos_vacios(self):
        assert filtrar_entradas([], "algo") == []


class TestColecciones:

    def test_colecciones_del_store(self):
        # Las 3 pestañas apuntan a colecciones reales de PersistenceStore
        # y sus etiquetas tienen traducción EN (candado i18n).
        from modules.i18n import TRADUCCIONES
        claves = [c for c, _ in _COLECCIONES]
        assert claves == ["historial", "favoritos", "estrellas"]
        for _, etiqueta in _COLECCIONES:
            assert etiqueta in TRADUCCIONES, f"'{etiqueta}' sin traducción EN"


class TestSmokeConstruccion:
    """Candado del bug 2026-07-04: el panel usaba bind_all() (prohibido en un
    CTkFrame por CustomTkinter) y crasheaba al abrir. Construye el widget de
    verdad para pillar errores que la lógica pura no ve. Se salta si el
    entorno no tiene display (CI headless)."""

    def test_toggle_construye_y_cierra_sin_error(self):
        try:
            import customtkinter as ctk
            root = ctk.CTk()
        except Exception as e:
            pytest.skip(f"sin display para Tk: {e}")
        try:
            root.store = SimpleNamespace(
                historial=[{"contenido": "test", "modo": "imagen",
                            "fecha": "2026-07-04", "plataforma": "SeaArt"}],
                favoritos=[], estrellas=[])
            root.set_estado = lambda *a, **k: None
            root.actualizar_salida = lambda *a, **k: None
            root._sesion_log = lambda *a, **k: None

            toggle_panel(root)              # abrir
            assert root._panel_lateral is not None
            assert root._panel_lateral.winfo_exists()
            root.update()                   # forzar render de las cards
            toggle_panel(root)              # cerrar
            assert root._panel_lateral is None
        finally:
            root.destroy()
