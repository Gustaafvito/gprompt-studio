"""Tests de la bienvenida para usuarios nuevos (modules/bienvenida.py).

Se dispara cuando NO hay ninguna API key configurada: sin "cerebro" la app no
puede generar nada, y antes nadie se lo decía a quien entraba por primera vez.
"""
from unittest.mock import MagicMock

import pytest

from modules import bienvenida


class TestHayAlgunCerebro:

    def test_true_si_algun_proveedor_tiene_key(self, monkeypatch):
        monkeypatch.setattr("api_clients.cargar_api_key",
                            lambda pid: "sk-x" if pid == "groq" else "")
        assert bienvenida.hay_algun_cerebro() is True

    def test_false_si_ninguno_tiene_key(self, monkeypatch):
        monkeypatch.setattr("api_clients.cargar_api_key", lambda pid: "")
        assert bienvenida.hay_algun_cerebro() is False

    def test_ante_un_fallo_asume_que_si_hay(self, monkeypatch):
        """Mejor no abrir la bienvenida que abrírsela a quien ya la configuró."""
        def _boom(_pid):
            raise RuntimeError("keyring caído")
        monkeypatch.setattr("api_clients.cargar_api_key", _boom)
        assert bienvenida.hay_algun_cerebro() is True


class TestDisparo:

    def test_no_molesta_si_ya_hay_cerebro(self, monkeypatch):
        monkeypatch.setattr(bienvenida, "hay_algun_cerebro", lambda: True)
        app = MagicMock()
        bienvenida.mostrar_si_hace_falta(app)
        app.after.assert_not_called()

    def test_se_programa_si_no_hay_cerebro(self, monkeypatch):
        monkeypatch.setattr(bienvenida, "hay_algun_cerebro", lambda: False)
        app = MagicMock()
        bienvenida.mostrar_si_hace_falta(app, retardo_ms=123)
        app.after.assert_called_once()
        assert app.after.call_args[0][0] == 123

    def test_un_fallo_al_programar_no_rompe_el_arranque(self, monkeypatch):
        monkeypatch.setattr(bienvenida, "hay_algun_cerebro", lambda: False)
        app = MagicMock()
        app.after.side_effect = RuntimeError("ventana no lista")
        bienvenida.mostrar_si_hace_falta(app)  # no debe lanzar


class TestContenido:

    def test_los_gratis_son_proveedores_reales(self):
        from api_clients import LLM_PROVIDERS
        for pid, _motivo in bienvenida.PROVEEDORES_GRATIS:
            assert pid in LLM_PROVIDERS, pid

    def test_los_gratis_tienen_url_para_sacar_la_key(self):
        for pid, _motivo in bienvenida.PROVEEDORES_GRATIS:
            _nombre, url = bienvenida._info_proveedor(pid)
            # Ollama es local: se instala, no se pide key en una web.
            if pid != "ollama":
                assert url.startswith("http"), pid

    def test_ningun_gratis_es_de_pago(self):
        from api_clients import LLM_PROVIDERS
        for pid, _motivo in bienvenida.PROVEEDORES_GRATIS:
            assert not LLM_PROVIDERS[pid].get("is_paid"), pid

    def test_hay_cinco_pasos_basicos(self):
        assert len(bienvenida.PASOS_BASICOS) == 5
        assert all(len(p) == 2 and p[0] and p[1]
                   for p in bienvenida.PASOS_BASICOS)
