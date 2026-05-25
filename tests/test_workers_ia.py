"""Tests para WorkersIaMixin (modules/workers_ia.py).

Cobertura de los 5 workers que se ejecutan en threads. Mockeamos:
  • self.after(0, fn) → fn() inmediato (sin event loop tk)
  • self.deepseek.generar → respuesta fija
  • self.vision.describir → tupla (desc, motor) fija
  • todos los métodos de UI (set_estado, actualizar_salida, etc.)
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from modules.workers_ia import WorkersIaMixin


def _var(value):
    return SimpleNamespace(get=lambda: value)


def _txt(value):
    return SimpleNamespace(
        get=lambda *_a, **_k: value + "\n",
        delete=MagicMock(),
        insert=MagicMock(),
        focus_set=MagicMock(),
    )


def _host(*, deepseek_resp="POSITIVE PROMPT: nice\nNEGATIVE PROMPT: bad",
          specs=None, modo="imagen", llm="DeepSeek",
          es_comfyui_turbo=False, is_natural=False,
          **overrides):
    """Construye un host con WorkersIaMixin + dependencias mockeadas."""
    cls = type("Host", (WorkersIaMixin,), {})
    h = cls()

    defaults = dict(
        # Datos
        modo_var=_var(modo),
        llm_var=_var(llm),
        ratio_var=_var("16:9"),
        switch_traduccion_var=_var(False),
        # Texto
        txt_idea=_txt(""),
        txt_salida=_txt(""),
        imagen_cargada="fake_image.png",
        _ultimo_anclaje_visual="",
        # Workers/Services
        deepseek=SimpleNamespace(
            generar=lambda *a, **k: deepseek_resp,
            traducir=lambda t: t + " [traducido]",
        ),
        vision=SimpleNamespace(
            describir=lambda *a, **k: ("una descripción visual", "GPT-4V"),
        ),
        # Specs y helpers
        get_current_model_specs=lambda: specs,
        _es_comfyui_turbo=lambda: es_comfyui_turbo,
        is_natural_mode=lambda: is_natural,
        detectar_idioma=lambda t: True,
        # Recorte / parseo
        _recortar_si_excede=lambda txt, max_c: txt[:max_c] if max_c and len(txt) > max_c else txt,
        _parsear_variaciones=lambda txt, n_esperado=None: ["v1", "v2", "v3"],
        # Construcción de petición
        _construir_peticion=lambda idea, letra: f"P[{letra}]:{idea}",
        construir_modelo_info=lambda: " Modelo: TestModel.",
        # Componente prompts (PromptsComponent) — delega al host
        prompts=SimpleNamespace(
            construir_modelo_info=lambda: " Modelo: TestModel.",
            inyectar_specs_modelo=lambda sp: sp,
            inyectar_specs_audio=lambda sp: sp,
            inyectar_destino=lambda sp: sp,
        ),
        estilos_texto=lambda: "cinematic, dramatic",
        # UI methods
        after=lambda _delay, fn=None: fn() if callable(fn) else None,
        set_estado=MagicMock(),
        actualizar_salida=MagicMock(),
        guardar_en_historial=MagicMock(),
        toggle_botones=MagicMock(),
        _sonar_completado=MagicMock(),
        _iniciar_progreso=MagicMock(),
        _detener_progreso=MagicMock(),
        _mostrar_ideas=MagicMock(),
        _mostrar_variaciones=MagicMock(),
        _mostrar_diff_refinamiento=MagicMock(),
        _on_modo_cambio=MagicMock(),
        _ocultar_ideas=MagicMock(),
    )
    defaults.update(overrides)
    for k, v in defaults.items():
        setattr(h, k, v)
    return h


# ──────────────────────────── _worker_ia ────────────────────────────────────


class TestWorkerIa:

    def test_caso_basico_actualiza_salida_y_historial(self):
        h = _host()
        h._worker_ia("petición")
        h.guardar_en_historial.assert_called_once()
        h.actualizar_salida.assert_called_once()
        h.toggle_botones.assert_called_with(True)
        h._detener_progreso.assert_called_once()

    def test_recorte_si_excede_max_chars(self):
        h = _host(
            deepseek_resp="X" * 3000,
            specs={"max_chars": 500},
        )
        h._worker_ia("petición")
        # El texto pasado a actualizar_salida debe estar recortado a 500
        texto = h.actualizar_salida.call_args[0][0]
        assert len(texto) <= 500
        # Y se avisa al usuario
        assert any("recortado" in str(c.args[0]).lower()
                   for c in h.set_estado.call_args_list)

    def test_no_recorta_si_no_excede(self):
        h = _host(deepseek_resp="corto", specs={"max_chars": 500})
        h._worker_ia("petición")
        texto = h.actualizar_salida.call_args[0][0]
        assert texto == "corto"

    def test_quita_negative_si_modelo_no_lo_soporta(self):
        h = _host(
            deepseek_resp="POSITIVE PROMPT: cat\nNEGATIVE PROMPT: dog",
            specs={"max_chars": 5000, "has_negative": False},
        )
        h._worker_ia("petición")
        texto = h.actualizar_salida.call_args[0][0]
        assert "NEGATIVE" not in texto.upper()
        assert "cat" in texto

    def test_mantiene_negative_si_modelo_lo_soporta(self):
        h = _host(
            deepseek_resp="POSITIVE PROMPT: cat\nNEGATIVE PROMPT: dog",
            specs={"max_chars": 5000, "has_negative": True},
        )
        h._worker_ia("petición")
        texto = h.actualizar_salida.call_args[0][0]
        assert "NEGATIVE" in texto

    def test_quita_negative_en_comfyui_turbo(self):
        h = _host(
            deepseek_resp="POSITIVE PROMPT: cat\nNEGATIVE PROMPT: dog",
            specs={"max_chars": 5000, "has_negative": True},
            es_comfyui_turbo=True,
        )
        h._worker_ia("petición")
        texto = h.actualizar_salida.call_args[0][0]
        assert "NEGATIVE" not in texto.upper()

    def test_quita_pesos_numericos_en_comfyui_turbo(self):
        h = _host(
            deepseek_resp="(cat:1.3), (sharp focus:1.2), masterpiece",
            specs={"max_chars": 5000, "has_negative": True},
            es_comfyui_turbo=True,
        )
        h._worker_ia("petición")
        texto = h.actualizar_salida.call_args[0][0]
        # Sin paréntesis con pesos
        assert ":1.3" not in texto
        assert ":1.2" not in texto
        assert "cat" in texto
        assert "sharp focus" in texto

    def test_modo_refinamiento_abre_diff_modal(self):
        h = _host()
        h._worker_ia("p", es_refinamiento=True, texto_previo="viejo prompt")
        h._mostrar_diff_refinamiento.assert_called_once()
        args = h._mostrar_diff_refinamiento.call_args[0]
        assert args[0] == "viejo prompt"
        # actualizar_salida NO debe llamarse en modo refinamiento
        h.actualizar_salida.assert_not_called()

    def test_modo_ideas_invoca_mostrar_ideas(self):
        h = _host(deepseek_resp="1. idea uno\n2. idea dos\n3. idea tres")
        h._worker_ia("p", es_ideas=True)
        h._mostrar_ideas.assert_called_once()
        ideas = h._mostrar_ideas.call_args[0][0]
        assert len(ideas) >= 1

    def test_modo_variaciones_invoca_mostrar_variaciones(self):
        h = _host(deepseek_resp="resp con varias variaciones")
        h._worker_ia("p", es_variaciones=True, n_variaciones=3)
        h._mostrar_variaciones.assert_called_once()
        h.actualizar_salida.assert_not_called()

    def test_excepcion_de_red_muestra_mensaje_error(self):
        h = _host()
        h.deepseek = SimpleNamespace(
            generar=MagicMock(side_effect=Exception("network")),
        )
        h._worker_ia("p")
        # Debe mostrar el mensaje de error
        h.actualizar_salida.assert_called_once()
        texto = h.actualizar_salida.call_args[0][0]
        assert "Error" in texto
        assert "network" in texto

    def test_max_tokens_grande_si_specs_max_chars_grande(self, monkeypatch):
        capturado = {}
        h = _host(specs={"max_chars": 5000, "has_negative": True})
        h.deepseek.generar = lambda *a, **k: (
            capturado.update(k) or "POSITIVE PROMPT: x"
        )
        h._worker_ia("p")
        assert capturado["max_tokens"] == 2500

    def test_max_tokens_medio_si_specs_max_chars_2000(self):
        capturado = {}
        h = _host(specs={"max_chars": 2500, "has_negative": True})
        h.deepseek.generar = lambda *a, **k: (
            capturado.update(k) or "POSITIVE PROMPT: x"
        )
        h._worker_ia("p")
        assert capturado["max_tokens"] == 2000

    def test_max_tokens_pequeno_por_defecto(self):
        capturado = {}
        h = _host(specs=None)
        h.deepseek.generar = lambda *a, **k: (
            capturado.update(k) or "POSITIVE PROMPT: x"
        )
        h._worker_ia("p")
        assert capturado["max_tokens"] == 1800


# ─────────────────────────── _worker_vision ─────────────────────────────────


class TestWorkerVision:

    def test_pone_descripcion_en_idea_si_estaba_vacia(self):
        h = _host()
        h._worker_vision()
        h.txt_idea.delete.assert_called_with("1.0", "end")
        h.txt_idea.insert.assert_called_with("1.0", "una descripción visual")
        h.toggle_botones.assert_called_with(True)

    def test_concatena_con_idea_previa_si_existe(self):
        h = _host(txt_idea=_txt("mi idea previa"))
        h._worker_vision()
        idea_insertada = h.txt_idea.insert.call_args[0][1]
        assert "una descripción visual" in idea_insertada
        assert "mi idea previa" in idea_insertada

    def test_excepcion_muestra_error_y_rehabilita_botones(self):
        h = _host()
        h.vision = SimpleNamespace(describir=MagicMock(side_effect=Exception("boom")))
        h._worker_vision()
        msgs = [c.args[0] for c in h.set_estado.call_args_list]
        assert any("Error" in m for m in msgs)
        h.toggle_botones.assert_called_with(True)


# ────────────────────── _worker_prompt_traduccion ───────────────────────────


class TestWorkerPromptTraduccion:

    def test_sin_flag_traduccion_no_traduce(self):
        h = _host()
        h.switch_traduccion_var = _var(False)
        h.deepseek = SimpleNamespace(
            generar=MagicMock(return_value="POSITIVE PROMPT: ok"),
            traducir=MagicMock(),
        )
        h._worker_prompt_traduccion("hola mundo")
        h.deepseek.traducir.assert_not_called()

    def test_con_flag_traduccion_traduce_antes_de_generar(self):
        h = _host()
        h.switch_traduccion_var = _var(True)
        h.deepseek = SimpleNamespace(
            generar=MagicMock(return_value="POSITIVE PROMPT: ok"),
            traducir=MagicMock(return_value="hello world"),
        )
        h._worker_prompt_traduccion("hola mundo")
        h.deepseek.traducir.assert_called_once_with("hola mundo")
        # La petición a deepseek.generar usa la idea traducida
        peticion = h.deepseek.generar.call_args[0][0]
        assert "hello world" in peticion


# ────────────────────────── _worker_prompt_quick ────────────────────────────


class TestWorkerPromptQuick:

    def test_construye_peticion_quick_mode(self):
        capturado = {}
        h = _host()
        h.deepseek.generar = lambda p, **k: (
            capturado.update({"peticion": p, **k}) or "POSITIVE PROMPT: x"
        )
        h._worker_prompt_quick("idea quick")
        assert "QUICK MODE" in capturado["peticion"]
        assert "idea quick" in capturado["peticion"]

    def test_quick_usa_temperatura_baja(self):
        capturado = {}
        h = _host()
        h.deepseek.generar = lambda p, **k: (
            capturado.update(k) or "POSITIVE PROMPT: x"
        )
        h._worker_prompt_quick("idea")
        assert capturado["temperature"] == 0.4

    def test_quick_tag_based_menciona_tags_y_pesos(self):
        capturado = {}
        h = _host(is_natural=False)
        h.deepseek.generar = lambda p, **k: (
            capturado.update({"peticion": p}) or "POSITIVE PROMPT: x"
        )
        h._worker_prompt_quick("idea")
        assert "tags" in capturado["peticion"].lower()

    def test_quick_natural_menciona_lenguaje_natural(self):
        capturado = {}
        h = _host(is_natural=True)
        h.deepseek.generar = lambda p, **k: (
            capturado.update({"peticion": p}) or "POSITIVE PROMPT: x"
        )
        h._worker_prompt_quick("idea")
        assert "natural" in capturado["peticion"].lower()

    def test_quick_quita_negative_si_modelo_no_lo_soporta(self):
        h = _host(specs={"max_chars": 2000, "has_negative": False})
        h.deepseek.generar = lambda p, **k: "POSITIVE PROMPT: a\nNEGATIVE PROMPT: b"
        h._worker_prompt_quick("idea")
        texto = h.actualizar_salida.call_args[0][0]
        assert "NEGATIVE" not in texto.upper()

    def test_quick_actualiza_salida_y_estado(self):
        h = _host()
        h._worker_prompt_quick("idea")
        h.actualizar_salida.assert_called_once()
        h.toggle_botones.assert_called_with(True)
        # estado final: "Quick listo"
        msgs = [c.args[0] for c in h.set_estado.call_args_list]
        assert any("Quick" in m for m in msgs)


# ───────────────────── _worker_imagen_a_prompt ──────────────────────────────


class TestWorkerImagenAPrompt:

    def test_sin_prompt_existente_usa_modo_generar(self):
        capturado = {}
        h = _host(txt_salida=_txt(""))
        h.deepseek.generar = lambda p, **k: (
            capturado.update({"peticion": p}) or "POSITIVE PROMPT: anclado"
        )
        h._worker_imagen_a_prompt()
        assert "MODO B" in capturado["peticion"]
        assert "ANCLAJE VISUAL" in capturado["peticion"]

    def test_con_prompt_existente_usa_modo_mejorar(self):
        capturado = {}
        h = _host(txt_salida=_txt("POSITIVE PROMPT: prompt existente largo " * 5))
        h.deepseek.generar = lambda p, **k: (
            capturado.update({"peticion": p}) or "POSITIVE PROMPT: mejorado"
        )
        h._worker_imagen_a_prompt()
        assert "corrector visual" in capturado["peticion"].lower()
        assert "MEJORA" in capturado["peticion"] or "mejora" in capturado["peticion"].lower()

    def test_actualiza_anclaje_visual_con_descripcion(self):
        h = _host()
        h._worker_imagen_a_prompt()
        assert h._ultimo_anclaje_visual == "una descripción visual"

    def test_excepcion_muestra_error(self):
        h = _host()
        h.vision = SimpleNamespace(describir=MagicMock(side_effect=Exception("vision_err")))
        h._worker_imagen_a_prompt()
        msgs = [c.args[0] for c in h.set_estado.call_args_list]
        assert any("Error" in m for m in msgs)
