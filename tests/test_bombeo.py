"""El bombeo de eventos de los tests no puede colgarse. Ver tests/_bombeo.py.

Tres volcados de la bitácora de cuelgues, el 24-sep-2026, señalaban el mismo
sitio: `root.after(ms, root.quit); root.mainloop()`. Si el `quit` vence antes
de que arranque el primer `mainloop()` de una ventana CTk, se pierde y el
bucle no vuelve nunca. Aquí se reproduce en un proceso aparte, para que un
cuelgue no se lleve la suite por delante.
"""
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent

# Lo que hacían los tests, con la construcción de la ventana más lenta que
# la espera: el temporizador del quit ya ha vencido al llegar al mainloop.
# (Salida en ASCII: la consola del subproceso no es UTF-8.)
_PATRON_VIEJO = """
import time
import customtkinter as ctk
r = ctk.CTk(); r.withdraw()
r.after(20, r.quit)
time.sleep(0.1)
r.mainloop()
print("volvio")
"""

_PATRON_NUEVO = """
import sys, time
sys.path.insert(0, {raiz!r})
import customtkinter as ctk
from tests._bombeo import bombear
r = ctk.CTk(); r.withdraw()
disparos = []
# Trabajo pendiente lento, como pintar una ventana recién construida: se
# hace DENTRO del primer update, después de programar la espera. Así es como
# el quit vencía a destiempo en los tests de verdad.
r.after_idle(lambda: time.sleep(0.2))
r.after(5, lambda: disparos.append(1))
bombear(r, 20)
print("volvio", disparos)
"""


def _correr(codigo, espera):
    try:
        r = subprocess.run([sys.executable, "-c", codigo], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=espera)
    except subprocess.TimeoutExpired:
        return None
    return r.stdout


class TestElCuelgueDeVerdad:

    def test_el_patron_viejo_se_cuelga(self, exige_tk):
        # Si esto dejara de colgarse (otra versión de CustomTkinter), el
        # arreglo seguiría siendo correcto, pero conviene saberlo.
        assert _correr(_PATRON_VIEJO, 6) is None, "el patrón viejo ya no se cuelga"

    def test_bombear_vuelve_y_atiende_el_temporizador(self, exige_tk):
        salida = _correr(_PATRON_NUEVO.format(raiz=str(RAIZ)), 20)
        assert salida is not None, "bombear() se colgó"
        assert "volvio [1]" in salida, salida


def test_ningun_test_bombea_con_quit_y_mainloop():
    # El patrón se había copiado en siete ficheros. Que no vuelva.
    fugas = []
    for py in (RAIZ / "tests").glob("*.py"):
        if py.name in ("test_bombeo.py", "_bombeo.py"):
            continue
        texto = py.read_text(encoding="utf-8")
        if ".mainloop()" in texto:
            fugas.append(py.name)
    assert not fugas, f"usa tests._bombeo.bombear en vez de after+quit+mainloop: {fugas}"
