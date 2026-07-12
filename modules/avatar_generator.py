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
from modules.i18n import tr


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
                tr("⚠️ {0} NO soporta negative prompt — se ha quitado "
                   "de los {1} prompts del dataset.").format(modelo, n_con_negative)
            )

    max_c = specs.get("max_chars")
    if max_c:
        excedidos = [it["filename"] for lista in listas for it in lista
                     if len(it["prompt"]) > max_c]
        if excedidos:
            avisos.append(
                tr("⚠️ {0} prompt(s) exceden el límite de "
                   "{1} caracteres de {2} (ej: {3}). "
                   "Acorta la ropa/rasgos en la ficha y regenera — NO se "
                   "truncan automáticamente para no romper la identidad.").format(
                    len(excedidos), max_c, modelo, excedidos[0])
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
        ratio = item.get("ratio", "")
        ratio_linea = f"RATIO SUGERIDO: {ratio}\n\n" if ratio else ""

        contenido = f"{ratio_linea}PROMPT:\n{item['prompt']}\n"
        if item["negative"]:
            contenido += f"\nNEGATIVE PROMPT:\n{item['negative']}\n"
        with open(os.path.join(dir_prompts, f"{nombre}.txt"), "w", encoding="utf-8") as f:
            f.write(contenido)

        with open(os.path.join(dir_captions, f"{nombre}.txt"), "w", encoding="utf-8") as f:
            f.write(item["caption"])

        cab_ratio = f"  [ratio {ratio}]" if ratio else ""
        bloque = f"=== {nombre} | {item['label']}{cab_ratio} ===\n{item['prompt']}\n"
        # El negative varía por encuadre (los primeros planos añaden el cuerpo
        # al negative para forzar el recorte), así que va por bloque, no uno
        # compartido al final.
        if item["negative"]:
            bloque += f"NEGATIVE: {item['negative']}\n"
        lineas_todos.append(bloque)

    with open(os.path.join(base, "prompts_todos.txt"), "w", encoding="utf-8") as f:
        if resultado.get("dataset_edicion"):
            f.write(tr(
                "⚠️ Estos son los prompts TEXT-TO-IMAGE. Hay también un modo\n"
                "   EDICIÓN (prompts_edicion_todos.txt). Son ALTERNATIVOS: usa\n"
                "   uno U otro por imagen, NO pegues los dos juntos.\n\n"
            ))
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
            ratio = item.get("ratio", "")
            ratio_linea = f"RATIO SUGERIDO: {ratio}\n\n" if ratio else ""

            contenido = f"{ratio_linea}PROMPT (edición):\n{item['prompt']}\n"
            if item["negative"]:
                contenido += f"\nNEGATIVE PROMPT:\n{item['negative']}\n"
            with open(os.path.join(dir_edicion, f"{nombre}.txt"), "w",
                      encoding="utf-8") as f:
                f.write(contenido)
            cab_ratio = f"  [ratio {ratio}]" if ratio else ""
            lineas_ed.append(
                f"=== {nombre} | {item['label']}{cab_ratio} ===\n{item['prompt']}\n")
        with open(os.path.join(base, "prompts_edicion_todos.txt"), "w",
                  encoding="utf-8") as f:
            f.write("\n".join(lineas_ed))

    # Consejos de la guía OFICIAL de SeaArt para entrenamiento LoRA
    # (docs.seaart.ai → Entrenamiento de LoRA avanzado → datasets).
    # El consejo se elige según el TIPO de LoRA (Personaje/Estilo/Objeto/Paisaje):
    # cada tipo tiene reglas distintas (p.ej. en Estilo la clave es variar sujetos).
    tipo = resultado.get("tipo_lora", "Personaje")
    consejo = CONSEJOS_LORA_POR_TIPO.get(tipo, CONSEJOS_LORA_POR_TIPO["Personaje"])
    # Si hay imagen de referencia se exportan DOS carpetas de prompts
    # (text-to-image + edición img2img). Explicamos la diferencia arriba
    # del todo para que no despiste — son ALTERNATIVAS, no se pegan juntas.
    cabecera = ""
    if resultado.get("dataset_edicion"):
        cabecera = tr(
            "ℹ️ ESTE DATASET TRAE DOS CARPETAS DE PROMPTS (porque cargaste una\n"
            "   imagen de referencia). Son ALTERNATIVAS — elige UNA vía por imagen:\n\n"
            "   • prompts/  → TEXTO→IMAGEN. La identidad la describe el texto\n"
            "     (tu trigger word). Es el dataset para ENTRENAR/generar un LoRA.\n"
            "   • prompts_edicion/  → EDICIÓN img2img. La identidad la aporta tu\n"
            "     'referencia.*': súbela como SUJETO en MAI / Nano Banana / Reve\n"
            "     y pega estos prompts; solo cambia la cámara.\n\n"
            "   (captions/ son los .txt emparejados para el entrenamiento LoRA.)\n\n"
            "===================================================================\n\n"
        )
    with open(os.path.join(base, "CONSEJOS_SEAART.txt"), "w", encoding="utf-8") as f:
        f.write(cabecera + consejo)

    return base


def exportar_workflows_comfy(resultado: dict, base: str, modelo: str) -> int:
    """Escribe workflows/ con los .json ComfyUI (formato UI) del dataset,
    cableados al `modelo` local elegido: loader por arquitectura, CFG/pasos/
    sampler de su familia y resolución del latent según el RATIO de cada toma.

    Salen DOS variantes (se cargan en ComfyUI con Load/arrastrar):
      • individuales/NN_toma.json — una toma por workflow.
      • LOTE_<ratio>.json — TODAS las tomas de ese ratio en un canvas
        (loaders compartidos, una rama por toma): un Queue = lote entero.
    Cada SaveImage lleva el nombre de la toma → la imagen generada empareja
    sola con su caption (01_..., 02_...).

    Solo tiene sentido con modelos ComfyUI locales (el caller decide, según
    la plataforma destino elegida). Devuelve el nº de tomas exportadas.
    """
    from config import comfy_workflow_params
    from modules.comfy_export import (
        construir_workflow_comfy,
        construir_workflow_comfy_lote,
    )

    dir_wf = os.path.join(base, "workflows")
    dir_ind = os.path.join(dir_wf, "individuales")
    os.makedirs(dir_ind, exist_ok=True)

    n = 0
    por_ratio: dict = {}
    for item in resultado.get("dataset", []):
        ratio = (item.get("ratio") or "").strip()
        wf = construir_workflow_comfy(
            pos=item.get("prompt", ""),
            neg=item.get("negative", "") or "",
            modelo=modelo,
            ratio=ratio,
            save_prefix=item.get("filename") or "G-Prompt-Studio",
            caption=item.get("caption", ""),
        )
        with open(os.path.join(dir_ind, f"{item['filename']}.json"),
                  "w", encoding="utf-8") as f:
            json.dump(wf, f, ensure_ascii=False, indent=2)
        por_ratio.setdefault(ratio, []).append({
            "pos": item.get("prompt", ""),
            "neg": item.get("negative", "") or "",
            "save_prefix": item.get("filename") or "G-Prompt-Studio",
            "caption": item.get("caption", ""),
        })
        n += 1

    # Un LOTE por ratio (si tiene 2+ tomas): un solo Queue genera el grupo.
    lotes = []
    for ratio, items in sorted(por_ratio.items()):
        if len(items) < 2:
            continue
        wf = construir_workflow_comfy_lote(items, modelo, ratio=ratio)
        nombre = f"LOTE_{(ratio or 'libre').replace(':', 'x')}.json"
        with open(os.path.join(dir_wf, nombre), "w", encoding="utf-8") as f:
            json.dump(wf, f, ensure_ascii=False, indent=2)
        lotes.append(f"{nombre} ({len(items)} tomas)")

    # LEEME con las instrucciones y la chuleta CLIP/VAE del modelo.
    p = comfy_workflow_params(modelo)
    if p["arch"] == "unet":
        chuleta = (f"CLIP: {p.get('clip') or '(elígelo en ComfyUI)'}\n"
                   f"   VAE:  {p.get('vae') or '(elígelo en ComfyUI)'}\n")
    else:
        chuleta = "CLIP y VAE van integrados en el checkpoint (no hay loaders aparte).\n"
    lotes_txt = ("\n".join(f"  • {x}" for x in lotes)) if lotes else "  (ninguno)"
    with open(os.path.join(dir_wf, "LEEME_WORKFLOWS.txt"), "w", encoding="utf-8") as f:
        f.write(
            f"WORKFLOWS ComfyUI DEL DATASET — modelo: {modelo}\n"
            f"{'=' * 60}\n\n"
            f"Ajustes: {p['sampler']}/{p['scheduler']} · CFG {p['cfg']} · "
            f"{p['steps']} pasos · resolución según el ratio de cada toma.\n\n"
            f"DOS FORMAS DE USARLOS:\n\n"
            f"A) LOTES POR RATIO (recomendado — un Queue genera el grupo):\n"
            f"{lotes_txt}\n"
            f"   Arrastra el LOTE al canvas de ComfyUI: el modelo se carga\n"
            f"   UNA vez y cada toma tiene su rama con su prompt/negative.\n\n"
            f"B) individuales/ — un .json por toma, por si quieres generar\n"
            f"   (o retocar) una toma suelta.\n\n"
            f"PASOS:\n"
            f"1. Arrastra el .json al canvas (o menú Load).\n"
            f"2. Verifica el modelo en el loader (si el nombre no coincide\n"
            f"   exacto con tu fichero, elígelo en el desplegable).\n"
            f"   {chuleta}"
            f"3. Queue Prompt.\n\n"
            f"Cada SaveImage lleva el NOMBRE de su toma (01_..., 02_...):\n"
            f"la imagen generada empareja sola con su caption de captions/\n"
            f"para entrenar el LoRA.\n"
        )
    return n


_CONSEJOS_PERSONAJE = """GUÍA OFICIAL SEAART — DATASET PARA LoRA DE PERSONAJE
====================================================
(fuente: docs.seaart.ai → Entrenamiento de LoRA avanzado)

• CANTIDAD: 25-40 imágenes en total. Más imágenes ≠ mejor (riesgo de
  LoRA sobreentrenada). Este generador da hasta 50 vistas: genera de
  sobra y ELIGE las mejores (el botón ⚖ Equilibrado cura una selección).
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

• CANTIDAD: 20-40 imágenes de SUJETOS VARIADOS (este generador da hasta 50:
  genera de sobra y ELIGE las mejores).
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
  solo una cara (este generador da hasta 50 vistas: genera de sobra y ELIGE).
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
  (este generador da hasta 50 encuadres: genera de sobra y ELIGE).
• SIN PERSONAS: un LoRA de paisaje no debe incluir gente (el negative ya la excluye).
• RESOLUCIÓN: 1024x1024 (o formato panorámico) para SDXL / Flux / SD 3.5.
• CAPTIONS: describe el encuadre, la luz y el clima, NO el bioma en sí.
• REGLA DE ORO: la identidad del lugar/bioma va en el TRIGGER WORD (no la
  etiquetes); las condiciones (luz, clima, encuadre) SÍ van en la caption.
"""

_CONSEJOS_RATIOS = """
ASPECT RATIO POR PLANO (clave en Z-Image y modelos modernos)
------------------------------------------------------------
Cada prompt trae un "RATIO SUGERIDO". Úsalo al generar en SeaArt:
• 1:1  (cuadrado)   → retratos cerrados, primeros planos, detalle, still life.
• 9:16 (vertical)   → cuerpo entero, figuras de pie, torres/castillos.
• 3:2  (horizontal) → paisajes/escenas abiertas, batallas, abstracto, vehículos.
Usar el ratio coherente con el plano mejora el encuadre y evita recortes raros.
"""

_CONSEJOS_NSFW = """DATASET PARA LoRA DE PERSONAJE NSFW (18+)
=========================================
(base: guía oficial SeaART de LoRA de personaje + reglas de contenido adulto)

⚠️ SOLO CONTENIDO ADULTO (18+):
• El sujeto es SIEMPRE un adulto; el negative de cada imagen ya bloquea
  rasgos de menor. NO lo quites.
• Si el personaje se parece a una persona REAL, necesitas su consentimiento.
• Revisa las normas de tu plataforma: en SeaArt el contenido NSFW requiere
  activar el modo NSFW de la cuenta y el LoRA quedará marcado como tal.
  Otras plataformas (Civitai, Tensor.Art) tienen reglas propias.

• CANTIDAD: 25-40 imágenes. Este generador da 50 tomas en 3 niveles
  (lencería → sugerente → desnudo artístico): genera de sobra y ELIGE.
• IDENTIDAD: la cara y el cuerpo se aprenden igual que en un LoRA normal —
  el ⚖ Equilibrado prioriza lencería + implied (más control de identidad)
  y deja los desnudos más explícitos a tu elección.
• VESTUARIO: aquí NO va en la descripción canónica (varía por toma). Los
  detalles de coherencia (tatuajes, lunares) hacen el papel de la "ropa".
• MEZCLA RECOMENDADA: si quieres un avatar que también funcione vestido,
  entrena con este dataset + el de Personaje (mismo trigger) o usa dos
  LoRAs separados (ohwx_ana + ohwx_ana_nsfw) y actívalos según la escena.
• RESOLUCIÓN: 1024x1024 para SDXL / Flux / SD 3.5 (512x512 para SD 1.5).
• CAPTIONS: describe vestuario, pose y luz — NO la identidad (esa va en el
  trigger). BLIP para fotorrealismo; Deepbooru para anime.
"""

CONSEJOS_LORA_POR_TIPO = {
    "Personaje": _CONSEJOS_PERSONAJE + _CONSEJOS_RATIOS,
    "Estilo": _CONSEJOS_ESTILO + _CONSEJOS_RATIOS,
    "Objeto": _CONSEJOS_OBJETO + _CONSEJOS_RATIOS,
    "Paisaje": _CONSEJOS_PAISAJE + _CONSEJOS_RATIOS,
    "NSFW": _CONSEJOS_NSFW + _CONSEJOS_RATIOS,
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
