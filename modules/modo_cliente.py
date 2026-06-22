"""Modo Cliente — brief profesional + 5 propuestas + Compañero Moodboard.

Cluster funcional independiente: trabaja con brief de cliente y
propuestas múltiples para presentación profesional.

Métodos:
  • _cmd_modo_cliente                  — modal de brief + plantillas +
                                         lanzar generación.
  • _generar_propuestas_cliente        — worker que pide 5 propuestas
                                         distintas al LLM.
  • _abrir_comparador_propuestas       — comparador especializado con
                                         scoring de las 5 propuestas.
  • _cmd_companero_moodboard           — selector de estilo visual con
                                         galería de referencias.
  • _abrir_biblioteca_estilos_moodboard — biblioteca de estilos
                                         guardados.

Dependencias self (provistas por ArquitectoApp):
  txt_idea, modo_var, deepseek, store, after, set_estado,
  toggle_botones, actualizar_salida, _sesion_log, _sonar_completado,
  _parsear_bloques_numerados, _abrir_comparador.
"""
import datetime
import logging

import customtkinter as ctk
import pyperclip

from config import get_theme_colors
from modules.gprompt_window import GPromptWindow
from modules.i18n import tr
from workers import limpiar_marcadores, log_future_exc

logger = logging.getLogger(__name__)


