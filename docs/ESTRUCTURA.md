# 🧠 G-Prompt Studio — Estructura del proyecto

> Aplicación de escritorio para generar, gestionar y optimizar prompts de IA
> (imagen, vídeo, audio). Documento técnico para mantenedores; ver
> [README.md](README.md) para info de usuario.

---

## 📁 Árbol del repo

```
gprompt-studio/
│
├── main.py                # Punto de entrada (parche CTkToolTip, tema, splash)
├── app.py                 # ArquitectoApp + install_components — 2.643 líneas
├── api_clients.py         # 14 proveedores LLM (patrón Provider, openai lazy) — 1.198 líneas
├── config.py              # API pública de constantes + carga desde data/*.json — 1.697 líneas
├── persistence.py         # DataStore atómico (tmp + os.replace + fsync)
├── prompts.py             # System prompts por modo/modelo — 751 líneas
├── workers.py             # DeepSeekWorker + VisionChain (retry backoff)
├── logging_utils.py       # @log_operation, silent(), silent_call()
├── theme.json             # Paleta dark/light de customtkinter
├── pyproject.toml         # Config del proyecto (PEP 621) + Ruff
├── .pre-commit-config.yaml # Hooks: ruff, whitespace, EOF, line-endings, etc.
├── .gitignore
├── README.md              # Doc para usuario (raíz)
├── HANDOFF.md             # Doc viva del proyecto (raíz)
├── GUIA_ESTILOS.md        # Referencia visual de ~250 estilos (raíz, va en el .exe)
│
├── docs/                  # Documentación de desarrollo
│   ├── ESTRUCTURA.md      # ← este archivo
│   ├── BUILD.md           # Cómo generar el .exe / instalador
│   ├── AGREGAR_MODELO.md  # Guía para añadir/auditar modelos
│   └── handoff-historico.md # Histórico de sesiones 6-19
│
├── modules/               # 40 servicios — ver tabla abajo
│   ├── __init__.py        # Re-export público
│   ├── core.py            # Workers, comandos, estado — 1.250 líneas
│   ├── ui_builders.py     # Construcción de UI — 1.996 líneas
│   ├── tools_analysis.py  # Stats, Scoring, Auto-improve — 2.188 líneas
│   ├── tools_creative.py  # Moodboard, ADN, Negative Builder — 2.033 líneas
│   ├── tools_workflow.py  # Macros, A/B Testing, Cron, Proyectos — 1.442 líneas
│   ├── data_mgmt.py       # Historial, favoritos, plantillas — 1.584 líneas
│   ├── dashboard.py       # Panel stats, logros, avisos — 1.518 líneas
│   ├── windows.py         # Ventanas auxiliares (Personajes, LoRAs…) — 1.411 líneas
│   ├── dialogs.py         # Modales: keys, tema, idioma — 835 líneas
│   ├── multiprompt.py     # Moodboard / Story / Board / Walk — 1.198 líneas
│   ├── modo_cliente.py    # Brief profesional + 5 propuestas — 875 líneas
│   ├── backup_export.py   # Backup, restore, CSV, búsqueda global — 820 líneas
│   ├── prompts_inyeccion.py # Inyección de specs por modelo — 1.075 líneas
│   ├── ui_footer.py       # Barra de estado + footer — 972 líneas
│   ├── json_prompt.py     # Import/export JSON pro (Veo/Sora/Kling) — 729 líneas
│   ├── adn_visual.py      # ADN Visual extraído de imagen — 673 líneas
│   ├── sesion_video.py    # Grabar / exportar / tutorial-mode — 560 líneas
│   ├── avatar_config.py   # Config del generador de datasets LoRA — 797 líneas
│   ├── avatar_ui.py       # UI del Avatar — 682 líneas
│   ├── avatar_prompts.py  # Prompts del Avatar — 614 líneas
│   ├── avatar_generator.py# Generador de prompts del Avatar — 333 líneas
│   ├── i18n.py            # Bilingüe ES/EN (~1.650 traducciones) — 1.704 líneas
│   ├── tutorial.py        # Tutorial interactivo — 449 líneas
│   ├── ab_testing.py      # A/B Testing 2x2 — variaciones comparadas
│   ├── workers_ia.py      # Threads de generación / visión / traducción — 430 líneas
│   ├── ui_events.py       # Event handlers de los combos superiores — 475 líneas
│   ├── atajos_ayuda.py    # Atajos de teclado + ventana de ayuda — 373 líneas
│   ├── refinamiento.py    # Refinamiento iterativo + diff visual — 346 líneas
│   ├── glosario.py        # Glosario de términos — 246 líneas
│   ├── style_guide.py     # Selector de estilos por modo — 378 líneas
│   ├── preview_pollinations.py # Preview rápido vía Pollinations — 535 líneas
│   ├── searchable_dropdown.py  # Dropdown con buscador + familias colapsables — 193 líneas
│   ├── clarity_hints.py   # Sugerencias de claridad (palabras polisémicas) — 170 líneas
│   ├── prompt_helpers.py  # Helpers reutilizables de prompt — 201 líneas
│   ├── prompt_logic.py    # Lógica de detección (turbo, familia, ComfyUI) — 127 líneas
│   ├── components.py      # Componentes que delegan a app — 744 líneas
│   ├── event_bus.py       # Pub/sub singleton — 97 líneas
│   ├── tooltip.py         # Wrapper CTkToolTip con fallback — 94 líneas
│   └── gprompt_window.py  # Wrapper de CTkToplevel — 78 líneas
│
├── data/                  # Datos cargados por config.py + app.py
│   ├── model_specs_imagen.json   # ~164 modelos de imagen (93 vigentes)
│   ├── model_specs_video.json    # 72 motores de vídeo por familia
│   ├── model_specs_audio.json    # 11 modelos de audio
│   ├── plantillas_default.json   # Plantillas por defecto
│   ├── biblioteca_ejemplos.json  # 27 ejemplos para nuevos usuarios
│   ├── estilos_grupos.json       # Grupos de estilos
│   ├── estilo_negativo_auto.json # Mapeos estilo → negativos
│   ├── glosario.json             # Glosario en español
│   ├── glosario.en.json          # Glosario en inglés
│   ├── tutorial.json             # Tutorial en español (42 pasos)
│   └── tutorial.en.json          # Tutorial en inglés
│
├── tests/                 # 760 tests pytest — 1 suite por módulo
│
├── gprompt-studio.spec         # PyInstaller spec (onedir)
├── gprompt-studio-onefile.spec # PyInstaller spec (onefile)
├── build.py               # Script de build (onedir / onefile / installer)
├── build_release.py       # Build limpio desde HEAD git
└── installer.iss          # Inno Setup script (instalador Windows)
```

