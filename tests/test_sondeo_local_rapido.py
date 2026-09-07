"""Cambiar de cerebro no puede congelar la ventana.

Reportado el 06-sep-2026 con captura: el título ponía "G-Prompt Studio v1.0.0
(No responde)" al cambiar de cerebro. Medido sobre la app real, con LM Studio
y Ollama apagados:

    lm_studio.disponible()          4.023 ms   (urlopen prueba IPv6 y luego IPv4)
    ollama.disponible()             2.007 ms
    _refrescar_indicadores_llm()   12.073 ms   ← la ventana, congelada

El desplegable de cerebros pinta un icono ✅/🔒/💤 por proveedor, y para
saberlo pregunta `disponible()` a los catorce. Los dos locales se quedaban
esperando su timeout.

ACTUALIZADO EL 07-SEP-2026 — la causa real era otra. Recortar el timeout a
0.6s tapaba el sintoma y creaba el contrario: con LM Studio ABIERTO y 19
modelos cargados, `/v1/models` tardaba 2,05s y se le declaraba dormido. Medido
en la maquina del usuario:

    http://localhost:1234/v1/models   ->  2019 ms
    http://127.0.0.1:1234/v1/models   ->     1 ms

`localhost` resuelve a ::1 antes que a 127.0.0.1, y ese puerto no rechaza: se
queda colgado hasta agotar el timeout. Arreglado forzando IPv4, y separando
las dos preguntas: "esta encendido" (connect de TCP, milisegundos) de "que
modelos tiene" (HTTP, ya puede esperar).
"""
import time

import api_clients


class TestSondeoLocalAcotado:

    def test_el_sondeo_del_puerto_es_corto(self):
        # Este es el que corre en el hilo de Tk, uno por proveedor.
        assert api_clients.TIMEOUT_SONDEO_LOCAL_S <= 1.0, (
            "el icono del desplegable no puede costar segundos")

    def test_las_urls_locales_no_usan_localhost(self):
        for pid in api_clients.PROVEEDORES_LOCALES:
            url = api_clients.LLM_PROVIDERS[pid].get("base_url", "")
            assert "//localhost:" not in url, (
                f"{pid}: 'localhost' resuelve ::1 primero y cuelga 1s; "
                f"usa 127.0.0.1")

    def test_forzar_ipv4_reescribe_solo_localhost(self):
        f = api_clients._forzar_ipv4
        assert f("http://localhost:1234/v1") == "http://127.0.0.1:1234/v1"
        assert f("http://127.0.0.1:1234/v1") == "http://127.0.0.1:1234/v1"
        assert f("https://api.deepseek.com") == "https://api.deepseek.com"

    def test_un_puerto_muerto_se_detecta_rapido(self):
        t = time.perf_counter()
        assert api_clients._puerto_abierto("http://127.0.0.1:1/v1") is False
        assert time.perf_counter() - t < 1.0

    def test_el_timeout_local_es_menor_que_el_de_generacion(self):
        assert api_clients.TIMEOUT_LOCAL_S < api_clients.LLM_TIMEOUT_S


class TestCacheDeDisponibilidad:

    def test_no_sondea_dos_veces_seguidas(self):
        api_clients._CACHE_LOCAL.clear()
        llamadas = []
        def _consulta():
            llamadas.append(1)
            return ["modelo"]
        api_clients._local_cacheado("prueba", _consulta)
        api_clients._local_cacheado("prueba", _consulta)
        api_clients._local_cacheado("prueba", _consulta)
        assert len(llamadas) == 1, "el refresco se dispara varias veces seguidas"

    def test_un_fallo_no_revienta_y_se_cachea(self):
        api_clients._CACHE_LOCAL.clear()
        llamadas = []
        def _rota():
            llamadas.append(1)
            raise OSError("servidor apagado")
        assert api_clients._local_cacheado("rota", _rota) == []
        assert api_clients._local_cacheado("rota", _rota) == []
        assert len(llamadas) == 1, "un servidor apagado no debe re-sondearse"

    def test_el_ttl_existe_y_es_razonable(self):
        assert 5 <= api_clients._CACHE_LOCAL_TTL_S <= 120


class TestLosLocalesUsanLaCache:

    def test_ollama_y_lm_studio_pasan_por_el_cacheado(self):
        import inspect
        for clase in (api_clients.OllamaProvider, api_clients.LMStudioProvider):
            fuente = inspect.getsource(clase.disponible)
            assert "_local_cacheado" in fuente, clase.__name__


class TestElRefrescoEsBarato:
    """Candado de coste: sondear 14 proveedores no puede costar segundos."""

    def test_sondear_los_locales_cacheados_es_instantaneo(self):
        api_clients._CACHE_LOCAL.clear()
        api_clients._local_cacheado("x", lambda: ["a"])
        t = time.perf_counter()
        for _ in range(100):
            api_clients._local_cacheado("x", lambda: ["a"])
        assert (time.perf_counter() - t) < 0.05
