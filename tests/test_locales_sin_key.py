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


class TestElWizardNoEnseñaCampoDeKeyALosLocales:
    """Reportado el 07-sep-2026: "en lm studio deberías quitar el sitio para
    poner la api". El usuario había llegado a pegar una key real en Ollama,
    que quedó muerta en el Credential Manager: los dos providers locales
    sobrescriben `api_key` con un literal en su __init__ y tiran lo que se les
    pase, así que el campo solo servía para engañar.
    """

    def _fuente(self):
        from modules import dialogs
        return inspect.getsource(dialogs)

    def test_los_locales_salen_antes_de_crear_el_entry(self):
        fuente = self._fuente()
        i = fuente.find("entries_keys[pid] = ent")
        assert i != -1, "no encuentro el alta del campo de key"
        antes = fuente[max(0, i - 6000):i]
        assert "PROVEEDORES_LOCALES" in antes and "continue" in antes, \
            "un proveedor local debe saltarse el campo de API key"

    def test_el_provider_local_ignora_la_key_que_le_pasen(self):
        for pid, literal in (("lm_studio", "lm-studio"), ("ollama", "ollama")):
            prov = api_clients.get_provider(pid, "sk-una-key-de-verdad")
            assert prov.api_key == literal, \
                f"{pid} descarta la key; el wizard no debe pedirla"

    def test_se_explica_por_que_no_hay_campo(self):
        assert "No necesita API key" in self._fuente(), \
            "quitar el campo sin decir nada deja al usuario sin saber qué hacer"
