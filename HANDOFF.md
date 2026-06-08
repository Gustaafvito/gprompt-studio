# 🧾 Handoff — G-Prompt Studio

Documento de continuación para retomar el proyecto en una sesión nueva.
Actualizado al final de la **sesión 16** (continuación de las sesiones 1-15).
Working tree limpio cuando se generó.

---

## 📍 Estado del proyecto

**G-Prompt Studio** — app de escritorio (Python + customtkinter) para
generar prompts de IA generativa (imagen, vídeo, audio) con LLMs como
motores. Incluye import/export JSON profesional para Veo/Sora/Kling,
sistema de empaquetado `.exe`, y CI/CD configurado.

| Métrica | Valor |
|---|---|
| Tests | **374/374** ✅ (+1 sesión 16) |
| Working tree | Limpio |
| Branch | `main` (sesión 16 cerrada en `de175e1`) |
| Bloques de profundidad | **6/6** ✅ |
| Mixins en `ArquitectoApp` | **1** (era 21 — 20 removidos en A1 fase 2 ⭐⭐⭐) |
| **Componentes (A1)** | **21/21** ✅ accesibles vía `self.X.metodo()` (+ footer) |
| **A1 fase 2** | **20/20 COMPLETO** ✅ — solo queda `CoreMixin` |
| `core.py` | 1665 líneas (era 2698, **−38%**) |
| `dialogs.py` | 543 líneas (era 1976, **−72%**) |
| `ui_builders.py` | 1553 líneas (era 2167, **−28%**, sesión 8) |
| F401 (imports muertos) | **0** (antes 171 silenciados) |
| F821 (undefined names) | **0** activo en CI (sesión 10) |
| Type hints | ✅ 104 firmas anotadas en 10 mixins |
| Build `.exe` | Distribuible al día (sesión 11) |
| Installer | Con diálogo **Reparar / Desinstalar / Cancelar** |
| Distribuible | `~/OneDrive/Desktop/GPromptStudio-Distribuible/` al día |
| CI | GitHub Actions (Ruff + tests 3.10/3.11/3.12) |
| Lint | Ruff con F401 + F821 activos |
| Pre-commit hooks | Activos (line endings, ruff, large files, secrets) |

Estructura: ver `ESTRUCTURA.md`. Empaquetado: ver `BUILD.md`.

---

## ✅ Qué se hizo en sesión 6

### Particiones #7, #8 y #9 de `core.py` (2698 → 1665 líneas, -38.3%)

Tres nuevos módulos extraídos de `core.py` en commits sucesivos:

**1. `modules/atajos_ayuda.py` (AtajosAyudaMixin) — commit `2bf3e74`**

Atajos de teclado + ventana de ayuda + búsqueda global + tutorial.
13 métodos, ~389 líneas. Incluye:
- `_bind_shortcuts` (registro de todos los bindings de teclado)
- `_cmd_cambiar_modo` (Alt+1/2/3), `_cmd_exportar_rapido` (Ctrl+E)
- `_atajo_guardar_estrella`, `_cmd_buscar_global`, `_atajo_buscar_global`
- `_atajo_traducir_idea` (Ctrl+Shift+T)
- `_toggle_fullscreen` (F11), `_cerrar_popup_activo` (Escape)
- `_cmd_abrir_loras` (Ctrl+L)
- `_cmd_mostrar_atajos` (Ctrl+?, ventana con 27 atajos + buscador + click-to-copy)
- `_abrir_busqueda_global` (búsqueda en historial/favoritos/estrellas)
- `_abrir_tutorial` (Ctrl+T, delega en `modules.tutorial`)

**2. `modules/ui_events.py` (UiEventsMixin) — commit `4c04ce2`**

Event handlers de los combos del panel superior. 8 métodos, ~345 líneas:
- `_on_modo_cambio` (imagen/vídeo/audio + sincronización de tabs)
- `_on_plataforma_cambio`, `_actualizar_motores_video`
- `_on_motor_cambio` (vídeo, con tooltip rico)
- `_on_modelo_imagen_cambio` (imagen, con tooltip + badges)
- `_on_motor_audio_cambio`, `_on_audio_filtro_cambio`, `_on_brief_cambio`

**Bonus**: importa `CTkToolTip` con `try/except` al top del módulo.
Antes core.py lo usaba SIN importar, lo que generaba `NameError`
silenciado por el `except Exception` envolvente — los tooltips ricos
de modelos de vídeo no se creaban nunca. Ahora sí funcionan.

**3. `modules/refinamiento.py` (RefinamientoMixin) — commit `4c04ce2`**

Refinamiento de prompts + iteración por elemento + diff visual.
6 métodos, ~313 líneas:
- `_menu_refinar_especifico` (popup con 7 refinamientos comunes)
- `_refinar_con_instruccion`
- `_cmd_iteracion` + `_iterar_elemento` (N variantes cambiando 1 elemento)
- `cmd_refinar` (refinamiento general con reglas tag-based vs natural)
- `_mostrar_diff_refinamiento` (modal con Aplicar/Cancelar/Deshacer)

### Auditoría del HANDOFF anterior

El HANDOFF v5 listaba como pendientes varias tareas que **ya estaban
hechas** en sesiones intermedias sin documentar:

- ✅ D1 GitHub Actions CI — `.github/workflows/ci.yml`
- ✅ D2 Ruff + pyproject.toml — configurado con `select` conservador
- ✅ D4 Pre-commit hooks — activos
- ✅ Build `.exe` real — `dist/GPromptStudio.exe` + installer existen
- ✅ Partición `_inyectar_specs_*` → `prompts_inyeccion.py`
- ✅ Tests crecieron 48 → 91

---

### Cobertura unitaria de los módulos extraídos

**`tests/test_prompts_inyeccion.py` — 37 tests** (commit `9dd4e1e`):
- `_inyectar_destino` (6): vacío, Personal, Instagram, Anthum,
  desconocido, sin atributo.
- `_inyectar_specs_modelo` (3): dispatcher audio/video/imagen.
- `_inyectar_specs_video` (6): sin specs, max_chars grande/pequeño,
  has_audio sí/no, nombre en mayúsculas.
- `_inyectar_template` (3): sin/con template, sin negative.
- `_inyectar_specs_formato` (7): natural con/sin neg, tags con pesos,
  ComfyUI Turbo (prohibe pesos+neg), tags sin neg, trigger words,
  sampler.
- `_inyectar_specs_audio` (7): combo ausente, separador, sin specs,
  instrumental/vocal, emoción/voz/idioma, placeholders.
- `construir_modelo_info` (5): composición, Personal, cache hit/miss,
  audio con emoción.

**`tests/test_refinamiento.py` — 32 tests** (commit `1c4ceff`):
- `_mostrar_diff_refinamiento` (12): textos vacíos/iguales/distintos,
  on_apply guarda pre-refinamiento + no duplica + limita a 30,
  on_undo disponible según stack + restaura la más reciente.
- `cmd_refinar` (13): sin texto / sin marcadores → warning; reglas
  por modo (imagen tag-based/natural, video, audio); incluye
  idea/personaje/lora/anclaje; límite chars desde specs o fallback;
  pasa es_refinamiento + texto_previo al worker.
- `_iterar_elemento` (5): parsing VARIANTE N, filtro de strings
  cortos, <2 variantes → avisa, respeta N, case-insensitive.
- `_menu_refinar_especifico` (2): guardas texto vacío/corto.

**Patrón establecido**: mockear `threading.Thread` con un
`SimpleNamespace` que ejecuta `target` sincrónicamente. Permite
testear workers IA sin red ni hilos reales.

### Rebuild .exe + distribución

- `python build.py` (onedir, ~1 min)
- `python build.py --installer` (onedir + Inno Setup, ~2-3 min)
- `python build.py --onefile` (onefile, ~2 min)
- Copia de los 3 a `~/OneDrive/Desktop/GPromptStudio-Distribuible/`:
  - `GPromptStudio-Portable/` (onedir, 13.4 MB)
  - `GPromptStudio-Portable-Onefile.exe` (124 MB)
  - `GPromptStudio-Setup-1.0.0.exe` (88 MB)

`gprompt-studio.spec` + `gprompt-studio-onefile.spec` actualizados con
los 3 mixins nuevos en `hiddenimports` (commit `bcbc1d5`).

---

### Lint cleanup masivo (commit `a503a07`)

Activado `F401` en ruff (estaba silenciado con 171 ocurrencias).
Auto-fix eliminó **192 imports muertos en 20 archivos** (-189 líneas
netas). Archivos más afectados: `app.py`, `modules/core.py` (-23),
`modules/ui_builders.py` (-16), y otros 17 archivos.

### Tests de `WorkersIaMixin` + fix bug latente (commit `7930ae0`)

**29 tests** para los 5 workers IA con mocks ligeros (after, deepseek,
vision). Cobertura: `_worker_ia` (14 tests con recorte, NEGATIVE,
ComfyUI Turbo, error handling), `_worker_vision` (3), `_worker_prompt_
traduccion` (2), `_worker_prompt_quick` (6), `_worker_imagen_a_prompt` (4).

**Bug fix incluido**: línea 195 de `_worker_prompt_quick` usaba `re.sub`
sin importar `re` (NameError silenciado por `except`). Movido
`import re` al top del módulo + eliminados 2 imports locales redundantes.
Quick Generate ahora funciona en el `.exe` distribuido.

### Partición #10: `dashboard.py` extraído de `dialogs.py` (commit `3d2e71d`)

`_cmd_dashboard` ocupaba 1433 líneas (72% de `dialogs.py`). Movido a
`modules/dashboard.py` (DashboardMixin) sin cambios funcionales.
`dialogs.py` ahora 543 líneas, enfocado en diálogos pequeños.
Specs actualizados con `modules.dashboard` en hiddenimports.

### Type hints en 4 mixins (commit `403bb1a`)

Anotadas 35 firmas públicas en:
- `prompts_inyeccion.py` (8): todos los `_inyectar_*` → `str`.
- `refinamiento.py` (6): comandos → `None`; `_iterar_elemento(elemento: str, n: int = 5)`.
- `atajos_ayuda.py` (13): atajos → `str` ("break"); `_abrir_*` → `None`.
- `ui_events.py` (8): `_on_*` → `None`; usa sintaxis PEP 604 (`str | None`).

### Installer con diálogo Reparar/Desinstalar/Cancelar (commits `d20a376`, `6075ba1`)

Antes el installer reinstalaba encima sin avisar. Ahora `InitializeSetup`
detecta la instalación previa vía registro y muestra:
- **Sí** = REINSTALAR / REPARAR (conserva datos)
- **No** = DESINSTALAR (lanza `unins000.exe /SILENT`)
- **Cancelar** = Salir sin tocar nada

Plus: `CloseApplications=force` cierra la app si está corriendo antes
de instalar (evita "archivo en uso").

**Bug fix**: el `#define MyAppId "{{...}}"` con escape doble de Inno
quedaba registrado en HKCU como `{...}}_is1` (1 llave inicial, **2 finales**).
Mi función de detección buscaba `{...}_is1` y no encontraba nada → el
diálogo nunca aparecía. Fix: `GetRegKeyLegacy` busca la forma real
(con `}}`) y `GetRegKeyClean` cubriría una entrada futura limpia.

---

### Extras post-cierre (commits adicionales):

- `41185de` **test(ab_testing)**: 11 tests para AbTestingMixin (estructura
  AB_DIMENSIONES, guardas de comandos, sugeridos por modo).
- `3dbadc7` **docs(installer)**: documentado que el escape `{{...}}`
  del AppId es sintaxis obligatoria de Inno (no es bug). El "limpieza
  AppId" del HANDOFF se cierra como no-actionable.
