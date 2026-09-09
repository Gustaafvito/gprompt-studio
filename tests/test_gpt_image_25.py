"""GPT Image 2.5: dos variantes, mismo precio, distinto compromiso.

OpenAI anunció Images 2.5 el 08-sep-2026 y SeaArt lo publicó el mismo día.
Se dan de alta las dos variantes de la API —`gpt-image-2.5-flare` y
`gpt-image-2.5-sunburst`— en los DOS grupos, el de SeaArt y el de la ruta
oficial de ChatGPT, porque a diferencia del vídeo de Grok aquí es el mismo
modelo: solo cambia quién factura.

**El dato que importa para elegir:** las dos cuestan EXACTAMENTE lo mismo
($5/1M de texto de entrada, $8/1M de imagen de entrada, $30/1M de imagen de
salida) y es el mismo precio que la generación anterior. Así que la decisión
es tiempo contra precisión, NO dinero — Flare para iterar, Sunburst para el
asset final. Si alguna vez se documenta que Sunburst cuesta más, hay que
reescribir las fichas, porque el consejo cambiaría.

Lo que OpenAI NO publica (ratios exactos, tope real de prompt, número de
imágenes de referencia) se hereda de GPT Image 2 y queda marcado POR
CONFIRMAR, en vez de inventar cifras.
"""
import config

VARIANTES = ("GPT Image 2.5 Flare", "GPT Image 2.5 Sunburst")


class TestLasDosVariantesExisten:

    def test_tienen_ficha_y_se_ven(self):
        for m in VARIANTES:
            assert config.get_image_model_specs(m), f"{m} sin ficha"
            assert config.es_modelo_imagen_vigente(m), f"{m} no se vería"

    def test_estan_en_la_ruta_oficial_de_chatgpt(self):
        for m in VARIANTES:
            assert m in config.MODELOS_DALLE_IMAGEN_FLAT

    def test_estan_tambien_en_seaart(self):
        # Mismo modelo por las dos vías: solo cambia quién factura.
        for m in VARIANTES:
            assert m in config.MODELOS_IMAGEN_FLAT


class TestHeredanLaFamiliaGptImage:

    def test_ni_negative_ni_pesos(self):
        for m in VARIANTES:
            assert not config.get_image_model_specs(m)["has_negative"]
            assert config.get_image_model_specs(m)["is_natural"]

    def test_mantienen_el_formato_de_seis_bloques(self):
        # La fórmula de prompt de GPT Image es lo que hace que el texto
        # dentro de la imagen salga legible: perderla degradaría el
        # resultado sin que nadie lo note.
        for m in VARIANTES:
            assert config.get_image_model_specs(m)["formato_bloques"] == "gpt_image"

    def test_tienen_mas_niveles_de_calidad_que_la_2(self):
        # La API documenta low/medium/high/xhigh/max/auto: tres más.
        n2 = len(config.get_image_model_specs("GPT Image 2")["modos_gen"])
        for m in VARIANTES:
            assert len(config.get_image_model_specs(m)["modos_gen"]) > n2


class TestElConsejoDeCuandoUsarCadaUna:

    def test_flare_se_describe_como_la_rapida(self):
        s = config.get_image_model_specs("GPT Image 2.5 Flare")
        assert "RAPIDA" in s["limitaciones"]
        assert "iterar" in s["best_for"].lower()

    def test_sunburst_se_describe_como_la_de_calidad(self):
        s = config.get_image_model_specs("GPT Image 2.5 Sunburst")
        assert "CALIDAD" in s["limitaciones"]
        assert "final" in s["best_for"].lower()

    def test_las_fichas_avisan_de_que_el_precio_es_el_MISMO(self):
        # Sin esto, alguien asume que Sunburst es "la cara" y se queda en
        # Flare para ahorrar un dinero que no existe.
        for m in VARIANTES:
            lim = config.get_image_model_specs(m)["limitaciones"]
            assert "identico" in lim or "idéntico" in lim, (
                f"{m}: la ficha no dice que las dos cuestan lo mismo")

    def test_sunburst_puntua_mas_alto_que_flare(self):
        f = config.get_image_model_specs("GPT Image 2.5 Flare")["nota"]
        s = config.get_image_model_specs("GPT Image 2.5 Sunburst")["nota"]
        assert s > f > config.get_image_model_specs("GPT Image 2")["nota"]

    def test_lo_no_publicado_queda_marcado(self):
        for m in VARIANTES:
            assert "POR CONFIRMAR" in config.get_image_model_specs(m)["limitaciones"]
