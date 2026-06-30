# AGENTS.md

Ovo je mapa, ne knjiga. Kaže gdje šta da se nađe i kad se koji proces
pokreće. Plan razvoja je u `FieldFix_IT_integrisani_plan_v2.md` — to je
izvor istine za faze i zadatke. Ovaj fajl je samo operativni vodič za rad
na kodu.

Jezik, git konvencije, memory protokol i obavezna procedura nakon zadatka
su u `CLAUDE.md` — ovaj fajl ih ne duplira, samo referiše gdje treba.

## Gdje je šta

```text
docs/architecture_notes.md        — donesene arhitektonske odluke
docs/future_modules_backlog.md    — moduli koji NISU MVP
docs/target_gui.md                — referenca na ciljni GUI mockup (v3, ne v1)
agent_runbooks/                   — procedure za rizične promjene
agent_reports/                    — kratki izvještaj nakon svakog zadatka
```

MVP **ne uvodi** `agent_skills/` i `agent_loops/` — to su V2+ dodaci, dok
se ne pokaže potreba (vidi sekciju 15 integrisanog plana).

`project_rooms/` je uveden u laganoj, jednofajlovskoj formi (vidi
"Handoff visokog rizika" ispod) jer GitNexus impact analiza sada postoji
i daje konkretan signal kad je project room potreban — prije toga nije
imalo smisla formalizovati taj korak.

## Osnovna pravila

- Scan Mode je default. Ništa se ne mijenja na Windows sistemu bez
  eksplicitnog Apply u Fix Mode-u.
- Aplikacija se ne pokreće kao Administrator po defaultu (vidi
  `docs/architecture_notes.md`).
- Dashboard nikad ne izvršava fix direktno — uvijek "Review Fix" prvo.
- Svaki fix/preporuka mora imati vidljiv risk level (LOW/MEDIUM/HIGH/CRITICAL).
- Ne pisati plugin sistem (PluginBase/PluginManager) u MVP-u — moduli su
  plugin-ready, ne formalni plugin-ovi.
- Ne parsirati/izvršavati slobodan string kao kod (npr. iz knowledge YAML
  fajlova) — vidi `docs/architecture_notes.md`, "Knowledge Base" sekcija.

## Linkovanje odluka ka agent_reports

Svaka odluka upisana u `docs/architecture_notes.md` mora imati liniju
`> Report: [agent_reports/...](../agent_reports/...)` odmah ispod naslova
sekcije, koja vodi na konkretan agent report u kom je odluka donesena ili
promijenjena. Cilj: kod refaktoringa, čovjek/agent može pratiti "zašto je
ovo tako" do izvora, ne samo "šta je odlučeno". Ako se odluka kasnije
promijeni, dodaj novi agent report i ažuriraj/dodaj link — ne brisati stari
link bez razloga, da istorija odluke ostane vidljiva.

## Kad je agent report obavezan

Obavezan nakon zadatka koji dira:

- PowerShellRunner,
- fix akcije,
- firewall promjene,
- SMB promjene,
- admin/elevation logiku,
- decision engine,
- report generator,
- installer.

Nije obavezan za: UI tekst, mali layout detalj, README typo, sitnu lokalnu
izmjenu.

Format: `agent_reports/YYYY-MM-DD_kratak-naziv.md`.

## Kad je runbook obavezan

Za svaki zadatak koji dira HIGH/CRITICAL oblast (lista iznad) koristi:

```text
agent_runbooks/high_critical_code_change.md
```

## Handoff visokog rizika (HIGH/CRITICAL GitNexus impact)

Kada `gitnexus_impact()` vrati `HIGH` ili `CRITICAL` rizik za simbol koji
mijenjaš, PRIJE izmjene prijavi korisniku rizik u ovom formatu:

