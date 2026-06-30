# Agent report: Dashboard v2 (Faza 11)

## Datum
2026-06-30

## Scope
- `app/core/scan_session.py` (novo)
- `app/gui/dashboard.py` (rewrite)
- `app/gui/widgets/status_card.py` (update — `update()` metoda)
- `app/gui/widgets/system_info_widget.py` (update — `update_data(network)`)
- `app/gui/widgets/recent_scan_widget.py` (rewrite — `update_data(report)`)
- `app/gui/widgets/issues_widget.py` (rewrite — `update_data(issues)`)
- `app/gui/widgets/quick_actions_widget.py` (rewrite — `update_data(issues)`)
- `app/gui/widgets/timeline_widget.py` (rewrite — `TimelineEvent`, `update_data(events)`)

## GitNexus impact
- `ScanSession` je novi simbol — nema upstream importera osim `DashboardPage`
- Widget izmjene su backward-compatible (zadržan `__init__` interfejs)
- LOW rizik

## Šta je urađeno

### `app/core/scan_session.py` (novo)

Implementirana `ScanSession` klasa (uvedena u Fazi 11 per arhitektonska odluka):
- `ScanResult(frozen=True)`: report, issues, scanned_at (ISO 8601)
- `ScanSession(runner).run(smb_target_ip, on_progress)`: pokrenemo
  NetworkScanner → SmbScanner → ServicesScanner → PrintersScanner →
  DecisionEngine; vraća `ScanResult`
- `on_progress: Callable[[str], None]` za UI feedback bez threadova

### `app/gui/widgets/` — refaktor (dummy → real data)

Svaki widget zadržava identičan `__init__` (nema breaking promjena), ali dobija:
- `self._content = QVBoxLayout()` kao odvojeni content sublayout
- `update_data()` metodu koja poziva `_clear_layout(self._content)` pa gradi nove redove

Specifično:
- **StatusCard**: dodat `self._value_label` + `update(value, status)` metoda
- **SystemInfoWidget**: `update_data(network: NetworkData | None)` — hostname,
  OS (via `sys.getwindowsversion()` s Win11 detekcijom build >= 22000), IPv4,
  subnet mask (prefix→mask konverzija), gateway+reachable, DNS, profil, adapter
- **RecentScanWidget**: `update_data(report: ScanReport)` — gateway ping,
  port 445, SMB1 status, 4 servisa (LanmanServer, Workstation, FDResPub, Spooler),
  broj štampača
- **IssuesRecommendationsWidget**: `update_data(issues)` — top 6 sa
  severiti-bojom (HIGH=red, MEDIUM=yellow, LOW=green)
- **QuickActionsWidget**: `update_data(issues)` — top 4 issue-a kao "Review"
  dugme (inertno do Faze 13)
- **ActivityTimelineWidget**: `TimelineEvent` NamedTuple + `update_data(events)`

### `app/gui/dashboard.py` (rewrite)

- Header panel: "Run Diagnostics" dugme + status label
- 6 imenovanих `StatusCard` instanci (network, smb, services, printers, issues, firewall)
- `_run_scan()`: `ScanSession.run(on_progress=_progress)` → `_update_dashboard()`
- `_module_status(issues, module)` helper: derivira ok/warning/critical iz issues tuplea
- `_build_timeline_events(result)` — gradi TimelineEvent listu iz ScanResult
- Firewall card ostaje "—" / neutral (Dashboard ne skenira Firewall)
- NetworkTopologyWidget i DecisionAssistantWidget ostaju sa dummy podacima (Faza 12)

## Šta nije dirano
- `app/gui/pages/` — sve module stranice netaknute
- `app/gui/main_window.py` — bez izmjena
- `app/gui/widgets/topology_widget.py` — ostaje dummy (Faza 12)
- `app/gui/widgets/decision_assistant_widget.py` — ostaje dummy (kasniji)
- Nijedna Windows postavka nije promijenjena

## Verifikacija
```
199 passed in 0.85s
```
Svi importi prošli bez grešaka.

**Potrebna korisnička potvrda:** izgled Dashboarda na stvarnom Windows uređaju
(posebno layout sa svim karticama i widgetima pri različitim rezolucijama).

## Rizici / ograničenja
- Skeniranje u main threadu (isto kao module stranice) — UI blokira za
  vrijeme scana. Za MVP je ok (progress callback + processEvents() drže UI
  relativno responsivnim). Pravi QThread za V2.
- Firewall card ostaje "—" dok Faza 6 (dev-firewall) ne bude merge-ovan i
  Dashboard ne bude ažuriran da i Firewall skenira

## Potreban follow-up
- Faza 12 — Topology v1 (Codex, dev-topology grana)
- Faza 13 — Fix Center v1 (Review → Apply flow)
- dev-topology i dev-firewall PR → merge u dev
