# Crear desde imágenes — versión de prueba en código fuente

## Revisión 9 — dirección de vídeo y manejo de proyectos

- Dirección de vídeo: cámara, movimiento del entorno y sonido/diálogo separados.
  En Inicio → final aparece además el recorrido de A a B. Son opcionales y se
  aplican a generación, mejora y ajuste de longitud. No certifican capacidades
  de audio, duración o sincronización labial del generador.
- Nombre de proyecto, guardado con Ctrl+S y botón Nuevo proyecto que abre otra
  ventana sin borrar el trabajo actual.
- Recuperación muestra fecha, nombre/idea y modelo en las 100 versiones más
  recientes disponibles. Cada sesión sigue conservando 12 versiones.
- Las miniaturas conservan proporciones y Ampliar abre la referencia en una
  ventana redimensionable.
- La ayuda indica si la cantidad de referencias corresponde al modo elegido.
- El límite manual también se aplica al generar por primera vez.
- Las instrucciones evitan inventar restricciones de proveedores sobre marcas.
- Los proyectos antiguos siguen abriendo; los campos nuevos se dejan vacíos.

Prueba sugerida: abre tu proyecto de la estación, guarda una copia con nombre,
selecciona Animar imagen con una única referencia y escribe una acción breve.
Cámara: acercamiento lento. Entorno: niebla suave. Sonido: ambiente sin diálogo.
Revisa el resultado y comprueba que conserva la identidad y los auriculares.

Validación de esta beta: pruebas automatizadas de lógica, persistencia y mensajes.
La interfaz en Windows y la calidad de respuestas reales requieren prueba local.

## Revisión 8 — ajustar y mejorar un prompt existente

- «Ajustar al límite» condensa el resultado con IA, conservando la idea y las
  restricciones, con objetivo del 90 % del máximo para dejar margen.
- «Mejorar prompt» revisa el resultado actual con instrucciones opcionales.
- Ambas acciones consumen una petición al proveedor de texto; no reanalizan
  las imágenes ni repiten automáticamente llamadas. Revisa el significado del resultado.
- Contador visible del positivo y límite manual opcional; vacío usa el catálogo.
- Antes de sustituir el original se guarda una versión y se valida el resultado.
  Si la IA falla o vuelve a superar el máximo, el original sigue intacto.
- Un borrador nuevo demasiado largo se conserva para poder ajustarlo.

## Revisión 7 — copiar el resultado completo

- «Copiar resultado» y «Llevar a salida principal» incluyen positivo y negativo,
  con etiquetas separadas cuando hay ambos. Las notas no se incluyen.
- «Copiar positivo» y «Copiar negativo» permiten pegar cada campo por separado
  en el generador. Si no hay negativo, se copia únicamente el positivo.

## Revisión 6 — búsqueda de modelos

- Buscador encima del selector de modelos, tanto para imagen como para vídeo.
- Lista alfabética, búsqueda por palabras sin distinguir mayúsculas y botón
  «Limpiar búsqueda». Selecciona el resultado en el desplegable para aplicarlo.
- Buscar no cambia el modelo seleccionado. Sin coincidencias, el desplegable
  se desactiva; al cambiar de plataforma se limpia el filtro.
- Para combinar producto y persona, usa «Varias referencias», con sus funciones
  correspondientes. «Imagen → prompt» requiere una sola imagen.

## Revisión 5 — recuperación y revisión

- Autoguardado local cada 15 segundos si hay cambios; también antes de analizar,
  generar o cerrar esta ventana. Conserva las últimas 12 versiones por sesión.
  «Recuperar versiones» abre una copia en otra ventana sin reemplazar la actual.
- Las copias contienen imágenes y textos, sin claves API. Se guardan en
  `%USERPROFILE%\.arquitecto_prompts\visual_drafts`. Puedes eliminar esa carpeta
  con la aplicación cerrada para borrar el historial local. No se suben a la nube.
- Un cierre brusco puede perder lo escrito desde el último autoguardado.
- Cambiar referencias conserva el texto y marca el análisis como pendiente;
  requiere analizar de nuevo antes de generar. Una respuesta vacía o fallida
  conserva el resultado anterior.