- `3eeaa71` **types**: 33 type hints en mixins viejos (backup_export,
  dashboard, tools_analysis).
- `e562182` **refactor(dashboard)**: extraída `_dashboard_palette()`
  a helper testeable + 10 tests.

### Investigación A2: `self.cmd_x` vs `self.creative.cmd_x`

`grep` confirma **0 usos** de los componentes (`self.creative`,
`self.workflow`, etc.) fuera de `components.py` mismo. La capa de
namespace existe pero no se está usando. **No es un problema actual**,
solo debt latente para cuando se inicie A1 (Mixins → Composición).

---

## 📜 Commits de sesión 6 (17 commits)

```
e562182 refactor(dashboard): extraer paleta de colores a helper testeable + 10 tests
3eeaa71 types: type hints en mixins viejos (backup_export, dashboard, tools_analysis)
3dbadc7 docs(installer): documentar por qué el AppId usa escape {{...}} (no bug)
41185de test(ab_testing): cobertura básica de AbTestingMixin (11 tests)
cc2e1de docs: actualizar HANDOFF con cierre de sesión 6
6075ba1 fix(installer): detectar AppId con doble llave (escape histórico Inno)
d20a376 installer: detección de instalación previa con Reparar/Desinstalar/Cancelar
403bb1a types: añadir type hints a los 4 mixins de sesión 6
3d2e71d refactor(dialogs): extraer _cmd_dashboard a modules/dashboard.py (#10)
7930ae0 test(workers_ia): cobertura de los 5 workers IA (29 tests) + fix re bug
a503a07 lint: quitar F401 del ignore + eliminar 192 imports sin usar
d62a620 docs: actualizar HANDOFF con tests + rebuild + distribución
1c4ceff test: cobertura de RefinamientoMixin (32 tests)
bcbc1d5 build: añadir hiddenimports de los 3 mixins nuevos
9dd4e1e test: cobertura unitaria de PromptsInyeccionMixin (37 tests)
f4a5733 docs: actualizar HANDOFF a sesión 6
4c04ce2 refactor(core): extraer ui_events + refinamiento (particiones #8 y #9)
2bf3e74 refactor(core): extraer atajos + ayuda a modules/atajos_ayuda.py
```

---

## 📦 Mixins en `ArquitectoApp` (20 en total tras sesión 6)

Orden en `class ArquitectoApp(ctk.CTk, ...)`:

1. `UIBuildersMixin`
2. `ToolsCreativeMixin`
3. `ToolsWorkflowMixin`
4. `ToolsAnalysisMixin`
5. `DataMgmtMixin`
6. `BackupExportMixin`
7. `DialogsMixin`
8. `CoreMixin`
9. `AdnVisualMixin`
10. `MultiPromptMixin`
11. `SesionVideoMixin`
12. `WorkersIaMixin`
13. `ModoClienteMixin`
14. `JsonPromptMixin`
15. `PromptsInyeccionMixin`
16. `AbTestingMixin`
17. `AtajosAyudaMixin` (sesión 6)
18. `UiEventsMixin` (sesión 6)
19. `RefinamientoMixin` (sesión 6)
20. `DashboardMixin` (sesión 6)

---

## 📂 Tamaño actual de archivos grandes

| Archivo | Líneas | Cambio vs HANDOFF v5 |
|---|---:|---|
| `app.py` | 2391 | +166 (limpieza F401 redujo algo) |
| `modules/ui_builders.py` | 2167 | +99 |
| `modules/tools_creative.py` | 1881 | +51 |
| `modules/core.py` | **1665** | **−1033** (-38.3%) ⭐ |
| `modules/dashboard.py` | 1457 | nuevo (extraído de dialogs.py) |
| `modules/tools_workflow.py` | 1178 | −548 |
| `modules/dialogs.py` | **543** | **−1433** (-72%) ⭐

---

## 🚧 Pendiente para la próxima sesión

### 🔴 ALTA

#### A1 Mixins → Composición pura — 🟡 EN MARCHA (1/20 migrado)

**Primer paso completado (commit `e60b5f9`)**: `PromptsComponent`
añadido a `modules/components.py` con API pública explícita
(`inyectar_specs_*`, `inyectar_destino`, `construir_modelo_info` sin
underscore). Los 9 call sites en `core.py` (7) + `workers_ia.py` (2)
migrados a `self.prompts.X()`.

`PromptsInyeccionMixin` sigue heredado en `ArquitectoApp` por
compatibilidad — cuando NO queden llamadas directas a sus métodos
(`self._inyectar_*`, `self.construir_modelo_info()`), se podrá
quitar del MRO (20 → 19 mixins).

**Patrón establecido**:
1. Crear `XxxComponent(_Component)` en `components.py` con métodos
   públicos que delegan a `self.app._método_privado()`.
2. Registrar en `install_components(app)`.
3. Migrar call sites de `self._método()` → `self.xxx.metodo()`.
4. Actualizar tests (añadir `prompts=SimpleNamespace(...)` al `_host()`).
5. Cuando todo migrado: quitar mixin del MRO de `ArquitectoApp`.

**Próximos candidatos** (orden de menor a mayor complejidad):
- `AbTestingMixin` (5 métodos, ya con 11 tests).
- `JsonPromptMixin` (modal-heavy pero autocontenido).
- `RefinamientoMixin` (6 métodos, ya con 32 tests).
- `WorkersIaMixin` (5 workers, ya con 29 tests).
- `AtajosAyudaMixin` (13 métodos, ya con 0 tests).

Refactor mayor restante: ~5-9 días para los 19 mixins restantes.

#### T1 Cobertura de tests
11 archivos cubren `api_clients`, `config`, `json_prompt`,
`parsear_variaciones`, `persistence`, `workers`, `prompts_inyeccion`
(37 tests), `refinamiento` (32 tests), `workers_ia` (29 tests),
`ab_testing` (11 tests) y `dashboard` (10 tests, solo paleta).

**Sin tests todavía**: `adn_visual`, `multiprompt`, `sesion_video`,
`modo_cliente`, `ui_events`, `atajos_ayuda`, `dialogs`, `core`.

Próximos candidatos limpios:
- `ui_events.py` (decisiones de packeo según modo, mockear widgets).
- `atajos_ayuda.py` (handlers con lógica testeable).
- `adn_visual.py` (gestión de rasgos, autocontenido).

#### Verificar `.exe` real arranca — ✅ HECHO en sesión 6
Verificado múltiples veces durante la sesión. Build final del 19:35
con todos los cambios:
- Bug fix de `re` en workers_ia (Quick Generate funciona).
- Partición dashboard.py empaquetada.
- Type hints aplicados.
- Installer con detección y diálogo Reparar/Desinstalar/Cancelar.

Pendiente menor: probar el installer end-to-end en una VM o usuario
nuevo (instalación limpia → arranque → desinstalación con borrado
de datos).

### 🟡 MEDIA

#### Particiones restantes de archivos grandes
- **`app.py` (2391)** — clase principal, difícil. Posible: extraer
  inicialización de UI (`__init__`) en helpers.
- **`ui_builders.py` (2167)** — constructores UI. Posible: separar
  barra superior, barra inferior, panel central.
- **`tools_creative.py` (1881)** — buscar bloques cohesivos.
- **`core.py` (1665)** — todavía grande. Candidatos: parsers
  (`_parsear_variaciones`, `_extraer_*`, `_recortar_si_excede`),
  commands top-level (`cmd_ideas`, `cmd_prompt`, etc.).
- **`dashboard.py` (1457)** — extraído recientemente como una sola
  función monolítica `_cmd_dashboard`. Podría partirse internamente
  en helpers (saludo, stats cards, gráfico, logros, etc.).

#### ~~Lint debt F401~~ — ✅ HECHO en sesión 6
192 imports muertos eliminados. F401 activo en ruff sin ignore.

#### Type hints incrementales
7 mixins ya anotados (mixins nuevos: prompts_inyeccion, refinamiento,
atajos_ayuda, ui_events; mixins viejos: backup_export, dashboard,
tools_analysis). Quedan: core, dialogs, tools_creative, tools_workflow,
data_mgmt, ui_builders, adn_visual, multiprompt, sesion_video,
modo_cliente, json_prompt, ab_testing, workers_ia, prompts_inyeccion.

#### ~~A2 Unificar `self.cmd_x` vs `self.creative.cmd_x`~~ — No es un problema actual
`grep` confirma **0 usos** de los componentes (`self.creative`, etc.)
fuera de `components.py`. La capa de namespace existe pero nadie la
usa, así que no hay inconsistencia real. Solo es debt latente para
cuando se inicie A1 (Mixins → Composición).

#### ~~Limpieza AppId del installer~~ — No es bug, está documentado
Investigado en sesión 6: el escape `{{...}}` es sintaxis OBLIGATORIA
de Inno Setup cuando el AppId contiene llaves. Sin escape, Inno
intenta interpretar `{...}` como constante y rompe. Que el registro
quede con `}}_is1` es comportamiento normal. Documentado en
`installer.iss`.

### 🟢 BAJA

#### Distribución
- Code-signing del `.exe` para evitar SmartScreen warning.
- Build CI: workflow que genera `.exe` en cada release tag.

#### SeaArt char limits
Pendiente que el usuario reporte modelo concreto + límite real
para corregir `data/model_specs_imagen.json`.

#### Mejoras UX
- Comparador "lado a lado con diff" entre 2 cards.
- Grid Pollinations con boceto por cada modelo.
- Tooltips visibles permanentes en barra inferior.
- Párrafo descriptivo del modelo → tooltip o "ℹ️ más info".

#### Rendimiento
- R1 Carga lazy de `data/*.json` (ahora se cargan en import).
- R2 Semáforo de workers IA simultáneos.
- R3 Virtual scrolling en historial/favoritos (cargan TODOS).

#### Seguridad
- S2 Sanitización de prompts antes de enviar a APIs externas.

#### Features
- F4 Exportar a PDF (Markdown a través de JSON pretty ya existe).
- F5 Diff entre versiones más visible (existe `_cmd_diff_versiones`).
- F1 Plugin system (ambicioso).
- F2 API REST (ambicioso).

---

## ✅ Sesión 7 — A1 iniciado + bug fixes UI

### Refactor A1: 6/20 mixins migrados a Composición

Patrón establecido: `XxxComponent(_Component)` en `components.py` con
API pública sin underscore, registrado en `install_components(app)`,
call sites migrados de `self._método()` → `self.xxx.metodo()`.

| # | Mixin → Componente | Acceso | Entry points | Call sites migrados |
|---|---|---|---:|---:|
| 1 | `PromptsInyeccionMixin` → `PromptsComponent` | `self.prompts` | 6 | 9 |
| 2 | `AbTestingMixin` → `AbTestingComponent` | `self.ab` | 2 | 2 |
| 3 | `JsonPromptMixin` → `JsonPromptComponent` | `self.json` | 2 | 2 |
| 4 | `RefinamientoMixin` → `RefinamientoComponent` | `self.refinar` | 5 | 11 |
| 5 | `WorkersIaMixin` → `WorkersIaComponent` | `self.workers` | 5 | 8 |
| 6 | `AtajosAyudaMixin` → `AtajosAyudaComponent` | `self.atajos` | 3 | 3 |

**Total**: 23 entry points expuestos, **35 call sites migrados** en 7
archivos (core.py, workers_ia.py, ui_builders.py, tools_creative.py,
tools_workflow.py, refinamiento.py, app.py).

Los mixins siguen heredados en `ArquitectoApp` (sin cambios de MRO)
por compatibilidad — cuando 0 call sites llamen al método legacy,
se podrá quitar del MRO (objetivo: 20 → 14 mixins tras completar A1).

### Bug fixes y mejoras UI