**Total**: ~38.000 líneas de Python.

---

## 🏗 Arquitectura

### Composición completa (patrón A1)

`ArquitectoApp` hereda solo de **`CoreMixin`** (foundation mínimo) y accede
al resto de funcionalidad a través de **servicios instanciados en `__init__`**:

```python
class ArquitectoApp(ctk.CTk, CoreMixin):
    def __init__(self):
        super().__init__()
        self.ui        = UIBuildersService(self)
        self.creative  = ToolsCreativeService(self)
        self.analysis  = ToolsAnalysisService(self)
        self.dashboard = DashboardService(self)
        self.inyeccion = PromptsInyeccionService(self)
        # … etc.
```

Los servicios reciben `app` como argumento y acceden a la UI vía `self.app.<attr>`.
Las referencias `self.X` legacy siguen funcionando porque `CoreMixin` las resuelve;
código nuevo usa siempre `self.<servicio>.metodo()`.

**Regla para código nuevo:** NO añadir métodos a `app.py`. Cada método nuevo
va en su servicio (`modules/X.py`). Instanciar en `__init__` de `ArquitectoApp`.

### Patrón Provider (LLMs)

`api_clients.py` define `BaseLLMProvider` con `completar()` y `disponible()`.
Cada proveedor implementa esa interfaz:

```
ArquitectoApp
  └── self.clients (APIClients)
        └── self.providers[pid] (BaseLLMProvider)
              ├── OpenAICompatibleProvider  → DeepSeek, OpenRouter, Groq, OpenAI, Mistral, xAI…
              ├── OllamaProvider            → Ollama local
              ├── GeminiProvider            → Google Gemini
              └── ClaudeProvider            → Anthropic Claude
```

**14 proveedores** soportados (ver `LLM_PROVIDERS` en `api_clients.py`).
Añadir uno = 2 métodos + entrada en el registro.

`openai` se importa de forma **lazy** (`OPENAI_DISPONIBLE` flag): si no
está instalado, los providers OpenAI-compatible lanzan `ImportError`
explicativo, no peta al cargar.

### Carga de datos desde JSON

Los specs y datasets grandes viven en `data/*.json` y se cargan al
import vía `_load_json_data()` en config.py:

