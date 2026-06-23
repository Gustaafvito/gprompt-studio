"""
Arquitecto de Prompts v1.0 — Ventanas secundarias.
Personajes, LoRAs, Batch, Historial, Favoritos.
"""
import datetime
import logging
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from modules.gprompt_window import GPromptWindow
from modules.i18n import tr
from workers import contar_tokens_aprox, log_future_exc

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
    """Gestor de personajes con buscador. El form de creación está
    colapsado por defecto; se despliega con el botón "+ Nuevo"."""
    cc = _card_colors()
    ventana = GPromptWindow(app)
    ventana.title(tr("🧑 Gestor de Personajes"))
    ventana.geometry("780x620")
    ventana.grab_set()

    # ── Cabecera ──
    head = ctk.CTkFrame(ventana, fg_color="transparent")
    head.pack(fill="x", padx=15, pady=(12, 4))
    ctk.CTkLabel(head, text=tr("🧑 Personajes Guardados"),
                 font=ctk.CTkFont(size=18, weight="bold"),
                 text_color=cc["label_main"]).pack(side="left")
    lbl_count = ctk.CTkLabel(head, text="", font=ctk.CTkFont(size=11),
                             text_color=cc["empty_text"])
    lbl_count.pack(side="left", padx=10)

    btn_toggle_form = ctk.CTkButton(head, text=tr("+ Nuevo personaje"), width=160,
                                    height=28, fg_color="#1a7a3c",
                                    hover_color="#145e2d")
    btn_toggle_form.pack(side="right")

    ctk.CTkLabel(ventana,
                 text=tr("Los personajes se insertan automáticamente en el prompt al seleccionarlos."),
                 font=ctk.CTkFont(size=10),
                 text_color=cc["empty_text"]).pack(pady=(0, 6), padx=15, anchor="w")

    # ── Buscador ──
    frame_busqueda = ctk.CTkFrame(ventana, fg_color="transparent")
    frame_busqueda.pack(fill="x", padx=15, pady=(0, 6))
    ctk.CTkLabel(frame_busqueda, text="🔍").pack(side="left", padx=(0, 6))
    entry_buscar = ctk.CTkEntry(frame_busqueda, placeholder_text=tr("Buscar por nombre o descripción…"),
                                height=30)
    entry_buscar.pack(side="left", fill="x", expand=True)
    busqueda_pending = [None]

    def _on_buscar(_e=None):
        if busqueda_pending[0]:
            ventana.after_cancel(busqueda_pending[0])
        busqueda_pending[0] = ventana.after(250, refrescar)
    entry_buscar.bind("<KeyRelease>", _on_buscar)

    ctk.CTkButton(frame_busqueda, text="✕", width=32, height=30,
                  fg_color="#444", hover_color="#222",
                  command=lambda: (entry_buscar.delete(0, "end"), refrescar())
                  ).pack(side="left", padx=(6, 0))

    # ── Form de creación (colapsable, oculto por defecto) ──
    frame_nuevo = ctk.CTkFrame(ventana)
    # No empaqueto aún: el toggle se encarga

    ctk.CTkLabel(frame_nuevo, text=tr("Nombre:"), font=ctk.CTkFont(weight="bold"),
                 text_color=cc["label_main"]).pack(side="left", padx=10, pady=8)
    entry_nombre = ctk.CTkEntry(frame_nuevo, width=160, placeholder_text=tr("ej: Luna, Detective…"))
    entry_nombre.pack(side="left", padx=5)

    ctk.CTkLabel(frame_nuevo, text=tr("Descripción:"), font=ctk.CTkFont(weight="bold"),
                 text_color=cc["label_main"]).pack(side="left", padx=(12, 5))
    entry_desc = ctk.CTkEntry(frame_nuevo, width=260,
                              placeholder_text=tr("ej: young woman, silver hair, blue eyes…"))
    entry_desc.pack(side="left", padx=5)

    form_visible = [False]

    def _toggle_form():
        if form_visible[0]:
            frame_nuevo.pack_forget()
            btn_toggle_form.configure(text=tr("+ Nuevo personaje"))
            form_visible[0] = False
        else:
            frame_nuevo.pack(fill="x", padx=15, pady=(2, 6), after=frame_busqueda)
            btn_toggle_form.configure(text=tr("× Cerrar form"))
            form_visible[0] = True
            entry_nombre.focus_set()

    btn_toggle_form.configure(command=_toggle_form)

    # ── Estado de edición (cuál personaje estoy editando) ──
    editando_idx = [None]

    def guardar():
        nombre = entry_nombre.get().strip()
        desc = entry_desc.get().strip()
        if not nombre or not desc:
            messagebox.showwarning(tr("Faltan datos"), tr("Rellena nombre y descripción."),
                                   parent=ventana)
            return
        if editando_idx[0] is not None:
            # Editar existente
            i = editando_idx[0]
            try:
                app.store.personajes[i] = {"nombre": nombre, "descripcion": desc}
                app.store._guardar("personajes")
                editando_idx[0] = None
                btn_guardar.configure(text=tr("💾 Guardar"))
            except Exception as e:
                messagebox.showerror(tr("Error"), tr('No se pudo editar: {0}').format(e), parent=ventana)
                return
        else:
            existia = app.store.guardar_personaje(nombre, desc)
            if existia:
                if not messagebox.askyesno(tr("Ya existe"),
                                           tr("¿Sobreescribir '{0}'?").format(nombre),
                                           parent=ventana):
                    return
        app.actualizar_combo_personajes()
        entry_nombre.delete(0, "end")
        entry_desc.delete(0, "end")
        refrescar()
        app.set_estado(tr("🧑 Personaje '{0}' guardado.").format(nombre), "#2ecc71")

    btn_guardar = ctk.CTkButton(frame_nuevo, text=tr("💾 Guardar"), width=90, height=30,
                                fg_color="#1a7a3c", hover_color="#145e2d",
                                command=guardar)
    btn_guardar.pack(side="left", padx=8)

    frame_lista = ctk.CTkScrollableFrame(ventana)
    frame_lista.pack(fill="both", expand=True, padx=15, pady=5)

    def refrescar():
        cc_loc = _card_colors()
        for w in frame_lista.winfo_children():
            w.destroy()

        personajes = app.store.personajes or []
        termino = entry_buscar.get().strip().lower()
        if termino:
            visibles = [(i, p) for i, p in enumerate(personajes)
                        if termino in p.get("nombre", "").lower()
                        or termino in p.get("descripcion", "").lower()]
        else:
            visibles = list(enumerate(personajes))

        lbl_count.configure(
            text=f"({len(visibles)} de {len(personajes)})" if termino
            else f"({len(personajes)})"
        )

        if not visibles:
            msg = (f"Sin resultados para '{termino}'" if termino
                   else "No hay personajes guardados aún. Pulsa '+ Nuevo personaje'.")
            ctk.CTkLabel(frame_lista, text=msg,
                         text_color=cc_loc["empty_text"]).pack(pady=20)
            return

        for idx, p in visibles:
            card = ctk.CTkFrame(frame_lista, fg_color=cc_loc["card_bg"], corner_radius=8)
            card.pack(fill="x", pady=4, padx=5)
            hdr = ctk.CTkFrame(card, fg_color=cc_loc["card_hdr"],
                               corner_radius=6, height=28)
            hdr.pack(fill="x", padx=5, pady=(5, 2))
            hdr.pack_propagate(False)
            ctk.CTkLabel(hdr, text=f"  🧑 {p['nombre']}",
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=cc_loc["card_hdr_text"]).pack(side="left", padx=8)
            ctk.CTkLabel(card, text=p["descripcion"],
                         wraplength=680, justify="left",
                         font=ctk.CTkFont(size=12),
                         text_color=cc_loc["card_text"]
                         ).pack(padx=10, pady=(3, 5), anchor="w")

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=10, pady=(0, 6))

            def usar(n=p["nombre"]):
                app.combo_personaje.set(n)
                ventana.destroy()
                app.set_estado(tr('🧑 Personaje activo: {0}').format(n), "#2ecc71")

            def editar(i=idx, p_=p):
                # Cargar en form y mostrar form si está oculto
                if not form_visible[0]:
                    _toggle_form()
                entry_nombre.delete(0, "end")
                entry_nombre.insert(0, p_["nombre"])
                entry_desc.delete(0, "end")
                entry_desc.insert(0, p_["descripcion"])
                editando_idx[0] = i
                btn_guardar.configure(text=tr("✏️ Actualizar"))
                entry_desc.focus_set()

            def copiar(p_=p):
                import pyperclip
                pyperclip.copy(p_["descripcion"])
                app.set_estado(tr("📋 Descripción de '{0}' copiada").format(p_['nombre']), "#3498db")

            def borrar(i=idx, n=p["nombre"]):
                if messagebox.askyesno(tr("Confirmar"), tr("¿Borrar '{0}'?").format(n), parent=ventana):
                    app.store.borrar_personaje(i)
                    app.actualizar_combo_personajes()
                    refrescar()

            ctk.CTkButton(btn_row, text=tr("✅ Usar"), width=70, height=26,
                          fg_color=cc_loc["btn_use"],
                          hover_color=cc_loc["btn_use_hov"],
                          command=usar).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text=tr("✏️ Editar"), width=80, height=26,
                          command=editar).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text=tr("📋 Copiar"), width=80, height=26,
                          command=copiar).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text=tr("🗑 Borrar"), width=80, height=26,
                          fg_color=cc_loc["btn_del"],
                          hover_color=cc_loc["btn_del_hov"],
                          command=borrar).pack(side="left", padx=2)

    refrescar()
    entry_buscar.focus_set()


