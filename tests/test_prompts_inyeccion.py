"""Tests para PromptsInyeccionService (modules/prompts_inyeccion.py).

A1 fase 2 (sesión 9): el mixin fue convertido a clase con app por
composición. Los tests ahora crean un fake_app con SimpleNamespace y
pasan al constructor del service.

Funciones puras sobre strings: dado un system_prompt base, devuelve uno
enriquecido con reglas del modelo activo y del destino.
"""
from types import SimpleNamespace

import pytest

from modules.prompts_inyeccion import PromptsInyeccionService


def _var(value):
    """Imita un tk.StringVar / BooleanVar (solo .get())."""
    return SimpleNamespace(get=lambda: value)


def _host(**attrs):
    """Construye un PromptsInyeccionService con app simulado.

    Mantiene la misma API que el helper antiguo: setattr en `app` con
    los atributos pasados. Compatible con todos los tests existentes
    (que esperan h.modo_var, h.combo_modelo_imagen, etc.).
    """
    app = SimpleNamespace()
    for k, v in attrs.items():
        setattr(app, k, v)
    return PromptsInyeccionService(app)


class TestInyectarDestino:

    def test_destino_vacio_no_cambia(self):
        h = _host(destino_var=_var(""))
        assert h._inyectar_destino("base") == "base"

    def test_destino_personal_no_cambia(self):
        h = _host(destino_var=_var("— Personal —"))
        assert h._inyectar_destino("base") == "base"

    def test_destino_instagram_añade_regla(self):
        h = _host(destino_var=_var("Instagram"))
        out = h._inyectar_destino("base")
        assert out.startswith("base\n\n📢 ")
        assert "INSTAGRAM" in out

    def test_destino_anthum_concurso_añade_regla_extensa(self):
        h = _host(destino_var=_var("Anthum (concurso)"))
        out = h._inyectar_destino("X")
        assert "ANTHUM" in out
        assert "ORIGINALIDAD" in out

    def test_destino_desconocido_no_cambia(self):
        h = _host(destino_var=_var("PlataformaInexistente"))
        assert h._inyectar_destino("base") == "base"

    def test_sin_atributo_destino_var_no_cambia(self):
        # Si destino_var no existe, hasattr() lo evita y devuelve base
        h = _host()
        assert h._inyectar_destino("base") == "base"


class TestInyectarSpecsModelo:

    def test_modo_audio_no_toca(self):
        # El dispatcher principal solo enruta video/imagen
        h = _host(modo_var=_var("audio"))
        assert h._inyectar_specs_modelo("base") == "base"

    def test_modo_video_invoca_video(self, monkeypatch):
        monkeypatch.setattr(
            "modules.prompts_inyeccion.get_model_specs",
            lambda m: None,  # sin specs → devuelve base sin tocar
        )
        h = _host(modo_var=_var("video"),
                  combo_modelo_video=_var("CualquierMotor"))
        assert h._inyectar_specs_modelo("base") == "base"

    def test_modo_imagen_invoca_imagen(self, monkeypatch):
        monkeypatch.setattr(
            "modules.prompts_inyeccion.es_separador",
            lambda m: False,
        )
        monkeypatch.setattr(
            "modules.prompts_inyeccion.get_image_model_specs",
            lambda m: None,
        )
        h = _host(modo_var=_var("imagen"),
                  combo_modelo_imagen=_var("CualquierModelo"))
        assert h._inyectar_specs_modelo("base") == "base"


