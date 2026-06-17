"""
G-Prompt Studio v1.0 — Configuración y constantes.
Modelos, estilos, ratios, presets de negativos, colores UI.
"""
import logging
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

def _load_json_data(filename: str):
    """Carga data/<filename> y devuelve el objeto deserializado."""
    path = _DATA_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return _json.load(f)

# Mapa de constantes lazy → archivo en data/. Solo cuando se accede al
# atributo por primera vez (vía __getattr__) se hace I/O y se cachea.
_LAZY_DATASETS = {
    "MODEL_SPECS":          "model_specs_video.json",
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
APP_TITLE = f"🧠 G-Prompt Studio v{PUBLIC_VERSION}"

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
GRUPOS_VIDEO = [
    ("── SeaArt Oficiales ──", sorted([
        "SeaArt Film Video", "SeaArt Ultra Pro",
    ])),
    ("── Kling ──", sorted([
        "Kling 01 Video Model", "Kling 2.6", "Kling 3.0", "Kling 3.0 Omni",
    ])),
    ("── Seedance ──", sorted([
        "Seedance 1.5 PRO", "Seedance 2.0", "Seedance 2.0 Fast",
    ])),
    ("── Nano Banana ──", sorted([
        "Nano Banana Video", "Nano Banana Pro Video",
    ])),
    ("── Otros Motores ──", sorted([
        "Wan 2.6", "Sora2 Video", "Veo 3.1", "Gemini Omni",
    ])),
]

# ══════════════════════════════════════════════════════════════════
# MODELOS DE IMAGEN
# ══════════════════════════════════════════════════════════════════
GRUPOS_IMAGEN = [
    ("── Anime / Ilustración ──", sorted([
        "Counterfeit V3.0",
        "Disney Pixar Cartoon type B",
        "GhostMix",
        "Hassaku XL (Illustrious)",
        "Lily-Illustrious XL",
        "majicMIX fantasy",
        "MiaoMiao Harem",
        "NiwaStyle - Animax (Illustrious)",
        "NiwaStyle - Animax Anime (Illustrious)",
        "NiwaStyle - Animax Chill (Illustrious)",
        "NiwaStyle - Animax ColorPop (Illustrious)",
        "NiwaStyle - Animax Plus (Illustrious)",
        "NiwaStyle - Anime (SDXL)",
        "NoobAI-XL (NAI-XL)",
        "Pie - Models 🥧",
        "Pipi-iL-CG6.5",
        "Pixel Illustrious",
        "REED_XXX_illustrious_SDXL",
        "SDXL FaeTastic",
        "T-Ponynai3 V6",
        "Temporal Paradox Mix",
        "WAI-Illustrious-SDXL",
        "WAI-Pluralistic-Noob",
    ])),
    ("── Familia FLUX ──", sorted([
        "FLUX.1 [dev]",
        "FLUX.1-dev-fp8",
        "FLUX.1D UltraReal",
        "MASTER FLUX (LoRA merged with flux1-dev fp16)",
        "Midjourney Mimic Neo",
        "CyberRealistic Flux",
        "Realistic Amateurs Flux",
        "Real Vision - FLUX",
        "True Real Vision - Flux",
        "lyh_anime_Flux",
        "XE: Anime Hentai (FLUX)",
        "Goddess Project (FLUX)",
        "XE: Cosplay Flux",
        "AnimePro FLUX",
        "VNS - Horror World Flux",
        "Moxie Fusion Flux",
        "Nai3-Flux",
        "Alpha_Fantasy_Flux",
        "XE: Figure Flux",
        "Disney Pixar Flux",
        "FLUX.1 Krea dev",
        "Flux 1.Dev UNLOCKED fp_16 & fp_8 [GGUF]",
        "FLUX.1-Kontext-dev",
        "Nepotism",
        "Splashed Flux",
    ])),
    ("── Familia Z-Image ──", sorted([
        "Z Image Turbo",
        "Z-Image-Base",
    ])),
    ("── GPT Image (OpenAI en SeaArt) ──", sorted([
        "GPT Image 1.5",
        "GPT Image 2",
    ])),
    ("── MAI Image (Microsoft en SeaArt) ──", sorted([
        "MAI-Image-2.5",
        "MAI-Image-2.5-Flash",
    ])),
    ("── Nano Banana ──", sorted([
        "Nano Banana", "Nano Banana Pro Image", "Nano Banana 2",
    ])),
    ("── Reve ──", sorted([
        "Reve 2.0",
    ])),
    ("── Realismo SD ──", sorted([
        "Alchemist Mix (Illustrious Realism)",
        "CyberRealistic",
        "Deliberate",
        "DreamShaper",
        "DreamShaper XL",
        "FantasticChix-HR",
        "Illustrious Realism by Klaabu",
        "Juggernaut XL",
        "MajicMIX Realistic v6",
        "NiwaStyle – DreamReal SR (Illustrious)",
        "PornRealistic",
        "Real Dream SDXL",
        "Realistic Vision V6.0 B1",
        "Realities Edge XL Turbo V7",
        "Prodigies",
        "Woman Realistic 3.1.0",
    ])),
    ("── SeaArt Familia (Film/Story/Fusion/Genesis/Ultra) ──", sorted([
        "SeaArt Film",
        "SeaArt Film V2.0",
        "SeaArt Film Edit",
        "SeaArt Film Edit 2.0",
        "SeaArt Film Edit 3.0",
        "SeaArt Furry XL V1.0",
        "SeaArt Story",
        "SeaArt Story 2.0",
        "SeaArt Story Edit",
        "SeaArt Fusion",
        "SeaArt Genesis",
        "SeaArt Ultra Edit",
    ])),
    ("── SeaArt Oficiales ──", sorted([
        "Luma Uni-1.1 Image",
        "SeaArt Infinity",
        "SeaArt Infinity V2.0",
        "SeaArt Realism",
    ])),
    ("── Stable Diffusion 3.5 ──", sorted([
        "SD 3.5 Large",
        "SD 3.5 Medium",
        "SD 3.5 Large Turbo",
    ])),
    ("── Estilos Únicos SD ──", sorted([
        "Inkpunk Diffusion",
        "Arcane Diffusion",
        "Cyberpunk Anime Diffusion",
        "Robo-Diffusion",
        "anima_pencil-XL",
        "Hollie Mengert Illustration",
        "Fred Herzog Photography Style",
    ])),
]

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


def escanear_modelos_comfyui(ruta_comfyui: str = None, preferencias: dict = None) -> tuple:
    """
    Escanea la carpeta de ComfyUI para encontrar modelos instalados.

    Returns:
        tuple: (grupos_img, grupos_vid) - listas de tuplas (grupo, [modelos])
    """
    if not ruta_comfyui:
        ruta_comfyui = get_comfyui_path(preferencias)

    if not ruta_comfyui or not Path(ruta_comfyui).exists():
        return None, None

    grupos_img = []
    grupos_vid = []

    checkpoints = Path(ruta_comfyui) / "models" / "checkpoints"
    if checkpoints.exists():
        # Modelos de imagen
        modelos_img = []
        # Modelos de video
        modelos_vid = []

        for f in checkpoints.glob("*.safetensors"):
            nombre = f.stem
            # Detectar si es modelo de video
            es_video = any(x in nombre.lower() for x in ["wan", "ltx", "svd", "i2v", "video", "stable_video"])
            if es_video:
                modelos_vid.append(nombre)
            else:
                modelos_img.append(nombre)

        modelos_img.extend([f.stem for f in checkpoints.glob("*.ckpt")])
        modelos_img.extend([f.stem for f in checkpoints.glob("*.pth")])

        modelos_img = sorted(modelos_img)
        modelos_vid = sorted(set(modelos_vid))

        if modelos_img:
            grupos_img.append(("── ComfyUI Checkpoints ──", modelos_img))
        if modelos_vid:
            grupos_vid.append(("── ComfyUI Video ──", modelos_vid))

    i2v = Path(ruta_comfyui) / "models" / "diffusion_models"
    if i2v.exists():
        modelos_video = sorted([f.stem for f in i2v.glob("*.safetensors")])
        modelos_video.extend(sorted([f.stem for f in i2v.glob("*.ckpt")]))
        # Filtrar solo los modelos de video conocidos
        modelos_video = [m for m in modelos_video if any(x in m.lower() for x in ["wan", "ltx", "svd", "i2v", "video", "stable_video"])]
        if modelos_video:
            grupos_vid.append(("── ComfyUI Video ──", modelos_video))

    return grupos_img if grupos_img else None, grupos_vid if grupos_vid else None


def _cargar_modelos_locales():
    """Carga modelos locales desde JSON con soporte para auto-discovery de ComfyUI."""
    import json as _json

    ruta_json = ARCHIVOS["modelos_comfy"]

    plantilla_default = {
        "_meta": {
            "version": 1,
            "descripcion": "Tus modelos locales. Edita este archivo o conecta ComfyUI para auto-discovery."
        },
        "imagen": [
            {"grupo": "── Checkpoints SDXL ──", "modelos": ["Juggernaut-XL v9 RunDiffusionPhoto v2", "RealVisXL V5.0 fp16", "JuggernautXL Ragnarok"]},
            {"grupo": "── Familia Z-Image ──", "modelos": ["z_image_bf16 (Base)", "z_image_turbo_bf16 (Turbo)", "zImageBase_base"]},
            {"grupo": "── Familia FLUX (UNet) ──", "modelos": ["flux-2-klein-base-4b-fp8"]},
            {"grupo": "── Edit ──", "modelos": ["qwen_image_edit_2509_fp8_e4m3fn"]},
        ],
        "video": [
            {"grupo": "── Wan 2.2 (Image-to-Video) ──", "modelos": ["wan2.2_i2v_high_noise_14B_fp8_scaled", "wan2.2_i2v_low_noise_14B_fp8_scaled"]},
            {"grupo": "── LTX-Video ──", "modelos": ["ltx-2.3-22b-dev-fp8"]},
            {"grupo": "── Stable Video ──", "modelos": ["svd"]},
        ]
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

    grupos_img = [(item.get("grupo", "── Otros ──"), sorted(item.get("modelos", []))) for item in data.get("imagen", [])]
    grupos_vid = [(item.get("grupo", "── Otros ──"), sorted(item.get("modelos", []))) for item in data.get("video", [])]

    # Auto-discovery: agregar modelos de ComfyUI si se configuró ruta
    comfy_ruta = data.get("comfyui_path") or ""
    if comfy_ruta and Path(comfy_ruta).exists():
        checkpoint_dir = Path(comfy_ruta) / "models" / "checkpoints"
        if checkpoint_dir.exists():
            modelos_img_comfy = []
            modelos_vid_comfy = []
            for f in checkpoint_dir.glob("*.safetensors"):
                nombre = f.stem
                if any(x in nombre.lower() for x in ["wan", "ltx", "svd", "i2v", "video"]):
                    modelos_vid_comfy.append(nombre)
                else:
                    modelos_img_comfy.append(nombre)

            modelos_img_comfy = sorted(set(modelos_img_comfy))
            modelos_vid_comfy = sorted(set(modelos_vid_comfy))

            if modelos_img_comfy:
                grupos_img.append(("── ComfyUI Local ──", modelos_img_comfy))
            if modelos_vid_comfy:
                grupos_vid.append(("── ComfyUI Video ──", modelos_vid_comfy))

    return grupos_img, grupos_vid


GRUPOS_IMAGEN_COMFYUI, GRUPOS_VIDEO_COMFYUI = _cargar_modelos_locales()

MODELOS_IMAGEN_COMFYUI_FLAT = []
for g, ms in GRUPOS_IMAGEN_COMFYUI:
    MODELOS_IMAGEN_COMFYUI_FLAT.append(g)
    MODELOS_IMAGEN_COMFYUI_FLAT.extend(ms)

MODELOS_VIDEO_COMFYUI_FLAT = []
for g, ms in GRUPOS_VIDEO_COMFYUI:
    MODELOS_VIDEO_COMFYUI_FLAT.append(g)
    MODELOS_VIDEO_COMFYUI_FLAT.extend(ms)

# ══════════════════════════════════════════════════════════════════
# MODELOS DE AUDIO
# ══════════════════════════════════════════════════════════════════
GRUPOS_AUDIO = [
    ("── Motores Externos ──", sorted([
        "Suno v5.5", "Suno v5", "Suno v4.5", "Suno v4",
    ])),
    ("── SeaArt Audio ──", sorted([
        "Minimax Music 2.6", "Minimax Music 2.5", "SeaArt MusicGo",
    ])),
]

def _lista_plana(grupos):
    r = []
    for g, ms in grupos:
        r.append(g)
        r.extend(ms)
    return r

MODELOS_VIDEO_FLAT  = _lista_plana(GRUPOS_VIDEO)
MODELOS_AUDIO_FLAT  = _lista_plana(GRUPOS_AUDIO)

# Orden alfabético INSENSIBLE A MAYÚSCULAS en TODOS los grupos de imagen, para
# que los nombres en minúscula (p. ej. lyh_anime_Flux) no caigan al final del
# desplegable (el sorted() por defecto es case-sensitive y ordena 'l' tras 'Z').
GRUPOS_IMAGEN = [(cab, sorted(ms, key=str.lower)) for cab, ms in GRUPOS_IMAGEN]

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
GRUPOS_MAGNIFIC_IMAGEN = [
    ("── Auto / Sugerido ──", [
        "Auto (Sugerencias)",
    ]),
    ("── OpenAI GPT ──", sorted([
        "GPT 2",
        "GPT 1.5 - High",
        "GPT 1.5",
        "GPT 1 - HQ",
        "GPT",
    ])),
    ("── Familia Flux ──", sorted([
        "Flux.2 Max",
        "Flux.2 Pro",
        "Flux.2 Flex",
        "Flux.2 Klein",
        "Flux.1 Kontext Max",
        "Flux.1 Kontext Pro",
        "Flux.1 Realism",
        "Flux.1 Fast",
        "Flux.1.1",
        "Flux.1",
    ])),
    ("── Mystic ──", sorted([
        "Mystic 2.5 Fluid",
    ])),
    ("── Google Imagen ──", sorted([
        "Google Imagen 4 Ultra",
        "Google Imagen 4",
        "Google Imagen 3",
    ])),
    ("── Seedream ──", sorted([
        "Seedream 5 Lite",
        "Seedream 4.5",
        "Seedream 4 4K",
        "Seedream 4",
    ])),
    ("── Recraft ──", sorted([
        "Recraft V4 Pro",
        "Recraft V4",
    ])),
    ("── Otros Magnific ──", sorted([
        "Z-Image",
        "Qwen",
        "Grok",
        "Classic",
        "Classic Fast",
    ])),
]
MODELOS_MAGNIFIC_IMAGEN_FLAT = _lista_plana(GRUPOS_MAGNIFIC_IMAGEN)

# Modelos OpenAI/ChatGPT oficial (DALL-E retirado mayo 2026)
# Solo familia GPT Image actualmente activa en la API oficial.
GRUPOS_DALLE_IMAGEN = [
    ("── ChatGPT / GPT Image (OpenAI oficial) ──", sorted([
        "GPT Image 1.5", "GPT Image 2",
    ])),
]
MODELOS_DALLE_IMAGEN_FLAT = _lista_plana(GRUPOS_DALLE_IMAGEN)

# Modelos exclusivos de Midjourney
GRUPOS_MIDJOURNEY_IMAGEN = [
    ("── Midjourney ──", sorted([
        "Midjourney v8.1", "Midjourney v8", "Midjourney v7", "Midjourney v6.1", "Midjourney v6",
    ])),
    ("── Niji (Anime) ──", sorted([
        "Niji 7", "Niji 6", "Niji 5",
    ])),
]
MODELOS_MIDJOURNEY_IMAGEN_FLAT = _lista_plana(GRUPOS_MIDJOURNEY_IMAGEN)

# Modelos exclusivos de Ideogram / Recraft
GRUPOS_IDEOGRAM_IMAGEN = [
    ("── Ideogram / Recraft ──", sorted([
        "Ideogram v3", "Recraft v3",
    ])),
]
MODELOS_IDEOGRAM_IMAGEN_FLAT = _lista_plana(GRUPOS_IDEOGRAM_IMAGEN)

# Mapeo plataforma -> lista de modelos (para imagen)
MODELOS_POR_PLATAFORMA_IMAGEN = {
    "SeaArt / Tensor.Art":          MODELOS_IMAGEN_FLAT,
    "ComfyUI / A1111 / Forge":      MODELOS_IMAGEN_COMFYUI_FLAT,
    "Midjourney":                    MODELOS_MIDJOURNEY_IMAGEN_FLAT,
    "ChatGPT / GPT Image":           MODELOS_DALLE_IMAGEN_FLAT,
    "Ideogram / Recraft":            MODELOS_IDEOGRAM_IMAGEN_FLAT,
    "Magnific":                      MODELOS_MAGNIFIC_IMAGEN_FLAT,
}

# Mapeo plataforma -> lista de modelos (para vídeo)
MODELOS_POR_PLATAFORMA_VIDEO = {
    "SeaArt Video":                MODELOS_VIDEO_FLAT,
    "ComfyUI / A1111 / Forge":    MODELOS_VIDEO_COMFYUI_FLAT,
    "Kling AI":                    [m for m in MODELOS_VIDEO_FLAT if "Kling" in m or m.startswith("──")],
}

# ── Ratios ────────────────────────────────────────────────────────
RATIOS_IMAGEN = ["1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9", "21:9", "Libre"]
RATIOS_VIDEO  = ["1:1", "3:4", "4:3", "9:16", "16:9", "21:9"]

# ══════════════════════════════════════════════════════════════════
# ESTILOS DE IMAGEN (NUEVA ORGANIZACIÓN POR GRUPOS)
# ══════════════════════════════════════════════════════════════════
ESTILOS_GRUPOS = _load_json_data("estilos_grupos.json")

# Se genera la lista plana y se ordena TODO globalmente de la A a la Z
ESTILOS_IMAGEN = []
for grupo in ESTILOS_GRUPOS.values():
    ESTILOS_IMAGEN.extend(grupo)

ESTILOS_IMAGEN = sorted(ESTILOS_IMAGEN)

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
])

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
])

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
    "Realismo":      "cartoon, anime, illustration, painting, drawing, 3d render, CGI, unrealistic, plastic skin, doll-like",
    "Texto/Marcas":  "text, watermark, signature, logo, username, caption, title, subtitle, letters, numbers, copyright",
}

