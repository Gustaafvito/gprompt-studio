"""
AVATAR_CONFIG — Módulo de generación de datasets de avatares para LoRA
======================================================================
Módulo autocontenido para "Arquitecto de Prompts" (Nexus).
Define los ángulos canónicos, el formulario de rasgos, estilos y
negative prompts del modo Avatar.

NOTA PARA INTEGRACIÓN (Claude Code):
- Este diccionario puede fusionarse en config.py junto a MODEL_SPECS,
  o mantenerse como archivo aparte e importarse desde config.py.
"""

# ---------------------------------------------------------------------------
# ÁNGULOS CANÓNICOS PARA DATASET LoRA
# Cada ángulo define: etiqueta en español (UI), fragmento de prompt en inglés,
# encuadre (para la caption kohya) y nombre de archivo sugerido.
# ---------------------------------------------------------------------------
AVATAR_ANGLES = {
    # --- ROSTRO / RETRATO ---
    "face_front": {
        "label": "Rostro — frontal",
        "prompt": "close-up headshot, head and shoulders only, face fills the frame, cropped at the chest, lower body out of frame, front view, looking directly at camera",
        "framing": "close-up portrait",
        "filename": "01_face_front",
        "group": "rostro",
    },
    "face_34_left": {
        "label": "Rostro — 3/4 izquierda",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, lower body out of frame, head turned three-quarter view to the left",
        "framing": "close-up portrait, three-quarter left",
        "filename": "02_face_34_left",
        "group": "rostro",
    },
    "face_34_right": {
        "label": "Rostro — 3/4 derecha",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, lower body out of frame, head turned three-quarter view to the right",
        "framing": "close-up portrait, three-quarter right",
        "filename": "03_face_34_right",
        "group": "rostro",
    },
    "face_profile_left": {
        "label": "Rostro — perfil izquierdo",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, lower body out of frame, full left side profile, head facing left",
        "framing": "close-up portrait, left profile",
        "filename": "04_face_profile_left",
        "group": "rostro",
    },
    "face_profile_right": {
        "label": "Rostro — perfil derecho",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, lower body out of frame, full right side profile, head facing right",
        "framing": "close-up portrait, right profile",
        "filename": "05_face_profile_right",
        "group": "rostro",
    },

    # --- BUSTO / MEDIO CUERPO ---
    "bust_front": {
        "label": "Busto — frontal",
        "prompt": "upper body shot, head to chest, cropped at the waist, legs not visible, facing camera directly, front view",
        "framing": "upper body, front view",
        "filename": "06_bust_front",
        "group": "busto",
    },
    "bust_34_left": {
        "label": "Busto — 3/4 izquierda",
        "prompt": "upper body shot, head to chest, cropped at the waist, legs not visible, body turned three-quarter to the left",
        "framing": "upper body, three-quarter left",
        "filename": "07_bust_34_left",
        "group": "busto",
    },
    "bust_34_right": {
        "label": "Busto — 3/4 derecha",
        "prompt": "upper body shot, head to chest, cropped at the waist, legs not visible, body turned three-quarter to the right",
        "framing": "upper body, three-quarter right",
        "filename": "08_bust_34_right",
        "group": "busto",
    },

    # --- CUERPO ENTERO ---
    "full_front": {
        "label": "Cuerpo entero — frontal",
        "prompt": "full body shot, standing upright, facing camera directly, entire body visible from head to feet",
        "framing": "full body, front view",
        "filename": "09_full_front",
        "group": "cuerpo",
    },
    "full_34_left": {
        "label": "Cuerpo entero — 3/4 izquierda",
        "prompt": "full body shot, standing, body turned three-quarter to the left, entire body visible",
        "framing": "full body, three-quarter left",
        "filename": "10_full_34_left",
        "group": "cuerpo",
    },
    "full_34_right": {
        "label": "Cuerpo entero — 3/4 derecha",
        "prompt": "full body shot, standing, body turned three-quarter to the right, entire body visible",
        "framing": "full body, three-quarter right",
        "filename": "11_full_34_right",
        "group": "cuerpo",
    },
    "full_back": {
        "label": "Cuerpo entero — espalda",
        "prompt": "full body shot from behind, back view, entire body visible, head facing away from camera",
        "framing": "full body, back view",
        "filename": "12_full_back",
        "group": "cuerpo",
    },

    # --- ÁNGULOS DE CÁMARA Y EXPRESIONES ---
    "low_angle": {
        "label": "Contrapicado (low angle)",
        "prompt": "upper body shot from the waist up, low camera angle looking up at the subject, legs not visible",
        "framing": "upper body, low angle",
        "filename": "13_low_angle",
        "group": "extras",
    },
    "high_angle": {
        "label": "Picado (high angle)",
        "prompt": "upper body shot from the waist up, high camera angle looking down at the subject, legs not visible",
        "framing": "upper body, high angle",
        "filename": "14_high_angle",
        "group": "extras",
    },
    "expression_smile": {
        "label": "Expresión — sonrisa",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, front view, warm genuine smile, joyful expression",
        "framing": "close-up portrait, smiling",
        "filename": "15_expression_smile",
        "group": "extras",
    },
    "expression_serious": {
        "label": "Expresión — seria",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, front view, serious neutral expression, calm look",
        "framing": "close-up portrait, serious",
        "filename": "16_expression_serious",
        "group": "extras",
    },

    # --- EXPRESIONES ADICIONALES (rango emocional para el LoRA) ---
    # Neutrales: solo cambian la expresión, sin props ni escenario.
    "expression_surprised": {
        "label": "Expresión — sorpresa",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, front view, surprised expression, wide open eyes, slightly open mouth",
        "framing": "close-up portrait, surprised",
        "filename": "17_expression_surprised",
        "group": "extras",
    },
    "expression_angry": {
        "label": "Expresión — enfado",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, front view, angry determined expression, furrowed eyebrows",
        "framing": "close-up portrait, angry",
        "filename": "18_expression_angry",
        "group": "extras",
    },
    "expression_eyes_closed": {
        "label": "Expresión — ojos cerrados",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, front view, eyes closed, calm peaceful expression, gentle smile",
        "framing": "close-up portrait, eyes closed",
        "filename": "19_expression_eyes_closed",
        "group": "extras",
    },
    "expression_blush": {
        "label": "Expresión — sonrojo tímido",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, front view, shy blushing expression, looking slightly away",
        "framing": "close-up portrait, blushing",
        "filename": "20_expression_blush",
        "group": "extras",
    },

    # --- POSES ADICIONALES (sin props ni escenario: solo pose/encuadre) ---
    "cowboy_front": {
        "label": "Plano americano — frontal",
        "prompt": "cowboy shot, framed from mid-thigh up, standing, facing camera directly, front view",
        "framing": "cowboy shot, front view",
        "filename": "21_cowboy_front",
        "group": "poses",
    },
    "seated_floor": {
        "label": "Sentada en el suelo",
        "prompt": "full body shot, seated cross-legged on the ground, relaxed sitting pose, entire body visible",
        "framing": "full body, seated",
        "filename": "22_seated_floor",
        "group": "poses",
    },
    "over_shoulder": {
        "label": "Mirando por encima del hombro",
        "prompt": "upper body shot, three-quarter back view, head turned looking over the shoulder toward the camera, cropped at the waist",
        "framing": "upper body, over the shoulder",
        "filename": "23_over_shoulder",
        "group": "poses",
    },
    "dynamic_action": {
        "label": "Pose dinámica / acción",
        "prompt": "full body shot, dynamic action pose, mid-movement, energetic stance, entire body visible",
        "framing": "full body, action pose",
        "filename": "24_dynamic_action",
        "group": "poses",
    },

    # --- EXPRESIONES Y POSES EXTRA (ampliación a 30, sin props ni escenario) ---
    "expression_laugh": {
        "label": "Expresión — risa abierta",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, front view, laughing out loud, open mouth, eyes crinkled with joy",
        "framing": "close-up portrait, laughing",
        "filename": "25_expression_laugh",
        "group": "extras",
    },
    "expression_thoughtful": {
        "label": "Expresión — pensativa",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, front view, thoughtful pensive expression, looking slightly upward",
        "framing": "close-up portrait, thoughtful",
        "filename": "26_expression_thoughtful",
        "group": "extras",
    },
    "pose_arms_crossed": {
        "label": "Pose — brazos cruzados",
        "prompt": "upper body shot, head to waist, standing with arms crossed over the chest, confident stance, front view, neutral background",
        "framing": "upper body, arms crossed",
        "filename": "27_pose_arms_crossed",
        "group": "poses",
    },
    "pose_hands_hips": {
        "label": "Pose — manos en la cadera",
        "prompt": "full body shot, standing with both hands on hips, confident posture, entire body visible, neutral background",
        "framing": "full body, hands on hips",
        "filename": "28_pose_hands_hips",
        "group": "poses",
    },
    "pose_walking": {
        "label": "Pose — caminando",
        "prompt": "full body shot, walking stride mid-step, natural movement, entire body visible from head to feet, neutral background",
        "framing": "full body, walking",
        "filename": "29_pose_walking",
        "group": "poses",
    },
    "pose_hands_pockets": {
        "label": "Pose — manos en los bolsillos",
        "prompt": "cowboy shot, framed from mid-thigh up, standing relaxed with hands in pockets, casual stance, front view",
        "framing": "cowboy shot, hands in pockets",
        "filename": "30_pose_hands_pockets",
        "group": "poses",
    },
}

