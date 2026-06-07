"""Tests para AtajosAyudaService (modules/atajos_ayuda.py).

Cobertura de comandos de atajos sin abrir ventanas Tk reales:
  • _cmd_cambiar_modo — guards de modo inválido + cambio válido.
  • _cmd_exportar_rapido — 3 ramas (con _exportar / cmd_exportar / nada).
  • _atajo_guardar_estrella — con / sin _guardar_estrella.
  • _atajo_traducir_idea — idea vacía, traducción OK, traducción igual,
    excepción.
  • _cmd_buscar_global / _atajo_buscar_global — manejo de errores.
  • _toggle_fullscreen — usa _toggle_fullscreen_principal o attributes.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.atajos_ayuda import AtajosAyudaService


def _var(value):
    return SimpleNamespace(get=lambda: value, set=MagicMock())


def _txt(value):
    return SimpleNamespace(get=lambda *_a, **_k: value + "\n",
                           delete=MagicMock(),
                           insert=MagicMock())


def _host(**overrides):
    app = SimpleNamespace()
    defaults = dict(
        modo_var=_var("imagen"),
        txt_idea=_txt(""),
        deepseek=SimpleNamespace(traducir=lambda txt: txt),
        attributes=MagicMock(return_value=False),
        winfo_children=lambda: [],
    )
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(app, k, v)
    app.dialogs = SimpleNamespace(set_estado=MagicMock())
    # A1 fase 2 bug-fix sesión 15: _cmd_cambiar_modo ahora llama
    # self.app.events.on_modo_cambio() en lugar de self.app._on_modo_cambio()
    app.events = SimpleNamespace(on_modo_cambio=MagicMock())
    return AtajosAyudaService(app)


# ─────────────────────── _cmd_cambiar_modo ────────────────────────────


class TestCmdCambiarModo:

    def test_modo_invalido_devuelve_break(self):
        h = _host()
        assert h._cmd_cambiar_modo("xxx") == "break"
        # No debió tocar modo_var
        h.app.modo_var.set.assert_not_called()

    def test_modo_imagen_cambia(self):
        h = _host()
        h._cmd_cambiar_modo("imagen")
        h.app.modo_var.set.assert_called_once_with("imagen")
        h.app.events.on_modo_cambio.assert_called_once()
        h.app.dialogs.set_estado.assert_called_once()
        msg = h.app.dialogs.set_estado.call_args[0][0]
        assert "IMAGEN" in msg

    def test_modo_video_cambia(self):
        h = _host()
        h._cmd_cambiar_modo("video")
        h.app.modo_var.set.assert_called_once_with("video")
        msg = h.app.dialogs.set_estado.call_args[0][0]
        assert "VÍDEO" in msg

    def test_modo_audio_cambia(self):
        h = _host()
        h._cmd_cambiar_modo("audio")
        h.app.modo_var.set.assert_called_once_with("audio")
        msg = h.app.dialogs.set_estado.call_args[0][0]
        assert "AUDIO" in msg


# ─────────────────────── _cmd_exportar_rapido ─────────────────────────


class TestCmdExportarRapido:

    def test_usa_exportar_si_existe(self):
        h = _host()
        h.app._exportar = MagicMock()
        h._cmd_exportar_rapido()
        h.app._exportar.assert_called_once()

    def test_usa_cmd_exportar_si_no_hay_exportar(self):
        h = _host()
        # No tiene _exportar pero sí cmd_exportar
        h.app.cmd_exportar = MagicMock()
        h._cmd_exportar_rapido()
        h.app.cmd_exportar.assert_called_once()

    def test_warns_si_no_hay_ninguno(self):
        h = _host()
        h._cmd_exportar_rapido()
        h.app.dialogs.set_estado.assert_called_once()
        assert "no disponible" in h.app.dialogs.set_estado.call_args[0][0].lower()


# ─────────────────────── _atajo_guardar_estrella ──────────────────────


class TestAtajoGuardarEstrella:

    def test_llama_guardar_estrella_si_existe(self):
        h = _host()
        h.app._guardar_estrella = MagicMock()
        h._atajo_guardar_estrella()
        h.app._guardar_estrella.assert_called_once()

    def test_warns_si_no_existe(self):
        h = _host()
        h._atajo_guardar_estrella()
        h.app.dialogs.set_estado.assert_called_once()


# ─────────────────────── _atajo_traducir_idea ─────────────────────────


class TestAtajoTraducirIdea:

    def test_idea_vacia_warns(self):
        h = _host(txt_idea=_txt(""))
        h._atajo_traducir_idea()
        h.app.dialogs.set_estado.assert_called_once()
        assert "Escribe" in h.app.dialogs.set_estado.call_args[0][0]

    def test_traduccion_distinta_reemplaza_idea(self):
        h = _host(
            txt_idea=_txt("hola mundo"),
            deepseek=SimpleNamespace(traducir=lambda _t: "hello world"),
        )
        h._atajo_traducir_idea()
        h.app.txt_idea.delete.assert_called_once()
        h.app.txt_idea.insert.assert_called_once_with("1.0", "hello world")
        msg = h.app.dialogs.set_estado.call_args[0][0]
        assert "traducida" in msg.lower() or "🌐" in msg

    def test_traduccion_igual_a_original_warns(self):
        # Cuando la traducción es igual al original (texto ya en inglés
        # o el motor no lo cambia), debe avisar y NO reemplazar.
        h = _host(
            txt_idea=_txt("hello world"),
            deepseek=SimpleNamespace(traducir=lambda _t: "hello world"),
        )
        h._atajo_traducir_idea()
        # El strip elimina \n → quedan iguales. Verificamos warning.
        msg = h.app.dialogs.set_estado.call_args[0][0]
        assert "No se pudo" in msg or "traducir" in msg.lower()

    def test_excepcion_en_motor_warns(self):
        def _explota(_t):
            raise RuntimeError("boom")
        h = _host(
            txt_idea=_txt("texto"),
            deepseek=SimpleNamespace(traducir=_explota),
        )
        h._atajo_traducir_idea()
        msg = h.app.dialogs.set_estado.call_args[0][0]
        assert "boom" in msg or "Error" in msg


# ─────────────────────── _cmd_buscar_global ───────────────────────────


class TestBuscarGlobal:

    def test_atajo_buscar_global_captura_excepcion(self, monkeypatch):
        h = _host()
        def _explota():
            raise RuntimeError("err")
        monkeypatch.setattr(h, "_abrir_busqueda_global", _explota)
        result = h._atajo_buscar_global()
        assert result == "break"
        h.app.dialogs.set_estado.assert_called_once()

    def test_cmd_buscar_global_captura_excepcion(self, monkeypatch):
        h = _host()
        def _explota():
            raise RuntimeError("err")
        monkeypatch.setattr(h, "_abrir_busqueda_global", _explota)
        result = h._cmd_buscar_global()
        assert result == "break"
        h.app.dialogs.set_estado.assert_called_once()


# ─────────────────────── _toggle_fullscreen ───────────────────────────


class TestToggleFullscreen:

    def test_usa_toggle_principal_si_existe(self):
        h = _host()
        h.app._toggle_fullscreen_principal = MagicMock()
        result = h._toggle_fullscreen()
        assert result == "break"
        h.app._toggle_fullscreen_principal.assert_called_once()

    def test_fallback_a_attributes(self):
        h = _host(attributes=MagicMock(return_value=False))
        result = h._toggle_fullscreen()
        assert result == "break"
        # Lee + escribe attributes
        assert h.app.attributes.call_count >= 2
