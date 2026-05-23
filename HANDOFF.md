# 🧾 Handoff — G-Prompt Studio

Documento de continuación para retomar el proyecto en una sesión nueva.
Generado al final de la **sesión 4** (continuación de las sesiones 1-3).
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
| Commits ahead de `origin/main` | **63** (sin push) |
| Total commits sesión 4 | 13 |
| Bloques de profundidad | **6/6 ✅** |

Estructura: ver `ESTRUCTURA.md`.

---

## ✅ Qué se hizo en sesión 4

### Bloques de profundidad finales — 4, 5 y 6 cerrados

#### 1. Bloque 4 — Refinar con diff + undo (commits `3fe9921`, `ca38268`)
`cmd_refinar` ya no sobreescribe el prompt directamente: ahora muestra
un **modal de diff** verde/rojo (original a la izquierda, refinado a la
derecha) con 3 botones:
- ✅ **Aplicar** → apila original como `v{N} (pre-refinamiento)` en
  `_versiones_prompt` y aplica el nuevo.
- ↩️ **Deshacer refinamiento previo** → solo visible si hay otra
  versión `(pre-refinamiento)` en el stack. Restaura esa versión.
- ❌ **Cancelar** → descarta. Esc también cancela.

El click-derecho de Refinar (7 sub-opciones: cinematográfico / facial /
iluminación / impacto / simplificar / paleta / detalle técnico) también
pasa por el mismo modal — antes tenía su propio worker que sobreescribía.

Bug pre-existente arreglado en `_abrir_ventana_diff`: la columna
izquierda nunca creaba su `CTkTextbox`, así que `txt_a._textbox.tag_configure(...)`
lanzaba `NameError`. Como ahora `cmd_refinar` reusa esa función, se
arregló de paso.

#### 2. Bloque 5 — Walk árbol visual (commits `63c08da`, `f76fb45`, `d65f876`, `a11e388`)
Reemplaza el Walk lineal (N derivaciones secuenciales) por un árbol
interactivo donde el usuario decide cuándo y dónde ramificar.

UI nueva en `_abrir_walk_arbol`:
- Ventana 1240x740 con dos paneles.
- Izquierda: `tk.Canvas` con scroll H/V mostrando el árbol horizontal.
  Raíz azul a la izquierda, hijos morados a la derecha, nodo
  seleccionado dorado con borde grueso. Líneas L padre→hijo.
- Derecha: panel detalle con etiqueta, ruta raíz→…→nodo, textbox de
  preview y 5 botones:
  - 🌿 **Ramificar (3 hijos)** — el LLM genera 3 derivaciones distintas
    del nodo seleccionado. Max profundidad 6.
  - 📋 **Usar este** — aplica el prompt del nodo a `txt_salida`
    (la ventana sigue abierta para seguir explorando).
  - 💾 **Guardar ruta** — abre modal con preview Markdown de la ruta
    completa + 2 acciones: copiar al portapapeles o **guardar en
    `📑 Versiones prompt`** (cada nodo se apila como versión con
    etiqueta `Walk Raíz → D2 → D2.1 · nodo D2.1`).
  - 🗑 **Borrar subárbol** — con askyesno, borra nodo + descendientes.
  - ✖ Cerrar (Esc también).

Estructura de datos: `nodos = [{id, parent, texto, depth, hijos[], label}]`.
Layout: `depth → X`; hojas reciben Y por orden DFS, internos = media
de Y de hijos. Recalculado en cada redibujado.

Etiquetas legibles: D1/D2/D3 en profundidad 1, D1.1/D1.2/D1.3 en
profundidad 2, etc.

Fix paralelo al ver versiones: el UI de `📑 Versiones prompt` mostraba
todas las entradas con el mismo formato "Versión #N · timestamp",
ignorando el campo `etiqueta`. Ahora el header de cada card detecta el
origen y lo muestra: **🌀 Walk Raíz → D2 · nodo D2.1** (azul) y
**🔁 pre-refinamiento** (ámbar).

#### 3. Bloque 6 — Story tipos + Board→Vídeo (commit `e2b954f`)

**Parte A — Story tipos explícitos** (`_pedir_story_config`):
Antes solo pedía N (slider 2-6) y dejaba al LLM elegir los tipos. Ahora
modal nuevo con:
- Slider N (2-6).
- Toggle "🤖 Que el LLM elija los tipos automáticamente" (default ON).
- Si se desmarca: 8 checkboxes con tipos canónicos (Wide / Medium /
  Close-Up / POV / OTS / Top-Down / Dutch / Aerial). Validación: el
  número de marcados debe coincidir con N.
