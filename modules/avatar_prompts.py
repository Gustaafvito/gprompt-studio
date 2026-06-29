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
    AVATAR_NEGATIVE_ANTIZOOM_CUERPO,
    AVATAR_NEGATIVE_CROP_BUSTO,
    AVATAR_NEGATIVE_CROP_CARA,
    AVATAR_NEGATIVE_EDIT_ROTACION,
    AVATAR_NEGATIVE_PROMPT,
)

# Pistas de que un ángulo EXIGE girar la cabeza/cuerpo respecto a un frontal.
# En el modo edición (img2img) estas tomas son las que el modelo de
# referencia tiende a dejar frontales como la imagen base; las empujamos
# con un prompt más fuerte y un negative anti-frontal.
_ROTACION_CUES = ("three-quarter", "profile", "back view", "over the shoulder")

# Aspect ratio SUGERIDO por plano (para el flujo con Z-Image y similares).
# Se infiere del encuadre, igual que requiere_rotacion. Un ángulo puede llevar
# un campo "ratio" explícito que tiene prioridad sobre la inferencia.
#   9:16 vertical  → cuerpo entero, figuras de pie, torres/castillos verticales.
#   1:1  cuadrado  → retratos cerrados, primeros planos, detalle, still life.
#   3:2  horizontal→ paisajes/escenas abiertas, batallas, composiciones abstractas.
_RATIO_VERTICAL_CUES = (
    "full body", "full length", "head to feet", "standing", "cowboy",
    "walking", "hands on hips", "hands in pockets", "arms crossed",
    "castle", "fortress", "tower",
)
_RATIO_SQUARE_CUES = (
    # OJO: nada de "eye" (matchea "bird's eye"/"worm's eye") ni "texture"
    # (matchea "colors and textures"); esos plano son horizontales. Para el
    # ojo humano de la pestaña Estilo se usa "close-up", que sí encaja.
    "close-up", "headshot", "portrait", "macro", "still life", "bust",
    "upper body", "detail", "pattern", "hands", "logo",
    "flowers", "feature", "centered",
)
_RATIO_HORIZONTAL_CUES = (
    "landscape", "panoramic", "panorama", "aerial", "wide", "vista", "horizon",
    "scene", "abstract", "action", "battle", "market", "skyline",
    "mountain", "ocean", "forest", "group of people", "sky",
)


def ratio_sugerido(angulo: dict) -> str:
    """Aspect ratio recomendado para el plano (1:1, 9:16 o 3:2).

    Prioridad: campo explícito "ratio" del ángulo > vertical (cuerpo entero/
    torres) > cuadrado (retrato/detalle) > horizontal (escena/paisaje). Por
    defecto 1:1 (el más seguro para sujetos centrados)."""
    explicito = angulo.get("ratio")
    if explicito:
        return explicito
    texto = (angulo.get("framing", "") + " " + angulo.get("prompt", "")).lower()
    if any(c in texto for c in _RATIO_VERTICAL_CUES):
        return "9:16"
    if any(c in texto for c in _RATIO_SQUARE_CUES):
        return "1:1"
    if any(c in texto for c in _RATIO_HORIZONTAL_CUES):
        return "3:2"
    return "1:1"


def requiere_rotacion(angulo: dict) -> bool:
    """True si la toma necesita una orientación distinta a la frontal.

    Cubre 3/4, perfiles, espalda y el over-the-shoulder. Los frontales,
    expresiones, picado/contrapicado, cowboy y sentada NO rotan la cabeza."""
    texto = (angulo.get("framing", "") + " " + angulo.get("prompt", "")).lower()
    return any(cue in texto for cue in _ROTACION_CUES)


