"""Workflows de vídeo del botón 🔧 Comfy, desde las plantillas oficiales.

17-oct-2026: con LTX 2.5 elegido en modo vídeo, el botón exportaba el modelo
que se había quedado en el desplegable de IMAGEN. Las plantillas de vídeo de
ComfyUI son demasiado complejas para montarlas a mano, así que la app parte
de las que trae el ComfyUI del usuario y les escribe lo suyo.

Las plantillas de aquí son sintéticas y mínimas, pero con las dos formas en
que ComfyUI guarda los valores de un subgrafo: la clásica (LTX, MiniMax H3)
y la de proxyWidgets (Wan 2.2). El CI no tiene ComfyUI.
"""
import json

import pytest

from modules import comfy_video as cv

PROMPT, NEG = "MY PROMPT", "MY NEGATIVE"
NOMBRES = {
    "diffusion_models": [
        "LTX-2.5-Distilled-Q3_K_M.gguf",
        "LoraLab-D\\wan2.2_t2v_high_noise_14B_fp16.safetensors",
        "LoraLab-D\\wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors",
    ],
    "text_encoders": ["gemma4-12b-with-proj-ltx-2.5-nvfp4.safetensors"],
}


def _w(nombre, link=None):
    return {"name": nombre, "widget": {"name": nombre}, "link": link}


def _l(lid, origen, destino, slot):
    return {"id": lid, "origin_id": origen, "origin_slot": 0,
            "target_id": destino, "target_slot": slot, "type": "*"}


def _clasica():
    """Como LTX 2.5: los valores, en el nodo exterior; el ancho llega de un
    ResolutionSelector de fuera."""
    sg = "aaaaaaaa-0000-4000-8000-000000000001"
    dentro = [
        {"id": 10, "type": "PrimitiveStringMultiline", "title": "Prompt",
         "inputs": [_w("value", 1)], "widgets_values": ["inner default " * 4]},
        {"id": 11, "type": "PrimitiveBoolean", "title": "Boolean (Enable Prompt Enhance)",
         "inputs": [_w("value", 2)], "widgets_values": [True]},
        {"id": 12, "type": "PrimitiveInt", "title": "Duration",
         "inputs": [_w("value", 3)], "widgets_values": [5, "fixed"]},
        {"id": 13, "type": "UNETLoader",
         "inputs": [_w("unet_name", 4), _w("weight_dtype")],
         "widgets_values": ["ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors",
                            "default"]},
        {"id": 14, "type": "CLIPLoader", "inputs": [_w("clip_name", 5)],
         "properties": {"models": [{
             "name": "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors",
             "url": "https://example.invalid/gemma.safetensors",
             "directory": "text_encoders"}]},
         "widgets_values": ["gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors",
                            "ltxv", "default"]},
        {"id": 15, "type": "CLIPTextEncode",
         "inputs": [{"name": "clip", "link": None}, _w("text")],
         "outputs": [{"name": "CONDITIONING", "links": [21]}],
         "widgets_values": ["pc game, console game, video game, cartoon, ugly"]},
        {"id": 16, "type": "CFGGuider",
         "inputs": [{"name": "model", "link": None}, {"name": "positive", "link": None},
                    {"name": "negative", "link": 21}], "widgets_values": [1]},
    ]
    enlaces = [_l(1, -10, 10, 0), _l(2, -10, 11, 0), _l(3, -10, 12, 0),
               _l(4, -10, 13, 0), _l(5, -10, 14, 0), _l(21, 15, 16, 2)]
    entradas = [{"name": "text", "type": "STRING", "linkIds": [1]},
                {"name": "value", "type": "BOOLEAN", "linkIds": [2]},
                {"name": "value_1", "type": "INT", "linkIds": [3]},
                {"name": "unet_name", "type": "COMBO", "linkIds": [4]},
                {"name": "clip_name", "type": "COMBO", "linkIds": [5]},
                {"name": "image", "type": "IMAGE", "linkIds": []},
                {"name": "width", "type": "INT", "linkIds": []}]
    instancia = {"id": 1, "type": sg, "pos": [0, 0],
                 "inputs": [_w("width", 30)],
                 "widgets_values": ["An arctic hunter, the template's own example " * 2,
                                    True, 5,
                                    "ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors",
                                    "gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors",
                                    1280]}
    selector = {"id": 2, "type": "ResolutionSelector", "pos": [-300, 0],
                "widgets_values": ["16:9 (Widescreen)", 0.9, 32]}
    return {"last_node_id": 20, "nodes": [instancia, selector],
            "links": [[30, 2, 0, 1, 0, "INT"]],
            "definitions": {"subgraphs": [{"id": sg, "name": "T2V", "inputs": entradas,
                                           "nodes": dentro, "links": enlaces}]}}


