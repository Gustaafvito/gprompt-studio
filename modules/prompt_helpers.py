"""Helpers puros de manipulación de prompts.

Funciones sin dependencias de widget ni de estado del app. Extraídas
de CoreMixin en sesión 18 siguiendo la guía del docstring de sesión 17
("conviene extraer primero los helpers puros — _parsear_variaciones,
_recortar_si_excede, _extraer_* — a un módulo standalone").

Las funciones equivalentes de CoreMixin (`_parsear_variaciones`,
`_extraer_pos_de_bloque`, `_recortar_si_excede`) ahora delegan en
estos helpers para mantener compat con todos los call sites
`self.app._método()`.

Esto reduce la superficie pura de CoreMixin sin tocar la
arquitectura (CoreMixin sigue siendo la foundation por diseño).
"""
import re

from workers import limpiar_marcadores


def parsear_variaciones(texto: str, n_esperado: int | None = None) -> list[str]:
    """Parser de variaciones generadas por el LLM.

    Reconoce bloques con encabezados tipo "Variación N", "Prompt N",
    "POSITIVE PROMPT:", o separadores `---`.

    `n_esperado`: si se pasa, filtra preámbulos del LLM cuando el
    número de bloques parseados supera N. Prefiere bloques con
    "POSITIVE PROMPT:" / "POSITIVE:"; si no hay suficientes, asume
    que el preámbulo va al principio y se queda con los últimos N.

    Devuelve [] si no consigue parsear ≥2 bloques.
    """
    texto_limpio = re.sub(r"[\*#]", "", texto)
    patron = r"\n\s*(?:Variaci[oó]n|Prompt)?\s*\d+[\.\)\-:]\s*|\n\s*---\s*\n"
    bloques = re.split(patron, "\n" + texto_limpio, flags=re.IGNORECASE)

    resultado = []
    for b in bloques:
        b = b.strip()
        if b and ("PROMPT:" in b.upper() or "ESTILO:" in b.upper() or len(b) > 60):
            resultado.append(b)

    if len(resultado) <= 1:
        bloques_alt = re.split(
            r"\n(?=(?:POSITIVE )?PROMPT:)", texto_limpio, flags=re.IGNORECASE
        )
        resultado = [b.strip() for b in bloques_alt if len(b.strip()) > 50]

    if len(resultado) <= 1:
        return []

    # Filtrar preámbulos cuando hay más bloques que los pedidos
    if n_esperado is not None and len(resultado) > n_esperado:
        con_marker = [
            b for b in resultado
            if re.search(r"POSITIVE\s+PROMPT|POSITIVE\s*:", b, re.IGNORECASE)
        ]
        if len(con_marker) >= n_esperado:
            resultado = con_marker[:n_esperado]
        else:
            resultado = resultado[-n_esperado:]

    return resultado


def extraer_pos_de_bloque(bloque: str) -> str:
    """Extrae la sección POSITIVE de un bloque LLM.

    Quita marcadores tipo ``` y separadores, después corta por
    NEGATIVE PROMPT: / NEGATIVE: si existen, y extrae lo que va tras
    POSITIVE PROMPT: o PROMPT:. Si no hay etiquetas explícitas,
    devuelve el bloque entero limpio.
    """
    limpio = limpiar_marcadores(bloque)
    p = limpio
    if "NEGATIVE PROMPT:" in p:
        p = p.split("NEGATIVE PROMPT:")[0]
    elif "NEGATIVE:" in p:
        p = p.split("NEGATIVE:")[0]

    if "POSITIVE PROMPT:" in p:
        return p.split("POSITIVE PROMPT:")[1].strip(" \n*")
    if "PROMPT:" in p:
        return p.split("PROMPT:")[1].strip(" \n*")
    return p.strip(" \n*")


