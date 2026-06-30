## Datum

2026-06-30

## Scope

- `fieldfix.spec`
- `build.ps1`
- `installer/setup.iss`
- `.gitignore`
- `app/gui/icons.py`

## GitNexus impact

Prije izmjene `app/gui/icons.py` pokrenut je GitNexus impact za `_ICONS_DIR`:

- Rizik: LOW
- Direktno pogođeno: 0 simbola/procesa
- Pogođeni execution flows: 0

## Šta je urađeno

Dodana je portable build konfiguracija za FieldFix IT:

- PyInstaller `fieldfix.spec` za one-file `FieldFix IT.exe`,
- `build.ps1` skripta koja aktivira `.venv` ako postoji i pokreće PyInstaller,
- Inno Setup konfiguracija `installer/setup.iss`,
- `.gitignore` dopuna za build artefakte i `fieldfix.spec`,
- `app/gui/icons.py` sada koristi `sys._MEIPASS` kada je aplikacija frozen.

## Zašto je urađeno

Faza 14 traži distribucioni artefakt koji korisnik može pokrenuti bez lokalno
instaliranog Python okruženja. Ikonice i knowledge YAML fajlovi moraju biti
dostupni i kada aplikacija radi iz PyInstaller one-file bundle-a.

## Kako je urađeno

`fieldfix.spec` bundle-uje:

- `asset/icons` → `resources/icons`,
- `app/knowledge` → `app/knowledge`.

`icons.py` u normalnom modu koristi postojeću putanju relativnu na `app/gui`,
a u PyInstaller modu koristi `sys._MEIPASS` kao bundle root.

EXE se gradi kao windowed app (`console=False`) i ne traži administrator prava
pri pokretanju (`uac_admin=False`, manifest `asInvoker`).

## Šta nije dirano

Nije mijenjano:

- `requirements.txt`,
- aplikacioni moduli,
- core runner / scan / fix logika,
- `docs/architecture_notes.md`,
- `AGENTS.md`,
- `CLAUDE.md`.

Nije dodat installer binary u repo; `dist/` i `build/` ostaju ignorisani.

## Verifikacija

- `python -m pytest tests/ -q` → 199 passed
- `pyinstaller --version` → 6.20.0
- `pyinstaller fieldfix.spec --noconfirm` → uspješno
- `powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1` → uspješno
- `dist/FieldFix IT.exe` generisan: oko 47 MB
- Kratki smoke-test: `FieldFix IT.exe` se pokrenuo i ostao aktivan; proces je
  zatim ručno zaustavljen.
- PyInstaller TOC potvrđuje uključene `resources/icons/*` i
  `app/knowledge/smb/*.yaml` fajlove.

## Rizici / ograničenja

- Nije testirano na čistoj Windows VM bez instaliranog Pythona; provjera je
  rađena na trenutnoj Windows 11 mašini.
- Inno Setup `.iss` fajl je dodat, ali nije kompajliran jer `ISCC.exe` nije
  dostupan na PATH-u.
- Prvi ponovni build poslije smoke testa je pao jer je prethodni EXE proces
  ostao aktivan i zaključao `dist/FieldFix IT.exe`; nakon zaustavljanja procesa
  i pooštravanja `build.ps1` exit-code provjere build prolazi.

## Potreban follow-up

- Testirati `dist/FieldFix IT.exe` na čistoj Windows 11 VM bez Python-a.
- Ako se koristi Inno Setup, pokrenuti `ISCC.exe installer/setup.iss` na mašini
  gdje je Inno Setup instaliran i provjeriti generated installer.

## Potrebna korisnička potvrda

Potrebna je ručna potvrda da EXE radi na ciljnoj čistoj Windows 11 mašini.