- **Bug Iterar/Usar perdía formato POSITIVE/NEGATIVE**: el LLM no
  incluía las etiquetas. Fix: el prompt al LLM ahora pide
  EXPLÍCITAMENTE el formato en cada variante, y el callback `_usar`
  reconstruye el texto formateado si la variante viene "pelada".
- **GPT Image 2 generaba sin etiqueta `PROMPT:`**: en
  `_inyectar_specs_formato`, modelos `is_natural=True + has_negative=False`
  no tenían instrucción explícita. Fix: incluir bloque
  "⚠️ FORMATO DE SALIDA OBLIGATORIO ⚠️ PROMPT: ...".
- **`PROMPT:` no se coloreaba en verde**: `_colorear_resultado` solo
  buscaba `POSITIVE PROMPT:` / `NEGATIVE PROMPT:`. Fix: añadidas
  variantes `POSITIVE:`, `NEGATIVE:` y `PROMPT:`.

### UI reorganización (feedback usuario)

- **Nuevo menú `📚 Aprender`**: agrupado contenido formativo:
  - ℹ️ Acerca de G-Prompt (nuevo `_cmd_acerca_de` en DialogsMixin)
  - ⌨️ Atajos teclado (movido desde `🎨 UI`)
  - 📖 Guía de estilos (movido desde `📊 Análisis`)
  - 📖 Modo educativo (movido desde `📊 Análisis`)
  - 📚 Tutorial completo (movido desde `📊 Análisis`)
- **`📊 Análisis`**: ahora solo contiene análisis real
  (Auto-mejora, Crítica historial, Estadísticas).
- **`🎨 UI`**: limpio (sin Atajos).
- **"Acerca de"**: modal con descripción, autor y 3 enlaces
  (GitHub, YouTube, X). Sin stats personales.

### Persistencia y unificación de switches

- **Persistencia automática**: NSFW, Auto-trad, Brief se guardan en
  `preferences.json` al cambiar y se restauran al arrancar.
- **Estilo unificado en los 5 switches** del proyecto (NSFW,
  Auto-trad, Instrumental, Modo Brief, Sonido, Grabar vídeo sesión):
  - `width: 50 → 42` / `height: 26 → 20` / `corner_radius: 13 → 10`
  - `button_length: 8` (pelota más pequeña, antes default ~16)
  - `border_width: 2 → 1`
  - `button_color: #ffffff → #e5e7eb` (gris claro, no blanco puro)

### Rebuild + redistribución (final del día)

3 artefactos en `~/OneDrive/Desktop/GPromptStudio-Distribuible/`
con timestamps del último build (23:03):
- `GPromptStudio-Portable/GPromptStudio.exe` (13.4 MB) — onedir
- `GPromptStudio-Portable-Onefile.exe` (124 MB) — onefile
- `GPromptStudio-Setup-1.0.0.exe` (88.5 MB) — installer

### Commits de sesión 7 (14 commits)

```
5294de0 fix(ui): pelota más pequeña + unificar estilo en los 5 switches
1599da5 fix(ui): switches más proporcionados + coloreado de etiqueta PROMPT
79ceea2 fix(prompt-natural): forzar etiqueta PROMPT: en modelos natural sin negative
5220eb3 revert(ui): restaurar colores originales del switch NSFW
602c5d8 fix(ui): no llamar reiniciar_memoria al sincronizar visual inicial de switches
681a453 fix(ui): unificar estilo de switches NSFW y Auto-trad cuando están OFF
769e40a feat(prefs): persistir estado de switches NSFW/Auto-trad/Brief entre sesiones
37353fa fix(acerca-de): URLs correctas + quitar stats personales
57be3ff fix(refinar) + ui: bug Iterar/Usar + nuevo menú "Aprender"
daf70a5 refactor(A1): pasos 4-6 — Refinamiento + WorkersIa + AtajosAyuda (6/20)
4ad15ed refactor(A1): tercer paso — JsonPromptComponent (3/20 migrados)
a72b750 refactor(A1): segundo paso — AbTestingComponent (2/20 migrados)
426cdd8 docs: actualizar HANDOFF con A1 en marcha (1/20 mixins migrados)
e60b5f9 refactor(A1): primer paso Mixins → Composición — PromptsComponent
```

### 🚧 Pendiente para sesión 8

#### 🔴 ALTA
- **A1 continuar (14/20 mixins restantes)** — orden sugerido por
  facilidad:
  1. `ModoClienteMixin` (brief profesional + 5 propuestas)
  2. `MultiPromptMixin` (Mood/Story/Board/Walk)
  3. `SesionVideoMixin` (grabación + tutorial)
  4. `AdnVisualMixin` (rasgos visuales inmutables)
  5. `UiEventsMixin` (event handlers UI)
  6. `DashboardMixin` (1 método grande)
  7. `ToolsAnalysisMixin` (22 métodos)
  8. `DataMgmtMixin`
  9. `BackupExportMixin`
  10. `DialogsMixin` (sin _cmd_dashboard)
  11. `ToolsCreativeMixin`
  12. `ToolsWorkflowMixin`
  13. `UIBuildersMixin` (muy grande)
  14. `CoreMixin` (el más complejo, último)

  Tras completar todos: quitar mixins del MRO de `ArquitectoApp`
  (20 → ?, dejando solo lo imprescindible).

- **T1 Tests pendientes** (8 módulos sin tests):
  `adn_visual`, `multiprompt`, `sesion_video`, `modo_cliente`,
  `ui_events`, `atajos_ayuda`, `dialogs`, `core`.

#### 🟡 MEDIA
- **Particiones restantes**: `app.py` 2391, `ui_builders.py` 2167,
  `tools_creative.py` 1881, `core.py` 1665, `dashboard.py` 1457.
- **Type hints en mixins viejos** restantes (13 sin anotar).

#### 🟢 BAJA
- Code-signing del `.exe` (SmartScreen warning).
- SeaArt char limits (necesita info del usuario).
- Performance: lazy load JSON, semáforo workers, virtual scrolling.

---

## ✅ Sesión 8 — A1 COMPLETO + más tests + más particiones

### A1 (Mixins → Composición): 20/20 COMPLETO ✅

Tabla completa de los 20 componentes accesibles:

| # | Mixin → Componente | Acceso | Métodos públicos |
|---|---|---|---:|
| 1 | PromptsInyeccionMixin → PromptsComponent | `self.prompts` | 6 |
| 2 | AbTestingMixin → AbTestingComponent | `self.ab` | 2 |
| 3 | JsonPromptMixin → JsonPromptComponent | `self.json` | 2 |
| 4 | RefinamientoMixin → RefinamientoComponent | `self.refinar` | 5 |
| 5 | WorkersIaMixin → WorkersIaComponent | `self.workers` | 5 |
| 6 | AtajosAyudaMixin → AtajosAyudaComponent | `self.atajos` | 3 |
| 7 | ModoClienteMixin → ModoClienteComponent | `self.cliente` | 2 |
| 8 | MultiPromptMixin → MultiPromptComponent | `self.multi` | 4 |
| 9 | AdnVisualMixin → AdnVisualComponent | `self.adn` | 2 |
| 10 | SesionVideoMixin → SesionVideoComponent | `self.sesion` | 1 |
| 11 | DashboardMixin → DashboardComponent | `self.dashboard` | 1 |
| 12 | UiEventsMixin → UiEventsComponent | `self.events` | 8 |
| 13 | ToolsCreativeMixin → CreativeComponent | `self.creative` | 7 |
| 14 | ToolsWorkflowMixin → WorkflowComponent | `self.workflow` | 6 |
| 15 | ToolsAnalysisMixin → AnalysisComponent | `self.analysis` | 14 |
| 16 | DataMgmtMixin → DataComponent | `self.data` | 11 |
| 17 | BackupExportMixin → BackupComponent | `self.backup` | 5 |
| 18 | DialogsMixin → DialogsComponent | `self.dialogs` | 4 |
| 19 | CoreMixin → CoreComponent | `self.core` | delegación pura |
| 20 | UIBuildersMixin → UIComponent | `self.ui` | delegación pura |

**Total: 88 métodos públicos declarados + delegación por `__getattr__`.**

### Bonus técnico

`_Component.__getattr__` relajado en sesión 8: ahora delega TAMBIÉN
nombres con underscore. Permite acceder a cualquier método del mixin
vía componente sin restricciones (`self.analysis._método_interno` funciona).

### Migración de call sites — masiva en sesión 8

- **ui_builders.py**: TODOS los items de los 8 menús del header
  migrados (`Análisis`, `Aprender`, `Backup`, `Datos`, `Herramientas`,
  `Plantillas`, `UI`, `Workflow`).
- **ui_footer.py**: barras inferiores (`HERRAMIENTAS`, `NEGATIVE`,
  `GUARDAR`) migradas + menú contextual del editor.
- **dashboard.py**: 3 botones de quick actions migrados.
- **core.py**: `_detectar_nsfw_auto` → `self.analysis`.
- **ui_events.py**: `_mostrar_consejo_contextual` → `self.analysis`.
- **tools_workflow.py**: `_traducir_salida` → `self.analysis`.

### Particiones

- **ui_footer.py** extraído de ui_builders.py:
  `_build_footer` (616 líneas, 28% del archivo) → `modules/ui_footer.py`
  como `UiFooterMixin`. ui_builders.py 2169 → 1553 líneas.

### Tests añadidos

- `tests/test_ui_events.py` (+18 tests): on_brief_cambio,
  on_audio_filtro_cambio, actualizar_motores_video, on_motor_cambio,
  on_motor_audio_cambio, on_plataforma_cambio. 210 → 228 tests.

### Type hints

- `data_mgmt.py`: +22 firmas
- `dialogs.py`: +8 firmas
- `sesion_video.py`: +6 firmas
- **Total acumulado: 104 firmas en 10 mixins**

### Commits de sesión 8 (6 commits)

```
96fe7c2 refactor(A1): completar 20/20 mixins — Creative, Workflow,
        Analysis, Data, Backup, Dialogs con métodos públicos + migración
7083b32 types: type hints automáticos en 3 mixins viejos (+36 firmas)
7e9cfae refactor(ui): extraer _build_footer a modules/ui_footer.py (#11)
2cfac51 test(ui_events): cobertura de UiEventsMixin (18 tests)
a1b910f refactor(A1): pasos 7-12 — Cliente + Multi + ADN + Sesión +
        Dashboard + Events (12/20)
```

### 🚧 Pendiente para sesión 9

#### 🔴 ALTA — Cerrar A1 de verdad
**Quitar mixins del MRO de `ArquitectoApp`**. Ahora hay 21 mixins
heredados Y 20 componentes que delegan al mismo app. El verdadero
beneficio de A1 viene cuando se quitan los mixins del MRO (queda
solo `ctk.CTk` + tal vez `CoreMixin` por intricación).

Pasos:
1. Verificar que NINGÚN call site usa `self._método()` directo
   (todo va vía `self.X.metodo()`).
2. Quitar mixin por mixin del MRO, ejecutando tests entre cada uno.
3. Cuando se quitan, los métodos siguen siendo accesibles vía
   componente — no por herencia.

Estimación: ~1-2 días con tests verdes en cada paso.

#### 🔴 ALTA — T1 cobertura tests
Quedan 7 módulos sin tests: `adn_visual`, `multiprompt`,
`sesion_video`, `modo_cliente`, `atajos_ayuda`, `dialogs`, `core`.

#### 🟡 MEDIA
- **Particiones**: `app.py` 2391, `tools_creative.py` 1881,
  `core.py` 1665, `ui_builders.py` 1553, `dashboard.py` 1457.
- **Type hints** en mixins restantes (~10 sin anotar).

#### 🟢 BAJA
- Code-signing del `.exe` (SmartScreen warning).
- SeaArt char limits (necesita info usuario).
- UX: comparador lado-a-lado, grid Pollinations.
- Performance: lazy load JSON, semáforo workers.

