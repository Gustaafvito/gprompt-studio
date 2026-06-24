"""Lógica pura de detección de modo y construcción de contexto.

Funciones sin dependencias de widget ni de estado Tk. Los wrappers
en CoreMixin leen las Tk vars y los combos, y delegan aquí.

Esto permite testear la lógica de negocio de forma aislada, sin
necesitar una instancia de la app.
"""
from config import (
    COMFY_TURBO_TOKENS,
    PLATAFORMAS_IMAGEN,
    PLATAFORMAS_VIDEO,
    es_separador,
    get_image_model_specs,
    get_model_specs,
)

_PLAT_CON_MODELOS = frozenset(("SeaArt / Tensor.Art", "ComfyUI / A1111 / Forge"))

# Nombres "de catálogo" históricos (referencia; todos quedan cubiertos por los
# tokens de COMFY_TURBO_TOKENS, definidos en config como fuente única).
_MODELOS_TURBO = ("Z Image Turbo", "Realities Edge XL Turbo V7", "SDXL Turbo", "FLUX.1 Schnell")


def is_natural_mode(modo: str, plataforma: str, modelo_imagen: str) -> bool:
    """Devuelve True si el modo activo usa lenguaje natural (no tags con pesos)."""
    if modo == "audio":
        return True
    if modo == "video":
        return PLATAFORMAS_VIDEO.get(plataforma, "natural") == "natural"
    if plataforma in _PLAT_CON_MODELOS:
        if modelo_imagen and not es_separador(modelo_imagen):
            specs = get_image_model_specs(modelo_imagen)
            if specs and specs.get("is_natural"):
                return True
    return PLATAFORMAS_IMAGEN.get(plataforma, "sd") == "natural"


def es_comfyui_turbo(plataforma: str, modelo: str) -> bool:
    """Detecta ComfyUI/A1111/Forge con un modelo Turbo (sin negative ni pesos)."""
    es_comfyui = any(x in plataforma for x in ("ComfyUI", "A1111", "Forge"))
    if not es_comfyui:
        return False
    modelo_l = (modelo or "").lower()
    return any(tok in modelo_l for tok in COMFY_TURBO_TOKENS)


def debe_mostrar_negatives(
    modo: str, plataforma: str, modelo_imagen: str, modelo_video: str
) -> bool:
    """Devuelve True si el modelo/plataforma activos soportan NEGATIVE PROMPT."""
    if modo == "audio":
        return False
    if modo == "video":
        specs = get_model_specs(modelo_video)
        if specs:
            return specs.get("has_negative", False)
        return PLATAFORMAS_VIDEO.get(plataforma, "sd") == "sd"
    if plataforma in _PLAT_CON_MODELOS:
        if modelo_imagen and not es_separador(modelo_imagen):
            if es_comfyui_turbo(plataforma, modelo_imagen):
                return False
            specs = get_image_model_specs(modelo_imagen)
            if specs:
                return specs.get("has_negative", False)
    return PLATAFORMAS_IMAGEN.get(plataforma, "sd") == "sd"


def contexto_loras_personaje(
    rasgos_loras: list,
    nombres_loras: list,
    pers_activo: str,
    sufijo_intro: str = "",
) -> str:
    """Bloque de contexto para que el LLM tenga en cuenta LoRA/Personaje activos."""
    if not nombres_loras and not pers_activo:
        return ""
    intro_quien = sufijo_intro or "el resultado"
    ctx = f"\n\n🎯 CONTEXTO IMPORTANTE — {intro_quien} DEBE encajar con:\n"
    if rasgos_loras:
        ctx += (
            f"  • PERSONAJE/ESTÉTICA del LoRA: {' | '.join(rasgos_loras)}.\n"
            f"    {intro_quien.capitalize()} debe PROTAGONIZAR o reflejar "
            f"este personaje/estética.\n"
        )
    elif nombres_loras:
        ctx += (
            f"  • LoRA(s) activo(s): {', '.join(nombres_loras)}. "
            f"{intro_quien.capitalize()} debe encajar con el ESTILO/personaje "
            f"que sugieren esos nombres.\n"
        )
    if pers_activo:
        ctx += (
            f"  • PERSONAJE adicional: {pers_activo}. "
            f"Inclúyelo en las escenas propuestas.\n"
        )
    ctx += (
        "  • Sugiere ESCENAS/ESCENARIOS/ACCIONES diversos donde ese "
        "personaje/estética encajen, NO descripciones del personaje en sí "
        "(esas las maneja el sistema aparte).\n"
    )
    return ctx


def contexto_modelo_para_ideas(modo: str, modelo: str, specs: dict | None) -> str:
    """Contexto del modelo activo para que las ideas encajen con su estilo."""
    if not modelo or es_separador(modelo):
        return ""
    txt = f"\n\nEl modelo destino es '{modelo}'."
    best = (specs or {}).get("best_for", "")
    if best:
        txt += f" Ideal para: {best[:220]}."
    if modo == "audio":
        txt += (
            " IMPORTANTE: las 3 ideas de canción deben ENCAJAR con el estilo "
            "musical y los puntos fuertes de este modelo (género, voz, "
            "instrumentación, mood), NO ideas genéricas. Aprovecha sus fortalezas."
        )
    else:
        txt += (
            " IMPORTANTE: las 3 ideas deben ENCAJAR con el estilo y los puntos "
            "fuertes de este modelo, NO ideas genéricas. Si el modelo es anime "
            "propón escenas/personajes anime; si es fotorrealista, escenas "
            "fotográficas reales; si es de fantasía, cómic o 3D, acorde a eso. "
            "Aprovecha sus fortalezas."
        )
    return txt
