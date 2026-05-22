# 🧾 Handoff — G-Prompt Studio

Documento de continuación para retomar el proyecto en una sesión nueva.
Generado al final de la **sesión 3** (continuación de las sesiones 1 y 2).
Working tree limpio cuando se generó.

---

## 📍 Estado del proyecto

**G-Prompt Studio** — app de escritorio (Python + customtkinter) para
generar prompts de IA generativa (imagen, vídeo, audio) con 14 LLMs
como motores.

| Métrica | Valor |
|---|---|
| Tests | **48/48** ✅ |
| Working tree | Limpio |
| Branch | `main` |
| Commits ahead de `origin/main` | **50** (sin push) |
| Total commits sesión 3 | 5 |

Estructura: ver `ESTRUCTURA.md`.

---

## ✅ Qué se hizo en sesión 3 (continuación)

### 1. Workflow — 4 detalles UX (commit `39232a7`)
Cierra los 6 detalles que quedaban del menú Workflow:
- 🆚 **A/B Testing**: comentario chino eliminado + checkboxes ahora se
  deshabilitan visualmente al llegar a N=2 (dict `dim_checks` con refs).
- 🎙 **Grabar sesión**: dead code en `_iniciar_grabacion` (rama `else`
  duplicada del toggle) + var `tipo_grabacion` no usada → eliminados.
- 🔎 **Búsqueda global**: debounce 250ms (antes scan en 8 colecciones
  por tecla) + 8 checkboxes de filtro por tipo (Historial, Favoritos,
  Estrellas, Seeds, Snippets, Fórmulas, Personajes, LoRAs).
- 👥 **Grupo personajes**: fake placeholder con `<FocusIn>` /
  `<FocusOut>` (CTkTextbox no tiene placeholder nativo). El texto
  ejemplo ya no se cuela en la idea generada.
- 🔄 **Macros**: editor inline (botón ✏️ Editar carga la macro al
  form, el botón principal cambia a "💾 Guardar cambios") + reordenar
  pasos con ↑ ↓ ✕ por paso. Estado `edit_state["idx"]` distingue
  modo crear vs editar. Botón "❌ Cancelar edición" visible solo
  en modo edición.

### 2. HANDOFF fusionado con HANDOFF2 (commit `e7c1b2a`)
El usuario tenía un segundo doc (`gprompt-studio 11.1/HANDOFF2.md`)
con análisis arquitectónico de toda la codebase. Estaba desfasado
pero tenía propuestas útiles. Filtrado lo redundante y añadida una
**sección F** con 8 sub-bloques de mejoras de fondo (ver "Pendiente"
abajo).

### 3. Bloque 3 — Slider N en 6 multi-prompts (commits `866f201`, `9262dae`)
Las 6 funciones multi-prompt ahora son configurables, no hardcoded.

Helper compartido **`_pedir_n_modal(titulo, descripcion, n_min, n_max,
default, key_pref=None)`** en `core.py`:
- Modal pequeño 440x240 con slider + label live "N = X" + ▶ Generar /
  Cancelar.
- `key_pref` opcional → recuerda última N en preferencias.
- `wait_window()` → devuelve int o None sincrónicamente.
- Enter en el modal dispara generar.

Tabla de las 6 funciones:

| Función | Rango N | Default | `key_pref` |
|---|---|---|---|
| 🔀 Variaciones (`cmd_variaciones`) | 2–6 | 3 | `variaciones_n` |
| 🔂 Iterar (`_cmd_iteracion`) | 3–10 | 5 | `iteracion_n` |
| 🎭 Mood (`_cmd_moodboard`) | 4–10 | 6 | `moodboard_n` |
| 🎞 Story (`_cmd_story_sequence`) | 2–6 | 3 | `story_n` |
| 📽 Board (`_cmd_storyboard_video`) | 3–8 | 4 | `board_n` |
| 🌀 Walk (`_cmd_random_walk`) | 3–10 | 5 | `walk_n` |

`max_tokens` escala con N (`min(8000, 1500 + n * 600)` o similar)
para que el LLM tenga margen suficiente con N grande.

**Pulse del Bloque 1 sigue con su propio sistema 3/5/custom** — no
necesita slider porque tiene un control más rico.

