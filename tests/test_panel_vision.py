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


class TestLaSeleccionViajaConElProyecto:
    """Elegir Ollama y que al reabrir vuelva «Cadena automática» es peor que
    no poder elegir: pulsas «Analizar» convencido de que no vas a gastar.

    Estos tests recorren guardar y reabrir de verdad, y el último cierra el
    circulo: tras reabrir, se simula que el proveedor falla y se comprueba que
    NINGUN otro recibe una llamada.
    """

    def _guardar(self, panel, destino):
        from PIL import Image

        from modules.visual_brief import ROLES, Reference, save_project
        panel.refs.append(Reference(Image.new("RGB", (32, 24), "red"),
                                    ROLES[0], "a.png"))
        save_project(str(destino), panel.refs, panel.fields())

    def test_se_guarda_en_el_proyecto(self, panel, tmp_path):
        panel.vision_provider_changed(i18n.tr("Ollama"))
        assert panel.fields()["vision_provider"] == "Ollama"

    def test_se_restaura_al_reabrir(self, panel, tmp_path):
        from modules.visual_brief import load_project
        panel.vision_provider_changed(i18n.tr("Ollama"))
        destino = tmp_path / "p.gprompt"
        self._guardar(panel, destino)

        _refs, campos = load_project(str(destino))
        assert campos["vision_provider"] == "Ollama"

        antes = set(panel.app.winfo_children())
        panel.open_project(str(destino))
        _bombear(panel.app, 250)
        abierto = [w for w in panel.app.winfo_children()
                   if w not in antes and isinstance(w, VisualStudio)][0]
        assert abierto.vision_provider.get() == "Ollama", (
            "al reabrir volvio a " + repr(abierto.vision_provider.get()))
        assert abierto.vision_menu.get() == i18n.tr("Ollama"), (
            "el desplegable no refleja lo guardado: " + abierto.vision_menu.get())
        abierto.destroy()

    def test_un_proyecto_viejo_sin_la_clave_se_queda_en_la_cadena(self, panel, tmp_path):
        """Los .gprompt anteriores no traen la clave; no deben romper nada."""
        from modules.visual_brief import load_project
        destino = tmp_path / "viejo.gprompt"
        self._guardar(panel, destino)
        _refs, campos = load_project(str(destino))
        campos.pop("vision_provider", None)
        assert campos.get("vision_provider", "") == ""

        antes = set(panel.app.winfo_children())
        panel.open_project(str(destino))
        _bombear(panel.app, 250)
        abierto = [w for w in panel.app.winfo_children()
                   if w not in antes and isinstance(w, VisualStudio)][0]
        assert abierto.vision_provider.get() == CADENA_AUTOMATICA
        abierto.destroy()

    def test_si_el_guardado_ya_no_esta_se_dice_y_NO_se_sustituye(self, root, tmp_path):
        """Lo importante es que no se cambie por la cadena en silencio.

        Sustituirlo seria justo lo que el usuario pidio evitar: creeria seguir
        con su proveedor local y estaria encadenando.
        """
        root.vision = _VisionFalsa(nombres=("Gemini", "Ollama"))
        root._executor = _EjecutorSincrono()
        origen = VisualStudio(root)
        _bombear(root)
        origen.vision_provider_changed(i18n.tr("Ollama"))
        destino = tmp_path / "sin-ollama.gprompt"
        self._guardar(origen, destino)

        # Ahora Ollama ya no esta: se apago entre guardar y reabrir.
        root.vision = _VisionFalsa(nombres=("Gemini",))
        antes = set(root.winfo_children())
        origen.open_project(str(destino))
        _bombear(root, 250)
        abierto = [w for w in root.winfo_children()
                   if w not in antes and isinstance(w, VisualStudio)][0]

        assert abierto.vision_provider.get() == "Ollama", (
            "se sustituyo por " + repr(abierto.vision_provider.get()))
        assert "no est" in abierto.vision_hint.cget("text"), (
            "no avisa de que el proveedor guardado falta: "
            + abierto.vision_hint.cget("text"))
        abierto.destroy()
        origen.destroy()

    def test_recorrido_entero_elegir_guardar_reabrir_y_fallar(self, root, tmp_path):
        """El recorrido completo, que es lo que de verdad hay que garantizar.

        Elegir Ollama, guardar, reabrir, simular que falla, y comprobar que la
        cadena NO llama a ningun otro proveedor. Si la seleccion no se hubiera
        restaurado, aqui habria una llamada con proveedor=None y el fallo se
        habria pagado con cuota de Gemini.
        """
        root.vision = _VisionFalsa(nombres=("Gemini", "Ollama", "OpenRouter"))
        root._executor = _EjecutorSincrono()
        origen = VisualStudio(root)
        _bombear(root)
        origen.vision_provider_changed(i18n.tr("Ollama"))
        destino = tmp_path / "recorrido.gprompt"
        self._guardar(origen, destino)

        antes = set(root.winfo_children())
        origen.open_project(str(destino))
        _bombear(root, 250)
        abierto = [w for w in root.winfo_children()
                   if w not in antes and isinstance(w, VisualStudio)][0]
        assert abierto.vision_provider.get() == "Ollama"

        # A partir de aqui, el proveedor falla.
        fallona = _VisionFalsa(nombres=("Gemini", "Ollama", "OpenRouter"),
                               fallo=ConnectionError("Ollama no responde"))
        root.vision = fallona
        abierto.analyze()
        _bombear(root, 300)

        assert fallona.peticiones == ["Ollama"], (
            "tras reabrir y fallar se pidio " + str(fallona.peticiones)
            + "; cualquier otro nombre ahi es saldo gastado sin querer")
        assert "Ollama no responde" in abierto.status.get(), (
            "el error del proveedor no llega al usuario: " + abierto.status.get())
        abierto.destroy()
        origen.destroy()
