"""Exportador de workflows ComfyUI en FORMATO UI (nodes[] + links[]).

Módulo PURO (sin customtkinter) extraído de tools_analysis para poder
reutilizarlo fuera del editor:
  • Botón 🔧 Comfy del footer (tools_analysis delega aquí).
  • Dataset de avatar/LoRA: carpeta workflows/ con un .json por toma,
    cableado al modelo ComfyUI destino (avatar_generator).

El formato UI es el ÚNICO que ComfyUI acepta al hacer Load/Paste en el
canvas (el formato API por id no lo acepta). Loader por arquitectura y
CFG/pasos/sampler por familia — ver config.comfy_workflow_params.
"""

# Definición de slots (inputs/outputs) por tipo de nodo, para serializar
# al formato UI de ComfyUI (el que acepta Load/Paste en el canvas).
COMFY_NODE_SLOTS = {
    "CheckpointLoaderSimple": ([], [("MODEL", "MODEL"), ("CLIP", "CLIP"), ("VAE", "VAE")]),
    "UNETLoader":   ([], [("MODEL", "MODEL")]),
    "CLIPLoader":   ([], [("CLIP", "CLIP")]),
    "VAELoader":    ([], [("VAE", "VAE")]),
    "LoraLoader":   ([("model", "MODEL"), ("clip", "CLIP")], [("MODEL", "MODEL"), ("CLIP", "CLIP")]),
    "CLIPTextEncode": ([("clip", "CLIP")], [("CONDITIONING", "CONDITIONING")]),
    "EmptyLatentImage": ([], [("LATENT", "LATENT")]),
    "KSampler":     ([("model", "MODEL"), ("positive", "CONDITIONING"),
                      ("negative", "CONDITIONING"), ("latent_image", "LATENT")],
                     [("LATENT", "LATENT")]),
    "VAEDecode":    ([("samples", "LATENT"), ("vae", "VAE")], [("IMAGE", "IMAGE")]),
    "SaveImage":    ([("images", "IMAGE")], []),
    # Impact Pack (retoque de caras/ojos). bbox_detector viene del provider.
    "UltralyticsDetectorProvider": ([], [("BBOX_DETECTOR", "BBOX_DETECTOR"),
                                         ("SEGM_DETECTOR", "SEGM_DETECTOR")]),
    "FaceDetailer": ([("image", "IMAGE"), ("model", "MODEL"), ("clip", "CLIP"),
                      ("vae", "VAE"), ("positive", "CONDITIONING"),
                      ("negative", "CONDITIONING"), ("bbox_detector", "BBOX_DETECTOR")],
                     [("image", "IMAGE"), ("cropped_refined", "IMAGE"),
                      ("cropped_enhanced_alpha", "IMAGE"), ("mask", "MASK"),
                      ("detailer_pipe", "DETAILER_PIPE"), ("cnet_images", "IMAGE")]),
}

# Semilla FIJA para los datasets: todas las tomas usan la misma → la
# identidad del personaje es consistente entre ángulos (misma "persona",
# distinta pose). Con "fixed" no se randomiza en cada Queue. En los LOTES
# hay un nodo 'seed (todos)' para cambiarla y re-rolar todo el grupo.
SEED_DATASET = 42

# Resolución del latent por aspect ratio (~1MP, múltiplos de 64: los
# tamaños estándar de SDXL/Flux/Z-Image). Fallback: 1024x1024.
RESOLUCION_POR_RATIO = {
    "1:1":  (1024, 1024),
    "2:3":  (832, 1216),
    "3:2":  (1216, 832),
    "3:4":  (896, 1152),
    "4:3":  (1152, 896),
    "9:16": (768, 1344),
    "16:9": (1344, 768),
}


