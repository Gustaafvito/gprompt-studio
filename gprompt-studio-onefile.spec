# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec para G-Prompt Studio en modo ONEFILE.

Genera UN solo .exe Windows autocontenido que se autoextrae a
%TEMP% al arrancar. Inicio más lento (~3-5 seg) pero un solo
archivo para distribuir.

Uso:
    pyinstaller gprompt-studio-onefile.spec
    # → dist/GPromptStudio.exe  (~88 MB)

Para el modo onedir (más rápido al arrancar, recomendado para
instalación con Inno Setup), usa gprompt-studio.spec.
"""
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ─── Recursos a incluir ────────────────────────────────────────────
# IMPORTANTE: misma lista que el spec onedir — mantener en sync.
datas = [
    # Datos JSON del proyecto (specs de modelos, estilos, plantillas, etc.)
    ('data',          'data'),
    *collect_data_files('customtkinter'),
    *collect_data_files('PIL'),
    # Tema visual personalizado (sin esto el .exe caía al tema azul)
    ('theme.json',    '.'),
    # Icono de la app (main.py lo aplica con iconbitmap en runtime)
    ('assets',        'assets'),
    # Solo docs de USUARIO (los docs de desarrollo no se empaquetan)
    ('README.md',     '.'),
    ('GUIA_ESTILOS.md', '.'),
    ('GUIA_ESTILOS.en.md', '.'),
]

# ─── Hidden imports (mismos que onedir) ──────────────────────────
hiddenimports = [
    'modules.ui_builders',
    'modules.tools_creative',
    'modules.tools_workflow',
    'modules.tools_analysis',
    'modules.data_mgmt',
    'modules.backup_export',
    'modules.dialogs',
    'modules.core',
    'modules.adn_visual',
    'modules.multiprompt',
    'modules.sesion_video',
    'modules.workers_ia',
    'modules.modo_cliente',
    'modules.json_prompt',
    'modules.gprompt_window',
    'modules.event_bus',
    'modules.preview_pollinations',
    'modules.panel_lateral',
    'modules.components',
    'modules.windows',
    'modules.tutorial',
    'modules.glosario',
    'modules.style_guide',
    'modules.ab_testing',
    'modules.prompts_inyeccion',
    'modules.atajos_ayuda',
    'modules.ui_events',
    'modules.refinamiento',
    'modules.dashboard',
    'modules.ui_footer',
    'modules.tooltip',
    'modules.i18n',
    'modules.avatar_config',
    'modules.avatar_prompts',
    'modules.avatar_generator',
    'modules.avatar_ui',
    'keyring.backends.Windows',
    'keyring.backends.SecretService',
    'keyring.backends.macOS',
    'keyring.backends.fail',
    'cryptography.hazmat.backends.openssl',
    'cryptography.hazmat.primitives.ciphers',
    'PIL._tkinter_finder',
]

hiddenimports += collect_submodules('keyring')

a = Analysis(
    ['main.py'],
    pathex=[os.path.abspath('.')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'pytest',
        'pytest_anyio',
        # ⚠️ SEGURIDAD: nunca incluir archivos con secretos.
        '.env',
        'keys.json',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ─── Modo ONEFILE ────────────────────────────────────────────────
# Diferencia clave vs onedir: incluimos a.binaries + a.zipfiles +
# a.datas directamente en el EXE, no en un COLLECT separado.
# Resultado: un solo archivo .exe que se autoextrae al ejecutarse.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GPromptStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)