### 4. Fix Bloque 3 — parsers + Variaciones cierra (commit `0adf770`)
Bugs reportados al probar Bloque 3:

- **Variaciones N=6 → recibía 7 cards**. Causa: parser
  `_parsear_variaciones` capturaba el preámbulo del LLM como bloque #1.
- **Mood/Story card #1 salía como "MOODBOARD: 10 PROMPTS..."**. Causa:
  `_parsear_bloques_numerados` capturaba el título descriptivo del LLM.
- **Variaciones "Aplicar" cerraba la ventana**. El modal de Variaciones
  se quedó con `vent.destroy()` antiguo mientras otros comparadores
  ya eran persistentes desde commit `5451292`.
- **Walk N=10 → 11 cards** (original + 10 derivaciones). No es un bug,
  pero el texto del slider no lo aclaraba.

Solución:
- **`_parsear_bloques_numerados(texto, n_esperado=None)`** y
  **`_parsear_variaciones(texto, n_esperado=None)`** — si reciben más
  bloques de los pedidos, prefieren los que contienen
  "POSITIVE PROMPT:" / "POSITIVE:". Si no hay suficientes con marker,
  descartan los primeros (heurística: el preámbulo del LLM va al inicio).
- **`_worker_ia`** acepta `n_variaciones` opcional, propagado a
  `_parsear_variaciones`. `cmd_variaciones` lo pasa.
- **`_mostrar_variaciones._aplicar()`** ya no llama a `vent.destroy()`.
  La card aplicada gana borde dorado `#fbbf24`, las demás vuelven a
  su color de acento. Refs en `cards_refs = [(card, accent), ...]`.
- **Textos de Variaciones dinámicos**: "🔀 {n} variaciones generadas",
  "Compara las {n} versiones..." (antes hardcoded a 3).
- **Walk texto del slider** aclarado: "¿Cuántas derivaciones nuevas?
  El comparador mostrará el original + N derivaciones (N+1 tarjetas)".

### 5. HANDOFF actualizado (este commit)
Sustitución completa del HANDOFF.md con resumen depurado.

---

## 📜 Commits de sesión 3 (5 en total)

```
0adf770 fix(bloque3): parsers respetan N + Variaciones no cierra + textos dinámicos
9262dae feat(profundidad): Bloque 3 (2/2) — Slider N en Mood/Story/Board/Walk
866f201 feat(profundidad): Bloque 3 (1/2) — Slider N en Variaciones + Iterar
e7c1b2a docs: HANDOFF.md fusionado con HANDOFF2 — sección F arquitectura/CI/tests
39232a7 feat(workflow): 4 detalles UX restantes — A/B · Búsqueda · Grupo · Macros
```

---

## ✅ Trabajo total acumulado (sesiones 1+2+3)

### Menús revisados completos
- 📊 **Análisis** (sesión 1)
- 💾 **Backup** (sesión 1)
- 📁 **Datos** (sesión 1)
- 🛠 **Herramientas** (sesión 1) + 3 detalles menores (sesión 2)
- 📝 **Plantillas** (sesión 1) + 4 detalles menores (sesión 2)
- 🎨 **UI** completo (sesión 2)
- ⚙️ **Workflow** completo (sesión 2: 2 bugs · sesión 3: 4 detalles UX)
- 🎬 **Barra de acciones** — refactor visual con colores semánticos (sesión 2)

### Bloques de profundidad (mejoras a funciones existentes)
- ✅ **Bloque 1** — Ideas clicables, Pulse 3/5/custom, Preview caché (sesión 2)
- ✅ **Bloque 2** — Sugerir top 3, Compar con ganador (sesión 2)
- ✅ **Bloque 3** — Slider N en 6 multi-prompts (sesión 3)
- ⏳ **Bloque 4** — Refinar con diff + undo (pendiente)
- ⏳ **Bloque 5** — Walk árbol visual (pendiente)
- ⏳ **Bloque 6** — Story/Board tipos configurables (parcialmente cumplido en Bloque 3)

