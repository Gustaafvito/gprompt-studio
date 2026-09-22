"""Image-based prompt workspace. Tk is accessed only on the main thread."""
import json
from tkinter import filedialog, messagebox

import customtkinter as ctk

from config import (
    MODELOS_POR_PLATAFORMA_IMAGEN,
    MODELOS_POR_PLATAFORMA_VIDEO,
    get_image_model_specs,
    get_model_specs,
)
from modules.gprompt_window import GPromptWindow
from modules.i18n import tr, tr_es
from modules.visual_brief import (
    MODE_HELP,
    MODES,
    ROLES,
    VISUAL_SYSTEM,
    Reference,
    analysis_input,
    check_attachment,
    filter_models,
    generation_request,
    load_image,
    load_project,
    output_kind,
    parse_visual_result,
    revision_request,
    save_project,
    validate,
    video_direction,
)
from modules.visual_history import VisualHistory


class VisualStudio(ctk.CTkToplevel):
    # Cuantos paneles se han abierto en esta sesion. Solo sirve para dar a
    # cada uno un identificador estable con el que titular sus ventanas.
    _contador_paneles = 0

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        # A transient dialog loses minimize/maximize controls on Windows.
        # The delayed bring_forward() handles focus without changing its style.
        self.resizable(True, True)
        self.title(tr("Crear desde imágenes · G-Prompt Studio") + " · Beta 9")
        self.geometry("1000x820")
        self.minsize(760, 620)
        # Identidad del panel. open_project() abre un VisualStudio NUEVO por
        # cada proyecto, asi que puede haber varios a la vez con una
        # referencia que se llame igual. GPromptWindow deduplica por titulo:
        # sin esto, la vista previa del segundo panel se cerraria sola y
        # enfocaria la del primero, ensenando la imagen equivocada.
        VisualStudio._contador_paneles += 1
        self.panel_id = VisualStudio._contador_paneles
        self.history = VisualHistory()
        self.analysis_stale = False
        self.refs = []
        self.busy = False
        self.closed = False
        self.future = None
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.mode = ctk.StringVar(value=MODES[0])
        self.language = ctk.StringVar(value="Inglés")
        self.aspect = ctk.StringVar(value="9:16")
        self.duration = ctk.StringVar(value="5")
        self.target = ctk.StringVar(value="Imagen")
        self.platform = ctk.StringVar(value="")
        self.model = ctk.StringVar(value="")
        self.reference_use = ctk.StringVar(value="Solo texto")
        self.attachment_confirmed = ctk.BooleanVar(value=False)
        self.status = ctk.StringVar(value=tr("Añade imágenes; el análisis se podrá revisar antes de generar."))
        body = ctk.CTkScrollableFrame(self)
        self.body = body
        body.pack(fill="both", expand=True, padx=12, pady=10)
        ctk.CTkLabel(body, text=tr("Crear desde imágenes"), font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w")
        # Sin variable=: CTkOptionMenu escribiria el texto MOSTRADO dentro de
        # self.mode y en ingles reventaria cada self.mode.get() == MODES[n].
        # Se pinta traducido y mode_changed() guarda el identificador.
        self.mode_menu = ctk.CTkOptionMenu(body, values=[tr(m) for m in MODES],
                          command=self.mode_changed, width=260)
        self.mode_menu.set(tr(self.mode.get()))
        self.mode_menu.pack(anchor="w", pady=8)
        self.help_label = ctk.CTkLabel(body, text=tr(MODE_HELP[self.mode.get()]),
                                     wraplength=700, justify="left")
        self.help_label.pack(anchor="w")
        bar = ctk.CTkFrame(body)
        bar.pack(fill="x", pady=6)
        ctk.CTkButton(bar, text=tr("Añadir imágenes"), command=self.add).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(bar, text=tr("Usar imagen cargada"), command=self.use_current).pack(side="left", padx=5)
        self.swap_button = ctk.CTkButton(bar, text=tr("Intercambiar A / B"), command=self.swap)
        self.cards = ctk.CTkFrame(body)
        self.cards.pack(fill="x")
        self.project_name = self.entry(body, "Nombre del proyecto (para reconocerlo en versiones)")
        self.idea = self.text_field(body, "Tu idea / acción deseada", 70)
        self.preserve = self.entry(body, "Conservar (ej.: rostro, ropa, forma del producto)")
        self.change = self.entry(body, "Cambiar (ej.: fondo, pose, iluminación)")
        destination = ctk.CTkFrame(body)
        destination.pack(fill="x", pady=8)
        self.target_menu = ctk.CTkOptionMenu(destination, values=[tr("Imagen"), tr("Vídeo")],
                                            command=self.target_changed)
        self.target_menu.pack(anchor="w", padx=5, pady=4)
        self.platform_menu = ctk.CTkOptionMenu(destination, variable=self.platform, values=[""],
                                              command=lambda _: self.refresh_models(), width=260)
        self.platform_menu.pack(anchor="w", padx=5, pady=4)
        self.model_search = ctk.StringVar(value="")
        search_bar = ctk.CTkFrame(destination)
        search_bar.pack(fill="x", padx=5, pady=4)
        ctk.CTkEntry(search_bar, textvariable=self.model_search,
                     placeholder_text=tr("Buscar modelo… (ej.: flux, z-image, kling)")).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(search_bar, text=tr("Limpiar búsqueda"), width=130,
                      command=lambda: self.model_search.set("")).pack(side="left", padx=5)
        self.model_matches = ctk.CTkLabel(destination, text="", anchor="w")
        self.model_matches.pack(fill="x", padx=5)
        self.model_menu = ctk.CTkOptionMenu(destination, variable=self.model, values=[""], width=500,
                                           command=lambda _: self.reset_confirmation())
        self.model_menu.pack(fill="x", padx=5, pady=4)
        ctk.CTkLabel(destination, text=tr("Cómo usarás el prompt en el generador")).pack(anchor="w", padx=5)
        self.reference_menu = ctk.CTkOptionMenu(destination,
                                               values=[tr("Solo texto"), tr("Adjuntar imágenes")],
                                               command=self.reference_use_changed, width=260)
        self.reference_menu.pack(anchor="w", padx=5, pady=4)
        self.reference_hint = ctk.CTkLabel(destination, text="", wraplength=700, justify="left")
        self.reference_hint.pack(anchor="w", padx=5)
        self.confirm_checkbox = ctk.CTkCheckBox(destination,
            text=tr("He comprobado que este modelo admite estas imágenes en mi panel"),
            variable=self.attachment_confirmed)
        self.reference_use_changed(tr("Solo texto"))
        options = ctk.CTkFrame(body)
        options.pack(fill="x", pady=8)
        def _guardar_identificador(variable):
            # Closure con la variable atada: sin esto, las dos entradas del
            # bucle compartirian la ultima.
            return lambda value: variable.set(tr_es(value))

        for title, variable, values in (
            ("Formato", self.aspect, ["9:16", "16:9", "1:1", "4:5"]),
            ("Idioma prompt", self.language, ["Inglés", "Español"]),
        ):
            # tr(title) y no tr("..."): aqui llega una VARIABLE, que es el
            # mismo punto ciego del candado que tenian text_field/entry.
            ctk.CTkLabel(options, text=tr(title)).pack(side="left", padx=5)
            # Se ensena traducido y se guarda el identificador espanol. El
            # idioma del prompt viaja al modelo tal cual ("IDIOMA DEL PROMPT:
            # Ingles"), y el formato es clave de catalogo: si la variable
            # guardara el texto mostrado, ambos se romperian en ingles.
            # tr()/tr_es() son la identidad para lo que no conocen, asi que
            # "9:16" pasa intacto.
            menu = ctk.CTkOptionMenu(options, values=[tr(v) for v in values],
                                     command=_guardar_identificador(variable),
                                     width=100)
            menu.set(tr(variable.get()))
            menu.pack(side="left")
            # Guardados para sync_menus(): al quitar variable= el widget ya
            # no sigue a la StringVar, asi que hay que ponerlo al dia a mano
            # cuando el valor cambia desde fuera (abrir un proyecto).
            if variable is self.aspect:
                self.aspect_menu = menu
            else:
                self.language_menu = menu
        self.duration_label = ctk.CTkLabel(options, text=tr("Segundos"))
        self.duration_entry = ctk.CTkEntry(options, textvariable=self.duration, width=75)
        ctk.CTkLabel(body, text=tr("Analizar envía las imágenes al proveedor de visión configurado y sus alternativas. "
                     "Generar envía el análisis y tu idea al proveedor de texto. Puede consumir cuota. "
                     "Varias imágenes se comparan juntas en un panel reducido."),
                     wraplength=700, justify="left").pack(anchor="w")
        self.video_controls = ctk.CTkFrame(body)
        ctk.CTkLabel(self.video_controls, text=tr("Dirección de vídeo (opcional)")).pack(anchor="w", padx=5)
        self.camera = self.entry(self.video_controls, "Cámara: fija, acercamiento lento, seguimiento…")
        self.environment_motion = self.entry(self.video_controls, "Entorno: niebla, viento, luces, objetos…")
        self.audio_direction = self.entry(self.video_controls, "Sonido: ambiente; diálogo literal e idioma si lo necesitas")
        self.transition_direction = self.entry(self.video_controls, "Inicio → final: cómo pasar de A a B, sin saltos")
        self.analyze_button = ctk.CTkButton(body, text=tr("1. Analizar imágenes"), command=self.analyze)
        self.analyze_button.pack(anchor="w", pady=8)
        self.analysis = self.text_field(body, "Análisis editable — corrige lo que la IA haya interpretado mal", 150)
        self.generate_button = ctk.CTkButton(body, text=tr("2. Generar prompt"), command=self.generate)
        self.generate_button.pack(anchor="w", pady=8)
        self.output = self.text_field(body, "Prompt positivo", 200)
        self.negative = self.text_field(body, "Prompt negativo (solo si el modelo lo admite)", 85)
        self.notes = self.text_field(body, "Notas de uso (no se copian al prompt)", 85)
        self.revision_instruction = self.entry(body, "Qué mejorar (opcional: más cinematográfico, menos adornos…)")
        self.manual_limit = self.entry(body, "Límite manual de caracteres (vacío = catálogo)")
        revision_bar = ctk.CTkFrame(body)
        revision_bar.pack(fill="x", pady=5)
        ctk.CTkButton(revision_bar, text=tr("Ajustar al límite"), command=lambda: self.revise(True)).pack(side="left", padx=5)
        ctk.CTkButton(revision_bar, text=tr("Mejorar prompt"), command=self.revise).pack(side="left", padx=5)
        self.character_count = ctk.CTkLabel(body, text="")
        self.character_count.pack(anchor="w")
        actions = ctk.CTkFrame(body)
        actions.pack(fill="x", pady=6)
        ctk.CTkButton(actions, text=tr("Copiar resultado"), command=self.copy).pack(side="left", padx=5)
        ctk.CTkButton(actions, text=tr("Llevar a salida principal"), command=self.apply).pack(side="left", padx=5)
        ctk.CTkButton(actions, text=tr("Copiar positivo"), command=self.copy_positive).pack(side="left", padx=5)
        ctk.CTkButton(actions, text=tr("Copiar negativo"), command=self.copy_negative).pack(side="left", padx=5)
        ctk.CTkButton(body, text=tr("Comprobar prompt"), command=self.check_prompt).pack(anchor="w", pady=5)
        project_bar = ctk.CTkFrame(body)
        project_bar.pack(fill="x", pady=5)
        ctk.CTkButton(project_bar, text=tr("Nuevo proyecto"), command=lambda: VisualStudio(self.app)).pack(side="left", padx=5)
        ctk.CTkButton(project_bar, text=tr("Guardar proyecto"), command=self.save).pack(side="left", padx=5)
        ctk.CTkButton(project_bar, text=tr("Abrir proyecto"), command=self.load).pack(side="left", padx=5)
        ctk.CTkButton(project_bar, text=tr("Recuperar versiones"), command=self.recover).pack(side="left", padx=5)
        ctk.CTkLabel(self, textvariable=self.status, wraplength=730, justify="left").pack(fill="x", padx=12, pady=8)
        self.model_search.trace_add("write", lambda *_: self.filter_model_menu())
        self.refresh_destination()
        self.render()
        self.bind("<Control-s>", lambda event: self.save())
        self.after(150, self.bring_forward)
        self.after(500, self.update_character_count)
        self.after(15000, self.autosave_tick)

    def bring_forward(self):
        if self.closed:
            return
        self.lift()
        self.attributes("-topmost", True)
        self.focus_force()
        self.after(300, self.release_topmost)

    def release_topmost(self):
        if not self.closed:
            self.attributes("-topmost", False)

    def refresh_destination(self, preserve_missing=False):
        mode = self.mode.get()
        if mode != MODES[3]:
            self.target.set("Vídeo" if mode in MODES[1:3] else "Imagen")
        self.target_menu.configure(state="normal" if mode == MODES[3] else "disabled")
        self.target_menu.set(tr(self.target.get()))
        kind = output_kind(mode, self.target.get())
        self.catalog = MODELOS_POR_PLATAFORMA_VIDEO if kind == "video" else MODELOS_POR_PLATAFORMA_IMAGEN
        platforms = list(self.catalog)
        self.platform_menu.configure(values=platforms)
        if self.platform.get() not in platforms:
            if preserve_missing:
                self.platform_menu.configure(values=[self.platform.get()] + platforms)
            else:
                self.platform.set(platforms[0])
        self.refresh_models(preserve_missing)
        self.duration_label.pack_forget()
        self.duration_entry.pack_forget()
        self.video_controls.pack_forget()
        self.transition_direction.pack_forget()
        if mode == MODES[2]:
            self.transition_direction.pack(fill="x", pady=4)
        if kind == "video":
            self.video_controls.pack(fill="x", pady=8, before=self.analyze_button)
            self.duration_label.pack(side="left", padx=5)
            self.duration_entry.pack(side="left", padx=5)

    def target_changed(self, value):
        self.target.set(tr_es(value))
        self.refresh_destination()

    def refresh_models(self, preserve_missing=False):
        models = filter_models(self.catalog.get(self.platform.get(), []))
        self.model_search.set("")
        self.model_menu.configure(values=models or [""])
        if self.model.get() not in models:
            if preserve_missing:
                self.model_menu.configure(values=[self.model.get()] + models)
            else:
                self.model.set(models[0] if models else "")
        self.reset_confirmation()
        self.filter_model_menu()

    def filter_model_menu(self):
        models = filter_models(self.catalog.get(self.platform.get(), []), self.model_search.get())
        self.model_menu.configure(values=models or [""],
                                  state="normal" if models and not self.busy else "disabled")
        self.model_matches.configure(text=tr("Coincidencias: {count}. Buscar no cambia el modelo seleccionado.").format(count=len(models)))

    def reset_confirmation(self):
        self.attachment_confirmed.set(False)

    def reference_use_changed(self, value):
        self.reference_use.set(tr_es(value))
        self.reference_menu.set(value)
        self.reset_confirmation()
        self.confirm_checkbox.pack_forget()
        if self.reference_use.get() == "Solo texto":
            self.reference_hint.configure(text=tr("Las imágenes solo sirven para redactar. Copia el texto al generador; no necesita admitir imágenes de entrada."))
        else:
            self.reference_hint.configure(text=tr("La carga de referencias depende de la plataforma, modelo y modo. El catálogo no confirma todas esas combinaciones."))
            self.confirm_checkbox.pack(anchor="w", padx=5, pady=5)

    def refresh_mode_help(self):
        self.help_label.configure(text=tr(MODE_HELP[self.mode.get()]))
        self.swap_button.pack_forget()
        if self.mode.get() == MODES[2]:
            self.swap_button.pack(side="left", padx=5)

    @staticmethod
    def text_field(parent, label, height):
        # tr() AQUÍ y no en cada llamada: el candado de i18n solo mira los
        # literales que van directos a un sink (text=, placeholder_text=…), y
        # aquí llega una variable, así que catorce rótulos en español se
        # colaban sin que saltara nada. Traduciendo en el ayudante se arregla
        # de una vez y quien llama sigue escribiendo el español tal cual.
        ctk.CTkLabel(parent, text=tr(label)).pack(anchor="w", pady=(6, 0))
        widget = ctk.CTkTextbox(parent, height=height)
        widget.pack(fill="x", pady=3)
        return widget

    @staticmethod
    def entry(parent, placeholder):
        # Mismo caso que text_field: el placeholder llegaba sin traducir.
        widget = ctk.CTkEntry(parent, placeholder_text=tr(placeholder))
        widget.pack(fill="x", pady=4)
        return widget

    def close(self):
        if not self.checkpoint() and not messagebox.askyesno(tr("No se pudo guardar"), tr("No se ha guardado la recuperación. ¿Cerrar y perder los cambios?"), parent=self):
            return
        self.closed = True
        if self.future:
            self.future.cancel()
        self.destroy()

    def invalidate(self):
        self.analysis_stale = True
        self.reset_confirmation()
        self.status.set(tr("Referencias modificadas. Vuelve a analizar antes de generar."))

    def sync_menus(self):
        """Pone los tres desplegables al dia con sus variables.

        Hace falta porque los menus van sin `variable=`: si la tuvieran,
        CTkOptionMenu escribiria el texto MOSTRADO dentro de la variable y en
        ingles se romperian las comparaciones con MODES y los proyectos
        guardados. El precio de esa separacion es este metodo: cuando el
        valor cambia desde fuera —abrir un proyecto, sobre todo— el widget no
        se entera solo.

        Sin esto, un proyecto guardado como «Inicio -> final», 16:9 y espanol
        se abria ensenando «Imagen -> prompt», 9:16 e ingles. Lo peor es que
        por dentro el valor era el correcto, asi que el usuario creia estar
        editando algo distinto de lo que iba a generar.
        """
        for menu, variable in ((getattr(self, "mode_menu", None), self.mode),
                               (getattr(self, "aspect_menu", None), self.aspect),
                               (getattr(self, "language_menu", None), self.language)):
            if menu is not None:
                menu.set(tr(variable.get()))

    def mode_changed(self, value):
        # value llega en el idioma de la interfaz; self.mode SIEMPRE guarda
        # el identificador espanol, que es lo que se escribe en el proyecto.
        self.mode.set(tr_es(value))
        if self.busy:
            self.mode.set(self.running_mode)
            self.mode_menu.set(tr(self.running_mode))
            return
        self.invalidate()
        self.refresh_mode_help()
        self.refresh_destination()
        self.render()

    def add(self):
        if self.busy:
            return
        paths = filedialog.askopenfilenames(parent=self, title=tr("Imágenes en orden A, B, C, D"),
                                           filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.bmp")])
        if not paths:
            return
        if len(paths) + len(self.refs) > 4:
            self.status.set(tr("Máximo cuatro imágenes. Quita alguna antes de añadir más."))
            return
        try:
            from pathlib import Path
            additions = [Reference(load_image(p), ROLES[0], Path(p).name) for p in paths]
        except Exception as exc:
            self.status.set(tr("No se pudieron cargar las imágenes: {0}").format(exc))
            return
        if not self.checkpoint():
            return
        self.refs.extend(additions)
        self.invalidate()
        self.render()

    def use_current(self):
        if self.busy:
            return
        image = getattr(self.app, "imagen_cargada", None)
        if image is None or len(self.refs) >= 4:
            self.status.set(tr("Carga una imagen en la app o deja espacio entre las cuatro referencias."))
            return
        image = image.convert("RGB").copy()
        image.thumbnail((1600, 1600))
        if not self.checkpoint():
            return
        self.refs.append(Reference(image, ROLES[0], "Imagen de la app"))
        self.invalidate()
        self.render()

    def swap(self):
        if not self.busy and len(self.refs) >= 2 and self.checkpoint():
            self.refs[0], self.refs[1] = self.refs[1], self.refs[0]
            self.invalidate()
            self.render()

    def remove(self, index):
        if not self.busy and self.checkpoint():
            self.refs.pop(index)
            self.invalidate()
            self.render()

    def role_changed(self, index, role):
        role = tr_es(role)
        if self.busy:
            self.render()
            return
        if not self.checkpoint():
            self.render()
            return
        old = self.refs[index]
        self.refs[index] = Reference(old.image, role, old.name)
        self.invalidate()

    def render(self):
        for child in self.cards.winfo_children():
            child.destroy()
        try:
            validate(self.mode.get(), self.refs)
            count_hint = tr("Referencias listas: {count}").format(count=len(self.refs))
        except ValueError as exc:
            count_hint = str(exc)
        self.help_label.configure(text=tr(MODE_HELP[self.mode.get()]) + "\n" + count_hint)
        for i, ref in enumerate(self.refs):
            row = ctk.CTkFrame(self.cards)
            row.pack(fill="x", pady=3)
            ratio = min(64 / ref.image.width, 64 / ref.image.height)
            thumb = ctk.CTkImage(ref.image, size=(max(1, int(ref.image.width * ratio)), max(1, int(ref.image.height * ratio))))
            ctk.CTkLabel(row, text="", image=thumb).pack(side="left", padx=6)
            # tr() sobre el nombre: los de fichero salen intactos y el unico
            # sintetico ("Imagen de la app") se traduce, sin alterar lo que
            # queda guardado en el proyecto.
            label = f"{chr(65+i)} · {tr(ref.name)[:45]}"
            if self.mode.get() == MODES[2]:
                # Se escaparon del candado de i18n porque van dentro de un
                # ternario encadenado y sumadas a una variable, no directas a
                # un sink; y ningun test construia este modo.
                label += " · " + (tr("INICIO") if i == 0
                                       else tr("FINAL") if i == 1
                                       else tr("Sobra: quitar"))
            ctk.CTkLabel(row, text=label).pack(side="left", padx=5)
            if self.mode.get() != MODES[2]:
                # Igual que los modos: se ensena traducido y se guarda el
                # identificador, porque ref.role se serializa en el proyecto.
                menu = ctk.CTkOptionMenu(row, values=[tr(r) for r in ROLES],
                                         command=lambda value, index=i: self.role_changed(index, value))
                menu.set(tr(ref.role))
                menu.pack(side="left", padx=5)
            ctk.CTkButton(row, text=tr("Ampliar"), width=75,
                          command=lambda index=i: self.preview_reference(index)).pack(side="right", padx=5)
            ctk.CTkButton(row, text=tr("Quitar"), width=65,
                          command=lambda index=i: self.remove(index)).pack(side="right", padx=5)

    def preview_reference(self, index):
        # GPromptWindow y no CTkToplevel: un Toplevel pelado se abre DETRÁS.
        # CustomTkinter hace withdraw()+deiconify() para pintar la barra de
        # título de Windows, y ese deiconify llega ~800 ms después del lift(),
        # así que subirla una sola vez no sirve — está medido en
        # tests/test_ventana_al_frente.py. GPromptWindow vuelve a subirla tras
        # CADA deiconify, pone el topmost 250 ms y lo suelta, y deja intactos
        # los botones de minimizar y maximizar (su transient() es un no-op a
        # propósito: en Windows, transient los esconde).
        # De regalo, al ser single-instance por título, volver a pulsar la lupa
        # sobre la misma referencia enfoca la ventana abierta en vez de apilar
        # otra encima.
        ref = self.refs[index]
        window = GPromptWindow(self)
        # El titulo es la CLAVE de deduplicacion de GPromptWindow, asi que
        # tiene que identificar la referencia, no el fichero: dos imagenes de
        # carpetas distintas pueden llamarse igual, y con el nombre a secas la
        # segunda se cerraba sola y enfocaba la ventana de la primera. Lleva
        # la letra (que referencia) y la etiqueta del panel (que proyecto).
        # Repetir la lupa sobre la MISMA referencia sigue reutilizando su
        # ventana, que es lo que se queria.
        window.title(f"{chr(65 + index)} · {tr(ref.name)[:45]} · {self.panel_label()}")
        window.geometry("850x700")
        label = ctk.CTkLabel(window, text="")
        label.pack(fill="both", expand=True, padx=10, pady=10)
        def resize(event):
            if event.widget is not window:
                return
            ratio = min(max(1, event.width - 30) / ref.image.width,
                        max(1, event.height - 30) / ref.image.height, 1)
            picture = ctk.CTkImage(ref.image, size=(max(1, int(ref.image.width * ratio)), max(1, int(ref.image.height * ratio))))
            label.configure(image=picture)
            label.image = picture
        window.bind("<Configure>", resize)

    def panel_label(self):
        """Como se nombra este panel en los titulos de sus ventanas hijas.

        El nombre del proyecto si lo hay, porque es lo que le dice algo al
        usuario, y el identificador del panel siempre: dos paneles pueden
        tener el mismo nombre de proyecto (o ninguno) y sus titulos seguirian
        chocando.
        """
        nombre = self.project_name.get().strip()
        if nombre:
            return f"{nombre[:30]} #{self.panel_id}"
        return tr("Panel {0}").format(self.panel_id)

    def direction(self):
        if output_kind(self.mode.get(), self.target.get()) != "video":
            return ""
        return video_direction(self.camera.get(), self.environment_motion.get(),
                               self.audio_direction.get(), self.transition_direction.get(), self.mode.get() == MODES[2])

    def submit(self, task, on_success):
        self.busy = True
        self.running_mode = self.mode.get()
        self.set_controls("disabled")
        try:
            self.future = self.app._executor.submit(task)
        except RuntimeError as exc:
            self.busy = False
            self.set_controls("normal")
            self.status.set(str(exc))
            return

        def poll():
            if self.closed:
                return
            if not self.future.done():
                self.after(100, poll)
                return
            self.busy = False
            self.set_controls("normal")
            try:
                on_success(self.future.result())
            except Exception as exc:
                self.status.set(tr("No se completó la operación: {0}").format(exc))
        self.after(100, poll)

    def set_controls(self, state):
        def visit(parent):
            for widget in parent.winfo_children():
                if isinstance(widget, (ctk.CTkButton, ctk.CTkEntry, ctk.CTkTextbox, ctk.CTkOptionMenu, ctk.CTkCheckBox)):
                    widget.configure(state=state)
                else:
                    visit(widget)
        visit(self.body)
        if state == "normal":
            self.filter_model_menu()
        if state == "normal" and self.mode.get() != MODES[3]:
            self.target_menu.configure(state="disabled")

    def save(self):
        if self.busy:
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".gprompt",
                                          initialfile="".join(c for c in self.project_name.get() if c.isalnum() or c in " -_")[:90] or "Proyecto-visual",
                                          filetypes=[("Proyecto visual", "*.gprompt")])
        if not path:
            return
        fields = self.fields()
        try:
            save_project(path, self.refs, fields)
            self.status.set(tr("Proyecto guardado con sus imágenes, idea, análisis y resultado."))
        except Exception as exc:
            self.status.set(tr("No se pudo guardar: {0}").format(exc))

    def load(self):
        if self.busy:
            return
        # Open in a separate window so unsaved work is retained.
        path = filedialog.askopenfilename(parent=self, filetypes=[("Proyecto visual", "*.gprompt")])
        if not path:
            return
        self.open_project(path)

    def open_project(self, path):
        try:
            refs, fields = load_project(path)
        except Exception as exc:
            self.status.set(tr("No se pudo abrir: {0}").format(exc))
            return
        other = VisualStudio(self.app)
        other.refs = refs
        for key in ("mode", "aspect", "duration", "language"):
            getattr(other, key).set(fields[key])
        other.target.set(fields.get("target") or "Imagen")
        other.platform.set(fields.get("platform", ""))
        other.model.set(fields.get("model", ""))
        other.refresh_mode_help()
        other.refresh_destination(preserve_missing=True)
        other.reference_use_changed(tr(fields.get("reference_use") or "Solo texto"))
        for key in ("preserve", "change", "manual_limit", "revision_instruction", "project_name", "camera", "environment_motion", "audio_direction", "transition_direction"):
            getattr(other, key).insert(0, fields.get(key, ""))
        for key in ("idea", "analysis", "output", "negative", "notes"):
            getattr(other, key).insert("1.0", fields.get(key, ""))
        other.analysis_stale = fields.get("analysis_stale", "true") != "false"
        # Los desplegables no siguen a sus variables (ver sync_menus): sin
        # esta llamada ensenarian los valores por defecto del panel recien
        # construido y no los del proyecto que se acaba de abrir.
        other.sync_menus()
        other.render()
        other.status.set(tr("Proyecto recuperado. Comprueba el modelo de destino del panel."))

    def analyze(self):
        if self.busy:
            return
        try:
            board, request = analysis_input(self.mode.get(), self.refs)
        except ValueError as exc:
            self.status.set(str(exc))
            return
        if not self.checkpoint():
            return
        self.status.set(tr("Analizando referencias…"))

        def done(result):
            text, provider = result
            if not isinstance(text, str) or not text.strip():
                raise ValueError(tr("El proveedor devolvió un análisis vacío."))
            self.analysis.delete("1.0", "end")
            self.analysis.insert("1.0", text)
            self.analysis_stale = False
            if not self.checkpoint():
                return
            self.status.set(tr("Análisis de {0}. Revísalo antes de generar.").format(provider))
        self.submit(lambda: self.app.vision.describir_con_prompt(board, request), done)

    def generate(self):
        if self.busy:
            return
        if self.analysis_stale:
            self.status.set(tr("Las referencias han cambiado. Conservamos tu trabajo: vuelve a analizar antes de generar."))
            return
        if self.model.get() not in self.catalog.get(self.platform.get(), []):
            self.status.set(tr("El modelo guardado no está disponible. Elige uno del catálogo; no lo hemos sustituido."))
            return
        mode = self.mode.get()
        if not self.model.get():
            self.status.set(tr("Selecciona un modelo de destino en este panel."))
            return
        try:
            specs = self.revision_specs()
            attach = self.reference_use.get() == "Adjuntar imágenes"
            check_attachment(specs, mode, len(self.refs), attach, self.attachment_confirmed.get())
            context = (f"Plataforma: {self.platform.get()}\nModelo: {self.model.get()}\n"
                       + json.dumps(specs or {"compatibilidad": "Por confirmar"}, ensure_ascii=False))
            request = generation_request(
                mode, self.refs, self.analysis.get("1.0", "end").strip(),
                self.idea.get("1.0", "end").strip(), self.preserve.get(), self.change.get(),
                self.duration.get(), self.aspect.get(), self.language.get(),
                context, (specs or {}).get("is_natural", True), self.target.get(), attach,
            ) + self.direction()
        except ValueError as exc:
            self.status.set(str(exc))
            return
        if not self.checkpoint():
            return
        self.status.set(tr("Generando prompt con el destino seleccionado…"))

        def done(text):
            prompt, negative, notes = parse_visual_result(text, specs, enforce_limit=False)
            for key, value in (("output", prompt), ("negative", negative), ("notes", notes)):
                getattr(self, key).delete("1.0", "end")
                getattr(self, key).insert("1.0", value)
            if not self.checkpoint():
                return
            limit = (specs or {}).get("max_chars")
            if isinstance(limit, (int, float)) and limit > 0 and len(prompt) > limit:
                self.status.set(tr("El borrador supera el límite. Usa Ajustar al límite; el texto se conserva."))
            else:
                self.status.set(tr("Prompt preparado. Revisa las limitaciones y el uso de las referencias."))
        self.submit(lambda: self.app.deepseek.generar_batch(
            VISUAL_SYSTEM, request, temperature=0.4, max_tokens=3500), done)

    def revision_specs(self):
        video = output_kind(self.mode.get(), self.target.get()) == "video"
        specs = dict((get_model_specs(self.model.get()) if video else get_image_model_specs(self.model.get())) or {})
        raw = self.manual_limit.get().strip()
        if raw:
            if not raw.isdecimal() or not 1 <= int(raw) <= 100000:
                raise ValueError(tr("Escribe un límite entero entre 1 y 100000 caracteres."))
            specs["max_chars"] = int(raw)
        return specs

    def update_character_count(self):
        if self.closed:
            return
        count = len(self.output.get("1.0", "end").strip())
        try:
            limit = self.revision_specs().get("max_chars")
            self.character_count.configure(text=tr("Positivo: {count} caracteres · límite: {limit}").format(
                count=count, limit=limit or "—"))
        except ValueError as exc:
            self.character_count.configure(text=str(exc))
        self.after(500, self.update_character_count)

    def revise(self, shorten=False):
        if self.busy:
            return
        try:
            if self.analysis_stale:
                raise ValueError(tr("Actualiza el análisis de las referencias antes de revisar el prompt."))
            if self.model.get() not in self.catalog.get(self.platform.get(), []):
                raise ValueError(tr("Selecciona un modelo disponible."))
            specs = self.revision_specs()
            attach = self.reference_use.get() == "Adjuntar imágenes"
            check_attachment(specs, self.mode.get(), len(self.refs), attach, self.attachment_confirmed.get())
            brief = generation_request(self.mode.get(), self.refs, self.analysis.get("1.0", "end").strip(),
                self.idea.get("1.0", "end").strip(), self.preserve.get(), self.change.get(),
                self.duration.get(), self.aspect.get(), self.language.get(),
                json.dumps({"platform": self.platform.get(), "model": self.model.get(), "specs": specs}, ensure_ascii=False),
                specs.get("is_natural", True), self.target.get(), attach) + self.direction()
            request = revision_request(brief, self.output.get("1.0", "end").strip(),
                self.negative.get("1.0", "end").strip(), self.revision_instruction.get(), specs.get("max_chars"), shorten)
        except ValueError as exc:
            self.status.set(str(exc))
            return
        if not self.checkpoint():
            return
        self.status.set(tr("Revisando el prompt con IA… Puede consumir cuota."))

        def done(text):
            # Validate before replacing any text. Failure leaves the original intact.
            positive, negative, notes = parse_visual_result(text, specs)
            for key, value in (("output", positive), ("negative", negative), ("notes", notes)):
                getattr(self, key).delete("1.0", "end")
                getattr(self, key).insert("1.0", value)
            if self.checkpoint():
                self.status.set(tr("Prompt revisado. El original está en Recuperar versiones."))
        self.submit(lambda: self.app.deepseek.generar_batch(VISUAL_SYSTEM, request,
                    temperature=0.2, max_tokens=3500), done)

    def fields(self):
        fields = {key: getattr(self, key).get() for key in
                  ("mode", "preserve", "change", "aspect", "duration", "language", "target", "platform", "model", "reference_use", "manual_limit", "revision_instruction", "project_name", "camera", "environment_motion", "audio_direction", "transition_direction")}
        fields.update({key: getattr(self, key).get("1.0", "end").strip()
                       for key in ("idea", "analysis", "output", "negative", "notes")})
        fields["analysis_stale"] = "true" if self.analysis_stale else "false"
        return fields

    def checkpoint(self):
        try:
            fields = self.fields()
            if self.refs or any(fields[key] for key in ("idea", "analysis", "output", "negative")):
                self.history.save(self.refs, fields)
            return True
        except Exception as exc:
            self.status.set(tr("No se pudo guardar la recuperación local: {0}").format(exc))
            return False

    def autosave_tick(self):
        if self.closed:
            return
        self.checkpoint()
        self.after(15000, self.autosave_tick)

    def recover(self):
        window = ctk.CTkToplevel(self)
        window.title(tr("Versiones locales — abrir sin reemplazar el trabajo actual"))
        window.geometry("700x450")
        body = ctk.CTkScrollableFrame(window)
        body.pack(fill="both", expand=True)
        ctk.CTkLabel(body, text=tr("Últimas 12 versiones por sesión. Se guardan en este equipo.")).pack()
        versions = self.history.versions()
        if not versions:
            ctk.CTkLabel(body, text=tr("Todavía no hay versiones guardadas.")).pack()
        from modules.visual_history import version_label
        for path in versions[:100]:
            ctk.CTkButton(body, text=version_label(path),
                          command=lambda p=path: self.open_project(p)).pack(fill="x", pady=3)
        window.lift()

    def copy_negative(self):
        text = self.negative.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.status.set(tr("Negativo copiado por separado."))

    def check_prompt(self):
        try:
            specs = self.revision_specs()
        except ValueError as exc:
            self.status.set(str(exc))
            return
        prompt = self.output.get("1.0", "end").strip()
        issues = []
        if not prompt:
            issues.append(tr("Falta el prompt positivo."))
        if self.analysis_stale:
            issues.append(tr("El análisis está pendiente de actualizar."))
        if self.model.get() not in self.catalog.get(self.platform.get(), []):
            issues.append(tr("El modelo no está disponible en el catálogo."))
        limit = specs.get("max_chars")
        if isinstance(limit, (int, float)) and limit > 0 and len(prompt) > limit:
            issues.append(tr("Supera el límite: {0}/{1} caracteres.").format(len(prompt), limit))
        if self.negative.get("1.0", "end").strip() and specs.get("has_negative") is not True:
            issues.append(tr("No está confirmado que el destino acepte un negativo separado."))
        try:
            check_attachment(specs, self.mode.get(), len(self.refs),
                             self.reference_use.get() == "Adjuntar imágenes", self.attachment_confirmed.get())
        except ValueError as exc:
            issues.append(str(exc))
        result = "\n".join(issues) if issues else tr("Sin incidencias en las comprobaciones disponibles. {0} caracteres.").format(len(prompt))
        messagebox.showinfo(tr("Revisión del prompt"), result + tr("\n\nRevisa también acción, identidad, cambios e idioma: esta comprobación no verifica el significado ni garantiza compatibilidad."), parent=self)

    def combined_result(self):
        positive = self.output.get("1.0", "end").strip()
        negative = self.negative.get("1.0", "end").strip()
        if positive and negative:
            return f"POSITIVE PROMPT:\n{positive}\n\nNEGATIVE PROMPT:\n{negative}"
        if negative:
            return f"NEGATIVE PROMPT:\n{negative}"
        return positive

    def copy_positive(self):
        text = self.output.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.status.set(tr("Positivo copiado por separado."))

    def copy(self):
        text = self.combined_result()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.status.set(tr("Resultado copiado."))

    def apply(self):
        text = self.combined_result()
        if text:
            self.app.dialogs.actualizar_salida(text)
            self.status.set(tr("Resultado enviado a la salida principal. Tu idea no se ha modificado."))


def open_visual_studio(app):
    previous = getattr(app, "_visual_studio", None)
    if previous is not None and previous.winfo_exists():
        previous.bring_forward()
        return previous
    app._visual_studio = VisualStudio(app)
    return app._visual_studio
