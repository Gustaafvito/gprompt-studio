# 🧠 G-Prompt Studio v1.0.9 — Estructura del Proyecto

> Aplicación de escritorio para generar, gestionar y optimizar prompts de IA (imagen, vídeo, audio).
> **Última versión**: v1.0.9 — con biblioteca integrada, headers, dashboard, herramientas creativas.

---

## 📁 Estructura de carpetas

```
gprompt-studio/
│
├── main.py                      # Punto de entrada con splash (~210 líneas)
├── app.py                       # ArquitectoApp (~1.130 líneas tras refactor)
├── api_clients.py               # 9 proveedores LLM (patrón Provider, ~550 líneas)
├── config.py                    # MODEL_SPECS, plataformas, constantes (~2.073 líneas)
├── persistence.py               # DataStore atómico (~210 líneas)
├── prompts.py                   # System prompts (~520 líneas)
├── workers.py                   # DeepSeekWorker + VisionChain (~310 líneas)
├── windows.py                   # Ventanas auxiliares (~800 líneas)
├── state.py                     # AppState centralizado (~40 líneas)
├── gtypes.py                    # TypedDicts (~80 líneas)
├── exceptions.py                # GPromptError + subclases (~30 líneas)
├── logging_utils.py             # @log_operation decorator (~25 líneas)
├── theme.json                   # Paleta dark/light (~507 líneas)
├── requirements.txt             # Dependencias mínimas
├── pyproject.toml               # Configuración del proyecto (PEP 621)
├── .gitignore
├── README.md
├── ESTRUCTURA.md                # Este archivo
│
├── modules/                     # 8 mixins extraídos de app.py
│   ├── __init__.py
│   ├── core.py                  # Workers, comandos, estado (~4.000 líneas)
│   ├── ui_builders.py           # Construcción de UI (~2.400 líneas)
│   ├── tools_creative.py        # Moodboard, ADN, Negative Builder, Paleta (~3.300 líneas)
│   ├── tools_workflow.py        # Macros, A/B Testing, Cron (~2.600 líneas)
│   ├── tools_analysis.py        # Stats, Scoring, Education (~1.600 líneas)
│   ├── data_mgmt.py             # Historial, favoritos, snippets (~1.700 líneas)
│   ├── backup_export.py        # Backup, restore, CSV, Export CLI (~1.100 líneas)
│   └── dialogs.py               # API Keys, Dashboard, Theme (~2.600 líneas)
│
└── tests/                       # 7 suites pytest
    ├── __init__.py
    ├── conftest.py
    ├── test_api_clients.py
    ├── test_config.py
    ├── test_exceptions.py
    ├── test_persistence.py
    ├── test_state.py
    ├── test_types.py
    └── test_workers.py
```

**Total**: ~22.500 líneas de código en 21 archivos principales + 7 suites de tests.

---

## 🆕 Cambios v1.0 vs v8.x

### 🐛 Bugs corregidos

| # | Bug | Solución |
|---|-----|----------|
| 1 | **Ventanas hijas (Copiloto, Batch...) salían DETRÁS de la principal** | Reescrito patch global de `CTkToplevel.transient()`: ahora mantiene `transient(master)` original Y fuerza `lift()+focus_force()` con delay tras `__init__`. Manteniendo además minimize/maximize de Windows. |
| 2 | `_build_header()` duplicado entre `app.py` y `UIBuildersMixin` | Eliminado de `app.py` (219 líneas). Solo vive en el mixin. |
| 3 | Parámetro muerto `modelo_llm=...` en 9 llamadas a `deepseek.generar()` | Eliminado. El provider activo se obtiene siempre desde `self.clients`. |
| 4 | README desactualizado (decía 4 LLMs cuando ya son 9) | Reescrito completo para v1.0. |
| 5 | Versión inconsistente entre archivos | Unificada a **v1.0** en todos los puntos. |

### ✨ Features nuevas

| # | Feature | Dónde |
|---|---------|-------|
| 1 | **Indicador visual del proveedor LLM** (🔑 verde si OK, ⚠ ámbar si falta key) | `app.py::_actualizar_indicador_proveedor` |
| 2 | **Splash screen** al arrancar | `main.py::SplashScreen` |
| 3 | **Toast in-app** no bloqueante | `app.py::show_toast()` |
| 4 | **Atajo Ctrl+Enter** = generar prompt | `app.py::_atajo_generar_prompt` |
| 5 | **Backup automático semanal** en zip | `app.py::_backup_semanal_check` |
| 6 | **Test de proveedor real** en wizard inicial | `app.py::_setup_wizard` |
| 7 | **Header responsive** (modo compacto <1180px) | `modules/ui_builders.py` |
| 8 | **Helper `open_child_window()`** para Toplevels correctos | `app.py::open_child_window` |
| 9 | **Cierre limpio** que destruye Toplevels hijos antes de la principal | `modules/dialogs.py::_on_cerrar` |
| 10 | **Validación de formato de keys** (sk-, AIza-, sk-or-) | `app.py::_setup_wizard::_validar_formato` |

