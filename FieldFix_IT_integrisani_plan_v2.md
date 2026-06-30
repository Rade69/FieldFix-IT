# FieldFix IT — integrisani plan razvoja v2

## 0. Kratki zaključak

**FieldFix IT** je Windows desktop alat za terensku IT dijagnostiku i kontrolisano rješavanje problema u malim firmama.

Glavna formula projekta:

```text
Scan → Evidence → Decision → Recommendation → Controlled Fix → Report
```

Najvažnije izmjene u odnosu na prethodni plan:

- MVP nije puni plugin system, nego **modularni monolit spreman za kasniji plugin sistem**.
- Agent workflow se u MVP-u olakšava: ne uvoditi punu ceremoniju odmah.
- PowerShell komande treba vraćati **JSON gdje god je moguće**, ne parsirati tekst ako postoji strukturisan cmdlet.
- Aplikacija ne treba cijela da se pokreće kao Administrator. Elevacija se traži samo za fix akcije.
- Dashboard ne smije imati direktan `Apply`; treba imati `Review Fix`.
- Svaka fix akcija mora imati vidljiv `Risk Level`.
- Topology, Decision Assistant i Timeline su target dizajn, ne prvi build.
- Future moduli idu u backlog, da ne prave scope creep.

---

## 1. Naziv aplikacije

Primarni naziv:

```text
FieldFix IT
```

Zašto:

- zvuči kao alat koji nosiš na teren,
- nije ograničen samo na mrežu,
- može se širiti na štampače, Windows servise, backup, diskove, baze, VPN i druge IT oblasti,
- dovoljno je profesionalan za internu upotrebu, a kasnije i za širu distribuciju.

Alternativni nazivi:

```text
WinScope
NetMedic
IT Scout
ServicePilot
Mrežni Doktor
```

Moj izbor ostaje:

```text
FieldFix IT
```

---

## 2. Glavna ideja

FieldFix IT treba pomoći kada serviser ili korisnik ne zna:

- zašto se računari ne vide,
- zašto `\\IP_ADRESA` ne radi,
- zašto mrežni share traži lozinku ili odbija pristup,
- zašto Windows javlja greške 53, 64, 6118, 1272, 5, 86, 1326,
- zašto štampač nije dostupan,
- da li je problem IP, DNS, firewall, SMB, servis, lozinka, Windows policy ili drajver,
- šta je bezbjedno promijeniti,
- šta je rizično dirati.

Aplikacija ne smije biti “magic repair tool”. Ona mora biti:

```text
dijagnostički alat + sistem preporuka + kontrolisani fix centar
```

---

## 3. Osnovni principi

### 3.1 Scan Mode je default

Aplikacija se uvijek pokreće u režimu:

```text
Scan Mode / Read Only
```

U ovom režimu aplikacija:

- ne mijenja Windows podešavanja,
- ne startuje/stopira servise,
- ne mijenja firewall,
- ne uključuje SMB1,
- ne mijenja Guest access,
- ne mijenja Group Policy,
- ne pravi nove korisnike,
- samo čita stanje i generiše nalaze.

### 3.2 Fix Mode se uključuje ručno

Fix Mode se ne smije aktivirati automatski.

Korisnik mora jasno vidjeti:

```text
You are entering Fix Mode.
Some actions may change Windows settings.
```

Svaki fix mora imati:

- naziv,
- kratko objašnjenje,
- risk level,
- šta tačno mijenja,
- šta ne mijenja,
- da li traži admin prava,
- Apply,
- Skip,
- rezultat izvršenja,
- rollback napomenu ako postoji.

### 3.3 Dashboard ne smije direktno izvršavati fix

Na Dashboardu ne koristiti dugme:

```text
Apply
```

Koristiti:

```text
Review Fix
```

Tok:

```text
Dashboard issue → Review Fix → Fix Center → explanation → Apply / Skip
```

Čak i LOW risk akcija treba proći kroz kratak confirm dijalog.

### 3.4 Risk level je obavezan

Svaka preporuka i svaka fix akcija mora imati vidljiv risk badge.

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Primjeri:

```text
Set network profile to Private
Risk: LOW
```

```text
Enable File and Printer Sharing firewall rules
Risk: LOW / MEDIUM
```

