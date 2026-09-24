"""Cada caja del panel dice qué es, esté vacía, escrita o recién abierta.

Las cajas de una línea de «Crear desde imágenes» no tenían rótulo: el texto
gris de ejemplo hacía de rótulo. Y ese texto desaparece en tres casos, los
tres vistos en capturas de la app real el 24-sep-2026:

  • en cuanto el usuario escribe algo;
  • al abrir un proyecto: `open_project()` hacía `insert(0, "")` en cada
    caja, y CustomTkinter quita el texto de ejemplo incluso con una cadena
    vacía. Quedaban cinco cajas en blanco sin saber qué era cada una;
  • en el buscador de modelos, siempre: con `textvariable`, CustomTkinter no
    pinta nunca el texto de ejemplo.

Ahora cada una lleva un rótulo propio a la izquierda y el gris es solo el
ejemplo.
"""
import pytest
from PIL import Image

ctk = pytest.importorskip("customtkinter")

from modules import i18n
from modules.visual_brief import MODES, ROLES, Reference, save_project
from modules.visual_studio import VisualStudio

# (atributo, rótulo, ejemplo)
CAJAS = [
    ("project_name", "Proyecto", "nombre para reconocerlo en «Recuperar versiones»"),
    ("preserve", "Conservar", "ej.: rostro, ropa, forma del producto"),
    ("change", "Cambiar", "ej.: fondo, pose, iluminación"),
    ("camera", "Cámara", "fija, acercamiento lento, seguimiento…"),
    ("environment_motion", "Entorno", "niebla, viento, luces, objetos…"),
    ("audio_direction", "Sonido", "ambiente; diálogo literal e idioma si lo necesitas"),
    ("transition_direction", "Inicio → final", "cómo pasar de A a B, sin saltos"),
    ("revision_instruction", "Qué mejorar", "opcional: más cinematográfico, menos adornos…"),
    ("manual_limit", "Límite manual", "caracteres; vacío = el del catálogo"),
]


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


def _rotulo(caja):
    """El texto del rótulo que acompaña a la caja en su fila, o None."""
    for hermano in caja.master.winfo_children():
        if isinstance(hermano, ctk.CTkLabel) and hermano.cget("text").strip():
            return hermano.cget("text")
    return None


def _abrir_guardado(origen, root, ruta):
    antes = set(root.winfo_children())
    origen.open_project(str(ruta))
    _bombear(root, 250)
    nuevos = [w for w in root.winfo_children()
              if w not in antes and isinstance(w, VisualStudio)]
    assert nuevos, "open_project no abrió ningún panel"
    return nuevos[0]


class TestCadaCajaTieneRotulo:

    @pytest.mark.parametrize("attr,rotulo,ejemplo", CAJAS, ids=[c[0] for c in CAJAS])
    def test_rotulo_propio_y_ejemplo_aparte(self, root, attr, rotulo, ejemplo):
        v = VisualStudio(root)
        _bombear(root)
        caja = getattr(v, attr)
        assert _rotulo(caja) == rotulo, f"{attr} sin rótulo propio"
        # Vacía, enseña el ejemplo; y get() no lo confunde con un valor.
        assert caja._entry.get() == ejemplo
        assert caja.get() == ""
        v.destroy()

    def test_el_rotulo_sigue_al_escribir(self, root):
        v = VisualStudio(root)
        _bombear(root)
        v.preserve.insert(0, "la chaqueta")
        _bombear(root)
        assert _rotulo(v.preserve) == "Conservar"
        v.destroy()

    def test_el_buscador_de_modelos_tambien(self, root):
        v = VisualStudio(root)
        _bombear(root)
        cajas = []

        def recorrer(w):
            for h in w.winfo_children():
                if isinstance(h, ctk.CTkEntry) and str(h.cget("textvariable")) == str(v.model_search):
                    cajas.append(h)
                recorrer(h)

        recorrer(v)
        assert len(cajas) == 1, "no encuentro la caja del buscador de modelos"
        assert _rotulo(cajas[0]) == "Buscar modelo"
        v.destroy()

    def test_en_ingles(self, root):
        i18n.set_idioma("en")
        try:
            v = VisualStudio(root)
            _bombear(root)
            assert _rotulo(v.preserve) == "Keep"
            assert v.preserve._entry.get() == "e.g. face, clothing, product shape"
            assert _rotulo(v.manual_limit) == "Manual limit"
            v.destroy()
        finally:
            i18n.set_idioma("es")


class TestAbrirUnProyectoConservaLosEjemplos:

    def test_las_cajas_vacias_siguen_ensenando_su_ejemplo(self, root, tmp_path):
        origen = VisualStudio(root)
        _bombear(root)
        origen.mode.set(MODES[3])
        origen.refs.append(Reference(Image.new("RGB", (32, 24), "red"), ROLES[0], "a.png"))
        origen.refs.append(Reference(Image.new("RGB", (32, 24), "blue"), ROLES[2], "b.png"))
        origen.project_name.insert(0, "Estación")
        destino = tmp_path / "p.gprompt"
        save_project(str(destino), origen.refs, origen.fields())

        abierto = _abrir_guardado(origen, root, destino)
        # Lo que tenía valor, lo enseña.
        assert abierto.project_name.get() == "Estación"
        # Lo que estaba vacío sigue enseñando su ejemplo, no una caja en blanco.
        for attr, _rotulo_esperado, ejemplo in CAJAS:
            if attr == "project_name":
                continue
            caja = getattr(abierto, attr)
            assert caja._entry.get() == ejemplo, f"{attr} perdió su ejemplo al abrir"
            assert caja.get() == ""
        abierto.destroy()
        origen.destroy()
