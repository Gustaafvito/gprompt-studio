# Política de seguridad

## Cómo reportar un fallo

**No abras un issue público para un fallo de seguridad.** Escríbeme por
privado desde [gustaafvito.com](https://gustaafvito.com/) o usa el botón
**Report a vulnerability** de la pestaña *Security* de este repositorio.

Dame margen para corregirlo antes de que sea público. Contesto en un par de
días; si en una semana no he dado señales, insiste — se me habrá pasado, no
te estoy ignorando.

Cuando esté corregido, si quieres te acredito en las notas de la versión.

## Qué versiones se mantienen

| Versión | Estado |
|---|---|
| 1.0.x | Se corrige |
| anteriores | No |

Es un proyecto de una persona: se mantiene la última versión publicada.

## Qué cuenta como fallo de seguridad aquí

Esta es una **aplicación de escritorio** que habla con APIs de terceros. Lo
que de verdad importa:

- **Fuga de claves API.** Se guardan en el Credential Manager de Windows, o
  cifradas con DPAPI en `~/.arquitecto_prompts/keys.json`. Si encuentras una
  forma de que acaben en un log, en el portapapeles, en una petición de red
  o dentro del ejecutable, eso es un fallo serio y quiero saberlo.
- **Ejecución de código** a partir de un fichero de datos: un
  `mis_modelos_comfy.json` manipulado, un JSON de `~/.arquitecto_prompts/data/`,
  una plantilla importada.
- **Escritura fuera de la carpeta de datos** al importar o exportar.
- **Cualquier conexión a un servidor que no sea un proveedor configurado por
  el usuario.** La app no debe hablar con ningún servidor mío.

## Qué NO es un fallo de seguridad

- **El aviso de SmartScreen al instalar.** El ejecutable no está firmado
  porque el certificado cuesta unos 300 € al año y Microsoft solo los vende
  a empresas de EE. UU. y Canadá o con tres años de historial. Está
  explicado en el README, y cada descarga publica su hash SHA-256 para que
  puedas verificarla.
- **Los avisos de VirusTotal.** En la 1.0.1: el instalador **1 de 67**
  (DeepInstinct) y el portable **2 de 68** (Bkav Pro y Microsoft
  Defender). Publico los dos porque cualquiera los comprueba en treinta
  segundos con el hash que doy yo mismo.
  **Ninguna de las tres detecciones nombra un malware real.** La de Bkav,
  `W32.Malware.67AF34BE`, es una etiqueta genérica derivada del propio
  fichero. La de Microsoft, `Trojan:Win32/Wacatac.C!ml`, lleva el sufijo
  **`!ml`** — la marca con la que Microsoft indica que el veredicto sale de
  un modelo estadístico y no de una firma— y *Wacatac* es su cajón de sastre
  para ejecutables sin firmar que le resultan raros.
  La prueba de que es el **empaquetado** y no el programa: el mismo código,
  empaquetado con Inno Setup en vez de PyInstaller, **Microsoft no lo marca**.
  ⚠️ Consecuencia práctica: Defender puede poner el portable en cuarentena.
  Si te pasa, usa el instalador.
- **Que tu clave API se gaste.** La app usa la clave que tú configuras
  contra el proveedor que tú eliges. Cada uno paga la suya.

## Lo que ya se hace

- Las dependencias que viajan dentro del `.exe` pasan **`pip-audit`** en
  cada build.
- Escrituras atómicas (`tmp` + `rename`) en todos los ficheros de datos.
- Ningún secreto en el repositorio: `.env` y las claves están en
  `.gitignore`, y se verifica sobre los artefactos construidos —no sobre la
  intención— buscando los prefijos de todos los proveedores.
