<!--
BORRADOR de la 1.1.2 (09-oct-2026). Nada publicado.

Lo que todavía es de la 1.1.1 y se rehace con el build:
- Los dos hashes del bloque de PowerShell. Se quedan los de la 1.1.1 porque
  la web los sigue publicando y los candados exigen que cuadren con este
  texto; build_release.py avisa mientras no se cambien.
- Los tamaños (188 y 187 MB). build_release.py los compara con los ficheros.
- VirusTotal: marcado PENDIENTE; build_release.py avisa mientras quede alguno.

Falta, en este orden:
1. `py -3.10 build_release.py --yes` desde el último commit de esta rama.
2. Hashes, tamaños y VirusTotal aquí, en docs/LEEME-PRIMERO.txt y en
   docs/WEB-descarga.md / .en.md (los dos con los mismos hashes).
3. Borrador de release en GitHub con la etiqueta `v1.1.2` («create on
   publish»), el cuerpo de docs/RELEASE-CUERPO.md y los dos assets:
   `GPromptStudio-Setup-1.1.2.exe` y `GPromptStudio-Portable-Onefile.exe`.
4. Fusionar el PR en main y publicar enseguida: el botón del README apunta
   ya a v1.1.2 y da 404 hasta que la release exista.
5. Web (gprompt-studio.html y datos/proyectos.json: 277 = 168 + 101 + 8),
   About del repo, perfil y el aviso «Versión antigua» en la 1.1.1 (y que
   los de la 1.1.0, 1.0.2, 1.0.1 y 1.0.0 apunten a la 1.1.2).
-->

---

## G-Prompt Studio v1.1.2

Suite de escritorio para escribir prompts de IA generativa —imagen, vídeo y
audio— adaptados al modelo concreto que vas a usar.

No es un chat con plantillas. Cada uno de los **277 modelos** del catálogo
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
| **[GPromptStudio-Setup-1.1.2.exe]** · 188 MB | **Recomendado.** Instalador, acceso directo y desinstalación limpia. No pide permisos de administrador |
| **[GPromptStudio-Portable-Onefile.exe]** · 187 MB | El mismo programa sin instalar nada. Borras el fichero y desaparece |

Las dos opciones son el mismo ejecutable: el instalador se limita a
colocarlo, crear los accesos directos y registrar la desinstalación. Tardan
lo mismo en abrir, unos 4-5 segundos.

Verifica el fichero antes de ejecutarlo si quieres (PowerShell):

```powershell
Get-FileHash .\GPromptStudio-Setup-1.1.2.exe -Algorithm SHA256
```

