"""
AVATAR_DESTINOS — Dónde se va a entrenar el LoRA y cómo se describe cada imagen
==============================================================================
El dataset sirve para ENTRENAR, y cada plataforma lee las descripciones (.txt)
a su manera: SeaArt pide tags para SD 1.5 / Pony / Illustrious y frases para
Flux, SDXL, Z-Image, Qwen o Anima; G-Entrena entrenó el LoRA Lyra con trozos
separados por comas; Higgsfield y Magnific no usan descripciones. El catálogo
vive en data/destinos_entrenamiento.json.

Qué va en la descripción (guía de SeaArt, la misma que sigue el resto del
módulo): lo que el LoRA NO debe absorber —encuadre, fondo, luz— y la palabra
de clase («a woman», «1girl»). La identidad no se describe: la absorbe el
trigger. En un LoRA de estilo, al revés: se describe el contenido y nunca el
estilo, que es lo que debe aprender el trigger.

Funciones puras (sin Tk): la ventana solo elige el destino y llama a
aplicar_destino() tras ensamblar el dataset.
"""

from modules.i18n import tr, tr_es

ESTILOS_DESCRIPCION = ("etiquetas", "frases", "natural", "ninguna")

# Palabra de clase de personaje según el género de la ficha (clave ES).
_CLASE_PERSONA = {
    "Mujer": ("1girl, solo", "a woman"),
    "Hombre": ("1boy, solo", "a man"),
}
_CLASE_PERSONA_DEFECTO = ("1other, solo", "a person")

# Clase de objeto según la categoría de la ficha (clave ES).
_CLASE_OBJETO = {
    "Joyería / Accesorio": "a piece of jewelry",
    "Electrónica / Gadget": "an electronic gadget",
    "Moda / Ropa": "a garment",
    "Alimento / Bebida": "a food or drink product",
    "Mueble / Decoración": "a piece of furniture",
    "Herramienta": "a tool",
    "Juguete / Coleccionable": "a toy",
    "Vehículo / Transporte": "a vehicle",
}


def cargar_destinos() -> list:
    """Destinos del catálogo (con override de usuario, como el resto de data/)."""
    from config import _load_json_data
    return list(_load_json_data("destinos_entrenamiento.json")["destinos"])


def etiqueta_destino(destino: dict) -> str:
    """Texto del desplegable: «SeaArt · Anima»."""
    return f"{destino['plataforma']} · {tr(destino['base'])}"


def destinos_para_tipo(tipo: str, destinos=None) -> list:
    """Los destinos que admiten ese tipo de LoRA, en el orden del catálogo."""
    destinos = cargar_destinos() if destinos is None else destinos
    return [d for d in destinos if tipo in d.get("tipos", [])]


def destino_por_defecto(modelo: str, plataforma: str, tipo: str, destinos=None):
    """Propone dónde entrenar a partir del modelo con el que se va a generar.

    Mismo modelo base: con ComfyUI se propone G-Entrena (los LoRA locales se
    entrenan ahí) y, si no, SeaArt. Sin coincidencia, el primero del tipo.
    """
    candidatos = destinos_para_tipo(tipo, destinos)
    if not candidatos:
        return None
    try:
        from modules.ui_footer import familia_modelo_para_lora
        familia = familia_modelo_para_lora(modelo) or ""
    except Exception:
        familia = ""
    if familia:
        mismos = [d for d in candidatos if d.get("familia") == familia]
        local = (plataforma or "").startswith("ComfyUI")
        preferida = "G-Entrena" if local else "SeaArt"
        for d in mismos:
            if d["plataforma"] == preferida:
                return d
        if mismos:
            return mismos[0]
    return candidatos[0]


def rango_imagenes(destino: dict, tipo: str):
    """[mín, máx] recomendado para ese tipo, o None si el destino no lo dice."""
    por_tipo = destino.get("imagenes_por_tipo") or {}
    return por_tipo.get(tipo) or destino.get("imagenes")


def clase_para(tipo: str, form_data: dict):
    """(tags, frase) de la palabra de clase, o None (estilo: no lleva clase)."""
    form_data = form_data or {}
    if tipo in ("Personaje", "NSFW"):
        genero = tr_es(str(form_data.get("genero", "")))
        return _CLASE_PERSONA.get(genero, _CLASE_PERSONA_DEFECTO)
    if tipo == "Paisaje":
        return ("scenery, no humans", "a place")
    if tipo == "Objeto":
        categoria = tr_es(str(form_data.get("categoria", "")))
        return ("no humans", _CLASE_OBJETO.get(categoria, "an object"))
    return None


