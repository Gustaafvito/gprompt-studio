"""Multi-prompt narrativo — Moodboard / Story / Board / Walk.

Cuatro comandos para generar variaciones narrativas a partir de una idea:

  • _cmd_moodboard          — N prompts mismo mood, distintos sujetos.
  • _cmd_story_sequence     — N shots cinematográficos (tipos configurables
                              por checkboxes).
  • _cmd_storyboard_video   — N frames clave para vídeo, con botón
                              "🎬 Encadenar como prompt de vídeo"
                              (_encadenar_board_a_video).
  • _cmd_random_walk        — árbol interactivo de derivaciones
                              (_abrir_walk_arbol con canvas + panel detalle).

Helpers internos:
  • _pedir_story_config / _story_label_de_key — modal de config Story.
  • _encadenar_board_a_video                 — Board → Vídeo.
  • _abrir_walk_arbol                        — UI del árbol.

Constante de clase:
  • STORY_SHOT_TYPES — 8 tipos canónicos de shot.

Dependencias self (provistas por ArquitectoApp y demás mixins):
  txt_idea, txt_salida, modo_var, deepseek, estilos_texto, store,
  after, set_estado, toggle_botones, actualizar_salida,
  guardar_en_historial, _sesion_log, _sonar_completado,
  _on_modo_cambio, _pedir_n_modal, _parsear_bloques_numerados,
  _abrir_comparador, _versiones_prompt.
"""
import datetime
import logging
import tkinter as tk

import customtkinter as ctk
import pyperclip

from config import get_image_model_specs, get_theme_colors
from modules.gprompt_window import GPromptWindow
from modules.i18n import tr
from workers import limpiar_marcadores, log_future_exc

logger = logging.getLogger(__name__)


