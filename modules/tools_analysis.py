"""Analysis Tools Mixin - Statistics, Auto-improve, Critique, Scoring, Education Mode, etc."""
import os
import re
import json
import threading
import datetime
import random
import pyperclip
from collections import Counter
import customtkinter as ctk
import tkinter as tk
from workers import limpiar_marcadores
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app import ArquitectoApp

class ToolsAnalysisMixin:
    """Mixin containing all analysis tool methods."""

    def _cmd_modo_educativo(self):
        """Activa/desactiva el modo educativo: tooltips explicativos para principiantes."""
        if not hasattr(self, '_modo_educativo_activo'):
            self._modo_educativo_activo = False
        self._modo_educativo_activo = not self._modo_educativo_activo

        if self._modo_educativo_activo:
            vent = ctk.CTkToplevel(self)
            vent.title("📖 Modo educativo — Glosario")
            vent.geometry("750x600")
            vent.transient(self)
            ctk.CTkLabel(vent, text="📖 Glosario de términos AI",
                         font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
            ctk.CTkLabel(vent, text="Aprende qué significa cada término de prompts AI",
                         font=ctk.CTkFont(size=10), text_color="#888888").pack(pady=(0, 8))

            scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
            scroll.pack(fill="both", expand=True, padx=15, pady=5)

            glosario = [
                ("📐 ¿Qué es un PROMPT?",
                 "El prompt es la descripción en texto que le das al modelo IA para que genere una imagen, vídeo o audio. Cuanto más específico, mejor resultado."),
                ("🟢 POSITIVE PROMPT",
                 "Lo que SÍ quieres que aparezca: sujeto, estilo, iluminación, cámara, atmósfera, calidad."),
                ("🔴 NEGATIVE PROMPT",
                 "Lo que NO quieres: artefactos, texto, deformaciones, estilo equivocado. Solo algunos modelos lo soportan."),
                ("🏷 TAGS vs LENGUAJE NATURAL",
                 "Tags = palabras clave separadas por comas (estilo Stable Diffusion). Natural = frases descriptivas (estilo Midjourney/GPT)."),
                ("⚖️ PESOS NUMÉRICOS — (tag:1.2)",
                 "Aumentan la importancia de un tag. (tag:1.5) refuerza, (tag:0.7) reduce. Solo en modelos Stable Diffusion."),
                ("🎯 CFG (Classifier-Free Guidance)",
                 "Controla qué tan fielmente el modelo sigue tu prompt. Bajo (1-3) = más creativo, Alto (7-15) = más estricto."),
                ("⚡ MODELOS TURBO",
                 "Modelos optimizados para velocidad (Z Image Turbo, FLUX Schnell). Generan en segundos pero con CFG bajo (~1) — IGNORAN pesos y negative prompt."),
                ("🌐 LENGUAJE NATURAL",
                 "Modelos como Midjourney, GPT Image, FLUX entienden frases completas. NO uses tags ni pesos numéricos en estos."),
                ("📐 RATIO / ASPECT RATIO",
                 "Proporción de la imagen. 1:1 = cuadrado (Instagram), 16:9 = horizontal (YouTube), 9:16 = vertical (TikTok/Stories)."),
                ("🎨 SAMPLER",
                 "Algoritmo que decide cómo el modelo va creando la imagen. Euler = rápido, DPM++ = balanceado, Karras = alta calidad."),
                ("🔢 STEPS / PASOS",
                 "Cuántas iteraciones hace el modelo. Más pasos = más detalle pero más lento. Turbo: 4-8, Estándar: 20-30, HQ: 50+."),
                ("🌱 SEED / SEMILLA",
                 "Número aleatorio que define las variaciones. Misma seed + mismo prompt = misma imagen exacta. Útil para iterar."),
                ("✨ MASTERPIECE / 8K / DETAILED",
                 "Tags 'mágicos' que mejoran calidad en SD. Cuidado: usarlos demasiado los degrada. 1-2 al final del prompt es suficiente."),
                ("👤 LORA",
                 "Modelo pequeño que se 'enchufa' al modelo principal para añadir un estilo, personaje o concepto específico."),
                ("🎯 TRIGGER WORDS",
                 "Palabras clave que activan un LoRA. Ej: 'sks dog' para un LoRA de perro. Van al inicio del prompt."),
            ]

            for titulo, desc in glosario:
                card = ctk.CTkFrame(scroll, fg_color="#111820", corner_radius=8)
                card.pack(fill="x", pady=4)
                ctk.CTkLabel(card, text=titulo, font=ctk.CTkFont(size=11, weight="bold"),
                             text_color="#aaccee").pack(anchor="w", padx=12, pady=(6, 2))
                ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=10),
                             text_color="#888888", wraplength=680, anchor="w",
                             justify="left").pack(fill="x", padx=12, pady=(0, 6))

            ctk.CTkButton(vent, text="✅ Entendido", width=140, height=30, fg_color="#1a7a3c",
                          command=vent.destroy).pack(pady=10)

    def _cmd_critica_historial(self):
        """LLM analiza tus ideas (no los prompts) y te da consejos sobre qué generas."""
        items = self.store.historial or []
        if len(items) < 5:
            return self.set_estado("⚠️ Necesitas al menos 5 prompts en historial.", "#e67e22")

        self.set_estado("🔍 Analizando tus ideas y patrones de uso...", "#f39c12")

        ultimos = items[:30]
        from collections import Counter
        modelos_usados = Counter()
        plataformas_usadas = Counter()
        modos_usados = Counter()
        estilos_usados = Counter()
        temas = []

        for it in ultimos:
            if isinstance(it, dict):
                if it.get("modelo"): modelos_usados[it["modelo"]] += 1
                if it.get("plataforma"): plataformas_usadas[it["plataforma"]] += 1
                if it.get("modo"): modos_usados[it["modo"]] += 1
                est = it.get("estilos", "")
                if est:
                    for e in est.split(","):
                        e = e.strip()
                        if e: estilos_usados[e] += 1
                contenido = it.get("contenido", "")
                if contenido:
                    import re
                    m = re.search(r'POSITIVE\s+PROMPT\s*:\s*([^,\n]+)', contenido, re.IGNORECASE)
                    if m:
                        temas.append(m.group(1).strip()[:80])

        resumen = (
            f"DATOS DEL USUARIO (sus últimos {len(ultimos)} prompts):\n\n"
            f"📊 Modelos más usados: {', '.join([f'{m} ({n}x)' for m, n in modelos_usados.most_common(5)]) or 'N/A'}\n"
            f"🌐 Plataformas: {', '.join([f'{p} ({n}x)' for p, n in plataformas_usadas.most_common(5)]) or 'N/A'}\n"
            f"📱 Modos: {', '.join([f'{m} ({n}x)' for m, n in modos_usados.most_common()]) or 'N/A'}\n"
            f"🎨 Estilos más marcados: {', '.join([f'{e} ({n}x)' for e, n in estilos_usados.most_common(8)]) or 'N/A'}\n\n"
            f"📝 Primeros elementos de cada prompt (lo que pidió el usuario):\n"
        )
        for i, t in enumerate(temas[:20], 1):
            resumen += f"  {i}. {t}\n"

        peticion = (
            f"{resumen}\n\n"
            f"Analiza los PATRONES de USO del usuario y dale consejos sobre QUÉ TIPO DE COSAS GENERA, no sobre la calidad técnica del prompt.\n\n"
            f"FORMATO DE RESPUESTA en español:\n\n"
            f"📊 PERFIL DETECTADO:\n"
            f"   - 2-3 frases describiendo qué tipo de creador es (¿retratista? ¿paisajista? ¿conceptual?)\n\n"
            f"🎯 TEMAS RECURRENTES:\n"
            f"   - 3-5 temas o sujetos que más repite\n\n"
            f"🔄 PATRONES (lo que repite mucho):\n"
            f"   - Estilos, modelos o tipos de escena que predominan\n\n"
            f"💡 SUGERENCIAS DE EXPERIMENTACIÓN:\n"
            f"   - 5 cosas NUEVAS que NO ha probado y le podrían interesar:\n"
            f"     * Estilos diferentes a los suyos típicos\n"
            f"     * Modelos que aún no usa\n"
            f"     * Géneros/temas que podrían enriquecer su trabajo\n\n"
            f"⚠️ POSIBLES MEJORAS EN SUS IDEAS:\n"
            f"   - Si sus ideas son muy cortas/genéricas, sugerir cómo enriquecerlas\n"
            f"   - Si solo prueba 1 estilo, recomendar combinaciones\n"
            f"   - Si no usa modelos avanzados, animar a probar (Mystic, GPT 2, etc.)\n\n"
            f"NOTA: Enfócate en QUÉ GENERA y CÓMO PUEDE EXPLORAR MÁS, no en cómo escribir prompts."
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.5, max_tokens=2500, modelo_llm=self.llm_var.get())
                resp = limpiar_marcadores(resp)

                def _mostrar():
                    vent = ctk.CTkToplevel(self)
                    vent.title("🔍 Análisis de tus patrones")
                    vent.geometry("750x650")
                    vent.transient(self)
                    ctk.CTkLabel(vent, text="🔍 Análisis de tus patrones creativos", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
                    ctk.CTkLabel(vent, text=f"Análisis de tus últimas {len(ultimos)} ideas — patrones, temas y sugerencias",
                                 font=ctk.CTkFont(size=10), text_color="#888888").pack(pady=(0, 8))
                    txt = ctk.CTkTextbox(vent, font=ctk.CTkFont(size=11), wrap="word")
                    txt.pack(fill="both", expand=True, padx=15, pady=(0, 5))
                    txt.insert("1.0", resp)
                    txt.configure(state="disabled")
                    ctk.CTkButton(vent, text="📋 Copiar análisis", width=140, height=28,
                                  command=lambda: pyperclip.copy(resp)).pack(pady=10)
                    self.set_estado("🔍 Análisis listo", "#2ecc71")
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_automejora_periodica(self):
        """Revisa los últimos prompts y sugiere mejoras automáticas."""
        items = self.store.historial or []
        if len(items) < 3:
            return self.set_estado("⚠️ Necesitas al menos 3 prompts en historial.", "#e67e22")

        self.set_estado("🚀 Auto-mejora: analizando tus últimos prompts...", "#f39c12")

        ultimos = items[:10]
        prompts = []
        for i, it in enumerate(ultimos, 1):
            contenido = it.get("contenido", "") if isinstance(it, dict) else str(it)
            prompts.append(f"{i}. {contenido[:300]}")

        peticion = (
            f"Aquí tienes los últimos 10 prompts del usuario:\n\n"
            f"{chr(10).join(prompts)}\n\n"
            f"Para cada prompt, proporciona:\n"
            f"1. Qué está BIEN (1 frase)\n"
            f"2. Qué podría MEJORAR (1 frase específica)\n"
            f"3. Versión MEJORADA del prompt\n\n"
            f"Devuelve en español, formato compacto."
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.7, max_tokens=4000, modelo_llm=self.llm_var.get())
                resp = limpiar_marcadores(resp)

                def _mostrar():
                    vent = ctk.CTkToplevel(self)
                    vent.title("🚀 Auto-mejora de prompts")
                    vent.geometry("800x700")
                    vent.transient(self)
                    ctk.CTkLabel(vent, text="🚀 Sugerencias de mejora", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
                    ctk.CTkLabel(vent, text=f"Análisis de tus últimos {len(ultimos)} prompts",
                                 font=ctk.CTkFont(size=10), text_color="#888888").pack(pady=(0, 8))
                    txt = ctk.CTkTextbox(vent, font=ctk.CTkFont(size=11), wrap="word")
                    txt.pack(fill="both", expand=True, padx=15, pady=(0, 5))
                    txt.insert("1.0", resp)
                    txt.configure(state="disabled")
                    ctk.CTkButton(vent, text="📋 Copiar mejoras", width=140, height=28,
                                  command=lambda: pyperclip.copy(resp)).pack(pady=10)
                    self.set_estado("🚀 Auto-mejora lista", "#2ecc71")
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))

        threading.Thread(target=_worker, daemon=True).start()

    def _abrir_estadisticas(self):
        """Ventana con estadísticas de uso: prompts generados, modelos más usados, etc."""
        import tkinter as tk
        prefs = self.store.cargar_preferencias()
        hist = self.store.historial or []
        favs = self.store.favoritos or []
        stars = self.store.estrellas or []
        seeds = prefs.get("seeds_favoritos", [])

        vent = ctk.CTkToplevel(self)
        vent.title("📈 Estadísticas de uso")
        vent.geometry("700x550")
        vent.transient(self)

        ctk.CTkLabel(vent, text="📈 Estadísticas", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 3))
        ctk.CTkLabel(vent, text=f"Desde {hist[-1].get('fecha', 'inicio') if hist else '—'} hasta {hist[0].get('fecha', 'hoy') if hist else '—'}",
                     font=ctk.CTkFont(size=10), text_color="#888888").pack(pady=(0, 15))

        stats = [
            ("📋 Prompts en historial", str(len(hist))),
            ("⭐ Favoritos", str(len(favs))),
            ("🌟 Estrellas", str(len(stars))),
            ("💎 Seeds guardados", str(len(seeds))),
            ("🧑 Personajes", str(len(self.store.personajes or []))),
            ("🔗 LoRAs", str(len(self.store.loras or []))),
            ("✂️ Snippets", str(len(prefs.get("snippets", [])))),
            ("🧪 Fórmulas", str(len(prefs.get("formulas", [])))),
            ("📑 Plantillas", str(len(prefs.get("plantillas", [])))),
        ]

        # Grid de stats
        grid = ctk.CTkFrame(vent, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=10)
        for i, (label, val) in enumerate(stats):
            col, row = i % 3, i // 3
            card = ctk.CTkFrame(grid, fg_color="#111820", corner_radius=10, border_color="#1e2d3d", border_width=1)
            card.grid(row=row, column=col, padx=8, pady=6, sticky="nsew")
            ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=22, weight="bold"),
                         text_color="#3498db").pack(pady=(12, 2))
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=10),
                         text_color="#888888").pack(pady=(0, 10))

        for c in range(3):
            grid.grid_columnconfigure(c, weight=1)

        # Modelos más usados
        if hist:
            from collections import Counter
            modelos = Counter()
            for it in hist:
                if isinstance(it, dict) and it.get("modelo"):
                    modelos[it["modelo"]] += 1
            top = modelos.most_common(5)
            if top:
                ctk.CTkLabel(vent, text="🏆 Top modelos usados", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(15, 8))
                for i, (modelo, count) in enumerate(top, 1):
                    bar = ctk.CTkFrame(vent, fg_color="#111820", corner_radius=6)
                    bar.pack(fill="x", padx=20, pady=2)
                    pct = int(count / len(hist) * 100)
                    ctk.CTkLabel(bar, text=f"{i}. {modelo}", font=ctk.CTkFont(size=10, weight="bold"),
                                 text_color="#aaccee", width=140, anchor="w").pack(side="left", padx=8, pady=4)
                    barra_pct = ctk.CTkProgressBar(bar, width=300, height=8)
                    barra_pct.pack(side="left", padx=(10, 5), pady=4)
                    barra_pct.set(pct / 100)
                    ctk.CTkLabel(bar, text=f"{count}x ({pct}%)", font=ctk.CTkFont(size=9),
                                 text_color="#888888").pack(side="left", padx=(0, 8))

        ctk.CTkButton(vent, text="Cerrar", width=120, height=30, command=vent.destroy).pack(pady=15)

    def _cmd_scoring(self):
        """Puntúa el prompt actual y genera versión mejorada.

        v1.0.8: renderizado con código de colores. Cada score se detecta
        con regex y se colorea según su valor (verde >= 80%, amarillo
        50-79%, rojo < 50%). El TOTAL se destaca en grande.
        """
        actual = self.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.set_estado("⚠️ Genera un prompt primero.", "#e67e22")

        self.set_estado("📝 Analizando y puntuando prompt...", "#f39c12")

        peticion = (
            f"Analiza este prompt de IA y devuelve EXACTAMENTE en este formato (mantén las etiquetas):\n\n"
            f"PUNTUACIÓN (0-100):\n"
            f"- Claridad del sujeto: X/25\n"
            f"- Detalle de estilo: X/25\n"
            f"- Composición y cámara: X/25\n"
            f"- Calidad y atmósfera: X/25\n"
            f"TOTAL: X/100\n\n"
            f"✅ PUNTOS FUERTES:\n"
            f"- (lista 2-3 cosas que están bien)\n\n"
            f"⚠️ PUNTOS DÉBILES:\n"
            f"- (lista 2-3 cosas que faltan o sobran)\n\n"
            f"💡 SUGERENCIA:\n"
            f"- (1-2 consejos específicos accionables)\n\n"
            f"PROMPT:\n{actual}"
        )

        def _color_para_score(valor: int, maximo: int) -> str:
            """Devuelve un color hex según el porcentaje del score."""
            if maximo <= 0:
                return "#888888"
            pct = (valor / maximo) * 100
            if pct >= 80:
                return "#2ecc71"  # verde
            elif pct >= 50:
                return "#f39c12"  # amarillo/naranja
            else:
                return "#e74c3c"  # rojo

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.3, max_tokens=2000, modelo_llm=self.llm_var.get())
                resp = limpiar_marcadores(resp)

                # Parsear scores con regex
                # Formato esperado: "- Claridad del sujeto: 18/25"
                pattern_cat = re.compile(r"-\s*([^:]+):\s*(\d+)\s*/\s*(\d+)")
                pattern_total = re.compile(r"TOTAL\s*:\s*(\d+)\s*/\s*(\d+)", re.IGNORECASE)

                scores_cat = []
                for m in pattern_cat.finditer(resp):
                    nombre, val, maxv = m.group(1).strip(), int(m.group(2)), int(m.group(3))
                    # Filtrar para que no capture líneas como "- bla bla 1/2" en sugerencias
                    if maxv in (10, 20, 25, 50, 100) and val <= maxv:
                        scores_cat.append((nombre, val, maxv))

                m_total = pattern_total.search(resp)
                total_val, total_max = (int(m_total.group(1)), int(m_total.group(2))) if m_total else (None, None)

                # Extraer secciones de texto
                def _extraer_seccion(texto, marcador, siguiente_marcadores):
                    idx = texto.find(marcador)
                    if idx == -1:
                        return ""
                    inicio = idx + len(marcador)
                    fin = len(texto)
                    for sig in siguiente_marcadores:
                        i = texto.find(sig, inicio)
                        if i != -1 and i < fin:
                            fin = i
                    return texto[inicio:fin].strip().lstrip(":").strip()

                fuertes = _extraer_seccion(resp, "✅ PUNTOS FUERTES", ["⚠️ PUNTOS DÉBILES", "💡 SUGERENCIA", "PROMPT:"])
                debiles = _extraer_seccion(resp, "⚠️ PUNTOS DÉBILES", ["💡 SUGERENCIA", "PROMPT:"])
                sugerencia = _extraer_seccion(resp, "💡 SUGERENCIA", ["PROMPT:"])

                def _mostrar():
                    is_lt = ctk.get_appearance_mode().lower() == "light"
                    try:
                        from config import get_theme_colors
                        c = get_theme_colors(is_lt)
                    except Exception:
                        c = {"panel_text": "#111827" if is_lt else "#e5e7eb",
                             "panel_bg": "#f9fafb" if is_lt else "#0f1318",
                             "muted_text": "#4b5563" if is_lt else "#9ca3af",
                             "card_bg": "#ffffff" if is_lt else "#111820",
                             "card_border": "#d1d5db" if is_lt else "#1f2937"}

                    vent = ctk.CTkToplevel(self)
                    vent.title("📝 Scoring de prompt")
                    vent.geometry("720x640")
                    vent.transient(self)
                    vent.configure(fg_color=c.get("panel_bg"))

                    ctk.CTkLabel(vent, text="📝 Análisis de calidad del prompt",
                                 font=ctk.CTkFont(size=15, weight="bold"),
                                 text_color=c.get("panel_text")).pack(pady=(12, 4))

                    # ── Bloque TOTAL grande ─────────────────────────
                    if total_val is not None:
                        total_color = _color_para_score(total_val, total_max)
                        total_frame = ctk.CTkFrame(vent, fg_color=c.get("card_bg"),
                                                    border_color=total_color, border_width=2,
                                                    corner_radius=10)
                        total_frame.pack(padx=20, pady=(4, 10), fill="x")

                        # Etiqueta calidad textual
                        pct = (total_val / total_max) * 100 if total_max else 0
                        if pct >= 85: etiqueta = "🏆 Excelente"
                        elif pct >= 70: etiqueta = "✨ Bueno"
                        elif pct >= 50: etiqueta = "🟡 Mejorable"
                        else: etiqueta = "⚠️ Necesita trabajo"

                        ctk.CTkLabel(total_frame, text=f"{total_val} / {total_max}",
                                     font=ctk.CTkFont(size=36, weight="bold"),
                                     text_color=total_color).pack(pady=(10, 0))
                        ctk.CTkLabel(total_frame, text=etiqueta,
                                     font=ctk.CTkFont(size=13, weight="bold"),
                                     text_color=total_color).pack(pady=(0, 10))

                    # ── Categorías con barras de color ──────────────
                    if scores_cat:
                        cat_frame = ctk.CTkFrame(vent, fg_color="transparent")
                        cat_frame.pack(padx=20, pady=4, fill="x")

                        for nombre, val, maxv in scores_cat[:4]:  # primeros 4 por seguridad
                            row = ctk.CTkFrame(cat_frame, fg_color="transparent")
                            row.pack(fill="x", pady=2)

                            color = _color_para_score(val, maxv)
                            # Nombre categoría
                            ctk.CTkLabel(row, text=nombre, anchor="w",
                                         font=ctk.CTkFont(size=11, weight="bold"),
                                         text_color=c.get("panel_text"),
                                         width=180).pack(side="left", padx=(2, 8))
                            # Barra de progreso
                            try:
                                bar = ctk.CTkProgressBar(row, width=320, height=14,
                                                          progress_color=color)
                                bar.set(val / maxv if maxv else 0)
                                bar.pack(side="left", padx=4)
                            except Exception:
                                pass
                            # Score numérico coloreado
                            ctk.CTkLabel(row, text=f"{val}/{maxv}",
                                         font=ctk.CTkFont(size=11, weight="bold"),
                                         text_color=color, width=60).pack(side="left", padx=4)

                    # ── Texto detallado (puntos fuertes/débiles/sugerencia) ──
                    detail_frame = ctk.CTkScrollableFrame(vent, fg_color="transparent",
                                                           height=180)
                    detail_frame.pack(fill="both", expand=True, padx=20, pady=(8, 4))

                    if fuertes:
                        ctk.CTkLabel(detail_frame, text="✅ Puntos fuertes",
                                     font=ctk.CTkFont(size=12, weight="bold"),
                                     text_color="#2ecc71", anchor="w").pack(anchor="w", pady=(2, 1))
                        ctk.CTkLabel(detail_frame, text=fuertes,
                                     font=ctk.CTkFont(size=11), wraplength=620,
                                     justify="left", anchor="w",
                                     text_color=c.get("panel_text")).pack(anchor="w", padx=12, pady=(0, 6))

                    if debiles:
                        ctk.CTkLabel(detail_frame, text="⚠️ Puntos débiles",
                                     font=ctk.CTkFont(size=12, weight="bold"),
                                     text_color="#e74c3c", anchor="w").pack(anchor="w", pady=(2, 1))
                        ctk.CTkLabel(detail_frame, text=debiles,
                                     font=ctk.CTkFont(size=11), wraplength=620,
                                     justify="left", anchor="w",
                                     text_color=c.get("panel_text")).pack(anchor="w", padx=12, pady=(0, 6))

                    if sugerencia:
                        ctk.CTkLabel(detail_frame, text="💡 Sugerencia",
                                     font=ctk.CTkFont(size=12, weight="bold"),
                                     text_color="#3498db", anchor="w").pack(anchor="w", pady=(2, 1))
                        ctk.CTkLabel(detail_frame, text=sugerencia,
                                     font=ctk.CTkFont(size=11), wraplength=620,
                                     justify="left", anchor="w",
                                     text_color=c.get("panel_text")).pack(anchor="w", padx=12, pady=(0, 6))

                    # Si no hubo parseo (formato raro), mostrar todo el texto
                    if not (scores_cat or fuertes or debiles or sugerencia):
                        txt = ctk.CTkTextbox(detail_frame, font=ctk.CTkFont(size=11),
                                              wrap="word", height=160)
                        txt.pack(fill="both", expand=True, padx=4, pady=4)
                        txt.insert("1.0", resp)
                        txt.configure(state="disabled")

                    # ── Botones ─────────────────────────────────────
                    btn_frame = ctk.CTkFrame(vent, fg_color="transparent")
                    btn_frame.pack(pady=10)
                    ctk.CTkButton(btn_frame, text="📋 Copiar análisis", width=140, height=30,
                                  command=lambda: pyperclip.copy(resp)).pack(side="left", padx=4)

                    def _generar_mejorado():
                        self.set_estado("✨ Generando versión mejorada...", "#f39c12")
                        peticion_mejora = (
                            f"Mejora este prompt de IA manteniendo la idea original pero añadiendo:\n"
                            f"- Más detalle en sujeto y estilo\n"
                            f"- Especificaciones de cámara e iluminación\n"
                            f"- Tags de calidad apropiados\n"
                            f"- Composición más interesante\n\n"
                            f"Devuelve SOLO el prompt mejorado, sin explicaciones:\n\n{actual}"
                        )
                        def _worker_mejorar():
                            try:
                                texto_mejorado = self.deepseek.generar(peticion_mejora, temperature=0.3, max_tokens=2000, modelo_llm=self.llm_var.get())
                                texto_mejorado = limpiar_marcadores(texto_mejorado)
                                def _aplicar():
                                    self.actualizar_salida(texto_mejorado)
                                    vent.destroy()
                                    self.set_estado("✨ Prompt mejorado aplicado", "#2ecc71")
                                self.after(0, _aplicar)
                            except Exception as e:
                                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                        threading.Thread(target=_worker_mejorar, daemon=True).start()

                    ctk.CTkButton(btn_frame, text="✨ Mejorar prompt", width=140, height=30,
                                  fg_color="#7c3aed", command=_generar_mejorado).pack(side="left", padx=4)

                    self.set_estado("📝 Scoring listo", "#2ecc71")
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))

        threading.Thread(target=_worker, daemon=True).start()

    def _detectar_nsfw_auto(self, idea=None):
        """Detecta si el prompt actual tiene elementos NSFW y avisa."""
        texto = idea if idea else self.txt_salida.get("1.0", "end").strip()
        actual = texto.lower()
        nsfw_terms = ["nude", "naked", "nsfw", "explicit", "xxx", "porn", "sex", "boobs", "butt", "ass"]
        if any(term in actual for term in nsfw_terms):
            if hasattr(self, 'nsfw_var'):
                self.nsfw_var.set(True)
            self.set_estado("⚠️ Contenido NSFW detectado — activado modo NSFW", "#e74c3c")

    def _guardar_seed_favorito(self):
        """Guarda la configuración actual como seed favorito."""
        prefs = self.store.cargar_preferencias()
        seeds = prefs.get("seeds_favoritos", [])
        seed = {
            "nombre": f"Seed {len(seeds)+1}",
            "estilos": self.estilos_seleccionados(),
            "plataforma": self.plataforma_var.get() if hasattr(self, 'plataforma_var') else "",
            "modelo_img": self.modelo_img_var.get() if hasattr(self, 'modelo_img_var') else "",
            "modelo_vid": self.modelo_vid_var.get() if hasattr(self, 'modelo_vid_var') else "",
            "ratio": self.ratio_var.get() if hasattr(self, 'ratio_var') else "",
        }
        seeds.append(seed)
        prefs["seeds_favoritos"] = seeds
        self.store.guardar_preferencias(prefs)
        self.set_estado("💎 Seed guardado", "#2ecc71")

    def _abrir_seeds_favoritos(self):
        """Ventana con seeds favoritos para aplicar."""
        prefs = self.store.cargar_preferencias()
        seeds = prefs.get("seeds_favoritos", [])
        if not seeds:
            return self.set_estado("⚠️ No tienes seeds guardados.", "#e67e22")

        vent = ctk.CTkToplevel(self)
        vent.title("💎 Seeds favoritos")
        vent.geometry("500x400")
        vent.transient(self)

        ctk.CTkLabel(vent, text="💎 Seeds favoritos", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 5))

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=5)

        for i, seed in enumerate(seeds):
            card = ctk.CTkFrame(scroll, fg_color="#111820", corner_radius=8)
            card.pack(fill="x", pady=3)
            ctk.CTkLabel(card, text=seed.get("nombre", "?"), font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#aaccee").pack(anchor="w", padx=10, pady=(6, 2))
            ctk.CTkLabel(card, text=f"Modelo: {seed.get('modelo_img') or seed.get('modelo_vid', '?')} | "
                                    f"Estilos: {', '.join(seed.get('estilos', [])[:3]) or 'Ninguno'}",
                         font=ctk.CTkFont(size=9), text_color="#888888").pack(anchor="w", padx=10, pady=(0, 4))
            def _aplicar(s=seed):
                self._aplicar_seed(s)
                vent.destroy()
            def _borrar(idx=i):
                seeds_actuales = prefs.get("seeds_favoritos", [])
                if 0 <= idx < len(seeds_actuales):
                    seeds_actuales.pop(idx)
                    prefs["seeds_favoritos"] = seeds_actuales
                    self.store.guardar_preferencias(prefs)
                    self._abrir_seeds_favoritos()
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(anchor="e", padx=8, pady=(0, 4))
            ctk.CTkButton(btn_frame, text="✅ Aplicar", width=80, height=22, fg_color="#1a7a3c",
                          font=ctk.CTkFont(size=9), command=_aplicar).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="🗑", width=24, height=22, fg_color="#c0392b",
                          font=ctk.CTkFont(size=9), command=_borrar).pack(side="left", padx=2)

    def _aplicar_seed(self, seed):
        """Aplica una configuración guardada como seed."""
        if seed.get("plataforma") and hasattr(self, 'plataforma_var'):
            self.plataforma_var.set(seed["plataforma"])
        if seed.get("modelo_img") and hasattr(self, 'modelo_img_var'):
            self.modelo_img_var.set(seed["modelo_img"])
        if seed.get("modelo_vid") and hasattr(self, 'modelo_vid_var'):
            self.modelo_vid_var.set(seed["modelo_vid"])
        if seed.get("ratio") and hasattr(self, 'ratio_var'):
            self.ratio_var.set(seed["ratio"])
        self.set_estado(f"💎 Seed '{seed.get('nombre', '?')}' aplicado", "#2ecc71")

    def _autocompletar_tags(self, event=None):
        """Auto-completar tags mientras escribe."""
        texto = self.txt_salida.get("1.0", "end").strip()
        if not texto:
            return
        # Sugerir tags comunes basados en lo que escribe
        tag_sugerencias = {
            "master": "masterpiece", "best": "best quality", "ultra": "ultra detailed",
            "8k": "8K resolution", "hd": "HD", "photo": "photorealistic",
            "real": "realistic", "cinema": "cinematic lighting", "dof": "depth of field",
            "bokeh": "bokeh", "soft": "soft lighting", "dramatic": "dramatic lighting",
        }
        palabras = texto.lower().split()
        for palabra, tag in tag_sugerencias.items():
            if palabra in texto and tag not in texto:
                pass  # Podría sugerir pero no es crítico

    def _abrir_atajos_tags(self):
        """Ventana para gestionar atajos de tags (snippets)."""
        prefs = self.store.cargar_preferencias()
        atajos = prefs.get("atajos_tags", [])

        vent = ctk.CTkToplevel(self)
        vent.title("✂️ Atajos de tags")
        vent.geometry("600x450")
        vent.transient(self)

        ctk.CTkLabel(vent, text="✂️ Atajos de tags (snippets)", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text="Atajos rápidos para insertar tags comunes",
                     font=ctk.CTkFont(size=10), text_color="#888888").pack(pady=(0, 8))

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=5)

        def refrescar():
            for w in scroll.winfo_children(): w.destroy()
            for i, atajo in enumerate(atajos):
                card = ctk.CTkFrame(scroll, fg_color="#111820", corner_radius=8)
                card.pack(fill="x", pady=3)
                ctk.CTkLabel(card, text=atajo.get("nombre", "?"), font=ctk.CTkFont(size=11, weight="bold"),
                             text_color="#aaccee").pack(anchor="w", padx=10, pady=(6, 2))
                ctk.CTkLabel(card, text=atajo.get("tags", ""), font=ctk.CTkFont(size=9),
                             text_color="#888888", wraplength=500).pack(anchor="w", padx=10, pady=(0, 4))
                def _aplicar(tags=atajo.get("tags", "")):
                    self._aplicar_atajo_tags(tags)
                    vent.destroy()
                def _borrar(idx=i):
                    atajos.pop(idx)
                    prefs["atajos_tags"] = atajos
                    self.store.guardar_preferencias(prefs)
                    refrescar()
                btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                btn_frame.pack(anchor="e", padx=8, pady=(0, 4))
                ctk.CTkButton(btn_frame, text="✅ Aplicar", width=80, height=22, fg_color="#1a7a3c",
                              font=ctk.CTkFont(size=9), command=_aplicar).pack(side="left", padx=2)
                ctk.CTkButton(btn_frame, text="🗑", width=24, height=22, fg_color="#c0392b",
                              font=ctk.CTkFont(size=9), command=_borrar).pack(side="left", padx=2)

        def crear():
            vent_add = ctk.CTkToplevel(vent)
            vent_add.title("➕ Nuevo atajo")
            vent_add.geometry("400x250")
            vent_add.transient(vent)
            ctk.CTkLabel(vent_add, text="Nombre:").pack(anchor="w", padx=15, pady=(10, 2))
            ent_nombre = ctk.CTkEntry(vent_add, width=350)
            ent_nombre.pack(anchor="w", padx=15)
            ctk.CTkLabel(vent_add, text="Tags:").pack(anchor="w", padx=15, pady=(10, 2))
            ent_tags = ctk.CTkEntry(vent_add, width=350)
            ent_tags.pack(anchor="w", padx=15)
            def _guardar():
                nombre = ent_nombre.get().strip()
                tags = ent_tags.get().strip()
                if nombre and tags:
                    atajos.append({"nombre": nombre, "tags": tags})
                    prefs["atajos_tags"] = atajos
                    self.store.guardar_preferencias(prefs)
                    refrescar()
                    vent_add.destroy()
            ctk.CTkButton(vent_add, text="Guardar", width=120, height=28, fg_color="#1a7a3c",
                          command=_guardar).pack(pady=15)

        def _copiar_ej():
            pyperclip.copy("masterpiece, best quality, ultra detailed, 8K resolution")
        def _usar_ej():
            self._aplicar_atajo_tags("masterpiece, best quality, ultra detailed, 8K resolution")
            vent.destroy()

        btn_frame = ctk.CTkFrame(vent, fg_color="transparent")
        btn_frame.pack(pady=8)
        ctk.CTkButton(btn_frame, text="➕ Nuevo atajo", width=140, height=28, fg_color="#1a7a3c",
                      command=crear).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="📋 Ejemplo: copiar", width=160, height=28,
                      command=_copiar_ej).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="✅ Ejemplo: usar", width=140, height=28, fg_color="#1a7a3c",
                      command=_usar_ej).pack(side="left", padx=4)

        refrescar()

    def _copiar_comfyui_json(self):
        """Copia el prompt en formato JSON compatible con ComfyUI."""
        actual = self.txt_salida.get("1.0", "end").strip()
        if not actual:
            return self.set_estado("⚠️ Genera un prompt primero.", "#e67e22")

        pos = self.extraer_positive() or actual
        neg = self.extraer_negative() or ""

        import json
        comfy_format = {
            "3": {"inputs": {"text": pos, "seed": 42}, "class_type": "CLIPTextEncode"},
            "4": {"inputs": {"text": neg, "seed": 42}, "class_type": "CLIPTextEncode"},
        }

        pyperclip.copy(json.dumps(comfy_format, indent=2, ensure_ascii=False))
        self.set_estado("📋 JSON ComfyUI copiado", "#2ecc71")

    def _traducir_salida(self):
        """Traduce el prompt actual al español en una ventana aparte."""
        actual = self.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 10:
            return self.set_estado("⚠️ Genera un prompt primero.", "#e67e22")

        self.set_estado("🌐 Traduciendo a español...", "#f39c12")

        def _worker():
            try:
                traducido = self.deepseek.traducir_a_espanol(actual)
                self.after(0, lambda: self._mostrar_ventana_traduccion(traducido))
                self.after(0, lambda: self.set_estado("🌐 Traducción lista", "#2ecc71"))
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))

        threading.Thread(target=_worker, daemon=True).start()

    def _mostrar_ventana_traduccion(self, texto):
        """Ventana con la traducción y opciones: Usar / Copiar."""
        from config import get_theme_colors
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = ctk.CTkToplevel(self)
        vent.title("🇪🇸 Traducción al español")
        vent.geometry("580x400")
        vent.transient(self)

        marco = ctk.CTkFrame(vent, fg_color=c.get("tab_bg", "#f3f4f6" if is_lt else "#0f1318"))
        marco.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(marco, text="🇪🇸 Traducción al español",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=c["hdr_text"]).pack(anchor="w", pady=(0, 6))

        txt = ctk.CTkTextbox(marco, wrap="word", font=ctk.CTkFont(size=12),
                             fg_color=c.get("entry_bg", "#ffffff" if is_lt else "#1a1a2e"),
                             text_color=c.get("entry_text", "#111827" if is_lt else "#e5e7eb"),
                             border_color=c.get("entry_border", "#9ca3af" if is_lt else "#2a2a3e"))
        txt.insert("1.0", texto)
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=True, pady=(0, 10))

        frame_btn = ctk.CTkFrame(marco, fg_color="transparent")
        frame_btn.pack(fill="x")

        def _usar():
            self.actualizar_salida(texto)
            vent.destroy()

        def _copiar():
            import pyperclip
            pyperclip.copy(texto)
            self.set_estado("📋 Traducción copiada", "#2ecc71")

        ctk.CTkButton(frame_btn, text="✅ Usar traducción", width=130,
                      fg_color="#2563eb", hover_color="#1d4ed8",
                      command=_usar).pack(side="left", padx=(0, 6))
        ctk.CTkButton(frame_btn, text="📋 Copiar", width=100,
                      fg_color="#4b5563", hover_color="#374151",
                      command=_copiar).pack(side="left", padx=(0, 6))
        ctk.CTkButton(frame_btn, text="❌ Cerrar", width=80,
                      fg_color="#6b7280", hover_color="#4b5563",
                      command=vent.destroy).pack(side="right")

    def _mostrar_consejo_contextual(self, modelo_name, specs):
        """Muestra consejos rápidos en la barra de estado según el contexto del modelo seleccionado."""
        consejos = []
        nota = specs.get("nota", 0)
        if specs.get("modos_gen") and "Quality" in str(specs.get("modos_gen", "")):
            pass
        if not specs.get("has_negative") and not specs.get("is_natural"):
            consejos.append("💡 Modelo Turbo — usa solo tags limpios")
        elif not specs.get("has_negative") and specs.get("is_natural"):
            consejos.append("💡 Modelo natural — describe en prosa, no uses tags")
        elif specs.get("is_natural"):
            consejos.append("💡 Lenguaje natural fluido funciona mejor que tags")
        if "80" in str(specs.get("coste_energia", "")) or "Mystic" in modelo_name:
            consejos.append("⚠️ Modelo costoso (80+ créditos por imagen)")
        best_for = specs.get("best_for", "").lower()
        if "lento" in best_for or "1m" in best_for:
            consejos.append("⏱ Modelo lento (~1+ min/imagen)")
        if consejos:
            import random
            consejo = random.choice(consejos)
            self.set_estado(consejo, "#3498db")

    def _validar_compatibilidad_modelo(self):
        """Valida la compatibilidad del modelo con la configuración actual."""
        modelo = self.modelo_img_var.get() if hasattr(self, 'modelo_img_var') else ""
        if not modelo:
            return True, ""
        # Aquí iría la lógica de validación
        return True, ""

    def _actualizar_compat_inline(self):
        """Actualiza la compatibilidad inline en la UI."""
        valido, msg = self._validar_compatibilidad_modelo()
        if hasattr(self, 'lbl_compat'):
            if valido:
                self.lbl_compat.configure(text="✅ Compatible", text_color="#2ecc71")
            else:
                self.lbl_compat.configure(text=f"⚠️ {msg}", text_color="#e67e22")

    def _cmd_modal_compatibilidad(self):
        """Abre modal de compatibilidad de modelos."""
        vent = ctk.CTkToplevel(self)
        vent.title("🔍 Compatibilidad de modelos")
        vent.geometry("600x400")
        vent.transient(self)
        ctk.CTkLabel(vent, text="🔍 Compatibilidad de modelos", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(vent, text="Información de compatibilidad entre modelos y configuraciones",
                     font=ctk.CTkFont(size=10), text_color="#888888").pack(pady=(0, 10))
        # Aquí iría la tabla de compatibilidad
        ctk.CTkButton(vent, text="Cerrar", width=120, height=30, command=vent.destroy).pack(pady=15)
