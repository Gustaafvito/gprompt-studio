"""Tests de los helpers puros de scoring/optimización de tools_analysis.py.

Cubren la lógica extraída en sesión 19 (sin UI):
- color_para_score
- construir_peticion_scoring / construir_peticion_mejora
- parsear_scoring
- ejecutar_loop_optimizacion (el bucle del optimizador)
"""
import pytest

from modules.tools_analysis import (
    asegurar_etiquetas_prompt,
    color_para_score,
    construir_peticion_mejora,
    construir_peticion_scoring,
    ejecutar_loop_optimizacion,
    parsear_scoring,
)

# ── color_para_score ──────────────────────────────────────────────

class TestColorParaScore:
    def test_verde_desde_80_pct(self):
        assert color_para_score(80, 100) == "#2ecc71"
        assert color_para_score(20, 25) == "#2ecc71"
        assert color_para_score(100, 100) == "#2ecc71"

    def test_amarillo_entre_50_y_79_pct(self):
        assert color_para_score(50, 100) == "#f39c12"
        assert color_para_score(79, 100) == "#f39c12"
        assert color_para_score(13, 25) == "#f39c12"

    def test_rojo_bajo_50_pct(self):
        assert color_para_score(49, 100) == "#e74c3c"
        assert color_para_score(0, 100) == "#e74c3c"

    def test_maximo_cero_o_negativo_devuelve_gris(self):
        assert color_para_score(10, 0) == "#888888"
        assert color_para_score(10, -5) == "#888888"


# ── construir_peticion_scoring ────────────────────────────────────

class TestConstruirPeticionScoring:
    def test_incluye_el_prompt(self):
        peticion = construir_peticion_scoring("un gato astronauta")
        assert "un gato astronauta" in peticion

    def test_incluye_etiquetas_parseables(self):
        peticion = construir_peticion_scoring("x")
        for etiqueta in ("TOTAL: X/100", "✅ PUNTOS FUERTES",
                         "⚠️ PUNTOS DÉBILES", "💡 SUGERENCIA"):
            assert etiqueta in peticion


# ── parsear_scoring ───────────────────────────────────────────────

RESPUESTA_COMPLETA = """PUNTUACIÓN (0-100):
- Claridad del sujeto: 20/25
- Detalle de estilo: 15/25
- Composición y cámara: 10/25
- Calidad y atmósfera: 22/25
TOTAL: 67/100

✅ PUNTOS FUERTES:
- Sujeto claro y reconocible
- Atmósfera bien definida

⚠️ PUNTOS DÉBILES:
- Falta especificar la cámara
- Sin tags de calidad

💡 SUGERENCIA:
- Añade "85mm lens, f/1.8" y tags de calidad
"""


class TestParsearScoring:
    def test_respuesta_completa(self):
        r = parsear_scoring(RESPUESTA_COMPLETA)
        assert r["total"] == (67, 100)
        assert len(r["scores_cat"]) == 4
        assert r["scores_cat"][0] == ("Claridad del sujeto", 20, 25)
        assert "Sujeto claro" in r["fuertes"]
        assert "Falta especificar" in r["debiles"]
        assert "85mm lens" in r["sugerencia"]

    def test_sin_total(self):
        r = parsear_scoring("- Claridad del sujeto: 20/25\nsin total aquí")
        assert r["total"] is None
        assert len(r["scores_cat"]) == 1

    def test_total_case_insensitive(self):
        assert parsear_scoring("total: 55/100")["total"] == (55, 100)

    def test_filtra_maximos_invalidos(self):
        # "1/2" y "3/7" no son máximos de scoring válidos → se ignoran
        r = parsear_scoring("- usa ratio: 1/2\n- otra cosa: 3/7\n- Detalle: 18/25")
        assert r["scores_cat"] == [("Detalle", 18, 25)]

    def test_filtra_valor_mayor_que_maximo(self):
        r = parsear_scoring("- Detalle: 30/25")
        assert r["scores_cat"] == []

    def test_respuesta_vacia(self):
        r = parsear_scoring("")
        assert r["total"] is None
        assert r["scores_cat"] == []
        assert r["fuertes"] == ""
        assert r["debiles"] == ""
        assert r["sugerencia"] == ""

    def test_secciones_sin_marcadores_posteriores(self):
        r = parsear_scoring("💡 SUGERENCIA:\n- mejora la luz")
        assert "mejora la luz" in r["sugerencia"]