---

## ✅ Sesión 9 — A1 fase 2 iniciado (3 mixins removidos del MRO)

### Patrón establecido: Mixin → Service aislado

**3 mixins convertidos** a servicios aislados con `app: ArquitectoApp`
por composición. Acceso vía componentes (`self.json.cmd_*`,
`self.prompts.inyectar_*`, `self.atajos.bind_*`).

| Mixin → Service | Líneas | self.X → self.app.X | Tests reescritos |
|---|---:|---:|---|
| JsonPromptMixin → JsonPromptService | 657 | 29 refs | 0 (tests sin mixin) |
| PromptsInyeccionMixin → PromptsInyeccionService | 287 | ~30 refs | 2 manual |
| AtajosAyudaMixin → AtajosAyudaService | 389 | ~40 refs | 0 |

Mixins en MRO: **21 → 18 (-3)**.

### Protocolo del refactor

1. Script regex transforma `self.X` → `self.app.X` (excepto métodos
   internos del service).
2. Fix manual de patrones widget-aware:
   - `GPromptWindow(self)` → `GPromptWindow(self.app)`
   - `.transient(self)` → `.transient(self.app)`
   - `hasattr(self, "X")` → `hasattr(self.app, "X")`
   - `getattr(self, "X", d)` → `getattr(self.app, "X", d)`
3. Componente instancia el service en `__init__` y delega métodos a él.
4. Quitar mixin del MRO en `app.py` + actualizar `modules/__init__.py`.
5. Actualizar tests si los usaban: `cls = type("Host", (Service,), {})()`
   ya no funciona porque `Service.__init__` requiere `app`. El helper
   `_host()` debe cambiar a `Service(app)` con `app: SimpleNamespace`.

### Lo que NO se migró en esta sesión (intento revertido)

Se intentaron migrar `RefinamientoMixin`, `WorkersIaMixin`,
`AbTestingMixin` y `DashboardMixin` pero requerían reescritura
significativa de sus tests (cambio de `h.X` por `h.app.X` en cientos
de líneas de tests). Revertido para no romper el suite.

**Lección**: A1 fase 2 requiere **1 mixin por commit con reescritura
de tests** — no se puede hacer en lote.

### Commits sesión 9

```
8842cef refactor(A1 fase 2): AtajosAyudaMixin removido del MRO (3/20)
ca1435e refactor(A1 fase 2): JsonPromptMixin + PromptsInyeccionMixin
        removidos del MRO
96fe7c2 refactor(A1): completar 20/20 mixins (sesión 8)
7e9cfae refactor(ui): extraer _build_footer (sesión 8)
2cfac51 test(ui_events): cobertura de UiEventsMixin (sesión 8)
```

### 🚧 Pendiente sesión 10+

---

## ✅ Sesión 10 — bug fixes masivos + feature Storyboard

### Bugs corregidos (5 commits)

- **`fea3886` fix(ui_footer)**: `NameError: tooltip_para` al construir
  checkboxes de estilos. Al extraer `_build_footer` en sesión 8, se
  omitieron `tooltip_para` (de `modules.style_guide`) y `logger`. La
  app crasheaba al instanciar la tab "🎨 Estilos".
- **`d0fcc7f` fix(logging)**: `UnicodeEncodeError` del `StreamHandler`
  en consola Windows (cp1252) al loggear `→` y emojis. No era fatal
  pero ensuciaba el output con stack traces. Fix: `sys.stdout.
  reconfigure(encoding="utf-8", errors="replace")` al inicio de
  `main.py`, antes de instanciar handlers.
- **`f8c252a` fix: 5 imports faltantes barridos con ruff F821**:
  - `ui_footer.py`: `re`, `pyperclip`, `detectar_idioma_es`,
    `ESTILO_NEGATIVO_AUTO`, `MOTOR_DEFAULT`, `NEGATIVE_PRESETS`,
    `PRESET_COLORES`, `es_separador` (8 símbolos en total).
    Crasheaba con Auto-trad activo.
  - `backup_export.py`, `data_mgmt.py`: `messagebox` (tkinter).
  - `sesion_video.py`: `pyperclip`.
  Todos eran fallout de la limpieza F401 (sesión 6) + partición #11
  (sesión 8) que eliminaron imports aparentemente muertos pero usados
  en ramas no testeadas.
- **`9cf2c40` fix: closures de `e` en except + F821 activado**:
  35 ocurrencias del patrón roto:
    `except Exception as e: self.after(0, lambda: f"...{e}...")`
  Python hace `del e` al exit del except → NameError silencioso en
  el callback. Fix con `lambda e=e:` (33 sitios) + `err = e; def _err()`
  (2 sitios). F821 activado en `pyproject.toml` → CI detectará esta
  clase de bugs automáticamente.

### Nueva feature: 🖼 Storyboard para imagen (`b35abc5`)

Botón nuevo en grupo "🎬 NARRATIVA" (fila 2 de acciones). Solo modo
IMAGEN. Genera N paneles cinematográficos (3-12, default 9) con:
- **SHOT type** (el LLM elige libremente: CLOSE-UP, MEDIUM, WIDE,
  EXTREME WIDE, POV, OVER-THE-SHOULDER, OVERHEAD, LOW ANGLE, DUTCH
  ANGLE, INSERT…), variándolos para ritmo cinematográfico.
- **DESCRIPCIÓN narrativa** corta por panel, estilo guion técnico.
- Coherencia visual entre paneles (paleta, iluminación, personajes).

Optimizado para modelos de lenguaje natural (GPT Image, DALL-E 3,
Imagen 3, Midjourney v6+, FLUX natural, Ideogram). Funciona también
con SD/Comfy pero requiere refinar cada panel (botón `🔁 Refinar`)
para convertir a formato tag-based.

Botón extra en el comparador: **📋 Fusionar en 1 prompt** combina los
N paneles en una descripción multi-panel estilo grid de cómic (útil
para Midjourney --tile, DALL-E multi-panel).

Implementación: `_cmd_storyboard_imagen` + `_fusionar_storyboard_imagen`
en `multiprompt.py`, expuestos vía `MultiPromptComponent.cmd_storyboard_imagen`.

### Rebuild + redistribución (3 rebuilds en la sesión)

3 artefactos finales regenerados en `~/OneDrive/Desktop/GPromptStudio-Distribuible/`
(timestamp ~10:23):
- `GPromptStudio-Portable/` (onedir, 13.4 MB)
- `GPromptStudio-Portable-Onefile.exe` (124.1 MB)
- `GPromptStudio-Setup-1.0.0.exe` (88.5 MB)

### Auditoría de complejidad real de mixins (D)

El HANDOFF v9 listaba `UiFooterMixin` como "1 método, autocontenido".
**Falso**: tiene 29 métodos y 87 call sites externos. Auditoría
completa de los 18 mixins pendientes con métricas reales:

| # | Mixin | Líneas | Métodos | Call sites ext. | Tests | Dificultad |
|---|---|---:|---:|---:|---:|---|
| 1 | DashboardMixin | 1502 | 1 | 1 | 10 | 🟢 TRIVIAL |
| 2 | AbTestingMixin | 614 | 5 | 2 | 11 | 🟢 TRIVIAL |
| 3 | AdnVisualMixin | 665 | 2 | 2 | 0 | 🟢 TRIVIAL |
| 4 | ModoClienteMixin | 868 | 5 | 2 | 0 | 🟢 TRIVIAL |
| 5 | MultiPromptMixin | 966 | 8 | 4 | 0 | 🟢 EASY |
| 6 | BackupExportMixin | 790 | 8 | 5 | 0 | 🟢 EASY |
| 7 | WorkersIaMixin | 273 | 5 | 6 | 29 | 🟡 EASY+tests |
| 8 | RefinamientoMixin | 336 | 6 | 7 | 32 | 🟡 EASY+tests |
| 9 | ToolsAnalysisMixin | 1491 | 23 | 15 | 0 | 🟡 MEDIUM |
| 10 | ToolsWorkflowMixin | 1172 | 14 | 15 | 0 | 🟡 MEDIUM |
| 11 | ToolsCreativeMixin | 1868 | 18 | 18 | 0 | 🟡 MEDIUM |
| 12 | UIBuildersMixin | 1546 | 26 | 22 | 0 | 🟡 MEDIUM |
| 13 | UiEventsMixin | 375 | 8 | 51 | 18 | 🟠 MED-HIGH+tests |
| 14 | SesionVideoMixin | 552 | 12 | 56 | 0 | 🟠 HIGH (`_sesion_log`) |
| 15 | DataMgmtMixin | 1545 | 30 | 57 | 0 | 🟠 HIGH |
| 16 | UiFooterMixin | 650 | 29 | 87 | 0 | 🟠 HIGH |
| 17 | CoreMixin | 1645 | 33 | 127 | 0 | 🔴 HARD |
| 18 | DialogsMixin | 612 | 17 | 619 (*) | 0 | 🔴 EXTREME |

(*) El conteo alto de `DialogsMixin` viene de métodos con nombres
genéricos (`cmd_*`) que colisionan con otros mixins en el grep — el
número real probable es ~20-40, pendiente medir con AST.

### 🚧 Pendiente sesión 11+

#### 🔴 ALTA — A1 fase 2 (17 mixins restantes)

Orden recomendado por la tabla de arriba (TRIVIAL → EXTREME):
**Dashboard → AbTesting → AdnVisual → ModoCliente → MultiPrompt →
Backup → Workers → Refinar → Analysis → Workflow → Creative → UI →
UiEvents → Sesion → DataMgmt → UiFooter → Core → Dialogs**.

Los 4 primeros (Dashboard, AbTesting, AdnVisual, ModoCliente) son
TRIVIAL: 1-5 call sites externos cada uno. Se pueden hacer 2-4 por
sesión. Los 4 últimos (DataMgmt, UiFooter, Core, Dialogs) son los
duros — 1 por sesión cada uno.

Estimación realista: ~6-8 sesiones para completar A1 fase 2.

#### 🔴 ALTA — T1 cobertura tests
7 módulos sin tests: `adn_visual`, `multiprompt`, `sesion_video`,
`modo_cliente`, `atajos_ayuda`, `dialogs`, `core`. Prioridad: cubrir
los mixins TRIVIAL antes de migrarlos (ahorra reescritura después).

#### 🟡 MEDIA
- Particiones de archivos grandes (top 5):
  `core.py` 1645, `data_mgmt.py` 1545, `ui_builders.py` 1546,
  `dashboard.py` 1502, `tools_analysis.py` 1491.
- Type hints en mixins restantes (~10 sin anotar).
- **Storyboard imagen + SD/Comfy**: añadir toggle "📐 Formato SD" al
  `_cmd_storyboard_imagen` que genere los paneles ya en formato
  tag-based POSITIVE/NEGATIVE (para no tener que refinar uno a uno).

#### 🟢 BAJA
Code-signing del `.exe`, SeaArt char limits, UX (comparador lado-a-lado),
performance (lazy load JSON, semáforo workers, virtual scrolling).

### Commits sesión 10

```
b35abc5 feat(narrativa): nuevo botón "🖼 Storyboard" para modelos de imagen
9cf2c40 fix: capturar e en closures de except + activar F821 en ruff
f8c252a fix: imports faltantes encontrados en barrido F821 (ruff)
d0fcc7f fix(logging): reconfigurar stdout/stderr a UTF-8 en Windows
fea3886 fix(ui_footer): añadir imports faltantes (logger + tooltip_para)
```

### Métricas finales sesión 10

