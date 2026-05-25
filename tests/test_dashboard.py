"""Tests para modules/dashboard.py.

Por ahora solo cubre la paleta de colores extraída en sesión 6+. La
función _cmd_dashboard sigue siendo monolítica (1457 líneas) y
requiere refactor mayor para testear sus 16 secciones.
"""
import pytest

from modules.dashboard import _dashboard_palette

CLAVES_PALETA = {
    "bg", "card_bg", "card_bg_alt", "card_border",
    "text_primary", "text_secondary", "text_muted",
    "accent_blue", "accent_green", "accent_amber", "accent_red",
    "accent_purple", "accent_pink", "bar_bg",
}


class TestDashboardPalette:

    def test_light_devuelve_dict_completo(self):
        p = _dashboard_palette(True)
        assert set(p.keys()) == CLAVES_PALETA

    def test_dark_devuelve_dict_completo(self):
        p = _dashboard_palette(False)
        assert set(p.keys()) == CLAVES_PALETA

    def test_todos_los_valores_son_hex_validos(self):
        for is_light in (True, False):
            p = _dashboard_palette(is_light)
            for k, v in p.items():
                assert isinstance(v, str), f"{k} no es string"
                assert v.startswith("#"), f"{k}={v} no empieza con #"
                assert len(v) == 7, f"{k}={v} no es #RRGGBB"
                int(v[1:], 16)  # debe ser hex válido

    def test_light_y_dark_son_distintos(self):
        light = _dashboard_palette(True)
        dark = _dashboard_palette(False)
        # Al menos el fondo y texto primario deben diferir
        assert light["bg"] != dark["bg"]
        assert light["text_primary"] != dark["text_primary"]
        assert light["card_bg"] != dark["card_bg"]

    def test_light_tiene_fondo_claro(self):
        p = _dashboard_palette(True)
        # bg claro: el componente R > 0xD0 indica color claro
        bg = p["bg"]
        r = int(bg[1:3], 16)
        assert r > 0xD0, f"bg light {bg} no parece claro"

    def test_dark_tiene_fondo_oscuro(self):
        p = _dashboard_palette(False)
        bg = p["bg"]
        r = int(bg[1:3], 16)
        assert r < 0x30, f"bg dark {bg} no parece oscuro"

    def test_text_primary_invertido_entre_temas(self):
        # En claro el texto principal es muy oscuro (~#111827)
        # En oscuro el texto principal es muy claro (~#e5e7eb)
        light_text = _dashboard_palette(True)["text_primary"]
        dark_text = _dashboard_palette(False)["text_primary"]
        light_r = int(light_text[1:3], 16)
        dark_r = int(dark_text[1:3], 16)
        assert light_r < 0x30, "text_primary light debería ser oscuro"
        assert dark_r > 0xD0, "text_primary dark debería ser claro"

    def test_text_muted_es_menos_intenso_que_secondary(self):
        # En cada tema, text_muted debe ser visualmente más débil que
        # text_secondary (no exigimos exacto, pero deben ser distintos)
        for is_light in (True, False):
            p = _dashboard_palette(is_light)
            assert p["text_muted"] != p["text_secondary"]

    def test_paleta_es_inmutable_entre_llamadas(self):
        """El dict devuelto en distintas llamadas con el mismo input
        debe tener los mismos valores (no estado interno)."""
        p1 = _dashboard_palette(True)
        p2 = _dashboard_palette(True)
        assert p1 == p2

    def test_acentos_son_colores_distintos(self):
        p = _dashboard_palette(True)
        acentos = [p["accent_blue"], p["accent_green"], p["accent_amber"],
                   p["accent_red"], p["accent_purple"], p["accent_pink"]]
        # Todos diferentes
        assert len(set(acentos)) == 6
