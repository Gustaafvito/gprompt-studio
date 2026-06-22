"""ADN Visual — extracción JSON estructurado de imagen + biblioteca de ADNs.

Comandos principales:

  • _cmd_adn_visual           — extrae ADN de la imagen cargada y abre
                                modal con categorías bloqueables +
                                conversión por plataforma.
  • _cmd_ver_biblioteca_adn   — biblioteca de ADNs guardados en
                                preferencias (buscar, cargar, borrar).

Dependencias self (provistas por ArquitectoApp):
  imagen_cargada, vision, txt_idea, store, after, set_estado,
  toggle_botones, actualizar_salida.
"""
import datetime
import json
import logging

import customtkinter as ctk
import pyperclip

from config import ADN_A_PLATAFORMA, get_theme_colors
from modules.gprompt_window import GPromptWindow
from modules.i18n import tr
from workers import log_future_exc

logger = logging.getLogger(__name__)


class AdnVisualService:
    """ADN Visual + biblioteca de ADNs guardados.

    A1 fase 2 (sesión 14): servicio aislado con app por composición.
    Acceso: `app.adn.cmd_ver_biblioteca()`, `app.adn.cmd_adn_visual()`.
    """

    def __init__(self, app):
        self.app = app

    def _cmd_ver_biblioteca_adn(self):
        """Muestra la biblioteca de ADNs guardados, con refresh sin recargar."""
        prefs = self.app.store.cargar_preferencias()
        adns = prefs.get("adns_guardados", [])

        vent = GPromptWindow(self.app)
        vent.title(tr("📚 Biblioteca de ADNs"))
        vent.geometry("720x540")
        vent.transient(self.app)

        is_light = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_light)

        # Header con contador dinámico
        hdr = ctk.CTkFrame(vent, fg_color=c["fg_dark"])
        hdr.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(hdr, text=tr("🧬 ADNs Guardados"),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        contador_var = ctk.StringVar(value=f"{len(adns)} guardado(s)")
        ctk.CTkLabel(hdr, textvariable=contador_var,
                     text_color=c["muted_text"]).pack(side="right", padx=10)

        # Buscador
        search_row = ctk.CTkFrame(vent, fg_color="transparent")
        search_row.pack(fill="x", padx=10, pady=(0, 4))
        ctk.CTkLabel(search_row, text="🔍").pack(side="left", padx=(0, 6))
        entry_buscar = ctk.CTkEntry(search_row,
                                    placeholder_text=tr("Buscar por nombre, sujeto, estética…"),
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
            prefs_act = self.app.store.cargar_preferencias()
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
                    ver = GPromptWindow(self.app)
                    ver.title(f"📋 {item_l.get('nombre', 'ADN')}")
                    ver.geometry("620x520")
                    ver.transient(self.app)

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
                            if hasattr(self.app, "txt_idea") and txt_libre:
                                self.app.txt_idea.delete("1.0", "end")
                                self.app.txt_idea.insert("1.0", txt_libre)
                            ver.destroy()
                            self.app.dialogs.set_estado(f"🧬 '{nombre_l}' cargado en idea (texto libre)",
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
                        if hasattr(self.app, "txt_idea"):
                            self.app.txt_idea.delete("1.0", "end")
                            self.app.txt_idea.insert("1.0", prompt)
                        ver.destroy()
                        self.app.dialogs.set_estado(f"🧬 '{nombre_l}' cargado en idea ({len(partes)} campos)",
                                        "#2ecc71")

                    btn_frame2 = ctk.CTkFrame(ver, fg_color="transparent")
                    btn_frame2.pack(pady=(0, 10))
                    ctk.CTkButton(btn_frame2, text=tr("🎯 Usar en idea"),
                                  command=_usar_en_idea).pack(side="left", padx=5)
                    ctk.CTkButton(btn_frame2, text=tr("Cerrar"),
                                  command=ver.destroy).pack(side="left", padx=5)

                def _borrar(idx_l=idx, nombre_l=nombre):
                    from tkinter import messagebox
                    if not messagebox.askyesno("Eliminar",
                                               f"¿Borrar '{nombre_l}'?",
                                               parent=vent):
                        return
                    prefs_b = self.app.store.cargar_preferencias()
                    lst = prefs_b.get("adns_guardados", [])
                    if 0 <= idx_l < len(lst):
                        lst.pop(idx_l)
                        prefs_b["adns_guardados"] = lst
                        self.app.store.guardar_preferencias(prefs_b)
                    _refrescar()  # FIX: antes vent.destroy() cerraba la ventana
                    self.app.dialogs.set_estado(f"🧬 '{nombre_l}' eliminado", "#e67e22")

                ctk.CTkButton(btn_frame, text=tr("👁 Ver"), width=70, height=25,
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
            if not getattr(self.app, "imagen_cargada", None):
                self.app.dialogs.set_estado(
                    tr("⚠️ Carga una imagen en la pantalla principal y vuelve."),
                    "#e67e22",
                )
                return
            vent.destroy()
            # _cmd_adn_visual abre su propio modal con botón "💾 Guardar".
            self._cmd_adn_visual()

        ctk.CTkButton(accion_frame, text=tr("➕ Crear nuevo ADN"),
                      width=180, height=28, fg_color="#1a5a8a",
                      command=_crear_nuevo_adn).pack(side="left", padx=4)
        ctk.CTkButton(accion_frame, text=tr("🔄 Refrescar"), width=110, height=28,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                      command=_refrescar).pack(side="left", padx=4)
        ctk.CTkButton(accion_frame, text=tr("Cerrar"), width=110, height=28,
                      command=vent.destroy).pack(side="left", padx=4)

    def _cmd_adn_visual(self):
        """Extrae ADN visual JSON estructurado de la imagen cargada."""
        if not hasattr(self.app, 'imagen_cargada') or not self.app.imagen_cargada:
            return self.app.dialogs.set_estado(tr("⚠️ Carga una imagen primero."), "#e67e22")

        self.app.dialogs.set_estado(tr("🧬 Extrayendo ADN visual..."), "#9b59b6")
        self.app.dialogs.toggle_botones(False)

        def _worker():
            try:
                def on_status(msg):
                    self.app.after(0, lambda: self.app.dialogs.set_estado(f"🧬 {msg}", "#9b59b6"))

                adn, motor = self.app.vision.analizar_adn(self.app.imagen_cargada, on_status)

                def _mostrar():
                    is_lt = ctk.get_appearance_mode().lower() == "light"
                    c = get_theme_colors(is_lt)

                    vent = GPromptWindow(self.app)
                    vent.title(tr("🧬 ADN Visual - Análisis estructurado"))
                    vent.geometry("700x650")
                    vent.transient(self.app)

                    ctk.CTkLabel(vent, text=tr("🧬 ADN Visual de tu imagen"),
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
                        estado_lbl = ctk.CTkLabel(hdr, text=tr("🔓 DESBLOQUEADO"), text_color="#27ae60", font=ctk.CTkFont(size=9))
                        estado_lbl.pack(side="left", padx=(2, 0))
                        bloqueos[cat_key]["label"] = estado_lbl

                        ctk.CTkLabel(hdr, text=cat_nombre, font=ctk.CTkFont(weight="bold")).pack(side="left")

                        # Contenido de la categoría
                        if isinstance(datos, dict):
                            for k, v in datos.items():
                                if v:
                                    txt = f"  {k}: {v}"
                                    ctk.CTkLabel(cat_frame, text=txt, font=ctk.CTkFont(size=10),
                                                 text_color=c.get("fg_dark_text", "#ffffff"),
                                                 anchor="w").pack(anchor="w", padx=12, pady=1)
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
                        json_str = json.dumps(adn, indent=2, ensure_ascii=False)
                        pyperclip.copy(json_str)
                        self.app.dialogs.set_estado(tr("🧬 JSON copiado"), "#2ecc71")

                    def _aplicar_partes_a_idea(partes, mensaje_ok):
                        """Helper compartido: junta partes y las añade al
                        txt_idea (en lugar de reemplazar). Devuelve True si
                        se aplicó algo."""
                        prompt = ", ".join([p for p in partes if p])
                        if not prompt:
                            return False
                        existente = self.app.txt_idea.get("1.0", "end").strip()
                        nuevo = f"{existente}\n\n{prompt}" if existente else prompt
                        self.app.txt_idea.delete("1.0", "end")
                        self.app.txt_idea.insert("1.0", nuevo)
                        vent.destroy()
                        self.app.dialogs.set_estado(mensaje_ok, "#2ecc71")
                        return True

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

                        # Construir mensaje de status según bloqueos
                        cats_excluidas = [cat for cat in
                                          ("sujeto", "escena", "iluminacion", "camara",
                                           "estilo", "atmosfera", "composicion", "tecnico")
                                          if bloqueos.get(cat, {}).get("bloqueado", False)]
                        if cats_excluidas:
                            msg_ok = f"🧬 Idea (bloqueados: {', '.join(cats_excluidas)})"
                        else:
                            msg_ok = "🧬 ADN en idea - pulsa Generar"

                        if not _aplicar_partes_a_idea(partes, msg_ok):
                            self.app.dialogs.set_estado(tr("⚠️ ADN vacío, no hay datos para convertir"), "#e67e22")

                    def _guardar_adn():
                        from tkinter import simpledialog

                        # Cargar ADNs primero para poder usar len(adns)
                        prefs = self.app.store.cargar_preferencias()
                        adns = prefs.get("adns_guardados", [])

                        # Generar sugerencia de nombre basada en el ADN
                        sujeto = adn.get("sujeto", {})
                        estilo = adn.get("estilo", {})
                        estetica = estilo.get("estetica", "") if isinstance(estilo, dict) else ""

                        sugerencia = f"ADN {estetica[:20] if estetica else 'visual'} {len(adns)+1}"

                        nombre = simpledialog.askstring("💾 Guardar ADN", "Nombre para el ADN:",
                                                          initialvalue=sugerencia)
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
                        self.app.store.guardar_preferencias(prefs)
                        self.app.dialogs.set_estado(f"🧬 ADN '{nombre}' guardado", "#2ecc71")

                    ctk.CTkButton(btn_frame, text=tr("📋 Copiar JSON"), width=110, height=30,
                                  command=_copiar_json).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text=tr("🎯 Usar en prompt"), width=130, height=30,
                                  fg_color="#1a7a3c", command=_usar_en_prompt).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text=tr("💾 Guardar ADN"), width=110, height=30,
                                  command=_guardar_adn).pack(side="left", padx=4)
                    ctk.CTkButton(btn_frame, text=tr("📚 Mi biblioteca"), width=130, height=30,
                                  fg_color="#4a1a6a", hover_color="#3a1050",
                                  command=self._cmd_ver_biblioteca_adn
                                  ).pack(side="left", padx=4)

                    # Botones de conversión por plataforma
                    plat_frame = ctk.CTkFrame(vent, fg_color="transparent")
                    plat_frame.pack(pady=(8, 0))

                    lbl_plat = ctk.CTkLabel(plat_frame, text=tr("🎨 Convertir a:"), font=ctk.CTkFont(size=11))
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

                        # Status según resultado
                        cats_bloqueadas = [cat for cat in bloqueos
                                            if bloqueos.get(cat, {}).get("bloqueado", False)]
                        if cats_bloqueadas:
                            msg = f"🧬 {plataforma} (bloqueados: {', '.join(cats_bloqueadas[:3])}{'...' if len(cats_bloqueadas) > 3 else ''})"
                            color_ok = "#2ecc71"
                        elif fallos:
                            msg = f"🧬 {plataforma} - parcial (falló: {', '.join(fallos)})"
                            color_ok = "#f39c12"
                        else:
                            msg = f"🧬 {plataforma} en idea"
                            color_ok = "#2ecc71"

                        if not _aplicar_partes_a_idea(partes, msg):
                            self.app.dialogs.set_estado(f"❌ Conversión {plataforma} falló completamente",
                                            "#e74c3c")
                        elif fallos:
                            # Sobrescribir color si hubo fallos parciales
                            self.app.dialogs.set_estado(msg, color_ok)

                    for plat in ["midjourney", "stable_diffusion", "dalle", "flux"]:
                        ctk.CTkButton(plat_frame, text=plat.replace("_", " ").upper(), width=80, height=24,
                                      font=ctk.CTkFont(size=9),
                                      command=lambda p=plat: _convertir_plataforma(p)).pack(side="left", padx=2)

                    ctk.CTkButton(vent, text=tr("Cerrar"), width=100, height=28,
                                  command=vent.destroy).pack(pady=(5, 12))

                    self.app.dialogs.toggle_botones(True)
                    self.app.dialogs.set_estado(f"🧬 ADN extraído ({motor})", "#2ecc71")

                self.app.after(0, _mostrar)

            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(f"❌ Error ADN: {e}", "#e74c3c"))
                self.app.after(0, lambda: self.app.dialogs.toggle_botones(True))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)