class TestInyectarSpecsVideo:

    SPECS_GRANDE = {
        "max_chars": 5000,
        "prompt_formula": "subject + action + style",
        "prompt_ejemplo": "A cat jumps",
        "best_for": "cinematic shots",
        "has_audio": True,
        "audio_desc": "stereo 48kHz",
        "has_negative": True,
        "limitaciones": "máx 10s",
    }

    SPECS_PEQUENO = {
        "max_chars": 500,
        "prompt_formula": "subject",
        "prompt_ejemplo": "cat",
        "best_for": "quick clips",
        "has_audio": False,
        "audio_desc": "",
        "has_negative": False,
    }

    def _make(self, monkeypatch, specs):
        monkeypatch.setattr(
            "modules.prompts_inyeccion.get_model_specs",
            lambda m: specs,
        )
        monkeypatch.setattr(
            "modules.prompts_inyeccion.get_prompt_template",
            lambda m: None,
        )
        return _host(combo_modelo_video=_var("VeoX"))

    def test_sin_specs_devuelve_base(self, monkeypatch):
        monkeypatch.setattr(
            "modules.prompts_inyeccion.get_model_specs",
            lambda m: None,
        )
        h = _host(combo_modelo_video=_var("Desconocido"))
        assert h._inyectar_specs_video("base") == "base"

    def test_max_chars_grande_usa_objetivo_extenso(self, monkeypatch):
        h = self._make(monkeypatch, self.SPECS_GRANDE)
        out = h._inyectar_specs_video("base")
        assert "400-700" in out
        assert "EXTREMADAMENTE DETALLADO" in out

    def test_max_chars_pequeno_usa_objetivo_conciso(self, monkeypatch):
        h = self._make(monkeypatch, self.SPECS_PEQUENO)
        out = h._inyectar_specs_video("base")
        assert "130-210" in out
        assert "DETALLADO Y CONCISO" in out

    def test_has_audio_menciona_soporte(self, monkeypatch):
        h = self._make(monkeypatch, self.SPECS_GRANDE)
        out = h._inyectar_specs_video("base")
        assert "SOPORTA audio" in out
        assert "stereo 48kHz" in out

    def test_no_has_audio_lo_prohibe(self, monkeypatch):
        h = self._make(monkeypatch, self.SPECS_PEQUENO)
        out = h._inyectar_specs_video("base")
        assert "NO tiene audio" in out

    def test_motor_nombre_en_mayusculas(self, monkeypatch):
        h = self._make(monkeypatch, self.SPECS_GRANDE)
        out = h._inyectar_specs_video("base")
        assert "VEOX" in out


class TestInyectarTemplate:

    def test_sin_template_no_añade_nada(self, monkeypatch):
        monkeypatch.setattr(
            "modules.prompts_inyeccion.get_prompt_template",
            lambda m: None,
        )
        h = _host()
        assert h._inyectar_template("motor", "X") == "X"

    def test_con_template_añade_positive_y_negative(self, monkeypatch):
        monkeypatch.setattr(
            "modules.prompts_inyeccion.get_prompt_template",
            lambda m: {"positive_base": "POS_BASE", "negative_base": "NEG_BASE"},
        )
        h = _host()
        out = h._inyectar_template("motor", "X")
        assert "POS_BASE" in out
        assert "NEG_BASE" in out
        assert "PLANTILLA BASE" in out

    def test_template_sin_negative_solo_añade_positive(self, monkeypatch):
        monkeypatch.setattr(
            "modules.prompts_inyeccion.get_prompt_template",
            lambda m: {"positive_base": "POS_ONLY"},
        )
        h = _host()
        out = h._inyectar_template("motor", "X")
        assert "POS_ONLY" in out
        assert "NEGATIVE:" not in out


