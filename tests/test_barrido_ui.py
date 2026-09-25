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

from tests._bombeo import bombear

ctk = pytest.importorskip("customtkinter")

from modules.i18n import tr  # noqa: E402
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

    def test_crear_desde_imagenes_se_ve_sin_abrir_ninguna_pestana(self, app):
        # Vivía dentro de la pestaña Ajustes Extra: con otra pestaña abierta,
        # o plegadas, no había forma de verlo.
        # Con la app recién creada la ventana aún no se ha mostrado: sin esta
        # espera, el test solo pasaba si otros le habían dado tiempo antes.
        _esperar(app)
        boton = app.btn_crear_desde_imagenes
        assert boton.winfo_ismapped()
        w = boton
        while w is not None:
            assert w is not app._tabview_container, "sigue dentro de las pestañas"
            w = w.master
        assert boton._command == app.cmd_crear_desde_imagenes

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
    bombear(app, 400)


def _redimensionar(app, alto):
    app.geometry(f"1382x{alto}")
    _esperar(app)


def _encogidos(app, botones):
    """Botones que no se ven enteros: desmapeados, encogidos o fuera."""
    derecha = app.winfo_rootx() + app.winfo_width()
    malos = []
    for b in botones:
        if (not b.winfo_ismapped()
                or b.winfo_width() < b.winfo_reqwidth() - 2
                or b.winfo_rootx() + b.winfo_width() > derecha):
            malos.append((b.cget("text"), b.winfo_width(), b.winfo_reqwidth()))
    return malos


@pytest.mark.slow
class TestNadaSeCortaDeAncho:
    """Medido el 24-sep-2026 a 1382 de ancho (el de 1920×1080): Reset, Última,
    Setup y Cargar setup no se veían, «Preview» quedaba en 34 px, el menú «UI»
    en 37 y «Workflow» no aparecía. Ver modules/fila_fluida.py."""

    @pytest.fixture(autouse=True)
    def _restaurar(self, app):
        geometria = app.geometry()
        yield
        app.geometry(geometria)
        app.update()

    @pytest.mark.parametrize("ancho", [1600, 1382, 1280, 1100])
    def test_la_botonera_entera(self, app, ancho):
        app.geometry(f"{ancho}x958")
        _esperar(app)
        botones = [b for fila in app._botonera_filas for b in _descendientes(fila)
                   if isinstance(b, ctk.CTkButton)]
        textos = [b.cget("text") for b in botones]
        for esperado in ("🗑 Reset", "🔁 Última", "💾 Setup", "🖼 Preview"):
            assert tr(esperado) in textos
        assert _encogidos(app, botones) == []

    @pytest.mark.parametrize("ancho", [1600, 1382, 1280, 1100])
    def test_los_ocho_menus_de_la_cabecera(self, app, ancho):
        app.geometry(f"{ancho}x958")
        _esperar(app)
        assert len(app._header_btns) == 8
        assert _encogidos(app, app._header_btns) == []

    @pytest.mark.parametrize("ancho", [1600, 1280])
    def test_la_ficha_del_modelo_no_se_sale_y_ocupa_dos_lineas(self, app, ancho):
        # Llevaba el ajuste de línea fijo en 1800: por debajo de ese ancho,
        # la primera línea se salía por la derecha (a 1280 acababa en «cu»).
        etiqueta = app.lbl_img_model_info
        app.pintar_info_modelo("descripción larga del modelo " * 40)
        app.geometry(f"{ancho}x958")
        _esperar(app)
        derecha = app.winfo_rootx() + app.winfo_width()
        assert etiqueta.winfo_rootx() + etiqueta.winfo_reqwidth() <= derecha
        assert etiqueta.cget("text").endswith("…")
        un_renglon = ctk.CTkFont(size=etiqueta.cget("font").cget("size")).metrics("linespace")
        escala = ctk.ScalingTracker.get_widget_scaling(etiqueta)
        assert etiqueta.winfo_reqheight() <= 3 * un_renglon * escala

    def test_con_sitio_los_menus_llevan_su_nombre(self, app):
        app.geometry("1600x958")
        _esperar(app)
        assert app._header_compacto is False
        assert app._header_btns[-1].cget("text") == tr("⚙️ Workflow")