def desc_para_angulo(desc: str, angulo: dict) -> str:
    """Para primeros planos, quita la ropa (', wearing ...') de la descripción.

    En un headshot la ropa de cuerpo (falda, botas) no se ve pero hace que el
    modelo se aleje para mostrarla. La identidad (cara, pelo, ojos, rasgos,
    complexión) se mantiene IDÉNTICA en todas las tomas; solo en los primeros
    planos se omite la ropa. Las tomas de busto y cuerpo conservan la ropa
    completa (ahí sí se ve y debe ser consistente)."""
    if angulo.get("prompt", "").startswith("close-up headshot"):
        import re as _re
        m = _re.search(r",?\s+wearing\b", desc, _re.IGNORECASE)
        if m:
            return desc[:m.start()].rstrip(" ,.")
    return desc


def fondo_para_indice(fondo, i: int) -> str:
    """Devuelve el fondo de la imagen i del dataset.

    `fondo` puede ser:
      - str: el mismo fondo en todo el dataset (comportamiento clásico).
      - list/tuple: fondos a ROTAR. Se asigna por índice (i % n) para
        repartirlos de forma uniforme y, sobre todo, DECORRELACIONARLOS de la
        pose — así el LoRA no aprende "frontal = gris". (Guía SeaArt: máx. 3-6
        imágenes por fondo.) Devuelve "" si no hay fondo."""
    if isinstance(fondo, (list, tuple)):
        fondos = [f for f in fondo if f]
        if not fondos:
            return ""
        return fondos[i % len(fondos)]
    return fondo or ""


def negativo_para_angulo(angulo: dict, incluir_negative: bool = True) -> str:
    """Negative del ángulo: base + términos de recorte según el encuadre.

    Para primeros planos (cara/expresión) y planos de busto añade el cuerpo al
    negative, porque la ropa de cuerpo de la descripción hace que el modelo se
    aleje pese al 'close-up' del positivo. Las tomas de cuerpo entero (cowboy,
    sentada, acción) hacen lo CONTRARIO: añaden el primer plano al negative para
    empujar al modelo a alejarse y mostrar el cuerpo (muchos modelos de
    personaje tienden a hacer zoom a la cara aunque pidas 'full body')."""
    if not incluir_negative:
        return ""
    prompt = angulo.get("prompt", "")
    if prompt.startswith("close-up headshot"):
        return AVATAR_NEGATIVE_PROMPT + ", " + AVATAR_NEGATIVE_CROP_CARA
    if prompt.startswith("upper body"):
        return AVATAR_NEGATIVE_PROMPT + ", " + AVATAR_NEGATIVE_CROP_BUSTO
    return AVATAR_NEGATIVE_PROMPT + ", " + AVATAR_NEGATIVE_ANTIZOOM_CUERPO

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


def _claves_ficha_validas() -> set:
    """Claves aceptadas en la ficha: 'trigger' + TODOS los campos de formulario
    de TODOS los tipos de LoRA (Personaje/Paisaje/Objeto/Estilo). Así el parser
    no descarta los campos de un tipo que no sea Personaje (bug histórico)."""
    claves = {"trigger"}
    try:
        from modules.avatar_config import LORA_TYPES
        for cfg in LORA_TYPES.values():
            for campo in cfg.get("form_fields", []):
                if campo.get("key"):
                    claves.add(campo["key"])
    except Exception:
        # Fallback al set de Personaje si algo falla en el import.
        claves |= {"genero", "edad", "etnia_piel", "pelo", "ojos",
                   "rasgos", "complexion", "ropa"}
    return claves


