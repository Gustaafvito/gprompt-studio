# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec para G-Prompt Studio.

Genera un .exe Windows con todos los recursos y dependencias.
Uso:
    pyinstaller gprompt-studio.spec
    # → dist/GPromptStudio/  (onedir, recomendado)
    # o
    pyinstaller --onefile gprompt-studio.spec
    # → dist/GPromptStudio.exe  (un solo archivo, inicio más lento)

Después puedes lanzar Inno Setup con installer.iss para empaquetar el
instalador completo.
"""
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ─── Recursos a incluir ────────────────────────────────────────────
datas = [
    # Datos JSON del proyecto (specs de modelos, estilos, etc.)
    ('data',          'data'),
    # Plantillas predefinidas (faltaba — _cmd_plantillas_populares
    # leía config/plantillas_default.json y devolvía [] en el .exe).
    ('config',        'config'),
    # CustomTkinter incluye themes y assets internos que no se detectan
    *collect_data_files('customtkinter'),
    # Pillow tiene plugins por formato
    *collect_data_files('PIL'),
    # Tema visual personalizado (sin esto el .exe caía al tema azul
    # por defecto de CTk — detectado en sesión 19 round 9).
    ('theme.json',    '.'),
    # Documentación de USUARIO únicamente. Los docs de desarrollo
    # (ESTRUCTURA.md, HANDOFF.md, BUILD.md, AGREGAR_MODELO.md) NO se
    # empaquetan: son material interno del proyecto.
    ('README.md',     '.'),
    ('GUIA_ESTILOS.md', '.'),
]

# ─── Hidden imports (módulos que PyInstaller no detecta solo) ────
hiddenimports = [
    # Mixins del proyecto — todos cargados desde modules/__init__.py
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
    # Módulo Avatar dataset LoRA (sesión 19)
    'modules.avatar_config',
    'modules.avatar_prompts',
    'modules.avatar_generator',
    'modules.avatar_ui',
    # Keyring backends por plataforma (PyInstaller suele perder éstos)
    'keyring.backends.Windows',
    'keyring.backends.SecretService',
    'keyring.backends.macOS',
    'keyring.backends.fail',
    # Cryptography (cifrado AES de keys.json)
    'cryptography.hazmat.backends.openssl',
    'cryptography.hazmat.primitives.ciphers',
    # Pillow extras
    'PIL._tkinter_finder',
    # Para sesión vídeo (opcional - no falla si no está)
    # 'cv2',
    # 'mss',
]

# Incluir todos los submódulos de keyring para evitar sorpresas
hiddenimports += collect_submodules('keyring')

# ─── Análisis ──────────────────────────────────────────────────────
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
        # Excluir cosas pesadas que no se usan
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'pytest',
        'pytest_anyio',
        # ⚠️ SEGURIDAD: nunca incluir archivos con secretos.
        # PyInstaller NO empaqueta .env/keys.json salvo que estén en `datas`,
        # pero los listamos aquí para dejarlo explícito y blindar contra
        # accidentes futuros si alguien los añade a datas por error.
        '.env',
        'keys.json',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ─── Modo ONEDIR (recomendado para iniciar más rápido) ───────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GPromptStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,           # comprimir con UPX si está disponible (más pequeño)
    console=False,       # ventana sin consola (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Si tienes un icono .ico, pónlo aquí:
    # icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GPromptStudio',
)
