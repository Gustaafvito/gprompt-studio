"""Cada estilo del desplegable tiene que inyectar algo de verdad.

11-sep-2026. El usuario se fijó en que la familia `gpt_image` ofrecía seis
estilos y ninguno era de arte estilizado — ni anime, ni cómic, ni 3D— mientras
que `flux` y `z_image` llevan Anime desde siempre. La lista estaba curada hacia
diseño comercial (Editorial, UI-Mockup, Poster-Typography), que es donde este
modelo gana por su texto en imagen, pero se pasó de frenada: GPT Image 2.5 hace
anime de sobra.

El fallo que estos candados persiguen no es que falte un estilo, sino algo más
silencioso: **un estilo puede aparecer en el desplegable sin tener inyección
detrás**. Las dos listas viven en ficheros distintos —`ESTILOS_POR_FAMILIA` en
`config.py`, el mapa de textos en `prompts_inyeccion.py`— y nada las ataba.
Añadir uno solo en `config.py` da una opción que el usuario elige, que no falla,
y que **no hace absolutamente nada**: el peor tipo de error, porque parece que
funciona.

Se añaden tres y no más a propósito. El selector de estilos generales (333
entradas) ya existe y se aplica encima; este desplegable es el TIPO de imagen.
"""
import pytest

import config

FAMILIA = "gpt_image"
ESTILOS = config.ESTILOS_POR_FAMILIA[FAMILIA]


def _mapa_de_inyeccion():
    """Los estilos que `_inyectar_formato_gpt_image` sabe traducir.

    Se lee del fuente en vez de llamar al método: el mapa es un literal dentro
    de la función y montar el host de UI para leerlo costaría más que el test.
    """
    from pathlib import Path
    ruta = Path(config.__file__).parent / "modules" / "prompts_inyeccion.py"
    txt = ruta.read_text(encoding="utf-8")
    ini = txt.index("estilo_map_gpt = {")
    fin = txt.index("hint = estilo_map_gpt.get", ini)
    return txt[ini:fin]


class TestTodoEstiloOfrecidoSeInyecta:

    @pytest.mark.parametrize("estilo", [e for e in ESTILOS if e != "Auto"])
    def test_tiene_bloque_de_inyeccion(self, estilo):
        assert f'"{estilo}": (' in _mapa_de_inyeccion(), (
            f"«{estilo}» sale en el desplegable de {FAMILIA} pero no tiene "
            f"texto que inyectar: el usuario lo elige, no falla, y no pasa "
            f"nada. Añádelo a estilo_map_gpt en prompts_inyeccion.py")

    def test_auto_no_tiene_bloque(self):
        # "Auto" significa no forzar nada; si tuviera bloque, forzaría.
        assert '"Auto": (' not in _mapa_de_inyeccion()


class TestLaFamiliaCubreArteEstilizado:
    """Lo que destapó el repaso: solo había opciones de diseño comercial."""

    def test_hay_anime(self):
        assert "Anime" in ESTILOS, (
            "todas las demás familias ofrecen Anime y este modelo lo hace")

    def test_sigue_habiendo_opciones_de_diseño(self):
        # El sesgo comercial era deliberado: es la ventaja real de GPT Image.
        # Añadir arte no puede haberse llevado por delante lo que ya valía.
        for e in ("Editorial", "UI-Mockup", "Poster-Typography"):
            assert e in ESTILOS

    def test_empieza_por_auto(self):
        assert ESTILOS[0] == "Auto"

    def test_sin_duplicados(self):
        assert len(ESTILOS) == len(set(ESTILOS))


class TestElDesplegableNoDuplicaAlSelectorGeneral:

    def test_sigue_siendo_una_lista_corta(self):
        # Los estilos generales son 333 y se aplican ENCIMA de este. Este
        # desplegable es el «tipo de imagen»: si crece, estorba en vez de
        # ayudar y se solapa con el otro.
        assert len(ESTILOS) <= 12, (
            f"{len(ESTILOS)} estilos en {FAMILIA}: esto ya es un listín, "
            f"no un selector de tipo de imagen")
