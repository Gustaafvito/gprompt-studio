"""Atajos de teclado, ventana de ayuda de atajos, búsqueda global y tutorial.

Extraído de modules/core.py para reducir tamaño y agrupar responsabilidades.

Contiene:
  • _bind_shortcuts          — registra todos los bindings de teclado.
  • _cmd_cambiar_modo        — Alt+1/2/3 cambia entre imagen/vídeo/audio.
  • _cmd_exportar_rapido     — Ctrl+E.
  • _atajo_guardar_estrella  — Ctrl+Shift+S.
  • _cmd_buscar_global       — Ctrl+F, abre la ventana de búsqueda global.
  • _atajo_buscar_global     — wrapper con manejo de errores.
  • _atajo_traducir_idea     — Ctrl+Shift+T, traduce idea con DeepSeek.
  • _toggle_fullscreen       — F11.
  • _cerrar_popup_activo     — Escape, cierra Toplevel más reciente.
  • _cmd_abrir_loras         — Ctrl+L.
  • _cmd_mostrar_atajos      — Ctrl+?, ventana scrolleable con todos los atajos.
  • _abrir_busqueda_global   — ventana de búsqueda en historial/favoritos/estrellas.
  • _abrir_tutorial          — Ctrl+T, delega en modules.tutorial.
"""
import logging

import customtkinter as ctk
import pyperclip

from config import get_theme_colors
from modules.gprompt_window import GPromptWindow
from modules.tutorial import abrir_tutorial
from modules.windows import abrir_loras

logger = logging.getLogger("gprompt")


