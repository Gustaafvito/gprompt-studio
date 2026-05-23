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


def log(msg, color=""):
    """Imprime mensaje con color ANSI (si terminal lo soporta)."""
    colors = {"green": "\033[92m", "red": "\033[91m", "yellow": "\033[93m",
              "blue": "\033[94m", "reset": "\033[0m"}
    if color and sys.stdout.isatty():
        print(f"{colors.get(color, '')}{msg}{colors['reset']}")
    else:
        print(msg)


def run(cmd, check=True, cwd=None):
    """Ejecuta un comando shell, mostrándolo antes."""
    if isinstance(cmd, list):
        log(f"  $ {' '.join(cmd)}", "blue")
    else:
        log(f"  $ {cmd}", "blue")
    return subprocess.run(cmd, check=check, cwd=cwd or ROOT, shell=isinstance(cmd, str))


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


def clean():
    """Borra dist/ y build/ para empezar de cero."""
    for p in (DIST, BUILD):
        if p.exists():
            log(f"🗑  Borrando {p}", "yellow")
            shutil.rmtree(p)
    # Borrar el spec generado por PyInstaller si existe (queremos usar el nuestro)
    for f in ROOT.glob("*.spec"):
        if f.name != "gprompt-studio.spec":
            log(f"🗑  Borrando {f.name}", "yellow")
            f.unlink()


def build_pyinstaller(onefile=False):
    """Lanza PyInstaller con nuestro spec."""
    if not SPEC.exists():
        log(f"✗ No encuentro {SPEC}", "red")
        sys.exit(1)

    log(f"📦 Ejecutando PyInstaller…", "blue")
    t0 = time.time()
    cmd = ["pyinstaller", "--noconfirm", str(SPEC)]
    if onefile:
        # Sobrescribir el modo onedir con --onefile via argv
        cmd.insert(-1, "--onefile")
    run(cmd)
    dt = time.time() - t0
    log(f"✓ PyInstaller completado en {dt:.1f}s", "green")

    # Verificar que el resultado existe
    if onefile:
        out = DIST / "GPromptStudio.exe"
    else:
        out = DIST / "GPromptStudio" / "GPromptStudio.exe"
    if out.exists():
        size_mb = out.stat().st_size / (1024 * 1024)
        log(f"  → {out}  ({size_mb:.1f} MB)", "green")
    else:
        log(f"✗ No encuentro el ejecutable en {out}", "red")
        sys.exit(1)
    return out


def build_installer():
    """Lanza Inno Setup con installer.iss."""
    if not ISS.exists():
        log(f"✗ No encuentro {ISS}", "red")
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
    t0 = time.time()
    run([iscc, str(ISS)])
    dt = time.time() - t0
    log(f"✓ Inno Setup completado en {dt:.1f}s", "green")

    # Buscar el .exe instalador generado
    out_dir = DIST / "installer"
    if out_dir.exists():
        instaladores = list(out_dir.glob("*.exe"))
        if instaladores:
            inst = instaladores[0]
            size_mb = inst.stat().st_size / (1024 * 1024)
            log(f"  → {inst}  ({size_mb:.1f} MB)", "green")
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
    args = parser.parse_args()

    log("═══════════════════════════════════════════════════════════", "blue")
    log(" G-Prompt Studio — Build Script", "blue")
    log("═══════════════════════════════════════════════════════════", "blue")

    check_dependencies()

    if args.clean:
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
    log(f"   Ejecutable: {exe}", "green")
    log("═══════════════════════════════════════════════════════════", "green")


if __name__ == "__main__":
    main()