# ── construir_peticion_mejora ─────────────────────────────────────

class TestConstruirPeticionMejora:
    def test_incluye_el_prompt(self):
        p = construir_peticion_mejora("gato astronauta")
        assert "gato astronauta" in p

    def test_sin_feedback_no_inyecta_secciones(self):
        p = construir_peticion_mejora("x")
        assert "PUNTOS DÉBILES DETECTADOS" not in p
        assert "SUGERENCIAS A APLICAR" not in p

    def test_con_debiles_los_inyecta(self):
        p = construir_peticion_mejora("x", debiles="- falta cámara")
        assert "PUNTOS DÉBILES DETECTADOS" in p
        assert "falta cámara" in p

    def test_con_sugerencia_la_inyecta(self):
        p = construir_peticion_mejora("x", sugerencia="- añade 85mm")
        assert "SUGERENCIAS A APLICAR" in p
        assert "añade 85mm" in p

    def test_pide_solo_el_prompt(self):
        p = construir_peticion_mejora("x")
        assert "SOLO el prompt mejorado" in p

    def test_exige_formato_si_original_tiene_etiquetas(self):
        p = construir_peticion_mejora("POSITIVE PROMPT:\ngato\nNEGATIVE PROMPT:\nblurry")
        assert "FORMATO DE SALIDA OBLIGATORIO" in p

    def test_no_exige_formato_sin_etiquetas(self):
        p = construir_peticion_mejora("un gato astronauta")
        assert "FORMATO DE SALIDA OBLIGATORIO" not in p


# ── asegurar_etiquetas_prompt ─────────────────────────────────────

class TestAsegurarEtiquetasPrompt:
    ORIGINAL = "POSITIVE PROMPT:\n(masterpiece), gato\nNEGATIVE PROMPT:\nblurry"

    def test_reconstruye_etiqueta_perdida(self):
        mejorado = "(masterpiece, raw photo), gato épico\nNEGATIVE PROMPT:\nblurry"
        r = asegurar_etiquetas_prompt(self.ORIGINAL, mejorado)
        assert r.startswith("POSITIVE PROMPT:\n")
        assert "gato épico" in r

    def test_no_toca_si_etiqueta_presente(self):
        mejorado = "POSITIVE PROMPT:\ngato épico\nNEGATIVE PROMPT:\nblurry"
        assert asegurar_etiquetas_prompt(self.ORIGINAL, mejorado) == mejorado

    def test_no_toca_si_original_sin_etiquetas(self):
        # Prompt natural sin etiquetas (GPT Image, etc.) → no inventar etiqueta
        r = asegurar_etiquetas_prompt("un gato", "un gato épico")
        assert r == "un gato épico"

    def test_case_insensitive(self):
        mejorado = "positive prompt: gato épico"
        assert asegurar_etiquetas_prompt(self.ORIGINAL, mejorado) == mejorado

    def test_mejorado_vacio_se_devuelve_tal_cual(self):
        assert asegurar_etiquetas_prompt(self.ORIGINAL, "") == ""


# ── ejecutar_loop_optimizacion ────────────────────────────────────

def _puntuar_secuencia(scores):
    """Crea un `puntuar` falso que devuelve scores en orden de llamada."""
    llamadas = []

    def puntuar(texto):
        idx = len(llamadas)
        llamadas.append(texto)
        score = scores[idx] if idx < len(scores) else scores[-1]
        return score, "- débil", "- sugerencia"

    puntuar.llamadas = llamadas
    return puntuar


def _mejorar_simple(texto, debiles, sugerencia):
    return texto + "+"