def parsear_ficha_json(respuesta: str, claves_validas: set | None = None) -> dict:
    """Extrae la ficha del JSON de la respuesta del LLM.

    Devuelve {} si no hay JSON parseable. Filtra a las claves conocidas del
    formulario (+trigger, de TODOS los tipos) y descarta vacíos o no escalares.
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
    claves = claves_validas if claves_validas is not None else _claves_ficha_validas()
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
    fondo,
    incluir_negative: bool = True,
) -> list:
    """Devuelve la lista de prompts del dataset.

    `fondo` puede ser un str (mismo fondo en todo el dataset) o una lista de
    fondos a rotar por imagen (ver fondo_para_indice).

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

    for i, key in enumerate(angulos_seleccionados):
        angulo = AVATAR_ANGLES.get(key)
        if not angulo:
            continue

        # Fondo de ESTA imagen: rota si `fondo` es una lista (consistencia LoRA).
        fondo_i = fondo_para_indice(fondo, i)

        # El ENCUADRE va justo tras el trigger, ANTES de la descripción. Si la
        # descripción (con ropa de cuerpo entero: medias, botas...) va primero,
        # el modelo intenta mostrarla y se aleja a plano entero, ignorando el
        # "close-up". Liderar con el tipo de plano fuerza el recorte correcto.
        # Además, en primeros planos se omite la ropa de la descripción (ver
        # desc_para_angulo) para que el modelo recorte de verdad a la cara.
        desc_ang = desc_para_angulo(desc, angulo)
        partes = [trigger, angulo["prompt"], desc_ang, fondo_i, AVATAR_LIGHTING]
        if estilo_sufijo:
            partes.append(estilo_sufijo)
        prompt = ", ".join(p for p in partes if p)

        # Caption kohya: trigger + encuadre + fondo + iluminación.
        # GUÍA OFICIAL SeaArt (datasets LoRA): la caption debe incluir lo
        # que el LoRA NO debe absorber (fondo, iluminación, pose) — si el
        # fondo no se etiqueta, el LoRA lo "pega" al personaje. La
        # identidad NO se describe: la absorbe el trigger word.
        partes_caption = [trigger, angulo["framing"]]
        if fondo_i:
            partes_caption.append(fondo_i.split(",")[0].strip())
        partes_caption.append(AVATAR_LIGHTING.split(",")[0].strip())
        caption = ", ".join(partes_caption)

        dataset.append({
            "angle_key": key,
            "label": angulo["label"],
            "filename": angulo["filename"],
            "prompt": prompt,
            "negative": negativo_para_angulo(angulo, incluir_negative),
            "caption": caption,
            "ratio": ratio_sugerido(angulo),
        })

    return dataset


# ---------------------------------------------------------------------------
# SYSTEM PROMPTS Y CONSTRUCTORES PARA TIPOS NO-PERSONAJE
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_PAISAJE_CANONICO = """Eres un experto en prompts para generación de imágenes con IA, especializado en CONSISTENCIA DE ESCENA para datasets de entrenamiento LoRA de paisaje.

Tu tarea: convertir la ficha de paisaje que recibirás en UNA ÚNICA descripción canónica en INGLÉS.

REGLAS ESTRICTAS:
1. Salida: SOLO la descripción, en una sola línea, sin comillas, sin preámbulo, sin explicaciones, sin markdown.
2. Idioma de salida: inglés. La ficha llega en español.
3. Longitud: entre 30 y 60 palabras. Compacta pero concreta.
4. Estructura fija: tipo de paisaje → ubicación/región → elementos característicos → paleta de colores → estación.
5. PROHIBIDO: hora del día, clima, ángulos de cámara, encuadres, iluminación concreta, personas. Eso se añade por código.
6. Usa descripciones geográficas y visuales concretas y verificables.
7. La descripción debe repetirse idéntica en todos los prompts del dataset.

EJEMPLO DE SALIDA VÁLIDA:
a dramatic mountain landscape in Patagonia, jagged granite peaks with snow caps, turquoise glacial lakes, sparse lenga beech forest, ochre and emerald color palette, autumn season"""


def construir_user_prompt_paisaje(form_data: dict) -> str:
    etiquetas = {
        "tipo_paisaje": "Tipo de paisaje",
        "pais_region": "País / Región",
        "epoca": "Estación",
        "elementos": "Elementos característicos",
        "paleta": "Paleta de colores",
        "estilo_foto": "Estilo fotográfico",
    }
    lineas = ["FICHA DEL PAISAJE:"]
    for key, etiqueta in etiquetas.items():
        valor = (form_data.get(key) or "").strip()
        if valor:
            lineas.append(f"- {etiqueta}: {valor}")
    lineas.append("\nGenera la descripción canónica del paisaje.")
    return "\n".join(lineas)


