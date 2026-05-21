# 🧾 Handoff — Sesión de revisión G-Prompt Studio

Documento para retomar la conversación en una sesión nueva sin perder contexto.
Generado al final de una sesión larga que se acercó al límite de tokens.

---

## 📍 Estado del proyecto

**G-Prompt Studio** es una app de escritorio (Python + customtkinter) para
generar prompts de IA generativa (imagen, vídeo, audio) usando 14 LLMs
distintos como motores.

**Working tree limpio** tras 36 commits en esta sesión. Tests baseline:
46/48 pasan (los 2 que fallan son drift preexistente en
`test_persistence.py`, no introducido en la sesión).

Estructura: ver [ESTRUCTURA.md](ESTRUCTURA.md) — está al día.

---

## 🎯 Lo que se hizo (en orden)

La sesión fue una revisión sistemática de toda la app, menú por menú,
con un patrón: **análisis honesto → priorización → arreglo**.

### Fases 1-5: refactor de base (commits `877bcdf` → `0488f58`)

1. **Limpieza segura**: borrado de tests muertos, mover `windows.py` a
   `modules/`, README/ESTRUCTURA actualizados.
2. **try/except + imports lazy**: 140 `except: pass` → `logger.debug`,
   `openai` lazy import, descubrí que muchos `logger.X(...)` eran
   NameError silenciados.
3. **Partir config.py**: 4040 → 1112 líneas. 6 estructuras movidas a
   `data/*.json` (MODEL_SPECS, estilos, biblioteca, etc.).
4. **Quitar monkey-patches**: 75 líneas de patches a `ctk.CTkToplevel`
   eliminadas. 69 `ctk.CTkToplevel(...)` → `GPromptWindow(...)` en 10
   archivos.
5. **Capa de componentes**: 8 componentes (`self.creative`,
   `self.workflow`, …) sobre los mixins existentes. NO es composición
   pura — los mixins siguen heredados — pero permite namespacing
   progresivo.

### Limpieza y assets (commit `0e50630`)
Borrados `imagenes/` y `MODELOS_IMAGEN.md` (no usados). Trackeados
`config/plantillas_default.json` y `GUIA_ESTILOS.md`.

### Guía de estilos (commits `3856577` → `ee19c89`)
- Botón "📖 Guía de estilos" en menú Análisis
- Tooltips por checkbox (256/257 estilos cubiertos)
- Filtro por modo (Imagen/Vídeo/Audio) con auto-detección
- Paginación + debounce (300ms)
- **100% de cobertura** con el catálogo de la app: 257 imagen, 118
  vídeo, 20 audio. Añadidos 97 estilos al `GUIA_ESTILOS.md`.

### Menú 📊 Análisis (commits `e95f86d` → `99c63c7`)
6 items revisados: Auto-mejora, Crítica historial, Estadísticas, Guía
de estilos, **Modo educativo (Glosario)**, **Tutorial completo**.

Cambios principales:
- **Glosario**: 43 entradas extraídas a `data/glosario.json`, 5
  categorías (ordenadas alfabéticamente), filtro segmentado, botón
  "▶ Probar" en 17 entradas vinculadas a funciones reales.
- **Tutorial**: 26 pasos extraídos a `data/tutorial.json`, índice
  lateral clicable, progreso persistente en `preferencias.json`,
  botón "▶ Probar ahora" en 24/26 pasos con mini-DSL `focus:WIDGET`,
  `mode:imagen|video|audio`, `tab:NOMBRE`. Pre-validación para
  acciones que necesitan prompt en salida.
- **Auto-mejora**: el LLM devuelve JSON estructurado, render como
  cards con botón "✨ Aplicar versión mejorada".
- **Crítica historial**: caché en preferencias.json + selector
  "últimos N".
- **Estadísticas**: filtro de rango (7d/30d/90d/Todo), top estilos
  restaurado.

### Menús 💾 Backup y 📁 Datos (commits `3194fc4` → `42d9b1a`)
- 🐛 **4 bugs críticos** arreglados: "Limpiar estrellas borraba
  favoritos", "CSV columna Modelo vacía", "CSV estilos lista mal
  serializada", "Backup no incluía plantillas".
- 🛡 **Auto-backup pre-restore**: si te equivocas restaurando, tus
  datos anteriores se guardan en
  `~/.arquitecto_prompts/backups/pre_restore_AAAA-MM-DD_HHMM.json`.
- Buscadores en Personajes y LoRAs (con edición inline + filtro por
  familia en LoRAs).
- Filtro por modo + paginación real + botón Copiar en
  historial/favoritos/estrellas.
- Estrellas ahora muestran su nota destacada en dorado.
- Export CSV con selector previo (qué exportar) + columna Origen.

