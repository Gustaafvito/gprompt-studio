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
}

# Set por defecto recomendado para un LoRA de personaje (16 vistas)
DEFAULT_ANGLE_SET = list(AVATAR_ANGLES.keys())

# Grupos para organizar los checkboxes en la UI
ANGLE_GROUPS = {
    "rostro": "Rostro / Retrato",
    "busto": "Busto / Medio cuerpo",
    "cuerpo": "Cuerpo entero",
    "extras": "Ángulos y expresiones",
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

# Iluminación fija para coherencia entre tomas
AVATAR_LIGHTING = "soft even studio lighting, no harsh shadows, neutral color temperature"
