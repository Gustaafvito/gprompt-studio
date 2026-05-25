# 🧾 Handoff — G-Prompt Studio

Documento de continuación para retomar el proyecto en una sesión nueva.
Generado al final de la **sesión 6** (continuación de las sesiones 1-5).
Working tree limpio cuando se generó.

---

## 📍 Estado del proyecto

**G-Prompt Studio** — app de escritorio (Python + customtkinter) para
generar prompts de IA generativa (imagen, vídeo, audio) con LLMs como
motores. Incluye import/export JSON profesional para Veo/Sora/Kling,
sistema de empaquetado `.exe`, y CI/CD configurado.

| Métrica | Valor |
|---|---|
| Tests | **210/210** ✅ |
| Working tree | Limpio |
| Branch | `main` (sincronizado con `origin/main`) |
| Bloques de profundidad | **6/6** ✅ |
| Mixins en `ArquitectoApp` | **20** |
| `core.py` | 1665 líneas (era 2698, **−38%**) |
| `dialogs.py` | 543 líneas (era 1976, **−72%**) |
| F401 (imports muertos) | **0** (antes 171 silenciados) |
| Type hints | ✅ 68 firmas anotadas (mixins nuevos + viejos) |
| Build `.exe` | Reconstruido + verificado arrancando |
| Installer | Con diálogo **Reparar / Desinstalar / Cancelar** |
| Distribuible | `~/OneDrive/Desktop/GPromptStudio-Distribuible/` al día |
| CI | GitHub Actions (Ruff + tests 3.10/3.11/3.12) |
| Lint | Ruff con F401 activo (sin imports muertos) |
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

#### A1 Mixins → Composición pura
`ArquitectoApp` heredaba 14 mixins en sesión 5, ahora **19**. Cada
partición agrava esto. Refactor mayor ~5-10 días. Hace falta:
- Decidir patrón: namespace objects (`self.atajos.bind()`,
  `self.refinamiento.cmd_refinar()`) vs servicios inyectados.
- Migrar mixin por mixin manteniendo retrocompatibilidad.
- Actualizar tests.

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

## 🔁 Cómo continuar (sesión nueva)

1. **Confirmar baseline**:
   ```powershell
   python -c "import app; print('OK')"
   python -m pytest tests/ -q
   ```
   Debe dar `OK` y `210 passed`.

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
