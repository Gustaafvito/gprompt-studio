# 🧾 Handoff — G-Prompt Studio (sesión 2)

Documento de continuación. Esta es la **segunda** sesión después del HANDOFF original.
Generado al final, working tree limpio.

---

## 📍 Estado del proyecto

**G-Prompt Studio** — app de escritorio Python + customtkinter para generar
prompts de IA generativa (imagen, vídeo, audio) con 14 LLMs como motores.

**Working tree limpio.** **48/48 tests pasan.** Branch: `main`, **44 commits
adelante de `origin/main`** (no he hecho push).

Estructura: ver `ESTRUCTURA.md`.

---

## 🎯 Qué se hizo en esta sesión (sesión 2)

Continuación del HANDOFF anterior. El usuario eligió:

1. **Primero los 7 detalles menores** pendientes del HANDOFF original ✅
2. **Después el menú 🎨 UI** completo (5 mejoras) ✅
3. **Después el menú ⚙️ Workflow** (solo los 2 bugs críticos) ✅
4. **Después refactor de la barra de acciones** (colores semánticos, agrupación) ✅
5. **Después un plan de "profundidad"** (Bloques 1-6 para hacer las funciones más completas):
   - ✅ **Bloque 1** completo (Ideas clicables · Pulse niveles · Preview caché)
   - ✅ **Bloque 2** completo (Sugerir top 3 · Compar con ganador) + 3 fixes posteriores
   - ⏳ Bloques 3-6 pendientes

### 7 detalles menores (commits `0103dd2` → `e47f0b5`)
- `0103dd2` fix: borrar plantilla sin cerrar ventana + confirmación al borrar fórmula
- `08c7f9e` feat: ADN biblioteca (Crear nuevo, Refrescar, fix `_guardar_biblioteca` roto, soporte `texto_libre`) + moodboard reusable (estilos guardables, validación imágenes corruptas, biblioteca de estilos del moodboard)
- `e47f0b5` test: arreglar 2 tests con drift en `test_persistence.py` (46/48 → 48/48)

### Menú 🎨 UI (commits `3ea46a3` → `0240790`)
- `3ea46a3` fix: eliminar `_cmd_toggle_tema` muerto en core.py (estaba en core.py:553 y dialogs.py:176, ganaba DialogsMixin por MRO), arreglo doble escaneo ComfyUI en Ajustes, auditoría de los 32 atajos hardcoded contra bindings reales (todo coincide), buscador + click-to-copy en Atajos teclado, debounce 200ms en Biblioteca
- `0240790` feat: barra de acciones con grupos visuales y separadores verticales (`_render_grupos()` helper), Quick movido a fila 1 (es variante de Generar)

### Menú ⚙️ Workflow (commit `7a3650e`)
- `7a3650e` fix: Cron crash al cerrar ventana (cancelar `after_id` + flag `cerrada` + `protocol(WM_DELETE_WINDOW)`), confirmación al borrar macro

### Refactor barra acciones (commit `174ecc4`)
- Sistema de colores semántico unificado:
  - 🟢 Verde (4 tonos) = genera output (Ideas, Generar, Quick, Variaciones, Regenerar)
  - 🔵 Azul = analiza input (Analizar, Img→Prompt, Análisis Inv)
  - 🟣 Morado = ADN + edición (ADN Visual, Refinar, Copiloto)
  - 🟠 Naranja = variantes múltiples (Iterar, Pulse, Sugerir)
  - 💗 Rosa = multi-prompt narrativo (Mood, Story, Board, Walk)
  - 🌐 Cyan = conversiones (→Vídeo, Compar)
  - ⚫ Gris = utilidades (Batch, Preview)
- Quick cambia de naranja a verde claro (antes rompía el grupo Generación)
- Variaciones cambia de azul a verde claro
- Iterar movido del grupo Edición al grupo Variantes (comparte lógica con Pulse/Sugerir)
- Story (solo Imagen) y Board (solo Vídeo) ahora se **deshabilitan visualmente**
  según el modo activo en `_on_modo_cambio()`, antes avisaban con messagebox después del click
