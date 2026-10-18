"""Workflows de VÍDEO para ComfyUI, a partir de las plantillas oficiales.

Las plantillas de vídeo de ComfyUI (LTX, Wan, MiniMax H3, Kandinsky…) llevan
subgrafos, varios cargadores, audio, reescalado latente y hasta su propio
mejorador de prompt. Construirlas a mano, como las de imagen
(comfy_export), sería reinventar cada una y romperlas con cada versión de
ComfyUI. Así que se parte de la plantilla que trae el propio ComfyUI del
usuario (paquete comfyui_workflow_templates*) y se le escribe lo nuestro: el
prompt, el negativo, el modelo elegido, la duración y el formato.

Hasta el 18-oct-2026 el botón 🔧 Comfy solo hacía imagen: con LTX 2.5
elegido en vídeo exportaba el modelo que se hubiera quedado en el
desplegable de imagen.

Módulo PURO (sin customtkinter).

Las plantillas guardan los valores de dos formas, y las dos se leen igual
aquí, como «campos» (un nodo, un widget y dónde vive su valor):
  • Subgrafo clásico (LTX, MiniMax H3): el nodo exterior lleva en
    widgets_values un valor por cada entrada del subgrafo que es un widget,
    en orden, y cada entrada apunta a un nodo de dentro. Ese valor manda
    sobre el del nodo de dentro.
  • proxyWidgets (Wan 2.2): el nodo exterior no guarda nada y los valores
    viven en los nodos de dentro.
"""
import copy
import json
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# (patrón del nombre del modelo, plantilla de texto a vídeo, plantilla con
# imagen). De lo más concreto a lo más general: gana el primero que casa.
PLANTILLAS_VIDEO = (
    (r"ltx[-_ .]?2[-_ .]?5", "video_ltx2_5_t2v", "video_ltx2_5_i2v"),
    (r"ltx[-_ .]?2[-_ .]?3", "video_ltx2_3_t2v", "video_ltx2_3_i2v"),
    (r"minimax[-_ ]?h3.*ref2va", "video_minimax_h3_r2v", "video_minimax_h3_r2v"),
    (r"minimax[-_ ]?h3", "video_minimax_h3_t2v", "video_minimax_h3_i2v"),
    (r"wan[-_ ]?2\.?2[-_ ]?animate|wan[-_ ]?animate", "video_wan_animate2", "video_wan_animate2"),
    (r"bernini", "video_bernini_r_video_editing", "video_bernini_r_video_editing"),
    (r"wan2\.?2.*fun[-_]camera", "video_wan2_2_14B_fun_camera", "video_wan2_2_14B_fun_camera"),
    (r"wan2\.?2.*fun[-_]control.*5b", "video_wan2_2_5B_fun_control", "video_wan2_2_5B_fun_control"),
    (r"wan2\.?2.*fun[-_]control", "video_wan2_2_14B_fun_control", "video_wan2_2_14B_fun_control"),
    (r"wan2\.?2.*s2v", "video_wan2_2_14B_s2v", "video_wan2_2_14B_s2v"),
    (r"wan2\.?2.*ti2v", "video_wan2_2_5B_ti2v", "video_wan2_2_5B_ti2v"),
    (r"wan2\.?2.*i2v", "video_wan2_2_14B_i2v", "video_wan2_2_14B_i2v"),
    (r"wan2\.?2.*t2v", "video_wan2_2_14B_t2v", "video_wan2_2_14B_i2v"),
    (r"wan2\.?1.*scail", "video_wan21_scail2_character_replacement_int8",
     "video_wan21_scail2_character_replacement_int8"),
    (r"wan2\.?1.*t2v", "text_to_video_wan", "image_to_video_wan"),
    (r"kandinsky[-_ ]?5.*i2v", "video_kandinsky5_i2v", "video_kandinsky5_i2v"),
    (r"kandinsky[-_ ]?5", "video_kandinsky5_t2v", "video_kandinsky5_i2v"),
)