def _add_loaders(A, add, p, fichero, lora):  # noqa: N803
    """Añade los nodos de carga (por arquitectura + LoRA opcional) a `A`.
    Devuelve (model_src, clip_src, vae_src) como tuplas (idx_nodo, slot)."""
    if p["arch"] == "unet":
        i_model = add("UNETLoader", [fichero, "default"])
        i_clip = add("CLIPLoader", [p.get("clip", ""), p.get("clip_type", "stable_diffusion")])
        i_vae = add("VAELoader", [p.get("vae", "")])
        model_src, clip_src, vae_src = (i_model, 0), (i_clip, 0), (i_vae, 0)
    else:
        i_check = add("CheckpointLoaderSimple", [fichero])
        model_src, clip_src, vae_src = (i_check, 0), (i_check, 1), (i_check, 2)

    if lora:
        i_lora = add("LoraLoader", [lora + ".safetensors", 1.0, 1.0],
                     {"model": model_src, "clip": clip_src})
        model_src, clip_src = (i_lora, 0), (i_lora, 1)
    return model_src, clip_src, vae_src


def _detailer_widgets(p) -> list:
    """widgets_values estándar del FaceDetailer (Impact Pack), usando el
    sampler/scheduler del modelo y denoise 0.5 para el retoque."""
    return [512, "bbox", 1024, 0, "randomize", p["steps"], p["cfg"],
            p["sampler"], p["scheduler"], 0.5, 5, True, True, 0.5, 10, 3.0,
            "center-1", 0, 0.93, 0, 0.7, "False", 10, "", 1, False, 20]


def construir_workflow_comfy(pos: str, neg: str, modelo: str,
                             lora: str = "", ratio: str = "",
                             save_prefix: str = "G-Prompt-Studio",
                             caption: str = "", con_detailer: bool = False) -> dict:
    """Workflow ComfyUI (formato UI) para `modelo` con el prompt dado.

    `lora`: si se pasa, inserta un LoraLoader entre el cargador y el sampler.
    `ratio`: aspect ratio ("9:16", "3:2"…) → tamaño del latent
    (RESOLUCION_POR_RATIO); vacío o desconocido → 1024x1024.
    `save_prefix`: prefijo del fichero de salida (SaveImage) — con el nombre
    de la toma, la imagen generada empareja sola con su caption.
    `caption`: si se pasa, añade un nodo Note con el caption de entrenamiento.
    `con_detailer`: añade un FaceDetailer (Impact Pack) DESACTIVADO (bypass)
    tras la imagen, para retocar caras/ojos si salen mal (Ctrl+B para
    activarlo). Requiere Impact Pack instalado.
    """
    from config import comfy_workflow_params

    p = comfy_workflow_params(modelo)
    fichero = (modelo + ".safetensors") if modelo else "model.safetensors"
    ancho, alto = RESOLUCION_POR_RATIO.get((ratio or "").strip(), (1024, 1024))

    # ── Nodos abstractos: (tipo, widgets, conns{input: (idx_nodo, slot)}) ──
    # idx_nodo referencia la posición en esta lista.
    A = []  # noqa: N806 — lista de nodos abstractos

    def add(tipo, widgets, conns=None, mode=0):
        A.append({"type": tipo, "widgets": widgets, "conns": conns or {}, "mode": mode})
        return len(A) - 1

    model_src, clip_src, vae_src = _add_loaders(A, add, p, fichero, lora)

    i_latent = add("EmptyLatentImage", [ancho, alto, 1])
    i_pos = add("CLIPTextEncode", [pos], {"clip": clip_src})
    i_neg = add("CLIPTextEncode", [neg], {"clip": clip_src})
    i_ks = add("KSampler",
               [SEED_DATASET, "fixed", p["steps"], p["cfg"], p["sampler"], p["scheduler"], 1.0],
               {"model": model_src, "positive": (i_pos, 0), "negative": (i_neg, 0),
                "latent_image": (i_latent, 0)})
    i_dec = add("VAEDecode", [], {"samples": (i_ks, 0), "vae": vae_src})
    add("SaveImage", [save_prefix], {"images": (i_dec, 0)})

    notas = [(chuleta_texto(modelo), [40, -300])]
    if caption:
        notas.append((f"📝 CAPTION ({save_prefix}):\n\n{caption}", [1560, 40]))

    if con_detailer:
        # FaceDetailer bypasseado (mode 4): retoca caras/ojos al activarlo.
        i_bbox = add("UltralyticsDetectorProvider", ["bbox/face_yolov8m.pt"], mode=4)
        i_fd = add("FaceDetailer", _detailer_widgets(p),
                   {"image": (i_dec, 0), "model": model_src, "clip": clip_src,
                    "vae": vae_src, "positive": (i_pos, 0), "negative": (i_neg, 0),
                    "bbox_detector": (i_bbox, 0)}, mode=4)
        add("SaveImage", [save_prefix + "_detailed"], {"images": (i_fd, 0)}, mode=4)
        notas.append((
            "🩹 RETOQUE (Impact Pack) — DESACTIVADO por defecto (bypass gris).\n"
            "¿Cara/ojos/manos mal? Selecciona el FaceDetailer + su SaveImage,\n"
            "pulsa Ctrl+B para activarlos y vuelve a Queue: sale una versión\n"
            "'_detailed' corregida. Sube/baja 'denoise' (~0.5) según haga falta.",
            [1560, 300]))

    return serializar_workflow_ui(A, modelo, p.get("_comfy_familia") or "?", notas)