```python
MODEL_SPECS         = _load_json_data("model_specs_video.json")
MODEL_SPECS_IMAGEN  = _load_json_data("model_specs_imagen.json")
MODEL_SPECS_AUDIO   = _load_json_data("model_specs_audio.json")
ESTILOS_GRUPOS      = _load_json_data("estilos_grupos.json")
ESTILO_NEGATIVO_AUTO = _load_json_data("estilo_negativo_auto.json")
BIBLIOTECA_EJEMPLOS = _load_json_data("biblioteca_ejemplos.json")
```

Beneficio: añadir un modelo nuevo es editar JSON, no Python. La **API
pública de config.py** (todas las constantes y funciones `get_*_specs`)
está intacta — los imports siguen siendo
`from config import MODEL_SPECS_IMAGEN, …`.

### Ventanas hijas — GPromptWindow

Todas las ventanas secundarias usan `GPromptWindow` (extiende
`CTkToplevel`). Comportamiento al crear:

- `resizable(True, True)`
- `attributes("-toolwindow", False)`
- `bring_to_front` diferido 50ms (lift + topmost momentáneo 250ms)
- Bind `<F11>` toggle fullscreen + `<Escape>` salir fullscreen
- `transient()` sobreescrito como **no-op**: en Windows, `transient()`
  oculta los botones minimize/maximize. Compensamos con lift+focus.

Sustituyó al monkey-patching global de `ctk.CTkToplevel.__init__` y
`.transient()`.

### Flujo de generación

```
Usuario escribe idea → txt_idea
  └── "Generar Prompt" o Ctrl+Enter → cmd_prompt()
        └── _construir_peticion() inyecta specs del modelo (max_chars, sampler…)
              └── self.deepseek.generar()  ← worker en thread daemon
                    └── self.clients.get_active_provider().completar()
                          └── Retry x3 con backoff exponencial
                                └── API → LLM → respuesta
                                      └── actualizar_salida() (vía self.after)
                                            └── guardar_en_historial()
```

**Threading:** todas las llamadas a IA en `threading.Thread(daemon=True)`.
UI updates con `self.after(0, callback)` para volver al hilo principal de Tk.

---

## 💾 Persistencia

Carpeta: **`~/.arquitecto_prompts/`**

| Archivo | Contenido |
|---|---|
| `historial.json` | Últimos 500 prompts |
| `favoritos.json` | Prompts marcados ⭐ |
| `estrellas.json` | Prompts con nota y modelo |
| `personajes.json` | Personajes guardados |
| `loras.json` | LoRAs con triggers |
| `plantillas.json` | Plantillas (modo + modelo + estilos + ratio) |
| `preferencias.json` | Preferencias de usuario |
| `keys.json` | API keys cifradas (AES-256-CBC, fallback si no hay keyring) |
| `borrador.txt` | Borrador auto-guardado cada 30s |
| `backups/auto-AAAAMMDD.zip` | Backups automáticos semanales (máx 10) |
| `logs/gprompt.log` | Log de la app |

### Almacenamiento de API keys (orden de prioridad)

1. **OS keyring** (Windows Credential Manager / macOS Keychain / Linux Secret Service)
2. `~/.arquitecto_prompts/keys.json` **cifrado AES-256-CBC** con clave derivada
   del hardware (MAC + usuario)
3. Variables de entorno (`.env`)

### Escrituras atómicas

TODOS los `.json` se escriben con el patrón **tmp + `os.replace()`**:

```python
def _guardar(self, nombre):
    path = ARCHIVOS[nombre]
    tmp = str(path) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, str(path))
```

---

## 🧪 Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

**760 tests, 760 passing ✅** — una suite por módulo.

```bash
python -m pytest tests -q   # → 760 passed
```

---

## 🧹 Linting

```bash
pip install -e ".[dev]"
ruff check .
pre-commit install      # hooks automáticos en cada commit
pre-commit run --all-files
```

Reglas activas en `pyproject.toml`: `E, W, F, I, UP` (pycodestyle, pyflakes,
isort, pyupgrade). Conservador inicialmente: varios `F4xx/F8xx` y `E7xx`
están en `ignore` para no bloquear código legacy — se irán activando
gradualmente al ir limpiando.

---

## 🪵 Logging

Todos los módulos usan `logger = logging.getLogger(__name__)` a nivel
módulo. Los `except: pass` originales se convirtieron en
`except Exception as _e: logger.debug(f"[silent] {_e}")` — silenciosos
en runtime normal, diagnosticables con `LOG_LEVEL=DEBUG`.

Helpers en [logging_utils.py](logging_utils.py):
- `@silent_call(operation, default=None)` — decorador
- `with silent(operation):` — context manager
- `@log_operation(operation)` — log inicio/fin con timing

---

## ⌨ Atajos de teclado