# Set por defecto recomendado para un LoRA de personaje (30 vistas)
DEFAULT_ANGLE_SET = list(AVATAR_ANGLES.keys())

# Selección EQUILIBRADA (botón "⚖ Equilibrado"): para personaje la guía SeaArt
# pide ~60% planos de control (rostro/busto/cuerpo neutros, para memorizar ropa
# y rasgos) y limitar expresiones extremas a 4-5. "Todos los 30" hace lo
# contrario (sobran expresiones/poses), así que aquí curamos: 12 control + 4
# expresiones + 4 poses + 2 ángulos de cámara = 22 (control = 55%).
AVATAR_BALANCED_ANGLE_SET = [
    # Control (12): rostro, busto y cuerpo entero, todas las orientaciones
    "face_front", "face_34_left", "face_34_right",
    "face_profile_left", "face_profile_right",
    "bust_front", "bust_34_left", "bust_34_right",
    "full_front", "full_34_left", "full_34_right", "full_back",
    # Expresiones (4, limitadas para que no se vuelvan rasgos permanentes)
    "expression_smile", "expression_serious",
    "expression_surprised", "expression_eyes_closed",
    # Poses (4) y ángulos de cámara (2)
    "cowboy_front", "seated_floor", "over_shoulder", "dynamic_action",
    "low_angle", "high_angle",
]

# Grupos para organizar los checkboxes en la UI
ANGLE_GROUPS = {
    "rostro": "Rostro / Retrato",
    "busto": "Busto / Medio cuerpo",
    "cuerpo": "Cuerpo entero",
    "extras": "Ángulos y expresiones",
    "poses": "Poses adicionales",
}

# ---------------------------------------------------------------------------
# FORMULARIO DE RASGOS DEL AVATAR
# type: "entry" (texto libre) | "option" (desplegable)
# ---------------------------------------------------------------------------
AVATAR_FORM_FIELDS = [
    {"key": "genero", "label": "Género", "type": "option",
     "options": ["Mujer", "Hombre", "Andrógino", "Otro (describir en rasgos)"]},
    {"key": "edad", "label": "Edad aparente", "type": "option",
     "options": ["18-25", "25-35", "35-45", "45-60", "60+"]},
    {"key": "etnia_piel", "label": "Tono de piel / etnia", "type": "entry",
     "placeholder": "ej: piel clara mediterránea, piel morena..."},
    {"key": "pelo", "label": "Pelo (color, largo, estilo)", "type": "entry",
     "placeholder": "ej: melena castaña ondulada hasta los hombros"},
    {"key": "ojos", "label": "Ojos (color, forma)", "type": "entry",
     "placeholder": "ej: ojos verdes grandes y almendrados"},
    {"key": "rasgos", "label": "Rasgos distintivos", "type": "entry",
     "placeholder": "ej: pecas, cicatriz en ceja, hoyuelos, gafas..."},
    {"key": "complexion", "label": "Complexión", "type": "option",
     "options": ["Delgada", "Atlética", "Media", "Robusta", "Curvy"]},
    {"key": "ropa", "label": "Ropa (idéntica en todo el dataset)", "type": "entry",
     "placeholder": "ej: camiseta blanca lisa y vaqueros azules"},
]

# ---------------------------------------------------------------------------
# ESTILOS VISUALES DEL AVATAR
# El sufijo se añade al final de cada prompt del dataset.
# ---------------------------------------------------------------------------
AVATAR_STYLES = {
    "Fotorrealista": "photorealistic, professional studio photography, sharp focus, detailed skin texture, 85mm lens",
    "Anime": "anime style, clean lineart, cel shading, high quality anime illustration",
    "Render 3D": "3D render, octane render, subsurface scattering, high poly character model",
    "Ilustración digital": "digital illustration, painterly style, detailed character art",
    "Cómic occidental": "western comic book style, bold ink lines, flat colors",
    "Pixar / Cartoon 3D": "3D cartoon style, stylized character, soft lighting, animation movie quality",
}

# ---------------------------------------------------------------------------
# FONDOS (consistencia crítica para LoRA)
# ---------------------------------------------------------------------------
AVATAR_BACKGROUNDS = {
    "Gris neutro (recomendado LoRA)": "plain solid light gray background, seamless studio backdrop",
    "Blanco": "plain solid white background, seamless studio backdrop",
    "Negro": "plain solid black background, seamless studio backdrop",
    "Verde croma": "solid chroma key green background",
}

