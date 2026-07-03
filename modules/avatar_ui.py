"""
AVATAR_UI — Pestaña de customtkinter del modo Avatar
====================================================
Frame autocontenido. Puede:
  a) Ejecutarse en standalone para probar:  python avatar_ui.py
  b) Integrarse como pestaña/modo en app.py de Arquitecto de Prompts.

NOTA PARA INTEGRACIÓN (Claude Code):
- AvatarFrame recibe `llm_call` (la función de backend LLM que ya existe
  en workers.py) y opcionalmente `carpeta_salida_default`.
- La generación se lanza en un hilo para no bloquear la UI, siguiendo el
  mismo patrón de workers.py. Si la app ya tiene su sistema de workers,
  sustituir threading.Thread por ese sistema.
"""

import threading
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

import customtkinter as ctk

try:
    from CTkToolTip import CTkToolTip
except ImportError:
    class CTkToolTip:
        def __init__(self, *args, **kwargs): pass

from modules import paleta as P
from modules.avatar_config import (
    LORA_TYPES,
)
from modules.avatar_generator import exportar_dataset, generar_dataset_lora
from modules.avatar_prompts import (
    PROMPT_VISION_FICHA,
    construir_user_prompt_ficha,
    construir_user_prompt_ficha_tipo,
    parsear_ficha_json,
    system_prompt_ficha_para_tipo,
)
from modules.i18n import tr, tr_es
from workers import log_future_exc


def _norm_opcion(s: str) -> str:
    """Normaliza para comparar opciones de combo: sin acentos, minúsculas y
    espacios colapsados (p.ej. 'Fotografía' == 'fotografia ')."""
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


