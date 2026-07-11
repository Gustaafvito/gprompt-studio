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
}

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


def construir_workflow_comfy(pos: str, neg: str, modelo: str,
                             lora: str = "", ratio: str = "") -> dict:
    """Workflow ComfyUI (formato UI) para `modelo` con el prompt dado.

    `lora`: si se pasa, inserta un LoraLoader entre el cargador y el sampler.
    `ratio`: aspect ratio ("9:16", "3:2"…) → tamaño del latent
    (RESOLUCION_POR_RATIO); vacío o desconocido → 1024x1024.
    """
    from config import comfy_workflow_params

    p = comfy_workflow_params(modelo)
    fichero = (modelo + ".safetensors") if modelo else "model.safetensors"
    ancho, alto = RESOLUCION_POR_RATIO.get((ratio or "").strip(), (1024, 1024))

    # ── Nodos abstractos: (tipo, widgets, conns{input: (idx_nodo, slot)}) ──
    # idx_nodo referencia la posición en esta lista.
    A = []  # noqa: N806 — lista de nodos abstractos

    def add(tipo, widgets, conns=None):
        A.append({"type": tipo, "widgets": widgets, "conns": conns or {}})
        return len(A) - 1

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

    i_latent = add("EmptyLatentImage", [ancho, alto, 1])
    i_pos = add("CLIPTextEncode", [pos], {"clip": clip_src})
    i_neg = add("CLIPTextEncode", [neg], {"clip": clip_src})
    i_ks = add("KSampler",
               [0, "randomize", p["steps"], p["cfg"], p["sampler"], p["scheduler"], 1.0],
               {"model": model_src, "positive": (i_pos, 0), "negative": (i_neg, 0),
                "latent_image": (i_latent, 0)})
    i_dec = add("VAEDecode", [], {"samples": (i_ks, 0), "vae": vae_src})
    add("SaveImage", ["G-Prompt-Studio"], {"images": (i_dec, 0)})

    return serializar_workflow_ui(A, modelo, p.get("_comfy_familia") or "?")


def serializar_workflow_ui(abstractos: list, modelo: str, familia: str) -> dict:
    """Convierte la lista de nodos abstractos al formato UI de ComfyUI:
    nodes[] con pos/size/inputs/outputs/widgets_values + links[]."""
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
            "flags": {}, "order": idx, "mode": 0,
            "inputs": inputs_ui, "outputs": outputs_ui,
            "properties": {"Node name for S&R": nodo["type"]},
            "widgets_values": nodo["widgets"],
        })

    return {
        "last_node_id": len(abstractos),
        "last_link_id": link_id,
        "nodes": nodes_ui,
        "links": links,
        "groups": [],
        "config": {},
        "extra": {"generado_por": "G-Prompt Studio", "modelo": modelo, "familia": familia},
        "version": 0.4,
    }
