"""
G-Prompt Studio v1.0 — Punto de entrada
"""
import json
import logging
import os
import sys
import traceback

# En Windows, la consola usa cp1252 por defecto y revienta al loggear
# caracteres como → o emojis. Forzamos UTF-8 antes de crear handlers.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# ─── Logging ───────────────────────────────────────────────
# Todo (datos, keys, logs, backups) vive en ~/.arquitecto_prompts/
# Importamos LOGS_DIR de config para tener una sola fuente de verdad.
from logging.handlers import RotatingFileHandler

import customtkinter as ctk

from config import LOGS_DIR

LOG_DIR = str(LOGS_DIR)
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        # Rotación: 2 MB por archivo, 3 backups (~8 MB máx en disco).
        # Sin esto gprompt.log crecía sin límite entre sesiones.
        RotatingFileHandler(os.path.join(LOG_DIR, "gprompt.log"),
                            maxBytes=2_000_000, backupCount=3,
                            encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("gprompt.main")

# Red anti-bugs: si GPROMPT_DEBUG está puesto, re-lanza las excepciones
# que normalmente se tragarían (los `logger.debug("[silent] ...")`).
from logging_utils import install_strict_silent_guard

if install_strict_silent_guard():
    logger.warning(
        "MODO ESTRICTO activo (GPROMPT_DEBUG): las excepciones [silent] "
        "se re-lanzarán en lugar de silenciarse."
    )

from modules.tooltip import install_ctk_tooltip_patches

install_ctk_tooltip_patches(logger)

# ─── Validación y recuperación de preferencias ─────────────

def _ruta_preferencias() -> str:
    """Ruta REAL de preferencias.json (~/.arquitecto_prompts/).

    Antes se leía preferencias.json junto a main.py (ruta legacy que
    normalmente no existe), por lo que el tema guardado nunca se
    aplicaba en el arranque y la validación operaba sobre nada.
    """
    from config import ARCHIVOS
    return str(ARCHIVOS["preferencias"])


def _validate_and_fix_prefs() -> bool:
    """Valida preferencias.json y repara si está corrupto.
    Devuelve True si todo OK, False si necesita intervención."""
    prefs_path = _ruta_preferencias()

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

        # Migración de plataformas retiradas/renombradas (2026-07-04):
        # "ComfyUI / A1111 / Forge" → "ComfyUI / Fooocus"; "Dola" eliminada.
        # Recorre cualquier valor string bajo claves que contengan "plataforma"
        # (prefs de sesión + setups guardados).
        _migracion_plataformas = {
            "ComfyUI / A1111 / Forge": "ComfyUI / Fooocus",
            "Dola": "SeaArt / Tensor.Art",
        }

        def _migrar(nodo):
            cambiado = False
            if isinstance(nodo, dict):
                for k, v in nodo.items():
                    if (isinstance(v, str) and "plataforma" in str(k).lower()
                            and v in _migracion_plataformas):
                        nodo[k] = _migracion_plataformas[v]
                        cambiado = True
                    elif isinstance(v, (dict, list)):
                        cambiado = _migrar(v) or cambiado
            elif isinstance(nodo, list):
                for item in nodo:
                    cambiado = _migrar(item) or cambiado
            return cambiado

        if _migrar(prefs_data):
            logger.info("Preferencias: plataformas antiguas migradas (A1111/Forge → Fooocus, Dola retirada)")
            _atomic_write(prefs_path, prefs_data)

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
    prefs_path = _ruta_preferencias()

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
        # Icono de la app (ventana + barra de tareas). El mismo patrón de
        # ruta que theme.json: junto a main.py tanto en dev como en el .exe
        # (assets/ va en datas del spec). CTk marca iconbitmap como llamado
        # y ya no lo pisa con su icono por defecto.
        try:
            ruta_icono = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "assets", "icon.ico")
            if os.path.exists(ruta_icono):
                app.iconbitmap(ruta_icono)
        except Exception as e:
            logger.debug(f"[silent] icono no aplicado: {e}")
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
