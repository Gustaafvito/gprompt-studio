"""JSON profesional — importar / exportar prompts estructurados.

Permite trabajar con prompts en formato JSON al estilo de Veo, Sora,
Kling y otros generadores avanzados de vídeo / imagen, que esperan
un dict con campos tipo:

  {
    "prompt": "...",
    "negative_prompt": "...",
    "duration": 8,
    "aspect_ratio": "9:16",
    "audio": {"music": "none", "sound_effects": [...]},
    "style_tags": [...],
    "camera": {"type": "...", "movement": "..."},
    "lighting": {"ambient": "...", "screen_glow": "..."},
    "vfx_notes": {...}
  }

Métodos:
  • _cmd_importar_json_prompt — pegar JSON → cargar prompt en
    txt_salida + negative en panel + mostrar metadatos extras.
  • _cmd_exportar_json_prompt — tomar prompt actual + llamar LLM
    para enriquecer con camera/lighting/vfx/audio → modal con JSON
    listo para copiar/guardar.

Dependencias self (provistas por ArquitectoApp):
  txt_idea, txt_salida, modo_var, ratio_var, deepseek, after,
  set_estado, toggle_botones, actualizar_salida, _sesion_log,
  _on_modo_cambio.
"""
import json
import logging
import threading
from tkinter import filedialog, messagebox

import pyperclip
import customtkinter as ctk

from config import get_theme_colors
from workers import limpiar_marcadores
from modules.gprompt_window import GPromptWindow

logger = logging.getLogger(__name__)

# Campos canónicos que el importador reconoce.
# Cualquier otro campo se muestra como "metadato extra".
CAMPOS_NUCLEO = {"prompt", "negative_prompt", "positive_prompt"}
CAMPOS_TECNICOS = {"duration", "aspect_ratio", "fps", "resolution"}
CAMPOS_AVANZADOS = {"audio", "style_tags", "camera", "lighting", "vfx_notes",
                     "composition", "color_grading", "post_processing"}


def _limpiar_json_de_newlines(texto: str) -> str:
    """Reemplaza saltos de línea literales DENTRO de strings JSON por espacios.

    Problema típico: al copiar JSON de webs (Gemini, ChatGPT, foros) los
    strings vienen partidos en varias líneas físicas con newlines reales
    en lugar de '\\n' escapado. json.loads rechaza eso con
    "Invalid control character at...".

    Recorre el texto en modo state-machine respetando las comillas y
    sustituye solo los newlines/tabs DENTRO de strings, dejando intactos
    los del exterior (indentación, separadores entre campos, etc.).

    No es un parser JSON completo — asume que las comillas dentro de
    strings vienen escapadas (\\"), lo cual es la convención estándar.
    """
    out = []
    in_string = False
    escape = False
    for ch in texto:
        if escape:
            out.append(ch)
            escape = False
            continue
        if ch == "\\":
            out.append(ch)
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string and ch in "\n\r\t":
            # Reemplazar newlines literales por espacio dentro de strings
            out.append(" ")
        else:
            out.append(ch)
    # Colapsar dobles espacios resultantes dentro de strings
    return "".join(out)