def _proxy():
    """Como Wan 2.2 t2v: el nodo exterior no guarda nada; los valores viven
    dentro aunque estén conectados a la entrada del subgrafo."""
    sg = "bbbbbbbb-0000-4000-8000-000000000002"
    dentro = [
        {"id": 89, "type": "CLIPTextEncode", "title": "CLIP Text Encode (Positive Prompt)",
         "inputs": [{"name": "clip", "link": 160}, _w("text", 214)],
         "widgets_values": ["Beautiful young woman turning her head, the example " * 2]},
        {"id": 72, "type": "CLIPTextEncode", "title": "CLIP Text Encode (Negative Prompt)",
         "inputs": [{"name": "clip", "link": 161}, _w("text")],
         "widgets_values": ["色调艳丽，过曝，静态"]},
        {"id": 75, "type": "UNETLoader", "inputs": [_w("unet_name", 215), _w("weight_dtype")],
         "widgets_values": ["wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors", "default"]},
        {"id": 76, "type": "UNETLoader", "inputs": [_w("unet_name", 216), _w("weight_dtype")],
         "widgets_values": ["wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors", "default"]},
        {"id": 74, "type": "EmptyHunyuanLatentVideo",
         "inputs": [_w("width", 217), _w("height", 218), _w("length"), _w("batch_size")],
         "widgets_values": [640, 640, 81, 1]},
        {"id": 126, "type": "PrimitiveFloat", "title": "Float (Duration)",
         "inputs": [_w("value")], "widgets_values": [5]},
    ]
    enlaces = [_l(214, -10, 89, 1), _l(215, -10, 75, 0), _l(216, -10, 76, 0),
               _l(217, -10, 74, 0), _l(218, -10, 74, 1), _l(160, 71, 89, 0), _l(161, 71, 72, 0)]
    instancia = {"id": 128, "type": sg, "pos": [0, 0], "inputs": [], "widgets_values": [],
                 "properties": {"proxyWidgets": [["89", "text"], ["74", "width"],
                                                 ["74", "height"], ["75", "unet_name"],
                                                 ["76", "unet_name"]]}}
    return {"last_node_id": 200, "nodes": [instancia], "links": [],
            "definitions": {"subgraphs": [{"id": sg, "name": "Wan", "nodes": dentro,
                                           "links": enlaces,
                                           "inputs": [{"name": "text", "type": "STRING",
                                                       "linkIds": [214]}]}]}}


@pytest.fixture
def plantillas(tmp_path):
    carpeta = tmp_path / "templates"
    carpeta.mkdir()
    (carpeta / "video_ltx2_5_t2v.json").write_text(json.dumps(_clasica()), encoding="utf-8")
    (carpeta / "video_wan2_2_14B_t2v.json").write_text(json.dumps(_proxy()), encoding="utf-8")
    (carpeta / "video_wan2_2_14B_i2v.json").write_text(
        json.dumps(_proxy()).replace("_t2v_", "_i2v_"), encoding="utf-8")
    return [carpeta]


def _nodo(wf, nid):
    for cont in [wf, *wf["definitions"]["subgraphs"]]:
        for n in cont["nodes"]:
            if n["id"] == nid:
                return n
    raise KeyError(nid)


