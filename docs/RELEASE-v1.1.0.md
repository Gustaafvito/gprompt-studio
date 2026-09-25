<!--
Build definitivo del 25-sep-2026 (build_release.py desde 777f1ba): hashes,
tamaños y VirusTotal ya son los de ESTOS dos ficheros. Si se regeneran, todo
eso cambia: hay que volver a analizarlos y rehacer los enlaces.

Falta, en este orden: fusionar el PR #1 en main, etiqueta `v1.1.0` («+ Create
new tag», no basta con escribirla), pegar `docs/RELEASE-CUERPO.md` y subir los
dos *assets*: `GPromptStudio-Setup-1.1.0.exe` y
`GPromptStudio-Portable-Onefile.exe`. Después, la página de descarga de la web.
-->

---

## G-Prompt Studio v1.1.0

Suite de escritorio para escribir prompts de IA generativa —imagen, vídeo y
audio— adaptados al modelo concreto que vas a usar.

No es un chat con plantillas. Cada uno de los **272 modelos** del catálogo
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
proveedores soportados.

### Descarga

| | |
|---|---|
| **[GPromptStudio-Setup-1.1.0.exe]** · 188 MB | **Recomendado.** Instalador, acceso directo y desinstalación limpia. No pide permisos de administrador |
| **[GPromptStudio-Portable-Onefile.exe]** · 187 MB | El mismo programa sin instalar nada. Borras el fichero y desaparece |

Las dos opciones son el mismo ejecutable: el instalador se limita a
colocarlo, crear los accesos directos y registrar la desinstalación. Tardan
lo mismo en abrir, unos 4-5 segundos.

Verifica el fichero antes de ejecutarlo si quieres (PowerShell):

```powershell
Get-FileHash .\GPromptStudio-Setup-1.1.0.exe -Algorithm SHA256
```

