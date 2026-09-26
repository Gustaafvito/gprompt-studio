"""Las etiquetas en cursiva ya no se comen su última letra.

CTkLabel crea su etiqueta interna de Tk con padx=0 y la mide sin contar la
inclinación de la cursiva, así que el final de la última letra se corta.
Visto en el barrido del 25-sep-2026: «Versión 1.1.C» en Acerca de, «persona
rea» y «luz natura» en la Guía de estilos, los ejemplos del A/B testing… Son
37 etiquetas en cursiva; se arregla aquí una vez en vez de en cada una.
"""
import customtkinter as ctk

# Lo justo para la inclinación de la última letra a los tamaños de la app.
MARGEN_CURSIVA = 3


def es_cursiva(fuente):
    try:
        if isinstance(fuente, ctk.CTkFont):
            return fuente.cget("slant") == "italic"
        if isinstance(fuente, tuple):
            return "italic" in fuente
    except Exception:
        pass
    return False


def instalar_margen_cursiva():
    """Parchea CTkLabel: si la fuente es cursiva y no se pidió padx, añade el margen."""
    original = ctk.CTkLabel.__init__
    if getattr(original, "_margen_cursiva", False):
        return

    def __init__(self, *args, **kwargs):
        if "padx" not in kwargs and es_cursiva(kwargs.get("font")):
            kwargs["padx"] = MARGEN_CURSIVA
        original(self, *args, **kwargs)

    __init__._margen_cursiva = True
    ctk.CTkLabel.__init__ = __init__
