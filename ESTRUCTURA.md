# 🧠 G-Prompt Studio — Estructura del proyecto

> Aplicación de escritorio para generar, gestionar y optimizar prompts de IA
> (imagen, vídeo, audio). Documento técnico para mantenedores; ver
> [README.md](README.md) para info de usuario.

---

## 📁 Árbol del repo

```
gprompt-studio/
│
├── main.py                # Punto de entrada (parche CTkToolTip, tema, splash) — 215 líneas
├── app.py                 # ArquitectoApp + install_components — 1.599 líneas
├── api_clients.py         # 14 proveedores LLM (patrón Provider, openai lazy) — 721 líneas
├── config.py              # API pública de constantes + carga desde data/*.json — 1.111 líneas
├── persistence.py         # DataStore atómico (tmp + os.replace + fsync) — 352 líneas
├── prompts.py             # System prompts por modo/modelo — 751 líneas
├── workers.py             # DeepSeekWorker + VisionChain (retry backoff) — 525 líneas
├── logging_utils.py       # @log_operation, silent(), silent_call() — 58 líneas
├── theme.json             # Paleta dark/light de customtkinter
├── pyproject.toml         # Config del proyecto (PEP 621)
├── .gitignore
├── README.md              # Doc para usuario
├── ESTRUCTURA.md          # ← este archivo
├── GUIA_ESTILOS.md        # Referencia visual de ~250 estilos
│
├── modules/               # Mixins + componentes + servicios auxiliares
│   ├── __init__.py        # Re-export público + install_components
│   ├── core.py            # Workers, comandos, estado — 2.799 líneas
│   ├── ui_builders.py     # Construcción de UI — 1.923 líneas
│   ├── tools_creative.py  # Moodboard, ADN, Negative Builder — 2.442 líneas
│   ├── tools_workflow.py  # Macros, A/B Testing, Cron, Proyectos — 1.937 líneas
│   ├── tools_analysis.py  # Stats, Scoring, Auto-improve — 1.309 líneas
│   ├── data_mgmt.py       # Historial, favoritos, plantillas — 1.335 líneas
│   ├── backup_export.py   # Backup, restore, CSV, Export CLI — 476 líneas
│   ├── dialogs.py         # API Keys, Dashboard, Theme — 1.887 líneas
│   ├── windows.py         # Ventanas auxiliares (Personajes, LoRAs…) — 849 líneas
│   ├── gprompt_window.py  # Wrapper de CTkToplevel — 76 líneas
│   ├── components.py      # 8 componentes que delegan a app — 99 líneas
│   ├── event_bus.py       # Pub/sub singleton — 98 líneas
│   ├── preview_service.py # Preview vía Pollinations — 82 líneas
│   └── comfyui_exporter.py# Exportador ComfyUI workflow — 232 líneas
│
├── config/
│   └── plantillas_default.json   # Plantillas por defecto (load-bearing)
│
├── data/                  # Datos extraídos de config.py en Fase 3 (cargados al import)
│   ├── model_specs_imagen.json   # 118 modelos de imagen
│   ├── model_specs_video.json    # 15 modelos de vídeo
│   ├── model_specs_audio.json    # 10 modelos de audio
│   ├── biblioteca_ejemplos.json  # 10 ejemplos para nuevos usuarios
│   ├── estilos_grupos.json       # 13 grupos / ~257 estilos
│   └── estilo_negativo_auto.json # 74 mapeos estilo → negativos
│
└── tests/                 # 4 suites pytest
    ├── __init__.py
    ├── conftest.py
    ├── test_api_clients.py
    ├── test_config.py
    ├── test_persistence.py
    └── test_workers.py
```

**Total**: ~21.000 líneas de Python.

---

## 🏗 Arquitectura

### Composición vs. herencia

`ArquitectoApp` hereda de 8 mixins (compatibilidad histórica) **y además** instala 8 componentes vía `install_components(self)` que delegan al app vía `__getattr__`:

