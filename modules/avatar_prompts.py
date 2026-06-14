"""
AVATAR_PROMPTS — System prompts y ensamblado del dataset
========================================================
Filosofía del módulo:
  FASE 1 (LLM): el LLM convierte el formulario en UNA descripción canónica
                cerrada del personaje, en inglés, sin sinónimos ni adornos.
  FASE 2 (Python): el ensamblado de los N prompts del dataset es 100%
                programático. El LLM NO interviene por ángulo, así la
                identidad del personaje es idéntica en todas las imágenes.

NOTA PARA INTEGRACIÓN (Claude Code):
- SYSTEM_PROMPT_AVATAR_CANONICO sigue el mismo patrón que los system
  prompts de prompts.py (instrucciones estrictas + formato de salida).
"""

from modules.avatar_config import (
    AVATAR_ANGLES,
    AVATAR_LIGHTING,
    AVATAR_NEGATIVE_CROP_BUSTO,
    AVATAR_NEGATIVE_CROP_CARA,
    AVATAR_NEGATIVE_PROMPT,
)


def negativo_para_angulo(angulo: dict, incluir_negative: bool = True) -> str:
    """Negative del ángulo: base + términos de recorte según el encuadre.

    Para primeros planos (cara/expresión) y planos de busto añade el cuerpo al
    negative, porque la ropa de cuerpo de la descripción hace que el modelo se
    aleje pese al 'close-up' del positivo. Cuerpo entero/cowboy/sentada usan
    solo el negative base (ahí sí queremos ver el cuerpo)."""
    if not incluir_negative:
        return ""
    prompt = angulo.get("prompt", "")
    if prompt.startswith("close-up headshot"):
        return AVATAR_NEGATIVE_PROMPT + ", " + AVATAR_NEGATIVE_CROP_CARA
    if prompt.startswith("upper body"):
        return AVATAR_NEGATIVE_PROMPT + ", " + AVATAR_NEGATIVE_CROP_BUSTO
    return AVATAR_NEGATIVE_PROMPT

# ---------------------------------------------------------------------------
# FASE 1 — SYSTEM PROMPT: descripción canónica del personaje
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_AVATAR_CANONICO = """Eres un experto en prompts para generación de imágenes con IA, especializado en CONSISTENCIA DE PERSONAJE para datasets de entrenamiento LoRA.

Tu tarea: convertir la ficha de personaje que recibirás en UNA ÚNICA descripción canónica en INGLÉS.

REGLAS ESTRICTAS:
1. Salida: SOLO la descripción, en una sola línea, sin comillas, sin preámbulo, sin explicaciones, sin markdown.
2. Idioma de salida: inglés. La ficha llega en español.
3. Longitud: entre 40 y 70 palabras. Compacta pero completa.
4. Estructura fija y en este orden: edad y género → rasgos faciales (cara, ojos, pelo) → rasgos distintivos → complexión → ropa exacta.
5. PROHIBIDO: lenguaje cinematográfico, ángulos de cámara, encuadres, iluminación, fondos, estilo artístico, emociones o poses. Eso se añade después por código.
6. PROHIBIDO: sinónimos ambiguos o adjetivos subjetivos vagos ("beautiful", "stunning"). Usa descripciones físicas concretas y verificables.
7. La descripción debe poder repetirse palabra por palabra en todos los prompts del dataset manteniendo la identidad exacta del personaje.
8. La ropa debe describirse de forma exacta y cerrada (color + prenda + detalle), porque será idéntica en todo el dataset.

EJEMPLO DE SALIDA VÁLIDA:
a 28 year old woman with fair mediterranean skin, oval face, large almond-shaped green eyes, wavy chestnut brown shoulder-length hair with side part, light freckles across the nose, slim athletic build, wearing a plain white crew-neck t-shirt and blue denim jeans"""


def construir_user_prompt_canonico(form_data: dict) -> str:
    """Convierte el dict del formulario en el mensaje de usuario para el LLM.

    form_data: {key_del_campo: valor_introducido} según AVATAR_FORM_FIELDS.
    """
    etiquetas = {
        "genero": "Género",
        "edad": "Edad aparente",
        "etnia_piel": "Tono de piel / etnia",
        "pelo": "Pelo",
        "ojos": "Ojos",
        "rasgos": "Rasgos distintivos",
        "complexion": "Complexión",
        "ropa": "Ropa",
    }
    lineas = ["FICHA DEL PERSONAJE:"]
    for key, etiqueta in etiquetas.items():
        valor = (form_data.get(key) or "").strip()
        if valor:
            lineas.append(f"- {etiqueta}: {valor}")
    lineas.append("\nGenera la descripción canónica.")
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# FICHA AUTOMÁTICA — el LLM inventa el personaje y rellena el formulario
# (sesión 19 round 10, petición del usuario)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_AVATAR_FICHA = """Eres un diseñador de personajes para datasets de entrenamiento LoRA.

