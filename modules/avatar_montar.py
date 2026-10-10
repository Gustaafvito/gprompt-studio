"""
AVATAR_MONTAR — De las imágenes descargadas a un dataset listo para entrenar
============================================================================
Fase 3 del Generador de Dataset LoRA. Tras «Generar dataset» quedan los
prompts y las descripciones; el usuario genera las imágenes (SeaArt, ComfyUI)
y las descarga con el nombre que les pone cada sitio. Para entrenar hay que
juntar cada imagen con su descripción y mismo nombre: G-Entrena lee
`000.png` + `000.txt` (lo dice su código: file.with_suffix('.txt')), y el
entrenador de SeaArt admite subir un dataset ya etiquetado igual.

Emparejado, en este orden:
  1. Por NOMBRE: los workflows de ComfyUI guardan cada toma con su nombre
     («05_bust_front_00001_.png»). Si hay versión «_detailed» (el detailer),
     gana esa.
  2. Por ORDEN de descarga (fecha de modificación) lo que quede: SeaArt
     descarga con nombres aleatorios, y el usuario genera los prompts en
     orden.

Funciones puras con ficheros (sin Tk): la ventana solo elige carpeta e
imágenes y enseña el resumen.
"""

import json
import os
import shutil

from modules.i18n import tr

# Lo que aceptan G-Entrena (dataset.py: IMAGES) y el entrenador de SeaArt
# («Soporta png/jpg/jpeg/webp»).
EXTENSIONES = (".png", ".jpg", ".jpeg", ".webp")


def leer_dataset(carpeta: str) -> dict:
    """El dataset.json de una exportación del generador."""
    ruta = os.path.join(carpeta, "dataset.json")
    if not os.path.isfile(ruta):
        raise ValueError(tr(
            "Esa carpeta no es un dataset del generador: falta dataset.json."))
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def _toma_de(nombre_imagen: str, items: list):
    """El item cuya toma lleva esa imagen en el nombre, o None."""
    raiz = os.path.splitext(os.path.basename(nombre_imagen))[0]
    for item in items:
        toma = item.get("filename", "")
        if toma and (raiz == toma or raiz.startswith(toma + "_")):
            return item
    return None


def emparejar(items: list, imagenes: list):
    """[(item, imagen | None)] en el orden del dataset, y las que sobran.

    Primero por nombre de toma; el resto, por orden de descarga."""
    validas = [p for p in imagenes if p.lower().endswith(EXTENSIONES)]
    asignadas = {}
    sobrantes = []
    for img in validas:
        item = _toma_de(img, items)
        if item is None:
            continue
        clave = item["filename"]
        previa = asignadas.get(clave)
        if previa is None:
            asignadas[clave] = img
        elif "_detailed" in os.path.basename(img) and "_detailed" not in os.path.basename(previa):
            sobrantes.append(previa)
            asignadas[clave] = img
        else:
            sobrantes.append(img)
    usadas = set(asignadas.values()) | set(sobrantes)
    por_orden = sorted((p for p in validas if p not in usadas),
                       key=lambda p: (os.path.getmtime(p), os.path.basename(p)))
    pares = []
    for item in items:
        img = asignadas.get(item["filename"])
        if img is None and por_orden:
            img = por_orden.pop(0)
        pares.append((item, img))
    sobrantes.extend(por_orden)
    return pares, sobrantes


def _carpeta_libre(base: str) -> str:
    ruta, n = base, 2
    while os.path.exists(ruta):
        ruta = f"{base}_{n}"
        n += 1
    return ruta


def montar_dataset(carpeta_dataset: str, imagenes: list) -> dict:
    """Copia las imágenes como 000.png, 001.jpg… con su 000.txt al lado.

    Devuelve el resumen: carpeta creada, cuántas por nombre y por orden, las
    tomas sin imagen, las imágenes que sobran y las de formato no admitido.
    Si el destino no usa descripciones (Higgsfield, Magnific), solo copia
    las imágenes. Nunca mueve ni borra lo descargado."""
    datos = leer_dataset(carpeta_dataset)
    items = datos.get("dataset") or []
    if not items:
        raise ValueError(tr("El dataset no tiene tomas."))
    omitidas = [p for p in imagenes if not p.lower().endswith(EXTENSIONES)]
    pares, sobrantes = emparejar(items, imagenes)
    por_nombre = {item["filename"] for item, img in pares
                  if img and _toma_de(img, items) is item}

    con_txt = not datos.get("sin_descripciones")
    salida = _carpeta_libre(os.path.join(carpeta_dataset, "dataset_listo"))
    os.makedirs(salida)
    copiadas = 0
    sin_imagen = []
    for item, img in pares:
        if img is None:
            sin_imagen.append(item.get("label") or item["filename"])
            continue
        nombre = f"{copiadas:03d}"
        ext = os.path.splitext(img)[1].lower()
        shutil.copy2(img, os.path.join(salida, nombre + ext))
        if con_txt:
            with open(os.path.join(salida, nombre + ".txt"), "w", encoding="utf-8") as f:
                f.write(item.get("caption", ""))
        copiadas += 1
    return {
        "carpeta": salida,
        "copiadas": copiadas,
        "por_nombre": len(por_nombre),
        "por_orden": copiadas - len(por_nombre),
        "sin_imagen": sin_imagen,
        "sobrantes": sobrantes,
        "omitidas": omitidas,
        "con_descripciones": con_txt,
        "destino": (datos.get("destino_entrenamiento") or {}),
    }


def resumen_montaje(r: dict) -> str:
    """Texto del aviso final para el usuario."""
    lineas = [tr("✅ {0} imágenes listas en:\n{1}").format(r["copiadas"], r["carpeta"])]
    if r["por_nombre"]:
        lineas.append(tr("• {0} emparejadas por nombre (las de ComfyUI).").format(r["por_nombre"]))
    if r["por_orden"]:
        lineas.append(tr(
            "• {0} emparejadas por orden de descarga: comprueba que cada una "
            "va con su descripción.").format(r["por_orden"]))
    if r["sin_imagen"]:
        lineas.append(tr("⚠️ Sin imagen ({0}): {1}").format(
            len(r["sin_imagen"]), ", ".join(r["sin_imagen"][:5])
            + ("…" if len(r["sin_imagen"]) > 5 else "")))
    if r["sobrantes"]:
        lineas.append(tr("⚠️ Sobran {0} imágenes: no se han copiado.").format(len(r["sobrantes"])))
    if r["omitidas"]:
        lineas.append(tr(
            "⚠️ {0} con formato no admitido (solo png, jpg o webp): no se han "
            "copiado.").format(len(r["omitidas"])))
    if not r["con_descripciones"]:
        lineas.append(tr("ℹ️ Este destino no usa descripciones: solo van las imágenes."))
    destino = r.get("destino") or {}
    if destino.get("plataforma") == "G-Entrena":
        lineas.append(tr(
            "Siguiente paso: en el proyecto de G-Entrena, «Importar carpeta» con "
            "esta carpeta. Si subes las imágenes sueltas, llegan sin descripción."))
    elif destino.get("plataforma") == "SeaArt":
        lineas.append(tr("Siguiente paso: en el entrenador de SeaArt, «Subir conjunto de datos» con esta carpeta."))
    return "\n\n".join(lineas)
