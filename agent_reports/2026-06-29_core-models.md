# Agent report — Core modeli (Zadatak 2)

Datum: 2026-06-29

## Scope

`app/core/` (novi paket): `risk_level.py`, `scan_status.py`,
`command_result.py`, `issue.py`, `recommendation.py`,
`diagnostic_result.py`. `tests/core/` sa odgovarajućim unit testovima.
GUI nije diran.

## GitNexus impact

Nije relevantno — svi fajlovi su novi, nemaju postojeće callere, nula
postojećeg rizika po definiciji. `npx gitnexus analyze` pokrenut nakon
izmjena radi svježeg indeksa (406 simbola, 494 relacije, vs. 275/311
prije).

## Šta je urađeno

- `RiskLevel(IntEnum)` — LOW/MEDIUM/HIGH/CRITICAL, prirodno uređenje
  (`RiskLevel.HIGH > RiskLevel.LOW`) radi buduće upotrebe u Decision
  Engine-u i Fix Center-u (npr. "blokiraj Apply ako risk >= HIGH dok
  korisnik ne potvrdi Danger Zone").
- `ScanStatus(Enum)` — OK/WARNING/CRITICAL/ERROR/NOT_CHECKED, status
  jednog modula nakon skeniranja.
- `CommandResult` (frozen dataclass) — command, stdout, stderr,
  exit_code, duration_ms, timed_out, requires_admin, parsed_json,
  raw_output, plus `succeeded` property (False ako je timeout ili
  exit_code nije 0/None).
- `Issue` (frozen dataclass) — id, title, severity (RiskLevel), evidence,
  likely_cause, confidence (string "High"/"Medium"/"Low" — bez posebnog
  enum-a, da se ne uvodi 7. model van onog što je traženo), recommended_actions,
  related_module.
- `Recommendation` (frozen dataclass) — title, risk_level, action_id,
  what_it_changes, what_it_does_not_change, requires_admin, can_apply,
  reason_if_not_applicable.
- `DiagnosticResult` (frozen dataclass) — module, status, issues,
  recommendations, evidence, duration_ms.
- 18 unit testova ukupno (12 novih za core modele + 6 ranijih GUI smoke
  testova), svi prolaze.

## Zašto je urađeno

Sekcija 7 integrisanog plana (v2) definiše ovih 6 modela kao MVP core,
potrebnih prije PowerShellRunner-a (Zadatak 3) i prvog modula (Zadatak 4,
Network). Modeli su namjerno bez ponašanja/logike — samo oblik podataka,
kako Zadatak 2 i traži ("Ne implementirati PowerShellRunner").

## Kako je urađeno

Plain Python `@dataclass(frozen=True)` za sve modele osim enuma — frozen
jer su ovo value-objekti (snapshot rezultata skeniranja), ne treba im
mutabilnost u ovoj fazi. `RiskLevel` je `IntEnum` radi poređenja
(`>=`, `<`), `ScanStatus` je plain `Enum` jer mu poređenje po vrijednosti
nije potrebno.

## Šta nije dirano

- GUI (main_window, dashboard, widgets) — `RiskBadge` i dalje prima
  string level; wiring na `RiskLevel` enum ide kad dashboard počne
  koristiti stvarne `Issue`/`Recommendation` objekte (Faza 11).
- PowerShellRunner — Zadatak 3.
- Nijedna logika zaključivanja (Decision Engine) — Faza 10.

## Verifikacija

- `python -m pytest tests/ -q` → 18 passed.
- `npx gitnexus analyze` → bez greške, brojke porasle u skladu sa novim
  fajlovima.

## Rizici / ograničenja

- Nema — modeli su bez spoljnih efekata, ne dodiruju Windows sistem.

## Potreban follow-up

Zadatak 3 — PowerShellRunner, koji će biti prvi pravi proizvođač
`CommandResult` instanci. To je HIGH/CRITICAL oblast po `AGENTS.md`
("Kad je agent report obavezan") — treba koristiti
`agent_runbooks/high_critical_code_change.md` i, ako GitNexus impact
pokaže HIGH/CRITICAL nakon prvih callera, `project_rooms/`.

## Potrebna korisnička potvrda

Nema ničeg za ručnu provjeru — bez GUI ili Windows efekata.
