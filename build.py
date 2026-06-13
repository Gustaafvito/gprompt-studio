#!/usr/bin/env python
"""Script de build para G-Prompt Studio.

Genera el .exe Windows usando PyInstaller con el spec definido en
gprompt-studio.spec. Opcionalmente lanza Inno Setup para producir el
instalador completo.

Uso:
    python build.py              # Build estandar (onedir -> dist/GPromptStudio/)
    python build.py --onefile    # .exe portable unico (mas lento al arrancar)
    python build.py --installer  # Build + Inno Setup -> instalador
    python build.py --clean      # Borra dist/ y build/ antes
    python build.py --clean-cache  # --clean + borra __pycache__/ recursivo
                                   # (necesario tras cambios en .py si
                                   # PyInstaller cachea bytecode viejo)
    python build.py --help

Requisitos:
    pip install pyinstaller

Para el instalador necesitas Inno Setup 6 instalado:
    https://jrsoftware.org/isinfo.php
    El script asume que ISCC.exe esta en el PATH o en la ruta estandar
    "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe".
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Forzar UTF-8 en stdout/stderr para evitar UnicodeEncodeError en consolas cp1252
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    try: sys.stderr.reconfigure(encoding="utf-8")
    except Exception: pass

ROOT = Path(__file__).parent.resolve()
SPEC = ROOT / "gprompt-studio.spec"
DIST = ROOT / "dist"
BUILD = ROOT / "build"
ISS = ROOT / "installer.iss"

INNO_PATHS = [
    "ISCC",
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
    # Instalación por usuario vía winget (~AppData\Local)
    os.path.expanduser(r"~\AppData\Local\Programs\Inno Setup 6\ISCC.exe"),
]


# Regex que captura "C:\Users\<algo>\..." o "/home/<algo>/..." en cualquier
# parte de un string — usado para limpiar el output de subprocesos.
_ABS_PATH_RE = re.compile(r"([A-Z]:\\Users\\[^\\\s'\"]+|/home/[^/\s'\"]+|/Users/[^/\s'\"]+)\\?")


def _print_scrubbed(text):
    """Imprime `text` con paths personales reemplazados por '~'.

    Convierte 'C:\\Users\\gusta\\AppData\\...\\foo.py' en '~\\AppData\\...\\foo.py'.
    Si el path está dentro del proyecto, lo deja relativo al proyecto.
    """
    if not text:
        return
    cleaned = text
    # 1. Reemplazar el ROOT del proyecto por nada (path queda relativo)
    root_str = str(ROOT)
    cleaned = cleaned.replace(root_str + "\\", "")
    cleaned = cleaned.replace(root_str + "/", "")
    cleaned = cleaned.replace(root_str, ".")
    # 2. Reemplazar C:\Users\<nombre> por ~ (anonimiza al usuario)
    cleaned = _ABS_PATH_RE.sub("~", cleaned)
    print(cleaned, end="" if cleaned.endswith("\n") else "\n")


def rel(path):
    """Devuelve `path` relativo a ROOT si está dentro del proyecto, o el
    último componente del path si está fuera (típico: ejecutables externos
    como pyinstaller o ISCC.exe instalados en %APPDATA% o Program Files).

    Mantiene la consola limpia sin paths absolutos tipo
    "C:\\Users\\<nombre>\\...\\proyecto\\..." que delatan datos personales.
    """
    try:
        p = Path(path)
        # Si es un path al ejecutable de un comando externo, devolver
        # solo el nombre (pyinstaller.exe, ISCC.exe, python.exe)
        if not p.is_absolute() or ROOT in p.parents or p == ROOT:
            return str(p.relative_to(ROOT)) if p.is_absolute() else str(p)
        return p.name
    except (ValueError, TypeError):
        return str(path)


def log(msg, color=""):
    """Imprime mensaje con color ANSI (si terminal lo soporta)."""
    colors = {"green": "\033[92m", "red": "\033[91m", "yellow": "\033[93m",
              "blue": "\033[94m", "reset": "\033[0m"}
    if color and sys.stdout.isatty():
        print(f"{colors.get(color, '')}{msg}{colors['reset']}")
    else:
        print(msg)


def _looks_like_path(arg):
    """True si arg parece un path (no una opción CLI tipo /Q o --foo)."""
    if not isinstance(arg, str):
        return False
    # Opciones CLI: empiezan por - o son /X / /XX cortas tipo /Q de Inno
    if arg.startswith("-"):
        return False
    if arg.startswith("/") and len(arg) <= 4:
        return False
    return "\\" in arg or "/" in arg


def run(cmd, check=True, cwd=None, env_extra=None):
    """Ejecuta un comando shell, mostrándolo antes con paths relativos.

    env_extra: dict opcional con variables de entorno extra para el child
    (típicamente PYTHONWARNINGS=ignore para silenciar warnings de libs).
    """
    if isinstance(cmd, list):
        display = [rel(arg) if _looks_like_path(arg) else arg for arg in cmd]
        log(f"  $ {' '.join(display)}", "blue")
    else:
        log(f"  $ {cmd}", "blue")
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(cmd, check=check, cwd=cwd or ROOT,
                          shell=isinstance(cmd, str), env=env)


def check_dependencies():
    """Verifica que PyInstaller esté disponible."""
    try:
        import PyInstaller
        log(f"✓ PyInstaller {PyInstaller.__version__}", "green")
    except ImportError:
        log("✗ PyInstaller no instalado", "red")
        log("  Instálalo con: pip install pyinstaller", "yellow")
        sys.exit(1)


def find_inno():
    """Busca ISCC.exe de Inno Setup en las ubicaciones conocidas."""
    for path in INNO_PATHS:
        if path == "ISCC":
            if shutil.which("ISCC"):
                return "ISCC"
        elif Path(path).exists():
            return path
    return None


def find_signtool():
    """Busca signtool.exe (en PATH o en el Windows 10/11 SDK)."""
    if shutil.which("signtool"):
        return "signtool"
    bases = [
        Path(r"C:\Program Files (x86)\Windows Kits\10\bin"),
        Path(r"C:\Program Files\Windows Kits\10\bin"),
    ]
    candidatos = []
    for base in bases:
        if base.exists():
            candidatos += list(base.glob(r"*\x64\signtool.exe"))
            candidatos += list(base.glob("signtool.exe"))
    # Preferir la versión más reciente del SDK (orden lexicográfico inverso).
    candidatos.sort(reverse=True)
    return str(candidatos[0]) if candidatos else None


def sign_file(path):
    """Firma `path` con Authenticode si hay certificado configurado.

    Lee la config de variables de entorno (nunca hardcodear secretos):
        GPROMPT_SIGN_CERT        ruta a un .pfx/.p12  (opción A)
        GPROMPT_SIGN_PASSWORD    contraseña del .pfx  (opcional)
        GPROMPT_SIGN_THUMBPRINT  huella SHA1 de un cert ya en el almacén (opción B)
        GPROMPT_SIGN_TIMESTAMP   URL del servidor de sellado de tiempo RFC3161
                                 (default: http://timestamp.digicert.com)

    Si no hay ni CERT ni THUMBPRINT, es un no-op informativo: el build
    sigue siendo válido, solo sin firmar (SmartScreen mostrará aviso).
    Devuelve True si firmó, False si se omitió o falló.
    """
    cert = os.environ.get("GPROMPT_SIGN_CERT")
    thumb = os.environ.get("GPROMPT_SIGN_THUMBPRINT")
    if not cert and not thumb:
        log("ℹ Code-signing omitido (define GPROMPT_SIGN_CERT o "
            "GPROMPT_SIGN_THUMBPRINT para firmar)", "yellow")
        return False

    signtool = find_signtool()
    if not signtool:
        log("⚠ Hay certificado configurado pero no encuentro signtool.exe "
            "(instala el Windows SDK). Build sin firmar.", "yellow")
        return False

    ts_url = os.environ.get("GPROMPT_SIGN_TIMESTAMP", "http://timestamp.digicert.com")
    cmd = [signtool, "sign", "/fd", "SHA256", "/tr", ts_url, "/td", "SHA256"]
    if cert:
        cmd += ["/f", cert]
        pwd = os.environ.get("GPROMPT_SIGN_PASSWORD")
        if pwd:
            cmd += ["/p", pwd]
    else:
        cmd += ["/sha1", thumb]
    cmd.append(str(path))

    # Log SIN la contraseña ni la ruta del cert (datos sensibles).
    log(f"🔏 Firmando {rel(path)}…", "blue")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    _print_scrubbed(proc.stdout)
    _print_scrubbed(proc.stderr)
    if proc.returncode != 0:
        log(f"⚠ Firma falló (rc={proc.returncode}). Continúo sin firmar.", "yellow")
        return False
    log(f"✓ Firmado: {rel(path)}", "green")
    return True


def clean(include_pycache=False):
    """Borra dist/ y build/ para empezar de cero.

    Si include_pycache=True también borra TODOS los __pycache__/ del
    proyecto. Necesario tras cambios en .py si PyInstaller cachea
    bytecode viejo (lección sesión 13: el .exe seguía mostrando código
    antiguo aunque build/ y dist/ estuvieran borrados, porque los .pyc
    de __pycache__/ se incrustaban en base_library.zip).
    """
    for p in (DIST, BUILD):
        if p.exists():
            log(f"🗑  Borrando {rel(p)}/", "yellow")
            shutil.rmtree(p)
    # Borrar el spec generado por PyInstaller si existe (queremos usar el nuestro)
    for f in ROOT.glob("*.spec"):
        if f.name not in ("gprompt-studio.spec", "gprompt-studio-onefile.spec"):
            log(f"🗑  Borrando {f.name}", "yellow")
            f.unlink()
    if include_pycache:
        n_borrados = 0
        for pycache in ROOT.rglob("__pycache__"):
            # Saltar los que están dentro de dist/ o build/ (ya borrados)
            # y los de .venv si existe.
            partes = pycache.parts
            if any(p in partes for p in ("dist", "build", ".venv", "venv", "env")):
                continue
            try:
                shutil.rmtree(pycache)
                n_borrados += 1
            except Exception as e:
                log(f"⚠ No pude borrar {rel(pycache)}: {e}", "yellow")
        if n_borrados:
            log(f"🗑  Borrados {n_borrados} __pycache__/ del proyecto", "yellow")


def build_pyinstaller(onefile=False):
    """Lanza PyInstaller con el spec correspondiente al modo."""
    spec_name = "gprompt-studio-onefile.spec" if onefile else "gprompt-studio.spec"
    spec_path = ROOT / spec_name
    if not spec_path.exists():
        log(f"✗ No encuentro {spec_name}", "red")
        sys.exit(1)

    log(f"📦 Ejecutando PyInstaller ({spec_name})…", "blue")
    t0 = time.time()
    # NOTA: cuando se pasa un .spec, PyInstaller IGNORA flags como --onefile
    # (el modo está hardcoded en el .spec). Por eso usamos dos specs distintos.
    # --log-level=WARN silencia los INFO de PyInstaller que imprimen paths
    # absolutos. PYTHONWARNINGS=ignore silencia los DeprecationWarnings de
    # pydantic/darkdetect (que también muestran paths de site-packages).
    cmd = ["pyinstaller", "--noconfirm", "--log-level=WARN", spec_name]
    log(f"  $ pyinstaller --noconfirm --log-level=WARN {spec_name}", "blue")
    env = os.environ.copy()
    env["PYTHONWARNINGS"] = "ignore"
    # Capturamos stdout/stderr para reescribir paths absolutos a relativos
    # antes de mostrarlos. Los pocos WARNINGs que quedan vienen con rutas
    # de site-packages que delatan el nombre del usuario.
    proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    _print_scrubbed(proc.stdout)
    _print_scrubbed(proc.stderr)
    if proc.returncode != 0:
        log("✗ PyInstaller falló", "red")
        sys.exit(proc.returncode)
    dt = time.time() - t0
    log(f"✓ PyInstaller completado en {dt:.1f}s", "green")

    # Verificar que el resultado existe
    if onefile:
        out = DIST / "GPromptStudio.exe"
    else:
        out = DIST / "GPromptStudio" / "GPromptStudio.exe"
    if out.exists():
        size_mb = out.stat().st_size / (1024 * 1024)
        log(f"  → {rel(out)}  ({size_mb:.1f} MB)", "green")
    else:
        log(f"✗ No encuentro el ejecutable en {rel(out)}", "red")
        sys.exit(1)
    # Firma opcional del .exe (antes de empaquetarlo en el instalador).
    sign_file(out)
    return out


def build_installer():
    """Lanza Inno Setup con installer.iss."""
    if not ISS.exists():
        log("✗ No encuentro installer.iss", "red")
        log("  El instalador requiere installer.iss en la raíz del proyecto.",
            "yellow")
        return False

    iscc = find_inno()
    if not iscc:
        log("✗ Inno Setup no instalado", "red")
        log("  Descárgalo de https://jrsoftware.org/isinfo.php", "yellow")
        log("  Asegúrate de que ISCC.exe está en PATH o en", "yellow")
        log(r"  'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'", "yellow")
        return False

    log(f"📦 Ejecutando Inno Setup…", "blue")
    log(f"  $ ISCC.exe /Q installer.iss", "blue")
    t0 = time.time()
    # /Q = quiet mode (solo errores). Sin esto Inno Setup imprime cada
    # archivo comprimido con su path absoluto. También capturamos y
    # limpiamos por si /Q deja escapar alguna línea.
    proc = subprocess.run([iscc, "/Q", "installer.iss"], cwd=ROOT,
                          capture_output=True, text=True)
    _print_scrubbed(proc.stdout)
    _print_scrubbed(proc.stderr)
    if proc.returncode != 0:
        log("✗ Inno Setup falló", "red")
        return False
    dt = time.time() - t0
    log(f"✓ Inno Setup completado en {dt:.1f}s", "green")

    # Buscar el .exe instalador generado
    out_dir = DIST / "installer"
    if out_dir.exists():
        instaladores = list(out_dir.glob("*.exe"))
        if instaladores:
            inst = instaladores[0]
            size_mb = inst.stat().st_size / (1024 * 1024)
            log(f"  → {rel(inst)}  ({size_mb:.1f} MB)", "green")
            # Firma opcional del instalador generado.
            sign_file(inst)
            return True
    log("⚠ Inno Setup terminó pero no encuentro el instalador", "yellow")
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--onefile", action="store_true",
                        help="Generar .exe portable en un solo archivo (más lento al arrancar)")
    parser.add_argument("--installer", action="store_true",
                        help="También generar instalador con Inno Setup")
    parser.add_argument("--clean", action="store_true",
                        help="Borrar dist/ y build/ antes de empezar")
    parser.add_argument("--clean-cache", action="store_true",
                        help="--clean + borrar __pycache__/ recursivo "
                             "(asegura build 100%% limpio sin .pyc cacheados)")
    args = parser.parse_args()

    log("═══════════════════════════════════════════════════════════", "blue")
    log(" G-Prompt Studio — Build Script", "blue")
    log("═══════════════════════════════════════════════════════════", "blue")

    check_dependencies()

    if args.clean_cache:
        clean(include_pycache=True)
    elif args.clean:
        clean()

    # Verificar que el smoke test pasa antes de empaquetar
    log("🔍 Smoke test (import app)…", "blue")
    try:
        run([sys.executable, "-c", "import app; print('OK')"], check=True)
    except subprocess.CalledProcessError:
        log("✗ Smoke test falló — corrige errores antes de empaquetar", "red")
        sys.exit(1)
    log("✓ Smoke test OK", "green")

    # Build PyInstaller
    exe = build_pyinstaller(onefile=args.onefile)

    # Build instalador (opcional)
    if args.installer:
        if args.onefile:
            log("⚠ Modo onefile + installer: el instalador empaqueta el onefile.",
                "yellow")
        build_installer()

    log("═══════════════════════════════════════════════════════════", "green")
    log(" ✓ Build completado", "green")
    log(f"   Ejecutable: {rel(exe)}", "green")
    log("═══════════════════════════════════════════════════════════", "green")


if __name__ == "__main__":
    main()
