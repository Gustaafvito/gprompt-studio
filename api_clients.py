"""
G-Prompt Studio v1.0 — Clientes API (Multi-LLM con arquitectura de adapters).

Cada proveedor implementa la misma interfaz BaseLLMProvider:
  - completar(messages, temperature, max_tokens) -> str
  - disponible() -> bool

Para añadir un proveedor nuevo solo hay que crear su clase aquí.
"""
import json
import logging
import os
import re
import urllib.request

try:
    from openai import OpenAI
    OPENAI_DISPONIBLE = True
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]
    OPENAI_DISPONIBLE = False

try:
    from google import genai as google_genai
    from google.genai import types as genai_types
    GEMINI_DISPONIBLE = True
except ImportError:
    GEMINI_DISPONIBLE = False

try:
    from dotenv import load_dotenv
    # Buscar .env tanto en cwd como en la carpeta del proyecto (donde está este archivo).
    # Sin esto, lanzar la app desde otra carpeta (p.ej. doble clic en main.py) ignora el .env.
    _proj_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv()                # .env de cwd (si existe)
    load_dotenv(_proj_env, override=False)  # .env del proyecto (no pisa lo ya cargado)
except ImportError:
    pass

logger = logging.getLogger(__name__)


# REGISTRO DE PROVEEDORES

