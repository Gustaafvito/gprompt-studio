"""
G-Prompt Studio v1.0 — Clientes API (Multi-LLM con arquitectura de adapters).

Cada proveedor implementa la misma interfaz BaseLLMProvider:
  - completar(messages, temperature, max_tokens) -> str
  - disponible() -> bool

Para añadir un proveedor nuevo solo hay que crear su clase aquí.
"""
import json
import time
import logging
import os
import re
import urllib.request
import urllib.parse
import socket

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
        # Actualizado el 06-sep-2026 a la familia Claude 5 y VERIFICADO ese
        # mismo día contra la API con una key real: los tres modelos de la
        # familia 5 responden y rechazan `temperature` con 400 (ver
        # MODELOS_CLAUDE_SIN_SAMPLING). Se conserva la generación 4.x debajo
        # por si una key antigua no alcanza la 5.
        "model_default": "claude-sonnet-5",
        "modelos": [
            "claude-fable-5-1",    # tope de gama ($10/$50)
            "claude-opus-5",       # Opus actual ($5/$25)
            "claude-sonnet-5",     # equilibrio ($2/$10) — default
            "claude-haiku-4-5",    # rápido y barato ($1/$5)
            "claude-opus-4-8",     # generación anterior ($5/$25)
            "claude-sonnet-4-6",   # ($3/$15)
        ],
        "is_paid": True,
    },
    "deepseek": {
        "name": "DeepSeek V4",
        "label": "🥈 DeepSeek V4",
        "descripcion": "Económico. Flash barato (~$0.14/1M) · Pro más potente (~$0.44/1M). Bueno para creatividad, robusto.",
        "url_obtener_key": "https://platform.deepseek.com/api_keys",
        "tipo": "openai_compatible",
        "base_url": "https://api.deepseek.com",
        # IDs V4 (los legacy deepseek-chat/deepseek-reasoner se deprecan el
        # 2026-07-24). Flash = barato y rápido; Pro = 1.6T params, mejor en
        # razonamiento/tareas complejas (~3x el precio).
        "model_default": "deepseek-v4-flash",
        "modelos": ["deepseek-v4-flash", "deepseek-v4-pro"],
        "is_paid": True,
    },
    "fireworks": {
        "name": "Fireworks AI",
        "label": "💎 Fireworks AI",
        "descripcion": "Inferencia ultrarrápida con modelos open-source. Buena relación calidad/precio.",
        "url_obtener_key": "https://fireworks.ai/api-keys",
        "tipo": "openai_compatible",
        "base_url": "https://api.fireworks.ai/inference/v1",
        # Rehecha entera el 06-sep-2026: los CUATRO modelos anteriores
        # (llama-v3p3-70b, qwen2p5-72b, deepseek-r1, mixtral-8x22b) habían
        # desaparecido del catálogo. Al no sobrevivir ninguno, el desplegable
        # caía al catálogo completo del proveedor — 25 entradas, dos de ellas
        # de embeddings. Estos ocho se probaron uno a uno con una petición real
        # de prompt: todos responden en formato correcto. Tiempos medidos entre
        # paréntesis.
        # OJO: /v1/models lista TODO el catálogo, incluidos los que NO son
        # serverless y exigen desplegar una GPU dedicada — esos dan 404 al
        # llamarlos (deepseek-v4-pro y minimax-m2p7 ese día). Por eso la lista
        # curada no se puede generar volcando el endpoint: hay que probarlos.
        "model_default": "accounts/fireworks/models/nemotron-lightning-3p5-30b-a3b",
        "modelos": [
            # rápido y baratísimo — default ($0,05/$0,20)         (2,3s)
            "accounts/fireworks/models/nemotron-lightning-3p5-30b-a3b",
            "accounts/fireworks/models/qwen3p8-max",              # (2,2s)
            "accounts/fireworks/models/qwen3p8-2p4t-a95b",        # (2,6s)
            "accounts/fireworks/models/minimax-m3",               # (3,3s)
            "accounts/fireworks/models/gpt-oss-120b",             # (3,6s)
            # visión + 1M de contexto ($0,15/$0,50)               (15,7s)
            "accounts/fireworks/models/glm-5p3-flash",
            # visión ($0,22/$0,66)                                (5,1s)
            "accounts/fireworks/models/deepseek-v4-flash-vision-exp",
            # tope de gama ($1,40/$4,40)                          (11,8s)
            "accounts/fireworks/models/glm-5p3",
        ],
        "is_paid": True,
    },
    "gemini": {
        "name": "Google Gemini",
        "label": "🏆 Google Gemini",
        "descripcion": "Gratis hasta 15rpm. Bueno para visión y prompts.",
        "url_obtener_key": "https://aistudio.google.com/apikey",
        "tipo": "google",
        # Verificado el 06-sep-2026 contra la API con una key real: 3.8-flash
        # respondió en 1.2s y siguió la instrucción al pie; 2.5-flash tardó
        # 2.3s y ADEMÁS la malinterpretó. Se deja 2.5 al final como red de
        # seguridad para keys antiguas.
        "model_default": "gemini-3.8-flash",
        "modelos": [
            "gemini-3.8-flash",       # el más rápido y certero (1.2s)
            "gemini-3.5-flash",       # alternativa estable (1.4s)
            "gemini-3.1-pro-preview", # máxima calidad, aún en preview
            "gemini-flash-latest",    # alias: siempre el flash más nuevo
            "gemini-2.5-flash",       # fallback para keys sin acceso a 3.x
            "gemini-2.5-pro",
        ],
        "is_paid": False,
    },
    # RETIRADO 08-sep-2026. GitHub cerro GitHub Models el 30-jul-2026: dejo de
    # admitir clientes nuevos el 16-jun, hubo brownouts el 16 y el 23-jul, y
    # ahora la API responde 410 "github_models_retirement_brownout" a todo.
    # Comprobado con un token recien creado del usuario.
    # Se quita en vez de dejarlo fallando porque estaba anunciado como opcion
    # ESTRELLA y GRATUITA del asistente de bienvenida: quien instalara la app
    # lo elegiria primero y se comeria un 410 sin entender nada.
    # Alternativas gratuitas que SI funcionan y ya estan aqui: Groq y Gemini.
    # "github_models": { ... }  <- base_url models.inference.ai.azure.com
    "groq": {
        "name": "Groq",
        "label": "🏆 Groq (gratis, rápido)",
        "descripcion": "Gratis y el más rápido de todos: Qwen3.8 responde en menos de un segundo.",
        "url_obtener_key": "https://console.groq.com/keys",
        "tipo": "openai_compatible",
        "base_url": "https://api.groq.com/openai/v1",
        # Rehecha el 07-sep-2026 con key real: los CINCO anteriores daban 404,
        # los dos Llama incluidos pese a que la documentación de Groq los sigue
        # dando por producción. Estos seis se probaron uno a uno.
        # OJO: con esta key `GET /v1/models` devuelve 403 (las keys de Groq
        # llevan permisos por ámbito), así que el filtro en vivo no puede
        # depurar Groq y la lista curada pasa tal cual. Es el único proveedor
        # OpenAI-compatible en esa situación.
        "model_default": "qwen/qwen3.8-27b",
        "modelos": [
            "qwen/qwen3.8-27b",       # el más rápido de todos — default (0,7s)
            "openai/gpt-oss-20b",     # (1,2s)
            "qwen/qwen3.6-27b",       # razona (<think>): ver _PISO_REINTENTO (1,9s)
            "openai/gpt-oss-120b",    # el más capaz de los rápidos   (2,5s)
            "groq/compound-mini",     # sistema con herramientas      (3,8s)
            "groq/compound",          # idem, más capaz               (8,4s)
        ],
        "is_paid": False,
    },
    "lm_studio": {
        "name": "LM Studio",
        "label": "🏠 LM Studio (local)",
        "descripcion": "Servidor local OpenAI-compatible. Requiere instalar LM Studio y cargar un modelo.",
        "url_obtener_key": "https://lmstudio.ai",
        "tipo": "openai_compatible",
        "base_url": "http://127.0.0.1:1234/v1",
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
        # Revisada el 07-sep-2026 con key real: de los cinco anteriores solo
        # sobrevivían small y codestral. mistral-large-latest, mistral-nemo y
        # open-mistral-7b habían desaparecido del catálogo (46 modelos vivos).
        # Los ministral SÍ respondieron; small/medium y los magistral devuelven
        # 429 "Rate limit exceeded" de forma persistente en el plan gratuito,
        # así que se conservan pero el default es uno que funciona sin pagar.
        "model_default": "ministral-8b-latest",
        "modelos": [
            "ministral-8b-latest",    # equilibrio — default   (7,1s)
            "ministral-3b-latest",    # el más rápido          (3,4s)
            "ministral-14b-latest",   # el más capaz de los que van (9,3s)
            "mistral-medium-latest",  # flagship — 429 en plan gratis
            "mistral-small-latest",   # 429 en plan gratis
            "codestral-latest",       # especializado en código (2,4s)
        ],
        "is_paid": True,
    },
    "ollama": {
        "name": "Ollama (local)",
        "label": "🏆 Ollama local (sin internet)",
        "descripcion": "Sin internet, sin coste. Requiere instalar Ollama y descargar modelo.",
        "url_obtener_key": "https://ollama.com/download",
        "tipo": "openai_compatible",
        "base_url": "http://127.0.0.1:11434/v1",
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
        "descripcion": "GPT-6 Astra, la familia 5.x (Sol/Terra/Luna) y la 4.x. Pago.",
        "url_obtener_key": "https://platform.openai.com/api-keys",
        "tipo": "openai_compatible",
        "base_url": "https://api.openai.com/v1",
        # La familia 5.x se anadio el 06-sep-2026 desde la documentacion, SIN
        # key. Verificada por fin el 08-sep con key real, y habia dos fallos:
        #
        #  · "gpt-5.6" a secas NO EXISTE — solo -sol, -terra y -luna. Y era el
        #    model_default, asi que "Probar keys" fallaba con una key buena.
        #  · toda la familia 5.x y 6 rechaza `max_tokens` Y `temperature` con
        #    un 400, asi que elegir cualquiera de ellos reventaba la app. Se
        #    arregla en OpenAICompatibleProvider._llamar, que aprende la mania
        #    de cada modelo del propio error.
        #
        # Los once probados con llamada real: 4o-mini 1,1s - 5.4-mini 0,7s -
        # 5.6-luna 1,7s - 5.6-sol 1,8s - 6-astra 1,9s - 5.5 y 5.6-terra 2,0s.
        #
        # OJO con los precios: OpenAI no los publica en /v1/models y la
        # familia 5.x/6 no esta en PRECIOS_USD_1M_MODELO, asi que el contador
        # de gasto les aplica el respaldo del proveedor (el de gpt-4o). Es una
        # aproximacion, no un dato: hay que leerlos del panel y rellenarlos.
        "model_default": "gpt-4o-mini",
        "modelos": [
            "gpt-6-astra",     # la generacion nueva
            "gpt-5.6-sol",     # flagship de la 5.6
            "gpt-5.6-terra",   # coste menor, rinde como 5.5
            "gpt-5.6-luna",    # el mas rapido de la 5.6
            "gpt-5.5",         # generacion anterior, estable
            "gpt-5.4-mini",    # 0,7s, el mas rapido de todos
            "gpt-4o",          # flagship multimodal de la serie 4
            "gpt-4o-mini",     # economico y con precio conocido: el default
            "gpt-4.1",         # contexto 1M, fuerte en codigo
            "o3",              # razonamiento maximo
            "o4-mini",         # razonamiento rapido
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
        # OJO: el catálogo gratuito de OpenRouter SE PUDRE cada pocos meses.
        # Historial de esta misma línea: "deepseek/deepseek-chat" murió y se
        # cambió por "meta-llama/llama-3.1-8b-instruct:free", que el
        # 06-sep-2026 también devolvía 404 — junto con los SEIS gratuitos que
        # había aquí. El 08-sep-2026, CUARTO rescate: de los 5 que quedaban,
        # "minimax/minimax-m3:free" y "anthropic/claude-sonnet-4-6" ya no
        # existían (y el primero era el model_default, así que probar la key
        # fallaba), y "nemotron-3.5-lightning:free" respondía en 120s cuando
        # aquí decía 8,6s.
        #
        # Aparecer en /v1/models NO es prueba de nada: hay que llamarlos. De
        # los 16 gratuitos vivos el 08-sep-2026, medidos uno a uno con la key
        # del usuario, solo CUATRO sirven:
        #
        #   inkling:free / inkling-small:free  403 "only available on
        #                                      agentic harnesses"
        #   nemotron-3-ultra-550b:free         211s
        #   nemotron-3.5-lightning:free        120s
        #   nemotron-3-super-120b:free         respuesta sin 'choices'
        #   gemma-4-26b-a4b-it:free            429 del proveedor
        #
        # La lista viva está en https://openrouter.ai/api/v1/models.
        "model_default": "google/gemma-4-31b-it:free",
        "modelos": [
            # Gratuitos — LLAMADOS uno a uno el 08-sep-2026
            "google/gemma-4-31b-it:free",           # 1,0s — el más rápido
            "inclusionai/ling-3.0-flash-fin:free",  # 1,9s
            "dots-studio/dots-3-note-preview:free", # 7,3s
            "cohere/north-mini-code:free",          # 7,7s
            # De pago (los mejores modelos con una sola key)
            "anthropic/claude-haiku-4.5",           # 1,9s
            "openai/gpt-4o",                        # 1,8s
            "google/gemini-2.5-pro",                # 14,3s
            # claude-opus-4.6 vive, pero con el saldo del usuario devuelve
            # 402 "requires more credits": fuera hasta que haya credito.
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
        # SIN VERIFICAR: no hay key de este proveedor. El 08-sep-2026 se
        # auditaron con key real los NUEVE proveedores que si la tienen y
        # las SEIS listas curadas que quedaban por revisar estaban podridas,
        # asi que lo probable es que esta tambien lo este. No se quita el
        # proveedor porque el servicio funciona para quien pague; lo que se
        # ha hecho es que el boton "Probar keys" pregunte al catalogo en vivo
        # en vez de fiarse del model_default (ver app.py), de modo que un
        # default muerto ya no declara invalida una key buena.
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
        # SIN VERIFICAR: no hay key de este proveedor. El 08-sep-2026 se
        # auditaron con key real los NUEVE proveedores que si la tienen y
        # las SEIS listas curadas que quedaban por revisar estaban podridas,
        # asi que lo probable es que esta tambien lo este. No se quita el
        # proveedor porque el servicio funciona para quien pague; lo que se
        # ha hecho es que el boton "Probar keys" pregunte al catalogo en vivo
        # en vez de fiarse del model_default (ver app.py), de modo que un
        # default muerto ya no declara invalida una key buena.
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
        "descripcion": "Modelos de xAI (Elon Musk). Calidad alta, 1M de contexto.",
        "url_obtener_key": "https://console.x.ai/",
        "tipo": "openai_compatible",
        "base_url": "https://api.x.ai/v1",
        # Lista rehecha el 08-sep-2026 con la key del usuario: la anterior
        # (grok-3, grok-3-mini, grok-2-1212) iba TRES generaciones por detras
        # y NINGUNO de los tres existia ya — el default incluido, asi que
        # probar la key fallaba.
        #
        # Todos los Grok RAZONAN menos la variante non-reasoning. Tokens
        # quemados pensando antes de escribir "OK", medidos uno a uno:
        # 4.20-non-reasoning 0, 4.5 30, 4.6 132, 4.3 165, 4.20 174,
        # build-0.1 366. Es la misma trampa que con DeepSeek V4: con
        # presupuestos pequenos se funden el max_tokens razonando y devuelven
        # vacio, de ahi que el default sea el non-reasoning (0,7s) y no el
        # flagship.
        #
        # OJO con los ids: x.ai publica el fechado ("grok-4.20-0309-reasoning")
        # y el estable como ALIAS ("grok-4.20"). Aqui se curan los estables,
        # que no se rompen al rotar la fecha; el catalogo en vivo cuenta los
        # alias como vivos para que no parezcan muertos.
        "model_default": "grok-4.20-non-reasoning",
        "modelos": [
            "grok-4.20-non-reasoning",  # 0,7s, sin razonar, 1M ctx — $1,25/$2,50
            "grok-4.6",                 # 3,2s, flagship, 500K ctx — $2/$6
            "grok-4.5",                 # 1,4s, 500K ctx — $2/$6
            "grok-4.3",                 # 2,0s, 1M ctx — $1,25/$2,50
            "grok-4.20",                # 1,7s, razona, 1M ctx — $1,25/$2,50
            "grok-build-0.1",           # 3,8s, para codigo, 256K — $1/$2
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
    "claude-fable-5-1":          (10.00, 50.00),
    "claude-fable-5":            (10.00, 50.00),
    "claude-opus-5":             (5.00, 25.00),
    "claude-sonnet-5":           (2.00, 10.00),   # más barato que Sonnet 4.6
    "claude-opus-4-8":           (5.00, 25.00),
    "claude-opus-4-7":           (5.00, 25.00),
    "claude-opus-4-6":           (5.00, 25.00),
    "claude-sonnet-4-6":         (3.00, 15.00),
    "claude-sonnet-4-5-20250929": (3.00, 15.00),
    "claude-haiku-4-5":          (1.00, 5.00),
    "deepseek-v4-flash":         (0.14, 0.28),
    "deepseek-v4-pro":           (0.435, 0.87),
    "deepseek-chat":             (0.14, 0.28),   # legacy (dep. 2026-07-24) → v4-flash
    "deepseek-reasoner":         (0.14, 0.28),   # legacy (dep. 2026-07-24)
    "gpt-4o":                    (2.50, 10.00),
    "gpt-4o-mini":               (0.15, 0.60),
    "gemini-2.5-flash":          (0.0, 0.0),   # free tier
    "gemini-2.5-pro":            (0.0, 0.0),   # free tier (límites más bajos)
    "gemini-2.0-flash":          (0.0, 0.0),   # free tier
    # OpenAI GPT-5.x y GPT-6. AVISO SOBRE LA FUENTE: openai.com devuelve 403 a
    # una peticion automatica, asi que estos numeros NO salen de la pagina
    # oficial ni de la API (que no publica precios en /v1/models). Salen de
    # varias fuentes secundarias independientes que coinciden entre si
    # (08-sep-2026). Sirven para que el contador de gasto de un orden de
    # magnitud razonable en vez de aplicar el respaldo de gpt-4o a todos;
    # si alguna vez cuadran mal contra el panel de facturacion, el panel manda.
    "gpt-6-astra":               (10.00, 50.00),
    "gpt-5.6-sol":               (5.00, 30.00),
    "gpt-5.6-terra":             (2.00, 12.00),
    "gpt-5.6-luna":              (0.20,  1.20),
    "gpt-5.5":                   (5.00, 30.00),
    "gpt-5.4-mini":              (0.75,  4.50),
    # OpenAI GPT-4.1 y razonamiento (precios abril 2025)
    "gpt-4.1":                   (2.00,  8.00),
    "gpt-4.1-mini":              (0.40,  1.60),
    "gpt-4.1-nano":              (0.10,  0.40),
    "o3":                        (10.00, 40.00),
    "o4-mini":                   (1.10,  4.40),
    # xAI Grok. Leidos del propio catalogo (/v1/models trae los precios en
    # centesimas de milesima de dolar por millon: dividir por 10.000) y
    # cuadrados contra la consola, que marca $2/$6 para 4.6 y $1/$2 para
    # build-0.1. Los de grok-3 estaban aqui y ese modelo ya no existe.
    "grok-4.6":                  (2.00,  6.00),
    "grok-4.5":                  (2.00,  6.00),
    "grok-4.3":                  (1.25,  2.50),
    "grok-4.20":                 (1.25,  2.50),
    "grok-4.20-non-reasoning":   (1.25,  2.50),
    "grok-build-0.1":            (1.00,  2.00),
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
    "deepseek":      (0.14, 0.28),    # deepseek-v4-flash
    "fireworks":     (0.05, 0.20),    # nemotron-lightning-3p5-30b (verificado 06-sep-2026)
    "gemini":        (0.0, 0.0),      # free tier 15rpm (tier de pago: 0.30/2.50)
    "groq":          (0.0, 0.0),      # free tier
    "lm_studio":     (0.0, 0.0),      # local
    # Referencia del flagship (mistral-medium): PRECIO SIN VERIFICAR, es
    # solo la estimación de respaldo. El default (ministral-8b) es mucho
    # más barato, así que la cifra peca de alta, que es el lado seguro.
    "mistral":       (2.00, 6.00),
    "ollama":        (0.0, 0.0),      # local
    "openai":        (2.50, 10.00),   # gpt-4o
    "openrouter":    None,            # depende del modelo elegido
    "perplexity":    (3.00, 15.00),   # sonar-pro
    "togetherai":    (0.88, 0.88),    # Llama-3.3-70B-Turbo
    "xai":           (1.25,  2.50),   # grok-4.20-non-reasoning (el default)
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
        import copy
        with self._lock:
            out = {}
            for pid, d in self._datos.items():
                # deepcopy: dict(d) compartía el subdict "modelos" con el
                # estado interno — un consumidor que lo mutara corrompía
                # el tracker.
                out[pid] = copy.deepcopy(d)
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

# Timeout de red para TODOS los proveedores LLM. Sin él, los SDKs esperan
# hasta 600 s (OpenAI/Anthropic) o indefinidamente (google-genai) y el
# worker queda colgado con la UI en "generando…".
LLM_TIMEOUT_S = 180
# El catálogo solo llena un desplegable: si tarda, no se espera.
TIMEOUT_CATALOGO_S = 5

# Groq esta detras de Cloudflare y RECHAZA el User-Agent por defecto de
# urllib ("Python-urllib/3.10") con un 403 "error code: 1010" — el codigo de
# bloqueo por cliente, no un problema de key. Medido el 08-sep-2026 contra su
# /openai/v1/models: sin cabecera 403, con CUALQUIER User-Agent 200 y 14
# modelos. La generacion no se enteraba porque va por el SDK de OpenAI, que
# manda el suyo; el que se quedaba mudo era el catalogo en vivo, y por eso la
# lista curada de Groq no se auto-depuraba nunca.
UA_CATALOGO = "G-Prompt-Studio/1.0"

# Servidores LOCALES (LM Studio / Ollama). Hay DOS operaciones distintas y
# confundirlas costó un bug en cada dirección:
#
#   1) "¿está encendido?" -> lo pregunta el refresco de iconos del desplegable
#      de cerebros, para los 14 proveedores y varias veces seguidas. Con 2s de
#      timeout, cambiar de cerebro congelaba la ventana 12 segundos ("No
#      responde", 06-sep-2026). Se bajó a 0.6s... y entonces se rompió al revés:
#      el 07-sep-2026, con 19 modelos cargados, el /v1/models de LM Studio
#      tardaba 2,05s CONSISTENTES (medido seis veces), así que se declaraba
#      dormido un servidor que estaba abierto.
#      Arreglo: para esto no hace falta la lista de modelos, basta con saber si
#      alguien escucha en el puerto. Un connect() de TCP tarda milisegundos.
#
#   2) "¿qué modelos tiene?" -> solo al poblar el desplegable de modelos, y
#      fuera del hilo de Tk. Ahí sí se puede esperar.
TIMEOUT_SONDEO_LOCAL_S = 0.4
TIMEOUT_LOCAL_S = 5.0


def _forzar_ipv4(url: str) -> str:
    """Cambia 'localhost' por '127.0.0.1' en una URL local.

    Medido el 07-sep-2026 en la maquina del usuario, con LM Studio ABIERTO:

        http://localhost:1234/v1/models   ->  2019 ms
        http://127.0.0.1:1234/v1/models   ->     1 ms

    'localhost' resuelve a ::1 (IPv6) primero, y ese puerto no rechaza la
    conexion: la deja colgada hasta agotar el timeout. Solo despues se prueba
    IPv4, que responde al instante. Esa espera fantasma es la causa REAL del
    cuelgue de 12s al cambiar de cerebro; bajar timeouts solo lo disimulaba, y
    de hecho el ultimo recorte (0.6s) dejaba a LM Studio por debajo del umbral
    y lo declaraba dormido estando abierto.
    """
    return (url or "").replace("//localhost:", "//127.0.0.1:")


def _puerto_abierto(url: str, timeout: float = TIMEOUT_SONDEO_LOCAL_S) -> bool:
    """¿Hay algo escuchando en el host:puerto de esa URL?

    No comprueba que sea LM Studio ni que responda bien: solo que el puerto
    esté abierto. Es justo lo que necesita el icono del desplegable, y cuesta
    milisegundos en vez de segundos.
    """
    try:
        url = _forzar_ipv4(url)
        partes = urllib.parse.urlsplit(url if "://" in url else "http://" + url)
        host = partes.hostname or "localhost"
        puerto = partes.port or (443 if partes.scheme == "https" else 80)
    except Exception:
        return False
    try:
        with socket.create_connection((host, puerto), timeout=timeout):
            return True
    except Exception:
        return False

# Y el resultado se cachea: el refresco se dispara varias veces seguidas (al
# cambiar de cerebro, al guardar una key, al abrir el desplegable).
_CACHE_LOCAL: dict[str, tuple[float, list[str]]] = {}
_CACHE_LOCAL_TTL_S = 20


def _local_cacheado(clave: str, consultar):
    """Ejecuta `consultar()` como mucho una vez cada _CACHE_LOCAL_TTL_S.

    La clave es la URL del servidor, no el nombre del proveedor: si el usuario
    cambia el puerto de LM Studio, una clave fija habria devuelto la respuesta
    del puerto anterior.
    """
    ahora = time.time()
    prev = _CACHE_LOCAL.get(clave)
    if prev and ahora - prev[0] < _CACHE_LOCAL_TTL_S:
        return prev[1]
    try:
        res = consultar() or []
    except Exception:
        res = []
    _CACHE_LOCAL[clave] = (ahora, res)
    return res

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
            # max_retries=0 A PROPOSITO: el SDK reintenta 2 veces por su
            # cuenta y DeepSeekWorker.generar() otras 3, asi que se
            # MULTIPLICAN: 3x3 = 9 llamadas de hasta LLM_TIMEOUT_S cada una =
            # 27 minutos mirando "Generando..." antes de ver el error. El
            # reintento se deja en un solo sitio (el worker), que ademas
            # aplica backoff y lo deja en el log.
            self._cliente = OpenAI(api_key=api_key, base_url=base_url,
                                   timeout=LLM_TIMEOUT_S, max_retries=0)

    def disponible(self) -> bool:
        return bool(self.api_key) and self._cliente is not None

    def listar_modelos(self) -> list[str]:
        """Catálogo EN VIVO del proveedor vía GET /v1/models ([] si no responde).

        Todos los proveedores OpenAI-compatible publican este endpoint con la
        misma forma, así que groq, mistral, together, fireworks, openrouter,
        xai, deepseek y openai lo heredan de golpe.

        Existe porque las listas escritas a mano se pudren: el 06-sep-2026 los
        SEIS modelos ":free" de OpenRouter devolvían 404 (y era el segundo
        rescate de esa misma lista), y Gemini iba dos generaciones por detrás.
        Timeout corto y fallo silencioso: esto alimenta un desplegable, nunca
        puede bloquear la interfaz.
        """
        if not (self.api_key and self.base_url):
            return []
        try:
            req = urllib.request.Request(
                self.base_url.rstrip("/") + "/models",
                headers={"Authorization": f"Bearer {self.api_key}",
                         "User-Agent": UA_CATALOGO})
            with urllib.request.urlopen(req, timeout=TIMEOUT_CATALOGO_S) as r:
                data = json.loads(r.read())
            vivos = []
            for m in data.get("data", []):
                if not m.get("id"):
                    continue
                vivos.append(m["id"])
                # Los ALIAS cuentan como vivos: son nombres que el proveedor
                # acepta igual en /chat/completions. x.ai publica el id con
                # fecha ("grok-4.20-0309-reasoning") y el estable como alias
                # ("grok-4.20"), que es lo que interesa curar — un id fechado
                # se rompe cuando rota la fecha. Sin esto, la lista curada de
                # x.ai aparecia MUERTA entera aunque los modelos respondan.
                vivos.extend(a for a in (m.get("aliases") or []) if a)
            return vivos
        except Exception as e:
            logger.debug(f"[silent] catálogo en vivo de {self.base_url}: {e}")
            return []

    # Cuanto se amplia el presupuesto al reintentar con un razonador, y hasta
    # donde. Un modelo que "piensa" gasta esos tokens del mismo max_tokens: con
    # el presupuesto normal se lo funde razonando y devuelve vacio.
    _FACTOR_REINTENTO = 3
    _TECHO_REINTENTO = 16000
    # Suelo del reintento. Medido el 06-sep-2026 contra la API de DeepSeek: V4
    # (pro Y flash, los dos razonan) quema entre 263 y 780 tokens pensando ANTES
    # de escribir nada. Con presupuestos pequeños —el boton "Sugerir negative"
    # pide 500, la traduccion 400, varios sitios 200— multiplicar por 3 deja
    # 1500 o menos, que es justo el margen donde unas veces entra y otras no:
    # de ahi que el usuario reportara que "suele" fallar. 4000 responde siempre
    # en la medicion, y solo se gasta cuando el sintoma ya ha ocurrido.
    _PISO_REINTENTO = 4000

    # Manias por modelo, APRENDIDAS del propio 400 y recordadas para pagar el
    # error una sola vez por modelo y proceso. Se guardan por MODELO y no por
    # proveedor porque conviven en el mismo: gpt-4o-mini acepta los parametros
    # de siempre y gpt-5.6-terra no.
    _SIN_MAX_TOKENS: set = set()    # exigen max_completion_tokens
    _SIN_TEMPERATURE: set = set()   # no aceptan temperature

    def _llamar(self, messages, temperature, max_tokens, modelo):
        """Una llamada. Devuelve (texto, finish_reason).

        OpenAI RETIRO dos parametros en sus modelos modernos. Toda la familia
        GPT-5.x y GPT-6 responde 400 a los dos:

          "Unsupported parameter: 'max_tokens' is not supported with this
           model. Use 'max_completion_tokens' instead."
          "Unsupported value: 'temperature' does not support 0.75..."

        Medido el 08-sep-2026 con la key del usuario: de su lista curada solo
        gpt-4o-mini y gpt-4o siguen aceptando los de siempre, asi que elegir
        cualquier GPT-5.5, 5.6 o 6 reventaba con un 400 en la cara. El resto
        de proveedores OpenAI-compatible (groq, xai, deepseek, mistral...)
        siguen con los parametros clasicos.

        Se aprende del error en vez de mantener una lista a mano: es
        exactamente el tipo de lista que se pudre (ver MODELOS_CLAUDE_SIN_
        SAMPLING, que hubo que descubrir igual para la familia Claude 5).
        """
        for intento in range(3):
            kwargs = {"model": modelo, "messages": messages}
            kwargs["max_completion_tokens" if modelo in self._SIN_MAX_TOKENS
                   else "max_tokens"] = max_tokens
            if modelo not in self._SIN_TEMPERATURE:
                kwargs["temperature"] = temperature
            try:
                res = self._cliente.chat.completions.create(**kwargs)
                break
            except Exception as e:
                msg = str(e)
                if ("max_completion_tokens" in msg
                        and modelo not in self._SIN_MAX_TOKENS):
                    logger.info(f"{modelo}: usa max_completion_tokens")
                    self._SIN_MAX_TOKENS.add(modelo)
                elif ("temperature" in msg and "nsupported" in msg
                        and modelo not in self._SIN_TEMPERATURE):
                    logger.info(f"{modelo}: no acepta temperature")
                    self._SIN_TEMPERATURE.add(modelo)
                else:
                    raise
        else:
            raise Exception(f"{modelo}: no acepta los parámetros de la llamada")
        usage = getattr(res, "usage", None)
        if usage is not None:
            self._registrar_uso(getattr(usage, "prompt_tokens", 0),
                                getattr(usage, "completion_tokens", 0))
        # `choices` puede venir vacío y `content` puede ser None (p.ej.
        # respuesta filtrada o proveedor "compatible" que no lo rellena).
        # Sin este guard, un None se propaga al historial y a los parsers.
        if not getattr(res, "choices", None):
            raise Exception(f"{modelo}: respuesta sin choices (filtrada o vacía)")
        choice = res.choices[0]
        return (choice.message.content or ""), (getattr(choice, "finish_reason", "") or "?")

    def completar(self, messages: list[dict], temperature: float = 0.75, max_tokens: int = 900, model: str | None = None) -> str:
        if not self._cliente:
            raise Exception("Proveedor no configurado (sin api key)")
        modelo = model or self.model
        logger.debug(f"OpenAICompatible: calling {modelo}")
        content, fr = self._llamar(messages, temperature, max_tokens, modelo)

        if not content.strip() and fr == "length":
            # RAZONADORES (deepseek-v4-pro, o3, deepseek-r1...): queman TODO el
            # max_tokens "pensando" (reasoning_tokens == completion_tokens) y
            # devuelven content VACÍO con HTTP 200. Auditoría 14-jul-2026: 3 de
            # cada 4 llamadas con max_tokens=900.
            #
            # Antes se fallaba directamente y el usuario veía "reintenta o sube
            # max_tokens" sin poder subirlo desde la UI. Ahora se reintenta UNA
            # vez con presupuesto ampliado, que es exactamente lo que hacía
            # falta. No se mantiene una lista de "modelos razonadores" porque
            # envejece mal: se reacciona al síntoma, que es inequívoco.
            ampliado = min(max(max_tokens * self._FACTOR_REINTENTO,
                               self._PISO_REINTENTO), self._TECHO_REINTENTO)
            if ampliado > max_tokens:
                logger.info(
                    f"{modelo}: razonamiento agotó {max_tokens} tokens sin "
                    f"responder; reintentando con {ampliado}")
                content, fr = self._llamar(messages, temperature, ampliado, modelo)

        if not content.strip():
            if fr == "length":
                # OJO: no recomendar aqui "deepseek-v4-flash como modelo no
                # razonador". Medido el 06-sep-2026: flash razona igual que pro
                # (500 tokens de razonamiento con max_tokens=500, respuesta
                # vacia). El consejo era falso y mandaba al usuario al mismo
                # muro. Gemini si respondio a la misma peticion sin agotarse.
                raise Exception(
                    f"{modelo}: se quedó sin tokens razonando, incluso al "
                    f"reintentar con {ampliado} — pide menos cantidad de golpe "
                    f"o cambia de proveedor (Gemini responde bien a esto)")
            raise Exception(f"{modelo}: respuesta vacía (finish_reason={fr})")
        return content


class OllamaProvider(OpenAICompatibleProvider):
    """Variante: Ollama local. Detecta modelo instalado automáticamente."""

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str = "http://127.0.0.1:11434/v1", **kwargs):
        super().__init__(api_key="ollama", model=model, base_url=base_url)

    def disponible(self) -> bool:
        raiz = _forzar_ipv4(self.base_url or "http://127.0.0.1:11434/v1")
        return bool(_local_cacheado(
            "puerto:" + raiz, lambda: ["ok"] if _puerto_abierto(raiz) else []))

    def listar_modelos(self) -> list[str]:
        """Modelos descargados en Ollama ([] si no responde)."""
        try:
            raiz = _forzar_ipv4(self.base_url or "http://127.0.0.1:11434/v1")
            tags = raiz.rsplit("/v1", 1)[0] + "/api/tags"
            with urllib.request.urlopen(tags, timeout=TIMEOUT_LOCAL_S) as r:
                data = json.loads(r.read())
            return [m["name"] for m in data.get("models", []) if m.get("name")]
        except Exception:
            return []

    def _obtener_modelo_disponible(self) -> str | None:
        return elegir_modelo_chat(self.listar_modelos())

    def completar(self, messages: list[dict], temperature: float = 0.75, max_tokens: int = 900, model: str | None = None) -> str:
        modelo = model or self.model or self._obtener_modelo_disponible()
        if not modelo:
            raise Exception("No se encontró Ollama corriendo o no tienes modelos instalados.")
        return super().completar(messages, temperature, max_tokens, model=modelo)


# Modelos locales que NO sirven para redactar prompts. Los servidores locales
# (LM Studio, Ollama) listan TODO lo que tengas descargado, y coger "el primero"
# puede caer en un modelo de embeddings -> error incomprensible para el usuario.
_TOKENS_NO_CHAT = ("embed", "embedding", "rerank", "reranker")
# Visión: sí generan texto, pero describiendo imágenes; como cerebro son malos.
# No se descartan (puede ser lo unico instalado), solo van al final.
_TOKENS_VISION = ("vl-", "vl.", "-vl", "llava", "vision", "qwen2.5vl")


def elegir_modelo_chat(modelos: list[str]) -> str | None:
    """Mejor modelo para chatear de una lista de un servidor local.

    Descarta los de embeddings/rerank (no pueden generar texto) y deja los de
    vision para el final. Devuelve None si no queda ninguno usable.
    """
    if not modelos:
        return None
    utiles = [m for m in modelos
              if not any(t in m.lower() for t in _TOKENS_NO_CHAT)]
    if not utiles:
        return None
    normales = [m for m in utiles
                if not any(t in m.lower() for t in _TOKENS_VISION)]
    return (normales or utiles)[0]


class LMStudioProvider(OpenAICompatibleProvider):
    """LM Studio: servidor local OpenAI-compatible (por defecto puerto 1234).

    Igual que en Ollama, el modelo NO se elige a mano: se usa el que el usuario
    tenga CARGADO en LM Studio. Antes se enviaba el literal "local-model" que
    venia en model_default, y las versiones recientes de LM Studio lo rechazan
    con "model not found" en vez de ignorarlo, asi que el proveedor estaba
    declarado pero no servia.

    LM Studio expone /v1/models (OpenAI-compatible), el equivalente al
    /api/tags de Ollama.
    """

    # Placeholder historico de model_default: no es un modelo real, hay que
    # resolverlo consultando al servidor.
    _PLACEHOLDER = "local-model"

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 base_url: str = "http://127.0.0.1:1234/v1", **kwargs):
        super().__init__(api_key="lm-studio", model=model, base_url=base_url)
        self._raiz = _forzar_ipv4(base_url or "http://127.0.0.1:1234/v1").rstrip("/")

    def listar_modelos(self) -> list[str]:
        """Modelos cargados ahora mismo en LM Studio ([] si no responde)."""
        try:
            with urllib.request.urlopen(self._raiz + "/models", timeout=TIMEOUT_LOCAL_S) as r:
                data = json.loads(r.read())
            return [m["id"] for m in data.get("data", []) if m.get("id")]
        except Exception:
            return []

    def disponible(self) -> bool:
        return bool(_local_cacheado(
            "puerto:" + self._raiz,
            lambda: ["ok"] if _puerto_abierto(self._raiz) else []))

    def _obtener_modelo_disponible(self) -> str | None:
        return elegir_modelo_chat(self.listar_modelos())

    def completar(self, messages: list[dict], temperature: float = 0.75,
                  max_tokens: int = 900, model: str | None = None) -> str:
        modelo = model or self.model
        if not modelo or modelo == self._PLACEHOLDER:
            modelo = self._obtener_modelo_disponible()
        if not modelo:
            raise Exception(
                "No se encontro LM Studio corriendo en "
                f"{self._raiz} o no tienes ningun modelo cargado. "
                "Abre LM Studio, carga un modelo y activa el servidor local.")
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
            self._cliente = google_genai.Client(
                api_key=api_key,
                http_options=genai_types.HttpOptions(timeout=LLM_TIMEOUT_S * 1000))

    def disponible(self) -> bool:
        return GEMINI_DISPONIBLE and bool(self.api_key)

    def listar_modelos(self) -> list[str]:
        """Catálogo EN VIVO de Google ([] si no responde).

        Google no es OpenAI-compatible: la key va en la query, el endpoint es
        /v1beta/models y los IDs vienen con prefijo ("models/gemini-2.5-flash").
        Hasta el 08-sep-2026 el filtro en vivo solo admitía openai_compatible y
        anthropic, así que la lista de Gemini era la ÚNICA de nube que no se
        auto-depuraba nunca — y es de las que más rota se ha quedado (ya iba
        dos generaciones por detrás una vez).

        Se queda solo con los que sirven para generar texto: de los 54 que
        devuelve, 40 aceptan generateContent y el resto son embeddings, TTS o
        imagen, que no pintan nada en el desplegable de cerebros.
        """
        if not self.api_key:
            return []
        try:
            req = urllib.request.Request(
                "https://generativelanguage.googleapis.com/v1beta/models"
                f"?pageSize=200&key={urllib.parse.quote(self.api_key)}",
                headers={"User-Agent": UA_CATALOGO})
            with urllib.request.urlopen(req, timeout=TIMEOUT_CATALOGO_S) as r:
                data = json.loads(r.read())
            return [m["name"].split("/")[-1] for m in data.get("models", [])
                    if m.get("name")
                    and "generateContent" in (m.get("supportedGenerationMethods") or [])]
        except Exception as e:
            logger.debug(f"[silent] catálogo de Google: {e}")
            return []

    def completar(self, messages: list[dict], temperature: float = 0.75, max_tokens: int = 900, model: str | None = None) -> str:
        if not self.api_key:
            raise Exception("Gemini no configurado (sin api key)")
        if not GEMINI_DISPONIBLE:
            raise Exception("google-genai no instalado")

        if self._cliente is None:
            self._cliente = google_genai.Client(
                api_key=self.api_key,
                http_options=genai_types.HttpOptions(timeout=LLM_TIMEOUT_S * 1000))
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
# claude-fable-5 (restaurado 1-jul-2026) rechaza sampling igual que Opus.
# Modelos Claude que devuelven 400 si se les envía `temperature`. La familia 5
# entera (Fable 5/5.1, Opus 5, Sonnet 5) eliminó el sampling, no solo Opus.
# Añadidos el 06-sep-2026 al actualizar el catálogo: sin esto, poner
# claude-sonnet-5 como default habría hecho fallar TODAS las llamadas.
MODELOS_CLAUDE_SIN_SAMPLING = ("claude-fable-5", "claude-opus-5", "claude-sonnet-5",
                               "claude-opus-4-8", "claude-opus-4-7")


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
                # max_retries=0: misma razon que en OpenAICompatibleProvider
                # (el reintento vive en el worker, no aqui).
                self._cliente = Anthropic(api_key=api_key,
                                          timeout=LLM_TIMEOUT_S, max_retries=0)
                self._anthropic_disponible = True
            except ImportError:
                self._anthropic_disponible = False
                self._cliente = None

    def disponible(self) -> bool:
        return getattr(self, "_anthropic_disponible", False) and bool(self.api_key)

    def listar_modelos(self) -> list[str]:
        """Catálogo EN VIVO de Anthropic ([] si no responde).

        Anthropic no es OpenAI-compatible: el endpoint es el mismo /v1/models
        pero la auth va en `x-api-key` y exige la cabecera `anthropic-version`,
        así que no se puede heredar de OpenAICompatibleProvider.
        """
        if not self.api_key:
            return []
        try:
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/models?limit=100",
                headers={"x-api-key": self.api_key,
                         "anthropic-version": "2023-06-01",
                         "User-Agent": UA_CATALOGO})
            with urllib.request.urlopen(req, timeout=TIMEOUT_CATALOGO_S) as r:
                data = json.loads(r.read())
            return [m["id"] for m in data.get("data", []) if m.get("id")]
        except Exception as e:
            logger.debug(f"[silent] catálogo de Anthropic: {e}")
            return []

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
        # `content` puede venir vacío o sin bloques de texto (respuesta
        # filtrada / refusal) — mismo guard que el provider OpenAI, sin él
        # esto revienta con un IndexError críptico.
        bloques_texto = [b.text for b in getattr(res, "content", None) or []
                         if getattr(b, "type", "") == "text"]
        if not bloques_texto:
            raise Exception(
                f"{modelo}: respuesta sin texto "
                f"(stop_reason={getattr(res, 'stop_reason', '?')})")
        return bloques_texto[0]


# FACTORY

# Proveedores que corren en la maquina del usuario: su lista de modelos NO se
# puede fijar en el codigo, es lo que cada uno tenga cargado/descargado.
PROVEEDORES_LOCALES = ("lm_studio", "ollama")


def ordenar_modelos_chat(modelos: list[str]) -> list[str]:
    """Ordena para el desplegable: primero los de chat, vision al final.

    Los de embeddings/rerank se QUITAN: no pueden generar texto, asi que
    ofrecerlos como "cerebro" solo sirve para que alguien los elija y falle.
    """
    utiles = [m for m in modelos
              if not any(t in m.lower() for t in _TOKENS_NO_CHAT)]
    normales = [m for m in utiles
                if not any(t in m.lower() for t in _TOKENS_VISION)]
    vision = [m for m in utiles if m not in normales]
    return normales + vision


# Catálogo en vivo cacheado: el desplegable puede abrirse muchas veces y no
# tiene sentido preguntar al proveedor en cada una.
_CACHE_CATALOGO: dict[str, tuple[float, list[str]]] = {}
_CACHE_CATALOGO_TTL_S = 600


def _catalogo_en_vivo(provider_id: str, api_key: str) -> list[str]:
    """Modelos que el proveedor dice servir ahora mismo ([] si no se sabe)."""
    ahora = time.time()
    cacheado = _CACHE_CATALOGO.get(provider_id)
    if cacheado and ahora - cacheado[0] < _CACHE_CATALOGO_TTL_S:
        return cacheado[1]
    try:
        prov = get_provider(provider_id, api_key)
        vivos = prov.listar_modelos() if hasattr(prov, "listar_modelos") else []
    except Exception as e:
        logger.debug(f"[silent] catálogo de {provider_id}: {e}")
        vivos = []
    if vivos:
        _CACHE_CATALOGO[provider_id] = (ahora, vivos)
    return vivos


_RE_FECHA_MODELO = re.compile(r"-\d{8}$")


def _sin_fecha(modelo: str) -> str:
    """Quita el sufijo -YYYYMMDD de un ID de modelo.

    Anthropic publica los modelos viejos CON fecha ("claude-haiku-4-5-20251001")
    pero acepta el alias sin ella, que es lo que guarda el catálogo curado (hay
    un candado que prohíbe las fechas en los IDs). Sin normalizar, el filtro en
    vivo daba por muerto un modelo que responde en 0,6s.
    """
    return _RE_FECHA_MODELO.sub("", modelo or "")


def modelos_disponibles(provider_id: str, api_key: str | None = None) -> list[str]:
    """Modelos elegibles de un proveedor, para poblar el desplegable.

    Los LOCALES se consultan EN VIVO (LM Studio /v1/models, Ollama /api/tags);
    si el servidor no responde se devuelve [] y la UI cae al comportamiento de
    siempre.

    Para los de nube OpenAI-compatible, si hay `api_key` se consulta su
    catálogo real y se usa para DEPURAR la lista curada: los IDs que el
    proveedor ya no sirve se caen. Las listas escritas a mano se pudren —el
    06-sep-2026 los seis modelos ":free" de OpenRouter daban 404— pero volcar
    el catálogo entero tampoco vale: OpenRouter publica 430 modelos y eso no
    es un desplegable, es un listín. Por eso se filtra en vez de sustituir.

    Si NINGUNO de los curados sobrevive, entonces sí se cae al catálogo vivo:
    peor un listín largo que un desplegable vacío.
    """
    info = LLM_PROVIDERS.get(provider_id, {})
    if provider_id in PROVEEDORES_LOCALES:
        try:
            prov = get_provider(provider_id, api_key="")
            return ordenar_modelos_chat(prov.listar_modelos())
        except Exception as e:
            logger.debug(f"[silent] modelos de {provider_id}: {e}")
            return []

    estaticos = list(info.get("modelos") or [])
    # Anthropic entra aunque no sea OpenAI-compatible: tiene su propio
    # listar_modelos(). Gemini sigue fuera, no lo implementa.
    if not api_key or info.get("tipo") not in ("openai_compatible", "anthropic",
                                               "google"):
        return estaticos

    vivos = _catalogo_en_vivo(provider_id, api_key)
    if not vivos:
        return estaticos

    conjunto = set(vivos) | {_sin_fecha(m) for m in vivos}
    validos = [m for m in estaticos if m in conjunto]
    if validos:
        if len(validos) != len(estaticos):
            caidos = [m for m in estaticos if m not in conjunto]
            logger.info(f"{provider_id}: {len(caidos)} modelo(s) del catálogo ya "
                        f"no se sirven y se ocultan: {caidos}")
        return validos

    logger.warning(f"{provider_id}: NINGÚN modelo del catálogo curado sigue vivo; "
                   f"se muestra el catálogo del proveedor ({len(vivos)} modelos)")
    return ordenar_modelos_chat(sorted(vivos))


def get_provider(provider_id: str, api_key: str, model: str | None = None) -> BaseLLMProvider:
    """Devuelve una instancia del proveedor configurado."""
    info = LLM_PROVIDERS.get(provider_id)
    if not info:
        raise ValueError(f"Proveedor desconocido: {provider_id}. Disponibles: {list(LLM_PROVIDERS.keys())}")

    tipo = info["tipo"]
    modelo_final = model or info.get("model_default")

    if provider_id == "ollama":
        prov = OllamaProvider(api_key=None, model=modelo_final, base_url=info.get("base_url"))
    elif provider_id == "lm_studio":
        # Local como Ollama: sin key y resolviendo el modelo cargado.
        prov = LMStudioProvider(api_key=None, model=modelo_final, base_url=info.get("base_url"))
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


# ── DPAPI (Windows) — cifrado real ligado a la cuenta del usuario ──
# CryptProtectData cifra con una clave gestionada por Windows que solo el
# MISMO usuario en la MISMA máquina puede descifrar. Sustituye al esquema
# AES legacy cuya clave se derivaba de MAC+username (trivial de reproducir
# por cualquier proceso local). El AES legacy se mantiene SOLO para leer
# keys.json v1 antiguos y como fallback en sistemas no-Windows.

def _dpapi_disponible() -> bool:
    return os.name == "nt"


def _dpapi_crypt(data: bytes, proteger: bool) -> bytes:
    """CryptProtectData / CryptUnprotectData (ámbito: usuario actual)."""
    import ctypes
    from ctypes import wintypes

    class _BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD),
                    ("pbData", ctypes.POINTER(ctypes.c_char))]

    buf = ctypes.create_string_buffer(data, len(data))
    blob_in = _BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    blob_out = _BLOB()
    fn = (ctypes.windll.crypt32.CryptProtectData if proteger
          else ctypes.windll.crypt32.CryptUnprotectData)
    if not fn(ctypes.byref(blob_in), None, None, None, None, 0,
              ctypes.byref(blob_out)):
        raise OSError(f"DPAPI {'protect' if proteger else 'unprotect'} falló")
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def _obtener_clave_cifrado() -> bytes:
    """Deriva una clave de cifrado del hardware local (esquema LEGACY v1)."""
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


