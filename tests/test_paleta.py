"""Candado de la paleta semántica (modules/paleta.py).

Los colores con rol semántico NO se hardcodean en los módulos de UI:
se referencia la constante (P.BTN_EXITO, P.TXT_OK...). Si este test
falla, sustituye el hex por su constante de modules.paleta.
"""
import re
from pathlib import Path

from modules import paleta as P

ROOT = Path(__file__).resolve().parent.parent

# Hex canónicos y variantes históricas ya unificadas: prohibidos como
# literal directo en kwargs de color.
PROHIBIDOS = {
    "#1a7a3c", "#145e2d", "#1a8a3c", "#127a30", "#1e5f3a", "#16492d",
    "#15633a", "#7a1a1a", "#5a1a1a", "#5a0f0f", "#7c3aed", "#6d28d9",
    "#1a4a5a", "#155e75", "#2ecc71", "#e74c3c", "#3498db", "#f39c12",
    "#fbbf24",
}
RE_KW = re.compile(r'\b(fg_color|hover_color|text_color)\s*=\s*"(#[0-9a-fA-F]{3,6})"')
# theme/config/components definen los DICCIONARIOS de tema (fuente legítima).
EXCLUIR = {"paleta.py", "theme.py", "config.py", "components.py",
           "gprompt_window.py"}


def test_paleta_consistente():
    # El hover de cada botón debe existir y ser distinto del fondo.
    for rol in ("PRIMARIO", "EXITO", "PELIGRO", "ACENTO", "SECUNDARIO", "NEUTRO"):
        bg = getattr(P, f"BTN_{rol}")
        hover = getattr(P, f"BTN_{rol}_HOVER")
        assert bg.startswith("#") and hover.startswith("#") and bg != hover


RE_FONT = re.compile(r"CTkFont\([^)]*?size\s*=\s*(\d+)", re.DOTALL)


def test_sin_tamanos_literales_en_fuentes():
    """Tamaños 7-16 dentro de CTkFont van por la escala P.FUENTE_*.

    Los ≥18 (splash, logos, displays del dashboard) quedan libres.
    """
    fugas = []
    for py in list(ROOT.glob("*.py")) + list((ROOT / "modules").glob("*.py")):
        if py.name in EXCLUIR:
            continue
        src = py.read_text(encoding="utf-8")
        for m in RE_FONT.finditer(src):
            n = int(m.group(1))
            if 7 <= n <= 16:
                linea = src[:m.start()].count("\n") + 1
                fugas.append(f"{py.name}:{linea} size={n}")
    assert not fugas, (
        f"{len(fugas)} tamaños de fuente literales (usa P.FUENTE_*): "
        + "; ".join(fugas[:10]))


def test_sin_hex_semanticos_hardcodeados():
    fugas = []
    for py in list(ROOT.glob("*.py")) + list((ROOT / "modules").glob("*.py")):
        if py.name in EXCLUIR:
            continue
        for i, ln in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            for m in RE_KW.finditer(ln):
                if m.group(2).lower() in PROHIBIDOS:
                    fugas.append(f"{py.name}:{i} {m.group(0)}")
    assert not fugas, (
        f"{len(fugas)} colores semánticos hardcodeados (usa modules.paleta): "
        + "; ".join(fugas[:10]))