### Menú 🛠 Herramientas (commits `5bb7120` → `c8c0539`)
6 items: Anclaje rasgos, Detectar estilo, Export CLI, Modo Cliente,
Negative Builder, Paleta colores.

Cambios:
- 🐛 **3 bugs**: paleta crasheaba al guardar (`store.guardar()` no
  existe), presets Negative Builder se perdían al cerrar, buscador
  destruía estado de checkboxes.
- 🐛 **NameError `_dt`** arreglado en 3 sitios (era código muerto que
  saltó al activar el guardado de paleta).
- 🧬 **Indicador ADN permanente** en header (aparece solo si hay ADN
  activo, click → ver/desactivar).
- 🎭 **Moodboard**: ❌ por thumbnail + aviso máximo 5 + "+N más".
- 📤 **Export CLI**: filtro `🖼 Imagen / 🎬 Vídeo / 🎵 Audio / 📦 Todos`
  con auto-selección del modo activo. Lista vertical de cards en vez
  de 15 tabs apretadas.
- 💾 **ADN persiste** entre reinicios (preferencias.anclaje_visual).
- 💼 **Modo Cliente**: 5 plantillas de brief predefinidas + recuerda
  el último brief.
- 📚 **Biblioteca de paletas** con UI (swatches clicables, Aplicar/
  Copiar/Borrar).
- 🐛 **Propuestas profesionales**: las 5 salían como "Propuesta sin
  nombre". Bug del parser corregido. Botón Guardar ahora persiste en
  Favoritos con `origen: "modo_cliente"`.
- 🐛 **`DataStore.borrar_entrada()` faltaba** — añadido método
  genérico que valida índice y persiste.

### Menú 📝 Plantillas (commits `6d568a0` → `e7f3f2a`)
6 items: Añadir tags (snippets), Biblioteca ADN, Expansión rápida,
Fórmulas, Plantillas, Seeds favoritos.

- 🐛 **4 bugs**: borrar ADN cerraba ventana, borrar Seed cerraba
  ventana, `combo_modelo_vid` mal nombrado (era `combo_modelo_video`),
  trigger expansión rechazaba guiones.
- 🔍 **Buscadores** en las 5 ventanas (snippets, ADN, fórmulas,
  seeds, plantillas).
- ✨ **Wizard de variables** al cargar plantilla: campo por variable,
  previsualización en vivo, **recuerda los últimos valores por
  plantilla** en `preferencias.plantilla_variables_ultimas`.
- 📂 **Filtro por categoría en plantillas** (10 categorías ya estaban
  en el JSON pero se descartaban al cargar).
- ✏️ **Edición inline** en snippets y fórmulas.
- 💡 **Tooltip de expansión rápida** en el campo "Describe tu idea"
  para que se descubra la funcionalidad `;trigger`+Espacio.
- 📝 Textos explicativos para clarificar Snippets vs Fórmulas (eran
  conceptos solapados sin documentación visible).

---

## 📜 Commits de la sesión (36 en total)

```
e7f3f2a feat(plantillas): wizard de variables recuerda últimos valores
51deba7 feat(plantillas): categorías + descubribilidad expansión + clarificar conceptos
3322d55 feat(plantillas): buscadores + wizard variables + editar inline
6d568a0 fix: 4 bugs en menú Plantillas
e31f18c fix: DataStore.borrar_entrada(coleccion, idx) faltaba
424e43a fix: propuestas Modo Cliente — nombres reales + bug guardar
c8c0539 fix: NameError _dt no definido al guardar paleta / ADN / biblioteca
b6e7180 feat(herramientas): persistencia ADN/brief + plantillas + biblioteca paletas
43204dd feat(herramientas): indicador ADN permanente + moodboard borrar + CLI por modo
fdbd84b test: añadir "paletas" al setup parcheado de DataStore
5bb7120 fix: 3 bugs en menú Herramientas
42d9b1a polish: messagebox de backup/restore más limpios
bc82cda feat(backup): Exportar CSV con selector de colecciones
3877cec feat(datos): UX en personajes, loras, historial/favoritos/estrellas
3194fc4 fix: 4 bugs en Backup/Datos + auto-backup pre-restore
99c63c7 fix(análisis): orden categorías glosario + tutorial diagnosticable
ba10ef3 fix(análisis): pasos 1-6/11/13/18 del tutorial + glosario "Todas" plano
9539fb8 fix(análisis): glosario alfabético + arregla "Probar" para funciones libres
e95f86d feat(análisis): mejoras al menú Análisis — 5 items
ee19c89 docs: guía de estilos — cobertura 100% de los 3 modos
c44924e perf: guía de estilos — paginación + debounce del buscador
73933a6 feat: guía de estilos — filtro por modo (imagen/vídeo/audio)
3856577 feat: guía de estilos integrada en la app + ESTRUCTURA al día
0e50630 chore: limpieza de archivos no usados + trackear assets necesarios
0488f58 refactor: fase 5 — capa de componentes sobre mixins
17c3d55 refactor: fase 4 — quitar monkey-patches de CTkToplevel
9eeb756 refactor: fase 3 — partir config.py en data/*.json
ec30dfb refactor: fase 2 — try/except + imports lazy
877bcdf chore: fase 1 — limpieza segura
```

