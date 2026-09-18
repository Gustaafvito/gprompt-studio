"""El recurso VERSIONINFO que Windows lee del .exe.

18-sep-2026. Windows Defender empezó a **borrar** la aplicación instalada
—no a avisar: la borraba, junto con el acceso directo y la clave de
desinstalación— marcándola como `Trojan:Win32/Wacatac.C!ml`. El sufijo `!ml`
es la marca de Microsoft para un veredicto de modelo estadístico, no de una
firma, así que no hay código concreto que reconozca: es un perfil.

Y el `.exe` encajaba en ese perfil como un guante. Un ejecutable de Windows
**sin firmar y además sin ningún metadato** —sin nombre de producto, sin
empresa, sin versión, sin copyright— es exactamente lo que un modelo aprende
a puntuar mal, porque el software legítimo casi siempre los lleva y el
malware casi nunca se molesta. PyInstaller no los pone si no se los das.

Esto **no garantiza** que Defender deje de marcarlo: es una hipótesis con
fundamento, no una cura conocida. Pero es gratis, es correcto de todas formas
—un instalador serio enseña su versión en las propiedades del fichero— y
elimina una de las pocas variables que están en nuestra mano sin pagar un
certificado de firma.

La versión sale de `config.PUBLIC_VERSION` y de ningún otro sitio, como el
resto del proyecto: hay un candado (`tests/test_version_unica.py`) que exige
que todas las declaraciones coincidan.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

# 0x0C0A = español (España), 1200 = 0x04B0 = Unicode. La clave de la
# StringTable es la concatenación en hexadecimal de los dos.
_IDIOMA, _PAGINA = 0x0C0A, 1200
_CLAVE = f"{_IDIOMA:04x}{_PAGINA:04x}"

EMPRESA = "Gustaafvito"
PRODUCTO = "G-Prompt Studio"
COPYRIGHT = "Copyright 2026 Gustavo Luis Sánchez Escobar — Apache License 2.0"
DESCRIPCION = "Suite de ingeniería de prompts para IA generativa"


def _cuatro_numeros(version: str) -> tuple:
    """«1.0.1» → (1, 0, 1, 0). Windows exige cuatro componentes."""
    partes = [int(x) for x in version.split(".") if x.isdigit()]
    partes += [0] * (4 - len(partes))
    return tuple(partes[:4])


def contenido(version: str, nombre_exe: str) -> str:
    n = _cuatro_numeros(version)
    return f"""# Generado por pyinstaller_version.py — no editar a mano.
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={n},
    prodvers={n},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '{_CLAVE}',
        [StringStruct('CompanyName', '{EMPRESA}'),
         StringStruct('FileDescription', '{DESCRIPCION}'),
         StringStruct('FileVersion', '{version}'),
         StringStruct('InternalName', 'GPromptStudio'),
         StringStruct('LegalCopyright', '{COPYRIGHT}'),
         StringStruct('OriginalFilename', '{nombre_exe}'),
         StringStruct('ProductName', '{PRODUCTO}'),
         StringStruct('ProductVersion', '{version}')])
      ]),
    VarFileInfo([VarStruct('Translation', [{_IDIOMA}, {_PAGINA}])])
  ]
)
"""


def escribir(nombre_exe: str = "GPromptStudio.exe") -> str:
    """Deja el fichero en build/ y devuelve su ruta, para pasarla a EXE()."""
    import config

    destino = RAIZ / "build" / f"version-{Path(nombre_exe).stem}.txt"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido(config.PUBLIC_VERSION, nombre_exe),
                       encoding="utf-8")
    return str(destino)
