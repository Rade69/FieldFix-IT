# Agent report: Printers module (Zadatak 8 / Faza 8)

## Datum
2026-06-30

## Scope
- `app/modules/printers/__init__.py` (novo)
- `app/modules/printers/models.py` (novo)
- `app/modules/printers/scanner.py` (novo)
- `app/gui/pages/printers_page.py` (update — stub → funkcionalna stranica)
- `tests/modules/printers/__init__.py` (novo)
- `tests/modules/printers/test_printers_scanner.py` (novo)

## GitNexus impact (provjera prije izmjene)
- `PrintersPage`: LOW (1 direktni — main_window.py, očekivano)
- Novi modul — nema izmjena na postojećim simbolima

## Šta je urađeno

### `app/modules/printers/models.py`

3 frozen dataclassa:
- `PrinterInfo` — name, driver_name, port_name, printer_type, shared, share_name,
  status, job_count, is_default
- `PrintJob` — job_id, printer_name, document_name, user_name, total_pages, status
- `PrintersData` — tuple printers, tuple print_jobs, scan_duration_ms, errors

### `app/modules/printers/scanner.py`

`PrintersScanner(runner: PowerShellRunner)` s metodom `scan() → PrintersData`.

**Tri PS poziva:**

1. `_get_default_printer_name` — `Get-CimInstance Win32_Printer -Filter "Default='True'"`
   Vraća ime default štampača (prazan string ako nije podešen ili query ne uspije —
   non-fatal, scan nastavlja).

2. `_get_printers` — `Get-Printer` s `ToString()` za `Type` i `PrinterStatus` enum
   vrijednosti. `is_default` se postavlja poređenjem sa imenom iz poziva #1.

3. `_get_print_jobs` — `Get-Printer | Get-PrintJob` za sve štampače odjednom.
   Prazan red je normalan (nema čekajućih poslova) — ne dodaje se u errors.
   `stderr` se dodaje u errors samo ako postoji.

### `app/gui/pages/printers_page.py`

- Header: "🖨 Printer Diagnostics" + status + dugme
- Summary: ✓ OK / ⚠ Problem / Total / Print Jobs badges
- Printers panel: ★ oznaka za default, Type, Status (zeleno/žuto/crveno), job count,
  driver/port info
- Print Jobs panel: tabela (ID, Printer, Document, User, Pages, Status) —
  prikazuje se samo ako ima aktivnih poslova
- Warnings panel za greške

## Šta nije dirano
- Nijedna Windows postavka nije promijenjena
- Fix komande (restart Spooler, delete job) nisu implementirane — Faza 13
- Ostali moduli i stranice — netaknuti

## Verifikacija
```
127 passed in 1.11s
```
(20 novih testova)

## Rizici / ograničenja
- **Sinhroni scan** — threading V2 (isti obrazac kao ostale stranice)
- **`Get-Printer | Get-PrintJob`**: ako nema štampača, PS može baciti grešku
  ("Cannot bind argument to parameter..."). Pokriveno sa `-ErrorAction SilentlyContinue`
  + stderr detekcijom
- **PrinterStatus "Normal" set**: definisan u `_STATUS_OK` — ako se pojavi novi
  status string na egzotičnom drajveru, padne u "crvenu" kategoriju (konzervativno,
  bolje false positive nego false negative za greške)

## Potreban follow-up
- Faza 9 — Report Generator
- Faza 13 (Fix Center): delete stuck print job, restart Print Spooler