```text
Reset Winsock
Risk: MEDIUM
```

```text
Enable SMB1
Risk: HIGH
```

```text
Allow insecure Guest access
Risk: HIGH
```

```text
Modify domain policy
Risk: CRITICAL
```

### 3.5 Danger Zone

Akcije u Danger Zone ne smiju biti dostupne kao običan klik.

Danger Zone uključuje:

- Enable SMB1,
- Allow insecure Guest access,
- Disable firewall,
- Modify Local Security Policy,
- Modify Group Policy,
- Reset network stack,
- Change domain-related settings.

Za ove akcije tražiti dodatnu potvrdu:

```text
I understand this is risky
```

---

## 4. UAC / Administrator prava

Ovo mora biti definisano prije implementacije `PowerShellRunner`.

### 4.1 Aplikacija se ne pokreće cijela kao Administrator

Default pokretanje:

```text
Normal user
Scan Mode
```

Razlog:

- manji rizik,
- jasnija kontrola,
- bolji UX,
- manje šanse da korisnik slučajno promijeni sistem.

### 4.2 Elevacija se traži po akciji

Ako fix zahtijeva admin prava:

```text
This action requires Administrator privileges.
[Run as Administrator]
```

Za MVP može jednostavnije:

- aplikacija detektuje da nije admin,
- fix dugme kaže “Restart as Admin required”,
- korisnik ručno pokrene aplikaciju kao Administrator za fix.

Kasnije se može implementirati per-action elevation pomoću odvojenog helper procesa.

---

## 5. PowerShell pravilo: JSON prvo, tekst fallback

Gdje god je moguće koristiti strukturisane PowerShell cmdlete i `ConvertTo-Json`.

Ne oslanjati se na tekstualno parsiranje legacy komandi ako postoji bolja alternativa.

Primjer:

```powershell
Get-NetAdapter |
Select-Object Name, InterfaceDescription, Status, LinkSpeed |
ConvertTo-Json
```

Dobri kandidati za JSON:

```powershell
Get-NetAdapter
Get-NetIPAddress
Get-NetRoute
Get-DnsClientServerAddress
Get-NetConnectionProfile
Get-NetFirewallProfile
Get-NetFirewallRule
Get-Service
Get-SmbServerConfiguration
Get-SmbClientConfiguration
Get-SmbShare
Get-Printer
Get-PrinterPort
Get-PrinterDriver
```

Legacy komande koristiti kao fallback ili za specifične Windows greške:

```text
net view
net share
net use
arp -a
ipconfig
ping
```

Ako se parsira tekst, parser mora biti izolovan u posebnom fajlu i testiran.

---

## 6. Arhitektura: modularni monolit, ne puni plugin system u MVP-u

Prethodni plan je išao prerano u plugin arhitekturu.

Ispravka:

```text
MVP = modularni monolit
Kasnije = plugin arhitektura
```

### 6.1 Zašto ne pravi plugin system odmah

Pravi plugin system od prvog dana uvodi previše boilerplate-a:

```text
plugin.json
scanner.py
fixer.py
models.py
ui_panel.py
report_section.py
README.md
```

Za MVP to usporava razvoj i stvara apstrakciju prije realne potrebe.

### 6.2 Šta raditi umjesto toga

Napraviti module koji su plugin-ready, ali bez Plugin Managera.

Primjer MVP strukture:

```text
app/
├── core/
├── modules/
│   ├── network/
│   ├── smb/
│   ├── firewall/
│   ├── services/
│   └── printers/
├── gui/
├── reports/
└── knowledge/
```

Svaki modul ima sličnu strukturu, ali ne mora imati formalni plugin interfejs odmah.

Primjer:

```text
app/modules/network/
├── scanner.py
├── models.py
├── recommendations.py
└── ui.py
```

Kasnije, kada se ponavljanje stabilizuje, uvodi se:

```text
PluginBase
PluginManager
plugin.json
```

Zaključak:

```text
Plugin-ready DA.
Plugin system NE u MVP-u.
```

---

## 7. Core komponente

MVP core treba imati:

```text
CommandResult
DiagnosticResult
Issue
Recommendation
RiskLevel
ScanStatus
PowerShellRunner
JsonPowerShellRunner
DecisionEngine
KnowledgeBaseLoader
ReportWriter
```

