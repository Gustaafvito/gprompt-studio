"""Dos guardados en el mismo instante no pueden pisarse.

VisualHistory nombraba cada versión con la hora, hasta el microsegundo. En
Windows con Python 3.10 esa hora avanza a saltos de 15,6 ms: medido el
24-sep-2026, 200.000 llamadas seguidas dieron solo 495 valores distintos. Dos
checkpoint() dentro del mismo salto —el panel guarda antes y después de cada
acción— recibían el mismo nombre, y el segundo borraba el primero sin avisar.

Aquí la hora se congela a propósito: es la forma de reproducir en cualquier
máquina lo que en Windows pasa solo.
"""
import os
from datetime import datetime, timedelta

import pytest
from PIL import Image

from modules import visual_history
from modules.visual_brief import MODES, Reference, load_project
from modules.visual_history import VisualHistory

INSTANTE = datetime(2026, 9, 24, 17, 30, 0, 123456)


class _RelojParado(datetime):
    @classmethod
    def now(cls, tz=None):
        return INSTANTE


@pytest.fixture
def reloj_parado(monkeypatch):
    monkeypatch.setattr(visual_history, "datetime", _RelojParado)


def _refs():
    return [Reference(Image.new("RGB", (40, 30), "red"), "Personaje", "ref-0")]


def _campos(texto):
    # Un proyecto que load_project acepta: sin modo ni formato válidos lo
    # rechaza, y el test fallaría por eso y no por lo que vigila.
    return dict(mode=MODES[2], idea="Abrir puerta", analysis="Una referencia",
                output=texto, aspect="9:16", duration="5", language="Inglés")


def _salidas(historia):
    """Lo que ofrece «Recuperar versiones», de la más nueva a la más vieja."""
    return [load_project(p)[1]["output"] for p in historia.versions()]


def _misma_fecha_de_modificacion(historia):
    # En el mismo salto de reloj también coincide la fecha de modificación de
    # los ficheros: NTFS la toma del mismo reloj. Se fuerza para que el orden
    # no pueda apoyarse en ella.
    for ruta in historia.versions():
        os.utime(ruta, (1_700_000_000, 1_700_000_000))


def test_el_reloj_parado_reproduce_la_colision(reloj_parado):
    # Si el andamio dejara de congelar la hora, los tests de abajo pasarían
    # sin probar nada.
    assert visual_history.datetime.now() == INSTANTE
    assert visual_history.datetime.now() == visual_history.datetime.now()


def test_guardados_en_el_mismo_instante_se_conservan_todos(tmp_path, reloj_parado):
    historia = VisualHistory(tmp_path)
    for texto in ("uno", "dos", "tres", "cuatro"):
        historia.save(_refs(), _campos(texto))
    assert sorted(_salidas(historia)) == ["cuatro", "dos", "tres", "uno"]


def test_recuperar_ofrece_primero_la_mas_reciente(tmp_path, reloj_parado):
    historia = VisualHistory(tmp_path)
    for texto in ("uno", "dos", "tres"):
        historia.save(_refs(), _campos(texto))
    _misma_fecha_de_modificacion(historia)
    assert _salidas(historia) == ["tres", "dos", "uno"]


def test_el_limite_de_12_se_queda_con_las_12_ultimas(tmp_path, reloj_parado):
    historia = VisualHistory(tmp_path)  # keep=12 por defecto
    textos = [f"v{i:02d}" for i in range(15)]
    for texto in textos:
        historia.save(_refs(), _campos(texto))
    _misma_fecha_de_modificacion(historia)
    assert _salidas(historia) == list(reversed(textos[-12:]))


def test_el_limite_no_depende_de_que_el_reloj_avance(tmp_path, monkeypatch):
    # El reloj del sistema es ajustable: una corrección de hora puede hacerlo
    # retroceder a mitad de sesión. El recorte tiene que seguir quitando las
    # versiones más VIEJAS de la sesión, no las que tengan la hora más baja.
    horas = iter(INSTANTE - timedelta(seconds=s) for s in range(100))

    class _RelojQueRetrocede(datetime):
        @classmethod
        def now(cls, tz=None):
            return next(horas)

    monkeypatch.setattr(visual_history, "datetime", _RelojQueRetrocede)
    historia = VisualHistory(tmp_path, keep=3)
    for texto in ("uno", "dos", "tres", "cuatro", "cinco"):
        historia.save(_refs(), _campos(texto))
    _misma_fecha_de_modificacion(historia)
    assert _salidas(historia) == ["cinco", "cuatro", "tres"]


def test_sin_cambios_no_se_guarda_otra_version(tmp_path, reloj_parado):
    historia = VisualHistory(tmp_path)
    historia.save(_refs(), _campos("uno"))
    historia.save(_refs(), _campos("uno"))
    assert _salidas(historia) == ["uno"]