def construir_workflow_comfy_lote(items: list, modelo: str,
                                  lora: str = "", ratio: str = "") -> dict:
    """Workflow ComfyUI (formato UI) con VARIAS tomas en un solo canvas.

    `items`: lista de dicts {"pos", "neg", "save_prefix"} — todas las tomas
    comparten el ratio (un único EmptyLatentImage) y los LOADERS (el modelo
    se carga una sola vez); cada toma tiene su rama prompt/negative →
    KSampler → VAEDecode → SaveImage con su prefijo. Un solo Queue genera
    el lote entero.
    """
    from config import comfy_workflow_params

    p = comfy_workflow_params(modelo)
    fichero = (modelo + ".safetensors") if modelo else "model.safetensors"
    ancho, alto = RESOLUCION_POR_RATIO.get((ratio or "").strip(), (1024, 1024))

    A = []  # noqa: N806

    def add(tipo, widgets, conns=None, mode=0):
        A.append({"type": tipo, "widgets": widgets, "conns": conns or {}, "mode": mode})
        return len(A) - 1

    model_src, clip_src, vae_src = _add_loaders(A, add, p, fichero, lora)
    i_latent = add("EmptyLatentImage", [ancho, alto, 1])

    notas = [(chuleta_texto(modelo), [40, -300])]
    for j, it in enumerate(items):
        i_pos = add("CLIPTextEncode", [it.get("pos", "")], {"clip": clip_src})
        i_neg = add("CLIPTextEncode", [it.get("neg", "") or ""], {"clip": clip_src})
        i_ks = add("KSampler",
                   [SEED_DATASET, "fixed", p["steps"], p["cfg"], p["sampler"], p["scheduler"], 1.0],
                   {"model": model_src, "positive": (i_pos, 0), "negative": (i_neg, 0),
                    "latent_image": (i_latent, 0)})
        i_dec = add("VAEDecode", [], {"samples": (i_ks, 0), "vae": vae_src})
        prefijo = it.get("save_prefix") or "G-Prompt-Studio"
        add("SaveImage", [prefijo], {"images": (i_dec, 0)})
        # Caption de cada toma junto a su rama (columna de la derecha).
        cap = it.get("caption")
        if cap:
            notas.append((f"📝 {prefijo}:\n\n{cap}", [2000, 40 + j * 240]))

    notas.append((
        "🎚 CONTROL COMPARTIDO (arriba): 'seed (todos)', 'steps (todos)' y\n"
        "'cfg (todos)' mandan sobre TODOS los KSampler del lote.\n\n"
        "👤 CONSISTENCIA: todas las tomas comparten la MISMA semilla → mismo\n"
        "personaje, distinto ángulo. Si el personaje base no te convence,\n"
        "cambia SOLO 'seed (todos)' y re-rola el lote entero hasta dar con\n"
        "una cara que te guste; entonces genera todas las tomas con esa.",
        [40, -160]))
    wf = serializar_workflow_ui(A, modelo, p.get("_comfy_familia") or "?", notas)
    return anadir_control_compartido(wf, p["steps"], p["cfg"])


