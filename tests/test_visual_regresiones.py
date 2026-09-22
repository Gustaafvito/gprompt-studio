"""Los tres recorridos que destapó ChatGPT revisando `10a398f`.

Dos de los tres son regresiones que introdujo ese mismo commit, y conviene
decirlo: el arreglo de i18n y el del foco trajeron cada uno su efecto
colateral, invisible para los 1.500 tests porque ninguno recorría «abrir un
proyecto» ni «dos referencias con el mismo nombre de archivo».

1. Al separar los desplegables de sus variables (`variable=` fuera, para que el
   menú pudiera enseñar inglés sin escribir inglés en la variable),
   `open_project()` se quedó restaurando solo las variables. Los menús seguían
   mostrando lo que tenían al construirse: un proyecto guardado como
   «Inicio → final», 16:9 y español se abría enseñando «Imagen → prompt», 9:16
   e inglés. El valor interno era el correcto, que es justo lo que lo hacía
   difícil de ver — y peligroso: el usuario cree que edita otra cosa.

2. `GPromptWindow` deduplica por título, y la vista previa se titulaba con el
   nombre del archivo. Dos referencias llamadas `imagen.png` compartían
   ventana: la segunda se cerraba sola y enfocaba la primera, enseñando la
   imagen equivocada. Antes no pasaba porque un `CTkToplevel` pelado no
   deduplica nada.

3. `INICIO`, `FINAL` y «Sobra: quitar» se quedaron sin `tr()`. Se escaparon de
   los candados porque el modo inicio/final no se construía en ningún test.
"""
import inspect

import pytest
from PIL import Image

ctk = pytest.importorskip("customtkinter")

from modules import i18n
from modules.gprompt_window import GPromptWindow
from modules.visual_brief import MODES, ROLES, Reference
from modules.visual_studio import VisualStudio


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


def _img(color="red"):
    return Image.new("RGB", (32, 24), color)


def _previas(panel):
    return [w for w in panel.winfo_children()
            if isinstance(w, GPromptWindow) and w.winfo_exists()]


class TestAbrirUnProyectoDejaLosMenusAlDia:

    def test_los_tres_menus_siguen_al_valor_restaurado(self, root):
        v = VisualStudio(root)
        _bombear(root)
        # Lo que hace open_project(): fijar las variables internas.
        v.mode.set(MODES[2])
        v.aspect.set("16:9")
        v.language.set("Español")
        v.sync_menus()
        _bombear(root)

        assert v.mode_menu.get() == i18n.tr(MODES[2]), (
            "el menú de modo no refleja el proyecto abierto")
        assert v.aspect_menu.get() == "16:9"
        assert v.language_menu.get() == i18n.tr("Español")
        v.destroy()

    def test_open_project_llama_a_sync_menus(self):
        fuente = inspect.getsource(VisualStudio.open_project)
        assert "sync_menus()" in fuente, (
            "sin esto los desplegables mienten sobre el proyecto cargado")

    def test_tambien_en_ingles(self, root):
        i18n.set_idioma("en")
        try:
            v = VisualStudio(root)
            _bombear(root)
            v.mode.set(MODES[2])
            v.language.set("Español")
            v.sync_menus()
            _bombear(root)
            # Se PINTA en ingles...
            assert v.mode_menu.get() == "Start → end"
            assert v.language_menu.get() == "Spanish"
            # ...y la variable conserva el identificador.
            assert v.mode.get() == MODES[2]
            assert v.language.get() == "Español"
            v.destroy()
        finally:
            i18n.set_idioma("es")


class TestDosImagenesConElMismoNombre:

    def test_cada_referencia_abre_su_propia_ventana(self, root):
        v = VisualStudio(root)
        _bombear(root)
        # El caso real: dos carpetas distintas, mismo nombre de archivo.
        v.refs.append(Reference(_img("red"), ROLES[0], "imagen.png"))
        v.refs.append(Reference(_img("blue"), ROLES[0], "imagen.png"))

        v.preview_reference(0)
        _bombear(root, 180)
        v.preview_reference(1)
        _bombear(root, 180)

        abiertas = _previas(v)
        assert len(abiertas) == 2, (
            "dos referencias distintas comparten ventana "
            f"({len(abiertas)} abierta/s): la segunda ensena la imagen de la "
            "primera")
        titulos = {w.title() for w in abiertas}
        assert len(titulos) == 2, f"titulos duplicados: {titulos}"
        for w in abiertas:
            w.destroy()
        v.destroy()

    def test_dos_paneles_distintos_no_se_pisan(self, root):
        uno = VisualStudio(root)
        dos = VisualStudio(root)
        _bombear(root)
        uno.refs.append(Reference(_img("red"), ROLES[0], "imagen.png"))
        dos.refs.append(Reference(_img("blue"), ROLES[0], "imagen.png"))
        uno.preview_reference(0)
        _bombear(root, 180)
        dos.preview_reference(0)
        _bombear(root, 180)

        abiertas = _previas(uno) + _previas(dos)
        assert len(abiertas) == 2, (
            "dos paneles con el mismo nombre de archivo comparten vista previa")
        for w in abiertas:
            w.destroy()
        uno.destroy()
        dos.destroy()

    def test_repetir_la_misma_referencia_reutiliza_su_ventana(self, root):
        # Lo contrario tambien importa: la lupa dos veces sobre la MISMA
        # referencia no debe apilar ventanas.
        v = VisualStudio(root)
        _bombear(root)
        v.refs.append(Reference(_img(), ROLES[0], "unica.png"))
        v.preview_reference(0)
        _bombear(root, 180)
        v.preview_reference(0)
        _bombear(root, 180)
        abiertas = _previas(v)
        assert len(abiertas) == 1, (
            f"{len(abiertas)} ventanas para una sola referencia")
        for w in abiertas:
            w.destroy()
        v.destroy()