| Atajo | Acción |
|---|---|
| `Ctrl+Enter` | Generar prompt |
| `Alt+Enter` | Quick Generate (sin traducción ni NSFW check) |
| `Ctrl+Shift+Enter` | Variaciones x3 |
| `Ctrl+I` | Ideas creativas |
| `Ctrl+Shift+A` | Analizar imagen |
| `Ctrl+Shift+P` | Previsualizar |
| `Ctrl+1` / `Ctrl+2` | Copiar POSITIVE / NEGATIVE |
| `Ctrl+S` / `Ctrl+Shift+S` | Guardar favorito / estrella |
| `Ctrl+F` | Búsqueda global |
| `Ctrl+H` | Modo Focus |
| `Ctrl+D` | Duplicar al historial |
| `Ctrl+P` / `Ctrl+L` | Personajes / LoRAs |
| `Ctrl+R` | Idea aleatoria del historial |
| `Ctrl+T` | Tutorial |
| `Ctrl+E` | Exportar rápido |
| `Ctrl+V` | Pegar inteligente |
| `Alt+1` / `Alt+2` / `Alt+3` | Modo imagen / vídeo / audio |
| `Ctrl+Shift+L` | Cambiar tema dark↔light |
| `Ctrl+Shift+T` | Traducir idea |
| `Ctrl+Shift+N` | Negative Builder |
| `Ctrl+?` | Mostrar todos los atajos |
| `F11` | Pantalla completa |
| `Escape` | Cerrar popup / salir fullscreen |

---

## 📐 Principios de diseño

1. **Provider Pattern** — añadir LLM = 2 métodos + entrada en `LLM_PROVIDERS`.
2. **Datos en JSON, lógica en Python** — `MODEL_SPECS_*`, `ESTILOS_*` y
   biblioteca viven en `data/*.json`.
3. **Composición progresiva** — mixins heredados + componentes
   (`self.creative.X`) que delegan al app. Migración sin romper.
4. **Lazy imports** — `openai`, `google-genai`, `anthropic` solo si
   están instalados. La app arranca sin ellos.
5. **Escritura atómica** — `tmp + fsync + os.replace()` en TODOS los
   `.json` del usuario.
6. **Threading + after** — IA en threads daemon; UI updates con
   `self.after(0, fn)`.
7. **Fallback chains** — VisionChain: Gemini → Ollama → OpenRouter.
8. **Validación + auto-recuperación** — JSONs corruptos se renombran a
   `.corrupt` y se recrean.
9. **Logging diagnosticable** — `except: pass` está prohibido; usar
   `logger.debug` o helpers de `logging_utils`.
10. **UX no bloqueante** — `show_toast()` en vez de `messagebox` cuando
    es posible.

---

## 🔑 Notas para mantenedores

1. **NO añadir métodos directamente a `app.py`.** Cada método nuevo va
   en su mixin (`modules/X.py`). Excepciones: helpers globales como
   `open_child_window`, `show_toast`,
   `_actualizar_indicador_proveedor`, `__init__`, `_setup_wizard`.

2. **Nuevas ventanas hijas:** instanciar `GPromptWindow(self)`
   directamente o usar `self.open_child_window(title, size)`. **NO**
   usar `ctk.CTkToplevel` (perdería el bring-to-front).

3. **Self vs componente:** dentro de un mixin sigue siendo `self.X`. En
   código nuevo (especialmente nuevas features), preferir
   `self.componente.X` para hacer explícita la dependencia.

4. **`self.deepseek`** es un `DeepSeekWorker` que delega en
   `self.clients.get_active_provider()`. NO pasarle `modelo_llm=` (el
   provider activo se resuelve solo).

5. **`self.store`** es un `DataStore` con escrituras atómicas. Toda
   persistencia pasa por aquí.

6. **`self.llm_var`** es un `ctk.StringVar` con la **LABEL** del LLM
   activo (no el id). Para resolver al id usar `self._llm_label_to_id`.

7. **Notificar al usuario:** `self.show_toast(msg, color)` para feedback
   no bloqueante; `messagebox` solo para confirmaciones importantes
   (borrar, sobrescribir).

8. **Theme switching** no destruye widgets — usa `_apply_theme_colors()`
   para actualizar en caliente.

9. **`.env` NO se commitea** — está en `.gitignore`. Lo mismo para
   `keys.json` y archivos de usuario.

10. **Añadir un modelo nuevo:** editar `data/model_specs_imagen.json`
    (o `_video.json` / `_audio.json`). Re-arrancar la app. Sin tocar
    Python.

---

*Documento mantenido manualmente. Si tocas la arquitectura, actualiza
este archivo.*