```
771bee4b26b9a33290a99bccad01bcb348d87f719c3bace16eaf986cd04f425c  GPromptStudio-Setup-1.1.2.exe
5c9d80f4fcff6175f8d4f1aa0d39dcfc1c7304daafb3a4107a8f2204f211b8e9  GPromptStudio-Portable-Onefile.exe
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

- **277 modelos con ficha propia** — 168 de imagen, 101 de vídeo, 8 de
  audio, en 13 plataformas. Y encima de esos, los tuyos: si usas ComfyUI,
  los detecta y los clasifica solo
- **Once cerebros** para redactar: DeepSeek, Claude, Gemini, Groq, Mistral,
  OpenAI, OpenRouter, Fireworks, xAI Grok, Perplexity y Together. Más
  **LM Studio y Ollama** si prefieres no salir de tu ordenador
- **ComfyUI automático**: encuentra tu carpeta sola, detecta tus checkpoints
  y los agrupa por familia (SDXL, Flux, SD 1.5, Pony, Illustrious, Qwen,
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

**Anima**, el modelo de anime de CircleStone Labs y Comfy Org, que SeaArt
ofrece como modelo oficial. Tiene 2.000 millones de parámetros, está hecho
sobre NVIDIA Cosmos y se centra en el anime —personajes, series y estilos
de artista—, aunque también hace otro arte que no sea foto. Fotorrealismo,
no: es a propósito.

La ficha sale del esquema oficial de SeaArt y de la guía del autor, no de
suposiciones. La app escribe tags de Danbooru en minúsculas y con espacios,
en el orden que él recomienda, con el prefijo de calidad y la etiqueta de
seguridad; pone los artistas con `@` delante, porque sin ella apenas se
notan; usa pesos más altos que en SDXL, como `(chibi:2)`; y parte de su
negativo oficial. Hasta 2.000 caracteres, 11 formatos y hasta 8 imágenes
por tanda.

En SeaArt tiene ocho versiones, y la que sale por defecto es la **Turbo**:
va con CFG 1 y de 8 a 12 pasos, y con CFG 1 el negativo no hace nada. La
**Base** y la **Aesthetic** piden de 30 a 50 pasos y un CFG de 3 a 6; con la
Aesthetic, mejor sin los tags `score_`. La ficha lo cuenta para que no
tengas que adivinarlo.

Un aviso: la licencia de Anima, la del modelo, es **no comercial**.

**Y si tienes Anima en ComfyUI**, ahora tiene su propio grupo. Antes se
trataba como un Illustrious más: el prompt no seguía sus reglas, y el
workflow del botón «🔧 Comfy» lo cargaba como un checkpoint de SDXL, así que
no funcionaba. Ahora lleva sus mismas reglas de prompt, los ajustes de la
versión Base (er_sde, 30 pasos, CFG 5) y un workflow con sus piezas: el
modelo de difusión, el codificador `qwen_3_06b_base` y el VAE de Qwen-Image.

**Generador de Dataset LoRA: dónde vas a entrenar.** Un desplegable nuevo,
«Entrenar en», con los destinos reales: G-Entrena (Anima, Krea 2, Qwen Image
2.1 y Z-Image, y también LTX 2.3 y MiniMax H3, que son de vídeo pero se
entrenan con imágenes), el entrenador de SeaArt (Anima, Krea 2, Flux.2, FLUX, Z
Image, Qwen Image, Wan 2.2, SDXL, Illustrious, Pony y SD 1.5), Higgsfield y
Magnific. Las descripciones de cada imagen se escriben como las pide ese
destino: tags, frases o una frase en lenguaje natural —«A photo of a woman
named…», como recomienda SeaArt—, y ahora llevan la palabra de clase («a
woman», «1girl»). Si el destino no usa descripciones, no se exportan. Y avisa
cuando el número de imágenes se sale de lo que recomienda.

**Y variedad en cada imagen.** Hasta ahora, un dataset de personaje repetía la
misma ropa y la misma luz de estudio en todas las imágenes, con cuatro fondos
lisos, y el LoRA acababa aprendiéndose la ropa y la luz como si fueran parte
del personaje. Ahora, en cada imagen cambian la ropa, el escenario (lugares
reales en vez de fondos de estudio), la expresión y la luz, y cada descripción
lo nombra para que el LoRA aprenda solo la cara y el pelo. Si la ropa es
parte del personaje, desmarcas «Variar ropa» y se queda la de la ficha. En
los paisajes cambian la hora del día y el tiempo; en los objetos, la luz; en
NSFW, la expresión y la luz.

**Gestor de LoRAs: cinco familias nuevas.** Anima, Krea 2, LTX, MiniMax H3 y
Qwen Image, junto a las de siempre, y todas en orden alfabético. Hasta ahora,
un LoRA de Anima solo podía guardarse como «Otra», y la app avisaba siempre
de «familia distinta» porque tampoco sabía reconocer un modelo Anima. Ahora
lo reconoce, también en tus modelos de ComfyUI. Y los LoRA de vídeo (LTX y
MiniMax H3) se comprueban también en el modo vídeo, que antes no miraba
ninguno.

**Lo demás no cambia** respecto a la
[1.1.1](https://github.com/Gustaafvito/gprompt-studio/releases/tag/v1.1.1):
mismo programa, mismos proveedores y mismas funciones. Si vienes de antes,
en sus notas tienes los cuatro modelos que trajo (Qwen Image 2.1, Nano
Banana 2.1, Vidu Q4 Preview y SeaArt Opera 2.0 Preview), y en las de la
1.1.0, «Crear desde imágenes» y la revisión de los ocho menús.

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