| Métrica | Antes | Ahora |
|---|---:|---:|
| Tests | 228 | 228 ✅ |
| Mixins en MRO | 18 | 18 |
| Componentes A1 | 20/20 | 20/20 |
| Reglas ruff activas | base | base + **F821** ⭐ |
| NameError latentes | ≥6 conocidos | 0 ✅ |
| Botones acción NARRATIVA | 4 | 5 (+ 🖼 Storyboard) |

---

## ✅ Sesión 11 — A1 paso 4/20 + workflow Storyboard→Vídeo completo

### A1 fase 2: DashboardMixin → DashboardService (4/20)

`DashboardMixin` removido del MRO de `ArquitectoApp`. Su único método
`_cmd_dashboard` (1433 líneas) ahora vive como `DashboardService`
aislado con `app` por composición.

- 37 referencias `self.X` → `self.app.X` (auto-script + fix manual de
  patrones widget-aware: `GPromptWindow`, `transient`, `hasattr`).
- `DashboardComponent.cmd_abrir()` delega a `self._service._cmd_dashboard()`.
- **0 call sites externos a reescribir** (ya usaban `self.dashboard.cmd_abrir()`
  desde sesión 8, gracias a la fase 1).
- Tests: cero reescritura (los 10 tests de `_dashboard_palette` son
  sobre función standalone).

Mixins en MRO: **18 → 17** (-1).

### Workflow Storyboard → Vídeo (3 features nuevas)

El usuario quería este flujo end-to-end:

```
Idea → app genera storyboard → imagen (otra plataforma) →
app analiza imagen como referencia → prompt de vídeo → Seedance 2.0
```

Cada paso destapó un problema, los 3 corregidos:

**1. `12de567` Switch "🖼 Ref" — referencia visual en Img→Prompt**

Cuando subes imagen de storyboard a la app, antes describía el grid
literalmente. Ahora con switch ON:
- Extrae solo paleta/iluminación/personajes/estilo gráfico.
- IGNORA composición de paneles, layout grid, viñetas.
- Genera prompt original para una escena que mantenga esa guía visual.

Ubicación: barra superior junto a NSFW/Auto-trad (púrpura, persistente).
Detección automática vía `is_natural` del modelo seleccionado.

**2. `8ca1819` Selector "Shots:" (Auto/1-6) — calibrado por duración**

Bug encontrado: el LLM generaba 5 shots para vídeos de 10s, lo que
causa errores en Seedance (mínimo ~3s por shot). Solución:

Combo `Shots:` junto a Duración en el panel de vídeo:
- "Auto" (default): regla rule-based según duración.
    4s→1 · 5s→2 · 10s→3 · 15s→4 · >15s→ceil(dur/4) capped 6
- "1-6": override manual exacto.

Inyección en system prompt:
```
🎬 NÚMERO DE SHOTS: EXACTAMENTE N shots para una duración total de
   Xs (~Y.Ys por shot). NO añadas más ni menos.
```

Helpers nuevos en `PromptsInyeccionService`:
- `_calcular_n_shots()`
- `_duracion_a_segundos()` (parsea "10s", "4-6s", etc.)

**3. `500e9ef` Fix parser — añadir PANEL al regex**

El comparador del Storyboard mostraba TODOS los paneles como una
única "Variación #1" en lugar de N bloques separados. Causa:
`_parsear_bloques_numerados` solo reconocía `PROMPT|SHOT|FRAME|
VARIANTE|VERSION` como prefijos, pero el storyboard usa `PANEL 1`,
`PANEL 2`, etc. → caía al fallback de "1 bloque completo".

Fix: añadido `PANEL` a la lista + `\n` al set de chars de fin
(porque PANEL N va seguido de newline, no `:`).

### Lección de workflow externo (no es bug nuestro)

El vídeo del usuario en SeaArt seguía mostrando el storyboard como
frame 1 incluso con el prompt corregido. **Causa real**: Seedance
2.0 en SeaArt interpreta imagen-junto-con-prompt como image-to-video
(la imagen pasa a ser el frame 1 literal). Solución: pegar SOLO el
texto del prompt en SeaArt (no subir la imagen del storyboard ahí).

Documentado para sesión 12+: añadir nota visible en la UI cuando el
usuario active "🖼 Ref" recordando NO subir esa imagen otra vez en
la plataforma de vídeo destino.

### Tests añadidos

- **+10** en `TestCalcularNShots`: Auto en 4s/5s/10s/15s + cap a 6
  para duraciones largas + override manual + valor inválido cae a
  Auto + sin shots_var en app + parsing "4-6s".
- **+2** en `TestWorkerImagenAPrompt`: modo referencia visual usa
  prompt distinto + prioriza sobre prompt existente.

Total: 228 → **240** verdes.

### Commits sesión 11

```
500e9ef fix(parser): añadir PANEL al regex de _parsear_bloques_numerados
8ca1819 feat(video): selector "Shots:" (Auto/1-6) + regla por duración
12de567 feat: switch "🖼 Ref" — Img→Prompt como referencia visual
436236c refactor(A1 fase 2): DashboardMixin → DashboardService (4/20)
```

### Métricas finales sesión 11

| Métrica | Antes | Ahora |
|---|---:|---:|
| Tests | 228 | **240** (+12) ⭐ |
| Mixins en MRO | 18 | **17** (-1) ⭐ |
| A1 fase 2 progreso | 3/20 | **4/20** |
| Componentes A1 | 20/20 | 20/20 |
| Switches en barra superior | 3 | **4** (+ 🖼 Ref) |
| Selectores en panel vídeo | 4 (Modelo/Dur/Ratio/Destino) | **5** (+ Shots) |

---

## ✅ Sesión 12 — UX comparador (lado-a-lado + grid Pollinations)

### Nueva UX en el comparador (ee3ad10, 0f0ed76)

Dos features grandes al comparador genérico (`_abrir_comparador`):

**1. 🆚 Comparar 2 lado-a-lado** (`ee3ad10`)
- Checkbox `🆚` en la cabecera de cada columna.
- Botón `🆚 Comparar 2` en el pie (deshabilitado por defecto, púrpura
  cuando hay exactamente 2 seleccionadas — FIFO si marcas una 3ª).
- Ventana 50/50 con diff palabra-por-palabra usando
  `difflib.SequenceMatcher`:
    - Tokens iguales → color muted normal.
    - Tokens en A pero no en B → fondo rojo en panel izquierdo.
    - Tokens en B pero no en A → fondo verde en panel derecho.
- Botones pie: copiar A / copiar B / cerrar.

**2. 👁 Pollinations preview** (`0f0ed76`)
- Botón `👁` por card → genera preview Flux/Turbo 512x512 y la
  incrusta como thumbnail dentro de la propia card.
- Botón `👁 Grid Pollinations` en el pie → ventana nueva con grid
  3-col mostrando previews de TODAS las variantes en paralelo.
- En el grid, click en una imagen abre versión 1024x1024 en navegador.
- Cache LRU en `~/.arquitecto_prompts/preview_cache/{md5}.png`
  (keyed por prompt+size).

### Saga Pollinations: 4 fixes hasta que funcionó (9ee6f8c, b7224f4, bc0e68e, 0d7f5f1)

Pollinations.ai migró a freemium durante 2026:
- **flux** → modelo de pago (HTTP 402)
- **turbo** → sigue libre pero con **rate limit 1 request concurrente
  por IP** para anónimos (también devuelve 402 con body JSON
  `{"x402Version":1,"error":"Queue full for IP: X: 1 already queued..."}`)

Fixes:
- `9ee6f8c`: flux → turbo + fallback al default sin model param.
- `b7224f4`: mensajes de error informativos (402 vs 429 vs 5xx vs
  Content-Type no-imagen).
- `bc0e68e`: **El fix clave**. `threading.Lock()` global en
  `ArquitectoApp.__init__` → el worker entra en `with self.
  _pollinations_lock:` antes de cada request. Garantiza max 1
  simultánea aunque el grid lance N en paralelo. Retry con backoff
  exponencial (2s/4s/8s) hasta 3 intentos por modelo. Discrimina
  "queue full" de "cuenta de pago requerida" leyendo el body JSON.
- `0d7f5f1`: `cmd_previsualizar` (botón "🖼 Preview" del panel
  principal) usaba `urllib.request` directo con flux. Refactor para
  reusar `_generar_preview_pollinations` (semáforo + retry + turbo).

### Lección aprendida sobre PyInstaller

Durante el debug del fix de Pollinations: los cambios en `app.py`
parecían no llegar al `.exe` reconstruido (seguía mostrando mensajes
de error del código viejo). Diagnóstico final:

1. PyInstaller NO siempre invalida bytecode cuando solo cambia el
   `.py` fuente — el archivo `base_library.zip` cachea los `.pyc`.
2. `find . -name "__pycache__" -type d -exec rm -rf {} +` ANTES de
   `python build.py` es necesario para builds 100% limpios.
3. `rm -rf build dist` solo no es suficiente.

Anotar para sesión 13: añadir `--clean-cache` flag a `build.py` que
borre `__pycache__/` además de `build/` y `dist/`.

### Trade-off del semáforo

El grid de 5 previews ahora tarda ~25-30s (5 × ~5s serializado) en
lugar de ~5-10s (paralelo, pero fallando 4 de 5). Es el precio
necesario por el rate limit anónimo de Pollinations.

Mejora UX pendiente: mostrar `⏳ En cola (3 por delante)` en lugar de
`cargando...` para que el usuario entienda que está esperando, no
colgado.

### Commits sesión 12

```
0d7f5f1 fix(preview): cmd_previsualizar reusa el helper con semáforo/retry
bc0e68e fix(pollinations): serializar requests (1 concurrente por IP) + retry
b7224f4 fix(pollinations): diagnóstico de errores más informativo
9ee6f8c fix(pollinations): cambiar de flux (de pago) a turbo + fallback
0f0ed76 feat(comparador): preview Pollinations por card + grid 👁 de todos
ee3ad10 feat(comparador): vista 🆚 lado-a-lado con diff palabra-por-palabra
```

### Métricas finales sesión 12

| Métrica | Antes | Ahora |
|---|---:|---:|
| Tests | 240 | 240 ✅ |
| Mixins en MRO | 17 | 17 (sin cambios A1 esta sesión) |
| Componentes A1 | 20/20 | 20/20 |
| Botones en comparador | 6 (📋🟢🔴🇪🇸✅) | **9** (+ 🆚 + 👁 + 👁Grid) |
| Métodos en ArquitectoApp | — | +2 (`_abrir_diff_lado_a_lado`, `_generar_preview_pollinations`, `_abrir_grid_pollinations`) |
| Bugs latentes Pollinations | flux 402, queue 402 | 0 ✅ |

---

## ✅ Sesión 13 — UX cola Pollinations + Z-Image-Base con bloques narrativos

### Bloque 1: UX cola Pollinations (58f7d0d, db0eaa9)

Feedback usuario sesión 12: el grid de 6 previews tardaba ~25s
serializando, pero todas las cards mostraban "cargando..." sin
indicación de turno → daba sensación de cuelgue.

**`58f7d0d` feat: "⏳ En cola (N por delante)"**
- Nuevo contador `self._pollinations_queue_size` con su propio lock
  (`self._pollinations_queue_lock`). Cada worker incrementa al
  entrar, decrementa al obtener el semáforo principal.
- Parámetro `on_progress` opcional en `_generar_preview_pollinations`:
  callback que la UI usa para mostrar `⏳ En cola (N por delante)`
  inicialmente, luego `🎨 Generando...` cuando le toca.
- Cableado en grid + per-card preview del comparador.

**`db0eaa9` feat: retry largo + ♻ Regenerar**
- Retries 3 → 4 por modelo. Backoffs 2/4/8s → 3/10/30s (total 43s
  wait). Cubre el rate limit por minuto que Pollinations aplica a
  IPs anónimas (descubierto al testear).