LLM_PROVIDERS = {
    "claude": {
        "name": "Claude (Anthropic)",
        "label": "💎 Claude (calidad top)",
        "descripcion": "Calidad excelente para creatividad. Pago (desde $3/1M).",
        "url_obtener_key": "https://console.anthropic.com/settings/keys",
        "tipo": "anthropic",
        # IDs oficiales junio 2026 (skill claude-api). Sonnet 4.6 como
        # default: mejor equilibrio velocidad/inteligencia/precio.
        # NOTA: claude-fable-5 retirado por Anthropic el 12-jun-2026
        # (orden gobierno EE.UU., suspensión para todos los usuarios).
        # Si lo restauran, volver a añadirlo aquí + a PRECIOS y al guard.
        "model_default": "claude-sonnet-4-6",
        "modelos": [
            "claude-opus-4-8",     # Opus actual ($5/$25)
            "claude-sonnet-4-6",   # equilibrio ($3/$15)
            "claude-haiku-4-5",    # rápido y barato ($1/$5)
        ],
        "is_paid": True,
    },
    "deepseek": {
        "name": "DeepSeek V4",
        "label": "🥈 DeepSeek V4",
        "descripcion": "Económico (~€0.14/1M tokens). Bueno para creatividad, robusto.",
        "url_obtener_key": "https://platform.deepseek.com/api_keys",
        "tipo": "openai_compatible",
        "base_url": "https://api.deepseek.com",
        "model_default": "deepseek-chat",
        "modelos": ["deepseek-chat", "deepseek-reasoner"],
        "is_paid": True,
    },
    "fireworks": {
        "name": "Fireworks AI",
        "label": "💎 Fireworks AI",
        "descripcion": "Inferencia ultrarrápida con modelos open-source. Buena relación calidad/precio.",
        "url_obtener_key": "https://fireworks.ai/api-keys",
        "tipo": "openai_compatible",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "model_default": "accounts/fireworks/models/llama-v3p3-70b-instruct",
        "modelos": [
            "accounts/fireworks/models/llama-v3p3-70b-instruct",  # Llama 3.3 70B
            "accounts/fireworks/models/qwen2p5-72b-instruct",     # Qwen 2.5 72B
            "accounts/fireworks/models/deepseek-r1",              # DeepSeek R1
            "accounts/fireworks/models/mixtral-8x22b-instruct",   # Mixtral 8x22B
        ],
        "is_paid": True,
    },
    "gemini": {
        "name": "Google Gemini",
        "label": "🏆 Google Gemini",
        "descripcion": "Gratis hasta 15rpm. Bueno para visión y prompts.",
        "url_obtener_key": "https://aistudio.google.com/apikey",
        "tipo": "google",
        "model_default": "gemini-2.5-flash",
        "modelos": [
            "gemini-2.5-flash",   # rápido, gratis tier generoso
            "gemini-2.5-pro",     # mayor calidad, límites más bajos
            "gemini-2.0-flash",   # estable, buena relación velocidad/coste
        ],
        "is_paid": False,
    },
    "github_models": {
        "name": "GitHub Models",
        "label": "🏆 GitHub Models",
        "descripcion": "Gratis con cuenta GitHub. Acceso a OpenAI/Claude/Llama. Límite generoso.",
        "url_obtener_key": "https://github.com/settings/tokens",
        "tipo": "openai_compatible",
        "base_url": "https://models.inference.ai.azure.com",
        "model_default": "gpt-4o-mini",
        "modelos": [
            "gpt-4o-mini",                      # OpenAI económico
            "gpt-4o",                           # OpenAI flagship
            "Meta-Llama-3.3-70B-Instruct",      # Llama 3.3 70B
            "Phi-4",                            # Microsoft Phi-4 14B
            "Phi-4-mini",                       # Microsoft Phi-4 mini
            "Mistral-large",                    # Mistral Large
        ],
        "is_paid": False,
    },
    "groq": {
        "name": "Groq",
        "label": "🏆 Groq (gratis, rápido)",
        "descripcion": "Gratis (14.400 req/día). Llama 3.3 70B muy rápido.",
        "url_obtener_key": "https://console.groq.com/keys",
        "tipo": "openai_compatible",
        "base_url": "https://api.groq.com/openai/v1",
        "model_default": "llama-3.3-70b-versatile",
        "modelos": [
            "llama-3.3-70b-versatile",        # más capaz, gratis
            "llama-3.1-8b-instant",            # ultra-rápido
            "llama-3.2-90b-vision-preview",    # con visión
            "gemma2-9b-it",                    # Google Gemma 2
            "mixtral-8x7b-32768",              # Mixtral MoE, contexto largo
        ],
        "is_paid": False,
    },
    "lm_studio": {
        "name": "LM Studio",
        "label": "🏠 LM Studio (local)",
        "descripcion": "Servidor local OpenAI-compatible. Requiere instalar LM Studio y cargar un modelo.",
        "url_obtener_key": "https://lmstudio.ai",
        "tipo": "openai_compatible",
        "base_url": "http://localhost:1234/v1",
        "model_default": "local-model",
        "is_paid": False,
    },
    "mistral": {
        "name": "Mistral",
        "label": "💎 Mistral",
        "descripcion": "Modelos europeos, calidad/precio competitivo.",
        "url_obtener_key": "https://console.mistral.ai/api-keys/",
        "tipo": "openai_compatible",
        "base_url": "https://api.mistral.ai/v1",
        "model_default": "mistral-large-latest",
        "modelos": [
            "mistral-large-latest",   # flagship Mistral
            "mistral-small-latest",   # económico, muy rápido
            "codestral-latest",       # especializado en código
            "mistral-nemo",           # 12B, Apache 2.0, contexto 128k
            "open-mistral-7b",        # open-source ligero
        ],
        "is_paid": True,
    },
    "ollama": {
        "name": "Ollama (local)",
        "label": "🏆 Ollama local (sin internet)",
        "descripcion": "Sin internet, sin coste. Requiere instalar Ollama y descargar modelo.",
        "url_obtener_key": "https://ollama.com/download",
        "tipo": "openai_compatible",
        "base_url": "http://localhost:11434/v1",
        "model_default": "llama3.2",
        "modelos": [
            "llama3.2",        # más reciente, 3B/11B
            "llama3.1",        # 8B/70B/405B
            "mistral",         # Mistral 7B
            "codellama",       # código, 7B-70B
            "phi3",            # Microsoft Phi-3, ligero
            "qwen2.5",         # Qwen 2.5, excelente en asiático/código
            "gemma2",          # Google Gemma 2
            "llava",           # visión multimodal local
            "deepseek-r1",     # razonamiento local
        ],
        "is_paid": False,
    },
    "openai": {
        "name": "OpenAI",
        "label": "💎 OpenAI",
        "descripcion": "GPT-4o, GPT-4.1 y modelos de razonamiento o3/o4. Pago.",
        "url_obtener_key": "https://platform.openai.com/api-keys",
        "tipo": "openai_compatible",
        "base_url": "https://api.openai.com/v1",
        "model_default": "gpt-4o",
        "modelos": [
            "gpt-4o",          # flagship multimodal
            "gpt-4o-mini",     # económico, rápido
            "gpt-4.1",         # contexto 1M, mejor en código/instrucciones
            "gpt-4.1-mini",    # 4.1 económico
            "gpt-4.1-nano",    # 4.1 ultra-rápido y barato
            "o3",              # razonamiento máximo
            "o4-mini",         # razonamiento rápido
        ],
        "is_paid": True,
    },
    "openrouter": {
        "name": "OpenRouter",
        "label": "🥈 OpenRouter (100+ modelos)",
        "descripcion": "Acceso a OpenAI/Claude/Gemini/Llama y más con UNA sola key.",
        "url_obtener_key": "https://openrouter.ai/keys",
        "tipo": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        # Modelo gratis y siempre disponible en OpenRouter. Antes era
        # "deepseek/deepseek-chat" pero ese ID legacy devuelve 404.
        "model_default": "meta-llama/llama-3.1-8b-instruct:free",
        "modelos": [
            # Gratuitos (sufijo :free)
            "meta-llama/llama-3.1-8b-instruct:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemma-2-9b-it:free",
            "mistralai/mistral-7b-instruct:free",
            "qwen/qwen-2.5-72b-instruct:free",
            "deepseek/deepseek-r1:free",
            # De pago (acceso a los mejores modelos con una sola key)
            "anthropic/claude-sonnet-4-6",
            "openai/gpt-4o",
            "google/gemini-2.5-pro",
            "meta-llama/llama-3.3-70b-instruct",
        ],
        "is_paid": True,
    },
    "perplexity": {
        "name": "Perplexity",
        "label": "💎 Perplexity",
        "descripcion": "API Sonar de Perplexity. Modelos con búsqueda en tiempo real integrada.",
        "url_obtener_key": "https://www.perplexity.ai/settings/api",
        "tipo": "openai_compatible",
        "base_url": "https://api.perplexity.ai",
        "model_default": "sonar-pro",
        "modelos": [
            "sonar-pro",        # con búsqueda web en tiempo real, máxima calidad
            "sonar",            # con búsqueda, económico
            "sonar-reasoning",  # razonamiento + búsqueda web
        ],
        "is_paid": True,
    },
    "togetherai": {
        "name": "Together AI",
        "label": "💎 Together AI",
        "descripcion": "Modelos open-source y propietarios. Bueno para code y razonamiento.",
        "url_obtener_key": "https://api.together.xyz/settings/api-keys",
        "tipo": "openai_compatible",
        "base_url": "https://api.together.xyz/v1",
        "model_default": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "modelos": [
            "meta-llama/Llama-3.3-70B-Instruct-Turbo",   # flagship open-source
            "Qwen/Qwen2.5-72B-Instruct-Turbo",            # Qwen 2.5 72B
            "deepseek-ai/DeepSeek-R1",                     # razonamiento
            "mistralai/Mistral-7B-Instruct-v0.3",          # ligero
            "google/gemma-2-27b-it",                       # Gemma 2 27B
        ],
        "is_paid": True,
    },
    "xai": {
        "name": "xAI Grok",
        "label": "💎 xAI Grok",
        "descripcion": "Modelos de xAI (Elon Musk). Calidad alta.",
        "url_obtener_key": "https://console.x.ai/",
        "tipo": "openai_compatible",
        "base_url": "https://api.x.ai/v1",
        "model_default": "grok-3",
        "modelos": [
            "grok-3",       # flagship xAI, excelente creatividad
            "grok-3-mini",  # rápido y económico
            "grok-2-1212",  # generación anterior, estable
        ],
        "is_paid": True,
    },
}


