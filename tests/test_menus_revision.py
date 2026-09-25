"""Fallos de los menús encontrados en la revisión del 25-sep-2026.

Cada uno salió de abrir las 50 opciones de los 8 menús con la app real y
mirar las capturas. Los que necesitan ventana están en test_barrido_ui.py.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

RAIZ = Path(__file__).resolve().parent.parent


class TestEstadisticas:
    """Estadísticas decía «SeaArt 316x (100%)» cuando era el 63 % de los
    prompts: el porcentaje se calculaba sobre el más usado."""

    def test_el_porcentaje_es_sobre_el_total(self):
        from modules.tools_analysis import pct_del_total
        assert pct_del_total(316, 500) == 63
        assert pct_del_total(106, 500) == 21

    def test_sin_total_no_divide_por_cero(self):
        from modules.tools_analysis import pct_del_total
        assert pct_del_total(5, 0) == 0

    def test_todas_las_barras_pasan_su_total(self):
        fuente = (RAIZ / "modules" / "tools_analysis.py").read_text(encoding="utf-8")
        llamadas = [ln for ln in fuente.splitlines() if "_barra(scroll," in ln]
        assert llamadas, "¿se renombró _barra?"
        for ln in llamadas:
            assert ln.count(",") >= 5, f"barra sin total: {ln.strip()}"


class TestAvisoDelHistorial:
    """El Dashboard avisaba «Historial casi lleno (500/100)»: la cifra era de
    cuando el límite era otro."""

    def test_usa_el_limite_real(self):
        from persistence import HISTORIAL_MAX
        dashboard = (RAIZ / "modules" / "dashboard.py").read_text(encoding="utf-8")
        assert "/100)" not in dashboard
        assert "HISTORIAL_MAX" in dashboard
        assert HISTORIAL_MAX == 500

    def test_el_historial_recorta_en_ese_limite(self, tmp_path, monkeypatch):
        import persistence
        monkeypatch.setattr(persistence.DataStore, "_guardar", lambda self, nombre: None)
        store = persistence.DataStore.__new__(persistence.DataStore)
        store.historial = [{"n": i} for i in range(persistence.HISTORIAL_MAX)]
        store.agregar_historial.__wrapped__(store, {"n": "nuevo"}) if hasattr(
            store.agregar_historial, "__wrapped__") else store.agregar_historial({"n": "nuevo"})
        assert len(store.historial) == persistence.HISTORIAL_MAX
        assert store.historial[0] == {"n": "nuevo"}


class TestAdaptarAlModelo:
    """«Adaptar al modelo activo» no decía nada durante los segundos que tarda
    la IA: parecía que el clic no hacía efecto."""

    def test_avisa_al_empezar(self):
        from modules.tools_workflow import ToolsWorkflowService
        estados = []
        app = SimpleNamespace(
            txt_salida=SimpleNamespace(get=lambda *a: "POSITIVE PROMPT: a lighthouse in a storm at dawn"),
            prompts=SimpleNamespace(inyectar_specs_modelo=lambda s: "MODELO: GPT Image 2 · max 5000 chars"),
            dialogs=SimpleNamespace(set_estado=lambda t, *a: estados.append(t)),
            _executor=SimpleNamespace(submit=lambda fn: MagicMock()))
        servicio = ToolsWorkflowService.__new__(ToolsWorkflowService)
        servicio.app = app
        servicio._cmd_adaptar_modelo()
        assert estados and estados[-1].startswith("⏳")


class TestCodigoMuerto:
    """Una «franja de compatibilidad» que nunca se rellenaba ocupaba ~30 px bajo
    el resultado, y abría una ventana que decía «Aquí iría la tabla»."""

    def test_no_vuelve(self):
        for f in (RAIZ / "modules").glob("*.py"):
            texto = f.read_text(encoding="utf-8")
            assert "lbl_compat_inline" not in texto, f.name
            assert "Aquí iría" not in texto, f.name