- Story usa 🎞 (era 🎬 que ya lo usa →Vídeo)
- Preview usa 🖼 (era 👁️ que se confundía con 👁 Analizar)

### Bloque 1 (commit `9ad60b0`)
- **💡 Ideas clicables**: cards con cursor hand2, click en la card aplica
  directo, botón "🔁 Más" en header, botón "✨ Similares" por idea
- **⚡ Pulse** con modal de configuración: 3 niveles (default rápido) / 5
  niveles (Ultra estable→Máximo riesgo) / 🎚 Personalizado con 3 sliders
  (T de 0.1 a 1.5). Recuerda última config en `preferencias.pulse_config`.
  Helper `_lanzar_pulse(idea, temperaturas)` reutilizable.
- **🖼 Preview** con caché in-memory (key=md5(prompt limpio), max 20
  entradas con LRU). Misma prompt → respuesta instantánea sin API. Ventana
  muestra URL Pollinations + botón "🔗 Copiar URL" + "🌐 Abrir en navegador"
  + banner "📥 Servido desde caché" cuando hay hit. Refactor a
  `_mostrar_preview_window()` reutilizable.

### Fix Variaciones (commit `61848e1`)
- Bug reportado: solo se veía "1" en Resultado editable al pulsar Variaciones.
- Causa: el panel inline insertado antes de `frame_entrada` comprimía
  `txt_salida` a 1 línea, y `_worker_ia` sobrescribía con texto crudo
  multi-bloque ilegible.
- Solución: ahora Variaciones abre un **Toplevel modal** con cards visibles
  donde cada variación se muestra con preview completo + 4 botones
  (✅ Aplicar al resultado · 📋 Todo · 📋 POS · 📋 NEG). El `txt_salida`
  ya no se sobrescribe automáticamente (solo cuando el usuario aplica una).

### Bloque 2 + sus fixes (commits `25db87b` → `2e4a54d`)
- `25db87b` Sugerir devuelve TOP 3 modelos con razón individual (medallas
  🥇🥈🥉), botón "✅ Usar este modelo" por card que cambia el combo del
  modelo activo, botón "🚀 Probar los 3 en paralelo" que genera el prompt
  optimizado para cada modelo y abre comparador. Helper
  `_probar_modelos_y_comparar(idea, modelos, modo)` reutilizable.
  Compar normal: slider de **2-5 modelos** (antes 3 fijos), filas
  dinámicas. Botón "🏆 Usar este (modelo+prompt)" aplica AMBAS cosas
  (modelo + prompt), antes solo cargaba el prompt.
- `1ade7f8` fix: el LLM devolvía respuestas CONCATENADAS con múltiples
  POSITIVE/NEGATIVE/prosa. Refuerzo del prompt + defensa regex client-side
  que extrae solo el primer bloque limpio. Detecta si las N respuestas son
  idénticas y avisa al usuario.
- `5451292` feat: comparador persistente — al pulsar "Usar" NO se cierra
  la ventana. La card aplicada gana borde dorado, las demás se desmarcan.
  Botón explícito "Cerrar comparador" añadido.
- `c1b4ef9` fix: IndexError con N>3 modelos en Compar (lista `colores_hdr`
  hardcoded a 3 elementos, ahora cíclica con 5 colores). Layout dinámico,
  highlight visual de card aplicada también en Compar normal.
- `2e4a54d` fix: replicar el prompt estricto + extractor regex en
  `_abrir_ventana_comparacion._generar()` — antes solo se aplicó en
  Sugerir → Probar los 3, no en Compar normal, y el LLM mezclaba modelos
  (Nano Banana incluía "counterfiet:" y "disney pixar:" en su respuesta).

---

## 📜 Commits de esta sesión (12 commits, en orden)

