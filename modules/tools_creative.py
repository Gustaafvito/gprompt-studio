"""Creative Tools Mixin - Moodboard, Client Mode, ADN Visual, Negative Builder, etc."""
import os
import re
import json
import threading
import datetime
import random
import webbrowser
import logging
import pyperclip
from PIL import Image
from collections import Counter
import customtkinter as ctk
import tkinter as tk
from config import MODELOS_IMAGEN_FLAT, MODELOS_VIDEO_FLAT, MODELOS_AUDIO_FLAT, get_image_model_specs, get_model_specs, get_audio_model_specs, get_theme_colors, ADN_A_PLATAFORMA
from workers import limpiar_marcadores

logger = logging.getLogger(__name__)
from typing import TYPE_CHECKING
from modules.gprompt_window import GPromptWindow

if TYPE_CHECKING:
    from app import ArquitectoApp

class ToolsCreativeMixin:
    """Mixin containing all creative tool methods."""

    def _cmd_sorprendeme(self):
        """Genera una idea aleatoria interesante para inspirarse."""
        modo = self.modo_var.get()
        try: self._sesion_log("🎲 Sorpréndeme: pidió idea aleatoria")
        except Exception as e:
            logger.debug(f"[silent] {e}")
        self.set_estado("🎲 Pensando algo creativo...", "#f39c12")
        self.toggle_botones(False)

        peticion = (
            f"Genera UNA SOLA idea creativa, original y visualmente interesante para un prompt de {modo}. "
            f"Debe ser una escena con: sujeto específico + acción/situación + atmósfera + un toque de originalidad. "
            f"Estilo: ni demasiado cliché ni demasiado abstracta. Algo que dé ganas de generarla. "
            f"Evita conceptos sobreusados (cyberpunk genérico, dragones simples, etc). "
            f"Responde con UNA SOLA frase en español, máximo 30 palabras, sin explicaciones."
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=1.0, max_tokens=200)
                resp = limpiar_marcadores(resp).strip().strip('"').strip("'")
                def _aplicar():
                    self.txt_idea.delete("1.0", "end")
                    self.txt_idea.insert("1.0", resp)
                    self.set_estado("🎲 Idea sorpresa generada — pulsa ✨ Generar para crear el prompt", "#2ecc71")
                    self.toggle_botones(True)
                self.after(0, _aplicar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    PULSE_PRESET_3 = [
        (0.3, "🎯 Conservador (T=0.3)"),
        (0.6, "⚖️ Equilibrado (T=0.6)"),
        (0.9, "🎨 Creativo (T=0.9)"),
    ]
    PULSE_PRESET_5 = [
        (0.2, "🧊 Ultra estable (T=0.2)"),
        (0.4, "🎯 Conservador (T=0.4)"),
        (0.6, "⚖️ Equilibrado (T=0.6)"),
        (0.8, "🎨 Creativo (T=0.8)"),
        (1.0, "🔥 Máximo riesgo (T=1.0)"),
    ]

    def _cmd_pulse(self):
        """Modo Pulse: configura N versiones con temperaturas distintas.

        Mejoras v2:
        - 3 modos: 3 niveles (default), 5 niveles, Personalizado (sliders).
        - Recuerda la última configuración usada en preferencias.
        """
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.set_estado("⚠️ Escribe una idea base primero.", "#e67e22")

        # Cargar última configuración
        prefs = self.store.cargar_preferencias()
        ultima = prefs.get("pulse_config", {"modo": "3", "custom_temps": [0.3, 0.6, 0.9]})

        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        cfg = GPromptWindow(self)
        cfg.title("⚡ Pulse — Configuración")
        cfg.geometry("440x520")
        cfg.transient(self)
        cfg.grab_set()

        ctk.CTkLabel(cfg, text="⚡ Pulse — Configuración",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 4))
        ctk.CTkLabel(cfg,
                     text="Cada nivel = un prompt con distinta temperatura.\nMenor T = más consistente, mayor T = más creativo.",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"],
                     justify="center").pack(pady=(0, 12))

        modo_var = ctk.StringVar(value=ultima.get("modo", "3"))

        # Frame para sliders custom (visible solo si modo=custom)
        custom_frame = ctk.CTkFrame(cfg, fg_color=c["fg_dark"], corner_radius=6)
        custom_sliders = []

        def _toggle_custom():
            if modo_var.get() == "custom":
                custom_frame.pack(fill="x", padx=20, pady=8)
            else:
                custom_frame.pack_forget()

        for valor, label in [("3", "3 niveles (rápido): 0.3 · 0.6 · 0.9"),
                              ("5", "5 niveles (completo): 0.2 → 1.0"),
                              ("custom", "🎚 Personalizado (sliders abajo)")]:
            ctk.CTkRadioButton(cfg, text=label, variable=modo_var, value=valor,
                               command=_toggle_custom,
                               font=ctk.CTkFont(size=11)
                               ).pack(anchor="w", padx=30, pady=4)

        # Sliders custom (3 sliders)
        ctk.CTkLabel(custom_frame, text="Temperaturas custom (3 niveles):",
                     font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=10, pady=(8, 4))
        temps_init = ultima.get("custom_temps", [0.3, 0.6, 0.9])
        for i in range(3):
            row = ctk.CTkFrame(custom_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)
            lbl_val = ctk.CTkLabel(row, text=f"T{i+1}: {temps_init[i]:.2f}",
                                    width=70, font=ctk.CTkFont(family="Consolas", size=10))
            lbl_val.pack(side="left", padx=(0, 6))
            sl = ctk.CTkSlider(row, from_=0.1, to=1.5, number_of_steps=28)
            sl.set(temps_init[i])
            sl.configure(command=lambda v, l=lbl_val, idx=i:
                          l.configure(text=f"T{idx+1}: {float(v):.2f}"))
            sl.pack(side="left", fill="x", expand=True)
            custom_sliders.append(sl)

        _toggle_custom()

        def _ejecutar():
            modo_sel = modo_var.get()
            if modo_sel == "3":
                temperaturas = list(self.PULSE_PRESET_3)
            elif modo_sel == "5":
                temperaturas = list(self.PULSE_PRESET_5)
            else:
                temps_custom = [round(sl.get(), 2) for sl in custom_sliders]
                temperaturas = [(t, f"🎚 Custom (T={t:.2f})") for t in temps_custom]
            # Guardar config
            prefs_g = self.store.cargar_preferencias()
            prefs_g["pulse_config"] = {
                "modo": modo_sel,
                "custom_temps": [round(sl.get(), 2) for sl in custom_sliders],
            }
            self.store.guardar_preferencias(prefs_g)
            cfg.destroy()
            self._lanzar_pulse(idea, temperaturas)

        btn_row = ctk.CTkFrame(cfg, fg_color="transparent")
        btn_row.pack(side="bottom", pady=(0, 15))
        ctk.CTkButton(btn_row, text="▶ Generar", width=140, height=34,
                      fg_color="#1a8a3c", hover_color="#127a30",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=_ejecutar).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Cancelar", width=100, height=34,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                      command=cfg.destroy).pack(side="left", padx=4)

        # Enter dispara generar
        cfg.bind("<Return>", lambda _e: _ejecutar())

    def _lanzar_pulse(self, idea, temperaturas):
        """Ejecuta Pulse con la lista de (temp, label) elegida."""
        try: self._sesion_log(f"⚡ Pulse: generó {len(temperaturas)} versiones")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.set_estado(f"⚡ Pulse: generando {len(temperaturas)} versiones (T={temperaturas[0][0]:.1f} → T={temperaturas[-1][0]:.1f})...",
                        "#f39c12")
        self.toggle_botones(False)

        resultados = {}

        def _generar(temp, label):
            try:
                modo = self.modo_var.get()
                specs = self.get_current_model_specs()
                max_c = specs.get("max_chars", 1500) if specs else 1500
                has_neg = specs.get("has_negative", True) if specs else True
                is_natural = specs.get("is_natural", False) if specs else False
                fmt = "lenguaje natural descriptivo" if is_natural else "tags con pesos (tag:1.2)"
                neg_str = "Genera POSITIVE y NEGATIVE." if has_neg else "Solo POSITIVE (sin NEGATIVE)."

                peticion = (
                    f"Genera un prompt de {modo} basado en: {idea}\n"
                    f"Formato: {fmt}. Límite: {max_c} chars. {neg_str}\n"
                    f"Estilos: {self.estilos_texto()}.\n"
                    f"Responde SOLO con el prompt, sin explicaciones."
                )
                resp = self.deepseek.generar(peticion, temperature=temp, max_tokens=2000)
                resp = limpiar_marcadores(resp)
                if not has_neg:
                    import re
                    resp = re.sub(r'\n?\s*NEGATIVE\s+PROMPT\s*:.*?$', '', resp, flags=re.DOTALL | re.IGNORECASE).strip()
                resultados[label] = resp
            except Exception as e:
                resultados[label] = f"❌ Error: {e}"

        def _worker_all():
            threads = []
            for temp, label in temperaturas:
                t = threading.Thread(target=_generar, args=(temp, label), daemon=True)
                t.start()
                threads.append(t)
            for t in threads:
                t.join()

            def _mostrar():
                # Construir lista para el comparador con label como "header"
                variantes = []
                for _, label in temperaturas:
                    if label in resultados:
                        variantes.append(f"### {label} ###\n{resultados[label]}")
                self._abrir_comparador(variantes)
                n = len(temperaturas)
                self.set_estado(f"⚡ Pulse: {n} versiones listas — compara y elige", "#2ecc71")
                self.toggle_botones(True)
                self._sonar_completado()
                self._notificar_sistema(f"⚡ Pulse completado",
                                         f"{n} versiones del prompt listas para comparar")
            self.after(0, _mostrar)

        threading.Thread(target=_worker_all, daemon=True).start()

    def _cmd_negative_optimo(self):
        """Genera el NEGATIVE ÓPTIMO según el modelo y tipo de prompt actual."""
        if not self._debe_mostrar_negatives():
            return self.set_estado("⚠️ El modelo actual no usa NEGATIVE PROMPT.", "#e67e22")

        modelo = self.modelo_imagen_valido() if self.modo_var.get() == "imagen" else (
            self.modelo_video_valido() if self.modo_var.get() == "video" else "")
        pos = self.extraer_positive() or self.txt_idea.get("1.0", "end").strip() or "imagen general"

        self.set_estado("🛡 Generando NEGATIVE óptimo para este modelo...", "#f39c12")
        self.toggle_botones(False)

        peticion = (
            f"Genera el NEGATIVE PROMPT MÁS COMPLETO Y ÓPTIMO para este modelo y contenido.\n\n"
            f"MODELO: {modelo}\n"
            f"POSITIVE PROMPT (contexto):\n{pos[:500]}\n\n"
            f"REGLAS:\n"
            f"- Usa pesos (tag:1.4) para las protecciones más críticas.\n"
            f"- Cubre: baja calidad, deformaciones, artefactos JPEG, anatomía mala, manos/dedos malformados.\n"
            f"- Si el positive es realista, añade tags contra anime/cartoon/3D/painting.\n"
            f"- Si el positive es anime, añade tags contra photorealistic/photograph.\n"
            f"- Si hay personas: refuerza anatomía, ojos, dedos.\n"
            f"- Si hay paisaje: protege contra distorsión y bordes pixelados.\n"
            f"- Adapta a las debilidades conocidas del modelo {modelo}.\n\n"
            f"Responde SOLO con la línea NEGATIVE PROMPT en una sola línea, sin explicaciones."
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.2, max_tokens=400)
                resp = limpiar_marcadores(resp)
                import re
                m = re.search(r'NEGATIVE\s+PROMPT\s*:?\s*(.+?)$', resp, re.DOTALL | re.IGNORECASE)
                negative = (m.group(1) if m else resp).strip()

                def _aplicar():
                    pos_actual = self.extraer_positive()
                    if pos_actual:
                        nuevo = f"POSITIVE PROMPT: {pos_actual}\nNEGATIVE PROMPT: {negative}"
                        self.actualizar_salida(nuevo)
                        self.set_estado("🛡 NEGATIVE óptimo aplicado", "#2ecc71")
                    else:
                        # Solo poner negative si no hay positive
                        pyperclip.copy(negative)
                        self.set_estado("🛡 NEGATIVE óptimo copiado al portapapeles", "#2ecc71")
                    self.toggle_botones(True)
                self.after(0, _aplicar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_sugerir_modelo(self):
        """Analiza la idea y sugiere TOP 3 modelos.

        v2:
        - Pide al LLM TOP 3 modelos rankeados (no solo 1).
        - Muestra cada uno como card clicable con razón individual.
        - Botón "✅ Usar este modelo" por card.
        - Botón global "🚀 Probar los 3" → genera el prompt con cada
          uno y abre el comparador.
        """
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 10:
            return self.set_estado("⚠️ Escribe una idea más detallada.", "#e67e22")
        try: self._sesion_log("🤖 Sugerir modelo: analizó idea")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.set_estado("🤖 Analizando idea para top 3 modelos...", "#f39c12")

        modo = self.modo_var.get()
        if modo == "imagen":
            modelos_lista = [m for m in MODELOS_IMAGEN_FLAT if not m.startswith("──")]
        elif modo == "video":
            modelos_lista = [m for m in MODELOS_VIDEO_FLAT if not m.startswith("──")]
        else:
            modelos_lista = [m for m in MODELOS_AUDIO_FLAT if not m.startswith("──")]

        # Resumen de specs para el LLM
        specs_resumen = []
        for m in modelos_lista[:20]:
            s = get_image_model_specs(m) or get_model_specs(m) or get_audio_model_specs(m) or {}
            specs_resumen.append(f"- {m}: {s.get('best_for', '')[:120]}")

        peticion = (
            f"Analiza esta idea y sugiere los 3 MEJORES modelos de {modo} rankeados.\n\n"
            f"IDEA: {idea}\n\n"
            f"MODELOS DISPONIBLES:\n" + "\n".join(specs_resumen) + "\n\n"
            f"Responde EN ESPAÑOL con este formato EXACTO (importante mantener \"#1:\", \"#2:\", \"#3:\"):\n\n"
            f"#1: [nombre exacto del modelo]\n"
            f"RAZÓN: [1 frase concreta]\n\n"
            f"#2: [nombre exacto del modelo]\n"
            f"RAZÓN: [1 frase concreta]\n\n"
            f"#3: [nombre exacto del modelo]\n"
            f"RAZÓN: [1 frase concreta]"
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.3, max_tokens=600)
                resp = limpiar_marcadores(resp)

                # Parsear las 3 sugerencias
                import re
                # Pattern: "#1: nombre\nRAZÓN: razón"
                pattern = r'#(\d)\s*:\s*([^\n]+)\n+\s*RAZ[ÓO]N\s*:\s*([^\n#]+(?:\n(?!#\d)[^\n]+)*)'
                matches = re.findall(pattern, resp, re.IGNORECASE)

                # Filtrar a modelos que existen realmente en la lista
                sugerencias = []
                for _rank, nombre, razon in matches[:3]:
                    nombre_limpio = nombre.strip().strip("[").strip("]").strip()
                    razon_limpia = razon.strip()
                    # Match exacto o por contenedor
                    coincidencia = None
                    if nombre_limpio in modelos_lista:
                        coincidencia = nombre_limpio
                    else:
                        # Búsqueda case-insensitive
                        nl_lower = nombre_limpio.lower()
                        for m_real in modelos_lista:
                            if nl_lower == m_real.lower() or nl_lower in m_real.lower():
                                coincidencia = m_real
                                break
                    if coincidencia:
                        sugerencias.append((coincidencia, razon_limpia))

                if not sugerencias:
                    self.after(0, lambda: self.set_estado(
                        "⚠️ No se pudieron parsear las sugerencias del LLM",
                        "#e67e22"))
                    return

                def _mostrar():
                    self._mostrar_sugerencias_modelo(idea, sugerencias, modo)
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))

        threading.Thread(target=_worker, daemon=True).start()

    def _mostrar_sugerencias_modelo(self, idea, sugerencias, modo):
        """Modal con las 3 sugerencias de modelo + botón para probar los 3."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self)
        vent.title("🤖 Top 3 modelos sugeridos")
        vent.geometry("680x520")
        vent.transient(self)

        ctk.CTkLabel(vent, text="🤖 Top 3 modelos para tu idea",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4))
        ctk.CTkLabel(vent, text=f"Idea: {idea[:80]}{'…' if len(idea) > 80 else ''}",
                     font=ctk.CTkFont(size=10, slant="italic"),
                     text_color=c["muted_text"]).pack(pady=(0, 10))

        # Colores y rankings
        rank_data = [
            ("🥇", "#fbbf24", "#1a1a2e"),  # oro
            ("🥈", "#94a3b8", "#1a1a2e"),  # plata
            ("🥉", "#cd7f32", "#1a1a2e"),  # bronce
        ]

        def _aplicar_modelo(nombre):
            if modo == "imagen" and hasattr(self, 'combo_modelo_imagen'):
                self.combo_modelo_imagen.set(nombre)
                self._on_modelo_imagen_cambio()
            elif modo == "video" and hasattr(self, 'combo_modelo_video'):
                self.combo_modelo_video.set(nombre)
            elif modo == "audio" and hasattr(self, 'combo_modelo_audio'):
                self.combo_modelo_audio.set(nombre)
            vent.destroy()
            self.set_estado(f"✅ Modelo '{nombre}' aplicado", "#2ecc71")

        for idx, (nombre_mod, razon) in enumerate(sugerencias):
            medalla, bg_medalla, fg_medalla = rank_data[idx] if idx < 3 else ("#", c["fg_dark"], c["hdr_text"])
            card = ctk.CTkFrame(vent, fg_color=c["fg_frame"], corner_radius=8,
                                 border_color=bg_medalla, border_width=2)
            card.pack(fill="x", pady=6, padx=12)

            hdr = ctk.CTkFrame(card, fg_color="transparent")
            hdr.pack(fill="x", padx=10, pady=(8, 2))
            ctk.CTkLabel(hdr, text=f"  {medalla} {nombre_mod}",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=bg_medalla).pack(side="left")

            ctk.CTkLabel(card, text=f"  💡 {razon}",
                         font=ctk.CTkFont(size=10),
                         text_color=c["muted_text"],
                         wraplength=620, justify="left",
                         anchor="w").pack(fill="x", padx=10, pady=(0, 6))

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=10, pady=(0, 8))
            ctk.CTkButton(btn_row, text=f"✅ Usar este modelo",
                          width=180, height=28,
                          fg_color="#1a8a3c", hover_color="#127a30",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          command=lambda n=nombre_mod: _aplicar_modelo(n)
                          ).pack(side="left", padx=2)

        # Botón "Probar los 3" — genera el prompt con cada modelo y compara
        def _probar_los_3():
            vent.destroy()
            modelos_a_probar = [n for n, _ in sugerencias]
            self._probar_modelos_y_comparar(idea, modelos_a_probar, modo)

        accion_row = ctk.CTkFrame(vent, fg_color="transparent")
        accion_row.pack(side="bottom", pady=(8, 12))
        ctk.CTkButton(accion_row, text=f"🚀 Probar los {len(sugerencias)} en paralelo",
                      width=240, height=34,
                      fg_color="#7c3aed", hover_color="#5d2ab5",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      command=_probar_los_3).pack(side="left", padx=4)
        ctk.CTkButton(accion_row, text="Cerrar", width=100, height=34,
                      fg_color=c["fg_dark"],
                      command=vent.destroy).pack(side="left", padx=4)

    def _probar_modelos_y_comparar(self, idea, modelos, modo):
        """Genera el prompt con cada modelo en paralelo y abre el comparador."""
        self.set_estado(f"🚀 Generando con {len(modelos)} modelos en paralelo...",
                        "#f39c12")
        self.toggle_botones(False)

        resultados = {}

        def _gen_modelo(nombre_mod):
            try:
                from config import get_image_model_specs as _gim, get_model_specs as _gms
                specs = _gim(nombre_mod) or _gms(nombre_mod) or {}
                max_c = specs.get("max_chars", 1500)
                has_neg = specs.get("has_negative", True)
                is_natural = specs.get("is_natural", False)
                best_for = specs.get("best_for", "")[:200] if specs else ""

                fmt = "lenguaje natural descriptivo en una sola línea" if is_natural else "tags separados por comas con pesos opcionales (tag:1.2)"
                # Petición ESTRICTA — el bug anterior era que el LLM
                # devolvía POSITIVE+NEGATIVE+prosa+POSITIVE concatenados.
                # Aquí forzamos UNA sola sección sin texto adicional.
                if has_neg:
                    estructura = (
                        "DEVUELVE EXACTAMENTE 2 LÍNEAS y nada más:\n"
                        "Línea 1: POSITIVE PROMPT: <prompt en una línea>\n"
                        "Línea 2: NEGATIVE PROMPT: <negative en una línea>"
                    )
                else:
                    estructura = (
                        "DEVUELVE EXACTAMENTE 1 LÍNEA y nada más:\n"
                        "Línea 1: POSITIVE PROMPT: <prompt en una línea>"
                    )
                peticion = (
                    f"Genera UN prompt de {modo} optimizado para este modelo concreto:\n\n"
                    f"MODELO: {nombre_mod}\n"
                    f"FORTALEZAS: {best_for}\n\n"
                    f"IDEA: {idea}\n"
                    f"ESTILOS A INCLUIR: {self.estilos_texto()}\n\n"
                    f"REGLAS ESTRICTAS:\n"
                    f"- Formato: {fmt}\n"
                    f"- Límite POSITIVE: {max_c} caracteres\n"
                    f"- Aprovecha las fortalezas del modelo {nombre_mod}\n"
                    f"- NO añadas explicaciones, NO añadas prosa descriptiva\n"
                    f"- NO repitas la sección POSITIVE/NEGATIVE\n\n"
                    f"{estructura}"
                )
                resp = self.deepseek.generar(peticion, temperature=0.55, max_tokens=1500)
                resp = limpiar_marcadores(resp)

                # Defensa contra LLMs que devuelven texto extra:
                # cortar SOLO al primer bloque POSITIVE [+ NEGATIVE].
                import re
                m_pos = re.search(r'POSITIVE\s+PROMPT\s*:\s*(.+?)(?=\n\s*NEGATIVE\s+PROMPT\s*:|\n\s*POSITIVE\s+PROMPT\s*:|\Z)',
                                  resp, flags=re.DOTALL | re.IGNORECASE)
                m_neg = re.search(r'NEGATIVE\s+PROMPT\s*:\s*(.+?)(?=\n\s*POSITIVE\s+PROMPT\s*:|\n\s*NEGATIVE\s+PROMPT\s*:|\Z)',
                                  resp, flags=re.DOTALL | re.IGNORECASE)
                if m_pos:
                    pos_clean = " ".join(m_pos.group(1).split())[:max_c * 2]  # margen de seguridad
                    if has_neg and m_neg:
                        neg_clean = " ".join(m_neg.group(1).split())
                        resp_limpio = f"POSITIVE PROMPT: {pos_clean}\nNEGATIVE PROMPT: {neg_clean}"
                    else:
                        resp_limpio = f"POSITIVE PROMPT: {pos_clean}"
                else:
                    # Fallback: respuesta sin etiquetas claras — asumir todo es POSITIVE
                    pos_clean = " ".join(resp.split())[:max_c * 2]
                    resp_limpio = f"POSITIVE PROMPT: {pos_clean}"

                resultados[nombre_mod] = resp_limpio
            except Exception as e:
                resultados[nombre_mod] = f"❌ Error: {e}"

        def _worker_all():
            threads = []
            for nombre in modelos:
                t = threading.Thread(target=_gen_modelo, args=(nombre,), daemon=True)
                t.start()
                threads.append(t)
            for t in threads:
                t.join()

            def _mostrar():
                variantes = []
                labels = []
                for nombre in modelos:
                    if nombre in resultados:
                        variantes.append(resultados[nombre])
                        labels.append(f"🏆 {nombre}")
                # Detectar si las respuestas son sospechosamente idénticas
                # (mismo POSITIVE → LLM no diferenció entre modelos)
                if len(set(resultados.values())) == 1 and len(resultados) > 1:
                    self.set_estado(
                        "⚠️ El LLM devolvió la misma respuesta para todos los modelos. Prueba con una idea más específica.",
                        "#e67e22")
                self._abrir_comparador(variantes, labels=labels)
                self.set_estado(f"🚀 {len(modelos)} versiones listas — elige tu favorita",
                                "#2ecc71")
                self.toggle_botones(True)
                self._sonar_completado()
            self.after(0, _mostrar)

        threading.Thread(target=_worker_all, daemon=True).start()

    def _cmd_solo_negative(self):
        """Genera solo el NEGATIVE PROMPT optimizado."""
        if not self._debe_mostrar_negatives():
            return self.set_estado("⚠️ Este modelo no usa NEGATIVE.", "#e67e22")

        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.set_estado("⚠️ Escribe una idea base primero.", "#e67e22")

        self.set_estado("🛡 Generando NEGATIVE optimizado...", "#f39c12")
        self.toggle_botones(False)

        modelo = self.modelo_imagen_valido() if self.modo_var.get() == "imagen" else (
            self.modelo_video_valido() if self.modo_var.get() == "video" else "")

        peticion = (
            f"Genera un NEGATIVE PROMPT optimizado para este modelo y contenido.\n\n"
            f"MODELO: {modelo}\n"
            f"IDEA BASE: {idea}\n\n"
            f"REGLAS:\n"
            f"- Usa pesos (tag:1.4) para las protecciones más importantes.\n"
            f"- Cubre: calidad baja, deformaciones, anatomía, manos, dedos, cara.\n"
            f"- Adapta según el modelo y tipo de contenido.\n\n"
            f"Responde SOLO con el NEGATIVE PROMPT, sin explicaciones."
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.3, max_tokens=400)
                resp = limpiar_marcadores(resp)
                import re
                m = re.search(r'NEGATIVE\s+PROMPT\s*:?\s*(.+?)$', resp, re.DOTALL | re.IGNORECASE)
                negative = (m.group(1) if m else resp).strip()

                def _aplicar():
                    pyperclip.copy(negative)
                    self.set_estado("🛡 NEGATIVE copiado al portapapeles", "#2ecc71")
                    self.toggle_botones(True)
                self.after(0, _aplicar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_grupo_personajes(self):
        """Define una escena con varios personajes y sus relaciones."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        vent = GPromptWindow(self)
        vent.title("👥 Grupo de personajes")
        vent.geometry("600x500")
        vent.transient(self)

        ctk.CTkLabel(vent, text="👥 Definir grupo de personajes", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text="Define hasta 3 personajes que aparecerán juntos en la escena",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 10))

        personajes_data = []
        # Cargar personajes existentes
        personajes_lista = ["— Personaje nuevo —"] + [p.get("nombre", "?") for p in (self.store.personajes or [])]

        for i in range(3):
            f = ctk.CTkFrame(vent, fg_color=c["fg_frame"], corner_radius=6)
            f.pack(fill="x", padx=15, pady=4)

            ctk.CTkLabel(f, text=f"Personaje #{i+1}:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(5, 2))

            row = ctk.CTkFrame(f, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)
            cb = ctk.CTkComboBox(row, values=personajes_lista, width=200, height=26)
            cb.set(personajes_lista[0])
            cb.pack(side="left", padx=(0, 5))

            ent_desc = ctk.CTkEntry(row, placeholder_text="Posición/acción (ej: 'a la izquierda, mirando al frente')", width=350, height=26)
            ent_desc.pack(side="left")

            personajes_data.append({"combo": cb, "desc": ent_desc})

        # Relación entre ellos — CTkTextbox no tiene placeholder_text nativo
        # así que simulamos uno: texto inicial gris, se borra al hacer focus.
        # Antes el placeholder se colaba en la idea generada si el usuario
        # no lo borraba manualmente.
        ctk.CTkLabel(vent, text="Relación / contexto entre ellos:",
                     font=ctk.CTkFont(size=11, weight="bold")
                     ).pack(anchor="w", padx=15, pady=(10, 2))
        txt_relacion = ctk.CTkTextbox(vent, height=60,
                                       font=ctk.CTkFont(size=11))
        txt_relacion.pack(fill="x", padx=15, pady=(0, 8))

        _placeholder_relacion = "ej: están negociando un contrato, primero plano de uno, los otros al fondo desenfocados"
        _relacion_state = {"placeholder_visible": True}
        _color_normal = txt_relacion.cget("text_color")

        def _mostrar_placeholder():
            txt_relacion.delete("1.0", "end")
            txt_relacion.insert("1.0", _placeholder_relacion)
            txt_relacion.configure(text_color="#6b7280")
            _relacion_state["placeholder_visible"] = True

        def _on_focus_in(_e=None):
            if _relacion_state["placeholder_visible"]:
                txt_relacion.delete("1.0", "end")
                txt_relacion.configure(text_color=_color_normal)
                _relacion_state["placeholder_visible"] = False

        def _on_focus_out(_e=None):
            if not txt_relacion.get("1.0", "end").strip():
                _mostrar_placeholder()

        _mostrar_placeholder()
        txt_relacion.bind("<FocusIn>", _on_focus_in)
        txt_relacion.bind("<FocusOut>", _on_focus_out)

        def _generar_grupo():
            personajes_def = []
            for i, p in enumerate(personajes_data):
                nombre_p = p["combo"].get()
                desc_p = p["desc"].get().strip()
                if nombre_p and nombre_p != "— Personaje nuevo —":
                    # Buscar el personaje en la base de datos
                    pers = next((x for x in (self.store.personajes or []) if x.get("nombre") == nombre_p), None)
                    if pers:
                        personajes_def.append({
                            "nombre": nombre_p,
                            "rasgos": pers.get("rasgos", ""),
                            "posicion": desc_p,
                        })
                    else:
                        personajes_def.append({"nombre": nombre_p, "rasgos": "", "posicion": desc_p})
                elif desc_p:
                    personajes_def.append({"nombre": f"Personaje #{i+1}", "rasgos": "", "posicion": desc_p})

            if len(personajes_def) < 2:
                self.set_estado("⚠️ Define al menos 2 personajes para hacer un grupo.", "#e67e22")
                return

            # Si el placeholder sigue visible, la relación se considera vacía
            relacion = "" if _relacion_state["placeholder_visible"] else txt_relacion.get("1.0", "end").strip()

            # Construir idea para el campo de idea
            idea_compuesta = f"Escena con {len(personajes_def)} personajes. "
            for p in personajes_def:
                idea_compuesta += f"{p['nombre']}"
                if p.get("rasgos"):
                    idea_compuesta += f" ({p['rasgos']})"
                idea_compuesta += f" {p.get('posicion', '')}. "
            if relacion:
                idea_compuesta += f"Contexto: {relacion}"

            self.txt_idea.delete("1.0", "end")
            self.txt_idea.insert("1.0", idea_compuesta)
            vent.destroy()
            self.set_estado(f"👥 {len(personajes_def)} personajes preparados — pulsa ✨ Generar", "#2ecc71")

        ctk.CTkButton(vent, text="✅ Aplicar a la idea", width=200, height=32,
                      fg_color="#1a7a3c", hover_color="#145e2d",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=_generar_grupo).pack(pady=10)

    def _cmd_analisis_inverso(self):
        """Compara una imagen con el prompt actual: ¿el prompt describe esa imagen?"""
        if not self.imagen_cargada:
            self.set_estado("⚠️ Carga una imagen primero (panel imagen ref).", "#e67e22")
            return
        prompt_actual = self.txt_salida.get("1.0", "end").strip()
        if not prompt_actual or len(prompt_actual) < 20:
            self.set_estado("⚠️ Necesitas un prompt en el resultado para comparar.", "#e67e22")
            return
        try: self._sesion_log("🔍 Análisis inverso: comparó imagen con prompt actual")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.set_estado("🔍 Análisis inverso: comparando imagen y prompt...", "#f39c12")
        self.toggle_botones(False)

        def _worker():
            try:
                # 1. Describir la imagen primero
                def on_status(msg): self.after(0, lambda: self.set_estado(msg, "#f39c12"))
                desc, motor = self.vision.describir(self.imagen_cargada, "imagen", on_status)

                # 2. Pedir al LLM comparar prompt con descripción
                peticion = (
                    f"Tienes DOS entradas: el análisis visual de una imagen y un prompt que supuestamente la describe.\n\n"
                    f"📷 ANÁLISIS VISUAL DE LA IMAGEN:\n{desc}\n\n"
                    f"📝 PROMPT QUE SUPUESTAMENTE LA DESCRIBE:\n{prompt_actual}\n\n"
                    f"Tu tarea: ANALIZAR si el prompt realmente describe lo que se ve en la imagen.\n\n"
                    f"FORMATO DE RESPUESTA en español:\n"
                    f"COINCIDENCIA: X/100% (porcentaje de coincidencia)\n\n"
                    f"✅ ELEMENTOS QUE COINCIDEN (3-5 puntos):\n"
                    f"   - Lista los elementos del prompt que SÍ se ven en la imagen\n\n"
                    f"❌ ELEMENTOS QUE FALTAN EN EL PROMPT (3-5 puntos):\n"
                    f"   - Lista cosas visibles en la imagen pero NO mencionadas en el prompt\n\n"
                    f"⚠️ ELEMENTOS DEL PROMPT QUE NO ESTÁN EN LA IMAGEN (3-5 puntos):\n"
                    f"   - Lista cosas que el prompt menciona pero NO se ven en la imagen\n\n"
                    f"🔧 PROMPT CORREGIDO:\n"
                    f"   - Reescribe el prompt para que describa fielmente la imagen real\n"
                    f"   - Mantén el formato original (tags/natural)\n"
                )
                resp = self.deepseek.generar(peticion, temperature=0.3, max_tokens=2500)
                resp = limpiar_marcadores(resp)

                def _mostrar():
                    is_lt = ctk.get_appearance_mode().lower() == "light"
                    c = get_theme_colors(is_lt)
                    vent = GPromptWindow(self)
                    vent.title("🔍 Análisis inverso")
                    vent.geometry("700x600")
                    vent.transient(self)
                    ctk.CTkLabel(vent, text="🔍 Análisis inverso: imagen vs prompt", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
                    ctk.CTkLabel(vent, text=f"Visión: {motor}", font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

                    txt = ctk.CTkTextbox(vent, font=ctk.CTkFont(size=11), wrap="word")
                    txt.pack(fill="both", expand=True, padx=15, pady=(0, 5))
                    txt.insert("1.0", resp)
                    txt.configure(state="disabled")

                    btn_frame = ctk.CTkFrame(vent, fg_color="transparent")
                    btn_frame.pack(pady=10)
                    ctk.CTkButton(btn_frame, text="📋 Copiar análisis", width=140, height=28,
                                  command=lambda: (pyperclip.copy(resp), self.set_estado("📋 Copiado", "#2ecc71"))).pack(side="left", padx=4)

                    def _aplicar_corregido():
                        import re
                        m = re.search(r'PROMPT\s+CORREGIDO[:\s]*\n(.+?)(?=\Z)', resp, re.DOTALL | re.IGNORECASE)
                        if m:
                            corregido = m.group(1).strip()
                            self.actualizar_salida(corregido)
                            vent.destroy()
                            self.set_estado("✅ Prompt corregido aplicado", "#2ecc71")
                        else:
                            self.set_estado("⚠️ No se encontró prompt corregido", "#e67e22")

                    ctk.CTkButton(btn_frame, text="✅ Aplicar corregido", width=140, height=28, fg_color="#1a7a3c",
                                  command=_aplicar_corregido).pack(side="left", padx=4)

                    self.toggle_botones(True)
                    self.set_estado(f"🔍 Análisis inverso completado (visión: {motor})", "#2ecc71")
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_ver_biblioteca_adn(self):
        """Muestra la biblioteca de ADNs guardados, con refresh sin recargar."""
        prefs = self.store.cargar_preferencias()
        adns = prefs.get("adns_guardados", [])

        vent = GPromptWindow(self)
        vent.title("📚 Biblioteca de ADNs")
        vent.geometry("720x540")
        vent.transient(self)

        is_light = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_light)

        # Header con contador dinámico
        hdr = ctk.CTkFrame(vent, fg_color=c["fg_dark"])
        hdr.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(hdr, text="🧬 ADNs Guardados",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        contador_var = ctk.StringVar(value=f"{len(adns)} guardado(s)")
        ctk.CTkLabel(hdr, textvariable=contador_var,
                     text_color=c["muted_text"]).pack(side="right", padx=10)

        # Buscador
        search_row = ctk.CTkFrame(vent, fg_color="transparent")
        search_row.pack(fill="x", padx=10, pady=(0, 4))
        ctk.CTkLabel(search_row, text="🔍").pack(side="left", padx=(0, 6))
        entry_buscar = ctk.CTkEntry(search_row,
                                    placeholder_text="Buscar por nombre, sujeto, estética…",
                                    height=28)
        entry_buscar.pack(side="left", fill="x", expand=True)
        busqueda_pending = {"after_id": None}
        def _on_buscar(_e=None):
            if busqueda_pending["after_id"]:
                try: vent.after_cancel(busqueda_pending["after_id"])
                except Exception as _e2: logger.debug(f"[silent] {_e2}")
            busqueda_pending["after_id"] = vent.after(200, _refrescar)
        entry_buscar.bind("<KeyRelease>", _on_buscar)
        ctk.CTkButton(search_row, text="✕", width=32, height=28,
                      fg_color="#444", hover_color="#222",
                      command=lambda: (entry_buscar.delete(0, "end"), _refrescar())
                      ).pack(side="left", padx=(6, 0))

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        def _refrescar():
            """Repinta la lista sin cerrar la ventana."""
            for w in scroll.winfo_children():
                w.destroy()
            prefs_act = self.store.cargar_preferencias()
            adns_act = prefs_act.get("adns_guardados", [])
            termino = entry_buscar.get().strip().lower()

            # Filtrar por término
            visibles = []
            for idx, item in enumerate(adns_act):
                if termino:
                    nombre_b = item.get("nombre", "").lower()
                    adn_b = item.get("adn", {})
                    sujeto_b = adn_b.get("sujeto", {}) if isinstance(adn_b, dict) else {}
                    if isinstance(sujeto_b, list): sujeto_b = sujeto_b[0] if sujeto_b else {}
                    tipo_b = (sujeto_b.get("tipo", "") if isinstance(sujeto_b, dict) else "").lower()
                    estilo_b = adn_b.get("estilo", {}) if isinstance(adn_b, dict) else {}
                    estetica_b = (estilo_b.get("estetica", "") if isinstance(estilo_b, dict) else "").lower()
                    if (termino not in nombre_b and termino not in tipo_b
                            and termino not in estetica_b):
                        continue
                visibles.append((idx, item))

            sufijo = "" if not termino else f" ({len(visibles)} resultados)"
            contador_var.set(f"{len(adns_act)} guardado(s){sufijo}")

            if not visibles:
                msg = (f"Sin resultados para '{termino}'" if termino
                       else "(sin ADNs guardados)")
                ctk.CTkLabel(scroll, text=msg,
                             text_color=c["muted_text"]).pack(pady=30)
                return

            for idx, item in visibles:
                nombre = item.get("nombre", f"ADN {idx+1}")
                fecha = item.get("fecha", "")
                motor = item.get("motor", "")
                adn_data = item.get("adn", {})

                # ADN texto libre (guardado desde _cmd_anclaje_visual) vs ADN estructurado
                es_texto_libre = isinstance(adn_data, dict) and "texto_libre" in adn_data
                if es_texto_libre:
                    texto_preview = (adn_data.get("texto_libre", "") or "").strip()[:80]
                    tipo, estetica = "📝 Texto libre", texto_preview
                else:
                    sujeto = adn_data.get("sujeto", {}) if isinstance(adn_data, dict) else {}
                    if isinstance(sujeto, list):
                        sujeto = sujeto[0] if sujeto else {}
                    tipo = sujeto.get("tipo", "") if isinstance(sujeto, dict) else ""
                    estilo = adn_data.get("estilo", {}) if isinstance(adn_data, dict) else {}
                    estetica = estilo.get("estetica", "") if isinstance(estilo, dict) else ""

                card = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=8)
                card.pack(fill="x", pady=5)

                info_frame = ctk.CTkFrame(card, fg_color="transparent")
                info_frame.pack(fill="x", padx=10, pady=8)
                ctk.CTkLabel(info_frame, text=nombre,
                             font=ctk.CTkFont(weight="bold")).pack(anchor="w")
                ctk.CTkLabel(info_frame, text=f"{tipo} • {estetica}",
                             text_color=c["muted_text"],
                             font=ctk.CTkFont(size=11)).pack(anchor="w")
                ctk.CTkLabel(info_frame, text=f"{fecha} • {motor}",
                             text_color=c["muted_text"],
                             font=ctk.CTkFont(size=10)).pack(anchor="w")

                btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                btn_frame.pack(fill="x", padx=10, pady=(0, 8))

                def _cargar(idx_l=idx, item_l=item, nombre_l=nombre):
                    ver = GPromptWindow(self)
                    ver.title(f"📋 {item_l.get('nombre', 'ADN')}")
                    ver.geometry("620x520")
                    ver.transient(self)

                    import json
                    json_str = json.dumps(item_l.get("adn", {}), indent=2, ensure_ascii=False)

                    txt = ctk.CTkTextbox(ver, font=ctk.CTkFont(family="Consolas", size=11),
                                         wrap="none")
                    txt.pack(fill="both", expand=True, padx=10, pady=10)
                    txt.insert("1.0", json_str)
                    txt.configure(state="disabled")

                    def _usar_en_idea():
                        # ADN texto libre: inserta el texto tal cual
                        adn_obj = item_l.get("adn", {})
                        if isinstance(adn_obj, dict) and "texto_libre" in adn_obj:
                            txt_libre = (adn_obj.get("texto_libre", "") or "").strip()
                            if hasattr(self, "txt_idea") and txt_libre:
                                self.txt_idea.delete("1.0", "end")
                                self.txt_idea.insert("1.0", txt_libre)
                            ver.destroy()
                            self.set_estado(f"🧬 '{nombre_l}' cargado en idea (texto libre)",
                                            "#2ecc71")
                            return
                        # ADN estructurado: construir prompt aprovechando campos
                        partes = []
                        def _add(seccion, campos):
                            sec = adn_obj.get(seccion, {})
                            if not isinstance(sec, dict):
                                return
                            for campo in campos:
                                v = sec.get(campo)
                                if v and isinstance(v, str):
                                    partes.append(v)
                        _add("sujeto", ["tipo", "rasgos"])
                        _add("escena", ["ubicacion", "ambiente"])
                        _add("iluminacion", ["tipo", "intensidad"])
                        _add("estilo", ["estetica", "tecnica"])
                        _add("camara", ["tipo_plano", "angulo"])
                        _add("composicion", ["regla"])
                        prompt = ", ".join(p for p in partes if p)
                        if hasattr(self, "txt_idea"):
                            self.txt_idea.delete("1.0", "end")
                            self.txt_idea.insert("1.0", prompt)
                        ver.destroy()
                        self.set_estado(f"🧬 '{nombre_l}' cargado en idea ({len(partes)} campos)",
                                        "#2ecc71")

                    btn_frame2 = ctk.CTkFrame(ver, fg_color="transparent")
                    btn_frame2.pack(pady=(0, 10))
                    ctk.CTkButton(btn_frame2, text="🎯 Usar en idea",
                                  command=_usar_en_idea).pack(side="left", padx=5)
                    ctk.CTkButton(btn_frame2, text="Cerrar",
                                  command=ver.destroy).pack(side="left", padx=5)

                def _borrar(idx_l=idx, nombre_l=nombre):
                    from tkinter import messagebox
                    if not messagebox.askyesno("Eliminar",
                                               f"¿Borrar '{nombre_l}'?",
                                               parent=vent):
                        return
                    prefs_b = self.store.cargar_preferencias()
                    lst = prefs_b.get("adns_guardados", [])
                    if 0 <= idx_l < len(lst):
                        lst.pop(idx_l)
                        prefs_b["adns_guardados"] = lst
                        self.store.guardar_preferencias(prefs_b)
                    _refrescar()  # FIX: antes vent.destroy() cerraba la ventana
                    self.set_estado(f"🧬 '{nombre_l}' eliminado", "#e67e22")

                ctk.CTkButton(btn_frame, text="👁 Ver", width=70, height=25,
                              command=_cargar).pack(side="left", padx=2)
                ctk.CTkButton(btn_frame, text="🗑", width=40, height=25,
                              fg_color="#c0392b", hover_color="#e74c3c",
                              command=_borrar).pack(side="right", padx=2)

        _refrescar()

        # ── Botones de acción ──
        accion_frame = ctk.CTkFrame(vent, fg_color="transparent")
        accion_frame.pack(pady=10)

        def _crear_nuevo_adn():
            # ADN se extrae de imagen: requiere imagen cargada.
            if not getattr(self, "imagen_cargada", None):
                self.set_estado(
                    "⚠️ Carga una imagen en la pantalla principal y vuelve.",
                    "#e67e22",
                )
                return
            vent.destroy()
            # _cmd_adn_visual abre su propio modal con botón "💾 Guardar".
            self._cmd_adn_visual()

        ctk.CTkButton(accion_frame, text="➕ Crear nuevo ADN",
                      width=180, height=28, fg_color="#1a5a8a",
                      command=_crear_nuevo_adn).pack(side="left", padx=4)
        ctk.CTkButton(accion_frame, text="🔄 Refrescar", width=110, height=28,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                      command=_refrescar).pack(side="left", padx=4)
        ctk.CTkButton(accion_frame, text="Cerrar", width=110, height=28,
                      command=vent.destroy).pack(side="left", padx=4)

    def _cmd_adn_visual(self):
        """Extrae ADN visual JSON estructurado de la imagen cargada."""
        if not hasattr(self, 'imagen_cargada') or not self.imagen_cargada:
            return self.set_estado("⚠️ Carga una imagen primero.", "#e67e22")

        self.set_estado("🧬 Extrayendo ADN visual...", "#9b59b6")
        self.toggle_botones(False)

        def _worker():
            try:
                import json

                def on_status(msg):
                    self.after(0, lambda: self.set_estado(f"🧬 {msg}", "#9b59b6"))

                adn, motor = self.vision.analizar_adn(self.imagen_cargada, on_status)

                def _mostrar():
                    is_lt = ctk.get_appearance_mode().lower() == "light"
                    from config import get_theme_colors
                    c = get_theme_colors(is_lt)

                    vent = GPromptWindow(self)
                    vent.title("🧬 ADN Visual - Análisis estructurado")
                    vent.geometry("700x650")
                    vent.transient(self)

                    ctk.CTkLabel(vent, text="🧬 ADN Visual de tu imagen",
                                 font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(12, 5))
                    ctk.CTkLabel(vent, text=f"Analizado con: {motor}",
                                 font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

                    # Categorías bloqueables
                    categorias = [
                        ("sujeto", "👤 Sujeto"),
                        ("escena", "🌅 Escena"),
                        ("iluminacion", "💡 Iluminación"),
                        ("camara", "📷 Cámara"),
                        ("estilo", "🎨 Estilo"),
                        ("composicion", "📐 Composición"),
                        ("atmosfera", "🌫️ Atmósfera"),
                        ("tecnico", "⚙️ Técnico"),
                    ]

                    # Diccionario de bloqueos (inicial todo desbloqueado)
                    bloqueos = {}

                    scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
                    scroll.pack(fill="both", expand=True, padx=10, pady=5)

                    for cat_key, cat_nombre in categorias:
                        datos = adn.get(cat_key, {})
                        if not datos:
                            continue

                        # Frame de la categoría
                        cat_frame = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=6)
                        cat_frame.pack(fill="x", pady=4, padx=5)

                        # Header con candado
                        hdr = ctk.CTkFrame(cat_frame, fg_color="transparent")
                        hdr.pack(fill="x", padx=8, pady=(6, 0))

                        # Estado de bloqueo
                        bloqueos[cat_key] = {"bloqueado": False, "label": None, "btn": None}

                        # Fix: el btn_lock se captura como default-arg para
                        # evitar late-binding del loop (antes el icono del
                        # candado solo cambiaba en el último botón creado).
                        def _toggle_bloqueo(key=cat_key):
                            bloqueos[key]["bloqueado"] = not bloqueos[key]["bloqueado"]
                            icono = "🔒" if bloqueos[key]["bloqueado"] else "🔓"
                            color = "#c0392b" if bloqueos[key]["bloqueado"] else "#27ae60"
                            btn_ref = bloqueos[key].get("btn")
                            if btn_ref is not None:
                                btn_ref.configure(text=icono, fg_color=color)
                            estado = "🔒 BLOQUEADO" if bloqueos[key]["bloqueado"] else "🔓 DESBLOQUEADO"
                            bloqueos[key]["label"].configure(text=estado, text_color=color)

                        btn_lock = ctk.CTkButton(hdr, text="🔓", width=30, height=22,
                                                 fg_color="#27ae60", hover_color="#2ecc71",
                                                 command=_toggle_bloqueo)
                        btn_lock.pack(side="left", padx=(0, 5))
                        bloqueos[cat_key]["btn"] = btn_lock

                        # Etiqueta de estado
                        estado_lbl = ctk.CTkLabel(hdr, text="🔓 DESBLOQUEADO", text_color="#27ae60", font=ctk.CTkFont(size=9))
                        estado_lbl.pack(side="left", padx=(2, 0))
                        bloqueos[cat_key]["label"] = estado_lbl

                        ctk.CTkLabel(hdr, text=cat_nombre, font=ctk.CTkFont(weight="bold")).pack(side="left")

                        # Contenido de la categoría
                        if isinstance(datos, dict):
                            for k, v in datos.items():
                                if v:
                                    txt = f"  {k}: {v}"
                                    ctk.CTkLabel(cat_frame, text=txt, font=ctk.CTkFont(size=10),
text_color=c.get("fg_dark_text", "#ffffff"), anchor="w").pack(anchor="w", padx=12, pady=1)
                        elif isinstance(datos, list) and datos:
                            for item in datos[:5]:
                                ctk.CTkLabel(cat_frame, text=f"  • {item}", font=ctk.CTkFont(size=10),
                                            text_color=c["text"], anchor="w").pack(anchor="w", padx=12, pady=1)
                        elif isinstance(datos, str) and datos:
                            ctk.CTkLabel(cat_frame, text=f"  {datos}", font=ctk.CTkFont(size=10),
                                        text_color=c["text"], anchor="w").pack(anchor="w", padx=12, pady=1)

                    # Botones de acción
                    btn_frame = ctk.CTkFrame(vent, fg_color="transparent")
                    btn_frame.pack(pady=10)

                    def _copiar_json():
                        import json
                        json_str = json.dumps(adn, indent=2, ensure_ascii=False)
                        import pyperclip
                        pyperclip.copy(json_str)
                        self.set_estado("🧬 JSON copiado", "#2ecc71")

                    def _usar_en_prompt():
                        # Convertir ADN a prompt detallado
                        partes = []

                        # SUJETO - solo si no está bloqueado
                        if not bloqueos.get("sujeto", {}).get("bloqueado", False):
                            sujeto = adn.get("sujeto", {})
                            if isinstance(sujeto, list):
                                sujeto = sujeto[0] if sujeto else {}
                            if sujeto:
                                if sujeto.get("tipo"):
                                    partes.append(sujeto.get("tipo"))
                                if sujeto.get("cabello"):
                                    partes.append(f"cabello {sujeto.get('cabello')}")
                                if sujeto.get("ojos"):
                                    partes.append(f"ojos {sujeto.get('ojos')}")
                                if sujeto.get("ropa"):
                                    ropa = sujeto["ropa"]
                                    if isinstance(ropa, dict):
                                        pr = ropa.get("prenda", "")
                                        col = ropa.get("color", "")
                                        if pr:
                                            partes.append(f"{pr} {col}".strip())
                                    elif isinstance(ropa, str):
                                        partes.append(ropa)
                                if sujeto.get("pose"):
                                    partes.append(f"pose: {sujeto.get('pose')}")
                                if sujeto.get("expresion"):
                                    partes.append(f"expresión: {sujeto.get('expresion')}")

                        # ESCENA - solo si no está bloqueado
                        if not bloqueos.get("escena", {}).get("bloqueado", False):
                            escena = adn.get("escena", {})
                            if escena.get("ubicacion"):
                                partes.append(escena.get("ubicacion"))
                            if escena.get("interior_exterior"):
                                partes.append(escena.get("interior_exterior"))
                            if escena.get("elementos"):
                                if isinstance(escena["elementos"], list):
                                    partes.append(", ".join(escena["elementos"][:5]))

                        # ILUMINACIÓN - solo si no está bloqueado
                        if not bloqueos.get("iluminacion", {}).get("bloqueado", False):
                            ilu = adn.get("iluminacion", {})
                            if ilu.get("tipo"):
                                partes.append(f"iluminación {ilu.get('tipo')}")
                            if ilu.get("hora_dia"):
                                partes.append(ilu.get("hora_dia"))
                            if ilu.get("color_temperatura"):
                                partes.append(f"temperatura de color: {ilu.get('color_temperatura')}")

                        # CÁMARA - solo si no está bloqueado
                        if not bloqueos.get("camara", {}).get("bloqueado", False):
                            cam = adn.get("camara", {})
                            if cam.get("encuadre"):
                                partes.append(cam.get("encuadre"))
                            if cam.get("angulo"):
                                partes.append(f"ángulo de cámara: {cam.get('angulo')}")
                            if cam.get("lente_simulada"):
                                partes.append(cam.get("lente_simulada"))
                            if cam.get("profundidad_campo"):
                                partes.append(f"profundidad de campo: {cam.get('profundidad_campo')}")

                        # ESTILO - solo si no está bloqueado
                        if not bloqueos.get("estilo", {}).get("bloqueado", False):
                            estilo = adn.get("estilo", {})
                            if estilo.get("estetica"):
                                partes.append(estilo.get("estetica"))
                            if estilo.get("tecnica"):
                                partes.append(estilo.get("tecnica"))
                            if estilo.get("paleta_dominante"):
                                if isinstance(estilo["paleta_dominante"], list):
                                    partes.extend(estilo["paleta_dominante"][:5])

                        # ATMOSFERA - solo si no está bloqueado
                        if not bloqueos.get("atmosfera", {}).get("bloqueado", False):
                            atmos = adn.get("atmosfera", {})
                            if atmos.get("estado_animo"):
                                partes.append(f"mood: {atmos.get('estado_animo')}")

                        # TÉCNICO
                        tecnico = adn.get("tecnico", {})
                        if tecnico.get("contraste"):
                            partes.append(f"contraste {tecnico.get('contraste')}")
                        if tecnico.get("saturacion"):
                            partes.append(f"saturación {tecnico.get('saturacion')}")
                        if tecnico.get("postproceso"):
                            partes.append(tecnico.get("postproceso"))

                        prompt = ", ".join(partes)
                        if prompt:
                            # Añadir al prompt existente en lugar de reemplazar
                            existente = self.txt_idea.get("1.0", "end").strip()
                            if existente:
                                nuevo = f"{existente}\n\n{prompt}"
                            else:
                                nuevo = prompt
                            
                            self.txt_idea.delete("1.0", "end")
                            self.txt_idea.insert("1.0", nuevo)
                            vent.destroy()
                            
                            # Mostrar qué categorías se incluyeron
                            cats_incluidas = []
                            cats_excluidas = []
                            for cat in ["sujeto", "escena", "iluminacion", "camara", "estilo", "atmosfera", "composicion", "tecnico"]:
                                if bloqueos.get(cat, {}).get("bloqueado", False):
                                    cats_excluidas.append(cat)
                                else:
                                    cats_incluidas.append(cat)
                            
                            if cats_excluidas:
                                self.set_estado(f"🧬Idea (bloqueados: {', '.join(cats_excluidas)})", "#2ecc71")
                            else:
                                self.set_estado("🧬 ADN en idea - pulsa Generar", "#2ecc71")
                        else:
                            self.set_estado("⚠️ ADN vacío, no hay datos para convertir", "#e67e22")

                    def _guardar_adn():
                        from tkinter import simpledialog
                        
                        # Cargar ADNs primero para poder usar len(adns)
                        prefs = self.store.cargar_preferencias()
                        adns = prefs.get("adns_guardados", [])
                        
                        # Generar sugerencia de nombre basada en el ADN
                        sujeto = adn.get("sujeto", {})
                        estilo = adn.get("estilo", {})
                        estetica = estilo.get("estetica", "") if isinstance(estilo, dict) else ""
                        tipo = sujeto.get("tipo", "") if isinstance(sujeto, dict) else ""
                        
                        sugerencia = f"ADN {estetica[:20] if estetica else 'visual'} {len(adns)+1}"
                        
                        nombre = simpledialog.askstring("💾 Guardar ADN", "Nombre para el ADN:", initialvalue=sugerencia)
                        if not nombre:
                            return
                        
                        # Verificar duplicados
                        nombres_exist = [a.get("nombre", "") for a in adns]
                        if nombre in nombres_exist:
                            idx = 2
                            while f"{nombre} ({idx})" in nombres_exist:
                                idx += 1
                            nombre = f"{nombre} ({idx})"
                        
                        adns.append({
                            "nombre": nombre,
                            "adn": adn,
                            "motor": motor,
                            "fecha": datetime.datetime.now().strftime("%Y-%m-%d"),
                        })
                        prefs["adns_guardados"] = adns
                        self.store.guardar_preferencias(prefs)
                        self.set_estado(f"🧬 ADN '{nombre}' guardado", "#2ecc71")

                    ctk.CTkButton(btn_frame, text="📋 Copiar JSON", width=110, height=30,
                                  command=_copiar_json).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text="🎯 Usar en prompt", width=130, height=30,
                                  fg_color="#1a7a3c", command=_usar_en_prompt).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text="💾 Guardar ADN", width=110, height=30,
                                  command=_guardar_adn).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text="📚 Mi biblioteca", width=130, height=30,
                                  fg_color="#4a1a6a", hover_color="#3a1050",
                                  command=self._cmd_ver_biblioteca_adn
                                  ).pack(side="left", padx=4)

                    # Botones de conversión por plataforma
                    plat_frame = ctk.CTkFrame(vent, fg_color="transparent")
                    plat_frame.pack(pady=(8, 0))

                    lbl_plat = ctk.CTkLabel(plat_frame, text="🎨 Convertir a:", font=ctk.CTkFont(size=11))
                    lbl_plat.pack(side="left", padx=(0, 5))

                    def _convertir_plataforma(plataforma):
                        partes = []
                        fallos = []
                        plantilla = ADN_A_PLATAFORMA.get(plataforma, {})

                        # Sujeto
                        sujeto = adn.get("sujeto", {})
                        if isinstance(sujeto, list):
                            sujeto = sujeto[0] if sujeto else {}
                        if plantilla.get("sujeto"):
                            try:
                                ropa_val = ""
                                ropa = sujeto.get("ropa", {})
                                if isinstance(ropa, dict):
                                    ropa_val = ropa.get("prenda", "")
                                elif isinstance(ropa, str):
                                    ropa_val = ropa
                                partes.append(plantilla["sujeto"].format(
                                    tipo=sujeto.get("tipo", ""),
                                    ropa=ropa_val,
                                    pose=sujeto.get("pose", ""),
                                    expresion=sujeto.get("expresion", "")
                                ))
                            except Exception as e:
                                logger.warning(f"Conversión {plataforma} sujeto falló: {e}")
                                fallos.append("sujeto")

                        # Estilo
                        estilo = adn.get("estilo", {})
                        if plantilla.get("estilo") and estilo:
                            try:
                                paleta_str = ""
                                paleta = estilo.get("paleta_exacta_5colores", [])
                                if isinstance(paleta, list):
                                    paleta_str = ", ".join(paleta[:3])
                                partes.append(plantilla["estilo"].format(
                                    estetica_exacta=estilo.get("estetica_exacta", ""),
                                    tecnica_precisa=estilo.get("tecnica_precisa", ""),
                                    paleta_exacta_5colores=paleta_str
                                ))
                            except Exception as e:
                                logger.warning(f"Conversión {plataforma} estilo falló: {e}")
                                fallos.append("estilo")

                        # Iluminación
                        ilu = adn.get("iluminacion", {})
                        if plantilla.get("iluminacion") and ilu:
                            try:
                                partes.append(plantilla["iluminacion"].format(tipo_exacto=ilu.get("tipo_exacto", "")))
                            except Exception as e:
                                logger.warning(f"Conversión {plataforma} iluminacion falló: {e}")
                                fallos.append("iluminacion")

                        # Cámara
                        if plantilla.get("camara"):
                            cam = adn.get("camara", {})
                            if cam:
                                try:
                                    partes.append(plantilla["camara"].format(
                                        angulo_exacto=cam.get("angulo_exacto", ""),
                                        encuadre_exacto=cam.get("encuadre_exacto", "")
                                    ))
                                except Exception as e:
                                    logger.warning(f"Conversión {plataforma} camara falló: {e}")
                                    fallos.append("camara")

                        # Escena
                        if plantilla.get("escena"):
                            esc = adn.get("escena", {})
                            try:
                                # Fix: antes usaba ilu.get("tipo_exacto") por
                                # copy-paste del bloque iluminación. Ahora
                                # toma el tipo_exacto desde esc (escena).
                                partes.append(plantilla["escena"].format(
                                    ubicacion_exacta=esc.get("ubicacion_exacta", ""),
                                    tipo_exacto=esc.get("tipo_exacto", "")
                                ))
                            except Exception as e:
                                logger.warning(f"Conversión {plataforma} escena falló: {e}")
                                fallos.append("escena")

                        # Atmósfera
                        if plantilla.get("atm"):
                            atmos = adn.get("atmosfera", {})
                            try:
                                partes.append(plantilla["atm"].format(estado_animo_exacto=atmos.get("estado_animo_exacto", "")))
                            except Exception as e:
                                logger.warning(f"Conversión {plataforma} atmosfera falló: {e}")
                                fallos.append("atmosfera")

                        prompt = ", ".join([p for p in partes if p])
                        if prompt:
                            # Añadir al prompt existente en lugar de reemplazar
                            existente = self.txt_idea.get("1.0", "end").strip()
                            if existente:
                                nuevo = f"{existente}\n\n{prompt}"
                            else:
                                nuevo = prompt
                            
                            self.txt_idea.delete("1.0", "end")
                            self.txt_idea.insert("1.0", nuevo)
                            vent.destroy()
                            
                            # Mostrar bloqueos
                            cats_bloqueadas = [cat for cat in bloqueos if bloqueos.get(cat, {}).get("bloqueado", False)]
                            if cats_bloqueadas:
                                msg = f"🧬 {plataforma} (bloqueados: {', '.join(cats_bloqueadas[:3])}{'...' if len(cats_bloqueadas) > 3 else ''})"
                            elif fallos:
                                msg = f"🧬 {plataforma} - parcial (falló: {', '.join(fallos)})"
                            else:
                                msg = f"🧬 {plataforma} en idea"
                            self.set_estado(msg, "#f39c12" if fallos else "#2ecc71")
                        else:
                            self.set_estado(f"❌ Conversión {plataforma} falló completamente", "#e74c3c")

                    for plat in ["midjourney", "stable_diffusion", "dalle", "flux"]:
                        ctk.CTkButton(plat_frame, text=plat.replace("_", " ").upper(), width=80, height=24,
                                      font=ctk.CTkFont(size=9),
                                      command=lambda p=plat: _convertir_plataforma(p)).pack(side="left", padx=2)

                    ctk.CTkButton(vent, text="Cerrar", width=100, height=28,
                                  command=vent.destroy).pack(pady=(5, 12))

                    self.toggle_botones(True)
                    self.set_estado(f"🧬 ADN extraído ({motor})", "#2ecc71")

                self.after(0, _mostrar)

            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error ADN: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_sugerir_estilos(self):
        """Analiza la idea y marca automáticamente los estilos más apropiados."""
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.set_estado("⚠️ Escribe una idea primero.", "#e67e22")
        try: self._sesion_log("🎨 Sugerir estilos: pidió sugerencia automática")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        modo = self.modo_var.get()
        if modo == "imagen":
            estilos_dispo = list(self.estilo_checks.keys())
        elif modo == "video":
            estilos_dispo = list(self.estilo_checks.keys())
        else:
            return self.set_estado("⚠️ Función disponible solo para imagen y vídeo.", "#e67e22")

        if not estilos_dispo:
            return self.set_estado("⚠️ No hay estilos disponibles.", "#e67e22")

        self.set_estado("🎨 Analizando idea para sugerir estilos...", "#f39c12")
        self.toggle_botones(False)

        peticion = (
            f"Analiza esta idea y sugiere LOS 3-6 ESTILOS MÁS APROPIADOS de la lista disponible.\n\n"
            f"IDEA: {idea}\n\n"
            f"ESTILOS DISPONIBLES:\n{', '.join(estilos_dispo[:200])}\n\n"
            f"REGLAS:\n"
            f"- Devuelve SOLO los nombres EXACTOS de la lista (no inventes nuevos).\n"
            f"- Sugiere entre 3 y 6 estilos que combinen bien.\n"
            f"- Prioriza coherencia (ej: no mezcles 'Anime' con 'Fotografía Realista').\n\n"
            f"FORMATO: Lista separada por COMAS, una sola línea, sin números ni explicaciones.\n"
            f"EJEMPLO: Cinematográfico 4K, Cinematic Noir, Drama Cinematográfico"
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.3, max_tokens=300)
                resp = limpiar_marcadores(resp).strip()

                # Parsear lista de estilos
                sugeridos = [s.strip() for s in resp.split(",") if s.strip()]
                # Filtrar solo los que existen
                validos = [s for s in sugeridos if s in estilos_dispo]

                # Fallback: matching fuzzy si no hay match exacto
                if not validos:
                    for s in sugeridos:
                        for est in estilos_dispo:
                            if s.lower() in est.lower() or est.lower() in s.lower():
                                validos.append(est)
                                break

                if not validos:
                    self.after(0, lambda: self.set_estado("⚠️ No se pudieron extraer estilos. Intenta de nuevo.", "#e67e22"))
                    self.after(0, lambda: self.toggle_botones(True))
                    return

                def _aplicar():
                    # Limpiar selección actual
                    for n, v in self.estilo_checks.items():
                        v.set(False)
                    # Marcar los sugeridos
                    for est in validos:
                        if est in self.estilo_checks:
                            self.estilo_checks[est].set(True)
                    self.set_estado(f"🎨 Estilos aplicados: {', '.join(validos)}", "#2ecc71")
                    self.toggle_botones(True)
                self.after(0, _aplicar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_anclaje_visual(self):
        """ADN visual: extrae rasgos detallados de imagen ref y los guarda como anclaje inmutable.

        v1.1: progreso visual, preview imagen, guardar en biblioteca ADN,
        mostrar rasgos activos, barra de estado.
        """
        if not self.imagen_cargada:
            self.set_estado("⚠️ Carga una imagen de referencia primero.", "#e67e22")
            return

        self.set_estado("🧬 Extrayendo ADN visual (rasgos exactos)...", "#f39c12")
        self.toggle_botones(False)

        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self)
        vent.title("🧬 ADN visual — Extracción")
        vent.geometry("720x580")
        vent.transient(self)

        ctk.CTkLabel(vent, text="🧬 Extracción de ADN visual",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 2))
        ctk.CTkLabel(vent, text="Analizando imagen de referencia para extraer rasgos inmutables",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 6))

        # Preview de la imagen cargada
        prev_frame = ctk.CTkFrame(vent, fg_color=c["fg_dark"], corner_radius=8)
        prev_frame.pack(fill="x", padx=15, pady=(0, 6))
        ctk.CTkLabel(prev_frame, text="🖼 Imagen de referencia",
                     font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(6, 2))
        img_preview = ctk.CTkLabel(prev_frame, text="")
        img_preview.pack(padx=10, pady=(0, 4))
        try:
            from PIL import Image as _PIL
            img_copy = self.imagen_cargada.copy()
            img_copy.thumbnail((160, 120))
            img_tk = ctk.CTkImage(img_copy, size=(img_copy.width, img_copy.height))
            img_preview.configure(image=img_tk)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # Estado / progreso
        lbl_estado = ctk.CTkLabel(vent, text="⏳ Iniciando extracción...",
                                   font=ctk.CTkFont(size=11), text_color="#f39c12")
        lbl_estado.pack(anchor="w", padx=15, pady=(0, 4))
        prog_bar = ctk.CTkProgressBar(vent, height=8)
        prog_bar.pack(fill="x", padx=15, pady=(0, 8))
        prog_bar.set(0)

        def _actualizar_progreso(pct, msg):
            prog_bar.set(pct)
            lbl_estado.configure(text=msg, text_color="#f39c12")

        def _trabajar():
            try:
                self.after(0, lambda: _actualizar_progreso(0.1, "🔍 Describiendo imagen..."))
                def on_status(msg): self.after(0, lambda m=msg: _actualizar_progreso(0.2, m))
                desc, motor = self.vision.describir(self.imagen_cargada, "imagen", on_status)

                self.after(0, lambda: _actualizar_progreso(0.5, "🧬 Extrayendo rasgos visuales..."))
                peticion = (
                    f"De esta descripción visual de una imagen, EXTRAE el ADN visual: rasgos físicos EXACTOS y constantes que deben mantenerse en cualquier variante futura.\n\n"
                    f"DESCRIPCIÓN VISUAL:\n{desc}\n\n"
                    f"FORMATO DE RESPUESTA — usa exactamente este formato (en inglés, separado por comas, lista de tags):\n\n"
                    f"PERSONAJE: [color exacto pelo, color exacto ojos, edad aproximada, género, rasgos faciales únicos, complexión]\n"
                    f"ROPA: [prendas específicas con colores y materiales]\n"
                    f"ACCESORIOS: [joyas, gafas, sombrero, etc.]\n"
                    f"MARCAS DISTINTIVAS: [tatuajes, cicatrices, lunares específicos]\n"
                    f"DETALLES CLAVE: [3-5 elementos que NO deben cambiar nunca]\n\n"
                    f"Sé MUY específico. 'pelo plateado plata-azulado' es mejor que 'pelo gris'. 'ojos verdes esmeralda con manchas doradas' es mejor que 'ojos verdes'."
                )
                adn = self.deepseek.generar(peticion, temperature=0.2, max_tokens=800)
                adn = limpiar_marcadores(adn).strip()
                self._anclaje_visual = adn
                if hasattr(self, "_actualizar_indicador_adn"):
                    self.after(0, self._actualizar_indicador_adn)
                self.after(0, lambda: _actualizar_progreso(0.9, "✅ Extracción completada"))

                def _mostrar():
                    prog_bar.pack_forget()
                    lbl_estado.pack_forget()
                    prev_frame.pack_forget()

                    vent2 = GPromptWindow(self)
                    vent2.title("🧬 ADN visual extraído")
                    vent2.geometry("700x500")
                    vent2.transient(self)
                    ctk.CTkLabel(vent2, text="🧬 ADN visual — Rasgos inmutables",
                                 font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
                    estado_activo = "🟢 ACTIVO" if self._anclaje_visual else "⚪ Inactivo"
                    ctk.CTkLabel(vent2, text=f"Vision: {motor}  ·  Estado: {estado_activo}",
                                  font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

                    txt = ctk.CTkTextbox(vent2, font=ctk.CTkFont(size=11), wrap="word", height=320)
                    txt.pack(fill="both", expand=True, padx=15, pady=(0, 5))
                    txt.insert("1.0", adn)

                    btn_frame = ctk.CTkFrame(vent2, fg_color="transparent")
                    btn_frame.pack(pady=10)

                    def _guardar_editado():
                        self._anclaje_visual = txt.get("1.0", "end").strip()
                        if hasattr(self, "_actualizar_indicador_adn"):
                            self._actualizar_indicador_adn()
                        vent2.destroy()
                        self.set_estado("🧬 ADN visual guardado y activo en próximas generaciones", "#2ecc71")

                    def _desactivar():
                        self._anclaje_visual = None
                        if hasattr(self, "_actualizar_indicador_adn"):
                            self._actualizar_indicador_adn()
                        vent2.destroy()
                        self.set_estado("🧬 ADN visual desactivado")

                    def _guardar_biblioteca():
                        # Persiste el ADN-texto en preferencias bajo
                        # `adns_guardados` con marcador texto_libre, para que
                        # la biblioteca pueda renderizarlo.
                        from tkinter import simpledialog
                        prefs_b = self.store.cargar_preferencias()
                        adns_b = prefs_b.get("adns_guardados", []) or []
                        if not isinstance(adns_b, list):
                            adns_b = []
                        sugerencia = f"ADN rasgos {len(adns_b) + 1}"
                        nombre = simpledialog.askstring(
                            "💾 Guardar ADN",
                            "Nombre para este ADN:",
                            initialvalue=sugerencia,
                            parent=vent2,
                        )
                        if not nombre:
                            return
                        adn_text = txt.get("1.0", "end").strip()
                        adns_b.append({
                            "nombre": nombre.strip(),
                            "adn": {"texto_libre": adn_text},
                            "motor": motor,
                            "fecha": datetime.datetime.now().strftime("%Y-%m-%d"),
                        })
                        prefs_b["adns_guardados"] = adns_b
                        self.store.guardar_preferencias(prefs_b)
                        self.set_estado(f"💾 ADN '{nombre}' guardado en biblioteca", "#2ecc71")

                    ctk.CTkButton(btn_frame, text="✅ Guardar y activar", width=150, height=30, fg_color="#1a7a3c",
                                  command=_guardar_editado).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text="💾 Guardar en biblioteca", width=160, height=30, fg_color="#4a1a6a",
                                  command=_guardar_biblioteca).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text="📚 Ver biblioteca", width=130, height=30,
                                  fg_color="#6a4a8a", hover_color="#503870",
                                  command=self._cmd_ver_biblioteca_adn
                                  ).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text="🚫 Desactivar", width=100, height=30, fg_color="#5a1a1a",
                                  command=_desactivar).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text="📋 Copiar", width=80, height=30,
                                  command=lambda: pyperclip.copy(adn)).pack(side="left", padx=4)

                    self.toggle_botones(True)
                    self.set_estado("🧬 ADN visual extraído — guarda para activarlo", "#2ecc71")
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: prog_bar.pack_forget())
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        ctk.CTkButton(vent, text="🧬 Iniciar extracción", width=200, height=34, fg_color="#7c3aed",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      text_color="#ffffff", command=lambda: threading.Thread(target=_trabajar, daemon=True).start()
                      ).pack(pady=8)

    def _cmd_variar_con_anclaje(self):
        """Genera variantes manteniendo el ADN visual como rasgos fijos."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        if not getattr(self, '_anclaje_visual', None):
            self.set_estado("⚠️ Primero extrae el ADN visual con 🧬 ADN.", "#e67e22")
            return
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            self.set_estado("⚠️ Escribe una idea base (qué quieres variar).", "#e67e22")
            return

        # Ventana selección
        sel = GPromptWindow(self)
        sel.title("🧬 Variar con ADN")
        sel.geometry("520x520")
        sel.transient(self)
        ctk.CTkLabel(sel, text="🧬 Variar con ADN visual", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 3))
        ctk.CTkLabel(sel, text="El sujeto mantendrá sus rasgos exactos. Solo cambia el contexto:",
                     font=ctk.CTkFont(size=11), text_color=c["muted_text"]).pack(pady=(0, 12))

        # Cantidad
        f = ctk.CTkFrame(sel, fg_color="transparent")
        f.pack(pady=5)
        ctk.CTkLabel(f, text="Cantidad de variantes:").pack(side="left", padx=8)
        ent_n = ctk.CTkEntry(f, width=60); ent_n.insert(0, "5"); ent_n.pack(side="left")

        # Qué variar (10 opciones)
        ctk.CTkLabel(sel, text="Qué cambiar (ADN se mantiene):", font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(15, 3))
        opciones = [
            "Localización / fondo",
            "Ropa diferente (cambiar prendas)",
            "Pose y expresión",
            "Iluminación y atmósfera",
            "Acción que está realizando",
            "Estilo artístico",
            "Hora del día / clima",
            "Ángulo de cámara y plano",
            "Paleta de color dominante",
            "Época o ambientación temporal",
        ]
        var_op = ctk.StringVar(value=opciones[0])
        cb = ctk.CTkComboBox(sel, values=opciones, variable=var_op, width=340, height=28)
        cb.pack()

        ent_extra = ctk.CTkEntry(sel, placeholder_text="Detalle adicional (opcional)", width=350, height=28)
        ent_extra.pack(pady=(15, 5))

        def _ejecutar():
            try: cantidad = int(ent_n.get())
            except: cantidad = 5
            cantidad = max(1, min(cantidad, 20))
            elemento = var_op.get()
            extra = ent_extra.get().strip()
            sel.destroy()
            self._generar_variantes_con_anclaje(idea, elemento, extra, cantidad)

        ctk.CTkButton(sel, text="🧬 Generar variantes", width=200, height=32,
                      fg_color="#1a7a3c", command=_ejecutar).pack(pady=15)

    def _generar_variantes_con_anclaje(self, idea, elemento, extra, cantidad):
        """Worker para generar N variantes manteniendo ADN."""
        self.set_estado(f"🧬 Generando {cantidad} variantes con ADN anclado...", "#f39c12")
        self.toggle_botones(False)
        adn = self._anclaje_visual
        modo = self.modo_var.get()
        resultados = []

        def _generar_una(num):
            try:
                specs = self.get_current_model_specs()
                has_neg = specs.get("has_negative", True) if specs else True
                is_natural = specs.get("is_natural", False) if specs else False
                fmt = "lenguaje natural descriptivo" if is_natural else "tags con pesos"
                neg_str = "Genera POSITIVE y NEGATIVE." if has_neg else "Solo POSITIVE (sin NEGATIVE)."

                peticion = (
                    f"Genera la variante #{num} de {cantidad} de un prompt de {modo}.\n\n"
                    f"⚓ ADN VISUAL INMUTABLE (estos rasgos NO PUEDEN cambiar nunca):\n{adn}\n\n"
                    f"IDEA BASE: {idea}\n"
                    f"QUÉ CAMBIAR EN ESTA VARIANTE: {elemento}{f' — {extra}' if extra else ''}\n\n"
                    f"REGLAS:\n"
                    f"- TODOS los rasgos del ADN deben aparecer literalmente en el POSITIVE.\n"
                    f"- SOLO cambia: {elemento}\n"
                    f"- Esta variante debe ser DIFERENTE a las anteriores en lo que cambia.\n"
                    f"- Formato: {fmt}\n"
                    f"- {neg_str}\n\n"
                    f"FORMATO:\nPOSITIVE PROMPT: [prompt completo con ADN intacto]\nNEGATIVE PROMPT: [si aplica]\n"
                )
                resp = self.deepseek.generar(peticion, temperature=0.7, max_tokens=2000)
                resp = limpiar_marcadores(resp)
                if not has_neg:
                    import re
                    resp = re.sub(r'\n?\s*NEGATIVE\s+PROMPT\s*:.*?$', '', resp, flags=re.DOTALL | re.IGNORECASE).strip()
                resultados.append(resp)
                self.guardar_en_historial(resp)
            except Exception as e:
                resultados.append(f"❌ Error en variante {num}: {e}")

        def _worker_all():
            for i in range(1, cantidad + 1):
                _generar_una(i)
                self.after(0, lambda i=i: self.set_estado(f"🧬 Variante {i}/{cantidad} lista", "#3498db"))
            def _mostrar():
                self._abrir_comparador(resultados)
                self.set_estado(f"🧬 {len(resultados)} variantes con ADN listas", "#2ecc71")
                self.toggle_botones(True)
                self._sonar_completado()
            self.after(0, _mostrar)

        threading.Thread(target=_worker_all, daemon=True).start()

    def _cmd_comparar_consistencia(self):
        """Compara dos prompts e indica qué difiere y qué coincide."""
        actual = self.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.set_estado("⚠️ Necesitas un prompt en el resultado.", "#e67e22")

        # Pedir el segundo prompt
        from tkinter import simpledialog
        otro = simpledialog.askstring("🔍 Comparar consistencia",
                                        "Pega aquí el otro prompt a comparar (el actual es el del resultado):",
                                        parent=self)
        if not otro or len(otro) < 20:
            return self.set_estado("⚠️ Pega un prompt válido para comparar.", "#e67e22")

        self.set_estado("🔍 Analizando consistencia entre prompts...", "#f39c12")
        self.toggle_botones(False)

        peticion = (
            f"Compara estos dos prompts y analiza la CONSISTENCIA entre ellos.\n\n"
            f"PROMPT A:\n{actual}\n\n"
            f"PROMPT B:\n{otro}\n\n"
            f"RESPONDE en español con este formato exacto:\n\n"
            f"📊 CONSISTENCIA: X/100% (qué tan similares son)\n\n"
            f"✅ ELEMENTOS QUE COINCIDEN (rasgos compartidos importantes):\n"
            f"   - Lista de elementos clave que aparecen en ambos\n\n"
            f"⚠️ DIFERENCIAS PRINCIPALES:\n"
            f"   - Lista de qué cambia entre A y B\n\n"
            f"🚨 INCONSISTENCIAS DETECTADAS (si los prompts deberían describir al MISMO sujeto/escena):\n"
            f"   - Lista de elementos que deberían ser iguales pero difieren\n\n"
            f"💡 SUGERENCIA: \n"
            f"   - 1-2 frases sobre cómo armonizar ambos prompts si fueran serie/secuencia\n"
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.3, max_tokens=2000)
                resp = limpiar_marcadores(resp)

                def _mostrar():
                    vent = GPromptWindow(self)
                    vent.title("🔍 Análisis de consistencia")
                    vent.geometry("700x550")
                    vent.transient(self)
                    ctk.CTkLabel(vent, text="🔍 Consistencia entre prompts", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 5))
                    txt = ctk.CTkTextbox(vent, font=ctk.CTkFont(size=11), wrap="word")
                    txt.pack(fill="both", expand=True, padx=15, pady=(0, 5))
                    txt.insert("1.0", resp)
                    txt.configure(state="disabled")
                    ctk.CTkButton(vent, text="📋 Copiar", width=100, height=28,
                                  command=lambda: pyperclip.copy(resp)).pack(pady=10)
                    self.toggle_botones(True)
                    self.set_estado("🔍 Consistencia analizada", "#2ecc71")
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_negative_builder(self):
        """Constructor visual de NEGATIVE PROMPT con checkboxes temáticos.

        v1.1: búsqueda/filtrar, guardar preset, mostrar activos, tabs por categoría.
        """
        if not self._debe_mostrar_negatives():
            return self.set_estado("⚠️ Este modelo no usa NEGATIVE.", "#e67e22")

        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        vent = GPromptWindow(self)
        vent.title("🧰 Constructor de NEGATIVE")
        vent.geometry("700x720")
        vent.transient(self)

        ctk.CTkLabel(vent, text="🧰 Constructor de NEGATIVE", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 2))
        lbl_activos = ctk.CTkLabel(vent, text="", font=ctk.CTkFont(size=9), text_color="#2ecc71")
        lbl_activos.pack(pady=(0, 4))

        # Búsqueda
        search_row = ctk.CTkFrame(vent, fg_color="transparent")
        search_row.pack(fill="x", padx=15, pady=(0, 4))
        search_entry = ctk.CTkEntry(search_row, placeholder_text="🔍 Busca un elemento...",
                                      height=28, font=ctk.CTkFont(size=11))
        search_entry.pack(fill="x")

        tabs = ctk.CTkTabview(vent, height=460)
        tabs.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        categorias = {
            "🔥 Anatomía": [
                ("Manos malas", "(bad hands:1.4), (deformed hands:1.3), (extra fingers:1.4), missing fingers, fused fingers"),
                ("Cara mal", "(deformed face:1.3), (asymmetric face:1.2), bad anatomy, ugly face"),
                ("Ojos raros", "(crossed eyes:1.3), (dead eyes:1.2), unaligned eyes, lazy eye"),
                ("Boca / dientes", "(bad teeth:1.3), crooked teeth, deformed mouth, ugly smile"),
                ("Múltiples cabezas", "(multiple heads:1.4), conjoined twins, cloned face"),
                ("Cuerpo deforme", "(bad anatomy:1.4), (mutation:1.3), extra limbs, deformed body"),
                ("Pies malos", "(bad feet:1.3), deformed toes, fused toes, missing legs"),
                ("Proporciones malas", "(bad proportions:1.3), gigantic head, tiny body, long neck"),
            ],
            "📷 Calidad": [
                ("Baja calidad", "(low quality:1.4), (worst quality:1.4), lowres, blurry, jpeg artifacts"),
                ("Pixelado", "(pixelated:1.3), aliasing, compression artifacts"),
                ("Sobreexpuesto", "(overexposed:1.3), washed out colors, blown highlights"),
                ("Subexpuesto", "(underexposed:1.2), too dark, crushed shadows"),
                ("Ruido", "(noisy:1.3), grainy, film grain"),
                ("Desenfoque", "(out of focus:1.3), motion blur, soft focus"),
                ("Color saturado mal", "oversaturated, neon vomit, ugly color cast"),
                ("Tinte amarillo", "(yellow tint:1.2), color cast, white balance off"),
            ],
            "📝 Texto": [
                ("Texto / letras", "(text:1.4), (watermark:1.4), letters, words, signature"),
                ("Logos / firmas", "logo, brand, copyright, username, artist signature"),
                ("Marca de agua", "(watermark:1.5), stamps, labels"),
                ("Bordes / frame", "(border:1.3), frame, picture frame, vignette"),
                ("Caption / subtítulo", "caption, subtitle, dialog text, speech bubble"),
            ],
            "🎨 Estilo": [
                ("Sin anime", "(anime:1.3), (cartoon:1.3), (illustration:1.3), unrealistic"),
                ("Sin foto", "(photorealistic:1.3), (photograph:1.3), realistic skin"),
                ("Sin 3D", "(3d render:1.3), CGI, plastic look, video game graphics"),
                ("Sin pintura", "(painting:1.2), (drawing:1.2), brush strokes, oil painting"),
                ("Sin sketch", "(sketch:1.3), pencil drawing, line art, lineart"),
                ("Sin abstracto", "(abstract:1.2), abstract art, non-representational"),
            ],
            "🚫 Composición": [
                ("Recortado", "(cropped:1.3), out of frame, cut off"),
                ("Multi-sujeto", "(multiple subjects:1.3), too many people, group, crowd"),
                ("Plano", "flat lighting, no depth, boring composition"),
                ("Simétrico forzado", "(perfect symmetry:1.2), too symmetrical"),
                ("Plano centrado", "centered subject, plain background, dead center"),
                ("Fondo desordenado", "cluttered background, busy background, distracting"),
            ],
            "✨ Realismo": [
                ("Piel plástica", "(plastic skin:1.3), waxy skin, smooth skin, doll-like"),
                ("Sin uncanny", "(uncanny valley:1.3), creepy, soulless"),
                ("Sin filtro IG", "(instagram filter:1.2), heavy makeup, beauty filter"),
                ("Errores luz", "(unnatural lighting:1.2), unrealistic shadows, no shadow"),
            ],
        }

        # check_vars[nombre] = (BooleanVar, tags, checkbox_widget)
        # Los checkboxes se crean UNA SOLA VEZ al inicio. El filtro
        # solo hace pack_forget()/pack() para no perder estado visual.
        check_vars = {}

        def _actualizar_lbl():
            n = sum(1 for tup in check_vars.values() if tup[0].get())
            activos = [nom for nom, tup in check_vars.items() if tup[0].get()]
            extra = f"… (+{len(activos) - 5})" if len(activos) > 5 else ""
            lbl_activos.configure(
                text=f"✅ {n} activos: {', '.join(activos[:5])}{extra}"
            )

        def _crear_checkbox(tab_frame, nombre, tags):
            v = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(tab_frame, text=nombre, variable=v,
                                 font=ctk.CTkFont(size=10),
                                 onvalue=True, offvalue=False)
            cb.pack(anchor="w", padx=16, pady=1)
            check_vars[nombre] = (v, tags, cb)
            v.trace_add("write", lambda *a: _actualizar_lbl())

        # Crear todos los checkboxes UNA SOLA VEZ
        for cat_nombre, cat_items in categorias.items():
            tab = tabs.add(cat_nombre)
            for nombre, tags in cat_items:
                _crear_checkbox(tab, nombre, tags)

        def _filtrar(e=None):
            """Filtra mostrando/ocultando con pack_forget/pack — NO destruye
            los checkboxes, así el estado marcado/desmarcado se conserva."""
            filtro = search_entry.get().lower().strip()
            for nombre, (v, tags, cb) in check_vars.items():
                if not filtro or filtro in nombre.lower() or filtro in tags.lower():
                    if not cb.winfo_ismapped():
                        cb.pack(anchor="w", padx=16, pady=1)
                else:
                    if cb.winfo_ismapped():
                        cb.pack_forget()

        search_entry.bind("<KeyRelease>", _filtrar)

        # Presets + guardar/guardados
        preset_row = ctk.CTkFrame(vent, fg_color="transparent")
        preset_row.pack(pady=(2, 0))

        def _marcar(nombres, exclusivo=False):
            if exclusivo:
                for tup in check_vars.values():
                    tup[0].set(False)
            for nombre in nombres:
                if nombre in check_vars:
                    check_vars[nombre][0].set(True)

        def _cargar_presets() -> list:
            """Lee los presets persistidos desde preferencias.json."""
            try:
                prefs = self.store.cargar_preferencias() or {}
                return list(prefs.get("negative_presets", []))
            except Exception as e:
                logger.debug(f"_cargar_presets: {e}")
                return []

        def _persistir_presets(presets: list) -> None:
            try:
                prefs = self.store.cargar_preferencias() or {}
                prefs["negative_presets"] = presets
                self.store.guardar_preferencias(prefs)
            except Exception as e:
                logger.warning(f"_persistir_presets falló: {e}")

        def _guardar_preset():
            activos = [nom for nom, tup in check_vars.items() if tup[0].get()]
            if not activos:
                return self.set_estado("⚠️ Marca elementos antes de guardar preset.", "#e67e22")
            # Pedir nombre al usuario
            from tkinter import simpledialog
            presets = _cargar_presets()
            sugerencia = f"Preset {len(presets) + 1}"
            nombre = simpledialog.askstring("Guardar preset NEGATIVE",
                                            "Nombre del preset:",
                                            initialvalue=sugerencia,
                                            parent=vent)
            if not nombre:
                return
            nombre = nombre.strip()
            # Si ya existe ese nombre, preguntar si sobreescribir
            if any(p.get("nombre") == nombre for p in presets):
                from tkinter import messagebox as _mb
                if not _mb.askyesno("Ya existe",
                                    f"Ya existe un preset llamado '{nombre}'. "
                                    f"¿Sobreescribir?",
                                    parent=vent):
                    return
                presets = [p for p in presets if p.get("nombre") != nombre]
            presets.append({"nombre": nombre, "items": activos})
            _persistir_presets(presets)
            self.set_estado(f"💾 Preset '{nombre}' guardado ({len(activos)} items)", "#2ecc71")
            _actualizar_lbl()

        def _mostrar_presets():
            presets = _cargar_presets()
            if not presets:
                self.set_estado("⚠️ No hay presets guardados todavía.", "#e67e22")
                return
            win = GPromptWindow(vent)
            win.title("💾 Presets de NEGATIVE")
            win.geometry("440x400")
            win.transient(vent)
            ctk.CTkLabel(win, text="💾 Presets guardados",
                         font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 4))
            scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
            scroll.pack(fill="both", expand=True, padx=15, pady=5)

            def _refrescar_presets():
                for w in scroll.winfo_children():
                    w.destroy()
                presets_act = _cargar_presets()
                if not presets_act:
                    ctk.CTkLabel(scroll, text="(sin presets)").pack(pady=20)
                    return
                for preset in presets_act:
                    row = ctk.CTkFrame(scroll, fg_color="#111820", corner_radius=6)
                    row.pack(fill="x", pady=3)
                    hdr = ctk.CTkFrame(row, fg_color="transparent")
                    hdr.pack(fill="x", padx=10, pady=(5, 0))
                    ctk.CTkLabel(hdr,
                                 text=f"📁 {preset['nombre']} ({len(preset['items'])} items)",
                                 font=ctk.CTkFont(size=11, weight="bold")
                                 ).pack(side="left")

                    def _aplicar(p=preset):
                        _marcar(p["items"])
                        win.destroy()
                        _actualizar_lbl()

                    def _borrar(p=preset):
                        from tkinter import messagebox as _mb
                        if not _mb.askyesno("Confirmar",
                                            f"¿Borrar preset '{p['nombre']}'?",
                                            parent=win):
                            return
                        nuevos = [x for x in _cargar_presets()
                                  if x.get("nombre") != p["nombre"]]
                        _persistir_presets(nuevos)
                        _refrescar_presets()

                    ctk.CTkButton(hdr, text="Aplicar", width=70, height=22,
                                  fg_color="#1a7a3c",
                                  command=_aplicar).pack(side="right", padx=2)
                    ctk.CTkButton(hdr, text="🗑", width=32, height=22,
                                  fg_color="#7a1a1a", hover_color="#5a0f0f",
                                  command=_borrar).pack(side="right", padx=2)
                    ctk.CTkLabel(
                        row,
                        text=f"{', '.join(preset['items'][:8])}"
                             f"{'…' if len(preset['items']) > 8 else ''}",
                        font=ctk.CTkFont(size=9), text_color="#888888",
                        wraplength=380,
                    ).pack(anchor="w", padx=10, pady=(0, 5))
            _refrescar_presets()

        ctk.CTkButton(preset_row, text="✓ Básicos", width=85, height=24, fg_color="#1a4a5a",
                      command=lambda: _marcar(["Manos malas", "Baja calidad", "Texto / letras", "Marca de agua"])
                      ).pack(side="left", padx=2)
        ctk.CTkButton(preset_row, text="👤 Retrato", width=85, height=24, fg_color="#1a4a5a",
                      command=lambda: _marcar(["Manos malas", "Cara mal", "Ojos raros", "Boca / dientes",
                                                "Proporciones malas", "Piel plástica", "Baja calidad",
                                                "Texto / letras", "Marca de agua"])
                      ).pack(side="left", padx=2)
        ctk.CTkButton(preset_row, text="🏆 Calidad", width=100, height=24, fg_color="#1a4a5a",
                      command=lambda: _marcar(["Baja calidad", "Pixelado", "Ruido", "Desenfoque",
                                                "Tinte amarillo", "Texto / letras", "Marca de agua", "Logos / firmas"])
                      ).pack(side="left", padx=2)
        ctk.CTkButton(preset_row, text="🧹 Limpiar", width=75, height=24, fg_color="#5a3a1a",
                      command=lambda: [tup[0].set(False) for tup in check_vars.values()]
                      ).pack(side="left", padx=2)
        ctk.CTkButton(preset_row, text="💾 Guardar", width=90, height=24, fg_color="#4a1a6a",
                      command=_guardar_preset).pack(side="left", padx=2)
        ctk.CTkButton(preset_row, text="📂 Presets", width=80, height=24, fg_color="#1a4a5a",
                      command=_mostrar_presets).pack(side="left", padx=2)

        btn_row = ctk.CTkFrame(vent, fg_color="transparent")
        btn_row.pack(pady=6)

        def _tags_seleccionados() -> list[str]:
            return [tup[1] for tup in check_vars.values() if tup[0].get()]

        def _aplicar():
            tags_sel = _tags_seleccionados()
            if not tags_sel:
                return self.set_estado("⚠️ Marca al menos un elemento.", "#e67e22")
            negativo = ", ".join(tags_sel)
            pos = self.extraer_positive()
            if pos:
                self.actualizar_salida(f"POSITIVE PROMPT: {pos}\nNEGATIVE PROMPT: {negativo}")
                self.set_estado(f"🧰 NEGATIVE construido ({len(tags_sel)} items)", "#2ecc71")
            else:
                pyperclip.copy(negativo)
                self.set_estado(f"🧰 NEGATIVE copiado ({len(tags_sel)} items)", "#2ecc71")
            vent.destroy()

        def _copiar():
            tags_sel = _tags_seleccionados()
            if not tags_sel:
                return self.set_estado("⚠️ Marca al menos un elemento.", "#e67e22")
            pyperclip.copy(", ".join(tags_sel))
            self.set_estado(f"📋 NEGATIVE copiado ({len(tags_sel)} items)", "#2ecc71")
            vent.destroy()

        ctk.CTkButton(btn_row, text="✅ Aplicar al prompt", width=170, height=30, fg_color="#1a7a3c",
                      command=_aplicar).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="📋 Solo copiar", width=130, height=30, fg_color="#475569",
                      command=_copiar).pack(side="left", padx=4)

    def _cmd_moodboard(self):
        """Genera N prompts complementarios con mismo mood pero distintos sujetos.

        v2: N configurable (4-10, default 6). Antes hardcoded a 6 sujetos
        fijos (persona/paisaje/objeto/animal/arquitectura/macro). Ahora el
        LLM elige los N sujetos diversos.
        """
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.set_estado("⚠️ Escribe un concepto base.", "#e67e22")

        n = self._pedir_n_modal(
            "🎭 Mood — número de prompts",
            "¿Cuántos prompts en el moodboard?\n"
            "Comparten mood/atmósfera pero con sujetos distintos.",
            n_min=4, n_max=10, default=6,
            key_pref="moodboard_n",
        )
        if n is None:
            return

        try: self._sesion_log(f"🎨 Mood: generó {n} prompts (mismo mood, distintos sujetos)")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.set_estado(f"🎨 Generando moodboard de {n} prompts...", "#f39c12")
        self.toggle_botones(False)

        formato_lineas = "\n---\n".join(
            f"PROMPT {i+1}: [sujeto diverso] — POSITIVE: ... NEGATIVE: ..."
            for i in range(n)
        )
        peticion = (
            f"Genera UN MOODBOARD: {n} prompts que comparten el MISMO MOOD/atmósfera pero con SUJETOS distintos.\n\n"
            f"CONCEPTO/MOOD BASE: {idea}\n"
            f"ESTILOS: {self.estilos_texto()}\n\n"
            f"REGLAS:\n"
            f"- Mantén la MISMA paleta, iluminación, atmósfera y estilo en TODOS los {n}.\n"
            f"- Cambia el SUJETO en cada uno (elige {n} categorías diversas: persona, "
            f"paisaje, objeto, animal, arquitectura, detalle macro, vehículo, comida, etc.).\n"
            f"- Todos juntos deben formar una serie visualmente coherente.\n\n"
            f"FORMATO ({n} prompts):\n{formato_lineas}"
        )

        def _worker():
            try:
                max_tok = min(8000, 1500 + n * 600)
                resp = self.deepseek.generar(peticion, temperature=0.8, max_tokens=max_tok)
                resp = limpiar_marcadores(resp)
                bloques = self._parsear_bloques_numerados(resp, n_esperado=n)
                if len(bloques) < 2:
                    self.after(0, lambda: self.set_estado("⚠️ Solo se generó 1 bloque, intenta de nuevo", "#e67e22"))
                    self.after(0, lambda: self.toggle_botones(True))
                    return

                def _mostrar():
                    self._abrir_comparador(bloques[:n])
                    self.set_estado(f"🎨 Moodboard listo ({len(bloques)} prompts)", "#2ecc71")
                    self.toggle_botones(True)
                    self._sonar_completado()
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    # Tipos de shot disponibles para Story (Bloque 6).
    # (key, label, descripción corta)
    STORY_SHOT_TYPES = [
        ("wide",      "Wide",            "Plano general — sujeto entero + entorno"),
        ("medium",    "Medium",          "Plano medio — cintura arriba"),
        ("close",     "Close-Up",        "Primer plano — rostro o detalle"),
        ("pov",       "POV",             "Punto de vista — cámara = ojos del sujeto"),
        ("ots",       "Over-the-Shoulder","Sobre el hombro — sigue al personaje"),
        ("topdown",   "Top-Down",        "Cenital — cámara desde arriba"),
        ("dutch",     "Dutch angle",     "Plano inclinado — tensión / desequilibrio"),
        ("aerial",    "Aerial",          "Aéreo — vista desde el cielo"),
    ]

    def _pedir_story_config(self, default_n=3):
        """Bloque 6 — Modal de configuración de Story.

        Permite elegir:
          • N (slider 2-6)
          • Tipos de shot explícitos (checkboxes) o "LLM elige" (toggle)

        Devuelve dict {"n": int, "tipos": [str]|None, "auto": bool} o
        None si el usuario cancela. `tipos` es lista de labels en el
        orden que el usuario marcó (no de la lista canónica).
        """
        prefs = {}
        try:
            prefs = self.store.cargar_preferencias() or {}
        except Exception as e:
            logger.debug(f"[silent] prefs: {e}")
        n_inicial = int(prefs.get("story_n", default_n) or default_n)
        tipos_pref = prefs.get("story_tipos") or []
        auto_pref = prefs.get("story_auto", True)
        if auto_pref is None: auto_pref = True

        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        v = GPromptWindow(self)
        v.title("🎞 Story — configuración")
        v.geometry("520x540")
        v.transient(self)

        ctk.CTkLabel(v, text="🎞 Story Sequence — configura tu secuencia",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 4))
        ctk.CTkLabel(v, text="Misma iluminación/paleta/sujeto · solo cambia el encuadre",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 12))

        # Slider N
        n_var = tk.IntVar(value=n_inicial)
        lbl_n = ctk.CTkLabel(v, text=f"N = {n_inicial} shots",
                              font=ctk.CTkFont(size=12, weight="bold"))
        lbl_n.pack(pady=(2, 2))
        def _on_slide(val):
            n_var.set(int(float(val)))
            lbl_n.configure(text=f"N = {int(float(val))} shots")
        slider = ctk.CTkSlider(v, from_=2, to=6, number_of_steps=4,
                                command=_on_slide, width=380)
        slider.set(n_inicial)
        slider.pack(pady=(2, 10))

        # Toggle auto
        auto_var = tk.BooleanVar(value=bool(auto_pref))
        # Frame checkboxes (oculto si auto=True)
        chk_frame = ctk.CTkFrame(v, fg_color=c["fg_dark"], corner_radius=8)
        chk_vars = {}

        def _redraw_checkboxes():
            for w in chk_frame.winfo_children():
                w.destroy()
            ctk.CTkLabel(chk_frame, text="Marca los tipos de shot a usar (en orden de marca):",
                          font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(anchor="w", padx=10, pady=(6, 4))
            grid = ctk.CTkFrame(chk_frame, fg_color="transparent")
            grid.pack(fill="x", padx=10, pady=(0, 6))
            for i, (key, label, desc) in enumerate(self.STORY_SHOT_TYPES):
                marcado = key in tipos_pref
                vbool = tk.BooleanVar(value=marcado)
                chk_vars[key] = vbool
                cb = ctk.CTkCheckBox(grid, text=f"{label}  —  {desc}",
                                       variable=vbool,
                                       font=ctk.CTkFont(size=10))
                cb.grid(row=i, column=0, sticky="w", padx=4, pady=2)

        chk_toggle = ctk.CTkCheckBox(v, text="🤖 Que el LLM elija los tipos automáticamente",
                                       variable=auto_var,
                                       font=ctk.CTkFont(size=11, weight="bold"),
                                       command=lambda: chk_frame.pack_forget() if auto_var.get()
                                                       else chk_frame.pack(fill="x", padx=20, pady=4))
        chk_toggle.pack(pady=(4, 4))

        if not auto_var.get():
            chk_frame.pack(fill="x", padx=20, pady=4)
        _redraw_checkboxes()

        # Hint de validación
        lbl_hint = ctk.CTkLabel(v, text="", font=ctk.CTkFont(size=10),
                                  text_color="#fbbf24")
        lbl_hint.pack(pady=(2, 2))

        resultado = {"v": None}

        def _generar():
            n = int(n_var.get())
            if auto_var.get():
                resultado["v"] = {"n": n, "tipos": None, "auto": True}
                _guardar_prefs(n, [], True)
                v.destroy()
                return
            # Modo manual: validar N tipos marcados
            marcados = [self._story_label_de_key(k) for k, vb in chk_vars.items() if vb.get()]
            marcados_keys = [k for k, vb in chk_vars.items() if vb.get()]
            if len(marcados) != n:
                lbl_hint.configure(
                    text=f"⚠️ Marca exactamente {n} tipos (ahora {len(marcados)}) o activa el modo automático.",
                    text_color="#e67e22",
                )
                return
            resultado["v"] = {"n": n, "tipos": marcados, "auto": False}
            _guardar_prefs(n, marcados_keys, False)
            v.destroy()

        def _guardar_prefs(n, tipos_keys, auto):
            try:
                p = self.store.cargar_preferencias() or {}
                p["story_n"] = n
                p["story_tipos"] = tipos_keys
                p["story_auto"] = auto
                self.store.guardar_preferencias(p)
            except Exception as e:
                logger.debug(f"[silent] guardar prefs story: {e}")

        btn_row = ctk.CTkFrame(v, fg_color="transparent")
        btn_row.pack(side="bottom", pady=10)
        ctk.CTkButton(btn_row, text="▶ Generar", width=130, height=34,
                       fg_color="#1a7a3c", hover_color="#15633a",
                       font=ctk.CTkFont(size=12, weight="bold"),
                       command=_generar).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text="Cancelar", width=110, height=34,
                       fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                       command=v.destroy).pack(side="left", padx=6)

        v.bind("<Return>", lambda _e: _generar())
        v.bind("<Escape>", lambda _e: v.destroy())
        v.wait_window()
        return resultado["v"]

    def _story_label_de_key(self, key):
        for k, label, _desc in self.STORY_SHOT_TYPES:
            if k == key:
                return label
        return key

    def _cmd_story_sequence(self):
        """Genera N shots cinematográficos coherentes. Solo modo imagen.

        v3 (Bloque 6): N configurable + selección explícita de tipos de
        shot (Wide/Medium/Close/POV/OTS/TopDown/Dutch/Aerial) o "auto"
        (LLM elige).
        """
        if self.modo_var.get() != "imagen":
            return self.set_estado("⚠️ Story Sequence solo está disponible en modo IMAGEN.", "#e67e22")
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.set_estado("⚠️ Escribe la escena base.", "#e67e22")

        cfg = self._pedir_story_config(default_n=3)
        if cfg is None:
            return
        n = cfg["n"]
        tipos = cfg["tipos"]   # lista de labels o None
        auto = cfg["auto"]

        modo_log = "auto (LLM elige)" if auto else f"manual [{', '.join(tipos)}]"
        try: self._sesion_log(f"🎬 Story: {n} shots · {modo_log}")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.set_estado(f"🎬 Generando secuencia cinematográfica ({n} shots)...", "#f39c12")
        self.toggle_botones(False)

        if auto:
            tipos_instr = (
                f"- Tipos sugeridos: Wide / Medium / Close-Up / POV / OTS / "
                f"top-down / Dutch angle / Aerial. Elige {n} diversos."
            )
            formato_lineas = "\n---\n".join(
                f"SHOT {i+1} (tipo de plano): POSITIVE: ... NEGATIVE: ... — Descripción del encuadre"
                for i in range(n)
            )
        else:
            tipos_str = ", ".join(tipos)
            tipos_instr = (
                f"- Usa EXACTAMENTE estos {n} tipos de shot en este orden: {tipos_str}. "
                f"No los cambies ni añadas otros."
            )
            formato_lineas = "\n---\n".join(
                f"SHOT {i+1} ({tipos[i]}): POSITIVE: ... NEGATIVE: ... — Descripción del encuadre"
                for i in range(n)
            )

        peticion = (
            f"Genera {n} SHOTS CINEMATOGRÁFICOS de la misma escena, manteniendo coherencia.\n\n"
            f"ESCENA: {idea}\n"
            f"ESTILOS: {self.estilos_texto()}\n\n"
            f"REGLAS:\n"
            f"- MISMO sujeto, MISMA iluminación, MISMA paleta, MISMA atmósfera.\n"
            f"- Solo cambia el ENCUADRE/PLANO en cada uno.\n"
            f"{tipos_instr}\n\n"
            f"FORMATO ({n} shots):\n{formato_lineas}"
        )

        # Labels para el comparador (si manual, usar tipo explícito)
        labels_comp = [f"#{i+1} {tipos[i]}" for i in range(n)] if not auto else None

        def _worker():
            try:
                max_tok = min(6000, 1200 + n * 600)
                resp = self.deepseek.generar(peticion, temperature=0.6, max_tokens=max_tok)
                resp = limpiar_marcadores(resp)
                bloques = self._parsear_bloques_numerados(resp, n_esperado=n)

                def _mostrar():
                    self._abrir_comparador(bloques[:n], labels=labels_comp)
                    self.set_estado(f"🎬 Secuencia de {len(bloques)} shots lista", "#2ecc71")
                    self.toggle_botones(True)
                    self._sonar_completado()
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_storyboard_video(self):
        """Para vídeo: N shots clave de la secuencia (apertura/desarrollo/climax/cierre).

        v2: N configurable (3-8, default 4). El LLM distribuye los beats
        de la microhistoria según el N elegido.
        """
        if self.modo_var.get() != "video":
            return self.set_estado("⚠️ Storyboard solo está disponible en modo VÍDEO.", "#e67e22")
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.set_estado("⚠️ Escribe la escena/historia base.", "#e67e22")

        n = self._pedir_n_modal(
            "📽 Board — número de frames",
            "¿Cuántos frames clave en el storyboard?\n"
            "Cuentan una microhistoria visual coherente.",
            n_min=3, n_max=8, default=4,
            key_pref="board_n",
        )
        if n is None:
            return

        try: self._sesion_log(f"📽 Board: generó storyboard de {n} shots")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.set_estado(f"📽 Generando storyboard de {n} shots...", "#f39c12")
        self.toggle_botones(False)

        formato_lineas = "\n---\n".join(
            f"FRAME {i+1} (rol narrativo): POSITIVE: ... NEGATIVE: ..."
            for i in range(n)
        )
        peticion = (
            f"Genera un STORYBOARD DE {n} SHOTS para una secuencia de vídeo.\n\n"
            f"HISTORIA/ESCENA: {idea}\n"
            f"ESTILOS: {self.estilos_texto()}\n\n"
            f"REGLAS:\n"
            f"- Cuenta una microhistoria visual con {n} beats: apertura → "
            f"desarrollo → (intensidad creciente) → climax → cierre.\n"
            f"- Distribuye proporcionalmente los beats según el número {n}.\n"
            f"- MISMA paleta, iluminación coherente entre frames.\n"
            f"- Cada shot es un prompt de IMAGEN (para usar como key frame del vídeo).\n\n"
            f"FORMATO ({n} frames):\n{formato_lineas}"
        )

        def _worker():
            try:
                max_tok = min(7000, 1500 + n * 600)
                resp = self.deepseek.generar(peticion, temperature=0.7, max_tokens=max_tok)
                resp = limpiar_marcadores(resp)
                bloques = self._parsear_bloques_numerados(resp, n_esperado=n)

                # Bloque 6: botón extra para encadenar Board → Vídeo.
                # Toma los N frames y pide al LLM un prompt de vídeo
                # cinematográfico que use esos frames como keyframes.
                def _encadenar_video(_variaciones, _vent):
                    self._encadenar_board_a_video(bloques[:n], _vent)

                def _mostrar():
                    self._abrir_comparador(
                        bloques[:n],
                        extra_botones=[
                            ("🎬 Encadenar como prompt de vídeo", "#7c3aed", _encadenar_video),
                        ],
                    )
                    self.set_estado(
                        f"📽 Storyboard de {len(bloques)} frames listo · 🎬 encadénalo a vídeo desde el comparador",
                        "#2ecc71",
                    )
                    self.toggle_botones(True)
                    self._sonar_completado()
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _encadenar_board_a_video(self, frames, vent_comparador):
        """Bloque 6 — Encadenar storyboard como prompt de vídeo.

        Toma los N frames del storyboard y pide al LLM un prompt único de
        vídeo cinematográfico que use esos frames como keyframes
        (apertura → desarrollo → climax → cierre). Aplica el resultado a
        txt_salida y cierra el comparador.
        """
        if not frames:
            return self.set_estado("⚠️ No hay frames para encadenar.", "#e67e22")

        try: self._sesion_log(f"🎬 Board→Vídeo: encadenando {len(frames)} frames")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.set_estado(f"🎬 Encadenando {len(frames)} frames como prompt de vídeo...", "#f39c12")
        self.toggle_botones(False)

        # Construir bloque con cada frame numerado
        frames_str = "\n\n".join(
            f"--- FRAME {i+1} ---\n{f.strip()}"
            for i, f in enumerate(frames)
        )

        peticion = (
            f"Tengo un STORYBOARD de {len(frames)} frames clave de una secuencia de vídeo. "
            f"Quiero un ÚNICO prompt de VÍDEO cinematográfico que recorra los {len(frames)} frames "
            f"como KEYFRAMES, con movimientos de cámara y transiciones coherentes entre ellos.\n\n"
            f"FRAMES DEL STORYBOARD:\n{frames_str}\n\n"
            f"REGLAS:\n"
            f"- UNA sola descripción de vídeo continuo (no {len(frames)} prompts separados).\n"
            f"- Indica explícitamente la progresión: 'opens with [frame 1] → [transición/movimiento] "
            f"→ [frame 2] → … → closes with [frame {len(frames)}]'.\n"
            f"- Usa lenguaje cinematográfico (dolly in, pan, tracking shot, cut to, dissolve, etc.).\n"
            f"- MANTÉN la paleta, iluminación y atmósfera consistentes con los frames originales.\n"
            f"- Incluye duración estimada y ritmo (ej: slow burn, fast cut, lingering close-ups).\n\n"
            f"FORMATO:\n"
            f"POSITIVE PROMPT: <descripción completa del vídeo de {len(frames)} keyframes>\n"
            f"NEGATIVE PROMPT: <qué evitar>"
        )

        def _worker():
            try:
                max_tok = min(4500, 1500 + len(frames) * 400)
                resp = self.deepseek.generar(peticion, temperature=0.6, max_tokens=max_tok)
                resp = limpiar_marcadores(resp)

                def _aplicar():
                    # Cambiar modo a vídeo si no lo estaba ya (callback real es _on_modo_cambio)
                    if self.modo_var.get() != "video":
                        try:
                            self.modo_var.set("video")
                            if hasattr(self, '_on_modo_cambio'):
                                self._on_modo_cambio()
                        except Exception as e:
                            logger.debug(f"[silent] cambio modo: {e}")
                    self.actualizar_salida(resp)
                    self.guardar_en_historial(resp)
                    self.set_estado(
                        f"🎬 Vídeo encadenado de {len(frames)} keyframes aplicado al editor",
                        "#2ecc71",
                    )
                    self.toggle_botones(True)
                    self._sonar_completado()
                    try:
                        if vent_comparador and vent_comparador.winfo_exists():
                            vent_comparador.destroy()
                    except Exception as e:
                        logger.debug(f"[silent] cerrar comparador: {e}")
                self.after(0, _aplicar)
            except Exception as e:
                logger.exception("encadenar board→vídeo")
                self.after(0, lambda: self.set_estado(f"❌ Error encadenando: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_random_walk(self):
        """Bloque 5 — Walk árbol visual.

        Abre una ventana con un árbol interactivo: el usuario parte del
        prompt actual (raíz) y puede ramificar en cualquier nodo para
        generar 3 derivaciones hijas. Cada hijo puede ramificarse a su
        vez. El usuario puede inspeccionar cualquier nodo, aplicar su
        prompt al editor o copiar la ruta completa raíz→…→nodo.

        Reemplaza el modo lineal (N derivaciones secuenciales) por una
        exploración no lineal estilo grafo.
        """
        actual = self.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.set_estado("⚠️ Genera un prompt primero como base.", "#e67e22")

        try: self._sesion_log("🌀 Walk árbol abierto")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self._abrir_walk_arbol(actual)

    def _abrir_walk_arbol(self, prompt_raiz):
        """Bloque 5 — UI del árbol de Walk.

        Estructura de datos: lista de nodos, cada uno
            {"id": int, "parent": int|None, "texto": str,
             "depth": int, "hijos": [int], "label": str}
        El layout es horizontal: depth → X; hojas se reparten Y por
        orden DFS, internos = media de Y de hijos.
        """
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        # ─── Estado ──────────────────────────────────────────────
        nodos = [{
            "id": 0, "parent": None, "texto": prompt_raiz, "depth": 0,
            "hijos": [], "label": "Raíz",
        }]
        sel = {"id": 0}  # nodo seleccionado actual
        rect_refs = {}   # id_nodo → (rect_canvas_id, text_canvas_id)

        # ─── Ventana ─────────────────────────────────────────────
        vent = GPromptWindow(self)
        vent.title("🌀 Walk árbol — Explora derivaciones")
        vent.geometry("1240x740")
        vent.transient(self)

        ctk.CTkLabel(vent, text="🌀 Walk árbol — Explora derivaciones evolutivas",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 2))
        ctk.CTkLabel(vent, text="Click en un nodo para inspeccionarlo · 🌿 Ramificar genera 3 hijos vía LLM",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

        main = ctk.CTkFrame(vent, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(0, weight=1)

        # ─── Panel izquierdo: canvas con árbol ──────────────────
        canvas_frame = ctk.CTkFrame(main, fg_color=c["fg_dark"], corner_radius=8)
        canvas_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        canvas_bg = "#0f1626" if not is_lt else "#f8fafc"
        canvas = tk.Canvas(canvas_frame, bg=canvas_bg, highlightthickness=0)
        scroll_y = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scroll_x = tk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
        canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)

        # ─── Panel derecho: detalle del nodo ────────────────────
        panel = ctk.CTkFrame(main, fg_color=c["fg_dark"], corner_radius=8)
        panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        lbl_titulo = ctk.CTkLabel(panel, text="🌿 Nodo: Raíz",
                                   font=ctk.CTkFont(size=13, weight="bold"))
        lbl_titulo.pack(anchor="w", padx=12, pady=(10, 2))
        lbl_ruta = ctk.CTkLabel(panel, text="Ruta: Raíz",
                                 font=ctk.CTkFont(size=10),
                                 text_color=c["muted_text"], wraplength=420, justify="left")
        lbl_ruta.pack(anchor="w", padx=12, pady=(0, 8))

        txt_preview = ctk.CTkTextbox(panel, wrap="word",
                                      font=ctk.CTkFont(family="Consolas", size=10),
                                      height=300)
        txt_preview.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        # ─── Botones del panel ──────────────────────────────────
        btn_row1 = ctk.CTkFrame(panel, fg_color="transparent")
        btn_row1.pack(fill="x", padx=12, pady=2)
        btn_row2 = ctk.CTkFrame(panel, fg_color="transparent")
        btn_row2.pack(fill="x", padx=12, pady=(2, 12))

        lbl_status = ctk.CTkLabel(panel, text="", font=ctk.CTkFont(size=10),
                                    text_color="#fbbf24")
        lbl_status.pack(padx=12, pady=(0, 4))

        # ─── Layout del árbol ──────────────────────────────────
        BOX_W = 200
        BOX_H = 60
        X_PAD = 60   # entre niveles
        Y_PAD = 25   # entre hojas

        def _calcular_layout():
            """DFS: hojas reciben Y por orden; internos = media de hijos."""
            leaf_y = [0]
            def dfs(nid):
                n = nodos[nid]
                if not n["hijos"]:
                    n["_y"] = leaf_y[0] * (BOX_H + Y_PAD) + 30
                    leaf_y[0] += 1
                else:
                    for h in n["hijos"]:
                        dfs(h)
                    ys = [nodos[h]["_y"] for h in n["hijos"]]
                    n["_y"] = sum(ys) / len(ys)
                n["_x"] = 30 + n["depth"] * (BOX_W + X_PAD)
            dfs(0)

        def _color_nodo(nid):
            n = nodos[nid]
            if nid == sel["id"]:
                return "#fbbf24", "#1f2937"  # seleccionado: dorado, texto oscuro
            if n["depth"] == 0:
                return "#2563eb", "#ffffff"  # raíz: azul
            return "#7c3aed", "#ffffff"      # derivado: morado

        def _redibujar():
            _calcular_layout()
            canvas.delete("all")
            rect_refs.clear()
            # Líneas padre→hijo primero (debajo de los nodos)
            for n in nodos:
                if n["parent"] is None:
                    continue
                p = nodos[n["parent"]]
                x1, y1 = p["_x"] + BOX_W, p["_y"] + BOX_H / 2
                x2, y2 = n["_x"], n["_y"] + BOX_H / 2
                mx = (x1 + x2) / 2
                canvas.create_line(x1, y1, mx, y1, mx, y2, x2, y2,
                                    fill=c["muted_text"], width=2, smooth=False)
            # Nodos
            for n in nodos:
                fill, txt_col = _color_nodo(n["id"])
                rect = canvas.create_rectangle(
                    n["_x"], n["_y"], n["_x"] + BOX_W, n["_y"] + BOX_H,
                    fill=fill, outline="#fbbf24" if n["id"] == sel["id"] else "",
                    width=3 if n["id"] == sel["id"] else 0,
                    tags=("nodo", f"n{n['id']}"),
                )
                preview = (n["texto"][:90] + "…") if len(n["texto"]) > 90 else n["texto"]
                # quitar saltos para preview compacto
                preview = preview.replace("\n", " ")
                label_box = f"{n['label']}\n{preview}"
                lbl = canvas.create_text(
                    n["_x"] + BOX_W / 2, n["_y"] + BOX_H / 2,
                    text=label_box, fill=txt_col, width=BOX_W - 12,
                    font=("Segoe UI", 9), tags=("nodo", f"n{n['id']}"),
                )
                rect_refs[n["id"]] = (rect, lbl)
            # Ajustar scroll region
            max_x = max(n["_x"] + BOX_W for n in nodos) + 40
            max_y = max(n["_y"] + BOX_H for n in nodos) + 40
            canvas.configure(scrollregion=(0, 0, max_x, max_y))

        def _ruta_de(nid):
            chain = []
            cur = nid
            while cur is not None:
                chain.append(nodos[cur])
                cur = nodos[cur]["parent"]
            return list(reversed(chain))

        def _refresh_panel():
            n = nodos[sel["id"]]
            lbl_titulo.configure(text=f"🌿 Nodo: {n['label']}  (profundidad {n['depth']})")
            ruta = _ruta_de(sel["id"])
            ruta_str = " → ".join(x["label"] for x in ruta)
            lbl_ruta.configure(text=f"Ruta: {ruta_str}")
            txt_preview.configure(state="normal")
            txt_preview.delete("1.0", "end")
            txt_preview.insert("1.0", n["texto"])
            txt_preview.configure(state="disabled")

        def _seleccionar(nid):
            sel["id"] = nid
            _redibujar()
            _refresh_panel()

        def _on_canvas_click(event):
            # Convertir coords pantalla → canvas (con scroll)
            cx = canvas.canvasx(event.x)
            cy = canvas.canvasy(event.y)
            for n in nodos:
                if n["_x"] <= cx <= n["_x"] + BOX_W and n["_y"] <= cy <= n["_y"] + BOX_H:
                    _seleccionar(n["id"])
                    return
        canvas.bind("<Button-1>", _on_canvas_click)

        # ─── Acción: ramificar (3 hijos vía LLM) ────────────────
        def _ramificar():
            nid_padre = sel["id"]
            padre = nodos[nid_padre]
            if padre["depth"] >= 6:
                lbl_status.configure(text="⚠️ Máxima profundidad alcanzada (6)", text_color="#e67e22")
                return

            lbl_status.configure(text="🌿 Generando 3 derivaciones...", text_color="#fbbf24")
            btn_ramificar.configure(state="disabled")
            btn_usar.configure(state="disabled")

            peticion = (
                f"Toma este prompt y genera EXACTAMENTE 3 derivaciones distintas, "
                f"cada una explorando una variación diferente (objeto, atmósfera, ángulo, color, estilo). "
                f"Cada derivación debe mantener el espíritu del original pero alejarse en una dirección distinta.\n\n"
                f"PROMPT BASE:\n{padre['texto']}\n\n"
                f"FORMATO ESTRICTO — devuelve EXACTAMENTE 3 bloques así:\n\n"
                f"PROMPT 1:\nPOSITIVE PROMPT: ...\nNEGATIVE PROMPT: ...\n\n"
                f"PROMPT 2:\nPOSITIVE PROMPT: ...\nNEGATIVE PROMPT: ...\n\n"
                f"PROMPT 3:\nPOSITIVE PROMPT: ...\nNEGATIVE PROMPT: ...\n\n"
                f"NO añadas explicaciones, NO añadas títulos, NO añadas un PROMPT 4."
            )

            def _worker():
                try:
                    resp = self.deepseek.generar(peticion, temperature=0.85, max_tokens=2400)
                    resp = limpiar_marcadores(resp)
                    bloques = self._parsear_bloques_numerados(resp, n_esperado=3)
                    if not bloques:
                        # Fallback: dividir por "PROMPT N:" o doble salto
                        bloques = [b.strip() for b in resp.split("\n\n") if len(b.strip()) > 40][:3]
                    # Asegurar 3 bloques exactos
                    bloques = bloques[:3]
                    if len(bloques) < 3:
                        # Rellenar con el primero si faltan
                        while len(bloques) < 3:
                            bloques.append(bloques[0] if bloques else padre["texto"])

                    def _aplicar():
                        # Crear 3 hijos
                        ids_nuevos = []
                        for i, b in enumerate(bloques):
                            nid = len(nodos)
                            etiq_padre = padre["label"]
                            nodos.append({
                                "id": nid,
                                "parent": nid_padre,
                                "texto": b,
                                "depth": padre["depth"] + 1,
                                "hijos": [],
                                "label": f"{etiq_padre}.{i+1}" if padre["depth"] > 0 else f"D{i+1}",
                            })
                            padre["hijos"].append(nid)
                            ids_nuevos.append(nid)
                        # Seleccionar el primer hijo nuevo
                        sel["id"] = ids_nuevos[0]
                        _redibujar()
                        _refresh_panel()
                        lbl_status.configure(text=f"✅ 3 derivaciones añadidas como hijos de {padre['label']}",
                                              text_color="#2ecc71")
                        btn_ramificar.configure(state="normal")
                        btn_usar.configure(state="normal")
                    self.after(0, _aplicar)
                except Exception as e:
                    logger.exception("walk ramificar")
                    def _err():
                        lbl_status.configure(text=f"❌ Error: {e}", text_color="#e74c3c")
                        btn_ramificar.configure(state="normal")
                        btn_usar.configure(state="normal")
                    self.after(0, _err)

            threading.Thread(target=_worker, daemon=True).start()

        # ─── Acción: usar este nodo (NO cierra, sigues explorando) ──
        def _usar_nodo():
            n = nodos[sel["id"]]
            self.actualizar_salida(n["texto"])
            ruta = _ruta_de(sel["id"])
            ruta_str = " → ".join(x["label"] for x in ruta)
            self.set_estado(f"📋 Walk: aplicado nodo {n['label']} (ruta: {ruta_str})", "#2ecc71")
            try: self._sesion_log(f"🌀 Walk: aplicó nodo {n['label']} (depth {n['depth']})")
            except Exception as e:
                logger.debug(f"[silent] {e}")
            lbl_status.configure(
                text=f"📋 Aplicado al editor: {n['label']} · ventana sigue abierta para seguir explorando",
                text_color="#2ecc71",
            )

        # ─── Acción: copiar ruta — abre modal con preview ───────
        def _copiar_ruta():
            ruta = _ruta_de(sel["id"])
            cadena = " → ".join(x["label"] for x in ruta)
            detalle = "\n\n".join(
                f"## {x['label']} (depth {x['depth']})\n{x['texto']}" for x in ruta
            )
            texto_copia = f"# Evolución Walk: {cadena}\n\n{detalle}"

            v = GPromptWindow(vent)
            v.title("📂 Ruta del nodo — preview")
            v.geometry("720x520")
            v.transient(vent)

            ctk.CTkLabel(v, text=f"📂 Ruta: {cadena}",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         wraplength=680, justify="left").pack(padx=14, pady=(12, 4), anchor="w")
            ctk.CTkLabel(v, text=f"{len(ruta)} nodos · profundidad {ruta[-1]['depth']}",
                         font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(padx=14, anchor="w")

            txt_ruta = ctk.CTkTextbox(v, wrap="word",
                                       font=ctk.CTkFont(family="Consolas", size=10))
            txt_ruta.pack(fill="both", expand=True, padx=14, pady=8)
            txt_ruta.insert("1.0", texto_copia)
            txt_ruta.configure(state="disabled")

            estado_lbl = ctk.CTkLabel(v, text="", font=ctk.CTkFont(size=10),
                                        text_color="#fbbf24")
            estado_lbl.pack(pady=(0, 4))

            def _copiar_clipboard():
                try:
                    pyperclip.copy(texto_copia)
                    estado_lbl.configure(text="✅ Copiado al portapapeles",
                                          text_color="#2ecc71")
                    lbl_status.configure(text=f"📂 Ruta copiada ({len(ruta)} nodos)",
                                          text_color="#2ecc71")
                except Exception as e:
                    estado_lbl.configure(text=f"❌ No se pudo copiar: {e}",
                                          text_color="#e74c3c")

            def _guardar_en_versiones():
                """Apila cada nodo de la ruta en _versiones_prompt para
                que se puedan recuperar desde el menú 📑 Versiones prompt."""
                try:
                    if not hasattr(self, '_versiones_prompt'):
                        self._versiones_prompt = []
                    ahora = datetime.datetime.now().strftime("%H:%M:%S")
                    cadena_corta = " → ".join(x["label"] for x in ruta)
                    nuevos = 0
                    for x in ruta:
                        # Evitar duplicados: si el texto exacto ya está
                        # como última versión, no apilamos.
                        if (self._versiones_prompt
                                and self._versiones_prompt[-1].get("texto") == x["texto"]):
                            continue
                        self._versiones_prompt.append({
                            "texto": x["texto"],
                            "fecha": ahora,
                            "etiqueta": (f"v{len(self._versiones_prompt) + 1} "
                                         f"(Walk {cadena_corta} · nodo {x['label']})"),
                        })
                        nuevos += 1
                        if len(self._versiones_prompt) > 30:
                            self._versiones_prompt = self._versiones_prompt[-30:]
                    estado_lbl.configure(
                        text=f"✅ {nuevos} nodo(s) guardados en Versiones prompt — accesibles desde 📑 Versiones",
                        text_color="#2ecc71",
                    )
                    lbl_status.configure(
                        text=f"💾 Ruta guardada ({nuevos} nodos) en 📑 Versiones prompt",
                        text_color="#2ecc71",
                    )
                    try: self._sesion_log(f"🌀 Walk: guardó ruta {cadena_corta} en Versiones ({nuevos} nodos)")
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
                except Exception as e:
                    estado_lbl.configure(text=f"❌ Error guardando: {e}",
                                          text_color="#e74c3c")

            btn_bar = ctk.CTkFrame(v, fg_color="transparent")
            btn_bar.pack(pady=(0, 12))
            ctk.CTkButton(btn_bar, text="💾 Guardar en Versiones prompt", width=230, height=32,
                          fg_color="#1a4a7a", hover_color="#15396a",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          command=_guardar_en_versiones).pack(side="left", padx=5)
            ctk.CTkButton(btn_bar, text="📋 Copiar al portapapeles", width=200, height=32,
                          fg_color="#1a7a3c", hover_color="#15633a",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          command=_copiar_clipboard).pack(side="left", padx=5)
            ctk.CTkButton(btn_bar, text="Cerrar", width=100, height=32,
                          fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                          command=v.destroy).pack(side="left", padx=5)
            v.bind("<Escape>", lambda _e: v.destroy())

        # ─── Acción: borrar subárbol ────────────────────────────
        def _borrar_subarbol():
            nid = sel["id"]
            if nid == 0:
                lbl_status.configure(text="⚠️ No puedes borrar la raíz", text_color="#e67e22")
                return
            from tkinter import messagebox
            n = nodos[nid]
            cnt_descendientes = 0
            def _contar(x):
                nonlocal cnt_descendientes
                for h in nodos[x]["hijos"]:
                    cnt_descendientes += 1
                    _contar(h)
            _contar(nid)
            msg = (f"¿Borrar el nodo {n['label']}"
                   + (f" y sus {cnt_descendientes} descendientes?" if cnt_descendientes else "?"))
            if not messagebox.askyesno("Confirmar borrado", msg, parent=vent):
                return
            # Marcar para borrar todos los descendientes + este
            a_borrar = {nid}
            def _marca(x):
                for h in nodos[x]["hijos"]:
                    a_borrar.add(h)
                    _marca(h)
            _marca(nid)
            # Quitar de la lista de hijos del padre
            padre_id = n["parent"]
            if padre_id is not None:
                nodos[padre_id]["hijos"].remove(nid)
            # Reconstruir lista de nodos manteniendo IDs originales
            # (los IDs son índices, así que marcamos como None en vez de quitar)
            for i in a_borrar:
                nodos[i] = None
            # Limpiamos la lista compactando con remapeo
            id_map = {}
            nuevos = []
            for old_n in nodos:
                if old_n is None: continue
                id_map[old_n["id"]] = len(nuevos)
                nuevos.append(old_n)
            # Remapear parent + hijos
            for new_n in nuevos:
                new_n["id"] = id_map[new_n["id"]]
                if new_n["parent"] is not None:
                    new_n["parent"] = id_map.get(new_n["parent"])
                new_n["hijos"] = [id_map[h] for h in new_n["hijos"] if h in id_map]
            nodos.clear()
            nodos.extend(nuevos)
            sel["id"] = id_map.get(padre_id, 0)
            _redibujar()
            _refresh_panel()
            lbl_status.configure(text=f"🗑 Subárbol borrado ({len(a_borrar)} nodos)",
                                  text_color="#2ecc71")

        btn_ramificar = ctk.CTkButton(btn_row1, text="🌿 Ramificar (3 hijos)",
                                        fg_color="#7c3aed", hover_color="#5b21b6",
                                        font=ctk.CTkFont(size=11, weight="bold"),
                                        command=_ramificar)
        btn_ramificar.pack(side="left", padx=2, fill="x", expand=True)

        btn_usar = ctk.CTkButton(btn_row1, text="📋 Usar este",
                                  fg_color="#1a7a3c", hover_color="#15633a",
                                  font=ctk.CTkFont(size=11, weight="bold"),
                                  command=_usar_nodo)
        btn_usar.pack(side="left", padx=2, fill="x", expand=True)

        ctk.CTkButton(btn_row2, text="💾 Guardar ruta", fg_color="#1a4a7a",
                       hover_color="#15396a", font=ctk.CTkFont(size=10),
                       command=_copiar_ruta).pack(side="left", padx=2, fill="x", expand=True)
        ctk.CTkButton(btn_row2, text="🗑 Borrar subárbol", fg_color="#8a1a1a",
                       hover_color="#6b1414", font=ctk.CTkFont(size=10),
                       command=_borrar_subarbol).pack(side="left", padx=2, fill="x", expand=True)
        ctk.CTkButton(btn_row2, text="✖ Cerrar", fg_color=c["fg_dark"],
                       hover_color=c["fg_dark_hover"], font=ctk.CTkFont(size=10),
                       command=vent.destroy).pack(side="left", padx=2, fill="x", expand=True)

        _redibujar()
        _refresh_panel()
        vent.bind("<Escape>", lambda _e: vent.destroy())

    def _cmd_color_palette(self):
        """Extrae paleta de colores de la imagen cargada.

        v1.1: copia color individual, genera complementarios/analogos,
        guarda paleta, muestra valores RGB/HSL.
        """
        if not self.imagen_cargada:
            return self.set_estado("⚠️ Carga una imagen de referencia primero.", "#e67e22")

        self.set_estado("🎨 Extrayendo paleta de colores...", "#f39c12")

        def _worker():
            try:
                from PIL import Image
                from collections import Counter
                import math

                img = self.imagen_cargada.copy()
                img.thumbnail((200, 200))
                img = img.convert("RGB")

                quantized = img.quantize(colors=8)
                palette_raw = quantized.getpalette()[:24]
                colores_raw = []
                for i in range(0, 24, 3):
                    r, g, b = palette_raw[i], palette_raw[i+1], palette_raw[i+2]
                    colores_raw.append((r, g, b))

                def rgb_to_hex(r, g, b):
                    return f"#{r:02X}{g:02X}{b:02X}"

                def rgb_to_hsl(r, g, b):
                    r, g, b = r/255.0, g/255.0, b/255.0
                    mx, mn = max(r, g, b), min(r, g, b)
                    l = (mx + mn) / 2
                    if mx == mn:
                        h = s = 0
                    else:
                        d = mx - mn
                        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
                        if mx == r: h = (g - b) / d + (6 if g < b else 0)
                        elif mx == g: h = (b - r) / d + 2
                        else: h = (r - g) / d + 4
                        h /= 6
                    return f"HSL({int(h*360)}, {int(s*100)}%, {int(l*100)}%)"

                def complementary(r, g, b):
                    return f"#{255-r:02X}{255-g:02X}{255-b:02X}"

                def analog_colors(r, g, b):
                    h = max(r, g, b) / 255.0
                    s = (max(r, g, b) - min(r, g, b)) / 255.0
                    adj = 30
                    results = []
                    for offset in [-2, -1, 1, 2]:
                        h2 = (h + offset * adj / 360) % 1.0
                        val = int(h2 * 255)
                        if offset == -2:
                            results.append(f"#{min(r+30,255):02X}{min(g+10,255):02X}{min(b+30,255):02X}")
                        elif offset == -1:
                            results.append(f"#{max(r-20,0):02X}{max(g-10,0):02X}{max(b-20,0):02X}")
                        elif offset == 1:
                            results.append(f"#{max(r-30,0):02X}{min(g+20,255):02X}{max(b-10,0):02X}")
                        else:
                            results.append(f"#{min(r+10,255):02X}{max(g-20,0):02X}{min(b+30,255):02X}")
                    return results

                def _mostrar():
                    vent = GPromptWindow(self)
                    vent.title("🎨 Paleta de colores extraída")
                    vent.geometry("580x600")
                    vent.transient(self)
                    ctk.CTkLabel(vent, text="🎨 Paleta extraída de la imagen",
                                 font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 4))
                    ctk.CTkLabel(vent, text="Haz clic en un color para copiarlo. Añade al prompt para aplicar la paleta.",
                                 font=ctk.CTkFont(size=9), text_color="#888888").pack(pady=(0, 8))

                    # Colores principales
                    sw_frame = ctk.CTkFrame(vent, fg_color="transparent")
                    sw_frame.pack(pady=4)
                    hex_codes = []
                    for i, (r, g, b) in enumerate(colores_raw[:5]):
                        hex_c = rgb_to_hex(r, g, b)
                        hex_codes.append(hex_c)
                        col_f = ctk.CTkFrame(sw_frame, fg_color=hex_c, width=80, height=80, corner_radius=10,
                                              border_color="#3a3a4a", border_width=1)
                        col_f.pack(side="left", padx=5)
                        col_f.pack_propagate(False)

                        def _copy_color(h=hex_c):
                            pyperclip.copy(h)
                            self.set_estado(f"📋 {h} copiado", "#2ecc71")

                        def _on_enter(e, f, orig):
                            f.configure(border_color="#ffffff", border_width=2)

                        def _on_leave(e, f, orig):
                            f.configure(border_color="#3a3a4a", border_width=1)

                        col_f.bind("<Button-1>", lambda e, h=hex_c: _copy_color(h))
                        col_f.bind("<Enter>", lambda e, f=col_f, o=hex_c: _on_enter(e, f, o))
                        col_f.bind("<Leave>", lambda e, f=col_f, o=hex_c: _on_leave(e, f, o))

                        lbl = ctk.CTkLabel(col_f, text=hex_c, font=ctk.CTkFont(size=7),
                                            text_color="white" if (r+g+b)/3 < 128 else "black",
                                            fg_color="transparent")
                        lbl.place(relx=0.5, rely=1.0, anchor="s", y=-2)

                    # Tabla de valores
                    val_frame = ctk.CTkFrame(vent, fg_color="#111820", corner_radius=8)
                    val_frame.pack(fill="x", padx=15, pady=4)
                    ctk.CTkLabel(val_frame, text="Valores detallados", font=ctk.CTkFont(size=11, weight="bold")
                                 ).pack(anchor="w", padx=10, pady=(6, 2))
                    for i, (r, g, b) in enumerate(colores_raw[:5]):
                        hex_c = rgb_to_hex(r, g, b)
                        row = ctk.CTkFrame(val_frame, fg_color="transparent")
                        row.pack(fill="x", padx=10, pady=1)
                        sw_small = ctk.CTkFrame(row, fg_color=hex_c, width=24, height=24, corner_radius=4)
                        sw_small.pack(side="left", padx=(0, 6))
                        sw_small.pack_propagate(False)
                        ctk.CTkLabel(row, text=f"#{i+1}", font=ctk.CTkFont(size=9, weight="bold"),
                                     width=30).pack(side="left")
                        ctk.CTkLabel(row, text=hex_c, font=ctk.CTkFont(family="Consolas", size=10),
                                     text_color="#aaccee").pack(side="left", padx=(0, 4))

                        def _cp(h):
                            return lambda: pyperclip.copy(h)
                        ctk.CTkButton(row, text=hex_c, width=90, height=20, fg_color="#1a4a5a",
                                      font=ctk.CTkFont(size=9), command=_cp(hex_c)).pack(side="left", padx=1)
                        ctk.CTkLabel(row, text=f"RGB({r},{g},{b})", font=ctk.CTkFont(size=9),
                                     text_color="#888888").pack(side="left", padx=(4, 0))
                        ctk.CTkLabel(row, text=rgb_to_hsl(r, g, b), font=ctk.CTkFont(size=8),
                                     text_color="#666666").pack(side="left", padx=(4, 0))
                        comp = complementary(r, g, b)
                        ctk.CTkLabel(row, text=f"Comp: {comp}", font=ctk.CTkFont(size=8),
                                     text_color="#f59e0b").pack(side="left", padx=(4, 0))

                    # Complementarios del primer color
                    r0, g0, b0 = colores_raw[0]
                    analogo = analog_colors(r0, g0, b0)
                    comp_frame = ctk.CTkFrame(vent, fg_color="#111820", corner_radius=8)
                    comp_frame.pack(fill="x", padx=15, pady=4)
                    ctk.CTkLabel(comp_frame, text="Colores complementarios y análogos",
                                 font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(6, 2))
                    analogs_row = ctk.CTkFrame(comp_frame, fg_color="transparent")
                    analogs_row.pack(padx=10, pady=(0, 6))
                    comp_c = complementary(r0, g0, b0)
                    for lab, col in [("Complementario", comp_c)] + list(zip(["A-1", "A-2", "A+1", "A+2"], analogo)):
                        f2 = ctk.CTkFrame(analogs_row, fg_color=col, width=50, height=40, corner_radius=6)
                        f2.pack(side="left", padx=3)
                        f2.pack_propagate(False)
                        ctk.CTkLabel(f2, text=lab, font=ctk.CTkFont(size=8),
                                     text_color="white" if sum(int(col[i*2+1:i*2+3], 16) for i in range(3))/3 < 128 else "black",
                                     fg_color="transparent").place(relx=0.5, rely=0.5, anchor="center")
                        f2.bind("<Button-1>", lambda e, h=col: (pyperclip.copy(h), self.set_estado(f"📋 {h} copiado", "#2ecc71")))

                    btn_row = ctk.CTkFrame(vent, fg_color="transparent")
                    btn_row.pack(pady=10)
                    hex_str = ", ".join(hex_codes)

                    def _guardar_paleta():
                        # Pedir nombre al usuario en vez de auto-numerar
                        from tkinter import simpledialog
                        nombre = simpledialog.askstring(
                            "Guardar paleta",
                            "Nombre de la paleta:",
                            initialvalue=f"Paleta {len(self.store.paletas or []) + 1}",
                            parent=vent,
                        )
                        if not nombre:
                            return
                        paleta = {
                            "nombre": nombre.strip(),
                            "hex": hex_codes,
                            "rgb": [list(c) for c in colores_raw[:5]],
                            "timestamp": str(datetime.datetime.now())[:19],
                        }
                        self.store.paletas.append(paleta)
                        self.store._guardar("paletas")  # FIX: era store.guardar() inexistente
                        self.set_estado(f"💾 Paleta '{paleta['nombre']}' guardada", "#2ecc71")

                    ctk.CTkButton(btn_row, text="📋 Copiar HEX", width=120, height=28,
                                  command=lambda: pyperclip.copy(hex_str)).pack(side="left", padx=4)
                    ctk.CTkButton(btn_row, text="🎨 Añadir al prompt", width=140, height=28, fg_color="#1a7a3c",
                                  command=lambda: (self._aplicar_atajo_tags(f"color palette: {hex_str}"),
                                                    vent.destroy())).pack(side="left", padx=4)
                    ctk.CTkButton(btn_row, text="💾 Guardar paleta", width=130, height=28, fg_color="#4a1a6a",
                                  command=_guardar_paleta).pack(side="left", padx=4)
                    ctk.CTkButton(btn_row, text="📚 Biblioteca", width=110, height=28, fg_color="#1a4a5a",
                                  command=lambda: self._abrir_biblioteca_paletas(vent)).pack(side="left", padx=4)

                    self.set_estado("🎨 Paleta extraída", "#2ecc71")
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))

        threading.Thread(target=_worker, daemon=True).start()

    def _abrir_biblioteca_paletas(self, parent_window=None):
        """Biblioteca de paletas guardadas con búsqueda, aplicar y borrar."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        bg_card = "#ffffff" if is_lt else "#1a1a2e"
        text_main = "#111827" if is_lt else "#e5e7eb"
        text_muted = "#4b5563" if is_lt else "#9ca3af"

        win = GPromptWindow(parent_window or self)
        win.title("📚 Biblioteca de paletas")
        win.geometry("560x600")
        win.transient(parent_window or self)

        ctk.CTkLabel(win, text="📚 Biblioteca de paletas",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4))

        # Cabecera con contador
        cont_var = ctk.StringVar(value="")
        ctk.CTkLabel(win, textvariable=cont_var, font=ctk.CTkFont(size=10),
                     text_color=text_muted).pack(pady=(0, 6))

        scroll = ctk.CTkScrollableFrame(win,
                                        fg_color=("#f3f4f6" if is_lt else "#0d1117"))
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        def _refrescar():
            for w in scroll.winfo_children():
                w.destroy()
            paletas = self.store.paletas or []
            cont_var.set(f"{len(paletas)} paletas guardadas")
            if not paletas:
                ctk.CTkLabel(scroll, text="No hay paletas guardadas todavía.\n"
                             "Extrae una imagen y pulsa '💾 Guardar paleta'.",
                             text_color=text_muted, justify="center"
                             ).pack(pady=30)
                return

            for idx, p in enumerate(paletas):
                card = ctk.CTkFrame(scroll, fg_color=bg_card, corner_radius=8)
                card.pack(fill="x", padx=4, pady=4)

                # Cabecera con nombre + timestamp + botones
                hdr = ctk.CTkFrame(card, fg_color="transparent")
                hdr.pack(fill="x", padx=12, pady=(8, 4))
                ctk.CTkLabel(hdr, text=p.get("nombre", f"Paleta {idx+1}"),
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=text_main).pack(side="left")
                if p.get("timestamp"):
                    ctk.CTkLabel(hdr, text=p["timestamp"][:10],
                                 font=ctk.CTkFont(size=9),
                                 text_color=text_muted).pack(side="left", padx=10)

                def _aplicar(pal=p):
                    hex_str = ", ".join(pal.get("hex", []))
                    self._aplicar_atajo_tags(f"color palette: {hex_str}")
                    self.set_estado(f"🎨 Paleta '{pal.get('nombre','')}' añadida al prompt",
                                    "#2ecc71")

                def _copiar(pal=p):
                    pyperclip.copy(", ".join(pal.get("hex", [])))
                    self.set_estado(f"📋 Hex de '{pal.get('nombre','')}' copiados",
                                    "#2ecc71")

                def _borrar(i=idx, nombre=p.get("nombre", "?")):
                    from tkinter import messagebox as _mb
                    if not _mb.askyesno("Confirmar",
                                        f"¿Borrar paleta '{nombre}'?",
                                        parent=win):
                        return
                    try:
                        self.store.paletas.pop(i)
                        self.store._guardar("paletas")
                        _refrescar()
                    except Exception as e:
                        logger.warning(f"Borrar paleta: {e}")

                ctk.CTkButton(hdr, text="🎨 Aplicar", width=80, height=24,
                              fg_color="#1a7a3c",
                              command=_aplicar).pack(side="right", padx=2)
                ctk.CTkButton(hdr, text="📋", width=32, height=24,
                              command=_copiar).pack(side="right", padx=2)
                ctk.CTkButton(hdr, text="🗑", width=32, height=24,
                              fg_color="#7a1a1a", hover_color="#5a0f0f",
                              command=_borrar).pack(side="right", padx=2)

                # Swatches de colores
                sw_row = ctk.CTkFrame(card, fg_color="transparent")
                sw_row.pack(fill="x", padx=12, pady=(0, 10))
                for hex_c in p.get("hex", []):
                    f = ctk.CTkFrame(sw_row, fg_color=hex_c, width=58, height=40,
                                     corner_radius=6)
                    f.pack(side="left", padx=3)
                    f.pack_propagate(False)
                    # Color del label legible según oscuridad del swatch
                    try:
                        r, g, b = int(hex_c[1:3], 16), int(hex_c[3:5], 16), int(hex_c[5:7], 16)
                        text_c = "white" if (r+g+b)/3 < 128 else "black"
                    except Exception:
                        text_c = "white"
                    ctk.CTkLabel(f, text=hex_c, font=ctk.CTkFont(size=8),
                                 text_color=text_c, fg_color="transparent"
                                 ).place(relx=0.5, rely=0.5, anchor="center")
                    # Click para copiar el color individual
                    def _cp_color(h=hex_c):
                        pyperclip.copy(h)
                        self.set_estado(f"📋 {h} copiado", "#2ecc71")
                    f.bind("<Button-1>", lambda _e, h=hex_c: _cp_color(h))

        _refrescar()

        ctk.CTkButton(win, text="Cerrar", width=100, height=30,
                      fg_color="#444", hover_color="#555",
                      command=win.destroy).pack(pady=8)

    def _cmd_modo_cliente(self):
        """Modo Cliente: brief simplificado para generar 5 propuestas profesionales.

        Recuerda el último brief (preferencias.modo_cliente_ultimo_brief)
        y ofrece plantillas predefinidas para arrancar rápido.
        """
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        vent = GPromptWindow(self)
        vent.title("💼 Modo Cliente")
        vent.geometry("640x720")
        vent.transient(self)

        ctk.CTkLabel(vent, text="💼 Modo Cliente — Brief profesional",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text="Define un brief y genera 5 propuestas profesionales coherentes",
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
        ctk.CTkLabel(plantilla_row, text="Plantilla:",
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
        ctk.CTkLabel(frame_img, text="📎 Imagen de referencia (opcional):",
                     font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(frame_img, text="Logo del cliente, moodboard, ejemplo de estilo deseado...",
                     font=ctk.CTkFont(size=9), text_color=c["muted_text"]).pack(anchor="w", padx=10)

        cliente_state = {"imagen": None, "descripcion": ""}
        lbl_estado_img = ctk.CTkLabel(frame_img, text="(sin imagen cargada)",
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
                        desc, motor = self.vision.describir(img, "imagen", lambda m: None)
                        cliente_state["descripcion"] = desc
                        lbl_estado_img.configure(text=f"✅ Imagen analizada (vision: {motor})", text_color="#2ecc71")
                    except Exception as e:
                        lbl_estado_img.configure(text=f"❌ Error al analizar: {e}", text_color="#e74c3c")
                threading.Thread(target=_analizar, daemon=True).start()
            except Exception as e:
                lbl_estado_img.configure(text=f"❌ Error: {e}", text_color="#e74c3c")

        def _quitar_imagen():
            cliente_state["imagen"] = None
            cliente_state["descripcion"] = ""
            lbl_estado_img.configure(text="(sin imagen cargada)", text_color=c["muted_text"])

        f_btns_img = ctk.CTkFrame(frame_img, fg_color="transparent")
        f_btns_img.pack(fill="x", padx=10, pady=(2, 8))
        ctk.CTkButton(f_btns_img, text="📂 Cargar imagen", width=140, height=26, fg_color="#1a4a5a",
                      command=_cargar_imagen_cliente).pack(side="left", padx=2)
        ctk.CTkButton(f_btns_img, text="✕ Quitar", width=80, height=26, fg_color="#5a1a1a",
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
            _prefs = self.store.cargar_preferencias() or {}
            ultimo = _prefs.get("modo_cliente_ultimo_brief") or {}
            for k, ent in campos.items():
                if ultimo.get(k):
                    ent.insert(0, ultimo[k])
        except Exception as _e:
            logger.debug(f"[silent] cargar último brief: {_e}")

        def _generar_propuestas():
            brief_dict = {k: v.get().strip() for k, v in campos.items()}
            if not any(brief_dict.values()):
                self.set_estado("⚠️ Rellena al menos un campo del brief.", "#e67e22")
                return

            # Persistir último brief
            try:
                _p = self.store.cargar_preferencias() or {}
                _p["modo_cliente_ultimo_brief"] = brief_dict
                self.store.guardar_preferencias(_p)
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

        ctk.CTkButton(vent, text="✨ Generar 5 propuestas", width=220, height=34,
                      fg_color="#1a7a3c",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=_generar_propuestas).pack(pady=15)

    def _generar_propuestas_cliente(self, brief):
        """Genera 5 propuestas basadas en un brief."""
        self.set_estado("💼 Generando 5 propuestas profesionales...", "#f39c12")
        self.toggle_botones(False)

        specs = self.get_current_model_specs()
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
                resp = self.deepseek.generar(peticion, temperature=0.7, max_tokens=4000)
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
                    bloques = self._parsear_bloques_numerados(resp, n_esperado=5)
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
                    self.set_estado(
                        f"💼 {len(propuestas)} propuestas profesionales generadas",
                        "#2ecc71",
                    )
                    self.toggle_botones(True)
                    self._sonar_completado()
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

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

        vent = GPromptWindow(self)
        vent.title("💼 Propuestas profesionales")
        vent.geometry("900x720")
        vent.transient(self)

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
                self.actualizar_salida(completo)
                self.set_estado(f"✅ Propuesta '{nom}' aplicada al prompt", "#2ecc71")
                vent.destroy()

            def _copiar(p=positivo, n=negativo, nom=titulo):
                completo = f"POSITIVE PROMPT: {p}\n" + (f"NEGATIVE PROMPT: {n}" if n else "")
                pyperclip.copy(completo)
                self.set_estado(f"📋 Propuesta '{nom}' copiada al portapapeles", "#2ecc71")

            def _guardar_prop(nom=titulo, p=positivo, neg=negativo):
                """Guarda como FAVORITO con marca de origen. Antes intentaba
                guardar en self.store.propuestas que no existe + llamaba a
                self.store.guardar() que no existe → crasheaba."""
                completo = f"POSITIVE PROMPT: {p}"
                if neg:
                    completo += f"\nNEGATIVE PROMPT: {neg}"
                try:
                    self.store.agregar_favorito({
                        "fecha":      datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "modo":       self.modo_var.get() if hasattr(self, "modo_var") else "imagen",
                        "plataforma": self.plataforma_var.get() if hasattr(self, "plataforma_var") else "",
                        "estilos":    "",
                        "ratio":      self.ratio_var.get() if hasattr(self, "ratio_var") else "",
                        "nsfw":       False,
                        "personaje":  "",
                        "lora":       "",
                        "destino":    "",
                        "brief":      brief[:200],
                        "origen":     "modo_cliente",
                        "nombre":     nom,
                        "contenido":  completo,
                    })
                    self.set_estado(f"💾 Propuesta '{nom}' guardada en Favoritos", "#2ecc71")
                except Exception as e:
                    self.set_estado(f"❌ No se pudo guardar: {e}", "#e74c3c")

            ctk.CTkButton(btn_row, text="✅ Usar propuesta", width=150, height=30, fg_color="#1a7a3c",
                          font=ctk.CTkFont(size=10, weight="bold"), command=_usar
                          ).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text="📋 Copiar", width=100, height=30, fg_color="#1a4a5a",
                          font=ctk.CTkFont(size=10), command=_copiar
                          ).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text="💾 Guardar", width=100, height=30, fg_color="#4a1a6a",
                          font=ctk.CTkFont(size=10), command=_guardar_prop
                          ).pack(side="left", padx=2)
            ctk.CTkLabel(btn_row, text=f"   {len(positivo)} chars",
                         font=ctk.CTkFont(size=9), text_color="#666666").pack(side="left", padx=(4, 0))

        ctk.CTkButton(vent, text="Cerrar", width=140, height=30, fg_color="#475569",
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

        vent = GPromptWindow(self)
        vent.title("🎭 Moodboard — Estilo común")
        vent.geometry("720x680")
        vent.transient(self)

        ctk.CTkLabel(vent, text="🎭 Moodboard — Detecta el estilo común de tus imágenes",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text="Añade imágenes con estilo similar (mínimo 2). Usa la imagen ya cargada como referencia.",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 6))

        # ── Imagen ya cargada ──
        if self.imagen_cargada:
            frame_ref = ctk.CTkFrame(vent, fg_color=c["fg_dark"], corner_radius=6)
            frame_ref.pack(fill="x", padx=15, pady=(0, 6))
            hdr_ref = ctk.CTkFrame(frame_ref, fg_color="transparent")
            hdr_ref.pack(fill="x", padx=10, pady=(6, 2))
            ctk.CTkLabel(hdr_ref, text="🖼 Imagen de referencia ya cargada",
                          font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
            ctk.CTkLabel(hdr_ref, text="Se usará automáticamente",
                          font=ctk.CTkFont(size=9), text_color="#2ecc71").pack(side="left", padx=(6, 0))
            preview_lbl = ctk.CTkLabel(frame_ref, text="")
            preview_lbl.pack(padx=10, pady=(0, 4))

        # ── Selector de archivos adicionales ──
        frame_arch = ctk.CTkFrame(vent, fg_color=c["fg_dark"], corner_radius=6)
        frame_arch.pack(fill="x", padx=15, pady=(0, 6))

        archivos_state = {"rutas": list(archivos_seleccionados)}

        lbl_count = ctk.CTkLabel(frame_arch, text="0 imágenes seleccionadas",
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
            from PIL import Image as _PIL_val, UnidentifiedImageError
            import os
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
        ctk.CTkButton(btn_row, text="➕ Añadir imágenes", width=140, height=26, fg_color="#1a4a5a",
                      command=_anadir_mas).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="🗑 Limpiar", width=100, height=26,
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
            if self.imagen_cargada:
                todas_imagenes.append(self.imagen_cargada)
            fallos_open = []
            if archivos_state["rutas"]:
                from PIL import Image as _PIL2, UnidentifiedImageError
                import os
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
                return self.set_estado("⚠️ Necesitas al menos 2 imágenes (usa la cargada o añade más).", "#e67e22")

            self.set_estado(f"🎭 Analizando {total_imgs} imágenes...", "#f39c12")
            self.toggle_botones(False)
            lbl_prog.pack(anchor="w")
            progress_bar.pack(fill="x", pady=(2, 0))
            lbl_prog.configure(text=f"Analizando imagen 1/{total_imgs}...")
            progress_bar.set(0)

            def _trabajar():
                try:
                    descripciones = []
                    for i, img in enumerate(todas_imagenes):
                        progreso_state["n"] = i + 1
                        self.after(0, lambda n=i+1, t=total_imgs:
                                   (lbl_prog.configure(text=f"Analizando imagen {n}/{t}..."),
                                    progress_bar.set(n / t)))
                        desc, _ = self.vision.describir(img, "imagen", lambda m: None)
                        descripciones.append(desc)

                    self.after(0, lambda: lbl_prog.configure(text="Extrayendo estilo común..."))
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
                    resp = self.deepseek.generar(peticion, temperature=0.4, max_tokens=2000)
                    resp = limpiar_marcadores(resp)

                    def _mostrar():
                        lbl_prog.pack_forget()
                        progress_bar.pack_forget()
                        vent2 = GPromptWindow(self)
                        vent2.title("🎭 Estilo común detectado")
                        vent2.geometry("720x650")
                        vent2.transient(self)
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
                                self.actualizar_salida(template)
                                vent2.destroy()
                                self.set_estado("🎭 Template aplicado", "#2ecc71")

                        def _guardar_estilo():
                            from tkinter import simpledialog
                            import re as _re
                            prefs_g = self.store.cargar_preferencias()
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
                            self.store.guardar_preferencias(prefs_g)
                            self.set_estado(f"💾 Estilo '{nombre}' guardado en biblioteca", "#2ecc71")

                        ctk.CTkButton(btn_row2, text="✅ Aplicar template", width=140, height=28,
                                      fg_color="#1a7a3c", command=_aplicar_template).pack(side="left", padx=4)
                        ctk.CTkButton(btn_row2, text="💾 Guardar estilo", width=140, height=28, fg_color="#4a1a6a",
                                      command=_guardar_estilo).pack(side="left", padx=4)
                        ctk.CTkButton(btn_row2, text="📋 Copiar análisis", width=140, height=28,
                                      command=lambda: pyperclip.copy(resp)).pack(side="left", padx=4)

                        self.toggle_botones(True)
                        self.set_estado("🎭 Estilo común detectado", "#2ecc71")
                    self.after(0, _mostrar)
                except Exception as e:
                    self.after(0, lambda: lbl_prog.pack_forget())
                    self.after(0, lambda: progress_bar.pack_forget())
                    self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                    self.after(0, lambda: self.toggle_botones(True))

            threading.Thread(target=_trabajar, daemon=True).start()

        botones_finales = ctk.CTkFrame(vent, fg_color="transparent")
        botones_finales.pack(pady=8)
        ctk.CTkButton(botones_finales, text="🎭 Analizar estilo común",
                      width=240, height=38,
                      fg_color="#a64aa6", hover_color="#7a2a7a",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      text_color="#ffffff",
                      command=_ejecutar_moodboard).pack(side="left", padx=4)
        ctk.CTkButton(botones_finales, text="📚 Mis estilos",
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

        win = GPromptWindow(parent_window or self)
        win.title("📚 Mis estilos de moodboard")
        win.geometry("640x560")
        win.transient(parent_window or self)

        ctk.CTkLabel(win, text="📚 Estilos detectados con moodboard",
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
            prefs_l = self.store.cargar_preferencias()
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
                        self.set_estado("⚠️ Este estilo no tiene template aplicable",
                                        "#e67e22")
                        return
                    self.actualizar_salida(tpl)
                    self.set_estado(f"🎭 Estilo '{e.get('nombre','')}' aplicado",
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
                    ctk.CTkButton(ver, text="Cerrar", command=ver.destroy
                                  ).pack(pady=8)

                def _borrar(i=idx, nombre=est.get("nombre","?")):
                    from tkinter import messagebox as _mb
                    if not _mb.askyesno("Confirmar",
                                        f"¿Borrar estilo '{nombre}'?",
                                        parent=win):
                        return
                    prefs_b = self.store.cargar_preferencias()
                    lst = prefs_b.get("estilos_moodboard", []) or []
                    if 0 <= i < len(lst):
                        lst.pop(i)
                        prefs_b["estilos_moodboard"] = lst
                        self.store.guardar_preferencias(prefs_b)
                    _refrescar()

                btn_row = ctk.CTkFrame(card, fg_color="transparent")
                btn_row.pack(fill="x", padx=10, pady=(4, 8))
                ctk.CTkButton(btn_row, text="✅ Aplicar template",
                              width=160, height=26,
                              fg_color="#1a7a3c" if tiene_template else c["fg_dark"],
                              state="normal" if tiene_template else "disabled",
                              font=ctk.CTkFont(size=10),
                              command=_aplicar).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text="👁 Ver análisis",
                              width=120, height=26,
                              font=ctk.CTkFont(size=10),
                              command=_ver).pack(side="left", padx=2)
                ctk.CTkButton(btn_row, text="🗑", width=40, height=26,
                              fg_color="#7a1a1a", hover_color="#5a0f0f",
                              command=_borrar).pack(side="right", padx=2)

        _refrescar()
        ctk.CTkButton(win, text="Cerrar", width=110, height=28,
                      command=win.destroy).pack(pady=(0, 12))