def construir_workflow_comfy_todas(items: list, modelo: str, lora: str = "") -> dict:
    """UN ÚNICO workflow con TODAS las tomas del dataset en un solo canvas:
    LOADERS compartidos (modelo/CLIP/VAE cargados una vez) + seed/steps/cfg
    compartidos, pero cada toma con su PROPIO tamaño (EmptyLatentImage según
    su ratio). Un solo Queue genera el dataset entero.

    `items`: lista de dicts {"pos", "neg", "save_prefix", "caption", "ratio"}.
    OJO: la semilla compartida da la MISMA identidad solo entre tomas del
    MISMO tamaño; entre ratios distintos la cara varía (limitación de la
    difusión). Aun así todo va en un workflow por comodidad.
    """
    from config import comfy_workflow_params

    p = comfy_workflow_params(modelo)
    fichero = (modelo + ".safetensors") if modelo else "model.safetensors"

    A = []  # noqa: N806

    def add(tipo, widgets, conns=None, mode=0):
        A.append({"type": tipo, "widgets": widgets, "conns": conns or {}, "mode": mode})
        return len(A) - 1

    model_src, clip_src, vae_src = _add_loaders(A, add, p, fichero, lora)

    notas = [(chuleta_texto(modelo), [40, -300])]
    for j, it in enumerate(items):
        ancho, alto = RESOLUCION_POR_RATIO.get((it.get("ratio") or "").strip(),
                                               (1024, 1024))
        i_latent = add("EmptyLatentImage", [ancho, alto, 1])
        i_pos = add("CLIPTextEncode", [it.get("pos", "")], {"clip": clip_src})
        i_neg = add("CLIPTextEncode", [it.get("neg", "") or ""], {"clip": clip_src})
        i_ks = add("KSampler",
                   [SEED_DATASET, "fixed", p["steps"], p["cfg"], p["sampler"], p["scheduler"], 1.0],
                   {"model": model_src, "positive": (i_pos, 0), "negative": (i_neg, 0),
                    "latent_image": (i_latent, 0)})
        i_dec = add("VAEDecode", [], {"samples": (i_ks, 0), "vae": vae_src})
        prefijo = it.get("save_prefix") or "G-Prompt-Studio"
        add("SaveImage", [prefijo], {"images": (i_dec, 0)})
        cap = it.get("caption")
        if cap:
            r = (it.get("ratio") or "1:1")
            notas.append((f"📝 {prefijo} [{r}]:\n\n{cap}", [2600, 40 + j * 240]))

    notas.append((
        "🎚 CONTROL COMPARTIDO (arriba): 'seed (todos)', 'steps (todos)' y\n"
        "'cfg (todos)' mandan sobre TODOS los KSampler del dataset.\n\n"
        "👤 CONSISTENCIA: la semilla es la misma para todas. Da el MISMO\n"
        "personaje entre tomas del MISMO tamaño; entre ratios distintos\n"
        "(1:1 vs 9:16...) la cara varía algo (así funciona la difusión).\n"
        "Cambia 'seed (todos)' para re-rolar el personaje base y cura las\n"
        "mejores 25-40 tomas para entrenar el LoRA.",
        [40, -160]))
    wf = serializar_workflow_ui(A, modelo, p.get("_comfy_familia") or "?", notas)
    return anadir_control_compartido(wf, p["steps"], p["cfg"])