def medio_para(estilo_visual: str) -> str:
    """Cómo empieza la frase natural según el estilo visual de la ficha."""
    e = tr_es(estilo_visual or "").lower()
    if "foto" in e or "editorial" in e or "realis" in e or "cinemat" in e:
        return "A photo of"
    if "anime" in e:
        return "An anime illustration of"
    if "3d" in e:
        return "A 3D render of"
    if "ilustr" in e or "cómic" in e or "comic" in e:
        return "An illustration of"
    return "An image of"


def redactar_descripcion(partes: dict, estilo: str, tipo: str, trigger: str,
                         clase=None, medio: str = "An image of") -> str:
    """La descripción (.txt) de UNA imagen en el formato del destino.

    `partes`: {"encuadre", "fondo", "luz"} en inglés; los vacíos se omiten.
    """
    if estilo == "ninguna":
        return ""
    trigger = (trigger or "").strip()
    resto = [partes.get(k, "").strip() for k in ("encuadre", "fondo", "luz")]
    resto = [r for r in resto if r]
    if estilo == "etiquetas":
        trozos = [trigger] + ([clase[0]] if clase else []) + resto
        return ", ".join(t for t in trozos if t)
    if estilo == "frases":
        trozos = [trigger] + ([clase[1]] if clase else []) + resto
        return ", ".join(t for t in trozos if t)
    # natural: una frase. En estilo, el trigger nombra el estilo y el
    # contenido se describe sin palabras de estilo.
    if tipo == "Estilo" or not clase:
        cabeza = (resto[0][:1].upper() + resto[0][1:]) if resto else "An image"
        cola = resto[1:]
        frase = f"{cabeza}, in the {trigger} style"
    else:
        frase = f"{medio} {clase[1]} named {trigger}"
        cola = resto
    if cola:
        frase += ", " + ", ".join(cola)
    return frase + "."


def aplicar_destino(resultado: dict, destino: dict, tipo: str,
                    form_data: dict, estilo_visual: str = "") -> list:
    """Reescribe las descripciones del dataset para el destino. Devuelve avisos.

    Muta `resultado`: cada elemento con 'partes_descripcion' recibe su nueva
    'caption'; se anota el destino y, si no usa descripciones,
    'sin_descripciones' para que la exportación no las escriba.
    """
    avisos = []
    if not destino:
        return avisos
    estilo = destino.get("descripciones", "frases")
    clase = clase_para(tipo, form_data)
    medio = medio_para(estilo_visual)
    trigger = resultado.get("trigger_word", "")

    listas = [resultado.get("dataset") or []]
    if resultado.get("dataset_edicion"):
        listas.append(resultado["dataset_edicion"])
    for lista in listas:
        for item in lista:
            partes = item.get("partes_descripcion")
            if partes is not None:
                item["caption"] = redactar_descripcion(
                    partes, estilo, tipo, trigger, clase, medio)

    resultado["destino_entrenamiento"] = {
        "id": destino.get("id", ""),
        "plataforma": destino.get("plataforma", ""),
        "base": destino.get("base", ""),
        "descripciones": estilo,
    }
    if estilo == "ninguna":
        resultado["sin_descripciones"] = True
        avisos.append(tr(
            "ℹ️ {0} no usa descripciones: sube solo las imágenes.").format(
                etiqueta_destino(destino)))

    rango = rango_imagenes(destino, tipo)
    n = len(resultado.get("dataset") or [])
    if rango and n:
        minimo, maximo = rango
        if n < minimo or n > maximo:
            recomendado = (str(minimo) if minimo == maximo
                           else tr("entre {0} y {1}").format(minimo, maximo))
            avisos.append(tr(
                "⚠️ {0} imágenes: para {1} se recomiendan {2}.").format(
                    n, etiqueta_destino(destino), recomendado))
    return avisos


def consejo_destino(destino: dict, tipo: str) -> str:
    """Bloque de texto para CONSEJOS_SEAART.txt con lo propio del destino."""
    if not destino:
        return ""
    rango = rango_imagenes(destino, tipo)
    lineas = [tr("DESTINO DE ENTRENAMIENTO: {0}").format(etiqueta_destino(destino))]
    nombres = {
        "etiquetas": tr("tags separados por comas"),
        "frases": tr("trigger y trozos separados por comas"),
        "natural": tr("una frase en lenguaje natural"),
        "ninguna": tr("ninguna (solo las imágenes)"),
    }
    lineas.append(tr("Descripciones: {0}").format(
        nombres.get(destino.get("descripciones"), destino.get("descripciones", ""))))
    if rango:
        minimo, maximo = rango
        lineas.append(tr("Imágenes recomendadas: {0}").format(
            minimo if minimo == maximo else f"{minimo}-{maximo}"))
    if destino.get("nota"):
        lineas.append(tr(destino["nota"]))
    return "\n".join(lineas) + "\n\n" + "=" * 67 + "\n\n"
