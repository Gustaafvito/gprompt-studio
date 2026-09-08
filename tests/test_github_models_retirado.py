"""GitHub Models cerró el 30-jul-2026: fuera de la app.

08-sep-2026. El usuario creó un token fine-grained con permiso `Models:
Read-only`, lo guardó, y la API respondió a todo:

    HTTP 410  {"error": {"code": "github_models_retirement_brownout",
               "message": "GitHub Models is temporarily unavailable as part
               of a scheduled retirement brownout."}}

No era un problema del token. GitHub anunció el cierre el 01-jul-2026: dejó
de admitir clientes nuevos el 16-jun, hubo brownouts el 16 y el 23-jul y la
retirada total fue el **30-jul-2026** — mes y medio antes de esta prueba. El
`base_url` que tenía la app (`models.inference.ai.azure.com`) ni siquiera
resuelve ya.

Se QUITA en vez de dejarlo fallando porque era la opción estrella y gratuita
del asistente de bienvenida ("🏆 GitHub Models", "GRATIS"): quien instalara
la app lo elegiría el primero y se comería un 410 sin entender nada. Las
gratuitas que sí funcionan y ya están dadas de alta son Groq y Gemini.
"""
import inspect

import api_clients as A
from modules import bienvenida


class TestNoQuedaRastroDelProveedor:

    def test_no_esta_en_los_proveedores(self):
        assert "github_models" not in A.LLM_PROVIDERS, (
            "el servicio cerró el 30-jul-2026: ofrecerlo es prometer un 410")

    def test_no_esta_en_la_tabla_de_precios(self):
        assert "github_models" not in A.PRECIOS_USD_1M

    def test_no_esta_en_las_variables_de_entorno(self):
        assert "github_models" not in A.ENV_VAR_POR_PROVIDER

    def test_no_esta_en_la_bienvenida(self):
        ids = [p for p, _ in bienvenida.PROVEEDORES_GRATIS]
        assert "github_models" not in ids

    def test_el_endpoint_muerto_no_aparece_en_ningun_sitio(self):
        # models.inference.ai.azure.com ya no resuelve. Si reaparece es que
        # alguien ha revivido el proveedor a medias.
        import app
        for modulo in (A, app):
            fuente = inspect.getsource(modulo)
            for linea in fuente.splitlines():
                if "models.inference.ai.azure.com" in linea:
                    assert linea.lstrip().startswith("#"), (
                        f"endpoint muerto en código vivo: {linea.strip()}")


class TestQuedanAlternativasGratuitas:

    def test_el_wizard_sigue_ofreciendo_algo_gratis(self):
        # Si se quedara solo con proveedores de pago, la primera experiencia
        # de quien instale la app sería sacar la tarjeta.
        gratis = [p for p, i in A.LLM_PROVIDERS.items() if not i.get("is_paid")]
        assert gratis, "tiene que quedar al menos un proveedor gratuito"

    def test_groq_y_gemini_siguen(self):
        for pid in ("groq", "gemini"):
            assert pid in A.LLM_PROVIDERS
