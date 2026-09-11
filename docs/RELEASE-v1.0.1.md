<!--
Pega el bloque de abajo en el cuerpo del release de GitHub. Los hashes los
rellena `build_release.py` al terminar el build — NO los copies de la 1.0.0.

Sube como *assets*: `GPromptStudio-Setup-1.0.1.exe` y
`GPromptStudio-Portable-Onefile.exe`.

Es un PARCHE: no hace falta repetir las capturas ni el texto largo de la
1.0.0. Quien entra a un release de parche viene a saber QUÉ se arregló.
-->

---

## G-Prompt Studio v1.0.1

Suite de escritorio para escribir prompts de IA generativa —imagen, vídeo y
audio— adaptados al modelo concreto que vas a usar.

No es un chat con plantillas. Cada uno de los **271 modelos** del catálogo
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

| | | VirusTotal |
|---|---|---|
| **[GPromptStudio-Setup-1.0.1.exe]** · 118 MB | **Recomendado.** Instalador, acceso directo y desinstalación limpia. No pide permisos de administrador | [**1/67**](https://www.virustotal.com/gui/file/0916fb761e988179a38f030f7acc85dc920c7be8663fd84e3e496f39830a6366) — ver abajo |
| **[GPromptStudio-Portable-Onefile.exe]** · 167 MB | Un solo fichero, sin instalar. Arranca más lento | [**2/68**](https://www.virustotal.com/gui/file/668fa06106bbb4d3bda4c5f527eb5252eb1dd34d29c1d70d3c6868608f4fe2f1) — ver abajo |

Verifica el fichero antes de ejecutarlo si quieres (PowerShell):

```powershell
Get-FileHash .\GPromptStudio-Setup-1.0.1.exe -Algorithm SHA256
```

```
0916fb761e988179a38f030f7acc85dc920c7be8663fd84e3e496f39830a6366  GPromptStudio-Setup-1.0.1.exe
668fa06106bbb4d3bda4c5f527eb5252eb1dd34d29c1d70d3c6868608f4fe2f1  GPromptStudio-Portable-Onefile.exe
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

Te lo cuento yo antes de que lo encuentres tú. El instalador lo marca
**1 motor de 67** (DeepInstinct) y el portable **2 de 68** (Bkav Pro y
Microsoft Defender).

**Ninguna de las tres detecciones nombra un malware real**, y eso es lo que
hay que mirar, no el número:

- Bkav Pro dice `W32.Malware.67AF34BE` — una etiqueta genérica derivada del
  propio fichero, no una familia conocida.
- Microsoft dice `Trojan:Win32/Wacatac.C!ml`. El sufijo **`!ml`** es la marca
  con la que Microsoft avisa de que el veredicto sale de un modelo
  estadístico y no de una firma, y *Wacatac* es su cajón de sastre para
  ejecutables sin firmar que le resultan sospechosos.
- DeepInstinct dice «MALICIOUS» a secas, sin nombre.

La prueba de que lo que molesta es el **empaquetado** y no el programa: el
mismo código exacto, metido en un instalador de Inno Setup en vez de en un
onefile de PyInstaller, **Microsoft no lo marca**. Es el mismo software, y
el veredicto cambia según cómo esté envuelto.

⚠️ **Si Defender te pone el portable en cuarentena, usa el instalador.** Es
la opción recomendada de todas formas, y Microsoft no lo señala.

Y si no quieres fiarte de nada de esto, están los dos análisis enlazados
arriba y el hash para comprobar que el fichero que has bajado es el mismo.

**Si te preocupa, usa el instalador**: es el mismo programa, no necesita
permisos de administrador y no arrastra ese falso positivo. Los dos informes
completos están enlazados arriba para que los mires tú.

### Qué trae

- **271 modelos con ficha propia** — 164 de imagen, 99 de vídeo, 8 de
  audio, en 13 plataformas. Y encima de esos, los tuyos: si usas ComfyUI,
  los detecta y los clasifica solo
- **GPT Image 2.5** (Flare y Sunburst) el mismo día del anuncio, por las
  dos vías: SeaArt y la API oficial de OpenAI
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

**Esta es una versión de parche.** Si ya tienes la 1.0.0 instalada, instala
encima: se conservan tus claves, tu historial, tus plantillas y tus modelos
de ComfyUI, que viven fuera del programa en `%USERPROFILE%\.arquitecto_prompts`.

**Arreglado: DeepSeek dejó de generar.** El 10 de septiembre DeepSeek publicó
V4.1 Flash y de paso le cambió el identificador al modelo —`deepseek-v4-flash`
pasó a llamarse `deepseek-flash`— sin anunciarlo. La 1.0.0 lleva el nombre
viejo como modelo por defecto, así que a quien tuviera DeepSeek configurado le
fallaba al generar. Ahora usa el identificador correcto, y si tenías el viejo
guardado se migra solo al abrir la app.

De paso se corrigió algo que llevaba roto desde julio sin que se notara: los
dos identificadores antiguos (`deepseek-chat` y `deepseek-reasoner`) migraban
al que acababa de morir, o sea de un modelo muerto a otro modelo muerto.

**Nuevo: tres estilos más para GPT Image 2.5.** La familia solo ofrecía
opciones de diseño comercial —Editorial, UI-Mockup, Poster-Typography— y
ninguna de arte. Se añaden **Anime**, **Comic** y **3D-Render**. Comic es el
que más se aprovecha de este modelo en concreto: las viñetas con bocadillos
exigen texto legible dentro de la imagen, que es justo donde gana.

**Botón de descarga en el README**, arriba del todo. Antes había que bajar
hasta la mitad de la página para encontrar cómo instalarlo.

Precio de DeepSeek actualizado a la tarifa nueva: 0,15 $ de entrada y 0,60 $
de salida por millón de tokens, fuera de horas punta.

1.401 tests. Las dependencias pasan auditoría de CVEs en cada build.

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