# Proveedores de IMAGEN (no LLM). Se gestionan en el mismo wizard
# 🔑 API Keys pero se renderizan en una sección aparte, y NO aparecen
# en el dropdown del LLM activo del header. Compartirán el mismo
# sistema de almacenamiento (keyring / keys.json / .env) que LLM_PROVIDERS.
IMAGE_PROVIDERS = {
    "pollinations": {
        "name": "Pollinations.ai",
        "label": "🖼 Pollinations.ai (previews)",
        "descripcion": (
            "Previews rápidos en el comparador 👁 y botón 🖼 Preview. "
            "Con tu key: hasta ~555 imágenes flux por 1€ (1 Pollen). "
            "Sin key: anonymous con rate limit estricto (lento). "
            "Registra cuenta gratis en pollinations.ai → API → + API Key."
        ),
        "url_obtener_key": "https://pollinations.ai/auth",
        "tipo": "image_service",
        "model_default": "flux",
        "is_paid": False,  # Funciona en anónimo, no es obligatorio
    },
}


# PRECIOS Y TRACKING DE USO (sesión 19)

# Precios por MODELO concreto (USD por 1M tokens entrada/salida).
# Tiene prioridad sobre PRECIOS_USD_1M cuando el modelo es conocido.
# Claude: IDs y precios oficiales de Anthropic (junio 2026).
PRECIOS_USD_1M_MODELO: dict[str, tuple[float, float]] = {
    # claude-fable-5 retirado 12-jun-2026 (ver nota en LLM_PROVIDERS).
    # Se deja el precio comentado por si se restaura el acceso.
    # "claude-fable-5":          (10.00, 50.00),
    "claude-opus-4-8":           (5.00, 25.00),
    "claude-opus-4-7":           (5.00, 25.00),
    "claude-opus-4-6":           (5.00, 25.00),
    "claude-sonnet-4-6":         (3.00, 15.00),
    "claude-sonnet-4-5-20250929": (3.00, 15.00),
    "claude-haiku-4-5":          (1.00, 5.00),
    "deepseek-chat":             (0.28, 0.42),
    "deepseek-reasoner":         (0.28, 0.42),
    "gpt-4o":                    (2.50, 10.00),
    "gpt-4o-mini":               (0.15, 0.60),
    "gemini-2.5-flash":          (0.0, 0.0),   # free tier
    "gemini-2.5-pro":            (0.0, 0.0),   # free tier (límites más bajos)
    "gemini-2.0-flash":          (0.0, 0.0),   # free tier
    # OpenAI GPT-4.1 y razonamiento (precios abril 2025)
    "gpt-4.1":                   (2.00,  8.00),
    "gpt-4.1-mini":              (0.40,  1.60),
    "gpt-4.1-nano":              (0.10,  0.40),
    "o3":                        (10.00, 40.00),
    "o4-mini":                   (1.10,  4.40),
    # xAI Grok 3
    "grok-3":                    (3.00, 15.00),
    "grok-3-mini":               (0.30,  0.50),
    # Mistral
    "mistral-large-latest":      (2.00,  6.00),
    "mistral-small-latest":      (0.10,  0.30),
    "codestral-latest":          (0.30,  0.90),
    "mistral-nemo":              (0.15,  0.15),
    # Perplexity Sonar
    "sonar-pro":                 (3.00, 15.00),
    "sonar":                     (1.00,  1.00),
    "sonar-reasoning":           (5.00,  5.00),
}

# Precios en USD por 1M tokens (entrada, salida) para el model_default
# de cada proveedor. Valores de junio 2026 — revisar periódicamente.
# - Proveedores gratuitos / locales: (0, 0).
# - None = coste variable o desconocido (p.ej. OpenRouter, donde el
#   precio depende del modelo elegido) → se muestra "—" en la UI.
PRECIOS_USD_1M: dict[str, tuple[float, float] | None] = {
    "claude":        (3.00, 15.00),   # claude-sonnet-4-5
    "deepseek":      (0.28, 0.42),    # deepseek-chat
    "fireworks":     (0.90, 0.90),    # llama-v3p3-70b
    "gemini":        (0.0, 0.0),      # free tier 15rpm (tier de pago: 0.30/2.50)
    "github_models": (0.0, 0.0),      # gratis con cuenta GitHub
    "groq":          (0.0, 0.0),      # free tier
    "lm_studio":     (0.0, 0.0),      # local
    "mistral":       (2.00, 6.00),    # mistral-large
    "ollama":        (0.0, 0.0),      # local
    "openai":        (2.50, 10.00),   # gpt-4o
    "openrouter":    None,            # depende del modelo elegido
    "perplexity":    (3.00, 15.00),   # sonar-pro
    "togetherai":    (0.88, 0.88),    # Llama-3.3-70B-Turbo
    "xai":           (3.00, 15.00),   # grok-3
}


def calcular_coste_usd(provider_id: str, tokens_entrada: int,
                       tokens_salida: int, modelo: str = "") -> float | None:
    """Coste estimado en USD, o None si el precio es desconocido.

    Si se pasa `modelo` y está en PRECIOS_USD_1M_MODELO, su precio tiene
    prioridad (p.ej. claude-opus-4-8 cuesta 1.67× más que sonnet-4-6).
    """
    precios = PRECIOS_USD_1M_MODELO.get(modelo) if modelo else None
    if precios is None:
        precios = PRECIOS_USD_1M.get(provider_id)
    if precios is None:
        return None
    p_in, p_out = precios
    return (tokens_entrada * p_in + tokens_salida * p_out) / 1_000_000


