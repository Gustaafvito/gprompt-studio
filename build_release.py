#!/usr/bin/env python
"""Build LIMPIO y reproducible del .exe DEFINITIVO de G-Prompt Studio.

Exporta el repositorio (solo lo que está en git: SIN cruft `dist/`/`build/`/
`__pycache__`, SIN datos de usuario, SIN `.git`, SIN `.env`/keys) a una carpeta
limpia aparte, ejecuta ahí el build completo (onedir + instalador + onefile) y
copia los 3 artefactos al distribuible del escritorio.

Así el build definitivo siempre sale de un árbol limpio y reproducible, sin
arrastrar caches ni archivos locales.

Uso:
    python build_release.py                # tests + export limpio + build + copia
    python build_release.py --skip-tests   # sin correr la suite de tests
    python build_release.py --skip-audit   # sin pip-audit de dependencias
    python build_release.py --export-only  # solo el export limpio (sin buildear)
    python build_release.py --keep         # no borra la carpeta de build al terminar
    python build_release.py --yes          # no pregunta si el árbol está sucio

Requisitos: PyInstaller (build onedir/onefile) e Inno Setup (instalador), igual
que `build.py`. Ver docs/BUILD.md.
"""
import argparse
import io
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

try:  # consolas Windows (cp1252) no encodean ✓/→/▶ — forzar UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
CLEAN = ROOT.parent / "GPromptStudio-build-clean"
DEST = Path.home() / "OneDrive" / "Desktop" / "GPromptStudio-Distribuible"

# Paquetes que PyInstaller empaqueta dentro del .exe (directos + transitivos
# relevantes). El entorno global tiene ~230 paquetes de otros proyectos que NO
# entran en el build — auditar solo estos evita falsos positivos.
APP_DEPS = [
    "anthropic", "certifi", "charset-normalizer", "cryptography", "CTkToolTip",
    "customtkinter", "google-genai", "httpcore", "httpx", "idna", "keyring",
    "openai", "pillow", "plyer", "pydantic", "pyperclip", "python-dotenv",
    "requests", "urllib3",
]


