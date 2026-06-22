# 📦 Build & Distribución — G-Prompt Studio

Cómo generar un ejecutable Windows distribuible de la aplicación.

---

## TL;DR

```powershell
# Build estándar (carpeta dist/GPromptStudio/ con GPromptStudio.exe + DLLs)
python build.py

# .exe portable único (~3-5 seg al arrancar)
python build.py --onefile

# Build + instalador profesional con Inno Setup
python build.py --installer
```

---

## Requisitos

### 1. Para generar el .exe (obligatorio)

```powershell
pip install pyinstaller
```

Ya viene en `pyproject.toml` si lo instalas con `pip install -e ".[build]"`.

### 2. Para generar el instalador (opcional)

Descarga e instala **Inno Setup 6**:
👉 https://jrsoftware.org/isinfo.php

El script `build.py` busca `ISCC.exe` en:
- `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`
- `C:\Program Files\Inno Setup 6\ISCC.exe`
- Cualquier ruta en `PATH`

---

## Opciones de build

### A. Modo `onedir` (recomendado)

```powershell
python build.py
```

Genera: **`dist/GPromptStudio/`**

- Una carpeta con `GPromptStudio.exe` + DLLs sueltas.
- Inicio rápido (~1 seg).
- Tamaño total: ~80-150 MB.
- Distribuir como ZIP o instalador.

### B. Modo `onefile` (portable)

```powershell
python build.py --onefile
```

Genera: **`dist/GPromptStudio.exe`**

- Un solo `.exe` portable.
- Inicio más lento (~3-5 seg — extrae a `%TEMP%` cada vez).
- Tamaño: ~70-120 MB (un solo archivo).
- Más fácil de compartir, peor experiencia de uso.

### C. Instalador completo

```powershell
python build.py --installer
```

Genera primero `dist/GPromptStudio/` y luego compila Inno Setup para
producir: **`dist/installer/GPromptStudio-Setup-1.0.0.exe`**

- Asistente de instalación profesional (Siguiente / Aceptar términos / etc.).
- Crea accesos directos al menú inicio + opcional al escritorio.
- Desinstalador en Panel de Control.
- Multilenguaje (inglés + español).
- Tamaño: ~60-100 MB (LZMA2 comprime mejor que ZIP).

---

## Lo que se incluye en el .exe

| Tipo | Contenido | Tamaño aprox |
|---|---|---:|
| Código Python | Todo `app.py`, `modules/`, `api_clients.py`, etc. | ~10 MB |
| Datos | `data/*.json` (specs de modelos, estilos, glosario, tutorial) | ~2 MB |
| Dependencias | customtkinter, Pillow, requests, keyring, cryptography, pyperclip | ~60-100 MB |
| Python runtime | Intérprete embebido | ~15 MB |
| Docs | README.md, GUIA_ESTILOS.md, ESTRUCTURA.md | ~70 KB |

**Lo que NO se incluye y debe instalarse aparte:**
- `cv2` (OpenCV) y `mss` para la grabación de sesión vídeo — el .exe
  funciona sin ellos, solo deshabilita esa función. Si los quieres,
  añádelos a `hiddenimports` en `gprompt-studio.spec`.

---

## Configuración avanzada

### Cambiar versión

Edita estos dos sitios:

1. **`installer.iss`**:
   ```
   #define MyAppVersion "1.0.0"
   ```

2. **`build.py`** (opcional, solo afecta a `--version` si lo añades).

### Añadir icono custom

1. Crea o consigue un `.ico` (256x256 recomendado).
2. Guárdalo como `assets/icon.ico` en la raíz del proyecto.
3. Descomenta en `gprompt-studio.spec`:
   ```python
   icon='assets/icon.ico',
   ```
4. Descomenta en `installer.iss`:
   ```
   SetupIconFile=assets/icon.ico
   ```

### Reducir tamaño

PyInstaller ya está configurado para excluir librerías pesadas
innecesarias (matplotlib, scipy, pandas, jupyter, IPython, pytest).

Para comprimir más, instala **UPX**:
👉 https://upx.github.io/

UPX comprime DLLs y binarios. El spec ya tiene `upx=True`.

### Limpiar build previo

```powershell
python build.py --clean
```

O manualmente:
```powershell
rm -rf dist build
```

---

## Antes de hacer un build oficial

Lista de comprobaciones rápidas:

