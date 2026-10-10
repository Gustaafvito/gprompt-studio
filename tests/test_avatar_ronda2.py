"""2ª ronda del Generador de Dataset LoRA: el LoRA de la 1ª en los workflows.

10-oct-2026: el dataset de Einar (Anima en ComfyUI, 50 tomas) salió con el
mismo estilo pero distinta cara en cada imagen: la barba amarilla, caqui o
naranja, a veces gordo o mayor. Sin una referencia, cada imagen se dibuja
desde cero. Lo que se hace es entrenar un primer LoRA con las mejores y
volver a generar con él cargado; para eso los workflows tienen que llevarlo,
y a mano eran 50 nodos que reconectar.
"""
import gc
import json
import os

import pytest

from modules import avatar_ui
from modules.avatar_generator import (
    LORA_RONDA_PESO,
    carpeta_ronda,
    exportar_dataset,
    exportar_workflows_comfy,
    generar_dataset_avatar,
    nombre_copia_lora,
)
from modules.avatar_montar import emparejar
from modules.comfy_export import nombre_lora_comfy
from modules.i18n import tr

MODELO = "anima-base-v1.0"
ANGULOS = ["face_front", "expression_smile", "full_front"]


def _llm_fake(system, user):
    return ("a 40 year old man with golden blonde hair, braided beard, "
            "wearing a white t-shirt and jeans")


def _exportar(tmp_path, lora=""):
    r = generar_dataset_avatar(_llm_fake, {}, "ohwx_einar", ANGULOS, "anime style", "bg")
    base = exportar_dataset(r, str(tmp_path))
    exportar_workflows_comfy(r, base, MODELO, lora=lora)
    wf_dir = os.path.join(base, "workflows")

    def leer(nombre):
        with open(os.path.join(wf_dir, nombre), encoding="utf-8") as f:
            return json.load(f)
    return wf_dir, leer


def _nodos(wf, tipo):
    return [nd for nd in wf["nodes"] if nd["type"] == tipo]


class TestNombreLoraComfy:
    """ComfyUI nombra cada LoRA por su ruta dentro de `loras`."""

    def test_en_la_raiz_de_loras(self):
        ruta = os.path.join("C:" + os.sep, "IA", "ComfyUI", "models", "loras",
                            "einar_v1.safetensors")
        assert nombre_lora_comfy(ruta) == ("einar_v1", True)

    def test_en_una_subcarpeta(self):
        ruta = os.path.join("D:" + os.sep, "ComfyUI", "models", "Loras", "Anima",
                            "einar_v1.safetensors")
        assert nombre_lora_comfy(ruta) == ("Anima" + os.sep + "einar_v1", True)

    def test_fuera_de_loras_comfy_no_lo_ve(self):
        ruta = os.path.join("C:" + os.sep, "G-Entrena", "salida", "einar_v1.safetensors")
        assert nombre_lora_comfy(ruta) == ("einar_v1", False)


