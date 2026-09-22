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


class TestLaVistaPreviaEnsenaLaImagenCORRECTA:
    """Ni la posicion ni el nombre identifican una imagen.

    Cuarto hallazgo de ChatGPT, y el mas fino de los cuatro. El titulo era
    «letra · nombre · panel», y eso parecia unico hasta que las referencias se
    mueven:

        1. dos imagenes distintas llamadas imagen.png
        2. amplias A y dejas la vista previa abierta
        3. intercambias A/B
        4. amplias la nueva A  ->  mismo titulo que el paso 2

    GPromptWindow deduplica por titulo, asi que devolvia la ventana vieja: la
    imagen equivocada, con el titulo correcto. Pasa igual quitando una
    referencia y anadiendo otra que se llame como la que habia.

    Estos tests miran la IMAGEN QUE SE VE, no cuantas ventanas hay. Contar
    ventanas daba verde en este caso: hay una, y es la de antes.
    """

    def _imagen_mostrada(self, ventana):
        """El PIL que la ventana esta pintando ahora mismo."""
        for hijo in ventana.winfo_children():
            imagen = getattr(hijo, "image", None)
            if imagen is not None:
                # CTkImage guarda el PIL original en light_image.
                return imagen.cget("light_image")
        return None

    def test_tras_intercambiar_ensena_la_nueva_A(self, root):
        roja, azul = _img("red"), _img("blue")
        v = VisualStudio(root)
        _bombear(root)
        v.refs.append(Reference(roja, ROLES[0], "imagen.png"))
        v.refs.append(Reference(azul, ROLES[0], "imagen.png"))

        v.preview_reference(0)          # A = roja
        _bombear(root, 200)
        v.swap()                        # ahora A = azul
        _bombear(root, 200)
        v.preview_reference(0)          # ampliar la NUEVA A
        _bombear(root, 220)

        ventanas = [w for w in v.winfo_children()
                    if isinstance(w, GPromptWindow) and w.winfo_exists()]
        mostradas = [self._imagen_mostrada(w) for w in ventanas]
        assert azul in mostradas, (
            "tras intercambiar, ampliar A no ensena la imagen de A; "
            "se ven " + str(len(ventanas)) + " ventana(s)")

        # Y la etiqueta tiene que seguir a la imagen. La roja paso a ser B: su
        # ventana ya no puede decir «A». La imagen mostrada siempre fue la
        # correcta —de eso se encarga el uid— pero un titulo caducado despista.
        por_imagen = {id(self._imagen_mostrada(w)): w.title() for w in ventanas}
        assert por_imagen[id(roja)].startswith("B "), (
            "la ventana de la imagen roja dice " + repr(por_imagen[id(roja)])
            + " cuando su referencia ya es la B")
        assert por_imagen[id(azul)].startswith("A "), (
            "la ventana de la imagen azul deberia decir A")
        for w in ventanas:
            w.destroy()
        v.destroy()

    def test_quitar_y_anadir_con_el_mismo_nombre(self, root):
        vieja, nueva = _img("red"), _img("green")
        v = VisualStudio(root)
        _bombear(root)
        v.refs.append(Reference(vieja, ROLES[0], "imagen.png"))
        v.preview_reference(0)
        _bombear(root, 200)

        v.refs.pop(0)
        v.refs.append(Reference(nueva, ROLES[0], "imagen.png"))
        v.render()
        _bombear(root, 200)
        v.preview_reference(0)
        _bombear(root, 220)

        ventanas = [w for w in v.winfo_children()
                    if isinstance(w, GPromptWindow) and w.winfo_exists()]
        mostradas = [self._imagen_mostrada(w) for w in ventanas]
        assert nueva in mostradas, (
            "la referencia nueva reutiliza la ventana de la que se quito")
        assert vieja not in mostradas, (
            "sigue abierta la vista previa de una referencia que ya no existe")
        for w in ventanas:
            w.destroy()
        v.destroy()

    def test_cambiar_la_funcion_conserva_su_ventana(self, root):
        """role_changed() RECONSTRUYE el Reference; sigue siendo la misma imagen.

        Si la identidad se perdiera al cambiar la funcion, la vista previa
        abierta quedaria huerfana y ampliar otra vez abriria una segunda.
        """
        roja = _img("red")
        v = VisualStudio(root)
        _bombear(root)
        v.refs.append(Reference(roja, ROLES[0], "imagen.png"))
        v.preview_reference(0)
        _bombear(root, 200)
        v.role_changed(0, i18n.tr(ROLES[1]))
        _bombear(root, 200)
        v.preview_reference(0)
        _bombear(root, 220)

        ventanas = [w for w in v.winfo_children()
                    if isinstance(w, GPromptWindow) and w.winfo_exists()]
        assert len(ventanas) == 1, (
            "cambiar la funcion dejo " + str(len(ventanas)) + " ventanas")
        assert self._imagen_mostrada(ventanas[0]) is roja
        assert v.refs[0].role == ROLES[1]
        for w in ventanas:
            w.destroy()
        v.destroy()

    def test_el_titulo_se_recalcula_al_quitar_una_referencia(self, root):
        """Quitar la A convierte a la B en A: su ventana tiene que enterarse."""
        primera, segunda = _img("red"), _img("blue")
        v = VisualStudio(root)
        _bombear(root)
        v.refs.append(Reference(primera, ROLES[0], "una.png"))
        v.refs.append(Reference(segunda, ROLES[0], "otra.png"))
        v.preview_reference(1)          # ampliar la B
        _bombear(root, 200)
        ventana = v.previews[v.refs[1].uid]
        assert ventana.title().startswith("B ")

        v.refs.pop(0)                   # la B pasa a ser la A
        v.render()
        _bombear(root, 200)
        assert ventana.title().startswith("A "), (
            "el titulo se quedo en " + repr(ventana.title()))
        assert self._imagen_mostrada(ventana) is segunda
        ventana.destroy()
        v.destroy()

    def test_el_titulo_sigue_siendo_solo_una_etiqueta(self, root):
        """Dos ventanas pueden compartir titulo sin pisarse.

        Es la diferencia con el diseno anterior: el titulo ya no es clave de
        nada. Si volviera a serlo, este test caeria.
        """
        v = VisualStudio(root)
        _bombear(root)
        v.refs.append(Reference(_img("red"), ROLES[0], "imagen.png"))
        v.refs.append(Reference(_img("blue"), ROLES[0], "imagen.png"))
        v.preview_reference(0)
        _bombear(root, 200)
        v.preview_reference(1)
        _bombear(root, 220)
        abiertas = [w for w in v.previews.values() if w.winfo_exists()]
        assert len(abiertas) == 2
        # Se les fuerza el MISMO titulo: ninguna debe cerrarse.
        for w in abiertas:
            w.title("mismo titulo para las dos")
        _bombear(root, 200)
        assert all(w.winfo_exists() for w in abiertas), (
            "una ventana se autocerro por compartir titulo: ha vuelto la "
            "deduplicacion de GPromptWindow")
        for w in abiertas:
            w.destroy()
        v.destroy()