def anadir_control_compartido(wf: dict, steps_val, cfg_val) -> dict:
    """Post-procesa un workflow serializado: añade tres PrimitiveNode
    ('seed (todos)', 'steps (todos)', 'cfg (todos)') conectados a los inputs
    seed/steps/cfg de TODOS los KSampler, para gobernar el lote entero desde
    un sitio. La semilla compartida es CLAVE para la consistencia de identidad
    (todas las tomas parten de la misma → mismo personaje, distinto ángulo).
    No hace nada si hay menos de 2 KSampler."""
    ks = [n for n in wf["nodes"] if n["type"] == "KSampler"]
    if len(ks) < 2:
        return wf
    lid = wf["last_link_id"]
    id_seed = wf["last_node_id"] + 1
    id_steps = wf["last_node_id"] + 2
    id_cfg = wf["last_node_id"] + 3
    links_seed, links_steps, links_cfg = [], [], []
    for k in ks:
        base = len(k["inputs"])
        for offset, (nombre, tipo, ids, acc) in enumerate((
                ("seed", "INT", id_seed, links_seed),
                ("steps", "INT", id_steps, links_steps),
                ("cfg", "FLOAT", id_cfg, links_cfg))):
            lid += 1
            k["inputs"].append({"name": nombre, "type": tipo, "link": lid,
                                "widget": {"name": nombre}})
            wf["links"].append([lid, ids, 0, k["id"], base + offset, tipo])
            acc.append(lid)

    def _prim(nid, nombre_widget, titulo, tipo, links, valor, x):
        return {
            "id": nid, "type": "PrimitiveNode", "title": titulo,
            "pos": [x, -560], "size": [230, 82], "flags": {},
            "order": 9990 + nid, "mode": 0, "inputs": [],
            "outputs": [{"name": tipo, "type": tipo, "links": links,
                         "slot_index": 0, "widget": {"name": nombre_widget}}],
            "properties": {"Run widget replace on values": False},
            "widgets_values": [valor, "fixed"],
            "color": "#323", "bgcolor": "#535",
        }
    wf["nodes"].append(_prim(id_seed, "seed", "seed (todos)", "INT",
                             links_seed, SEED_DATASET, 40))
    wf["nodes"].append(_prim(id_steps, "steps", "steps (todos)", "INT",
                             links_steps, steps_val, 300))
    wf["nodes"].append(_prim(id_cfg, "cfg", "cfg (todos)", "FLOAT",
                             links_cfg, cfg_val, 560))
    wf["last_node_id"] = id_cfg
    wf["last_link_id"] = lid
    return wf


def chuleta_texto(modelo: str) -> str:
    """Texto del nodo Note 🧩 CHULETA: qué elegir en los cargadores y
    ajustes recomendados, dentro del propio workflow."""
    from config import comfy_workflow_params
    p = comfy_workflow_params(modelo)
    L = [f"🧩 CHULETA — {modelo}", ""]  # noqa: N806
    if p["arch"] == "unet":
        L += ["Selecciona en los cargadores (si el nombre no coincide con",
              "tu fichero, elígelo en el desplegable de cada nodo):",
              f"• UNETLoader → {modelo}.safetensors",
              f"• CLIPLoader → {p.get('clip') or '(elige tu CLIP)'}   type: {p.get('clip_type')}",
              f"• VAELoader  → {p.get('vae') or '(elige tu VAE)'}"]
    else:
        L += ["Checkpoint (CLIP y VAE ya integrados):",
              f"• CheckpointLoaderSimple → {modelo}.safetensors"]
    L += ["",
          f"AJUSTES: {p['sampler']} / {p['scheduler']} · CFG {p['cfg']} · {p['steps']} pasos",
          "(cámbialos en el/los nodo KSampler)",
          "",
          "¿Manos/ojos/caras defectuosas? Tras el VAEDecode añade un",
          "FaceDetailer (Impact Pack) o reinyecta la imagen en img2img",
          "(VAEEncode → KSampler denoise ~0.4) para retocar."]
    return "\n".join(L)