### Fixes mayores
- Variaciones convertido de panel inline a modal con cards (sesión 2)
- Comparadores persistentes con highlight dorado (sesión 2-3)
- Compar con N>3 (IndexError + layout) (sesión 2)
- Sugerir/Compar — prompt estricto + extractor (sesión 2)
- Parsers respetan N esperado (sesión 3)

---

## 🚧 Pendiente para la próxima sesión

### A) Bloques de profundidad sin terminar (3 de 6)

#### Bloque 4 — Refinar con diff + undo (~2h)
- `cmd_refinar` (`modules/core.py`) sobrescribe el prompt sin avisar
  qué cambió.
- Antes de aplicar, mostrar un **diff visual** verde/rojo (ya existe
  `_cmd_diff_versiones` en `app.py` para inspiración).
- Botón "↩️ Deshacer refinamiento" usando `_versiones_prompt`.
- Permitir cancelar antes de aplicar.

#### Bloque 5 — Walk árbol visual (~3h)
- `_cmd_random_walk` (`modules/tools_creative.py`) actualmente lineal.
- Convertir a **árbol con ramas**: el usuario puede en cualquier paso
  ramificar en 3 direcciones distintas.
- Visualización tipo grafo simple (CTkCanvas o frames anidados).
- Guardar la ruta como "evolución X→Y→Z".

#### Bloque 6 — Story/Board configurables (~3h restante)
- Bloque 3 ya añadió slider N a Story y Board.
- Pendiente: permitir **elegir tipos de shot** explícitos en Story
  (POV/OTS/Aerial/Dutch/etc.) en lugar de dejar al LLM.
- Pendiente: **encadenar Board con →Vídeo** automáticamente (generar
  prompt de vídeo que use esos N frames como keyframes).

### B) Botones de barra principal (no auditados a fondo)
- 🧬 **ADN Visual** (`_cmd_adn_visual` en `tools_creative.py`) — usado
  en otros sitios, recibió fixes indirectos en sesiones 1-2.
- 🔍 **Análisis Inverso** (`_cmd_analisis_inverso` en
  `tools_creative.py`) — sin auditoría a fondo.

### C) Mejoras opcionales del comparador (no implementadas)
- Botón "comparar lado a lado con diff" entre 2 cards seleccionadas.
- Botón "abrir Preview Pollinations con cada modelo" (grid de bocetos).

### D) Mejoras de UX globales pendientes
- **Reorganizar barra de acciones en 3 secciones explícitas** con
  títulos visibles: Generación / Análisis / Composición. Hoy hay
  separadores pero la jerarquía visual podría ser más fuerte.
- **Tooltips visibles permanentes** para los 14 botones-icono de la
  barra inferior (POS/NEG/Todo/Comfy/Trad/etc.).
- **Párrafo del modelo** (la descripción larga debajo del combo
  Modelo) — convertirlo en tooltip o "ℹ️ más info" colapsable.

### E) Mejoras de fondo / arquitectura (HANDOFF2 fusionado)

#### E1) Tests y CI/CD  🔴 ALTA
- **D1 GitHub Actions CI** — sin CI hoy. Crear `.github/workflows/ci.yml`
  con pytest en Python 3.10/3.11/3.12 + Ruff lint. ~1 día.
- **T1 Cobertura tests** — 11 de 15 módulos sin un solo test. Empezar
  por `core.py` (los workers IA, generación, atajos). ~3-5 días.
- **T2 Tests de integración** — sin tests de flujos UI→worker→API.
  Añadir con mocks. ~2-3 días.

#### E2) Linting y formateo  🟡 MEDIA
- **D2 Ruff** — sin linter ni formateador. Añadir a `pyproject.toml`.
- **D3 Type hints incrementales** — ~30-50% del código sin hints.
- **D4 Pre-commit hooks** — Ruff + secrets detection + tests básicos.

#### E3) Archivos demasiado grandes  🟡 MEDIA
8 archivos exceden 1000 líneas. Empezar por `core.py` (2799) y
`tools_creative.py` (2442+). Validar con smoke tests entre cada
partición.

| Archivo | Líneas aprox |
|---|---|
| `modules/core.py` | 2,800+ |
| `modules/tools_creative.py` | 2,500+ |
| `modules/tools_workflow.py` | 2,000+ |
| `modules/ui_builders.py` | 1,900+ |
| `modules/dialogs.py` | 1,900+ |
| `app.py` | 1,700+ |
| `modules/data_mgmt.py` | 1,400+ |
| `modules/tools_analysis.py` | 1,300+ |

