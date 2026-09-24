"""Barrido de UI: que TODAS las ventanas abran y ningún botón quede muerto.

Arranca la aplicación real y abre una a una todas las ventanas secundarias,
comprobando que se construyen y que cada CTkButton conserva su callback. Es lo
que de verdad se rompe al refactorizar: un botón que se queda sin `command`
sigue pintándose igual, pero al pulsarlo no pasa nada y nadie se entera.

NO se pulsa nada: hacerlo dispararía llamadas a la API (créditos del usuario) y
escrituras en disco. Aquí se verifica construcción y cableado.

Como crea ventanas reales, se salta entero si el entorno no tiene display.
"""
import tkinter
from tkinter import filedialog, messagebox

import pytest

ctk = pytest.importorskip("customtkinter")

from tests._arranque_tk import crear_con_reintentos  # noqa: E402

# Ventanas de la app: (módulo, función, argumentos extra además de `app`)
VENTANAS = [
    ("avatar_ui", "abrir_avatar_window", ()),
    ("bienvenida", "abrir_bienvenida", ()),
    ("command_palette", "abrir_command_palette", ()),
    ("glosario", "abrir_glosario", ()),
    ("style_guide", "abrir_guia_estilos", ()),
    ("tutorial", "abrir_tutorial", ()),
    ("windows", "abrir_personajes", ()),
    ("windows", "abrir_loras", ()),
    ("windows", "abrir_batch_variables", ()),
    ("windows", "abrir_batch", ()),
    ("windows", "abrir_lista", ("favoritos", "Favoritos", "#3b82f6")),
]


@pytest.fixture(scope="module")
def app(monkeypatch_module, exige_tk):
    """La aplicación real, con todo lo que puede BLOQUEAR neutralizado."""
    from app import ArquitectoApp
    # Se salta SOLO si el entorno no tiene Tk (CI headless). Si Tk funciona,
    # que la app no arranque es un FALLO y tiene que verse: cazarlo aqui
    # convertia una regresion de arranque en un salto silencioso.
    #
    # Con reintentos porque ArquitectoApp ES un root de Tk (hereda de ctk.CTk)
    # y por tanto arranca su propio interprete de Tcl. Es el TERCERO que crea
    # cada proceso de pytest —el sondeo de conftest, este y el root
    # compartido—, y los tres leen el mismo init.tcl: tres tiradas de dado por
    # suite. Si le toca a este, no salen 62 errores sino los 24 de este
    # fichero, que es la misma averia disfrazada. Ver tests/_arranque_tk.py:
    # solo se reintentan los TclError, asi que una regresion de arranque de la
    # app (AttributeError, un import que falta) sigue fallando a la primera y
    # se ve, que es lo que dice el parrafo de arriba.
    a = crear_con_reintentos(ArquitectoApp)
    a.update()
    a.update_idletasks()
    yield a
    try:
        a.destroy()
    except Exception:
        pass


@pytest.fixture(scope="module")
def monkeypatch_module():
    """Silencia diálogos modales: sin esto el barrido se queda colgado."""
    mp = pytest.MonkeyPatch()
    for nombre, valor in (("showinfo", None), ("showwarning", None),
                          ("showerror", None), ("askyesno", False),
                          ("askokcancel", False), ("askquestion", "no")):
        mp.setattr(messagebox, nombre, lambda *a, _v=valor, **k: _v)
    for nombre in ("askopenfilename", "asksaveasfilename", "askdirectory"):
        mp.setattr(filedialog, nombre, lambda *a, **k: "")
    mp.setattr(tkinter.Misc, "wait_window", lambda self, w=None: None)
    mp.setattr(tkinter.Misc, "grab_set", lambda self: None)
    mp.setattr(tkinter.Misc, "grab_release", lambda self: None)
    yield mp
    mp.undo()


def _descendientes(widget):
    acc = []

    def _rec(w):
        for h in w.winfo_children():
            acc.append(h)
            _rec(h)

    _rec(widget)
    return acc


def _botones_sin_accion(widget):
    """Textos de los CTkButton que se quedaron sin callback."""
    sin = []
    for b in _descendientes(widget):
        if not isinstance(b, ctk.CTkButton):
            continue
        if not callable(getattr(b, "_command", None)):
            try:
                sin.append(b.cget("text"))
            except Exception:
                sin.append("?")
    return sin


def _abrir(app, modname, fname, extra):
    """Abre una ventana y devuelve las Toplevel nuevas que haya creado."""
    antes = {id(w) for w in app.winfo_children()
             if isinstance(w, tkinter.Toplevel)}
    mod = __import__(f"modules.{modname}", fromlist=[fname])
    getattr(mod, fname)(app, *extra)
    app.update()
    app.update_idletasks()
    return [w for w in app.winfo_children()
            if isinstance(w, tkinter.Toplevel) and id(w) not in antes]