Tu tarea: inventar UNA ficha de personaje coherente y devolverla EXCLUSIVAMENTE como un objeto JSON válido.

REGLAS ESTRICTAS:
1. Salida: SOLO el JSON, sin texto antes ni después, sin markdown ni ```.
2. Claves EXACTAS del JSON: trigger, genero, edad, etnia_piel, pelo, ojos, rasgos, complexion, ropa.
3. Valores en ESPAÑOL, salvo "trigger": formato ohwx_nombre (minúsculas, sin espacios, ej. "ohwx_vera").
4. Valores cerrados obligatorios:
   - genero: uno de [Mujer, Hombre, Andrógino]
   - edad: uno de [18-25, 25-35, 35-45, 45-60, 60+]
   - complexion: uno de [Delgada, Atlética, Media, Robusta, Curvy]
5. Descripciones físicas CONCRETAS y verificables (color + forma + detalle), nada de adjetivos vagos tipo "bonito".
6. La ropa debe ser cerrada y exacta (color + prenda + detalle) — será idéntica en todo el dataset.
7. Personaje visualmente distintivo pero realista de generar con IA.

EJEMPLO DE SALIDA VÁLIDA:
{"trigger": "ohwx_vera", "genero": "Mujer", "edad": "25-35", "etnia_piel": "piel morena con subtono cálido", "pelo": "melena negra lisa hasta la cintura con flequillo recto", "ojos": "ojos marrón oscuro grandes y rasgados", "rasgos": "lunar bajo el ojo izquierdo, pendientes de aro dorados", "complexion": "Atlética", "ropa": "chaqueta bomber verde oliva sobre camiseta negra lisa y vaqueros negros"}"""


PROMPT_VISION_FICHA = """Analiza a la PERSONA o PERSONAJE de esta imagen y devuelve su ficha EXCLUSIVAMENTE como un objeto JSON válido.

REGLAS ESTRICTAS:
1. Salida: SOLO el JSON, sin texto antes ni después, sin markdown ni ```.
2. Claves EXACTAS: trigger, genero, edad, etnia_piel, pelo, ojos, rasgos, complexion, ropa.
3. Valores en ESPAÑOL, salvo "trigger": inventa uno en formato ohwx_nombre (minúsculas, sin espacios).
4. Valores cerrados obligatorios:
   - genero: uno de [Mujer, Hombre, Andrógino]
   - edad: uno de [18-25, 25-35, 35-45, 45-60, 60+] (edad APARENTE)
   - complexion: uno de [Delgada, Atlética, Media, Robusta, Curvy]
5. Describe SOLO lo que VES: piel, cara, ojos, pelo, rasgos distintivos (cicatrices, pecas, gafas, tatuajes, joyas) y la ropa EXACTA (color + prenda + detalle).
6. Sé concreto y verificable — nada de adjetivos vagos. La ficha se usará para recrear a esta persona de forma idéntica en varios ángulos distintos.
7. NO describas el fondo, la iluminación ni el encuadre de la foto.