# Set de fondos NEUTROS para ROTAR a lo largo del dataset.
# La guía oficial SeaArt pide variar el fondo (máx. 3-6 imágenes por fondo)
# para que el LoRA no lo absorba y lo "pegue" siempre al personaje. Estos son
# todos claros/neutros de estudio: dan variación de píxeles sin enseñar una
# "escena" al LoRA. Se evita el negro puro a propósito, para no fundir pelo o
# ropa oscuros con el fondo. El ensamblado los reparte por índice (i % n), lo
# que además DECORRELACIONA el fondo de la pose (el LoRA no aprende
# "frontal = gris").
AVATAR_BACKGROUNDS_ROTACION = [
    "plain solid light gray background, seamless studio backdrop",
    "plain solid off-white background, seamless studio backdrop",
    "soft neutral gray gradient background, seamless studio backdrop",
    "plain solid light blue-gray background, seamless studio backdrop",
]

# ---------------------------------------------------------------------------
# NEGATIVE PROMPT FIJO DEL DATASET
# Se repite idéntico en todas las imágenes.
# ---------------------------------------------------------------------------
AVATAR_NEGATIVE_PROMPT = (
    "multiple people, two persons, deformed face, asymmetric eyes, extra fingers, "
    "extra limbs, missing limbs, bad anatomy, bad hands, blurry, lowres, jpeg artifacts, "
    "watermark, text, logo, signature, cropped head, out of frame, different clothing, "
    "different hairstyle, inconsistent face, busy background, cluttered background"
)

# Términos extra de negative para FORZAR el recorte en modelos que tienden a
# alejarse (Z-Image-Base, etc.): aunque el positivo pida "close-up", la ropa de
# cuerpo (falda, botas) en la descripción hace que el modelo se aleje. Meter el
# cuerpo en el negative es el lever que de verdad fuerza el encuadre.
AVATAR_NEGATIVE_CROP_CARA = (
    "full body, full-length shot, wide shot, long shot, distant shot, "
    "legs, thighs, knees, feet, shoes, boots, skirt, pants, lower body"
)
AVATAR_NEGATIVE_CROP_BUSTO = (
    "full body, full-length shot, wide shot, long shot, "
    "legs, thighs, knees, feet, shoes, boots, lower body"
)

# Simétrico al anterior, pero en la dirección contraria: para las tomas de
# CUERPO ENTERO (full, cowboy, sentada, acción). Muchos modelos de personaje
# tienden a hacer zoom a la cara/busto aunque el positivo pida "full body";
# meter el primer plano en el negative los empuja a ALEJARSE y mostrar el
# cuerpo. No se usa en cara/busto (ahí sí queremos el zoom).
AVATAR_NEGATIVE_ANTIZOOM_CUERPO = (
    "close-up, close-up portrait, headshot, head and shoulders, bust shot, "
    "portrait, face fills the frame, cropped at the chest, cropped at the waist, "
    "zoomed in, upper body only"
)

# Negative EXTRA solo para el MODO EDICIÓN (img2img) en tomas de ángulo.
# Los modelos de sujeto/referencia se anclan a la pose frontal de la imagen de
# referencia e ignoran la rotación pedida en el positivo. Meter el frontal en el
# negative es el lever que de verdad empuja al modelo a girar la cabeza. NO se
# usa en txt2img (ahí el frontal ya se respeta sin problema).
AVATAR_NEGATIVE_EDIT_ROTACION = (
    "front view, frontal view, facing camera directly, "
    "same frontal pose as the reference, no rotation, straight-on angle"
)

# Iluminación fija para coherencia entre tomas
AVATAR_LIGHTING = "soft even studio lighting, no harsh shadows, neutral color temperature"