_INTERACTIVOS = (ctk.CTkButton, ctk.CTkEntry, ctk.CTkComboBox, ctk.CTkOptionMenu,
                 ctk.CTkCheckBox, ctk.CTkSwitch, ctk.CTkTextbox, ctk.CTkSegmentedButton,
                 ctk.CTkSlider, ctk.CTkRadioButton)


def _en_desplazable(w):
    while w is not None:
        if isinstance(w, ctk.CTkScrollableFrame):
            return True
        w = getattr(w, "master", None)
    return False


def _recortes(ventana):
    """Controles sin sitio o fuera de la ventana, y textos que no caben."""
    vx, vy = ventana.winfo_rootx(), ventana.winfo_rooty()
    vw, vh = ventana.winfo_width(), ventana.winfo_height()
    malos = []
    for h in _descendientes(ventana):
        try:
            texto = str(h.cget("text"))[:50]
        except Exception:
            texto = type(h).__name__
        if isinstance(h, _INTERACTIVOS) and not _en_desplazable(h):
            # Así «desaparece» en Tk lo que no cabe: pack/grid lo desmapea.
            if (not h.winfo_ismapped() and h.winfo_manager() in ("pack", "grid")
                    and h.master.winfo_ismapped()):
                malos.append(f"sin sitio: {type(h).__name__} «{texto}»")
                continue
            if h.winfo_ismapped() and (h.winfo_rooty() + h.winfo_height() > vy + vh + 2
                                       or h.winfo_rootx() + h.winfo_width() > vx + vw + 2):
                malos.append(f"fuera: {type(h).__name__} «{texto}»")
        if (isinstance(h, (ctk.CTkLabel, ctk.CTkButton)) and h.winfo_ismapped()
                and texto.strip() and h.winfo_width() > 1
                and h.winfo_reqwidth() > h.winfo_width() + 3):
            malos.append(f"texto cortado: {type(h).__name__} «{texto}» "
                         f"({h.winfo_reqwidth()} > {h.winfo_width()})")
    return malos


# Las que al abrirse llaman a la IA, lanzan algo o no abren ventana.
_NO_ABRIR = ("Exportar como JSON", "Adaptar al modelo", "Grabar sesión", "Backup completo",
             "Restaurar backup", "Cambiar tema", "Idioma", "Modo Focus", "Panel lateral",
             "Anclaje rasgos", "Negative builder", "Paleta colores")


@pytest.mark.slow
class TestNadaSeCortaEnLasVentanasDeLosMenus:
    """Revisión del 25-sep-2026 con la app real: Ajustes escondía «Guardar» y
    la ruta de ComfyUI (500x400 para bastante más contenido), la ventana de
    grabación escondía «Sin vídeo», «X / Twitter» salía cortado en Acerca de,
    y en Historial y Favoritos se perdía la fecha."""

    def test_ningun_control_ni_texto_cortado(self, app):
        from modules.i18n import tr as _tr
        menus = {_tr(m) for m in ("📊 Análisis", "📚 Aprender", "💾 Backup", "📁 Datos",
                                  "🛠 Herramientas", "📝 Plantillas", "🎨 UI", "⚙️ Workflow")}
        _esperar(app)
        problemas = {}
        for grupo, etiqueta, cmd in app._paleta_comandos:
            if grupo not in menus or any(n in etiqueta for n in _NO_ABRIR):
                continue
            antes = {id(w) for w in app.winfo_children() if isinstance(w, tkinter.Toplevel)}
            try:
                cmd()
                bombear(app, 700)
                for w in app.winfo_children():
                    if (isinstance(w, tkinter.Toplevel) and id(w) not in antes
                            and w.state() != "withdrawn"):
                        malos = _recortes(w)
                        if malos:
                            problemas[f"{etiqueta} › {w.title()}"] = malos
            finally:
                for w in app.winfo_children():
                    if isinstance(w, tkinter.Toplevel) and id(w) not in antes:
                        try:
                            w.destroy()
                        except Exception:
                            pass
                app.update()
        assert problemas == {}


