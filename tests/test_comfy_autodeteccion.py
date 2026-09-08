"""La plantilla no reparte los modelos del autor, y ComfyUI se busca solo.

Hasta el 08-sep-2026 `plantilla_default` traía los ONCE checkpoints del equipo
del autor (Juggernaut-XL, z_image_turbo, flux-2-klein, wan2.2_i2v...). Quien
instalara la app veía once modelos que no tiene: elegir cualquiera daba
"model not found" en ComfyUI, y de paso tapaba el auto-discovery haciendo
creer que ya estaba configurado.

Y sin ruta configurada `aplicar_autodiscovery_comfy()` devolvía 0 en silencio,
sin detección alguna: el usuario nuevo se quedaba con el desplegable vacío y
ninguna pista de que le faltaba pegar una ruta en Ajustes.
"""
import inspect
import json

import config


class TestLaPlantillaNoTraeModelosAjenos:

    def _plantilla(self):
        fuente = inspect.getsource(config._cargar_modelos_locales)
        i = fuente.find("plantilla_default = {")
        assert i != -1, "no encuentro la plantilla"
        return fuente[i:i + 1400]

    def test_ningun_checkpoint_del_autor(self):
        bloque = self._plantilla()
        for ajeno in ("Juggernaut", "RealVisXL", "z_image", "flux-2-klein",
                      "qwen_image_edit", "wan2.2", "ltx-", "zImageBase"):
            assert ajeno not in bloque, (
                f"{ajeno} es un modelo del equipo del autor: quien instale la "
                f"app no lo tiene y ComfyUI le dará 'model not found'")

    def test_las_listas_nacen_vacias(self):
        bloque = self._plantilla()
        assert '"imagen": []' in bloque and '"video": []' in bloque

    def test_la_descripcion_explica_que_hacer(self):
        bloque = self._plantilla()
        assert "auto-discovery" in bloque, (
            "un desplegable vacío solo sirve si dice cómo llenarlo")


class TestAutodeteccionDeComfyUI:

    def test_existe_la_funcion(self):
        assert callable(config.detectar_comfy_automatico)

    def test_solo_mira_unidades_fijas(self):
        fuente = inspect.getsource(config._unidades_fijas)
        assert "DRIVE_FIXED" in fuente or "== 3" in fuente, (
            "tocar una unidad de red caída o un USB vacío puede tardar "
            "segundos en el arranque")

    def test_devuelve_cadena(self):
        r = config.detectar_comfy_automatico()
        assert isinstance(r, str)

    def test_es_cacheada(self, monkeypatch):
        # La segunda llamada no vuelve a tocar el disco: corre en el arranque.
        monkeypatch.setattr(config, "_ruta_comfy_detectada", "C:/lo-que-sea")
        llamadas = []
        monkeypatch.setattr(config, "_unidades_fijas",
                            lambda: llamadas.append(1) or ["C:/"])
        config.detectar_comfy_automatico()
        assert not llamadas, "estaba cacheada; no debía re-escanear"

    def test_una_ruta_configurada_manda_sobre_la_detectada(self):
        fuente = inspect.getsource(config._ruta_comfy_configurada)
        i_manual = fuente.find("get_comfyui_path")
        i_auto = fuente.find("detectar_comfy_automatico")
        assert i_manual != -1 and i_auto != -1
        assert i_manual < i_auto, (
            "lo que el usuario configuró a mano gana a la autodetección")


class TestLaRutaDetectadaSeGuarda:

    def test_existe_el_persistidor(self):
        assert callable(config._persistir_ruta_comfy)

    def test_no_pisa_una_ruta_ya_puesta(self, tmp_path, monkeypatch):
        destino = tmp_path / "mis_modelos_comfy.json"
        destino.write_text(json.dumps(
            {"_meta": {"comfyui_path": "D:/la-mia"}, "imagen": [], "video": []}),
            encoding="utf-8")
        monkeypatch.setitem(config.ARCHIVOS, "modelos_comfy", destino)
        assert config._persistir_ruta_comfy("C:/otra") is False
        d = json.loads(destino.read_text(encoding="utf-8"))
        assert d["_meta"]["comfyui_path"] == "D:/la-mia"

    def test_escribe_cuando_no_hay_ninguna(self, tmp_path, monkeypatch):
        destino = tmp_path / "mis_modelos_comfy.json"
        destino.write_text(json.dumps({"_meta": {}, "imagen": [], "video": []}),
                           encoding="utf-8")
        monkeypatch.setitem(config.ARCHIVOS, "modelos_comfy", destino)
        assert config._persistir_ruta_comfy("C:/IA/ComfyUI") is True
        d = json.loads(destino.read_text(encoding="utf-8"))
        assert d["_meta"]["comfyui_path"] == "C:/IA/ComfyUI"
        assert d["imagen"] == [] and d["video"] == []
