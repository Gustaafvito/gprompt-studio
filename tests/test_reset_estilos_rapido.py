"""Cambiar de modo no debe repintar los 257 checkboxes de estilos.

`_construir_checkboxes` ya cachea los widgets por modo, pero al reaparecer
desmarcaba TODAS las casillas con `var.set(False)`. En Tk el trace de una
variable se dispara aunque el valor no cambie, y cada disparo repinta el
checkbox entero (~40 itemconfigure en el canvas).

Medido el 06-sep-2026 sobre la app real: volver de vídeo a imagen tardaba
575 ms con la interfaz congelada, de los cuales 2.375 de cada 2.803 ms del
perfil se iban en este bucle. Preguntando antes de escribir: 179 ms.
"""
import inspect

from modules import ui_footer


class TestResetSoloDeLoMarcado:

    def test_pregunta_antes_de_escribir(self):
        fuente = inspect.getsource(ui_footer.UiFooterService._construir_checkboxes)
        bloque = fuente.split("Reset visual")[1].split("lbl_estilos_sel")[0]
        assert "if var.get():" in bloque, \
            "sin el guard, cada cambio de modo repinta todos los estilos"

    def test_sigue_desmarcando(self):
        """El guard no puede haberse llevado por delante el reset."""
        fuente = inspect.getsource(ui_footer.UiFooterService._construir_checkboxes)
        assert "var.set(False)" in fuente


class TestSimulacionDelCoste:
    """Reproduce el patrón con variables falsas que cuentan repintados."""

    class _VarFalsa:
        pintados = 0
        def __init__(self, valor=False): self._v = valor
        def get(self): return self._v
        def set(self, v):
            # Tk dispara el trace SIEMPRE, cambie o no el valor
            type(self).pintados += 1
            self._v = v

    def test_con_guard_solo_repinta_las_marcadas(self):
        V = self._VarFalsa
        V.pintados = 0
        estilos = {f"e{i}": V(i in (3, 17)) for i in range(257)}
        for var in estilos.values():
            if var.get():
                var.set(False)
        assert V.pintados == 2, f"deberían repintarse solo las 2 marcadas, no {V.pintados}"

    def test_sin_guard_repintaria_las_257(self):
        """Candado del contraste: así era antes."""
        V = self._VarFalsa
        V.pintados = 0
        estilos = {f"e{i}": V(i in (3, 17)) for i in range(257)}
        for var in estilos.values():
            var.set(False)
        assert V.pintados == 257