SYSTEM_PROMPT_OBJETO_CANONICO = """Eres un experto en prompts para generación de imágenes con IA, especializado en CONSISTENCIA DE OBJETO para datasets de entrenamiento LoRA de producto/objeto.

Tu tarea: convertir la ficha del objeto que recibirás en UNA ÚNICA descripción canónica en INGLÉS.

REGLAS ESTRICTAS:
1. Salida: SOLO la descripción, en una sola línea, sin comillas, sin preámbulo, sin explicaciones, sin markdown.
2. Idioma de salida: inglés. La ficha llega en español.
3. Longitud: entre 25 y 50 palabras. Compacta y descriptiva.
4. Estructura fija: nombre y categoría del objeto → materiales → colores exactos → forma/silueta → rasgos distintivos.
5. PROHIBIDO: ángulos de cámara, encuadres, iluminación, fondo, personas. Eso se añade por código.
6. Usa descripciones físicas concretas y verificables (material + color + detalle).
7. La descripción debe repetirse idéntica en todos los prompts del dataset.

EJEMPLO DE SALIDA VÁLIDA:
a vintage brass pocket watch, polished gold-toned case with engraved floral pattern, white enamel dial with roman numerals, open-face design, worn brown leather chain attachment"""


def construir_user_prompt_objeto(form_data: dict) -> str:
    etiquetas = {
        "nombre_objeto": "Nombre del objeto",
        "categoria": "Categoría",
        "materiales": "Materiales",
        "colores": "Colores",
        "forma": "Forma / silueta",
        "rasgos_distintos": "Rasgos distintivos",
    }
    lineas = ["FICHA DEL OBJETO:"]
    for key, etiqueta in etiquetas.items():
        valor = (form_data.get(key) or "").strip()
        if valor:
            lineas.append(f"- {etiqueta}: {valor}")
    lineas.append("\nGenera la descripción canónica del objeto.")
    return "\n".join(lineas)


SYSTEM_PROMPT_ESTILO_CANONICO = """Eres un experto en prompts para generación de imágenes con IA, especializado en CONSISTENCIA DE ESTILO para datasets de entrenamiento LoRA de estilo artístico.

Tu tarea: convertir la ficha de estilo que recibirás en UNA ÚNICA descripción de estilo en INGLÉS para usar como sufijo en todos los prompts del dataset.

REGLAS ESTRICTAS:
1. Salida: SOLO el sufijo de estilo, en una sola línea, sin comillas, sin preámbulo, sin explicaciones, sin markdown.
2. Idioma de salida: inglés. La ficha llega en español.
3. Longitud: entre 20 y 45 palabras. Lista de descriptores de estilo separados por comas.
4. Debe describir CÓMO se ve, no QUÉ se ve: técnica, trazo, paleta, textura, atmósfera.
5. PROHIBIDO: describir sujetos, personas, objetos o escenas concretas. Solo el ESTILO.
6. El sufijo se añadirá al final de cada prompt del dataset.

EJEMPLO DE SALIDA VÁLIDA:
in the style of ohwx_moebius, clean precise linework, flat cel shading, muted earth tones with turquoise accents, retro-futurist aesthetic, french bande dessinee comic art style"""


def construir_user_prompt_estilo(form_data: dict) -> str:
    etiquetas = {
        "nombre_estilo": "Nombre / descripción del estilo",
        "artista_ref": "Artista o referencia",
        "tecnica": "Técnica principal",
        "paleta": "Paleta de colores",
        "rasgos_estilo": "Rasgos visuales distintivos",
        "epoca": "Época / período",
    }
    lineas = ["FICHA DEL ESTILO:"]
    for key, etiqueta in etiquetas.items():
        valor = (form_data.get(key) or "").strip()
        if valor:
            lineas.append(f"- {etiqueta}: {valor}")
    lineas.append("\nGenera el sufijo de estilo canónico.")
    return "\n".join(lineas)