```
2e4a54d fix(compar): petición estricta + extractor — antes el LLM mezclaba modelos
c1b4ef9 fix(compar): IndexError con N>3 modelos + layout + highlight aplicado
5451292 feat(comparador): persistente al usar — modelo+prompt+highlight visual
1ade7f8 fix(sugerir/compar): Probar los 3 — respuestas concatenadas + labels
25db87b feat(profundidad): Bloque 2 — Sugerir top 3 + Compar con ganador
61848e1 fix(variaciones): modal con cards visibles — antes el resultado se comprimía
9ad60b0 feat(profundidad): Bloque 1 — Ideas clicables · Pulse niveles · Preview caché
0240790 feat(ui): barra de acciones con grupos visuales
174ecc4 feat(ui): colores semánticos + Iterar reagrupado + Story/Board disabled-aware
7a3650e fix(workflow): 2 bugs — Cron crash al cerrar + Macros sin confirmación
3ea46a3 feat(ui): mejoras en menú UI — código muerto, escaneo doble, atajos
e47f0b5 test: arreglar drift en test_persistence (2 tests)
08c7f9e feat(herramientas): ADN biblioteca + moodboard reusable
0103dd2 fix(plantillas/formulas): UX al borrar — sin parpadeo + confirmación
```

(14 commits desde el HANDOFF anterior. Working tree limpio.)

---

## ✅ Menús ya revisados

- 📊 **Análisis** — completo (sesión 1)
- 💾 **Backup** — completo (sesión 1)
- 📁 **Datos** — completo (sesión 1)
- 🛠 **Herramientas** — completo (sesión 1) + detalles menores (sesión 2)
- 📝 **Plantillas** — completo (sesión 1) + detalles menores (sesión 2)
- 🎨 **UI** — completo (sesión 2)
- ⚙️ **Workflow** — solo los 2 bugs críticos en sesión 2. **5 detalles UX/menores
  NO atacados** (ver abajo).
- 🎬 **Barra de acciones** — refactor visual completo (sesión 2)

---

## 🚧 Pendiente para la próxima sesión

### A) Bloques de "profundidad" sin terminar (4 de 6)

El usuario quería implementar 6 bloques para hacer las funciones más completas.
Hechos los Bloques 1 y 2. Pendientes:

#### Bloque 3 — Slider N en multi-prompts (~2-3h)
Permitir N variable (en vez de N hardcoded) en estas funciones:
- 🔀 **Variaciones** (`cmd_variaciones` en `modules/core.py:1905`) — actualmente 3 fijo
- 🔂 **Iterar** (`_cmd_iteracion` en `modules/core.py:2059`) — actualmente 5 fijo
- 🎭 **Mood** (`_cmd_moodboard` en `modules/tools_creative.py`) — actualmente 6 fijo
- 🎞 **Story** (`_cmd_story_sequence` en `modules/tools_creative.py:1882`) — 3 fijo
- 📽 **Board** (`_cmd_storyboard_video` en `modules/tools_creative.py:1927`) — 4 fijo
- 🌀 **Walk** (`_cmd_random_walk` en `modules/tools_creative.py:1974`) — 5 fijo

(Pulse ya tiene su propio sistema 3/5/custom — no tocar)

**Patrón a aplicar**: similar al modal de Pulse del Bloque 1 (`_cmd_pulse` en
tools_creative.py:73) — modal con slider, recordar última config en
preferencias, Enter dispara generar. Cuidado con las funciones que se llaman
también desde Macros (`_cmd_iteracion` y derivadas) — no romper esa ruta.

#### Bloque 4 — Refinar con diff + undo (~2h)
- `cmd_refinar` (`modules/core.py:2139`) sobrescribe el prompt sin avisar qué cambió.
- Antes de aplicar, mostrar un **diff visual** verde/rojo (ya existe la
  función `_cmd_diff_versiones` en `app.py:837` para inspiración).
- Botón "↩️ Deshacer refinamiento" usando el sistema `_versiones_prompt` ya
  existente (`_guardar_version_prompt` en `tools_workflow.py:452`).
- Permitir cancelar el refinamiento antes de aplicar.

#### Bloque 5 — Walk árbol visual (~3h)
- `_cmd_random_walk` (`modules/tools_creative.py:1974`) hace 5 derivaciones
  lineales (cada una basada en la anterior).
- Convertir a **árbol con ramas**: el usuario puede en cualquier paso
  "ramificar" en 3 direcciones distintas en lugar de seguir lineal.
