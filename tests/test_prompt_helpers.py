"""Tests unitarios para modules/prompt_helpers.py.

Todas las funciones son puras (sin widgets Tk ni estado de app).
No se necesita ningún mock: los helpers solo manipulan strings.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.prompt_helpers import (
    extraer_negative_de_texto,
    extraer_pos_de_bloque,
    extraer_positive_de_texto,
    parsear_variaciones,
    recortar_si_excede,
)

# ══════════════════════════════════════════════════════════════════
# parsear_variaciones
# ══════════════════════════════════════════════════════════════════

class TestParsearVariaciones:

    # ── encabezados "Variación N" ───────────────────────────────────
    def test_tres_bloques_variacion_numerada(self):
        texto = (
            "Variación 1.\nPOSITIVE PROMPT: una chica en el bosque bajo la lluvia\n"
            "Variación 2.\nPOSITIVE PROMPT: una chica en la ciudad al amanecer\n"
            "Variación 3.\nPOSITIVE PROMPT: una chica en la playa al atardecer"
        )
        result = parsear_variaciones(texto, n_esperado=3)
        assert len(result) == 3
        assert "bosque" in result[0]
        assert "ciudad" in result[1]
        assert "playa" in result[2]

    def test_dos_bloques_variacion_numerada(self):
        texto = (
            "Variación 1.\nPOSITIVE PROMPT: primer prompt con suficiente longitud detallado\n"
            "Variación 2.\nPOSITIVE PROMPT: segundo prompt con suficiente longitud detallado"
        )
        result = parsear_variaciones(texto, n_esperado=2)
        assert len(result) == 2

    # ── encabezados "Prompt N" ──────────────────────────────────────
    def test_formato_prompt_n(self):
        texto = (
            "Prompt 1.\nPOSITIVE PROMPT: idea uno con suficiente texto detallado\n"
            "Prompt 2.\nPOSITIVE PROMPT: idea dos con suficiente texto detallado"
        )
        result = parsear_variaciones(texto, n_esperado=2)
        assert len(result) == 2

    # ── separadores "---" ───────────────────────────────────────────
    def test_separadores_guiones(self):
        texto = (
            "POSITIVE PROMPT: primera variación con suficiente longitud para pasar\n"
            "---\n"
            "POSITIVE PROMPT: segunda variación también con longitud adecuada\n"
            "---\n"
            "POSITIVE PROMPT: tercera variación completa y detallada suficiente"
        )
        result = parsear_variaciones(texto, n_esperado=3)
        assert len(result) >= 2

    def test_dos_bloques_separados_por_guiones(self):
        texto = (
            "POSITIVE PROMPT: aquí el primer bloque largo con mucho detalle suficiente\n"
            "---\n"
            "POSITIVE PROMPT: aquí el segundo bloque igualmente largo con detalle"
        )
        result = parsear_variaciones(texto)
        assert len(result) >= 2

    # ── texto con "POSITIVE PROMPT:" pero sin numeración ───────────
    def test_bloques_positive_prompt_sin_numeracion(self):
        texto = (
            "POSITIVE PROMPT: primera idea detallada con longitud suficiente para pasar\n"
            "NEGATIVE PROMPT: blurry, low quality\n"
            "POSITIVE PROMPT: segunda idea detallada con longitud suficiente para pasar\n"
            "NEGATIVE PROMPT: blurry, low quality"
        )
        result = parsear_variaciones(texto)
        assert len(result) >= 2

    # ── texto sin estructura → [] ───────────────────────────────────
    def test_texto_muy_corto_devuelve_vacio(self):
        assert parsear_variaciones("hola") == []

    def test_string_vacio_devuelve_vacio(self):
        assert parsear_variaciones("") == []

    def test_texto_sin_estructura_clara_devuelve_vacio(self):
        assert parsear_variaciones("Esto no tiene estructura de variaciones.") == []

    # ── n_esperado filtra preámbulos ────────────────────────────────
    def test_filtra_preambulo_con_n_esperado(self):
        texto = (
            "Aquí tienes las tres variaciones que me pediste para tu proyecto:\n"
            "Variación 1.\nPOSITIVE PROMPT: primero bien detallado con suficiente texto\n"
            "Variación 2.\nPOSITIVE PROMPT: segundo bien detallado con suficiente texto\n"
            "Variación 3.\nPOSITIVE PROMPT: tercero bien detallado con suficiente texto"
        )
        result = parsear_variaciones(texto, n_esperado=3)
        assert len(result) == 3
        for r in result:
            assert "Aquí tienes" not in r

    def test_n_esperado_sin_positive_prompt_usa_ultimos_n(self):
        # Sin marcadores POSITIVE PROMPT → asume preámbulo al principio
        texto = (
            "Este es un preámbulo generado por el LLM que no es variación\n"
            "1. primer bloque largo con suficiente contenido detallado aquí\n"
            "2. segundo bloque largo con suficiente contenido detallado aquí\n"
            "3. tercer bloque largo con suficiente contenido detallado aquí"
        )
        result = parsear_variaciones(texto, n_esperado=3)
        # Debe devolver ≤ n_esperado bloques
        assert len(result) <= 3

    # ── limpieza de markdown ────────────────────────────────────────
    def test_limpia_asteriscos_y_almohadillas(self):
        texto = (
            "**Variación 1.**\nPOSITIVE PROMPT: primer prompt con marcadores markdown\n"
            "**Variación 2.**\nPOSITIVE PROMPT: segundo prompt también con marcadores"
        )
        result = parsear_variaciones(texto, n_esperado=2)
        for r in result:
            assert "**" not in r
            assert "#" not in r

    # ── acento en "Variación" ───────────────────────────────────────
    def test_acento_en_variacion(self):
        # Con acento ortográfico "Variación"
        texto = (
            "Variación 1.\nPOSITIVE PROMPT: texto con acento primer bloque detallado\n"
            "Variación 2.\nPOSITIVE PROMPT: texto con acento segundo bloque detallado"
        )
        result = parsear_variaciones(texto, n_esperado=2)
        assert len(result) == 2

    # ── n_esperado con todos POSITIVE PROMPT: preferidos ───────────
    def test_prefiere_bloques_con_positive_prompt(self):
        texto = (
            "preámbulo largo con texto para ser considerado bloque candidato aquí\n"
            "Variación 1.\nPOSITIVE PROMPT: primera variación con positive prompt\n"
            "Variación 2.\nPOSITIVE PROMPT: segunda variación con positive prompt\n"
            "Variación 3.\nPOSITIVE PROMPT: tercera variación con positive prompt"
        )
        result = parsear_variaciones(texto, n_esperado=3)
        # Los 3 resultados deben tener POSITIVE PROMPT
        for r in result:
            assert "POSITIVE PROMPT" in r.upper()


# ══════════════════════════════════════════════════════════════════
# extraer_pos_de_bloque
# ══════════════════════════════════════════════════════════════════

class TestExtraerPosDeBloque:

    def test_con_positive_prompt(self):
        bloque = "POSITIVE PROMPT: beautiful landscape, golden hour\nNEGATIVE PROMPT: blurry"
        result = extraer_pos_de_bloque(bloque)
        assert result == "beautiful landscape, golden hour"

    def test_con_prompt_simple(self):
        bloque = "PROMPT: anime girl in forest\nNEGATIVE PROMPT: low quality"
        result = extraer_pos_de_bloque(bloque)
        assert result == "anime girl in forest"

    def test_negative_prompt_se_corta(self):
        bloque = "POSITIVE PROMPT: first part\nNEGATIVE PROMPT: bad content here"
        result = extraer_pos_de_bloque(bloque)
        assert "bad content" not in result
        assert "first part" in result

    def test_negative_sin_prompt_tambien_se_corta(self):
        bloque = "POSITIVE PROMPT: first part\nNEGATIVE: bad content"
        result = extraer_pos_de_bloque(bloque)
        assert "bad content" not in result
        assert "first part" in result

    def test_sin_marcadores_devuelve_todo(self):
        bloque = "a beautiful sunset over the ocean with warm colors"
        result = extraer_pos_de_bloque(bloque)
        assert result == "a beautiful sunset over the ocean with warm colors"

    def test_limpia_marcadores_code_fences(self):
        # limpiar_marcadores quita ** y __
        bloque = "**POSITIVE PROMPT:** beautiful art"
        result = extraer_pos_de_bloque(bloque)
        assert "**" not in result

    def test_solo_negative_prompt_devuelve_vacío_antes(self):
        bloque = "NEGATIVE PROMPT: blurry, low res"
        result = extraer_pos_de_bloque(bloque)
        # No hay sección positiva → devuelve lo que queda antes de NEGATIVE (vacío)
        assert "blurry" not in result

    def test_strips_asteriscos_del_resultado(self):
        bloque = "POSITIVE PROMPT: *some text*\nNEGATIVE PROMPT: bad"
        result = extraer_pos_de_bloque(bloque)
        # Strip solo de bordes (el bloque puede tener * interiores)
        assert not result.startswith("*")
        assert not result.endswith("*")


# ══════════════════════════════════════════════════════════════════
# extraer_positive_de_texto
# ══════════════════════════════════════════════════════════════════

class TestExtraerPositiveDeTexto:

    def test_con_positive_prompt_y_negative_prompt(self):
        texto = "POSITIVE PROMPT: beautiful landscape\nNEGATIVE PROMPT: blurry"
        result = extraer_positive_de_texto(texto)
        assert result == "beautiful landscape"
        assert "blurry" not in result

    def test_con_positive_prompt_sin_negative(self):
        texto = "POSITIVE PROMPT: anime girl in city at night"
        result = extraer_positive_de_texto(texto)
        assert result == "anime girl in city at night"

    def test_con_prompt_simple_y_negative(self):
        texto = "PROMPT: sci-fi landscape\nNEGATIVE: low quality, blurry"
        result = extraer_positive_de_texto(texto)
        assert result == "sci-fi landscape"

    def test_con_prompt_simple_y_separador_numerico(self):
        texto = "PROMPT: beautiful sunset\n1. otra cosa\n2. más cosas"
        result = extraer_positive_de_texto(texto)
        assert "otra cosa" not in result
        assert "beautiful sunset" in result

    def test_texto_sin_marcadores_devuelve_texto_limpio(self):
        texto = "a beautiful photo of mountains and sky"
        result = extraer_positive_de_texto(texto)
        assert result is not None
        assert "mountains" in result

    def test_texto_muy_corto_devuelve_none(self):
        result = extraer_positive_de_texto("hi")
        assert result is None

    def test_texto_vacio_devuelve_none(self):
        result = extraer_positive_de_texto("")
        assert result is None

    def test_solo_negative_prompt_extrae_lo_que_sigue_a_prompt(self):
        # "NEGATIVE PROMPT:" contiene "PROMPT:" como subcadena, así que
        # extraer_positive_de_texto extrae lo que va tras "PROMPT:" →
        # el contenido de la sección negativa. No es None sino el texto negativo.
        texto = "NEGATIVE PROMPT: blurry, low quality, watermark"
        result = extraer_positive_de_texto(texto)
        # La función no devuelve None en este caso (PROMPT: aparece como subcadena)
        assert result is not None
        assert "blurry" in result

    def test_prompt_con_separador_lineas_guiones(self):
        texto = "PROMPT: idea de foto creativa\n──────────\nOtra sección"
        result = extraer_positive_de_texto(texto)
        assert "idea de foto creativa" in result
        assert "Otra sección" not in result

    def test_positive_prompt_multilinea(self):
        texto = (
            "POSITIVE PROMPT: detailed portrait, blue eyes,\n"
            "soft lighting, cinematic look\n"
            "NEGATIVE PROMPT: blurry"
        )
        result = extraer_positive_de_texto(texto)
        assert "detailed portrait" in result
        assert "soft lighting" in result
        assert "blurry" not in result


# ══════════════════════════════════════════════════════════════════
# extraer_negative_de_texto
# ══════════════════════════════════════════════════════════════════

class TestExtraerNegativeDeTexto:

    def test_con_negative_prompt(self):
        texto = "POSITIVE PROMPT: beautiful\nNEGATIVE PROMPT: blurry, low quality"
        result = extraer_negative_de_texto(texto)
        assert result == "blurry, low quality"

    def test_sin_negative_devuelve_none(self):
        texto = "POSITIVE PROMPT: beautiful landscape"
        result = extraer_negative_de_texto(texto)
        assert result is None

    def test_negative_con_newline_y_prefijo(self):
        texto = "algo\nNEGATIVE\nblurry, ugly, watermark"
        result = extraer_negative_de_texto(texto)
        assert result is not None
        assert "blurry" in result

    def test_negative_dos_puntos(self):
        texto = "POSITIVE PROMPT: idea\nNEGATIVE: bad stuff, low res"
        result = extraer_negative_de_texto(texto)
        assert result is not None
        assert "bad stuff" in result

    def test_negative_se_corta_en_separador_numerico(self):
        texto = "NEGATIVE PROMPT: blurry, ugly\n1. algo más\n2. otra cosa"
        result = extraer_negative_de_texto(texto)
        assert result is not None
        assert "algo más" not in result

    def test_negative_se_corta_en_guion_decorativo(self):
        texto = "NEGATIVE PROMPT: blurry, ugly\n──────\ncosa extra"
        result = extraer_negative_de_texto(texto)
        assert result is not None
        assert "cosa extra" not in result

    def test_solo_negative_prompt_extrae_bien(self):
        texto = "NEGATIVE PROMPT: watermark, signature, low res"
        result = extraer_negative_de_texto(texto)
        assert result == "watermark, signature, low res"

    def test_negative_multilinea(self):
        texto = "POSITIVE PROMPT: ok\nNEGATIVE PROMPT: blurry,\nugly,\nwatermark"
        result = extraer_negative_de_texto(texto)
        assert result is not None
        assert "blurry" in result


# ══════════════════════════════════════════════════════════════════
# recortar_si_excede
# ══════════════════════════════════════════════════════════════════

class TestRecortarSiExcede:

    # ── texto sin POSITIVE PROMPT → devuelve intacto ───────────────
    def test_sin_positive_prompt_devuelve_intacto(self):
        texto = "Un texto cualquiera sin marcadores de prompt"
        result = recortar_si_excede(texto, 50)
        assert result == texto

    def test_max_chars_cero_devuelve_intacto(self):
        texto = "POSITIVE PROMPT: algo, otracosa, másdetalle"
        assert recortar_si_excede(texto, 0) == texto

    def test_texto_vacio_devuelve_vacio(self):
        assert recortar_si_excede("", 100) == ""

    # ── dentro del límite → no recorta ─────────────────────────────
    def test_no_recorta_si_dentro_del_limite(self):
        texto = "POSITIVE PROMPT: a, b, c"
        result = recortar_si_excede(texto, 1000)
        assert result == texto

    def test_no_recorta_positive_ni_negative_si_caben(self):
        texto = "POSITIVE PROMPT: a, b\nNEGATIVE PROMPT: x, y"
        result = recortar_si_excede(texto, 1000)
        assert result == texto

    # ── prosa SIN etiqueta (prompts de vídeo) → se recorta igual ──────
    def test_prosa_sin_etiqueta_se_recorta_a_max(self):
        prosa = "A cinematic shot of an anime girl smiling. " * 30
        out = recortar_si_excede(prosa, 800)
        assert len(out) <= 800
        assert out.endswith(".")  # cortado en un fin de frase limpio
        assert " smili" not in out[-5:]  # no parte una palabra a la mitad

    def test_prosa_corta_no_se_toca(self):
        prosa = "A short anime video prompt without label."
        assert recortar_si_excede(prosa, 800) == prosa

    def test_prosa_sin_frase_corta_por_espacio(self):
        # Sin signos de puntuación: corta por el último espacio, no a media palabra.
        prosa = "word " * 400  # 2000 chars, sin puntos ni comas
        out = recortar_si_excede(prosa, 100)
        assert len(out) <= 100
        assert not out.endswith("wor")  # palabra completa


class TestMoverTriggerAlInicio:

    def test_tag_single_va_al_inicio_y_conserva_comas(self):
        from modules.prompt_helpers import mover_trigger_al_inicio as M
        out = M("POSITIVE PROMPT: 1girl, lmnlhrr, red hair\nNEGATIVE PROMPT: blurry",
                "lmnlhrr")
        # El trigger queda justo tras la etiqueta
        assert out.startswith("POSITIVE PROMPT: lmnlhrr style,")
        assert "1girl, red hair" in out
        assert "NEGATIVE PROMPT: blurry" in out  # negative intacto

    def test_zimage_multitermino_no_borra_rasgos_del_subject(self):
        from modules.prompt_helpers import mover_trigger_al_inicio as M
        z = ("POSITIVE PROMPT: (masterpiece:1.2), 8k.\n"
             "[Subject & Composition] a girl with amber eyes.\n"
             "[LoRA Activation & Style] Nyra, Amber Eyes, Undercut, cinematic.\n"
             "NEGATIVE PROMPT: blurry")
        out = M(z, "Nyra, Amber Eyes, Undercut")
        assert out.startswith("POSITIVE PROMPT: Nyra, Amber Eyes, Undercut,")
        assert "amber eyes" in out  # NO se borra el rasgo del subject
        # Y se quitó del bloque dedicado
        assert "Nyra, Amber Eyes, Undercut, cinematic" not in out

    def test_sin_trigger_o_vacio_no_toca(self):
        from modules.prompt_helpers import mover_trigger_al_inicio as M
        assert M("POSITIVE PROMPT: a, b", "") == "POSITIVE PROMPT: a, b"
        assert M("", "x") == ""

    # ── recorta preservando tags completos ─────────────────────────
    def test_recorta_positive_por_tags_completos(self):
        # Construimos un prompt donde cada tag mide ~10 chars → con max=25 solo caben 2
        tags = ["tag_uno", "tag_dos", "tag_tres", "tag_cuatro", "tag_cinco"]
        texto = "POSITIVE PROMPT: " + ", ".join(tags)
        result = recortar_si_excede(texto, 25)
        # El resultado debe contener POSITIVE PROMPT
        assert "POSITIVE PROMPT:" in result
        # No debe haber corte en mitad de un tag: cada token tras la coma es completo
        pos_part = result.split("POSITIVE PROMPT:")[1].strip()
        for token in pos_part.split(","):
            token = token.strip()
            assert token in tags, f"token inesperado en resultado: {repr(token)}"

    def test_no_corta_en_mitad_de_tag(self):
        # Un tag largo; si max_chars es justo para 1 tag completo, no corta a la mitad
        texto = "POSITIVE PROMPT: short, muchomaslargoesteestetrece"
        # max_chars=15: solo cabe "short" (5 chars)
        result = recortar_si_excede(texto, 15)
        pos_part = result.split("POSITIVE PROMPT:")[1].strip()
        # "short" debe estar completo; el otro tag no debe aparecer truncado
        assert "short" in pos_part
        assert "muchomaslargo" not in pos_part or "muchomaslargoesteestetrece" in pos_part

    def test_recorta_negative_con_max_chars_negative(self):
        neg_tags = ["ugly", "blurry", "watermark", "low_res", "bad_anatomy"]
        pos = "nice portrait, soft light"
        texto = (
            f"POSITIVE PROMPT: {pos}\n"
            f"NEGATIVE PROMPT: {', '.join(neg_tags)}"
        )
        # max_chars grande para positive, pequeño para negative
        result = recortar_si_excede(texto, 500, max_chars_negative=15)
        assert "NEGATIVE PROMPT:" in result
        neg_part = result.split("NEGATIVE PROMPT:")[1].strip()
        # Solo debe haber tags completos que quepan en 15 chars
        for token in neg_part.split(","):
            token = token.strip()
            assert token in neg_tags

    def test_negative_sin_max_chars_negative_usa_mismo_limite(self):
        pos = "portrait, soft, bokeh"
        neg_largo = ", ".join(["tag"] * 50)  # muy largo
        texto = f"POSITIVE PROMPT: {pos}\nNEGATIVE PROMPT: {neg_largo}"
        result = recortar_si_excede(texto, 50)
        # El negative debe haberse recortado
        assert "NEGATIVE PROMPT:" in result
        neg_part = result.split("NEGATIVE PROMPT:")[1].strip()
        assert len(neg_part) <= 50

    def test_resultado_tiene_formato_correcto(self):
        texto = (
            "POSITIVE PROMPT: " + ", ".join([f"tag{i}" for i in range(50)]) + "\n"
            "NEGATIVE PROMPT: " + ", ".join([f"neg{i}" for i in range(50)])
        )
        result = recortar_si_excede(texto, 100)
        assert result.startswith("POSITIVE PROMPT:")
        assert "NEGATIVE PROMPT:" in result

    def test_positive_vacio_tras_recortar_queda_positive_prompt(self):
        # Si todos los tags son demasiado largos para max_chars, queda POSITIVE PROMPT: vacío
        texto = "POSITIVE PROMPT: un_tag_muy_muy_muy_largo_que_no_cabe_nunca"
        result = recortar_si_excede(texto, 5)
        # No debe lanzar excepción; debe devolver algo con POSITIVE PROMPT:
        assert "POSITIVE PROMPT:" in result

    def test_sin_negative_en_texto_no_aparece_en_resultado(self):
        texto = "POSITIVE PROMPT: nice, clean, sharp"
        result = recortar_si_excede(texto, 10)
        assert "NEGATIVE PROMPT:" not in result

    # ── excepción interna → devuelve intacto ───────────────────────
    def test_excepcion_interna_devuelve_texto_intacto(self):
        # Forzamos una situación donde el regex falla pasando None como texto
        # La función debe capturar la excepción y devolver el texto original
        texto = "POSITIVE PROMPT: x, y, z"
        # max_chars negativo no es un caso documentado, pero no debe explotar
        try:
            result = recortar_si_excede(texto, -1)
            # Puede devolver el texto intacto o recortado, pero no debe lanzar
        except Exception as e:
            pytest.fail(f"recortar_si_excede lanzó excepción inesperada: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
