@echo off
setlocal
cd /d "%~dp0"
echo G-Prompt Studio - prueba de Crear desde imagenes
echo Cierra la otra instancia de G-Prompt Studio antes de continuar.
echo Esta prueba utiliza tus preferencias habituales. No modifica el EXE instalado.
pause
if not exist ".venv-visual\Scripts\python.exe" (
    py -3.12 -m venv .venv-visual
    if errorlevel 1 goto error
)
if not exist ".venv-visual\visual-ready" (
    ".venv-visual\Scripts\python.exe" -m pip install -c VISUAL-constraints.txt -e ".[all]"
    if errorlevel 1 goto error
    echo ready> ".venv-visual\visual-ready"
)
".venv-visual\Scripts\python.exe" main.py
if errorlevel 1 goto error
exit /b 0
:error
echo.
echo No se pudo iniciar. Copia las ultimas lineas para revisar el error.
pause
exit /b 1