class AvatarFrame(ctk.CTkFrame):
    def __init__(self, master, llm_call, carpeta_salida_default=".",
                 adaptador=None, modelo_destino="", modelos_destino=None,
                 plataformas_destino=None,
                 vision_call=None, executor=None, **kwargs):
        """adaptador: callable(resultado, modelo) -> list[str] de avisos.
        Se aplica tras generar y antes de exportar (adaptación al modelo).
        modelo_destino: modelo inicial seleccionado en el desplegable.
        modelos_destino: lista plana de modelos (modo legacy/standalone).
        plataformas_destino: dict {plat: [(grupo, [modelos])]} para el
        selector en tres niveles plataforma→grupo→modelo.
        vision_call: callable(imagen_pil, prompt) -> str. Si se pasa,
        aparece el botón "📷 Desde imagen" que rellena la ficha
        analizando una imagen de referencia.
        executor: concurrent.futures.Executor opcional para lanzar hilos
        de fondo sin crear threading.Thread manualmente."""
        super().__init__(master, **kwargs)
        self._executor = executor
        self.llm_call = llm_call
        self.carpeta_salida = carpeta_salida_default
        self.adaptador = adaptador
        self.modelo_destino = modelo_destino
        self.modelos_destino = modelos_destino or []
        self.plataformas_destino = plataformas_destino or {}
        self.vision_call = vision_call
        self._imagen_referencia = ""   # ruta de la imagen usada para la ficha
        self._campos = {}
        self._angulo_vars = {}
        self._tipo_lora = "Personaje"  # tipo activo
        self._frame_form = None        # ref al scrollable de formulario
        self._frame_angulos = None     # ref al scrollable de ángulos
        self._construir_ui()

    # ------------------------------------------------------------------ UI
    def _construir_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Fila 0 — Título
        titulo = ctk.CTkLabel(
            self, text=tr("🧑‍🎨 Generador de Dataset LoRA"),
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        titulo.grid(row=0, column=0, columnspan=2, pady=(12, 2), sticky="n")

        # Fila 1 — Selector de tipo de LoRA
        fila_tipo = ctk.CTkFrame(self, fg_color="transparent")
        fila_tipo.grid(row=1, column=0, columnspan=2, pady=(0, 4), sticky="n")
        ctk.CTkLabel(fila_tipo, text=tr("Tipo de LoRA:"),
                     font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold")).pack(side="left", padx=(0, 8))
        # El segmented muestra la traducción; el mapa recupera el tipo ES
        # ("Personaje"...) que es la clave de LORA_TYPES.
        self._tipo_disp2key = {
            tr(v): v.split(" ", 1)[1]
            for v in ("🧑 Personaje", "🏔 Paisaje", "📦 Objeto", "🎨 Estilo")
        }
        self._seg_tipo = ctk.CTkSegmentedButton(
            fila_tipo,
            values=list(self._tipo_disp2key),
            command=self._on_tipo_change,
            font=ctk.CTkFont(size=P.FUENTE_SECCION),
        )
        self._seg_tipo.set(tr("🧑 Personaje"))
        self._seg_tipo.pack(side="left")

        # Selector de modelo destino: el dataset se adapta a sus specs
        if self.plataformas_destino:
            fila_modelo = ctk.CTkFrame(self, fg_color="transparent")
            fila_modelo.grid(row=1, column=0, columnspan=2, pady=(32, 0), sticky="n")

            plat_ini, grupo_ini = self._encontrar_plataforma_grupo(self.modelo_destino)
            plats = list(self.plataformas_destino.keys())

            ctk.CTkLabel(fila_modelo, text="🌐",
                         font=ctk.CTkFont(size=P.FUENTE_SECCION)).pack(side="left", padx=(0, 2))
            self.menu_plataforma = ctk.CTkOptionMenu(
                fila_modelo, values=plats, width=145,
                command=self._on_plataforma_change,
                font=ctk.CTkFont(size=P.FUENTE_CUERPO))
            self.menu_plataforma.set(plat_ini)
            self.menu_plataforma.pack(side="left", padx=(0, 10))

            ctk.CTkLabel(fila_modelo, text="📁",
                         font=ctk.CTkFont(size=P.FUENTE_SECCION)).pack(side="left", padx=(0, 2))
            # El combo muestra el grupo traducido; los lookups des-traducen
            # con tr_es() (los nombres de grupo son claves ES de los datos).
            grupos_ini = [tr(g) for g, _ in self.plataformas_destino.get(plat_ini, [])]
            self.menu_grupo = ctk.CTkOptionMenu(
                fila_modelo, values=grupos_ini or [""],
                width=210, command=self._on_grupo_change,
                font=ctk.CTkFont(size=P.FUENTE_CUERPO))
            self.menu_grupo.set(tr(grupo_ini) if tr(grupo_ini) in grupos_ini
                                else (grupos_ini[0] if grupos_ini else ""))
            self.menu_grupo.pack(side="left", padx=(0, 10))

            ctk.CTkLabel(fila_modelo, text="🎯",
                         font=ctk.CTkFont(size=P.FUENTE_SECCION)).pack(side="left", padx=(0, 2))
            modelos_ini = self._get_modelos_grupo(plat_ini, self.menu_grupo.get())
            inicial_m = (self.modelo_destino if self.modelo_destino in modelos_ini
                         else (modelos_ini[0] if modelos_ini else ""))
            self.menu_modelo = ctk.CTkOptionMenu(
                fila_modelo, values=modelos_ini or [""], width=220,
                font=ctk.CTkFont(size=P.FUENTE_CUERPO))
            self.menu_modelo.set(inicial_m)
            self.menu_modelo.pack(side="left")

        elif self.modelos_destino:
            fila_modelo = ctk.CTkFrame(self, fg_color="transparent")
            fila_modelo.grid(row=1, column=0, columnspan=2, pady=(32, 0), sticky="n")
            ctk.CTkLabel(
                fila_modelo, text=tr("🎯 Modelo destino:"),
                font=ctk.CTkFont(size=P.FUENTE_CUERPO, weight="bold"),
            ).pack(side="left", padx=(0, 6))
            inicial = (self.modelo_destino
                       if self.modelo_destino in self.modelos_destino
                       else self.modelos_destino[0])
            self.menu_modelo = ctk.CTkOptionMenu(
                fila_modelo, values=self.modelos_destino, width=260)
            self.menu_modelo.set(inicial)
            self.menu_modelo.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(
                fila_modelo,
                text=tr("(negative y límite de chars según sus specs)"),
                font=ctk.CTkFont(size=P.FUENTE_PEQUENA), text_color="#9ca3af",
            ).pack(side="left")
        else:
            self.menu_modelo = None

        # --- Columna izquierda: formulario dinámico ---
        cfg = LORA_TYPES[self._tipo_lora]
        form = ctk.CTkScrollableFrame(self, label_text=tr(cfg["label_form"]))
        form.grid(row=2, column=0, padx=(12, 6), pady=6, sticky="nsew")
        self._frame_form = form

        self._poblar_form(form, cfg)

        # --- Columna derecha: ángulos dinámicos ---
        angulos = ctk.CTkScrollableFrame(self, label_text=tr(cfg["label_angles"]))
        angulos.grid(row=2, column=1, padx=(6, 12), pady=6, sticky="nsew")
        self._frame_angulos = angulos
        self._poblar_angulos(cfg)

        # --- Pie: botón y estado ---
        pie = ctk.CTkFrame(self, fg_color="transparent")
        pie.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 12))
        pie.grid_columnconfigure(0, weight=1)

        self.label_estado = ctk.CTkLabel(pie, text=tr("Listo."))
        self.label_estado.grid(row=0, column=0, sticky="w")

        self.boton_generar = ctk.CTkButton(
            pie, text=tr("⚡ Generar dataset"), command=self._on_generar)
        self.boton_generar.grid(row=0, column=1, padx=(8, 0))

    # ----------------------------------------------------------- tipo LoRA
    def _on_tipo_change(self, valor: str) -> None:
        # "🧑 Character" (display) → "Personaje" (clave de LORA_TYPES)
        tipo = self._tipo_disp2key.get(
            valor, valor.split(" ", 1)[1] if " " in valor else valor)
        self._tipo_lora = tipo
        self._imagen_referencia = ""
        cfg = LORA_TYPES[tipo]

        # Reconstruir form
        self._frame_form.configure(label_text=tr(cfg["label_form"]))
        for w in self._frame_form.winfo_children():
            w.destroy()
        self._campos = {}
        self._poblar_form(self._frame_form, cfg)

        # Reconstruir ángulos
        self._frame_angulos.configure(label_text=tr(cfg["label_angles"]))
        for w in self._frame_angulos.winfo_children():
            w.destroy()
        self._angulo_vars = {}
        self._poblar_angulos(cfg)

    def _poblar_form(self, form, cfg: dict) -> None:
        """Rellena el scrollable frame del formulario según el cfg del tipo."""
        fila = 0
        form.grid_columnconfigure(0, weight=1)

        # Ficha automática
        ctk.CTkLabel(form,
                     text=tr("🎲 Ficha automática — tema opcional (vacío = aleatorio)")
                     ).grid(row=fila, column=0, sticky="w", padx=8, pady=(8, 0)); fila += 1
        fila_auto = ctk.CTkFrame(form, fg_color="transparent")
        fila_auto.grid(row=fila, column=0, sticky="ew", padx=8, pady=(0, 8)); fila += 1
        fila_auto.grid_columnconfigure(0, weight=1)
        self.entry_tema = ctk.CTkEntry(
            fila_auto, placeholder_text=tr("ej: guerrera élfica, volcán japonés, reloj steampunk…"))
        self.entry_tema.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.boton_auto = ctk.CTkButton(
            fila_auto, text=tr("🎲 Generar ficha"), width=130,
            **P.estilo_boton(P.BTN_ACENTO),
            command=self._on_ficha_auto)
        self.boton_auto.grid(row=0, column=1)

        # Imagen de referencia — solo si el tipo lo admite
        if cfg.get("tiene_imagen_ref") and self.vision_call:
            self.boton_imagen = ctk.CTkButton(
                fila_auto, text=tr("📷 Desde imagen"), width=120,
                **P.estilo_boton(P.BTN_SECUNDARIO),
                command=self._on_ficha_desde_imagen)
            self.boton_imagen.grid(row=0, column=2, padx=(6, 0))
        else:
            self.boton_imagen = None

        self.label_imagen_ref = ctk.CTkLabel(
            form, text="", anchor="w", compound="left",
            font=ctk.CTkFont(size=P.FUENTE_PEQUENA), text_color="#9ca3af")
        self.label_imagen_ref.grid(row=fila, column=0, sticky="w",
                                   padx=8, pady=(0, 4)); fila += 1

        # Trigger word
        ctk.CTkLabel(form, text=tr(cfg["label_trigger"])).grid(
            row=fila, column=0, sticky="w", padx=8, pady=(8, 0)); fila += 1
        self.entry_trigger = ctk.CTkEntry(
            form, placeholder_text=tr(cfg["placeholder_trigger"]))
        self.entry_trigger.grid(row=fila, column=0, sticky="ew", padx=8, pady=(0, 8)); fila += 1

        # Campos específicos del tipo
        for campo in cfg["form_fields"]:
            ctk.CTkLabel(form, text=tr(campo["label"])).grid(
                row=fila, column=0, sticky="w", padx=8, pady=(8, 0)); fila += 1
            if campo["type"] == "option":
                widget = ctk.CTkOptionMenu(
                    form, values=[tr(o) for o in campo["options"]])
            else:
                widget = ctk.CTkEntry(
                    form, placeholder_text=tr(campo.get("placeholder", "")))
            widget.grid(row=fila, column=0, sticky="ew", padx=8, pady=(0, 4)); fila += 1
            self._campos[campo["key"]] = widget

        # Estilo visual
        ctk.CTkLabel(form, text=tr("Estilo visual")).grid(
            row=fila, column=0, sticky="w", padx=8, pady=(12, 0)); fila += 1
        self.menu_estilo = ctk.CTkOptionMenu(
            form, values=[tr(k) for k in cfg["styles"]])
        self.menu_estilo.grid(row=fila, column=0, sticky="ew", padx=8, pady=(0, 4)); fila += 1

        # Fondo — solo si el tipo tiene fondos
        if cfg.get("backgrounds"):
            ctk.CTkLabel(form, text=tr("Fondo (si NO se varían fondos)")).grid(
                row=fila, column=0, sticky="w", padx=8, pady=(8, 0)); fila += 1
            self.menu_fondo = ctk.CTkOptionMenu(
                form, values=[tr(k) for k in cfg["backgrounds"]])
            self.menu_fondo.grid(row=fila, column=0, sticky="ew", padx=8, pady=(0, 4)); fila += 1

            self.check_variar_fondos = ctk.CTkCheckBox(
                form, text=tr("Variar fondos (recomendado LoRA)"))
            self.check_variar_fondos.select()
            self.check_variar_fondos.grid(
                row=fila, column=0, sticky="w", padx=8, pady=(0, 8)); fila += 1
        else:
            self.menu_fondo = None
            self.check_variar_fondos = None

        self.check_negative = ctk.CTkCheckBox(form, text=tr("Incluir negative prompt"))
        self.check_negative.select()
        self.check_negative.grid(row=fila, column=0, sticky="w", padx=8, pady=(4, 12))

    def _poblar_angulos(self, cfg: dict) -> None:
        """Rellena el scrollable frame de ángulos según el cfg del tipo."""
        fila = 0
        self._frame_angulos.grid_columnconfigure(0, weight=1)

        # Barra de selección rápida: Todos / Ninguno / Equilibrado.
        barra = ctk.CTkFrame(self._frame_angulos, fg_color="transparent")
        barra.grid(row=fila, column=0, sticky="ew", padx=8, pady=(2, 6)); fila += 1
        ctk.CTkButton(barra, text=tr("Todos"), width=58, height=24,
                      command=lambda: self._marcar_angulos(True)).pack(side="left", padx=(0, 4))
        ctk.CTkButton(barra, text=tr("Ninguno"), width=64, height=24,
                      fg_color="#6b7280", hover_color="#4b5563",
                      command=lambda: self._marcar_angulos(False)).pack(side="left", padx=4)
        n_eq = len(cfg.get("balanced_angles") or cfg["angles"])
        boton_eq = ctk.CTkButton(
            barra, text=tr("⚖ Equilibrado ({0})").format(n_eq),
            width=126, height=24, **P.estilo_boton(P.BTN_SECUNDARIO),
            command=self._aplicar_equilibrado)
        boton_eq.pack(side="left", padx=4)
        CTkToolTip(boton_eq, message=tr(
            "Marca la selección recomendada por la guía SeaArt para este tipo "
            "de LoRA (reparto equilibrado, sin sesgar el entrenamiento)."))

        for grupo, titulo_grupo in cfg["angle_groups"].items():
            ctk.CTkLabel(
                self._frame_angulos, text=tr(titulo_grupo),
                font=ctk.CTkFont(weight="bold"),
            ).grid(row=fila, column=0, sticky="w", padx=8, pady=(10, 2)); fila += 1
            for key, datos in cfg["angles"].items():
                if datos["group"] != grupo:
                    continue
                var = ctk.BooleanVar(value=True)
                aviso = datos.get("warn")
                etiqueta = (f"⚠ {tr(datos['label'])}" if aviso
                            else tr(datos["label"]))
                chk = ctk.CTkCheckBox(
                    self._frame_angulos, text=etiqueta, variable=var)
                chk.grid(row=fila, column=0, sticky="w", padx=16, pady=2); fila += 1
                if aviso:
                    CTkToolTip(chk, message=tr(aviso))
                self._angulo_vars[key] = var

    def _marcar_angulos(self, valor: bool) -> None:
        """Marca/desmarca TODOS los checkboxes de ángulo."""
        for v in self._angulo_vars.values():
            v.set(valor)

    def _aplicar_equilibrado(self) -> None:
        """Aplica la selección equilibrada recomendada para el tipo activo."""
        cfg = LORA_TYPES[self._tipo_lora]
        balanced = set(cfg.get("balanced_angles") or cfg["angles"].keys())
        for k, v in self._angulo_vars.items():
            v.set(k in balanced)
        n = sum(1 for v in self._angulo_vars.values() if v.get())
        if hasattr(self, "label_estado"):
            self.label_estado.configure(
                text=tr("⚖ Selección equilibrada aplicada: {0} ángulos").format(n))

    # ------------------------------------------------------------- acciones
    def _on_ficha_auto(self):
        """La IA inventa la ficha (con tema opcional) y rellena el form."""
        tema = self.entry_tema.get().strip()
        tipo = self._tipo_lora
        self.boton_auto.configure(state="disabled")
        self.label_estado.configure(text=tr('🎲 Inventando {0} con la IA…').format(tipo.lower()))

        def _worker():
            try:
                sys_p = system_prompt_ficha_para_tipo(tipo)
                if tipo == "Personaje":
                    user_p = construir_user_prompt_ficha(tema)
                else:
                    user_p = construir_user_prompt_ficha_tipo(tipo, tema)
                try:
                    resp = self.llm_call(sys_p, user_p, temperature=0.9)
                except TypeError:
                    resp = self.llm_call(sys_p, user_p)
                ficha = parsear_ficha_json(resp)
                if not ficha:
                    raise ValueError(tr(
                        "La IA no devolvió una ficha JSON parseable. "
                        "Prueba otra vez (o con otro tema)."))
                self.after(0, lambda: self._aplicar_ficha(ficha))
            except Exception as e:
                self.after(0, lambda e=e: self._fin_ficha_error(str(e)))

        if self._executor is not None:
            self._executor.submit(_worker).add_done_callback(log_future_exc)
        else:
            threading.Thread(target=_worker, daemon=True).start()

    def _on_ficha_desde_imagen(self):
        """Analiza una imagen de referencia con visión y rellena la ficha."""
        import os

        ruta = filedialog.askopenfilename(
            title=tr("Imagen de referencia del personaje"),
            filetypes=[(tr("Imágenes"), "*.png *.jpg *.jpeg *.webp *.bmp"),
                       (tr("Todos"), "*.*")])
        if not ruta:
            return
        nombre = os.path.basename(ruta)
        self.boton_imagen.configure(state="disabled")
        # Feedback INMEDIATO de que la imagen está cargada y en análisis
        self.label_imagen_ref.configure(
            text=tr('  📷 {0} — ⏳ analizando con IA de visión…').format(nombre), image=None)
        self.label_estado.configure(text=tr("📷 Analizando la imagen de referencia…"))

        def _worker():
            try:
                from PIL import Image
                imagen = Image.open(ruta)
                imagen.load()
                if imagen.mode not in ("RGB", "L"):
                    imagen = imagen.convert("RGB")
                # Miniatura para el feedback visual
                thumb = imagen.copy()
                thumb.thumbnail((42, 42))
                resp = self.vision_call(imagen, PROMPT_VISION_FICHA)
                ficha = parsear_ficha_json(resp)
                if not ficha:
                    raise ValueError(tr(
                        "La IA de visión no devolvió una ficha JSON parseable. "
                        "Prueba con otra imagen (mejor un retrato claro)."))
                self._imagen_referencia = ruta

                def _ok():
                    try:
                        ctk_img = ctk.CTkImage(light_image=thumb,
                                               dark_image=thumb,
                                               size=(thumb.width, thumb.height))
                        self.label_imagen_ref.configure(
                            image=ctk_img, text=tr('  📷 {0} ✓ ficha extraída').format(nombre))
                        self.label_imagen_ref._image_ref = ctk_img
                    except Exception:
                        self.label_imagen_ref.configure(
                            text=tr('  📷 {0} ✓ ficha extraída').format(nombre))
                    self._aplicar_ficha(
                        ficha, origen=tr("📷 Ficha extraída de la imagen"))
                self.after(0, _ok)
            except Exception as e:
                def _err(e=e):
                    self.label_imagen_ref.configure(
                        text=tr('  ❌ {0} — no se pudo analizar').format(nombre), image=None)
                    self._fin_ficha_error(str(e))
                self.after(0, _err)

        if self._executor is not None:
            self._executor.submit(_worker).add_done_callback(log_future_exc)
        else:
            threading.Thread(target=_worker, daemon=True).start()

    def _aplicar_ficha(self, ficha: dict, origen: str = "🎲 Ficha generada"):
        """Vuelca la ficha generada en los widgets del formulario."""
        for key, widget in self._campos.items():
            valor = ficha.get(key, "")
            if not valor:
                continue
            if isinstance(widget, ctk.CTkOptionMenu):
                # Aceptar valores del desplegable, tolerante a acentos/espacios
                # (p.ej. el LLM devuelve "fotografia" → opción "Fotografía").
                # El LLM responde en ES; con la UI en EN el combo muestra la
                # traducción, así que se compara también contra tr_es(opción).
                opciones = list(widget.cget("values"))
                vnorm = _norm_opcion(valor)

                def _normas(o):
                    return {_norm_opcion(o), _norm_opcion(tr_es(o))}

                match = next((o for o in opciones
                              if vnorm in _normas(o)), None)
                if not match:  # match parcial (contiene) como último recurso
                    match = next((o for o in opciones
                                  if any(vnorm in n or n in vnorm
                                         for n in _normas(o))), None)
                if match:
                    widget.set(match)
            else:
                widget.delete(0, "end")
                widget.insert(0, valor)
        trigger = ficha.get("trigger", "")
        if trigger:
            self.entry_trigger.delete(0, "end")
            self.entry_trigger.insert(0, trigger)
        self.boton_auto.configure(state="normal")
        if self.boton_imagen:
            self.boton_imagen.configure(state="normal")
        self.label_estado.configure(
            text=tr('{0} — revísala/edítala y pulsa ⚡ Generar dataset.').format(origen))

    def _fin_ficha_error(self, mensaje: str):
        self.boton_auto.configure(state="normal")
        if self.boton_imagen:
            self.boton_imagen.configure(state="normal")
        self.label_estado.configure(text=tr("❌ Error generando la ficha."))
        messagebox.showerror(tr("Error"), mensaje)

    def _on_generar(self):
        trigger = self.entry_trigger.get().strip()
        if not trigger:
            messagebox.showwarning(
                tr("Falta trigger word"),
                tr("Introduce un trigger word (ej: ohwx_ana). Es la palabra que "
                "aprenderá el LoRA para invocar al personaje."))
            return

        seleccionados = [k for k, v in self._angulo_vars.items() if v.get()]
        if not seleccionados:
            messagebox.showwarning(tr("Sin ángulos"), tr("Selecciona al menos un ángulo."))
            return

        carpeta = filedialog.askdirectory(
            title=tr("Carpeta donde exportar el dataset"),
            initialdir=self.carpeta_salida)
        if not carpeta:
            return

        form_data = {}
        for key, widget in self._campos.items():
            form_data[key] = widget.get() if hasattr(widget, "get") else ""

        self.boton_generar.configure(state="disabled")
        self.label_estado.configure(text=tr("Generando descripción canónica con el LLM…"))

        modelo_sel = self.menu_modelo.get() if self.menu_modelo else ""
        if self._executor is not None:
            self._executor.submit(
                self._worker_generar, form_data, trigger, seleccionados, carpeta, modelo_sel
            ).add_done_callback(log_future_exc)
        else:
            threading.Thread(
                target=self._worker_generar,
                args=(form_data, trigger, seleccionados, carpeta, modelo_sel),
                daemon=True).start()

    def _worker_generar(self, form_data, trigger, seleccionados, carpeta,
                        modelo_sel=""):
        try:
            cfg = LORA_TYPES[self._tipo_lora]
            # Fondo: lista rotante si tiene fondos y "Variar fondos" marcado
            if cfg.get("backgrounds") and self.check_variar_fondos and self.check_variar_fondos.get():
                fondo = cfg["backgrounds_rotacion"]
            elif cfg.get("backgrounds") and self.menu_fondo:
                fondo = cfg["backgrounds"][tr_es(self.menu_fondo.get())]
            else:
                fondo = None

            estilo_sufijo = cfg["styles"].get(tr_es(self.menu_estilo.get()), "")

            resultado = generar_dataset_lora(
                tipo=self._tipo_lora,
                llm_call=self.llm_call,
                form_data=form_data,
                trigger_word=trigger,
                angulos_seleccionados=seleccionados,
                estilo_sufijo=estilo_sufijo,
                fondo=fondo,
                incluir_negative=bool(self.check_negative.get()),
            )
            # Si hay imagen de referencia → generar TAMBIÉN los prompts
            # de edición img2img (la identidad la aporta la imagen).
            if self._imagen_referencia:
                from modules.avatar_prompts import ensamblar_dataset_edicion
                resultado["dataset_edicion"] = ensamblar_dataset_edicion(
                    trigger_word=trigger,
                    angulos_seleccionados=seleccionados,
                    fondo=fondo,
                    incluir_negative=bool(self.check_negative.get()),
                )
            # Adaptación al modelo destino elegido (specs SeaArt) ANTES
            # de exportar
            avisos = (self.adaptador(resultado, modelo_sel)
                      if self.adaptador else [])
            ruta = exportar_dataset(resultado, carpeta)
            # Copiar la imagen de referencia al dataset: en SeaArt se sube
            # como "sujeto" para anclar la identidad en todos los ángulos.
            if self._imagen_referencia:
                try:
                    import os
                    import shutil
                    ext = os.path.splitext(self._imagen_referencia)[1] or ".png"
                    shutil.copy2(self._imagen_referencia,
                                 os.path.join(ruta, f"referencia{ext}"))
                except Exception:
                    pass  # la copia es un extra; no rompe la exportación
            self.after(0, lambda: self._fin_ok(resultado, ruta, avisos))
        except Exception as e:
            # lambda e=e: Python hace `del e` al salir del except — sin la
            # captura, el callback diferido lanza NameError (patrón sesión 10)
            self.after(0, lambda e=e: self._fin_error(str(e)))

    # ── Helpers selector plataforma/grupo/modelo ──────────────────────
    def _get_modelos_grupo(self, plataforma: str, grupo: str) -> list:
        grupo = tr_es(grupo)  # el combo puede mostrar el nombre traducido
        for g, ms in self.plataformas_destino.get(plataforma, []):
            if g == grupo:
                return list(ms)
        return []

    def _encontrar_plataforma_grupo(self, modelo: str) -> tuple:
        for plat, grupos in self.plataformas_destino.items():
            for grupo, modelos in grupos:
                if modelo in modelos:
                    return plat, grupo
        plat = next(iter(self.plataformas_destino), "")
        grupos = self.plataformas_destino.get(plat, [])
        return plat, (grupos[0][0] if grupos else "")

    def _on_plataforma_change(self, plat: str) -> None:
        grupos = self.plataformas_destino.get(plat, [])
        nombres = [tr(g) for g, _ in grupos]
        self.menu_grupo.configure(values=nombres or [""])
        nuevo = nombres[0] if nombres else ""
        self.menu_grupo.set(nuevo)
        self._on_grupo_change(nuevo)

    def _on_grupo_change(self, grupo: str) -> None:
        plat = self.menu_plataforma.get()
        modelos = self._get_modelos_grupo(plat, grupo)
        self.menu_modelo.configure(values=modelos or [""])
        self.menu_modelo.set(modelos[0] if modelos else "")

    def _fin_ok(self, resultado, ruta, avisos=None):
        self.boton_generar.configure(state="normal")
        self.label_estado.configure(
            text=tr('✅ {0} prompts exportados.').format(resultado['total_prompts']))
        mensaje = tr("Descripción canónica:\n\n{0}\n\nExportado en:\n{1}").format(
            resultado['descripcion_canonica'], ruta)
        if resultado.get("dataset_edicion"):
            mensaje += tr(
                "\n\n📷 Incluye prompts_edicion/ (img2img): sube "
                "referencia.* como SUJETO en MAI / Nano Banana / Reve y "
                "pega esos prompts — la identidad la ancla tu imagen.")
        if avisos:
            mensaje += "\n\n" + "\n\n".join(avisos)
        messagebox.showinfo(tr("Dataset generado"), mensaje)

    def _fin_error(self, mensaje):
        self.boton_generar.configure(state="normal")
        self.label_estado.configure(text=tr("❌ Error en la generación."))
        messagebox.showerror(tr("Error"), mensaje)


