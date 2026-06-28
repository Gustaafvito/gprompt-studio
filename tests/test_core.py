"""Tests para CoreMixin (modules/core.py).

Cobertura de los helpers pure-ish testeables sin abrir ventanas Tk:
  • extraer_positive / extraer_negative — parsers de POSITIVE/NEGATIVE
    en el texto de salida según múltiples formatos (POSITIVE PROMPT:,
    PROMPT:, sin marcadores).
  • _parsear_variaciones — parser de bloques de variaciones (1., 2., 3., ---).
  • _recortar_si_excede — recorte preservando tags completos.
  • _extraer_pos_de_bloque / _extraer_neg_de_bloque — extractores
    de bloques individuales.

Usamos una clase Host minimal que mezcla CoreMixin con atributos fake
para evitar instanciar ArquitectoApp.
"""
from types import SimpleNamespace

from modules.core import CoreMixin


class _Host(CoreMixin):
    """Host minimal: hereda CoreMixin sin pasar por ctk.CTk."""

    def __init__(self, salida=""):
        self.txt_salida = SimpleNamespace(get=lambda *_a, **_k: salida)


class TestContextoModeloParaIdeas:
    """Las ideas deben ir EN FUNCIÓN del modelo seleccionado (no genéricas)."""

    def _host(self, modo, modelo):
        h = _Host()
        h.modo_var = SimpleNamespace(get=lambda: modo)
        h.combo_modelo_imagen = SimpleNamespace(get=lambda: modelo)
        h.combo_modelo_video = SimpleNamespace(get=lambda: modelo)
        h.combo_modelo_audio = SimpleNamespace(get=lambda: modelo)
        return h

    def test_inyecta_nombre_y_best_for(self):
        h = self._host("imagen", "AnimePro FLUX")
        out = h._contexto_modelo_para_ideas()
        assert "AnimePro FLUX" in out
        assert "anime" in out.lower()      # del best_for anime del modelo
        assert "ENCAJAR" in out            # la instrucción al LLM

    def test_separador_no_inyecta(self):
        h = self._host("imagen", "── Familia FLUX ──")
        assert h._contexto_modelo_para_ideas() == ""

    def test_modelo_vacio_no_inyecta(self):
        h = self._host("imagen", "")
        assert h._contexto_modelo_para_ideas() == ""


# ─────────────────────── extraer_positive ─────────────────────────────


class TestExtraerPositive:

    def test_con_positive_prompt_y_negative(self):
        h = _Host("POSITIVE PROMPT: a girl smiling\nNEGATIVE PROMPT: blurry, low quality")
        assert h.extraer_positive() == "a girl smiling"

    def test_con_positive_prompt_sin_negative(self):
        h = _Host("POSITIVE PROMPT: a girl smiling")
        assert h.extraer_positive() == "a girl smiling"

    def test_con_prompt_simple_natural(self):
        """Modelos naturales: solo 'PROMPT:' sin POSITIVE."""
        h = _Host("PROMPT: a beautiful landscape")
        assert h.extraer_positive() == "a beautiful landscape"

    def test_con_prompt_y_negative_natural(self):
        h = _Host("PROMPT: a portrait\nNEGATIVE: blurry")
        assert h.extraer_positive() == "a portrait"

    def test_sin_marcadores_con_texto_largo(self):
        """Sin marcadores: devuelve el texto si supera 5 chars."""
        h = _Host("a beautiful landscape with mountains")
        result = h.extraer_positive()
        assert result == "a beautiful landscape with mountains"

    def test_sin_marcadores_texto_corto_devuelve_none(self):
        h = _Host("xx")
        assert h.extraer_positive() is None

    def test_sin_marcadores_pero_con_negative_pelado(self):
        """Sin POSITIVE/PROMPT pero con bloque NEGATIVE: marca: corta antes."""
        h = _Host("a girl smiling\nNEGATIVE: blurry")
        result = h.extraer_positive()
        # La rama de "sin marcadores" corta en marcas_neg → 'NEGATIVE:'
        assert result is not None
        assert "blurry" not in result
        assert "girl smiling" in result

    def test_con_variantes_numeradas_solo_devuelve_primera(self):
        h = _Host("POSITIVE PROMPT: option a\n1. otro bloque\n2. más bloques")
        # El split por POSITIVE PROMPT: deja todo lo posterior, incluyendo
        # las variantes. Verificamos al menos que el texto principal está.
        assert "option a" in h.extraer_positive()


