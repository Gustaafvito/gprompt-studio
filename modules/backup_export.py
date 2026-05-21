"""Backup & Export Mixin - Backup, Restore, CSV Export, CLI Export, Global Search."""
import os
import re
import json
import csv
import datetime
import logging
import pyperclip
import customtkinter as ctk
import tkinter as tk
from config import VERSION
from typing import TYPE_CHECKING
from modules.gprompt_window import GPromptWindow

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app import ArquitectoApp

class BackupExportMixin:
    """Mixin containing all backup, export, and search methods."""

    def _cmd_backup_completo(self):
        """Exporta TODOS los datos del usuario a un único archivo JSON de respaldo."""
        from tkinter import filedialog, messagebox
        archivo = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Backup", "*.json"), ("Todos", "*.*")],
            initialfile=f"gprompt_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.json"
        )
        if not archivo:
            return

        try:
            backup = self._construir_backup()
            with open(archivo, 'w', encoding='utf-8') as f:
                json.dump(backup, f, ensure_ascii=False, indent=2)

            tot = sum(len(backup[k]) for k in
                      ("historial", "favoritos", "estrellas",
                       "personajes", "loras", "plantillas"))
            tam_kb = os.path.getsize(archivo) / 1024
            mensaje = (
                f"💾 Backup guardado correctamente\n\n"
                f"Archivo: {os.path.basename(archivo)}\n"
                f"Tamaño: {tam_kb:.1f} KB\n"
                f"Entradas: {tot} (historial {len(backup['historial'])}, "
                f"favoritos {len(backup['favoritos'])}, "
                f"estrellas {len(backup['estrellas'])}, "
                f"personajes {len(backup['personajes'])}, "
                f"loras {len(backup['loras'])}, "
                f"plantillas {len(backup['plantillas'])})"
            )
            messagebox.showinfo("Backup completo", mensaje, parent=self)
            self.set_estado(f"💾 Backup guardado ({tot} entradas)", "#2ecc71")
        except Exception as e:
            self.set_estado(f"❌ Error en backup: {e}", "#e74c3c")
            messagebox.showerror("Error", f"No se pudo guardar el backup:\n{e}", parent=self)

    def _construir_backup(self) -> dict:
        """Construye el diccionario con todos los datos del usuario."""
        return {
            "version": VERSION,
            "fecha_backup": datetime.datetime.now().isoformat(),
            "historial":   self.store.historial or [],
            "favoritos":   self.store.favoritos or [],
            "estrellas":   self.store.estrellas or [],
            "personajes":  self.store.personajes or [],
            "loras":       self.store.loras or [],
            "plantillas":  self.store.plantillas or [],
            "preferencias": self.store.cargar_preferencias() or {},
        }

    def _cmd_restore_completo(self):
        """Restaura un backup JSON completo. ANTES de sobreescribir, guarda
        automáticamente un backup de seguridad de los datos actuales en
        ~/.arquitecto_prompts/backups/pre_restore_AAAA-MM-DD_HHMM.json
        para que el usuario pueda volver atrás si se equivoca de archivo.
        """
        from tkinter import filedialog, messagebox
        from config import BACKUPS_DIR

        archivo = filedialog.askopenfilename(
            filetypes=[("JSON Backup", "*.json"), ("Todos", "*.*")],
        )
        if not archivo:
            return

        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                backup = json.load(f)

            if not isinstance(backup, dict) or "version" not in backup:
                messagebox.showerror("Backup inválido",
                                     "El archivo no parece un backup de G-Prompt Studio "
                                     "(falta el campo 'version').",
                                     parent=self)
                return

            tot_actual = (len(self.store.historial or []) +
                          len(self.store.favoritos or []) +
                          len(self.store.estrellas or []) +
                          len(self.store.personajes or []) +
                          len(self.store.loras or []) +
                          len(self.store.plantillas or []))
            tot_backup = (len(backup.get("historial", [])) +
                          len(backup.get("favoritos", [])) +
                          len(backup.get("estrellas", [])) +
                          len(backup.get("personajes", [])) +
                          len(backup.get("loras", [])) +
                          len(backup.get("plantillas", [])))

            if not messagebox.askyesno(
                "⚠️ Confirmar restauración",
                f"Vas a SOBRESCRIBIR todos tus datos actuales con el backup.\n\n"
                f"Datos actuales: {tot_actual} entradas\n"
                f"Backup a restaurar: {tot_backup} entradas\n"
                f"Fecha del backup: {backup.get('fecha_backup', 'desconocida')}\n\n"
                f"🛡 G-Prompt guardará automáticamente un backup de seguridad "
                f"de tus datos ACTUALES antes de sobrescribir, así puedes volver "
                f"atrás si te equivocas.\n\n"
                f"¿Continuar?",
                parent=self,
            ):
                return

            # ── BACKUP AUTOMÁTICO ANTES DE RESTAURAR ──
            try:
                BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
                ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
                pre_path = BACKUPS_DIR / f"pre_restore_{ts}.json"
                with open(pre_path, 'w', encoding='utf-8') as f:
                    json.dump(self._construir_backup(), f, ensure_ascii=False, indent=2)
                logger.info(f"Backup pre-restore guardado en {pre_path}")
            except Exception as e:
                # Si no se puede guardar el backup pre-restore, ABORTAR
                # (mejor no restaurar que perder datos)
                messagebox.showerror(
                    "Error",
                    f"No se pudo crear el backup de seguridad pre-restore:\n{e}\n\n"
                    f"Restauración CANCELADA para no arriesgar tus datos actuales.",
                    parent=self,
                )
                return

            # ── RESTAURAR ──
            self.store.historial   = backup.get("historial", [])
            self.store.favoritos   = backup.get("favoritos", [])
            self.store.estrellas   = backup.get("estrellas", [])
            self.store.personajes  = backup.get("personajes", [])
            self.store.loras       = backup.get("loras", [])
            self.store.plantillas  = backup.get("plantillas", [])

            for col in ["historial", "favoritos", "estrellas",
                        "personajes", "loras", "plantillas"]:
                self.store._guardar(col)

            if backup.get("preferencias"):
                self.store.guardar_preferencias(backup["preferencias"])

            self.actualizar_combo_personajes()
            self.actualizar_combo_loras()
            if hasattr(self, "actualizar_combo_plantillas"):
                self.actualizar_combo_plantillas()

            messagebox.showinfo(
                "Restauración completada",
                f"✅ Backup restaurado ({tot_backup} entradas).\n\n"
                f"Tus datos anteriores se guardaron en:\n{pre_path}\n\n"
                f"Si te has equivocado, puedes restaurar ese archivo.",
                parent=self,
            )
            self.set_estado(f"✅ Backup restaurado ({tot_backup} entradas)", "#2ecc71")
        except Exception as e:
            self.set_estado(f"❌ Error al restaurar: {e}", "#e74c3c")
            messagebox.showerror("Error", f"No se pudo restaurar el backup:\n{e}", parent=self)

    def _cmd_exportar_csv(self):
        """Selector previo de qué exportar: historial / favoritos / estrellas /
        todos juntos. Después abre filedialog y vuelca a CSV.
        """
        # Pre-comprobación: ¿hay algo que exportar?
        hist  = self.store.historial or []
        favs  = self.store.favoritos or []
        stars = self.store.estrellas or []
        if not (hist or favs or stars):
            return self.set_estado(
                "⚠️ No hay nada que exportar (historial/favoritos/estrellas vacíos).",
                "#e67e22",
            )

        # ── Selector ──
        from modules.gprompt_window import GPromptWindow
        sel = GPromptWindow(self)
        sel.title("📊 Exportar a CSV")
        sel.geometry("420x300")
        sel.transient(self)

        ctk.CTkLabel(sel, text="📊 Exportar a CSV",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 6))
        ctk.CTkLabel(sel, text="¿Qué quieres exportar?",
                     font=ctk.CTkFont(size=11),
                     text_color="#888").pack(pady=(0, 12))

        # Checkboxes
        chk_hist_var = ctk.BooleanVar(value=True)
        chk_favs_var = ctk.BooleanVar(value=False)
        chk_stars_var = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(sel, variable=chk_hist_var,
                        text=f"📋 Historial ({len(hist)} entradas)"
                        ).pack(anchor="w", padx=40, pady=2)
        ctk.CTkCheckBox(sel, variable=chk_favs_var,
                        text=f"⭐ Favoritos ({len(favs)} entradas)"
                        ).pack(anchor="w", padx=40, pady=2)
        ctk.CTkCheckBox(sel, variable=chk_stars_var,
                        text=f"🌟 Estrellas ({len(stars)} entradas)"
                        ).pack(anchor="w", padx=40, pady=2)

        def _lanzar():
            seleccion = []
            if chk_hist_var.get(): seleccion.append(("historial", hist))
            if chk_favs_var.get(): seleccion.append(("favoritos", favs))
            if chk_stars_var.get(): seleccion.append(("estrellas", stars))
            if not seleccion:
                messagebox.showwarning("Sin selección",
                                       "Marca al menos una colección.",
                                       parent=sel)
                return
            sel.destroy()
            self._exportar_csv_ejecutar(seleccion)

        ctk.CTkButton(sel, text="▶ Exportar", width=160, height=34,
                      fg_color="#1a7a3c", command=_lanzar).pack(pady=(14, 4))
        ctk.CTkButton(sel, text="Cancelar", width=100, height=28,
                      fg_color="#444", hover_color="#555",
                      command=sel.destroy).pack(pady=2)

    def _exportar_csv_ejecutar(self, colecciones: list):
        """Exporta las colecciones seleccionadas a un CSV único.

        Args:
            colecciones: lista de tuplas (nombre, items)
        """
        from tkinter import filedialog, messagebox

        # Nombre por defecto del archivo
        nombres = "_".join(n for n, _ in colecciones)
        fecha = datetime.datetime.now().strftime("%Y%m%d")
        archivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialfile=f"gprompt_{nombres}_{fecha}.csv",
        )
        if not archivo:
            return

        def _modelo_de(it: dict) -> str:
            if it.get("modelo"):
                return str(it["modelo"])
            modo = it.get("modo", "")
            return str(it.get({
                "imagen": "modelo_img",
                "video":  "modelo_vid",
                "audio":  "modelo_aud",
            }.get(modo, "modelo_img"), "") or "")

        def _estilos_de(it: dict) -> str:
            est = it.get("estilos", "")
            if isinstance(est, list):
                return ", ".join(str(e) for e in est if e)
            return str(est)

        try:
            n = 0
            with open(archivo, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(["Origen", "Fecha", "Modo", "Plataforma", "Modelo",
                            "Ratio", "Estilos", "Destino", "NSFW", "Brief",
                            "Personaje", "LoRA", "Nota", "Prompt"])
                for nombre_col, items in colecciones:
                    for it in items:
                        if not isinstance(it, dict):
                            continue
                        w.writerow([
                            nombre_col,
                            it.get("fecha", ""),
                            it.get("modo", ""),
                            it.get("plataforma", ""),
                            _modelo_de(it),
                            it.get("ratio", ""),
                            _estilos_de(it),
                            it.get("destino", ""),
                            "Sí" if it.get("nsfw") else "No",
                            "Sí" if it.get("brief") else "No",
                            it.get("personaje", ""),
                            it.get("lora", ""),
                            it.get("nota", ""),  # solo estrellas
                            it.get("contenido", ""),
                        ])
                        n += 1
            self.set_estado(f"💾 {n} filas exportadas a CSV", "#2ecc71")
            messagebox.showinfo(
                "Exportación completada",
                f"💾 Exportadas {n} filas desde {len(colecciones)} colección(es) a:\n{archivo}",
                parent=self,
            )
        except Exception as e:
            self.set_estado(f"❌ Error al exportar: {e}", "#e74c3c")
            messagebox.showerror("Error", f"No se pudo exportar:\n{e}", parent=self)

    def _cmd_export_cli(self):
        """Convierte el prompt actual a múltiples formatos CLI / plataformas.

        15 formatos disponibles:
        - Midjourney v6+, Niji 6
        - FLUX Dev, FLUX Schnell
        - Grok / X, DALL-E 3, Leonardo.AI, Ideogram
        - ComfyUI, Automatic1111 / WebUI
        - Stable Diffusion (tags limpios)
        - Kling, Seedance (vídeo)
        - Suno (audio)
        - JSON genérico (para automatización)
        """
        import re
        import json as _json
        actual = self.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.set_estado("⚠️ Genera un prompt primero.", "#e67e22")

        ratio = self.ratio_var.get() or "1:1"
        pos = self.extraer_positive() or actual
        neg = self.extraer_negative() or ""

        # Limpiezas
        pos_sin_pesos = re.sub(r'\(([^()]+?):\s*[0-9.]+\s*\)', r'\1', pos).strip().rstrip(",").strip()
        pos_con_pesos = pos.strip().rstrip(",").strip()
        neg_sin_pesos = re.sub(r'\(([^()]+?):\s*[0-9.]+\s*\)', r'\1', neg).strip()
        neg_texto = neg.strip()

        # Negativo limpio para CLI (limitado a 6 tags principales)
        if neg_sin_pesos:
            neg_cli = ", ".join([t.strip() for t in neg_sin_pesos.split(",")[:6] if t.strip()])
        else:
            neg_cli = ""

        # ── Construir cada formato ───────────────────────────────────

        # Midjourney v6+
        mj = pos_sin_pesos + f" --ar {ratio}"
        if neg_cli:
            mj += f" --no {neg_cli}"
        mj += " --stylize 250 --quality 1 --v 6"

        # Niji 6 (anime) — Bug fix: ahora usa neg_cli directamente
        niji = pos_sin_pesos + f" --ar {ratio} --niji 6 --stylize 180"
        if neg_cli:
            niji += f" --no {neg_cli}"

        # FLUX formats
        flux_dev = pos_sin_pesos
        flux_schnell = pos_sin_pesos

        # Grok / X (texto plano sin flags)
        grok = pos_sin_pesos

        # DALL-E 3 (lenguaje natural, sin negativos)
        dalle = pos_sin_pesos
        if not dalle.endswith("."):
            dalle += "."

        # Leonardo.AI (positive + ratio aparte; sin pesos en negative)
        leonardo_pos = pos_sin_pesos
        leonardo_neg = neg_sin_pesos

        # Ideogram (positive simple, soporta texto)
        ideogram = pos_sin_pesos + f" [aspect_ratio={ratio}]"

        # ComfyUI (texto limpio sin pesos — los Turbo no los aceptan)
        comfyui = pos_sin_pesos
        if neg_sin_pesos:
            comfyui += f"\n\n--- NEGATIVE ---\n{neg_sin_pesos}"

        # Automatic1111 / WebUI (con pesos preservados)
        a1111 = pos_con_pesos
        if neg_texto:
            a1111 += f"\n\nNegative prompt: {neg_texto}"
        a1111 += f"\nSampler: DPM++ 2M Karras, Steps: 25, CFG: 7, Aspect: {ratio}"

        # Stable Diffusion / SDXL genérico (tags limpios sin pesos)
        sd = pos_sin_pesos
        if neg_sin_pesos:
            sd += f"\nNEG: {neg_sin_pesos}"

        # Video: Kling
        kling_prompt = pos_sin_pesos
        kling_neg = neg_sin_pesos

        # Video: Seedance
        seedance_prompt = pos_sin_pesos
        seedance_neg = neg_sin_pesos

        # Audio: Suno
        suno_prompt = pos_sin_pesos

        # JSON genérico (para automatización / API)
        json_payload = _json.dumps({
            "positive": pos_sin_pesos,
            "negative": neg_sin_pesos,
            "aspect_ratio": ratio,
            "model_target": getattr(self, "combo_modelo_imagen", None).get() if hasattr(self, "combo_modelo_imagen") else "unknown",
            "formats": {
                "midjourney": mj,
                "niji6": niji,
                "flux_dev": flux_dev,
                "flux_schnell": flux_schnell,
                "grok": grok,
                "dalle3": dalle,
                "leonardo": leonardo_pos,
                "ideogram": ideogram,
                "comfyui": comfyui,
                "a1111": a1111,
                "stable_diffusion": sd,
                "kling": kling_prompt,
                "seedance": seedance_prompt,
                "suno": suno_prompt,
            }
        }, indent=2, ensure_ascii=False)

        # ── Ventana con tabs ──────────────────────────────────────────

        vent = GPromptWindow(self)
        vent.title("📤 Export CLI — múltiples formatos")
        vent.geometry("780x620")
        vent.transient(self)

        ctk.CTkLabel(vent, text="📤 Export en múltiples formatos",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text="Selecciona la plataforma destino. Click en 'Copiar' para llevar al portapapeles.",
                     font=ctk.CTkFont(size=10), text_color="#888888").pack(pady=(0, 8))

        tabs = ctk.CTkTabview(vent, height=480)
        tabs.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        formatos = [
            ("🎨 Midjourney v6", mj, "#1a7a3c"),
            ("🌸 Niji 6 (anime)", niji, "#a64aa6"),
            ("⚡ FLUX Dev", flux_dev, "#7c3aed"),
            ("⚡ FLUX Schnell", flux_schnell, "#9333ea"),
            ("🤖 Grok / X", grok, "#1c1c1c"),
            ("🖌 DALL-E 3", dalle, "#10a37f"),
            ("✨ Leonardo.AI", f"POS: {leonardo_pos}\n\nNEG: {leonardo_neg}" if leonardo_neg else leonardo_pos, "#7b3aed"),
            ("📝 Ideogram", ideogram, "#d97706"),
            ("⚡ ComfyUI", comfyui, "#0891b2"),
            ("🖥 Automatic1111", a1111, "#dc2626"),
            ("🎯 SD genérico", sd, "#475569"),
            ("🎬 Kling (vídeo)", kling_prompt, "#f59e0b"),
            ("🎬 Seedance (vídeo)", seedance_prompt, "#eab308"),
            ("🎵 Suno (audio)", suno_prompt, "#ec4899"),
            ("📦 JSON (API)", json_payload, "#6366f1"),
        ]

        for nombre, contenido, color in formatos:
            tab = tabs.add(nombre)

            txt = ctk.CTkTextbox(tab, font=ctk.CTkFont(family="Consolas", size=10),
                                  wrap="word", height=380)
            txt.pack(fill="both", expand=True, padx=8, pady=(8, 4))
            txt.insert("1.0", contenido)

            btn_row = ctk.CTkFrame(tab, fg_color="transparent")
            btn_row.pack(fill="x", padx=8, pady=(0, 8))

            def _make_copy(c=contenido, n=nombre):
                def _copiar():
                    pyperclip.copy(c)
                    self.set_estado(f"📋 {n} copiado al portapapeles", "#2ecc71")
                    if hasattr(self, "show_toast"):
                        try:
                            self.show_toast(f"📋 Copiado: {n}", color, 1800)
                        except Exception as _e:
                            logger.debug(f"[silent] {_e}")
                return _copiar

            ctk.CTkButton(btn_row, text=f"📋 Copiar {nombre}", width=200, height=32,
                          fg_color=color, font=ctk.CTkFont(size=11, weight="bold"),
                          command=_make_copy()).pack(side="left", padx=4)

            ctk.CTkLabel(btn_row, text=f"   {len(contenido)} chars",
                          font=ctk.CTkFont(size=10), text_color="#888888").pack(side="left", padx=8)

        # Seleccionar Midjourney por defecto
        try:
            tabs.set("🎨 Midjourney v6")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        # ── Botón Copiar Todo ──────────────────────────────────────────
        def _copiar_todo():
            todo = "\n".join([f"===== {nom} =====\n{cont}\n" for nom, cont, _ in formatos])
            pyperclip.copy(todo)
            self.set_estado(f"📋 {len(formatos)} formatos copiados al portapapeles", "#2ecc71")

        ctk.CTkButton(vent, text=f"📋 Copiar todos los formatos ({len(formatos)})",
                      width=280, height=36, fg_color="#0f172a", hover_color="#1e293b",
                      font=ctk.CTkFont(size=11, weight="bold"),
                      text_color="#e2e8f0",
                      command=_copiar_todo).pack(pady=(4, 12))

    def _cmd_busqueda_global(self):
        """Busca un término en TODAS las colecciones: historial, favoritos, estrellas, seeds, snippets, fórmulas."""
        vent = GPromptWindow(self)
        vent.title("🔎 Búsqueda global")
        vent.geometry("750x600")
        vent.transient(self)

        ctk.CTkLabel(vent, text="🔎 Búsqueda en todas las colecciones",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text="Busca en: Historial, Favoritos, Estrellas, Seeds, Snippets, Fórmulas, Personajes, LoRAs",
                     font=ctk.CTkFont(size=10), text_color="#888888").pack(pady=(0, 10))

        f_search = ctk.CTkFrame(vent, fg_color="transparent")
        f_search.pack(fill="x", padx=15, pady=5)
        ent = ctk.CTkEntry(f_search, placeholder_text="Escribe lo que buscas (ej: 'cyberpunk', 'fox', 'masterpiece')...",
                            width=600, height=32, font=ctk.CTkFont(size=12))
        ent.pack(side="left", fill="x", expand=True)
        ent.focus_set()

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        def buscar(event=None):
            for w in scroll.winfo_children(): w.destroy()
            termino = ent.get().strip().lower()
            if not termino or len(termino) < 2:
                ctk.CTkLabel(scroll, text="Escribe al menos 2 caracteres para buscar.",
                             font=ctk.CTkFont(size=11), text_color="#666666").pack(pady=20)
                return

            resultados = []
            prefs = self.store.cargar_preferencias()

            for i, item in enumerate(self.store.historial or []):
                if isinstance(item, dict):
                    txt_full = " ".join([
                        str(item.get("contenido", "")),
                        str(item.get("estilos", "")),
                        str(item.get("personaje", "")),
                        str(item.get("plataforma", "")),
                    ]).lower()
                else:
                    txt_full = str(item).lower()
                if termino in txt_full:
                    contenido = item.get("contenido", "") if isinstance(item, dict) else str(item)
                    resultados.append(("📋 Historial", item.get("fecha", "") if isinstance(item, dict) else "", contenido[:200], lambda c=contenido: self.actualizar_salida(c)))

            for item in (self.store.favoritos or []):
                if isinstance(item, dict):
                    txt = item.get("contenido", "") + " " + item.get("nombre", "")
                else:
                    txt = str(item)
                if termino in txt.lower():
                    contenido = item.get("contenido", "") if isinstance(item, dict) else str(item)
                    nombre = item.get("nombre", "") if isinstance(item, dict) else ""
                    resultados.append(("⭐ Favorito", nombre, contenido[:200], lambda c=contenido: self.actualizar_salida(c)))

            for item in (self.store.estrellas or []):
                if isinstance(item, dict):
                    txt = item.get("contenido", "") + " " + item.get("nombre", "")
                else:
                    txt = str(item)
                if termino in txt.lower():
                    contenido = item.get("contenido", "") if isinstance(item, dict) else str(item)
                    nombre = item.get("nombre", "") if isinstance(item, dict) else ""
                    resultados.append(("🌟 Estrella", nombre, contenido[:200], lambda c=contenido: self.actualizar_salida(c)))

            for s in (prefs.get("seeds_favoritos") or []):
                txt = " ".join([s.get("nombre", ""), str(s.get("estilos", [])), s.get("plataforma", ""),
                                 s.get("modelo_img", ""), s.get("modelo_vid", "")]).lower()
                if termino in txt:
                    desc = f"Modelo: {s.get('modelo_img') or s.get('modelo_vid', '')}, Estilos: {', '.join(s.get('estilos', [])[:3])}"
                    resultados.append(("💎 Seed", s.get("nombre", "?"), desc, lambda seed=s: self._aplicar_seed(seed)))

            for s in (prefs.get("snippets") or []):
                txt = (s.get("nombre", "") + " " + s.get("tags", "")).lower()
                if termino in txt:
                    resultados.append(("✂️ Snippet", s.get("nombre", "?"), s.get("tags", "")[:200],
                                        lambda tags=s.get("tags", ""): self._aplicar_atajo_tags(tags)))

            for f in (prefs.get("formulas") or []):
                txt = (f.get("nombre", "") + " " + f.get("positive", "") + " " + f.get("negative", "")).lower()
                if termino in txt:
                    pos_neg = f.get("positive", "")[:200]
                    def _cargar_formula(ff=f):
                        txt_form = f"POSITIVE PROMPT: {ff.get('positive', '')}"
                        if ff.get('negative'):
                            txt_form += f"\nNEGATIVE PROMPT: {ff.get('negative')}"
                        self.actualizar_salida(txt_form)
                    resultados.append(("🧪 Fórmula", f.get("nombre", "?"), pos_neg, _cargar_formula))

            for p in (self.store.personajes or []):
                txt = (p.get("nombre", "") + " " + p.get("rasgos", "")).lower()
                if termino in txt:
                    resultados.append(("🧑 Personaje", p.get("nombre", "?"), p.get("rasgos", "")[:200],
                                        lambda nombre=p.get("nombre", ""): self.combo_personaje.set(nombre) if hasattr(self, 'combo_personaje') else None))

            for l in (self.store.loras or []):
                txt = (l.get("nombre", "") + " " + l.get("descripcion", "")).lower()
                if termino in txt:
                    resultados.append(("🔗 LoRA", l.get("nombre", "?"), l.get("descripcion", "")[:200],
                                        lambda nombre=l.get("nombre", ""): self.combo_lora.set(nombre) if hasattr(self, 'combo_lora') else None))

            if not resultados:
                ctk.CTkLabel(scroll, text=f"Sin resultados para '{termino}'",
                             font=ctk.CTkFont(size=11), text_color="#666666").pack(pady=20)
                return

            ctk.CTkLabel(scroll, text=f"📊 {len(resultados)} resultado{'s' if len(resultados) != 1 else ''} encontrado{'s' if len(resultados) != 1 else ''}",
                         font=ctk.CTkFont(size=11, weight="bold"), text_color="#2ecc71").pack(anchor="w", pady=(0, 8))

            for tipo, nombre, contenido, accion in resultados[:50]:
                card = ctk.CTkFrame(scroll, fg_color="#111820", corner_radius=6)
                card.pack(fill="x", pady=3)
                hdr = ctk.CTkFrame(card, fg_color="#1a2a3a", corner_radius=4, height=22)
                hdr.pack(fill="x", padx=4, pady=(3, 0))
                hdr.pack_propagate(False)
                ctk.CTkLabel(hdr, text=f"  {tipo}", font=ctk.CTkFont(size=10, weight="bold"),
                             text_color="#aaccee").pack(side="left", padx=4)
                if nombre:
                    ctk.CTkLabel(hdr, text=nombre[:50], font=ctk.CTkFont(size=10),
                                 text_color="#cccccc").pack(side="left", padx=10)

                ctk.CTkLabel(card, text=contenido, font=ctk.CTkFont(size=10),
                             text_color="#888888", wraplength=680, justify="left", anchor="w").pack(fill="x", padx=8, pady=(2, 4))

                btn = ctk.CTkButton(card, text="✅ Aplicar", width=90, height=22, fg_color="#1a7a3c",
                                      font=ctk.CTkFont(size=10),
                                      command=lambda a=accion: (a(), vent.destroy(), self.set_estado(f"✅ Aplicado: {nombre or tipo}", "#2ecc71")))
                btn.pack(anchor="e", padx=8, pady=(0, 4))

        ent.bind("<KeyRelease>", buscar)

    def _close_menu_if_open(self, event=None):
        """Cierra el menú desplegable si está abierto."""
        if hasattr(self, '_menu_activo') and self._menu_activo:
            try:
                self._menu_activo.destroy()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            self._menu_activo = None