- Visualización tipo grafo simple (CTkCanvas o frames anidados).
- Guardar la ruta elegida como "evolución X→Y→Z".

#### Bloque 6 — Story/Board configurables (~3h)
- 🎞 Story (`_cmd_story_sequence` en `tools_creative.py:1882`) — actualmente
  Wide/Medium/Close fijos. Permitir elegir tipos de shot
  (POV/OTS/Aerial/Dutch/Low/High angle/...).
- 📽 Board (`_cmd_storyboard_video` en `tools_creative.py:1927`) —
  apertura/desarrollo/climax/cierre fijos. Permitir elegir N frames (4/6/8)
  y nombrar cada beat.
- Encadenar Board con **🎬 →Vídeo** automáticamente (generar prompt de
  vídeo que use esos N frames como keyframes).

### B) Workflow — 5 detalles UX que se dejaron pasar

El usuario eligió "solo los 2 bugs 🔴" en la revisión del menú Workflow,
pero estos 5 detalles UX/menores siguen pendientes (de la tabla del análisis):

1. **🆚 A/B Testing**: comentario en chino mezclado en `_actualizar_checkboxes`
   (línea 1575 de `tools_workflow.py`) — copy-paste stale. Limpieza trivial.
2. **🔄 Macros sin editor**: solo se puede borrar+recrear, no editar.
   Tampoco se pueden reordenar pasos.
3. **🔎 Búsqueda global sin debounce**: cada tecla busca en 8 colecciones.
4. **🔎 Búsqueda global sin filtro por tipo**: mucho ruido.
5. **👥 Grupo personajes**: el textbox de "Relación" lleva ejemplo pre-poblado
   que se cuela en la idea si el usuario no lo borra. Sustituir por
   `placeholder` real del Textbox.
6. **🎙 Grabar sesión**: dead code en `_iniciar_grabacion` líneas 1207-1217 —
   rama `else` que duplica el "parar" del toggle. Limpieza trivial.

### C) Botones de barra principal (no revisados a fondo todavía)

- 🧬 **ADN Visual** (`_cmd_adn_visual` en `tools_creative.py:670`) — revisión
  pendiente, pero está bastante usado en otros sitios y ya recibió fixes
  indirectos en sesión 1.
- 🔍 **Análisis Inverso** (`_cmd_analisis_inverso` en `tools_creative.py:397`)
  — revisión pendiente.

### D) Comparador — mejoras opcionales que ofrecí pero no se implementaron

- Botón "comparar lado a lado con diff" entre 2 cards seleccionadas
- Botón "abrir Preview Pollinations con cada modelo" (genera bocetos en grid)

### E) Mejoras de UX globales propuestas pero no implementadas

- **Reorganizar barra de acciones en 3 secciones explícitas** (mencionado al
  usuario): Generación / Análisis / Composición con divider entre cada
  bloque. Hoy hay separadores entre grupos pero la jerarquía visual
  podría ser más fuerte.
- **Tooltips visibles permanentes** para los 14 botones-icono de la barra
  inferior (POS/NEG/Todo/Comfy/Trad/etc) — algunos no tienen texto
  y la descubribilidad depende del hover.
- **Párrafo del modelo** (la descripción larga de "GPT Image 2..." debajo
  del combo Modelo) — colapsable o tooltip, hoy ocupa 6 líneas.

---

## 🪶 Detalles importantes para la próxima sesión

### Patrón establecido para confirmar antes de borrar
- ADN, Seeds, Snippets, Fórmulas, Plantillas, Macros — TODOS tienen
  `messagebox.askyesno()` antes del pop().
- Cuando añadas nuevas listas de colecciones, **NO te olvides** del askyesno.

