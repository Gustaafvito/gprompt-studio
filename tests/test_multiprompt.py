"""Tests para MultiPromptService (modules/multiprompt.py).

Cobertura:
  • STORY_SHOT_TYPES — estructura del catálogo de shots.
  • _story_label_de_key — pure helper, lookup en lista canónica.
  • _cmd_moodboard — guarda de idea corta.
  • _cmd_story_sequence — guarda de modo + idea.
  • _cmd_storyboard_video — guarda de modo + idea.
  • _cmd_storyboard_imagen — guarda de modo + idea.
  • _encadenar_board_a_video — guarda de frames vacíos.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.multiprompt import (
    MultiPromptService,
    construir_peticion_cortometraje,
)


def _var(value):
    return SimpleNamespace(get=lambda: value, set=lambda _v: None)


def _txt(value):
    return SimpleNamespace(get=lambda *_a, **_k: value + "\n",
                           delete=lambda *_a, **_k: None,
                           insert=lambda *_a, **_k: None)


class _SyncExec:
    def submit(self, fn, *args, **kwargs):
        try:
            fn(*args, **kwargs)
        except Exception:
            pass
        return SimpleNamespace(add_done_callback=lambda _cb: None)


def _host(modo="imagen", idea="una idea bastante larga", **overrides):
    app = SimpleNamespace()
    defaults = dict(
        modo_var=_var(modo),
        txt_idea=_txt(idea),
        deepseek=SimpleNamespace(generar=lambda *a, **k: ""),
        store=SimpleNamespace(
            cargar_preferencias=lambda: {},
            guardar_preferencias=lambda _p: None,
        ),
        after=lambda *a, **k: None,
        _pedir_n_modal=lambda *a, **k: 3,
        _parsear_bloques_numerados=lambda txt, n_esperado=None: [],
        _abrir_comparador=MagicMock(),
        _sesion_log=MagicMock(),
        _on_modo_cambio=MagicMock(),
        guardar_en_historial=MagicMock(),
        STORY_SHOT_TYPES=MultiPromptService.STORY_SHOT_TYPES,
        _executor=_SyncExec(),
    )
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(app, k, v)
    app.dialogs = SimpleNamespace(
        set_estado=MagicMock(),
        toggle_botones=MagicMock(),
        actualizar_salida=MagicMock(),
        _sonar_completado=MagicMock(),
    )
    app.footer = SimpleNamespace(
        estilos_texto=lambda: "cinematic",
        modelo_imagen_valido=lambda: None,
    )
    return MultiPromptService(app)


# ─────────────────────── STORY_SHOT_TYPES ─────────────────────────────


class TestStoryShotTypes:

    def test_tiene_8_tipos(self):
        assert len(MultiPromptService.STORY_SHOT_TYPES) == 8

    def test_cada_tipo_es_3_tuple(self):
        for entry in MultiPromptService.STORY_SHOT_TYPES:
            assert isinstance(entry, tuple) and len(entry) == 3
            k, label, desc = entry
            assert isinstance(k, str) and isinstance(label, str) and isinstance(desc, str)
            assert k and label  # ni vacíos

    def test_keys_son_unicas(self):
        keys = [k for k, _, _ in MultiPromptService.STORY_SHOT_TYPES]
        assert len(keys) == len(set(keys))


# ─────────────────────── _story_label_de_key ──────────────────────────


class TestStoryLabelDeKey:

    def test_devuelve_label_si_key_existe(self):
        h = _host()
        assert h._story_label_de_key("wide") == "Wide"
        assert h._story_label_de_key("close") == "Close-Up"

    def test_devuelve_key_si_no_existe(self):
        h = _host()
        assert h._story_label_de_key("inexistente") == "inexistente"


# ─────────────────────── _cmd_moodboard ───────────────────────────────


class TestCmdMoodboard:

    def test_idea_vacia_warns(self):
        h = _host(idea="")
        h._cmd_moodboard()
        h.app.dialogs.set_estado.assert_called_once()
        assert "concepto" in h.app.dialogs.set_estado.call_args[0][0].lower()

    def test_idea_corta_warns(self):
        h = _host(idea="abc")  # < 5 chars
        h._cmd_moodboard()
        h.app.dialogs.set_estado.assert_called_once()

    def test_cancelar_pedir_n_aborta(self):
        mock_exec = MagicMock()
        h = _host(_executor=mock_exec)
        h.app._pedir_n_modal = lambda *a, **k: None  # usuario cancela
        h._cmd_moodboard()
        mock_exec.submit.assert_not_called()

    def test_inicia_worker_con_idea_valida(self):
        mock_exec = MagicMock()
        mock_exec.submit.return_value = SimpleNamespace(add_done_callback=lambda _cb: None)
        h = _host(_executor=mock_exec)
        h._cmd_moodboard()
        mock_exec.submit.assert_called_once()
        h.app.dialogs.toggle_botones.assert_called_once_with(False)


# ─────────────────────── _cmd_story_sequence ──────────────────────────


class TestCmdStorySequence:

    def test_modo_no_imagen_warns(self):
        h = _host(modo="video")
        h._cmd_story_sequence()
        assert "IMAGEN" in h.app.dialogs.set_estado.call_args[0][0]

    def test_idea_vacia_warns(self):
        h = _host(modo="imagen", idea="")
        h._cmd_story_sequence()
        h.app.dialogs.set_estado.assert_called_once()


# ─────────────────────── _cmd_storyboard_video ────────────────────────


class TestCmdStoryboardVideo:

    def test_modo_no_video_warns(self):
        h = _host(modo="imagen")
        h._cmd_storyboard_video()
        assert "VÍDEO" in h.app.dialogs.set_estado.call_args[0][0]

    def test_idea_vacia_warns(self):
        h = _host(modo="video", idea="")
        h._cmd_storyboard_video()
        h.app.dialogs.set_estado.assert_called_once()


# ─────────────────────── Cortometraje ─────────────────────────────────


class TestCortometraje:

    def test_peticion_tiene_formato_completo(self):
        p = construir_peticion_cortometraje(
            "una ex se venga en el apocalipsis", "Emma: mujer fría", 6, "es")
        assert "=== PERSONAJES ===" in p
        assert "=== ESCENA 1 ===" in p and "ESCENA 6" in p
        assert "@ref" in p
        for campo in ("Tiempo:", "Plano:", "Tema:", "Acción:",
                      "Cámara:", "Diálogo:", "SFX:"):
            assert campo in p, f"falta {campo}"

    def test_peticion_idioma_en(self):
        assert "INGLÉS" in construir_peticion_cortometraje("x", "", 4, "en")
        assert "ESPAÑOL" in construir_peticion_cortometraje("x", "", 4, "es")

    def test_sin_personajes_usa_fallback(self):
        p = construir_peticion_cortometraje("premisa", "", 3, "es")
        assert "Inventa" in p  # fallback de personajes

    def test_modo_no_video_warns(self):
        h = _host(modo="imagen")
        h._cmd_cortometraje()
        assert "VÍDEO" in h.app.dialogs.set_estado.call_args[0][0]

    def test_idea_vacia_warns(self):
        h = _host(modo="video", idea="")
        h._cmd_cortometraje()
        h.app.dialogs.set_estado.assert_called_once()


# ─────────────────────── _cmd_storyboard_imagen ───────────────────────


class TestCmdStoryboardImagen:

    def test_modo_no_imagen_warns(self):
        h = _host(modo="audio")
        h._cmd_storyboard_imagen()
        assert "IMAGEN" in h.app.dialogs.set_estado.call_args[0][0]

    def test_idea_vacia_warns(self):
        h = _host(modo="imagen", idea="")
        h._cmd_storyboard_imagen()
        h.app.dialogs.set_estado.assert_called_once()


# ─────────────────────── _encadenar_board_a_video ─────────────────────


class TestEncadenarBoardAVideo:

    def test_sin_frames_warns(self):
        h = _host()
        h._encadenar_board_a_video([], vent_comparador=None)
        h.app.dialogs.set_estado.assert_called_once()
        assert "frames" in h.app.dialogs.set_estado.call_args[0][0].lower()

    def test_con_frames_lanza_worker(self):
        mock_exec = MagicMock()
        mock_exec.submit.return_value = SimpleNamespace(add_done_callback=lambda _cb: None)
        h = _host(_executor=mock_exec)
        h._encadenar_board_a_video(["frame A", "frame B"], vent_comparador=None)
        mock_exec.submit.assert_called_once()
        h.app.dialogs.toggle_botones.assert_called_once_with(False)
