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
        # Listas propias: la función muta las globales in place y sin esto
        # contaminaría al resto de la suite.
        for nombre in ("GRUPOS_IMAGEN_COMFYUI", "GRUPOS_VIDEO_COMFYUI",
                       "MODELOS_IMAGEN_COMFYUI_FLAT", "MODELOS_VIDEO_COMFYUI_FLAT",
                       "GRUPOS_AUDIO_VIGENTES", "MODELOS_AUDIO_FLAT"):
            monkeypatch.setattr(config, nombre, [])

        assert config.aplicar_autodiscovery_comfy() > 0
