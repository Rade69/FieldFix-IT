---
name: pyinstaller-pyside6
description: "Use when packaging a PySide6 (Qt6) Python application with PyInstaller into a one-folder Windows build. Covers the correct .spec file template, required hidden imports, resource path resolution via sys._MEIPASS, CREATE_NO_WINDOW for subprocess, and common pitfalls."
---

# PyInstaller + PySide6 — Windows one-folder build

## Kada koristiti

- Pakovati PySide6 aplikaciju u `.exe` za distribuciju
- Resursi (ikone, YAML, itd.) nisu vidljivi u pakovanoj aplikaciji
- Subprocess otvara crni CMD prozor u pakovanoj verziji
- Taskbar ikona je generička nakon pakovanja

## Gotchas koji koštaju sat-dva svaki put

| Problem | Uzrok | Rješenje |
|---------|-------|----------|
| `ImportError: QtSvg` pri pokretanju exe | PySide6 SVG moduli nisu detektovani | Dodaj u `hiddenimports` |
| Resursi (ikone, fajlovi) nisu nađeni | `datas` mapiranje pogrešno ili `_base()` ne koristi `_MEIPASS` | Vidi sekciju "Putanje resursa" |
| Crni CMD prozor kod svakog PowerShell poziva | Nedostaje `CREATE_NO_WINDOW` flag | Vidi sekciju "subprocess" |
| Taskbar ikona je generička | `.ico` fajlu nedostaje 48×48 veličina | Vidi skill `windows-ico-pillow` |
| `ModuleNotFoundError` za PySide6 plugin | Tree-shaking PyInstaller-a uklonio plugin | Dodaj u `hiddenimports` |

## Spec fajl — template

```python
# -*- mode: python ; coding: utf-8 -*-
# Build: pyinstaller fieldfix.spec

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Format: ('izvorni_put', 'destinacija_unutar_MEIPASS')
        # VAŽNO: destinacija mora odgovarati onome što kod očekuje (vidi _base() ispod)
        ('app/resources', 'resources'),
        ('app/knowledge', 'app/knowledge'),
    ],
    hiddenimports=[
        # PySide6 moduli koje PyInstaller ne detektuje automatski
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
    name='MyApp',
    debug=False,
    strip=False,
    upx=False,           # UPX isključen — lažni pozitivni u antivirusima
    console=False,       # bez konzolnog prozora
    icon='app/resources/icons/app_icon.ico',
    version_file=None,
    uac_admin=False,     # admin se traži ručno iz aplikacije, ne pri startu
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='MyApp',        # naziv output foldera u dist/
)
```

## Putanje resursa — `_base()` pattern

U kodu koji učitava resurse, uvijek koristi ovu funkciju umjesto hardkodovanih putanja:

```python
import sys
from pathlib import Path

def _base() -> Path:
    """Root of resource tree — works both in dev and PyInstaller frozen mode."""
    if getattr(sys, 'frozen', False):
        # PyInstaller: resources su u sys._MEIPASS/resources/
        return Path(sys._MEIPASS) / 'resources'
    else:
        # Dev mode: resources su u app/resources/ relativno od project root
        return Path(__file__).resolve().parent.parent / 'resources'

# Primjer upotrebe
ICON_PATH = _base() / 'icons' / 'app_icon.ico'
```

Ključno: ako spec fajl kaže `('app/resources', 'resources')`, tada u `_MEIPASS` postoji folder `resources/`, ne `app/resources/`. Mora se poklapati sa `_base()`.

## subprocess — spriječiti crni CMD prozor

```python
import subprocess

proc = subprocess.run(
    ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace',
    timeout=30,
    creationflags=subprocess.CREATE_NO_WINDOW,  # ← obavezno za windowed app
)
```

Bez `CREATE_NO_WINDOW` svaki PowerShell/CMD poziv otvara vidljivi crni prozor.

## Build i pokretanje

```bash
# Instalacija
pip install pyinstaller

# Build (iz project root-a)
pyinstaller fieldfix.spec

# Output: dist/MyApp/ (one-folder)
# Pokrenuti: dist/MyApp/MyApp.exe
```

## Šta NE raditi

- **Ne koristi `--onefile`** za PySide6 — sporo se raspakuje, antivirusi blokiraju
- **Ne stavljaj `uac_admin=True`** u spec — traži UAC pri svakom pokretanju, loše UX
- **Ne koristi `upx=True`** — komprimuje binaries, lažni pozitivni u antivirusima
- **Ne hardkoduj putanje resursa** — neće raditi u frozen modu

## Reference

- `fieldfix.spec` — radni primjer u ovom projektu
- `app/gui/icons.py` — implementacija `_base()` funkcije
- `app/core/powershell_runner.py` — `CREATE_NO_WINDOW` u praksi
- Skill `windows-ico-pillow` — generisanje ispravne `.ico` datoteke
