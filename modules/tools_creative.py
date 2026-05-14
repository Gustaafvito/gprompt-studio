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
                resp = self.deepseek.generar(peticion, temperature=1.0, max_tokens=200, modelo_llm=self.llm_var.get())
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

    def _cmd_pulse(self):
        """Modo Pulse: genera 3 prompts con distinta temperatura (0.3, 0.6, 0.9)."""
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.set_estado("⚠️ Escribe una idea base primero.", "#e67e22")
        try: self._sesion_log("⚡ Pulse: generó 3 versiones (conservador/equilibrado/creativo)")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.set_estado("⚡ Pulse: generando 3 versiones (conservadora → creativa)...", "#f39c12")
        self.toggle_botones(False)

        temperaturas = [
            (0.3, "🎯 Conservador (T=0.3)"),
            (0.6, "⚖️ Equilibrado (T=0.6)"),
            (0.9, "🎨 Creativo (T=0.9)"),
        ]
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
                resp = self.deepseek.generar(peticion, temperature=temp, max_tokens=2000, modelo_llm=self.llm_var.get())
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
                self.set_estado("⚡ Pulse: 3 versiones listas — compara y elige", "#2ecc71")
                self.toggle_botones(True)
                self._sonar_completado()
                self._notificar_sistema("⚡ Pulse completado", "3 versiones del prompt listas para comparar")
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
                resp = self.deepseek.generar(peticion, temperature=0.2, max_tokens=400, modelo_llm=self.llm_var.get())
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
        """Analiza la idea y sugiere el mejor modelo según contenido."""
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 10:
            return self.set_estado("⚠️ Escribe una idea más detallada.", "#e67e22")
        try: self._sesion_log("🤖 Sugerir modelo: analizó idea")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.set_estado("🤖 Analizando idea para sugerir modelo...", "#f39c12")

        modo = self.modo_var.get()
        # Lista de modelos disponibles
        if modo == "imagen":
            modelos_lista = [m for m in MODELOS_IMAGEN_FLAT if not m.startswith("──")]
        elif modo == "video":
            modelos_lista = [m for m in MODELOS_VIDEO_FLAT if not m.startswith("──")]
        else:
            modelos_lista = [m for m in MODELOS_AUDIO_FLAT if not m.startswith("──")]

        # Resumen de specs para el LLM
        specs_resumen = []
        for m in modelos_lista[:15]:  # limitar para no saturar
            s = get_image_model_specs(m) or get_model_specs(m) or get_audio_model_specs(m) or {}
            specs_resumen.append(f"- {m}: {s.get('best_for', '')[:120]}")

        peticion = (
            f"Analiza esta idea y sugiere el MEJOR modelo de {modo} para generarla:\n\n"
            f"IDEA: {idea}\n\n"
            f"MODELOS DISPONIBLES:\n" + "\n".join(specs_resumen) + "\n\n"
            f"Responde EN ESPAÑOL con este formato exacto:\n"
            f"MODELO RECOMENDADO: [nombre exacto del modelo]\n"
            f"RAZÓN: [1-2 frases explicando por qué]\n"
            f"ALTERNATIVAS: [otros 1-2 modelos válidos]"
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.3, max_tokens=400, modelo_llm=self.llm_var.get())
                resp = limpiar_marcadores(resp)

                # Extraer modelo recomendado
                import re
                m = re.search(r'MODELO\s+RECOMENDADO\s*:?\s*([^\n]+)', resp, re.IGNORECASE)
                modelo_sug = m.group(1).strip().strip("[").strip("]").strip() if m else None

                def _mostrar():
                    vent = ctk.CTkToplevel(self)
                    vent.title("🤖 Modelo sugerido")
                    vent.geometry("550x350")
                    vent.transient(self)

                    ctk.CTkLabel(vent, text="🤖 Sugerencia de modelo", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 8))

                    txt = ctk.CTkTextbox(vent, font=ctk.CTkFont(size=11), wrap="word", height=200)
                    txt.pack(fill="both", expand=True, padx=15, pady=10)
                    txt.insert("1.0", resp)
                    txt.configure(state="disabled")

                    btn_row = ctk.CTkFrame(vent, fg_color="transparent")
                    btn_row.pack(pady=10)

                    if modelo_sug and modelo_sug in modelos_lista:
                        def _aplicar():
                            if modo == "imagen" and hasattr(self, 'combo_modelo_imagen'):
                                self.combo_modelo_imagen.set(modelo_sug)
                                self._on_modelo_imagen_cambio()
                            elif modo == "video" and hasattr(self, 'combo_modelo_video'):
                                self.combo_modelo_video.set(modelo_sug)
                            elif modo == "audio" and hasattr(self, 'combo_modelo_audio'):
                                self.combo_modelo_audio.set(modelo_sug)
                            vent.destroy()
                            self.set_estado(f"✅ Modelo {modelo_sug} aplicado", "#2ecc71")
                        ctk.CTkButton(btn_row, text=f"✅ Usar {modelo_sug[:25]}", width=180, height=30,
                                      fg_color="#1a7a3c", command=_aplicar).pack(side="left", padx=4)
                    ctk.CTkButton(btn_row, text="Cerrar", width=80, height=30,
                                  command=vent.destroy).pack(side="left", padx=4)

                    self.set_estado("🤖 Sugerencia lista", "#2ecc71")
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))

        threading.Thread(target=_worker, daemon=True).start()

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
                resp = self.deepseek.generar(peticion, temperature=0.3, max_tokens=400, modelo_llm=self.llm_var.get())
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
        vent = ctk.CTkToplevel(self)
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

        # Relación entre ellos
        ctk.CTkLabel(vent, text="Relación / contexto entre ellos:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=15, pady=(10, 2))
        txt_relacion = ctk.CTkTextbox(vent, height=60, font=ctk.CTkFont(size=11))
        txt_relacion.pack(fill="x", padx=15, pady=(0, 8))
        txt_relacion.insert("1.0", "ej: están negociando un contrato, primero plano de uno, los otros al fondo desenfocados")

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

            relacion = txt_relacion.get("1.0", "end").strip()

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
                resp = self.deepseek.generar(peticion, temperature=0.3, max_tokens=2500, modelo_llm=self.llm_var.get())
                resp = limpiar_marcadores(resp)

                def _mostrar():
                    is_lt = ctk.get_appearance_mode().lower() == "light"
                    c = get_theme_colors(is_lt)
                    vent = ctk.CTkToplevel(self)
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
        """Muestra la biblioteca de ADNs guardados."""
        prefs = self.store.cargar_preferencias()
        adns = prefs.get("adns_guardados", [])
        
        if not adns:
            return self.set_estado("⚠️ No hay ADNs guardados.", "#e67e22")
        
        vent = ctk.CTkToplevel(self)
        vent.title("📚 Biblioteca de ADNs")
        vent.geometry("700x500")
        vent.transient(self)
        
        is_light = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_light)
        
        # Header
        hdr = ctk.CTkFrame(vent, fg_color=c["fg_dark"])
        hdr.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(hdr, text="🧬 ADNs Guardados", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        ctk.CTkLabel(hdr, text=f"{len(adns)} guardado(s)", text_color=c["muted_text"]).pack(side="right", padx=10)
        
        # Scroll frame para la lista
        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        for idx, item in enumerate(adns):
            nombre = item.get("nombre", f"ADN {idx+1}")
            fecha = item.get("fecha", "")
            motor = item.get("motor", "")
            adn_data = item.get("adn", {})
            
            # Obtener info del sujeto y estilo
            sujeto = adn_data.get("sujeto", {})
            if isinstance(sujeto, list):
                sujeto = sujeto[0] if sujeto else {}
            tipo = sujeto.get("tipo", "") if isinstance(sujeto, dict) else ""
            
            estilo = adn_data.get("estilo", {})
            estetica = ""
            if isinstance(estilo, dict):
                estetica = estilo.get("estetica", "")
            
            card = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=8)
            card.pack(fill="x", pady=5)
            
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(fill="x", padx=10, pady=8)
            
            ctk.CTkLabel(info_frame, text=nombre, font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"{tipo} • {estetica}", text_color=c["muted_text"], font=ctk.CTkFont(size=11)).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"{fecha} • {motor}", text_color=c["muted_text"], font=ctk.CTkFont(size=10)).pack(anchor="w")
            
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=(0, 8))
            
            def _cargar(idx=idx, item=item):
                # Mostrar el ADN en una ventana de solo lectura
                ver = ctk.CTkToplevel(self)
                ver.title(f"📋 {item.get('nombre', 'ADN')}")
                ver.geometry("600x500")
                ver.transient(self)
                
                import json
                json_str = json.dumps(item.get("adn", {}), indent=2, ensure_ascii=False)
                
                txt = ctk.CTkTextbox(ver, font=ctk.CTkFont(family="Consolas", size=11), wrap="none")
                txt.pack(fill="both", expand=True, padx=10, pady=10)
                txt.insert("1.0", json_str)
                txt.configure(state="disabled")
                
                # Botón usar en idea
                def _usar_en_idea():
                    prompt = ", ".join([
                        item["adn"].get("sujeto", {}).get("tipo", ""),
                        item["adn"].get("estilo", {}).get("estetica", ""),
                        item["adn"].get("iluminacion", {}).get("tipo", ""),
                        item["adn"].get("escena", {}).get("ubicacion", "")
                    ])
                    self.txt_idea.delete("1.0", "end")
                    self.txt_idea.insert("1.0", prompt)
                    ver.destroy()
                    self.set_estado(f"🧬 '{nombre}' cargado en idea", "#2ecc71")
                
                btn_frame2 = ctk.CTkFrame(ver, fg_color="transparent")
                btn_frame2.pack(pady=(0, 10))
                ctk.CTkButton(btn_frame2, text="🎯 Usar en idea", command=_usar_en_idea).pack(side="left", padx=5)
                ctk.CTkButton(btn_frame2, text="Cerrar", command=ver.destroy).pack(side="left", padx=5)
            
            def _borrar(idx=idx):
                from tkinter import messagebox
                if messagebox.askyesno("🗑 Eliminar", f"¿Borrar '{nombre}'?"):
                    prefs = self.store.cargar_preferencias()
                    prefs["adns_guardados"].pop(idx)
                    self.store.guardar_preferencias(prefs)
                    vent.destroy()
                    self.set_estado(f"🧬 '{nombre}' eliminado", "#e67e22")
            
            ctk.CTkButton(btn_frame, text="👁 Ver", width=70, height=25, command=_cargar).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="🗑", width=40, height=25, fg_color="#c0392b", hover_color="#e74c3c", command=_borrar).pack(side="right", padx=2)
        
        # Cerrar
        ctk.CTkButton(vent, text="Cerrar", command=vent.destroy).pack(pady=10)

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

                    vent = ctk.CTkToplevel(self)
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
                        bloqueos[cat_key] = {"bloqueado": False, "label": None}

                        def _toggle_bloqueo(key=cat_key):
                            bloqueos[key]["bloqueado"] = not bloqueos[key]["bloqueado"]
                            icono = "🔒" if bloqueos[key]["bloqueado"] else "🔓"
                            color = "#c0392b" if bloqueos[key]["bloqueado"] else "#27ae60"
                            btn_lock.configure(text=icono, fg_color=color)
                            estado = "🔒 BLOQUEADO" if bloqueos[key]["bloqueado"] else "🔓 DESBLOQUEADO"
                            bloqueos[key]["label"].configure(text=estado, text_color=color)

                        btn_lock = ctk.CTkButton(hdr, text="🔓", width=30, height=22,
                                                 fg_color="#27ae60", hover_color="#2ecc71",
                                                 command=_toggle_bloqueo)
                        btn_lock.pack(side="left", padx=(0, 5))

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
                                partes.append(plantilla["escena"].format(
                                    ubicacion_exacta=esc.get("ubicacion_exacta", ""),
                                    tipo_exacto=ilu.get("tipo_exacto", "")
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
                resp = self.deepseek.generar(peticion, temperature=0.3, max_tokens=300, modelo_llm=self.llm_var.get())
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
        """ADN visual: extrae rasgos detallados de imagen ref y los guarda como anclaje inmutable."""
        if not self.imagen_cargada:
            self.set_estado("⚠️ Carga una imagen de referencia primero.", "#e67e22")
            return

        self.set_estado("🧬 Extrayendo ADN visual (rasgos exactos)...", "#f39c12")
        self.toggle_botones(False)

        def _worker():
            try:
                # 1. Describir la imagen con vision
                def on_status(msg): self.after(0, lambda: self.set_estado(msg, "#f39c12"))
                desc, motor = self.vision.describir(self.imagen_cargada, "imagen", on_status)

                # 2. Extraer ADN específico
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
                adn = self.deepseek.generar(peticion, temperature=0.2, max_tokens=800, modelo_llm=self.llm_var.get())
                adn = limpiar_marcadores(adn).strip()

                # Guardar ADN en el atributo
                self._anclaje_visual = adn

                def _mostrar():
                    is_lt = ctk.get_appearance_mode().lower() == "light"
                    c = get_theme_colors(is_lt)
                    vent = ctk.CTkToplevel(self)
                    vent.title("🧬 ADN visual extraído")
                    vent.geometry("700x500")
                    vent.transient(self)
                    ctk.CTkLabel(vent, text="🧬 ADN visual — Rasgos inmutables", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
                    ctk.CTkLabel(vent, text=f"Vision: {motor}  ·  Estos rasgos se mantendrán en TODAS las variantes futuras",
                                  font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

                    txt = ctk.CTkTextbox(vent, font=ctk.CTkFont(size=11), wrap="word", height=350)
                    txt.pack(fill="both", expand=True, padx=15, pady=(0, 5))
                    txt.insert("1.0", adn)

                    btn_frame = ctk.CTkFrame(vent, fg_color="transparent")
                    btn_frame.pack(pady=10)

                    def _guardar_editado():
                        self._anclaje_visual = txt.get("1.0", "end").strip()
                        vent.destroy()
                        self.set_estado("🧬 ADN visual guardado y activo en próximas generaciones", "#2ecc71")

                    def _desactivar():
                        self._anclaje_visual = None
                        vent.destroy()
                        self.set_estado("🧬 ADN visual desactivado")

                    ctk.CTkButton(btn_frame, text="✅ Guardar y activar", width=160, height=30, fg_color="#1a7a3c",
                                  command=_guardar_editado).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text="🚫 Desactivar ADN", width=140, height=30, fg_color="#5a1a1a",
                                  command=_desactivar).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text="📋 Copiar", width=80, height=30,
                                  command=lambda: pyperclip.copy(adn)).pack(side="left", padx=4)

                    self.toggle_botones(True)
                    self.set_estado("🧬 ADN visual extraído — guarda para activarlo", "#2ecc71")
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

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
        sel = ctk.CTkToplevel(self)
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

        # Qué variar — v1.0.8: ampliado de 6 a 10 opciones
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
                resp = self.deepseek.generar(peticion, temperature=0.7, max_tokens=2000, modelo_llm=self.llm_var.get())
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
                resp = self.deepseek.generar(peticion, temperature=0.3, max_tokens=2000, modelo_llm=self.llm_var.get())
                resp = limpiar_marcadores(resp)

                def _mostrar():
                    vent = ctk.CTkToplevel(self)
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

        v1.0.8: ampliado de 22 a 36 items en 6 categorías.
        Añadidos botones rápidos: Básicos, Retrato, Calidad máxima, Limpiar.
        """
        if not self._debe_mostrar_negatives():
            return self.set_estado("⚠️ Este modelo no usa NEGATIVE.", "#e67e22")

        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        vent = ctk.CTkToplevel(self)
        vent.title("🧰 Constructor de NEGATIVE")
        vent.geometry("600x680")
        vent.transient(self)

        ctk.CTkLabel(vent, text="🧰 Constructor de NEGATIVE", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text="Marca lo que quieras EVITAR en tu imagen",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 8))

        # Categorías de negative — v1.0.8: 36 items en 6 categorías
        categorias = {
            "🔥 Anatomía / Personas": [
                ("Manos malas", "(bad hands:1.4), (deformed hands:1.3), (extra fingers:1.4), missing fingers, fused fingers"),
                ("Cara mal", "(deformed face:1.3), (asymmetric face:1.2), bad anatomy, ugly face"),
                ("Ojos raros", "(crossed eyes:1.3), (dead eyes:1.2), unaligned eyes, lazy eye"),
                ("Boca / dientes", "(bad teeth:1.3), crooked teeth, deformed mouth, ugly smile"),
                ("Múltiples cabezas", "(multiple heads:1.4), conjoined twins, cloned face"),
                ("Cuerpo deforme", "(bad anatomy:1.4), (mutation:1.3), extra limbs, deformed body"),
                ("Pies malos", "(bad feet:1.3), deformed toes, fused toes, missing legs"),
                ("Proporciones malas", "(bad proportions:1.3), gigantic head, tiny body, long neck"),
            ],
            "📷 Calidad técnica": [
                ("Baja calidad", "(low quality:1.4), (worst quality:1.4), lowres, blurry, jpeg artifacts"),
                ("Pixelado", "(pixelated:1.3), aliasing, compression artifacts"),
                ("Sobreexpuesto", "(overexposed:1.3), washed out colors, blown highlights"),
                ("Subexpuesto", "(underexposed:1.2), too dark, crushed shadows"),
                ("Ruido", "(noisy:1.3), grainy, film grain"),
                ("Desenfoque", "(out of focus:1.3), motion blur, soft focus"),
                ("Color saturado mal", "oversaturated, neon vomit, ugly color cast"),
                ("Tinte amarillo", "(yellow tint:1.2), color cast, white balance off"),
            ],
            "📝 Texto y marcas": [
                ("Texto / letras", "(text:1.4), (watermark:1.4), letters, words, signature"),
                ("Logos / firmas", "logo, brand, copyright, username, artist signature"),
                ("Marca de agua", "(watermark:1.5), stamps, labels"),
                ("Bordes / frame", "(border:1.3), frame, picture frame, vignette"),
                ("Caption / subtítulo", "caption, subtitle, dialog text, speech bubble"),
            ],
            "🎨 Estilo no deseado": [
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
            "✨ Realismo extra": [
                ("Piel plástica", "(plastic skin:1.3), waxy skin, smooth skin, doll-like"),
                ("Sin uncanny", "(uncanny valley:1.3), creepy, soulless"),
                ("Sin filtro IG", "(instagram filter:1.2), heavy makeup, beauty filter"),
                ("Errores luz", "(unnatural lighting:1.2), unrealistic shadows, no shadow"),
            ],
        }

        check_vars = {}
        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=5)

        for categoria, items in categorias.items():
            ctk.CTkLabel(scroll, text=categoria, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=c["hdr_text"]).pack(anchor="w", pady=(8, 2))
            for nombre, tags in items:
                v = ctk.BooleanVar()
                cb = ctk.CTkCheckBox(scroll, text=nombre, variable=v, font=ctk.CTkFont(size=10))
                cb.pack(anchor="w", padx=20, pady=1)
                check_vars[nombre] = (v, tags)

        # Contador inferior
        lbl_count = ctk.CTkLabel(vent, text="0 items seleccionados", font=ctk.CTkFont(size=10),
                                 text_color=c["muted_text"])
        lbl_count.pack(pady=(2, 0))

        def _actualizar_contador():
            n = sum(1 for (v, _) in check_vars.values() if v.get())
            lbl_count.configure(text=f"{n} items seleccionados")
        for (v, _) in check_vars.values():
            v.trace_add("write", lambda *a: _actualizar_contador())

        # Botones rápidos (presets)
        preset_row = ctk.CTkFrame(vent, fg_color="transparent")
        preset_row.pack(pady=(4, 2))

        def _marcar(nombres, exclusivo=False):
            if exclusivo:
                for v, _ in check_vars.values(): v.set(False)
            for nombre in nombres:
                if nombre in check_vars:
                    check_vars[nombre][0].set(True)

        ctk.CTkButton(preset_row, text="✓ Básicos", width=85, height=24, fg_color="#1a4a5a",
                      command=lambda: _marcar(["Manos malas", "Baja calidad", "Texto / letras", "Marca de agua"])
                      ).pack(side="left", padx=3)
        ctk.CTkButton(preset_row, text="👤 Retrato", width=85, height=24, fg_color="#1a4a5a",
                      command=lambda: _marcar(["Manos malas", "Cara mal", "Ojos raros", "Boca / dientes",
                                                "Proporciones malas", "Piel plástica", "Baja calidad",
                                                "Texto / letras", "Marca de agua"])
                      ).pack(side="left", padx=3)
        ctk.CTkButton(preset_row, text="🏆 Calidad máx", width=110, height=24, fg_color="#1a4a5a",
                      command=lambda: _marcar(["Baja calidad", "Pixelado", "Ruido", "Desenfoque",
                                                "Tinte amarillo", "Sobreexpuesto", "Subexpuesto",
                                                "Texto / letras", "Marca de agua", "Logos / firmas"])
                      ).pack(side="left", padx=3)
        ctk.CTkButton(preset_row, text="🧹 Limpiar", width=80, height=24, fg_color="#5a3a1a",
                      command=lambda: [v.set(False) for (v, _) in check_vars.values()]
                      ).pack(side="left", padx=3)

        # Botones aplicar
        btn_row = ctk.CTkFrame(vent, fg_color="transparent")
        btn_row.pack(pady=8)

        def _aplicar():
            tags_seleccionados = []
            for nombre, (v, tags) in check_vars.items():
                if v.get():
                    tags_seleccionados.append(tags)
            if not tags_seleccionados:
                self.set_estado("⚠️ Marca al menos un elemento.", "#e67e22")
                return
            negative_completo = ", ".join(tags_seleccionados)
            # Aplicar al prompt actual
            pos = self.extraer_positive()
            if pos:
                nuevo = f"POSITIVE PROMPT: {pos}\nNEGATIVE PROMPT: {negative_completo}"
                self.actualizar_salida(nuevo)
                self.set_estado(f"🧰 NEGATIVE construido con {len(tags_seleccionados)} items", "#2ecc71")
            else:
                pyperclip.copy(negative_completo)
                self.set_estado(f"🧰 NEGATIVE copiado al portapapeles ({len(tags_seleccionados)} items)", "#2ecc71")
            vent.destroy()

        def _solo_copiar():
            tags_seleccionados = [tags for nombre, (v, tags) in check_vars.items() if v.get()]
            if not tags_seleccionados:
                self.set_estado("⚠️ Marca al menos un elemento.", "#e67e22")
                return
            pyperclip.copy(", ".join(tags_seleccionados))
            self.set_estado(f"📋 NEGATIVE copiado ({len(tags_seleccionados)} items)", "#2ecc71")
            vent.destroy()

        ctk.CTkButton(btn_row, text="✅ Aplicar al prompt", width=170, height=30, fg_color="#1a7a3c",
                      command=_aplicar).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="📋 Solo copiar", width=130, height=30, fg_color="#475569",
                      command=_solo_copiar).pack(side="left", padx=4)

    def _cmd_moodboard(self):
        """Genera 6 prompts complementarios con mismo mood pero distintos sujetos."""
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.set_estado("⚠️ Escribe un concepto base.", "#e67e22")
        try: self._sesion_log("🎨 Mood: generó 6 prompts (mismo mood, distintos sujetos)")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.set_estado("🎨 Generando moodboard de 6 prompts...", "#f39c12")
        self.toggle_botones(False)

        peticion = (
            f"Genera UN MOODBOARD: 6 prompts que comparten el MISMO MOOD/atmósfera pero con SUJETOS distintos.\n\n"
            f"CONCEPTO/MOOD BASE: {idea}\n"
            f"ESTILOS: {self.estilos_texto()}\n\n"
            f"REGLAS:\n"
            f"- Mantén la MISMA paleta, iluminación, atmósfera y estilo en todos.\n"
            f"- Cambia el SUJETO en cada uno (1: persona, 2: paisaje, 3: objeto, 4: animal, 5: arquitectura, 6: detalle macro).\n"
            f"- Todos juntos deben formar una serie visualmente coherente.\n\n"
            f"FORMATO:\n"
            f"PROMPT 1: [persona] — POSITIVE: ... NEGATIVE: ...\n---\n"
            f"PROMPT 2: [paisaje] — POSITIVE: ... NEGATIVE: ...\n---\n"
            f"PROMPT 3: [objeto] — POSITIVE: ... NEGATIVE: ...\n---\n"
            f"PROMPT 4: [animal] — POSITIVE: ... NEGATIVE: ...\n---\n"
            f"PROMPT 5: [arquitectura] — POSITIVE: ... NEGATIVE: ...\n---\n"
            f"PROMPT 6: [macro/detalle] — POSITIVE: ... NEGATIVE: ..."
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.8, max_tokens=4000, modelo_llm=self.llm_var.get())
                resp = limpiar_marcadores(resp)
                bloques = self._parsear_bloques_numerados(resp)
                if len(bloques) < 2:
                    self.after(0, lambda: self.set_estado("⚠️ Solo se generó 1 bloque, intenta de nuevo", "#e67e22"))
                    self.after(0, lambda: self.toggle_botones(True))
                    return

                def _mostrar():
                    self._abrir_comparador(bloques[:6])
                    self.set_estado(f"🎨 Moodboard listo ({len(bloques)} prompts)", "#2ecc71")
                    self.toggle_botones(True)
                    self._sonar_completado()
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_story_sequence(self):
        """Genera 3 shots cinematográficos: Wide → Medium → Close-Up. Solo modo imagen."""
        if self.modo_var.get() != "imagen":
            return self.set_estado("⚠️ Story Sequence solo está disponible en modo IMAGEN.", "#e67e22")
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.set_estado("⚠️ Escribe la escena base.", "#e67e22")
        try: self._sesion_log("🎬 Story: generó 3 shots Wide/Medium/Close-Up")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.set_estado("🎬 Generando secuencia cinematográfica (Wide/Medium/Close)...", "#f39c12")
        self.toggle_botones(False)

        peticion = (
            f"Genera 3 SHOTS CINEMATOGRÁFICOS de la misma escena, manteniendo coherencia entre ellos.\n\n"
            f"ESCENA: {idea}\n"
            f"ESTILOS: {self.estilos_texto()}\n\n"
            f"REGLAS:\n"
            f"- MISMO sujeto, MISMA iluminación, MISMA paleta, MISMA atmósfera.\n"
            f"- Solo cambia el ENCUADRE/PLANO.\n\n"
            f"FORMATO:\n"
            f"SHOT 1 (WIDE / Plano amplio): POSITIVE: ... NEGATIVE: ... — Establece el lugar, sujeto pequeño en el frame, contexto amplio\n---\n"
            f"SHOT 2 (MEDIUM / Plano medio): POSITIVE: ... NEGATIVE: ... — Sujeto de cintura para arriba, equilibrio sujeto-fondo\n---\n"
            f"SHOT 3 (CLOSE-UP / Primer plano): POSITIVE: ... NEGATIVE: ... — Cara o detalle clave, máxima intimidad y emoción"
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.6, max_tokens=3000, modelo_llm=self.llm_var.get())
                resp = limpiar_marcadores(resp)
                bloques = self._parsear_bloques_numerados(resp)

                def _mostrar():
                    self._abrir_comparador(bloques[:3])
                    self.set_estado("🎬 Secuencia Wide/Medium/Close lista", "#2ecc71")
                    self.toggle_botones(True)
                    self._sonar_completado()
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_storyboard_video(self):
        """Para vídeo: 4 shots clave de la secuencia (apertura/mid/climax/cierre). Solo modo vídeo."""
        if self.modo_var.get() != "video":
            return self.set_estado("⚠️ Storyboard solo está disponible en modo VÍDEO.", "#e67e22")
        idea = self.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.set_estado("⚠️ Escribe la escena/historia base.", "#e67e22")
        try: self._sesion_log("📽 Board: generó storyboard 4 shots (apertura/mid/climax/cierre)")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.set_estado("📽 Generando storyboard de 4 shots...", "#f39c12")
        self.toggle_botones(False)

        peticion = (
            f"Genera un STORYBOARD DE 4 SHOTS para una secuencia de vídeo.\n\n"
            f"HISTORIA/ESCENA: {idea}\n"
            f"ESTILOS: {self.estilos_texto()}\n\n"
            f"REGLAS:\n"
            f"- Cuenta una microhistoria visual: apertura → desarrollo → climax → cierre.\n"
            f"- MISMA paleta, iluminación coherente entre frames.\n"
            f"- Cada shot es un prompt de IMAGEN (para usar como key frame del vídeo).\n\n"
            f"FORMATO:\n"
            f"FRAME 1 (Apertura/Establishing): POSITIVE: ... NEGATIVE: ...\n---\n"
            f"FRAME 2 (Desarrollo): POSITIVE: ... NEGATIVE: ...\n---\n"
            f"FRAME 3 (Climax/Punto álgido): POSITIVE: ... NEGATIVE: ...\n---\n"
            f"FRAME 4 (Cierre/Resolución): POSITIVE: ... NEGATIVE: ..."
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.7, max_tokens=3500, modelo_llm=self.llm_var.get())
                resp = limpiar_marcadores(resp)
                bloques = self._parsear_bloques_numerados(resp)

                def _mostrar():
                    self._abrir_comparador(bloques[:4])
                    self.set_estado("📽 Storyboard 4 frames listo", "#2ecc71")
                    self.toggle_botones(True)
                    self._sonar_completado()
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_random_walk(self):
        """Toma el prompt actual y lo deriva 5 veces (cada output base del siguiente)."""
        actual = self.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.set_estado("⚠️ Genera un prompt primero como base.", "#e67e22")
        try: self._sesion_log("🌀 Walk: random walk de 5 derivaciones evolutivas")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.set_estado("🌀 Random walk: derivando 5 veces...", "#f39c12")
        self.toggle_botones(False)
        evoluciones = [actual]

        def _worker():
            try:
                base = actual
                for i in range(5):
                    self.after(0, lambda i=i: self.set_estado(f"🌀 Generando derivación {i+1}/5...", "#f39c12"))
                    peticion = (
                        f"Toma este prompt y EVOLUCIONA hacia algo SIMILAR pero ligeramente distinto.\n"
                        f"Cambia 1-2 elementos (objeto, color, atmósfera, ángulo) pero mantén el espíritu.\n"
                        f"Cada paso debe alejarse un poco del anterior.\n\n"
                        f"PROMPT BASE:\n{base}\n\n"
                        f"Responde SOLO con el nuevo prompt, sin explicaciones.\n"
                        f"FORMATO: POSITIVE PROMPT: ... NEGATIVE PROMPT: ..."
                    )
                    resp = self.deepseek.generar(peticion, temperature=0.85, max_tokens=1800, modelo_llm=self.llm_var.get())
                    resp = limpiar_marcadores(resp)
                    evoluciones.append(resp)
                    base = resp

                def _mostrar():
                    self._abrir_comparador(evoluciones)
                    self.set_estado(f"🌀 Random walk: 6 evoluciones (original + 5 derivaciones)", "#2ecc71")
                    self.toggle_botones(True)
                    self._sonar_completado()
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_color_palette(self):
        """Extrae paleta de 5 colores hex de la imagen cargada."""
        if not self.imagen_cargada:
            return self.set_estado("⚠️ Carga una imagen de referencia primero.", "#e67e22")

        self.set_estado("🎨 Extrayendo paleta de colores...", "#f39c12")

        def _worker():
            try:
                from PIL import Image
                from collections import Counter

                img = self.imagen_cargada.copy()
                img.thumbnail((200, 200))
                img = img.convert("RGB")

                # Quantizar a 5 colores principales
                quantized = img.quantize(colors=5)
                palette = quantized.getpalette()[:15]
                colores_hex = []
                for i in range(0, 15, 3):
                    r, g, b = palette[i], palette[i+1], palette[i+2]
                    colores_hex.append(f"#{r:02X}{g:02X}{b:02X}")

                # Generar tags descriptivos
                tags_color = ", ".join([f"color {c}" for c in colores_hex])

                def _mostrar():
                    vent = ctk.CTkToplevel(self)
                    vent.title("🎨 Paleta de colores extraída")
                    vent.geometry("500x400")
                    vent.transient(self)
                    ctk.CTkLabel(vent, text="🎨 Paleta extraída de la imagen", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 8))

                    # Mostrar swatches
                    sw_frame = ctk.CTkFrame(vent, fg_color="transparent")
                    sw_frame.pack(pady=10)
                    for hex_c in colores_hex:
                        col = ctk.CTkFrame(sw_frame, fg_color=hex_c, width=60, height=60, corner_radius=8)
                        col.pack(side="left", padx=5)
                        ctk.CTkLabel(sw_frame, text=hex_c, font=ctk.CTkFont(size=9)).pack_forget()

                    # Hex codes
                    txt = ctk.CTkTextbox(vent, font=ctk.CTkFont(family="Consolas", size=11), height=80)
                    txt.pack(fill="x", padx=15, pady=10)
                    txt.insert("1.0", ", ".join(colores_hex))

                    btn_row = ctk.CTkFrame(vent, fg_color="transparent")
                    btn_row.pack(pady=10)
                    ctk.CTkButton(btn_row, text="📋 Copiar HEX", width=120, height=28,
                                  command=lambda: pyperclip.copy(", ".join(colores_hex))).pack(side="left", padx=4)
                    ctk.CTkButton(btn_row, text="✅ Añadir al prompt", width=160, height=28, fg_color="#1a7a3c",
                                  command=lambda: (self._aplicar_atajo_tags(f"color palette: {', '.join(colores_hex)}"),
                                                    vent.destroy())).pack(side="left", padx=4)

                    self.set_estado("🎨 Paleta extraída", "#2ecc71")
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_modo_cliente(self):
        """Modo Cliente: brief simplificado para generar 5 propuestas profesionales."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        vent = ctk.CTkToplevel(self)
        vent.title("💼 Modo Cliente")
        vent.geometry("600x600")
        vent.transient(self)

        ctk.CTkLabel(vent, text="💼 Modo Cliente — Brief profesional",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text="Define un brief y genera 5 propuestas profesionales coherentes",
                     font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(pady=(0, 12))

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
            ent = ctk.CTkEntry(vent, placeholder_text=placeholder, width=540, height=28)
            ent.pack(padx=20)
            campos[label] = ent

        def _generar_propuestas():
            brief = "\n".join([f"- {k}: {v.get().strip() or '(no especificado)'}" for k, v in campos.items()])
            if all(v.get().strip() == "" for v in campos.values()):
                self.set_estado("⚠️ Rellena al menos un campo del brief.", "#e67e22")
                return

            # Si hay imagen analizada, añadirla al brief
            if cliente_state["descripcion"]:
                brief += f"\n\n📎 IMAGEN DE REFERENCIA proporcionada por el cliente:\n{cliente_state['descripcion']}\n(Usa el estilo visual de esta imagen como guía estética)"

            vent.destroy()
            self._generar_propuestas_cliente(brief)

        ctk.CTkButton(vent, text="✨ Generar 5 propuestas", width=200, height=32, fg_color="#1a7a3c",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=_generar_propuestas).pack(pady=15)

    def _generar_propuestas_cliente(self, brief):
        """Genera 5 propuestas basadas en un brief."""
        self.set_estado("💼 Generando 5 propuestas profesionales...", "#f39c12")
        self.toggle_botones(False)

        # Saber si el modelo soporta negative
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
                resp = self.deepseek.generar(peticion, temperature=0.7, max_tokens=4000, modelo_llm=self.llm_var.get())
                resp = limpiar_marcadores(resp)

                # Parsear con parser robusto
                bloques = self._parsear_bloques_numerados(resp)

                # Limpiar cada bloque: quitar líneas tipo "Enfoque: ..." antes del POSITIVE
                bloques_limpios = []
                import re
                for b in bloques:
                    # Buscar desde POSITIVE PROMPT hacia adelante
                    m = re.search(r'(POSITIVE\s+PROMPT\s*:.*?)(?=\Z|===)', b, re.DOTALL | re.IGNORECASE)
                    if m:
                        bloques_limpios.append(m.group(1).strip())
                    else:
                        bloques_limpios.append(b)

                if not bloques_limpios:
                    bloques_limpios = bloques

                def _mostrar():
                    self._abrir_comparador(bloques_limpios[:5])
                    self.set_estado(f"💼 {len(bloques_limpios)} propuestas profesionales generadas", "#2ecc71")
                    self.toggle_botones(True)
                    self._sonar_completado()
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_companero_moodboard(self):
        """Sube 3 imágenes y la IA detecta el estilo común."""
        from tkinter import filedialog
        archivos = filedialog.askopenfilenames(
            title="Selecciona 2-5 imágenes con estilo similar",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp")]
        )
        if not archivos or len(archivos) < 2:
            return self.set_estado("⚠️ Selecciona al menos 2 imágenes.", "#e67e22")

        self.set_estado(f"🎭 Analizando {len(archivos)} imágenes para extraer estilo común...", "#f39c12")
        self.toggle_botones(False)

        def _worker():
            try:
                from PIL import Image
                descripciones = []
                for i, ruta in enumerate(archivos[:5]):
                    img = Image.open(ruta)
                    self.after(0, lambda i=i: self.set_estado(f"🎭 Analizando imagen {i+1}/{min(len(archivos), 5)}...", "#f39c12"))
                    desc, _ = self.vision.describir(img, "imagen", lambda m: None)
                    descripciones.append(desc)

                # Extraer estilo común
                peticion = (
                    f"Has analizado {len(descripciones)} imágenes. Extrae el ESTILO COMÚN entre ellas.\n\n"
                    + "\n---\n".join([f"IMAGEN {i+1}:\n{d}" for i, d in enumerate(descripciones)])
                    + "\n\nRESPONDE EN ESPAÑOL con este formato:\n\n"
                    + "🎨 ESTILO DETECTADO: [nombre del estilo común]\n\n"
                    + "📐 ELEMENTOS COMUNES:\n   - [3-5 elementos compartidos]\n\n"
                    + "🎨 PALETA: [colores predominantes]\n\n"
                    + "💡 ILUMINACIÓN: [tipo de luz común]\n\n"
                    + "🎬 PROMPT TEMPLATE EN INGLÉS (para generar imágenes en este mismo estilo):\n[prompt completo en formato POSITIVE PROMPT: ...]"
                )
                resp = self.deepseek.generar(peticion, temperature=0.4, max_tokens=2000, modelo_llm=self.llm_var.get())
                resp = limpiar_marcadores(resp)

                def _mostrar():
                    vent = ctk.CTkToplevel(self)
                    vent.title("🎭 Estilo común detectado")
                    vent.geometry("700x600")
                    vent.transient(self)
                    ctk.CTkLabel(vent, text=f"🎭 Análisis de {len(descripciones)} imágenes",
                                 font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 8))

                    txt = ctk.CTkTextbox(vent, font=ctk.CTkFont(size=11), wrap="word")
                    txt.pack(fill="both", expand=True, padx=15, pady=(0, 5))
                    txt.insert("1.0", resp)
                    txt.configure(state="disabled")

                    btn_row = ctk.CTkFrame(vent, fg_color="transparent")
                    btn_row.pack(pady=10)

                    def _aplicar_template():
                        # Extraer el PROMPT TEMPLATE
                        import re
                        m = re.search(r'PROMPT\s+TEMPLATE[^:]*:\s*(.+?)(?=\Z)', resp, re.DOTALL | re.IGNORECASE)
                        if m:
                            template = m.group(1).strip()
                            self.actualizar_salida(template)
                            vent.destroy()
                            self.set_estado("🎭 Template aplicado al resultado", "#2ecc71")

                    ctk.CTkButton(btn_row, text="✅ Usar template", width=140, height=28, fg_color="#1a7a3c",
                                  command=_aplicar_template).pack(side="left", padx=4)
                    ctk.CTkButton(btn_row, text="📋 Copiar análisis", width=140, height=28,
                                  command=lambda: pyperclip.copy(resp)).pack(side="left", padx=4)

                    self.toggle_botones(True)
                    self.set_estado("🎭 Estilo común detectado", "#2ecc71")
                self.after(0, _mostrar)
            except Exception as e:
                self.after(0, lambda: self.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()
