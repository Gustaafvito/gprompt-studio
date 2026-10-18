"""Tus ficheros en los Load Image / Video / Audio del workflow de vídeo.

18-oct-2026: el usuario generó el prompt para el MiniMax H3 ref2va
(Singularity) sin imágenes, y el workflow de 🔧 Comfy salió con las dos de
ejemplo de la plantilla (un superhéroe y un dragón) y sin forma de saber que
ese modelo parte de referencias. Ahora la app lo avisa en la ficha del modelo,
copia la imagen cargada a la carpeta input de ComfyUI y la pone en su Load
Image, pide lo que falte (el vídeo de Animate, el audio de S2V…) y, en el
ref2va, deja tantas imágenes como <Picture N> nombre el prompt.

Plantillas sintéticas: el CI no tiene ComfyUI.
"""
import json
from types import SimpleNamespace

import pytest
from PIL import Image

from modules import comfy_video as cv

LARGO = "An example prompt from the template, long enough to be found " * 2


def _carga(nid, tipo, fichero, link, modo=0, pos=(0, 0)):
    salida = {"IMAGE": "IMAGE", "VIDEO": "VIDEO", "AUDIO": "AUDIO"}
    clase = {"LoadImage": "IMAGE", "LoadVideo": "VIDEO", "LoadAudio": "AUDIO"}[tipo]
    outs = [{"name": clase, "type": salida[clase], "links": [link]}]
    if tipo == "LoadImage":
        outs.append({"name": "MASK", "type": "MASK", "links": None})
    clave = {"LoadImage": "image", "LoadVideo": "file", "LoadAudio": "audio"}[tipo]
    return {"id": nid, "type": tipo, "pos": list(pos), "mode": modo, "inputs": [],
            "outputs": outs, "properties": {"Node name for S&R": tipo},
            "widgets_values": [fichero, "image"],
            "widgets_values_named": {clave: fichero, "upload": "image"}}


def _r2v():
    """Como video_minimax_h3_r2v: dos Load Image a las entradas que crecen."""
    def ref(n, link):
        return {"label": f"ref_image_{n}", "name": f"ref_images.ref_image_{n}",
                "shape": 7, "type": "IMAGE", "link": link}
    nodo = {"id": 136, "type": "MiniMaxH3ReferenceToVideo", "pos": [0, 0], "mode": 0,
            "inputs": [{"name": "clip", "type": "CLIP", "link": 272},
                       ref(0, 278), ref(1, 282), ref(2, None),
                       {"name": "ref_videos.ref_video_0", "shape": 7, "type": "IMAGE",
                        "link": None},
                       {"name": "prompt", "type": "STRING", "link": 279,
                        "widget": {"name": "prompt"}}],
            "outputs": [{"name": "positive", "type": "CONDITIONING", "links": []}]}
    prompt = {"id": 138, "type": "PrimitiveStringMultiline", "title": "Prompt",
              "pos": [0, -300], "mode": 0, "inputs": [{"name": "value", "widget": {"name": "value"},
                                                       "link": None}],
              "outputs": [{"name": "STRING", "type": "STRING", "links": [279]}],
              "widgets_values": [LARGO], "widgets_values_named": {"value": LARGO}}
    clip = {"id": 128, "type": "CLIPLoader", "pos": [0, 300], "mode": 0, "inputs": [],
            "outputs": [{"name": "CLIP", "type": "CLIP", "links": [272]}],
            "widgets_values": ["qwen3vl.safetensors", "minimax_h3", "default"]}
    return {"last_node_id": 146, "last_link_id": 291,
            "nodes": [nodo, prompt, clip,
                      _carga(137, "LoadImage", "red_superboy_on_city_roof.png", 278, pos=(-1050, 0)),
                      _carga(139, "LoadImage", "mecha_dragon_lightning.png", 282, pos=(-700, 0))],
            "links": [[272, 128, 0, 136, 0, "CLIP"], [278, 137, 0, 136, 1, "IMAGE"],
                      [282, 139, 0, 136, 2, "IMAGE"], [279, 138, 0, 136, 5, "STRING"]]}