# ===========================================================================
# TIPO: PAISAJE
# ===========================================================================
LANDSCAPE_ANGLES = {
    "ls_panoramic": {
        "label": "Vista panorámica (gran angular)",
        "prompt": "ultra-wide panoramic landscape shot, sweeping vista, horizon line, expansive scene, no people",
        "framing": "panoramic landscape",
        "filename": "01_panoramic",
        "group": "composicion",
    },
    "ls_aerial": {
        "label": "Vista aérea / desde arriba",
        "prompt": "aerial overhead view, bird's eye perspective, looking straight down or at high angle, vast terrain visible, no people",
        "framing": "aerial view",
        "filename": "02_aerial",
        "group": "composicion",
    },
    "ls_ground_level": {
        "label": "A ras del suelo (worm's eye)",
        "prompt": "ground level shot, low camera angle, foreground detail prominent, sky filling upper frame, no people",
        "framing": "ground level, low angle",
        "filename": "03_ground_level",
        "group": "composicion",
        "ratio": "3:2",  # paisaje horizontal pese al "detail" del prompt
    },
    "ls_midground": {
        "label": "Plano medio (sujeto + entorno)",
        "prompt": "medium distance landscape shot, foreground and background in balance, clear subject and context, no people",
        "framing": "medium distance landscape",
        "filename": "04_midground",
        "group": "composicion",
    },
    "ls_closeup_texture": {
        "label": "Primer plano — textura / detalle",
        "prompt": "extreme close-up macro detail shot, surface texture, intricate natural pattern, shallow depth of field, no people",
        "framing": "close-up macro detail",
        "filename": "05_closeup_texture",
        "group": "detalle",
    },
    "ls_detail_element": {
        "label": "Detalle de elemento natural",
        "prompt": "close-up detail of characteristic landscape element, sharp focus on subject, blurred background, no people",
        "framing": "close-up detail element",
        "filename": "06_detail_element",
        "group": "detalle",
    },
    "ls_dawn": {
        "label": "Amanecer / primera luz",
        "prompt": "dawn scene, first light of day, soft golden pink horizon, long shadows, mist in valleys, no people",
        "framing": "dawn, golden hour light",
        "filename": "07_dawn",
        "group": "luz",
    },
    "ls_golden_hour": {
        "label": "Hora dorada (atardecer)",
        "prompt": "golden hour sunset landscape, warm orange amber light, long shadows, dramatic sky colors, no people",
        "framing": "golden hour, sunset",
        "filename": "08_golden_hour",
        "group": "luz",
    },
    "ls_midday": {
        "label": "Luz de mediodía",
        "prompt": "midday bright sunlight landscape, harsh directional light, saturated colors, strong shadows, no people",
        "framing": "midday sunlight",
        "filename": "09_midday",
        "group": "luz",
    },
    "ls_night": {
        "label": "Escena nocturna / luna",
        "prompt": "nighttime landscape, moonlit scene, stars visible, deep blue and silver tones, long exposure look, no people",
        "framing": "night, moonlight",
        "filename": "10_night",
        "group": "luz",
    },
    "ls_fog": {
        "label": "Niebla / bruma",
        "prompt": "misty foggy landscape, soft diffused light, layers of atmospheric haze, ethereal mood, no people",
        "framing": "foggy, misty atmosphere",
        "filename": "11_fog",
        "group": "clima",
    },
    "ls_rain": {
        "label": "Lluvia / tormenta",
        "prompt": "rainy stormy landscape, wet surfaces reflecting light, dramatic storm clouds, moody dark atmosphere, no people",
        "framing": "rain, storm",
        "filename": "12_rain",
        "group": "clima",
    },
    "ls_snow": {
        "label": "Nieve / invierno",
        "prompt": "winter snowy landscape, white snow covering ground and trees, cold blue-white tones, no people",
        "framing": "snow, winter",
        "filename": "13_snow",
        "group": "clima",
    },
    "ls_long_exposure": {
        "label": "Larga exposición (agua / nubes)",
        "prompt": "long exposure photograph effect, silky smooth water or streaking clouds, motion blur, no people",
        "framing": "long exposure effect",
        "filename": "14_long_exposure",
        "group": "tecnica",
        "ratio": "3:2",  # técnica de paisaje (agua/nubes) → horizontal
    },
    "ls_reflection": {
        "label": "Reflejo en agua",
        "prompt": "mirror reflection in calm water surface, perfect symmetry, landscape reflected below, no people",
        "framing": "water reflection, symmetry",
        "filename": "15_reflection",
        "group": "tecnica",
    },

    # --- AMPLIACIÓN A 30 ---
    "ls_leading_lines": {
        "label": "Líneas de fuga (camino / río)",
        "prompt": "landscape with strong leading lines, a path road or river guiding the eye toward the horizon, sense of depth, no people",
        "framing": "leading lines composition",
        "filename": "16_leading_lines",
        "group": "composicion",
    },
    "ls_natural_frame": {
        "label": "Encuadre natural (marco)",
        "prompt": "landscape framed by natural elements, arch of branches or rock opening surrounding the scene, layered foreground, no people",
        "framing": "natural frame composition",
        "filename": "17_natural_frame",
        "group": "composicion",
    },
    "ls_minimalist": {
        "label": "Minimalista (espacio negativo)",
        "prompt": "minimalist landscape, vast negative space, single subject isolated, simple clean composition, calm mood, no people",
        "framing": "minimalist, negative space",
        "filename": "18_minimalist",
        "group": "composicion",
    },
    "ls_layered_depth": {
        "label": "Capas de profundidad",
        "prompt": "landscape with layered depth, distinct foreground midground and background planes fading into distance, atmospheric perspective, no people",
        "framing": "layered depth planes",
        "filename": "19_layered_depth",
        "group": "composicion",
    },
    "ls_flora_detail": {
        "label": "Detalle de flora",
        "prompt": "close-up of characteristic plants or flowers, sharp botanical detail, soft natural light, blurred background, no people",
        "framing": "flora close-up detail",
        "filename": "20_flora_detail",
        "group": "detalle",
    },
    "ls_geology": {
        "label": "Textura geológica (roca)",
        "prompt": "close-up of rock formation and geological texture, layered stone, weathered surface detail, natural light, no people",
        "framing": "geological rock texture",
        "filename": "21_geology",
        "group": "detalle",
    },
    "ls_water_detail": {
        "label": "Detalle de agua (ondas)",
        "prompt": "close-up of water surface detail, ripples and reflections, droplets, shallow depth of field, no people",
        "framing": "water surface detail",
        "filename": "22_water_detail",
        "group": "detalle",
    },
    "ls_blue_hour": {
        "label": "Hora azul / crepúsculo",
        "prompt": "blue hour twilight landscape, deep blue and violet tones, soft fading light after sunset, calm atmosphere, no people",
        "framing": "blue hour, twilight",
        "filename": "23_blue_hour",
        "group": "luz",
    },
    "ls_backlit": {
        "label": "A contraluz / destello solar",
        "prompt": "backlit landscape with the sun behind the scene, lens flare, glowing rim light on edges, silhouetted shapes, no people",
        "framing": "backlit, sun flare",
        "filename": "24_backlit",
        "group": "luz",
    },
    "ls_overcast": {
        "label": "Cielo cubierto (luz difusa)",
        "prompt": "overcast landscape, soft diffused even light, muted colors, gentle flat lighting, calm subdued mood, no people",
        "framing": "overcast, diffused light",
        "filename": "25_overcast",
        "group": "luz",
    },
    "ls_windy": {
        "label": "Viento (movimiento)",
        "prompt": "windy landscape, grass and trees bending in the wind, sense of motion, dynamic moving clouds, no people",
        "framing": "windy, motion in foliage",
        "filename": "26_windy",
        "group": "clima",
    },
    "ls_after_rain": {
        "label": "Después de la lluvia",
        "prompt": "landscape just after rain, wet reflective surfaces, fresh saturated colors, puddles, clearing sky, no people",
        "framing": "after rain, wet reflective",
        "filename": "27_after_rain",
        "group": "clima",
    },
    "ls_heat_haze": {
        "label": "Calima / aire seco",
        "prompt": "arid landscape with heat haze shimmering on the horizon, dry cracked ground, intense warm light, no people",
        "framing": "heat haze, arid",
        "filename": "28_heat_haze",
        "group": "clima",
    },
    "ls_silhouette": {
        "label": "Silueta a contraluz",
        "prompt": "landscape silhouette at sunset, dark shapes against a glowing colorful sky, high contrast, no people",
        "framing": "silhouette against sky",
        "filename": "29_silhouette",
        "group": "tecnica",
    },
    "ls_tilt_shift": {
        "label": "Tilt-shift (miniatura)",
        "prompt": "tilt-shift miniature effect landscape, selective focus band, blurred top and bottom, toy-like miniature look, no people",
        "framing": "tilt-shift, miniature effect",
        "filename": "30_tilt_shift",
        "group": "tecnica",
    },
}

LANDSCAPE_ANGLE_GROUPS = {
    "composicion": "Composición / Encuadre",
    "detalle": "Detalle y Textura",
    "luz": "Luz y Hora del día",
    "clima": "Clima y Atmósfera",
    "tecnica": "Técnicas especiales",
}

LANDSCAPE_DEFAULT_ANGLE_SET = list(LANDSCAPE_ANGLES.keys())
# Paisaje: la variedad de condiciones (luz/clima/encuadre) ES el objetivo,
# así que el set equilibrado = el completo.
LANDSCAPE_BALANCED_ANGLE_SET = list(LANDSCAPE_ANGLES.keys())