- Durante backoff: muestra `⏳ Sobrecarga, esperando 30s...`
- Mensaje de error específico: si ≥4 intentos fueron "queue full",
  el error final es `Pollinations sobrecargado. Espera 1-2 min y
  pulsa ♻ para reintentar.` (antes: `Cola Pollinations llena,
  reintentando...` engañoso).
- Botón `♻ Regenerar` por card en el grid: oculto por defecto,
  aparece solo al fallar. Click → relanza esa card sola con
  `force_refresh=True` (borra caché previa).

### Bloque 2: Z-Image-Base con bloques narrativos (f13f11d, 0ccd031)

Usuario aportó docs oficiales del modelo + ejemplos de prompts que
estaba usando con éxito en SeaArt. Z-Image-Base es un Foundation
checkpoint de 6B params con arquitectura S3-DiT que prefiere un
formato HÍBRIDO específico:

**`f13f11d` feat: nuevo modelo Z-Image-Base**
- Añadido a `config.py` (grupo "Familia Z-Image").
- Spec en `data/model_specs_imagen.json` con flags nuevos:
  - `is_natural: true`
  - `has_negative: true`
  - `formato_bloques: "z_image"` ← dispara la ruta especial.
  - `pasos: "28-50"`, `cfg: "3-5"`.
- Dispatcher en `_inyectar_specs_formato`: si
  `specs.formato_bloques == "z_image"`, delega a nuevo
  `_inyectar_formato_z_image()`.
- El método inyecta TODA la estructura:
  - Preámbulo de quality tags con pesos: `(masterpiece, top quality,
    raw photo:1.2), 8k, ultra-detailed, cinematic composition`
  - 4 bloques narrativos obligatorios: `[Sujeto y Composición]`,
    `[Acción]`, `[Entorno]`, `[Lighting & Mood]`.
  - NEGATIVE PROMPT con bloques dinámicos por categoría
    (Fotorrealismo / Fantasía Mística / Ciencia Ficción).

**`0ccd031` feat: negative ADAPTATIVO en 3 bloques**
- Feedback usuario: el bloque "universal" anterior era demasiado
  rígido (metía `extra fingers` aunque no hubiera personas).
- Refactor a 3 bloques:
  1. **BASE** — solo calidad técnica (siempre): `blurry, low-res,
     watermark, signature, cropped, out of frame, digital noise,
     jpeg artifacts`.
  2. **CONDICIONAL** — el LLM elige según contenido de la escena:
     - Personas/criaturas con manos → anatomía
     - Caras/retratos → asymmetric eyes, distorted face
     - SIN texto intencional → distorted text (SI sí hay: omite)
     - Detalle alto (close-up) → low detail, smooth
     - Paisaje sin humanos → omite anatomía/caras
     - Estático vs movimiento → motion blur vs static
  3. **ESTILÍSTICO** — categoría (Fotorrealismo / Fantasía / SciFi).
- 2 ejemplos finales en el system prompt para guiar al LLM.

### Validación end-to-end con usuario

Probó con idea "criatura Lovecraftian descongelándose". Output:
- POSITIVE perfecto: 4 bloques en orden, descripción cinematográfica.
- NEGATIVE adaptó perfectamente:
  - ✅ Incluyó anatomía (tentáculos cuentan como extremidades).
  - ✅ NO incluyó tags de caras humanas (no es retrato humano).
  - ✅ Incluyó `low detail, smooth, simplified` (close-up macro).
  - ✅ Detectó "Lovecraftian" → mezcló Fotorrealismo + Fantasía
       Mística (decisión razonable híbrida, no estrictamente UNA
       categoría como decían las reglas).

Decisión: dejar comportamiento híbrido (más flexible para escenas
mixtas).

### Tests añadidos

- `TestInyectarFormatoZImage` (sesión 13a): 7 tests verificando
  que el método inyecta los 4 bloques, preámbulo de quality tags,
  3 categorías, settings recomendados, y se activa via dispatcher.
- `0ccd031`: 2 tests extra verifican que la anatomía está en bloque
  condicional (no base) — confirma la refactorización.

Total: 240 → **249** verdes.

### Lección sesión 13

- "Universal" en negativos es engañoso — los tags tipo `extra
  fingers` solo aplican si hay manos en la escena. Estructurar el
  prompt para que el LLM elija activamente cada bloque produce
  outputs más limpios.
- PyInstaller cachea bytecode incluso con cambios en `.py`: borrar
  `__pycache__/` + `build/` + `dist/` antes del `python build.py`
  es necesario para builds 100% limpios. Patrón establecido:
  ```bash
  find . -name "__pycache__" -type d -exec rm -rf {} +
  rm -rf build dist
  python build.py
  ```
  Confirmado por necesitar 3 intentos en sesión 13 hasta acertar.

### Commits sesión 13

```
0ccd031 feat(z-image): negative ADAPTATIVO en 3 bloques (base + condicional + estilo)
f13f11d feat(z-image): soporte Z-Image-Base con bloques narrativos + negative dinámico
db0eaa9 feat(pollinations): retry largo + mensaje claro + ♻ Regenerar por card
58f7d0d feat(pollinations): mostrar "⏳ En cola (N por delante)" en cargas
```

### Métricas finales sesión 13

| Métrica | Antes | Ahora |
|---|---:|---:|
| Tests | 240 | **249** (+9) ⭐ |
| Mixins en MRO | 17 | 17 (sin cambios A1 esta sesión) |
| Modelos imagen | 99 | **100** (+ Z-Image-Base) |
| Botones por card en grid Pollinations | 0 | **1** (+ ♻ Regenerar al fallar) |
| Estados visibles del worker Pollinations | "cargando..." | 4 (En cola N · Generando · Sobrecarga Ns · Error claro) |

---

## ✅ Sesión 14 — A1 fase 2 COMPLETO (10 mixins migrados, 16→1 en MRO)

### Maratón A1 fase 2: 10 commits en una sesión

| # | Mixin | Métodos | Call sites | Tests reescritos | Commit |
|---|---|---:|---:|---:|---|
| 5 | AbTestingMixin → AbTestingService | 5 | 0 | 11 | `9c20fa3` |
| 6 | AdnVisualMixin → AdnVisualService | 2 | 0 | — | `1136d64` |
| 7 | ModoClienteMixin → ModoClienteService | 5 | 0 | — | `62825c9` |
| 8 | MultiPromptMixin → MultiPromptService | 10 | 0 | — | `cc0ab57` |
| 9 | BackupExportMixin → BackupExportService | 8 | 0 | — | `fb018f3` |
| 10 | WorkersIaMixin → WorkersIaService | 5 | 0 | 31 | `d4a76bc` |
| 11 | RefinamientoMixin → RefinamientoService | 6 | 0 | 32 | `2e2645f` |
| 12 | ToolsAnalysisMixin → ToolsAnalysisService | 23 | 0 | — | `cdf48e4` |
| 13 | ToolsWorkflowMixin → ToolsWorkflowService | 14 | 0 | — | `cbdd40b` |
| 14 | ToolsCreativeMixin → ToolsCreativeService | 18 | 0 | — | `05202d3` |
| 15 | UIBuildersMixin → UIBuildersService | 26 | 21 | — | `da5a9d3` |
| 16 | UiEventsMixin → UiEventsService | 8 | 15 | 18 | `3b1aad9` |
| 17 | SesionVideoMixin → SesionVideoService | 12 | 27 | — | `c104ca1` |
| 18 | DataMgmtMixin → DataMgmtService | 30 | 12 | — | `f8bb2e3` |
| 19 | UiFooterMixin → UiFooterService | 29 | 75 | — | `90f9b21` |
| 20 | DialogsMixin → DialogsService | 17 | **570** | — | `d31310c` |

**Total**: ~218 métodos migrados, ~720 call sites bulk-replaced.

### Patrón establecido y refinado

1. Service class con `__init__(self, app)`.
2. Script `_tmp_migrate.py` con SERVICE_ATTRS específicos para hacer
   `self.X` → `self.app.X` (preservando métodos internos del service).
3. Fix manual de patrones widget: `widget(self,...)` → `widget(self.app,...)`,
   `parent=self` → `parent=self.app`, `hasattr/getattr(self, var)` →
   `hasattr/getattr(self.app, var)`.
4. Component con `__slots__ = ("app", "_service")` + `__init__` instanciando
   service + delegate via `_service` para entry points + `__getattr__`
   para métodos no listados (cuando se usan desde muchos sitios).
5. Bulk replace de call sites externos con script Python.
6. Tests con shortcut `app.footer = app` y `app.dialogs = app` para que
   los mocks viejos sigan funcionando transparentemente.

### Lecciones aprendidas

- **Los más fáciles**: mixins con pocos call sites externos (AdnVisual,
  ModoCliente, Backup) — directos.
- **Los medio**: los que tienen tests (Workers, Refinamiento, UiEvents,
  AbTesting) — reescritura mecánica del helper `_host()`.
- **Los duros**: los con muchísimos call sites (Sesion 27, Data 12,
  UiFooter 75, **Dialogs 570**). Estos requirieron bulk replace
  cross-files.
- **DialogsMixin fue el más invasivo** por `set_estado`,
  `actualizar_salida`, `toggle_botones` usados en CIENTOS de sitios.
  La solución: shortcut `app.dialogs = app` en los tests evitó
  reescribir 100+ aserciones.

### Métricas finales sesión 14

| | Empezando | Cerrando |
|---|---:|---:|
| Mixins en MRO | **17** | **1** ⭐⭐⭐ (-16) |
| A1 fase 2 progreso | 4/20 | **20/20** ✅ COMPLETO |
| Tests | 249 | **249** (sin regresiones) |
| Componentes A1 | 20/20 | 20/20 |
| Working tree | Limpio | Limpio ✅ |

### Estado final

`ArquitectoApp` ahora hereda **únicamente** de:
- `ctk.CTk` (la app es un widget Tk)
- `CoreMixin` (el mixin fundamental con `__init__`, helpers de
  prompt building, _abrir_comparador, _parsear_*, etc.)

Los otros 20 mixins están como **Service classes aisladas**
accesibles vía componentes (`app.dialogs`, `app.ui`, `app.events`,
etc.).

---

## ✅ Sesión 15 — Tests + cascada de regresiones A1 + sistema LoRA repensado

Sesión muy productiva: 17 commits cubriendo desde tests a features
nuevas pasando por una **cascada de bugs de A1 fase 2** que impedía
arrancar la app y un **rediseño completo del flujo de LoRAs** para
que sea usable end-to-end sin tener que mantener Personaje + LoRA
sincronizados a mano.

### Bloque 1 — Cobertura de tests (+112 tests, 249 → 361)

Tests para los 7 mixins sin cobertura que listaba el HANDOFF:
- `test_adn_visual.py` (5 tests) — guards de comandos.
- `test_modo_cliente.py` (6 tests) — worker propuestas, formatos.
- `test_multiprompt.py` (17 tests) — STORY_SHOT_TYPES, helpers, guards
  de los 4 cmd.
- `test_atajos_ayuda.py` (17 tests) — `_cmd_cambiar_modo`, exportar
  rápido, traducir, fullscreen.
- `test_sesion_video.py` (14 tests) — `_sesion_init`, `_sesion_log`,
  `_sesion_agrupar_pasos`, narrativas.
- `test_dialogs.py` (23 tests) — `_darker`, `set_estado`,
  `actualizar_salida`, `toggle_botones`, progreso, tokens, tema.
- `test_core.py` (30 tests) — `extraer_positive`/`negative`,
  `_parsear_variaciones`, `_recortar_si_excede`, `_extraer_pos_de_bloque`.

Patrón establecido: SimpleNamespace + mock de ctk.* + threading.Thread.
Documentado en cada archivo el bug latente del `while True` en
`_colorear_resultado` que requiere mockear `txt.search` con `""`.

