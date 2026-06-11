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

from modules.avatar_config import (
    ANGLE_GROUPS,
    AVATAR_ANGLES,
    AVATAR_BACKGROUNDS,
    AVATAR_FORM_FIELDS,
    AVATAR_STYLES,
)
from modules.avatar_generator import exportar_dataset, generar_dataset_avatar


class AvatarFrame(ctk.CTkFrame):
    def __init__(self, master, llm_call, carpeta_salida_default=".",
                 adaptador=None, modelo_destino="", **kwargs):
        """adaptador: callable(resultado) -> list[str] de avisos. Se aplica
        tras generar y antes de exportar (adaptación al modelo destino).
        modelo_destino: nombre del modelo para el label informativo."""
        super().__init__(master, **kwargs)
        self.llm_call = llm_call
        self.carpeta_salida = carpeta_salida_default
        self.adaptador = adaptador
        self.modelo_destino = modelo_destino
        self._campos = {}
        self._angulo_vars = {}
        self._construir_ui()

    # ------------------------------------------------------------------ UI
    def _construir_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        titulo = ctk.CTkLabel(
            self, text="🧑‍🎨 Generador de Dataset de Avatar (LoRA)",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        titulo.grid(row=0, column=0, columnspan=2, pady=(12, 6), sticky="n")

        if self.modelo_destino:
            ctk.CTkLabel(
                self,
                text=f"🎯 Adaptado al modelo activo: {self.modelo_destino} "
                     f"(negative y límite de caracteres según sus specs)",
                font=ctk.CTkFont(size=11),
                text_color="#9ca3af",
            ).grid(row=0, column=0, columnspan=2, pady=(40, 0), sticky="n")

        # --- Columna izquierda: formulario de rasgos ---
        form = ctk.CTkScrollableFrame(self, label_text="Ficha del personaje")
        form.grid(row=1, column=0, padx=(12, 6), pady=6, sticky="nsew")

        fila = 0
        # Trigger word
        ctk.CTkLabel(form, text="Trigger word (LoRA)").grid(
            row=fila, column=0, sticky="w", padx=8, pady=(8, 0)); fila += 1
        self.entry_trigger = ctk.CTkEntry(form, placeholder_text="ej: ohwx_ana")
        self.entry_trigger.grid(row=fila, column=0, sticky="ew", padx=8, pady=(0, 8)); fila += 1

        for campo in AVATAR_FORM_FIELDS:
            ctk.CTkLabel(form, text=campo["label"]).grid(
                row=fila, column=0, sticky="w", padx=8, pady=(8, 0)); fila += 1
            if campo["type"] == "option":
                widget = ctk.CTkOptionMenu(form, values=campo["options"])
            else:
                widget = ctk.CTkEntry(
                    form, placeholder_text=campo.get("placeholder", ""))
            widget.grid(row=fila, column=0, sticky="ew", padx=8, pady=(0, 4)); fila += 1
            self._campos[campo["key"]] = widget
        form.grid_columnconfigure(0, weight=1)

        # Estilo y fondo
        ctk.CTkLabel(form, text="Estilo visual").grid(
            row=fila, column=0, sticky="w", padx=8, pady=(12, 0)); fila += 1
        self.menu_estilo = ctk.CTkOptionMenu(form, values=list(AVATAR_STYLES.keys()))
        self.menu_estilo.grid(row=fila, column=0, sticky="ew", padx=8, pady=(0, 4)); fila += 1

        ctk.CTkLabel(form, text="Fondo (idéntico en todo el dataset)").grid(
            row=fila, column=0, sticky="w", padx=8, pady=(8, 0)); fila += 1
        self.menu_fondo = ctk.CTkOptionMenu(form, values=list(AVATAR_BACKGROUNDS.keys()))
        self.menu_fondo.grid(row=fila, column=0, sticky="ew", padx=8, pady=(0, 8)); fila += 1

        self.check_negative = ctk.CTkCheckBox(form, text="Incluir negative prompt")
        self.check_negative.select()
        self.check_negative.grid(row=fila, column=0, sticky="w", padx=8, pady=(4, 12))

        # --- Columna derecha: ángulos ---
        angulos = ctk.CTkScrollableFrame(self, label_text="Ángulos del dataset")
        angulos.grid(row=1, column=1, padx=(6, 12), pady=6, sticky="nsew")

        fila = 0
        for grupo, titulo_grupo in ANGLE_GROUPS.items():
            ctk.CTkLabel(
                angulos, text=titulo_grupo,
                font=ctk.CTkFont(weight="bold"),
            ).grid(row=fila, column=0, sticky="w", padx=8, pady=(10, 2)); fila += 1
            for key, datos in AVATAR_ANGLES.items():
                if datos["group"] != grupo:
                    continue
                var = ctk.BooleanVar(value=True)
                chk = ctk.CTkCheckBox(angulos, text=datos["label"], variable=var)
                chk.grid(row=fila, column=0, sticky="w", padx=16, pady=2); fila += 1
                self._angulo_vars[key] = var

        # --- Pie: botón y estado ---
        pie = ctk.CTkFrame(self, fg_color="transparent")
        pie.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 12))
        pie.grid_columnconfigure(0, weight=1)

        self.label_estado = ctk.CTkLabel(pie, text="Listo.")
        self.label_estado.grid(row=0, column=0, sticky="w")

        self.boton_generar = ctk.CTkButton(
            pie, text="⚡ Generar dataset", command=self._on_generar)
        self.boton_generar.grid(row=0, column=1, padx=(8, 0))

    # ------------------------------------------------------------- acciones
    def _on_generar(self):
        trigger = self.entry_trigger.get().strip()
        if not trigger:
            messagebox.showwarning(
                "Falta trigger word",
                "Introduce un trigger word (ej: ohwx_ana). Es la palabra que "
                "aprenderá el LoRA para invocar al personaje.")
            return

        seleccionados = [k for k, v in self._angulo_vars.items() if v.get()]
        if not seleccionados:
            messagebox.showwarning("Sin ángulos", "Selecciona al menos un ángulo.")
            return

        carpeta = filedialog.askdirectory(
            title="Carpeta donde exportar el dataset",
            initialdir=self.carpeta_salida)
        if not carpeta:
            return

        form_data = {}
        for key, widget in self._campos.items():
            form_data[key] = widget.get() if hasattr(widget, "get") else ""

        self.boton_generar.configure(state="disabled")
        self.label_estado.configure(text="Generando descripción canónica con el LLM…")

        hilo = threading.Thread(
            target=self._worker_generar,
            args=(form_data, trigger, seleccionados, carpeta),
            daemon=True)
        hilo.start()

    def _worker_generar(self, form_data, trigger, seleccionados, carpeta):
        try:
            resultado = generar_dataset_avatar(
                llm_call=self.llm_call,
                form_data=form_data,
                trigger_word=trigger,
                angulos_seleccionados=seleccionados,
                estilo_sufijo=AVATAR_STYLES[self.menu_estilo.get()],
                fondo=AVATAR_BACKGROUNDS[self.menu_fondo.get()],
                incluir_negative=bool(self.check_negative.get()),
            )
            # Adaptación al modelo destino (specs SeaArt) ANTES de exportar
            avisos = self.adaptador(resultado) if self.adaptador else []
            ruta = exportar_dataset(resultado, carpeta)
            self.after(0, lambda: self._fin_ok(resultado, ruta, avisos))
        except Exception as e:
            # lambda e=e: Python hace `del e` al salir del except — sin la
            # captura, el callback diferido lanza NameError (patrón sesión 10)
            self.after(0, lambda e=e: self._fin_error(str(e)))

    def _fin_ok(self, resultado, ruta, avisos=None):
        self.boton_generar.configure(state="normal")
        self.label_estado.configure(
            text=f"✅ {resultado['total_prompts']} prompts exportados.")
        mensaje = (
            f"Descripción canónica:\n\n{resultado['descripcion_canonica']}\n\n"
            f"Exportado en:\n{ruta}")
        if avisos:
            mensaje += "\n\n" + "\n\n".join(avisos)
        messagebox.showinfo("Dataset generado", mensaje)

    def _fin_error(self, mensaje):
        self.boton_generar.configure(state="normal")
        self.label_estado.configure(text="❌ Error en la generación.")
        messagebox.showerror("Error", mensaje)


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

    def _llm_call(system_prompt: str, user_prompt: str) -> str:
        return app.deepseek.generar_batch(
            system_prompt, user_prompt, temperature=0.3, max_tokens=900)

    # Adaptación al modelo de imagen activo (specs SeaArt auditados):
    # quita el negative si el modelo no lo soporta y avisa si algún
    # prompt excede su max_chars medido. Determinista, sin LLM extra.
    modelo_activo = ""
    adaptador = None
    try:
        from config import get_image_model_specs
        modelo_activo = app.footer.modelo_imagen_valido() or ""
        specs = get_image_model_specs(modelo_activo) if modelo_activo else None
        if specs:
            from modules.avatar_generator import adaptar_dataset_a_modelo

            def adaptador(resultado, _m=modelo_activo, _s=specs):
                return adaptar_dataset_a_modelo(resultado, _m, _s)
        else:
            modelo_activo = ""  # sin specs → sin label ni adaptación
    except Exception:
        modelo_activo = ""

    vent = GPromptWindow(app)
    vent.title("🧑‍🎨 Avatar dataset (LoRA)")
    vent.geometry("920x700")
    vent.transient(app)

    frame = AvatarFrame(
        vent, llm_call=_llm_call,
        carpeta_salida_default=str(Path.home()),
        adaptador=adaptador, modelo_destino=modelo_activo)
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
    app.title("Avatar Dataset — prueba standalone")
    app.geometry("900x680")
    frame = AvatarFrame(app, llm_call=_llm_fake)
    frame.pack(fill="both", expand=True)
    app.mainloop()