# Fichas automáticas para tipos no-personaje
SYSTEM_PROMPT_PAISAJE_FICHA = """Eres un diseñador de datasets para LoRA de paisaje.

Tu tarea: inventar UNA ficha de paisaje coherente y devolverla EXCLUSIVAMENTE como un objeto JSON válido.

REGLAS:
1. Salida: SOLO el JSON, sin texto antes ni después, sin markdown.
2. Claves EXACTAS: trigger, tipo_paisaje, pais_region, epoca, elementos, paleta, estilo_foto.
3. trigger: formato ohwx_nombre (minúsculas, sin espacios).
4. tipo_paisaje: uno de [Montaña, Bosque, Playa / Costa, Desierto, Pradera, Ciudad / Urbano, Lago / Río, Valle, Volcán, Tundra / Ártico].
5. epoca: uno de [Primavera, Verano, Otoño, Invierno].
6. Descripciones concretas y visuales.

EJEMPLO:
{"trigger": "ohwx_fjord", "tipo_paisaje": "Lago / Río", "pais_region": "Noruega", "epoca": "Otoño", "elementos": "fiordos profundos, cascadas, abedules dorados, niebla baja sobre el agua", "paleta": "azul acero, dorado, gris piedra", "estilo_foto": "Fotografía naturaleza (National Geographic)"}"""

SYSTEM_PROMPT_OBJETO_FICHA = """Eres un diseñador de datasets para LoRA de objeto/producto.

Tu tarea: inventar UNA ficha de objeto coherente y devolverla EXCLUSIVAMENTE como un objeto JSON válido.

REGLAS:
1. Salida: SOLO el JSON, sin texto antes ni después, sin markdown.
2. Claves EXACTAS: trigger, nombre_objeto, categoria, materiales, colores, forma, rasgos_distintos.
3. trigger: formato ohwx_nombre (minúsculas, sin espacios).
4. Objeto visualmente distintivo y fotogénico.

EJEMPLO:
{"trigger": "ohwx_linterna", "nombre_objeto": "linterna de minero victoriana", "categoria": "Herramienta", "materiales": "hierro forjado oxidado y latón pulido", "colores": "negro óxido con detalles dorados y vidrio ámbar", "forma": "cilíndrica con asa en arco y gancho superior", "rasgos_distintos": "ventilación con patrón de estrellas, llama de aceite visible interior"}"""

SYSTEM_PROMPT_ESTILO_FICHA = """Eres un diseñador de datasets para LoRA de estilo artístico.

Tu tarea: inventar UN estilo artístico coherente y devolverlo EXCLUSIVAMENTE como un objeto JSON válido.

REGLAS:
1. Salida: SOLO el JSON, sin texto antes ni después, sin markdown.
2. Claves EXACTAS: trigger, nombre_estilo, artista_ref, tecnica, paleta, rasgos_estilo, epoca.
3. trigger: formato ohwx_estilo_nombre.
4. Estilo visualmente distintivo y entrenable con LoRA.

EJEMPLO:
{"trigger": "ohwx_estilo_grabado", "nombre_estilo": "grabado en madera xilografía", "artista_ref": "Hokusai", "tecnica": "Grabado / Litografía", "paleta": "negro y blanco con toques de rojo bermellón", "rasgos_estilo": "líneas paralelas de corte manual, texturas rugosas, alto contraste, siluetas planas", "epoca": "Edo japonés, 1800s"}"""


def construir_user_prompt_ficha_tipo(tipo: str, tema: str = "") -> str:
    """Devuelve el user prompt para ficha automática según el tipo de LoRA."""
    tema = (tema or "").strip()
    base = {
        "Paisaje": "Inventa una ficha de paisaje",
        "Objeto": "Inventa una ficha de objeto / producto",
        "Estilo": "Inventa una ficha de estilo artístico",
    }.get(tipo, "Inventa una ficha")
    if tema:
        return f"{base} basado en: {tema}\n\nDevuelve SOLO el JSON."
    return f"{base} original y visualmente interesante.\n\nDevuelve SOLO el JSON."


