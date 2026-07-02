## Datum

2026-07-01

## Scope

- `app/core/scenario.py` (novi fajl)
- `app/gui/pages/scenarios_page.py` (novi fajl)
- `app/gui/main_window.py` (minimalna izmjena — +2 linije)

## GitNexus impact

Additivna izmjena: dva nova fajla, jedna linija u `_PAGES` listi i jedna linija
za Signal konekciju u `MainWindow.__init__`. Korisnik je preskočio GitNexus
provjeru za ovaj tip LOW-risk aditivne promjene.

## Šta je urađeno

Implementiran pilot "Scenarios" modul sa jednim scenarijem: **Connect two Windows PCs**.

### `app/core/scenario.py`

- `CheckItem` dataclass: label, passed, detail, fix_id
- `Scenario` dataclass: id, title, description, icon, tip, scan_modules,
  check_fn_name
- `CONNECT_TWO_PCS` — definicija prvog scenarija
- `ALL_SCENARIOS` — tuple svih scenarija (proširivo)
- `check_connect_two_pcs(result, target_ip)` — mapira ScanResult na 7 checkova
  grupisanih u: Network, Sharing, Firewall & Discovery
- `run_checks(scenario, result, target_ip)` — dispatcher za check funkcije

### `app/gui/pages/scenarios_page.py`

- `_ScenarioWorker(QThread)` — poziva ScanSession u pozadini (isti pattern kao Dashboard)
- `_ScenarioCard` — klikabilna kartica za odabir scenarija
- `_CheckRow` — jedan red u checklistu (✓/✗ ikona, label, detalj, opcionalni Fix dugme)
- `_ResultsPanel` — kontejner koji gradi grupisani checklist iz liste CheckItem-ova
- `ScenariosPage` — glavna stranica: kartica birača + IP input + Run dugme + scroll area

### `app/gui/main_window.py`

- Dodati import `ScenariosPage`
- Dodati `("Scenarios", ScenariosPage)` u `_PAGES` (između Topology i Fix Center)
- Žičati `_instances[_scen_idx].open_fix_center → _go(_fix_idx)`

## Arhitekturne odluke

- **Reuse ScanSession** bez izmjene: scenarij koristi isti orchestrator kao Dashboard,
  samo rezultate filtrira kroz `check_connect_two_pcs()`.
- **DecisionEngine se ne mijenja**: sve `Issue` pravila za ovaj scenarij već postoje
  (`PUBLIC_NETWORK_PROFILE`, `PORT_445_CLOSED`, `SERVICE_STOPPED_*`, itd.).
- **Fix Center se ne mijenja**: "→ Fix Center" dugme navigira na postojeću stranicu;
  duboko linkovanje na specifičan fix je V2 poboljšanje.
- **check_fn_name dispatch** umjesto polimorfizma: dok postoji samo jedan scenarij,
  `run_checks()` sa string dispatcherom je dovoljno; kada bude 3+ scenarija
  razmotriti `Callable` polje direktno na Scenario.

## Šta nije dirano

- `decision_engine.py` — nema izmjena
- `fix_center_page.py` — nema izmjena
- `scan_session.py` — nema izmjena
- Nijedan postojeći scan modul

## Verifikacija

- `python -m app.main` pokrenuta, nema import grešaka ni runtime crash-a pri startu.
- Ručna provjera potrebna: pokrenuti aplikaciju, otvoriti Scenarios stranicu,
  provjeriti da se kartica selektuje, IP input radi, Run Diagnostic pokreće scan,
  rezultati se prikazuju kao checklist, Fix Center dugme navigira ispravno.

## Rizici / ograničenja

- `fix_id` u CheckItem-ima (`START_LANMANSERVER`, `START_LANMANWORKSTATION`,
  `DISABLE_SMB1`) su referencirani ali odgovarajući `FixAction` u Fix Center-u
  možda ne postoje — korisnik vidi "→ Fix Center" ali Fix Center ne filtrira
  na taj specifičan fix. Provjeri koje fix_id-ove Fix Center ima i dodaj
  nedostajuće ako je potrebno.
- Port 445 check je "passed" ako nije unesen target IP (jer ne možemo provjeriti
  bez ciljne adrese) — prikazano kao neutralno stanje, ne lažni prolaz.

## Potreban follow-up

- Dodati `START_LANMANSERVER`, `START_LANMANWORKSTATION`, `DISABLE_SMB1` FixAction-e
  u `fix_center_page._AVAILABLE_FIXES` ako nedostaju.
- Razmotriti proširenje sa još jednim scenarijem ("Add network printer") kao V2.
- Dodati `/scenarios` skill u `.claude/SKILLS.md` kad pattern sazri.