def extraer_positive_de_texto(texto: str):
    """Extrae POSITIVE PROMPT de un string ya limpio (sin acceso a widgets)."""
    if "POSITIVE PROMPT:" in texto:
        bloque = texto.split("POSITIVE PROMPT:")[1]
        if "NEGATIVE PROMPT:" in bloque:
            return bloque.split("NEGATIVE PROMPT:")[0].strip(" \n*")
        return bloque.strip(" \n*")

    if "PROMPT:" in texto:
        bloque = texto.split("PROMPT:")[1]
        for marca in ["\nNEGATIVE\n", "\nNEGATIVE ", "\nNEGATIVE:", "\nNEGATIVE PROMPT:"]:
            if marca in bloque:
                bloque = bloque.split(marca)[0]
        for sep in ["\n1.", "\n2.", "\n3.", "\n──"]:
            if sep in bloque:
                bloque = bloque.split(sep)[0]
        return bloque.strip(" \n*")

    marcas_neg = ["NEGATIVE PROMPT:", "NEGATIVE:", "\nNEGATIVE\n", "\nNEGATIVE ", "\nNEGATIVE:"]
    limpia = texto
    for marca in marcas_neg:
        if marca in limpia:
            limpia = limpia.split(marca, 1)[0]
            break
    for sep in ["\n1.", "\n2.", "\n3.", "\n──", "\n══"]:
        if sep in limpia:
            limpia = limpia.split(sep)[0]
    limpia = limpia.strip(" \n*:")
    if limpia and len(limpia.strip()) > 5:
        return limpia
    return None


def extraer_negative_de_texto(texto: str):
    """Extrae NEGATIVE PROMPT de un string ya limpio (sin acceso a widgets)."""
    for marca in ["NEGATIVE PROMPT:", "\nNEGATIVE\n", "\nNEGATIVE:", "\nNEGATIVE "]:
        if marca in texto:
            bloque = texto.split(marca, 1)[1]
            for sep in ["\n1.", "\n2.", "\n3.", "\n──"]:
                if sep in bloque:
                    bloque = bloque.split(sep)[0]
            return bloque.strip(" \n*:")
    return None


def recortar_si_excede(
    texto: str, max_chars: int, max_chars_negative: int | None = None
) -> str:
    """Recorta POSITIVE y NEGATIVE si exceden el límite del modelo.

    Preserva la estructura POSITIVE PROMPT: / NEGATIVE PROMPT: y recorta
    por TAGS COMPLETOS (separadores: comas). Nunca corta en mitad de
    un tag.

    `max_chars_negative`: límite específico para NEGATIVE. Si None,
    se usa el mismo `max_chars`. Antes había un hardcoded de 1500
    para el negative, pero eso era erróneo para modelos como Z Image
    Turbo (negative también es 2000 chars, no 1500). El spec del modelo
    declara `max_chars_negative` para forzar un límite distinto.

    Si no hay match de POSITIVE PROMPT en el texto, lo devuelve sin
    tocar. Si falla cualquier excepción, también lo devuelve intacto.
    """
    if not max_chars or not texto:
        return texto
    try:
        m_pos = re.search(
            r"(?:POSITIVE\s+)?PROMPT\s*:\s*(.+?)(?=\n\s*NEGATIVE|$)",
            texto, re.DOTALL | re.IGNORECASE,
        )
        m_neg = re.search(
            r"NEGATIVE\s+PROMPT\s*:\s*(.+?)$",
            texto, re.DOTALL | re.IGNORECASE,
        )
        if not m_pos:
            return texto
        pos = m_pos.group(1).strip()
        neg = m_neg.group(1).strip() if m_neg else ""

        # Límite NEGATIVE: por defecto el mismo que POSITIVE.
        # El spec puede sobreescribir con `max_chars_negative`.
        NEGATIVE_MAX = max_chars_negative if max_chars_negative else max_chars
        neg_recortado = False
        if len(neg) > NEGATIVE_MAX:
            partes_neg = neg.split(",")
            neg = ""
            for p in partes_neg:
                p_stripped = p.strip()
                if len(neg) + len(p_stripped) + 2 > NEGATIVE_MAX:
                    break
                neg += (", " if neg else "") + p_stripped
            neg_recortado = True

        if len(pos) <= max_chars and not neg_recortado:
            return texto

        # Recortar pos preservando tags completos (separados por comas)
        pos_recortado = pos
        if len(pos) > max_chars:
            partes = pos.split(",")
            pos_recortado = ""
            for p in partes:
                p_stripped = p.strip()
                if len(pos_recortado) + len(p_stripped) + 2 > max_chars:
                    break
                pos_recortado += (", " if pos_recortado else "") + p_stripped

        nuevo = f"POSITIVE PROMPT: {pos_recortado}"
        if neg:
            nuevo += f"\nNEGATIVE PROMPT: {neg}"
        return nuevo
    except Exception:
        return texto