def _con_positivo(cargas, enlaces):
    """Un prompt que entra en «positive», más las cargas que se pasen."""
    texto = {"id": 6, "type": "CLIPTextEncode", "pos": [0, 0], "mode": 0,
             "inputs": [{"name": "clip", "link": None}, {"name": "text", "widget": {"name": "text"},
                                                         "link": None}],
             "outputs": [{"name": "CONDITIONING", "links": [900]}], "widgets_values": [LARGO]}
    destino = {"id": 50, "type": "WanAnimateToVideo", "pos": [400, 0], "mode": 0,
               "inputs": [{"name": "positive", "link": 900},
                          *({"name": f"entrada_{lid}", "shape": 7, "link": lid} for lid in enlaces)],
               "outputs": []}
    links = [[900, 6, 0, 50, 0, "CONDITIONING"]]
    links += [[lid, c["id"], 0, 50, 1 + i, "*"] for i, (lid, c) in enumerate(zip(enlaces, cargas))]
    return {"last_node_id": 200, "last_link_id": 900, "nodes": [texto, destino, *cargas],
            "links": links}


def _animate():
    """Como video_wan_animate2 y Fun Control 14B: imagen y vídeo, y la imagen
    repetida en un grupo apagado (mode 4) con el mismo fichero."""
    cargas = [_carga(189, "LoadImage", "pink_hair_ref.png", 993),
              _carga(240, "LoadVideo", "street_dance.mp4", 970),
              _carga(178, "LoadImage", "pink_hair_ref.png", 994, modo=4)]
    return _con_positivo(cargas, [993, 970, 994])


def _ti2v():
    """Como video_wan2_2_5B_ti2v: la imagen es opcional y viene apagada."""
    return _con_positivo([_carga(56, "LoadImage", "example.png", 106, modo=4)], [106])


@pytest.fixture
def plantillas(tmp_path):
    carpeta = tmp_path / "templates"
    carpeta.mkdir()
    for nombre, wf in (("video_minimax_h3_r2v", _r2v()), ("video_wan_animate2", _animate()),
                       ("video_wan2_2_5B_ti2v", _ti2v())):
        (carpeta / f"{nombre}.json").write_text(json.dumps(wf), encoding="utf-8")
    return [carpeta]


R2V = "Minimax-h3_Singularity_ref2va_Pruned_v1.3_int8"
ANIMATE = "wan_animate_2_int8_convrot"
TI2V = "wan2.2_ti2v_5B_fp16"


def _cargas(wf, tipo="LoadImage"):
    return [n for n in wf["nodes"] if n["type"] == tipo]


def _coherente(wf):
    """Cada conexión, en los dos extremos; ids sin repetir."""
    nodos = {n["id"]: n for n in wf["nodes"]}
    ids = [lk[0] for lk in wf["links"]]
    assert len(ids) == len(set(ids))
    for lid, origen, _os, destino, slot, _t in wf["links"]:
        assert nodos[destino]["inputs"][slot]["link"] == lid
        assert any(lid in (o.get("links") or []) for o in nodos[origen]["outputs"])
    for n in wf["nodes"]:
        for i in n.get("inputs", []):
            if i.get("link") is not None:
                assert i["link"] in ids, (n["id"], i["name"])
    assert wf["last_link_id"] >= max(ids) and wf["last_node_id"] >= max(nodos)


