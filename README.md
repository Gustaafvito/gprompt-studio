# 🧠 G-Prompt Studio v1.0.0

> Suite profesional de ingeniería de prompts para IA generativa.
> Convierte ideas en instrucciones técnicas de alta precisión para **imagen, vídeo y audio**.

[![CI](https://github.com/Gustaafvito/gprompt-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/Gustaafvito/gprompt-studio/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Version](https://img.shields.io/badge/version-1.0.0-brightgreen.svg)](https://github.com/Gustaafvito/gprompt-studio)

---

## ✨ Qué hace

G-Prompt Studio toma una idea simple ("una chica con pelo plateado en un bosque mágico") y la convierte en un prompt profesional optimizado para el modelo concreto que vas a usar — con sus reglas, sus tags, sus límites, su sampler recomendado y, si aplica, su prompt negativo.

| Modo | Modelos soportados |
|------|--------------------|
| 🖼 **Imagen** | 93+ modelos vigentes: FLUX.1 [dev/schnell], Z-Image, GPT Image, Nano Banana, Illustrious, Pony, Qwen, Realismo SD, Anime/Ilustración y más |
| 🎬 **Vídeo** | 72 motores: Kling, Seedance, Wan, Hailuo, StarDream, PixVerse, Vidu, Grok, Happy Horse, Nano Banana, Sora2, Veo, SeaArt y más |
| 🎵 **Audio** | 11 modelos: Suno (×4), Udio (×2), Minimax Music (×2), MusicGo, Mureka V9 — con letras, estilo, emoción, voz e idioma |

## 🧠 Multi-Cerebro (14 LLMs soportados)

Conecta con cualquiera de estos proveedores con una sola key:

| Proveedor | Tipo | Coste |
|-----------|------|-------|
| 🥈 **DeepSeek V3** | Pago | ~€0.14/1M tokens |
| 💎 **Claude (Anthropic)** | Pago | ~€2.40/1M tokens |
| 💎 **Fireworks AI** | Pago | Modelos open-source rápidos |
| 🏆 **Google Gemini** | Gratis | 15 rpm |
| 🏆 **GitHub Models** | Gratis | Acceso a OpenAI/Claude/Llama |
| 🏆 **Groq** | Gratis | 14.400 req/día |
| 🏆 **LM Studio** | Local | Servidor OpenAI-compatible |
| 💎 **Mistral** | Pago | Modelos europeos |
| 🏆 **Ollama** | Local | Sin internet, sin coste |
| 💎 **OpenAI GPT-4o** | Pago | ~€2.40/1M |
| 🥈 **OpenRouter** | Pago | 100+ modelos con UNA key |
| 💎 **Perplexity** | Pago | Modelos con búsqueda en tiempo real |
| 💎 **Together AI** | Pago | Modelos open-source y propietarios |
| 🏆 **Google Gemini Omni** | Nuevo | Modelo de vídeo multimodal |

## 🚀 Funciones principales

| Función | Qué hace |
|---|---|
| 💡 **Ideas** | 3 ideas creativas basadas en tus estilos |
| ✨ **Generar Prompt** | Traduce tu idea a prompt profesional adaptado al modelo |
| 🔀 **Variaciones x3** | 3 ángulos distintos del mismo concepto |
| 👁 **Analizar Imagen** | Describe una imagen de referencia (Gemini → Ollama → OpenRouter) |
| 🎯 **Img→Prompt** | Genera prompt anclado a una imagen |
| 🔁 **Refinar** | Mejora y expande el prompt actual |
| 💬 **Copiloto** | Chat conversacional para dictar cambios específicos |
| 📦 **Batch** | Generación masiva (2-10 prompts a la vez) |
| 🎨 **Previsualizar** | Boceto rápido vía Pollinations |
| ⚡ **Modo Brief** | Optimización para anuncios/concursos |

## 📋 Gestión de datos

- **🌟 Estrellas** — prompts que dieron buenos resultados (con nota y modelo)
- **⭐ Favoritos** — tus prompts marcados
- **📋 Historial** — últimos 100 prompts generados
- **🧑 Personajes** — descripciones reutilizables
- **🔗 LoRAs** — trigger words guardadas
- **📐 Plantillas** — configuraciones completas (modo + modelo + estilos + ratio)
- **💾 Backup automático semanal** — zip de tus datos cada 7 días en `~/.arquitecto_prompts/backups/`
- **📤 Exportar** a `.txt`, `.csv` o formato CLI Midjourney/Grok

## 🎯 Adaptación inteligente

- **Por modelo**: cada modelo tiene specs (sampler, CFG, steps, max_chars, negative) que se inyectan automáticamente al LLM. Si usas Kling 3.0, el LLM SABE las reglas de Kling 3.0.
- **Por formato**: detecta si el modelo usa tags SD o lenguaje natural y fuerza el formato correcto.
- **Por destino**: Instagram, TikTok, YouTube, Anthum, Freepik, etc. — cada destino adapta el prompt (ratio, estilo, gancho).
- **ComfyUI + Turbo**: detecta automáticamente y elimina pesos numéricos `(tag:1.2)` que rompen los modelos Turbo.
- **Negative inteligente**: añade NEGATIVE PROMPT solo si el modelo lo soporta.

## 🆕 Novedades v1.0

- ✅ **FIX**: ventanas hijas (Copiloto, Batch, Personajes...) ahora salen siempre AL FRENTE.
- ✅ **NEW**: indicador visual del proveedor LLM activo (botón 🔑 verde si OK, ámbar si falta key).
- ✅ **NEW**: splash de carga al arrancar.
- ✅ **NEW**: toast in-app no bloqueante (`self.show_toast()`).
- ✅ **NEW**: atajo `Ctrl+Enter` desde el textarea = generar prompt.
- ✅ **NEW**: backup automático semanal en zip.
- ✅ **NEW**: header responsive (modo compacto en ventanas estrechas).
- ✅ **NEW**: wizard inicial con botón "🧪 Test conexión" para validar la key real.
- ✅ **NEW**: cierre limpio que cierra ventanas hijas antes de destruir la principal.
- 🧹 **CLEAN**: eliminado código duplicado entre `app.py` y `ui_builders.py`.
- 🧹 **CLEAN**: 9 referencias muertas al parámetro `modelo_llm` eliminadas.

## 🛠 Instalación

### Requisitos
- **Python 3.10 o superior**
- Conexión a internet (para las APIs)
- Windows / macOS / Linux

### Setup rápido

```bash
git clone https://github.com/tu-usuario/gprompt-studio.git
cd gprompt-studio
pip install -e .
python main.py
```

Para instalar todas las dependencias opcionales (Claude, keyring, visión, etc.):

```bash
pip install -e ".[all]"
```

La primera vez se abrirá un **wizard de configuración** para introducir tus API keys. Puedes usar el botón **🧪 Test conexión** para verificar que tu key funciona antes de empezar.

### API Keys

Las keys se guardan de forma **segura** en este orden de prioridad:

1. **Windows Credential Manager / macOS Keychain / Secret Service** (vía `keyring` si está instalado)
2. `~/.arquitecto_prompts/keys.json` (fallback)
3. Variables de entorno desde `.env`

Para usar el almacenamiento seguro:
```bash
pip install keyring
```

### Ollama (modo local, sin internet)

```bash
# Instalar desde ollama.com
ollama run llama3.1
ollama pull llava       # para visión
```

### Dependencias opcionales

```bash
# Soporte Claude (Anthropic)
pip install anthropic

# Grabación de vídeo de sesión (modo tutorial)
pip install mss imageio[ffmpeg] numpy

# Almacenamiento seguro de keys
pip install keyring

# O todo de una vez
pip install -e ".[all]"
```

## 📁 Estructura del proyecto

```
gprompt-studio/
├── main.py              # Punto de entrada
├── app.py               # ArquitectoApp (clase principal)
├── api_clients.py       # 14 proveedores LLM (patrón Provider)
├── workers.py           # DeepSeekWorker + VisionChain
├── persistence.py       # DataStore con escrituras atómicas
├── prompts.py           # System prompts por modo/modelo
├── config.py            # MODEL_SPECS, plataformas, estilos
├── logging_utils.py     # @log_operation decorator
├── theme.json           # Tema customtkinter (dark/light)
├── modules/             # 40 servicios: UI, IA, datos, Avatar, i18n…
│   ├── core.py          # Workers, comandos, estado
│   ├── ui_builders.py   # Construcción UI
│   ├── i18n.py          # Bilingüe ES/EN (~1400 traducciones)
│   ├── dashboard.py     # Panel de estadísticas y logros
│   ├── avatar_*.py      # Generador de datasets LoRA (4 módulos)
│   └── …               # (ver docs/ESTRUCTURA.md para el árbol completo)
├── data/                # JSONs: specs de modelos, estilos, plantillas
└── tests/               # 760 tests pytest
```

## 🧪 Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v   # → 760 passed
```

## ⌨ Atajos de teclado (29 registrados — `Ctrl+?` muestra la lista completa)

| Atajo | Acción |
|-------|--------|
| `Ctrl+Enter` | Generar prompt |
| `Ctrl+Shift+Enter` | Variaciones x3 |
| `Alt+Enter` | Quick Generate |
| `Ctrl+I` | Ideas creativas |
| `Ctrl+S` / `Ctrl+Shift+S` | Guardar favorito / estrella |
| `Ctrl+F` | Búsqueda global |
| `Ctrl+Shift+R` | Refinar prompt |
| `Ctrl+Shift+O` | Optimizador en bucle |
| `Ctrl+Shift+D` | Abrir Dashboard |
| `Alt+1/2/3` | Modo imagen / vídeo / audio |
| `Ctrl+?` | Mostrar todos los atajos |
| `F11` | Pantalla completa |
| `Escape` | Cerrar popup activo |

## 🔒 Seguridad

- El `.env` está en `.gitignore` por defecto.
- Keys guardadas en keyring del SO si está disponible.
- Escrituras atómicas (tmp + rename) en TODOS los archivos JSON para prevenir corrupción.
- Auto-recuperación de `preferencias.json` corrupto al arrancar (con backup `.bak`).

## 🐛 Reportar bugs

Si algo no funciona, revisa el log en:
- Windows: `%USERPROFILE%\.arquitecto_prompts\logs\gprompt.log`
- macOS/Linux: `~/.arquitecto_prompts/logs/gprompt.log`

---

**Creado por [Gustaafvito](https://github.com/Gustaafvito)** ·
[Instagram](https://www.instagram.com/gustaafvito.creador.ia) ·
[TikTok](https://www.tiktok.com/@gustaafvito.creador.ia) ·
[YouTube](https://www.youtube.com/@GustaafvitocreadorIA)

Licencia MIT.