# ---------------------------------------------------------------------------
# Integración con G-Prompt Studio (sesión 19)
# Se abre como ventana desde el menú 🛠 Herramientas, NO como 4º modo:
# los modos imagen/vídeo/audio tienen demasiada lógica acoplada
# (_on_modo_cambio, footer, tabs) y el doc de integración pide
# explícitamente no tocar esos modos.
# ---------------------------------------------------------------------------
def abrir_avatar_window(app) -> None:
    """Abre el generador de datasets de avatar en una GPromptWindow.

    El LLM se conecta a generar_batch (one-shot, sin contaminar el
    historial de conversación) con temperatura baja: la descripción
    canónica debe ser determinista y repetible.
    """
    from pathlib import Path

    from modules.gprompt_window import GPromptWindow

    try:
        app._sesion_log("🧑‍🎨 Abrió Avatar dataset (LoRA)")
    except Exception:
        pass

    def _llm_call(system_prompt: str, user_prompt: str,
                  temperature: float = 0.3) -> str:
        # T=0.3 para la descripción canónica (determinista); la ficha
        # automática pide T=0.9 para variedad.
        return app.deepseek.generar_batch(
            system_prompt, user_prompt, temperature=temperature, max_tokens=900)

    # Selector de modelo destino: organizado por plataforma y grupo.
    # El adaptador resuelve specs del modelo elegido al generar.
    modelo_activo = ""
    plataformas_destino = {}
    adaptador = None
    try:
        from config import (
            GRUPOS_DALLE_IMAGEN,
            GRUPOS_IMAGEN_VIGENTES,
            get_image_model_specs,
        )
        from modules.avatar_generator import adaptar_dataset_a_modelo

        plataformas_destino = {
            "SeaArt": GRUPOS_IMAGEN_VIGENTES,
            "ChatGPT / GPT Image": GRUPOS_DALLE_IMAGEN,
        }
        modelo_activo = app.footer.modelo_imagen_valido() or ""

        def adaptador(resultado, modelo):
            if not modelo:
                return []
            specs = get_image_model_specs(modelo) or {}
            return adaptar_dataset_a_modelo(resultado, modelo, specs)
    except Exception:
        plataformas_destino = {}
        adaptador = None

    vent = GPromptWindow(app)
    vent.title(tr("🧑‍🎨 Avatar dataset (LoRA)"))
    vent.geometry("920x720")
    vent.transient(app)

    # Visión para "📷 Desde imagen": cadena Gemini→Ollama→OpenRouter de
    # la app con el prompt custom de ficha. None si no hay visión.
    vision_call = None
    try:
        if getattr(app, "vision", None) and app.vision.proveedores:
            def vision_call(imagen_pil, prompt):
                return app.vision.describir_con_prompt(imagen_pil, prompt)[0]
    except Exception:
        vision_call = None

    frame = AvatarFrame(
        vent, llm_call=_llm_call,
        carpeta_salida_default=str(Path.home()),
        adaptador=adaptador, modelo_destino=modelo_activo,
        plataformas_destino=plataformas_destino,
        vision_call=vision_call,
        executor=app._executor)
    frame.pack(fill="both", expand=True, padx=4, pady=4)


# ---------------------------------------------------------------------------
# Standalone para probar la UI sin la app principal:  python avatar_ui.py
# Usa un LLM falso; sustituir por el backend real al integrar.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    def _llm_fake(system, user):
        return ("a 28 year old woman with fair mediterranean skin, oval face, "
                "large almond-shaped green eyes, wavy chestnut brown shoulder-length "
                "hair, light freckles, slim athletic build, wearing a plain white "
                "crew-neck t-shirt and blue denim jeans")

    ctk.set_appearance_mode("dark")
    app = ctk.CTk()
    app.title(tr("Avatar Dataset — prueba standalone"))
    app.geometry("900x680")
    frame = AvatarFrame(app, llm_call=_llm_fake)
    frame.pack(fill="both", expand=True)
    app.mainloop()
