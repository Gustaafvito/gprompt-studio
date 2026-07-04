# CONTINUAR AQUÍ — Estado del proyecto (2026-07-03)

Archivo de traspaso entre conversaciones de Claude Code. Última sesión:
lavado de cara completo de la UI + i18n + distribuible.

## Estado actual

- **Repo**: `C:\Proyectos\gprompt-studio` (GitHub privado
  `Gustaafvito/gprompt-studio`, rama `main`). Todo commiteado y pusheado.
- **Tests**: 849/849 en verde · ruff limpio. Correr con `python -m pytest -q`.
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
- PENDIENTE del usuario: lista real de plataformas de VÍDEO (Pika/Luma,
  Runway, Pixverse están vacías; ¿Magnific vídeo?) — limpiar/altas cuando
  pase capturas.

## Pendientes que necesitan al usuario

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