@pytest.mark.slow
class TestNsfwEnLaAppReal:
    """El interruptor 🔞 NSFW con la app de verdad. Nada se guarda en las
    preferencias del usuario: el interruptor las escribe al cambiar."""

    @pytest.fixture(autouse=True)
    def _aislar(self, app, monkeypatch):
        monkeypatch.setattr(app.store, "guardar_preferencias", lambda *a, **k: None)
        antes = (app.switch_nsfw_var.get(), app.modo_var.get(), app.combo_modelo_imagen.get())
        yield
        app.switch_nsfw_var.set(antes[0])
        app.combo_modelo_imagen.set(antes[2])
        app._toggle_nsfw_visual()
        app.update()

    def _elegir(self, app, modelo):
        app.combo_modelo_imagen.set(modelo)
        app.events._service._on_modelo_imagen_cambio(modelo)

    def _system(self, app):
        return app.deepseek.historial[0]["content"]

    def test_la_idea_explicita_enciende_nsfw_de_verdad(self, app):
        app.switch_nsfw_var.set(False)
        app._toggle_nsfw_visual()
        assert app.analysis.detectar_nsfw_auto("una mujer desnuda en la playa") is True
        assert app.switch_nsfw_var.get() is True
        # Y el system prompt ya es el NSFW: antes el aviso salía, pero el
        # prompt se generaba en modo normal.
        assert "NSFW" in self._system(app)

    def test_al_generar_el_aviso_no_se_pierde(self, app, monkeypatch):
        # Probado por el usuario el 24-sep: el aviso iba solo en la barra de
        # estado y los mensajes de progreso lo pisaban. Se ve flotando. La
        # petición no sale: el envío está simulado, no gasta nada.
        from unittest.mock import MagicMock
        enviado = MagicMock()
        monkeypatch.setattr(app, "_executor", MagicMock(submit=enviado))
        avisos = MagicMock()
        monkeypatch.setattr(app, "show_toast", avisos)
        app.switch_nsfw_var.set(False)
        app._toggle_nsfw_visual()
        app.txt_idea.delete("1.0", "end")
        app.txt_idea.insert("1.0", "retrato erótico en blanco y negro")
        try:
            app.cmd_prompt()
            assert enviado.called
            assert any("NSFW" in str(c.args[0]) for c in avisos.call_args_list)
        finally:
            app.txt_idea.delete("1.0", "end")
            app.toggle_botones(True)

    def test_nsfw_con_modelo_que_filtra_se_queda_en_sugerente(self, app):
        app.switch_nsfw_var.set(True)
        self._elegir(app, "GPT Image 2")
        assert "MODELO CON FILTRO DE CONTENIDO ADULTO" in self._system(app)
        assert "GPT Image 2" in app.lbl_estado.cget("text")
        # Con un checkpoint que no filtra, la regla no está.
        self._elegir(app, "Juggernaut XL")
        assert "MODELO CON FILTRO DE CONTENIDO ADULTO" not in self._system(app)

    def test_modelo_para_adultos_con_nsfw_apagado_avisa(self, app):
        app.switch_nsfw_var.set(False)
        self._elegir(app, "PornRealistic")
        assert "PornRealistic" in app.lbl_estado.cget("text")


@pytest.mark.slow
class TestBriefEnLaAppReal:
    """El interruptor ⚡ Brief vivía en Ajustes Extra, una pestaña que puede
    ir plegada, y se recuerda entre sesiones: podía quedarse encendido sin
    verse y convertir cada prompt en un anuncio."""

    @pytest.fixture(autouse=True)
    def _aislar(self, app, monkeypatch):
        monkeypatch.setattr(app.store, "guardar_preferencias", lambda *a, **k: None)
        antes = app.brief_var.get()
        yield
        app.brief_var.set(antes)
        app.events.on_brief_cambio()
        app.update()

    def test_uno_junto_a_cada_destino_y_ninguno_en_las_pestanas(self, app):
        paneles = [app.frame_modelo_imagen, app.frame_video, app.frame_audio]
        assert len(app._switches_brief) == 3
        encontrados = []
        for sw in app._switches_brief:
            w = sw
            while w is not None:
                assert w is not app._tabview_container, "sigue en las pestañas"
                if any(w is p for p in paneles):
                    encontrados.append(w)
                w = w.master
        # Uno en cada panel, ninguno repetido.
        assert len(encontrados) == 3
        assert all(any(e is p for e in encontrados) for p in paneles)

    def test_encendido_se_ve_arriba_y_un_clic_lo_apaga(self, app):
        app.geometry("1382x958")
        app.brief_var.set(True)
        app.events.on_brief_cambio()
        _esperar(app)
        assert app._btn_brief.winfo_ismapped()
        # Y sin quitarle sitio a la cabecera: junto al de ADN, los 8 menús
        # dejaban de caber a 1382 y se quedaban solo con el icono.
        assert app._header_compacto is False
        app._btn_brief.invoke()
        _esperar(app)
        assert app.brief_var.get() is False
        assert not app._btn_brief.winfo_ismapped()

    def test_en_imagen_van_las_reglas_de_imagen(self, app):
        app.modo_var.set("imagen")
        app.brief_var.set(True)
        app.events.on_brief_cambio()
        system = app.deepseek.historial[0]["content"]
        assert "MODO BRIEF PUBLICITARIO ACTIVO — IMAGEN" in system
        assert "PRIMEROS 2 SEGUNDOS" not in system


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
            # El ajuste de línea sigue al ancho de la ventana (1382): hace
            # falta texto para unas ocho líneas.
            etiqueta.configure(text="línea larga " * 200)
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
            bombear(app, 2200)
            assert servicio._aviso_focus_dado is False
            # Portátil de 768: ni plegando cabe, y se dice cómo arreglarlo.
            _redimensionar(app, 640)
            bombear(app, 2200)
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