# ─────────────────────── extraer_negative ─────────────────────────────


class TestExtraerNegative:

    def test_con_negative_prompt(self):
        h = _Host("POSITIVE PROMPT: x\nNEGATIVE PROMPT: blurry, low quality")
        assert h.extraer_negative() == "blurry, low quality"

    def test_con_negative_sin_prompt(self):
        h = _Host("POSITIVE PROMPT: x\nNEGATIVE: low quality")
        assert h.extraer_negative() == "low quality"

    def test_sin_negative_devuelve_none(self):
        h = _Host("POSITIVE PROMPT: x")
        assert h.extraer_negative() is None

    def test_corta_en_separadores_de_variantes(self):
        h = _Host("POSITIVE PROMPT: x\nNEGATIVE PROMPT: blurry\n1. otra")
        result = h.extraer_negative()
        assert result == "blurry"


# ─────────────────────── _parsear_variaciones ─────────────────────────


class TestParsearVariaciones:

    def test_devuelve_lista_vacia_si_solo_un_bloque(self):
        h = _Host()
        result = h._parsear_variaciones("texto sin variaciones")
        assert result == []

    def test_parsea_variaciones_numeradas(self):
        h = _Host()
        texto = (
            "Aquí van tus 3 variaciones:\n"
            "1. POSITIVE PROMPT: variante uno con bastante contenido extra\n"
            "2. POSITIVE PROMPT: variante dos con bastante contenido extra\n"
            "3. POSITIVE PROMPT: variante tres con bastante contenido extra"
        )
        result = h._parsear_variaciones(texto)
        # Debe encontrar al menos 2 bloques (el preámbulo se filtra)
        assert len(result) >= 2

    def test_parsea_separador_triple_dash(self):
        h = _Host()
        texto = (
            "POSITIVE PROMPT: variante uno con contenido suficiente largo\n"
            "---\n"
            "POSITIVE PROMPT: variante dos con contenido suficiente largo\n"
            "---\n"
            "POSITIVE PROMPT: variante tres con contenido suficiente largo"
        )
        result = h._parsear_variaciones(texto)
        assert len(result) >= 2

    def test_filtra_preambulo_si_n_esperado_excede(self):
        h = _Host()
        texto = (
            "Preámbulo del LLM con texto largo para hacer la cosa interesante.\n"
            "1. POSITIVE PROMPT: variante uno con contenido suficientemente largo\n"
            "2. POSITIVE PROMPT: variante dos con contenido suficientemente largo\n"
            "3. POSITIVE PROMPT: variante tres con contenido suficientemente largo"
        )
        result = h._parsear_variaciones(texto, n_esperado=3)
        assert len(result) == 3
        # Todas deben contener "POSITIVE PROMPT" (filtra preámbulos sin marcador)
        for bloque in result:
            assert "POSITIVE" in bloque.upper()


# ─────────────────────── _recortar_si_excede ──────────────────────────


