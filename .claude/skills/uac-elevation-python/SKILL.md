---
name: uac-elevation-python
description: "Use when a Python/PySide6 Windows app needs to restart itself with Administrator privileges via UAC prompt. Covers is_admin() check, restart_as_admin() that works for both PyInstaller frozen .exe and dev-mode python -m, and the ShellExecuteW 'runas' pattern."
---

# UAC Elevacija — Python Windows app (frozen + dev mode)

## Kada koristiti

- Aplikacija treba admin privilegije za određene operacije (Fix Center, mrežne promjene...)
- Ne želiš da se aplikacija uvijek pokreće kao admin (loš UX, sigurnosni rizik)
- Trebaš programski podići privilegije na zahtjev korisnika

## Dva slučaja koja moraju raditi

| Situacija | `sys.executable` | Kako pokrenuti elevated |
|-----------|-----------------|------------------------|
| PyInstaller frozen exe | `dist/MyApp/MyApp.exe` | `ShellExecuteW(exe, params=None)` |
| Dev mode | `python.exe` | `ShellExecuteW(python, params="-m app.main")` |

**Najčešća greška:** uzeti kod s interneta koji radi samo za frozen exe, ili koji u dev modu poziva `python app/main.py` umjesto `python -m app.main` — što lomi relative imports.

## Kompletna implementacija

```python
import ctypes
import os
import sys
import time
from pathlib import Path


def is_admin() -> bool:
    """True if current process has Administrator privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def restart_as_admin() -> None:
    """Relaunch this process with Administrator privileges via UAC.

    If user accepts UAC prompt — current (non-elevated) process exits and
    a new elevated instance starts. If user cancels — function returns
    without doing anything.

    Works for both PyInstaller frozen exe and dev-mode python -m app.main.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller bundle: pokrenuti exe direktno
        prog = sys.executable
        params = None
        work_dir = str(Path(sys.executable).parent)
    else:
        # Dev mode: MORA biti "python -m app.main", ne "python app/main.py"
        # app/main.py lomi relative imports; -m app.main radi ispravno
        prog = sys.executable
        params = '-m app.main'
        # Ovaj fajl je npr. app/core/utils.py → project root je 2 nivoa gore
        work_dir = str(Path(__file__).resolve().parent.parent.parent)

    ret = ctypes.windll.shell32.ShellExecuteW(
        None,       # hwnd
        'runas',    # lpOperation — traži UAC prompt
        prog,       # lpFile
        params,     # lpParameters (None za frozen exe)
        work_dir,   # lpDirectory
        1,          # nShowCmd (SW_SHOWNORMAL)
    )

    if int(ret) > 32:
        # UAC prihvaćen — novi elevated process se pokreće
        # Kratka pauza da mu se da šansa da se inicijalizuje
        time.sleep(0.4)
        os._exit(0)
    # ret <= 32 znači da je korisnik otkazao UAC ili došlo do greške
    # Funkcija se vraća tiho, aplikacija nastavlja bez elevacije
```

## Kako pozvati iz UI-a

```python
from app.core.powershell_runner import is_admin, restart_as_admin

class FixCenterPage(QWidget):
    def _on_request_admin(self) -> None:
        if is_admin():
            self._enable_fix_mode()
            return

        reply = QMessageBox.question(
            self,
            'Administrator Required',
            'This operation requires Administrator privileges.\n'
            'Restart FieldFix IT as Administrator?',
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            restart_as_admin()
            # Ako je UAC prihvaćen, os._exit(0) je već pozvan u restart_as_admin()
            # Ako je otkazan, izvršavanje nastavlja ovdje — ne raditi ništa
```

## Sigurnosna pravila

- **Ne postavljati `uac_admin=True` u PyInstaller spec** — aplikacija ne treba admin za normalni rad, samo za Fix operacije
- **Admin mode je opt-in** — korisnik mora eksplicitno zatražiti; nikad ne elevirati automatski pri startu
- **Sve Fix operacije moraju proći kroz korisničku potvrdu** — čak i nakon elevacije, svaki fix se primjenjuje tek na eksplicitni Apply klik

## Debugging

```python
# Provjera u konzoli tokom razvoja
import ctypes
print("Is admin:", bool(ctypes.windll.shell32.IsUserAnAdmin()))

# U dev modu, ručno testirati elevated pokretanje:
# Otvori PowerShell kao Admin i pokreni:
# python -m app.main
```

## Reference

- `app/core/powershell_runner.py` — `is_admin()` i `restart_as_admin()` implementacija
- `app/gui/pages/fix_center_page.py` — primjer poziva iz UI-a