```
e08a66d7652d38f998d5d7a190f5e416f4cd80ff19e9cef47414e085ff225ef9  GPromptStudio-Setup-1.1.0.exe
95d8896656c8ff6f471b98501d44a8fda199eb03ebba999fb7c703e342cfe626  GPromptStudio-Portable-Onefile.exe
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
**[1 de 60](https://www.virustotal.com/gui/file/e08a66d7652d38f998d5d7a190f5e416f4cd80ff19e9cef47414e085ff225ef9)** y el portable
**[2 de 64](https://www.virustotal.com/gui/file/95d8896656c8ff6f471b98501d44a8fda199eb03ebba999fb7c703e342cfe626)**.
**Microsoft Defender no marca ninguno de los dos.**

Ninguna de las tres detecciones encuentra código malicioso. Arctic Wolf da un
veredicto genérico, «Unsafe», sin nombrar nada. Bkav Pro pone
`W32.Malware.A6C4837A`, una etiqueta derivada del propio fichero. Y Zillya
dice `Backdoor.XWorm.Win32.3294`: XWorm sí es un malware real, y justo por
eso lo explico abajo.

Fíjate además en el reparto: Arctic Wolf solo marca el instalador, y Bkav y
Zillya solo el portable. Es el mismo programa en dos envoltorios, y cada
motor puntúa el envoltorio, no el código.

Y sobre por qué pasa esto en general, que conviene saberlo:

Estos ejecutables se construyen con **PyInstaller**, y su componente de
arranque —el mismo binario precompilado que viene con la herramienta— lo
comparten muchas muestras de malware reales. Hay motores que reconocen ese
componente y no el código: por eso una de las etiquetas que aparece es
literalmente `XWorm`, que es un malware que también se empaqueta así.

Cuando un veredicto acaba en **`!ml`**, como el `Trojan:Win32/Wacatac.C!ml`
de Microsoft, es la propia marca del fabricante para decir que lo ha dicho
un modelo estadístico y no una firma. No hay código reconocido: hay un
perfil que encaja.

Si tu antivirus se queja, **compara el hash** con el publicado arriba. Si
coincide, el fichero es exactamente el que se publicó aquí, sin manipular. Y
el código está entero en este repositorio para que lo mires.

### Qué trae

- **272 modelos con ficha propia** — 165 de imagen, 99 de vídeo, 8 de
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

**Crear desde imágenes.** Una ventana nueva para cuando ya tienes las
imágenes: le das las de inicio, final y referencia, eliges qué es cada una
(personaje, escenario, estilo…) y la app las analiza y redacta el prompt a
partir de ellas. Se abre con el botón «🖼 Crear desde imágenes», junto a la
caja de la idea, o con `Ctrl+Shift+I`. Guarda cada proyecto con su historial
de versiones.

- **Tú eliges quién analiza las imágenes**, y esa elección se respeta: si el
  proveedor falla, la app te lo dice en vez de saltar a otro de pago sin
  avisar. Si prefieres Ollama, local y gratis, es para no gastar cuota.
- **De ahí, al Cortometraje.** Con las referencias ya preparadas, un botón
  lanza el guion por escenas sin volver a describir nada a mano. Cada
  referencia viaja con su etiqueta (`@ref1`, `@ref2`…), y de una referencia de
  estilo solo se lleva la estética. Si cambias las imágenes después de
  analizarlas, no te deja seguir con un análisis caducado.
- **El guion se revisa antes de enseñártelo**, en local y sin coste: número
  de escenas, tiempos encadenados y referencias que no existen.

**Seedream 5.0 Flash**, anunciado por SeaArt el 24 de septiembre: la
variante rápida de Seedream 5.0, unos 10-20 segundos por imagen, pensada
para iterar y para editar por instrucciones.

**El resultado se ve.** Con la ventana a su tamaño por defecto, el prompt
generado tenía una línea de alto: 30 píxeles de los 240 que necesita. Ahora
las pestañas y la caja de la idea ceden sitio, y si ni así cabe, las
pestañas se pliegan a su tira de títulos. Con el escalado de Windows al
125 %, la ventana ya no pide más alto que la pantalla.

**Nada se esconde al estrechar la ventana.** Reset, Setup, Última y Cargar
setup no se veían a su tamaño por defecto, y el menú Workflow tampoco.
Ahora lo que no cabe baja de línea.

**Más cosas:**

- El atajo `Ctrl+Shift+A` (analizar imagen) no funcionaba nunca. Ahora sí.
- `Ctrl+K` encuentra también «Crear desde imágenes» y el Cortometraje.
- El tutorial explica las dos herramientas nuevas, en español y en inglés,
  y el Modo educativo tiene sus fichas.
- Las cajas de texto llevan su rótulo: antes lo único que decía para qué
  eran era un texto gris que desaparecía al escribir.
- Claude Opus 5.5, y gpt-6-sol y gpt-6-luna de OpenAI. El modelo por defecto
  de OpenAI pasa a gpt-6-luna, más barato que el anterior.
- Al salir del Modo Focus, las pestañas no volvían. Arreglado.

**🔞 NSFW, mejor.** La detección automática no funcionaba: anunciaba que
activaba el modo NSFW y no lo hacía. Ahora entiende la idea en castellano y
en inglés, y la app sabe qué modelos filtran el contenido adulto (GPT Image,
Nano Banana, Veo, Midjourney…): con ellos el prompt se queda en sugerente
para que no te lo rechacen, y te avisa. Si eliges un modelo para adultos con
NSFW apagado, también te lo dice. Apagado, el negativo excluye la desnudez.

**⚡ Modo Brief por modo.** Sus reglas eran de anuncio de vídeo y se
aplicaban igual a una imagen fija. Ahora cada modo tiene las suyas: en
imagen, producto protagonista y hueco para el titular; en audio, una cuña
de 15-30 segundos. El interruptor está junto a Destino y, mientras esté
encendido, lo ves arriba.

**Destino** ya no pone un formato que el modelo no tiene. El concurso Anthum
sale de la lista.

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
