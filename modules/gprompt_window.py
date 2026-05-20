"""
GPromptWindow: Widget personalizado que reemplaza el monkey-patching de CTkToplevel.
Elimina la necesidad de parchear globalmente la clase CTkToplevel.
"""
import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)


class GPromptWindow(ctk.CTkToplevel):
    """Ventana personalizada con bring_to_front y atajos de teclado.

    Reemplaza el monkey-patching de CTkToplevel para evitar problemas
    de compatibilidad con actualizaciones de CustomTkinter.
    """

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        self.resizable(True, True)
        self.attributes("-toolwindow", False)

        self.after(50, self._bring_to_front)

        self.bind("<F11>", self._toggle_fullscreen)
        self.bind("<Escape>", self._exit_fullscreen)

    def _bring_to_front(self):
        """Trae la ventana al frente sin bloquearla permanentemente."""
        try:
            if not self.winfo_exists():
                return
            self.lift()
            self.attributes("-topmost", True)
            self.after(250, lambda: self.attributes("-topmost", False) if self.winfo_exists() else None)
            try:
                self.focus_force()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        except Exception as e:
            logger.debug(f"GPromptWindow._bring_to_front: {e}")

    def _toggle_fullscreen(self, event=None):
        """Alterna pantalla completa."""
        try:
            actual = bool(self.attributes("-fullscreen"))
            self.attributes("-fullscreen", not actual)
        except Exception as e:
            logger.debug(f"GPromptWindow._toggle_fullscreen: {e}")
        return "break"

    def _exit_fullscreen(self, event=None):
        """Sale de pantalla completa si está activa."""
        try:
            if bool(self.attributes("-fullscreen")):
                self.attributes("-fullscreen", False)
                return "break"
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        return None

    def transient(self, master=None):
        """No-op: en Windows, transient() oculta los botones minimize/maximize
        de la ventana. Lo evitamos pero forzamos bring_to_front para que la
        ventana siga apareciendo al frente al crearse (que es lo que
        normalmente se buscaba con transient).
        """
        try:
            self.attributes("-toolwindow", False)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        self.after(60, self._bring_to_front)

    def set_transient(self, master=None):
        """Alias retrocompat — usa transient()."""
        self.transient(master)