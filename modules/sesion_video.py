"""Sesión vídeo — grabar/exportar/tutorial-mode + log de eventos.

Métodos relacionados con la "sesión" del usuario:
  • _sesion_init / _sesion_log              — inicializar log + registrar
                                              eventos (texto plano).
  • _sesion_video_disponible / _iniciar     — chequeo de dependencias.
  • _sesion_video_iniciar / _worker /
    _detener / _cmd_sesion_grabar_toggle    — grabación de pantalla con
                                              cv2/mss en thread.
  • _iniciar_grabacion                      — wrapper de inicio.
  • _cmd_sesion_exportar                    — exportar Markdown/HTML
                                              con eventos + ruta a vídeo.
  • _cmd_sesion_modo_tutorial               — narración paso a paso.
  • _sesion_agrupar_pasos / _narrar_paso    — helpers de narración.

Dependencias self (provistas por ArquitectoApp):
  after, set_estado, store (preferencias), llm_var, modo_var,
  txt_idea, txt_salida y atributos _sesion_* internos.
"""
import datetime
import logging
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pyperclip

from config import get_theme_colors as _get_tc
from modules.gprompt_window import GPromptWindow
from modules.i18n import tr

logger = logging.getLogger(__name__)


class SesionVideoService:
    """Grabación de sesión + log + exportación tutorial.

    A1 fase 2 (sesión 14): servicio aislado con app por composición.
    """

    def __init__(self, app):
        self.app = app

    def _sesion_init(self) -> None:
        """Inicializa el registro de sesión si no existe."""
        if not hasattr(self.app, "_sesion_eventos"):
            self.app._sesion_eventos = []
            self.app._sesion_grabando = False
            self.app._sesion_inicio = None
            self.app._sesion_video_thread = None
            self.app._sesion_video_path = None
            self.app._sesion_video_writer = None
            self.app._sesion_video_running = False

    def _sesion_log(self, evento):
        """Añade un evento al registro si está grabando."""
        self._sesion_init()
        if not self.app._sesion_grabando: return
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.app._sesion_eventos.append((ts, evento))

    def _sesion_video_disponible(self) -> None:
        """Comprueba si las dependencias para grabar vídeo están instaladas."""
        try:
            import mss  # noqa
            import imageio  # noqa
            return True
        except ImportError:
            return False

    def _sesion_video_iniciar(self, solo_app=False):
        """Arranca la grabación de vídeo en thread separado. solo_app=True captura solo la ventana."""
        if not self._sesion_video_disponible():
            return False
        self.app._sesion_solo_app = solo_app
        try:
            import os

            import imageio
            # Crear directorio de salida si no existe
            output_dir = os.path.join(os.path.expanduser("~"), "GPromptStudio_videos")
            os.makedirs(output_dir, exist_ok=True)
            # Path del vídeo
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.app._sesion_video_path = os.path.join(output_dir, f"sesion_{ts}.mp4")
            # Configurar writer (5 FPS, codec H.264)
            self.app._sesion_video_writer = imageio.get_writer(
                self.app._sesion_video_path,
                fps=5,
                codec="libx264",
                quality=7,
                pixelformat="yuv420p",
                macro_block_size=1,
            )
            self.app._sesion_video_running = True
            self.app._sesion_video_thread = threading.Thread(
                target=self._sesion_video_worker, daemon=True
            )
            self.app._sesion_video_thread.start()
            return True
        except Exception as e:
            self.app._sesion_video_writer = None
            self.app._sesion_video_running = False
            self.app.dialogs.set_estado(tr('⚠️ Error iniciando vídeo: {0}').format(e), "#e74c3c")
            return False

    def _sesion_video_worker(self) -> None:
        """Thread worker: captura pantalla a 5 FPS y la pasa al writer."""
        try:
            import time

            import mss
            import numpy as np

            solo_app = getattr(self.app, '_sesion_solo_app', False)

            with mss.mss() as sct:
                interval = 0.2  # 5 FPS
                next_t = time.time()
                while self.app._sesion_video_running:
                    if solo_app:
                        # Capturar solo la región de la ventana de la app
                        try:
                            # Obtener posición y tamaño de la ventana
                            x = self.app.winfo_x()
                            y = self.app.winfo_y()
                            w = self.app.winfo_width()
                            h = self.app.winfo_height()

                            # Ajustar a múltiplo de 2 (H.264 requiere dimensiones pares)
                            w = w if w % 2 == 0 else w - 1
                            h = h if h % 2 == 0 else h - 1

                            # Capturar región
                            monitor = {"left": x, "top": y, "width": w, "height": h}
                            img = sct.grab(monitor)
                        except Exception:
                            # Si falla, capturar toda la pantalla
                            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                            # Ajustar también
                            monitor = dict(monitor)
                            if monitor["width"] % 2 != 0:
                                monitor["width"] -= 1
                            if monitor["height"] % 2 != 0:
                                monitor["height"] -= 1
                            img = sct.grab(monitor)
                    else:
                        # Capturar toda la pantalla
                        monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
                        img = sct.grab(monitor)

                    # Convertir BGRA → RGB
                    frame = np.array(img)[:, :, [2, 1, 0]]  # BGRA→RGB
                    try:
                        self.app._sesion_video_writer.append_data(frame)
                    except Exception:
                        break
                    # Mantener cadencia 5 FPS
                    next_t += interval
                    delta = next_t - time.time()
                    if delta > 0:
                        time.sleep(delta)
                    else:
                        next_t = time.time()
        except Exception as e:
            self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('⚠️ Vídeo se detuvo: {0}').format(e), "#e74c3c"))

    def _sesion_video_detener(self) -> None:
        """Detiene grabación y cierra el archivo. Devuelve la ruta del MP4 o None."""
        self.app._sesion_video_running = False
        # Esperar al thread (max 1.5s)
        if self.app._sesion_video_thread:
            try: self.app._sesion_video_thread.join(timeout=1.5)
            except Exception as e:
                logger.debug(f"[silent] {e}")
        # Cerrar writer
        if self.app._sesion_video_writer:
            try: self.app._sesion_video_writer.close()
            except Exception as e:
                logger.debug(f"[silent] {e}")
        path = self.app._sesion_video_path
        self.app._sesion_video_writer = None
        self.app._sesion_video_path = None
        self.app._sesion_video_thread = None
        return path

    def _cmd_sesion_grabar_toggle(self) -> None:
        """Inicia / detiene la grabación de sesión (con o sin vídeo según preferencia)."""
        self._sesion_init()
        if not self.app._sesion_grabando:
            # Preguntar tipo de grabación de vídeo si el switch está ON
            if getattr(self.app, '_sesion_grabar_video', False):
                if self._sesion_video_disponible():
                    # Ventana de selección
                    sel = GPromptWindow(self.app)
                    sel.title(tr("🎬 Tipo de grabación"))
                    sel.geometry("350x180")
                    sel.transient(self.app)
                    sel.grab_set()

                    ctk.CTkLabel(sel, text=tr("¿Qué quieres grabar en vídeo?"), font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(15, 10))
                    ctk.CTkLabel(sel, text=tr("(La grabación de texto siempre está activa)"), font=ctk.CTkFont(size=10), text_color="#888").pack(pady=(0, 15))

                    def _iniciar(tipo):
                        self.app._sesion_tipo_video = tipo
                        sel.destroy()
                        self._iniciar_grabacion(tipo)

                    ctk.CTkButton(sel, text=tr("📱 Solo ventana de la app"), width=250, height=35, fg_color="#1a6a3a",
                                  command=lambda: _iniciar("app")).pack(pady=5)
                    ctk.CTkButton(sel, text=tr("🖥️ Toda la pantalla"), width=250, height=35, fg_color="#1a4a7a",
                                  command=lambda: _iniciar("pantalla")).pack(pady=5)
                    ctk.CTkButton(sel, text=tr("❌ Sin vídeo (solo texto)"), width=250, height=30, fg_color="#5a1a1a",
                                  command=lambda: _iniciar("nada")).pack(pady=5)
                    return
                else:
                    self._sesion_log("⚠️ Vídeo no disponible: instala 'mss' e 'imageio[ffmpeg]'")

            # Sin vídeo o no disponible
            self._iniciar_grabacion("nada")
        else:
            # Parar
            self._sesion_log("⏹ GRABACIÓN DETENIDA")
            self.app._sesion_grabando = False
            video_path = None
            if self.app._sesion_video_running or self.app._sesion_video_writer:
                self.app.dialogs.set_estado(tr("⏹ Cerrando vídeo..."))
                video_path = self._sesion_video_detener()
            self._cmd_sesion_exportar(video_path=video_path)

    def _iniciar_grabacion(self, tipo_video):
        """Inicia la grabación con el tipo de vídeo especificado.

        `tipo_video`: "nada" | "app" | "pantalla". (La rama `else` previa
        replicaba el código de "parar" del toggle pero era dead code —
        esta función solo se llama desde el flujo de inicio).
        """
        self.app._sesion_eventos = []
        self.app._sesion_grabando = True
        self.app._sesion_inicio = datetime.datetime.now()
        self._sesion_log("🔴 GRABACIÓN INICIADA")

        if tipo_video == "nada":
            self.app.dialogs.set_estado(tr("🔴 Grabando sesión (sin vídeo)... Click 🎬 para parar"), "#e74c3c")
        elif tipo_video == "app":
            if self._sesion_video_iniciar(solo_app=True):
                self._sesion_log("🎥 Grabación de vídeo (solo app, 5 FPS)")
                self.app.dialogs.set_estado(tr("🔴 Grabando sesión + 🎥 app... Click 🎬 para parar"), "#e74c3c")
            else:
                self.app.dialogs.set_estado(tr("🔴 Grabando solo texto. Click 🎬 para parar"), "#e67e22")
        elif tipo_video == "pantalla":
            if self._sesion_video_iniciar(solo_app=False):
                self._sesion_log("🎥 Grabación de vídeo (pantalla completa, 5 FPS)")
                self.app.dialogs.set_estado(tr("🔴 Grabando sesión + 🎥 pantalla... Click 🎬 para parar"), "#e74c3c")
            else:
                self.app.dialogs.set_estado(tr("🔴 Grabando solo texto. Click 🎬 para parar"), "#e67e22")

    def _cmd_sesion_exportar(self, video_path=None):
        """Abre ventana con el log de la sesión y opciones de exportación.
        Si video_path está dado, también muestra info del MP4 y botón para abrirlo."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        self._sesion_init()
        if not self.app._sesion_eventos:
            self.app.dialogs.set_estado(tr("⚠️ No hay eventos grabados"), "#e67e22")
            return

        v = GPromptWindow(self.app)
        v.title(tr("🎬 Sesión grabada"))
        v.geometry("780x640")
        v.transient(self.app)

        ctk.CTkLabel(v, text=tr("🎬 Registro de sesión"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4))
        dur = ""
        if self.app._sesion_inicio:
            delta = datetime.datetime.now() - self.app._sesion_inicio
            mins = int(delta.total_seconds() // 60)
            secs = int(delta.total_seconds() % 60)
            dur = f"  ·  duración: {mins}m {secs}s"
        ctk.CTkLabel(v, text=tr('{0} eventos{1}').format((len(self.app._sesion_eventos)), (dur)),
                     font=ctk.CTkFont(size=11), text_color="#888").pack(pady=(0, 4))

        # ── Banner con info del vídeo si se grabó ──
        if video_path:
            import os as _os
            try:
                tam_mb = _os.path.getsize(video_path) / (1024 * 1024)
                video_info = f"🎥 Vídeo guardado: {_os.path.basename(video_path)}  ·  {tam_mb:.1f} MB"
            except Exception:
                video_info = f"🎥 Vídeo guardado: {_os.path.basename(video_path)}"
            video_banner = ctk.CTkFrame(v, fg_color="#1a3a5a", corner_radius=6)
            video_banner.pack(fill="x", padx=15, pady=(0, 8))
            ctk.CTkLabel(video_banner, text=video_info, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=c["hdr_text"]).pack(side="left", padx=12, pady=8)

            def _abrir_carpeta():
                try:
                    import subprocess
                    import sys
                    folder = _os.path.dirname(video_path)
                    if sys.platform == "win32":
                        _os.startfile(folder)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", folder])
                    else:
                        subprocess.run(["xdg-open", folder])
                except Exception as e:
                    self.app.dialogs.set_estado(tr('⚠️ No se pudo abrir: {0}').format(e), "#e74c3c")

            def _abrir_video():
                try:
                    import subprocess
                    import sys
                    if sys.platform == "win32":
                        _os.startfile(video_path)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", video_path])
                    else:
                        subprocess.run(["xdg-open", video_path])
                except Exception as e:
                    self.app.dialogs.set_estado(tr('⚠️ Error: {0}').format(e), "#e74c3c")

            ctk.CTkButton(video_banner, text=tr("📁 Abrir carpeta"), width=120, height=24,
                          fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                          command=_abrir_carpeta).pack(side="right", padx=4, pady=6)
            ctk.CTkButton(video_banner, text=tr("▶ Reproducir"), width=110, height=24,
                          fg_color="#1e5f3a", hover_color="#16492d",
                          command=_abrir_video).pack(side="right", padx=4, pady=6)

        # Construir texto
        lines_md = ["# Registro de sesión",
                    f"_Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}_",
                    "",
                    "| Hora | Evento |",
                    "| --- | --- |"]
        lines_txt = [f"REGISTRO DE SESIÓN",
                     f"Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
                     "=" * 60, ""]
        for ts, evento in self.app._sesion_eventos:
            lines_md.append(f"| {ts} | {evento} |")
            lines_txt.append(f"[{ts}]  {evento}")

        texto_md = "\n".join(lines_md)
        texto_txt = "\n".join(lines_txt)

        # Preview
        txt = ctk.CTkTextbox(v, wrap="none", font=ctk.CTkFont(family="Consolas", size=11))
        txt.pack(fill="both", expand=True, padx=15, pady=5)
        txt.insert("1.0", texto_txt)

        btn_row = ctk.CTkFrame(v, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 12))

        def _exp_md():
            ruta = filedialog.asksaveasfilename(
                defaultextension=".md",
                filetypes=[("Markdown", "*.md"), (tr("Todos"), "*.*")],
                initialfile=f"sesion_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.md",
                parent=v)
            if ruta:
                try:
                    with open(ruta, "w", encoding="utf-8") as fp: fp.write(texto_md)
                    self.app.dialogs.set_estado(tr('📄 Exportado: {0}').format(ruta), "#2ecc71")
                except Exception as e:
                    self.app.dialogs.set_estado(tr('⚠️ Error: {0}').format(e), "#e74c3c")

        def _exp_txt():
            ruta = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[(tr("Texto"), "*.txt"), (tr("Todos"), "*.*")],
                initialfile=f"sesion_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                parent=v)
            if ruta:
                try:
                    with open(ruta, "w", encoding="utf-8") as fp: fp.write(texto_txt)
                    self.app.dialogs.set_estado(tr('📄 Exportado: {0}').format(ruta), "#2ecc71")
                except Exception as e:
                    self.app.dialogs.set_estado(tr('⚠️ Error: {0}').format(e), "#e74c3c")

        def _limpiar():
            if messagebox.askyesno(tr("Limpiar registro"), tr("¿Borrar todos los eventos grabados?"), parent=v):
                self.app._sesion_eventos = []
                self.app._sesion_inicio = None
                v.destroy()
                self.app.dialogs.set_estado(tr("🗑 Registro de sesión limpiado"))

        ctk.CTkButton(btn_row, text=tr("📄 Exportar .md"), width=130, command=_exp_md,
                      fg_color="#1e5f3a", hover_color="#16492d").pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text=tr("📄 Exportar .txt"), width=130, command=_exp_txt,
                      fg_color="#1e5f3a", hover_color="#16492d").pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text=tr("📚 Modo Tutorial"), width=140,
                      command=lambda: self._cmd_sesion_modo_tutorial(),
                      fg_color="#5b2c8e", hover_color="#3d1a6a").pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text=tr("🗑 Limpiar"), width=110, command=_limpiar,
                      fg_color="#6a1a1a", hover_color="#4a0f0f").pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text=tr("Cerrar"), width=110, command=v.destroy,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"]).pack(side="right", padx=2)

    def _cmd_sesion_modo_tutorial(self) -> None:
        """Modo Tutorial: convierte el log en un guion paso a paso para tutoriales de YouTube."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        if not self.app._sesion_eventos:
            self.app.dialogs.set_estado(tr("⚠️ No hay eventos grabados"), "#e67e22")
            return

        # Agrupar eventos en pasos lógicos según los tipos
        pasos = self._sesion_agrupar_pasos(self.app._sesion_eventos)

        v = GPromptWindow(self.app)
        v.title(tr("📚 Modo Tutorial — Guion para YouTube"))
        v.geometry("900x700")
        v.transient(self.app)

        ctk.CTkLabel(v, text=tr("📚 Guion de tutorial"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4))
        ctk.CTkLabel(v, text=tr('{0} pasos · {1} acciones').format((len(pasos)), (len(self.app._sesion_eventos))),
                     font=ctk.CTkFont(size=11), text_color="#888").pack(pady=(0, 10))

        # Construir el guion
        lines = ["# 📚 Tutorial: " + datetime.datetime.now().strftime("%d/%m/%Y"),
                 "",
                 "_Generado automáticamente desde la sesión grabada de G-Prompt Studio_",
                 ""]
        for i, (titulo, eventos) in enumerate(pasos, 1):
            ts_inicio = eventos[0][0] if eventos else ""
            lines.append(f"## Paso {i}: {titulo}")
            lines.append(f"_{ts_inicio}_")
            lines.append("")
            # Narración explicativa según tipo de paso
            narracion = self._sesion_narrar_paso(titulo, eventos)
            if narracion:
                lines.append(narracion)
                lines.append("")
            # Detalle de acciones
            lines.append("**Acciones detalladas:**")
            for ts, evento in eventos:
                lines.append(f"- `{ts}` {evento}")
            lines.append("")

        guion = "\n".join(lines)

        txt = ctk.CTkTextbox(v, wrap="word", font=ctk.CTkFont(size=11))
        txt.pack(fill="both", expand=True, padx=15, pady=5)
        txt.insert("1.0", guion)

        btn_row = ctk.CTkFrame(v, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 12))

        def _exportar_md():
            ruta = filedialog.asksaveasfilename(
                defaultextension=".md",
                filetypes=[("Markdown", "*.md"), (tr("Todos"), "*.*")],
                initialfile=f"tutorial_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.md",
                parent=v)
            if ruta:
                try:
                    with open(ruta, "w", encoding="utf-8") as fp: fp.write(guion)
                    self.app.dialogs.set_estado(tr('📄 Tutorial exportado: {0}').format(ruta), "#2ecc71")
                except Exception as e:
                    self.app.dialogs.set_estado(tr('⚠️ Error: {0}').format(e), "#e74c3c")

        def _copiar():
            try:
                pyperclip.copy(guion)
                self.app.dialogs.set_estado(tr("📋 Guion copiado al portapapeles"), "#2ecc71")
            except Exception as e:
                logger.debug(f"[silent] {e}")

        ctk.CTkButton(btn_row, text=tr("📄 Exportar .md"), width=130,
                      fg_color="#1e5f3a", hover_color="#16492d",
                      command=_exportar_md).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text=tr("📋 Copiar todo"), width=130,
                      fg_color="#1e3a5f", hover_color="#162d49",
                      command=_copiar).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text=tr("Cerrar"), width=110, command=v.destroy,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"]).pack(side="right", padx=2)

    def _sesion_agrupar_pasos(self, eventos):
        """Agrupa eventos consecutivos en pasos lógicos según el tipo de acción.
        Devuelve [(titulo_paso, [eventos]), ...]"""
        pasos = []
        actual_titulo = None
        actual_eventos = []

        # Mapeo: emoji prefijo → categoría de paso
        def categoria(evento):
            e = evento[1] if isinstance(evento, tuple) else evento
            if "🔴 GRABACIÓN" in e or "⏹ GRABACIÓN" in e or "🎥" in e: return None  # ignorar
            if "Cambió modo" in e: return "Configurar modo de trabajo"
            if "Cambió plataforma" in e or "Cambió modelo" in e: return "Seleccionar plataforma y modelo"
            if "Cambió ratio" in e or "Cambió destino" in e or "NSFW" in e or "Brief" in e or "Auto-trad" in e: return "Ajustar parámetros"
            if "Personaje" in e or "LoRA" in e: return "Aplicar personaje/LoRA"
            if "Cargó plantilla" in e: return "Cargar plantilla base"
            if "Cargó imagen" in e: return "Cargar imagen de referencia"
            if "Analizó imagen" in e or "Img→Prompt" in e or "Análisis inverso" in e: return "Analizar imagen"
            if "Pidió ideas" in e or "Sorpréndeme" in e: return "Generar ideas"
            if "Sugerir" in e: return "Pedir sugerencias"
            if "Generó prompt" in e: return "Generar el prompt principal"
            if "Regeneró" in e: return "Regenerar variantes"
            if "Refinó" in e: return "Refinar el prompt"
            if "Variaciones" in e: return "Crear variaciones"
            if "Pulse" in e or "Mood" in e or "Story" in e or "Board" in e or "Walk" in e or "Iterar" in e: return "Exploración creativa"
            if "A/B Testing" in e: return "Probar A/B"
            if "Convirtió prompt" in e: return "Convertir formato"
            if "Comparar" in e: return "Comparar opciones"
            if "Copió" in e or "Ctrl+D" in e: return "Exportar resultado"
            if "Expandió snippet" in e: return "Usar snippet de expansión"
            if "Aplicó setup" in e or "Guardó setup" in e: return "Gestionar setup"
            if "Copiloto" in e: return "Usar Copiloto"
            if "Preview" in e or "Previsualizó" in e: return "Previsualizar"
            if "Reset" in e: return "Reset"
            if "Dashboard" in e: return "Inicio"
            return "Otras acciones"

        for ev in eventos:
            cat = categoria(ev)
            if cat is None: continue  # ignorar inicio/fin de grabación
            if cat != actual_titulo:
                if actual_eventos:
                    pasos.append((actual_titulo, actual_eventos))
                actual_titulo = cat
                actual_eventos = [ev]
            else:
                actual_eventos.append(ev)
        if actual_eventos:
            pasos.append((actual_titulo, actual_eventos))
        return pasos

    def _sesion_narrar_paso(self, titulo, eventos):
        """Genera una narración corta tipo guion para cada tipo de paso."""
        narrativas = {
            "Configurar modo de trabajo": "Empezamos eligiendo el modo de trabajo (imagen, vídeo o audio).",
            "Seleccionar plataforma y modelo": "A continuación seleccionamos la plataforma destino y el modelo que vamos a usar.",
            "Ajustar parámetros": "Ahora ajustamos los parámetros básicos: ratio, destino, NSFW si aplica, etc.",
            "Aplicar personaje/LoRA": "Aplicamos un personaje guardado o un LoRA específico para personalizar el output.",
            "Cargar plantilla base": "Cargamos una plantilla guardada que ya tiene la estructura del prompt.",
            "Cargar imagen de referencia": "Cargamos una imagen de referencia para guiar la generación.",
            "Analizar imagen": "Pedimos a la IA que analice la imagen y nos dé información visual de ella.",
            "Generar ideas": "Pedimos al sistema ideas creativas para arrancar.",
            "Pedir sugerencias": "Pedimos sugerencias automáticas para optimizar el prompt.",
            "Generar el prompt principal": "Aquí es cuando generamos el prompt principal a partir de nuestra idea.",
            "Regenerar variantes": "Si no nos convence, regeneramos manteniendo la idea pero cambiando los detalles.",
            "Refinar el prompt": "Refinamos el prompt para mejorarlo (más detallado, más conciso, etc).",
            "Crear variaciones": "Generamos varias versiones del prompt para tener opciones.",
            "Exploración creativa": "Exploramos creativamente con técnicas avanzadas (Pulse, Mood, Story, etc).",
            "Probar A/B": "Hacemos A/B testing para comparar 4 variantes con dimensiones distintas.",
            "Convertir formato": "Convertimos el prompt entre formatos (imagen → vídeo, etc).",
            "Comparar opciones": "Comparamos resultados de distintos modelos o versiones.",
            "Exportar resultado": "Copiamos el prompt final al portapapeles para usarlo.",
            "Usar snippet de expansión": "Usamos un snippet (`;palabra` + Espacio) para expandir frases comunes.",
            "Gestionar setup": "Guardamos o aplicamos un setup completo para reutilizarlo.",
            "Usar Copiloto": "Abrimos el Copiloto narrativo para conversar con la IA sobre el prompt.",
            "Previsualizar": "Generamos una previsualización rápida para ver el resultado.",
            "Reset": "Limpiamos todo para empezar de cero.",
            "Inicio": "Volvemos a la pantalla de inicio.",
            "Otras acciones": "Realizamos varias acciones sueltas.",
        }
        return narrativas.get(titulo, "")