```python
class ArquitectoApp(ctk.CTk, *MIXINS):
    def __init__(self):
        super().__init__()
        install_components(self)
        # Ahora ambas formas funcionan:
        self.cmd_moodboard()          # vía mixin
        self.creative.cmd_moodboard() # vía componente delegado
```

| Componente | Mixin equivalente |
|---|---|
| `self.core` | `CoreMixin` |
| `self.ui` | `UIBuildersMixin` |
| `self.creative` | `ToolsCreativeMixin` |
| `self.workflow` | `ToolsWorkflowMixin` |
| `self.analysis` | `ToolsAnalysisMixin` |
| `self.data` | `DataMgmtMixin` |
| `self.backup` | `BackupExportMixin` |
| `self.dialogs` | `DialogsMixin` |

**Regla:** código nuevo debe usar `self.componente.X`. Las refs `self.X` se mantienen para no reescribir 2.640 referencias internas en los mixins.

### Patrón Provider (LLMs)

`api_clients.py` define `BaseLLMProvider` con `completar()` y `disponible()`. Cada proveedor implementa esa interfaz:

```
ArquitectoApp
  └── self.clients (APIClients)
        └── self.providers[pid] (BaseLLMProvider)
              ├── OpenAICompatibleProvider  → DeepSeek, OpenRouter, Groq, OpenAI, Mistral, xAI…
              ├── OllamaProvider            → Ollama local
              ├── GeminiProvider            → Google Gemini
              └── ClaudeProvider            → Anthropic Claude
```

**14 proveedores** soportados (ver [LLM_PROVIDERS en api_clients.py](api_clients.py)). Añadir uno = 2 métodos + entrada en el registro.

`openai` se importa de forma **lazy** (`OPENAI_DISPONIBLE` flag): si no está instalado, los providers OpenAI-compatible lanzan `ImportError` explicativo, no peta al cargar.

### Carga de datos desde JSON

Los specs y datasets grandes viven en `data/*.json` y se cargan al import vía `_load_json_data()` en config.py:

```python
MODEL_SPECS        = _load_json_data("model_specs_video.json")
MODEL_SPECS_IMAGEN = _load_json_data("model_specs_imagen.json")
MODEL_SPECS_AUDIO  = _load_json_data("model_specs_audio.json")
ESTILOS_GRUPOS     = _load_json_data("estilos_grupos.json")
ESTILO_NEGATIVO_AUTO = _load_json_data("estilo_negativo_auto.json")
BIBLIOTECA_EJEMPLOS  = _load_json_data("biblioteca_ejemplos.json")
```

Beneficio: añadir un modelo nuevo es editar JSON, no Python. La **API pública de config.py** (todas las constantes y funciones `get_*_specs`) está intacta — los imports siguen siendo `from config import MODEL_SPECS_IMAGEN, …`.

### Ventanas hijas — GPromptWindow

Todas las ventanas secundarias usan `GPromptWindow` (extiende `CTkToplevel`). Comportamiento al crear:

- `resizable(True, True)`
- `attributes("-toolwindow", False)`
- `bring_to_front` diferido 50ms (lift + topmost momentáneo 250ms)
- Bind `<F11>` toggle fullscreen + `<Escape>` salir fullscreen
- `transient()` sobreescrito como **no-op**: en Windows, transient() oculta los botones minimize/maximize. Compensamos lift+focus.

Sustituyó al monkey-patching global de `ctk.CTkToplevel.__init__` y `.transient()` (Fase 4).

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

**Threading:** todas las llamadas a IA en `threading.Thread(daemon=True)`. UI updates con `self.after(0, callback)` para volver al hilo principal de Tk.

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
| `keys.json` | API keys (fallback si no hay keyring) |
| `borrador.txt` | Borrador auto-guardado cada 30s |
| `backups/auto-AAAAMMDD.zip` | Backups automáticos semanales (máx 10) |
| `logs/gprompt.log` | Log de la app |