def serializar_workflow_ui(abstractos: list, modelo: str, familia: str,
                           notas: list | None = None) -> dict:
    """Convierte la lista de nodos abstractos al formato UI de ComfyUI:
    nodes[] con pos/size/inputs/outputs/widgets_values + links[].

    `notas`: lista de (texto, [x, y]) → nodos Note nativos (amarillos), sin
    conexiones, para chuletas/captions dentro del propio canvas.
    """
    slots = COMFY_NODE_SLOTS
    # id real = índice + 1 (ComfyUI usa enteros >= 1)
    nodes_ui, links = [], []
    # outputs[idx][slot] -> lista de link_ids (se rellena al crear links)
    out_links = {i: {} for i in range(len(abstractos))}
    link_id = 0

    # 1) Primer pase: crear links a partir de las conexiones de cada input.
    #    Guardamos, por nodo, el link_id de cada input (para inputs[].link).
    in_link = {i: {} for i in range(len(abstractos))}
    for idx, nodo in enumerate(abstractos):
        in_defs = slots[nodo["type"]][0]
        for nombre_in, _tipo in in_defs:
            if nombre_in in nodo["conns"]:
                src_idx, src_slot = nodo["conns"][nombre_in]
                link_id += 1
                tipo_link = slots[abstractos[src_idx]["type"]][1][src_slot][1]
                links.append([link_id, src_idx + 1, src_slot, idx + 1,
                              in_defs.index((nombre_in, _tipo)), tipo_link])
                in_link[idx][nombre_in] = link_id
                out_links[src_idx].setdefault(src_slot, []).append(link_id)

    # 2) Segundo pase: construir cada nodo UI con posición en columnas.
    col_x, row_y = {}, {}
    for idx, nodo in enumerate(abstractos):
        in_defs, out_defs = slots[nodo["type"]]
        # Columna = profundidad topológica simple (0 si no tiene inputs).
        col = 0
        for nombre_in in nodo["conns"]:
            src_idx = nodo["conns"][nombre_in][0]
            col = max(col, col_x.get(src_idx, 0) + 1)
        col_x[idx] = col
        y = row_y.get(col, 0)
        row_y[col] = y + 220

        inputs_ui = [{"name": n, "type": t,
                      "link": in_link[idx].get(n)} for n, t in in_defs]
        outputs_ui = [{"name": n, "type": t,
                       "links": out_links[idx].get(s) or []}
                      for s, (n, t) in enumerate(out_defs)]
        nodes_ui.append({
            "id": idx + 1, "type": nodo["type"],
            "pos": [col * 360 + 40, y + 40], "size": [300, 200],
            "flags": {}, "order": idx, "mode": nodo.get("mode", 0),
            "inputs": inputs_ui, "outputs": outputs_ui,
            "properties": {"Node name for S&R": nodo["type"]},
            "widgets_values": nodo["widgets"],
        })

    # 3) Nodos Note (nativos, sin conexiones): chuleta + captions. Van con
    #    ids por encima de los de trabajo, en las posiciones indicadas.
    next_id = len(abstractos)
    for j, (texto, pos) in enumerate(notas or []):
        next_id += 1
        nodes_ui.append({
            "id": next_id, "type": "Note",
            "pos": pos, "size": [340, 200],
            "flags": {}, "order": len(abstractos) + j, "mode": 0,
            "inputs": [], "outputs": [],
            "properties": {"text": ""},
            "widgets_values": [texto],
            "color": "#432", "bgcolor": "#653",  # amarillo Note nativo
        })

    return {
        "last_node_id": next_id,
        "last_link_id": link_id,
        "nodes": nodes_ui,
        "links": links,
        "groups": [],
        "config": {},
        "extra": {"generado_por": "G-Prompt Studio", "modelo": modelo, "familia": familia},
        "version": 0.4,
    }
