# Texto del release v1.0.0

Pega el bloque de abajo en el cuerpo del release de GitHub. Los hashes son
del build del 09-sep-2026 14:26 — **si regeneras, cámbialos** (los saca
`build_release.py` o `sha256sum *.exe` en la carpeta de distribución).

Sube como *assets*: `GPromptStudio-Setup-1.0.0.exe` y
`GPromptStudio-Portable-Onefile.exe`. La carpeta portable no, es lo mismo
que instala el Setup y tres opciones confunden.

---

## G-Prompt Studio v1.0.0

Suite de escritorio para escribir prompts de IA generativa —imagen, vídeo y
audio— adaptados al modelo concreto que vas a usar.

No es un chat con plantillas. Cada uno de los **276 modelos** del catálogo
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
| **[GPromptStudio-Setup-1.0.0.exe]** · 118 MB | **Recomendado.** Instalador, acceso directo y desinstalación limpia. No pide permisos de administrador |
| **[GPromptStudio-Portable-Onefile.exe]** · 167 MB | Un solo fichero, sin instalar. Arranca más lento |

Verifica el fichero antes de ejecutarlo si quieres (PowerShell):

```powershell
Get-FileHash .\GPromptStudio-Setup-1.0.0.exe -Algorithm SHA256
```

```
40f3ab05f6ac0d9597c99fea357f274ec6e1ae3a551eb617d343f5774c0caf28  GPromptStudio-Setup-1.0.0.exe
d11f32741865565acdbb814ec88732ce628ab76a861816e248958355fd6304b8  GPromptStudio-Portable-Onefile.exe
```

### ⚠️ Windows mostrará un aviso (SmartScreen)

Al abrirlo verás **"Windows protegió su PC"**. Es esperado: el ejecutable no
está firmado con un certificado de firma de código, que cuesta unos 300 €
al año. El aviso no dice que el programa sea peligroso — dice que Windows
no conoce a quien lo firma.

**Para abrirlo:** *Más información* → *Ejecutar de todas formas*.

Si prefieres no fiarte de mi palabra, compara el hash de arriba: si coincide,
el fichero es exactamente el que se publicó aquí.

### Qué trae

- **276 modelos con ficha propia** — 165 de imagen, 100 de vídeo, 11 de
  audio. Y encima de esos, los tuyos: si usas ComfyUI, los detecta y los
  clasifica solo
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

- Los once proveedores verificados uno a uno con keys reales: catálogo en
  vivo y una llamada real a cada modelo del desplegable. Si un modelo
  desaparece del catálogo de su proveedor, la app lo oculta sola
- ComfyUI: detección automática de la carpeta, y soporta que `models/` sea
  un enlace a otro disco
- 1.298 tests. Las dependencias pasan auditoría de CVEs en cada build

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
