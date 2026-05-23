# 🧾 Handoff — G-Prompt Studio

Documento de continuación para retomar el proyecto en una sesión nueva.
Generado al final de la **sesión 5** (continuación de las sesiones 1-4).
Working tree limpio cuando se generó.

---

## 📍 Estado del proyecto

**G-Prompt Studio** — app de escritorio (Python + customtkinter) para
generar prompts de IA generativa (imagen, vídeo, audio) con 14 LLMs
como motores. Ahora también con **import/export JSON profesional** para
Veo/Sora/Kling y **sistema de empaquetado** para distribuir como .exe.

| Métrica | Valor |
|---|---|
| Tests | **48/48** ✅ |
| Working tree | Limpio |
| Branch | `main` |
| Commits ahead de `origin/main` | **70** (sin push) |
| Total commits sesión 5 | 5 |
| Bloques de profundidad | **6/6** ✅ |
| Mixins en `ArquitectoApp` | **14** |

Estructura: ver `ESTRUCTURA.md`. Empaquetado: ver `BUILD.md`.

---

## ✅ Qué se hizo en sesión 5

### 1. JSON profesional Veo/Sora/Kling (commits `fee7d99`, `ceefba4`, `8399c40`)

Nuevo módulo `modules/json_prompt.py` con `JsonPromptMixin`:

**📥 Importar (`_cmd_importar_json_prompt`)**:
- Modal con textbox grande para pegar JSON + botones:
  - 📋 Pegar portapapeles
  - 📂 Cargar .json desde disco
  - ✅ Importar
- Reparación automática en 4 estrategias progresivas:
  1. Parsear tal cual (caso ideal).
  2. Limpiar newlines literales dentro de strings (state machine que
     respeta comillas escapadas).
  3. Quitar trailing commas (`,]` y `,}`).
  4. Ambas combinadas.
- Al importar:
  - `prompt` (o `positive_prompt`) → `txt_salida` con formato
    `POSITIVE PROMPT: … \n NEGATIVE PROMPT: …` si hay también
    `negative_prompt`.
  - Detecta modo según señales (`duration`/`fps`/`camera`/`vfx_notes`
    → vídeo; `audio.music`/`lyrics` → audio).
  - Cambia modo activo automáticamente y dispara `_on_modo_cambio`.
  - Aplica `aspect_ratio` al combo.
  - Detecta `duration` como nota.
- Modal de resumen con:
  - Lista verde de qué se aplicó.
  - Aviso ámbar si se aplicó autorepair (qué estrategia).
  - Cards scrolleables con cada metadato extra (camera, lighting,
    vfx_notes, audio, style_tags, etc.) y su valor en JSON pretty.
  - Botón "📋 Copiar metadatos extras" para usarlos manualmente.

**📤 Exportar (`_cmd_exportar_json_prompt`)**:
- Toma `txt_salida` y pide al LLM enriquecer a JSON profesional.
- Petición específica por modo:
  - **Vídeo**: duration, aspect_ratio, camera{type,movement,dof},
    lighting{ambient,key,accent}, vfx_notes, audio{music,sfx},
    style_tags (8-12 keywords).
  - **Imagen**: aspect_ratio, camera{lens,angulo,dof}, lighting,
    style_tags, composition.
  - **Audio**: duration, genre, tempo_bpm, instrumentation, mood.