class TestRef2vaDeMiniMax:

    def test_una_imagen_tuya_y_fuera_la_de_ejemplo_que_sobra(self, plantillas):
        r = cv.construir_workflow_video(
            R2V, "<Subject 1> is the woman in <Picture 1>.", carpetas=plantillas,
            refs={"imagen": ["gprompt_ana_1234567890.png"]})
        wf = r["workflow"]
        assert [n["widgets_values"][0] for n in _cargas(wf)] == ["gprompt_ana_1234567890.png"]
        assert _cargas(wf)[0]["widgets_values_named"]["image"] == "gprompt_ana_1234567890.png"
        # El dragón de ejemplo se metería en tu vídeo: fuera, con su conexión.
        assert "mecha_dragon_lightning.png" not in json.dumps(wf)
        _coherente(wf)
        assert r["huecos"] == [{"tipo": "imagen", "n": 1, "ejemplo": "red_superboy_on_city_roof.png",
                                "fichero": "gprompt_ana_1234567890.png", "opcional": False,
                                "etiqueta": "<Picture 1>"}]

    def test_tantas_imagenes_como_nombra_el_prompt(self, plantillas):
        prompt = ("<Subject 1> is the woman in <Picture 1>. <Subject 2> is the dog in "
                  "<Picture 2>. <Picture 4> is the first frame. <Picture 3> is the house.")
        r = cv.construir_workflow_video(R2V, prompt, carpetas=plantillas,
                                        refs={"imagen": ["a.png", None, "c.png"]})
        wf = r["workflow"]
        nodo = next(n for n in wf["nodes"] if n["id"] == 136)
        refs = [i["name"] for i in nodo["inputs"] if i["name"].startswith("ref_images.")]
        # La plantilla trae 3 entradas; la cuarta se crea, y las de detrás se corren.
        assert refs == [f"ref_images.ref_image_{k}" for k in range(4)]
        _coherente(wf)
        assert [h["fichero"] for h in r["huecos"]] == ["a.png", None, "c.png", None]
        assert [h["etiqueta"] for h in r["huecos"]] == [f"<Picture {k}>" for k in range(1, 5)]
        assert len(_cargas(wf)) == 4

    def test_no_pasa_de_nueve(self, plantillas):
        r = cv.construir_workflow_video(R2V, "<Picture 12> is a frame.", carpetas=plantillas)
        assert len(_cargas(r["workflow"])) == 9
        _coherente(r["workflow"])

    def test_sin_imagen_queda_una_por_poner(self, plantillas):
        r = cv.construir_workflow_video(R2V, LARGO, carpetas=plantillas)
        assert [(h["n"], h["fichero"], h["opcional"]) for h in r["huecos"]] == [(1, None, False)]
        nota = next(n for n in r["workflow"]["nodes"] if n["type"] == "Note")
        assert "red_superboy_on_city_roof.png" in nota["widgets_values"][0]

    def test_los_valores_por_nombre_tambien_llevan_lo_nuestro(self, plantillas):
        # El JSON del usuario enseñaba en widgets_values_named el prompt de
        # ejemplo de la plantilla junto al nuestro (18-oct-2026).
        prompt = "<Subject 1> is the woman in <Picture 1>."
        wf = cv.construir_workflow_video(R2V, prompt, carpetas=plantillas)["workflow"]
        nodo = next(n for n in wf["nodes"] if n["id"] == 138)
        assert nodo["widgets_values"] == [prompt]
        assert nodo["widgets_values_named"] == {"value": prompt}

    def test_la_nota_avisa_de_refrescar_comfyui(self, plantillas):
        con = cv.construir_workflow_video(R2V, "<Picture 1>", carpetas=plantillas,
                                          refs={"imagen": ["mia.png"]})
        sin = cv.construir_workflow_video(R2V, "<Picture 1>", carpetas=plantillas)
        nota = lambda r: next(n for n in r["workflow"]["nodes"] if n["type"] == "Note")  # noqa: E731
        assert "pulsa R" in nota(con)["widgets_values"][0]
        assert "pulsa R" not in nota(sin)["widgets_values"][0]

    def test_avisa_si_el_prompt_nombra_un_video(self, plantillas):
        r = cv.construir_workflow_video(R2V, "<Picture 1> and the camera of <Video 1>.",
                                        carpetas=plantillas)
        assert any("<Video 1>" in a for a in r["avisos"])


class TestImagenYVideo:

    def test_cada_fichero_en_su_carga_tambien_en_el_grupo_apagado(self, plantillas):
        r = cv.construir_workflow_video(ANIMATE, "a dancer", carpetas=plantillas,
                                        refs={"imagen": ["yo.png"], "video": ["baile.mp4"]})
        wf = r["workflow"]
        assert {(n["id"], n["mode"], n["widgets_values"][0]) for n in _cargas(wf)} == {
            (189, 0, "yo.png"), (178, 4, "yo.png")}
        assert _cargas(wf, "LoadVideo")[0]["widgets_values"][0] == "baile.mp4"
        assert [(h["tipo"], h["fichero"]) for h in r["huecos"]] == [
            ("imagen", "yo.png"), ("video", "baile.mp4")]

    def test_sin_ficheros_quedan_por_poner(self, plantillas):
        r = cv.construir_workflow_video(ANIMATE, "a dancer", carpetas=plantillas)
        assert [(h["tipo"], h["fichero"], h["opcional"]) for h in r["huecos"]] == [
            ("imagen", None, False), ("video", None, False)]

    def test_la_imagen_opcional_se_enciende_si_hay_una(self, plantillas):
        con = cv.construir_workflow_video(TI2V, "a fox", carpetas=plantillas,
                                          refs={"imagen": ["zorro.png"]})
        assert [(n["mode"], n["widgets_values"][0]) for n in _cargas(con["workflow"])] == [
            (0, "zorro.png")]
        sin = cv.construir_workflow_video(TI2V, "a fox", carpetas=plantillas)
        assert _cargas(sin["workflow"])[0]["mode"] == 4
        assert sin["huecos"][0]["opcional"] is True


