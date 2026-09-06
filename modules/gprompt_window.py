"""
GPromptWindow: Widget personalizado que reemplaza el monkey-patching de CTkToplevel.
Elimina la necesidad de parchear globalmente la clase CTkToplevel.
"""
import logging

import customtkinter as ctk

logger = logging.getLogger(__name__)


class GPromptWindow(ctk.CTkToplevel):
    """Ventana personalizada con bring_to_front y atajos de teclado.

    Reemplaza el monkey-patching de CTkToplevel para evitar problemas
    de compatibilidad con actualizaciones de CustomTkinter.

    SINGLE-INSTANCE (por título): si se abre una ventana con un título que
    ya tiene otra ventana VIVA, la nueva se cierra sola y se enfoca la
    existente. Así todas las herramientas/paneles evitan duplicados sin
    tener que añadir lógica en cada sitio que las abre. Los títulos vacíos
    o el por defecto ("CTkToplevel") NO deduplican: toasts, splash y otras
    ventanas sin barra de título (overrideredirect) no se ven afectadas.
    """

    # Registro de ventanas VIVAS por título (clase entera).
    _por_titulo: dict = {}

    def __init__(self, master=None, **kwargs):
        # Estos atributos deben existir antes de super().__init__ porque CTk
        # puede llamar a self.title() durante su propia inicialización.
        self._titulo_registrado = None
        self._es_duplicado = False
        super().__init__(master, **kwargs)

        self.resizable(True, True)
        self.attributes("-toolwindow", False)

        self.after(50, self._bring_to_front)

        self.bind("<F11>", self._toggle_fullscreen)
        self.bind("<Escape>", self._exit_fullscreen)

    # ── Single-instance por título ─────────────────────────────────────
    def title(self, string=None):
        if string is None:
            return super().title()  # lectura
        # NO deduplicar títulos que no son "de la app":
        #  • vacío o el por defecto de CTk/tkinter,
        #  • el HEREDADO del master: al crear la ventana, CTk/tkinter le copia
        #    el título del root/padre (p.ej. "G-Prompt Studio v1.0"); eso NO es
        #    un título propio y no debe colisionar con otras ventanas.
        heredado = ""
        try:
            if self.master is not None:
                heredado = self.master.title()
        except Exception:
            heredado = ""
        if (not string or string in ("CTkToplevel", "CTk", "Tk")
                or string == heredado):
            return super().title(string)

        previa = GPromptWindow._por_titulo.get(string)
        es_dup = False
        if previa is not None and previa is not self:
            try:
                es_dup = bool(previa.winfo_exists())
            except Exception:
                es_dup = False

        if es_dup:
            # Ya hay una ventana viva con este título: enfocarla y cerrarse.
            try:
                self.withdraw()  # oculta la duplicada para que no parpadee
                previa.lift()
                previa.focus_force()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            self._es_duplicado = True
            # Destruir a los 60ms (no antes): CTk agenda callbacks a 5/10ms
            # (revert-withdraw y restaurar foco) que reventarían si la ventana
            # ya no existe. A los 60ms ya han corrido sobre la ventana viva
            # (oculta, sin parpadeo); los de 200/1000ms van blindados aparte.
            self.after(60, self._autocerrar_duplicado)
            return None

        # Registrar esta ventana bajo el título (liberando el anterior si lo tenía).
        ant = self._titulo_registrado
        if ant and GPromptWindow._por_titulo.get(ant) is self:
            GPromptWindow._por_titulo.pop(ant, None)
        GPromptWindow._por_titulo[string] = self
        self._titulo_registrado = string
        return super().title(string)

    def _autocerrar_duplicado(self):
        try:
            self.destroy()
        except Exception as _e:
            logger.debug(f"[silent] {_e}")

    # CTkToplevel programa varios callbacks diferidos (color de barra de
    # título, icono, min/max) que revientan con "bad window path name" si la
    # ventana se destruye antes de que corran — justo lo que hace una ventana
    # duplicada. Los blindamos: si la ventana es duplicada o ya no existe,
    # el callback se aborta en silencio.
    def _windows_set_titlebar_color(self, *a, **k):
        if self._es_duplicado or not self.winfo_exists():
            return
        return super()._windows_set_titlebar_color(*a, **k)

    def _revert_withdraw_after_windows_set_titlebar_color(self, *a, **k):
        if self._es_duplicado or not self.winfo_exists():
            return
        res = super()._revert_withdraw_after_windows_set_titlebar_color(*a, **k)
        # CTk hace withdraw()+deiconify() para pintar la barra de título, y ese
        # deiconify ocurre DESPUÉS del _bring_to_front que programa __init__,
        # dejando la ventana DETRÁS de la principal. Medido el 06-sep-2026 con
        # el diálogo de API keys (el usuario reportó que no salía delante):
        #
        #   2816 ms  _bring_to_front        <- nuestro lift()
        #   3628 ms  _revert_withdraw...    <- el deiconify de CTk, 800 ms despues
        #
        # Se vuelve a subir DESPUÉS de cada deiconify, que es el único momento
        # en que se sabe que CTk ya terminó de mostrarla.
        try:
            self.after(10, self._bring_to_front)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        return res

    def _windows_set_titlebar_icon(self, *a, **k):
        if self._es_duplicado or not self.winfo_exists():
            return
        return super()._windows_set_titlebar_icon(*a, **k)

    def _set_scaled_min_max(self, *a, **k):
        if not self.winfo_exists():
            return
        return super()._set_scaled_min_max(*a, **k)

    def destroy(self):
        # Liberar el título del registro al cerrarse.
        try:
            t = getattr(self, "_titulo_registrado", None)
            if t and GPromptWindow._por_titulo.get(t) is self:
                GPromptWindow._por_titulo.pop(t, None)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        return super().destroy()

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
