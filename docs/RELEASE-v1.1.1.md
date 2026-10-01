<!--
BORRADOR de la 1.1.1 (01-oct-2026). Nada publicado.

Lo que todavía es de la 1.1.0 y se rehace con el build:
- Los dos hashes del bloque de PowerShell. Se quedan los de la 1.1.0 porque
  la web los sigue publicando y los candados exigen que cuadren con este
  texto; build_release.py avisa mientras no se cambien.
- Los tamaños (188 y 187 MB). build_release.py los compara con los ficheros.
- VirusTotal: marcado PENDIENTE; build_release.py avisa mientras quede alguno.

Falta, en este orden:
1. `python build_release.py --yes` desde el último commit de esta rama.
2. Hashes, tamaños y VirusTotal aquí, en docs/LEEME-PRIMERO.txt y en
   docs/WEB-descarga.md / .en.md (los dos con los mismos hashes).
3. Borrador de release en GitHub con la etiqueta `v1.1.1` («create on
   publish»), el cuerpo de docs/RELEASE-CUERPO.md y los dos assets:
   `GPromptStudio-Setup-1.1.1.exe` y `GPromptStudio-Portable-Onefile.exe`.
4. Fusionar el PR en main y publicar enseguida: el botón del README apunta
   ya a v1.1.1 y da 404 hasta que la release exista.
5. Web (gprompt-studio.html y datos/proyectos.json: 273 = 166 + 99 + 8),
   About del repo, perfil y el aviso «Versión antigua» en la 1.1.0.
-->

---

## G-Prompt Studio v1.1.1

Suite de escritorio para escribir prompts de IA generativa —imagen, vídeo y
audio— adaptados al modelo concreto que vas a usar.

No es un chat con plantillas. Cada uno de los **273 modelos** del catálogo
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
| **[GPromptStudio-Setup-1.1.1.exe]** · 188 MB | **Recomendado.** Instalador, acceso directo y desinstalación limpia. No pide permisos de administrador |
| **[GPromptStudio-Portable-Onefile.exe]** · 187 MB | El mismo programa sin instalar nada. Borras el fichero y desaparece |

Las dos opciones son el mismo ejecutable: el instalador se limita a
colocarlo, crear los accesos directos y registrar la desinstalación. Tardan
lo mismo en abrir, unos 4-5 segundos.

Verifica el fichero antes de ejecutarlo si quieres (PowerShell):

```powershell
Get-FileHash .\GPromptStudio-Setup-1.1.1.exe -Algorithm SHA256
```

```
4104cb2257165e4c4819e1ee4e3be8970f98b712ca270b684889fd6e2f4e3aba  GPromptStudio-Setup-1.1.1.exe
0ae8f89a69b83f069c689325ef74d250b81a0f39e4fe7a9dcaf215da49d4622b  GPromptStudio-Portable-Onefile.exe
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

- **273 modelos con ficha propia** — 166 de imagen, 99 de vídeo, 8 de
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

**Qwen Image 2.1**, que SeaArt añadió el 21 de septiembre, justo cuando se
cerraba la 1.1.0. Es el Qwen ligero de Alibaba —7.000 millones de
parámetros en la parte que genera— y hace dos cosas en un solo modelo:
crear imágenes a partir de texto y editarlas por instrucciones, con hasta
3 imágenes de referencia. Según SeaArt, además genera y edita con fondo
transparente y recorta el sujeto de una foto.

La ficha sale del esquema oficial de SeaArt, no de suposiciones: hasta
2.000 caracteres, prompt negativo, 9 formatos (del 21:9 al 9:21), modos
Estándar y Calidad, hasta 8 imágenes por tanda y su muestreo por defecto
(Euler, 25 pasos, CFG 1). Un detalle que conviene saber: con CFG 1, que es
el valor por defecto, el negativo no hace nada. Si lo usas, sube el CFG a 2
o 3 en SeaArt.

**Seguridad.** La auditoría que pasa cada build encontró tres
vulnerabilidades en `urllib3`, una librería que la app usa por debajo para
parte de sus conexiones, publicadas después de la 1.1.0. Va actualizada a la
2.8.0, que las corrige.

**Lo demás no cambia** respecto a la
[1.1.0](https://github.com/Gustaafvito/gprompt-studio/releases/tag/v1.1.0):
mismo programa, mismos proveedores y mismas funciones. Si vienes de la
1.0.x, en sus notas tienes todo lo que trajo: «Crear desde imágenes»,
MiniMax H3 con su formato oficial y la revisión de los ocho menús.

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
