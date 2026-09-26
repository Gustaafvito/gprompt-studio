"""Si el root compartido de Tk no se crea, el informe tiene que decir por qué.

De la fixture de sesión `tk_root` cuelgan 62 tests. pytest CACHEA la excepción
de una fixture de sesión y la relanza en cada test que la pida, así que un
único fallo al crear el root sale en el informe como 62 errores de setup
idénticos, repartidos por seis ficheros distintos.

Leído sin contexto, eso parece una cascada: «empieza en TestElBotonDelPanel y
contagia a todo lo que abre ventana después». No lo es —ese test es sólo el
PRIMERO de los 62 en orden de colección— y perseguir la cascada cuesta una
sesión entera revisando fixtures que no tienen la culpa.

El fallo es intermitente y no se ha conseguido reproducir (272 tiradas). Por
eso lo que se vigila aquí no es que el root se cree, sino que el día que NO se
cree quede escrito qué pasó: sin el texto real del TclError no se puede
distinguir un problema de DPI, de escritorio bloqueado o de un root anterior
mal destruido.
"""
from pathlib import Path

CONFTEST = Path(__file__).with_name("conftest.py").read_text(encoding="utf-8")


class TestElFalloDelRootDejaPrueba:

    def test_la_creacion_del_root_esta_protegida(self):
        # Sin el try, la excepción sale cruda y sin explicación 62 veces.
        assert "crear_con_reintentos(ctk.CTk)" in CONFTEST, \
            "el root ya no se crea con reintentos"
        cuerpo = CONFTEST[CONFTEST.index("def tk_root():"):]
        i_try = cuerpo.index("try:")
        i_crea = cuerpo.index("crear_con_reintentos(ctk.CTk)")
        assert i_try < i_crea, "la creación del root salió del try"
        assert "_dejar_prueba_del_fallo()" in cuerpo[i_crea:]

    def test_la_app_real_de_barrido_tambien_reintenta(self):
        # ArquitectoApp hereda de ctk.CTk: es el TERCER intérprete de Tcl que
        # arranca cada proceso. Si se queda fuera, la misma avería sale como
        # los 24 errores de test_barrido_ui en vez de los 62 de tk_root.
        barrido = Path(__file__).with_name("test_barrido_ui.py").read_text(
            encoding="utf-8")
        assert "crear_con_reintentos(ArquitectoApp)" in barrido, \
            "la app de barrido_ui volvió a arrancar sin reintentos"

    def test_el_sondeo_de_disponibilidad_tambien_reintenta(self):
        # Si el sondeo se come el fallo transitorio, los 62 tests de interfaz
        # se SALTAN en silencio, que es peor que fallar.
        sondeo = CONFTEST[CONFTEST.index("def tk_disponible():"):
                          CONFTEST.index("def exigir_tk():")]
        assert "crear_con_reintentos(tkinter.Tk)" in sondeo

    def test_el_mensaje_avisa_de_que_los_demas_son_el_mismo_fallo(self):
        assert "ESTE MISMO fallo" in CONFTEST
        assert "cachea la excepción" in CONFTEST

    def test_se_deja_prueba_en_disco_con_el_entorno(self):
        assert "_dejar_prueba_del_fallo()" in CONFTEST
        assert "tk_root_fallido.log" in CONFTEST
        # Lo que hace falta para saber POR QUÉ falló, no sólo que falló.
        for dato in ("customtkinter=", "tcl=", "_default_root=", "format_exc"):
            assert dato in CONFTEST, f"el diagnóstico ya no anota {dato}"

    def test_dejar_prueba_nunca_puede_romper_la_suite(self):
        # Si el diagnóstico reventara, taparía el fallo que intenta explicar.
        cuerpo = CONFTEST[CONFTEST.index("def _dejar_prueba_del_fallo"):
                          CONFTEST.index("@pytest.fixture(scope=\"session\")\ndef tk_root")]
        assert "except Exception:" in cuerpo and "pass" in cuerpo


class TestLosBorradoresNoVanACasaDelUsuario:
    """Una tirada de tests no puede dejar proyectos en ~/.arquitecto_prompts.

    `VisualStudio` crea un `VisualHistory()` por panel y el autoguardado
    salta cada 15 s. Con cientos de paneles por suite, eso llenaba la
    carpeta del usuario de sesiones de test mezcladas con las suyas.
    """

    # Ojo: en Windows el temporal de pytest cuelga de la propia carpeta del
    # usuario (AppData\Local\Temp), asi que comprobar "no esta bajo home"
    # daria falso positivo. Lo que importa es que no caiga en la carpeta de
    # datos de la aplicacion, que es la que el usuario mira.
    CARPETA_DEL_USUARIO = Path.home() / ".arquitecto_prompts"

    def test_el_destino_por_defecto_es_temporal(self):
        from modules.visual_history import VisualHistory
        destino = Path(VisualHistory().root)
        assert "visual_drafts" in str(destino)
        assert self.CARPETA_DEL_USUARIO not in destino.parents, (
            f"los tests siguen escribiendo en la carpeta del usuario: "
            f"{destino}")

    def test_quien_pasa_su_ruta_manda(self, tmp_path):
        # La redirección no puede pisar a los tests que eligen destino.
        from modules.visual_history import VisualHistory
        assert VisualHistory(tmp_path).root == tmp_path

    def test_guardar_de_verdad_escribe_en_el_temporal(self):
        from modules.visual_history import VisualHistory
        historia = VisualHistory()
        historia.save([], {"idea": "una prueba"})
        escritos = list(Path(historia.root).rglob("*.gprompt"))
        assert escritos, "no escribió nada donde dice"
        assert self.CARPETA_DEL_USUARIO not in escritos[0].parents
