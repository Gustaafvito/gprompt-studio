"""Dónde se entrena el LoRA y cómo se describe cada imagen del dataset.

09-oct-2026: el Generador de Dataset LoRA escribía siempre las descripciones
(.txt) igual —«trigger, encuadre, fondo, luz»—, sin palabra de clase y sin
mirar dónde se iba a entrenar. Cada plataforma las quiere a su manera: SeaArt
pide tags para SD 1.5 / Pony / Illustrious y frases para Flux, SDXL, Z-Image,
Qwen o Anima; Higgsfield y Magnific no las usan. El catálogo de destinos sale
del código de G-Entrena, de una grabación del entrenador de SeaArt y de las
guías públicas de cada plataforma.
"""
import json
import os

import pytest

from modules import i18n
from modules.avatar_config import LORA_TYPES
from modules.avatar_destinos import (
    ESTILOS_DESCRIPCION,
    aplicar_destino,
    cargar_destinos,
    clase_para,
    destino_por_defecto,
    destinos_para_tipo,
    rango_imagenes,
    redactar_descripcion,
)

DESTINOS = cargar_destinos()
POR_ID = {d["id"]: d for d in DESTINOS}


class TestElCatalogo:

    def test_ids_unicos(self):
        assert len(POR_ID) == len(DESTINOS)

    def test_campos_validos(self):
        for d in DESTINOS:
            assert d["descripciones"] in ESTILOS_DESCRIPCION, d["id"]
            assert d["tipos"] and set(d["tipos"]) <= set(LORA_TYPES), d["id"]
            minimo, maximo = d["imagenes"]
            assert 0 < minimo <= maximo, d["id"]

    def test_cada_tipo_tiene_destinos(self):
        for tipo in LORA_TYPES:
            assert destinos_para_tipo(tipo, DESTINOS), tipo

    def test_estan_las_bases_de_g_entrena(self):
        # Las seis que entrena G-Entrena. LTX y MiniMax H3 son modelos de
        # vídeo, pero sus LoRA se entrenan con imágenes (H3 admite también
        # vídeos): un dataset de esta ventana les sirve.
        g = {d["base"] for d in DESTINOS if d["plataforma"] == "G-Entrena"}
        assert {"Anima", "Krea 2", "Qwen Image 2.1", "Z-Image",
                "LTX 2.3", "MiniMax H3"} <= g

    def test_los_de_g_entrena_van_juntos(self):
        # En el desplegable salen seguidos, no mezclados con SeaArt.
        plataformas = [d["plataforma"] for d in DESTINOS]
        primero = plataformas.index("G-Entrena")
        n = plataformas.count("G-Entrena")
        assert plataformas[primero:primero + n] == ["G-Entrena"] * n

    def test_higgsfield_y_magnific_no_usan_descripciones(self):
        for d in DESTINOS:
            if d["plataforma"] in ("Higgsfield", "Magnific"):
                assert d["descripciones"] == "ninguna", d["id"]
                assert "NSFW" not in d["tipos"], d["id"]

    def test_textos_traducidos(self):
        # El desplegable y su tooltip los muestran con tr(): sin entrada EN,
        # la UI inglesa los enseñaría en español.
        faltan = {d["nota"] for d in DESTINOS if d.get("nota")}
        faltan |= {"Personaje propio", "Estilo propio"}
        faltan -= set(i18n.TRADUCCIONES)
        assert not faltan, sorted(faltan)[:3]


class TestElDestinoQueSePropone:

    def test_anima_de_seaart(self):
        d = destino_por_defecto("Anima", "SeaArt / Tensor.Art", "Personaje", DESTINOS)
        assert d["id"] == "seaart-anima"

    def test_anima_local_se_entrena_en_g_entrena(self):
        d = destino_por_defecto("anima-base-v1.0", "ComfyUI / Fooocus",
                                "Personaje", DESTINOS)
        assert d["id"] == "g-entrena-anima"

    def test_illustrious(self):
        d = destino_por_defecto("Illustrious XL V3.6", "SeaArt / Tensor.Art",
                                "Personaje", DESTINOS)
        assert d["id"] == "seaart-illustrious"

    def test_sin_coincidencia_el_primero_del_tipo(self):
        d = destino_por_defecto("GPT Image 2", "ChatGPT / GPT Image", "Paisaje", DESTINOS)
        assert d == destinos_para_tipo("Paisaje", DESTINOS)[0]

    def test_higgsfield_solo_para_personaje(self):
        assert "higgsfield-soul-id" in {d["id"] for d in destinos_para_tipo("Personaje", DESTINOS)}
        assert "higgsfield-soul-id" not in {d["id"] for d in destinos_para_tipo("NSFW", DESTINOS)}

    def test_rango_por_tipo(self):
        assert rango_imagenes(POR_ID["seaart-anima"], "Personaje") == [25, 40]
        assert rango_imagenes(POR_ID["seaart-anima"], "Paisaje") == [20, 40]


PARTES = {"encuadre": "close-up portrait, three-quarter left",
          "fondo": "plain light gray studio background",
          "luz": "soft even studio lighting"}


