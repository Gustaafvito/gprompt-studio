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
TXT_MUTED = "#888888"     # ayuda / secundario (tema oscuro)
TXT_MUTED_OSCURO = "#666666"  # ayuda con más contraste (sirve en claro)

# ── Escala tipográfica (tamaños CTkFont) ───────────────────────────────
# Adoptar en código nuevo; el existente se migra de forma incremental.
FUENTE_TITULO = 18       # título de ventana
FUENTE_SECCION = 13      # cabecera de sección/card
FUENTE_CUERPO = 11       # texto normal, botones
FUENTE_HINT = 9          # ayudas, hints en cursiva
