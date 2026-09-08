"""
G-Prompt Studio v1.0 — Configuración y constantes.
Modelos, estilos, ratios, presets de negativos, colores UI.
"""
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)


# Cargador de datos JSON
# Datos grandes (MODEL_SPECS, ESTILOS_GRUPOS, BIBLIOTECA_EJEMPLOS...)
# viven en data/*.json para que añadir/editar modelos no requiera
# tocar este archivo y para mantener config.py legible.
#
# Lazy loading: los datasets se cargan la primera vez que se accede
# a ellos vía __getattr__ (PEP 562). Esto reduce el tiempo de arranque
# cuando un módulo solo necesita parte de las constantes.
import json as _json

_DATA_DIR = Path(__file__).resolve().parent / "data"

# Copia EDITABLE por el usuario. Los datos empaquetados viajan DENTRO del .exe
# (ver ('data','data') en gprompt-studio.spec), asi que son de solo lectura: sin
# esto, tocar un JSON del repo no cambiaba nada en un .exe ya construido. Si el
# usuario deja aqui un fichero con el mismo nombre, MANDA sobre el empaquetado,
# y puede anadir modelos o estilos sin recompilar.
_DATA_DIR_USUARIO = Path.home() / ".arquitecto_prompts" / "data"


def _load_json_data(filename: str):
    """Carga data/<filename> y devuelve el objeto deserializado.

    Prioridad: copia del usuario (_DATA_DIR_USUARIO) -> copia empaquetada.
    Si la del usuario existe pero esta corrupta se avisa y se usa la
    empaquetada: una edicion a mano con una coma de mas no debe dejar la
    aplicacion sin arrancar.
    """
    override = _DATA_DIR_USUARIO / filename
    if override.is_file():
        try:
            with open(override, "r", encoding="utf-8") as f:
                return _json.load(f)
        except Exception as e:
            print(f"[config] {filename}: override de usuario invalido ({e}); "
                  f"se usa el empaquetado")
    path = _DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return _json.load(f)

# Catalogos de modelos por grupo. Viven en datos (no en codigo) para poder
# anadir modelos sin tocar Python: con el override de _DATA_DIR_USUARIO basta
# dejar modelos_grupos.json en ~/.arquitecto_prompts/data/ y no hay que
# recompilar el .exe.
_GRUPOS_DATA = _load_json_data("modelos_grupos.json")


def _grupos(clave: str) -> list:
    """Devuelve [(cabecera, [modelos...])] del catalogo `clave`."""
    return [(cab, list(modelos)) for cab, modelos in _GRUPOS_DATA[clave]]


# Mapa de constantes lazy → archivo en data/. Solo cuando se accede al
# atributo por primera vez (vía __getattr__) se hace I/O y se cachea.
_LAZY_DATASETS = {
    "MODEL_SPECS":          "model_specs_video.json",
    "MODEL_SPECS_VIDEO":    "model_specs_video.json",
    "MODEL_SPECS_IMAGEN":   "model_specs_imagen.json",
    "MODEL_SPECS_AUDIO":    "model_specs_audio.json",
    "ESTILO_NEGATIVO_AUTO": "estilo_negativo_auto.json",
    "BIBLIOTECA_EJEMPLOS":  "biblioteca_ejemplos.json",
}
_lazy_cache: dict = {}

def _get_dataset(name: str):
    """Devuelve el dataset cargado bajo demanda y cacheado."""
    if name not in _lazy_cache:
        _lazy_cache[name] = _load_json_data(_LAZY_DATASETS[name])
    return _lazy_cache[name]

