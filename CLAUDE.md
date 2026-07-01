# CLAUDE.md - Projektne instrukcije za AI asistenta

## ⚠️ JEZIK: ISKLJUČIVO SRPSKI LATINICA

- Svi odgovori, objašnjenja, komentari za korisnika: **srpski jezik, latinica**.
- Nikad ćirilica — nigdje, ni u komentarima ni u stringovima koji se prikazuju.
- Komentari u kodu: engleski (kod je u Pythonu/PySide6, prati postojeći stil fajla).
- Commit poruke: srpski latinica, format `tip(oblast): opis` (npr. `feat(network): dodaj ARP scan`).

## Memorija — kako stvarno radi u ovom okruženju

Ovaj projekat **ne koristi** poseban MCP memory server sa `project_id` i
alatima poput `get_project_context` / `search_project_memory` (to je bio
pattern na nekom ranijem projektu, ovdje ta infrastruktura ne postoji).

Ovdje memorija radi u dva sloja:

1. **Repo dokumentacija (autoritativni izvor, vidljiv svim alatima):**
   `docs/architecture_notes.md` (odluke), `docs/future_modules_backlog.md`,
   `docs/target_gui.md`, `agent_reports/` (istorija zadataka). Pročitaj
   `docs/architecture_notes.md` prije bilo kakvog netrivijalnog kodiranja.
2. **Claude Code auto-memory (samo radne navike, cross-session):**
   fajlovi pod `~/.claude/projects/.../memory/` se automatski učitavaju na
   početku sesije (`MEMORY.md` indeks). Ovo NIJE mjesto za projektne
   odluke (one idu u sloj 1) — ovdje ide samo "kako da radim s ovim
   korisnikom" (npr. navika linkovanja odluka ka agent_reports, navika da
   se GitNexus indeksira odmah pri inicijalizaciji projekta).

Ako su ova dva sloja u sukobu, repo dokumentacija (sloj 1) je tačnija —
ona je verzionisana i vidljiva i drugim agentima (Qwen, Copilot, Cursor,
itd. ako se ikad uključe na ovom projektu), auto-memory je samo moj lični
radni kontekst.

## Tech stack

| Sloj | Tehnologija |
| --- | --- |
| GUI | PySide6 (Qt6) |
| Backend | PowerShell (pozivan iz Python-a, JSON-first — vidi `docs/architecture_notes.md`) |
| Python | 3.11+ |
| Testovi | pytest, `tests/` folder |
| Build | PyInstaller (kasnije), Inno Setup (kasnije) |

## Struktura projekta

```text
app/
├── main.py
├── gui/            # main_window, sidebar, dashboard, pages/, widgets/
├── core/            # CommandResult, Issue, RiskLevel... (Zadatak 2+)
├── modules/         # network/, smb/, firewall/... (plugin-ready, ne plugin system)
├── knowledge/       # YAML opisi grešaka (Zadatak 5+)
└── reports/         # markdown/html/json report writer (Faza 9+)
docs/                # architecture_notes, future_modules_backlog, target_gui
agent_runbooks/      # procedure za rizične promjene
agent_reports/       # izvještaj po zadatku
project_rooms/       # samo za HIGH/CRITICAL GitNexus impact (vidi AGENTS.md)
```

Detaljnija pravila (šta je gdje, kad je runbook/report/project_room
obavezan, tabela zabrana) su u `AGENTS.md` — ovaj fajl ih ne duplira.

## Format zadatka za agenta (preporučeno za netrivijalne zadatke)

- **Zadatak** — šta treba implementirati/popraviti
- **Moja radna pretpostavka** — pristup koji planiram
- **Provjeri hipotezu** — prije izmjene potvrdi/odbaci pretpostavku
  dokazima (plan, kod, GitNexus impact)
- **Granice** — šta NE smijem dirati (van scope-a)
- **Šta je dobar ishod** — vidljiv/testabilan rezultat
- **Obavezno** — ako je HIGH/CRITICAL: GitNexus impact prijavljen
  korisniku PRIJE izmjene (format u `AGENTS.md`, "Handoff visokog
  rizika"), i `agent_report` na kraju

Za sitne, jednolinijske izmjene (typo, jedan layout detalj) ovaj format
je nepotreban overhead.

## Plan prije izmjene — HIGH/CRITICAL GitNexus impact

Vidi `AGENTS.md`, sekcija "Handoff visokog rizika (HIGH/CRITICAL GitNexus
impact)" — tamo je i format prijave rizika korisniku i template za
`project_rooms/YYYY-MM-DD_kratak-naziv-zadatka.md`.

## Obavezna procedura nakon završenog zadatka

### Korak 1 — Git

Pripremiti staged promjene grupisane po logičkim cjelinama i predloženu
commit poruku (`tip(oblast): opis`, `Co-Authored-By: Claude Sonnet 4.6
<noreply@anthropic.com>`) — **ali ne commit-ovati bez eksplicitnog
zahtjeva korisnika.** Ovo je svjesna razlika od ranijeg radnog obrasca
(auto-commit nakon svakog zadatka): ovdje važi pravilo da se git commit
radi samo kad korisnik to direktno traži.

### Korak 2 — Agent report

`agent_reports/YYYY-MM-DD_naziv-zadatka.md` sa sekcijama (kao `##`):

- **Datum**, **Scope** — fajlovi/moduli
- **GitNexus impact** — rezultat provjere prije izmjene (ako je rađena)
- **Šta je urađeno** / **Zašto je urađeno** / **Kako je urađeno**
- **Šta nije dirano** — eksplicitno, da se spriječi širenje scope-a
- **Verifikacija** — testovi, ručna provjera
- **Rizici / ograničenja**
- **Potreban follow-up**
- **Potrebna korisnička potvrda** — ako postoji nešto što korisnik treba
  ručno provjeriti (npr. izgled na stvarnom Windows uređaju)

Obavezan za zadatke iz liste u `AGENTS.md` ("Kad je agent report
obavezan"); za sitne izmjene nije potreban.

### Korak 3 — Link odluke (ako je relevantno)

Ako je zadatak doneo ili promijenio arhitektonsku odluku, dodaj/ažuriraj
sekciju u `docs/architecture_notes.md` sa `> Report: [agent_reports/...]`
linkom (vidi `AGENTS.md`, "Linkovanje odluka ka agent_reports").

### Korak 4 — GitNexus

Nakon netrivijalne izmjene koda provjeriti da index nije zastario; ako
jeste, pokrenuti `npx gitnexus analyze`.

### Korak 5 — Memorija (samo ako je nešto ne-očigledno za buduće sesije)

Ako je zadatak otkrio radnu naviku/preferencu korisnika koja nije već u
auto-memory, sačuvati je (vidi "Memorija" sekciju iznad za granicu šta
ide u repo vs. šta ide u auto-memory).

## DOC Guard

Nije postavljen za ovaj projekat (nema `scripts/doc_link_checker.sh` ni
hook infrastrukturu) — preneseno sa ranijeg projekta, ali nije dio MVP-a.
Dodati kasnije ako zatreba, ne fabrikovati skriptu bez potrebe.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **FieldFix-IT** (2344 symbols, 4234 relationships, 57 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

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
