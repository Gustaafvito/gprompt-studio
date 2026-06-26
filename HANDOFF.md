# 🧾 Handoff — G-Prompt Studio

Documento vivo para retomar el proyecto en una sesión nueva. Se mantiene
**conciso y al día**: estado actual + pendientes vivos. El detalle
round-a-round de las sesiones 6-19 está archivado en
[`docs/handoff-historico.md`](docs/handoff-historico.md) (no se actualiza).

Actualizado al cierre de la **sesión 33**.

---

## 📍 Qué es

**G-Prompt Studio** — app de escritorio (Python + customtkinter) para
generar prompts de IA generativa (imagen, vídeo, audio) usando LLMs como
motores (DeepSeek, Gemini, OpenRouter, Claude…). Incluye import/export JSON
para Veo/Sora/Kling, optimizador de prompts en bucle, coste de sesión,
módulo Avatar para datasets LoRA, empaquetado `.exe` + installer, y CI.

Estructura del código: ver [`docs/ESTRUCTURA.md`](docs/ESTRUCTURA.md).
Empaquetado: ver [`docs/BUILD.md`](docs/BUILD.md). Añadir modelos: ver
[`docs/AGREGAR_MODELO.md`](docs/AGREGAR_MODELO.md).

---

## 📊 Estado actual

| Métrica | Valor |
|---|---|
| Tests | **784 passed / 0 failing** (`python -m pytest tests -q`) ✅ |
| Idioma UI | **Bilingüe ES/EN — MERGEADO a `main`** (~1290 traducciones). UI estática+dinámica + config-driven (pestañas, Tags, negativos, ratio `Libre`, combo Estilo vía mapeo display↔clave, **centinelas `— Sin X —`** en 34 sitios) + ideas del LLM en idioma de UI + 177 descripciones de modelo (`best_for_en`, helper `config.best_for_display`) + **Brain labels** + **detección idioma del SO en 1er arranque** (`idioma_inicial`) + **Auto-translate OFF por defecto en EN** + setups por defecto renombrados a EN. Toggle UI→Idioma con auto-reinicio. ⚠️ **PENDIENTE (ver Pendiente i18n)**: `tr()` solo hace ES→EN, así que en modo ES los datos nativos en inglés (estilos tipo `Photoreal/Cyberpunk`, nombres de modelos/LoRAs, setups) se ven en inglés → "mezcla". Decisión abierta: traducción bidireccional (EN→ES) vs dejar datos-convención fijos. |
| Build definitivo | `python build_release.py` (export limpio de HEAD + build + copia al distribuible) |
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
| Modelos vídeo | **77 totales**, por familia, alfabéticas (Grok · Hailuo · Happy Horse · Kling · Nano Banana · Otros · PixVerse · SeaArt Oficiales · Seedance · StarDream · Vidu · Wan). Sesión 31: +4 (StarDream 2.0 Mini, Seedance 2.0 Mini, SeaArt Pony 1.1, Happy Horse 1.1, por panel). Reference (Vidu Drama/Ad, Drama/Ad) descartados por convención |
| Modelos audio | **11** (Suno ×4, Udio ×2, Minimax ×2, MusicGo, Mureka V9⚠️prov.). SeaArt audio: Minimax Music 2.5 + Mureka V9 |
| Plataforma ComfyUI | **Operativa** (sesión 28+31): auto-discovery recursivo (checkpoints+diffusion_models+unet, clasifica imagen/vídeo/audio), detección Turbo por tokens. **Specs sintéticas por familia** — imagen `comfy_image_specs` (flux/z_image/qwen/ideogram/pony/illustrious/sd15/sdxl) **y vídeo `comfy_video_specs`** (ltx/wan/svd/hunyuan/cogvideo/mochi), ambas bilingües (`best_for_en` + `prompt_formula/ejemplo`). Pendiente: estilos por familia + wiring en caliente del dropdown |
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

