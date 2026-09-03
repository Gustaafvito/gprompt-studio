"""El prompt no debe arrastrar el ECO de las instrucciones del system prompt.

Los modelos LOCALES (LM Studio, Ollama) y los más flojos tienden a repetir las
reglas que se les dan y a comentar su propio trabajo. Sin filtrar, todo eso
acababa pegado en el prompt que copia el usuario.

Detectado probando LM Studio de punta a punta (sep-2026): al generar con
FLUX.1 [dev] el POSITIVE extraído medía 476 caracteres e incluía
"(No generes NEGATIVE PROMPT — este modelo no lo soporta)" y
"• Limitaciones: Modelo muy pesado...". La app instruía BIEN; el modelo era
el que devolvía las instrucciones dentro del resultado.
"""
from modules.prompt_helpers import (
    extraer_positive_de_texto,
    quitar_eco_instrucciones,
)

# Salida REAL de qwen2.5-32b-instruct en LM Studio (recortada).
SALIDA_REAL = "\n".join([
    "PROMPT: An astronaut on Mars, casting a fishing line into water,",
    "cinematic and serene ambiance with muted color grading.",
    "",
    "(No generes NEGATIVE PROMPT — este modelo no lo soporta)",
    "",
    "• Limitaciones: Modelo muy pesado, tarda más que otros.",
    "• ⚠️ IDIOMA DEL PROMPT: escribe el PROMPT SIEMPRE en INGLÉS.",
    "",
    "Caracteres totales del prompt: 203",
    "",
    "Este prompt se centra en una escena visualmente rica.",
])


class TestSalidaRealDeLMStudio:

    def test_el_prompt_sale_limpio(self):
        res = extraer_positive_de_texto(SALIDA_REAL)
        for basura in ("No generes", "Limitaciones", "IDIOMA",
                       "Caracteres totales", "Este prompt se centra"):
            assert basura not in res, f"se coló: {basura}"

    def test_conserva_el_prompt_de_verdad(self):
        res = extraer_positive_de_texto(SALIDA_REAL)
        assert "astronaut on Mars" in res
        assert "muted color grading" in res

    def test_encoge_lo_suficiente(self):
        """Antes del filtro salían 476 chars; el prompt real son ~120."""
        res = extraer_positive_de_texto(SALIDA_REAL)
        assert len(res) < 250, f"sigue arrastrando eco ({len(res)} chars)"


class TestNoRompeLoBueno:

    def test_prompt_normal_intacto(self):
        txt = ("POSITIVE PROMPT: a cat, masterpiece, (detailed:1.2)\n"
               "NEGATIVE PROMPT: blurry")
        assert extraer_positive_de_texto(txt) == "a cat, masterpiece, (detailed:1.2)"

    def test_prosa_larga_intacta_aunque_suene_parecido(self):
        """Una frase LARGA es prompt aunque mencione palabras de instrucción."""
        largo = ("a cinematic portrait of a woman reading a book about the total "
                 "number of characters engraved on an ancient stone tablet, warm "
                 "light, shallow depth of field, highly detailed textures and a "
                 "carefully composed background that fills the frame nicely")
        assert quitar_eco_instrucciones(largo) == largo

    def test_tags_con_pesos_intactos(self):
        tags = "masterpiece, best quality, 1girl, (rooftop:1.2), (sunset:1.3)"
        assert quitar_eco_instrucciones(tags) == tags


class TestCasosLimite:

    def test_quita_vinetas_de_instruccion(self):
        assert quitar_eco_instrucciones("un gato\n• Limitaciones: pesado") == "un gato"

    def test_texto_vacio(self):
        assert quitar_eco_instrucciones("") == ""

    def test_none_no_rompe(self):
        assert quitar_eco_instrucciones(None) is None

    def test_solo_eco_deja_vacio(self):
        solo = "• Limitaciones: pesado\n⚠️ IDIOMA DEL PROMPT: en inglés"
        assert quitar_eco_instrucciones(solo).strip() == ""
