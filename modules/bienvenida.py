"""Bienvenida para usuarios nuevos: se abre cuando NO hay ningún "cerebro".

Sin una API key la aplicación no puede generar nada, pero antes nadie se lo
decía a quien entraba por primera vez: se encontraba con 126 modelos, 333
estilos y 14 proveedores y ninguna pista de por dónde empezar.

El disparador es "cero keys configuradas" y no "primer arranque" a propósito:
es lo que de verdad bloquea. Si alguien borra sus keys, o estrena el .exe en
otro equipo, vuelve a salir — que es justo cuando hace falta.

El tutorial completo (42 pasos) sigue estando, pero es demasiado para un
primer contacto: aquí solo se enseña a desbloquear la app y los 5 pasos del
flujo básico.
"""
import logging

import customtkinter as ctk

from modules import paleta as P
from modules.gprompt_window import GPromptWindow
from modules.i18n import tr
from modules.navegador import abrir_url

logger = logging.getLogger(__name__)

# Proveedores GRATIS (sin tarjeta) que desbloquean la app. El orden es el de
# "menos fricción primero": Gemini pide solo cuenta Google; Ollama no pide
# cuenta pero hay que instalarlo. Los datos (nombre, url) salen de
# api_clients.LLM_PROVIDERS: aquí solo se elige cuáles destacar y por qué.
PROVEEDORES_GRATIS = [
    ("gemini", tr("Gratis hasta 15 peticiones/min. La opción más rápida para empezar.")),
    ("groq", tr("Gratis, 14.400 peticiones/día. Muy rápido.")),
    ("ollama", tr("Local: sin internet, sin cuenta y sin coste. Hay que instalarlo.")),
]

PASOS_BASICOS = [
    (tr("1. Escribe tu IDEA"), tr("Una frase basta: “astronauta pescando en Marte”.")),
    (tr("2. Elige MODO"), tr("Imagen, Vídeo o Audio.")),
    (tr("3. Elige MODELO"), tr("Define el formato del prompt (prosa o tags, con negativo o sin él).")),
    (tr("4. Añade ESTILOS"), tr("Opcional, pero es lo que le da carácter al resultado.")),
    (tr("5. Pulsa GENERAR"), tr("Y refina desde ahí las veces que quieras.")),
]


def hay_algun_cerebro() -> bool:
    """True si al menos un proveedor LLM tiene API key configurada."""
    try:
        from api_clients import LLM_PROVIDERS, cargar_api_key
        return any(cargar_api_key(pid) for pid in LLM_PROVIDERS)
    except Exception as e:
        # Ante la duda NO molestamos: mejor no abrir la bienvenida que
        # abrírsela a alguien que ya tiene todo configurado.
        logger.debug(f"[silent] hay_algun_cerebro: {e}")
        return True


def _info_proveedor(pid: str) -> tuple[str, str]:
    """(nombre visible, url para obtener la key) de un proveedor."""
    try:
        from api_clients import LLM_PROVIDERS
        ficha = LLM_PROVIDERS.get(pid, {})
        return ficha.get("name", pid), ficha.get("url_obtener_key", "")
    except Exception:
        return pid, ""


