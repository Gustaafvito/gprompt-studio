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
        "prompt": "full body shot, standing upright, facing camera directly, entire body visible from head to feet, both feet flat on the floor including shoes, complete figure framed with headroom above and floor below, no cropping",
        "framing": "full body, front view",
        "filename": "09_full_front",
        "group": "cuerpo",
    },
    "full_34_left": {
        "label": "Cuerpo entero — 3/4 izquierda",
        "prompt": "full body shot, standing, body turned three-quarter to the left, entire body visible from head to feet, both feet and shoes on the floor, complete figure with floor below, no cropping",
        "framing": "full body, three-quarter left",
        "filename": "10_full_34_left",
        "group": "cuerpo",
    },
    "full_34_right": {
        "label": "Cuerpo entero — 3/4 derecha",
        "prompt": "full body shot, standing, body turned three-quarter to the right, entire body visible from head to feet, both feet and shoes on the floor, complete figure with floor below, no cropping",
        "framing": "full body, three-quarter right",
        "filename": "11_full_34_right",
        "group": "cuerpo",
    },
    "full_back": {
        "label": "Cuerpo entero — espalda",
        "prompt": "full body shot from behind, back view, entire body visible from head to feet, both feet and shoes on the floor, complete figure with floor below, head facing away from camera, no cropping",
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

    # --- AMPLIACIÓN A 50 (2026-07-06): genera de sobra y ELIGE ---
    # Mismas convenciones: los rostros empiezan por "close-up headshot", los
    # bustos por "upper body" y los cuerpos enteros llevan "full body" +
    # pies visibles (así heredan el negative correcto de avatar_prompts).
    "face_up": {
        "label": "Rostro — mirando arriba",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, lower body out of frame, front view, chin tilted up, eyes looking upward above the camera",
        "framing": "close-up portrait, looking up",
        "filename": "31_face_up",
        "group": "rostro",
    },
    "face_down": {
        "label": "Rostro — mirando abajo",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, lower body out of frame, front view, chin tilted down, eyes looking downward",
        "framing": "close-up portrait, looking down",
        "filename": "32_face_down",
        "group": "rostro",
    },
    "face_tilt": {
        "label": "Rostro — cabeza ladeada",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, lower body out of frame, front view, head tilted slightly to one side, relaxed natural look",
        "framing": "close-up portrait, tilted head",
        "filename": "33_face_tilt",
        "group": "rostro",
    },
    "bust_profile_left": {
        "label": "Busto — perfil izquierdo",
        "prompt": "upper body shot, head to chest, cropped at the waist, legs not visible, full left side profile, body and head facing left",
        "framing": "upper body, left profile",
        "filename": "34_bust_profile_left",
        "group": "busto",
    },
    "bust_profile_right": {
        "label": "Busto — perfil derecho",
        "prompt": "upper body shot, head to chest, cropped at the waist, legs not visible, full right side profile, body and head facing right",
        "framing": "upper body, right profile",
        "filename": "35_bust_profile_right",
        "group": "busto",
    },
    "bust_back": {
        "label": "Busto — espalda (peinado)",
        "prompt": "upper body shot from behind, head to chest, cropped at the waist, back view showing the hairstyle and shoulders, head facing away from camera",
        "framing": "upper body, back view",
        "filename": "36_bust_back",
        "group": "busto",
    },
    "full_profile_left": {
        "label": "Cuerpo entero — perfil izquierdo",
        "prompt": "full body shot, standing upright in full left side profile, entire body visible from head to feet, both feet and shoes on the floor, complete figure with floor below, no cropping",
        "framing": "full body, left profile",
        "filename": "37_full_profile_left",
        "group": "cuerpo",
    },
    "full_profile_right": {
        "label": "Cuerpo entero — perfil derecho",
        "prompt": "full body shot, standing upright in full right side profile, entire body visible from head to feet, both feet and shoes on the floor, complete figure with floor below, no cropping",
        "framing": "full body, right profile",
        "filename": "38_full_profile_right",
        "group": "cuerpo",
    },
    "full_34_back": {
        "label": "Cuerpo entero — 3/4 espalda",
        "prompt": "full body shot, body turned three-quarter away from camera showing the back and one shoulder, entire body visible from head to feet, both feet and shoes on the floor, no cropping",
        "framing": "full body, three-quarter back",
        "filename": "39_full_34_back",
        "group": "cuerpo",
    },
    "expression_sad": {
        "label": "Expresión — tristeza",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, front view, sad melancholic expression, downcast eyes",
        "framing": "close-up portrait, sad",
        "filename": "40_expression_sad",
        "group": "extras",
    },
    "expression_wink": {
        "label": "Expresión — guiño",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, front view, playful wink, one eye closed, light smile",
        "framing": "close-up portrait, winking",
        "filename": "41_expression_wink",
        "group": "extras",
    },
    "expression_smirk": {
        "label": "Expresión — sonrisa pícara",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, front view, confident smirk, one raised eyebrow",
        "framing": "close-up portrait, smirking",
        "filename": "42_expression_smirk",
        "group": "extras",
    },
    "expression_talking": {
        "label": "Expresión — hablando",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, front view, mid-speech expression, mouth slightly open as if talking, engaged look",
        "framing": "close-up portrait, talking",
        "filename": "43_expression_talking",
        "group": "extras",
    },
    "expression_side_glance": {
        "label": "Expresión — mirada de reojo",
        "prompt": "close-up headshot, head and shoulders only, cropped at the chest, front view, eyes glancing to the side, subtle intriguing look",
        "framing": "close-up portrait, side glance",
        "filename": "44_expression_side_glance",
        "group": "extras",
    },
    "pose_kneeling": {
        "label": "Pose — de rodillas",
        "prompt": "whole figure visible, kneeling on the ground with upright torso, hands resting on the thighs, neutral background",
        "framing": "whole figure, kneeling",
        "filename": "45_pose_kneeling",
        "group": "poses",
    },
    "pose_crouching": {
        "label": "Pose — en cuclillas",
        "prompt": "whole figure visible, crouching low on the balls of the feet, arms resting on the knees, compact pose, neutral background",
        "framing": "whole figure, crouching",
        "filename": "46_pose_crouching",
        "group": "poses",
    },
    "pose_jumping": {
        "label": "Pose — saltando",
        "prompt": "full body shot, jumping in mid-air, both feet off the ground and visible, dynamic joyful leap, entire body visible, no cropping",
        "framing": "full body, jumping mid-air",
        "filename": "47_pose_jumping",
        "group": "poses",
    },
    "pose_running": {
        "label": "Pose — corriendo",
        "prompt": "full body shot, running stride mid-motion, dynamic movement, entire body visible from head to feet, no cropping",
        "framing": "full body, running",
        "filename": "48_pose_running",
        "group": "poses",
    },
    "pose_arms_up": {
        "label": "Pose — brazos en alto",
        "prompt": "full body shot, standing with both arms raised above the head, stretching upward, entire body visible from head to feet, both feet on the floor, no cropping",
        "framing": "full body, arms raised",
        "filename": "49_pose_arms_up",
        "group": "poses",
    },
    "pose_lean_wall": {
        "label": "Pose — apoyada en pared",
        "prompt": "full body shot, leaning casually against a plain wall, one leg crossed over the other, relaxed stance, entire body visible from head to feet, both feet visible, no cropping",
        "framing": "full body, leaning against wall",
        "filename": "50_pose_lean_wall",
        "group": "poses",
    },
}