# Tipos de entrada de subgrafo que son un widget (los demás son conexiones).
_TIPOS_WIDGET = {"STRING", "INT", "FLOAT", "BOOLEAN", "COMBO"}

# Orden de los widgets de los nodos que se tocan, por si el nodo guardado no
# los lista en sus inputs.
_WIDGETS = {
    "CLIPTextEncode": ["text"],
    "PrimitiveStringMultiline": ["value"], "PrimitiveString": ["value"],
    "PrimitiveInt": ["value"], "PrimitiveFloat": ["value"], "PrimitiveBoolean": ["value"],
    "UNETLoader": ["unet_name", "weight_dtype"], "UnetLoaderGGUF": ["unet_name"],
    "CheckpointLoaderSimple": ["ckpt_name"],
    "CLIPLoader": ["clip_name", "type", "device"],
    "DualCLIPLoader": ["clip_name1", "clip_name2", "type", "device"],
    "VAELoader": ["vae_name"],
    "LoraLoaderModelOnly": ["lora_name", "strength_model"],
    "LatentUpscaleModelLoader": ["model_name"], "UpscaleModelLoader": ["model_name"],
    "CLIPVisionLoader": ["clip_name"], "AudioEncoderLoader": ["audio_encoder_name"],
    "EmptyHunyuanLatentVideo": ["width", "height", "length", "batch_size"],
    "EmptyLTXVLatentVideo": ["width", "height", "length", "batch_size"],
    "ResolutionSelector": ["aspect_ratio", "megapixels", "multiple"],
    "CreateVideo": ["fps"],
}

# Carpetas de models/ de cada cargador (como en nombres_modelos_comfy).
_CARPETAS = {
    ("UNETLoader", "unet_name"): ("diffusion_models", "unet"),
    ("UnetLoaderGGUF", "unet_name"): ("diffusion_models", "unet"),
    ("CheckpointLoaderSimple", "ckpt_name"): ("checkpoints",),
    ("CLIPLoader", "clip_name"): ("text_encoders", "clip"),
    ("DualCLIPLoader", "clip_name1"): ("text_encoders", "clip"),
    ("DualCLIPLoader", "clip_name2"): ("text_encoders", "clip"),
    ("VAELoader", "vae_name"): ("vae",),
    ("LoraLoaderModelOnly", "lora_name"): ("loras",),
    ("LoraLoader", "lora_name"): ("loras",),
    ("LatentUpscaleModelLoader", "model_name"): ("latent_upscale_models",),
    ("UpscaleModelLoader", "model_name"): ("upscale_models",),
    ("CLIPVisionLoader", "clip_name"): ("clip_vision",),
    ("AudioEncoderLoader", "audio_encoder_name"): ("audio_encoders",),
}
_CARGADORES_PRINCIPALES = {("UNETLoader", "unet_name"), ("UnetLoaderGGUF", "unet_name"),
                           ("CheckpointLoaderSimple", "ckpt_name")}

# Formatos del nodo ResolutionSelector de ComfyUI (comfy_extras/nodes_resolution).
_ASPECTOS = {
    "1:1": "1:1 (Square)", "2:3": "2:3 (Portrait Photo)", "3:2": "3:2 (Photo)",
    "3:4": "3:4 (Portrait Standard)", "4:3": "4:3 (Standard)",
    "9:16": "9:16 (Portrait Widescreen)", "16:9": "16:9 (Widescreen)",
    "21:9": "21:9 (Ultrawide)",
}

# Marcas de precisión o cuantización: el mismo fichero en otra precisión
# (la plantilla pide gemma…-int8-convrot y el usuario tiene gemma…-nvfp4).
_PRECISION = {"bf16", "fp16", "fp32", "fp8", "fp4", "int8", "int4", "nvfp4", "mxfp8",
              "convrot", "scaled", "e4m3fn", "e5m2", "mixed", "fpmixed", "comfy",
              "awq", "w4a8"}


def _tipo_modelo(nombre: str) -> int | None:
    """Índice de la fila de PLANTILLAS_VIDEO que corresponde al nombre."""
    n = _sin_ext(nombre or "").lower()
    for i, (patron, _t2v, _i2v) in enumerate(PLANTILLAS_VIDEO):
        if re.search(patron, n):
            return i
    return None


