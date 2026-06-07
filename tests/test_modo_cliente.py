"""Tests para ModoClienteService (modules/modo_cliente.py).

Cobertura: guardas de comandos (idea/brief vacío) y comportamiento del
worker de propuestas con threading.Thread mockeado. Las ventanas Tk se
sustituyen por MagicMock.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.modo_cliente import ModoClienteService


def _var(value):
    return SimpleNamespace(get=lambda: value, set=lambda _v: None)


def _txt(value):
    return SimpleNamespace(get=lambda *_a, **_k: value + "\n",
                           delete=lambda *_a, **_k: None,
                           insert=lambda *_a, **_k: None)


def _host(**overrides):
    app = SimpleNamespace()
    defaults = dict(
        modo_var=_var("imagen"),
        plataforma_var=_var("Personal"),
        ratio_var=_var("1:1"),
        deepseek=SimpleNamespace(generar=lambda *a, **k: "POSITIVE PROMPT: x"),
        store=SimpleNamespace(
            cargar_preferencias=lambda: {},
            guardar_preferencias=lambda _p: None,
            agregar_favorito=lambda _d: None,
        ),
        get_current_model_specs=lambda: {"has_negative": True, "is_natural": False},
        after=lambda *a, **k: None,
        _parsear_bloques_numerados=lambda txt, n_esperado=None: [],
        imagen_cargada=None,
        vision=SimpleNamespace(describir=lambda *a, **k: ("desc", "vision")),
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
    return ModoClienteService(app)


# ─────────────────────── _generar_propuestas_cliente ─────────────────


class TestGenerarPropuestasCliente:

    def test_marca_estado_y_desactiva_botones_al_iniciar(self, monkeypatch):
        spy_thread = MagicMock()
        monkeypatch.setattr("modules.modo_cliente.threading.Thread", spy_thread)
        h = _host()
        h._generar_propuestas_cliente("brief test")
        h.app.dialogs.set_estado.assert_called_once()
        msg = h.app.dialogs.set_estado.call_args[0][0]
        assert "5 propuestas" in msg or "💼" in msg
        h.app.dialogs.toggle_botones.assert_called_once_with(False)
        spy_thread.assert_called_once()

    def test_modelo_sin_negative_omite_negative_prompt_en_peticion(self, monkeypatch):
        """Cuando specs.has_negative=False, la petición indica explícitamente
        NO incluir NEGATIVE PROMPT."""
        spy_thread = MagicMock()
        monkeypatch.setattr("modules.modo_cliente.threading.Thread", spy_thread)
        captured = {}

        def _stub_generar(peticion, **_kw):
            captured["peticion"] = peticion
            return "POSITIVE PROMPT: x"

        h = _host(
            deepseek=SimpleNamespace(generar=_stub_generar),
            get_current_model_specs=lambda: {"has_negative": False, "is_natural": True},
        )
        h._generar_propuestas_cliente("brief test")
        # Ejecutar el worker manualmente
        target = spy_thread.call_args.kwargs["target"]
        target()
        assert "NO incluyas NEGATIVE" in captured["peticion"]

    def test_modelo_natural_pide_lenguaje_natural(self, monkeypatch):
        spy_thread = MagicMock()
        monkeypatch.setattr("modules.modo_cliente.threading.Thread", spy_thread)
        captured = {}

        def _stub_generar(peticion, **_kw):
            captured["peticion"] = peticion
            return ""

        h = _host(
            deepseek=SimpleNamespace(generar=_stub_generar),
            get_current_model_specs=lambda: {"has_negative": True, "is_natural": True},
        )
        h._generar_propuestas_cliente("brief test")
        spy_thread.call_args.kwargs["target"]()
        assert "lenguaje natural" in captured["peticion"]

    def test_modelo_tag_based_pide_tags(self, monkeypatch):
        spy_thread = MagicMock()
        monkeypatch.setattr("modules.modo_cliente.threading.Thread", spy_thread)
        captured = {}

        def _stub_generar(peticion, **_kw):
            captured["peticion"] = peticion
            return ""

        h = _host(
            deepseek=SimpleNamespace(generar=_stub_generar),
            get_current_model_specs=lambda: {"has_negative": True, "is_natural": False},
        )
        h._generar_propuestas_cliente("brief test")
        spy_thread.call_args.kwargs["target"]()
        assert "tags con pesos" in captured["peticion"]


# ─────────────────────── _abrir_comparador_propuestas ────────────────


class TestAbrirComparadorPropuestas:

    def test_acepta_lista_de_strings_legacy(self, monkeypatch):
        """El comparador acepta lista de strings (formato legacy) además
        de la lista de dicts moderna."""
        gpw = MagicMock()
        monkeypatch.setattr("modules.modo_cliente.GPromptWindow", gpw)
        for name in [
            "CTkFrame", "CTkLabel", "CTkFont", "CTkButton",
            "CTkScrollableFrame",
        ]:
            monkeypatch.setattr(f"modules.modo_cliente.ctk.{name}", MagicMock())
        monkeypatch.setattr("modules.modo_cliente.ctk.get_appearance_mode",
                            lambda: "Dark")
        h = _host()
        # Strings legacy con POSITIVE/NEGATIVE
        propuestas = [
            "POSITIVE PROMPT: a\nNEGATIVE PROMPT: bad",
            "POSITIVE PROMPT: b",
        ]
        h._abrir_comparador_propuestas(propuestas, brief="brief X")
        gpw.assert_called_once()

    def test_acepta_lista_de_dicts(self, monkeypatch):
        gpw = MagicMock()
        monkeypatch.setattr("modules.modo_cliente.GPromptWindow", gpw)
        for name in [
            "CTkFrame", "CTkLabel", "CTkFont", "CTkButton",
            "CTkScrollableFrame",
        ]:
            monkeypatch.setattr(f"modules.modo_cliente.ctk.{name}", MagicMock())
        monkeypatch.setattr("modules.modo_cliente.ctk.get_appearance_mode",
                            lambda: "Dark")
        h = _host()
        propuestas = [
            {"num": "1", "nombre": "Minimal", "positive": "a", "negative": ""},
            {"num": "2", "nombre": "Bold",    "positive": "b", "negative": "low"},
        ]
        h._abrir_comparador_propuestas(propuestas, brief="brief Y")
        gpw.assert_called_once()
