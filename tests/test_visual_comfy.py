"""«Crear desde imágenes» con los modelos de vídeo de tu ComfyUI.

18-oct-2026: el ref2va de MiniMax H3 pide varias imágenes de referencia y la
ventana principal solo carga una. El usuario pidió hacerlo desde «Crear desde
imágenes», que ya tiene varias referencias con su función. Faltaba que ese
panel:
  • aceptara hasta 9 imágenes con el ref2va de destino (4 con el resto);
  • escribiera el prompt con las reglas del formato del modelo, las mismas
    de la ventana principal, con A = <Picture 1>, B = <Picture 2>…;
  • tuviera su botón «🔧 Workflow ComfyUI», que mete esas imágenes en los
    Load Image, en su orden (y en «Inicio → final», B en el last_frame del
    fl2va).

El CI no tiene ComfyUI: plantillas sintéticas.
"""
import json
from types import SimpleNamespace

import pytest
from PIL import Image

import config
from modules import comfy_video as cv
from modules.prompts_inyeccion import planos_por_duracion, reglas_minimax_h3
from modules.visual_brief import (
    MAX_REFS_AMPLIADO,
    MODES,
    ROLES,
    Reference,
    analysis_input,
    generation_request,
    load_project,
    pista_minimax,
    save_project,
    validate,
)
from tests.test_comfy_video_refs import LARGO, _cargas, _r2v

R2V = "Minimax-h3_Singularity_ref2va_Pruned_v1.3_int8"
FL2VA = "minimax_h3_fl2va_pruned_int8_convrot"
WAN_I2V = "wan2.2_i2v_high_noise_14B_fp16"


def referencias(n):
    return [Reference(Image.new("RGB", (64, 48), (25 * i, 0, 0)), ROLES[i % len(ROLES)],
                      f"ref-{i}.png") for i in range(n)]


