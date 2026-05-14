"""
G-Prompt Studio v1.0 — Configuración y constantes.
Modelos, estilos, ratios, presets de negativos, colores UI.
"""
from pathlib import Path

# ── Versión ───────────────────────────────────────────────────────
VERSION = "1.0.9"
PUBLIC_VERSION = "1.0"
APP_TITLE = f"🧠 G-Prompt Studio v{PUBLIC_VERSION}"

# ── Persistencia ──────────────────────────────────────────────────
CARPETA_APP = Path.home() / ".arquitecto_prompts"
CARPETA_APP.mkdir(exist_ok=True)

ARCHIVOS = {
    "historial":     CARPETA_APP / "historial.json",
    "favoritos":     CARPETA_APP / "favoritos.json",
    "personajes":    CARPETA_APP / "personajes.json",
    "plantillas":    CARPETA_APP / "plantillas.json",
    "loras":         CARPETA_APP / "loras.json",
    "preferencias":  CARPETA_APP / "preferencias.json",
    "estrellas":     CARPETA_APP / "estrellas.json",
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
        "Wan 2.6", "Sora2 Video", "Veo 3.1",
    ])),
]

# ══════════════════════════════════════════════════════════════════
# MODELOS DE IMAGEN
# ══════════════════════════════════════════════════════════════════
GRUPOS_IMAGEN = [
    ("── SeaArt Oficiales ──", sorted([
        "SeaArt Infinity",
        "SeaArt Infinity V2.0",
    ])),
    ("── Familia Z-Image ──", sorted([
        "Z Image Turbo",
        "Z-Image-Base-Realistic",
    ])),
    ("── Realismo SD ──", sorted([
        "Illustrious Realism by Klaabu",
        "Real Dream SDXL",
        "MajicMIX Realistic v6",
        "Realities Edge XL Turbo V7",
        "CyberRealistic",
        "Realistic Vision V6.0",
        "Prodigies",
        "DreamShaper",
    ])),
    ("── Anime / Ilustración ──", sorted([
        "NiwaStyle - Animax ColorPop",
        "NiwaStyle - Animax Plus",
        "NiwaStyle - Animax Chill",
        "Pipi-iL-CG6.5",
    ])),
    ("── Familia FLUX ──", sorted([
        "Mix Max Cinematic Realism",
        "FLUX.1 [dev]",
        "FLUX.1-dev-fp8",
        "FLUX.1",
        "FLUX.1D UltraReal",
        "MASTER FLUX (LoRA merged with flux1-dev fp16)",
    ])),
    ("── Nano Banana ──", sorted([
        "Nano Banana Pro Image", "Nano Banana 2",
    ])),
]

# ══════════════════════════════════════════════════════════════════
# MODELOS DE IMAGEN — ESPECÍFICOS PARA COMFYUI / A1111 / FORGE
# (Solo los que el usuario tiene instalados localmente)
# ══════════════════════════════════════════════════════════════════
GRUPOS_IMAGEN_COMFYUI = [
    ("── Checkpoints SDXL ──", sorted([
        "Juggernaut-XL v9 RunDiffusionPhoto v2",
        "RealVisXL V5.0 fp16",
        "JuggernautXL Ragnarok",
    ])),
    ("── Familia Z-Image ──", sorted([
        "z_image_bf16 (Base)",
        "z_image_turbo_bf16 (Turbo)",
        "zImageBase_base",
    ])),
    ("── Familia FLUX (UNet) ──", sorted([
        "flux-2-klein-base-4b-fp8",
    ])),
    ("── Edit ──", sorted([
        "qwen_image_edit_2509_fp8_e4m3fn",
    ])),
]
MODELOS_IMAGEN_COMFYUI_FLAT = []
for g, ms in GRUPOS_IMAGEN_COMFYUI:
    MODELOS_IMAGEN_COMFYUI_FLAT.append(g)
    MODELOS_IMAGEN_COMFYUI_FLAT.extend(ms)

# ══════════════════════════════════════════════════════════════════
# MODELOS DE VÍDEO PARA COMFYUI (locales)
# ══════════════════════════════════════════════════════════════════
GRUPOS_VIDEO_COMFYUI = [
    ("── Wan 2.2 (Image-to-Video) ──", sorted([
        "wan2.2_i2v_high_noise_14B_fp8_scaled",
        "wan2.2_i2v_low_noise_14B_fp8_scaled",
    ])),
    ("── LTX-Video ──", sorted([
        "ltx-2.3-22b-dev-fp8",
    ])),
    ("── Stable Video ──", sorted([
        "svd",
    ])),
]
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

# Modelos exclusivos de DALL-E (ChatGPT)
GRUPOS_DALLE_IMAGEN = [
    ("── OpenAI ──", sorted([
        "DALL-E 3 (legacy)", "GPT Image 1", "GPT Image 1.5", "GPT Image 2",
    ])),
]
MODELOS_DALLE_IMAGEN_FLAT = _lista_plana(GRUPOS_DALLE_IMAGEN)

