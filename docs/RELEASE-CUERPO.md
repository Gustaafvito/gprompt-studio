## G-Prompt Studio v1.1.3

Suite de escritorio para escribir prompts de IA generativa —imagen, vídeo y
audio— adaptados al modelo concreto que vas a usar.

No es un chat con plantillas. Cada uno de los **281 modelos** del catálogo
tiene su ficha: si escribe en prosa o en tags, cuántos caracteres acepta, si
usa prompt negativo, qué sampler le va bien y con qué CFG. La app redacta
respetando esas reglas, así que el prompt que sale funciona en el modelo que
has elegido, no "en general".

### Qué necesitas

Windows 10 u 11 de 64 bits y **una API key gratuita**. Nada más — no hace
falta Python ni instalar dependencias.

**Gemini** (Google) y **Groq** regalan key sin tarjeta y con límites
generosos; con cualquiera de las dos la app funciona al completo. Groq
responde en menos de un segundo, y es el más rápido de los once
proveedores en la nube.

### Descarga

| | |
|---|---|
| **[GPromptStudio-Setup-1.1.3.exe]** · 82 MB | **Recomendado.** Instalador, acceso directo y desinstalación limpia. No pide permisos de administrador |
| **[GPromptStudio-Portable-Onefile.exe]** · 81 MB | El mismo programa sin instalar nada. Borras el fichero y desaparece |

Las dos opciones son el mismo ejecutable: el instalador se limita a
colocarlo, crear los accesos directos y registrar la desinstalación. Tardan
lo mismo en abrir, unos 4-5 segundos.

Verifica el fichero antes de ejecutarlo si quieres (PowerShell):

```powershell
Get-FileHash .\GPromptStudio-Setup-1.1.3.exe -Algorithm SHA256
```

```
6c8a667f2fce58481796f30ae14c6f51868182afe66236860af954bc2a5ff007  GPromptStudio-Setup-1.1.3.exe
e80b54e493e8f27c4c40c61f2401b44b5e00f4b2852428f144a80ccfe98348ac  GPromptStudio-Portable-Onefile.exe
```

### ⚠️ Windows mostrará un aviso (SmartScreen)

Al abrirlo verás **"Windows protegió su PC"**. Es esperado: el ejecutable no
está firmado con un certificado de firma de código, que cuesta unos 300 €
al año. El aviso no dice que el programa sea peligroso — dice que Windows
no conoce a quien lo firma.

**Para abrirlo:** *Más información* → *Ejecutar de todas formas*.

Si prefieres no fiarte de mi palabra, compara el hash de arriba: si coincide,
el fichero es exactamente el que se publicó aquí.

### Sobre los avisos de los antivirus