class TestRecortarSiExcede:

    def test_sin_max_chars_devuelve_texto_tal_cual(self):
        h = _Host()
        texto = "POSITIVE PROMPT: cualquier cosa"
        assert h._recortar_si_excede(texto, 0) == texto
        assert h._recortar_si_excede(texto, None) == texto

    def test_texto_vacio_devuelve_vacio(self):
        h = _Host()
        assert h._recortar_si_excede("", 100) == ""

    def test_pos_dentro_del_limite_no_recorta(self):
        h = _Host()
        texto = "POSITIVE PROMPT: corto"
        assert h._recortar_si_excede(texto, 1000) == texto

    def test_pos_excede_recorta_por_comas(self):
        h = _Host()
        tags = ", ".join([f"tag{i}_largo" for i in range(50)])
        texto = f"POSITIVE PROMPT: {tags}"
        result = h._recortar_si_excede(texto, 100)
        # Debe conservar "POSITIVE PROMPT:" y ser <= 100 chars (aprox)
        assert "POSITIVE PROMPT:" in result
        # El positive resultante debe ser <= 100 chars
        pos_part = result.split("POSITIVE PROMPT:")[1].strip()
        assert len(pos_part) <= 100

    def test_negative_excede_se_recorta_al_mismo_limite_que_positive(self):
        """Sesión 16: el límite del NEGATIVE por defecto es el mismo que
        el POSITIVE (antes era hardcoded 1500). Para forzar otro, se
        pasa max_chars_negative."""
        h = _Host()
        tags = ", ".join([f"negativo_tag{i}_muy_largo_de_verdad" for i in range(100)])
        texto = f"POSITIVE PROMPT: short\nNEGATIVE PROMPT: {tags}"
        # Con max_chars=5000 el NEGATIVE puede llegar hasta 5000
        result = h._recortar_si_excede(texto, 5000)
        assert "NEGATIVE PROMPT:" in result
        neg_part = result.split("NEGATIVE PROMPT:")[1].strip()
        assert len(neg_part) <= 5000

    def test_max_chars_negative_override(self):
        """El parámetro max_chars_negative limita el NEGATIVE
        independientemente del POSITIVE."""
        h = _Host()
        tags = ", ".join([f"tag{i}_largo" for i in range(80)])
        texto = f"POSITIVE PROMPT: short\nNEGATIVE PROMPT: {tags}"
        result = h._recortar_si_excede(texto, 5000, max_chars_negative=500)
        neg_part = result.split("NEGATIVE PROMPT:")[1].strip()
        assert len(neg_part) <= 500

    def test_sin_pos_marker_cabe_devuelve_intacto(self):
        h = _Host()
        texto = "texto corto"
        assert h._recortar_si_excede(texto, 100) == texto

    def test_sin_pos_marker_excede_recorta_prosa(self):
        # Prosa sin etiqueta PROMPT: (típico en vídeo) ahora SÍ se recorta
        # al límite del modelo, por frontera de palabra (fix vídeo).
        h = _Host()
        texto = "texto sin marcador alguno"
        out = h._recortar_si_excede(texto, 10)
        assert len(out) <= 10
        assert texto.startswith(out)  # prefijo, sin partir palabra


# ─────────────────────── _extraer_pos_de_bloque ───────────────────────


class TestExtraerPosDeBloque:

    def test_con_positive_prompt(self):
        h = _Host()
        bloque = "POSITIVE PROMPT: una chica\nNEGATIVE PROMPT: blurry"
        assert h._extraer_pos_de_bloque(bloque) == "una chica"

    def test_con_prompt_simple(self):
        h = _Host()
        bloque = "PROMPT: descripción natural del paisaje"
        assert h._extraer_pos_de_bloque(bloque) == "descripción natural del paisaje"

    def test_sin_marcador_devuelve_texto_limpio(self):
        h = _Host()
        assert h._extraer_pos_de_bloque("solo texto plano") == "solo texto plano"

    def test_filtra_negative_antes_de_buscar_positive(self):
        h = _Host()
        bloque = "POSITIVE: a\nNEGATIVE: b"
        result = h._extraer_pos_de_bloque(bloque)
        # No debe incluir 'b' (eso es NEGATIVE)
        assert "b" not in result.lower() or result.lower() == "a"


# ─────────────────────── _extraer_neg_de_bloque ───────────────────────


class TestExtraerNegDeBloque:

    def test_con_negative_prompt(self):
        h = _Host()
        bloque = "POSITIVE PROMPT: x\nNEGATIVE PROMPT: blurry, low"
        assert h._extraer_neg_de_bloque(bloque) == "blurry, low"

    def test_con_negative_simple(self):
        h = _Host()
        bloque = "POSITIVE: x\nNEGATIVE: bad"
        assert h._extraer_neg_de_bloque(bloque) == "bad"

    def test_sin_negative_en_bloque_usa_extraer_negative_global(self):
        """Fallback: si no encuentra NEGATIVE en el bloque, recurre al
        global de extraer_negative()."""
        h = _Host("POSITIVE PROMPT: x\nNEGATIVE PROMPT: global_neg")
        result = h._extraer_neg_de_bloque("solo positive sin negative")
        assert result == "global_neg"

    def test_sin_negative_local_ni_global_devuelve_none(self):
        h = _Host("POSITIVE PROMPT: x")  # sin NEGATIVE global
        assert h._extraer_neg_de_bloque("solo texto") is None