- [ ] `python -m pytest tests/ -q` → todo verde ✅
- [ ] `python -c "import app; print('OK')"` → OK
- [ ] Working tree limpio (`git status`)
- [ ] Versión actualizada en `installer.iss`
- [ ] `HANDOFF.md` actualizado con cambios desde el último build
- [ ] Probar el .exe resultante antes de distribuir:
  ```powershell
  dist\GPromptStudio\GPromptStudio.exe
  ```

---

## Solución de problemas

### "ModuleNotFoundError" al ejecutar el .exe

PyInstaller no detectó un import dinámico. Añádelo a `hiddenimports` en
`gprompt-studio.spec` y vuelve a buildear.

Identifícalo con:
```powershell
# Ver qué falta exactamente cuando lanzas el .exe
dist\GPromptStudio\GPromptStudio.exe
```

### Tarda demasiado en arrancar (modo onefile)

Normal: PyInstaller `--onefile` extrae todo a `%TEMP%` cada vez. Usa
`onedir` para arranque inmediato.

### "Failed to load Python DLL"

Suele pasar por antivirus que cuarentena el `.exe`. Añade exclusión o
firma el .exe.

### Falta `tcl/tk` o customtkinter pierde estilos

El spec ya incluye `collect_data_files('customtkinter')`. Si aún falla,
verifica que la versión instalada de `customtkinter` es la misma con
la que PyInstaller buildea.

### Inno Setup no se encuentra

Edita `INNO_PATHS` en `build.py` con la ruta real de tu instalación.

---

## Distribución

Después del build tienes 3 opciones para compartir:

| Método | Ventajas | Desventajas |
|---|---|---|
| Subir `.exe` portable (onefile) | Un archivo, sin instalación | Arranca lento, antivirus a veces se queja |
| Subir ZIP de `dist/GPromptStudio/` | Arranque rápido | El usuario debe descomprimir y crear acceso directo |
| **Subir instalador Inno Setup** | Profesional, accesos directos automáticos, desinstalador | Requiere "Permitir" en SmartScreen al ejecutar |

Para evitar la advertencia de SmartScreen necesitas **firmar el .exe**
con un certificado de code-signing (Authenticode). Es de pago (~150-400
€/año). Sin firmar, los usuarios verán "Windows protegió tu PC" y
tendrán que pulsar "Más info → Ejecutar de todas formas".

---

## Code-signing (Authenticode)

`build.py` firma automáticamente el `.exe` y el instalador **si** hay un
certificado configurado por variables de entorno. Si no, el build sigue
funcionando igual, solo sin firmar (no-op informativo). Nunca se
hardcodea ningún secreto en el repo.

### Requisitos

- Un certificado de code-signing válido (`.pfx`/`.p12`) o uno ya
  importado en el almacén de Windows.
- `signtool.exe` (viene con el **Windows 10/11 SDK**). `build.py` lo
  busca en `PATH` y en `C:\Program Files (x86)\Windows Kits\10\bin\...`.

### Variables de entorno

| Variable | Para qué |
|---|---|
| `GPROMPT_SIGN_CERT` | Ruta a un `.pfx`/`.p12` (opción A) |
| `GPROMPT_SIGN_PASSWORD` | Contraseña del `.pfx` (opcional) |
| `GPROMPT_SIGN_THUMBPRINT` | Huella SHA1 de un cert ya en el almacén (opción B) |
| `GPROMPT_SIGN_TIMESTAMP` | URL de sellado de tiempo RFC3161 (default `http://timestamp.digicert.com`) |

Define **CERT** (opción A) **o** **THUMBPRINT** (opción B), no ambos.

### Ejemplo (PowerShell)

```powershell
# Opción A: firmar con un .pfx
$env:GPROMPT_SIGN_CERT = "C:\ruta\a\mi-cert.pfx"
$env:GPROMPT_SIGN_PASSWORD = "********"
python build.py --installer    # firma el .exe y el instalador

# Opción B: cert ya importado en el almacén
$env:GPROMPT_SIGN_THUMBPRINT = "a1b2c3d4e5f6...."
python build.py --installer
```

> ⚠️ No pongas estas variables en el repo ni en scripts versionados.
> Úsalas solo en la sesión de build (o en un secreto de CI). La firma
> usa SHA-256 + sellado de tiempo, así que el binario sigue siendo
> válido aunque el certificado caduque después.

Si hay certificado pero falta `signtool.exe`, o la firma falla,
`build.py` avisa y continúa generando un build **sin firmar** (no aborta).