LANDSCAPE_FORM_FIELDS = [
    {"key": "tipo_paisaje", "label": "Tipo de paisaje", "type": "option",
     "options": ["Montaña", "Bosque", "Playa / Costa", "Desierto", "Pradera",
                 "Ciudad / Urbano", "Lago / Río", "Valle", "Volcán", "Tundra / Ártico"]},
    {"key": "pais_region", "label": "País / Región (opcional)", "type": "entry",
     "placeholder": "ej: Patagonia, Islandia, Toscana..."},
    {"key": "epoca", "label": "Estación del año", "type": "option",
     "options": ["Primavera", "Verano", "Otoño", "Invierno"]},
    {"key": "elementos", "label": "Elementos característicos", "type": "entry",
     "placeholder": "ej: pinos nevados, cascada, peñascos, molinos de viento..."},
    {"key": "paleta", "label": "Paleta de colores dominante", "type": "entry",
     "placeholder": "ej: verdes exuberantes, tonos áridos ocre y naranja..."},
    {"key": "estilo_foto", "label": "Estilo fotográfico", "type": "option",
     "options": ["Fotografía naturaleza (National Geographic)",
                 "Fotografía de viaje (editorial)",
                 "Pintura al óleo",
                 "Acuarela",
                 "Arte digital / fantástico"]},
]

LANDSCAPE_STYLES = {
    "Fotografía realista": "professional nature photography, ultra sharp, RAW photo quality, 16mm lens",
    "Anime": "anime background art, clean lineart, cel shading, vibrant colors, anime scenery, Makoto Shinkai style",
    "Cinematográfico": "cinematic landscape, anamorphic lens, film grain, color graded",
    "Pintura al óleo": "oil painting style, visible brushstrokes, rich texture, traditional art",
    "Acuarela": "watercolor painting, soft washes, translucent layers, paper texture",
    "Arte digital": "digital art, concept art landscape, detailed matte painting",
}

LANDSCAPE_NEGATIVE_PROMPT = (
    "people, person, human, man, woman, child, character, portrait, face, hands, "
    "text, watermark, logo, signature, blurry, lowres, jpeg artifacts, overexposed, "
    "underexposed, oversaturated, cartoon, anime, 3d render, ugly"
)


# ===========================================================================
# TIPO: OBJETO / PRODUCTO
# ===========================================================================
OBJECT_ANGLES = {
    "obj_front": {
        "label": "Frontal (vista principal)",
        "prompt": "front view product shot, object centered, facing camera directly, clean background, studio lighting",
        "framing": "front view, centered",
        "filename": "01_front",
        "group": "vistas",
    },
    "obj_side_left": {
        "label": "Lateral izquierdo",
        "prompt": "left side view product shot, object in full profile, clean background, studio lighting",
        "framing": "left side profile",
        "filename": "02_side_left",
        "group": "vistas",
    },
    "obj_side_right": {
        "label": "Lateral derecho",
        "prompt": "right side view product shot, object in full profile, clean background, studio lighting",
        "framing": "right side profile",
        "filename": "03_side_right",
        "group": "vistas",
    },
    "obj_34_left": {
        "label": "3/4 izquierda",
        "prompt": "three-quarter left angle product shot, dynamic perspective showing front and left side, clean background",
        "framing": "three-quarter left angle",
        "filename": "04_34_left",
        "group": "vistas",
    },
    "obj_34_right": {
        "label": "3/4 derecha",
        "prompt": "three-quarter right angle product shot, dynamic perspective showing front and right side, clean background",
        "framing": "three-quarter right angle",
        "filename": "05_34_right",
        "group": "vistas",
    },
    "obj_top": {
        "label": "Vista superior (flat lay)",
        "prompt": "top-down flat lay shot, overhead view, object laid on flat surface, centered, even lighting",
        "framing": "top view, flat lay",
        "filename": "06_top",
        "group": "vistas",
        "warn": "Vista cenital agresiva — recomendado máx. 1-2 en el dataset.",
    },
    "obj_back": {
        "label": "Vista posterior",
        "prompt": "back view product shot, rear of object fully visible, clean background, studio lighting",
        "framing": "back view",
        "filename": "07_back",
        "group": "vistas",
    },
    "obj_detail_texture": {
        "label": "Detalle de textura / material",
        "prompt": "extreme close-up macro shot of surface texture and material detail, shallow depth of field, sharp focus",
        "framing": "macro detail, texture",
        "filename": "08_detail_texture",
        "group": "detalle",
    },
    "obj_detail_feature": {
        "label": "Detalle de característica clave",
        "prompt": "close-up detail shot highlighting distinctive feature or key element, sharp focus, blurred background",
        "framing": "close-up feature detail",
        "filename": "09_detail_feature",
        "group": "detalle",
    },
    "obj_in_context": {
        "label": "En contexto / en uso",
        "prompt": "lifestyle contextual shot, object shown in its natural use environment, realistic scene, no people",
        "framing": "in context, lifestyle",
        "filename": "10_in_context",
        "group": "contexto",
    },
    "obj_scale": {
        "label": "Con referencia de escala",
        "prompt": "product shot with scale reference, object next to familiar size reference, clean studio setting",
        "framing": "with scale reference",
        "filename": "11_scale",
        "group": "contexto",
    },
    "obj_shadow": {
        "label": "Con sombra proyectada",
        "prompt": "product shot with dramatic cast shadow, directional studio light, shadow adds depth and dimension",
        "framing": "dramatic shadow",
        "filename": "12_shadow",
        "group": "contexto",
    },

    # --- AMPLIACIÓN A 30 ---
    "obj_bottom": {
        "label": "Vista inferior",
        "prompt": "bottom view product shot, underside of the object visible, clean background, studio lighting",
        "framing": "bottom view",
        "filename": "13_bottom",
        "group": "vistas",
        "warn": "Vista poco habitual y agresiva — recomendado máx. 1-2 en el dataset.",
    },
    "obj_elevated_45": {
        "label": "Picado 45° (elevado)",
        "prompt": "elevated 45 degree angle product shot, looking down at the object, top and front visible, clean background",
        "framing": "elevated 45 degree angle",
        "filename": "14_elevated_45",
        "group": "vistas",
    },
    "obj_isometric": {
        "label": "Perspectiva isométrica",
        "prompt": "isometric perspective product shot, object at equal angles, technical clean look, even lighting, clean background",
        "framing": "isometric perspective",
        "filename": "15_isometric",
        "group": "vistas",
        "warn": "Perspectiva muy marcada — recomendado máx. 1-2 en el dataset.",
    },
    "obj_hero_low": {
        "label": "Contrapicado heroico",
        "prompt": "low hero angle product shot, camera looking up at the object, imposing dramatic perspective, clean background",
        "framing": "low hero angle",
        "filename": "16_hero_low",
        "group": "vistas",
        "warn": "Contrapicado dramático — recomendado máx. 1-2 en el dataset.",
    },
    "obj_open_state": {
        "label": "Abierto / estado interior",
        "prompt": "product shot of the object in its open state, interior or moving parts revealed, clean background, studio lighting",
        "framing": "open state, interior",
        "filename": "17_open_state",
        "group": "vistas",
    },
    "obj_fill_frame": {
        "label": "Encuadre completo (full frame)",
        "prompt": "tightly cropped product shot, object filling the entire frame, bold close composition, studio lighting",
        "framing": "full frame, tight crop",
        "filename": "18_fill_frame",
        "group": "vistas",
    },
    "obj_logo_detail": {
        "label": "Detalle de logo / marca",
        "prompt": "extreme close-up macro of the branding or logo on the object, sharp focus, shallow depth of field",
        "framing": "logo branding macro",
        "filename": "19_logo_detail",
        "group": "detalle",
    },
    "obj_edge_seam": {
        "label": "Detalle de borde / unión",
        "prompt": "close-up detail of edges seams and joints of the object, construction quality visible, sharp focus",
        "framing": "edge and seam detail",
        "filename": "20_edge_seam",
        "group": "detalle",
    },
    "obj_gloss": {
        "label": "Brillo / reflejo del material",
        "prompt": "close-up showing material gloss and reflections, specular highlights on the surface, controlled studio light",
        "framing": "material gloss, reflection",
        "filename": "21_gloss",
        "group": "detalle",
    },
    "obj_functional_part": {
        "label": "Detalle de parte funcional",
        "prompt": "close-up detail of a functional part of the object, button connector or mechanism, sharp focus, blurred background",
        "framing": "functional part detail",
        "filename": "22_functional_part",
        "group": "detalle",
    },
    "obj_rustic_surface": {
        "label": "Sobre superficie natural",
        "prompt": "product shot on a rustic natural surface, wood or stone texture beneath, warm contextual lighting, no people",
        "framing": "on natural surface",
        "filename": "23_rustic_surface",
        "group": "contexto",
    },
    "obj_with_props": {
        "label": "Con props complementarios",
        "prompt": "styled product shot surrounded by complementary props that hint at its use, balanced composition, no people",
        "framing": "styled with props",
        "filename": "24_with_props",
        "group": "contexto",
    },
    "obj_dark_backdrop": {
        "label": "Fondo oscuro dramático",
        "prompt": "product shot on a dark dramatic backdrop, single directional light, moody high-contrast mood, no people",
        "framing": "dark dramatic backdrop",
        "filename": "25_dark_backdrop",
        "group": "contexto",
    },
    "obj_white_seamless": {
        "label": "Fondo blanco infinito",
        "prompt": "product shot on a pure white seamless background, bright even commercial lighting, no shadows, no people",
        "framing": "white seamless studio",
        "filename": "26_white_seamless",
        "group": "contexto",
    },
    "obj_outdoor": {
        "label": "Exterior / lifestyle",
        "prompt": "product shot in an outdoor lifestyle setting, natural daylight, realistic environment context, no people",
        "framing": "outdoor lifestyle",
        "filename": "27_outdoor",
        "group": "contexto",
    },
    "obj_floating": {
        "label": "Flotando / levitando",
        "prompt": "product shot of the object floating in mid air, levitation effect, soft shadow below, clean background",
        "framing": "floating levitation",
        "filename": "28_floating",
        "group": "contexto",
    },
    "obj_backlit": {
        "label": "A contraluz (rim light)",
        "prompt": "backlit product shot, rim light outlining the object edges, glowing silhouette, dark background, no people",
        "framing": "backlit, rim light",
        "filename": "29_backlit",
        "group": "contexto",
    },
    "obj_collection": {
        "label": "Colección / varias unidades",
        "prompt": "product shot with several identical units arranged together, repetition composition, clean background, even lighting",
        "framing": "collection, arranged units",
        "filename": "30_collection",
        "group": "contexto",
    },
}

