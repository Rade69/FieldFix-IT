# Agent report: Decision Engine v1 (Faza 10)

## Datum
2026-06-30

## Scope
- `app/core/decision_engine.py` (novo)
- `app/reports/json_report.py` (update — dodan `issues` parametar)
- `app/reports/markdown_report.py` (update — Issues sekcija + `issues` parametar)
- `app/reports/html_report.py` (update — Issues sekcija + `issues` parametar)
- `app/gui/pages/reports_page.py` (update — poziva DE, proslijeđuje issues writerima)
- `tests/core/test_decision_engine.py` (novo)
- `docs/architecture_notes.md` (update — Engine pattern odluka)
- `README.md` (update — arhitektura sekcija)

## GitNexus impact (provjera prije izmjene)
- Novi fajl `decision_engine.py` — nema upstream importera
- Izmjene u report writerima: non-breaking (novi opcionalni `issues=()` param)
- LOW rizik za sve izmjene

## Šta je urađeno

### Postojeći core modeli (Zadatak 2 — nisu mijenjani)
Pronađeni u `app/core/`: `RiskLevel` (IntEnum: LOW=1, MEDIUM=2, HIGH=3, CRITICAL=4),
`Issue` (id, title, severity, evidence, likely_cause, confidence, recommended_actions,
related_module), `Recommendation`, `DiagnosticResult`, `ScanStatus`.
Korišćeni su direktno — bez duplikata.

### `app/core/decision_engine.py`

`DecisionEngine.analyze(report: ScanReport) → tuple[Issue, ...]`

**23 pravila u 5 metoda:**

`_analyze_network` (4 pravila):
- `NO_ACTIVE_ADAPTERS` → HIGH
- `NO_GATEWAY` → HIGH
- `GATEWAY_UNREACHABLE` → HIGH
- `PUBLIC_NETWORK_PROFILE` → MEDIUM

`_analyze_smb` (9 pravila):
- `SMB1_ENABLED_SERVER` → HIGH
- `SMB1_ENABLED_CLIENT` → MEDIUM
- `GUEST_LOGONS_ENABLED` → MEDIUM
- `PORT_445_CLOSED` → HIGH
- `NET_VIEW_ERROR_53` → HIGH (network path not found)
- `NET_VIEW_ERROR_6118` → MEDIUM (server list unavailable)
- `NET_VIEW_ERROR_1272` → MEDIUM (guest access blocked)
- `NET_VIEW_ERROR_5` → MEDIUM (access denied)
- `NET_VIEW_ERROR_86/1326` → MEDIUM (wrong password)

`_analyze_combined` (2 kompozitna pravila iz plana):
- `FIREWALL_PORT_445_BLOCKED`: gateway ok + port 445 fail → HIGH
- `BROWSING_PROBLEM_NOT_SMB`: net view 6118 + port 445 ok → MEDIUM

`_analyze_services` (5 pravila):
- `SERVICE_STOPPED_LANMANSERVER` → HIGH
- `SERVICE_STOPPED_LANMANWORKSTATION` → HIGH
- `SERVICE_STOPPED_SPOOLER` → MEDIUM
- `SERVICE_STOPPED_FDRESPUB` → LOW
- `SERVICE_STOPPED_FDPHOST` → LOW

`_analyze_printers` (3 pravila):
- Printer status not in {"Normal", "Printing"} → HIGH (Error/Offline) ili MEDIUM
- Stuck print job (status contains "Error") → LOW

Rezultat sortiran: HIGH > MEDIUM > LOW (IntEnum ordering).

### Report writeri (update)

Svi 3 writera dobili opcionalni `issues: tuple[Issue, ...] = ()` parametar.
Izlaz sadrži **Issues sekciju kao prvu** (pregled HIGH/MEDIUM/LOW broja + detalji
per issue s evidence, likely_cause, recommended_actions).

`json_report`: `_issue_to_dict()` helper koji `str(issue.severity)` daje "HIGH"
(via `RiskLevel.__str__` = `self.name`).

### Architecture decision

Dodan u `docs/architecture_notes.md`: Engine pattern (Scanner/Decision/Report/Fix)
je formalna arhitektura; `ScanSession` koordinator dolazi u Fazi 11.
`README.md` ažuriran s arhitektura sekcijom.

## Šta nije dirano
- `ScanReport` model — nije promijenjen (issues nisu polje u ScanReport,
  vraćaju se zasebno iz DE; writerima se prosljeđuju kao parametar)
- Nijedna Windows postavka nije promijenjena
- Ostali moduli — netaknuti

## Verifikacija
```
196 passed in 0.91s
```
(26 novih testova u test_decision_engine.py)

## Rizici / ograničenja
- **Decision Engine nema pristup prethodnim scanovanjima** — svaki poziv je
  stateless. Historijski trendovi (npr. "servis je bio aktivan juče") dolaze
  u V2+ s persistence slojem
- **Confidence je "High" za sve pravila u v1** — granularnije confidence scoring
  (uzimajući u obzir kombinovane faktore) je posao za DE v2

## Potreban follow-up
- Faza 11 — Dashboard v2 (pravi podaci + Issues lista)
- Faza 12 — Topology v1 (Codex, na `dev-topology` grani)
- Faza 13 — Fix Center v1