class UsageTracker:
    """Acumulador thread-safe de tokens consumidos en la sesión.

    Los providers llaman a registrar() tras cada completar(); la UI
    consulta resumen() para mostrar el coste estimado de la sesión.
    """

    def __init__(self):
        import threading
        self._lock = threading.Lock()
        self._datos: dict[str, dict] = {}
        # Contadores ya volcados al histórico persistente (para calcular
        # deltas en pendiente_persistir sin contar dos veces).
        self._drenado: dict[str, dict] = {}

    def registrar(self, provider_id: str, tokens_entrada: int,
                  tokens_salida: int, modelo: str = "") -> None:
        if not provider_id:
            provider_id = "desconocido"
        with self._lock:
            d = self._datos.setdefault(provider_id, {
                "llamadas": 0, "tokens_entrada": 0, "tokens_salida": 0,
                "modelos": {},
            })
            d["llamadas"] += 1
            t_in = max(0, int(tokens_entrada or 0))
            t_out = max(0, int(tokens_salida or 0))
            d["tokens_entrada"] += t_in
            d["tokens_salida"] += t_out
            # Desglose por modelo: el coste varía mucho dentro de un mismo
            # proveedor (claude-opus-4-8 = 1.67× claude-sonnet-4-6).
            m = d["modelos"].setdefault(modelo or "_default",
                                        {"tokens_entrada": 0, "tokens_salida": 0})
            m["tokens_entrada"] += t_in
            m["tokens_salida"] += t_out

    def resumen(self) -> dict[str, dict]:
        """Copia del estado con coste_usd calculado por proveedor.

        El coste se calcula por MODELO (suma de los desgloses) usando
        PRECIOS_USD_1M_MODELO cuando el modelo es conocido; None si
        ningún precio es conocido (p.ej. OpenRouter con modelo custom)."""
        with self._lock:
            out = {}
            for pid, d in self._datos.items():
                out[pid] = dict(d)
                costes = []
                for modelo, m in d.get("modelos", {}).items():
                    costes.append(calcular_coste_usd(
                        pid, m["tokens_entrada"], m["tokens_salida"],
                        modelo="" if modelo == "_default" else modelo))
                if not costes or all(c is None for c in costes):
                    out[pid]["coste_usd"] = None
                else:
                    out[pid]["coste_usd"] = sum(c for c in costes if c is not None)
            return out

    def total_usd(self) -> float:
        """Suma de los costes conocidos (los None no suman)."""
        return sum(d["coste_usd"] for d in self.resumen().values()
                   if d["coste_usd"] is not None)

    def pendiente_persistir(self) -> dict[str, dict]:
        """Delta de uso desde el último volcado al histórico.

        Devuelve {provider: {llamadas, tokens_entrada, tokens_salida}}
        solo con lo NUEVO desde la última llamada, y lo marca como
        drenado. Idempotente: dos llamadas seguidas → la segunda {}.
        """
        with self._lock:
            delta = {}
            for pid, d in self._datos.items():
                prev = self._drenado.get(pid, {})
                dif = {k: d[k] - prev.get(k, 0)
                       for k in ("llamadas", "tokens_entrada", "tokens_salida")}
                if any(v > 0 for v in dif.values()):
                    delta[pid] = dif
                self._drenado[pid] = dict(d)
            return delta

    def reset(self) -> None:
        with self._lock:
            self._datos.clear()
            self._drenado.clear()


def acumular_historico(historico: dict, delta: dict, fecha: str,
                       max_dias: int = 60) -> dict:
    """Acumula un delta de uso en el histórico persistente.

    Formato: {fecha_iso: {provider: {llamadas, tokens_entrada,
    tokens_salida}}}. Muta y devuelve `historico`. Poda los días más
    antiguos si supera max_dias (las fechas ISO ordenan correctamente).
    """
    dia = historico.setdefault(fecha, {})
    for pid, d in delta.items():
        acc = dia.setdefault(pid, {"llamadas": 0, "tokens_entrada": 0,
                                   "tokens_salida": 0})
        for k in ("llamadas", "tokens_entrada", "tokens_salida"):
            acc[k] = acc.get(k, 0) + max(0, int(d.get(k, 0)))
    if len(historico) > max_dias:
        for vieja in sorted(historico)[:len(historico) - max_dias]:
            historico.pop(vieja, None)
    return historico


def coste_dia_usd(datos_dia: dict) -> float:
    """Coste estimado de un día del histórico (suma de costes conocidos)."""
    total = 0.0
    for pid, d in datos_dia.items():
        c = calcular_coste_usd(pid, d.get("tokens_entrada", 0),
                               d.get("tokens_salida", 0))
        if c is not None:
            total += c
    return total


# Instancia global de sesión (se resetea al reiniciar la app).
usage_tracker = UsageTracker()


# INTERFAZ BASE

class BaseLLMProvider:
    """Interfaz que todos los proveedores deben implementar."""

    # Asignado por get_provider() — permite que completar() registre
    # el uso de tokens en usage_tracker con la key correcta.
    provider_id: str = ""

    def __init__(self, api_key: str | None, model: str | None = None, **kwargs):
        self.api_key = api_key
        self.model = model
        self._cliente = None

    def _registrar_uso(self, tokens_entrada, tokens_salida) -> None:
        """Registra tokens en el tracker global. Nunca rompe la generación."""
        try:
            usage_tracker.registrar(self.provider_id,
                                    tokens_entrada or 0, tokens_salida or 0,
                                    modelo=self.model or "")
        except Exception as e:
            logger.debug(f"[silent] registro de uso: {e}")

    def disponible(self) -> bool:
        return bool(self.api_key)

    def completar(self, messages: list[dict], temperature: float = 0.75, max_tokens: int = 900, model: str | None = None) -> str:
        raise NotImplementedError