class TestInyectarSpecsFormato:

    SPECS_NATURAL = {"is_natural": True, "has_negative": True}
    SPECS_NATURAL_SIN_NEG = {"is_natural": True, "has_negative": False}
    SPECS_TAGS = {"is_natural": False, "has_negative": True}
    SPECS_TAGS_SIN_NEG = {"is_natural": False, "has_negative": False}

    def test_natural_con_negative(self):
        h = _host(plataforma_var=_var("X"), _es_comfyui_turbo=lambda *_: False)
        out = h._inyectar_specs_formato("modelo", self.SPECS_NATURAL, "")
        assert "lenguaje natural" in out
        assert "PROMPT:" in out
        assert "NEGATIVE PROMPT:" in out

    def test_natural_sin_negative(self):
        h = _host(plataforma_var=_var("X"), _es_comfyui_turbo=lambda *_: False)
        out = h._inyectar_specs_formato("modelo", self.SPECS_NATURAL_SIN_NEG, "")
        # Pedimos al LLM que use 'PROMPT:' literal + aviso de no generar NEGATIVE
        assert "PROMPT:" in out
        assert "No generes NEGATIVE" in out

    def test_tags_con_pesos_si_no_es_comfyui_turbo(self):
        h = _host(plataforma_var=_var("SeaArt"),
                  _es_comfyui_turbo=lambda *_: False)
        out = h._inyectar_specs_formato("modelo", self.SPECS_TAGS, "")
        assert "tag-based Danbooru" in out
        assert "Puedes usar pesos" in out
        assert "POSITIVE PROMPT:" in out
        assert "NEGATIVE PROMPT:" in out

    def test_comfyui_turbo_prohibe_pesos_y_negative(self):
        h = _host(plataforma_var=_var("ComfyUI"),
                  _es_comfyui_turbo=lambda *_: True)
        out = h._inyectar_specs_formato("modelo", self.SPECS_TAGS, "")
        assert "NO USES PESOS NUMÉRICOS" in out
        assert "NO generes NEGATIVE PROMPT" in out

    def test_tags_sin_negative_lo_prohibe(self):
        h = _host(plataforma_var=_var("X"),
                  _es_comfyui_turbo=lambda *_: False)
        out = h._inyectar_specs_formato("modelo", self.SPECS_TAGS_SIN_NEG, "")
        assert "NO SOPORTA NEGATIVE" in out

    def test_trigger_words_se_inyectan(self):
        specs = {**self.SPECS_TAGS, "trigger_words": "masterpiece, best quality"}
        h = _host(plataforma_var=_var("X"),
                  _es_comfyui_turbo=lambda *_: False)
        out = h._inyectar_specs_formato("modelo", specs, "")
        assert "TRIGGER WORDS OBLIGATORIOS" in out
        assert "masterpiece, best quality" in out

    def test_sampler_recomendado_se_inyecta(self):
        specs = {**self.SPECS_TAGS, "sampler_recomendado": "DPM++ 2M Karras"}
        h = _host(plataforma_var=_var("X"),
                  _es_comfyui_turbo=lambda *_: False)
        out = h._inyectar_specs_formato("modelo", specs, "")
        assert "DPM++ 2M Karras" in out


class TestInyectarSpecsAudio:

    SPECS_AUDIO = {
        "nota": 4,
        "best_for": "letras complejas",
        "duracion_max_min": 4,
        "usa_tags_estructurales": True,
        "has_instrumental_toggle": True,
        "prompt_ejemplo_estilo": "Indie pop, female voice",
        "limitaciones": "máx 2 versos",
    }

    def test_sin_combo_modelo_audio_devuelve_base(self):
        h = _host()  # sin combo_modelo_audio
        assert h._inyectar_specs_audio("base") == "base"

    def test_separador_no_toca(self, monkeypatch):
        monkeypatch.setattr(
            "modules.prompts_inyeccion.es_separador",
            lambda m: True,
        )
        h = _host(combo_modelo_audio=_var("──── Separador ────"))
        assert h._inyectar_specs_audio("base") == "base"

    def test_sin_specs_no_toca(self, monkeypatch):
        monkeypatch.setattr(
            "modules.prompts_inyeccion.es_separador", lambda m: False,
        )
        monkeypatch.setattr(
            "modules.prompts_inyeccion.get_audio_model_specs", lambda m: None,
        )
        h = _host(combo_modelo_audio=_var("Desconocido"))
        assert h._inyectar_specs_audio("base") == "base"

    def test_instrumental_activo_avisa_no_letra(self, monkeypatch):
        monkeypatch.setattr(
            "modules.prompts_inyeccion.es_separador", lambda m: False,
        )
        monkeypatch.setattr(
            "modules.prompts_inyeccion.get_audio_model_specs",
            lambda m: self.SPECS_AUDIO,
        )
        h = _host(
            combo_modelo_audio=_var("Suno"),
            switch_instrumental_var=_var(True),
        )
        out = h._inyectar_specs_audio("base")
        assert "MODO INSTRUMENTAL ACTIVO" in out
        assert "NO generes letra" in out

    def test_vocal_no_avisa_instrumental(self, monkeypatch):
        monkeypatch.setattr(
            "modules.prompts_inyeccion.es_separador", lambda m: False,
        )
        monkeypatch.setattr(
            "modules.prompts_inyeccion.get_audio_model_specs",
            lambda m: self.SPECS_AUDIO,
        )
        h = _host(
            combo_modelo_audio=_var("Suno"),
            switch_instrumental_var=_var(False),
        )
        out = h._inyectar_specs_audio("base")
        assert "VOCAL" in out
        assert "MODO INSTRUMENTAL ACTIVO" not in out

    def test_emocion_voz_idioma_se_inyectan(self, monkeypatch):
        monkeypatch.setattr(
            "modules.prompts_inyeccion.es_separador", lambda m: False,
        )
        monkeypatch.setattr(
            "modules.prompts_inyeccion.get_audio_model_specs",
            lambda m: self.SPECS_AUDIO,
        )
        h = _host(
            combo_modelo_audio=_var("Suno"),
            switch_instrumental_var=_var(False),
            emocion_var=_var("Melancólica"),
            voz_var=_var("Femenina grave"),
            idioma_audio_var=_var("Inglés"),
        )
        out = h._inyectar_specs_audio("base")
        assert "Melancólica" in out
        assert "Femenina grave" in out
        assert "Inglés" in out

    def test_placeholders_emocion_no_se_inyectan(self, monkeypatch):
        monkeypatch.setattr(
            "modules.prompts_inyeccion.es_separador", lambda m: False,
        )
        monkeypatch.setattr(
            "modules.prompts_inyeccion.get_audio_model_specs",
            lambda m: self.SPECS_AUDIO,
        )
        h = _host(
            combo_modelo_audio=_var("Suno"),
            switch_instrumental_var=_var(False),
            emocion_var=_var("— Emoción —"),
            voz_var=_var("— Voz —"),
            idioma_audio_var=_var("— Idioma —"),
        )
        out = h._inyectar_specs_audio("base")
        assert "EMOCIÓN SOLICITADA" not in out
        assert "VOZ SOLICITADA" not in out
        assert "IDIOMA DE LA LETRA" not in out


