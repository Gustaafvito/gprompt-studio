"""Centralized app state — todas las variables Tkinter en un solo lugar."""
import customtkinter as ctk
from typing import Optional


class AppState:
    def __init__(self):
        self.modo = ctk.StringVar(value="imagen")
        self.plataforma = ctk.StringVar(value="SeaArt / Tensor.Art")
        self.llm = ctk.StringVar(value="DeepSeek V3")
        self.nsfw = ctk.BooleanVar(value=False)
        self.traduccion = ctk.BooleanVar(value=True)
        self.brief = ctk.BooleanVar(value=False)
        self.duracion = ctk.StringVar(value="10s")
        self.ratio = ctk.StringVar(value="1:1")
        self.destino = ctk.StringVar(value="— Personal —")
        self.instrumental = ctk.BooleanVar(value=False)

        self.estilo_checks: dict[str, ctk.BooleanVar] = {}
        self.preset_vars: dict[str, ctk.BooleanVar] = {}
        self.preset_btns: dict[str, ctk.CTkButton] = {}

        self._cache_natural: Optional[bool] = None
        self._cache_natural_plat: Optional[str] = None
        self._cache_natural_modo: Optional[str] = None

    def invalidate_natural_cache(self):
        self._cache_natural = None

    def reset(self):
        for attr in ["estilo_checks", "preset_vars", "preset_btns"]:
            getattr(self, attr).clear()
        self.invalidate_natural_cache()