#### E4) Arquitectura  🟡 MEDIA (refactor mayor, riesgo alto)
- **A1 Migrar Mixins → Composición pura** — `ArquitectoApp` hereda
  8 mixins. Ya hay `components.py` con proxies. ~5-10 días.
- **A2 Unificar `self.cmd_x()` vs `self.creative.cmd_x()`**.
- **A5 GPromptWindow expandida** con patrones comunes (auto-centrado,
  bind Escape global, confirmación al cerrar).

#### E5) Seguridad  🟡 MEDIA
- **S1 keys.json texto plano** — el fallback sin OS Keyring guarda
  las API keys en texto plano. Considerar encriptación básica o
  exigir Keyring.
- **S2 Validación inputs** — sin sanitización de prompts antes de
  enviar a APIs externas.

#### E6) Rendimiento  🟢 BAJA
- **R1 Carga lazy JSON** — `data/*.json` se cargan en import.
- **R2 Límite workers simultáneos** — sin semáforo, threads se
  acumulan.
- **R3 Virtual scrolling** — historial/favoritos/estrellas cargan
  TODOS los elementos. Con 500+ degrada.

#### E7) UI/UX polish  🟢 BAJA
- **U4 Monkey-patch CTkToolTip** — `main.py` tiene ~20 líneas de
  monkey-patch. Crear envoltorio (`GPromptToolTip`).
- **U5 i18n** — toda la UI en español.

#### E8) Features nuevas  🟢 BAJA
- **F3 Undo/Redo en `txt_salida`** — sin Ctrl+Z hoy. Tk Text widget
  tiene `undo=True` nativo. **Fácil win, ~30 min**.
- **F4 Exportar a JSON/Markdown/PDF** — solo CSV hoy.
- **F5 Diff visual entre versiones** — ya existe `_cmd_diff_versiones`,
  podría hacerse más visible.
- **F1 Plugin system** — ambicioso.
- **F2 API REST** — ambicioso.

---

## 🪶 Patrones establecidos en esta serie de sesiones

Para mantener coherencia, la próxima sesión debería respetarlos:

### Patrón "modal de configuración"
Hecho en Pulse (Bloque 1) y replicado en las 6 funciones del Bloque 3.
```python
def _cmd_X(self):
    ...
    n = self._pedir_n_modal(titulo, descripcion, n_min, n_max,
                             default, key_pref="X_n")
    if n is None:
        return
    # ... usar n
```
`_pedir_n_modal` está en `modules/core.py`.

### Patrón "comparador persistente"
Aplicado en `_abrir_comparador` (app.py), `_abrir_ventana_comparacion`
(tools_workflow.py) y `_mostrar_variaciones` (core.py). Al pulsar
"Usar" / "Aplicar":
1. NO destruir la ventana.
2. Marcar la card aplicada con borde dorado `#fbbf24`, width=3.
3. Desmarcar las demás (volver a su color de acento).
4. Botón explícito "Cerrar comparador" en el pie de la ventana.

### Patrón "petición al LLM para N prompts en paralelo"
1. Petición ESTRICTA con estructura exacta:
   `DEVUELVE EXACTAMENTE N LÍNEAS: POSITIVE PROMPT: ... / NEGATIVE PROMPT: ...`
   "NO menciones otros modelos · NO añadas explicaciones · NO repitas
   la sección POSITIVE/NEGATIVE".
2. Defensa regex client-side tras la respuesta:
   ```python
   m_pos = re.search(r'(?:POSITIVE\s+)?PROMPT\s*:\s*(.+?)(?=\n\s*NEGATIVE\s+PROMPT\s*:|\n\s*POSITIVE\s+PROMPT\s*:|\n\s*###|\n\s*\*\*\*|\Z)',
                     resp, re.DOTALL|re.IGNORECASE)
   ```
3. Detección de duplicados: si las N respuestas son idénticas, avisar.

