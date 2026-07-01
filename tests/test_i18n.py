"""Tests para modules/i18n.py — interfaz bilingüe ES/EN."""
import ast
import re
from pathlib import Path

from modules import i18n

ROOT = Path(__file__).resolve().parent.parent

# Heurística "parece español": acentos/signos o palabras función frecuentes.
RE_ESPANOL = re.compile(
    r"[áéíóúñÁÉÍÓÚÑ¿¡]|\b(el|la|los|las|un|una|de|del|para|con|sin|según|"
    r"que|qué|este|esta|todo|todos|nuevo|nueva|guardar|generar|borrar|"
    r"añadir|crear|abrir|cerrar|copiar|pegar|aplicar|seleccionar|escribe|"
    r"pulsa|aquí|más|sólo|vacío|listo|hecho|ningún|hay|anuncio|aventura|"
    r"comedia|cortometraje|misterio|naturaleza|producto|paisaje|retrato)\b",
    re.IGNORECASE)


def _parece_espanol(s: str) -> bool:
    s = re.sub(r"\{[^}]*\}", "", s)
    return bool(RE_ESPANOL.search(s)) and any(c.isalpha() for c in s)


def _reset():
    i18n.set_idioma("es")


def test_es_devuelve_el_texto_original():
    _reset()
    assert i18n.tr("Modelo") == "Modelo"
    assert i18n.tr("Cualquier cosa sin traducir") == "Cualquier cosa sin traducir"


def test_en_traduce_lo_conocido():
    i18n.set_idioma("en")
    try:
        assert i18n.tr("Modelo") == "Model"
        assert i18n.tr("Estilo") == "Style"
        assert i18n.tr("Cerrar") == "Close"
        assert i18n.tr("▶ Generar") == "▶ Generate"
    finally:
        _reset()


def test_en_fallback_al_espanol_si_no_hay_traduccion():
    i18n.set_idioma("en")
    try:
        # Texto que NO está en TRADUCCIONES → devuelve el español tal cual.
        assert i18n.tr("Texto inventado xyz") == "Texto inventado xyz"
    finally:
        _reset()


def test_set_idioma_normaliza():
    i18n.set_idioma("english")
    assert i18n.get_idioma() == "en"
    i18n.set_idioma("ES")
    assert i18n.get_idioma() == "es"
    i18n.set_idioma(None)
    assert i18n.get_idioma() == "es"
    _reset()


def test_traducciones_no_vacias_y_sin_claves_vacias():
    assert len(i18n.TRADUCCIONES) > 10
    assert all(k and v for k, v in i18n.TRADUCCIONES.items())


def test_ningun_sink_de_ui_con_espanol_sin_tr():
    """Ningún literal con pinta de español llega a un sink de UI sin tr().

    Sinks: text=/label_text=/placeholder_text=/message=/title=/values= y
    .title()/messagebox/show_toast/set_estado con literal o f-string. Si este
    test falla, ese texto saldría en ESPAÑOL con la interfaz en inglés:
    envuélvelo en tr("...") (f-strings → tr("...{0}...").format(...)) y añade
    la traducción a TRADUCCIONES.
    """
    ui_keywords = {"text", "label_text", "placeholder_text", "message", "title"}
    ui_methods = {"title", "showinfo", "showwarning", "showerror", "askyesno",
                  "askokcancel", "show_toast", "set_estado"}
    # dialogs.py: avisos del cambio de idioma, bilingües ES+EN a propósito.
    permitidos = {"dialogs.py"}

    def _literal(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.JoinedStr):
            partes = [v.value for v in node.values
                      if isinstance(v, ast.Constant) and isinstance(v.value, str)]
            return "".join(partes) if partes else None
        return None

    fugas = []
    for py in list(ROOT.glob("*.py")) + list((ROOT / "modules").glob("*.py")):
        if py.name in permitidos:
            continue
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            fname = f.attr if isinstance(f, ast.Attribute) else (
                f.id if isinstance(f, ast.Name) else "")
            candidatos = []
            for kw in node.keywords:
                if kw.arg in ui_keywords:
                    candidatos.append(kw.value)
                elif kw.arg == "values" and isinstance(kw.value, (ast.List, ast.Tuple)):
                    candidatos.extend(kw.value.elts)
            if fname in ui_methods and node.args:
                candidatos.extend(node.args[:2])
            for c in candidatos:
                txt = _literal(c)
                if txt and _parece_espanol(txt):
                    fugas.append(f"{py.name}:{node.lineno} {txt[:60]!r}")
    assert not fugas, (
        f"{len(fugas)} textos españoles llegan a la UI sin tr(): "
        + "; ".join(fugas[:8]))


