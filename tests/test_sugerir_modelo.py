"""Guardián del fix sesión 34: "Sugerir modelo" debe ofrecer TODOS los modelos
del modo activo al LLM, no solo los 20 primeros de la lista (antes salían
siempre los mismos, sesgados al inicio alfabético).
"""
import config
from modules.tools_creative import ToolsCreativeService


class _SyncFuture:
    def add_done_callback(self, fn):
        pass


class _SyncExec:
    """Ejecutor síncrono: corre el worker en el acto."""
    def submit(self, fn, *a, **k):
        fn(*a, **k)
        return _SyncFuture()


class _FakeDeepseek:
    def __init__(self):
        self.peticion = None
        self.temperature = None

    def generar(self, peticion, temperature=None, max_tokens=None):
        self.peticion = peticion
        self.temperature = temperature
        # Respuesta que NO casa con ningún modelo → rama "sin sugerencias"
        # (evita abrir la ventana GUI en el test).
        return "#1: __no_existe__\nRAZÓN: n/a"


class _Txt:
    def __init__(self, txt):
        self._txt = txt

    def get(self, *a):
        return self._txt


class _Var:
    def __init__(self, v):
        self._v = v

    def get(self):
        return self._v


class _Dialogs:
    def set_estado(self, *a, **k):
        pass


class _FakeApp:
    def __init__(self, idea, modo="imagen"):
        self.txt_idea = _Txt(idea)
        self.modo_var = _Var(modo)
        self.dialogs = _Dialogs()
        self.deepseek = _FakeDeepseek()
        self._executor = _SyncExec()

    def _sesion_log(self, *a, **k):
        pass

    def after(self, _delay, fn=None, *a):
        # No ejecutar callbacks de UI en el test.
        return None


def test_sugerir_modelo_envia_todos_los_modelos_imagen():
    app = _FakeApp("una mujer cyberpunk con luces de neón, retrato fotorrealista")
    svc = ToolsCreativeService(app)
    svc._cmd_sugerir_modelo()

    peticion = app.deepseek.peticion
    assert peticion is not None, "No se llamó al LLM"

    modelos = [m for m in config.MODELOS_IMAGEN_FLAT if not m.startswith("─")]
    # TODOS los modelos visibles deben aparecer en el prompt, no solo 20.
    faltan = [m for m in modelos if m not in peticion]
    assert not faltan, f"Modelos ausentes del prompt (cap [:20] no eliminado): {faltan[:5]}"
    # Sanidad: hay bastantes más de 20.
    assert len(modelos) > 20


def test_sugerir_modelo_temperatura_con_variedad():
    app = _FakeApp("paisaje de montaña al amanecer, estilo acuarela")
    svc = ToolsCreativeService(app)
    svc._cmd_sugerir_modelo()
    # Subida de 0.3 → 0.5 para que no salga siempre lo mismo.
    assert app.deepseek.temperature == 0.5