class AtajosAyudaMixin:
    def _bind_shortcuts(self):
        for widget in [self, self.txt_idea]:
            widget.bind("<Control-Return>",       lambda e: self.cmd_prompt())
            widget.bind("<Control-Shift-Return>", lambda e: self.cmd_variaciones())
            # ⚡ Quick Generate · Alt+Enter
            widget.bind("<Alt-Return>",           lambda e: self.cmd_prompt_quick())
            widget.bind("<Control-i>",            lambda e: self.cmd_ideas())
            widget.bind("<Control-1>",            lambda e: self._copiar("positivo"))
            widget.bind("<Control-2>",            lambda e: self._copiar("negativo"))
            widget.bind("<Control-Shift-a>",      lambda e: self.cmd_vision())
            widget.bind("<Control-r>",            lambda e: self._idea_aleatoria_historial())
            # ── MEJORA 4: Ctrl+D = duplicar prompt actual al historial ──
            widget.bind("<Control-d>",            lambda e: self._cmd_duplicar_a_historial())
            # ── TANDA 5: Atajos nuevos ──
            widget.bind("<Control-s>",            lambda e: (self._guardar_favorito(), "break")[1])
            widget.bind("<Control-Shift-S>",      lambda e: self._atajo_guardar_estrella())
            # Alt+1/2/3: cambiar modo
            widget.bind("<Alt-Key-1>",            lambda e: self._cmd_cambiar_modo("imagen"))
            widget.bind("<Alt-Key-2>",            lambda e: self._cmd_cambiar_modo("video"))
            widget.bind("<Alt-Key-3>",            lambda e: self._cmd_cambiar_modo("audio"))
            # Nuevos atajos (MEJORA #14) - con return "break" para evitar duplicados
            widget.bind("<Control-Shift-P>",      lambda e: (self.cmd_previsualizar(), "break")[1])
            widget.bind("<Control-e>",            lambda e: (self._cmd_exportar_rapido(), "break")[1])
            widget.bind("<Control-f>",            lambda e: self._atajo_buscar_global())
            widget.bind("<Control-l>",            lambda e: (self._cmd_abrir_loras(), "break")[1])
            widget.bind("<Control-p>",            lambda e: (self._cmd_grupo_personajes(), "break")[1])
            widget.bind("<Control-t>",            lambda e: (self._abrir_tutorial(), "break")[1])
            widget.bind("<Control-Shift-N>",      lambda e: (self._cmd_negative_builder(), "break")[1])
            widget.bind("<Control-h>",            lambda e: (self._cmd_modo_focus(), "break")[1])
            widget.bind("<Control-Shift-L>",      lambda e: (self._cmd_toggle_tema(), "break")[1])
            widget.bind("<Control-Shift-T>",      lambda e: (self._atajo_traducir_idea(), "break")[1])
        # Ctrl+V inteligente (detecta prompt o imagen en clipboard)
        self.bind("<Control-v>", self._pegar_inteligente_clipboard)
        # Ctrl+? = mostrar atajos
        self.bind("<Control-question>", lambda e: self._cmd_mostrar_atajos())
        # F11 y Escape para pantalla completa
        self.bind("<F11>", lambda e: self._toggle_fullscreen())
        self.bind("<Escape>", lambda e: self._cerrar_popup_activo())

    def _cmd_cambiar_modo(self, modo_destino):
        """Cambia el modo (imagen/video/audio) por atajo Alt+1/2/3."""
        if modo_destino not in ("imagen", "video", "audio"): return "break"
        try:
            self.modo_var.set(modo_destino)
            self._on_modo_cambio()
            etiqueta = {"imagen": "🎨 IMAGEN", "video": "🎬 VÍDEO", "audio": "🎵 AUDIO"}[modo_destino]
            self.set_estado(f"{etiqueta} (Alt+{1 if modo_destino == 'imagen' else 2 if modo_destino == 'video' else 3})", "#3498db")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        return "break"

    def _cmd_exportar_rapido(self):
        """Atajo Ctrl+E - Exportar rápidamente el prompt actual."""
        if hasattr(self, '_exportar'):
            self._exportar()
        elif hasattr(self, 'cmd_exportar'):
            self.cmd_exportar()
        else:
            self.set_estado("⚠️ Función de exportar no disponible", "#e67e22")
        return "break"

    def _atajo_guardar_estrella(self):
        """Atajo Ctrl+Shift+S - Guardar como estrella."""
        try:
            if hasattr(self, '_guardar_estrella'):
                self._guardar_estrella()
            else:
                self.set_estado("⚠️ Función no disponible", "#e74c3c")
        except Exception as e:
            self.set_estado(f"⚠️ Error: {e}", "#e74c3c")
        return "break"

    def _cmd_buscar_global(self):
        """Atajo Ctrl+F - Buscar en historial, favoritos, estrellas."""
        try:
            self._abrir_busqueda_global()
        except Exception as e:
            self.set_estado(f"⚠️ Error: {e}", "#e74c3c")
        return "break"

    def _atajo_buscar_global(self):
        """Helper para Ctrl+F con manejo de errores."""
        try:
            self._cmd_buscar_global()
        except Exception as e:
            self.set_estado(f"⚠️ Error búsqueda: {e}", "#e74c3c")
        return "break"

    def _atajo_traducir_idea(self):
        """Ctrl+Shift+T - Traduce el campo idea al inglés."""
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea:
            self.set_estado("⚠️ Escribe algo en la idea primero", "#e67e22")
            return "break"
        try:
            texto_traducido = self.deepseek.traducir(idea)
            if texto_traducido and texto_traducido != idea:
                self.txt_idea.delete("1.0", "end")
                self.txt_idea.insert("1.0", texto_traducido)
                self.set_estado("🌐 Idea traducida al inglés", "#3498db")
            else:
                self.set_estado("⚠️ No se pudo traducir", "#e67e22")
        except Exception as e:
            self.set_estado(f"⚠️ Error: {e}", "#e74c3c")
        return "break"

    def _toggle_fullscreen(self):
        """F11 - Alternar pantalla completa."""
        if hasattr(self, '_toggle_fullscreen_principal'):
            self._toggle_fullscreen_principal()
        else:
            current = self.attributes('-fullscreen')
            self.attributes('-fullscreen', not current)
        return "break"

    def _cerrar_popup_activo(self):
        """Escape - Cerrar popup activo (Toplevel más reciente)."""
        try:
            popups = [w for w in self.winfo_children() if isinstance(w, ctk.CTkToplevel)]
            if popups:
                popups[-1].destroy()
                return "break"
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        if self.attributes('-fullscreen'):
            self.attributes('-fullscreen', False)
            return "break"
        return "break"

    def _cmd_abrir_loras(self):
        """Atajo Ctrl+L - Abrir gestión de LoRAs."""
        try:
            abrir_loras(self)
        except Exception as e:
            self.set_estado(f"⚠️ Error al abrir LoRAs: {e}", "#e74c3c")
        return "break"

    def _cmd_mostrar_atajos(self):
        """Ctrl+? - Muestra ventana con todos los atajos de teclado.

        Buscador filtra por tecla o acción. Click sobre un atajo lo copia
        al portapapeles.
        """
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self)
        vent.title("⌨️ Atajos de teclado")
        vent.geometry("620x640")
        vent.transient(self)

        ctk.CTkLabel(vent, text="⌨️ Atajos de teclado",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(12, 5))
        ctk.CTkLabel(vent,
                     text="Click sobre un atajo para copiarlo · busca por tecla o acción",
                     font=ctk.CTkFont(size=10),
                     text_color=c["muted_text"]).pack(pady=(0, 6))

        search_row = ctk.CTkFrame(vent, fg_color="transparent")
        search_row.pack(fill="x", padx=15, pady=(0, 6))
        ctk.CTkLabel(search_row, text="🔍").pack(side="left", padx=(0, 6))
        entry_buscar = ctk.CTkEntry(search_row,
                                    placeholder_text="Filtrar por tecla o acción…",
                                    height=28)
        entry_buscar.pack(side="left", fill="x", expand=True)
        contador_var = ctk.StringVar(value="")
        ctk.CTkLabel(vent, textvariable=contador_var,
                     font=ctk.CTkFont(size=9),
                     text_color=c["muted_text"]).pack(anchor="w", padx=15)

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=5)

        atajos = [
            ("⚡ Generación", [
                ("Ctrl+Enter", "Generar prompt"),
                ("Ctrl+Shift+Enter", "Generar variaciones (x3)"),
                ("Alt+Enter", "Generación rápida (Quick)"),
                ("Ctrl+I", "Generar 3 ideas"),
            ]),
            ("✏️  Edición", [
                ("Ctrl+S", "Guardar como favorito"),
                ("Ctrl+Shift+S", "Guardar como estrella"),
                ("Ctrl+D", "Duplicar al historial"),
                ("Ctrl+Shift+P", "Previsualizar (Pollinations)"),
                ("Ctrl+Shift+T", "Traducir idea al inglés"),
                ("Ctrl+V", "Pegar inteligente"),
            ]),
            ("📋 Portapapeles", [
                ("Ctrl+1", "Copiar POSITIVE"),
                ("Ctrl+2", "Copiar NEGATIVE"),
                ("Ctrl+Shift+A", "Analizar imagen (Vision)"),
            ]),
            ("🎬 Navegación", [
                ("Alt+1", "Modo imagen"),
                ("Alt+2", "Modo vídeo"),
                ("Alt+3", "Modo audio"),
                ("Ctrl+R", "Idea aleatoria del historial"),
                ("Ctrl+T", "Abrir tutorial"),
            ]),
            ("🛠 Herramientas", [
                ("Ctrl+E", "Exportar rápido"),
                ("Ctrl+F", "Búsqueda global"),
                ("Ctrl+L", "Abrir LoRAs"),
                ("Ctrl+P", "Grupo de personajes"),
                ("Ctrl+Shift+N", "Constructor de negative"),
                ("Ctrl+H", "Modo Focus"),
                ("Ctrl+Shift+L", "Cambiar tema claro/oscuro"),
            ]),
            ("❓ Extra", [
                ("F11", "Pantalla completa"),
                ("Escape", "Cerrar popup / Salir de pantalla completa"),
                ("Ctrl+?", "Mostrar atajos"),
            ]),
        ]

        total = sum(len(lst) for _, lst in atajos)

        def _copiar_tecla(tecla):
            try:
                pyperclip.copy(tecla)
                self.set_estado(f"📋 '{tecla}' copiado", "#2ecc71")
            except Exception as _e:
                logger.debug(f"[silent] {_e}")

        def _refrescar():
            for w in scroll.winfo_children():
                w.destroy()
            termino = entry_buscar.get().strip().lower()
            mostrados = 0
            for categoria, lista in atajos:
                visibles = [
                    (t, a) for (t, a) in lista
                    if not termino or termino in t.lower() or termino in a.lower()
                ]
                if not visibles:
                    continue
                mostrados += len(visibles)
                frame_cat = ctk.CTkFrame(scroll, fg_color=c["fg_dark"], corner_radius=6)
                frame_cat.pack(fill="x", pady=4)
                ctk.CTkLabel(frame_cat, text=categoria,
                             font=ctk.CTkFont(size=11, weight="bold"),
                             text_color=c["hdr_text"]).pack(anchor="w", padx=10, pady=(6, 4))
                for tecla, accion in visibles:
                    row = ctk.CTkFrame(frame_cat, fg_color="transparent",
                                       cursor="hand2")
                    row.pack(fill="x", padx=10, pady=1)
                    lbl_tecla = ctk.CTkLabel(
                        row, text=tecla,
                        font=ctk.CTkFont(size=10, weight="bold"),
                        width=160, anchor="w", text_color="#3498db",
                        cursor="hand2",
                    )
                    lbl_tecla.pack(side="left")
                    lbl_accion = ctk.CTkLabel(
                        row, text=accion,
                        font=ctk.CTkFont(size=10),
                        anchor="w", text_color=c["panel_text"],
                        cursor="hand2",
                    )
                    lbl_accion.pack(side="left")
                    for w in (row, lbl_tecla, lbl_accion):
                        w.bind("<Button-1>", lambda _e, t=tecla: _copiar_tecla(t))

            if mostrados == 0:
                ctk.CTkLabel(scroll,
                             text=f"Sin atajos que coincidan con '{termino}'",
                             text_color=c["muted_text"]).pack(pady=30)
            sufijo = f" (filtrando '{termino}')" if termino else ""
            contador_var.set(f"{mostrados} de {total} atajos{sufijo}")

        pendiente = {"after_id": None}
        def _on_buscar(_e=None):
            if pendiente["after_id"]:
                try: vent.after_cancel(pendiente["after_id"])
                except Exception as _e2: logger.debug(f"[silent] {_e2}")
            pendiente["after_id"] = vent.after(150, _refrescar)
        entry_buscar.bind("<KeyRelease>", _on_buscar)

        _refrescar()
        ctk.CTkButton(vent, text="Cerrar", width=120, height=30,
                      command=vent.destroy).pack(pady=12)
        entry_buscar.focus_set()
        return "break"

    def _abrir_busqueda_global(self):
        """Abre ventana de búsqueda global en historial, favoritos, estrellas."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self)
        vent.title("🔍 Búsqueda global")
        vent.geometry("550x450")
        vent.transient(self)

        ctk.CTkLabel(vent, text="🔍 Búsqueda global", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(vent, text="Busca en historial, favoritos y estrellas", font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

        ent_buscar = ctk.CTkEntry(vent, placeholder_text="Escribe para buscar...", width=480, height=32)
        ent_buscar.pack(pady=5)

        resultados_frame = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        resultados_frame.pack(fill="both", expand=True, padx=15, pady=5)

        def _buscar(*args):
            termino = ent_buscar.get().strip().lower()
            for w in resultados_frame.winfo_children(): w.destroy()

            if not termino:
                ctk.CTkLabel(resultados_frame, text="Escribe algo para buscar", text_color=c["muted_text"]).pack(pady=20)
                return

            resultados = []

            for item in (self.store.historial or [])[:50]:
                if isinstance(item, dict):
                    contenido = item.get("contenido", "")
                    if termino in contenido.lower():
                        resultados.append(("📋 Historial", contenido[:100]))

            for item in (self.store.favoritos or []):
                if isinstance(item, dict):
                    contenido = item.get("contenido", "")
                    if termino in contenido.lower():
                        resultados.append(("⭐ Favorito", contenido[:100]))

            for item in (self.store.estrellas or []):
                if isinstance(item, dict):
                    contenido = item.get("contenido", "")
                    if termino in contenido.lower():
                        resultados.append(("🌟 Estrella", contenido[:100]))

            if not resultados:
                ctk.CTkLabel(resultados_frame, text="No se encontraron resultados", text_color=c["muted_text"]).pack(pady=20)
                return

            for tipo, texto in resultados[:20]:
                card = ctk.CTkFrame(resultados_frame, fg_color=c["fg_frame"], corner_radius=4)
                card.pack(fill="x", pady=2)
                color = {"📋": "#3498db", "⭐": "#f39c12", "🌟": "#9b59b6"}.get(tipo[:2], "#888")
                ctk.CTkLabel(card, text=tipo, font=ctk.CTkFont(size=9, weight="bold"),
                             text_color=color, width=60, anchor="w").pack(side="left", padx=6, pady=4)
                ctk.CTkLabel(card, text=texto + "..." if len(texto) > 90 else texto,
                             font=ctk.CTkFont(size=9), text_color=c["muted_text"],
                             anchor="w").pack(side="left", padx=4, fill="x", expand=True)

        ent_buscar.bind("<KeyRelease>", _buscar)
        _buscar()

        ctk.CTkButton(vent, text="Cerrar", width=100, height=28, command=vent.destroy).pack(pady=8)

    def _abrir_tutorial(self):
        """Abre el tutorial interactivo (data/tutorial.json) con índice
        lateral, progreso persistente y botón "Probar ahora".
        """
        abrir_tutorial(self)
