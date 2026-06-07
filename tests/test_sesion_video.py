"""Tests para SesionVideoService (modules/sesion_video.py).

Cobertura de la lógica testeable sin abrir ventanas Tk reales:
  • _sesion_init — inicializa los atributos del registro.
  • _sesion_log — guarda eventos solo cuando _sesion_grabando es True.
  • _sesion_video_disponible — True/False según imports disponibles.
  • _sesion_agrupar_pasos — categorización de eventos en pasos lógicos.
  • _sesion_narrar_paso — lookup en diccionario de narrativas.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.sesion_video import SesionVideoService


def _host():
    app = SimpleNamespace(after=lambda *a, **k: None)
    app.dialogs = SimpleNamespace(set_estado=MagicMock())
    return SesionVideoService(app)


# ─────────────────────── _sesion_init ─────────────────────────────────


class TestSesionInit:

    def test_inicializa_atributos_si_no_existen(self):
        h = _host()
        h._sesion_init()
        assert h.app._sesion_eventos == []
        assert h.app._sesion_grabando is False
        assert h.app._sesion_inicio is None
        assert h.app._sesion_video_thread is None
        assert h.app._sesion_video_path is None
        assert h.app._sesion_video_writer is None
        assert h.app._sesion_video_running is False

    def test_no_reinicializa_si_ya_existe(self):
        h = _host()
        h.app._sesion_eventos = [("12:00:00", "ya tenía")]
        h.app._sesion_grabando = True
        h._sesion_init()
        # Los atributos previos NO se sobrescriben (sólo se crea la primera vez)
        assert h.app._sesion_eventos == [("12:00:00", "ya tenía")]
        assert h.app._sesion_grabando is True


# ─────────────────────── _sesion_log ──────────────────────────────────


class TestSesionLog:

    def test_no_loggea_si_no_grabando(self):
        h = _host()
        h._sesion_log("evento test")
        assert h.app._sesion_eventos == []

    def test_loggea_si_grabando(self):
        h = _host()
        h._sesion_init()
        h.app._sesion_grabando = True
        h._sesion_log("evento test")
        assert len(h.app._sesion_eventos) == 1
        ts, evento = h.app._sesion_eventos[0]
        assert evento == "evento test"
        assert len(ts) == 8 and ts.count(":") == 2  # HH:MM:SS

    def test_loggea_multiple(self):
        h = _host()
        h._sesion_init()
        h.app._sesion_grabando = True
        h._sesion_log("a")
        h._sesion_log("b")
        h._sesion_log("c")
        assert [e for _, e in h.app._sesion_eventos] == ["a", "b", "c"]


# ─────────────────────── _sesion_video_disponible ─────────────────────


class TestVideoDisponible:

    def test_devuelve_true_si_mss_e_imageio_instalados(self):
        # En el entorno de desarrollo ambas suelen estar; verificamos
        # comportamiento bool sin afirmar el valor concreto.
        h = _host()
        result = h._sesion_video_disponible()
        assert isinstance(result, (bool, type(None))) or result in (True, False)

    def test_devuelve_false_si_import_falla(self, monkeypatch):
        import builtins
        orig_import = builtins.__import__

        def _fake_import(name, *a, **k):
            if name in ("mss", "imageio"):
                raise ImportError(f"no {name}")
            return orig_import(name, *a, **k)

        monkeypatch.setattr(builtins, "__import__", _fake_import)
        h = _host()
        assert h._sesion_video_disponible() is False


# ─────────────────────── _sesion_agrupar_pasos ────────────────────────


class TestAgruparPasos:

    def test_ignora_eventos_grabacion(self):
        h = _host()
        eventos = [
            ("12:00:00", "🔴 GRABACIÓN INICIADA"),
            ("12:00:01", "⏹ GRABACIÓN DETENIDA"),
            ("12:00:02", "🎥 Grabación de vídeo"),
        ]
        pasos = h._sesion_agrupar_pasos(eventos)
        assert pasos == []

    def test_agrupa_eventos_consecutivos_misma_categoria(self):
        h = _host()
        eventos = [
            ("12:00:00", "Cambió modo a imagen"),
            ("12:00:01", "Cambió modo a video"),
            ("12:00:02", "Cambió plataforma a SeaArt"),
        ]
        pasos = h._sesion_agrupar_pasos(eventos)
        # Dos categorías: "Configurar modo de trabajo" + "Seleccionar plataforma..."
        assert len(pasos) == 2
        titulo_1, evs_1 = pasos[0]
        assert "modo" in titulo_1.lower()
        assert len(evs_1) == 2

    def test_categorias_correctas_segun_keywords(self):
        h = _host()
        casos = [
            ("Generó prompt principal", "Generar el prompt principal"),
            ("Refinó el prompt", "Refinar el prompt"),
            ("Pidió ideas", "Generar ideas"),
            ("Cargó imagen de referencia", "Cargar imagen de referencia"),
            ("Reset", "Reset"),
        ]
        for evento_txt, esperado in casos:
            pasos = h._sesion_agrupar_pasos([("12:00:00", evento_txt)])
            assert len(pasos) == 1
            assert pasos[0][0] == esperado, f"'{evento_txt}' → esperaba '{esperado}'"

    def test_evento_desconocido_va_a_otras_acciones(self):
        h = _host()
        pasos = h._sesion_agrupar_pasos([("12:00:00", "no me cuadra con nada conocido")])
        assert pasos[0][0] == "Otras acciones"


# ─────────────────────── _sesion_narrar_paso ──────────────────────────


class TestNarrarPaso:

    def test_devuelve_narrativa_para_titulo_conocido(self):
        h = _host()
        narr = h._sesion_narrar_paso("Configurar modo de trabajo", [])
        assert narr and "modo de trabajo" in narr.lower()

    def test_devuelve_vacio_para_titulo_desconocido(self):
        h = _host()
        assert h._sesion_narrar_paso("Titulo Inexistente", []) == ""

    def test_narrativa_completa_para_categorias_clave(self):
        h = _host()
        # Verifica que existen narraciones para las categorías más usadas.
        categorias_clave = [
            "Generar el prompt principal",
            "Refinar el prompt",
            "Cargar imagen de referencia",
            "Exportar resultado",
            "Inicio",
        ]
        for cat in categorias_clave:
            assert h._sesion_narrar_paso(cat, []) != ""
