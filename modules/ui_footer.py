"""Footer/barra inferior — grupos de acciones (COPIAR, HERRAMIENTAS, etc.).

Extraído de modules/ui_builders.py (era una función monolítica de 616
líneas, ~28% del archivo). Contiene la barra inferior con todos los
grupos visuales de botones de acción rápida (copiar, generar negative
óptimo, scoring, traducir, guardar favorito/estrella/seed, etc.).

Dependencias self (provistas por ArquitectoApp): muchas — el método
usa decenas de comandos (cmd_*, _copiar, _guardar_*, _abrir_*, etc.)
de los mixins de la app.
"""
import logging
import re

import customtkinter as ctk
import pyperclip

from config import (
    ESTILO_NEGATIVO_AUTO,
    MOTOR_DEFAULT,
    NEGATIVE_PRESETS,
    PRESET_COLORES,
    es_separador,
    get_theme_colors,
)
from modules.style_guide import tooltip_para
from workers import detectar_idioma_es

try:
    from CTkToolTip import CTkToolTip
except ImportError:
    class CTkToolTip:  # noqa: N801
        def __init__(self, *args, **kwargs):
            pass


logger = logging.getLogger(__name__)


def _get_real_is_light():
    return ctk.get_appearance_mode().lower() == 'light'


class UiFooterService:
    """Footer/barra inferior + helpers de selección.

    A1 fase 2 (sesión 14): servicio aislado con app por composición.
    """

    def __init__(self, app):
        self.app = app

    def _build_footer(self):
        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)
        outer = ctk.CTkFrame(self.app, fg_color="transparent")
        outer.pack(side="bottom", fill="x", padx=16, pady=(1, 2))

        self.app.lbl_tokens = ctk.CTkLabel(outer, text="", font=ctk.CTkFont(family="Consolas", size=10),
                                        fg_color="transparent",
                                        text_color=c["muted_text"])
        self.app.lbl_tokens.pack(fill="x", pady=(0, 2))

        frame = ctk.CTkFrame(outer, fg_color="transparent")
        frame.pack(fill="x")

        pill = {"height": 28, "corner_radius": 6, "font": ctk.CTkFont(size=10)}

        # ═══ FILA INFERIOR — grupos con título visible ═══
        # Estructura: (titulo_grupo, color_titulo, [(label, w, fg, cmd, tip), …])
        grupos_inf = [
            ("📋 COPIAR", "#15803d", [
                ("🟢 POS",     60, "#15803d",  lambda: self.app._copiar("positivo"),     "Copiar POSITIVE · Ctrl+1"),
                ("🔴 NEG",     60, "#991b1b",  lambda: self.app._copiar("negativo"),     "Copiar NEGATIVE · Ctrl+2"),
                ("📋 Todo",    55, "#475569",  lambda: self.app._copiar("todo"),          "Copiar todo el prompt"),
            ]),
            ("🔧 HERRAMIENTAS", "#1e3a8a", [
                ("🔧 Comfy",   60, "#1e3a8a",  self.app.analysis.copiar_comfyui_json,     "Exportar/Importar ComfyUI JSON"),
                ("🇪🇸 Trad",    55, "#1e3a8a",  self.app.analysis.traducir_salida,         "Traducir al español"),
                ("📊",         30, "#1e3a8a",  self.app.analysis.cmd_scoring,             "Scoring del prompt"),
                ("✨",         30, "#1e3a8a",  self.app.analysis.abrir_atajos_tags,       "Atajos de tags rápidos"),
            ]),
            ("🛡 NEGATIVE", "#991b1b", [
                ("🔴+",        35, "#991b1b",  self.app.creative.cmd_solo_negative,        "Regenerar SOLO el NEGATIVE"),
                ("🛡",         30, "#991b1b",  self.app.creative.cmd_negative_optimo,      "Generar NEGATIVE óptimo según modelo"),
            ]),
            ("⭐ GUARDAR", "#a16207", [
                ("⭐",         30, "#a16207",  self.app.data.guardar_favorito,             "Guardar en Favoritos"),
                ("🌟",         30, "#b45309",  self.app.data.guardar_estrella,             "Guardar como Estrella"),
                ("💎",         30, "#854d0e",  self.app.analysis.guardar_seed_favorito,    "Guardar config como Seed favorito"),
            ]),
            ("💾 EXPORT", "#15803d", [
                ("💾",         30, "#15803d",  self.app.data._exportar,                         "Exportar como .txt"),
            ]),
        ]

        is_lt = ctk.get_appearance_mode().lower() == "light"
        tip_kwargs = dict(fg_color="#f0f0f0" if is_lt else "#1a1a2e",
                          text_color="#111827" if is_lt else "#e5e7eb",
                          font=("Segoe UI", 11))

        for titulo, color_tit, botones in grupos_inf:
            grp_frame = ctk.CTkFrame(frame, fg_color="transparent")
            grp_frame.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(grp_frame, text=titulo,
                          font=ctk.CTkFont(size=8, weight="bold"),
                          text_color=color_tit, anchor="w").pack(
                          anchor="w", padx=4, pady=(0, 1))
            btn_row = ctk.CTkFrame(grp_frame, fg_color="transparent")
            btn_row.pack(side="top", anchor="w")
            for text, w, fg, cmd, tip in botones:
                btn = ctk.CTkButton(btn_row, text=text, width=w, fg_color=fg,
                                     hover_color=self.app.dialogs._darker(fg),
                                     command=cmd, **pill)
                btn.pack(side="left", padx=2)
                CTkToolTip(btn, delay=0.3, message=tip, **tip_kwargs)

    def _mostrar_menu_contextual(self, event):
        """Menú contextual con click derecho en el resultado."""
        import tkinter as tk
        menu = tk.Menu(self.app, tearoff=0, bg="#1a1a2a", fg="white",
                       activebackground="#2a4a6a", activeforeground="white",
                       font=("Segoe UI", 10), borderwidth=1)

        menu.add_command(label="🟢 Copiar POSITIVE", command=lambda: self.app._copiar("positivo"))
        menu.add_command(label="🔴 Copiar NEGATIVE", command=lambda: self.app._copiar("negativo"))
        menu.add_command(label="📋 Copiar todo", command=lambda: self.app._copiar("todo"))
        menu.add_separator()

        # Submenú: pegar último prompt del historial
        if self.app.store.historial:
            submenu_hist = tk.Menu(menu, tearoff=0, bg="#1a1a2a", fg="white",
                                    activebackground="#2a4a6a", font=("Segoe UI", 10))
            for i, item in enumerate(self.app.store.historial[:5]):
                if isinstance(item, dict):
                    txt = item.get("texto", "")
                else:
                    txt = item
                if txt:
                    label = f"#{i+1} {txt[:50]}{'...' if len(txt) > 50 else ''}"
                    submenu_hist.add_command(label=label, command=lambda t=txt: self.app.dialogs.actualizar_salida(t))
            menu.add_cascade(label="📋 Pegar de historial reciente", menu=submenu_hist)

        # Submenú: pegar de favoritos
        if self.app.store.favoritos:
            submenu_fav = tk.Menu(menu, tearoff=0, bg="#1a1a2a", fg="white",
                                   activebackground="#2a4a6a", font=("Segoe UI", 10))
            for i, item in enumerate(self.app.store.favoritos[:5]):
                if isinstance(item, dict):
                    txt = item.get("texto", "")
                    nombre = item.get("nombre", "")
                else:
                    txt = item
                    nombre = ""
                if txt:
                    label = f"⭐ {nombre or txt[:50]}"
                    submenu_fav.add_command(label=label[:60], command=lambda t=txt: self.app.dialogs.actualizar_salida(t))
            menu.add_cascade(label="⭐ Pegar de favoritos", menu=submenu_fav)

        menu.add_separator()
        menu.add_command(label="📊 Analizar calidad", command=self.app.analysis.cmd_scoring)
        menu.add_command(label="✨ Atajos de tags", command=self.app.analysis.abrir_atajos_tags)
        menu.add_command(label="🇪🇸 Traducir al español", command=self.app.analysis.traducir_salida)
        menu.add_command(label="🧬 Variar con ADN visual", command=self.app._cmd_variar_con_anclaje)
        menu.add_command(label="🔍 Comparar consistencia", command=self.app._cmd_comparar_consistencia)
        menu.add_separator()
        menu.add_command(label="🗑 Limpiar resultado", command=lambda: self.app.txt_salida.delete("1.0", "end"))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _mostrar_menu_contextual_idea(self, event):
        """Menú contextual click derecho en el textbox de idea (Cortar/Copiar/Pegar/Seleccionar todo)."""
        import tkinter as tk
        menu = tk.Menu(self.app, tearoff=0, bg="#1a1a2a", fg="white",
                       activebackground="#2a4a6a", activeforeground="white",
                       font=("Segoe UI", 10), borderwidth=1)

        # Comprobar si hay selección
        try:
            tiene_seleccion = bool(self.app.txt_idea.tag_ranges("sel"))
        except Exception:
            tiene_seleccion = False

        def _cortar():
            try:
                if tiene_seleccion:
                    sel = self.app.txt_idea.get("sel.first", "sel.last")
                    pyperclip.copy(sel)
                    self.app.txt_idea.delete("sel.first", "sel.last")
                    self.app.dialogs.set_estado("✂️ Cortado al portapapeles", "#3498db")
            except Exception as e:
                logger.debug(f"[silent] {e}")

        def _copiar_sel():
            try:
                if tiene_seleccion:
                    sel = self.app.txt_idea.get("sel.first", "sel.last")
                else:
                    # Si no hay selección, copiar todo
                    sel = self.app.txt_idea.get("1.0", "end").strip()
                if sel:
                    pyperclip.copy(sel)
                    self.app.dialogs.set_estado("📋 Copiado al portapapeles", "#3498db")
            except Exception as e:
                logger.debug(f"[silent] {e}")

        def _pegar():
            try:
                texto = pyperclip.paste()
                if texto:
                    if tiene_seleccion:
                        self.app.txt_idea.delete("sel.first", "sel.last")
                    self.app.txt_idea.insert("insert", texto)
                    self.app.ui._actualizar_barra_chars()
            except Exception as e:
                logger.debug(f"[silent] {e}")

        def _seleccionar_todo():
            try:
                self.app.txt_idea.tag_add("sel", "1.0", "end")
                self.app.txt_idea.mark_set("insert", "1.0")
                self.app.txt_idea.see("insert")
            except Exception as e:
                logger.debug(f"[silent] {e}")

        def _limpiar():
            self.app.txt_idea.delete("1.0", "end")
            self.app.ui._actualizar_barra_chars()

        menu.add_command(label="✂️ Cortar" + ("" if tiene_seleccion else "  (sin selección)"),
                         command=_cortar, state="normal" if tiene_seleccion else "disabled")
        menu.add_command(label="📋 Copiar" + ("" if tiene_seleccion else "  (todo)"),
                         command=_copiar_sel)
        menu.add_command(label="📥 Pegar", command=_pegar)
        menu.add_separator()
        menu.add_command(label="🔘 Seleccionar todo", command=_seleccionar_todo)
        menu.add_separator()
        menu.add_command(label="🗑 Limpiar idea", command=_limpiar)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _construir_checkboxes(self, lista):
        """Construye / muestra los checkboxes de estilos para el modo actual.

        Cachea sub-frames por modo dentro de frame_checks. Al cambiar
        modo hace pack_forget del anterior y pack del nuevo — sin
        destruir/reconstruir widgets. Evita recrear ~257 widgets de
        IMAGEN cada vez que el usuario alterna Imagen/Vídeo/Audio.

        Compatibilidad: self.app.estilo_checks sigue apuntando al dict del
        modo activo (consumido por _filtrar_estilos, _validar_estilos,
        estilos_seleccionados, etc.).
        """
        # Inicializar cachés si es la primera vez
        if not hasattr(self.app, '_checks_subframes_cache'):
            self.app._checks_subframes_cache = {}   # id(lista) → sub-frame
            self.app._checks_vars_cache = {}        # id(lista) → dict {nombre: BooleanVar}

        cache_key = id(lista)

        # Si ya existe sub-frame para esta lista: solo swap visibility
        if cache_key in self.app._checks_subframes_cache:
            # Ocultar todos los sub-frames anteriores
            for k, sub in self.app._checks_subframes_cache.items():
                if k != cache_key:
                    try: sub.pack_forget()
                    except Exception: pass
            # Mostrar el actual
            try: self.app._checks_subframes_cache[cache_key].pack(fill="both", expand=True)
            except Exception: pass
            # Apuntar self.app.estilo_checks al dict cacheado
            self.app.estilo_checks = self.app._checks_vars_cache[cache_key]
            # Reset visual: desmarcar todo
            for var in self.app.estilo_checks.values():
                try: var.set(False)
                except Exception as _e:
                    logger.debug(f"[silent] {_e}")
            if hasattr(self.app, 'lbl_estilos_sel'):
                self.app.lbl_estilos_sel.configure(text="")
            self.app._estilos_lista_actual = lista
            self._auto_sugerir_negativos()
            self.app.ui._actualizar_contador_estilos()
            return

        # Primera construcción para esta lista: ocultar otros sub-frames
        for sub in self.app._checks_subframes_cache.values():
            try: sub.pack_forget()
            except Exception: pass

        is_light = _get_real_is_light()
        c = get_theme_colors(is_light)

        # Sub-frame propio para esta lista (anidado dentro de frame_checks)
        sub_frame = ctk.CTkFrame(self.app.frame_checks, fg_color="transparent")
        sub_frame.pack(fill="both", expand=True)
        self.app._checks_subframes_cache[cache_key] = sub_frame

        local_checks = {}
        cols = 3

        for i, nombre in enumerate(lista):
            # Ningún estilo marcado por defecto — el usuario debe elegir
            var = ctk.BooleanVar(value=False)
            local_checks[nombre] = var
            cb = ctk.CTkCheckBox(sub_frame, text=nombre, variable=var,
                                 command=self._on_estilo_cambio,
                                 font=ctk.CTkFont(size=10),
                                 checkbox_width=16, checkbox_height=16,
                                 text_color=c["chk_text"],
                                 hover_color=c["accent_text"],
                                 border_color=c["chk_border"],
                                 fg_color=c["accent_text"])
            cb.grid(row=i // cols, column=i % cols, sticky="w", padx=5, pady=1)
            # Tooltip con la descripción de GUIA_ESTILOS.md (si está cubierto)
            _tip = tooltip_para(nombre)
            if _tip:
                try:
                    CTkToolTip(cb, message=_tip, delay=0.4, wraplength=320)
                except Exception as _e:
                    logger.debug(f"[silent] tooltip estilo {nombre}: {_e}")

        for c_i in range(cols):
            sub_frame.columnconfigure(c_i, weight=1)

        self.app._checks_vars_cache[cache_key] = local_checks
        self.app.estilo_checks = local_checks
        self.app._estilos_lista_actual = lista
        if hasattr(self.app, 'lbl_estilos_sel'):
            self.app.lbl_estilos_sel.configure(text="")

        self._auto_sugerir_negativos()
        self.app.ui._actualizar_contador_estilos()

    def _filtrar_estilos(self, event=None):
        termino = self.app.entry_busqueda.get().lower()
        # v1.2: los CTkCheckBox ahora viven en un sub-frame cacheado por
        # modo, no directamente en frame_checks. Iterar recursivamente.
        def _filter_in(parent):
            for child in parent.winfo_children():
                if isinstance(child, ctk.CTkCheckBox):
                    if termino in child.cget("text").lower():
                        child.grid()
                    else:
                        child.grid_remove()
                else:
                    try: _filter_in(child)
                    except Exception: pass
        _filter_in(self.app.frame_checks)

    def _validar_estilos(self, maximo):
        marcados = [n for n, v in self.app.estilo_checks.items() if v.get()]
        if len(marcados) > maximo:
            self.app.estilo_checks[marcados[0]].set(False)

    def _on_estilo_cambio(self):
        self._validar_estilos(6)
        self._auto_sugerir_negativos()
        self.app.ui._actualizar_contador_estilos()
        sel = self.estilos_seleccionados()
        if sel:
            self.app.dialogs.set_estado(f"🎨 Estilos: {' + '.join(sel)}", "#2ecc71")
        else:
            self.app.dialogs.set_estado("🎨 Estilos: General (ninguno seleccionado)")

    def _on_personaje_selected(self, nombre: str):
        # Refrescar panel fuentes activas siempre (incluso al deseleccionar)
        try:
            self.actualizar_fuentes_activas()
        except Exception:
            pass
        if not nombre or nombre == "— Sin personaje —":
            return
        desc = self.app.store.descripcion_personaje(nombre) if hasattr(self.app, 'store') else ""
        if desc:
            self.app.txt_idea.delete("1.0", "end")
            self.app.txt_idea.insert("1.0", desc)
            if hasattr(self.app, "_sesion_eventos"):
                self.app.sesion._sesion_log(f"🧑 Personaje → {nombre}")

    def _actualizar_coste_estimado(self, event=None):
        """Calcula y muestra el coste estimado de la generación."""
        try:
            texto = self.app.txt_idea.get("1.0", "end").strip()
            if not texto or len(texto) < 5:
                self.app.lbl_coste.configure(text="")
                return

            tokens = max(1, len(texto) // 4)
            proveedor = self.app.llm_var.get().lower() if hasattr(self.app, 'llm_var') else ""

            precios = {
                "deepseek": 0.27,
                "openai": 1.5,
                "gpt": 1.5,
                "claude": 3.0,
                "gemini": 0.075,
                "ollama": 0.0,
                "mistral": 0.8,
                "groq": 0.2,
                "fireworks": 0.5,
            }

            precio_base = 0.27
            for clave, valor in precios.items():
                if clave in proveedor:
                    precio_base = valor
                    break

            coste = (tokens / 1000) * precio_base

            if precio_base == 0:
                self.app.lbl_coste.configure(text=f"🆓 gratis")
            elif coste < 0.001:
                self.app.lbl_coste.configure(text=f"$0.00{coste:.0f}")
            elif coste < 0.01:
                self.app.lbl_coste.configure(text=f"${coste:.3f}")
            else:
                self.app.lbl_coste.configure(text=f"${coste:.2f}")

        except Exception:
            self.app.lbl_coste.configure(text="")

    def _auto_sugerir_negativos(self):
        if not self.app._debe_mostrar_negatives():
            return

        presets_sugeridos = set()
        for estilo, var in self.app.estilo_checks.items():
            if var.get() and estilo in ESTILO_NEGATIVO_AUTO:
                for preset in ESTILO_NEGATIVO_AUTO[estilo]:
                    presets_sugeridos.add(preset)

        cambio = False
        for pname, pvar in self.app.preset_vars.items():
            deberia_estar = pname in presets_sugeridos
            if deberia_estar != pvar.get():
                pvar.set(deberia_estar)
                if pname in self.app.preset_btns:
                    fg = PRESET_COLORES.get(pname, ("#333", "#555"))[0]
                    self.app.preset_btns[pname].configure(fg_color="#2ecc71" if deberia_estar else fg, text=f"✓ {pname}" if deberia_estar else pname)
                cambio = True

        if cambio:
            self._rebuild_negative_text()

    def actualizar_combo_personajes(self):
        nombres = self.app.store.nombres_personajes()
        self.app.combo_personaje.configure(values=nombres)
        if self.app.combo_personaje.get() not in nombres:
            self.app.combo_personaje.set("— Sin personaje —")

    def actualizar_combo_loras(self):
        nombres = self.app.store.nombres_loras()
        self.app.combo_lora.configure(values=nombres)
        if self.app.combo_lora.get() not in nombres:
            self.app.combo_lora.set("— Sin LoRA —")
        # Refrescar trigger visible y aviso de compatibilidad
        try: self._actualizar_lora_trigger_visible()
        except Exception as e:
            logger.debug(f"[silent] {e}")

    def actualizar_combo_plantillas(self):
        nombres = self.app.store.nombres_plantillas()
        self.app.combo_plantilla.configure(values=nombres)
        if self.app.combo_plantilla.get() not in nombres:
            self.app.combo_plantilla.set("— Sin plantilla —")

    def estilos_seleccionados(self):
        return [n for n, v in self.app.estilo_checks.items() if v.get()]

    def estilos_texto(self):
        sel = self.estilos_seleccionados()
        return " + ".join(sel) if sel else "General"

    def ratio_actual(self):
        return self.app.ratio_var.get() if self.app.ratio_var.get() != "Libre" else ""

    def personaje_activo(self):
        nombre = self.app.combo_personaje.get()
        if nombre and nombre != "— Sin personaje —":
            return self.app.store.descripcion_personaje(nombre)
        return ""

    def lora_activo(self):
        nombre = self.app.combo_lora.get()
        if nombre and nombre != "— Sin LoRA —":
            return self.app.store.trigger_lora(nombre)
        return ""

    def triggers_loras_activos(self) -> list:
        """Devuelve TODOS los triggers activos: el del combo principal +
        los de loras_multi (modal multi-LoRA). Sin duplicados, en orden
        de inserción (primario primero).
        """
        triggers = []
        vistos = set()
        # Primario
        trig_principal = self.lora_activo()
        if trig_principal:
            triggers.append(trig_principal)
            vistos.add(trig_principal.lower())
        # Extras del multi-LoRA
        for nombre in getattr(self.app, "loras_multi", []) or []:
            try:
                t = self.app.store.trigger_lora(nombre)
            except Exception:
                t = ""
            if t and t.lower() not in vistos:
                triggers.append(t)
                vistos.add(t.lower())
        return triggers

    def actualizar_fuentes_activas(self) -> None:
        """Refresca el panel "Fuentes activas" con chips clickables que
        muestran qué está inyectándose en el prompt. Click en cada chip
        limpia esa fuente.

        Fuentes detectadas:
          • 🧑 Personaje (combo_personaje)
          • 🔗 LoRA primario + extras (combo_lora + loras_multi)
          • ⚓ Anclaje visual (_anclaje_visual)
          • 🧬 Último ADN visual (_ultimo_anclaje_visual)
        """
        if not hasattr(self.app, "frame_fuentes_chips"):
            return
        # Limpiar chips previos
        for w in self.app.frame_fuentes_chips.winfo_children():
            w.destroy()

        chips: list = []
        # 🧑 Personaje
        try:
            pers = self.app.combo_personaje.get() if hasattr(self.app, "combo_personaje") else ""
            if pers and pers != "— Sin personaje —":
                chips.append(("🧑 " + pers, "#3b82f6", "personaje"))
        except Exception:
            pass
        # 🔗 LoRA primario + extras
        n_loras = 0
        try:
            principal = self.app.combo_lora.get() if hasattr(self.app, "combo_lora") else ""
            if principal and principal != "— Sin LoRA —":
                n_loras += 1
        except Exception:
            pass
        n_loras += len(getattr(self.app, "loras_multi", []) or [])
        if n_loras:
            lbl = f"🔗 {n_loras} LoRA" + ("s" if n_loras > 1 else "")
            chips.append((lbl, "#7c3aed", "loras"))
        # ⚓ Anclaje visual persistido
        if getattr(self.app, "_anclaje_visual", None):
            chips.append(("⚓ Anclaje", "#f59e0b", "anclaje"))
        # 🧬 ADN visual (último análisis de imagen)
        if getattr(self.app, "_ultimo_anclaje_visual", None):
            chips.append(("🧬 ADN", "#10b981", "adn"))

        if not chips:
            # Sin fuentes → ocultar el panel entero
            try:
                self.app.frame_fuentes_activas.pack_forget()
            except Exception:
                pass
            return
        # Hay fuentes → asegurar que el panel se muestra
        try:
            if not self.app.frame_fuentes_activas.winfo_ismapped():
                self.app.frame_fuentes_activas.pack(
                    fill="x", pady=1, before=self.app.frame_plantilla_brief,
                )
        except Exception as _e:
            logger.debug(f"[silent fuentes pack] {_e}")

        for label, color, tipo in chips:
            btn = ctk.CTkButton(
                self.app.frame_fuentes_chips, text=label + "  ✕",
                width=0, height=22,
                fg_color=color, hover_color=color,
                font=ctk.CTkFont(size=10, weight="bold"),
                corner_radius=10,
                command=lambda t=tipo: self._limpiar_fuente(t),
            )
            btn.pack(side="left", padx=2)

    def _limpiar_fuente(self, tipo: str) -> None:
        """Limpia una fuente activa (personaje / loras / anclaje / adn)
        y refresca el panel."""
        try:
            if tipo == "personaje" and hasattr(self.app, "combo_personaje"):
                self.app.combo_personaje.set("— Sin personaje —")
                try:
                    self._on_personaje_selected("— Sin personaje —")
                except Exception:
                    pass
            elif tipo == "loras":
                if hasattr(self.app, "combo_lora"):
                    self.app.combo_lora.set("— Sin LoRA —")
                self.app.loras_multi = []
                try:
                    prefs = self.app.store.cargar_preferencias() or {}
                    prefs["loras_multi"] = []
                    self.app.store.guardar_preferencias(prefs)
                except Exception:
                    pass
                self._actualizar_lora_trigger_visible()
            elif tipo == "anclaje":
                self.app._anclaje_visual = None
                try:
                    prefs = self.app.store.cargar_preferencias() or {}
                    prefs["anclaje_visual"] = None
                    self.app.store.guardar_preferencias(prefs)
                except Exception:
                    pass
            elif tipo == "adn":
                self.app._ultimo_anclaje_visual = None
            try:
                self.app.dialogs.set_estado(f"🧹 Fuente '{tipo}' limpiada", "#9b59b6")
            except Exception:
                pass
        finally:
            self.actualizar_fuentes_activas()

    def rasgos_loras_activos(self) -> list:
        """Devuelve los 'rasgos visuales' (descripciones de personaje)
        de TODOS los LoRAs activos que los tengan rellenados.

        Cada LoRA puede tener un campo 'rasgos_visuales' opcional. Si está
        relleno, la app lo trata como descripción del personaje del LoRA
        y la inyecta en el prompt sin necesidad del combo Personaje.

        Devuelve lista de strings (en orden: primario primero, luego
        extras). Strings vacíos se omiten.
        """
        rasgos: list = []
        # LoRA primario del combo
        nombre_primario = ""
        try:
            nombre_primario = self.app.combo_lora.get() or ""
        except Exception:
            pass
        if nombre_primario and nombre_primario != "— Sin LoRA —":
            for l in (self.app.store.loras or []):
                if l.get("nombre") == nombre_primario:
                    r = (l.get("rasgos_visuales") or "").strip()
                    if r:
                        rasgos.append(r)
                    break
        # Extras del multi-LoRA
        for nombre in getattr(self.app, "loras_multi", []) or []:
            for l in (self.app.store.loras or []):
                if l.get("nombre") == nombre:
                    r = (l.get("rasgos_visuales") or "").strip()
                    if r:
                        rasgos.append(r)
                    break
        return rasgos

    def _abrir_multi_lora_modal(self):
        """Modal con checkboxes para seleccionar VARIOS LoRAs adicionales
        además del primario del combo. Persiste en self.app.loras_multi.
        """
        from modules.gprompt_window import GPromptWindow
        is_light = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_light)

        vent = GPromptWindow(self.app)
        vent.title("🔗 Multi-LoRA — selecciona varios")
        vent.geometry("520x560")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text="🔗 Multi-LoRA",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 2))
        ctk.CTkLabel(vent,
                     text=("Marca los LoRAs adicionales a usar junto con el "
                           "primario.\nEl combo principal sigue siendo el LoRA "
                           "primario; estos se añaden encima."),
                     font=ctk.CTkFont(size=10),
                     text_color=c["muted_text"], justify="center").pack(pady=(0, 8))

        # Cabecera con LoRA primario (informativo)
        nombre_primario = ""
        try:
            nombre_primario = self.app.combo_lora.get() or ""
        except Exception:
            pass
        if nombre_primario and nombre_primario != "— Sin LoRA —":
            ctk.CTkLabel(
                vent,
                text=f"🔹 Primario (combo): {nombre_primario}",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#2ecc71",
            ).pack(pady=(0, 6))

        # Scrollable con checkboxes
        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=4)

        loras = self.app.store.loras or []
        seleccionados_actual = set(getattr(self.app, "loras_multi", []) or [])
        # No incluimos el primario en el modal (ya está en el combo)
        chk_vars: dict = {}
        if not loras:
            ctk.CTkLabel(
                scroll,
                text="(No hay LoRAs guardados — añádelos desde 📁 Datos → 🔗 LoRAs)",
                text_color=c["muted_text"],
            ).pack(pady=20)
        else:
            for l in loras:
                nombre = l.get("nombre", "")
                if not nombre or nombre == nombre_primario:
                    continue  # Saltar el primario
                trigger = l.get("trigger", "")
                familia = l.get("familia", "")
                var = ctk.BooleanVar(value=(nombre in seleccionados_actual))
                row = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=4)
                row.pack(fill="x", pady=2)
                cb = ctk.CTkCheckBox(
                    row, text=nombre, variable=var,
                    font=ctk.CTkFont(size=11, weight="bold"),
                )
                cb.pack(side="left", padx=8, pady=4)
                meta = f'→ "{trigger}"'
                if familia:
                    meta += f"  [{familia}]"
                ctk.CTkLabel(row, text=meta,
                             font=ctk.CTkFont(family="Consolas", size=9),
                             text_color="#9b59b6").pack(side="left", padx=4)
                chk_vars[nombre] = var

        # Botones
        btns = ctk.CTkFrame(vent, fg_color="transparent")
        btns.pack(pady=10)

        def _guardar():
            nuevos = [n for n, v in chk_vars.items() if v.get()]
            self.app.loras_multi = nuevos
            # Persistir
            try:
                prefs = self.app.store.cargar_preferencias() or {}
                prefs["loras_multi"] = nuevos
                self.app.store.guardar_preferencias(prefs)
            except Exception as _e:
                logger.debug(f"[silent multi-lora persist] {_e}")
            # Actualizar label inline con conteo
            try:
                self._actualizar_lora_trigger_visible()
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            try:
                self.app.dialogs.set_estado(
                    f"🔗 Multi-LoRA: {len(nuevos)} extra(s) activo(s)",
                    "#7c3aed",
                )
            except Exception:
                pass
            vent.destroy()

        def _limpiar():
            for v in chk_vars.values():
                v.set(False)

        ctk.CTkButton(btns, text="💾 Guardar", width=110, height=30,
                      fg_color="#1a7a3c",
                      command=_guardar).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="✕ Limpiar todo", width=120, height=30,
                      fg_color="#7a1a1a",
                      command=_limpiar).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Cancelar", width=100, height=30,
                      fg_color=c["fg_dark"],
                      command=vent.destroy).pack(side="left", padx=4)

    def _actualizar_lora_trigger_visible(self):
        """Muestra el trigger del LoRA seleccionado al lado del combo (Mejora LoRAs)."""
        if not hasattr(self.app, "lbl_lora_trigger"): return
        nombre = self.app.combo_lora.get() if hasattr(self.app, "combo_lora") else ""
        if not nombre or nombre == "— Sin LoRA —":
            self.app.lbl_lora_trigger.configure(text="")
            return
        trigger = self.app.store.trigger_lora(nombre)
        # Encontrar familia
        familia = ""
        for l in self.app.store.loras:
            if l.get("nombre") == nombre:
                familia = l.get("familia", "")
                break
        # Verificar compatibilidad con modelo actual
        compatible = self._es_lora_compatible(familia)
        if compatible is False:
            warning = "  ⚠️ familia distinta"
            color = "#f39c12"
        elif compatible is True:
            warning = "  ✓"
            color = "#2ecc71"
        else:
            # None: sin info, color neutral
            warning = ""
            color = "#9b59b6"
        # Mostrar también hint si el LoRA no tiene familia configurada
        if not familia:
            warning = "  (sin familia · edítalo en 🔗)"
            color = "#4b5563" if ctk.get_appearance_mode().lower() == "light" else "#888888"
        texto = f'→ "{trigger}"'
        if familia: texto += f"  [{familia}]"
        texto += warning
        # Indicador multi-LoRA "+N más"
        try:
            n_extra = len(getattr(self.app, "loras_multi", []) or [])
            if n_extra:
                texto += f"  🔗+{n_extra}"
        except Exception:
            pass
        self.app.lbl_lora_trigger.configure(text=texto, text_color=color)
        # Refrescar panel "Fuentes activas"
        try:
            self.actualizar_fuentes_activas()
        except Exception:
            pass

    def _es_lora_compatible(self, familia_lora):
        """Devuelve True/False si el LoRA es compatible con el modelo activo. None si no se puede determinar."""
        if not familia_lora or familia_lora == "—":
            return None  # sin info, no juzgamos
        modo = self.app.modo_var.get() if hasattr(self.app, "modo_var") else "imagen"
        if modo != "imagen":
            return None  # LoRAs son cosa de imagen mayormente
        modelo = self.app.combo_modelo_imagen.get() if hasattr(self.app, "combo_modelo_imagen") else ""
        modelo_l = modelo.lower()
        # Normalizar familia del LoRA: "Z Image" → "z image", quitar guiones.
        f = familia_lora.lower().replace("-", " ").replace("_", " ").strip()
        # Detectar familia del modelo (más casos)
        modelo_familia = None
        # Z-Image PRIMERO porque "z-image" no contiene flux/sdxl/etc.
        # Cubre: "Z-Image-Base", "Z Image Turbo", "z_image", etc.
        if "z-image" in modelo_l or "z image" in modelo_l or "z_image" in modelo_l:
            modelo_familia = "z image"
        elif "flux" in modelo_l: modelo_familia = "flux"
        elif "sd3.5" in modelo_l or "sd 3.5" in modelo_l: modelo_familia = "sd3.5"
        elif "pony" in modelo_l: modelo_familia = "pony"
        elif "illustrious" in modelo_l or "noob" in modelo_l or "wai " in modelo_l: modelo_familia = "illustrious"
        elif "sdxl" in modelo_l or "juggernaut" in modelo_l or "realvis" in modelo_l: modelo_familia = "sdxl"
        elif "1.5" in modelo_l or "sd15" in modelo_l or "epic" in modelo_l: modelo_familia = "sd15"

        # Compatibilidades cruzadas: Pony e Illustrious son SDXL-based
        compatible_pares = {
            ("pony", "sdxl"), ("sdxl", "pony"),
            ("illustrious", "sdxl"), ("sdxl", "illustrious"),
            ("pony", "illustrious"), ("illustrious", "pony"),
        }
        if modelo_familia is None:
            return False  # familia del modelo desconocida → no garantizamos compatibilidad
        if (f, modelo_familia) in compatible_pares:
            return True
        return f == modelo_familia

    def _recomendar_loras_para_modelo(self, modelo_name):
        """Cuando cambia el modelo, busca LoRAs guardados compatibles y avisa al usuario."""
        if not hasattr(self.app, "store") or not self.app.store.loras:
            return
        # Si ya hay un LoRA seleccionado, no molestar
        try:
            actual = self.app.combo_lora.get()
            if actual and actual != "— Sin LoRA —":
                return
        except Exception as e:
            logger.debug(f"[silent] {e}")

        # Filtrar LoRAs con familia compatible con el nuevo modelo
        compatibles = []
        for lora in self.app.store.loras:
            familia = lora.get("familia", "")
            if not familia or familia == "—": continue
            if self._es_lora_compatible(familia) is True:
                compatibles.append(lora)

        if not compatibles:
            return

        # Mostrar mensaje amigable en el estado (en color violeta para que destaque)
        nombres = [l["nombre"] for l in compatibles[:3]]
        if len(compatibles) == 1:
            msg = f"💡 LoRA compatible disponible: '{nombres[0]}' — selecciónalo en el combo 🔗 LoRA"
        elif len(compatibles) <= 3:
            msg = f"💡 {len(compatibles)} LoRAs compatibles disponibles: {', '.join(nombres)}"
        else:
            msg = f"💡 {len(compatibles)} LoRAs compatibles ({', '.join(nombres)} +{len(compatibles) - 3} más)"
        self.app.dialogs.set_estado(msg, "#a78bfa")

    def modelo_video_valido(self):
        v = self.app.combo_modelo_video.get()
        plat = self.app.plataforma_var.get()
        if not v or es_separador(v):
            return MOTOR_DEFAULT.get(plat, plat)
        return v

    def modelo_imagen_valido(self):
        v = self.app.combo_modelo_imagen.get()
        return v if not es_separador(v) else ""

    def detectar_idioma(self, texto):
        return detectar_idioma_es(texto)

    def _validar_negative_length(self, event=None):
        """Limita el negative extra manual a 1500 chars y muestra advertencia."""
        NEGATIVE_MAX = 1500
        texto = self.app.txt_negative.get("1.0", "end").strip()
        if len(texto) > NEGATIVE_MAX:
            recortado = texto[:NEGATIVE_MAX].rsplit(",", 1)[0].rstrip(", ")
            self.app.txt_negative.delete("1.0", "end")
            self.app.txt_negative.insert("1.0", recortado)
            self.app.txt_negative.mark_set("insert", "end")
        if hasattr(self.app, 'lbl_negative_warning'):
            if len(texto) > NEGATIVE_MAX * 0.8:
                self.app.lbl_negative_warning.configure(
                    text=f"⚠️ Negative: {len(texto)}/{NEGATIVE_MAX} chars" + (" (recortado)" if len(texto) >= NEGATIVE_MAX else ""),
                    text_color="#e74c3c" if len(texto) >= NEGATIVE_MAX else "#f39c12")
                self.app.lbl_negative_warning.pack(fill="x", padx=2, pady=(2, 0))
            else:
                self.app.lbl_negative_warning.configure(text="")
                if self.app.lbl_negative_warning.winfo_ismapped():
                    self.app.lbl_negative_warning.pack_forget()

    def _rebuild_negative_text(self):
        partes = [NEGATIVE_PRESETS[n] for n, v in self.app.preset_vars.items() if v.get()]
        manual = self._get_negative_manual()
        if manual: partes.append(manual)
        texto = ", ".join(partes)
        NEGATIVE_MAX = 1500
        if len(texto) > NEGATIVE_MAX:
            texto = texto[:NEGATIVE_MAX].rsplit(",", 1)[0].rstrip(", ")
            if hasattr(self.app, 'lbl_negative_warning'):
                self.app.lbl_negative_warning.configure(
                    text=f"⚠️ Negative recortado a {NEGATIVE_MAX} chars (límite SeaArt)",
                    text_color="#e74c3c")
                self.app.lbl_negative_warning.pack(fill="x", padx=2, pady=(2, 0))
        else:
            if hasattr(self.app, 'lbl_negative_warning'):
                self.app.lbl_negative_warning.configure(text="")
                if self.app.lbl_negative_warning.winfo_ismapped():
                    self.app.lbl_negative_warning.pack_forget()
        self.app.txt_negative.delete("1.0", "end")
        if texto: self.app.txt_negative.insert("1.0", texto)
        self.app.reiniciar_memoria()

    def _get_negative_manual(self):
        texto = self.app.txt_negative.get("1.0", "end").strip()
        if not texto: return ""
        for pname in self.app.preset_vars:
            texto = texto.replace(NEGATIVE_PRESETS[pname], "")
        return re.sub(r',\s*,', ',', texto).strip(", \n")

    def _limpiar_negatives(self):
        self.app.txt_negative.delete("1.0", "end")
        for pname, pvar in self.app.preset_vars.items():
            pvar.set(False)
            if pname in self.app.preset_btns:
                fg = PRESET_COLORES.get(pname, ("#333", "#555"))[0]
                self.app.preset_btns[pname].configure(fg_color=fg, text=pname)
        self.app.reiniciar_memoria()

    def _resetear_presets_visual(self):
        for pname, pvar in self.app.preset_vars.items():
            pvar.set(False)
            if pname in self.app.preset_btns:
                fg = PRESET_COLORES.get(pname, ("#333", "#555"))[0]
                self.app.preset_btns[pname].configure(fg_color=fg, text=pname)
