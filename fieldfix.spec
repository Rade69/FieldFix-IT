# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for FieldFix IT
# Build: pyinstaller fieldfix.spec
# Output: dist/FieldFix IT/  (one-folder build)

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # icons.py: _base() / "resources" / "icons" → sys._MEIPASS / "resources" / "icons"
        ('app/resources', 'resources'),
        # knowledge YAMLs — not loaded at runtime yet, bundled for future use
        ('app/knowledge', 'app/knowledge'),
    ],
    hiddenimports=[
        'PySide6.QtSvg',
        'PySide6.QtSvgWidgets',
        'PySide6.QtNetwork',
        'PySide6.QtXml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FieldFix IT',
    debug=False,
    strip=False,
    upx=False,           # UPX off — lažni pozitivni u antivirusima
    console=False,       # bez konzolnog prozora
    icon='app/resources/icons/fieldfix_icon.ico',
    version_file=None,
    uac_admin=False,     # admin se traži ručno iz app (Fix Center UAC prompt)
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='FieldFix IT',
)
