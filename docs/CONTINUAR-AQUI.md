# CONTINUAR AQUÍ — Estado del proyecto (2026-07-05)

Archivo de traspaso entre conversaciones de Claude Code. Últimas sesiones
(04-05 jul): integración ComfyUI a fondo (export de workflow, chuleta,
LoRA, modelos nuevos) + fix pies en dataset avatar.

## Estado actual

- **Repo**: `C:\Proyectos\gprompt-studio` (GitHub privado
  `Gustaafvito/gprompt-studio`, rama `main`). Todo commiteado y pusheado.
- **Tests**: 880/880 en verde · ruff limpio. Correr con `python -m pytest -q`.
- **Distribuible**: `Desktop\GPromptStudio-Distribuible` (3 artefactos +
  LEEME). Regenerar TODO con `python build_release.py --yes` (tests +
  pip-audit + onedir + instalador + onefile + copia al escritorio).
- **App**: `python main.py` desde la raíz del repo.

## Sistema de diseño (respetar SIEMPRE)

- **`modules/paleta.py` = fuente única de color y tipografía.**
  - Botones: `**P.estilo_boton(P.BTN_X)` (sobrio: neutro + borde 1px +
    hover) o `primario=True` para relleno. Rellenos directos solo
    verde/rojo/azul (`BTN_EXITO/PELIGRO/PRIMARIO` = confirmar/peligro/
    primario).
  - Texto de estado: `P.TXT_OK/ERROR/AVISO/INFO/ACENTO/MUTED` (los MUTED
    son dinámicos por tema vía `__getattr__`).
  - Fuentes: `P.FUENTE_TITULO(16)/SECCION(13)/CUERPO(11)/PEQUENA(10)/HINT(9)`.
  - OJO: no aplicar `estilo_boton` a CTkCheckBox (su fg_color es el color
    de marcado) y vigilar kwargs duplicados al hacer codemods.
- **i18n**: cadenas en ESPAÑOL envueltas en `tr(...)`; f-strings →
  `tr("...{0}...").format(...)`. Combos cuyo valor es clave interna:
  display `[tr(v)...]` + des-traducir con `tr_es()` (ojo colisiones tipo
  Todo/Todos→All: ahí comparar contra `tr()`).
- **Candados en tests** (si fallan, algo se hardcodeó mal):
  - `test_paleta.py`: prohíbe hex semánticos y tamaños de fuente 7-16
    literales en CTkFont.
  - `test_i18n.py`: 4 tests — literales tr() en dict, sinks de UI sin tr,
    dominios de combos dinámicos, avatar_config; + NEGATIVE builder.
  - `test_config.py::TestCatalogoSpecsCompleto`: todo modelo visible en
    cualquier plataforma debe resolver specs.

## Hecho en las últimas sesiones (jul 2026)

1. Auditoría seguridad cerrada: keys DPAPI, requirements.lock + pip-audit
   en cada build, deps sin CVEs, claude-fable-5 restaurado.
2. i18n inglés 100% (3 barridos AST; ~2800 entradas en TRADUCCIONES).
3. Paleta semántica (866 sustituciones) + escala tipográfica (771).
4. Estilo sobrio de botones: barra central + footer + 30 botones
   SECUNDARIO/ACENTO de ventanas. Aprobado por el usuario.
5. Command palette **Ctrl+K** (`modules/command_palette.py`): indexa
   automáticamente `app._paleta_comandos` (se registra en ui_builders al
   construir los menús — herramientas nuevas aparecen solas). También en
   menú Aprender.
6. LEEME-PRIMERO versionado en `docs/` (el build lo copia al distribuible).
7. (2026-07-03 noche) Barrido final de estilos: purpuras hardcodeados
   rezagados a paleta; menús del header con RELLENO semántico (ojo:
   theme.py reaplica ese relleno — no volver al neutro btn_bg);
   dropdown buscable de modelos con tema + modelo actual resaltado.
8. **Icono propio**: `assets/icon.ico` + `icon.png` (G blanca + chispa
   ámbar sobre violeta, generado en SeaArt con Z-Image-Base). Cableado
   en main.py (iconbitmap), ambos specs (icon= y assets/ en datas) e
   installer.iss (SetupIconFile). La tanda 3 del prompt (cerebro de
   circuitos + burbuja) quedó como candidata para splash/Acerca de.

