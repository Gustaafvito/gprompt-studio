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

from modules.i18n import tr


def _es_separador(v):
    return isinstance(v, str) and v.strip().startswith("──")


def attach_searchable_dropdown(combo, command=None, max_height=380,
                               placeholder="🔍 Buscar modelo…"):
    """Engancha un popup buscador+scroll al CTkComboBox `combo`.

    command(valor): se llama al elegir un modelo (como el command del combo;
    `combo.set()` no dispara el command, por eso se invoca a mano).
    Devuelve la función de apertura.
    """
    # `collapsed`: conjunto de cabeceras de familia plegadas. Persiste entre
    # aperturas del popup (estado en el closure), así el usuario no tiene que
    # volver a plegar lo mismo. Por defecto todas desplegadas.
    state = {"popup": None, "collapsed": set()}
    original_open = combo._open_dropdown_menu  # fallback defensivo

    def _cerrar():
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
            top.configure(bg="#2b2b2b")

            cont = ctk.CTkFrame(top, corner_radius=6)
            cont.pack(fill="both", expand=True)

            buscar_var = tkinter.StringVar()
            entry = ctk.CTkEntry(cont, textvariable=buscar_var,
                                 placeholder_text=placeholder, height=30)
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
                fam_colapsada = False  # ¿la familia en curso está plegada?
                for v in valores:
                    if _es_separador(v):
                        if filtro:  # al buscar se ocultan las cabeceras de grupo
                            fam_colapsada = False
                            continue
                        colapsada = v in state["collapsed"]
                        fam_colapsada = colapsada
                        flecha = "▸" if colapsada else "▾"
                        # Cabecera = CTkLabel (mismo aspecto que el original, color
                        # del tema) pero clicable para plegar/desplegar la familia.
                        hdr = ctk.CTkLabel(
                            lista, text=f"{flecha} {tr(v)}", anchor="w",
                            font=ctk.CTkFont(size=10, weight="bold"),
                            cursor="hand2",
                        )
                        hdr.pack(fill="x", padx=4, pady=(6, 0))
                        hdr.bind("<Button-1>", lambda e, fam=v: _toggle_fam(fam))
                        continue
                    if filtro and filtro not in v.lower():
                        continue
                    if not filtro and fam_colapsada:
                        continue  # familia plegada: ocultar sus modelos
                    hay = True
                    # Truncar SOLO el texto mostrado (el valor real va en command).
                    texto = v if len(v) <= 42 else v[:41] + "…"
                    ctk.CTkButton(
                        lista, text=texto, anchor="w", height=26,
                        fg_color="transparent",
                        command=lambda val=v: _elegir(val),
                    ).pack(fill="x", padx=2, pady=1)
                if not hay and filtro:
                    ctk.CTkLabel(lista, text=tr("(sin coincidencias)"),
                                 anchor="w").pack(fill="x", padx=6, pady=6)

            buscar_var.trace_add("write", _repintar)
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