# Modelos exclusivos de Midjourney
GRUPOS_MIDJOURNEY_IMAGEN = [
    ("── Midjourney ──", sorted([
        "Midjourney v6.1",
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
    "SeaArt / Tensor.Art":        MODELOS_IMAGEN_FLAT,
    "ComfyUI / A1111 / Forge":    MODELOS_IMAGEN_COMFYUI_FLAT,
    "Midjourney":                  MODELOS_MIDJOURNEY_IMAGEN_FLAT,
    "DALL-E (ChatGPT)":            MODELOS_DALLE_IMAGEN_FLAT,
    "Ideogram / Recraft":          MODELOS_IDEOGRAM_IMAGEN_FLAT,
    "Magnific":                    MODELOS_MAGNIFIC_IMAGEN_FLAT,
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
        "Studio Shot", "Product Photography", "Foodie", "Phone Photo",
        "Low-key Cinematic", "Cinematic Still", "Documental",
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
    ],
    "💥 Cómic & Manga": [
        "Comic Book", "Retro Comic", "Western Comic", "Marvel/DC Style",
        "Manga (Black & White)", "Manga Color", "Shonen", "Shojo", "Seinen",
        "Webtoon / Manhwa", "Comic Strip", "Graphic Novel",
        "Anime / Ilustración", "Anime 90s Retro", "Anime Classic",
        "Studio Ghibli", "Chibi / Kawaii", "Cartoon",
        "Cartoon Fun", "Cute Cartoon", "Whimsy Anime",
        "Speech Bubbles", "Halftone Print", "Inked Style",
    ],
    "🚀 Digital & 3D": [
        "3D Render", "Pixar / Disney 3D", "Character 3D", "Glossy 3D Icon",
        "Plushy / Stuffed Toy", "Vinyl Toy", "Amigurumi 3D", "Felt 3D",
        "Squishy 3D", "Claytoon / Plasticine", "Origami", "Stop Motion",
        "Cyberpunk / Neon", "Sci-Fi", "Retro / Synthwave", "Vaporwave / Aesthetic",
        "Isometric", "Low Poly", "Pixel Art", "Voxel Art",
        "Holography", "Iridescent / Pearlescent", "Chrome / Metallic",
        "Glass / Translucent", "Liquid / Fluid", "Dreamglass",
    ],
    "🎬 Cine & TV": [
        "Cinematic Lighting", "Film Noir", "Concrete Noir", "Silent Noir",
        "Movie Poster", "Trailer Style", "Music Video", "Videoclip",
        "70s Vibe", "80s Couture", "Found Footage", "VHS Aesthetic",
        "Old Money Still", "Cinematic Pastel", "Vibrant Film",
    ],
    "🎯 Diseño Gráfico": [
        "Minimalista", "Bold Poster", "Letterpop", "RetroGrid",
        "Neo Memphis", "Paper Noise", "Glitch Collage", "Halftone",
        "Typography Heavy", "Bold Typo", "Vector / Flat",
        "Vintage Vector", "Simple Vector", "Indie Poster",
        "Sticker Icon", "Pixel Icon", "3D Icon",
    ],
    "🌑 Oscuro & Fantasy": [
        "Fantasy Épica", "Dark Fantasy", "Gothic / Oscuro", "Tarot / Místico",
        "Terror / Horror", "Halloween", "Cursed", "Sinister Nights",
        "Scary Times", "Burnt Velvet", "Dark Concept", "Lucid Sci-Fi",
        "Steampunk", "Mistery Mist", "Foggy", "Surreal Fashion",
    ],
    "✨ Estética & Mood": [
        "Pastel Aesthetic", "Pink History", "Pink Whimsical", "Coquette",
        "Soft Float", "Soft Muted", "Coolpastel", "Softpasty", "Softprism",
        "Peachy", "Trendy Mocha", "Warm Cozy", "Mediterranean",
        "Italian Vibes", "Cozy Coffee Shop", "Botanical Folk", "Floral Elegance",
        "Glimmerish", "Sparkling", "Aetherial", "Dreamy Mini",
    ],
    "🎭 Editorial & Fashion": [
        "Vogue Editorial", "Runway Fashion", "High Fashion", "Editorial Glow",
        "Editorial Portrait", "Cover Art", "Avant Garde", "Stylized Cyber",
        "Symbolic Editorial", "Neon Editorial", "Boldproduct",
    ],
    "👶 Infantil & Juguete": [
        "Children's Story", "Childbook Illustration", "Storybook",
        "Sunset Cartoon", "Fresh Cartoon", "Cute Grainy", "Kawaii",
        "Mini World", "Squishy", "Plushies", "Adorable", "Cute Cartoon",
    ],
    "🏛 Otros estilos": [
        "Architecture", "Interior Design", "Eclectic Mocking", "Eclectic Decor",
        "Mockup / Phone Photo", "Tshirt Mockup", "Laptop Mockup",
        "Coffee Shop Mockup", "Branding in the Wild", "Italian Vibes",
        "Pinup Vintage", "Space / Cosmic", "Underwater Scene",
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
    "DALL-E (ChatGPT)":            "natural",
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
    "Sora / Veo": ["Sora2 Video", "Veo 3.1"],
}

MOTORES_AUDIO = {
    "Suno": ["Suno v5", "Suno v4.5", "Suno v4"],
    "SeaArt Audio": ["Minimax Music 2.5", "SeaArt MusicGo"],
}

MOTOR_DEFAULT = {
    "SeaArt Video": "Kling 3.0",
    "Kling AI": "Kling 3.0",
    "Suno": "Suno v5",
    "SeaArt Audio": "Minimax Music 2.5",
}

# ── Límites de Tokens por Plataforma ─────────────────
TOKEN_LIMITS = {
    "SeaArt / Tensor.Art": 200,
    "ComfyUI / A1111 / Forge": 75,
    "Midjourney": 60,
    "DALL-E (ChatGPT)": 75,
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
        "nota": 4.4,
        "has_negative": True,
        "has_audio": False,
        "audio_desc": "Subir audio manual (MP3/WAV/AAC/M4A, 3-30s, <15MB)",
        "duraciones": ["5s", "10s", "15s"],
        "ratios": ["9:16", "16:9", "1:1"],
        "max_chars": 2000,
        "modos_gen": ["Estándar", "Calidad", "Ultra HD", "Profesional"],
        "best_for": "OpenAI Sora integrado en SeaArt. 172K usos. Image-to-Video + Text-to-Video. Prompt negativo. Magia de sugerencia.",
        "prompt_formula": "Subject + action + camera + setting + mood. Prompts descriptivos cinematográficos.",
        "prompt_ejemplo": "A lone astronaut floating above Earth, helmet reflecting blue planet, slow rotation, stars in background, epic cinematic scale.",
        "limitaciones": "Sin audio nativo (subida manual). Coste variable.",
    },
    "Veo 3.1": {
        "nota": 4.2,
        "has_negative": False,
        "has_audio": False,
        "audio_desc": "",
        "duraciones": ["4s", "6s", "8s"],
        "ratios": ["9:16", "16:9"],
        "max_chars": 1500,
        "modos_gen": ["720p", "1080p"],
        "best_for": "Google Veo integrado en SeaArt. 2.8K usos (nuevo). Solo 2 ratios (9:16, 16:9). Duración corta (4-8s). Image-to-Video + Text-to-Video.",
        "prompt_formula": "Subject + action + camera + style. Prompts concisos y directos.",
        "prompt_ejemplo": "A person walking through a foggy forest path, mysterious atmosphere, cinematic lighting, 1080p.",
        "limitaciones": "Sin audio, sin prompt negativo. Solo 2 ratios. Máx 8s. Modelo nuevo con pocos usos.",
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
    "NiwaStyle - Animax ColorPop": {
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
    # ── Nano Banana ──────────────────────────────────────────
    "Nano Banana Pro Image": {
        "nota": 4.5,
        "has_negative": False,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "3:4"],
        "max_chars": 2000,
        "modos_gen": ["Estándar"],
        "max_imagenes": 8,
        "best_for": "Motor Gemini 3 Pro. Edición de imágenes con lenguaje natural. Subir imagen de referencia + prompt de texto para transformar. Alta precisión en instrucciones complejas.",
        "prompt_formula": "Lenguaje natural descriptivo. Describe la escena o las modificaciones deseadas en prosa fluida.",
        "prompt_ejemplo": "A cinematic portrait of a woman in a red coat standing in the rain, soft bokeh background, dramatic lighting",
        "coste_energia": "Variable",
        "limitaciones": "Sin sampler/CFG/negative (motor Gemini, no SD). Orientado a edición de imagen más que generación desde cero. Max 14 imágenes de referencia.",
    },
    "Nano Banana 2": {
        "nota": 4.7,
        "has_negative": False,
        "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9"],
        "max_chars": 2500,
        "modos_gen": ["Estándar", "Pro"],
        "max_imagenes": 14,
        "best_for": "Motor Gemini 3 Pro Image. Siguiente generación de Nano Banana Pro. Mayor fidelidad, mejor comprensión de instrucciones complejas, coherencia superior en composiciones. Excelente para edición avanzada con múltiples referencias, texto en imagen, composición precisa con objetos específicos en posiciones exactas.",
        "prompt_formula": "Lenguaje natural detallado. Describe escena, sujeto, entorno, iluminación, cámara y estilo en prosa fluida. Puede seguir instrucciones espaciales precisas ('X a la izquierda de Y').",
        "prompt_ejemplo": "A hyper-realistic photo of a vintage leather-bound book on a wooden desk, with a steaming cup of coffee to the right and a pair of round glasses placed on top of the book. Warm morning light streams through a window, creating soft shadows. Shallow depth of field, 85mm lens.",
        "coste_energia": "Variable (más alto que Pro Image)",
        "limitaciones": "Sin sampler/CFG/negative (motor Gemini, no SD). Sin prompt negativo. Orientado a calidad profesional sobre velocidad.",
    },
    # ── Anime / Ilustración ─────────────────────────────────
    "NiwaStyle - Animax Plus": {
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
    "NiwaStyle - Animax Chill": {
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
    # ══════════════════════════════════════════════════════════════
    "Midjourney v6.1": {
        "nota": 4.8, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9", "4:5", "5:4", "21:9"],
        "max_chars": 4000, "modos_gen": ["Standard", "Turbo", "Relax"],
        "best_for": "Estándar de la industria en imagen generativa. Mejor estética cinematográfica. Excelente para arte conceptual, fotografía, ilustración. Sintaxis natural + parámetros CLI (--ar, --stylize, --weird, --chaos, --no, --sref).",
        "prompt_formula": "Lenguaje natural descriptivo + parámetros CLI al final. Estructura: scene + subject + style + lighting + mood --ar X:Y --stylize 100-1000 --no [exclusions].",
        "prompt_ejemplo": "Cinematic portrait of an elderly fisherman at sunset, weathered face, deep blue ocean background, golden hour lighting, shot on 35mm film, photographic style --ar 16:9 --stylize 250 --no boat, watermark",
        "limitaciones": "Sin negative prompt tradicional (usar --no). Sin pesos numéricos estilo SD. Solo accesible vía Discord o web app oficial.",
    },

    # ══════════════════════════════════════════════════════════════
    # DALL-E / GPT Image (OpenAI)
    # ══════════════════════════════════════════════════════════════
    "DALL-E 3 (legacy)": {
        "nota": 4.0, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 4000, "modos_gen": ["Standard", "HD"],
        "best_for": "Modelo OpenAI legacy (pre-2025). Bueno para conceptos creativos, ilustración, arte estilizado. Reemplazado por GPT Image en ChatGPT.",
        "prompt_formula": "Lenguaje natural muy descriptivo. ChatGPT reescribe automáticamente el prompt para añadir detalles.",
        "prompt_ejemplo": "A vibrant illustration of a cyberpunk cat playing a holographic guitar in a neon-lit alleyway, colorful, detailed, digital art style",
        "limitaciones": "Sin pesos, sin negative. Solo 3 ratios. Reemplazado por GPT Image series.",
    },
    "GPT Image 1": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "1024x1024", "1024x1536", "1536x1024"],
        "max_chars": 4000, "modos_gen": ["Low", "Medium", "High"],
        "best_for": "Primer GPT Image (Marzo 2025). Modelo nativo multimodal de GPT-4o. Excelente integración con ChatGPT, mejor que DALL-E 3 en text-in-image y composición compleja. Famoso por estilo Studio Ghibli viral.",
        "prompt_formula": "Lenguaje natural en prosa fluida. Estructura: background/scene → subject → key details → constraints + intended use (ad, UI, infographic).",
        "prompt_ejemplo": "Create a photorealistic portrait of an elderly sailor on a fishing boat at dawn, weathered face, soft coastal light, 35mm film aesthetic, medium close-up at eye level",
        "limitaciones": "Warm color bias en muchas salidas. Sin negative prompt. Cropping prematuro a veces. Sin pesos numéricos.",
    },
    "GPT Image 1.5": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "1024x1024", "1024x1536", "1536x1024", "9:16", "16:9"],
        "max_chars": 4000, "modos_gen": ["Low", "Medium", "High"],
        "best_for": "GPT Image 1.5 (Diciembre 2025). 4x más rápido que GPT Image 1. Mejor edición de imagen, preserva detalles, branding consistente. Inputs/outputs 20% más baratos. Excelente para ecommerce y branding.",
        "prompt_formula": "Lenguaje natural estructurado. Para edición: 'Change X to Y, keep Z intact'. Para generación: scene → subject → details → style → constraints.",
        "prompt_ejemplo": "Edit this product photo: change the background to a clean white studio with soft shadows, keep the product, lighting and proportions exactly as they are, photorealistic",
        "limitaciones": "Sigue sin negative prompt ni pesos. Algunas regresiones en estilos artísticos respecto a GPT Image 1.",
    },
    "GPT Image 2": {
        "nota": 4.9, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "2:3", "3:2", "9:16", "16:9", "4:5", "5:4"],
        "max_chars": 5000, "modos_gen": ["Low", "Medium", "High"],
        "best_for": "GPT Image 2 (Abril 2026). Modelo más reciente con razonamiento integrado. Text rendering casi perfecto, screenshots realistas, fotorrealismo top. Capacidades de búsqueda web y multi-imagen desde un prompt.",
        "prompt_formula": "Lenguaje natural muy estructurado. Estructura: background/scene → subject → key details → constraints + intended use. Usar lenguaje fotográfico (lens, lighting, framing) y pedir texturas reales (poros, arrugas, imperfecciones).",
        "prompt_ejemplo": "Photorealistic candid photo of an elderly fisherman on his boat at dawn. Weathered skin with visible pores and sun texture, faded sailor tattoos. Adjusting nets while his dog sits nearby. Shot like 35mm film, 50mm lens, soft coastal daylight, shallow DOF, subtle film grain. Honest, unposed feel.",
        "limitaciones": "Sin negative ni pesos. Solo accesible vía ChatGPT o API OpenAI.",
    },

    # ══════════════════════════════════════════════════════════════
    # IDEOGRAM / RECRAFT
    # ══════════════════════════════════════════════════════════════
    "Ideogram v3": {
        "nota": 4.6, "has_negative": True, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "16:10", "10:16", "3:2", "2:3"],
        "max_chars": 4000, "modos_gen": ["Default", "Quality", "Turbo"],
        "best_for": "Líder en text-in-image. Rendering de tipografías, logos, posters. Excelente para diseño gráfico, branding, social media con texto visible.",
        "prompt_formula": "Lenguaje natural + tipografía explícita. Para texto: poner el texto entre comillas. Soporta negative prompt nativo.",
        "prompt_ejemplo": 'A vintage 1970s rock concert poster with bold typography saying "MIDNIGHT TOUR" in golden letters, psychedelic background, bright colors, retro design',
        "limitaciones": "Calidad fotográfica menor que Mystic/FLUX. Mejor para diseño con texto que para foto pura.",
    },
    "Recraft v3": {
        "nota": 4.5, "has_negative": True, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "2:3", "3:2"],
        "max_chars": 3000, "modos_gen": ["Standard", "HD"],
        "best_for": "Especializado en arte vectorial, ilustraciones consistentes, branding. Excelente para diseñadores. Genera SVG editable.",
        "prompt_formula": "Lenguaje natural + estilo vectorial. Mencionar 'flat illustration', 'vector art', 'icon style' funciona muy bien.",
        "prompt_ejemplo": "Flat vector illustration of a cozy coffee shop at night, warm color palette, geometric shapes, minimalist design, no gradients",
        "limitaciones": "No hace fotorrealismo. Mejor para gráfico/vectorial. Salida SVG no siempre limpia.",
    },

    # ══════════════════════════════════════════════════════════════
    # MAGNIFIC (antes Freepik AI) — TODOS LOS MODELOS DISPONIBLES (Marzo 2026)
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
        "max_chars": 5000, "modos_gen": ["Standard", "Quality"],
        "best_for": "GPT Image 2 en Magnific (Destacado/Nuevo). Salida 2K-4K. ~1m 27s de generación. El más reciente con razonamiento integrado, text rendering casi perfecto, fotorrealismo top.",
        "prompt_formula": "Lenguaje natural muy estructurado. Estructura: scene → subject → key details → constraints + intended use. Lenguaje fotográfico (lens, lighting, framing) y texturas reales.",
        "prompt_ejemplo": "Photorealistic candid photo of an elderly fisherman on his boat at dawn. Weathered skin with visible pores, sun texture. Adjusting nets, dog nearby. 35mm film aesthetic, 50mm lens, soft coastal daylight, shallow DOF.",
        "limitaciones": "Lento (~1m 27s). Sin negative ni pesos. Soporta referencias.",
    },
    "GPT 1.5 - High": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2"],
        "max_chars": 4000, "modos_gen": ["High"],
        "best_for": "GPT Image 1.5 alta calidad en Magnific. ~59s. Buena edición de imagen, preserva detalles, branding consistente.",
        "prompt_formula": "Lenguaje natural estructurado. Para edición: 'Change X to Y, keep Z intact'.",
        "prompt_ejemplo": "Edit this product photo: change the background to a clean white studio with soft shadows, keep the product, lighting and proportions exactly as they are",
        "limitaciones": "Sin negative prompt ni pesos.",
    },
    "GPT 1.5": {
        "nota": 4.6, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2"],
        "max_chars": 4000, "modos_gen": ["Standard"],
        "best_for": "GPT Image 1.5 estándar. ~41s. 4x más rápido que GPT 1, mejor edición, preserva detalles.",
        "prompt_formula": "Lenguaje natural estructurado.",
        "prompt_ejemplo": "Modern poster design with bold typography, minimalist layout, gradient background, professional design",
        "limitaciones": "Sin negative ni pesos.",
    },
    "GPT 1 - HQ": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 4000, "modos_gen": ["HQ"],
        "best_for": "GPT Image 1 alta calidad. ~1m 3s. Modelo viral por estilo Studio Ghibli. Excelente integración multimodal.",
        "prompt_formula": "Lenguaje natural en prosa. Estructura: scene → subject → details → style.",
        "prompt_ejemplo": "Studio Ghibli style illustration of a young girl walking through a field of sunflowers at dusk, soft warm light, dreamy atmosphere",
        "limitaciones": "Lento (~1m 3s). Warm color bias. Sin negative ni pesos.",
    },
    "GPT": {
        "nota": 4.3, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 3000, "modos_gen": ["Standard"],
        "best_for": "GPT Image base. ~40s. Versión rápida y económica.",
        "prompt_formula": "Lenguaje natural simple. Soporta referencias.",
        "prompt_ejemplo": "A vibrant illustration of a cyberpunk cat in a neon-lit alleyway, colorful, detailed",
        "limitaciones": "Calidad inferior a GPT 1.5/2. Sin negative.",
    },

    # ── Familia Flux ─────────────────────────────────────
    "Flux.2 Max": {
        "nota": 4.8, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2", "4:3", "3:4"],
        "max_chars": 4000, "modos_gen": ["Max"],
        "best_for": "Flux 2 Max en Magnific. Salida 2K. ~38s. Máxima calidad de la familia Flux 2. Ideal para hero shots, branding crítico.",
        "prompt_formula": "Lenguaje natural muy descriptivo y específico. Flux 2 entiende prompts complejos con múltiples sujetos y relaciones espaciales.",
        "prompt_ejemplo": "A high-end fashion editorial photograph of a model standing in a brutalist concrete corridor, dramatic side lighting from a single skylight, wearing a sculptural black dress, photorealistic, magazine quality",
        "limitaciones": "Sin negative ni pesos. Más lento que Pro.",
    },
    "Flux.2 Pro": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2", "4:3", "3:4"],
        "max_chars": 4000, "modos_gen": ["Pro"],
        "best_for": "Flux 2 Pro. Salida 2K. ~22s. Producción profesional, alta resolución, fotorrealismo top, hasta 10 imágenes ref. Para uso comercial intensivo.",
        "prompt_formula": "Lenguaje natural fluido + tipografía explícita si necesitas texto. Hasta 10 referencias.",
        "prompt_ejemplo": "Professional product photo of a luxury watch on dark velvet, soft directional lighting from upper left, macro detail, sharp focus on dial, depth of field",
        "limitaciones": "Sin negative ni pesos.",
    },
    "Flux.2 Flex": {
        "nota": 4.6, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2"],
        "max_chars": 4000, "modos_gen": ["Flex"],
        "best_for": "Flux 2 Flex. Salida 2K. ~25s. Especializado en TIPOGRAFÍA y detalles finos. El mejor cuando el texto en imagen es crítico.",
        "prompt_formula": "Para texto: usar comillas y describir tipografía explícitamente. 'Bold serif typeface', 'handwritten script', etc.",
        "prompt_ejemplo": 'Vintage diner sign with the text "DINER" in bold red retro typography, neon accent, weathered metal background, 1950s aesthetic',
        "limitaciones": "Optimizado para texto. Para foto pura, Pro o Max son mejores.",
    },
    "Flux.2 Klein": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 3000, "modos_gen": ["Klein"],
        "best_for": "Flux 2 Klein. Salida 2K. ⚡ ~7s (RÁPIDO). Compacto para generación en tiempo real. Para iteración rápida.",
        "prompt_formula": "Lenguaje natural conciso. Optimizado para velocidad.",
        "prompt_ejemplo": "A red apple on a wooden table, soft natural light from the right, photorealistic",
        "limitaciones": "Calidad menor que Pro/Max pero muy rápido.",
    },
    "Flux.1 Kontext Max": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2"],
        "max_chars": 4000, "modos_gen": ["Max"],
        "best_for": "Flux 1 Kontext Max. ~18s. Modelo de EDICIÓN avanzada. Preserva contexto entre ediciones múltiples.",
        "prompt_formula": "Instrucciones de edición específicas: 'Change [elemento] to [nuevo]', 'Keep [elemento] exactly the same', 'Add [elemento] to [posición]'.",
        "prompt_ejemplo": "Change the woman's dress from red to emerald green, keep her face, hair, pose and lighting exactly the same",
        "limitaciones": "Especializado en edición. Para generación desde cero, otros Flux son mejores.",
    },
    "Flux.1 Kontext Pro": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 3000, "modos_gen": ["Pro"],
        "best_for": "Flux 1 Kontext Pro. ~13s. Edición rápida con preservación de contexto.",
        "prompt_formula": "Instrucciones de edición concisas y específicas.",
        "prompt_ejemplo": "Add subtle bokeh background blur, keep subject sharp",
        "limitaciones": "Para edición. Más rápido que Max pero menos preciso.",
    },
    "Flux.1 Realism": {
        "nota": 4.6, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2"],
        "max_chars": 3000, "modos_gen": ["Realism"],
        "best_for": "Flux 1 Realism. ⚡ ~8s. Optimizado para FOTORREALISMO. Pieles, texturas, escenarios fotográficos.",
        "prompt_formula": "Lenguaje natural fotográfico. Mencionar lente, distancia focal, tipo de cámara mejora resultados.",
        "prompt_ejemplo": "Candid photograph of a barista preparing coffee, shallow depth of field, 50mm lens, natural window light, film grain",
        "limitaciones": "Para arte estilizado, Flux 2 Max es mejor.",
    },
    "Flux.1 Fast": {
        "nota": 4.3, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 2500, "modos_gen": ["Fast"],
        "best_for": "Flux 1 Fast. ⚡ ~8s. Velocidad máxima en familia Flux 1. Ideal para iteración rápida y exploración.",
        "prompt_formula": "Prompts cortos y directos.",
        "prompt_ejemplo": "A cat in a garden, golden hour light",
        "limitaciones": "Calidad más baja que Realism o 1.1.",
    },
    "Flux.1.1": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 3000, "modos_gen": ["Standard"],
        "best_for": "Flux 1.1 ULTRA RÁPIDO. ⚡ ~6s. Mejorado respecto Flux 1 base.",
        "prompt_formula": "Lenguaje natural fluido.",
        "prompt_ejemplo": "A young woman with curly hair laughing, soft studio lighting, professional portrait",
        "limitaciones": "Para máxima calidad usar Flux 2 Max o Pro.",
    },
    "Flux.1": {
        "nota": 4.3, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 3000, "modos_gen": ["Standard"],
        "best_for": "Flux 1 base. ~17s. El primer Flux de Black Forest Labs.",
        "prompt_formula": "Lenguaje natural descriptivo.",
        "prompt_ejemplo": "A serene mountain landscape at sunset, dramatic clouds, vibrant colors",
        "limitaciones": "Reemplazado por versiones más recientes.",
    },

    # ── Mystic ─────────────────────────────────────────
    "Mystic 2.5 Fluid": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "2:3", "3:2"],
        "max_chars": 3000, "modos_gen": ["Fluid"],
        "best_for": "Mystic 2.5 Fluid. ~24s. 80 créditos. Hiperrealismo nativo de Magnific basado en Flux + tecnología de upscaling Magnific. 2K nativo. El mejor para retratos, expresiones faciales.",
        "prompt_formula": "Lenguaje natural muy descriptivo. Soporta texto en imagen con comillas.",
        "prompt_ejemplo": "A young woman with long brown hair wearing a yellow dress against a patterned background, natural skin texture, individual hair strands, soft daylight, 2K resolution",
        "limitaciones": "Costoso (80 créditos). Para diseño con texto, otros como Ideogram funcionan mejor.",
    },

    # ── Google Imagen ─────────────────────────────────
    "Google Imagen 4 Ultra": {
        "nota": 4.8, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"],
        "max_chars": 3000, "modos_gen": ["Ultra"],
        "best_for": "Google Imagen 4 Ultra. ~18s. Fotorrealismo top de Google. Excelente entendimiento espacial y físico. Ideal para escenas complejas.",
        "prompt_formula": "Lenguaje natural muy descriptivo. Imagen entiende relaciones espaciales precisas.",
        "prompt_ejemplo": "A red coffee mug placed on a wooden desk to the right of an open notebook, soft morning light streaming through a window from the left, shallow depth of field",
        "limitaciones": "Sin negative.",
    },
    "Google Imagen 4": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"],
        "max_chars": 3000, "modos_gen": ["Standard"],
        "best_for": "Google Imagen 4. ⚡ ~10s. Fotorrealismo + rápido. Buen balance velocidad/calidad.",
        "prompt_formula": "Lenguaje natural descriptivo con relaciones espaciales claras.",
        "prompt_ejemplo": "A photorealistic portrait of a young woman with auburn hair, soft natural lighting from a window on the left, blurred forest background",
        "limitaciones": "Menos detalle que Imagen 4 Ultra.",
    },
    "Google Imagen 3": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 2500, "modos_gen": ["Standard"],
        "best_for": "Google Imagen 3. ⚡ ~9s. Generación rápida calidad media.",
        "prompt_formula": "Lenguaje natural simple.",
        "prompt_ejemplo": "A cat sitting in a garden of wildflowers, sunny day, photorealistic",
        "limitaciones": "Reemplazado por Imagen 4. Calidad menor.",
    },

    # ── Seedream ──────────────────────────────────────
    "Seedream 5 Lite": {
        "nota": 4.7, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "2:3", "3:2"],
        "max_chars": 3000, "modos_gen": ["Lite"],
        "best_for": "Seedream 5 Lite (Destacado/Nuevo). Salida 2K. ~51s. Modelo más reciente de ByteDance. Excelente para fotorrealismo y arte.",
        "prompt_formula": "Lenguaje natural muy descriptivo. Soporta múltiples sujetos y composiciones complejas.",
        "prompt_ejemplo": "A cinematic shot of two friends sitting at a vintage diner counter, neon reflections on the chrome surface, warm dramatic lighting, 35mm film aesthetic",
        "limitaciones": "Más lento que Flux Klein.",
    },
    "Seedream 4.5": {
        "nota": 4.6, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "2:3", "3:2"],
        "max_chars": 3000, "modos_gen": ["High Resolution"],
        "best_for": "Seedream 4.5. Salida 2K-4K. ~1m 5s. Alta resolución, fotorrealismo, soporta referencias.",
        "prompt_formula": "Lenguaje natural detallado. Mencionar resolución target.",
        "prompt_ejemplo": "Highly detailed product photo of a luxury watch, macro lens, perfect studio lighting, 4K resolution, commercial quality",
        "limitaciones": "Lento (~1m 5s).",
    },
    "Seedream 4 4K": {
        "nota": 4.5, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 3000, "modos_gen": ["4K"],
        "best_for": "Seedream 4 4K. ~37s. Genera directamente en 4K nativo. Para impresión y trabajos de alta resolución.",
        "prompt_formula": "Lenguaje natural detallado. Aprovecha la alta resolución pidiendo detalles finos.",
        "prompt_ejemplo": "An intricate macro photograph of a butterfly wing showing fine scale patterns, ultra-detailed, 4K resolution",
        "limitaciones": "Sin negative.",
    },
    "Seedream 4": {
        "nota": 4.4, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 2500, "modos_gen": ["Standard"],
        "best_for": "Seedream 4. ~19s. Versión estándar, balance calidad/velocidad.",
        "prompt_formula": "Lenguaje natural fluido.",
        "prompt_ejemplo": "A serene Japanese garden with a koi pond, cherry blossoms falling, soft natural light",
        "limitaciones": "Reemplazado por Seedream 4.5 y 5 Lite.",
    },

    # ── Recraft ──────────────────────────────────────
    "Recraft V4 Pro": {
        "nota": 4.7, "has_negative": True, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "2:3", "3:2"],
        "max_chars": 3000, "modos_gen": ["Pro"],
        "best_for": "Recraft V4 Pro (Nuevo). ~35s. Soporta NEGATIVE PROMPT. Especialista en arte vectorial, ilustraciones, branding. Mejor que V3.",
        "prompt_formula": "Lenguaje natural + estilo vectorial. 'Flat illustration', 'vector art', 'icon style'.",
        "prompt_ejemplo": "Flat vector illustration of a cozy coffee shop at night, warm color palette, geometric shapes, minimalist design",
        "limitaciones": "No fotorrealismo. Mejor para gráfico/vectorial.",
    },
    "Recraft V4": {
        "nota": 4.5, "has_negative": True, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4"],
        "max_chars": 2500, "modos_gen": ["Standard"],
        "best_for": "Recraft V4 (Nuevo). ~18s. Soporta NEGATIVE PROMPT. Versión estándar para vectorial.",
        "prompt_formula": "Lenguaje natural + estilo vectorial.",
        "prompt_ejemplo": "Minimalist vector poster with geometric shapes, monochrome palette, clean lines",
        "limitaciones": "No fotorrealismo.",
    },

    # ── Otros Magnific ────────────────────────────────
    "Z-Image": {
        "nota": 4.4, "has_negative": False, "is_natural": False, "no_weights": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 1500, "modos_gen": ["Turbo"],
        "best_for": "Z-Image en Magnific. ⚡ ~8s. Modelo Turbo: tags limpios sin pesos ni negative. Latencia mínima.",
        "prompt_formula": "Tags limpios separados por comas SIN pesos numéricos.",
        "prompt_ejemplo": "close-up portrait, silver hair, blue eyes, detailed skin, soft studio lighting, 8K, masterpiece",
        "limitaciones": "Sin negative ni pesos. Para alta calidad usar Mystic/Flux.",
    },
    "Qwen": {
        "nota": 4.3, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 3000, "modos_gen": ["Standard"],
        "best_for": "Qwen Image en Magnific. ~12s. Buena calidad general, soporta referencias. De Alibaba/Aliyun.",
        "prompt_formula": "Lenguaje natural descriptivo.",
        "prompt_ejemplo": "A modern minimalist living room with large windows, natural light, scandinavian design",
        "limitaciones": "Sin negative.",
    },
    "Grok": {
        "nota": 4.2, "has_negative": False, "is_natural": True,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 3000, "modos_gen": ["Standard"],
        "best_for": "Grok Imagine en Magnific. ~11s. Modelo de xAI. Buena para arte conceptual y escenas creativas.",
        "prompt_formula": "Lenguaje natural creativo. Le va bien lo absurdo y la fantasía.",
        "prompt_ejemplo": "A surreal scene of giant mushrooms in a crystal forest, dreamy ethereal lighting, fantasy art style",
        "limitaciones": "Sin negative ni pesos.",
    },
    "Classic": {
        "nota": 4.0, "has_negative": True, "is_natural": False,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 2000, "modos_gen": ["Classic"],
        "best_for": "Modelo Classic de Magnific. ⚡ ~4s. Soporta NEGATIVE PROMPT. Tags estilo SD tradicional. Ideal cuando quieres control con negatives.",
        "prompt_formula": "Tags con pesos estilo Stable Diffusion. (tag:1.2). Soporta negative.",
        "prompt_ejemplo": "(beautiful portrait:1.3), 1girl, detailed face, soft lighting, professional photography, 8K",
        "limitaciones": "Calidad inferior a modelos modernos pero soporta negative.",
    },
    "Classic Fast": {
        "nota": 3.9, "has_negative": True, "is_natural": False,
        "ratios": ["1:1", "16:9", "9:16"],
        "max_chars": 1500, "modos_gen": ["Fast"],
        "best_for": "Classic Fast. ⚡ ~2s (más rápido). Soporta NEGATIVE PROMPT. Ideal para iteración rápida con tags + negative.",
        "prompt_formula": "Tags con pesos. Soporta negative.",
        "prompt_ejemplo": "(portrait:1.2), 1girl, detailed face, studio lighting, masterpiece",
        "limitaciones": "Calidad menor que Classic estándar.",
    },
}

