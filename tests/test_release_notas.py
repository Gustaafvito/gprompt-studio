"""El texto del release no puede prometer cifras que no son.

09-sep-2026, preparando la publicación. El borrador decía "350 modelos" y
esa cifra salía de la auditoría del día anterior, que contó los **97
checkpoints locales de ComfyUI del autor**. Un usuario que instala no tiene
esos: ve las fichas empaquetadas y las suyas propias. Prometer 350 y
entregar 276 es una decepción evitable, y ademas la version honesta vende
mejor — "276 fichas, y encima las tuyas si usas ComfyUI".

Este candado ata la cifra del texto al contenido real de `data/`, así que
añadir o retirar modelos hace fallar el test hasta que se actualice el
texto. Los hashes los vigila `build_release.py`, que los recalcula en cada
build y avisa si el texto lleva los de otro.
"""
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOTAS = RAIZ / "docs" / "RELEASE-v1.0.0.md"


def _seleccionables():
    """(imagen, vídeo, audio) que el usuario puede ELEGIR de verdad.

    No se cuentan las fichas del JSON: hay fichas que no cuelgan de ningún
    desplegable y prometerlas infla la cifra. Tampoco los de ComfyUI, que
    existen solo en el ordenador de quien los tenga — contarlos fue
    justamente el error de los "406 modelos".
    """
    import config

    def _limpio(lista):
        return {m for m in lista if not m.startswith("──")}

    img = set().union(*[_limpio(l)
                        for p, l in config.MODELOS_POR_PLATAFORMA_IMAGEN.items()
                        if "ComfyUI" not in p])
    vid = set().union(*[_limpio(l)
                        for p, l in config.MODELOS_POR_PLATAFORMA_VIDEO.items()
                        if "ComfyUI" not in p])
    return len(img), len(vid), len(_limpio(config.MODELOS_AUDIO_FLAT))


class TestLasCifrasCuadranConElCatalogo:

    def test_el_total_es_el_de_los_seleccionables(self):
        real = sum(_seleccionables())
        texto = NOTAS.read_text(encoding="utf-8")
        anunciados = {int(n) for n in re.findall(r"\*\*(\d{3}) modelos", texto)}
        assert anunciados, "el texto del release ya no anuncia ninguna cifra"
        assert anunciados == {real}, (
            f"el release anuncia {anunciados} y son {real} seleccionables")

    def test_el_desglose_por_modo_tambien(self):
        texto = NOTAS.read_text(encoding="utf-8")
        m = re.search(r"(\d+) de imagen, (\d+) de vídeo, (\d+) de\s*\n?\s*audio",
                      texto)
        assert m, "no encuentro el desglose por modo en el release"
        assert tuple(int(x) for x in m.groups()) == _seleccionables()

    def test_no_promete_los_modelos_locales_del_autor(self):
        # La cifra vieja (350) incluía los 97 checkpoints de ComfyUI del
        # autor. Nadie más los tiene.
        texto = NOTAS.read_text(encoding="utf-8")
        for fantasma in ("350 modelos", "352 modelos"):
            assert fantasma not in texto


class TestElTextoDiceLoImprescindible:

    def test_avisa_de_smartscreen(self):
        # Sin este aviso, el usuario se encuentra la pantalla azul de
        # Windows sin contexto y abandona la instalación.
        assert "SmartScreen" in NOTAS.read_text(encoding="utf-8")

    def test_publica_los_dos_hashes(self):
        texto = NOTAS.read_text(encoding="utf-8")
        assert len(re.findall(r"\b[0-9a-f]{64}\b", texto)) >= 2, (
            "los SHA-256 son lo que permite verificar un .exe sin firmar")

    def test_dice_la_licencia(self):
        assert "Apache 2.0" in NOTAS.read_text(encoding="utf-8")

    def test_no_deja_la_marca_del_build_a_medias(self):
        # Se escribió "14:2x" en un borrador: una plantilla sin rellenar
        # publicada es peor que no poner la hora.
        assert "14:2x" not in NOTAS.read_text(encoding="utf-8")


class TestElReadmeNoInflaLasCifras:
    """El README anunciaba "406 modelos repartidos en 15 plataformas".

    Esa cifra contaba los 97 checkpoints de imagen y 28 de video LOCALES de
    ComfyUI del autor: 125 modelos que solo existen en su ordenador. Quien
    instale ve 271 (164 imagen + 99 video + 8 audio) mas los suyos propios,
    que son distintos en cada equipo.
    """

    def _readme(self):
        return (RAIZ / "README.md").read_text(encoding="utf-8")

    def test_la_cifra_coincide_con_lo_seleccionable(self):
        import config
        def cuenta(flat):
            return len([m for m in flat if not m.startswith("──")])
        img = {m for p, l in config.MODELOS_POR_PLATAFORMA_IMAGEN.items()
               if "ComfyUI" not in p for m in l if not m.startswith("──")}
        vid = {m for p, l in config.MODELOS_POR_PLATAFORMA_VIDEO.items()
               if "ComfyUI" not in p for m in l if not m.startswith("──")}
        real = len(img) + len(vid) + cuenta(config.MODELOS_AUDIO_FLAT)
        anunciados = {int(n) for n in re.findall(r"\*\*(\d{3}) modelos", self._readme())}
        assert anunciados == {real}, (
            f"el README anuncia {anunciados} y son {real} seleccionables")

    def test_no_vuelve_la_cifra_con_los_locales_del_autor(self):
        assert "406 modelos" not in self._readme()

    def test_github_models_fuera_tambien_del_readme(self):
        # El servicio cerro el 30-jul-2026: anunciarlo es prometer un 410.
        assert "GitHub Models" not in self._readme()

    def test_se_instala_descargando_el_exe(self):
        # El README lideraba con git clone + pip, que es la via de
        # desarrollo. Quien llega a la portada quiere el instalador.
        txt = self._readme()
        i_exe = txt.find("GPromptStudio-Setup")
        i_clone = txt.find("git clone")
        assert i_exe != -1, "el README no dice como descargar el instalador"
        assert i_exe < i_clone, "el .exe tiene que ir ANTES que git clone"

    def test_cuenta_por_que_existe(self):
        assert "## Por qué existe" in self._readme()