class TestHastaNueve:

    def test_por_defecto_siguen_siendo_cuatro(self):
        with pytest.raises(ValueError, match="cuatro"):
            validate(MODES[3], referencias(5))

    def test_con_el_ref2va_hasta_nueve(self):
        validate(MODES[3], referencias(9), MAX_REFS_AMPLIADO)
        with pytest.raises(ValueError, match="9"):
            validate(MODES[3], referencias(10), MAX_REFS_AMPLIADO)

    def test_el_panel_de_analisis_pasa_a_tres_columnas(self):
        panel, texto = analysis_input(MODES[3], referencias(9), MAX_REFS_AMPLIADO)
        assert panel.size == (1600, 3 * (1600 // 3 + 40))
        assert "Hay exactamente 9" in texto and "I: " in texto
        # Hasta cuatro, como siempre.
        assert analysis_input(MODES[3], referencias(4))[0].size == (1600, 2 * 840)

    def test_el_proyecto_guarda_las_nueve(self, tmp_path):
        ruta = tmp_path / "nueve.gprompt"
        save_project(ruta, referencias(9), {"mode": MODES[3], "aspect": "9:16",
                                            "language": "Inglés", "target": "Vídeo"})
        refs, _campos = load_project(ruta)
        assert [r.name for r in refs] == [f"ref-{i}.png" for i in range(9)]


class TestFormatoDeMiniMax:

    def test_el_ref2va_numera_por_letra_y_funcion(self):
        pista = pista_minimax(MODES[3], referencias(3), True, True)
        assert "<Picture 1> = A (Personaje)" in pista
        assert "<Picture 3> = C (Escenario)" in pista
        assert "No inventes <Video N>" in pista

    def test_el_ref2va_en_animar_e_inicio_final(self):
        assert "first frame of [Shot 1]" in pista_minimax(MODES[1], referencias(1), True, True)
        dos = pista_minimax(MODES[2], referencias(2), True, True)
        assert "PRIMER" in dos and "ÚLTIMO" in dos and "[keyframe completion]" in dos

    def test_el_fl2va_es_i2va_o_fl2va(self):
        assert "I2VA" in pista_minimax(MODES[1], referencias(1), True, False)
        assert "FL2VA" in pista_minimax(MODES[2], referencias(2), True, False)

    def test_solo_texto_no_usa_etiquetas(self):
        assert "no uses etiquetas <Picture N>" in pista_minimax(MODES[3], referencias(2), False, True)
        assert "T2VA" in pista_minimax(MODES[1], referencias(1), False, False)

    def test_las_reglas_llevan_la_pista(self):
        ref = reglas_minimax_h3(R2V, config.comfy_video_specs(R2V), 8, planos_por_duracion(8),
                                False, "PISTA-REF")
        assert "PISTA-REF" in ref and "subject_definitions" in ref and "350-500" in ref
        base = reglas_minimax_h3(FL2VA, config.comfy_video_specs(FL2VA), 6, 2, False, "PISTA-BASE")
        assert "PISTA-BASE" in base and "integrated_multimodal_description" in base

    def test_planos_por_duracion(self):
        assert [planos_por_duracion(s) for s in (4, 5, 10, 15, 24)] == [1, 2, 3, 4, 6]

    def test_la_peticion_lleva_el_formato_del_modelo(self):
        args = (MODES[3], referencias(3), "análisis", "idea", "", "", "8", "16:9", "Inglés",
                "DESTINO", True, "Vídeo", True, MAX_REFS_AMPLIADO)
        con = generation_request(*args, "REGLAS-MINIMAX")
        assert "FORMATO PROPIO DEL MODELO" in con and con.endswith("REGLAS-MINIMAX")
        assert "SIN la etiqueta «PROMPT:»" in con
        assert "FORMATO PROPIO" not in generation_request(*args)


def _i2v(ultimo="last_frame"):
    """Como video_minimax_h3_i2v: un Load Image al first_frame y el
    last_frame libre."""
    carga = {"id": 114, "type": "LoadImage", "pos": [0, 0], "mode": 0, "inputs": [],
             "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [218]},
                         {"name": "MASK", "type": "MASK", "links": None}],
             "widgets_values": ["mouse.png", "image"]}
    nodo = {"id": 105, "type": "MiniMaxH3ImageToVideo", "pos": [400, 0], "mode": 0,
            "inputs": [{"name": "first_frame", "type": "IMAGE", "shape": 7, "link": 218},
                       {"name": ultimo, "type": "IMAGE", "shape": 7, "link": None}],
            "outputs": []}
    prompt = {"id": 7, "type": "PrimitiveStringMultiline", "title": "Prompt", "pos": [0, -200],
              "mode": 0, "inputs": [], "outputs": [{"name": "STRING", "links": []}],
              "widgets_values": [LARGO]}
    return {"last_node_id": 120, "last_link_id": 300, "nodes": [carga, nodo, prompt],
            "links": [[218, 114, 0, 105, 0, "IMAGE"]]}


class TestEnLaPlantilla:

    def test_lo_que_admite_cada_modelo(self):
        assert cv.capacidades(R2V) == {"image_reference": True, "multi_reference": True,
                                       "start_end": True}
        assert cv.capacidades(FL2VA) == {"image_reference": True, "multi_reference": False,
                                         "start_end": True}
        assert cv.capacidades(WAN_I2V) == {"image_reference": True, "multi_reference": False,
                                           "start_end": False}
        assert cv.capacidades("Juggernaut-XL_v9") is None

    def test_el_formato_mas_parecido(self):
        # Con 4:5 se quedaba el 16:9 de la plantilla.
        assert cv._aspecto("4:5") == "3:4 (Portrait Standard)"
        assert cv._aspecto("9:16") == "9:16 (Portrait Widescreen)"
        assert cv._aspecto("Libre") is None

    @pytest.fixture
    def plantillas(self, tmp_path):
        carpeta = tmp_path / "templates"
        carpeta.mkdir()
        (carpeta / "video_minimax_h3_i2v.json").write_text(json.dumps(_i2v()), encoding="utf-8")
        (carpeta / "video_ltx2_5_i2v.json").write_text(json.dumps(_i2v("input")), encoding="utf-8")
        return [carpeta]

    def test_inicio_y_final_en_el_fl2va(self, plantillas):
        r = cv.construir_workflow_video(FL2VA, "<Picture 1> to <Picture 2>", con_imagen=True,
                                        carpetas=plantillas, refs={"imagen": ["a.png", "b.png"]},
                                        inicio_final=True)
        wf = r["workflow"]
        assert [n["widgets_values"][0] for n in _cargas(wf)] == ["a.png", "b.png"]
        nodo = next(n for n in wf["nodes"] if n["id"] == 105)
        ultimo = next(i for i in nodo["inputs"] if i["name"] == "last_frame")
        assert [lk for lk in wf["links"] if lk[0] == ultimo["link"]][0][1] == _cargas(wf)[1]["id"]
        assert r["huecos"][-1]["etiqueta"] == "(last_frame)"

    def test_sin_inicio_final_va_solo_la_primera(self, plantillas):
        r = cv.construir_workflow_video(FL2VA, "x", con_imagen=True, carpetas=plantillas,
                                        refs={"imagen": ["a.png", "b.png"]})
        assert [n["widgets_values"][0] for n in _cargas(r["workflow"])] == ["a.png"]

    def test_avisa_si_la_plantilla_no_tiene_ultimo_fotograma(self, plantillas):
        r = cv.construir_workflow_video("LTX 2.5", "x", con_imagen=True, carpetas=plantillas,
                                        refs={"imagen": ["a.png", "b.png"]}, inicio_final=True)
        assert any("último fotograma" in a for a in r["avisos"])


class TestElBotonDelPanel:
    """ToolsAnalysisService.workflow_video_comfy con las imágenes del panel."""

    def test_las_imagenes_entran_en_orden(self, tmp_path, monkeypatch):
        base = tmp_path / "ComfyUI"
        plantillas = (base / "venv" / "Lib" / "site-packages"
                      / "comfyui_workflow_templates_media_video" / "templates")
        plantillas.mkdir(parents=True)
        (base / "input").mkdir()
        (plantillas / "video_minimax_h3_r2v.json").write_text(json.dumps(_r2v()), encoding="utf-8")
        monkeypatch.setattr(config, "ruta_comfyui", lambda: str(base))
        monkeypatch.setattr(config, "nombres_modelos_comfy", lambda: {})
        from modules.tools_analysis import ToolsAnalysisService
        svc = ToolsAnalysisService(SimpleNamespace())
        mostrado = []
        svc._mostrar_ventana_comfyui = lambda js, modelo, chuleta=None, parent=None: mostrado.append(
            (json.loads(js), parent))
        svc._pedir_ficheros_comfy = lambda *a, **k: pytest.fail("no tenía que pedir nada")
        panel = SimpleNamespace(status=SimpleNamespace(set=lambda texto: None))
        imagenes = [(Image.new("RGB", (8, 8), color), None, f"{nombre}.png")
                    for color, nombre in (("red", "ana"), ("blue", "perro"), ("green", "casa"))]
        prompt = "<Picture 1> is Ana, <Picture 2> her dog, <Picture 3> the house."
        assert svc.workflow_video_comfy(R2V, prompt, "", "16:9", 8, imagenes, parent=panel) is True
        wf, parent = mostrado[0]
        nombres = [n["widgets_values"][0] for n in _cargas(wf)]
        assert [n.split("_")[1] for n in nombres] == ["ana", "perro", "casa"]
        assert all((base / "input" / n).is_file() for n in nombres)
        assert parent is panel


class TestElPanel:
    """La ventana de verdad (Tk), con el catálogo de ComfyUI del usuario."""

    @pytest.fixture
    def panel(self, tk_root, monkeypatch):
        from modules import visual_studio as vs
        from tests._bombeo import bombear
        monkeypatch.setattr(vs, "MODELOS_POR_PLATAFORMA_VIDEO", {
            "SeaArt Video": ["Kling 3.0"], "ComfyUI / Fooocus": [R2V, WAN_I2V]})
        v = vs.VisualStudio(tk_root)
        bombear(tk_root, 120)
        v.mode.set(MODES[3])
        v.target.set("Vídeo")
        v.refresh_destination()
        v.platform.set("ComfyUI / Fooocus")
        v.refresh_models()
        v.model.set(R2V)
        v.model_changed()
        yield v
        v.destroy()

    def test_el_ref2va_admite_nueve_y_adjunta_las_imagenes(self, panel):
        assert panel.max_refs() == 9
        assert panel.reference_use.get() == "Adjuntar imágenes"
        panel.refs = referencias(3)
        panel.render()
        texto = panel.reference_hint.cget("text")
        assert "A = <Picture 1> · B = <Picture 2> · C = <Picture 3>" in texto
        # La plantilla lo confirma: sin casilla de «He comprobado…».
        assert not panel.confirm_checkbox.winfo_manager()
        # Y el paso 3 está en la barra de abajo.
        assert panel.comfy_button.winfo_manager()

    def test_con_otro_modelo_vuelven_a_ser_cuatro(self, panel):
        panel.model.set(WAN_I2V)
        panel.model_changed()
        assert panel.max_refs() == 4

    def test_el_boton_manda_las_imagenes_en_orden(self, panel, tk_root, monkeypatch):
        llamadas = []
        monkeypatch.setattr(tk_root, "analysis", SimpleNamespace(
            workflow_video_comfy=lambda *a, **k: llamadas.append((a, k)) or True), raising=False)
        panel.refs = referencias(3)
        panel.output.insert("1.0", "<Picture 1> <Picture 2> <Picture 3>")
        panel.duration.set("8")
        panel.comfy_workflow()
        (modelo, prompt, _neg, _formato, segundos, imagenes), k = llamadas[0]
        assert modelo == R2V and segundos == 8.0 and prompt.startswith("<Picture 1>")
        assert [nombre for _img, _ruta, nombre in imagenes] == ["ref-0.png", "ref-1.png", "ref-2.png"]
        assert k == {"inicio_final": False, "parent": panel}
        assert "pulsa R" in panel.status.get()

    def test_sin_comfyui_lo_dice(self, panel):
        panel.platform.set("SeaArt Video")
        panel.refresh_models()
        panel.output.insert("1.0", "prompt")
        panel.comfy_workflow()
        assert "ComfyUI / Fooocus" in panel.status.get()
        assert not panel.comfy_button.winfo_manager()