class TestLaDescripcion:

    def test_etiquetas(self):
        out = redactar_descripcion(PARTES, "etiquetas", "Personaje", "lyr4",
                                   ("1girl, solo", "a woman"))
        assert out == ("lyr4, 1girl, solo, close-up portrait, three-quarter left, "
                       "plain light gray studio background, soft even studio lighting")

    def test_frases_como_las_de_lyra(self):
        out = redactar_descripcion(PARTES, "frases", "Personaje", "lyr4",
                                   ("1girl, solo", "a woman"))
        assert out.startswith("lyr4, a woman, close-up portrait")

    def test_natural_como_pide_seaart(self):
        out = redactar_descripcion(PARTES, "natural", "Personaje", "lyr4",
                                   ("1girl, solo", "a woman"), "A photo of")
        assert out.startswith("A photo of a woman named lyr4, close-up portrait")
        assert out.endswith(".")

    def test_estilo_no_lleva_clase_y_nombra_el_estilo(self):
        out = redactar_descripcion({"encuadre": "urban scene"}, "natural",
                                   "Estilo", "brsh", None)
        assert out == "Urban scene, in the brsh style."

    def test_ninguna(self):
        assert redactar_descripcion(PARTES, "ninguna", "Personaje", "x", None) == ""

    def test_clase_segun_la_ficha(self):
        assert clase_para("Personaje", {"genero": "Hombre"})[1] == "a man"
        # La ficha guarda lo que MUESTRA el combo: en inglés, «Woman».
        i18n.set_idioma("en")
        try:
            assert clase_para("NSFW", {"genero": i18n.tr("Mujer")})[1] == "a woman"
        finally:
            i18n.set_idioma("es")
        assert clase_para("Objeto", {"categoria": "Herramienta"})[1] == "a tool"
        assert clase_para("Estilo", {}) is None


def _resultado(n=3):
    item = {"filename": "01_x", "label": "x", "prompt": "p", "negative": "",
            "caption": "vieja", "partes_descripcion": dict(PARTES)}
    return {"trigger_word": "lyr4",
            "dataset": [dict(item, filename=f"{i:02d}_x") for i in range(n)]}


class TestAplicarDestino:

    def test_reescribe_las_descripciones(self):
        r = _resultado()
        aplicar_destino(r, POR_ID["seaart-illustrious"], "Personaje",
                        {"genero": "Mujer"}, "Anime")
        assert all(it["caption"].startswith("lyr4, 1girl, solo,") for it in r["dataset"])
        assert r["destino_entrenamiento"]["id"] == "seaart-illustrious"

    def test_avisa_si_faltan_imagenes(self):
        avisos = aplicar_destino(_resultado(3), POR_ID["seaart-anima"], "Personaje", {}, "")
        assert any("25" in a and "40" in a for a in avisos)

    def test_en_rango_no_avisa(self):
        avisos = aplicar_destino(_resultado(30), POR_ID["seaart-anima"], "Personaje", {}, "")
        assert avisos == []

    def test_sin_descripciones(self):
        r = _resultado(20)
        avisos = aplicar_destino(r, POR_ID["higgsfield-soul-id"], "Personaje", {}, "")
        assert r["sin_descripciones"] is True
        assert all(it["caption"] == "" for it in r["dataset"])
        assert avisos  # dice que se suben solo las imágenes

    def test_sin_destino_no_toca_nada(self):
        r = _resultado()
        assert aplicar_destino(r, None, "Personaje", {}, "") == []
        assert r["dataset"][0]["caption"] == "vieja"


class TestElEnsambladoDejaLasPiezas:

    @pytest.mark.parametrize("tipo", list(LORA_TYPES))
    def test_cada_imagen_lleva_sus_partes(self, tipo):
        from modules.avatar_generator import generar_dataset_lora
        cfg = LORA_TYPES[tipo]
        r = generar_dataset_lora(
            tipo=tipo, llm_call=lambda s, u: "a test subject",
            form_data={}, trigger_word="tw",
            angulos_seleccionados=list(cfg["angles"])[:3],
            estilo_sufijo="", fondo=None)
        for it in r["dataset"]:
            assert set(it["partes_descripcion"]) == {
                "encuadre", "expresion", "ropa", "fondo", "luz"}
            assert it["partes_descripcion"]["encuadre"]


class TestLaExportacion:

    def test_sin_descripciones_no_hay_carpeta_captions(self, tmp_path):
        from modules.avatar_generator import exportar_dataset
        r = _resultado(20)
        aplicar_destino(r, POR_ID["magnific-personaje"], "Personaje", {}, "")
        base = exportar_dataset(r, str(tmp_path))
        assert not os.path.isdir(os.path.join(base, "captions"))
        consejos = open(os.path.join(base, "CONSEJOS_SEAART.txt"), encoding="utf-8").read()
        assert consejos.startswith("DESTINO DE ENTRENAMIENTO: Magnific")

    def test_con_descripciones_las_escribe(self, tmp_path):
        from modules.avatar_generator import exportar_dataset
        r = _resultado(3)
        aplicar_destino(r, POR_ID["g-entrena-anima"], "Personaje", {"genero": "Mujer"}, "Anime")
        base = exportar_dataset(r, str(tmp_path))
        txt = open(os.path.join(base, "captions", "00_x.txt"), encoding="utf-8").read()
        assert txt.startswith("lyr4, a woman,")
        datos = json.load(open(os.path.join(base, "dataset.json"), encoding="utf-8"))
        assert datos["destino_entrenamiento"]["base"] == "Anima"
