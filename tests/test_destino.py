"""El combo Destino: formato automático y Brief del concurso.

Revisado el 24-sep-2026:
  • destino_var guarda el nombre TRADUCIDO y las reglas iban por el
    castellano: en inglés, «Anthum (contest)» no activaba el Brief ni ponía su
    formato 9:16.
  • El formato se ponía aunque el modelo no lo tuviera.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from modules import i18n


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


@pytest.fixture()
def en_ingles():
    i18n.set_idioma("en")
    yield
    i18n.set_idioma("es")


class TestDestino:

    def test_el_concurso_activa_el_brief_y_su_formato(self):
        servicio, app = _servicio("Anthum (concurso)")
        servicio._on_destino_cambio()
        assert app.brief_var.get() is True
        assert app.ratio_var.get() == "9:16"

    def test_tambien_en_ingles(self, en_ingles):
        servicio, app = _servicio(i18n.tr("Anthum (concurso)"))
        assert app.destino_var.get() == "Anthum (contest)"
        servicio._on_destino_cambio()
        assert app.brief_var.get() is True
        assert app.ratio_var.get() == "9:16"

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