OBJECT_ANGLE_GROUPS = {
    "vistas": "Vistas principales",
    "detalle": "Detalles y Texturas",
    "contexto": "Contexto y Ambiente",
}

OBJECT_DEFAULT_ANGLE_SET = list(OBJECT_ANGLES.keys())
# Objeto: el set equilibrado excluye las vistas más agresivas (inferior,
# isométrica, contrapicado heroico) que sesgan el dataset si se abusa de ellas
# (máx. 1-2 recomendado). Deja la flat-lay y el picado 45º como cenitales suaves.
_OBJECT_VISTAS_AGRESIVAS = {"obj_bottom", "obj_isometric", "obj_hero_low"}
OBJECT_BALANCED_ANGLE_SET = [
    k for k in OBJECT_ANGLES if k not in _OBJECT_VISTAS_AGRESIVAS
]

OBJECT_FORM_FIELDS = [
    {"key": "nombre_objeto", "label": "Nombre del objeto / producto", "type": "entry",
     "placeholder": "ej: reloj de bolsillo de bronce, botella de perfume..."},
    {"key": "categoria", "label": "Categoría", "type": "option",
     "options": ["Joyería / Accesorio", "Electrónica / Gadget", "Moda / Ropa",
                 "Alimento / Bebida", "Mueble / Decoración", "Herramienta",
                 "Juguete / Coleccionable", "Vehículo / Transporte", "Otro"]},
    {"key": "materiales", "label": "Materiales principales", "type": "entry",
     "placeholder": "ej: cuero marrón, metal dorado mate, madera de nogal..."},
    {"key": "colores", "label": "Colores exactos", "type": "entry",
     "placeholder": "ej: negro brillante con detalles en cobre..."},
    {"key": "forma", "label": "Forma / silueta", "type": "entry",
     "placeholder": "ej: cilíndrico, rectangular, con asas curvas..."},
    {"key": "rasgos_distintos", "label": "Elementos o rasgos distintivos", "type": "entry",
     "placeholder": "ej: grabado floral, pantalla OLED, tapa con bisagra..."},
]

OBJECT_STYLES = {
    "Fotografía de producto": "professional product photography, studio lighting, clean white background, commercial quality",
    "Anime": "anime style object, clean lineart, cel shading, vibrant colors, anime illustration",
    "Editorial / Lifestyle": "editorial lifestyle product shot, atmospheric lighting, contextual background, magazine quality",
    "Render 3D": "3D product render, photorealistic rendering, perfect lighting, no imperfections",
    "Artístico / Dramático": "artistic dramatic product shot, moody lighting, artistic composition, fine art photography",
}

OBJECT_NEGATIVE_PROMPT = (
    "people, person, human, hands, face, blurry, lowres, jpeg artifacts, "
    "watermark, text, logo, signature, multiple objects of same type, "
    "distorted shape, wrong proportions, bad lighting, overexposed"
)


