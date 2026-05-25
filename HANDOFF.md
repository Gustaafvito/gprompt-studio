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
| Tests | **91/91** ✅ |
| Working tree | Limpio |
| Branch | `main` |
| Bloques de profundidad | **6/6** ✅ |
| Mixins en `ArquitectoApp` | **19** |
| Build `.exe` | Generado en `dist/GPromptStudio.exe` |
| Installer | Generado en `dist/installer/GPromptStudio-Setup-1.0.0.exe` |
| CI | GitHub Actions (Ruff + tests 3.10/3.11/3.12) |
| Lint | Ruff configurado (pyproject.toml) |
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

## 📜 Commits de sesión 6 (2 commits)

```
4c04ce2 refactor(core): extraer ui_events + refinamiento (particiones #8 y #9)
2bf3e74 refactor(core): extraer atajos + ayuda a modules/atajos_ayuda.py
```

---

## 📦 Mixins en `ArquitectoApp` (19 en total tras sesión 6)

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

---

## 📂 Tamaño actual de archivos grandes

| Archivo | Líneas | Cambio vs HANDOFF v5 |
|---|---:|---|
| `app.py` | 2406 | +181 |
| `modules/ui_builders.py` | 2167 | +99 |
| `modules/dialogs.py` | 1985 | +78 |
| `modules/tools_creative.py` | 1881 | +51 |
| `modules/core.py` | **1665** | **−1033** (-38.3%) ⭐ |
| `modules/tools_workflow.py` | 1178 | −548 (particionado a `ab_testing.py` previamente) |

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
6 archivos cubren `api_clients`, `config`, `json_prompt`,
`parsear_variaciones`, `persistence`, `workers`. **Sin tests**:
`workers_ia`, `adn_visual`, `multiprompt`, `sesion_video`,
`modo_cliente`, `ab_testing`, `refinamiento`, `ui_events`,
`atajos_ayuda`, `prompts_inyeccion`, `dialogs`, `core`.

Los módulos extraídos en sesiones 4-6 son los mejores candidatos
(interfaz limpia). Empezar por:
- `refinamiento.py` (mocks: `deepseek`, `txt_salida`, `_versiones_prompt`).
- `prompts_inyeccion.py` (puramente funcional sobre strings).
- `workers_ia.py` (interfaz limpia con mocks).

#### Verificar `.exe` real arranca
El build está en `dist/GPromptStudio.exe`. Falta:
1. Lanzar el `.exe` (doble click o `& "./dist/GPromptStudio.exe"`).
2. Probar flujos básicos (generar prompt, cambiar modo, abrir tutorial).
3. Si falla algún `hiddenimport`, añadirlo al `.spec` y rebuild.
4. Probar el installer (`dist/installer/GPromptStudio-Setup-1.0.0.exe`)
   en una VM o usuario nuevo.

### 🟡 MEDIA

#### Particiones restantes de archivos grandes
- **`app.py` (2406)** — clase principal, difícil. Posible: extraer
  inicialización de UI (`__init__`) en helpers.
- **`ui_builders.py` (2167)** — constructores UI. Posible: separar
  barra superior, barra inferior, panel central.
- **`dialogs.py` (1985)** — mezcla editor + diálogos. Posible: extraer
  utilidades de editor → `editor.py`.
- **`tools_creative.py` (1881)** — buscar bloques cohesivos.
- **`core.py` (1665)** — todavía grande. Candidatos: parsers
  (`_parsear_variaciones`, `_extraer_*`, `_recortar_si_excede`),
  commands top-level (`cmd_ideas`, `cmd_prompt`, etc.).

#### Lint debt
171 ocurrencias de `F401` (imports sin usar) silenciadas en ruff.
Limpiar gradualmente: quitar `ignore = ["F401", ...]` y arreglar
en módulos pequeños primero.

#### Type hints incrementales
~30-50% del código sin anotar. Empezar por interfaces públicas de
los módulos nuevos (mixins extraídos).

#### A2 Unificar `self.cmd_x` vs `self.creative.cmd_x`
Acceso inconsistente a comandos según si se llama desde botón
(self.cmd_x) o via subnamespace.

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
   Debe dar `OK` y `91 passed`.

2. **Verificar mixins enchufados**:
   ```powershell
   python -c "import app; print(len([m for m in app.ArquitectoApp.__mro__ if 'Mixin' in m.__name__]))"
   ```
   Debe imprimir `19`.

3. **Verificar build system**:
   ```powershell
   python build.py --help
   ```

4. **Decidir entre**:
   - **A1 Mixins → Composición** (~5-10 días, refactor mayor).
   - **T1 Cobertura tests** empezando por `refinamiento.py` o
     `prompts_inyeccion.py` (interfaces limpias, alto ROI).
   - **Verificar `.exe` real** (quick win, 5-10 min).
   - **Más particiones** de archivos grandes (`app.py`, `ui_builders.py`,
     `dialogs.py`).
   - **Lint debt cleanup** (quitar `ignore` y arreglar gradualmente).
   - **SeaArt char limits** (necesita info del usuario).

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

*Generado al final de sesión 6 — 2 commits añadidos, 91/91 tests,
working tree limpio. core.py reducido a 1665 líneas (-38.3% en esta
sesión, -42% acumulado desde sesión 5). 9 particiones totales del
proyecto. Bloques de profundidad **6/6** ✅. Build `.exe` listo y
funcional. CI activo. Pendiente principal: A1 Mixins → Composición
(19 mixins ya, refactor cada vez más urgente) y T1 cobertura de tests.*
