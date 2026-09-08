"""Probar una key ya no depende de una lista escrita a mano.

Historial de este mismo botón, que ha declarado inválida una key BUENA tres
veces seguidas:

  07-sep-2026  Los modelos de prueba estaban a fuego en app.py y TRES de los
               cinco apuntaban a modelos muertos (groq a llama-3.3-70b-
               versatile, openrouter a un ":free" retirado, gemini a
               2.0-flash-exp). Se cambió por `model_default`.
  08-sep-2026  `model_default` resultó ser OTRA lista escrita a mano, y el
               mismo día se le murieron CUATRO: openrouter
               (minimax-m3:free), xai (grok-3), openai (gpt-5.6, que ni
               existe) y groq antes.

La raíz es siempre la misma: cualquier nombre de modelo guardado a mano se
pudre. Así que ahora se le pregunta al proveedor cuál sirve AHORA —
`modelos_disponibles()` ya depura la lista curada contra el catálogo en
vivo— y `model_default` queda de red de seguridad para cuando no conteste.

Esto cubre además a togetherai y perplexity, cuyas listas NO se han podido
verificar por falta de key y que, con seis de seis podridas en la auditoría
del 08-sep, es probable que también lo estén.
"""
import inspect

import app as _app


class TestElModeloDePruebaSaleDelCatalogoEnVivo:

    def test_el_wizard_consulta_modelos_disponibles(self):
        fuente = inspect.getsource(_app.ArquitectoApp._setup_wizard)
        assert "vivos = modelos_disponibles(" in fuente, (
            "sin preguntar al proveedor se vuelve a probar con un nombre "
            "guardado a mano, que es lo que ha fallado tres veces")

    def test_el_default_sigue_de_respaldo(self):
        fuente = inspect.getsource(_app.ArquitectoApp._setup_wizard)
        assert "model_default" in fuente, (
            "si el catálogo no contesta hay que probar con algo, no con ''")

    def test_ningun_nombre_de_modelo_escrito_a_mano(self):
        # El fallo original: 'gpt-4o-mini', 'llama-3.3-70b-versatile' y demás
        # incrustados en la llamada de prueba.
        fuente = inspect.getsource(_app.ArquitectoApp._setup_wizard)
        for linea in fuente.splitlines():
            if "create(model=" in linea or "generate_content(model=" in linea:
                assert "modelo_test" in linea, (
                    f"modelo a fuego en la prueba de key: {linea.strip()}")

    def test_no_puede_reventar_el_wizard(self):
        # Si el catálogo falla, la prueba de key debe seguir adelante con el
        # default en vez de tirar al usuario de la pantalla de bienvenida.
        fuente = inspect.getsource(_app.ArquitectoApp._setup_wizard)
        # Anclado en la LLAMADA, no en la primera mención (que está en un
        # comentario y hacía pasar el test sin comprobar nada).
        i = fuente.find("vivos = modelos_disponibles(")
        assert i != -1, "no encuentro la llamada al catálogo"
        assert "except" in fuente[i:i + 400], (
            "la consulta del catálogo va sin red: si falla, tira al usuario "
            "de la pantalla de bienvenida")


class TestLosProveedoresSinVerificarEstanMarcados:

    def test_perplexity_y_together_avisan_en_el_codigo(self):
        fuente = inspect.getsource(__import__("api_clients"))
        for pid in ('"perplexity": {', '"togetherai": {'):
            i = fuente.find(pid)
            assert i != -1, pid
            bloque = fuente[i:i + 1400]
            assert "SIN VERIFICAR" in bloque, (
                f"{pid} no se ha podido probar con key real: la lista no "
                f"puede aparentar estar comprobada como las otras nueve")