---

## ✅ Menús ya revisados

- 📊 **Análisis** — completo
- 💾 **Backup** — completo
- 📁 **Datos** — completo
- 🛠 **Herramientas** — completo (con 3 detalles menores pendientes,
  ver abajo)
- 📝 **Plantillas** — completo (con 4 detalles menores cosméticos
  pendientes, ver abajo)

## 🚧 Menús pendientes de revisar

- 🎨 **UI** (Ajustes, Atajos teclado, Biblioteca, Cambiar tema,
  Dashboard, Modo Focus)
- ⚙️ **Workflow** (A/B Testing, Búsqueda global, Cron prompts, Grabar
  sesión, Grupo personajes, Macros, Proyectos, Versiones prompt)

Hay también dos botones grandes en la barra del medio que merecen
review: **ADN Visual** (en barra principal, no en menú) y **Análisis
inverso**.

---

## 🪶 Detalles menores pendientes (no críticos)

### En Herramientas
1. **Anclaje rasgos**: cuando la biblioteca de ADNs crezca a 20+
   entradas, sería útil añadir buscador. Hoy ya tiene buscador
   (commit `3322d55`) pero la **descubribilidad de la "Biblioteca
   ADN"** podría mejorar (botón más visible).
2. **Moodboard**: si una imagen está corrupta o ilegible, el flujo
   falla silenciosamente. Convendría capturar el error y mostrar
   cuál imagen falló.
3. **Estilo detectado del moodboard**: actualmente NO se guarda como
   preset reusable — solo se aplica al prompt actual. Idea: guardar
   en biblioteca de estilos.

### En Plantillas
4. **Borrar plantilla predefinida** cierra y reabre la ventana
   (parpadea ~0.5s). En ADN y Seeds usé `_refrescar()` sin cerrar —
   sería consistente aplicarlo aquí.
5. **Crear ADN desde la biblioteca** no existe — Seeds tiene
   "+ Crear nuevo seed" pero ADN no. Hoy solo se crean ADNs desde
   "Anclaje rasgos" (carga imagen + Vision).
6. **Confirmación al borrar snippet** — actualmente borra sin
   `askyesno`. Un click accidental podría perder un snippet.
7. **Snippets vs Fórmulas técnicamente solapadas** — los textos
   explicativos ahora ayudan, pero estructuralmente son lo mismo
   (lista de dicts con nombre + contenido). Refactor mayor sin valor
   inmediato.

### Tests
8. **2 tests de `test_persistence.py` fallan** desde hace tiempo
   (drift entre tests y código, no introducido en esta sesión):
   - `test_historial_max_100` — el código permite > 100
   - `test_corrupt_preferences_returns_empty` — `{}` esperado pero
     `{'_ejemplos_iniciados': True}` devuelto
   No los he tocado para no enmascarar el drift; merece su propio
   commit de "arreglar tests o actualizar comportamiento".

---

## 🔁 Cómo continuar (en sesión nueva)

Para retomar:

1. **Confirmar baseline**: `python main.py` debe arrancar limpio,
   `python -m pytest tests/` debe dar 46/48.
2. **Decidir qué tocar** entre:
   - Los menús pendientes (UI, Workflow, botones de barra principal)
   - Los detalles menores listados arriba
   - Algún reporte nuevo del usuario
3. **Patrón de trabajo de la sesión**:
   - Antes de tocar: leer las funciones implicadas, dar análisis
     honesto en formato tabla (bugs / UX / cosmético)
   - Priorizar: 🔴 ALTA (bugs) / 🟡 MEDIA (UX) / 🟢 BAJA (polish)
   - Preguntar antes de empezar refactors grandes
   - 1 commit por bloque de cambios coherente
   - Smoke test (`python -c "import app; print('OK')"`) tras cada bloque
   - Si tocas estructuras del DataStore, recordar añadir el nombre a
     `_NAMES` en `tests/test_persistence.py::_setup_store` o los tests
     fallan con KeyError

---

## ⚙️ Atajos útiles para retomar

```powershell
# Ver el árbol de la sesión
git log --oneline -30

# Ver qué cambia un commit
git show <hash>

# Revertir un commit aislado si rompe algo
git revert <hash>

# Tests
python -m pytest tests/ -v

# Arrancar la app
python main.py
```

---

*Generado el 2026-05-21 al final de una sesión de ~22 horas de trabajo.*
*Working tree limpio. Branch: main.*