class TestWorkflowsDeLaSegundaRonda:

    def test_el_completo_carga_el_lora_para_todas_las_tomas(self, tmp_path):
        _, leer = _exportar(tmp_path, lora="einar_v1")
        wf = leer("DATASET_COMPLETO.json")
        (lora,) = _nodos(wf, "LoraLoader")
        assert lora["widgets_values"] == ["einar_v1.safetensors",
                                          LORA_RONDA_PESO, LORA_RONDA_PESO]
        assert LORA_RONDA_PESO < 1.0
        # El MODEL de cada KSampler sale del LoraLoader, no del UNETLoader.
        sale_del_lora = {lk[0] for lk in wf["links"] if lk[1] == lora["id"] and lk[2] == 0}
        ks = _nodos(wf, "KSampler")
        assert len(ks) == len(ANGULOS)
        for k in ks:
            modelo = next(i for i in k["inputs"] if i["name"] == "model")
            assert modelo["link"] in sale_del_lora

    def test_guarda_aparte_de_la_primera_ronda(self, tmp_path):
        _, leer = _exportar(tmp_path, lora="einar_v1")
        prefijos = {nd["widgets_values"][0]
                    for nd in _nodos(leer("DATASET_COMPLETO.json"), "SaveImage")}
        assert prefijos == {"ohwx_einar_ronda2/01_face_front",
                            "ohwx_einar_ronda2/15_expression_smile",
                            "ohwx_einar_ronda2/09_full_front"}

    def test_los_individuales_tambien(self, tmp_path):
        _, leer = _exportar(tmp_path, lora="einar_v1")
        wf = leer(os.path.join("individuales", "01_face_front.json"))
        assert _nodos(wf, "LoraLoader")[0]["widgets_values"][0] == "einar_v1.safetensors"
        prefijos = {nd["widgets_values"][0] for nd in _nodos(wf, "SaveImage")}
        assert prefijos == {"ohwx_einar_ronda2/01_face_front",
                            "ohwx_einar_ronda2/01_face_front_detailed"}

    def test_lo_explica_en_el_canvas_y_en_el_leeme(self, tmp_path):
        wf_dir, leer = _exportar(tmp_path, lora="einar_v1")
        notas = [nd["widgets_values"][0] for nd in _nodos(leer("DATASET_COMPLETO.json"), "Note")]
        assert any("2ª RONDA" in n and "einar_v1.safetensors" in n for n in notas)
        with open(os.path.join(wf_dir, "LEEME_WORKFLOWS.txt"), encoding="utf-8") as f:
            leeme = f.read()
        assert "2ª RONDA" in leeme and "output/ohwx_einar_ronda2/" in leeme

    def test_sin_lora_la_primera_ronda_de_siempre(self, tmp_path):
        wf_dir, leer = _exportar(tmp_path)
        wf = leer("DATASET_COMPLETO.json")
        assert not _nodos(wf, "LoraLoader")
        prefijos = {nd["widgets_values"][0] for nd in _nodos(wf, "SaveImage")}
        assert "01_face_front" in prefijos
        with open(os.path.join(wf_dir, "LEEME_WORKFLOWS.txt"), encoding="utf-8") as f:
            assert "2ª RONDA" not in f.read()

    def test_los_lora_de_g_entrena_se_copian_con_nombre_propio(self):
        # G-Entrena llama igual a todos sus LoRA: el de otro personaje
        # pisaría a este en models/loras.
        assert nombre_copia_lora(os.path.join("x", "G-Entrena_anima_FINAL_LoRA.safetensors"),
                                 "ohwx_einar") == "ohwx_einar_anima_ronda1.safetensors"
        assert nombre_copia_lora("G-Entrena_anima_step_000750.safetensors",
                                 "ohwx_einar") == "ohwx_einar_anima_ronda1_paso750.safetensors"
        assert nombre_copia_lora("G-Entrena_qwen-image-2.1_FINAL_LoRA.safetensors",
                                 "lyr4") == "lyr4_qwen-image-2.1_ronda1.safetensors"
        # Los demás conservan su nombre; sin trigger, también.
        assert nombre_copia_lora("einar_v1.safetensors", "ohwx_einar") == "einar_v1.safetensors"
        assert nombre_copia_lora("G-Entrena_anima_FINAL_LoRA.safetensors",
                                 "") == "G-Entrena_anima_FINAL_LoRA.safetensors"

    def test_carpeta_de_la_ronda_sin_caracteres_raros(self):
        assert carpeta_ronda("ohwx_einar") == "ohwx_einar_ronda2"
        assert carpeta_ronda("lyr4 / v2") == "lyr4_v2_ronda2"
        assert carpeta_ronda("") == "dataset_ronda2"

    def test_montar_dataset_las_empareja_por_nombre(self, tmp_path):
        items = [{"filename": "01_face_front"}, {"filename": "09_full_front"}]
        carpeta = tmp_path / "ohwx_einar_ronda2"
        carpeta.mkdir()
        imgs = []
        for nombre in ("09_full_front_00001_.png", "01_face_front_00001_.png"):
            (carpeta / nombre).write_bytes(b"png")
            imgs.append(str(carpeta / nombre))
        pares, sobrantes = emparejar(items, imgs)
        assert [os.path.basename(img) for _, img in pares] == [
            "01_face_front_00001_.png", "09_full_front_00001_.png"]
        assert sobrantes == []


