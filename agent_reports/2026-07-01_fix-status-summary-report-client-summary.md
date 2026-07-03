# Agent report: Fix status, dashboard summary, client report summary

## Datum

2026-07-01

## Scope

- `app/gui/pages/fix_center_page.py`
- `app/gui/dashboard.py`
- `app/reports/html_report.py`
- `app/reports/markdown_report.py`
- `tests/gui/test_fix_center_status_check.py`
- `tests/gui/test_dashboard_summary.py`
- `tests/reports/test_report_writers.py`

## GitNexus impact

Pre-change impact:

- `FixAction` — LOW
- `_FixActionCard.__init__` — LOW
- `DashboardPage._setup_ui` — LOW
- `DashboardPage._update_dashboard` — LOW
- `write_html` — LOW
- `write_markdown` — LOW

Post-change `detect_changes(scope="unstaged")` prijavljuje HIGH za cijeli
radni tree, jer postoje i druge nekomitovane izmjene (`AGENTS.md`,
`CLAUDE.md`) i zato što report/dashboard procesi imaju širi indeksirani tok.
Scope ove izmjene je ostao ograničen na tražene fajlove.

## Šta je urađeno

- Dodan `check_cmd` u `FixAction`.
- Svih 5 postojećih Fix Center akcija sada imaju read-only status check.
- `_FixActionCard` pri kreiranju pokreće `check_cmd`; ako komanda vrati
  `True`, prikazuje `✓ Already active` i sakriva Apply dugme.
- Dodana `_build_summary(result: ScanResult) -> str` u dashboardu.
- Dashboard prikazuje mali info banner nakon skena sa `Found / Issues /
  Suggested` summary tekstom.
- HTML i Markdown report sada imaju `Client Summary` na vrhu i `Technical
  Details` prije postojećih detaljnih sekcija.

## Zašto je urađeno

Fix Center ne treba nuditi Apply za stanje koje je već aktivno. Dashboardu
treba kratki rule-based rezime nakon skena, bez AI i bez kompleksne logike.
Report treba imati čitljiv vrh za klijenta, dok tehnički detalji ostaju
dostupni ispod.

## Kako je urađeno

- Status check koristi postojeći `PowerShellRunner.run()` i komande koje
  vraćaju `True` ili `False`.
- Check komande su read-only i ne mijenjaju Windows postavke.
- Dashboard summary broji gatewaye, printere, realne LAN uređaje i issue-e,
  zatim bira preporučeni sljedeći korak po najgorem issue modulu.
- Report summary prikazuje broj issue-a, suggested next steps i osnovnu
  listu printera (`name`, `status`).

## Šta nije dirano

- Nisu dodane nove fix akcije.
- Nije dodana Danger Zone logika.
- Nije mijenjan `PowerShellRunner`.
- Nije mijenjana admin/elevation logika.
- Nisu mijenjane Windows postavke tokom testiranja.
- Nije uveden AI summary.

## Verifikacija

Prošlo:

```text
python -m pytest tests\gui\test_fix_center_status_check.py tests\gui\test_dashboard_summary.py tests\reports\test_report_writers.py -q
36 passed
```

Kompletan suite:

```text
python -m pytest tests\ -q
197 passed, 21 failed
```

Padovi nisu iz ovog scope-a:

- `tests/gui/test_topology_layout.py::test_printer_label_truncated_at_14_chars`
  očekuje 14 znakova, dok trenutni nekomitovani topology kod vraća 18.
- `tests/modules/printers/test_printers_scanner.py` pada na `StopIteration`
  zbog trenutnih nekomitovanih promjena u printer scanner flow-u i mock
  call order-u.

## Rizici / ograničenja

- Fix Center status check se pokreće pri kreiranju kartica, pa stranica radi
  nekoliko read-only PowerShell poziva pri otvaranju.
- Firewall status check koristi `netsh ... show rule` + `Select-String`, jer
  je to specifičan status legacy rule grupe; komanda ne mijenja postavke.
- Dashboard summary je namjerno rule-based i jednostavan; ne pokušava duboku
  dijagnostiku.

## Potreban follow-up

- Uskladiti topology test sa novim printer label ponašanjem ili vratiti label
  truncation na 14 znakova.
- Uskladiti printer scanner test mock redoslijed sa trenutnim printer scanner
  promjenama.

## Potrebna korisnička potvrda

Nije potrebna za ovu izmjenu. Preporučena ručna provjera: otvoriti Fix Center
na Windows mašini i potvrditi da već aktivne stavke prikazuju `✓ Already active`.