def __getattr__(name):
    """PEP 562 — resuelve atributos lazy del módulo.

    Se invoca solo cuando un atributo no existe en globals(). Permite
    que `from config import MODEL_SPECS_IMAGEN` siga funcionando, pero
    sin cargar el JSON hasta el primer acceso.
    """
    if name in _LAZY_DATASETS:
        return _get_dataset(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# ── Versión ───────────────────────────────────────────────────────
VERSION = "1.0.0"
PUBLIC_VERSION = "1.0.0"
APP_TITLE = f"G-Prompt Studio v{PUBLIC_VERSION}"

# ── Persistencia ──────────────────────────────────────────────────
# Única carpeta para todo: datos, keys, logs y backups.
CARPETA_APP = Path.home() / ".arquitecto_prompts"
LOGS_DIR    = CARPETA_APP / "logs"
BACKUPS_DIR = CARPETA_APP / "backups"
CARPETA_APP.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
BACKUPS_DIR.mkdir(exist_ok=True)

ARCHIVOS = {
    "historial":     CARPETA_APP / "historial.json",
    "favoritos":     CARPETA_APP / "favoritos.json",
    "personajes":    CARPETA_APP / "personajes.json",
    "plantillas":    CARPETA_APP / "plantillas.json",
    "loras":         CARPETA_APP / "loras.json",
    "paletas":       CARPETA_APP / "paletas.json",
    "preferencias":  CARPETA_APP / "preferencias.json",
    "estrellas":     CARPETA_APP / "estrellas.json",
    "keys":          CARPETA_APP / "keys.json",
    "active_provider": CARPETA_APP / "active_provider.txt",
    "active_models":   CARPETA_APP / "active_models.json",
    "autobackup_marker": CARPETA_APP / "_last_autobackup.txt",
    "modelos_comfy": CARPETA_APP / "mis_modelos_comfy.json",
    "comfy_cache":   CARPETA_APP / "comfy_cache.json",
}

# ── Modelos Ollama Vision ─────────────────────────────────────────
MODELOS_OLLAMA_VISION = [
    "llama3.2-vision:latest", "qwen2.5vl:latest",
    "llava:latest", "moondream:latest",
]

# ── Modelos Gemini Vision ─────────────────────────────────────────
MODELOS_GEMINI_CANDIDATOS = [
    "gemini-2.5-flash", "gemini-2.0-flash",
    "gemini-1.5-flash", "gemini-2.0-flash-lite",
]

# ── Modelos OpenRouter Vision ─────────────────────────────────────
MODELOS_OPENROUTER_VISION = [
    "meta-llama/llama-4-scout:free",
    "qwen/qwen2.5-vl-72b-instruct:free",
    "google/gemma-3-27b-it:free",
]

# ── ADN Visual Schema ────────────────────────────────────────────
ADN_SCHEMA = {
    "sujeto": {
        "tipo": str, "genero": str, "edad_aprox": str, "etnia": str,
        "cabello": dict, "ojos": dict, "ropa": dict, "pose": dict, "expresion": dict,
        "piel_tono": str, "cicatrices_marcas": str
    },
    "escena": {
        "ubicacion_exacta": str, "interior_exterior": str, "ambiente": str,
        "elementos_principales": list, "elementos_secundarios": list,
        "objetos_en_escena": list, "profundidad_z": str, "espacio_negativo": str
    },
    "iluminacion": {
        "tipo_exacto": str, "direccion_precisa": str, "intensidad_exacta": str,
        "hora_dia_exacta": str, "color_temperatura_kelvin": str,
        "fuentes_luminosas": list, "sombras_dureza": str, "reflejos_superficies": str,
        "luz_ambiental_porcentaje": str
    },
    "camara": {
        "encuadre_exacto": str, "angulo_exacto": str, "distancia_focal_mm": str,
        "apertura_f": str, "profundidad_campo_exacta": str, "distorsion_lente": str,
        "movimiento_camara": str, "estabilidad": str
    },
    "estilo": {
        "estetica_exacta": str, "movimiento_artistico": str, "epoca_referenciada": str,
        "tecnica_precisa": str, "paleta_exacta_5colores": list,
        "texturas_visibles": list, "finish_superficial": str
    },
    "composicion": {
        "regla_exacta": str, "punto_foco_exacto": str, "lineas_principales": list,
        "lineas_secundarias": list, "equilibrio_visual": str,
        "peso_visual": str, "espacio_activo": str
    },
    "atmosfera": {
        "estado_animo_exacto": str, "energia_exacta": str,
        "temperatura_emocional": str, "elementos_ambientales": list,
        "densidad_atmosferica": str
    },
    "tecnico": {
        "grano_exacto": str, "contraste_exacto": str, "saturacion_exacta": str,
        "rango_dinamico": str, "postprocesos_exactos": list,
        "efectos_visibles": list, "calidad_render": str
    }
}

# ── Conversión ADN por plataforma ─────────────────────────────────
# IMPORTANTE: los placeholders {clave} deben coincidir exactamente con las
# claves que produce VISION_SYSTEM_PROMPT y que tools_creative.py pasa al .format().
# Si cambias un placeholder aquí, actualiza también tools_creative._convertir_plataforma.
ADN_A_PLATAFORMA = {
    "midjourney": {
        "sujeto": "{tipo}, {ropa}, {pose}, {expresion}",
        "estilo": "--style {estetica_exacta} --ar 16:9",
        "iluminacion": "--lighting {tipo_exacto}",
        "camara": "--{angulo_exacto} --{encuadre_exacto}"
    },
    "stable_diffusion": {
        "sujeto": "1person, {ropa}, {pose}",
        "estilo": "{estetica_exacta}, {tecnica_precisa}",
        "iluminacion": "{tipo_exacto} lighting",
        "tags": "{paleta_exacta_5colores}"
    },
    "dalle": {
        "sujeto": "{tipo} wearing {ropa}, {pose}",
        "estilo": "{estetica_exacta} style, {tecnica_precisa}",
        "atm": "{estado_animo_exacto} mood"
    },
    "flux": {
        "sujeto": "portrait of {tipo}, {ropa}, {pose}",
        "estilo": "{estetica_exacta}, detailed, high quality",
        "escena": "{ubicacion_exacta}, {tipo_exacto}"
    }
}

# ══════════════════════════════════════════════════════════════════
# MODELOS DE VÍDEO
# ══════════════════════════════════════════════════════════════════
# Reference-to-video: subes imagenes de personajes/objetos y etiquetas
# con @ref. El prompt describe la escena -> flujo del modo Cortometraje.
# "Drama" = cine/cortometraje . "Ad" = anuncios/publicidad.
GRUPOS_VIDEO = _grupos("video")
# Familias en orden alfabético (case-insensitive), ignorando los ── decorativos.
GRUPOS_VIDEO = sorted(GRUPOS_VIDEO, key=lambda g: g[0].strip("─ ").lower())

# ══════════════════════════════════════════════════════════════════
# MODELOS DE IMAGEN
# ══════════════════════════════════════════════════════════════════
GRUPOS_IMAGEN = _grupos("imagen")

# ══════════════════════════════════════════════════════════════════
# RUTA COMFYUI Y AUTO-DISCOVERY DE MODELOS
# ══════════════════════════════════════════════════════════════════

def get_comfyui_path(preferencias: dict = None) -> str:
    """Obtiene la ruta de ComfyUI configurada en preferencias."""
    if preferencias:
        return preferencias.get("comfyui_path", "") or ""
    return ""


def guardar_comfyui_path(ruta: str, store) -> bool:
    """Guarda la ruta de ComfyUI en preferencias."""
    try:
        prefs = store.cargar_preferencias() or {}
        prefs["comfyui_path"] = ruta
        store.guardar_preferencias(prefs)
        return True
    except Exception:
        return False


# Tokens (case-insensitive) para clasificar un checkpoint por su nombre de
# fichero. Se prueban contra el stem en minúscula. AUDIO y VÍDEO tienen
# prioridad; si no encaja ninguno, se asume IMAGEN.
# NOTA: ACE-Step va en _COMFY_EXCLUIR_TOKENS (se elimina del escaneo, el
# usuario no lo usa desde la herramienta), no en esta lista.
_COMFY_TOKENS_AUDIO = (
    "musicgen", "stable_audio",
    "stableaudio", "audioldm", "mmaudio",
)
_COMFY_TOKENS_VIDEO = (
    "wan", "ltx", "ltxv", "svd", "i2v", "t2v", "video", "stable_video",
    "stable-video", "hunyuanvideo", "hunyuan_video", "hunyuan-video",
    "cogvideo", "mochi", "animatediff",
    # MiniMax/Hailuo local (minimax_h3_fl2va…): el usuario confirma que es
    # vídeo (ago-2026). 'ltxv' porque los ficheros LTX-Video suelen llamarse
    # 'ltxv-…' y el token 'ltx' (límite de palabra) NO casa con 'ltxv'.
    "minimax", "hailuo",
)
# Tokens "fast" (pocos pasos, CFG~1): el modelo IGNORA NEGATIVE y pesos
# numéricos. Fuente única; prompt_logic.es_comfyui_turbo los reutiliza.
COMFY_TURBO_TOKENS = (
    "turbo", "schnell", "lightning", "hyper-sd", "hypersd",
    "hyper sd", "lcm", "dmd2", "nitro", "flash",
)
# Carpetas de ComfyUI que contienen checkpoints/UNets utilizables como modelo.
_COMFY_SUBDIRS = ("checkpoints", "diffusion_models", "unet")
_COMFY_EXTS = (".safetensors", ".ckpt", ".pth", ".gguf", ".sft")

# Ficheros que NO sirven en un generador de prompts y se excluyen del escaneo:
# refinadores (2ª pasada, sin prompt propio), SVD (image-to-video puro que
# ignora el texto), piezas sueltas de un pipeline (transformer_only), modelos
# de inpainting (necesitan máscara + imagen) y ACE-Step (audio).
# NOTA (jul-2026): Ideogram 4 pasó a ser un modelo de IMAGEN local real
# (ideogram4_fp8_transformer + su encoder/VAE en el inventario del usuario),
# así que YA NO se excluye; tiene familia y specs propias.
# NOTA (ago-2026): SUPIR es un upscaler/restaurador (no genera desde texto),
# hunyuan3d genera malla 3D (no imagen 2D) y stable_cascade_stage_b/c son
# piezas sueltas de un pipeline de 2 etapas — ninguno sirve como modelo
# destino de prompts, así que se excluyen del escaneo.
# Subcarpetas que NO contienen modelos generables aunque cuelguen de
# checkpoints/ o unet/. El formato HuggingFace reparte un modelo en
# transformer/, text_encoder/ y vae/, y el escaneo recursivo se tragaba las
# piezas sueltas: en el equipo del usuario colaba 'model' (235 MB) desde
# unet/flux_unchained/text_encoder/ como si fuera un checkpoint.
_COMFY_CARPETAS_EXCLUIDAS = frozenset({
    "text_encoder", "text_encoders", "text_encoder_2", "tokenizer",
    "tokenizer_2", "vae", "vae_decoder", "vae_encoder", "clip", "clip_vision",
    "scheduler", "feature_extractor", "safety_checker", ".cache",
})

# Carpetas cuyo NOMBRE nombra la familia. El usuario organiza sus checkpoints
# en SDXL/, Flux/, SD15/, ZImage/, Krea2/... y hasta ahora esa informacion se
# tiraba: 'playground-v2.5-1024px-aesthetic.fp16' vivia en checkpoints/SDXL/ y
# salia sin familia. El nombre del fichero sigue mandando; la carpeta solo
# entra cuando el nombre no dice nada.
_COMFY_CARPETA_FAMILIA = {
    "sdxl": "sdxl", "sd15": "sd15", "sd1.5": "sd15", "flux": "flux",
    "flux_unchained": "flux", "krea": "krea", "krea2": "krea",
    "zimage": "z_image", "z_image": "z_image", "z-image": "z_image",
    "pony": "pony", "illustrious": "illustrious", "qwen": "qwen",
    "ideogram": "ideogram", "hidream": "hidream",
}
# stem normalizado -> familia deducida de su carpeta (lo rellena el escaneo)
_COMFY_FAMILIA_CARPETA: dict = {}


_COMFY_EXCLUIR_TOKENS = ("refiner", "transformer_only", "svd", "inpainting",
                         "inpaint", "acestep", "ace_step", "ace-step",
                         "supir", "hunyuan3d", "stable_cascade",
                         # 3D: generan mallas o splats, no imagenes. Salian en
                         # el desplegable de IMAGEN y elegirlos no podia
                         # funcionar. 'hunyuan3d' ya estaba pero NO cazaba
                         # 'hunyuan_3d_v2.1' (guion bajo) — de ahi las
                         # variantes. Confirmado en el inventario del usuario
                         # el 08-sep-2026: hunyuan_3d_v2.1 (6,9 GB) y
                         # triposplat_fp16 (707 MB).
                         "hunyuan_3d", "hunyuan-3d", "triposplat", "tripo",
                         "trellis", "sf3d", "instantmesh", "zero123", "splat",
                         # Pieza suelta del pipeline LTX (proyección de texto),
                         # no un modelo generable: 'ltx-2.3_text_projection_bf16'.
                         "text_projection",
                         # No-generativos desde texto (sep-2026, confirmado por
                         # el usuario): rife=interpolador de frames ('rife49'),
                         # cosmos=world model Text2World de NVIDIA, relight_lora=
                         # LoRA de reiluminación ('WanAnimate_relight_lora').
                         "rife", "cosmos", "relight_lora")


# Tokens cortos que aparecen dentro de palabras normales ("swan", "wanostyle",
# "mochimix" clasificarían mal como vídeo): solo casan si NO están pegados a
# otra letra. Dígitos y separadores SÍ cuentan como límite, así "wan2.2",
# "svd_xt" o "ltx-2.3" siguen casando. El resto de tokens ("xl", "pony",
# "noobai"...) se mantiene como substring porque la convención real los pega
# al nombre ("juggernautXL", "T-ponynai3", "CogVideoX").
_TOKENS_LIMITE_PALABRA = frozenset({"wan", "svd", "ltx", "i2v", "t2v", "mochi"})


def _token_en_nombre(token: str, nombre_lower: str) -> bool:
    """True si `token` aparece en el nombre (con límite de palabra si es ambiguo)."""
    if token in _TOKENS_LIMITE_PALABRA:
        return re.search(rf"(?<![a-z]){re.escape(token)}(?![a-z])",
                         nombre_lower) is not None
    return token in nombre_lower


def clasificar_modelo_comfy(nombre: str) -> str:
    """Clasifica un checkpoint ComfyUI por su nombre: 'audio' | 'video' | 'imagen'."""
    n = (nombre or "").lower()
    if any(_token_en_nombre(t, n) for t in _COMFY_TOKENS_AUDIO):
        return "audio"
    if any(_token_en_nombre(t, n) for t in _COMFY_TOKENS_VIDEO):
        return "video"
    return "imagen"


def _resolver_junction(carpeta: Path):
    """Ruta REAL de una carpeta cuando se llega a ella por un junction.

    Windows 11 no deja recorrer un junction creado por un usuario sin permisos
    de administrador (Redirection Guard): [WinError 448] "punto de montaje no
    confiable". El equipo del autor tiene

        C:/IA/ComfyUI/models  ->  D:/ComfyUI/models

    y la app se quedaba SIN NINGUN modelo local aunque la carpeta se lea
    perfectamente desde una consola. Entrando por D:/ ya no hay redireccion
    que vigilar y el escaneo funciona.

    Returns: la ruta real, o None si no hay junction o tampoco se puede leer.
    """
    try:
        real = Path(os.path.realpath(str(carpeta)))
    except OSError as e:
        logger.debug(f"[silent] no se pudo resolver {carpeta}: {e}")
        return None
    if real == carpeta:
        return None          # no era un junction: el fallo es otro
    try:
        if not real.exists():
            return None
    except OSError as e:
        logger.debug(f"[silent] la ruta real tampoco se lee: {e}")
        return None
    return real


def _escanear_comfy_root(ruta_comfyui: Path) -> dict:
    """Escanea models/{checkpoints,diffusion_models,unet} de forma recursiva.

    Returns:
        dict {'imagen': [...], 'video': [...], 'audio': [...]} con los stems
        ordenados (case-insensitive) y sin duplicados entre carpetas.
    """
    hallados = {"imagen": set(), "video": set(), "audio": set()}
    for sub in _COMFY_SUBDIRS:
        carpeta = ruta_comfyui / "models" / sub
        # exists() normalmente devuelve False ante un error, pero solo se traga
        # los de "no encontrado": un [WinError 448] "punto de montaje no
        # confiable" LO PROPAGA y antes tumbaba el escaneo COMPLETO, dejando al
        # usuario sin ningun modelo local. Visto 16 veces en el log del usuario
        # sobre C:\IA\ComfyUI\models\checkpoints (jul-sep 2026), aunque la
        # carpeta se lee bien desde una consola normal.
        try:
            if not carpeta.exists():
                continue
        except OSError as e:
            # Antes se saltaba la carpeta y se seguia: no habia crash, pero el
            # usuario se quedaba con CERO modelos, que para el es lo mismo.
            # Casi siempre es un junction, asi que se reintenta por la ruta
            # real antes de rendirse.
            real = _resolver_junction(carpeta)
            if real is None:
                logger.warning(f"ComfyUI: no se puede acceder a {carpeta}: {e}")
                continue
            logger.info(f"ComfyUI: {carpeta} redirige a {real}; se entra por ahi")
            carpeta = real

        # rglob tambien puede reventar a media recorrida (un subdirectorio
        # inaccesible, un enlace roto). Se recorre tolerando fallos para
        # quedarse con lo que SI se pudo leer, en vez de con nada.
        try:
            for f in carpeta.rglob("*"):
                try:
                    if not (f.is_file() and f.suffix.lower() in _COMFY_EXTS):
                        continue
                except OSError as e:
                    logger.debug(f"[silent] ComfyUI: {f}: {e}")
                    continue
                try:
                    partes = [p.lower() for p in f.relative_to(carpeta).parts[:-1]]
                except Exception:
                    partes = []
                if any(p in _COMFY_CARPETAS_EXCLUIDAS for p in partes):
                    continue
                stem_l = f.stem.lower()
                if any(_token_en_nombre(t, stem_l) for t in _COMFY_EXCLUIR_TOKENS):
                    continue
                # La carpeta como pista de familia, de la mas profunda a la mas
                # externa: checkpoints/SDXL/x.safetensors -> sdxl.
                for p in reversed(partes):
                    fam_dir = _COMFY_CARPETA_FAMILIA.get(p)
                    if fam_dir:
                        _COMFY_FAMILIA_CARPETA[_norm_nombre_comfy(f.stem)] = fam_dir
                        break
                hallados[clasificar_modelo_comfy(f.stem)].add(f.stem)
        except OSError as e:
            logger.warning(
                f"ComfyUI: recorrido de {carpeta} interrumpido ({e}); "
                f"se conserva lo encontrado hasta ahora")
    return {k: sorted(v, key=str.lower) for k, v in hallados.items()}


def escanear_modelos_comfyui(ruta_comfyui: str = None, preferencias: dict = None) -> tuple:
    """
    Escanea la carpeta de ComfyUI para encontrar modelos instalados.

    Recorre checkpoints + diffusion_models + unet (recursivo, incluye
    subcarpetas) y clasifica cada fichero en imagen/vídeo/audio por su nombre.

    Returns:
        tuple: (grupos_img, grupos_vid) - listas de tuplas (grupo, [modelos])
    """
    if not ruta_comfyui:
        ruta_comfyui = get_comfyui_path(preferencias)

    if not ruta_comfyui or not Path(ruta_comfyui).exists():
        return None, None

    hallados = _escanear_comfy_root(Path(ruta_comfyui))
    grupos_img = [("── ComfyUI Local ──", hallados["imagen"])] if hallados["imagen"] else None
    grupos_vid = [("── ComfyUI Video ──", hallados["video"])] if hallados["video"] else None
    return grupos_img, grupos_vid


# ── Familias ComfyUI por nombre → specs sintéticas ────────────────
# Permiten que la inyección de prompt sea correcta (formato natural vs tags,
# soporte de NEGATIVE, sampler sugerido) para checkpoints locales que NO están
# en el JSON curado. Robusto a renombrados: detecta por substring del nombre.
# (clave, tokens) — orden de específico → genérico; gana el primero que casa.
_COMFY_FAMILIAS = (
    # 'krea' (Flux.1/2 Krea de BFL+Krea) es arquitectura Flux, pero el usuario
    # lo quiere como grupo propio "Krea" (ago-2026). VA ANTES de flux porque
    # varios ficheros llevan AMBOS tokens ('flux1KreaDev…') y krea debe ganar.
    # Sus specs de prompt son Flux-like; el workflow deja CLIP/VAE en blanco
    # (los ficheros Krea son heterogéneos: all-in-one, GGUF, fp8).
    ("krea",        ("krea",)),
    # 'chroma' (des-destilado de Flux.1 schnell) sigue en Flux: prosa natural,
    # CFG real, encoder T5. Token → captura variantes futuras.
    ("flux",        ("flux", "chroma")),
    ("z_image",     ("z_image", "zimage", "z-image")),
    ("hidream",     ("hidream",)),
    ("ideogram",    ("ideogram",)),
    ("qwen",        ("qwen",)),
    ("pony",        ("pony",)),
    ("illustrious", ("illustrious", "noobai", "noob")),
    ("sd15",        ("512-", "_512", "sd15", "sd_1.5", "sd-1.5", "v1-5", "1.5-pruned")),
    ("sdxl",        ("sdxl", "sd_xl", "sd-xl", "juggernaut", "realvis", "dreamshaper", "ragnarok", "stockphoto", "xl")),
)

# Nombres legibles de familia para las cabeceras del desplegable
# (autodiscovery agrupa por familia; '' = sin familia reconocida).
_COMFY_FAMILIA_LABELS = {
    "flux": "Flux", "krea": "Krea", "z_image": "Z-Image", "ideogram": "Ideogram",
    "qwen": "Qwen", "pony": "Pony", "illustrious": "Illustrious",
    "sd15": "SD 1.5 (Fooocus)", "sdxl": "SDXL (Fooocus)", "": "Otros",
}
_COMFY_FAMILIA_LABELS_VIDEO = {
    "ltx": "LTX", "wan": "Wan", "svd": "SVD", "hunyuan": "Hunyuan",
    "cogvideo": "CogVideo", "mochi": "Mochi", "minimax": "MiniMax", "": "Otros",
}


def _norm_nombre_comfy(s: str) -> str:
    """Normaliza para deduplicar manifest vs autodiscovery: el manifest suele
    tener nombres embellecidos ('Juggernaut-XL v9 ...', 'z_image_bf16 (Base)')
    del mismo fichero que el escaneo halla como stem crudo."""
    s = re.sub(r"\([^)]*\)", "", s or "")
    return re.sub(r"[^a-z0-9]", "", s.lower())


# Descripciones por checkpoint local (INVENTARIO_MODELOS.md del usuario,
# jul-2026). Clave = nombre normalizado con _norm_nombre_comfy; valor =
# (descripción ES, descripción EN). Se anteponen al best_for de la familia
# para que el hint bajo el combo describa el modelo concreto, como en SeaArt.
_COMFY_DESC_LOCAL = {
    "realisticstockphotov20": ("Foto stock ultra realista", "Ultra-realistic stock photo"),
    "realvisxlv50fp16": ("Fotorrealismo extremo", "Extreme photorealism"),
    "juggernautxlv9rundiffusionphotov2": ("Retratos realistas", "Realistic portraits"),
    "juggernautxlragnarokby": ("Retratos artísticos", "Artistic portraits"),
    "juggernautxlv8rundiffusion": ("Versátil, todoterreno", "Versatile all-rounder"),
    "animapencilxlv500": ("Ilustración / dibujo", "Illustration / drawing"),
    "sdxlbase1009vae": ("SDXL base oficial", "Official SDXL base"),
    "flux2klein9bfp8": ("Flux 2 Klein 9B", "Flux 2 Klein 9B"),
    "flux2klein9bkvfp8": ("Flux 2 Klein 9B (variante KV)", "Flux 2 Klein 9B (KV variant)"),
    "flux2kleinbase4bfp8": ("Flux 2 Klein 4B, ligero y rápido", "Flux 2 Klein 4B, light and fast"),
    "zimagebf16": ("Z-Image Base 6B (S3-DiT)", "Z-Image Base 6B (S3-DiT)"),
    "zimageturbobf16": ("Z-Image Turbo, destilado y rápido", "Z-Image Turbo, distilled and fast"),
    "qwenimageedit2509fp8e4m3fn": ("Qwen Image Edit: edición por instrucciones", "Qwen Image Edit: instruction-based editing"),
    "ideogram4fp8transformer": ("Ideogram 4: prompt-adherence y texto en imagen", "Ideogram 4: prompt-adherence and in-image text"),
    "wan22i2vhighnoise14bfp8scaled": ("Wan 2.2 i2v 14B — etapa high noise", "Wan 2.2 i2v 14B — high-noise stage"),
    "wan22i2vlownoise14bfp8scaled": ("Wan 2.2 i2v 14B — etapa low noise", "Wan 2.2 i2v 14B — low-noise stage"),
    "ltx2322bdev": ("LTX 2.3 22B: vídeo con audio nativo", "LTX 2.3 22B: video with native audio"),
    "uberrealisticpornmergeponyxlponyxlhybridv1": ("Pony XL fotorrealista NSFW", "Photoreal NSFW Pony XL"),
}


def _aplicar_desc_local(nombre: str, specs: dict) -> dict:
    """Antepone la descripción curada del checkpoint local (si existe) al
    best_for genérico de su familia. Muta y devuelve `specs`."""
    d = _COMFY_DESC_LOCAL.get(_norm_nombre_comfy(nombre))
    if d:
        specs["best_for"] = f"{d[0]} · {specs.get('best_for', '')}".strip(" ·")
        if specs.get("best_for_en"):
            specs["best_for_en"] = f"{d[1]} · {specs['best_for_en']}".strip(" ·")
    return specs


def _agrupar_por_familia(nombres, detector, labels, prefijo):
    """Agrupa checkpoints por familia detectada → [(cabecera, [modelos])].

    Cabeceras "── {prefijo} · {Familia} ──" ordenadas alfabéticamente;
    modelos ordenados case-insensitive dentro de cada grupo.
    """
    por_fam = {}
    for n in nombres:
        por_fam.setdefault(detector(n), []).append(n)
    grupos = []
    for fam in sorted(por_fam, key=lambda f: labels.get(f, "Otros").lower()):
        label = f"── {prefijo} · {labels.get(fam, 'Otros')} ──"
        grupos.append((label, sorted(por_fam[fam], key=str.lower)))
    return grupos


# Negatives base por familia (guía de prompts del usuario, probados en local
# jul-2026). Se inyectan como sugerencia al LLM cuando la familia usa negative.
_NEG_FLUX_QWEN_ZIMAGE = (
    "blurry, low quality, deformed, ugly, cartoon, anime, 3D, text, watermark, "
    "signature, oversaturated, flat lighting, smooth skin, plastic texture"
)
_NEG_SDXL = (
    "worst quality, low quality, blurry, jpeg artifacts, overexposed, cartoon, "
    "anime, deformed hands, ugly face, dark shadows, bad anatomy, text, watermark, "
    "smooth skin, cloned face, multiple people"
)

_COMFY_SPECS_FAMILIA = {
    "flux": {
        # Flux 2 Klein (local): a diferencia de Flux.1 (guidance destilada, CFG~1),
        # Flux 2 reintroduce CFG real (~3.5) y SÍ responde a negative prompt.
        # Confirmado por testing local del usuario (jul-2026).
        "is_natural": True, "has_negative": True,
        "negative_sugerido": _NEG_FLUX_QWEN_ZIMAGE,
        "sampler_recomendado": "euler / simple (~20 pasos, CFG ~3.5; Flux 2 Klein acepta negative)",
        "best_for": "Prosa natural fluida y detallada (casi un párrafo): sujeto → escena → iluminación → cámara. Encoder Qwen (multilingüe). CFG ~3.5, ~20 pasos, euler/simple. Flux 2 Klein SÍ usa negative.",
        "best_for_en": "Flowing, detailed natural-language prose (almost a paragraph): subject → scene → lighting → camera. Qwen text encoder (multilingual). CFG ~3.5, ~20 steps, euler/simple. Flux 2 Klein DOES use negative.",
        "prompt_formula": "Frases completas en prosa, NO tags por comas. Empieza por el sujeto, sigue con el entorno, describe la iluminación exacta y cierra con los detalles de cámara/lente.",
        "prompt_ejemplo": "A weathered fisherman mending nets on a wooden dock at golden hour, warm rim light catching the salt in his beard, calm harbor water behind, shot on 50mm with shallow depth of field.",
    },
    "krea": {
        # Krea (Flux.1/2 Krea): arquitectura Flux → prosa natural, CFG real,
        # SÍ negative. Grupo propio a petición del usuario. Muy fuerte en
        # fotorrealismo con estética "sin plástico" y buena piel/textura.
        "is_natural": True, "has_negative": True,
        "negative_sugerido": _NEG_FLUX_QWEN_ZIMAGE,
        "sampler_recomendado": "euler / simple (~20 pasos, CFG ~3.5; Turbo ~8 pasos CFG 2, sin negative)",
        "best_for": "Krea (BFL+Krea): fotorrealismo con estética natural (piel y texturas creíbles, sin acabado 'plástico' de IA). Prosa fluida: sujeto → escena → iluminación → cámara. CFG ~3.5, ~20 pasos. Variantes Turbo: 8 pasos, CFG 2, sin negative.",
        "best_for_en": "Krea (BFL+Krea): photorealism with a natural aesthetic (believable skin and textures, no 'plastic' AI finish). Flowing prose: subject → scene → lighting → camera. CFG ~3.5, ~20 steps. Turbo variants: 8 steps, CFG 2, no negative.",
        "prompt_formula": "Frases completas en prosa, NO tags por comas. Sujeto → entorno → iluminación exacta → detalles de cámara/lente. Enfatiza textura de piel y materiales realistas.",
        "prompt_ejemplo": "A candid portrait of a woman laughing in a sunlit kitchen, natural window light, fine skin texture and flyaway hairs, shot on 50mm at f/1.8 with soft background blur.",
    },
    "z_image": {
        # LOCAL (ComfyUI): testing del usuario dice LENGUAJE NATURAL PURO, sin
        # el preámbulo de tags de calidad (a diferencia del "híbrido" que
        # SeaArt anuncia para su Z-Image-Base cloud, que sí conserva su spec
        # curada). Con negative. Turbo (destilada, CFG~2) pierde negative vía
        # el override de COMFY_TURBO_TOKENS.
        "is_natural": True, "has_negative": True,
        "negative_sugerido": _NEG_FLUX_QWEN_ZIMAGE,
        "sampler_recomendado": "euler / simple — Base ~25 pasos CFG 4.0 · Turbo ~8 pasos CFG 2.0 (sin negative)",
        "best_for": "Lenguaje natural detallado y específico (NO tags de calidad tipo 'masterpiece'): define ropa, pose, fondo y luz. Términos de fotografía para retratos ('85mm, shallow DoF'). Base: 25 pasos CFG 4. Turbo: 8 pasos CFG 2.",
        "best_for_en": "Detailed, specific natural language (NO quality tags like 'masterpiece'): define outfit, pose, background and lighting. Photography terms for portraits ('85mm, shallow DoF'). Base: 25 steps CFG 4. Turbo: 8 steps CFG 2.",
        "prompt_formula": "Descripción concreta y enfocada en prosa incluyendo iluminación y entorno explícitos. Para retratos usa lenguaje de fotografía (lente, apertura, profundidad de campo).",
        "prompt_ejemplo": "A confident woman in a tailored charcoal suit standing in a sunlit loft, large windows with soft diffused light, 85mm portrait lens, shallow depth of field, natural skin texture.",
    },
    "hidream": {
        # HiDream-I1 (local): DiT abierto de 17B (MoE). Prompts en lenguaje
        # natural, encoders y VAE propios → se carga como unet (UNETLoader) con
        # CLIP/VAE aparte (en blanco, el usuario los elige al pegar el workflow).
        # Familia confirmada por el usuario (ago-2026).
        "is_natural": True, "has_negative": True,
        "negative_sugerido": _NEG_FLUX_QWEN_ZIMAGE,
        "sampler_recomendado": "euler / simple (~25 pasos, CFG ~5.0)",
        "best_for": "HiDream-I1: modelo abierto de 17B. Prosa natural detallada (sujeto → escena → iluminación → cámara), fuerte adherencia al prompt y texto en imagen. CFG ~5, ~25 pasos, euler/simple. Encoders y VAE propios (elígelos en ComfyUI).",
        "best_for_en": "HiDream-I1: open 17B model. Detailed natural-language prose (subject → scene → lighting → camera), strong prompt adherence and in-image text. CFG ~5, ~25 steps, euler/simple. Own encoders and VAE (pick them in ComfyUI).",
        "prompt_formula": "Frases completas en prosa, NO tags por comas. Sujeto → entorno → iluminación → detalles de cámara. Puedes pedir texto en la imagen entre comillas.",
        "prompt_ejemplo": "A serene mountain lake at dawn, mist rising over still water, a lone wooden canoe near the shore, soft pink and gold sky, ultra-detailed, cinematic wide shot.",
    },
    "edit": {
        # Modelos de EDICIÓN por instrucciones LOCALES (FireRed, JoyAI…): se les
        # da una imagen de referencia + una instrucción en lenguaje natural de
        # qué cambiar. NO usan prompt negativo. Se cargan como unet con CLIP/VAE
        # aparte (en blanco, el usuario los elige). Familia confirmada por el
        # usuario (ago-2026): "si son edición, trátalos como edición".
        "is_natural": True, "has_negative": False,
        "sampler_recomendado": "euler / simple (~20-25 pasos)",
        "best_for": "Edición por instrucciones: sube la imagen a editar y describe EN LENGUAJE NATURAL qué cambiar y qué mantener (no tags, no negative). Requiere imagen de referencia.",
        "best_for_en": "Instruction-based editing: upload the image to edit and describe IN NATURAL LANGUAGE what to change and what to keep (no tags, no negative). Requires a reference image.",
        "prompt_formula": "Instrucción directa: qué cambiar + qué preservar, en prosa. Sin tags ni negative. Requiere imagen de referencia.",
        "prompt_ejemplo": "Change the season to winter with fresh snow on the ground and rooftops, keep the house, the people and the composition exactly the same.",
    },
    "ideogram": {
        # Ideogram 4 local (INVENTARIO_MODELOS jul-2026): fuerte en adherencia
        # al prompt, tipografías y logos. Formato tags + frase media.
        "is_natural": False, "has_negative": True,
        "negative_sugerido": _NEG_FLUX_QWEN_ZIMAGE,
        "sampler_recomendado": "euler / simple (~25 pasos, CFG 4.0)",
        "best_for": "Ideogram 4: máxima adherencia al prompt y texto/tipografía dentro de la imagen. Tags + frase media (sujeto → detalles → iluminación → fondo). CFG 4, 25 pasos, euler/simple. Encoder ideogram4_text_encoder, VAE ideogram4_vae.",
        "best_for_en": "Ideogram 4: top prompt adherence and in-image text/typography. Tags + medium sentence (subject → details → lighting → background). CFG 4, 25 steps, euler/simple. Encoder ideogram4_text_encoder, VAE ideogram4_vae.",
        "prompt_formula": "Sujeto claro + detalles + iluminación + fondo, separados por comas con una frase descriptiva. Si quieres TEXTO en la imagen, escríbelo entre comillas — es el punto fuerte de Ideogram.",
        "prompt_ejemplo": "portrait of a young chef holding a sign that says \"OPEN\", warm kitchen background, soft window light, professional photography, 8K, sharp focus, photorealistic.",
    },
    "qwen": {
        # A CFG 4 (base, no la LoRA Lightning) responde a negative — confirmado
        # por el testing del usuario. Formato DOBLE (workflow del usuario):
        # una etapa T2I (genera base) + una img2img (edita esa base).
        "is_natural": True, "has_negative": True,
        "formato_bloques": "qwen_edit",
        "max_chars": 1800,  # margen para los 4 bloques (T2I + img2img)
        "negative_sugerido": _NEG_FLUX_QWEN_ZIMAGE,
        "sampler_recomendado": "euler / simple (~25 pasos, CFG 4.0; con la LoRA Lightning: 8 pasos CFG 1)",
        "best_for": "Lenguaje natural fluido (foto o edición): frase clara de objetivo + referencia a 'image 1/2/3' (hasta 3 imágenes). CFG 4, 25 pasos, euler. Acepta negative. Con LoRA Lightning: 8 pasos CFG 1.",
        "best_for_en": "Fluid natural language (photo or editing): clear goal sentence + reference to 'image 1/2/3' (up to 3 images). CFG 4, 25 steps, euler. Accepts negative. With Lightning LoRA: 8 steps CFG 1.",
        "prompt_formula": "Frase fluida descriptiva; para edición di qué cambiar y qué mantener, con referencia 'image 1/2/3' cuando uses varias. Evita meter tags al inicio.",
        "prompt_ejemplo": "A young woman wearing a floral summer dress walks through an outdoor market bathed in golden sunset light, market stalls with fresh produce behind her, soft warm backlighting, professional photography, sharp focus, photorealistic.",
    },
    "pony": {
        "is_natural": False, "has_negative": True,
        "trigger_words": "score_9, score_8_up, score_7_up, score_6_up, score_5_up",
        "negative_sugerido": ("score_4, score_3, score_2, score_1, worst quality, "
                              "low quality, blurry, deformed, bad anatomy, extra "
                              "limbs, cartoon, monochrome, text, watermark"),
        "sampler_recomendado": "euler / karras (~25 pasos, CFG 5.0)",
        "best_for": "SDXL Pony con tags Danbooru. Trigger obligatorio al inicio: score_9, score_8_up, score_7_up, score_6_up, score_5_up. euler/karras, 25 pasos, CFG 5.0. Para NSFW activa el toggle 🔞.",
        "best_for_en": "SDXL Pony with Danbooru tags. Required trigger at start: score_9, score_8_up, score_7_up, score_6_up, score_5_up. euler/karras, 25 steps, CFG 5.0. For NSFW enable the 🔞 toggle.",
    },
    "illustrious": {
        "is_natural": False, "has_negative": True,
        "sampler_recomendado": "Euler a (~28 pasos, CFG 5-6)",
        "best_for": "Anime/ilustración con tags Danbooru (Illustrious/NoobAI). CFG 5-6.",
        "best_for_en": "Anime/illustration with Danbooru tags (Illustrious/NoobAI). CFG 5-6.",
    },
    "sd15": {
        "is_natural": False, "has_negative": True,
        "negative_sugerido": _NEG_SDXL,
        "sampler_recomendado": "DPM++ 2M Karras (~25 pasos, CFG 7)",
        "best_for": "SD 1.5 (512px nativo), tags de calidad + descripción + negative. DPM++ 2M Karras ~25 pasos, CFG 7.",
        "best_for_en": "SD 1.5 (512px native), quality tags + description + negative. DPM++ 2M Karras ~25 steps, CFG 7.",
    },
    "sdxl": {
        "is_natural": False, "has_negative": True,
        "negative_sugerido": _NEG_SDXL,
        "sampler_recomendado": "euler o dpmpp_2m / karras (~20 pasos, CFG 6.5)",
        "best_for": "SDXL de propósito general / fotorrealismo: tags de calidad ('masterpiece, best quality') + descripción + negative. euler/karras o dpmpp_2m/karras, ~20 pasos, CFG 6.5.",
        "best_for_en": "General-purpose / photoreal SDXL: quality tags ('masterpiece, best quality') + description + negative. euler/karras or dpmpp_2m/karras, ~20 steps, CFG 6.5.",
    },
}


# Override de familia para modelos LOCALES cuyo NOMBRE no la revela (el
# usuario confirma la familia real). Clave = nombre normalizado
# (_norm_nombre_comfy); tiene PRIORIDAD sobre la detección por tokens.
# Ej.: "uberRealisticPornMerge_v23Final" es un merge PonyXL, pero el nombre
# perdió el token "pony" → sin esto caería en "Otros" con params genéricos.
_COMFY_FAMILIA_OVERRIDE = {
    "uberrealisticpornmergev23final": "pony",
    "uberrealisticpornmergeponyxlponyxlhybridv1": "pony",
    # SD 1.5 clásicos cuyo nombre no lleva token de familia (caían en "Otros"
    # con params genéricos euler/CFG 6.5). Inventario CivitAI del usuario.
    "analogmadnessv70": "sd15",
    "lazymixrealamateurv40": "sd15",
    "revanimatedv2pruned": "sd15",
    # Z-Image Base ("ZiB") destilado: sin el override caía en "Otros" y, peor,
    # se cableaba como CheckpointLoaderSimple cuando Z-Image usa UNETLoader +
    # CLIP/VAE aparte (el workflow salía roto). OJO: es DESTILADO (pocos pasos)
    # pero "distilled" no está en COMFY_TURBO_TOKENS, así que sale con los 25
    # pasos/CFG 4 de Z-Image base; baja a ~8 pasos/CFG 1-2 al generar.
    "zibbadmilkdistilledv10": "z_image",
    # ── Inventario ampliado (ago-2026), familias confirmadas por el usuario ──
    # SD 1.5 clásicos sin token de familia en el nombre (caían en "Otros").
    "chilloutmixniprunedfp32fix": "sd15",
    "epicrealismnaturalsin": "sd15",
    "majicmixrealisticv1": "sd15",
    "meinamixv12final": "sd15",
    "realisticvisionv60b1v51hypervae": "sd15",
    "revanimatedv2rebirth": "sd15",
    "cyberrealisticv90": "sd15",
    # Flux sin el token 'flux' en el nombre. unstableEvolution ADEMÁS corrige
    # un falso positivo: el token 'xl' casaba dentro de 't5xxl' → salía sdxl,
    # cuando 'T5xxl'+'Clip' delatan Flux (el override tiene prioridad).
    "unstableevolutionnf4vaeclipt5xxl": "flux",
    "unstabledissolutionfp8e4m3": "flux",
    "snofssexnudesandotherfunstuffv14distilled": "flux",
    # Illustrious (prefijo 'illust' pero sin token 'illustrious'/'noob').
    "illustoccultsemiv2": "illustrious",
    # ── Altas ago-2026 (guiadas una a una por el usuario) ──
    # snofs sobre Flux.2 Klein 9B: snofs ya es Flux; 'klein' delata Flux.2 → flux.
    "snofsklein9bdistilledfp8": "flux",
    # 'Anima' (base/preview) → el usuario confirma que es ANIME (Illustrious).
    # Va por override, NO por token: 'anima' colisiona con anima_pencil-XL (SDXL)
    # y con animatediff/revAnimated.
    "animabasev10": "illustrious",
    "animapreview3base": "illustrious",
    # Modelos de EDICIÓN por instrucciones → familia 'edit' (prosa + imagen ref,
    # sin negative). Por override para no chocar con qwen_image_edit.
    "fireredimageedit11q3km": "edit",
    "fireredimageedit11transformer": "edit",
    "joyaiimageeditint8convrot": "edit",
}


def detectar_familia_comfy(nombre: str) -> str:
    """Familia ComfyUI ('flux'|'sdxl'|'pony'…) por nombre, o '' si no se reconoce."""
    override = _COMFY_FAMILIA_OVERRIDE.get(_norm_nombre_comfy(nombre))
    if override:
        return override
    n = (nombre or "").lower()
    for clave, tokens in _COMFY_FAMILIAS:
        if any(_token_en_nombre(t, n) for t in tokens):
            return clave
    # El nombre no dice nada: probar con la carpeta donde estaba el fichero.
    return _COMFY_FAMILIA_CARPETA.get(_norm_nombre_comfy(nombre), "")


def comfy_image_specs(nombre: str) -> dict | None:
    """Specs sintéticas por familia para un checkpoint ComfyUI local.

    None si no se reconoce la familia (→ comportamiento genérico de la
    plataforma). Las variantes 'fast' (turbo/schnell/lightning/lcm…) fuerzan
    has_negative=False.
    """
    fam = detectar_familia_comfy(nombre)
    if not fam:
        return None
    specs = dict(_COMFY_SPECS_FAMILIA[fam])
    if any(t in (nombre or "").lower() for t in COMFY_TURBO_TOKENS):
        specs["has_negative"] = False
        # Los formatos especiales (z_image híbrido con negative dinámico)
        # no aplican a variantes destiladas: prompt directo natural.
        specs.pop("formato_bloques", None)
    specs.setdefault("max_chars", 1500 if specs["is_natural"] else 500)
    # La UI (combo de ratio) lee specs["ratios"] directamente: los modelos
    # locales aceptan cualquier resolución, así que exponemos los estándar
    # (sin "Libre", que es una opción de UI no del modelo).
    specs.setdefault("ratios", [r for r in RATIOS_IMAGEN if r != "Libre"])
    specs["_comfy_familia"] = fam
    return _aplicar_desc_local(nombre, specs)


# ── Parámetros de WORKFLOW ComfyUI por familia ────────────────────
# Alimentan al exportador "🔧 Comfy" (KSampler + arquitectura de carga):
#   arch = "checkpoint" (CheckpointLoaderSimple: SDXL/SD1.5/Pony/Illustrious)
#          "unet"       (UNETLoader + CLIPLoader + VAELoader: diffusion_models)
# cfg/steps/sampler/scheduler = valores validados por el usuario (jul-2026).
# Para arch=unet, clip/vae son los ficheros típicos del inventario del usuario;
# si no se conocen, quedan "" y ComfyUI los deja en blanco para que el usuario
# los elija en el dropdown (no rompe el paste).
_COMFY_WORKFLOW = {
    "flux":        {"arch": "unet", "cfg": 3.5, "steps": 20, "sampler": "euler", "scheduler": "simple",
                    "clip": "qwen_3_8b_fp8mixed.safetensors", "vae": "flux2-vae.safetensors", "clip_type": "flux2"},
    # Krea: mismo muestreo que Flux, pero CLIP/VAE en BLANCO porque los ficheros
    # Krea son heterogéneos (all-in-one 'CLIPVAEFP8', GGUF, fp8 sueltos) y los
    # de Flux 2 (qwen/flux2-vae) NO son los suyos. ComfyUI deja los dropdowns
    # para que el usuario elija los correctos al pegar el workflow.
    "krea":        {"arch": "unet", "cfg": 3.5, "steps": 20, "sampler": "euler", "scheduler": "simple",
                    "clip": "", "vae": "", "clip_type": "flux2"},
    # Z-Image local (INVENTARIO_MODELOS jul-2026): CLIP qwen_3_4b (type
    # qwen_image), VAE ae. Confirmado por el inventario del usuario.
    "z_image":     {"arch": "unet", "cfg": 4.0, "steps": 25, "sampler": "euler", "scheduler": "simple",
                    "clip": "qwen_3_4b.safetensors", "vae": "ae.safetensors", "clip_type": "qwen_image"},
    "qwen":        {"arch": "unet", "cfg": 4.0, "steps": 25, "sampler": "euler", "scheduler": "simple",
                    "clip": "qwen_2.5_vl_7b_fp8_scaled.safetensors", "vae": "qwen_image_vae.safetensors", "clip_type": "qwen_image"},
    # Ideogram 4 local (INVENTARIO_MODELOS jul-2026): encoder y VAE propios.
    "ideogram":    {"arch": "unet", "cfg": 4.0, "steps": 25, "sampler": "euler", "scheduler": "simple",
                    "clip": "ideogram4_text_encoder.safetensors", "vae": "ideogram4_vae.safetensors", "clip_type": "ideogram4"},
    # HiDream: unet + encoders/VAE propios (en blanco → el usuario los elige).
    "hidream":     {"arch": "unet", "cfg": 5.0, "steps": 25, "sampler": "euler", "scheduler": "simple",
                    "clip": "", "vae": ""},
    # Edición local (FireRed/JoyAI): unet + CLIP/VAE en blanco. clip_type cae en
    # "stable_diffusion" por defecto → el usuario ajusta el loader al pegar.
    "edit":        {"arch": "unet", "cfg": 4.0, "steps": 25, "sampler": "euler", "scheduler": "simple",
                    "clip": "", "vae": ""},
    "sdxl":        {"arch": "checkpoint", "cfg": 6.5, "steps": 20, "sampler": "euler", "scheduler": "karras"},
    "sd15":        {"arch": "checkpoint", "cfg": 7.0, "steps": 25, "sampler": "dpmpp_2m", "scheduler": "karras"},
    "pony":        {"arch": "checkpoint", "cfg": 5.0, "steps": 25, "sampler": "euler", "scheduler": "karras"},
    "illustrious": {"arch": "checkpoint", "cfg": 5.5, "steps": 28, "sampler": "euler_ancestral", "scheduler": "normal"},
}
_COMFY_WORKFLOW_DEFAULT = {"arch": "checkpoint", "cfg": 6.5, "steps": 25,
                           "sampler": "euler", "scheduler": "normal"}


def comfy_workflow_params(nombre: str) -> dict:
    """Parámetros para construir el workflow ComfyUI de `nombre` (por familia).

    Aplica overrides Turbo/destilado (menos pasos, CFG bajo). Siempre devuelve
    un dict completo (arch/cfg/steps/sampler/scheduler + clip/vae si unet)."""
    fam = detectar_familia_comfy(nombre)
    params = dict(_COMFY_WORKFLOW.get(fam, _COMFY_WORKFLOW_DEFAULT))
    if any(t in (nombre or "").lower() for t in COMFY_TURBO_TOKENS):
        params["steps"] = min(params.get("steps", 8), 8)
        params["cfg"] = 2.0
    params["_comfy_familia"] = fam
    return params


def comfy_cheatsheet() -> list[dict]:
    """Filas de chuleta para los modelos de IMAGEN ComfyUI detectados:
    modelo + CLIP + VAE + ajustes de muestreo. Los checkpoints (SDXL/SD1.5/
    Pony/Illustrious) llevan CLIP y VAE integrados (no loaders aparte)."""
    filas = []
    for _grupo, modelos in GRUPOS_IMAGEN_COMFYUI:
        for m in modelos:
            if m.startswith("──"):
                continue
            p = comfy_workflow_params(m)
            if p["arch"] == "checkpoint":
                clip = vae = "(integrado en el checkpoint)"
            else:
                clip = p.get("clip") or "(elígelo en ComfyUI)"
                vae = p.get("vae") or "(elígelo en ComfyUI)"
            filas.append({
                "familia": p.get("_comfy_familia") or "?",
                "modelo": m + ".safetensors",
                "clip": clip,
                "vae": vae,
                "ajustes": f"{p['sampler']} / {p['scheduler']} · CFG {p['cfg']} · {p['steps']} pasos",
            })
    return filas


# ── Familias de VÍDEO ComfyUI por nombre → specs sintéticas ────────
# Espejo de comfy_image_specs para el lado vídeo. El motor de inyección de
# vídeo (_inyectar_specs_video) indexa: max_chars, prompt_formula,
# prompt_ejemplo, best_for, has_audio, audio_desc, has_negative — así que las
# specs sintéticas deben incluir TODAS esas claves.
# (clave, tokens) — específico → genérico.
_COMFY_FAMILIAS_VIDEO = (
    ("ltx",      ("ltx", "ltxv")),
    ("wan",      ("wan",)),
    ("svd",      ("svd", "stable_video", "stable-video", "stablevideo")),
    ("hunyuan",  ("hunyuanvideo", "hunyuan_video", "hunyuan-video")),
    ("cogvideo", ("cogvideo",)),
    ("mochi",    ("mochi",)),
    ("minimax",  ("minimax", "hailuo")),
)

_COMFY_SPECS_FAMILIA_VIDEO = {
    "ltx": {
        "is_natural": True, "has_negative": True, "has_audio": True,
        "audio_desc": "Audio nativo (LTX-2): ambiente, SFX, música y diálogo. Pon el diálogo entre comillas e indica idioma/acento; describe la cualidad de la voz y el entorno acústico",
        "duraciones": ["6s", "8s", "10s"],
        "ratios": ["1:1", "3:4", "4:3", "9:16", "16:9"],
        "modos_gen": ["768p", "1080p", "1440p"],
        "max_chars": 1500, "max_imagenes": 1, "nota": None,
        "best_for": "LTX-2.3 (Lightricks): vídeo+audio nativo. UN párrafo fluido en presente, estilo director: encuadre → escena+luz → acción → personaje → cámara (describe el estado final del movimiento) → audio. 4-8 frases, detallado para llenar la duración. CFG bajo (no lo subas).",
        "best_for_en": "LTX-2.3 (Lightricks): native video+audio. ONE flowing paragraph in present tense, director style: framing → scene+light → action → character → camera (describe motion end-state) → audio. 4-8 sentences, detailed enough to fill the duration. Low CFG (don't raise it).",
        "prompt_formula": "Párrafo único en presente: [Encuadre/plano] + [Escena, iluminación, color, textura] + [Acción central] + [Personaje: rasgos] + [Movimiento de cámara con estado final] + [Audio: ambiente/voz/música]. Físico, no emocional ('he pauses and looks aside', no 'he feels sad').",
        "prompt_ejemplo": "Wide cinematic shot of a young woman in a red coat walking briskly through a rain-soaked Tokyo street at night, neon reflections on wet pavement, handheld camera following from behind then pushing in to a close-up as she stops and turns. Audio: ambient rain, distant traffic, soft synth music.",
        "limitaciones": "CFG demasiado alto y aspect ratio incorrecto son los principales asesinos de calidad. Prompt corto en vídeo largo → el modelo se acelera. No uses tags ni pesos numéricos.",
        "vigente": True,
    },
    "wan": {
        "is_natural": True, "has_negative": True, "has_audio": False, "audio_desc": "",
        "duraciones": ["3s", "4s", "5s"],
        "ratios": ["1:1", "9:16", "16:9"],
        "modos_gen": ["480p", "720p"],
        "max_chars": 1200, "max_imagenes": 1, "nota": None,
        "best_for": "Wan 2.2 (i2v/t2v local): prompts cortos y orientados a la acción con lenguaje de cámara profesional. Estructura: Sujeto + Acción + Cámara + Iluminación + Estilo. CFG 5-7, ~3-8s. Soporta prompt negativo.",
        "best_for_en": "Wan 2.2 (local i2v/t2v): short, action-oriented prompts with professional camera language. Structure: Subject + Action + Camera + Lighting + Style. CFG 5-7, ~3-8s. Supports negative prompt.",
        "prompt_formula": "Sujeto + Acción + Cámara + Iluminación + Estilo/medio. Movimiento sutil y creíble ('soft wind moving grass; camera dolly left 10%', 'gentle zoom out'). Corto y concreto; en i2v deja que la imagen ancle la escena.",
        "prompt_ejemplo": "Cinematic product hero shot, a perfume bottle on wet stone, gentle slow zoom out, soft rim light, shallow depth of field, filmic color grade.",
        "limitaciones": "Evita acciones enormes en i2v (alucina). Más dirigible en t2v. CFG 5-7; sube steps si los frames salen blandos.",
        "vigente": True,
    },
    "svd": {
        "is_natural": True, "has_negative": False, "has_audio": False, "audio_desc": "",
        "duraciones": ["2s", "3s", "4s"],
        "ratios": ["16:9"],
        "modos_gen": ["576p", "1024x576"],
        "max_chars": 400, "max_imagenes": 1, "nota": None,
        "best_for": "Stable Video Diffusion: image-to-video PURO. NO usa prompt de texto — el movimiento se controla con motion_bucket_id (1-1023, def. 127) y fps en ComfyUI. Sube una imagen; el texto se ignora. Clips de 2-4s.",
        "best_for_en": "Stable Video Diffusion: PURE image-to-video. Does NOT use a text prompt — motion is controlled via motion_bucket_id (1-1023, default 127) and fps in ComfyUI. Upload an image; text is ignored. 2-4s clips.",
        "prompt_formula": "SVD ignora el texto. Sube la imagen de origen y ajusta motion_bucket_id (~50 sutil, ~180 dinámico) y fps (~6-10). El prompt de texto NO condiciona el resultado.",
        "prompt_ejemplo": "(SVD no usa texto — controla el movimiento con motion_bucket_id y fps en el nodo de ComfyUI).",
        "limitaciones": "Sin condicionamiento por texto. Solo image-to-video. Clips cortos (2-4s).",
        "vigente": True,
    },
    "hunyuan": {
        "is_natural": True, "has_negative": True, "has_audio": False, "audio_desc": "",
        "duraciones": ["5s"],
        "ratios": ["1:1", "9:16", "16:9"],
        "modos_gen": ["540p", "720p"],
        "max_chars": 1200, "max_imagenes": 1, "nota": None,
        "best_for": "HunyuanVideo (Tencent): lenguaje natural cinematográfico, buena coherencia de movimiento. Describe sujeto, acción, cámara e iluminación en prosa. Soporta negative.",
        "best_for_en": "HunyuanVideo (Tencent): cinematic natural language, good motion coherence. Describe subject, action, camera and lighting in prose. Supports negative.",
        "prompt_formula": "Prosa cinematográfica: sujeto + acción + movimiento de cámara + iluminación + estilo. Presente, fluido.",
        "prompt_ejemplo": "A lone astronaut walking across a red desert at dusk, slow tracking shot, long shadows, dust drifting in the wind, cinematic sci-fi tone.",
        "limitaciones": "Sin audio nativo (modelo base). Clips cortos.",
        "vigente": True,
    },
    "cogvideo": {
        "is_natural": True, "has_negative": True, "has_audio": False, "audio_desc": "",
        "duraciones": ["6s"],
        "ratios": ["16:9"],
        "modos_gen": ["480p", "720p"],
        "max_chars": 1200, "max_imagenes": 1, "nota": None,
        "best_for": "CogVideoX (Zhipu): lenguaje natural descriptivo y detallado. Funciona mejor con prompts largos y ricos en detalle de escena y movimiento. Soporta negative.",
        "best_for_en": "CogVideoX (Zhipu): descriptive, detailed natural language. Works best with long prompts rich in scene and motion detail. Supports negative.",
        "prompt_formula": "Descripción larga y detallada en prosa: escena, sujeto, acción, cámara, iluminación, atmósfera.",
        "prompt_ejemplo": "A golden retriever puppy running through a sunlit meadow of wildflowers, camera tracking alongside at low angle, petals scattering, warm afternoon light, joyful energetic mood.",
        "limitaciones": "Sin audio nativo. Resolución/duración limitadas según variante.",
        "vigente": True,
    },
    "mochi": {
        "is_natural": True, "has_negative": False, "has_audio": False, "audio_desc": "",
        "duraciones": ["5s"],
        "ratios": ["16:9"],
        "modos_gen": ["480p"],
        "max_chars": 1000, "max_imagenes": 1, "nota": None,
        "best_for": "Mochi 1 (Genmo): lenguaje natural, movimiento fluido y físico realista. Prosa cinematográfica concisa; no requiere negative.",
        "best_for_en": "Mochi 1 (Genmo): natural language, fluid motion and realistic physics. Concise cinematic prose; no negative needed.",
        "prompt_formula": "Prosa cinematográfica concisa: sujeto + acción + cámara + iluminación. Enfatiza el movimiento físico realista.",
        "prompt_ejemplo": "A surfer carving down the face of a large wave at sunrise, dynamic side-tracking shot, spray catching golden light, fluid realistic water motion.",
        "limitaciones": "Sin audio nativo. Generación pesada (modelo grande).",
        "vigente": True,
    },
    "minimax": {
        # MiniMax/Hailuo H3 local (minimax_h3_fl2va…). El usuario lo clasifica
        # como vídeo. Lenguaje natural, buena coherencia de movimiento; base
        # sin audio nativo (conservador). Fuerte en image-to-video.
        "is_natural": True, "has_negative": True, "has_audio": False, "audio_desc": "",
        "duraciones": ["5s", "6s"],
        "ratios": ["1:1", "9:16", "16:9"],
        "modos_gen": ["720p"],
        "max_chars": 1200, "max_imagenes": 1, "nota": None,
        "best_for": "MiniMax/Hailuo H3 (local): lenguaje natural cinematográfico con muy buena coherencia de movimiento y físicas. Excelente en image-to-video: sube una imagen y describe la acción y el movimiento de cámara. Soporta negative.",
        "best_for_en": "MiniMax/Hailuo H3 (local): cinematic natural language with very good motion coherence and physics. Excellent at image-to-video: upload an image and describe the action and camera move. Supports negative.",
        "prompt_formula": "Sujeto + acción + movimiento de cámara + iluminación + estilo, en prosa presente. En i2v deja que la imagen ancle la escena y describe solo el movimiento.",
        "prompt_ejemplo": "A woman in a flowing red dress turns slowly toward the camera as wind lifts her hair, slow dolly-in, warm sunset backlight, cinematic shallow depth of field.",
        "limitaciones": "Clips cortos. Sin audio nativo en la base. Evita acciones extremas en i2v (puede alucinar).",
        "vigente": True,
    },
}


# ── Familias de AUDIO ComfyUI local → specs sintéticas ────────────
# Espejo de comfy_image_specs para el modo audio. _inyectar_specs_audio
# indexa: nota, best_for, duracion_max_min, usa_tags_estructurales,
# has_instrumental_toggle, prompt_ejemplo_estilo, limitaciones.
# NOTA: ACE-Step NO está aquí — el fine-tune del usuario genera imagen (ver
# familia 'ace' de imagen). Vacío por ahora; se rellena si aparece un modelo
# de audio local real (MusicGen, Stable Audio…).
_COMFY_FAMILIAS_AUDIO = ()

_COMFY_SPECS_FAMILIA_AUDIO = {}


def comfy_audio_specs(nombre: str) -> dict | None:
    """Specs sintéticas para un modelo de AUDIO ComfyUI local, o None."""
    n = (nombre or "").lower()
    for clave, tokens in _COMFY_FAMILIAS_AUDIO:
        if any(_token_en_nombre(t, n) for t in tokens):
            specs = dict(_COMFY_SPECS_FAMILIA_AUDIO[clave])
            specs["_comfy_familia"] = clave
            return _aplicar_desc_local(nombre, specs)
    return None


def detectar_familia_comfy_video(nombre: str) -> str:
    """Familia de vídeo ComfyUI ('ltx'|'wan'|'svd'…) por nombre, o '' si no."""
    n = (nombre or "").lower()
    for clave, tokens in _COMFY_FAMILIAS_VIDEO:
        if any(_token_en_nombre(t, n) for t in tokens):
            return clave
    return ""


def comfy_video_specs(nombre: str) -> dict | None:
    """Specs sintéticas por familia para un modelo de VÍDEO ComfyUI local.

    None si no se reconoce la familia (→ comportamiento genérico). Incluye todas
    las claves que _inyectar_specs_video indexa.
    """
    fam = detectar_familia_comfy_video(nombre)
    if not fam:
        return None
    specs = dict(_COMFY_SPECS_FAMILIA_VIDEO[fam])
    specs["_comfy_familia"] = fam
    return _aplicar_desc_local(nombre, specs)


def _cargar_preferencias_seguras() -> dict:
    """Lee preferencias.json directamente (sin depender de persistence.py para
    evitar import circular). Devuelve {} si no existe o falla."""
    import json as _json
    try:
        ruta = ARCHIVOS["preferencias"]
        if ruta.exists():
            with open(ruta, "r", encoding="utf-8") as f:
                return _json.load(f) or {}
    except Exception as e:
        logger.debug(f"[silent] {e}")
    return {}


def _cargar_modelos_locales():
    """Carga modelos locales desde JSON con soporte para auto-discovery de ComfyUI."""
    import json as _json

    ruta_json = ARCHIVOS["modelos_comfy"]

    # VACIA A PROPOSITO. Hasta el 08-sep-2026 esta plantilla traia los once
    # checkpoints del equipo del autor (Juggernaut-XL, z_image_turbo,
    # flux-2-klein, wan2.2_i2v...). Quien instalara la app veia once modelos
    # que NO tiene: elegir cualquiera daba "model not found" en ComfyUI, y de
    # paso tapaba el auto-discovery haciendo creer que ya estaba configurado.
    # Un desplegable vacio es mejor: empuja a poner la ruta, que es lo unico
    # que hace falta.
    plantilla_default = {
        "_meta": {
            "version": 2,
            "descripcion": ("Tus modelos locales. Con la ruta de ComfyUI configurada, "
                            "el auto-discovery los detecta y agrupa por familia solo. "
                            "Usa este archivo solo para entradas manuales extra "
                            "(nombres bonitos, modelos fuera de ComfyUI)."),
        },
        "imagen": [],
        "video": [],
    }

    if not ruta_json.exists():
        try:
            with open(ruta_json, "w", encoding="utf-8") as f:
                _json.dump(plantilla_default, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"No se pudo crear mis_modelos_comfy.json: {e}")
        data = plantilla_default
    else:
        try:
            with open(ruta_json, "r", encoding="utf-8") as f:
                data = _json.load(f)
        except Exception as e:
            logger.warning(f"Error leyendo mis_modelos_comfy.json, usando fallback: {e}")
            data = plantilla_default

    grupos_img = [(item.get("grupo", "── Otros ──"), sorted(item.get("modelos", []), key=str.lower)) for item in data.get("imagen", [])]
    grupos_vid = [(item.get("grupo", "── Otros ──"), sorted(item.get("modelos", []), key=str.lower)) for item in data.get("video", [])]

    return grupos_img, grupos_vid


GRUPOS_IMAGEN_COMFYUI, GRUPOS_VIDEO_COMFYUI = _cargar_modelos_locales()

# ── Modelos ComfyUI curados (visibles aunque el fichero no esté en disco) ──
# La herramienta genera PROMPTS: tener "LTX 2.5" seleccionable ya da valor
# (prompts optimizados para LTX) aunque el usuario aún no haya descargado el
# .safetensors. Van en la BASE (antes de _COMFY_BASE_VID) para que el
# auto-discovery no los borre; cuando el fichero real aparezca se añade aparte
# (el dedup solo funde nombres idénticos normalizados). Alta ago-2026.
_COMFY_VIDEO_CURADO = [
    ("── ComfyUI Video · LTX (curado) ──", ["LTX 2.5"]),
]
GRUPOS_VIDEO_COMFYUI = _COMFY_VIDEO_CURADO + GRUPOS_VIDEO_COMFYUI

MODELOS_IMAGEN_COMFYUI_FLAT = []
for g, ms in GRUPOS_IMAGEN_COMFYUI:
    MODELOS_IMAGEN_COMFYUI_FLAT.append(g)
    MODELOS_IMAGEN_COMFYUI_FLAT.extend(ms)

MODELOS_VIDEO_COMFYUI_FLAT = []
for g, ms in GRUPOS_VIDEO_COMFYUI:
    MODELOS_VIDEO_COMFYUI_FLAT.append(g)
    MODELOS_VIDEO_COMFYUI_FLAT.extend(ms)


# ── Caché del auto-discovery ───────────────────────────────────────
# El escaneo tarda <1s, pero el hilo compite por el GIL con la construcción de
# la UI y no aterriza hasta ~17s después del arranque. Sin nada síncrono que
# mostrar, el desplegable de ComfyUI se veía VACÍO todo ese rato y el usuario
# lo leía como "han desaparecido los modelos". Se persiste el último escaneo y
# se puebla aquí, en el import; el hilo pasa a ser solo reconciliación.
#
# Cuántos grupos vienen del manifest curado: los del auto-discovery se
# sustituyen enteros (así desaparecen los modelos que el usuario borre), pero
# los del manifest nunca se tocan.
_COMFY_BASE_IMG = len(GRUPOS_IMAGEN_COMFYUI)
_COMFY_BASE_VID = len(GRUPOS_VIDEO_COMFYUI)
_COMFY_CACHE_APLICADA = {"imagen": [], "video": []}


# Carpetas donde suele vivir ComfyUI. Se prueban en orden y gana la primera
# que tenga models/ dentro. Sin esto, quien instalaba la app abria un
# desplegable vacio y no tenia forma de saber que le faltaba pegar una ruta en
# Ajustes: el auto-discovery devolvia 0 en silencio.
_COMFY_SUFIJOS = (
    "ComfyUI",
    "IA/ComfyUI",
    "AI/ComfyUI",
    "ComfyUI_windows_portable/ComfyUI",
    "ComfyUI/ComfyUI",
    "StabilityMatrix/Packages/ComfyUI",
    "Documents/ComfyUI",
)
_ruta_comfy_detectada = None   # None = aun no se ha buscado; "" = no hay


def _unidades_fijas() -> list:
    """Letras de unidad FIJAS (no CD ni red ni USB).

    Se consulta a Windows en vez de probar de la A a la Z: tocar una unidad
    extraible vacia o una de red caida puede tardar segundos o sacar un dialogo
    del sistema, y esto corre en el arranque.
    """
    letras = []
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        mascara = k32.GetLogicalDrives()
        for i in range(26):
            if not (mascara >> i) & 1:
                continue
            letra = "%s:/" % chr(ord("A") + i)
            if k32.GetDriveTypeW(ctypes.c_wchar_p(letra)) == 3:   # DRIVE_FIXED
                letras.append(letra)
    except Exception as e:
        logger.debug(f"[silent] unidades fijas: {e}")
        letras = ["C:/"]
    return letras


def detectar_comfy_automatico() -> str:
    """Busca ComfyUI en las rutas habituales. Devuelve "" si no lo encuentra.

    Solo mira si existe `models/`: no abre nada ni escanea, para que el coste
    en el arranque sea de milisegundos.
    """
    global _ruta_comfy_detectada
    if _ruta_comfy_detectada is not None:
        return _ruta_comfy_detectada
    _ruta_comfy_detectada = ""
    bases = list(_unidades_fijas())
    try:
        bases.insert(0, str(Path.home()) + "/")
    except Exception as e:
        logger.debug(f"[silent] home para autodeteccion: {e}")
    for base in bases:
        for sufijo in _COMFY_SUFIJOS:
            try:
                cand = Path(base) / sufijo
                if (cand / "models").is_dir():
                    _ruta_comfy_detectada = str(cand)
                    logger.info(f"ComfyUI detectado automaticamente en {cand}")
                    return _ruta_comfy_detectada
            except Exception as e:
                logger.debug(f"[silent] candidata {base}{sufijo}: {e}")
    return _ruta_comfy_detectada


def _ruta_comfy_configurada() -> str:
    """Ruta de ComfyUI: manifest (raíz o _meta) y, si no, preferencias."""
    import json as _json
    ruta_manifest = None
    try:
        if ARCHIVOS["modelos_comfy"].exists():
            with open(ARCHIVOS["modelos_comfy"], encoding="utf-8") as f:
                _datos = _json.load(f) or {}
            # v1 la escribía en la raíz; v2 la anida en "_meta".
            ruta_manifest = (_datos.get("comfyui_path")
                             or (_datos.get("_meta") or {}).get("comfyui_path"))
    except Exception as e:
        logger.debug(f"[silent] comfyui_path del manifest: {e}")
    ruta = ruta_manifest or get_comfyui_path(_cargar_preferencias_seguras())
    if ruta and Path(ruta).exists():
        return ruta
    # Nadie la ha configurado: mirar donde suele estar. Lo que se detecta NO se
    # guarda desde aqui — el que decide persistirla es quien arranca el
    # auto-discovery, para que Ajustes muestre la ruta que se esta usando en
    # vez de un campo vacio con modelos apareciendo por arte de magia.
    return detectar_comfy_automatico()


def _rehacer_flat(grupos: list, flat: list) -> None:
    """Reconstruye la lista plana desde los grupos, IN PLACE (las listas se
    comparten con MODELOS_POR_PLATAFORMA_* y MOTORES_VIDEO)."""
    flat[:] = [x for g, ms in grupos for x in (g, *ms)]


def _poblar_comfy(imagen: list, video: list) -> None:
    """Sustituye los grupos del auto-discovery por los indicados."""
    del GRUPOS_IMAGEN_COMFYUI[_COMFY_BASE_IMG:]
    del GRUPOS_VIDEO_COMFYUI[_COMFY_BASE_VID:]
    if imagen:
        GRUPOS_IMAGEN_COMFYUI.extend(_agrupar_por_familia(
            imagen, detectar_familia_comfy, _COMFY_FAMILIA_LABELS, "ComfyUI"))
    if video:
        GRUPOS_VIDEO_COMFYUI.extend(_agrupar_por_familia(
            video, detectar_familia_comfy_video, _COMFY_FAMILIA_LABELS_VIDEO,
            "ComfyUI Video"))
    _rehacer_flat(GRUPOS_IMAGEN_COMFYUI, MODELOS_IMAGEN_COMFYUI_FLAT)
    _rehacer_flat(GRUPOS_VIDEO_COMFYUI, MODELOS_VIDEO_COMFYUI_FLAT)


def _guardar_cache_comfy(ruta: str, imagen: list, video: list) -> None:
    import json as _json
    try:
        with open(ARCHIVOS["comfy_cache"], "w", encoding="utf-8") as f:
            _json.dump({"path": str(ruta), "imagen": imagen, "video": video},
                       f, indent=1, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"No se pudo guardar la caché de ComfyUI: {e}")


def aplicar_cache_comfy() -> int:
    """Puebla los desplegables con el último escaneo conocido, sin tocar disco
    más que un JSON pequeño. Devuelve cuántos modelos aportó."""
    import json as _json
    ruta = _ruta_comfy_configurada()
    if not ruta:
        return 0
    try:
        if not ARCHIVOS["comfy_cache"].exists():
            return 0
        with open(ARCHIVOS["comfy_cache"], encoding="utf-8") as f:
            cache = _json.load(f) or {}
    except Exception as e:
        logger.debug(f"[silent] caché comfy: {e}")
        return 0
    # Si la ruta cambió, la caché es de otra instalación: se ignora.
    if cache.get("path") != str(ruta):
        return 0
    imagen = cache.get("imagen") or []
    video = cache.get("video") or []
    if not (imagen or video):
        return 0
    _poblar_comfy(imagen, video)
    _COMFY_CACHE_APLICADA["imagen"] = imagen
    _COMFY_CACHE_APLICADA["video"] = video
    return len(imagen) + len(video)


# Síncrono y barato (un JSON pequeño): los desplegables ya salen poblados en el
# primer frame, sin esperar al hilo.
#
# Sin log aquí: main.py importa config ANTES de llamar a basicConfig, así que
# cualquier mensaje emitido durante este import se pierde. Lo reporta app.py
# al lanzar el hilo, ya con el logging montado.
_COMFY_DESDE_CACHE = aplicar_cache_comfy()


# ── Auto-discovery ComfyUI diferido ────────────────────────────────
# Antes el escaneo (rglob recursivo sobre models/, potencialmente miles de
# ficheros) corría en el import de config.py y frenaba el arranque. Ahora la
# app lo lanza en un hilo tras crear la ventana (app.py). Muta las listas IN
# PLACE porque MODELOS_POR_PLATAFORMA_* y MOTORES_VIDEO comparten las mismas
# instancias — así los desplegables ven los modelos nuevos al repoblarse.
_autodiscovery_hecho = False


def _persistir_ruta_comfy(ruta: str) -> bool:
    """Escribe la ruta detectada en _meta del manifest. No pisa una existente."""
    import json as _json
    destino = ARCHIVOS["modelos_comfy"]
    try:
        datos = {}
        if destino.exists():
            with open(destino, encoding="utf-8") as f:
                datos = _json.load(f) or {}
        meta = datos.setdefault("_meta", {})
        if meta.get("comfyui_path") or datos.get("comfyui_path"):
            return False
        meta["comfyui_path"] = ruta
        datos.setdefault("imagen", [])
        datos.setdefault("video", [])
        with open(destino, "w", encoding="utf-8") as f:
            _json.dump(datos, f, indent=4, ensure_ascii=False)
        logger.info(f"Ruta de ComfyUI detectada y guardada: {ruta}")
        return True
    except Exception as e:
        logger.warning(f"No se pudo guardar la ruta detectada de ComfyUI: {e}")
        return False


def aplicar_autodiscovery_comfy() -> int:
    """Escanea la carpeta ComfyUI configurada y añade los modelos hallados a
    GRUPOS_*_COMFYUI / MODELOS_*_COMFYUI_FLAT (mutación in place).

    Idempotente: la segunda llamada devuelve 0 sin re-escanear.
    Returns: número de modelos añadidos (0 si no hay ruta o ya se aplicó).
    """
    global _autodiscovery_hecho
    if _autodiscovery_hecho:
        return 0
    _autodiscovery_hecho = True

    comfy_ruta = _ruta_comfy_configurada()
    if not comfy_ruta:
        return 0
    # Si la ruta salio de la autodeteccion, dejarla escrita en el manifest: sin
    # esto el usuario veria modelos aparecer con el campo de Ajustes vacio y no
    # sabria de donde salen ni como cambiarlos.
    if comfy_ruta == _ruta_comfy_detectada:
        _persistir_ruta_comfy(comfy_ruta)

    hallados = _escanear_comfy_root(Path(comfy_ruta))
    # Dedupe contra el manifest curado (mis_modelos_comfy.json): si el usuario
    # ya listó ese fichero con nombre bonito, el manifest manda. Solo los
    # grupos base — los del auto-discovery se sustituyen enteros.
    _en_manifest_img = {_norm_nombre_comfy(m)
                        for _, ms in GRUPOS_IMAGEN_COMFYUI[:_COMFY_BASE_IMG] for m in ms}
    _en_manifest_vid = {_norm_nombre_comfy(m)
                        for _, ms in GRUPOS_VIDEO_COMFYUI[:_COMFY_BASE_VID] for m in ms}
    hallados["imagen"] = [m for m in hallados["imagen"]
                          if _norm_nombre_comfy(m) not in _en_manifest_img]
    hallados["video"] = [m for m in hallados["video"]
                         if _norm_nombre_comfy(m) not in _en_manifest_vid]
    total = 0
    # Si la caché ya mostraba justo esto, los desplegables están al día y no
    # hay que repoblar nada (evita el parpadeo de reconstruir los combos).
    # Un escaneo EN BLANCO no es una noticia: es un sintoma. Si la cache tenia
    # modelos y ahora no se encuentra ninguno, lo probable es que la carpeta no
    # se pueda leer (junction bloqueado, disco externo dormido, ComfyUI movido),
    # no que el usuario haya borrado sus 124 checkpoints. Antes se creia el cero:
    # vaciaba los desplegables Y guardaba la cache vacia, asi que el arranque
    # siguiente ya nacia sin modelos y sin forma de recuperarlos.
    habia_en_cache = bool(_COMFY_CACHE_APLICADA["imagen"]
                          or _COMFY_CACHE_APLICADA["video"])
    if not (hallados["imagen"] or hallados["video"]) and habia_en_cache:
        logger.warning(
            f"ComfyUI: el escaneo de {comfy_ruta} no encontro nada, pero la "
            f"cache tenia modelos: se conserva la cache. Revisa que la carpeta "
            f"sea accesible.")
    elif (hallados["imagen"] != _COMFY_CACHE_APLICADA["imagen"]
            or hallados["video"] != _COMFY_CACHE_APLICADA["video"]):
        _poblar_comfy(hallados["imagen"], hallados["video"])
        _guardar_cache_comfy(comfy_ruta, hallados["imagen"], hallados["video"])
        total += len(hallados["imagen"]) + len(hallados["video"])
    if hallados["audio"]:
        # Audio local (ACE-Step, etc.): entra directo en las listas del modo
        # audio — el filtro de vigencia ya corrió en el import y solo aplica
        # al catálogo curado. Las specs salen de comfy_audio_specs (fallback
        # en get_audio_model_specs); sin familia reconocida → inyección
        # genérica, sin crash.
        ms = sorted(hallados["audio"], key=str.lower)
        GRUPOS_AUDIO_VIGENTES.append(("── ComfyUI Audio ──", ms))
        MODELOS_AUDIO_FLAT.append("── ComfyUI Audio ──")
        MODELOS_AUDIO_FLAT.extend(ms)
        total += len(ms)
    if total:
        logger.info(f"Auto-discovery ComfyUI: {total} modelos añadidos desde {comfy_ruta}")
    return total

# ══════════════════════════════════════════════════════════════════
# MODELOS DE AUDIO
# ══════════════════════════════════════════════════════════════════
GRUPOS_AUDIO = _grupos("audio")

def _lista_plana(grupos):
    r = []
    for g, ms in grupos:
        r.append(g)
        r.extend(ms)
    return r

MODELOS_VIDEO_FLAT_TODOS = _lista_plana(GRUPOS_VIDEO)
MODELOS_AUDIO_FLAT_TODOS = _lista_plana(GRUPOS_AUDIO)

def es_modelo_video_vigente(nombre):
    spec = _get_dataset("MODEL_SPECS_VIDEO").get(nombre)
    return bool(spec and spec.get("vigente"))

def es_modelo_audio_vigente(nombre):
    spec = _get_dataset("MODEL_SPECS_AUDIO").get(nombre)
    return bool(spec and spec.get("vigente"))

def _filtrar_grupos_vigentes_video(grupos):
    out = []
    for cabecera, modelos in grupos:
        visibles = [m for m in modelos if es_modelo_video_vigente(m)]
        if visibles:
            out.append((cabecera, visibles))
    return out

def _filtrar_grupos_vigentes_audio(grupos):
    out = []
    for cabecera, modelos in grupos:
        visibles = [m for m in modelos if es_modelo_audio_vigente(m)]
        if visibles:
            out.append((cabecera, visibles))
    return out

GRUPOS_VIDEO_VIGENTES = _filtrar_grupos_vigentes_video(GRUPOS_VIDEO)
GRUPOS_AUDIO_VIGENTES = _filtrar_grupos_vigentes_audio(GRUPOS_AUDIO)
MODELOS_VIDEO_FLAT    = _lista_plana(GRUPOS_VIDEO_VIGENTES)
MODELOS_AUDIO_FLAT    = _lista_plana(GRUPOS_AUDIO_VIGENTES)

# Orden alfabético INSENSIBLE A MAYÚSCULAS en TODOS los grupos de imagen, para
# que los nombres en minúscula (p. ej. lyh_anime_Flux) no caigan al final del
# desplegable (el sorted() por defecto es case-sensitive y ordena 'l' tras 'Z').
GRUPOS_IMAGEN = [(cab, sorted(ms, key=str.lower)) for cab, ms in GRUPOS_IMAGEN]
# Familias también en orden alfabético (case-insensitive), ignorando los ──.
GRUPOS_IMAGEN = sorted(GRUPOS_IMAGEN, key=lambda g: g[0].strip("─ ").lower())

# ── Filtro de modelos VIGENTES (imagen) ───────────────────────────
# Solo se MUESTRAN en los desplegables los modelos cuyo spec tiene
# "vigente": true. El resto (specs antiguos pendientes de actualizar) quedan
# ocultos hasta que se revisen — basta con poner "vigente": true en su spec
# para que reaparezcan. GRUPOS_IMAGEN sigue siendo la lista MAESTRA
# (validación/referencia) y MODELOS_IMAGEN_FLAT_TODOS conserva el set completo.
def es_modelo_imagen_vigente(nombre):
    """True si el modelo de imagen está marcado como vigente en su spec."""
    spec = _get_dataset("MODEL_SPECS_IMAGEN").get(nombre)
    return bool(spec and spec.get("vigente"))

def best_for_display(spec):
    """Descripción `best_for` en el idioma de la UI: `best_for_en` si idioma=='en'
    y existe; si no, cae al `best_for` español. No rompe nada (fallback seguro)."""
    if not spec:
        return ""
    try:
        from modules.i18n import get_idioma
        if get_idioma() == "en" and spec.get("best_for_en"):
            return spec["best_for_en"]
    except Exception:
        pass
    return spec.get("best_for", "")

def _filtrar_grupos_vigentes(grupos):
    """Quita de cada grupo los modelos no vigentes y descarta grupos vacíos."""
    out = []
    for cabecera, modelos in grupos:
        visibles = [m for m in modelos if es_modelo_imagen_vigente(m)]
        if visibles:
            out.append((cabecera, visibles))
    return out

MODELOS_IMAGEN_FLAT_TODOS = _lista_plana(GRUPOS_IMAGEN)        # master, sin filtrar
GRUPOS_IMAGEN_VIGENTES = _filtrar_grupos_vigentes(GRUPOS_IMAGEN)
MODELOS_IMAGEN_FLAT = _lista_plana(GRUPOS_IMAGEN_VIGENTES)     # lo que se MUESTRA

# ══════════════════════════════════════════════════════════════════
# MODELOS POR PLATAFORMA — IMAGEN
# Cada plataforma muestra SÓLO los modelos disponibles en ella
# ══════════════════════════════════════════════════════════════════

# Modelos exclusivos de Magnific (anteriormente Freepik AI, rebrand abril 2026)
GRUPOS_MAGNIFIC_IMAGEN = _grupos("magnific_imagen")
MODELOS_MAGNIFIC_IMAGEN_FLAT = _lista_plana(GRUPOS_MAGNIFIC_IMAGEN)

# Modelos OpenAI/ChatGPT oficial (DALL-E retirado mayo 2026)
# Solo familia GPT Image actualmente activa en la API oficial.
GRUPOS_DALLE_IMAGEN = _grupos("dalle_imagen")
MODELOS_DALLE_IMAGEN_FLAT = _lista_plana(GRUPOS_DALLE_IMAGEN)

# Grok (xAI) — plataforma propia (alta ago-2026 a petición del usuario).
GRUPOS_GROK_IMAGEN = _grupos("grok_imagen")
MODELOS_GROK_IMAGEN_FLAT = _lista_plana(GRUPOS_GROK_IMAGEN)

# Higgsfield — plataforma propia (alta sep-2026). SOLO MAPEADA: el usuario aún
# NO genera ahí (lo probará más adelante), así que las specs son mínimas y van
# marcadas "por confirmar en panel". Modelos PROPIOS de Higgsfield: familia Soul
# (alta estética / art-directed, con presets y Moodboards) + Popcorn. Los de
# terceros que revende (Nano Banana, GPT Image, Seedream, FLUX, Recraft) NO se
# duplican aquí: ya están en sus plataformas/grupos. OJO: "Higgsfield Image"
# sigue en el grupo Higgsfield de SeaArt (SeaArt lo revende), igual que Grok.
GRUPOS_HIGGSFIELD_IMAGEN = _grupos("higgsfield_imagen")
MODELOS_HIGGSFIELD_IMAGEN_FLAT = _lista_plana(GRUPOS_HIGGSFIELD_IMAGEN)

# Mapeo plataforma -> lista de modelos (para imagen)
MODELOS_POR_PLATAFORMA_IMAGEN = {
    "SeaArt / Tensor.Art":          MODELOS_IMAGEN_FLAT,
    "ComfyUI / Fooocus":            MODELOS_IMAGEN_COMFYUI_FLAT,
    "ChatGPT / GPT Image":           MODELOS_DALLE_IMAGEN_FLAT,
    "Grok (xAI)":                    MODELOS_GROK_IMAGEN_FLAT,
    "Higgsfield":                    MODELOS_HIGGSFIELD_IMAGEN_FLAT,
    "Magnific":                      MODELOS_MAGNIFIC_IMAGEN_FLAT,
}

# Mapeo plataforma -> lista de modelos (para vídeo)
MODELOS_POR_PLATAFORMA_VIDEO = {
    "SeaArt Video":                MODELOS_VIDEO_FLAT,
    "ComfyUI / Fooocus":          MODELOS_VIDEO_COMFYUI_FLAT,
    "Kling AI":                    [m for m in MODELOS_VIDEO_FLAT if "Kling" in m or m.startswith("──")],
    "Veo / Gemini":                ["Veo 3.1", "Gemini Omni Flash"],
    "Pollo AI":                    ["Runway Gen-4 Turbo", "Runway Gen-3 Turbo",
                                    "Luma Ray 2", "Luma Ray 2 Flash", "Pika 2.2",
                                    "Hunyuan Video", "SkyReels V2"],
    "Higgsfield":                  ["Higgsfield DOP"],
}

# ── Ratios ────────────────────────────────────────────────────────
RATIOS_IMAGEN = ["1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9", "21:9", "Libre"]
RATIOS_VIDEO  = ["1:1", "3:4", "4:3", "9:16", "16:9", "21:9"]

# ══════════════════════════════════════════════════════════════════
# ESTILOS DE IMAGEN (NUEVA ORGANIZACIÓN POR GRUPOS)
# ══════════════════════════════════════════════════════════════════
ESTILOS_GRUPOS = _load_json_data("estilos_grupos.json")

# Se genera la lista plana y se ordena TODO globalmente de la A a la Z
def clave_alfabetica(s: str) -> str:
    """Clave de orden alfabético insensible a mayúsculas Y acentos, para que
    listas mixtas ES/EN ordenen bien ('Épico' junto a la E, no al final)."""
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


ESTILOS_IMAGEN = []
for grupo in ESTILOS_GRUPOS.values():
    ESTILOS_IMAGEN.extend(grupo)

ESTILOS_IMAGEN = sorted(ESTILOS_IMAGEN, key=clave_alfabetica)

ESTILOS_VIDEO = sorted([
    # Géneros narrativos
    "Acción / Corte Rápido", "Anime", "Anuncio Producto", "Aventura",
    "Ciencia Ficción", "Comedia", "Documental", "Drama Cinematográfico",
    "Fantasy Épica", "Found Footage", "Misterio / Suspense",
    "Música Videojuegos", "Romance", "Sátira", "Slasher / Horror",
    "Terror / Atmósfera", "Thriller", "True Crime",
    # Estilos visuales
    "ASMR Visual", "Black & White", "Cinematográfico 4K", "Cinematic Noir",
    "Cinematic VFX", "Color Pop", "Cyberpunk Visual", "Cinemagraph",
    "Cottagecore", "Dreamcore", "Glitch / VHS", "Lo-Fi Aesthetic",
    "Neon / Vaporwave", "Polished / Hi-Res", "Retro 70s", "Retro 80s",
    "Retro 90s", "Synthwave", "Vintage Film",
    # Cámara y movimiento
    "Cámara Lenta / Slow Motion", "Cámara Mano (Handheld)", "Crane / Grúa",
    "Dolly Zoom", "Drone / Aéreo", "First Person POV", "Gimbal Smooth",
    "Helicóptero", "Hyperlapse", "Match Cut", "Orbital Shot",
    "Parallax", "Plano Secuencia / Oner", "Pull Back / Reveal",
    "Steadicam", "Time-Lapse", "Tracking Shot", "Whip Pan", "Zoom Burst",
    # Formatos y duración
    "Anuncio 6s (bumper)", "Anuncio 15s (TikTok/IG)", "Anuncio 30s (TV)",
    "Cortometraje", "Loop / Bucle", "Music Video Sync",
    "Reels / Stories", "Trailer Cinematográfico", "Tutorial / Explainer",
    "Videoclip Musical", "Vlog / Handheld",
    # Edición y efectos
    "Jump Cut", "Motion Graphics", "Split Screen", "Stop Motion",
    "Tilt-Shift Miniature",
    # Temáticos
    "Anuncio Lifestyle", "Cooking / Foodie", "Deportes / Sports",
    "Fashion Editorial", "Gaming Highlights", "Interior / Real Estate",
    "Naturaleza / Wildlife", "Producto Macro", "Tech Review",
    "Tutorial Cocina", "Unboxing",
    # ── Producción audiovisual ──
    "Corporate Video", "Brand Storytelling", "Behind-the-Scenes",
    "Event Coverage", "Feature Film", "Testimonial / Case Study",
    # ── Social Media ──
    "TikTok / Short-form", "YouTube Shorts", "Instagram Reels",
    "Shoppable Video", "Influencer Content", "UGC Content",
    # ── Cinematografía ──
    "Silent Film", "Experimental Film", "Neo-noir",
    "Surrealist Film", "Exploratory / Documentary",
    # ── Animación ──
    "2D Animation", "3D Animation", "Whiteboard Animation",
    "Infographic Video", "Typography Animation", "Kinetic Typography",
    # ── Corporativo ──
    "Explainer Video", "Training Video", "Onboarding Video",
    "Product Demo", "FAQ Video", "How-to / Tutorial",
    # ── Musical ──
    "Lyric Video", "Live Performance", "Concert Documentary",
    # ── Interactivo/VR ──
    "360° Video", "VR Experience", "Interactive Video",
    "Gamified Content", "Immersive / AR",
], key=clave_alfabetica)

# Presets de LOOK visual para el combo "Estilo" de la barra de vídeo.
# Complementan los géneros narrativos de ESTILOS_VIDEO (checkboxes): aquí se
# define la estética de render, no el género. "Auto" = no fuerza nada.
# La selección se inyecta como hint en el system prompt vía
# prompts_inyeccion._inyectar_estilo_video.
ESTILOS_VISUAL_VIDEO = [
    "Auto", "Cinematográfico", "Anime", "Realista", "3D / Pixar",
    "Cómic / Cartoon", "Cyberpunk / Neón", "Blanco y Negro",
    "Vintage / Retro", "Acuarela / Artístico",
]

ESTILOS_AUDIO = sorted([
    # Géneros raíz
    "Ambient", "Blues", "Cinematográfico", "Clásica", "Country",
    "Electrónica", "Flamenco", "Folk", "Funk", "Hip-hop",
    "Indie", "Jazz", "Lo-fi", "Metal", "Música Videojuegos",
    "Pop", "R&B", "Reggaeton", "Rock", "Synthwave",
    # Electrónica (subgéneros)
    "House", "Techno", "Trance", "Drum & Bass", "Dubstep", "Trap",
    "EDM", "Future Bass", "Hardstyle", "Phonk", "UK Garage",
    # Pop (subgéneros)
    "Synth-pop", "Hyperpop", "K-pop", "J-pop", "Dream Pop", "City Pop",
    # Rock (subgéneros)
    "Punk", "Grunge", "Indie Rock", "Hard Rock", "Post-rock", "Emo",
    # Urbano
    "Boom Bap", "Drill", "Grime", "Afrobeats",
    # Latino / World
    "Salsa", "Bachata", "Cumbia", "Tango", "Bossa Nova", "Samba",
    "Reggae", "Ska",
    # Soul / Funk / Disco
    "Soul", "Disco", "Gospel", "Motown",
    # Folk / Acústico
    "Indie Folk", "Bluegrass", "Celtic", "Singer-songwriter",
    # Jazz (subgéneros)
    "Swing", "Smooth Jazz", "Bebop",
    # Cinemático / Orquestal
    "Orquestal", "Épico / Trailer", "Banda Sonora",
    # Mood / Uso
    "Chillout", "Meditación / Relax", "Workout / Gym", "ASMR",
    "Estudio / Focus",
    # Otros
    "Ópera / Coral", "Vaporwave", "Chiptune 8-bit",
], key=clave_alfabetica)

EMOCIONES_AUDIO = sorted([
    "Alegre", "Melancólico", "Épico", "Romántico", "Enérgico", "Relajado",
    "Oscuro", "Nostálgico", "Tenso", "Esperanzador", "Triste", "Agresivo",
])
VOCES_AUDIO = sorted([
    "Masculina grave", "Masculina media", "Masculina aguda",
    "Femenina grave", "Femenina media", "Femenina aguda",
    "Coro", "Susurro", "Sin voz (instrumental)",
])
IDIOMAS_AUDIO = sorted([
    "Español (castellano)", "Español (latino)", "Inglés",
    "Portugués", "Italiano", "Francés", "Instrumental",
])

# ── Presets de Negativos ──────────────────────────────────────────
NEGATIVE_PRESETS = {
    "Anatomía":      "bad anatomy, deformed hands, missing fingers, extra limbs, extra fingers, fused fingers, too many fingers, malformed limbs, disfigured, cloned face",
    "Anime/2D":      "photorealistic, photo, realistic skin, pores, wrinkles, 3d render, hyperrealistic",
    "Baja Calidad":  "low quality, worst quality, jpeg artifacts, compression artifacts, pixelated, noisy, grainy, overexposed, underexposed",
    "Censura":       "censored, mosaic, blur, bar censor, black bar, pixelated censor, safe, covered",
    "Deformación":   "deformed, distorted, mutation, mutated, disfigured, bad proportions, cropped, out of frame, duplicate",
    "Fondos":        "ugly background, cluttered, messy, distracting background, busy background, multiple subjects",
    "Fotografía":    "film grain, chromatic aberration, motion blur, out of focus, heavy noise, lens flare, overexposed highlights",
    "Pose":          "awkward pose, impossible pose, bad posture, twisted body, unnatural position, floating limbs, stiff pose",
    "Realismo":      "cartoon, anime, illustration, painting, drawing, 3d render, CGI, unrealistic, plastic skin, doll-like",
    "Texto/Marcas":  "text, watermark, signature, logo, username, caption, title, subtitle, letters, numbers, copyright",
}

PRESET_COLORES = {
    "Anatomía":     ("#3a2020", "#5a3030"),
    "Anime/2D":     ("#2a203a", "#3a305a"),
    "Baja Calidad": ("#3a3020", "#5a4a30"),
    "Censura":      ("#3a2030", "#5a3050"),
    "Deformación":  ("#3a2a20", "#5a3a30"),
    "Fondos":       ("#203030", "#304a4a"),
    "Fotografía":   ("#1a2a3a", "#2a3a5a"),
    "Pose":         ("#2a1a3a", "#3a2a5a"),
    "Realismo":     ("#203a2a", "#305a3a"),
    "Texto/Marcas": ("#2a2a3a", "#3a3a5a"),
}

NEGATIVE_PAQUETES = {
    "📸 Foto Pro":    ["Anatomía", "Baja Calidad", "Texto/Marcas", "Deformación"],
    "🎨 Ilustración": ["Realismo", "Baja Calidad", "Texto/Marcas"],
    "🖼 Anime Pro":   ["Realismo", "Baja Calidad", "Anatomía"],
    "🧹 Limpieza":    ["Baja Calidad", "Texto/Marcas", "Fondos"],
}

TAG_PICKER_CATEGORIES = {
    # Cada entrada: (nombre_español, término_inglés_para_la_IA, descripción_tooltip)
    "💡 Iluminación": [
        ("Hora dorada",       "golden hour",                 "Luz cálida al amanecer/atardecer; tonos dorados y naranjas suaves"),
        ("Luz dramática",     "dramatic lighting",           "Contraste fuerte entre luces y sombras para impacto visual"),
        ("Luz suave",         "soft light",                  "Iluminación difusa sin sombras duras; aspecto suave y limpio"),
        ("Luz de borde",      "rim lighting",                "Halo de luz en el contorno del sujeto, separándolo del fondo"),
        ("Contraluz",         "backlit",                     "Fuente de luz detrás del sujeto; crea silueta o efecto translúcido"),
        ("Brillo neón",       "neon glow",                   "Resplandor de luces de neón; colores eléctricos en la escena"),
        ("Luz de estudio",    "studio lighting",             "Iluminación controlada de estudio; aspecto profesional y limpio"),
        ("Luz volumétrica",   "volumetric light",            "Rayos de luz visibles en el aire (polvo, niebla, humo)"),
        ("Luz cinemat.",      "cinematic lighting",          "Iluminación de película; contraste cuidado y atmósfera narrativa"),
        ("Claroscuro",        "chiaroscuro",                 "Técnica de pintura clásica: sombras muy oscuras vs luces muy brillantes"),
        ("Luz de luna",       "moonlight",                   "Luz azulada y fría de la luna llena; ambiente nocturno sereno"),
        ("Luz de vela",       "candlelight",                 "Luz cálida y parpadeante de velas; ambiente íntimo y antiguo"),
        ("Rayos de sol",      "sunbeams",                    "Rayos de sol visibles entre nubes, árboles o ventanas"),
        ("Sombras duras",     "hard shadows",                "Sombras con bordes muy definidos; efecto solar o foco directo"),
        ("Rayos divinos",     "god rays",                    "Haces de luz descendentes desde el cielo o una abertura; efecto épico"),
    ],
    "📷 Cámara": [
        ("Primer plano",      "close-up",                    "Encuadre muy cercano al sujeto, mostrando detalles del rostro u objeto"),
        ("Macro",             "macro shot",                  "Fotografía extrema de objetos pequeños a escala 1:1 o mayor"),
        ("Gran angular",      "wide angle",                  "Lente que captura un campo visual amplio; distorsión leve en bordes"),
        ("Teleobjetivo",      "telephoto lens",              "Lente larga que comprime la perspectiva y acerca sujetos lejanos"),
        ("Bokeh",             "bokeh",                       "Fondo desenfocado con círculos de luz suaves; sujeto bien definido"),
        ("Poco enfoque",      "shallow depth of field",      "Solo una franja estrecha del plano está enfocada; fondo muy borroso"),
        ("Ojo de pez",        "fisheye lens",                "Lente gran angular extremo con fuerte distorsión curvada"),
        ("Tilt-shift",        "tilt-shift",                  "Técnica que hace que escenas reales parezcan maquetas en miniatura"),
        ("Vista aérea",       "aerial view",                 "Plano tomado desde el aire, mirando hacia abajo"),
        ("Ángulo holandés",   "dutch angle",                 "Cámara inclinada en diagonal; transmite desequilibrio o tensión"),
        ("Sobre el hombro",   "over the shoulder",           "Encuadre desde detrás del hombro de un personaje hacia otro"),
        ("Punto de vista",    "POV shot",                    "Cámara desde los ojos del personaje; el espectador ve lo que él ve"),
        ("Ángulo bajo",       "low angle",                   "Cámara mirando hacia arriba; el sujeto parece imponente o poderoso"),
        ("Ángulo alto",       "high angle",                  "Cámara mirando hacia abajo; el sujeto parece pequeño o vulnerable"),
        ("Vista de pájaro",   "bird's eye view",             "Plano cenital, directamente desde arriba hacia abajo"),
    ],
    "🎭 Mood": [
        ("Melancólico",       "melancholic",                 "Tristeza suave y reflexiva; tonos fríos y silencio"),
        ("Eufórico",          "euphoric",                    "Alegría intensa y desbordante; colores vibrantes y energía máxima"),
        ("Misterioso",        "mysterious",                  "Atmósfera de enigma; sombras, niebla y elementos sin revelar"),
        ("Tranquilo",         "peaceful",                    "Calma y serenidad; luz suave, naturaleza, quietud"),
        ("Tenso",             "tense",                       "Sensación de peligro inminente; sombras, ángulos cerrados, silencio"),
        ("Onírico",           "dreamy",                      "Aspecto de sueño; bordes difusos, colores pastel, irrealidad"),
        ("Nostálgico",        "nostalgic",                   "Recuerdo de épocas pasadas; tonos cálidos envejecidos, grano"),
        ("Inquietante",       "eerie",                       "Extrañeza perturbadora; algo no cuadra, sensación de amenaza latente"),
        ("Romántico",         "romantic",                    "Atmósfera de amor; luz cálida, suavidad, intimidad"),
        ("Épico",             "epic",                        "Grandiosidad y escala monumental; cielos dramáticos, héroe imponente"),
        ("Sereno",            "serene",                      "Paz profunda sin tensión; naturaleza, amanecer, quietud total"),
        ("Perturbador",       "haunting",                    "Imagen que persiste en la mente; belleza mezclada con incomodidad"),
        ("Alegre",            "joyful",                      "Felicidad luminosa; colores brillantes, sonrisas, movimiento"),
        ("Sombrío",           "somber",                      "Oscuridad emocional; grises, lluvias, soledad, peso"),
        ("Fantástico",        "whimsical",                   "Juguetón y caprichoso; magia cotidiana, objetos imposibles, humor"),
    ],
    "🖼 Composición": [
        ("Regla de tercios",  "rule of thirds",              "Sujeto en los cruces de una cuadrícula 3×3; composición equilibrada"),
        ("Comp. centrada",    "centered composition",        "Sujeto exactamente en el centro del encuadre; impacto directo"),
        ("Simétrico",         "symmetric",                   "Mitad izquierda refleja la derecha; equilibrio visual perfecto"),
        ("Líneas guía",       "leading lines",               "Líneas en la imagen que guían la vista hacia el sujeto principal"),
        ("Plano enmarcado",   "framed shot",                 "Elementos del entorno enmarcan al sujeto (arcos, ventanas, ramas)"),
        ("Minimalista",       "minimalist",                  "Máximo espacio vacío, mínimo de elementos; simplicidad extrema"),
        ("Prof. en capas",    "layered depth",               "Primer plano, sujeto y fondo claramente diferenciados en capas"),
        ("Espacio negativo",  "negative space",              "Gran área vacía alrededor del sujeto que refuerza su aislamiento"),
        ("Comp. dinámica",    "dynamic composition",         "Diagonales y movimiento que dan energía y tensión a la imagen"),
        ("Silueta",           "silhouette",                  "Sujeto oscuro y opaco contra un fondo muy iluminado"),
        ("Elem. al frente",   "foreground elements",         "Objetos en primer plano que añaden profundidad y contexto"),
    ],
    "✨ Calidad": [
        ("Ultra detallado",   "ultra detailed",              "Máximo nivel de detalle en texturas, piel, telas y entornos"),
        ("Obra maestra",      "masterpiece",                 "Indicador de calidad excepcional; empuja al modelo al máximo"),
        ("Resolución 8K",     "8k resolution",               "Sugiere altísima resolución y nitidez extrema en toda la imagen"),
        ("Fotorrealista",     "photorealistic",              "Tan cercano a una foto real que es difícil distinguirlo"),
        ("Enfoque nítido",    "sharp focus",                 "Aristas muy definidas; sin desenfoque, máxima claridad"),
        ("Profesional",       "professional",                "Aspecto de producción profesional; bien expuesto y compuesto"),
        ("Premiado",          "award-winning",               "Calidad de fotografía ganadora de premios; composición cuidada"),
        ("Muy detallado",     "intricate details",           "Detalles complejos y elaborados; microdetalles visibles en todo"),
        ("Hiperrealista",     "hyper realistic",             "Más detallado que una foto; cada poro, hilo y textura visible"),
        ("Alta resolución",   "high resolution",             "Imagen grande y nítida; sin píxeles visibles"),
        ("Foto RAW",          "RAW photo",                   "Aspecto de fichero RAW sin procesar; grano natural y colores fieles"),
        ("Foto analógica",    "film photography",            "Estética de carrete fotográfico; grano, colores cálidos, imperfecciones"),
    ],
    "🎨 Arte/Estilo": [
        ("Hiperrealista",     "hyperrealistic",              "Pintura tan detallada que parece fotografía; tradición clásica moderna"),
        ("Impresionista",     "impressionist",               "Pinceladas sueltas que capturan la luz y el momento, no los detalles"),
        ("Art Nouveau",       "art nouveau",                 "Estilo de 1900: líneas curvas orgánicas, plantas, mujeres con flores"),
        ("Cyberpunk",         "cyberpunk",                   "Futuro distópico: neones, lluvia, implantes, megaciudades oscuras"),
        ("Vintage",           "vintage",                     "Aspecto envejecido de décadas pasadas; colores desaturados, grano"),
        ("Acuarela",          "watercolor",                  "Colores transparentes con bordes difusos; papel visible detrás"),
        ("Óleo",              "oil painting",                "Pintura al óleo clásica; empaste, pinceladas visibles, profundidad"),
        ("Concept art",       "concept art",                 "Arte de diseño para videojuegos/películas; funcional y expresivo"),
        ("Pintura digital",   "digital painting",            "Arte creado digitalmente imitando técnicas pictóricas tradicionales"),
        ("Anime",             "anime style",                 "Estética japonesa: ojos grandes, líneas limpias, colores planos"),
        ("Cine negro",        "film noir",                   "Blanco/negro con sombras duras; atmósfera de misterio y crimen"),
        ("Barroco",           "baroque",                     "Arte del s.XVII: dramatismo, movimiento, contrastes de luz extremos"),
        ("Surrealismo",       "surrealism",                  "Imágenes imposibles de sueño; fusión de objetos incongruentes"),
        ("Pixel art",         "pixel art",                   "Arte retro con píxeles grandes visibles; estética de videojuegos 8/16-bit"),
        ("Boceto",            "sketch",                      "Dibujo a lápiz o carboncillo; líneas sueltas, sin color ni relleno"),
    ],
}

# ── Constantes IA ─────────────────────────────────────────────────
MAX_HIST_IA = 12

# ══════════════════════════════════════════════════════════════════
# ESTILOS POR FAMILIA (toggle "Estilo" en el panel del modelo)
# ══════════════════════════════════════════════════════════════════
# Cada familia define sus estilos. "Auto" significa que el LLM decide
# según la idea. El resto fuerza una categoría que se inyecta como hint
# en la plantilla específica de cada familia.
# Paletas de estilo reutilizables por TIPO de familia (imagen). Las 4 familias
# con inyección a medida (flux/z_image/gpt_image/nano_banana) conservan su set;
# el resto usa una paleta acorde a su naturaleza, inyectada de forma genérica
# (_inyectar_estilo_imagen_generico) a partir de _ESTILO_HINT_IMG.
_PAL_FOTO     = ["Auto", "Photoreal", "Anime", "Creative", "Fantasy", "SciFi"]
_PAL_ANIME    = ["Auto", "Anime", "Manga", "Ilustración", "Chibi", "Realista", "Acuarela"]
_PAL_REALISMO = ["Auto", "Fotorrealista", "Retrato", "Cinematográfico", "Editorial", "Fantasía", "SciFi"]
_PAL_ARTE     = ["Auto", "Cinematográfico", "Ilustración", "Pintura", "Concept-Art", "Surrealista", "Anime"]
_PAL_DISENO   = ["Auto", "Tipografía", "Póster", "Logo", "Ilustración", "Flat-Design", "3D-Render"]
_PAL_CINE_IMG = ["Auto", "Cinematográfico", "Fotorrealista", "Dramático", "Editorial", "Fantasía", "SciFi"]

ESTILOS_POR_FAMILIA = {
    # ── Especiales (inyección a medida, NO tocar las claves) ──
    "z_image": [
        "Auto", "Photoreal", "Anime", "Creative", "Fantasy", "SciFi",
    ],
    "gpt_image": [
        "Auto", "Photoreal", "Editorial", "Illustration",
        "UI-Mockup", "Poster-Typography",
    ],
    "nano_banana": [
        "Auto", "Photoreal", "Editorial",
        "Character-Consistent", "Artistic", "Edit-Focus",
    ],
    "flux": [
        "Auto", "Photoreal", "Anime", "Creative", "Fantasy", "SciFi",
    ],
    # ── Resto de familias (clave = cabecera de GRUPOS_IMAGEN), por paleta ──
    "── Anime / Ilustración ──": _PAL_ANIME,
    "── Estilos Únicos SD ──": _PAL_ARTE,
    "── Grok (xAI en SeaArt) ──": _PAL_FOTO,
    "── Higgsfield ──": _PAL_CINE_IMG,
    "── Ideogram (en SeaArt) ──": _PAL_DISENO,
    "── Kling Image (Kuaishou en SeaArt) ──": _PAL_FOTO,
    "── MAI Image (Microsoft en SeaArt) ──": _PAL_FOTO,
    "── Midjourney / Niji (en SeaArt) ──": _PAL_ARTE,
    "── Qwen (Alibaba en SeaArt) ──": _PAL_FOTO,
    "── Realismo SD ──": _PAL_REALISMO,
    "── Reve ──": _PAL_FOTO,
    "── SeaArt Familia (Film/Story/Fusion/Genesis/Ultra) ──": _PAL_ARTE,
    "── SeaArt Oficiales ──": _PAL_ARTE,
    "── Seedream (ByteDance en SeaArt) ──": _PAL_FOTO,
    "── Stable Diffusion 3.5 ──": _PAL_REALISMO,
    "── Wan ──": _PAL_FOTO,
}

# Modelos de la familia FLUX (para el toggle "Estilo"). Se deriva del grupo
# "Familia FLUX" de GRUPOS_IMAGEN para no mantener una lista aparte; incluye
# los que no llevan 'flux' en el nombre (p. ej. Midjourney Mimic Neo).
_MODELOS_FLUX = {m for cab, ms in GRUPOS_IMAGEN if "flux" in cab.lower() for m in ms}

# Membresía por grupo para las 4 familias especiales (más robusto que el nombre:
# p. ej. GLM-Image está en el grupo Z-Image pero no lleva 'z-image' en el nombre).
def _modelos_de_grupo(substr):
    return {m for cab, ms in GRUPOS_IMAGEN if substr in cab.lower() for m in ms}

_MODELOS_ZIMAGE = _modelos_de_grupo("z-image")
_MODELOS_GPTIMG = _modelos_de_grupo("gpt image")
_MODELOS_NANO   = _modelos_de_grupo("nano banana")

# Mapa modelo → cabecera de familia (para el resto de familias no-especiales).
_FAMILIA_IMG_DE_MODELO = {m: cab for cab, ms in GRUPOS_IMAGEN for m in ms}


def detectar_familia(modelo_nombre: str) -> str | None:
    """Detecta la familia de un modelo (clave de ESTILOS_POR_FAMILIA).

    Las 4 familias especiales devuelven su clave semántica (inyección a
    medida); el resto devuelve la cabecera del grupo de GRUPOS_IMAGEN.
    None si no se detecta. Usada por el combo "Estilo" para repoblar opciones.
    """
    if not modelo_nombre:
        return None
    n = modelo_nombre.lower()
    if modelo_nombre in _MODELOS_ZIMAGE or "z-image" in n or "z image" in n or "z_image" in n:
        return "z_image"
    if modelo_nombre in _MODELOS_GPTIMG or "gpt image" in n or "gpt-image" in n:
        return "gpt_image"
    if modelo_nombre in _MODELOS_NANO or "nano banana" in n or "nano-banana" in n or "nano_banana" in n:
        return "nano_banana"
    if modelo_nombre in _MODELOS_FLUX or "flux" in n:
        return "flux"
    return _FAMILIA_IMG_DE_MODELO.get(modelo_nombre)


# ── Estilo por familia para VÍDEO (paletas acordes al motor) ──
_PALV_CINE  = ["Auto", "Cinematográfico", "Anime", "Realista", "3D / Pixar",
               "Cyberpunk / Neón", "Vintage / Retro"]
_PALV_REAL  = ["Auto", "Realista", "Cinematográfico", "Documental", "Acción", "Cámara lenta"]
_PALV_ANIME = ["Auto", "Anime", "Cartoon", "3D / Pixar", "Cómic", "Acuarela / Artístico"]

ESTILOS_POR_FAMILIA_VIDEO = {
    "── SeaArt Oficiales ──": _PALV_CINE,
    "── Kling ──": _PALV_CINE,
    "── Seedance ──": _PALV_CINE,
    "── StarDream ──": _PALV_CINE,
    "── Vidu ──": _PALV_CINE,
    "── Reference ──": _PALV_CINE,
    "── Otros Motores ──": _PALV_CINE,
    "── Wan ──": _PALV_REAL,
    "── Hailuo ──": _PALV_REAL,
    "── PixVerse ──": _PALV_REAL,
    "── Grok ──": _PALV_REAL,
    "── Happy Horse ──": _PALV_ANIME,
    "── Nano Banana ──": _PALV_ANIME,
}

_FAMILIA_VID_DE_MODELO = {m: cab for cab, ms in GRUPOS_VIDEO for m in ms}


def detectar_familia_video(modelo_nombre: str) -> str | None:
    """Cabecera de familia de un modelo de vídeo (clave de ESTILOS_POR_FAMILIA_VIDEO)."""
    if not modelo_nombre:
        return None
    return _FAMILIA_VID_DE_MODELO.get(modelo_nombre)


# ══════════════════════════════════════════════════════════════════
# PLATAFORMAS
# ══════════════════════════════════════════════════════════════════
PLATAFORMAS_IMAGEN = {
    "SeaArt / Tensor.Art":        "sd",
    "ComfyUI / Fooocus":          "sd",
    "ChatGPT / GPT Image":         "natural",
    "Grok (xAI)":                  "natural",
    "Higgsfield":                  "natural",
    "Magnific":                    "natural",
}

PLATAFORMAS_VIDEO = {
    "SeaArt Video":     "sd",
    "ComfyUI / Fooocus": "sd",
    "Kling AI":         "natural",
    "Veo / Gemini":     "natural",
    # Agregadores dados de alta sep-2026 SOLO COMO MAPEO (el usuario aun no
    # genera ahi). Pollo AI aporta los motores que no cubriamos por otra via
    # (Runway, Luma, Pika, Hunyuan, SkyReels) -> hace innecesarias las
    # plataformas "Pika / Luma" y "Runway Gen" que estaban apagadas.
    "Pollo AI":         "natural",
    "Higgsfield":       "natural",
    # APAGADA 2026-07-04 (sin modelos dados de alta):
    # "Pixverse.ai":      "natural",
}

PLATAFORMAS_AUDIO = {
    "Suno":             "natural",
    "Udio":             "natural",
    "SeaArt Audio":     "natural",
}

PLATAFORMAS_IMAGEN_LISTA = sorted(PLATAFORMAS_IMAGEN.keys())
PLATAFORMAS_VIDEO_LISTA  = sorted(PLATAFORMAS_VIDEO.keys())
PLATAFORMAS_AUDIO_LISTA  = sorted(PLATAFORMAS_AUDIO.keys())

# ══════════════════════════════════════════════════════════════════
# DESTINOS DE PUBLICACIÓN
# ══════════════════════════════════════════════════════════════════
DESTINOS = ["— Personal —"] + sorted([
    "Instagram",
    "TikTok",
    "YouTube",
    "YouTube Shorts",
    "Twitter / X",
    "Anthum (concurso)",
    "Freepik community",
    "Reddit",
    "LinkedIn",
    "Web / Blog",
    "Cliente",
], key=clave_alfabetica)

# ── Motores por plataforma ────────────────────────────
MOTORES_VIDEO = {
    "SeaArt Video": MODELOS_VIDEO_FLAT,
    "ComfyUI / Fooocus": MODELOS_VIDEO_COMFYUI_FLAT,
    "Kling AI": ["Kling 01 Video Model", "Kling 2.6", "Kling 3.0", "Kling 3.0 Omni",
                 "Kling 3.0 Turbo"],
    "Veo / Gemini": ["Veo 3.1", "Gemini Omni Flash"],
    # Pollo AI: solo los motores que NO cubrimos ya por SeaArt (el resto de su
    # catalogo -- Kling/Veo/Sora/Hailuo/Wan/Vidu/Seedance/PixVerse -- duplica).
    "Pollo AI": ["Runway Gen-4 Turbo", "Runway Gen-3 Turbo", "Luma Ray 2",
                 "Luma Ray 2 Flash", "Pika 2.2", "Hunyuan Video", "SkyReels V2"],
    # Higgsfield: solo su motor PROPIO de video (DOP, control por presets).
    "Higgsfield": ["Higgsfield DOP"],
    # Apagada (ver PLATAFORMAS_VIDEO): "Pixverse.ai"
}

MOTORES_AUDIO = {
    "Suno": ["Suno v5.5", "Suno v5", "Suno v4.5", "Suno v4.5-All (Free)", "Suno v4"],
    "Udio": ["Udio v4", "Udio v1.5"],
    "SeaArt Audio": ["Minimax Music 2.6", "Minimax Music 2.5", "Mureka V9", "SeaArt MusicGo"],
}

MOTOR_DEFAULT = {
    "SeaArt Video": "Kling 3.0",
    "Kling AI": "Kling 3.0",
    "Suno": "Suno v5.5",
    "Udio": "Udio v4",
    "SeaArt Audio": "Minimax Music 2.6",
}

# ── Límites de Tokens por Plataforma ─────────────────
TOKEN_LIMITS = {
    "SeaArt / Tensor.Art": 200,
    "ComfyUI / Fooocus": 75,
    "Midjourney": 60,
    "ChatGPT / GPT Image": 75,
    "Adobe Firefly": 75,
    "Ideogram / Recraft": 75,
    "Leonardo.AI": 75,
    "Google Imagen": 75,
    "Fooocus": 75,
    "Focusss": 75,
    "Magnific": 75,
    "SeaArt Video": 200,
    "Pika / Luma": 60,
    "Kling AI": 75,
    "Runway Gen": 75,
    "Pixverse.ai": 75,
    "Veo / Gemini": 75,
    "Suno": 500,
    "SeaArt Audio": 400,
}

# ══════════════════════════════════════════════════════════════════
# ESPECIFICACIONES DE MODELOS (vídeo / imagen / audio)
# ══════════════════════════════════════════════════════════════════
# MODEL_SPECS, MODEL_SPECS_IMAGEN y MODEL_SPECS_AUDIO se cargan
# bajo demanda — ver _LAZY_DATASETS arriba. El acceso sigue siendo
# el mismo: from config import MODEL_SPECS_IMAGEN, etc.

# ══════════════════════════════════════════════════════════════════
# PRESETS DE PROMPT POR MODELO (plantillas base probadas)
# El LLM usa estos como esqueleto y adapta según la idea del usuario
# ══════════════════════════════════════════════════════════════════
PROMPT_TEMPLATES = {
    # ── Realismo SD (tag-based con pesos) ────────────────────
    "fotorrealismo_sd": {
        "modelos": ["Z Image Turbo", "CyberRealistic", "Realistic Vision V6.0 B1", "Juggernaut XL", "DreamShaper", "DreamShaper XL", "Illustrious Realism by Klaabu", "Real Dream SDXL", "MajicMIX Realistic v6", "Prodigies"],
        "positive_base": "({encuadre}:1.2), {sujeto}, {detalles_sujeto}, (detailed skin texture:1.2), {ropa_accesorios}, {entorno}, ({iluminacion}:1.3), {atmosfera}, {paleta_colores}, {estilo_fotografico}, sharp focus, photorealistic, 8K, masterpiece, highly detailed",
        "negative_base": "(worst quality, low quality, lowres, blurry:1.4), (anime, cartoon, 3d render, painting, drawing, illustration:1.3), (text, watermark, signature:1.3), (deformed, distorted, asymmetric:1.2), jpeg artifacts",
    },
    "retrato_sd": {
        "modelos": ["Z Image Turbo", "CyberRealistic", "Realistic Vision V6.0 B1", "Prodigies", "MajicMIX Realistic v6"],
        "positive_base": "(close-up portrait:1.3), {sujeto}, (detailed eyes:1.2), (detailed skin:1.2), {expresion}, {pelo}, {ropa}, ({iluminacion}:1.3), shallow DOF, bokeh, {fondo}, professional portrait photography, 8K, masterpiece",
        "negative_base": "(worst quality, low quality:1.4), (bad anatomy, deformed hands, extra fingers:1.3), (anime, cartoon:1.3), (text, watermark:1.3), (overexposed:0.9), blurry, jpeg artifacts",
    },
    # ── Anime/Ilustración (tag-based Danbooru) ───────────────
    "anime_illustrious": {
        "modelos": ["NiwaStyle - Animax ColorPop (Illustrious)", "NiwaStyle - Animax Plus (Illustrious)", "NiwaStyle - Animax Chill (Illustrious)"],
        "positive_base": "masterpiece, 8k, Highest Quality, detail, high resolution, Digital Painting, ultra detailed, {encuadre}, {sujeto}, {pelo}, {ojos}, {ropa}, {pose}, {entorno}, ({iluminacion}:1.2), {atmosfera}, {estilo}",
        "negative_base": "(worst quality, low quality, lowres:1.4), (photorealistic, photo, realistic skin:1.3), (3d render, hyperrealistic:1.2), bad anatomy, deformed, text, watermark",
    },
    # ── CG/Sci-fi ────────────────────────────────────────────
    "cg_scifi": {
        "modelos": ["Pipi-iL-CG6.5", "DreamShaper"],
        "positive_base": "({encuadre}:1.2), {sujeto}, {detalles_mecanicos}, (detailed mechanical parts:1.3), {entorno}, ({iluminacion}:1.3), {atmosfera}, CG render quality, {paleta_colores}, cinematic composition, 8K, ultra detailed, masterpiece",
        "negative_base": "(worst quality, low quality:1.4), (blurry, out of focus:1.2), simple background, flat lighting, text, watermark, (deformed:1.2)",
    },
    # ── FLUX / Natural Language ──────────────────────────────
    "natural_flux": {
        "modelos": ["FLUX.1 [dev]", "FLUX.1-dev-fp8", "FLUX.1D UltraReal", "SeaArt Infinity", "SeaArt Infinity V2.0", "Reve 2.0", "MAI-Image-2.5", "MAI-Image-2.5-Flash",
                    "Midjourney Mimic Neo", "CyberRealistic Flux", "Realistic Amateurs Flux", "Real Vision - FLUX", "True Real Vision - Flux", "Goddess Project (FLUX)", "lyh_anime_Flux", "XE: Anime Hentai (FLUX)", "AnimePro FLUX", "XE: Cosplay Flux", "VNS - Horror World Flux", "Moxie Fusion Flux", "Nai3-Flux", "Alpha_Fantasy_Flux", "XE: Figure Flux", "Disney Pixar Flux", "MASTER FLUX (LoRA merged with flux1-dev fp16)", "FLUX.1 Krea dev", "Flux 1.Dev UNLOCKED fp_16 & fp_8 [GGUF]", "FLUX.1-Kontext-dev", "Nepotism", "Splashed Flux"],
        "positive_base": "A {encuadre} of {sujeto}, {accion_pose}, {entorno_detallado}, {iluminacion_descriptiva}, {atmosfera}, {estilo_referencia}, {calidad}",
        "negative_base": "",
    },
    # ── Vídeo Cinematográfico ────────────────────────────────
    "video_cinematico": {
        "modelos": ["Kling 3.0", "Kling 3.0 Omni", "SeaArt Ultra Pro", "Wan 2.6"],
        "positive_base": "{duracion}. {encuadre_camara}, {sujeto} {accion}, {entorno}, {iluminacion}, {movimiento_camara}, {atmosfera}. Audio: {audio_desc}.",
        "negative_base": "worst quality, static shot, no movement, blurry, low resolution, deformed, morphing, flickering",
    },
}

# ── Autor ─────────────────────────────────────────────────────────
AUTHOR = {
    "nombre":    "Gustaafvito",
    "web":       "https://gustaafvito.com/",
    "instagram": "gustaafvito.creador.ia",
    "tiktok":    "gustaafvito.creador.ia",
    "youtube":   "@GustaafvitocreadorIA",
    "github":    "https://github.com/Gustaafvito",
    "x":         "gustaafvito",  # X / Twitter handle (sin @)
}

# ── Auto-sugerir Negativos por Estilo ─────────────────────────────
# ESTILO_NEGATIVO_AUTO se carga lazy — ver _LAZY_DATASETS arriba.

# ── Helpers ───────────────────────────────────────────────────────
def es_separador(valor):
    return valor.startswith("──")

def get_model_specs(motor_name):
    # El JSON curado manda; si el modelo de vídeo no está (típico de modelos
    # ComfyUI locales: LTX, Wan, SVD…), se sintetizan specs por familia.
    return _get_dataset("MODEL_SPECS").get(motor_name) or comfy_video_specs(motor_name)

def get_image_model_specs(modelo_name):
    # El JSON curado manda; si el modelo no está (típico de checkpoints
    # ComfyUI locales), se sintetizan specs por familia detectada en el nombre.
    return _get_dataset("MODEL_SPECS_IMAGEN").get(modelo_name) or comfy_image_specs(modelo_name)

def get_audio_model_specs(modelo_name):
    # El JSON curado manda; fallback sintético para modelos de audio locales
    # de ComfyUI (ACE-Step) que no están en el catálogo.
    return _get_dataset("MODEL_SPECS_AUDIO").get(modelo_name) or comfy_audio_specs(modelo_name)

def get_prompt_template(modelo_name):
    """Busca el template de prompt que aplica a este modelo."""
    for key, tmpl in PROMPT_TEMPLATES.items():
        if modelo_name in tmpl.get("modelos", []):
            return tmpl
    return None


def get_theme_colors(is_light: bool) -> dict:
    """Devuelve paleta de colores adaptativa para UI basada en el tema.

    Incluye `chk_text`, `chk_bg`, `panel_bg`, `panel_text`, `accent_text`
    para garantizar contraste en modo light en checkboxes, scrollables
    y labels que viven dentro de tabs."""
    if is_light:
        return {
            "hdr_bg": "#e8e8e8", "hdr_text": "#111827", "hdr_label": "#4b5563",
            "combo_bg": "#ffffff", "combo_border": "#9ca3af", "combo_btn": "#2563eb",
            "badge_bg": "#dbeafe",
            "btn_bg": "#ffffff", "btn_hover": "#f3f4f6",
            "key_bg": "#7c3aed", "key_hover": "#6d28d9",
            "modo_bg": "#e8e8e8", "modo_label": "#4b5563",
            "nsfw_text_on": "#dc2626", "nsfw_text_off": "#4b5563",
            "nsfw_border_on": "#dc2626", "nsfw_border_off": "#9ca3af", "nsfw_fg": "#9ca3af",
            "trad_text_on": "#2563eb",
            "trad_border_on": "#2563eb",
            "fg_frame": "#f3f4f6", "fg_off": "#e5e7eb",
            "fg_dark": "#374151", "fg_dark_border": "#9ca3af",
            "fg_dark_text": "#4b5563", "fg_dark_hover": "#4b5563",
            "instr_active_text": "#7c3aed", "instr_active_border": "#7c3aed",
            "chk_text": "#1f2937",
            "chk_bg": "#ffffff",
            "chk_hover": "#bfdbfe",
            "chk_border": "#6b7280",
            "panel_bg": "#f9fafb",
            "panel_text": "#111827",
            "panel_label": "#1f2937",
            "accent_text": "#2563eb",
            "muted_text": "#4b5563",
            "card_bg": "#ffffff",
            "card_border": "#d1d5db",
            "card_title": "#1e40af",
            "danger_text": "#dc2626",
            "success_text": "#059669",
        }
    else:
        return {
            "hdr_bg": "#0d1117", "hdr_text": "#e5e7eb", "hdr_label": "#888888",
            "combo_bg": "#1a2030", "combo_border": "#2a3a50", "combo_btn": "#2a3a50",
            "badge_bg": "#1a2a3a",
            "btn_bg": "#1a1a2a", "btn_hover": "#2a2a3a",
            "key_bg": "#3a2a4a", "key_hover": "#4a3a5a",
            "modo_bg": "#0f1318", "modo_label": "#888888",
            "nsfw_text_on": "#fca5a5", "nsfw_text_off": "#9ca3af",
            "nsfw_border_on": "#ef4444", "nsfw_border_off": "#374151", "nsfw_fg": "#1f2937",
            "trad_text_on": "#93c5fd",
            "trad_border_on": "#3b82f6",
            "fg_frame": "#1f2937", "fg_off": "#2a3a50",
            "fg_dark": "#1f2937", "fg_dark_border": "#374151",
            "fg_dark_text": "#9ca3af", "fg_dark_hover": "#374151",
            "instr_active_text": "#9ca3af", "instr_active_border": "#374151",
            "chk_text": "#ffffff",
            "chk_bg": "#0d1117",
            "chk_hover": "#1f2937",
            "chk_border": "#374151",
            "panel_bg": "#0f1318",
            "panel_text": "#e5e7eb",
            "panel_label": "#9ca3af",
            "accent_text": "#60a5fa",
            "muted_text": "#9ca3af",
            "card_bg": "#111820",
            "card_border": "#1f2937",
            "card_title": "#aaccee",
            "danger_text": "#f87171",
            "success_text": "#34d399",
        }


# ══════════════════════════════════════════════════════════════════
# BIBLIOTECA DE PROMPTS DE EJEMPLO (ordenados alfabéticamente por título)
# Muestras para nuevos usuarios.
#
# Campos por entrada:
#   titulo (str)       — nombre visible en la UI
#   modo (str)         — "imagen" | "video" | "audio"
#   modelo (str)       — modelo recomendado (debe existir en MODEL_SPECS/MODEL_SPECS_IMAGEN/MODEL_SPECS_AUDIO)
#   plataforma (str)   — plataforma donde se ejecutó el prompt
#   dificultad (str)   — "principiante" | "medio" | "avanzado"
#   tags (list[str])   — etiquetas libres para búsqueda fina
#   autor (str)        — quién aportó/validó el prompt
#   prompt (str)       — el prompt completo (POSITIVE + NEGATIVE si aplica)
#   estilos (list[str])— estilos visibles en el catálogo
# ══════════════════════════════════════════════════════════════════
# BIBLIOTECA_EJEMPLOS se carga lazy — ver _LAZY_DATASETS arriba.


# ══════════════════════════════════════════════════════════════════
# VALIDADOR DE BIBLIOTECA
# ══════════════════════════════════════════════════════════════════
def validar_biblioteca(estricto: bool = False) -> list[str]:
    """
    Verifica la integridad de BIBLIOTECA_EJEMPLOS.

    Detecta:
      - Campos obligatorios faltantes (titulo, modo, modelo, prompt).
      - Valores de modo inválidos (debe ser imagen/video/audio).
      - Valores de dificultad inválidos (debe ser principiante/medio/avanzado).
      - Modelos que no existen en MODEL_SPECS, MODEL_SPECS_IMAGEN ni MODEL_SPECS_AUDIO.
      - Plataformas que no existen en PLATAFORMAS_IMAGEN/VIDEO/AUDIO.
      - Títulos duplicados.
      - Tipos incorrectos (tags debe ser lista, prompt debe ser string, etc.).

    Args:
        estricto: si True, también avisa de campos opcionales faltantes
                  (plataforma, dificultad, tags, autor).

    Returns:
        Lista de strings con los problemas detectados (vacía si todo OK).

    Uso típico (en arranque opcional):
        from config import validar_biblioteca
        problemas = validar_biblioteca()
        if problemas:
            logger.warning("Biblioteca con problemas: " + "; ".join(problemas))
    """
    problemas = []

    MODOS_VALIDOS = {"imagen", "video", "audio"}
    DIFICULTADES_VALIDAS = {"principiante", "medio", "avanzado"}
    CAMPOS_OBLIGATORIOS = ("titulo", "modo", "modelo", "prompt")
    CAMPOS_OPCIONALES = ("plataforma", "dificultad", "tags", "autor", "estilos")

    # Construir conjunto de modelos válidos (de los tres MODEL_SPECS)
    modelos_validos = set()
    for nombre in ("MODEL_SPECS", "MODEL_SPECS_IMAGEN", "MODEL_SPECS_AUDIO"):
        modelos_validos.update(_get_dataset(nombre).keys())

    # Construir conjunto de plataformas válidas
    plataformas_validas = (
        set(PLATAFORMAS_IMAGEN.keys())
        | set(PLATAFORMAS_VIDEO.keys())
        | set(PLATAFORMAS_AUDIO.keys())
    )

    # Detectar títulos duplicados
    titulos_vistos = {}
    for i, entrada in enumerate(_get_dataset("BIBLIOTECA_EJEMPLOS")):
        prefijo = f"#{i+1}"
        titulo = entrada.get("titulo", "")
        if titulo in titulos_vistos:
            problemas.append(
                f"{prefijo} '{titulo}': título duplicado (también en #{titulos_vistos[titulo]+1})"
            )
        else:
            titulos_vistos[titulo] = i

        # Campos obligatorios
        for campo in CAMPOS_OBLIGATORIOS:
            if campo not in entrada:
                problemas.append(f"{prefijo} '{titulo}': falta campo obligatorio '{campo}'")

        # Campos opcionales (solo en modo estricto)
        if estricto:
            for campo in CAMPOS_OPCIONALES:
                if campo not in entrada:
                    problemas.append(f"{prefijo} '{titulo}': falta campo opcional '{campo}'")

        # Validar valores
        modo = entrada.get("modo", "")
        if modo and modo not in MODOS_VALIDOS:
            problemas.append(f"{prefijo} '{titulo}': modo '{modo}' inválido (esperado: imagen/video/audio)")

        dificultad = entrada.get("dificultad", "")
        if dificultad and dificultad not in DIFICULTADES_VALIDAS:
            problemas.append(
                f"{prefijo} '{titulo}': dificultad '{dificultad}' inválida "
                f"(esperado: principiante/medio/avanzado)"
            )

        modelo = entrada.get("modelo", "")
        if modelo and modelo not in modelos_validos:
            problemas.append(f"{prefijo} '{titulo}': modelo '{modelo}' no existe en MODEL_SPECS")

        plataforma = entrada.get("plataforma", "")
        if plataforma and plataforma not in plataformas_validas:
            problemas.append(
                f"{prefijo} '{titulo}': plataforma '{plataforma}' no existe en PLATAFORMAS_*"
            )

        # Tipos
        tags = entrada.get("tags")
        if tags is not None and not isinstance(tags, list):
            problemas.append(f"{prefijo} '{titulo}': 'tags' debe ser lista, no {type(tags).__name__}")

        estilos = entrada.get("estilos")
        if estilos is not None and not isinstance(estilos, list):
            problemas.append(
                f"{prefijo} '{titulo}': 'estilos' debe ser lista, no {type(estilos).__name__}"
            )

        prompt = entrada.get("prompt")
        if prompt is not None and not isinstance(prompt, str):
            problemas.append(f"{prefijo} '{titulo}': 'prompt' debe ser str, no {type(prompt).__name__}")
        elif prompt is not None and len(prompt.strip()) == 0:
            problemas.append(f"{prefijo} '{titulo}': 'prompt' está vacío")

    return problemas


# ══════════════════════════════════════════════════════════════════
# VALIDADOR DE MODELOS
# Verifica que todos los modelos en listas existan en specs y viceversa
# ══════════════════════════════════════════════════════════════════
def validar_modelos() -> list[str]:
    """
    Verifica la integridad de modelos entre listas y specs.

    Detecta:
      - Modelos en listas (GRUPOS_*) sin especificación en MODEL_SPECS_*
      - Especificaciones en MODEL_SPECS_* sin modelo en ninguna lista

    Returns:
        Lista de strings con los problemas detectados (vacía si todo OK).
    """
    problemas = []

    # Recopilar todos los modelos de las listas planas
    modelos_en_listas = set()

    for g, ms in GRUPOS_IMAGEN:
        for m in ms:
            modelos_en_listas.add(m)
    for g, ms in GRUPOS_IMAGEN_COMFYUI:
        for m in ms:
            modelos_en_listas.add(m)

    modelos_en_specs = set(_get_dataset("MODEL_SPECS_IMAGEN").keys())

    # Modelos en listas sin spec
    for m in modelos_en_listas:
        if m not in modelos_en_specs:
            problemas.append(f"Modelo '{m}' en GRUPOS_IMAGEN pero sin spec en MODEL_SPECS_IMAGEN")

    # Specs sin modelo en lista (INFO, no error)
    for m in modelos_en_specs:
        if m not in modelos_en_listas:
            logger.debug(f"[INFO] Modelo '{m}' tiene spec pero no aparece en GRUPOS_IMAGEN")

    # Video
    modelos_video_lista = set()
    for g, ms in GRUPOS_VIDEO:
        for m in ms:
            modelos_video_lista.add(m)
    for g, ms in GRUPOS_VIDEO_COMFYUI:
        for m in ms:
            modelos_video_lista.add(m)

    modelos_video_specs = set(_get_dataset("MODEL_SPECS").keys())

    for m in modelos_video_lista:
        if m not in modelos_video_specs:
            problemas.append(f"Modelo '{m}' en GRUPOS_VIDEO pero sin spec en MODEL_SPECS")

    # Audio
    modelos_audio_lista = set()
    for g, ms in GRUPOS_AUDIO:
        for m in ms:
            modelos_audio_lista.add(m)

    modelos_audio_specs = set(_get_dataset("MODEL_SPECS_AUDIO").keys())

    for m in modelos_audio_lista:
        if m not in modelos_audio_specs:
            problemas.append(f"Modelo '{m}' en GRUPOS_AUDIO pero sin spec en MODEL_SPECS_AUDIO")

    return problemas