### 7.1 CommandResult

Sadrži:

- command,
- stdout,
- stderr,
- exit_code,
- duration_ms,
- timed_out,
- requires_admin,
- parsed_json,
- raw_output.

### 7.2 Issue

Sadrži:

- id,
- title,
- severity,
- evidence,
- likely_cause,
- confidence,
- recommended_actions,
- related_module.

### 7.3 Recommendation

Sadrži:

- title,
- risk_level,
- what_it_changes,
- what_it_does_not_change,
- requires_admin,
- action_id,
- can_apply,
- reason_if_not_applicable.

---

## 8. Knowledge Base

Ne hardkodovati sve Windows greške u kod.

Napraviti folder:

```text
app/knowledge/
├── smb/
│   ├── error_53.yaml
│   ├── error_64.yaml
│   ├── error_6118.yaml
│   ├── error_1272.yaml
│   ├── error_5.yaml
│   ├── error_86.yaml
│   └── error_1326.yaml
├── printers/
├── firewall/
├── services/
└── network/
```

Primjer YAML fajla:

```yaml
id: smb_error_6118
title: Workgroup server list unavailable
meaning: Windows cannot list computers in the workgroup.
likely_causes:
  - Network Discovery disabled
  - Function Discovery services stopped
  - Computer Browser / legacy browsing unavailable
important_note: Direct access by IP may still work.
recommended_checks:
  - Test \\\\IP directly
  - Check FDResPub service
  - Check Network Discovery firewall rules
safe_fixes:
  - enable_network_discovery
  - start_fdrespub
dangerous_fixes: []
confidence_rules:
  - if net_view_error == 6118 and direct_ip_access_works: browsing_issue_not_smb_failure
```

Prednost:

- greške se šire bez promjene koda,
- lakše testiranje,
- znanje ostaje dokumentovano,
- kasnije AI assistant može koristiti istu bazu znanja.

---

## 9. Decision Engine

Aplikacija ne smije samo prikazati podatke.

Mora zaključiti:

```text
Problem → Evidence → Reasoning → Conclusion → Confidence → Recommended Fix
```

Primjer:

```text
Problem:
Cannot access \\192.168.100.55

Evidence:
✔ Ping OK
✔ Port 445 reachable
✔ SMB service reachable
❌ Credentials rejected

Conclusion:
Authentication problem.

Confidence:
94%

Recommended Fix:
Use correct username format:
COMPUTER\\USER
```

Za MVP confidence može biti:

```text
High / Medium / Low
```

---

## 10. Profiles

Dodati profil dijagnostike.

Primjeri:

```text
Office PC
Laptop
Server
Printer
NAS
Unknown device
```

Profil utiče na to koje provjere su prioritetne.

### 10.1 Printer profile

Provjere:

- ping,
- port 9100,
- IPP,
- WSD,
- printer port,
- driver,
- spooler,
- SNMP status,
- shared printer status.

### 10.2 Server profile

Provjere:

- SMB,
- DNS,
- RDP,
- shares,
- permissions,
- firewall,
- services.

### 10.3 Office PC profile

Provjere:

- network profile,
- discovery,
- SMB client/server,
- firewall,
- shares,
- credentials.

Za MVP profil može biti samo izbor u UI:

```text
Target type: PC / Printer / Unknown
```

---

## 11. GUI koncept

Prvi mockup ostaje target dizajn, ali ne build target za Fazu 1.

### 11.1 Sidebar

```text
Dashboard
Network
Sharing / SMB
Firewall
Services
Printers
Topology
Reports
Settings
About
```

Topology može biti posebna sekcija jer je flagship feature.

### 11.2 Dashboard

Dashboard prikazuje:

- gornji status header,
- agregirane status kartice,
- system/network info,
- recent scan summary,
- issues,
- recommendations,
- topologiju u skraćenom obliku,
- timeline.

### 11.3 Desni panel

Desni panel:

```text
Issues
Recommendations
Review Fix
```

Ne direktno Apply.

Svaka preporuka ima:

- risk badge,
- short reason,
- Review button.

### 11.4 Fix Center

Fix Center prikazuje:

