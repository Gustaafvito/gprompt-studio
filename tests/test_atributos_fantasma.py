"""Atributos de `app` que el código lee y que nadie define en ningún sitio.

Es el fallo más traicionero de esta app: con `hasattr(self.app, "x")` o
`getattr(self.app, "x", None)` delante no revienta, simplemente no hace nada.
Encontrados así el 24 y 25-sep-2026:
  • la detección de NSFW escribía en `nsfw_var` (es `switch_nsfw_var`) y
    anunciaba «activado modo NSFW» sin activarlo;
  • los Seeds favoritos leían `modelo_img_var` y `modelo_vid_var`: todos se
    guardaban SIN modelo, y aplicar uno antiguo que sí lo trajera reventaba;
  • el botón «🔑 Configurar» del Dashboard llamaba a `_cmd_api_keys`;
  • `lbl_compat`: un comprobador de compatibilidad a medio hacer.

Este candado hace el escaneo en cada ejecución de la suite.
"""
import ast
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Consultados a propósito con un valor por defecto: pueden no existir y no
# pasa nada. Añadir aquí SOLO con esa justificación.
OPCIONALES = {
    "_focus_pack_info",   # core._safe_pack: {} si Focus nunca ocultó nada
    "barra_progreso",     # dialogs: alternativa a `progress`, que es la que existe
}


def _escanear():
    ficheros = [RAIZ / "app.py", RAIZ / "api_clients.py", RAIZ / "workers.py"]
    ficheros += sorted((RAIZ / "modules").glob("*.py"))
    usados, definidos = {}, set()
    for f in ficheros:
        arbol = ast.parse(f.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.ClassDef):
                for b in nodo.body:
                    if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        definidos.add(b.name)
                    elif isinstance(b, ast.Assign):
                        definidos.update(t.id for t in b.targets if isinstance(t, ast.Name))
            if isinstance(nodo, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                objetivos = nodo.targets if isinstance(nodo, ast.Assign) else [nodo.target]
                for t in objetivos:
                    definidos.update(s.attr for s in ast.walk(t) if isinstance(s, ast.Attribute))
            if (isinstance(nodo, ast.Call) and getattr(nodo.func, "id", "") == "setattr"
                    and len(nodo.args) >= 2 and isinstance(nodo.args[1], ast.Constant)):
                definidos.add(nodo.args[1].value)
            if isinstance(nodo, ast.Attribute) and isinstance(nodo.ctx, ast.Load):
                v = nodo.value
                es_app = ((isinstance(v, ast.Attribute) and v.attr == "app"
                           and isinstance(v.value, ast.Name) and v.value.id == "self")
                          or (isinstance(v, ast.Name) and v.id == "app"))
                if es_app:
                    usados.setdefault(nodo.attr, []).append(f"{f.name}:{nodo.lineno}")
            if (isinstance(nodo, ast.Call) and getattr(nodo.func, "id", "") in ("hasattr", "getattr")
                    and len(nodo.args) >= 2):
                obj, nombre = nodo.args[0], nodo.args[1]
                es_app = ((isinstance(obj, ast.Attribute) and obj.attr == "app")
                          or (isinstance(obj, ast.Name) and obj.id in ("app", "self")))
                if es_app and isinstance(nombre, ast.Constant) and isinstance(nombre.value, str):
                    usados.setdefault(nombre.value, []).append(f"{f.name}:{nodo.lineno}")
    componentes = (RAIZ / "modules" / "components.py").read_text(encoding="utf-8")
    definidos.update(re.findall(r'_name = "(\w+)"', componentes))
    import customtkinter as ctk
    definidos.update(dir(ctk.CTk))
    return {k: v for k, v in usados.items()
            if k not in definidos and not k.startswith("__") and k not in OPCIONALES}


def test_ningun_atributo_de_app_se_lee_sin_existir():
    fantasmas = _escanear()
    assert fantasmas == {}, (
        "Se leen atributos de `app` que no existen en ningún sitio (con hasattr "
        f"delante fallan en silencio): {fantasmas}")