class TestPlantillaClasica:

    def _hacer(self, plantillas, modelo="LTX-2.5-Distilled-Q3_K_M"):
        r = cv.construir_workflow_video(modelo, PROMPT, NEG, "9:16", 8, False,
                                        plantillas, NOMBRES)
        return r, r["workflow"]

    def test_prompt_duracion_y_mejorador_en_el_nodo_exterior(self, plantillas):
        _r, wf = self._hacer(plantillas)
        valores = _nodo(wf, 1)["widgets_values"]
        assert valores[0] == PROMPT
        assert valores[1] is False            # el mejorador de prompt, apagado
        assert valores[2] == 8                # la duración, entera como en la plantilla

    def test_el_gguf_entra_con_su_cargador(self, plantillas):
        _r, wf = self._hacer(plantillas)
        assert _nodo(wf, 1)["widgets_values"][3] == "LTX-2.5-Distilled-Q3_K_M.gguf"
        cargador = _nodo(wf, 13)
        assert cargador["type"] == "UnetLoaderGGUF"
        assert [i["name"] for i in cargador["inputs"]] == ["unet_name"]
        # También dentro: con el fichero viejo, ComfyUI lo daba por ausente.
        assert cargador["widgets_values"] == ["LTX-2.5-Distilled-Q3_K_M.gguf"]
        assert _nodo(wf, 10)["widgets_values"] == [PROMPT]

    def test_el_codificador_en_la_precision_que_tienes(self, plantillas):
        r, wf = self._hacer(plantillas)
        assert _nodo(wf, 1)["widgets_values"][4] == "gemma4-12b-with-proj-ltx-2.5-nvfp4.safetensors"
        assert r["faltan"] == []

    def test_sin_descarga_del_fichero_sustituido(self, plantillas):
        # Las plantillas llevan el enlace de su fichero en properties.models:
        # si se queda, ComfyUI pide bajar un modelo que ya no se usa.
        _r, wf = self._hacer(plantillas)
        assert _nodo(wf, 14)["properties"]["models"] == []

    def test_negativo_por_su_conexion_y_formato_en_el_selector(self, plantillas):
        _r, wf = self._hacer(plantillas)
        assert _nodo(wf, 15)["widgets_values"][0] == NEG
        assert _nodo(wf, 2)["widgets_values"][0] == "9:16 (Portrait Widescreen)"
        # El ancho lo da el selector: el valor guardado no se toca.
        assert _nodo(wf, 1)["widgets_values"][5] == 1280

    def test_la_entrada_curada_usa_tu_fichero(self, plantillas):
        r, _wf = self._hacer(plantillas, "LTX 2.5")
        assert r["fichero"] == "LTX-2.5-Distilled-Q3_K_M.gguf"

    def test_deja_una_nota(self, plantillas):
        _r, wf = self._hacer(plantillas)
        nota = wf["nodes"][-1]
        assert nota["type"] == "Note" and nota["id"] == wf["last_node_id"] == 21
        assert "video_ltx2_5_t2v" in nota["widgets_values"][0]


class TestPlantillaProxy:

    def _hacer(self, plantillas, modelo="wan2.2_t2v_high_noise_14B_fp16", con_imagen=False):
        r = cv.construir_workflow_video(modelo, PROMPT, NEG, "9:16", 8, con_imagen,
                                        plantillas, NOMBRES)
        return r, r["workflow"]

    def test_prompt_y_negativo_dentro(self, plantillas):
        _r, wf = self._hacer(plantillas)
        assert _nodo(wf, 89)["widgets_values"][0] == PROMPT
        assert _nodo(wf, 72)["widgets_values"][0] == NEG

    def test_la_pareja_high_low(self, plantillas):
        # Elige el high en fp16; el low no lo tiene en fp16, sí en fp8.
        _r, wf = self._hacer(plantillas)
        assert _nodo(wf, 75)["widgets_values"][0] == \
            "LoraLab-D\\wan2.2_t2v_high_noise_14B_fp16.safetensors"
        assert _nodo(wf, 76)["widgets_values"][0] == \
            "LoraLab-D\\wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors"

    def test_formato_y_duracion(self, plantillas):
        _r, wf = self._hacer(plantillas)
        w, h = _nodo(wf, 74)["widgets_values"][:2]
        assert h > w and w % 32 == 0 and h % 32 == 0
        assert abs(w * h - 640 * 640) / (640 * 640) < 0.05   # los mismos píxeles
        assert _nodo(wf, 126)["widgets_values"][0] == 8.0

    def test_con_imagen_un_t2v_no_entra_en_la_plantilla_i2v(self, plantillas):
        r, wf = self._hacer(plantillas, con_imagen=True)
        assert r["plantilla"] == "video_wan2_2_14B_i2v"
        assert _nodo(wf, 75)["widgets_values"][0] == "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
        assert any("texto a vídeo" in a for a in r["avisos"])
        assert "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" in r["faltan"]


class TestRamasApagadas:
    """ComfyUI valida también las ramas apagadas: sin el codificador del
    mejorador de LTX 2.5 (gemma4_e2b), rechazaba el workflow entero aunque el
    mejorador fuera apagado (18-oct-2026, validado contra su ComfyUI)."""

    def _con_mejorador(self):
        wf = _clasica()
        sg = wf["definitions"]["subgraphs"][0]
        sg["nodes"] += [
            {"id": 17, "type": "CLIPLoader", "inputs": [_w("clip_name")],
             "outputs": [{"name": "CLIP", "links": [40]}],
             "widgets_values": ["gemma4_e2b_it_int8_convrot.safetensors", "ltxv", "default"]},
            {"id": 18, "type": "TextGenerateLTX2Prompt",
             "inputs": [{"name": "clip", "link": 40}], "widgets_values": [""]},
        ]
        sg["links"].append(_l(40, 17, 18, 0))
        return wf

    def test_el_codificador_del_mejorador_se_cambia_por_uno_parecido(self, tmp_path):
        (tmp_path / "video_ltx2_5_t2v.json").write_text(json.dumps(self._con_mejorador()),
                                                        encoding="utf-8")
        nombres = dict(NOMBRES, text_encoders=NOMBRES["text_encoders"]
                       + ["gemma4_e4b_it_fp8_scaled.safetensors", "umt5_xxl_fp8.safetensors"])
        r = cv.construir_workflow_video("LTX-2.5-Distilled-Q3_K_M", PROMPT, carpetas=[tmp_path],
                                        nombres=nombres)
        assert _nodo(r["workflow"], 17)["widgets_values"][0] == "gemma4_e4b_it_fp8_scaled.safetensors"
        assert r["faltan"] == [] and "va apagada" in r["avisos"][0]

    def test_en_una_rama_activa_no_se_inventa_nada(self, plantillas):
        # El codificador principal que falta se queda y se avisa.
        nombres = {"diffusion_models": NOMBRES["diffusion_models"],
                   "text_encoders": ["gemma4_e4b_it_fp8_scaled.safetensors"]}
        r = cv.construir_workflow_video("LTX-2.5-Distilled-Q3_K_M", PROMPT, carpetas=plantillas,
                                        nombres=nombres)
        assert r["faltan"] == ["gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors"]


