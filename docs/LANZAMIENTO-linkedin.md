# Lanzamiento en LinkedIn

<!--
NOTAS PARA TI — no van en el post.

MECÁNICA, que decide más que el texto:

1. EL ENLACE VA EN EL PRIMER COMENTARIO, no en el cuerpo. LinkedIn
   penaliza los posts con enlaces externos: los muestra a mucha menos
   gente porque quiere retenerla dentro. Publicas el post, e
   inmediatamente escribes tú el primer comentario con el enlace.

2. LAS DOS PRIMERAS LÍNEAS SON TODO. LinkedIn corta el resto tras un
   «…ver más». Si esas dos líneas no enganchan, nadie despliega. Por eso
   el post empieza por el problema y no por «he creado una herramienta».

3. SUBE LA CAPTURA como imagen nativa (docs/capturas/01-pantalla-
   principal.png). Los posts con imagen propia rinden bastante mejor que
   los de solo texto, y aquí además demuestra que existe.

4. PUBLICA martes, miércoles o jueves por la mañana, hora española. Y
   quédate la primera hora contestando: LinkedIn mide la interacción
   temprana para decidir a cuánta gente se lo enseña.

5. TRES HASHTAGS COMO MUCHO. Más parece spam y no ayuda.

6. NO EDITES EL POST la primera hora. Editar reinicia parte del alcance.

POR QUÉ ESTE ÁNGULO: no abre con «he construido una herramienta» —eso lo
publica todo el mundo y no dice nada. Abre con un dato concreto y
verificable que además explica por qué la herramienta hacía falta. La
credibilidad viene de los números, y todos se pueden comprobar.
-->

## Post principal

> De los 11 proveedores de IA que conecté a mi herramienta, **los 11 tenían
> la lista de modelos podrida**. Modelos que ya no existen, otros que
> responden 404, y uno que llevaba cerrado desde julio.
>
> Lo descubrí porque me puse a verificarlos uno a uno con claves reales
> antes de publicar. Once de once.
>
> Llevo meses generando imagen y vídeo con IA, y siempre chocaba con lo
> mismo: cada modelo quiere el prompt de una forma distinta. Flux pide
> prosa, SDXL pide etiquetas, unos aceptan prompt negativo y otros lo
> ignoran, y cada uno tiene su límite de caracteres y su sampler.
>
> Tenía esas reglas repartidas entre notas, pestañas abiertas y capturas
> de pantalla. Y aun así escribía el prompt para el modelo equivocado.
>
> No encontré un sitio donde estuviera todo junto, así que lo construí.
>
> **G-Prompt Studio** es una aplicación de escritorio para Windows:
> escribes la idea en castellano, eliges el modelo, y sale el prompt con
> las reglas de ESE modelo.
>
> · 271 modelos de imagen, vídeo y audio, cada uno con su ficha
> · 13 proveedores de IA, incluidos Gemini y Groq, que son gratis
> · Si usas ComfyUI, detecta tus modelos locales y los clasifica solos
> · 1.337 tests automáticos y auditoría de dependencias en cada versión
>
> Es gratis, es código abierto con licencia Apache 2.0, y publico el hash
> SHA-256 de cada descarga para que puedas verificar que el fichero es el
> mío y nadie lo ha tocado.
>
> Lo he construido con el mismo criterio con el que audito un sistema:
> entender qué hace cada pieza, medirla y no fiarme de lo que no puedo
> verificar. De ahí salió lo de los 11 catálogos.
>
> Enlace de descarga en el primer comentario 👇
>
> #IAGenerativa #OpenSource #Ciberseguridad

## Primer comentario (lo escribes tú, nada más publicar)

> Descarga y código, los dos aquí:
> https://github.com/Gustaafvito/gprompt-studio
>
> Windows 10/11, no necesita Python. Con una clave gratuita de Gemini o
> Groq ya funciona entero.
>
> Si lo pruebas y algo falla, ábreme un issue: se arregla antes.

## Ángulo alternativo, por si prefieres el personal

Cambia las tres primeras líneas por esto y deja el resto igual:

> Me cansé de escribir el prompt para el modelo equivocado.
>
> Flux quiere prosa. SDXL quiere etiquetas. Uno acepta prompt negativo, el
> otro lo ignora. Cada uno tiene su límite de caracteres y su sampler, y
> yo tenía todo eso en notas sueltas.

Es más cercano y menos técnico. El principal engancha mejor a perfiles
técnicos; este a creadores. Elige según a quién quieras llegar.

<!--
QUÉ NO PONER, y por qué:

· «Después de meses de trabajo, por fin puedo anunciar…» — es la fórmula
  más gastada de LinkedIn. La gente la salta.
· Emojis en cada línea. Uno o dos, y donde signifiquen algo.
· «Revolucionario», «disruptivo», «game changer». Los números dicen más.
· No pidas «un like si te parece útil». Resta credibilidad y LinkedIn
  detecta la petición de interacción.
· No etiquetes a gente que no lo haya probado.

DESPUÉS DEL POST:

· Contesta a TODOS los comentarios, aunque sea un «gracias». Cuenta para
  el alcance y es de educación.
· Si alguien reporta un fallo, arréglalo y responde con el commit. Eso
  convierte una crítica en la mejor demostración de que mantienes lo que
  publicas.
· A la semana, un segundo post distinto: qué te han pedido, qué has
  arreglado. El seguimiento suele rendir más que el anuncio.
-->
