"""Un modelo renombrado no puede dejar tirado a quien lo tenía elegido.

11-sep-2026. DeepSeek publicó V4.1 Flash y de paso le quitó la versión al ID:
`deepseek-v4-flash` dejó de existir y pasó a llamarse `deepseek-flash`. El
catálogo de la app seguía pidiendo el nombre viejo, y encima era su
`model_default`.

Lo que hace daño de verdad no es el desplegable —`modelos_disponibles()`
filtra contra el catálogo vivo y el muerto simplemente desaparece— sino
`active_models.json`: a quien tuviera Flash elegido se le queda el ID muerto
guardado en disco, y ahí no hay filtro que valga. Genera, y falla.

Para eso está `_MIGRAR_MODELO`. Y su trampa es sutil: **el destino de una
migración también se pudre**. Las dos entradas legacy de julio apuntaban a
`deepseek-v4-flash`, así que al morir ese ID quedaron migrando de un modelo
muerto a otro modelo muerto — un arreglo que había dejado de arreglar y que
nadie habría notado hasta que un usuario de hace meses abriera la app.

Estos candados atan las dos puntas: que ningún ID retirado se quede fuera del
mapa, y que todo destino del mapa siga estando en el catálogo curado.
"""
import pytest

from api_clients import LLM_PROVIDERS, APIClients

MIGRAR = APIClients._MIGRAR_MODELO


def _curados():
    """Todos los IDs que el catálogo ofrece hoy, de cualquier proveedor."""
    return {m for p in LLM_PROVIDERS.values() for m in (p.get("modelos") or [])}


class TestElDestinoDeCadaMigracionSigueVivo:

    @pytest.mark.parametrize("viejo,nuevo", sorted(MIGRAR.items()))
    def test_apunta_a_un_modelo_del_catalogo(self, viejo, nuevo):
        assert nuevo in _curados(), (
            f"«{viejo}» migra a «{nuevo}», que ya no está en ningún catálogo. "
            f"Migrar de un ID muerto a otro ID muerto no arregla nada: "
            f"apúntalo al reemplazo vigente")

    @pytest.mark.parametrize("viejo,nuevo", sorted(MIGRAR.items()))
    def test_no_migra_a_si_mismo(self, viejo, nuevo):
        assert viejo != nuevo, f"«{viejo}» migra a sí mismo"

    def test_ningun_origen_sigue_ofreciendose(self):
        # Si un ID está en el mapa es porque murió; ofrecerlo otra vez en el
        # desplegable sería mandar al usuario justo a lo que se migra.
        for viejo in MIGRAR:
            assert viejo not in _curados(), (
                f"«{viejo}» se migra por muerto pero el catálogo lo sigue "
                f"ofreciendo")


class TestElRenombradoDeDeepSeek:
    """El caso que destapó todo esto."""

    def test_el_id_viejo_de_flash_se_migra(self):
        assert MIGRAR.get("deepseek-v4-flash") == "deepseek-flash", (
            "sin esta entrada, quien tuviera Flash elegido antes del "
            "11-sep-2026 arrastra un ID muerto en active_models.json")

    def test_las_entradas_legacy_no_apuntan_al_id_retirado(self):
        # Apuntaban a deepseek-v4-flash, que murió con el renombrado.
        for viejo in ("deepseek-chat", "deepseek-reasoner"):
            assert MIGRAR[viejo] != "deepseek-v4-flash"

    def test_el_catalogo_ya_no_ofrece_el_id_viejo(self):
        assert "deepseek-v4-flash" not in LLM_PROVIDERS["deepseek"]["modelos"]


class TestCadaProveedorOfreceSuPropioPorDefecto:
    """Un `model_default` fuera de su lista deja el desplegable incoherente."""

    @pytest.mark.parametrize("pid", sorted(LLM_PROVIDERS))
    def test_el_default_esta_en_la_lista(self, pid):
        info = LLM_PROVIDERS[pid]
        modelos = info.get("modelos") or []
        if not modelos:
            pytest.skip(f"{pid} no trae lista curada")
        assert info.get("model_default") in modelos, (
            f"{pid}: el modelo por defecto no está entre los que ofrece")