```text
Safe Fixes
Careful Fixes
Danger Zone
```

Svaka akcija:

```text
Title
Risk badge
What it changes
What it does not change
Requires admin: yes/no
Evidence
Apply / Skip
```

### 11.5 Decision Assistant

Poseban panel:

```text
Problem
Evidence
Reasoning
Conclusion
Confidence
Recommended next step
```

### 11.6 Timeline

Na dnu ili u zasebnom panelu:

```text
11:04 Scan started
11:04 Gateway found
11:05 SMB port OK
11:05 Authentication required
11:06 Scan completed
```

---

## 12. Target GUI nije MVP

Važno pravilo:

```text
Mockup je v3 cilj, ne v1 zadatak.
```

Faza 1 ne smije pokušati napraviti:

- topology,
- decision assistant,
- timeline,
- quick actions,
- full dashboard.

Faza 1 radi samo:

- prozor,
- sidebar,
- prazne stranice,
- osnovni layout,
- placeholder kartice.

---

## 13. MVP moduli

MVP uključuje:

```text
Network
SMB / Sharing
Firewall
Services
Printers
Reports
```

Ali implementacija ide redom.

Prvi realni moduli:

```text
Network
SMB
Firewall
```

Tek poslije:

```text
Services
Printers
Reports
```

---

## 14. Future Modules Backlog

Ne držati predugačak spisak budućih modula u glavnom razvojnom toku.

Držati kao backlog:

```text
docs/future_modules_backlog.md
```

Mogući budući moduli:

- Windows Update,
- Event Viewer,
- Disk / SMART,
- Backup,
- RDP,
- VPN,
- PostgreSQL,
- SQL Server,
- Docker,
- Hyper-V,
- IIS,
- Active Directory,
- Certificates,
- USB devices,
- UPS,
- Wi-Fi analysis,
- speed test,
- Linux SSH diagnostics.

Ovi moduli nisu MVP i ne smiju ulaziti u prve Codex zadatke.

---

## 15. Agent workflow — olakšana MVP verzija

Prethodni plan je bio dobar za ozbiljan dugoročni razvoj, ali pretežak za MVP.

MVP uvodi samo:

```text
AGENTS.md
agent_reports/
agent_runbooks/high_critical_code_change.md
```

Ne uvoditi odmah:

```text
agent_skills/
agent_loops/
project_rooms/
```

osim ako se pokaže potreba ili se radi rizična promjena.

### 15.1 Kada je agent report obavezan u MVP-u

Obavezan za:

- PowerShellRunner,
- fix akcije,
- firewall promjene,
- SMB promjene,
- admin/elevation logiku,
- decision engine,
- report generator,
- installer.

Nije obavezan za:

- UI tekst,
- mali layout,
- README typo,
- lokalnu sitnu izmjenu.

### 15.2 Kada je project room obavezan

Tek kada zadatak dira HIGH/CRITICAL oblast:

- fix engine,
- Windows settings,
- admin execution,
- policy promjene,
- installer,
- runner,
- decision engine.

### 15.3 Agent workflow kasnije

Kada MVP postane stabilan, dodati:

```text
agent_skills/
agent_loops/
project_rooms/
```

prema ranijem agent workflow planu.

---

## 16. Agent loops

Ne uvoditi loopove u prvoj fazi.

Kasnije dozvoliti:

```text
test_fix_loop
lint_fix_loop
documentation_sync_loop
```

Važno:

```text
Fix loop ne smije sam mijenjati Windows postavke.
Može samo predložiti fix i čekati potvrdu.
```

Loop mora imati:

- maksimalan broj pokušaja,
- verifier,
- stop uslove,
- zabranu širenja scope-a.

---

## 17. Predložena struktura projekta za MVP

