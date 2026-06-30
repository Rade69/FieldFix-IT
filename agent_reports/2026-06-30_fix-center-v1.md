# Agent report: Fix Center v1 (Faza 13)

## Datum
2026-06-30

## Scope
- `app/gui/pages/fix_center_page.py` (novo)
- `app/gui/main_window.py` (update — Fix Center stranica + signal wiring)
- `app/gui/widgets/quick_actions_widget.py` (update — `open_fix_center` Signal)
- `app/gui/dashboard.py` (update — propagacija signala)

## GitNexus impact (provjera prije izmjene)
- `QuickActionsWidget` → d=1: `dashboard.py` → d=2: `main_window.py` → LOW
- `DashboardPage` → d=1: `main_window.py` → LOW
- `MainWindow` → d=1: `main.py` → LOW
- Sve izmjene su aditivne (novi Signal, nova stranica) — nema breaking promjena

## Šta je urađeno

### `app/gui/pages/fix_center_page.py` (novo)

**`FixAction`** (frozen dataclass): id, title, description, what_it_changes,
risk_level, requires_admin, ps_command.

**5 akcija u scope-u Faze 13** (sve LOW, sve zahtijevaju admin):
1. `SET_NETWORK_PRIVATE` — Public → Private profil
2. `ENABLE_NETWORK_DISCOVERY` — netsh advfirewall firewall rule group enable
3. `ENABLE_FILE_PRINTER_SHARING` — netsh advfirewall firewall rule group enable
4. `START_PRINT_SPOOLER` — Start-Service + Set-Service Automatic
5. `START_FDRESPUB` — Start-Service

**`_FixActionCard`** (QFrame per akcija):
- Title + RiskBadge, opis, metadata (what_it_changes, "⚠ Requires admin")
- Apply dugme: **ako nije admin → disabled** sa tooltipom
- Apply flow: `QMessageBox.question()` → confirm → `runner.run()` → show result
- Retry: dugme postaje "▶ Retry" ako PS vrati grešku

**`FixCenterPage`**:
- Header s admin status badge-om (zeleni "✓ Administrator" ili žuti "⚠ Standard user")
- Žuti banner ako nije admin (objašnjava kako pokrenuti kao admin)
- QScrollArea s `_FixActionCard` widgetima za svaku akciju

**Admin detekcija**: koristi modul-level `is_admin()` iz `powershell_runner.py`
(ctypes.windll.shell32.IsUserAnAdmin) — ne metoda na klasi.

### Sigurnosne garancije (per arhitektura)
- Apply se ne izvršava bez `QMessageBox.question()` confirm — UVIJEK
- Ako nije admin: Apply dugme disabled, nije moguće zaobići
- PS komande su hardcoded u Python kodu — ne čitaju se iz YAML ni iz external inputa
- Nema automatskog Apply — korisnik mora kliknuti dugme za svaku akciju
- HIGH/CRITICAL akcije nisu u ovom scope-u (samo LOW/MEDIUM)
- `netsh` komande koriste interne group nazive (locale-independent)

### Navigacioni signal

`QuickActionsWidget.open_fix_center = Signal()` — emituje se kad korisnik
klikne "Open Fix Center". `DashboardPage.open_fix_center = Signal()` — propagira
signal navišе. `MainWindow` drži referencu na DashboardPage (index 0) i
koneкtuje signal na `pages.setCurrentIndex(fix_center_idx)`.

## Šta nije dirano
- `app/core/` modeli — netaknuti
- Nijedna stranica osim main_window (samo dodat import i stranica u listu)
- Nijedna Windows postavka nije promijenjena (Fix Center samo UI — ništa ne
  mijenja bez korisnikove potvrde)

## Verifikacija
```
209 passed in 0.88s
```

**Potrebna korisnička potvrda:**
- Izgled Fix Center stranice u GUI
- Ponašanje Apply/Cancel dijaloga
- Provjera admin detekcije (da li badge pokazuje tačno stanje)
- Faktičko pokretanje jedne akcije (npr. Start FDResPub) kao admin

## Rizici / ograničenja
- `netsh advfirewall firewall set rule group=...` ne vraća strukturisani JSON
  (legacy CLI) — uspjeh se detektuje po exit code-u (0 = OK), ne po parsiranom
  outputu. Može se desiti da komanda "uspije" a pravilo nije primijenjeno
  (npr. rule group ne postoji). Za V2: provjera stanja pravila poslije apply.
- Kada je app standardni user, Apply button je disabled — korisnik mora
  da zatvori app i ponovo pokrene kao Administrator. Per-action elevation
  (runas) odgođena za V2 per arhitektonska odluka.

## Potreban follow-up
- Faza 13 v2: per-action UAC elevation (runas helper proces)
- Faza 13 v2: filtriranje akcija po detektovanim issues (samo relevantne)
- MVP je sada kompletan (Faze 1–14)
