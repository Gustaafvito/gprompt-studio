# Sección de descarga para gustaafvito.com

Texto listo para pegar en la web. Dos bloques: el de descarga y el del aviso
de Windows, que es el que más abandonos evita.

**Lo importante: el aviso va ANTES del botón, no después.** Quien se
encuentra la pantalla azul sin haberlo leído, cierra y no vuelve. Quien ya
sabe que va a salir, la pasa sin pensar.

---

## Bloque 1 — Descarga

> ### Descargar G-Prompt Studio
>
> Windows 10 u 11 (64 bits). No necesitas Python ni instalar nada más.
>
> **[⬇ Descargar el instalador (118 MB)]**
> ← enlazar al asset del release en GitHub
>
> ¿Prefieres no instalar nada? [Versión portable, un solo archivo (167 MB)]
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
> Get-FileHash .\GPromptStudio-Setup-1.0.0.exe -Algorithm SHA256
> ```
>
> Y si te gusta mirar el código, está entero
> [en GitHub](https://github.com/Gustaafvito/gprompt-studio) bajo licencia
> Apache 2.0.

---

## Bloque 3 — Si algún antivirus se queja (opcional)

Solo si te lo reportan. Tenerlo escrito de antemano ahorra discusiones.

> **¿Tu antivirus ha marcado el archivo?**
>
> Puede pasar con la versión portable de un solo fichero. Es un falso
> positivo conocido de este tipo de ejecutables: se descomprimen en una
> carpeta temporal al arrancar, que es también lo que hace cierto malware, y
> algunos motores heurísticos lo confunden.
>
> Si te preocupa, usa el **instalador** en lugar de la versión portable:
> tiene otra estructura y no da ese falso positivo. Y compara siempre el
> hash.

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
