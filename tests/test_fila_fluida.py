"""Filas de botones que bajan a otra línea lo que no cabe, en vez de esconderlo.

Medido el 24-sep-2026 a 1382 de ancho: Reset, Última, Setup y Cargar setup no
se veían, «Preview» quedaba en 34 px y el menú «Workflow» no aparecía. Ver
modules/fila_fluida.py.
"""
import pytest

from modules.fila_fluida import ancho_boton, cabe_completo, repartir_en_filas
from tests._bombeo import bombear


class TestRepartirEnFilas:

    def test_si_cabe_todo_va_en_una_linea(self):
        assert repartir_en_filas([100, 100, 100], 400, hueco=10) == [0, 0, 0]

    def test_lo_que_no_cabe_baja_entero(self):
        # 100 + 10 + 100 = 210 cabe en 250; el tercero ya no.
        assert repartir_en_filas([100, 100, 100], 250, hueco=10) == [0, 0, 1]

    def test_el_hueco_cuenta(self):
        # Sin hueco cabrían los dos en 200; con él, no.
        assert repartir_en_filas([100, 100], 200, hueco=0) == [0, 0]
        assert repartir_en_filas([100, 100], 200, hueco=10) == [0, 1]

    def test_una_pieza_mas_ancha_que_todo_va_sola(self):
        assert repartir_en_filas([50, 500, 50], 300, hueco=10) == [0, 1, 2]

    def test_nunca_cambia_el_orden(self):
        lineas = repartir_en_filas([80, 300, 40, 40, 200, 90], 320, hueco=18)
        assert lineas == sorted(lineas)

    def test_sin_piezas(self):
        assert repartir_en_filas([], 300) == []


class TestCabeCompleto:

    def test_justo(self):
        assert cabe_completo(310, [100, 100, 100], hueco=5)
        assert not cabe_completo(309, [100, 100, 100], hueco=5)

    def test_sin_piezas_siempre_cabe(self):
        assert cabe_completo(0, [])


class _Fuente:
    def measure(self, texto):
        return 7 * len(texto)


class TestAnchoBoton:

    def test_se_ajusta_al_texto(self):
        assert ancho_boton(_Fuente(), "Batch", 80) == 7 * 5 + 24

    def test_nunca_mas_ancho_que_antes(self):
        assert ancho_boton(_Fuente(), "Un texto larguísimo de verdad", 90) == 90

    def test_los_de_solo_icono_no_se_tocan(self):
        assert ancho_boton(_Fuente(), "←", 30) == 30
        assert ancho_boton(_Fuente(), "🎲", 40) == 40


ctk = pytest.importorskip("customtkinter")


@pytest.fixture()
def ventana(tk_root):
    # El root compartido está retirado (withdraw): sin mapear, todo mide 1 px
    # y la fila no sabe cuánto sitio tiene.
    v = ctk.CTkToplevel(tk_root)
    v.geometry("300x300")
    yield v
    v.destroy()


@pytest.fixture()
def fila(ventana):
    from modules.fila_fluida import FilaFluida
    f = FilaFluida(ventana, "#888888")
    f.pack(fill="x")
    return f


def _pieza(fila, texto):
    cuerpo = fila.nueva_pieza()
    ctk.CTkButton(cuerpo, text=texto, width=120).pack(side="left")
    return cuerpo


class TestFilaFluida:

    def test_estrecha_baja_piezas_y_ninguna_desaparece(self, ventana, fila):
        cuerpos = [_pieza(fila, f"B{i}") for i in range(4)]
        bombear(ventana, 300)
        assert fila.lineas() >= 2
        for cuerpo in cuerpos:
            assert cuerpo.winfo_ismapped()
            assert cuerpo.winfo_width() >= cuerpo.winfo_reqwidth() - 2

    def test_ancha_todo_en_una_linea(self, ventana, fila):
        ventana.geometry("1200x300")
        for i in range(4):
            _pieza(fila, f"B{i}")
        bombear(ventana, 300)
        assert fila.lineas() == 1

    def test_ninguna_linea_empieza_con_separador(self, ventana, fila):
        # 300 de ancho y piezas de 120: dos por línea, así hay de las dos.
        for i in range(4):
            _pieza(fila, f"B{i}")
        bombear(ventana, 300)
        primera_de_linea = set()
        for (_u, separador, _c), num in zip(fila._piezas, fila._reparto):
            if num not in primera_de_linea:
                primera_de_linea.add(num)
                assert not separador.winfo_ismapped()
            else:
                assert separador.winfo_ismapped()
