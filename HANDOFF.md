# 🧾 Handoff — G-Prompt Studio

Documento vivo para retomar el proyecto en una sesión nueva. Se mantiene
**conciso y al día**: estado actual + pendientes vivos. El detalle
round-a-round de las sesiones 6-19 está archivado en
[`docs/handoff-historico.md`](docs/handoff-historico.md) (no se actualiza).

Actualizado al cierre de la **sesión 24**.

---

## 📍 Qué es

**G-Prompt Studio** — app de escritorio (Python + customtkinter) para
generar prompts de IA generativa (imagen, vídeo, audio) usando LLMs como
motores (DeepSeek, Gemini, OpenRouter, Claude…). Incluye import/export JSON
para Veo/Sora/Kling, optimizador de prompts en bucle, coste de sesión,
módulo Avatar para datasets LoRA, empaquetado `.exe` + installer, y CI.

Estructura del código: ver [`ESTRUCTURA.md`](ESTRUCTURA.md).
Empaquetado: ver [`BUILD.md`](BUILD.md). Añadir modelos: ver
[`AGREGAR_MODELO.md`](AGREGAR_MODELO.md).

---

## 📊 Estado actual

| Métrica | Valor |
|---|---|
| Tests | **724 passed / 0 failing** (`python -m pytest tests -q`) ✅ |
| Working tree | Limpio |
| Branch | `main` |
| Arquitectura | Composición completa: **1 mixin** (`CoreMixin`) en el MRO, resto son servicios accedidos por `self.<componente>` |
| Lint | Ruff con **F401 + F821** activos (CI 3.10/3.11/3.12) |
| Pre-commit hooks | Activos (line endings, ruff, large files, secrets) |
| Build `.exe` | onedir + onefile + installer (Inno Setup) — al día |
| Code-signing | Opcional vía env vars (`GPROMPT_SIGN_*`), ver BUILD.md |
| Modelos de imagen VISIBLES | ~93 vigentes / 164 total (filtro `vigente:true`) |
| Familia FLUX | **CERRADA — 25/25** vigentes ✅ |
| Familia Anime/Ilustración | **17/17** vigentes ✅ (auditados sesión 22-23) |
| Familia Realismo SD | **6/15** vigentes (9 ocultos, pendiente auditoría) |
| Modelos vídeo | **72 totales**, por familia, alfabéticas (Grok · Hailuo · Happy Horse · Kling · Nano Banana · Otros · PixVerse · SeaArt Oficiales · Seedance · StarDream · Vidu · Wan). Catálogo SeaArt vídeo CERRADO (queda solo "Kling O1" 4.0 suelto, opcional) |
| Modelos audio | **11** (Suno ×4, Udio ×2, Minimax ×2, MusicGo, Mureka V9⚠️prov.). SeaArt audio: Minimax Music 2.5 + Mureka V9 |
| Combo "Estilo" | **por familia** en imagen y vídeo (cada familia su paleta). config.ESTILOS_POR_FAMILIA(_VIDEO) + detectar_familia(_video) |
| Desplegable modelos | Buscador + scroll + **familias colapsables** (▾/▸) + familias alfabéticas |
| Biblioteca ejemplos | 27 entradas |
| Tab Tags | **83 tags** en 6 categorías, bilingüe + tooltips + botón ✨ Sugerir |
| Tab Negativos | presets + campo manual + botón 🛡 Sugerir |
| Tab Estilos | botón 🎨 Sugerir estilos (fix Gemini: usa generar_batch) |
| Coste API | sesión + histórico + desglose por modelo |

### Archivos más grandes (líneas)

| Archivo | Líneas |
|---|---:|
| `app.py` | 2619 |
| `modules/tools_analysis.py` | 2187 |
| `modules/tools_creative.py` | 1902 |
| `modules/ui_builders.py` | 1928 |
| `modules/data_mgmt.py` | 1582 |
| `modules/core.py` | 1242 |

---

## ✅ Sesión 25 — Vídeo SeaArt completo (72), familias UX, Estilo por familia, audio