# ===========================================================================
# TIPO: ESTILO ARTÍSTICO
# ===========================================================================
STYLE_ANGLES = {
    "sty_portrait_f": {
        "label": "Retrato — mujer",
        "prompt": "portrait of a woman, head and shoulders, front view, neutral expression, studio setting",
        "framing": "portrait, woman",
        "filename": "01_portrait_woman",
        "group": "sujetos",
    },
    "sty_portrait_m": {
        "label": "Retrato — hombre",
        "prompt": "portrait of a man, head and shoulders, front view, neutral expression, studio setting",
        "framing": "portrait, man",
        "filename": "02_portrait_man",
        "group": "sujetos",
    },
    "sty_landscape": {
        "label": "Paisaje natural",
        "prompt": "natural landscape scene, mountains or forest or beach, daytime, no people",
        "framing": "landscape scene",
        "filename": "03_landscape",
        "group": "sujetos",
    },
    "sty_urban": {
        "label": "Escena urbana",
        "prompt": "urban city street scene, buildings and architecture, daytime, few people in distance",
        "framing": "urban scene",
        "filename": "04_urban",
        "group": "sujetos",
    },
    "sty_still_life": {
        "label": "Bodegón / Still life",
        "prompt": "still life composition, everyday objects arranged on a surface, dramatic side lighting",
        "framing": "still life",
        "filename": "05_still_life",
        "group": "sujetos",
    },
    "sty_animal": {
        "label": "Animal",
        "prompt": "an animal in its natural habitat or neutral setting, full body visible, sharp focus",
        "framing": "animal subject",
        "filename": "06_animal",
        "group": "sujetos",
        "ratio": "3:2",  # animal a cuerpo entero → horizontal, no 9:16
    },
    "sty_architecture": {
        "label": "Arquitectura",
        "prompt": "architectural exterior or interior, building structure, geometric lines, no people",
        "framing": "architecture",
        "filename": "07_architecture",
        "group": "sujetos",
    },
    "sty_fullbody": {
        "label": "Figura humana — cuerpo entero",
        "prompt": "full body standing figure, person visible from head to feet, neutral background",
        "framing": "full body figure",
        "filename": "08_full_body",
        "group": "sujetos",
    },
    "sty_abstract": {
        "label": "Composición abstracta",
        "prompt": "abstract composition, shapes and colors, no recognizable objects or people, pure artistic expression",
        "framing": "abstract composition",
        "filename": "09_abstract",
        "group": "variedad",
    },
    "sty_action": {
        "label": "Escena de acción / movimiento",
        "prompt": "dynamic action scene, movement and energy, dramatic composition, figures in motion",
        "framing": "action scene",
        "filename": "10_action",
        "group": "variedad",
    },

    # --- AMPLIACIÓN A 30 (más sujetos = el LoRA aprende el ESTILO, no el contenido) ---
    "sty_portrait_child": {
        "label": "Retrato — niño/a",
        "prompt": "portrait of a child, head and shoulders, front view, innocent expression, soft setting",
        "framing": "portrait, child",
        "filename": "11_portrait_child",
        "group": "sujetos",
    },
    "sty_portrait_elder": {
        "label": "Retrato — persona mayor",
        "prompt": "portrait of an elderly person, head and shoulders, front view, wise expression, detailed face",
        "framing": "portrait, elderly person",
        "filename": "12_portrait_elder",
        "group": "sujetos",
    },
    "sty_group_people": {
        "label": "Grupo de personas",
        "prompt": "a small group of people together, medium shot, varied poses and interaction, balanced composition",
        "framing": "group of people",
        "filename": "13_group_people",
        "group": "sujetos",
    },
    "sty_forest": {
        "label": "Bosque",
        "prompt": "dense forest scene, trees and undergrowth, dappled light, no people",
        "framing": "forest scene",
        "filename": "14_forest",
        "group": "naturaleza",
    },
    "sty_mountains": {
        "label": "Montañas",
        "prompt": "mountain range scene, peaks and valleys, expansive sky, no people",
        "framing": "mountain landscape",
        "filename": "15_mountains",
        "group": "naturaleza",
    },
    "sty_ocean": {
        "label": "Mar / olas",
        "prompt": "ocean scene with waves, water surface and horizon, coastal atmosphere, no people",
        "framing": "ocean and waves",
        "filename": "16_ocean",
        "group": "naturaleza",
    },
    "sty_flowers": {
        "label": "Flores (primer plano)",
        "prompt": "close-up of flowers and plants, botanical detail, soft light, shallow depth of field",
        "framing": "flowers close-up",
        "filename": "17_flowers",
        "group": "naturaleza",
    },
    "sty_sky": {
        "label": "Cielo / nubes dramáticas",
        "prompt": "dramatic sky filled with clouds, atmospheric lighting, vast open scene, no people",
        "framing": "dramatic sky and clouds",
        "filename": "18_sky",
        "group": "naturaleza",
    },
    "sty_interior": {
        "label": "Interior acogedor",
        "prompt": "cozy interior room scene, furniture and decor, warm ambient light, no people",
        "framing": "interior room",
        "filename": "19_interior",
        "group": "urbano_objetos",
    },
    "sty_vehicle": {
        "label": "Vehículo",
        "prompt": "a vehicle such as a car or motorcycle, three-quarter view, parked in a neutral setting, no people",
        "framing": "vehicle",
        "filename": "20_vehicle",
        "group": "urbano_objetos",
        "ratio": "3:2",  # los vehículos son más anchos que altos
    },
    "sty_food": {
        "label": "Comida / plato",
        "prompt": "an appetizing plated meal on a table, food styling, soft side lighting, top-down or angled view",
        "framing": "food, plated meal",
        "filename": "21_food",
        "group": "urbano_objetos",
    },
    "sty_books_desk": {
        "label": "Libros / escritorio",
        "prompt": "books and objects arranged on a desk, study scene, warm light, detailed everyday objects, no people",
        "framing": "books and desk",
        "filename": "22_books_desk",
        "group": "urbano_objetos",
    },
    "sty_machine": {
        "label": "Máquina / mecanismo",
        "prompt": "a mechanical device or machine with gears and intricate parts, detailed engineering, no people",
        "framing": "machine, mechanism",
        "filename": "23_machine",
        "group": "urbano_objetos",
    },
    "sty_market": {
        "label": "Mercado / puestos",
        "prompt": "a busy market with stalls and goods, lively scene, varied colors and textures, few people in distance",
        "framing": "market stalls",
        "filename": "24_market",
        "group": "urbano_objetos",
    },
    "sty_castle": {
        "label": "Castillo / fortaleza",
        "prompt": "a grand castle or fortress, imposing architecture, epic establishing shot, no people",
        "framing": "castle, fortress",
        "filename": "25_castle",
        "group": "fantasia",
    },
    "sty_creature": {
        "label": "Criatura fantástica",
        "prompt": "a mythical fantasy creature such as a dragon, full body, dynamic pose, neutral background",
        "framing": "fantasy creature",
        "filename": "26_creature",
        "group": "fantasia",
    },
    "sty_scifi": {
        "label": "Nave / robot sci-fi",
        "prompt": "a science fiction spaceship or robot, detailed technology, futuristic setting, no people",
        "framing": "sci-fi spaceship or robot",
        "filename": "27_scifi",
        "group": "fantasia",
    },
    "sty_eye_detail": {
        "label": "Detalle — ojo (primer plano)",
        "prompt": "extreme close-up of a single human eye, iris detail, eyelashes, intimate macro framing",
        "framing": "eye extreme close-up",
        "filename": "28_eye_detail",
        "group": "detalles",
    },
    "sty_hands_detail": {
        "label": "Detalle — manos",
        "prompt": "close-up of hands in a natural gesture, finger and skin detail, soft light, blurred background",
        "framing": "hands detail",
        "filename": "29_hands_detail",
        "group": "detalles",
    },
    "sty_pattern": {
        "label": "Patrón / ornamento",
        "prompt": "decorative ornamental pattern, repeating motif, intricate detail filling the frame, no recognizable subject",
        "framing": "ornamental pattern",
        "filename": "30_pattern",
        "group": "detalles",
    },
}

