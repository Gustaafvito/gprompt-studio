"""«Montar dataset»: de las imágenes descargadas a 000.png + 000.txt.

Fase 3 del Generador de Dataset LoRA (09-oct-2026). G-Entrena lee cada
imagen con el .txt de su mismo nombre, y SeaArt admite subir un dataset ya
etiquetado igual. Las imágenes llegan con el nombre de cada sitio: las de
ComfyUI llevan el de la toma («05_bust_front_00001_.png»); las de SeaArt,
uno aleatorio.
"""
import json
import os

import pytest

from modules.avatar_montar import (
    emparejar,
    leer_dataset,
    montar_dataset,
    resumen_montaje,
)

TOMAS = ["01_face_front", "02_bust_front", "03_full_front"]


def _dataset(carpeta, sin_descripciones=False, plataforma="G-Entrena"):
    datos = {
        "trigger_word": "lyr4",
        "dataset": [{"filename": t, "label": t, "caption": f"lyr4, a woman, toma {t}"}
                    for t in TOMAS],
        "destino_entrenamiento": {"plataforma": plataforma, "base": "Anima"},
    }
    if sin_descripciones:
        datos["sin_descripciones"] = True
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "dataset.json").write_text(json.dumps(datos), encoding="utf-8")
    return carpeta


def _imagen(carpeta, nombre, mtime, contenido=b"img"):
    ruta = carpeta / nombre
    ruta.write_bytes(contenido)
    os.utime(ruta, (mtime, mtime))
    return str(ruta)


@pytest.fixture
def descargas(tmp_path):
    d = tmp_path / "descargas"
    d.mkdir()
    return d


class TestEmparejar:

    def test_por_nombre_las_de_comfyui(self, descargas):
        items = [{"filename": t} for t in TOMAS]
        imgs = [_imagen(descargas, f"{t}_00001_.png", 100 - i) for i, t in enumerate(TOMAS)]
        pares, sobran = emparejar(items, imgs)
        assert [os.path.basename(i) for _, i in pares] == [
            "01_face_front_00001_.png", "02_bust_front_00001_.png", "03_full_front_00001_.png"]
        assert sobran == []

    def test_por_orden_de_descarga_las_de_seaart(self, descargas):
        items = [{"filename": t} for t in TOMAS]
        # Nombres aleatorios: manda la fecha de descarga, no el nombre.
        c = _imagen(descargas, "aaa.png", 300)
        a = _imagen(descargas, "zzz.png", 100)
        b = _imagen(descargas, "mmm.webp", 200)
        pares, _ = emparejar(items, [c, a, b])
        assert [i for _, i in pares] == [a, b, c]

    def test_gana_la_version_del_detailer(self, descargas):
        items = [{"filename": "01_face_front"}]
        normal = _imagen(descargas, "01_face_front_00001_.png", 100)
        retocada = _imagen(descargas, "01_face_front_detailed_00001_.png", 101)
        pares, sobran = emparejar(items, [retocada, normal])
        assert pares[0][1] == retocada and sobran == [normal]

    def test_mezcla_nombre_y_orden(self, descargas):
        items = [{"filename": t} for t in TOMAS]
        por_nombre = _imagen(descargas, "02_bust_front_00001_.png", 50)
        x = _imagen(descargas, "x.png", 100)
        y = _imagen(descargas, "y.png", 200)
        pares, _ = emparejar(items, [y, por_nombre, x])
        assert [i for _, i in pares] == [x, por_nombre, y]

    def test_faltan_y_sobran(self, descargas):
        items = [{"filename": t} for t in TOMAS]
        pares, sobran = emparejar(items, [_imagen(descargas, "a.png", 1)])
        assert [i is None for _, i in pares] == [False, True, True]
        imgs = [_imagen(descargas, f"{n}.png", n) for n in range(5)]
        _, sobran = emparejar(items, imgs)
        assert len(sobran) == 2


class TestMontar:

    def test_000_png_con_su_txt(self, tmp_path, descargas):
        ds = _dataset(tmp_path / "ds")
        imgs = [_imagen(descargas, f"{t}_00001_.png", i) for i, t in enumerate(TOMAS)]
        r = montar_dataset(str(ds), imgs)
        nombres = sorted(os.listdir(r["carpeta"]))
        assert nombres == ["000.png", "000.txt", "001.png", "001.txt", "002.png", "002.txt"]
        txt = open(os.path.join(r["carpeta"], "001.txt"), encoding="utf-8").read()
        assert txt == "lyr4, a woman, toma 02_bust_front"
        assert r["por_nombre"] == 3 and r["por_orden"] == 0

    def test_conserva_la_extension(self, tmp_path, descargas):
        ds = _dataset(tmp_path / "ds")
        r = montar_dataset(str(ds), [_imagen(descargas, "a.webp", 1),
                                     _imagen(descargas, "b.jpg", 2)])
        assert {"000.webp", "001.jpg"} <= set(os.listdir(r["carpeta"]))
        assert r["sin_imagen"] == ["03_full_front"]

    def test_sin_descripciones_solo_imagenes(self, tmp_path, descargas):
        ds = _dataset(tmp_path / "ds", sin_descripciones=True, plataforma="Higgsfield")
        r = montar_dataset(str(ds), [_imagen(descargas, f"{n}.png", n) for n in range(3)])
        assert not any(n.endswith(".txt") for n in os.listdir(r["carpeta"]))

    def test_formatos_no_admitidos_se_quedan_fuera(self, tmp_path, descargas):
        ds = _dataset(tmp_path / "ds")
        avif = _imagen(descargas, "rara.avif", 1)
        r = montar_dataset(str(ds), [avif, _imagen(descargas, "ok.png", 2)])
        assert r["omitidas"] == [avif] and r["copiadas"] == 1

    def test_no_toca_lo_descargado(self, tmp_path, descargas):
        ds = _dataset(tmp_path / "ds")
        img = _imagen(descargas, "a.png", 1, b"original")
        montar_dataset(str(ds), [img])
        assert open(img, "rb").read() == b"original"

    def test_no_pisa_un_montaje_anterior(self, tmp_path, descargas):
        ds = _dataset(tmp_path / "ds")
        img = _imagen(descargas, "a.png", 1)
        primero = montar_dataset(str(ds), [img])["carpeta"]
        segundo = montar_dataset(str(ds), [img])["carpeta"]
        assert primero != segundo and segundo.endswith("dataset_listo_2")

    def test_sin_dataset_json(self, tmp_path):
        with pytest.raises(ValueError):
            leer_dataset(str(tmp_path))


class TestResumen:

    def test_cuenta_lo_que_paso_y_el_siguiente_paso(self, tmp_path, descargas):
        ds = _dataset(tmp_path / "ds")
        imgs = [_imagen(descargas, "01_face_front_00001_.png", 1),
                _imagen(descargas, "x.png", 2)]
        texto = resumen_montaje(montar_dataset(str(ds), imgs))
        assert "2 imágenes listas" in texto
        assert "por nombre" in texto and "orden de descarga" in texto
        assert "Sin imagen (1)" in texto
        assert "G-Entrena" in texto
