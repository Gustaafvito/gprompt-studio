"""
AVATAR_GENERATOR — Generación y exportación del dataset
=======================================================
La llamada al LLM se inyecta como función para no acoplar el módulo a un
backend concreto (DeepSeek, Ollama, etc.).

NOTA PARA INTEGRACIÓN (Claude Code):
- `llm_call` debe ser la misma función que ya usa workers.py para llamar
  al backend LLM: llm_call(system_prompt: str, user_prompt: str) -> str
- `generar_dataset_avatar` puede ejecutarse dentro del worker/hilo
  existente de la app para no bloquear la UI de customtkinter.
"""

import json
import os
from datetime import datetime

from modules.avatar_prompts import (
    SYSTEM_PROMPT_AVATAR_CANONICO,
    construir_user_prompt_canonico,
    construir_user_prompt_para_tipo,
    ensamblar_dataset,
    ensamblar_dataset_generico,
    system_prompt_canonico_para_tipo,
)


def generar_descripcion_canonica(llm_call, form_data: dict) -> str:
    """FASE 1: una sola llamada al LLM para fijar la identidad del personaje."""
    user_prompt = construir_user_prompt_canonico(form_data)
    respuesta = llm_call(SYSTEM_PROMPT_AVATAR_CANONICO, user_prompt)
    # Saneado defensivo: una línea, sin markdown ni comillas envolventes.
    # Primero quitar newlines/fences y DESPUÉS las comillas — al revés,
    # un cierre tipo «"…"\n```» dejaba la comilla final colgando.
    desc = respuesta.strip()
    desc = desc.replace("\n", " ").replace("```", "").strip()
    desc = desc.strip('"').strip("'").strip()
    return desc


def generar_dataset_avatar(
    llm_call,
    form_data: dict,
    trigger_word: str,
    angulos_seleccionados: list,
    estilo_sufijo: str,
    fondo,
    incluir_negative: bool = True,
) -> dict:
    """Pipeline completo. Devuelve dict con la descripción canónica y el dataset.

    `fondo` puede ser un str (mismo fondo en todo el dataset) o una lista de
    fondos a rotar por imagen (ver ensamblar_dataset / fondo_para_indice)."""
    descripcion = generar_descripcion_canonica(llm_call, form_data)
    dataset = ensamblar_dataset(
        trigger_word=trigger_word,
        descripcion_canonica=descripcion,
        angulos_seleccionados=angulos_seleccionados,
        estilo_sufijo=estilo_sufijo,
        fondo=fondo,
        incluir_negative=incluir_negative,
    )
    return {
        "trigger_word": trigger_word.strip(),
        "descripcion_canonica": descripcion,
        "creado": datetime.now().isoformat(timespec="seconds"),
        "total_prompts": len(dataset),
        "dataset": dataset,
    }


def generar_dataset_lora(
    tipo: str,
    llm_call,
    form_data: dict,
    trigger_word: str,
    angulos_seleccionados: list,
    estilo_sufijo: str,
    fondo,
    incluir_negative: bool = True,
) -> dict:
    """Pipeline completo para cualquier tipo de LoRA (Personaje/Paisaje/Objeto/Estilo).

    Para 'Personaje' delega en el pipeline original (descripción canónica de
    personaje con lógica de ropa y recorte). Para el resto usa el pipeline
    genérico que no modifica la descripción por ángulo."""
    from modules.avatar_config import LORA_TYPES

    if tipo == "Personaje":
        return generar_dataset_avatar(
            llm_call=llm_call,
            form_data=form_data,
            trigger_word=trigger_word,
            angulos_seleccionados=angulos_seleccionados,
            estilo_sufijo=estilo_sufijo,
            fondo=fondo,
            incluir_negative=incluir_negative,
        )

    cfg = LORA_TYPES[tipo]
    system_p = system_prompt_canonico_para_tipo(tipo)
    user_p = construir_user_prompt_para_tipo(tipo, form_data)
    descripcion = llm_call(system_p, user_p)
    descripcion = descripcion.strip().replace("\n", " ").replace("```", "").strip()
    descripcion = descripcion.strip('"').strip("'").strip()

    dataset = ensamblar_dataset_generico(
        tipo=tipo,
        trigger_word=trigger_word,
        descripcion_canonica=descripcion,
        angulos_seleccionados=angulos_seleccionados,
        angles_dict=cfg["angles"],
        estilo_sufijo=estilo_sufijo,
        fondo=fondo,
        lighting=cfg["lighting"],
        negative_base=cfg["negative"],
        incluir_negative=incluir_negative,
    )

    return {
        "tipo_lora": tipo,
        "trigger_word": trigger_word.strip(),
        "descripcion_canonica": descripcion,
        "creado": datetime.now().isoformat(timespec="seconds"),
        "total_prompts": len(dataset),
        "dataset": dataset,
    }


