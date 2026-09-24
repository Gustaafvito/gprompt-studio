# Estado: «Crear desde imágenes» → Cortometraje

Última actualización: **24-sep-2026, tarde**. Escrito como traspaso entre
sesiones: si abres una sesión nueva sobre este repo, lee esto primero. También
sirve para pegárselo a ChatGPT, que viene revisando cada entrega.

---

## 1. Dónde está el trabajo

| | |
|---|---|
| Rama | `feat/visual-studio` |
| Último commit publicado | `d2e4ddf` |
| PR | [#1](https://github.com/Gustaafvito/gprompt-studio/pull/1) — abierto, **sin fusionar**, no es borrador |
| Base | `main` en `5929aeb` |

**El arreglo de Tcl ya está en la rama, pero sin publicar.** El commit `9d045a5`
del worktree `claude/youthful-almeida-847f8d` se trajo a `feat/visual-studio`
como `b04ead2`, y encima va `81c1bb9`, que acota su bitácora de cuelgues (ver
§5). Después van `8ca6da0` (este documento) y `f1712f0` (guardados que se
pisaban, ver §5b). Los cuatro están en local, **pendientes del visto bueno
para el push**.

La rama del worktree sigue existiendo con el commit original. Está limpia, no
hay nada en el stash y `git range-diff` confirma que `b04ead2` es el mismo
parche. Se puede retirar sin perder nada **cuando esto esté publicado**.

El título y la descripción del PR siguen hablando solo de la beta visual 9.1.
Hay un borrador nuevo listo para pegar (lo tiene el usuario); desde aquí no se
puede editar el PR, porque no hay `gh` ni token. El texto actual del PR tiene
además un error: fecha `5929aeb` el 25-sep, y es del 22-sep.

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

## 5. El parpadeo de Tk, resuelto (`b04ead2` + `81c1bb9`, sin publicar)

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

Ya traído a esta rama, el reintento **salvó una tirada real** en la primera
pasada completa: `tcl_findLibrary` al arrancar el `ArquitectoApp()` de
`test_barrido_ui`. Es la segunda vez que se le ve actuar. Comprobado además
rompiéndolo: sin reintento caen 3 tests, y con el filtro de traza abierto caen 2.

**`81c1bb9` corrige dos cosas del propio arreglo:**

- Su bitácora de cuelgues era un único `tests_colgados.log` en modo "a", con
  una línea por test: 687 KB y ningún volcado tras unas pocas tiradas. Ahora es
  una por proceso y se borra sola si no hubo cuelgue. **Si ves una, hubo
  cuelgue.** El fichero viejo ya no lo escribe nadie y se puede borrar a mano.
- Su `faulthandler.enable()` no hacía nada, porque el plugin de pytest lo pisa.
  Se comprobó provocando un fallo fatal. Los fallos fatales van a stderr.

**Sigue abierto:** un CUELGUE observado en el mismo punto (22 minutos de reloj,
45 s de CPU). Hay un cortafuegos de tiempo por test que vuelca la pila y aborta,
pero la causa de fondo no está identificada.

---

## 5b. Guardados que se pisaban (`f1712f0`, sin publicar)

Lo señaló ChatGPT. Redirigir los borradores de los tests a un temporal no
arreglaba `VisualHistory.save()`, que nombraba cada versión solo con la hora.
En Windows con Python 3.10 la hora avanza a **saltos de 15,6 ms**: 200.000
llamadas seguidas dieron 495 valores distintos. Dos `checkpoint()` en el mismo
salto se llamaban igual y el segundo borraba el primero. Con la hora congelada,
de cuatro guardados sobrevivía uno.

Al escribir el test salió un segundo fallo. Si el reloj retrocedía, el recorte
a 12 borraba las versiones **más nuevas**, porque ordena por nombre y el nombre
empezaba por la hora.

Ahora el nombre empieza por un contador de la sesión
(`000007-20260924-173000-123456.gprompt`), y «Recuperar» desempata por nombre.
Los borradores viejos siguen apareciendo. Un test que ya existía guardaba tres
versiones seguidas y pasaba solo porque cada guardado tarda más de 15,6 ms.

---

## 6. Lo que queda abierto

**Bloqueado, esperando al usuario:**

1. **La sintaxis real de SeaArt.** El constructor escribe `@ref1`; la ficha del
   catálogo dice `Nombre@imagenN`. Una de las dos está mal y solo se resuelve
   con una captura de la pantalla de generación, con el modelo elegido y las
   imágenes cargadas. No hace falta generar nada.
   - El 24-sep por la tarde se buscó por otras vías, y ninguna lo resuelve.
     Drama Reference no sale en el `list_models` del MCP de SeaArt. La ayuda de
     `seaart reference2video` dice que las referencias van «ligadas al prompt»
     sin decir cómo. El binario está comprimido con UPX y no se abrió. Además,
     el propio catálogo ya usa tres formas: `@ref1`, `@imagen1` en las
     fórmulas en español y `@image1` en los ejemplos en inglés.
   - Separar la numeración interna de la sintaxis de cada generador **se deja
     para cuando haya una sintaxis confirmada**. Sin ninguna, el mapa por
     generador se diseñaría a ciegas. `@ref` aparece 27 veces en 6 ficheros
     de `modules/`, varias en comentarios. Ojo con la de
     `prompts_inyeccion.py`: es una regla que PROHÍBE esas etiquetas en otro
     modo. Si cambia la sintaxis, hay que añadir la nueva ahí sin quitar
     `@ref`.

2. **El push de los cuatro commits** (ver §1), y pegar el borrador nuevo del
   PR, que hay que ampliar con §5b.

**No se hace, salvo que el usuario diga otra cosa:**

3. Que el formato (9:16) llegue a los prompts de imagen del bloque de
   personajes. ChatGPT y esta sesión coinciden: una referencia de personaje y
   un clip pueden necesitar encuadres distintos. Tampoco se cambia ahora a
   fondo neutro de forma automática. Los motivos:
   - El formato solo existe en la entrada desde el panel, porque la clásica no
     pasa `aspecto`. Y ahí los personajes suelen tener ya su imagen real.
   - En el vídeo por referencia, el encuadre del clip lo fija un parámetro
     aparte: `seaart reference2video` tiene su propio `--aspect-ratio`. No
     depende de la forma de la imagen de referencia.
   - Una ficha de personaje a 16:9 es un retrato con media imagen vacía.
   Si algún día se toca, la idea sería pedir que esos prompts sean de
   **retrato de referencia**, con cara y vestuario bien visibles.

**Propuesto y no hecho:**

4. El cuelgue de Tk (§5).

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
python -m pytest -q      1672 passed, 1 skipped
python -m ruff check .   All checks passed!
timeout 25 python main.py  exit 124 (sigue viva), 0 errores en el log
```
