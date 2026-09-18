## G-Prompt Studio v1.0.2

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

| | |
|---|---|
| **[GPromptStudio-Setup-1.0.2.exe]** · 179 MB | **Recomendado.** Instalador, acceso directo y desinstalación limpia. No pide permisos de administrador |
| **[GPromptStudio-Portable-Onefile.exe]** · 186 MB | El mismo programa sin instalar nada. Borras el fichero y desaparece |

Desde esta versión **las dos opciones son el mismo ejecutable**: el
instalador se limita a colocarlo, crear los accesos directos y registrar la
desinstalación. Tardan lo mismo en abrir, unos 4-5 segundos.

Verifica el fichero antes de ejecutarlo si quieres (PowerShell):

```powershell
Get-FileHash .\GPromptStudio-Setup-1.0.2.exe -Algorithm SHA256
```

```
da63460f6ca202638c7b60b0ed205f47a29b11755ecb423d54c383f66e26effb  GPromptStudio-Setup-1.0.2.exe
614fcb74a646c52d2ec3a416e8e6e91045087647ec84d7254f2e0d682d1850cc  GPromptStudio-Portable-Onefile.exe
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

Te lo cuento yo antes de que lo encuentres tú, y esta vez son buenas
noticias: el instalador sale **[limpio, 0 de 67](https://www.virustotal.com/gui/file/da63460f6ca202638c7b60b0ed205f47a29b11755ecb423d54c383f66e26effb)** y el portable
**[1 de 66](https://www.virustotal.com/gui/file/614fcb74a646c52d2ec3a416e8e6e91045087647ec84d7254f2e0d682d1850cc)**, un único motor minoritario. **Microsoft Defender no
marca ninguno de los dos.**

Para comparar: la 1.0.1 iba 1/67 y 2/68, y el ejecutable que dejaba
instalado —que nunca llegó a analizarse— 5 de 69, con Microsoft dentro.

La detección que queda, `W32.Malware.62456B6B` de Bkav Pro, es una etiqueta
genérica derivada del propio fichero: no nombra ningún malware conocido.

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

**En la 1.0.1 esto tuvo consecuencias reales**, y por eso existe esta
versión: Windows Defender no avisaba, **borraba** el programa después de
instalarlo. La 1.0.2 se empaqueta de otra forma, y con ella Defender lo
deja en paz.

Si tu antivirus se queja igualmente, **compara el hash** con el publicado
arriba. Si coincide, el fichero es exactamente el que se publicó aquí, sin
manipular. Y el código está entero en este repositorio para que lo mires.

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

**Si tienes la 1.0.1 instalada, actualiza.** Windows Defender estaba
**borrando** la aplicación después de instalarla —el ejecutable, el acceso
directo y la entrada de desinstalación— sin más explicación que un error al
abrirla. Si te pasó, no era cosa tuya ni de tu equipo.

**Qué pasaba.** El instalador pasaba los análisis sin problema, pero el
programa que dejaba en disco es otro fichero distinto, y ese nunca se había
analizado. Defender lo marcaba como `Trojan:Win32/Wacatac.C!ml`. El sufijo
`!ml` significa que el veredicto sale de un modelo estadístico y no de una
firma: no hay código que reconocer, hay un perfil que encaja.

**Y encajaba por una razón tonta.** El ejecutable no llevaba **ningún
metadato**: ni nombre de producto, ni empresa, ni versión, ni copyright.
PyInstaller no los pone si no se los pides. Un ejecutable sin firmar y además
anónimo es justo lo que esos modelos aprenden a marcar, porque el software
legítimo casi siempre los lleva.

Ahora el `.exe` se identifica: si miras sus propiedades en Windows verás
producto, versión y copyright. Tras el cambio, el build sobrevive a un
análisis explícito de Defender que antes lo borraba.

También se apagó la compresión UPX en la configuración de empaquetado. No
estaba haciendo nada —UPX no está instalado— pero es otro disparador conocido
de falso positivo y se habría activado sola el día que alguien lo instalara.

**Lo demás no cambia** respecto a la 1.0.1: mismo catálogo, mismos modelos,
mismos proveedores. Tus claves, tu historial y tus plantillas se conservan al
instalar encima: viven fuera del programa, en
`%USERPROFILE%\.arquitecto_prompts`.

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
