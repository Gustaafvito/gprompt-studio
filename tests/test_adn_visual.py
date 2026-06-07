"""Tests para AdnVisualService (modules/adn_visual.py).

Cobertura ligera: guardas de comandos sin abrir ventanas Tk reales y
verificación de mensajes de estado. Toda la UI se mockea con MagicMock.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.adn_visual import AdnVisualService


def _host(**overrides):
    app = SimpleNamespace()
    defaults = dict(
        imagen_cargada=None,
        store=SimpleNamespace(
            cargar_preferencias=lambda: {"adns_guardados": []},
            guardar_preferencias=lambda _p: None,
        ),
        vision=SimpleNamespace(analizar_adn=lambda *a, **k: ({}, "stub")),
        txt_idea=SimpleNamespace(
            get=lambda *_a, **_k: "",
            delete=lambda *_a, **_k: None,
            insert=lambda *_a, **_k: None,
        ),
        after=lambda *a, **k: None,
    )
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(app, k, v)
    app.dialogs = SimpleNamespace(
        set_estado=MagicMock(),
        toggle_botones=MagicMock(),
    )
    return AdnVisualService(app)


# ─────────────────────── _cmd_adn_visual ──────────────────────────────


class TestCmdAdnVisual:

    def test_sin_imagen_cargada_muestra_warning(self):
        h = _host(imagen_cargada=None)
        h._cmd_adn_visual()
        h.app.dialogs.set_estado.assert_called_once()
        args = h.app.dialogs.set_estado.call_args[0]
        assert "imagen" in args[0].lower()

    def test_imagen_falsy_string_vacio_tambien_warns(self):
        h = _host(imagen_cargada="")
        h._cmd_adn_visual()
        h.app.dialogs.set_estado.assert_called_once()

    def test_con_imagen_lanza_thread_y_pone_estado_extrayendo(self, monkeypatch):
        # Mock threading.Thread para no lanzar realmente
        spy_thread = MagicMock()
        monkeypatch.setattr("modules.adn_visual.threading.Thread", spy_thread)
        h = _host(imagen_cargada=object())
        h._cmd_adn_visual()
        # Primer set_estado: "extrayendo"
        called_msgs = [c.args[0] for c in h.app.dialogs.set_estado.call_args_list]
        assert any("Extrayendo" in m or "🧬" in m for m in called_msgs)
        h.app.dialogs.toggle_botones.assert_called_with(False)
        spy_thread.assert_called_once()


# ─────────────────────── _cmd_ver_biblioteca_adn ──────────────────────


class TestCmdVerBibliotecaAdn:

    def test_abre_ventana_con_lista_vacia(self, monkeypatch):
        """Sin ADNs guardados — la ventana sigue abriéndose."""
        gpw = MagicMock()
        monkeypatch.setattr("modules.adn_visual.GPromptWindow", gpw)
        for name in [
            "CTkFrame", "CTkLabel", "CTkFont", "CTkEntry", "CTkButton",
            "CTkScrollableFrame", "StringVar",
        ]:
            monkeypatch.setattr(f"modules.adn_visual.ctk.{name}", MagicMock())
        monkeypatch.setattr("modules.adn_visual.ctk.get_appearance_mode",
                            lambda: "Dark")
        h = _host()
        h._cmd_ver_biblioteca_adn()
        gpw.assert_called_once()

    def test_lee_adns_desde_store(self, monkeypatch):
        """La biblioteca consulta cargar_preferencias() al menos una vez
        al abrir la ventana."""
        gpw = MagicMock()
        monkeypatch.setattr("modules.adn_visual.GPromptWindow", gpw)
        for name in [
            "CTkFrame", "CTkLabel", "CTkFont", "CTkEntry", "CTkButton",
            "CTkScrollableFrame", "StringVar",
        ]:
            monkeypatch.setattr(f"modules.adn_visual.ctk.{name}", MagicMock())
        monkeypatch.setattr("modules.adn_visual.ctk.get_appearance_mode",
                            lambda: "Dark")
        spy_load = MagicMock(return_value={"adns_guardados": []})
        store = SimpleNamespace(
            cargar_preferencias=spy_load,
            guardar_preferencias=lambda _p: None,
        )
        h = _host(store=store)
        h._cmd_ver_biblioteca_adn()
        assert spy_load.call_count >= 1