def plantilla_para(modelo: str, con_imagen: bool = False) -> str | None:
    """Nombre de la plantilla oficial para `modelo`, o None si no hay."""
    i = _tipo_modelo(modelo)
    if i is None:
        return None
    _patron, t2v, i2v = PLANTILLAS_VIDEO[i]
    return i2v if con_imagen else t2v


def carpetas_plantillas(ruta_comfy: str) -> list:
    """Carpetas «templates» de los paquetes comfyui_workflow_templates*.

    Están en el Python de ComfyUI: venv o .venv dentro de la carpeta, o el
    python_embeded de la versión portable, al lado.
    """
    if not ruta_comfy:
        return []
    base = Path(ruta_comfy)
    sitios = ("venv/Lib/site-packages", ".venv/Lib/site-packages",
              "python_embeded/Lib/site-packages",
              "venv/lib/python3*/site-packages", ".venv/lib/python3*/site-packages")
    halladas = []
    for raiz in (base, base.parent):
        for sitio in sitios:
            try:
                for sp in raiz.glob(sitio):
                    halladas += sorted(sp.glob("comfyui_workflow_templates*/templates"))
            except OSError:
                continue
    return halladas


def cargar_plantilla(nombre: str, carpetas: list) -> dict | None:
    for carpeta in carpetas:
        fichero = Path(carpeta) / f"{nombre}.json"
        try:
            if fichero.is_file():
                return json.loads(fichero.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            logger.warning(f"Plantilla de ComfyUI ilegible: {fichero}: {e}")
    return None


# ── Campos: dónde vive cada valor ────────────────────────────────

class _Campo:
    """Un widget de un nodo y el sitio donde vive su valor efectivo.

    `espejo`: en el subgrafo clásico el valor manda desde el nodo exterior,
    pero también se escribe en el de dentro. Si no, el JSON queda con el
    fichero viejo de la plantilla dentro, y ComfyUI lo marca como ausente
    aunque no se use (visto con LTX 2.5 el 18-oct-2026).
    """
    __slots__ = ("nodo", "widget", "almacen", "clave", "contenedor", "espejo")

    def __init__(self, nodo, widget, almacen, clave, contenedor, espejo=False):
        self.nodo, self.widget = nodo, widget
        self.almacen, self.clave = almacen, clave
        self.contenedor, self.espejo = contenedor, espejo

    @property
    def valor(self):
        return self.almacen[self.clave]

    @valor.setter
    def valor(self, v):
        self.almacen[self.clave] = v
        if self.espejo:
            propios = self.nodo.get("widgets_values")
            widgets = _widgets_de(self.nodo)
            if isinstance(propios, list) and self.widget in widgets:
                i = widgets.index(self.widget)
                if i < len(propios):
                    propios[i] = v

    @property
    def titulo(self) -> str:
        return (self.nodo.get("title") or "").lower()


def _widgets_de(nodo: dict) -> list:
    conocidos = _WIDGETS.get(nodo.get("type"))
    if conocidos:
        return conocidos
    return [i["name"] for i in nodo.get("inputs", []) if "widget" in i]


def _enlazado(nodo: dict, widget: str, enlaces: dict | None = None) -> bool:
    """True si el widget recibe el valor por una conexión (su valor no cuenta).

    Con `enlaces`, la conexión desde la entrada del subgrafo (el nodo -10) no
    cuenta: con proxyWidgets el valor sigue viviendo en el nodo de dentro.
    """
    for i in nodo.get("inputs", []):
        if i.get("name") == widget and i.get("link") is not None:
            origen = enlaces.get(i["link"]) if enlaces is not None else None
            return not (origen and origen[0] == -10)
    return False


def _enlaces(contenedor: dict) -> dict:
    """{id: (origen, slot_origen, destino, slot_destino)} de un grafo."""
    salida = {}
    for lk in contenedor.get("links", []) or []:
        if isinstance(lk, dict):
            salida[lk["id"]] = (lk["origin_id"], lk["origin_slot"],
                                lk["target_id"], lk["target_slot"])
        elif isinstance(lk, (list, tuple)) and len(lk) >= 5:
            salida[lk[0]] = tuple(lk[1:5])
    return salida


def _nodos_por_id(contenedor: dict) -> dict:
    return {n.get("id"): n for n in contenedor.get("nodes", [])}


def _campos(wf: dict) -> list:
    defs = {sg["id"]: sg for sg in wf.get("definitions", {}).get("subgraphs", [])}
    todos = [n for cont in [wf, *defs.values()] for n in cont.get("nodes", [])]
    # Subgrafos que alguien usa con proxyWidgets: sus valores viven dentro.
    con_proxy = {n["type"] for n in todos
                 if n.get("type") in defs and (n.get("properties") or {}).get("proxyWidgets")}
    campos = []
    for cont in [wf, *defs.values()]:
        enlaces = _enlaces(cont) if cont.get("id") in con_proxy else None
        for nodo in cont.get("nodes", []):
            if nodo.get("type") in defs:
                if nodo["type"] not in con_proxy:
                    campos += _campos_instancia(nodo, defs[nodo["type"]])
                continue
            campos += _campos_nodo(nodo, cont, enlaces)
    return campos


def _campos_nodo(nodo: dict, cont: dict, enlaces: dict | None = None) -> list:
    valores = nodo.get("widgets_values")
    if isinstance(valores, dict):
        return [_Campo(nodo, k, valores, k, cont) for k in valores
                if not _enlazado(nodo, k, enlaces)]
    if not isinstance(valores, list):
        return []
    return [_Campo(nodo, w, valores, i, cont)
            for i, w in enumerate(_widgets_de(nodo))
            if i < len(valores) and not _enlazado(nodo, w, enlaces)]


def _campos_instancia(inst: dict, sg: dict) -> list:
    entradas = [e for e in sg.get("inputs", []) if e.get("type") in _TIPOS_WIDGET]
    valores = inst.get("widgets_values")
    if not isinstance(valores, list) or len(valores) != len(entradas):
        logger.debug(f"[comfy vídeo] subgrafo {sg.get('name')}: "
                     f"{len(entradas)} entradas y {len(valores or [])} valores")
        return []
    enlaces, nodos = _enlaces(sg), _nodos_por_id(sg)
    campos = []
    for i, entrada in enumerate(entradas):
        # Si fuera del subgrafo algo alimenta esta entrada (un
        # ResolutionSelector, por ejemplo), el valor guardado no cuenta.
        if _enlazado(inst, entrada["name"]):
            continue
        for lid in entrada.get("linkIds", []):
            destino = enlaces.get(lid)
            nodo = nodos.get(destino[2]) if destino else None
            if not nodo:
                continue
            ins = nodo.get("inputs", [])
            widget = ins[destino[3]]["name"] if destino[3] < len(ins) else entrada["name"]
            campos.append(_Campo(nodo, widget, valores, i, sg, espejo=True))
            break
    return campos


def _va_a(campo: _Campo, entrada: str) -> bool:
    """True si la salida del nodo entra en una entrada llamada `entrada`."""
    enlaces, nodos = _enlaces(campo.contenedor), _nodos_por_id(campo.contenedor)
    for salida in campo.nodo.get("outputs", []) or []:
        for lid in salida.get("links") or []:
            destino = enlaces.get(lid)
            nodo = nodos.get(destino[2]) if destino else None
            ins = (nodo or {}).get("inputs", [])
            if destino and destino[3] < len(ins) and entrada in ins[destino[3]].get("name", ""):
                return True
    return False


def _es_negativo(campo: _Campo) -> bool:
    return "negativ" in campo.titulo or _va_a(campo, "negative")


# ── Ficheros ─────────────────────────────────────────────────────

def _base(nombre: str) -> str:
    return re.split(r"[\\/]", nombre or "")[-1]


_EXTS = (".safetensors", ".gguf", ".ckpt", ".pth", ".pt", ".sft", ".bin")


def _sin_ext(nombre: str) -> str:
    """Nombre de fichero sin carpeta ni extensión de modelo. Solo esas: en
    «ltx-2.3-22b-distilled-Q4_0», splitext tomaba «.3-22b…» por extensión."""
    base = _base(nombre)
    raiz, ext = os.path.splitext(base)
    return raiz if ext.lower() in _EXTS else base


def _sin_precision(nombre: str) -> str:
    raiz = _sin_ext(nombre).lower()
    return "-".join(t for t in re.split(r"[-_.]+", raiz) if t and t not in _PRECISION)


def _instalado(valor: str, instalados: list) -> str | None:
    """El nombre con que ComfyUI lista `valor`: tal cual, por nombre de
    fichero (en una subcarpeta) o en otra precisión. None si no está."""
    if valor in instalados:
        return valor
    menos_anidado = lambda ns: min(ns, key=lambda n: (n.count("\\") + n.count("/"), n.lower()))  # noqa: E731
    mismos = [n for n in instalados if _base(n).lower() == _base(valor).lower()]
    if mismos:
        return menos_anidado(mismos)
    clave = _sin_precision(valor)
    variantes = [n for n in instalados if _sin_precision(n) == clave]
    return menos_anidado(variantes) if variantes else None


def _parecido(valor: str, instalados: list) -> str | None:
    """El instalado que más se parece por nombre (gemma4_e2b → gemma4_e4b):
    el que comparte más palabras del principio, y luego más palabras."""
    def palabras(n):
        return [t for t in re.split(r"[-_.]+", _sin_ext(n).lower()) if t and t not in _PRECISION]
    buscadas = palabras(valor)

    def puntos(n):
        suyas = palabras(n)
        prefijo = 0
        for a, b in zip(buscadas, suyas):
            if a != b:
                break
            prefijo += 1
        return prefijo, len(set(buscadas) & set(suyas))
    mejores = [n for n in instalados if puntos(n)[0] > 0]
    return max(sorted(mejores, key=str.lower), key=puntos) if mejores else None


def _llega_a(campo: _Campo, tipo: str, pasos: int = 3) -> bool:
    """True si la salida del nodo llega, en pocos pasos, a un nodo cuyo tipo
    contiene `tipo`."""
    enlaces, nodos = _enlaces(campo.contenedor), _nodos_por_id(campo.contenedor)
    frontera, vistos = [campo.nodo], set()
    for _ in range(pasos):
        siguiente = []
        for nodo in frontera:
            for salida in nodo.get("outputs", []) or []:
                for lid in salida.get("links") or []:
                    destino = nodos.get((enlaces.get(lid) or (None, None, None))[2])
                    if destino and id(destino) not in vistos:
                        if tipo in (destino.get("type") or ""):
                            return True
                        vistos.add(id(destino))
                        siguiente.append(destino)
        frontera = siguiente
    return False


def _dormido(campo: _Campo, campos: list) -> bool:
    """True si el cargador está en una rama que el workflow deja apagada: el
    mejorador de prompt (siempre se apaga) o una LoRA turbo cuyo interruptor
    está desactivado."""
    tipo = campo.nodo.get("type")
    if tipo == "CLIPLoader" and _llega_a(campo, "TextGenerate"):
        return True
    if tipo in ("LoraLoaderModelOnly", "LoraLoader") and re.search(
            r"lightning|lightx2v|turbo|\dstep", str(campo.valor).lower()):
        interruptores = [c for c in campos if c.nodo.get("type") == "PrimitiveBoolean"
                         and re.search(r"lightning|turbo", c.titulo)]
        return bool(interruptores) and all(c.valor is False for c in interruptores)
    return False


def _lista(nombres: dict, carpetas) -> list:
    return [n for c in carpetas for n in nombres.get(c, [])]


def fichero_del_modelo(modelo: str, nombres: dict) -> str | None:
    """El fichero de difusión del modelo elegido, como lo lista ComfyUI.

    El desplegable muestra el nombre sin extensión; las entradas curadas
    («LTX 2.5») no son un fichero, y entonces vale cualquiera instalado que
    use la misma plantilla.
    """
    instalados = _lista(nombres, ("diffusion_models", "unet", "checkpoints"))
    m = (modelo or "").lower()
    for n in instalados:
        if _sin_ext(n).lower() == m:
            return n
    tipo = _tipo_modelo(modelo)
    if tipo is None:
        return None
    for n in sorted(instalados, key=str.lower):
        if _tipo_modelo(n) == tipo:
            return n
    return None


def _poner_fichero(campo: _Campo, nuevo: str) -> None:
    """Cambia el fichero de un cargador y quita la descarga del original.

    Los cargadores de las plantillas llevan en properties.models el enlace
    de su fichero; si se queda, ComfyUI pide descargar un modelo que ya no
    se usa. Los que faltan de verdad conservan el suyo.
    """
    original = campo.valor
    campo.valor = nuevo
    if _base(original).lower() == _base(nuevo).lower():
        return
    modelos = (campo.nodo.get("properties") or {}).get("models")
    if isinstance(modelos, list):
        campo.nodo["properties"]["models"] = [
            m for m in modelos
            if not (isinstance(m, dict) and _base(m.get("name", "")).lower() == _base(original).lower())]


def _cambiar_cargador(campo: _Campo, gguf: bool) -> None:
    """UNETLoader ⇄ UnetLoaderGGUF (ComfyUI-GGUF), según el fichero."""
    nodo = campo.nodo
    tipo = "UnetLoaderGGUF" if gguf else "UNETLoader"
    if nodo.get("type") not in ("UNETLoader", "UnetLoaderGGUF") or nodo.get("type") == tipo:
        return
    nodo["type"] = tipo
    nodo.setdefault("properties", {})["Node name for S&R"] = tipo
    nodo["inputs"] = [i for i in nodo.get("inputs", []) if i.get("name") != "weight_dtype"]
    valores = nodo.get("widgets_values")
    if isinstance(valores, list) and valores:
        nodo["widgets_values"] = [valores[0]] if gguf else [valores[0], "default"]
        if campo.almacen is valores:
            campo.almacen = nodo["widgets_values"]


# ── Construcción ─────────────────────────────────────────────────

def _tam(ratio: str, ancho: int, alto: int) -> tuple:
    """El mismo número de píxeles que la plantilla, en el formato pedido,
    en múltiplos de 32 (lo piden LTX y Wan)."""
    try:
        a, b = (float(x) for x in ratio.split(":"))
    except (AttributeError, ValueError):
        return ancho, alto
    area = ancho * alto
    w = (area * a / b) ** 0.5
    return max(32, round(w / 32) * 32), max(32, round(w * b / a / 32) * 32)


def construir_workflow_video(modelo: str, prompt: str, negativo: str = "",
                             ratio: str = "", segundos: float = 0,
                             con_imagen: bool = False, carpetas: list = (),
                             nombres: dict | None = None) -> dict:
    """Workflow de vídeo desde la plantilla oficial, con lo nuestro dentro.

    Devuelve {"workflow", "plantilla", "fichero", "faltan", "imagen"} o
    {"error": texto} si no hay plantilla o no se encuentra dónde va el prompt.
    """
    nombres = nombres or {}
    plantilla = plantilla_para(modelo, con_imagen)
    if not plantilla:
        return {"error": "sin_plantilla"}
    original = cargar_plantilla(plantilla, carpetas)
    if original is None:
        return {"error": "plantilla_no_encontrada", "plantilla": plantilla}
    wf = copy.deepcopy(original)
    campos = _campos(wf)

    # 1. El prompt: lo que entra en un «positive», o si no, el texto de
    # ejemplo más largo que no sea el negativo. Algunas (SCAIL, Bernini)
    # traen la caja vacía.
    candidatos = [c for c in campos
                  if c.widget in ("text", "prompt", "value") and isinstance(c.valor, str)
                  and not _es_negativo(c) and "system" not in c.titulo
                  and (len(c.valor) >= 40 or _va_a(c, "positive"))]
    if not candidatos:
        return {"error": "sin_prompt", "plantilla": plantilla}
    elegido = max(candidatos, key=lambda c: (_va_a(c, "positive"),
                                             "prompt" in c.titulo or "positive" in c.titulo,
                                             len(c.valor)))
    ejemplo = elegido.valor
    for c in candidatos:
        if c is elegido or c.valor == ejemplo:
            c.valor = prompt

    # 2. El negativo, si la app escribió uno.
    if negativo:
        for c in campos:
            if isinstance(c.valor, str) and c.widget in ("text", "value") and _es_negativo(c):
                c.valor = negativo

    # 3. Fuera el mejorador de prompt de la plantilla: el prompt ya va escrito.
    for c in campos:
        if c.nodo.get("type") == "PrimitiveBoolean" and re.search(r"enhanc|upsampl", c.titulo):
            c.valor = False

    # Las que parten de un vídeo tuyo (SCAIL, Bernini, Animate…) toman de él
    # la duración y el tamaño: ahí no se tocan los fotogramas ni los píxeles.
    desde_video = any(n.get("type") == "LoadVideo"
                      for cont in [wf, *wf.get("definitions", {}).get("subgraphs", [])]
                      for n in cont.get("nodes", []))

    # 4. La duración.
    hay_duracion = False
    if segundos:
        for c in campos:
            if c.nodo.get("type") in ("PrimitiveInt", "PrimitiveFloat") and "duration" in c.titulo:
                c.valor = int(round(segundos)) if isinstance(c.valor, int) else float(segundos)
                hay_duracion = True
        if not hay_duracion and not desde_video:
            fps = next((c.valor for c in campos if c.widget == "fps"
                        and isinstance(c.valor, (int, float))), 16)
            for c in campos:
                if c.widget == "length" and isinstance(c.valor, int):
                    c.valor = 4 * round(segundos * fps / 4) + 1

    # 5. El formato.
    if ratio:
        for c in campos:
            if c.nodo.get("type") == "ResolutionSelector" and c.widget == "aspect_ratio":
                if ratio in _ASPECTOS:
                    c.valor = _ASPECTOS[ratio]
        pares = {}
        for c in campos if not desde_video else []:
            if c.widget in ("width", "height") and isinstance(c.valor, int):
                pares.setdefault(id(c.nodo), {})[c.widget] = c
            elif c.titulo in ("width", "height") and isinstance(c.valor, int):
                pares.setdefault("primitivas", {})[c.titulo] = c
        for par in pares.values():
            if "width" in par and "height" in par:
                w, h = _tam(ratio, par["width"].valor, par["height"].valor)
                par["width"].valor, par["height"].valor = w, h

    # 6. El modelo elegido, en su cargador (y su pareja high/low en Wan 2.2).
    # Solo se cambian los cargadores cuyo fichero es del mismo tipo que el
    # elegido: SCAIL carga además el checkpoint de SAM3, y con imagen, un Wan
    # t2v cae en la plantilla i2v, cuyos modelos i2v no se pueden sustituir.
    fichero = fichero_del_modelo(modelo, nombres)
    avisos = []
    tipo = _tipo_modelo(modelo)
    principales = [c for c in campos
                   if (c.nodo.get("type"), c.widget) in _CARGADORES_PRINCIPALES
                   and isinstance(c.valor, str) and _tipo_modelo(c.valor) == tipo]
    if fichero and principales:
        instalados = _lista(nombres, ("diffusion_models", "unet", "checkpoints"))
        es_checkpoint = fichero in nombres.get("checkpoints", [])
        for c in principales:
            # Un checkpoint completo trae dentro su VAE (y en LTX 2.3, el
            # audio): un modelo de difusión suelto, o un GGUF, no cabe en su
            # cargador sin rehacer la plantilla.
            if (c.nodo.get("type") == "CheckpointLoaderSimple") != es_checkpoint:
                aviso = (f"La plantilla carga «{c.valor}» como checkpoint completo; "
                         f"tu «{_base(fichero)}» no va en ese cargador.")
                if aviso not in avisos:
                    avisos.append(aviso)
                continue
            destino = fichero
            rol = next((r for r in ("high_noise", "low_noise") if r in c.valor.lower()), None)
            otro = {"high_noise": "low_noise", "low_noise": "high_noise"}.get(rol)
            if rol and otro in fichero.lower():
                destino = _instalado(re.sub(otro, rol, fichero, flags=re.I), instalados)
                if not destino:
                    continue
            _poner_fichero(c, destino)
            _cambiar_cargador(c, destino.lower().endswith(".gguf"))
    elif fichero and con_imagen and plantilla_para(modelo) != plantilla:
        avisos.append(f"Con imagen, esta es la plantilla de imagen a vídeo; tu "
                      f"«{_base(fichero)}» es de texto a vídeo y no va en ella.")

    # 7. El resto de ficheros, con el nombre con que los lista tu ComfyUI.
    faltan = []
    for c in campos:
        carpetas_tipo = _CARPETAS.get((c.nodo.get("type"), c.widget))
        if not carpetas_tipo or not isinstance(c.valor, str) or not c.valor:
            continue
        instalados = _lista(nombres, carpetas_tipo)
        hallado = _instalado(c.valor, instalados)
        if hallado:
            _poner_fichero(c, hallado)
            continue
        # ComfyUI valida también las ramas apagadas: sin el fichero del
        # mejorador de prompt, o de la LoRA turbo desactivada, rechaza el
        # workflow entero. Ahí, y solo ahí, vale uno parecido que sí esté:
        # esa parte no se ejecuta.
        parecido = _parecido(c.valor, instalados) if _dormido(c, campos) else None
        if parecido:
            avisos.append(f"«{_base(c.valor)}» no lo tienes; esa parte va apagada y he "
                          f"puesto «{_base(parecido)}» para que ComfyUI no se pare.")
            _poner_fichero(c, parecido)
        elif nombres and c.valor not in faltan:
            faltan.append(c.valor)

    imagen = any(n.get("type") in ("LoadImage", "LoadVideo", "LoadAudio")
                 for cont in [wf, *wf.get("definitions", {}).get("subgraphs", [])]
                 for n in cont.get("nodes", []))
    _anadir_nota(wf, modelo, plantilla, faltan, imagen, avisos)
    return {"workflow": wf, "plantilla": plantilla, "fichero": fichero,
            "faltan": faltan, "imagen": imagen, "avisos": avisos}


def _anadir_nota(wf: dict, modelo: str, plantilla: str, faltan: list, imagen: bool,
                 avisos: list = ()) -> None:
    lineas = [f"G-Prompt Studio · {modelo}",
              f"Plantilla oficial de ComfyUI: {plantilla}",
              "El prompt ya va escrito: el mejorador de prompt de la plantilla, apagado."]
    lineas += list(avisos)
    if imagen:
        lineas.append("Carga tus ficheros en los nodos Load Image / Load Video / Load Audio.")
    if faltan:
        lineas.append("No están en tu ComfyUI (te ofrecerá descargarlos):")
        lineas += [f"  • {f}" for f in faltan]
    nodos = wf.setdefault("nodes", [])
    nuevo_id = max([wf.get("last_node_id") or 0, *(n.get("id", 0) for n in nodos
                                                     if isinstance(n.get("id"), int))]) + 1
    def _pos(n):
        p = n.get("pos") or [0, 0]
        return [p.get("0", 0), p.get("1", 0)] if isinstance(p, dict) else p
    x = min((_pos(n)[0] for n in nodos), default=0) - 460
    y = min((_pos(n)[1] for n in nodos), default=0)
    nodos.append({"id": nuevo_id, "type": "Note", "pos": [x, y], "size": [420, 220],
                  "flags": {}, "order": len(nodos), "mode": 0, "inputs": [],
                  "outputs": [], "properties": {}, "widgets_values": ["\n".join(lineas)],
                  "color": "#432", "bgcolor": "#653"})
    wf["last_node_id"] = nuevo_id
