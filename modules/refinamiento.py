"""Refinamiento de prompts: menú rápido, iteración por elemento y diff visual.

Extraído de modules/core.py para reducir tamaño y agrupar responsabilidades.

Contiene:
  • _menu_refinar_especifico  — menú popup con 7 refinamientos comunes.
  • _refinar_con_instruccion  — aplica una instrucción concreta + abre diff.
  • _cmd_iteracion            — genera N variantes cambiando 1 solo elemento.
  • _iterar_elemento          — worker IA para iteración con parser de VARIANTE N.
  • cmd_refinar               — refinamiento general (mejora el prompt actual).
  • _mostrar_diff_refinamiento — modal de diff con Aplicar/Cancelar/Deshacer.
"""
import datetime
import logging
import re
import threading
import tkinter as tk

import customtkinter as ctk

from modules.gprompt_window import GPromptWindow
from workers import limpiar_marcadores

logger = logging.getLogger("gprompt")


class RefinamientoService:
    """Refinamiento + iteración + diff visual.

    A1 fase 2 (sesión 14): servicio aislado con app por composición.
    """

    def __init__(self, app):
        self.app = app

    def _menu_refinar_especifico(self, event=None) -> None:
        """Menú con 5 opciones de refinamiento específico."""
        texto = self.app.txt_salida.get("1.0", "end").strip()
        if not texto or len(texto) < 20:
            return self.app.dialogs.set_estado("⚠️ Genera un prompt primero.", "#e67e22")

        is_lt = ctk.get_appearance_mode().lower() == "light"
        menu = tk.Menu(self, tearoff=0,
                       bg="#f0f0f0" if is_lt else "#1a1a2a",
                       fg="#111827" if is_lt else "white",
                       activebackground="#dbeafe" if is_lt else "#2a4a6a",
                       activeforeground="#111827" if is_lt else "white",
                       font=("Segoe UI", 10), borderwidth=1)

        opciones = [
            ("🎬 Más cinematográfico",   "más cinematográfico, con encuadre épico, movimientos de cámara dramáticos, iluminación de película"),
            ("👤 Más detalle facial",    "más detalle facial, ojos detallados, textura de piel realista, expresión emotiva, pelo individual"),
            ("💡 Mejor iluminación",     "iluminación más profesional, luces volumétricas, ambiente atmosférico, dirección de luz definida, sombras dramáticas"),
            ("⚡ Más impacto visual",    "más impacto visual, composición más fuerte, elementos contrastantes, paleta de colores definida, foco visual claro"),
            ("✂️ Simplificar",           "más simple y conciso. Elimina redundancias, tags innecesarios. Mantén solo lo esencial."),
            ("🌈 Cambiar paleta",        "con una paleta de colores diferente y más interesante. Sugiere una combinación cromática específica"),
            ("🔍 Más detalle técnico",   "con detalles técnicos: sampler, lente, distancia focal, tipo de cámara, resolución específica"),
        ]
        for label, instruccion in opciones:
            menu.add_command(label=label, command=lambda i=instruccion: self._refinar_con_instruccion(i))

        try:
            x = event.x_root if event else self.app.winfo_pointerx()
            y = event.y_root if event else self.app.winfo_pointery()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _refinar_con_instruccion(self, instruccion_extra: str) -> None:
        """Refina el prompt con una instrucción específica."""
        texto = self.app.txt_salida.get("1.0", "end").strip()
        if not texto: return

        self.app.dialogs.set_estado(f"🔁 Refinando: {instruccion_extra[:40]}...", "#f39c12")
        self.app.dialogs.toggle_botones(False)

        es_tag_based = not self.app.is_natural_mode()
        formato = "Mantén formato tags con pesos (tag:1.2)." if es_tag_based else "Mantén formato lenguaje natural descriptivo."

        peticion = (
            f"Refina este prompt aplicando esta instrucción específica: {instruccion_extra}\n\n"
            f"PROMPT ORIGINAL:\n{texto}\n\n"
            f"REGLAS:\n"
            f"- {formato}\n"
            f"- NO cambies el sujeto principal ni la idea central.\n"
            f"- Aplica la instrucción de forma específica y notable.\n"
            f"- Responde SOLO con el prompt refinado, sin explicaciones.\n"
        )

        texto_previo = texto

        def _worker():
            try:
                resp = self.app.deepseek.generar(peticion, temperature=0.5, max_tokens=2000)
                resp = limpiar_marcadores(resp)
                def _aplicar():
                    self.app.guardar_en_historial(resp)
                    self.app.dialogs.set_estado(f"🔍 Refinamiento listo ({instruccion_extra[:30]}...) — revisa el diff.", "#2ecc71")
                    self.app.dialogs.toggle_botones(True)
                    self.app.dialogs._sonar_completado()
                    self._mostrar_diff_refinamiento(texto_previo, resp)
                self.app.after(0, _aplicar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _cmd_iteracion(self) -> None:
        """Genera N variantes del prompt cambiando solo 1 elemento (iluminación, encuadre, etc).

        v2: el usuario elige primero N (slider 3-10) y luego el elemento.
        """
        texto = self.app.txt_salida.get("1.0", "end").strip()
        if not texto or len(texto) < 20:
            return self.app.dialogs.set_estado("⚠️ Genera un prompt primero para iterar.", "#e67e22")

        n = self.app._pedir_n_modal(
            "🔂 Iterar — número de variantes",
            "¿Cuántas variantes quieres? Todas cambiarán SOLO el "
            "elemento que elijas en el siguiente paso.",
            n_min=3, n_max=10, default=5,
            key_pref="iteracion_n",
        )
        if n is None:
            return

        try: self.app._sesion_log(f"🔂 Iterar: abrió ventana de variación 1 elemento (n={n})")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        sel = GPromptWindow(self.app)
        sel.title("🔂 Iteración")
        sel.geometry("400x320")
        sel.transient(self.app)

        is_lt = ctk.get_appearance_mode().lower() == "light"
        ctk.CTkLabel(sel, text="🔂 Modo Iteración",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 3))
        ctk.CTkLabel(sel,
                     text=f"Genera {n} variantes cambiando SOLO un elemento:",
                     font=ctk.CTkFont(size=11),
                     text_color="#6b7280" if is_lt else "#888888"
                     ).pack(pady=(0, 12))

        opciones = [
            ("💡 Iluminación", "iluminación (tipo, dirección, color)"),
            ("📐 Encuadre", "encuadre y plano de cámara"),
            ("🎨 Paleta de colores", "paleta de colores"),
            ("🌫 Atmósfera/mood", "atmósfera y mood"),
            ("🎬 Estilo/género", "estilo artístico / género"),
        ]
        for label, descripcion in opciones:
            btn = ctk.CTkButton(sel, text=label, width=300, height=32,
                                fg_color="#2563eb" if is_lt else "#1a3a5a",
                                hover_color="#1d4ed8" if is_lt else "#2a4a6a",
                                font=ctk.CTkFont(size=11),
                                command=lambda d=descripcion, n_=n: (
                                    sel.destroy(),
                                    self._iterar_elemento(d, n_)))
            btn.pack(pady=3)

    def _iterar_elemento(self, elemento: str, n: int = 5) -> None:
        """Genera N variantes cambiando un elemento específico."""
        texto = self.app.txt_salida.get("1.0", "end").strip()
        self.app.dialogs.set_estado(f"🔂 Generando {n} variantes ({elemento})...", "#f39c12")
        self.app.dialogs.toggle_botones(False)

        # ¿El prompt original tiene NEGATIVE PROMPT? Le pedimos al LLM
        # que respete ese formato (POSITIVE/NEGATIVE) en cada variante.
        tiene_neg = bool(self.app._extraer_neg_de_bloque(texto))
        bloque_ejemplo = (
            "POSITIVE PROMPT: [tags del positivo con el cambio aplicado]\n"
            "NEGATIVE PROMPT: [tags del negativo, idénticos al original]"
            if tiene_neg
            else "POSITIVE PROMPT: [tags del positivo con el cambio aplicado]"
        )
        variantes_lineas = "\n---\n".join(
            f"VARIANTE {i + 1}:\n{bloque_ejemplo}" for i in range(n)
        )
        regla_neg = (
            "- MANTÉN el NEGATIVE PROMPT del original IDÉNTICO en cada variante.\n"
            if tiene_neg else ""
        )
        peticion = (
            f"Genera {n} VARIANTES de este prompt, cambiando ÚNICAMENTE el elemento: {elemento}.\n"
            f"Todo lo demás (sujeto, composición, formato) debe permanecer IDÉNTICO.\n"
            f"{regla_neg}"
            f"- USA exactamente las etiquetas 'POSITIVE PROMPT:' (y 'NEGATIVE PROMPT:' si aplica) en cada variante.\n\n"
            f"PROMPT ORIGINAL:\n{texto}\n\n"
            f"FORMATO DE RESPUESTA (sigue EXACTAMENTE esta estructura, una variante tras otra):\n{variantes_lineas}"
        )
        max_tok = min(8000, 1500 + n * 700)

        def _worker():
            try:
                resp = self.app.deepseek.generar(peticion, temperature=0.7, max_tokens=max_tok)
                resp = limpiar_marcadores(resp)

                variantes = re.split(r'VARIANTE\s*\d+\s*:?\s*', resp, flags=re.IGNORECASE)
                variantes = [v.strip().strip("-").strip() for v in variantes
                              if v.strip() and len(v.strip()) > 30]

                if len(variantes) < 2:
                    self.app.after(0, lambda: self.app.dialogs.set_estado("⚠️ Solo se generó 1 variante, intenta de nuevo", "#e67e22"))
                    self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))
                    return

                def _mostrar():
                    self.app._abrir_comparador(variantes[:n])
                    self.app.dialogs.set_estado(f"🔂 {len(variantes)} variantes de '{elemento}' listas", "#2ecc71")
                    self.app.dialogs.toggle_botones(True)
                    self.app.dialogs._sonar_completado()
                self.app.after(0, _mostrar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(f"❌ Error: {e}", "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def cmd_refinar(self) -> None:
        texto = self.app.txt_salida.get("1.0", "end").strip()
        if not texto or not (("PROMPT:" in limpiar_marcadores(texto)) or ("ESTILO:" in limpiar_marcadores(texto))):
            return self.app.dialogs.set_estado("⚠️ Genera un prompt primero para refinarlo.", "#e67e22")

        self.app._ocultar_ideas()
        idea, pers, lora, modo = self.app.txt_idea.get("1.0", "end").strip(), self.app.footer.personaje_activo(), self.app.footer.lora_activo(), self.app.modo_var.get()
        try: self.app._sesion_log("🔁 Refinó prompt")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        es_tag_based = not self.app.is_natural_mode()

        peticion = f"Refina y mejora ESTE prompt:\n\n{texto}\n\n"
        if modo == "imagen":
            if es_tag_based:
                peticion += (
                    "REGLAS CRÍTICAS DE REFINAMIENTO:\n"
                    "1. FORMATO: Tags separados por comas, CON pesos (tag:1.2). PROHIBIDO escribir prosa fluida o párrafos.\n"
                    "2. DENSIDAD: Un tag bueno = 2-5 palabras máximo. '(cinematic god rays:1.3)' SÍ. 'The lighting is a masterpiece of soft diffusion emanating from a heavy overcast sky' NO.\n"
                    "3. MEJORA: Añade tags de composición, iluminación, texturas, materiales, atmósfera que falten.\n"
                    "4. COMPACTA: Si el prompt ya es largo, ELIMINA redundancias antes de añadir. Mejor 60 tags densos que 20 frases largas.\n"
                    "5. PESOS: Usa 5-10 pesos estratégicos en POSITIVE y 3-6 en NEGATIVE.\n"
                    "EJEMPLO DE TAG BUENO: 'extreme macro shot, (translucent crystalline egg:1.4), cross-section view, (bioluminescent mushrooms:1.3), (subsurface scattering:1.3), 8K, sharp focus, HDR'\n"
                    "EJEMPLO DE TAG MALO: 'A hyper-detailed photograph showing an egg that appears to be made of crystal with light passing through it in a beautiful way'"
                )
            else:
                peticion += "Es UNA imagen fija en formato NATURAL (prosa descriptiva). Expande composición, luz, texturas, atmósfera. Mantén la prosa concisa."
        elif modo == "video": peticion += "Es un vídeo. Usa lenguaje cinematográfico, iluminación, textura y movimiento de cámara."
        else: peticion += "Es audio. Especifica género, instrumentación, tempo, voces y mood."

        if idea: peticion += f"\nIncorpora: {idea}"
        if pers: peticion += f"\nManteniendo personaje: {pers}"
        if lora: peticion += f"\nManteniendo LoRA: {lora}"
        if self.app._ultimo_anclaje_visual: peticion += f"\nMANTÉN ESTRICTAMENTE LA GEOMETRÍA VISUAL: {self.app._ultimo_anclaje_visual}"

        specs = self.app.get_current_model_specs()
        limite_chars = specs.get("max_chars") or specs.get("max_chars_letra") or 2000 if specs else 2000
        peticion += f"\n\n⛔ REGLA ESTRICTA DE LONGITUD: El POSITIVE PROMPT final no debe superar los {limite_chars} caracteres. Si el prompt original ya está cerca del límite, COMPACTA en vez de expandir: usa tags más densos, elimina redundancias, prioriza calidad sobre cantidad."

        self.app.dialogs.set_estado("🔁 Refinando con meticulosidad máxima...", "#f39c12")
        self.app.dialogs.toggle_botones(False)
        threading.Thread(
            target=self.app.workers.worker_ia,
            args=(peticion,),
            kwargs={"es_refinamiento": True, "texto_previo": texto},
            daemon=True,
        ).start()

    def _mostrar_diff_refinamiento(self, texto_previo: str, texto_nuevo: str) -> None:
        """Modal de diff visual antes de aplicar el refinamiento.

        Muestra el prompt original vs refinado lado a lado con colores
        verde (añadido) / rojo (quitado). Botones:
          • ✅ Aplicar refinamiento → guarda el original como versión
            "(pre-refinamiento)" en `_versiones_prompt` y aplica el nuevo.
          • ↩️ Deshacer refinamiento previo → si existe una versión
            "(pre-refinamiento)" en el stack, la restaura (rollback de un
            refinamiento anterior ya aplicado).
          • ❌ Cancelar (mantener original) → cierra sin tocar nada.
        """
        if not texto_previo or not texto_nuevo:
            self.app.dialogs.actualizar_salida(texto_nuevo or "")
            return

        if texto_previo.strip() == texto_nuevo.strip():
            self.app.dialogs.actualizar_salida(texto_nuevo)
            self.app.dialogs.set_estado("ℹ️ El refinamiento no produjo cambios.", "#3498db")
            return

        def _on_apply():
            try:
                if not hasattr(self.app, '_versiones_prompt'):
                    self.app._versiones_prompt = []
                if not (self.app._versiones_prompt
                        and self.app._versiones_prompt[-1].get("texto") == texto_previo):
                    self.app._versiones_prompt.append({
                        "texto": texto_previo,
                        "fecha": datetime.datetime.now().strftime("%H:%M:%S"),
                        "etiqueta": f"v{len(self.app._versiones_prompt) + 1} (pre-refinamiento)",
                    })
                    if len(self.app._versiones_prompt) > 30:
                        self.app._versiones_prompt = self.app._versiones_prompt[-30:]
            except Exception as e:
                logger.debug(f"[silent] versionado pre-refinamiento: {e}")
            self.app.dialogs.actualizar_salida(texto_nuevo)
            self.app.dialogs.set_estado("✅ Refinamiento aplicado · usa 📑 Versiones para deshacer.", "#2ecc71")
            try: self.app._sesion_log("🔁 Aplicó refinamiento (diff)")
            except Exception as e:
                logger.debug(f"[silent] {e}")

        def _on_cancel():
            self.app.dialogs.set_estado("❌ Refinamiento descartado — prompt original intacto.", "#e67e22")
            try: self.app._sesion_log("🔁 Canceló refinamiento (diff)")
            except Exception as e:
                logger.debug(f"[silent] {e}")

        on_undo = None
        if hasattr(self.app, '_versiones_prompt') and self.app._versiones_prompt:
            for ver in reversed(self.app._versiones_prompt):
                if "pre-refinamiento" in (ver.get("etiqueta", "") or ""):
                    texto_undo = ver["texto"]
                    def _on_undo(_t=texto_undo, _v=ver):
                        try: self.app._versiones_prompt.remove(_v)
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
                        self.app.dialogs.actualizar_salida(_t)
                        self.app.dialogs.set_estado("↩️ Refinamiento previo deshecho — restaurada versión anterior.", "#f39c12")
                        try: self.app._sesion_log("↩️ Deshizo refinamiento previo")
                        except Exception as e:
                            logger.debug(f"[silent] {e}")
                    on_undo = _on_undo
                    break

        self.app._abrir_ventana_diff(
            texto_previo, texto_nuevo,
            label_a="🔹 Original",
            label_b="🔸 Refinado",
            on_apply=_on_apply,
            on_cancel=_on_cancel,
            on_undo=on_undo,
            titulo="🔁 Refinamiento — revisa los cambios antes de aplicar",
            hint="🟢 Verde = añadido por el refinamiento    🔴 Rojo = eliminado del original    ⚪ Sin color = igual",
        )