- Positivo, negativo y notas tienen campos separados. «Copiar resultado» y
  «Llevar a salida principal» transferían SOLO el positivo (corregido en la revisión 7). «Copiar negativo»
  transfiere el negativo. Los proyectos antiguos separan el bloque NEGATIVE.
- Abrir un proyecto mantiene el modelo guardado aunque ya no esté disponible;
  exige elegir uno válido antes de generar, sin sustituirlo en silencio.
- «Comprobar prompt» revisa texto vacío, límite de caracteres conocido, estado
  del análisis, modelo y configuración de referencias/negativo. No comprueba
  semánticamente tu idea ni certifica capacidades desconocidas del catálogo.

## Revisión 4 — generación y uso real de referencias

- La generación usa una petición independiente, sin heredar el historial ni el
  system prompt del modo de la ventana principal.
- Tu idea define la transformación: producto fotografiado → personaje anime
  llevando el producto no se considera una contradicción. Soportes y atrezo
  no forman parte del producto salvo que lo pidas.
- La respuesta debe contener un prompt estructurado válido. Si solo devuelve
  comentarios, muestra error en lugar de dar la tarea por completada. No se
  repiten llamadas automáticamente ni se recorta un prompt que supera el límite.
- Resultado y notas se muestran separados; Copiar y Llevar a salida principal
  transferían el prompt y el negativo juntos (separados desde la revisión 5).
- **Solo texto**: las imágenes se analizan para redactar, pero el generador de
  destino solo recibe texto. El prompt describe explícitamente los rasgos.
- **Adjuntar imágenes**: comprueba en tu plataforma que ese modelo y ese modo
  admiten las imágenes. La casilla registra tu comprobación para la petición;
  no convierte un modelo en compatible. Cambiar referencias o destino la reinicia.
- No se ha inventado una lista de compatibilidad de SeaArt. El catálogo no
  contiene capacidades de entrada verificadas para todos los modelos. Su campo
  `max_imagenes` NO se interpreta como número de referencias admitidas.
- La petición de análisis especifica el número exacto de referencias para evitar
  que la IA invente letras o vistas adicionales.

Para tu ejemplo: una foto de auriculares, función Producto, idea «Un chico anime
lleva puestos estos auriculares», conservar diseño/colores/materiales del producto,
cambiar soporte y fondo. Usa Solo texto si tu panel de destino no acepta imágenes.
El parecido exacto del producto no está garantizado usando únicamente texto.

## Revisión 3

Se restaura la ventana normal redimensionable con sus controles de maximizar
y minimizar en Windows. Se mantiene la elevación temporal al abrir.

## Revisión 2

- Duración editable: admite 12 segundos y decimales. Es una duración solicitada;
  la disponibilidad real depende del modelo, que puede tener otros límites.
- Plataforma y modelo se eligen dentro del panel, usando el catálogo existente.
- Varias referencias permite salida de imagen o vídeo.
- Ayuda específica por modo. Intercambiar A/B solo aparece en Inicio → final.
- Enfoque y elevación temporal al abrir.
- Los proyectos guardan plataforma, modelo, tipo de salida y duración.

Base: gprompt-studio, commit 855b757. Esta carpeta añade funciones a la aplicación;
no es un nuevo release ni sustituye los ejecutables publicados de la v1.0.2.

## Abrir en Windows

1. Extrae TODO el ZIP en una carpeta nueva, distinta del candidato de Defender.
2. Cierra la aplicación instalada: esta prueba utiliza las mismas preferencias
   y los mismos proveedores configurados de G-Prompt Studio.
3. Haz doble clic en `INICIAR-VISUAL.cmd`. Requiere `py -3.12`, que ya instalaste.
   La primera vez instala dependencias en un entorno propio de esta carpeta;
   necesita Internet. Las siguientes abre la aplicación directamente.
4. En **Ajustes Extra**, pulsa **Crear desde imágenes · Inicio/final · Referencias**.

No compila ejecutables, cambia Defender, publica releases ni modifica el EXE instalado.
Los README y documentos de release originales describen la versión publicada,
no certifican esta prueba ni sus dependencias.