### Patrón establecido para modales de configuración
Hecho en Pulse (Bloque 1) y Compar (Bloque 2). Mismo patrón para Bloque 3:
```python
def _cmd_X(self):
    ...
    prefs = self.store.cargar_preferencias()
    ultima = prefs.get("X_config", {"n": default, ...})

    cfg = GPromptWindow(self)
    cfg.geometry(...)
    cfg.transient(self); cfg.grab_set()

    # ... sliders / radio / etc ...

    def _ejecutar():
        n = ...
        # Guardar config
        prefs_g["X_config"] = {...}
        self.store.guardar_preferencias(prefs_g)
        cfg.destroy()
        self._lanzar_X(idea, n)  # helper reutilizable

    cfg.bind("<Return>", lambda _e: _ejecutar())
```

### Patrón establecido para extraer prompt del LLM
Cuando se generen N prompts en paralelo desde múltiples threads (Compar,
Sugerir → Probar los 3), seguir:
1. **Petición ESTRICTA** con estructura exacta:
   `DEVUELVE EXACTAMENTE 2 LÍNEAS: POSITIVE PROMPT: ... / NEGATIVE PROMPT: ...`
2. **Defensa regex client-side** tras la respuesta:
   ```python
   m_pos = re.search(r'(?:POSITIVE\s+)?PROMPT\s*:\s*(.+?)(?=\n\s*NEGATIVE\s+PROMPT\s*:|\n\s*POSITIVE\s+PROMPT\s*:|\n\s*###|\n\s*\*\*\*|\Z)', resp, re.DOTALL|re.IGNORECASE)
   ```
   Capturar solo el primer bloque. Truncar a `max_c + 200` por la última coma.
3. **Detección de duplicados**: si las N respuestas son idénticas, avisar.

### Patrón establecido para `_abrir_comparador`
Acepta `labels=` opcional para sustituir "Variación #N". Si una variante
empieza con `### nombre ###\n`, esa cabecera se extrae automáticamente.

### Patrón establecido para "Usar" en comparadores
NO destruir la ventana. Aplicar (modelo + prompt) y marcar la card
aplicada con borde dorado (#fbbf24). Botón explícito "Cerrar comparador"
en el pie.

### Helper nuevo a usar
- `_intentar_cambiar_modelo(nombre)` en `app.py` — busca el modelo en la
  lista del modo actual y aplica al combo correspondiente. Devuelve el
  nombre aplicado o None. Útil para integrar comparadores con la UI.

### Story/Board y modo activo
- `_on_modo_cambio()` en `modules/core.py:950` habilita/deshabilita los
  botones `self.btn_story` y `self.btn_board` según el modo.
- Si en Bloque 6 se renombran o se mueven, recordar actualizar las refs
  en `_on_modo_cambio()`.

---

## 🔁 Cómo continuar (sesión nueva)

1. **Confirmar baseline**:
   - `python main.py` arranca limpio
   - `python -m pytest tests/` → 48/48
2. **Decidir entre**:
   - Bloque 3 (Slider N) — más rápido, alto valor
   - Bloque 4 (Refinar diff+undo) — más impactante visualmente
   - Bloque 5 (Walk árbol) — más ambicioso
   - Bloque 6 (Story/Board config) — útil para creadores serios
   - O atacar los detalles UX restantes de Workflow (A.1-A.6)
   - O revisar los botones de barra ADN Visual y Análisis Inverso (C)
3. **Patrón de trabajo de esta sesión**:
   - Análisis honesto en tabla antes de tocar nada
   - Priorización 🔴 ALTA / 🟡 MEDIA / 🟢 BAJA
   - Preguntar antes de empezar bloques grandes
   - 1 commit por bloque coherente
   - Smoke test (`python -c "import app; print('OK')"`) tras cada Edit
   - Probar la app en background con `python main.py` cuando el usuario lo pida
   - Si algo da bug en la prueba, fix inmediato + commit + relanzar app

---

## ⚙️ Atajos útiles para retomar

```powershell
# Árbol de commits de esta sesión
git log --oneline 5d4a662..HEAD

# Ver cambios de un commit
git show <hash>

# Revertir un commit aislado si rompe algo
git revert <hash>

# Tests
python -m pytest tests/ -v

# Arrancar app (modo background para probar)
python main.py
```

---

*Generado al final de sesión 2 — 14 commits añadidos, 48/48 tests, working tree limpio.*
*Branch: `main`. No se ha hecho push.*