# Set por defecto: TODAS las vistas (50). La idea es generar de sobra y
# ELEGIR 25-40 según la guía SeaArt (el botón ⚖ Equilibrado cura 22).
DEFAULT_ANGLE_SET = list(AVATAR_ANGLES.keys())

# Selección EQUILIBRADA (botón "⚖ Equilibrado"): para personaje la guía SeaArt
# pide ~60% planos de control (rostro/busto/cuerpo neutros, para memorizar ropa
# y rasgos) y limitar expresiones extremas a 4-5. "Todos los 50" hace lo
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

# Variante en LENGUAJE NATURAL de cada estilo, para modelos que NO usan tags
# (Flux, Z-Image, Qwen: is_natural=True). La jerga de Stable Diffusion
# ("octane render, subsurface scattering, high poly") esos modelos la ignoran;
# aquí el estilo se expresa como una frase que sí interpretan. Mismas claves
# que AVATAR_STYLES (un candado lo verifica).
AVATAR_STYLES_NATURAL = {
    "Fotorrealista": "as a photorealistic professional studio photograph, sharp focus, natural detailed skin texture, shot on an 85mm lens",
    "Anime": "in a clean, high-quality anime illustration style with crisp linework, cel shading and vibrant colors",
    "Render 3D": "rendered as a polished 3D CGI character with soft stylized shading, like a modern animated film",
    "Ilustración digital": "as a detailed digital painting with painterly brushwork and rich color",
    "Cómic occidental": "in a bold Western comic-book art style with strong ink outlines and flat graphic colors",
    "Pixar / Cartoon 3D": "in the style of a Pixar-like 3D animated movie, stylized and charming, with soft cinematic lighting",
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
# Refuerzo de los DOS defectos más frecuentes en modelos SDXL/Pony (los que
# se colaban en los datasets): MANOS deformes y MARCAS DE AGUA/texto que el
# modelo base "recuerda" de sus imágenes de entrenamiento. Los términos base
# ("bad hands", "watermark") son demasiado flojos; estos fragmentos añaden el
# vocabulario que de verdad pesa. Se anexan a los negativos de datasets con
# persona (Personaje y NSFW).
AVATAR_NEGATIVE_MANOS = (
    "mutated hands, malformed hands, poorly drawn hands, fused fingers, "
    "too many fingers, missing fingers, extra digits, deformed fingers, "
    "disfigured hands, mangled hands"
)
AVATAR_NEGATIVE_MARCA_AGUA = (
    "watermark, text, logo, signature, username, artist name, caption text, letters"
)

AVATAR_NEGATIVE_PROMPT = (
    "multiple people, two persons, deformed face, asymmetric eyes, extra fingers, "
    "extra limbs, missing limbs, bad anatomy, bad hands, blurry, lowres, jpeg artifacts, "
    "watermark, text, logo, signature, cropped head, out of frame, different clothing, "
    "different hairstyle, inconsistent face, busy background, cluttered background, "
    + AVATAR_NEGATIVE_MANOS + ", " + AVATAR_NEGATIVE_MARCA_AGUA
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

# EXTRA solo para tomas de CUERPO ENTERO (no cowboy, que es de medio muslo
# arriba): fuerza que se vean los pies. Muchos modelos recortan a la altura de
# tobillos/rodillas aunque el positivo pida "head to feet"; meter el recorte de
# piernas/pies en el negative es el lever que empuja a encuadrar la figura entera.
AVATAR_NEGATIVE_PIES = (
    "cropped legs, cropped at the ankles, cropped at the knees, cropped at the shins, "
    "feet out of frame, feet cut off, cut off feet, feet not visible, partial body"
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

    # --- AMPLIACIÓN A 50 (2026-07-06): genera de sobra y ELIGE ---
    "ls_vertical": {
        "label": "Formato vertical (9:16)",
        "prompt": "vertical landscape composition, tall scene emphasizing height, strong foreground leading upward to the sky, no people",
        "framing": "vertical composition",
        "filename": "31_vertical",
        "group": "composicion",
        "ratio": "9:16",  # el único plano de paisaje pensado en vertical
    },
    "ls_symmetry": {
        "label": "Simetría central",
        "prompt": "perfectly symmetrical landscape composition, centered subject, mirrored balance left and right, no people",
        "framing": "symmetrical composition",
        "filename": "32_symmetry",
        "group": "composicion",
        "ratio": "3:2",
    },
    "ls_diagonal": {
        "label": "Composición diagonal",
        "prompt": "landscape with strong diagonal lines crossing the frame, slopes and ridgelines, dynamic tension, no people",
        "framing": "diagonal composition",
        "filename": "33_diagonal",
        "group": "composicion",
        "ratio": "3:2",
    },
    "ls_low_horizon": {
        "label": "Horizonte bajo (cielo protagonista)",
        "prompt": "landscape with very low horizon line, sky filling most of the frame, dramatic cloudscape above, no people",
        "framing": "low horizon, sky dominant",
        "filename": "34_low_horizon",
        "group": "composicion",
    },
    "ls_high_horizon": {
        "label": "Horizonte alto (suelo protagonista)",
        "prompt": "landscape with high horizon line, terrain filling most of the frame, patterns and textures of the land, no people",
        "framing": "high horizon, land dominant",
        "filename": "35_high_horizon",
        "group": "composicion",
        "ratio": "3:2",  # el "textures" del prompt no debe volverlo 1:1
    },
    "ls_telephoto": {
        "label": "Teleobjetivo (compresión)",
        "prompt": "telephoto compressed landscape, distant layers stacked together, flattened perspective, tight crop of faraway scenery, no people",
        "framing": "telephoto compression",
        "filename": "36_telephoto",
        "group": "composicion",
        "ratio": "3:2",
    },
    "ls_autumn_leaves": {
        "label": "Hojas de otoño (detalle)",
        "prompt": "close-up of autumn foliage, colorful fallen leaves, warm oranges and reds, soft light, no people",
        "framing": "autumn foliage close-up",
        "filename": "37_autumn_leaves",
        "group": "detalle",
    },
    "ls_ice_detail": {
        "label": "Detalle de hielo",
        "prompt": "close-up of ice formations, frozen textures, crystalline detail, cold blue tones, no people",
        "framing": "ice close-up detail",
        "filename": "38_ice_detail",
        "group": "detalle",
    },
    "ls_sand_texture": {
        "label": "Textura de arena / dunas",
        "prompt": "close-up of sand patterns and ripples, wind-carved texture, warm tones, raking light, no people",
        "framing": "sand texture close-up",
        "filename": "39_sand_texture",
        "group": "detalle",
    },
    "ls_moss_bark": {
        "label": "Musgo y corteza",
        "prompt": "close-up of moss and tree bark, rich green texture, forest floor detail, soft diffused light, no people",
        "framing": "moss and bark close-up",
        "filename": "40_moss_bark",
        "group": "detalle",
    },
    "ls_god_rays": {
        "label": "Rayos crepusculares (god rays)",
        "prompt": "landscape with god rays, sunbeams breaking through clouds or trees, volumetric light shafts, no people",
        "framing": "god rays, volumetric light",
        "filename": "41_god_rays",
        "group": "luz",
    },
    "ls_milky_way": {
        "label": "Vía Láctea",
        "prompt": "night landscape under the milky way, star-filled sky, galactic core visible, dark foreground silhouette, no people",
        "framing": "milky way night sky",
        "filename": "42_milky_way",
        "group": "luz",
    },
    "ls_aurora": {
        "label": "Aurora boreal",
        "prompt": "landscape under the aurora borealis, green and violet lights dancing in the night sky, snowy foreground, no people",
        "framing": "aurora borealis",
        "filename": "43_aurora",
        "group": "luz",
    },
    "ls_lightning": {
        "label": "Tormenta eléctrica (rayos)",
        "prompt": "stormy landscape with a lightning bolt striking in the distance, dramatic dark clouds, electric illumination, no people",
        "framing": "lightning storm",
        "filename": "44_lightning",
        "group": "luz",
    },
    "ls_rainbow": {
        "label": "Arcoíris",
        "prompt": "landscape with a vivid rainbow after the rain, clearing storm clouds, fresh saturated colors, no people",
        "framing": "rainbow after rain",
        "filename": "45_rainbow",
        "group": "clima",
    },
    "ls_frost": {
        "label": "Escarcha matinal",
        "prompt": "frosty morning landscape, frost covering grass and branches, crisp cold air, pale early light, no people",
        "framing": "morning frost",
        "filename": "46_frost",
        "group": "clima",
    },
    "ls_dust_storm": {
        "label": "Tormenta de polvo / arena",
        "prompt": "arid landscape with an approaching dust storm, hazy wall of sand on the horizon, dramatic ochre tones, no people",
        "framing": "dust storm, arid",
        "filename": "47_dust_storm",
        "group": "clima",
    },
    "ls_black_white": {
        "label": "Blanco y negro",
        "prompt": "black and white fine art landscape, dramatic tonal contrast, monochrome photography, rich texture, no people",
        "framing": "black and white, monochrome",
        "filename": "48_black_white",
        "group": "tecnica",
    },
    "ls_drone_low": {
        "label": "Dron a baja altura",
        "prompt": "low altitude drone shot gliding over the terrain, oblique aerial perspective, sense of depth and scale, no people",
        "framing": "low drone, oblique aerial",
        "filename": "49_drone_low",
        "group": "tecnica",
    },
    "ls_star_trails": {
        "label": "Círculos de estrellas (startrails)",
        "prompt": "long exposure star trails circling in the night sky above the landscape, concentric arcs of light, no people",
        "framing": "star trails, long exposure",
        "filename": "50_star_trails",
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

LANDSCAPE_STYLES_NATURAL = {
    "Fotografía realista": "as a professional nature photograph, ultra sharp, natural light, shot on a 16mm wide-angle lens",
    "Anime": "as anime background art in the style of Makoto Shinkai, clean and vibrant with painterly skies",
    "Cinematográfico": "with a cinematic anamorphic look, subtle film grain and graded film color",
    "Pintura al óleo": "as a traditional oil painting with visible brushstrokes and rich texture",
    "Acuarela": "as a soft watercolor painting with translucent washes and paper texture",
    "Arte digital": "as detailed digital concept art, a polished matte painting",
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

    # --- AMPLIACIÓN A 50 (2026-07-06): genera de sobra y ELIGE ---
    "obj_34_back_left": {
        "label": "3/4 trasera izquierda",
        "prompt": "three-quarter back left angle product shot, showing the back and left side of the object, clean background, studio lighting",
        "framing": "three-quarter back left",
        "filename": "31_34_back_left",
        "group": "vistas",
    },
    "obj_34_back_right": {
        "label": "3/4 trasera derecha",
        "prompt": "three-quarter back right angle product shot, showing the back and right side of the object, clean background, studio lighting",
        "framing": "three-quarter back right",
        "filename": "32_34_back_right",
        "group": "vistas",
    },
    "obj_tilted": {
        "label": "Inclinado (ángulo dinámico)",
        "prompt": "product shot with the object tilted at a dynamic diagonal angle, floating tension, bold composition, clean background",
        "framing": "tilted dynamic angle",
        "filename": "33_tilted",
        "group": "vistas",
        "warn": "Ángulo muy marcado — recomendado máx. 1-2 en el dataset.",
    },
    "obj_exploded": {
        "label": "Vista explotada (piezas)",
        "prompt": "exploded view product shot, parts separated and floating in alignment, technical presentation, clean background",
        "framing": "exploded view",
        "filename": "34_exploded",
        "group": "vistas",
        "warn": "Vista técnica agresiva — recomendado máx. 1-2 en el dataset.",
    },
    "obj_interior_detail": {
        "label": "Detalle interior",
        "prompt": "close-up of the interior of the object, inner construction and lining visible, sharp focus, controlled light",
        "framing": "interior detail",
        "filename": "35_interior_detail",
        "group": "detalle",
    },
    "obj_base_detail": {
        "label": "Detalle de base / soporte",
        "prompt": "close-up of the base or underside support of the object, feet stand or bottom finish detail, sharp focus",
        "framing": "base and stand detail",
        "filename": "36_base_detail",
        "group": "detalle",
    },
    "obj_engraving": {
        "label": "Detalle de grabado / relieve",
        "prompt": "extreme close-up macro of engraving or embossed relief on the object surface, raking light revealing depth",
        "framing": "engraving relief macro",
        "filename": "37_engraving",
        "group": "detalle",
    },
    "obj_top_detail": {
        "label": "Detalle superior (tapa)",
        "prompt": "close-up of the top part of the object, cap lid or upper edge detail, sharp focus, shallow depth of field",
        "framing": "top part detail",
        "filename": "38_top_detail",
        "group": "detalle",
    },
    "obj_packaging": {
        "label": "Con su packaging",
        "prompt": "product shot next to its box or packaging, retail presentation, clean studio setting, no people",
        "framing": "with packaging",
        "filename": "39_packaging",
        "group": "contexto",
    },
    "obj_on_shelf": {
        "label": "En estantería",
        "prompt": "product displayed on a shelf, retail or home context, neat arrangement, ambient light, no people",
        "framing": "on a shelf",
        "filename": "40_on_shelf",
        "group": "contexto",
    },
    "obj_mirror_surface": {
        "label": "Sobre superficie espejo",
        "prompt": "product shot on a reflective mirror surface, clean symmetrical reflection below the object, studio lighting",
        "framing": "mirror surface reflection",
        "filename": "41_mirror_surface",
        "group": "contexto",
    },
    "obj_water_splash": {
        "label": "Salpicadura de agua",
        "prompt": "dynamic product shot with a water splash frozen in motion around the object, high speed photography look, clean background",
        "framing": "water splash, high speed",
        "filename": "42_water_splash",
        "group": "contexto",
    },
    "obj_smoke": {
        "label": "Humo / niebla ambiental",
        "prompt": "product shot surrounded by wisps of smoke or mist, atmospheric mood, dark background, dramatic light",
        "framing": "smoke and mist mood",
        "filename": "43_smoke",
        "group": "contexto",
    },
    "obj_colored_backdrop": {
        "label": "Fondo de color liso",
        "prompt": "product shot on a bold solid color backdrop, complementary color contrast, modern commercial look, even lighting",
        "framing": "solid color backdrop",
        "filename": "44_colored_backdrop",
        "group": "contexto",
    },
    "obj_gradient_backdrop": {
        "label": "Fondo degradado",
        "prompt": "product shot on a smooth gradient backdrop, soft color transition behind the object, clean commercial lighting",
        "framing": "gradient backdrop",
        "filename": "45_gradient_backdrop",
        "group": "contexto",
    },
    "obj_window_light": {
        "label": "Luz natural de ventana",
        "prompt": "product shot lit by soft window light, gentle shadows, natural daylight mood, lifestyle setting, no people",
        "framing": "window light, natural",
        "filename": "46_window_light",
        "group": "contexto",
    },
    "obj_spotlight": {
        "label": "Foco puntual (spotlight)",
        "prompt": "product shot under a single spotlight beam, pool of light on dark surroundings, theatrical presentation",
        "framing": "single spotlight",
        "filename": "47_spotlight",
        "group": "contexto",
    },
    "obj_texture_backdrop": {
        "label": "Fondo con textura (tela/papel)",
        "prompt": "product shot on a textured backdrop such as linen fabric or craft paper, tactile warm setting, soft light",
        "framing": "textured backdrop",
        "filename": "48_texture_backdrop",
        "group": "contexto",
    },
    "obj_wet_surface": {
        "label": "Superficie mojada (gotas)",
        "prompt": "product shot on a wet surface with water droplets, fresh glossy look, subtle reflections, controlled studio light",
        "framing": "wet surface, droplets",
        "filename": "49_wet_surface",
        "group": "contexto",
    },
    "obj_neon": {
        "label": "Neón / luz de color",
        "prompt": "product shot with colored neon lighting, vibrant rim lights in contrasting hues, dark moody background",
        "framing": "neon colored lighting",
        "filename": "50_neon",
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
_OBJECT_VISTAS_AGRESIVAS = {"obj_bottom", "obj_isometric", "obj_hero_low",
                            "obj_tilted", "obj_exploded"}
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

OBJECT_STYLES_NATURAL = {
    "Fotografía de producto": "as a professional product photograph with clean studio lighting and crisp commercial quality",
    "Anime": "in a clean anime illustration style with crisp linework and vibrant colors",
    "Editorial / Lifestyle": "as an editorial lifestyle photograph with atmospheric lighting and a contextual setting",
    "Render 3D": "as a photorealistic 3D product render with perfect, clean lighting",
    "Artístico / Dramático": "as an artistic, dramatically lit fine-art photograph with a moody composition",
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
        "prompt": "urban city street scene, buildings and architecture, empty street, daytime, no people",
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
        "prompt": "market stalls full of goods, varied colors and textures, daytime, no people, empty of vendors",
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

    # --- AMPLIACIÓN A 50 (2026-07-06): más sujetos = más variedad de estilo ---
    "sty_portrait_profile": {
        "label": "Retrato — perfil",
        "prompt": "portrait of a person in full side profile, head and shoulders, elegant contour, neutral setting",
        "framing": "portrait, side profile",
        "filename": "31_portrait_profile",
        "group": "sujetos",
    },
    "sty_couple": {
        "label": "Pareja",
        "prompt": "two people together in a warm moment, medium shot, natural interaction, balanced composition",
        "framing": "couple, medium shot",
        "filename": "32_couple",
        "group": "sujetos",
    },
    "sty_dancer": {
        "label": "Bailarín/a en movimiento",
        "prompt": "a dancer in mid-movement, flowing motion, expressive full body pose, minimal setting",
        "framing": "dancer in motion",
        "filename": "33_dancer",
        "group": "sujetos",
    },
    "sty_musician": {
        "label": "Músico con instrumento",
        "prompt": "a musician playing an instrument, medium shot, focused expression, atmospheric setting",
        "framing": "musician, medium shot",
        "filename": "34_musician",
        "group": "sujetos",
    },
    "sty_desert": {
        "label": "Desierto",
        "prompt": "desert scene with dunes or arid terrain, vast dry landscape, warm tones, no people",
        "framing": "desert scene",
        "filename": "35_desert",
        "group": "naturaleza",
    },
    "sty_waterfall": {
        "label": "Cascada",
        "prompt": "waterfall scene, falling water and rocks, lush surroundings, mist in the air, no people",
        "framing": "waterfall scene",
        "filename": "36_waterfall",
        "group": "naturaleza",
    },
    "sty_snow_scene": {
        "label": "Paisaje nevado",
        "prompt": "snowy winter scene, snow-covered terrain and trees, cold tones, quiet atmosphere, no people",
        "framing": "snowy winter scene",
        "filename": "37_snow_scene",
        "group": "naturaleza",
    },
    "sty_starry_night": {
        "label": "Cielo estrellado",
        "prompt": "starry night sky scene over a dark landscape, stars and constellations, deep blues, no people",
        "framing": "starry night scene",
        "filename": "38_starry_night",
        "group": "naturaleza",
    },
    "sty_underwater": {
        "label": "Escena submarina",
        "prompt": "underwater scene, light rays filtering through the water, marine life or coral, blue depths, no people",
        "framing": "underwater scene",
        "filename": "39_underwater",
        "group": "naturaleza",
    },
    "sty_night_city": {
        "label": "Ciudad nocturna",
        "prompt": "city street at night, glowing lights and signs, reflections on wet pavement, no people",
        "framing": "night city scene",
        "filename": "40_night_city",
        "group": "urbano_objetos",
    },
    "sty_bridge": {
        "label": "Puente",
        "prompt": "a large bridge structure spanning water or a valley, engineering lines, dramatic perspective, no people",
        "framing": "bridge structure",
        "filename": "41_bridge",
        "group": "urbano_objetos",
        "ratio": "3:2",  # estructura horizontal; sin cue de escena en el prompt
    },
    "sty_cafe_interior": {
        "label": "Interior de cafetería",
        "prompt": "cozy cafe interior, tables cups and warm lamps, inviting atmosphere, no people",
        "framing": "cafe interior",
        "filename": "42_cafe_interior",
        "group": "urbano_objetos",
        "ratio": "3:2",  # sala completa → horizontal
    },
    "sty_harbor": {
        "label": "Puerto / barcas",
        "prompt": "harbor scene with boats moored at the dock, water reflections, maritime atmosphere, no people",
        "framing": "harbor scene",
        "filename": "43_harbor",
        "group": "urbano_objetos",
    },
    "sty_ruins": {
        "label": "Ruinas antiguas",
        "prompt": "ancient ruins overgrown with vegetation, crumbling columns and stone, mysterious atmosphere, no people",
        "framing": "ancient ruins scene",
        "filename": "44_ruins",
        "group": "fantasia",
    },
    "sty_floating_islands": {
        "label": "Islas flotantes",
        "prompt": "fantasy floating islands in the sky, waterfalls falling into the clouds, epic scale, no people",
        "framing": "floating islands, sky",
        "filename": "45_floating_islands",
        "group": "fantasia",
    },
    "sty_space": {
        "label": "Espacio / planetas",
        "prompt": "outer space scene with planets and nebulae, cosmic colors, vast scale, no people",
        "framing": "outer space scene",
        "filename": "46_space",
        "group": "fantasia",
    },
    "sty_fabric": {
        "label": "Tela / pliegues",
        "prompt": "close-up of draped fabric with flowing folds, texture and light interplay, rich material detail",
        "framing": "fabric folds close-up",
        "filename": "47_fabric",
        "group": "detalles",
    },
    "sty_glass": {
        "label": "Cristal / transparencia",
        "prompt": "close-up of glass objects, transparency and refraction, light passing through, delicate highlights",
        "framing": "glass close-up",
        "filename": "48_glass",
        "group": "detalles",
    },
    "sty_rain_window": {
        "label": "Lluvia en la ventana",
        "prompt": "raindrops on a window pane, blurred lights behind the glass, melancholic mood, close-up detail",
        "framing": "rain on window close-up",
        "filename": "49_rain_window",
        "group": "detalles",
    },
    "sty_fire_smoke": {
        "label": "Fuego y humo",
        "prompt": "flames and smoke composition, glowing embers, dramatic light and movement, no people",
        "framing": "fire and smoke",
        "filename": "50_fire_smoke",
        "group": "variedad",
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
# Estilo: los 50 reparten humanos / entornos / objetos / detalles-fantasía
# a ~25% cada categoría, que es lo que enseña el ESTILO sin sesgar a un
# solo sujeto → equilibrado = completo (genera de sobra y elige).
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

STYLE_STYLES_NATURAL = {
    "Coherente (sin estilo adicional)": "",
    "Anime": "in a clean, high-quality anime illustration style with crisp linework, cel shading and vibrant colors",
    "Alta calidad base": "highly detailed and polished, high quality",
    "Arte digital": "as high-resolution, detailed digital art",
    "Ilustración": "as a detailed illustration",
}

STYLE_NEGATIVE_PROMPT = (
    "blurry, lowres, jpeg artifacts, watermark, text, logo, signature, "
    "bad anatomy, bad proportions, ugly, poorly drawn"
)


# ===========================================================================
# TIPO: NSFW (PERSONAJE ADULTO, 18+)
# ===========================================================================
# Dataset de identidad para LoRA de personaje ADULTO con contenido NSFW.
# Diseño (2026-07-06, petición del usuario):
# - SOLO sujeto en solitario (para un LoRA de identidad no hacen falta
#   actos: se entrena la persona, no la escena). 3 niveles: lencería →
#   sugerente (implied) → desnudo artístico.
# - La descripción canónica NO lleva ropa (el vestuario varía por toma y
#   lo pone cada prompt) y DEBE declarar "adult". El negative bloquea
#   términos de menores en todas las imágenes.
# - La luz va por toma (claroscuro, ventana...) → lighting global vacío,
#   y el escenario también (cama, ducha) → sin selector de fondos.
NSFW_ANGLES = {
    # --- LENCERÍA / BOUDOIR ---
    "nsfw_lenc_full_front": {
        "label": "Lencería — cuerpo entero frontal",
        "prompt": "full body shot, adult subject standing, wearing an elegant black lace lingerie set, facing camera, entire body visible from head to feet, both feet on the floor, no cropping, soft boudoir lighting",
        "framing": "full body, black lingerie",
        "filename": "01_lenc_full_front",
        "group": "lenceria",
        "neg_extra": "cropped legs, feet out of frame, cut off feet",
    },
    "nsfw_lenc_full_back": {
        "label": "Lencería — cuerpo entero espalda",
        "prompt": "full body shot from behind, adult subject standing, back view, wearing an elegant black lace lingerie set, entire body visible from head to feet, no cropping, soft boudoir lighting",
        "framing": "full body back view, lingerie",
        "filename": "02_lenc_full_back",
        "group": "lenceria",
        "neg_extra": "cropped legs, feet out of frame, cut off feet",
    },
    "nsfw_lenc_34": {
        "label": "Lencería — 3/4",
        "prompt": "full body shot, adult subject standing, body turned three-quarter view, wearing an elegant black lace lingerie set, entire body visible, no cropping, soft boudoir lighting",
        "framing": "full body three-quarter, lingerie",
        "filename": "03_lenc_34",
        "group": "lenceria",
    },
    "nsfw_lenc_bust": {
        "label": "Lencería — busto",
        "prompt": "upper body shot, adult subject, head to chest, cropped at the waist, wearing an elegant lace bralette, front view, soft flattering light",
        "framing": "upper body, lace bralette",
        "filename": "04_lenc_bust",
        "group": "lenceria",
    },
    "nsfw_lenc_seated_bed": {
        "label": "Lencería — sentada al borde de la cama",
        "prompt": "adult subject in elegant lingerie sitting on the edge of a bed, relaxed pose, whole figure visible, soft warm bedroom light",
        "framing": "seated on bed edge, lingerie",
        "filename": "05_lenc_seated_bed",
        "group": "lenceria",
    },
    "nsfw_lenc_lying_bed": {
        "label": "Lencería — tumbada en la cama",
        "prompt": "adult subject in elegant lingerie lying on a bed, reclined sensual pose, whole figure visible, soft warm bedroom light",
        "framing": "lying on bed, lingerie",
        "filename": "06_lenc_lying_bed",
        "group": "lenceria",
        "ratio": "3:2",  # figura reclinada → horizontal
    },
    "nsfw_lenc_white": {
        "label": "Lencería blanca delicada",
        "prompt": "adult subject standing in a delicate white lace lingerie set, soft innocent styling, whole figure visible, bright airy light",
        "framing": "white lingerie set",
        "filename": "07_lenc_white",
        "group": "lenceria",
    },
    "nsfw_lenc_red_satin": {
        "label": "Lencería roja de satén",
        "prompt": "adult subject standing in a red satin lingerie set, glossy fabric highlights, whole figure visible, warm dramatic light",
        "framing": "red satin lingerie",
        "filename": "08_lenc_red_satin",
        "group": "lenceria",
    },
    "nsfw_lenc_bodysuit": {
        "label": "Body de encaje",
        "prompt": "adult subject standing in a sheer lace bodysuit, elegant single-piece lingerie, whole figure visible, soft boudoir lighting",
        "framing": "sheer lace bodysuit",
        "filename": "09_lenc_bodysuit",
        "group": "lenceria",
    },
    "nsfw_lenc_stockings": {
        "label": "Medias y liguero",
        "prompt": "adult subject in lingerie with stockings and garter belt, seated pose showing the legs, whole figure visible, classic boudoir styling",
        "framing": "stockings and garter belt",
        "filename": "10_lenc_stockings",
        "group": "lenceria",
    },
    "nsfw_lenc_open_shirt": {
        "label": "Camisa abierta (insinuante)",
        "prompt": "adult subject wearing an unbuttoned oversized shirt over underwear, suggestive but covered, relaxed standing pose, soft morning light",
        "framing": "open shirt, suggestive",
        "filename": "11_lenc_open_shirt",
        "group": "lenceria",
    },
    "nsfw_lenc_towel": {
        "label": "Toalla (recién duchada)",
        "prompt": "adult subject wrapped in a white towel after a shower, damp hair, bare shoulders, fresh clean look, bathroom setting, soft light",
        "framing": "wrapped in towel",
        "filename": "12_lenc_towel",
        "group": "lenceria",
    },

    # --- SUGERENTE (IMPLIED, sin desnudo explícito) ---
    "nsfw_impl_sheet": {
        "label": "Envuelta en sábana",
        "prompt": "adult subject wrapped in a white bed sheet, bare shoulders and legs visible, implied nudity, elegant pose on a bed, soft window light",
        "framing": "wrapped in bed sheet, implied",
        "filename": "13_impl_sheet",
        "group": "sugerente",
    },
    "nsfw_impl_back_bare": {
        "label": "Espalda desnuda",
        "prompt": "adult subject with bare back to the camera, back view from the waist up, no clothing on the upper body, looking away, elegant curve of the spine, soft light",
        "framing": "bare back view, waist up",
        "filename": "14_impl_back_bare",
        "group": "sugerente",
    },
    "nsfw_impl_hands_cover": {
        "label": "Cubierta con los brazos",
        "prompt": "adult subject topless with arms crossed covering the chest, implied nudity, front view from the waist up, confident gaze, studio lighting",
        "framing": "arms covering chest, implied",
        "filename": "15_impl_hands_cover",
        "group": "sugerente",
    },
    "nsfw_impl_silhouette": {
        "label": "Silueta tras cortina (contraluz)",
        "prompt": "adult subject nude silhouette backlit behind a sheer curtain, body outline visible but no explicit detail, artistic backlight, moody atmosphere",
        "framing": "backlit silhouette, curtain",
        "filename": "16_impl_silhouette",
        "group": "sugerente",
    },
    "nsfw_impl_shower_glass": {
        "label": "Tras el cristal de la ducha",
        "prompt": "adult subject behind frosted shower glass, blurred body shape through steamy glass, implied nudity, water droplets on the glass, soft bathroom light",
        "framing": "behind frosted shower glass",
        "filename": "17_impl_shower_glass",
        "group": "sugerente",
    },
    "nsfw_impl_over_shoulder": {
        "label": "Mirada sobre hombro desnudo",
        "prompt": "adult subject with bare shoulders looking back over the shoulder at the camera, upper back visible, intimate expression, close warm light",
        "framing": "over bare shoulder look",
        "filename": "18_impl_over_shoulder",
        "group": "sugerente",
    },
    "nsfw_impl_side_curve": {
        "label": "Perfil insinuado (curva lateral)",
        "prompt": "adult subject nude in full side profile with arms and pose concealing explicit detail, implied nudity, elegant body curve, rim lighting on the skin",
        "framing": "side profile curve, implied",
        "filename": "19_impl_side_curve",
        "group": "sugerente",
    },
    "nsfw_impl_bath": {
        "label": "En la bañera (espuma)",
        "prompt": "adult subject relaxing in a bathtub with foam covering the body, bare shoulders and knees visible, candles around, cozy intimate atmosphere",
        "framing": "in bathtub with foam",
        "filename": "20_impl_bath",
        "group": "sugerente",
        "ratio": "3:2",  # bañera horizontal
    },

    # --- DESNUDO ARTÍSTICO ---
    "nsfw_nude_standing": {
        "label": "Desnudo — de pie frontal",
        "prompt": "full body artistic nude, adult subject standing, tasteful frontal pose, entire body visible from head to feet, both feet on the floor, no cropping, professional fine art photography lighting",
        "framing": "full body nude, standing front",
        "filename": "21_nude_standing",
        "group": "artistico",
        "neg_extra": "cropped legs, feet out of frame, cut off feet",
    },
    "nsfw_nude_34": {
        "label": "Desnudo — 3/4",
        "prompt": "full body artistic nude, adult subject standing turned three-quarter view, elegant posture, entire body visible, no cropping, sculptural studio lighting",
        "framing": "full body nude, three-quarter",
        "filename": "22_nude_34",
        "group": "artistico",
    },
    "nsfw_nude_back": {
        "label": "Desnudo — espalda entera",
        "prompt": "full body artistic nude from behind, adult subject standing, back view, entire body visible from head to feet, no cropping, soft directional light on the skin",
        "framing": "full body nude, back view",
        "filename": "23_nude_back",
        "group": "artistico",
        "neg_extra": "cropped legs, feet out of frame, cut off feet",
    },
    "nsfw_nude_seated": {
        "label": "Desnudo — sentado artístico",
        "prompt": "artistic nude, adult subject seated on a stool, classic figure study pose, whole figure visible, dramatic side lighting, fine art photography",
        "framing": "nude figure study, seated",
        "filename": "24_nude_seated",
        "group": "artistico",
    },
    "nsfw_nude_reclining": {
        "label": "Desnudo — reclinado clásico",
        "prompt": "artistic nude, adult subject reclining on draped fabric, classical odalisque pose, whole figure visible, painterly soft light, fine art composition",
        "framing": "reclining nude, classical",
        "filename": "25_nude_reclining",
        "group": "artistico",
        "ratio": "3:2",  # reclinado clásico → horizontal
    },
    "nsfw_nude_kneeling_bed": {
        "label": "Desnudo — de rodillas en la cama",
        "prompt": "artistic nude, adult subject kneeling on a bed, upright torso, sensual but tasteful pose, whole figure visible, warm intimate bedroom light",
        "framing": "nude kneeling on bed",
        "filename": "26_nude_kneeling_bed",
        "group": "artistico",
    },
    "nsfw_nude_chiaroscuro": {
        "label": "Desnudo — claroscuro",
        "prompt": "artistic nude, adult subject, dramatic chiaroscuro lighting, deep shadows sculpting the body, dark background, low-key fine art photography",
        "framing": "nude chiaroscuro, low key",
        "filename": "27_nude_chiaroscuro",
        "group": "artistico",
    },
    "nsfw_nude_window": {
        "label": "Desnudo — luz de ventana",
        "prompt": "artistic nude, adult subject standing by a large window, soft natural daylight wrapping the body, contemplative mood, whole figure visible",
        "framing": "nude by window light",
        "filename": "28_nude_window",
        "group": "artistico",
    },
    "nsfw_nude_torso": {
        "label": "Desnudo — torso (detalle)",
        "prompt": "artistic nude close-up of the torso, adult subject, from shoulders to hips, sculptural skin detail, soft directional light, fine art crop",
        "framing": "nude torso close-up",
        "filename": "29_nude_torso",
        "group": "artistico",
        "neg_extra": "full body, full-length shot, wide shot, face, head",
    },
    "nsfw_nude_wet": {
        "label": "Desnudo — piel mojada",
        "prompt": "artistic nude, adult subject with wet skin and damp hair under falling water, glistening water droplets on the body, shower setting, moody light",
        "framing": "nude wet skin, shower",
        "filename": "30_nude_wet",
        "group": "artistico",
    },

    # --- AMPLIACIÓN A 50 (2026-07-06): más ángulos por nivel ---
    "nsfw_lenc_bust_34": {
        "label": "Lencería — busto 3/4",
        "prompt": "upper body shot, adult subject in an elegant lace bralette, body turned three-quarter view, cropped at the waist, soft flattering light",
        "framing": "upper body three-quarter, lingerie",
        "filename": "31_lenc_bust_34",
        "group": "lenceria",
    },
    "nsfw_lenc_profile": {
        "label": "Lencería — perfil cuerpo entero",
        "prompt": "full body shot, adult subject standing in full side profile wearing an elegant lingerie set, entire body visible from head to feet, no cropping, soft boudoir lighting",
        "framing": "full body side profile, lingerie",
        "filename": "32_lenc_profile",
        "group": "lenceria",
        "neg_extra": "cropped legs, feet out of frame, cut off feet",
    },
    "nsfw_lenc_kneel_bed": {
        "label": "Lencería — de rodillas en la cama",
        "prompt": "adult subject in elegant lingerie kneeling on a bed, upright torso, playful sensual pose, whole figure visible, warm bedroom light",
        "framing": "kneeling on bed, lingerie",
        "filename": "33_lenc_kneel_bed",
        "group": "lenceria",
    },
    "nsfw_lenc_robe": {
        "label": "Bata de seda entreabierta",
        "prompt": "adult subject in a silk robe slipping off one shoulder, lingerie visible underneath, standing relaxed pose, warm soft light",
        "framing": "silk robe over lingerie",
        "filename": "34_lenc_robe",
        "group": "lenceria",
    },
    "nsfw_lenc_mirror": {
        "label": "Lencería — frente al espejo",
        "prompt": "adult subject in lingerie standing in front of a full-length mirror, reflection visible, bedroom setting, soft ambient light",
        "framing": "mirror reflection, lingerie",
        "filename": "35_lenc_mirror",
        "group": "lenceria",
    },
    "nsfw_lenc_low_angle": {
        "label": "Lencería — contrapicado",
        "prompt": "low camera angle looking up at an adult subject in elegant lingerie, standing confident pose, dramatic perspective, whole figure visible",
        "framing": "low angle, lingerie",
        "filename": "36_lenc_low_angle",
        "group": "lenceria",
    },
    "nsfw_impl_lying_front": {
        "label": "Boca abajo en la cama (espalda)",
        "prompt": "adult subject lying face down on a bed with bare back exposed, a sheet covering the lower body, implied nudity, relaxed intimate mood, soft light",
        "framing": "lying face down, bare back",
        "filename": "37_impl_lying_front",
        "group": "sugerente",
        "ratio": "3:2",  # tumbada → horizontal
    },
    "nsfw_impl_morning": {
        "label": "Mañana entre sábanas",
        "prompt": "adult subject waking up tangled in white sheets, bare shoulders visible, sleepy soft expression, morning window light, implied nudity",
        "framing": "morning sheets, implied",
        "filename": "38_impl_morning",
        "group": "sugerente",
        "ratio": "3:2",  # escena de cama → horizontal
    },
    "nsfw_impl_steam_mirror": {
        "label": "Espejo empañado (baño)",
        "prompt": "adult subject partially visible in a steamy fogged bathroom mirror, wrapped in a towel, one hand wiping the glass, implied intimate mood",
        "framing": "foggy mirror, bathroom",
        "filename": "39_impl_steam_mirror",
        "group": "sugerente",
    },
    "nsfw_impl_doorway": {
        "label": "Contraluz en el umbral",
        "prompt": "adult subject nude silhouette standing in a doorway backlit by warm light, body outline visible without explicit detail, moody atmosphere",
        "framing": "doorway silhouette, backlit",
        "filename": "40_impl_doorway",
        "group": "sugerente",
    },
    "nsfw_impl_legs": {
        "label": "Detalle — piernas con medias",
        "prompt": "close-up detail of the legs of an adult subject wearing sheer stockings, seated pose, elegant crop from thighs to feet, soft light",
        "framing": "legs and stockings close-up",
        "filename": "41_impl_legs",
        "group": "sugerente",
        "neg_extra": "full body, face, head",
    },
    "nsfw_impl_collarbone": {
        "label": "Detalle — cuello y clavícula",
        "prompt": "close-up of the neck collarbone and bare shoulder of an adult subject, delicate skin detail, intimate crop, soft directional light",
        "framing": "neck and collarbone close-up",
        "filename": "42_impl_collarbone",
        "group": "sugerente",
        "neg_extra": "full body, legs, feet",
    },
    "nsfw_nude_profile": {
        "label": "Desnudo — perfil completo",
        "prompt": "full body artistic nude, adult subject standing in full side profile, elegant posture, entire body visible from head to feet, no cropping, sculptural studio lighting",
        "framing": "full body nude, side profile",
        "filename": "43_nude_profile",
        "group": "artistico",
        "neg_extra": "cropped legs, feet out of frame, cut off feet",
    },
    "nsfw_nude_high_angle": {
        "label": "Desnudo — picado (tumbada)",
        "prompt": "artistic nude, high camera angle looking down at an adult subject lying gracefully on draped fabric, elegant pose, whole figure visible, soft light",
        "framing": "high angle nude, lying",
        "filename": "44_nude_high_angle",
        "group": "artistico",
        "ratio": "3:2",  # figura tumbada vista desde arriba → horizontal
    },
    "nsfw_nude_seated_back": {
        "label": "Desnudo — sentada de espaldas",
        "prompt": "artistic nude, adult subject seated on the floor with the back to the camera, spine curve and shoulders visible, whole figure visible, sculptural light",
        "framing": "seated nude, back view",
        "filename": "45_nude_seated_back",
        "group": "artistico",
    },
    "nsfw_nude_hug_knees": {
        "label": "Desnudo — abrazando las rodillas",
        "prompt": "artistic nude, adult subject seated hugging the knees to the chest, modest compact pose, whole figure visible, soft window light",
        "framing": "nude hugging knees",
        "filename": "46_nude_hug_knees",
        "group": "artistico",
    },
    "nsfw_nude_fabric": {
        "label": "Desnudo — con tela al vuelo",
        "prompt": "artistic nude, adult subject with flowing sheer fabric partially draped across the body, sense of motion and grace, studio lighting",
        "framing": "nude with flowing fabric",
        "filename": "47_nude_fabric",
        "group": "artistico",
    },
    "nsfw_nude_blinds": {
        "label": "Desnudo — sombras de persiana",
        "prompt": "artistic nude, adult subject with venetian blind shadow stripes across the skin, film noir mood, dramatic light patterns",
        "framing": "nude with blind shadows",
        "filename": "48_nude_blinds",
        "group": "artistico",
    },
    "nsfw_nude_milk_bath": {
        "label": "Baño de leche (flores)",
        "prompt": "artistic nude, adult subject in a milk bath with flower petals floating on the surface, shoulders and knees above the milk, dreamy aesthetic, soft light",
        "framing": "milk bath with petals",
        "filename": "49_nude_milk_bath",
        "group": "artistico",
        "ratio": "3:2",  # bañera → horizontal
    },
    "nsfw_nude_back_detail": {
        "label": "Desnudo — detalle de espalda",
        "prompt": "artistic nude close-up of the bare back and lumbar curve of an adult subject, skin texture and light interplay, fine art crop",
        "framing": "bare back close-up",
        "filename": "50_nude_back_detail",
        "group": "artistico",
        "neg_extra": "full body, face, head, legs, feet",
    },
}

NSFW_ANGLE_GROUPS = {
    "lenceria": "Lencería / Boudoir",
    "sugerente": "Sugerente (implied)",
    "artistico": "Desnudo artístico",
}

NSFW_DEFAULT_ANGLE_SET = list(NSFW_ANGLES.keys())
# Equilibrado NSFW: identidad primero — lencería completa (la ropa varía,
# la cara/cuerpo se aprenden) + implied suaves + 4 desnudos artísticos de
# control. Los más explícitos se dejan a elección manual.
NSFW_BALANCED_ANGLE_SET = [
    "nsfw_lenc_full_front", "nsfw_lenc_full_back", "nsfw_lenc_34",
    "nsfw_lenc_profile", "nsfw_lenc_bust", "nsfw_lenc_bust_34",
    "nsfw_lenc_seated_bed", "nsfw_lenc_lying_bed",
    "nsfw_lenc_white", "nsfw_lenc_red_satin", "nsfw_lenc_bodysuit",
    "nsfw_lenc_stockings", "nsfw_lenc_open_shirt", "nsfw_lenc_towel",
    "nsfw_impl_sheet", "nsfw_impl_back_bare", "nsfw_impl_hands_cover",
    "nsfw_impl_silhouette", "nsfw_impl_over_shoulder", "nsfw_impl_bath",
    "nsfw_nude_standing", "nsfw_nude_back", "nsfw_nude_seated",
    "nsfw_nude_window",
]

# Ficha: como la de Personaje pero SIN ropa fija (el vestuario va por toma)
# y con un campo de detalles del cuerpo para la coherencia entre imágenes.
NSFW_FORM_FIELDS = [
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
    {"key": "cuerpo_detalle", "label": "Cuerpo (detalles de coherencia)", "type": "entry",
     "placeholder": "ej: tatuaje en la cadera, lunar en el hombro, pecho medio..."},
]

NSFW_STYLES = {
    "Fotorrealista": "photorealistic, professional boudoir photography, sharp focus, detailed skin texture, 85mm lens",
    "Anime": "anime style, clean lineart, cel shading, high quality anime illustration",
    "Ilustración digital": "digital illustration, painterly style, detailed character art",
    "Render 3D": "3D render, octane render, subsurface scattering, high poly character model",
}

NSFW_STYLES_NATURAL = {
    "Fotorrealista": "as a photorealistic professional boudoir photograph, sharp focus, natural detailed skin texture, shot on an 85mm lens",
    "Anime": "in a clean, high-quality anime illustration style with crisp linework and cel shading",
    "Ilustración digital": "as a detailed digital painting with painterly brushwork",
    "Render 3D": "rendered as a polished 3D CGI character with soft stylized shading, like a modern animated film",
}

# Negative fijo: el de Personaje (sin las cláusulas de ropa, que aquí varía
# por toma) + BLOQUEO DURO de menores en todas las imágenes + anti-extra
# de anatomía típica NSFW.
NSFW_NEGATIVE_PROMPT = (
    "child, teen, teenager, underage, minor, childlike features, young face, "
    "multiple people, two persons, deformed face, asymmetric eyes, extra fingers, "
    "extra limbs, missing limbs, bad anatomy, bad hands, deformed body, "
    "blurry, lowres, jpeg artifacts, watermark, text, logo, signature, "
    "cropped head, out of frame, different hairstyle, inconsistent face, "
    "busy background, cluttered background, "
    + AVATAR_NEGATIVE_MANOS + ", " + AVATAR_NEGATIVE_MARCA_AGUA
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
        "styles_natural": AVATAR_STYLES_NATURAL,
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
        "styles_natural": LANDSCAPE_STYLES_NATURAL,
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
        "styles_natural": OBJECT_STYLES_NATURAL,
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
        "styles_natural": STYLE_STYLES_NATURAL,
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
    "NSFW": {
        "icon": "🔞",
        "angles": NSFW_ANGLES,
        "angle_groups": NSFW_ANGLE_GROUPS,
        "default_angles": NSFW_DEFAULT_ANGLE_SET,
        "balanced_angles": NSFW_BALANCED_ANGLE_SET,
        "form_fields": NSFW_FORM_FIELDS,
        "styles": NSFW_STYLES,
        "styles_natural": NSFW_STYLES_NATURAL,
        # Sin selector de fondos: el escenario (cama, ducha, estudio) va
        # embebido en cada toma y un fondo global chocaría con él.
        "backgrounds": None,
        "backgrounds_rotacion": None,
        "negative": NSFW_NEGATIVE_PROMPT,
        # La luz también va por toma (claroscuro, ventana, contraluz).
        "lighting": "",
        "label_form": "Ficha del personaje (adulto 18+)",
        "label_angles": "Tomas del dataset",
        "label_trigger": "Trigger word (LoRA)",
        "placeholder_trigger": "ej: ohwx_ana_nsfw",
        "tiene_ficha_auto": True,
        "tiene_imagen_ref": True,
    },
}
