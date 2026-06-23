"""Preview de imágenes vía Pollinations.ai — servicio aislado.

Extraído de app.py (sesión 20). Agrupa toda la feature de boceto rápido:
generación con semáforo + retry, grid de previews y la ventana de preview
individual. Es autocontenido: solo lo llama app.py (cmd_previsualizar y
_abrir_comparador), nunca módulos externos.

Acceso desde la app: `self.preview.<metodo>()`.
La identidad/estado de cola (locks, contador) vive en la app:
`app._pollinations_lock`, `app._pollinations_queue_lock`,
`app._pollinations_queue_size`.
"""
import logging
from tkinter import filedialog, messagebox

import customtkinter as ctk
import pyperclip

from config import get_theme_colors
from modules.gprompt_window import GPromptWindow
from modules.i18n import tr
from workers import log_future_exc

logger = logging.getLogger("gprompt")


class PreviewPollinationsService:
    """Boceto rápido vía Pollinations.ai. Recibe la app por composición."""

    def __init__(self, app):
        self.app = app

    def generar(self, prompt_text, on_imagen, on_error,
                parent_widget=None, size=512,
                on_progress=None, force_refresh=False,
                modelo="auto"):
        """Genera preview de imagen vía Pollinations.ai API (sin auth).

        - `prompt_text`: texto del prompt. Se extrae solo POSITIVE y se trunca
          a ~500 chars (la URL no debe ser absurda).
        - `on_imagen(PIL.Image)`: callback al obtener la imagen.
        - `on_error(str)`: callback en caso de fallo.
        - `parent_widget`: si se pasa, los callbacks se programan con .after()
          para ser thread-safe sobre el Tk principal.
        - `size`: ancho/alto de la imagen pedida (default 512).
        - `modelo`: "auto" (default, fallback turbo → none) o nombre concreto
          ("turbo", "kontext", "sdxl", "anime"). En modo concreto solo se
          intenta ese modelo (sin fallback) — útil para A/B testing.

        Caché en `~/.arquitecto_prompts/preview_cache/{md5}.png` para no
        regenerar el mismo prompt entre sesiones. La clave de caché incluye
        el modelo para no mezclar resultados entre toggles.
        """
        import hashlib
        from io import BytesIO
        from pathlib import Path
        from urllib.parse import quote

        import requests
        from PIL import Image as _Image

        # Limpiar prompt: solo POSITIVE, sin etiquetas, máx 500 chars
        try:
            pos = self.app._extraer_pos_de_bloque(prompt_text) or prompt_text
        except Exception:
            pos = prompt_text or ""
        pos = (pos or "").strip()
        if not pos:
            return on_error("Prompt vacío")
        pos = pos[:500]

        # Cache
        cache_dir = Path.home() / ".arquitecto_prompts" / "preview_cache"
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as _e:
            logger.debug(f"[silent] cache dir: {_e}")
        key = hashlib.md5(f"{pos}|{size}|{modelo}".encode()).hexdigest()[:16]
        cache_path = cache_dir / f"{key}.png"

        def _safe_cb(cb, arg):
            if parent_widget is not None:
                try:
                    parent_widget.after(0, lambda: cb(arg))
                    return
                except Exception:
                    pass
            cb(arg)

        if cache_path.exists() and not force_refresh:
            try:
                img = _Image.open(cache_path)
                img.load()
                return _safe_cb(on_imagen, img)
            except Exception as _e:
                logger.debug(f"[silent] cache load: {_e}")
        elif force_refresh and cache_path.exists():
            # Forzar regeneración: borrar caché previa
            try:
                cache_path.unlink()
            except Exception as _e:
                logger.debug(f"[silent] cache delete: {_e}")

        def _worker():
            # Pollinations limita a 1 request concurrente por IP para usuarios
            # anónimos. Cuando se exceden, devuelve HTTP 402 con body JSON
            # tipo:
            #   {"x402Version":1,"error":"Queue full for IP: X: 1 requests
            #    already queued (max: 1)..."}
            # Por eso usamos un SEMÁFORO global para serializar las llamadas
            # (max 1 simultánea) + retry con backoff exponencial al recibir 402.
            # El contador `_pollinations_queue_size` permite mostrar
            # "⏳ En cola (N por delante)" en la UI.
            #
            # Sesión 18 round 5: si el usuario tiene API key de Pollinations
            # guardada (keyring o keys.json), se usa el endpoint NUEVO
            # `gen.pollinations.ai/image/{prompt}` con `Authorization: Bearer`
            # → sin rate limit (tier server-to-server). Si NO hay key, se
            # cae al endpoint legacy `image.pollinations.ai` con retry.
            # El endpoint legacy NO acepta auth (la ignora silenciosamente),
            # por eso decidimos en runtime cuál URL usar.
            try:
                from api_clients import cargar_api_key
                pollinations_key = cargar_api_key("pollinations") or ""
            except Exception:
                pollinations_key = ""
            req_headers = {}
            if pollinations_key:
                req_headers["Authorization"] = f"Bearer {pollinations_key}"
                base_url = "https://gen.pollinations.ai/image/"
            else:
                base_url = "https://image.pollinations.ai/prompt/"

            # Si el usuario pidió un modelo concreto, solo ese.
            # En "auto" (default), elegir modelos según endpoint:
            #   - Sin key (legacy): turbo + sin param (comportamiento histórico)
            #   - Con key (gen.pollinations.ai): flux (free ∞) como default,
            #     fallback al endpoint sin model (por si flux falla, raro).
            if modelo and modelo != "auto":
                modelos_a_probar = [modelo]
            elif pollinations_key:
                modelos_a_probar = ["flux", None]
            else:
                modelos_a_probar = ["turbo", None]
            last_err = None

            # Registrarse en la cola y notificar posición inicial
            with self.app._pollinations_queue_lock:
                self.app._pollinations_queue_size += 1
                position = self.app._pollinations_queue_size
            decremented = False

            try:
                # Notificar posición inicial en la UI
                if on_progress and position > 1:
                    _safe_cb(on_progress, f"⏳ En cola ({position - 1} por delante)")
                elif on_progress:
                    _safe_cb(on_progress, "🎨 Generando...")

                with self.app._pollinations_lock:  # serializa entre threads
                    # Ya tengo el lock → dejo de estar en cola
                    with self.app._pollinations_queue_lock:
                        self.app._pollinations_queue_size -= 1
                        decremented = True
                    if on_progress and position > 1:
                        # Antes mostraba "En cola N", actualizo a "Generando..."
                        _safe_cb(on_progress, "🎨 Generando...")

                    # 4 intentos x 2 modelos = 8 requests. Backoffs entre
                    # rondas: 3s, 10s, 30s (total 43s wait). Cubre el rate
                    # limit por minuto que Pollinations aplica a IPs anónimas.
                    BACKOFFS = [3, 10, 30]
                    queue_full_hits = 0  # cuenta veces que Pollinations dijo
                                          # "queue full" → si son la mayoría,
                                          # mensaje final es claro.
                    for intento in range(4):
                        for mdl_actual in modelos_a_probar:
                            try:
                                extra = f"&model={mdl_actual}" if mdl_actual else ""
                                url = (
                                    f"{base_url}{quote(pos)}"
                                    f"?width={size}&height={size}&nologo=true&enhance=false"
                                    f"&referrer=gprompt-studio{extra}"
                                )
                                resp = requests.get(url, timeout=60, headers=req_headers)
                                sc = resp.status_code
                                if sc == 402:
                                    body_lower = (resp.text or "")[:300].lower()
                                    if "queue full" in body_lower or "queued" in body_lower:
                                        queue_full_hits += 1
                                        last_err = "Cola Pollinations llena, reintentando..."
                                    elif (
                                        "insufficient balance" in body_lower
                                        or "payment_required" in body_lower
                                    ) and pollinations_key:
                                        # Sesión 18 round 5: la key del usuario
                                        # no tiene Pollen para este modelo.
                                        # Caer automáticamente al endpoint
                                        # legacy anónimo (más lento pero
                                        # gratis) en el siguiente intento.
                                        # Avisa al usuario por la UI.
                                        if on_progress:
                                            _safe_cb(
                                                on_progress,
                                                "💸 Sin Pollen — usando endpoint anónimo (más lento)",
                                            )
                                        base_url = "https://image.pollinations.ai/prompt/"
                                        req_headers = {}
                                        # Cambiar también el modelo a uno
                                        # que el legacy SÍ acepta (turbo).
                                        # flux/kontext/etc. no existen ahí.
                                        if mdl_actual not in ("turbo", None,
                                                              "kontext", "sdxl",
                                                              "anime"):
                                            mdl_actual = "turbo"
                                        last_err = "Sin Pollen — fallback a legacy"
                                    else:
                                        last_err = "Pollinations: cuenta de pago requerida"
                                    continue
                                if sc == 429:
                                    last_err = "Rate limit, reintentando..."
                                    continue
                                if sc >= 500:
                                    last_err = f"{sc} Pollinations caído"
                                    continue
                                if sc != 200:
                                    last_err = f"HTTP {sc}"
                                    continue
                                ct = resp.headers.get("Content-Type", "").lower()
                                if not ct.startswith("image/"):
                                    last_err = f"Respuesta no es imagen ({ct})"
                                    continue
                                img = _Image.open(BytesIO(resp.content))
                                img.load()
                                try:
                                    img.save(cache_path)
                                except Exception as _e:
                                    logger.debug(f"[silent] cache save: {_e}")
                                _safe_cb(on_imagen, img)
                                return
                            except requests.Timeout:
                                last_err = "Timeout (>60s)"
                                continue
                            except requests.RequestException as e:
                                last_err = f"Red: {e}"
                                continue
                            except Exception as e:
                                last_err = str(e)
                                continue
                        # Los 2 modelos fallaron este intento. Backoff entre
                        # rondas: 3s, 10s, 30s.
                        if intento < len(BACKOFFS):
                            import time as _time
                            wait_s = BACKOFFS[intento]
                            if on_progress:
                                _safe_cb(on_progress,
                                         f"⏳ Sobrecarga, esperando {wait_s}s...")
                            _time.sleep(wait_s)
                # Si salimos del with sin return → todos los intentos fallaron.
                # Si la mayoría fueron "queue full", mensaje específico claro.
                if queue_full_hits >= 4:
                    last_err = ("Pollinations sobrecargado. Espera 1-2 min "
                                "y pulsa ♻ para reintentar.")
                _safe_cb(on_error, last_err or "Pollinations no devolvió imagen")
            finally:
                # Defensa: si el counter no se decrementó (excepción antes
                # de tomar el lock), hacerlo aquí para no dejar la cuenta sesgada.
                if not decremented:
                    with self.app._pollinations_queue_lock:
                        self.app._pollinations_queue_size -= 1

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def abrir_grid(self, variaciones, labels=None):
        """Ventana con grid 3-col de previews Pollinations de todas las variantes.

        Genera las N previews EN PARALELO (un thread por variante).
        Click en una imagen → la abre a tamaño completo en ventana nueva.
        """
        import webbrowser
        from urllib.parse import quote

        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self.app)
        vent.title(tr("👁 Grid Pollinations"))
        n = len(variaciones)
        screen_w = self.app.winfo_screenwidth()
        screen_h = self.app.winfo_screenheight()
        thumb_size = 256
        cols = min(3, n)
        ancho = min(thumb_size * cols + 80, screen_w - 100)
        alto = min(800, screen_h - 100)
        vent.geometry(f"{ancho}x{alto}")
        vent.transient(self.app)

        ctk.CTkLabel(vent,
                     text=f"👁 Grid Pollinations ({n} previews)  ·  click en una imagen para verla en grande",
                     font=ctk.CTkFont(size=12, weight="bold")
                     ).pack(pady=(8, 4))

        # Toggle de modelo Pollinations. Lista dinámica según endpoint:
        # - SIN key (legacy image.pollinations.ai): turbo / kontext / sdxl / anime
        # - CON key (gen.pollinations.ai): flux (free ∞) / kontext / gptimage /
        #   zimage / klein / nova-canvas. Solo flux es gratis; los demás
        #   consumen Pollen del balance de la key.
        # "auto" = fallback chain inteligente (flux con key, turbo sin).
        # Las regeneraciones (♻) y "open large" usan el modelo seleccionado.
        # Las previews ya generadas NO se auto-regeneran al cambiar el toggle.
        try:
            from api_clients import cargar_api_key as _cargar
            _has_pol_key = bool(_cargar("pollinations"))
        except Exception:
            _has_pol_key = False
        if _has_pol_key:
            _modelos_disponibles = [
                "auto", "flux", "kontext", "gptimage",
                "zimage", "klein", "nova-canvas",
            ]
            _hint_modo = "🔑 con API key · flux es gratis"
        else:
            _modelos_disponibles = ["auto", "turbo", "kontext", "sdxl", "anime"]
            _hint_modo = "anónimo · con rate limit"
        modelo_pollinations_var = ctk.StringVar(value="auto")
        bar_modelo = ctk.CTkFrame(vent, fg_color="transparent")
        bar_modelo.pack(pady=(0, 4))
        ctk.CTkLabel(bar_modelo, text=tr("Modelo:"),
                     font=ctk.CTkFont(size=10)
                     ).pack(side="left", padx=(0, 4))
        combo_modelo_pol = ctk.CTkComboBox(
            bar_modelo,
            values=_modelos_disponibles,
            variable=modelo_pollinations_var,
            width=130, height=24,
            font=ctk.CTkFont(size=10),
            dropdown_font=ctk.CTkFont(size=10),
            state="readonly",
        )
        combo_modelo_pol.pack(side="left")
        ctk.CTkLabel(bar_modelo,
                     text=f"({_hint_modo})",
                     font=ctk.CTkFont(size=9), text_color="#666"
                     ).pack(side="left", padx=(6, 0))

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="both", expand=True)

        for i, var in enumerate(variaciones):
            row, col_i = divmod(i, cols)
            cell = ctk.CTkFrame(grid, fg_color=c["fg_frame"], corner_radius=8,
                                 width=thumb_size + 10, height=thumb_size + 60)
            cell.grid(row=row, column=col_i, padx=4, pady=4, sticky="nsew")
            cell.grid_propagate(False)

            label_txt = (
                labels[i] if labels and i < len(labels) and labels[i]
                else f"Variación #{i+1}"
            )
            ctk.CTkLabel(cell, text=label_txt,
                         font=ctk.CTkFont(size=10, weight="bold"),
                         wraplength=thumb_size - 10
                         ).pack(pady=(4, 2))

            img_lbl = ctk.CTkLabel(cell, text=tr("⏳ Preparando..."),
                                    width=thumb_size, height=thumb_size,
                                    fg_color="#0a0e14", text_color="#888",
                                    wraplength=thumb_size - 20)
            img_lbl.pack(pady=2)

            # Botón ♻ Regenerar (SIEMPRE visible — sesión 18 round 5).
            # Antes solo aparecía al fallar; ahora también permite cambiar
            # de modelo (con el toggle del header) sin esperar a un error.
            btn_row_cell = ctk.CTkFrame(cell, fg_color="transparent")
            btn_row_cell.pack(pady=(2, 4))  # siempre visible
            btn_regen = ctk.CTkButton(btn_row_cell, text=tr("♻ Regenerar"),
                                       width=120, height=22,
                                       fg_color="#7c3aed", hover_color="#5b21b6",
                                       font=ctk.CTkFont(size=10, weight="bold"))
            btn_regen.pack()

            def _on_img(image, lbl=img_lbl, prompt_text=var, btn_frame=btn_row_cell):
                try:
                    from PIL import Image as _Image
                    thumb = image.copy()
                    thumb.thumbnail((thumb_size, thumb_size), _Image.Resampling.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=thumb, dark_image=thumb,
                                            size=(thumb.width, thumb.height))
                    lbl.configure(image=ctk_img, text="")
                    lbl.image = ctk_img
                    # Click → abrir en navegador con tamaño 1024 usando el
                    # modelo seleccionado en el toggle.
                    # "auto" → flux (con key) o turbo (sin key).
                    # Cuando hay key: gen.pollinations.ai requiere auth.
                    # El navegador NO envía el header Bearer automáticamente,
                    # así que pasamos la key como `?key=` query param
                    # (formato documentado por su error 401: "Please provide
                    # an API key via Authorization header (Bearer token) or
                    # ?key= query parameter"). Trade-off: la key queda en el
                    # historial del navegador del usuario — aceptable porque
                    # es su propio escritorio.
                    def _open_large(_e=None, p=prompt_text):
                        try:
                            pos = self.app._extraer_pos_de_bloque(p) or p
                            m = modelo_pollinations_var.get()
                            if m == "auto":
                                modelo_url = "flux" if _has_pol_key else "turbo"
                            else:
                                modelo_url = m
                            if _has_pol_key:
                                try:
                                    from api_clients import (
                                        cargar_api_key as _ck,
                                    )
                                    _k = _ck("pollinations") or ""
                                except Exception:
                                    _k = ""
                                base = "https://gen.pollinations.ai/image/"
                                auth_qs = f"&key={quote(_k)}" if _k else ""
                            else:
                                base = "https://image.pollinations.ai/prompt/"
                                auth_qs = ""
                            url = (
                                f"{base}{quote((pos or '')[:500])}"
                                f"?width=1024&height=1024&model={modelo_url}&nologo=true"
                                f"&referrer=gprompt-studio{auth_qs}"
                            )
                            webbrowser.open(url)
                        except Exception as _e:
                            logger.debug(f"[silent] open large: {_e}")
                    lbl.bind("<Button-1>", _open_large)
                    # Si la generación fue OK, mantener el botón regenerar
                    # visible (ahora siempre, no solo al fallar). Sesión 18
                    # round 5: usuario pidió poder cambiar modelo + ♻ sin
                    # tener que esperar a un fallo.
                except Exception as _e:
                    logger.debug(f"[silent] grid thumb: {_e}")
                    lbl.configure(text=f"❌ {_e}", text_color="#e74c3c")

            def _on_err(msg, lbl=img_lbl, btn_frame=btn_row_cell):
                lbl.configure(text=f"❌ {msg}", text_color="#e74c3c",
                              wraplength=thumb_size - 20)
                # Botón ♻ ya está siempre visible (round 5).

            def _on_progress(msg, lbl=img_lbl, btn_frame=btn_row_cell):
                lbl.configure(text=msg, text_color="#888",
                              wraplength=thumb_size - 20)
                # Botón ♻ se mantiene visible durante la generación —
                # útil si el usuario cambia de modelo y quiere ♻ ya.

            def _regenerar(prompt_text=var, _img=_on_img, _err=_on_err,
                            _prog=_on_progress, lbl=img_lbl, btn_frame=btn_row_cell):
                lbl.configure(text=tr("⏳ Preparando..."), text_color="#888")
                try: btn_frame.pack_forget()
                except Exception: pass
                self.generar(
                    prompt_text, _img, _err, vent, size=512,
                    on_progress=_prog, force_refresh=True,
                    modelo=modelo_pollinations_var.get(),
                )

            btn_regen.configure(command=_regenerar)

            self.generar(var, _on_img, _on_err, vent,
                         size=512,
                         on_progress=_on_progress)

        for ci in range(cols):
            grid.columnconfigure(ci, weight=1)

        # Pie
        pie = ctk.CTkFrame(vent, fg_color="transparent")
        pie.pack(pady=(0, 10))
        ctk.CTkLabel(pie,
                     text=tr("Cache en ~/.arquitecto_prompts/preview_cache/"),
                     font=ctk.CTkFont(size=9), text_color="#666"
                     ).pack(side="left", padx=8)
        ctk.CTkButton(pie, text=tr("Cerrar"), width=120, height=30,
                      fg_color="#6b7280", hover_color="#4b5563",
                      font=ctk.CTkFont(size=10, weight="bold"),
                      command=vent.destroy).pack(side="left", padx=4)

    def mostrar_window(self, image_pil, img_ctk, url_imagen, desde_cache=False):
        """Ventana de preview con imagen + URL + botones Guardar/Copiar/Abrir."""
        import webbrowser
        vent_previa = GPromptWindow(self.app)
        vent_previa.title(tr("🖼 Preview") + (tr(" (caché)") if desde_cache else ""))
        vent_previa.geometry("560x680")
        vent_previa.transient(self.app)

        lbl_img = ctk.CTkLabel(vent_previa, text="", image=img_ctk)
        lbl_img.pack(pady=(15, 6))

        if desde_cache:
            ctk.CTkLabel(vent_previa, text=tr("📥 Servido desde caché — instantáneo, sin llamada a la API"),
                         font=ctk.CTkFont(size=10, slant="italic"),
                         text_color="#2ecc71").pack(pady=(0, 4))

        # URL Pollinations (truncada para no romper layout)
        url_corta = url_imagen if len(url_imagen) <= 80 else url_imagen[:77] + "..."
        ctk.CTkLabel(vent_previa,
                     text=f"🔗 URL: {url_corta}",
                     font=ctk.CTkFont(family="Consolas", size=9),
                     text_color="#888",
                     wraplength=520, justify="left"
                     ).pack(pady=(2, 8), padx=15)

        btn_row = ctk.CTkFrame(vent_previa, fg_color="transparent")
        btn_row.pack(pady=5)
        ctk.CTkButton(btn_row, text=tr("💾 Guardar boceto"), width=140, height=30,
                      fg_color="#2ecc71", hover_color="#27ae60",
                      command=lambda: self.guardar_boceto(image_pil)
                      ).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=tr("🔗 Copiar URL"), width=120, height=30,
                      fg_color="#3498db", hover_color="#2876b8",
                      command=lambda: (pyperclip.copy(url_imagen),
                                       self.app.dialogs.set_estado(tr("📋 URL copiada"), "#2ecc71"))
                      ).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=tr("🌐 Abrir en navegador"), width=160, height=30,
                      fg_color="#7c3aed", hover_color="#5d2ab5",
                      command=lambda: webbrowser.open(url_imagen)
                      ).pack(side="left", padx=4)

    def guardar_boceto(self, image_pil):
        ruta = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPEG files", "*.jpg"), ("PNG files", "*.png")], title="Guardar boceto")
        if ruta:
            try:
                if image_pil.mode in ("RGBA", "P"): image_pil = image_pil.convert("RGB")
                image_pil.save(ruta)
                self.app.dialogs.set_estado(tr('✅ Boceto guardado en: {0}').format(ruta), "#2ecc71")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la imagen:\n{e}")
