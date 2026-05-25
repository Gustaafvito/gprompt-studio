"""Dialogs & Windows Mixin - API Keys, Preferences, Preview, Dashboard, Status, etc."""
import logging
from typing import TYPE_CHECKING

import customtkinter as ctk
import pyperclip

from config import get_theme_colors
from modules.gprompt_window import GPromptWindow

logger = logging.getLogger("gprompt")

# CTkToolTip es opcional — si no está instalado usamos un stub
try:
    from CTkToolTip import CTkToolTip
except ImportError:
    class CTkToolTip:  # noqa: N801
        """Stub silencioso si CTkToolTip no está disponible."""
        def __init__(self, *args, **kwargs):
            pass

if TYPE_CHECKING:
    pass

class DialogsMixin:
    """Mixin containing all dialog, window, and special UI panel methods."""

    def _cmd_configurar_api_keys(self, provider_focus=None):
        """Abre wizard de configuración de API keys para todos los proveedores."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        try:
            from api_clients import (
                LLM_PROVIDERS,
                borrar_api_key,
                cargar_api_key,
                guardar_api_key,
                ubicacion_api_key,
            )
        except ImportError:
            self.set_estado("⚠️ api_clients.py no disponible", "#e74c3c")
            return

        v = GPromptWindow(self)
        v.title("🔑 Configurar API Keys")
        v.geometry("780x720")

        ctk.CTkLabel(v, text="🔑 Configura tus motores de IA",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(14, 4))
        ctk.CTkLabel(v, text="Tu app puede usar varios proveedores. Cada uno tiene su API key.",
                     font=ctk.CTkFont(size=11), text_color="#888").pack(pady=(0, 4))
        ctk.CTkLabel(v, text="🏆 = gratis (con límites)   💎 = de pago",
                     font=ctk.CTkFont(size=10, slant="italic"), text_color="#666").pack(pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(v, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=(0, 8))

        entries_keys = {}

        # Map de íconos por origen de la key (dónde está guardada)
        ICONO_ORIGEN = {
            "keyring":             "🔐 Windows Credential Manager",
            "keys.json (cifrado)": "🔒 keys.json (AES-256 cifrado)",
            "env (.env)":          "📄 variable de entorno .env",
            "":                    "",
        }

        # Helper para refrescar una card concreta sin cerrar la ventana
        cards_refs = {}  # pid → dict con refs a labels que dependen del estado

        def _refrescar_card(pid):
            refs = cards_refs.get(pid, {})
            current = cargar_api_key(pid) or ""
            origen = ubicacion_api_key(pid)
            # Estado
            if refs.get("lbl_estado"):
                refs["lbl_estado"].configure(
                    text="✅ configurado" if current else "⚠️ sin configurar",
                    text_color="#2ecc71" if current else "#e67e22",
                )
            # Origen
            if refs.get("lbl_origen"):
                refs["lbl_origen"].configure(
                    text=ICONO_ORIGEN.get(origen, ""),
                    text_color="#3498db" if origen else "#666",
                )
            # Botón borrar habilitado solo si hay key
            if refs.get("btn_borrar"):
                if current:
                    refs["btn_borrar"].configure(state="normal")
                else:
                    refs["btn_borrar"].configure(state="disabled")

        for pid, info in LLM_PROVIDERS.items():
            card = ctk.CTkFrame(scroll, fg_color="#0f1820", corner_radius=8)
            card.pack(fill="x", pady=4)

            hdr = ctk.CTkFrame(card, fg_color="transparent")
            hdr.pack(fill="x", padx=12, pady=(8, 4))
            current_key_init = cargar_api_key(pid) or ""
            origen_init = ubicacion_api_key(pid)
            estado_actual = "✅ configurado" if current_key_init else "⚠️ sin configurar"
            color_estado = "#2ecc71" if current_key_init else "#e67e22"
            ctk.CTkLabel(hdr, text=f"{info['label']}",
                         font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            lbl_estado = ctk.CTkLabel(hdr, text=estado_actual,
                                        font=ctk.CTkFont(size=10),
                                        text_color=color_estado)
            lbl_estado.pack(side="right")

            ctk.CTkLabel(card, text=f"  {info['descripcion']}",
                         font=ctk.CTkFont(size=10, slant="italic"), text_color="#aaaaaa",
                         wraplength=720, justify="left", anchor="w").pack(fill="x", padx=12, pady=(0, 2))

            # Indicador de origen: keyring / keys.json cifrado / .env
            lbl_origen = ctk.CTkLabel(
                card,
                text=ICONO_ORIGEN.get(origen_init, ""),
                font=ctk.CTkFont(size=9, slant="italic"),
                text_color="#3498db" if origen_init else "#666",
                anchor="w",
            )
            lbl_origen.pack(fill="x", padx=12, pady=(0, 4))

            fila = ctk.CTkFrame(card, fg_color="transparent")
            fila.pack(fill="x", padx=12, pady=(0, 8))
            placeholder = "Pega aquí tu API key…" if pid != "ollama" else "(Ollama no necesita key)"
            ent = ctk.CTkEntry(fila, width=440, placeholder_text=placeholder, show="•")
            if current_key_init:
                ent.insert(0, current_key_init)
            ent.pack(side="left", padx=(0, 6))
            entries_keys[pid] = ent

            def _crear_toggle_show(e=ent):
                def _toggle():
                    e.configure(show="" if e.cget("show") else "•")
                return _toggle
            ctk.CTkButton(fila, text="👁", width=30, height=28, fg_color=c["fg_dark"],
                          hover_color=c["fg_dark_hover"], command=_crear_toggle_show()).pack(side="left", padx=2)

            def _crear_obtener_btn(url=info.get('url_obtener_key', '')):
                def _abrir():
                    try:
                        import webbrowser
                        webbrowser.open(url)
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
                return _abrir
            ctk.CTkButton(fila, text="🌐 Obtener key", width=100, height=28,
                          fg_color="#1e3a5f", hover_color="#162d49",
                          font=ctk.CTkFont(size=10),
                          command=_crear_obtener_btn()).pack(side="left", padx=2)

            # Botón borrar individual
            def _crear_borrar_btn(p=pid, e=ent, info_l=info):
                def _borrar():
                    from tkinter import messagebox
                    if not messagebox.askyesno(
                        "Borrar API key",
                        f"¿Borrar la API key de {info_l['label']}?\n\n"
                        "Se eliminará de keyring del SO y de keys.json cifrado.\n"
                        "Esta acción no se puede deshacer.",
                        parent=v,
                    ):
                        return
                    try:
                        borrar_api_key(p)
                        e.delete(0, "end")
                        _refrescar_card(p)
                        self.set_estado(f"🗑 Key de {info_l['label']} borrada", "#e67e22")
                    except Exception as ex:
                        self.set_estado(f"❌ Error borrando key: {ex}", "#e74c3c")
                return _borrar
            btn_borrar = ctk.CTkButton(
                fila, text="🗑", width=36, height=28,
                fg_color="#7a1a1a", hover_color="#5a1010",
                font=ctk.CTkFont(size=11),
                command=_crear_borrar_btn(),
                state="normal" if current_key_init else "disabled",
            )
            btn_borrar.pack(side="left", padx=2)

            # Guardar refs para _refrescar_card
            cards_refs[pid] = {
                "lbl_estado": lbl_estado,
                "lbl_origen": lbl_origen,
                "btn_borrar": btn_borrar,
            }

        btn_row = ctk.CTkFrame(v, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 14))

        def _guardar_todas():
            cambios = 0
            for pid, ent in entries_keys.items():
                nueva_key = ent.get().strip()
                key_actual = cargar_api_key(pid) or ""
                if nueva_key != key_actual:
                    if hasattr(self.clients, "actualizar_key"):
                        self.clients.actualizar_key(pid, nueva_key)
                    else:
                        guardar_api_key(pid, nueva_key)
                    cambios += 1
            if cambios:
                self.set_estado(f"🔑 {cambios} API keys actualizadas", "#2ecc71")
                # Refrescar el desplegable del cerebro para que los iconos ✅/🔒
                # reflejen las keys recién guardadas
                try:
                    if hasattr(self, "_refrescar_indicadores_llm"):
                        self._refrescar_indicadores_llm()
                except Exception as _e:
                    logger.debug(f"[silent] {_e}")
                try:
                    if hasattr(self, "_actualizar_indicador_proveedor"):
                        self._actualizar_indicador_proveedor()
                except Exception as _e:
                    logger.debug(f"[silent] {_e}")
            else:
                self.set_estado("Sin cambios")
            v.destroy()

        ctk.CTkButton(btn_row, text="💾 Guardar todas", width=140,
                      fg_color="#1e5f3a", hover_color="#16492d",
                      command=_guardar_todas).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="Cerrar", width=110,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                      command=v.destroy).pack(side="right", padx=2)

    # _apply_theme_colors VIVE EN CoreMixin (modules/core.py). NO
    # añadir aquí: el orden de herencia (DialogsMixin antes que
    # CoreMixin) haría que esta versión tomara precedencia.


    def _close_menu_if_open(self, event=None):
        """Cierra menú del header si el click fue fuera del popup y botones."""
        popup = getattr(self, '_active_menu_popup', None)
        if not popup or not popup.winfo_exists():
            return
        if event:
            try:
                px, py = popup.winfo_rootx(), popup.winfo_rooty()
                pw, ph = popup.winfo_width(), popup.winfo_height()
                if px <= event.x_root <= px + pw and py <= event.y_root <= py + ph:
                    return
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            for btn in getattr(self, '_header_menu_btns', []):
                try:
                    bx, by, bw, bh = btn.winfo_rootx(), btn.winfo_rooty(), btn.winfo_width(), btn.winfo_height()
                    if bx <= event.x_root <= bx + bw and by <= event.y_root <= by + bh:
                        return
                except Exception as _e:
                    logger.debug(f"[silent] {_e}")
        try:
            popup.destroy()
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        self._active_menu_popup = None

    def _cmd_acerca_de(self) -> None:
        """Modal 'Acerca de' con info de la app, versión, autor y enlaces."""
        import webbrowser

        from config import APP_TITLE, AUTHOR, PUBLIC_VERSION

        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        v = GPromptWindow(self)
        v.title("ℹ️ Acerca de G-Prompt Studio")
        v.geometry("520x520")
        v.transient(self)

        # Cabecera
        ctk.CTkLabel(v, text=APP_TITLE, font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=c["hdr_text"]).pack(pady=(20, 4))
        ctk.CTkLabel(v, text=f"Versión {PUBLIC_VERSION}",
                     font=ctk.CTkFont(size=11, slant="italic"),
                     text_color=c["muted_text"]).pack(pady=(0, 16))

        # Descripción
        descripcion = (
            "Suite profesional de ingeniería de prompts para IA generativa\n"
            "(imagen, vídeo, audio) con 14+ LLMs como motores.\n\n"
            "Incluye comparador de modelos, A/B testing, ADN visual,\n"
            "import/export JSON pro (Veo/Sora/Kling), dashboard,\n"
            "atajos de teclado y mucho más."
        )
        ctk.CTkLabel(v, text=descripcion, font=ctk.CTkFont(size=11),
                     text_color=c["panel_text"], justify="center",
                     wraplength=460).pack(pady=(0, 16))

        # Stats
        try:
            n_historial = len(self.store.historial or [])
            n_fav = len(self.store.favoritos or [])
            n_estrellas = len(self.store.estrellas or [])
            stats = f"📋 {n_historial} prompts · ⭐ {n_fav} favoritos · 🌟 {n_estrellas} estrellas"
            ctk.CTkLabel(v, text=stats, font=ctk.CTkFont(size=10),
                         text_color=c["muted_text"]).pack(pady=(0, 16))
        except Exception as _e:
            logger.debug(f"[silent acerca stats] {_e}")

        # Autor
        ctk.CTkLabel(v, text=f"Creado por {AUTHOR}",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=c["panel_text"]).pack(pady=(8, 6))

        # Enlaces
        links_frame = ctk.CTkFrame(v, fg_color="transparent")
        links_frame.pack(pady=(0, 14))
        enlaces = [
            ("🐙 GitHub", "https://github.com/Gustaafvito/gprompt-studio"),
            ("💖 Patreon", "https://www.patreon.com/Gustaafvito"),
            ("📺 YouTube", "https://www.youtube.com/@gustaafvito"),
            ("🐦 X / Twitter", "https://x.com/gustaafvito"),
        ]
        for label, url in enlaces:
            ctk.CTkButton(links_frame, text=label, width=130, height=28,
                          fg_color=c["fg_dark"],
                          font=ctk.CTkFont(size=10),
                          command=lambda u=url: webbrowser.open(u)).pack(side="left", padx=4)

        # Botón cerrar
        ctk.CTkButton(v, text="Cerrar", width=120, height=32,
                      fg_color="#6b7280", hover_color="#4b5563",
                      command=v.destroy).pack(pady=(8, 16))

    def _cmd_toggle_tema(self):
        """Cambia entre tema claro y oscuro."""
        actual = ctk.get_appearance_mode()
        nuevo = "Light" if actual == "Dark" else "Dark"
        ctk.set_appearance_mode(nuevo)
        # Guardar preferencia
        prefs = self.store.cargar_preferencias()
        prefs["tema"] = nuevo.lower()
        self.store.guardar_preferencias(prefs)
        self.after(100, self._apply_theme_colors)
        self.set_estado(f"🌗 Tema: {nuevo}", "#2ecc71")

    def _build_author(self):
        """Barra de autor en el footer con enlaces sociales clickables.

        Texto de "Creado por..." y los 4 enlaces sociales comparten la
        MISMA fila en el footer (texto a la izquierda, enlaces a la
        derecha), todo en la última línea de la ventana.
        """
        import webbrowser

        from config import AUTHOR, PUBLIC_VERSION

        is_light = ctk.get_appearance_mode().lower() == "light"
        author_frame = ctk.CTkFrame(self, fg_color="transparent", height=30)
        author_frame.pack(side="bottom", fill="x", padx=16, pady=(4, 6))

        # Texto autor (izquierda)
        ctk.CTkLabel(
            author_frame,
            text=f"G-Prompt Studio v{PUBLIC_VERSION} — Creado con ❤️ por {AUTHOR['nombre']}",
            font=ctk.CTkFont(size=10),
            text_color="#6b7280" if is_light else "#9ca3af"
        ).pack(side="left", padx=(2, 0))

        # Enlaces sociales (derecha) — botones discretos clickables
        # En light, los botones blancos sobre fondo blanco no se ven —
        # damos un fondo sutil con borde.
        if is_light:
            btn_bg = "#ffffff"
            btn_hover = "#dbeafe"
            ig_color = "#E1306C"
            tt_color = "#000000"
            yt_color = "#FF0000"
            gh_color = "#181717"
            x_color  = "#000000"
        else:
            btn_bg = "#1a1f2e"
            btn_hover = "#2a3a5a"
            ig_color = "#E1306C"
            tt_color = "#ffffff"
            yt_color = "#FF0000"
            gh_color = "#f0f6fc"
            x_color  = "#ffffff"

        x_handle = AUTHOR.get("x", "")
        redes = [
            ("📷 Instagram",  f"https://www.instagram.com/{AUTHOR['instagram']}",  ig_color),
            ("🎵 TikTok",     f"https://www.tiktok.com/@{AUTHOR['tiktok']}",       tt_color),
            ("▶ YouTube",     f"https://www.youtube.com/{AUTHOR['youtube']}",      yt_color),
        ]
        if x_handle:
            redes.append(("𝕏 Twitter", f"https://x.com/{x_handle}", x_color))
        redes.append(("🐙 GitHub", AUTHOR['github'], gh_color))

        def _abrir(url):
            try:
                webbrowser.open(url)
                if hasattr(self, "show_toast"):
                    try:
                        self.show_toast(f"🌐 Abriendo {url[:40]}...", "#3b82f6", 1500)
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")
            except Exception as e:
                self.set_estado(f"⚠ No se pudo abrir el enlace: {e}", "#e74c3c")

        # Pack en orden inverso para que aparezcan IG/TikTok/YT/GitHub de
        # izquierda a derecha (pack side="right" apila al revés)
        for txt, url, col in reversed(redes):
            btn = ctk.CTkButton(
                author_frame, text=txt, width=98, height=22,
                fg_color=btn_bg, hover_color=btn_hover,
                text_color=col,
                font=ctk.CTkFont(size=10, weight="bold"),
                corner_radius=4,
                border_width=1 if is_light else 0,
                border_color="#d1d5db" if is_light else "#374151",
                command=lambda u=url: _abrir(u)
            )
            btn.pack(side="right", padx=2)
            try:
                CTkToolTip(btn, message=url, delay=0.4)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
    def _darker(self, hex_color, factor=0.8):
        """Oscurece un color hex."""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = int(r * factor)
        g = int(g * factor)
        b = int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

    def set_estado(self, texto, color=None):
        """Actualiza la barra de estado."""
        if color is None:
            is_light = ctk.get_appearance_mode().lower() == "light"
            try:
                from config import get_theme_colors
                c = get_theme_colors(is_light)
                color = c["muted_text"]
            except Exception:
                color = "#6b7280" if is_light else "#888888"
        if hasattr(self, 'lbl_estado'):
            self.lbl_estado.configure(text=texto, text_color=color)

    def actualizar_salida(self, texto):
        """Actualiza el textbox de salida."""
        if hasattr(self, 'txt_salida'):
            try: self._guardar_version_prompt()
            except Exception as e:
                logger.debug(f"[silent] {e}")
            # F3: marcar separador para que la escritura programática
            # sea un solo paso de undo, distinto del que tenía el usuario.
            try: self.txt_salida._textbox.edit_separator()
            except Exception: pass
            self.txt_salida.delete("1.0", "end")
            self.txt_salida.insert("1.0", texto)
            try: self.txt_salida._textbox.edit_separator()
            except Exception: pass
            self._colorear_resultado()
            try: self._actualizar_tokens()
            except Exception as e:
                logger.debug(f"[silent] {e}")

    def _colorear_resultado(self):
        """Colorea las etiquetas POSITIVE/NEGATIVE en el resultado."""
        if not hasattr(self, 'txt_salida'): return
        self.txt_salida.tag_config("pos_label", foreground="#2ecc71")
        self.txt_salida.tag_config("neg_label", foreground="#e74c3c")
        contenido = self.txt_salida.get("1.0", "end")
        for tag, label in [("pos_label", "POSITIVE PROMPT:"), ("neg_label", "NEGATIVE PROMPT:")]:
            start = "1.0"
            while True:
                pos = self.txt_salida.search(label, start, stopindex="end")
                if not pos: break
                end = f"{pos}+{len(label)}c"
                self.txt_salida.tag_add(tag, pos, end)
                start = end

    def _on_doble_click_salida(self, event=None):
        """Doble click en resultado: si está en línea POSITIVE/NEGATIVE, copiar esa parte."""
        try:
            idx = self.txt_salida.index("current")
            linea = self.txt_salida.get(f"{idx} linestart", f"{idx} lineend")
            if "POSITIVE PROMPT:" in linea or "POSITIVE:" in linea:
                pos = self.extraer_positive()
                if pos:
                    pyperclip.copy(pos)
                    self.set_estado("🟢 POSITIVE copiado (doble-click)", "#2ecc71")
            elif "NEGATIVE PROMPT:" in linea or "NEGATIVE:" in linea:
                neg = self.extraer_negative()
                if neg:
                    pyperclip.copy(neg)
                    self.set_estado(" NEGATIVE copiado (doble-click)", "#e74c3c")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    def toggle_botones(self, estado=True):
        """Activa/desactiva botones de generación."""
        if hasattr(self, 'action_btns'):
            for btn in self.action_btns:
                btn.configure(state="normal" if estado else "disabled")
        if estado:
            self._detener_progreso()
        else:
            self._iniciar_progreso()

    def _iniciar_progreso(self):
        """Inicia la barra de progreso."""
        if not getattr(self, '_progreso_activo', False):
            self._progreso_activo = True
            bar = getattr(self, 'progress', None) or getattr(self, 'barra_progreso', None)
            if bar:
                bar.pack(side="right", padx=(10, 0))
                bar.start()

    def _detener_progreso(self):
        """Detiene y oculta la barra de progreso."""
        if getattr(self, '_progreso_activo', False):
            self._progreso_activo = False
            bar = getattr(self, 'progress', None) or getattr(self, 'barra_progreso', None)
            if bar:
                bar.stop()
                bar.pack_forget()

    def _on_cerrar(self):
        """Guarda estado al cerrar la app y cierra Toplevels hijos.

        v1.0: cierra ventanas hijas antes de destruir la principal para
        evitar errores de 'invalid command name'."""
        import logging as _log
        logger = _log.getLogger(__name__)
        try:
            # Auto-guardar borrador y preferencias
            try:
                self._auto_guardar_borrador()
            except Exception as e:
                logger.warning(f"_auto_guardar_borrador en cierre: {e}")
            try:
                self._guardar_preferencias()
            except Exception as e:
                logger.warning(f"_guardar_preferencias en cierre: {e}")

            # Detener grabación de sesión si está activa
            try:
                if getattr(self, "_sesion_activa", False):
                    self._sesion_activa = False
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            # Cerrar todas las ventanas hijas (Toplevel)
            try:
                for w in list(self.winfo_children()):
                    try:
                        if isinstance(w, ctk.CTkToplevel) and w.winfo_exists():
                            w.destroy()
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
        finally:
            try:
                self.destroy()
            except Exception:
                logger.error("Error destruyendo ventana principal", exc_info=True)

    def _on_salida_editada(self, event=None):
        """Detecta cuando el usuario edita la salida."""
        self._salida_editada = True
        if getattr(self, '_token_pending', None):
            self.after_cancel(self._token_pending)
        self._token_pending = self.after(300, self._actualizar_tokens)

    def _actualizar_tokens(self):
        """Actualiza el contador de tokens y caracteres."""
        if not hasattr(self, 'txt_salida') or not hasattr(self, 'lbl_tokens'):
            return
        texto = self.txt_salida.get("1.0", "end").strip()
        pos = self.extraer_positive()
        neg = self.extraer_negative()
        c_pos = len(pos) if pos else 0
        c_neg = len(neg) if neg else 0
        c_tot = len(texto)

        specs = self.get_current_model_specs()
        if specs:
            max_c = specs.get("max_chars") or specs.get("max_chars_letra") or 1500
        else:
            plat = getattr(self, 'plataforma_var', None)
            max_c = 2000  # Default si no hay specs

        excede = c_pos > max_c
        if c_pos or c_neg:
            color = "#e74c3c" if excede else "#3498db"
            aviso = " ⚠️ EXCEDE" if excede else ""
            if c_neg:
                self.lbl_tokens.configure(
                    text=f"📝 Positive: {c_pos}/{max_c}{aviso}  |  Negative: {c_neg}  |  Total: {c_tot}",
                    text_color=color)
            else:
                self.lbl_tokens.configure(
                    text=f"📝 Prompt: {c_pos}/{max_c}{aviso}  |  Total: {c_tot}",
                    text_color=color)
        elif texto:
            self.lbl_tokens.configure(text=f"📝 Total: {c_tot} chars", text_color="#555555")
        else:
            self.lbl_tokens.configure(text="", text_color="#555555")

    def _sonar_completado(self):
        """Sonido de notificación al completar generación."""
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