# LORAS

def abrir_loras(app):
    """Gestor de LoRAs con buscador, filtro por familia y edición inline."""
    cc = _card_colors()
    ventana = GPromptWindow(app)
    ventana.title(tr("🔗 Gestor de LoRAs"))
    ventana.geometry("840x640")
    ventana.grab_set()

    FAMILIAS = ["Todas", "SDXL", "SD15", "Pony", "Illustrious",
                "Flux", "SD3.5", "Z Image", "Otra"]

    # ── Cabecera ──
    head = ctk.CTkFrame(ventana, fg_color="transparent")
    head.pack(fill="x", padx=15, pady=(12, 4))
    ctk.CTkLabel(head, text=tr("🔗 LoRAs Guardados"),
                 font=ctk.CTkFont(size=18, weight="bold"),
                 text_color=cc["label_main"]).pack(side="left")
    lbl_count = ctk.CTkLabel(head, text="", font=ctk.CTkFont(size=11),
                             text_color=cc["empty_text"])
    lbl_count.pack(side="left", padx=10)

    btn_toggle_form = ctk.CTkButton(head, text=tr("+ Nuevo LoRA"), width=140,
                                    height=28, fg_color="#5b2c8e",
                                    hover_color="#3d1a6a")
    btn_toggle_form.pack(side="right")

    ctk.CTkLabel(ventana,
                 text=tr("Los LoRAs insertan su trigger word al inicio del prompt automáticamente."),
                 font=ctk.CTkFont(size=10),
                 text_color=cc["empty_text"]).pack(pady=(0, 6), padx=15, anchor="w")

    # ── Buscador + filtro de familia ──
    frame_busqueda = ctk.CTkFrame(ventana, fg_color="transparent")
    frame_busqueda.pack(fill="x", padx=15, pady=(0, 6))
    ctk.CTkLabel(frame_busqueda, text="🔍").pack(side="left", padx=(0, 6))
    entry_buscar = ctk.CTkEntry(frame_busqueda,
                                placeholder_text=tr("Buscar por nombre, trigger o nota…"),
                                height=30)
    entry_buscar.pack(side="left", fill="x", expand=True)
    busqueda_pending = [None]

    def _on_buscar(_e=None):
        if busqueda_pending[0]:
            ventana.after_cancel(busqueda_pending[0])
        busqueda_pending[0] = ventana.after(250, refrescar)
    entry_buscar.bind("<KeyRelease>", _on_buscar)

    ctk.CTkButton(frame_busqueda, text="✕", width=32, height=30,
                  fg_color="#444", hover_color="#222",
                  command=lambda: (entry_buscar.delete(0, "end"), refrescar())
                  ).pack(side="left", padx=(6, 8))

    ctk.CTkLabel(frame_busqueda, text=tr("Familia:")).pack(side="left", padx=(8, 4))
    filtro_familia_var = ctk.StringVar(value="Todas")
    combo_filtro = ctk.CTkComboBox(frame_busqueda, width=120,
                                   values=FAMILIAS, variable=filtro_familia_var,
                                   command=lambda _v: refrescar())
    combo_filtro.pack(side="left")

    # ── Form de creación/edición (colapsable) ──
    frame_nuevo = ctk.CTkFrame(ventana)

    ctk.CTkLabel(frame_nuevo, text=tr("Nombre:"),
                 font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=8)
    entry_nombre = ctk.CTkEntry(frame_nuevo, width=130, placeholder_text=tr("ej: Detail Enhancer"))
    entry_nombre.pack(side="left", padx=5)

    ctk.CTkLabel(frame_nuevo, text=tr("Trigger:"),
                 font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(10, 5))
    entry_trigger = ctk.CTkEntry(frame_nuevo, width=140, placeholder_text=tr("ej: add_detail"))
    entry_trigger.pack(side="left", padx=5)

    ctk.CTkLabel(frame_nuevo, text=tr("Familia:"),
                 font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(10, 5))
    combo_familia_form = ctk.CTkComboBox(frame_nuevo, width=100,
                                         values=["—"] + FAMILIAS[1:])
    combo_familia_form.set("—")
    combo_familia_form.pack(side="left", padx=5)

    ctk.CTkLabel(frame_nuevo, text=tr("Nota:"),
                 font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(10, 5))
    entry_nota = ctk.CTkEntry(frame_nuevo, width=130, placeholder_text=tr("opcional"))
    entry_nota.pack(side="left", padx=5)

    # ── Sub-fila: Rasgos visuales (opcional) ──
    # Si está relleno, la app inyecta estos rasgos en [Subject & Composition]
    # del prompt cuando este LoRA está activo, en lugar de exigir un
    # Personaje separado.
    frame_nuevo_2 = ctk.CTkFrame(ventana, fg_color="transparent")
    rasgos_row = ctk.CTkFrame(frame_nuevo_2, fg_color="transparent")
    rasgos_row.pack(fill="x", padx=10, pady=(0, 6))
    ctk.CTkLabel(
        rasgos_row,
        text=tr("Rasgos visuales (opcional):"),
        font=ctk.CTkFont(size=10, weight="bold"),
    ).pack(anchor="w")
    ctk.CTkLabel(
        rasgos_row,
        text=(
            tr("Si es un LoRA de PERSONAJE, describe sus rasgos físicos clave "
            "(pelo, ojos, undercut, etc). La app los inyectará automáticamente "
            "en el prompt — no necesitas crear un Personaje aparte.")
        ),
        font=ctk.CTkFont(size=9), text_color="#888",
        wraplength=780, justify="left",
    ).pack(anchor="w", pady=(0, 4))
    txt_rasgos = ctk.CTkTextbox(rasgos_row, height=60,
                                font=ctk.CTkFont(size=11))
    txt_rasgos.pack(fill="x")

    form_visible = [False]
    editando_idx = [None]

    def _toggle_form():
        if form_visible[0]:
            frame_nuevo.pack_forget()
            frame_nuevo_2.pack_forget()
            btn_toggle_form.configure(text=tr("+ Nuevo LoRA"))
            form_visible[0] = False
            editando_idx[0] = None
            btn_guardar.configure(text=tr("💾 Guardar"))
        else:
            frame_nuevo.pack(fill="x", padx=15, pady=(2, 0), after=frame_busqueda)
            frame_nuevo_2.pack(fill="x", padx=15, pady=(0, 6), after=frame_nuevo)
            btn_toggle_form.configure(text=tr("× Cerrar form"))
            form_visible[0] = True
            entry_nombre.focus_set()

    btn_toggle_form.configure(command=_toggle_form)

    def guardar():
        nombre  = entry_nombre.get().strip()
        trigger = entry_trigger.get().strip()
        nota    = entry_nota.get().strip()
        familia = combo_familia_form.get().strip()
        rasgos  = txt_rasgos.get("1.0", "end").strip()
        if familia in ("—", ""):
            familia = ""
        if not nombre or not trigger:
            messagebox.showwarning(tr("Faltan datos"), tr("Rellena nombre y trigger word."),
                                   parent=ventana)
            return
        # Validación: detectar triggers que parecen DESCRIPCIONES de
        # personaje en lugar de trigger words reales. Las comas son
        # válidas (LoRAs multi-trigger las usan, p.ej.
        # "Nyra, Amber Eyes, Undercut" para "Nyra for Z-image"), así
        # que solo avisamos en casos claros:
        #   • >40 caracteres (frase larga)
        #   • >8 palabras (lista demasiado extensa)
        #   • puntuación de prosa (puntos, ;, dos puntos finales)
        # Aviso no bloqueante.
        _palabras = trigger.split()
        _sospechoso = (
            len(trigger) > 40
            or len(_palabras) > 8
            or any(c in trigger for c in ".;:")
        )
        if _sospechoso:
            _confirma = messagebox.askyesno(
                tr("¿Trigger correcto?"),
                tr("El trigger '{0}' parece una descripción de personaje, no una palabra de activación.\n\nLos triggers de LoRAs son palabras únicas (ej. 'nira', 'lmnlhrr') o, como mucho, varias separadas por comas (ej. 'Nyra, Amber Eyes, Undercut').\n\nSi quieres guardar la descripción del personaje, ponla en 🧑 Personajes; aquí solo el/los trigger(s).\n\n¿Guardar igualmente '{1}'?").format(trigger, trigger),
                parent=ventana,
            )
            if not _confirma:
                return
        if editando_idx[0] is not None:
            i = editando_idx[0]
            try:
                _entry = {
                    "nombre": nombre, "trigger": trigger,
                    "descripcion": nota, "familia": familia,
                }
                if rasgos:
                    _entry["rasgos_visuales"] = rasgos
                app.store.loras[i] = _entry
                app.store._guardar("loras")
                editando_idx[0] = None
                btn_guardar.configure(text=tr("💾 Guardar"))
            except Exception as e:
                messagebox.showerror(tr("Error"), tr('No se pudo editar: {0}').format(e),
                                     parent=ventana)
                return
        else:
            existia = app.store.guardar_lora(nombre, trigger, nota, familia, rasgos)
            if existia:
                if not messagebox.askyesno(tr("Ya existe"),
                                           tr("¿Sobreescribir '{0}'?").format(nombre),
                                           parent=ventana):
                    return
        app.actualizar_combo_loras()
        entry_nombre.delete(0, "end")
        entry_trigger.delete(0, "end")
        entry_nota.delete(0, "end")
        combo_familia_form.set("—")
        txt_rasgos.delete("1.0", "end")
        refrescar()
        app.set_estado(tr("🔗 LoRA '{0}' guardado.").format(nombre), "#9b59b6")

    btn_guardar = ctk.CTkButton(frame_nuevo, text=tr("💾 Guardar"), width=90, height=30,
                                fg_color="#5b2c8e", hover_color="#3d1a6a",
                                command=guardar)
    btn_guardar.pack(side="left", padx=8)

    frame_lista = ctk.CTkScrollableFrame(ventana)
    frame_lista.pack(fill="both", expand=True, padx=15, pady=5)

    def refrescar():
        cc_loc = _card_colors()
        for w in frame_lista.winfo_children():
            w.destroy()

        loras = app.store.loras or []
        termino = entry_buscar.get().strip().lower()
        fam_sel = filtro_familia_var.get()

        def _filtra(l):
            if fam_sel != "Todas" and (l.get("familia", "") or "Otra") != fam_sel:
                return False
            if not termino:
                return True
            return (termino in l.get("nombre", "").lower()
                    or termino in l.get("trigger", "").lower()
                    or termino in l.get("descripcion", "").lower())

        visibles = [(i, l) for i, l in enumerate(loras) if _filtra(l)]
        sufijo_filtro = "" if fam_sel == "Todas" else f" · familia={fam_sel}"
        lbl_count.configure(
            text=f"({len(visibles)} de {len(loras)}{sufijo_filtro})"
            if (termino or fam_sel != "Todas")
            else f"({len(loras)})"
        )

        if not visibles:
            msg = (f"Sin resultados" if (termino or fam_sel != "Todas")
                   else "No hay LoRAs guardados aún.\nPulsa '+ Nuevo LoRA' para añadir.")
            ctk.CTkLabel(frame_lista, text=msg,
                         text_color=cc_loc["empty_text"], justify="center").pack(pady=20)
            return

        for idx, l in visibles:
            card = ctk.CTkFrame(frame_lista, fg_color=cc_loc["card_bg"], corner_radius=8)
            card.pack(fill="x", pady=4, padx=5)
            hdr = ctk.CTkFrame(card, fg_color=cc_loc["card_hdr"],
                               corner_radius=6, height=28)
            hdr.pack(fill="x", padx=5, pady=(5, 2))
            hdr.pack_propagate(False)
            familia = l.get("familia", "")
            badge_familia = f"  [{familia}]" if familia else ""
            ctk.CTkLabel(hdr,
                         text=tr('  🔗 {0}{1}   →   trigger: "{2}"').format((l['nombre']), (badge_familia), (l['trigger'])),
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=cc_loc["card_hdr_text"]).pack(side="left", padx=8)
            nota = l.get("descripcion", "")
            if nota:
                ctk.CTkLabel(card, text=nota, wraplength=760, justify="left",
                             font=ctk.CTkFont(size=11),
                             text_color=cc_loc["card_text2"]
                             ).pack(padx=10, pady=(2, 3), anchor="w")
            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=10, pady=(0, 6))

            def usar(n=l["nombre"]):
                app.combo_lora.set(n)
                ventana.destroy()
                app.set_estado(tr('🔗 LoRA activo: {0}').format(n), "#9b59b6")

            def editar(i=idx, l_=l):
                if not form_visible[0]:
                    _toggle_form()
                entry_nombre.delete(0, "end"); entry_nombre.insert(0, l_["nombre"])
                entry_trigger.delete(0, "end"); entry_trigger.insert(0, l_["trigger"])
                entry_nota.delete(0, "end"); entry_nota.insert(0, l_.get("descripcion", ""))
                f = l_.get("familia") or "—"
                combo_familia_form.set(f if f in FAMILIAS[1:] else "—")
                # Cargar rasgos visuales (campo nuevo sesión 16)
                txt_rasgos.delete("1.0", "end")
                txt_rasgos.insert("1.0", l_.get("rasgos_visuales", ""))
                editando_idx[0] = i
                btn_guardar.configure(text=tr("✏️ Actualizar"))

            def copiar(l_=l):
                import pyperclip
                pyperclip.copy(l_["trigger"])
                app.set_estado(tr("📋 Trigger '{0}' copiado").format(l_['trigger']), "#3498db")

            def borrar(i=idx, n=l["nombre"]):
                if messagebox.askyesno(tr("Confirmar"),
                                       tr("¿Borrar LoRA '{0}'?").format(n),
                                       parent=ventana):
                    app.store.borrar_lora(i)
                    app.actualizar_combo_loras()
                    refrescar()

            ctk.CTkButton(btn_row, text=tr("✅ Usar"), width=70, height=26,
                          fg_color="#7c3aed" if _is_light() else "#3a1a5a",
                          hover_color="#6d28d9" if _is_light() else "#2a0f4a",
                          command=usar).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text=tr("✏️ Editar"), width=80, height=26,
                          command=editar).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text=tr("📋 Trigger"), width=80, height=26,
                          command=copiar).pack(side="left", padx=2)
            ctk.CTkButton(btn_row, text=tr("🗑 Borrar"), width=80, height=26,
                          fg_color="#dc2626" if _is_light() else "#6a1a1a",
                          hover_color="#b91c1c" if _is_light() else "#4a0f0f",
                          command=borrar).pack(side="left", padx=2)

    refrescar()
    entry_buscar.focus_set()


