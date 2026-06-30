# Runbook: HIGH / CRITICAL code change

Koristi ovaj runbook kad zadatak dira: PowerShellRunner, fix akcije,
firewall promjene, SMB promjene, admin/elevation logiku, decision engine,
report generator ili installer.

## Prije promjene

1. Pročitaj `docs/architecture_notes.md` — provjeri da li je odluka već
   donesena za ovu oblast (UAC, JSON-first PowerShell, Review Fix tok,
   knowledge base semantika).
2. Potvrdi scope zadatka — ne širiti van onoga što je traženo.

## Tokom promjene

1. Scan Mode ostaje default; nijedna nova funkcija ne smije promijeniti
   Windows podešavanje bez eksplicitnog Apply poziva od korisnika.
2. Svaka nova fix akcija mora imati: naziv, risk level, "what it changes",
   "what it does not change", da li traži admin prava.
3. PowerShell pozivi koriste `ConvertTo-Json` strukturisane cmdlete gdje
   postoje; text-parsing legacy komandi ide u izolovan, testiran parser.
4. Dodati/ažurirati unit testove za novu logiku.

## Nakon promjene

1. Napraviti `agent_reports/YYYY-MM-DD_kratak-naziv.md` sa: šta je
   urađeno, šta NIJE urađeno (granice), koji rizici postoje, šta treba
   provjeriti prije sljedećeg zadatka.
2. Ako je zadatak doveo do nove ili promijenjene arhitektonske odluke,
   dodati/ažurirati odgovarajuću sekciju u `docs/architecture_notes.md`
   sa `> Report: [agent_reports/...]` linkom ka ovom izvještaju (vidi
   AGENTS.md, "Linkovanje odluka ka agent_reports").
3. Ako je promjena dotakla Windows sistem tokom testiranja (npr. firewall
   pravilo), navesti tačno šta i kako se vraća u prethodno stanje.
