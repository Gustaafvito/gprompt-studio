"""Tests para DialogsService (modules/dialogs.py).

Cobertura de la API base que usan todos los demás services:
  • _darker — helper de manipulación de hex puro.
  • set_estado — actualiza lbl_estado si existe, no-op si no.
  • actualizar_salida — delete + insert + colorear.
  • toggle_botones — activa/desactiva action_btns + maneja barra de progreso.
  • _iniciar_progreso / _detener_progreso — gestión del flag _progreso_activo.
  • _actualizar_tokens — formato del contador según POS/NEG.
  • _sonar_completado — captura ImportError de winsound silenciosamente.
  • _cmd_toggle_tema — alterna y persiste preferencia.
  • _colorear_resultado — añade tags POSITIVE/NEGATIVE/PROMPT.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.dialogs import DialogsService


def _host(**overrides):
    app = SimpleNamespace()
    defaults = dict(
        after=lambda *a, **k: None,
        store=SimpleNamespace(
            cargar_preferencias=lambda: {},
            guardar_preferencias=MagicMock(),
        ),
        _apply_theme_colors=MagicMock(),
        get_current_model_specs=lambda: {"max_chars": 1500},
        extraer_positive=lambda: "",
        extraer_negative=lambda: "",
    )
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(app, k, v)
    return DialogsService(app)


# ─────────────────────── _darker ──────────────────────────────────────


class TestDarker:

    def test_oscurece_blanco_a_gris(self):
        h = _host()
        result = h._darker("#ffffff", factor=0.5)
        assert result == "#7f7f7f"

    def test_oscurece_color_arbitrario(self):
        h = _host()
        # #1a8a3c → cada componente * 0.8
        result = h._darker("#1a8a3c", factor=0.8)
        # 0x1a=26 * 0.8 = 20.8 → int = 20 = 0x14
        # 0x8a=138 * 0.8 = 110.4 → 110 = 0x6e
        # 0x3c=60 * 0.8 = 48 = 0x30
        assert result == "#146e30"

    def test_negro_se_mantiene_negro(self):
        h = _host()
        assert h._darker("#000000", factor=0.5) == "#000000"

    def test_acepta_hex_sin_almohadilla(self):
        h = _host()
        # lstrip('#') hace que funcione con o sin #
        result = h._darker("ffffff", factor=1.0)
        assert result == "#ffffff"


# ─────────────────────── set_estado ───────────────────────────────────


class TestSetEstado:

    def test_actualiza_label_si_existe(self):
        lbl = MagicMock()
        h = _host(lbl_estado=lbl)
        h.set_estado("test msg", "#fff")
        lbl.configure.assert_called_once()
        kwargs = lbl.configure.call_args.kwargs
        assert kwargs["text"] == "test msg"
        assert kwargs["text_color"] == "#fff"

    def test_no_crashea_si_no_hay_label(self):
        h = _host()
        # Sin lbl_estado: simplemente no hace nada.
        h.set_estado("test", "#fff")  # No raise

    def test_color_por_defecto_se_resuelve_desde_tema(self):
        lbl = MagicMock()
        h = _host(lbl_estado=lbl)
        h.set_estado("test")  # sin color → resuelve desde tema
        kwargs = lbl.configure.call_args.kwargs
        assert kwargs["text_color"]  # algún color válido


# ─────────────────────── actualizar_salida ────────────────────────────


class TestActualizarSalida:

    def test_borra_e_inserta_texto_en_txt_salida(self):
        txt = MagicMock()
        txt._textbox = MagicMock()
        # CRÍTICO: txt.search debe devolver "" para que el while True
        # de _colorear_resultado salga; un MagicMock por defecto es
        # truthy → bucle infinito.
        txt.search.return_value = ""
        h = _host(
            txt_salida=txt,
            _guardar_version_prompt=MagicMock(),
            _actualizar_tokens=MagicMock(),
            lbl_tokens=MagicMock(),
            extraer_positive=lambda: "",
            extraer_negative=lambda: "",
        )
        h.actualizar_salida("nuevo texto")
        txt.delete.assert_called_once_with("1.0", "end")
        txt.insert.assert_called_once_with("1.0", "nuevo texto")

    def test_no_crashea_sin_txt_salida(self):
        h = _host()
        h.actualizar_salida("x")  # No raise


# ─────────────────────── toggle_botones ───────────────────────────────


class TestToggleBotones:

    def test_activa_todos_los_botones(self):
        btns = [MagicMock(), MagicMock(), MagicMock()]
        h = _host(action_btns=btns)
        h.toggle_botones(True)
        for b in btns:
            b.configure.assert_called_with(state="normal")

    def test_desactiva_todos_los_botones(self):
        btns = [MagicMock(), MagicMock()]
        h = _host(action_btns=btns)
        h.toggle_botones(False)
        for b in btns:
            b.configure.assert_called_with(state="disabled")

    def test_sin_action_btns_no_crashea(self):
        h = _host()
        h.toggle_botones(True)  # No raise


# ─────────────────────── _iniciar_progreso / _detener_progreso ────────


class TestProgreso:

    def test_iniciar_marca_flag_y_arranca_barra(self):
        bar = MagicMock()
        h = _host(progress=bar, _progreso_activo=False)
        h._iniciar_progreso()
        assert h.app._progreso_activo is True
        bar.start.assert_called_once()

    def test_iniciar_es_idempotente(self):
        bar = MagicMock()
        h = _host(progress=bar, _progreso_activo=True)
        h._iniciar_progreso()
        # Ya activo → no inicia de nuevo
        bar.start.assert_not_called()

    def test_detener_resetea_flag_y_oculta_barra(self):
        bar = MagicMock()
        h = _host(progress=bar, _progreso_activo=True)
        h._detener_progreso()
        assert h.app._progreso_activo is False
        bar.stop.assert_called_once()


# ─────────────────────── _actualizar_tokens ───────────────────────────


class TestActualizarTokens:

    def test_sin_salida_o_lbl_tokens_no_crashea(self):
        h = _host()
        h._actualizar_tokens()  # No raise

    def test_pos_dentro_del_limite_muestra_color_normal(self):
        lbl = MagicMock()
        txt = SimpleNamespace(get=lambda *_a, **_k: "POSITIVE PROMPT: corto")
        h = _host(
            txt_salida=txt, lbl_tokens=lbl,
            extraer_positive=lambda: "corto",
            extraer_negative=lambda: "",
        )
        h._actualizar_tokens()
        lbl.configure.assert_called_once()
        kwargs = lbl.configure.call_args.kwargs
        assert "EXCEDE" not in kwargs["text"]

    def test_pos_excede_max_muestra_aviso(self):
        lbl = MagicMock()
        long_pos = "x" * 2000
        txt = SimpleNamespace(get=lambda *_a, **_k: f"POSITIVE PROMPT: {long_pos}")
        h = _host(
            txt_salida=txt, lbl_tokens=lbl,
            extraer_positive=lambda: long_pos,
            extraer_negative=lambda: "",
            get_current_model_specs=lambda: {"max_chars": 1500},
        )
        h._actualizar_tokens()
        kwargs = lbl.configure.call_args.kwargs
        assert "EXCEDE" in kwargs["text"]


# ─────────────────────── _sonar_completado ────────────────────────────


class TestSonarCompletado:

    def test_no_raise_si_winsound_no_disponible(self, monkeypatch):
        import builtins
        orig = builtins.__import__

        def _fake(name, *a, **k):
            if name == "winsound":
                raise ImportError("no winsound")
            return orig(name, *a, **k)

        monkeypatch.setattr(builtins, "__import__", _fake)
        h = _host()
        h._sonar_completado()  # No raise


# ─────────────────────── _cmd_toggle_tema ─────────────────────────────


class TestCmdToggleTema:

    def test_alterna_dark_a_light(self, monkeypatch):
        guardadas = {}
        def _guardar(p):
            guardadas.update(p)
        h = _host(store=SimpleNamespace(
            cargar_preferencias=lambda: {"otro": "x"},
            guardar_preferencias=_guardar,
        ))
        monkeypatch.setattr("modules.dialogs.ctk.get_appearance_mode",
                            lambda: "Dark")
        spy_set = MagicMock()
        monkeypatch.setattr("modules.dialogs.ctk.set_appearance_mode", spy_set)
        h._cmd_toggle_tema()
        spy_set.assert_called_once_with("Light")
        assert guardadas.get("tema") == "light"

    def test_alterna_light_a_dark(self, monkeypatch):
        guardadas = {}
        h = _host(store=SimpleNamespace(
            cargar_preferencias=lambda: {},
            guardar_preferencias=lambda p: guardadas.update(p),
        ))
        monkeypatch.setattr("modules.dialogs.ctk.get_appearance_mode",
                            lambda: "Light")
        spy_set = MagicMock()
        monkeypatch.setattr("modules.dialogs.ctk.set_appearance_mode", spy_set)
        h._cmd_toggle_tema()
        spy_set.assert_called_once_with("Dark")
        assert guardadas.get("tema") == "dark"


# ─────────────────────── _colorear_resultado ──────────────────────────


class TestColorearResultado:

    def test_no_crashea_sin_txt_salida(self):
        h = _host()
        h._colorear_resultado()  # No raise

    def test_aplica_tags_pos_y_neg(self):
        """search devuelve un índice y luego "" para parar el while."""
        txt = MagicMock()
        # search devolverá "1.0" en la primera llamada y "" en la segunda
        # por cada etiqueta probada; con 5 etiquetas → 10 llamadas.
        txt.search.side_effect = ["1.0", ""] * 5
        h = _host(txt_salida=txt)
        h._colorear_resultado()
        # Se llamó a tag_add al menos una vez por etiqueta encontrada
        assert txt.tag_add.call_count == 5
