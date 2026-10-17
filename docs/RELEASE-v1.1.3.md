<!--
BORRADOR de la 1.1.3 (17-oct-2026). Nada publicado.

Lo que todavía es de la 1.1.2 y se rehace con el build:
- Los dos hashes del bloque de PowerShell. Se quedan los de la 1.1.2 porque
  la web los sigue publicando y los candados exigen que cuadren con este
  texto; build_release.py avisa mientras no se cambien.
- Los tamaños (188 y 187 MB). build_release.py los compara con los ficheros.
- VirusTotal: marcado PENDIENTE; build_release.py avisa mientras quede alguno.

Falta, en este orden:
1. `py -3.10 build_release.py --yes` desde el último commit de esta rama.
2. Hashes, tamaños y VirusTotal aquí, en docs/LEEME-PRIMERO.txt y en
   docs/WEB-descarga.md / .en.md (los dos con los mismos hashes).
3. Borrador de release en GitHub con la etiqueta `v1.1.3` («create on
   publish»), el cuerpo de docs/RELEASE-CUERPO.md y los dos assets:
   `GPromptStudio-Setup-1.1.3.exe` y `GPromptStudio-Portable-Onefile.exe`.
4. Fusionar el PR en main y publicar enseguida: el botón del README apunta
   ya a v1.1.3 y da 404 hasta que la release exista.
5. Web (gprompt-studio.html y datos/proyectos.json: 279 = 170 + 101 + 8),
   About del repo, perfil y el aviso «Versión antigua» en la 1.1.2 (y que
   los de la 1.1.1, 1.1.0, 1.0.2, 1.0.1 y 1.0.0 apunten a la 1.1.3).
-->

---

## G-Prompt Studio v1.1.3

Suite de escritorio para escribir prompts de IA generativa —imagen, vídeo y
audio— adaptados al modelo concreto que vas a usar.

No es un chat con plantillas. Cada uno de los **279 modelos** del catálogo
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
| **[GPromptStudio-Setup-1.1.3.exe]** · 188 MB | **Recomendado.** Instalador, acceso directo y desinstalación limpia. No pide permisos de administrador |
| **[GPromptStudio-Portable-Onefile.exe]** · 187 MB | El mismo programa sin instalar nada. Borras el fichero y desaparece |

Las dos opciones son el mismo ejecutable: el instalador se limita a
colocarlo, crear los accesos directos y registrar la desinstalación. Tardan
lo mismo en abrir, unos 4-5 segundos.

Verifica el fichero antes de ejecutarlo si quieres (PowerShell):

```powershell
Get-FileHash .\GPromptStudio-Setup-1.1.3.exe -Algorithm SHA256
```

```
e18af11a2ffaf7389db52e7053c3a2528895670cf86371179f6304755856d85d  GPromptStudio-Setup-1.1.3.exe
ec1084ab1d1dd7a02d366311ee6d38f3d266c2b7e1c0823065d4ef1cd2f160c6  GPromptStudio-Portable-Onefile.exe
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
**PENDIENTE** y el portable **PENDIENTE**.

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

- **279 modelos con ficha propia** — 170 de imagen, 101 de vídeo, 8 de
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