class TestErrores:

    def test_modelo_sin_plantilla(self, plantillas):
        assert cv.construir_workflow_video("svd_xt", PROMPT, carpetas=plantillas)["error"] == \
            "sin_plantilla"

    def test_comfyui_sin_esa_plantilla(self, plantillas):
        r = cv.construir_workflow_video("wan2.2_ti2v_5B_fp16", PROMPT, carpetas=plantillas)
        assert r == {"error": "plantilla_no_encontrada", "plantilla": "video_wan2_2_5B_ti2v"}


@pytest.mark.parametrize("modelo, plantilla", [
    ("LTX 2.5", "video_ltx2_5_t2v"),
    ("LTX-2.5-Distilled-Q3_K_M", "video_ltx2_5_t2v"),
    ("ltx-2.3-22b-distilled-Q4_0", "video_ltx2_3_t2v"),
    ("minimax_h3_fl2va_pruned_int8_convrot", "video_minimax_h3_t2v"),
    ("minimax_h3_ref2va_pruned_int8_convrot", "video_minimax_h3_r2v"),
    ("Minimax-h3_Singularity_ref2va_Pruned_v1.3_int8", "video_minimax_h3_r2v"),
    ("wan2.1_t2v_1.3B_bf16", "text_to_video_wan"),
    ("wan2.1_14B_SCAIL_2_int8_convrot", "video_wan21_scail2_character_replacement_int8"),
    ("Wan2.2-Animate-14B-Q5_K_M", "video_wan_animate2"),
    ("wan_animate_2_int8_convrot", "video_wan_animate2"),
    ("wan2.2_bernini_r_high_noise_fp8_scaled", "video_bernini_r_video_editing"),
    ("wan2.2_fun_camera_low_noise_14B_fp8_scaled", "video_wan2_2_14B_fun_camera"),
    ("wan2.2_fun_control_5B_bf16", "video_wan2_2_5B_fun_control"),
    ("wan2.2_fun_control_high_noise_14B_fp8_scaled", "video_wan2_2_14B_fun_control"),
    ("wan2.2_s2v_14B_fp8_scaled", "video_wan2_2_14B_s2v"),
    ("wan2.2_ti2v_5B_fp16", "video_wan2_2_5B_ti2v"),
    ("wan2.2_i2v_high_noise_14B_fp16", "video_wan2_2_14B_i2v"),
    ("wan2.2_t2v_low_noise_14B_fp8_scaled", "video_wan2_2_14B_t2v"),
    ("kandinsky5lite_t2v_sft_5s", "video_kandinsky5_t2v"),
    ("kandinsky5lite_i2v_5s", "video_kandinsky5_i2v"),
])
def test_cada_modelo_del_autor_tiene_su_plantilla(modelo, plantilla):
    # Los 30 modelos de vídeo del equipo del autor (18-oct-2026), por familia.
    assert cv.plantilla_para(modelo) == plantilla


def test_los_puntos_del_nombre_no_son_extension():
    assert cv._sin_ext("ltx-2.3-22b-distilled-Q4_0") == "ltx-2.3-22b-distilled-Q4_0"
    assert cv._sin_ext("LoraLab-D\\LTX-2.5-Distilled-Q3_K_M.gguf") == "LTX-2.5-Distilled-Q3_K_M"


def test_encuentra_las_plantillas_en_el_python_de_comfyui(tmp_path):
    carpeta = (tmp_path / "ComfyUI" / "venv" / "Lib" / "site-packages"
               / "comfyui_workflow_templates_media_video" / "templates")
    carpeta.mkdir(parents=True)
    assert cv.carpetas_plantillas(str(tmp_path / "ComfyUI")) == [carpeta]
    assert cv.carpetas_plantillas("") == []