### 🧹 Limpieza

- Logging estructurado en `workers.py` (warnings cuando hay fallback)
- Tooltip en botón 🔑 del header
- Wizard con keys ocultas (`show="*"`)
- `.env` y `keys.json` autoexplicativo en docstrings

---

## 🏗 Arquitectura

### Patrón de diseño: Herencia múltiple por Mixins

`ArquitectoApp` hereda de 8 clases mixin. Todas comparten el mismo `self`:

```python
class ArquitectoApp(
    ctk.CTk,               # Ventana principal CustomTkinter
    UIBuildersMixin,       # Construcción de UI
    ToolsCreativeMixin,    # Moodboard, ADN, Negative Builder
    ToolsWorkflowMixin,    # Macros, A/B Testing, Cron
    ToolsAnalysisMixin,    # Stats, Scoring, Education
    DataMgmtMixin,         # Historial, favoritos, snippets
    BackupExportMixin,     # Backup, restore, CSV
    DialogsMixin,          # API Keys, Dashboard, Theme
    CoreMixin,             # Workers, comandos, estado
):
    def __init__(self):
        super().__init__()
        # ...
```

**Regla**: NO añadir métodos directamente a `app.py`. Cada método nuevo va en su mixin correspondiente. La excepción son los helpers de uso global (`open_child_window`, `show_toast`) que son del propio `ArquitectoApp` y no encajan en ningún mixin.

### Patrón Provider (LLMs)

`api_clients.py` define `BaseLLMProvider` con `completar()` y `disponible()`. Cada proveedor implementa esa interfaz.

```
ArquitectoApp
  └── self.clients (APIClients)
        └── self.providers[pid] (BaseLLMProvider)
              ├── OpenAICompatibleProvider  → DeepSeek, OpenRouter, Groq, OpenAI, Mistral, xAI
              ├── OllamaProvider            → Ollama local
              ├── GeminiProvider            → Google Gemini
              └── ClaudeProvider            → Anthropic Claude
```

Añadir un nuevo proveedor = crear una clase con 2 métodos + entrada en `LLM_PROVIDERS`.

### Flujo de generación

```
Usuario escribe idea → txt_idea
  └── Click "Generar Prompt" o Ctrl+Enter → cmd_prompt()
        └── _construir_peticion() construye prompt con specs del modelo
              └── self.deepseek.generar()  ← worker en thread daemon
                    └── self.clients.get_active_provider().completar()
                          └── API → LLM
                                └── Respuesta → actualizar_salida()
                                      └── guardar_en_historial()
```

**Threading**: TODAS las llamadas a IA van en `threading.Thread(daemon=True)`.
Las actualizaciones de UI se hacen con `self.after(0, callback)` para volver al hilo principal.

---

## 🔌 Persistencia

Archivos en **`~/.arquitecto_prompts/`**:

| Archivo | Contenido |
|---------|-----------|
| `historial.json` | Últimos 500 prompts |
| `favoritos.json` | Prompts marcados ⭐ |
| `estrellas.json` | Prompts con nota y modelo |
| `personajes.json` | Personajes guardados |
| `loras.json` | LoRAs con triggers |
| `plantillas.json` | Plantillas (modo + modelo + estilos + ratio) |
| `preferences.json` | Preferencias de usuario |
| `keys.json` | API keys (fallback si no hay keyring) |
| `borrador.txt` | Borrador auto-guardado |
| `_last_autobackup.txt` | Marca de tiempo del último backup |
| `backups/auto-AAAAMMDD.zip` | Backups automáticos semanales (máx 10) |
| `logs/gprompt.log` | Log de la app |

### Almacenamiento de API keys (orden de prioridad)

1. **OS keyring** (Windows Credential Manager / macOS Keychain / Linux Secret Service)
2. `~/.arquitecto_prompts/keys.json` (fallback)
3. Variables de entorno (`.env`)

### Escrituras atómicas

TODOS los `.json` se escriben con el patrón **tmp + `os.replace()`** para prevenir corrupción si la app se cierra mid-write:

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

**40+ tests** cubriendo:

