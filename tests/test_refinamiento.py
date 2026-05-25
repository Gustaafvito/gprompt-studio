"""Tests para RefinamientoMixin (modules/refinamiento.py).

Cobertura de la lógica testeable sin abrir ventanas Tk reales:
  • _mostrar_diff_refinamiento  — decisiones + versionado pre-refinamiento.
  • cmd_refinar                 — construcción de petición según modo/formato.
  • _iterar_elemento            — parsing de VARIANTE N en la respuesta LLM.
  • _menu_refinar_especifico    — guardas (texto vacío).

Los modales (GPromptWindow), threads (threading.Thread) y popups (tk.Menu) se
mockean para no requerir display ni dispatch de eventos.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from modules.refinamiento import RefinamientoMixin


def _var(value):
    """Imita un tk.StringVar / BooleanVar (solo .get())."""
    return SimpleNamespace(get=lambda: value)


def _txt(value):
    """Imita un tk.Text: get(start, end) devuelve value + '\\n'."""
    return SimpleNamespace(get=lambda *_a, **_k: value + "\n")


def _host(**attrs):
    """Construye un host con RefinamientoMixin y los atributos dados."""
    cls = type("Host", (RefinamientoMixin,), {})
    h = cls()
    defaults = dict(
        set_estado=MagicMock(),
        toggle_botones=MagicMock(),
        actualizar_salida=MagicMock(),
        guardar_en_historial=MagicMock(),
        _sonar_completado=MagicMock(),
        _ocultar_ideas=MagicMock(),
        _abrir_ventana_diff=MagicMock(),
        _abrir_comparador=MagicMock(),
        _sesion_log=MagicMock(),
        after=lambda _delay, fn=None: fn() if callable(fn) else None,
        personaje_activo=lambda: "",
        lora_activo=lambda: "",
        is_natural_mode=lambda: False,
        get_current_model_specs=lambda: None,
        _ultimo_anclaje_visual="",
    )
    defaults.update(attrs)
    for k, v in defaults.items():
        setattr(h, k, v)
    return h


# ──────────────────────── _mostrar_diff_refinamiento ────────────────────────


class TestMostrarDiffRefinamiento:

    def test_texto_previo_vacio_aplica_directo(self):
        h = _host()
        h._mostrar_diff_refinamiento("", "nuevo")
        h.actualizar_salida.assert_called_once_with("nuevo")
        h._abrir_ventana_diff.assert_not_called()

    def test_texto_nuevo_vacio_aplica_string_vacio(self):
        h = _host()
        h._mostrar_diff_refinamiento("prev", "")
        h.actualizar_salida.assert_called_once_with("")
        h._abrir_ventana_diff.assert_not_called()

    def test_textos_iguales_aplica_con_aviso(self):
        h = _host()
        h._mostrar_diff_refinamiento("igual", "igual")
        h.actualizar_salida.assert_called_once_with("igual")
        h.set_estado.assert_called_once()
        assert "no produjo cambios" in h.set_estado.call_args[0][0]
        h._abrir_ventana_diff.assert_not_called()

    def test_textos_distintos_abre_ventana_diff(self):
        h = _host()
        h._mostrar_diff_refinamiento("viejo", "nuevo")
        h._abrir_ventana_diff.assert_called_once()
        args, kwargs = h._abrir_ventana_diff.call_args
        assert args[0] == "viejo"
        assert args[1] == "nuevo"
        assert kwargs["label_a"] == "🔹 Original"
        assert kwargs["label_b"] == "🔸 Refinado"
        assert callable(kwargs["on_apply"])
        assert callable(kwargs["on_cancel"])

    def test_apply_guarda_version_pre_refinamiento(self):
        h = _host()
        h._mostrar_diff_refinamiento("viejo", "nuevo")
        on_apply = h._abrir_ventana_diff.call_args.kwargs["on_apply"]
        on_apply()
        h.actualizar_salida.assert_called_once_with("nuevo")
        assert hasattr(h, "_versiones_prompt")
        assert len(h._versiones_prompt) == 1
        ver = h._versiones_prompt[0]
        assert ver["texto"] == "viejo"
        assert "pre-refinamiento" in ver["etiqueta"]

    def test_apply_no_duplica_si_ultima_version_es_la_misma(self):
        h = _host()
        h._versiones_prompt = [{"texto": "viejo", "etiqueta": "v1 (pre-refinamiento)"}]
        h._mostrar_diff_refinamiento("viejo", "nuevo")
        on_apply = h._abrir_ventana_diff.call_args.kwargs["on_apply"]
        on_apply()
        assert len(h._versiones_prompt) == 1  # no se duplica

    def test_apply_limita_stack_a_30_versiones(self):
        h = _host()
        h._versiones_prompt = [
            {"texto": f"v{i}", "etiqueta": f"v{i} (pre-refinamiento)"}
            for i in range(30)
        ]
        h._mostrar_diff_refinamiento("nueva_version", "nuevo")
        on_apply = h._abrir_ventana_diff.call_args.kwargs["on_apply"]
        on_apply()
        assert len(h._versiones_prompt) == 30
        # La primera (v0) cayó del stack
        assert h._versiones_prompt[0]["texto"] == "v1"
        assert h._versiones_prompt[-1]["texto"] == "nueva_version"

    def test_undo_disponible_si_hay_pre_refinamiento_en_stack(self):
        h = _host()
        h._versiones_prompt = [
            {"texto": "anterior", "etiqueta": "v1 (pre-refinamiento)"},
        ]
        h._mostrar_diff_refinamiento("viejo", "nuevo")
        kwargs = h._abrir_ventana_diff.call_args.kwargs
        assert kwargs["on_undo"] is not None

    def test_undo_no_disponible_si_no_hay_pre_refinamiento(self):
        h = _host()
        h._mostrar_diff_refinamiento("viejo", "nuevo")
        kwargs = h._abrir_ventana_diff.call_args.kwargs
        assert kwargs["on_undo"] is None

    def test_undo_no_disponible_si_solo_hay_versiones_normales(self):
        h = _host()
        h._versiones_prompt = [{"texto": "x", "etiqueta": "v1"}]  # sin "pre-refinamiento"
        h._mostrar_diff_refinamiento("viejo", "nuevo")
        kwargs = h._abrir_ventana_diff.call_args.kwargs
        assert kwargs["on_undo"] is None

    def test_undo_restaura_y_remueve_del_stack(self):
        h = _host()
        ver = {"texto": "previa", "etiqueta": "v1 (pre-refinamiento)"}
        h._versiones_prompt = [ver]
        h._mostrar_diff_refinamiento("viejo", "nuevo")
        on_undo = h._abrir_ventana_diff.call_args.kwargs["on_undo"]
        on_undo()
        h.actualizar_salida.assert_called_with("previa")
        assert ver not in h._versiones_prompt
        assert h._versiones_prompt == []

    def test_undo_busca_la_pre_refinamiento_mas_reciente(self):
        h = _host()
        h._versiones_prompt = [
            {"texto": "muy_antigua", "etiqueta": "v1 (pre-refinamiento)"},
            {"texto": "intermedia", "etiqueta": "v2"},  # no pre-refinamiento
            {"texto": "reciente", "etiqueta": "v3 (pre-refinamiento)"},
        ]
        h._mostrar_diff_refinamiento("viejo", "nuevo")
        on_undo = h._abrir_ventana_diff.call_args.kwargs["on_undo"]
        on_undo()
        h.actualizar_salida.assert_called_with("reciente")  # la más reciente


# ───────────────────────────── cmd_refinar ─────────────────────────────────


class TestCmdRefinar:

    def _setup(self, *, txt="POSITIVE PROMPT: a cat", modo="imagen",
               is_natural=False, specs=None, anclaje="",
               idea="", pers="", lora="", monkeypatch_thread=None):
        worker_mock = MagicMock()
        h = _host(
            txt_salida=_txt(txt),
            txt_idea=_txt(idea),
            modo_var=_var(modo),
            personaje_activo=lambda: pers,
            lora_activo=lambda: lora,
            is_natural_mode=lambda: is_natural,
            get_current_model_specs=lambda: specs,
            _ultimo_anclaje_visual=anclaje,
            _worker_ia=worker_mock,
            # cmd_refinar usa self.workers.worker_ia tras migración A1
            workers=SimpleNamespace(worker_ia=worker_mock),
        )
        if monkeypatch_thread is not None:
            monkeypatch_thread.setattr(
                "modules.refinamiento.threading.Thread",
                lambda **kw: SimpleNamespace(
                    start=lambda: (kw.get("target") or (lambda *a, **kw: None))
                    (*kw.get("args", ()), **kw.get("kwargs", {})),
                    _kw=kw,
                ),
            )
        return h

    def test_sin_texto_devuelve_warning(self, monkeypatch):
        h = self._setup(txt="", monkeypatch_thread=monkeypatch)
        h.cmd_refinar()
        h.set_estado.assert_called_once()
        assert "Genera un prompt primero" in h.set_estado.call_args[0][0]
        h._worker_ia.assert_not_called()

    def test_texto_sin_marcadores_devuelve_warning(self, monkeypatch):
        h = self._setup(txt="solo texto plano sin keys", monkeypatch_thread=monkeypatch)
        h.cmd_refinar()
        assert "Genera un prompt primero" in h.set_estado.call_args[0][0]

    def test_imagen_tag_based_incluye_reglas_tag(self, monkeypatch):
        h = self._setup(txt="POSITIVE PROMPT: x", is_natural=False,
                        monkeypatch_thread=monkeypatch)
        h.cmd_refinar()
        h._worker_ia.assert_called_once()
        peticion = h._worker_ia.call_args[0][0]
        assert "Tags separados por comas" in peticion
        assert "tag:1.2" in peticion

    def test_imagen_natural_incluye_texto_natural(self, monkeypatch):
        h = self._setup(txt="PROMPT: x", is_natural=True,
                        monkeypatch_thread=monkeypatch)
        h.cmd_refinar()
        peticion = h._worker_ia.call_args[0][0]
        assert "NATURAL" in peticion
        assert "prosa descriptiva" in peticion

    def test_video_menciona_cinematografico(self, monkeypatch):
        h = self._setup(txt="PROMPT: x", modo="video",
                        monkeypatch_thread=monkeypatch)
        h.cmd_refinar()
        peticion = h._worker_ia.call_args[0][0]
        assert "cinematográfico" in peticion or "vídeo" in peticion.lower()

    def test_audio_menciona_instrumentacion(self, monkeypatch):
        h = self._setup(txt="PROMPT: x", modo="audio",
                        monkeypatch_thread=monkeypatch)
        h.cmd_refinar()
        peticion = h._worker_ia.call_args[0][0]
        assert "instrumentación" in peticion or "género" in peticion

    def test_incluye_idea_si_presente(self, monkeypatch):
        h = self._setup(txt="PROMPT: x", idea="mi nueva idea genial",
                        monkeypatch_thread=monkeypatch)
        h.cmd_refinar()
        peticion = h._worker_ia.call_args[0][0]
        assert "mi nueva idea genial" in peticion
        assert "Incorpora:" in peticion

    def test_incluye_personaje_si_presente(self, monkeypatch):
        h = self._setup(txt="PROMPT: x", pers="Alicia",
                        monkeypatch_thread=monkeypatch)
        h.cmd_refinar()
        peticion = h._worker_ia.call_args[0][0]
        assert "Alicia" in peticion
        assert "personaje" in peticion.lower()

    def test_incluye_lora_si_presente(self, monkeypatch):
        h = self._setup(txt="PROMPT: x", lora="AnimeStyle",
                        monkeypatch_thread=monkeypatch)
        h.cmd_refinar()
        peticion = h._worker_ia.call_args[0][0]
        assert "AnimeStyle" in peticion

    def test_incluye_anclaje_visual_si_presente(self, monkeypatch):
        h = self._setup(txt="PROMPT: x", anclaje="ojos verdes, pelo plateado",
                        monkeypatch_thread=monkeypatch)
        h.cmd_refinar()
        peticion = h._worker_ia.call_args[0][0]
        assert "ojos verdes, pelo plateado" in peticion
        assert "GEOMETRÍA VISUAL" in peticion

    def test_limite_chars_desde_specs(self, monkeypatch):
        h = self._setup(txt="PROMPT: x",
                        specs={"max_chars": 1500},
                        monkeypatch_thread=monkeypatch)
        h.cmd_refinar()
        peticion = h._worker_ia.call_args[0][0]
        assert "1500" in peticion
        assert "LÍMITE" in peticion or "límite" in peticion.lower()

    def test_limite_chars_fallback_2000_si_no_hay_specs(self, monkeypatch):
        h = self._setup(txt="PROMPT: x", specs=None,
                        monkeypatch_thread=monkeypatch)
        h.cmd_refinar()
        peticion = h._worker_ia.call_args[0][0]
        assert "2000" in peticion

    def test_pasa_es_refinamiento_y_texto_previo_al_worker(self, monkeypatch):
        h = self._setup(txt="POSITIVE PROMPT: x",
                        monkeypatch_thread=monkeypatch)
        h.cmd_refinar()
        kwargs = h._worker_ia.call_args.kwargs
        assert kwargs["es_refinamiento"] is True
        assert kwargs["texto_previo"] == "POSITIVE PROMPT: x"


# ──────────────────────────── _iterar_elemento ─────────────────────────────


class TestIterarElemento:
    """Solo testeamos el parsing de VARIANTE N en la respuesta del LLM."""

    def _setup(self, monkeypatch, *, resp="", n=5, txt_actual="prompt base"):
        # Suplantamos threading.Thread para ejecutar el worker sincronamente
        monkeypatch.setattr(
            "modules.refinamiento.threading.Thread",
            lambda **kw: SimpleNamespace(
                start=lambda: kw["target"](*kw.get("args", ()),
                                            **kw.get("kwargs", {})),
            ),
        )
        deepseek = SimpleNamespace(generar=lambda *a, **k: resp)
        h = _host(
            txt_salida=_txt(txt_actual),
            deepseek=deepseek,
            # _iterar_elemento usa _extraer_neg_de_bloque del CoreMixin para
            # decidir si pedir formato POSITIVE/NEGATIVE al LLM
            _extraer_neg_de_bloque=lambda bloque: None,
        )
        return h

    def test_parsea_n_variantes_validas(self, monkeypatch):
        resp = (
            "VARIANTE 1: una variante con iluminación suave y dorada, ambiente cálido\n"
            "VARIANTE 2: otra variante con iluminación dura y azul, ambiente frío\n"
            "VARIANTE 3: tercera variante con iluminación lateral y verde, mood neutro"
        )
        h = self._setup(monkeypatch, resp=resp, n=3)
        h._iterar_elemento("iluminación", n=3)
        h._abrir_comparador.assert_called_once()
        variantes = h._abrir_comparador.call_args[0][0]
        assert len(variantes) == 3
        assert "iluminación suave" in variantes[0]

    def test_filtra_strings_muy_cortos(self, monkeypatch):
        resp = (
            "VARIANTE 1: x\n"  # demasiado corto, se filtra
            "VARIANTE 2: descripción suficientemente larga con detalles ricos\n"
            "VARIANTE 3: otra descripción suficientemente larga con muchos detalles"
        )
        h = self._setup(monkeypatch, resp=resp, n=3)
        h._iterar_elemento("iluminación", n=3)
        variantes = h._abrir_comparador.call_args[0][0]
        assert len(variantes) == 2  # la corta se filtró

    def test_menos_de_2_variantes_valida_avisa_y_no_abre_comparador(self, monkeypatch):
        resp = "VARIANTE 1: solo una variante larga suficiente"
        h = self._setup(monkeypatch, resp=resp, n=3)
        h._iterar_elemento("iluminación", n=3)
        h._abrir_comparador.assert_not_called()
        msg = h.set_estado.call_args_list[-1][0][0]
        assert "Solo se generó" in msg or "intenta de nuevo" in msg

    def test_respeta_n_aunque_haya_mas_variantes(self, monkeypatch):
        resp = "\n".join(
            f"VARIANTE {i+1}: descripción larga número {i+1} suficiente"
            for i in range(7)
        )
        h = self._setup(monkeypatch, resp=resp, n=3)
        h._iterar_elemento("iluminación", n=3)
        variantes = h._abrir_comparador.call_args[0][0]
        assert len(variantes) == 3

    def test_parsing_es_case_insensitive(self, monkeypatch):
        resp = (
            "variante 1: descripción uno suficientemente larga\n"
            "Variante 2: descripción dos suficientemente larga\n"
            "VARIANTE 3: descripción tres suficientemente larga"
        )
        h = self._setup(monkeypatch, resp=resp, n=3)
        h._iterar_elemento("iluminación", n=3)
        variantes = h._abrir_comparador.call_args[0][0]
        assert len(variantes) == 3


# ─────────────────────── _menu_refinar_especifico ──────────────────────────


class TestMenuRefinarEspecifico:

    def test_sin_texto_devuelve_warning(self):
        h = _host(txt_salida=_txt(""))
        h._menu_refinar_especifico()
        h.set_estado.assert_called_once()
        assert "Genera un prompt primero" in h.set_estado.call_args[0][0]

    def test_texto_corto_devuelve_warning(self):
        h = _host(txt_salida=_txt("corto"))  # menos de 20 chars
        h._menu_refinar_especifico()
        assert "Genera un prompt primero" in h.set_estado.call_args[0][0]
