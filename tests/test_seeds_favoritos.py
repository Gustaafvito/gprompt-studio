"""Los Seeds favoritos guardan y recuperan el modelo.

Hasta el 25-sep-2026 leían `app.modelo_img_var` y `app.modelo_vid_var`, que
no existen: todos los seeds se guardaban sin modelo, y aplicar uno antiguo
que sí lo trajera reventaba el botón con un AttributeError.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock


class _Var:
    def __init__(self, v):
        self.v = v

    def get(self):
        return self.v

    def set(self, v):
        self.v = v


class _Combo:
    def __init__(self, valor, valores):
        self.valor, self.valores = valor, valores

    def get(self):
        return self.valor

    def set(self, v):
        self.valor = v

    def cget(self, _clave):
        return self.valores


def _servicio(monkeypatch, prefs):
    from modules.tools_analysis import ToolsAnalysisService
    app = SimpleNamespace(
        combo_modelo_imagen=_Combo("GPT Image 2", ["GPT Image 2", "Seedream 5.0 Flash"]),
        combo_modelo_video=_Combo("Kling 3.0", ["Kling 3.0", "Veo 3.1"]),
        combo_plataforma=_Combo("SeaArt / Tensor.Art", ["SeaArt / Tensor.Art"]),
        combo_ratio=_Combo("1:1", ["1:1", "9:16"]),
        plataforma_var=_Var("SeaArt / Tensor.Art"), ratio_var=_Var("1:1"),
        estilo_checks={}, footer=SimpleNamespace(estilos_seleccionados=lambda: []),
        store=SimpleNamespace(cargar_preferencias=lambda: prefs,
                              guardar_preferencias=lambda p: prefs.update(p)),
        dialogs=SimpleNamespace(set_estado=MagicMock()),
        events=SimpleNamespace(on_plataforma_cambio=MagicMock(),
                               on_modelo_imagen_cambio=MagicMock(),
                               on_motor_cambio=MagicMock()),
        reiniciar_memoria=MagicMock())
    monkeypatch.setattr("tkinter.simpledialog.askstring", lambda *a, **k: "Mi seed")
    return ToolsAnalysisService(app), app


def test_el_seed_guarda_los_modelos(monkeypatch):
    prefs = {}
    servicio, _app = _servicio(monkeypatch, prefs)
    servicio._guardar_seed_favorito()
    seed = prefs["seeds_favoritos"][0]
    assert seed["modelo_img"] == "GPT Image 2"
    assert seed["modelo_vid"] == "Kling 3.0"


def test_aplicar_un_seed_recupera_el_modelo(monkeypatch):
    servicio, app = _servicio(monkeypatch, {})
    servicio._aplicar_seed({"nombre": "x", "plataforma": "SeaArt / Tensor.Art",
                            "modelo_img": "Seedream 5.0 Flash", "modelo_vid": "Veo 3.1",
                            "ratio": "9:16", "estilos": []})
    assert app.combo_modelo_imagen.get() == "Seedream 5.0 Flash"
    assert app.combo_modelo_video.get() == "Veo 3.1"
    assert app.ratio_var.get() == "9:16"