## ✅ Sesión 33 — Plataforma Dola + i18n D (LLM) + E (Style guide bilingüe)

Tres bloques, todos en `main` (780 → 784 verdes, ruff limpio):

1. **Plataforma Dola** (`1a483b6`): dola.com (afiliado Dreamina/ByteDance) añadido como
   plataforma **natural** de imagen y vídeo. Imagen: modelo "Dola" (hasta 10 refs,
   ratios 1:1/2:3/3:4/4:3/9:16/16:9). Vídeo: motores Seedance 2.0 Fast (existente) +
   **Seedance 1.0 Fast** (nuevo, Dreamina), 5s/10s. Specs bilingües. PLATAFORMAS_*,
   MODELOS_POR_PLATAFORMA_*, MOTORES_VIDEO, MOTOR_DEFAULT, TOKEN_LIMITS. +3 tests.
   (Su política de privacidad/ToS NO se embebe — es un generador de prompts.)
2. **i18n D — salida del LLM** (`6daabb2`): Auto-improve y Analysis of patterns
   inyectan directiva de idioma (`get_idioma()`), antes siempre devolvían español.
3. **i18n E — Style guide bilingüe** (`ae56526`): `GUIA_ESTILOS.en.md` (391 estilos,
   mismos nombres-clave, descripciones+ejemplos+grupos en inglés) + `cargar_guia()`
   por idioma + título de card vía `tr()`. Empaquetado en ambos `.spec`.

Catálogo vídeo **76 → 77** (Seedance 1.0 Fast). Plataformas imagen +1 (Dola), vídeo +1.

---

## ✅ Sesión 32 — i18n: limpieza de remanentes ES en modo EN (enfoque b)

QA del usuario en modo EN destapó "mezcla" de idiomas. Decidido enfoque **(b)** y
limpiados los remanentes ES visibles (3 commits, 776 → 780 verdes, ruff limpio):

1. **Footer de estilos + best_for de audio** (`711fad1`): los checkboxes de estilo
   usaban `text=nombre` crudo → siempre español; ahora `text=tr(nombre)` (clave de la
   var sin cambios). +25 traducciones de estilos. Los 11 modelos de audio sin
   `best_for_en` → añadido (la barra de info salía en español en EN).
2. **Combos audio + destinos** (`b6f39c5`): Emoción/Voz/Idioma (28 valores +
   centinelas) y Destination con el patrón centinela `tr()` en values + comparaciones.
   DESTINOS es keyed (REGLAS_POR_DESTINO) → `_inyectar_destino` mapea de vuelta
   `{tr(d): d}`. +43 traducciones. Comparaciones actualizadas en prompts_inyeccion,
   ui_events, data_mgmt.
3. Tests guardián anti-regresión (estilos/combos sin acentos en EN + reverse-map).

Pendiente (ver "Pendiente i18n"): **D** salida del LLM (auto-mejora/patrones) y **E**
contenido del Style guide (391 estilos → `.en.json`).

---

## ✅ Sesión 31 — ComfyUI vídeo (LTX/Wan/SVD) + 4 modelos SeaArt nuevos

Dos bloques, ambos mergeados a `main`. Tests **760 → 773 verdes**, ruff limpio.

**1. 4 modelos de vídeo SeaArt nuevos** (`f2c8551`), auditados uno a uno con panel
real (sin inventar defaults): **StarDream 2.0 Mini** (máx 720p, 5000 chars),
**Seedance 2.0 Mini** (máx 720p, 5000 chars, sin audio aunque el padre sí),
**SeaArt Pony 1.1** (9 refs, 720p/1080p, 2500 chars) y **Happy Horse 1.1** (9 refs,
720p/1080p, 2500 chars; `has_negative` asumido false, panel cortado). Cada uno con
`best_for`+`best_for_en`, añadidos a sus familias en `GRUPOS_VIDEO`. Catálogo vídeo
**72 → 76**. Los 4 modelos "Reference" (Vidu Drama/Ad, Drama/Ad) descartados por
convención (referencia/remake/edición).

