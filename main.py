"""
G-Prompt Studio v1.0 — Punto de entrada
"""
import os
import sys
import json
import logging
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

# CTkToolTip 0.9 hace `StringVar().set(None)` en DOS sitios:
#   - __init__ línea 78  (cuando message=None al crear)
#   - configure() línea 253  (cuando se llama configure() sin message)
# Tkinter convierte None en la cadena literal "None" — apareciendo
# como tooltip al pasar el ratón. Parcheamos los dos métodos en
# main.py para que se aplique ANTES que cualquier import de la app.
try:
    from CTkToolTip.ctk_tooltip import CTkToolTip as _CTkToolTip_class

    # Parche 1: __init__
    # - Si message=None → "" (evita "None" literal)
    # - Si no se pasan colores → forzar par adaptativo al tema actual,
    #   con buen contraste tanto en dark como en light.
    _CTkToolTip_orig_init = _CTkToolTip_class.__init__
    def _CTkToolTip_safe_init(self, widget=None, message=None, **kwargs):
        if message is None:
            message = ""

        # Detectar tema actual al crear el tooltip (mismo enfoque que los
        # tooltips inferiores POS/NEG/Comfy que ya se ven bien).
        try:
            _is_lt = ctk.get_appearance_mode().lower() == "light"
        except Exception:
            _is_lt = False

        # Si no se especifica fg_color del label, usar par claro/oscuro
        # legible. fg_color en message_kwargs colorea el FONDO del label.
        if "fg_color" not in kwargs:
            kwargs["fg_color"] = "#f0f0f0" if _is_lt else "#1a1a2e"
        if "text_color" not in kwargs:
            kwargs["text_color"] = "#111827" if _is_lt else "#e5e7eb"
        if "bg_color" not in kwargs or kwargs.get("bg_color") is None:
            kwargs["bg_color"] = "#f0f0f0" if _is_lt else "#1a1a2e"
        if "padding" not in kwargs:
            kwargs["padding"] = (10, 4)
        if "corner_radius" not in kwargs:
            kwargs["corner_radius"] = 6
        if "border_width" not in kwargs:
            kwargs["border_width"] = 1
        if "border_color" not in kwargs or kwargs.get("border_color") is None:
            kwargs["border_color"] = "#cbd5e1" if _is_lt else "#3b82f6"

        _CTkToolTip_orig_init(self, widget=widget, message=message, **kwargs)
    _CTkToolTip_class.__init__ = _CTkToolTip_safe_init

    # Parche 2: configure() — sino al reconfigurar un tooltip se rompe
    _CTkToolTip_orig_configure = _CTkToolTip_class.configure
    def _CTkToolTip_safe_configure(self, message=None, **kwargs):
        if message is None:
            try: message = self.messageVar.get()
            except Exception: message = ""
            # Evitar el bucle "None" si ya estaba mal
            if message == "None":
                message = ""
        _CTkToolTip_orig_configure(self, message=message, **kwargs)
    _CTkToolTip_class.configure = _CTkToolTip_safe_configure

    logger.info("[v1.0.8] CTkToolTip patched OK (None → \"\", colores adaptativos al tema)")
except ImportError:
    logger.info("[v1.0.8] CTkToolTip no instalado, sin parche")
except Exception as _e_patch:
    logger.warning(f"[v1.0.8] CTkToolTip patch falló: {_e_patch}")

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
        except Exception:
            pass
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
        # NOTA v1.0.1: el splash inicial se eliminó porque al usar un root
        # temporal y luego destruirlo justo antes de crear la app real, los
        # after() pendientes intentaban ejecutarse contra widgets ya muertos
        # y la consola se llenaba de "invalid command name". La app arranca
        # rápido (<1 segundo en máquinas modernas), no necesita splash.
        app = ArquitectoApp()
        logger.info("App inicializada correctamente.")
        app.mainloop()

    except Exception as e:
        logger.critical(f"Error fatal al arrancar: {e}", exc_info=True)
        print(f"\n❌ Error fatal: {e}")
        print(f"Detalles:\n{traceback.format_exc()}")
        print(f"\nRevisa el log en: {os.path.join(LOG_DIR, 'gprompt.log')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
