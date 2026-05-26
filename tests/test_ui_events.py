"""Tests para UiEventsMixin (modules/ui_events.py).

Cobertura de la lógica testeable de los event handlers de los combos
del panel superior. Los widgets ctk se mockean con SimpleNamespace +
MagicMock para no requerir display tk.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from modules.ui_events import UiEventsMixin


def _var(value):
    return SimpleNamespace(get=lambda: value, set=MagicMock())


def _combo(value="", values=None):
    """Imita CTkComboBox con get()/set()/configure()."""
    state = {"value": value, "values": values or []}

    def _configure(**kw):
        if "values" in kw:
            state["values"] = kw["values"]
        # ignora otros kw (width, height, etc.)

    cb = SimpleNamespace(
        get=lambda: state["value"],
        set=lambda v: state.update(value=v),
        configure=_configure,
        _state=state,
    )
    return cb


def _host(**overrides):
    cls = type("Host", (UiEventsMixin,), {})
    h = cls()
    defaults = dict(
        set_estado=MagicMock(),
        reiniciar_memoria=MagicMock(),
        _sesion_log=MagicMock(),
        _packear_negative_y_imgref=MagicMock(),
        is_natural_mode=lambda: False,
        modo_var=_var("imagen"),
        plataforma_var=_var("SeaArt / Tensor.Art"),
        ratio_var=_var("1:1"),
        brief_var=_var(False),
        combo_modelo_video=_combo("Veo 3.1", values=[]),
        combo_modelo_audio=_combo("Suno v5", values=[]),
        combo_modelo_imagen=_combo("FLUX.1 [dev]", values=[]),
        combo_ratio_v=_combo("16:9", values=[]),
        combo_ratio=_combo("1:1", values=[]),
        combo_plataforma=_combo("SeaArt / Tensor.Art", values=[]),
        lbl_img_model_info=SimpleNamespace(
            pack_forget=MagicMock(),
            configure=MagicMock(),
        ),
        _safe_pack=MagicMock(),
        _tabview_container=SimpleNamespace(),
        # Estos métodos pertenecen al mixin testeado. Algunos tests los
        # mockean explícitamente vía overrides para verificar llamadas
        # cruzadas (p.ej. _on_plataforma_cambio en audio dispara
        # _on_motor_audio_cambio). El default es no mockear, así el
        # mixin real se ejecuta.
        _construir_checkboxes=MagicMock(),
        _ocultar_ideas=MagicMock(),
        _actualizar_tokens=MagicMock(),
        _actualizar_lora_trigger_visible=MagicMock(),
        _recomendar_loras_para_modelo=MagicMock(),
        _mostrar_consejo_contextual=MagicMock(),
        actualizar_salida=MagicMock(),
        after=lambda _delay, fn=None: fn() if callable(fn) else None,
    )
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(h, k, v)
    return h


# ────────────────────────── _on_brief_cambio ───────────────────────────────


class TestOnBriefCambio:

    def test_brief_on_muestra_mensaje_naranja(self):
        h = _host(brief_var=_var(True))
        h._on_brief_cambio()
        msg, color = h.set_estado.call_args[0]
        assert "Brief ACTIVO" in msg or "brief" in msg.lower()
        assert color == "#f39c12"
        h.reiniciar_memoria.assert_called_once()

    def test_brief_off_muestra_mensaje_default(self):
        h = _host(brief_var=_var(False))
        h._on_brief_cambio()
        msg = h.set_estado.call_args[0][0]
        assert "desactivado" in msg.lower() or "artísticos" in msg.lower()
        h.reiniciar_memoria.assert_called_once()


# ─────────────────────── _on_audio_filtro_cambio ──────────────────────────


class TestOnAudioFiltroCambio:

    def test_sin_filtros_muestra_mensaje_default(self):
        h = _host(
            emocion_var=_var("— Emoción —"),
            voz_var=_var("— Voz —"),
            idioma_audio_var=_var("— Idioma —"),
        )
        h._on_audio_filtro_cambio()
        msg = h.set_estado.call_args[0][0]
        assert "Sin filtros" in msg

    def test_con_emocion_muestra_chip(self):
        h = _host(
            emocion_var=_var("Melancólica"),
            voz_var=_var("— Voz —"),
            idioma_audio_var=_var("— Idioma —"),
        )
        h._on_audio_filtro_cambio()
        msg = h.set_estado.call_args[0][0]
        assert "Melancólica" in msg
        assert "🎭" in msg

    def test_con_todos_los_filtros(self):
        h = _host(
            emocion_var=_var("Triste"),
            voz_var=_var("Femenina"),
            idioma_audio_var=_var("Inglés"),
        )
        h._on_audio_filtro_cambio()
        msg = h.set_estado.call_args[0][0]
        assert "Triste" in msg
        assert "Femenina" in msg
        assert "Inglés" in msg

    def test_sin_atributos_vars_no_falla(self):
        h = _host()  # sin emocion_var, voz_var, idioma_audio_var
        h._on_audio_filtro_cambio()
        h.set_estado.assert_called_once()


# ───────────────────── _actualizar_motores_video ──────────────────────────


class TestActualizarMotoresVideo:

    def test_con_motores_setea_default_y_dispara_on_motor(self, monkeypatch):
        monkeypatch.setattr(
            "modules.ui_events.MOTORES_VIDEO",
            {"SeaArt Video": ["Veo 3.1", "Kling 3.0"]},
        )
        monkeypatch.setattr(
            "modules.ui_events.MOTOR_DEFAULT",
            {"SeaArt Video": "Veo 3.1"},
        )
        h = _host(
            plataforma_var=_var("SeaArt Video"),
            _on_motor_cambio=MagicMock(),  # spy explícito
        )
        h._actualizar_motores_video()
        assert h.combo_modelo_video._state["value"] == "Veo 3.1"
        h._on_motor_cambio.assert_called_once()

    def test_sin_default_usa_primer_motor(self, monkeypatch):
        monkeypatch.setattr(
            "modules.ui_events.MOTORES_VIDEO",
            {"X": ["A", "B"]},
        )
        monkeypatch.setattr(
            "modules.ui_events.MOTOR_DEFAULT",
            {"X": ""},
        )
        h = _host(plataforma_var=_var("X"))
        h._actualizar_motores_video()
        assert h.combo_modelo_video._state["value"] == "A"

    def test_sin_motores_usa_plataforma_como_motor(self, monkeypatch):
        monkeypatch.setattr("modules.ui_events.MOTORES_VIDEO", {})
        monkeypatch.setattr("modules.ui_events.MOTOR_DEFAULT", {})
        h = _host(plataforma_var=_var("PlatX"))
        h._actualizar_motores_video()
        assert h.combo_modelo_video._state["value"] == "PlatX"


# ────────────────────────── _on_motor_cambio ──────────────────────────────


class TestOnMotorCambio:

    SPECS = {
        "ratios": ["16:9", "9:16"],
        "nota": 4.5,
        "best_for": "cinematic",
        "max_chars": 2000,
        "duraciones": ["5s", "10s"],
        "prompt_formula": "subject + action",
        "prompt_ejemplo": "A cat jumps",
        "has_audio": False,
    }

    def test_sin_specs_no_aplica_ratios(self, monkeypatch):
        monkeypatch.setattr(
            "modules.ui_events.get_model_specs", lambda m: None,
        )
        monkeypatch.setattr(
            "modules.ui_events.RATIOS_VIDEO", ["16:9", "9:16"],
        )
        h = _host()
        h._on_motor_cambio("DesconocidoX")
        assert h.combo_ratio_v._state["values"] == ["16:9", "9:16"]
        msg = h.set_estado.call_args[0][0]
        assert "DesconocidoX" in msg

    def test_con_specs_aplica_ratios(self, monkeypatch):
        monkeypatch.setattr(
            "modules.ui_events.get_model_specs", lambda m: self.SPECS,
        )
        h = _host()
        h._on_motor_cambio("Veo")
        assert h.combo_ratio_v._state["values"] == self.SPECS["ratios"]

    def test_ratio_fuera_de_specs_se_resetea(self, monkeypatch):
        monkeypatch.setattr(
            "modules.ui_events.get_model_specs", lambda m: self.SPECS,
        )
        h = _host(ratio_var=_var("21:9"))  # no está en specs
        h._on_motor_cambio("Veo")
        # debe resetearse al primero
        h.ratio_var.set.assert_called_with("16:9")

    def test_motor_name_por_defecto_lee_del_combo(self, monkeypatch):
        monkeypatch.setattr(
            "modules.ui_events.get_model_specs", lambda m: None,
        )
        monkeypatch.setattr(
            "modules.ui_events.RATIOS_VIDEO", ["16:9"],
        )
        h = _host(combo_modelo_video=_combo("MotorActual"))
        h._on_motor_cambio()  # sin argumento
        msg = h.set_estado.call_args[0][0]
        assert "MotorActual" in msg


# ────────────────────── _on_motor_audio_cambio ────────────────────────────


class TestOnMotorAudioCambio:

    SPECS_AUDIO = {
        "nota": 4.5,
        "best_for": "letras complejas",
        "duracion_max_min": 4,
    }

    def test_separador_oculta_info(self, monkeypatch):
        monkeypatch.setattr("modules.ui_events.es_separador", lambda m: True)
        h = _host()
        h._on_motor_audio_cambio("──── Separador ────")
        h.lbl_img_model_info.pack_forget.assert_called()

    def test_sin_specs_oculta_info(self, monkeypatch):
        monkeypatch.setattr("modules.ui_events.es_separador", lambda m: False)
        monkeypatch.setattr(
            "modules.ui_events.get_audio_model_specs", lambda m: None,
        )
        h = _host()
        h._on_motor_audio_cambio("X")
        h.lbl_img_model_info.pack_forget.assert_called()

    def test_con_specs_actualiza_info(self, monkeypatch):
        monkeypatch.setattr("modules.ui_events.es_separador", lambda m: False)
        monkeypatch.setattr(
            "modules.ui_events.get_audio_model_specs", lambda m: self.SPECS_AUDIO,
        )
        h = _host()
        h._on_motor_audio_cambio("Suno v5")
        h.lbl_img_model_info.configure.assert_called()
        msg = h.set_estado.call_args[0][0]
        assert "Suno v5" in msg


# ────────────────────── _on_plataforma_cambio ─────────────────────────────


class TestOnPlataformaCambio:

    def test_modo_audio_setea_motor_default(self, monkeypatch):
        monkeypatch.setattr(
            "modules.ui_events.MOTORES_AUDIO",
            {"Suno": ["Suno v5", "Suno v4"]},
        )
        monkeypatch.setattr(
            "modules.ui_events.MOTOR_DEFAULT",
            {"Suno": "Suno v5"},
        )
        h = _host(
            modo_var=_var("audio"),
            plataforma_var=_var("Suno"),
            _on_motor_audio_cambio=MagicMock(),  # spy explícito
        )
        h._on_plataforma_cambio()
        assert h.combo_modelo_audio._state["value"] == "Suno v5"
        h._on_motor_audio_cambio.assert_called_once()

    def test_modo_video_dispara_actualizar_motores(self):
        h = _host(
            modo_var=_var("video"),
            _actualizar_motores_video=MagicMock(),  # spy explícito
        )
        h._on_plataforma_cambio()
        h._actualizar_motores_video.assert_called_once()
