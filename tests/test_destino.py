"""El combo Destino: el formato automático.

Revisado el 24-sep-2026: el formato se ponía aunque el modelo no lo tuviera.
El 25-sep-2026 se quitó el concurso Anthum, que además encendía el Brief.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import config


class _Var:
    def __init__(self, valor):
        self.valor = valor

    def get(self):
        return self.valor

    def set(self, valor):
        self.valor = valor


class _Combo:
    def __init__(self, valores):
        self.valores = valores
        self.puesto = None

    def cget(self, _clave):
        return self.valores

    def set(self, valor):
        self.puesto = valor


def _servicio(destino, ratios=("1:1", "9:16", "16:9"), modo="imagen"):
    from modules.ui_builders import UIBuildersService
    app = SimpleNamespace(
        destino_var=_Var(destino), ratio_var=_Var("1:1"), brief_var=_Var(False),
        modo_var=_Var(modo), combo_ratio=_Combo(list(ratios)),
        combo_ratio_v=_Combo(list(ratios)),
        dialogs=SimpleNamespace(set_estado=MagicMock()),
        events=SimpleNamespace(on_brief_cambio=MagicMock()),
        reiniciar_memoria=MagicMock())
    servicio = UIBuildersService.__new__(UIBuildersService)
    servicio.app = app
    return servicio, app


class TestDestino:

    def test_pone_el_formato_de_la_red(self):
        servicio, app = _servicio("TikTok")
        servicio._on_destino_cambio()
        assert app.ratio_var.get() == "9:16"

    def test_ningun_destino_enciende_el_brief(self):
        # Solo lo hacía el concurso Anthum. El Brief lo decide el usuario.
        for destino in config.DESTINOS:
            servicio, app = _servicio(destino)
            servicio._on_destino_cambio()
            assert app.brief_var.get() is False, destino

    def test_anthum_ya_no_esta(self):
        from modules.prompts_inyeccion import PromptsInyeccionService
        assert not any("Anthum" in d for d in config.DESTINOS)
        assert not any("Anthum" in d for d in PromptsInyeccionService.REGLAS_POR_DESTINO)

    def test_no_pone_un_formato_que_el_modelo_no_tiene(self):
        servicio, app = _servicio("TikTok", ratios=("1:1", "16:9"))
        servicio._on_destino_cambio()
        assert app.ratio_var.get() == "1:1"
        texto = app.dialogs.set_estado.call_args[0][0]
        assert "9:16" in texto and "1:1" in texto

    def test_en_video_mira_los_formatos_del_video(self):
        servicio, app = _servicio("YouTube", modo="video")
        app.combo_ratio_v.valores = ["9:16"]
        servicio._on_destino_cambio()
        assert app.ratio_var.get() == "1:1"
