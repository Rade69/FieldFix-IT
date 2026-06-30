# Architecture notes / odluke

Ovaj fajl drži odluke koje su donesene tokom planiranja, da se ne improvizuju
ponovo kasnije (od strane čovjeka ili agenta).

## Modularni monolit, ne plugin system (MVP)

> Report: [agent_reports/2026-06-29_initial-skeleton.md](../agent_reports/2026-06-29_initial-skeleton.md)

MVP koristi `app/modules/<name>/` strukturu (scanner.py, models.py,
recommendations.py) koja je *plugin-ready*, ali bez `PluginBase` /
`PluginManager`. Formalni plugin sistem se uvodi tek kad se ponavljanje
između modula stabilizuje (V3).

## PowerShell: JSON prvo, tekst fallback

> Report: [agent_reports/2026-06-29_initial-skeleton.md](../agent_reports/2026-06-29_initial-skeleton.md)

Svaki PowerShellRunner pozivi treba da koriste strukturisane cmdlete sa
`ConvertTo-Json` gdje god postoje (Get-NetAdapter, Get-SmbShare, Get-Service,
itd). Legacy komande (`net view`, `net share`, `arp -a`) koriste se samo kao
fallback ili za prepoznavanje specifičnih Windows error kodova, i njihov
text-parsing mora biti izolovan u posebnom, testiranom parseru — ne
raspoređen po kodu.

## UAC / elevacija

> Report: [agent_reports/2026-06-29_initial-skeleton.md](../agent_reports/2026-06-29_initial-skeleton.md)

Aplikacija se **ne pokreće** kao Administrator po defaultu. Default je
"Normal user + Scan Mode". Elevacija se traži po fix akciji; za MVP je to
jednostavno: app detektuje da nije admin i fix dugme javlja da je potreban
restart kao Administrator. Per-action elevacija kroz helper proces je V2+
poboljšanje, ne MVP zahtjev.

## Dashboard: Review Fix, ne Apply

> Report: [agent_reports/2026-06-29_initial-skeleton.md](../agent_reports/2026-06-29_initial-skeleton.md)

Dashboard nikad ne izvršava fix direktno. Tok je:

```text
Dashboard issue → Review Fix → Fix Center → explanation → Apply / Skip
```

Čak i LOW risk akcija prolazi kroz confirm dijalog.

## Knowledge Base: `confidence_rules` je dokumentaciono polje (Opcija A)

> Report: [agent_reports/2026-06-29_initial-skeleton.md](../agent_reports/2026-06-29_initial-skeleton.md) — odluka donesena nakon razmatranja u razgovoru (rizik od `eval()` na string pravilima iz YAML-a).

Odlučeno: YAML knowledge fajlovi (`app/knowledge/**/*.yaml`) mogu imati
polje koje opisuje logiku zaključivanja (npr. nešto poput
`confidence_rules`), ali **to polje se ne parsira ni izvršava u kodu**.

Razlog: string koji liči na kod (`if X and Y: Z`) bi morao biti parsiran
nekim DSL interpreterom ili, najgore, proslijeđen kroz `eval()` — što je
sigurnosni i robusnosni rizik (izvršavanje proizvoljnog stringa kao kod),
pogotovo ako knowledge fajlovi kasnije dolaze iz manje pouzdanih izvora
(deljeni fajlovi, V3 plugin marketplace).

**Pravilo:**

- YAML knowledge fajl sadrži samo statične, opisne podatke: `meaning`,
  `likely_causes`, `recommended_checks`, `safe_fixes`, `dangerous_fixes`, i
  opciono `notes` / `rationale` kao tekst za čovjeka/agenta.
- Stvarna logika zaključivanja (npr. "net_view_error == 6118 i direct IP
  pristup radi → browsing problem, ne SMB connectivity problem") se piše
  kao pravi Python kod u `app/core/decision_engine.py` (Faza 10).
- Ako se ikad poželi data-driven pravila bez izmjene koda, prelazi se na
  strukturisan format (`when: {...}` / `conclusion: ...`), nikad na
  slobodan string koji se evaluira.

Ova odluka važi za Zadatak 5 (SMB module + knowledge YAML) i Fazu 10
(Decision Engine v1).

## PowerShellRunner: dizajn i ograničenja (MVP)

> Report: [agent_reports/2026-06-30_powershell-runner.md](../agent_reports/2026-06-30_powershell-runner.md)

`PowerShellRunner` živi u `app/core/powershell_runner.py` i jedina je tačka
ulaza za sve PS pozive u aplikaciji.

Dvije javne metode:

- `run(command, timeout)` → `CommandResult` (raw stdout/stderr)
- `run_json(command, timeout)` → `CommandResult` sa popunjenim `parsed_json`

Poziva `powershell.exe -NoProfile -NonInteractive -Command <cmd>`.
UTF-8 enkoding, `errors='replace'` za robusnost.

**Scan-only**: ova klasa nikad ne izvršava fix komande — to je rezervisano
za Fix Center (Faza 13) koji zahtijeva eksplicitni Apply od korisnika.

**Admin detekcija**: `is_admin()` helper (`ctypes.windll.shell32.IsUserAnAdmin`).
MVP putanja: app detektuje ne-admin status i fix akcija kaže "restart as
admin required". Per-action elevation je V2+.

**Encoding rizik**: `-NoProfile` smanjuje startup overhead, ali PS može
vratiti non-UTF8 u edge case-ovima. `raw_output` field čuva unstripped
original za legacy parsere. Pratiti pri prvim stvarnim pozivima (Faza 4).

## Agent workflow: GitNexus handoff format + project_rooms (lagana forma)

> Report: [agent_reports/2026-06-29_agent-workflow-claude-md.md](../agent_reports/2026-06-29_agent-workflow-claude-md.md)

Nakon što je GitNexus indeksirao projekat, preneseno je (i prilagođeno iz
ranijeg radnog obrasca na drugom projektu) sljedeće:

- Formalan "Handoff visokog rizika" format za prijavu HIGH/CRITICAL
  GitNexus impact rezultata korisniku PRIJE izmjene (`AGENTS.md`).
- `project_rooms/` kao jednofajlovski (ne višefajlovski) artefakt, koji
  se pravi samo kad GitNexus impact vrati HIGH/CRITICAL — prije GitNexus
  indeksiranja ovo nije imalo pouzdan trigger, pa je bilo ispravno
  odgoditi ga (vidi sekciju 15.3 integrisanog plana).
- Konvencija jezika (srpski latinica), git format poruka i obavezna
  procedura nakon zadatka su izdvojeni u novi `CLAUDE.md`, da se ne
  dupliraju sa `AGENTS.md`.

**Svjesna razlika od ranijeg obrasca:** auto-commit nakon svakog zadatka
NIJE prenesen — ovdje commit zahtijeva eksplicitnu korisničku potvrdu
(vidi `CLAUDE.md`, "Obavezna procedura nakon završenog zadatka", Korak 1).
Taj dio ranijeg workflow-a je u sukobu sa pravilom po kom Claude Code radi
po defaultu i nije prenesen bez pitanja.