def system_prompt_ficha_para_tipo(tipo: str) -> str:
    """Devuelve el system prompt de ficha automática según el tipo."""
    return {
        "Paisaje": SYSTEM_PROMPT_PAISAJE_FICHA,
        "Objeto": SYSTEM_PROMPT_OBJETO_FICHA,
        "Estilo": SYSTEM_PROMPT_ESTILO_FICHA,
    }.get(tipo, SYSTEM_PROMPT_AVATAR_FICHA)


def system_prompt_canonico_para_tipo(tipo: str) -> str:
    """Devuelve el system prompt canónico según el tipo de LoRA."""
    return {
        "Personaje": SYSTEM_PROMPT_AVATAR_CANONICO,
        "Paisaje": SYSTEM_PROMPT_PAISAJE_CANONICO,
        "Objeto": SYSTEM_PROMPT_OBJETO_CANONICO,
        "Estilo": SYSTEM_PROMPT_ESTILO_CANONICO,
    }.get(tipo, SYSTEM_PROMPT_AVATAR_CANONICO)


def construir_user_prompt_para_tipo(tipo: str, form_data: dict) -> str:
    """Devuelve el user prompt canónico según el tipo de LoRA."""
    if tipo == "Paisaje":
        return construir_user_prompt_paisaje(form_data)
    if tipo == "Objeto":
        return construir_user_prompt_objeto(form_data)
    if tipo == "Estilo":
        return construir_user_prompt_estilo(form_data)
    return construir_user_prompt_canonico(form_data)


# Términos para excluir personas en ángulos que deben ir SIN gente
# (arquitectura, paisaje, monumentos…). Refuerza el "no people" del positivo,
# que por sí solo el modelo suele ignorar.
_NEG_SIN_PERSONAS = ("person, people, human, man, woman, child, "
                     "figure, crowd, silhouette, portrait, face")


def negativo_generico_para_angulo(angulo: dict, negative_base: str,
                                  incluir_negative: bool = True) -> str:
    """Negative POR ÁNGULO para tipos no-personaje (Estilo/Paisaje/Objeto).

    Parte del negative_base del tipo y añade:
      - exclusión de personas si el ángulo es explícitamente SIN gente (su
        positivo dice 'no people'/'no person') y el base no lo cubre ya. Evita
        que en arquitectura/paisaje/monumentos se cuelen figuras.
      - cualquier 'neg_extra' declarado en el propio ángulo (override manual).
    """
    if not incluir_negative:
        return ""
    base = (negative_base or "").strip().strip(",")
    prompt = (angulo.get("prompt", "") or "").lower()
    partes = [base] if base else []

    sin_personas = ("no people" in prompt or "no person" in prompt)
    ya_excluye = "person" in base.lower() or "people" in base.lower()
    if sin_personas and not ya_excluye:
        partes.append(_NEG_SIN_PERSONAS)

    extra = (angulo.get("neg_extra", "") or "").strip().strip(",")
    if extra:
        partes.append(extra)

    return ", ".join(p for p in partes if p)


