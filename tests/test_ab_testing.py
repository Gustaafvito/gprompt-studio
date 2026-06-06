"""Tests para AbTestingService (modules/ab_testing.py).

A1 fase 2 (sesión 14): el mixin fue convertido a clase con app por
composición. Los tests crean un fake_app con SimpleNamespace y pasan
al constructor del service.

Cobertura de la lógica testeable sin abrir ventanas Tk reales:
  • AB_DIMENSIONES — estructura del catálogo de dimensiones.
  • _cmd_ab_testing — guarda de idea vacía (no abre modal).
  • _cmd_comparar_modelos — guardas idea vacía/corta + sugeridos por modo.

Las ventanas (GPromptWindow) se mockean con un stub que captura
__init__ y proporciona métodos no-op.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from modules.ab_testing import AbTestingService


def _var(value):
    return SimpleNamespace(get=lambda: value)


def _txt(value):
    return SimpleNamespace(get=lambda *_a, **_k: value + "\n")


def _host(**overrides):
    """Construye un AbTestingService con app simulado.

    Crea un SimpleNamespace como `app` con los atributos por defecto.
    Cualquier override se aplica sobre app antes de instanciar el service.
    """
    app = SimpleNamespace()
    defaults = dict(
        txt_idea=_txt(""),
        modo_var=_var("imagen"),
        set_estado=MagicMock(),
        toggle_botones=MagicMock(),
        _sesion_log=MagicMock(),
        deepseek=SimpleNamespace(generar=lambda *a, **k: "POSITIVE PROMPT: x"),
        actualizar_salida=MagicMock(),
        estilos_texto=lambda: "cinematic",
        get_current_model_specs=lambda: {"max_chars": 1500, "has_negative": True},
    )
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(app, k, v)
    return AbTestingService(app)


# ─────────────────────── AB_DIMENSIONES ──────────────────────────────


class TestAbDimensiones:

    def test_tiene_dimensiones_clave(self):
        dims = AbTestingService.AB_DIMENSIONES
        assert "iluminación" in dims
        assert "mood" in dims
        assert "ángulo" in dims

    def test_cada_dimension_tiene_exactamente_4_valores(self):
        for nombre, valores in AbTestingService.AB_DIMENSIONES.items():
            assert len(valores) == 4, f"{nombre} tiene {len(valores)} valores, esperaba 4"

    def test_todos_los_valores_son_strings_no_vacios(self):
        for nombre, valores in AbTestingService.AB_DIMENSIONES.items():
            for v in valores:
                assert isinstance(v, str) and len(v.strip()) > 0


# ─────────────────────── _cmd_ab_testing ─────────────────────────────


class TestCmdAbTesting:

    def test_idea_vacia_muestra_warning_sin_abrir_modal(self, monkeypatch):
        h = _host(txt_idea=_txt(""))
        # Spy sobre GPromptWindow: si se llamase, lo registramos
        spy = MagicMock()
        monkeypatch.setattr("modules.ab_testing.GPromptWindow", spy)
        h._cmd_ab_testing()
        h.app.set_estado.assert_called_once()
        assert "Escribe una idea" in h.app.set_estado.call_args[0][0]
        spy.assert_not_called()  # No se abrió ventana

    def test_idea_solo_espacios_es_vacia(self, monkeypatch):
        h = _host(txt_idea=_txt("   "))
        spy = MagicMock()
        monkeypatch.setattr("modules.ab_testing.GPromptWindow", spy)
        h._cmd_ab_testing()
        h.app.set_estado.assert_called_once()
        spy.assert_not_called()


# ─────────────────────── _cmd_comparar_modelos ───────────────────────


class TestCmdCompararModelos:

    def test_idea_vacia_muestra_warning(self, monkeypatch):
        h = _host(txt_idea=_txt(""))
        spy = MagicMock()
        monkeypatch.setattr("modules.ab_testing.GPromptWindow", spy)
        h._cmd_comparar_modelos()
        h.app.set_estado.assert_called_once()
        assert "Escribe una idea" in h.app.set_estado.call_args[0][0]
        spy.assert_not_called()

    def test_idea_muy_corta_muestra_warning(self, monkeypatch):
        h = _host(txt_idea=_txt("abc"))  # < 5 chars
        spy = MagicMock()
        monkeypatch.setattr("modules.ab_testing.GPromptWindow", spy)
        h._cmd_comparar_modelos()
        h.app.set_estado.assert_called_once()
        spy.assert_not_called()

    def test_idea_de_5_chars_no_es_corta_y_abre_modal(self, monkeypatch):
        h = _host(txt_idea=_txt("hello"))  # = 5 chars
        # Stub completo de GPromptWindow para que el modal "funcione" sin tk
        gpw = MagicMock()
        monkeypatch.setattr("modules.ab_testing.GPromptWindow", gpw)
        # Stub todos los widgets de ctk que se usan en el modal
        for name in ["CTkLabel", "CTkFrame", "CTkComboBox", "CTkSlider",
                    "CTkButton", "CTkFont", "IntVar"]:
            monkeypatch.setattr(f"modules.ab_testing.ctk.{name}", MagicMock())
        h._cmd_comparar_modelos()
        gpw.assert_called_once()  # Sí se abrió ventana

    def test_modo_imagen_sugiere_modelos_de_imagen(self, monkeypatch):
        """Verificamos indirectamente que el modo correcto activa el código
        de imagen consultando que NO se mencione un modelo de vídeo en
        la llamada al combo."""
        h = _host(txt_idea=_txt("una idea suficientemente larga"),
                  modo_var=_var("imagen"))
        gpw = MagicMock()
        monkeypatch.setattr("modules.ab_testing.GPromptWindow", gpw)
        # Capturar los valores pasados al primer CTkComboBox
        ctk_combo = MagicMock()
        monkeypatch.setattr("modules.ab_testing.ctk.CTkComboBox", ctk_combo)
        for name in ["CTkLabel", "CTkFrame", "CTkSlider", "CTkButton",
                    "CTkFont", "IntVar"]:
            monkeypatch.setattr(f"modules.ab_testing.ctk.{name}", MagicMock())
        h._cmd_comparar_modelos()
        # Algún combo debe haberse creado con la lista de modelos de imagen
        assert ctk_combo.called
        # Primer combo: values=[lista de imagen]
        primer_call = ctk_combo.call_args_list[0]
        valores = primer_call.kwargs.get("values", [])
        # No debería haber modelos típicos de vídeo
        modelos_video = ["Kling 3.0", "Veo 3.1", "Seedance 2.0"]
        for mv in modelos_video:
            assert mv not in valores, f"{mv} no debería estar en lista de imagen"

    def test_modo_video_sugiere_modelos_de_video(self, monkeypatch):
        h = _host(txt_idea=_txt("una idea suficientemente larga"),
                  modo_var=_var("video"))
        gpw = MagicMock()
        monkeypatch.setattr("modules.ab_testing.GPromptWindow", gpw)
        ctk_combo = MagicMock()
        monkeypatch.setattr("modules.ab_testing.ctk.CTkComboBox", ctk_combo)
        for name in ["CTkLabel", "CTkFrame", "CTkSlider", "CTkButton",
                    "CTkFont", "IntVar"]:
            monkeypatch.setattr(f"modules.ab_testing.ctk.{name}", MagicMock())
        h._cmd_comparar_modelos()
        primer_call = ctk_combo.call_args_list[0]
        valores = primer_call.kwargs.get("values", [])
        # No debería haber modelos típicos de imagen
        modelos_imagen = ["FLUX.1 [dev]", "Z Image Turbo", "Nano Banana Pro Image"]
        for mi in modelos_imagen:
            assert mi not in valores, f"{mi} no debería estar en lista de vídeo"

    def test_modo_audio_sugiere_modelos_de_audio(self, monkeypatch):
        h = _host(txt_idea=_txt("una idea suficientemente larga"),
                  modo_var=_var("audio"))
        gpw = MagicMock()
        monkeypatch.setattr("modules.ab_testing.GPromptWindow", gpw)
        ctk_combo = MagicMock()
        monkeypatch.setattr("modules.ab_testing.ctk.CTkComboBox", ctk_combo)
        for name in ["CTkLabel", "CTkFrame", "CTkSlider", "CTkButton",
                    "CTkFont", "IntVar"]:
            monkeypatch.setattr(f"modules.ab_testing.ctk.{name}", MagicMock())
        h._cmd_comparar_modelos()
        primer_call = ctk_combo.call_args_list[0]
        valores = primer_call.kwargs.get("values", [])
        # Debe tener al menos Suno o algún modelo de audio
        nombres = " ".join(valores).lower()
        assert "suno" in nombres or "minimax" in nombres or len(valores) > 0
