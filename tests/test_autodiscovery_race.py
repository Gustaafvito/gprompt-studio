"""Candados de la carrera del auto-discovery de ComfyUI.

Bug real (20-jul-2026): el escaneo aterrizaba ~18s tras el arranque, después
de restaurar preferencias. Durante esa ventana el combo de ComfyUI estaba
vacío y el guardado persistía un modelo de otra plataforma, dejando
`plataforma='ComfyUI / Fooocus'` con `modelo_img='GPT Image 2'`.
"""
import json

import config
from modules.data_mgmt import DataMgmtService


class _ComboFalso:
    def __init__(self, valor, valores):
        self._valor, self._valores = valor, valores

    def get(self):
        return self._valor

    def cget(self, _clave):
        return self._valores


class _AppFalsa:
    def __init__(self, combo):
        self.combo_modelo_imagen = combo


def _persistible(valor, valores, prefs):
    svc = DataMgmtService.__new__(DataMgmtService)
    svc.app = _AppFalsa(_ComboFalso(valor, valores))
    return svc._modelo_img_persistible(prefs)


class TestModeloImgPersistible:

    def test_combo_vacio_conserva_lo_guardado(self):
        """Antes de que aterrice el escaneo el combo no tiene valores."""
        assert _persistible("", [], {"modelo_img": "zibBadmilk"}) == "zibBadmilk"

    def test_modelo_de_otra_plataforma_no_machaca(self):
        """El caso exacto del bug: ComfyUI seleccionado, combo con un modelo
        de OpenAI heredado porque la lista aún estaba vacía."""
        guardado = _persistible("GPT Image 2", ["── ComfyUI ──", "zibBadmilk"],
                                {"modelo_img": "zibBadmilk"})
        assert guardado == "zibBadmilk"

    def test_seleccion_valida_si_se_guarda(self):
        assert _persistible("zibBadmilk", ["── ComfyUI ──", "zibBadmilk"],
                            {"modelo_img": "otro"}) == "zibBadmilk"

    def test_sin_nada_guardado_cae_al_actual(self):
        assert _persistible("GPT Image 2", [], {}) == "GPT Image 2"


def _aislar_listas(monkeypatch):
    """Listas propias: las funciones mutan las globales in place."""
    for nombre in ("GRUPOS_IMAGEN_COMFYUI", "GRUPOS_VIDEO_COMFYUI",
                   "MODELOS_IMAGEN_COMFYUI_FLAT", "MODELOS_VIDEO_COMFYUI_FLAT",
                   "GRUPOS_AUDIO_VIGENTES", "MODELOS_AUDIO_FLAT"):
        monkeypatch.setattr(config, nombre, [])
    monkeypatch.setattr(config, "_COMFY_BASE_IMG", 0)
    monkeypatch.setattr(config, "_COMFY_BASE_VID", 0)


class TestCacheComfy:
    """La caché es lo que evita el desplegable vacío: el escaneo tarda 0.8s
    pero su hilo no aterriza hasta ~17s por la contienda del GIL con la UI."""

    def _montar(self, tmp_path, monkeypatch, cache_path, modelos):
        raiz = tmp_path / "ComfyUI"
        (raiz / "models" / "checkpoints").mkdir(parents=True)
        (raiz / "models" / "checkpoints" / "juggernautXL_v9.safetensors").touch()

        cache = tmp_path / "comfy_cache.json"
        cache.write_text(json.dumps({"path": cache_path or str(raiz),
                                     "imagen": modelos, "video": []}),
                         encoding="utf-8")
        monkeypatch.setitem(config.ARCHIVOS, "comfy_cache", cache)
        monkeypatch.setitem(config.ARCHIVOS, "modelos_comfy", tmp_path / "no-hay.json")
        monkeypatch.setattr(config, "_cargar_preferencias_seguras",
                            lambda: {"comfyui_path": str(raiz)})
        monkeypatch.setitem(config._COMFY_CACHE_APLICADA, "imagen", [])
        monkeypatch.setitem(config._COMFY_CACHE_APLICADA, "video", [])
        _aislar_listas(monkeypatch)
        return raiz

    def test_puebla_los_combos_sin_escanear(self, tmp_path, monkeypatch):
        self._montar(tmp_path, monkeypatch, None, ["juggernautXL_v9"])
        assert config.aplicar_cache_comfy() == 1
        assert "juggernautXL_v9" in config.MODELOS_IMAGEN_COMFYUI_FLAT

    def test_cache_de_otra_ruta_se_ignora(self, tmp_path, monkeypatch):
        """Si el usuario cambia la carpeta de ComfyUI, la caché es de otra
        instalación y no debe colarse."""
        self._montar(tmp_path, monkeypatch, r"D:\otra\ComfyUI", ["fantasma"])
        assert config.aplicar_cache_comfy() == 0
        assert config.MODELOS_IMAGEN_COMFYUI_FLAT == []

    def test_escaneo_coincidente_no_repuebla(self, tmp_path, monkeypatch):
        """Caché al día → el hilo no toca los combos (0 = nada que cambiar)."""
        self._montar(tmp_path, monkeypatch, None, ["juggernautXL_v9"])
        monkeypatch.setattr(config, "_autodiscovery_hecho", False)
        assert config.aplicar_cache_comfy() == 1
        assert config.aplicar_autodiscovery_comfy() == 0
        assert "juggernautXL_v9" in config.MODELOS_IMAGEN_COMFYUI_FLAT

    def test_modelo_borrado_desaparece_del_combo(self, tmp_path, monkeypatch):
        """La caché no puede dejar fantasmas: el escaneo sustituye los grupos
        del auto-discovery enteros, no los acumula."""
        self._montar(tmp_path, monkeypatch, None, ["borrado_hace_tiempo"])
        monkeypatch.setattr(config, "_autodiscovery_hecho", False)
        config.aplicar_cache_comfy()
        assert "borrado_hace_tiempo" in config.MODELOS_IMAGEN_COMFYUI_FLAT
        config.aplicar_autodiscovery_comfy()
        assert "borrado_hace_tiempo" not in config.MODELOS_IMAGEN_COMFYUI_FLAT
        assert "juggernautXL_v9" in config.MODELOS_IMAGEN_COMFYUI_FLAT


class TestRutaComfyDesdeMeta:

    def test_lee_comfyui_path_anidado_en_meta(self, tmp_path, monkeypatch):
        """El manifest v2 anida la ruta en _meta; leer solo la raíz dejaba
        todo colgando del fallback a preferencias.json."""
        raiz = tmp_path / "ComfyUI"
        (raiz / "models" / "checkpoints").mkdir(parents=True)
        (raiz / "models" / "checkpoints" / "juggernautXL_v9.safetensors").touch()

        manifest = tmp_path / "mis_modelos_comfy.json"
        manifest.write_text(json.dumps({
            "_meta": {"version": 2, "comfyui_path": str(raiz)},
            "imagen": [], "video": [],
        }), encoding="utf-8")

        monkeypatch.setitem(config.ARCHIVOS, "modelos_comfy", manifest)
        # Sin fallback: la ruta solo puede salir de _meta.
        monkeypatch.setattr(config, "_cargar_preferencias_seguras", lambda: {})
        monkeypatch.setattr(config, "_autodiscovery_hecho", False)
        monkeypatch.setitem(config.ARCHIVOS, "comfy_cache", tmp_path / "sin-cache.json")
        _aislar_listas(monkeypatch)

        assert config.aplicar_autodiscovery_comfy() > 0
