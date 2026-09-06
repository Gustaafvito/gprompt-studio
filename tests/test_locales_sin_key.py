"""LM Studio y Ollama no llevan API key: no se les puede pedir una.

Reportado por el usuario el 06-sep-2026 con captura: en el desplegable de
cerebros, LM Studio salía con 🔒 igual que los de pago, y al pulsarlo se abría
el wizard ofreciendo introducir una API key que no existe. Ollama salía con ✅
solo porque estaba arrancado en ese momento.

Lo que les falta a los locales no es una key, es estar ABIERTOS con un modelo
cargado — `disponible()` de ambos consulta su servidor local. Así que el icono
pasa a 💤 y el mensaje explica qué hacer.
"""
import inspect

import api_clients
from modules import core, ui_builders


class TestElIconoDistingueLosCasos:

    def test_hay_un_icono_propio_para_los_locales(self):
        fuente = inspect.getsource(ui_builders.UIBuildersService)
        assert "💤" in fuente, "un local apagado no es lo mismo que uno sin key"

    def test_el_icono_depende_de_si_es_local(self):
        fuente = inspect.getsource(ui_builders.UIBuildersService)
        bloque = fuente[fuente.find("_label_con_estado"):][:900]
        assert "PROVEEDORES_LOCALES" in bloque


class TestNoSePideKeyAUnLocal:

    def test_el_handler_corta_antes_del_wizard(self):
        fuente = inspect.getsource(core.CoreMixin) if hasattr(core, "CoreMixin") \
            else inspect.getsource(core)
        i = fuente.find("no tiene API key")
        assert i != -1, "no encuentro la rama del wizard"
        antes = fuente[max(0, i - 900):i]
        assert "PROVEEDORES_LOCALES" in antes, \
            "los locales deben salir por otra rama ANTES de abrir el wizard"

    def test_el_mensaje_dice_que_no_hace_falta_key(self):
        fuente = inspect.getsource(core.CoreMixin) if hasattr(core, "CoreMixin") \
            else inspect.getsource(core)
        assert "no necesita API key" in fuente


class TestLosDosLocalesEstanDeclarados:

    def test_lm_studio_y_ollama_son_locales(self):
        assert "lm_studio" in api_clients.PROVEEDORES_LOCALES
        assert "ollama" in api_clients.PROVEEDORES_LOCALES

    def test_ninguno_es_de_pago(self):
        for pid in api_clients.PROVEEDORES_LOCALES:
            assert api_clients.LLM_PROVIDERS[pid].get("is_paid") is not True
