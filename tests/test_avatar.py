"""Tests del módulo Avatar dataset (LoRA) — sesión 19.

Cubre la lógica pura (sin UI ni LLM real): construcción del user
prompt, ensamblado programático del dataset, pipeline con LLM falso
y exportación a disco.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.avatar_config import (
    AVATAR_ANGLES,
    AVATAR_FORM_FIELDS,
    AVATAR_LIGHTING,
    AVATAR_NEGATIVE_PROMPT,
    DEFAULT_ANGLE_SET,
)
from modules.avatar_generator import (
    adaptar_dataset_a_modelo,
    exportar_dataset,
    generar_dataset_avatar,
    generar_descripcion_canonica,
)
from modules.avatar_prompts import (
    PROMPT_VISION_FICHA,
    SYSTEM_PROMPT_AVATAR_FICHA,
    construir_user_prompt_canonico,
    construir_user_prompt_ficha,
    ensamblar_dataset,
    ensamblar_dataset_edicion,
    parsear_ficha_json,
)

DESC = ("a 28 year old woman with fair skin, oval face, green eyes, "
        "wavy brown hair, slim build, wearing a white t-shirt and jeans")


def _llm_fake(system, user):
    return DESC


# ── Configuración ─────────────────────────────────────────────────

class TestAvatarConfig:
    def test_16_angulos_canonicos(self):
        assert len(AVATAR_ANGLES) == 16
        assert DEFAULT_ANGLE_SET == list(AVATAR_ANGLES.keys())

    def test_angulos_tienen_campos_obligatorios(self):
        for key, datos in AVATAR_ANGLES.items():
            for campo in ("label", "prompt", "framing", "filename", "group"):
                assert campo in datos, f"{key} sin campo {campo}"

    def test_filenames_unicos(self):
        nombres = [d["filename"] for d in AVATAR_ANGLES.values()]
        assert len(nombres) == len(set(nombres))

    def test_form_fields_con_key_y_tipo(self):
        for campo in AVATAR_FORM_FIELDS:
            assert campo["type"] in ("entry", "option")
            assert campo["key"]


# ── construir_user_prompt_canonico ────────────────────────────────

class TestConstruirUserPrompt:
    def test_incluye_campos_rellenos(self):
        p = construir_user_prompt_canonico({"genero": "Mujer", "pelo": "castaña"})
        assert "Género: Mujer" in p
        assert "Pelo: castaña" in p

    def test_omite_campos_vacios(self):
        p = construir_user_prompt_canonico({"genero": "Mujer", "ojos": "  "})
        assert "Ojos" not in p

    def test_pide_la_descripcion(self):
        assert "descripción canónica" in construir_user_prompt_canonico({})


# ── Ficha automática (sesión 19 round 10) ─────────────────────────

class TestFichaAutomatica:
    FICHA_JSON = ('{"trigger": "ohwx_vera", "genero": "Mujer", "edad": "25-35", '
                  '"pelo": "melena negra lisa", "ojos": "marrones grandes", '
                  '"complexion": "Atlética", "ropa": "bomber verde y vaqueros"}')

    def test_system_prompt_exige_json_y_claves(self):
        assert "JSON" in SYSTEM_PROMPT_AVATAR_FICHA
        for clave in ("trigger", "genero", "edad", "complexion", "ropa"):
            assert clave in SYSTEM_PROMPT_AVATAR_FICHA

    def test_user_prompt_con_tema(self):
        p = construir_user_prompt_ficha("guerrera élfica")
        assert "guerrera élfica" in p

    def test_user_prompt_sin_tema_pide_aleatorio(self):
        assert "aleatorio" in construir_user_prompt_ficha("")

    def test_parsea_json_limpio(self):
        f = parsear_ficha_json(self.FICHA_JSON)
        assert f["trigger"] == "ohwx_vera"
        assert f["genero"] == "Mujer"
        assert f["ropa"] == "bomber verde y vaqueros"

    def test_parsea_json_con_texto_y_fences(self):
        sucio = f"Claro, aquí tienes:\n```json\n{self.FICHA_JSON}\n```\n¡Listo!"
        f = parsear_ficha_json(sucio)
        assert f["trigger"] == "ohwx_vera"

    def test_filtra_claves_desconocidas_y_vacias(self):
        f = parsear_ficha_json('{"trigger": "x", "hacker": "no", "pelo": "  "}')
        assert f == {"trigger": "x"}

    def test_respuesta_sin_json_devuelve_vacio(self):
        assert parsear_ficha_json("no hay nada aquí") == {}
        assert parsear_ficha_json("") == {}

    def test_json_invalido_devuelve_vacio(self):
        assert parsear_ficha_json("{trigger: sin comillas}") == {}

    def test_valores_numericos_se_castean(self):
        f = parsear_ficha_json('{"edad": 25, "pelo": "negro"}')
        assert f["edad"] == "25"

    def test_prompt_vision_exige_json_y_mismas_claves(self):
        # La ficha por visión reutiliza parsear_ficha_json → mismas claves
        assert "JSON" in PROMPT_VISION_FICHA
        for clave in ("trigger", "genero", "edad", "etnia_piel", "pelo",
                      "ojos", "rasgos", "complexion", "ropa"):
            assert clave in PROMPT_VISION_FICHA

    def test_prompt_vision_prohibe_fondo_e_iluminacion(self):
        # El fondo/iluminación los pone el ensamblador, no la ficha
        assert "NO describas el fondo" in PROMPT_VISION_FICHA


# ── ensamblar_dataset (núcleo de la consistencia) ─────────────────

class TestEnsamblarDataset:
    def test_descripcion_identica_en_todos_los_prompts(self):
        # La razón de ser del módulo: identidad palabra por palabra
        ds = ensamblar_dataset("ohwx_ana", DESC, DEFAULT_ANGLE_SET,
                               "photorealistic", "gray background")
        assert len(ds) == 16
        for item in ds:
            assert DESC in item["prompt"]
            assert item["prompt"].startswith("ohwx_ana, ")

    def test_estructura_del_prompt(self):
        ds = ensamblar_dataset("trig", DESC, ["face_front"],
                               "estilo_x", "fondo_y")
        p = ds[0]["prompt"]
        # Orden: trigger, desc, ángulo, fondo, iluminación, estilo
        assert p.index("trig") < p.index(DESC) < p.index("close-up portrait")
        assert "fondo_y" in p
        assert AVATAR_LIGHTING in p
        assert p.endswith("estilo_x")

    def test_caption_kohya_incluye_fondo_e_iluminacion(self):
        # GUÍA OFICIAL SeaArt: la caption etiqueta fondo/iluminación/pose
        # para que el LoRA no los absorba; la identidad NO va (trigger).
        ds = ensamblar_dataset("ohwx_ana", DESC, ["face_front"], "",
                               "plain gray background, seamless backdrop")
        assert ds[0]["caption"] == ("ohwx_ana, close-up portrait, "
                                    "plain gray background, "
                                    "soft even studio lighting")
        assert DESC not in ds[0]["caption"]

    def test_caption_sin_fondo_omite_el_segmento(self):
        ds = ensamblar_dataset("t", DESC, ["face_front"], "", "")
        assert ds[0]["caption"] == "t, close-up portrait, soft even studio lighting"

    def test_negative_opcional(self):
        con = ensamblar_dataset("t", DESC, ["face_front"], "", "bg",
                                incluir_negative=True)
        sin = ensamblar_dataset("t", DESC, ["face_front"], "", "bg",
                                incluir_negative=False)
        assert con[0]["negative"] == AVATAR_NEGATIVE_PROMPT
        assert sin[0]["negative"] == ""

    def test_angulos_desconocidos_se_ignoran(self):
        ds = ensamblar_dataset("t", DESC, ["face_front", "no_existe"], "", "bg")
        assert len(ds) == 1

    def test_sin_estilo_no_deja_coma_colgando(self):
        ds = ensamblar_dataset("t", DESC, ["face_front"], "", "bg")
        assert not ds[0]["prompt"].endswith(", ")


# ── Modo edición img2img (sesión 19 round 12) ─────────────────────

class TestDatasetEdicion:
    def test_16_prompts_de_edicion(self):
        ds = ensamblar_dataset_edicion("ohwx_t", DEFAULT_ANGLE_SET, "gray bg")
        assert len(ds) == 16

    def test_prompt_ordena_conservar_identidad_y_cambiar_camara(self):
        ds = ensamblar_dataset_edicion("t", ["face_profile_left"], "gray bg")
        p = ds[0]["prompt"]
        assert "EXACT same person from the reference image" in p
        assert "Change ONLY the camera" in p
        assert "full left side profile" in p
        assert "gray bg" in p

    def test_sin_descripcion_canonica(self):
        # La identidad la aporta la imagen — el texto NO describe al personaje
        ds = ensamblar_dataset_edicion("t", ["face_front"], "bg")
        assert DESC not in ds[0]["prompt"]

    def test_caption_identica_al_modo_texto(self):
        texto = ensamblar_dataset("t", DESC, ["face_front"], "", "bg")
        edicion = ensamblar_dataset_edicion("t", ["face_front"], "bg")
        assert edicion[0]["caption"] == texto[0]["caption"]
        assert edicion[0]["filename"] == texto[0]["filename"]

    def test_adaptador_tambien_vacia_negatives_de_edicion(self):
        r = generar_dataset_avatar(_llm_fake, {}, "t", ["face_front"], "", "bg")
        r["dataset_edicion"] = ensamblar_dataset_edicion("t", ["face_front"], "bg")
        adaptar_dataset_a_modelo(r, "Nano Banana", {"has_negative": False})
        assert r["dataset"][0]["negative"] == ""
        assert r["dataset_edicion"][0]["negative"] == ""

    def test_export_incluye_prompts_edicion(self, tmp_path):
        r = generar_dataset_avatar(_llm_fake, {}, "t", ["face_front"], "", "bg")
        r["dataset_edicion"] = ensamblar_dataset_edicion("t", ["face_front"], "bg")
        base = exportar_dataset(r, str(tmp_path))
        assert os.path.isfile(os.path.join(base, "prompts_edicion",
                                           "01_face_front.txt"))
        assert os.path.isfile(os.path.join(base, "prompts_edicion_todos.txt"))
        with open(os.path.join(base, "prompts_edicion_todos.txt"),
                  encoding="utf-8") as f:
            assert "MODO EDICIÓN" in f.read()

    def test_export_sin_edicion_no_crea_carpeta(self, tmp_path):
        r = generar_dataset_avatar(_llm_fake, {}, "t", ["face_front"], "", "bg")
        base = exportar_dataset(r, str(tmp_path))
        assert not os.path.isdir(os.path.join(base, "prompts_edicion"))


# ── Pipeline completo + exportación ───────────────────────────────

class TestPipeline:
    def test_descripcion_canonica_sanea_la_respuesta(self):
        def llm_sucio(system, user):
            return f'  "{DESC}"\n```  '
        desc = generar_descripcion_canonica(llm_sucio, {})
        assert desc == DESC

    def test_generar_dataset_avatar_estructura(self):
        r = generar_dataset_avatar(
            _llm_fake, {"genero": "Mujer"}, "ohwx_ana",
            DEFAULT_ANGLE_SET, "photorealistic", "gray bg")
        assert r["trigger_word"] == "ohwx_ana"
        assert r["descripcion_canonica"] == DESC
        assert r["total_prompts"] == 16
        assert len(r["dataset"]) == 16

    def test_adaptar_modelo_sin_negative_vacia_negatives(self):
        r = generar_dataset_avatar(_llm_fake, {}, "t", ["face_front"], "", "bg")
        avisos = adaptar_dataset_a_modelo(r, "Nano Banana", {"has_negative": False})
        assert r["dataset"][0]["negative"] == ""
        assert r["modelo_destino"] == "Nano Banana"
        assert any("NO soporta negative" in a for a in avisos)

    def test_adaptar_modelo_con_negative_no_toca(self):
        r = generar_dataset_avatar(_llm_fake, {}, "t", ["face_front"], "", "bg")
        avisos = adaptar_dataset_a_modelo(r, "Reve 2.0",
                                          {"has_negative": True, "max_chars": 2000})
        assert r["dataset"][0]["negative"] != ""
        assert avisos == []

    def test_adaptar_avisa_si_excede_max_chars_sin_truncar(self):
        r = generar_dataset_avatar(_llm_fake, {}, "t", ["face_front"], "x" * 300, "bg")
        prompt_original = r["dataset"][0]["prompt"]
        avisos = adaptar_dataset_a_modelo(r, "Mini", {"has_negative": True,
                                                      "max_chars": 100})
        assert any("exceden el límite" in a for a in avisos)
        # NO trunca: la identidad entre ángulos es sagrada
        assert r["dataset"][0]["prompt"] == prompt_original

    def test_adaptar_sin_specs_no_hace_nada(self):
        r = generar_dataset_avatar(_llm_fake, {}, "t", ["face_front"], "", "bg")
        assert adaptar_dataset_a_modelo(r, "X", {}) == []
        assert "modelo_destino" not in r

    def test_exportar_dataset_escribe_estructura_completa(self, tmp_path):
        r = generar_dataset_avatar(
            _llm_fake, {}, "ohwx_test", ["face_front", "full_back"],
            "style", "bg")
        base = exportar_dataset(r, str(tmp_path))

        assert os.path.isfile(os.path.join(base, "dataset.json"))
        assert os.path.isfile(os.path.join(base, "prompts_todos.txt"))
        assert os.path.isfile(os.path.join(base, "prompts", "01_face_front.txt"))
        assert os.path.isfile(os.path.join(base, "captions", "01_face_front.txt"))
        assert os.path.isfile(os.path.join(base, "prompts", "12_full_back.txt"))

        with open(os.path.join(base, "dataset.json"), encoding="utf-8") as f:
            d = json.load(f)
        assert d["total_prompts"] == 2

        with open(os.path.join(base, "captions", "01_face_front.txt"),
                  encoding="utf-8") as f:
            assert f.read() == ("ohwx_test, close-up portrait, bg, "
                                "soft even studio lighting")

        # Consejos oficiales de SeaArt incluidos en cada export
        consejos = os.path.join(base, "CONSEJOS_SEAART.txt")
        assert os.path.isfile(consejos)
        with open(consejos, encoding="utf-8") as f:
            assert "25-40 imágenes" in f.read()

        with open(os.path.join(base, "prompts", "01_face_front.txt"),
                  encoding="utf-8") as f:
            contenido = f.read()
        assert "PROMPT:" in contenido
        assert "NEGATIVE PROMPT:" in contenido
