"""Variedad de lo que NO es el sujeto en el Generador de Dataset LoRA (fase 2).

09-oct-2026: el dataset de personaje repetía la misma ropa (la de la ficha,
«idéntica en todo el dataset») y la misma luz de estudio en todas las
imágenes, con solo cuatro fondos lisos. El LoRA se aprendía la ropa y la luz
como parte del personaje. La guía de SeaArt pide imágenes «variadas en pose,
ángulo, expresión, ropa y fondo», y el dataset del LoRA Lyra (G-Entrena), que
salió limpio, variaba todo eso y lo nombraba en cada descripción.
"""
import pytest

from modules import i18n
from modules.avatar_config import (
    AVATAR_ANGLES,
    AVATAR_EXPRESIONES_ROTACION,
    AVATAR_LIGHTING,
    AVATAR_ROPA_ROTACION,
    LORA_TYPES,
)
from modules.avatar_destinos import redactar_descripcion
from modules.avatar_prompts import (
    admite_expresion,
    ensamblar_dataset,
    ensamblar_dataset_edicion,
    ensamblar_dataset_generico,
    sin_ropa,
    valor_rotado,
)

DESC = ("a 28 year old woman with fair skin, large green eyes, wavy chestnut "
        "hair, slim build, wearing a plain white t-shirt and blue denim jeans")
ANGULOS = ["face_front", "bust_front", "full_front", "full_back",
           "expression_smile", "cowboy_front", "pose_walking", "bust_34_left"]


def _variar(tipo, *claves):
    return {c: v for c, _, v, _ in LORA_TYPES[tipo]["variaciones"]
            if not claves or c in claves}


def _personaje(variar=None):
    return ensamblar_dataset("tw", DESC, ANGULOS, "", None, True, variar=variar)


class TestSinVariarTodoSigueIgual:

    def test_misma_luz_y_ropa_de_la_ficha(self):
        for it in _personaje():
            assert AVATAR_LIGHTING in it["prompt"]
            assert it["partes_descripcion"]["ropa"] == ""
            assert it["partes_descripcion"]["expresion"] == ""
        # La ropa de la ficha sigue en los planos que no son de cara.
        assert "white t-shirt" in _personaje()[1]["prompt"]

    def test_caption_de_siempre(self):
        it = _personaje()[1]
        assert it["caption"] == "tw, upper body, front view, soft even studio lighting"


class TestRopaVariada:

    def test_fuera_la_de_la_ficha_y_dentro_la_rotada(self):
        datos = _personaje(_variar("Personaje", "ropa"))
        for it in datos:
            assert "white t-shirt" not in it["prompt"], it["angle_key"]
        # Los primeros planos (cara y expresiones) no llevan ropa: ver abajo.
        cuerpo = [it for it in datos if not AVATAR_ANGLES[it["angle_key"]]
                  ["prompt"].startswith("close-up headshot")]
        assert len(cuerpo) == 6
        assert all("wearing " in it["prompt"] for it in cuerpo)
        assert len({it["partes_descripcion"]["ropa"] for it in cuerpo}) > 3

    def test_en_el_primer_plano_no_hay_ropa(self):
        # Ahí no se ve y alejaría la cámara (la misma razón por la que el
        # primer plano ya quitaba la ropa de la ficha).
        it = _personaje(_variar("Personaje", "ropa"))[0]
        assert it["angle_key"] == "face_front"
        assert "wearing" not in it["prompt"]
        assert it["partes_descripcion"]["ropa"] == ""

    def test_la_ropa_va_en_la_descripcion(self):
        it = _personaje(_variar("Personaje", "ropa"))[1]
        ropa = it["partes_descripcion"]["ropa"]
        assert ropa.startswith("wearing ") and ropa in it["caption"]


class TestEscenarioLuzExpresion:

    def test_escenarios_reales_en_vez_de_estudio(self):
        datos = _personaje(_variar("Personaje", "escenario"))
        assert all("studio backdrop" not in it["prompt"] for it in datos)
        assert len({it["partes_descripcion"]["fondo"] for it in datos}) == len(datos)

    def test_el_escenario_quita_el_fondo_neutro_del_angulo(self):
        # «Pose — caminando» trae «neutral background» de serie: con un
        # escenario real quedaba «neutral background, beach at sunset».
        assert "neutral background" in AVATAR_ANGLES["pose_walking"]["prompt"]
        it = _personaje(_variar("Personaje", "escenario"))[6]
        assert it["angle_key"] == "pose_walking"
        assert "neutral background" not in it["prompt"]
        ed = ensamblar_dataset_edicion("tw", ["pose_walking"], None, True,
                                       variar=_variar("Personaje", "escenario"))
        assert "neutral background" not in ed[0]["prompt"]
        # Sin escenario, el ángulo queda como siempre.
        assert "neutral background" in _personaje()[6]["prompt"]

    def test_luz_rotada(self):
        datos = _personaje(_variar("Personaje", "luz"))
        assert len({it["partes_descripcion"]["luz"] for it in datos}) > 3
        assert not all(AVATAR_LIGHTING in it["prompt"] for it in datos)

    def test_expresion_solo_donde_tiene_sentido(self):
        datos = {it["angle_key"]: it for it in _personaje(_variar("Personaje", "expresion"))}
        # El de «Expresión — sonrisa» ya la trae; de espaldas no se ve la cara.
        assert datos["expression_smile"]["partes_descripcion"]["expresion"] == ""
        assert datos["full_back"]["partes_descripcion"]["expresion"] == ""
        assert datos["bust_front"]["partes_descripcion"]["expresion"] in AVATAR_EXPRESIONES_ROTACION

    def test_admite_expresion(self):
        assert admite_expresion(AVATAR_ANGLES["bust_front"])
        assert not admite_expresion(AVATAR_ANGLES["expression_laugh"])
        assert not admite_expresion(AVATAR_ANGLES["full_34_back"])

    def test_no_se_repiten_siempre_juntas(self):
        # Longitudes distintas: la misma ropa no cae siempre con el mismo
        # escenario (si no, el LoRA los asociaría).
        datos = ensamblar_dataset("tw", DESC, list(AVATAR_ANGLES), "", None,
                                  True, variar=_variar("Personaje"))
        pares = {}
        for it in datos:
            p = it["partes_descripcion"]
            if p["ropa"]:
                pares.setdefault(p["ropa"], set()).add(p["fondo"])
        assert any(len(fondos) > 1 for fondos in pares.values())


