"""Textos que pasan por tr() como variable también necesitan su inglés.

Los candados de i18n miraban `tr("texto literal")`. Se les escapaban dos
patrones, y el barrido en inglés del 25-sep-2026 encontró sus huecos: los
filtros «🖼 Imagen / 🎬 Vídeo / 📦 Todos» de Export CLI, la Biblioteca y la
Guía de estilos, «📚 Todas» del glosario, los títulos de Favoritos e
Historial, las etiquetas del Dashboard…

  • `tr(v) for v in ("…", "…")` — una lista de literales traducida elemento
    a elemento;
  • `tr({"a": "…"}.get(clave, "…"))` — un diccionario de literales.
"""
import ast
from pathlib import Path

from modules.i18n import TRADUCCIONES

RAIZ = Path(__file__).resolve().parent.parent

# Iguales en los dos idiomas: no necesitan entrada.
IGUALES = {"Instagram", "TikTok", "YouTube", "YouTube Shorts", "Twitter / X", "LinkedIn",
           "Reddit", "Web / Blog", "Freepik community", "Dark", "Light", "System", "Auto"}


def _es_tr(nodo):
    return isinstance(nodo, ast.Call) and getattr(nodo.func, "id", "") == "tr"


def _literales(nodo):
    if isinstance(nodo, (ast.Tuple, ast.List, ast.Set)):
        return [e.value for e in nodo.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    return []


def _sin_traduccion():
    faltan = {}
    for f in [RAIZ / "app.py"] + sorted((RAIZ / "modules").glob("*.py")):
        arbol = ast.parse(f.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            textos = []
            # [tr(v) for v in ("…", "…")]  y  (tr(v) for v in […])
            if isinstance(nodo, (ast.ListComp, ast.GeneratorExp, ast.SetComp)) and _es_tr(nodo.elt):
                arg = nodo.elt.args[0] if nodo.elt.args else None
                gen = nodo.generators[0]
                if isinstance(arg, ast.Name) and isinstance(gen.target, ast.Name) and arg.id == gen.target.id:
                    textos += _literales(gen.iter)
            # tr({…}.get(clave, "…"))
            if _es_tr(nodo) and nodo.args:
                arg = nodo.args[0]
                if (isinstance(arg, ast.Call) and getattr(arg.func, "attr", "") == "get"
                        and isinstance(arg.func.value, ast.Dict)):
                    textos += [v.value for v in arg.func.value.values
                               if isinstance(v, ast.Constant) and isinstance(v.value, str)]
                    textos += [a.value for a in arg.args[1:]
                               if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            for t in textos:
                if t and t not in TRADUCCIONES and t not in IGUALES:
                    faltan.setdefault(t, f"{f.name}:{nodo.lineno}")
    return faltan


def test_los_textos_que_se_traducen_como_variable_tienen_ingles():
    faltan = _sin_traduccion()
    assert faltan == {}, f"sin traducción al inglés: {faltan}"