def _migrar_a_dpapi(claves: dict) -> None:
    """Reescribe el fichero de fallback con DPAPI si venia en un formato viejo.

    Se llama al LEER un formato v0 (claro) o v1 (AES con clave MAC+usuario).
    Silencioso a proposito: si falla, el usuario conserva sus claves y se
    reintentara en el siguiente arranque.
    """
    if not claves or not _dpapi_disponible():
        return
    try:
        _escribir_dict_fallback(claves)
        logger.info("API keys migradas al formato cifrado con DPAPI.")
    except Exception as e:
        logger.debug(f"[silent] migracion DPAPI: {e}")


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
            # Formato v2: DPAPI (Windows)
            if isinstance(datos, dict) and datos.get("encrypted") == "dpapi":
                import base64
                descifrado = {}
                for k, v in datos.get("keys", {}).items():
                    try:
                        descifrado[k] = _dpapi_crypt(
                            base64.b64decode(v), proteger=False).decode("utf-8")
                    except Exception as e:
                        logger.debug(f"[silent] DPAPI unprotect '{k}': {e}")
                        descifrado[k] = ""
                return descifrado
            # Formato v1 legacy: AES con clave derivada de MAC+usuario. Eso es
            # OFUSCACION, no criptografia real (la clave se puede reconstruir en
            # la propia maquina), asi que en cuanto se lee se REESCRIBE con
            # DPAPI. Migracion silenciosa: el formato v1 se extingue solo y no
            # deja a nadie sin claves, que es lo que pasaria si lo borrasemos.
            if isinstance(datos, dict) and "encrypted" in datos:
                clave = _obtener_clave_cifrado()
                descifrado = {}
                for k, v in datos.get("keys", {}).items():
                    descifrado[k] = _descifrar_aes(v, clave)
                _migrar_a_dpapi(descifrado)
                return descifrado
            # Formato v0: JSON en claro (instalaciones muy antiguas) -> migrar.
            if isinstance(datos, dict) and datos:
                _migrar_a_dpapi(datos)
            return datos
    except Exception:
        return {}


