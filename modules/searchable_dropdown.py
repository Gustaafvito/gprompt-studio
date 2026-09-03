"""Desplegable con buscador + scroll para CTkComboBox.

customtkinter 5.2.2 NO trae scroll en el dropdown del CTkComboBox: con muchos
modelos la lista crece hasta tapar la pantalla. `attach_searchable_dropdown()`
sustituye el dropdown por un popup con caja de búsqueda y lista scrollable de
altura limitada, SIN cambiar la API del combo (get/set/configure(values) siguen
funcionando igual; los valores se leen en vivo del combo al abrir, así el cambio
de plataforma se refleja solo).

Implementación robusta:
- Toplevel PLANO de tkinter (no CTkToplevel: su maquinaria de titlebar pelea con
  overrideredirect y a veces no renderiza). Dentro van widgets CTk normales.
- Cierre con `grab_set` (modal): los clics FUERA llegan al popup y se cierran por
  coordenadas. NO se bindea nada en el root (el `unbind(seq, funcid)` de tkinter
  borra TODOS los bindings de ese evento — rompería otros cierres de la app).

Uso:
    from modules.searchable_dropdown import attach_searchable_dropdown
    attach_searchable_dropdown(combo, command=on_cambio)
"""
import tkinter

import customtkinter as ctk

from modules import paleta as P
from modules.i18n import tr


# Tope de filas dibujadas de una vez. Cada fila es un CTkButton y crearlos es
# CARO (canvas + label + bindings): con el catalogo de imagen entero eran ~170
# widgets en cada apertura Y en cada tecla, que es el "tarda en activarse".
_MAX_FILAS = 80
# Espera antes de repintar al escribir: teclear 6 letras hacia 6 repintados.
_DEBOUNCE_MS = 140


def _es_separador(v):
    return isinstance(v, str) and v.strip().startswith("──")