class OpenAICompatibleProvider(BaseLLMProvider):
    """Para todos los proveedores OpenAI-compatible."""

    def __init__(self, api_key: str | None, model: str | None = None, base_url: str | None = None, **kwargs):
        super().__init__(api_key, model)
        self.base_url = base_url
        if api_key:
            if not OPENAI_DISPONIBLE:
                raise ImportError("Paquete `openai` no instalado. Instala con: pip install openai")
            self._cliente = OpenAI(api_key=api_key or "sin-key", base_url=base_url)

    def disponible(self) -> bool:
        return bool(self.api_key) and self._cliente is not None

    def completar(self, messages: list[dict], temperature: float = 0.75, max_tokens: int = 900, model: str | None = None) -> str:
        if not self._cliente:
            raise Exception("Proveedor no configurado (sin api key)")
        modelo = model or self.model
        logger.debug(f"OpenAICompatible: calling {modelo}")
        res = self._cliente.chat.completions.create(
            model=modelo, messages=messages, temperature=temperature, max_tokens=max_tokens,
        )
        usage = getattr(res, "usage", None)
        if usage is not None:
            self._registrar_uso(getattr(usage, "prompt_tokens", 0),
                                getattr(usage, "completion_tokens", 0))
        # `choices` puede venir vacío y `content` puede ser None (p.ej.
        # respuesta filtrada o proveedor "compatible" que no lo rellena).
        # Sin este guard, un None se propaga al historial y a los parsers.
        if not getattr(res, "choices", None):
            raise Exception(f"{modelo}: respuesta sin choices (filtrada o vacía)")
        return res.choices[0].message.content or ""


class OllamaProvider(OpenAICompatibleProvider):
    """Variante: Ollama local. Detecta modelo instalado automáticamente."""

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str = "http://localhost:11434/v1", **kwargs):
        super().__init__(api_key="ollama", model=model, base_url=base_url)

    def disponible(self) -> bool:
        try:
            with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as r:
                data = json.loads(r.read())
                return bool(data.get("models", []))
        except Exception:
            return False

    def _obtener_modelo_disponible(self) -> str | None:
        try:
            with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
                data = json.loads(r.read())
            modelos = [m["name"] for m in data.get("models", [])]
            return modelos[0] if modelos else None
        except Exception:
            return None

    def completar(self, messages: list[dict], temperature: float = 0.75, max_tokens: int = 900, model: str | None = None) -> str:
        modelo = model or self.model or self._obtener_modelo_disponible()
        if not modelo:
            raise Exception("No se encontró Ollama corriendo o no tienes modelos instalados.")
        return super().completar(messages, temperature, max_tokens, model=modelo)


def _limpiar_respuesta_gemini(raw: str) -> str:
    """Elimina ecos de tags <system-reminder> de una respuesta de Gemini.

    Solo se tocan esos tags (nunca legítimos en un prompt generado) y se
    loggea cuando actúa. El scrubbing anterior borraba además frases
    genéricas ("You are Claude", "You are an AI"...) y corrompía en
    silencio prompts que las contenían de verdad.
    """
    limpio = re.sub(r"<system-reminder>.*?</system-reminder>", "",
                    raw, flags=re.DOTALL)
    limpio = (limpio.replace("<system-reminder>", "")
                    .replace("</system-reminder>", ""))
    if limpio != raw:
        logger.warning("GeminiProvider: tags <system-reminder> "
                       "eliminados de la respuesta")
    return limpio.strip()


class GeminiProvider(BaseLLMProvider):
    """Adapter para Google Gemini con soporte nativo multi-turno (chat sessions)."""

    def __init__(self, api_key: str | None, model: str | None = None, **kwargs):
        super().__init__(api_key, model)
        if api_key and GEMINI_DISPONIBLE:
            self._cliente = google_genai.Client(api_key=api_key)

    def disponible(self) -> bool:
        return GEMINI_DISPONIBLE and bool(self.api_key)

    def completar(self, messages: list[dict], temperature: float = 0.75, max_tokens: int = 900, model: str | None = None) -> str:
        if not self.api_key:
            raise Exception("Gemini no configurado (sin api key)")
        if not GEMINI_DISPONIBLE:
            raise Exception("google-genai no instalado")

        if self._cliente is None:
            self._cliente = google_genai.Client(api_key=self.api_key)
        cliente = self._cliente

        modelo = model or self.model or "gemini-2.5-flash"

        contents = []
        system_instruction = ""
        for m in messages:
            if m["role"] == "system":
                system_instruction = m["content"]
            else:
                role = "user" if m["role"] == "user" else "model"
                contents.append(genai_types.Content(role=role, parts=[genai_types.Part.from_text(text=m["content"])]))

        if not contents:
            raise Exception("Gemini: no hay mensajes de usuario para enviar.")

        config = genai_types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction if system_instruction else None,
        )

        response = cliente.models.generate_content(
            model=modelo,
            contents=contents,
            config=config,
        )

        meta = getattr(response, "usage_metadata", None)
        if meta is not None:
            self._registrar_uso(getattr(meta, "prompt_token_count", 0),
                                getattr(meta, "candidates_token_count", 0))

        return _limpiar_respuesta_gemini(response.text or "")


# Modelos Claude que RECHAZAN parámetros de sampling (temperature/top_p/
# top_k devuelven 400): Opus 4.7/4.8 los tienen eliminados.
# Fuente: doc oficial de migración de Anthropic (junio 2026).
# claude-fable-5 se mantiene como entrada DEFENSIVA: está retirado del
# catálogo (12-jun-2026) pero, si Anthropic restaura el acceso, ya
# queda blindado contra el 400 sin tener que recordar añadirlo.
MODELOS_CLAUDE_SIN_SAMPLING = ("claude-fable-5", "claude-opus-4-8", "claude-opus-4-7")


def modelo_acepta_temperature(modelo: str) -> bool:
    """True si el modelo Claude acepta el parámetro temperature."""
    return not any((modelo or "").startswith(m) for m in MODELOS_CLAUDE_SIN_SAMPLING)