1. **Catálogo vídeo SeaArt CERRADO: 72 modelos** (commits `3aab79f`, `0fe8ba7` +
   4ª tanda). Motores externos en SUS familias: Wan (2.2/2.5/2.6/2.7), Kling (+3.0
   Turbo, O1), Seedance, StarDream (2.0/Fast), Vidu (Q3 Pro/Turbo), Grok (Video/1.5),
   Hailuo (2.0/2.3 Fast), PixVerse (V6), Happy Horse, Nano Banana, Otros (Sora2/Veo/
   Gemini). Reauditorías: muchos pasaron a modos por RESOLUCIÓN (480p–4K).
   Descartados: remake/edición/referencia. Queda opcional "Kling O1" 4.0 suelto.

2. **UX desplegable** (`feat(ui)` `9514ddf`): familias **alfabéticas** (imagen y
   vídeo) + cabeceras **colapsables** ▾/▸ en `searchable_dropdown` (estado por sesión).
   Retoques tras feedback: cabeceras con el **color original del tema** (`d64e6b9`,
   eran CTkLabel, no botón gris) y **menú "Workflow" reposicionado** para no cortarse
   contra el borde derecho (`2aa9b46`+`a1ddd33`: clamp ANTES del geometry, margen 40px).

3. **Combo "Estilo" por familia** (`feat(estilo)` `e4848af`): TODAS las familias de
   imagen y vídeo tienen su propia paleta. `config.ESTILOS_POR_FAMILIA` (imagen, las 4
   especiales con set a medida; resto por tipo: foto/anime/realismo/arte/diseño/cine)
   + `ESTILOS_POR_FAMILIA_VIDEO` (por motor) + `detectar_familia(_video)`. Inyección:
   `_inyectar_estilo_imagen_generico` (familias sin plantilla) y repoblado del combo
   vídeo al cambiar de modelo.

4. **Audio**: añadido **Mureka V9** al grupo SeaArt Audio (⚠️ PROVISIONAL, sin panel:
   nota/duración/max_chars por medir). Fix de robustez: la descripción de audio
   reventaba con `nota` nula / `duracion_max_min` ausente (mismo patrón que vídeo).

5. **Bug descripción vídeo** (`9eb295b`): `ratios:[]` → IndexError; corregido con
   fallback a `RATIOS_VIDEO` + guardas de `nota:null` en tooltips.

---

## ✅ Sesión 24 — Catálogo vídeo SeaArt 32/32, combo Estilo vídeo, build

1. **Catálogo de vídeo SeaArt: 32/32 oficiales** (`data/model_specs_video.json`,
   `config.GRUPOS_VIDEO`, commit `dc33f97`). Auditados **uno a uno con panel real**
   (sin defaults inventados, decisión del usuario): 28 modelos nuevos + 4 reauditados
   (Film Video, Ultra Pro, Ultra, Sono Lite). Catálogo vídeo total: **45** (32 SeaArt
   + Kling/Seedance/Nano Banana/Sora2/Veo/Wan/Gemini). Convención: `max_chars` del
   contador `0/XXXX`; `has_negative` por la sección "Configuración avanzada"
   (Etiqueta negativa) o anotado *asumido* si el recorte la tapaba; audio manual →
   `has_audio:false`, Sonido nativo → `true`; `max_imagenes` para badge 🖼×N.

2. **Combo "Estilo" (look visual) en la barra de vídeo** (commit `dc33f97`).
   Complementa los géneros narrativos del footer (`ESTILOS_VIDEO`), no los duplica:
   - `config.ESTILOS_VISUAL_VIDEO` (Auto/Cinematográfico/Anime/Realista/3D-Pixar/
     Cómic/Cyberpunk/B&N/Vintage/Acuarela) + `estilo_video_var` (app.py) con persistencia.
   - `ui_builders`: combo + tooltip en `frame_video` (entre Shots y Ratio).
   - `prompts_inyeccion._inyectar_estilo_video`: inyecta hint estético al system prompt
     de vídeo (patrón espejo de `_inyectar_estilo_flux`). +5 tests.

