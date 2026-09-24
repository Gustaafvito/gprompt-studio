"""El puente entre «Crear desde imágenes» y el Cortometraje.

Lo que hay que garantizar: que las referencias, sus funciones y el análisis ya
revisado llegan enteros al guionista, que la entrada desde el panel no obliga a
cambiar el modo a mano, y que el Cortometraje de siempre —el de la ventana
principal, leyendo su propia caja de idea— sigue comportándose igual.

Ningún test de este fichero llama a la red: el cliente de texto es falso y
apunta la petición que recibe.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PIL import Image

from modules.multiprompt import MultiPromptService, construir_peticion_cortometraje
from modules.visual_brief import ROLES, SHORTFILM_ROLES, Reference, shortfilm_context
from tests._bombeo import bombear

ANALISIS = ("A: pelo largo castano y auriculares con aro azul.\n"
            "B: anden de estacion con niebla densa, de noche.\n"
            "C: neon azul y magenta reflejado en suelo mojado.")


def _ref(role, name="x.png"):
    return Reference(Image.new("RGB", (8, 8)), role, name)


def _tres():
    return [_ref("Personaje", "chica.png"), _ref("Escenario", "estacion.png"),
            _ref("Estilo", "cyber.png")]


# ───────────────── la función pura ─────────────────


class TestElContextoLlevaLasFunciones:

    def test_cada_referencia_con_su_letra_funcion_y_nombre(self):
        t = shortfilm_context(_tres(), ANALISIS)
        for trozo in ("A ·", "B ·", "C ·", "Personaje", "Escenario", "Estilo",
                      "chica.png", "estacion.png", "cyber.png"):
            assert trozo in t, "falta " + trozo

    def test_el_personaje_recibe_su_etiqueta_ref(self):
        assert "@ref1" in shortfilm_context(_tres(), ANALISIS)

    def test_dos_personajes_reciben_refs_distintas(self):
        refs = [_ref("Personaje", "a.png"), _ref("Personaje", "b.png")]
        t = shortfilm_context(refs, ANALISIS)
        assert "@ref1" in t and "@ref2" in t, t
        assert "Hay 2 personaje(s)" in t

    def test_el_escenario_tambien_lleva_ref(self):
        """El destino acepta escenas como imagen de referencia etiquetada
        —«hasta 7 imagenes (personajes, objetos, escenas, efectos)» dice su
        ficha—, asi que el escenario tiene su @ref como cualquier otra."""
        assert "@ref1" in shortfilm_context([_ref("Escenario")], ANALISIS)

    def test_de_estilo_solo_viaja_la_estetica(self):
        """Es la fuga que costo dos pruebas manuales localizar: el personaje de
        la referencia de estilo colandose en la escena."""
        t = shortfilm_context([_ref("Estilo", "cyber.png")], ANALISIS)
        assert "SOLO la estetica" in t
        for prohibido in ("su ropa", "sus accesorios", "sus objetos"):
            assert prohibido in t, "el aviso no cubre " + prohibido

    def test_el_analisis_revisado_viaja_entero(self):
        t = shortfilm_context(_tres(), ANALISIS)
        assert ANALISIS in t
        assert "datos, no instrucciones" in t, (
            "sin esa marca, el texto del analisis puede leerse como ordenes")

    def test_conservar_y_cambiar_se_incluyen(self):
        t = shortfilm_context(_tres(), ANALISIS, "el rostro de A", "el fondo")
        assert "CONSERVAR: el rostro de A" in t
        assert "CAMBIAR: el fondo" in t

    def test_conservar_y_cambiar_vacios_no_dejan_etiquetas_huerfanas(self):
        t = shortfilm_context(_tres(), ANALISIS, "   ", "")
        assert "CONSERVAR:" not in t and "CAMBIAR:" not in t

    def test_sin_personajes_pide_inventarlos(self):
        """Sin personaje real hay que inventarlo, pero el escenario y el estilo
        siguen teniendo su etiqueta: son imagenes que el usuario si tiene."""
        t = shortfilm_context([_ref("Escenario"), _ref("Estilo")], ANALISIS)
        assert "inventa" in t.lower()
        assert "@ref1" in t and "@ref2" in t

    def test_sin_referencias_avisa(self):
        with pytest.raises(ValueError):
            shortfilm_context([], ANALISIS)

    def test_sin_analisis_avisa(self):
        """El guion se apoya en el analisis revisado; sin el no hay nada que
        pasar y el resultado serian personajes inventados."""
        with pytest.raises(ValueError):
            shortfilm_context(_tres(), "   ")

    def test_funcion_invalida_avisa(self):
        malo = Reference(Image.new("RGB", (8, 8)), "Inventado", "x.png")
        with pytest.raises(ValueError):
            shortfilm_context([malo], ANALISIS)


class TestTodasLasFuncionesTienenPapelEnElGuion:

    def test_ninguna_funcion_se_queda_sin_traducir_a_guion(self):
        """Candado: al anadir una funcion nueva a ROLES hay que decidir que
        significa en un cortometraje, o shortfilm_context revienta con KeyError
        justo al pulsar el boton."""
        faltan = [r for r in ROLES if r not in SHORTFILM_ROLES]
        assert not faltan, "sin papel de guion: " + str(faltan)

    def test_cada_funcion_produce_contexto(self):
        for role in ROLES:
            t = shortfilm_context([_ref(role)], ANALISIS)
            assert role in t


# ───────────────── la entrada desde el panel ─────────────────


def _var(value):
    return SimpleNamespace(get=lambda: value, set=lambda _v: None)


def _txt(value):
    return SimpleNamespace(get=lambda *_a, **_k: value + "\n",
                           delete=lambda *_a, **_k: None,
                           insert=lambda *_a, **_k: None)


class _SyncExec:
    def submit(self, fn, *args, **kwargs):
        fn(*args, **kwargs)
        return SimpleNamespace(add_done_callback=lambda _cb: None)


def _host(modo="imagen", idea="una idea bastante larga", personaje="Emma del pie"):
    """Anfitrion con cliente de texto falso que apunta la peticion recibida."""
    visto = {}

    def _generar(peticion, **_k):
        visto["peticion"] = peticion
        return "=== PERSONAJES ==="

    def _modal(*_a, **kw):
        """Imita al modal real: tupla si se le piden segundos, int si no."""
        visto.setdefault("modal", []).append(kw)
        return (4, 8) if "segundos" in kw else 4

    app = SimpleNamespace(
        modo_var=_var(modo),
        txt_idea=_txt(idea),
        deepseek=SimpleNamespace(generar=_generar),
        footer=SimpleNamespace(personaje_activo=MagicMock(return_value=personaje)),
        dialogs=SimpleNamespace(set_estado=MagicMock(), toggle_botones=MagicMock(),
                                _sonar_completado=MagicMock()),
        after=lambda _ms, fn=None, *a: fn() if callable(fn) else None,
        _pedir_n_modal=_modal,
        _sesion_log=MagicMock(),
        _executor=_SyncExec(),
    )
    servicio = MultiPromptService(app)
    servicio._mostrar_guion_cortometraje = MagicMock()
    servicio._visto = visto
    return servicio


class TestDesdeElPanelNoHayQueCambiarElModo:

    def test_en_modo_imagen_el_guion_se_genera_igual(self):
        """El tropiezo que habia que quitar: tres referencias analizadas y un
        «solo disponible en modo VIDEO» obligandote a cerrar el panel."""
        h = _host(modo="imagen")
        h._cmd_cortometraje(premisa="La mujer de A espera en la estacion de B.",
                            contexto=shortfilm_context(_tres(), ANALISIS))
        assert "peticion" in h._visto, "no llego a pedir el guion"
        h._mostrar_guion_cortometraje.assert_called_once()

    def test_el_contexto_de_las_referencias_llega_al_guionista(self):
        h = _host(modo="imagen")
        contexto = shortfilm_context(_tres(), ANALISIS, "el rostro de A", "el fondo")
        h._cmd_cortometraje(premisa="La mujer de A espera en la estacion de B.",
                            contexto=contexto)
        peticion = h._visto["peticion"]
        assert contexto in peticion, "el contexto no viaja entero"
        assert ANALISIS in peticion
        assert "CONSERVAR: el rostro de A" in peticion

    def test_la_premisa_es_la_del_panel_y_no_la_caja_principal(self):
        h = _host(modo="imagen", idea="ESTO ES LA CAJA PRINCIPAL")
        h._cmd_cortometraje(premisa="La mujer de A espera en la estacion de B.",
                            contexto=shortfilm_context(_tres(), ANALISIS))
        peticion = h._visto["peticion"]
        assert "La mujer de A espera" in peticion
        assert "CAJA PRINCIPAL" not in peticion

    def test_no_se_mezcla_el_personaje_del_pie(self):
        """Dos repartos distintos en la misma peticion dejarian al guionista
        eligiendo entre las referencias reales y un personaje suelto."""
        h = _host(modo="imagen", personaje="Emma del pie")
        h._cmd_cortometraje(premisa="La mujer de A espera en la estacion de B.",
                            contexto=shortfilm_context(_tres(), ANALISIS))
        assert "Emma del pie" not in h._visto["peticion"]
        h.app.footer.personaje_activo.assert_not_called()

    def test_una_premisa_demasiado_corta_no_gasta_nada(self):
        h = _host(modo="imagen")
        h._cmd_cortometraje(premisa="corta", contexto="lo que sea")
        assert "peticion" not in h._visto
        h.app.dialogs.set_estado.assert_called_once()


class TestElCortometrajeDeSiempreNoCambia:

    def test_sigue_cerrado_a_modo_video(self):
        h = _host(modo="imagen")
        h._cmd_cortometraje()
        assert "VÍDEO" in h.app.dialogs.set_estado.call_args[0][0]
        assert "peticion" not in h._visto

    def test_sigue_leyendo_la_caja_de_idea_principal(self):
        h = _host(modo="video", idea="una premisa larga de la ventana principal")
        h._cmd_cortometraje()
        assert "ventana principal" in h._visto["peticion"]

    def test_sigue_usando_el_personaje_activo_del_pie(self):
        h = _host(modo="video", personaje="Emma: mujer fria")
        h._cmd_cortometraje()
        assert "Emma: mujer fria" in h._visto["peticion"]
        h.app.footer.personaje_activo.assert_called_once()

    def test_idea_vacia_sigue_avisando(self):
        h = _host(modo="video", idea="")
        h._cmd_cortometraje()
        h.app.dialogs.set_estado.assert_called_once()
        assert "peticion" not in h._visto


class TestLosDosIdiomas:

    def test_el_guion_se_pide_en_el_idioma_elegido(self):
        contexto = shortfilm_context(_tres(), ANALISIS)
        assert "INGLÉS" in construir_peticion_cortometraje("premisa", contexto, 4, "en")
        assert "ESPAÑOL" in construir_peticion_cortometraje("premisa", contexto, 4, "es")

    def test_el_contexto_no_se_traduce(self):
        """Lo que va al LLM se queda en espanol, como VISUAL_SYSTEM y el resto
        de constructores: traducirlo cambiaria el prompt segun el idioma de la
        interfaz, que no es lo que el usuario elige en «Idioma del prompt»."""
        import modules.i18n as i18n

        previo = i18n.get_idioma()
        try:
            i18n.set_idioma("en")
            t = shortfilm_context(_tres(), ANALISIS)
            assert "REFERENCIAS VISUALES REALES" in t
            assert "Personaje" in t
        finally:
            i18n.set_idioma(previo)


# ───────────────── el botón del panel ─────────────────

ctk = pytest.importorskip("customtkinter")

from modules import i18n  # noqa: E402
from modules.visual_studio import VisualStudio  # noqa: E402


class _VisionFalsa:
    def nombres_proveedores(self):
        return ["Gemini", "Ollama"]

    def describir_con_prompt(self, *_a, **_k):
        return "descripcion", "Gemini/x"


def _bombear(root, ms=120):
    bombear(root, ms)


@pytest.fixture()
def panel(tk_root):
    for w in list(tk_root.winfo_children()):
        if isinstance(w, VisualStudio):
            try:
                w.destroy()
            except Exception:
                pass
    tk_root.vision = _VisionFalsa()
    tk_root.multi = SimpleNamespace(cmd_cortometraje=MagicMock())
    v = VisualStudio(tk_root)
    _bombear(tk_root)
    yield v
    try:
        v.destroy()
    except Exception:
        pass
    for nombre in ("vision", "multi"):
        try:
            delattr(tk_root, nombre)
        except Exception:
            pass


def _preparar(panel, idea="La mujer de A espera sola en la estacion de B.",
              analisis=ANALISIS, refs=True):
    if refs:
        panel.refs.extend(_tres())
    panel.idea.delete("1.0", "end")
    panel.idea.insert("1.0", idea)
    panel.analysis.delete("1.0", "end")
    panel.analysis.insert("1.0", analisis)


class TestElBotonDelPanel:

    def test_el_boton_existe_con_su_traduccion(self, panel):
        def _botones(w):
            for hijo in w.winfo_children():
                if isinstance(hijo, ctk.CTkButton):
                    yield hijo.cget("text")
                yield from _botones(hijo)

        etiquetas = list(_botones(panel))
        esperada = i18n.tr("Crear cortometraje con estas referencias")
        assert esperada in etiquetas, etiquetas

    def test_pulsarlo_manda_premisa_y_contexto(self, panel):
        _preparar(panel)
        panel.shortfilm()
        llamada = panel.app.multi.cmd_cortometraje
        llamada.assert_called_once()
        kwargs = llamada.call_args.kwargs
        assert kwargs["premisa"].startswith("La mujer de A")
        contexto = kwargs["contexto"]
        assert "Personaje" in contexto and "Escenario" in contexto and "Estilo" in contexto
        assert ANALISIS in contexto

    def test_conservar_y_cambiar_del_panel_viajan(self, panel):
        _preparar(panel)
        panel.preserve.insert(0, "el rostro y los auriculares de A")
        panel.change.insert(0, "nada del personaje de C")
        panel.shortfilm()
        contexto = panel.app.multi.cmd_cortometraje.call_args.kwargs["contexto"]
        assert "CONSERVAR: el rostro y los auriculares de A" in contexto
        assert "CAMBIAR: nada del personaje de C" in contexto

    def test_sin_analisis_avisa_en_el_panel_y_no_llama(self, panel):
        """El aviso tiene que verse AQUI: el estado de la ventana principal
        puede estar tapado por el propio panel."""
        _preparar(panel, analisis="")
        panel.shortfilm()
        panel.app.multi.cmd_cortometraje.assert_not_called()
        assert panel.status.get(), "no se dijo nada"

    def test_sin_referencias_avisa_y_no_llama(self, panel):
        _preparar(panel, refs=False)
        panel.shortfilm()
        panel.app.multi.cmd_cortometraje.assert_not_called()
        assert "referencia" in panel.status.get().lower()

    def test_premisa_corta_avisa_y_no_llama(self, panel):
        _preparar(panel, idea="corta")
        panel.shortfilm()
        panel.app.multi.cmd_cortometraje.assert_not_called()
        assert panel.status.get()

    def test_sin_cortometraje_detras_no_revienta(self, panel):
        """El panel se construye en tests colgando de un root pelado."""
        _preparar(panel)
        delattr(panel.app, "multi")
        panel.shortfilm()
        assert panel.status.get()

    def test_analisis_caducado_bloquea(self, panel):
        """El agujero que ChatGPT vio antes que yo: cambiar una referencia tras
        analizar deja las letras del analisis apuntando a otras imagenes, y el
        guion saldria con @ref1 sobre la imagen equivocada."""
        _preparar(panel)
        panel.invalidate()
        panel.shortfilm()
        panel.app.multi.cmd_cortometraje.assert_not_called()
        assert "analizar" in panel.status.get().lower(), panel.status.get()

    def test_reordenar_las_referencias_tambien_bloquea(self, panel):
        """Reordenar no cambia QUE imagenes hay, pero si a que letra
        corresponde cada una, que es justo lo que lee el guionista."""
        _preparar(panel)
        panel.refs.reverse()
        panel.invalidate()
        panel.shortfilm()
        panel.app.multi.cmd_cortometraje.assert_not_called()

    def test_tras_volver_a_analizar_deja_pasar(self, panel):
        _preparar(panel)
        panel.invalidate()
        panel.analysis_stale = False
        panel.shortfilm()
        panel.app.multi.cmd_cortometraje.assert_called_once()


# ───────────────── idioma, formato y cancelación ─────────────────


class TestElMapaDeRefs:
    """Las letras cuentan todas las imágenes; los @ref solo los personajes."""

    def test_la_letra_y_el_numero_coinciden(self):
        """Numerar solo los personajes creaba un desfase invisible: con A
        escenario y B personaje, B era @ref1 mientras la letra decia B."""
        from modules.visual_brief import shortfilm_ref_map
        refs = [_ref("Escenario", "estacion.png"), _ref("Personaje", "chica.png")]
        assert shortfilm_ref_map(refs) == [("@ref1", "estacion.png"),
                                           ("@ref2", "chica.png")]

    def test_entran_todas_y_en_orden(self):
        from modules.visual_brief import shortfilm_ref_map
        refs = [_ref("Personaje", "a.png"), _ref("Estilo", "c.png"),
                _ref("Personaje", "b.png")]
        assert shortfilm_ref_map(refs) == [("@ref1", "a.png"), ("@ref2", "c.png"),
                                           ("@ref3", "b.png")]

    def test_sin_referencias_no_hay_mapa(self):
        from modules.visual_brief import shortfilm_ref_map
        assert shortfilm_ref_map([]) == []

    def test_sin_personajes_sigue_habiendo_imagenes_que_subir(self):
        from modules.visual_brief import shortfilm_ref_map
        mapa = shortfilm_ref_map([_ref("Escenario", "e.png"), _ref("Estilo", "s.png")])
        assert mapa == [("@ref1", "e.png"), ("@ref2", "s.png")]


class TestElFormatoLlegaAlGuion:

    def test_apaisado_cambia_la_formula_entera(self):
        p = construir_peticion_cortometraje("premisa", "ctx", 4, "es", "16:9")
        assert "drama apaisado" in p, "sigue pidiendo un corto vertical"
        assert "FORMATO: 16:9 (apaisado)" in p
        assert "Encuadra todos los planos para 16:9" in p

    def test_vertical_sigue_siendo_vertical(self):
        p = construir_peticion_cortometraje("premisa", "ctx", 4, "es", "9:16")
        assert "drama vertical" in p
        assert "FORMATO: 9:16 (vertical)" in p

    def test_cuadrado_tiene_su_palabra(self):
        assert "drama cuadrado" in construir_peticion_cortometraje(
            "premisa", "ctx", 4, "es", "1:1")

    def test_sin_formato_la_peticion_es_la_de_siempre(self):
        """La entrada clásica no puede cambiar por un parámetro que no usa."""
        p = construir_peticion_cortometraje("premisa", "ctx", 4, "es")
        assert "drama vertical estilo Netflix/redes" in p
        assert "FORMATO:" not in p
        assert "Encuadra todos los planos" not in p


class TestElPanelMandaSusOpciones:
    """Lo que pidió ChatGPT: comprobar la petición FINAL que recibe el
    proveedor simulado, no solo los argumentos de la llamada intermedia."""

    def _puente_real(self, panel, modo="imagen"):
        from modules.components import MultiPromptComponent
        visto = {}

        def _generar(peticion, **_k):
            visto["peticion"] = peticion
            return "=== PERSONAJES ==="

        def _modal(*_a, **kw):
            visto.setdefault("modal", []).append(kw)
            return (4, 8) if "segundos" in kw else 4

        host = SimpleNamespace(
            modo_var=_var(modo),
            txt_idea=_txt("caja principal sin usar"),
            deepseek=SimpleNamespace(generar=_generar),
            footer=SimpleNamespace(personaje_activo=MagicMock(return_value="")),
            dialogs=SimpleNamespace(set_estado=MagicMock(), toggle_botones=MagicMock(),
                                    _sonar_completado=MagicMock()),
            after=lambda _ms, fn=None, *a: fn() if callable(fn) else None,
            _pedir_n_modal=_modal,
            _sesion_log=MagicMock(),
            _executor=_SyncExec(),
        )
        componente = MultiPromptComponent(host)
        componente._service._mostrar_guion_cortometraje = MagicMock()
        panel.app.multi = componente
        return visto

    def test_interfaz_espanola_con_prompt_ingles_y_16_9(self, panel):
        """El caso que estaba roto: la interfaz en español imponía el idioma
        del guion aunque el panel pidiera inglés."""
        previo = i18n.get_idioma()
        try:
            i18n.set_idioma("es")
            visto = self._puente_real(panel)
            _preparar(panel)
            panel.language.set("Inglés")
            panel.aspect.set("16:9")
            panel.shortfilm()
            peticion = visto["peticion"]
            assert "INGLÉS" in peticion, "el guion se pidió en el idioma de la interfaz"
            assert "FORMATO: 16:9 (apaisado)" in peticion
            assert "drama apaisado" in peticion
        finally:
            i18n.set_idioma(previo)

    def test_prompt_espanol_con_interfaz_inglesa(self, panel):
        previo = i18n.get_idioma()
        try:
            i18n.set_idioma("en")
            visto = self._puente_real(panel)
            _preparar(panel)
            panel.language.set("Español")
            panel.aspect.set("9:16")
            panel.shortfilm()
            assert "ESPAÑOL" in visto["peticion"]
        finally:
            i18n.set_idioma(previo)

    def test_el_contexto_completo_llega_al_proveedor(self, panel):
        visto = self._puente_real(panel)
        _preparar(panel)
        panel.preserve.insert(0, "el rostro de A")
        panel.shortfilm()
        peticion = visto["peticion"]
        assert ANALISIS in peticion
        assert "@ref1" in peticion
        assert "CONSERVAR: el rostro de A" in peticion
        assert "SOLO la estetica" in peticion
        # Las tres imagenes con su etiqueta, no solo el personaje.
        for etiqueta in ("@ref1", "@ref2", "@ref3"):
            assert etiqueta in peticion, "falta " + etiqueta

    def test_el_estado_dice_que_imagen_subir(self, panel):
        self._puente_real(panel)
        _preparar(panel)
        panel.shortfilm()
        assert "@ref1 = chica.png" in panel.status.get(), panel.status.get()

    def test_el_estado_lista_las_tres_imagenes(self, panel):
        """La barra decia «@ref1 = chica.png» y el guion usaba @ref2 y @ref3:
        seguirla al pie de la letra dejaba dos imagenes sin subir."""
        TestElPanelMandaSusOpciones()._puente_real(panel)
        _preparar(panel)
        panel.shortfilm()
        estado = panel.status.get()
        for esperado in ("@ref1 = chica.png", "@ref2 = estacion.png",
                         "@ref3 = cyber.png"):
            assert esperado in estado, "falta " + esperado + " en: " + estado


class TestCancelarNoMiente:

    def test_cancelar_el_numero_de_escenas_no_dice_que_va(self, panel):
        """Antes se anunciaba «van tus referencias» aunque no se generara nada."""
        panel.app.multi = SimpleNamespace(cmd_cortometraje=MagicMock(return_value=None))
        _preparar(panel)
        panel.shortfilm()
        assert "cancel" in panel.status.get().lower(), panel.status.get()

    def test_el_servicio_avisa_de_que_arranco(self):
        h = _host(modo="imagen")
        arrancado = h._cmd_cortometraje(premisa="La mujer de A espera en la estacion.",
                                        contexto="ctx")
        assert arrancado is True

    def test_el_servicio_no_lo_dice_si_cancelan(self):
        h = _host(modo="imagen")
        h.app._pedir_n_modal = lambda *a, **k: None
        assert not h._cmd_cortometraje(premisa="La mujer de A espera en la estacion.",
                                       contexto="ctx")

    def test_la_fachada_reenvia_todas_las_opciones(self):
        from modules.components import MultiPromptComponent
        componente = MultiPromptComponent(SimpleNamespace())
        componente._service = SimpleNamespace(_cmd_cortometraje=MagicMock())
        componente.cmd_cortometraje(premisa="p", contexto="c", idioma="en",
                                    aspecto="16:9", segundos="8")
        componente._service._cmd_cortometraje.assert_called_once_with(
            "p", "c", "en", "16:9", "8")


class TestLasEtiquetasSiguenAlIdioma:
    """El guion salía mezclado: acción y diálogo en inglés, pero «Plano» y
    «Tema» en español. La plantilla tenía las etiquetas a fuego en español y
    el modelo las copiaba, arrastrando con ellas los campos cortos.
    """

    ES = ("Tiempo:", "Plano:", "Tema:", "Acción:", "Cámara:", "Diálogo:")
    EN = ("Time:", "Shot:", "Theme:", "Action:", "Camera:", "Dialogue:")

    def test_en_ingles_las_etiquetas_van_en_ingles(self):
        p = construir_peticion_cortometraje("premisa", "ctx", 4, "en")
        for etiqueta in self.EN:
            assert etiqueta in p, "falta " + etiqueta
        assert "=== CHARACTERS ===" in p
        assert "=== SCENE 1 ===" in p

    def test_en_ingles_no_se_cuela_ninguna_etiqueta_espanola(self):
        p = construir_peticion_cortometraje("premisa", "ctx", 4, "en")
        for etiqueta in self.ES:
            assert etiqueta not in p, "se cuela " + etiqueta
        assert "=== ESCENA" not in p
        assert "=== PERSONAJES ===" not in p

    def test_la_ultima_escena_tambien_se_traduce(self):
        """El «continúa hasta === ESCENA n ===» es donde mas facil se olvida."""
        p = construir_peticion_cortometraje("premisa", "ctx", 7, "en")
        assert "=== SCENE 7 ===" in p

    def test_en_espanol_la_plantilla_es_la_de_siempre(self):
        """Candado de la entrada clásica: ni una etiqueta cambiada."""
        p = construir_peticion_cortometraje("premisa", "ctx", 4, "es")
        for etiqueta in self.ES:
            assert etiqueta in p, "falta " + etiqueta
        assert "=== PERSONAJES ===" in p
        assert "=== ESCENA 1 ===" in p
        for etiqueta in self.EN:
            assert etiqueta not in p, "se cuela " + etiqueta

    def test_sfx_es_igual_en_los_dos(self):
        for idioma in ("es", "en"):
            assert "SFX:" in construir_peticion_cortometraje("p", "c", 3, idioma)

    def test_se_pide_explicitamente_traducir_las_etiquetas(self):
        """Traducir la plantilla no basta si la orden no lo menciona: el modelo
        puede «corregirla» de vuelta al idioma en que esta escrito el resto."""
        p = construir_peticion_cortometraje("premisa", "ctx", 4, "en")
        assert "incluidas las etiquetas" in p

    def test_desde_el_panel_en_ingles_llegan_etiquetas_inglesas(self, panel):
        """El recorrido entero, que es donde se vio el fallo."""
        visto = TestElPanelMandaSusOpciones()._puente_real(panel)
        _preparar(panel)
        panel.language.set("Inglés")
        panel.shortfilm()
        peticion = visto["peticion"]
        assert "=== SCENE 1 ===" in peticion
        assert "Shot:" in peticion and "Theme:" in peticion
        assert "Plano:" not in peticion and "Tema:" not in peticion


class TestLaDuracionPorEscena:
    """El primer guion se fue a 13s en una escena con la banda «5-12s». Sin un
    objetivo concreto el reparto es una sugerencia, y cada escena se genera
    como un clip aparte: pasarse significa un clip que hay que repetir.
    """

    def test_con_segundos_la_regla_es_exacta(self):
        p = construir_peticion_cortometraje("premisa", "ctx", 4, "es", None, "8")
        assert "EXACTAMENTE 8 segundos" in p
        assert "5-12s" not in p, "sigue la banda ancha junto a la regla exacta"

    def test_se_dice_la_duracion_total(self):
        p = construir_peticion_cortometraje("premisa", "ctx", 6, "es", None, "8")
        assert "DURACIÓN POR ESCENA: 8 segundos" in p
        assert "total del corto: 48 segundos" in p

    def test_se_pide_encadenar_los_tramos(self):
        """El guion traia 0-9s, 9-20s, 20-32s, 32-45s: tramos que no cuadraban
        con ninguna duracion fija."""
        p = construir_peticion_cortometraje("premisa", "ctx", 4, "es", None, "8")
        assert "sin huecos ni solapes" in p

    def test_sin_segundos_la_regla_es_la_de_siempre(self):
        p = construir_peticion_cortometraje("premisa", "ctx", 4, "es")
        assert "- Cada escena es un clip independiente de 5-12s." in p
        assert "DURACIÓN POR ESCENA" not in p
        # «EXACTAMENTE» a secas ya sale en «con EXACTAMENTE este formato».
        assert "dura EXACTAMENTE" not in p

    def test_una_duracion_ilegible_no_inventa_un_total(self):
        """El campo del panel es texto libre; antes de mentir, callar."""
        p = construir_peticion_cortometraje("premisa", "ctx", 4, "es", None, "ocho")
        assert "EXACTAMENTE ocho segundos" in p
        assert "total del corto" not in p

    def test_decimales(self):
        p = construir_peticion_cortometraje("premisa", "ctx", 3, "es", None, "7.5")
        assert "total del corto: 22.5 segundos" in p


class TestElPanelYLaDuracion:

    def test_los_segundos_del_modal_llegan_a_la_peticion(self, panel):
        visto = TestElPanelMandaSusOpciones()._puente_real(panel)
        _preparar(panel)
        panel.shortfilm()
        assert "EXACTAMENTE 8 segundos" in visto["peticion"]

    def test_en_salida_de_imagen_el_modal_pregunta_igual(self, panel):
        """Preparar un corto no debe obligar a cambiar el destino del panel a
        vídeo solo para que aparezca el campo «Segundos»."""
        visto = TestElPanelMandaSusOpciones()._puente_real(panel)
        _preparar(panel)
        panel.target.set("Imagen")
        panel.shortfilm()
        assert "segundos" in visto["modal"][0], "el modal no pidió la duración"
        assert "EXACTAMENTE 8 segundos" in visto["peticion"]
        assert "5-12s" not in visto["peticion"]

    def test_el_panel_prerrellena_el_modal_con_su_duracion(self, panel):
        """Si el panel ya tiene una duración elegida, el modal parte de ella."""
        visto = TestElPanelMandaSusOpciones()._puente_real(panel)
        _preparar(panel)
        panel.target.set("Vídeo")
        panel.mode.set("Animar imagen")
        panel.duration.set("11")
        panel.shortfilm()
        assert visto["modal"][0]["segundos"] == "11"

    def test_el_cortometraje_clasico_no_pregunta_segundos(self):
        """Candado: la entrada de la ventana principal conserva su modal."""
        h = _host(modo="video")
        h._cmd_cortometraje()
        assert "segundos" not in h._visto["modal"][0]
        assert "5-12s" in h._visto["peticion"]

    def test_cancelar_el_modal_con_segundos_no_genera(self):
        h = _host(modo="imagen")
        h.app._pedir_n_modal = lambda *a, **k: None
        assert not h._cmd_cortometraje(premisa="La mujer de A espera en la estacion.",
                                       contexto="ctx")

    def test_una_duracion_invalida_avisa_y_no_gasta(self, panel):
        visto = TestElPanelMandaSusOpciones()._puente_real(panel)
        _preparar(panel)
        panel.target.set("Vídeo")
        panel.mode.set("Animar imagen")
        panel.duration.set("-3")
        panel.shortfilm()
        assert "peticion" not in visto, "se pidio el guion con una duracion invalida"
        assert panel.status.get()


class TestLaRevisionLocalDelGuion:
    """Pedirle algo al modelo no garantiza que lo cumpla. Esto se comprueba en
    local, sin ninguna llamada, así que se mira siempre.
    """

    GUION_REAL = (
        "=== SCENE 1 ===\nTime: 0-9s\n"
        "=== SCENE 2 ===\nTime: 9-20s\n"
        "=== SCENE 3 ===\nTime: 20-32s\n"
        "=== SCENE 4 ===\nTime: 32-45s\n"
    )
    GUION_OK = ("=== ESCENA 1 ===\nTiempo: 0-8s\n"
                "=== ESCENA 2 ===\nTiempo: 8-16s\n")

    def test_un_guion_que_cuadra_no_genera_avisos(self):
        from modules.multiprompt import revisar_guion_cortometraje
        assert revisar_guion_cortometraje(self.GUION_OK, 2, "8") == []

    def test_caza_la_escena_de_13_segundos(self):
        """El caso real: banda 5-12s y una escena de 13."""
        from modules.multiprompt import revisar_guion_cortometraje
        avisos = revisar_guion_cortometraje(self.GUION_REAL, 4, "8")
        assert any("13s" in a for a in avisos), avisos

    def test_caza_que_falten_escenas(self):
        from modules.multiprompt import revisar_guion_cortometraje
        avisos = revisar_guion_cortometraje(self.GUION_OK, 6, None)
        assert any("6" in a and "2" in a for a in avisos), avisos

    def test_caza_un_hueco_entre_escenas(self):
        from modules.multiprompt import revisar_guion_cortometraje
        hueco = "=== ESCENA 1 ===\nTiempo: 0-8s\n=== ESCENA 2 ===\nTiempo: 12-20s\n"
        avisos = revisar_guion_cortometraje(hueco, 2, "8")
        assert any("empieza en 12s" in a for a in avisos), avisos

    def test_caza_una_referencia_que_no_existe(self):
        """@ref7 con tres imágenes es un guion imposible de montar."""
        from modules.multiprompt import revisar_guion_cortometraje
        texto = self.GUION_OK + "Action: Mara@ref1 y Ghost@ref7\n"
        avisos = revisar_guion_cortometraje(texto, 2, "8", 3)
        assert any("@ref7" in a for a in avisos), avisos

    def test_las_referencias_validas_no_avisan(self):
        from modules.multiprompt import revisar_guion_cortometraje
        texto = self.GUION_OK + "Action: Mara@ref1 en Station@ref2\n"
        assert revisar_guion_cortometraje(texto, 2, "8", 3) == []

    def test_sin_duracion_se_mide_contra_la_banda_de_la_plantilla(self):
        """Este test afirmaba lo contrario —«sin duración no hay nada que
        medir»— y esa premisa era el propio fallo: la plantilla sigue pidiendo
        5-12s, así que la escena de 13s del guion real tenía que avisar y no
        avisaba. Lo encontró ChatGPT ejecutando la función aislada.
        """
        from modules.multiprompt import revisar_guion_cortometraje
        avisos = revisar_guion_cortometraje(self.GUION_REAL, 4, None)
        assert any("13s" in a for a in avisos), avisos
        # Pero no se inventa una duración exacta que nadie fijó.
        assert not any("en vez de" in a for a in avisos), avisos

    def test_entiende_los_dos_idiomas_de_etiqueta(self):
        from modules.multiprompt import revisar_guion_cortometraje
        assert revisar_guion_cortometraje(self.GUION_OK, 2, "8") == []
        ingles = "=== SCENE 1 ===\nTime: 0-8s\n=== SCENE 2 ===\nTime: 8-16s\n"
        assert revisar_guion_cortometraje(ingles, 2, "8") == []

    def test_un_guion_vacio_no_revienta(self):
        from modules.multiprompt import revisar_guion_cortometraje
        assert revisar_guion_cortometraje("", 4, "8", 3)
        assert revisar_guion_cortometraje(None, 4, "8", 3)

    def test_los_avisos_llegan_a_la_ventana(self):
        """De nada sirve detectarlo si no se ve antes de copiar el guion."""
        h = _host(modo="imagen")
        h.app.deepseek = SimpleNamespace(
            generar=lambda *a, **k: TestLaRevisionLocalDelGuion.GUION_REAL)
        h._cmd_cortometraje(premisa="La mujer de A espera en la estacion.",
                            contexto="A · @ref1 · Personaje — chica.png")
        h._mostrar_guion_cortometraje.assert_called_once()
        avisos = h._mostrar_guion_cortometraje.call_args[0][2]
        assert avisos, "la ventana no recibio ningun aviso"


class TestLosTresCasosQueSeEscapaban:
    """Los encontró ChatGPT ejecutando la función aislada. El patrón común es
    el peor posible en un comprobador: cuanto MENOS información traía el
    guion, menos avisaba. Un guion sin tiempos pasaba limpio.
    """

    def test_escenas_sin_campo_de_tiempo(self):
        from modules.multiprompt import revisar_guion_cortometraje
        texto = "=== SCENE 1 ===\nAction: x\n=== SCENE 2 ===\nAction: y\n"
        avisos = revisar_guion_cortometraje(texto, 2, "8")
        assert avisos, "un guion sin tiempos pasaba limpio"
        assert any("tiempo legible" in a for a in avisos), avisos

    def test_dos_escenas_con_el_mismo_numero(self):
        """Parece un guion entero y al montarlo te falta un clip."""
        from modules.multiprompt import revisar_guion_cortometraje
        texto = "=== SCENE 1 ===\nTime: 0-8s\n=== SCENE 1 ===\nTime: 8-16s\n"
        avisos = revisar_guion_cortometraje(texto, 2, "8")
        assert any("numeradas" in a for a in avisos), avisos

    def test_numeracion_saltada(self):
        from modules.multiprompt import revisar_guion_cortometraje
        texto = "=== ESCENA 1 ===\nTiempo: 0-8s\n=== ESCENA 3 ===\nTiempo: 8-16s\n"
        assert any("numeradas" in a
                   for a in revisar_guion_cortometraje(texto, 2, "8"))

    def test_la_banda_de_la_plantilla_se_mide_sin_duracion_fija(self):
        """El recorrido clásico no fija duración, pero la plantilla sigue
        pidiendo 5-12s: hay contra qué medir."""
        from modules.multiprompt import revisar_guion_cortometraje
        avisos = revisar_guion_cortometraje("=== ESCENA 1 ===\nTiempo: 0-13s\n", 1, None)
        assert any("5-12s" in a for a in avisos), avisos

    def test_dentro_de_la_banda_no_avisa(self):
        from modules.multiprompt import revisar_guion_cortometraje
        assert revisar_guion_cortometraje("=== ESCENA 1 ===\nTiempo: 0-9s\n", 1, None) == []

    def test_demasiado_corta_tambien_avisa(self):
        from modules.multiprompt import revisar_guion_cortometraje
        assert any("5-12s" in a for a in
                   revisar_guion_cortometraje("=== ESCENA 1 ===\nTiempo: 0-3s\n", 1, None))

    def test_la_banda_sale_de_la_constante_que_usa_la_plantilla(self):
        """Candado: si la plantilla cambia de banda y el comprobador no, este
        mide contra algo que ya nadie pidió."""
        from modules.multiprompt import (
            BANDA_CORTO,
            construir_peticion_cortometraje,
        )
        peticion = construir_peticion_cortometraje("premisa", "ctx", 4, "es")
        assert f"{BANDA_CORTO[0]}-{BANDA_CORTO[1]}s" in peticion
