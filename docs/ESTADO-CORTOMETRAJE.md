# Estado: «Crear desde imágenes» → Cortometraje

Última actualización: **24-sep-2026**. Escrito como traspaso entre sesiones: si
abres una sesión nueva sobre este repo, lee esto primero. También sirve para
pegárselo a ChatGPT, que viene revisando cada entrega.

---

## 1. Dónde está el trabajo

| | |
|---|---|
| Rama | `feat/visual-studio` |
| Último commit publicado | `658f308` |
| PR | [#1](https://github.com/Gustaafvito/gprompt-studio/pull/1) — abierto, **sin fusionar**, no es borrador |
| Base | `main` en `5929aeb` |

**Hay trabajo sin publicar.** El commit `9d045a5` (arranque de Tcl, ver §5) vive
solo en local, en la rama `claude/youthful-almeida-847f8d`, dentro de un
worktree. No está en ningún remoto y **no está fusionado** en
`feat/visual-studio`. Decidir qué se hace con él es lo primero.

El título y la descripción del PR siguen hablando solo de la beta visual 9.1 y
no mencionan el Cortometraje. Quien tenga permiso de escritura en GitHub puede
actualizarlos; desde aquí no se puede sin un token.

---

## 2. Qué hace el puente

«Crear desde imágenes» puede lanzar el Cortometraje reutilizando lo que el
usuario ya tiene preparado —las referencias, sus funciones y el análisis ya
revisado— en vez de obligarle a describir las imágenes otra vez a mano.

Las piezas, todas en `feat/visual-studio`:

- **`modules/visual_brief.py`**
  - `shortfilm_context(refs, analysis, preserve, change)` — función pura.
    Traduce las funciones de las referencias a instrucciones de guion.
  - `SHORTFILM_ROLES` — qué significa cada función (Personaje, Producto,
    Escenario, Estilo, Iluminación, Composición) cuando el destino es un guion.
    Hay un candado que obliga a cubrir las seis de `ROLES`.
  - `shortfilm_ref_map(refs)` — qué archivo corresponde a cada `@ref`.

- **`modules/multiprompt.py`**
  - `construir_peticion_cortometraje(logline, contexto, n, idioma, aspecto, segundos)`
    — pura. Los tres últimos parámetros son nuevos y opcionales.
  - `revisar_guion_cortometraje(texto, n, segundos, n_refs)` — revisa el guion
    RECIBIDO y devuelve avisos. Local, sin coste.
  - `_cmd_cortometraje(premisa, contexto, idioma, aspecto, segundos)` — con
    `premisa` llega desde el panel; sin ella se comporta como siempre.

- **`modules/visual_studio.py`** — el botón «Crear cortometraje con estas
  referencias» y el método `shortfilm()`.

- **`modules/core.py`** — `_pedir_n_modal()` acepta un segundo campo opcional
  de segundos y devuelve `(n, segundos)` cuando se le piden.

Tests: `tests/test_cortometraje_desde_referencias.py`, 88 tests con
proveedores simulados. Ninguno toca la red ni gasta saldo.

---

## 3. Decisiones tomadas, y por qué

Estas ya se discutieron. No hace falta volver a abrirlas salvo que aparezca
información nueva.

**La entrada clásica no cambia, nunca.** El Cortometraje de la ventana
principal sigue leyendo su caja de idea, exigiendo modo VÍDEO y usando el
personaje activo del pie. Todos los parámetros nuevos son opcionales y sin
ellos la petición sale palabra por palabra como antes. Hay tests dedicados.

**Desde el panel se salta el candado de modo VÍDEO.** Un guion de cortometraje
es vídeo por definición, y obligar a cerrar el panel para mover un desplegable
era el tropiezo que había que quitar.

**Desde el panel NO se mezcla el personaje activo del pie.** Las referencias
definen el reparto; dos repartos distintos en la misma petición dejarían al
guionista eligiendo.

**Las etiquetas `@ref` van por POSICIÓN y cubren las seis funciones**, así que
la letra y el número coinciden: A es `@ref1`. Numerar solo los personajes creaba
un desfase invisible (con A escenario y B personaje, B era `@ref1`). El destino
lo admite: la ficha de Vidu Drama Reference dice «hasta 7 imágenes (personajes,
objetos, escenas, efectos)».

**El análisis caducado bloquea.** Si las referencias cambian después de
analizar, las letras A/B/C apuntan a otras imágenes y el guion saldría con
`@ref1` sobre la imagen equivocada, repetido en todas las escenas.

**Las etiquetas de la plantilla siguen al idioma pedido.** Estaban a fuego en
español y el modelo las copiaba, arrastrando a español los campos cortos
(`Plano`, `Tema`) aunque el guion se pidiera en inglés.

**El default de OpenAI pasó a `gpt-6-luna`** ($0,10/$0,50), más barato que
`gpt-4o-mini` ($0,15/$0,60) en las dos dimensiones. Decisión tomada
explícitamente por el usuario el 24-sep.

---

## 4. Lo que se aprendió probando con imágenes reales

Dos pruebas con tres referencias: chica con auriculares (Personaje), estación de
tren (Escenario), figura cyberpunk con paraguas (Estilo). Guardadas en
`~/.arquitecto_prompts/casos_referencia/20260923-separacion-de-funciones/`, con
su LEEME.

**La separación de funciones se sostiene sola.** En la prueba de control, con
los campos «Conservar» y «Cambiar» VACÍOS, de la referencia de Estilo solo
viajaron los colores, la iluminación y los reflejos. No se coló su personaje, ni
su pelo corto, ni sus gafas LED, ni su chaqueta, ni sus guantes, ni su paraguas.

Eso descartó añadir un glosario de funciones al prompt: no hace falta. **Un caso
no demuestra que esté garantizado** para cualquier imagen o modelo, pero sí que
aquí aguantó sin ayuda manual.

**Ollama con `llava:latest` no sirve para esto:** mezcló las tres imágenes,
repitió descripciones e inventó una referencia «H» que no existía. Gemini las
distinguió bien. El selector de proveedor de visión del panel permite elegirlo,
en modo exclusivo y sin alternativas.

**El generador inventa cosas que el prompt no pide.** La mochila de la imagen
generada NO estaba en el prompt: la añadió GPT Image. Una regla dirigida al
modelo que REDACTA el prompt no evita eso; son dos modelos distintos.

---

## 5. El parpadeo de Tk, resuelto (commit `9d045a5`, sin publicar)

La suite fallaba a veces con 62 errores de setup. **No era una cascada**: 62 es
exactamente el número de tests que cuelgan de la fixture de sesión `tk_root`, y
pytest cachea la excepción de una fixture de sesión y la relanza en cada uno. Un
solo fallo contado 62 veces.

Lo que falla es **crear el intérprete de Tcl**, capturado con dos mensajes
distintos. El arreglo lo reintenta en los tres sitios que crean uno, filtrando
por la TRAZA y no por el mensaje.

Descartado con medidas, no con opiniones: los `after` huérfanos de un panel
destruido son inofensivos (`Misc.destroy()` los neutraliza con `deletecommand`),
y no es agotamiento de handles (120 paneles → 392 GDI de 10000).

**Sigue abierto:** un CUELGUE observado en el mismo punto (22 minutos de reloj,
45 s de CPU). Hay un cortafuegos de tiempo por test que vuelca la pila y aborta,
pero la causa de fondo no está identificada.

---

## 6. Lo que queda abierto

**Bloqueado, esperando al usuario:**

1. **La sintaxis real de SeaArt.** El constructor escribe `@ref1`; la ficha del
   catálogo dice `Nombre@imagenN`. Una de las dos está mal y solo se resuelve
   con una captura de la pantalla de generación, con el modelo elegido y las
   imágenes cargadas. No hace falta generar nada. Mientras tanto, conviene
   separar la numeración interna de cómo se escribe en cada generador.

2. **Qué se hace con `9d045a5`** (ver §1).

**Propuesto y no hecho:**

3. El formato (9:16) no llega a los prompts de imagen del bloque de personajes.
4. El cuelgue de Tk (§5).
5. Título y descripción del PR (§1).

**Prueba pendiente del usuario:** personaje + escenario + estilo con sus propias
imágenes, comprobando que el personaje se mantiene entre escenas y que el
escenario sigue siendo reconocible.

---

## 7. Cómo se trabaja en este repo

- **Todos los commits van al repo principal** `C:\Proyectos\gprompt-studio`,
  nunca a un worktree.
- Cada literal nuevo dentro de `tr()` necesita su inglés en `modules/i18n.py`.
- Las listas de modelos, alfabéticas (sin distinguir mayúsculas).
- Las claves de API viven en `~/.arquitecto_prompts/keys.json`, fuera del
  proyecto. El correo personal no aparece en material público del repo.
- El código con escapes se escribe con el editor, **nunca con heredocs**: los
  heredocs entrecomillados se comen los `\\` y los `\u00b7`. Ha pasado tres
  veces.
- Antes de dar por bueno un arreglo, **desactívalo y comprueba que el test
  falla**. Un test que no cae al romper lo que vigila no vigila nada.
- Los precios y los modelos se verifican contra su fuente. No de memoria y no
  porque lo diga otro agente.

---

## 8. Verificación al día de hoy

```
python -m pytest -q      1635 passed, 1 skipped
python -m ruff check .   All checks passed!
timeout 25 python main.py  exit 124 (sigue viva), 0 errores en el log
```
