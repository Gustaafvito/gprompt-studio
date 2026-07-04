"""Panel lateral acoplado (drawer) — Historial / Favoritos / Estrellas.

Se superpone al borde derecho de la ventana principal con place(), sin
tocar el layout pack existente. Es la versión COMPACTA de acceso rápido:
buscar y cargar un prompt sin abrir ventanas. Las ventanas completas
(Datos → Historial/Favoritos/Estrellas) siguen existiendo para gestión a
fondo (limpiar todo, filtros por modo, agrupación por fechas).

Uso: toggle_panel(app)  — Ctrl+B, menú UI y command palette.
El panel se destruye al cerrar y se recrea al abrir: así siempre está
fresco de datos y de tema (no hay que repintarlo en cmd_toggle_tema).
"""

import logging

import customtkinter as ctk

from config import get_theme_colors
from modules import paleta as P
from modules.i18n import tr

logger = logging.getLogger(__name__)

ANCHO_PANEL = 400
PAGE_SIZE = 30

# (clave colección en app.store, etiqueta ES para el segmented)
_COLECCIONES = (
    ("historial", "Historial"),
    ("favoritos", "Favoritos"),
    ("estrellas", "Estrellas"),
)


def filtrar_entradas(datos: list, termino: str) -> list:
    """[(idx_real, entrada)] cuyo texto contiene `termino` (case-insensitive).

    Puro (sin UI) para poder testearlo. Con término vacío devuelve todo.
    """
    termino = (termino or "").strip().lower()
    resultado = []
    for i, e in enumerate(datos):
        if not termino:
            resultado.append((i, e))
            continue
        texto = " ".join([
            str(e.get("contenido", "")), str(e.get("estilos", "")),
            str(e.get("modo", "")), str(e.get("fecha", "")),
            str(e.get("personaje", "")), str(e.get("lora", "")),
            str(e.get("plataforma", "")), str(e.get("nota", "")),
        ]).lower()
        if termino in texto:
            resultado.append((i, e))
    return resultado


def toggle_panel(app) -> None:
    """Abre o cierra el panel lateral (Ctrl+B)."""
    panel = getattr(app, "_panel_lateral", None)
    if panel is not None and panel.winfo_exists():
        panel.destroy()
        app._panel_lateral = None
        return
    app._panel_lateral = PanelLateral(app)
    try:
        app._sesion_log("🗂 Abrió el panel lateral")
    except Exception as e:
        logger.debug(f"[silent] {e}")


