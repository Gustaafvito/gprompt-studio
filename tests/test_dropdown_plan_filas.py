"""Las familias del final del desplegable eran inalcanzables.

08-sep-2026. Recién arreglado el escaneo de ComfyUI, el combo de imagen ya
listaba los modelos locales pero terminaba así:

    v1-5-pruned
    ▾ ── ComfyUI · SDXL (Fooocus) ──
    ▾ ── ComfyUI · Z-Image ──
    … y 17 más — escribe para afinar

Dos cabeceras con NADA debajo. El tope de filas (80) cortaba justo ahí: 97
modelos - 80 pintados = los 17 del resumen. La cabecera se pintaba al leerla
y solo después se descubría que todos sus modelos caían pasado el tope, así
que la familia parecía vacía en vez de recortada — y sus 15 modelos no había
forma de elegirlos salvo escribiendo a ciegas el nombre.

Medido en el equipo del usuario, pintar N filas (cada una un CTkButton):
80 -> 174 ms, 97 -> 208 ms, 130 -> 296 ms, 170 -> 501 ms. Subir el tope a 120
cubre su catálogo local entero por 90 ms más y sigue lejos del tramo que se
nota, así que el recorte deja de aparecer en su caso.
"""
from modules import searchable_dropdown as sd
from modules.searchable_dropdown import _MAX_FILAS, _plan_filas


def _cabeceras(plan):
    return [v for k, v, *_ in ((f[0], f[1], *f[2:]) for f in plan) if k == "cab"]


def _modelos(plan):
    return [f[1] for f in plan if f[0] == "mod"]


class TestNingunaCabeceraSeQuedaSinModelos:

    def test_la_cabecera_recortada_no_se_pinta(self):
        valores = ["── A ──", "a1", "a2", "── B ──", "b1"]
        plan, ocultas, hay = _plan_filas(valores, tope=2)
        assert _cabeceras(plan) == ["── A ──"], (
            "B no tiene ni un modelo pintado: su cabecera es un hueco")
        assert _modelos(plan) == ["a1", "a2"]
        assert ocultas == 1 and hay is True

    def test_la_cabecera_entra_si_cabe_uno_solo_de_los_suyos(self):
        plan, ocultas, _ = _plan_filas(
            ["── A ──", "a1", "── B ──", "b1", "b2"], tope=2)
        assert _cabeceras(plan) == ["── A ──", "── B ──"]
        assert _modelos(plan) == ["a1", "b1"]
        assert ocultas == 1

    def test_una_familia_vacia_del_todo_tampoco_se_pinta(self):
        plan, _, _ = _plan_filas(["── A ──", "── B ──", "b1"])
        assert _cabeceras(plan) == ["── B ──"]

    def test_la_ultima_cabecera_no_se_queda_pendiente(self):
        # Si el bucle termina con una cabecera esperando su primer modelo, no
        # debe colarse al final del plan.
        plan, _, _ = _plan_filas(["── A ──", "a1", "── B ──"])
        assert _cabeceras(plan) == ["── A ──"]


class TestFamiliasPlegadas:

    def test_una_familia_plegada_conserva_su_cabecera(self):
        # Sin cabecera no habria forma de volver a desplegarla.
        plan, _, _ = _plan_filas(["── A ──", "a1", "a2"], colapsadas={"── A ──"})
        assert plan == [("cab", "── A ──", True)]

    def test_plegada_no_consume_tope(self):
        plan, ocultas, _ = _plan_filas(
            ["── A ──", "a1", "a2", "── B ──", "b1", "b2"],
            colapsadas={"── A ──"}, tope=2)
        assert _modelos(plan) == ["b1", "b2"]
        assert ocultas == 0, "los modelos plegados no se cuentan como recortados"


class TestAlBuscarNoHayCabeceras:

    def test_los_resultados_salen_planos(self):
        plan, _, hay = _plan_filas(
            ["── A ──", "juggernautXL_v9", "── B ──", "flux1-dev"], filtro="flux")
        assert _cabeceras(plan) == []
        assert _modelos(plan) == ["flux1-dev"] and hay is True

    def test_sin_coincidencias(self):
        plan, ocultas, hay = _plan_filas(["── A ──", "a1"], filtro="zzz")
        assert plan == [] and ocultas == 0 and hay is False

    def test_el_filtro_no_distingue_mayusculas(self):
        _, _, hay = _plan_filas(["── A ──", "JuggernautXL_v9"], filtro="juggernaut")
        assert hay is True


class TestElTopeCubreElCatalogoLocal:

    def test_caben_las_109_entradas_de_comfyui(self):
        # 97 modelos + 12 cabeceras en el equipo del usuario. Con el tope a 80
        # se perdian las dos ultimas familias enteras.
        assert _MAX_FILAS >= 97, (
            f"con tope {_MAX_FILAS} vuelven a quedar familias inalcanzables")

    def test_no_se_sube_hasta_donde_se_nota(self):
        # 170 filas = ~500 ms por apertura Y por tecla: el "tarda en activarse".
        assert _MAX_FILAS < 170

    def test_el_plan_no_pasa_del_tope(self):
        valores = [x for i in range(20)
                   for x in (f"── F{i} ──", *[f"m{i}_{j}" for j in range(10)])]
        plan, ocultas, _ = _plan_filas(valores)
        assert len(_modelos(plan)) == _MAX_FILAS
        assert len(_modelos(plan)) + ocultas == 200

    def test_el_repintado_usa_el_plan(self):
        # Candado de integracion: si alguien vuelve a decidir que se pinta
        # dentro del bucle de widgets, este test avisa.
        import inspect
        fuente = inspect.getsource(sd.attach_searchable_dropdown)
        assert "_plan_filas(" in fuente, (
            "el pintado debe consumir el plan, no recalcularlo entre widgets")
