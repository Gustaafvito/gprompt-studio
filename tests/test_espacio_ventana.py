"""El alto de la ventana principal: al abrir cabe, y el resultado va primero.

Ver modules/espacio_ventana.py. Medido el 24-sep-2026 en 1920×1080 al 100 %:
a tamaño por defecto el «Resultado editable» recibía 30 px de los 240 que
pide, y con el escalado al 125 % la ventana pedía más alto que la pantalla.
"""
import pytest

from modules import espacio_ventana as ev
from modules.espacio_ventana import (
    IDEA_MAX,
    IDEA_MIN,
    PESTANAS_MAX,
    PESTANAS_MIN,
    SALIDA_UTIL,
    geometria_inicial,
    plegar_pestanas,
    repartir,
)

PANTALLAS = [
    (1920, 1080, 1.0), (1920, 1080, 1.25), (1920, 1080, 1.5),
    (1920, 1200, 1.5), (1366, 768, 1.0), (1366, 768, 1.25),
    (1280, 720, 1.0), (1536, 864, 1.0), (2560, 1440, 1.0),
    (2560, 1440, 1.5), (3840, 2160, 1.5), (3840, 2160, 2.0),
]


class TestAlAbrirCabe:

    @pytest.mark.parametrize("pw,ph,escala", PANTALLAS,
                             ids=[f"{a}x{b}@{int(c * 100)}" for a, b, c in PANTALLAS])
    def test_la_ventana_entera_cabe_en_la_pantalla(self, pw, ph, escala):
        # CTk.geometry() multiplica por la escala: esto es lo que acaba
        # ocupando de verdad, marco incluido, encima de la barra de tareas.
        w, h, x, y = geometria_inicial(pw, ph, escala)
        util = ph - ev._BARRA_TAREAS * escala
        assert x >= 0 and y >= 0
        assert (x + w) * escala <= pw + 1
        assert (y + h) * escala + ev._MARCO * escala <= util + 1, (w, h, x, y)

    def test_con_escalado_ya_no_pide_mas_que_la_pantalla(self):
        # Antes: 897 lógicos, que al 125 % son 1121 px reales en 1080.
        _, h, _, _ = geometria_inicial(1920, 1080, 1.25)
        assert h * 1.25 < 1080

    def test_en_full_hd_abre_mas_alta_que_antes(self):
        # 897 dejaba 30 px al resultado; cada píxel de alto va para él.
        w, h, _, _ = geometria_inicial(1920, 1080, 1.0)
        assert w == 1382
        assert h > 897 + 40


class TestRepartir:

    def test_con_sitio_de_sobra_todo_a_su_tamano_de_siempre(self):
        assert repartir(2000, 300) == (PESTANAS_MAX, IDEA_MAX)

    def test_con_poco_sitio_ceden_hasta_su_minimo_y_no_mas(self):
        assert repartir(300, 300) == (PESTANAS_MIN, IDEA_MIN)

    def test_primero_ceden_las_pestanas_y_luego_la_idea(self):
        # De 230 a 195 las pestañas solo pierden hueco vacío; la idea
        # perdería líneas a la vista. Faltan 20: los pone todos la pestaña.
        assert repartir(300 + PESTANAS_MAX + IDEA_MAX - 20, 300) == (PESTANAS_MAX - 20, IDEA_MAX)
        # Cuando las pestañas ya están en su mínimo, cede la idea.
        falta = PESTANAS_MAX - PESTANAS_MIN + 10
        assert repartir(300 + PESTANAS_MAX + IDEA_MAX - falta, 300) == (PESTANAS_MIN, IDEA_MAX - 10)

    def test_plegadas_miden_su_tira_y_la_idea_se_lleva_lo_que_quede(self):
        assert repartir(300 + 44 + IDEA_MAX, 300, plegadas=44) == (44, IDEA_MAX)
        assert repartir(300, 300, plegadas=44) == (44, IDEA_MIN)


class TestPlegar:

    def test_se_pliegan_solas_si_desplegadas_no_cabe_el_resultado(self):
        justo = PESTANAS_MIN + IDEA_MIN + SALIDA_UTIL
        assert plegar_pestanas(justo) is False
        assert plegar_pestanas(justo - 1) is True

    def test_lo_que_decide_el_usuario_manda(self):
        assert plegar_pestanas(10_000, manual=True) is True
        assert plegar_pestanas(10, manual=False) is False