class PanelLateral(ctk.CTkFrame):
    def __init__(self, app):
        self.app = app
        is_light = ctk.get_appearance_mode() == "Light"
        c = get_theme_colors(is_light)
        self._c = c
        self._is_light = is_light
        super().__init__(
            app, width=ANCHO_PANEL, corner_radius=0,
            fg_color=c["panel_bg"],
            border_width=1, border_color=c["combo_border"],
        )
        self._coleccion = "historial"
        self._visible = PAGE_SIZE
        self._debounce = None
        self._construir()
        # Drawer pegado al borde derecho, alto completo.
        self.place(relx=1.0, rely=0.0, relheight=1.0, anchor="ne")
        self.lift()
        self._entry.focus_set()  # Escape y búsqueda operan de inmediato

    # ── UI ────────────────────────────────────────────────────────
    def _construir(self):
        c = self._c

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=P.ESPACIO_M, pady=(P.ESPACIO_M, P.ESPACIO_XS))
        ctk.CTkLabel(hdr, text=tr("🗂 Panel lateral"),
                     font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold"),
                     text_color=c["panel_text"]).pack(side="left")
        ctk.CTkButton(hdr, text="✕", width=28, height=24,
                      **P.estilo_boton(P.BTN_NEUTRO),
                      command=lambda: toggle_panel(self.app)).pack(side="right")

        # Pestañas de colección
        self._disp2col = {tr(lbl): col for col, lbl in _COLECCIONES}
        seg = ctk.CTkSegmentedButton(
            self, values=list(self._disp2col),
            command=self._on_tab,
            font=ctk.CTkFont(size=P.FUENTE_CUERPO),
        )
        seg.set(tr(_COLECCIONES[0][1]))
        seg.pack(fill="x", padx=P.ESPACIO_M, pady=(0, P.ESPACIO_S))

        # Búsqueda con debounce
        fila_busq = ctk.CTkFrame(self, fg_color="transparent")
        fila_busq.pack(fill="x", padx=P.ESPACIO_M, pady=(0, P.ESPACIO_S))
        self._entry = ctk.CTkEntry(
            fila_busq, placeholder_text=tr("Buscar por texto, estilo, fecha..."),
            height=30)
        self._entry.pack(side="left", fill="x", expand=True, padx=(0, P.ESPACIO_XS))
        self._entry.bind("<KeyRelease>", self._on_buscar)
        # Escape cierra el panel cuando el foco está en la búsqueda. Se enlaza
        # aquí (no bind_all: CustomTkinter lo prohíbe en un CTkFrame). Fuera de
        # la búsqueda, se cierra con la ✕ o repitiendo Ctrl+B.
        self._entry.bind("<Escape>", self._on_escape)
        ctk.CTkButton(fila_busq, text="✕", width=30, height=30,
                      **P.estilo_boton(P.BTN_NEUTRO),
                      command=self._limpiar_busqueda).pack(side="left")

        self._lbl_contador = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=P.FUENTE_HINT),
            text_color=c["muted_text"], anchor="w")
        self._lbl_contador.pack(fill="x", padx=P.ESPACIO_M)

        self._lista = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._lista.pack(fill="both", expand=True,
                         padx=P.ESPACIO_S, pady=(P.ESPACIO_XS, P.ESPACIO_S))

        self._refrescar()

    # ── Eventos ───────────────────────────────────────────────────
    def _on_escape(self, _e=None):
        if self.winfo_exists():
            toggle_panel(self.app)

    def _on_tab(self, valor):
        self._coleccion = self._disp2col.get(valor, "historial")
        self._visible = PAGE_SIZE
        self._refrescar()

    def _on_buscar(self, _e=None):
        if self._debounce:
            self.after_cancel(self._debounce)
        self._visible = PAGE_SIZE
        self._debounce = self.after(300, self._refrescar)

    def _limpiar_busqueda(self):
        self._entry.delete(0, "end")
        self._visible = PAGE_SIZE
        self._refrescar()

    # ── Render ────────────────────────────────────────────────────
    def _refrescar(self):
        for w in self._lista.winfo_children():
            w.destroy()

        datos = getattr(self.app.store, self._coleccion, []) or []
        filtrados = filtrar_entradas(datos, self._entry.get())
        visibles = min(self._visible, len(filtrados))
        self._lbl_contador.configure(
            text=tr('{0} de {1} mostrados ({2} total){3}').format(
                visibles, len(filtrados), len(datos), ""))

        if not filtrados:
            ctk.CTkLabel(self._lista, text=tr("(sin entradas)"),
                         text_color=self._c["muted_text"]).pack(pady=P.ESPACIO_XL)
            return

        for idx_real, entrada in filtrados[:visibles]:
            self._card(entrada, idx_real)

        restantes = len(filtrados) - visibles
        if restantes > 0:
            ctk.CTkButton(
                self._lista,
                text=tr('▼ Mostrar {0} más  ({1} restantes)').format(
                    min(PAGE_SIZE, restantes), restantes),
                height=28, **P.estilo_boton(P.BTN_SECUNDARIO),
                command=self._mostrar_mas).pack(fill="x", padx=2, pady=(P.ESPACIO_S, P.ESPACIO_XS))

    def _mostrar_mas(self):
        self._visible += PAGE_SIZE
        self._refrescar()

    def _card(self, entrada, idx):
        c = self._c
        card_bg = "#f0f0f0" if self._is_light else "#1a1a2e"
        card = ctk.CTkFrame(self._lista, fg_color=card_bg, corner_radius=6)
        card.pack(fill="x", pady=3, padx=2)

        fecha = (entrada.get("fecha") or "—")[:16]
        modo = entrada.get("modo", "imagen")
        plat = entrada.get("plataforma", "")
        meta = f"{fecha}  ·  {modo}" + (f"  ·  {plat[:18]}" if plat else "")
        ctk.CTkLabel(card, text=meta, font=ctk.CTkFont(size=P.FUENTE_HINT),
                     text_color=c["muted_text"], anchor="w"
                     ).pack(fill="x", padx=P.ESPACIO_S, pady=(P.ESPACIO_XS, 0))

        nota = entrada.get("nota", "") if self._coleccion == "estrellas" else ""
        if nota:
            ctk.CTkLabel(card, text=f"🌟 {nota[:80]}",
                         font=ctk.CTkFont(size=P.FUENTE_PEQUENA, weight="bold"),
                         text_color=P.TXT_ACENTO, wraplength=ANCHO_PANEL - 60,
                         justify="left", anchor="w"
                         ).pack(fill="x", padx=P.ESPACIO_S)

        contenido = entrada.get("contenido", "")
        preview = contenido[:150].replace("\n", " ") + ("…" if len(contenido) > 150 else "")
        ctk.CTkLabel(card, text=preview, wraplength=ANCHO_PANEL - 60, justify="left",
                     font=ctk.CTkFont(size=P.FUENTE_PEQUENA),
                     text_color=c["panel_text"], anchor="w"
                     ).pack(fill="x", padx=P.ESPACIO_S, pady=(2, P.ESPACIO_XS))

        fila = ctk.CTkFrame(card, fg_color="transparent")
        fila.pack(fill="x", padx=P.ESPACIO_S, pady=(0, P.ESPACIO_XS))

        def _cargar(cont=contenido):
            self.app.actualizar_salida(cont)
            self.app.set_estado(tr("📋 Prompt cargado."), P.TXT_INFO)

        def _copiar(cont=contenido):
            try:
                import pyperclip
                pyperclip.copy(cont)
                self.app.set_estado(tr('📋 {0} caracteres copiados').format(len(cont)), P.TXT_OK)
            except Exception as _e:
                self.app.set_estado(tr('❌ No se pudo copiar: {0}').format(_e), P.TXT_ERROR)

        def _borrar(i=idx):
            from tkinter import messagebox
            tipo = {"historial": "entrada del historial",
                    "favoritos": "favorito",
                    "estrellas": "estrella"}.get(self._coleccion, "entrada")
            if messagebox.askyesno(tr("Confirmar"),
                                   tr('¿Borrar este {0}?').format(tipo),
                                   parent=self.app):
                self.app.store.borrar_entrada(self._coleccion, i)
                self._refrescar()

        ctk.CTkButton(fila, text=tr("Cargar"), width=70, height=24,
                      font=ctk.CTkFont(size=P.FUENTE_PEQUENA),
                      **P.estilo_boton(P.BTN_EXITO),
                      command=_cargar).pack(side="left", padx=(0, 3))
        ctk.CTkButton(fila, text="📋", width=32, height=24,
                      font=ctk.CTkFont(size=P.FUENTE_PEQUENA),
                      **P.estilo_boton(P.BTN_SECUNDARIO),
                      command=_copiar).pack(side="left", padx=3)
        ctk.CTkButton(fila, text="🗑", width=32, height=24,
                      font=ctk.CTkFont(size=P.FUENTE_PEQUENA),
                      fg_color=P.BTN_PELIGRO, hover_color=P.BTN_PELIGRO_HOVER,
                      command=_borrar).pack(side="right")