## Roadmap UI pendiente

1. **Espaciados por ventana**: usar `P.ESPACIO_XS/S/M/L/XL` (4/8/12/16/20)
   al tocar cada ventana, con revisión visual. NO codemod ciego.
2. ✅ HECHO (27d4110): **Panel lateral** `modules/panel_lateral.py` —
   drawer al borde derecho con historial/favoritos/estrellas, buscador,
   Cargar/Copiar/Borrar. Ctrl+B / menú UI / Ctrl+K. OJO: NO usar bind_all
   en un CTkFrame (CustomTkinter lo prohíbe → crash silencioso al abrir);
   se enlaza al entry. Las ventanas de Datos siguen para gestión a fondo.
3. Contraste de hints #666 en tema claro (menor).
4. Revisar OneDrive del usuario: el cliente está APAGADO — su escritorio
   no tiene copia en la nube (el repo sí, en GitHub). Decidir si reactivar
   (solo 0,6 GB libres) o dejarlo consciente.

**Bug crítico resuelto 2026-07-04 (c3f2227):** las specs sintéticas de
checkpoints ComfyUI locales no traían `ratios` → KeyError al seleccionar
uno (p.ej. 512-inpainting-ema quedó guardado en prefs) → crash al arrancar.
Ahora comfy_image_specs expone `ratios` + UI defensiva + candado en tests.
Lección: al hacer modelos nuevos seleccionables, sus specs deben tener
TODAS las claves que la UI lee directamente (ratios, y en su ruta nota/
max_chars aunque esas ya iban con .get()).

## Hecho 2026-07-04 (sesión catálogo local + limpieza plataformas)

