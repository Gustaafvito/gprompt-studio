"""El panel «Crear desde imágenes» ordenado por pasos, con las acciones a mano.

Revisado con capturas el 24-sep-2026: era un formulario de cuatro pantallas
sin divisiones, con «1. Analizar» y «2. Generar» a mitad de recorrido, «Crear
cortometraje» al final del todo y todos los botones del mismo azul. Ahora:

  • secciones con título (Imágenes, Qué quieres crear, Destino, Análisis,
    Prompt) y todo lo del proyecto en la cabecera;
  • una barra FIJA abajo con Analizar, Generar, Copiar y Cortometraje,
    fuera del cuerpo que se desplaza;
  • el análisis sin los asteriscos del markdown del proveedor.
"""
import pytest
from PIL import Image

from tests._bombeo import bombear

ctk = pytest.importorskip("customtkinter")

from modules import i18n
from modules.visual_brief import MODES, ROLES, Reference, texto_sin_markdown
from modules.visual_studio import VisualStudio


@pytest.fixture()
def root(tk_root):
    for w in list(tk_root.winfo_children()):
        if isinstance(w, VisualStudio):
            try:
                w.destroy()
            except Exception:
                pass
    return tk_root


@pytest.fixture()
def panel(root):
    v = VisualStudio(root)
    bombear(root)
    yield v
    try:
        v.destroy()
    except Exception:
        pass


def _dentro_de(widget, contenedor):
    w = widget
    while w is not None:
        if w is contenedor:
            return True
        w = w.master
    return False


def _botones(w):
    for hijo in w.winfo_children():
        if isinstance(hijo, ctk.CTkButton):
            yield hijo
        yield from _botones(hijo)


def _textos(w):
    for hijo in w.winfo_children():
        if isinstance(hijo, ctk.CTkLabel):
            yield hijo.cget("text")
        yield from _textos(hijo)


class TestLasAccionesSiempreALaVista:

    def test_analizar_generar_y_cortometraje_van_en_la_barra_fija(self, panel):
        corto = [b for b in _botones(panel)
                 if b.cget("text") == i18n.tr("Crear cortometraje con estas referencias")]
        assert len(corto) == 1
        for boton in (panel.analyze_button, panel.generate_button, corto[0]):
            assert _dentro_de(boton, panel.action_bar), boton.cget("text")
            # Fuera del cuerpo: el cuerpo se desplaza y se los llevaba.
            assert not _dentro_de(boton, panel.body), boton.cget("text")

    def test_con_una_peticion_en_marcha_tambien_se_bloquea_la_barra(self, panel):
        # set_controls() solo recorría el cuerpo: con los botones fuera,
        # Analizar y Generar seguirían pulsables a mitad de una petición.
        panel.set_controls("disabled")
        assert panel.analyze_button.cget("state") == "disabled"
        assert panel.generate_button.cget("state") == "disabled"
        panel.set_controls("normal")
        assert panel.analyze_button.cget("state") == "normal"


class TestSecciones:

    def test_en_orden_y_con_titulo(self, panel):
        textos = list(_textos(panel.body))
        esperadas = ["Imágenes", "Qué quieres crear", "Destino", "Análisis", "Prompt"]
        posiciones = [textos.index(i18n.tr(s)) for s in esperadas]
        assert posiciones == sorted(posiciones), textos

    def test_en_ingles(self, root):
        i18n.set_idioma("en")
        try:
            v = VisualStudio(root)
            bombear(root)
            textos = list(_textos(v.body))
            for s in ("Images", "What you want to create", "Destination", "Analysis"):
                assert s in textos, textos
            v.destroy()
        finally:
            i18n.set_idioma("es")


class TestModosDeVideo:

    def test_animar_imagen_no_deja_el_rotulo_de_transicion_suelto(self, panel):
        # Desde que cada caja lleva su rótulo en su fila, ocultar solo la
        # caja dejaba «Inicio → final» suelto en Animar imagen.
        panel.mode_changed(i18n.tr(MODES[1]))
        bombear(panel.master)
        assert panel.transition_direction.master.winfo_manager() == ""
        panel.mode_changed(i18n.tr(MODES[2]))
        bombear(panel.master)
        assert panel.transition_direction.master.winfo_manager() == "pack"

    def test_la_direccion_de_video_va_dentro_de_destino(self, panel):
        # Antes se colocaba «antes del botón Analizar», que ya no está en el
        # cuerpo.
        panel.mode_changed(i18n.tr(MODES[1]))
        bombear(panel.master)
        assert panel.video_controls.winfo_manager() == "pack"
        assert panel.video_controls.master is panel.model_menu.master


class TestEstadoVacio:

    def test_sin_imagenes_se_explica_y_no_deja_un_hueco(self, panel):
        aviso = i18n.tr("Todavía no hay imágenes. Añádelas, o usa la que tengas cargada en la ventana principal.")
        assert aviso in list(_textos(panel.cards))
        panel.refs.append(Reference(Image.new("RGB", (32, 24), "red"), ROLES[0], "a.png"))
        panel.render()
        bombear(panel.master)
        assert aviso not in list(_textos(panel.cards))


class TestAnalisisSinMarkdown:

    def test_negritas_titulos_y_vinetas(self):
        crudo = ("Aquí tienes la descripción:\n\n"
                 "**A: Personaje**\n"
                 "*   **Sujeto:** Una mujer joven.\n"
                 "- Pose: de frente\n"
                 "### B\n"
                 "__Escenario__: estación")
        limpio = texto_sin_markdown(crudo)
        assert "**" not in limpio and "__" not in limpio and "###" not in limpio
        assert "A: Personaje" in limpio
        assert "• Sujeto: Una mujer joven." in limpio
        assert "• Pose: de frente" in limpio
        assert "\nB\n" in limpio
        assert "Escenario: estación" in limpio

    def test_el_texto_normal_no_cambia(self):
        normal = "Una mujer joven con auriculares, 2 * 3 = 6, y un guion - suelto."
        assert texto_sin_markdown(normal) == normal

    def test_lo_que_ve_el_usuario_al_analizar(self, root):
        class _Vision:
            def nombres_proveedores(self):
                return ["Gemini"]

            def describir_con_prompt(self, imagen, prompt_v, on_status=None, proveedor=None):
                return "**A: Personaje**\n*   **Sujeto:** Una mujer joven.", "Gemini"

        class _Futuro:
            def __init__(self, fn):
                self._valor = fn()

            def done(self):
                return True

            def result(self):
                return self._valor

        previas = getattr(root, "vision", None), getattr(root, "_executor", None)
        root.vision = _Vision()
        root._executor = type("E", (), {"submit": lambda self, fn: _Futuro(fn)})()
        try:
            v = VisualStudio(root)
            bombear(root)
            v.refs.append(Reference(Image.new("RGB", (32, 24), "red"), ROLES[0], "a.png"))
            v.analyze()
            bombear(root, 300)
            texto = v.analysis.get("1.0", "end")
            assert "**" not in texto, texto
            assert "• Sujeto: Una mujer joven." in texto
            v.destroy()
        finally:
            for nombre, previa in zip(("vision", "_executor"), previas):
                if previa is None:
                    try:
                        delattr(root, nombre)
                    except Exception:
                        pass
                else:
                    setattr(root, nombre, previa)
