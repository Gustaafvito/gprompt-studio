"""La ventana de atajos solo promete lo que de verdad está registrado.

Ctrl+Shift+A («Analizar imagen») salía en la ventana de atajos y no hacía
nada: estaba registrado como `<Control-Shift-a>`. Con Shift pulsado, Tk
entrega la letra en MAYÚSCULA (keysym «A»), así que ese binding no se
disparaba nunca. Comprobado el 24-sep-2026 con pulsaciones reales del
sistema: `<Control-Shift-A>` salta y `<Control-Shift-a>` no.
"""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ATAJOS = (RAIZ / "modules" / "atajos_ayuda.py").read_text(encoding="utf-8")

_RE_BINDING = re.compile(r"""bind(?:_all)?\(\s*["'](<[^"']+>)""")
# Las filas de la ventana: ("Ctrl+Shift+A", tr("Analizar imagen (Vision)"))
_RE_FILA = re.compile(r"""\(\s*"((?:Ctrl|Alt)\+[^"]+)"\s*,\s*tr\(""")
_TECLAS = {"Enter": "Return", "?": "question"}


def _todos_los_bindings():
    fuentes = list((RAIZ / "modules").glob("*.py")) + [RAIZ / "app.py"]
    return {b for f in fuentes
            for b in _RE_BINDING.findall(f.read_text(encoding="utf-8"))}


def _secuencia_tk(atajo):
    """«Ctrl+Shift+A» → «<Control-Shift-A>», como hay que registrarlo."""
    partes = atajo.split("+")
    tecla = partes[-1]
    mods = ["Control" if p == "Ctrl" else p for p in partes[:-1]]
    tecla = _TECLAS.get(tecla, tecla)
    if len(tecla) == 1 and tecla.isalpha():
        # Con Shift llega en mayúscula; sin Shift, en minúscula.
        tecla = tecla.upper() if "Shift" in mods else tecla.lower()
    elif len(tecla) == 1 and tecla.isdigit() and mods == ["Alt"]:
        tecla = f"Key-{tecla}"
    return "<" + "-".join(mods + [tecla]) + ">"


def test_ctrl_shift_letra_se_registra_en_mayuscula():
    malos = [b for b in _todos_los_bindings()
             if re.fullmatch(r"<Control-Shift-[a-z]>", b)]
    assert not malos, f"no se dispararían nunca: {malos}"


def test_cada_atajo_anunciado_esta_registrado():
    filas = _RE_FILA.findall(ATAJOS)
    # Si la ventana cambia de forma, este test dejaría de leerla y pasaría
    # sin comprobar nada.
    assert len(filas) >= 30, f"solo {len(filas)} filas: ¿cambió la ventana?"
    registrados = _todos_los_bindings()
    faltan = [f"{f} (esperaba {_secuencia_tk(f)})" for f in filas
              if _secuencia_tk(f) not in registrados]
    assert not faltan, "la ventana anuncia atajos que no existen: " + "; ".join(faltan)


def test_el_readme_dice_cuantos_atajos_hay():
    # Decía 29 y la ventana de Ctrl+? lista 39 (revisión del 26-sep-2026).
    import re
    from pathlib import Path
    raiz = Path(__file__).resolve().parent.parent
    fuente = (raiz / "modules" / "atajos_ayuda.py").read_text(encoding="utf-8")
    i = fuente.index("        atajos = [")
    bloque = fuente[i:fuente.index("\n        ]\n", i)]
    n = len(re.findall(r'^\s*\("[^"]+", tr\(', bloque, re.M))
    assert f"({n} registrados" in (raiz / "README.md").read_text(encoding="utf-8")
    assert f"{n} registered" in (raiz / "README.en.md").read_text(encoding="utf-8")