class TestEnLaVentana:

    @pytest.fixture(autouse=True)
    def _recoger_en_el_hilo_principal(self):
        # Los widgets destruidos quedan en ciclos de referencias; si el
        # recolector los suelta más tarde desde el hilo de otro test, sus
        # variables de Tk avisan «main thread is not in main loop».
        yield
        gc.collect()

    def _ventana(self, tk_root):
        f = avatar_ui.AvatarFrame(tk_root, llm_call=lambda s, u: "x")
        tk_root.update_idletasks()
        return f

    def test_elegir_uno_de_la_carpeta_de_loras(self, tk_root, tmp_path, monkeypatch):
        loras = tmp_path / "models" / "loras" / "Anima"
        loras.mkdir(parents=True)
        (loras / "einar_v1.safetensors").write_bytes(b"lora")
        monkeypatch.setattr("config.carpeta_loras_comfy", lambda: str(loras.parent))
        monkeypatch.setattr(avatar_ui.filedialog, "askopenfilename",
                            lambda **kw: str(loras / "einar_v1.safetensors"))
        f = self._ventana(tk_root)
        try:
            assert f.label_lora_ronda.cget("text") == tr("Ninguno: es la 1ª ronda")
            f._on_elegir_lora_ronda()
            assert f._lora_ronda == "Anima" + os.sep + "einar_v1"
            assert "einar_v1.safetensors" in f.label_lora_ronda.cget("text")
            # Cambiar de tipo de LoRA rehace el formulario, pero no lo olvida.
            f._on_tipo_change(tr("🏔 Paisaje"))
            assert "einar_v1.safetensors" in f.label_lora_ronda.cget("text")
            f._on_quitar_lora_ronda()
            assert f._lora_ronda == ""
        finally:
            f.destroy()

    def test_uno_de_fuera_se_copia_a_comfyui(self, tk_root, tmp_path, monkeypatch):
        loras = tmp_path / "models" / "loras"
        loras.mkdir(parents=True)
        fuera = tmp_path / "G-Entrena" / "einar_v1.safetensors"
        fuera.parent.mkdir()
        fuera.write_bytes(b"lora")
        monkeypatch.setattr("config.carpeta_loras_comfy", lambda: str(loras))
        monkeypatch.setattr(avatar_ui.filedialog, "askopenfilename",
                            lambda **kw: str(fuera))
        monkeypatch.setattr(avatar_ui.messagebox, "askyesno", lambda *a, **kw: True)
        f = self._ventana(tk_root)
        try:
            f._on_elegir_lora_ronda()
            assert (loras / "einar_v1.safetensors").read_bytes() == b"lora"
            assert fuera.exists()  # copia, no mueve
            assert f._lora_ronda == "einar_v1"
        finally:
            f.destroy()

    def test_el_de_g_entrena_se_copia_con_el_trigger(self, tk_root, tmp_path, monkeypatch):
        loras = tmp_path / "models" / "loras"
        loras.mkdir(parents=True)
        fuera = tmp_path / "proyecto" / "output" / "G-Entrena_anima_FINAL_LoRA.safetensors"
        fuera.parent.mkdir(parents=True)
        fuera.write_bytes(b"lora")
        monkeypatch.setattr("config.carpeta_loras_comfy", lambda: str(loras))
        monkeypatch.setattr(avatar_ui.filedialog, "askopenfilename",
                            lambda **kw: str(fuera))
        preguntas = []
        monkeypatch.setattr(avatar_ui.messagebox, "askyesno",
                            lambda titulo, texto: preguntas.append(texto) or True)
        f = self._ventana(tk_root)
        try:
            f.entry_trigger.delete(0, "end")
            f.entry_trigger.insert(0, "ohwx_einar")
            f._on_elegir_lora_ronda()
            assert "ohwx_einar_anima_ronda1.safetensors" in preguntas[0]
            assert (loras / "ohwx_einar_anima_ronda1.safetensors").read_bytes() == b"lora"
            assert f._lora_ronda == "ohwx_einar_anima_ronda1"
        finally:
            f.destroy()

    def test_si_no_se_copia_avisa(self, tk_root, tmp_path, monkeypatch):
        loras = tmp_path / "models" / "loras"
        loras.mkdir(parents=True)
        fuera = tmp_path / "einar_v1.safetensors"
        fuera.write_bytes(b"lora")
        monkeypatch.setattr("config.carpeta_loras_comfy", lambda: str(loras))
        monkeypatch.setattr(avatar_ui.filedialog, "askopenfilename",
                            lambda **kw: str(fuera))
        monkeypatch.setattr(avatar_ui.messagebox, "askyesno", lambda *a, **kw: False)
        f = self._ventana(tk_root)
        try:
            f._on_elegir_lora_ronda()
            assert not (loras / "einar_v1.safetensors").exists()
            assert "models/loras" in f.label_estado.cget("text")
        finally:
            f.destroy()