```text
fieldfix_it/
├── app/
│   ├── main.py
│   ├── gui/
│   │   ├── main_window.py
│   │   ├── sidebar.py
│   │   ├── dashboard.py
│   │   ├── pages/
│   │   │   ├── network_page.py
│   │   │   ├── smb_page.py
│   │   │   ├── firewall_page.py
│   │   │   ├── services_page.py
│   │   │   ├── printers_page.py
│   │   │   ├── topology_page.py
│   │   │   └── reports_page.py
│   │   └── widgets/
│   │       ├── status_card.py
│   │       ├── risk_badge.py
│   │       ├── issue_card.py
│   │       └── timeline_widget.py
│   ├── core/
│   │   ├── powershell_runner.py
│   │   ├── command_result.py
│   │   ├── diagnostic_result.py
│   │   ├── issue.py
│   │   ├── recommendation.py
│   │   ├── risk_level.py
│   │   ├── decision_engine.py
│   │   └── errors.py
│   ├── modules/
│   │   ├── network/
│   │   │   ├── scanner.py
│   │   │   ├── models.py
│   │   │   └── recommendations.py
│   │   ├── smb/
│   │   ├── firewall/
│   │   ├── services/
│   │   └── printers/
│   ├── knowledge/
│   │   ├── smb/
│   │   ├── printers/
│   │   ├── firewall/
│   │   └── services/
│   ├── reports/
│   │   ├── markdown_report.py
│   │   ├── html_report.py
│   │   └── json_report.py
│   └── resources/
├── docs/
│   ├── target_gui.md
│   ├── future_modules_backlog.md
│   └── architecture_notes.md
├── scripts/
├── tests/
├── agent_runbooks/
│   └── high_critical_code_change.md
├── agent_reports/
├── AGENTS.md
├── README.md
├── pyproject.toml
└── requirements.txt
```

---

## 18. Faze razvoja

### Faza 1 — Skeleton / UI shell

Cilj:

- PySide6 aplikacija,
- glavni prozor,
- sidebar,
- prazne stranice,
- placeholder dashboard,
- status kartice kao dummy,
- bez realne dijagnostike,
- bez fix funkcija.

Ne raditi:

- topology engine,
- decision assistant,
- fix center,
- plugin manager,
- installer.

### Faza 2 — Core modeli

Implementirati:

- CommandResult,
- DiagnosticResult,
- Issue,
- Recommendation,
- RiskLevel,
- ScanStatus.

### Faza 3 — PowerShellRunner

Implementirati:

- run command,
- timeout,
- stdout,
- stderr,
- exit_code,
- duration,
- JSON parsing helper,
- admin detection,
- bez fix komandi.

Ova faza je rizična i treba agent report.

### Faza 4 — Network module

Implementirati čitanje:

- hostname,
- active adapter,
- IPv4,
- gateway,
- DNS,
- network profile,
- ping gateway,
- ARP table.

Koristiti JSON PowerShell gdje je moguće.

### Faza 5 — SMB module

Implementirati:

- SMB server config,
- SMB client config,
- Get-SmbShare,
- test port 445,
- opcioni `net view` fallback,
- poznate greške 53, 64, 6118, 1272, 5, 86, 1326,
- preporuke iz Knowledge Base.

### Faza 6 — Firewall module

Implementirati:

- firewall profiles,
- File and Printer Sharing rules,
- Network Discovery rules,
- status i preporuke.

### Faza 7 — Services module

Implementirati:

- LanmanServer,
- LanmanWorkstation,
- FDResPub,
- fdPHost,
- Dnscache,
- SSDPSRV,
- upnphost,
- Spooler.

### Faza 8 — Printer module

Implementirati:

- Get-Printer,
- Get-PrinterPort,
- Get-PrinterDriver,
- shared printers,
- port IP,
- spooler status.

### Faza 9 — Report Generator

Implementirati export:

- JSON,
- Markdown,
- HTML.

Report mora jasno navesti:

- šta je provjereno,
- šta nije provjereno,
- evidence,
- recommendations,
- risk levels.

### Faza 10 — Decision Engine v1

Implementirati osnovna pravila:

- ping fail + gateway ok = target/device problem,
- ping ok + port 445 fail = firewall/SMB port problem,
- ping ok + SMB ok + credentials fail = auth problem,
- net view 6118 + direct IP works = browsing problem, ne SMB connectivity problem,
- 1272 = guest access blocked.

### Faza 11 — Dashboard v2

Dodati:

- stvarne status kartice,
- issue listu,
- recommendations listu,
- risk badges,
- Review Fix dugmad.

### Faza 12 — Topology v1

Dodati:

- local computer,
- gateway,
- target IP,
- ARP discovered devices,
- printer nodes ako postoje.

