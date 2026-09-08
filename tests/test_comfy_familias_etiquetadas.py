"""Tres cabeceras "Otros" seguidas en el desplegable de ComfyUI.

08-sep-2026, en el inventario del usuario:

    ComfyUI · Otros   16   <- familia ''         (de verdad sin clasificar)
    ComfyUI · Otros    3   <- familia 'edit'     (FireRed-Image-Edit, joyai…)
    ComfyUI · Otros    1   <- familia 'hidream'  (hidream_o1_image_dev)

`edit` y `hidream` SÍ tienen ficha en `_COMFY_SPECS_FAMILIA` — reciben sus
1500 chars y sus reglas — pero les faltaba la entrada en
`_COMFY_FAMILIA_LABELS`, así que `labels.get(fam, "Otros")` las mandaba al
cajón de sastre. Las dos tablas se habían desincronizado.

Y encima `_agrupar_por_familia` agrupaba por CLAVE de familia, no por
etiqueta, de modo que cada clave huérfana generaba su propio grupo con la
misma cabecera. El plegado de familias se indexa por el TEXTO de la cabecera,
así que las tres se plegaban y desplegaban a la vez.
"""
import config


class TestCadaFamiliaConFichaTieneEtiqueta:

    def test_ninguna_familia_con_ficha_cae_en_otros(self):
        sin_etiqueta = sorted(f for f in config._COMFY_SPECS_FAMILIA
                              if f not in config._COMFY_FAMILIA_LABELS)
        assert not sin_etiqueta, (
            f"{sin_etiqueta} tienen ficha propia pero saldrían bajo 'Otros', "
            f"mezcladas con lo que de verdad no está clasificado")

    def test_las_dos_que_faltaban(self):
        for fam, etiqueta in (("edit", "Edición de imagen"), ("hidream", "HiDream")):
            assert config._COMFY_FAMILIA_LABELS.get(fam) == etiqueta

    def test_otros_sigue_existiendo_para_lo_desconocido(self):
        # La familia '' (nombre que no dice nada) es legítima y debe agruparse.
        assert config._COMFY_FAMILIA_LABELS[""] == "Otros"


class TestNoSeRepitenCabeceras:

    def test_dos_claves_sin_etiqueta_dan_UNA_cabecera(self):
        labels = {"a": "Alfa", "": "Otros"}
        grupos = config._agrupar_por_familia(
            ["m_a", "m_x", "m_y"],
            lambda n: {"m_a": "a", "m_x": "desconocida1",
                       "m_y": "desconocida2"}[n],
            labels, "ComfyUI")
        cabeceras = [c for c, _ in grupos]
        assert len(cabeceras) == len(set(cabeceras)), (
            f"cabeceras repetidas: {cabeceras} — el plegado se indexa por "
            f"texto y las plegaría todas juntas")
        otros = [ms for c, ms in grupos if "Otros" in c]
        assert otros == [["m_x", "m_y"]], "las huérfanas van al mismo grupo"

    def test_el_inventario_real_no_repite_ninguna(self):
        config.aplicar_autodiscovery_comfy()
        for grupos in (config.GRUPOS_IMAGEN_COMFYUI, config.GRUPOS_VIDEO_COMFYUI):
            cabeceras = [c for c, _ in grupos]
            assert len(cabeceras) == len(set(cabeceras)), cabeceras

    def test_los_modelos_siguen_ordenados_dentro_del_grupo(self):
        grupos = config._agrupar_por_familia(
            ["zeta", "Alfa", "beta"], lambda n: "", {"": "Otros"}, "ComfyUI")
        assert grupos == [("── ComfyUI · Otros ──", ["Alfa", "beta", "zeta"])]