def adaptar_dataset_a_modelo(resultado: dict, modelo: str, specs: dict) -> list:
    """Adapta el dataset al modelo de imagen destino usando sus specs.

    100% determinista (sin LLM). Muta `resultado` y devuelve la lista
    de avisos para mostrar al usuario. Reglas (sesión 19):
    - has_negative=False (Nano Banana, GPT Image...) → vacía los
      negatives del dataset: el modelo los ignoraría o los trataría
      como prompt positivo.
    - max_chars → avisa si algún prompt lo excede. NO trunca: recortar
      rompería la consistencia de identidad entre ángulos; mejor que
      el usuario acorte ropa/rasgos y regenere.
    - Registra el modelo destino en el dataset.json (trazabilidad).
    """
    avisos = []
    if not specs:
        return avisos

    resultado["modelo_destino"] = modelo

    # El dataset de edición (img2img), si existe, sigue las mismas reglas
    listas = [resultado["dataset"]] + (
        [resultado["dataset_edicion"]] if resultado.get("dataset_edicion") else [])

    if specs.get("has_negative") is False:
        n_con_negative = sum(1 for lista in listas
                             for it in lista if it["negative"])
        if n_con_negative:
            for lista in listas:
                for it in lista:
                    it["negative"] = ""
            avisos.append(
                f"⚠️ {modelo} NO soporta negative prompt — se ha quitado "
                f"de los {n_con_negative} prompts del dataset."
            )

    max_c = specs.get("max_chars")
    if max_c:
        excedidos = [it["filename"] for lista in listas for it in lista
                     if len(it["prompt"]) > max_c]
        if excedidos:
            avisos.append(
                f"⚠️ {len(excedidos)} prompt(s) exceden el límite de "
                f"{max_c} caracteres de {modelo} (ej: {excedidos[0]}). "
                f"Acorta la ropa/rasgos en la ficha y regenera — NO se "
                f"truncan automáticamente para no romper la identidad."
            )

    return avisos


# ---------------------------------------------------------------------------
# EXPORTACIÓN
# Estructura de salida:
#   <carpeta>/
#     dataset.json            -> todo el dataset (machine-readable)
#     prompts/NN_nombre.txt   -> un prompt por archivo (positivo + negative)
#     prompts_todos.txt       -> todos los prompts seguidos (copiar/pegar rápido)
#     captions/NN_nombre.txt  -> captions kohya (mismo nombre que la imagen)
# ---------------------------------------------------------------------------
def _slug_carpeta(trigger: str) -> str:
    """Convierte el trigger en un nombre de carpeta SEGURO para Windows.

    Un trigger con comas, ':', '/' o muy largo (p. ej. si el usuario pega un
    negative prompt en el campo) rompe la creación de carpeta con WinError 123.
    Dejamos solo [A-Za-z0-9_-], colapsamos lo demás a '_' y truncamos a 40."""
    import re as _re
    slug = _re.sub(r"[^\w\-]+", "_", (trigger or "").strip()).strip("_")
    return slug[:40] or "dataset"