- Limpia fences markdown ` ```json ` si el LLM los añade.
- Valida JSON parseando; si no parsea lo muestra igual con aviso.
- Modal con textbox **editable** del JSON pretty:
  - 📋 Copiar JSON
  - 💾 Guardar .json (filedialog)
  - ✓ Validar sintaxis (re-parsea contenido editado en vivo)
  - Cerrar

**Wiring**:
- `modules/__init__.py` → exporta `JsonPromptMixin`.
- `app.py` → `ArquitectoApp` hereda al final.
- `modules/ui_builders.py` → 2 entradas en menú **📁 Datos** (ordenado
  alfabéticamente):
  ```
  🌟 Estrellas
  📤 Exportar como JSON pro (Veo/Sora/Kling)
  ⭐ Favoritos
  📋 Historial
  📥 Importar prompt JSON pro
  🔗 LoRAs
  🧑 Personajes
  ```

### 2. Gestión de API keys — UX mejorada (commit `c92196b`)

**Nota**: el cifrado de keys **YA estaba implementado** en sesiones
anteriores. El HANDOFF v4 decía "keys.json texto plano" pero era
información desactualizada. Tres capas existentes:
1. **Windows Credential Manager** (keyring del SO) — primero.
2. **keys.json cifrado AES-256-CBC** con clave derivada del hardware
   (MAC + usuario) — fallback.
3. **Variables de entorno .env** — último recurso.

Lo que se añadió en sesión 5 son **detalles UX que faltaban**:

- Nueva función `ubicacion_api_key(provider_id)` en `api_clients.py`
  que devuelve `"keyring"` / `"keys.json (cifrado)"` / `"env (.env)"` / `""`.
- En el wizard de configuración (`_cmd_configurar_api_keys`), cada
  card de proveedor muestra ahora bajo la descripción:
  ```
  🔐 Windows Credential Manager
  🔒 keys.json (AES-256 cifrado)
  📄 variable de entorno .env
  ```
- Botón 🗑 individual al lado de "🌐 Obtener key":
  - Habilitado solo si hay key configurada.
  - Confirma con `askyesno` antes de borrar.
  - Llama a `borrar_api_key(pid)` (limpia keyring + keys.json).
  - Refresca la card sin cerrar la ventana (vía `_refrescar_card`
    helper).

### 3. Sistema de empaquetado .exe (commit `b689c82`)

**Archivos nuevos**:
- `gprompt-studio.spec` — PyInstaller spec con todos los 14 mixins en
  `hiddenimports`, `collect_data_files` de customtkinter + PIL, keyring
  backends por plataforma (Windows/SecretService/macOS), cryptography
  hazmat, `data/` + READMEs como recursos. `console=False`,
  UPX compression.
- `build.py` — Script automatizado con argparse:
  ```powershell
  python build.py             # onedir → dist/GPromptStudio/
  python build.py --onefile   # .exe portable único
  python build.py --installer # build + Inno Setup
  python build.py --clean     # borra dist/ y build/
  ```
  Verifica PyInstaller instalado, busca Inno Setup en rutas estándar
  (PATH + Program Files), valida smoke test antes de empaquetar,
  muestra tamaño del .exe resultante.
- `installer.iss` — Inno Setup 6 script. Empaqueta TODO
  `dist/GPromptStudio/` con LZMA2, lenguajes inglés + español, accesos
  directos opcionales al escritorio, desinstalador en Panel de Control.
  Output: `dist/installer/GPromptStudio-Setup-1.0.0.exe`.
- `BUILD.md` — Documentación: TL;DR, comparativa onedir vs onefile vs
  installer, tabla de tamaños esperados (~80-150 MB), cómo añadir
  icono custom, solución de problemas, notas sobre code-signing
  y SmartScreen.

`.gitignore` actualizado con `dist/`, `build/`, `*.spec~`.

---

## 📜 Commits de sesión 5 (5 en total)

```
8399c40 fix(json-pro): reparación robusta + reordenar menú Datos alfabéticamente
ceefba4 fix(json-pro): autolimpieza de newlines literales dentro de strings JSON
b689c82 build: PyInstaller spec + script + Inno Setup installer + BUILD.md
c92196b feat(keys): indicador de origen + botón borrar individual en cada API key
fee7d99 feat(json-pro): importar/exportar prompts JSON profesional Veo/Sora/Kling
```

---

## ✅ Trabajo total acumulado (sesiones 1+2+3+4+5)

### Menús revisados completos
- 📊 **Análisis** (sesión 1)
- 💾 **Backup** (sesión 1)
- 📁 **Datos** (sesión 1 + sesión 5: 2 entradas JSON pro + reorden alfabético)
- 🛠 **Herramientas** (sesión 1) + 3 detalles menores (sesión 2)
- 📝 **Plantillas** (sesión 1) + 4 detalles menores (sesión 2)
- 🎨 **UI** completo (sesión 2)
- ⚙️ **Workflow** completo (sesión 2 + sesión 3)
- 🎬 **Barra de acciones** (sesión 2) + títulos de grupo (sesión 4)
- 🔻 **Barra inferior** — títulos de grupo (sesión 4)
- 🔑 **API Keys** — wizard con indicador de origen + borrar individual (sesión 5)
- 🎞 **JSON profesional** — import + export Veo/Sora/Kling (sesión 5)

### Bloques de profundidad — 6/6 ✅
- ✅ **Bloque 1** — Ideas clicables, Pulse 3/5/custom, Preview caché (sesión 2)
- ✅ **Bloque 2** — Sugerir top 3, Compar con ganador (sesión 2)
- ✅ **Bloque 3** — Slider N en 6 multi-prompts (sesión 3)
- ✅ **Bloque 4** — Refinar con diff + undo (sesión 4)
- ✅ **Bloque 5** — Walk árbol visual + guardar ruta en Versiones (sesión 4)
- ✅ **Bloque 6** — Story tipos configurables + Board→Vídeo encadenado (sesión 4)

### Particiones de archivos grandes (sesiones 4-5)
- `modules/adn_visual.py` (666 líneas)
- `modules/multiprompt.py` (969 líneas)
- `modules/sesion_video.py` (565 líneas)
- `modules/workers_ia.py` (281 líneas)
- `modules/modo_cliente.py` (869 líneas)
- `modules/json_prompt.py` (657 líneas) ← sesión 5

### Distribución (sesión 5)
- `gprompt-studio.spec` (PyInstaller)
- `build.py` (script automatizado)
- `installer.iss` (Inno Setup)
- `BUILD.md` (documentación)

### Fixes mayores acumulados
- Variaciones convertido de panel inline a modal con cards (sesión 2)
- Comparadores persistentes con highlight dorado (sesión 2-3)
- Compar con N>3 (IndexError + layout) (sesión 2)
- Sugerir/Compar — prompt estricto + extractor (sesión 2)
- Parsers respetan N esperado (sesión 3)
- Diff visual con columna izquierda vacía (sesión 4)
- ADN Visual: candado late-binding + escena con `ilu.get` (sesión 4)
- Lag al cambiar modo: 257 widgets recreados → 0 (sesión 4)
- JSON import con saltos de línea + trailing commas (sesión 5)

---

## 🚧 Pendiente para la próxima sesión

### A) SeaArt + char limits (pendiente de info del usuario, sin cambios)
El usuario reportó en sesión 4 que en webs como SeaArt el límite real
de caracteres es menor que el `max_chars` en
`data/model_specs_imagen.json`. Necesita: que el usuario reporte el
modelo concreto + límite real para corregir las specs.

### B) Build .exe real (pendiente verificar)
El sistema de build está implementado pero no se ha lanzado el build
real (tarda 1-2 min). Próxima sesión:
1. `python build.py` para generar `dist/GPromptStudio/`.
2. Lanzar `GPromptStudio.exe` y verificar que abre.
3. Si falla por algún `hiddenimport` que falta, añadirlo al spec.
4. Probar `python build.py --installer` con Inno Setup instalado.

### C) Mejoras opcionales del comparador (no implementadas)
- Botón "comparar lado a lado con diff" entre 2 cards seleccionadas.
- Botón "abrir Preview Pollinations con cada modelo" (grid de bocetos).

### D) Mejoras UX globales pendientes
- **Tooltips visibles permanentes** para los iconos sin texto de la
  barra inferior (ahora se ven con hover gracias a CTkToolTip; el
  título de grupo ayuda pero no sustituye).
- **Párrafo del modelo** — convertirlo en tooltip o "ℹ️ más info"
  colapsable.

### E) Mejoras de fondo / arquitectura

#### E1) Tests y CI/CD  🔴 ALTA
- **D1 GitHub Actions CI** — sin CI hoy. Crear `.github/workflows/ci.yml`
  con pytest en Python 3.10/3.11/3.12 + Ruff lint. ~1 día.
- **T1 Cobertura tests** — 11+ módulos sin tests. Con los nuevos
  `json_prompt.py`, `multiprompt.py`, `adn_visual.py`, `workers_ia.py`,
  `sesion_video.py`, `modo_cliente.py` aislados, son más fáciles de
  testear. Empezar por `workers_ia.py` (interfaz limpia con mocks).
- **T2 Tests de integración** — sin tests de flujos UI→worker→API.

#### E2) Linting y formateo  🟡 MEDIA
- **D2 Ruff** — sin linter ni formateador. Añadir a `pyproject.toml`. ~1h.
- **D3 Type hints incrementales** — ~30-50% del código sin hints.
- **D4 Pre-commit hooks** — Ruff + secrets detection + tests básicos.

#### E3) Archivos grandes restantes  🟡 MEDIA
Estado tras las 6 particiones de sesiones 4-5:

| Archivo | Líneas | Notas |
|---|---:|---|
| `modules/core.py` | 2861 | Próximo candidato: `_inyectar_specs_*` (~180 líneas) → `prompts_inyeccion.py`. |
| `modules/tools_creative.py` | 1830 | Reducido un 57% (4211→1830). |
| `modules/tools_workflow.py` | 1726 | Posible: A/B testing + comparar modelos (~552 líneas) → `ab_testing.py`. |
| `app.py` | 2225 | Clase principal, difícil particionar. |
| `modules/ui_builders.py` | 2068 | Constructores UI, naturalmente largo. |
| `modules/dialogs.py` | 1907 | Mezcla editor + diálogos. Posible: editor utils → `editor.py`. |

#### E4) Arquitectura  🟡 MEDIA (refactor mayor, riesgo alto)
- **A1 Migrar Mixins → Composición pura** — `ArquitectoApp` hereda
  ahora **14 mixins** (era 13 en sesión 4). Más urgente cada sesión.
  ~5-10 días.
- **A2 Unificar `self.cmd_x()` vs `self.creative.cmd_x()`**.
- **A5 GPromptWindow expandida** con patrones comunes (auto-centrado,
  bind Escape global, confirmación al cerrar).

#### E5) Seguridad  🟢 BAJA (ya implementado)
- ✅ ~~**S1 keys.json texto plano**~~ — el cifrado AES-256-CBC ya
  estaba implementado en sesiones previas. La UX se mejoró en sesión 5
  con indicador de origen + botón borrar individual.
- **S2 Validación inputs** — sin sanitización de prompts antes de
  enviar a APIs externas.

#### E6) Rendimiento  🟢 BAJA
- ✅ ~~**Lag cambio de modo**~~ — arreglado en sesión 4.
- **R1 Carga lazy JSON** — `data/*.json` se cargan en import.
- **R2 Límite workers simultáneos** — sin semáforo.
- **R3 Virtual scrolling** — historial/favoritos cargan TODOS.

#### E7) UI/UX polish  🟢 BAJA
- **U4 Monkey-patch CTkToolTip** — `main.py` tiene ~20 líneas de
  monkey-patch. Crear envoltorio (`GPromptToolTip`).
- **U5 i18n** — toda la UI en español.

#### E8) Features nuevas  🟢 BAJA
- ✅ ~~**F3 Undo/Redo en `txt_salida`**~~ — hecho en sesión 4.
- ✅ ~~**JSON estructurado**~~ — hecho en sesión 5.
- ✅ ~~**Empaquetado .exe**~~ — sistema implementado en sesión 5.
- **F4 Exportar a Markdown/PDF** — Markdown a través de JSON pretty
  ya existe; PDF aún no.
- **F5 Diff visual entre versiones** — ya existe `_cmd_diff_versiones`,
  podría hacerse más visible.
- **F1 Plugin system** — ambicioso.
- **F2 API REST** — ambicioso.

---

## 🪶 Patrones nuevos establecidos en sesión 5

### Patrón "reparación progresiva de input"
Cuando el usuario pega contenido externo que puede tener artefactos
(JSON copiado de webs, CSV mal formado, etc.), implementar un helper
que pruebe N estrategias en orden de menor a mayor agresividad:

```python
def _intentar_reparar(texto):
    estrategias = []
    try:
        return parse(texto), estrategias
    except SpecificError:
        pass
    try:
        limpio = limpieza_basica(texto)
        return parse(limpio), ["limpieza_basica"]
    except SpecificError:
        pass
    # … más estrategias …
    return None, "error final"
```

Modal de resultado muestra qué estrategias se aplicaron en ámbar
para que el usuario sepa que el contenido se transformó.

Aplicado en `_intentar_reparar_json` (newlines + trailing commas).
Replicar para CSV import, prompt parsing del LLM cuando devuelve
formatos imperfectos, etc.

### Patrón "indicador de origen sin exponer valor"
Para datos sensibles (API keys, tokens), mostrar en la UI **dónde**
están guardados sin revelar el valor:

```python
def ubicacion_X(id):
    if existe_en(keyring): return "keyring"
    if existe_en(file): return "file (cifrado)"
    if existe_en(env): return "env (.env)"
    return ""
```

La UI muestra un icono + texto con la fuente, no el valor. El usuario
sabe a dónde acudir para modificar/borrar sin que la key se filtre
nunca a memoria visible.

### Patrón "exportador con limpieza de markdown del LLM"
Cuando se pide al LLM que produzca JSON/código, suele añadir
```` ```json ```` o ```` ```python ```` que rompe el parseo:

```python
resp = llm.generar(peticion)
if resp.startswith("```"):
    lineas = resp.splitlines()
    if lineas[0].startswith("```"): lineas = lineas[1:]
    if lineas and lineas[-1].startswith("```"): lineas = lineas[:-1]
    resp = "\n".join(lineas).strip()
```

Aplicado en `_cmd_exportar_json_prompt`. Replicable para cualquier
extracción de "el LLM debe devolver SOLO X" donde X tenga sintaxis
estricta.

### Patrón "build distribuible con docs"
Cada release necesita:
- `*.spec` con `hiddenimports` exhaustivos (mixins + libs nativas).
- `build.py` con `--clean`, `--onefile`, `--installer`.
- `installer.iss` con `AppId` UUID estable para upgrades.
- `BUILD.md` con TL;DR + troubleshooting.
- `.gitignore` con `dist/` y `build/`.

---

## 🔁 Cómo continuar (sesión nueva)

1. **Confirmar baseline**:
   ```powershell
   python -c "import app; print('OK')"
   python -m pytest tests/ -q
   ```
   Debe dar `OK` y `48 passed`.

2. **Verificar mixins enchufados** (sanity check rápido):
   ```powershell
   python -c "import app; print(len([m for m in app.ArquitectoApp.__mro__ if 'Mixin' in m.__name__]))"
   ```
   Debe imprimir `14`.

3. **Verificar build system** (sin ejecutar build):
   ```powershell
   python build.py --help
   ```
   Debe mostrar argparse OK.

4. **Decidir entre**:
   - **Lanzar build real** (`python build.py`) y verificar `.exe`.
   - **D1 GitHub Actions CI** (~1 día) — alta prioridad.
   - **D2 Ruff + pre-commit** (~1h) — quick win.
   - **A1 Migrar Mixins → Composición** (~5-10 días) — refactor mayor.
   - **Auditar `core.py`** (2861 líneas) y particionar
     `_inyectar_specs_*` a `prompts_inyeccion.py`.
   - **T1 Cobertura tests** empezando por `workers_ia.py` o
     `json_prompt.py` (interfaces limpias tras particiones).
   - **SeaArt char limits** — necesita info del usuario.

5. **Patrón de trabajo establecido**:
   - Análisis honesto en tabla antes de tocar (bugs / UX / cosmético).
   - Priorización 🔴 ALTA / 🟡 MEDIA / 🟢 BAJA.
   - Preguntar antes de empezar bloques grandes.
   - 1 commit por bloque coherente (a veces 2-3 si son cambios
     independientes en la misma área).
   - Smoke test (`python -c "import app; print('OK')"`) tras cada Edit.
   - Lanzar app en background con `python main.py` cuando el usuario
     lo pida (probar manualmente las mejoras).
   - Si algo falla en la prueba, fix inmediato + commit + relanzar app.

---

## ⚙️ Atajos útiles para retomar

```powershell
# Ver árbol de commits de la sesión 5
git log --oneline 808eb0a..HEAD

# Ver árbol de commits desde el HANDOFF original (sesión 3)
git log --oneline 5d4a662..HEAD

# Ver cambios de un commit
git show <hash>

# Tests
python -m pytest tests/ -v

# Arrancar app (modo background para probar)
python main.py

# Verificar dónde se resuelve un método
python -c "import app, inspect, os; print(os.path.basename(inspect.getsourcefile(app.ArquitectoApp._cmd_importar_json_prompt)))"

# Construir el .exe
python build.py             # dist/GPromptStudio/GPromptStudio.exe
python build.py --installer # dist/installer/GPromptStudio-Setup-1.0.0.exe
```

---

## 📦 Mixins en `ArquitectoApp` (14 en total tras sesión 5)

Orden en `class ArquitectoApp(ctk.CTk, ...)`:

1. `UIBuildersMixin` — header, barras, paneles principales.
2. `ToolsCreativeMixin` — sorpréndeme, pulse, sugerir, anclaje, etc.
3. `ToolsWorkflowMixin` — setups, macros, A/B testing, comparar modelos.
4. `ToolsAnalysisMixin` — scoring, atajos tags.
5. `DataMgmtMixin` — historial, favoritos, estrellas, LoRAs.
6. `BackupExportMixin` — backup completo, CSV, restore.
7. `DialogsMixin` — modales (configurar keys, etc.).
8. `CoreMixin` — comandos principales, event handlers, setup.
9. `AdnVisualMixin` (sesión 4) — ADN Visual + biblioteca.
10. `MultiPromptMixin` (sesión 4) — Mood/Story/Board/Walk.
11. `SesionVideoMixin` (sesión 4) — grabación + tutorial.
12. `WorkersIaMixin` (sesión 4) — workers de threading IA.
13. `ModoClienteMixin` (sesión 4) — brief profesional + 5 propuestas.
14. `JsonPromptMixin` (sesión 5) — import/export JSON Veo/Sora/Kling.

---

*Generado al final de sesión 5 — 5 commits añadidos, 48/48 tests,
working tree limpio. 70 commits ahead de origin/main acumulados desde
las 5 sesiones. No se ha hecho push. Bloques de profundidad **6/6** ✅.
6 particiones reducen `tools_creative.py` un 57% (4211 → 1830 líneas).
Sistema de empaquetado `.exe` listo (sin ejecutar build real todavía).*