### Patrón "parsers con n_esperado"
`_parsear_bloques_numerados(texto, n_esperado=None)` y
`_parsear_variaciones(texto, n_esperado=None)` — si el parser recibe
más bloques de los pedidos:
1. Preferir los que contienen "POSITIVE PROMPT:" / "POSITIVE:".
2. Si no hay suficientes con marker, descartar los primeros
   (heurística: el preámbulo del LLM va al inicio).

### Patrón "confirmación antes de borrar"
ADN, Seeds, Snippets, Fórmulas, Plantillas, Macros — TODOS tienen
`messagebox.askyesno()` antes del pop(). Cuando añadas nuevas
colecciones, NO olvidar el askyesno.

### Patrón "fake placeholder en CTkTextbox"
CTkTextbox no soporta `placeholder_text` nativo. Hecho en
"Grupo personajes" (sesión 3):
```python
_state = {"placeholder_visible": True}
def _mostrar_placeholder():
    txt.delete("1.0", "end")
    txt.insert("1.0", PLACEHOLDER)
    txt.configure(text_color="#6b7280")
    _state["placeholder_visible"] = True

def _on_focus_in(_e=None):
    if _state["placeholder_visible"]:
        txt.delete("1.0", "end")
        txt.configure(text_color=COLOR_NORMAL)
        _state["placeholder_visible"] = False
# ... bind FocusIn / FocusOut
# Al recopilar: relacion = "" if _state["placeholder_visible"] else txt.get(...)
```

### Patrón "debounce en búsqueda"
Aplicado en Atajos teclado (sesión 2), Biblioteca (sesión 2),
Búsqueda global (sesión 3). 200-250ms:
```python
_pendiente = {"after_id": None}
def _disparar(_e=None):
    if _pendiente["after_id"]:
        try: vent.after_cancel(_pendiente["after_id"])
        except Exception as _e2: logger.debug(...)
    _pendiente["after_id"] = vent.after(250, buscar)
entry.bind("<KeyRelease>", _disparar)
```

### Helper nuevo a usar
`_intentar_cambiar_modelo(nombre)` en `app.py` — busca el modelo en
la lista del modo actual y aplica al combo. Devuelve nombre aplicado
o None.

---

## 🔁 Cómo continuar (sesión nueva)

1. **Confirmar baseline**:
   ```powershell
   python -c "import app; print('OK')"
   python -m pytest tests/ -q
   ```
   Debe dar `OK` y `48 passed`.

2. **Decidir entre**:
   - **Bloque 4** (Refinar diff+undo) — más visible al usuario, ~2h.
   - **Bloque 5** (Walk árbol) — más ambicioso, ~3h.
   - **Bloque 6 final** (Story/Board tipos + encadenar →Vídeo) — ~3h.
   - **Botones de barra** ADN Visual / Análisis Inverso (B).
   - **Quick wins del HANDOFF2**: F3 Undo/Redo en `txt_salida` (~30 min,
     `txt_salida.configure(undo=True)` nativo de Tk).
   - **D1 GitHub Actions CI** (~1 día).

3. **Patrón de trabajo establecido**:
   - Análisis honesto en tabla antes de tocar (bugs / UX / cosmético).
   - Priorización 🔴 ALTA / 🟡 MEDIA / 🟢 BAJA.
   - Preguntar antes de empezar bloques grandes.
   - 1 commit por bloque coherente.
   - Smoke test (`python -c "import app; print('OK')"`) tras cada Edit.
   - Lanzar app en background con `python main.py` cuando el usuario
     lo pida (probar manualmente las mejoras).
   - Si algo falla en la prueba, fix inmediato + commit + relanzar app.

---

## ⚙️ Atajos útiles para retomar

```powershell
# Ver árbol de commits de la sesión 3
git log --oneline 5e67c8f..HEAD

# Ver árbol de commits desde el HANDOFF original
git log --oneline 5d4a662..HEAD

# Ver cambios de un commit
git show <hash>

# Tests
python -m pytest tests/ -v

# Arrancar app (modo background para probar)
python main.py
```

---

*Generado al final de sesión 3 — 5 commits añadidos, 48/48 tests,
working tree limpio. 50 commits ahead de origin/main acumulados desde
las 3 sesiones. No se ha hecho push.*