### Almacenamiento de API keys (orden de prioridad)

1. **OS keyring** (Windows Credential Manager / macOS Keychain / Linux Secret Service)
2. `~/.arquitecto_prompts/keys.json` (fallback)
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

**48 tests** (46 pasan, 2 con drift conocido en `test_persistence.py`):

| Suite | Cobertura |
|---|---|
| `test_api_clients.py` | Proveedores LLM, fábrica `get_provider()`, interfaces |
| `test_config.py` | Helpers (`es_separador`, `get_model_specs`, etc.) |
| `test_persistence.py` | DataStore CRUD, atomic writes, preferencias |
| `test_workers.py` | Token counting, parser de ideas, detección idioma |

---

## 🪵 Logging

Todos los módulos usan `logger = logging.getLogger(__name__)` a nivel módulo. Los 140 `except: pass` originales se convirtieron en `except Exception as _e: logger.debug(f"[silent] {_e}")` — silenciosos en runtime normal, diagnosticables con `LOG_LEVEL=DEBUG`.

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
2. **Datos en JSON, lógica en Python** — `MODEL_SPECS_*`, `ESTILOS_*` y biblioteca viven en `data/*.json`.
3. **Composición progresiva** — mixins heredados + componentes (`self.creative.X`) que delegan al app. Migración sin romper.
4. **Lazy imports** — `openai`, `google-genai`, `anthropic` solo si están instalados. La app arranca sin ellos.
5. **Escritura atómica** — `tmp + fsync + os.replace()` en TODOS los `.json` del usuario.
6. **Threading + after** — IA en threads daemon; UI updates con `self.after(0, fn)`.
7. **Fallback chains** — VisionChain: Gemini → Ollama → OpenRouter.
8. **Validación + auto-recuperación** — JSONs corruptos se renombran a `.corrupt` y se recrean.
9. **Logging diagnosticable** — `except: pass` está prohibido; usar `logger.debug` o helpers de `logging_utils`.
10. **UX no bloqueante** — `show_toast()` en vez de `messagebox` cuando es posible.

---

## 🔑 Notas para mantenedores

1. **NO añadir métodos directamente a `app.py`.** Cada método nuevo va en su mixin (`modules/X.py`). Excepciones: helpers globales como `open_child_window`, `show_toast`, `_actualizar_indicador_proveedor`, `__init__`, `_setup_wizard`.

2. **Nuevas ventanas hijas:** instanciar `GPromptWindow(self)` directamente o usar `self.open_child_window(title, size)`. **NO** usar `ctk.CTkToplevel` (perdería el bring-to-front).

3. **Self vs componente:** dentro de un mixin sigue siendo `self.X`. En código nuevo (especialmente nuevas features), preferir `self.componente.X` para hacer explícita la dependencia.

4. **`self.deepseek`** es un `DeepSeekWorker` que delega en `self.clients.get_active_provider()`. NO pasarle `modelo_llm=` (el provider activo se resuelve solo).

5. **`self.store`** es un `DataStore` con escrituras atómicas. Toda persistencia pasa por aquí.

6. **`self.llm_var`** es un `ctk.StringVar` con la **LABEL** del LLM activo (no el id). Para resolver al id usar `self._llm_label_to_id`.

7. **Notificar al usuario:** `self.show_toast(msg, color)` para feedback no bloqueante; `messagebox` solo para confirmaciones importantes (borrar, sobrescribir).

8. **Theme switching** no destruye widgets — usa `_apply_theme_colors()` para actualizar en caliente.

9. **`.env` NO se commitea** — está en `.gitignore`. Lo mismo para `keys.json` y archivos de usuario.

10. **Añadir un modelo nuevo:** editar `data/model_specs_imagen.json` (o `_video.json` / `_audio.json`). Re-arrancar la app. Sin tocar Python.

---

*Documento mantenido manualmente. Si tocas la arquitectura, actualiza este archivo.*
