# Agent report: PowerShellRunner (Zadatak 3)

## Datum
2026-06-30

## Scope
- `app/core/powershell_runner.py` (novo)
- `tests/core/test_powershell_runner.py` (novo)

## GitNexus impact (provjera prije izmjene)
- Target: `CommandResult` (jedini tip koji PowerShellRunner vraća)
- Rezultat: **LOW** — 0 direktnih kalera, 0 procesa pogođeno
- Razlog: PowerShellRunner je novi simbol, ne modifikacija postojećeg

## Šta je urađeno

### `app/core/powershell_runner.py`

Implementirane su dvije javne metode i jedna helper funkcija:

**`PowerShellRunner.run(command, timeout=30) → CommandResult`**
- Pokreće `powershell.exe -NoProfile -NonInteractive -Command <cmd>`
- Vraća `CommandResult` sa svim fieldovima: `stdout` (stripped), `stderr`,
  `exit_code`, `duration_ms`, `timed_out`, `raw_output` (unstripped, za
  legacy text parsere)
- Timeout: hvata `subprocess.TimeoutExpired`, postavlja `timed_out=True`,
  `exit_code=None`; parcijalni stdout je sačuvan u `raw_output`

**`PowerShellRunner.run_json(command, timeout=30) → CommandResult`**
- Interno poziva `run()`, pa na uspješnom stdout-u radi `json.loads()`
- Popunjava `CommandResult.parsed_json` (već postojeći field iz Zadatka 2)
- Na grešci (JSONDecodeError, neuspješna komanda, prazan stdout):
  `parsed_json` ostaje `None` — nije exception, caller mora provjeriti

**`is_admin() → bool`**
- Wrapper za `ctypes.windll.shell32.IsUserAnAdmin()`
- Hvata sve exceptione, vraća `False` — sigurno za pozivanje na
  non-Windows platformama i u testovima

### `tests/core/test_powershell_runner.py`

17 testova, svi mockuju `subprocess.run` — nema stvarnih PowerShell poziva:
- `TestRun` (7): uspješan poziv, nonzero exit, strip vs raw_output, timeout,
  duration, command storage, bytes decoding pri timeoutu
- `TestRunJson` (6): JSON lista, JSON dict, invalid JSON, failed command,
  prazan stdout, preservacija ostalih fieldova
- `TestIsAdmin` (4): vraća bool, mock True/False/exception

## Zašto je urađeno ovako

- **Frozen dataclass + `dataclasses.replace()`**: `CommandResult` je frozen
  (immutable snapshot); `run_json()` kreira novu instancu sa `parsed_json`
  umjesto da mutira
- **`run_json()` vraća `CommandResult`, ne tuple**: `parsed_json` field već
  postoji na `CommandResult` (Zadatak 2), tako da nema potrebe za tupletom —
  caller dobija jedan konzistentan tip iz oba metoda
- **UTF-8 + `errors='replace'`**: PS na Windowsu može da vrati non-UTF8
  bajtove; `errors='replace'` sprečava crash dok `raw_output` čuva originalni
  sadržaj za debugging

## Šta nije dirano

- Nijedna Windows postavka nije promijenjena (Scan Mode princip)
- Fix komande nisu implementirane (scope: Faza 13 — Fix Center)
- GUI nije dirano
- Svi ostali fajlovi u `app/core/` su netaknuti

## Verifikacija

```
35 passed in 4.32s
```

- Postojećih 18 testova i dalje prolaze (nema regresije)
- 17 novih testova prolaze; nema stvarnih PS poziva u testovima

## Rizici / ograničenja

- **Encoding edge case**: PS može da ispiše UTF-16 ili CP1250 u nekim
  edge case-ovima (npr. stariji Windows s non-UTF8 locale). `errors='replace'`
  sprečava crash ali može da korumpira output. Pratiti u Faza 4 (Network
  module) sa stvarnim PS pozivima
- **PowerShell startup overhead**: `-NoProfile` smanjuje overhead, ali svaki
  `run()` pokreće novi PS proces (~200-500ms). Ako Faza 4 ispadne presporo,
  razmotriti runspace pooling (V2)
- **`is_admin()` MVP ograničenje**: detektuje samo globalni admin status
  procesa, ne granularne dozvole. Per-action elevation (helper process) je V2

## Potreban follow-up

- **Faza 4 (Network module)**: prvi pravi potrošač `PowerShellRunner.run_json()`;
  testirati sa `Get-NetAdapter | ConvertTo-Json` na stvarnom Windowsu
- **Admin UX**: MVP putanja (detect non-admin → prikaži poruku "restart as
  admin needed") još nije vezana za GUI — uraditi u Fazi 13 (Fix Center)
- Razmotriti `gitnexus analyze --force` ako FTS indeksi ostanu zastarjeli
  (FTS warning je pojavio se pri `gitnexus_query` pozivu)

## Potrebna korisnička potvrda

Nema direktnih Windows poziva u ovom zadatku — sve je mocked u testovima.
Stvarna verifikacija PS poziva (encoding, startup time) dolazi u Fazi 4.
