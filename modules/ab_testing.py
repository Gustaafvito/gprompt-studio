"""A/B Testing 2x2 + Comparador de modelos.

Dos features para evaluar variaciones de un prompt:

  • A/B Testing 2x2  — genera 4 variantes del mismo prompt variando 1-2
    dimensiones a elegir (iluminación, mood, ángulo, estilo, paleta,
    detalle). Útil para encontrar la mejor versión sin teclear cada
    variación a mano.

  • Comparar modelos — toma una idea y la procesa por N modelos (2-5)
    en paralelo, mostrando los prompts adaptados a las particularidades
    de cada modelo lado a lado.

Métodos:
  • _cmd_ab_testing           — modal de configuración (qué dimensiones)
  • _ab_lanzar                — worker que genera las 4 variantes
  • _mostrar_ab_grid          — grid 2x2 de resultados
  • _cmd_comparar_modelos     — modal de selección de modelos
  • _abrir_ventana_comparacion — ventana con N cards generándose en
                                 paralelo

Dependencias self (provistas por ArquitectoApp):
  txt_idea, modo_var, deepseek, after, set_estado, toggle_botones,
  actualizar_salida, estilos_texto, get_current_model_specs,
  combo_modelo_imagen, combo_modelo_video, combo_modelo_audio,
  _on_modelo_imagen_cambio, _sesion_log.
"""
import logging
import re as _re
import threading
from tkinter import messagebox

import customtkinter as ctk
import pyperclip

from config import (
    MODELOS_AUDIO_FLAT,
    MODELOS_IMAGEN_FLAT,
    MODELOS_VIDEO_FLAT,
    get_audio_model_specs,
    get_image_model_specs,
    get_model_specs,
)
from config import get_theme_colors as _get_tc
from modules.gprompt_window import GPromptWindow
from workers import limpiar_marcadores

logger = logging.getLogger(__name__)


