"""
G-Prompt Studio v1.0 — Clientes API (Multi-LLM con arquitectura de adapters).

Cada proveedor implementa la misma interfaz BaseLLMProvider:
  - completar(messages, temperature, max_tokens) -> str
  - disponible() -> bool

Para añadir un proveedor nuevo solo hay que crear su clase aquí.
"""
import os
import json
import logging
import urllib.request
from openai import OpenAI
from typing import Optional

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
        "descripcion": "Calidad excelente para creatividad. Pago (~€2.40/1M).",
        "url_obtener_key": "https://console.anthropic.com/settings/keys",
        "tipo": "anthropic",
        "model_default": "claude-sonnet-4-5-20250929",
        "is_paid": True,
    },
    "deepseek": {
        "name": "DeepSeek V3",
        "label": "🥈 DeepSeek V3",
        "descripcion": "Económico (~€0.14/1M tokens). Bueno para creatividad, robusto.",
        "url_obtener_key": "https://platform.deepseek.com/api_keys",
        "tipo": "openai_compatible",
        "base_url": "https://api.deepseek.com",
        "model_default": "deepseek-chat",
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
        "is_paid": True,
    },
    "gemini": {
        "name": "Google Gemini",
        "label": "🏆 Google Gemini (gratis)",
        "descripcion": "Gratis hasta 15rpm. Bueno para visión y prompts.",
        "url_obtener_key": "https://aistudio.google.com/apikey",
        "tipo": "google",
        "model_default": "gemini-2.5-flash",
        "is_paid": False,
    },
    "github_models": {
        "name": "GitHub Models",
        "label": "🏆 GitHub Models (gratis)",
        "descripcion": "Gratis con cuenta GitHub. Acceso a OpenAI/Claude/Llama. Límite generoso.",
        "url_obtener_key": "https://github.com/settings/tokens",
        "tipo": "openai_compatible",
        "base_url": "https://models.inference.ai.azure.com",
        "model_default": "gpt-4o-mini",
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
        "is_paid": True,
    },
    "ollama": {
        "name": "Ollama (local)",
        "label": "🏆 Ollama local (sin internet)",
        "descripcion": "Sin internet, sin coste. Requiere instalar Ollama y descargar modelo.",
        "url_obtener_key": "https://ollama.com/download",
        "tipo": "openai_compatible",
        "base_url": "http://localhost:11434/v1",
        "model_default": "llama3.1",
        "is_paid": False,
    },
    "openai": {
        "name": "OpenAI GPT-4o",
        "label": "💎 OpenAI GPT-4o",
        "descripcion": "Pago (~€2.40/1M). Calidad alta, requiere cuenta de pago.",
        "url_obtener_key": "https://platform.openai.com/api-keys",
        "tipo": "openai_compatible",
        "base_url": "https://api.openai.com/v1",
        "model_default": "gpt-4o",
        "is_paid": True,
    },
    "openrouter": {
        "name": "OpenRouter",
        "label": "🥈 OpenRouter (100+ modelos)",
        "descripcion": "Acceso a OpenAI/Claude/Gemini/Llama y más con UNA sola key.",
        "url_obtener_key": "https://openrouter.ai/keys",
        "tipo": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "model_default": "deepseek/deepseek-chat",
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
        "is_paid": True,
    },
    "xai": {
        "name": "xAI Grok",
        "label": "💎 xAI Grok",
        "descripcion": "Modelos de xAI (Elon Musk). Calidad alta.",
        "url_obtener_key": "https://console.x.ai/",
        "tipo": "openai_compatible",
        "base_url": "https://api.x.ai/v1",
        "model_default": "grok-2-1212",
        "is_paid": True,
    },
}


# INTERFAZ BASE

class BaseLLMProvider:
    """Interfaz que todos los proveedores deben implementar."""

    def __init__(self, api_key: str | None, model: str | None = None, **kwargs):
        self.api_key = api_key
        self.model = model
        self._cliente = None

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
        return res.choices[0].message.content


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

        cliente = google_genai.Client(api_key=self.api_key)

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

        raw = response.text or ""
        markers = [
            "<system-reminder>", "<system-reminder",
            "Your operational mode", "You are no longer in read-only mode",
            "You are permitted to make file changes", "You are a helpful assistant",
            "You are Claude", "You are an AI"
        ]
        for marker in markers:
            while marker in raw:
                raw = raw.replace(marker, "")
        return raw.strip()


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
        modelo = model or self.model or "claude-sonnet-4-5-20250929"

        system_prompt = ""
        msgs = []
        for m in messages:
            if m["role"] == "system":
                system_prompt = m["content"]
            else:
                msgs.append({"role": m["role"], "content": m["content"]})

        kwargs_api: dict = {
            "model": modelo, "messages": msgs, "max_tokens": max_tokens, "temperature": temperature,
        }
        if system_prompt:
            kwargs_api["system"] = system_prompt
        res = self._cliente.messages.create(**kwargs_api)
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
        return OllamaProvider(api_key=None, model=modelo_final, base_url=info.get("base_url"))
    elif tipo == "openai_compatible":
        return OpenAICompatibleProvider(api_key=api_key, model=modelo_final, base_url=info.get("base_url"))
    elif tipo == "google":
        return GeminiProvider(api_key=api_key, model=modelo_final)
    elif tipo == "anthropic":
        return ClaudeProvider(api_key=api_key, model=modelo_final)
    else:
        raise ValueError(f"Tipo de proveedor desconocido: {tipo}")


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
    except Exception:
        pass
    try:
        _borrar_keys_fallback(provider_id)
    except Exception:
        pass


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
    import base64, os
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(clave), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padded = texto.encode() + b" " * (16 - len(texto.encode()) % 16)
    ct = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(iv + ct).decode()


def _descifrar_aes(texto_cifrado: str, clave: bytes) -> str:
    """Descifra texto AES-256-CBC. Devuelve texto plano."""
    import base64
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

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

        # Log de diagnóstico para Gemini (key enmascarada por seguridad)
        gkey = self.api_keys.get("gemini", "")
        if gkey:
            masked = f"{gkey[:6]}...{gkey[-4:]}" if len(gkey) > 12 else "(corta)"
            logger.info(f"Gemini key cargada: {masked} (longitud: {len(gkey)})")

        self.providers: dict[str, BaseLLMProvider | None] = {}
        for pid, info in LLM_PROVIDERS.items():
            try:
                self.providers[pid] = get_provider(pid, self.api_keys.get(pid, ""))
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
            info = LLM_PROVIDERS.get(self.provider_activo_id, {})
            self.error = (f"No hay API key configurada para {info.get('name', self.provider_activo_id)}. "
                          f"Abre Ajustes para configurarla.")

    def _cliente_raw(self, provider_id: str):
        info = LLM_PROVIDERS.get(provider_id, {})
        api_key = self.api_keys.get(provider_id, "")
        return OpenAI(api_key=api_key or "sin-key", base_url=info.get("base_url", "")) if info.get("tipo") == "openai_compatible" else None

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
        except Exception:
            pass
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
        except Exception:
            pass
        return True

    def get_active_provider(self) -> BaseLLMProvider | None:
        return self.providers.get(self.provider_activo_id)

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
