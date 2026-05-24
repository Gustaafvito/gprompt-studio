"""Wrapper para CTkToolTip con monkey-patches defensivos.

CTkToolTip 0.9 tiene 2 bugs:
  1. `StringVar().set(None)` en __init__ (cuando message=None al crear)
     — Tkinter lo convierte en la cadena literal "None", que aparece
     como tooltip al pasar el ratón.
  2. Mismo bug en configure() al re-asignar mensaje.

Además los colores por defecto no son legibles en ambos temas
(claro/oscuro), por lo que aplicamos un par adaptativo al crear.

Uso desde main.py:
    from modules.tooltip import install_ctk_tooltip_patches
    install_ctk_tooltip_patches(logger)

Si CTkToolTip no está instalado, los patches no se aplican y la
app sigue arrancando (los tooltips simplemente no se muestran).
"""
import logging

logger = logging.getLogger(__name__)


def _colores_adaptativos(is_lt: bool) -> dict:
    """Devuelve un par de colores legibles según tema claro/oscuro."""
    if is_lt:
        return {
            "fg_color": "#f0f0f0",
            "text_color": "#111827",
            "bg_color": "#f0f0f0",
            "border_color": "#cbd5e1",
        }
    return {
        "fg_color": "#1a1a2e",
        "text_color": "#e5e7eb",
        "bg_color": "#1a1a2e",
        "border_color": "#3b82f6",
    }


def install_ctk_tooltip_patches(log: logging.Logger | None = None) -> bool:
    """Aplica los 2 monkey-patches a CTkToolTip si está disponible.

    Devuelve True si los patches se aplicaron, False si CTkToolTip
    no está instalado o si algún patch falló (no interrumpe arranque).
    """
    log = log or logger
    try:
        import customtkinter as ctk
        from CTkToolTip.ctk_tooltip import CTkToolTip as _Tooltip
    except ImportError:
        log.info("CTkToolTip no instalado, sin parche")
        return False

    try:
        _orig_init = _Tooltip.__init__

        def _safe_init(self, widget=None, message=None, **kwargs):
            if message is None:
                message = ""
            try:
                is_lt = ctk.get_appearance_mode().lower() == "light"
            except Exception:
                is_lt = False
            defaults = _colores_adaptativos(is_lt)
            for key, val in defaults.items():
                if key not in kwargs or kwargs.get(key) is None:
                    kwargs[key] = val
            kwargs.setdefault("padding", (10, 4))
            kwargs.setdefault("corner_radius", 6)
            kwargs.setdefault("border_width", 1)
            _orig_init(self, widget=widget, message=message, **kwargs)

        _Tooltip.__init__ = _safe_init

        _orig_configure = _Tooltip.configure

        def _safe_configure(self, message=None, **kwargs):
            if message is None:
                try:
                    message = self.messageVar.get()
                except Exception:
                    message = ""
                if message == "None":
                    message = ""
            _orig_configure(self, message=message, **kwargs)

        _Tooltip.configure = _safe_configure

        log.info("CTkToolTip patched OK (None coerced to empty, theme-adaptive colors)")
        return True
    except Exception as e:
        log.warning(f"CTkToolTip patch falló: {e}")
        return False