class ModoClienteService:
    """Modo Cliente (brief + 5 propuestas) + Compañero Moodboard.

    A1 fase 2 (sesión 14): servicio aislado con app por composición.
    Acceso: `app.cliente.cmd_modo_cliente()`, `app.cliente.cmd_companero_moodboard()`.
    """

    def __init__(self, app):
        self.app = app

    def _cmd_modo_cliente(self):
        """Modo Cliente: brief simplificado para generar 5 propuestas profesionales.

        Recuerda el último brief (preferencias.modo_cliente_ultimo_brief)
        y ofrece plantillas predefinidas para arrancar rápido.
        """
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        vent = GPromptWindow(self.app)
        vent.title("💼 Modo Cliente")
        vent.geometry("640x720")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("💼 Modo Cliente — Brief profesional"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text=tr("Define un brief y genera 5 propuestas profesionales coherentes"),
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

        # ── Plantillas predefinidas ──
        PLANTILLAS_BRIEF = {
            "Logo minimalista": {
                "Tipo de proyecto": "Logo",
                "Cliente / sector": "Marca tech / startup",
                "Tono / estilo deseado": "Minimalista geométrico, sans-serif, monocromo",
                "Público objetivo": "Profesionales 25-40 urbanos",
                "Restricciones / keywords": "Sin gradientes, formato vectorial, fondo blanco",
            },
            "Banner web hero": {
                "Tipo de proyecto": "Banner / Hero image para landing",
                "Cliente / sector": "App SaaS B2B",
                "Tono / estilo deseado": "Moderno, espacioso, ilustración isométrica suave",
                "Público objetivo": "Profesionales tech, decision-makers",
                "Restricciones / keywords": "16:9 horizontal, paleta corporativa azul-blanco",
            },
            "Producto e-commerce": {
                "Tipo de proyecto": "Foto de producto",
                "Cliente / sector": "E-commerce moda",
                "Tono / estilo deseado": "Studio shot, fondo blanco, iluminación 360°",
                "Público objetivo": "Compradores online 20-45",
                "Restricciones / keywords": "Sin modelo, solo producto, formato 1:1",
            },
            "Editorial fashion": {
                "Tipo de proyecto": "Editorial de moda",
                "Cliente / sector": "Revista de moda / marca lujo",
                "Tono / estilo deseado": "Editorial cinematográfico, alta producción, drama lumínico",
                "Público objetivo": "Lectores de Vogue / Harper's Bazaar",
                "Restricciones / keywords": "Formato vertical 2:3, paleta tierra y dorado",
            },
            "Anuncio TikTok 15s": {
                "Tipo de proyecto": "Vídeo corto vertical para TikTok/Reels",
                "Cliente / sector": "Marca DTC (bebida / cosmética / wellness)",
                "Tono / estilo deseado": "Energético, viral, gancho en primer segundo",
                "Público objetivo": "Gen Z 16-24",
                "Restricciones / keywords": "9:16, texto en pantalla, máximo 15s",
            },
        }

        plantilla_row = ctk.CTkFrame(vent, fg_color="transparent")
        plantilla_row.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkLabel(plantilla_row, text=tr("Plantilla:"),
                     font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(0, 6))
        plantilla_var = ctk.StringVar(value="— Personalizada —")
        combo_plantilla = ctk.CTkComboBox(
            plantilla_row, width=280, variable=plantilla_var,
            values=["— Personalizada —"] + list(PLANTILLAS_BRIEF.keys()),
        )
        combo_plantilla.pack(side="left")

        # Imagen de referencia opcional (logo, moodboard, etc.)
        frame_img = ctk.CTkFrame(vent, fg_color=c["fg_dark"], corner_radius=6)
        frame_img.pack(fill="x", padx=20, pady=(0, 8))
        ctk.CTkLabel(frame_img, text=tr("📎 Imagen de referencia (opcional):"),
                     font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(frame_img, text=tr("Logo del cliente, moodboard, ejemplo de estilo deseado..."),
                     font=ctk.CTkFont(size=9), text_color=c["muted_text"]).pack(anchor="w", padx=10)

        cliente_state = {"imagen": None, "descripcion": ""}
        lbl_estado_img = ctk.CTkLabel(frame_img, text=tr("(sin imagen cargada)"),
                                        font=ctk.CTkFont(size=10), text_color=c["muted_text"])
        lbl_estado_img.pack(anchor="w", padx=10, pady=2)

        def _cargar_imagen_cliente():
            from tkinter import filedialog

            from PIL import Image
            ruta = filedialog.askopenfilename(
                title="Selecciona imagen de referencia (logo, moodboard...)",
                filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp")]
            )
            if not ruta: return
            try:
                img = Image.open(ruta)
                cliente_state["imagen"] = img
                lbl_estado_img.configure(text=f"⏳ Analizando imagen...", text_color="#f39c12")

                def _analizar():
                    try:
                        desc, motor = self.app.vision.describir(img, "imagen", lambda m: None)
                        cliente_state["descripcion"] = desc
                        lbl_estado_img.configure(text=f"✅ Imagen analizada (vision: {motor})", text_color="#2ecc71")
                    except Exception as e:
                        lbl_estado_img.configure(text=f"❌ Error al analizar: {e}", text_color="#e74c3c")
                self.app._executor.submit(_analizar).add_done_callback(log_future_exc)
            except Exception as e:
                lbl_estado_img.configure(text=f"❌ Error: {e}", text_color="#e74c3c")

        def _quitar_imagen():
            cliente_state["imagen"] = None
            cliente_state["descripcion"] = ""
            lbl_estado_img.configure(text=tr("(sin imagen cargada)"), text_color=c["muted_text"])

        f_btns_img = ctk.CTkFrame(frame_img, fg_color="transparent")
        f_btns_img.pack(fill="x", padx=10, pady=(2, 8))
        ctk.CTkButton(f_btns_img, text=tr("📂 Cargar imagen"), width=140, height=26, fg_color="#1a4a5a",
                      command=_cargar_imagen_cliente).pack(side="left", padx=2)
        ctk.CTkButton(f_btns_img, text=tr("✕ Quitar"), width=80, height=26, fg_color="#5a1a1a",
                      command=_quitar_imagen).pack(side="left", padx=2)

        # Campos del brief
        campos = {}
        for label, placeholder in [
            ("Tipo de proyecto", "ej: Logo, Banner, Producto, Editorial, Anuncio..."),
            ("Cliente / sector", "ej: Café orgánico, Marca de moda, App tech..."),
            ("Tono / estilo deseado", "ej: Minimalista elegante, Vibrante juvenil, Lujo discreto..."),
            ("Público objetivo", "ej: Mujeres 25-40 urbanas, Profesionales tech, Familia..."),
            ("Restricciones / keywords", "ej: Sin texto, paleta verde-marrón, formato vertical..."),
        ]:
            ctk.CTkLabel(vent, text=label, font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=20, pady=(4, 2))
            ent = ctk.CTkEntry(vent, placeholder_text=placeholder, width=560, height=28)
            ent.pack(padx=20)
            campos[label] = ent

        def _aplicar_plantilla(_v=None):
            sel = plantilla_var.get()
            if sel == "— Personalizada —":
                return
            datos = PLANTILLAS_BRIEF.get(sel, {})
            for k, ent in campos.items():
                ent.delete(0, "end")
                if datos.get(k):
                    ent.insert(0, datos[k])
        combo_plantilla.configure(command=_aplicar_plantilla)

        # ── Cargar último brief desde preferencias ──
        try:
            _prefs = self.app.store.cargar_preferencias() or {}
            ultimo = _prefs.get("modo_cliente_ultimo_brief") or {}
            for k, ent in campos.items():
                if ultimo.get(k):
                    ent.insert(0, ultimo[k])
        except Exception as _e:
            logger.debug(f"[silent] cargar último brief: {_e}")

        def _generar_propuestas():
            brief_dict = {k: v.get().strip() for k, v in campos.items()}
            if not any(brief_dict.values()):
                self.app.dialogs.set_estado("⚠️ Rellena al menos un campo del brief.", "#e67e22")
                return

            # Persistir último brief
            try:
                _p = self.app.store.cargar_preferencias() or {}
                _p["modo_cliente_ultimo_brief"] = brief_dict
                self.app.store.guardar_preferencias(_p)
            except Exception as _e:
                logger.debug(f"[silent] persistir brief: {_e}")

            brief = "\n".join([f"- {k}: {v or '(no especificado)'}"
                               for k, v in brief_dict.items()])

            # Si hay imagen analizada, añadirla al brief
            if cliente_state["descripcion"]:
                brief += (f"\n\n📎 IMAGEN DE REFERENCIA proporcionada por el cliente:\n"
                          f"{cliente_state['descripcion']}\n"
                          f"(Usa el estilo visual de esta imagen como guía estética)")

            vent.destroy()
            self._generar_propuestas_cliente(brief)

        ctk.CTkButton(vent, text=tr("✨ Generar 5 propuestas"), width=220, height=34,
                      fg_color="#1a7a3c",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=_generar_propuestas).pack(pady=15)

    def _generar_propuestas_cliente(self, brief):
        """Genera 5 propuestas basadas en un brief."""
        self.app.dialogs.set_estado("💼 Generando 5 propuestas profesionales...", "#f39c12")
        self.app.dialogs.toggle_botones(False)

        specs = self.app.get_current_model_specs()
        has_neg = specs.get("has_negative", True) if specs else True
        is_natural = specs.get("is_natural", False) if specs else False
        fmt = "lenguaje natural descriptivo en prosa" if is_natural else "tags con pesos (tag:1.2) separados por comas"
        neg_str = "Incluye también NEGATIVE PROMPT al final con tags negativos relevantes." if has_neg else "NO incluyas NEGATIVE PROMPT (este modelo no lo soporta)."

        peticion = (
            f"Eres un director creativo. Recibes este BRIEF de cliente y debes generar 5 PROPUESTAS de prompt distintas, profesionales y coherentes con el brief, pero con enfoques creativos diferentes.\n\n"
            f"BRIEF:\n{brief}\n\n"
            f"FORMATO DE LA SALIDA:\n"
            f"Para CADA propuesta, escribe EXACTAMENTE así (sin texto extra entre la etiqueta y POSITIVE):\n\n"
            f"=== PROPUESTA 1: [Nombre del enfoque] ===\n"
            f"POSITIVE PROMPT: [el prompt completo en {fmt}]\n"
            f"{('NEGATIVE PROMPT: [tags negativos]' if has_neg else '')}\n\n"
            f"=== PROPUESTA 2: [Nombre del enfoque] ===\n"
            f"POSITIVE PROMPT: ...\n"
            f"...etc hasta 5 propuestas\n\n"
            f"REGLAS:\n"
            f"- Las 5 propuestas son ENFOQUES DIFERENTES pero todas adecuadas al brief.\n"
            f"- {neg_str}\n"
            f"- NO incluyas explicaciones entre el título y POSITIVE PROMPT.\n"
            f"- El POSITIVE PROMPT debe ser DIRECTAMENTE COPIABLE para usar en SeaArt/Midjourney/etc."
        )

        def _worker():
            try:
                resp = self.app.deepseek.generar(peticion, temperature=0.7, max_tokens=4000)
                resp = limpiar_marcadores(resp)

                # ── Parseo específico de "=== PROPUESTA N: Nombre === ... ──
                # Captura: (numero, nombre, contenido) por cada bloque
                import re
                # Permitimos ===, ##, **, o nada como delimitador alrededor
                patron_propuesta = re.compile(
                    r'(?:^|\n)\s*(?:===|\*\*|##)?\s*PROPUESTA\s+(\d+)\s*:?\s*([^\n=*#]*?)\s*(?:===|\*\*|##)?\s*\n'
                    r'(.*?)(?=(?:\n\s*(?:===|\*\*|##)?\s*PROPUESTA\s+\d+)|\Z)',
                    re.DOTALL | re.IGNORECASE,
                )
                propuestas: list[dict] = []
                for m in patron_propuesta.finditer(resp):
                    num = m.group(1).strip()
                    nombre = (m.group(2) or "").strip(" :-—–[]")
                    contenido = m.group(3).strip()
                    # Extraer POSITIVE / NEGATIVE del contenido
                    mp = re.search(r'POSITIVE\s+PROMPT\s*:?\s*(.+?)(?=\n\s*NEGATIVE\s+PROMPT\s*:|\Z)',
                                   contenido, re.DOTALL | re.IGNORECASE)
                    mn = re.search(r'NEGATIVE\s+PROMPT\s*:?\s*(.+?)\Z',
                                   contenido, re.DOTALL | re.IGNORECASE)
                    pos_txt = (mp.group(1).strip() if mp else contenido).strip().rstrip("=").strip()
                    neg_txt = (mn.group(1).strip().rstrip("=").strip() if mn else "")
                    propuestas.append({
                        "num": num,
                        "nombre": nombre or f"Propuesta {num}",
                        "positive": pos_txt,
                        "negative": neg_txt,
                    })

                # Fallback: si el LLM no respetó el formato, usar el parser legacy
                if not propuestas:
                    bloques = self.app._parsear_bloques_numerados(resp, n_esperado=5)
                    for i, b in enumerate(bloques[:5], 1):
                        mp = re.search(r'POSITIVE\s+PROMPT\s*:?\s*(.+?)(?=\n\s*NEGATIVE|\Z)',
                                       b, re.DOTALL | re.IGNORECASE)
                        mn = re.search(r'NEGATIVE\s+PROMPT\s*:?\s*(.+?)\Z',
                                       b, re.DOTALL | re.IGNORECASE)
                        propuestas.append({
                            "num": str(i),
                            "nombre": f"Propuesta {i}",
                            "positive": mp.group(1).strip() if mp else b,
                            "negative": mn.group(1).strip() if mn else "",
                        })

                def _mostrar():
                    self._abrir_comparador_propuestas(propuestas[:5], brief)
                    self.app.dialogs.set_estado(
                        f"💼 {len(propuestas)} propuestas profesionales generadas",
                        "#2ecc71",
                    )
                    self.app.dialogs.toggle_botones(True)
                    self.app.dialogs._sonar_completado()
                self.app.after(0, _mostrar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _abrir_comparador_propuestas(self, propuestas, brief=""):
        """Muestra propuestas como cards interactivos.

        Args:
            propuestas: lista de dicts {num, nombre, positive, negative}
                (formato nuevo). Si llega como lista de strings (formato
                legacy), se reparsean al vuelo.
            brief: texto del brief original (para mostrar en cabecera y
                guardar con la propuesta como favorito).
        """
        import re as _re
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        # Normalizar: aceptar list[str] legacy convirtiendo a dicts
        propuestas_norm: list[dict] = []
        for i, p in enumerate(propuestas, 1):
            if isinstance(p, dict):
                propuestas_norm.append(p)
            else:
                # Legacy: string. Extraer positive/negative al vuelo.
                texto = str(p)
                mp = _re.search(r'POSITIVE\s+PROMPT\s*:?\s*(.+?)(?=\n\s*NEGATIVE|\Z)',
                                texto, _re.DOTALL | _re.IGNORECASE)
                mn = _re.search(r'NEGATIVE\s+PROMPT\s*:?\s*(.+?)\Z',
                                texto, _re.DOTALL | _re.IGNORECASE)
                propuestas_norm.append({
                    "num": str(i),
                    "nombre": f"Propuesta {i}",
                    "positive": mp.group(1).strip() if mp else texto,
                    "negative": mn.group(1).strip() if mn else "",
                })

        vent = GPromptWindow(self.app)
        vent.title("💼 Propuestas profesionales")
        vent.geometry("900x720")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=f"💼 {len(propuestas_norm)} Propuestas para tu brief",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 2))
        ctk.CTkLabel(vent, text=f"Brief: {brief[:120]}{'...' if len(brief) > 120 else ''}",
                     font=ctk.CTkFont(size=9), text_color=c["muted_text"], wraplength=840
                     ).pack(pady=(0, 8))

        cards_frame = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        cards_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        col_colors = ["#1a7a3c", "#1a4a7a", "#7a1a4a", "#7a4a1a", "#1a5a7a"]

        for idx, prop in enumerate(propuestas_norm):
            num = prop.get("num") or str(idx + 1)
            nombre_corto = prop.get("nombre") or f"Propuesta {num}"
            titulo = f"Propuesta {num}: {nombre_corto}" if nombre_corto != f"Propuesta {num}" else nombre_corto
            positivo = prop.get("positive", "")
            negativo = prop.get("negative", "")
            preview = positivo[:150].replace("\n", " ") + ("..." if len(positivo) > 150 else "")

            card = ctk.CTkFrame(cards_frame, fg_color="#111820", corner_radius=10,
                                border_color=col_colors[idx % len(col_colors)], border_width=1)
            card.pack(fill="x", pady=6, padx=4)

            hdr = ctk.CTkFrame(card, fg_color="transparent")
            hdr.pack(fill="x", padx=12, pady=(8, 4))
            emoji = emojis[idx] if idx < len(emojis) else "•"
            ctk.CTkLabel(hdr, text=f"{emoji}  {titulo}",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=col_colors[idx % len(col_colors)]).pack(side="left")

            desc_row = ctk.CTkFrame(card, fg_color="transparent")
            desc_row.pack(fill="x", padx=12, pady=(0, 4))
            ctk.CTkLabel(desc_row, text=preview, font=ctk.CTkFont(size=10),
                         text_color="#888888", wraplength=820, anchor="w"
                         ).pack(anchor="w")

            if negativo:
                neg_preview = negativo[:100].replace("\n", " ")
                ctk.CTkLabel(desc_row, text=f"🔴 NEG: {neg_preview}…",
                             font=ctk.CTkFont(size=9), text_color="#ef4444",
                             anchor="w").pack(anchor="w", pady=(2, 0))

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=12, pady=(0, 8))

            def _usar(p=positivo, n=negativo, nom=titulo):
                completo = f"POSITIVE PROMPT: {p}\n" + (f"NEGATIVE PROMPT: {n}" if n else "")
                self.app.dialogs.actualizar_salida(completo)
                self.app.dialogs.set_estado(f"✅ Propuesta '{nom}' aplicada al prompt", "#2ecc71")
                vent.destroy()

            def _copiar(p=positivo, n=negativo, nom=titulo):
                completo = f"POSITIVE PROMPT: {p}\n" + (f"NEGATIVE PROMPT: {n}" if n else "")
                pyperclip.copy(completo)
                self.app.dialogs.set_estado(f"📋 Propuesta '{nom}' copiada al portapapeles", "#2ecc71")

            def _guardar_prop(nom=titulo, p=positivo, neg=negativo):
                """Guarda como FAVORITO con marca de origen. Antes intentaba
                guardar en self.app.store.propuestas que no existe + llamaba a
                self.app.store.guardar() que no existe → crasheaba."""
                completo = f"POSITIVE PROMPT: {p}"
                if neg:
                    completo += f"\nNEGATIVE PROMPT: {neg}"
                try:
                    self.app.store.agregar_favorito({
                        "fecha":      datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "modo":       self.app.modo_var.get() if hasattr(self.app, "modo_var") else "imagen",
                        "plataforma": self.app.plataforma_var.get() if hasattr(self.app, "plataforma_var") else "",
                        "estilos":    "",
                        "ratio":      self.app.ratio_var.get() if hasattr(self.app, "ratio_var") else "",
                        "nsfw":       False,
                        "personaje":  "",
                        "lora":       "",
                        "destino":    "",
                        "brief":      brief[:200],
                        "origen":     "modo_cliente",
                        "nombre":     nom,
                        "contenido":  completo,
                    })
                    self.app.dialogs.set_estado(f"💾 Propuesta '{nom}' guardada en Favoritos", "#2ecc71")
                except Exception as e:
                    self.app.dialogs.set_estado(f"❌ No se pudo guardar: {e}", "#e74c3c")

            ctk.CTkButton(btn_row, text=tr("✅ Usar propuesta"), width=150, height=30, fg_color="#1a7a3c",
                          font=ctk.CTkFont(size=10, weight="bold"), command=_usar
                          ).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text=tr("📋 Copiar"), width=100, height=30, fg_color="#1a4a5a",
                          font=ctk.CTkFont(size=10), command=_copiar
                          ).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text=tr("💾 Guardar"), width=100, height=30, fg_color="#4a1a6a",
                          font=ctk.CTkFont(size=10), command=_guardar_prop
                          ).pack(side="left", padx=2)
            ctk.CTkLabel(btn_row, text=f"   {len(positivo)} chars",
                         font=ctk.CTkFont(size=9), text_color="#666666").pack(side="left", padx=(4, 0))

        ctk.CTkButton(vent, text=tr("Cerrar"), width=140, height=30, fg_color="#475569",
                      command=vent.destroy).pack(pady=(0, 8))

    def _cmd_companero_moodboard(self):
        """Sube imágenes y la IA detecta el estilo común.

        v1.1: usa imagen cargada, barra de progreso, preview thumbnails,
        guarda estilo detectado y permite añadir más imágenes.
        """
        from tkinter import filedialog

        archivos_seleccionados = []
        progreso_state = {"n": 0, "total": 1}

        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self.app)
        vent.title("🎭 Moodboard — Estilo común")
        vent.geometry("720x680")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("🎭 Moodboard — Detecta el estilo común de tus imágenes"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text=tr("Añade imágenes con estilo similar (mínimo 2). Usa la imagen ya cargada como referencia."),
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 6))

        # ── Imagen ya cargada ──
        if self.app.imagen_cargada:
            frame_ref = ctk.CTkFrame(vent, fg_color=c["fg_dark"], corner_radius=6)
            frame_ref.pack(fill="x", padx=15, pady=(0, 6))
            hdr_ref = ctk.CTkFrame(frame_ref, fg_color="transparent")
            hdr_ref.pack(fill="x", padx=10, pady=(6, 2))
            ctk.CTkLabel(hdr_ref, text=tr("🖼 Imagen de referencia ya cargada"),
                          font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
            ctk.CTkLabel(hdr_ref, text=tr("Se usará automáticamente"),
                          font=ctk.CTkFont(size=9), text_color="#2ecc71").pack(side="left", padx=(6, 0))
            preview_lbl = ctk.CTkLabel(frame_ref, text="")
            preview_lbl.pack(padx=10, pady=(0, 4))

        # ── Selector de archivos adicionales ──
        frame_arch = ctk.CTkFrame(vent, fg_color=c["fg_dark"], corner_radius=6)
        frame_arch.pack(fill="x", padx=15, pady=(0, 6))

        archivos_state = {"rutas": list(archivos_seleccionados)}

        lbl_count = ctk.CTkLabel(frame_arch, text=tr("0 imágenes seleccionadas"),
                                 font=ctk.CTkFont(size=10), text_color=c["muted_text"])
        lbl_count.pack(anchor="w", padx=10, pady=(6, 2))

        thumbs_area = ctk.CTkFrame(frame_arch, fg_color="transparent")
        thumbs_area.pack(fill="x", padx=10, pady=(0, 4))

        def _actualizar_thumbs():
            for w in thumbs_area.winfo_children():
                w.destroy()
            n = len(archivos_state['rutas'])
            sufijo = " (máx 5 procesadas)" if n > 5 else ""
            lbl_count.configure(text=f"{n} imágenes seleccionadas{sufijo}")
            for i, ruta in enumerate(archivos_state["rutas"][:8]):
                try:
                    from PIL import Image as _PIL
                    thumb = _PIL.Image.open(ruta).copy()
                    thumb.thumbnail((60, 60))
                    img_tk = ctk.CTkImage(thumb, size=(60, 60))

                    # Frame contenedor por miniatura para superponer botón ❌
                    cont = ctk.CTkFrame(thumbs_area, fg_color="transparent",
                                        width=64, height=70)
                    cont.pack(side="left", padx=2)
                    cont.pack_propagate(False)
                    lbl = ctk.CTkLabel(cont, image=img_tk, text="")
                    lbl.place(x=0, y=4)

                    def _quitar(idx=i):
                        try:
                            archivos_state["rutas"].pop(idx)
                            _actualizar_thumbs()
                        except Exception as e:
                            logger.debug(f"_quitar thumb: {e}")

                    btn_x = ctk.CTkButton(
                        cont, text="✕", width=18, height=18,
                        fg_color="#7a1a1a", hover_color="#5a0f0f",
                        font=ctk.CTkFont(size=9, weight="bold"),
                        corner_radius=9, border_width=0,
                        command=_quitar,
                    )
                    btn_x.place(x=44, y=0)
                except Exception as _e:
                    logger.debug(f"[silent] {_e}")
            if n > 8:
                ctk.CTkLabel(thumbs_area,
                             text=f"+{n - 8} más",
                             font=ctk.CTkFont(size=10),
                             text_color=c["muted_text"]).pack(side="left", padx=4)
        def _anadir_mas():
            nuevas = filedialog.askopenfilenames(
                title="Selecciona más imágenes",
                filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp")]
            )
            if not nuevas:
                return
            # Validar cada archivo antes de añadirlo: las corruptas no entran
            # silenciosamente, sino que se reportan al usuario.
            import os

            from PIL import Image as _PIL_val
            from PIL import UnidentifiedImageError
            buenas, fallos = [], []
            for ruta in nuevas:
                try:
                    with _PIL_val.open(ruta) as _im:
                        _im.verify()
                    buenas.append(ruta)
                except (UnidentifiedImageError, OSError, Exception) as _e:
                    fallos.append((os.path.basename(ruta), str(_e)[:60]))
                    logger.debug(f"moodboard: imagen rechazada {ruta}: {_e}")
            if buenas:
                archivos_state["rutas"].extend(buenas)
                _actualizar_thumbs()
            if fallos:
                detalle = "\n".join(f"• {n}: {err}" for n, err in fallos[:5])
                mas = f"\n+{len(fallos)-5} más" if len(fallos) > 5 else ""
                from tkinter import messagebox as _mb
                _mb.showwarning(
                    "Imágenes rechazadas",
                    f"{len(fallos)} imagen(es) no se pudieron leer:\n\n{detalle}{mas}",
                    parent=vent,
                )

        def _limpiar():
            archivos_state["rutas"] = []
            _actualizar_thumbs()

        btn_row = ctk.CTkFrame(frame_arch, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkButton(btn_row, text=tr("➕ Añadir imágenes"), width=140, height=26, fg_color="#1a4a5a",
                      command=_anadir_mas).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text=tr("🗑 Limpiar"), width=100, height=26,
                      command=_limpiar).pack(side="left", padx=2)

        # ── Barra de progreso ──
        progress_frame = ctk.CTkFrame(vent, fg_color="transparent")
        progress_frame.pack(fill="x", padx=15, pady=(0, 4))
        lbl_prog = ctk.CTkLabel(progress_frame, text="", font=ctk.CTkFont(size=10),
                                 text_color=c["muted_text"])
        lbl_prog.pack(anchor="w")
        progress_bar = ctk.CTkProgressBar(progress_frame, height=8)
        progress_bar.pack(fill="x", pady=(2, 0))
        progress_bar.set(0)
        progress_bar.pack_forget()
        lbl_prog.pack_forget()

        def _ejecutar_moodboard():
            # Construir lista de imágenes. Si alguna falla al abrir (corrupta o
            # ruta inválida) lo reportamos en vez de tragarlo silenciosamente.
            todas_imagenes = []
            if self.app.imagen_cargada:
                todas_imagenes.append(self.app.imagen_cargada)
            fallos_open = []
            if archivos_state["rutas"]:
                import os

                from PIL import Image as _PIL2
                from PIL import UnidentifiedImageError
                for ruta in archivos_state["rutas"][:5]:
                    try:
                        todas_imagenes.append(_PIL2.open(ruta))
                    except (UnidentifiedImageError, OSError, Exception) as _e:
                        fallos_open.append((os.path.basename(ruta), str(_e)[:60]))
                        logger.debug(f"moodboard open {ruta}: {_e}")
            if fallos_open:
                detalle = "\n".join(f"• {n}: {err}" for n, err in fallos_open[:5])
                from tkinter import messagebox as _mb
                _mb.showwarning(
                    "Imágenes no leídas",
                    f"{len(fallos_open)} imagen(es) no se pudieron abrir y se "
                    f"omitirán del análisis:\n\n{detalle}",
                    parent=vent,
                )
            total_imgs = len(todas_imagenes)
            if total_imgs < 2:
                return self.app.dialogs.set_estado("⚠️ Necesitas al menos 2 imágenes (usa la cargada o añade más).", "#e67e22")

            self.app.dialogs.set_estado(f"🎭 Analizando {total_imgs} imágenes...", "#f39c12")
            self.app.dialogs.toggle_botones(False)
            lbl_prog.pack(anchor="w")
            progress_bar.pack(fill="x", pady=(2, 0))
            lbl_prog.configure(text=f"Analizando imagen 1/{total_imgs}...")
            progress_bar.set(0)

            def _trabajar():
                try:
                    descripciones = []
                    for i, img in enumerate(todas_imagenes):
                        progreso_state["n"] = i + 1
                        self.app.after(0, lambda n=i+1, t=total_imgs:
                                   (lbl_prog.configure(text=f"Analizando imagen {n}/{t}..."),
                                    progress_bar.set(n / t)))
                        desc, _ = self.app.vision.describir(img, "imagen", lambda m: None)
                        descripciones.append(desc)

                    self.app.after(0, lambda: lbl_prog.configure(text=tr("Extrayendo estilo común...")))
                    peticion = (
                        f"Has analizado {len(descripciones)} imágenes con estilo similar. "
                        f"Extrae el ESTILO COMÚN entre ellas.\n\n"
                        + "\n---\n".join([f"IMAGEN {i+1}:\n{d}" for i, d in enumerate(descripciones)])
                        + "\n\nRESPONDE EN ESPAÑOL con este formato:\n\n"
                        + "🎨 ESTILO DETECTADO: [nombre del estilo común]\n\n"
                        + "📐 ELEMENTOS COMUNES:\n   - [3-5 elementos compartidos]\n\n"
                        + "🎨 PALETA: [colores predominantes]\n\n"
                        + "💡 ILUMINACIÓN: [tipo de luz común]\n\n"
                        + "🎬 PROMPT TEMPLATE EN INGLÉS (para generar imágenes en este mismo estilo):\n[prompt completo]"
                    )
                    resp = self.app.deepseek.generar(peticion, temperature=0.4, max_tokens=2000)
                    resp = limpiar_marcadores(resp)

                    def _mostrar():
                        lbl_prog.pack_forget()
                        progress_bar.pack_forget()
                        vent2 = GPromptWindow(self.app)
                        vent2.title("🎭 Estilo común detectado")
                        vent2.geometry("720x650")
                        vent2.transient(self.app)
                        ctk.CTkLabel(vent2, text=f"🎭 Estilo detectado en {len(descripciones)} imágenes",
                                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 8))

                        txt = ctk.CTkTextbox(vent2, font=ctk.CTkFont(size=11), wrap="word")
                        txt.pack(fill="both", expand=True, padx=15, pady=(0, 5))
                        txt.insert("1.0", resp)
                        txt.configure(state="disabled")

                        btn_row2 = ctk.CTkFrame(vent2, fg_color="transparent")
                        btn_row2.pack(pady=10)

                        def _aplicar_template():
                            import re
                            m = re.search(r'PROMPT\s+TEMPLATE[^:]*:\s*(.+?)(?=\Z)', resp, re.DOTALL | re.IGNORECASE)
                            if m:
                                template = m.group(1).strip()
                                self.app.dialogs.actualizar_salida(template)
                                vent2.destroy()
                                self.app.dialogs.set_estado("🎭 Template aplicado", "#2ecc71")

                        def _guardar_estilo():
                            import re as _re
                            from tkinter import simpledialog
                            prefs_g = self.app.store.cargar_preferencias()
                            estilos_g = prefs_g.get("estilos_moodboard", []) or []
                            if not isinstance(estilos_g, list):
                                estilos_g = []
                            sugerencia = f"Estilo Moodboard {len(estilos_g) + 1}"
                            nombre = simpledialog.askstring(
                                "💾 Guardar estilo",
                                "Nombre del estilo (lo verás en 📚 Mis estilos):",
                                initialvalue=sugerencia,
                                parent=vent2,
                            )
                            if not nombre:
                                return
                            nombre = nombre.strip()
                            # Extraer template inglés para poder reaplicarlo después
                            m_t = _re.search(
                                r'PROMPT\s+TEMPLATE[^:]*:\s*(.+?)(?=\Z)',
                                resp, _re.DOTALL | _re.IGNORECASE,
                            )
                            template = m_t.group(1).strip() if m_t else ""
                            estilos_g.append({
                                "nombre": nombre,
                                "descripcion": resp,
                                "template": template,
                                "fecha": datetime.datetime.now().strftime("%Y-%m-%d"),
                                "n_imagenes": len(descripciones),
                            })
                            prefs_g["estilos_moodboard"] = estilos_g
                            self.app.store.guardar_preferencias(prefs_g)
                            self.app.dialogs.set_estado(f"💾 Estilo '{nombre}' guardado en biblioteca", "#2ecc71")

                        ctk.CTkButton(btn_row2, text=tr("✅ Aplicar template"), width=140, height=28,
                                      fg_color="#1a7a3c", command=_aplicar_template).pack(side="left", padx=4)
                        ctk.CTkButton(btn_row2, text=tr("💾 Guardar estilo"), width=140, height=28, fg_color="#4a1a6a",
                                      command=_guardar_estilo).pack(side="left", padx=4)
                        ctk.CTkButton(btn_row2, text=tr("📋 Copiar análisis"), width=140, height=28,
                                      command=lambda: pyperclip.copy(resp)).pack(side="left", padx=4)

                        self.app.dialogs.toggle_botones(True)
                        self.app.dialogs.set_estado("🎭 Estilo común detectado", "#2ecc71")
                    self.app.after(0, _mostrar)
                except Exception as e:
                    self.app.after(0, lambda: lbl_prog.pack_forget())
                    self.app.after(0, lambda: progress_bar.pack_forget())
                    self.app.after(0, lambda e=e: self.app.dialogs.set_estado(f"❌ Error: {e}", "#e74c3c"))
                    self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

            self.app._executor.submit(_trabajar).add_done_callback(log_future_exc)

        botones_finales = ctk.CTkFrame(vent, fg_color="transparent")
        botones_finales.pack(pady=8)
        ctk.CTkButton(botones_finales, text=tr("🎭 Analizar estilo común"),
                      width=240, height=38,
                      fg_color="#a64aa6", hover_color="#7a2a7a",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      text_color="#ffffff",
                      command=_ejecutar_moodboard).pack(side="left", padx=4)
        ctk.CTkButton(botones_finales, text=tr("📚 Mis estilos"),
                      width=140, height=38,
                      fg_color="#4a1a6a", hover_color="#3a1050",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      text_color="#ffffff",
                      command=lambda: self._abrir_biblioteca_estilos_moodboard(vent)
                      ).pack(side="left", padx=4)

    def _abrir_biblioteca_estilos_moodboard(self, parent_window=None):
        """Biblioteca de estilos detectados con moodboard: aplicar / ver / borrar."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        win = GPromptWindow(parent_window or self.app)
        win.title("📚 Mis estilos de moodboard")
        win.geometry("640x560")
        win.transient(parent_window or self.app)

        ctk.CTkLabel(win, text=tr("📚 Estilos detectados con moodboard"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4))
        cont_var = ctk.StringVar(value="")
        ctk.CTkLabel(win, textvariable=cont_var,
                     font=ctk.CTkFont(size=10),
                     text_color=c["muted_text"]).pack(pady=(0, 6))

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        def _refrescar():
            for w in scroll.winfo_children():
                w.destroy()
            prefs_l = self.app.store.cargar_preferencias()
            estilos = prefs_l.get("estilos_moodboard", []) or []
            cont_var.set(f"{len(estilos)} estilo(s) guardado(s)")
            if not estilos:
                ctk.CTkLabel(
                    scroll,
                    text="No has guardado ningún estilo todavía.\n"
                         "Analiza un moodboard y pulsa '💾 Guardar estilo'.",
                    text_color=c["muted_text"], justify="center",
                ).pack(pady=30)
                return
            for idx, est in enumerate(estilos):
                card = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=8)
                card.pack(fill="x", pady=4)
                hdr = ctk.CTkFrame(card, fg_color="transparent")
                hdr.pack(fill="x", padx=10, pady=(6, 2))
                ctk.CTkLabel(hdr, text=est.get("nombre", f"Estilo {idx+1}"),
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=c["hdr_text"]).pack(side="left")
                meta = f"  · {est.get('fecha','')}"
                if est.get("n_imagenes"):
                    meta += f"  · {est['n_imagenes']} img"
                ctk.CTkLabel(hdr, text=meta,
                             font=ctk.CTkFont(size=9),
                             text_color=c["muted_text"]).pack(side="left")

                tiene_template = bool(est.get("template", "").strip())

                def _aplicar(e=est):
                    tpl = e.get("template", "").strip()
                    if not tpl:
                        self.app.dialogs.set_estado("⚠️ Este estilo no tiene template aplicable",
                                        "#e67e22")
                        return
                    self.app.dialogs.actualizar_salida(tpl)
                    self.app.dialogs.set_estado(f"🎭 Estilo '{e.get('nombre','')}' aplicado",
                                    "#2ecc71")

                def _ver(e=est):
                    ver = GPromptWindow(win)
                    ver.title(f"🎭 {e.get('nombre','Estilo')}")
                    ver.geometry("680x500")
                    ver.transient(win)
                    txt = ctk.CTkTextbox(ver, font=ctk.CTkFont(size=11), wrap="word")
                    txt.pack(fill="both", expand=True, padx=10, pady=10)
                    txt.insert("1.0", e.get("descripcion", ""))
                    txt.configure(state="disabled")
                    ctk.CTkButton(ver, text=tr("Cerrar"), command=ver.destroy
                                  ).pack(pady=8)

                def _borrar(i=idx, nombre=est.get("nombre","?")):
                    from tkinter import messagebox as _mb
                    if not _mb.askyesno("Confirmar",
                                        f"¿Borrar estilo '{nombre}'?",
                                        parent=win):
                        return
                    prefs_b = self.app.store.cargar_preferencias()
                    lst = prefs_b.get("estilos_moodboard", []) or []
                    if 0 <= i < len(lst):
                        lst.pop(i)
                        prefs_b["estilos_moodboard"] = lst
                        self.app.store.guardar_preferencias(prefs_b)
                    _refrescar()

                btn_row = ctk.CTkFrame(card, fg_color="transparent")
                btn_row.pack(fill="x", padx=10, pady=(4, 8))
                ctk.CTkButton(btn_row, text=tr("✅ Aplicar template"),
                              width=160, height=26,
                              fg_color="#1a7a3c" if tiene_template else c["fg_dark"],
                              state="normal" if tiene_template else "disabled",
                              font=ctk.CTkFont(size=10),
                              command=_aplicar).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text=tr("👁 Ver análisis"),
                              width=120, height=26,
                              font=ctk.CTkFont(size=10),
                              command=_ver).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text="🗑", width=40, height=26,
                              fg_color="#7a1a1a", hover_color="#5a0f0f",
                              command=_borrar).pack(side="right", padx=2)

        _refrescar()
        ctk.CTkButton(win, text=tr("Cerrar"), width=110, height=28,
                      command=win.destroy).pack(pady=(0, 12))