# ══════════════════════════════════════════════════════════════════
# ESPECIFICACIONES DE MODELOS DE AUDIO
# ══════════════════════════════════════════════════════════════════
MODEL_SPECS_AUDIO = {
    "Suno v5": {
        "nota": 4.8,
        "has_negative": True,
        "has_lyrics": True,
        "has_instrumental_toggle": True,
        "usa_tags_estructurales": True,
        "duracion_max_min": 8,
        "max_chars_letra": 5000,
        "max_chars_estilo": 1000,
        "idiomas": ["inglés", "español", "francés", "italiano", "portugués", "alemán", "chino", "japonés", "coreano"],
        "best_for": "Expresividad vocal superior, modelo top actual. Ideal para releases.",
        "prompt_formula": "Estilo: géneros+mood. Letra: tags [Verse]/[Chorus] + letra",
        "prompt_ejemplo_estilo": "indie pop, dreamy vocals, 90s alternative, melancholic",
        "prompt_ejemplo_letra": "[Verse 1]\nCaminando por la calle vieja...",
        "limitaciones": "Requiere suscripción Pro/Premier para acceso temprano.",
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
        "best_for": "Mashups de géneros avanzados, vocales ricas, hasta 8 min.",
        "prompt_formula": "Estilo: géneros+mood. Letra: tags estructurales + letra.",
        "prompt_ejemplo_estilo": "midwest emo mixed with neosoul, warm vocals",
        "prompt_ejemplo_letra": "[Intro]\n(soft piano)...",
        "limitaciones": "Aún puede tener inconsistencias en letras largas.",
    },
    "Suno v4": {
        "nota": 4.3,
        "has_negative": False,
        "has_lyrics": True,
        "has_instrumental_toggle": True,
        "usa_tags_estructurales": True,
        "duracion_max_min": 4,
        "max_chars_letra": 3000,
        "max_chars_estilo": 200,
        "idiomas": ["inglés", "español", "francés", "italiano", "portugués", "alemán", "chino", "japonés", "coreano"],
        "best_for": "Audio limpio, estructura refinada, hasta 4 min.",
        "prompt_formula": "Estilo: géneros directos. Letra: tags + letra",
        "prompt_ejemplo_estilo": "acoustic folk, fingerpicking, soft male vocals",
        "prompt_ejemplo_letra": "[Verse]\n...",
        "limitaciones": "Máx 4 min. Menos expresividad vocal que v4.5+",
    },
    "Minimax Music 2.5": {
        "nota": 4.4,
        "has_negative": False,
        "has_lyrics": True,
        "has_instrumental_toggle": False,
        "usa_tags_estructurales": False,
        "duracion_max_min": 4,
        "max_chars_letra": 2000,
        "max_chars_estilo": 400,
        "idiomas": ["inglés", "español", "chino", "japonés", "coreano", "francés"],
        "generos": ["Pop", "R&B", "Rock", "Disco", "Electrónica", "Folk", "Hip-hop", "Blues", "Clásica", "Música de videojuegos"],
        "best_for": "Integrado en SeaArt. Filtros por género, emoción, voz.",
        "prompt_formula": "Letra: directa SIN tags. Estilo: género + mood.",
        "prompt_ejemplo_estilo": "Pop romántico, voz femenina aguda, tempo medio",
        "prompt_ejemplo_letra": "Letra directa en castellano...",
        "coste_energia": "135",
        "limitaciones": "No usa tags estructurales de Suno.",
    },
    "SeaArt MusicGo": {
        "nota": 4.2,
        "has_negative": False,
        "has_lyrics": True,
        "has_instrumental_toggle": True,
        "usa_tags_estructurales": False,
        "duracion_max_min": 3,
        "max_chars_letra": 1500,
        "max_chars_estilo": 300,
        "idiomas": ["inglés", "español", "chino", "japonés", "francés"],
        "generos": ["Pop", "R&B", "Rock", "Disco", "Electrónica", "Folk", "Hip-hop", "Blues", "Clásica", "Música de videojuegos"],
        "best_for": "Integrado en SeaArt. Toggle Vocal/Instrumental explícito. Económico.",
        "prompt_formula": "Toggle Vocal/Instrumental. Letra directa. Estilo: género + mood",
        "prompt_ejemplo_estilo": "Instrumental electrónico, synthwave relajado",
        "prompt_ejemplo_letra": "Letra directa sin tags",
        "coste_energia": "120",
        "limitaciones": "Menor variedad de géneros. Sin tags estructurales.",
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
        "modelos": ["NiwaStyle - Animax ColorPop", "NiwaStyle - Animax Plus", "NiwaStyle - Animax Chill"],
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

    v1.0.2: añadidos `chk_text`, `chk_bg`, `panel_bg`, `panel_text`,
    `accent_text` para garantizar contraste en modo light en checkboxes,
    scrollables y labels que viven dentro de tabs."""
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
            # v1.0.2 — colores explícitos consistentes con dark
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
# Muestras para nuevos usuarios — Lanzamiento v1.0.9
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
