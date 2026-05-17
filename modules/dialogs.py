"""Dialogs & Windows Mixin - API Keys, Preferences, Preview, Dashboard, Status, etc."""
import os
import re
import json
import logging
import threading
import datetime
import pyperclip
import customtkinter as ctk
import tkinter as tk
from typing import TYPE_CHECKING
from config import get_theme_colors
from logging_utils import silent

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
    from app import ArquitectoApp

class DialogsMixin:
    """Mixin containing all dialog, window, and special UI panel methods."""

    def _cmd_configurar_api_keys(self, provider_focus=None):
        """Abre wizard de configuración de API keys para todos los proveedores."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        try:
            from api_clients import LLM_PROVIDERS, cargar_api_key, guardar_api_key
        except ImportError:
            self.set_estado("⚠️ api_clients.py no disponible", "#e74c3c")
            return

        v = ctk.CTkToplevel(self)
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

        for pid, info in LLM_PROVIDERS.items():
            card = ctk.CTkFrame(scroll, fg_color="#0f1820", corner_radius=8)
            card.pack(fill="x", pady=4)

            hdr = ctk.CTkFrame(card, fg_color="transparent")
            hdr.pack(fill="x", padx=12, pady=(8, 4))
            estado_actual = "✅ configurado" if (cargar_api_key(pid) or "") else "⚠️ sin configurar"
            color_estado = "#2ecc71" if (cargar_api_key(pid) or "") else "#e67e22"
            ctk.CTkLabel(hdr, text=f"{info['label']}",
                         font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            ctk.CTkLabel(hdr, text=estado_actual,
                         font=ctk.CTkFont(size=10), text_color=color_estado).pack(side="right")

            ctk.CTkLabel(card, text=f"  {info['descripcion']}",
                         font=ctk.CTkFont(size=10, slant="italic"), text_color="#aaaaaa",
                         wraplength=720, justify="left", anchor="w").pack(fill="x", padx=12, pady=(0, 6))

            fila = ctk.CTkFrame(card, fg_color="transparent")
            fila.pack(fill="x", padx=12, pady=(0, 8))
            current_key = cargar_api_key(pid) or ""
            placeholder = "Pega aquí tu API key…" if pid != "ollama" else "(Ollama no necesita key)"
            ent = ctk.CTkEntry(fila, width=480, placeholder_text=placeholder, show="•")
            if current_key:
                ent.insert(0, current_key)
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
            ctk.CTkButton(fila, text="🌐 Obtener key", width=110, height=28,
                          fg_color="#1e3a5f", hover_color="#162d49",
                          font=ctk.CTkFont(size=10),
                          command=_crear_obtener_btn()).pack(side="left", padx=2)

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
            else:
                self.set_estado("Sin cambios")
            v.destroy()

        ctk.CTkButton(btn_row, text="💾 Guardar todas", width=140,
                      fg_color="#1e5f3a", hover_color="#16492d",
                      command=_guardar_todas).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="Cerrar", width=110,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                      command=v.destroy).pack(side="right", padx=2)

    # ──────────────────────────────────────────────────────────
    # NOTA v1.0.8: la implementación de _apply_theme_colors VIVE EN
    # CoreMixin (modules/core.py). Aquí había una versión obsoleta que,
    # por orden de herencia (DialogsMixin antes que CoreMixin), tomaba
    # precedencia y solo repintaba header+switches, dejando frame_video,
    # frame_audio, frame_modelo_imagen, tabview y labels de paneles
    # con los colores del tema anterior al cambiar dark↔light en
    # caliente. Eliminada para que el MRO encuentre la versión completa
    # de core.py.
    # ──────────────────────────────────────────────────────────

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
            except Exception:
                pass
            for btn in getattr(self, '_header_menu_btns', []):
                try:
                    bx, by, bw, bh = btn.winfo_rootx(), btn.winfo_rooty(), btn.winfo_width(), btn.winfo_height()
                    if bx <= event.x_root <= bx + bw and by <= event.y_root <= by + bh:
                        return
                except Exception:
                    pass
        try:
            popup.destroy()
        except Exception:
            pass
        self._active_menu_popup = None

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

        v1.0.4: el texto de "Creado por..." y los 4 enlaces sociales
        comparten la MISMA fila en el footer (texto a la izquierda,
        enlaces a la derecha), todo en la última línea de la ventana.
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
            redes.append(("𝕏 X / Twitter", f"https://x.com/{x_handle}", x_color))
        redes.append(("🐙 GitHub", AUTHOR['github'], gh_color))

        def _abrir(url):
            try:
                webbrowser.open(url)
                if hasattr(self, "show_toast"):
                    try:
                        self.show_toast(f"🌐 Abriendo {url[:40]}...", "#3b82f6", 1500)
                    except Exception:
                        pass
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
            except Exception:
                pass

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
            self.txt_salida.delete("1.0", "end")
            self.txt_salida.insert("1.0", texto)
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
        except Exception:
            pass

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
            except Exception:
                pass

            # Cerrar todas las ventanas hijas (Toplevel)
            try:
                for w in list(self.winfo_children()):
                    try:
                        if isinstance(w, ctk.CTkToplevel) and w.winfo_exists():
                            w.destroy()
                    except Exception:
                        pass
            except Exception:
                pass

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
        except Exception:
            pass

    def _cmd_dashboard(self):
        """🏠 Dashboard v2 — Panel de control completo con estadísticas, accesos
        rápidos, gráficos y herramientas. Implementado en v1.0.8.

        Features:
        - Saludo personalizado por hora del día
        - Stats cards (prompts, favoritos, estrellas, personajes, LoRAs)
        - Gráfico de barras de últimos 7 días
        - Modelo + plataforma más usados
        - Estado del LLM activo (verde/rojo)
        - Cards "Continuar trabajando" + "Plantilla más usada"
        - Búsqueda global rápida
        - Bloque de avisos
        - Logros / medallas
        - Reto del día
        - Estilo del día
        - Galería rotativa de prompts estrella
        - Mood aleatorio
        - Recordatorios de mantenimiento
        - Atajos de teclado
        - Tip del día
        - Botón cerrar
        """
        import datetime as _dt
        import os as _os
        import random as _rnd
        import re as _re
        from collections import Counter

        is_light = ctk.get_appearance_mode().lower() == "light"
        bg = "#f5f5f5" if is_light else "#0a0e14"
        card_bg = "#ffffff" if is_light else "#111820"
        card_bg_alt = "#f9fafb" if is_light else "#0f1620"
        card_border = "#e5e7eb" if is_light else "#1e2d3d"
        text_primary = "#111827" if is_light else "#e5e7eb"
        text_secondary = "#6b7280" if is_light else "#9ca3af"
        text_muted = "#9ca3af" if is_light else "#6b7280"
        accent_blue = "#2563eb" if is_light else "#3b82f6"
        accent_green = "#16a34a" if is_light else "#22c55e"
        accent_amber = "#d97706" if is_light else "#f59e0b"
        accent_red = "#dc2626" if is_light else "#ef4444"
        accent_purple = "#7c3aed" if is_light else "#a855f7"
        accent_pink = "#db2777" if is_light else "#ec4899"
        bar_bg = "#e5e7eb" if is_light else "#1f2937"

        v = ctk.CTkToplevel(self)
        v.title("🏠 Dashboard")
        v.geometry("960x780")
        v.transient(self)
        v.configure(fg_color=bg)
        try:
            v.lift()
            v.focus_force()
        except Exception:
            pass

        main = ctk.CTkScrollableFrame(v, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=15)

        # FEATURE 21 — Saludo personalizado por hora del día
        hora = _dt.datetime.now().hour
        if 5 <= hora < 12:
            saludo = "🌅 Buenos días"
        elif 12 <= hora < 19:
            saludo = "☀️ Buenas tardes"
        elif 19 <= hora < 24:
            saludo = "🌆 Buenas noches"
        else:
            saludo = "🌙 De madrugada"

        nombre_user = "Creador"
        try:
            prefs_user = self.store.cargar_preferencias() or {}
            nombre_guardado = prefs_user.get("nombre", "").strip()
            if nombre_guardado:
                nombre_user = nombre_guardado
        except Exception:
            pass

        header_box = ctk.CTkFrame(main, fg_color="transparent")
        header_box.pack(fill="x")
        ctk.CTkLabel(header_box, text=f"{saludo}, {nombre_user}",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=text_primary, fg_color="transparent").pack(anchor="w")
        ctk.CTkLabel(header_box, text="🏠 Panel de control · G-Prompt Studio",
                     font=ctk.CTkFont(size=11),
                     text_color=text_secondary, fg_color="transparent").pack(anchor="w", pady=(0, 12))

        # FEATURE 23 — Búsqueda global inline (resultados en el dashboard)
        # otra ventana.
        search_frame = ctk.CTkFrame(main, fg_color=card_bg, corner_radius=10,
                                     border_color=card_border, border_width=1)
        search_frame.pack(fill="x", pady=(0, 10))
        search_inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_inner.pack(fill="x", padx=12, pady=10)
        ctk.CTkLabel(search_inner, text="🔍", font=ctk.CTkFont(size=18),
                     fg_color="transparent", text_color=accent_blue).pack(side="left", padx=(0, 8))
        search_entry = ctk.CTkEntry(search_inner, height=34,
                                     placeholder_text="Buscar en historial, favoritos, plantillas, personajes…",
                                     font=ctk.CTkFont(size=12), border_width=1,
                                     border_color=card_border)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Frame de resultados (oculto inicialmente)
        results_box = ctk.CTkFrame(search_frame, fg_color="transparent")

        def _buscar_inline(_evt=None):
            q = search_entry.get().strip().lower()
            # Limpiar resultados anteriores
            for w in results_box.winfo_children():
                try: w.destroy()
                except Exception as e:
                    logger.debug(f"[silent] {e}")
            if not q:
                results_box.pack_forget()
                return

            # Buscar en historial, favoritos, estrellas, personajes, plantillas, loras
            resultados = []
            try:
                for h in (self.store.historial or []):
                    txt = (h.get("contenido", "") or "").lower()
                    if q in txt:
                        preview = h.get("contenido", "")[:80].replace("\n", " ")
                        resultados.append(("📋 Historial", preview, h.get("contenido", "")))
                        if len(resultados) >= 8:
                            break
            except Exception as e:
                logger.debug(f"[silent] {e}")

            try:
                for f in (self.store.favoritos or []):
                    txt = (f.get("contenido", "") or "").lower()
                    if q in txt:
                        preview = f.get("contenido", "")[:80].replace("\n", " ")
                        resultados.append(("⭐ Favorito", preview, f.get("contenido", "")))
                        if len(resultados) >= 16:
                            break
            except Exception as e:
                logger.debug(f"[silent] {e}")

            try:
                for e in (self.store.estrellas or []):
                    txt = (e.get("contenido", "") or "").lower()
                    if q in txt:
                        preview = e.get("contenido", "")[:80].replace("\n", " ")
                        resultados.append(("🌟 Estrella", preview, e.get("contenido", "")))
                        if len(resultados) >= 24:
                            break
            except Exception as e:
                logger.debug(f"[silent] {e}")

            try:
                for p in (self.store.personajes or []):
                    if q in (p.get("nombre", "") or "").lower() or q in (p.get("descripcion", "") or "").lower():
                        preview = f"{p.get('nombre', '')} — {p.get('descripcion', '')[:60]}"
                        resultados.append(("🧑 Personaje", preview, p.get("descripcion", "")))
            except Exception as e:
                logger.debug(f"[silent] {e}")

            try:
                for pl in (self.store.plantillas or []):
                    if q in (pl.get("nombre", "") or "").lower():
                        preview = f"{pl.get('nombre', '')}"
                        resultados.append(("📐 Plantilla", preview, pl.get("nombre", "")))
            except Exception as e:
                logger.debug(f"[silent] {e}")

            try:
                for lo in (self.store.loras or []):
                    if q in (lo.get("nombre", "") or "").lower() or q in (lo.get("trigger", "") or "").lower():
                        preview = f"{lo.get('nombre', '')} → {lo.get('trigger', '')}"
                        resultados.append(("🔗 LoRA", preview, lo.get("trigger", "")))
            except Exception as e:
                logger.debug(f"[silent] {e}")

            # Mostrar resultados
            results_box.pack(fill="x", padx=12, pady=(0, 10))
            if not resultados:
                ctk.CTkLabel(results_box, text=f"Sin resultados para «{q}»",
                             font=ctk.CTkFont(size=11),
                             fg_color="transparent", text_color=text_muted).pack(pady=8)
                return

            ctk.CTkLabel(results_box, text=f"📌 {len(resultados)} resultado(s)",
                         font=ctk.CTkFont(size=10, weight="bold"),
                         fg_color="transparent", text_color=text_secondary).pack(anchor="w", pady=(2, 4))

            # Limitar a primeros 12 resultados visibles
            for tipo, preview, contenido_full in resultados[:12]:
                row = ctk.CTkFrame(results_box, fg_color=card_bg_alt, corner_radius=6,
                                    border_color=card_border, border_width=1)
                row.pack(fill="x", pady=2)
                tipo_lbl = ctk.CTkLabel(row, text=tipo,
                                         font=ctk.CTkFont(size=9, weight="bold"),
                                         fg_color="transparent", text_color=accent_blue,
                                         width=90, anchor="w")
                tipo_lbl.pack(side="left", padx=(8, 4), pady=4)
                ctk.CTkLabel(row, text=preview + ("…" if len(preview) >= 80 else ""),
                             font=ctk.CTkFont(size=10),
                             fg_color="transparent", text_color=text_primary,
                             anchor="w").pack(side="left", fill="x", expand=True, padx=4)
                # Botón cargar
                def _cargar(c=contenido_full):
                    try:
                        # Si parece prompt completo, cárgalo en salida
                        if len(c) > 30:
                            self.actualizar_salida(c)
                        # Si no, mete en idea
                        else:
                            self.txt_idea.delete("1.0", "end")
                            self.txt_idea.insert("1.0", c)
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
                    self.set_estado("✅ Cargado desde búsqueda", accent_green)
                    v.destroy()
                ctk.CTkButton(row, text="Cargar", width=60, height=22,
                              fg_color=accent_blue, hover_color="#1d4ed8",
                              font=ctk.CTkFont(size=9),
                              command=_cargar).pack(side="right", padx=6, pady=2)

            if len(resultados) > 12:
                ctk.CTkLabel(results_box,
                             text=f"… y {len(resultados) - 12} más. Refina la búsqueda.",
                             font=ctk.CTkFont(size=9, slant="italic"),
                             fg_color="transparent", text_color=text_muted).pack(pady=(2, 4))

        # Búsqueda en vivo: cada vez que el usuario escribe, refresca
        # (con un pequeño debounce para no saturar)
        _search_after_id = [None]
        def _on_typing(_evt=None):
            if _search_after_id[0]:
                try: v.after_cancel(_search_after_id[0])
                except Exception as e:
                    logger.debug(f"[silent] {e}")
            _search_after_id[0] = v.after(300, _buscar_inline)
        search_entry.bind("<KeyRelease>", _on_typing)
        search_entry.bind("<Return>", _buscar_inline)

        ctk.CTkButton(search_inner, text="Buscar", width=80, height=32,
                      fg_color=accent_blue, hover_color="#1d4ed8",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=_buscar_inline).pack(side="left")

        # Datos comunes
        favoritos = self.store.favoritos or []
        estrellas = self.store.estrellas or []
        historial = self.store.historial or []
        personajes = self.store.personajes or []
        loras = self.store.loras or []
        plantillas = self.store.plantillas or []

        # FEATURE 18 — LAYOUT EN 2 COLUMNAS (con grid)
        twocol = ctk.CTkFrame(main, fg_color="transparent")
        twocol.pack(fill="both", expand=True)
        twocol.grid_columnconfigure(0, weight=3)  # izq más ancha
        twocol.grid_columnconfigure(1, weight=2)
        col_izq = ctk.CTkFrame(twocol, fg_color="transparent")
        col_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        col_der = ctk.CTkFrame(twocol, fg_color="transparent")
        col_der.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # COLUMNA IZQUIERDA — Stats / Actividad / Continuar

        # ─── Stats cards (5 contadores grandes) ───────────────
        stats = [
            ("📋", str(len(historial)), "prompts", accent_blue),
            ("⭐", str(len(favoritos)), "favoritos", accent_amber),
            ("🌟", str(len(estrellas)), "estrellas", accent_purple),
            ("🧑", str(len(personajes)), "personajes", accent_pink),
            ("🔗", str(len(loras)), "LoRAs", accent_green),
        ]
        stats_frame = ctk.CTkFrame(col_izq, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 10))
        for i, (icon, val, label, col_acc) in enumerate(stats):
            card = ctk.CTkFrame(stats_frame, fg_color=card_bg, corner_radius=10,
                                border_color=card_border, border_width=1)
            card.grid(row=0, column=i, padx=4, sticky="nsew")
            ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=18),
                         fg_color="transparent", text_color=text_primary).pack(pady=(8, 2))
            ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=18, weight="bold"),
                         fg_color="transparent", text_color=col_acc).pack()
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=9),
                         fg_color="transparent", text_color=text_secondary).pack(pady=(0, 6))
        for ci in range(len(stats)):
            stats_frame.grid_columnconfigure(ci, weight=1)

        # FEATURE 1 — Gráfico de actividad últimos 7 días
        chart_frame = ctk.CTkFrame(col_izq, fg_color=card_bg, corner_radius=10,
                                    border_color=card_border, border_width=1)
        chart_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(chart_frame, text="📈 Actividad — últimos 7 días",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     fg_color="transparent", text_color=text_primary).pack(anchor="w", padx=14, pady=(10, 4))

        # Calcular conteo por día
        hoy = _dt.date.today()
        dias = [(hoy - _dt.timedelta(days=6 - i)) for i in range(7)]
        conteo_dias = [0] * 7
        for entrada in historial:
            try:
                fstr = entrada.get("fecha", "")
                if not fstr:
                    continue
                f = _dt.datetime.strptime(fstr[:10], "%Y-%m-%d").date()
                for idx, d in enumerate(dias):
                    if f == d:
                        conteo_dias[idx] += 1
                        break
            except Exception:
                continue

        max_val = max(conteo_dias) if conteo_dias and max(conteo_dias) > 0 else 1
        chart_inner = ctk.CTkFrame(chart_frame, fg_color="transparent", height=85)
        chart_inner.pack(fill="x", padx=14, pady=(2, 6))
        chart_inner.pack_propagate(False)
        nombres_dias = ["L", "M", "X", "J", "V", "S", "D"]
        for idx, (d, val) in enumerate(zip(dias, conteo_dias)):
            col_frame = ctk.CTkFrame(chart_inner, fg_color="transparent", width=36)
            col_frame.pack(side="left", padx=3, fill="y")
            col_frame.pack_propagate(False)
            # Valor numérico arriba de la barra (compacto)
            ctk.CTkLabel(col_frame, text=str(val) if val > 0 else "·",
                         font=ctk.CTkFont(size=9, weight="bold"),
                         fg_color="transparent",
                         text_color=accent_blue if val > 0 else text_muted).pack(pady=(2, 0))
            # Barra coloreada proporcional (max 35px)
            altura_barra = int(35 * (val / max_val)) if max_val > 0 else 0
            altura_barra = max(altura_barra, 3 if val > 0 else 2)
            bar_container = ctk.CTkFrame(col_frame, fg_color="transparent", height=38)
            bar_container.pack(fill="x")
            bar_container.pack_propagate(False)
            # Spacer para alinear barras al fondo del contenedor
            spacer = ctk.CTkFrame(bar_container, fg_color="transparent")
            spacer.pack(fill="both", expand=True)
            bar = ctk.CTkFrame(bar_container,
                                fg_color=accent_blue if val > 0 else bar_bg,
                                height=altura_barra, corner_radius=2)
            bar.pack(fill="x", padx=4, side="bottom")
            # Día del mes + nombre día junto
            nombre_d = nombres_dias[d.weekday()]
            ctk.CTkLabel(col_frame, text=f"{nombre_d}{d.day}",
                         font=ctk.CTkFont(size=8),
                         fg_color="transparent", text_color=text_secondary).pack(pady=(1, 2))

        total_semana = sum(conteo_dias)
        ctk.CTkLabel(chart_frame, text=f"Total semana: {total_semana} prompts",
                     font=ctk.CTkFont(size=10),
                     fg_color="transparent", text_color=text_secondary).pack(anchor="w", padx=14, pady=(0, 6))

        # FEATURE 2 — Modelo más usado (top 3)
        # FEATURE 3 — Plataforma favorita (porcentajes)
        models_platforms_frame = ctk.CTkFrame(col_izq, fg_color="transparent")
        models_platforms_frame.pack(fill="x", pady=(0, 10))
        models_platforms_frame.grid_columnconfigure(0, weight=1)
        models_platforms_frame.grid_columnconfigure(1, weight=1)

        # Modelo más usado (inferido de la plataforma; el historial NO guarda modelo
        # por entrada, así que mostramos top de plataformas en lugar de modelos
        # individuales — más fiable con los datos disponibles).
        contador_plat = Counter()
        contador_modo = Counter()
        for e in historial:
            p = e.get("plataforma", "")
            m = e.get("modo", "")
            if p:
                contador_plat[p] += 1
            if m:
                contador_modo[m] += 1

        # Card: Top modos (imagen/video/audio)
        modo_card = ctk.CTkFrame(models_platforms_frame, fg_color=card_bg, corner_radius=10,
                                  border_color=card_border, border_width=1)
        modo_card.grid(row=0, column=0, padx=(0, 4), sticky="nsew")
        ctk.CTkLabel(modo_card, text="🎯 Modo más usado",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     fg_color="transparent", text_color=text_primary).pack(anchor="w", padx=12, pady=(10, 4))
        if contador_modo:
            top_modos = contador_modo.most_common(3)
            total_modos = sum(contador_modo.values())
            for modo_n, count in top_modos:
                pct = int(count / total_modos * 100) if total_modos else 0
                emoji_modo = {"imagen": "🖼", "video": "🎬", "audio": "🎵"}.get(modo_n, "•")
                row = ctk.CTkFrame(modo_card, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=2)
                ctk.CTkLabel(row, text=f"{emoji_modo} {modo_n.capitalize()}",
                             font=ctk.CTkFont(size=10), width=100, anchor="w",
                             fg_color="transparent", text_color=text_primary).pack(side="left")
                ctk.CTkLabel(row, text=f"{count} ({pct}%)",
                             font=ctk.CTkFont(size=10, weight="bold"),
                             fg_color="transparent", text_color=accent_blue).pack(side="right")
        else:
            ctk.CTkLabel(modo_card, text="Aún sin datos. Genera prompts para ver tu modo favorito.",
                         font=ctk.CTkFont(size=9), wraplength=200,
                         fg_color="transparent", text_color=text_muted).pack(padx=12, pady=(0, 10))
        ctk.CTkLabel(modo_card, text="", fg_color="transparent").pack(pady=2)

        # Card: Plataforma favorita
        plat_card = ctk.CTkFrame(models_platforms_frame, fg_color=card_bg, corner_radius=10,
                                  border_color=card_border, border_width=1)
        plat_card.grid(row=0, column=1, padx=(4, 0), sticky="nsew")
        ctk.CTkLabel(plat_card, text="🌐 Plataforma favorita",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     fg_color="transparent", text_color=text_primary).pack(anchor="w", padx=12, pady=(10, 4))
        if contador_plat:
            top_plats = contador_plat.most_common(3)
            total_plats = sum(contador_plat.values())
            for p, count in top_plats:
                pct = int(count / total_plats * 100) if total_plats else 0
                # Truncar nombre largo
                nombre_p = (p[:18] + "…") if len(p) > 18 else p
                row = ctk.CTkFrame(plat_card, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=2)
                ctk.CTkLabel(row, text=nombre_p,
                             font=ctk.CTkFont(size=10), anchor="w",
                             fg_color="transparent", text_color=text_primary).pack(side="left")
                ctk.CTkLabel(row, text=f"{pct}%",
                             font=ctk.CTkFont(size=10, weight="bold"),
                             fg_color="transparent", text_color=accent_purple).pack(side="right")
        else:
            ctk.CTkLabel(plat_card, text="Aún sin datos.",
                         font=ctk.CTkFont(size=9),
                         fg_color="transparent", text_color=text_muted).pack(padx=12, pady=(0, 10))
        ctk.CTkLabel(plat_card, text="", fg_color="transparent").pack(pady=2)

        # FEATURE 6 — Última sesión + FEATURE 5 — Tokens estimados
        info_sesion = ctk.CTkFrame(col_izq, fg_color=card_bg, corner_radius=10,
                                    border_color=card_border, border_width=1)
        info_sesion.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(info_sesion, text="📊 Datos de uso",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     fg_color="transparent", text_color=text_primary).pack(anchor="w", padx=12, pady=(10, 4))

        # Última sesión: tomar la fecha del prompt más reciente
        ultima_str = "Aún no hay actividad"
        if historial:
            try:
                ultima = historial[0].get("fecha", "")
                if ultima:
                    f_ult = _dt.datetime.strptime(ultima[:16], "%Y-%m-%d %H:%M")
                    delta = _dt.datetime.now() - f_ult
                    if delta.days > 0:
                        ultima_str = f"Hace {delta.days} día{'s' if delta.days != 1 else ''}"
                    elif delta.seconds >= 3600:
                        h = delta.seconds // 3600
                        ultima_str = f"Hace {h} hora{'s' if h != 1 else ''}"
                    elif delta.seconds >= 60:
                        m = delta.seconds // 60
                        ultima_str = f"Hace {m} minuto{'s' if m != 1 else ''}"
                    else:
                        ultima_str = "Hace unos segundos"
            except Exception:
                pass

        # Estimación de tokens (cuenta caracteres del historial / 4)
        chars_total = sum(len(e.get("contenido", "")) for e in historial)
        tokens_estimados = chars_total // 4

        info_grid = ctk.CTkFrame(info_sesion, fg_color="transparent")
        info_grid.pack(fill="x", padx=12, pady=(0, 10))
        info_grid.grid_columnconfigure(0, weight=1)
        info_grid.grid_columnconfigure(1, weight=1)
        # Última sesión
        ctk.CTkLabel(info_grid, text="🕒 Última sesión",
                     font=ctk.CTkFont(size=9),
                     fg_color="transparent", text_color=text_secondary).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(info_grid, text=ultima_str,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     fg_color="transparent", text_color=accent_green).grid(row=1, column=0, sticky="w", pady=(0, 4))
        # Tokens
        ctk.CTkLabel(info_grid, text="🪙 Tokens consumidos (estim.)",
                     font=ctk.CTkFont(size=9),
                     fg_color="transparent", text_color=text_secondary).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(info_grid, text=f"~{tokens_estimados:,}".replace(",", "."),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     fg_color="transparent", text_color=accent_amber).grid(row=1, column=1, sticky="w", pady=(0, 4))

        # FEATURE 7 — Continuar trabajando + FEATURE 8 — Plantilla más usada
        continuar_frame = ctk.CTkFrame(col_izq, fg_color=card_bg, corner_radius=10,
                                        border_color=card_border, border_width=1)
        continuar_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(continuar_frame, text="▶️ Continuar trabajando",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     fg_color="transparent", text_color=text_primary).pack(anchor="w", padx=14, pady=(10, 4))

        # Borrador
        try:
            from config import CARPETA_APP
            borrador_path = CARPETA_APP / "borrador.txt"
            tiene_borrador = borrador_path.exists() and borrador_path.stat().st_size > 0
        except Exception:
            tiene_borrador = False

        cont_inner = ctk.CTkFrame(continuar_frame, fg_color="transparent")
        cont_inner.pack(fill="x", padx=14, pady=(0, 10))

        if tiene_borrador:
            def _restaurar():
                try:
                    self._restaurar_borrador()
                    self.set_estado("📝 Borrador restaurado", accent_green)
                except Exception:
                    self.set_estado("⚠️ No se pudo restaurar el borrador", accent_red)
                v.destroy()
            ctk.CTkButton(cont_inner, text="📝 Restaurar borrador no guardado",
                          height=32, fg_color=accent_blue, hover_color="#1d4ed8",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          text_color="#ffffff",
                          command=_restaurar).pack(fill="x", pady=2)
        elif historial:
            # Cargar último prompt del historial
            ultimo = historial[0]
            preview_corto = ultimo.get("contenido", "")[:60].replace("\n", " ")
            def _cargar_ultimo():
                self.actualizar_salida(ultimo.get("contenido", ""))
                self.set_estado("📋 Último prompt cargado", accent_green)
                v.destroy()
            ctk.CTkButton(cont_inner, text=f"📋 Cargar último: {preview_corto}…",
                          height=32, fg_color=accent_blue, hover_color="#1d4ed8",
                          font=ctk.CTkFont(size=10),
                          text_color="#ffffff", anchor="w",
                          command=_cargar_ultimo).pack(fill="x", pady=2)
        else:
            ctk.CTkLabel(cont_inner, text="Aún no hay nada que continuar. ¡Genera tu primer prompt!",
                         font=ctk.CTkFont(size=10), wraplength=380,
                         fg_color="transparent", text_color=text_muted).pack(pady=4)

        # Plantilla más usada (no se trackea, así que mostramos la primera/destacada)
        if plantillas:
            primera = plantillas[0]
            nombre_pl = primera.get("nombre", "Sin nombre")
            def _aplicar_plantilla():
                try:
                    self.combo_plantilla.set(nombre_pl)
                    self._cargar_plantilla(nombre_pl)
                    self.set_estado(f"📐 Plantilla aplicada: {nombre_pl}", accent_green)
                except Exception:
                    self.set_estado("⚠️ Error aplicando plantilla", accent_red)
                v.destroy()
            ctk.CTkButton(cont_inner, text=f"📐 Aplicar plantilla: {nombre_pl}",
                          height=28, fg_color=accent_purple, hover_color="#6d28d9",
                          font=ctk.CTkFont(size=10, weight="bold"),
                          text_color="#ffffff",
                          command=_aplicar_plantilla).pack(fill="x", pady=(4, 2))

        # FEATURE 13 — Galería de prompts estrella (top 3)
        if estrellas:
            estr_frame = ctk.CTkFrame(col_izq, fg_color=card_bg, corner_radius=10,
                                       border_color=card_border, border_width=1)
            estr_frame.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(estr_frame, text="🌟 Tus prompts estrella",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         fg_color="transparent", text_color=text_primary).pack(anchor="w", padx=14, pady=(10, 4))

            # Ordenar por nota descendente y tomar top 3
            try:
                top_estr = sorted(estrellas, key=lambda x: float(x.get("nota", 0)), reverse=True)[:3]
            except Exception:
                top_estr = estrellas[:3]

            for estr in top_estr:
                contenido_e = estr.get("contenido", "")
                modelo_e = estr.get("modelo", "—")
                nota_e = estr.get("nota", "—")
                preview_e = contenido_e[:80].replace("\n", " ") + ("…" if len(contenido_e) > 80 else "")
                row = ctk.CTkFrame(estr_frame, fg_color=card_bg_alt, corner_radius=6,
                                    border_color=card_border, border_width=1)
                row.pack(fill="x", padx=14, pady=3)
                hdr_e = ctk.CTkFrame(row, fg_color="transparent")
                hdr_e.pack(fill="x", padx=10, pady=(6, 0))
                ctk.CTkLabel(hdr_e, text=f"⭐ {nota_e}/10",
                             font=ctk.CTkFont(size=10, weight="bold"),
                             fg_color="transparent", text_color=accent_amber).pack(side="left")
                ctk.CTkLabel(hdr_e, text=f"  •  {modelo_e}",
                             font=ctk.CTkFont(size=9),
                             fg_color="transparent", text_color=text_secondary).pack(side="left")

                def _cargar_estrella(c=contenido_e):
                    self.actualizar_salida(c)
                    self.set_estado("🌟 Prompt estrella cargado", accent_green)
                    v.destroy()
                ctk.CTkButton(hdr_e, text="Cargar", width=60, height=20,
                              fg_color=accent_blue, hover_color="#1d4ed8",
                              font=ctk.CTkFont(size=9), command=_cargar_estrella).pack(side="right")
                ctk.CTkLabel(row, text=preview_e,
                             font=ctk.CTkFont(size=9), wraplength=460,
                             fg_color="transparent", text_color=text_secondary,
                             anchor="w", justify="left").pack(fill="x", padx=10, pady=(0, 6))
            ctk.CTkLabel(estr_frame, text="", fg_color="transparent").pack(pady=2)

        # COLUMNA DERECHA — LLM, avisos, retos, herramientas

        # FEATURE 10 — Estado del LLM activo
        llm_card = ctk.CTkFrame(col_der, fg_color=card_bg, corner_radius=10,
                                 border_color=card_border, border_width=1)
        llm_card.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(llm_card, text="🧠 LLM activo",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     fg_color="transparent", text_color=text_primary).pack(anchor="w", padx=12, pady=(10, 2))

        # Verificar si hay key configurada
        try:
            llm_label = self.llm_var.get() if hasattr(self, "llm_var") else "—"
        except Exception:
            llm_label = "—"

        try:
            provider = self.clients.get_active_provider() if hasattr(self, "clients") else None
            disponible = provider.disponible() if provider and hasattr(provider, "disponible") else False
        except Exception:
            disponible = False

        estado_color = accent_green if disponible else accent_red
        estado_emoji = "🟢" if disponible else "🔴"
        estado_text = "Conectado" if disponible else "Sin key"

        ctk.CTkLabel(llm_card, text=llm_label,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     fg_color="transparent", text_color=text_primary).pack(anchor="w", padx=12)
        estado_row = ctk.CTkFrame(llm_card, fg_color="transparent")
        estado_row.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(estado_row, text=f"{estado_emoji} {estado_text}",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     fg_color="transparent", text_color=estado_color).pack(side="left")
        if not disponible:
            def _abrir_keys():
                v.destroy()
                try:
                    self._cmd_api_keys()
                except Exception:
                    self.set_estado("Configura tu key en 🔑 (header)", accent_amber)
            ctk.CTkButton(estado_row, text="🔑 Configurar", width=100, height=22,
                          fg_color=accent_purple, hover_color="#6d28d9",
                          font=ctk.CTkFont(size=9), command=_abrir_keys).pack(side="right")

        # FEATURE 22 — Bloque de Avisos
        avisos = []
        if not disponible:
            avisos.append(("⚠️", "Sin LLM configurado", accent_red))
        if len(historial) >= 90:
            avisos.append(("📋", f"Historial casi lleno ({len(historial)}/100)", accent_amber))
        if not personajes:
            avisos.append(("🧑", "No tienes personajes guardados", text_muted))
        if not plantillas:
            avisos.append(("📐", "No tienes plantillas guardadas", text_muted))

        # Backup
        try:
            from config import ARCHIVOS
            marker = ARCHIVOS["autobackup_marker"]
            if marker.exists():
                last_bk = _dt.datetime.fromtimestamp(marker.stat().st_mtime)
                dias_bk = (_dt.datetime.now() - last_bk).days
                if dias_bk >= 7:
                    avisos.append(("💾", f"Último backup hace {dias_bk} días", accent_amber))
            else:
                avisos.append(("💾", "Aún no se ha hecho backup", text_muted))
        except Exception:
            pass

        if avisos:
            avisos_frame = ctk.CTkFrame(col_der, fg_color=card_bg, corner_radius=10,
                                         border_color=card_border, border_width=1)
            avisos_frame.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(avisos_frame, text="🔔 Avisos",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         fg_color="transparent", text_color=text_primary).pack(anchor="w", padx=12, pady=(10, 4))
            for emoji_av, txt_av, col_av in avisos[:5]:
                row = ctk.CTkFrame(avisos_frame, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=2)
                ctk.CTkLabel(row, text=emoji_av, font=ctk.CTkFont(size=12),
                             fg_color="transparent", text_color=col_av).pack(side="left", padx=(0, 6))
                ctk.CTkLabel(row, text=txt_av, font=ctk.CTkFont(size=10), wraplength=240,
                             fg_color="transparent", text_color=text_secondary,
                             anchor="w", justify="left").pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(avisos_frame, text="", fg_color="transparent").pack(pady=2)

        # FEATURE 24 — Logros / Medallas

        # Definición completa de logros: (emoji, nombre, descripción, condición lambda → bool, valor_actual_y_objetivo)
        TODOS_LOS_LOGROS = [
            # Hitos de cantidad
            ("🏁", "Primer prompt", "Genera tu primer prompt",
             len(historial) >= 1, (len(historial), 1)),
            ("🚀", "Aprendiz", "Genera 10 prompts",
             len(historial) >= 10, (len(historial), 10)),
            ("⚡", "Productivo", "Genera 50 prompts",
             len(historial) >= 50, (len(historial), 50)),
            ("💯", "Centenario", "Genera 100 prompts",
             len(historial) >= 100, (len(historial), 100)),

            # Favoritos
            ("⭐", "Selectivo", "Marca 5 favoritos",
             len(favoritos) >= 5, (len(favoritos), 5)),
            ("🌟", "Coleccionista", "Marca 20 favoritos",
             len(favoritos) >= 20, (len(favoritos), 20)),

            # Estrellas
            ("✨", "Reconocedor", "Guarda 3 prompts estrella",
             len(estrellas) >= 3, (len(estrellas), 3)),
            ("🏆", "Curador", "Guarda 10 prompts estrella",
             len(estrellas) >= 10, (len(estrellas), 10)),

            # Personajes
            ("🧑", "Creador de personajes", "Crea 3 personajes",
             len(personajes) >= 3, (len(personajes), 3)),
            ("👥", "Casting completo", "Crea 10 personajes",
             len(personajes) >= 10, (len(personajes), 10)),

            # LoRAs
            ("🔗", "Mezclador", "Guarda 3 LoRAs",
             len(loras) >= 3, (len(loras), 3)),
            ("🧪", "Alquimista", "Guarda 10 LoRAs",
             len(loras) >= 10, (len(loras), 10)),

            # Plantillas
            ("📐", "Organizado", "Guarda 3 plantillas",
             len(plantillas) >= 3, (len(plantillas), 3)),
            ("🗂", "Sistemático", "Guarda 10 plantillas",
             len(plantillas) >= 10, (len(plantillas), 10)),

            # Variedad
            ("🌐", "Explorador", "Usa 3 plataformas distintas",
             len(set(e.get("plataforma", "") for e in historial if e.get("plataforma"))) >= 3,
             (len(set(e.get("plataforma", "") for e in historial if e.get("plataforma"))), 3)),
            ("🌍", "Cosmopolita", "Usa 5 plataformas distintas",
             len(set(e.get("plataforma", "") for e in historial if e.get("plataforma"))) >= 5,
             (len(set(e.get("plataforma", "") for e in historial if e.get("plataforma"))), 5)),
            ("🎨", "Multiestilo", "Usa los 3 modos (imagen/vídeo/audio)",
             len(set(e.get("modo", "") for e in historial if e.get("modo"))) >= 3,
             (len(set(e.get("modo", "") for e in historial if e.get("modo"))), 3)),

            # Específicos
            ("🎬", "Cineasta", "Genera 10 prompts de vídeo",
             sum(1 for e in historial if e.get("modo") == "video") >= 10,
             (sum(1 for e in historial if e.get("modo") == "video"), 10)),
            ("🎵", "Compositor", "Genera 10 prompts de audio",
             sum(1 for e in historial if e.get("modo") == "audio") >= 10,
             (sum(1 for e in historial if e.get("modo") == "audio"), 10)),
            ("📸", "Fotógrafo", "Genera 50 prompts de imagen",
             sum(1 for e in historial if e.get("modo") == "imagen") >= 50,
             (sum(1 for e in historial if e.get("modo") == "imagen"), 50)),
        ]

        n_total = len(TODOS_LOS_LOGROS)
        n_desbloq = sum(1 for _, _, _, d, _ in TODOS_LOS_LOGROS if d)

        logros_frame = ctk.CTkFrame(col_der, fg_color=card_bg, corner_radius=10,
                                     border_color=card_border, border_width=1)
        logros_frame.pack(fill="x", pady=(0, 10))

        # Header con título y botón "Ver todos"
        logros_hdr = ctk.CTkFrame(logros_frame, fg_color="transparent")
        logros_hdr.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(logros_hdr, text=f"🏆 Logros ({n_desbloq}/{n_total})",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     fg_color="transparent", text_color=text_primary).pack(side="left")

        def _abrir_todos_los_logros():
            """Ventana con todos los logros: desbloqueados arriba, bloqueados abajo."""
            win = ctk.CTkToplevel(v)
            win.title("🏆 Todos los logros")
            win.geometry("520x620")
            win.transient(v)
            try:
                win.lift()
                win.focus_force()
            except Exception as e:
                logger.debug(f"[silent] {e}")

            ctk.CTkLabel(win, text=f"🏆 Logros — {n_desbloq} de {n_total} desbloqueados",
                         font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 4))

            # Barra de progreso
            pct_total = n_desbloq / n_total if n_total else 0
            try:
                pb = ctk.CTkProgressBar(win, width=440, height=10,
                                         progress_color=accent_amber)
                pb.set(pct_total)
                pb.pack(pady=(0, 10))
            except Exception as e:
                logger.debug(f"[silent] {e}")

            ctk.CTkLabel(win, text=f"{int(pct_total * 100)}% completado",
                         font=ctk.CTkFont(size=10),
                         text_color=text_secondary).pack(pady=(0, 8))

            scroll = ctk.CTkScrollableFrame(win, fg_color="transparent",
                                              width=480, height=480)
            scroll.pack(fill="both", expand=True, padx=15, pady=5)

            # Desbloqueados primero, luego bloqueados (con progreso)
            desbloq_list = [(e, n, d, ok, pg) for (e, n, d, ok, pg) in TODOS_LOS_LOGROS if ok]
            blocked_list = [(e, n, d, ok, pg) for (e, n, d, ok, pg) in TODOS_LOS_LOGROS if not ok]

            if desbloq_list:
                ctk.CTkLabel(scroll, text="✅ Desbloqueados",
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=accent_green).pack(anchor="w", pady=(4, 4))
                for emoji_l, nombre_l, desc_l, _ok, (val, obj) in desbloq_list:
                    row = ctk.CTkFrame(scroll, fg_color=card_bg_alt, corner_radius=6,
                                        border_color=card_border, border_width=1)
                    row.pack(fill="x", pady=2)
                    inner = ctk.CTkFrame(row, fg_color="transparent")
                    inner.pack(fill="x", padx=10, pady=6)
                    ctk.CTkLabel(inner, text=emoji_l, font=ctk.CTkFont(size=20),
                                 width=36).pack(side="left")
                    txt_box = ctk.CTkFrame(inner, fg_color="transparent")
                    txt_box.pack(side="left", fill="x", expand=True, padx=(8, 0))
                    ctk.CTkLabel(txt_box, text=nombre_l,
                                 font=ctk.CTkFont(size=11, weight="bold"),
                                 anchor="w").pack(anchor="w")
                    ctk.CTkLabel(txt_box, text=desc_l,
                                 font=ctk.CTkFont(size=9),
                                 text_color=text_secondary, anchor="w").pack(anchor="w")
                    ctk.CTkLabel(inner, text="✓",
                                 font=ctk.CTkFont(size=16, weight="bold"),
                                 text_color=accent_green, width=30).pack(side="right")

            if blocked_list:
                ctk.CTkLabel(scroll, text="🔒 Por desbloquear",
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=text_muted).pack(anchor="w", pady=(12, 4))
                for emoji_l, nombre_l, desc_l, _ok, (val, obj) in blocked_list:
                    row = ctk.CTkFrame(scroll, fg_color="transparent")
                    row.pack(fill="x", pady=2)
                    inner = ctk.CTkFrame(row, fg_color="transparent")
                    inner.pack(fill="x", padx=10, pady=4)
                    ctk.CTkLabel(inner, text=emoji_l, font=ctk.CTkFont(size=18),
                                 text_color=text_muted, width=36).pack(side="left")
                    txt_box = ctk.CTkFrame(inner, fg_color="transparent")
                    txt_box.pack(side="left", fill="x", expand=True, padx=(8, 0))
                    ctk.CTkLabel(txt_box, text=nombre_l,
                                 font=ctk.CTkFont(size=11, weight="bold"),
                                 text_color=text_muted, anchor="w").pack(anchor="w")
                    ctk.CTkLabel(txt_box, text=f"{desc_l}  ·  ({val}/{obj})",
                                 font=ctk.CTkFont(size=9),
                                 text_color=text_muted, anchor="w").pack(anchor="w")

            ctk.CTkButton(win, text="Cerrar", width=120, height=30,
                          fg_color="#6b7280", hover_color="#4b5563",
                          command=win.destroy).pack(pady=10)

        ctk.CTkButton(logros_hdr, text="Ver todos", width=80, height=22,
                      fg_color=accent_amber, hover_color="#b45309",
                      font=ctk.CTkFont(size=9, weight="bold"),
                      text_color="#ffffff",
                      command=_abrir_todos_los_logros).pack(side="right")

        # Mostrar primeros 6 desbloqueados o cercanos a desbloquear
        # Ordenar: primero desbloqueados, luego bloqueados con progreso > 50%
        logros_ordenados = sorted(TODOS_LOS_LOGROS,
                                    key=lambda x: (-int(x[3]),
                                                    -(x[4][0] / x[4][1] if x[4][1] else 0)))

        for emoji_l, nombre_l, desc_l, desbloqueado, (val, obj) in logros_ordenados[:6]:
            row = ctk.CTkFrame(logros_frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=1)
            opacity_color = text_primary if desbloqueado else text_muted
            ctk.CTkLabel(row, text=emoji_l, font=ctk.CTkFont(size=14),
                         fg_color="transparent",
                         text_color=opacity_color).pack(side="left", padx=(0, 6))
            txt_l = nombre_l if desbloqueado else f"{nombre_l} ({val}/{obj})"
            ctk.CTkLabel(row, text=txt_l, font=ctk.CTkFont(size=10),
                         fg_color="transparent", text_color=opacity_color,
                         anchor="w").pack(side="left")
            if desbloqueado:
                ctk.CTkLabel(row, text="✓", font=ctk.CTkFont(size=10, weight="bold"),
                             fg_color="transparent", text_color=accent_green).pack(side="right")
        ctk.CTkLabel(logros_frame, text="", fg_color="transparent").pack(pady=2)

        # FEATURE 12 — Reto del día + FEATURE 11 — Estilo del día
        # ratio sugerido e idea precargada. Al aceptar, configura TODO el
        # UI para empezar a trabajar inmediatamente.

        # Cada reto: (descripción visible, modo, modelo, ratio, estilo_match, idea_a_cargar,
        #              [audio_emocion, audio_voz, audio_idioma]) — los 3 últimos solo si modo=audio
        retos_config = [
            ("Genera un retrato fotorrealista en 9:16 sin usar 'beautiful'",
             "imagen", "Z Image Turbo", "9:16", "Fotografía Realista",
             "retrato cercano de una persona en interior, luz natural cálida",
             None, None, None),
            ("Crea un vídeo cinematográfico de 5s con Kling 3.0",
             "video", "Kling 3.0", "16:9", "Cinematográfico",
             "una taza de café humeante en una mesa de madera, lluvia al fondo",
             None, None, None),
            ("Genera una pieza pop con Suno v5",
             "audio", "Suno v5", None, "Pop",
             "una canción pop alegre de verano, voz femenina, 130 bpm",
             "Alegre", "Femenina media", "Español (castellano)"),
            ("Crea un personaje de fantasía épica con FLUX.1",
             "imagen", "FLUX.1 [dev]", "2:3", "Concept Art",
             "guerrera élfica con armadura plateada, bosque encantado al amanecer",
             None, None, None),
            ("Diseña un anime ColorPop vibrante",
             "imagen", "Z Image Turbo", "1:1", "Anime/Manga",
             "chica anime con pelo plateado largo, kimono floral, cherry blossoms",
             None, None, None),
            ("Genera un paisaje épico con DreamShaper",
             "imagen", "DreamShaper", "16:9", "Paisaje",
             "valle montañoso al atardecer, ríos serpenteantes, cielo dorado",
             None, None, None),
            ("Crea una escena cyberpunk neón",
             "imagen", "Z Image Turbo", "16:9", "Cyberpunk",
             "callejón de Tokio futurista de noche, letreros de neón, lluvia, reflejos",
             None, None, None),
            ("Vídeo dramático de 10s con Seedance 2.0",
             "video", "Seedance 2.0", "9:16", "Cinematográfico",
             "primer plano de una llama encendida que se apaga lentamente",
             None, None, None),
            ("Retrato realista con Realistic Vision V6.0",
             "imagen", "Realistic Vision V6.0", "2:3", "Fotografía Realista",
             "hombre de 40 años, barba, mirando a cámara, luz de ventana lateral",
             None, None, None),
            ("Audio acústico melancólico con Suno v4.5",
             "audio", "Suno v4.5", None, "Acústico",
             "guitarra acústica melódica, ambiente cálido y nostálgico",
             "Melancólico", "Masculina media", "Español (castellano)"),
            ("Crea arte conceptual con FLUX.1D UltraReal",
             "imagen", "FLUX.1D UltraReal", "16:9", "Concept Art",
             "ciudad flotante entre nubes, arquitectura art deco futurista",
             None, None, None),
            ("Genera un meme visual divertido",
             "imagen", "Z Image Turbo", "1:1", "Cartoon",
             "un gato mirando con cara seria a un plato vacío, expresión cómica",
             None, None, None),
            ("Vídeo 5s estilo film noir",
             "video", "Kling 3.0", "16:9", "Film Noir",
             "detective con sombrero en un callejón oscuro, humo de cigarrillo",
             None, None, None),
            ("Pieza electrónica synthwave con Suno v5",
             "audio", "Suno v5", None, "Electrónica",
             "track electrónico tipo synthwave, 120 bpm, atmosférico",
             "Enérgico", "Sin voz (instrumental)", "Instrumental"),
        ]

        # Cada estilo: (emoji, nombre, sugerencia, modo, modelo, ratio, idea, [emo, voz, idioma])
        estilos_config = [
            ("🎨", "Cyberpunk Neón", "Combínalo con golden hour para contraste.",
             "imagen", "Z Image Turbo", "16:9",
             "calle de Tokio futurista, luces neón violeta y cian, lluvia",
             None, None, None),
            ("📸", "Fotografía analógica", "Prueba con grano de película 35mm.",
             "imagen", "Realistic Vision V6.0", "3:2",
             "retrato familiar en una cafetería, luz de ventana, look 35mm",
             None, None, None),
            ("🌸", "Anime ColorPop", "Ideal con personajes femeninos y vibrantes.",
             "imagen", "Z Image Turbo", "2:3",
             "chica anime con pelo lila, vestido kawaii, cherry blossoms",
             None, None, None),
            ("🎬", "Cinematográfico", "Añade 'shot on ARRI Alexa, anamorphic lens'.",
             "imagen", "FLUX.1 [dev]", "21:9",
             "escena de thriller en azotea de Manhattan, hora azul",
             None, None, None),
            ("✨", "Art Nouveau", "Bueno para retratos con marcos decorativos.",
             "imagen", "DreamShaper", "2:3",
             "retrato de mujer victoriana con marco Mucha, ornamentos florales",
             None, None, None),
            ("🌌", "Space Opera", "Combina con 'volumetric lighting' para impacto.",
             "imagen", "FLUX.1 [dev]", "21:9",
             "nave espacial atravesando un campo de asteroides, nebulosa púrpura",
             None, None, None),
            ("🏞", "Paisaje épico", "Prueba con 'depth of field' agresivo.",
             "imagen", "DreamShaper", "16:9",
             "cordillera al amanecer, bruma en el valle, lago reflectante",
             None, None, None),
            ("👁", "Surrealismo", "Mezcla objetos imposibles para extrañeza.",
             "imagen", "FLUX.1 [dev]", "1:1",
             "reloj derritiéndose sobre roca tipo Dalí, cielo cálido, sombras largas",
             None, None, None),
            ("🌃", "Synthwave 80s", "Usa magenta, púrpura y cian saturados.",
             "imagen", "Z Image Turbo", "16:9",
             "carretera infinita con sol rosa, montañas geométricas, grid retro",
             None, None, None),
            ("⛩", "Estilo japonés", "Combina con cherry blossoms o templos.",
             "imagen", "Z Image Turbo", "2:3",
             "templo japonés tradicional, cherry blossoms, atardecer dorado",
             None, None, None),
            ("🎭", "Barroco", "Iluminación tipo Caravaggio, claroscuros fuertes.",
             "imagen", "Realistic Vision V6.0", "2:3",
             "retrato barroco con iluminación tenebrista, fondo oscuro",
             None, None, None),
            ("🌿", "Solarpunk", "Naturaleza + tecnología + colores cálidos.",
             "imagen", "FLUX.1 [dev]", "16:9",
             "ciudad futurista cubierta de vegetación, paneles solares orgánicos",
             None, None, None),
        ]

        day_idx = _dt.date.today().toordinal()
        reto_cfg = retos_config[day_idx % len(retos_config)]
        estilo_cfg = estilos_config[day_idx % len(estilos_config)]

        # Helper común para aplicar configuración completa al UI
        def _aplicar_config_completa(modo, modelo, ratio, estilo_match, idea,
                                       audio_emocion=None, audio_voz=None, audio_idioma=None):
            """Configura modo, modelo, ratio, estilo (si encaja), audio fields y precarga idea."""
            try:
                # 1. Cambiar modo
                if modo and hasattr(self, "modo_var"):
                    self.modo_var.set(modo)
                    if hasattr(self, "_on_modo_cambio"):
                        try: self._on_modo_cambio()
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
            except Exception as e:
                logger.debug(f"[silent] {e}")

            # Tras el cambio de modo, los combos podrían recrearse — usamos
            # un pequeño delay antes de aplicar lo demás.
            def _continuar():
                try:
                    # 2. Cambiar modelo según el modo
                    if modelo and modo:
                        try:
                            if modo == "imagen" and hasattr(self, "combo_modelo_imagen"):
                                self.combo_modelo_imagen.set(modelo)
                                if hasattr(self, "_on_modelo_imagen_cambio"):
                                    try: self._on_modelo_imagen_cambio()
                                    except Exception as e:
                                        logger.debug(f"[silent] {e}")
                            elif modo == "video" and hasattr(self, "combo_modelo_video"):
                                self.combo_modelo_video.set(modelo)
                                if hasattr(self, "_on_motor_cambio"):
                                    try: self._on_motor_cambio()
                                    except Exception as e:
                                        logger.debug(f"[silent] {e}")
                            elif modo == "audio" and hasattr(self, "combo_modelo_audio"):
                                self.combo_modelo_audio.set(modelo)
                                if hasattr(self, "_on_motor_audio_cambio"):
                                    try: self._on_motor_audio_cambio()
                                    except Exception as e:
                                        logger.debug(f"[silent] {e}")
                        except Exception as e:
                            logger.debug(f"[silent] {e}")

                    # 3. Cambiar ratio si es relevante (ignora None para audio)
                    if ratio and hasattr(self, "ratio_var"):
                        try:
                            self.ratio_var.set(ratio)
                        except Exception as e:
                            logger.debug(f"[silent] {e}")

                    # 4. Marcar estilo (buscar match en estilo_checks)
                    if estilo_match and hasattr(self, "estilo_checks"):
                        # Limpiar otros estilos primero
                        try:
                            for n_chk, v_chk in self.estilo_checks.items():
                                v_chk.set(False)
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
                        # Buscar match
                        try:
                            match_lower = estilo_match.lower()
                            for nombre_chk, var_chk in self.estilo_checks.items():
                                if (match_lower in nombre_chk.lower() or
                                        nombre_chk.lower() in match_lower):
                                    var_chk.set(True)
                                    break
                        except Exception as e:
                            logger.debug(f"[silent] {e}")

                    # 5. Configurar campos de audio si aplica
                    if modo == "audio":
                        try:
                            if audio_emocion and hasattr(self, "emocion_var"):
                                self.emocion_var.set(audio_emocion)
                                if hasattr(self, "_on_audio_filtro_cambio"):
                                    try: self._on_audio_filtro_cambio()
                                    except Exception as e:
                                        logger.debug(f"[silent] {e}")
                            if audio_voz and hasattr(self, "voz_var"):
                                self.voz_var.set(audio_voz)
                            if audio_idioma and hasattr(self, "idioma_audio_var"):
                                self.idioma_audio_var.set(audio_idioma)
                            # Si es instrumental, activar el switch
                            if audio_voz and "instrumental" in audio_voz.lower():
                                if hasattr(self, "switch_instrumental_var"):
                                    try: self.switch_instrumental_var.set(True)
                                    except Exception as e:
                                        logger.debug(f"[silent] {e}")
                        except Exception as e:
                            logger.debug(f"[silent] {e}")

                    # 6. Cargar idea
                    if idea:
                        try:
                            self.txt_idea.delete("1.0", "end")
                            self.txt_idea.insert("1.0", idea)
                            self.txt_idea.focus_set()
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
                except Exception as e:
                    logger.debug(f"[silent] {e}")

            # Aplicar en cascada con un delay tras el cambio de modo
            self.after(150, _continuar)

        # ── Reto del día ──────────────────────────────────────
        (reto_desc, reto_modo, reto_modelo, reto_ratio, reto_estilo, reto_idea,
         reto_emo, reto_voz, reto_idioma) = reto_cfg

        reto_frame = ctk.CTkFrame(col_der, fg_color=card_bg, corner_radius=10,
                                   border_color=accent_blue, border_width=2)
        reto_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(reto_frame, text="🎯 Reto del día",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     fg_color="transparent", text_color=accent_blue).pack(anchor="w", padx=12, pady=(10, 4))
        ctk.CTkLabel(reto_frame, text=reto_desc,
                     font=ctk.CTkFont(size=11, weight="bold"), wraplength=280,
                     fg_color="transparent", text_color=text_primary,
                     anchor="w", justify="left").pack(fill="x", padx=12, pady=(0, 4))

        # Línea de detalles (modo + modelo + audio extras si aplica)
        emoji_modo_r = {"imagen": "🖼", "video": "🎬", "audio": "🎵"}.get(reto_modo, "•")
        ratio_str_r = f" · {reto_ratio}" if reto_ratio else ""
        detalles_r = f"{emoji_modo_r} {reto_modelo}{ratio_str_r} · {reto_estilo}"
        if reto_modo == "audio" and reto_emo:
            detalles_r += f"\n💗 {reto_emo} · 🎤 {reto_voz} · 🌐 {reto_idioma}"
        ctk.CTkLabel(reto_frame, text=detalles_r,
                     font=ctk.CTkFont(size=9, slant="italic"), wraplength=280,
                     fg_color="transparent", text_color=text_secondary,
                     anchor="w", justify="left").pack(fill="x", padx=12, pady=(0, 6))

        def _aceptar_reto():
            _aplicar_config_completa(reto_modo, reto_modelo, reto_ratio,
                                       reto_estilo, reto_idea,
                                       reto_emo, reto_voz, reto_idioma)
            self.set_estado(f"🎯 Reto activado: {emoji_modo_r} {reto_modelo}", accent_blue)
            v.destroy()

        ctk.CTkButton(reto_frame, text="🎯 Aceptar reto",
                      height=28, fg_color=accent_blue, hover_color="#1d4ed8",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      text_color="#ffffff",
                      command=_aceptar_reto).pack(fill="x", padx=12, pady=(0, 10))

        # ── Estilo del día ────────────────────────────────────
        (emoji_est, nombre_est, sugerencia_est, est_modo, est_modelo, est_ratio,
         est_idea, est_emo, est_voz, est_idioma) = estilo_cfg

        estilo_frame = ctk.CTkFrame(col_der, fg_color=card_bg, corner_radius=10,
                                     border_color=accent_pink, border_width=2)
        estilo_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(estilo_frame, text=f"{emoji_est} Estilo del día",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     fg_color="transparent", text_color=accent_pink).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(estilo_frame, text=nombre_est,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     fg_color="transparent", text_color=text_primary).pack(anchor="w", padx=12)
        ctk.CTkLabel(estilo_frame, text=sugerencia_est,
                     font=ctk.CTkFont(size=10, slant="italic"), wraplength=280,
                     fg_color="transparent", text_color=text_secondary,
                     anchor="w", justify="left").pack(fill="x", padx=12, pady=(2, 4))

        # Detalles modo + modelo
        emoji_modo_e = {"imagen": "🖼", "video": "🎬", "audio": "🎵"}.get(est_modo, "•")
        ratio_str_e = f" · {est_ratio}" if est_ratio else ""
        detalles_e = f"{emoji_modo_e} {est_modelo}{ratio_str_e}"
        if est_modo == "audio" and est_emo:
            detalles_e += f"\n💗 {est_emo} · 🎤 {est_voz}"
        ctk.CTkLabel(estilo_frame, text=detalles_e,
                     font=ctk.CTkFont(size=9, slant="italic"), wraplength=280,
                     fg_color="transparent", text_color=text_secondary,
                     anchor="w", justify="left").pack(fill="x", padx=12, pady=(0, 6))

        def _probar_estilo():
            _aplicar_config_completa(est_modo, est_modelo, est_ratio,
                                       nombre_est, est_idea,
                                       est_emo, est_voz, est_idioma)
            self.set_estado(f"{emoji_est} Estilo «{nombre_est}» activado", accent_pink)
            v.destroy()

        ctk.CTkButton(estilo_frame, text=f"{emoji_est} Probar este estilo",
                      height=28, fg_color=accent_pink, hover_color="#be185d",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      text_color="#ffffff",
                      command=_probar_estilo).pack(fill="x", padx=12, pady=(0, 10))

        # FEATURE 14 — Mood Aleatorio
        def _mood_aleatorio():
            try:
                from config import ESTILOS_IMAGEN
                # Limpiar separadores y nombres no válidos
                estilos_validos = [e for e in ESTILOS_IMAGEN if not str(e).startswith("─")]
                if len(estilos_validos) < 3:
                    return
                muestra = _rnd.sample(estilos_validos, k=min(3, len(estilos_validos)))
                # Aplicar al UI
                for nombre_est, var_est in self.estilo_checks.items():
                    var_est.set(nombre_est in muestra)
                self.set_estado(f"🎲 Mood aplicado: {' + '.join(muestra)}", accent_pink)
                v.destroy()
            except Exception as ex:
                self.set_estado(f"⚠️ Error en mood: {ex}", accent_red)

        ctk.CTkButton(col_der, text="🎲 Inspírame con Mood Aleatorio",
                      height=36, fg_color=accent_pink, hover_color="#be185d",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      text_color="#ffffff",
                      command=_mood_aleatorio).pack(fill="x", pady=(0, 10))

        # FEATURE 9 — Atajos de teclado
        atajos_frame = ctk.CTkFrame(col_izq, fg_color=card_bg, corner_radius=10,
                                     border_color=card_border, border_width=1)
        atajos_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(atajos_frame, text="⌨️ Atajos de teclado",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     fg_color="transparent", text_color=text_primary).pack(anchor="w", padx=12, pady=(10, 4))
        atajos = [
            ("Alt+1", "Modo imagen"),
            ("Alt+2", "Modo vídeo"),
            ("Alt+3", "Modo audio"),
            ("Alt+Enter", "Quick generate"),
            ("Ctrl+1", "Copiar POSITIVE"),
            ("Ctrl+2", "Copiar NEGATIVE"),
            ("Ctrl+D", "Duplicar al historial"),
            ("Ctrl+E", "Exportar rápido"),
            ("Ctrl+Enter", "Generar prompt"),
            ("Ctrl+F", "Búsqueda global"),
            ("Ctrl+H", "Modo Focus"),
            ("Ctrl+I", "Ideas creativas"),
            ("Ctrl+L", "Abrir LoRAs"),
            ("Ctrl+P", "Grupo personajes"),
            ("Ctrl+R", "Idea aleatoria"),
            ("Ctrl+S", "Guardar favorito"),
            ("Ctrl+Shift+A", "Analizar imagen"),
            ("Ctrl+Shift+Enter", "Variaciones x3"),
            ("Ctrl+Shift+L", "Cambiar tema"),
            ("Ctrl+Shift+N", "Negative builder"),
            ("Ctrl+Shift+P", "Previsualizar"),
            ("Ctrl+Shift+S", "Guardar estrella"),
            ("Ctrl+Shift+T", "Traducir idea"),
            ("Ctrl+T", "Abrir tutorial"),
            ("Ctrl+V", "Pegar inteligente"),
            ("Ctrl+?", "Mostrar todos"),
            ("Escape", "Cerrar popup"),
            ("F11", "Pantalla completa"),
]
        # 3 columnas para atajos
        atajos_cols = ctk.CTkFrame(atajos_frame, fg_color="transparent")
        atajos_cols.pack(fill="x", padx=6, pady=(2, 6))
        atajos_cols.grid_columnconfigure(0, weight=1)
        atajos_cols.grid_columnconfigure(1, weight=1)
        atajos_cols.grid_columnconfigure(2, weight=1)

        # Dividir atajos en 3 grupos (9, 9, 10)
        n = len(atajos)
        tercio = (n + 2) // 3
        grupos_atajos = [atajos[i*tercio:(i+1)*tercio] for i in range(3)]

        for grupo in grupos_atajos:
            col_frame = ctk.CTkFrame(atajos_cols, fg_color="transparent")
            col_frame.pack(side="left", fill="both", expand=True, padx=4)
            for combo, accion in grupo:
                row = ctk.CTkFrame(col_frame, fg_color="transparent")
                row.pack(fill="x", pady=0)
                ctk.CTkLabel(row, text=combo,
                             font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
                             fg_color=card_bg_alt, corner_radius=3,
                             text_color=accent_blue, width=88, anchor="center").pack(side="left", padx=(0, 5))
                ctk.CTkLabel(row, text=accion, font=ctk.CTkFont(size=9),
                             fg_color="transparent", text_color=text_secondary,
                             anchor="w").pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(atajos_frame, text="", fg_color="transparent").pack(pady=2)

        # FEATURES 15, 16, 17 — Mantenimiento
        mant_frame = ctk.CTkFrame(col_der, fg_color=card_bg, corner_radius=10,
                                   border_color=card_border, border_width=1)
        mant_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(mant_frame, text="🧹 Mantenimiento",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     fg_color="transparent", text_color=text_primary).pack(anchor="w", padx=12, pady=(10, 4))

        # Tamaño de datos
        try:
            from config import CARPETA_APP
            base = CARPETA_APP
            total_bytes = 0
            # Solo archivos en la raíz de la carpeta (excluye logs/ y backups/)
            for f in base.iterdir():
                try:
                    if f.is_file():
                        total_bytes += f.stat().st_size
                except Exception:
                    pass
            if total_bytes < 1024:
                tamano_str = f"{total_bytes} B"
            elif total_bytes < 1024 * 1024:
                tamano_str = f"{total_bytes / 1024:.1f} KB"
            else:
                tamano_str = f"{total_bytes / (1024*1024):.1f} MB"
        except Exception:
            tamano_str = "—"

        ctk.CTkLabel(mant_frame, text=f"📦 Tus datos: {tamano_str}",
                     font=ctk.CTkFont(size=10),
                     fg_color="transparent", text_color=text_secondary).pack(anchor="w", padx=12, pady=2)

        # Sugerencia limpiar historial
        if len(historial) >= 80:
            def _limpiar_historial():
                v.destroy()
                try:
                    self.store.limpiar_historial()
                    self.set_estado("🧹 Historial limpiado", accent_green)
                except Exception:
                    pass
            ctk.CTkButton(mant_frame, text=f"🧹 Limpiar historial ({len(historial)} prompts)",
                          height=28, fg_color=accent_amber, hover_color="#b45309",
                          font=ctk.CTkFont(size=9, weight="bold"),
                          text_color="#ffffff",
                          command=_limpiar_historial).pack(fill="x", padx=12, pady=2)

        # Backup ahora
        def _backup_ahora():
            try:
                import time as _t
                from config import CARPETA_APP, ARCHIVOS
                base = CARPETA_APP
                marker = ARCHIVOS["autobackup_marker"]
                self._crear_backup_automatico(base, marker, _t.time())
                self.set_estado("💾 Backup hecho", accent_green)
            except Exception as ex:
                self.set_estado(f"⚠️ Error backup: {ex}", accent_red)
        ctk.CTkButton(mant_frame, text="💾 Hacer backup ahora",
                      height=28, fg_color=accent_blue, hover_color="#1d4ed8",
                      font=ctk.CTkFont(size=9, weight="bold"),
                      text_color="#ffffff",
                      command=_backup_ahora).pack(fill="x", padx=12, pady=(2, 8))

        # ── TIP DEL DÍA (card separado, debajo de mantenimiento) ──
        tips = [
            "Usa pesos como (masterpiece:1.3) para enfatizar.",
            "Negative: empieza con 'ugly, blurry, deformed'.",
            "Añade 'shot on 35mm' para fotos realistas.",
            "Especifica la hora: 'golden hour', 'blue hour'.",
            "Incluye material: 'silk', 'chrome', 'weathered wood'.",
            "Usa 'depth of field, f/1.4' para fondos cremosos.",
            "Prueba composiciones diagonales para dinamismo.",
            "Añade 'volumetric lighting' para rayos de luz.",
            "Usa 'rule of thirds' para mejor composición.",
            "Incluye 'color grading, teal and orange'.",
        ]
        day_idx = _dt.datetime.now().day
        tip = tips[day_idx % len(tips)]

        tip_frame = ctk.CTkFrame(col_der, fg_color=card_bg, corner_radius=10,
                                 border_color=accent_amber, border_width=2)
        tip_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(tip_frame, text="💡 Tip del día",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     fg_color="transparent", text_color=accent_amber).pack(anchor="w", padx=12, pady=(10, 4))
        ctk.CTkLabel(tip_frame, text=tip,
                     font=ctk.CTkFont(size=10, slant="italic"),
                     fg_color="transparent", text_color=text_primary,
                     wraplength=280, justify="left").pack(fill="x", padx=12, pady=(0, 10))

        # ACCIONES RÁPIDAS — Bloque inferior, ancho completo
        ctk.CTkLabel(main, text="✨ Acciones rápidas",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     fg_color="transparent", text_color=text_primary).pack(anchor="w", pady=(8, 4))

        acciones_rapidas = [
            ("✨ Generar Prompt", self.cmd_prompt, accent_blue, "IA genera un prompt completo"),
            ("⚡ Quick Generate", getattr(self, "cmd_prompt_quick", self.cmd_prompt),
             accent_amber, "Generación rápida y barata"),
            ("💡 Ideas Aleatorias", self.cmd_ideas, accent_green, "Genera 3 ideas creativas"),
            ("🔄 Variaciones", self.cmd_variaciones, "#7c3aed", "Crea variantes del prompt"),
            ("📝 Refinar", getattr(self, "cmd_refinar", self.cmd_prompt),
             "#db2777", "Mejora el prompt actual"),
            ("📦 Batch", self.cmd_batch, "#e84393", "Genera múltiples prompts"),
        ]

        quick_grid = ctk.CTkFrame(main, fg_color="transparent")
        quick_grid.pack(fill="x", pady=(0, 10))
        for col in range(3):
            quick_grid.grid_columnconfigure(col, weight=1)
        for i, (label, cmd, color, tip) in enumerate(acciones_rapidas):
            col, row = i % 3, i // 3
            def _make_handler(c=cmd):
                def _h():
                    v.destroy()
                    try: c()
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
                return _h
            card = ctk.CTkButton(quick_grid, text=f"{label}\n{tip}", width=200, height=56,
                                  fg_color=card_bg, hover_color="#e5e7eb" if is_light else "#1f2937",
                                  corner_radius=8, border_color=card_border, border_width=1,
                                  font=ctk.CTkFont(size=11, weight="bold"),
                                  text_color=text_primary,
                                  command=_make_handler(), compound="top")
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

        # HERRAMIENTAS — Bloque inferior
        ctk.CTkLabel(main, text="🛠 Herramientas",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     fg_color="transparent", text_color=text_primary).pack(anchor="w", pady=(8, 4))

        herramientas = [
            ("🎯 Scoring", self._cmd_scoring),
            ("📊 Estadísticas", self._abrir_estadisticas),
            ("📐 Fórmulas", self._abrir_formulas),
            ("🏷️ Añadir tags", self._abrir_snippets),
            ("📋 Plantillas", self._cmd_plantillas_populares),
            ("💎 Seeds", self._abrir_seeds_favoritos),
            ("🔄 Macros", self._abrir_macros),
            ("📁 Proyectos", self._cmd_proyectos),
        ]

        tools_frame = ctk.CTkFrame(main, fg_color="transparent")
        tools_frame.pack(fill="x", pady=(0, 10))
        for col in range(4):
            tools_frame.grid_columnconfigure(col, weight=1)

        for i, (label, cmd) in enumerate(herramientas):
            col, row = i % 4, i // 4
            def _make_handler(c=cmd):
                def _h():
                    v.destroy()
                    try: c()
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
                return _h
            card = ctk.CTkButton(tools_frame, text=label, width=160, height=38,
                                  fg_color=card_bg, hover_color="#e5e7eb" if is_light else "#1f2937",
                                  corner_radius=8, border_color=card_border, border_width=1,
                                  font=ctk.CTkFont(size=10, weight="bold"),
                                  text_color=text_primary,
                                  command=_make_handler())
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

        # Botón cerrar al final
        ctk.CTkButton(main, text="🚪 Cerrar Dashboard", width=180, height=34,
                      fg_color="#6b7280", hover_color="#4b5563",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      text_color="#ffffff",
                      command=v.destroy).pack(pady=(12, 8))