class TestConstruirModeloInfo:

    def _host_imagen(self):
        return _host(
            modo_var=_var("imagen"),
            modelo_imagen_valido=lambda: "FluxDev",
            modelo_video_valido=lambda: "",
            combo_modelo_audio=_var(""),
            ratio_actual=lambda: "16:9",
            personaje_activo=lambda: "Alicia",
            lora_activo=lambda: "AnimeStyle",
            destino_var=_var("Instagram"),
        )

    def test_imagen_compone_info_completa(self):
        h = self._host_imagen()
        info = h.construir_modelo_info()
        assert "Modelo: FluxDev" in info
        assert "Ratio: 16:9" in info
        assert "Personaje: Alicia" in info
        assert "LoRA: AnimeStyle" in info
        assert "Destino: Instagram" in info

    def test_destino_personal_no_se_incluye(self):
        h = self._host_imagen()
        h.app.destino_var = _var("— Personal —")  # A1 fase 2: el atributo vive en app
        info = h.construir_modelo_info()
        assert "Destino" not in info

    def test_cache_hit_devuelve_mismo_objeto(self):
        h = self._host_imagen()
        info1 = h.construir_modelo_info()
        info2 = h.construir_modelo_info()
        assert info1 is info2  # mismo objeto, viene de cache

    def test_cache_invalida_al_cambiar_modelo(self):
        h = self._host_imagen()
        info1 = h.construir_modelo_info()
        # Cambiar el modelo invalida la caché
        h.app.modelo_imagen_valido = lambda: "SDXL"  # A1 fase 2
        info2 = h.construir_modelo_info()
        assert info1 != info2
        assert "SDXL" in info2

    def test_modo_audio_incluye_emocion(self):
        h = _host(
            modo_var=_var("audio"),
            modelo_imagen_valido=lambda: "",
            modelo_video_valido=lambda: "",
            combo_modelo_audio=_var("Suno"),
            ratio_actual=lambda: "",
            personaje_activo=lambda: "",
            lora_activo=lambda: "",
            destino_var=_var("— Personal —"),
            emocion_var=_var("Triste"),
            voz_var=_var("— Voz —"),
            idioma_audio_var=_var("Español"),
        )
        info = h.construir_modelo_info()
        assert "Motor audio: Suno" in info
        assert "Emoción: Triste" in info
        assert "Idioma letra: Español" in info
        assert "Voz" not in info  # placeholder no se inyecta