def _escribir_dict_fallback(d: dict):
    ruta = _ruta_keys_fallback()
    tmp = ruta + ".tmp"
    datos = None
    # Preferir DPAPI (cifrado real del SO). Cae al AES legacy si falla
    # o en sistemas no-Windows.
    if _dpapi_disponible():
        try:
            import base64
            cifrado = {
                k: base64.b64encode(
                    _dpapi_crypt(v.encode("utf-8"), proteger=True)).decode("ascii")
                for k, v in d.items()
            }
            datos = {"version": 2, "encrypted": "dpapi", "keys": cifrado}
        except Exception as e:
            logger.warning(f"DPAPI no disponible, usando cifrado legacy: {e}")
    if datos is None:
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

    # Modelos deprecados → su reemplazo (se migran al cargar la preferencia).
    _MIGRAR_MODELO = {
        "deepseek-chat": "deepseek-v4-flash",       # dep. 2026-07-24
        "deepseek-reasoner": "deepseek-v4-flash",   # dep. 2026-07-24
    }

    def _cargar_modelos_activos(self) -> dict:
        """Lee active_models.json: {provider_id: modelo_elegido}."""
        try:
            from config import ARCHIVOS
            ruta = ARCHIVOS.get("active_models")
            if ruta and os.path.exists(str(ruta)):
                with open(str(ruta), encoding="utf-8") as f:
                    datos = json.load(f)
                if isinstance(datos, dict):
                    return {k: self._MIGRAR_MODELO.get(str(v), str(v))
                            for k, v in datos.items() if v}
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