- Persistencia: N + tipos + modo auto se guardan en preferencias
  (`story_n`, `story_tipos`, `story_auto`).

En modo manual, el prompt al LLM cambia de "elige N diversos" a
"usa EXACTAMENTE estos N tipos en este orden" y el comparador
etiqueta cada columna con el tipo (`#1 Wide`, `#2 POV`, etc.).

Constante `STORY_SHOT_TYPES` con los 8 tipos como tuples `(key, label, desc)`.

**Parte B — Board → Vídeo encadenado**:
`_abrir_comparador` acepta nuevo kwarg `extra_botones`: lista de
`(label, fg_color, callback)`. Cada uno se renderiza al pie de la
ventana. Permite extender el comparador sin tocar su núcleo.

`_cmd_storyboard_video` pasa ahora un extra-botón **"🎬 Encadenar como
prompt de vídeo"** (morado). Al pulsarlo:
1. Construye un bloque con los N frames numerados.
2. Pide al LLM un ÚNICO prompt de vídeo cinematográfico que recorra
   los frames como **keyframes**, con movimientos de cámara y
   transiciones explícitas ("opens with [frame 1] → dolly in →
   [frame 2] → …").
3. Cambia modo a "video" (dispara `_on_modo_cambio`).
4. Aplica el resultado a `txt_salida` y guarda en historial.
5. Cierra el comparador.

### Mejoras UX globales (commit `b8021fc`)

**F3 — Undo/Redo nativo en `txt_salida`**:
`CTkTextbox` envuelve un `tk.Text` interno (`_textbox`) que sí soporta
undo nativo. Activamos `undo=True, autoseparators=True, maxundo=-1` y
binds explícitos:
- Ctrl+Z / Ctrl+Shift+Z → `edit_undo`
- Ctrl+Y → `edit_redo`
Cada binding devuelve `"break"` para evitar doble procesamiento.

`actualizar_salida()` ahora emite `edit_separator()` antes y después
de delete+insert, así una escritura programática (refinar, generar,
walk) cuenta como un solo paso de undo distinto de los toques manuales.

**Barra de acciones con títulos de grupo**:
Los 9 grupos de la barra superior ya no se separan solo con líneas
verticales — cada uno lleva un mini-label en su color:

Fila 1: **💡 INSPIRACIÓN · ✨ GENERACIÓN · 🔍 ANÁLISIS · 🧬 ADN**
Fila 2: **🔁 EDICIÓN · 🔂 VARIANTES · 🎬 NARRATIVA · 🎬 CONVERSIÓN · 📦 UTILIDADES**

### Auditoría + 2 bugs ADN Visual (commit `f9cf527`)

Durante la auditoría se detectaron 2 bugs reales:

1. **Candado late-binding**: `_toggle_bloqueo` capturaba `btn_lock` por
   late binding del loop. Pulsar 🔒 en cualquier categoría solo cambiaba
   el icono del último botón creado. Fix: guardar btn_lock en
   `bloqueos[cat_key]["btn"]` y leerlo desde el dict.
2. **Copy-paste error en escena**: `_convertir_plataforma` en sección
   "Escena" usaba `ilu.get("tipo_exacto", "")` (variable de iluminación
   del bloque anterior). Cambiado a `esc.get("tipo_exacto", "")`.

### Refactor — 5 particiones de archivos grandes

Tras auditar archivos >2000 líneas, identifiqué clusters cohesivos y
los moví a módulos independientes. Cada partición verificada con
`import app` + 48/48 tests + `inspect.getsourcefile` confirmando que
los métodos se resuelven al nuevo módulo.

| Commit | Mueve | Líneas | A módulo |
|---|---|---:|---|
| `ba72993` | `_cmd_adn_visual` + `_cmd_ver_biblioteca_adn` | 645 | `modules/adn_visual.py` |
| `b37621f` | Mood/Story/Board/Walk + helpers + `STORY_SHOT_TYPES` | 920 | `modules/multiprompt.py` |
| `1d998b1` | Sesión vídeo (`_sesion_*`) | 526 | `modules/sesion_video.py` |
| `1d998b1` | Workers IA (`_worker_*`) | 240 | `modules/workers_ia.py` |
| `1d998b1` | Modo Cliente + Compañero Moodboard | 824 | `modules/modo_cliente.py` |
| **Total** | | **3155** | 5 módulos nuevos |

Resultado en archivos originales:
- `tools_creative.py`: **4211 → 1830** (−57%)
- `tools_workflow.py`: 2252 → 1726 (−23%)
- `core.py`: 3100 → 2861 (−8%)

Pequeña deduplicación en ADN al particionar: extraído helper
`_aplicar_partes_a_idea` para reusar entre `_usar_en_prompt` y
`_convertir_plataforma` (antes ~80 líneas duplicadas, ahora ~10
compartidas).

Wiring de mixins en `modules/__init__.py` y `app.py`:
- `AdnVisualMixin`, `MultiPromptMixin`, `SesionVideoMixin`,
  `WorkersIaMixin`, `ModoClienteMixin` añadidos al final de la cadena
  de bases de `ArquitectoApp`.

### Mejoras UX adicionales (commit `f8bc2aa`)

Detectadas al probar la app:

1. **Fix lag al cambiar modo Imagen/Vídeo/Audio**:
   `_construir_checkboxes` destruía y reconstruía hasta 257 widgets
   (ESTILOS_IMAGEN) en cada cambio. La optimización v1.1 ya cubría el
   caso "misma lista" pero como ESTILOS_IMAGEN ≠ VIDEO ≠ AUDIO,
   prácticamente nunca aplicaba.
   v1.2 cachea sub-frames anidados por lista (`id(lista)` como key).
   Primera entrada construye + cachea; siguientes hacen
   `pack_forget`/`pack` del cacheado. CERO destrucción/reconstrucción.
   `_filtrar_estilos` ahora itera recursivamente para encontrar los
   checkboxes dentro del sub-frame activo.

2. **Barra inferior con títulos de grupo**:
   Misma idea que la barra superior aplicada a los 13 botones inferiores:
   **📋 COPIAR · 🔧 HERRAMIENTAS · 🛡 NEGATIVE · ⭐ GUARDAR · 💾 EXPORT**

3. **Análisis Inverso — mejoras de auditoría**:
   - "Aplicar corregido" ya no sobreescribe directamente. Pasa por
     `_mostrar_diff_refinamiento` (Bloque 4) para que el usuario vea
     el diff antes de aplicar.
   - Nuevo botón **"📋 Solo corregido"** que copia ÚNICAMENTE el
     bloque `PROMPT CORREGIDO` en lugar de todo el análisis.
   - Renombrado "📋 Copiar análisis" para distinguir mejor.

---

## 📜 Commits de sesión 4 (13 en total)

```
f8bc2aa feat(ux): fix lag cambio modo + títulos barra inferior + Análisis Inverso
1d998b1 refactor: 3 particiones más — Sesión vídeo / Workers IA / Modo Cliente
b37621f refactor(multiprompt): particionar Mood/Story/Board/Walk a modules/multiprompt.py
ba72993 refactor(adn): particionar ADN Visual a modules/adn_visual.py
f9cf527 fix(adn): 2 bugs detectados en auditoría de ADN Visual
b8021fc feat(ux): Undo/Redo en txt_salida (F3) + títulos visibles en barra de acciones
e2b954f feat(bloque6): Story tipos configurables + Board encadenado a Vídeo
a11e388 fix(versiones): mostrar origen Walk / pre-refinamiento en el header
d65f876 feat(bloque5): Walk — Guardar ruta en Versiones prompt (recuperable)
f76fb45 fix(bloque5): Walk árbol — Usar este no cierra + Copiar ruta abre modal
63c08da feat(bloque5): Walk árbol visual — exploración no lineal con ramas
ca38268 feat(bloque4): click-derecho de Refinar también pasa por diff modal
3fe9921 feat(bloque4): Refinar con diff + undo — modal Aplicar/Cancelar/Deshacer
```

---

## ✅ Trabajo total acumulado (sesiones 1+2+3+4)

### Menús revisados completos
- 📊 **Análisis** (sesión 1)
- 💾 **Backup** (sesión 1)
- 📁 **Datos** (sesión 1)
- 🛠 **Herramientas** (sesión 1) + 3 detalles menores (sesión 2)
- 📝 **Plantillas** (sesión 1) + 4 detalles menores (sesión 2)
- 🎨 **UI** completo (sesión 2)
- ⚙️ **Workflow** completo (sesión 2: 2 bugs · sesión 3: 4 detalles UX)
- 🎬 **Barra de acciones** — refactor visual con colores semánticos
  (sesión 2) + títulos de grupo visibles (sesión 4)
- 🔻 **Barra inferior** — títulos de grupo visibles (sesión 4)

### Bloques de profundidad — 6/6 ✅
- ✅ **Bloque 1** — Ideas clicables, Pulse 3/5/custom, Preview caché (sesión 2)
- ✅ **Bloque 2** — Sugerir top 3, Compar con ganador (sesión 2)
- ✅ **Bloque 3** — Slider N en 6 multi-prompts (sesión 3)
- ✅ **Bloque 4** — Refinar con diff + undo (sesión 4)
- ✅ **Bloque 5** — Walk árbol visual + guardar ruta en Versiones (sesión 4)
- ✅ **Bloque 6** — Story tipos configurables + Board→Vídeo encadenado (sesión 4)

### Particiones de archivos grandes (sesión 4)
- `modules/adn_visual.py` (666 líneas)
- `modules/multiprompt.py` (969 líneas)
- `modules/sesion_video.py` (565 líneas)
- `modules/workers_ia.py` (281 líneas)
- `modules/modo_cliente.py` (869 líneas)

### Fixes mayores
- Variaciones convertido de panel inline a modal con cards (sesión 2)
- Comparadores persistentes con highlight dorado (sesión 2-3)
- Compar con N>3 (IndexError + layout) (sesión 2)
- Sugerir/Compar — prompt estricto + extractor (sesión 2)
- Parsers respetan N esperado (sesión 3)
- Diff visual con columna izquierda vacía (bug pre-existente, sesión 4)
- ADN Visual: candado late-binding + escena con `ilu.get` (sesión 4)
- Lag al cambiar modo: 257 widgets recreados → 0 (sesión 4)

---

## 🚧 Pendiente para la próxima sesión

### A) Botones de barra principal
- 🧬 **ADN Visual** — auditoría hecha en sesión 4, 2 bugs arreglados.
  Pendiente: refactor para reducir 416 líneas (función monolítica) y
  unificar `_usar_en_prompt` con `_convertir_plataforma` (en
  `modules/adn_visual.py` ya se hizo deduplicación parcial vía
  `_aplicar_partes_a_idea`).
- 🔍 **Análisis Inverso** — auditoría hecha + 2 mejoras aplicadas
  (diff + copiar solo corregido). Pendiente: botón "🔄 Volver a
  analizar" si el regex de PROMPT CORREGIDO no parsea.

### B) SeaArt + char limits (pendiente de info del usuario)
El usuario reportó que en webs como SeaArt el límite real de
caracteres es **menor** que el `max_chars` en `data/model_specs_imagen.json`.
Posibles causas:
- Las specs están desactualizadas (SeaArt redujo límites).
- Hay sub-límites por sección (POSITIVE solo, NEGATIVE solo) no
  reflejados.
- El usuario compara totales con secciones individuales.

Necesita: que el usuario reporte el modelo concreto + límite real
para corregir `model_specs_imagen.json` (o aplicar un margen defensivo
del 80%).

### C) Mejoras opcionales del comparador (no implementadas)
- Botón "comparar lado a lado con diff" entre 2 cards seleccionadas.
- Botón "abrir Preview Pollinations con cada modelo" (grid de bocetos).

### D) Mejoras de UX globales pendientes
- **Tooltips visibles permanentes** para los iconos sin texto de la
  barra inferior (ahora se ven con hover gracias a CTkToolTip; el
  título de grupo ayuda pero no sustituye).
- **Párrafo del modelo** — convertirlo en tooltip o "ℹ️ más info"
  colapsable.

### E) Mejoras de fondo / arquitectura

#### E1) Tests y CI/CD  🔴 ALTA
- **D1 GitHub Actions CI** — sin CI hoy. Crear `.github/workflows/ci.yml`
  con pytest en Python 3.10/3.11/3.12 + Ruff lint. ~1 día.
- **T1 Cobertura tests** — 11 de 15 módulos sin un solo test. Ahora con
  los nuevos `multiprompt.py`, `adn_visual.py`, `workers_ia.py`,
  `sesion_video.py`, `modo_cliente.py` aislados, son más fáciles de
  testear. Empezar por `workers_ia.py` (interfaz limpia). ~3-5 días.
- **T2 Tests de integración** — sin tests de flujos UI→worker→API.
  Añadir con mocks. ~2-3 días.

#### E2) Linting y formateo  🟡 MEDIA
- **D2 Ruff** — sin linter ni formateador. Añadir a `pyproject.toml`. ~1h.
- **D3 Type hints incrementales** — ~30-50% del código sin hints.
- **D4 Pre-commit hooks** — Ruff + secrets detection + tests básicos.

#### E3) Archivos grandes restantes  🟡 MEDIA
Estado actualizado tras las 5 particiones de sesión 4:

| Archivo | Líneas | Notas |
|---|---:|---|
| `modules/core.py` | 2861 | Próximo candidato: `_inyectar_specs_*` (~180 líneas, función de prompts) → `prompts_inyeccion.py`. |
| `app.py` | 2222 | Clase principal, difícil particionar. Posible: extraer `_abrir_comparador` y `_abrir_ventana_diff` a `widgets/`. |
| `modules/ui_builders.py` | 2043 | Naturalmente largo (constructores UI). Posible: extraer `_build_acciones` a `ui_acciones.py`. |
| `modules/dialogs.py` | 1893 | Mezcla editor + diálogos. Extraer `actualizar_salida`, `_colorear_resultado` a `editor.py`. |
| `modules/tools_creative.py` | 1830 | Queda lo cohesivo (sugerir/pulse/anclaje/comparar consistencia / negative builder). |
| `modules/tools_workflow.py` | 1726 | Posible: A/B testing + comparar modelos (~552 líneas) → `ab_testing.py`. |

#### E4) Arquitectura  🟡 MEDIA (refactor mayor, riesgo alto)
- **A1 Migrar Mixins → Composición pura** — `ArquitectoApp` hereda
  ahora **13 mixins** (era 8). Ya hay `components.py` con proxies.
  ~5-10 días. Más urgente ahora con tantos mixins.
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
- ✅ ~~**Lag cambio de modo**~~ — arreglado en sesión 4.

#### E7) UI/UX polish  🟢 BAJA
- **U4 Monkey-patch CTkToolTip** — `main.py` tiene ~20 líneas de
  monkey-patch. Crear envoltorio (`GPromptToolTip`).
- **U5 i18n** — toda la UI en español.

#### E8) Features nuevas  🟢 BAJA
- ✅ ~~**F3 Undo/Redo en `txt_salida`**~~ — hecho en sesión 4.
- **F4 Exportar a JSON/Markdown/PDF** — solo CSV hoy.
- **F5 Diff visual entre versiones** — ya existe `_cmd_diff_versiones`,
  podría hacerse más visible.
- **F1 Plugin system** — ambicioso.
- **F2 API REST** — ambicioso.

---

## 🪶 Patrones nuevos establecidos en sesión 4

### Patrón "diff modal antes de aplicar"
Aplicado en Bloque 4 (Refinar) y Análisis Inverso. Cualquier acción que
sobreescriba `txt_salida` con un texto nuevo del LLM debería pasar por:

```python
self._mostrar_diff_refinamiento(texto_previo, texto_nuevo)
```

Que abre `_abrir_ventana_diff(... on_apply=..., on_cancel=..., on_undo=...)`.
El callback `on_apply` apila el original como `v{N} (pre-refinamiento)` en
`_versiones_prompt`. `on_undo` solo aparece si hay una versión previa
`(pre-refinamiento)` en el stack.

### Patrón "comparador con botones extra"
`_abrir_comparador(variaciones, labels=None, extra_botones=None)`. Cada
extra-botón es `(label, fg_color, callback)`. El callback recibe
`(variaciones, ventana)`. Permite extender el comparador sin tocar su
núcleo. Usado por Board→Vídeo (Bloque 6).

### Patrón "partición de mixin"
Pasos canónicos para particionar un cluster cohesivo a su propio
módulo:

1. **Identificar el rango** con `grep -n "^    def "` (líneas y next defs).
2. **Crear `modules/<nuevo>.py`** con:
   - Docstring claro listando métodos + dependencias `self.*`.
   - Imports necesarios.
   - Clase `<Nuevo>Mixin`.
   - Métodos copiados sin modificar (excepto deduplicaciones obvias).
3. **Eliminar el rango** del original (Python con slicing de listas,
   no sed):
   ```python
   new_lines = lines[:start_idx] + lines[end_idx:]
   ```
4. **Update `modules/__init__.py`**: import + añadir al `__all__`.
5. **Update `app.py`**: añadir mixin al final de la cadena de bases.
6. **Verificar**:
   - `python -c "import app; print('OK')"`
   - `python -m pytest tests/ -q` → 48/48
   - `inspect.getsourcefile(ArquitectoApp.<metodo>)` apunta al nuevo módulo.

### Patrón "caché de UI por modo"
Aplicado en `_construir_checkboxes`. En vez de destruir/reconstruir
widgets al cambiar modo:

```python
if not hasattr(self, '_cache_X'):
    self._cache_X = {}
key = id(lista_inputs)  # o modo, o cualquier discriminante
if key in self._cache_X:
    # Mostrar el cacheado, ocultar los demás
    for k, sub in self._cache_X.items():
        if k != key:
            sub.pack_forget()
    self._cache_X[key].pack(...)
    return
# Primera vez: construir + cachear
sub = ctk.CTkFrame(parent)
self._cache_X[key] = sub
# ...construir hijos dentro de sub...
```

Funcionó perfectamente para los 395 checkboxes de estilos (257+118+20).

### Patrón "edit_separator para undo coherente"
Si `actualizar_salida(texto)` o similar reemplaza el texto de un
`CTkTextbox` con `undo=True`, emitir `edit_separator()` antes y después:

```python
try: txt._textbox.edit_separator()
except Exception: pass
txt.delete("1.0", "end")
txt.insert("1.0", nuevo_texto)
try: txt._textbox.edit_separator()
except Exception: pass
```

Así Ctrl+Z lo cuenta como un solo paso distinto de las ediciones manuales.

### Patrón "títulos de grupo en barras"
Estructura de datos para barras con grupos visualmente identificables:

```python
grupos = [
    ("📋 TITULO_GRUPO", "#color_titulo", [
        (label, width, fg, cmd, tooltip),
        ...
    ]),
    ...
]
for titulo, color_tit, botones in grupos:
    grp_frame = ctk.CTkFrame(parent, fg_color="transparent")
    grp_frame.pack(side="left", padx=(0, 6))
    ctk.CTkLabel(grp_frame, text=titulo,
                  font=ctk.CTkFont(size=8, weight="bold"),
                  text_color=color_tit).pack(anchor="w", padx=4)
    btn_row = ctk.CTkFrame(grp_frame, fg_color="transparent")
    btn_row.pack(side="top", anchor="w")
    for text, w, fg, cmd, tip in botones:
        # crear botón en btn_row
```

Aplicado a la barra superior (b8021fc) y la inferior (f8bc2aa).

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
   python -c "import app; print(app.ArquitectoApp.__mro__)"
   ```
   Debe listar los 13 mixins en la cadena de herencia.

3. **Decidir entre**:
   - **D1 GitHub Actions CI** (~1 día) — alta prioridad.
   - **D2 Ruff + pre-commit** (~1h) — quick win.
   - **A1 Migrar Mixins → Composición** (~5-10 días) — refactor mayor,
     ahora más urgente con 13 mixins.
   - **Auditar `core.py`** (2861 líneas, próximo más grande) +
     particionar `_inyectar_specs_*` a `prompts_inyeccion.py`.
   - **T1 Cobertura tests** empezando por `workers_ia.py` (interfaz
     limpia tras partición).
   - **SeaArt char limits** — necesita info del usuario.

4. **Patrón de trabajo establecido**:
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
# Ver árbol de commits de la sesión 4
git log --oneline 4402075..HEAD

# Ver árbol de commits desde el HANDOFF original
git log --oneline 5d4a662..HEAD

# Ver cambios de un commit
git show <hash>

# Tests
python -m pytest tests/ -v

# Arrancar app (modo background para probar)
python main.py

# Verificar dónde se resuelve un método
python -c "import app, inspect, os; print(os.path.basename(inspect.getsourcefile(app.ArquitectoApp._cmd_adn_visual)))"
```

---

*Generado al final de sesión 4 — 13 commits añadidos, 48/48 tests,
working tree limpio. 63 commits ahead de origin/main acumulados desde
las 4 sesiones. No se ha hecho push. Bloques de profundidad **6/6** ✅.
5 particiones reducen `tools_creative.py` un 57% (4211 → 1830 líneas).*