> "GitNexus impact za `<simbol>` je `<risk>`: zavise od njega `<broj>`
> simbola/procesa (`<koji>`). Promjena je mala/velika po obimu ali
> `<visoka/niska>` po sistemskoj važnosti jer `<razlog>`. Scope ostaje
> ograničen na: `<šta NE dirаš>`. Obavezan izlaz: `<šta MORA postojati —
> npr. ciljane izmjene + test pokrivenost>`."

Za svaku takvu izmjenu, prije pisanja koda, napraviti jedan kratak fajl
(ne cijeli višefajlovski "project room"):

```text
project_rooms/YYYY-MM-DD_kratak-naziv-zadatka.md
```

sa sekcijama:

- **Cilj** — šta se mijenja i zašto
- **Pogođeno** — simboli/procesi iz `gitnexus_impact` (broj, koji, rizik)
- **Plan** — fajlovi i redoslijed izmjena
- **Šta NE dirati** — eksplicitne granice (scope lock — format prijave
  rizika korisniku je iznad)
- **Konflikti** — ako postoje kontradiktorni izvori (stari agent_report,
  `docs/architecture_notes.md`, kod), navesti oba, koji se tretira kao
  važeći i zašto, i da li treba korisnička potvrda (DA/NE)

Fajl se na kraju može spojiti u `agent_report` ili obrisati — nije trajna
dokumentacija. Za MEDIUM ili niži impact ovaj korak se preskače.

## Format outputa

Na kraju zadatka, prije agent_report-a, sažeti rezultat ovako:

```text
STATUS: OK | PARCIJALNO | BLOKIRANO
IZMIJENJENI FAJLOVI: lista
ŠTA JE URAĐENO: kratko
ŠTA NIJE URAĐENO: (ako PARCIJALNO/BLOKIRANO)
PITANJA: (ako postoje)
```

## Provjera prije predaje

- [ ] Nisam mijenjao kod van scope-a zadatka.
- [ ] Nisam dodao nepotrebne komentare ili docstrings.
- [ ] Nisam ostavio zakomentarisan kod.
- [ ] Nijedna Windows postavka nije promijenjena bez eksplicitnog Apply
      poziva od korisnika (Scan Mode ostaje default).
- [ ] Svaki novi fix/preporuka ima vidljiv risk level.
- [ ] Testovi prolaze: `python -m pytest tests/ -q`
- [ ] Ako je dirana HIGH/CRITICAL oblast: runbook ispoštovan, project room
      (ako je trebao) i agent_report napravljeni, odluka linkovana u
      `docs/architecture_notes.md`.
- [ ] Output format je popunjen (STATUS, IZMIJENJENI FAJLOVI, itd.).

## Šta je zabranjeno

| Zabrana | Razlog |
| --- | --- |
| Automatski fix bez korisničke potvrde | Scan Mode / kontrolisani fix je osnovni princip aplikacije |
| SMB1 fix, Guest access fix, firewall off, policy change bez Danger Zone potvrde ("I understand this is risky") | Visok rizik za klijentsku mrežu |
| `eval()` ili slično izvršavanje stringa iz knowledge YAML fajlova | Vidi `docs/architecture_notes.md` — "Knowledge Base" (Opcija A) |
| Plugin Manager, AI assistant, remote execution, cloud sync u MVP-u | Nije MVP (sekcija 20 integrisanog plana) |
| Aplikacija pokrenuta kao Administrator po defaultu | Vidi `docs/architecture_notes.md` — "UAC / elevacija" |
| Dashboard dugme koje direktno izvršava fix (bez Review Fix koraka) | Vidi `docs/architecture_notes.md` — "Dashboard: Review Fix, ne Apply" |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **FieldFix-IT** (1852 symbols, 3433 relationships, 34 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/FieldFix-IT/context` | Codebase overview, check index freshness |
| `gitnexus://repo/FieldFix-IT/clusters` | All functional areas |
| `gitnexus://repo/FieldFix-IT/processes` | All execution flows |
| `gitnexus://repo/FieldFix-IT/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
