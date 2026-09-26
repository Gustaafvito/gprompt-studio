"""MiniMax H3 y MiniMax Music 3 en ComfyUI (26-sep-2026).

El usuario pasó la guía oficial de prompts de H3
(huggingface.co/MiniMaxAI/MiniMax-H3/docs). La app trataba H3 como un vídeo
más: «prosa + línea Audio: + NEGATIVE», sin audio y con 5-6 s. H3 genera
vídeo CON audio, de 4 a 15 s, no usa negative (pesos CFG-distilled) y se
entrenó con prompts en un formato fijo de campos y planos. Además,
minimax_music3 (un modelo de MÚSICA) caía en vídeo por el token «minimax».
"""
import re
from types import SimpleNamespace

import config
from modules.core import system_audio_para
from modules.prompts_inyeccion import PromptsInyeccionService
from prompts import (
    SYSTEM_AUDIO_MINIMAX_MUSIC3,
    SYSTEM_AUDIO_SEAART,
    SYSTEM_AUDIO_SEAART_TAGS,
    SYSTEM_AUDIO_SUNO,
)

BASE = "minimax_h3_fl2va_pruned_int8_convrot"
REF = "minimax_h3_ref2va_pruned_int8_convrot"
MUSIC3 = "minimax_music3_dit_fp16"


def _var(v):
    return SimpleNamespace(get=lambda: v)


def _system(modelo, duracion="10s", imagen=None, shots="Auto"):
    app = SimpleNamespace(modo_var=_var("video"), combo_modelo_video=_var(modelo),
                          duracion_var=_var(duracion), shots_var=_var(shots),
                          imagen_cargada=imagen, estilo_video_var=_var("Auto"))
    return PromptsInyeccionService(app)._inyectar_specs_video("SYS")


class TestClasificacion:

    def test_music3_es_audio_y_no_video(self):
        assert config.clasificar_modelo_comfy(MUSIC3) == "audio"
        specs = config.get_audio_model_specs(MUSIC3)
        assert specs["formato"] == "minimax_music3"
        assert specs["usa_tags_estructurales"] is True

    def test_los_dos_h3_siguen_en_video(self):
        for n in (BASE, REF):
            assert config.clasificar_modelo_comfy(n) == "video"
            assert config.detectar_familia_comfy_video(n) == "minimax"

    def test_ficha_base_con_audio_sin_negative_y_4_a_15_s(self):
        s = config.get_model_specs(BASE)
        assert s["has_audio"] is True
        assert s["has_negative"] is False
        assert s["duraciones"][0] == "4s" and s["duraciones"][-1] == "15s"
        assert s["formato_bloques"] == "minimax_h3"
        assert s["sin_recorte"] is True

    def test_ref2va_usa_el_formato_de_referencia(self):
        s = config.get_model_specs(REF)
        assert s["formato_bloques"] == "minimax_h3_ref"
        assert s["max_imagenes"] == 9
        # y no contamina la ficha base (dict compartido de la familia)
        assert config.get_model_specs(BASE)["formato_bloques"] == "minimax_h3"


class TestFormatoBase:

    def test_campos_literales_y_sin_plantilla_generica(self):
        out = _system(BASE)
        for campo in ("integrated_multimodal_description:", "overall_soundscape:",
                      "non_diegetic_music:"):
            assert campo in out
        # Las reglas genéricas de vídeo no deben colarse: pedían línea
        # «Audio:» y NEGATIVE, que H3 no usa.
        assert "AÑADE línea 'Audio:'" not in out
        assert "Genera POSITIVE y NEGATIVE" not in out

    def test_instrucciones_de_fotograma_con_la_duracion_real(self):
        out = _system(BASE, duracion="6s")
        assert ("For the target video, at 0.00 seconds into the target video, "
                "<Picture 1> (from [Shot 1]) is fully referenced.") in out
        assert "aligns with the 6.00-second mark of the target video" in out
        assert "10.00-second" not in out

    def test_sin_huecos_de_plantilla(self):
        for out in (_system(BASE), _system(REF)):
            assert not re.search(r"\{[a-z_]+\}", out), "quedó un {hueco} sin rellenar"

    def test_con_imagen_cargada_por_defecto_i2va(self):
        assert "HA CARGADO una imagen" in _system(BASE, imagen="x.png")
        assert "NO ha cargado imagen" in _system(BASE)

    def test_el_nombre_del_fichero_no_decide_el_modo(self):
        # Visto en real: sin imagen, la IA ponía la línea de FL2VA porque el
        # fichero se llama «…fl2va…».
        assert "NO decide el modo" in _system(BASE)

    def test_fl2va_en_un_solo_plano(self):
        assert "FL2VA va en UN SOLO plano" in _system(BASE)

    def test_planos_fijados_por_el_usuario_son_exactos(self):
        assert "EXACTAMENTE 2 planos" in _system(BASE, shots="2")


class TestFormatoReferencia:

    def test_seis_secciones_y_etiquetas(self):
        out = _system(REF, duracion="8s")
        for sec in ("subject_definitions:", "summary:", "retention_analysis:",
                    "detailed_description:", "overall_soundscape:", "non_diegetic_music:"):
            assert sec in out
        for etiqueta in ("<Subject N>", "<Picture N>", "<Video N>", "<Audio N>",
                         "fully_preserved", "fully_copy", "[reference generation]"):
            assert etiqueta in out


class TestAudio:

    def test_cada_motor_recibe_su_system(self):
        assert system_audio_para("Suno v5") is SYSTEM_AUDIO_SUNO
        assert system_audio_para(MUSIC3) is SYSTEM_AUDIO_MINIMAX_MUSIC3
        assert system_audio_para("SeaArt MusicGo") is SYSTEM_AUDIO_SEAART
        for motor in ("Minimax Music 2.6", "Minimax Music 2.5", "Mureka V9"):
            assert system_audio_para(motor) is SYSTEM_AUDIO_SEAART_TAGS, motor

    def test_la_variante_con_tags_no_prohibe_los_tags(self):
        # Minimax Music y Mureka recibían «NO uses [Verse]» y, en su ficha,
        # «USA tags estructurales obligatorios».
        assert "NO usa tags estructurales" not in SYSTEM_AUDIO_SEAART_TAGS
        assert "NO uses [Verse]" not in SYSTEM_AUDIO_SEAART_TAGS
        assert "sin tags [Verse]" not in SYSTEM_AUDIO_SEAART_TAGS
        assert "[Verse]\nPrimera estrofa" in SYSTEM_AUDIO_SEAART_TAGS
        # MusicGo sigue sin tags
        assert "NO usa tags estructurales" in SYSTEM_AUDIO_SEAART

    def test_music3_pide_los_tres_apartados_oficiales(self):
        for ap in ("Global Metadata:", "Vocal Details:", "Arrangement:"):
            assert ap in SYSTEM_AUDIO_MINIMAX_MUSIC3
        # «ESTILO:» es el bloque que reconocen refinar y el resto de la app.
        assert "\nESTILO:\n" in SYSTEM_AUDIO_MINIMAX_MUSIC3
