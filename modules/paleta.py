"""Paleta semántica de la UI — fuente única de color para toda la app.

Antes de esto había ~750 colores hex hardcodeados (149 valores distintos,
8 tonos de verde para el mismo tipo de botón...). Este módulo define UN
color canónico por rol; los módulos de UI referencian el rol, no el hex.
Para redecorar la app entera basta con tocar este archivo.

Convención de roles:
  BTN_*   → fg_color / hover_color de botones según su semántica.
  TXT_*   → text_color de estados y mensajes (set_estado, labels).
  FUENTE_* → escala tipográfica (tamaños CTkFont).

Uso:
    from modules import paleta as P
    ctk.CTkButton(f, text="Guardar", fg_color=P.BTN_EXITO,
                  hover_color=P.BTN_EXITO_HOVER)
    self.set_estado(tr("✅ Guardado"), P.TXT_OK)

Los colores dependientes del tema claro/oscuro NO viven aquí: siguen en
config.get_theme_colors() (fondos, paneles, texto base).
"""

# ── Botones por semántica (fondo + hover) ──────────────────────────────
# Primario: la acción principal de la ventana (azul).
BTN_PRIMARIO = "#2563eb"
BTN_PRIMARIO_HOVER = "#1d4ed8"

# Éxito / confirmar / generar (verde).
BTN_EXITO = "#1a7a3c"
BTN_EXITO_HOVER = "#145e2d"

# Peligro / borrar / detener (rojo oscuro).
BTN_PELIGRO = "#7a1a1a"
BTN_PELIGRO_HOVER = "#5a0f0f"

# Acento IA / acciones especiales (morado).
BTN_ACENTO = "#7c3aed"
BTN_ACENTO_HOVER = "#6d28d9"

# Secundario / utilidades (teal apagado).
BTN_SECUNDARIO = "#1a4a5a"
BTN_SECUNDARIO_HOVER = "#155e75"

# Neutro / cancelar / cerrar (gris).
BTN_NEUTRO = "#444444"
BTN_NEUTRO_HOVER = "#555555"

# ── Texto de estado (set_estado, labels de feedback) ───────────────────
TXT_OK = "#2ecc71"        # éxito
TXT_ERROR = "#e74c3c"     # error
TXT_AVISO = "#e67e22"     # advertencia
TXT_INFO = "#3498db"      # progreso / info
TXT_ACENTO = "#fbbf24"    # destacado ámbar

# TXT_MUTED y TXT_MUTED_OSCURO son DINÁMICOS según el tema activo (ver
# __getattr__ abajo): en claro devuelven grises con contraste suficiente
# (#888 sobre blanco no llega a AA); en oscuro, los grises clásicos.
# Se resuelven al construir cada ventana, como el resto de colores.
_DINAMICOS_POR_TEMA = {
    # nombre: (tema claro, tema oscuro)
    "TXT_MUTED": ("#6b7280", "#888888"),
    "TXT_MUTED_OSCURO": ("#4b5563", "#666666"),
}


def __getattr__(nombre):  # PEP 562 — atributos de módulo dinámicos
    par = _DINAMICOS_POR_TEMA.get(nombre)
    if par is None:
        raise AttributeError(f"module 'paleta' has no attribute {nombre!r}")
    claro, oscuro = par
    try:
        import customtkinter as ctk
        if ctk.get_appearance_mode().lower() == "light":
            return claro
    except Exception:
        pass
    return oscuro

# ── Escala tipográfica (tamaños CTkFont) ───────────────────────────────
# 5 niveles. Tamaños ≥18 (splash, logos, dashboards) quedan fuera de la
# escala a propósito. El candado de tests/test_paleta.py impide volver a
# usar literales 7-16 dentro de CTkFont en los módulos de UI.
FUENTE_TITULO = 16       # título de ventana (antes 14/15/16 mezclados)
FUENTE_SECCION = 13      # cabecera de sección/card (antes 12/13)
FUENTE_CUERPO = 11       # texto normal, botones
FUENTE_PEQUENA = 10      # texto denso: listas, cards compactas
FUENTE_HINT = 9          # ayudas, hints en cursiva (antes 7/8/9)

# ── Estilo de botón sobrio (aprobado 2026-07-03) ───────────────────────
# Relleno neutro + borde fino del color semántico + hover coloreado.
# Se aplica a botones de utilidades (SECUNDARIO) y de acciones IA
# (ACENTO). Los rellenos verde/rojo/azul se conservan: marcan la
# jerarquía (confirmar / peligro / primario).
FONDO_SOBRIO = ("#eef1f5", "#1e2430")


def _oscurecer(hex_color: str, factor: float = 0.75) -> str:
    """Variante más oscura de un color hex (para hovers)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"#{int(r * factor):02x}{int(g * factor):02x}{int(b * factor):02x}"


def estilo_boton(color: str, primario: bool = False) -> dict:
    """kwargs de CTkButton para el estilo de la app.

    primario=True → relleno del color (acción principal de la ventana).
    primario=False → sobrio: neutro + borde y hover del color semántico.
    """
    if primario:
        return {"fg_color": color, "hover_color": _oscurecer(color)}
    return {
        "fg_color": FONDO_SOBRIO,
        "hover_color": _oscurecer(color),
        "border_width": 1,
        "border_color": color,
    }


# ── Escala de espaciado (padx/pady) — guía para código nuevo ───────────
# Usar múltiplos de 4: 4 (compacto), 8 (normal), 12 (secciones),
# 16 (márgenes de ventana), 20 (aire exterior). El código existente se
# migra por ventana, con revisión visual (no por codemod ciego).
ESPACIO_XS = 4
ESPACIO_S = 8
ESPACIO_M = 12
ESPACIO_L = 16
ESPACIO_XL = 20
