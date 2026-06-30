# Agent report — Agent workflow upgrade (AGENTS.md + novi CLAUDE.md)

Datum: 2026-06-29

## Scope

`AGENTS.md`, novi `CLAUDE.md`, `docs/architecture_notes.md` (dokumentacija
odluke). Nije dirana app/ logika ni testovi.

## GitNexus impact

Nije relevantno — promjena su procesni/dokumentacioni fajlovi, ne kod.
Pokrenut je `npx gitnexus analyze` nakon izmjena da index ostane svjež
(275 simbola, 311 relacija, vs. 247/284 prije).

## Šta je urađeno

- Korisnik je dao na uvid `AGENTS.md` i `CLAUDE.md` sa ranijeg projekta
  (deklarant_pro) i tražio da se najrelevantnije prenese u FieldFix IT,
  uz nova uputstva iz ovog projekta.
- `AGENTS.md` dopunjen sa: cross-referencom ka `CLAUDE.md` (da se ne
  duplira jezik/git/memory/procedura), napomenom da je `project_rooms/`
  sada uveden (lagana forma), "Handoff visokog rizika (HIGH/CRITICAL
  GitNexus impact)" sekcijom s template-om za `project_rooms/`, "Format
  outputa" sekcijom, "Provjera prije predaje" checklistom, i tabelom
  "Šta je zabranjeno" (ranije je to bila prosta lista bez razloga).
- Napravljen novi `CLAUDE.md` (FieldFix IT prije nije imao ovaj fajl) sa:
  jezik (srpski latinica, obavezno), memorija (objašnjeno da ne postoji
  MCP memory server kao na ranijem projektu — umjesto toga, dva sloja:
  repo dokumentacija kao izvor istine + Claude Code auto-memory za radne
  navike), tech stack, struktura projekta, format zadatka za agenta,
  pointer na handoff format, i "Obavezna procedura nakon završenog
  zadatka" (5 koraka: git priprema, agent report, link odluke, GitNexus
  refresh, memorija).
- `docs/architecture_notes.md` dopunjen novom sekcijom koja dokumentuje
  ovu odluku i razlike od ranijeg obrasca.
- `npx gitnexus analyze` pokrenut dva puta (jednom prije ovog zadatka pri
  inicijalizaciji projekta, jednom nakon ovih izmjena) — GitNexus je i
  sam ubacio/ažurirao `<!-- gitnexus:start -->` blok u oba fajla, to nije
  ručno editovano.

## Zašto je urađeno

Korisnik ima provjeren radni obrazac sa drugog projekta (deklarant_pro) i
želi konzistentnost između projekata, ali FieldFix IT je u ranijoj fazi
(MVP skeleton, lagana agent ceremonija po odluci iz v2 plana) pa nije sve
prenešeno 1:1 — samo ono što je odmah korisno i ne uvodi nepotrebnu
infrastrukturu (npr. DOC Guard hook nije postavljen, jer ne postoji
prateći skript/hook za ovaj projekat).

## Kako je urađeno

Edit na postojećem `AGENTS.md` (dodate sekcije, ne prepisan cijeli fajl).
Write na `CLAUDE.md` — fajl je već postojao (GitNexus ga je generisao sa
samim gitnexus blokom), pa je sadržaj ubačen Edit-om iznad
`<!-- gitnexus:start -->` markera, ne Write-om koji bi obrisao blok.

## Šta nije dirano

- DOC Guard (hook + `scripts/doc_link_checker.sh`) — nije postavljen,
  nema prateće infrastrukture, nije dio MVP-a.
- Auto-commit nakon zadatka — eksplicitno NIJE prenesen (sukob sa
  pravilom da Claude Code ne commit-uje bez eksplicitnog zahtjeva).
- MCP memory server / `get_project_context` tooling — ne postoji za ovaj
  projekat, CLAUDE.md to izričito objašnjava umjesto da fabrikuje
  nepostojeće alate.
- app/ kod, testovi, knowledge fajlovi — netaknuto.

## Verifikacija

- `npx gitnexus analyze` prošao bez greške, brojke simbola/relacija
  porasle (novi CLAUDE.md sadržaj se indeksira kao dokument).
- Ručna provjera da `<!-- gitnexus:start/end -->` blok nije oštećen u oba
  fajla nakon Edit operacija.
- Markdownlint upozorenje (MD025, dva H1 naslova u `CLAUDE.md`) primljeno
  i svjesno ostavljeno — posljedica GitNexus auto-bloka, isti pattern
  postoji u korisnikovim referentnim fajlovima sa drugog projekta.

## Rizici / ograničenja

- `project_rooms/` direktorijum još nije fizički kreiran (nema još
  HIGH/CRITICAL GitNexus impact zadatka) — kreiraće se kad prvi takav
  zadatak nastupi.
- Ako se kasnije uvede prava MCP memorija, CLAUDE.md "Memorija" sekciju
  treba ažurirati da ne bude zastarjela.

## Potreban follow-up

Nema neposrednog — sledeći korak po planu je Zadatak 2 (core modeli),
koji bi trebalo da prvi put koristi novi "Format zadatka za agenta" i
"Format outputa" iz ovih fajlova.

## Potrebna korisnička potvrda

Nema ničeg za ručnu provjeru na stvarnom uređaju — ovo su samo
dokumentacioni/procesni fajlovi.
