"""El Modo Brief: reglas de anuncio distintas para imagen, vídeo y audio.

Hasta el 24-sep-2026 las reglas eran solo de anuncio de VÍDEO (primer shot,
6-15 s, voz en off) y se pegaban igual a imagen y audio.
"""
from prompts import BRIEF_MODIFIER, BRIEF_MODIFIER_AUDIO, BRIEF_MODIFIER_IMAGEN, brief_para_modo


class TestUnBriefPorModo:

    def test_cada_modo_el_suyo(self):
        assert brief_para_modo("imagen") is BRIEF_MODIFIER_IMAGEN
        assert brief_para_modo("video") is BRIEF_MODIFIER
        assert brief_para_modo("audio") is BRIEF_MODIFIER_AUDIO

    def test_el_de_imagen_no_habla_de_video(self):
        texto = BRIEF_MODIFIER_IMAGEN.lower()
        # «en menos de un segundo de feed» sí vale: es lo que dura un vistazo.
        for cosa_de_video in ("shot", "primeros 2 segundos", "voz en off", "6-15"):
            assert cosa_de_video not in texto, cosa_de_video
        assert "hueco para el texto" in texto

    def test_el_de_audio_es_una_cuna(self):
        texto = BRIEF_MODIFIER_AUDIO.lower()
        assert "cuña" in texto and "shot" not in texto

    def test_cantada_o_para_locutar_lo_decide_la_idea(self):
        # Probado de verdad el 25-sep con Suno: las reglas pedían letra y
        # marca cantada Y «que funcione debajo de una voz en off»; el modelo
        # hizo una base instrumental, sin letra ni marca. Ahora las dos
        # salidas son válidas y cada una trae su forma de decir la marca.
        texto = BRIEF_MODIFIER_AUDIO
        assert "JINGLE CANTADO" in texto
        assert "Si la idea no lo dice: jingle cantado" in texto
        assert "sting" in texto
        assert "debajo de una voz en off" not in texto

    def test_los_tres_son_capa_adicional(self):
        for texto in (BRIEF_MODIFIER, BRIEF_MODIFIER_IMAGEN, BRIEF_MODIFIER_AUDIO):
            assert "CAPA ADICIONAL" in texto