# BATCH VARIABLES

def abrir_batch_variables(app):
    """Modal para sustituir {variables} en la idea actual con múltiples valores."""
    import itertools
    import re
    cc = _card_colors()
    is_lt = _is_light()

    plantilla = app.txt_idea.get("1.0", "end").strip()
    vars_detectadas = list(dict.fromkeys(re.findall(r'\{(\w+)\}', plantilla)))

    ventana = GPromptWindow(app)
    ventana.title(tr("⚡ Batch de Variables"))
    ventana.geometry("600x620")
    ventana.grab_set()

    ctk.CTkLabel(ventana, text=tr("⚡ Batch de Variables"),
                 font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(12, 2))
    ctk.CTkLabel(ventana, text=tr("Usa {variable} en tu idea y aquí define múltiples valores"),
                 font=ctk.CTkFont(size=10),
                 text_color=cc["card_text2"]).pack(pady=(0, 8))

    # Plantilla editable
    frame_tmpl = ctk.CTkFrame(ventana)
    frame_tmpl.pack(fill="x", padx=15, pady=(0, 8))
    ctk.CTkLabel(frame_tmpl, text=tr("Plantilla (idea con {variables}):"),
                 font=ctk.CTkFont(weight="bold", size=11)).pack(anchor="w", padx=8, pady=(6, 2))
    txt_tmpl = ctk.CTkTextbox(frame_tmpl, height=55, font=ctk.CTkFont(size=12))
    txt_tmpl.pack(fill="x", padx=8, pady=(0, 8))
    txt_tmpl.insert("1.0", plantilla or "una {animal} en {lugar} con iluminación {luz}")

    # Frame de variables dinámico
    frame_vars_outer = ctk.CTkFrame(ventana)
    frame_vars_outer.pack(fill="x", padx=15, pady=(0, 8))
    ctk.CTkLabel(frame_vars_outer, text=tr("Variables detectadas (valores separados por coma):"),
                 font=ctk.CTkFont(weight="bold", size=11)).pack(anchor="w", padx=8, pady=(6, 2))

    entries_vars = {}  # var_name → CTkEntry

    def _refrescar_vars():
        for w in frame_vars_outer.winfo_children():
            if hasattr(w, "_es_var_row"):
                w.destroy()
        tmpl_text = txt_tmpl.get("1.0", "end").strip()
        detectadas = list(dict.fromkeys(re.findall(r'\{(\w+)\}', tmpl_text)))
        entries_vars.clear()
        for vname in detectadas:
            row = ctk.CTkFrame(frame_vars_outer, fg_color="transparent")
            row._es_var_row = True
            row.pack(fill="x", padx=8, pady=2)
            ctk.CTkLabel(row, text=f"{{{vname}}}",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#3b82f6", width=100).pack(side="left", padx=(0, 8))
            ent = ctk.CTkEntry(row, placeholder_text=tr("val1, val2, val3"), font=ctk.CTkFont(size=11))
            ent.pack(side="left", fill="x", expand=True)
            entries_vars[vname] = ent
        if not detectadas:
            row = ctk.CTkFrame(frame_vars_outer, fg_color="transparent")
            row._es_var_row = True
            row.pack(fill="x", padx=8)
            ctk.CTkLabel(row, text=tr("No se detectaron {variables} en la plantilla."),
                         font=ctk.CTkFont(size=10), text_color=cc["card_text2"]).pack(anchor="w")

    _refrescar_vars()

    ctk.CTkButton(frame_vars_outer, text=tr("🔄 Detectar variables"), height=26, width=160,
                  fg_color="#374151", hover_color="#4b5563",
                  font=ctk.CTkFont(size=10),
                  command=_refrescar_vars).pack(anchor="e", padx=8, pady=(4, 8))

    # Modo: lineal vs combinaciones
    modo_var = ctk.StringVar(value="lineal")
    frame_modo = ctk.CTkFrame(ventana, fg_color="transparent")
    frame_modo.pack(fill="x", padx=15, pady=(0, 6))
    ctk.CTkLabel(frame_modo, text=tr("Modo:"), font=ctk.CTkFont(weight="bold", size=11)).pack(side="left", padx=(0, 8))
    ctk.CTkRadioButton(frame_modo, text=tr("Secuencial (valor a valor, mismo índice)"), variable=modo_var, value="lineal").pack(side="left", padx=6)
    ctk.CTkRadioButton(frame_modo, text=tr("Todas las combis (máx 20)"), variable=modo_var, value="product").pack(side="left", padx=6)

    # Resultado
    ctk.CTkLabel(ventana, text=tr("Variaciones generadas:"),
                 font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=15, pady=(0, 2))
    txt_resultado = ctk.CTkTextbox(ventana, font=ctk.CTkFont(family="Consolas", size=11), wrap="word")
    txt_resultado.pack(fill="both", expand=True, padx=15, pady=(0, 4))

    lbl_count = ctk.CTkLabel(ventana, text="", font=ctk.CTkFont(size=10), text_color=cc["card_text2"])
    lbl_count.pack(pady=(0, 2))

    def _generar():
        tmpl = txt_tmpl.get("1.0", "end").strip()
        if not tmpl:
            return
        vals_por_var = {}
        for vname, ent in entries_vars.items():
            raw = ent.get().strip()
            if raw:
                vals_por_var[vname] = [v.strip() for v in raw.split(",") if v.strip()]
            else:
                vals_por_var[vname] = [f"{{{vname}}}"]

        if not vals_por_var:
            txt_resultado.delete("1.0", "end")
            txt_resultado.insert("1.0", tmpl)
            lbl_count.configure(text=tr("1 variación (sin variables)"))
            return

        keys = list(vals_por_var.keys())
        listas = [vals_por_var[k] for k in keys]

        if modo_var.get() == "product":
            combinaciones = list(itertools.product(*listas))[:20]
        else:
            max_len = max(len(l) for l in listas)
            combinaciones = list(zip(*[l + [l[-1]] * (max_len - len(l)) for l in listas]))

        variaciones = []
        for combo in combinaciones:
            texto = tmpl
            for k, v in zip(keys, combo):
                texto = texto.replace(f"{{{k}}}", v)
            variaciones.append(texto)

        txt_resultado.delete("1.0", "end")
        txt_resultado.insert("1.0", "\n\n---\n\n".join(
            f"[{i+1}] {v}" for i, v in enumerate(variaciones)
        ))
        lbl_count.configure(text=tr('{0} variación(es) generadas').format(len(variaciones)))

    def _copiar_todo():
        contenido = txt_resultado.get("1.0", "end").strip()
        if contenido:
            ventana.clipboard_clear()
            ventana.clipboard_append(contenido)
            lbl_count.configure(text=tr("✅ Copiado al portapapeles"))

    def _enviar_a_salida():
        contenido = txt_resultado.get("1.0", "end").strip()
        if contenido:
            app.txt_salida.delete("1.0", "end")
            app.txt_salida.insert("1.0", contenido)
            ventana.destroy()
            app.dialogs.set_estado(tr("⚡ Variaciones volcadas al resultado"), "#22c55e")

    frame_btns = ctk.CTkFrame(ventana, fg_color="transparent")
    frame_btns.pack(fill="x", padx=15, pady=(0, 12))
    ctk.CTkButton(frame_btns, text=tr("⚡ Generar variaciones"), height=32, width=160,
                  fg_color="#1a8a3c", hover_color="#166d30",
                  font=ctk.CTkFont(size=11, weight="bold"),
                  command=_generar).pack(side="left", padx=4)
    ctk.CTkButton(frame_btns, text=tr("📋 Copiar todo"), height=32, width=120,
                  fg_color="#374151", hover_color="#4b5563",
                  font=ctk.CTkFont(size=11), command=_copiar_todo).pack(side="left", padx=4)
    ctk.CTkButton(frame_btns, text=tr("→ Enviar a resultado"), height=32, width=150,
                  fg_color="#1e3a8a", hover_color="#162d6e",
                  font=ctk.CTkFont(size=11), command=_enviar_a_salida).pack(side="left", padx=4)

    if vars_detectadas:
        ventana.after(200, _generar)


# BATCH

def abrir_batch(app):
    cc = _card_colors()
    ventana = GPromptWindow(app)
    ventana.title(tr("📦 Generación Batch"))
    ventana.geometry("850x750")
    ventana.grab_set()

    ctk.CTkLabel(ventana, text=tr("📦 Generación Batch"),
                 font=ctk.CTkFont(size=18, weight="bold")).pack(pady=12)

    batch_modo_var = ctk.StringVar(value="auto")
    frame_bmodo = ctk.CTkFrame(ventana)
    frame_bmodo.pack(fill="x", padx=15, pady=(0, 8))
    ctk.CTkLabel(frame_bmodo, text=tr("Modo:"), font=ctk.CTkFont(weight="bold")).pack(side="left", padx=12, pady=10)
    ctk.CTkRadioButton(frame_bmodo, text=tr("🔁 Auto (1 idea → N prompts)"),
                       variable=batch_modo_var, value="auto",
                       command=lambda: actualizar_panel()).pack(side="left", padx=12)
    ctk.CTkRadioButton(frame_bmodo, text=tr("📋 Lista (N ideas → N prompts)"),
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
            ctk.CTkLabel(frame_panel, text=tr("Idea base:"), font=ctk.CTkFont(weight="bold")).pack(
                anchor="w", padx=12, pady=(8, 2))
            entry_bidea[0] = ctk.CTkTextbox(frame_panel, height=55, font=ctk.CTkFont(size=13))
            entry_bidea[0].pack(fill="x", padx=12, pady=(0, 6))
            idea_actual = app.txt_idea.get("1.0", "end").strip()
            if idea_actual:
                entry_bidea[0].insert("1.0", idea_actual)
            frame_bn = ctk.CTkFrame(frame_panel, fg_color="transparent")
            frame_bn.pack(fill="x", padx=12, pady=(0, 8))
            ctk.CTkLabel(frame_bn, text=tr("Número de prompts:"), font=ctk.CTkFont(weight="bold")).pack(side="left")
            lbl_bn = ctk.CTkLabel(frame_bn, text=str(batch_n_var.get()),
                                   font=ctk.CTkFont(size=14, weight="bold"), text_color="#3498db", width=28)
            ctk.CTkSlider(frame_bn, from_=2, to=10, number_of_steps=8, variable=batch_n_var,
                          command=lambda v: lbl_bn.configure(text=f"{int(v)}")).pack(
                side="left", padx=10, fill="x", expand=True)
            lbl_bn.pack(side="left")
        else:
            ctk.CTkLabel(frame_panel, text=tr("Lista de ideas (una por línea, máx 10):"),
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

    ctk.CTkLabel(ventana, text=tr("Resultado batch:"),
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
        ctk.CTkLabel(row1, text=tr("📋 Copiar completo:"),
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
                    text=tr('✅ Prompt #{0} completo copiado').format(n), text_color="#2ecc71")
            ctk.CTkButton(row1, text=f"#{i+1}", width=40, height=24,
                          fg_color=color, hover_color="#d1d5db" if is_lt else "#333333",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          command=copiar_todo).pack(side="left", padx=2)

        # Fila de botones positive
        row2 = ctk.CTkFrame(frame_selector, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(row2, text=tr("🟢 Solo POSITIVE:"),
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#2ecc71").pack(side="left", padx=(0, 6))

        for i, prompt in enumerate(prompts):
            pos, neg = _extraer_pos_neg(prompt)
            def copiar_pos(p=pos, n=i+1):
                import pyperclip
                if p:
                    pyperclip.copy(p)
                    lbl_batch_estado.configure(
                        text=tr('✅ POSITIVE #{0} copiado').format(n), text_color="#2ecc71")
                else:
                    lbl_batch_estado.configure(
                        text=tr('⚠️ Prompt #{0} sin POSITIVE detectado').format(n), text_color="#e67e22")
            ctk.CTkButton(row2, text=f"#{i+1}", width=40, height=24,
                          fg_color="#15803d" if is_lt else "#1a5a2a",
                          hover_color="#166534" if is_lt else "#0f3a1a",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          command=copiar_pos).pack(side="left", padx=2)

        # Fila de botones negative
        row3 = ctk.CTkFrame(frame_selector, fg_color="transparent")
        row3.pack(fill="x")
        ctk.CTkLabel(row3, text=tr("🔴 Solo NEGATIVE:"),
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#e74c3c").pack(side="left", padx=(0, 6))

        for i, prompt in enumerate(prompts):
            pos, neg = _extraer_pos_neg(prompt)
            def copiar_neg(n_text=neg, n=i+1):
                import pyperclip
                if n_text:
                    pyperclip.copy(n_text)
                    lbl_batch_estado.configure(
                        text=tr('✅ NEGATIVE #{0} copiado').format(n), text_color="#2ecc71")
                else:
                    lbl_batch_estado.configure(
                        text=tr('ℹ️ Prompt #{0} sin NEGATIVE (modo natural)').format(n), text_color="#3498db")
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
            ventana.after(0, lambda e=e: _safe_update_error(str(e)))

    def _safe_update_batch(texto):
        """Actualiza la UI solo si la ventana existe y no fue cancelado."""
        if _batch_cancelado.is_set() or not _ventana_existe():
            return
        _set_batch(texto)
        lbl_batch_estado.configure(text=tr('✅ Batch completado — ~{0} tokens').format(contar_tokens_aprox(texto)), text_color="#2ecc71")
        btn_gen.configure(state="normal")
        btn_exp.configure(state="normal")
        prompts = _parsear_batch(texto)
        _mostrar_selector(prompts)

    def _safe_update_error(error_msg):
        """Muestra error solo si la ventana existe."""
        if _batch_cancelado.is_set() or not _ventana_existe():
            return
        _set_batch(f"❌ Error: {error_msg}")
        lbl_batch_estado.configure(text=tr("❌ Error en batch"), text_color="#e74c3c")
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
                lbl_batch_estado.configure(text=tr("⚠️ Escribe una idea base."), text_color="#e67e22")
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
                lbl_batch_estado.configure(text=tr("⚠️ Escribe al menos una idea."), text_color="#e67e22")
                return
            ideas = [l.strip() for l in lista_raw.splitlines() if l.strip()][:10]
            if app.switch_traduccion_var.get():
                ideas = [app.deepseek.traducir(i) if app.detectar_idioma(i) else i for i in ideas]
            lista_fmt = "\n".join(f"{i+1}. {idea}" for i, idea in enumerate(ideas))
            peticion = (f"MODO E: Genera un prompt para CADA idea ({len(ideas)} ideas). "
                        f"Estilos: {estilos}.{modelo_info}\n\n{lista_fmt}")

        lbl_batch_estado.configure(text=tr("⏳ Generando batch..."), text_color="#f39c12")
        btn_gen.configure(state="disabled")
        btn_exp.configure(state="disabled")
        _set_batch("⏳ Procesando batch...")
        app._executor.submit(_worker, peticion).add_done_callback(log_future_exc)

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
            lbl_batch_estado.configure(text=tr('💾 Exportado: {0}').format(Path(ruta).name), text_color="#2ecc71")

    import pyperclip
    is_lt = _is_light()
    btn_gen = ctk.CTkButton(frame_bfoot, text=tr("⚡ Generar Batch"), width=160, height=36,
                             fg_color=cc["btn_use"], hover_color=cc["btn_use_hov"], command=generar)
    btn_gen.pack(side="left", padx=4)
    btn_exp = ctk.CTkButton(frame_bfoot, text=tr("💾 Exportar .txt"), width=140, height=36,
                             fg_color="#15803d" if is_lt else "#1a3a2a",
                             hover_color="#166534" if is_lt else "#0f2a1a",
                             state="disabled", command=exportar)
    btn_exp.pack(side="left", padx=4)
    ctk.CTkButton(frame_bfoot, text=tr("📋 Copiar todo"), width=130, height=36,
                  fg_color="#475569" if is_lt else "#2c3e50",
                  hover_color="#334155" if is_lt else "#1a252f",
                  command=lambda: pyperclip.copy(txt_batch.get("1.0", "end").strip())).pack(side="left", padx=4)


# HISTORIAL / FAVORITOS

def abrir_lista(app, coleccion, titulo, color_hdr):
    """Abre ventana de historial o favoritos con búsqueda."""
    datos = getattr(app.store, coleccion)
    if not datos:
        messagebox.showinfo(titulo, tr("No hay entradas guardadas aún."))
        return

    cc = _card_colors()
    ventana = GPromptWindow(app)
    ventana.title(titulo)
    ventana.geometry("820x700")
    ventana.grab_set()

    # Header
    frame_vtitulo = ctk.CTkFrame(ventana, fg_color="transparent")
    frame_vtitulo.pack(fill="x", padx=15, pady=(12, 4))
    ctk.CTkLabel(frame_vtitulo, text=titulo, font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")

    def limpiar_todo():
        total = len(getattr(app.store, coleccion))
        if not messagebox.askyesno(tr("Confirmar"),
                                   tr('¿Borrar TODAS las {0} entradas?\nEsta acción no se puede deshacer.').format(total),
                                   parent=ventana):
            return
        # FIX: antes el `else` llamaba a limpiar_favoritos() incluso para
        # estrellas (que borraba favoritos por error). Ahora dispatch correcto.
        metodo = {
            "historial":  app.store.limpiar_historial,
            "favoritos":  app.store.limpiar_favoritos,
            "estrellas":  app.store.limpiar_estrellas,
        }.get(coleccion)
        if metodo:
            metodo()
        else:
            # Fallback genérico (otras colecciones añadidas en el futuro)
            setattr(app.store, coleccion, [])
            app.store._guardar(coleccion)
        refrescar()
        app.set_estado(tr('🗑 {0} limpiado.').format(titulo))

    ctk.CTkButton(frame_vtitulo, text=tr("🗑 Limpiar todo"), width=130, height=28,
                  fg_color=cc["btn_del"], hover_color=cc["btn_del_hov"], command=limpiar_todo).pack(side="right", padx=4)

    lbl_contador = ctk.CTkLabel(frame_vtitulo, text="", font=ctk.CTkFont(size=11), text_color=cc["empty_text"])
    lbl_contador.pack(side="right", padx=8)

    # Barra de búsqueda
    frame_busqueda = ctk.CTkFrame(ventana, fg_color="transparent")
    frame_busqueda.pack(fill="x", padx=15, pady=(0, 6))
    ctk.CTkLabel(frame_busqueda, text="🔍", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 6))
    entry_buscar = ctk.CTkEntry(frame_busqueda, placeholder_text=tr("Buscar por texto, estilo, fecha..."),
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

    # ── Filtro por modo ──
    ctk.CTkLabel(frame_busqueda, text=tr("Modo:")).pack(side="left", padx=(12, 4))
    filtro_modo_var = ctk.StringVar(value="Todos")
    combo_filtro_modo = ctk.CTkComboBox(
        frame_busqueda, width=110, variable=filtro_modo_var,
        values=["Todos", "imagen", "video", "audio"],
        command=lambda _v: refrescar(),
    )
    combo_filtro_modo.pack(side="left")

    frame_lista = ctk.CTkScrollableFrame(ventana)
    frame_lista.pack(fill="both", expand=True, padx=15, pady=5)

    # Estado de paginación
    PAGE_SIZE = 50
    estado = {"visible": PAGE_SIZE}

    def refrescar():
        cc = _card_colors()
        for w in frame_lista.winfo_children():
            w.destroy()
        datos_act = getattr(app.store, coleccion)

        termino = entry_buscar.get().strip().lower()
        modo_sel = filtro_modo_var.get()

        def _coincide(entrada: dict) -> bool:
            if modo_sel != "Todos" and entrada.get("modo", "") != modo_sel:
                return False
            if not termino:
                return True
            texto = " ".join([
                str(entrada.get("contenido", "")),
                str(entrada.get("estilos", "")),
                str(entrada.get("modo", "")),
                str(entrada.get("fecha", "")),
                str(entrada.get("personaje", "")),
                str(entrada.get("lora", "")),
                str(entrada.get("plataforma", "")),
                str(entrada.get("nota", "")),  # estrellas
            ]).lower()
            return termino in texto

        filtrados = [(i, e) for i, e in enumerate(datos_act) if _coincide(e)]

        total = len(datos_act)
        total_filtrado = len(filtrados)
        visibles = min(estado["visible"], total_filtrado)

        suf_filtro = []
        if termino: suf_filtro.append(f"búsqueda '{termino}'")
        if modo_sel != "Todos": suf_filtro.append(f"modo={modo_sel}")
        filtro_txt = " · " + " · ".join(suf_filtro) if suf_filtro else ""
        lbl_contador.configure(
            text=tr('{0} de {1} mostrados ({2} total){3}').format((visibles), (total_filtrado), (total), (filtro_txt))
        )

        if total_filtrado == 0:
            msg = "Sin resultados con esos filtros" if (termino or modo_sel != "Todos") else "(sin entradas)"
            ctk.CTkLabel(frame_lista, text=msg, text_color=cc["empty_text"]).pack(pady=20)
            return

        # ── Agrupar SOLO si: historial + sin búsqueda + sin filtro modo ──
        items_pag = filtrados[:visibles]
        if coleccion == "historial" and not termino and modo_sel == "Todos":
            _renderizar_agrupado(items_pag)
        else:
            for idx_real, entrada in items_pag:
                _card(frame_lista, entrada, idx_real)

        # ── Botón "Mostrar más" si quedan ──
        restantes = total_filtrado - visibles
        if restantes > 0:
            def _mas():
                estado["visible"] += PAGE_SIZE
                refrescar()
            ctk.CTkButton(
                frame_lista,
                text=tr('▼ Mostrar {0} más  ({1} restantes)').format((min(PAGE_SIZE, restantes)), (restantes)),
                command=_mas, height=32,
                fg_color=cc["btn_bg"], hover_color=cc["btn_bg_hov"],
            ).pack(fill="x", padx=4, pady=(10, 6))

    # Cuando cambia búsqueda o filtro, resetear paginación
    def _resetear_paginacion(_e=None):
        estado["visible"] = PAGE_SIZE
        if busqueda_pending[0]:
            ventana.after_cancel(busqueda_pending[0])
        busqueda_pending[0] = ventana.after(300, refrescar)
    entry_buscar.bind("<KeyRelease>", _resetear_paginacion)
    combo_filtro_modo.configure(
        command=lambda _v: (estado.update({"visible": PAGE_SIZE}), refrescar())[1]
    )

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
        if isinstance(estilos, list):
            estilos = ", ".join(str(e) for e in estilos if e) or "—"
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

        # Nota (solo estrellas). Aparece encima del contenido si existe.
        nota = entrada.get("nota", "") if coleccion == "estrellas" else ""
        if nota:
            ctk.CTkLabel(card,
                         text=f"🌟 {nota}",
                         font=ctk.CTkFont(size=11, weight="bold", slant="italic"),
                         text_color="#f59e0b" if _is_light() else "#fbbf24",
                         wraplength=740, justify="left", anchor="w"
                         ).pack(fill="x", padx=10, pady=(4, 0))

        contenido = entrada.get("contenido", "")
        preview = contenido[:200].replace("\n", " ") + ("..." if len(contenido) > 200 else "")
        ctk.CTkLabel(card, text=preview, wraplength=740, justify="left",
                     font=ctk.CTkFont(size=12), text_color=cc["card_text"]
                     ).pack(padx=10, pady=(3, 5), anchor="w")

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 6))

        def cargar(c=contenido):
            app.actualizar_salida(c)
            ventana.destroy()
            app.set_estado(tr("📋 Prompt cargado."), "#3498db")

        def copiar(c=contenido):
            try:
                import pyperclip
                pyperclip.copy(c)
                app.set_estado(tr('📋 {0} caracteres copiados').format(len(c)), "#2ecc71")
            except Exception as _e:
                app.set_estado(tr('❌ No se pudo copiar: {0}').format(_e), "#e74c3c")

        ctk.CTkButton(btn_row, text=tr("Cargar"), width=80, height=26,
                      fg_color=cc["btn_bg"], hover_color=cc["btn_bg_hov"],
                      command=cargar).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text=tr("📋 Copiar"), width=90, height=26,
                      command=copiar).pack(side="left", padx=2)

        def borrar(i=idx):
            tipo = {"historial": "entrada del historial",
                    "favoritos": "favorito",
                    "estrellas": "estrella"}.get(coleccion, "entrada")
            if messagebox.askyesno(tr("Confirmar"), tr('¿Borrar este {0}?').format(tipo), parent=ventana):
                app.store.borrar_entrada(coleccion, i)
                refrescar()

        ctk.CTkButton(btn_row, text=tr("🗑 Borrar"), width=88, height=26,
                      fg_color=cc["btn_del"], hover_color=cc["btn_del_hov"], command=borrar).pack(side="left", padx=2)

    refrescar()
    entry_buscar.focus_set()