class ClaudeProvider(BaseLLMProvider):
    """Adapter para Anthropic Claude."""

    def __init__(self, api_key: str | None, model: str | None = None, **kwargs):
        super().__init__(api_key, model)
        if api_key:
            try:
                from anthropic import Anthropic
                self._cliente = Anthropic(api_key=api_key)
                self._anthropic_disponible = True
            except ImportError:
                self._anthropic_disponible = False
                self._cliente = None

    def disponible(self) -> bool:
        return getattr(self, "_anthropic_disponible", False) and bool(self.api_key)

    def completar(self, messages: list[dict], temperature: float = 0.75, max_tokens: int = 900, model: str | None = None) -> str:
        if not self._cliente:
            raise Exception("Claude no configurado (instala 'anthropic' o falta api key)")
        modelo = model or self.model or "claude-sonnet-4-6"

        system_prompt = ""
        msgs = []
        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
            else:
                msgs.append({"role": m["role"], "content": m["content"]})

        kwargs_api: dict = {
            "model": modelo, "messages": msgs, "max_tokens": max_tokens,
        }
        # Fable 5 / Opus 4.8 / 4.7 rechazan temperature con 400 — solo
        # se envía en los modelos que lo aceptan (Sonnet, Haiku...).
        if modelo_acepta_temperature(modelo):
            kwargs_api["temperature"] = temperature
        if system_prompt:
            kwargs_api["system"] = system_prompt
        res = self._cliente.messages.create(**kwargs_api)
        usage = getattr(res, "usage", None)
        if usage is not None:
            self._registrar_uso(getattr(usage, "input_tokens", 0),
                                getattr(usage, "output_tokens", 0))
        return res.content[0].text


# FACTORY

def get_provider(provider_id: str, api_key: str, model: str | None = None) -> BaseLLMProvider:
    """Devuelve una instancia del proveedor configurado."""
    info = LLM_PROVIDERS.get(provider_id)
    if not info:
        raise ValueError(f"Proveedor desconocido: {provider_id}. Disponibles: {list(LLM_PROVIDERS.keys())}")

    tipo = info["tipo"]
    modelo_final = model or info.get("model_default")

    if provider_id == "ollama":
        prov = OllamaProvider(api_key=None, model=modelo_final, base_url=info.get("base_url"))
    elif tipo == "openai_compatible":
        prov = OpenAICompatibleProvider(api_key=api_key, model=modelo_final, base_url=info.get("base_url"))
    elif tipo == "google":
        prov = GeminiProvider(api_key=api_key, model=modelo_final)
    elif tipo == "anthropic":
        prov = ClaudeProvider(api_key=api_key, model=modelo_final)
    else:
        raise ValueError(f"Tipo de proveedor desconocido: {tipo}")
    # Para que completar() registre el uso de tokens con la key correcta
    prov.provider_id = provider_id
    return prov


# ALMACENAMIENTO DE API KEYS (keyring + fallback .env)

KEYRING_SERVICE = "GPromptStudio"

def guardar_api_key(provider_id: str, api_key: str) -> bool:
    """Guarda la API key de forma segura (keyring del SO)."""
    if not api_key:
        return False
    try:
        import keyring
        keyring.set_password(KEYRING_SERVICE, f"api_key_{provider_id}", api_key)
        logger.info(f"API key guardada en keyring para {provider_id}")
        return True
    except Exception as e:
        logger.warning(f"keyring no disponible para {provider_id}, usando fallback: {e}")
        return _guardar_keys_fallback(provider_id, api_key)


def _key_valida(valor: str) -> bool:
    """Una key es válida si tiene >= 8 caracteres y no es un placeholder vacío."""
    if not valor:
        return False
    val = valor.strip()
    if len(val) < 8:
        return False
    # Descartar placeholders comunes
    placeholders = {"none", "null", "tu_key_aqui", "your_key_here", "xxx", "..."}
    if val.lower() in placeholders:
        return False
    return True


# Mapa de variables de entorno (compartido, no se redefine en cada llamada)
ENV_VAR_POR_PROVIDER = {
    "deepseek": "DEEPSEEK_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "groq": "GROQ_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "xai": "XAI_API_KEY",
    "fireworks": "FIREWORKS_API_KEY",
    "github_models": "GITHUB_TOKEN",
    "lm_studio": "",  # local, no necesita key
    "perplexity": "PERPLEXITY_API_KEY",
    "togetherai": "TOGETHER_API_KEY",
    # Pollinations es proveedor de IMAGEN (no LLM). Se usa solo para
    # previews en el comparador. Endpoint autenticado:
    # https://gen.pollinations.ai/image/{prompt} con Authorization: Bearer.
    # Sin key cae al endpoint anónimo legacy (image.pollinations.ai)
    # que tiene rate limit estricto.
    "pollinations": "POLLINATIONS_API_KEY",
}


def cargar_api_key(provider_id: str) -> str:
    """Recupera la API key del proveedor con 3 fallbacks robustos:
    1. Sistema operativo (keyring) — almacenamiento seguro
    2. Fichero keys.json en ~/.arquitecto_prompts/
    3. Variable de entorno (cargada del .env del proyecto)

    Si una fuente devuelve un valor inválido (vacío, placeholder, demasiado corto),
    se pasa silenciosamente a la siguiente. Esto evita el bug en el que un keyring
    con entrada vacía rompía el fallback al .env.
    """
    # 1) keyring del SO
    try:
        import keyring
        valor = keyring.get_password(KEYRING_SERVICE, f"api_key_{provider_id}")
        if _key_valida(valor):
            logger.debug(f"Key '{provider_id}' encontrada en keyring del SO")
            return valor.strip()
    except Exception as e:
        logger.debug(f"keyring fallback para {provider_id}: {e}")

    # 2) keys.json local
    try:
        val = _cargar_keys_fallback(provider_id)
        if _key_valida(val):
            logger.debug(f"Key '{provider_id}' encontrada en keys.json")
            return val.strip()
    except Exception as e:
        logger.debug(f"keys.json fallback para {provider_id}: {e}")

    # 3) variable de entorno (.env)
    var_env = ENV_VAR_POR_PROVIDER.get(provider_id, "")
    if var_env:
        valor_env = os.getenv(var_env, "")
        if _key_valida(valor_env):
            logger.debug(f"Key '{provider_id}' encontrada en variable de entorno {var_env}")
            return valor_env.strip()

    return ""