### Bloque 2 — Cascada A1 fase 2 (app arrancando otra vez)

La maratón A1 fase 2 (sesión 14) removió 16 mixins del MRO de
`ArquitectoApp` pero dejó **MUCHOS** call sites legacy que asumían
que `self` era el app o que ciertos métodos estaban heredados. La
app **crasheaba al arrancar** desde la primera línea de
`_build_author`. Fixes en un solo commit:

1. **`__getattr__` en `ArquitectoApp`** (red de seguridad sistémica):
   delega a los `_service` de los componentes registrados como
   fallback antes de tirar `AttributeError`. Esto cubre cualquier
   `self.app._método()` superviviente.
2. **`_build_author` en dialogs.py**: `CTkFrame(self, ...)` →
   `CTkFrame(self.app, ...)`. El service no es un widget Tk.
3. **Bulk replace de 28 call sites** `self.app._on_X_cambio` →
   `self.app.events.on_X_cambio` en 9 archivos.
4. **Helpers externos** que recibían `self` (que ya no era el app)
   en `ui_builders` (abrir_lista, abrir_loras, abrir_personajes),
   `atajos_ayuda` (GPromptWindow), `modo_cliente`, `tools_creative`.
5. **`_on_resize` en ui_builders**: el guard `event.widget is not
   self` era siempre True (self ahora es el service, no el app),
   causando que los botones del header se quedaran en "modo
   compacto" (cuadrados de 42px solo emoji) permanentemente.

### Bloque 3 — Bugs de menús (4 menús rotos)

1. **📖 Guía de estilos** no abría: `abrir_guia_estilos(self, ...)`
   con `self` = service. Fix → `self.app`.
2. **📖 Modo educativo** no abría: `abrir_glosario(self)` mismo error.
3. **📋 Plantillas** "no se pudieron cargar" — la carpeta `config/`
   no estaba en `datas` del PyInstaller spec. Añadido a los 2 specs.
4. **🎯 Modo Focus** dejaba un hueco negro arriba al salir — el
   re-pack usaba `after=prev` que rompía el orden de los frames.
   Fix: `pack(before=frame_entrada)` para TODOS + `update_idletasks()`.

### Bloque 4 — Quick wins MEDIA del HANDOFF

- **`build.py --clean-cache`**: nuevo flag que combina `--clean` con
  borrado recursivo de `__pycache__/` (resuelve el problema de
  PyInstaller cacheando bytecode viejo documentado en sesiones 12-13).
- **Toast 🖼 Ref ON**: al activar el switch, aparece la nota
  *"pega SOLO el prompt en la plataforma de vídeo destino — NO
  subas otra vez la imagen ahí"*. Resuelve la confusión de sesión 11
  con Seedance interpretando la imagen como image-to-video.

### Bloque 5 — Sistema LoRA repensado (el corazón de la sesión)

Reportes encadenados del usuario que terminaron en un rediseño
completo del flujo LoRA con Z-Image-Base:

1. **Familia Z-Image** no detectada en `_es_lora_compatible` (siempre
   "⚠️ familia distinta"). Añadido detector `z-image`/`z image`/
   `z_image` como primera rama del matcher.

2. **Trigger del LoRA no aparecía en el output**: el LLM ignoraba
   la sugerencia "LoRA: trigger" como contexto informativo. Fix en
   2 capas:
   - Instrucción imperativa en `construir_modelo_info`.
   - **Safety-net** en `_garantizar_lora_trigger` (workers_ia.py)
     que inserta el trigger automáticamente si el LLM lo olvidó.

3. **Plantilla Z-Image** con bloque dedicado `[LoRA Activation &
   Style]` cuando hay LoRA activo + estructura 4 bloques en inglés
   (Subject & Composition / LoRA Activation & Style / Lighting &
   Environment / Mood). Sin LoRA mantiene plantilla cinematográfica
   clásica.

4. **Anti-duplicado del trigger**: el LLM ponía el trigger en
   preámbulo + bloque dedicado. Safety-net detecta el bloque
   dedicado y elimina apariciones fuera de él automáticamente.

5. **Toggle "Estilo Z"** (Auto/Photoreal/Creative/Fantasy/SciFi) —
   combo que aparece junto al modelo SOLO si es de la familia
   Z-Image. Fuerza la categoría del bloque NEGATIVE estilístico
   sin que el LLM tenga que adivinar.

6. **Sistema multi-LoRA**: combo primario + botón `🔗+` que abre
   modal con checkboxes para combinar varios LoRAs. Indicador
   inline "🔗+N" junto al trigger. Persistido en
   `preferences.json["loras_multi"]`. Inyección unificada:
   `"trig1 style + trig2 style + ..."` en el bloque dedicado.

7. **Validación de trigger mal formado** al guardar LoRAs: avisa
   (no bloqueante) si el trigger tiene >40 chars, >8 palabras o
   puntuación de prosa. Acepta comas (multi-trigger válidos como
   `Nyra, Amber Eyes, Undercut`).

8. **Campo "Rasgos visuales" en cada LoRA** — la feature clave que
   resuelve el problema raíz. Para LoRAs de personaje, el usuario
   guarda los rasgos físicos (pelo, ojos, complexión, vestuario)
   en el propio LoRA. La app los inyecta automáticamente en
   `[Subject & Composition]` sin necesidad de mantener un Personaje
   separado.

   Workflow nuevo (validado con LoRA "Nyra for Z-image"):
   - LoRA con `rasgos_visuales` rellenado.
   - Sin Personaje en el combo.
   - Idea: solo escena/acción.
   - Resultado: Nyra pelirroja+undercut+ámbar EN LA ESCENA, sin
     contradicciones, sin tener que crear Personaje aparte.

9. **Contexto LoRA/personaje en TODOS los comandos generativos** —
   no solo `cmd_prompt`. Helper centralizado
   `_contexto_loras_personaje(intro)` en CoreMixin aplicado a:
   `cmd_ideas`, `cmd_prompt_quick`, `_cmd_moodboard`,
   `_cmd_story_sequence`, `_cmd_storyboard_video`,
   `_cmd_storyboard_imagen`, Walk `_ramificar`. Antes generaban
   ideas/variaciones genéricas; ahora respetan el LoRA activo.

10. **Panel "🎯 Fuentes activas"** con chips clickables que muestra
    qué se está inyectando en el prompt:
      🧑 Personaje · 🔗 N LoRAs · ⚓ Anclaje · 🧬 ADN.
    Click → limpia esa fuente (combo a "Sin X", anclaje a None,
    multi-LoRA vaciado, etc.) + persiste el cambio. Se oculta solo
    cuando no hay nada activo.

### Bloque 6 — Auditoría de specs (empezada)

- **SeaArt Film Video** (data/model_specs_video.json):
  - `has_negative: false` → `true`.
  - `max_chars: 2400` → `1500`.
  - Quitada la frase "Sin prompt negativo" de limitaciones.

Quedan 118 modelos imagen + 14 vídeo + 10 audio por revisar.

### Resumen de la sesión 15

| Métrica | Inicio | Cierre |
|---|---:|---:|
| Tests | 249 | **373** (+124) |
| App arranca | ❌ Crash | ✅ |
| Menús funcionando | 4 rotos | ✅ Todos |
| LoRAs usables | ⚠️ confusos | ✅ flujo unificado |
| Mixins en MRO | 1 | 1 (sin cambios) |
| Working tree | Limpio | Limpio ✅ |

### Commits sesión 15

```
f8937dc fix(specs): SeaArt Film Video max_chars 2400 → 1500
decea45 fix(specs): SeaArt Film Video sí soporta prompt negativo
98b3bd8 feat: panel "Fuentes activas" con chips clickables
9dcf3ae feat: contexto de LoRAs/personaje en TODOS los comandos generativos
8d7c75b feat(ideas): contexto de LoRAs/personaje activos en cmd_ideas
0097952 feat(loras): campo "Rasgos visuales" para LoRAs de personaje
bacce21 fix(z-image+lora): reforzar verbalmente rasgos del personaje
d8af7f9 fix(z-image+lora): dejar la apariencia del sujeto al LoRA
87ec7c1 fix(loras): relajar validación de trigger
dca5e11 feat(loras): validación de trigger mal formado al guardar
4c377cb feat(loras): sistema multi-LoRA con modal checkboxes
2bbdab0 feat(z-image): toggle "Estilo Z" Auto/Photoreal/Creative/Fantasy/SciFi
1af4962 fix(loras): eliminar duplicación del trigger en preámbulo + bloque
2789526 feat(z-image): bloque [LoRA Activation & Style] dedicado
413b6f4 fix(loras): el trigger del LoRA no aparecía en el prompt generado
1d5890e fix(loras): detectar familia Z-Image en _es_lora_compatible
1ec53b3 feat(quick wins): build.py --clean-cache + aviso 🖼 Ref
f398437 fix: 4 regresiones reportadas por el usuario tras los fixes A1
aaef195 fix(A1 fase 2): cascada de regresiones que impedían arrancar la app
1935a20 test: cobertura de los 7 mixins sin tests (+112 tests, 249 → 361)
```

### 🚧 Pendiente sesión 16+

#### 🔴 ALTA
- **CoreMixin (último mixin restante)**: 33 métodos, 127 call sites
  externos. Es el más complejo. Para abordarlo habrá que decidir si
  vale la pena (la app necesita un esqueleto base) o dejarlo como
  "foundation" definitiva.

#### 🟡 MEDIA
- **Toggle modelo Pollinations** (turbo / kontext / sdxl / anime)
  como combo en el comparador.
- **Variante SD/Comfy del storyboard imagen** (tag-based directo
  con POSITIVE/NEGATIVE + pesos, sin tener que refinar uno a uno).
- **Particiones de archivos grandes** (`core.py` 1700+, `data_mgmt.py`
  1545, `ui_builders.py` ~1700 tras los cambios de sesión 15).
- **Auditoría de specs** — empezada con SeaArt Film Video. Quedan
  118 modelos imagen + 14 vídeo + 10 audio.
- **Verificar installer end-to-end** en VM/usuario nuevo: instalación
  limpia → arranque → desinstalación.

#### 🟢 BAJA
- Code-signing del `.exe` (SmartScreen warning).
- Performance: lazy load de `data/*.json`, semáforo workers IA,
  virtual scrolling historial/favoritos.
- Features ambiciosos: PDF export, plugin system, API REST.

---

## ✅ Sesión 16 — Auditoría de specs + sistema "Estilo por familia"

Sesión enfocada en **calidad de output** para los modelos que el
usuario realmente usa. Política establecida: todas las auditorías de
modelos se hacen **desde la perspectiva de SeaArt** (cómo aparecen y
se comportan en SeaArt, no en API original ni otras plataformas).

### Bloque 1 — Documentación viva para futuras auditorías

Creado **`AGREGAR_MODELO.md`** en la raíz: guía con plantilla JSON,
checklist pre-commit, tabla de campos críticos vs informativos,
método empírico para medir `max_chars`, los 4 sitios a actualizar
al añadir un modelo, y ejemplos validados. Pensado para incorporar
modelos sesión a sesión sin recordar todos los pasos.

### Bloque 2 — Auditoría familia Z-Image (SeaArt)

- **Z Image Turbo**: nota 4.6→**4.3**, pasos 20→**8**,
  max_chars 1500→**2000** (medido), best_for reescrito.
- **Z-Image-Base**: nota 4.7→**4.8**, max_chars 1800→**2000**.
- **Z-Image-Base-Realistic eliminado** (no disponible en SeaArt).

### Bloque 3 — Bug latente: `max_chars_negative` hardcoded a 1500

