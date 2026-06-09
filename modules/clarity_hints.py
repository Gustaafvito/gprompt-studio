"""Sugerencias de claridad para palabras españolas polisémicas.

Detecta palabras del español con varios significados posibles que
podrían confundir al LLM (y por tanto al modelo de imagen). Surgió
del problema con "pulso" en sesión 18: el reto "duelo de pulsos"
se generó como pelea genérica en vez de arm wrestling porque el LLM
eligió la interpretación equivocada.

Uso:
    >>> from modules.clarity_hints import detect_ambiguous
    >>> ambiguities = detect_ambiguous("Un duelo de pulsos épico")
    >>> ambiguities[0]["word"]
    'pulso'

Para extender: añadir entradas a AMBIGUOUS_WORDS con la palabra en
minúsculas como clave. El detector hace match por palabra completa
(word boundaries), case-insensitive.
"""
import re

# Diccionario de palabras polisémicas relevantes para generación de
# imágenes. Cada entrada tiene:
#   - meanings: lista de interpretaciones posibles (en inglés para que
#     coincida con el vocabulario que el LLM usa internamente).
#   - hint: sugerencia concreta de reformulación para el usuario.
#
# Criterio de inclusión: la palabra DEBE tener ≥2 significados
# visualmente distintos. No se incluyen polisemias que producen la
# misma imagen (ej. "casa" = vivienda/familia → misma imagen).
AMBIGUOUS_WORDS: dict[str, dict] = {
    "pulso": {
        "meanings": ["arm wrestling (echar un pulso)", "heartbeat (latido)", "steady hand (mano firme)"],
        "hint": (
            "¿Quieres un PULSO (arm wrestling): dos personajes con los "
            "codos sobre una superficie y las manos agarradas? "
            "Especifícalo o el LLM puede interpretar 'pulso' como "
            "pelea genérica o latido."
        ),
    },
    "muñeca": {
        "meanings": ["doll (juguete)", "wrist (parte del cuerpo)"],
        "hint": (
            "'Muñeca' puede ser un juguete (doll) o la articulación "
            "(wrist). Aclara cuál quieres."
        ),
    },
    "vela": {
        "meanings": ["candle (de cera)", "sail (de barco)", "vigil (velatorio)"],
        "hint": (
            "'Vela' puede ser una vela de cera (candle), una vela de "
            "barco (sail) o un velatorio (vigil). Especifica."
        ),
    },
    "pluma": {
        "meanings": ["feather (de ave)", "pen (de escribir)", "fountain pen nib"],
        "hint": (
            "'Pluma' puede ser una pluma de ave (feather) o un "
            "instrumento de escritura (pen). Especifica."
        ),
    },
    "silla": {
        "meanings": ["chair (mueble)", "saddle (de montar caballo)"],
        "hint": (
            "'Silla' puede ser un mueble (chair) o una montura "
            "(saddle, de caballo). Especifica."
        ),
    },
    "gato": {
        "meanings": ["cat (animal)", "car jack (herramienta)"],
        "hint": (
            "'Gato' puede ser el animal (cat) o la herramienta para "
            "levantar coches (car jack). Especifica el contexto."
        ),
    },
    "llave": {
        "meanings": ["key (de puerta)", "wrench (herramienta)", "faucet (grifo)"],
        "hint": (
            "'Llave' puede ser una llave de puerta (key), una "
            "herramienta (wrench/spanner) o un grifo (faucet). "
            "Especifica."
        ),
    },
    "planta": {
        "meanings": ["plant (vegetal)", "floor (piso del edificio)", "foot sole (planta del pie)"],
        "hint": (
            "'Planta' puede ser un vegetal (plant), un piso de edificio "
            "(floor) o la planta del pie (foot sole). Especifica."
        ),
    },
    "manga": {
        "meanings": ["sleeve (de camisa)", "Japanese comic (manga style)"],
        "hint": (
            "'Manga' puede ser la manga de una camisa (sleeve) o el "
            "estilo japonés de cómic (manga). Especifica."
        ),
    },
    "carta": {
        "meanings": ["letter (correspondencia)", "playing card (de juego)", "menu (de restaurante)"],
        "hint": (
            "'Carta' puede ser una carta de correspondencia (letter), "
            "una carta de juego (playing card) o el menú de un "
            "restaurante (menu). Especifica."
        ),
    },
    "banco": {
        "meanings": ["bank building (edificio)", "bench (asiento)", "school of fish (banco de peces)"],
        "hint": (
            "'Banco' puede ser un edificio (bank), un asiento (bench) "
            "o un grupo de peces (school of fish). Especifica."
        ),
    },
    "caballo": {
        "meanings": ["horse (animal)", "knight (pieza de ajedrez)", "pommel horse (gimnasia)"],
        "hint": (
            "'Caballo' puede ser el animal (horse), una pieza de "
            "ajedrez (knight) o el potro de gimnasia (pommel horse). "
            "Especifica."
        ),
    },
    "torre": {
        "meanings": ["tower (edificio)", "rook (pieza de ajedrez)"],
        "hint": (
            "'Torre' puede ser una construcción (tower) o una pieza "
            "de ajedrez (rook). Especifica el contexto."
        ),
    },
    "rey": {
        "meanings": ["king (monarca)", "king (pieza de ajedrez)", "king-size (tamaño)"],
        "hint": (
            "'Rey' puede ser un monarca (king person) o una pieza de "
            "ajedrez (king piece). Para evitar ambigüedad, especifica."
        ),
    },
}


# Plurales irregulares en español que NO siguen el patrón "+s".
# Para los regulares (vela→velas, pulso→pulsos, muñeca→muñecas...)
# usamos la regex `\bword(s)?\b` directamente.
PLURALES_IRREGULARES = {
    "rey": ["reyes"],
}


def detect_ambiguous(texto: str) -> list[dict]:
    """Devuelve lista de palabras polisémicas detectadas en `texto`.

    Cada elemento es un dict con:
      - word: la palabra en minúsculas (forma singular)
      - meanings: lista de interpretaciones
      - hint: sugerencia de reformulación

    Match case-insensitive por palabra completa (\\b). Detecta singular
    Y plural regular ("+s"). Plurales irregulares (rey→reyes) están
    en PLURALES_IRREGULARES. Acentos respetados (NO normaliza tildes).
    """
    if not texto:
        return []
    texto_lower = texto.lower()
    hallazgos = []
    for palabra, data in AMBIGUOUS_WORDS.items():
        # Construir patrón que cubra singular + plural regular y, si
        # aplica, plural irregular.
        variantes = [re.escape(palabra) + "s?"]
        for plural in PLURALES_IRREGULARES.get(palabra, []):
            variantes.append(re.escape(plural))
        patron = rf"\b({'|'.join(variantes)})\b"
        if re.search(patron, texto_lower):
            hallazgos.append({"word": palabra, **data})
    return hallazgos
