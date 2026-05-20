"""Data Management Mixin - History, Favorites, Stars, Snippets, Formulas, Templates, etc."""
import os
import re
import json
import datetime
import logging
import random
import pyperclip

logger = logging.getLogger(__name__)
import customtkinter as ctk
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.simpledialog as simpledialog
from PIL import Image
from pathlib import Path
from config import PUBLIC_VERSION, PRESET_COLORES, BIBLIOTECA_EJEMPLOS, DESTINOS, get_theme_colors
try:
    from CTkToolTip import CTkToolTip
except ImportError:
    class CTkToolTip:
        def __init__(self, *args, **kwargs): pass
from typing import TYPE_CHECKING
from modules.gprompt_window import GPromptWindow

if TYPE_CHECKING:
    from app import ArquitectoApp

class DataMgmtMixin:
    """Mixin containing all data management methods."""

    SNIPPETS_DEFAULT = {
        "realism": "photorealistic, realistic, 8k, detailed, high quality",
        "cinema": "cinematic lighting, dramatic, volumetric, film grain",
        "photo": "professional photography, studio lighting, sharp focus, dslr",
        "anime": "anime style, cel shading, manga, vibrant colors",
        "art": "digital art, concept art, illustration, highly detailed",
        "portrait": "portrait, detailed eyes, realistic skin, depth of field",
        "landscape": "landscape, wide angle, atmospheric, epic, nature",
        "cyber": "cyberpunk, neon lights, rgb, city nightscape, futuristic",
        "fantasy": "fantasy, magical, epic, mythical, enchanted",
        "vintage": "vintage, film grain, analog, retro, nostalgic",
        "emergent": "{animal} powerfully breaking through a dark matte surface barrier, head is a hybrid of animal texture seamlessly integrated with geometric crystal fragments, polished chrome plates and iridized glass, intricate internal patterns, eyes intensely glowing with electric bioluminescent energy, jagged violent break with debris flying, pulsating bioluminescent filaments (electric blue, gold, purple) revealed within fracture, scattered geometric crystal and metal shards floating, dramatic directional spotlight from top combined with powerful internal light, dark infinite matte void, high-resolution photorealistic 3D conceptual art render, 8k, masterpiece",
    }

    def _auto_guardar_borrador(self):
        """Guarda el borrador actual cada 30 segundos."""
        try:
            idea = self.txt_idea.get("1.0", "end").strip()
            salida = self.txt_salida.get("1.0", "end").strip()
            if idea or salida:
                prefs = self.store.cargar_preferencias()
                prefs["borrador"] = {
                    "idea": idea,
                    "salida": salida,
                    "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "modo": self.modo_var.get(),
                }
                self.store.guardar_preferencias(prefs)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # Reagendar
        try:
            self.after(30000, self._auto_guardar_borrador)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    def _restaurar_borrador(self):
        """Si hay un borrador guardado, ofrece restaurarlo al abrir la app."""
        try:
            prefs = self.store.cargar_preferencias()
            borrador = prefs.get("borrador")
            if not borrador: return
            idea = borrador.get("idea", "")
            salida = borrador.get("salida", "")
            if not (idea or salida): return

            from tkinter import messagebox
            fecha = borrador.get("fecha", "")
            preview = (idea or salida)[:100]
            if messagebox.askyesno("📝 Borrador encontrado",
                                      f"Hay un borrador no guardado de la sesión anterior ({fecha}):\n\n"
                                      f"\"{preview}{'...' if len(preview) >= 100 else ''}\"\n\n"
                                      f"¿Quieres restaurarlo?",
                                      parent=self):
                if idea:
                    self.txt_idea.delete("1.0", "end")
                    self.txt_idea.insert("1.0", idea)
                if salida:
                    self.actualizar_salida(salida)
                if borrador.get("modo"):
                    self.modo_var.set(borrador["modo"])
                    self._on_modo_cambio()
                self.set_estado("📝 Borrador restaurado", "#2ecc71")
            else:
                # Limpiar borrador descartado
                prefs["borrador"] = None
                self.store.guardar_preferencias(prefs)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    def _cmd_guardar_plantilla(self):
        nombre = simpledialog.askstring("Guardar Plantilla", "Nombre para la plantilla:", parent=self)
        if not nombre or not nombre.strip(): return
        nombre = nombre.strip()
        neg_extra = self.txt_negative.get("1.0", "end").strip() if hasattr(self, 'txt_negative') else ""
        plantilla = {
            "nombre":      nombre,
            "modo":        self.modo_var.get(),
            "modelo_img":  self.combo_modelo_imagen.get() if hasattr(self, 'combo_modelo_imagen') else "",
            "modelo_vid":  self.combo_modelo_video.get() if hasattr(self, 'combo_modelo_video') else "",
            "modelo_aud":  self.combo_modelo_audio.get() if hasattr(self, 'combo_modelo_audio') else "",
            "ratio":       self.ratio_var.get(),
            "estilos":     self.estilos_seleccionados(),
            "nsfw":        self.switch_nsfw_var.get(),
            "neg_extra":   neg_extra,
            "neg_presets": [n for n, v in self.preset_vars.items() if v.get()],
            "lora":        self.combo_lora.get(),
            "personaje":   self.combo_personaje.get(),
            "duracion":    self.duracion_var.get(),
            "traduccion":  self.switch_traduccion_var.get(),
            "plataforma":  self.plataforma_var.get(),
            "destino":     self.destino_var.get(),
            "brief":       self.brief_var.get(),
            "instrumental": self.switch_instrumental_var.get() if hasattr(self, 'switch_instrumental_var') else False,
        }
        self.store.guardar_plantilla(plantilla)
        self.actualizar_combo_plantillas()
        self.set_estado(f"📐 Plantilla '{nombre}' guardada.", "#9b59b6")

    def _cmd_borrar_plantilla(self):
        nombre = self.combo_plantilla.get()
        if not nombre or nombre == "— Sin plantilla —": return
        if messagebox.askyesno("Confirmar", f"¿Borrar la plantilla '{nombre}'?"):
            self.store.borrar_plantilla(nombre)
            self.combo_plantilla.set("— Sin plantilla —")
            self.actualizar_combo_plantillas()
            self.set_estado(f"🗑 Plantilla '{nombre}' eliminada.")

    def _cargar_plantilla(self, nombre):
        if not nombre or nombre == "— Sin plantilla —": return
        p = self.store.obtener_plantilla(nombre)
        if not p: return
        try: self._sesion_log(f"📐 Cargó plantilla: {nombre}")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        modo = p.get("modo", "imagen")
        if modo != self.modo_var.get():
            self.modo_var.set(modo)
            self._on_modo_cambio()
        if modo == "video":
            if hasattr(self, 'combo_modelo_video'): self.combo_modelo_video.set(p.get("modelo_vid", "Kling 3.0"))
        elif modo == "audio":
            if hasattr(self, 'combo_modelo_audio'): self.combo_modelo_audio.set(p.get("modelo_aud", "Suno v5"))
        else:
            if hasattr(self, 'combo_modelo_imagen'): self.combo_modelo_imagen.set(p.get("modelo_img", "Z Image Turbo"))
        self.ratio_var.set(p.get("ratio", "1:1"))
        for n, v in self.estilo_checks.items():
            v.set(n in p.get("estilos", []))
        self.switch_nsfw_var.set(p.get("nsfw", False))
        if hasattr(self, 'txt_negative'):
            self.txt_negative.delete("1.0", "end")
            neg = p.get("neg_extra", "")
            if neg: self.txt_negative.insert("1.0", neg)
        for pn, pv in self.preset_vars.items():
            activo = pn in p.get("neg_presets", [])
            pv.set(activo)
            if pn in self.preset_btns:
                fg = PRESET_COLORES.get(pn, ("#333", "#555"))[0]
                self.preset_btns[pn].configure(fg_color="#2ecc71" if activo else fg, text=f"✓ {pn}" if activo else pn)
        self.combo_personaje.set(p.get("personaje", "— Sin personaje —"))
        self.combo_lora.set(p.get("lora", "— Sin LoRA —"))
        self.duracion_var.set(p.get("duracion", "10s"))
        self.switch_traduccion_var.set(p.get("traduccion", True))
        dest = p.get("destino", "— Personal —")
        if dest in DESTINOS: self.destino_var.set(dest)
        self.brief_var.set(p.get("brief", False))
        self._on_brief_cambio()
        if hasattr(self, 'switch_instrumental_var'):
            self.switch_instrumental_var.set(p.get("instrumental", False))
        plat = p.get("plataforma", "SeaArt / Tensor.Art")
        self.plataforma_var.set(plat)
        self._on_plataforma_cambio()
        self.reiniciar_memoria()
        self.set_estado(f"📐 Plantilla '{nombre}' cargada.", "#9b59b6")

    def _cargar_imagen(self):
        ruta = filedialog.askopenfilename(filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp *.bmp")])
        if ruta:
            self._cargar_imagen_desde_pil(Image.open(ruta).convert("RGB"), Path(ruta).name)

    def _cargar_imagen_desde_pil(self, img, nombre="imagen"):
        if max(img.size) > 1024:
            gem = img.copy()
            gem.thumbnail((1024, 1024), Image.LANCZOS)
        else:
            gem = img.copy()
        self.imagen_cargada = gem
        thumb = img.copy()
        thumb.thumbnail((34, 34), Image.LANCZOS)
        ctk_thumb = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=(34, 34))
        self.lbl_img_preview.configure(image=ctk_thumb, text="")
        self.lbl_img_preview._ctk_image = ctk_thumb
        self.lbl_img_nombre.configure(text=f"{nombre[:20]}  ({gem.width}×{gem.height})", text_color="#2ecc71")
        self.btn_cargar_img.configure(text="✅ OK", fg_color="#1a7a3c")
        self.set_estado(f"✅ Imagen: {nombre}", "#2ecc71")
        self._sesion_log(f"📂 Cargó imagen: {nombre} ({gem.width}×{gem.height})")

        # Guardar en historial de imágenes
        self._agregar_img_historial(gem, nombre)

    def _limpiar_imagen(self):
        self.imagen_cargada = None
        self._ultimo_anclaje_visual = None
        self.lbl_img_preview.configure(image=ctk.CTkImage(light_image=Image.new("RGB", (1, 1)), dark_image=Image.new("RGB", (1, 1)), size=(1, 1)), text="")
        self.lbl_img_nombre.configure(text="Sin imagen", text_color="#666666")
        self.btn_cargar_img.configure(text="📂 Cargar", fg_color=["#3B8ED0", "#1F6AA5"])
        self.set_estado("Imagen eliminada.")

    def _agregar_img_historial(self, pil_img, nombre):
        """Añade una imagen al historial visual de recientes."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        # Evitar duplicados por nombre
        for h in self._img_history:
            if h[2] == nombre:
                return

        # Crear thumbnail para el historial
        mini = pil_img.copy()
        mini.thumbnail((30, 30), Image.LANCZOS)
        ctk_mini = ctk.CTkImage(light_image=mini, dark_image=mini, size=(30, 30))

        # Crear botón clickeable
        btn = ctk.CTkButton(self._img_history_frame, image=ctk_mini, text="", width=32, height=32,
                            fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"], corner_radius=4,
                            command=lambda im=pil_img, nm=nombre: self._cargar_imagen_desde_pil(im, nm))
        btn.pack(side="left", padx=1)
        btn._ctk_image = ctk_mini
        CTkToolTip(btn, delay=0.3, message=nombre[:25])

        self._img_history.append((pil_img, ctk_mini, nombre))

        # Limitar historial
        while len(self._img_history) > self._MAX_IMG_HISTORY:
            _, _, _ = self._img_history.pop(0)
            widgets = self._img_history_frame.winfo_children()
            if widgets:
                widgets[0].destroy()

    def _snippets_obtener(self):
        """Devuelve los snippets actuales (predefinidos + custom del usuario)."""
        prefs = self.store.cargar_preferencias()
        custom = prefs.get("snippets_expand", {}) or {}
        # Mergear: custom sobrescribe a default si tienen el mismo trigger
        result = dict(self.SNIPPETS_DEFAULT)
        if isinstance(custom, dict):
            result.update(custom)
        return result

    def _snippets_guardar_custom(self, snippets_custom):
        """Guarda solo los snippets custom (no los default)."""
        prefs = self.store.cargar_preferencias()
        prefs["snippets_expand"] = snippets_custom
        self.store.guardar_preferencias(prefs)

    def _snippet_expand(self):
        """Si justo antes del cursor hay ';palabra ', expande la palabra al snippet completo."""
        try:
            # Posición actual del cursor
            cursor = self.txt_idea.index("insert")
            # Tomar texto desde inicio hasta el cursor
            texto_antes = self.txt_idea.get("1.0", cursor)
            # Buscar último ; en el texto (sin espacios entre el ; y la palabra)
            # Patrón: \s;palabra<espacio> (donde espacio es lo que se acaba de teclear)
            import re as _re
            match = _re.search(r'(?:^|\s)(;)([a-zA-Z0-9_]+)(\s)$', texto_antes)
            if not match:
                return
            trigger_pos = match.start(1)  # posición del ;
            palabra = match.group(2).lower()
            snippets = self._snippets_obtener()
            if palabra not in snippets:
                return  # no es un snippet conocido
            expansion = snippets[palabra]
            # Calcular índices de tkinter para reemplazar ;palabra (incluye el ;) por la expansión
            # texto_antes va de "1.0" a cursor; el match dentro de texto_antes
            # convertir offset de string a índice tkinter
            inicio = self.txt_idea.index(f"1.0+{trigger_pos}c")
            fin = self.txt_idea.index(f"1.0+{match.end(2)}c")  # final de palabra (no incluye espacio)
            self.txt_idea.delete(inicio, fin)
            self.txt_idea.insert(inicio, expansion)
            self.set_estado(f"✨ Snippet expandido: ;{palabra}", "#2ecc71")
            try: self._sesion_log(f"✨ Expandió snippet: ;{palabra}")
            except Exception as e:
                logger.debug(f"[silent] {e}")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    def _cmd_gestionar_snippets(self):
        """Ventana de gestión de snippets: ver predefinidos + añadir/editar/borrar custom."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        v = GPromptWindow(self)
        v.title("⚡ Expansión rápida")
        v.geometry("680x620")
        v.transient(self)

        ctk.CTkLabel(v, text="⚡ Snippets de expansión rápida",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4))
        ctk.CTkLabel(v, text="Escribe ';palabra' + Espacio en la idea y se expande automáticamente.",
                     font=ctk.CTkFont(size=10), text_color="#888").pack(pady=(0, 4))
        ctk.CTkLabel(v, text="Los custom sobrescriben a los default si comparten trigger.",
                     font=ctk.CTkFont(size=9, slant="italic"), text_color="#666").pack(pady=(0, 10))

        # Form añadir/editar
        form = ctk.CTkFrame(v, fg_color=c["fg_dark"])
        form.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(form, text="Trigger (sin ;):",
                     font=ctk.CTkFont(size=10)).pack(side="left", padx=(10, 4), pady=8)
        ent_trigger = ctk.CTkEntry(form, width=110, placeholder_text="ej: cine")
        ent_trigger.pack(side="left", padx=4)
        ctk.CTkLabel(form, text="Expansión:",
                     font=ctk.CTkFont(size=10)).pack(side="left", padx=(10, 4))
        ent_expansion = ctk.CTkEntry(form, width=320, placeholder_text="ej: cinematic lighting, film grain")
        ent_expansion.pack(side="left", padx=4)

        def _add():
            t = ent_trigger.get().strip().lower().lstrip(";")
            e = ent_expansion.get().strip()
            if not t or not e:
                self.set_estado("⚠️ Trigger y expansión son obligatorios", "#e67e22")
                return
            if not t.replace("_", "").isalnum():
                self.set_estado("⚠️ Trigger solo puede tener letras/números", "#e67e22")
                return
            prefs = self.store.cargar_preferencias()
            custom = prefs.get("snippets_expand", {}) or {}
            if not isinstance(custom, dict): custom = {}
            custom[t] = e
            self._snippets_guardar_custom(custom)
            ent_trigger.delete(0, "end"); ent_expansion.delete(0, "end")
            refrescar()

        ctk.CTkButton(form, text="➕", width=40, height=28, fg_color="#1a7a3c",
                      command=_add).pack(side="left", padx=8, pady=8)

        scroll = ctk.CTkScrollableFrame(v, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=8)

        def refrescar():
            for w in scroll.winfo_children(): w.destroy()
            prefs = self.store.cargar_preferencias()
            custom = prefs.get("snippets_expand", {}) or {}
            if not isinstance(custom, dict): custom = {}
            todos = self._snippets_obtener()
            # Separar custom de default
            custom_keys = set(custom.keys())

            # Sección custom
            if custom:
                ctk.CTkLabel(scroll, text=f"📝 Tus snippets ({len(custom)})",
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color="#2ecc71").pack(anchor="w", pady=(4, 4))
                for trigger in sorted(custom_keys):
                    expansion = custom[trigger]
                    es_override = trigger in self.SNIPPETS_DEFAULT
                    _row_snippet(trigger, expansion, custom=True, override=es_override)

            # Sección defaults (los que NO han sido sobrescritos)
            ctk.CTkLabel(scroll, text=f"📦 Predefinidos ({len(self.SNIPPETS_DEFAULT) - len(custom_keys & set(self.SNIPPETS_DEFAULT.keys()))})",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=c["hdr_text"]).pack(anchor="w", pady=(12, 4))
            for trigger in sorted(self.SNIPPETS_DEFAULT.keys()):
                if trigger in custom_keys: continue  # ya se mostró arriba
                expansion = self.SNIPPETS_DEFAULT[trigger]
                _row_snippet(trigger, expansion, custom=False, override=False)

        def _row_snippet(trigger, expansion, custom=False, override=False):
            row = ctk.CTkFrame(scroll, fg_color=c["fg_dark"] if custom else c["fg_frame"], corner_radius=6)
            row.pack(fill="x", pady=2)
            badge = "  ⚡" if override else ""
            ctk.CTkLabel(row, text=f"  ;{trigger}{badge}",
                         font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                         text_color=c["hdr_text"], width=120, anchor="w").pack(side="left", padx=8, pady=6)
            preview = expansion[:60] + ("…" if len(expansion) > 60 else "")
            ctk.CTkLabel(row, text=preview, font=ctk.CTkFont(size=10),
                         text_color=c["muted_text"], anchor="w").pack(side="left", fill="x", expand=True)

            # Botón Copiar — disponible en TODOS los snippets (custom y predefinidos)
            def _copiar(e=expansion, t=trigger):
                pyperclip.copy(e)
                self.set_estado(f"📋 Snippet ;{t} copiado al portapapeles", "#2ecc71")
            ctk.CTkButton(row, text="📋", width=30, height=24, fg_color=c["fg_frame"],
                          hover_color=c["fg_dark_hover"], command=_copiar).pack(side="right", padx=2, pady=4)

            if custom:
                def _editar(t=trigger, e=expansion):
                    ent_trigger.delete(0, "end"); ent_trigger.insert(0, t)
                    ent_expansion.delete(0, "end"); ent_expansion.insert(0, e)
                def _borrar(t=trigger):
                    if not messagebox.askyesno("Borrar", f"¿Borrar snippet ;{t}?", parent=v): return
                    prefs = self.store.cargar_preferencias()
                    cust = prefs.get("snippets_expand", {}) or {}
                    cust.pop(t, None)
                    self._snippets_guardar_custom(cust)
                    refrescar()
                ctk.CTkButton(row, text="✏️", width=30, height=24, fg_color="#1a4a5a",
                              command=_editar).pack(side="right", padx=2, pady=4)
                ctk.CTkButton(row, text="🗑", width=30, height=24, fg_color="#5a1a1a",
                              command=_borrar).pack(side="right", padx=2, pady=4)

        refrescar()
        ctk.CTkButton(v, text="Cerrar", width=110, command=v.destroy,
                       fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"]).pack(pady=(0, 12))

    def _cmd_duplicar_a_historial(self, event=None):
        """Guarda el prompt actual en el historial sin generar uno nuevo."""
        try:
            texto = self.txt_salida.get("1.0", "end").strip()
            if not texto:
                self.set_estado("⚠️ No hay prompt para duplicar", "#e67e22")
                return "break"
            idea = self.txt_idea.get("1.0", "end").strip()
            modelo = ""
            modo = self.modo_var.get() if hasattr(self, "modo_var") else "imagen"
            if modo == "imagen" and hasattr(self, "combo_modelo_imagen"):
                modelo = self.combo_modelo_imagen.get() or ""
            elif modo == "video" and hasattr(self, "combo_modelo_video"):
                modelo = self.combo_modelo_video.get() or ""
            elif modo == "audio" and hasattr(self, "combo_modelo_audio"):
                modelo = self.combo_modelo_audio.get() or ""
            entry = {
                "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "idea": idea[:300],
                "texto": texto,
                "contenido": texto,
                "modo": self.modo_var.get() if hasattr(self, "modo_var") else "imagen",
                "modelo": modelo,
                "plataforma": self.plataforma_var.get() if hasattr(self, "plataforma_var") else "",
                "duplicado": True,
            }
            self.store.historial.insert(0, entry)
            self.store._guardar("historial")
            self.set_estado("📋 Duplicado al historial · Ctrl+D", "#2ecc71")
            try: self._sesion_log("📋 Ctrl+D: duplicó prompt al historial")
            except Exception as e:
                logger.debug(f"[silent] {e}")
        except Exception as e:
            self.set_estado(f"⚠️ Error al duplicar: {e}", "#e74c3c")
        return "break"

    def guardar_en_historial(self, texto):
        # Capturar configuración usada
        config_actual = {
            "modo":       self.modo_var.get(),
            "plataforma": self.plataforma_var.get(),
            "estilos":    [n for n, v in self.estilo_checks.items() if v.get()],
            "ratio":      self.ratio_var.get(),
            "nsfw":       self.switch_nsfw_var.get(),
            "personaje":  self.personaje_activo(),
            "lora":       self.lora_activo(),
            "destino":    self.destino_var.get(),
            "brief":      self.brief_var.get(),
            "modelo_img": self.combo_modelo_imagen.get() if hasattr(self, 'combo_modelo_imagen') else "",
            "modelo_vid": self.combo_modelo_video.get() if hasattr(self, 'combo_modelo_video') else "",
            "modelo_aud": self.combo_modelo_audio.get() if hasattr(self, 'combo_modelo_audio') else "",
        }
        self._ultima_config = config_actual

        self.store.agregar_historial({
            "fecha":      datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "modo":       self.modo_var.get(),
            "plataforma": self.plataforma_var.get(),
            "estilos":    self.estilos_texto(),
            "ratio":      self.ratio_var.get(),
            "nsfw":       self.switch_nsfw_var.get(),
            "personaje":  self.personaje_activo(),
            "lora":       self.lora_activo(),
            "destino":    self.destino_var.get(),
            "brief":      self.brief_var.get(),
            "contenido":  texto,
        })

    def _repetir_ultima_config(self):
        """Aplica la última configuración usada en el último prompt generado."""
        cfg = getattr(self, "_ultima_config", None)
        if not cfg:
            self.set_estado("⚠️ Aún no hay última configuración guardada. Genera un prompt primero.", "#e67e22")
            return

        try:
            # Modo
            if cfg.get("modo") and cfg["modo"] != self.modo_var.get():
                self.modo_var.set(cfg["modo"])
                self._on_modo_cambio()

            # Plataforma
            if cfg.get("plataforma"):
                self.plataforma_var.set(cfg["plataforma"])
                self._on_plataforma_cambio()

            # Modelo según modo
            if cfg["modo"] == "imagen" and cfg.get("modelo_img") and hasattr(self, 'combo_modelo_imagen'):
                self.combo_modelo_imagen.set(cfg["modelo_img"])
                self._on_modelo_imagen_cambio()
            elif cfg["modo"] == "video" and cfg.get("modelo_vid") and hasattr(self, 'combo_modelo_video'):
                self.combo_modelo_video.set(cfg["modelo_vid"])
            elif cfg["modo"] == "audio" and cfg.get("modelo_aud") and hasattr(self, 'combo_modelo_audio'):
                self.combo_modelo_audio.set(cfg["modelo_aud"])

            # Ratio, destino, NSFW, brief
            if cfg.get("ratio"): self.ratio_var.set(cfg["ratio"])
            if cfg.get("destino"): self.destino_var.set(cfg["destino"])
            self.switch_nsfw_var.set(cfg.get("nsfw", False))
            self.brief_var.set(cfg.get("brief", False))

            # Estilos
            if isinstance(cfg.get("estilos"), list):
                for n, v in self.estilo_checks.items():
                    v.set(n in cfg["estilos"])

            self.set_estado("🔁 Última configuración aplicada", "#2ecc71")
        except Exception as e:
            self.set_estado(f"⚠️ No se pudo aplicar todo: {e}", "#e67e22")

    def _guardar_favorito(self):
        texto = self.txt_salida.get("1.0", "end").strip()
        if not texto:
            self.set_estado("⚠️ No hay prompt para guardar.", "#e67e22")
            return
        self.store.agregar_favorito({
            "fecha":      datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "modo":       self.modo_var.get(),
            "plataforma": self.plataforma_var.get(),
            "estilos":    self.estilos_texto(),
            "ratio":      self.ratio_var.get(),
            "nsfw":       self.switch_nsfw_var.get(),
            "personaje":  self.personaje_activo(),
            "lora":       self.lora_activo(),
            "destino":    self.destino_var.get(),
            "brief":      self.brief_var.get(),
            "contenido":  texto,
        })
        self.set_estado("⭐ Guardado en favoritos.", "#f1c40f")

    def _guardar_estrella(self):
        texto = self.txt_salida.get("1.0", "end").strip()
        if not texto:
            self.set_estado("⚠️ No hay prompt para guardar como estrella.", "#e67e22")
            return
        nota = simpledialog.askstring("🌟 Prompt Estrella", "Nota breve (ej: 'pescador inuit brutal', 'huevo cristal top'):", parent=self)
        if not nota: nota = ""
        modo = self.modo_var.get()
        modelo = ""
        if modo == "video":
            modelo = self.modelo_video_valido()
        elif modo == "audio":
            modelo = self.combo_modelo_audio.get() if hasattr(self, 'combo_modelo_audio') else ""
        else:
            modelo = self.modelo_imagen_valido()
        self.store.agregar_estrella({
            "fecha":      datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "nota":       nota.strip(),
            "modo":       modo,
            "modelo":     modelo,
            "plataforma": self.plataforma_var.get(),
            "estilos":    self.estilos_texto(),
            "contenido":  texto,
        })
        self.set_estado(f"🌟 Prompt estrella guardado{': ' + nota if nota else ''}.", "#f39c12")

    def _exportar(self):
        texto = self.txt_salida.get("1.0", "end").strip()
        if not texto:
            self.set_estado("⚠️ No hay contenido para exportar.", "#e67e22")
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Texto", "*.txt")],
            initialfile=f"prompt_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        if ruta:
            fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            modo = self.modo_var.get().upper()
            plat = self.plataforma_var.get()
            header = (
                f"═══════════════════════════════════════════════\n"
                f"  G-Prompt Studio v{PUBLIC_VERSION}\n"
                f"  Exportado: {fecha}\n"
                f"═══════════════════════════════════════════════\n"
                f"  Modo:        {modo}\n"
                f"  Plataforma:  {plat}\n"
            )
            if modo == "VIDEO":
                header += f"  Motor:       {self.modelo_video_valido()}\n  Duración:    {self.duracion_var.get()}\n"
            elif modo == "AUDIO":
                motor_a = self.combo_modelo_audio.get() if hasattr(self, 'combo_modelo_audio') else ""
                header += f"  Motor:       {motor_a}\n"
            else:
                modelo = self.modelo_imagen_valido()
                if modelo: header += f"  Modelo:      {modelo}\n"
            header += f"  Ratio:       {self.ratio_var.get()}\n  Estilos:     {self.estilos_texto()}\n"

            p = self.combo_personaje.get()
            if p and p != "— Sin personaje —": header += f"  Personaje:   {p}\n"
            l = self.combo_lora.get()
            if l and l != "— Sin LoRA —": header += f"  LoRA:        {l}\n"

            dest = self.destino_var.get()
            if dest and dest != "— Personal —": header += f"  Destino:     {dest}\n"
            if self.switch_nsfw_var.get(): header += f"  NSFW:        Sí\n"
            if self.brief_var.get(): header += f"  Brief:       Activo\n"

            # Filtros audio
            if modo == "AUDIO":
                em = self.emocion_var.get() if hasattr(self, 'emocion_var') else ""
                if em and em != "— Emoción —": header += f"  Emoción:     {em}\n"
                vz = self.voz_var.get() if hasattr(self, 'voz_var') else ""
                if vz and vz != "— Voz —": header += f"  Voz:         {vz}\n"
                id_a = self.idioma_audio_var.get() if hasattr(self, 'idioma_audio_var') else ""
                if id_a and id_a != "— Idioma —": header += f"  Idioma:      {id_a}\n"

            header += f"═════════════════════════════════════════════\n\n"

            with open(ruta, "w", encoding="utf-8") as f:
                f.write(header + texto)
            self.set_estado(f"💾 Exportado: {Path(ruta).name}", "#2ecc71")

    def _abrir_snippets(self):
        """Gestor de snippets reutilizables (frases cortas que añades a prompts)."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        prefs = self.store.cargar_preferencias()
        snippets = prefs.get("snippets", [])

        vent = GPromptWindow(self)
        vent.title("🏷️ Snippets reutilizables")
        vent.geometry("620x550")
        vent.transient(self)
        ctk.CTkLabel(vent, text="🏷️ Snippets reutilizables", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text="Frases cortas que añades al final del POSITIVE con un click",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

        # Form añadir nuevo
        form = ctk.CTkFrame(vent, fg_color=c["fg_dark"], corner_radius=6)
        form.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(form, text="➕ Nuevo snippet", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(8, 2))
        ent_nombre = ctk.CTkEntry(form, placeholder_text="Nombre (ej: 'Mi look cinematográfico')", width=520)
        ent_nombre.pack(padx=10, pady=2)
        ent_tags = ctk.CTkEntry(form, placeholder_text="Tags/frase (ej: cinematic lighting, volumetric, 8K)", width=520)
        ent_tags.pack(padx=10, pady=(2, 5))

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        def refrescar():
            for w in scroll.winfo_children(): w.destroy()
            actual = prefs.get("snippets", [])
            if not actual:
                ctk.CTkLabel(scroll, text="Aún no tienes snippets. Crea el primero arriba.",
                             font=ctk.CTkFont(size=11), text_color="#666666").pack(pady=20)
                return
            for i, s in enumerate(actual):
                card = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=6)
                card.pack(fill="x", pady=2)
                ctk.CTkLabel(card, text=f"  🏷️ {s.get('nombre', '?')}",
                             font=ctk.CTkFont(size=11, weight="bold"), text_color=c["hdr_text"]).pack(anchor="w", padx=8, pady=(4, 0))
                ctk.CTkLabel(card, text=f"  {s.get('tags', '')[:120]}",
                             font=ctk.CTkFont(size=10), text_color=c["muted_text"],
                             wraplength=480, justify="left", anchor="w").pack(fill="x", padx=8, pady=(0, 2))
                btn_row = ctk.CTkFrame(card, fg_color="transparent")
                btn_row.pack(fill="x", padx=5, pady=(0, 4))
                def _aplicar(s=s):
                    self._aplicar_atajo_tags(s.get("tags", ""))
                    vent.destroy()
                def _borrar(idx=i):
                    actual2 = prefs.get("snippets", [])
                    if idx < len(actual2):
                        actual2.pop(idx)
                        prefs["snippets"] = actual2
                        self.store.guardar_preferencias(prefs)
                        refrescar()
                ctk.CTkButton(btn_row, text="➕ Añadir al prompt", width=140, height=22, fg_color="#1a7a3c",
                              font=ctk.CTkFont(size=10), command=_aplicar).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text="🗑", width=30, height=22, fg_color="#5a1a1a",
                              font=ctk.CTkFont(size=10), command=_borrar).pack(side="right", padx=2)

        def crear():
            nombre = ent_nombre.get().strip()
            tags = ent_tags.get().strip()
            if not nombre or not tags:
                self.set_estado("⚠️ Rellena nombre y tags.", "#e67e22")
                return
            actual = prefs.get("snippets", [])
            actual.append({"nombre": nombre, "tags": tags})
            prefs["snippets"] = actual
            self.store.guardar_preferencias(prefs)
            ent_nombre.delete(0, "end")
            ent_tags.delete(0, "end")
            refrescar()

        ctk.CTkButton(form, text="✅ Crear snippet", width=140, height=26, fg_color="#1a7a3c",
                      font=ctk.CTkFont(size=10, weight="bold"), command=crear).pack(pady=(0, 8))

        refrescar()

    def _abrir_formulas(self):
        """Gestor de fórmulas: combinaciones de tags reutilizables (igual que snippets pero más estructurado)."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        # Reutilizar snippets pero llamarlas "fórmulas" (UI diferente sin entrada inline)
        prefs = self.store.cargar_preferencias()
        formulas = prefs.get("formulas", [])

        vent = GPromptWindow(self)
        vent.title("📐 Fórmulas guardadas")
        vent.geometry("680x550")
        vent.transient(self)
        ctk.CTkLabel(vent, text="📐 Fórmulas guardadas", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text="Combinaciones de tags listas para aplicar (más completas que snippets)",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

        # Botón "Guardar el POSITIVE actual como fórmula"
        def _guardar_actual():
            from tkinter import simpledialog
            pos = self.extraer_positive()
            if not pos:
                self.set_estado("⚠️ No hay POSITIVE para guardar como fórmula.", "#e67e22")
                return
            nombre = simpledialog.askstring("📐 Nueva fórmula", "Nombre para esta fórmula:", parent=vent)
            if not nombre: return
            actual = prefs.get("formulas", [])
            actual.append({
                "nombre": nombre,
                "positive": pos,
                "negative": self.extraer_negative() or "",
                "fecha": datetime.datetime.now().strftime("%Y-%m-%d"),
            })
            prefs["formulas"] = actual
            self.store.guardar_preferencias(prefs)
            refrescar()
            self.set_estado(f"📐 Fórmula '{nombre}' guardada", "#2ecc71")

        ctk.CTkButton(vent, text="💾 Guardar POSITIVE actual como fórmula", width=300, height=28,
                      fg_color="#1a7a3c", hover_color="#145e2d",
                      font=ctk.CTkFont(size=11), command=_guardar_actual).pack(pady=5)

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        def refrescar():
            for w in scroll.winfo_children(): w.destroy()
            actual = prefs.get("formulas", [])
            if not actual:
                ctk.CTkLabel(scroll, text="No hay fórmulas. Genera un prompt y guárdalo aquí.",
                             font=ctk.CTkFont(size=11), text_color="#666666").pack(pady=20)
                return
            for i, f in enumerate(actual):
                card = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=6)
                card.pack(fill="x", pady=3)
                ctk.CTkLabel(card, text=f"  📐 {f.get('nombre', '?')}  ·  {f.get('fecha', '')}",
                             font=ctk.CTkFont(size=11, weight="bold"), text_color=c["hdr_text"]).pack(anchor="w", padx=8, pady=(4, 0))
                preview = f.get("positive", "")[:200]
                ctk.CTkLabel(card, text=f"  POS: {preview}{'...' if len(f.get('positive','')) > 200 else ''}",
                             font=ctk.CTkFont(size=10), text_color=c["muted_text"],
                             wraplength=540, justify="left", anchor="w").pack(fill="x", padx=8, pady=(0, 2))
                btn_row = ctk.CTkFrame(card, fg_color="transparent")
                btn_row.pack(fill="x", padx=5, pady=(0, 4))
                def _cargar(form=f):
                    txt = f"POSITIVE PROMPT: {form.get('positive', '')}"
                    if form.get('negative'):
                        txt += f"\nNEGATIVE PROMPT: {form.get('negative')}"
                    self.actualizar_salida(txt)
                    vent.destroy()
                    self.set_estado(f"📐 Fórmula '{form.get('nombre')}' cargada", "#2ecc71")
                def _borrar(idx=i):
                    actual2 = prefs.get("formulas", [])
                    if idx < len(actual2):
                        actual2.pop(idx)
                        prefs["formulas"] = actual2
                        self.store.guardar_preferencias(prefs)
                        refrescar()
                ctk.CTkButton(btn_row, text="✅ Cargar", width=80, height=22, fg_color="#1a7a3c",
                              font=ctk.CTkFont(size=10), command=_cargar).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text="🗑", width=30, height=22, fg_color="#5a1a1a",
                              font=ctk.CTkFont(size=10), command=_borrar).pack(side="right", padx=2)

        refrescar()

    def _abrir_biblioteca(self):
        """Ventana con prompts de ejemplo probados.

        Features:
          - Búsqueda en tiempo real por título, modelo, tags y estilos.
          - Filtros adicionales por plataforma y dificultad.
          - Badges visuales (dificultad coloreada, plataforma, tags).
          - Contador "Mostrando X de Y".
          - Botón "⭐ Favorito" para guardar el ejemplo en favoritos.
        """
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        vent = GPromptWindow(self)
        vent.title("📚 Biblioteca de Prompts de Ejemplo")
        vent.geometry("820x680")
        vent.transient(self)

        # ── Encabezado ───────────────────────────────────────────────
        ctk.CTkLabel(
            vent, text="📚 Prompts de ejemplo probados",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(10, 2))
        lbl_subtitulo = ctk.CTkLabel(
            vent, text="Filtra, busca y carga uno en el resultado",
            font=ctk.CTkFont(size=10), text_color=c["muted_text"]
        )
        lbl_subtitulo.pack(pady=(0, 6))

        # ── Estado de filtros ────────────────────────────────────────
        filtro_modo_var = ctk.StringVar(value="todos")
        filtro_plat_var = ctk.StringVar(value="todas")
        filtro_dif_var = ctk.StringVar(value="todas")
        busqueda_var = ctk.StringVar(value="")

        # ── Fila 1: Búsqueda ─────────────────────────────────────────
        fila_busqueda = ctk.CTkFrame(vent, fg_color="transparent")
        fila_busqueda.pack(fill="x", padx=15, pady=(2, 4))
        ctk.CTkLabel(
            fila_busqueda, text="🔍", font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(0, 4))
        entry_busqueda = ctk.CTkEntry(
            fila_busqueda, textvariable=busqueda_var,
            placeholder_text="Buscar por título, modelo, tags o estilos…",
            height=26, font=ctk.CTkFont(size=11)
        )
        entry_busqueda.pack(side="left", fill="x", expand=True)

        # ── Fila 2: Filtros de modo (botones rápidos) ───────────────
        fila_modos = ctk.CTkFrame(vent, fg_color="transparent")
        fila_modos.pack(fill="x", padx=15, pady=(2, 2))
        ctk.CTkLabel(
            fila_modos, text="Modo:", font=ctk.CTkFont(size=10, weight="bold"),
            text_color=c["muted_text"], width=55, anchor="w"
        ).pack(side="left")
        btns_modo = []  # para poder cambiar su color visualmente

        def _set_modo(val):
            filtro_modo_var.set(val)
            for b, v in btns_modo:
                b.configure(fg_color=c["fg_frame"] if v == val else c["fg_dark"])
            refrescar()

        for txt, val in [("Todos", "todos"), ("🖼 Imagen", "imagen"),
                         ("🎬 Vídeo", "video"), ("🎵 Audio", "audio")]:
            b = ctk.CTkButton(
                fila_modos, text=txt, width=78, height=24,
                fg_color=c["fg_frame"] if val == "todos" else c["fg_dark"],
                hover_color="#2a2a3a", font=ctk.CTkFont(size=10),
                command=lambda v=val: _set_modo(v)
            )
            b.pack(side="left", padx=2)
            btns_modo.append((b, val))

        # ── Fila 3: Filtros de plataforma + dificultad (combos) ──────
        fila_combos = ctk.CTkFrame(vent, fg_color="transparent")
        fila_combos.pack(fill="x", padx=15, pady=(4, 2))

        # Construir lista dinámica de plataformas presentes en la biblioteca
        plataformas_presentes = ["todas"] + sorted({
            ej.get("plataforma", "") for ej in BIBLIOTECA_EJEMPLOS if ej.get("plataforma")
        })

        ctk.CTkLabel(
            fila_combos, text="Plataforma:", font=ctk.CTkFont(size=10, weight="bold"),
            text_color=c["muted_text"], width=80, anchor="w"
        ).pack(side="left")
        combo_plat = ctk.CTkComboBox(
            fila_combos, values=plataformas_presentes, variable=filtro_plat_var,
            width=200, height=24, font=ctk.CTkFont(size=10),
            command=lambda _: refrescar()
        )
        combo_plat.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            fila_combos, text="Dificultad:", font=ctk.CTkFont(size=10, weight="bold"),
            text_color=c["muted_text"], width=72, anchor="w"
        ).pack(side="left")
        combo_dif = ctk.CTkComboBox(
            fila_combos, values=["todas", "principiante", "medio", "avanzado"],
            variable=filtro_dif_var, width=130, height=24,
            font=ctk.CTkFont(size=10),
            command=lambda _: refrescar()
        )
        combo_dif.pack(side="left")

        # Botón "Limpiar filtros"
        def _limpiar():
            busqueda_var.set("")
            filtro_plat_var.set("todas")
            filtro_dif_var.set("todas")
            _set_modo("todos")

        ctk.CTkButton(
            fila_combos, text="✖ Limpiar", width=80, height=24,
            fg_color=c["fg_dark"], hover_color="#2a2a3a",
            font=ctk.CTkFont(size=10), command=_limpiar
        ).pack(side="right")

        # ── Contador "Mostrando X de Y" ──────────────────────────────
        lbl_contador = ctk.CTkLabel(
            vent, text="", font=ctk.CTkFont(size=10),
            text_color=c["muted_text"], anchor="w"
        )
        lbl_contador.pack(fill="x", padx=15, pady=(6, 2))

        # ── Lista scrollable de cards ────────────────────────────────
        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        # ── Colores por dificultad (para badges) ─────────────────────
        DIF_COLORS = {
            "principiante": ("#2ecc71", "#FFFFFF"),  # verde
            "medio":        ("#f39c12", "#FFFFFF"),  # naranja
            "avanzado":     ("#e74c3c", "#FFFFFF"),  # rojo
        }

        def _filtrar():
            """Aplica los filtros activos y devuelve la lista resultante."""
            modo_f = filtro_modo_var.get()
            plat_f = filtro_plat_var.get()
            dif_f = filtro_dif_var.get()
            q = busqueda_var.get().strip().lower()

            resultado = []
            for ej in BIBLIOTECA_EJEMPLOS:
                if modo_f != "todos" and ej.get("modo") != modo_f:
                    continue
                if plat_f != "todas" and ej.get("plataforma") != plat_f:
                    continue
                if dif_f != "todas" and ej.get("dificultad") != dif_f:
                    continue
                if q:
                    # Busca en título, modelo, tags y estilos
                    haystack = " ".join([
                        ej.get("titulo", ""),
                        ej.get("modelo", ""),
                        " ".join(ej.get("tags", []) or []),
                        " ".join(ej.get("estilos", []) or []),
                    ]).lower()
                    if q not in haystack:
                        continue
                resultado.append(ej)
            return resultado

        def refrescar():
            for w in scroll.winfo_children():
                w.destroy()

            ejemplos = _filtrar()
            total_biblioteca = len(BIBLIOTECA_EJEMPLOS)
            lbl_contador.configure(
                text=f"Mostrando {len(ejemplos)} de {total_biblioteca} ejemplos"
            )

            if not ejemplos:
                ctk.CTkLabel(
                    scroll, text="🔎  Ningún ejemplo coincide con los filtros.",
                    font=ctk.CTkFont(size=12), text_color=c["muted_text"]
                ).pack(pady=30)
                return

            for ej in ejemplos:
                card = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=8)
                card.pack(fill="x", pady=3, padx=3)

                # Header con título + modelo
                hdr = ctk.CTkFrame(card, fg_color=c["fg_dark"], corner_radius=6, height=30)
                hdr.pack(fill="x", padx=5, pady=(5, 2))
                hdr.pack_propagate(False)

                modo_emoji = {"imagen": "🖼", "video": "🎬", "audio": "🎵"}.get(ej.get("modo", ""), "")
                ctk.CTkLabel(
                    hdr,
                    text=f"  {modo_emoji} {ej.get('titulo', '(sin título)')}  ·  {ej.get('modelo', '')}",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=c["hdr_text"]
                ).pack(side="left")

                # Fila de badges (dificultad + plataforma + estilos)
                fila_badges = ctk.CTkFrame(card, fg_color="transparent")
                fila_badges.pack(fill="x", padx=8, pady=(2, 2))

                dif = ej.get("dificultad", "")
                if dif in DIF_COLORS:
                    bg, fg = DIF_COLORS[dif]
                    ctk.CTkLabel(
                        fila_badges, text=f" {dif.upper()} ",
                        font=ctk.CTkFont(size=9, weight="bold"),
                        fg_color=bg, text_color=fg, corner_radius=4
                    ).pack(side="left", padx=(0, 4))

                plat = ej.get("plataforma", "")
                if plat:
                    ctk.CTkLabel(
                        fila_badges, text=f" {plat} ",
                        font=ctk.CTkFont(size=9),
                        fg_color=c["fg_dark"], text_color=c["muted_text"],
                        corner_radius=4
                    ).pack(side="left", padx=(0, 4))

                estilos = ej.get("estilos", [])
                if estilos:
                    ctk.CTkLabel(
                        fila_badges, text=f"{', '.join(estilos)}",
                        font=ctk.CTkFont(size=9, slant="italic"),
                        text_color=c["muted_text"]
                    ).pack(side="left", padx=(4, 0))

                # Tags (si existen, segunda línea)
                tags = ej.get("tags", [])
                if tags:
                    ctk.CTkLabel(
                        card, text="🏷  " + " · ".join(tags),
                        font=ctk.CTkFont(size=9), text_color=c["muted_text"],
                        anchor="w"
                    ).pack(fill="x", padx=10, pady=(0, 2))

                # Preview del prompt
                preview = ej["prompt"][:150] + "..." if len(ej["prompt"]) > 150 else ej["prompt"]
                ctk.CTkLabel(
                    card, text=preview,
                    font=ctk.CTkFont(size=10), text_color=c["muted_text"],
                    wraplength=760, justify="left", anchor="w"
                ).pack(fill="x", padx=10, pady=(2, 4))

                # Botones de acción
                btn_row = ctk.CTkFrame(card, fg_color="transparent")
                btn_row.pack(fill="x", padx=5, pady=(0, 6))

                def _usar(e=ej):
                    self.actualizar_salida(e["prompt"])
                    vent.destroy()
                    self.set_estado(f"📚 Ejemplo cargado: {e['titulo']}", "#2ecc71")

                def _copiar(e=ej):
                    pyperclip.copy(e["prompt"])
                    self.set_estado(f"📋 Ejemplo copiado: {e['titulo']}", "#2ecc71")

                def _favorito(e=ej):
                    """Guarda el ejemplo en favoritos del usuario."""
                    try:
                        self.store.agregar_favorito({
                            "fecha":      datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "modo":       e.get("modo", "imagen"),
                            "plataforma": e.get("plataforma", ""),
                            "estilos":    ", ".join(e.get("estilos", [])),
                            "ratio":      "",
                            "nsfw":       False,
                            "personaje":  "",
                            "lora":       "",
                            "destino":    "— Personal —",
                            "brief":      False,
                            "contenido":  e["prompt"],
                            "origen":     f"Biblioteca: {e.get('titulo', '')}",
                        })
                        self.set_estado(
                            f"⭐ Guardado en favoritos: {e['titulo']}", "#f1c40f"
                        )
                    except Exception as err:
                        import logging
                        logging.getLogger("gprompt").warning(
                            f"No se pudo guardar favorito: {err}"
                        )
                        self.set_estado("⚠️ Error al guardar favorito", "#e67e22")

                ctk.CTkButton(
                    btn_row, text="✅ Usar", width=68, height=22,
                    fg_color="#1a7a3c", hover_color="#145e2d",
                    font=ctk.CTkFont(size=10), command=_usar
                ).pack(side="left", padx=2)
                ctk.CTkButton(
                    btn_row, text="📋 Copiar", width=68, height=22,
                    fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                    font=ctk.CTkFont(size=10), command=_copiar
                ).pack(side="left", padx=2)
                ctk.CTkButton(
                    btn_row, text="⭐ Favorito", width=78, height=22,
                    fg_color="#b8860b", hover_color="#8b6508",
                    font=ctk.CTkFont(size=10), command=_favorito
                ).pack(side="left", padx=2)

        # Reactividad: cualquier cambio en la búsqueda refresca al instante
        busqueda_var.trace_add("write", lambda *_: refrescar())

        # Render inicial
        refrescar()

    def actualizar_combo_personajes(self):
        nombres = self.store.nombres_personajes()
        self.combo_personaje.configure(values=nombres)
        if self.combo_personaje.get() not in nombres:
            self.combo_personaje.set("— Sin personaje —")

    def actualizar_combo_loras(self):
        nombres = self.store.nombres_loras()
        self.combo_lora.configure(values=nombres)
        if self.combo_lora.get() not in nombres:
            self.combo_lora.set("— Sin LoRA —")
        # Refrescar trigger visible y aviso de compatibilidad
        try: self._actualizar_lora_trigger_visible()
        except Exception as e:
            logger.debug(f"[silent] {e}")

    def actualizar_combo_plantillas(self):
        nombres = self.store.nombres_plantillas()
        self.combo_plantilla.configure(values=nombres)
        if self.combo_plantilla.get() not in nombres:
            self.combo_plantilla.set("— Sin plantilla —")

    def _cargar_preferencias(self):
        prefs = self.store.cargar_preferencias()
        if not prefs: return
        try:
            # Geometría de ventana
            geo = prefs.get("geometria", "")
            if geo:
                try:
                    self.geometry(geo)
                except Exception as _e:
                    logger.debug(f"[silent] {_e}")
            # Tema (cargado de forma segura: diferido y con fallback)
            tema = prefs.get("tema", "dark")
            if tema in ("dark", "light", "system"):
                # Diferir la aplicación del tema hasta que mainloop esté listo
                # para evitar TclError "application has been destroyed" durante init
                def _aplicar_tema_diferido(t=tema):
                    try:
                        ctk.set_appearance_mode(t)
                    except Exception as e:
                        # Si falla (ej. tema light incompatible con theme.json), reset a dark
                        try:
                            ctk.set_appearance_mode("dark")
                            # Persistir el reset para que no vuelva a fallar
                            try:
                                prefs2 = self.store.cargar_preferencias()
                                prefs2["tema"] = "dark"
                                self.store.guardar_preferencias(prefs2)
                            except Exception as e:
                                logger.debug(f"[silent] {e}")
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
                    # Tras cambiar el modo de apariencia, los labels que
                    # se construyeron con el tema "dark" inicial mantienen
                    # sus text_color de tema oscuro y quedan invisibles
                    # sobre el fondo claro. Hay que repintar el tema
                    # MANUALMENTE después del set_appearance_mode con un
                    # pequeño delay
                    # para que CTk termine su transición interna.
                    try:
                        if hasattr(self, "_apply_theme_colors"):
                            self.after(50, self._apply_theme_colors)
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")
                try:
                    self.after(200, _aplicar_tema_diferido)
                except Exception as e:
                    logger.debug(f"[silent] {e}")

            # Sonido
            self._sonido_activo = prefs.get("sonido", False)

            # --- Cargar el Cerebro (LLM) ---
            llm = prefs.get("llm", "DeepSeek V3")
            if hasattr(self, 'llm_var'): self.llm_var.set(llm)

            modo = prefs.get("modo", "imagen")
            if modo != self.modo_var.get():
                self.modo_var.set(modo)
                self._on_modo_cambio()

            plat = prefs.get("plataforma", "")
            if plat:
                self.plataforma_var.set(plat)
                self._on_plataforma_cambio()

            m_img = prefs.get("modelo_img", "")
            if m_img: self.combo_modelo_imagen.set(m_img)

            m_vid = prefs.get("modelo_vid", "")
            if m_vid: self.combo_modelo_video.set(m_vid)

            ratio = prefs.get("ratio", "")
            if ratio: self.ratio_var.set(ratio)

            estilos = prefs.get("estilos", [])
            if estilos:
                for n, v in self.estilo_checks.items(): v.set(n in estilos)

            self.switch_nsfw_var.set(prefs.get("nsfw", False))
            self.switch_traduccion_var.set(prefs.get("traduccion", True))

            pers = prefs.get("personaje", "")
            if pers: self.combo_personaje.set(pers)

            lora = prefs.get("lora", "")
            if lora: self.combo_lora.set(lora)

            dur = prefs.get("duracion", "")
            if dur: self.duracion_var.set(dur)

            m_aud = prefs.get("modelo_aud", "")
            if m_aud and hasattr(self, 'combo_modelo_audio'): self.combo_modelo_audio.set(m_aud)

            if hasattr(self, 'switch_instrumental_var'):
                self.switch_instrumental_var.set(prefs.get("instrumental", False))

            if hasattr(self, 'emocion_var'):
                em = prefs.get("emocion_audio", "— Emoción —")
                self.emocion_var.set(em if em else "— Emoción —")
            if hasattr(self, 'voz_var'):
                vz = prefs.get("voz_audio", "— Voz —")
                self.voz_var.set(vz if vz else "— Voz —")
            if hasattr(self, 'idioma_audio_var'):
                id_a = prefs.get("idioma_audio", "— Idioma —")
                self.idioma_audio_var.set(id_a if id_a else "— Idioma —")

            dest = prefs.get("destino", "— Personal —")
            if dest in DESTINOS: self.destino_var.set(dest)

            self.brief_var.set(prefs.get("brief", False))
            self._on_brief_cambio()

            # Cargar preferencia de grabación de vídeo de sesión
            self._sesion_grabar_video = prefs.get("sesion_grabar_video", False)

        except Exception as _e:

            logger.debug(f"[silent] {_e}")
    def _guardar_preferencias(self):
        # como `nombre` que no se gestionan en este método.
        try:
            prefs = self.store.cargar_preferencias() or {}
        except Exception:
            prefs = {}

        prefs.update({
            "llm":         self.llm_var.get() if hasattr(self, 'llm_var') else "DeepSeek V3",
            "modo":        self.modo_var.get(),
            "plataforma":  self.plataforma_var.get(),
            "modelo_img":  self.combo_modelo_imagen.get(),
            "modelo_vid":  self.combo_modelo_video.get(),
            "modelo_aud":  self.combo_modelo_audio.get() if hasattr(self, 'combo_modelo_audio') else "",
            "ratio":       self.ratio_var.get(),
            "estilos":     self.estilos_seleccionados(),
            "nsfw":        self.switch_nsfw_var.get(),
            "traduccion":  self.switch_traduccion_var.get(),
            "personaje":   self.combo_personaje.get(),
            "lora":        self.combo_lora.get(),
            "duracion":    self.duracion_var.get(),
            "destino":     self.destino_var.get(),
            "brief":       self.brief_var.get(),
            "instrumental": self.switch_instrumental_var.get() if hasattr(self, 'switch_instrumental_var') else False,
            "emocion_audio": self.emocion_var.get() if hasattr(self, 'emocion_var') else "",
            "voz_audio": self.voz_var.get() if hasattr(self, 'voz_var') else "",
            "idioma_audio": self.idioma_audio_var.get() if hasattr(self, 'idioma_audio_var') else "",
            "tema":        ctk.get_appearance_mode().lower(),
            "sonido":      getattr(self, '_sonido_activo', False),
            "sesion_grabar_video": getattr(self, '_sesion_grabar_video', False),
        })
        self.store.guardar_preferencias(prefs)

    def _pegar_inteligente_clipboard(self, event=None):
        """Pegado inteligente: si el portapapeles tiene un prompt completo (con cabecera POSITIVE PROMPT:),
        lo carga en txt_salida. Si tiene imagen, la pone como imagen ref. Si no, comportamiento normal."""
        try:
            # Si el foco está en el textbox de idea, NO interceptar — comportamiento normal de pegar
            try:
                foco = self.focus_get()
                if foco is not None and hasattr(self, "txt_idea") and foco == self.txt_idea._textbox:
                    return None  # dejar que tk lo maneje normalmente
            except Exception as e:
                logger.debug(f"[silent] {e}")
            # Comprobar si el clipboard tiene texto que parece un prompt formado
            try:
                texto_clip = pyperclip.paste()
            except Exception:
                texto_clip = ""
            es_prompt_completo = False
            if texto_clip and len(texto_clip) > 30:
                # Detectar marcadores típicos
                marcadores = ["POSITIVE PROMPT:", "NEGATIVE PROMPT:", "PROMPT:", "POSITIVE:", "NEGATIVE:"]
                tiene_marcador = any(m in texto_clip for m in marcadores)
                if tiene_marcador:
                    es_prompt_completo = True

            if es_prompt_completo:
                # Cargar en txt_salida
                self.actualizar_salida(texto_clip)
                self.set_estado("📥 Prompt pegado en Resultado (detectado por marcadores)", "#2ecc71")
                try: self._sesion_log("📥 Pegó prompt completo desde portapapeles")
                except Exception as e:
                    logger.debug(f"[silent] {e}")
                return "break"
            # Si no es prompt completo, intentar imagen
            return self._pegar_imagen_clipboard(event)
        except Exception:
            return None

    def _idea_aleatoria_historial(self):
        """Carga una idea aleatoria de prompts pasados (inspiración rápida)."""
        import random
        items = (self.store.historial or []) + (self.store.favoritos or []) + (self.store.estrellas or [])
        if not items:
            self.set_estado("⚠️ Aún no hay prompts en historial.", "#e67e22")
            return "break"
        item = random.choice(items)
        if isinstance(item, dict):
            txt = item.get("contenido") or item.get("texto", "")
        else:
            txt = str(item)
        # Extraer solo el positive como idea
        import re
        m = re.search(r'POSITIVE\s+PROMPT\s*:\s*(.+?)(?=\n\s*NEGATIVE|$)', txt, re.DOTALL | re.IGNORECASE)
        idea = m.group(1).strip() if m else txt[:300]
        self.txt_idea.delete("1.0", "end")
        self.txt_idea.insert("1.0", idea[:300])
        self.set_estado("🎲 Idea cargada desde historial", "#3498db")
        return "break"

    def _pegar_imagen_clipboard(self, event=None):
        """Intenta pegar una imagen del portapapeles."""
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img and hasattr(img, 'size'):
                self._cargar_imagen_desde_pil(img.convert("RGB"), "clipboard_paste")
                self.set_estado("📋 Imagen pegada desde el portapapeles", "#2ecc71")
                return "break"
        except Exception as _e:
            logger.debug(f"[silent] {_e}")