def exportar_dataset(resultado: dict, carpeta_salida: str) -> str:
    """Escribe el dataset en disco. Devuelve la ruta de la carpeta creada."""
    base = os.path.join(
        carpeta_salida,
        f"avatar_{_slug_carpeta(resultado.get('trigger_word'))}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    )
    dir_prompts = os.path.join(base, "prompts")
    dir_captions = os.path.join(base, "captions")
    os.makedirs(dir_prompts, exist_ok=True)
    os.makedirs(dir_captions, exist_ok=True)

    # dataset.json completo
    with open(os.path.join(base, "dataset.json"), "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    # Archivos individuales + archivo "todos"
    lineas_todos = []
    for item in resultado["dataset"]:
        nombre = item["filename"]

        contenido = f"PROMPT:\n{item['prompt']}\n"
        if item["negative"]:
            contenido += f"\nNEGATIVE PROMPT:\n{item['negative']}\n"
        with open(os.path.join(dir_prompts, f"{nombre}.txt"), "w", encoding="utf-8") as f:
            f.write(contenido)

        with open(os.path.join(dir_captions, f"{nombre}.txt"), "w", encoding="utf-8") as f:
            f.write(item["caption"])

        bloque = f"=== {nombre} | {item['label']} ===\n{item['prompt']}\n"
        # El negative varía por encuadre (los primeros planos añaden el cuerpo
        # al negative para forzar el recorte), así que va por bloque, no uno
        # compartido al final.
        if item["negative"]:
            bloque += f"NEGATIVE: {item['negative']}\n"
        lineas_todos.append(bloque)

    with open(os.path.join(base, "prompts_todos.txt"), "w", encoding="utf-8") as f:
        if resultado.get("dataset_edicion"):
            f.write(
                "⚠️ Estos son los prompts TEXT-TO-IMAGE. Hay también un modo\n"
                "   EDICIÓN (prompts_edicion_todos.txt). Son ALTERNATIVOS: usa\n"
                "   uno U otro por imagen, NO pegues los dos juntos.\n\n"
            )
        f.write("\n".join(lineas_todos))

    # Prompts de EDICIÓN img2img (solo si se generaron — requieren
    # imagen de referencia). Van en su propia carpeta para no mezclar
    # con los text-to-image.
    if resultado.get("dataset_edicion"):
        dir_edicion = os.path.join(base, "prompts_edicion")
        os.makedirs(dir_edicion, exist_ok=True)
        lineas_ed = [
            "=== MODO EDICIÓN (img2img con imagen de sujeto) ===",
            "",
            "⚠️ ALTERNATIVO al text-to-image (prompts_todos.txt): usa el modo",
            "   edición O el text-to-image por imagen, NUNCA los dos juntos.",
            "   Pegar ambos en el mismo prompt confunde al modelo.",
            "",
            "1. En SeaArt elige un modelo con edición/sujeto: MAI-Image-2.5,",
            "   Nano Banana o Reve 2.0.",
            "2. Sube la imagen 'referencia.*' de esta carpeta como SUJETO.",
            "3. Pega cada prompt de abajo: cambia solo la cámara, la",
            "   identidad la aporta tu imagen.",
            "",
        ]
        for item in resultado["dataset_edicion"]:
            nombre = item["filename"]
            contenido = f"PROMPT (edición):\n{item['prompt']}\n"
            if item["negative"]:
                contenido += f"\nNEGATIVE PROMPT:\n{item['negative']}\n"
            with open(os.path.join(dir_edicion, f"{nombre}.txt"), "w",
                      encoding="utf-8") as f:
                f.write(contenido)
            lineas_ed.append(f"=== {nombre} | {item['label']} ===\n{item['prompt']}\n")
        with open(os.path.join(base, "prompts_edicion_todos.txt"), "w",
                  encoding="utf-8") as f:
            f.write("\n".join(lineas_ed))

    # Consejos de la guía OFICIAL de SeaArt para entrenamiento LoRA
    # (docs.seaart.ai → Entrenamiento de LoRA avanzado → datasets).
    # El consejo se elige según el TIPO de LoRA (Personaje/Estilo/Objeto/Paisaje):
    # cada tipo tiene reglas distintas (p.ej. en Estilo la clave es variar sujetos).
    tipo = resultado.get("tipo_lora", "Personaje")
    consejo = CONSEJOS_LORA_POR_TIPO.get(tipo, CONSEJOS_LORA_POR_TIPO["Personaje"])
    with open(os.path.join(base, "CONSEJOS_SEAART.txt"), "w", encoding="utf-8") as f:
        f.write(consejo)

    return base


_CONSEJOS_PERSONAJE = """GUÍA OFICIAL SEAART — DATASET PARA LoRA DE PERSONAJE
====================================================
(fuente: docs.seaart.ai → Entrenamiento de LoRA avanzado)

• CANTIDAD: 25-40 imágenes en total. Más imágenes ≠ mejor (riesgo de
  LoRA sobreentrenada).
• DISTRIBUCIÓN por encuadre (ejemplo oficial para 30 imágenes):
  ~12 retratos, ~6 medios, ~8 cuerpo entero, 8-10 de pie.
  Máximo 3-6 imágenes por término/etiqueta.
• FONDOS: NO uses el mismo fondo en todo el dataset — el LoRA lo
  absorberá y lo generará siempre. Máximo 3-6 imágenes por fondo.
  → Esta herramienta ya rota varios fondos neutros automáticamente
    si dejas marcado "Variar fondos" (recomendado). Si lo desmarcas,
    usa un fondo único: genera el dataset 2-3 veces cambiándolo a mano.
• RESOLUCIÓN: 1024x1024 para SDXL / Flux / SD 3.5 (512x512 para SD 1.5).
• RECORTE: "Focus Crop" es el modo recomendado para personajes.
• CAPTIONS: BLIP para fotorrealismo/SDXL/Flux; Deepbooru para
  anime/furry/cómic. Umbral 0.5-0.8.
• REGLA DE ORO: la identidad del personaje va en el TRIGGER WORD
  (no la etiquetes); el fondo, la iluminación, la pose y la expresión
  SÍ van en la caption (este dataset ya lo hace así).
"""

_CONSEJOS_ESTILO = """GUÍA OFICIAL SEAART — DATASET PARA LoRA DE ESTILO
==================================================
(fuente: docs.seaart.ai → Entrenamiento de LoRA avanzado)

• CANTIDAD: 20-40 imágenes de SUJETOS VARIADOS (este generador ya da hasta 30).
• CLAVE DEL ESTILO — VARÍA EL SUJETO: lo que enseña el estilo es la VARIEDAD
  de contenidos renderizados igual. Si todo son retratos, el LoRA aprenderá
  "retratos en este estilo", no el estilo en general. Mezcla personas,
  naturaleza, objetos, arquitectura, fantasía, detalles… (este dataset lo hace).
• LO QUE DEBE REPETIRSE es el ESTILO (paleta, trazo, sombreado, técnica),
  NO el contenido. Mantén la descripción de estilo idéntica en todas las imágenes.
• FONDOS: aquí el fondo/color SÍ forma parte del estilo y puede ser coherente;
  lo que cambia es el SUJETO, no la estética.
• RESOLUCIÓN: 1024x1024 para SDXL / Flux / SD 3.5 (512x512 para SD 1.5).
• CAPTIONS: describe el CONTENIDO (qué se ve), NO el estilo. Deepbooru para
  anime/cómic/ilustración; BLIP para foto/render. Umbral 0.5-0.8.
• REGLA DE ORO: el ESTILO va en el TRIGGER WORD (no lo etiquetes); el sujeto
  y la escena SÍ van en la caption (este dataset ya lo hace así).
"""

_CONSEJOS_OBJETO = """GUÍA OFICIAL SEAART — DATASET PARA LoRA DE OBJETO / PRODUCTO
============================================================
(fuente: docs.seaart.ai → Entrenamiento de LoRA avanzado)

• CANTIDAD: 20-40 vistas del MISMO objeto desde ángulos distintos.
• CLAVE — MUCHAS VISTAS: frontal, laterales, 3/4, superior, inferior, posterior
  y primeros planos de detalle. Así el LoRA aprende la forma 3D COMPLETA y no
  solo una cara (este generador ya da hasta 30 vistas).
• FONDOS: varía el fondo y el contexto (estudio, superficie natural, lifestyle)
  — si repites fondo, el LoRA lo absorberá. Máx. 3-6 imágenes por fondo.
• ILUMINACIÓN: varía la luz (suave, dramática, contraluz) para un LoRA robusto.
• RESOLUCIÓN: 1024x1024 para SDXL / Flux / SD 3.5 (512x512 para SD 1.5).
• CAPTIONS: describe el ángulo, el fondo y la luz, NO la identidad del objeto.
• REGLA DE ORO: la identidad del objeto va en el TRIGGER WORD (no la etiquetes);
  el ángulo, el fondo y la iluminación SÍ van en la caption (este dataset lo hace).
"""

_CONSEJOS_PAISAJE = """GUÍA OFICIAL SEAART — DATASET PARA LoRA DE PAISAJE / LUGAR
==========================================================
(fuente: docs.seaart.ai → Entrenamiento de LoRA avanzado)

• CANTIDAD: 20-40 encuadres del mismo tipo de paisaje o lugar.
• CLAVE — VARÍA CONDICIONES: encuadre (panorámica, detalle, aéreo), luz
  (amanecer, mediodía, hora dorada, noche), clima (niebla, lluvia, nieve) y
  estación. Así el LoRA captura el LUGAR/BIOMA en todas sus condiciones
  (este generador ya da hasta 30 encuadres).
• SIN PERSONAS: un LoRA de paisaje no debe incluir gente (el negative ya la excluye).
• RESOLUCIÓN: 1024x1024 (o formato panorámico) para SDXL / Flux / SD 3.5.
• CAPTIONS: describe el encuadre, la luz y el clima, NO el bioma en sí.
• REGLA DE ORO: la identidad del lugar/bioma va en el TRIGGER WORD (no la
  etiquetes); las condiciones (luz, clima, encuadre) SÍ van en la caption.
"""

CONSEJOS_LORA_POR_TIPO = {
    "Personaje": _CONSEJOS_PERSONAJE,
    "Estilo": _CONSEJOS_ESTILO,
    "Objeto": _CONSEJOS_OBJETO,
    "Paisaje": _CONSEJOS_PAISAJE,
}

# Retrocompat: algunos sitios importaban el texto único.
CONSEJOS_LORA_SEAART = _CONSEJOS_PERSONAJE


# ---------------------------------------------------------------------------
# Modo de prueba sin LLM (smoke test): python avatar_generator.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    def _llm_fake(system, user):
        return ("a 28 year old woman with fair mediterranean skin, oval face, "
                "large almond-shaped green eyes, wavy chestnut brown shoulder-length hair, "
                "light freckles, slim athletic build, wearing a plain white crew-neck "
                "t-shirt and blue denim jeans")

    from modules.avatar_config import AVATAR_BACKGROUNDS, AVATAR_STYLES, DEFAULT_ANGLE_SET

    res = generar_dataset_avatar(
        llm_call=_llm_fake,
        form_data={"genero": "Mujer", "edad": "25-35", "pelo": "castaña ondulada",
                   "ojos": "verdes", "ropa": "camiseta blanca y vaqueros"},
        trigger_word="ohwx_ana",
        angulos_seleccionados=DEFAULT_ANGLE_SET,
        estilo_sufijo=AVATAR_STYLES["Fotorrealista"],
        fondo=AVATAR_BACKGROUNDS["Gris neutro (recomendado LoRA)"],
    )
    ruta = exportar_dataset(res, ".")
    print(f"OK — {res['total_prompts']} prompts exportados en: {ruta}")
