"""Tests para config — helpers y funciones utility."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _ratios_en_orden_canonico(ratios, canon):
    """Devuelve True si `ratios` sigue el orden canónico: los que están en
    `canon` primero en ese orden, y los extras después en orden lexicográfico."""
    idx = {r: i for i, r in enumerate(canon)}
    esperado = sorted(ratios, key=lambda r: (idx.get(r, len(canon)), r))
    return ratios == esperado


class TestRatiosOrdenCanonico:
    """Guarda: todos los `ratios` de los specs siguen RATIOS_VIDEO/RATIOS_IMAGEN."""

    def test_video_specs_ratios_canonicos(self):
        import json
        import os

        from config import RATIOS_VIDEO
        path = os.path.join(os.path.dirname(__file__), "..", "data", "model_specs_video.json")
        data = json.load(open(path, encoding="utf-8"))
        malos = [k for k, s in data.items()
                 if isinstance(s, dict) and s.get("ratios")
                 and not _ratios_en_orden_canonico(s["ratios"], RATIOS_VIDEO)]
        assert malos == [], f"ratios fuera de orden canónico: {malos}"

    def test_imagen_specs_ratios_canonicos(self):
        import json
        import os

        from config import RATIOS_IMAGEN
        path = os.path.join(os.path.dirname(__file__), "..", "data", "model_specs_imagen.json")
        data = json.load(open(path, encoding="utf-8"))
        malos = [k for k, s in data.items()
                 if isinstance(s, dict) and s.get("ratios")
                 and not _ratios_en_orden_canonico(s["ratios"], RATIOS_IMAGEN)]
        assert malos == [], f"ratios fuera de orden canónico: {malos}"

    def test_comfy_video_synthetic_ratios_canonicos(self):
        from config import _COMFY_SPECS_FAMILIA_VIDEO, RATIOS_VIDEO
        for fam, s in _COMFY_SPECS_FAMILIA_VIDEO.items():
            assert _ratios_en_orden_canonico(s["ratios"], RATIOS_VIDEO), fam


class TestStyleGuideBilingue:
    """La guía de estilos tiene versión EN con las MISMAS claves (nombres)."""

    def test_en_mismas_claves_y_contenido_traducido(self):
        import modules.style_guide as sg
        from modules.i18n import set_idioma
        try:
            set_idioma("es"); sg._cache = None
            g_es = sg.cargar_guia()
            set_idioma("en"); sg._cache = None
            g_en = sg.cargar_guia()
            assert g_es and g_en
            assert set(g_es) == set(g_en), "las claves (nombres) deben coincidir"
            # Una descripción concreta debe estar en inglés en modo EN
            assert g_en["Fotografía Realista"]["descripcion"] == "Professional camera photo, no filters"
            assert g_en["Cinematográfico"]["grupo"] == "🎵 Audio Styles"
        finally:
            set_idioma("es"); sg._cache = None


class TestPlataformaDola:
    """Dola (dola.com) integrada como plataforma natural de imagen y vídeo."""

    def test_dola_en_plataformas(self):
        import config
        assert config.PLATAFORMAS_IMAGEN.get("Dola") == "natural"
        assert config.PLATAFORMAS_VIDEO.get("Dola") == "natural"
        assert "Dola" in config.PLATAFORMAS_IMAGEN_LISTA
        assert "Dola" in config.PLATAFORMAS_VIDEO_LISTA

    def test_dola_modelos_y_motores(self):
        import config
        assert "Dola" in config.MODELOS_POR_PLATAFORMA_IMAGEN
        assert config.MOTORES_VIDEO["Dola"] == ["Seedance 1.0 Fast", "Seedance 2.0 Fast"]
        assert config.MOTOR_DEFAULT["Dola"] == "Seedance 2.0 Fast"

    def test_dola_specs_bilingues(self):
        from config import get_image_model_specs, get_model_specs
        img = get_image_model_specs("Dola")
        assert img and img["is_natural"] is True and img["best_for_en"]
        assert img["max_imagenes"] == 10
        vid = get_model_specs("Seedance 1.0 Fast")
        assert vid and vid["best_for_en"] and vid["duraciones"] == ["5s", "10s"]


class TestConfigHelpers:
    def test_es_separador_true(self):
        from config import es_separador
        assert es_separador("── SeaArt ──") is True
        assert es_separador("──") is True

    def test_es_separador_false(self):
        from config import es_separador
        assert es_separador("SeaArt Infinity") is False
        assert es_separador("Z Image Turbo") is False

    def test_get_model_specs(self):
        from config import get_model_specs
        specs = get_model_specs("Kling 3.0")
        assert specs is not None
        assert specs["nota"] == 4.5
        assert specs["has_negative"] is False  # Kling 3.0 no usa prompt negativo
        assert specs["has_audio"] is True
        assert specs["max_chars"] == 2500

    def test_get_model_specs_unknown(self):
        from config import get_model_specs
        assert get_model_specs("Modelo Inexistente") is None

    def test_get_image_model_specs(self):
        from config import get_image_model_specs
        specs = get_image_model_specs("SeaArt Infinity")
        assert specs is not None
        assert specs["is_natural"] is True
        assert specs["has_negative"] is False

    def test_get_image_model_specs_unknown(self):
        from config import get_image_model_specs
        assert get_image_model_specs("Modelo Fake") is None

    def test_get_prompt_template(self):
        from config import get_prompt_template
        tmpl = get_prompt_template("Z Image Turbo")
        assert tmpl is not None
        assert "positive_base" in tmpl
        assert "negative_base" in tmpl

    def test_get_prompt_template_unknown(self):
        from config import get_prompt_template
        assert get_prompt_template("Modelo SinTemplate") is None


class TestModelosVigentes:
    """Filtro de modelos de imagen: solo se muestran los 'vigente': true."""

    def test_es_modelo_imagen_vigente(self):
        from config import es_modelo_imagen_vigente
        # Vigentes marcados en el JSON
        assert es_modelo_imagen_vigente("Z-Image-Base") is True
        assert es_modelo_imagen_vigente("Nano Banana") is True
        assert es_modelo_imagen_vigente("Reve 2.0") is True
        # Un modelo NO vigente
        assert es_modelo_imagen_vigente("SD 3.5 Large Turbo") is False
        # Inexistente
        assert es_modelo_imagen_vigente("Modelo Fake") is False

    def test_flat_solo_contiene_vigentes(self):
        from config import MODELOS_IMAGEN_FLAT, es_modelo_imagen_vigente, es_separador
        modelos = [m for m in MODELOS_IMAGEN_FLAT if not es_separador(m)]
        assert modelos, "no debería quedar vacío"
        assert all(es_modelo_imagen_vigente(m) for m in modelos)
        # El no-vigente no aparece; el vigente sí
        assert "SD 3.5 Large Turbo" not in modelos
        assert "Z-Image-Base" in modelos

    def test_master_conserva_todos(self):
        from config import MODELOS_IMAGEN_FLAT, MODELOS_IMAGEN_FLAT_TODOS, es_separador
        todos = [m for m in MODELOS_IMAGEN_FLAT_TODOS if not es_separador(m)]
        vis = [m for m in MODELOS_IMAGEN_FLAT if not es_separador(m)]
        assert len(todos) > len(vis)         # el master sigue completo
        assert "SD 3.5 Large Turbo" in todos    # el no-vigente sigue en el master

    def test_no_quedan_grupos_vacios(self):
        from config import GRUPOS_IMAGEN_VIGENTES
        for cabecera, modelos in GRUPOS_IMAGEN_VIGENTES:
            assert modelos, f"grupo vacío: {cabecera}"

    def test_familia_flux_tiene_estilos(self):
        # La familia FLUX debe ofrecer el toggle "Estilo" como las demás.
        from config import ESTILOS_POR_FAMILIA, detectar_familia
        assert "flux" in ESTILOS_POR_FAMILIA
        assert ESTILOS_POR_FAMILIA["flux"][0] == "Auto"
        # Detección por nombre y por pertenencia al grupo (Mimic Neo sin 'flux')
        assert detectar_familia("CyberRealistic Flux") == "flux"
        assert detectar_familia("Midjourney Mimic Neo") == "flux"
        assert detectar_familia("Z-Image-Base") == "z_image"

    def test_grupos_orden_alfabetico_case_insensitive(self):
        # Todos los grupos de imagen deben quedar en orden alfabético sin
        # distinguir mayúsculas (los nombres en minúscula no caen al final).
        from config import GRUPOS_IMAGEN
        for cabecera, modelos in GRUPOS_IMAGEN:
            assert modelos == sorted(modelos, key=str.lower), f"desordenado: {cabecera}"
        # Caso concreto: lyh_anime_Flux antes de Midjourney/XE en Familia FLUX
        flux = next(ms for cab, ms in GRUPOS_IMAGEN if "FLUX" in cab.upper())
        assert flux.index("lyh_anime_Flux") < flux.index("Midjourney Mimic Neo")

    def test_todos_los_catalogos_orden_alfabetico(self):
        # Vídeo, audio y ComfyUI también: cada grupo case-insensitive ordenado.
        # (ComfyUI usaba sorted() sin key=str.lower → "zImageBase" mal colocado.)
        from config import (
            GRUPOS_AUDIO,
            GRUPOS_IMAGEN_COMFYUI,
            GRUPOS_VIDEO,
            GRUPOS_VIDEO_COMFYUI,
        )
        for nombre, grupos in [
            ("VIDEO", GRUPOS_VIDEO), ("AUDIO", GRUPOS_AUDIO),
            ("COMFY_IMG", GRUPOS_IMAGEN_COMFYUI),
            ("COMFY_VID", GRUPOS_VIDEO_COMFYUI),
        ]:
            for cabecera, modelos in grupos:
                assert modelos == sorted(modelos, key=str.lower), \
                    f"{nombre} desordenado: {cabecera}"

    def test_modelo_sin_nota_no_rompe(self):
        # Real Vision - FLUX no tiene nota (None). Debe seguir vigente y los
        # puntos que usan nota deben tolerarlo (label 's/n', sort -> 0).
        from config import es_modelo_imagen_vigente, get_image_model_specs
        s = get_image_model_specs("Real Vision - FLUX")
        assert s["nota"] is None
        assert es_modelo_imagen_vigente("Real Vision - FLUX") is True
        # patrones de consumo que antes petaban / mostraban "None"
        assert (s.get("nota") or "s/n") == "s/n"
        assert float(s.get("nota") or 0) == 0.0


class TestI18nSinRemanentesEspanol:
    """Guarda: en modo EN no se cuela español en estilos ni en best_for de audio."""

    def test_estilos_sin_acentos_en_ingles(self):
        # Ningún estilo (footer) debe conservar acentos españoles tras tr() en EN.
        import re

        import config
        from modules.i18n import set_idioma, tr
        try:
            set_idioma("en")
            malos = []
            for nom in ("ESTILOS_IMAGEN", "ESTILOS_VIDEO", "ESTILOS_AUDIO"):
                for e in getattr(config, nom, []):
                    if isinstance(e, str) and not e.startswith("─") and re.search(r"[áéíóúñ]", tr(e).lower()):
                        malos.append((nom, e))
            assert malos == [], f"estilos en español sin traducir en EN: {malos}"
        finally:
            set_idioma("es")

    def test_audio_best_for_en_completo(self):
        import json
        import os
        path = os.path.join(os.path.dirname(__file__), "..", "data", "model_specs_audio.json")
        d = json.load(open(path, encoding="utf-8"))
        falta = [k for k, s in d.items()
                 if isinstance(s, dict) and s.get("best_for") and not s.get("best_for_en")]
        assert falta == [], f"modelos de audio sin best_for_en: {falta}"

    def test_combos_audio_y_destinos_sin_acentos_en_ingles(self):
        # Combos emoción/voz/idioma + destinos: ningún valor debe conservar
        # acentos españoles tras tr() en modo EN.
        import re

        import config
        from modules.i18n import set_idioma, tr
        try:
            set_idioma("en")
            malos = []
            fuentes = ("EMOCIONES_AUDIO", "VOCES_AUDIO", "IDIOMAS_AUDIO", "DESTINOS",
                       "ESTILOS_GRUPOS")
            for nom in fuentes:
                v = getattr(config, nom, [])
                vals = list(v.keys()) if isinstance(v, dict) else list(v)
                for x in vals:
                    if isinstance(x, str) and re.search(r"[áéíóúñ]", tr(x).lower()):
                        malos.append((nom, x))
            assert malos == [], f"valores en español sin traducir en EN: {malos}"
        finally:
            set_idioma("es")

    def test_destino_reverse_map_round_trip(self):
        # En EN el combo muestra el destino traducido; el reverse-map debe
        # devolver la clave ES para el lookup de REGLAS_POR_DESTINO.
        import config
        from modules.i18n import set_idioma, tr
        try:
            set_idioma("en")
            rev = {tr(d): d for d in config.DESTINOS}
            assert rev["Client"] == "Cliente"
            assert rev["Anthum (contest)"] == "Anthum (concurso)"
            assert rev["Instagram"] == "Instagram"  # neutro
        finally:
            set_idioma("es")