class MultiPromptService:
    """Moodboard / Story / Board / Walk — generadores multi-prompt.

    A1 fase 2 (sesión 14): servicio aislado con app por composición.
    Acceso: `app.multi.cmd_moodboard()`, `cmd_story_sequence()`,
    `cmd_storyboard_video()`, `cmd_storyboard_imagen()`, `cmd_random_walk()`.
    """

    def __init__(self, app):
        self.app = app

    def _cmd_moodboard(self):
        """Genera N prompts complementarios con mismo mood pero distintos sujetos.

        v2: N configurable (4-10, default 6). Antes hardcoded a 6 sujetos
        fijos (persona/paisaje/objeto/animal/arquitectura/macro). Ahora el
        LLM elige los N sujetos diversos.
        """
        idea = self.app.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.app.dialogs.set_estado(tr("⚠️ Escribe un concepto base."), "#e67e22")

        n = self.app._pedir_n_modal(
            "🎭 Mood — número de prompts",
            "¿Cuántos prompts en el moodboard?\n"
            "Comparten mood/atmósfera pero con sujetos distintos.",
            n_min=4, n_max=10, default=6,
            key_pref="moodboard_n",
        )
        if n is None:
            return

        try: self.app._sesion_log(f"🎨 Mood: generó {n} prompts (mismo mood, distintos sujetos)")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.app.dialogs.set_estado(tr('🎨 Generando moodboard de {0} prompts...').format(n), "#f39c12")
        self.app.dialogs.toggle_botones(False)

        formato_lineas = "\n---\n".join(
            f"PROMPT {i+1}: [sujeto diverso] — POSITIVE: ... NEGATIVE: ..."
            for i in range(n)
        )
        peticion = (
            f"Genera UN MOODBOARD: {n} prompts que comparten el MISMO MOOD/atmósfera pero con SUJETOS distintos.\n\n"
            f"CONCEPTO/MOOD BASE: {idea}\n"
            f"ESTILOS: {self.app.footer.estilos_texto()}\n\n"
            f"REGLAS:\n"
            f"- Mantén la MISMA paleta, iluminación, atmósfera y estilo en TODOS los {n}.\n"
            f"- Cambia el SUJETO en cada uno (elige {n} categorías diversas: persona, "
            f"paisaje, objeto, animal, arquitectura, detalle macro, vehículo, comida, etc.).\n"
            f"- Todos juntos deben formar una serie visualmente coherente.\n\n"
            f"FORMATO ({n} prompts):\n{formato_lineas}"
        )
        try:
            peticion += self.app._contexto_loras_personaje(f"los {n} prompts del moodboard")
        except Exception as _e:
            logger.debug(f"[silent ctx] {_e}")

        def _worker():
            try:
                max_tok = min(8000, 1500 + n * 600)
                resp = self.app.deepseek.generar(peticion, temperature=0.8, max_tokens=max_tok)
                resp = limpiar_marcadores(resp)
                bloques = self.app._parsear_bloques_numerados(resp, n_esperado=n)
                if len(bloques) < 2:
                    self.app.after(0, lambda: self.app.dialogs.set_estado(tr("⚠️ Solo se generó 1 bloque, intenta de nuevo"), "#e67e22"))
                    self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))
                    return

                def _mostrar():
                    self.app._abrir_comparador(bloques[:n])
                    self.app.dialogs.set_estado(f"🎨 Moodboard listo ({len(bloques)} prompts)", "#2ecc71")
                    self.app.dialogs.toggle_botones(True)
                    self.app.dialogs._sonar_completado()
                self.app.after(0, _mostrar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    # Tipos de shot disponibles para Story.
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
        """Modal de configuración de Story.

        Permite elegir:
          • N (slider 2-6)
          • Tipos de shot explícitos (checkboxes) o "LLM elige" (toggle)

        Devuelve dict {"n": int, "tipos": [str]|None, "auto": bool} o
        None si el usuario cancela. `tipos` es lista de labels en el
        orden que el usuario marcó (no de la lista canónica).
        """
        prefs = {}
        try:
            prefs = self.app.store.cargar_preferencias() or {}
        except Exception as e:
            logger.debug(f"[silent] prefs: {e}")
        n_inicial = int(prefs.get("story_n", default_n) or default_n)
        tipos_pref = prefs.get("story_tipos") or []
        auto_pref = prefs.get("story_auto", True)
        if auto_pref is None: auto_pref = True

        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        v = GPromptWindow(self.app)
        v.title(tr("🎞 Story — configuración"))
        v.geometry("520x540")
        v.transient(self.app)

        ctk.CTkLabel(v, text=tr("🎞 Story Sequence — configura tu secuencia"),
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 4))
        ctk.CTkLabel(v, text=tr("Misma iluminación/paleta/sujeto · solo cambia el encuadre"),
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
            ctk.CTkLabel(chk_frame, text=tr("Marca los tipos de shot a usar (en orden de marca):"),
                          font=ctk.CTkFont(size=10), text_color=c["muted_text"]).pack(anchor="w", padx=10, pady=(6, 4))
            grid = ctk.CTkFrame(chk_frame, fg_color="transparent")
            grid.pack(fill="x", padx=10, pady=(0, 6))
            for i, (key, label, desc) in enumerate(self.app.STORY_SHOT_TYPES):
                marcado = key in tipos_pref
                vbool = tk.BooleanVar(value=marcado)
                chk_vars[key] = vbool
                cb = ctk.CTkCheckBox(grid, text=f"{label}  —  {desc}",
                                       variable=vbool,
                                       font=ctk.CTkFont(size=10))
                cb.grid(row=i, column=0, sticky="w", padx=4, pady=2)

        chk_toggle = ctk.CTkCheckBox(v, text=tr("🤖 Que el LLM elija los tipos automáticamente"),
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
                p = self.app.store.cargar_preferencias() or {}
                p["story_n"] = n
                p["story_tipos"] = tipos_keys
                p["story_auto"] = auto
                self.app.store.guardar_preferencias(p)
            except Exception as e:
                logger.debug(f"[silent] guardar prefs story: {e}")

        btn_row = ctk.CTkFrame(v, fg_color="transparent")
        btn_row.pack(side="bottom", pady=10)
        ctk.CTkButton(btn_row, text=tr("▶ Generar"), width=130, height=34,
                       fg_color="#1a7a3c", hover_color="#15633a",
                       font=ctk.CTkFont(size=12, weight="bold"),
                       command=_generar).pack(side="left", padx=6)
        ctk.CTkButton(btn_row, text=tr("Cancelar"), width=110, height=34,
                       fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                       command=v.destroy).pack(side="left", padx=6)

        v.bind("<Return>", lambda _e: _generar())
        v.bind("<Escape>", lambda _e: v.destroy())
        v.wait_window()
        return resultado["v"]

    def _story_label_de_key(self, key):
        for k, label, _desc in self.app.STORY_SHOT_TYPES:
            if k == key:
                return label
        return key

    def _cmd_story_sequence(self):
        """Genera N shots cinematográficos coherentes. Solo modo imagen.

        N configurable + selección explícita de tipos de shot
        (Wide/Medium/Close/POV/OTS/TopDown/Dutch/Aerial) o "auto"
        (LLM elige).
        """
        if self.app.modo_var.get() != "imagen":
            return self.app.dialogs.set_estado(tr("⚠️ Story Sequence solo está disponible en modo IMAGEN."), "#e67e22")
        idea = self.app.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.app.dialogs.set_estado(tr("⚠️ Escribe la escena base."), "#e67e22")

        cfg = self._pedir_story_config(default_n=3)
        if cfg is None:
            return
        n = cfg["n"]
        tipos = cfg["tipos"]   # lista de labels o None
        auto = cfg["auto"]

        modo_log = "auto (LLM elige)" if auto else f"manual [{', '.join(tipos)}]"
        try: self.app._sesion_log(f"🎬 Story: {n} shots · {modo_log}")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.app.dialogs.set_estado(tr('🎬 Generando secuencia cinematográfica ({0} shots)...').format(n), "#f39c12")
        self.app.dialogs.toggle_botones(False)

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
            f"ESTILOS: {self.app.footer.estilos_texto()}\n\n"
            f"REGLAS:\n"
            f"- MISMO sujeto, MISMA iluminación, MISMA paleta, MISMA atmósfera.\n"
            f"- Solo cambia el ENCUADRE/PLANO en cada uno.\n"
            f"{tipos_instr}\n\n"
            f"FORMATO ({n} shots):\n{formato_lineas}"
        )
        try:
            peticion += self.app._contexto_loras_personaje(f"los {n} shots de la secuencia")
        except Exception as _e:
            logger.debug(f"[silent ctx] {_e}")

        # Labels para el comparador (si manual, usar tipo explícito)
        labels_comp = [f"#{i+1} {tipos[i]}" for i in range(n)] if not auto else None

        def _worker():
            try:
                max_tok = min(6000, 1200 + n * 600)
                resp = self.app.deepseek.generar(peticion, temperature=0.6, max_tokens=max_tok)
                resp = limpiar_marcadores(resp)
                bloques = self.app._parsear_bloques_numerados(resp, n_esperado=n)

                def _mostrar():
                    self.app._abrir_comparador(bloques[:n], labels=labels_comp)
                    self.app.dialogs.set_estado(f"🎬 Secuencia de {len(bloques)} shots lista", "#2ecc71")
                    self.app.dialogs.toggle_botones(True)
                    self.app.dialogs._sonar_completado()
                self.app.after(0, _mostrar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _cmd_storyboard_video(self):
        """Para vídeo: N shots clave de la secuencia (apertura/desarrollo/climax/cierre).

        v2: N configurable (3-8, default 4). El LLM distribuye los beats
        de la microhistoria según el N elegido.
        """
        if self.app.modo_var.get() != "video":
            return self.app.dialogs.set_estado(tr("⚠️ Storyboard solo está disponible en modo VÍDEO."), "#e67e22")
        idea = self.app.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.app.dialogs.set_estado(tr("⚠️ Escribe la escena/historia base."), "#e67e22")

        n = self.app._pedir_n_modal(
            "📽 Board — número de frames",
            "¿Cuántos frames clave en el storyboard?\n"
            "Cuentan una microhistoria visual coherente.",
            n_min=3, n_max=8, default=4,
            key_pref="board_n",
        )
        if n is None:
            return

        try: self.app._sesion_log(f"📽 Board: generó storyboard de {n} shots")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.app.dialogs.set_estado(tr('📽 Generando storyboard de {0} shots...').format(n), "#f39c12")
        self.app.dialogs.toggle_botones(False)

        formato_lineas = "\n---\n".join(
            f"FRAME {i+1} (rol narrativo): POSITIVE: ... NEGATIVE: ..."
            for i in range(n)
        )
        peticion = (
            f"Genera un STORYBOARD DE {n} SHOTS para una secuencia de vídeo.\n\n"
            f"HISTORIA/ESCENA: {idea}\n"
            f"ESTILOS: {self.app.footer.estilos_texto()}\n\n"
            f"REGLAS:\n"
            f"- Cuenta una microhistoria visual con {n} beats: apertura → "
            f"desarrollo → (intensidad creciente) → climax → cierre.\n"
            f"- Distribuye proporcionalmente los beats según el número {n}.\n"
            f"- MISMA paleta, iluminación coherente entre frames.\n"
            f"- Cada shot es un prompt de IMAGEN (para usar como key frame del vídeo).\n\n"
            f"FORMATO ({n} frames):\n{formato_lineas}"
        )
        try:
            peticion += self.app._contexto_loras_personaje(f"los {n} frames del storyboard")
        except Exception as _e:
            logger.debug(f"[silent ctx] {_e}")

        def _worker():
            try:
                max_tok = min(7000, 1500 + n * 600)
                resp = self.app.deepseek.generar(peticion, temperature=0.7, max_tokens=max_tok)
                resp = limpiar_marcadores(resp)
                bloques = self.app._parsear_bloques_numerados(resp, n_esperado=n)

                # Botón extra para encadenar Board → Vídeo: toma los N
                # frames y pide al LLM un prompt de vídeo cinematográfico
                # que use esos frames como keyframes.
                def _encadenar_video(_variaciones, _vent):
                    self._encadenar_board_a_video(bloques[:n], _vent)

                def _mostrar():
                    self.app._abrir_comparador(
                        bloques[:n],
                        extra_botones=[
                            ("🎬 Encadenar como prompt de vídeo", "#7c3aed", _encadenar_video),
                        ],
                    )
                    self.app.dialogs.set_estado(
                        f"📽 Storyboard de {len(bloques)} frames listo · 🎬 encadénalo a vídeo desde el comparador",
                        "#2ecc71",
                    )
                    self.app.dialogs.toggle_botones(True)
                    self.app.dialogs._sonar_completado()
                self.app.after(0, _mostrar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _encadenar_board_a_video(self, frames, vent_comparador):
        """Encadenar storyboard como prompt de vídeo.

        Toma los N frames del storyboard y pide al LLM un prompt único de
        vídeo cinematográfico que use esos frames como keyframes
        (apertura → desarrollo → climax → cierre). Aplica el resultado a
        txt_salida y cierra el comparador.
        """
        if not frames:
            return self.app.dialogs.set_estado(tr("⚠️ No hay frames para encadenar."), "#e67e22")

        try: self.app._sesion_log(f"🎬 Board→Vídeo: encadenando {len(frames)} frames")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.app.dialogs.set_estado(f"🎬 Encadenando {len(frames)} frames como prompt de vídeo...", "#f39c12")
        self.app.dialogs.toggle_botones(False)

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
                resp = self.app.deepseek.generar(peticion, temperature=0.6, max_tokens=max_tok)
                resp = limpiar_marcadores(resp)

                def _aplicar():
                    # Cambiar modo a vídeo si no lo estaba ya (callback real es _on_modo_cambio)
                    if self.app.modo_var.get() != "video":
                        try:
                            self.app.modo_var.set("video")
                            if hasattr(self.app, '_on_modo_cambio'):
                                self.app.events.on_modo_cambio()
                        except Exception as e:
                            logger.debug(f"[silent] cambio modo: {e}")
                    self.app.dialogs.actualizar_salida(resp)
                    self.app.guardar_en_historial(resp)
                    self.app.dialogs.set_estado(
                        f"🎬 Vídeo encadenado de {len(frames)} keyframes aplicado al editor",
                        "#2ecc71",
                    )
                    self.app.dialogs.toggle_botones(True)
                    self.app.dialogs._sonar_completado()
                    try:
                        if vent_comparador and vent_comparador.winfo_exists():
                            vent_comparador.destroy()
                    except Exception as e:
                        logger.debug(f"[silent] cerrar comparador: {e}")
                self.app.after(0, _aplicar)
            except Exception as e:
                logger.exception("encadenar board→vídeo")
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error encadenando: {0}').format(e), "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _cmd_storyboard_imagen(self):
        """Storyboard cinematográfico para modelos de IMAGEN.

        Auto-detecta el formato según el modelo seleccionado:
          • Natural (GPT Image, DALL-E, Imagen 3, Midjourney, FLUX natural):
            SHOT + DESCRIPCIÓN narrativa cinematográfica.
          • Tag-based (Stable Diffusion, Comfy, SeaArt, NovelAI):
            SHOT + POSITIVE (tags con pesos) + NEGATIVE.

        Botón extra en el comparador: 'Fusionar en 1 prompt' que pide al LLM
        combinar los N paneles en una sola descripción multi-panel.
        """
        if self.app.modo_var.get() != "imagen":
            return self.app.dialogs.set_estado(
                tr("⚠️ Storyboard de imagen solo está disponible en modo IMAGEN."),
                "#e67e22",
            )
        idea = self.app.txt_idea.get("1.0", "end").strip()
        if not idea or len(idea) < 5:
            return self.app.dialogs.set_estado(tr("⚠️ Escribe la escena/historia base."), "#e67e22")

        # Detectar formato del modelo actual (natural vs tag-based)
        modelo = self.app.footer.modelo_imagen_valido()
        specs = get_image_model_specs(modelo) if modelo else None
        is_natural = bool(specs and specs.get("is_natural"))
        has_negative = bool(specs and specs.get("has_negative"))
        formato_etiqueta = "natural" if is_natural else "tag-based (SD/Comfy)"
        modelo_label = modelo or "modelo no detectado"

        n = self.app._pedir_n_modal(
            "🖼 Storyboard — número de paneles",
            f"¿Cuántos paneles en el storyboard?\n"
            f"Cada panel tendrá su shot type y prompt cinematográfico.\n"
            f"📐 Formato: {formato_etiqueta} · Modelo: {modelo_label}",
            n_min=3, n_max=12, default=9,
            key_pref="storyboard_img_n",
        )
        if n is None:
            return

        try: self.app._sesion_log(f"🖼 Storyboard imagen ({formato_etiqueta}): generó {n} paneles")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.app.dialogs.set_estado(tr('🖼 Generando storyboard de {0} paneles ({1})...').format(n, formato_etiqueta), "#f39c12")
        self.app.dialogs.toggle_botones(False)

        if is_natural:
            formato_lineas = "\n---\n".join(
                f"PANEL {i+1}\nSHOT: <tipo de plano>\nDESCRIPCIÓN: <una frase cinematográfica>"
                for i in range(n)
            )
            reglas_formato = (
                f"- DESCRIPCIÓN: UNA frase narrativa, en presente, visual y "
                f"emocional (estilo guion técnico).\n"
                f"- Cada panel debe ser un prompt completo y autocontenido "
                f"para pegar directamente en {modelo_label}.\n"
            )
        else:
            # Formato tag-based para SD/Comfy
            neg_block = (
                "NEGATIVE: <tags negativos comunes (blurry, low quality, "
                "deformed, etc.) + específicos del panel>"
                if has_negative
                else "(NO incluyas NEGATIVE — este modelo no lo soporta)"
            )
            formato_lineas = "\n---\n".join(
                f"PANEL {i+1}\nSHOT: <tipo de plano>\n"
                f"POSITIVE: <tags Danbooru/SD separados por comas, con pesos "
                f"(tag:1.2) cuando importe>\n{neg_block}"
                for i in range(n)
            )
            reglas_formato = (
                f"- POSITIVE: tags estilo Danbooru/SD separados por comas, "
                f"orden estándar (sujeto principal → acción → detalles → "
                f"iluminación → estilo).\n"
                f"- Usa pesos `(tag:1.2)` solo para enfatizar elementos clave.\n"
                f"- NO uses lenguaje narrativo (nada de 'a young woman who...'), "
                f"solo tags atomicos.\n"
                f"- Cada panel debe ser un prompt completo y autocontenido "
                f"para pegar directamente en {modelo_label}.\n"
            )

        peticion = (
            f"Genera un STORYBOARD DE {n} PANELES en formato {formato_etiqueta} "
            f"para el modelo {modelo_label}.\n\n"
            f"HISTORIA/ESCENA: {idea}\n"
            f"ESTILOS: {self.app.footer.estilos_texto()}\n\n"
            f"REGLAS COMUNES:\n"
            f"- Cuenta una microhistoria visual con {n} momentos: apertura → "
            f"desarrollo → tensión → climax → resolución (distribuido según N).\n"
            f"- Para cada panel, ELIGE el shot type que mejor cuente ese "
            f"momento (CLOSE-UP, MEDIUM, WIDE, EXTREME WIDE, POV, OVER-THE-"
            f"SHOULDER, OVERHEAD, LOW ANGLE, DUTCH ANGLE, INSERT, etc.).\n"
            f"- Varía los shot types entre paneles para ritmo cinematográfico "
            f"(no repitas el mismo dos veces seguidas).\n"
            f"- MANTÉN coherencia visual: misma paleta, iluminación, época y "
            f"personajes entre paneles.\n\n"
            f"REGLAS DE FORMATO:\n{reglas_formato}\n"
            f"FORMATO DE SALIDA (devuelve EXACTAMENTE {n} bloques, separados por ---):\n"
            f"{formato_lineas}"
        )
        try:
            peticion += self.app._contexto_loras_personaje(f"los {n} paneles del storyboard")
        except Exception as _e:
            logger.debug(f"[silent ctx] {_e}")

        def _worker():
            try:
                max_tok = min(7000, 1500 + n * 500)
                resp = self.app.deepseek.generar(peticion, temperature=0.75, max_tokens=max_tok)
                resp = limpiar_marcadores(resp)
                bloques = self.app._parsear_bloques_numerados(resp, n_esperado=n)

                def _fusionar(_variaciones, _vent):
                    self._fusionar_storyboard_imagen(bloques[:n], _vent)

                def _mostrar():
                    self.app._abrir_comparador(
                        bloques[:n],
                        extra_botones=[
                            ("📋 Fusionar en 1 prompt", "#7c3aed", _fusionar),
                        ],
                    )
                    self.app.dialogs.set_estado(
                        f"🖼 Storyboard de {len(bloques)} paneles listo · 📋 fusiona en 1 prompt desde el comparador",
                        "#2ecc71",
                    )
                    self.app.dialogs.toggle_botones(True)
                    self.app.dialogs._sonar_completado()
                self.app.after(0, _mostrar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _fusionar_storyboard_imagen(self, paneles, vent_comparador):
        """Fusiona los N paneles del storyboard en un único prompt multi-panel.

        Útil para modelos que soportan generar grids o múltiples viñetas en
        una sola imagen (Midjourney --tile, DALL-E con descripción multi-
        panel explícita, etc.).
        """
        if not paneles:
            return self.app.dialogs.set_estado(tr("⚠️ No hay paneles para fusionar."), "#e67e22")

        try: self.app._sesion_log(f"📋 Storyboard→1 prompt: fusionando {len(paneles)} paneles")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.app.dialogs.set_estado(f"📋 Fusionando {len(paneles)} paneles en 1 prompt...", "#f39c12")
        self.app.dialogs.toggle_botones(False)

        paneles_str = "\n\n".join(
            f"--- PANEL {i+1} ---\n{p.strip()}"
            for i, p in enumerate(paneles)
        )

        peticion = (
            f"Tengo un STORYBOARD de {len(paneles)} paneles cinematográficos. "
            f"Quiero un ÚNICO prompt para un modelo de imagen (GPT Image, "
            f"DALL-E, Midjourney) que genere una IMAGEN ÚNICA tipo página de "
            f"cómic / storyboard con los {len(paneles)} paneles dispuestos en "
            f"grid.\n\n"
            f"PANELES:\n{paneles_str}\n\n"
            f"REGLAS:\n"
            f"- UNA sola descripción de imagen multi-panel (no {len(paneles)} prompts).\n"
            f"- Indica explícitamente: 'a {len(paneles)}-panel storyboard "
            f"layout, comic book style, arranged in a grid'.\n"
            f"- Por cada panel, resume su shot type + acción en una frase "
            f"corta numerada dentro del prompt.\n"
            f"- MANTÉN paleta, iluminación, época y personajes consistentes.\n"
            f"- Estilo gráfico: pencil sketch / storyboard art / comic line "
            f"art (no foto-realista).\n\n"
            f"FORMATO:\n"
            f"PROMPT: <descripción completa de la imagen multi-panel>"
        )

        def _worker():
            try:
                max_tok = min(4500, 1500 + len(paneles) * 300)
                resp = self.app.deepseek.generar(peticion, temperature=0.6, max_tokens=max_tok)
                resp = limpiar_marcadores(resp)

                def _aplicar():
                    self.app.dialogs.actualizar_salida(resp)
                    self.app.guardar_en_historial(resp)
                    self.app.dialogs.set_estado(
                        f"📋 Storyboard fusionado en 1 prompt ({len(paneles)} paneles) aplicado al editor",
                        "#2ecc71",
                    )
                    self.app.dialogs.toggle_botones(True)
                    self.app.dialogs._sonar_completado()
                    try:
                        if vent_comparador and vent_comparador.winfo_exists():
                            vent_comparador.destroy()
                    except Exception as e:
                        logger.debug(f"[silent] cerrar comparador: {e}")
                self.app.after(0, _aplicar)
            except Exception as e:
                logger.exception("fusionar storyboard imagen")
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error fusionando: {0}').format(e), "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _cmd_random_walk(self):
        """Walk árbol visual.

        Abre una ventana con un árbol interactivo: el usuario parte del
        prompt actual (raíz) y puede ramificar en cualquier nodo para
        generar 3 derivaciones hijas. Cada hijo puede ramificarse a su
        vez. El usuario puede inspeccionar cualquier nodo, aplicar su
        prompt al editor o copiar la ruta completa raíz→…→nodo.

        Reemplaza el modo lineal (N derivaciones secuenciales) por una
        exploración no lineal estilo grafo.
        """
        actual = self.app.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.app.dialogs.set_estado(tr("⚠️ Genera un prompt primero como base."), "#e67e22")

        try: self.app._sesion_log("🌀 Walk árbol abierto")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self._abrir_walk_arbol(actual)

    def _abrir_walk_arbol(self, prompt_raiz):
        """UI del árbol de Walk.

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
        vent = GPromptWindow(self.app)
        vent.title(tr("🌀 Walk árbol — Explora derivaciones"))
        vent.geometry("1240x740")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("🌀 Walk árbol — Explora derivaciones evolutivas"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 2))
        ctk.CTkLabel(vent, text=tr("Click en un nodo para inspeccionarlo · 🌿 Ramificar genera 3 hijos vía LLM"),
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

        lbl_titulo = ctk.CTkLabel(panel, text=tr("🌿 Nodo: Raíz"),
                                   font=ctk.CTkFont(size=13, weight="bold"))
        lbl_titulo.pack(anchor="w", padx=12, pady=(10, 2))
        lbl_ruta = ctk.CTkLabel(panel, text=tr("Ruta: Raíz"),
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
                lbl_status.configure(text=tr("⚠️ Máxima profundidad alcanzada (6)"), text_color="#e67e22")
                return

            lbl_status.configure(text=tr("🌿 Generando 3 derivaciones..."), text_color="#fbbf24")
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
            try:
                peticion += self.app._contexto_loras_personaje("las 3 derivaciones")
            except Exception as _e:
                logger.debug(f"[silent ctx] {_e}")

            def _worker():
                try:
                    resp = self.app.deepseek.generar(peticion, temperature=0.85, max_tokens=2400)
                    resp = limpiar_marcadores(resp)
                    bloques = self.app._parsear_bloques_numerados(resp, n_esperado=3)
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
                    self.app.after(0, _aplicar)
                except Exception as e:
                    logger.exception("walk ramificar")
                    err = e
                    def _err():
                        lbl_status.configure(text=f"❌ Error: {err}", text_color="#e74c3c")
                        btn_ramificar.configure(state="normal")
                        btn_usar.configure(state="normal")
                    self.app.after(0, _err)

            self.app._executor.submit(_worker).add_done_callback(log_future_exc)

        # ─── Acción: usar este nodo (NO cierra, sigues explorando) ──
        def _usar_nodo():
            n = nodos[sel["id"]]
            self.app.dialogs.actualizar_salida(n["texto"])
            ruta = _ruta_de(sel["id"])
            ruta_str = " → ".join(x["label"] for x in ruta)
            self.app.dialogs.set_estado(f"📋 Walk: aplicado nodo {n['label']} (ruta: {ruta_str})", "#2ecc71")
            try: self.app._sesion_log(f"🌀 Walk: aplicó nodo {n['label']} (depth {n['depth']})")
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
            v.title(tr("📂 Ruta del nodo — preview"))
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
                    estado_lbl.configure(text=tr("✅ Copiado al portapapeles"),
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
                    if not hasattr(self.app, '_versiones_prompt'):
                        self.app._versiones_prompt = []
                    ahora = datetime.datetime.now().strftime("%H:%M:%S")
                    cadena_corta = " → ".join(x["label"] for x in ruta)
                    nuevos = 0
                    for x in ruta:
                        # Evitar duplicados: si el texto exacto ya está
                        # como última versión, no apilamos.
                        if (self.app._versiones_prompt
                                and self.app._versiones_prompt[-1].get("texto") == x["texto"]):
                            continue
                        self.app._versiones_prompt.append({
                            "texto": x["texto"],
                            "fecha": ahora,
                            "etiqueta": (f"v{len(self.app._versiones_prompt) + 1} "
                                         f"(Walk {cadena_corta} · nodo {x['label']})"),
                        })
                        nuevos += 1
                        if len(self.app._versiones_prompt) > 30:
                            self.app._versiones_prompt = self.app._versiones_prompt[-30:]
                    estado_lbl.configure(
                        text=f"✅ {nuevos} nodo(s) guardados en Versiones prompt — accesibles desde 📑 Versiones",
                        text_color="#2ecc71",
                    )
                    lbl_status.configure(
                        text=f"💾 Ruta guardada ({nuevos} nodos) en 📑 Versiones prompt",
                        text_color="#2ecc71",
                    )
                    try: self.app._sesion_log(f"🌀 Walk: guardó ruta {cadena_corta} en Versiones ({nuevos} nodos)")
                    except Exception as e:
                        logger.debug(f"[silent] {e}")
                except Exception as e:
                    estado_lbl.configure(text=f"❌ Error guardando: {e}",
                                          text_color="#e74c3c")

            btn_bar = ctk.CTkFrame(v, fg_color="transparent")
            btn_bar.pack(pady=(0, 12))
            ctk.CTkButton(btn_bar, text=tr("💾 Guardar en Versiones prompt"), width=230, height=32,
                          fg_color="#1a4a7a", hover_color="#15396a",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          command=_guardar_en_versiones).pack(side="left", padx=5)
            ctk.CTkButton(btn_bar, text=tr("📋 Copiar al portapapeles"), width=200, height=32,
                          fg_color="#1a7a3c", hover_color="#15633a",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          command=_copiar_clipboard).pack(side="left", padx=5)
            ctk.CTkButton(btn_bar, text=tr("Cerrar"), width=100, height=32,
                          fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                          command=v.destroy).pack(side="left", padx=5)
            v.bind("<Escape>", lambda _e: v.destroy())

        # ─── Acción: borrar subárbol ────────────────────────────
        def _borrar_subarbol():
            nid = sel["id"]
            if nid == 0:
                lbl_status.configure(text=tr("⚠️ No puedes borrar la raíz"), text_color="#e67e22")
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

        btn_ramificar = ctk.CTkButton(btn_row1, text=tr("🌿 Ramificar (3 hijos)"),
                                        fg_color="#7c3aed", hover_color="#5b21b6",
                                        font=ctk.CTkFont(size=11, weight="bold"),
                                        command=_ramificar)
        btn_ramificar.pack(side="left", padx=2, fill="x", expand=True)

        btn_usar = ctk.CTkButton(btn_row1, text=tr("📋 Usar este"),
                                  fg_color="#1a7a3c", hover_color="#15633a",
                                  font=ctk.CTkFont(size=11, weight="bold"),
                                  command=_usar_nodo)
        btn_usar.pack(side="left", padx=2, fill="x", expand=True)

        ctk.CTkButton(btn_row2, text=tr("💾 Guardar ruta"), fg_color="#1a4a7a",
                       hover_color="#15396a", font=ctk.CTkFont(size=10),
                       command=_copiar_ruta).pack(side="left", padx=2, fill="x", expand=True)
        ctk.CTkButton(btn_row2, text=tr("🗑 Borrar subárbol"), fg_color="#8a1a1a",
                       hover_color="#6b1414", font=ctk.CTkFont(size=10),
                       command=_borrar_subarbol).pack(side="left", padx=2, fill="x", expand=True)
        ctk.CTkButton(btn_row2, text=tr("✖ Cerrar"), fg_color=c["fg_dark"],
                       hover_color=c["fg_dark_hover"], font=ctk.CTkFont(size=10),
                       command=vent.destroy).pack(side="left", padx=2, fill="x", expand=True)

        _redibujar()
        _refresh_panel()
        vent.bind("<Escape>", lambda _e: vent.destroy())