@pytest.mark.slow
class TestVentanas:

    @pytest.mark.parametrize("modname,fname,extra", VENTANAS,
                             ids=[v[1] for v in VENTANAS])
    def test_la_ventana_abre_sin_romperse(self, app, modname, fname, extra):
        nuevas = _abrir(app, modname, fname, extra)
        try:
            assert nuevas, f"{fname} no creó ninguna ventana"
        finally:
            for w in nuevas:
                try:
                    w.destroy()
                except Exception:
                    pass
            app.update()

    @pytest.mark.parametrize("modname,fname,extra", VENTANAS,
                             ids=[v[1] for v in VENTANAS])
    def test_la_ventana_no_tiene_botones_muertos(self, app, modname, fname, extra):
        nuevas = _abrir(app, modname, fname, extra)
        try:
            sin = [t for w in nuevas for t in _botones_sin_accion(w)]
            assert not sin, f"{fname}: botones sin acción -> {sin}"
        finally:
            for w in nuevas:
                try:
                    w.destroy()
                except Exception:
                    pass
            app.update()


@pytest.mark.slow
class TestVentanaPrincipal:

    def test_no_hay_botones_muertos(self, app):
        sin = _botones_sin_accion(app)
        assert not sin, f"botones sin acción en la ventana principal: {sin}"

    def test_tiene_una_cantidad_razonable_de_botones(self, app):
        """Si esto cae en picado es que media UI dejó de construirse."""
        botones = [w for w in _descendientes(app)
                   if isinstance(w, ctk.CTkButton)]
        assert len(botones) >= 50, f"solo {len(botones)} botones"


def _visible(app, widget):
    """Alto que de verdad se ve dentro de la ventana.

    `winfo_height()` no basta: cuando pack se queda sin sitio, desmapea el
    widget y su alto se queda con el último valor que tuvo.
    """
    if not widget.winfo_ismapped():
        return 0
    arriba = widget.winfo_rooty() - app.winfo_rooty()
    return max(0, min(widget.winfo_height(), app.winfo_height() - arriba))


def _esperar(app):
    for _ in range(6):
        app.update()
    # El reparto va agrupado con un after(50) y puede encadenar una segunda
    # pasada: hay que darle tiempo.
    app.after(400, app.quit)
    app.mainloop()
    app.update()


def _redimensionar(app, alto):
    app.geometry(f"1382x{alto}")
    _esperar(app)


@pytest.mark.slow
class TestElResultadoSeVe:
    """El «Resultado editable» recibía 30 px de los 240 que pide.

    Medido el 24-sep-2026 con la ventana a su tamaño por defecto en
    1920×1080: con pack, lo último que se empaqueta es lo primero que se
    encoge, y lo último era el resultado. Ver modules/espacio_ventana.py.
    """

    @pytest.fixture(autouse=True)
    def _restaurar(self, app):
        geometria = app.geometry()
        yield
        app.ui._service._pestanas_plegadas_manual = None
        if getattr(app, "_modo_focus_activo", False):
            app._cmd_modo_focus()
        app.geometry(geometria)
        app.update()

    def test_con_la_ventana_por_defecto_en_full_hd(self, app):
        _redimensionar(app, 958)
        assert _visible(app, app.txt_salida) >= 150

    def test_con_ventana_baja_las_pestanas_se_pliegan(self, app):
        # Portátil típico: 1920×1080 al 125 %, unos 760 de alto lógico.
        # Sin plegar, el resultado desaparecía del todo.
        _redimensionar(app, 760)
        assert app.ui._service._pestanas_plegadas is True
        assert _visible(app, app.txt_salida) >= 100
        # Y lo que queda encima sigue entero: nada se come la botonera.
        assert _visible(app, app.frame_entrada) == app.frame_entrada.winfo_height()

    def test_si_algo_de_encima_crece_se_reparte_otra_vez(self, app):
        # La línea de información del modelo se rellena después de arrancar
        # y puede ocupar varias líneas. La ventana no cambia de tamaño, así
        # que sin escuchar al marco del resultado el reparto se quedaba
        # viejo: medido, el resultado bajaba de 177 a 127 px sin plegar nada.
        etiqueta = app.lbl_img_model_info
        texto, ancho = etiqueta.cget("text"), etiqueta.cget("wraplength")
        try:
            _redimensionar(app, 975)
            assert app.ui._service._pestanas_plegadas is False
            etiqueta.configure(text="línea larga " * 60, wraplength=500)
            # Sin tocar la ventana: geometry() ya provoca un recálculo y
            # taparía justo lo que se comprueba.
            _esperar(app)
            assert app.ui._service._pestanas_plegadas is True
            assert _visible(app, app.txt_salida) >= 150
        finally:
            etiqueta.configure(text=texto, wraplength=ancho)

    def test_el_aviso_de_ctrl_h_solo_si_ni_plegando_cabe(self, app):
        servicio = app.ui._service
        servicio._aviso_focus_dado = False
        try:
            # Con sitio no se avisa. Salía también así: al arrancar, la
            # ventana pasa por un tamaño provisional.
            _redimensionar(app, 958)
            app.after(2200, app.quit)
            app.mainloop()
            assert servicio._aviso_focus_dado is False
            # Portátil de 768: ni plegando cabe, y se dice cómo arreglarlo.
            _redimensionar(app, 640)
            app.after(2200, app.quit)
            app.mainloop()
            assert servicio._aviso_focus_dado is True
            assert "Ctrl+H" in app.lbl_estado.cget("text")
        finally:
            servicio._aviso_focus_dado = False

    def test_pulsar_una_pestana_plegada_la_despliega(self, app):
        _redimensionar(app, 760)
        assert app.ui._service._pestanas_plegadas is True
        app.ui.desplegar_pestanas()
        app.update()
        assert app.ui._service._pestanas_plegadas is False
        # Y es lo que hace el cambio de pestaña, no solo un método suelto.
        import inspect

        from modules.ui_builders import UIBuildersService
        fuente = inspect.getsource(UIBuildersService._build_tabs_centrales)
        cuerpo = fuente[fuente.index("def _on_tab_change"):fuente.index("configure(command=_on_tab_change)")]
        assert "desplegar_pestanas()" in cuerpo

    def test_el_modo_focus_da_sitio_y_al_salir_vuelven_las_pestanas(self, app):
        _redimensionar(app, 958)
        antes = _visible(app, app.txt_salida)
        app._cmd_modo_focus()
        _redimensionar(app, 958)
        # Antes ocultaba las pestañas pero no su contenedor de alto fijo.
        assert not app._tabview_container.winfo_ismapped()
        assert _visible(app, app.txt_salida) > antes + 150
        app._cmd_modo_focus()
        _redimensionar(app, 958)
        # Antes no volvían nunca: se re-empaquetaban en la ventana principal,
        # y Tk no deja empaquetar las pestañas fuera de su contenedor.
        assert app.tabview.winfo_ismapped(), "al salir de Focus no volvieron las pestañas"
        assert app._tabview_container.winfo_ismapped()


