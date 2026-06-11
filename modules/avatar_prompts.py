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
    AVATAR_NEGATIVE_PROMPT,
)

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
7. La descripción debe poder repetirse palabra por palabra en 16 prompts distintos manteniendo la identidad exacta del personaje.
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

        partes = [trigger, desc, angulo["prompt"], fondo, AVATAR_LIGHTING]
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
            "negative": AVATAR_NEGATIVE_PROMPT if incluir_negative else "",
            "caption": caption,
        })

    return dataset
