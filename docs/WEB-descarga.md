# Sección de descarga para gustaafvito.com

Versión en inglés: [`WEB-descarga.en.md`](WEB-descarga.en.md). Las dos
tienen que decir lo mismo — dos páginas de descarga que discrepan en el
tamaño, el hash o el resultado de VirusTotal son peor que una sola.

Texto listo para pegar en la web. Dos bloques: el de descarga y el del aviso
de Windows, que es el que más abandonos evita.

Para la **portada** hay algo aparte: [`WEB-destacado.html`](WEB-destacado.html),
una banda para poner entre el titular y «#01 Proyectos». Este fichero es
para la página de descarga; ese es para el escaparate.

**Lo importante: el aviso va ANTES del botón, no después.** Quien se
encuentra la pantalla azul sin haberlo leído, cierra y no vuelve. Quien ya
sabe que va a salir, la pasa sin pensar.

**Ya está publicado**, el 18-sep-2026, en
`gustaafvito-web/gprompt-studio.html`. Este fichero es la fuente del texto:
si cambias algo aquí, llévalo también a esa página — y al revés. Estuvo nueve
días escrito sin llegar a la web, que es la forma más tonta de perder el
trabajo.

---

## Bloque 1 — Descarga

> ### Descargar G-Prompt Studio
>
> Windows 10 u 11 (64 bits). No necesitas Python ni instalar nada más.
>
> **[⬇ Descargar el instalador (188 MB)]**
> ← enlazar al asset del release en GitHub
>
> ¿Prefieres no instalar nada? [Versión portable, un solo archivo (187 MB)]
>
> Para empezar solo necesitas una **API key gratuita** de
> [Gemini](https://aistudio.google.com/apikey) o
> [Groq](https://console.groq.com/keys). Las dos son gratis, sin tarjeta, y
> con cualquiera de las dos la app funciona al completo.

---

## Bloque 2 — El aviso de Windows

Ponlo justo debajo del botón, visible sin desplegar nada. Si tu web permite
un acordeón, que el título se vea siempre y el detalle se despliegue.

> ### ⚠️ Windows te mostrará un aviso al abrirlo
>
> Verás una pantalla azul que dice **"Windows protegió su PC"**. Es normal y
> esperado.
>
> **Para abrirlo:** pulsa *Más información* y luego *Ejecutar de todas
> formas*.
>
> **Por qué sale.** Windows avisa de cualquier programa que no esté firmado
> con un certificado de firma de código. Esos certificados cuestan unos
> 300 € al año y, además, Microsoft solo los vende a empresas de EE. UU. y
> Canadá o con tres años de historial verificable. G-Prompt Studio es un
> proyecto de una persona.
>
> El aviso **no dice que el programa sea peligroso**. Dice que Windows no
> conoce a quien lo firma. Es la misma pantalla que sale con casi cualquier
> herramienta independiente.
>
> **Si no quieres fiarte de mi palabra**, no hace falta. Cada descarga
> publica su huella SHA-256 en
> [la página del release](https://github.com/Gustaafvito/gprompt-studio/releases).
> Comprueba que coincide con la del archivo que has bajado y sabrás que es
> exactamente el que publiqué, sin manipular:
>
> ```powershell
> Get-FileHash .\GPromptStudio-Setup-1.0.2.exe -Algorithm SHA256
> ```
>
> ```
> da63460f6ca202638c7b60b0ed205f47a29b11755ecb423d54c383f66e26effb  GPromptStudio-Setup-1.0.2.exe
> 614fcb74a646c52d2ec3a416e8e6e91045087647ec84d7254f2e0d682d1850cc  GPromptStudio-Portable-Onefile.exe
> ```
>
> Y si te gusta mirar el código, está entero
> [en GitHub](https://github.com/Gustaafvito/gprompt-studio) bajo licencia
> Apache 2.0.

---

## Bloque 3 — Si algún antivirus se queja (opcional)

Solo si te lo reportan. Tenerlo escrito de antemano ahorra discusiones.

> **Analizado en VirusTotal, y te cuento el resultado entero**
>
> - **Instalador:** [limpio, 0 de 67 motores](https://www.virustotal.com/gui/file/da63460f6ca202638c7b60b0ed205f47a29b11755ecb423d54c383f66e26effb)
> - **Portable de un solo fichero:** [1 de 66](https://www.virustotal.com/gui/file/614fcb74a646c52d2ec3a416e8e6e91045087647ec84d7254f2e0d682d1850cc) — Bkav Pro
>
> **Microsoft Defender no marca ninguno de los dos.**
>
> **La única detección que queda no nombra un malware real**, y eso importa
> más que el número: Bkav Pro dice `W32.Malware.62456B6B`, una etiqueta
> genérica derivada del propio fichero, no una familia conocida.
>
> Lo que puntúan los antivirus es el **empaquetado**, no el programa. La
> prueba está en la propia 1.0.2: el mismo código exacto sale limpio del todo
> metido en el instalador y con una detección metido en un fichero único.
> Mismo software, distinto envoltorio, distinto veredicto.
>
> **Si tu antivirus se queja del portable, baja el instalador**, que es la
> opción recomendada de todas formas. Y compara el hash en cualquier caso.

---

## Bloque 4 — Dudas y soporte

> ### ¿Dudas o algo no funciona?
>
> - **Fallos:** [abre un issue en
>   GitHub](https://github.com/Gustaafvito/gprompt-studio/issues) y adjunta
>   el log, que está en
>   `%USERPROFILE%\.arquitecto_prompts\logs\gprompt.log`
> - **Dudas e ideas:**
>   [Discussions](https://github.com/Gustaafvito/gprompt-studio/discussions)
> - **Sígueme:** [Instagram](https://www.instagram.com/gustaafvito.creador.ia)
>   · [TikTok](https://www.tiktok.com/@gustaafvito.creador.ia) ·
>   [YouTube](https://www.youtube.com/@GustaafvitocreadorIA)

Si creas un correo del dominio (`hola@gustaafvito.com`), añádelo aquí. Si el
hosting no da buzones, **Cloudflare Email Routing** reenvía gratis a tu Gmail
sin exponerlo.

⚠️ **NO pongas el Gmail personal en la web ni en el README.** Los bots
cosechan direcciones de páginas publicas en cuestion de dias y eso no se
deshace: un alias del dominio se puede borrar y rehacer, una cuenta personal
no. Ademas contradiria el trabajo de sacar el email de los 577 commits.


<!--
## Recordatorios para ti

- **Los hashes cambian en cada build.** Si regeneras los .exe, actualiza la
  web y el release. `build_release.py` te avisa si el LEEME se desfasa, pero
  los hashes de la web tienes que cambiarlos a mano
- **Enlaza los botones a los assets del release de GitHub**, no subas los
  270 MB a tu hosting: GitHub los sirve gratis y sin límite de tráfico
- Cuando reportes el falso positivo a Microsoft
  (`microsoft.com/wdsi/filesubmission`, opción *Software developer*) y lo
  acepten, Defender deja de marcarlo para todos. Es gratis y tarda 1-3 días
- SmartScreen **acumula reputación con las descargas**: cuanta más gente lo
  instale sin incidencias, más se suaviza el aviso por sí solo
-->