`_recortar_si_excede` en core.py tenía `NEGATIVE_MAX = 1500` hardcoded.
Truncaba el NEGATIVE a 1500 incluso en modelos donde el límite real
es el mismo que el POSITIVE.

Fix: nuevo parámetro `max_chars_negative`. Si `None`, usa
`max_chars` (mismo límite POSITIVE/NEGATIVE — comportamiento real
SeaArt). `workers_ia.py` lee `specs.get("max_chars_negative")` y lo
pasa al recortador. Test actualizado + nuevo test del override.

### Bloque 4 — SeaArt Film Video corregido

`has_negative: false→true`, `max_chars: 2400→1500`. Limpieza de
limitaciones.

### Bloque 5 — Auditoría familia GPT Image (SeaArt)

- **GPT Image 1** y **mini eliminados** (no en SeaArt).
- **GPT Image 2**: nota 4.9→**4.5**, max_chars confirmado **5000**
  (medido, corta en 4997). Ratios 13→**9** (solo aspect ratios
  estándar). Modos Low/Med/High→**Baja/Media/Alta** (etiquetas
  SeaArt). Nuevos campos: `resoluciones [1K, 2K, 4K]`,
  `max_imagenes 8`, `max_imagenes_referencia 10`,
  `magia_sugerencia [Auto, Abrir, Cerrar]`.
- **GPT Image 1.5**: nota 4.7→**3.5**, max_chars 4000→**2000**
  (medido). modos→**["2048×2048"]** (única resolución). Ratios
  8→**10**. `max_imagenes_referencia: 7`.

### Bloque 6 — Plantilla `formato_bloques: "gpt_image"`

Análoga a `z_image` pero adaptada al lenguaje natural de GPT.
Nuevo método `_inyectar_formato_gpt_image()` con **7 bloques en
inglés**:

```
[Subject] sujeto + rasgos físicos + ropa + pose
[Setting] lugar + entorno + props + era
[Lighting] fuente + dirección + calidad + mood
[Style] photoreal/cinematic/illustration + lente/film
[Composition] shot + ángulo + framing
[Mood] atmósfera emocional
[Text in image] SOLO si el usuario menciona texto → con comillas
```

Reglas: NO NEGATIVE, NO pesos numéricos, NO triggers SD,
`[Text in image]` se OMITE si no aplica.

Integración con multi-LoRA: si hay LoRA con "Rasgos visuales", se
inyectan en `[Subject]` como REFUERZO verbal (NO se crea bloque
`[LoRA Activation & Style]` porque GPT no usa triggers SD).

Validado en vivo: GPT Image 2 generó imagen con "NEON DREAMS"
enorme en una billboard, demostrando que el bloque `[Text in image]`
funciona end-to-end.

### Bloque 7 — Sistema "Estilo por familia" (refactor + extensión)

Refactor del antiguo toggle "Estilo Z" a un sistema **genérico
por familia**. Cada familia declara sus estilos en
`config.ESTILOS_POR_FAMILIA` y la UI los muestra dinámicamente.

Diccionario inicial (ampliable):

```python
ESTILOS_POR_FAMILIA = {
    "z_image":   ["Auto", "Photoreal", "Creative", "Fantasy", "SciFi"],
    "gpt_image": ["Auto", "Photoreal", "Editorial", "Illustration",
                  "UI-Mockup", "Poster-Typography"],
}
```

Cambios:
- `z_image_estilo_var` → **`familia_estilo_var`** (genérico, compat
  con la pref vieja `z_image_estilo`).
- `frame_z_estilo` → **`frame_familia_estilo`** + label "Estilo Z"→
  "Estilo".
- `_on_modelo_imagen_cambio`: detecta familia → repuebla combo →
  muestra/oculta panel + reset a "Auto" si el valor previo no
  encaja.
- `_inyectar_formato_z_image`: lee `familia_estilo_var`.
- `_inyectar_formato_gpt_image`: nuevo bloque "🎯 ESTILO FORZADO"
  con hints específicos para los 5 estilos no-Auto de GPT.

Para añadir una familia nueva: extender `ESTILOS_POR_FAMILIA` +
añadir entrada en `detectar_familia()` + opcionalmente mapa de
hints en su plantilla específica.

### Estado del catálogo al cierre

| Categoría | Auditados | Total |
|---|---:|---:|
| Imagen | 4 ✅ | 117 (-2 eliminados) |
| Vídeo | 1 ✅ | 15 |
| Audio | 0 | 10 |

Auditados: Z Image Turbo · Z-Image-Base · GPT Image 1.5 · GPT Image
2 · SeaArt Film Video.

### Commits sesión 16

```
de175e1 feat(estilos): toggle "Estilo" genérico por familia
7454be4 feat(gpt_image): plantilla formato_bloques="gpt_image"
afaec27 fix(specs): GPT Image 1.5 — datos exactos panel SeaArt
7601a72 fix(specs): GPT Image 2 — datos exactos panel SeaArt
9227d18 fix(specs): GPT Image SeaArt — eliminar 1 y 1 mini
2427ca1 docs: añadir AGREGAR_MODELO.md (guía + plantilla)
0f38bf0 fix(specs): eliminar Z-Image-Base-Realistic
2aab178 fix(specs): Z-Image-Base nota 4.7→4.8 + max_chars 1800→2000
9542401 fix: max_chars_negative del spec + Z Image Turbo
```

### Métricas finales sesión 16

| | Empezando | Cerrando |
|---|---:|---:|
| Tests | 373 | **374** (+1) |
| Modelos auditados SeaArt | 0 | **5** ✅ |
| Familias con estilos | 1 (Z-Image) | **2** (+ GPT Image) |
| Plantillas `formato_bloques` | 1 | **2** |
| Working tree | Limpio | Limpio ✅ |

### 🚧 Pendiente sesión 17+

#### 🔴 ALTA
- **CoreMixin → CoreService** (decisión arquitectónica).

#### 🟡 MEDIA
- **Auditoría de specs continúa** — quedan ~112 imagen + 14 vídeo
  + 10 audio. Orden sugerido por uso real:
    - Imagen: Nano Banana, Midjourney, Flux, Ideogram, Recraft,
      Illustrious, SDXL.
    - Vídeo: Seedance, Kling, Veo, Sora, Wan, Hailuo.
    - Audio: Suno (4), Udio, MiniMax, SeaArt MusicGo.
- **Estilos por familia** — extender `ESTILOS_POR_FAMILIA` por
  cada familia auditada (4-6 estilos relevantes).
- **Plantillas `formato_bloques`** — crear para familias con
  prompt format distintivo (Flux con prosa, Midjourney con
  `--parámetros`, etc.).
- Toggle modelo Pollinations en comparador.
- Variante SD/Comfy del storyboard imagen.
- Particiones de archivos grandes.
- Verificar installer end-to-end en VM.

#### 🟢 BAJA
- Code-signing del `.exe`.
- Performance: lazy load JSON, semáforo workers, virtual scrolling.
- Features ambiciosos: PDF export, plugin system, API REST.

---

## 🔁 Cómo continuar (sesión nueva)

1. **Confirmar baseline**:
   ```powershell
   python -c "import app; print('OK')"
   python -m pytest tests/ -q
   ```
   Debe dar `OK` y `228 passed`.

2. **Verificar mixins enchufados**:
   ```powershell
   python -c "import app; print(len([m for m in app.ArquitectoApp.__mro__ if 'Mixin' in m.__name__]))"
   ```
   Debe imprimir `20`.

3. **Verificar build system**:
   ```powershell
   python build.py --help
   ```

4. **Decidir entre**:
   - **A1 Mixins → Composición** (~5-10 días, refactor mayor).
   - **T1 Cobertura tests** — quedan `ab_testing`, `ui_events`,
     `atajos_ayuda`, `dashboard`, `adn_visual`, `multiprompt`,
     `sesion_video`, `modo_cliente`, `dialogs`, `core`. Próximo
     candidato limpio: `ab_testing.py`.
   - **Más particiones** de archivos grandes (`app.py` 2391,
     `ui_builders.py` 2167, `tools_creative.py` 1881, `core.py` 1665,
     `dashboard.py` 1457).
   - **Type hints en mixins viejos** (core, dialogs, tools_*, etc).
   - **Code-signing del .exe** (evitar SmartScreen).
   - **SeaArt char limits** (necesita info del usuario).
   - **Limpieza AppId installer** (con migración del registro).

5. **Patrón de trabajo establecido**:
   - Análisis honesto en tabla antes de tocar.
   - Priorización 🔴 ALTA / 🟡 MEDIA / 🟢 BAJA.
   - Preguntar antes de empezar bloques grandes.
   - 1 commit por bloque coherente.
   - Smoke test (`python -c "import app; print('OK')"`) tras cada Edit.
   - Pre-commit hooks pueden re-formatear (mixed line endings, ruff) y
     requerir `git add` + recommit — patrón conocido.

---

## ⚙️ Atajos útiles para retomar

```powershell
# Ver árbol de commits de la sesión 6
git log --oneline 831f31e..HEAD

# Ver árbol de commits totales (desde HANDOFF v5)
git log --oneline 808eb0a..HEAD

# Ver cambios de un commit
git show <hash>

# Tests
python -m pytest tests/ -v

# Tests con cobertura
python -m pytest tests/ --cov=modules --cov-report=term-missing

# Arrancar app
python main.py

# Verificar dónde se resuelve un método
python -c "import app, inspect, os; print(os.path.basename(inspect.getsourcefile(app.ArquitectoApp._cmd_mostrar_atajos)))"

# Lanzar el .exe ya construido
& "./dist/GPromptStudio.exe"

# Reconstruir el .exe
python build.py             # dist/GPromptStudio/GPromptStudio.exe
python build.py --installer # dist/installer/GPromptStudio-Setup-1.0.0.exe

# Lint local (lo mismo que ejecuta CI)
ruff check .
```

---

## 🪶 Patrones establecidos en sesiones previas (referencia)

### "Reparación progresiva de input"
Para contenido externo (JSON pegado, CSV mal formado), implementar
helper que pruebe N estrategias en orden de menor a mayor agresividad
y reporte cuál se aplicó. Ver `_intentar_reparar_json` en
`modules/json_prompt.py`.

### "Indicador de origen sin exponer valor"
Para datos sensibles (API keys), mostrar **dónde** están guardados
sin revelar el valor. Ver `ubicacion_api_key` en `api_clients.py`.

### "Exportador con limpieza de markdown del LLM"
Cuando se pide al LLM JSON/código, limpiar fences ` ```json `.
Ver `_cmd_exportar_json_prompt` en `modules/json_prompt.py`.

### "Build distribuible con docs"
Cada release: `*.spec` con `hiddenimports` exhaustivos + `build.py`
con flags + `installer.iss` con `AppId` UUID estable + `BUILD.md` con
troubleshooting + `.gitignore` con `dist/` y `build/`.

---

*Generado al final de sesión 6 — **17 commits añadidos**, **210/210 tests**
(+119 nuevos, +131% respecto al inicio), working tree limpio y sincronizado
con origin/main. core.py reducido a 1665 líneas (-38.3% en esta sesión),
dialogs.py reducido a 543 líneas (-72%). **10 particiones + 1 helper
extraído** (_dashboard_palette). **0 imports F401**. Type hints añadidos
a 7 mixins (68 firmas). 2 bugs latentes corregidos (`re` en workers_ia,
AppId en installer). 2 puntos del HANDOFF cerrados como no-actionable
(A2 sin uso, limpieza AppId es sintaxis Inno obligatoria). Bloques de
profundidad **6/6** ✅. Build `.exe` listo, verificado y redistribuido
con installer que ofrece Reparar/Desinstalar/Cancelar. CI activo.
Pendiente principal: A1 Mixins → Composición (20 mixins ya) y T1
cobertura de tests para los 8 mixins restantes sin cubrir.*