def attach_searchable_dropdown(combo, command=None, max_height=380,
                               placeholder=None):
    """Engancha un popup buscador+scroll al CTkComboBox `combo`.

    command(valor): se llama al elegir un modelo (como el command del combo;
    `combo.set()` no dispara el command, por eso se invoca a mano).
    Devuelve la función de apertura.
    """
    # `collapsed`: conjunto de cabeceras de familia plegadas. Persiste entre
    # aperturas del popup (estado en el closure), así el usuario no tiene que
    # volver a plegar lo mismo. Por defecto todas desplegadas.
    state = {"popup": None, "collapsed": set(), "job": None}
    original_open = combo._open_dropdown_menu  # fallback defensivo

    def _cerrar():
        if state.get("job") is not None:
            try:
                combo.after_cancel(state["job"])
            except Exception:
                pass
            state["job"] = None
        p = state["popup"]
        state["popup"] = None
        if p is not None:
            try:
                p.grab_release()
            except Exception:
                pass
            # Ocultar al instante (la UI responde inmediatamente), destruir
            # con retardo largo para que el event loop procese los clics del
            # usuario antes de que la destrucción de ~80 widgets CTk bloquee
            # el hilo principal.
            try:
                p.withdraw()
            except Exception:
                pass
            try:
                combo.after(2000, p.destroy)
            except Exception:
                try:
                    combo.after(0, p.destroy)
                except Exception:
                    pass

    def _elegir(valor):
        _cerrar()
        try:
            combo.set(valor)
        except Exception:
            pass
        if command:
            try:
                command(valor)
            except Exception:
                pass

    def _abrir():
        if state["popup"] is not None:  # toggle
            _cerrar()
            return
        try:
            valores = list(combo.cget("values"))
        except Exception:
            valores = []
        if not valores:
            return original_open()

        try:
            from config import get_theme_colors
            is_light = ctk.get_appearance_mode().lower() == "light"
            c = get_theme_colors(is_light)
            valor_actual = combo.get()

            top = tkinter.Toplevel(combo)
            state["popup"] = top
            top.wm_overrideredirect(True)
            try:
                top.transient(combo.winfo_toplevel())
                top.attributes("-topmost", True)
            except Exception:
                pass
            x = combo.winfo_rootx()
            y = combo.winfo_rooty() + combo.winfo_height()
            ancho = max(combo.winfo_width(), 320)
            top.geometry(f"{ancho}x{max_height}+{x}+{y}")
            top.configure(bg=c["combo_border"])

            cont = ctk.CTkFrame(top, corner_radius=6, fg_color=c["panel_bg"],
                                border_width=1, border_color=c["combo_border"])
            cont.pack(fill="both", expand=True, padx=1, pady=1)

            buscar_var = tkinter.StringVar()
            entry = ctk.CTkEntry(cont, textvariable=buscar_var,
                                 placeholder_text=placeholder or tr("🔍 Buscar modelo…"),
                                 height=30, fg_color=c["combo_bg"], border_color=c["combo_border"],
                                 text_color=c["panel_text"])
            entry.pack(fill="x", padx=6, pady=6)

            lista = ctk.CTkScrollableFrame(cont, fg_color="transparent")
            lista.pack(fill="both", expand=True, padx=4, pady=(0, 6))

            def _toggle_fam(fam):
                if fam in state["collapsed"]:
                    state["collapsed"].discard(fam)
                else:
                    state["collapsed"].add(fam)
                _repintar()

            def _repintar(*_):
                for w in lista.winfo_children():
                    w.destroy()
                filtro = buscar_var.get().strip().lower()
                hay = False
                dibujadas = 0   # filas realmente pintadas (tope _MAX_FILAS)
                ocultas = 0     # las que no caben: se resumen al final
                fam_colapsada = False  # ¿la familia en curso está plegada?
                for v in valores:
                    if _es_separador(v):
                        if filtro:  # al buscar se ocultan las cabeceras de grupo
                            fam_colapsada = False
                            continue
                        colapsada = v in state["collapsed"]
                        fam_colapsada = colapsada
                        flecha = "▸" if colapsada else "▾"
                        # Cabecera = CTkLabel (color acento, discreta) pero
                        # clicable para plegar/desplegar la familia.
                        hdr = ctk.CTkLabel(
                            lista, text=f"{flecha} {tr(v)}", anchor="w",
                            font=ctk.CTkFont(size=P.FUENTE_PEQUENA, weight="bold"),
                            text_color=c["accent_text"],
                            cursor="hand2",
                        )
                        hdr.pack(fill="x", padx=4, pady=(6, 1))
                        hdr.bind("<Button-1>", lambda e, fam=v: _toggle_fam(fam))
                        sep = ctk.CTkFrame(lista, fg_color=c["combo_border"], height=1)
                        sep.pack(fill="x", padx=4, pady=(0, 2))
                        continue
                    if filtro and filtro not in v.lower():
                        continue
                    if not filtro and fam_colapsada:
                        continue  # familia plegada: ocultar sus modelos
                    hay = True
                    if dibujadas >= _MAX_FILAS:
                        ocultas += 1
                        continue
                    dibujadas += 1
                    # Truncar SOLO el texto mostrado (el valor real va en command).
                    texto = v if len(v) <= 42 else v[:41] + "…"
                    es_actual = v == valor_actual
                    ctk.CTkButton(
                        lista, text=f"✓ {texto}" if es_actual else texto,
                        anchor="w", height=26, corner_radius=4,
                        fg_color=c["btn_hover"] if es_actual else "transparent",
                        hover_color=c["btn_hover"],
                        text_color=P.TXT_ACENTO if es_actual else c["panel_text"],
                        font=ctk.CTkFont(size=P.FUENTE_PEQUENA,
                                          weight="bold" if es_actual else "normal"),
                        command=lambda val=v: _elegir(val),
                    ).pack(fill="x", padx=2, pady=1)
                if ocultas:
                    ctk.CTkLabel(
                        lista,
                        text=tr("… y {0} más — escribe para afinar").format(ocultas),
                        text_color=c["muted_text"], anchor="w",
                        font=ctk.CTkFont(size=P.FUENTE_PEQUENA),
                    ).pack(fill="x", padx=6, pady=6)
                if not hay and filtro:
                    ctk.CTkLabel(lista, text=tr("(sin coincidencias)"),
                                 text_color=c["muted_text"],
                                 anchor="w").pack(fill="x", padx=6, pady=6)

            def _repintar_pronto(*_):
                """Repinta tras una pausa: escribir rapido no dispara N repintados."""
                if state.get("job") is not None:
                    try:
                        combo.after_cancel(state["job"])
                    except Exception:
                        pass
                state["job"] = combo.after(_DEBOUNCE_MS, _repintar)

            buscar_var.trace_add("write", _repintar_pronto)
            _repintar()

            # Mapear y dar foco antes del grab (Windows lo necesita mapeado).
            top.update_idletasks()
            top.lift()
            entry.focus_set()

            def _on_click(e):
                # Con grab_set, los clics de TODA la pantalla llegan aquí. Si el
                # clic cae fuera del popup, cerrar.
                rx, ry = top.winfo_rootx(), top.winfo_rooty()
                if not (rx <= e.x_root <= rx + top.winfo_width()
                        and ry <= e.y_root <= ry + top.winfo_height()):
                    _cerrar()

            top.bind("<Button-1>", _on_click)
            top.bind("<Escape>", lambda e: _cerrar())
            try:
                top.grab_set()
            except Exception:
                pass
        except Exception:
            _cerrar()
            return original_open()

    combo._open_dropdown_menu = _abrir
    return _abrir