def test_cobertura_dominios_combos_dinamicos():
    """Los valores 'españoles' de los combos dinámicos tienen entrada EN.

    Estos combos se pintan con tr(variable): estilos del footer, emociones/
    voces/idiomas de audio, destinos, cabeceras de grupos de modelos. Los
    nombres propios/ingleses del catálogo no necesitan entrada.
    """
    import config
    dominios = {
        "DESTINOS": config.DESTINOS,
        "ESTILOS_VISUAL_VIDEO": config.ESTILOS_VISUAL_VIDEO,
        "EMOCIONES_AUDIO": config.EMOCIONES_AUDIO,
        "VOCES_AUDIO": config.VOCES_AUDIO,
        "IDIOMAS_AUDIO": config.IDIOMAS_AUDIO,
        "ESTILOS_IMAGEN": config.ESTILOS_IMAGEN,
        "ESTILOS_VIDEO": config.ESTILOS_VIDEO,
        "ESTILOS_AUDIO": config.ESTILOS_AUDIO,
        "ESTILOS_GRUPOS": list(config.ESTILOS_GRUPOS.keys()),
        "GRUPOS_IMAGEN": [g for g, _ in config.GRUPOS_IMAGEN],
        "GRUPOS_VIDEO": [g for g, _ in config.GRUPOS_VIDEO],
    }
    fugas = [f"{nombre}: {v!r}"
             for nombre, valores in dominios.items()
             for v in valores
             if v not in i18n.TRADUCCIONES and _parece_espanol(v)]
    assert not fugas, (
        f"{len(fugas)} valores de combos dinámicos sin traducción EN: "
        + "; ".join(fugas[:8]))


def test_cobertura_avatar_config_traducido():
    """Todo texto visible del Avatar dataset (data-driven) tiene entrada EN.

    avatar_ui.py los muestra con tr(variable), que el test de literales no ve:
    labels/placeholders/opciones del formulario, títulos de grupo, etiquetas
    de ángulo, avisos, estilos y fondos de los 4 tipos de LoRA.
    """
    from modules.avatar_config import LORA_TYPES
    faltan = set()
    for cfg in LORA_TYPES.values():
        for k in ("label_form", "label_angles", "label_trigger",
                  "placeholder_trigger"):
            if cfg.get(k):
                faltan.add(cfg[k])
        for campo in cfg.get("form_fields", []):
            faltan.add(campo["label"])
            faltan.update(campo.get("options", []))
            if campo.get("placeholder"):
                faltan.add(campo["placeholder"])
        faltan.update(cfg.get("angle_groups", {}).values())
        for datos in cfg.get("angles", {}).values():
            faltan.add(datos["label"])
            if datos.get("warn"):
                faltan.add(datos["warn"])
        faltan.update(cfg.get("styles", {}))
        faltan.update(cfg.get("backgrounds") or {})
    faltan -= set(i18n.TRADUCCIONES)
    assert not faltan, (
        f"{len(faltan)} textos del Avatar dataset sin traducción EN: "
        + "; ".join(repr(t) for t in sorted(faltan)[:10]))


def test_tr_es_destraduce():
    assert i18n.tr_es("Woman") == "Mujer"
    assert i18n.tr_es("🧑 Character") == "🧑 Personaje"
    assert i18n.tr_es("Mujer") == "Mujer"           # identidad si ya es ES
    assert i18n.tr_es("texto inventado") == "texto inventado"


def test_cobertura_todo_tr_literal_esta_traducido():
    """Todo tr('literal') del código debe tener entrada en TRADUCCIONES.

    Si este test falla, el texto nuevo se mostraría en español en la UI
    inglesa (el fallback lo hace invisible en desarrollo). Los tr(variable)
    dinámicos no se pueden comprobar aquí; sus valores se añaden a mano.
    """
    faltan = {}
    for py in list(ROOT.glob("*.py")) + list((ROOT / "modules").glob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and node.args):
                continue
            f = node.func
            name = f.id if isinstance(f, ast.Name) else (
                f.attr if isinstance(f, ast.Attribute) else None)
            arg = node.args[0]
            if (name == "tr" and isinstance(arg, ast.Constant)
                    and isinstance(arg.value, str)
                    and arg.value not in i18n.TRADUCCIONES):
                faltan.setdefault(arg.value, f"{py.name}:{node.lineno}")
    assert not faltan, (
        f"{len(faltan)} textos tr() sin traducción EN: "
        + "; ".join(f"{t!r} ({loc})" for t, loc in list(faltan.items())[:10]))