EJEMPLO DE SALIDA VÁLIDA:
{"trigger": "ohwx_valquiria", "genero": "Mujer", "edad": "25-35", "etnia_piel": "piel pálida con subtono rosado", "pelo": "pelo platino corto rapado a los lados y largo arriba", "ojos": "ojos gris acero almendrados", "rasgos": "cicatriz fina en la ceja derecha, cejas rectas y gruesas", "complexion": "Atlética", "ropa": "armadura de placas cromada brillante con correas negras"}"""


def construir_user_prompt_ficha(tema: str = "") -> str:
    """Mensaje de usuario para la ficha automática. tema opcional."""
    tema = (tema or "").strip()
    if tema:
        return (f"Inventa la ficha de un personaje basado en este "
                f"tema/concepto: {tema}\n\nDevuelve SOLO el JSON.")
    return ("Inventa la ficha de un personaje original aleatorio "
            "(varía género, edad, etnia y estilo).\n\nDevuelve SOLO el JSON.")


def parsear_ficha_json(respuesta: str) -> dict:
    """Extrae la ficha del JSON de la respuesta del LLM.

    Devuelve {} si no hay JSON parseable. Filtra a las claves conocidas
    del formulario (+trigger) y descarta valores vacíos o no escalares.
    """
    import json as _json
    import re as _re

    m = _re.search(r"\{.*\}", respuesta or "", _re.DOTALL)
    if not m:
        return {}
    try:
        datos = _json.loads(m.group(0))
    except Exception:
        return {}
    if not isinstance(datos, dict):
        return {}
    claves = {"trigger", "genero", "edad", "etnia_piel", "pelo", "ojos",
              "rasgos", "complexion", "ropa"}
    ficha = {}
    for k, v in datos.items():
        if k in claves and isinstance(v, (str, int, float)) and str(v).strip():
            ficha[k] = str(v).strip()
    return ficha


# ---------------------------------------------------------------------------
# FASE 2 — ENSAMBLADO PROGRAMÁTICO DEL DATASET
# ---------------------------------------------------------------------------
def ensamblar_dataset(
    trigger_word: str,
    descripcion_canonica: str,
    angulos_seleccionados: list,
    estilo_sufijo: str,
    fondo: str,
    incluir_negative: bool = True,
) -> list:
    """Devuelve la lista de prompts del dataset.

    Cada elemento es un dict:
      {
        "angle_key":  clave del ángulo,
        "label":      etiqueta en español (UI),
        "filename":   nombre de archivo sin extensión,
        "prompt":     prompt positivo completo,
        "negative":   negative prompt (o "" si incluir_negative=False),
        "caption":    caption formato kohya para el entrenamiento,
      }
    """
    trigger = trigger_word.strip()
    desc = descripcion_canonica.strip().rstrip(".,")
    dataset = []

    for key in angulos_seleccionados:
        angulo = AVATAR_ANGLES.get(key)
        if not angulo:
            continue

        # El ENCUADRE va justo tras el trigger, ANTES de la descripción. Si la
        # descripción (con ropa de cuerpo entero: medias, botas...) va primero,
        # el modelo intenta mostrarla y se aleja a plano entero, ignorando el
        # "close-up". Liderar con el tipo de plano fuerza el recorte correcto.
        partes = [trigger, angulo["prompt"], desc, fondo, AVATAR_LIGHTING]
        if estilo_sufijo:
            partes.append(estilo_sufijo)
        prompt = ", ".join(p for p in partes if p)

        # Caption kohya: trigger + encuadre + fondo + iluminación.
        # GUÍA OFICIAL SeaArt (datasets LoRA): la caption debe incluir lo
        # que el LoRA NO debe absorber (fondo, iluminación, pose) — si el
        # fondo no se etiqueta, el LoRA lo "pega" al personaje. La
        # identidad NO se describe: la absorbe el trigger word.
        partes_caption = [trigger, angulo["framing"]]
        if fondo:
            partes_caption.append(fondo.split(",")[0].strip())
        partes_caption.append(AVATAR_LIGHTING.split(",")[0].strip())
        caption = ", ".join(partes_caption)

        dataset.append({
            "angle_key": key,
            "label": angulo["label"],
            "filename": angulo["filename"],
            "prompt": prompt,
            "negative": negativo_para_angulo(angulo, incluir_negative),
            "caption": caption,
        })

    return dataset


def ensamblar_dataset_edicion(
    trigger_word: str,
    angulos_seleccionados: list,
    fondo: str,
    incluir_negative: bool = True,
) -> list:
    """Variante IMG2IMG del dataset: prompts de EDICIÓN por ángulo.

    Para modelos con imagen de sujeto/edición (MAI-Image-2.5, Nano
    Banana, Reve 2.0, SeaArt Film Edit): se sube la imagen de
    referencia como sujeto y cada prompt ordena cambiar SOLO la cámara
    manteniendo la identidad. Sin descripción canónica: la identidad
    la aporta la imagen, no el texto (sesión 19 round 12).
    """
    trigger = trigger_word.strip()
    dataset = []
    for key in angulos_seleccionados:
        angulo = AVATAR_ANGLES.get(key)
        if not angulo:
            continue
        partes = [
            ("Keep the EXACT same person from the reference image: "
             "same face identity, same hairstyle, same facial hair, "
             "same clothing"),
            f"Change ONLY the camera and pose to: {angulo['prompt']}",
        ]
        if fondo:
            partes.append(f"Background: {fondo}")
        partes.append(AVATAR_LIGHTING)
        partes.append("Preserve photorealistic detail and natural skin texture")
        prompt = ". ".join(partes) + "."

        # La caption de entrenamiento es la misma que en el modo texto
        partes_caption = [trigger, angulo["framing"]]
        if fondo:
            partes_caption.append(fondo.split(",")[0].strip())
        partes_caption.append(AVATAR_LIGHTING.split(",")[0].strip())

        dataset.append({
            "angle_key": key,
            "label": angulo["label"],
            "filename": angulo["filename"],
            "prompt": prompt,
            "negative": negativo_para_angulo(angulo, incluir_negative),
            "caption": ", ".join(partes_caption),
        })
    return dataset
