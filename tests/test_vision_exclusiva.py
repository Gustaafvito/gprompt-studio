"""Elegir un proveedor de visión tiene que significar SOLO ese proveedor.

22-sep-2026. La cadena de visión encadena Gemini → Ollama → OpenRouter y, si
uno falla, pasa al siguiente. Eso está bien por defecto, pero tiene una
consecuencia que no se ve hasta que la sufres: quien elige Ollama —local y
gratis— casi siempre lo elige PARA no gastar cuota de pago, y una cadena que
continúa al fallar hace exactamente lo contrario. Se cae al siguiente y
factura sin avisar.

Reordenar la cadena NO lo arregla: solo cambia a quién se le factura cuando el
primero falla. Lo que hace falta es poder decir «este y ninguno más».

Estos tests usan proveedores falsos —no tocan ninguna red ni ninguna clave— y
lo que comprueban sobre todo es lo que NO pasa: que al fallar el elegido,
nadie más recibe una llamada.
"""
import pytest

# `modules` primero a proposito: workers.py importa modules.i18n y
# modules/__init__ importa de vuelta workers, asi que empezar por
# workers deja el modulo a medias y revienta el import. Los otros
# tests de workers no lo notan porque para cuando corren ya hay otro
# test que importo modules; este fichero tiene que valerse solo.
import modules  # noqa: F401
from workers import VisionChain


class _ClientesFalsos:
    """Lo mínimo que mira VisionChain al construirse."""

    def __init__(self, gemini=True, openrouter=True):
        self._gemini = gemini
        self._openrouter = openrouter

    def has_gemini(self):
        return self._gemini

    def has_openrouter(self):
        return self._openrouter


@pytest.fixture()
def cadena(monkeypatch):
    """Una VisionChain con los tres proveedores, todos falsos y contados."""
    monkeypatch.setattr(VisionChain, "_ollama_disponible", lambda self: True)
    c = VisionChain(_ClientesFalsos())
    llamadas = []

    def falso(nombre, respuesta=None, error=None):
        def _fn(imagen, prompt_v):
            llamadas.append(nombre)
            if error is not None:
                raise error
            return respuesta, nombre + "/modelo-falso"
        return _fn

    c._falso = falso
    c._llamadas = llamadas
    return c


def _montar(cadena, **comportamientos):
    """Sustituye los proveedores por falsos, conservando el orden real."""
    cadena.proveedores = [
        (nombre, cadena._falso(nombre, **comportamientos.get(nombre, {})))
        for nombre, _ in cadena.proveedores
    ]


class TestLaCadenaAutomaticaSigueIgual:
    """Lo de siempre no se toca: es el comportamiento por defecto."""

    def test_sin_proveedor_encadena_cuando_hay_429(self, cadena):
        _montar(cadena,
                Gemini={"error": RuntimeError("429 quota exceeded")},
                Ollama={"respuesta": "una descripcion suficientemente larga"})
        texto, motor = cadena.describir_con_prompt(object(), "prompt")
        assert texto.startswith("una descripcion")
        assert motor.startswith("Ollama")
        assert cadena._llamadas == ["Gemini", "Ollama"]

    def test_la_constante_pide_la_cadena_igual_que_none(self, cadena):
        _montar(cadena,
                Gemini={"error": RuntimeError("429 quota")},
                Ollama={"respuesta": "descripcion valida de la imagen"})
        cadena.describir_con_prompt(object(), "p", None, VisionChain.AUTOMATICA)
        assert cadena._llamadas == ["Gemini", "Ollama"]


class TestElegirUnoSignificaSoloEse:

    def test_usa_el_elegido_y_no_toca_a_los_demas(self, cadena):
        _montar(cadena,
                Gemini={"respuesta": "no deberia llamarse a Gemini"},
                Ollama={"respuesta": "descripcion local de la imagen"})
        texto, motor = cadena.describir_con_prompt(object(), "p", None, "Ollama")
        assert texto.startswith("descripcion local")
        assert motor.startswith("Ollama")
        assert cadena._llamadas == ["Ollama"], (
            "se llamo a " + str(cadena._llamadas))

    def test_si_falla_NO_se_cae_a_gemini(self, cadena):
        """El que de verdad importa: fallar no puede costar dinero."""
        _montar(cadena,
                Gemini={"respuesta": "Gemini contestaria, pero no debe"},
                Ollama={"error": ConnectionError("Ollama no responde")},
                OpenRouter={"respuesta": "OpenRouter tampoco debe"})
        with pytest.raises(ConnectionError):
            cadena.describir_con_prompt(object(), "p", None, "Ollama")
        assert cadena._llamadas == ["Ollama"], (
            "tras fallar el elegido se llamo a " + str(cadena._llamadas)
            + "; eso gasta cuota de pago sin avisar")

    def test_tampoco_se_cae_con_un_429(self, cadena):
        """Un 429 es justo lo que hace saltar a la cadena. Aquí no."""
        _montar(cadena,
                Gemini={"respuesta": "no"},
                Ollama={"error": RuntimeError("429 quota exceeded")})
        with pytest.raises(RuntimeError):
            cadena.describir_con_prompt(object(), "p", None, "Ollama")
        assert cadena._llamadas == ["Ollama"]

    def test_una_respuesta_vacia_es_un_fallo_no_un_salto(self, cadena):
        _montar(cadena,
                Gemini={"respuesta": "no deberia llegar aqui"},
                Ollama={"respuesta": ""})
        with pytest.raises(RuntimeError, match="vac"):
            cadena.describir_con_prompt(object(), "p", None, "Ollama")
        assert cadena._llamadas == ["Ollama"]

    def test_pedir_uno_que_no_existe_lo_dice_sin_llamar_a_nadie(self, cadena):
        _montar(cadena, Gemini={"respuesta": "no"})
        with pytest.raises(RuntimeError, match="no está disponible"):
            cadena.describir_con_prompt(object(), "p", None, "Inventado")
        assert cadena._llamadas == []

    def test_el_error_que_sube_es_el_del_proveedor(self, cadena):
        """Sin envolverlo: el usuario tiene que leer qué pasó de verdad."""
        _montar(cadena, Ollama={"error": ConnectionError("conexion rechazada")})
        with pytest.raises(ConnectionError, match="conexion rechazada"):
            cadena.describir_con_prompt(object(), "p", None, "Ollama")


class TestSeSabeQuienVaAResponderYQuienRespondio:

    def test_los_nombres_salen_en_orden(self, cadena):
        assert cadena.nombres_proveedores() == ["Gemini", "Ollama", "OpenRouter"]

    def test_sin_proveedores_la_lista_esta_vacia(self, monkeypatch):
        monkeypatch.setattr(VisionChain, "_ollama_disponible", lambda self: False)
        c = VisionChain(_ClientesFalsos(gemini=False, openrouter=False))
        assert c.nombres_proveedores() == []

    def test_el_estado_nombra_al_proveedor_antes_de_llamarlo(self, cadena):
        _montar(cadena, Ollama={"respuesta": "descripcion valida de la imagen"})
        avisos = []
        cadena.describir_con_prompt(object(), "p", avisos.append, "Ollama")
        assert any("Ollama" in a for a in avisos), avisos

    def test_devuelve_quien_respondio(self, cadena):
        _montar(cadena, Ollama={"respuesta": "descripcion valida de la imagen"})
        _, motor = cadena.describir_con_prompt(object(), "p", None, "Ollama")
        assert motor.startswith("Ollama")