@pytest.mark.slow
class TestLoQueEnsenaAprender:
    """Lo que el tutorial, la paleta y los atajos prometen, existe de verdad.

    Se comprueba con la app montada porque la mayoría de las acciones se
    resuelven en tiempo de ejecución, a través de los servicios de la app.
    NO se ejecutan: abrirían ventanas o llamarían a la API.
    """

    def test_cada_probar_ahora_del_tutorial_existe(self, app):
        import json
        from pathlib import Path

        from modules import windows
        from modules.tutorial import _FREE_FUNCS

        data = Path(__file__).resolve().parent.parent / "data"
        pasos = json.loads((data / "tutorial.json").read_text(encoding="utf-8"))["pasos"]
        # El glosario (Modo educativo) tiene su propio «▶ Probar», con el
        # mismo mecanismo: método de la app o función de modules.windows.
        glosario = json.loads((data / "glosario.json").read_text(encoding="utf-8"))["entradas"]
        pasos = pasos + [{"id": f"glosario «{e['titulo']}»", "accion": e["accion"]}
                         for e in glosario]
        norm = lambda s: "".join(c.lower() for c in s if c.isalnum())
        pestanas = {norm(n) for n in getattr(app.tabview, "_name_list", [])}
        rotas = []
        for p in pasos:
            accion = p["accion"]
            if not accion or accion == "focus_modelo":
                continue
            if accion.startswith("focus:"):
                ok = getattr(app, accion.split(":", 1)[1], None) is not None
            elif accion.startswith("mode:"):
                ok = accion.split(":", 1)[1] in ("imagen", "video", "audio")
            elif accion.startswith("tab:"):
                ok = norm(accion.split(":", 1)[1]) in pestanas
            elif accion in _FREE_FUNCS:
                ok = callable(getattr(windows, accion, None))
            else:
                ok = callable(getattr(app, accion, None))
            if not ok:
                rotas.append(f"paso {p['id']}: {accion}")
        assert not rotas, "«Probar ahora» apunta a algo que no existe: " + "; ".join(rotas)

    def test_la_paleta_encuentra_las_herramientas_nuevas(self, app):
        comandos = [c for _, _, c in app._paleta_comandos]
        assert app.cmd_crear_desde_imagenes in comandos, \
            "Ctrl+K no encuentra «Crear desde imágenes»"
        # El Cortometraje va en un lambda (difiere `multi`): se mira a quién llama.
        assert any("cmd_cortometraje" in getattr(getattr(c, "__code__", None), "co_names", ())
                   for c in comandos), "Ctrl+K no encuentra el Cortometraje"

    def test_ctrl_shift_i_esta_registrado_en_la_app_viva(self, app):
        # Registrado en la ventana y en la caja de idea, como el resto de
        # atajos. No se simula la pulsación: sin el foco del sistema, Tk no
        # entrega el evento, y en una tirada de tests la ventana no lo tiene.
        # Que la mayúscula es la forma correcta se comprobó aparte con
        # pulsaciones reales (ver tests/test_atajos_teclado.py).
        for widget in (app, app.txt_idea._textbox):
            assert widget.bind("<Control-Shift-I>"), f"sin Ctrl+Shift+I en {widget}"
        from pathlib import Path
        fuente = (Path(__file__).resolve().parent.parent / "modules"
                  / "atajos_ayuda.py").read_text(encoding="utf-8")
        linea = next(l for l in fuente.splitlines() if '"<Control-Shift-I>"' in l)
        assert "cmd_crear_desde_imagenes" in linea
