"""El panel deja elegir proveedor de visión y avisa de quién va a responder.

Complemento de `tests/test_vision_exclusiva.py`, que cubre el motor. Aquí se
mira lo que el usuario ve y lo que el panel le pasa a la cadena: que se
anuncia el proveedor ANTES de gastar nada, que elegir uno concreto se traduce
en una llamada exclusiva, y que después se dice quién respondió de verdad
—que con la cadena automática no tiene por qué ser el primero—.

Ningún test de este fichero toca la red: la cadena de visión es falsa y
apunta lo que se le pide.
"""
import inspect

import pytest

ctk = pytest.importorskip("customtkinter")

from modules import i18n
from modules.visual_studio import CADENA_AUTOMATICA, VisualStudio


class _VisionFalsa:
    def __init__(self, nombres=("Gemini", "Ollama", "OpenRouter"), fallo=None):
        self._nombres = list(nombres)
        self.peticiones = []
        self.fallo = fallo

    def nombres_proveedores(self):
        return list(self._nombres)

    def describir_con_prompt(self, imagen, prompt_v, on_status=None,
                             proveedor=None):
        self.peticiones.append(proveedor)
        if self.fallo:
            raise self.fallo
        return "una descripcion suficientemente larga", (proveedor or "Gemini") + "/x"


def _bombear(root, ms=120):
    root.after(ms, root.quit)
    root.mainloop()


@pytest.fixture()
def root(tk_root):
    for w in list(tk_root.winfo_children()):
        if isinstance(w, VisualStudio):
            try:
                w.destroy()
            except Exception:
                pass
    return tk_root


class _EjecutorSincrono:
    """Corre la tarea en el acto y devuelve algo que parece un Future.

    El panel hace submit() y luego sondea con after(100, poll) hasta que el
    future esta done(). Ejecutando en el momento, el primer sondeo ya lo
    encuentra listo y el test no depende de hilos.
    """

    class _Futuro:
        def __init__(self, fn):
            try:
                self._valor, self._error = fn(), None
            except Exception as exc:  # se reexpone en result()
                self._valor, self._error = None, exc

        def done(self):
            return True

        def cancel(self):
            return False

        def result(self):
            if self._error is not None:
                raise self._error
            return self._valor

    def submit(self, fn):
        return self._Futuro(fn)


@pytest.fixture()
def panel(root):
    """Un panel con una cadena de visión falsa colgada de su app."""
    previa = getattr(root, "vision", None)
    root.vision = _VisionFalsa()
    root._executor = _EjecutorSincrono()
    v = VisualStudio(root)
    _bombear(root)
    yield v
    try:
        v.destroy()
    except Exception:
        pass
    if previa is None:
        try:
            delattr(root, "vision")
        except Exception:
            pass
    else:
        root.vision = previa


class TestElSelectorOfreceLoQueHay:

    def test_la_primera_opcion_es_la_cadena(self, panel):
        assert panel.vision_options()[0] == CADENA_AUTOMATICA

    def test_detras_van_los_proveedores_vivos(self, panel):
        assert panel.vision_options()[1:] == ["Gemini", "Ollama", "OpenRouter"]

    def test_por_defecto_se_encadena(self, panel):
        assert panel.vision_provider.get() == CADENA_AUTOMATICA

    def test_sin_proveedores_lo_dice(self, root):
        root.vision = _VisionFalsa(nombres=())
        v = VisualStudio(root)
        _bombear(root)
        assert v.vision_options() == [CADENA_AUTOMATICA]
        assert "Sin proveedores" in v.vision_hint.cget("text")
        v.destroy()
        delattr(root, "vision")

    def test_sin_app_detras_no_revienta(self, root):
        # El panel se construye en tests colgando de un root pelado.
        if hasattr(root, "vision"):
            delattr(root, "vision")
        v = VisualStudio(root)
        _bombear(root)
        assert v.vision_options() == [CADENA_AUTOMATICA]
        v.destroy()


class TestSeSabeQuienVaAResponderAntesDeGastar:

    def test_la_cadena_enumera_el_orden(self, panel):
        panel.refresh_vision_hint()
        texto = panel.vision_hint.cget("text")
        assert "Gemini" in texto and "Ollama" in texto, texto

    def test_elegir_uno_avisa_de_que_no_hay_alternativa(self, panel):
        panel.vision_provider_changed(i18n.tr("Ollama"))
        texto = panel.vision_hint.cget("text")
        assert "Ollama" in texto
        assert "ning" in texto.lower(), (
            "el aviso tiene que decir que NO se usara ningun otro: " + texto)

    def test_uno_que_ya_no_esta_se_marca(self, panel):
        panel.vision_provider.set("Inventado")
        panel.refresh_vision_hint()
        assert "no est" in panel.vision_hint.cget("text")


class TestLoQueElPanelLePideALaCadena:
    """analyze() valida las referencias ANTES de llamar a la cadena, asi
    que estos tests tienen que darle una imagen o no llegan a pedir nada."""

    @staticmethod
    def _con_una_imagen(panel):
        from PIL import Image

        from modules.visual_brief import ROLES, Reference
        panel.refs.append(Reference(Image.new("RGB", (32, 24), "red"),
                                    ROLES[0], "a.png"))
        return panel

    def test_por_defecto_no_fija_proveedor(self, panel):
        self._con_una_imagen(panel)
        panel.analyze()
        _bombear(panel.app, 250)
        assert panel.app.vision.peticiones == [None], (
            "la cadena automatica no debe fijar proveedor")

    def test_al_elegir_uno_se_pide_ese_y_solo_ese(self, panel):
        self._con_una_imagen(panel)
        panel.vision_provider_changed(i18n.tr("Ollama"))
        panel.analyze()
        _bombear(panel.app, 250)
        assert panel.app.vision.peticiones == ["Ollama"], (
            "se pidio " + str(panel.app.vision.peticiones))

    def test_despues_se_dice_quien_respondio(self, panel):
        self._con_una_imagen(panel)
        panel.vision_provider_changed(i18n.tr("Ollama"))
        panel.analyze()
        _bombear(panel.app, 300)
        texto = panel.vision_hint.cget("text")
        assert "Ollama" in texto, texto

    def test_el_estado_nombra_al_elegido_antes_de_analizar(self, panel):
        self._con_una_imagen(panel)
        panel.vision_provider_changed(i18n.tr("Ollama"))
        panel.analyze()
        assert "Ollama" in panel.status.get(), panel.status.get()


class TestLaConstanteCuadraConElMotor:
    """El panel y VisionChain tienen que entenderse sobre qué es «automático»."""

    def test_el_panel_manda_None_y_no_la_etiqueta(self):
        fuente = inspect.getsource(VisualStudio.analyze)
        assert "None if not exclusivo else elegido" in fuente, (
            "si el panel mandara la etiqueta como proveedor, VisionChain "
            "buscaria un proveedor llamado «Cadena automatica» y fallaria")

    def test_la_etiqueta_tiene_traduccion(self):
        assert CADENA_AUTOMATICA in i18n.TRADUCCIONES
