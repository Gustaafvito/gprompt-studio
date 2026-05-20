"""
G-Prompt Studio v1.0 — Configuración y constantes.
Modelos, estilos, ratios, presets de negativos, colores UI.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Versión ───────────────────────────────────────────────────────
VERSION = "1.0.9"
PUBLIC_VERSION = "1.0"
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
    "preferencias":  CARPETA_APP / "preferencias.json",
    "estrellas":     CARPETA_APP / "estrellas.json",
    "keys":          CARPETA_APP / "keys.json",
    "active_provider": CARPETA_APP / "active_provider.txt",
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
        "Mix Max Cinematic Realism",
        "FLUX.1 [dev]",
        "FLUX.1-dev-fp8",
        "FLUX.1",
        "FLUX.1D UltraReal",
        "Flux-dev",
        "MASTER FLUX (LoRA merged with flux1-dev fp16)",
    ])),
    ("── Familia Z-Image ──", sorted([
        "Z Image Turbo",
        "Z-Image-Base-Realistic",
    ])),
    ("── GPT Image (OpenAI en SeaArt) ──", sorted([
        "GPT Image 2",
    ])),
    ("── Nano Banana ──", sorted([
        "Nano Banana Pro Image", "Nano Banana 2",
    ])),
    ("── Realismo SD ──", sorted([
        "Alchemist Mix (Illustrious Realism)",
        "CyberRealistic",
        "Deliberate",
        "DreamShaper",
        "FantasticChix-HR",
        "Illustrious Realism by Klaabu",
        "Juggernaut XL",
        "MajicMIX Realistic v6",
        "NiwaStyle – DreamReal SR (Illustrious)",
        "PornRealistic",
        "Real Dream SDXL",
        "Realistic Vision V6.0",
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
        "Suno v5", "Suno v4.5", "Suno v4",
    ])),
    ("── SeaArt Audio ──", sorted([
        "Minimax Music 2.5", "SeaArt MusicGo",
    ])),
]

def _lista_plana(grupos):
    r = []
    for g, ms in grupos:
        r.append(g)
        r.extend(ms)
    return r

MODELOS_VIDEO_FLAT  = _lista_plana(GRUPOS_VIDEO)
MODELOS_IMAGEN_FLAT = _lista_plana(GRUPOS_IMAGEN)
MODELOS_AUDIO_FLAT  = _lista_plana(GRUPOS_AUDIO)

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
        "GPT Image 1", "GPT Image 1 mini", "GPT Image 1.5", "GPT Image 2",
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
ESTILOS_GRUPOS = {
    "📸 Fotografía": [
        "Fotografía Realista", "Retrato / Portrait", "Paisaje / Landscape",
        "Wildlife / Naturaleza", "Macro / Close-up", "Underwater", "Drone / Aéreo",
        "Editorial Fashion", "Street Photography", "Polaroid / Vintage Photo",
        "Disposable Camera", "Analog Film / 35mm", "Cross-processed",
        "Studio Shot", "Studio Headshot", "Product Photography", "Foodie", "Phone Photo",
        "Low-key Cinematic", "Cinematic Still", "Documental",
        # Añadidos v1.1
        "HDR Photography", "Long Exposure", "Fisheye / Wide-angle",
        "Black & White Photography", "Lifestyle / Candid", "Tilt-shift",
        "Bokeh Portrait", "Golden Hour", "Blue Hour",
    ],
    "🎨 Arte": [
        "Óleo / Oil Painting", "Acrílico", "Watercolor", "Charcoal / Carboncillo",
        "Sumi-e / Tinta china", "Ukiyo-e", "Realismo Mágico", "Surreal / Dreamlike",
        "Pastel Painting", "Fauvist Painting", "Pointillism", "Renaissance",
        "Baroque", "Art Nouveau", "Art Deco", "Bauhaus", "Pop Art",
        "Fine Art", "Concept Art", "Hand Drawn", "Coloring Book",
        "Linocut", "Risograph", "Screenprint", "Collage",
        "Pencil / Sketch", "Ink / Lineart", "Pen & Ink",
        "Oil Pastel", "Colored Pencil", "Wax Crayon",
        # Añadidos v1.1
        "Impressionism", "Cubism", "Abstract Expressionism", "Minimalism",
        "Street Art / Graffiti", "Mural", "Mosaic", "Stained Glass / Vitral",
        "Gouache", "Sketchbook",
    ],
    "💥 Cómic & Manga": [
        "Comic Book", "Retro Comic", "Western Comic", "Marvel/DC Style",
        "Manga (Black & White)", "Manga Color", "Shonen", "Shojo", "Seinen",
        "Webtoon / Manhwa", "Comic Strip", "Graphic Novel",
        "Anime / Ilustración", "Anime 90s Retro", "Anime Classic",
        "Studio Ghibli", "Chibi / Kawaii", "Cartoon",
        "Cartoon Fun", "Whimsy Anime",
        "Speech Bubbles", "Halftone Print", "Inked Style",
    ],
    "🚀 Digital & 3D": [
        "3D Render", "Pixar / Disney 3D", "Character 3D", "Glossy 3D Icon",
        "Plushy / Stuffed Toy", "Vinyl Toy", "Amigurumi 3D", "Felt 3D",
        "Squishy 3D", "Claytoon / Plasticine", "Origami", "Stop Motion",
        "Cyberpunk / Neon", "Sci-Fi", "Retro / Synthwave", "Vaporwave / Aesthetic",
        "Isometric", "Low Poly", "Pixel Art", "Voxel Art",
        "Holography", "Iridescent / Pearlescent", "Chrome / Metallic",
        "Glass / Translucent", "Liquid / Fluid",
        # Añadidos v1.1
        "Octane Render", "Unreal Engine 5", "Blender Stylized",
        "Toy Photography", "Claymation", "Bioluminescent",
        "Liquid Metal", "Holographic Foil",
    ],
    "🎬 Cine & TV": [
        "Cinematic Lighting", "Film Noir", "Movie Poster", "Trailer Style",
        "Music Video", "Videoclip", "70s Vibe", "80s Couture",
        "Found Footage", "VHS Aesthetic", "Old Money Still",
        "Cinematic Pastel", "Vibrant Film",
        # Añadidos v1.1 — directores y estéticas reconocibles
        "Wes Anderson Style", "David Fincher Style", "Christopher Nolan Style",
        "A24 Aesthetic", "Studio Ghibli Cinematography",
        "Tarantino Style", "Denis Villeneuve Style",
    ],
    "🎯 Diseño Gráfico": [
        "Minimalista", "Bold Poster",
        "Neo Memphis", "Paper Noise", "Glitch Collage", "Halftone",
        "Typography Heavy", "Bold Typo", "Vector / Flat",
        "Vintage Vector", "Simple Vector", "Indie Poster",
        "Sticker Icon", "Pixel Icon", "3D Icon",
        # Añadidos v1.1
        "Swiss Design", "Brutalist Web", "Editorial Layout",
    ],
    "🌑 Oscuro & Fantasy": [
        "Fantasy Épica", "Dark Fantasy", "Gothic / Oscuro", "Tarot / Místico",
        "Terror / Horror", "Halloween", "Cursed",
        "Dark Concept", "Lucid Sci-Fi",
        "Steampunk", "Foggy", "Surreal Fashion",
        # Añadidos v1.1
        "Cosmic Horror / Lovecraftian", "Dieselpunk", "Biopunk",
        "Apocalyptic / Wasteland",
    ],
    "✨ Estética & Mood": [
        "Pastel Aesthetic", "Coquette",
        "Peachy", "Trendy Mocha", "Warm Cozy", "Mediterranean",
        "Italian Vibes", "Cozy Coffee Shop", "Botanical Folk", "Floral Elegance",
        "Sparkling", "Aetherial", "Dreamy Mini",
        # Añadidos v1.1 — estéticas trending 2024-2026
        "Cottagecore", "Dark Academia", "Light Academia", "Y2K Aesthetic",
        "Bohemian", "Maximalism", "Brutalism", "Nordic / Scandinavian",
        "Japandi", "Wabi-sabi",
    ],
    "🎭 Editorial & Fashion": [
        "Vogue Editorial", "Runway Fashion", "High Fashion", "Editorial Glow",
        "Editorial Portrait", "Cover Art", "Avant Garde", "Stylized Cyber",
        "Symbolic Editorial", "Neon Editorial",
        # Añadidos v1.1
        "Haute Couture", "Streetwear Lookbook", "Y2K Fashion",
        "Vintage Glam", "Punk Editorial",
    ],
    "👶 Infantil & Juguete": [
        "Children's Story", "Childbook Illustration", "Storybook",
        "Sunset Cartoon", "Fresh Cartoon", "Cute Grainy", "Kawaii",
        "Mini World", "Squishy", "Plushies", "Adorable", "Cute Cartoon",
        # Añadidos v1.1
        "Crayon Drawing", "Felt Craft", "Paper Cut-out",
    ],
    "🏗 Arquitectura & Espacios": [
        # Grupo renombrado de "Otros estilos" — ahora coherente
        "Architecture", "Interior Design", "Eclectic Decor",
        "Brutalist Architecture", "Mid-century Modern", "Art Deco Interior",
        "Industrial Loft", "Tropical Modern", "Japanese Tea House",
    ],
    "📦 Mockups & Producto": [
        # Grupo nuevo — extraído de "Otros estilos"
        "Mockup / Phone Photo", "Tshirt Mockup", "Laptop Mockup",
        "Coffee Shop Mockup", "Branding in the Wild",
        "Packaging Design", "Book Cover Mockup",
    ],
    "🏛 Otros estilos": [
        "Pinup Vintage", "Space / Cosmic",
        # Añadidos v1.1
        "Tattoo Old School", "Tattoo Neo Traditional",
        "Manuscript / Codex", "Cartography / Maps",
        "Religious Iconography",
    ],
}

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
    "Parallax", "Pull Back / Reveal", "Steadicam", "Time-Lapse",
    "Tracking Shot", "Whip Pan", "Zoom Burst",
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
    "Infographic Video", "Typography Animation",
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
    "Ambient", "Blues", "Cinematográfico", "Clásica", "Country",
    "Electrónica", "Flamenco", "Folk", "Funk", "Hip-hop", 
    "Indie", "Jazz", "Lo-fi", "Metal", "Música Videojuegos", 
    "Pop", "R&B", "Reggaeton", "Rock", "Synthwave",
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
# ESPECIFICACIONES DE MODELOS DE VÍDEO
# ══════════════════════════════════════════════════════════════════
MODEL_SPECS = {
    "Kling 3.0": {
        "nota": 4.5,
        "has_negative": True,
        "has_audio": True,
        "audio_desc": "Lip-sync, diálogos, SFX, música, ambiente",
        "duraciones": ["5s", "10s", "15s"],
        "ratios": ["9:16", "1:1", "16:9"],
        "max_chars": 2500,
        "modos_gen": ["Estándar", "Calidad", "Ultra HD", "Profesional"],
        "best_for": "DIRECTOR DE CINE. Prompts negativos. Multi-toma, secuencias narrativas, coherencia brutal de personajes. Audio: lip-sync, diálogos, SFX, música.",
        "prompt_formula": "Subject + action → setting → time → camera → motion → mood → audio (opcional)",
        "prompt_ejemplo": "10-15 seconds. Slow push-in on subject's face. Subtle breathing, soft blink. Golden hour rim light, shallow depth of field. Quiet city ambience.",
        "limitaciones": "Prompts muy cargados pueden fallar; simplificar cámara a un movimiento",
    },
    "Kling 3.0 Omni": {
        "nota": 4.5,
        "has_negative": True,
        "has_audio": True,
        "audio_desc": "Lip-sync avanzado, SFX, voz consistente entre clips",
        "duraciones": ["5s", "10s", "15s"],
        "ratios": ["9:16", "1:1", "16:9"],
        "max_chars": 2500,
        "modos_gen": ["Estándar", "Calidad", "Ultra HD", "Profesional"],
        "best_for": "Continuidad personaje/voz. Referencia multi-imagen. Secuencias coherentes. Lip-sync avanzado, SFX, voz consistente entre clips",
        "prompt_formula": "Subject + action → setting → camera → motion → mood → audio",
        "prompt_ejemplo": "12s. Wide establishing shot, slow pan left. Light rain, wet reflections, neon signs. Distant traffic ambience.",
        "limitaciones": "Demasiadas referencias conflictivas causan inconsistencia",
    },
    "Kling 01 Video Model": {
        "nota": 4.3,
        "has_negative": False,
        "has_audio": False,
        "audio_desc": "",
        "duraciones": ["3s", "5s", "10s"],
        "ratios": ["9:16", "1:1", "16:9"],
        "max_chars": 2500,
        "modos_gen": ["Estándar", "Calidad"],
        "best_for": "Creador básico y estable. Genera clips 3-10s desde texto o imagen. Punto fuerte: imagen inicio+fin para transición perfecta.",
        "prompt_formula": "Scene description + subject + action + camera movement",
        "prompt_ejemplo": "A cyberpunk city at dusk with neon lights reflecting on wet pavement, cinematic dolly shot.",
        "limitaciones": "Sin audio nativo, máximo 10 segundos",
    },
    "Kling 2.6": {
        "nota": 3.1,
        "has_negative": False,
        "has_audio": True,
        "audio_desc": "Voz nativa, lip-sync, monólogos, diálogos, música, SFX ambientales",
        "duraciones": ["5s", "10s", "15s"],
        "ratios": ["16:9", "1:1", "9:16"],
        "max_chars": 2500,
        "modos_gen": ["Estándar", "Calidad"],
        "best_for": "ESPECIALISTA EN SONIDO. Personaje hablando a cámara con sincronización labial. Diálogos, vlogs con voz, performances musicales",
        "prompt_formula": "Scene description + subject + movement + [Character, Emotion] says: 'dialogue' + audio description",
        "prompt_ejemplo": "[Ana, excited] says: 'Welcome to my channel!' Bright studio, warm key light, slight camera push-in. Upbeat pop BGM.",
        "limitaciones": "Sin prompt negativo, calidad visual inferior a Kling 3.0",
    },
    "Seedance 1.5 PRO": {
        "nota": 4.3,
        "has_negative": True,
        "has_audio": True,
        "audio_desc": "Síntesis audio+video conjunta: BGM, SFX, doblaje adaptado sin postproducción",
        "duraciones": ["5s", "10s", "12s"],
        "ratios": ["16:9", "9:16", "4:3", "3:4", "1:1", "21:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar", "Calidad", "Ultra HD", "Profesional"],
        "best_for": "Audio nativo integrado (BGM+SFX+doblaje). Text/Image-to-Video. 480p-4K. Multi-ratios. Realismo cine, ads, naturaleza",
        "prompt_formula": "Scene + subject + action + camera + lighting + audio description",
        "prompt_ejemplo": "Drone shot over crashing ocean coastline during storm. Audio: roaring waves, howling wind, distant thunder.",
        "limitaciones": "Máx 5000 letras. Coste energía variable 230-3840pts",
    },
    "Seedance 2.0": {
        "nota": 4.2,
        "has_negative": False,
        "has_audio": True,
        "audio_desc": "Audio nativo: ambiental, SFX, señales de audio alineadas con prompt",
        "duraciones": ["4s", "5s", "10s", "15s"],
        "ratios": ["3:4", "9:16", "1:1", "4:3", "16:9"],
        "max_chars": 5000,
        "modos_gen": ["Estándar", "Calidad"],
        "best_for": "DIRECTOR DE CINE. Multi-shot storytelling. Lenguaje cámara+ritmo+iluminación. Audio nativo integrado. Prompts hasta 5000 chars.",
        "prompt_formula": "Shot 1: [wide/plano/cámara]. Shot 2: [medium/acción]. Shot 3: [close-up/detail]. Audio: [SFX, ambiente, música]",
        "prompt_ejemplo": "Shot 1: Wide establishing shot, minimalist studio. Shot 2: Medium shot, product on pedestal. Shot 3: Close-up on label. Audio: soft room tone, subtle whoosh.",
        "limitaciones": "NO caras reales (usar avatares IA o anime). Sin prompt negativo. Coste energía 540-4275pts",
    },
    "Seedance 2.0 Fast": {
        "nota": 3.0,
        "has_negative": False,
        "has_audio": False,
        "audio_desc": "",
        "duraciones": ["8s", "10s", "15s"],
        "ratios": ["3:4", "9:16", "1:1", "4:3", "16:9"],
        "max_chars": 5000,
        "modos_gen": ["Estándar", "Calidad"],
        "best_for": "Velocidad y VLOGs. Image/Text/Video-ref. 8-15s. Prompts hasta 5000 letras.",
        "prompt_formula": "Natural description of scene + subject + action + camera",
        "prompt_ejemplo": "Young woman walks through colorful Tokyo streets at night, handheld camera following, neon reflections.",
        "limitaciones": "SIN audio, SIN negative, SIN Ultra HD/Pro.",
    },
    "Nano Banana Pro Video": {
        "nota": 3.3,
        "has_negative": True,
        "has_audio": False,
        "audio_desc": "Subir audio manual (MP3/WAV/AAC/M4A, 3-30s, <15MB)",
        "duraciones": ["5s", "10s", "15s"],
        "ratios": ["9:16", "16:9", "1:1", "4:3", "3:4"],
        "max_chars": 2000,
        "modos_gen": ["Estándar", "Calidad", "Ultra HD", "Profesional"],
        "best_for": "Gemini 3. Alta fidelidad profesional. Image-to-Video 2K/4K. Text-to-Video 6s@720p/10s@1080p. Control cámara avanzado.",
        "prompt_formula": "Subject + action + camera movement + style + lighting",
        "prompt_ejemplo": "Hyper-realistic racing car drifting around wet track corner, fixed camera, smoke billowing from tires.",
        "limitaciones": "Clips reales 6-10s (UI muestra 15s), manos ocasionalmente inconsistentes",
    },
    "Nano Banana Video": {
        "nota": 4.5,
        "has_negative": False,
        "has_audio": True,
        "audio_desc": "Generación automática de SFX y BGM integrados",
        "duraciones": ["5s", "10s"],
        "ratios": ["9:16", "16:9", "1:1"],
        "max_chars": 1500,
        "modos_gen": ["Estándar"],
        "best_for": "Modelo estándar rápido. Image/Text-to-Video 6-10s. Estilos: cine, anime, sci-fi, Disney. Control cámara en prompt.",
        "prompt_formula": "Subject + action + camera control + style description",
        "prompt_ejemplo": "Majestic lion in jungle, paw moves to adjust camera, jungle background sways gently, cinematic quality.",
        "limitaciones": "Máximo 10 segundos real (6-10s), sin prompt negativo",
    },
    # ── SeaArt Oficiales Video ───────────────────────────────
    "SeaArt Film Video": {
        "nota": 4.5,
        "has_negative": False,
        "has_audio": True,
        "audio_desc": "SFX + BGM integrados (toggles Efecto de sonido / Agregar BGM)",
        "duraciones": ["5s", "10s"],
        "ratios": ["9:16", "16:9", "1:1"],
        "max_chars": 2400,
        "modos_gen": ["Estándar", "Calidad"],
        "best_for": "El modelo de vídeo más usado de SeaArt (10.4M usos). Cinematográfico, HQ, fotogramas. Sujetos múltiples, magia de sugerencia. Image-to-Video y Text-to-Video.",
        "prompt_formula": "Subject + action + camera + lighting + style. Prompts descriptivos con magia de sugerencia.",
        "prompt_ejemplo": "A woman in a flowing white dress walks through golden wheat fields at sunset, cinematic slow motion, warm golden hour light, shallow DOF.",
        "limitaciones": "Sin prompt negativo. Máx 10s. Coste ~480-2400 energía.",
    },
    "SeaArt Ultra Pro": {
        "nota": 4.6,
        "has_negative": True,
        "has_audio": True,
        "audio_desc": "SFX + BGM integrados + slider de Similitud (0-1)",
        "duraciones": ["5s", "10s", "15s"],
        "ratios": ["9:16", "16:9", "1:1"],
        "max_chars": 3000,
        "modos_gen": ["Estándar", "Calidad", "Ultra HD", "Profesional"],
        "best_for": "Versión Pro del Ultra. 4.4M usos. 15s, calidad profesional. Sujetos múltiples, magia de sugerencia, prompt negativo. Ideal para producción seria.",
        "prompt_formula": "Subject + action → setting → camera → motion → mood → audio. Similar a Kling 3.0 pero con slider de similitud.",
        "prompt_ejemplo": "Epic drone shot over a misty mountain valley at dawn, volumetric god rays piercing through clouds, cinematic 4K, slow crane movement.",
        "limitaciones": "Coste alto (~600-3000 energía). Similitud 0.5 por defecto.",
    },
    # ── Otros Motores ────────────────────────────────────────
    "Wan 2.6": {
        "nota": 4.3,
        "has_negative": True,
        "has_audio": False,
        "audio_desc": "Subir audio manual (MP3/WAV/AAC/M4A, 3-30s, <15MB)",
        "duraciones": ["5s", "10s", "15s"],
        "ratios": ["9:16", "16:9", "1:1"],
        "max_chars": 1500,
        "modos_gen": ["Estándar", "Calidad", "Ultra HD", "Profesional"],
        "best_for": "Motor Wan (ByteDance). 88K usos. Image-to-Video con prompt negativo. Magia de sugerencia. Semilla fija disponible.",
        "prompt_formula": "Subject + action + camera movement + style + lighting. Prompts descriptivos.",
        "prompt_ejemplo": "A samurai drawing his sword in a bamboo forest, slow motion, dramatic backlight, leaves falling, cinematic atmosphere.",
        "limitaciones": "Sin audio nativo (subida manual). Coste ~1080 energía.",
    },
    "Sora2 Video": {
        "nota": 4.8,
        "has_negative": True,
        "has_audio": True,
        "audio_desc": "Audio nativo integrado (diálogos, música, SFX automáticos)",
        "duraciones": ["5s", "10s", "15s", "20s"],
        "ratios": ["9:16", "16:9", "1:1", "3:4"],
        "max_chars": 2000,
        "modos_gen": ["Estándar", "Calidad", "Ultra HD", "Profesional"],
        "best_for": "CONSISTENCIA DE PERSONAJES superior. Manejo excepcional de física de materiales (ropa ondeando, colisiones, telas). API de referencias para personajes consistentes. Audio nativo con diálogos sincronizados. Timing preciso de acciones.",
        "prompt_formula": "BLOQUES SEPARADOS: [Scene Description] + Cinematography: + Physics & Motion: + Dialogue: + Background Sound:. Descriptivo con peso y velocidad de movimientos.",
        "prompt_ejemplo": "A weathered blacksmith hammers molten metal in his forge. The sparks fly in precise timing with each strike, ember particles drifting slowly in the cool air.\n\nCinematography:\n- Camera: Medium close-up, slow push-in with parallax effect on the sparks\n- Lighting: Warm orange glow from the forge, deep shadows on face, dramatic contrast\n\nPhysics & Motion:\nThe heavy leather apron moves with realistic weight as he swings the hammer. Sweat droplets fly off with each impact, cloth physics perfectly synced to movement. Metal rings with each collision.\n\nDialogue:\n- Blacksmith: \"This blade will outlive us all.\"\n\nBackground Sound:\nMetallic clang of hammer striking steel, crackling fire, heavy breathing, distant town ambiance, no background music.",
        "prompt_ejemplo_simple": "A lone astronaut floating above Earth, helmet reflecting blue planet, slow rotation, stars in background, epic cinematic scale.",
        "prompt_tips": [
            "BLOQUES EXPLÍCITOS: Usa headers como 'Cinematography:', 'Physics & Motion:', 'Dialogue:', 'Background Sound:'.",
            "CONSISTENCIA DE PERSONAJES: Usa la API de referencias para mantener same character across shots.",
            "FÍSICA DE MATERIALES: Describe peso, velocidad, sincronización. 'La tela se mueve con peso realista', 'el agua salpica con física natural'.",
            "TIMING PRECISO: Sincroniza acciones: 'los chispas vuelan en timing preciso con cada golpe'.",
            "DIÁLOGOS: Especifica líneas exactas con nombre del personaje: '- Personaje: \"Línea\"'.",
            "BACKGROUND SOUND: Incluye foley específico: 'pasos sobre grava', 'lluvia golpeando', 'sin música de fondo'.",
            "PROFUNDIDAD: Describe capas de audio: foreground (diálogos), midground (SFX cercanos), background (ambiente lejano).",
            "MENCIONA LENTE: 'lente de 35mm', 'cámara en mano', 'drone' para control de estilo visual.",
            "NO USES TAGS COMA-SEPARADOS: Escribe en párrafos descriptivos estructurados.",
            "MASSIVE PROMPT: Sora 2 acepta prompts largos y detallados. No escatimes en descripción.",
        ],
        "estructura_bloques": ["Scene Description", "Cinematography", "Lighting & Mood", "Physics & Motion", "Dialogue", "Background Sound"],
        "estructura_camara": ["medium close-up", "slow push-in", "tracking shot", "dolly zoom", "crane up", "handheld", "stabilized", "parallax effect", "rack focus", "slow motion"],
        "estructura_audio": ["dialogue", "background music", "foley", "ambient", "silence", "SFX", "voiceover"],
        "limitaciones": "Coste más alto que otros. Requiere referencia de personaje para consistencia. Duración máxima ~20s.",
    },
    "Veo 3.1": {
        "nota": 4.7,
        "has_negative": False,
        "has_audio": True,
        "audio_desc": "Audio nativo (música ambiental, SFX, diálogos)",
        "duraciones": ["4s", "6s", "8s", "12s"],
        "ratios": ["9:16", "16:9", "1:1", "4:3"],
        "max_chars": 1500,
        "modos_gen": ["720p", "1080p", "4K"],
        "best_for": "ÓPTICA Y LENTE cinematográfica avanzada. Consistencia de fluidos, reflejos, texturas (fuego, cristales, espejos, agua). Iluminación fotorrealista. Mejor comprensión de lenguaje natural (no tan rígido como versiones anteriores).",
        "prompt_formula": "FOCALIZACIÓN PROGRESIVA: [CÁMARA/PLANO] + [SUJETO EN ACCIÓN] + [ILUMINACIÓN/ÓPTICA] + [TEXTURAS/MATERIALES] + [AUDIO]. Front-loading: lo más importante al principio.",
        "prompt_ejemplo": "Medium close-up filmed with a 35mm cinematic lens, shallow depth of field. An artisan with weathered hands shapes molten blown glass in his dark workshop. The scene features dramatic lighting coming solely from the incandescent glass glow, creating deep shadows and orange glints on his face. Highlights include subtle rising smoke, imperfections in the molten glass, and sweat on the skin. Audio: the crackle of fire, the hiss of cooling glass, and a deep steady breathing.",
        "prompt_ejemplo_simple": "A person walking through a foggy forest path, mysterious atmosphere, cinematic lighting, 1080p.",
        "prompt_tips": [
            "FRONT-LOADING: Tipo de plano y sujeto al principio. Máximo 3-5 frases.",
            "ÓPTICA DE LENTE: Especifica tipo de lente (35mm cinematográfico, 50mm, macro). Añade efectos: bokeh, chromatic aberration, lens flare.",
            "CÁMARA EN UN FRASE INDEPENDIENTE: 'La cámara hace un push-in lento hacia su rostro' al final.",
            "MATERIALIDAD: Describe texturas difíciles: humo, fuego, líquidos reflectantes, piel, metal, cristal, espejo.",
            "CONSISTENCIA LUMÍNICA: Fuente de luz principal clara: 'luz cenital', 'contraluz', 'neón reflejado en suelo mojado'.",
            "FLUIDOS Y REFLEJOS: Especializado en física de fluidos, reflejos realistas (fuego en cristal, agua en espejo).",
            "TEXTURAS ÓPTICAS: 'destellos anaranjados', 'sombras profundas', 'imperfecciones del material'.",
            "AUDIO INTEGRADO: Incluye descripción de sonido: 'graznido de gaviotas', 'olas rompiendo', 'respiración profunda'.",
            "ESCENA ATÓMICA: Una sola acción principal por toma. No sobrecargues.",
            "LENGUAJE FLUIDO: Ya no necesitas ser ultra-estructurado. Describe con frases naturales.",
            "ESTILO DE CÁMARA: Selecciona de menú: 'Lente Cinematográfica 35mm', 'Cámara en mano (documental)', 'Drone cenital', 'Macro detalle'.",
            "NO TAGS COMA-SEPARADOS: Frases descriptivas fluidas pero directas.",
        ],
        "estructura_camara": ["medium close-up", "close-up", "wide shot", "extreme close-up", "over the shoulder", "pov shot", "drone shot", "aerial view", "macro shot"],
        "estructura_lente": ["35mm cinematic lens", "50mm lens", "85mm portrait lens", "wide-angle lens", "macro lens", "anamorphic lens", "handheld camera", "steadicam", "gimbal stabilized"],
        "estructura_fisica": ["smoke rising", "fire glow", "water reflections", "glass imperfections", "metal shine", "fabric movement", "particle dispersion", "light refraction", "shadow casting"],
        "estructura_audio": ["ambient noise", "dialogue", "foley", "silence", "music", "SFX", "weather sounds", "footsteps", "breathing"],
        "limitaciones": "Solo 2 ratios básicos (9:16, 16:9). Máx ~12s. Sin negative prompt. Mejor para cinematografía que para acciones complejas.",
    },
    "Gemini Omni": {
        "nota": 4.9,
        "has_negative": False,
        "has_audio": True,
        "audio_desc": "Audio realista (música ambiental, SFX, voz sincronizada)",
        "duraciones": ["~10s", "~20s"],
        "ratios": ["9:16", "16:9", "1:1", "4:3"],
        "max_chars": 2000,
        "modos_gen": ["Text-to-Video", "Image-to-Video", "Video-to-Video", "Omni Motion"],
        "best_for": "DIRECTOR CREATIVO CON INTELIGENCIA FÍSICA. Modelo de MUNDO que entiende causa-efecto, dinámicas de fluidos, gravedad, materiales. Edición conversacional iterativa. Cámara cinematográfica avanzada. Renderiza texto animado. Referencia multimodal (imagen+vídeo+audio+texto).",
        "prompt_formula": "5 BLOQUES CLAVE: {Sujeto/Acción} + {Entorno} + {Física/Dinámica} + {Cámara} + {Estilo/Iluminación}. Narrativa técnica, no lista de keywords. Enfoca en causa-efecto.",
        "prompt_ejemplo": "Close-up of a coffee cup dripping in slow motion on a rustic wooden table in a dim café. The liquid splashes recreating hyperrealistic fluid dynamics and emits illuminated steam. Cinematic golden hour side lighting with lens flare. Dolly push-in, grounded cinematic feel.",
        "prompt_ejemplo_estructura": {
            "sujeto": "a coffee cup dripping in slow motion",
            "entorno": "a rustic wooden table in a dim café",
            "fisica": "The liquid splashes recreating hyperrealistic fluid dynamics and emits illuminated steam",
            "camara": "Close-up, slow motion, dolly push-in",
            "estilo": "Cinematic, golden hour side lighting, lens flare, grounded feel"
        },
        "prompt_tips": [
            "5 BLOQUES OBLIGATORIOS: Sujeto + Entorno + Física + Cámara + Estilo. Todos deben estar presentes.",
            "NARRATIVA TÉCNICA: Escribe como si narraras una escena de película, no como lista de tags.",
            "FÍSICA/DINÁMICA ES CLAVE: Omni entiende causa-efecto. Describe qué pasa 'cuando' ocurre una acción.",
            "FLUIDOS Y MATERIALES: 'El líquido salpica creando gotas', 'el humo se dispersa', 'la tela ondea con viento'.",
            "EVITA SOBRESPECIFICAR: No listes cada objeto. Describe atmósfera y Omni infiere los detalles.",
            "CÁMARA: wide-angle, medium shot, close-up, dolly zoom, push-in, punch in, oners (toma continua).",
            "ILUMINACIÓN: Fuente + efecto + temperatura. 'Warm golden light from the left', 'ethereal backlight'.",
            "EDICIÓN ITERATIVA: Pide cambios específicos sin reescribir todo: 'Change the butterfly to a bee'.",
            "OMNI MOTION: Para movimiento fluido, describe keyframes de acción: 'starting from X, transitioning to Y'.",
            "CONOCIMIENTO DEL MUNDO: No explains contexto histórico/científico. Omni lo sabe. Solo describe tu visión.",
            "TEXT EN VÍDEO: Especifica tipo de letra, posición, animación, exposición.",
            "REFERENCIAS MULTIMODAL: Combina imagen de referencia + prompt para control de estilo.",
            "NO USES MIDJOURNEY STYLE: No '(word:1.5)'. Escribe en prosa narrativa técnica.",
        ],
        "estructura_camara": ["close-up", "medium shot", "wide shot", "extreme close-up", "over the shoulder", "pov", "dolly push-in", "dolly zoom", "crane up/down", "tracking shot", "steadicam", "oner (continuous shot)", "slow motion", "fast motion", "push-in", "pull-out", "punch in", "rack focus"],
        "estructura_fisica": ["fluid dynamics", "gravity simulation", "particle systems", "smoke dispersion", "cloth physics", "water splashes", "explosion debris", "elastic deformation", "bounce physics", "light refraction", "shadow casting", "reflection"],
        "limitaciones": "Acceso vía Google AI Studio. Requiere suscripción. Sin negative prompt nativo.",
    },
}

# ══════════════════════════════════════════════════════════════════
# ESPECIFICACIONES DE MODELOS DE IMAGEN
# ══════════════════════════════════════════════════════════════════
MODEL_SPECS_IMAGEN = {
    # ── SeaArt Oficiales ─────────────────────────────────────
    "SeaArt Infinity": {
        "nota": 4.7,
        "has_negative": False,
        "is_natural": True,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 8,
        "best_for": "Modelo oficial all-in-one de SeaArt. 144.5M usos. Versátil para cualquier estilo. Magia de sugerencia integrada. Control con sampler/steps/CFG.",
        "prompt_formula": "Lenguaje natural descriptivo o tags. Modelo versátil que acepta ambos formatos.",
        "prompt_ejemplo": "A young woman in a sunlit meadow, golden hour, soft bokeh, cinematic composition, professional photography",
        "sampler_recomendado": "Euler",
        "pasos": 30,
        "cfg": 3.5,
        "coste_energia": "Gratis VIP",
        "limitaciones": "Sin prompt negativo visible en UI. Modelo cerrado de SeaArt.",
    },
    "SeaArt Infinity V2.0": {
        "nota": 4.7,
        "has_negative": False,
        "is_natural": True,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar"],
        "max_imagenes": 4,
        "best_for": "Modelo oficial V2.0 de SeaArt. Simplificado: sin sampler/CFG/steps. Solo prompt + genera. Magia de sugerencia. Ideal para principiantes y resultados rápidos.",
        "prompt_formula": "Lenguaje natural descriptivo. Describe la escena con detalle, el modelo se encarga del resto.",
        "prompt_ejemplo": "Cinematic portrait of an old man reading a book in a cozy library, warm lamp light, dust particles in the air, shallow depth of field",
        "coste_energia": "Gratis VIP",
        "limitaciones": "Sin control avanzado (no sampler, no CFG, no steps, no negative). Solo semilla fija. Máx 4 imágenes.",
    },
    "SeaArt Realism": {
        "nota": 3.6,
        "has_negative": False,
        "is_natural": True,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Fotorrealismo de SeaArt. 3.9M usos. Modelo Flux.1 D. Ideal para retratos y escenas realistas.",
        "prompt_formula": "Lenguaje natural descriptivo. Describe la escena con detalle.",
        "prompt_ejemplo": "A beautiful woman portrait, detailed skin texture, natural lighting, soft bokeh background, professional photography",
        "coste_energia": "Gratis VIP",
        "limitaciones": "Sin prompt negativo visible en UI. Modelo basado en Flux.1 D.",
    },
    "Luma Uni-1.1 Image": {
        "nota": 4.3,
        "has_negative": False,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9", "9:1", "1:9", "4:5", "5:4"],
        "max_chars": 2000,
        "modos_gen": ["Create", "Modify"],
        "max_imagenes": 9,
        "best_for": "Modelo multimodal de Luma. Create vs Modify modes. Hasta 9 referencias con roles asignados (estilo, personaje, composición, color, iluminación). Seeds para reproducibilidad.",
        "prompt_formula": "Modo Create: descripción nueva. Modo Modify: 'Use IMAGE1 for style, IMAGE2 for lighting'. Naming references + roles es clave.",
        "prompt_ejemplo": "Create: a cinematic portrait of a woman in dramatic lighting. Modify: lighting shift, mood change to darker tone",
        "coste_energia": "Gratis (evento) — VIP",
        "limitaciones": "Modelo nuevo (1.4K usos, may 2026). Solo evento gratuito por ahora.",
    },
    # ── Familia Z-Image ──────────────────────────────────────
    "Z Image Turbo": {
        "nota": 4.6,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 8,
        "best_for": "Fotorrealismo ultrarrápido, latencia sub-segundo. Renderizado de texto bilingüe (inglés/chino). Razonamiento profundo. Sampler Euler, 20 pasos. En ComfyUI funciona como Turbo puro (CFG ~1.0, sin negative ni pesos); en SeaArt la plataforma lo adapta para aceptar negative y pesos.",
        "prompt_formula": "Depende de plataforma. SeaArt: tags con pesos SD tradicionales + negative. ComfyUI: tags limpios sin pesos ni negative (modelo Turbo puro).",
        "prompt_ejemplo": "close-up portrait, 1girl, silver hair, blue eyes, detailed skin, soft studio lighting, shallow DOF, muted teal background, professional photography, 8K",
        "sampler_recomendado": "Euler",
        "pasos": 20,
        "cfg": 1.0,
        "coste_energia": "28 (Calidad) — gratis VIP",
        "limitaciones": "En ComfyUI: modelo Turbo puro que NO soporta negative ni pesos numéricos. En SeaArt: adaptado por la plataforma. No tiene panel de reparación de rostros/personajes en la UI.",
    },
    "Z-Image-Base-Realistic": {
        "nota": 4.8,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 8,
        "best_for": "Fotorrealismo de máxima fidelidad (no destilado). Versión Europe-v1.0: texturas de personajes optimizadas para estética europea. Más pasos = más detalle que Z Image Turbo.",
        "prompt_formula": "Tag-based con pesos SD: vista/plano, sujeto+detalles, medium, resolución, estilo, fondo, colores, iluminación, calidad. Mayor budget de pasos permite prompts más detallados.",
        "prompt_ejemplo": "close-up portrait, 1girl, European features, (detailed skin texture:1.3), freckles, green eyes, auburn hair, soft natural lighting, shallow DOF, (cinematic color grading:1.2), 8K, hyper-realistic, professional photography",
        "sampler_recomendado": "Euler",
        "pasos": "25-50",
        "cfg": "3-5",
        "clip_skip": 1,
        "negative_recomendado": "Low quality, blurry, distorted, ugly, extra fingers, deformed face, asymmetrical eyes, misaligned teeth, repetitive textures, compression artifacts, watermarks, text, overexposure, heavy shadows, color distortion, lack of details, stiff movements, deformities",
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Más lento que Z Image Turbo (más pasos). Optimizado para personajes europeos en v1.0.",
    },
    "NiwaStyle - Animax ColorPop (Illustrious)": {
        "nota": 5.0,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 800,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Anime / Digital Painting de altísima calidad. Ideal para ilustración, personajes anime, obras masterpiece.",
        "prompt_formula": "Tag-based Danbooru style: masterpiece, 8k, Highest Quality, detail, high resolution, Digital Painting, ultra detailed, [tags]",
        "prompt_ejemplo": "masterpiece, 8k, Highest Quality, detail, high resolution, Digital Painting, ultra detailed, 1girl, silver hair, blue eyes",
        "sampler_recomendado": "Euler a / DPM++ 2M",
        "pasos": "25-40",
        "cfg": "4-7",
        "clip_skip": 2,
        "resolucion_recomendada": "936x1536",
        "trigger_words": "masterpiece, 8k, Highest Quality, detail, high resolution, Digital Painting, ultra detailed",
        "coste_energia": "6 (mín) - 40 (máx) — gratis VIP",
        "limitaciones": "No diseñado para fotorrealismo extremo.",
    },
    "FLUX.1 [dev]": {
        "nota": 4.4,
        "has_negative": False,
        "is_natural": True,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 8,
        "best_for": "Excelente adherencia al prompt y renderizado de texto impecable. Genera gran variedad de contenido sin necesidad de Loras.",
        "prompt_formula": "Lenguaje natural simple y descriptivo. Olvida las técnicas de Midjourney o Stable Diffusion.",
        "prompt_ejemplo": "A young woman lying on a bed wearing a shirt with the words 'touch me', soft lighting, cinematic atmosphere",
        "sampler_recomendado": "Euler",
        "pasos": 30,
        "cfg": 3.5,
        "coste_energia": "Aprox. 7 por imagen",
        "limitaciones": "Modelo muy pesado, tarda más que otros. Estrictamente SFW",
    },
    "FLUX.1-dev-fp8": {
        "nota": 4.6,
        "has_negative": False,
        "is_natural": True,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 8,
        "best_for": "Versión optimizada (quantized) de FLUX.1 [dev]. Más rápida y consume menos recursos.",
        "prompt_formula": "Lenguaje natural simple y descriptivo.",
        "prompt_ejemplo": "A high-fashion studio portrait of a woman exuding serene elegance.",
        "sampler_recomendado": "Euler",
        "pasos": 25,
        "cfg": 1,
        "coste_energia": "Aprox. 7 por imagen",
        "limitaciones": "Podría perder ligerísimos detalles comparado con el original.",
    },
    "FLUX.1": {
        "nota": 4.9,
        "has_negative": False,
        "is_natural": True,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 8,
        "best_for": "Versión 'schnell'. VELOCIDAD: genera imágenes de altísima calidad con 1-4 pasos. Ideal prototipado.",
        "prompt_formula": "Lenguaje natural simple.",
        "prompt_ejemplo": "A high-fashion studio portrait of a woman exuding serene elegance",
        "sampler_recomendado": "Euler",
        "pasos": 4,
        "cfg": 1,
        "coste_energia": "Aprox. 7 por imagen",
        "limitaciones": "Podría carecer de los micro-detalles absolutos de la versión [dev].",
    },
    "FLUX.1D UltraReal": {
        "nota": 5.0,
        "has_negative": False,
        "is_natural": True,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 8,
        "best_for": "FOTORREALISMO ABSOLUTO. Retratos con detalles de piel hiperrealistas.",
        "prompt_formula": "Lenguaje natural descriptivo. Describe con detalle iluminación y textura.",
        "prompt_ejemplo": "A close-up cinematic portrait of a young woman, highly detailed skin texture, soft natural lighting",
        "sampler_recomendado": "Euler",
        "pasos": 25,
        "cfg": 3.5,
        "coste_energia": "Aprox. 7 por imagen",
        "limitaciones": "Optimizado para 1024x1024 o superior. Licencia no comercial.",
    },
    "MASTER FLUX (LoRA merged with flux1-dev fp16)": {
        "nota": 4.3,
        "has_negative": False,
        "is_natural": True,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 8,
        "best_for": "CONTENIDO NSFW. Diseñado para saltarse la censura.",
        "prompt_formula": "Lenguaje natural descriptivo. Enfocado en anatomía y acción.",
        "prompt_ejemplo": "A high-fashion studio portrait...",
        "sampler_recomendado": "Euler",
        "pasos": 30,
        "cfg": 6,
        "coste_energia": "Aprox. 12 por imagen",
        "limitaciones": "Estrictamente para contenido adulto/NSFW.",
    },
    "Flux-dev": {
        "nota": 4.4,
        "has_negative": True,
        "is_natural": True,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Flux-dev (fp8). 1.1M usos. Modelo Flux.1 D con excelente adherencia al prompt y renderizado de texto.",
        "prompt_formula": "Lenguaje natural descriptivo. Describe la escena con detalle.",
        "prompt_ejemplo": "A fantasy character portrait, detailed armor, magical effects, cinematic lighting",
        "sampler_recomendado": "Euler",
        "pasos": 30,
        "cfg": 3.5,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "fp8 quantization. Sin modo 'fast'.",
    },
    # ── Stable Diffusion 3.5 ────────────────────────────────────
    "SD 3.5 Large": {
        "nota": 3.9,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Stable Diffusion 3.5 Large (fp8). 229.7K usos. Modelo base SD 3.5L. Alta calidad, versátil para distintos estilos.",
        "prompt_formula": "Tag-based: tags descriptivos separados por comas.weights como (tag:1.2). Negative prompt recomendado.",
        "prompt_ejemplo": "1girl, portrait, detailed skin, natural lighting, (cinematic:1.3), best quality, masterpiece, (deformed hands:0.8)",
        "clip_skip": 1,
        "sampler_recomendado": "Euler",
        "pasos": "25-40",
        "cfg": "4-7",
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "fp8 quantization. Sin modo 'fast'. Requiere negative prompt para mejores resultados.",
    },
    "SD 3.5 Medium": {
        "nota": 3.8,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Stable Diffusion 3.5 Medium (fp8). Versión reducida del modelo SD 3.5. Más eficiente en recursos manteniendo buena calidad.",
        "prompt_formula": "Tag-based: tags descriptivos. Negative prompt recomendado para evitar artefactos.",
        "prompt_ejemplo": "landscape, nature, mountains, golden hour, (detailed:1.2), best quality, masterpiece",
        "clip_skip": 1,
        "sampler_recomendado": "Euler",
        "pasos": "20-35",
        "cfg": "4-6",
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Menor capacidad que Large para detalles finos.",
    },
    "SD 3.5 Large Turbo": {
        "nota": 3.7,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar"],
        "max_imagenes": 4,
        "best_for": "Stable Diffusion 3.5 Large Turbo (fp8). Versión rápida del SD 3.5. Menos pasos, generación más rápida.",
        "prompt_formula": "Tag-based simplificado. Fewer steps, good results.",
        "prompt_ejemplo": "1girl, portrait, soft lighting, (high quality:1.2), masterpiece, (nsfw:0.9)",
        "clip_skip": 1,
        "sampler_recomendado": "Euler",
        "pasos": "10-20",
        "cfg": "3-5",
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Modo 'fast' no funciona. Menor calidad que la versión completa.",
    },
    # ── SeaArt Film ─────────────────────────────────────────────
    "SeaArt Film": {
        "nota": 4.5,
        "has_negative": True,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 2000,
        "modos_gen": ["Estándar", "Quality"],
        "max_imagenes": 8,
        "best_for": "SeaArt Film. 8.8M usos. Cinematografía profesional, iluminación avanzada, composición artística. Soporta Text-to-Image e Image-to-Image.",
        "prompt_formula": "Lenguaje natural descriptivo: sujeto + escena + iluminación + cámara + estilo + calidad.",
        "prompt_ejemplo": "A dramatic portrait of a woman in golden hour light, cinematic composition, volumetric lighting, 8K, professional photography",
        "sampler_recomendado": "Euler",
        "pasos": 30,
        "cfg": 5,
        "clip_skip": 1,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Optimizado para cinematografía. Menos versátil que Infinity para estilos variados.",
    },
    "SeaArt Film V2.0": {
        "nota": 4.4,
        "has_negative": True,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 2000,
        "modos_gen": ["Estándar", "Quality"],
        "max_imagenes": 8,
        "best_for": "SeaArt Film V2.0. 247K usos. Cinematografía mejorada, control preciso de luz/sombra/composición. Mejor consistencia visual.",
        "prompt_formula": "Lenguaje natural detallado: escena + sujeto + iluminación profesional + cámara + mood + calidad.",
        "prompt_ejemplo": "Wide establishing shot of a cowboy walking through a desert at sunset, dust particles in golden light, cinematic wide angle, dramatic atmosphere",
        "sampler_recomendado": "Euler",
        "pasos": 25,
        "cfg": 5,
        "clip_skip": 1,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Nuevo modelo (sep 2025). Menos documentación de settings óptimos.",
    },
    "SeaArt Film Edit": {
        "nota": 4.3,
        "has_negative": True,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar"],
        "max_imagenes": 4,
        "best_for": "SeaArt Film Edit. 1.5M usos. Edición de imágenes con referencia. Cambios precisos: peinado, ropa, pose, ángulo. Preserva identidad del sujeto.",
        "prompt_formula": "Instrucciones de edición: cambiar/añadir/remplazar elementos. Reference images para estilo consistente.",
        "prompt_ejemplo": "Change the hairstyle to spiky hair, keep the same face and outfit, add studio lighting from above",
        "sampler_recomendado": "Euler",
        "pasos": 20,
        "cfg": 4,
        "clip_skip": 1,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Editor, no generador puro. Requiere imagen de referencia.",
    },
    "SeaArt Film Edit 2.0": {
        "nota": 4.0,
        "has_negative": True,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar"],
        "max_imagenes": 4,
        "best_for": "SeaArt Film Edit 2.0. 898.8K usos. Edición avanzada con multi-referencia. Mejor preservación de identidad, texto layout profesional, texturas realistas.",
        "prompt_formula": "Instrucciones de edición precisas + múltiples referencias. Soporta combinación de estilos de diferentes imágenes.",
        "prompt_ejemplo": "Replace the clothing with a black suit, keep the pose unchanged, add warm studio lighting from the left, match the style of reference image 2",
        "sampler_recomendado": "Euler",
        "pasos": 20,
        "cfg": 4,
        "clip_skip": 1,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Editor especializado. Multi-referencia puede reducir consistencia si son muy diferentes.",
    },
    "SeaArt Film Edit 3.0": {
        "nota": 4.4,
        "has_negative": True,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 2000,
        "modos_gen": ["Estándar", "Pro"],
        "max_imagenes": 4,
        "best_for": "SeaArt Film Edit 3.0. 114.2K usos. Producción visual profesional. Física correcta, materiales realistas, Ultra HD 4K, tipografía profesional.",
        "prompt_formula": "Instrucciones complejas multi-cláusula. Ejecuta planes estructurados: distribuir elementos, mantener mientras modifica. Ideal para publicidad, e-commerce, diagramas.",
        "prompt_ejemplo": "Generate product photo: place the perfume bottle centered, add dramatic lighting from above, change background to pure white, maintain glass reflections",
        "sampler_recomendado": "Euler",
        "pasos": 25,
        "cfg": 5,
        "clip_skip": 1,
        "coste_energia": "Variable — gratis VIP (evento)",
        "limitaciones": "Producción industrial. Resultados más técnicos/artísticos según el caso.",
    },
    # ── SeaArt Furry ────────────────────────────────────────────
    "SeaArt Furry XL V1.0": {
        "nota": 4.5,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar"],
        "max_imagenes": 4,
        "best_for": "SeaArt Furry XL V1.0. 546.4K usos. Primer modelo open-source de SeaArt. Especializado en furry/anthro. Millones de imágenes furry en training.",
        "prompt_formula": "Tag-based: calidad + especie + character details + estilo + iluminación.",
        "prompt_ejemplo": "masterpiece, best quality, 1 furry wolf character, detailed fur texture, blue eyes, standing pose, fantasy forest background, cinematic lighting",
        "sampler_recomendado": "Euler",
        "pasos": 28,
        "cfg": 7,
        "clip_skip": 1,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Especializado en furry. No fotorrealismo general.",
    },
    # ── SeaArt Story ────────────────────────────────────────────
    "SeaArt Story": {
        "nota": 4.6,
        "has_negative": True,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 2000,
        "modos_gen": ["Estándar", "Quality"],
        "max_imagenes": 4,
        "best_for": "SeaArt Story. 444.8K usos. Storytelling/narrativa visual. Captura momentos emocionales, storytelling cinematográfico. Ideal para storyboards, conceptos visuales.",
        "prompt_formula": "Lenguaje natural narrativo: describe escena + emoción + composición visual + estilo.",
        "prompt_ejemplo": "A dramatic scene of two strangers meeting in a rain-soaked Tokyo alleyway at night, cinematic lighting, emotional tension, film quality",
        "sampler_recomendado": "Euler",
        "pasos": 30,
        "cfg": 5,
        "clip_skip": 1,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Optimizado para narrativa, menos para static portraits aislados.",
    },
    "SeaArt Story 2.0": {
        "nota": 4.7,
        "has_negative": True,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 2000,
        "modos_gen": ["Estándar", "Quality"],
        "max_imagenes": 4,
        "best_for": "SeaArt Story 2.0. 71.5K usos. Fotorrealismo cinematográfico mejorado, consistencia de personaje entre frames, text+image hybrid editing.",
        "prompt_formula": "Lenguaje natural descriptivo + referencia de imagen. Describe pose, expresión, iluminación precisa. Control de identidad entre generaciones.",
        "prompt_ejemplo": "Close-up portrait of a woman with silver hair in a vintage diner, golden hour light streaming through window, cinematic mood, sharp focus on eyes",
        "sampler_recomendado": "Euler",
        "pasos": 25,
        "cfg": 5,
        "clip_skip": 1,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Mejor para escenas narrativas que para static portraits aislados.",
    },
    # ── SeaArt Fusion ────────────────────────────────────────────
    "SeaArt Fusion": {
        "nota": 5.0,
        "has_negative": True,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 2000,
        "modos_gen": ["Estándar", "Pro"],
        "max_imagenes": 4,
        "best_for": "SeaArt Fusion. 65.8K usos. Razonamiento conceptual multimodal, contenido educativo, científico, histórico. Combina conocimiento real con expresión artística.",
        "prompt_formula": "Lenguaje natural descriptivo para conceptos complejos. Explicar principios científicos, procesos históricos, contenido educativo visual.",
        "prompt_ejemplo": "Create a four-panel diagram showing the bee life cycle: egg, larva, pupa, adult bee, scientific illustration style, clean lines, labeled",
        "sampler_recomendado": "Euler",
        "pasos": 25,
        "cfg": 5,
        "clip_skip": 1,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Mejor para contenido conceptual/educativo que para arte puro.",
    },
    # ── SeaArt Genesis ─────────────────────────────────────────
    "SeaArt Genesis": {
        "nota": 3.5,
        "has_negative": True,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 2000,
        "modos_gen": ["Estándar"],
        "max_imagenes": 4,
        "best_for": "SeaArt Genesis. 57.9K usos. Moda, diseño de alta costura, estética, arte personalizado. Detalles hiperrealistas, texturas stunning. Feature de personalización de estilo único.",
        "prompt_formula": "Lenguaje natural con enfoque en moda y diseño. Describe prendas, accesorios, iluminación editorial, pose. SFW solo.",
        "prompt_ejemplo": "A high-fashion editorial of a model wearing a sculptural silver gown, dramatic runway lighting, luxury brand aesthetic, 8K resolution, professional photography",
        "sampler_recomendado": "Euler",
        "pasos": 25,
        "cfg": 5,
        "clip_skip": 1,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "SFW solo. Enfoque en moda. Menos versátil para otros estilos. Nota baja (3.5).",
    },
    # ── SeaArt Story Edit ──────────────────────────────────────
    "SeaArt Story Edit": {
        "nota": 4.4,
        "has_negative": True,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar"],
        "max_imagenes": 4,
        "best_for": "SeaArt Story Edit. 9.1K usos. Precision local editing sin máscara. Rewriting de historia: cambiar expresión, pose, elementos. Consistencia de identidad del sujeto. Soporta multi-referencia.",
        "prompt_formula": "Instrucciones de edición precisas: 'Change [elemento] to [nuevo]', 'Keep [elemento] same'. Sin máscara, solo instrucciones.",
        "prompt_ejemplo": "Change the expression to a confident smile, keep the same outfit and background, add soft studio lighting from above",
        "sampler_recomendado": "Euler",
        "pasos": 20,
        "cfg": 4,
        "clip_skip": 1,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Editor especializado. Más edición que generación pura.",
    },
    # ── SeaArt Ultra Edit ──────────────────────────────────────
    "SeaArt Ultra Edit": {
        "nota": 4.6,
        "has_negative": True,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 2500,
        "modos_gen": ["Estándar", "Pro"],
        "max_imagenes": 4,
        "best_for": "SeaArt Ultra Edit. 53.5K usos. Next-gen all-in-one: Text-to-Image + Image-to-Image + Multi-Reference. Preserva identidad, respuestas precisas a edits detallados, control de estilo. Cine, portraits, publicidad.",
        "prompt_formula": "Lenguaje natural detallado. Describe escena completa o usa referencias múltiples para consistencia. Soporta inicio+fin frames para transiciones.",
        "prompt_ejemplo": "Cinematic portrait of a samurai warrior in a bamboo forest, golden hour backlight, traditional armor, misty atmosphere, ultra detailed, sharp focus on katana",
        "sampler_recomendado": "Euler",
        "pasos": 25,
        "cfg": 5,
        "clip_skip": 1,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Multi-referencia puede reducir consistencia si son muy diferentes.",
    },
    # ── T-Ponynai3 ──────────────────────────────────────────────
    "T-Ponynai3 V6": {
        "nota": 4.7,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1200,
        "modos_gen": ["Estándar"],
        "max_imagenes": 4,
        "best_for": "T-Ponynai3 V6. 1.1M usos. Fusion anime (PonyV6 + NAI3). Estilo anime vibrant. Excelente en escenas, manos/pies, luz/sombra. No requiere VAE (incluido). Usa score tags y source_anime.",
        "prompt_formula": "Score tags primero: score_9, score_8_up, score_7_up, source_anime, anime, sujeto, composicion tag-based.",
        "prompt_ejemplo": "score_9, score_8_up, score_7_up, source_anime, anime, 1girl, raiden shogun, holding sword, sakura forest, purple sky, dramatic lighting",
        "sampler_recomendado": "Euler a",
        "pasos": "25-30",
        "cfg": 7,
        "clip_skip": 2,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Requiere anime/source_anime para estilo. No fotorrealismo.",
    },
    # ── NoobAI XL ─────────────────────────────────────────────
    "NoobAI-XL (NAI-XL)": {
        "nota": 4.5,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar", "Quality"],
        "max_imagenes": 4,
        "best_for": "NoobAI-XL (NAI-XL). 796.5K usos. V-prediction model. Excelente para anime y furry. 13M imágenes Danbooru+e621. Reconoce personajes, artistas, series.",
        "prompt_formula": "Calidad tags al inicio: masterpiece, best quality, newest, absurdres, highres. Luego: personaje, serie, artistas, tags. No underscores, escapar ().",
        "prompt_ejemplo": "masterpiece, best quality, newest, absurdres, highres, ganyu (genshin impact), genshin impact, solo, blue hair, detailed background",
        "sampler_recomendado": "Euler",
        "pasos": "28-35",
        "cfg": "4-5",
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Solo V-prediction. No Karras samplers. No CLIP skip. Compatible con LoRA PonyV6 y Animagine.",
    },
    # ── WAI-Pluralistic-Noob ──────────────────────────────────
    "WAI-Pluralistic-Noob": {
        "nota": 4.6,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar"],
        "max_imagenes": 4,
        "best_for": "WAI-Pluralistic-Noob. 1.7M usos. Estilo artístico estable basado en Noob. Colaboración con artistas NOOB para ángulos de composición y colores.",
        "prompt_formula": "Tag-based SDXL: calidad + sujeto + estilo + iluminación. Noob estilo base.",
        "prompt_ejemplo": "masterpiece, best quality, 1girl, detailed face, elegant dress, soft lighting, bokeh background, cinematic",
        "sampler_recomendado": "Euler",
        "pasos": "28-35",
        "cfg": "4-5",
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Basado en SDXL. No soporta weights como Flux.",
    },
    # ── Counterfeit V3.0 ──────────────────────────────────────
    "Counterfeit V3.0": {
        "nota": 4.4,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar"],
        "max_imagenes": 4,
        "best_for": "Counterfeit V3.0. Modelo anime de alta calidad enfocado en personajes femeninos. Composición creativa, estilo anime estilizado. Uso de Danbooru tags.",
        "prompt_formula": "Calidad + vista + sujeto + detalles + tags + iluminacion. EasyNegativeV2 en negativo.",
        "prompt_ejemplo": "(masterpiece, best quality), highly detailed, office scene, 1girl, brown eyes, glasses, green hair, office woman, formal attire, depth of field, bokeh",
        "sampler_recomendado": "DPM++ 2M Karras / DPM++ SDE Karras",
        "pasos": "20-25",
        "cfg": "8-10",
        "clip_skip": 2,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Prioriza composición sobre anatomía. Problemas con manos. Solo personajes conocidos limitados.",
    },
    # ── Temporal Paradox Mix ──────────────────────────────────
    "Temporal Paradox Mix": {
        "nota": 4.5,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1200,
        "modos_gen": ["Estándar"],
        "max_imagenes": 4,
        "best_for": "Temporal Paradox Mix. 37.7K usos. Fusion de 10+ modelos. Versátil: personajes M/F, paisajes, mechas, animales. Excelente manos y uñas. Funciona con prompts largos y cortos.",
        "prompt_formula": "Tag-based mixto. Funciona con prompts breves o detallados. Embeddings negativos recomendados.",
        "prompt_ejemplo": "cinematic portrait, 1woman, detailed hands, elegant outfit, studio lighting, 8K, photorealistic, sharp focus",
        "sampler_recomendado": "Euler a / DPM++ 2M Karras",
        "pasos": "20-40",
        "cfg": "7-8",
        "clip_skip": "1-2",
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "SD 1.5 base. Menos versátil que SDXL para estilos modernos.",
    },
    # ── Realismo SD ──────────────────────────────────────────
    "Illustrious Realism by Klaabu": {
        "nota": 4.9,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1200,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Fotorrealismo cinematográfico de alta fidelidad. Fine-tuned sobre Illustrious. 1.6M usos. Personajes ricos en detalle, texturas realistas, text rendering.",
        "prompt_formula": "Tag-based SD: vista/plano, sujeto+detalles, medium, resolución, estilo, fondo, iluminación, calidad. Pesos (tag:1.2).",
        "prompt_ejemplo": "cinematic portrait, 1woman, freckled skin, green eyes, auburn hair, (detailed skin texture:1.3), soft golden hour light, shallow DOF, 8K, photorealistic",
        "sampler_recomendado": "DPM++ 2M Karras",
        "pasos": 25,
        "cfg": "4-6.5",
        "clip_skip": 1,
        "coste_energia": "Gratis VIP",
        "limitaciones": "Máx 4 imágenes simultáneas. Tiene reparación avanzada (rostros/personajes).",
    },
    "Real Dream SDXL": {
        "nota": 4.6,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1200,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Realismo SDXL versátil. 873K usos. Personajes, paisajes, celebridades. Base Pony/SDXL11. Reparación avanzada de rostros.",
        "prompt_formula": "Tag-based SD: vista/plano, sujeto+detalles, medium, resolución, estilo, fondo, iluminación, calidad.",
        "prompt_ejemplo": "full body portrait, 1woman, elegant dress, dramatic lighting, urban background at dusk, (cinematic:1.2), photorealistic, 8K, sharp focus",
        "sampler_recomendado": "DPM++ SDE Karras",
        "pasos": 20,
        "cfg": 6,
        "clip_skip": 2,
        "coste_energia": "Gratis VIP",
        "limitaciones": "Máx 4 imágenes simultáneas. Resolución por defecto 768x1152.",
    },
    "MajicMIX Realistic v6": {
        "nota": 5.0,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 800,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Clásico del fotorrealismo SD. 1.2M usos, nota 5.0. Excelente para retratos, fotografía y fantasía realista. Reparación de rostros/personajes.",
        "prompt_formula": "Tag-based SD: vista/plano, sujeto+detalles, medium, resolución, estilo, fondo, iluminación, calidad. Modelo SD 1.5, prompts más cortos.",
        "prompt_ejemplo": "close-up portrait, 1girl, detailed face, soft studio light, (skin pores:1.2), natural makeup, blurred background, professional photo, masterpiece",
        "sampler_recomendado": "Euler",
        "pasos": 30,
        "cfg": 7,
        "clip_skip": 2,
        "coste_energia": "Gratis VIP",
        "limitaciones": "SD 1.5, resolución base 512x768. Prompts cortos funcionan mejor (~800 chars max).",
    },
    "Realities Edge XL Turbo V7": {
        "nota": 4.7,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1200,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 8,
        "best_for": "SDXL Turbo ultrarrápido. Prompts cortos y directos dan mejores resultados. Fotorrealismo, 3D, retratos, mangas. Versión Lightning disponible.",
        "prompt_formula": "Tag-based SD: prompts cortos y concisos. Este modelo responde mejor a prompts simples y directos que a prompts muy elaborados.",
        "prompt_ejemplo": "portrait of a rugged man, cinematic dust, sharp details, dramatic light, photorealistic, 8K",
        "sampler_recomendado": "DPM++ SDE Karras",
        "pasos": 20,
        "cfg": 2,
        "clip_skip": 2,
        "coste_energia": "Gratis VIP",
        "limitaciones": "CFG muy bajo (2.0). Resolución por defecto 1152x1536. Prompts largos pueden dar resultados inconsistentes.",
    },
    "CyberRealistic": {
        "nota": 4.6,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Fotorrealismo alternativo de alta calidad. 8.7M usos. Versión Final. Excelente para retratos, escenas urbanas, moda. Upscaler 4x-UltraSharp integrado.",
        "prompt_formula": "Tag-based SD: vista/plano, sujeto+detalles, medium, estilo, fondo, iluminación, calidad.",
        "prompt_ejemplo": "close-up portrait, 1woman, detailed face, urban background, (cinematic lighting:1.3), shallow DOF, photorealistic, sharp focus, 8K",
        "sampler_recomendado": "DPM++ 2M SDE",
        "pasos": 32,
        "cfg": 7,
        "clip_skip": 2,
        "coste_energia": "Gratis VIP",
        "limitaciones": "SD 1.5 base. Resolución nativa 1024x1024. Muchas versiones disponibles (Final es la recomendada).",
    },
    "Realistic Vision V6.0": {
        "nota": 4.9,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 800,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 8,
        "best_for": "El estándar de oro del fotorrealismo SD. 4.2M usos, 99.6K favoritos. Retratos masculinos/femeninos hiperrealistas. Steps bajos (10) para resultados rápidos.",
        "prompt_formula": "Tag-based SD: vista/plano, sujeto+detalles, medium, resolución, estilo fotográfico, iluminación, calidad. Prompts concisos funcionan mejor.",
        "prompt_ejemplo": "RAW photo, portrait, 1man, formal suit, sharp jawline, (detailed skin:1.2), studio lighting, professional photography, 8K",
        "sampler_recomendado": "DPM++ SDE Karras",
        "pasos": 10,
        "cfg": 3,
        "clip_skip": 1,
        "coste_energia": "Gratis VIP",
        "limitaciones": "CFG muy bajo (3.0), solo 10 steps por defecto. Prompts cortos y directos dan mejor resultado.",
    },
    "Prodigies": {
        "nota": 4.9,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 800,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Retratos femeninos de altísima calidad. 596.8K usos. VAE incluido. Upscaler 4x-UltraSharp. Reparación de rostros/personajes avanzada.",
        "prompt_formula": "Tag-based SD: vista/plano, sujeto+detalles faciales, estilo, iluminación, calidad. Especialmente bueno con tags de belleza y moda.",
        "prompt_ejemplo": "close-up portrait, 1girl, detailed eyes, soft skin, natural makeup, (golden hour:1.2), bokeh, photorealistic, masterpiece",
        "sampler_recomendado": "DPM++ 2M Karras",
        "pasos": 25,
        "cfg": 7,
        "clip_skip": 1,
        "coste_energia": "Gratis VIP",
        "limitaciones": "SD 1.5 base. Resolución nativa 512x768. Orientado a retratos femeninos principalmente.",
    },
    "DreamShaper": {
        "nota": 4.9,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Clásico legendario versátil. 5.9M usos, 99.3K favoritos. Realismo + fantasía + arte digital. V8. CFG alto (9.0) para máximo seguimiento del prompt.",
        "prompt_formula": "Tag-based SD: vista/plano, sujeto+detalles, medium, resolución, estilo, fondo, iluminación. Acepta prompts largos y detallados gracias al CFG alto.",
        "prompt_ejemplo": "epic fantasy portrait, 1woman warrior, ornate golden armor, (dramatic lighting:1.3), volumetric fog, castle background, cinematic, masterpiece, 8K",
        "sampler_recomendado": "DPM++ SDE Karras",
        "pasos": 30,
        "cfg": 9,
        "clip_skip": 2,
        "coste_energia": "Gratis VIP",
        "limitaciones": "CFG alto (9.0). Upscaler 8x-NMKD. Muchas versiones disponibles (v8 es la actual).",
    },
    "Deliberate": {
        "nota": 5.0,
        "has_negative": False,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar"],
        "max_imagenes": 4,
        "best_for": "Deliberate v4. 1.5M usos, 14.3K favoritos, 122.1K likes. All-in-One. Prompts cortos funcionan mejor. Sin negativos necesarios. Tokens mj, cozy, cinematic.",
        "prompt_formula": "Prompts cortos y simples. Añadir mj, cozy o cinematic para boost. Sin necesidad de質量 tags.",
        "prompt_ejemplo": "beautiful woman portrait, mj, cinematic",
        "sampler_recomendado": "Euler a / UniPC",
        "pasos": "15-25",
        "cfg": "6-8",
        "coste_energia": "Gratis VIP",
        "limitaciones": "CC BY-NC-ND 4.0 (comercial requiere permiso). v4 (abr 2026).",
    },
    "PornRealistic": {
        "nota": 3.0,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar"],
        "max_imagenes": 4,
        "best_for": "PornRealistic. 53.1K usos. Merge de Epicrealism + CyberRealistic. Retratos femeninos fotorrealistas.",
        "prompt_formula": "Tag-based SD: sujeto + detalles + iluminación realista + calidad.",
        "prompt_ejemplo": "portrait, 1woman, detailed face, realistic skin, natural lighting, professional photography, 8K",
        "sampler_recomendado": "Euler a",
        "pasos": "20-30",
        "cfg": "6-8",
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Merge experimental. Orientado a femenino. Base SD 1.5.",
    },
    "Woman Realistic 3.1.0": {
        "nota": 4.3,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar"],
        "max_imagenes": 4,
        "best_for": "Woman Realistic 3.1.0. 922.6K usos. Fotorrealismo femenino. SD 2.1 base. Excelente para retratos de mujeres.",
        "prompt_formula": "Realism, (masterpiece:1.4, best quality), intricate details + sujeto + estilo.",
        "prompt_ejemplo": "Realistic, masterpiece, best quality, 1girl, detailed face, elegant dress, Victorian mansion",
        "sampler_recomendado": "DPM++ SDE Karras",
        "pasos": 15,
        "cfg": 6,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Trigger words: Realism, Photorealism, Woman, Vestido, Minifalda. Base SD 2.1.",
    },
    "Alchemist Mix (Illustrious Realism)": {
        "nota": 4.9,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Alchemist Mix (Illustrious Realism). 209.7K usos. Merge de Illustrious + RillusmRealistic + RedcraftCADS. Semi-realismo de alta calidad.",
        "prompt_formula": "DSLR photo style: very awa, masterpiece, best quality, year 2024, absurdres, highres + sujeto + detalles.",
        "prompt_ejemplo": "DSLR, realistic, cosplay photo, very awa, masterpiece, best quality, year 2024, absurdres, highres, realistic skin texture, photography shot with Canon EOS 5D",
        "sampler_recomendado": "Euler a",
        "pasos": 30,
        "cfg": 4.5,
        "clip_skip": 1,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Rostro en distancias largas puede requerir inpaint. v4.1 Finetune (jul 2025).",
    },
    "FantasticChix-HR": {
        "nota": 4.7,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "FantasticChix-HR. 695.8K usos. Semi-realismo/mezcla. Fusiona Fantastic Mix V4, ChikMix V3, ZemiHR V2. Retratos femeninos excelentes.",
        "prompt_formula": "Simple prompts funcionan bien: 1girl + sujeto + calidad. Soporta LoRAs.",
        "prompt_ejemplo": "A 21 year old female, masterpiece, best quality, detailed skin, natural lighting",
        "sampler_recomendado": "DPM++ SDE Karras",
        "pasos": 20,
        "cfg": 7,
        "clip_skip": 1,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Requiere VAE: vae-ft-mse-840000-ema-pruned. Base SD 1.5.",
    },
    "Juggernaut XL": {
        "nota": 4.6,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Juggernaut XL. 203.2K usos. Fotorrealismo SDXL versátil. Personajes de fantasía, retratos, escenas diversas.",
        "prompt_formula": "Tag-based SDXL: sujeto + detalles + iluminación + estilo + calidad.",
        "prompt_ejemplo": "portrait, 1woman, detailed face, studio lighting, cinematic, photorealistic, 8K, sharp focus",
        "sampler_recomendado": "Euler",
        "pasos": 25,
        "cfg": 5,
        "clip_skip": 1,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Base SDXL 1.0. Versión v7.0 disponible.",
    },
    "majicMIX fantasy": {
        "nota": 4.9,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 800,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "majicMIX fantasy (麦橘幻想). 680.3K usos. Estilo 2D/2.5D con mezcla de arte digital y semi-realismo. v3.0. Merge de Noosphere + dalcefoPainting.",
        "prompt_formula": "official art, unity 8k wallpaper, ultra detailed, masterpiece, best quality + sujeto + estilo artístico.",
        "prompt_ejemplo": "official art, unity 8k wallpaper, ultra detailed, beautiful and aesthetic, masterpiece, 1girl, elegant dress, dramatic lighting, fantasy style",
        "sampler_recomendado": "Euler",
        "pasos": "25-35",
        "cfg": "4-7",
        "clip_skip": 2,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Estilo fuertemente estilizado. Rostros lejanos requieren inpaint. Base SD 1.5.",
    },
    "Disney Pixar Cartoon type B": {
        "nota": 4.1,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Disney Pixar Cartoon type B. 2.2M usos. Estilo Pixar/Disney/Dreamworks. Merge de Type A + LoRA entrenado con imágenes Midjourney. Mejor en masculino y mayores que type A.",
        "prompt_formula": "Disney/Pixar style tags + sujeto + iluminación. Compatible con hires.fix.",
        "prompt_ejemplo": "pixar style, 3d render, beautiful girl, detailed hair, cinematic lighting, vibrant colors, 8k",
        "sampler_recomendado": "Euler a",
        "pasos": "25-30",
        "cfg": 7,
        "clip_skip": 2,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Requiere VAE o los colores salen pálidos/grisáceos. Base SD 1.5.",
    },
    "MiaoMiao Harem": {
        "nota": 4.8,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "MiaoMiao Harem V2.0. 1.7M usos. Estilo anime/harem con concepto 2026. CKXL05 architecture. Excelente manos/pies, LoRA compatible, prompts simples.",
        "prompt_formula": "very aesthetic, masterpiece, best quality, ultra-detailed, high contrast + sujeto + detalles.",
        "prompt_ejemplo": "very aesthetic, masterpiece, best quality, ultra-detailed, 1girl, elegant dress, beautiful face, soft lighting",
        "sampler_recomendado": "Euler a / DPM++ 2M Exponential",
        "pasos": "20-30",
        "cfg": "5-7",
        "clip_skip": 2,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Orientado a personajes. Sin hires.fix puede perder detalles.",
    },
    "REED_XXX_illustrious_SDXL": {
        "nota": 4.4,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1200,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "REED_XXX_illustrious_SDXL. 1.9M usos. Soporta 2D y 3D. Excelente retratos, character sheets, poses dinámicas. Iluminación limpia, mínima necesidad de ajuste.",
        "prompt_formula": "masterpiece, best quality, high quality, newest, highres, 8K, HDR, absurdres + sujeto + tags de composición.",
        "prompt_ejemplo": "masterpiece, best quality, highres, 8K, portrait, 1girl, elegant pose, looking at viewer, dramatic lighting",
        "sampler_recomendado": "Euler a / DPM++ 2M",
        "pasos": "15-40",
        "cfg": "5-8",
        "clip_skip": 2,
"coste_energia": "Variable — gratis VIP",
        "limitaciones": "Orientado a personajes. Sin hires.fix puede perder detalles.",
    },
    "Lily-Illustrious XL": {
        "nota": 4.9,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Lily-Illustrious XL. 1.8M usos. Estilo anime suave con colores pastel. Detección de artistas/caracteres. Compatible LoRA.",
        "prompt_formula": "Anime style tags + sujeto + colores pastel. Soporta JP/EN/tags.",
        "prompt_ejemplo": "1girl, pastel colors, soft lighting, beautiful landscape, masterpiece, best quality",
        "sampler_recomendado": "Euler a / DPM++ 2M",
        "pasos": "20-30",
        "cfg": "5-8",
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "v3.0. No vender imágenes sin editar.",
    },
    "Pixel Illustrious": {
        "nota": 4.0,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar"],
        "max_imagenes": 4,
        "best_for": "Pixel Illustrious v3.0. 23.8K usos. Pixel art retro anime/cyber-fantasy. 16-32bit video games style. Glowing eyes, expressive characters.",
        "prompt_formula": "Pixel art style tags + sujeto + neon/retro elementos.",
        "prompt_ejemplo": "pixel art, 1girl, cyberpunk city, neon lights, glowing eyes, retro game style",
        "sampler_recomendado": "Euler a",
        "pasos": "25-45",
        "cfg": "5-7",
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "A veces no dispara pixel. Ver trigger words.",
    },
    "SDXL FaeTastic": {
        "nota": 4.9,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1200,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "SDXL FaeTastic v24. 294.2K usos. Colores vibrantes tipo 1.5 FaeTastic. SDXL optimizado con LoRAs de detalles y ojos.",
        "prompt_formula": "masterpiece, newest, absurdres, best quality, amazing quality + sujeto + estilo.",
        "prompt_ejemplo": "1girl, fantasy dress, magical forest, vibrant colors, masterpiece, best quality, detailed",
        "sampler_recomendado": "DPM++ 2M Karras",
        "pasos": "25-35",
        "cfg": "5-7",
        "clip_skip": 2,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Base SDXL 1.0. No monetizar en third-party sites sin permiso.",
    },
    "Pie - Models 🥧": {
        "nota": 5.0,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1000,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Pie Models 🥧. 2.0M usos. Colección Illustrious: Apple Pie (anime), Blueberry (semi-real), Cherry (híbrido), Mango (vibrant 2.5D), etc.",
        "prompt_formula": "Varía por tipo. general: masterpiece, newest, absurdres, best quality + sujeto.",
        "prompt_ejemplo": "1girl, beautiful portrait, (add realistic tag for semi-real pies), masterpiece, best quality",
        "sampler_recomendado": "DPM++ 2M Karras",
        "pasos": 30,
        "cfg": 5,
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "12 variantes: Apple, Blueberry, Cherry, Derby, Elderberry, Fudge, Grape, Honey, Impossible, Jam, Key Lime, Mango, Lemon.",
    },
# ── Nano Banana ──────────────────────────────────────────
    "Nano Banana Pro Image": {
        "nota": 3.6,
        "has_negative": False,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9"],
        "max_chars": 2000,
        "modos_gen": ["Estándar"],
        "max_imagenes": 10,
        "best_for": "Motor Gemini 3 Pro. 331.9K usos. Text rendering mejorado, multi-image fusion, character consistency, 2K nativo con 4K upscale. Generación 1-5 segundos.",
        "prompt_formula": "Lenguaje natural: describe cambios deseados, usa 'Replace background with...', 'Keep face identity...'",
        "prompt_ejemplo": "Replace the background with a snowy mountain, keep the person's face and pose",
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Sin sampler/CFG/negative. Limitaciones ocasionales en manos y reflejos complejos.",
    },
    "Nano Banana 2": {
        "nota": 4.0,
        "has_negative": False,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9"],
        "max_chars": 2500,
        "modos_gen": ["Estándar", "Pro"],
        "max_imagenes": 14,
        "best_for": "Motor Gemini 3.1 Flash Image. 505.9K usos. Fast iteration, strong world knowledge, text-to-image + editing avanzado. Mejor price-performance.",
        "prompt_formula": "Write constraints as checklist: Subject, Scene, Composition, Lighting, Materials, Output. Para editing: 'Replace background with...', 'Keep face identity...'",
        "prompt_ejemplo": "A portrait of a woman, studio lighting, golden hour, professional photography, keep the face identity, change outfit to formal suit",
        "coste_energia": "Variable — gratis VIP",
        "limitaciones": "Sin sampler/CFG/negative. No soporta cropping preciso de aspect ratio.",
    },
    # ── Anime / Ilustración ─────────────────────────────────
    "NiwaStyle - Animax Plus (Illustrious)": {
        "nota": 5.0,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 800,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Hermana mayor de Animax ColorPop. Anime/2.5D de altísima calidad. 285K usos. Illustrious SDXL. Ideal para personajes anime detallados con toques semi-realistas.",
        "prompt_formula": "Tag-based Danbooru style: masterpiece, 8k, Highest Quality, detail, high resolution, Digital Painting, ultra detailed, [tags]",
        "prompt_ejemplo": "masterpiece, 8k, Highest Quality, ultra detailed, 1girl, long white hair, violet eyes, gothic lolita dress, moonlit balcony, (cinematic lighting:1.2), cherry blossoms",
        "sampler_recomendado": "DPM++ 2M Karras",
        "pasos": 25,
        "cfg": 7,
        "clip_skip": 2,
        "resolucion_recomendada": "936x1536",
        "trigger_words": "masterpiece, 8k, Highest Quality, detail, high resolution, Digital Painting, ultra detailed",
        "coste_energia": "Gratis VIP",
        "limitaciones": "Máx 4 imágenes. Optimizado para anime/2.5D, no fotorrealismo.",
    },
    "Pipi-iL-CG6.5": {
        "nota": 4.7,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 800,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Estilo CG/3D render cinematográfico. Ideal para mech suits, sci-fi, personajes con armaduras, escenas épicas con iluminación dramática.",
        "prompt_formula": "Tag-based SD: vista/plano, sujeto+detalles, medium, resolución, estilo CG, fondo, iluminación cinematográfica.",
        "prompt_ejemplo": "1girl, mech pilot, futuristic cockpit, (detailed mechanical suit:1.3), neon blue accents, dramatic rim light, CG render, 8K, ultra detailed",
        "sampler_recomendado": "Euler a",
        "pasos": 25,
        "cfg": 4.5,
        "clip_skip": 2,
        "resolucion_recomendada": "720x1280",
        "coste_energia": "Gratis VIP",
        "limitaciones": "Máx 4 imágenes. Nicho CG/sci-fi, menos versátil para otros estilos.",
    },
    "NiwaStyle - Animax Chill (Illustrious)": {
        "nota": 5.0,
        "has_negative": True,
        "is_natural": False,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 800,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 4,
        "best_for": "Anime relajado, slice-of-life, personajes suaves. 316K usos. Illustrious v3.0. Estética chill/dreamy, tonos suaves, iluminación atmosférica.",
        "prompt_formula": "Tag-based Danbooru style: masterpiece, 8k, Highest Quality, detail, high resolution, Digital Painting, ultra detailed, [tags]",
        "prompt_ejemplo": "masterpiece, 8k, ultra detailed, 1girl, short brown hair, cozy sweater, sitting by window, rainy day, (warm lighting:1.2), soft focus background, slice of life",
        "sampler_recomendado": "DPM++ 2M Karras",
        "pasos": 25,
        "cfg": 6,
        "clip_skip": 2,
        "resolucion_recomendada": "936x1536",
        "trigger_words": "masterpiece, 8k, Highest Quality, detail, high resolution, Digital Painting, ultra detailed",
        "coste_energia": "Gratis VIP",
        "limitaciones": "Máx 4 imágenes. Estilo chill/suave, menos indicado para acción intensa o dark fantasy.",
    },
    "Mix Max Cinematic Realism": {
        "nota": 5.0,
        "has_negative": False,
        "is_natural": True,
        "ratios": ["1:1", "1:2", "2:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["Estándar", "Calidad"],
        "max_imagenes": 8,
        "best_for": "Realismo cinematográfico FLUX. 391K usos. Nota 5.0. Retratos, escenas con iluminación de cine, color grading profesional. Magia de sugerencia integrada.",
        "prompt_formula": "Lenguaje natural descriptivo. Describe la escena como un director de fotografía: sujeto, iluminación, color grading, atmósfera.",
        "prompt_ejemplo": "A cinematic portrait of a young woman with windswept hair, golden hour backlight, warm color grading, shallow depth of field, film grain",
        "sampler_recomendado": "Euler",
        "pasos": 25,
        "cfg": 7,
        "coste_energia": "Gratis VIP",
        "limitaciones": "Modelo FLUX: sin negative prompt, sin clip skip. Prompts en lenguaje natural, no tags SD.",
    },

    # ══════════════════════════════════════════════════════════════
    # MODELOS COMFYUI / A1111 / FORGE (LOCALES)
    # ══════════════════════════════════════════════════════════════
    "Juggernaut-XL v9 RunDiffusionPhoto v2": {
        "nota": 4.7, "has_negative": True, "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9", "4:5", "5:4"],
        "max_chars": 2000, "modos_gen": ["Estándar"],
        "best_for": "Fotorrealismo SDXL premium. Excelente para retratos, personas, escenas naturales. Uno de los mejores SDXL para foto realista.",
        "prompt_formula": "Tags SDXL con pesos. cinematic photo, RAW photo, dslr, ultra detailed.",
        "prompt_ejemplo": "(cinematic photo:1.3), 1girl, detailed face, soft natural lighting, shallow DOF, 8K, RAW photo, masterpiece",
        "sampler_recomendado": "DPM++ 2M Karras", "pasos": 30, "cfg": 5,
    },
    "RealVisXL V5.0 fp16": {
        "nota": 4.6, "has_negative": True, "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 2000, "modos_gen": ["Estándar"],
        "best_for": "Hiperrealismo SDXL. Pieles, texturas reales, escenarios fotográficos. Excelente para portraits.",
        "prompt_formula": "RAW photo, photographic style, ultra realistic, professional photography.",
        "prompt_ejemplo": "RAW photo, professional portrait, 1woman, natural skin texture, golden hour lighting, 85mm lens, bokeh background",
        "sampler_recomendado": "DPM++ 2M Karras", "pasos": 30, "cfg": 5,
    },
    "JuggernautXL Ragnarok": {
        "nota": 4.5, "has_negative": True, "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 2000, "modos_gen": ["Estándar"],
        "best_for": "Variante de Juggernaut con estética más cinematográfica/fantasy. Bueno para escenas épicas y entornos detallados.",
        "prompt_formula": "Tags SDXL con énfasis en cinematic + fantasy.",
        "prompt_ejemplo": "(epic cinematic shot:1.3), warrior in dramatic landscape, volumetric lighting, intricate armor details, 8K",
        "sampler_recomendado": "DPM++ 2M Karras", "pasos": 30, "cfg": 5,
    },
    "z_image_bf16 (Base)": {
        "nota": 4.4, "has_negative": True, "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1500, "modos_gen": ["Estándar"],
        "best_for": "Z-Image base (no Turbo). Soporta CFG normal, negative prompt y pesos. Buena calidad fotorrealista.",
        "prompt_formula": "Tags con pesos SD tradicional. Acepta prompts complejos.",
        "prompt_ejemplo": "(close-up portrait:1.2), silver hair, detailed eyes, soft studio lighting, 8K, masterpiece",
        "sampler_recomendado": "Euler", "pasos": 25, "cfg": 4,
    },
    "z_image_turbo_bf16 (Turbo)": {
        "nota": 4.6, "has_negative": False, "is_natural": False, "no_weights": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1500, "modos_gen": ["Estándar"],
        "best_for": "Z-Image TURBO local. Rapidísimo (~1s). CFG ~1.0 — ignora negative y pesos. Solo tags limpios.",
        "prompt_formula": "Tags limpios SIN pesos numéricos. SIN negative prompt.",
        "prompt_ejemplo": "close-up portrait, silver hair, detailed skin, soft studio lighting, 8K, masterpiece",
        "sampler_recomendado": "Euler", "pasos": 8, "cfg": 1.0,
        "limitaciones": "Modelo TURBO: ignora negative prompt y pesos numéricos. Solo tags limpios.",
    },
    "zImageBase_base": {
        "nota": 4.3, "has_negative": True, "is_natural": False,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 1500, "modos_gen": ["Estándar"],
        "best_for": "Z-Image Base alternativo. Soporta negative y pesos. Calidad similar a z_image_bf16.",
        "prompt_formula": "Tags con pesos SD tradicional.",
        "prompt_ejemplo": "(detailed portrait:1.2), 1girl, professional lighting, sharp focus, 8K",
        "sampler_recomendado": "Euler", "pasos": 25, "cfg": 4,
    },
    "flux-2-klein-base-4b-fp8": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 2500, "modos_gen": ["Estándar"],
        "best_for": "FLUX 2 Klein base 4B (versión cuantizada fp8). Lenguaje natural descriptivo. Sin negative prompt.",
        "prompt_formula": "Lenguaje natural en prosa fluida. Describe escena, sujeto, iluminación, cámara, estilo.",
        "prompt_ejemplo": "A photorealistic portrait of a woman with silver hair, soft natural lighting from a window on the left, shallow depth of field, professional photography, 85mm lens",
        "sampler_recomendado": "Euler", "pasos": 20, "cfg": 1.0,
        "limitaciones": "Sin negative prompt. CFG bajo. Solo lenguaje natural.",
    },
    "wan2.2_i2v_high_noise_14B_fp8_scaled": {
        "nota": 4.4, "has_negative": True, "is_natural": True,
        "ratios": ["9:16", "16:9", "1:1"],
        "max_chars": 1500, "modos_gen": ["Estándar"],
        "best_for": "Wan 2.2 Image-to-Video (high noise). 14B parámetros fp8. Convierte imagen estática en vídeo de 5s. Animación más expresiva (high noise = más movimiento).",
        "prompt_formula": "Lenguaje natural describiendo el MOVIMIENTO que quieres añadir a la imagen. Cámara, sujeto, transiciones.",
        "prompt_ejemplo": "Camera slowly zooms in, subject's hair gently moves with the wind, leaves fall in the background",
        "sampler_recomendado": "Euler", "pasos": 20, "cfg": 5,
        "limitaciones": "Solo Image-to-Video. Necesita imagen base. 5s de duración.",
    },
    "wan2.2_i2v_low_noise_14B_fp8_scaled": {
        "nota": 4.4, "has_negative": True, "is_natural": True,
        "ratios": ["9:16", "16:9", "1:1"],
        "max_chars": 1500, "modos_gen": ["Estándar"],
        "best_for": "Wan 2.2 Image-to-Video (low noise). Animación más sutil y conservadora (low noise = movimiento mínimo, mantiene fielmente la imagen base).",
        "prompt_formula": "Lenguaje natural describiendo movimientos sutiles. Ideal para parallax, viento suave, miradas.",
        "prompt_ejemplo": "Subtle breathing motion, slight head tilt, soft eye blink, minimal background sway",
        "sampler_recomendado": "Euler", "pasos": 20, "cfg": 4,
        "limitaciones": "Movimiento limitado por diseño. Para animaciones más dinámicas usar high_noise.",
    },
    "qwen_image_edit_2509_fp8_e4m3fn": {
        "nota": 4.3, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9"],
        "max_chars": 2000, "modos_gen": ["Estándar"],
        "best_for": "Qwen Image Edit (Septiembre 2025). Modelo de edición tipo InstructPix2Pix. Recibe imagen + instrucción de edición en lenguaje natural.",
        "prompt_formula": "Instrucción de edición en lenguaje natural. 'change X to Y', 'add Z', 'make it more...'.",
        "prompt_ejemplo": "Change the dress color to red, add soft sunset lighting, make the background more blurred",
        "sampler_recomendado": "Euler", "pasos": 25, "cfg": 4,
        "limitaciones": "Solo edición de imagen. Necesita imagen base. No genera desde cero.",
    },
    "ltx-2.3-22b-dev-fp8": {
        "nota": 4.7, "has_negative": True, "is_natural": True,
        "ratios": ["16:9", "9:16", "1:1", "1280x720", "1920x1080", "2560x1440"],
        "max_chars": 2500, "modos_gen": ["Estándar", "Quality"],
        "best_for": "LTX-Video 2.3 dev (22B fp8). El mejor open-source para Text-to-Video y Image-to-Video. Soporta 2K y 50fps. Audio sincronizado opcional, vídeo vertical nativo (1080×1920), text rendering mejorado, prompt adherence top.",
        "prompt_formula": "MUY ESPECÍFICO: Mantén el prompt a 1-2 acciones máximo (más de eso confunde al modelo). Estructura: [sujeto] + [acción concreta] + [movimiento de cámara] + [iluminación] + [estilo]. Resolución debe ser divisible por 32. Frames: 8n+1 (ej: 121 frames). Específica resolución target desde el inicio (no upscalear después).",
        "prompt_ejemplo": "A woman walks through misty forest, camera slowly zooms in, soft morning light filtering through trees, cinematic style. [resolution: 1280x720, 121 frames, 24fps]",
        "sampler_recomendado": "LTX Sampler", "pasos": 30, "cfg": 4,
        "limitaciones": "REQUIERE 32GB+ VRAM (versión bf16) o fp8 para 16-24GB. Negative recomendado: 'worst quality, inconsistent motion, blurry, jittery, distorted, watermarks'. Prompts demasiado largos empeoran resultado. Resolución debe ser múltiplo de 32.",
    },
    "svd": {
        "nota": 4.0, "has_negative": False, "is_natural": True,
        "ratios": ["16:9", "9:16", "1:1"],
        "max_chars": 800, "modos_gen": ["Estándar"],
        "best_for": "Stable Video Diffusion (SVD). Image-to-Video. Genera 14-25 frames a partir de una imagen estática. Movimiento sutil.",
        "prompt_formula": "Casi sin texto — funciona principalmente con la imagen de entrada. Prompt mínimo.",
        "prompt_ejemplo": "Subtle camera motion, gentle background movement",
        "sampler_recomendado": "Euler", "pasos": 25, "cfg": 2.5,
        "limitaciones": "Solo Image-to-Video. Movimiento muy sutil. No control fino del prompt.",
    },

    # ══════════════════════════════════════════════════════════════
    # MIDJOURNEY (lenguaje natural + parámetros CLI)
    # Modelos principales: v8.1, v8, v7, v6.1, v6
    # Niji (anime): 7, 6, 5
    # ══════════════════════════════════════════════════════════════
    "Midjourney v8.1": {
        "nota": 5.0, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9", "4:5", "5:4", "21:9", "3:1", "1:3"],
        "max_chars": 4000, "modos_gen": ["Standard", "Turbo", "Relax", "Draft"],
        "best_for": (
            "Modelo más reciente de Midjourney (lanzado 30 abril 2026, default actual). "
            "4-5× más rápido que V7 en jobs estándar. Primer modelo con HD 2K nativo (sin "
            "upscale). Mejor lectura de prompt, retención de detalles pequeños, --raw para "
            "más adherencia. Ideal para: arte conceptual de máxima calidad, fotografía "
            "profesional editorial, branding corporativo, marketing premium, personajes "
            "consistentes con Omni Reference, series narrativas, product shots, wallpapers HD. "
            "Requiere Global V7/V8 Personalization Profile desbloqueado."
        ),
        "prompt_formula": (
            "Lenguaje natural en frases completas (no keywords). ORDEN: scene/setting → "
            "subject → action → style/medium → lighting → mood → camera/lens → composition. "
            "Parámetros al final, todos opcionales:\n"
            "  --ar X:Y → ratio (1:1 hasta 4:1 panorámico)\n"
            "  --v 8.1 → fuerza versión (default si está en settings)\n"
            "  --hd → activa salida HD 2K\n"
            "  --raw → elimina estilo MJ por defecto (más fotográfico)\n"
            "  --stylize 0-1000 (default 100) → fuerza del estilo MJ\n"
            "  --chaos 0-100 (default 0) → variedad entre los 4 results\n"
            "  --weird 0-3000 → composiciones extrañas/únicas\n"
            "  --q .25/.5/1/2 → tiempo de render (más = más detalle)\n"
            "  --sref [url/code] → referencia de estilo\n"
            "  --oref [url] → personaje consistente (V7/V8)\n"
            "  --p [code] → personalization profile\n"
            "  --no [items] → exclusión (equivalente a negative)\n"
            "  --seed N → reproducibilidad"
        ),
        "prompt_ejemplo": (
            "Cinematic portrait of an elderly fisherman mending nets on a wooden boat at "
            "golden hour, weathered hands and face full of stories, soft warm light from "
            "the setting sun, deep blue ocean in the background, shot on 35mm film with "
            "shallow depth of field --ar 16:9 --stylize 250 --raw --no boat name, watermark, text"
        ),
        "limitaciones": (
            "Plan gratuito: NO existe (Midjourney retiró el free trial; Basic desde $10/mes). "
            "Sin negative tradicional (usar --no). Sin pesos numéricos estilo SD. Solo "
            "Discord o midjourney.com. Text rendering mejor que V7 pero no perfecto. "
            "Aspect ratios >2:1 marcados experimentales. --sv 6 con Style References cuesta "
            "4× más GPU. --hd y --q 4 cuestan 4× más GPU cada uno; combinados, 16× más."
        ),
    },
    "Midjourney v8": {
        "nota": 4.9, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9", "4:5", "5:4", "21:9", "3:1", "1:3"],
        "max_chars": 4000, "modos_gen": ["Fast"],
        "best_for": (
            "V8.0 Alpha (lanzado 17 marzo 2026 en alpha.midjourney.com). Primera "
            "iteración V8, todavía disponible tiempo limitado pero V8.1 es el modelo "
            "activamente mejorado. Útil para A/B testing entre V8.0 y V8.1, o para "
            "mantener consistencia con jobs anteriores hechos con V8.0."
        ),
        "prompt_formula": (
            "Misma estructura que V8.1 (NL + CLI). ORDEN: scene → subject → style → "
            "lighting → mood → camera. Parámetros principales: --ar, --stylize, --chaos, "
            "--weird, --sref, --oref, --p, --no, --seed. NO admite --raw como V8.1."
        ),
        "prompt_ejemplo": (
            "Hyperrealistic macro shot of a dewdrop on a vibrant rose petal at dawn, "
            "soft morning light, intricate reflections inside the droplet, shallow depth "
            "of field --ar 1:1 --stylize 500"
        ),
        "limitaciones": (
            "SOLO Fast mode (no Relax ni Turbo). --sv 6 con Style References y Moodboards "
            "cuesta 4× más GPU y no funciona con --hd ni --q 4. V8.1 ya tiene todas las "
            "mejoras y es 4-5× más rápido. Disponible tiempo limitado: migra a V8.1 si puedes."
        ),
    },
    "Midjourney v7": {
        "nota": 4.8, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9", "4:5", "5:4", "21:9", "3:1", "1:3"],
        "max_chars": 4000, "modos_gen": ["Standard", "Turbo", "Relax", "Draft"],
        "best_for": (
            "Lanzado 3 abril 2025, default desde 17 junio 2025 hasta abril 2026. Modelo "
            "muy estable y maduro. Textos e imagen-prompts manejados con precisión, calidad "
            "visual con texturas ricas y detalles coherentes (especialmente cuerpos, manos, "
            "objetos). Introduce DRAFT MODE (10× más rápido para iteración) y OMNI REFERENCE "
            "(personajes/objetos consistentes entre generaciones). 85% de usuarios prefieren "
            "V7 sobre V6.1. Sigue siendo opción muy sólida si V8.1 da problemas o resulta caro."
        ),
        "prompt_formula": (
            "Lenguaje natural en frases (no keywords). ORDEN: scene → subject → style → "
            "lighting → mood → camera. Parámetros: --ar, --v 7, --stylize 0-1000, --chaos "
            "0-100, --weird 0-3000, --q .25/.5/1/2, --sref [url/code] (estilo), --oref [url] "
            "(personaje), --cref [url] (legacy, mejor usar --oref en V7), --p [code] (profile "
            "personalizado), --no [items] (excluir), --draft (Draft Mode), --raw (sin estilo "
            "default MJ), --seed N."
        ),
        "prompt_ejemplo": (
            "Editorial fashion photograph of a model wearing a flowing red silk dress on an "
            "urban rooftop, soft golden hour backlight, distant city skyline, shot on medium "
            "format film, shallow depth of field --ar 3:4 --stylize 400 --v 7 --raw"
        ),
        "limitaciones": (
            "Sin negative tradicional (usar --no). Sin pesos numéricos. Slightly slower than "
            "V8.1 (4-5× diferencia). Personalization profile recomendado para mejores resultados. "
            "Draft Mode útil para explorar antes de pasar a Standard. V8.1 es superior en text "
            "rendering y velocidad."
        ),
    },
    "Midjourney v6.1": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9", "4:5", "5:4", "21:9"],
        "max_chars": 4000, "modos_gen": ["Standard", "Turbo", "Relax"],
        "best_for": (
            "Lanzado 30 julio 2024, default hasta 16 junio 2025. 25% más rápido que V6. "
            "Coherencia mejorada de detalles y texturas. Aún ampliamente usado por su "
            "balance velocidad/calidad y estilo artístico característico de Midjourney. "
            "Ideal para arte conceptual, ilustración, posters, social media, cuando quieres "
            "el 'look' clásico MJ pintado/cinematográfico. Más estable que V7 en algunos "
            "estilos artísticos específicos. --cref (Character Reference) original aquí."
        ),
        "prompt_formula": (
            "Lenguaje natural descriptivo (más keyword-friendly que V7/V8). ORDEN: scene → "
            "subject → style → lighting → mood. Parámetros: --v 6.1, --ar X:Y, --stylize "
            "100-1000 (más alto = más estilo MJ), --chaos 0-100, --no [exclusions], --cref "
            "[url] --cw 0-100 (character weight), --sref [url/code] (style reference), --q "
            ".25/.5/1, --seed N. NO admite --oref ni --draft ni --raw (son V7+)."
        ),
        "prompt_ejemplo": (
            "Cinematic portrait of an elderly fisherman at sunset, weathered face, deep blue "
            "ocean background, golden hour lighting, shot on 35mm film, painterly photographic "
            "style --ar 16:9 --stylize 250 --v 6.1 --no boat, watermark"
        ),
        "limitaciones": (
            "Sin negative tradicional (usar --no). Sin --raw (estilo MJ siempre presente, "
            "para fotografía pura V7+ es mejor). --cref menos potente que --oref de V7. Sin "
            "Draft Mode (iteración más lenta). V7/V8.1 superiores en prompt understanding "
            "complejo. Buen fallback si V8.1 da resultados inesperados."
        ),
    },
    "Midjourney v6": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9", "4:5", "5:4"],
        "max_chars": 4000, "modos_gen": ["Standard", "Turbo", "Relax"],
        "best_for": (
            "Lanzado diciembre 2023. Primera versión con mejor prompt accuracy en inputs "
            "largos y coherence mejorada. Legacy pero aún disponible. Útil para mantener "
            "consistencia con trabajos antiguos hechos en V6, o cuando V6.1 da artifacts "
            "específicos no presentes en V6. Estilo MJ ligeramente más pictórico que V6.1."
        ),
        "prompt_formula": (
            "Lenguaje natural más keyword-friendly. ORDEN: scene → subject → details → "
            "style → lighting. Parámetros: --v 6, --ar X:Y, --stylize 0-1000, --chaos 0-100, "
            "--no [exclusions], --cref [url], --q .25/.5/1, --seed N. Funciona bien con "
            "weights y multi-prompts usando ::."
        ),
        "prompt_ejemplo": (
            "A serene Japanese garden in spring with cherry blossoms in full bloom, a koi "
            "pond with orange fish, traditional wooden bridge, soft morning mist, ukiyo-e "
            "inspired painterly style --ar 16:9 --stylize 200 --v 6"
        ),
        "limitaciones": (
            "Legacy. V6.1, V7 y V8.1 superiores en casi todo. Sin --oref, sin --draft, sin "
            "--raw, sin --hd. Menor coherencia en manos/cuerpos vs V7. Usar solo si "
            "necesitas reproducir el look específico de V6 o continuar series antiguas."
        ),
    },

    # ── Niji (Anime) ──────────────────────────────────────────────

    "Niji 7": {
        "nota": 4.9, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9", "4:5", "5:4", "21:9"],
        "max_chars": 4000, "modos_gen": ["Standard", "Turbo", "Relax"],
        "best_for": (
            "Lanzado 9 enero 2026. Modelo especializado en anime/manga, la línea Niji "
            "actual. Mejoras clave: ojos crystal-clear, reflejos, detalles finos de fondo, "
            "coherencia mejorada en poses complejas y multi-arm setups, interpretación "
            "MÁS LITERAL del prompt (respeta colores específicos y peinados exactos), "
            "mejor text rendering Japanese, mejor --sref performance. Soporta Personalization "
            "y Moodboards. Perfecto para: anime/manga art, ilustraciones japonesas, "
            "character design, wallpapers, game assets, illustration commercial work."
        ),
        "prompt_formula": (
            "Lenguaje natural + CLI (misma sintaxis que MJ). ORDEN: character/subject → "
            "outfit/style → pose/action → scene → details (hair color, eye color, expression) "
            "→ mood. Parámetros: --niji 7, --ar X:Y, --stylize 0-1000, --sref [url/code], "
            "--cref [url] (Niji 6/V6-era control; en Niji 7 algunas implementaciones todavía "
            "lo usan), --p [code] (Personalization), --no [items], --seed N. Más literal que "
            "Niji 6: prompts vagos dan resultados diferentes a Niji 6/5."
        ),
        "prompt_ejemplo": (
            "Beautiful anime girl with long silver hair tied in a ponytail, large expressive "
            "violet eyes, wearing a traditional Japanese school uniform, cherry blossom "
            "petals falling around her, soft afternoon light, detailed background of a "
            "Japanese garden --niji 7 --ar 3:4 --stylize 500 --no background clutter, watermark"
        ),
        "limitaciones": (
            "Solo anime/ilustración (NO usar para fotorrealismo). Interpretación más literal: "
            "prompts vagos rinden distinto que Niji 6. --cref en Niji 7 es Niji 6/V6-era "
            "(no V7-path completo). Sin --oref nativo. Sin --raw. Plan gratuito no existe "
            "(igual que Midjourney general)."
        ),
    },
    "Niji 6": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9", "4:5", "5:4"],
        "max_chars": 4000, "modos_gen": ["Standard", "Turbo", "Relax"],
        "best_for": (
            "Lanzado junio 2024. Default Niji hasta enero 2026. Japanese text rendering "
            "mejorado (kana, kanji básicos, Chinese simple). Mejor estructura de ojos anime "
            "vs Niji 5. Menos artifacts. Sigue siendo buena opción para diseño de personajes "
            "con texto japonés visible (signage, manga panels, posters anime). Estilo "
            "ligeramente más estilizado/expresivo que Niji 7 (que es más literal)."
        ),
        "prompt_formula": (
            "Lenguaje natural anime-focused. ORDEN: character → outfit → scene → style → "
            "mood. Parámetros: --niji 6, --ar X:Y, --stylize 0-1000, --cref [url] (Character "
            "Reference, funciona bien), --sref [url/code], --no [items], --q .25/.5/1, "
            "--seed N. Acepta multi-prompts con :: para weight."
        ),
        "prompt_ejemplo": (
            "Anime warrior princess with flowing white dress and silver armor, holding a "
            "katana, standing on a cliff overlooking a stormy ocean, dramatic clouds, "
            "epic cinematic lighting, manga illustration style --niji 6 --ar 16:9 --stylize 300"
        ),
        "limitaciones": (
            "Niji 7 superior en coherencia, ojos, multi-poses y --sref. Sin Personalization "
            "completa (Niji 7 sí). Más estilizado que Niji 7 (puede ser pro o contra según "
            "uso). Sin --oref."
        ),
    },
    "Niji 5": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9", "4:5", "5:4"],
        "max_chars": 4000, "modos_gen": ["Standard", "Turbo", "Relax"],
        "best_for": (
            "Lanzado abril 2023. Modelo Niji clásico con --style parameters muy expresivos: "
            "--style cute (adorable, infantil, kawaii), --style expressive (sofisticado, "
            "detallado, expresivo), --style original (Niji V5 default, balanced), --style "
            "scenic (cinematic backgrounds, escenarios épicos). Legacy pero útil para "
            "conseguir looks anime específicos que Niji 6/7 no replican exactamente."
        ),
        "prompt_formula": (
            "Anime scene + character + style modifier. Parámetros distintivos de Niji 5: "
            "--niji 5, --style cute/expressive/original/scenic (CRÍTICO en esta versión), "
            "--ar X:Y, --stylize 0-1000, --no [items], --seed N. El --style elegido cambia "
            "drásticamente el resultado, más que en Niji 6/7."
        ),
        "prompt_ejemplo": (
            "Cute chibi anime girl with pink twin-tails in a magical forest, surrounded by "
            "small glowing fairies and floating mushrooms, soft pastel colors, dreamy "
            "atmosphere --niji 5 --style cute --ar 1:1 --stylize 200"
        ),
        "limitaciones": (
            "Legacy. Niji 6 y 7 superiores en coherencia, detalles y prompt understanding. "
            "Sin --cref ni --sref ni --oref. Sin Personalization. Los --style flags pueden "
            "ignorarse en algunos casos. Útil solo para reproducir el look específico V5."
        ),
    },

    # ══════════════════════════════════════════════════════════════
    # ChatGPT / GPT Image (OpenAI oficial)
    # DALL-E 2 y 3 retirados de la API el 12 de mayo de 2026.
    # Familia GPT Image: 1 (Abr 2025), 1 mini, 1.5 (Nov 2025), 2 (Abr 2026).
    # ══════════════════════════════════════════════════════════════
    "GPT Image 1": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "1024x1024", "1024x1536", "1536x1024"],
        "max_chars": 4000, "modos_gen": ["Low", "Medium", "High"],
        "best_for": (
            "Primer GPT Image (Abril 2025). Modelo nativo multimodal de GPT-4o. "
            "Excelente integración con ChatGPT, mejor que DALL-E 3 en text-in-image, "
            "composición compleja y world knowledge. Famoso por estilo Studio Ghibli "
            "viral. Disponible en API (gpt-image-1) y ChatGPT. Requiere verificación "
            "de organización en la API. Casos de uso destacados: ilustración con texto, "
            "personajes con specs detalladas, prototipos UI, posters, branding visual."
        ),
        "prompt_formula": (
            "Lenguaje natural en prosa fluida. Estructura: background/scene → subject "
            "→ key details → constraints + intended use (ad, UI, infographic). "
            "Para texto literal: usar comillas, e.g. 'with the words \"Hello World\"'. "
            "Soporta specs muy largas tipo character sheet (rasgos físicos, paleta, "
            "movimiento, mood). Para fondo transparente: incluir 'on a transparent "
            "background' (auto-detecta y aplica transparency en PNG/WebP)."
        ),
        "prompt_ejemplo": (
            "Create a photorealistic portrait of an elderly sailor on a fishing boat "
            "at dawn, weathered face, soft coastal light, 35mm film aesthetic, "
            "medium close-up at eye level"
        ),
        "limitaciones": (
            "Warm color bias en muchas salidas. Sin negative prompt. Cropping "
            "prematuro a veces. Sin pesos numéricos. Resolución máxima ~1024px. "
            "Edición: soporta hasta 10 imágenes input + máscara con alpha channel "
            "(para edición localizada). Parámetro 'input_fidelity=high' preserva "
            "caras, logos y texturas con más detalle (primera imagen retiene mejor). "
            "Precio: ~$0.02 low / ~$0.07 medium / ~$0.19 high (1024x1024)."
        ),
    },
    "GPT Image 1 mini": {
        "nota": 4.2, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "1024x1024", "1024x1536", "1536x1024"],
        "max_chars": 4000, "modos_gen": ["Low", "Medium"],
        "best_for": (
            "GPT Image 1 mini (2026). Versión optimizada para coste y velocidad. "
            "Ideal para alto volumen, prototipado, iteración rápida y workflows "
            "automatizados donde el coste por imagen importa más que la fidelidad "
            "máxima. Mantiene la capacidad multimodal de GPT Image 1."
        ),
        "prompt_formula": (
            "Igual que GPT Image 1 pero prefiere prompts más cortos y directos. "
            "Estructura: subject + scene + 2-3 detalles clave. Evita prompts muy "
            "complejos con muchas restricciones simultáneas."
        ),
        "prompt_ejemplo": (
            "A friendly cartoon mascot for a coffee app, smiling coffee cup with "
            "arms and legs, holding a tablet, flat vector style, warm orange and "
            "brown palette, simple background"
        ),
        "limitaciones": (
            "Solo modos Low y Medium (no High). Menos detalle fino que GPT Image 1 "
            "full. Sin negative. ~3-5× más barato por imagen que GPT Image 1. "
            "Recomendado para tareas que no requieran 4K ni text rendering complejo."
        ),
    },
    "GPT Image 1.5": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "1024x1024", "1024x1536", "1536x1024", "9:16", "16:9"],
        "max_chars": 4000, "modos_gen": ["Low", "Medium", "High"],
        "best_for": (
            "GPT Image 1.5 (Noviembre 2025). 4× más rápido que GPT Image 1. "
            "Mejor edición de imagen preservando detalles (lighting, composición, "
            "rostros). Adherencia a instrucciones reforzada. Inputs/outputs ~20% "
            "más baratos. EXCELENTE para edición precisa con input_fidelity=high: "
            "item edits (cambiar color de un objeto sin tocar resto), element "
            "removal (quitar limpio), element addition (insertar nuevo natural), "
            "face preservation (mantener identidad en variaciones), branding "
            "consistency (logo sin distorsión), product photography (mismo "
            "producto en nuevos fondos), fashion (cambiar outfit sin alterar pose). "
            "Ideal para ecommerce, branding, story sequences, avatares consistentes."
        ),
        "prompt_formula": (
            "Lenguaje natural estructurado. Para edición: 'Change X to Y, keep Z "
            "intact'. Para generación: scene → subject → details → style → "
            "constraints. Reseteo de identidad facial: 'maintain the same person'. "
            "Cuando se editan múltiples caras: combina las fotos en un canvas único "
            "antes de enviar (la primera imagen del input preserva más fidelidad)."
        ),
        "prompt_ejemplo": (
            "Edit this product photo: change the background to a clean white "
            "studio with soft shadows, keep the product, lighting and proportions "
            "exactly as they are, photorealistic"
        ),
        "limitaciones": (
            "Sigue sin negative prompt ni pesos. Algunas regresiones en estilos "
            "artísticos respecto a GPT Image 1. Resolución máxima ~1024px (no 4K). "
            "input_fidelity=high consume más tokens de input pero crítico para "
            "preservar caras y logos. Output formats: PNG, JPEG, WebP."
        ),
    },
    "GPT Image 2": {
        "nota": 4.9, "has_negative": False, "is_natural": True,
        "ratios": [
            "1:1", "2:3", "3:2", "9:16", "16:9", "4:5", "5:4",
            "1024x1024", "1536x1024", "1024x1536",
            "2048x2048", "2048x1152", "3840x2160 (4K)",
        ],
        "max_chars": 5000, "modos_gen": ["Low", "Medium", "High"],
        "best_for": (
            "GPT Image 2 (Abril 2026). Modelo OpenAI más reciente y capaz. "
            "Primero con razonamiento O-series integrado (Understand→Plan→Generate→Review). "
            "Destacado por: (1) text rendering casi perfecto en posters, signage, "
            "labels y UI; (2) realismo natural en piel, materiales, iluminación; "
            "(3) prompt understanding superior con múltiples requisitos; "
            "(4) consistencia entre generaciones (series, campañas, story boards); "
            "(5) RESOLUCIÓN NATIVA HASTA 4K (3840×2160); "
            "(6) HIGH FIDELITY AUTOMÁTICO en imágenes de referencia (no necesita "
            "el parámetro input_fidelity explícito como GPT Image 1/1.5); "
            "(7) hasta 5 imágenes de referencia + máscara para edición composite "
            "('subject from img1 + scene from img2 + style from img3'). "
            "Ideal para marketing profesional, UI/app mockups, product shots, "
            "fotorrealismo editorial, posters de cine, wallpapers."
        ),
        "prompt_formula": (
            "Lenguaje natural estructurado. ORDEN: subject → scene/setting → "
            "lighting → style/mood → composition → exact text (entre comillas si "
            "aparece en la imagen). Para texto literal: 'with the words \"...\"'. "
            "Para UI/mockups: indicar tipo de pantalla, elementos de interfaz, "
            "estado. Para realismo: pedir lens (35mm, 50mm), DOF, grain, texturas. "
            "Para edición composite: 'subject from img1, scene from img2, style "
            "from img3'. Para fondos transparentes: incluir 'transparent background' "
            "en el texto (en GPT Image 2 ya no se acepta el parámetro background=transparent)."
        ),
        "prompt_ejemplo": (
            "Photorealistic marketing banner for a coffee brand. Subject: a "
            "ceramic cup of espresso on a wooden table at golden hour. Soft "
            "natural light coming from the left, visible steam, reflections on "
            "the cup, shallow depth of field. Above the cup, clean modern "
            "typography with the words \"Morning Ritual\" in dark brown sans-serif. "
            "Composition: rule of thirds, cup bottom-left, copy upper-right. "
            "Cinematic still, 50mm lens, soft film grain."
        ),
        "limitaciones": (
            "Sin negative prompt ni pesos (no aplican sintaxis SD). Solo n=1 por "
            "llamada en API (lanzar requests paralelas para múltiples). Tiempo: "
            "high quality + 2K/4K puede tardar 3-5 minutos (timeout recomendado "
            "≥360s, exponential backoff en 5xx). Resoluciones >2560×1440 marcadas "
            "experimentales. NO admite parámetro 'background=transparent' (usar "
            "post-procesado). NO usar input_fidelity (auto-forzado high; el "
            "parámetro genera error). Precio: ~$0.006 low / $0.053 medium / "
            "$0.211 high (1024×1024); 4K alta sube a ~$0.41/imagen."
        ),
    },

    # ══════════════════════════════════════════════════════════════
    # IDEOGRAM / RECRAFT
    # ══════════════════════════════════════════════════════════════
    "Ideogram v3": {
        "nota": 4.8, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "16:10", "10:16", "3:2", "2:3"],
        "max_chars": 2000, "modos_gen": ["Default", "Quality", "Turbo"],
        "best_for": "Líder en text-in-image. Rendering de tipografías, logos, posters. Estilo References hasta 3 imágenes. 4.3B presets de estilo. Mejor para diseño gráfico, branding, social media con texto visible.",
        "prompt_formula": "Lenguaje natural descriptivo. Máx ~150-160 palabras. Texto entre comillas. Estructura: [Image summary]. [Main subject], [Pose], [Setting], [Lighting], [Style], [Technical enhancers]",
        "prompt_ejemplo": 'A vintage 1970s rock concert poster with bold typography saying "MIDNIGHT TOUR" in golden letters, psychedelic background with swirling colors, retro design, warm tones, professional typography, concert photography style',
        "prompt_tips": [
            "ESCRIBE EN INGLÉS: Para resultados más fiables (especialmente con texto), usa inglés.",
            "NATURAL LANGUAGE: Escribe como le explicarías la imagen a otra persona. Full sentences.",
            "TEXTO EN COMILLAS: Para texto visible, ponlo entre comillas dobles.",
            "ORDEN IMPORTANTE: Lo más importante va al principio, hasta 150-160 palabras.",
            "NO PESOS: No uses (palabra:1.5) ni pesos. Describe mejor.",
            "NO FLAGS: No uses --ar, --v, --style. Describe el estilo en texto.",
            "STYLE REFERENCES: Sube hasta 3 imágenes de referencia para controlar estética.",
            "MAGIC PROMPT: Puede expandir tu prompt automáticamente si lo necesitas.",
        ],
        "limitaciones": "Sin negative prompt. Máx ~150-160 palabras. Scripts no latinos (árabe, chino) pueden renderizar mal.",
    },
    "Recraft v3": {
        "nota": 4.6, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "2:3", "3:2"],
        "max_chars": 2000, "modos_gen": ["Standard", "HD"],
        "best_for": "Especializado en arte vectorial, ilustraciones consistentes, branding. Genera SVG editable. Style References hasta 3 imágenes. Ideal para diseñadores.",
        "prompt_formula": "Lenguaje natural + estilo artístico. Mencionar 'flat illustration', 'vector art', 'icon style', 'realistic'.",
        "prompt_ejemplo": "Flat vector illustration of a cozy coffee shop at night, warm color palette, geometric shapes, minimalist design, no gradients, clean lines",
        "prompt_tips": [
            "USA ESTILOS EXPLÍCITOS: 'flat illustration', 'realistic photo', 'vector art'.",
            "SVG OUTPUT: Genera graphics escalables editables.",
            "STYLE REFERENCES: Hasta 3 imágenes de referencia para consistencia.",
            "COMPOSICIÓN ESTRUCTURADA: Excelente para layouts con texto y iconografía.",
        ],
        "limitaciones": "No fotorrealismo. Mejor para gráfico/vectorial. SVG puede necesitar limpieza.",
    },

# ══════════════════════════════════════════════════════════════
    # MAGNIFIC (antes Freepik AI) — TODOS LOS MODELOS DISPONIBLES (Mayo 2026)
    # NOTA: La mayoría NO soporta negative prompt nativo. Solo Classic y Recraft V4 lo soportan.
    # ══════════════════════════════════════════════════════════════
    "Auto (Sugerencias)": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "2:3", "3:2"],
        "max_chars": 4000, "modos_gen": ["Auto"],
        "best_for": "Modo automático de Magnific. Selecciona el mejor modelo según tu prompt y referencias. ~10s de generación. Ideal cuando no sabes qué modelo elegir.",
        "prompt_formula": "Lenguaje natural muy descriptivo. Magnific decide internamente qué modelo usar según contenido.",
        "prompt_ejemplo": "A cinematic portrait of a young woman with auburn hair against a soft blurred forest background, golden hour lighting",
        "limitaciones": "No tienes control sobre qué modelo se usa internamente.",
    },

    # ── OpenAI GPT (en Magnific) ────────────────────────
    "GPT 2": {
        "nota": 4.9, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2", "4:3", "3:4"],
        "max_chars": 2000, "modos_gen": ["Standard", "Quality"],
        "best_for": "GPT Image 2 en Magnific (Destacado/Nuevo). Salida 2K-4K. ~1m 27s. El más reciente con razonamiento integrado, text rendering casi perfecto, fotorrealismo top.",
        "prompt_formula": "Lenguaje natural muy estructurado. Estructura: scene → subject → key details → constraints. Lenguaje fotográfico (lens, lighting, framing) y texturas reales.",
        "prompt_ejemplo": "Photorealistic candid photo of an elderly fisherman on his boat at dawn. Weathered skin with visible pores, sun texture. Adjusting nets, dog nearby. 35mm film aesthetic, 50mm lens, soft coastal daylight, shallow DOF.",
        "prompt_tips": [
            "ESCRIBE EN INGLÉS: Resultados más fiables.",
            "LENGUAJE FOTOGRÁFICO: Menciona lentes, iluminación, profundidad de campo.",
            "TEXTURAS REALES: Describe piel, telas, materiales con detalle.",
            "ESTRUCTURA CLARA: escena → sujeto → detalles → estilo.",
            "MÁX 150-160 PALABRAS: Lo más importante al inicio.",
            "SIN NEGATIVE PROMPT: No funciona aquí.",
            "REFERENCIAS: Soporta hasta varias imágenes de referencia.",
        ],
        "limitaciones": "Lento (~1m 27s). Sin negative ni pesos. Máx ~160 palabras.",
    },
    "GPT 1.5 - High": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2"],
        "max_chars": 2000, "modos_gen": ["High"],
        "best_for": "GPT Image 1.5 alta calidad en Magnific. ~59s. Buena edición de imagen, preserva detalles, branding consistente.",
        "prompt_formula": "Lenguaje natural estructurado. Para edición: 'Change X to Y, keep Z intact'.",
        "prompt_ejemplo": "Edit this product photo: change the background to a clean white studio with soft shadows, keep the product, lighting and proportions exactly as they are",
        "prompt_tips": [
            "EDICIÓN CLARA: 'Change X to Y, keep Z intact'.",
            "REFERENCIAS: Soporta varias imágenes de referencia.",
            "INGLÉS MEJOR: Para resultados más predecibles.",
        ],
        "limitaciones": "Sin negative prompt ni pesos.",
    },
    "GPT 1.5": {
        "nota": 4.6, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2"],
        "max_chars": 2000, "modos_gen": ["Standard"],
        "best_for": "GPT Image 1.5 estándar. ~41s. 4x más rápido que GPT 1, mejor edición, preserva detalles.",
        "prompt_formula": "Lenguaje natural estructurado.",
        "prompt_ejemplo": "Modern poster design with bold typography, minimalist layout, gradient background, professional design",
        "limitaciones": "Sin negative ni pesos.",
    },
    "GPT 1 - HQ": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 2000, "modos_gen": ["HQ"],
        "best_for": "GPT Image 1 alta calidad. ~1m 3s. Modelo viral por estilo Studio Ghibli. Excelente integración multimodal.",
        "prompt_formula": "Lenguaje natural en prosa. Estructura: scene → subject → details → style.",
        "prompt_ejemplo": "Studio Ghibli style illustration of a young girl walking through a field of sunflowers at dusk, soft warm light, dreamy atmosphere",
        "prompt_tips": [
            "PROSA NATURAL: Escribe en oraciones completas.",
            "ESTILO ARTÍSTICO: Menciona estilos como 'Studio Ghibli', 'Pixar', etc.",
            "EMOCIÓN Y ATMÓSFERA: Describe el mood además de lo visual.",
        ],
        "limitaciones": "Lento (~1m 3s). Warm color bias. Sin negative ni pesos.",
    },
    "GPT": {
        "nota": 4.3, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 1500, "modos_gen": ["Standard"],
        "best_for": "GPT Image base. ~40s. Versión rápida y económica.",
        "prompt_formula": "Lenguaje natural simple. Soporta referencias.",
        "prompt_ejemplo": "A vibrant illustration of a cyberpunk cat in a neon-lit alleyway, colorful, detailed",
        "limitaciones": "Calidad inferior a GPT 1.5/2. Sin negative.",
    },

    # ── Familia Flux ─────────────────────────────────────
    "Flux.2 Max": {
        "nota": 4.8, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2", "4:3", "3:4"],
        "max_chars": 2000, "modos_gen": ["Max"],
        "best_for": "Flux 2 Max en Magnific. Salida 2K. ~38s. Máxima calidad de la familia Flux 2. Ideal para hero shots, branding crítico.",
        "prompt_formula": "Lenguaje natural muy descriptivo y específico. Flux 2 entiende prompts complejos con múltiples sujetos y relaciones espaciales.",
        "prompt_ejemplo": "A high-end fashion editorial photograph of a model standing in a brutalist concrete corridor, dramatic side lighting from a single skylight, wearing a sculptural black dress, photorealistic, magazine quality",
        "prompt_tips": [
            "DESCRIPTIVO Y ESPECÍFICO: Flux 2 entiende prompts complejos.",
            "MULTIPLES SUJETOS: Maneja composiciones con varios elementos.",
            "RELACIONES ESPACIALES: Describe posiciones y direcciones con precisión.",
            "ILUMINACIÓN DRAMÁTICA: Funciona muy bien con descripciones de luz.",
        ],
        "limitaciones": "Sin negative ni pesos. Más lento que Pro.",
    },
    "Flux.2 Pro": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2", "4:3", "3:4"],
        "max_chars": 2000, "modos_gen": ["Pro"],
        "best_for": "Flux 2 Pro. Salida 2K. ~22s. Producción profesional, alta resolución, fotorrealismo top, hasta 10 imágenes ref. Para uso comercial intensivo.",
        "prompt_formula": "Lenguaje natural fluido + tipografía explícita si necesitas texto. Hasta 10 referencias.",
        "prompt_ejemplo": "Professional product photo of a luxury watch on dark velvet, soft directional lighting from upper left, macro detail, sharp focus on dial, depth of field",
        "prompt_tips": [
            "HASTA 10 REFERENCIAS: Usa múltiples imágenes para controlar estilo.",
            "TIPOGRAFÍA: Describe explícitamente si necesitas texto visible.",
            "FLUIDO Y DESCRIPTIVO: No necesitas estructura rígida.",
        ],
        "limitaciones": "Sin negative ni pesos.",
    },
    "Flux.2 Flex": {
        "nota": 4.6, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2"],
        "max_chars": 2000, "modos_gen": ["Flex"],
        "best_for": "Flux 2 Flex. Salida 2K. ~25s. Especializado en TIPOGRAFÍA y detalles finos. El mejor cuando el texto en imagen es crítico.",
        "prompt_formula": "Para texto: usar comillas y describir tipografía explícitamente. 'Bold serif typeface', 'handwritten script', etc.",
        "prompt_ejemplo": 'Vintage diner sign with the text "DINER" in bold red retro typography, neon accent, weathered metal background, 1950s aesthetic',
        "prompt_tips": [
            "TEXTO EN COMILLAS: \"TU TEXTO AQUÍ\" para texto visible.",
            "TIPOGRAFÍA EXPLÍCITA: Describe fuente, peso, estilo.",
            "MEJOR PARA TEXTO: Que otros Flux para renderizar palabras.",
        ],
        "limitaciones": "Optimizado para texto. Para foto pura, Pro o Max son mejores.",
    },
    "Flux.2 Klein": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 1500, "modos_gen": ["Klein"],
        "best_for": "Flux 2 Klein. Salida 2K. ⚡ ~7s (RÁPIDO). Compacto para generación en tiempo real. Para iteración rápida.",
        "prompt_formula": "Lenguaje natural conciso. Optimizado para velocidad.",
        "prompt_ejemplo": "A red apple on a wooden table, soft natural light from the right, photorealistic",
        "prompt_tips": [
            "CONCISO: Prompts más cortos funcionan mejor.",
            "VELOCIDAD: Ideal para iterar y probar ideas rápido.",
            "NATURAL PERO BREVE: No necesitas essays.",
        ],
        "limitaciones": "Calidad menor que Pro/Max pero muy rápido.",
    },
    "Flux.1 Kontext Max": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2"],
        "max_chars": 2000, "modos_gen": ["Max"],
        "best_for": "Flux 1 Kontext Max. ~18s. Modelo de EDICIÓN avanzada. Preserva contexto entre ediciones múltiples.",
        "prompt_formula": "Instrucciones de edición específicas: 'Change [elemento] to [nuevo]', 'Keep [elemento] exactly the same', 'Add [elemento] to [posición]'.",
        "prompt_ejemplo": "Change the woman's dress from red to emerald green, keep her face, hair, pose and lighting exactly the same",
        "prompt_tips": [
            "EDICIÓN ESPECÍFICA: Change X to Y, keep Z.",
            "PRESERVA CONTEXTO: Funciona mejor con múltiples ediciones.",
            "REFERENCIAS: Soporta imágenes de referencia para estilo.",
        ],
        "limitaciones": "Especializado en edición. Para generación desde cero, otros Flux son mejores.",
    },
    "Flux.1 Kontext Pro": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 1500, "modos_gen": ["Pro"],
        "best_for": "Flux 1 Kontext Pro. ~13s. Edición rápida con preservación de contexto.",
        "prompt_formula": "Instrucciones de edición concisas y específicas.",
        "prompt_ejemplo": "Add subtle bokeh background blur, keep subject sharp",
        "limitaciones": "Para edición. Más rápido que Max pero menos preciso.",
    },
    "Flux.1 Realism": {
        "nota": 4.6, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2"],
        "max_chars": 1500, "modos_gen": ["Realism"],
        "best_for": "Flux 1 Realism. ⚡ ~8s. Optimizado para FOTORREALISMO. Pieles, texturas, escenarios fotográficos.",
        "prompt_formula": "Lenguaje natural fotográfico. Mencionar lente, distancia focal, tipo de cámara mejora resultados.",
        "prompt_ejemplo": "Candid photograph of a barista preparing coffee, shallow depth of field, 50mm lens, natural window light, film grain",
        "prompt_tips": [
            "LENGUAJE FOTOGRÁFICO: 50mm, f/1.8, shallow DOF, etc.",
            "TEXTURAS REALES: Piel con poros, tela con textura, etc.",
            "REFERENCIAS: Funcionan muy bien para realismo.",
        ],
        "limitaciones": "Para arte estilizado, Flux 2 Max es mejor.",
    },
    "Flux.1 Fast": {
        "nota": 4.3, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 1000, "modos_gen": ["Fast"],
        "best_for": "Flux 1 Fast. ⚡ ~8s. Velocidad máxima en familia Flux 1. Ideal para iteración rápida y exploración.",
        "prompt_formula": "Prompts cortos y directos.",
        "prompt_ejemplo": "A cat in a garden, golden hour light",
        "limitaciones": "Calidad más baja que Realism o 1.1.",
    },
    "Flux.1.1": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 1500, "modos_gen": ["Standard"],
        "best_for": "Flux 1.1 ULTRA RÁPIDO. ⚡ ~6s. Mejorado respecto Flux 1 base.",
        "prompt_formula": "Lenguaje natural fluido.",
        "prompt_ejemplo": "A young woman with curly hair laughing, soft studio lighting, professional portrait",
        "limitaciones": "Para máxima calidad usar Flux 2 Max o Pro.",
    },
    "Flux.1": {
        "nota": 4.3, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 1500, "modos_gen": ["Standard"],
        "best_for": "Flux 1 base. ~17s. El primer Flux de Black Forest Labs.",
        "prompt_formula": "Lenguaje natural descriptivo.",
        "prompt_ejemplo": "A serene mountain landscape at sunset, dramatic clouds, vibrant colors",
        "limitaciones": "Reemplazado por versiones más recientes.",
    },

    # ── Mystic ─────────────────────────────────────────
    "Mystic 2.5 Fluid": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "2:3", "3:2"],
        "max_chars": 2000, "modos_gen": ["Fluid"],
        "best_for": "Mystic 2.5 Fluid. ~24s. 80 créditos. Hiperrealismo nativo de Magnific basado en Flux + tecnología de upscaling Magnific. 2K nativo. El mejor para retratos, expresiones faciales.",
        "prompt_formula": "Lenguaje natural muy descriptivo. Soporta texto en imagen con comillas.",
        "prompt_ejemplo": "A young woman with long brown hair wearing a yellow dress against a patterned background, natural skin texture, individual hair strands, soft daylight, 2K resolution",
        "prompt_tips": [
            "DESCRIPTIVO DETALLADO: Piel con poros, cabellos individuales, etc.",
            "RETRATOS: Excelente para rostros y expresiones.",
            "UPSDALING NATIVO: 2K de salida sin post-procesamiento.",
        ],
        "limitaciones": "Costoso (80 créditos). Para diseño con texto, Ideogram funciona mejor.",
    },

    # ── Google Imagen ─────────────────────────────────
    "Google Imagen 4 Ultra": {
        "nota": 4.8, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"],
        "max_chars": 2000, "modos_gen": ["Ultra"],
        "best_for": "Google Imagen 4 Ultra. ~18s. Fotorrealismo top de Google. Excelente entendimiento espacial y físico. Ideal para escenas complejas.",
        "prompt_formula": "Lenguaje natural muy descriptivo. Imagen entiende relaciones espaciales precisas.",
        "prompt_ejemplo": "A red coffee mug placed on a wooden desk to the right of an open notebook, soft morning light streaming through a window from the left, shallow depth of field",
        "prompt_tips": [
            "RELACIONES ESPACIALES: Describe posiciones precisas (to the right of, behind, above).",
            "FÍSICA REALISTA: Entiende gravedad, luz, sombras correctamente.",
            "ESCENAS COMPLEJAS: Maneja múltiples objetos y sus interacciones.",
        ],
        "limitaciones": "Sin negative.",
    },
    "Google Imagen 4": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"],
        "max_chars": 1500, "modos_gen": ["Standard"],
        "best_for": "Google Imagen 4. ⚡ ~10s. Fotorrealismo + rápido. Buen balance velocidad/calidad.",
        "prompt_formula": "Lenguaje natural descriptivo con relaciones espaciales claras.",
        "prompt_ejemplo": "A photorealistic portrait of a young woman with auburn hair, soft natural lighting from a window on the left, blurred forest background",
        "limitaciones": "Menos detalle que Imagen 4 Ultra.",
    },
    "Google Imagen 3": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 1000, "modos_gen": ["Standard"],
        "best_for": "Google Imagen 3. ⚡ ~9s. Generación rápida calidad media.",
        "prompt_formula": "Lenguaje natural simple.",
        "prompt_ejemplo": "A cat sitting in a garden of wildflowers, sunny day, photorealistic",
        "limitaciones": "Reemplazado por Imagen 4. Calidad menor.",
    },

    # ── Seedream ──────────────────────────────────────
    "Seedream 5 Lite": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "2:3", "3:2"],
        "max_chars": 2000, "modos_gen": ["Lite"],
        "best_for": "Seedream 5 Lite (Destacado/Nuevo). Salida 2K. ~51s. Modelo más reciente de ByteDance. Excelente para fotorrealismo y arte.",
        "prompt_formula": "Lenguaje natural muy descriptivo. Soporta múltiples sujetos y composiciones complejas.",
        "prompt_ejemplo": "A cinematic shot of two friends sitting at a vintage diner counter, neon reflections on the chrome surface, warm dramatic lighting, 35mm film aesthetic",
        "prompt_tips": [
            "DESCRIPTIVO CINEMÁTICO: Menciona iluminación, ángulo, estética.",
            "MÚLTIPLES SUJETOS: Maneja grupos y composiciones complejas.",
            "RECIENTE: Último modelo de ByteDance, tecnología actualizada.",
        ],
        "limitaciones": "Más lento que Flux Klein.",
    },
    "Seedream 4.5": {
        "nota": 4.6, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2"],
        "max_chars": 2000, "modos_gen": ["High Resolution"],
        "best_for": "Seedream 4.5. Salida 2K-4K. ~1m 5s. Alta resolución, fotorrealismo, soporta referencias.",
        "prompt_formula": "Lenguaje natural detallado. Mencionar resolución target.",
        "prompt_ejemplo": "Highly detailed product photo of a luxury watch, macro lens, perfect studio lighting, 4K resolution, commercial quality",
        "prompt_tips": [
            "RESOLUCIÓN EXPLÍCITA: Menciona 2K, 4K si necesitas alta calidad.",
            "REFERENCIAS: Soporta imágenes de estilo.",
            "MACRO/DETALLE: Excelente para productos y texturas.",
        ],
        "limitaciones": "Lento (~1m 5s).",
    },
    "Seedream 4 4K": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 2000, "modos_gen": ["4K"],
        "best_for": "Seedream 4 4K. ~37s. Genera directamente en 4K nativo. Para impresión y trabajos de alta resolución.",
        "prompt_formula": "Lenguaje natural detallado. Aprovecha la alta resolución pidiendo detalles finos.",
        "prompt_ejemplo": "An intricate macro photograph of a butterfly wing showing fine scale patterns, ultra-detailed, 4K resolution",
        "limitaciones": "Sin negative.",
    },
    "Seedream 4": {
        "nota": 4.4, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 1500, "modos_gen": ["Standard"],
        "best_for": "Seedream 4. ~19s. Versión estándar, balance calidad/velocidad.",
        "prompt_formula": "Lenguaje natural fluido.",
        "prompt_ejemplo": "A serene Japanese garden with a koi pond, cherry blossoms falling, soft natural light",
        "limitaciones": "Reemplazado por Seedream 4.5 y 5 Lite.",
    },

    # ── Recraft ──────────────────────────────────────
    "Recraft V4 Pro": {
        "nota": 4.7, "has_negative": True, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "2:3", "3:2"],
        "max_chars": 2000, "modos_gen": ["Pro"],
        "best_for": "Recraft V4 Pro (Nuevo). ~35s. Soporta NEGATIVE PROMPT. Especialista en arte vectorial, ilustraciones, branding. Mejor que V3.",
        "prompt_formula": "Lenguaje natural + estilo vectorial. 'Flat illustration', 'vector art', 'icon style'.",
        "prompt_ejemplo": "Flat vector illustration of a cozy coffee shop at night, warm color palette, geometric shapes, minimalist design",
        "prompt_tips": [
            "SOPORTA NEGATIVE: Usa (cosa:1.2) para mejorar precisión.",
            "ESTILOS VECTORIALES: Flat, line art, icon, etc.",
            "SVG OUTPUT: Genera graphics escalables editables.",
            "REFERENCIAS: Hasta 3 imágenes de estilo.",
        ],
        "limitaciones": "No fotorrealismo. Mejor para gráfico/vectorial.",
    },
    "Recraft V4": {
        "nota": 4.5, "has_negative": True, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"],
        "max_chars": 1500, "modos_gen": ["Standard"],
        "best_for": "Recraft V4 (Nuevo). ~18s. Soporta NEGATIVE PROMPT. Versión estándar para vectorial.",
        "prompt_formula": "Lenguaje natural + estilo vectorial.",
        "prompt_ejemplo": "Minimalist vector poster with geometric shapes, monochrome palette, clean lines",
        "limitaciones": "No fotorrealismo.",
    },

    # ── Otros Magnific ────────────────────────────────
    "Z-Image": {
        "nota": 4.4, "has_negative": False, "is_natural": False, "no_weights": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 1000, "modos_gen": ["Turbo"],
        "best_for": "Z-Image en Magnific. ⚡ ~8s. Modelo Turbo: tags limpios sin pesos ni negative. Latencia mínima.",
        "prompt_formula": "Tags limpios separados por comas SIN pesos numéricos.",
        "prompt_ejemplo": "close-up portrait, silver hair, blue eyes, detailed skin, soft studio lighting, 8K, masterpiece",
        "prompt_tips": [
            "TAGS LIMPIOS: Sin paréntesis ni números.",
            "COMAS SEPARAN: keyword1, keyword2, keyword3.",
            "MÁX SIMPLICIDAD: Diseñado para velocidad.",
        ],
        "limitaciones": "Sin negative ni pesos. Para alta calidad usar Mystic/Flux.",
    },
    "Qwen": {
        "nota": 4.3, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 1500, "modos_gen": ["Standard"],
        "best_for": "Qwen Image en Magnific. ~12s. Buena calidad general, soporta referencias. De Alibaba/Aliyun.",
        "prompt_formula": "Lenguaje natural descriptivo.",
        "prompt_ejemplo": "A modern minimalist living room with large windows, natural light, scandinavian design",
        "limitaciones": "Sin negative.",
    },
    "Grok": {
        "nota": 4.2, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 1500, "modos_gen": ["Standard"],
        "best_for": "Grok Imagine en Magnific. ~11s. Modelo de xAI. Buena para arte conceptual y escenas creativas.",
        "prompt_formula": "Lenguaje natural creativo. Le va bien lo absurdo y la fantasía.",
        "prompt_ejemplo": "A surreal scene of giant mushrooms in a crystal forest, dreamy ethereal lighting, fantasy art style",
        "limitaciones": "Sin negative ni pesos.",
    },
    "Classic": {
        "nota": 4.0, "has_negative": True, "is_natural": False,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 1000, "modos_gen": ["Classic"],
        "best_for": "Modelo Classic de Magnific. ⚡ ~4s. Soporta NEGATIVE PROMPT. Tags estilo Stable Diffusion. Ideal cuando quieres control con negatives.",
        "prompt_formula": "Tags con pesos estilo Stable Diffusion. (tag:1.2). Soporta negative.",
        "prompt_ejemplo": "(beautiful portrait:1.3), 1girl, detailed face, soft lighting, professional photography, 8K",
        "prompt_tips": [
            "PESOS CON PARÉNTESIS: (tag:1.2) para усилить, (tag:0.8) para debilitar.",
            "NEGATIVE PROMPT: Campo separado para excluir elementos.",
            "TAGS COMO SD: Inspirado en Stable Diffusion clásico.",
            "RÁPIDO: ~4s para generación.",
        ],
        "limitaciones": "Calidad inferior a modelos modernos pero soporta negative.",
    },
    "Classic Fast": {
        "nota": 3.9, "has_negative": True, "is_natural": False,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 500, "modos_gen": ["Fast"],
        "best_for": "Classic Fast. ⚡ ~2s (más rápido). Soporta NEGATIVE PROMPT. Ideal para iteración rápida con tags + negative.",
        "prompt_formula": "Tags con pesos. Soporta negative.",
        "prompt_ejemplo": "(portrait:1.2), 1girl, detailed face, studio lighting, masterpiece",
        "prompt_tips": [
            "VELOCIDAD MÁXIMA: ~2s para iterar ultra-rápido.",
            "TAGS SIMPLES: No necesitas essays.",
            "NEGATIVE DISPONIBLE: Control sobre qué excluir.",
        ],
        "limitaciones": "Calidad menor que Classic estándar.",
    },
}

# ══════════════════════════════════════════════════════════════════
# ESPECIFICACIONES DE MODELOS DE AUDIO (Mayo 2026)
# ══════════════════════════════════════════════════════════════════
MODEL_SPECS_AUDIO = {
    # ─────────────────────────────────────────────────────────────────
    # SUNO (Modelos principales - Todos tienen negative prompt)
    # ─────────────────────────────────────────────────────────────────
    "Suno v5.5": {
        "nota": 4.9,
        "has_negative": True,
        "has_lyrics": True,
        "has_instrumental_toggle": True,
        "usa_tags_estructurales": True,
        "duracion_max_min": 8,
        "max_chars_letra": 5000,
        "max_chars_estilo": 200,
        "idiomas": ["inglés", "español", "frañol", "italiano", "portugués", "alemán", "chino", "japonés", "coreano"],
        "best_for": "Modelo flagship actual (Marzo 2026). Expresividad máxima, voces naturales, Studio integrado, 12 stems, Voice Cloning, Custom Models personalizados. Comercial con Pro/Premier.",
        "prompt_formula": "GMVP: Genre + Mood + Vocals + Production. Tags limpios (5-8 máximo). Negative: 'no elemento'. Custom Mode obligatorio.",
        "prompt_ejemplo_estilo": "indie folk, melancholic, breathy female vocals, fingerpicked acoustic guitar, warm analog sound, 94 BPM, no reverb wash, no synths",
        "prompt_ejemplo_letra": "[Verse 1]\nWalking down the old street...\n[Chorus]\nMidnight rain falling on me...",
        "prompt_tips": [
            "GMVP METHOD: Genre + Mood + Vocals + Production (en ese orden).",
            "SIMPLIFICAR: v5.5 funciona MEJOR con prompts simples (5-8 tags). Menos = mejor.",
            "CUSTOM MODE: Siempre usa Custom Mode para control total sobre Style + Lyrics.",
            "TAGS ESTRUCTURALES: [Verse], [Chorus], [Bridge], [Pre-Chorus], [Intro], [Outro] (funcionan mejor en letras).",
            "NEGATIVE PROMPT: Añade 'no autotune', 'no reverb', 'no falsetto' al final del Style.",
            "VOCALS: Especifica género (male/female), tono (breathy/raspy), técnica (belting/whispered).",
            "NO EXAGERES: 10+ tags = peor resultado. 5-8 tags óptimos.",
            "WEIRDNESS/STYLE INFLUENCE: 50/70 por defecto para empezar.",
            "VOICE CLONING: Pro/Premier. Clone tu voz para consistencia en albumes.",
            "CUSTOM MODELS: Entrena hasta 3 modelos con tu catálogo (mín 6 canciones).",
            "MY TASTE: Sesión aprende preferencias. Desactívalo si quieres control total.",
        ],
        "estructura_tags": ["[Verse]", "[Verse 1]", "[Verse 2]", "[Pre-Chorus]", "[Chorus]", "[Post-Chorus]", "[Bridge]", "[Intro]", "[Outro]", "[Instrumental]", "[Instrumental Break]", "[Guitar Solo]", "[Break]", "[Build]", "[Drop]", "[Spoken]", "[Whispered]", "[Belting]", "[Harmonies]", "[Tag: descriptors]"],
        "limitaciones": "Pro/Premier para v5.5. Credits no se acumulan. Extensiones >6min pueden derivar estilísticamente.",
    },
    "Suno v5": {
        "nota": 4.8,
        "has_negative": True,
        "has_lyrics": True,
        "has_instrumental_toggle": True,
        "usa_tags_estructurales": True,
        "duracion_max_min": 8,
        "max_chars_letra": 5000,
        "max_chars_estilo": 200,
        "idiomas": ["inglés", "español", "francés", "italiano", "portugués", "alemán", "chino", "japonés", "coreano"],
        "best_for": "Studio-grade audio (48kHz), Suno Studio DAW integrado, 12-stem separation, vocals realistas con vibrato natural. Generación 10x más rápida que v4.",
        "prompt_formula": "Genre + Mood + Vocals + Production. Negative: 'no X'. 5-8 tags óptimos.",
        "prompt_ejemplo_estilo": "neo-soul R&B, warm and groovy, smooth female vocals, talking drum, melodic guitar, 100 BPM, F minor",
        "prompt_ejemplo_letra": "[Verse]\nTalk to me softly...\n[Chorus]\nWe could be dancing all night long...",
        "prompt_tips": [
            "ESTUDIO-GRADE: Audio más limpio y profesional que versiones anteriores.",
            "NEGATIVE PROMPTING FUNCIONA: 'no autotune', 'no heavy reverb', 'no falsetto'.",
            "SUNO STUDIO: Editor timeline, regenerar secciones, exportar 12 stems.",
            "STEM SEPARATION: Vocals, drums, bass, other — hasta 12 tracks separados.",
            "VOCAL REALISM: Respiraciones naturales, phrasing mejorado, menos 'robótico'.",
            "GMVP: Genre + Mood + Vocals + Production — en ese orden exacto.",
            "STRUCTURAL TAGS: [Verse], [Chorus], [Bridge], [Pre-Chorus] + nuevos como [Build], [Drop].",
            "SIMPLIFICAR: 5-8 tags funciona mejor que essays descriptivos.",
            "NEGATIVE AL FINAL: Suno procesa positives primero, luego exclusions.",
        ],
        "estructura_tags": ["[Verse]", "[Pre-Chorus]", "[Chorus]", "[Bridge]", "[Outro]", "[Intro]", "[Instrumental Break]", "[Build]", "[Drop]", "[Spoken]", "[Whispered]"],
        "limitaciones": "Pro/Premier. Extensiones largas pueden perder coherencia. No tiene Voice Cloning ni Custom Models (v5.5).",
    },
    "Suno v4.5": {
        "nota": 4.7,
        "has_negative": True,
        "has_lyrics": True,
        "has_instrumental_toggle": True,
        "usa_tags_estructurales": True,
        "duracion_max_min": 8,
        "max_chars_letra": 5000,
        "max_chars_estilo": 1000,
        "idiomas": ["inglés", "español", "francés", "italiano", "portugués", "alemán", "chino", "japonés", "coreano"],
        "best_for": "Heavy genres (metal, rock, punk), Mashups creativos, géneros híbridos. Prompt Enhancement Helper. Agrega Add Vocals / Add Instrumentals / Inspire.",
        "prompt_formula": "Más conversacional que v5. Descripciones detalladas funcionan. 'A crushing industrial metal track with mechanical drums...'",
        "prompt_ejemplo_estilo": "midwest emo mixed with neosoul, warm vocals, dynamic drums, emotional guitar solos, introspective mood",
        "prompt_ejemplo_letra": "[Intro]\n(soft piano)...\n[Verse 1]\nI used to think I'd never fall in love...",
        "prompt_tips": [
            "MÁS DETALLE = MEJOR: v4.5 se beneficia de descripciones más ricas que v5.",
            "CONVERSATIONAL STYLE: 'A crushing industrial metal track with...' funciona mejor que tags simples.",
            "GENRE COMBINATIONS: midwest emo + neosoul, jazz + hip-hop, etc. v4.5 lo maneja bien.",
            "PROMPT ENHANCEMENT HELPER: AI expande tus tags antes de generar. Úsalo.",
            "ADD VOCALS: Genera encima de un instrumental (uploaded o generado).",
            "ADD INSTRUMENTALS: Genera pista debajo de una vocal.",
            "INSPIRE: Mantén coherencia de estilo en sets/albumes.",
            "MEJOR PARA: Heavy metal, hard rock, punk, EDM rápido.",
            "NO PARA: Soft genres (usa v5 para eso).",
        ],
        "estructura_tags": ["[Verse]", "[Pre-Chorus]", "[Chorus]", "[Bridge]", "[Outro]", "[Intro]", "[Instrumental]"],
        "limitaciones": "Vocales menos naturales que v5. Prompts muy complejos pueden confundirse. v5 supera en audio quality.",
    },
    "Suno v4": {
        "nota": 4.5,
        "has_negative": True,
        "has_lyrics": True,
        "has_instrumental_toggle": True,
        "usa_tags_estructurales": True,
        "duracion_max_min": 4,
        "max_chars_letra": 3000,
        "max_chars_estilo": 200,
        "idiomas": ["inglés", "español", "francés", "italiano", "portugués", "alemán", "chino", "japonés", "coreano"],
        "best_for": "Audio limpio, Covers feature, Personas, hasta 4 min. Introdujo stem separation básico (2 stems).",
        "prompt_formula": "Tags directos: género + mood + instrumentos. Estilo simple.",
        "prompt_ejemplo_estilo": "acoustic folk, fingerpicking, soft male vocals, warm and intimate, campfire atmosphere",
        "prompt_ejemplo_letra": "[Verse]\nWalking through the morning light...\n[Chorus]\nThis is where we come alive...",
        "prompt_tips": [
            "MÁS SIMPLE QUE v4.5/v5: No necesitas estructuras complejas.",
            "TAGS BÁSICOS: Genre + Mood + Instruments suficiente.",
            "LIMITADO A 4 MIN: No genera tracks tan largos como versiones nuevas.",
            "PERSONAS: Guarda voces generadas para reutilizar en future songs.",
            "COVERS: Cambia género/estilo manteniendo melodía de una canción existente.",
            "STEM SEPARATION: Solo 2 stems (vocals + instrumental). Limitado para producción.",
        ],
        "estructura_tags": ["[Verse]", "[Chorus]", "[Bridge]", "[Intro]", "[Outro]"],
        "limitaciones": "Máx 4 min. Vocales menos expresivas. Reemplazado por v4.5+ y v5.",
    },

    # ─────────────────────────────────────────────────────────────────
    # UDIO (Modelos alternativos - v1.5 y v4)
    # ─────────────────────────────────────────────────────────────────
    "Udio v4": {
        "nota": 4.7,
        "has_negative": True,
        "has_lyrics": True,
        "has_instrumental_toggle": True,
        "usa_tags_estructurales": True,
        "duracion_max_min": 10,
        "max_chars_letra": 4000,
        "max_chars_estilo": 700,
        "idiomas": ["inglés", "español", "francés", "italiano", "portugués", "alemán", "chino", "japonés", "coreano"],
        "best_for": "Audio 48kHz stereo, instrumentales de calidad, jazz/clásica/electrónica. Timeline editing, inpainting (fix secciones), extiende hasta 10min sin drift musical.",
        "prompt_formula": "Tag-based: [Genre], [Mood], [Instruments], [Production]. Estilo 'sandwich': Top Bun (genre), Meat (vibe), Bottom Bun (production).",
        "prompt_ejemplo_estilo": "cinematic orchestral, epic trailer music, intense building tension, full strings brass stabs deep percussion, warm analog sound no vocals",
        "prompt_ejemplo_letra": "[Intro]\n(Orchestral build)...\n[Verse]\nDark clouds gathering above...",
        "prompt_tips": [
            "SANDWICH METHOD: Genre (top bun) + Vibe/Instruments (meat) + Production (bottom bun).",
            "MEJOR PARA: Instrumentales, jazz, clásica, electrónica, scores cinematográficos.",
            "48kHz STEREO: Mejor resolución que Suno (44.1kHz). Audio más limpio.",
            "INPAINTING: Selecciona 2 segundos de una sección y regenera solo esa parte.",
            "TIMELINE EDITING: Visual para reorganizar secciones con precisión.",
            "EXTEND 30s: Cada extensión mantiene key, tempo, estilo. Hasta 10+ minutos.",
            "QUALITY TAGS: Añade 'clean mix', 'streaming-ready', 'pristine' al final.",
            "STEREO FIELD: 'wide stereo image', 'spacious', 'immersive' para sonido envolvente.",
            "LOW END: 'tight bass', 'controlled sub-bass', 'punchy low-end' para graves profesionales.",
            "PRODUCTION: 'warm tape saturation', 'vintage crackle', 'analog warmth' para carácter.",
        ],
        "estructura_tags": ["[Intro]", "[Verse]", "[Pre-Chorus]", "[Chorus]", "[Post-Chorus]", "[Bridge]", "[Solo]", "[Outro]", "[Interlude]", "[Instrumental Break]", "[Drop]", "[Build]", "[Breakdown]"],
        "limitaciones": "Vocales menos expresivas que Suno v5. Generación nativa más corta (30s). Requiere extender para songs completos.",
    },
    "Udio v1.5": {
        "nota": 4.6,
        "has_negative": True,
        "has_lyrics": True,
        "has_instrumental_toggle": True,
        "usa_tags_estructurales": True,
        "duracion_max_min": 10,
        "max_chars_letra": 4000,
        "max_chars_estilo": 700,
        "idiomas": ["inglés", "español", "francés", "italiano", "portugués", "alemán", "chino", "japonés", "coreano"],
        "best_for": "Audio-to-audio remixing, key control, granular production control. Stem downloads (paid). Inpainting básico.",
        "prompt_formula": "Basic: 'A song about [tema], [genre], [mood], [instruments]'. Custom: título + estilo + letras separadas.",
        "prompt_ejemplo_estilo": "emotional pop ballad, piano soft strings intimate female vocals, slow tempo 65 BPM building to full chorus layered harmonies modern production warm vulnerable",
        "prompt_ejemplo_letra": "[Verse]\nEvery night I think about us...\n[Chorus]\nWe could be dancing in the rain...",
        "prompt_tips": [
            "BASIC VS CUSTOM MODE: Basic = describe todo en un prompt. Custom = separate title/style/lyrics.",
            "AUDIO-TO-AUDIO: Sube un track y reinterpreta en diferente género manteniendo melodía.",
            "KEY CONTROL: Especifica tonalidad (A minor, C major, etc.) para mejor precisión armónica.",
            "BPM/TEMPO: 'slow ballad at 70 BPM' o 'fast-paced at 140 BPM' mejora precisión rítmica.",
            "SPECIFIC INSTRUMENTS: 'acoustic guitar upright bass brushed drums' > solo 'jazz'.",
            "ERA REFERENCES: '1970s funk', '1990s R&B', '2010s blog-era indie' para sonido auténtico.",
            "STRUCTURE TAGS: Funcionan en Custom Mode para control de secciones.",
            "MANUAL MODE: Disable auto-rewrite para control total (solo tags, no free text).",
            "VOICE CLONING: Upload 1min audio + verificación de identidad.",
        ],
        "estructura_tags": ["[Verse]", "[Chorus]", "[Hook]", "[Bridge]", "[Intro]", "[Outro]", "[Guitar Solo]", "[Drop]", "[Spoken Word]", "[Choir]", "[Announcer]"],
        "limitaciones": "Stem export limitado (Standard/Pro). Vocales menos naturales que Suno. Manual mode puede producir lyrics genéricos.",
    },

    # ─────────────────────────────────────────────────────────────────
    # MINIMAX MUSIC (Modelos de integración - SeaArt/Tensor.art)
    # ─────────────────────────────────────────────────────────────────
    "Minimax Music 2.6": {
        "nota": 4.6,
        "has_negative": False,
        "has_lyrics": True,
        "has_instrumental_toggle": True,
        "usa_tags_estructurales": True,
        "duracion_max_min": 5,
        "max_chars_letra": 3500,
        "max_chars_estilo": 2000,
        "idiomas": ["inglés", "chino mandarín"],
        "best_for": "Physical-grade high fidelity, paragraph-level precision control (14+ structural tags), 100+ instruments, automatic style-adaptive mixing.",
        "prompt_formula": "Style: [Genre], [Mood], [Vocal description], [Tempo], [Key instruments], [Era/Style reference], [Production]. Lyrics: [Verse], [Chorus], etc.",
        "prompt_ejemplo_estilo": "indie folk melancholic intimate female vocals slightly raspy mid-register breathy on verse open on chorus fingerpicked acoustic guitar warm upright bass sparse brushed drums 94 BPM D minor no reverb wash no synths no drum machines",
        "prompt_ejemplo_letra": "[Verse]\nCaminando por la calle...\n[Chorus]\nLa lluvia cae sobre mí...",
        "prompt_tips": [
            "14+ STRUCTURAL TAGS: Intro, Verse, Pre-Chorus, Chorus, Hook, Bridge, Build-up, Interlude, Outro, Instrumental Break, etc.",
            "PARAGRAPH-LEVEL CONTROL: Cada sección tiene instrucciones específicas (guitar only, soft drums).",
            "100+ INSTRUMENTS: Guitarra (acoustic/distorted/clean), piano, synth, orchestral strings, brass, drums, 808, hi-hats, etc.",
            "STYLE-ADAPTIVE MIXING: Rock = distortion/power. Jazz = vintage warmth. 80s = lo-fi texture automáticamente.",
            "VOCAL SYNTHESIS: Natural vibrato, chest/head transitions, authentic breathing. Menos robótico.",
            "GENRE PROMPT: 'lo-fi jazz', '2010s blog-era indie', '1980s Minneapolis sound' para precisión.",
            "TEMPO/BPM: '94 BPM', 'driving 125 BPM', 'slow tempo' para control rítmico.",
            "PRODUCTION DESCRIPTORS: 'wide soundstage', 'intimate studio feel', 'vintage warmth'.",
            "INSTRUMENTAL MODE: isInstrumental=true para tracks sin vocal (2.6 only).",
            "AUTO LYRICS: lyricsOptimizer=true genera lyrics del prompt (2.6 only).",
            "BEST FOR: Productores que necesitan control granular de secciones.",
        ],
        "estructura_tags": ["[Intro]", "[Verse]", "[Pre-Chorus]", "[Chorus]", "[Hook]", "[Bridge]", "[Build-up]", "[Interlude]", "[Instrumental Break]", "[Solo]", "[Outro]", "[Outro-Fade]", "[Tag]", "[Inst]", "[Break]"],
        "limitaciones": "Up to ~5 min por generación. No stem export. Sin negative prompt nativo. Español/otros idiomas menos precisos que inglés/chino.",
    },
    "Minimax Music 2.5": {
        "nota": 4.5,
        "has_negative": False,
        "has_lyrics": True,
        "has_instrumental_toggle": True,
        "usa_tags_estructurales": True,
        "duracion_max_min": 5,
        "max_chars_letra": 3500,
        "max_chars_estilo": 2000,
        "idiomas": ["inglés", "chino mandarín", "español"],
        "best_for": "Precisión de sección, 100+ instrumentos, producción profesional. Mejor que v2.0 en vocal y instrument separation.",
        "prompt_formula": "Prompt: [Genre], [Mood/Emotion], [Vocal description], [Tempo], [Key instruments], [Era/Style], [Production]. Lyrics: con tags [Verse], [Chorus].",
        "prompt_ejemplo_estilo": "blues soulful rainy night electric guitar melancholic male vocals slow tempo moody atmosphere warm analog production",
        "prompt_ejemplo_letra": "[Intro]\n(Guitar solo - slow mournful bluesy)...\n[Verse]\nEach drop of rain...\n[Chorus]\nMidnight rain falling on me...",
        "prompt_tips": [
            "LIRICS REQUIRED: A diferencia de 2.6, en 2.5 los lyrics son obligatorios.",
            "14 STRUCTURAL TAGS: Control de sección completo como 2.6.",
            "100+ INSTRUMENTS: Biblioteca extensa con orchestral, rock, jazz, electronic.",
            "STYLE-AWARE MIXING: Automáticamente adapta mixing a género.",
            "VOCAL QUALITY: Mejor que 2.0 — vibrato natural, transiciones chest/head.",
            "FORMATOS: MP3 (256kbps) o WAV (44.1kHz) para producción.",
            "SAMPLE RATE: 16kHz a 44.1kHz. 44.1kHz recomendado para calidad CD.",
            "BITRATE: 32kbps a 256kbps. 256kbps para máxima calidad.",
        ],
        "estructura_tags": ["[Verse]", "[Chorus]", "[Bridge]", "[Intro]", "[Outro]", "[Instrumental Break]", "[Build-up]", "[Hook]", "[Interlude]", "[Solo]", "[Tag]"],
        "limitaciones": "Lyrics obligatorios (no instrumental mode). No stem export. Max ~5min. Sin negative prompt.",
    },
    "SeaArt MusicGo": {
        "nota": 4.3,
        "has_negative": False,
        "has_lyrics": True,
        "has_instrumental_toggle": True,
        "usa_tags_estructurales": False,
        "duracion_max_min": 3,
        "max_chars_letra": 1500,
        "max_chars_estilo": 300,
        "idiomas": ["inglés", "español", "chino", "japonés", "francés"],
        "generos": ["Pop", "R&B", "Rock", "Disco", "Electrónica", "Folk", "Hip-hop", "Blues", "Clásica", "Música de videojuegos"],
        "best_for": "Integrado en SeaArt. Toggle Vocal/Instrumental explícito. Generación rápida y económica.",
        "prompt_formula": "Toggle Vocal/Instrumental. Letra directa sin tags. Estilo: género + mood + instrumentos.",
        "prompt_ejemplo_estilo": "electronic synthwave relaxing ambient background 80s retro vibes",
        "prompt_ejemplo_letra": "Letra directa sin tags estructurales",
        "prompt_tips": [
            "INTERFAZ SIMPLE: Integración directa con SeaArt para usuarios de esa plataforma.",
            "TOGGLE EXPLICITO: Selecciona Vocal Mode o Instrumental Mode claramente.",
            "SIN TAGS ESTRUCTURALES: No uses [Verse], [Chorus] — no los interpreta.",
            "LETRA DIRECTA: Escribe la letra tal cual quieres que se cante.",
            "ESTILO SIMPLE: 'electronic synthwave', 'acoustic folk', 'jazz ballad'.",
            "ECONÓMICO: Coste de energía bajo comparado con otras plataformas.",
        ],
        "limitaciones": "Sin tags estructurales. Menor variedad de géneros que Suno/Udio. Max 3 min. Sin control de sección.",
    },

    # ─────────────────────────────────────────────────────────────────
    # OTROS MODELOS DE AUDIO
    # ─────────────────────────────────────────────────────────────────
    "Suno v4.5-All (Free)": {
        "nota": 4.5,
        "has_negative": True,
        "has_lyrics": True,
        "has_instrumental_toggle": True,
        "usa_tags_estructurales": True,
        "duracion_max_min": 8,
        "max_chars_letra": 5000,
        "max_chars_estilo": 1000,
        "idiomas": ["inglés", "español", "francés", "italiano", "portugués", "alemán", "chino", "japonés", "coreano"],
        "best_for": "Versión gratuita de v4.5 con mejoras. Available para usuarios free. Buena opción si no puedes pagar.",
        "prompt_formula": "Igual que v4.5: más detalle funciona bien. Genre + mood + instrumentos + vocal description.",
        "prompt_ejemplo_estilo": "dream pop ethereal atmospheric floating vocals reverb-drenched guitars ambient synths 90s shoegaze influence",
        "prompt_ejemplo_letra": "[Verse]\nFloating through the neon lights...\n[Chorus]\nWe are infinite tonight...",
        "prompt_tips": [
            "SAME AS v4.5: Usa los mismos tips y fórmulas que v4.5.",
            "FREE TIER: Sin necesidad de Pro/Premier para acceder.",
            "BUENA CALIDAD: Las mismas mejoras de v4.5 disponibles sin pagar.",
            "LIMITADO EN: No tiene Studio, stems limitados, menos créditos.",
        ],
        "limitaciones": "Credits limitados. Sin Studio features. Stem export básico.",
    },
}

# ══════════════════════════════════════════════════════════════════
# PRESETS DE PROMPT POR MODELO (plantillas base probadas)
# El LLM usa estos como esqueleto y adapta según la idea del usuario
# ══════════════════════════════════════════════════════════════════
PROMPT_TEMPLATES = {
    # ── Realismo SD (tag-based con pesos) ────────────────────
    "fotorrealismo_sd": {
        "modelos": ["Z Image Turbo", "Z-Image-Base-Realistic", "CyberRealistic", "Realistic Vision V6.0", "Illustrious Realism by Klaabu", "Real Dream SDXL", "MajicMIX Realistic v6", "Prodigies"],
        "positive_base": "({encuadre}:1.2), {sujeto}, {detalles_sujeto}, (detailed skin texture:1.2), {ropa_accesorios}, {entorno}, ({iluminacion}:1.3), {atmosfera}, {paleta_colores}, {estilo_fotografico}, sharp focus, photorealistic, 8K, masterpiece, highly detailed",
        "negative_base": "(worst quality, low quality, lowres, blurry:1.4), (anime, cartoon, 3d render, painting, drawing, illustration:1.3), (text, watermark, signature:1.3), (deformed, distorted, asymmetric:1.2), jpeg artifacts",
    },
    "retrato_sd": {
        "modelos": ["Z Image Turbo", "Z-Image-Base-Realistic", "CyberRealistic", "Realistic Vision V6.0", "Prodigies", "MajicMIX Realistic v6"],
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
        "modelos": ["FLUX.1 [dev]", "FLUX.1-dev-fp8", "FLUX.1", "FLUX.1D UltraReal", "Mix Max Cinematic Realism", "SeaArt Infinity", "SeaArt Infinity V2.0", "Nano Banana Pro Image", "Nano Banana 2"],
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
ESTILO_NEGATIVO_AUTO = {
    # ── Realismo → quitar anime/cartoon ──
    "Fotografía Realista":    ["Anime/2D", "Baja Calidad"],
    "Retrato":                ["Anime/2D", "Anatomía", "Deformación"],
    "Macro":                  ["Anime/2D", "Baja Calidad"],
    "Street Photography":     ["Anime/2D", "Baja Calidad"],
    "Landscape / Nature":     ["Anime/2D", "Texto/Marcas"],
    "Producto / Comercial":   ["Anime/2D", "Baja Calidad", "Texto/Marcas"],
    "Food Photography":       ["Anime/2D", "Baja Calidad"],
    "Fashion / Editorial":    ["Anime/2D", "Anatomía", "Deformación"],
    "Arquitectura":           ["Anime/2D", "Deformación"],
    # ── Anime/Ilustración → quitar realismo ──
    "Anime / Ilustración":    ["Realismo"],
    "Comic / Manga":          ["Realismo"],
    "Chibi / Kawaii":          ["Realismo"],
    "Studio Ghibli":          ["Realismo"],
    "Anime 90s Retro":        ["Realismo"],
    "Sketch / Lineart":       ["Realismo"],
    "Pixar / Disney 3D":      ["Realismo", "Anime/2D"],
    # ── Arte → quitar realismo ──
    "Oil Painting":           ["Realismo"],
    "Watercolor":             ["Realismo"],
    "Pixel Art":              ["Realismo"],
    "Vaporwave / Aesthetic":  ["Realismo"],
    "Tarot / Místico":        ["Realismo"],
    "Sumi-e / Tinta china":   ["Realismo"],
    "Acrílico":               ["Realismo"],
    "Charcoal / Carboncillo": ["Realismo"],
    "Low Poly":               ["Realismo"],
    "Isometric":              ["Realismo"],
    "Ukiyo-e":                ["Realismo"],
    "Art Nouveau":            ["Realismo"],
    "Art Deco":               ["Realismo"],
    "Bauhaus":                ["Realismo"],
    # ── Temáticos → quitar baja calidad ──
    "Cyberpunk / Neon":       ["Baja Calidad"],
    "Dark Fantasy":           ["Baja Calidad", "Anatomía"],
    "Terror / Horror":        ["Baja Calidad"],
    "Sci-Fi":                 ["Baja Calidad"],
    "Fantasy Épica":          ["Baja Calidad", "Anatomía"],
    "Steampunk":              ["Baja Calidad"],
    "Retro / Synthwave":      ["Realismo"],
    "Pinup Vintage":          ["Deformación", "Anatomía"],
    "3D Render":              ["Anime/2D", "Baja Calidad"],
    "Realismo Mágico":        ["Anime/2D"],
    "Underwater":             ["Anime/2D"],
    "Space / Cosmic":         ["Anime/2D", "Baja Calidad"],
    "Minimalista":            [],
    "Surreal / Dreamlike":  ["Realismo"],
    "Gothic / Oscuro":      ["Baja Calidad"],
    "Pop Art":              ["Realismo"],
    "Arte Conceptual":      ["Baja Calidad"],
    "Chibi / Kawaii":         ["Realismo"],
    "Retrato / Portrait":     ["Anime/2D", "Deformación"],
    "Paisaje / Landscape":    ["Anime/2D"],
    "Macro / Close-up":       ["Anime/2D"],
    "Wildlife / Naturaleza":  ["Anime/2D"],
    "Arquitectura":           ["Anime/2D", "Deformación"],
    "Underwater":             ["Anime/2D"],
    "Space / Cosmic":         ["Anime/2D"],
    "Minimalista":            [],
    "Vaporwave / Aesthetic":  ["Realismo"],
    "Tarot / Místico":        ["Realismo"],
    "Sumi-e / Tinta china":   ["Realismo"],
    "Acrílico":               ["Realismo"],
    "Charcoal / Carboncillo": ["Realismo"],
    "Low Poly":               ["Realismo"],
    "Isometric":              ["Realismo"],
    "Pixar / Disney 3D":      ["Realismo", "Anime/2D"],
    "Studio Ghibli":          ["Realismo"],
    "Ukiyo-e":                ["Realismo"],
    "Art Nouveau":            ["Realismo"],
    "Art Deco":               ["Realismo"],
    "Bauhaus":                ["Realismo"],
    "Anime 90s Retro":        ["Realismo"],
    "Realismo Mágico":        ["Anime/2D"],

    # ── Estilos de vídeo ──
    "Cinematográfico 4K":     ["Anime/2D", "Baja Calidad"],
    "Anime":                  ["Realismo"],
    "Acción / Corte Rápido":  ["Baja Calidad"],
    "Documental":             ["Anime/2D"],
    "Ciencia Ficción":        ["Baja Calidad"],
    "Terror / Atmósfera":     ["Baja Calidad"],
    "Videoclip Musical":      ["Baja Calidad"],
    "Cortometraje":           ["Baja Calidad"],
    "Drone / Aéreo":          ["Anime/2D", "Deformación"],
    "Cámara Lenta":           ["Baja Calidad"],
    "Motion Graphics":        ["Realismo"],
    "Time-Lapse":             ["Anime/2D"],
    "First Person POV":       ["Anime/2D"],
    "Found Footage":          ["Anime/2D"],
    "Stop Motion":            ["Realismo"],
    "Vlog / Handheld":        ["Anime/2D"],
    "Sports / Deportes":      ["Anime/2D"],
    "Anuncio Producto":       ["Baja Calidad"],
    "Cinemagraph":            ["Baja Calidad"],
    "Hyperlapse":             ["Anime/2D"],
    "Tutorial / Explainer":   ["Baja Calidad"],
    "Trailer Cinematográfico":["Baja Calidad"],
    "Music Video Sync":       ["Baja Calidad"],
}

# ── Helpers ───────────────────────────────────────────────────────
def es_separador(valor):
    return valor.startswith("──")

def get_model_specs(motor_name):
    return MODEL_SPECS.get(motor_name, None)

def get_image_model_specs(modelo_name):
    return MODEL_SPECS_IMAGEN.get(modelo_name, None)

def get_audio_model_specs(modelo_name):
    return MODEL_SPECS_AUDIO.get(modelo_name, None)

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
BIBLIOTECA_EJEMPLOS = [
    {
        "titulo": "Caída cazarecompensas",
        "modo": "video",
        "modelo": "Seedance 2.0",
        "plataforma": "SeaArt Video",
        "dificultad": "avanzado",
        "tags": ["multi-shot", "POV", "audio", "vertical", "9:16", "fantasy futurista"],
        "autor": "Gustaafvito",
        "prompt": "POSITIVE PROMPT: Shot 1 (The Dive - 0s to 5s): Extreme high-angle over-the-shoulder vertical tracking shot, camera locked to the subject's perspective as it plummets. A futuristic bounty hunter in sleek, matte black high-tech armor adorned with glowing cyan circuit lines freefalls face-first down the sheer, reflective glass facade of a colossal megacity skyscraper. The sense of acceleration is visceral, with the camera's motion blur rendering the deep background into a breathtaking vortex of light. A dense forest of towering neon skyscrapers, holographic billboards in Japanese and Chinese scripts, and sleek flying vehicles blur into vibrant streaks of neon pink, magenta, and electric cyan. Torrential rain, backlit by the city's omnipresent glow, streaks upwards against the lens in hypnotic patterns, creating dynamic light trails and realistic water droplets on the virtual camera. 8k resolution, vertical 9:16 composition.\n\nShot 2 (The Catch - 5s to 10s): Rapid transition from a shaky, immersive POV to a dynamic low-angle hero shot. Still in violent freefall, the hunter executes a sharp, athletic mid-air twist to face the camera directly, their polished visor reflecting a kaleidoscope of the chaotic neon storm rushing past. From directly above, a sleek, predatory black carbon-fiber hover-bike with an aggressive angular design and pulsating blue intake vents dives into frame with perfect timing, matching the descent velocity. The hunter's gloved hands grab the handlebars with a forceful, definitive clunk. Instantly, the bike's powerful rear thrusters ignite with a concentrated, blinding burst of brilliant cerulean blue plasma energy, firing a jetwash directly at the camera lens, causing a stunning chromatic lens flare and a dramatic light wash over the frame. The vehicle then pulls up with immense, crushing G-force, banking hard into a steep turn and accelerating away from the camera, diving like a predator into the chaotic, rain-soaked neon labyrinth of the city's lower levels.\n\nAudio: A driving, intense synthwave score with a deep, pounding bassline and rapid, precise electronic percussion. Layered sound design includes the roaring, distorted wind of terminal velocity, the high-pitched scream of the freefall, and the distorted Doppler whoosh of passing vehicles. The catch moment is punctuated by a powerful, metallic CLUNK of connection, followed immediately by a deep, sub-bass THRUM and crackle of the thrusters igniting. This transitions into the sustained, powerful roar of the bike's engines and the whip-crack sonic boom of breaking the fall.\nNEGATIVE PROMPT: distorted face, body deformation, blurry, bad lighting, cartoon, anime, watermark, text, extra limbs, slow motion, static scene",
        "estilos": ["Cyberpunk / Neon", "Acción"],
    },
    {
        "titulo": "Chica espejo (Seedance)",
        "modo": "video",
        "modelo": "Seedance 2.0",
        "plataforma": "SeaArt Video",
        "dificultad": "avanzado",
        "tags": ["multi-shot", "reflejo", "horror", "vertical", "9:16", "psicológico"],
        "autor": "Gustaafvito",
        "prompt": "POSITIVE PROMPT: 9:16 ratio. Universal Template & Character: A young woman with an exhausted expression and messy hair, in a dark, moody bathroom, consistent outfit throughout. Shot 1 (Establishing): Medium shot, she washes her face at a sink under flickering cold fluorescent light, slow push-in camera in dim light. Shot 2 (Emotion): Close-up, she looks up, makes intense eye contact with her mirror reflection, takes a deep breath, turns, and walks out of frame, static camera with stable focus. Shot 3 (Horror): Medium shot, camera fixed on the mirror; the physical room is empty, but her reflection remains, slowly breaking into a creepy, sinister smile. Cinematic lighting, dark premium tone, psychological thriller vibe, 4K ultra HD, rich details, clear stable features, no distortion. [style consistency] [scene extension] [motion reference: slow push-in, static, fixed]. Duration: 10 seconds.\nNEGATIVE PROMPT: distorted face, body deformation, blurry, bad lighting, cheerful mood, bright colors, cartoon, anime, watermark, text, extra limbs, fast motion, inconsistent outfit, reflection error, happy expression, clean hair, well-lit room, mirror without reflection, sudden cut",
        "estilos": ["Cinematográfico", "Terror Psicológico"],
    },
    {
        "titulo": "Henshin - Jinete Enmascarado",
        "modo": "imagen",
        "modelo": "Z Image Turbo",
        "plataforma": "SeaArt / Tensor.Art",
        "dificultad": "medio",
        "tags": ["tokusatsu", "explosión", "hero pose", "pesos numéricos"],
        "autor": "Gustaafvito",
        "prompt": "POSITIVE PROMPT: (obra maestra, mejor calidad:1.2), ultra detallada, 1 niño, solo, héroe jinete enmascarado, intrincada armadura de insectos mechas, visera brillante, pose dinámica de henshin, enorme explosión de fuego en segundo plano, brillante cinturón de transformación, escombros voladores, chispas que vuelan, toma de acción dinámica, estilo tokusatsu, contraste dramático, iluminación cinematográfica, 8k\nNEGATIVE PROMPT: (peor calidad, baja calidad:1.4), mala anatomía, armadura deformada, extremidades faltantes, texto, firma, marca de agua",
        "estilos": ["Tokusatsu", "Acción"],
    },
    {
        "titulo": "Hoja táctica NEON APOCALYPSE",
        "modo": "imagen",
        "modelo": "GPT Image 2",
        "plataforma": "SeaArt / Tensor.Art",
        "dificultad": "avanzado",
        "tags": ["UI design", "game design", "infografía", "9:16", "alta complejidad"],
        "autor": "Gustaafvito",
        "prompt": "POSITIVE PROMPT: Una hoja de diseño de juego completa y organizada con una cuadrícula de 3x2 para un RPG futurista titulado NEON APOCALYPSE, presentada como una pieza de arte conceptual de alta fidelidad con una estética ciberpunk oscura y cinematográfica. La composición es una maqueta vertical de 9:16 de un documento de diseño de juego, tomada desde un ángulo ligeramente elevado de 15 grados que le da a la cuadrícula una sutil perspectiva isométrica y enfatiza la profundidad entre los paneles. Cada panel está separado por finos bordes cian brillantes y un marco de aluminio cepillado con un ligero desgaste en los bordes. El fondo es de un negro carbón intenso con sutiles líneas de cuadrícula retro en cian desvaído, creando profundidad detrás de los paneles. Un tenue efecto de lluvia digital cae en el fondo, con pequeños flujos de datos cian goteando por la pantalla. Un sutil efecto de glitch distorsiona la esquina inferior derecha del marco, con algunos píxeles fuera de lugar, y una tenue marca de agua holográfica dice DESIGN DOC v2.3 - CLASSIFIED en el fondo. El ambiente general es oscuro, futurista y ligeramente crudo, con alto contraste y sombras profundas en las esquinas. Un sutil grano de película y una ligera aberración cromática le dan una sensación cinematográfica y vivida. En la esquina superior izquierda, una interfaz de INFORME DE MISIÓN muestra un avatar de personaje con un brillo holográfico y tipografía limpia, sin serifa, que explica la historia de BROTE CIBERNÉTICO y la mecánica HACK & SLASH. El texto tiene un sutil brillo de borde cian neón con bordes ligeramente pixelados, sobre un fondo mate de fibra de carbono. En la parte superior central, una pantalla de PERSONALIZACIÓN DE PERSONAJE etiquetada como NEON CYBERPUNK muestra al héroe con múltiples opciones de atuendo y accesorios, todos renderizados con elementos de interfaz de usuario de vidrio brillante y texto blanco nítido y legible sobre fondos oscuros. Los botones tienen un sutil reflejo de vidrio y una suave sombra interior. Completando la fila superior, un PERFIL DE PERSONAJE presenta EQUIPO TÁCTICO seleccionable que incluye GAFAS DE NEÓN frente a BOINA Y AURICULARES, junto con barras de estadísticas para AGILIDAD, FUERZA y TECNOLOGÍA en un vibrante verde neón con un ligero efecto de animación de pulso. Descendiendo a la fila inferior, el panel izquierdo muestra una cuadrícula de EQUIPAMIENTO para modificación, etiquetada como escopeta SG-70 SMARTER con opciones de modificación como SILENCIADOR, MIRA DE PUNTERÍA INTELIGENTE y BALAS EMP, con estadísticas precisas en una fuente monoespaciada sobre un fondo de metal cepillado. Los iconos de modificación tienen una superposición holográfica con una sutil aberración cromática. El panel central muestra una vista sigilosa de la interfaz de usuario del juego, donde la heroína se encuentra en ruinas urbanas con muros de hormigón derruidos y varillas de refuerzo oxidadas, cristales rotos en el suelo y un letrero de neón parpadeante que cuelga torcido. Los indicadores de detección aparecen en amarillo y rojo, las superposiciones tácticas en cian semitransparente, los datos de búsqueda de ruta y un multiplicador de combo de x4 que pulsa con un cálido resplandor naranja sobre el entorno oscuro. El panel inferior derecho muestra un resumen de MISIÓN COMPLETADA con estadísticas organizadas de ZOMBIS ELIMINADOS, DISPAROS DE PRECISIÓN y RANGO: S. Toda la hoja está iluminada por una luz cian ambiental fría desde arriba, con franjas de neón magenta cálidas que proyectan sombras nítidas y angulares sobre los paneles. Los elementos holográficos emiten un brillo suave y pulsante. La paleta de colores está dominada por azules marinos intensos, cian eléctrico, magenta intenso y toques de verde neón. Relación de aspecto 9:16.\nNEGATIVE PROMPT: (worst quality, low quality:1.4), (anime, cartoon:1.3), (text, watermark:1.3), blurry, deformed, bad anatomy",
        "estilos": ["Cyberpunk / Neon", "Concept Art"],
    },
    {
        "titulo": "Infografía AURORA-7 smartphone",
        "modo": "imagen",
        "modelo": "GPT Image 2",
        "plataforma": "SeaArt / Tensor.Art",
        "dificultad": "avanzado",
        "tags": ["producto", "infografía", "tipografía", "marketing"],
        "autor": "Gustaafvito",
        "prompt": "POSITIVE PROMPT: Una fotografía cinematográfica de una infografía de alta costura de primera calidad en una relación vertical de 9:16, ambientada en un laboratorio minimalista y luminoso con elegantes superficies de mármol blanco y sutiles detalles dorados. En el centro, un teléfono inteligente de vidrio y titanio llamado AURORA-7 se muestra en una vista explosionada sobre un fondo degradado suave de melocotón a crema, organizado por una elegante interfaz de usuario minimalista superpuesta a la imagen. Un gran texto blanco elegante con serifa en la parte superior dice AURORA-7 SMARTPHONE - PERFIL DE PRODUCTO DECONSTRUIDO. Los componentes flotantes están etiquetados con precisión con líneas de conexión doradas limpias y texto sans-serif ultra legible: PANTALLA DE CRISTAL - OLED de 6,7 pulgadas con difusión de luz prismática, MARCO DE TITANIO DORADO - Aleación aeroespacial pulida a mano con acabado cepillado, LENTE DE ZOOM PERISCOPE - Matriz de triple cámara con estabilización óptica, PROCESADOR AURORA-X - Sistema de refrigeración líquida con disipación de calor brillante. Debajo del perfil del producto, una cuadrícula de cuatro paneles de interfaz de usuario minimalistas muestra iconos de aplicaciones glassmorphism con degradados pastel y bordes dorados, etiquetados como DISEÑADO PARA GPT-IMAGE 2.0, GRADO ESTÉTICO S, CALIFICACIÓN DE PRECISIÓN A+, MEZCLA MINERAL ÚNICA. La escena está iluminada por una gran caja de luz a 45 grados arriba a la izquierda, creando suaves reflejos especulares en los bordes del cristal y suaves sombras a la derecha, con una sutil luz de contorno que separa el teléfono del fondo. Tomada con una lente de 50 mm a f/2.8 desde un ángulo ligeramente bajo, la poca profundidad de campo desenfoca el primer plano donde un par de guantes de algodón blanco descansan junto al teléfono. Resolución 8k, renderizado fotorrealista, brillo editorial, estética minimalista de alta costura.\nNEGATIVE PROMPT: (worst quality, low quality:1.4), (anime, cartoon:1.3), (text, watermark:1.3), blurry, deformed",
        "estilos": ["Producto", "Infografía"],
    },
    {
        "titulo": "Persecución cazarecompensas",
        "modo": "video",
        "modelo": "Seedance 2.0",
        "plataforma": "SeaArt Video",
        "dificultad": "avanzado",
        "tags": ["multi-shot", "persecución", "vertical", "9:16", "cyberpunk"],
        "autor": "Gustaafvito",
        "prompt": "POSITIVE PROMPT: Shot 1 (The Chase - 0s to 5s): Dynamic third-person vertical tracking shot following a sleek black hover-bike as it weaves at breakneck speed through the rain-soaked neon canyons of a futuristic megacity. The bounty hunter in matte black high-tech armor with glowing cyan circuit lines leans into a sharp turn, sparks flying as the bike's undercarriage grazes a rain-slicked metal bridge. Towering holographic billboards cast shifting pools of magenta and cyan light across the wet surfaces. An enemy flying vehicle with aggressive angular design and red plasma cannons enters frame from above, opening fire. Bright orange plasma bolts streak past the hunter, one narrowly missing the camera perspective, creating dramatic lens flares and heat distortion effects. 8k resolution, vertical 9:16 composition.\n\nShot 2 (The Evasion - 5s to 10s): The hunter dives the bike into a narrow alleyway between two monolithic skyscrapers, the camera executing a rapid side-sweep to maintain visual contact. The pursuing vehicle, too wide to follow, banks hard and takes an alternate route above. The hunter emerges from the alley in a steep vertical climb, spinning the bike 180 degrees to face backward, and returns fire with twin cyan energy blasts from the bike's under-mounted cannons. The camera pulls back to a wide establishing shot as the two vehicles engage in a dizzying dogfight through a maze of towering infrastructure, holographic advertisements, and dense aerial traffic, with rain and neon light creating a dazzling tapestry of streaking colors.\nNEGATIVE PROMPT: distorted face, body deformation, blurry, bad lighting, cartoon, anime, watermark, text, extra limbs, slow motion, static scene, happy mood, bright daylight",
        "estilos": ["Cyberpunk / Neon", "Acción"],
    },
    {
        "titulo": "Póster cinematográfico combate MMA",
        "modo": "imagen",
        "modelo": "GPT Image 2",
        "plataforma": "SeaArt / Tensor.Art",
        "dificultad": "medio",
        "tags": ["póster", "claroscuro", "deportivo", "vertical", "9:16"],
        "autor": "Gustaafvito",
        "prompt": "POSITIVE PROMPT: Un dramático diseño de póster cinematográfico para una pelea clandestina de artes marciales mixtas, formato vertical 9:16. Filmado con una lente gran angular de 24 mm a f/1.8, la perspectiva de ángulo bajo extremo crea una marcada distorsión de ojo de pez que exagera la imponente y heroica estatura de los luchadores, mientras que el fondo se convierte en un bokeh cremoso de tenues siluetas de la multitud y pantallas de teléfonos brillantes dispersas. A la izquierda, un fornido y poderoso hombre con la cabeza rapada, una espesa barba y elaborados tatuajes geométricos en índigo profundo que envuelven su brazo, aprieta la mandíbula, una vena palpita en su sien, su piel aceitunada está cubierta de sudor. Viste pantalones cortos de lucha de satén carmesí. Frente a él, un luchador alto y delgado con cabello oscuro recogido en un moño apretado entrecierra los ojos, los labios apretados en una fina línea de fría determinación, su piel pálida brillando bajo la luz. Viste pantalones cortos de satén gris carbón. Ambos están sin camisa, con guantes de MMA, de pie frente a frente en un tenso enfrentamiento. Un único foco de estadio atraviesa la oscuridad, proyectando un cálido resplandor ámbar que crea un halo dorado alrededor de sus músculos venosos y altamente detallados, mientras que frías sombras azul oscuro se acumulan alrededor de sus pies. El fondo se disuelve en profundas sombras con tenues siluetas de una multitud, salpicadas por algunas pantallas de teléfonos brillantes. Toda la imagen está tratada con una textura de cómic retro cruda, patrones de puntos de semitono irregulares y toscos que recuerdan a los cómics underground de los años 70, con un ligero efecto de desajuste en los canales cian y magenta, y un sutil grano de película, que evoca un póster coleccionable de alta calidad. Calidad de obra maestra, resolución 8k, textura de piel hiperdetallada con poros y gotas de sudor visibles, iluminación cinematográfica, audacia de novela gráfica, composición которая, claroscuro dramático.\nNEGATIVE PROMPT: (worst quality, low quality:1.4), (anime, cartoon:1.3), (text, watermark:1.3), blurry, deformed, bad anatomy",
        "estilos": ["Cinematográfico", "Póster"],
    },
    {
        "titulo": "Pop electrónico melancólico",
        "modo": "audio",
        "modelo": "Suno v5",
        "plataforma": "Suno",
        "dificultad": "principiante",
        "tags": ["pop", "electrónica", "melancólico", "castellano"],
        "autor": "Gustaafvito",
        "prompt": "ESTILO: Synthpop, Electropop, Melancholic, Dreamy, Reverb-heavy vocals, Atmospheric pads, 80s inspired, Minor key\n\n[Intro]\nFloating synth pads, slow build\n\n[Verse 1]\nLost in neon corridors of memory\nEvery echo sounds like your goodbye\nDigital tears on a pixel screen\nWe were electric, now just a dream\n\n[Chorus]\nFading signals in the night\nWe were stars that lost their light\nFading signals, can't rewind\nLeaving frequencies behind",
        "estilos": ["Pop", "Electrónica"],
    },
    {
        "titulo": "Retrato cyberpunk con reflejos neon",
        "modo": "imagen",
        "modelo": "Z Image Turbo",
        "plataforma": "SeaArt / Tensor.Art",
        "dificultad": "principiante",
        "tags": ["retrato", "close-up", "cyberpunk", "pesos numéricos"],
        "autor": "Gustaafvito",
        "prompt": "POSITIVE PROMPT: (close-up portrait:1.3), 1girl, cyberpunk city reflection in eyes, (neon lights:1.4), wet skin, rain drops on face, (chromatic aberration:1.2), dark alley background, purple and teal color palette, (cinematic lighting:1.3), sharp focus, 8K, masterpiece, highly detailed\nNEGATIVE PROMPT: (worst quality, low quality:1.4), (anime, cartoon:1.3), (text, watermark:1.3), blurry, deformed",
        "estilos": ["Cyberpunk / Neon", "Retrato"],
    },
    {
        "titulo": "Steampunk Wonderland infografía",
        "modo": "imagen",
        "modelo": "Z Image Turbo",
        "plataforma": "SeaArt / Tensor.Art",
        "dificultad": "avanzado",
        "tags": ["steampunk", "infografía", "vintage", "tipografía"],
        "autor": "Gustaafvito",
        "prompt": "POSITIVE PROMPT: (composición infográfica vertical 16:9:1.3), (diseño de tríptico: título de la pancarta superior, ilustración principal central, paneles de información inferiores:1.3), (primer plano: setas de latón gigantes con rejillas de ventilación de vapor brillantes:1.4), (punto medio: dirigible de tetera flotante con casco de cobre:1.3), (fondo: silueta de castillo de relojería contra el cielo de cobre:1.4), (tipografía victoriana dorada: País de las maravillas steampunk en estilo art nouveau:1.4), (detalles mecánicos intrincados: engranajes, remaches, manómetros:1.3), (texturas de pátina de cobre oxidado:1.3), (reflejos de latón pulido:1.2), (patrones de filigrana victoriana grabados en metal:1.4), (condensación de vapor en superficies de latón:1.2), (pintura digital mate:1.3), (bordes ornamentales de estilo art nouveau:1.3), (atmósfera onírica surrealista:1.2), (islas flotantes en el fondo:1.1), (estructuras geométricas imposibles:1.1), (iluminación lateral dramática de las rejillas de ventilación de vapor:1.3), (mezcla de luz cálida ámbar con sombras frías verdeazuladas:1.2), (rayos de dios volumétricos a través de partículas de vapor:1.4), (luz de borde en bordes de latón:1.3), (ámbar, verdete y paleta de colores dorados:1.2), (mariposas de relojería brillantes:1.2), (planetario a vapor en el fondo:1.3), (ultra detallado:1.3), 8k, obra maestra\nNEGATIVE PROMPT: (worst quality, low quality, lowres:1.4), (anime, cartoon, 3d render:1.3), (text, watermark, signature:1.3), (deformed, distorted, asymmetric:1.2), (blurry, jpeg artifacts:1.2), (oversaturated colors:1.3), (plastic texture:1.3), (depth of field error:1.2), (chromatic aberration:1.2), (grainy noise:1.2), (flat lighting:1.3), (underexposed shadows:1.2), (blown out highlights:1.2), (motion blur:1.2)",
        "estilos": ["Steampunk", "Infografía"],
    },
]


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
    for spec in (MODEL_SPECS, MODEL_SPECS_IMAGEN, MODEL_SPECS_AUDIO):
        modelos_validos.update(spec.keys())

    # Construir conjunto de plataformas válidas
    plataformas_validas = (
        set(PLATAFORMAS_IMAGEN.keys())
        | set(PLATAFORMAS_VIDEO.keys())
        | set(PLATAFORMAS_AUDIO.keys())
    )

    # Detectar títulos duplicados
    titulos_vistos = {}
    for i, entrada in enumerate(BIBLIOTECA_EJEMPLOS):
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

    modelos_en_specs = set(MODEL_SPECS_IMAGEN.keys())

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

    modelos_video_specs = set(MODEL_SPECS.keys())

    for m in modelos_video_lista:
        if m not in modelos_video_specs:
            problemas.append(f"Modelo '{m}' en GRUPOS_VIDEO pero sin spec en MODEL_SPECS")

    # Audio
    modelos_audio_lista = set()
    for g, ms in GRUPOS_AUDIO:
        for m in ms:
            modelos_audio_lista.add(m)

    modelos_audio_specs = set(MODEL_SPECS_AUDIO.keys())

    for m in modelos_audio_lista:
        if m not in modelos_audio_specs:
            problemas.append(f"Modelo '{m}' en GRUPOS_AUDIO pero sin spec en MODEL_SPECS_AUDIO")

    return problemas
