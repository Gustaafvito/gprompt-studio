"""
Arquitecto de Prompts v1.0 — Ventanas secundarias.
Personajes, LoRAs, Batch, Historial, Favoritos.
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
import datetime
import logging
import threading
from pathlib import Path

from workers import contar_tokens_aprox

logger = logging.getLogger(__name__)


def _is_light():
    return ctk.get_appearance_mode().lower() == "light"


def _card_colors():
    """Devuelve colores para cards según tema actual."""
    light = _is_light()
    return {
        "card_bg":      "#f0f0f0" if light else "#1a1a2e",
        "card_hdr":     "#e0e0e0" if light else "#2a1a3a",
        "card_text":    "#1f2937" if light else "#cccccc",
        "card_text2":   "#4b5563" if light else "#999999",
        "card_hdr_text": "#111827" if light else "#e5e7eb",
        "empty_text":   "#6b7280" if light else "#666666",
        "label_main":   "#111827" if light else "#e5e7eb",
        "btn_use":      "#15803d" if light else "#1a4a2a",
        "btn_use_hov":  "#166534" if light else "#0f3320",
        "btn_del":      "#dc2626" if light else "#6a1a1a",
        "btn_del_hov":  "#b91c1c" if light else "#4a0f0f",
        "btn_bg":       "#2563eb" if light else "#2a4a6a",
        "btn_bg_hov":   "#1d4ed8" if light else "#1a3a5a",
    }


# PERSONAJES

def abrir_personajes(app):
    cc = _card_colors()
    ventana = ctk.CTkToplevel(app)
    ventana.title("🧑 Gestor de Personajes")
    ventana.geometry("720x580")
    ventana.grab_set()

    ctk.CTkLabel(ventana, text="🧑 Personajes Guardados",
                 font=ctk.CTkFont(size=18, weight="bold"),
                 text_color=cc["label_main"]).pack(pady=12)
    ctk.CTkLabel(ventana,
                 text="Los personajes se insertan automáticamente en el prompt al seleccionarlos.",
                 font=ctk.CTkFont(size=11), text_color=cc["label_main"]).pack(pady=(0, 8))

    frame_nuevo = ctk.CTkFrame(ventana)
    frame_nuevo.pack(fill="x", padx=15, pady=(0, 8))

    ctk.CTkLabel(frame_nuevo, text="Nombre:", font=ctk.CTkFont(weight="bold"),
                 text_color=cc["label_main"]).pack(side="left", padx=10, pady=8)
    entry_nombre = ctk.CTkEntry(frame_nuevo, width=160, placeholder_text="ej: Luna, Detective...")
    entry_nombre.pack(side="left", padx=5)

    ctk.CTkLabel(frame_nuevo, text="Descripción:", font=ctk.CTkFont(weight="bold"),
                 text_color=cc["label_main"]).pack(side="left", padx=(12, 5))
    entry_desc = ctk.CTkEntry(frame_nuevo, width=260,
                               placeholder_text="ej: young woman, silver hair, blue eyes...")
    entry_desc.pack(side="left", padx=5)

    def guardar():
        nombre = entry_nombre.get().strip()
        desc = entry_desc.get().strip()
        if not nombre or not desc:
            messagebox.showwarning("Faltan datos", "Rellena nombre y descripción.", parent=ventana)
            return
        existia = app.store.guardar_personaje(nombre, desc)
        if existia:
            if not messagebox.askyesno("Ya existe", f"¿Sobreescribir '{nombre}'?", parent=ventana):
                return
        app.actualizar_combo_personajes()
        entry_nombre.delete(0, "end")
        entry_desc.delete(0, "end")
        refrescar()
        app.set_estado(f"🧑 Personaje '{nombre}' guardado.", "#2ecc71")

    ctk.CTkButton(frame_nuevo, text="💾 Guardar", width=90, height=30,
                  fg_color="#1a7a3c", hover_color="#145e2d", command=guardar).pack(side="left", padx=8)

    frame_lista = ctk.CTkScrollableFrame(ventana)
    frame_lista.pack(fill="both", expand=True, padx=15, pady=5)

    def refrescar():
        cc = _card_colors()
        for w in frame_lista.winfo_children():
            w.destroy()
        if not app.store.personajes:
            ctk.CTkLabel(frame_lista, text="No hay personajes guardados aún.",
                         text_color=cc["empty_text"]).pack(pady=20)
            return
        for idx, p in enumerate(app.store.personajes):
            card = ctk.CTkFrame(frame_lista, fg_color=cc["card_bg"], corner_radius=8)
            card.pack(fill="x", pady=4, padx=5)
            hdr = ctk.CTkFrame(card, fg_color=cc["card_hdr"], corner_radius=6, height=28)
            hdr.pack(fill="x", padx=5, pady=(5, 2))
            hdr.pack_propagate(False)
            ctk.CTkLabel(hdr, text=f"  🧑 {p['nombre']}",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=cc["card_hdr_text"]).pack(side="left", padx=8)
            ctk.CTkLabel(card, text=p["descripcion"], wraplength=620, justify="left",
                         font=ctk.CTkFont(size=12), text_color=cc["card_text"]).pack(padx=10, pady=(3, 5), anchor="w")
            btn_row = ctk.CTkFrame(card, fg_color=cc["card_bg"])
            btn_row.pack(fill="x", padx=10, pady=(0, 6))

            def usar(n=p["nombre"]):
                app.combo_personaje.set(n)
                ventana.destroy()
                app.set_estado(f"🧑 Personaje activo: {n}", "#2ecc71")

            def borrar(i=idx):
                if messagebox.askyesno("Confirmar", f"¿Borrar '{app.store.personajes[i]['nombre']}'?", parent=ventana):
                    app.store.borrar_personaje(i)
                    app.actualizar_combo_personajes()
                    refrescar()

            ctk.CTkButton(btn_row, text="✅ Usar", width=80, height=26,
                          fg_color=cc["btn_use"], hover_color=cc["btn_use_hov"], command=usar).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text="🗑 Borrar", width=88, height=26,
                          fg_color=cc["btn_del"], hover_color=cc["btn_del_hov"], command=borrar).pack(side="left", padx=2)
    refrescar()


# LORAS

def abrir_loras(app):
    cc = _card_colors()
    ventana = ctk.CTkToplevel(app)
    ventana.title("🔗 Gestor de LoRAs")
    ventana.geometry("780x580")
    ventana.grab_set()

    ctk.CTkLabel(ventana, text="🔗 LoRAs Guardados",
                 font=ctk.CTkFont(size=18, weight="bold"),
                 text_color=cc["label_main"]).pack(pady=12)
    ctk.CTkLabel(ventana,
                 text="Los LoRAs insertan su trigger word al inicio del prompt automáticamente.",
                 font=ctk.CTkFont(size=11), text_color=cc["label_main"]).pack(pady=(0, 8))

    frame_nuevo = ctk.CTkFrame(ventana)
    frame_nuevo.pack(fill="x", padx=15, pady=(0, 8))

    ctk.CTkLabel(frame_nuevo, text="Nombre:", font=ctk.CTkFont(weight="bold"),
                 text_color=cc["label_main"]).pack(side="left", padx=10, pady=8)
    entry_nombre = ctk.CTkEntry(frame_nuevo, width=130, placeholder_text="ej: Detail Enhancer")
    entry_nombre.pack(side="left", padx=5)

    ctk.CTkLabel(frame_nuevo, text="Trigger:", font=ctk.CTkFont(weight="bold"),
                 text_color=cc["label_main"]).pack(side="left", padx=(10, 5))
    entry_trigger = ctk.CTkEntry(frame_nuevo, width=160, placeholder_text="ej: add_detail")
    entry_trigger.pack(side="left", padx=5)

    ctk.CTkLabel(frame_nuevo, text="Familia:", font=ctk.CTkFont(weight="bold"),
                 text_color=cc["label_main"]).pack(side="left", padx=(10, 5))
    combo_familia = ctk.CTkComboBox(frame_nuevo, width=110,
                                      values=["—", "SDXL", "SD15", "Pony", "Illustrious", "Flux", "SD3.5", "Z Image", "Otra"])
    combo_familia.set("—")
    combo_familia.pack(side="left", padx=5)

    ctk.CTkLabel(frame_nuevo, text="Nota:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(10, 5))
    entry_nota = ctk.CTkEntry(frame_nuevo, width=120, placeholder_text="opcional")
    entry_nota.pack(side="left", padx=5)

    def guardar():
        nombre  = entry_nombre.get().strip()
        trigger = entry_trigger.get().strip()
        nota    = entry_nota.get().strip()
        familia = combo_familia.get().strip()
        if familia in ("—", ""): familia = ""
        if not nombre or not trigger:
            messagebox.showwarning("Faltan datos", "Rellena nombre y trigger word.", parent=ventana)
            return
        existia = app.store.guardar_lora(nombre, trigger, nota, familia)
        if existia:
            if not messagebox.askyesno("Ya existe", f"¿Sobreescribir '{nombre}'?", parent=ventana):
                return
        app.actualizar_combo_loras()
        entry_nombre.delete(0, "end")
        entry_trigger.delete(0, "end")
        entry_nota.delete(0, "end")
        combo_familia.set("—")
        refrescar()
        app.set_estado(f"🔗 LoRA '{nombre}' guardado.", "#9b59b6")

    ctk.CTkButton(frame_nuevo, text="💾 Guardar", width=90, height=30,
                  fg_color="#5b2c8e", hover_color="#3d1a6a", command=guardar).pack(side="left", padx=8)

    frame_lista = ctk.CTkScrollableFrame(ventana)
    frame_lista.pack(fill="both", expand=True, padx=15, pady=5)

    def refrescar():
        cc = _card_colors()
        for w in frame_lista.winfo_children():
            w.destroy()
        if not app.store.loras:
            ctk.CTkLabel(frame_lista,
                         text="No hay LoRAs guardados aún.\n\n"
                              "Añade el nombre del LoRA y su trigger word\n"
                              "(la palabra clave que activa el LoRA en SeaArt, CivitAI, etc).",
                         text_color=cc["empty_text"], justify="center").pack(pady=20)
            return
        for idx, l in enumerate(app.store.loras):
            card = ctk.CTkFrame(frame_lista, fg_color=cc["card_bg"], corner_radius=8)
            card.pack(fill="x", pady=4, padx=5)
            hdr = ctk.CTkFrame(card, fg_color=cc["card_hdr"], corner_radius=6, height=28)
            hdr.pack(fill="x", padx=5, pady=(5, 2))
            hdr.pack_propagate(False)
            familia = l.get("familia", "")
            badge_familia = f"  [{familia}]" if familia else ""
            ctk.CTkLabel(hdr, text=f"  🔗 {l['nombre']}{badge_familia}   →   trigger: \"{l['trigger']}\"",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=cc["card_hdr_text"]).pack(side="left", padx=8)
            nota = l.get("descripcion", "")
            if nota:
                ctk.CTkLabel(card, text=nota, wraplength=700, justify="left",
                             font=ctk.CTkFont(size=11), text_color=cc["card_text2"]).pack(padx=10, pady=(2, 3), anchor="w")
            btn_row = ctk.CTkFrame(card, fg_color=cc["card_bg"])
            btn_row.pack(fill="x", padx=10, pady=(0, 6))

            def usar(n=l["nombre"]):
                app.combo_lora.set(n)
                ventana.destroy()
                app.set_estado(f"🔗 LoRA activo: {n}", "#9b59b6")

            def borrar(i=idx):
                if messagebox.askyesno("Confirmar", f"¿Borrar LoRA '{app.store.loras[i]['nombre']}'?", parent=ventana):
                    app.store.borrar_lora(i)
                    app.actualizar_combo_loras()
                    refrescar()

            ctk.CTkButton(btn_row, text="✅ Usar", width=80, height=26,
                          fg_color="#7c3aed" if _is_light() else "#3a1a5a",
                          hover_color="#6d28d9" if _is_light() else "#2a0f4a", command=usar).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text="🗑 Borrar", width=88, height=26,
                          fg_color="#dc2626" if _is_light() else "#6a1a1a",
                          hover_color="#b91c1c" if _is_light() else "#4a0f0f", command=borrar).pack(side="left", padx=2)
    refrescar()


# BATCH

def abrir_batch(app):
    cc = _card_colors()
    ventana = ctk.CTkToplevel(app)
    ventana.title("📦 Generación Batch")
    ventana.geometry("850x750")
    ventana.grab_set()

    ctk.CTkLabel(ventana, text="📦 Generación Batch",
                 font=ctk.CTkFont(size=18, weight="bold")).pack(pady=12)

    batch_modo_var = ctk.StringVar(value="auto")
    frame_bmodo = ctk.CTkFrame(ventana)
    frame_bmodo.pack(fill="x", padx=15, pady=(0, 8))
    ctk.CTkLabel(frame_bmodo, text="Modo:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=12, pady=10)
    ctk.CTkRadioButton(frame_bmodo, text="🔁 Auto (1 idea → N prompts)",
                       variable=batch_modo_var, value="auto",
                       command=lambda: actualizar_panel()).pack(side="left", padx=12)
    ctk.CTkRadioButton(frame_bmodo, text="📋 Lista (N ideas → N prompts)",
                       variable=batch_modo_var, value="lista",
                       command=lambda: actualizar_panel()).pack(side="left", padx=12)

    frame_panel = ctk.CTkFrame(ventana)
    frame_panel.pack(fill="x", padx=15, pady=(0, 8))

    batch_n_var = ctk.IntVar(value=5)
    entry_bidea = [None]
    entry_blista = [None]

    def actualizar_panel():
        for w in frame_panel.winfo_children():
            w.destroy()
        if batch_modo_var.get() == "auto":
            ctk.CTkLabel(frame_panel, text="Idea base:", font=ctk.CTkFont(weight="bold")).pack(
                anchor="w", padx=12, pady=(8, 2))
            entry_bidea[0] = ctk.CTkTextbox(frame_panel, height=55, font=ctk.CTkFont(size=13))
            entry_bidea[0].pack(fill="x", padx=12, pady=(0, 6))
            idea_actual = app.txt_idea.get("1.0", "end").strip()
            if idea_actual:
                entry_bidea[0].insert("1.0", idea_actual)
            frame_bn = ctk.CTkFrame(frame_panel, fg_color="transparent")
            frame_bn.pack(fill="x", padx=12, pady=(0, 8))
            ctk.CTkLabel(frame_bn, text="Número de prompts:", font=ctk.CTkFont(weight="bold")).pack(side="left")
            lbl_bn = ctk.CTkLabel(frame_bn, text=str(batch_n_var.get()),
                                   font=ctk.CTkFont(size=14, weight="bold"), text_color="#3498db", width=28)
            ctk.CTkSlider(frame_bn, from_=2, to=10, number_of_steps=8, variable=batch_n_var,
                          command=lambda v: lbl_bn.configure(text=f"{int(v)}")).pack(
                side="left", padx=10, fill="x", expand=True)
            lbl_bn.pack(side="left")
        else:
            ctk.CTkLabel(frame_panel, text="Lista de ideas (una por línea, máx 10):",
                         font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=12, pady=(8, 2))
            entry_blista[0] = ctk.CTkTextbox(frame_panel, height=140, font=ctk.CTkFont(size=13))
            entry_blista[0].pack(fill="x", padx=12, pady=(0, 8))
            entry_blista[0].insert("1.0",
                "chica anime en playa al atardecer\n"
                "robot samurái en ciudad cyberpunk\n"
                "mago anciano en biblioteca encantada\n")

    actualizar_panel()

    # Selector de prompts individuales (aparece tras generar)
    frame_selector = ctk.CTkFrame(ventana, fg_color="transparent")

    ctk.CTkLabel(ventana, text="Resultado batch:",
                 font=ctk.CTkFont(size=12), text_color=cc["card_text"]).pack(anchor="w", padx=15, pady=(4, 2))
    txt_batch = ctk.CTkTextbox(ventana, font=ctk.CTkFont(family="Consolas", size=12), wrap="word")
    txt_batch.pack(fill="both", expand=True, padx=15, pady=(0, 4))

    lbl_batch_estado = ctk.CTkLabel(ventana, text="", font=ctk.CTkFont(size=12), text_color=cc["card_text2"])
    lbl_batch_estado.pack(pady=(0, 4))

    frame_bfoot = ctk.CTkFrame(ventana, fg_color="transparent")
    frame_bfoot.pack(fill="x", padx=15, pady=(0, 10))

    # ── Parsear prompts individuales ──────────────────────────────
    prompts_parseados = []  # lista de strings, cada uno un prompt completo

    def _parsear_batch(texto):
        """Extrae prompts individuales del resultado batch."""
        import re
        bloque = texto.strip()

        patron1 = re.split(r'━+\s*Prompt\s*\d+\s*━+|──+\s*Prompt\s*\d+\s*──+', bloque)
        if len(patron1) > 2:
            resultado = [b.strip() for b in patron1
                         if b.strip() and len(b.strip()) > 30
                         and not re.match(r'^MODO\s+[A-Z]', b.strip()[:20])]
            if len(resultado) >= 2:
                return resultado

        patron2 = re.split(r'(?:^|\n)\s*(?:Prompt\s*\d+[\.:\-]|[\d]+[\.)]\s*(?:Prompt|Verbo|Sustantivo))', bloque, flags=re.IGNORECASE)
        if len(patron2) > 2:
            resultado = [b.strip() for b in patron2 if b.strip() and len(b.strip()) > 30]
            if len(resultado) >= 2:
                return resultado

        patron3 = re.split(r'\n(?=\d+[\.)]\s)', bloque)
        if len(patron3) > 1:
            resultado = [b.strip() for b in patron3 if b.strip() and len(b.strip()) > 20]
            if len(resultado) >= 2:
                return resultado

        patron4 = re.split(r'\n(?=POSITIVE PROMPT:)', bloque, flags=re.IGNORECASE)
        if len(patron4) > 1:
            resultado = [b.strip() for b in patron4 if b.strip() and len(b.strip()) > 20]
            if len(resultado) >= 2:
                return resultado

        secciones = re.split(r'\n(?=\d+\s)', bloque)
        if len(secciones) > 2:
            resultado = []
            for s in secciones:
                s = s.strip()
                if len(s) > 20:
                    if re.match(r'^\d+[\.)]', s):
                        s = re.sub(r'^\d+[\.)]\s*', '', s)
                    resultado.append(s)
            if len(resultado) >= 2:
                return resultado

        return [bloque] if bloque else []

    def _extraer_pos_neg(bloque):
        """Extrae positive y negative de un bloque de texto."""
        from workers import limpiar_marcadores
        limpio = limpiar_marcadores(bloque)
        pos, neg = None, None
        if "POSITIVE PROMPT:" in limpio:
            p = limpio.split("POSITIVE PROMPT:")[1]
            pos = (p.split("NEGATIVE PROMPT:")[0] if "NEGATIVE PROMPT:" in p else p).strip(" \n*")
        elif "PROMPT:" in limpio:
            p = limpio.split("PROMPT:")[1]
            pos = p.strip(" \n*")
        if "NEGATIVE PROMPT:" in limpio:
            n = limpio.split("NEGATIVE PROMPT:")[1]
            neg = n.strip(" \n*")
        return pos, neg

    def _mostrar_selector(prompts):
        """Muestra botones numerados con opciones positive/negative."""
        if not _ventana_existe():
            return
        for w in frame_selector.winfo_children():
            w.destroy()
        prompts_parseados.clear()
        prompts_parseados.extend(prompts)

        if len(prompts) <= 1:
            frame_selector.pack_forget()
            return

        frame_selector.pack(fill="x", padx=15, pady=(0, 4), before=lbl_batch_estado)

        # Fila de botones de prompt completo
        row1 = ctk.CTkFrame(frame_selector, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(row1, text="📋 Copiar completo:",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#f39c12").pack(side="left", padx=(0, 6))

        is_lt = _is_light()
        colores = (
            ["#2563eb", "#15803d", "#7c3aed", "#c2410c", "#0891b2",
             "#be185d", "#65a30d", "#7c3aed", "#1d4ed8", "#b45309"]
            if is_lt else
            ["#1a4a7a", "#1a7a3c", "#4a1a7a", "#7a3c1a", "#1a6a6a",
             "#6a1a4a", "#3a5a1a", "#5a1a6a", "#1a3a5a", "#5a3a1a"]
        )

        for i, prompt in enumerate(prompts):
            color = colores[i % len(colores)]
            def copiar_todo(p=prompt, n=i+1):
                import pyperclip
                pyperclip.copy(p)
                lbl_batch_estado.configure(
                    text=f"✅ Prompt #{n} completo copiado", text_color="#2ecc71")
            ctk.CTkButton(row1, text=f"#{i+1}", width=40, height=24,
                          fg_color=color, hover_color="#d1d5db" if is_lt else "#333333",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          command=copiar_todo).pack(side="left", padx=2)

        # Fila de botones positive
        row2 = ctk.CTkFrame(frame_selector, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(row2, text="🟢 Solo POSITIVE:",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#2ecc71").pack(side="left", padx=(0, 6))

        for i, prompt in enumerate(prompts):
            pos, neg = _extraer_pos_neg(prompt)
            def copiar_pos(p=pos, n=i+1):
                import pyperclip
                if p:
                    pyperclip.copy(p)
                    lbl_batch_estado.configure(
                        text=f"✅ POSITIVE #{n} copiado", text_color="#2ecc71")
                else:
                    lbl_batch_estado.configure(
                        text=f"⚠️ Prompt #{n} sin POSITIVE detectado", text_color="#e67e22")
            ctk.CTkButton(row2, text=f"#{i+1}", width=40, height=24,
                          fg_color="#15803d" if is_lt else "#1a5a2a",
                          hover_color="#166534" if is_lt else "#0f3a1a",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          command=copiar_pos).pack(side="left", padx=2)

        # Fila de botones negative
        row3 = ctk.CTkFrame(frame_selector, fg_color="transparent")
        row3.pack(fill="x")
        ctk.CTkLabel(row3, text="🔴 Solo NEGATIVE:",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#e74c3c").pack(side="left", padx=(0, 6))

        for i, prompt in enumerate(prompts):
            pos, neg = _extraer_pos_neg(prompt)
            def copiar_neg(n_text=neg, n=i+1):
                import pyperclip
                if n_text:
                    pyperclip.copy(n_text)
                    lbl_batch_estado.configure(
                        text=f"✅ NEGATIVE #{n} copiado", text_color="#2ecc71")
                else:
                    lbl_batch_estado.configure(
                        text=f"ℹ️ Prompt #{n} sin NEGATIVE (modo natural)", text_color="#3498db")
            ctk.CTkButton(row3, text=f"#{i+1}", width=40, height=24,
                          fg_color="#dc2626" if is_lt else "#5a1a1a",
                          hover_color="#b91c1c" if is_lt else "#3a0f0f",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          command=copiar_neg).pack(side="left", padx=2)

    def _ventana_existe():
        """Comprueba si la ventana batch sigue abierta."""
        try:
            return ventana.winfo_exists()
        except Exception:
            return False

    _batch_cancelado = threading.Event()

    def _on_cerrar_batch():
        """Señaliza cancelación al thread y cierra la ventana."""
        _batch_cancelado.set()
        try:
            ventana.grab_release()
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        ventana.destroy()

    ventana.protocol("WM_DELETE_WINDOW", _on_cerrar_batch)

    def _worker(peticion):
        try:
            if _batch_cancelado.is_set():
                return
            system = app.deepseek.historial[0]["content"] if app.deepseek.historial else ""
            texto = app.deepseek.generar_batch(system, peticion)
            if _batch_cancelado.is_set():
                return
            app.guardar_en_historial(texto)
            if not _ventana_existe():
                return
            ventana.after(0, lambda: _safe_update_batch(texto))
        except Exception as e:
            if _batch_cancelado.is_set() or not _ventana_existe():
                return
            ventana.after(0, lambda: _safe_update_error(str(e)))

    def _safe_update_batch(texto):
        """Actualiza la UI solo si la ventana existe y no fue cancelado."""
        if _batch_cancelado.is_set() or not _ventana_existe():
            return
        _set_batch(texto)
        lbl_batch_estado.configure(text=f"✅ Batch completado — ~{contar_tokens_aprox(texto)} tokens", text_color="#2ecc71")
        btn_gen.configure(state="normal")
        btn_exp.configure(state="normal")
        prompts = _parsear_batch(texto)
        _mostrar_selector(prompts)

    def _safe_update_error(error_msg):
        """Muestra error solo si la ventana existe."""
        if _batch_cancelado.is_set() or not _ventana_existe():
            return
        _set_batch(f"❌ Error: {error_msg}")
        lbl_batch_estado.configure(text="❌ Error en batch", text_color="#e74c3c")
        btn_gen.configure(state="normal")

    def _set_batch(texto):
        if not _ventana_existe():
            return
        txt_batch.delete("1.0", "end")
        txt_batch.insert("1.0", texto)

    def generar():
        # Ocultar selector anterior
        frame_selector.pack_forget()
        for w in frame_selector.winfo_children():
            w.destroy()

        modelo_info = app.construir_modelo_info()
        estilos = app.estilos_texto()
        if batch_modo_var.get() == "auto":
            if not entry_bidea[0]:
                return
            idea = entry_bidea[0].get("1.0", "end").strip()
            if not idea:
                lbl_batch_estado.configure(text="⚠️ Escribe una idea base.", text_color="#e67e22")
                return
            n = int(batch_n_var.get())
            if app.switch_traduccion_var.get() and app.detectar_idioma(idea):
                idea = app.deepseek.traducir(idea)
            peticion = (f"MODO D: Genera {n} prompts distintos para: '{idea}'. "
                        f"Cada uno con enfoque diferente. Estilos base: {estilos}.{modelo_info} "
                        f"Numera cada bloque como ── Prompt 1 ──, etc. POSITIVE PROMPT y NEGATIVE PROMPT en cada uno.")
        else:
            if not entry_blista[0]:
                return
            lista_raw = entry_blista[0].get("1.0", "end").strip()
            if not lista_raw:
                lbl_batch_estado.configure(text="⚠️ Escribe al menos una idea.", text_color="#e67e22")
                return
            ideas = [l.strip() for l in lista_raw.splitlines() if l.strip()][:10]
            if app.switch_traduccion_var.get():
                ideas = [app.deepseek.traducir(i) if app.detectar_idioma(i) else i for i in ideas]
            lista_fmt = "\n".join(f"{i+1}. {idea}" for i, idea in enumerate(ideas))
            peticion = (f"MODO E: Genera un prompt para CADA idea ({len(ideas)} ideas). "
                        f"Estilos: {estilos}.{modelo_info}\n\n{lista_fmt}")

        lbl_batch_estado.configure(text="⏳ Generando batch...", text_color="#f39c12")
        btn_gen.configure(state="disabled")
        btn_exp.configure(state="disabled")
        _set_batch("⏳ Procesando batch...")
        threading.Thread(target=_worker, args=(peticion,), daemon=True).start()

    def exportar():
        texto = txt_batch.get("1.0", "end").strip()
        if not texto or texto.startswith("⏳"):
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Texto", "*.txt")],
            initialfile=f"batch_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            parent=ventana)
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(texto)
            lbl_batch_estado.configure(text=f"💾 Exportado: {Path(ruta).name}", text_color="#2ecc71")

    import pyperclip
    is_lt = _is_light()
    btn_gen = ctk.CTkButton(frame_bfoot, text="⚡ Generar Batch", width=160, height=36,
                             fg_color=cc["btn_use"], hover_color=cc["btn_use_hov"], command=generar)
    btn_gen.pack(side="left", padx=4)
    btn_exp = ctk.CTkButton(frame_bfoot, text="💾 Exportar .txt", width=140, height=36,
                             fg_color="#15803d" if is_lt else "#1a3a2a",
                             hover_color="#166534" if is_lt else "#0f2a1a",
                             state="disabled", command=exportar)
    btn_exp.pack(side="left", padx=4)
    ctk.CTkButton(frame_bfoot, text="📋 Copiar todo", width=130, height=36,
                  fg_color="#475569" if is_lt else "#2c3e50",
                  hover_color="#334155" if is_lt else "#1a252f",
                  command=lambda: pyperclip.copy(txt_batch.get("1.0", "end").strip())).pack(side="left", padx=4)


# HISTORIAL / FAVORITOS

def abrir_lista(app, coleccion, titulo, color_hdr):
    """Abre ventana de historial o favoritos con búsqueda."""
    datos = getattr(app.store, coleccion)
    if not datos:
        messagebox.showinfo(titulo, "No hay entradas guardadas aún.")
        return

    cc = _card_colors()
    ventana = ctk.CTkToplevel(app)
    ventana.title(titulo)
    ventana.geometry("820x700")
    ventana.grab_set()

    # Header
    frame_vtitulo = ctk.CTkFrame(ventana, fg_color="transparent")
    frame_vtitulo.pack(fill="x", padx=15, pady=(12, 4))
    ctk.CTkLabel(frame_vtitulo, text=titulo, font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")

    def limpiar_todo():
        total = len(getattr(app.store, coleccion))
        if messagebox.askyesno("Confirmar",
                               f"¿Borrar TODAS las {total} entradas?\nEsta acción no se puede deshacer.",
                               parent=ventana):
            if coleccion == "historial":
                app.store.limpiar_historial()
            else:
                app.store.limpiar_favoritos()
            refrescar()
            app.set_estado(f"🗑 {titulo} limpiado.")

    ctk.CTkButton(frame_vtitulo, text="🗑 Limpiar todo", width=130, height=28,
                  fg_color=cc["btn_del"], hover_color=cc["btn_del_hov"], command=limpiar_todo).pack(side="right", padx=4)

    lbl_contador = ctk.CTkLabel(frame_vtitulo, text="", font=ctk.CTkFont(size=11), text_color=cc["empty_text"])
    lbl_contador.pack(side="right", padx=8)

    # Barra de búsqueda
    frame_busqueda = ctk.CTkFrame(ventana, fg_color="transparent")
    frame_busqueda.pack(fill="x", padx=15, pady=(0, 6))
    ctk.CTkLabel(frame_busqueda, text="🔍", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 6))
    entry_buscar = ctk.CTkEntry(frame_busqueda, placeholder_text="Buscar por texto, estilo, fecha...",
                                 width=400, height=32)
    entry_buscar.pack(side="left", fill="x", expand=True, padx=(0, 8))

    busqueda_pending = [None]
    def _on_buscar(event=None):
        if busqueda_pending[0]:
            ventana.after_cancel(busqueda_pending[0])
        busqueda_pending[0] = ventana.after(300, refrescar)
    entry_buscar.bind("<KeyRelease>", _on_buscar)

    ctk.CTkButton(frame_busqueda, text="✕", width=32, height=32,
                  fg_color=cc["btn_del"] if _is_light() else "#444",
                  hover_color=cc["btn_del_hov"] if _is_light() else "#222",
                  command=lambda: (entry_buscar.delete(0, "end"), refrescar())).pack(side="left")

    frame_lista = ctk.CTkScrollableFrame(ventana)
    frame_lista.pack(fill="both", expand=True, padx=15, pady=5)

    def refrescar():
        cc = _card_colors()
        for w in frame_lista.winfo_children():
            w.destroy()
        datos_act = getattr(app.store, coleccion)

        # Filtrar por búsqueda
        termino = entry_buscar.get().strip().lower()
        if termino:
            filtrados = []
            for i, entrada in enumerate(datos_act):
                texto_buscar = " ".join([
                    entrada.get("contenido", ""),
                    entrada.get("estilos", ""),
                    entrada.get("modo", ""),
                    entrada.get("fecha", ""),
                    entrada.get("personaje", ""),
                    entrada.get("lora", ""),
                    entrada.get("plataforma", ""),
                ]).lower()
                if termino in texto_buscar:
                    filtrados.append((i, entrada))
        else:
            filtrados = list(enumerate(datos_act[:100]))

        total = len(datos_act)
        mostrados = len(filtrados)
        if termino:
            lbl_contador.configure(text=f"{mostrados} encontrados / {total} total")
        else:
            lbl_contador.configure(text=f"{min(total, 100)} mostrados / {total} total")

        if not filtrados:
            msg = f"Sin resultados para '{termino}'" if termino else "(sin entradas)"
            ctk.CTkLabel(frame_lista, text=msg, text_color=cc["empty_text"]).pack(pady=20)
            return

        # ── MEJORA 7: agrupar por fechas SOLO en historial sin búsqueda activa ──
        if coleccion == "historial" and not termino:
            _renderizar_agrupado(filtrados[:100])
        else:
            for idx_real, entrada in filtrados[:100]:
                _card(frame_lista, entrada, idx_real)

    def _renderizar_agrupado(items):
        """Agrupa las entradas por fechas (Hoy / Ayer / Esta semana / Este mes / Más antiguo) en secciones colapsables."""
        import datetime as _dt
        hoy = _dt.date.today()
        ayer = hoy - _dt.timedelta(days=1)
        inicio_semana = hoy - _dt.timedelta(days=7)
        inicio_mes = hoy - _dt.timedelta(days=30)

        grupos = {
            "Hoy": [],
            "Ayer": [],
            "Esta semana": [],
            "Este mes": [],
            "Más antiguo": [],
        }
        for idx_real, entrada in items:
            fecha_str = (entrada.get("fecha") or "")[:10]
            try:
                f = _dt.date.fromisoformat(fecha_str)
            except Exception:
                f = None
            if f is None:
                grupos["Más antiguo"].append((idx_real, entrada))
            elif f == hoy:
                grupos["Hoy"].append((idx_real, entrada))
            elif f == ayer:
                grupos["Ayer"].append((idx_real, entrada))
            elif f >= inicio_semana:
                grupos["Esta semana"].append((idx_real, entrada))
            elif f >= inicio_mes:
                grupos["Este mes"].append((idx_real, entrada))
            else:
                grupos["Más antiguo"].append((idx_real, entrada))

        # Por defecto: Hoy y Ayer abiertos, resto colapsados
        abiertos_default = {"Hoy", "Ayer"}
        for nombre_grupo in ["Hoy", "Ayer", "Esta semana", "Este mes", "Más antiguo"]:
            entradas = grupos[nombre_grupo]
            if not entradas: continue
            _seccion_colapsable(nombre_grupo, entradas, expanded=(nombre_grupo in abiertos_default))

    def _seccion_colapsable(nombre, entradas, expanded=True):
        """Crea una sección colapsable con cabecera y lista de cards."""
        seccion = ctk.CTkFrame(frame_lista, fg_color="transparent")
        seccion.pack(fill="x", pady=(8, 2))
        # Cabecera clicable
        hdr = ctk.CTkFrame(seccion, fg_color=cc["card_hdr"], corner_radius=6, height=32, cursor="hand2")
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        estado = {"abierto": expanded}
        flecha = ctk.CTkLabel(hdr, text="▼" if expanded else "▶", font=ctk.CTkFont(size=11),
                              text_color=cc["card_hdr_text"], cursor="hand2")
        flecha.pack(side="left", padx=(10, 6))
        ctk.CTkLabel(hdr, text=f"{nombre}", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=cc["card_hdr_text"], cursor="hand2").pack(side="left")
        ctk.CTkLabel(hdr, text=f"  ({len(entradas)})", font=ctk.CTkFont(size=10),
                     text_color=cc["empty_text"], cursor="hand2").pack(side="left", padx=4)

        contenedor = ctk.CTkFrame(seccion, fg_color="transparent")
        if expanded:
            contenedor.pack(fill="x", pady=(2, 0))
            for idx_real, entrada in entradas:
                _card(contenedor, entrada, idx_real)

        def _toggle(_e=None):
            if estado["abierto"]:
                contenedor.pack_forget()
                flecha.configure(text="▶")
                estado["abierto"] = False
            else:
                # Crear las cards si aún no existen (lazy)
                if not contenedor.winfo_children():
                    for idx_real, entrada in entradas:
                        _card(contenedor, entrada, idx_real)
                contenedor.pack(fill="x", pady=(2, 0))
                flecha.configure(text="▼")
                estado["abierto"] = True

        for w in (hdr, flecha):
            w.bind("<Button-1>", _toggle)
        # También hacer clicables los labels internos del header
        for child in hdr.winfo_children():
            child.bind("<Button-1>", _toggle)

    def _card(parent, entrada, idx):
        card = ctk.CTkFrame(parent, fg_color=cc["card_bg"], corner_radius=8)
        card.pack(fill="x", pady=4, padx=5)
        hdr = ctk.CTkFrame(card, fg_color=cc["card_hdr"], corner_radius=6, height=27)
        hdr.pack(fill="x", padx=5, pady=(5, 2))
        hdr.pack_propagate(False)

        fecha   = entrada.get("fecha", "—")
        modo_e  = entrada.get("modo", "imagen")
        estilos = entrada.get("estilos", "—")
        ratio_e = entrada.get("ratio", "")
        nsfw_e  = " 🔥" if entrada.get("nsfw") else ""
        pers_e  = f"  🧑{entrada['personaje'][:12]}" if entrada.get("personaje") else ""
        lora_e  = f"  🔗{entrada['lora'][:15]}" if entrada.get("lora") else ""
        plat_e  = f"  [{entrada['plataforma'][:15]}]" if entrada.get("plataforma") else ""
        ratio_t = f"  [{ratio_e}]" if ratio_e and ratio_e != "Libre" else ""
        ctk.CTkLabel(hdr,
                     text=f"  {fecha}  |  {modo_e.upper()}{nsfw_e}{ratio_t}{plat_e}{pers_e}{lora_e}  |  {estilos}",
                     font=ctk.CTkFont(size=11),
                     text_color=cc["card_hdr_text"]).pack(side="left", padx=8)

        contenido = entrada.get("contenido", "")
        preview = contenido[:200].replace("\n", " ") + ("..." if len(contenido) > 200 else "")
        ctk.CTkLabel(card, text=preview, wraplength=740, justify="left",
                     font=ctk.CTkFont(size=12), text_color=cc["card_text"]).pack(padx=10, pady=(3, 5), anchor="w")

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 6))

        def cargar(c=contenido):
            app.actualizar_salida(c)
            ventana.destroy()
            app.set_estado("📋 Prompt cargado.", "#3498db")

        ctk.CTkButton(btn_row, text="Cargar", width=80, height=26,
                      fg_color=cc["btn_bg"], hover_color=cc["btn_bg_hov"], command=cargar).pack(side="left", padx=2)

        def borrar(i=idx):
            tipo = "entrada" if coleccion == "historial" else "favorito"
            if messagebox.askyesno("Confirmar", f"¿Borrar este {tipo}?", parent=ventana):
                app.store.borrar_entrada(coleccion, i)
                refrescar()

        ctk.CTkButton(btn_row, text="🗑 Borrar", width=88, height=26,
                      fg_color=cc["btn_del"], hover_color=cc["btn_del_hov"], command=borrar).pack(side="left", padx=2)

    refrescar()
    entry_buscar.focus_set()