PRESET_COLORES = {
    "Anatomía":     ("#3a2020", "#5a3030"),
    "Texto/Marcas": ("#2a2a3a", "#3a3a5a"),
    "Baja Calidad": ("#3a3020", "#5a4a30"),
    "Realismo":     ("#203a2a", "#305a3a"),
    "Anime/2D":     ("#2a203a", "#3a305a"),
    "Censura":      ("#3a2030", "#5a3050"),
    "Fondos":       ("#203030", "#304a4a"),
    "Deformación":  ("#3a2a20", "#5a3a30"),
}

# ── Constantes IA ─────────────────────────────────────────────────
MAX_HIST_IA = 12

# ══════════════════════════════════════════════════════════════════
# ESTILOS POR FAMILIA (toggle "Estilo" en el panel del modelo)
# ══════════════════════════════════════════════════════════════════
# Cada familia define sus estilos. "Auto" significa que el LLM decide
# según la idea. El resto fuerza una categoría que se inyecta como hint
# en la plantilla específica de cada familia.
ESTILOS_POR_FAMILIA = {
    "z_image": [
        "Auto", "Photoreal", "Creative", "Fantasy", "SciFi",
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
}

# Modelos de la familia FLUX (para el toggle "Estilo"). Se deriva del grupo
# "Familia FLUX" de GRUPOS_IMAGEN para no mantener una lista aparte; incluye
# los que no llevan 'flux' en el nombre (p. ej. Midjourney Mimic Neo).
_MODELOS_FLUX = {m for cab, ms in GRUPOS_IMAGEN if "flux" in cab.lower() for m in ms}


def detectar_familia(modelo_nombre: str) -> str | None:
    """Detecta la familia de un modelo a partir de su nombre.

    Devuelve la clave de familia (ej. "z_image", "gpt_image") o None
    si no se detecta. Usada por el combo "Estilo" para repoblar
    opciones cuando el usuario cambia de modelo.
    """
    if not modelo_nombre:
        return None
    n = modelo_nombre.lower()
    if "z-image" in n or "z image" in n or "z_image" in n:
        return "z_image"
    if "gpt image" in n or "gpt-image" in n:
        return "gpt_image"
    if "nano banana" in n or "nano-banana" in n or "nano_banana" in n:
        return "nano_banana"
    if modelo_nombre in _MODELOS_FLUX or "flux" in n:
        return "flux"
    return None


# ══════════════════════════════════════════════════════════════════
# PLATAFORMAS
# ══════════════════════════════════════════════════════════════════
PLATAFORMAS_IMAGEN = {
    "SeaArt / Tensor.Art":        "sd",
    "ComfyUI / A1111 / Forge":    "sd",
    "Midjourney":                  "natural",
    "ChatGPT / GPT Image":         "natural",
    "Ideogram / Recraft":          "natural",
    "Magnific":                    "natural",
}

PLATAFORMAS_VIDEO = {
    "SeaArt Video":     "sd",
    "ComfyUI / A1111 / Forge": "sd",
    "Kling AI":         "natural",
    "Pika / Luma":      "natural",
    "Runway Gen":       "natural",
    "Pixverse.ai":      "natural",
    "Sora / Veo":       "natural",
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
])

