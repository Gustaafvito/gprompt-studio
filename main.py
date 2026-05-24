"""
G-Prompt Studio v1.0 — Punto de entrada
"""
import json
import logging
import os
import sys
import traceback

import customtkinter as ctk

# ─── Logging ───────────────────────────────────────────────
# Todo (datos, keys, logs, backups) vive en ~/.arquitecto_prompts/
# Importamos LOGS_DIR de config para tener una sola fuente de verdad.
from config import LOGS_DIR

LOG_DIR = str(LOGS_DIR)
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "gprompt.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("gprompt.main")

from modules.tooltip import install_ctk_tooltip_patches

install_ctk_tooltip_patches(logger)

# ─── Validación y recuperación de preferencias ─────────────

def _validate_and_fix_prefs() -> bool:
    """Valida preferencias.json y repara si está corrupto.
    Devuelve True si todo OK, False si necesita intervención."""
    base = os.path.dirname(os.path.abspath(__file__))
    prefs_path = os.path.join(base, "preferencias.json")

    if not os.path.exists(prefs_path):
        return True

    try:
        with open(prefs_path, "r", encoding="utf-8") as f:
            prefs_data = json.load(f)

        if not isinstance(prefs_data, dict):
            logger.warning("preferencias.json no es un dict, recreando")
            _backup_and_reset(prefs_path)
            return True

        temas_validos = {"dark", "light", "system"}
        tema_actual = prefs_data.get("tema", "dark")
        if tema_actual not in temas_validos:
            logger.warning(f"Tema '{tema_actual}' no soportado, reseteando a 'dark'")
            prefs_data["tema"] = "dark"
            _atomic_write(prefs_path, prefs_data)
            return True

        return True

    except json.JSONDecodeError as e:
        logger.error(f"preferencias.json corrupto: {e}")
        _backup_and_reset(prefs_path)
        return True
    except Exception as e:
        logger.error(f"Error validando preferencias: {e}")
        return False


def _backup_and_reset(prefs_path: str):
    """Crea backup del archivo corrupto y genera uno nuevo."""
    try:
        backup = prefs_path + ".bak"
        if os.path.exists(prefs_path):
            import shutil
            shutil.copy2(prefs_path, backup)
            logger.info(f"Backup creado: {backup}")
    except Exception as e:
        logger.error(f"No se pudo crear backup: {e}")

    try:
        _atomic_write(prefs_path, {"tema": "dark"})
        logger.info("preferencias.json recreado con valores por defecto")
    except Exception as e:
        logger.error(f"No se pudo recrear preferencias.json: {e}")


def _atomic_write(path: str, data: dict):
    """Escritura atómica con temp + rename."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


# ─── Tema ──────────────────────────────────────────────────

def _cargar_tema():
    """Aplica tema guardado y theme.json personalizado."""
    base = os.path.dirname(os.path.abspath(__file__))
    prefs_path = os.path.join(base, "preferencias.json")

    tema_guardado = "dark"
    if os.path.exists(prefs_path):
        try:
            with open(prefs_path, "r", encoding="utf-8") as f:
                tema_guardado = json.load(f).get("tema", "dark")
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
    ctk.set_appearance_mode(tema_guardado)
    logger.info(f"Tema aplicado: {tema_guardado}")

    ruta_tema = os.path.join(base, "theme.json")
    if os.path.exists(ruta_tema):
        try:
            ctk.set_default_color_theme(ruta_tema)
            logger.info(f"Tema personalizado cargado: {ruta_tema}")
        except Exception as e:
            logger.warning(f"Error al cargar theme.json: {e}, usando tema por defecto")
            ctk.set_default_color_theme("blue")
    else:
        ctk.set_default_color_theme("blue")


# ─── Arranque ──────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("Iniciando G-Prompt Studio v1.0")
    logger.info("=" * 60)

    _validate_and_fix_prefs()
    _cargar_tema()

    try:
        from app import ArquitectoApp
        # Sin splash de root temporal: destruirlo antes de crear la app
        # real disparaba after() pendientes contra widgets muertos
        # ("invalid command name"). La app arranca rápido y no lo necesita.
        app = ArquitectoApp()
        logger.info("App inicializada correctamente.")
        try:
            app.mainloop()
        except Exception as e:
            # Errores de cleanup durante el cierre — esperados, no son fatales.
            # Pasa cuando customtkinter intenta focus_get() o titlebar_color
            # sobre una ventana que ya fue destruida (race condition al cerrar,
            # típica si había dos instancias abiertas).
            msg = str(e).lower()
            cleanup_signatures = (
                "application has been destroyed",
                "can't invoke \"focus\"",
                "invalid command name",
                "bad window path",
            )
            if any(sig in msg for sig in cleanup_signatures):
                logger.info(f"App cerrada (cleanup esperado: {e})")
            else:
                raise

    except Exception as e:
        logger.critical(f"Error fatal al arrancar: {e}", exc_info=True)
        print(f"\n❌ Error fatal: {e}")
        print(f"Detalles:\n{traceback.format_exc()}")
        print(f"\nRevisa el log en: {os.path.join(LOG_DIR, 'gprompt.log')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