### Faza 13 — Fix Center v1

Dozvoliti samo LOW/MEDIUM fix akcije:

- set network profile private,
- enable Network Discovery firewall rules,
- enable File and Printer Sharing firewall rules,
- start/restart Print Spooler,
- start FDResPub.

Svaka akcija traži potvrdu.

### Faza 14 — Installer / Portable build

- PyInstaller portable EXE,
- kasnije Inno Setup.

---

## 19. Minimalni Codex zadaci

### Zadatak 1 — Skeleton

```text
Napravi početni skeleton FieldFix IT aplikacije.

Stack:
- Python
- PySide6
- Windows target

Važno:
Ovo je samo UI shell, ne finalni GUI.

Dodaj:
- osnovni main window
- lijevi sidebar
- stranice: Dashboard, Network, Sharing/SMB, Firewall, Services, Printers, Topology, Reports, Settings, About
- placeholder dashboard sa dummy status karticama
- widget za RiskBadge, ali bez prave logike
- README.md
- AGENTS.md
- agent_reports/
- agent_runbooks/high_critical_code_change.md

Ne dodavati:
- plugin manager
- prave fix funkcije
- PowerShell komande
- installer
- topology engine
- decision engine

Na kraju napravi agent report:
agent_reports/YYYY-MM-DD_initial-skeleton.md
```

### Zadatak 2 — Core modeli

```text
Implementiraj core modele:
- CommandResult
- DiagnosticResult
- Issue
- Recommendation
- RiskLevel
- ScanStatus

Dodaj osnovne unit testove.

Ne implementirati PowerShellRunner još.
Ne dirati GUI osim ako je minimalno potrebno.

Napravi agent report.
```

### Zadatak 3 — PowerShellRunner

```text
Implementiraj PowerShellRunner.

Zahtjevi:
- run(command, timeout)
- run_json(command, timeout)
- stdout
- stderr
- exit_code
- duration_ms
- timeout handling
- admin detection
- structured error handling

Koristiti ConvertTo-Json za strukturisane cmdlete.

Ne implementirati fix komande.
Ne mijenjati Windows podešavanja.

Ovo je rizična centralna komponenta.
Koristi high_critical_code_change runbook.
Napravi agent report.
```

### Zadatak 4 — Network module

```text
Implementiraj Network module.

Prikuplja:
- hostname
- active adapters
- IPv4
- gateway
- DNS
- network category
- ping gateway
- ARP table

Koristi JSON PowerShell gdje god je moguće.

Prikaži rezultate na Network stranici.

Ne implementirati fix.
Napravi agent report.
```

### Zadatak 5 — SMB module

```text
Implementiraj SMB module.

Prikuplja:
- SMB server config
- SMB client config
- Get-SmbShare
- test port 445 za target IP
- net view kao fallback / legacy check

Prepoznaje greške:
- 53
- 64
- 6118
- 1272
- 5
- 86
- 1326

Dodaj knowledge YAML fajlove za ove greške.

Ne implementirati automatski fix.
Napravi agent report.
```

---

## 20. Šta ne raditi u MVP-u

Ne raditi odmah:

- puni plugin system,
- Plugin Manager,
- AI assistant,
- automatski repair svega,
- SMB1 fix,
- Guest access fix,
- domain/Active Directory alat,
- remote execution,
- agent orchestration,
- cloud sync,
- licenciranje,
- kompleksan installer,
- marketplace za module.

---

## 21. Kasniji AI Assistant

AI Assistant nije MVP.

Kasnije može koristiti:

- scan rezultate,
- decision engine,
- knowledge base,
- report,
- korisnikov opis problema.

AI može predložiti, ali ne smije sam izvršavati fix.

---

## 22. Završni princip

FieldFix IT treba da ostane praktičan.

Ne praviti birokratiju.

Ne praviti enterprise platformu prije nego što postoji koristan alat.

Najkraće:

```text
MVP = modularni monolit + scan + evidence + report
V2 = decision engine + topology + safe fix center
V3 = plugin system + AI assistant + prošireni moduli
```

Prva verzija mora riješiti realne probleme:

```text
mreža + SMB + firewall + servisi + štampači
```

Sve ostalo ide kasnije.
