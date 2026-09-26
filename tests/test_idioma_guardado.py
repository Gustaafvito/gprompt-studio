"""Valores guardados en un idioma y cargados con la app en otro.

Probado el 25-sep-2026 con la app en inglés: las preferencias traían
«— Sin personaje —» y «— Sin LoRA —» de cuando estaba en castellano. La app
las comparaba con «— No character —» y las tomaba por un personaje y un LoRA
de verdad: «Active sources: 1 LoRA». Ver i18n.al_idioma_actual.
"""
import re
from pathlib import Path

import pytest

import config
from modules import i18n
from modules.i18n import al_idioma_actual

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture()
def en_ingles():
    i18n.set_idioma("en")
    yield
    i18n.set_idioma("es")


class TestAlIdiomaActual:

    def test_del_castellano_al_ingles(self, en_ingles):
        assert al_idioma_actual("— Sin personaje —") == "— No character —"
        assert al_idioma_actual("— Sin LoRA —") == "— No LoRA —"

    def test_del_ingles_al_castellano(self):
        assert al_idioma_actual("— No character —") == "— Sin personaje —"

    def test_ya_en_su_idioma_no_cambia(self, en_ingles):
        assert al_idioma_actual("— No LoRA —") == "— No LoRA —"

    def test_un_nombre_de_verdad_no_se_toca(self, en_ingles):
        # Un personaje que se llame como una palabra traducible sigue siendo
        # suyo: solo se convierten los «ninguno» de la lista.
        assert al_idioma_actual("Cliente") == "Cliente"
        assert al_idioma_actual("Lucía") == "Lucía"
        assert al_idioma_actual("") == ""

    def test_destinos_con_su_lista(self, en_ingles):
        assert al_idioma_actual("Cliente", config.DESTINOS) == "Client"
        assert al_idioma_actual("TikTok", config.DESTINOS) == "TikTok"


class TestCadaCargaPasaPorAhi:
    """Candado: ningún valor GUARDADO llega a los combos sin convertir."""

    CARGAS = re.compile(r"(combo_personaje|combo_lora|destino_var)\.set\((.+)\)")

    @pytest.mark.parametrize("fichero", ["modules/data_mgmt.py", "modules/tools_workflow.py"])
    def test_personaje_lora_y_destino(self, fichero):
        malos = []
        for n, linea in enumerate((RAIZ / fichero).read_text(encoding="utf-8").splitlines(), 1):
            m = self.CARGAS.search(linea)
            if not m:
                continue
            arg = m.group(2)
            # Poner el «ninguno» del idioma actual, o un valor ya convertido,
            # está bien; lo que viene de un dict guardado, no.
            if arg.startswith("tr(") or "al_idioma_actual" in arg or arg in ("dest", "pers", "lora", "v"):
                continue
            malos.append(f"{fichero}:{n}: {linea.strip()}")
        assert malos == []