class TestCarpetaInput:

    def test_la_de_comfyui_y_la_de_la_portable(self, tmp_path):
        (tmp_path / "ComfyUI" / "input").mkdir(parents=True)
        assert cv.carpeta_input(str(tmp_path / "ComfyUI")) == tmp_path / "ComfyUI" / "input"
        assert cv.carpeta_input(str(tmp_path)) == tmp_path / "ComfyUI" / "input"
        assert cv.carpeta_input(str(tmp_path / "otra")) is None
        assert cv.carpeta_input("") is None

    def test_copia_con_su_huella_y_una_sola_vez(self, tmp_path):
        entrada = tmp_path / "input"
        entrada.mkdir()
        foto = tmp_path / "Mi foto ñ.JPG"
        foto.write_bytes(b"\xff\xd8 una foto")
        nombre = cv.copiar_a_input(foto, entrada)
        assert nombre.startswith("gprompt_Mi_foto_") and nombre.endswith(".jpg")
        assert (entrada / nombre).read_bytes() == foto.read_bytes()
        assert cv.copiar_a_input(foto, entrada) == nombre
        assert len(list(entrada.iterdir())) == 1
        # Otra con el mismo nombre no la pisa.
        foto.write_bytes(b"\xff\xd8 otra foto")
        assert cv.copiar_a_input(foto, entrada) != nombre

    def test_la_imagen_cargada_como_png(self, tmp_path):
        nombre = cv.guardar_imagen_en_input(Image.new("RGB", (8, 6), "red"), tmp_path)
        assert nombre.startswith("gprompt_imagen_") and nombre.endswith(".png")
        with Image.open(tmp_path / nombre) as img:
            assert img.size == (8, 6)


@pytest.mark.parametrize("modelo, necesita", [
    (R2V, ("imagen",)),
    ("minimax_h3_fl2va_pruned_int8_convrot", ()),
    ("LTX 2.5", ()),
    ("wan2.2_t2v_low_noise_14B_fp8_scaled", ()),
    ("wan2.2_i2v_high_noise_14B_fp16", ("imagen",)),
    (ANIMATE, ("imagen", "video")),
    ("wan2.2_s2v_14B_fp8_scaled", ("imagen", "audio")),
    ("wan2.1_14B_SCAIL_2_int8_convrot", ("video", "imagen")),
])
def test_lo_que_necesita_cada_modelo(modelo, necesita):
    assert cv.referencias_necesarias(modelo) == necesita


def test_las_referencias_son_de_plantillas_que_existen():
    plantillas = {p for _r, t2v, i2v in cv.PLANTILLAS_VIDEO for p in (t2v, i2v)}
    assert set(cv.REFERENCIAS) <= plantillas