def ensamblar_dataset_generico(
    tipo: str,
    trigger_word: str,
    descripcion_canonica: str,
    angulos_seleccionados: list,
    angles_dict: dict,
    estilo_sufijo: str,
    fondo,
    lighting: str,
    negative_base: str,
    incluir_negative: bool = True,
) -> list:
    """Ensambla un dataset para cualquier tipo de LoRA (Paisaje, Objeto, Estilo).

    A diferencia del personaje, no hay lógica de recorte ni de ropa: la
    descripción canónica va entera en cada prompt sin modificar."""
    trigger = trigger_word.strip()
    desc = descripcion_canonica.strip().rstrip(".,")
    dataset = []

    for i, key in enumerate(angulos_seleccionados):
        angulo = angles_dict.get(key)
        if not angulo:
            continue

        fondo_i = fondo_para_indice(fondo, i) if fondo else ""
        partes = [trigger, angulo["prompt"], desc]
        if fondo_i:
            partes.append(fondo_i)
        if lighting:
            partes.append(lighting)
        if estilo_sufijo:
            partes.append(estilo_sufijo)
        prompt = ", ".join(p for p in partes if p)

        partes_caption = [trigger, angulo["framing"]]
        if fondo_i:
            partes_caption.append(fondo_i.split(",")[0].strip())
        if lighting:
            partes_caption.append(lighting.split(",")[0].strip())
        caption = ", ".join(partes_caption)

        negative = negativo_generico_para_angulo(
            angulo, negative_base, incluir_negative)

        dataset.append({
            "angle_key": key,
            "label": angulo["label"],
            "filename": angulo["filename"],
            "prompt": prompt,
            "negative": negative,
            "caption": caption,
            "ratio": ratio_sugerido(angulo),
        })

    return dataset


def ensamblar_dataset_edicion(
    trigger_word: str,
    angulos_seleccionados: list,
    fondo,
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
    for i, key in enumerate(angulos_seleccionados):
        angulo = AVATAR_ANGLES.get(key)
        if not angulo:
            continue
        fondo_i = fondo_para_indice(fondo, i)

        if requiere_rotacion(angulo):
            # Tomas de ÁNGULO: lideramos con la rotación y exigimos un punto de
            # vista NUEVO, porque el modelo de referencia tiende a clavar el
            # frontal de la imagen base. La identidad se mantiene, la
            # orientación NO.
            partes = [
                (f"Rotate the subject to a NEW viewpoint: {angulo['prompt']}. "
                 "This is a DIFFERENT camera angle from the reference image: the "
                 "head and body must be physically turned to present this new "
                 "orientation, not the frontal pose of the reference"),
                ("Keep the SAME person: same face identity, same skin tone, same "
                 "hairstyle, same facial hair, same clothing, only the "
                 "orientation changes"),
            ]
        else:
            # Tomas FRONTALES (incl. expresiones, picado/contrapicado, cowboy,
            # sentada): la pose ya coincide con la referencia, así que clavamos
            # identidad y cambiamos solo cámara/expresión.
            partes = [
                ("Keep the EXACT same person from the reference image: "
                 "same face identity, same hairstyle, same facial hair, "
                 "same clothing"),
                f"Change ONLY the camera and pose to: {angulo['prompt']}",
            ]

        if fondo_i:
            partes.append(f"Background: {fondo_i}")
        partes.append(AVATAR_LIGHTING)
        partes.append("Preserve photorealistic detail and natural skin texture")
        prompt = ". ".join(partes) + "."

        # Negative: el base por encuadre + el anti-frontal SOLO en tomas de
        # ángulo (empuja a girar la cabeza venciendo el ancla de la referencia).
        negative = negativo_para_angulo(angulo, incluir_negative)
        if incluir_negative and requiere_rotacion(angulo):
            negative = (negative + ", " + AVATAR_NEGATIVE_EDIT_ROTACION
                        if negative else AVATAR_NEGATIVE_EDIT_ROTACION)

        # La caption de entrenamiento es la misma que en el modo texto
        partes_caption = [trigger, angulo["framing"]]
        if fondo_i:
            partes_caption.append(fondo_i.split(",")[0].strip())
        partes_caption.append(AVATAR_LIGHTING.split(",")[0].strip())

        dataset.append({
            "angle_key": key,
            "label": angulo["label"],
            "filename": angulo["filename"],
            "prompt": prompt,
            "negative": negative,
            "caption": ", ".join(partes_caption),
            "ratio": ratio_sugerido(angulo),
        })
    return dataset