class TestOtrosTipos:

    def _generico(self, tipo, variar):
        cfg = LORA_TYPES[tipo]
        return ensamblar_dataset_generico(
            tipo, "tw", "a place", list(cfg["angles"])[:6], cfg["angles"], "",
            cfg.get("backgrounds_rotacion"), cfg["lighting"], cfg["negative"],
            True, variar=variar)

    def test_paisaje_cambia_hora_y_tiempo(self):
        datos = self._generico("Paisaje", _variar("Paisaje"))
        luces = {it["partes_descripcion"]["luz"] for it in datos}
        assert "at sunrise" in luces and len(luces) > 3

    def test_objeto_solo_varia_la_luz(self):
        # Sus ángulos ya fijan cada uno su fondo (blanco, degradado, textura,
        # oscuro…): un escenario encima chocaría con ellos.
        assert [c for c, *_ in LORA_TYPES["Objeto"]["variaciones"]] == ["luz"]
        datos = self._generico("Objeto", _variar("Objeto"))
        assert len({it["partes_descripcion"]["luz"] for it in datos}) > 3

    def test_nsfw_varia_expresion_y_luz_pero_no_ropa(self):
        assert [c for c, *_ in LORA_TYPES["NSFW"]["variaciones"]] == ["expresion", "luz"]

    def test_estilo_no_varia_nada_mas(self):
        # Su variedad son los temas, que ya cambian con cada ángulo.
        assert LORA_TYPES["Estilo"]["variaciones"] == []


class TestModoEdicion:

    def test_con_ropa_variada_no_pide_la_misma_ropa(self):
        datos = ensamblar_dataset_edicion("tw", ["bust_front", "full_34_left"],
                                          None, True, variar=_variar("Personaje", "ropa"))
        for it in datos:
            assert "same clothing" not in it["prompt"]
            assert "Change the outfit to" in it["prompt"]

    def test_sin_variar_sigue_pidiendo_la_misma_ropa(self):
        datos = ensamblar_dataset_edicion("tw", ["bust_front"], None, True)
        assert "same clothing" in datos[0]["prompt"]


class TestPiezasSueltas:

    def test_valor_rotado(self):
        assert valor_rotado({"luz": ["a", "b"]}, "luz", 3) == "b"
        assert valor_rotado(None, "luz", 0) == ""
        assert valor_rotado({"luz": []}, "luz", 0) == ""

    def test_sin_ropa(self):
        assert sin_ropa(DESC).endswith("slim build")
        assert sin_ropa("a man with short hair") == "a man with short hair"

    def test_la_descripcion_lleva_lo_variado_en_orden(self):
        partes = {"encuadre": "upper body, front view", "expresion": "gentle smile",
                  "ropa": "wearing a black hoodie", "fondo": "forest trail",
                  "luz": "golden hour sunlight"}
        out = redactar_descripcion(partes, "frases", "Personaje", "lyr4",
                                   ("1girl, solo", "a woman"))
        assert out == ("lyr4, a woman, upper body, front view, gentle smile, "
                       "wearing a black hoodie, forest trail, golden hour sunlight")


@pytest.mark.parametrize("tipo", list(LORA_TYPES))
def test_las_casillas_estan_traducidas(tipo):
    for _clave, etiqueta, valores, _defecto in LORA_TYPES[tipo]["variaciones"]:
        assert etiqueta in i18n.TRADUCCIONES, etiqueta
        assert valores and len(set(valores)) == len(valores)


def test_las_listas_tienen_longitudes_distintas():
    # Si dos listas midieran igual, sus valores irían siempre emparejados.
    for tipo in LORA_TYPES:
        largos = [len(v) for _, _, v, _ in LORA_TYPES[tipo]["variaciones"]]
        assert len(largos) == len(set(largos)), tipo


def test_la_ropa_es_de_calle_y_unisex():
    # La ropa rota en personajes de cualquier género: nada de vestidos ni
    # trajes de época que contradigan la ficha.
    assert len(AVATAR_ROPA_ROTACION) >= 10