def run(cmd, cwd=None):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def audit_deps():
    """pip-audit sobre las dependencias que van dentro del .exe. Avisa, no bloquea."""
    import importlib.metadata as md
    import tempfile

    pins = []
    for pkg in APP_DEPS:
        try:
            pins.append(f"{pkg}=={md.version(pkg)}")
        except md.PackageNotFoundError:
            continue
    with tempfile.NamedTemporaryFile(
        "w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("\n".join(pins))
        req = Path(f.name)
    try:
        res = subprocess.run(
            [sys.executable, "-m", "pip_audit", "-r", str(req), "--no-deps"],
            cwd=ROOT, capture_output=True, text=True,
        )
    finally:
        req.unlink(missing_ok=True)
    salida = (res.stdout or "") + (res.stderr or "")
    if "No module named" in salida:
        print("  (pip-audit no instalado — auditoría omitida; pip install pip-audit)")
    elif res.returncode != 0:
        print(salida.strip())
        print("⚠️  Vulnerabilidades conocidas en dependencias del .exe (el build continúa).")
    else:
        print("  ✓ Sin CVEs conocidos en las dependencias del .exe")


def export_limpio() -> Path:
    """git archive HEAD → carpeta limpia (solo archivos trackeados)."""
    if CLEAN.exists():
        shutil.rmtree(CLEAN)
    CLEAN.mkdir(parents=True)
    blob = subprocess.run(
        ["git", "archive", "HEAD"], cwd=ROOT, capture_output=True, check=True
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(blob)) as tf:
        tf.extractall(CLEAN)
    print(f"✓ Export limpio de HEAD → {CLEAN}")
    return CLEAN


def _con_reintentos(accion, descripcion, intentos=5, espera=3.0):
    """Reintenta una operación de archivo que OneDrive puede bloquear
    temporalmente al sincronizar (PermissionError sobre el .exe de destino).

    El distribuible vive en OneDrive; al copiar los .exe (130 MB) el cliente
    de sincronización a veces tiene el fichero abierto y la copia falla. Un
    reintento corto lo resuelve sin intervención manual."""
    for i in range(intentos):
        try:
            return accion()
        except (PermissionError, OSError) as e:
            if i == intentos - 1:
                raise
            print(f"  ⚠ {descripcion}: bloqueado ({type(e).__name__}); "
                  f"reintento {i + 1}/{intentos - 1} en {espera:.0f}s "
                  f"(¿OneDrive sincronizando?)…")
            time.sleep(espera)


def copiar_artefactos(src_dist: Path):
    DEST.mkdir(parents=True, exist_ok=True)
    portable = DEST / "GPromptStudio-Portable"

    def _copiar_portable():
        if portable.exists():
            shutil.rmtree(portable)
        shutil.copytree(src_dist / "GPromptStudio", portable)

    _con_reintentos(_copiar_portable, "onedir Portable")
    _con_reintentos(
        lambda: shutil.copy2(src_dist / "GPromptStudio.exe",
                             DEST / "GPromptStudio-Portable-Onefile.exe"),
        "onefile .exe")
    _con_reintentos(
        lambda: shutil.copy2(src_dist / "installer" / "GPromptStudio-Setup-1.0.0.exe",
                             DEST / "GPromptStudio-Setup-1.0.0.exe"),
        "installer .exe")
    # README del distribuible: versionado en el repo para que no se quede
    # obsoleto en el escritorio (rutas, tamaños, opciones).
    _con_reintentos(
        lambda: shutil.copy2(ROOT / "docs" / "LEEME-PRIMERO.txt",
                             DEST / "LEEME-PRIMERO.txt"),
        "LEEME-PRIMERO.txt")
    print(f"✓ 3 artefactos + LEEME copiados a {DEST}")


def main():
    ap = argparse.ArgumentParser(description="Build limpio del .exe definitivo")
    ap.add_argument("--skip-tests", action="store_true")
    ap.add_argument("--skip-audit", action="store_true",
                    help="no correr pip-audit sobre las dependencias del .exe")
    ap.add_argument("--export-only", action="store_true")
    ap.add_argument("--keep", action="store_true",
                    help="no borrar la carpeta de build limpio al terminar")
    ap.add_argument("--yes", action="store_true",
                    help="no preguntar si el árbol git tiene cambios sin commitear")
    args = ap.parse_args()

    # El export usa HEAD (último commit), NO el working tree: avisar si hay
    # cambios sin commitear para que el usuario no se sorprenda.
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    if dirty and not args.yes:
        print("⚠️  Hay cambios SIN COMMITEAR. El build limpio usa el ÚLTIMO COMMIT")
        print("    (HEAD), así que esos cambios NO entrarán. Commitea primero si los quieres.")
        if input("    ¿Continuar igualmente? [y/N] ").strip().lower() != "y":
            sys.exit(1)

    if not args.skip_tests:
        print("▶ Tests…")
        run([sys.executable, "-m", "pytest", "tests", "-q"], cwd=ROOT)

    if not args.skip_audit:
        print("▶ Auditoría CVEs (pip-audit)…")
        audit_deps()

    clean = export_limpio()
    if args.export_only:
        print("(--export-only) Hecho. Build no ejecutado.")
        return

    print("▶ Build onedir + instalador…")
    run([sys.executable, "build.py", "--clean", "--installer"], cwd=clean)
    print("▶ Build onefile…")
    run([sys.executable, "build.py", "--onefile"], cwd=clean)

    copiar_artefactos(clean / "dist")

    if not args.keep:
        shutil.rmtree(clean, ignore_errors=True)
        print("✓ Carpeta de build limpio eliminada")
    print("\n✅ Build definitivo listo en", DEST)


if __name__ == "__main__":
    main()