# ── Motores por plataforma ────────────────────────────
MOTORES_VIDEO = {
    "SeaArt Video": MODELOS_VIDEO_FLAT,
    "ComfyUI / A1111 / Forge": MODELOS_VIDEO_COMFYUI_FLAT,
    "Kling AI": ["Kling 01 Video Model", "Kling 2.6", "Kling 3.0", "Kling 3.0 Omni"],
    "Pika / Luma": [],
    "Runway Gen": [],
    "Pixverse.ai": [],
    "Sora / Veo": ["Sora2 Video", "Veo 3.1", "Gemini Omni"],
}

MOTORES_AUDIO = {
    "Suno": ["Suno v5.5", "Suno v5", "Suno v4.5", "Suno v4.5-All (Free)", "Suno v4"],
    "Udio": ["Udio v4", "Udio v1.5"],
    "SeaArt Audio": ["Minimax Music 2.6", "Minimax Music 2.5", "SeaArt MusicGo"],
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
    "ComfyUI / A1111 / Forge": 75,
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
    "Sora / Veo": 75,
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
        "modelos": ["Kling 3.0", "Kling 3.0 Omni", "SeaArt Ultra Pro", "Sora2 Video", "Wan 2.6"],
        "positive_base": "{duracion}. {encuadre_camara}, {sujeto} {accion}, {entorno}, {iluminacion}, {movimiento_camara}, {atmosfera}. Audio: {audio_desc}.",
        "negative_base": "worst quality, static shot, no movement, blurry, low resolution, deformed, morphing, flickering",
    },
}

# ── Autor ─────────────────────────────────────────────────────────
AUTHOR = {
    "nombre":    "Gustaafvito",
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
    return _get_dataset("MODEL_SPECS").get(motor_name, None)

def get_image_model_specs(modelo_name):
    return _get_dataset("MODEL_SPECS_IMAGEN").get(modelo_name, None)

def get_audio_model_specs(modelo_name):
    return _get_dataset("MODEL_SPECS_AUDIO").get(modelo_name, None)

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
