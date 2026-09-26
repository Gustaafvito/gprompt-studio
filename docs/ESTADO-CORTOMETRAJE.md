# Estado: «Crear desde imágenes» → Cortometraje

Última actualización: **24-sep-2026, noche**. Escrito como traspaso entre
sesiones: si abres una sesión nueva sobre este repo, lee esto primero. También
sirve para pegárselo a ChatGPT, que viene revisando cada entrega.

---

## 1. Dónde está el trabajo

| | |
|---|---|
| Rama | `feat/visual-studio` |
| Último commit publicado | `c48176c` |
| PR | [#1](https://github.com/Gustaafvito/gprompt-studio/pull/1) — abierto, **sin fusionar**, no es borrador |
| Base | `main` en `5929aeb` |

Publicado el 24-sep, hasta `92e7e50`: el arreglo de Tcl y su bitácora, los
guardados, Aprender (tutorial, glosario, atajos, Ctrl+K), los rótulos del
panel, el resultado visible, los cuelgues de los tests, el panel por pasos y
su botón a la vista, los botones que se escondían, Seedream 5.0 Flash con la
preparación de la 1.1.0 (§5e), NSFW/Destino/tutorial y el Brief por modo
(§5f).

La rama del worktree sigue existiendo con el commit original. Está limpia, no
hay nada en el stash y `git range-diff` confirma que `b04ead2` es el mismo
parche. Ya se puede retirar sin perder nada.

El título y la descripción del PR siguen hablando solo de la beta visual 9.1.
Hay un borrador nuevo listo para pegar (lo tiene el usuario); desde aquí no se
puede editar el PR, porque no hay `gh` ni token. El texto actual del PR tiene
dos errores: fecha `5929aeb` el 25-sep, y es del 22-sep; y dice que el botón
está «en la botonera». Ahora está junto a la caja de la idea (`80aa6a5`).

**Dónde vive cada versión** (el usuario preguntó por qué no veía nada nuevo):

| Sitio | Versión | ¿Tiene esto? |
|---|---|---|
| Rama `feat/visual-studio` | todo lo de septiembre | sí, con `python main.py` |
| `main` y la release v1.0.2 | 18-sep | no |
| App instalada (`AppData\Local\Programs\G-Prompt Studio`) y distribuible del escritorio | v1.0.2 | no |
| Escritorio: `GPromptStudio-Prueba-Crear-desde-imagenes\GPromptStudio-Prueba.exe` | portable de prueba de `c48176c` (24-sep, título v1.1.0) | todo, hasta el Brief por modo |
| Escritorio: `GPromptStudio-Visual-Beta` y `GPromptStudio-candidato-codigo` | copias del 19 al 21-sep | obsoletas; no se tocan |

Para que llegue a la app instalada: fusionar el PR, compilar y publicar (1.1.0).

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

## 5. El parpadeo de Tk, resuelto (`b04ead2` + `81c1bb9`)

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

**Cuelgues cazados (`0de5038`).** La bitácora dejó tres volcados el 24-sep
por la tarde, los tres en el mismo sitio: el ayudante de los tests
`root.after(ms, root.quit); root.mainloop()`. La primera vez que se llama a
`CTk.mainloop()`, CustomTkinter hace un `update()` para pintar la barra de
título; si ahí vence el `quit`, se pierde, porque `_tkinter` pone a cero la
marca de salida al arrancar el bucle, y el bucle no vuelve. Reproducido a
propósito. Ahora todos los tests bombean con `tests/_bombeo.bombear()`,
basado en `update()`, y hay un candado contra el patrón viejo.

**Sigue sin volcado** el cuelgue de 22 minutos de la mañana (45 s de CPU), que
fue creando el intérprete de Tcl: no se puede afirmar que fuera el mismo. Si
vuelve, la bitácora lo dirá.

---

## 5b. Guardados que se pisaban (`f1712f0`)

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

## 5c. Aprender, atajos e idioma (`3825315`, `93efa19`, `38695d9`)

Nada de lo nuevo estaba en Aprender. Ahora:

- **Tutorial**, en español y en inglés. El paso 43 es «Crear desde imágenes»
  y el 44 el «Cortometraje», los dos con «Probar ahora». El paso 32 describía
  cuatro botones narrativos de cinco, y mal (Walk era «un recorrido
  espacial»); corregido, igual que las ayudas emergentes de esos botones.
- **Ctrl+K** encuentra las dos herramientas.
- **Ctrl+Shift+I** abre «Crear desde imágenes». El botón está en la pestaña
  ⚙️ Ajustes Extra, no en la botonera.
- **Ctrl+Shift+A** no funcionaba nunca: estaba en minúscula y, con Shift, Tk
  entrega la letra en mayúscula. Se comprobó con pulsaciones reales, que
  además capturaron teclas que el usuario estaba escribiendo: **no repetir
  pruebas con teclado real** con el usuario delante.
- La ayuda de «🎬 Corto» no tenía inglés. El candado de traducciones solo ve
  `tr("literal")` y no `tr(variable)`; hay uno nuevo para la botonera.

- **Modo educativo**, que es el glosario (`data/glosario.json` y su `.en`).
  Tiene fichas nuevas para «Crear desde imágenes», el «Cortometraje» y el
  concepto de vídeo por referencia. La ficha de narrativa tenía el mismo
  error que el paso 32. Un test nuevo vigila que los dos idiomas vayan a la
  par, y el barrido comprueba también sus botones «▶ Probar».

La **guía de estilos** no se tocó: es el catálogo de estilos artísticos
(`GUIA_ESTILOS.md`), no habla de herramientas.

---

## 5d. El resultado se ve, y las cajas dicen qué son (`30d044a`, `35c964e`)

Salió de una revisión crítica con capturas de la app real (el usuario pidió
«que sea una herramienta que la gente quiera tener»).

- **Resultado visible.** Recibía 30 px de los 240 que pide a tamaño por
  defecto en 1920×1080: se empaqueta el último y pack encoge primero lo
  último. Ahora pestañas e idea ceden alto, y si ni así cabe, las pestañas
  se pliegan a su tira de títulos (▴/▾; pulsar un título despliega). Cálculo
  en `modules/espacio_ventana.py`. Medido: 30 → 160 px por defecto, 142 →
  211 maximizada, 0 → 113 a 760 de alto.
- **Tamaño inicial con escalado de Windows.** `CTk.geometry()` multiplica
  por la escala y la app le pasaba píxeles reales: al 125 % la ventana
  pedía más alto que la pantalla. Probado solo con cálculo; esta máquina
  está al 100 %.
- **Modo Focus.** Al salir, las pestañas no volvían nunca. Arreglado.
- **Rótulos del panel.** Las cajas de una línea usaban el texto gris como
  único rótulo, y se perdía al escribir, al abrir un proyecto (se escribía
  "" en cada caja) y siempre en el buscador de modelos.

**Queda abierto de esa revisión:**
- Por debajo de ~680 de alto (portátiles de 1366×768) ni plegando cabe el
  resultado; la app avisa de Ctrl+H. Arreglarlo de verdad pide rediseñar la
  ventana principal (por ejemplo, el resultado a la derecha en pantallas
  anchas).
- Dos tests fallaron una vez cada uno en la suite completa y nunca aislados:
  el de extremo a extremo de la bitácora de cuelgues (ahora enseña la salida
  del subproceso si vuelve a caer) y
  `test_panel_vision::test_por_defecto_no_fija_proveedor`. Descartado que
  fuera esperar a un hilo: su ejecutor es síncrono. Uno de sus cuelgues sí
  era el de `mainloop()` ya arreglado; el fallo simple, no se sabe.

**Hecho de esa revisión (`e0188b6`, `80aa6a5`):** el panel «Crear desde
imágenes» va por secciones con título, con Analizar, Generar, Copiar y
Cortometraje en una barra fija abajo, jerarquía de colores, bajada
automática al resultado, análisis sin markdown, estado vacío y sin «Beta 9».
Su botón está ahora en la fila de «Describe tu idea» de la ventana
principal, a la vista sin abrir ninguna pestaña.

## 5e. Nada se esconde al estrechar, Seedream 5.0 Flash y la 1.1.0

**Los botones que desaparecían (`9465f48`).** Medido a 1382 de ancho, el de
la ventana por defecto: Reset, Última, Setup y Cargar setup no se veían,
«Preview» quedaba en 34 px, el menú «UI» en 37 y «Workflow» no aparecía.
Tk no avisa: con `pack(side="left")` encoge los últimos hasta dejarlos en
nada. Ahora los botones miden lo que su texto, las dos filas de la botonera
son `FilaFluida` (`modules/fila_fluida.py`: lo que no cabe baja de línea
entero) y la cabecera se compacta a solo iconos según el hueco real, no con
un «< 1180» de cuando había 7 menús. La ficha del modelo tenía el ajuste de
línea fijo en 1800 y se salía por la derecha: ahora sigue a la ventana y se
queda en dos líneas con «…».

**Trampa cazada:** escuchar el `<Configure>` de la propia etiqueta de la
ficha **cuelga la app al 100 % de CPU**. Cada ajuste cambia su ancho
(1310 → 1322 → 1304) y una `CTkScrollbar` se queda redibujándose sin fin. Se
vio porque un pytest llevaba 12 minutos vivo sin volcado; `faulthandler`
con `dump_traceback_later` en un guion aparte dio la pila en 25 s.

**Seedream 5.0 Flash** (anunciado el 24-sep). Datos del esquema oficial vía
el MCP de SeaArt (`get_model_params`, modelo `daqedfle878c73d0emlg`): prompt
hasta 2000, 8 formatos (con 21:9), 1K/1,5K/2K, hasta 6 imágenes para editar
y 8 por tanda, sin negativo. El catálogo pasa a **272**.

**La 1.1.0, preparada y sin publicar.** Añadir un modelo rompe los candados
que atan la cifra a las notas del release de la versión vigente. Cambiar las
de la 1.0.2 sería falsearlas (salió con 271), así que, con el visto bueno
del usuario, se subió la versión a 1.1.0 (config, pyproject, installer.iss)
y se empezó `docs/RELEASE-v1.1.0.md`. Su comentario de cabecera lista lo que
falta antes de publicar: build, hashes (los del bloque son aún los de la
1.0.2), VirusTotal, tamaños (marcados PENDIENTE; `build_release.py` avisa
mientras quede alguno) y fusionar. **El PR no se fusiona antes de publicar:**
los README ya apuntan a `releases/download/v1.1.0/…`, que dará 404 hasta
entonces.

## 5f. NSFW, Destino y el tutorial (`e3eb5a0`, `c090a98`)

El usuario pidió opinión sobre Brief, Destino y NSFW («NSFW no lo quites;
si puedes, mejóralo»).

- **NSFW.** La detección automática no había funcionado nunca: escribía en
  `nsfw_var`, que no existe, y anunciaba el cambio igualmente. Ahora
  `modules/nsfw.py` detecta palabras enteras en inglés y castellano, y
  conoce los modelos cuyo fabricante filtra el contenido adulto (GPT Image,
  Nano Banana, Veo, Midjourney…). Con NSFW encendido y uno de ellos, el
  prompt se queda en sugerente para que no lo rechacen, y se avisa. Con un
  modelo para adultos y NSFW apagado, también se avisa. El negativo SFW
  excluye «nsfw, nudity».
- **Destino.** En inglés no activaba nada (comparaba el nombre traducido) y
  ponía formatos que el modelo no tenía. Arreglado.
- **Tutorial.** La casilla doble era un ✅ en el texto.

**Brief (`22d80b8`, con el visto bueno del usuario).** Estaba escrito para
anuncios de VÍDEO (primer shot, 6-15 s, voz en off) y se pegaba igual a
imagen y audio; se recuerda entre sesiones y su interruptor vivía en una
pestaña que puede ir plegada. Ahora hay reglas por modo
(`prompts.brief_para_modo`), un interruptor junto a Destino en cada panel y
un indicador «⚡ Brief» en la fila de modo que lo apaga de un clic. En la
cabecera, junto al de ADN, no cabía: los 8 menús se compactaban a 1382.
Glosario con fichas de Brief, Destino y NSFW.

**Anthum, fuera** (`bed6370`, 25-sep, pedido por el usuario): de Destino,
de las reglas, de la plantilla de ejemplo y de las traducciones. Era lo
único que encendía el Brief sin que el usuario lo pidiera.

**Probado por el usuario con el portable de `c48176c` (24-sep, noche):**
Seedream Flash, Brief de imagen (con GPT Image 2.5 Sunburst: cumple las seis
reglas; salió ilustración porque tenía Estilo «Illustration»), Destino, y
los avisos de NSFW con modelo que filtra y con modelo adulto, bien. Falta
«Crear desde imágenes» (paso 7).

**Arreglado tras esa prueba** (`eaa0f61`): al encenderse NSFW solo, el
aviso iba únicamente en el mensaje de «Compilando…» y los mensajes de
progreso lo pisaban; el usuario vio el interruptor encendido pero no el
porqué. Ahora sale también flotando, 6 segundos.

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

2. **El push de `93efa19` y `38695d9`** (ver §1), y pegar el borrador nuevo
   del PR, que ya recoge §5b y §5c.

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
python -m pytest -q      1816 passed, 1 skipped
python -m ruff check .   All checks passed!
timeout 25 python main.py  exit 124 (sigue viva), 0 errores en el log
```
