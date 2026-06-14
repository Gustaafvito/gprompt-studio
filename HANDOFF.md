# 🧾 Handoff — G-Prompt Studio

Documento vivo para retomar el proyecto en una sesión nueva. Se mantiene
**conciso y al día**: estado actual + pendientes vivos. El detalle
round-a-round de las sesiones 6-19 está archivado en
[`docs/handoff-historico.md`](docs/handoff-historico.md) (no se actualiza).

Actualizado al cierre de la **sesión 21**.

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
| Tests | **592** ✅ (`python -m pytest tests -q`) |
| Working tree | Limpio |
| Branch | `main` |
| Arquitectura | Composición completa: **1 mixin** (`CoreMixin`) en el MRO, resto son servicios accedidos por `self.<componente>` |
| Lint | Ruff con **F401 + F821** activos (CI 3.10/3.11/3.12) |
| Pre-commit hooks | Activos (line endings, ruff, large files, secrets) |
| Build `.exe` | onedir + onefile + installer (Inno Setup) — al día |
| Code-signing | Opcional vía env vars (`GPROMPT_SIGN_*`), ver BUILD.md |
| Modelos de imagen VISIBLES | **35** vigentes (filtro `vigente:true`); el resto ocultos |
| Familia FLUX | **CERRADA — 25** modelos ✅ (incl. `FLUX.1-Kontext-dev` edición; 3 legacy borrados) |
| Coste API | sesión + histórico + desglose por modelo |

### Archivos más grandes (líneas)

| Archivo | Líneas |
|---|---:|
| `app.py` | 2670 |
| `modules/tools_analysis.py` | 2112 |
| `modules/tools_creative.py` | 1876 |
| `modules/ui_builders.py` | 1831 |
| `modules/core.py` | 1674 |
| `modules/data_mgmt.py` | 1581 |

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
- **Auditoría de specs**: familia **Flux ✅ hecha (17, sesión 21)**; queda
  **Illustrious (10)** — requiere pantallazos del panel SeaArt (input del usuario).
- **Vigentes vídeo/audio/plataformas**: aplicar el filtro `vigente` también a
  vídeo y audio, y ocultar plataformas no usadas (solo imagen hecho en sesión 21).
- ✅ **Flux: líos heredados limpiados (sesión 21)**: borrados `FLUX.1` (schnell),
  `Flux-dev` y `Mix Max Cinematic Realism`. Añadido **`FLUX.1-Kontext-dev`**
  (modelo de EDICIÓN, `max_imagenes_referencia:1`) — pendiente PROBARLO para la
  rotación del avatar desde referencia (debería funcionar donde Z-Image/Flux txt2img no).

### 🟡 MEDIA
- **max_chars empírico** de los 10 modelos semi-auditados (Infinity, SD 3.5,
  Realism, NoobAI, T-Ponynai3, Counterfeit, Temporal) — prompt marcado o
  contador del panel.
- **Fable 5**: vigilar si Anthropic restaura el acceso (suspendido 12-jun-2026).
  Descomentar precio + re-añadir a `LLM_PROVIDERS["claude"]["modelos"]`; el
  guard de `temperature` ya lo cubre.
- **Revisar precios** de `PRECIOS_USD_1M` / `PRECIOS_USD_1M_MODELO`.
- **Particiones restantes**: `app.py` (2670, p.ej. extraer comparador/diff o
  plantillas), `tools_analysis.py` (2112), `tools_creative.py` (1876),
  `ui_builders.py` (1831).
- **QoL**: overlay de ratio sobre imagen de referencia; variante SD/Comfy del
  storyboard de imagen.

### 🟢 BAJA
- Code-signing real: conseguir el certificado (la infraestructura ya está).
- Verificar installer end-to-end en una VM (instalación limpia → arranque →
  desinstalación con borrado de datos).
- Performance: semáforo de workers, virtual scrolling en historial/favoritos
  (solo si se nota lentitud). **Lazy-load JSON descartado**: medido, `import
  config` = 21 ms (231 KB), no compensa el riesgo de volver lazy constantes
  usadas en muchos call sites.
- Auditar los `[silent]` que oculten bugs reales — ahora hay herramienta:
  arrancar con `GPROMPT_DEBUG=1` y reproducir el flujo sospechoso.
- Features ambiciosos: export PDF, plugin system, API REST.

### ✅ Completado en sesión 20 (antes pendiente)
- `adaptar_modelo` como botón de un clic · import/export de macros ·
  `optimizar_1pasada` headless · aviso Avatar prompts alternativos.

---

## 🔁 Cómo continuar (sesión nueva)

```powershell
# Baseline
python -c "import app; print('OK')"          # → OK
python -m pytest tests -q                     # → 592 passed
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
