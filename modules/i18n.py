"""i18n — interfaz bilingüe (español por defecto, inglés opcional).

Sistema ligero y de bajo riesgo: las cadenas se siguen escribiendo en ESPAÑOL
en el código y se envuelven con `tr("texto en español")`. `tr` devuelve la
traducción al inglés SOLO si el idioma activo es "en" y existe en TRADUCCIONES;
en cualquier otro caso devuelve el español tal cual (fallback seguro, nunca
rompe ni muestra una clave).

El idioma se elige en el menú "UI → 🌐 Idioma" y se aplica al **reiniciar** la
app (lo más fiable: al reconstruir la UI, `tr` ya devuelve el idioma nuevo).
La preferencia se guarda en `preferences.json` (clave `idioma`).

FASE A (infraestructura): este módulo + el toggle + la persistencia. El
diccionario TRADUCCIONES arranca con un set representativo y se irá completando
en la Fase B (envolver los ~760 textos de la UI con `tr(...)`).

Uso:
    from modules.i18n import tr, set_idioma, get_idioma
    ctk.CTkLabel(parent, text=tr("Modelo"))
"""

_IDIOMA = "es"

# ES → EN. Lo que NO esté aquí cae al español (fallback). Se completa en Fase B.
TRADUCCIONES = {
    # Modos / barra superior
    "Imagen": "Image",
    "Vídeo": "Video",
    "Audio": "Audio",
    "Plataforma:": "Platform:",
    # Etiquetas de combos (barra imagen/vídeo/audio)
    "Modelo": "Model",
    "Modelo:": "Model:",
    "Estilo": "Style",
    "Estilo:": "Style:",
    "Ratio": "Ratio",
    "Ratio:": "Ratio:",
    "Destino": "Destination",
    "Destino:": "Destination:",
    "Duración:": "Duration:",
    "Shots:": "Shots:",
    "Personaje:": "Character:",
    "Plantilla:": "Template:",
    "Imagen ref:": "Ref image:",
    # Botones de acción comunes
    "Generar": "Generate",
    "Variaciones": "Variations",
    "Refinar": "Refine",
    "Iterar": "Iterate",
    "Sugerir": "Suggest",
    "Analizar": "Analyze",
    "Cargar": "Load",
    "Borrar": "Delete",
    "Guardar actual": "Save current",
    "Reset": "Reset",
    "Cerrar": "Close",
    # Menús de cabecera
    "📊 Análisis": "📊 Analytics",
    "📚 Aprender": "📚 Learn",
    "💾 Backup": "💾 Backup",
    "📁 Datos": "📁 Data",
    "🛠 Herramientas": "🛠 Tools",
    "📝 Plantillas": "📝 Templates",
    "🎨 UI": "🎨 UI",
    "⚙️ Workflow": "⚙️ Workflow",
    # Misc
    "Describe tu idea": "Describe your idea",
    "Resultado editable": "Editable result",
    "Sin imagen": "No image",
    "Recientes:": "Recent:",
    "Modo Brief": "Brief mode",
}


def set_idioma(lang: str) -> None:
    """Fija el idioma activo. 'en'/'english' → inglés; cualquier otro → español."""
    global _IDIOMA
    _IDIOMA = "en" if str(lang or "").strip().lower().startswith("en") else "es"


def get_idioma() -> str:
    """Devuelve el idioma activo ('es' o 'en')."""
    return _IDIOMA


def tr(texto_es: str) -> str:
    """Traduce `texto_es` al idioma activo. Fallback al español si no hay traducción."""
    if _IDIOMA == "en":
        return TRADUCCIONES.get(texto_es, texto_es)
    return texto_es
