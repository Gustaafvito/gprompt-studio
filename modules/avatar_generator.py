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
    ensamblar_dataset,
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
    with open(os.path.join(base, "CONSEJOS_SEAART.txt"), "w", encoding="utf-8") as f:
        f.write(CONSEJOS_LORA_SEAART)

    return base


CONSEJOS_LORA_SEAART = """GUÍA OFICIAL SEAART — DATASET PARA LoRA DE PERSONAJE
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