**2. Specs de VÍDEO ComfyUI por familia** (`acd6e8c`): el motor de vídeo trataba
ComfyUI como tag-based (`"sd"`) e ignoraba el modelo → LTX/Wan/SVD salían mal.
Nuevo `comfy_video_specs()` + fallback en `get_model_specs` (curado primero). Cada
familia con su guía real (investigada en fuentes oficiales + docs ComfyUI):
- **LTX-2.3**: párrafo cinematográfico en presente, audio nativo, `has_negative`,
  CFG bajo, ~1500 chars. Estructura encuadre→escena→acción→cámara(estado final)→audio.
- **Wan 2.2**: prompts cortos orientados a acción + lenguaje de cámara, negative, sin audio.
- **SVD**: image-to-video puro (ignora el texto; motion_bucket_id). + Hunyuan/CogVideo/Mochi.

Además, **imagen bilingüe**: `best_for_en` + `prompt_formula`/`prompt_ejemplo` en las
8 familias sintéticas de `comfy_image_specs`, y `best_for_en` añadido a 3 entradas
curadas locales que no lo tenían (flux-2-klein-base-4b, zImageBase_base, qwen edit).
Patrón clave: por nombre de familia (robusto a renombrados), NO catálogo exacto.

**3. Ratios en orden canónico** (`141185f`): los arrays `ratios` de los 161 modelos
(imagen+vídeo) y de `comfy_video_specs` reordenados para seguir RATIOS_IMAGEN/
RATIOS_VIDEO (canónicos primero, extras lexicográficos), consistentes entre modelos.
Test guardián `TestRatiosOrdenCanonico`. Además, eliminada una entrada fantasma
`ltx-2.3-22b-dev-fp8` que estaba mal en `model_specs_imagen.json` (LTX es vídeo).

---

## ✅ Sesión 30 — i18n EN-mode: ~110 strings restantes envueltos con tr()

### Cambios (1 commit `e41b79a`)

**Archivos modificados**: `modules/i18n.py` (+110 entradas), `modules/tools_analysis.py`,
`modules/dialogs.py`, `modules/ui_events.py`, `modules/ui_builders.py`,
`modules/workers_ia.py`, `modules/searchable_dropdown.py`, `persistence.py`, `app.py`.

**Qué se traduce ahora**:
- **Analytics** (`tools_analysis.py`): subtítulo "Análisis de tus últimas N ideas",
  estado auto-mejora, todas las cabeceras de sección (Colecciones, Top modelos,
  Top plataformas, Ratios más usados, Top estilos, Longitud, Prompts por mes, Seeds),
  etiquetas de las 9 tarjetas de colecciones, cabeceras CSV, vacío de seeds.
- **Coste de sesión**: cabeceras de tabla (Proveedor/Llamadas/Tokens entrada/
  Tokens salida/Coste/Coste/día) y del histórico.
- **Scoring**: etiquetas de calidad (🏆 Excelente/✨ Bueno/🟡 Mejorable/⚠️ Necesita trabajo).
- **Optimizador**: "Original"/"Iteración N", mensajes de finalización (detenido/
  alcanzado/máximo), etiqueta diff "Optimizada (N/100)".
- **Pistas contextuales de modelo**: Turbo/Natural/costoso/lento.
- **Badges de modelo**: 🌐 Natural/⚡ Turbo/🏷 Tags/🔴 Neg ✓/🚫 Sin neg.
- **Ratio tooltips**: Cuadrado/Vertical/Horizontal/Foto vertical/Foto horizontal.
- **Familias de modelos** (`searchable_dropdown.py`): los separadores `── X ──`
  se traducen al renderizar vía `tr(v)` (no en config.py, que es import-time).
