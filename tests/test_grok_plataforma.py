"""Grok (xAI) como plataforma propia, en imagen Y en vídeo.

08-sep-2026. En imagen ya existía la plataforma propia "Grok (xAI)", con una
única entrada genérica; en vídeo no existía, y sus dos motores solo se podían
elegir entrando por SeaArt Video.

La trampa: `Grok Imagine Video` y `Grok Imagine Video 1.5` YA estaban
catalogados, pero son la ruta de SEAART y describen OTRO producto. Colgarlos
de la plataforma directa parecía lo obvio y era un error — lo cazó
test_la_ruta_directa_no_usa_negative:

    vía SeaArt       la 1.5 es SOLO imagen-a-vídeo · tope 720p · SÍ tiene
                     campo de negativo, porque lo pone SeaArt
    directo x.ai     multi-modo (texto Y imagen) · llega a 1080p · sin
                     negativo

Así que la ruta directa lleva fichas APARTE, con sufijo "(xAI)", y las de
SeaArt se quedan intactas porque describen bien lo que SeaArt ofrece.

Es un alta SOLO DE MAPEO, como Pollo AI y Higgsfield: la app escribe el
prompt adaptado y el usuario lo pega en Grok. No consume API. Que además haya
key de x.ai como CEREBRO (el LLM que redacta) es independiente — son los dos
conceptos que se confunden.

Precios de la consola, por segundo: 1.5 en 480p $0,08 · 720p $0,14 · 1080p
$0,25; la anterior 480p $0,05 · 720p $0,07 y acepta vídeo de entrada para
editar.
"""
import config


class TestLaPlataformaExisteEnLosDosModos:

    def test_grok_esta_en_video(self):
        assert "Grok (xAI)" in config.PLATAFORMAS_VIDEO
        assert "Grok (xAI)" in config.MOTORES_VIDEO
        assert "Grok (xAI)" in config.MODELOS_POR_PLATAFORMA_VIDEO

    def test_grok_sigue_en_imagen(self):
        assert "Grok (xAI)" in config.PLATAFORMAS_IMAGEN
        assert "Grok (xAI)" in config.MODELOS_POR_PLATAFORMA_IMAGEN

    def test_es_de_lenguaje_natural(self):
        # Ni negative ni pesos numéricos: si se marcara "sd", la app le
        # inyectaría tags y prompt negativo que Grok ignora.
        assert config.PLATAFORMAS_VIDEO["Grok (xAI)"] == "natural"

    def test_los_dos_motores_de_video(self):
        motores = config.MOTORES_VIDEO["Grok (xAI)"]
        assert motores == ["Grok Imagine Video 1.5 (xAI)",
                           "Grok Imagine Video (xAI)"]

    def test_no_reutiliza_las_fichas_de_seaart(self):
        # Las entradas sin "(xAI)" describen la ruta de SeaArt, que es OTRO
        # producto: solo imagen-a-video, tope 720p y con campo de negativo
        # (el de SeaArt). Colgarlas de la plataforma directa haria que la app
        # inyecte un negativo que x.ai ignora y esconda el 1080p.
        for m in config.MOTORES_VIDEO["Grok (xAI)"]:
            assert m.endswith("(xAI)")

    def test_las_dos_listas_de_video_coinciden(self):
        # MOTORES_VIDEO alimenta el combo y MODELOS_POR_PLATAFORMA_VIDEO la
        # validación: si se separan, un modelo elegible deja de validar.
        assert (config.MOTORES_VIDEO["Grok (xAI)"]
                == config.MODELOS_POR_PLATAFORMA_VIDEO["Grok (xAI)"])


class TestTodoModeloDeGrokTieneFicha:

    def test_los_de_video(self):
        for m in config.MOTORES_VIDEO["Grok (xAI)"]:
            assert config.get_model_specs(m), f"{m} sin ficha"
            assert config.es_modelo_video_vigente(m), f"{m} no se vería"

    def test_los_de_imagen(self):
        for m in config.MODELOS_GROK_IMAGEN_FLAT:
            if m.startswith("──"):
                continue
            assert config.get_image_model_specs(m), f"{m} sin ficha"
            assert config.es_modelo_imagen_vigente(m), f"{m} no se vería"

    def test_la_ruta_directa_no_usa_negative(self):
        # x.ai no expone campo de negativo en sus modelos de imagen ni de
        # video. Marcarlo haria que la app redacte un negativo inutil.
        for m in config.MOTORES_VIDEO["Grok (xAI)"]:
            assert not config.get_model_specs(m).get("has_negative")
        for m in config.MODELOS_GROK_IMAGEN_FLAT:
            if not m.startswith("──"):
                assert not config.get_image_model_specs(m).get("has_negative")


class TestLosModosDeVideoSonLosReales:

    def test_la_1_5_llega_a_1080p(self):
        modos = config.get_model_specs("Grok Imagine Video 1.5 (xAI)")["modos_gen"]
        assert "1080p" in modos, (
            "la consola de x.ai factura 1080p a $0,25/s: ofrecer solo hasta "
            "720p esconde la mejor calidad que el usuario ya paga")

    def test_la_version_vieja_no_llega_a_1080p(self):
        modos = config.get_model_specs("Grok Imagine Video (xAI)")["modos_gen"]
        assert "1080p" not in modos, "solo 480p y 720p en la consola"

    def test_la_de_seaart_se_queda_como_estaba(self):
        # No se toca: su ficha describe correctamente lo que ofrece SeaArt.
        s = config.get_model_specs("Grok Imagine Video 1.5")
        assert s["modos_gen"] == ["480p", "720p"]
        assert s["has_negative"] is True, "el campo de negativo lo pone SeaArt"

    def test_las_fichas_dicen_que_estan_por_confirmar(self):
        # Alta por mapeo: mientras no se genere de verdad, la ficha tiene que
        # decirlo en vez de aparentar datos medidos.
        for m in config.MOTORES_VIDEO["Grok (xAI)"]:
            assert "POR CONFIRMAR" in config.get_model_specs(m)["limitaciones"]


class TestLosDosModelosNuevosDeImagen:

    NUEVOS = ("Grok Imagine Image 2.0", "Grok Imagine Image Quality")

    def test_estan_en_la_plataforma_directa(self):
        for m in self.NUEVOS:
            assert m in config.MODELOS_GROK_IMAGEN_FLAT

    def test_la_2_0_acepta_prompts_mas_largos(self):
        # 64K de contexto y pensada para infografías, mockups y storyboards:
        # el layout hay que describirlo, y eso ocupa.
        assert (config.get_image_model_specs("Grok Imagine Image 2.0")["max_chars"]
                > config.get_image_model_specs("Grok Imagine Image Quality")["max_chars"])

    def test_ambas_ofrecen_1K_y_2K(self):
        for m in self.NUEVOS:
            assert config.get_image_model_specs(m)["modos_gen"] == ["1K", "2K"]

    def test_las_fichas_dicen_que_estan_por_confirmar(self):
        for m in self.NUEVOS:
            assert "POR CONFIRMAR" in config.get_image_model_specs(m)["limitaciones"]