def borrar_api_key(provider_id: str):
    """Elimina la API key guardada."""
    try:
        import keyring
        keyring.delete_password(KEYRING_SERVICE, f"api_key_{provider_id}")
    except Exception as _e:
        logger.debug(f"[silent] {_e}")
    try:
        _borrar_keys_fallback(provider_id)
    except Exception as _e:
        logger.debug(f"[silent] {_e}")


def ubicacion_api_key(provider_id: str) -> str:
    """Indica DÓNDE está guardada la API key sin exponer su valor.

    Devuelve: "keyring" | "keys.json (cifrado)" | "env (.env)" | ""
    Útil para la UI de gestión de keys (saber qué fuente sirve cada una).
    """
    # 1) keyring del SO
    try:
        import keyring
        valor = keyring.get_password(KEYRING_SERVICE, f"api_key_{provider_id}")
        if _key_valida(valor):
            return "keyring"
    except Exception:
        pass
    # 2) keys.json cifrado
    try:
        val = _cargar_keys_fallback(provider_id)
        if _key_valida(val):
            return "keys.json (cifrado)"
    except Exception:
        pass
    # 3) variable de entorno
    var_env = ENV_VAR_POR_PROVIDER.get(provider_id, "")
    if var_env:
        valor_env = os.getenv(var_env, "")
        if _key_valida(valor_env):
            return "env (.env)"
    return ""
def _ruta_keys_fallback() -> str:
    from config import ARCHIVOS
    ruta = str(ARCHIVOS["keys"])
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    return ruta


def _obtener_clave_cifrado() -> bytes:
    """Deriva una clave de cifrado del hardware local."""
    import hashlib
    try:
        import uuid
        mac = uuid.getnode()
        usuario = os.getenv("USERNAME") or os.getenv("USER") or "gprompt"
        raw = f"{mac}_{usuario}_GPromptStudio_v1".encode()
        return hashlib.sha256(raw).digest()
    except Exception:
        import hashlib
        clave_fija = b"GPromptStudio_v1_key_backup_2024"
        return hashlib.sha256(clave_fija).digest()


def _cifrar_aes(texto: str, clave: bytes) -> str:
    """Cifra texto con AES-256-CBC. Devuelve base64."""
    import base64
    import os

    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(clave), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padded = texto.encode() + b" " * (16 - len(texto.encode()) % 16)
    ct = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(iv + ct).decode()


def _descifrar_aes(texto_cifrado: str, clave: bytes) -> str:
    """Descifra texto AES-256-CBC. Devuelve texto plano."""
    import base64

    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    try:
        data = base64.b64decode(texto_cifrado.encode())
        iv, ct = data[:16], data[16:]
        cipher = Cipher(algorithms.AES(clave), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        pt = decryptor.update(ct) + decryptor.finalize()
        return pt.rstrip(b" ").decode()
    except Exception:
        return ""


def _cargar_dict_fallback() -> dict:
    ruta = _ruta_keys_fallback()
    if not os.path.exists(ruta):
        return {}
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
            if not contenido:
                return {}
            datos = json.loads(contenido)
            if isinstance(datos, dict) and "encrypted" in datos:
                clave = _obtener_clave_cifrado()
                descifrado = {}
                for k, v in datos.get("keys", {}).items():
                    descifrado[k] = _descifrar_aes(v, clave)
                return descifrado
            return datos
    except Exception:
        return {}


def _escribir_dict_fallback(d: dict):
    ruta = _ruta_keys_fallback()
    tmp = ruta + ".tmp"
    clave = _obtener_clave_cifrado()
    cifrado = {}
    for k, v in d.items():
        cifrado[k] = _cifrar_aes(v, clave)
    datos = {"version": 1, "encrypted": True, "keys": cifrado}
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, ruta)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def _guardar_keys_fallback(provider_id: str, api_key: str) -> bool:
    d = _cargar_dict_fallback()
    d[provider_id] = api_key
    _escribir_dict_fallback(d)
    return True


def _cargar_keys_fallback(provider_id: str) -> str:
    d = _cargar_dict_fallback()
    return d.get(provider_id, "")


def _borrar_keys_fallback(provider_id: str):
    d = _cargar_dict_fallback()
    d.pop(provider_id, None)
    _escribir_dict_fallback(d)


# CONTENEDOR PRINCIPAL