- **API keys** (`dialogs.py`): estado ✅/⚠️/⚪, placeholders, confirmación borrado.
- **About**: descripción en español → bilingüe.
- **Persistence** (`persistence.py`): centinelas "— Sin personaje/LoRA/plantilla —"
  ahora retornan `tr(...)` → combo siempre muestra el texto en el idioma activo.
- **Workers IA**: mensajes "Refinamiento listo"/"Completado"/modo visión.
- **Plantillas** (`app.py`): "Sin resultados para X"/"Sin plantillas en Y".

Tests: **760/760 ✅** · Ruff: limpio.

---

## ✅ Sesión 29 — Auditoría de seguridad, idioma y limpieza estructural

### Seguridad (6 fixes)
1. **Inyección AppleScript macOS** (`app.py` ~L1119): sanitizado `"` y `\`
   antes de interpolar `mensaje`/`titulo` en `-e` de osascript.
2. **Log Gemini reducido** (`api_clients.py`): eliminados los primeros 6 +
   últimos 4 chars de la key del log → solo `[presente]`.

Vulnerabilidades detectadas pero **pendientes de decisión** (no se tocan
en caliente):
- 🔴 CRÍTICA: `.env` con 3 keys reales sincronizado a OneDrive → **ROTAR YA**.
- 🔴 ALTA: clave AES fallback hardcodeada `GPromptStudio_v1_key_backup_2024`
  en `api_clients.py` L902 → migrar fallback al keyring del SO.
- 🔴 ALTA: padding AES con espacios (no PKCS#7) en `api_clients.py` L918 →
  migrar a AES-GCM.
- 🟡 MEDIA: `comfyui_path` va directo a `rglob()` sin validar (`config.py`).
- 🟡 MEDIA: JSON del LLM no validado contra `ADN_SCHEMA` antes de usarlo.

### Idioma (8 correcciones)
- `i18n.py`: `¿Sobreescribir` → `¿Sobrescribir`; `record on video` → `record as video`
- `windows.py` (×2): llamadas `tr("¿Sobreescribir…")` alineadas con clave corregida
- `tools_creative.py`: `¿Sobreescribir?` → `¿Sobrescribir?`
- `glosario.json`: `Marcalos` → `Márcalos`; `resol.` → `resolución`
- `tutorial.json`: `compara aesthetics` → `compara estéticas`; `Mucho éxito!` → `¡Mucho éxito!`

### i18n — strings sin `tr()` envueltos (98 traducciones nuevas)
- **`atajos_ayuda.py`**: 7 categorías + 29 descripciones de acciones + contador
  `"{N} de {M} atajos"` — la ventana de atajos (Ctrl+?) ahora es bilingüe.
- **`dashboard.py`**: tiempo relativo (singular/plural día/hora/minuto), estado
  LLM (`Conectado`/`Sin key`), 5 avisos, 20 logros × nombre+descripción.
- **`i18n.py`**: +98 entradas (dashboard + atajos + estado + logros).

### Limpieza estructural
- **`config/` eliminada**: `plantillas_default.json` movido a `data/` (donde
  están todos los demás JSON). Referencias actualizadas en `app.py` L1194 y
  ambos `.spec`. La carpeta `config/` ya no existe.
- **`.gitignore`**: añadidos `.ruff_cache/` y `.claudeignore`.
- **`modules/__init__.py`**: eliminados comentarios internos de desarrollo.
- **`README.md`**: conteos actualizados (93+ imagen, 72 vídeo, 11 audio,
  760 tests, 29 atajos), árbol y lista de atajos corregidos.
- **`docs/ESTRUCTURA.md`**: árbol completo con las 40 módulos actuales,
  líneas reales, sección de arquitectura actualizada a composición de servicios,
  tests 48 → 760.

Tests: **760/760 ✅** · Ruff: limpio.

---

## ✅ Sesión 28 — Plataforma ComfyUI operativa (3 fixes/feat)

Rama **`feat/comfyui-platform`**. El usuario aportó su inventario real (carpetas
`checkpoints` + `diffusion_models` con imagen/vídeo/audio mezclados + subcarpeta
`FLUX2/`). Tres problemas reales que ese inventario destapó:

1. **Detección Turbo robusta** (`87daa25`): `_MODELOS_TURBO` solo casaba 4 nombres
   exactos de catálogo → los ficheros locales reales (`z_image_turbo_bf16`,
   `flux1-schnell`, `dreamshaperXL_lightning`…) NUNCA activaban la regla "sin
   pesos / sin negative". Ahora por tokens case-insensitive (`COMFY_TURBO_TOKENS`
   centralizado en config; `prompt_logic.es_comfyui_turbo` lo reutiliza). +8 tests.

2. **Auto-discovery completo** (`1df9141`): el escaneo solo miraba
   `models/checkpoints` y trataba `diffusion_models` como vídeo → FLUX.2 Klein,
   Z-Image, Qwen Edit, ACE-Step (que viven en `diffusion_models`) eran invisibles;
   las subcarpetas también. Nuevo: `clasificar_modelo_comfy()` (imagen/video/audio
   por tokens) + `_escanear_comfy_root()` (recorre checkpoints+diffusion_models+unet
   recursivo, dedup, orden case-insensitive), compartido por el escáner de Ajustes
   y el dropdown. El dropdown lee `comfyui_path` también de preferencias. +11 tests.

3. **Specs sintéticas por familia** (`4dfde6c`): los modelos ComfyUI no están en el
   JSON curado → `get_image_model_specs` devolvía None → la inyección no añadía nada
   específico. Ahora `detectar_familia_comfy()` + `comfy_image_specs()` generan specs
   por familia (is_natural, has_negative, sampler sugerido, best_for, trigger_words
   de Pony; variantes fast fuerzan has_negative=False; max_chars por tipo). El curado
   siempre tiene prioridad. +13 tests.

Resultado verificado end-to-end: FLUX.2 Klein/Z-Image/Qwen → natural sin negative;
Z-Image Turbo → natural + turbo; Juggernaut/RealVis/512-inpaint → tags con negative.
Tests **729 → 760 verdes**, ruff limpio. Decisión de diseño: por patrón de nombre
(robusto a renombrados y modelos futuros), NO catálogo exacto como SeaArt.

---

## ✅ Sesión 27 (cont.) — Bilingüe COMPLETO: Fase B residual + Fase C

Continuación en `feat/i18n-fase-b` hasta cerrar el bilingüe entero (~1236 entradas).

5. **set_estado** (`1a0de9a` literales + `3ee66ea`/`e0f5147` f-strings): los ~470
   mensajes de la barra de estado. Literales con `tr()`; f-strings convertidas con
   un **motor AST** a `tr("...{0}...").format(expr)` (placeholders **posicionales**
   para evitar colisiones `self`/`cls`; format-spec `:.2f` y conversion `!r`
   preservados; offsets en **bytes UTF-8**). set_estado 100% bilingüe.
6. **messagebox** (`e0f5147`): títulos y mensajes de los diálogos (incl. multilínea
   de backup/trigger LoRA).
7. **Dinámicos `configure(text=)`/`title()`/`show_toast`** (`41b13fb`, `a339844`):
   labels y títulos dinámicos. **Bug encontrado**: `tools_workflow.py` tenía un
   **BOM** que rompía `ast.parse` → el conversor saltaba el archivo (22 set_estado
   sin tocar). BOM eliminado + sus messagebox (`4931994`).
8. **Fase C** (`216a87c`): `tutorial.py`/`glosario.py` eligen `data/<x>.en.json`
   si idioma=='en' (fallback a ES). Creados `tutorial.en.json` (42 pasos) y
   `glosario.en.json` (56 entradas) traducidos; `data/` ya se empaqueta en ambos `.spec`.

**Único residual** (correcto dejarlo): f-strings sin texto traducible — solo icono
+ valor dinámico (`f"❌ {error}"`, `f"🎭 {nombre}"`). No hay nada que traducir.

Patrón de trabajo: scripts de wrapping (solo literales puros) + validador que cruza
las claves `tr()` extraídas del código con el diccionario → **0 faltantes** antes de
cada inyección. Tests **729 verdes** y ruff limpio en los ~12 commits.

---

## ✅ Sesión 27 — Bilingüe Fase B (núcleo): 661 textos traducidos

Rama **`feat/i18n-fase-b`** (4 commits, sin mergear a `main` aún). Enfoque
semi-automático acordado: script que envuelve **solo literales puros** (ignora
f-strings/variables/numéricos por construcción) + validador que cruza claves
canónicas extraídas del código con el diccionario (0 faltantes garantizado).

1. **Wrapping `text="..."`** (`6ed7358`): 632 literales envueltos con `tr()` en
   27 archivos (496 únicas). Maneja concatenación implícita `text="a" "b"` como
   grupo. Import de `tr` añadido a nivel de módulo donde faltaba.
2. **504 traducciones EN** (`92f2d1d`): `TRADUCCIONES` rellenado una a una
   (emojis, placeholders `{var}`, `\n` y espacios preservados).
3. **Menús + barra de modo** (`676cda0`): 8 cabeceras del header + ~48 items
   (tuplas `(label, cmd)`) y la barra Imagen/Vídeo/Audio (`CTkSegmentedButton`).
   Los 3 mapas display↔lógico (`_on_segmento_modo`, `ui_events` mapa_inv,
   `tutorial` mapa_label) pasan por `tr()` — consistentes porque el idioma se
   fija antes de construir la UI. +58 traducciones.
4. **Placeholders + títulos** (`ec42232`): 37 `placeholder_text=` + ~80 títulos
   `.title("...")`. 2 títulos con concatenación (`Preview`/`Análisis patrones` +
   sufijo caché) a mano. +99 traducciones. **Total 661, 0 faltantes.**

En modo ES el comportamiento es **idéntico** (`tr()` devuelve el español si no
hay traducción). Tests **729 verdes**, ruff limpio en los 4 commits.
**PENDIENTE Fase B residual**: textos dinámicos (f-strings, `set_estado`,
mensajes de error en runtime). **Fase C**: tutorial.json/glosario.json/ayuda EN.

---

## ✅ Sesión 26 — Limpieza, build limpio, bilingüe ES/EN (Fase A)

1. **Limpieza de carpeta** (`b8e97f7`): borrado cruft local (~730 MB:
   dist/build/__pycache__/.pytest_cache/.ruff_cache, gitignored). Docs de
   desarrollo (AGREGAR_MODELO/BUILD/ESTRUCTURA) movidos a `docs/`; README,
   HANDOFF y GUIA_ESTILOS se quedan en raíz (el `.spec` empaqueta los 2 últimos).

2. **Build limpio/reproducible** (`83f0ff5`): `build_release.py` exporta solo lo
   trackeado en git (HEAD) a `../GPromptStudio-build-clean/`, buildea ahí
   (onedir+installer+onefile) y copia los 3 al distribuible. Doc en docs/BUILD.md.

3. **Bilingüe ES/EN — Fase A** (`637e9a8`): infraestructura i18n.
   - `modules/i18n.py`: `tr("texto es")` → EN si idioma=="en" y está en
     TRADUCCIONES, si no fallback al español. `set_idioma`/`get_idioma`.
   - `app.py`: carga pref `idioma` y fija el idioma ANTES del build de la UI.
   - Toggle en menú **UI → 🌐 Idioma (EN/ES)** (`dialogs._cmd_toggle_idioma`),
     guarda pref y avisa "reinicia para aplicar" (cambio NO en caliente).
   - 10 etiquetas de ejemplo envueltas con `tr()` (barras imagen/vídeo).
   - **PENDIENTE Fase B**: envolver los ~760 textos restantes con `tr(...)` +
     rellenar TRADUCCIONES. **Fase C**: tutorial.json/glosario.json/ayuda en EN.

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

### 🌐 i18n — mezcla de idiomas — ENFOQUE (b) EN MARCHA (sesión 32)
**Decisión tomada con el usuario: (b) datos-convención fijos** — estilos-keyword
(`Cyberpunk`, `Anime`), nombres de modelo/LoRA/setup quedan en inglés en ambos modos
(traducirlos ensuciaría los prompts); solo se **limpian los remanentes ES** que se
cuelan en modo EN. `tr()` sigue siendo unidireccional ES→EN.

**Ya limpiado (sesión 32):**
- Footer de estilos (`text=tr(nombre)`; +25 traducciones).
- `best_for` de los 11 modelos de audio (`best_for_en`).
- Combos de audio Emoción/Voz/Idioma (+ centinelas) y combo Destination (con
  reverse-map `{tr(d): d}` para las reglas keyed). +43 traducciones.
- Test guardián `TestI18nSinRemanentesEspanol` / combos (acentos en EN + reverse-map).

**HECHO (sesión 33):**
- ✅ **D — Salida del LLM** en *Auto-improve* y *Analysis of patterns* (`tools_analysis`):
  inyectan directiva de idioma según `get_idioma()`.
- ✅ **E — Style guide bilingüe**: `GUIA_ESTILOS.en.md` (391 estilos, mismos nombres-clave)
  + `cargar_guia()` por idioma + título de card vía `tr()`.

**PENDIENTE (residual, menor):**
- **Scoring** y **crítica de historial** (`tools_analysis`): mismo patrón que D, sus
  prompts (`construir_peticion_scoring` y otros) aún piden/devuelven español.
- **Nombres de estilo Spanish-native** en el Style guide (p.ej. "Fotografía Realista",
  "Retrato / Portrait") que NO están en `TRADUCCIONES`: el título de card sigue en
  español aunque la descripción esté en inglés. Bajo (b) es aceptable; si se quiere,
  añadir esos nombres a `TRADUCCIONES`.
- **Nota cross-mode:** los valores de combo se persisten traducidos; al cambiar de
  idioma un setup/pref viejo puede no recargar la selección (aceptable, requiere
  reinicio igual).

### 🔴 ALTA
- **Vídeo SeaArt — quedan ~8 motores externos**: Wan 2.7, Vidu Q3 Pro/Reference,
  Kling 3.0 turbo, Kling O1, Grok Imagine (+1.5), StarDream 2.0 Fast, Happy Horse,
  Hailuo 2.3 fast. Panel a panel; remake/edición/referencia se descartan.
- **Auditoría specs Anime/Ilustración**: 6/17 vigentes, 11 ocultos sin auditar.
  Requiere pantallazos del panel SeaArt (Illustrious, NoobAI, etc.).
- **Auditoría specs Realismo SD**: 6/15 vigentes, 9 ocultos sin auditar.

### 🟡 MEDIA
- **ComfyUI — estilos por familia**: `ESTILOS_POR_FAMILIA` no cubre las familias
  ComfyUI, así que el combo "Estilo" no se repuebla para estos modelos. Complemento
  natural a las specs sintéticas de la sesión 28. (Detección ya existe:
  `detectar_familia_comfy`.)
- **ComfyUI — wiring en caliente**: cambiar `comfyui_path` en Ajustes no refresca
  el dropdown sin reiniciar (los grupos se calculan al importar config). Mejorable.
- **ComfyUI — audio**: ACE-Step ya se detecta como audio en el escaneo, pero no hay
  plataforma de audio ComfyUI ni panel → de momento no se usa. Decidir si se integra.
- **ComfyUI — plantilla `mis_modelos_comfy.json`**: la plantilla por defecto podría
  agruparse mejor; el auto-discovery ya cubre el caso de tener `comfyui_path`.
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
python -m pytest tests -q                     # → 784 passed / 0 failing ✅ (sesión 33)
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