- **ComfyUI local**: autodiscovery agrupa por familia ("── ComfyUI · SDXL
  (Fooocus) ──" etc.), dedupe contra el manifest (vaciado, backup .bak),
  audio local ACE-Step en modo Audio, descripciones por checkpoint del
  inventario del usuario (`_COMFY_DESC_LOCAL`), exclusiones de ficheros
  sin prompt (refiner/svd/transformer_only, con candado).
- z_image local alineado con la spec curada (formato híbrido + negative;
  turbo destilado sin ambos).
- **Avatar dataset**: selector con las 4 plataformas de imagen reales
  (SeaArt/ComfyUI-Fooocus/ChatGPT/Magnific) con familias como grupos.
- **Dola ELIMINADA** de toda la app (decisión usuario) + Seedance 1.0 Fast.
- Plataforma renombrada: "ComfyUI / A1111 / Forge" → **"ComfyUI / Fooocus"**
  (migración automática de prefs/setups en main._validate_and_fix_prefs).
- Altas con panel real: **Gemini Omni Flash** (vídeo, renombrado desde
  Gemini Omni; 3-10s, 5000 chars, 10 refs, audio nativo, fórmula 8 bloques)
  y **Nano Banana 2 Lite** (imagen 4.8, 14 imgs sujeto, 10 ratios).
- Plataformas de VÍDEO vacías APAGADAS (a6d9c40): Pika/Luma, Runway,
  Pixverse comentadas (sin modelos). Selector vídeo = SeaArt Video /
  ComfyUI-Fooocus / Kling AI / Sora-Veo. Migración de setups antiguos.

## Hecho 2026-07-05 (sesión ComfyUI a fondo)

Toda la integración ComfyUI quedó sólida. Familias locales del usuario:
**Flux, Qwen, SDXL, Z-Image** (Ideogram/ACE/inpainting/refiner/svd EXCLUIDOS
del escaneo vía `_COMFY_EXCLUIR_TOKENS`).

- **Prompts por familia** (guía de testing del usuario, commits d995e8a):
  Flux 2 Klein y Qwen SÍ usan negative (antes se les borraba); Z-Image
  LOCAL = lenguaje natural PURO sin tags (la spec cloud de SeaArt sigue
  híbrida — intacta); SDXL CFG 6.5; `negative_sugerido` por familia.
  IDIOMA: el modo imagen fuerza inglés (los hints ES arrastraban al LLM).
- **Qwen formato DOBLE** (formato_bloques `qwen_edit` en el JSON curado):
  workflow 2 etapas del usuario → 4 bloques PROMPT/NEGATIVE T2I + PROMPT/
  NEGATIVE IMG2IMG.
- **Exportador 🔧 Comfy** (botón footer): reescrito a **FORMATO UI** de
  ComfyUI (nodes[]+links[], `_serializar_workflow_ui`) — el formato API por
  id NO lo acepta el canvas. Loader correcto por arch (Checkpoint vs
  UNET+CLIP+VAE), CFG/pasos/sampler por familia (`config.comfy_workflow_params`),
  LoraLoader encadenado si hay LoRA. **Chuleta** (config.comfy_cheatsheet):
  línea del modelo actual + botón "🧩 Chuleta modelos" (tabla CLIP/VAE/ajustes).
- **Multi-LoRA fix** (f698b5b): el safety-net garantiza TODOS los triggers
  (era solo el primario) vía `footer.triggers_loras_activos()`.
- **Modelos**: Krea-2 (SeaArt, grupo Krea); familia Pony afinada al
  uberRealisticPornMerge PonyXL del usuario (CFG 5.0, euler/karras, score
  tags 9..5_up).
- **Avatar dataset** (e1d6264): tomas de CUERPO ENTERO fuerzan pies visibles
  (positivo reforzado + `AVATAR_NEGATIVE_PIES`); cowboy/sentada NO (recorte
  correcto). Selector con las 4 plataformas de imagen y familias como grupos.

## Hecho 2026-07-06 (auditoría de código)

- Avatar: nota en CONSEJOS_SEAART explicando prompts/ vs prompts_edicion/
  (solo con imagen de referencia) + RATIO SUGERIDO también en modo edición.
- **Auditoría completa** (7 hallazgos, todos corregidos):
  1. `guardar_en_historial` se llamaba desde el hilo worker en workers_ia
     (leía ~12 variables Tk fuera del main thread) → ahora vía `after(0)`.
  2. ClaudeProvider sin guard de respuesta vacía → mismo guard que OpenAI.
  3. **97 fugas de paleta** (hexes posicionales en set_estado, ternarios,
     dicts) sustituidas por P.X con valor IDÉNTICO (cero cambio visual).
     Candado nuevo `test_sin_hex_identicos_en_ninguna_posicion`. Los tonos
     históricos distintos (#f39c12, #1a8a3c, #5a1a1a) quedan — cambiarlos
     altera el aspecto y necesita validación visual del usuario.
  4. Fugas i18n: "JSON importado…" y "puede tener errores de sintaxis"
     sin tr() (evadían el candado por ser f-string/BinOp en el sink).
  5. `LLM_TIMEOUT_S = 180` en los 3 SDKs (OpenAI/Anthropic esperaban 600s;
     google-genai podía colgarse sin límite).
  6. Candado test_paleta reforzado (cualquier posición, no solo kwargs).
  7. Código muerto `or "sin-key"` eliminado.
- Sano confirmado: sin eval/exec/pickle/shell=True, persistencia atómica,
  keys DPAPI, logging rotado, requests con timeout, 882 tests verdes.
- **Candado i18n reforzado**: el check de sinks ahora recorre BinOp (+) e
  IfExp — cazó 2 fugas latentes ("(N de M)" en Personajes/LoRAs, ya tr()).
- **Roadmap UI punto 3 HECHO**: hints con gris fijo → P.TXT_MUTED(_OSCURO)
  dinámicos por tema (dialogs, avatar_ui, tools_creative, tools_analysis,
  app). El del splash queda fijo a propósito (fondo siempre oscuro).
  Validado visualmente por el usuario (2026-07-06).
- Pillow 10.4.0→12.3.0 en el entorno local (6 CVEs; el lock ya lo pinaba
  — estaba desincronizado). El .exe final quedó sin CVEs.

## Hecho 2026-07-06 (tarde): datasets LoRA ampliados a 50

Los 4 catálogos de tomas (Personaje/Paisaje/Objeto/Estilo) pasan de 30 a
**50 vistas** (petición del usuario: generar de sobra y elegir). Claves:
- Personaje: nuevas tomas respetan los PREFIJOS de prompt que deciden el
  negative en avatar_prompts ("close-up headshot"/"upper body"/"full body"
  + pies visibles). De rodillas/cuclillas usan "whole figure" a propósito
  (forzar pies ahí sería incorrecto).
- Ratios: por cues o campo "ratio" explícito donde la inferencia fallaría
  (ls_vertical 9:16, sty_bridge/cafe 3:2...). Verificado por script.
- Objeto: 2 vistas agresivas nuevas (inclinado, explotada) con warn y
  EXCLUIDAS del set ⚖ Equilibrado (queda en 45).
- 82 traducciones EN nuevas (candado test_cobertura_avatar_config pasa).
- Tests de conteo 30→50 actualizados; CONSEJOS_SEAART menciona "hasta 50:
  genera de sobra y ELIGE".

## Hecho 2026-07-06 (noche): tipo de LoRA NSFW (18+)

5º tipo "🔞 NSFW" en LORA_TYPES (petición usuario). Diseño:
- 30 tomas SOLO de sujeto adulto en 3 niveles: lencería (12) → sugerente/
  implied (8) → desnudo artístico (10). Sin actos: un LoRA de identidad
  entrena la persona, no la escena.
- Descripción canónica SIN ropa (SYSTEM_PROMPT_NSFW_CANONICO: empieza por
  "adult" + franja de edad; el vestuario va por toma). Campo nuevo
  cuerpo_detalle (tatuajes/lunares = coherencia entre tomas).
- SALVAGUARDAS con candado (TestTipoNSFW::test_salvaguardas_adulto):
  negative bloquea child/teen/underage/minor en TODAS las imágenes y
  todos los prompts declaran "adult". NO quitar.
- Pipeline genérico (no el de Personaje): neg_extra por toma para el
  control de recorte; luz y escenario embebidos por toma (lighting="" y
  backgrounds=None). Consejo propio _CONSEJOS_NSFW (ToS SeaArt, 18+,
  consentimiento si se parece a persona real, mezcla con LoRA vestido).
- El selector de tipos de avatar_ui ahora se DERIVA de LORA_TYPES
  (tipos nuevos aparecen solos). Ficha auto e imagen de referencia
  soportadas; el modo edición ignora las claves NSFW (esperado).

## Pendientes que necesitan al usuario

- **Krea-2**: confirmar formato (asumí natural), `max_chars` real (contador
  bajo la caja) y nota — puestos por estimación.
- **Z-Image local**: nombres exactos de CLIP y VAE para clavar la chuleta
  y el workflow (ahora salen "(elígelo en ComfyUI)").
- Validar VÍDEO ComfyUI (Wan 2.2, LTX 2.3) con la herramienta — nunca
  probado.
- Probar el dataset avatar con pies visibles y avisar si algún checkpoint
  sigue recortando (subir agresividad si hace falta).

- Capturas de paneles SeaArt para dar de alta motores de vídeo externos:
  Wan 2.7, Vidu Q3 Pro, Kling 3.0 turbo, Kling O1, Grok Imagine,
  StarDream 2.0 Fast, Happy Horse, Hailuo 2.3 fast (política: NO inventar
  specs, solo con panel real).
- Discrepancias de nota: Veo 3.1 (4.7 vs 3.0 SeaArt) y Wan 2.6 (4.3 vs 3.5).
- Probar FLUX.1-Kontext-dev para rotar el avatar desde referencia.
- Filtro "vigente" para vídeo/audio/plataformas (el usuario dijo que él).

## Convenciones de trabajo con este usuario

- Commits en español con prefijo tipo `feat(ui):`/`fix(i18n):`; siempre
  push tras commit (GitHub es el único backup, el repo NO está en OneDrive).
- Al generar el .exe: SIEMPRE `build_release.py` (onefile + instalador +
  onedir, los 3 al escritorio) — nunca builds parciales.
- Listas de modelos siempre alfabéticas (case-insensitive).
- Tras cambios de UI: relanzar la app (`python main.py`) para que el
  usuario los vea y valide antes de commitear cambios de gusto.