class TestBusquedaGlobalEnLaAppReal:
    """Revisión del 25-sep-2026 de 🔎 Búsqueda global, con la app real:
    buscaba los personajes en un campo que no existe («rasgos»), el «✅
    Aplicado: …» nombraba siempre el ÚLTIMO resultado y, al aplicar un
    personaje, «Fuentes activas» seguía enseñando el anterior."""

    PERSONAJES = [{"nombre": "Nora Prueba", "descripcion": "mujer de 30 años, pelo rojo"},
                  {"nombre": "Otro Prueba", "descripcion": "hombre mayor con barba"}]

    @pytest.fixture(autouse=True)
    def _aislar(self, app, monkeypatch):
        monkeypatch.setattr(app.store, "personajes", [dict(p) for p in self.PERSONAJES])
        antes = app.combo_personaje.get()
        yield
        for w in app.winfo_children():
            if isinstance(w, tkinter.Toplevel):
                w.destroy()
        app.combo_personaje.set(antes)
        bombear(app)

    def _abrir(self, app):
        antes = set(app.winfo_children())
        app.backup.cmd_busqueda_global()
        bombear(app)
        return next(w for w in app.winfo_children() if w not in antes)

    def _buscar(self, app, vent, termino):
        ent = next(w for w in _descendientes(vent) if isinstance(w, ctk.CTkEntry))
        ent.insert(0, termino)
        # Sin foco del sistema Tk no entrega teclas: cada filtro relanza la
        # búsqueda igual que una tecla. Se quita «Historial» (datos del usuario).
        next(w for w in _descendientes(vent) if isinstance(w, ctk.CTkCheckBox)).toggle()
        bombear(app, 400)

    def _textos(self, vent):
        return [w.cget("text") for w in _descendientes(vent) if isinstance(w, ctk.CTkLabel)]

    def _aplicar(self, vent):
        return [b for b in _descendientes(vent)
                if isinstance(b, ctk.CTkButton) and b.cget("text") == tr("✅ Aplicar")]

    def test_al_abrir_dice_que_escribir(self, app):
        vent = self._abrir(app)
        assert tr("Escribe al menos 2 caracteres para buscar.") in self._textos(vent)

    def test_encuentra_el_personaje_por_su_descripcion(self, app):
        vent = self._abrir(app)
        self._buscar(app, vent, "pelo rojo")
        assert "mujer de 30 años, pelo rojo" in self._textos(vent)
        assert len(self._aplicar(vent)) == 1

    def test_aplicar_nombra_el_que_pulsas_y_refresca_las_fuentes(self, app):
        app.combo_personaje.set("Otro Prueba")
        bombear(app)
        vent = self._abrir(app)
        self._buscar(app, vent, "prueba")
        botones = self._aplicar(vent)
        assert len(botones) == 2
        botones[0].invoke()          # el primero: Nora
        bombear(app)
        assert app.combo_personaje.get() == "Nora Prueba"
        assert "Nora Prueba" in app.lbl_estado.cget("text")
        chips = [w.cget("text") for w in _descendientes(app.frame_fuentes_chips)
                 if isinstance(w, ctk.CTkButton)]
        assert any("Nora Prueba" in c for c in chips), chips
        assert not any("Otro Prueba" in c for c in chips), chips


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
