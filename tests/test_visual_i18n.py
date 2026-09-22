"""El panel visual no puede volver a enseñar español con la interfaz en inglés.

22-sep-2026. `text_field()` y `entry()` pasaban su rótulo directo al widget:

    ctk.CTkLabel(parent, text=label)          # label es una VARIABLE

El candado general (`tests/test_i18n.py::test_ningun_sink_de_ui_con_espanol_sin_tr`)
no lo veía, y con razón: solo mira literales que llegan a un sink. Aquí el
literal está en quien LLAMA al ayudante, que no es un sink de nada. Catorce
rótulos —«Prompt positivo», «Tu idea / acción deseada»— salían en español con
la app en inglés.

El arreglo fue traducir dentro del ayudante. Estos candados vigilan las dos
mitades: que el ayudante siga aplicando `tr()`, y que cada texto que se le pasa
tenga su entrada inglesa. Sin el segundo, añadir un campo nuevo volvería a
dejar español sin que saltara nada.

Lo que estos tests NO exigen, a propósito: que el texto que viaja al LLM esté
traducido. `VISUAL_SYSTEM` y los constructores de instrucciones de
`visual_brief` están en español porque el modelo los lee así; traducirlos
cambiaría lo que genera. Igual con `MODES` y `ROLES`, que se guardan dentro de
los proyectos: si cambiara su valor, un proyecto guardado dejaría de abrirse.
"""
import ast
import inspect
from pathlib import Path

from modules import i18n
from modules.visual_studio import VisualStudio

RAIZ = Path(__file__).resolve().parent.parent
FUENTE = (RAIZ / "modules" / "visual_studio.py").read_text(encoding="utf-8")
AYUDANTES = ("text_field", "entry")


def _literales_pasados(nombre):
    """Los textos que se le pasan al ayudante desde cualquier punto del fichero."""
    arbol = ast.parse(FUENTE)
    textos = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.Call):
            continue
        f = nodo.func
        llamada = f.attr if isinstance(f, ast.Attribute) else (
            f.id if isinstance(f, ast.Name) else "")
        if llamada != nombre:
            continue
        for arg in nodo.args[1:2]:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                textos.append(arg.value)
    return textos


class TestLosAyudantesTraducen:

    def test_text_field_aplica_tr(self):
        fuente = inspect.getsource(VisualStudio.text_field)
        assert "tr(label)" in fuente, (
            "text_field volvería a pintar el rótulo en español con la app en inglés")

    def test_entry_aplica_tr(self):
        fuente = inspect.getsource(VisualStudio.entry)
        assert "tr(placeholder)" in fuente, (
            "entry volvería a pintar el marcador en español con la app en inglés")


class TestTodoLoQuePasaPorEllosTieneIngles:

    def test_hay_textos_que_vigilar(self):
        # Si alguien renombra los ayudantes, los tests de abajo pasarían
        # vacíos y en verde sin comprobar nada.
        total = sum(len(_literales_pasados(n)) for n in AYUDANTES)
        assert total >= 10, f"solo {total} textos: ¿se renombró el ayudante?"

    def test_ninguno_se_queda_sin_traducir(self):
        faltan = [t for n in AYUDANTES for t in _literales_pasados(n)
                  if t not in i18n.TRADUCCIONES]
        assert not faltan, (
            f"{len(faltan)} rótulos del panel visual sin inglés: {faltan[:5]}")


class TestLosEstadosDelPanelTambien:
    """`self.status.set(...)` es el sitio por donde el panel habla al usuario."""

    def test_ningun_status_set_con_literal_pelado(self):
        arbol = ast.parse(FUENTE)
        fugas = []
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Call):
                continue
            f = nodo.func
            if not (isinstance(f, ast.Attribute) and f.attr == "set"):
                continue
            base = f.value
            if not (isinstance(base, ast.Attribute) and base.attr == "status"):
                continue
            for arg in nodo.args[:1]:
                if isinstance(arg, (ast.Constant, ast.JoinedStr)):
                    fugas.append(nodo.lineno)
        assert not fugas, (
            f"status.set con texto sin tr() en las líneas {fugas}")


class TestLosMenusGuardanElIdentificador:
    """Se PINTA la traducción, se GUARDA el identificador español.

    `MODES` y `ROLES` no son rótulos: su valor se serializa dentro del
    `.gprompt` y, en el caso del idioma, viaja literalmente al prompt del
    modelo («IDIOMA DEL PROMPT: Inglés»). Si el desplegable escribiera el texto
    mostrado en la variable, con la app en inglés se romperían a la vez las
    comparaciones `self.mode.get() == MODES[n]`, los proyectos ya guardados y
    la instrucción que lee el modelo.

    Por eso los menús van sin `variable=` y con `tr_es()` en la devolución de
    llamada, que es el patrón que este fichero ya usaba en `target_changed()`.
    """

    def test_el_menu_de_modos_no_escribe_en_la_variable(self):
        fuente = inspect.getsource(VisualStudio)
        assert "values=[tr(m) for m in MODES]" in fuente, (
            "el desplegable de modos volvería a enseñar español en inglés")
        # Con la coma: sin ella, la subcadena casa tambien con
        # "variable=self.model", que es otro desplegable y es legitimo.
        assert "variable=self.mode," not in fuente, (
            "con variable= el menú escribe el texto MOSTRADO en self.mode")

    def test_mode_changed_destraduce(self):
        fuente = inspect.getsource(VisualStudio.mode_changed)
        assert "tr_es(value)" in fuente

    def test_role_changed_destraduce(self):
        fuente = inspect.getsource(VisualStudio.role_changed)
        assert "tr_es(role)" in fuente

    def test_los_identificadores_tienen_ingles(self):
        from modules.visual_brief import MODES, ROLES
        faltan = [v for v in list(MODES) + list(ROLES)
                  if v not in i18n.TRADUCCIONES]
        assert not faltan, f"identificadores sin traducción: {faltan}"

    def test_la_vuelta_es_exacta(self):
        """tr_es(tr(x)) == x para cada identificador, en inglés.

        Es lo que de verdad protege los proyectos guardados: si dos
        identificadores compartieran traducción, la vuelta devolvería el otro y
        el proyecto se guardaría con un modo o una función equivocados.
        """
        from modules.visual_brief import MODES, ROLES
        i18n.set_idioma("en")
        try:
            malos = [v for v in list(MODES) + list(ROLES)
                     if i18n.tr_es(i18n.tr(v)) != v]
        finally:
            i18n.set_idioma("es")
        assert not malos, f"la ida y vuelta no es exacta para: {malos}"

    def test_el_idioma_del_prompt_sigue_en_espanol(self):
        # self.language.get() se incrusta en el prompt del modelo.
        i18n.set_idioma("en")
        try:
            assert i18n.tr_es("English") == "Inglés"
            assert i18n.tr_es("Spanish") == "Español"
        finally:
            i18n.set_idioma("es")
