## Datum

2026-06-30

## Scope

- `app/modules/firewall/__init__.py`
- `app/modules/firewall/models.py`
- `app/modules/firewall/scanner.py`
- `app/gui/pages/firewall_page.py`
- `tests/modules/firewall/__init__.py`
- `tests/modules/firewall/test_firewall_scanner.py`

## GitNexus impact

Prije izmjene postojećeg `FirewallPage` simbola pokrenut je GitNexus impact:

- Target: `FirewallPage` (`app/gui/pages/firewall_page.py`)
- Rizik: LOW
- Direktno pogođeno: `app/gui/main_window.py`
- Indirektno pogođeno: `tests/test_app_shell.py`, `app/main.py`
- Pogođeni execution flows: 0

## Šta je urađeno

Implementiran je Firewall modul za Fazu 6:

- dodati frozen dataclass modeli `FirewallProfile`, `FirewallRule`, `FirewallData`,
- dodat scan-only `FirewallScanner` sa tri JSON-first PowerShell poziva,
- normalizovan PowerShell JSON quirk gdje jedan rezultat dolazi kao dict,
- greške su non-fatal i skupljaju se u `FirewallData.errors`,
- `FirewallPage` placeholder je zamijenjen funkcionalnom stranicom sa profilima,
  File & Printer Sharing pravilima, Network Discovery pravilima i panelom grešaka,
- dodati unit testovi za profile, pravila, dict/list normalizaciju, non-fatal greške
  i prazne rezultate.

## Zašto je urađeno

Faza 6 iz integrisanog plana uvodi Firewall dijagnostiku kao scan-only modul.
Modul treba prikazati stanje firewall profila i relevantnih rule grupa bez
mijenjanja Windows postavki.

## Kako je urađeno

Scanner koristi `PowerShellRunner.run_json()` i strukturisane PowerShell cmdlete:

- `Get-NetFirewallProfile`
- `Get-NetFirewallRule -DisplayGroup "File and Printer Sharing"`
- `Get-NetFirewallRule -DisplayGroup "Network Discovery"`

Sve enum vrijednosti se u PowerShell komandi pretvaraju kroz `.ToString()`.
GUI prati pattern `ServicesPage`: header, `QScrollArea`, paneli rezultata i
scan dugme.

## Šta nije dirano

Nije mijenjano:

- `app/core/`
- `app/gui/main_window.py`
- `app/gui/sidebar.py`
- `app/modules/network/`
- `app/modules/smb/`
- `app/modules/services/`
- `tests/core/`
- `tests/modules/network/`
- `tests/modules/smb/`
- `tests/modules/services/`
- `docs/architecture_notes.md`
- `AGENTS.md`
- `CLAUDE.md`

Nisu dodate fix akcije i nijedna Windows postavka se ne mijenja.

## Verifikacija

- `python -m pytest tests/modules/firewall -q` → 13 passed
- `python -m pytest tests/ -q` → 140 passed

## Rizici / ograničenja

- PowerShell rule grupe zavise od lokalizacije Windows DisplayGroup naziva.
  Trenutna implementacija prati brief i koristi tačno tražene engleske nazive.
- GUI scan je sinhron, kao i postojeće stranice; pri sporijem PowerShell pozivu
  UI može kratko čekati.

## Potreban follow-up

- Ručno provjeriti Firewall stranicu na stvarnom Windows uređaju sa različitim
  profilima i firewall rule grupama.
- Ako se pojavi lokalizovan Windows gdje DisplayGroup nije engleski, razmotriti
  stabilniji filter po rule name prefixima ili resource-independent grupama.

## Potrebna korisnička potvrda

Nije potrebna za sigurnost sistema: implementacija je scan-only.