3. **Build regenerado** (ciclo completo): instalador + onefile; los 3 artefactos
   copiados al distribuible del escritorio (`GPromptStudio-Portable/`,
   `-Portable-Onefile.exe`, `-Setup-1.0.0.exe`). Borrados 2 sobrantes viejos.

### 🎬 2ª/3ª tanda de vídeo SeaArt — casi cerrada (commits `3aab79f`, `0fe8ba7`)
Auditado el grid COMPLETO de SeaArt panel a panel. Catálogo **64 modelos**, por familia.
- **SeaArt-branded: COMPLETO** ✅ (Stage, Flow 2.0, Jump Go, Magic Star, Ultra Frame
  Video, Sono Blink, Genesis Video, Sono Epic, Pony, Flow, Magic Rise, Magic Pro,
  Ultra 3.0 Turbo… + los 32 de la 1ª tanda).
- **Motores externos en SUS PROPIAS familias** (decisión usuario: "aunque sean de
  SeaArt, ponlos con su familia"). Grupos nuevos en `GRUPOS_VIDEO`: **Wan** (2.2/2.5/2.6),
  **StarDream** (2.0), **PixVerse** (V6), **Hailuo** (2.0), **Vidu** (Q3 Turbo).
  Reauditados: Seedance 2.0/2.0 Fast/1.5 PRO, Nano Banana Video/Pro, Kling 3.0/2.6,
  Sora2, Wan 2.6 (muchos pasaron a modos por RESOLUCIÓN 480p–4K).
- **FALTAN (motores externos):** Wan 2.7, Vidu Q3 Pro/Reference, Kling 3.0 turbo,
  Kling O1, Grok Imagine Video (+1.5), StarDream 2.0 Fast, Happy Horse, Hailuo 2.3 fast.
- **DECISIÓN: remake/edición/referencia DESCARTADOS** (Clip Remake/Refer, Spark/Opera
  Refer, Ultra Remix, Vidu Q3 Reference…): vídeo-a-vídeo, no generación → el generador
  de prompts aporta poco.
- **Fuera de scope:** checkpoints ComfyUI/HuggingFace ("SeaArt Comfy Helper").
- **Bug corregido** (`9eb295b`): la descripción de vídeo no cargaba con `ratios:[]`
  (IndexError) ni con `nota:null` ("None/5") — fallback a `RATIOS_VIDEO` + guardas. +1 test.
- Discrepancias nota: Veo 3.1 lo tenemos 4.7 / SeaArt 3.0; Wan 2.6 4.3 / SeaArt 3.5.

---

## ✅ Sesión 23 — Tests 0 fallos, lazy Tags, sugerir tags/negativos, fix Gemini

1. **Tests: 28 fallos → 0** (`tests/test_refinamiento.py`, `test_multiprompt.py`,
   `test_adn_visual.py`, `test_modo_cliente.py`): todos los módulos usan
   `_executor.submit()` no `threading.Thread`. Añadido `_SyncExec` (ejecutor
   síncrono fake) a los 4 archivos de test; eliminados los `monkeypatch.setattr`
   de threading que fallaban. Además: `config.py` registró `MODEL_SPECS_VIDEO` en
   `_LAZY_DATASETS` (KeyError en arranque); `test_config.py` actualizado con
   modelo no-vigente válido (`SD 3.5 Large Turbo`).

2. **MiaoMiao Harem V2.0**: `max_chars` corregido 1000 → 2000 según specs reales.

3. **perf(startup): lazy build pestaña Tags** (`ui_builders.py`): los 83
   `CTkButton` + 83 `CTkToolTip` bloqueaban el hilo principal durante el arranque.
   Ahora se construyen la primera vez que el usuario abre la pestaña
   (`tabview.configure(command=…)`). La app es interactiva desde el primer instante.

4. **feat: pestaña Tags oculta en modo Audio** (`ui_events.py`): los tags son
   descriptores visuales que no aplican a audio. `_set_tabs_visibles()` manipula
   el `_segmented_button` del tabview para mostrar/ocultar la pestaña según modo.
   Imagen y Vídeo → 4 tabs; Audio → 3 tabs (sin Tags).

5. **fix Gemini en "Sugerir estilos"** (`tools_creative.py`): usaba `generar()`
   (stateful con historial) que con Gemini contaminaba el contexto.
   Ahora usa `generar_batch()` (stateless). Parser mejorado: soporta CSV y
   bullet-list (`* Estilo`, `- Estilo`) que algunos LLMs devuelven.

6. **feat: "✨ Sugerir" en pestaña Tags** (`tools_creative._cmd_sugerir_tags`,
   `ui_builders.py`): el LLM analiza la idea y añade 3-5 tags técnicos del
   catálogo directamente al campo idea. Usa `generar_batch()`.

7. **feat: "🛡 Sugerir" en pestaña Negativos** (`tools_creative._cmd_sugerir_negative_tab`,
   `ui_builders.py`): genera el negative óptimo con el LLM e inserta el resultado
   en `txt_negative`, llamando después a `_rebuild_negative_text()` para
   combinarlo con los presets activos. Diferente a `_cmd_negative_optimo` que
   actualizaba el output principal o copiaba al portapapeles.

---

## ✅ Sesión 22 — Tags bilingüe+tooltips, fix LoRA multi-término, modelos nuevos

1. **Tab 🏷️ Tags — bilingüe con tooltips** (`config.py`, `modules/ui_builders.py`):
   los 83 tags del picker pasan de inglés puro a tuplas `(nombre_es, val_en, descripción)`.
   Los botones muestran el nombre en **español**, insertan el **término inglés** en
   `txt_idea` al hacer clic, y al pasar el ratón aparece un `CTkToolTip` con el término
   EN + descripción de una línea de qué hace ese tag visualmente.

2. **fix(lora): triggers multi-término con comas** (`modules/prompts_inyeccion.py`):
   antes, un trigger como `"Nyra, Amber Eyes, Undercut"` producía
   `"Nyra, Amber Eyes, Undercut style"` ("`style`" colgado del último término).
   Ahora la lógica aplana: un trigger de **1 sola palabra** → `"palabra style"`;
   un trigger con **comas** → se separa en términos individuales sin "`style`".
   Resultado con 2 LoRAs: `"lmnlhrr style, Nyra, Amber Eyes, Undercut"` (formato
   SD estándar, que el LLM maneja correctamente).

3. **fix(lora): safety-net `_garantizar_lora_trigger`** (`modules/workers_ia.py`):
   el regex de limpieza de duplicados usaba `trigger` completo como palabra, lo que
   fallaba si el trigger contenía comas. Ahora extrae `trigger_key` (primer término
   antes de la primera coma) para la búsqueda/limpieza regex. La inserción de
   fallback también distingue: multi-término → inserta `trigger, `; una palabra →
   inserta `trigger style, `.

4. **Modelos nuevos** (commits sesión 21–22): Wan 2.2, Wan2.5 Image, Sora2 Image,
   Seedream 4.5/4.0, Kling O1 Image, Qwen-Image, Illustrious XL V3.5-vpred y
   V3.6, MiaoMiao Harem V2.0, eliminados GhostMix / Hassaku XL / todos NiwaStyle.

5. **Biblioteca** (`data/biblioteca_ejemplos.json`, `modules/data_mgmt.py`):
   normalización de nombres de plataforma; pre-filtrado por modo al abrir.
   Añadidos **8 ejemplos Seedance 2.0** y **9 ejemplos GPT Image 2/1.5**.

6. **UI varios**: presets negativos en 2 filas, icono Vars → gauge, modos batch
   más claros, menú Plantillas ordenado alfabéticamente, enfocar `txt_idea` al
   arrancar, fix KeyError en specs sin `prompt_formula`/`prompt_ejemplo`.

---

## ✅ Sesión 21 — Avatar (fondos/rotación/anti-zoom), filtro de modelos vigentes y auditoría FLUX

1. **Avatar — rotación de fondos** (`avatar_config.py`, `avatar_prompts.py`,
   `avatar_ui.py`): checkbox **"Variar fondos"** (por defecto ON) que reparte
   4 fondos neutros por índice (`fondo_para_indice`, `i % n`) → ~6 por fondo y
   **decorrelacionados de la pose** (guía SeaArt: el LoRA absorbe un fondo único).
2. **Avatar — modo edición (img2img) reforzado para ángulos**: las tomas que
   rotan (3/4, perfiles, espalda, over-shoulder → `requiere_rotacion`) lideran
   con "Rotate the subject to a NEW viewpoint…" + negative anti-frontal
   (`AVATAR_NEGATIVE_EDIT_ROTACION`). Hallazgo: en modelos NO de edición
   (Z-Image, Flux/Mimic) la referencia bloquea el frontal igual → para ángulos,
   **txt2img**; edición real solo en MAI/Nano Banana/Reve/Kontext.
3. **Avatar — anti-zoom en cuerpo entero** (`AVATAR_NEGATIVE_ANTIZOOM_CUERPO`):
   simétrico al recorte de los primeros planos; las tomas full/cowboy/sentada/
   acción niegan `close-up, headshot, bust…` para empujar al modelo a alejarse.
4. **Filtro de modelos VIGENTES** (`config.py`): solo se muestran los modelos
   de imagen con `"vigente": true` en su spec. `GRUPOS_IMAGEN` sigue siendo la
   lista maestra; `MODELOS_IMAGEN_FLAT` = filtrado (helper `es_modelo_imagen_vigente`,
   `MODELOS_IMAGEN_FLAT_TODOS` conserva el set completo). Oculta ~57 legacy
   no-Flux **sin borrarlos** (decisión del usuario). Vídeo/audio/plataformas:
   pendiente.
5. **Auditoría FLUX completa** (`model_specs_imagen.json`): **17 modelos**
   dados de alta/reactivados con specs reales de SeaArt (base Flux.1 D →
   `has_negative:false`, lenguaje natural, sampler/steps/CFG del panel). Incluye
   Midjourney Mimic Neo, CyberRealistic, Real Vision, Disney Pixar, Nai3, etc.
   Todos en el estilo `natural_flux` de `PROMPT_TEMPLATES`.
6. **Orden alfabético case-insensitive** en todos los grupos de imagen
   (`GRUPOS_IMAGEN = [(cab, sorted(ms, key=str.lower)) …]`) — los nombres en
   minúscula (lyh_anime_Flux) ya no caen al final. **Preferencia del usuario.**
7. **`nota: null` tolerado**: algunos modelos no tienen rating; se maneja con
   `.get('nota') or …` en `ui_events`, `dashboard` y `prompts_inyeccion`
   (antes `float(None)` rompía el orden y mostraba "None").
8. **Toggle "Estilo" para FLUX** (`config.ESTILOS_POR_FAMILIA["flux"]` +
   `detectar_familia` + `_MODELOS_FLUX`): la familia FLUX ya muestra el combo
   Estilo (Auto/Photoreal/Anime/Creative/Fantasy/SciFi) como Z-Image/GPT/Nano.
   La selección se inyecta como hint en el prompt vía `_inyectar_estilo_flux`
   (rama `is_natural` de `prompts_inyeccion`). Detección incluye Mimic Neo (sin
   'flux' en el nombre) por pertenencia al grupo. Familias con estilos: **3 → 4**.
   También: los 17 Flux entran en el template `natural_flux` de `PROMPT_TEMPLATES`.

9. **Desplegable buscador+scroll** (`modules/searchable_dropdown.py`): el
   `CTkComboBox` no tiene scroll y con 35+ modelos tapaba la pantalla.
   `attach_searchable_dropdown()` sustituye el dropdown por un popup (Toplevel
   plano + `grab_set` para cerrar al clic fuera, SIN tocar el root) con caja de
   búsqueda y lista scrollable. Enganchado a los combos de **imagen, vídeo y
   audio**. Nombres largos con ellipsis; valor real al seleccionar.
10. **Fix "Sugerir estilos" en audio** (`tools_creative.py`): estaba bloqueado
    a "solo imagen y vídeo" por descuido; audio sí tiene `ESTILOS_AUDIO`. Ahora
    funciona en los 3 modos.

Tests **561 → 592** (avatar + config vigentes/orden/nota + estilo flux + searchable dropdown).

---

## ✅ Sesión 20 — limpieza, refactor, auditoría de headers, Avatar y Skills

1. **`.gitignore`**: la carpeta de integración del Avatar (ya incorporada
   en `modules/avatar_*.py`) se ignora en lugar de aparecer como untracked.
2. **Aviso Avatar**: el export deja claro en `prompts_todos.txt` y
   `prompts_edicion_todos.txt` que el modo edición (img2img) y el
   text-to-image son **alternativos, no acumulativos** (error real del
   round 12: el usuario pegó ambos juntos).
3. **HANDOFF reescrito**: este resumen vivo + histórico archivado en
   `docs/handoff-historico.md` (antes 2822 líneas con datos contradictorios).
4. **Red anti-bugs `[silent]`** (`logging_utils.py`): `GPROMPT_DEBUG=1`
   re-lanza las excepciones que se tragarían (~336 `logger.debug("[silent]")`
   inline + los 3 helpers). Lo hace un `ReRaiseSilentFilter` en los handlers
   (re-lanza `sys.exc_info()` vivo, cero cambios en los 336 call sites) +
   `install_strict_silent_guard()` enganchado en `main.py`. +24 tests.
5. **Partición de `app.py`** (3172 → 2670, −16%): el bloque de preview
   Pollinations (boceto rápido + grid + ventana de preview) → nuevo servicio
   `modules/preview_pollinations.py` (`self.preview`). +4 tests de cableado.
   ⚠️ El camino GUI/red no es auto-testeable; conviene un click-test manual
   de **🖼 Preview** y **👁 Grid Pollinations** antes de distribuir.
6. **Code-signing** (`build.py` + `BUILD.md`): firma Authenticode opcional
   del `.exe` y del instalador vía `GPROMPT_SIGN_CERT`/`_PASSWORD` o
   `GPROMPT_SIGN_THUMBPRINT`. No-op si no hay cert; nunca aborta el build.
7. **Contenido de apoyo al día** (se había quedado atrás frente a las
   features): tutorial **26 → 42 pasos** (sección "Funciones avanzadas"),
   **+5 atajos** (Ctrl+Shift+R/O/D/B/M = Refinar/Optimizador/Dashboard/
   Storyboard/Coste) + en la ayuda, glosario (Modo educativo) **43 → 56**.
   Bug del modal **"Acerca de"** corregido (volcaba el dict `AUTHOR` entero).
8. **Auditoría de los 8 headers** (lectura de código). 2 huecos 🔴 reales
   arreglados: `paletas` faltaban en backup/restore (pérdida de datos al
   restaurar) y **Ctrl+F** abría una "búsqueda global" duplicada e inferior
   (ahora abre la buena). 🟡: caché en Auto-mejora (+ botón Regenerar), copy
   del Coste actualizado a "por modelo", renombrados los 2 gestores de snippets
   ("Tags reutilizables" vs "Auto-expansión") para no colisionar.
9. **Avatar** — dos mejoras: (a) **fix de encuadre**: el encuadre lidera el
   prompt (antes la descripción con ropa de cuerpo iba primero y cara/busto
   salían de cuerpo entero); cara/busto piden recorte explícito. (b) dataset
   **16 → 24 ángulos** (4 expresiones + 4 poses neutrales, grupo "poses").
10. **Features inspiradas en YouMind ("Skills")**: `Adaptar al modelo activo`
    como **botón de un clic** (🛠 Herramientas, antes solo en macros);
    **import/export de macros** a `.json` (Skills portables, helpers
    `macro_valida`/`parsear_macros_importadas`); `Optimizar (1 pasada)`
    headless encadenable en macros.

> Nota: descubrimos que **Macros ya ERA** el sistema de "recetas/Skills" y
> **Proyectos** el "Board" — por eso se potenció Macros en vez de duplicar.

---

## 🚧 Pendiente

### 🔴 ALTA
- **Vídeo SeaArt — quedan ~8 motores externos**: Wan 2.7, Vidu Q3 Pro/Reference,
  Kling 3.0 turbo, Kling O1, Grok Imagine (+1.5), StarDream 2.0 Fast, Happy Horse,
  Hailuo 2.3 fast. Panel a panel; remake/edición/referencia se descartan.
- **Auditoría specs Anime/Ilustración**: 6/17 vigentes, 11 ocultos sin auditar.
  Requiere pantallazos del panel SeaArt (Illustrious, NoobAI, etc.).
- **Auditoría specs Realismo SD**: 6/15 vigentes, 9 ocultos sin auditar.

### 🟡 MEDIA
- **`FLUX.1-Kontext-dev` (edición)**: modelo añadido, pendiente PROBARLO para
  rotación Avatar desde referencia img2img (debería ir donde Z-Image falla).
- **max_chars empírico** de modelos semi-auditados (Infinity, SD 3.5, Realism,
  NoobAI, T-Ponynai3, Counterfeit, Temporal).
- **Fable 5**: suspendido 12-jun-2026 por Anthropic. Descomentar cuando vuelva:
  precio + `LLM_PROVIDERS["claude"]["modelos"]`; el guard de `temperature` ya existe.
- **Revisar precios** de `PRECIOS_USD_1M` / `PRECIOS_USD_1M_MODELO`.
- **Particiones restantes**: `tools_analysis.py` (2187), `tools_creative.py` (1902),
  `ui_builders.py` (1928) — extraer módulos cuando haya motivo funcional.
- **QoL**: overlay de ratio sobre imagen de referencia; variante SD/Comfy del
  storyboard de imagen.

### 🟢 BAJA
- Code-signing real: conseguir el certificado (infraestructura ya lista).
- Verificar installer end-to-end en VM limpia.
- Performance: semáforo de workers, virtual scrolling en historial/favoritos.
- Auditar `[silent]` que oculten bugs: arrancar con `GPROMPT_DEBUG=1`.
- Features ambiciosos: export PDF, plugin system, API REST.

---

## 🔁 Cómo continuar (sesión nueva)

```powershell
# Baseline
python -c "import app; print('OK')"          # → OK
python -m pytest tests -q                     # → 719 passed / 0 failing ✅
ruff check .                                  # → All checks passed

# Arrancar (keys del usuario: deepseek, gemini, openrouter; sin Anthropic)
python main.py
# Depurar con la red anti-bugs activa (re-lanza excepciones [silent]):
$env:GPROMPT_DEBUG = "1"; python main.py

# Build
python build.py --installer ; python build.py --onefile
# → copiar los 3 a ~/OneDrive/Desktop/GPromptStudio-Distribuible/
```

### Patrón de trabajo establecido
- Análisis honesto en tabla antes de tocar; priorización 🔴/🟡/🟢.
- Preguntar antes de empezar bloques grandes; 1 commit por bloque coherente.
- Smoke test (`python -c "import app; print('OK')"`) + `pytest` tras cada cambio.
- Pre-commit hooks pueden re-formatear y requerir `git add` + recommit.

### Patrón Mixin → Servicio (composición)
Para extraer lógica de `app.py` o de un mixin a un módulo aislado:
1. Crear `XxxService(app)` en `modules/`; los métodos usan `self.app.<attr>`.
2. Convertir patrones widget-aware: `GPromptWindow(self)` → `GPromptWindow(self.app)`,
   `.transient(self)` → `.transient(self.app)`, `hasattr(self, …)` → `hasattr(self.app, …)`.
3. Instanciar en `ArquitectoApp.__init__` (`self.xxx = XxxService(self)`).
4. Migrar call sites a `self.xxx.metodo()`.
5. Añadir el módulo a `hiddenimports` en ambos `*.spec`.
6. Tests de cableado contra un `SimpleNamespace` como app falsa.

Ejemplo reciente y limpio: `modules/preview_pollinations.py` (sesión 20).
