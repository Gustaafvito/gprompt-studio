"""Backup & Export Mixin - Backup, Restore, CSV Export, CLI Export, Global Search."""
import csv
import datetime
import json
import logging
import os
from tkinter import messagebox
from typing import TYPE_CHECKING

import customtkinter as ctk
import pyperclip

from config import VERSION
from modules.gprompt_window import GPromptWindow
from modules.i18n import tr

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


def _csv_safe(valor) -> str:
    """Neutraliza CSV injection: Excel/Sheets ejecutan como fórmula las
    celdas que empiezan por =, +, -, @ o tab. Se prefija con ' (apóstrofo),
    que Excel interpreta como "texto literal"."""
    s = "" if valor is None else str(valor)
    if s and s[0] in ("=", "+", "-", "@", "\t"):
        return "'" + s
    return s

class BackupExportService:
    """Backup, Restore, Export CSV/CLI, Búsqueda Global.

    A1 fase 2 (sesión 14): servicio aislado con app por composición.
    """

    def __init__(self, app):
        self.app = app

    def _cmd_backup_completo(self) -> None:
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
                       "personajes", "loras", "plantillas", "paletas"))
            tam_kb = os.path.getsize(archivo) / 1024
            mensaje = (
                f"Backup guardado correctamente.\n\n"
                f"Archivo: {os.path.basename(archivo)}\n"
                f"Tamaño: {tam_kb:.1f} KB\n"
                f"Total entradas: {tot}\n\n"
                f"  - Historial:  {len(backup['historial'])}\n"
                f"  - Favoritos:  {len(backup['favoritos'])}\n"
                f"  - Estrellas:  {len(backup['estrellas'])}\n"
                f"  - Personajes: {len(backup['personajes'])}\n"
                f"  - LoRAs:      {len(backup['loras'])}\n"
                f"  - Plantillas: {len(backup['plantillas'])}\n"
                f"  - Paletas:    {len(backup['paletas'])}"
            )
            messagebox.showinfo(tr("Backup completo"), mensaje, parent=self.app)
            self.app.dialogs.set_estado(tr('💾 Backup guardado ({0} entradas)').format(tot), "#2ecc71")
        except Exception as e:
            self.app.dialogs.set_estado(tr('❌ Error en backup: {0}').format(e), "#e74c3c")
            messagebox.showerror(tr("Error"), tr('No se pudo guardar el backup:\n{0}').format(e), parent=self.app)

    def _construir_backup(self) -> dict:
        """Construye el diccionario con todos los datos del usuario."""
        return {
            "version": VERSION,
            "fecha_backup": datetime.datetime.now().isoformat(),
            "historial":   self.app.store.historial or [],
            "favoritos":   self.app.store.favoritos or [],
            "estrellas":   self.app.store.estrellas or [],
            "personajes":  self.app.store.personajes or [],
            "loras":       self.app.store.loras or [],
            "plantillas":  self.app.store.plantillas or [],
            "paletas":     self.app.store.paletas or [],
            "preferencias": self.app.store.cargar_preferencias() or {},
        }

    def _cmd_restore_completo(self) -> None:
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
                messagebox.showerror(tr("Backup inválido"),
                                     tr("El archivo no parece un backup de G-Prompt Studio "
                                     "(falta el campo 'version')."),
                                     parent=self.app)
                return

            tot_actual = (len(self.app.store.historial or []) +
                          len(self.app.store.favoritos or []) +
                          len(self.app.store.estrellas or []) +
                          len(self.app.store.personajes or []) +
                          len(self.app.store.loras or []) +
                          len(self.app.store.plantillas or []) +
                          len(self.app.store.paletas or []))
            tot_backup = (len(backup.get("historial", [])) +
                          len(backup.get("favoritos", [])) +
                          len(backup.get("estrellas", [])) +
                          len(backup.get("personajes", [])) +
                          len(backup.get("loras", [])) +
                          len(backup.get("plantillas", [])) +
                          len(backup.get("paletas", [])))

            # Formatear fecha del backup en algo legible
            fecha_backup_raw = backup.get("fecha_backup", "")
            try:
                fecha_backup = (
                    datetime.datetime.fromisoformat(fecha_backup_raw)
                                     .strftime("%Y-%m-%d %H:%M")
                )
            except Exception:
                fecha_backup = fecha_backup_raw or "desconocida"

            if not messagebox.askyesno(
                tr("Confirmar restauración"),
                tr('Vas a SOBRESCRIBIR todos tus datos actuales con el backup.\n\nDatos actuales: {0} entradas\nBackup a restaurar: {1} entradas\nFecha del backup: {2}\n\nG-Prompt guardará automáticamente un backup de seguridad de tus datos ACTUALES antes de sobrescribir, así puedes volver atrás si te equivocas.\n\n¿Continuar?').format(tot_actual, tot_backup, fecha_backup),
                parent=self.app,
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
                    tr("Error"),
                    tr('No se pudo crear el backup de seguridad pre-restore:\n{0}\n\nRestauración CANCELADA para no arriesgar tus datos actuales.').format(e),
                    parent=self.app,
                )
                return

            # ── RESTAURAR ──
            # Validación de tipos: un backup editado/corrupto podría traer
            # un string o dict donde se espera una lista de dicts, lo que
            # corrompería el store y crashearía la UI más adelante.
            def _lista_valida(clave: str) -> list:
                valor = backup.get(clave, [])
                if not isinstance(valor, list):
                    logger.warning(f"Backup: '{clave}' no es una lista, se ignora")
                    return []
                return [it for it in valor if isinstance(it, dict)]

            self.app.store.historial   = _lista_valida("historial")
            self.app.store.favoritos   = _lista_valida("favoritos")
            self.app.store.estrellas   = _lista_valida("estrellas")
            self.app.store.personajes  = _lista_valida("personajes")
            self.app.store.loras       = _lista_valida("loras")
            self.app.store.plantillas  = _lista_valida("plantillas")
            # paletas: solo si el backup las trae (compat con backups viejos
            # que no incluían esta colección — no pisamos las actuales).
            if "paletas" in backup:
                self.app.store.paletas = _lista_valida("paletas")

            cols_restaurar = ["historial", "favoritos", "estrellas",
                              "personajes", "loras", "plantillas"]
            if "paletas" in backup:
                cols_restaurar.append("paletas")
            for col in cols_restaurar:
                self.app.store._guardar(col)

            prefs_backup = backup.get("preferencias")
            if isinstance(prefs_backup, dict) and prefs_backup:
                self.app.store.guardar_preferencias(prefs_backup)

            self.app.actualizar_combo_personajes()
            self.app.actualizar_combo_loras()
            if hasattr(self.app, "actualizar_combo_plantillas"):
                self.app.actualizar_combo_plantillas()

            messagebox.showinfo(
                tr("Restauración completada"),
                tr('Backup restaurado ({0} entradas).\n\nTus datos anteriores se guardaron en:\n{1}\n\nSi te has equivocado, puedes restaurar ese archivo.').format(tot_backup, pre_path),
                parent=self.app,
            )
            self.app.dialogs.set_estado(tr('✅ Backup restaurado ({0} entradas)').format(tot_backup), "#2ecc71")
        except Exception as e:
            self.app.dialogs.set_estado(tr('❌ Error al restaurar: {0}').format(e), "#e74c3c")
            messagebox.showerror(tr("Error"), tr('No se pudo restaurar el backup:\n{0}').format(e), parent=self.app)

    def _cmd_exportar_csv(self) -> None:
        """Selector previo de qué exportar: historial / favoritos / estrellas /
        todos juntos. Después abre filedialog y vuelca a CSV.
        """
        # Pre-comprobación: ¿hay algo que exportar?
        hist  = self.app.store.historial or []
        favs  = self.app.store.favoritos or []
        stars = self.app.store.estrellas or []
        if not (hist or favs or stars):
            return self.app.dialogs.set_estado(
                tr("⚠️ No hay nada que exportar (historial/favoritos/estrellas vacíos)."),
                "#e67e22",
            )

        # ── Selector ──
        from modules.gprompt_window import GPromptWindow
        sel = GPromptWindow(self.app)
        sel.title(tr("📊 Exportar a CSV"))
        sel.geometry("420x300")
        sel.transient(self.app)

        ctk.CTkLabel(sel, text=tr("📊 Exportar a CSV"),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 6))
        ctk.CTkLabel(sel, text=tr("¿Qué quieres exportar?"),
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
                messagebox.showwarning(tr("Sin selección"),
                                       tr("Marca al menos una colección."),
                                       parent=sel)
                return
            sel.destroy()
            self._exportar_csv_ejecutar(seleccion)

        ctk.CTkButton(sel, text=tr("▶ Exportar"), width=160, height=34,
                      fg_color="#1a7a3c", command=_lanzar).pack(pady=(14, 4))
        ctk.CTkButton(sel, text=tr("Cancelar"), width=100, height=28,
                      fg_color="#444", hover_color="#555",
                      command=sel.destroy).pack(pady=2)

    def _exportar_csv_ejecutar(self, colecciones: list) -> None:
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
                        w.writerow([_csv_safe(v) for v in (
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
                        )])
                        n += 1
            self.app.dialogs.set_estado(tr('💾 {0} filas exportadas a CSV').format(n), "#2ecc71")
            messagebox.showinfo(
                tr("Exportación completada"),
                f"Exportadas {n} filas desde {len(colecciones)} colección(es) a:\n{archivo}",
                parent=self.app,
            )
        except Exception as e:
            self.app.dialogs.set_estado(tr('❌ Error al exportar: {0}').format(e), "#e74c3c")
            messagebox.showerror(tr("Error"), tr('No se pudo exportar:\n{0}').format(e), parent=self.app)

    def _cmd_export_cli(self) -> None:
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
        import json as _json
        import re
        actual = self.app.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.app.dialogs.set_estado(tr("⚠️ Genera un prompt primero."), "#e67e22")

        ratio = self.app.ratio_var.get() or "1:1"
        pos = self.app.extraer_positive() or actual
        neg = self.app.extraer_negative() or ""

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
            "model_target": getattr(self.app, "combo_modelo_imagen", None).get() if hasattr(self.app, "combo_modelo_imagen") else "unknown",
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

        # ── Ventana con filtro por modo + cards ───────────────────────

        vent = GPromptWindow(self.app)
        vent.title(tr("📤 Export CLI — múltiples formatos"))
        vent.geometry("820x680")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("📤 Export en múltiples formatos"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent,
                     text=tr("Filtra por modo y pulsa 📋 en la plataforma deseada."),
                     font=ctk.CTkFont(size=10), text_color="#888888").pack(pady=(0, 8))

        # Formatos: (nombre, contenido, color, modo)
        formatos = [
            ("🎨 Midjourney v6",     mj,            "#1a7a3c", "imagen"),
            ("🌸 Niji 6 (anime)",    niji,          "#a64aa6", "imagen"),
            ("⚡ FLUX Dev",          flux_dev,      "#7c3aed", "imagen"),
            ("⚡ FLUX Schnell",      flux_schnell,  "#9333ea", "imagen"),
            ("🤖 Grok / X",          grok,          "#1c1c1c", "imagen"),
            ("🖌 DALL-E 3",          dalle,         "#10a37f", "imagen"),
            ("✨ Leonardo.AI",
             (f"POS: {leonardo_pos}\n\nNEG: {leonardo_neg}" if leonardo_neg else leonardo_pos),
             "#7b3aed", "imagen"),
            ("📝 Ideogram",          ideogram,      "#d97706", "imagen"),
            ("⚡ ComfyUI",           comfyui,       "#0891b2", "imagen"),
            ("🖥 Automatic1111",     a1111,         "#dc2626", "imagen"),
            ("🎯 SD genérico",       sd,            "#475569", "imagen"),
            ("🎬 Kling",             kling_prompt,  "#f59e0b", "video"),
            ("🎬 Seedance",          seedance_prompt,"#eab308", "video"),
            ("🎵 Suno",              suno_prompt,   "#ec4899", "audio"),
            ("📦 JSON (API)",        json_payload,  "#6366f1", "todos"),
        ]

        # Filtro arriba
        filtro_row = ctk.CTkFrame(vent, fg_color="transparent")
        filtro_row.pack(fill="x", padx=12, pady=(0, 4))
        ctk.CTkLabel(filtro_row, text=tr("Modo:")).pack(side="left", padx=(0, 8))
        modo_activo = self.app.modo_var.get() if hasattr(self.app, "modo_var") else "imagen"
        valor_inicial = {
            "imagen": "🖼 Imagen", "video": "🎬 Vídeo", "audio": "🎵 Audio"
        }.get(modo_activo, "🖼 Imagen")
        filtro_var = ctk.StringVar(value=valor_inicial)
        seg = ctk.CTkSegmentedButton(
            filtro_row,
            values=["🖼 Imagen", "🎬 Vídeo", "🎵 Audio", "📦 Todos"],
            variable=filtro_var,
            command=lambda _v: _render(),
        )
        seg.pack(side="left")
        lbl_count = ctk.CTkLabel(filtro_row, text="", font=ctk.CTkFont(size=10),
                                  text_color="#888")
        lbl_count.pack(side="left", padx=10)

        # Área scrollable con las cards
        scroll = ctk.CTkScrollableFrame(vent, fg_color=("#f3f4f6"
                                                        if ctk.get_appearance_mode().lower() == "light"
                                                        else "#0d1117"))
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        is_lt = ctk.get_appearance_mode().lower() == "light"
        bg_card = "#ffffff" if is_lt else "#1a1a2e"
        text_main = "#111827" if is_lt else "#e5e7eb"

        def _make_copy(c, n, color):
            def _copiar():
                pyperclip.copy(c)
                self.app.dialogs.set_estado(tr('📋 {0} copiado').format(n), "#2ecc71")
                if hasattr(self.app, "show_toast"):
                    try:
                        self.app.show_toast(tr('📋 Copiado: {0}').format(n), color, 1800)
                    except Exception as _e:
                        logger.debug(f"[silent] {_e}")
            return _copiar

        def _render():
            for w in scroll.winfo_children():
                w.destroy()
            label = filtro_var.get()
            modo_sel = {
                "🖼 Imagen": "imagen",
                "🎬 Vídeo":  "video",
                "🎵 Audio":  "audio",
                "📦 Todos":  None,
            }.get(label)

            filtrados = [f for f in formatos
                         if modo_sel is None or f[3] in (modo_sel, "todos")]
            lbl_count.configure(text=tr('{0} formatos disponibles').format(len(filtrados)))

            if not filtrados:
                ctk.CTkLabel(scroll, text=tr("(sin formatos para este modo)"),
                             text_color="#888").pack(pady=20)
                return

            for nombre, contenido, color, modo_fmt in filtrados:
                card = ctk.CTkFrame(scroll, fg_color=bg_card, corner_radius=8)
                card.pack(fill="x", padx=4, pady=4)

                hdr = ctk.CTkFrame(card, fg_color="transparent")
                hdr.pack(fill="x", padx=12, pady=(8, 4))
                ctk.CTkLabel(hdr, text=nombre,
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=text_main).pack(side="left")
                ctk.CTkLabel(hdr, text=f"{len(contenido)} chars",
                             font=ctk.CTkFont(size=10),
                             text_color="#888").pack(side="left", padx=10)
                ctk.CTkButton(hdr, text=tr("📋 Copiar"), width=100, height=26,
                              fg_color=color,
                              font=ctk.CTkFont(size=10, weight="bold"),
                              command=_make_copy(contenido, nombre, color)
                              ).pack(side="right")

                txt = ctk.CTkTextbox(card,
                                     font=ctk.CTkFont(family="Consolas", size=10),
                                     wrap="word", height=110,
                                     fg_color=("#f9fafb" if is_lt else "#0f172a"),
                                     text_color=text_main)
                txt.pack(fill="x", padx=12, pady=(0, 10))
                txt.insert("1.0", contenido)
                txt.configure(state="disabled")

        _render()

        # ── Botón Copiar Todos (solo del filtro actual) ──
        def _copiar_filtrados():
            label = filtro_var.get()
            modo_sel = {
                "🖼 Imagen": "imagen", "🎬 Vídeo": "video",
                "🎵 Audio": "audio", "📦 Todos": None
            }.get(label)
            filtrados = [(n, c) for n, c, _col, m in formatos
                         if modo_sel is None or m in (modo_sel, "todos")]
            todo = "\n".join([f"===== {nom} =====\n{cont}\n" for nom, cont in filtrados])
            pyperclip.copy(todo)
            self.app.dialogs.set_estado(tr('📋 {0} formatos copiados al portapapeles').format(len(filtrados)),
                            "#2ecc71")

        ctk.CTkButton(vent, text=tr("📋 Copiar todos los del filtro actual"),
                      width=280, height=34, fg_color="#0f172a", hover_color="#1e293b",
                      text_color="#e2e8f0",
                      command=_copiar_filtrados).pack(pady=(4, 12))

    def _cmd_busqueda_global(self) -> None:
        """Búsqueda global con debounce 250ms + filtro por tipo.

        Antes: `ent.bind("<KeyRelease>", buscar)` disparaba la búsqueda
        en 8 colecciones con cada tecla → notable lag con catálogos grandes.
        Sin filtro por tipo → mucho ruido cuando solo buscas en una
        colección concreta.
        """
        vent = GPromptWindow(self.app)
        vent.title(tr("🔎 Búsqueda global"))
        vent.geometry("780x680")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("🔎 Búsqueda en todas las colecciones"),
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(10, 3))

        f_search = ctk.CTkFrame(vent, fg_color="transparent")
        f_search.pack(fill="x", padx=15, pady=(0, 4))
        ent = ctk.CTkEntry(f_search,
                            placeholder_text=tr("Escribe lo que buscas (ej: 'cyberpunk', 'fox', 'masterpiece')..."),
                            width=600, height=32, font=ctk.CTkFont(size=12))
        ent.pack(side="left", fill="x", expand=True)
        ent.focus_set()

        # ── Filtros por tipo (checkboxes) ──
        # Default: todos los tipos activos. Al desmarcar, esa colección
        # se omite de la búsqueda → menos ruido y más rapidez.
        filtros = {
            "historial":  ctk.BooleanVar(value=True),
            "favoritos":  ctk.BooleanVar(value=True),
            "estrellas":  ctk.BooleanVar(value=True),
            "seeds":      ctk.BooleanVar(value=True),
            "snippets":   ctk.BooleanVar(value=True),
            "formulas":   ctk.BooleanVar(value=True),
            "personajes": ctk.BooleanVar(value=True),
            "loras":      ctk.BooleanVar(value=True),
        }
        filtro_labels = [
            ("historial",  "📋 Historial"),
            ("favoritos",  "⭐ Favoritos"),
            ("estrellas",  "🌟 Estrellas"),
            ("seeds",      "💎 Seeds"),
            ("snippets",   "✂️ Snippets"),
            ("formulas",   "🧪 Fórmulas"),
            ("personajes", "🧑 Personajes"),
            ("loras",      "🔗 LoRAs"),
        ]

        f_filtros = ctk.CTkFrame(vent, fg_color="transparent")
        f_filtros.pack(fill="x", padx=15, pady=(2, 6))
        ctk.CTkLabel(f_filtros, text=tr("Filtrar:"),
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#888").pack(side="left", padx=(0, 6))
        for key, label in filtro_labels:
            ctk.CTkCheckBox(f_filtros, text=label, variable=filtros[key],
                            font=ctk.CTkFont(size=10), width=20,
                            command=lambda: _disparar_busqueda()
                            ).pack(side="left", padx=4)

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        def buscar():
            for w in scroll.winfo_children(): w.destroy()
            termino = ent.get().strip().lower()
            if not termino or len(termino) < 2:
                ctk.CTkLabel(scroll, text=tr("Escribe al menos 2 caracteres para buscar."),
                             font=ctk.CTkFont(size=11), text_color="#666666").pack(pady=20)
                return

            resultados = []
            prefs = self.app.store.cargar_preferencias()

            if filtros["historial"].get():
                for item in (self.app.store.historial or []):
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
                        resultados.append(("📋 Historial", item.get("fecha", "") if isinstance(item, dict) else "", contenido[:200], lambda c=contenido: self.app.dialogs.actualizar_salida(c)))

            if filtros["favoritos"].get():
                for item in (self.app.store.favoritos or []):
                    if isinstance(item, dict):
                        txt = item.get("contenido", "") + " " + item.get("nombre", "")
                    else:
                        txt = str(item)
                    if termino in txt.lower():
                        contenido = item.get("contenido", "") if isinstance(item, dict) else str(item)
                        nombre = item.get("nombre", "") if isinstance(item, dict) else ""
                        resultados.append(("⭐ Favorito", nombre, contenido[:200], lambda c=contenido: self.app.dialogs.actualizar_salida(c)))

            if filtros["estrellas"].get():
                for item in (self.app.store.estrellas or []):
                    if isinstance(item, dict):
                        txt = item.get("contenido", "") + " " + item.get("nombre", "")
                    else:
                        txt = str(item)
                    if termino in txt.lower():
                        contenido = item.get("contenido", "") if isinstance(item, dict) else str(item)
                        nombre = item.get("nombre", "") if isinstance(item, dict) else ""
                        resultados.append(("🌟 Estrella", nombre, contenido[:200], lambda c=contenido: self.app.dialogs.actualizar_salida(c)))

            if filtros["seeds"].get():
                for s in (prefs.get("seeds_favoritos") or []):
                    txt = " ".join([s.get("nombre", ""), str(s.get("estilos", [])), s.get("plataforma", ""),
                                     s.get("modelo_img", ""), s.get("modelo_vid", "")]).lower()
                    if termino in txt:
                        desc = f"Modelo: {s.get('modelo_img') or s.get('modelo_vid', '')}, Estilos: {', '.join(s.get('estilos', [])[:3])}"
                        resultados.append(("💎 Seed", s.get("nombre", "?"), desc, lambda seed=s: self.app._aplicar_seed(seed)))

            if filtros["snippets"].get():
                for s in (prefs.get("snippets") or []):
                    txt = (s.get("nombre", "") + " " + s.get("tags", "")).lower()
                    if termino in txt:
                        resultados.append(("✂️ Snippet", s.get("nombre", "?"), s.get("tags", "")[:200],
                                            lambda tags=s.get("tags", ""): self.app._aplicar_atajo_tags(tags)))

            if filtros["formulas"].get():
                for f in (prefs.get("formulas") or []):
                    txt = (f.get("nombre", "") + " " + f.get("positive", "") + " " + f.get("negative", "")).lower()
                    if termino in txt:
                        pos_neg = f.get("positive", "")[:200]
                        def _cargar_formula(ff=f):
                            txt_form = f"POSITIVE PROMPT: {ff.get('positive', '')}"
                            if ff.get('negative'):
                                txt_form += f"\nNEGATIVE PROMPT: {ff.get('negative')}"
                            self.app.dialogs.actualizar_salida(txt_form)
                        resultados.append(("🧪 Fórmula", f.get("nombre", "?"), pos_neg, _cargar_formula))

            if filtros["personajes"].get():
                for p in (self.app.store.personajes or []):
                    txt = (p.get("nombre", "") + " " + p.get("rasgos", "")).lower()
                    if termino in txt:
                        resultados.append(("🧑 Personaje", p.get("nombre", "?"), p.get("rasgos", "")[:200],
                                            lambda nombre=p.get("nombre", ""): self.app.combo_personaje.set(nombre) if hasattr(self.app, 'combo_personaje') else None))

            if filtros["loras"].get():
                for l in (self.app.store.loras or []):
                    txt = (l.get("nombre", "") + " " + l.get("descripcion", "")).lower()
                    if termino in txt:
                        resultados.append(("🔗 LoRA", l.get("nombre", "?"), l.get("descripcion", "")[:200],
                                            lambda nombre=l.get("nombre", ""): self.app.combo_lora.set(nombre) if hasattr(self.app, 'combo_lora') else None))

            if not resultados:
                # ¿Por qué no hay resultados? Distinguir entre "filtros restrictivos"
                # y "el término no existe en ninguna colección activa".
                tipos_activos = sum(1 for v in filtros.values() if v.get())
                if tipos_activos == 0:
                    msg = "⚠️ No hay tipos seleccionados. Marca al menos uno."
                elif tipos_activos < len(filtros):
                    msg = f"Sin resultados para '{termino}' en los {tipos_activos} tipo(s) seleccionados."
                else:
                    msg = f"Sin resultados para '{termino}'"
                ctk.CTkLabel(scroll, text=msg,
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

                btn = ctk.CTkButton(card, text=tr("✅ Aplicar"), width=90, height=22, fg_color="#1a7a3c",
                                      font=ctk.CTkFont(size=10),
                                      command=lambda a=accion: (a(), vent.destroy(), self.app.dialogs.set_estado(tr('✅ Aplicado: {0}').format(nombre or tipo), "#2ecc71")))
                btn.pack(anchor="e", padx=8, pady=(0, 4))

        # Debounce: cada tecla cancela el `after` pendiente y reprograma.
        # 250ms es suficiente para no disparar 8-collection-scan por cada letra.
        _busqueda_pendiente = {"after_id": None}
        def _disparar_busqueda(_e=None):
            if _busqueda_pendiente["after_id"]:
                try: vent.after_cancel(_busqueda_pendiente["after_id"])
                except Exception as _e2: logger.debug(f"[silent] {_e2}")
            _busqueda_pendiente["after_id"] = vent.after(250, buscar)
        ent.bind("<KeyRelease>", _disparar_busqueda)

    def _close_menu_if_open(self, event=None) -> None:
        """Cierra el menú desplegable si está abierto."""
        if hasattr(self.app, '_menu_activo') and self.app._menu_activo:
            try:
                self.app._menu_activo.destroy()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            self.app._menu_activo = None
