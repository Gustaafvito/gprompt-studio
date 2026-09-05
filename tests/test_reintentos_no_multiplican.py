"""Los reintentos del SDK y los del worker NO deben multiplicarse.

El cliente de OpenAI reintenta 2 veces por defecto (3 intentos HTTP) y
DeepSeekWorker.generar() otras 3. Sin desactivar los primeros salen 3x3 = 9
llamadas de hasta LLM_TIMEOUT_S (180s) cada una: 27 MINUTOS mirando
"🎨 Generando..." antes de ver un error.

Medido el 05-sep-2026 persiguiendo por qué un moodboard de 10 no volvía nunca.
El reintento se deja en un único sitio — el worker — que además aplica backoff
y lo deja escrito en el log.
"""
import inspect

import api_clients


class TestClientesSinReintentoPropio:

    def test_el_cliente_openai_se_crea_con_max_retries_0(self):
        fuente = inspect.getsource(api_clients.OpenAICompatibleProvider.__init__)
        assert "max_retries=0" in fuente, \
            "sin esto los reintentos se multiplican con los del worker"

    def test_el_cliente_anthropic_tambien(self):
        fuente = inspect.getsource(api_clients.ClaudeProvider.__init__)
        assert "max_retries=0" in fuente

    def test_el_timeout_sigue_puesto(self):
        """Quitar el reintento no debe llevarse por delante el timeout."""
        fuente = inspect.getsource(api_clients.OpenAICompatibleProvider.__init__)
        assert "timeout=LLM_TIMEOUT_S" in fuente


class TestPeorCasoAcotado:

    def test_la_espera_maxima_no_pasa_de_10_minutos(self):
        """Candado sobre el producto real: intentos x timeout."""
        import workers
        fuente = inspect.getsource(workers.DeepSeekWorker.generar)
        intentos = int(fuente.split("max_reintentos = ")[1].split("\n")[0])
        peor_caso = intentos * api_clients.LLM_TIMEOUT_S
        assert peor_caso <= 600, (
            f"peor caso {peor_caso}s: el usuario no puede esperar tanto "
            f"sin ver un error")