class AbTestingMixin:

    # Dimensiones disponibles en A/B Testing 2x2.
    # Cada dimensión tiene 4 valores; se toman :4 (1 dim) o :2 + :2 (2 dims).
    AB_DIMENSIONES = {
        "iluminación": ["soft natural light", "harsh dramatic lighting", "neon glow", "golden hour sunset"],
        "mood": ["serene and peaceful", "tense and ominous", "joyful and energetic", "melancholic and quiet"],
        "ángulo": ["close-up portrait", "wide establishing shot", "low-angle hero shot", "overhead bird's-eye"],
        "estilo artístico": ["photorealistic", "oil painting style", "cyberpunk aesthetic", "watercolor illustration"],
        "paleta de color": ["warm orange and red tones", "cool blue and teal palette", "monochrome black and white", "pastel pink and lavender"],
        "detalle": ["minimalist clean composition", "highly detailed intricate", "abstract impressionist", "hyperrealistic ultra-detail"],
    }

    def _cmd_ab_testing(self):
        """A/B testing 2x2: configura dimensiones a variar y genera 4 variantes."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea:
            self.set_estado("⚠️ Escribe una idea primero", "#e67e22")
            return
        try:
            self._sesion_log("🧪 A/B Testing: abrió configuración 2x2")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        # Ventana de configuración
        cfg = GPromptWindow(self)
        cfg.title("🧪 A/B Testing 2x2")
        cfg.geometry("520x520")
        cfg.transient(self)
        cfg.grab_set()

        ctk.CTkLabel(cfg, text="🧪 A/B Testing 2x2",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 4))
        ctk.CTkLabel(cfg,
                     text="Marca 1 o 2 dimensiones a variar.\nSe generarán 4 prompts variando solo esas.",
                     font=ctk.CTkFont(size=10), text_color="#888",
                     justify="center").pack(pady=(0, 10))

        # Checkboxes para cada dimensión
        dim_vars = {}
        scroll = ctk.CTkScrollableFrame(cfg, fg_color="transparent", height=300)
        scroll.pack(fill="both", expand=True, padx=20, pady=5)

        # Contador y función para actualizar estado
        lbl_contador = ctk.CTkLabel(cfg, text="Seleccionadas: 0 (máx 2)",
                                    font=ctk.CTkFont(size=10), text_color="#888")
        lbl_contador.pack(pady=(0, 5))

        # Refs a los checkboxes para deshabilitar visualmente los no
        # seleccionados cuando ya hay 2 marcados.
        dim_checks = {}

        def _actualizar_checkboxes():
            total = sum(1 for v in dim_vars.values() if v.get())
            lbl_contador.configure(
                text=f"Seleccionadas: {total} (máx 2)",
                text_color="#2ecc71" if 1 <= total <= 2 else "#e67e22",
            )
            # Deshabilitar visualmente los no seleccionados si ya hay 2
            for nombre, var in dim_vars.items():
                cb = dim_checks.get(nombre)
                if not cb:
                    continue
                if total >= 2 and not var.get():
                    cb.configure(state="disabled")
                else:
                    cb.configure(state="normal")

        for nombre, valores in self.AB_DIMENSIONES.items():
            var = ctk.BooleanVar(value=False)
            dim_vars[nombre] = var
            var.trace_add("write", lambda *a: _actualizar_checkboxes())
            row = ctk.CTkFrame(scroll, fg_color=c["fg_dark"], corner_radius=6)
            row.pack(fill="x", pady=2)
            cb = ctk.CTkCheckBox(row, text=f"  {nombre}", variable=var,
                                  font=ctk.CTkFont(size=11))
            cb.pack(side="left", padx=10, pady=6)
            dim_checks[nombre] = cb
            ctk.CTkLabel(row, text=f"  ej: {valores[0]}",
                         font=ctk.CTkFont(size=9, slant="italic"),
                         text_color="#666").pack(side="left", padx=4)

        def _generar():
            sel = [n for n, v in dim_vars.items() if v.get()]
            if not sel:
                messagebox.showwarning("Sin selección", "Marca al menos 1 dimensión a variar.", parent=cfg)
                return
            if len(sel) > 2:
                messagebox.showwarning("Demasiadas", "Marca como mucho 2 dimensiones (4 combinaciones).", parent=cfg)
                return
            cfg.destroy()
            self._ab_lanzar(idea, sel)

        btn_row = ctk.CTkFrame(cfg, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(5, 15))
        ctk.CTkButton(btn_row, text="🧪 Generar 4 variantes", width=200, height=36,
                      fg_color="#1a8a3c", hover_color="#127a30",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=_generar).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Cancelar", width=100, height=36,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                      command=cfg.destroy).pack(side="right", padx=4)

    def _ab_lanzar(self, idea_base, dimensiones):
        """Genera las 4 combinaciones con el LLM y las muestra en grid 2x2."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)

        # Combinar valores de las dimensiones seleccionadas
        if len(dimensiones) == 1:
            valores = self.AB_DIMENSIONES[dimensiones[0]]
            combos = [(dimensiones[0], v) for v in valores[:4]]
        else:
            d1, d2 = dimensiones
            v1 = self.AB_DIMENSIONES[d1][:2]
            v2 = self.AB_DIMENSIONES[d2][:2]
            combos = []
            for a in v1:
                for b in v2:
                    combos.append([(d1, a), (d2, b)])

        # Obtener specs del modelo actual
        specs = self.get_current_model_specs() or {}
        max_chars = specs.get("max_chars", 1500)
        has_neg = specs.get("has_negative", True)
        is_natural = specs.get("is_natural", False)
        fmt = "lenguaje natural descriptivo" if is_natural else "tags con pesos (tag:1.2)"
        neg_str = "Genera POSITIVE y NEGATIVE." if has_neg else "No generes NEGATIVE."

        self.set_estado("🧪 Generando 4 variantes con IA...", "#3498db")
        self.toggle_botones(False)

        def _generar():
            prompts_generados = []
            for combo in combos[:4]:
                if isinstance(combo, tuple):
                    dim_name, dim_val = combo
                    variacion = f"Cambia {dim_name} a: {dim_val}"
                    etiqueta = f"{dim_name}: {dim_val}"
                else:
                    cambios = ", ".join(f"{d}: {v}" for d, v in combo)
                    variacion = f"Cambia: {cambios}"
                    etiqueta = "  ·  ".join(f"{d}: {v}" for d, v in combo)

                peticion = (
                    "Genera un prompt profesional para esta idea:\n\n"
                    f"IDEA ORIGINAL: {idea_base}\n"
                    f"VARIACIÓN APLICAR: {variacion}\n\n"
                    "REGLAS:\n"
                    "- Mantén la idea original pero aplica la variación especificada\n"
                    f"- Formato: {fmt}\n"
                    "- Añade estilos y calidad profesional\n"
                    f"- Límite: {max_chars} caracteres\n"
                    f"- {neg_str}\n\n"
                    f"Estilos activos: {self.estilos_texto()}\n\n"
                    "Responde SOLO con el prompt."
                )

                try:
                    resp = self.deepseek.generar(peticion, temperature=0.7, max_tokens=1500)
                    resp = limpiar_marcadores(resp)
                    if not has_neg:
                        resp = _re.sub(r'\n?\s*NEGATIVE\s+PROMPT\s*:.*?$', '', resp, flags=_re.DOTALL | _re.IGNORECASE).strip()
                    prompts_generados.append((etiqueta, resp))
                except Exception as e:
                    prompts_generados.append((etiqueta, f"❌ Error: {e}"))

            self.after(0, lambda: self._mostrar_ab_grid(idea_base, dimensiones, prompts_generados, is_lt, c))

        threading.Thread(target=_generar, daemon=True).start()

    def _mostrar_ab_grid(self, idea_base, dimensiones, prompts_generados, is_lt, c):
        """Muestra la grid de resultados."""
        v = GPromptWindow(self)
        v.title(f"🧪 A/B Testing — {' + '.join(dimensiones)}")
        v.geometry("1100x720")
        v.transient(self)

        ctk.CTkLabel(v, text=f"🧪 4 variantes de: {idea_base[:60]}{'…' if len(idea_base) > 60 else ''}",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(12, 4))
        ctk.CTkLabel(v, text=f"Variando: {' + '.join(dimensiones)}",
                     font=ctk.CTkFont(size=10), text_color="#888").pack(pady=(0, 10))

        grid = ctk.CTkFrame(v, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=10, pady=5)
        grid.grid_columnconfigure((0, 1), weight=1)
        grid.grid_rowconfigure((0, 1), weight=1)

        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for idx, ((etiqueta, prompt), (r, col)) in enumerate(zip(prompts_generados, positions)):
            cell = ctk.CTkFrame(grid, fg_color=c["fg_dark"], corner_radius=8)
            cell.grid(row=r, column=col, padx=5, pady=5, sticky="nsew")
            ctk.CTkLabel(cell, text=f"📌 Variante {idx + 1}", font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=c["hdr_text"]).pack(anchor="w", padx=10, pady=(8, 0))
            ctk.CTkLabel(cell, text=etiqueta, font=ctk.CTkFont(size=9, slant="italic"),
                         text_color="#888", wraplength=440, justify="left", anchor="w").pack(fill="x", padx=10, pady=(0, 4))
            txt = ctk.CTkTextbox(cell, wrap="word", height=180, font=ctk.CTkFont(family="Consolas", size=10))
            txt.pack(fill="both", expand=True, padx=10, pady=(0, 5))
            txt.insert("1.0", prompt)

            def _usar(p=prompt):
                self.actualizar_salida(p)
                self.set_estado("🧪 Variante aplicada al editor", "#2ecc71")
                # No cerramos la ventana para poder ver las otras opciones

            btn = ctk.CTkButton(cell, text="✅ Usar este", height=28, fg_color="#1a8a3c", hover_color="#127a30",
                          command=_usar)
            btn.pack(fill="x", padx=10, pady=(0, 8))

        ctk.CTkButton(v, text="Cerrar", width=110, command=v.destroy, fg_color=c["fg_dark"]).pack(pady=(5, 12))
        self.set_estado("🧪 Elige la variante que más te guste", "#3498db")
        self.toggle_botones(True)

    def _cmd_comparar_modelos(self):
        """Genera el prompt actual adaptado a 3 modelos a elegir por el usuario."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.set_estado("⚠️ Escribe una idea primero para comparar modelos.", "#e67e22")
        try:
            self._sesion_log("🆚 Comparar: abrió comparador de modelos")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        modo = self.modo_var.get()

        # Lista de modelos disponibles según modo
        if modo == "imagen":
            modelos_disponibles = [m for m in MODELOS_IMAGEN_FLAT if not m.startswith("──")]
            sugeridos = ["Z Image Turbo", "FLUX.1 [dev]", "Nano Banana Pro Image"]
        elif modo == "video":
            modelos_disponibles = [m for m in MODELOS_VIDEO_FLAT if not m.startswith("──")]
            sugeridos = ["Kling 3.0", "Seedance 2.0", "Veo 3.1"]
        else:
            modelos_disponibles = [m for m in MODELOS_AUDIO_FLAT if not m.startswith("──")]
            sugeridos = ["Suno v5", "Suno v4.5", "Minimax Music 2.5"]

        # Asegurar que los sugeridos estén disponibles
        sugeridos = [m for m in sugeridos if m in modelos_disponibles]
        while len(sugeridos) < 5 and modelos_disponibles:
            for m in modelos_disponibles:
                if m not in sugeridos:
                    sugeridos.append(m)
                    if len(sugeridos) >= 5:
                        break

        sel_vent = GPromptWindow(self)
        sel_vent.title("🆚 Elige modelos para comparar")
        sel_vent.geometry("520x500")
        sel_vent.transient(self)

        ctk.CTkLabel(sel_vent, text="🆚 Comparador de modelos",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 3))
        ctk.CTkLabel(sel_vent, text=f"Idea: {idea[:60]}{'...' if len(idea) > 60 else ''}",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"],
                     wraplength=470).pack(pady=(0, 5))

        # Selector de N modelos (2-5)
        n_frame = ctk.CTkFrame(sel_vent, fg_color="transparent")
        n_frame.pack(fill="x", padx=20, pady=(8, 4))
        ctk.CTkLabel(n_frame, text="¿Cuántos modelos comparar?",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     anchor="w").pack(side="left", padx=(0, 8))
        n_var = ctk.IntVar(value=3)
        n_lbl = ctk.CTkLabel(n_frame, text="3 modelos",
                              font=ctk.CTkFont(size=11, weight="bold"),
                              text_color="#2ecc71", width=90)
        n_lbl.pack(side="right")

        frame_combos = ctk.CTkFrame(sel_vent, fg_color="transparent")
        frame_combos.pack(fill="x", padx=20, pady=5)

        combos = []
        combo_rows = []
        for i in range(5):
            f = ctk.CTkFrame(frame_combos, fg_color="transparent")
            f.pack(fill="x", pady=3)
            ctk.CTkLabel(f, text=f"#{i+1}:",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         width=40, anchor="w").pack(side="left", padx=(0, 8))
            cb = ctk.CTkComboBox(f, values=modelos_disponibles, width=380,
                                  height=28, font=ctk.CTkFont(size=11))
            cb.set(sugeridos[i] if i < len(sugeridos) else modelos_disponibles[0])
            cb.pack(side="left")
            combos.append(cb)
            combo_rows.append(f)

        def _actualizar_n(v):
            n = int(round(float(v)))
            n_var.set(n)
            n_lbl.configure(text=f"{n} modelos")
            for i, row in enumerate(combo_rows):
                if i < n:
                    row.pack(fill="x", pady=3)
                else:
                    row.pack_forget()

        slider = ctk.CTkSlider(n_frame, from_=2, to=5, number_of_steps=3,
                                width=130, command=_actualizar_n)
        slider.set(3)
        slider.pack(side="right", padx=(0, 8))

        # Inicialmente mostrar 3 filas
        _actualizar_n(3)

        # Botones
        btn_frame = ctk.CTkFrame(sel_vent, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=(0, 20))

        def _comparar():
            n = n_var.get()
            seleccionados = [combos[i].get() for i in range(n)]
            # Validar que sean diferentes
            if len(set(seleccionados)) < n:
                self.set_estado(f"⚠️ Elige {n} modelos diferentes.", "#e67e22")
                return
            sel_vent.destroy()
            self._abrir_ventana_comparacion(idea, modo, seleccionados)

        ctk.CTkButton(btn_frame, text="🆚 Comparar", width=140, height=34,
                      fg_color="#1a7a3c", hover_color="#145e2d",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=_comparar).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Cancelar", width=100, height=34,
                      fg_color="#444444", hover_color="#222222",
                      command=sel_vent.destroy).pack(side="left", padx=4)

    def _abrir_ventana_comparacion(self, idea, modo, modelos_compare):
        """Ventana donde se muestran los N prompts generados (N=2..5)."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = _get_tc(is_lt)
        n_modelos = len(modelos_compare)
        vent = GPromptWindow(self)
        vent.title(f"🆚 Comparativa de modelos ({n_modelos})")
        # Tamaño dinámico: más alto si hay más modelos (cards apiladas)
        alto = min(620 + max(0, n_modelos - 3) * 120, 950)
        vent.geometry(f"820x{alto}")
        vent.transient(self)

        ctk.CTkLabel(vent, text=f"🆚 Comparativa de {n_modelos} modelos",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text=f"Idea: {idea[:80]}{'...' if len(idea) > 80 else ''}",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"], wraplength=780).pack(pady=(0, 8))

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=(0, 5))

        lbl_status = ctk.CTkLabel(vent, text=f"🔄 Generando para {n_modelos} modelos...",
                                   font=ctk.CTkFont(size=11), text_color="#f39c12")
        lbl_status.pack(pady=(0, 4))

        # Botón "Cerrar comparativa" — la ventana ya no se cierra al pulsar
        # "Usar este (modelo+prompt)" en una card, así que el usuario
        # necesita un botón explícito para cerrar cuando termine.
        ctk.CTkButton(vent, text="Cerrar comparativa", width=180, height=30,
                      fg_color="#6b7280", hover_color="#4b5563",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=vent.destroy).pack(pady=(0, 8))

        cards = {}
        # 5 colores cíclicos para soportar hasta 5 cards sin IndexError.
        colores_hdr = ["#1a3a5a", "#1a5a3a", "#5a1a3a", "#5a3a1a", "#3a1a5a"]
        for i, m in enumerate(modelos_compare):
            card = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=8)
            card.pack(fill="x", pady=4, padx=2)
            hdr_color = colores_hdr[i % len(colores_hdr)]
            hdr = ctk.CTkFrame(card, fg_color=hdr_color, corner_radius=6, height=28)
            hdr.pack(fill="x", padx=5, pady=(5, 3))
            hdr.pack_propagate(False)

            # Mostrar info del modelo en el header
            specs = get_image_model_specs(m) or get_model_specs(m) or get_audio_model_specs(m) or {}
            chars_max = specs.get("max_chars", "?")
            has_neg = "✅ Neg" if specs.get("has_negative", False) else "❌ Sin neg"
            ctk.CTkLabel(hdr, text=f"  #{i+1}  {m}  ·  {chars_max} chars  ·  {has_neg}",
                         font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=8)

            txt = ctk.CTkTextbox(card, font=ctk.CTkFont(family="Consolas", size=10), height=130, wrap="word")
            txt.pack(fill="x", padx=8, pady=(0, 4))
            txt.insert("1.0", "⏳ Generando...")
            txt.configure(state="disabled")

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=8, pady=(0, 6))
            btn_usar = ctk.CTkButton(btn_row, text="✅ Usar este", width=100, height=22, fg_color="#1a7a3c",
                                       state="disabled", font=ctk.CTkFont(size=10))
            btn_usar.pack(side="left", padx=2)
            btn_copiar = ctk.CTkButton(btn_row, text="📋 Copiar", width=80, height=22, fg_color=c["fg_dark"],
                                          state="disabled", font=ctk.CTkFont(size=10))
            btn_copiar.pack(side="left", padx=2)
            lbl_chars = ctk.CTkLabel(btn_row, text="", font=ctk.CTkFont(size=9), text_color=c["muted_text"])
            lbl_chars.pack(side="right", padx=4)
            cards[m] = {"txt": txt, "btn_usar": btn_usar, "btn_copiar": btn_copiar,
                        "lbl_chars": lbl_chars, "card": card, "hdr": hdr,
                        "hdr_color": hdr_color}

            def _generar(modelo):
                try:
                    specs = get_image_model_specs(modelo) or get_model_specs(modelo) or get_audio_model_specs(modelo) or {}
                    max_c = specs.get("max_chars", 1500)
                    has_neg = specs.get("has_negative", True)
                    is_natural = specs.get("is_natural", False)
                    no_weights = specs.get("no_weights", False)
                    best_for = specs.get("best_for", "")[:200] if specs else ""

                    if is_natural:
                        tipo_format = "lenguaje natural descriptivo en una sola línea, sin saltos de línea"
                    elif no_weights:
                        tipo_format = "tags separados por comas, sin pesos numéricos"
                    else:
                        tipo_format = "tags separados por comas con pesos opcionales (tag:1.2)"

                    # Petición ESTRICTA — antes el LLM mezclaba contenido entre
                    # respuestas y a veces devolvía "Aquí tienes prompts para
                    # varios modelos" o concatenaba múltiples bloques.
                    if has_neg:
                        estructura = (
                            "DEVUELVE EXACTAMENTE 2 LÍNEAS, nada más:\n"
                            "POSITIVE PROMPT: <prompt en una sola línea>\n"
                            "NEGATIVE PROMPT: <negative en una sola línea>"
                        )
                    else:
                        estructura = (
                            "DEVUELVE EXACTAMENTE 1 LÍNEA, nada más:\n"
                            "POSITIVE PROMPT: <prompt en una sola línea>"
                        )

                    peticion = (
                        f"Genera UN prompt de {modo} optimizado para este modelo concreto:\n\n"
                        f"MODELO: {modelo}\n"
                        f"FORTALEZAS: {best_for}\n\n"
                        f"IDEA: {idea}\n"
                        f"ESTILOS A INCLUIR: {self.estilos_texto()}\n\n"
                        "REGLAS ESTRICTAS:\n"
                        f"- Formato: {tipo_format}\n"
                        f"- Límite POSITIVE: {max_c} caracteres\n"
                        "- NO menciones otros modelos en la respuesta\n"
                        "- NO añadas explicaciones tipo 'Aquí tienes...'\n"
                        "- NO añadas prosa descriptiva extra\n"
                        "- NO repitas la sección POSITIVE/NEGATIVE\n"
                        f"- Aprovecha las fortalezas del modelo {modelo}\n\n"
                        f"{estructura}"
                    )
                    resp = self.deepseek.generar(peticion, temperature=0.45, max_tokens=1500)
                    resp = limpiar_marcadores(resp)

                    # Defensa client-side: extraer SOLO el primer bloque
                    # POSITIVE [+ NEGATIVE], descartando todo lo demás.
                    m_pos = _re.search(
                        r'(?:POSITIVE\s+)?PROMPT\s*:\s*(.+?)(?=\n\s*NEGATIVE\s+PROMPT\s*:|\n\s*POSITIVE\s+PROMPT\s*:|\n\s*###|\n\s*\*\*\*|\Z)',
                        resp, flags=_re.DOTALL | _re.IGNORECASE)
                    m_neg = _re.search(
                        r'NEGATIVE\s+PROMPT\s*:\s*(.+?)(?=\n\s*POSITIVE\s+PROMPT\s*:|\n\s*NEGATIVE\s+PROMPT\s*:|\n\s*###|\n\s*\*\*\*|\Z)',
                        resp, flags=_re.DOTALL | _re.IGNORECASE)
                    if m_pos:
                        pos_clean = " ".join(m_pos.group(1).split())
                        # Truncar suave al límite del modelo (con margen)
                        if isinstance(max_c, int) and len(pos_clean) > max_c + 200:
                            pos_clean = pos_clean[:max_c + 200].rsplit(",", 1)[0]
                        if has_neg and m_neg:
                            neg_clean = " ".join(m_neg.group(1).split())
                            resp = f"POSITIVE PROMPT: {pos_clean}\nNEGATIVE PROMPT: {neg_clean}"
                        else:
                            resp = f"POSITIVE PROMPT: {pos_clean}"
                    else:
                        # Sin marcador detectable: asumir todo es POSITIVE
                        pos_clean = " ".join(resp.split())
                        if isinstance(max_c, int) and len(pos_clean) > max_c + 200:
                            pos_clean = pos_clean[:max_c + 200].rsplit(",", 1)[0]
                        resp = f"POSITIVE PROMPT: {pos_clean}"

                    # Eliminar pesos si el modelo no los soporta
                    if no_weights:
                        resp = _re.sub(r'\(([^()]+?):\s*[0-9.]+\s*\)', r'\1', resp)

                    def _mostrar(r=resp, m=modelo, mc=max_c):
                        try:
                            if not vent.winfo_exists():
                                return
                            cards[m]["txt"].configure(state="normal")
                            cards[m]["txt"].delete("1.0", "end")
                            cards[m]["txt"].insert("1.0", r)
                            cards[m]["txt"].configure(state="disabled")
                            cards[m]["lbl_chars"].configure(text=f"{len(r)} / {mc} chars")

                            def _aplicar_y_cambiar_modelo(r2=r, m2=m):
                                # Aplica el prompt al resultado Y cambia el
                                # modelo activo en el combo correspondiente.
                                # La ventana NO se cierra: el usuario puede
                                # seguir probando otros modelos del set sin
                                # perder las opciones.
                                modo_act = self.modo_var.get()
                                try:
                                    if modo_act == "imagen" and hasattr(self, "combo_modelo_imagen"):
                                        valores = list(self.combo_modelo_imagen.cget("values") or [])
                                        if m2 in valores:
                                            self.combo_modelo_imagen.set(m2)
                                            if hasattr(self, "_on_modelo_imagen_cambio"):
                                                self._on_modelo_imagen_cambio()
                                    elif modo_act == "video" and hasattr(self, "combo_modelo_video"):
                                        valores = list(self.combo_modelo_video.cget("values") or [])
                                        if m2 in valores:
                                            self.combo_modelo_video.set(m2)
                                    elif modo_act == "audio" and hasattr(self, "combo_modelo_audio"):
                                        valores = list(self.combo_modelo_audio.cget("values") or [])
                                        if m2 in valores:
                                            self.combo_modelo_audio.set(m2)
                                except Exception as _e:
                                    logger.debug(f"[silent compar usar] {_e}")
                                self.actualizar_salida(r2)

                                # Highlight visual: borde dorado en la card aplicada,
                                # las demás vuelven a su color original.
                                for _m_key, _info in cards.items():
                                    try:
                                        if _m_key == m2:
                                            _info["card"].configure(border_color="#fbbf24",
                                                                     border_width=3)
                                            _info["hdr"].configure(fg_color="#fbbf24")
                                        else:
                                            _info["card"].configure(border_width=0)
                                            _info["hdr"].configure(fg_color=_info["hdr_color"])
                                    except Exception as _e:
                                        logger.debug(f"[silent highlight] {_e}")

                                self.set_estado(
                                    f"🏆 '{m2}' aplicado — la ventana sigue abierta para probar otros",
                                    "#2ecc71")

                            cards[m]["btn_usar"].configure(
                                state="normal",
                                text="🏆 Usar este (modelo+prompt)",
                                width=200,
                                command=_aplicar_y_cambiar_modelo,
                            )
                            cards[m]["btn_copiar"].configure(
                                state="normal",
                                command=lambda r=r, m=m: (
                                    pyperclip.copy(r),
                                    self.set_estado(f"📋 Copiado prompt de {m}", "#2ecc71")))
                        except Exception as _e:
                            logger.debug(f"[silent] {_e}")
                    self.after(0, _mostrar)
                except Exception as e:
                    def _err(m=modelo, exc=e):
                        try:
                            if not vent.winfo_exists():
                                return
                            cards[m]["txt"].configure(state="normal")
                            cards[m]["txt"].delete("1.0", "end")
                            cards[m]["txt"].insert("1.0", f"❌ Error: {exc}")
                            cards[m]["txt"].configure(state="disabled")
                        except Exception as _e:
                            logger.debug(f"[silent] {_e}")
                    self.after(0, lambda: _err(m=modelo, exc=e))

            def _todos():
                for m in modelos_compare:
                    threading.Thread(target=_generar, args=(m,), daemon=True).start()

            threading.Thread(target=_todos, daemon=True).start()