| Suite | Cobertura |
|-------|-----------|
| `test_api_clients.py` | Proveedores LLM, fábrica `get_provider()`, interfaces |
| `test_config.py` | Helpers (`es_separador`, `get_model_specs`, etc.) |
| `test_exceptions.py` | Jerarquía de excepciones |
| `test_persistence.py` | DataStore CRUD, atomic writes, preferencias |
| `test_state.py` | AppState, logging |
| `test_types.py` | TypedDicts |
| `test_workers.py` | Token counting, parser de ideas, detección de idioma |

---

## ⌨ Atajos de teclado (27 activos)

| Atajo | Acción |
|------|--------|
| `Alt+1` | Modo imagen |
| `Alt+2` | Modo vídeo |
| `Alt+3` | Modo audio |
| `Alt+Enter` | Quick generate |
| `Ctrl+1` | Copiar POSITIVE |
| `Ctrl+2` | Copiar NEGATIVE |
| `Ctrl+D` | Duplicar al historial |
| `Ctrl+E` | Exportar rápido |
| `Ctrl+Enter` | Generar prompt |
| `Ctrl+F` | Búsqueda global |
| `Ctrl+H` | Modo Focus |
| `Ctrl+I` | Ideas creativas |
| `Ctrl+L` | Abrir LoRAs |
| `Ctrl+P` | Grupo personajes |
| `Ctrl+R` | Idea aleatoria |
| `Ctrl+S` | Guardar favorito |
| `Ctrl+Shift+A` | Analizar imagen |
| `Ctrl+Shift+Enter` | Variaciones x3 |
| `Ctrl+Shift+L` | Cambiar tema |
| `Ctrl+Shift+N` | Negative builder |
| `Ctrl+Shift+P` | Previsualizar |
| `Ctrl+Shift+S` | Guardar estrella |
| `Ctrl+Shift+T` | Traducir idea |
| `Ctrl+T` | Abrir tutorial |
| `Ctrl+V` | Pegar inteligente |
| `Ctrl+?` | Mostrar todos los atajos |
| `Escape` | Cerrar popup activo |
| `F11` | Pantalla completa |

---

## 📐 Principios de diseño

1. **Provider Pattern** — Todos los LLMs usan la misma interfaz. Añadir provider = 2 métodos.
2. **Mixin Architecture** — 8 mixins separan responsabilidades sin duplicar estado.
3. **Escritura atómica** — `tmp + os.replace()` en TODO write a JSON.
4. **Threading + after** — IA en threads daemon; UI updates con `self.after(0, fn)`.
5. **Fallback chains** — VisionChain: Gemini → Ollama → OpenRouter.
6. **Sin duplicación if/elif** — Worker delega siempre en `provider.completar()`.
7. **Validación + auto-recuperación** — Archivos corruptos se respaldan y recrean.
8. **UX no bloqueante** — Toasts en lugar de `messagebox` cuando es posible.

---

## 🔑 Notas para futuros mantenedores

1. **NO modificar directamente `app.py`** para añadir métodos de un mixin — añadir al mixin correspondiente.
2. **Las únicas excepciones** que viven en `app.py` son helpers globales: `open_child_window`, `show_toast`, `_actualizar_indicador_proveedor`, `_backup_semanal_check`, `_atajo_generar_prompt`, `__init__`, `_setup_wizard`, `cmd_preferencias`, `_regen_*`, `_cmd_diff_versiones`, `cmd_previsualizar`, `_cmd_plantillas_populares`, `_abrir_comparador`. Todo lo demás → mixin.
3. **`self.deepseek`** es un `DeepSeekWorker` que delega en `self.clients.get_active_provider()`. NO pasarle parámetro `modelo_llm`.
4. **`self.store`** es un `DataStore` para persistencia.
5. **`self.llm_var`** es un `ctk.StringVar` con la LABEL del LLM activo (no el id).
6. **Nuevas ventanas hijas**: usar `self.open_child_window(title, size)` en lugar de `ctk.CTkToplevel(self)` directo. Garantiza que aparece al frente.
7. **Notificar al usuario**: usar `self.show_toast(msg, color)` para feedback no bloqueante; `messagebox` solo para confirmaciones importantes.
8. **El `.env` NO se commitea** — está en `.gitignore`.
9. **Theme switching** no destruye widgets — usa `_apply_theme_colors()` para actualizar.
10. **Backups automáticos** se crean cada 7 días en `~/.arquitecto_prompts/backups/`. Se conservan los últimos 10.

---

*Generado: 2026-05-16 | Versión: 1.0.9 | Python: 3.10+*
*Última versión — biblioteca integrada, dashboard, herramientas creativas.*
