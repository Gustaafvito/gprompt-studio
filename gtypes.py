"""TypedDicts para tipado estático de estructuras de datos."""
from typing import TypedDict


class ModelSpecVideo(TypedDict):
    nota: float
    has_negative: bool
    has_audio: bool
    audio_desc: str
    duraciones: list
    ratios: list
    max_chars: int
    modos_gen: list
    best_for: str
    prompt_formula: str
    prompt_ejemplo: str
    limitaciones: str


class ModelSpecImagen(TypedDict):
    nota: float
    has_negative: bool
    is_natural: bool
    ratios: list
    max_chars: int
    modos_gen: list
    max_imagenes: int
    best_for: str
    prompt_formula: str
    prompt_ejemplo: str
    sampler_recomendado: str
    pasos: str
    cfg: str
    trigger_words: str
    limitaciones: str


class ModelSpecAudio(TypedDict):
    nota: float
    has_negative: bool
    has_lyrics: bool
    has_instrumental_toggle: bool
    usa_tags_estructurales: bool
    duracion_max_min: int
    max_chars_letra: int
    max_chars_estilo: int
    idiomas: list
    best_for: str
    prompt_formula: str
    prompt_ejemplo_estilo: str
    prompt_ejemplo_letra: str
    limitaciones: str


class PromptTemplate(TypedDict):
    modelos: list
    positive_base: str
    negative_base: str


class HistorialEntry(TypedDict):
    contenido: str
    fecha: str
    modo: str
    modelo: str
    plataforma: str


class FavoritoEntry(TypedDict):
    contenido: str
    fecha: str
    titulo: str


class PersonajeEntry(TypedDict):
    nombre: str
    descripcion: str


class LoRAEntry(TypedDict):
    nombre: str
    trigger: str
    descripcion: str
    familia: str


class PlantillaEntry(TypedDict):
    nombre: str
    modo: str
    plataforma: str
    modelo_img: str
    modelo_vid: str
    modelo_aud: str
    ratio: str
    estilos: list
    nsfw: bool
    destino: str
    brief: bool


class Preferencias(TypedDict):
    tema: str
    llm: str
