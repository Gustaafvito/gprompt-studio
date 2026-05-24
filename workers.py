"""
G-Prompt Studio v1.0 — Workers IA (Multi-LLM + Visión).

Refactor v1.0:
- Eliminado parámetro modelo_llm (ya redundante con patrón Provider).
- Logging estructurado en errores.
- VisionChain con timeout configurable.
"""
import os

try:
    from dotenv import load_dotenv
    _proj_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv()
    load_dotenv(_proj_env, override=False)
except ImportError:
    pass
import base64
import io
import json as _json
import logging
import re
import time
import urllib.request
from typing import TYPE_CHECKING, Callable, Optional

from google.genai import types as genai_types

from config import (
    MAX_HIST_IA,
    MODELOS_GEMINI_CANDIDATOS,
    MODELOS_OLLAMA_VISION,
    MODELOS_OPENROUTER_VISION,
)
from prompts import VISION_SYSTEM_PROMPT

if TYPE_CHECKING:
    from api_clients import APIClients

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────

def contar_tokens_aprox(texto: str) -> int:
    """Estimación rápida: ~1 token por cada 4 caracteres."""
    if not texto:
        return 0
    return max(1, len(texto) // 4)


def limpiar_marcadores(texto: str) -> str:
    """Elimina marcadores markdown **, __ del texto."""
    return texto.replace("**", "").replace("__", "")


def parsear_ideas(texto: str) -> list[str]:
    """Extrae 3 ideas de una respuesta numerada del LLM."""
    ideas = []
    modo_prompt = False
    for linea in texto.strip().splitlines():
        linea = linea.strip()
        m = re.match(r'^[1-3][.)]\s*(.+)', linea)
        if m:
            ideas.append(m.group(1).strip())
            modo_prompt = False
        elif not ideas and not modo_prompt:
            m2 = re.match(r'^PROMPT\s*[1-3]\s*[:.\-]\s*(.+)', linea, re.IGNORECASE)
            if m2:
                ideas.append(m2.group(1).strip())
                modo_prompt = True
        elif modo_prompt:
            m3 = re.match(r'^PROMPT\s*[1-3]\s*[:.\-]\s*(.+)', linea, re.IGNORECASE)
            if m3:
                ideas.append(m3.group(1).strip())
        if len(ideas) == 3:
            break
    return ideas


def detectar_idioma_es(texto: str) -> bool:
    """Heurístico: devuelve True si el texto parece español."""
    palabras_es = {
        "una", "un", "chica", "chico", "mujer", "hombre", "con", "en",
        "de", "del", "al", "que", "por", "para", "como", "sobre",
        "estilo", "fondo", "luz", "colores", "oscuro", "brillante",
        "anime", "foto", "imagen", "escena", "retrato", "paisaje",
    }
    palabras = set(texto.lower().split())
    return len(palabras & palabras_es) >= 2


# ── Worker Multi-LLM ──────────────────────────────────────────────

class DeepSeekWorker:
    """
    Gestiona las peticiones a los distintos LLMs mediante el patrón Provider.

    El nombre "DeepSeekWorker" se conserva por compatibilidad histórica, pero
    en realidad delega en cualquier proveedor activo (DeepSeek, Claude, Gemini,
    OpenAI, Groq, Ollama, etc.) configurado en self.clients.
    """

    def __init__(self, clients: "APIClients"):
        self.clients = clients
        self.historial: list[dict[str, str]] = []

    def reiniciar(self, system_prompt: str):
        """Reinicia el historial de conversación con un nuevo system prompt."""
        self.historial = [{"role": "system", "content": system_prompt}]

    def _get_provider(self):
        """Obtiene el proveedor activo configurado."""
        provider = self.clients.get_active_provider() if hasattr(self.clients, "get_active_provider") else None
        if not provider or not provider.disponible():
            raise RuntimeError(
                "No hay proveedor LLM configurado. Abre Ajustes (🔑) para configurar una API key."
            )
        return provider

    def _escalar_max_tokens(self, max_tokens: int) -> int:
        """Ajusta max_tokens según el provider activo.

        Algunos modelos (Gemini, Claude) usan tokenizadores donde cada token
        cubre menos texto en inglés que DeepSeek/GPT, por lo que necesitan
        más presupuesto para producir la misma salida.
        """
        try:
            pid = self.clients.provider_activo_id if hasattr(self.clients, "provider_activo_id") else ""
        except Exception:
            return max_tokens
        # Multiplicadores empíricos por provider
        multiplicadores = {
            "gemini": 2.5,    # Gemini 2.5 Flash necesita ~2.5x más tokens
            "claude": 1.8,    # Claude también algo más
            "openai": 1.0,    # GPT base
            "deepseek": 1.0,  # Referencia
        }
        mult = multiplicadores.get(pid, 1.0)
        return int(max_tokens * mult)

    def generar(self, peticion: str, temperature: float = 0.75, max_tokens: int = 900, **kwargs) -> str:
        """
        Envía petición al provider activo manteniendo historial.
        Si falla, limpia la última entrada del historial para no contaminar.

        Retry automático con backoff exponencial (3 intentos).
        max_tokens se escala según provider activo (Gemini necesita más).
        **kwargs se ignora (retrocompat: el provider activo se obtiene
        siempre desde self.clients.get_active_provider()).
        """
        import time

        self.historial.append({"role": "user", "content": peticion})
        max_tokens_escalado = self._escalar_max_tokens(max_tokens)

        # Retry con backoff exponencial (3 intentos)
        max_reintentos = 3
        delay_base = 1.0  # segundos

        for intento in range(max_reintentos):
            try:
                provider = self._get_provider()
                texto = provider.completar(self.historial, temperature=temperature, max_tokens=max_tokens_escalado)

                self.historial.append({"role": "assistant", "content": texto})

                # Truncar historial si crece demasiado (mantener system prompt)
                if len(self.historial) > MAX_HIST_IA:
                    self.historial[1:] = self.historial[-(MAX_HIST_IA - 1):]
                return texto

            except Exception as e:
                if intento < max_reintentos - 1:
                    delay = delay_base * (2 ** intento)  # 1s, 2s, 4s
                    logger.warning(f"DeepSeekWorker.generar() intento {intento+1} falló: {e}. Reintentando en {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"DeepSeekWorker.generar() falló después de {max_reintentos} intentos: {e}")
                    # Eliminar la petición fallida del historial
                    if self.historial and self.historial[-1]["role"] == "user":
                        self.historial.pop()
                    raise

    def generar_batch(self, system_content: str, peticion: str, **kwargs) -> str:
        """Generación batch sin historial (one-shot). max_tokens se
        escala según provider. **kwargs se ignora (retrocompat)."""
        msgs = [
            {"role": "system", "content": system_content},
            {"role": "user",   "content": peticion},
        ]
        provider = self._get_provider()
        max_tokens_escalado = self._escalar_max_tokens(6000)
        return provider.completar(msgs, temperature=0.8, max_tokens=max_tokens_escalado)

    def traducir(self, texto_es: str, **kwargs) -> str:
        """Traduce ES → EN para prompts de IA. Devuelve original si falla."""
        peticion_trad = (
            "Translate this to English for an AI image/video prompt. "
            "Keep it concise, preserve all descriptive details. "
            "Return ONLY the translation, no explanations: " + texto_es
        )
        msgs = [{"role": "user", "content": peticion_trad}]

        try:
            provider = self._get_provider()
            return provider.completar(msgs, temperature=0.2, max_tokens=200).strip()
        except Exception as e:
            logger.warning(f"Traducción ES→EN falló, devolviendo original: {e}")
            return texto_es

    def traducir_a_espanol(self, texto_en: str, **kwargs) -> str:
        """Traduce EN → ES. Devuelve original si falla."""
        peticion = (
            "Traduce este prompt de IA al español de forma natural y clara. "
            "Devuelve SOLO la traducción, sin explicaciones: " + texto_en
        )
        msgs = [{"role": "user", "content": peticion}]
        try:
            provider = self._get_provider()
            return provider.completar(msgs, temperature=0.2, max_tokens=5000).strip()
        except Exception as e:
            logger.warning(f"Traducción EN→ES falló, devolviendo original: {e}")
            return texto_en


# ── Cadena de Visión ──────────────────────────────────────────────

class VisionChain:
    """
    Cadena de fallback para análisis de imagen: Gemini → Ollama → OpenRouter.

    Si un proveedor falla con 429 (cuota), pasa al siguiente.
    Si falla con error distinto, lanza excepción.
    """

    def __init__(self, clients: "APIClients"):
        self.clients = clients
        self.proveedores: list[tuple[str, Callable]] = []
        if clients.has_gemini():
            self.proveedores.append(("Gemini", self._describir_gemini))
        # Ollama se añade siempre, pero la función _describir_ollama hace check
        # interno; si no está corriendo, lanza excepción que la cadena maneja
        # como fallback al siguiente. Adicionalmente, al inicio comprobamos en
        # background si Ollama está disponible para log informativo.
        if self._ollama_disponible():
            self.proveedores.append(("Ollama", self._describir_ollama))
            logger.info("VisionChain: Ollama disponible (será fallback)")
        else:
            logger.info("VisionChain: Ollama no detectado (se omite del fallback)")
        if clients.has_openrouter():
            self.proveedores.append(("OpenRouter", self._describir_openrouter))

        if not self.proveedores:
            logger.warning(
                "VisionChain: sin proveedores de visión disponibles. "
                "Configura Gemini, OpenRouter o instala Ollama para usar ADN Visual."
            )
        else:
            nombres = ", ".join(n for n, _ in self.proveedores)
            logger.info(f"VisionChain: cadena activa → {nombres}")

    def describir(
        self,
        imagen_pil,
        modo: str,
        on_status: Callable[[str], None] | None = None
    ) -> tuple[str, str]:
        """
        Describe una imagen usando la cadena de fallback.
        Devuelve (descripcion, motor_usado) o lanza excepción.
        """
        prompt_v = self._prompt_vision(modo)
        ultimo_error = None

        for nombre, fn in self.proveedores:
            if on_status:
                on_status(f"👁 Probando {nombre}...")
            try:
                desc, motor = fn(imagen_pil, prompt_v)
                if desc and len(desc) >= 5:
                    return desc, motor
            except Exception as e:
                ultimo_error = e
                es_429 = any(x in str(e).lower() for x in ["429", "quota", "resource_exhausted"])
                logger.warning(f"VisionChain[{nombre}] falló: {e} (rate-limited={es_429})")
                if not es_429 and nombre == "Gemini":
                    raise
                continue

        if ultimo_error:
            raise ultimo_error
        raise RuntimeError("Sin proveedores de visión disponibles.")

    def _prompt_vision(self, modo: str) -> str:
        if modo == "video":
            return (
                "Eres una herramienta de análisis visual detallado para generación de vídeo IA. "
                "Describe esta imagen en ESPAÑOL con 100-150 palabras. Incluye TODO esto:\n"
                "- Sujeto principal: apariencia, ropa, pelo, expresión, posición corporal\n"
                "- Acción o pose que realiza el sujeto\n"
                "- Entorno/fondo: escenario, objetos, profundidad\n"
                "- Iluminación: tipo, dirección, temperatura de color\n"
                "- Paleta de colores: colores dominantes y de acento\n"
                "- Ambiente/atmósfera\n"
                "- Ángulo de cámara y encuadre\n"
                "Escribe SOLO la descripción, sin etiquetas ni explicaciones."
            )
        return (
            "Eres una herramienta de análisis visual detallado para generación de imágenes IA. "
            "Describe esta imagen en ESPAÑOL con 100-150 palabras. Incluye TODO esto:\n"
            "- Sujeto principal: apariencia, ropa, color/estilo de pelo, expresión, pose\n"
            "- Fondo/entorno: escenario, objetos, profundidad de campo\n"
            "- Iluminación: tipo (suave/dura/contraluz), dirección, sombras\n"
            "- Paleta de colores: colores dominantes y de acento\n"
            "- Estilo artístico: fotorrealista, anime, pintura, 3D, etc.\n"
            "- Composición: ángulo de cámara, encuadre, perspectiva\n"
            "Escribe SOLO la descripción, sin etiquetas ni explicaciones."
        )

    # ADN VISUAL — Análisis estructurado JSON

    # Aquí solo está la lógica de la cadena de fallback (Gemini → Ollama → OpenRouter).

    def analizar_adn(
        self,
        imagen_pil,
        on_status: Callable[[str], None] | None = None
    ) -> tuple[dict, str]:
        """
        Analiza imagen y devuelve ADN estructurado en JSON.
        Returns: (adn_dict, motor_usado)
        """
        ultimo_error = None

        for nombre, fn in self.proveedores:
            if on_status:
                on_status(f"🧬 Extrayendo ADN con {nombre}...")
            try:
                desc, motor = fn(imagen_pil, VISION_SYSTEM_PROMPT)
                if desc and len(desc) >= 10:
                    # Parsear JSON
                    import json
                    import re
                    # Limpiar wrappers comunes
                    cleaned = desc.strip()

                    # Intentar parsear, si falla por JSON incompleto o múltiples JSONs, intentar arreglar
                    try:
                        adn = json.loads(cleaned)
                    except json.JSONDecodeError as je:
                        error_msg = str(je)
                        partial = cleaned

                        # Si hay "Extra data" significa que hay más de un JSON - tomar solo el primero
                        if "Extra data" in error_msg:
                            # Encontrar el primer JSON completo
                            try:
                                adn = json.loads(partial[:je.pos])
                            except:
                                # Si falla, buscar primer { y intentar cerrar correctamente
                                match = re.search(r"[\[{]", partial)
                                if match:
                                    partial = partial[match.start():]
                                    open_braces = partial.count("{") - partial.count("}")
                                    open_brackets = partial.count("[") - partial.count("]")
                                    partial += "}" * max(0, open_braces)
                                    partial += "]" * max(0, open_brackets)
                                    adn = json.loads(partial)

                        # Si es "Unterminated string" o similar, intentar completar el JSON
                        elif "Unterminated" in error_msg or "expecting" in error_msg:
                            open_braces = partial.count("{") - partial.count("}")
                            open_brackets = partial.count("[") - partial.count("]")
                            partial += "}" * max(0, open_braces)
                            partial += "]" * max(0, open_brackets)
                            adn = json.loads(partial)
                        else:
                            raise je

                    return adn, motor
            except Exception as e:
                ultimo_error = e
                logger.warning(f"VisionChain ADN[{nombre}] falló: {e}")
                if "429" not in str(e).lower() and nombre == "Gemini":
                    raise
                continue

        if ultimo_error:
            raise ultimo_error
        raise RuntimeError("Sin proveedores de visión disponibles.")

    # ── Gemini ────────────────────────────────────────────────────

    def _modelos_gemini_disponibles(self) -> list[str]:
        try:
            todos = list(self.clients.gemini.models.list())
            nombres = {m.name.split("/")[-1] for m in todos}
            disponibles = [m for m in MODELOS_GEMINI_CANDIDATOS if m in nombres]
            return disponibles if disponibles else MODELOS_GEMINI_CANDIDATOS
        except Exception:
            return MODELOS_GEMINI_CANDIDATOS

    def _describir_gemini(self, imagen_pil, prompt_v: str) -> tuple[str, str]:
        buf = io.BytesIO()
        imagen_pil.save(buf, format="JPEG", quality=90)
        img_bytes = buf.getvalue()

        # Buscar key en este orden: cliente preexistente → keyring/keys.json → .env
        # Esto evita que la visión falle si la key vive en keyring pero no en .env.
        client = getattr(self.clients, "gemini", None)
        if client is None:
            api_key = ""
            try:
                # Sistema centralizado de keys (keyring → keys.json → variable env)
                from api_clients import cargar_api_key
                api_key = cargar_api_key("gemini")
            except Exception:
                api_key = ""
            if not api_key:
                api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                raise RuntimeError("No hay API key de Gemini configurada.")
            import google.genai as genai
            client = genai.Client(api_key=api_key)

        modelos = self._modelos_gemini_disponibles()
        ultimo_error = None

        for modelo in modelos:
            for intento in range(2):
                try:
                    r = client.models.generate_content(
                        model=modelo,
                        contents=[
                            genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                            genai_types.Part.from_text(text=prompt_v),
                        ],
                        config=genai_types.GenerateContentConfig(
                            temperature=0, max_output_tokens=32000
                        ),
                    )
                    desc = r.text.strip().strip("'\"\n ")
                    if desc and len(desc) >= 5:
                        return desc, f"Gemini/{modelo}"
                except Exception as e:
                    ultimo_error = e
                    es_429 = any(x in str(e).lower() for x in ["429", "quota", "resource_exhausted"])
                    if es_429 and intento == 0:
                        time.sleep(5)
                    elif es_429:
                        break
                    else:
                        raise
        raise ultimo_error or RuntimeError("Gemini: sin respuesta válida.")

    # ── Ollama ────────────────────────────────────────────────────

    def _ollama_disponible(self) -> bool:
        try:
            urllib.request.urlopen("http://localhost:11434", timeout=2)
            return True
        except Exception:
            return False

    def _modelos_ollama_instalados(self) -> list[str]:
        try:
            with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
                data = _json.loads(r.read())
            nombres = {m["name"].split(":")[0] for m in data.get("models", [])}
            return [m for m in MODELOS_OLLAMA_VISION if m.split(":")[0] in nombres]
        except Exception:
            return []

    def _describir_ollama(self, imagen_pil, prompt_v: str) -> tuple[str, str]:
        if not self._ollama_disponible():
            raise RuntimeError("Ollama no disponible.")
        modelos = self._modelos_ollama_instalados()
        if not modelos:
            raise RuntimeError("Ollama sin modelos de visión instalados.")

        buf = io.BytesIO()
        imagen_pil.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()
        ultimo_error = None

        for modelo in modelos:
            try:
                res = self.clients.ollama.chat.completions.create(
                    model=modelo,
                    messages=[{"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                        {"type": "text", "text": prompt_v},
                    ]}],
                    max_tokens=1500, temperature=0, timeout=90,
                )
                desc = res.choices[0].message.content.strip().strip("'\"\n ")
                if desc and len(desc) >= 5:
                    return desc, f"Ollama/{modelo}"
            except Exception as e:
                ultimo_error = e
                continue
        raise ultimo_error or RuntimeError("Ollama: sin respuesta válida.")

    # ── OpenRouter ────────────────────────────────────────────────

    def _describir_openrouter(self, imagen_pil, prompt_v: str) -> tuple[str, str]:
        buf = io.BytesIO()
        imagen_pil.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()
        ultimo_error = None

        for modelo in MODELOS_OPENROUTER_VISION:
            try:
                res = self.clients.openrouter.chat.completions.create(
                    model=modelo,
                    messages=[{"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                        {"type": "text", "text": prompt_v},
                    ]}],
                    max_tokens=250, temperature=0.1,
                )
                desc = res.choices[0].message.content.strip().strip("'\"\n ")
                if desc and len(desc) >= 5:
                    return desc, f"OpenRouter/{modelo.split('/')[1]}"
            except Exception as e:
                ultimo_error = e
                continue
        raise ultimo_error or RuntimeError("OpenRouter: sin respuesta válida.")
