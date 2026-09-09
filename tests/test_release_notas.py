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


def _vigentes(fichero):
    d = json.loads((RAIZ / "data" / fichero).read_text(encoding="utf-8"))
    return sum(1 for v in d.values() if isinstance(v, dict) and v.get("vigente"))


class TestLasCifrasCuadranConElCatalogo:

    def test_el_total_es_el_de_las_fichas_vigentes(self):
        real = (_vigentes("model_specs_imagen.json")
                + _vigentes("model_specs_video.json")
                + _vigentes("model_specs_audio.json"))
        texto = NOTAS.read_text(encoding="utf-8")
        anunciados = {int(n) for n in re.findall(r"\*\*(\d{3}) modelos", texto)}
        assert anunciados, "el texto del release ya no anuncia ninguna cifra"
        assert anunciados == {real}, (
            f"el release anuncia {anunciados} y hay {real} fichas vigentes")

    def test_el_desglose_por_modo_tambien(self):
        texto = NOTAS.read_text(encoding="usa-ascii" if False else "utf-8")
        m = re.search(r"(\d+) de imagen, (\d+) de vídeo, (\d+) de\s*\n?\s*audio",
                      texto)
        assert m, "no encuentro el desglose por modo en el release"
        img, vid, aud = (int(x) for x in m.groups())
        assert img == _vigentes("model_specs_imagen.json")
        assert vid == _vigentes("model_specs_video.json")
        assert aud == _vigentes("model_specs_audio.json")

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