class TestElModoInicioFinalTambienSeTraduce:

    def test_las_etiquetas_pasan_por_tr(self):
        # Por AST y no por subcadena: buscar '"INICIO"' casaria tambien dentro
        # de tr("INICIO"), que es justo lo que se quiere. Aqui se recogen los
        # literales que NO cuelgan de una llamada a tr().
        import ast

        arbol = ast.parse(inspect.getsource(VisualStudio.render).lstrip())
        dentro_de_tr = set()
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Call):
                f = nodo.func
                nombre = f.attr if isinstance(f, ast.Attribute) else (
                    f.id if isinstance(f, ast.Name) else "")
                if nombre == "tr":
                    for a in nodo.args:
                        if isinstance(a, ast.Constant):
                            dentro_de_tr.add(id(a))
        sueltos = [n.value for n in ast.walk(arbol)
                   if isinstance(n, ast.Constant)
                   and isinstance(n.value, str)
                   and n.value in ("INICIO", "FINAL", "Sobra: quitar")
                   and id(n) not in dentro_de_tr]
        assert not sueltos, f"llegan a la UI sin tr(): {sueltos}"

    def test_tienen_traduccion(self):
        for texto in ("INICIO", "FINAL", "Sobra: quitar"):
            assert texto in i18n.TRADUCCIONES, "falta el ingles de " + texto

    def test_la_ventana_en_ingles_no_deja_rastro_espanol(self, root):
        """El estado que no cubria ningun test: inicio/final CON referencias."""
        i18n.set_idioma("en")
        try:
            v = VisualStudio(root)
            _bombear(root)
            v.mode.set(MODES[2])
            v.refs.append(Reference(_img("red"), ROLES[0], "a.png"))
            v.refs.append(Reference(_img("blue"), ROLES[0], "b.png"))
            v.refs.append(Reference(_img("green"), ROLES[0], "c.png"))
            v.render()
            _bombear(root)

            textos = []

            def recorrer(w, prof=0):
                if prof > 14:
                    return
                for hijo in w.winfo_children():
                    try:
                        val = hijo.cget("text")
                    except Exception:
                        val = None
                    if isinstance(val, str) and val.strip():
                        textos.append(val)
                    recorrer(hijo, prof + 1)

            recorrer(v)
            crudos = [t for t in textos
                      if "INICIO" in t or "FINAL" in t or "Sobra" in t]
            assert not crudos, f"etiquetas sin traducir: {crudos}"
            v.destroy()
        finally:
            i18n.set_idioma("es")


class TestElRecorridoCompletoDeGuardarYAbrir:
    """Guardar de verdad, abrir de verdad, y mirar lo que se ve en pantalla.

    Los tests de arriba llaman a `sync_menus()` a mano, que prueba el arreglo
    pero no el recorrido. Este pasa por `save_project()` y `open_project()`
    como lo haría el usuario, que es donde estaba la regresión: el fallo no
    era que `sync_menus()` no funcionara —no existía— sino que nadie lo
    llamaba al abrir.
    """

    def test_lo_guardado_es_lo_que_se_ve_al_reabrir(self, root, tmp_path):
        from modules.visual_brief import save_project

        origen = VisualStudio(root)
        _bombear(root)
        origen.mode.set(MODES[2])
        origen.aspect.set("16:9")
        origen.language.set("Español")
        origen.refs.append(Reference(_img("red"), ROLES[0], "a.png"))
        origen.refs.append(Reference(_img("blue"), ROLES[0], "b.png"))
        origen.project_name.insert(0, "Prueba recorrido")

        destino = tmp_path / "proyecto.gprompt"
        save_project(str(destino), origen.refs, origen.fields())

        # open_project abre un panel NUEVO, que es lo que hace de verdad.
        antes = set(root.winfo_children())
        origen.open_project(str(destino))
        _bombear(root, 250)
        nuevos = [w for w in root.winfo_children()
                  if w not in antes and isinstance(w, VisualStudio)]
        assert nuevos, "open_project no abrió ningún panel"
        abierto = nuevos[0]

        # Lo que se VE en los tres desplegables.
        assert abierto.mode_menu.get() == i18n.tr(MODES[2]), (
            "el desplegable de modo enseña "
            + repr(abierto.mode_menu.get())
            + " y el proyecto se guardó como "
            + repr(MODES[2]))
        assert abierto.aspect_menu.get() == "16:9"
        assert abierto.language_menu.get() == i18n.tr("Español")

        # Y lo que se GUARDA sigue siendo el identificador.
        assert abierto.mode.get() == MODES[2]
        assert abierto.language.get() == "Español"

        abierto.destroy()
        origen.destroy()

    def test_el_recorrido_tambien_en_ingles(self, root, tmp_path):
        from modules.visual_brief import save_project

        origen = VisualStudio(root)
        _bombear(root)
        origen.mode.set(MODES[1])
        origen.aspect.set("1:1")
        origen.refs.append(Reference(_img(), ROLES[0], "a.png"))
        destino = tmp_path / "en.gprompt"
        save_project(str(destino), origen.refs, origen.fields())

        i18n.set_idioma("en")
        try:
            antes = set(root.winfo_children())
            origen.open_project(str(destino))
            _bombear(root, 250)
            nuevos = [w for w in root.winfo_children()
                      if w not in antes and isinstance(w, VisualStudio)]
            abierto = nuevos[0]
            assert abierto.mode_menu.get() == "Animate image"
            assert abierto.aspect_menu.get() == "1:1"
            assert abierto.mode.get() == MODES[1]
            abierto.destroy()
        finally:
            i18n.set_idioma("es")
        origen.destroy()