STYLE_ANGLE_GROUPS = {
    "sujetos": "Sujetos variados (enseñan el estilo)",
    "naturaleza": "Naturaleza",
    "urbano_objetos": "Urbano y objetos",
    "fantasia": "Fantasía / ficción",
    "detalles": "Detalles y primeros planos",
    "variedad": "Variedad adicional",
}

STYLE_DEFAULT_ANGLE_SET = list(STYLE_ANGLES.keys())
# Estilo: los 30 ya reparten ~6 humanos / ~9 entornos / ~7 objetos / ~8
# detalles-fantasía-abstracto (cerca de 25% cada categoría), que es lo que
# enseña el ESTILO sin sesgar a un solo sujeto → equilibrado = completo.
STYLE_BALANCED_ANGLE_SET = list(STYLE_ANGLES.keys())

STYLE_FORM_FIELDS = [
    {"key": "nombre_estilo", "label": "Nombre / descripción del estilo", "type": "entry",
     "placeholder": "ej: impressionismo, cyberpunk noir, acuarela japonesa..."},
    {"key": "artista_ref", "label": "Artista o referencia (opcional)", "type": "entry",
     "placeholder": "ej: Van Gogh, Moebius, Studio Ghibli..."},
    {"key": "tecnica", "label": "Técnica principal", "type": "option",
     "options": ["Fotografía", "Pintura al óleo", "Acuarela", "Dibujo a lápiz",
                 "Arte digital 2D", "Pixel Art", "Cómic / Manga", "Render 3D",
                 "Grabado / Litografía", "Arte conceptual"]},
    {"key": "paleta", "label": "Paleta de colores característica", "type": "entry",
     "placeholder": "ej: colores desaturados fríos, paleta vibrante neón..."},
    {"key": "rasgos_estilo", "label": "Rasgos visuales distintivos", "type": "entry",
     "placeholder": "ej: trazos gruesos, líneas limpias, sombras duras, textura..."},
    {"key": "epoca", "label": "Época / período", "type": "entry",
     "placeholder": "ej: años 80, Belle Époque, futurismo, contemporáneo..."},
]

STYLE_STYLES = {
    "Coherente (sin estilo adicional)": "",
    "Anime": "anime style, clean lineart, cel shading, vibrant colors, high quality anime illustration",
    "Alta calidad base": "masterpiece, high quality, detailed",
    "Arte digital": "digital art, high resolution, detailed",
    "Ilustración": "illustration, detailed artwork",
}

STYLE_NEGATIVE_PROMPT = (
    "blurry, lowres, jpeg artifacts, watermark, text, logo, signature, "
    "bad anatomy, bad proportions, ugly, poorly drawn"
)


# ===========================================================================
# ENRUTAMIENTO POR TIPO DE LoRA
# ===========================================================================
LORA_TYPES = {
    "Personaje": {
        "icon": "🧑",
        "angles": AVATAR_ANGLES,
        "angle_groups": ANGLE_GROUPS,
        "default_angles": DEFAULT_ANGLE_SET,
        "balanced_angles": AVATAR_BALANCED_ANGLE_SET,
        "form_fields": AVATAR_FORM_FIELDS,
        "styles": AVATAR_STYLES,
        "backgrounds": AVATAR_BACKGROUNDS,
        "backgrounds_rotacion": AVATAR_BACKGROUNDS_ROTACION,
        "negative": AVATAR_NEGATIVE_PROMPT,
        "lighting": AVATAR_LIGHTING,
        "label_form": "Ficha del personaje",
        "label_angles": "Ángulos del dataset",
        "label_trigger": "Trigger word (LoRA)",
        "placeholder_trigger": "ej: ohwx_ana",
        "tiene_ficha_auto": True,
        "tiene_imagen_ref": True,
    },
    "Paisaje": {
        "icon": "🏔",
        "angles": LANDSCAPE_ANGLES,
        "angle_groups": LANDSCAPE_ANGLE_GROUPS,
        "default_angles": LANDSCAPE_DEFAULT_ANGLE_SET,
        "balanced_angles": LANDSCAPE_BALANCED_ANGLE_SET,
        "form_fields": LANDSCAPE_FORM_FIELDS,
        "styles": LANDSCAPE_STYLES,
        "backgrounds": None,
        "backgrounds_rotacion": None,
        "negative": LANDSCAPE_NEGATIVE_PROMPT,
        "lighting": "natural outdoor lighting, realistic atmosphere",
        "label_form": "Descripción del paisaje",
        "label_angles": "Encuadres del dataset",
        "label_trigger": "Trigger word (LoRA)",
        "placeholder_trigger": "ej: ohwx_patagonia",
        "tiene_ficha_auto": True,
        "tiene_imagen_ref": True,
    },
    "Objeto": {
        "icon": "📦",
        "angles": OBJECT_ANGLES,
        "angle_groups": OBJECT_ANGLE_GROUPS,
        "default_angles": OBJECT_DEFAULT_ANGLE_SET,
        "balanced_angles": OBJECT_BALANCED_ANGLE_SET,
        "form_fields": OBJECT_FORM_FIELDS,
        "styles": OBJECT_STYLES,
        "backgrounds": AVATAR_BACKGROUNDS,
        "backgrounds_rotacion": AVATAR_BACKGROUNDS_ROTACION,
        "negative": OBJECT_NEGATIVE_PROMPT,
        "lighting": "professional studio lighting, soft shadows, clean setup",
        "label_form": "Descripción del objeto",
        "label_angles": "Vistas del dataset",
        "label_trigger": "Trigger word (LoRA)",
        "placeholder_trigger": "ej: ohwx_reloj",
        "tiene_ficha_auto": True,
        "tiene_imagen_ref": True,
    },
    "Estilo": {
        "icon": "🎨",
        "angles": STYLE_ANGLES,
        "angle_groups": STYLE_ANGLE_GROUPS,
        "default_angles": STYLE_DEFAULT_ANGLE_SET,
        "balanced_angles": STYLE_BALANCED_ANGLE_SET,
        "form_fields": STYLE_FORM_FIELDS,
        "styles": STYLE_STYLES,
        "backgrounds": None,
        "backgrounds_rotacion": None,
        "negative": STYLE_NEGATIVE_PROMPT,
        "lighting": "",
        "label_form": "Descripción del estilo",
        "label_angles": "Sujetos de muestra",
        "label_trigger": "Trigger word (LoRA)",
        "placeholder_trigger": "ej: ohwx_estilo_moebius",
        "tiene_ficha_auto": True,
        "tiene_imagen_ref": False,
    },
}