## Flujo

- **Imagen → prompt:** una referencia, idea opcional, conservar y cambiar.
- **Animar imagen:** una imagen y una acción; selecciona plataforma y modelo en el panel.
- **Inicio → final:** dos imágenes. A es inicio; B es final. Usa Intercambiar A/B para invertirlas.
- **Varias referencias:** de dos a cuatro imágenes. Asigna personaje, producto,
  escenario, estilo, iluminación o composición a cada una.

Pulsa **Analizar**, revisa y corrige el análisis, escribe tu idea y pulsa **Generar**.
La idea se conserva separada del análisis. No reutiliza automáticamente la salida anterior.
El formato, duración e idioma del prompt son independientes del idioma de explicación.
En animación/inicio-final la salida es vídeo. En Varias referencias puedes elegir
Imagen o Vídeo. El modelo se toma del selector del propio panel al pulsar Generar.

**Guardar proyecto** crea un `.gprompt` con imágenes, idea, análisis y resultado.
No incluye las claves API. Sí contiene tus imágenes y texto: comparte solo lo que quieras compartir.
**Abrir proyecto** abre otra ventana para preservar el trabajo que tengas sin guardar.
El modelo de destino se restaura si sigue disponible en el catálogo; si ya no está,
se selecciona el primero de la plataforma. Revisa los selectores al abrir un proyecto.

## Límites de esta entrega

- Es un generador de prompts: no renderiza imágenes ni vídeos.
- Las referencias múltiples se envían juntas en un panel con letras; el detalle
  fino puede perderse por reducción. No se promete identidad exacta.
- Utiliza la cadena de visión configurada en la aplicación, incluidos proveedores
  alternativos. Las llamadas pueden consumir cuota. El análisis muestra el motor usado.
- No certifica automáticamente si un modelo admite dos fotogramas o múltiples
  referencias. Las instrucciones piden indicar compatibilidad no confirmada.
- Los controles principales nuevos usan el sistema de traducción. Algunas ayudas,
  opciones y mensajes del espacio visual siguen en español.
- Pruebas automáticas realizadas en Linux; quedan pendientes la revisión visual en
  Windows y llamadas reales con tus proveedores. No se ha creado ni analizado un EXE nuevo.

## Cambios técnicos

`modules/visual_brief.py`: referencias, comparación conjunta, instrucciones, carga
limitada de imágenes, orientación EXIF y proyectos portátiles de escritura atómica.
`modules/visual_studio.py`: ventana con vista previa, roles, revisión, generación,
copiado, salida principal y proyectos. Captura las entradas antes del trabajo en
segundo plano; consulta las respuestas desde Tk sin acceder a widgets desde el worker.
`modules/core.py` y `modules/ui_builders.py`: entrada al nuevo panel.
`workers.py`: el límite de respuesta de visión de OpenRouter sube de 250 a 1500
tokens para permitir comparaciones; puede aumentar el coste de esas respuestas.
`modules/i18n.py`: traducciones de los nuevos botones y textos principales.
`tests/test_visual_brief.py`: pruebas de referencias, proyectos y ciclo asíncrono.
`tests/test_tools_analysis.py`: corrige una expectativa anterior que usaba un gris
literal, mientras la función utiliza el color semántico `P.TXT_MUTED`.

## Comprobación manual sugerida

1. Una imagen → análisis → corregir un detalle → generar. La idea no debe cambiar.
2. Inicio/final → comparar → invertir A/B. Se debe invalidar el análisis anterior.
3. Personaje + escenario + estilo → comprobar las funciones en el resultado.
4. Guardar proyecto, cerrar su ventana y volver a abrirlo: imágenes y texto se conservan.
5. Cerrar el panel durante una petición: la respuesta no debe intentar actualizarlo.
   Cerrar la ventana descarta la respuesta; una petición ya enviada puede seguir consumiendo cuota.

## Verificación automática de esta entrega

1426 pruebas superadas, 31 omitidas en Linux, incluidas 40 pruebas del espacio visual.
Ruff sin errores en todos los archivos Python modificados. Sin llamadas reales
a APIs ni comprobación visual de Tk en Windows.