class TestEnLaApp:

    def test_la_ficha_del_modelo_avisa(self):
        from modules.tools_analysis import ToolsAnalysisService as S
        assert "hasta 9" in S.texto_referencias_comfy(R2V)
        assert "🔧 Comfy" in S.texto_referencias_comfy(R2V)
        assert "audio" in S.texto_referencias_comfy("wan2.2_s2v_14B_fp8_scaled")
        assert S.texto_referencias_comfy("wan2.2_t2v_low_noise_14B_fp8_scaled") == ""

    @staticmethod
    def _comfy(tmp_path, monkeypatch):
        import config
        base = tmp_path / "ComfyUI"
        plantillas = (base / "venv" / "Lib" / "site-packages"
                      / "comfyui_workflow_templates_media_video" / "templates")
        plantillas.mkdir(parents=True)
        (base / "input").mkdir()
        for nombre, wf in (("video_minimax_h3_r2v", _r2v()), ("video_wan_animate2", _animate())):
            (plantillas / f"{nombre}.json").write_text(json.dumps(wf), encoding="utf-8")
        monkeypatch.setattr(config, "ruta_comfyui", lambda: str(base))
        monkeypatch.setattr(config, "nombres_modelos_comfy", lambda: {})
        return base / "input"

    @staticmethod
    def _app(modelo, imagen=None, ruta=None, prompt="<Subject 1> is the man in <Picture 1>."):
        estados = []
        return SimpleNamespace(
            modo_var=SimpleNamespace(get=lambda: "video"),
            plataforma_var=SimpleNamespace(get=lambda: "ComfyUI / Fooocus"),
            txt_salida=SimpleNamespace(get=lambda *a: prompt),
            extraer_positive=lambda: prompt, extraer_negative=lambda: "",
            combo_modelo_video=SimpleNamespace(get=lambda: modelo),
            duracion_var=SimpleNamespace(get=lambda: "6s"),
            imagen_cargada=imagen, imagen_cargada_ruta=ruta,
            footer=SimpleNamespace(ratio_actual=lambda: "16:9"),
            dialogs=SimpleNamespace(set_estado=lambda *a, **k: estados.append(a[0])),
        )

    def _pulsar(self, app, pedir=None):
        from modules.tools_analysis import ToolsAnalysisService
        svc = ToolsAnalysisService(app)
        pedidos, mostrado = [], []

        def _pedir(modelo, faltan):
            pedidos.append([(h["tipo"], h["n"]) for h in faltan])
            return pedir
        svc._pedir_ficheros_comfy = _pedir
        svc._mostrar_ventana_comfyui = lambda js, modelo, chuleta=None: mostrado.append(
            (json.loads(js), chuleta))
        svc._copiar_comfyui_json()
        return pedidos, mostrado

    def test_la_imagen_cargada_va_al_ref2va_sin_preguntar(self, tmp_path, monkeypatch):
        entrada = self._comfy(tmp_path, monkeypatch)
        app = self._app(R2V, imagen=Image.new("RGB", (16, 16), "blue"))
        pedidos, mostrado = self._pulsar(app)
        assert pedidos == []
        copiada = [f.name for f in entrada.iterdir()]
        assert len(copiada) == 1 and copiada[0].startswith("gprompt_imagen_")
        wf, chuleta = mostrado[0]
        assert [n["widgets_values"][0] for n in _cargas(wf)] == copiada
        assert "📎 1" in chuleta
        # ComfyUI lee la lista de input/ al abrir la página.
        assert "pulsa R" in chuleta

    def test_copia_el_fichero_original_de_la_imagen(self, tmp_path, monkeypatch):
        entrada = self._comfy(tmp_path, monkeypatch)
        foto = tmp_path / "retrato.png"
        Image.new("RGB", (2048, 2048), "green").save(foto)
        self._pulsar(self._app(R2V, imagen=Image.new("RGB", (16, 16)), ruta=str(foto)))
        copiada = next(entrada.iterdir())
        assert copiada.name.startswith("gprompt_retrato_")
        assert copiada.read_bytes() == foto.read_bytes()

    def test_pide_lo_que_falta_y_lo_mete(self, tmp_path, monkeypatch):
        entrada = self._comfy(tmp_path, monkeypatch)
        baile = tmp_path / "baile.mp4"
        baile.write_bytes(b"video")
        app = self._app(ANIMATE, imagen=Image.new("RGB", (16, 16)), prompt="a dancer")
        pedidos, mostrado = self._pulsar(app, pedir={("video", 1): str(baile)})
        # La imagen ya la tiene la app: solo pide el vídeo.
        assert pedidos == [[("video", 1)]]
        wf, chuleta = mostrado[0]
        video = _cargas(wf, "LoadVideo")[0]["widgets_values"][0]
        assert video.startswith("gprompt_baile_") and (entrada / video).is_file()
        assert "📎 2" in chuleta

    def test_sin_elegir_avisa_de_lo_que_lleva_el_de_ejemplo(self, tmp_path, monkeypatch):
        self._comfy(tmp_path, monkeypatch)
        pedidos, mostrado = self._pulsar(self._app(ANIMATE, prompt="a dancer"), pedir={})
        assert pedidos == [[("imagen", 1), ("video", 1)]]
        _wf, chuleta = mostrado[0]
        assert "imagen 1" in chuleta and "vídeo 1" in chuleta

    def test_cancelar_no_saca_workflow(self, tmp_path, monkeypatch):
        entrada = self._comfy(tmp_path, monkeypatch)
        pedidos, mostrado = self._pulsar(self._app(ANIMATE, prompt="a dancer"), pedir=None)
        assert pedidos and mostrado == [] and list(entrada.iterdir()) == []
