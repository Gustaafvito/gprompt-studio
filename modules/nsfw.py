"""El modo 🔞 NSFW: cuándo pedirlo, y cuándo el modelo elegido no lo va a dejar.

QUÉ PASABA (revisado el 24-sep-2026)
  • La detección automática no funcionaba NUNCA. Escribía en `nsfw_var`, que
    no existe (la variable es `switch_nsfw_var`), y aun así anunciaba
    «Contenido NSFW detectado — activado modo NSFW». El prompt salía en modo
    normal.
  • Buscaba subcadenas en inglés: «ass» saltaba con «class», «glass» o
    «passion»; «butt» con «button»; «sex» con «sexy». Y ninguna palabra en
    castellano, que es como se escribe la idea.
  • Con NSFW encendido y un modelo que filtra el contenido adulto (GPT Image,
    Nano Banana, Midjourney…), el prompt salía explícito y la plataforma lo
    rechazaba. Nadie avisaba.
  • Con un modelo para adultos elegido y NSFW apagado, el prompt salía
    suavizado. Tampoco se avisaba.

Aquí, funciones puras; la interfaz solo las consulta.
"""
import re

# Solo términos INEQUÍVOCOS. «sexy», «lencería» o «bikini» son sugerentes, no
# explícitos: un prompt normal los maneja bien y no deben encender nada.
_EXPLICITOS = (
    # inglés
    "nude", "nudes", "naked", "nudity", "topless", "nsfw", "porn", "porno",
    "pornographic", "xxx", "hentai", "erotic", "erotica", "sex", "sexual",
    "genitals", "nipples", "lewd",
    # castellano
    "desnuda", "desnudas", "desnudo", "desnudos", "desnudez", "pornográfico",
    "pornográfica", "erótico", "erótica", "eróticos", "eróticas", "sexo",
    "pezones", "genitales",
)
_PATRON = re.compile(r"\b(" + "|".join(map(re.escape, _EXPLICITOS)) + r")\b",
                     re.IGNORECASE)

# Familias cuyo fabricante filtra desnudos y contenido sexual explícito en su
# propia API, lo sirva quien lo sirva (OpenAI, Google, Midjourney, Ideogram,
# Microsoft, Adobe). Por PREFIJO exacto: «Midjourney Mimic Neo» es un modelo
# comunitario de FLUX, no Midjourney, y no filtra nada.
_FILTRAN = (
    "GPT Image", "DALL-E", "Sora",                       # OpenAI
    "Nano Banana", "Imagen ", "Veo ", "Gemini",          # Google
    "Midjourney v", "Niji",                              # Midjourney
    "Ideogram",                                          # Ideogram
    "MAI-Image",                                         # Microsoft
    "Firefly",                                           # Adobe
)

GRUPO_ADULTOS = "── NSFW / Adultos ──"


def pide_nsfw(texto):
    """¿La idea pide contenido explícito? Palabras enteras, en inglés o castellano."""
    return bool(texto) and _PATRON.search(texto) is not None


def filtra_adultos(modelo):
    """¿El fabricante del modelo rechaza desnudos y contenido explícito?"""
    return bool(modelo) and modelo.startswith(_FILTRAN)


def es_modelo_adulto(modelo, grupos=None):
    """¿Es un modelo hecho para contenido adulto?

    `grupos`: [(cabecera, [modelos])] del catálogo de imagen. Los de vídeo
    «SeaArt Spicy Video» no tienen grupo propio: van por nombre.
    """
    if not modelo:
        return False
    if "Spicy" in modelo:
        return True
    for cabecera, modelos in grupos or ():
        if cabecera == GRUPO_ADULTOS and modelo in modelos:
            return True
    return False


def aviso(modelo, nsfw_activo, grupos=None):
    """Qué decirle al usuario sobre NSFW con este modelo, o None si nada.

    Devuelve la clave del mensaje (sin traducir) para que la interfaz la pase
    por tr(): «filtra» o «adulto_apagado».
    """
    if nsfw_activo and filtra_adultos(modelo):
        return "filtra"
    if not nsfw_activo and es_modelo_adulto(modelo, grupos):
        return "adulto_apagado"
    return None