class JsonPromptMixin:
    """Mixin con importar / exportar prompts en JSON profesional."""

    # ─────────────────────────────────────────────────────────────
    # IMPORTAR
    # ─────────────────────────────────────────────────────────────

    def _cmd_importar_json_prompt(self):
        """Modal para pegar un JSON profesional y cargarlo en la app."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self)
        vent.title("📥 Importar prompt JSON profesional")
        vent.geometry("780x640")
        vent.transient(self)

        ctk.CTkLabel(vent, text="📥 Importar prompt JSON profesional",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4))
        ctk.CTkLabel(
            vent,
            text="Pega un JSON tipo Veo / Sora / Kling. Se extraerá el prompt principal,\n"
                 "negative, ratio/duración y se mostrarán los metadatos extra (camera/lighting/vfx).",
            font=ctk.CTkFont(size=10), text_color=c["muted_text"], justify="center",
        ).pack(pady=(0, 8))

        # Textbox para pegar JSON
        txt_json = ctk.CTkTextbox(vent, wrap="word",
                                    font=ctk.CTkFont(family="Consolas", size=10),
                                    height=320)
        txt_json.pack(fill="both", expand=True, padx=15, pady=(0, 6))

        # Status label
        lbl_status = ctk.CTkLabel(vent, text="",
                                    font=ctk.CTkFont(size=10),
                                    text_color="#fbbf24")
        lbl_status.pack(pady=(0, 4))

        # Botones de acción
        btn_row = ctk.CTkFrame(vent, fg_color="transparent")
        btn_row.pack(pady=(0, 12))

        def _pegar_portapapeles():
            try:
                contenido = pyperclip.paste()
                if contenido:
                    txt_json.delete("1.0", "end")
                    txt_json.insert("1.0", contenido)
                    lbl_status.configure(text=f"📋 Pegado ({len(contenido)} chars)",
                                          text_color="#2ecc71")
            except Exception as e:
                lbl_status.configure(text=f"❌ No se pudo pegar: {e}",
                                      text_color="#e74c3c")

        def _cargar_desde_archivo():
            ruta = filedialog.askopenfilename(
                title="Seleccionar archivo JSON",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                parent=vent,
            )
            if not ruta:
                return
            try:
                with open(ruta, encoding="utf-8") as f:
                    contenido = f.read()
                txt_json.delete("1.0", "end")
                txt_json.insert("1.0", contenido)
                lbl_status.configure(text=f"📂 Cargado: {ruta}",
                                      text_color="#2ecc71")
            except Exception as e:
                lbl_status.configure(text=f"❌ Error abriendo archivo: {e}",
                                      text_color="#e74c3c")

        def _importar():
            texto = txt_json.get("1.0", "end").strip()
            if not texto:
                lbl_status.configure(text="⚠️ Pega un JSON primero",
                                      text_color="#e67e22")
                return
            limpieza_aplicada = False
            try:
                data = json.loads(texto)
            except json.JSONDecodeError as e:
                # Caso típico: JSON con saltos de línea literales dentro de
                # strings (copy/paste de webs). Intentamos limpiar y reparsear
                # automáticamente. Si tampoco funciona, devolvemos el error.
                if "Invalid control character" in str(e) or "control character" in str(e).lower():
                    texto_limpio = _limpiar_json_de_newlines(texto)
                    try:
                        data = json.loads(texto_limpio)
                        limpieza_aplicada = True
                        # Actualizamos el textbox con la versión limpia por si
                        # el usuario quiere verla.
                        txt_json.delete("1.0", "end")
                        txt_json.insert("1.0", texto_limpio)
                    except json.JSONDecodeError as e2:
                        lbl_status.configure(
                            text=f"❌ JSON inválido (incluso tras autolimpieza): {e2}",
                            text_color="#e74c3c",
                        )
                        return
                else:
                    lbl_status.configure(text=f"❌ JSON inválido: {e}",
                                          text_color="#e74c3c")
                    return
            if not isinstance(data, dict):
                lbl_status.configure(text="❌ El JSON debe ser un objeto {} en raíz",
                                      text_color="#e74c3c")
                return

            if limpieza_aplicada:
                # Avisar antes de cerrar para que el usuario sepa qué pasó
                logger.info("JSON import: autolimpieza de newlines aplicada")

            resumen = self._aplicar_json_a_app(data)
            resumen["limpieza_aplicada"] = limpieza_aplicada
            vent.destroy()
            # Resumen → modal nuevo con lo aplicado + metadatos extras
            self._mostrar_resumen_import(data, resumen)

        ctk.CTkButton(btn_row, text="📋 Pegar portapapeles", width=170, height=32,
                       fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                       command=_pegar_portapapeles).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="📂 Cargar .json", width=130, height=32,
                       fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                       command=_cargar_desde_archivo).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="✅ Importar", width=140, height=32,
                       fg_color="#1a7a3c", hover_color="#15633a",
                       font=ctk.CTkFont(size=12, weight="bold"),
                       command=_importar).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Cancelar", width=110, height=32,
                       fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                       command=vent.destroy).pack(side="left", padx=4)

        vent.bind("<Escape>", lambda _e: vent.destroy())

    def _aplicar_json_a_app(self, data):
        """Aplica los campos reconocidos del JSON a la UI.

        Devuelve dict con resumen de qué se aplicó:
          {"prompt": bool, "negative": bool, "ratio": str|None,
           "duration": int|None, "modo": str|None, "extras": [keys]}
        """
        resumen = {"prompt": False, "negative": False, "ratio": None,
                   "duration": None, "modo": None, "extras": []}

        # 1. Prompt principal — puede venir como "prompt" o "positive_prompt"
        prompt = data.get("prompt") or data.get("positive_prompt")
        if isinstance(prompt, str) and prompt.strip():
            # Si tiene formato POSITIVE/NEGATIVE explícito, dejarlo tal cual
            negative = data.get("negative_prompt")
            if isinstance(negative, str) and negative.strip():
                texto_final = (
                    f"POSITIVE PROMPT: {prompt.strip()}\n\n"
                    f"NEGATIVE PROMPT: {negative.strip()}"
                )
                resumen["negative"] = True
            else:
                texto_final = f"POSITIVE PROMPT: {prompt.strip()}"
            try:
                self.actualizar_salida(texto_final)
                resumen["prompt"] = True
            except Exception as e:
                logger.warning(f"actualizar_salida desde JSON falló: {e}")

        # 2. Detectar modo según señales
        modo_detectado = None
        if any(k in data for k in ("duration", "fps", "camera", "vfx_notes")):
            modo_detectado = "video"
        elif "audio" in data and not data.get("prompt", "").lower().count("video"):
            # Si tiene audio pero no menciona video → puede ser audio puro
            audio = data.get("audio")
            if isinstance(audio, dict) and (audio.get("music") or audio.get("lyrics")):
                modo_detectado = "audio"
        # Cambiar modo si difiere del actual
        if modo_detectado and hasattr(self, "modo_var"):
            try:
                modo_actual = self.modo_var.get()
                if modo_actual != modo_detectado:
                    self.modo_var.set(modo_detectado)
                    if hasattr(self, "_on_modo_cambio"):
                        self._on_modo_cambio()
                    resumen["modo"] = modo_detectado
            except Exception as e:
                logger.debug(f"[silent] cambio modo: {e}")

        # 3. Aspect ratio
        ratio = data.get("aspect_ratio")
        if isinstance(ratio, str) and ratio.strip():
            try:
                if hasattr(self, "ratio_var"):
                    self.ratio_var.set(ratio.strip())
                if hasattr(self, "combo_ratio"):
                    self.combo_ratio.set(ratio.strip())
                resumen["ratio"] = ratio.strip()
            except Exception as e:
                logger.debug(f"[silent] ratio: {e}")

        # 4. Duración (vídeo)
        duration = data.get("duration")
        if isinstance(duration, (int, float)):
            resumen["duration"] = int(duration)
            # Algunos models tienen combo_duracion_video — buscarlo
            for attr in ("combo_duracion_video", "combo_duracion", "duracion_var"):
                if hasattr(self, attr):
                    try:
                        widget = getattr(self, attr)
                        if hasattr(widget, "set"):
                            widget.set(str(int(duration)))
                    except Exception:
                        pass

        # 5. Cualquier otro campo "avanzado" → guardar en self._json_import_extras
        # para que el resumen lo muestre y el usuario lo tenga a mano.
        extras = {}
        for k, v in data.items():
            if k in CAMPOS_NUCLEO or k in CAMPOS_TECNICOS:
                continue
            extras[k] = v
        if extras:
            self._json_import_extras = extras
            resumen["extras"] = list(extras.keys())

        # 6. Sesión log
        try:
            origen = "Veo/Sora/Kling JSON"
            self._sesion_log(f"📥 Importó prompt JSON ({origen}, {len(data)} campos)")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.set_estado(
            f"📥 JSON importado — prompt aplicado"
            + (f" · modo→{resumen['modo']}" if resumen["modo"] else "")
            + (f" · ratio={resumen['ratio']}" if resumen["ratio"] else ""),
            "#2ecc71",
        )
        return resumen

    def _mostrar_resumen_import(self, data, resumen):
        """Modal con resumen de qué se aplicó + metadatos extras visibles."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self)
        vent.title("📥 Importación completada")
        vent.geometry("760x640")
        vent.transient(self)

        ctk.CTkLabel(vent, text="📥 Importación completada",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 4))

        # Aviso si se aplicó autolimpieza
        if resumen.get("limpieza_aplicada"):
            ctk.CTkLabel(
                vent,
                text="🧹 JSON con saltos de línea dentro de strings — "
                     "autolimpieza aplicada (newlines → espacios)",
                font=ctk.CTkFont(size=10),
                text_color="#fbbf24",
                wraplength=720, justify="center",
            ).pack(pady=(0, 6), padx=15)

        # Resumen
        partes = []
        if resumen.get("prompt"):
            partes.append("✅ Prompt aplicado al editor")
        if resumen.get("negative"):
            partes.append("✅ NEGATIVE incluido")
        if resumen.get("modo"):
            partes.append(f"🎛 Modo cambiado a {resumen['modo'].upper()}")
        if resumen.get("ratio"):
            partes.append(f"📐 Aspect ratio: {resumen['ratio']}")
        if resumen.get("duration"):
            partes.append(f"⏱ Duración: {resumen['duration']}s (mostrada como nota)")
        ctk.CTkLabel(vent, text="  ·  ".join(partes) if partes else "Nada aplicado.",
                     font=ctk.CTkFont(size=11),
                     text_color="#2ecc71" if partes else "#e67e22",
                     wraplength=720, justify="center").pack(pady=(0, 10), padx=15)

        # Metadatos extras (camera, lighting, vfx_notes, audio, etc.)
        extras = resumen.get("extras", [])
        if extras:
            ctk.CTkLabel(
                vent,
                text=f"🧩 Metadatos avanzados detectados ({len(extras)}):",
                font=ctk.CTkFont(size=11, weight="bold"),
            ).pack(anchor="w", padx=15, pady=(8, 4))
            ctk.CTkLabel(
                vent,
                text="No se aplican automáticamente — algunos motores (Veo/Sora/Kling) "
                     "los usan vía API JSON. Puedes verlos a continuación e incorporarlos "
                     "manualmente al prompt si tu motor no soporta JSON estructurado.",
                font=ctk.CTkFont(size=9),
                text_color=c["muted_text"],
                wraplength=720, justify="left",
            ).pack(anchor="w", padx=15, pady=(0, 6))

            scroll = ctk.CTkScrollableFrame(vent, fg_color=c["fg_dark"],
                                              corner_radius=8)
            scroll.pack(fill="both", expand=True, padx=15, pady=4)

            for k in extras:
                v = data.get(k)
                card = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=6)
                card.pack(fill="x", pady=4, padx=4)
                ctk.CTkLabel(card, text=f"  {k}",
                              font=ctk.CTkFont(size=11, weight="bold"),
                              text_color=c["hdr_text"]).pack(anchor="w", padx=8, pady=(6, 2))
                # Convertir el valor a texto legible (JSON pretty)
                try:
                    val_text = json.dumps(v, indent=2, ensure_ascii=False)
                except Exception:
                    val_text = str(v)
                # Limitar preview a ~600 chars para no inflar
                if len(val_text) > 600:
                    val_text = val_text[:600] + "\n…"
                ctk.CTkLabel(card, text=val_text,
                              font=ctk.CTkFont(family="Consolas", size=9),
                              text_color=c["muted_text"], wraplength=680,
                              justify="left", anchor="w").pack(anchor="w",
                              padx=12, pady=(0, 6))
        else:
            ctk.CTkLabel(vent, text="(Sin metadatos avanzados detectados)",
                         font=ctk.CTkFont(size=10),
                         text_color=c["muted_text"]).pack(pady=10)

        # Botones
        btn_row = ctk.CTkFrame(vent, fg_color="transparent")
        btn_row.pack(pady=(8, 12))

        def _copiar_extras():
            extras_dict = {k: data.get(k) for k in extras}
            try:
                pyperclip.copy(json.dumps(extras_dict, indent=2, ensure_ascii=False))
                self.set_estado("📋 Metadatos extras copiados al portapapeles", "#2ecc71")
            except Exception as e:
                self.set_estado(f"❌ No se pudo copiar: {e}", "#e74c3c")

        if extras:
            ctk.CTkButton(btn_row, text="📋 Copiar metadatos extras", width=210, height=32,
                          fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                          command=_copiar_extras).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Cerrar", width=120, height=32,
                       fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                       command=vent.destroy).pack(side="left", padx=4)
        vent.bind("<Escape>", lambda _e: vent.destroy())

    # ─────────────────────────────────────────────────────────────
    # EXPORTAR
    # ─────────────────────────────────────────────────────────────

    def _cmd_exportar_json_prompt(self):
        """Convierte el prompt actual + idea en un JSON profesional.

        Llama al LLM para enriquecer con camera, lighting, vfx_notes,
        audio.sound_effects, style_tags, duration, aspect_ratio.
        Muestra modal con el JSON listo para copiar o guardar.
        """
        prompt_actual = self.txt_salida.get("1.0", "end").strip()
        if not prompt_actual or len(prompt_actual) < 20:
            self.set_estado(
                "⚠️ Genera primero un prompt para exportarlo como JSON profesional.",
                "#e67e22",
            )
            return

        modo = self.modo_var.get() if hasattr(self, "modo_var") else "video"
        ratio = ""
        if hasattr(self, "ratio_var"):
            try: ratio = self.ratio_var.get() or ""
            except Exception: ratio = ""

        try: self._sesion_log(f"📤 Exportó prompt JSON profesional ({modo})")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        self.set_estado("📤 Enriqueciendo prompt a JSON profesional vía LLM...",
                         "#f39c12")
        self.toggle_botones(False)

        # Construir petición al LLM para producir el JSON
        guia_modo = {
            "video": (
                "El prompt es para un GENERADOR DE VÍDEO (estilo Veo / Sora / Kling). "
                "Incluye campos para: duration (int en segundos, 4-12), "
                "aspect_ratio (16:9, 9:16 o 1:1), "
                "camera (type, movement, depth_of_field), "
                "lighting (ambient, key_light, accent), "
                "vfx_notes con efectos específicos descritos, "
                "audio con music y sound_effects lista, "
                "style_tags lista de 8-12 keywords cinematográficas."
            ),
            "imagen": (
                "El prompt es para un GENERADOR DE IMAGEN. "
                "Incluye campos para: aspect_ratio, "
                "camera (lens_simulada, angulo, depth_of_field), "
                "lighting (tipo, hora_dia, mood), "
                "style_tags lista de 8-12 keywords visuales, "
                "composition (regla, foco, balance)."
            ),
            "audio": (
                "El prompt es para un GENERADOR DE AUDIO. "
                "Incluye campos para: duration (segundos), "
                "genre, tempo_bpm, instrumentation lista, "
                "mood, vocal_style si aplica, "
                "style_tags lista de 6-10 keywords."
            ),
        }.get(modo, "")

        peticion = (
            f"Tengo este prompt y quiero convertirlo en un JSON ESTRUCTURADO "
            f"profesional tipo Veo/Sora/Kling para envío a APIs avanzadas.\n\n"
            f"PROMPT ACTUAL:\n{prompt_actual}\n\n"
            f"{guia_modo}\n\n"
            f"REGLAS:\n"
            f"1. Devuelve SOLO el JSON, sin ningún texto antes o después.\n"
            f"2. NO uses markdown (```json), SOLO el objeto JSON crudo.\n"
            f"3. Incluye el campo 'prompt' con la descripción narrativa principal "
            f"(puede ser larga, 3-8 frases continuas describiendo la escena/acción).\n"
            f"4. Incluye 'negative_prompt' con lo que evitar.\n"
            f"5. {'Aspect_ratio sugerido: ' + ratio if ratio else 'Elige aspect_ratio apropiado'}.\n"
            f"6. Sé ESPECÍFICO y CINEMATOGRÁFICO en camera/lighting/vfx_notes.\n"
            f"7. style_tags debe ser lista de strings, no objeto."
        )

        def _worker():
            try:
                resp = self.deepseek.generar(peticion, temperature=0.5, max_tokens=2800)
                resp = limpiar_marcadores(resp).strip()

                # Limpiar posibles fences markdown
                if resp.startswith("```"):
                    # quitar primera y última línea si son fences
                    lineas = resp.splitlines()
                    if lineas[0].startswith("```"):
                        lineas = lineas[1:]
                    if lineas and lineas[-1].startswith("```"):
                        lineas = lineas[:-1]
                    resp = "\n".join(lineas).strip()

                # Intentar parsear para validar
                try:
                    parsed = json.loads(resp)
                    json_pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
                except json.JSONDecodeError as e:
                    # Mostrar igual aunque no parsee — usuario podrá corregir
                    parsed = None
                    json_pretty = resp
                    logger.warning(f"JSON pro inválido: {e}")

                def _mostrar():
                    self.toggle_botones(True)
                    self._mostrar_modal_export(json_pretty, parsed is not None)
                    self.set_estado(
                        "📤 JSON profesional listo"
                        + ("" if parsed is not None else " ⚠️ (puede tener errores de sintaxis)"),
                        "#2ecc71" if parsed is not None else "#e67e22",
                    )

                self.after(0, _mostrar)
            except Exception as e:
                logger.exception("exportar json")
                self.after(0, lambda: self.set_estado(f"❌ Error exportando: {e}",
                                                       "#e74c3c"))
                self.after(0, lambda: self.toggle_botones(True))

        threading.Thread(target=_worker, daemon=True).start()

    def _mostrar_modal_export(self, json_texto, json_valido=True):
        """Modal con el JSON exportado + copiar / guardar como archivo."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self)
        vent.title("📤 JSON profesional exportado")
        vent.geometry("840x680")
        vent.transient(self)

        titulo = "📤 JSON profesional exportado"
        if not json_valido:
            titulo += "  ⚠️ JSON con errores de sintaxis"
        ctk.CTkLabel(vent, text=titulo,
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 2))
        ctk.CTkLabel(
            vent,
            text="Listo para enviar a Veo / Sora / Kling u otros motores con JSON API."
                 if json_valido
                 else "El LLM no devolvió JSON 100% válido — revisa antes de usar.",
            font=ctk.CTkFont(size=10),
            text_color=c["muted_text"] if json_valido else "#fbbf24",
        ).pack(pady=(0, 8))

        txt = ctk.CTkTextbox(vent, wrap="none",
                              font=ctk.CTkFont(family="Consolas", size=10))
        txt.pack(fill="both", expand=True, padx=15, pady=(0, 8))
        txt.insert("1.0", json_texto)
        # Permitir edición por si el usuario quiere corregir
        # (sin disabled para que pueda ajustar campos)

        lbl_status = ctk.CTkLabel(vent, text="", font=ctk.CTkFont(size=10),
                                    text_color="#fbbf24")
        lbl_status.pack(pady=(0, 2))

        # Botones
        btn_row = ctk.CTkFrame(vent, fg_color="transparent")
        btn_row.pack(pady=(0, 12))

        def _copiar():
            contenido = txt.get("1.0", "end").strip()
            try:
                pyperclip.copy(contenido)
                lbl_status.configure(text="✅ JSON copiado al portapapeles",
                                      text_color="#2ecc71")
            except Exception as e:
                lbl_status.configure(text=f"❌ No se pudo copiar: {e}",
                                      text_color="#e74c3c")

        def _guardar_archivo():
            contenido = txt.get("1.0", "end").strip()
            ruta = filedialog.asksaveasfilename(
                title="Guardar JSON profesional",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                parent=vent,
            )
            if not ruta:
                return
            try:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(contenido)
                lbl_status.configure(text=f"💾 Guardado: {ruta}",
                                      text_color="#2ecc71")
            except Exception as e:
                lbl_status.configure(text=f"❌ Error guardando: {e}",
                                      text_color="#e74c3c")

        def _validar():
            contenido = txt.get("1.0", "end").strip()
            try:
                json.loads(contenido)
                lbl_status.configure(text="✅ JSON válido (parsea correctamente)",
                                      text_color="#2ecc71")
            except json.JSONDecodeError as e:
                lbl_status.configure(text=f"❌ Error de sintaxis: {e}",
                                      text_color="#e74c3c")

        ctk.CTkButton(btn_row, text="📋 Copiar JSON", width=140, height=32,
                       fg_color="#1a7a3c", hover_color="#15633a",
                       font=ctk.CTkFont(size=12, weight="bold"),
                       command=_copiar).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="💾 Guardar .json", width=140, height=32,
                       fg_color="#1a4a7a", hover_color="#15396a",
                       command=_guardar_archivo).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="✓ Validar sintaxis", width=140, height=32,
                       fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                       command=_validar).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Cerrar", width=110, height=32,
                       fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                       command=vent.destroy).pack(side="left", padx=4)
        vent.bind("<Escape>", lambda _e: vent.destroy())
