# 🧠 G-Prompt Studio v1.0.1

> Suite profesional de ingeniería de prompts para IA generativa.
> Convierte ideas en instrucciones técnicas de alta precisión para **imagen, vídeo y audio**.

[![Web](https://img.shields.io/badge/web-gustaafvito.com-orange.svg)](https://gustaafvito.com/)
[![CI](https://github.com/Gustaafvito/gprompt-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/Gustaafvito/gprompt-studio/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.1-brightgreen.svg)](https://github.com/Gustaafvito/gprompt-studio)

**Español** · [English](README.en.md)

<p align="center">
  <a href="https://github.com/Gustaafvito/gprompt-studio/releases/download/v1.0.1/GPromptStudio-Setup-1.0.1.exe">
    <img src="https://img.shields.io/badge/Descargar%20para%20Windows-v1.0.1-0c9ee6?style=for-the-badge&logo=windows&logoColor=white" alt="Descargar G-Prompt Studio para Windows">
  </a>
</p>

<p align="center">
  <sub>118 MB &middot; Windows 10 u 11 de 64 bits &middot; no necesita Python ni permisos de administrador<br>
  &iquest;Prefieres no instalar nada? <a href="https://github.com/Gustaafvito/gprompt-studio/releases/latest">Versi&oacute;n portable y hashes SHA-256</a></sub>
</p>


---

![La pantalla principal de G-Prompt Studio: una idea en español convertida en prompt para GPT Image 2.5 Sunburst, con positivo, negativo y ajustes recomendados](docs/capturas/01-pantalla-principal.png)

<p align="center"><em>Una idea en una frase → el prompt que ese modelo concreto entiende, con su negativo y sus ajustes.</em></p>

---

## Por qué existe

Empecé a generar imágenes y vídeo y me encontré con lo mismo una y otra vez:
cada modelo quiere el prompt de una forma. Flux pide prosa, SDXL pide tags,
unos aceptan prompt negativo y otros lo ignoran, cada uno tiene su límite de
caracteres y su sampler. Tenía las reglas repartidas entre notas, pestañas
abiertas y capturas, y aun así escribía el prompt para el modelo equivocado.

No encontré un sitio donde estuviera todo junto, así que lo hice. G-Prompt
Studio es esas notas convertidas en herramienta: escribes la idea en
castellano, eliges el modelo, y sale el prompt con **sus** reglas.

---


## Funciona

Los prompts de mis **dos últimos premios en SeaArt** los generó esta
herramienta — los dos en Wan 3.0, en septiembre de 2026:

- [«¡Esa cosa flotante en el cielo me da escalofríos!»](https://www.seaart.ai/postDetail/daff1kle878c73923gj0)
- [«¡Un castillo de chatarra de niño es asombroso!»](https://www.seaart.ai/postDetail/daen215e878c73fpeong)

Si abres cualquiera de los dos verás el prompt entero: tres planos
coreografiados, dirección de cámara, paleta de color y diseño de audio. Eso
es lo que la herramienta escribe cuando le dices que el destino es Wan 3.0.

---

## ✨ Qué hace

G-Prompt Studio toma una idea simple ("una chica con pelo plateado en un bosque mágico") y la convierte en un prompt profesional optimizado para el modelo concreto que vas a usar — con sus reglas, sus tags, sus límites, su sampler recomendado y, si aplica, su prompt negativo.

**271 modelos repartidos en 13 plataformas**, cada uno con sus reglas propias:

| Modo | Modelos | Plataformas |
|------|---------|-------------|
| 🖼 **Imagen** | **164** | SeaArt/Tensor.Art (127) · Magnific (31) · GPT Image (4) · Higgsfield (4) · Grok (3) |
| 🎬 **Vídeo** | **99** | SeaArt Video (91) · Pollo AI (7) · Kling AI (5) · Grok (2) · Veo/Gemini (2) · Higgsfield (1) |
| 🎵 **Audio** | **8** | Suno (5) · SeaArt Audio (4) · Udio (2) — con letras, estilo, emoción, voz e idioma |

Y **encima de esos, los tuyos**: si usas ComfyUI no cuentan aquí porque son
distintos en cada ordenador.

Entre ellos: FLUX.1, Z-Image, Qwen Image 3.0 / 3.0 Pro, Illustrious, Pony, Nano Banana,
Wan 3.0 y Wan 3.0 Prime, Kling, Seedance, Hailuo, PixVerse, Vidu, Sora 2, Veo, Suno v5.5…
Y **333 estilos** agrupados por familia.

Los modelos locales de **ComfyUI se detectan solos**: apunta a tu carpeta y la herramienta
clasifica cada checkpoint por familia para aplicarle el formato de prompt correcto.

## 🧠 Multi-Cerebro (13 proveedores)

Conecta con cualquiera de estos proveedores con una sola key. Los once de
nube se verificaron uno a uno con keys reales: catálogo en vivo y una
llamada de verdad a cada modelo del desplegable. Si un modelo desaparece
del catálogo de su proveedor, la app lo oculta sola.

| Proveedor | Tipo | Coste |
|-----------|------|-------|
| 🥈 **DeepSeek V4** | Pago | ~€0.14/1M tokens |
| 💎 **Claude (Anthropic)** | Pago | ~€2.40/1M tokens |
| 💎 **Fireworks AI** | Pago | Modelos open-source rápidos |
| 🏆 **Google Gemini** | Gratis | 15 rpm |
| 🏆 **Groq** | Gratis | 14.400 req/día |
| 🏆 **LM Studio** | Local | Servidor OpenAI-compatible |
| 💎 **Mistral** | Pago | Modelos europeos |
| 🏆 **Ollama** | Local | Sin internet, sin coste |
| 💎 **OpenAI** | Pago | GPT-6 Astra, familia 5.x y 4.x |
| 🥈 **OpenRouter** | Pago | 100+ modelos con UNA key |
| 💎 **Perplexity** | Pago | Modelos con búsqueda en tiempo real |
| 💎 **Together AI** | Pago | Modelos open-source y propietarios |
| 💎 **xAI (Grok)** | Pago | Grok 4.6, 4.5, 4.3 — hasta 1M de contexto |

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
| 👋 **Bienvenida** | Al primer arranque sin ninguna key: te guía hasta un cerebro gratis o local |

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

## 🆕 Novedades (septiembre 2026)

**Modelos y plataformas**
- Wan 3.0 y Wan 3.0 Prime, Qwen Image 3.0 y 3.0 Pro (SeaArt).
- Alta de Pollo AI y Higgsfield; modelos que faltaban, enganchados a su plataforma.
- +75 estilos para equilibrar los grupos más flacos (hasta 333).
- Los catálogos viven en `data/*.json` y se pueden **sobrescribir desde
  `~/.arquitecto_prompts/data/`** sin recompilar nada.

**Cerebro**
- **LM Studio** como proveedor de primera clase: autodetecta el modelo cargado.
- Selector de modelo para LM Studio y Ollama, que ya no ofrece modelos de
  *embeddings* (no sirven como cerebro).
- Reintento automático cuando el LLM agota `max_tokens` y devuelve vacío.
- Los reintentos del SDK ya no se multiplican con los del worker.

**Fiabilidad**
- Aviso cuando el LLM entrega **menos prompts de los pedidos** (antes fallaba en silencio).
- El prompt final ya no arrastra el eco de las instrucciones.
- Una carpeta de ComfyUI ilegible ya no te deja sin ningún modelo local.
- Cerrar la ventana a mitad de una generación ya no ensucia el log.
- Las API keys antiguas se migran solas a DPAPI.
- Selector de modelos sin lag al abrir y buscar.

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

### La forma normal: descargar e instalar

Ve a [**Releases**](https://github.com/Gustaafvito/gprompt-studio/releases),
baja `GPromptStudio-Setup-1.0.1.exe` y ábrelo. **No hace falta Python ni
instalar dependencias**: va todo dentro.

- Windows 10 u 11 de 64 bits
- No pide permisos de administrador — se instala en tu perfil de usuario
- Windows mostrará un aviso de SmartScreen porque el ejecutable no está
  firmado: *Más información* → *Ejecutar de todas formas*. En la página del
  release está el hash SHA-256 y el análisis de VirusTotal para que lo
  compruebes tú

También hay una **versión portable** de un solo fichero, sin instalar.

### Desde el código (desarrollo)

Solo si quieres tocar el código o correrlo en macOS/Linux. Necesitas
**Python 3.10 o superior**:

```bash
git clone https://github.com/Gustaafvito/gprompt-studio.git
cd gprompt-studio
pip install -e .
python main.py
```

Para todas las dependencias opcionales (Claude, keyring, visión…):

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
├── api_clients.py       # 13 proveedores LLM (patrón Provider)
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
└── tests/               # 1319 tests pytest
```

## 🧪 Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v   # → 1319 passed
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

## Capturas

<table>
<tr>
<td width="50%">

![El catálogo de modelos con su buscador, agrupado por familias](docs/capturas/02-catalogo-modelos.png)

**271 modelos con ficha propia**, agrupados por familia y con buscador. Si
usas ComfyUI, los tuyos aparecen solos.

</td>
<td width="50%">

![La paleta de comandos abierta sobre la aplicación, con las herramientas filtrables](docs/capturas/03-paleta-comandos.png)

**`Ctrl+K`** y escribe lo que buscas. Todas las herramientas a una tecla, sin
bucear por los menús.

</td>
</tr>
</table>

---

## Dudas, fallos e ideas

- **¿Algo no funciona?** Abre un
  [issue](https://github.com/Gustaafvito/gprompt-studio/issues). Cuenta qué
  hacías, qué esperabas y qué pasó, y adjunta el log —
  `%USERPROFILE%\.arquitecto_prompts\logs\gprompt.log`. Con el log se
  arregla en la mitad de tiempo.
- **¿Una duda o una idea?**
  [Discussions](https://github.com/Gustaafvito/gprompt-studio/discussions).
  Se responden en público a propósito: así la siguiente persona con la misma
  duda la encuentra sin preguntar.
- **¿Un fallo de seguridad?** No lo abras como issue público. Escribe por
  privado desde [gustaafvito.com](https://gustaafvito.com/) y dame margen
  para corregirlo antes de que sea público.

---

**Creado por [Gustaafvito](https://gustaafvito.com/)** ·
[Web](https://gustaafvito.com/) ·
[GitHub](https://github.com/Gustaafvito) ·
[Instagram](https://www.instagram.com/gustaafvito.creador.ia) ·
[TikTok](https://www.tiktok.com/@gustaafvito.creador.ia) ·
[YouTube](https://www.youtube.com/@GustaafvitocreadorIA)

## Licencia

Apache License 2.0 — ver [LICENSE](LICENSE) y [NOTICE](NOTICE).

**Copyright 2026 Gustavo Luis Sánchez Escobar** «Gustaafvito».

Puedes usar, modificar y redistribuir este software, incluso con fines
comerciales. A cambio, la licencia te pide tres cosas: conservar el aviso de
copyright y el fichero NOTICE, indicar los cambios que hagas, y no usar el
nombre del proyecto para dar a entender que una versión modificada es la
original.