Te lo cuento yo antes de que lo encuentres tú: el instalador sale
**[1 de 67](https://www.virustotal.com/gui/file/6c8a667f2fce58481796f30ae14c6f51868182afe66236860af954bc2a5ff007)** y el portable
**[1 de 67](https://www.virustotal.com/gui/file/e80b54e493e8f27c4c40c61f2401b44b5e00f4b2852428f144a80ccfe98348ac)**.
**Microsoft Defender no marca ninguno de los dos.**

Cada uno lo marca un motor distinto, y ninguno encuentra código malicioso.
En el instalador, DeepInstinct da «Malicious», el veredicto de su modelo de
aprendizaje profundo, sin nombrar ningún malware. En el portable, Bkav Pro
da `W32.Malware.FA956205`, una etiqueta derivada del propio fichero. Y cada
motor deja pasar la otra opción, que lleva dentro el mismo programa: lo que
puntúan es el envoltorio, no el código.

Y sobre por qué pasa esto en general, que conviene saberlo:

Estos ejecutables se construyen con **PyInstaller**, y su componente de
arranque —el mismo binario precompilado que viene con la herramienta— lo
comparten muchas muestras de malware reales. Hay motores que reconocen ese
componente y no el código: por eso una de las etiquetas que aparece a veces
es literalmente `XWorm`, que es un malware que también se empaqueta así.

Cuando un veredicto acaba en **`!ml`**, como el `Trojan:Win32/Wacatac.C!ml`
de Microsoft, es la propia marca del fabricante para decir que lo ha dicho
un modelo estadístico y no una firma. No hay código reconocido: hay un
perfil que encaja.

Si tu antivirus se queja, **compara el hash** con el publicado arriba. Si
coincide, el fichero es exactamente el que se publicó aquí, sin manipular. Y
el código está entero en este repositorio para que lo mires.

### Qué trae

- **281 modelos con ficha propia** — 171 de imagen, 102 de vídeo, 8 de
  audio, en 13 plataformas. Y encima de esos, los tuyos: si usas ComfyUI,
  los detecta y los clasifica solo
- **Once cerebros** para redactar: DeepSeek, Claude, Gemini, Groq, Mistral,
  OpenAI, OpenRouter, Fireworks, xAI Grok, Perplexity y Together. Más
  **LM Studio y Ollama** si prefieres no salir de tu ordenador
- **ComfyUI automático**: encuentra tu carpeta sola, detecta tus checkpoints
  y los agrupa por familia (SDXL, Flux, FLUX 3, SD 1.5, Pony, Illustrious, Qwen,
  Z-Image…) para inyectar a cada uno sus reglas
- Comparador de modelos, A/B testing, ADN visual, moodboards, dashboard,
  paleta de comandos (`Ctrl+K`), import/export JSON para Veo, Sora y Kling
- **Bilingüe** español/inglés, detecta el idioma de Windows

### Privacidad

Tus API keys se guardan cifradas en el **Windows Credential Manager**, o en
un fichero protegido con DPAPI que solo tu usuario puede descifrar. **La app
no envía nada a ningún servidor mío**: solo habla con los proveedores que tú
configures.

Ninguna key mía viaja en el paquete. Está verificado sobre los artefactos
reales, buscando los prefijos de todos los proveedores.

### Notas de esta versión

**FLUX 3 Image Klein**, el nuevo modelo abierto de Black Forest Labs: 5.600
millones de parámetros que crean y editan en un solo modelo, con hasta 10
imágenes de referencia y texto dentro de la imagen. BFL avisa de que no se
use nunca sin su *prompt upsampler*, otro modelo que convierte tu idea corta
en el caption largo y concreto con el que se entrenó FLUX 3; sin él, la
imagen sale genérica. La app no necesita ese modelo: redacta el prompt con
sus mismas instrucciones, las oficiales, copiadas tal cual. Escribe un solo
bloque de prosa en inglés —primero el tipo de imagen, luego la escena, la
luz y la cámara, y después cada sujeto con sus colores, sus materiales y su
sitio en el encuadre—, con el texto de la imagen entre comillas y sin
valoraciones. Y si lo que quieres es editar una imagen, usa las de edición:
qué cambia, cómo queda y qué se conserva.

Está en SeaArt, como «Flux.3 Image Klein», con la ficha de su esquema
oficial: hasta 2.000 caracteres, 9 formatos, hasta 3 imágenes para editar y
8 por tanda, 15 pasos y CFG 1. SeaArt muestra la casilla del negativo, pero
con CFG 1 no hace nada, así que la app no lo escribe: como pide BFL, lo que
no quieres se describe como lo que sí hay.

**Y si lo tienes en ComfyUI**, tiene grupo propio. Antes caía con Flux 2, y
el workflow del botón «🔧 Comfy» le ponía el codificador y el tipo de Flux 2,
que no son los suyos. Ahora lleva sus piezas —el codificador `qwen3vl_4b`
con el tipo `flux3` y el VAE `flux2-vae`— y el muestreo de las plantillas
oficiales (er_sde y simple). Y distingue las dos versiones: el **Klein**
destilado, con 16 pasos y sin CFG, y el **Klein Base**, con 50 pasos y CFG
3.5, que es el que sirve para entrenar LoRA. Ojo con los nombres: en los
primeros ficheros que publicó BFL, `flux3_image_klein_…`, con guion bajo,
era la Base, y en los de ahora la Base lleva «base» en el nombre. La app
reconoce los dos. El workflow no carga el upsampler de las plantillas (otro
modelo de 9.000 millones de parámetros, de 7 a 19 GB): el prompt ya llega
escrito.

Un aviso: la licencia de FLUX 3, la del modelo (FLUX Kommunity), permite el
uso no comercial, y las imágenes comerciales solo si facturas menos de 5
millones de dólares al año.

**Krea 3**, en SeaArt: un modelo pensado para producción, que genera desde
texto, edita por instrucciones y combina hasta 6 imágenes de referencia sin
perder lo importante —caras, la forma de un producto, sus etiquetas y sus
logotipos—. La app le escribe en prosa y, para editar, empieza por la
acción, nombra cada referencia por lo que contiene y cierra con lo que no
cambia. Sin negativo, hasta 2.000 caracteres, 11 formatos y hasta 8
imágenes por tanda.

**SeaArt Ultra 4.0**, en SeaArt desde el 23 de octubre, sobre Kling 4.0:
vídeos de 5 a 30 segundos en una sola generación, con audio estéreo nativo
—diálogo, ambiente y efectos—, en 720p o 1080p y en cuatro formatos, 21:9
incluido. Hace texto a vídeo, imagen a vídeo y Referencia, con hasta 10
imágenes y 5 vídeos. La app le escribe como pide la guía de Kling 4.0: qué
sale, los sujetos con sus rasgos, la acción por tramos con su tiempo («0–4s
— …»), la cámara aparte y el sonido con quién habla y cómo. Admite prompts
de hasta 11.000 caracteres y negativo.

**MOSS-Image**, en SeaArt: el modelo abierto de MOSI.AI (OpenMOSS), de 5.000
millones de parámetros, hecho para que el texto se lea bien y cada cosa
quede donde la pides: carteles, portadas e infografías con texto largo, en
inglés o en chino, fotorrealismo y anime. La app le escribe en inglés, con
la composición explícita y el texto entre comillas, y le pone su negativo
oficial. Hasta 2.000 caracteres, 9 formatos y LoRA de MOSS Image.

**El botón «🔧 Comfy», también en vídeo.** Hasta ahora solo montaba
workflows de imagen, y en vídeo exportaba el modelo de imagen que se
hubiera quedado elegido. Ahora parte de la plantilla oficial que trae tu
ComfyUI para cada modelo de vídeo —LTX 2.5 y 2.3, MiniMax H3, Wan 2.1 y 2.2
(con Animate, S2V, Fun Control y Fun Camera), SCAIL, Bernini y Kandinsky 5—
y le escribe el prompt, el negativo, la duración, el formato y tu fichero
del modelo, con el cargador que le toca si es GGUF. El mejorador de prompt
de la plantilla va apagado: el prompt ya llega escrito.

Y los modelos que parten de ficheros tuyos lo dicen en su ficha: el ref2va
de MiniMax H3 trabaja con imágenes de referencia; Animate, con la imagen
del personaje y un vídeo con el movimiento; S2V, con el audio de la voz… La
imagen que cargues en la app entra sola en su Load Image (se copia a la
carpeta input de ComfyUI), y lo que falte te lo pide al pulsar el botón. En
el ref2va, el workflow lleva tantas imágenes como nombre el prompt
(`<Picture 1>`, `<Picture 2>`…), hasta 9.

Para varias referencias, **«Crear desde imágenes»**: con el ref2va de
destino admite hasta 9 imágenes, escribe el prompt en el formato oficial de
MiniMax H3 con cada una numerada según su función (la A es `<Picture 1>`, la
B `<Picture 2>`…) y su paso «3. 🔧 Workflow ComfyUI» las mete en orden en
los Load Image. Con el fl2va, «Inicio → final» pone la segunda como último
fotograma. Y en la ventana principal, Img→Prompt en vídeo ya cuenta lo que
pasa —lo que escribas en la idea, o una acción que se inventa— en vez de
dejar al personaje quieto, y no corta los prompts largos.

**Dos arreglos** que salieron probando FLUX 3: el texto que tiene que salir
escrito en la imagen —un cartel que dice «ABIERTO»— ya no se traduce al
inglés con el resto del prompt, y el workflow de imagen sale en el formato
que eliges en la app, no siempre cuadrado.

**Por dentro**, la app se compila ahora con Python 3.12 y lleva Pillow 13,
que corrige 37 fallos de seguridad conocidos de la librería de imágenes —el
más serio, al abrir una imagen JPEG 2000 preparada a propósito—, y los
certificados raíz al día.

**Lo demás no cambia** respecto a la
[1.1.2](https://github.com/Gustaafvito/gprompt-studio/releases/tag/v1.1.2):
mismo programa, mismos proveedores y mismas funciones. Si vienes de antes,
en sus notas tienes Anima y el Generador de Dataset LoRA completo, con la
2ª ronda para que todas las imágenes salgan con la misma cara.

Tus claves, tu historial y tus plantillas se conservan al instalar encima:
viven fuera del programa, en `%USERPROFILE%\.arquitecto_prompts`.

### Licencia

Apache 2.0 — ver [LICENSE](LICENSE). Puedes usarla, modificarla y
redistribuirla, incluso comercialmente, conservando el aviso de copyright y
señalando los cambios que hagas.

---

**¿Algo no funciona?**
[Abre un issue](https://github.com/Gustaafvito/gprompt-studio/issues) y
adjunta el log (`%USERPROFILE%\.arquitecto_prompts\logs\gprompt.log`).

**¿Dudas o ideas?**
[Discussions](https://github.com/Gustaafvito/gprompt-studio/discussions).

Más en [gustaafvito.com](https://gustaafvito.com/).
