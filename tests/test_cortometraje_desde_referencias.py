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

    def test_el_escenario_no_lleva_ref(self):
        """Etiquetar un escenario con @ref lo convertiria en un personaje."""
        t = shortfilm_context([_ref("Escenario")], ANALISIS)
        assert "@ref" not in t

    def test_de_estilo_solo_viaja_la_estetica(self):
        """Es la fuga que costo dos pruebas manuales localizar: el personaje de
        la referencia de estilo colandose en la escena."""
        t = shortfilm_context([_ref("Estilo", "cyber.png")], ANALISIS)
        assert "SOLO estetica" in t
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
        t = shortfilm_context([_ref("Escenario"), _ref("Estilo")], ANALISIS)
        assert "inventa" in t.lower()
        assert "@ref" not in t

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

    app = SimpleNamespace(
        modo_var=_var(modo),
        txt_idea=_txt(idea),
        deepseek=SimpleNamespace(generar=_generar),
        footer=SimpleNamespace(personaje_activo=MagicMock(return_value=personaje)),
        dialogs=SimpleNamespace(set_estado=MagicMock(), toggle_botones=MagicMock(),
                                _sonar_completado=MagicMock()),
        after=lambda _ms, fn=None, *a: fn() if callable(fn) else None,
        _pedir_n_modal=lambda *a, **k: 4,
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
    root.after(ms, root.quit)
    root.mainloop()


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
