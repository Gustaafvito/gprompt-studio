"""El modo 🔞 NSFW: detección, modelos que filtran y modelos para adultos.

Revisado el 24-sep-2026: la detección automática no había funcionado nunca
(escribía en `nsfw_var`, que no existe) y aun así anunciaba el cambio. Ver
modules/nsfw.py.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import config
from modules.nsfw import aviso, es_modelo_adulto, filtra_adultos, pide_nsfw


class TestPideNsfw:

    @pytest.mark.parametrize("idea", [
        "una mujer desnuda en la playa",
        "retrato erótico en blanco y negro",
        "Escena ERÓTICA con luz de vela",
        "nude portrait, soft light",
        "hentai girl, anime style",
        "foto nsfw de estudio",
    ])
    def test_lo_explicito_si(self, idea):
        assert pide_nsfw(idea)

    @pytest.mark.parametrize("idea", [
        # Las subcadenas que saltaban antes: «ass», «butt», «sex».
        "una clase de cristal, glass texture, passion for art",
        "a red button on a control panel",
        "a sexy red dress on a runway",
        "a cottage in Essex",
        # Sugerente no es explícito: un prompt normal lo maneja bien.
        "modelo en bikini en la playa, lencería de encaje",
        "",
    ])
    def test_lo_demas_no(self, idea):
        assert not pide_nsfw(idea)


class TestFiltraAdultos:

    @pytest.mark.parametrize("modelo", [
        "GPT Image 2", "GPT Image 2.5 Sunburst", "Nano Banana Pro Image",
        "Nano Banana Video", "Veo 3.1", "Midjourney v8.1", "Niji 7",
        "Ideogram 4", "MAI-Image-2.5",
    ])
    def test_los_que_filtran(self, modelo):
        assert filtra_adultos(modelo)

    @pytest.mark.parametrize("modelo", [
        # Modelo comunitario de FLUX con «Midjourney» en el nombre.
        "Midjourney Mimic Neo",
        "FLUX.1 [dev]", "Juggernaut XL", "PornRealistic", "", None,
    ])
    def test_los_que_no(self, modelo):
        assert not filtra_adultos(modelo)

    def test_los_prefijos_existen_en_el_catalogo(self):
        # Un prefijo que ya no casa con ningún modelo es un aviso que no sale.
        from modules.nsfw import _FILTRAN
        nombres = set()
        for grupos in (config.MODELOS_POR_PLATAFORMA_IMAGEN, config.MODELOS_POR_PLATAFORMA_VIDEO):
            for modelos in grupos.values():
                nombres.update(modelos)
        sin_modelo = [p for p in _FILTRAN
                      if p not in ("DALL-E", "Sora", "Firefly", "Imagen ")
                      and not any(n.startswith(p) for n in nombres)]
        assert sin_modelo == []


class TestModelosParaAdultos:

    def test_el_grupo_del_catalogo(self):
        assert es_modelo_adulto("PornRealistic", config.GRUPOS_IMAGEN)
        assert es_modelo_adulto("XE: Anime Hentai (FLUX)", config.GRUPOS_IMAGEN)

    def test_los_spicy_de_video(self):
        assert es_modelo_adulto("SeaArt Spicy Video 27")

    def test_los_demas_no(self):
        assert not es_modelo_adulto("Juggernaut XL", config.GRUPOS_IMAGEN)
        assert not es_modelo_adulto("", config.GRUPOS_IMAGEN)

    def test_el_grupo_sigue_llamandose_asi(self):
        from modules.nsfw import GRUPO_ADULTOS
        assert GRUPO_ADULTOS in [c for c, _ in config.GRUPOS_IMAGEN]


class TestAviso:

    def test_nsfw_con_modelo_que_filtra(self):
        assert aviso("GPT Image 2", True) == "filtra"

    def test_modelo_adulto_con_nsfw_apagado(self):
        assert aviso("PornRealistic", False, config.GRUPOS_IMAGEN) == "adulto_apagado"

    def test_si_casan_no_se_dice_nada(self):
        assert aviso("GPT Image 2", False) is None
        assert aviso("PornRealistic", True, config.GRUPOS_IMAGEN) is None
        assert aviso("Juggernaut XL", True, config.GRUPOS_IMAGEN) is None


class _Var:
    def __init__(self, valor):
        self.valor = valor

    def get(self):
        return self.valor

    def set(self, valor):
        self.valor = valor


class TestDeteccionAutomatica:
    """El AnalysisService real con una app simulada."""

    def _servicio(self, nsfw=False):
        from modules.tools_analysis import ToolsAnalysisService
        app = SimpleNamespace(switch_nsfw_var=_Var(nsfw), _toggle_nsfw_visual=MagicMock(),
                              reiniciar_memoria=MagicMock())
        return ToolsAnalysisService(app), app

    def test_una_idea_explicita_enciende_nsfw(self):
        servicio, app = self._servicio()
        assert servicio._detectar_nsfw_auto("una mujer desnuda en la playa") is True
        assert app.switch_nsfw_var.get() is True
        # Por el mismo camino que el interruptor: color y system prompt.
        app._toggle_nsfw_visual.assert_called_once()

    def test_una_idea_normal_no_toca_nada(self):
        servicio, app = self._servicio()
        assert servicio._detectar_nsfw_auto("a glass of water on a button") is False
        assert app.switch_nsfw_var.get() is False
        app._toggle_nsfw_visual.assert_not_called()

    def test_si_ya_estaba_encendido_no_hace_nada(self):
        servicio, app = self._servicio(nsfw=True)
        assert servicio._detectar_nsfw_auto("desnudo artístico") is False
        app._toggle_nsfw_visual.assert_not_called()


class TestNegativos:

    def test_con_nsfw_apagado_el_negativo_excluye_la_desnudez(self):
        from prompts import NEGATIVE_BASE_NSFW, NEGATIVE_BASE_SFW, NEGATIVE_BASE_VIDEO
        for base in (NEGATIVE_BASE_SFW, NEGATIVE_BASE_VIDEO):
            assert "nsfw" in base and "nudity" in base
        # Y con NSFW encendido, no.
        assert "nudity" not in NEGATIVE_BASE_NSFW