class APIClients:
    """Contenedor de proveedores LLM + Vision."""

    def __init__(self, provider_activo: str | None = None, vision_provider: str | None = None):
        self.provider_activo_id = provider_activo or self._cargar_provider_default()
        self.vision_provider_id = vision_provider or "gemini"

        self.api_keys: dict[str, str] = {}
        configurados = []
        for pid in LLM_PROVIDERS.keys():
            key = cargar_api_key(pid)
            self.api_keys[pid] = key
            if key:
                configurados.append(pid)
        if configurados:
            logger.info(f"API keys cargadas para: {', '.join(configurados)}")
        else:
            logger.warning("No se encontraron API keys para ningún proveedor.")

        gkey = self.api_keys.get("gemini", "")
        if gkey:
            logger.info("Gemini key cargada: [presente]")

        # Modelo elegido por proveedor (persistido en active_models.json).
        # Si no hay elección guardada, cada provider usa su model_default.
        self.modelos_activos: dict[str, str] = self._cargar_modelos_activos()

        self.providers: dict[str, BaseLLMProvider | None] = {}
        for pid, info in LLM_PROVIDERS.items():
            try:
                self.providers[pid] = get_provider(
                    pid, self.api_keys.get(pid, ""),
                    model=self.modelos_activos.get(pid))
            except Exception as e:
                logger.error(f"Error creando provider {pid}: {e}")
                self.providers[pid] = None

        # Compatibilidad con código antiguo
        self.deepseek = self._cliente_raw("deepseek")
        self.openrouter = self._cliente_raw("openrouter")
        self.gemini = self._cliente_raw_gemini()
        self.ollama = self._cliente_raw("ollama")

        self.deepseek_key = self.api_keys.get("deepseek", "")
        self.gemini_key = self.api_keys.get("gemini", "")
        self.openrouter_key = self.api_keys.get("openrouter", "")

        self.error = None
        active = self.get_active_provider()
        if not active or not active.disponible():
            # El provider activo (de preferencias o default) no tiene key.
            # Si HAY otro provider configurado, auto-cambiar a él en lugar
            # de bloquear la app. Solo fallar si NADIE tiene key.
            fallback_id = next(
                (pid for pid, prov in self.providers.items()
                 if prov is not None and prov.disponible()),
                None,
            )
            if fallback_id:
                old_id = self.provider_activo_id
                self.provider_activo_id = fallback_id
                logger.info(
                    f"Auto-switch: '{old_id}' sin key → usando '{fallback_id}' "
                    "(tiene key configurada)"
                )
            else:
                self.error = (
                    "No hay ninguna API key configurada. "
                    "Abre Ajustes para añadir al menos una."
                )

    def _cliente_raw(self, provider_id: str):
        info = LLM_PROVIDERS.get(provider_id, {})
        if info.get("tipo") != "openai_compatible" or not OPENAI_DISPONIBLE:
            return None
        api_key = self.api_keys.get(provider_id, "")
        return OpenAI(api_key=api_key or "sin-key", base_url=info.get("base_url", ""))

    def _cliente_raw_gemini(self):
        if not GEMINI_DISPONIBLE:
            return None
        key = self.api_keys.get("gemini", "")
        if not key:
            return None
        try:
            return google_genai.Client(api_key=key)
        except Exception:
            return None

    def _cargar_provider_default(self) -> str:
        try:
            from config import ARCHIVOS
            ruta = str(ARCHIVOS["active_provider"])
            if os.path.exists(ruta):
                with open(ruta, "r", encoding="utf-8") as f:
                    pid = f.read().strip()
                if pid in LLM_PROVIDERS:
                    return pid
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        return "deepseek"

    def cambiar_provider(self, provider_id: str) -> bool:
        if provider_id not in LLM_PROVIDERS:
            return False
        self.provider_activo_id = provider_id
        try:
            from config import ARCHIVOS, CARPETA_APP
            os.makedirs(str(CARPETA_APP), exist_ok=True)
            ruta = str(ARCHIVOS["active_provider"])
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(provider_id)
        except Exception as _e:
            logger.debug(f"[silent] {_e}")
        return True

    def get_active_provider(self) -> BaseLLMProvider | None:
        return self.providers.get(self.provider_activo_id)

    # ── Selección de modelo por proveedor (sesión 19 round 13) ────────

    def _cargar_modelos_activos(self) -> dict:
        """Lee active_models.json: {provider_id: modelo_elegido}."""
        try:
            from config import ARCHIVOS
            ruta = ARCHIVOS.get("active_models")
            if ruta and os.path.exists(str(ruta)):
                with open(str(ruta), encoding="utf-8") as f:
                    datos = json.load(f)
                if isinstance(datos, dict):
                    return {k: str(v) for k, v in datos.items() if v}
        except Exception as e:
            logger.debug(f"[silent] modelos activos: {e}")
        return {}

    def set_model(self, provider_id: str, modelo: str) -> bool:
        """Cambia el modelo de un proveedor y lo persiste.

        Reconstruye la instancia del provider con el modelo nuevo para
        que la siguiente llamada ya lo use."""
        modelo = (modelo or "").strip()
        if not modelo or provider_id not in LLM_PROVIDERS:
            return False
        self.modelos_activos[provider_id] = modelo
        try:
            self.providers[provider_id] = get_provider(
                provider_id, self.api_keys.get(provider_id, ""), model=modelo)
        except Exception as e:
            logger.error(f"Error recreando provider {provider_id} con {modelo}: {e}")
            return False
        try:
            from config import ARCHIVOS, CARPETA_APP
            os.makedirs(str(CARPETA_APP), exist_ok=True)
            with open(str(ARCHIVOS["active_models"]), "w", encoding="utf-8") as f:
                json.dump(self.modelos_activos, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"[silent] persistir modelo: {e}")
        return True

    def get_model(self, provider_id: str) -> str:
        """Modelo actualmente activo de un proveedor."""
        prov = self.providers.get(provider_id)
        if prov is not None and prov.model:
            return prov.model
        return (self.modelos_activos.get(provider_id)
                or LLM_PROVIDERS.get(provider_id, {}).get("model_default", ""))

    def actualizar_key(self, provider_id: str, nueva_key: str):
        guardar_api_key(provider_id, nueva_key)
        self.api_keys[provider_id] = nueva_key
        try:
            self.providers[provider_id] = get_provider(provider_id, nueva_key)
        except Exception:
            self.providers[provider_id] = None
        if provider_id == "deepseek":
            self.deepseek = self._cliente_raw("deepseek")
            self.deepseek_key = nueva_key
        elif provider_id == "openrouter":
            self.openrouter = self._cliente_raw("openrouter")
            self.openrouter_key = nueva_key
        elif provider_id == "gemini":
            self.gemini = self._cliente_raw_gemini()
            self.gemini_key = nueva_key

    def has_openrouter(self) -> bool:
        return bool(self.api_keys.get("openrouter"))

    def has_gemini(self) -> bool:
        return self.gemini is not None

    def listar_providers_configurados(self) -> list[str]:
        out = []
        for pid in LLM_PROVIDERS.keys():
            p = self.providers.get(pid)
            if p and p.disponible():
                out.append(pid)
        return out