def abrir_bienvenida(app) -> None:
    """Abre la ventana de bienvenida."""
    win = GPromptWindow(app)
    win.title(tr("👋 Bienvenido a G-Prompt Studio"))
    win.geometry("640x680")
    win.configure(fg_color=P.FONDO_SOBRIO)

    cont = ctk.CTkScrollableFrame(win, fg_color="transparent")
    cont.pack(fill="both", expand=True, padx=P.ESPACIO_L, pady=P.ESPACIO_L)

    ctk.CTkLabel(
        cont, text=tr("👋 Te falta un paso para empezar"),
        font=ctk.CTkFont(size=P.FUENTE_TITULO, weight="bold"),
        text_color=P.TXT_ACENTO, anchor="w",
    ).pack(fill="x", pady=(0, P.ESPACIO_XS))

    ctk.CTkLabel(
        cont,
        text=tr("G-Prompt no genera los prompts por su cuenta: usa un modelo de "
                "lenguaje como “cerebro”. Necesitas conectar uno.\n"
                "Estas cuatro opciones son GRATIS y no piden tarjeta."),
        font=ctk.CTkFont(size=P.FUENTE_CUERPO), justify="left", anchor="w",
        wraplength=560,
    ).pack(fill="x", pady=(0, P.ESPACIO_M))

    for pid, motivo in PROVEEDORES_GRATIS:
        nombre, url = _info_proveedor(pid)
        fila = ctk.CTkFrame(cont, fg_color=("gray92", "gray17"), corner_radius=8)
        fila.pack(fill="x", pady=P.ESPACIO_XS)

        izq = ctk.CTkFrame(fila, fg_color="transparent")
        izq.pack(side="left", fill="both", expand=True, padx=P.ESPACIO_M,
                 pady=P.ESPACIO_S)
        ctk.CTkLabel(izq, text=nombre, anchor="w",
                     font=ctk.CTkFont(size=P.FUENTE_CUERPO, weight="bold")
                     ).pack(fill="x")
        ctk.CTkLabel(izq, text=motivo, anchor="w", justify="left",
                     wraplength=380,
                     font=ctk.CTkFont(size=P.FUENTE_PEQUENA)).pack(fill="x")

        if url:
            ctk.CTkButton(
                fila, text=tr("Obtener key"), width=110, height=30,
                fg_color=P.BTN_ACENTO, hover_color=P.BTN_ACENTO_HOVER,
                command=lambda u=url: _abrir_url(u),
            ).pack(side="right", padx=P.ESPACIO_M, pady=P.ESPACIO_S)

    ctk.CTkButton(
        cont, text=tr("🔑 Ya tengo mi key — configurarla"), height=40,
        font=ctk.CTkFont(size=P.FUENTE_CUERPO, weight="bold"),
        fg_color=P.BTN_EXITO, hover_color=P.BTN_EXITO_HOVER,
        command=lambda: _configurar_keys(app, win),
    ).pack(fill="x", pady=(P.ESPACIO_M, P.ESPACIO_L))

    # ── Flujo básico ──
    ctk.CTkLabel(
        cont, text=tr("Y ya está: así se usa"),
        font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold"),
        text_color=P.TXT_ACENTO, anchor="w",
    ).pack(fill="x", pady=(0, P.ESPACIO_S))

    for titulo, detalle in PASOS_BASICOS:
        paso = ctk.CTkFrame(cont, fg_color="transparent")
        paso.pack(fill="x", pady=2)
        ctk.CTkLabel(paso, text=titulo, anchor="w",
                     font=ctk.CTkFont(size=P.FUENTE_CUERPO, weight="bold")
                     ).pack(fill="x")
        ctk.CTkLabel(paso, text=detalle, anchor="w", justify="left",
                     wraplength=540, text_color=P.TXT_INFO,
                     font=ctk.CTkFont(size=P.FUENTE_PEQUENA)).pack(fill="x")

    pie = ctk.CTkFrame(cont, fg_color="transparent")
    pie.pack(fill="x", pady=(P.ESPACIO_L, 0))
    ctk.CTkButton(
        pie, text=tr("📚 Ver el tutorial completo"), height=36,
        fg_color=P.BTN_NEUTRO, hover_color=P.BTN_NEUTRO_HOVER,
        command=lambda: _abrir_tutorial(app, win),
    ).pack(side="left", expand=True, fill="x", padx=(0, P.ESPACIO_XS))
    ctk.CTkButton(
        pie, text=tr("Empezar a trastear"), height=36,
        fg_color=P.BTN_GRIS, hover_color=P.BTN_GRIS_HOVER,
        command=win.destroy,
    ).pack(side="left", expand=True, fill="x", padx=(P.ESPACIO_XS, 0))

    return win


def _abrir_url(url: str) -> None:
    try:
        abrir_url(url)
    except Exception as e:
        logger.warning(f"No se pudo abrir {url}: {e}")


def _configurar_keys(app, win) -> None:
    """Cierra la bienvenida y abre el diálogo de API keys ya existente."""
    try:
        win.destroy()
    except Exception as e:
        logger.debug(f"[silent] cerrar bienvenida: {e}")
    try:
        app.dialogs._cmd_configurar_api_keys()
    except Exception as e:
        logger.warning(f"No se pudo abrir el diálogo de API keys: {e}")


def _abrir_tutorial(app, win) -> None:
    try:
        win.destroy()
    except Exception as e:
        logger.debug(f"[silent] cerrar bienvenida: {e}")
    try:
        from modules.tutorial import abrir_tutorial
        abrir_tutorial(app)
    except Exception as e:
        logger.warning(f"No se pudo abrir el tutorial: {e}")


def mostrar_si_hace_falta(app, retardo_ms: int = 800) -> None:
    """Abre la bienvenida si no hay ninguna API key configurada.

    Se llama al arrancar. El retardo deja que la ventana principal termine de
    construirse antes, para que la bienvenida salga por delante y centrada.
    """
    if hay_algun_cerebro():
        return

    def _abrir():
        try:
            abrir_bienvenida(app)
            logger.info("Bienvenida mostrada: no hay ninguna API key configurada.")
        except Exception as e:
            # Nunca debe impedir usar la app.
            logger.warning(f"No se pudo mostrar la bienvenida: {e}")

    try:
        app.after(retardo_ms, _abrir)
    except Exception as e:
        logger.debug(f"[silent] programar bienvenida: {e}")
