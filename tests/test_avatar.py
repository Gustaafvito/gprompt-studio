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
    exportar_dataset,
    generar_dataset_avatar,
    generar_descripcion_canonica,
)
from modules.avatar_prompts import (
    construir_user_prompt_canonico,
    ensamblar_dataset,
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

    def test_caption_kohya_solo_trigger_y_encuadre(self):
        ds = ensamblar_dataset("ohwx_ana", DESC, ["face_front"], "", "bg")
        # La identidad NO va en la caption (la absorbe el trigger)
        assert ds[0]["caption"] == "ohwx_ana, close-up portrait"
        assert DESC not in ds[0]["caption"]

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
            assert f.read() == "ohwx_test, close-up portrait"

        with open(os.path.join(base, "prompts", "01_face_front.txt"),
                  encoding="utf-8") as f:
            contenido = f.read()
        assert "PROMPT:" in contenido
        assert "NEGATIVE PROMPT:" in contenido