class TestEjecutarLoopOptimizacion:
    def test_objetivo_alcanzado_de_entrada_no_itera(self):
        puntuar = _puntuar_secuencia([90])
        r = ejecutar_loop_optimizacion("base", puntuar, _mejorar_simple,
                                       score_objetivo=85, max_iteraciones=3)
        assert r["alcanzado"] is True
        assert r["iteraciones"] == 0
        assert r["mejor"]["texto"] == "base"
        assert r["mejor"]["score"] == 90
        assert len(puntuar.llamadas) == 1  # solo el inicial

    def test_mejora_hasta_alcanzar_objetivo(self):
        puntuar = _puntuar_secuencia([60, 75, 88])
        r = ejecutar_loop_optimizacion("base", puntuar, _mejorar_simple,
                                       score_objetivo=85, max_iteraciones=5)
        assert r["alcanzado"] is True
        assert r["iteraciones"] == 2
        assert r["mejor"]["score"] == 88
        assert r["mejor"]["texto"] == "base++"
        assert [h["score"] for h in r["historial"]] == [60, 75, 88]

    def test_respeta_max_iteraciones(self):
        puntuar = _puntuar_secuencia([50, 55, 60, 65, 70])
        r = ejecutar_loop_optimizacion("base", puntuar, _mejorar_simple,
                                       score_objetivo=95, max_iteraciones=3)
        assert r["alcanzado"] is False
        assert r["iteraciones"] == 3
        assert r["mejor"]["score"] == 65  # scores[3] = iteración 3

    def test_conserva_la_mejor_si_el_score_baja(self):
        # La iteración 1 sube a 80, la 2 baja a 70 → mejor sigue siendo 80
        puntuar = _puntuar_secuencia([60, 80, 70])
        r = ejecutar_loop_optimizacion("base", puntuar, _mejorar_simple,
                                       score_objetivo=95, max_iteraciones=2)
        assert r["mejor"]["score"] == 80
        assert r["mejor"]["iteracion"] == 1
        assert r["mejor"]["texto"] == "base+"

    def test_score_inicial_no_parseable_devuelve_error(self):
        def puntuar(texto):
            return None, "", ""
        r = ejecutar_loop_optimizacion("base", puntuar, _mejorar_simple)
        assert "error" in r
        assert r["mejor"] is None
        assert r["alcanzado"] is False

    def test_score_no_parseable_a_mitad_para_y_conserva_mejor(self):
        puntuar = _puntuar_secuencia([60, None])
        r = ejecutar_loop_optimizacion("base", puntuar, _mejorar_simple,
                                       score_objetivo=95, max_iteraciones=3)
        assert "error" not in r
        assert r["mejor"]["score"] == 60
        assert r["iteraciones"] == 0  # la mejora fallida no cuenta
        assert len(r["historial"]) == 1

    def test_mejora_vacia_para_el_bucle(self):
        puntuar = _puntuar_secuencia([60])

        def mejorar_vacio(texto, debiles, sugerencia):
            return "   "
        r = ejecutar_loop_optimizacion("base", puntuar, mejorar_vacio,
                                       score_objetivo=95, max_iteraciones=3)
        assert r["iteraciones"] == 0
        assert r["mejor"]["texto"] == "base"

    def test_on_progreso_recibe_cada_iteracion(self):
        eventos = []
        puntuar = _puntuar_secuencia([60, 75, 88])
        ejecutar_loop_optimizacion("base", puntuar, _mejorar_simple,
                                   score_objetivo=85, max_iteraciones=5,
                                   on_progreso=lambda i, s, t: eventos.append((i, s)))
        assert eventos == [(0, 60), (1, 75), (2, 88)]

    def test_feedback_del_scoring_llega_a_mejorar(self):
        recibido = {}

        def puntuar(texto):
            return 60, "- falta luz", "- añade 85mm"

        def mejorar(texto, debiles, sugerencia):
            recibido["debiles"] = debiles
            recibido["sugerencia"] = sugerencia
            return texto + "+"

        ejecutar_loop_optimizacion("base", puntuar, mejorar,
                                   score_objetivo=95, max_iteraciones=1)
        assert recibido["debiles"] == "- falta luz"
        assert recibido["sugerencia"] == "- añade 85mm"

    def test_historial_incluye_iteracion_cero(self):
        puntuar = _puntuar_secuencia([88])
        r = ejecutar_loop_optimizacion("base", puntuar, _mejorar_simple,
                                       score_objetivo=85)
        assert r["historial"][0] == {"iteracion": 0, "score": 88, "texto": "base"}
