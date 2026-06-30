# FieldFix IT — dopunjeni plan razvoja

## 0. Naziv aplikacije

Primarni naziv:

```text
FieldFix IT
```

Razlog:

- zvuči kao alat za teren,
- nije ograničen samo na mrežu,
- može pokriti Windows, mrežu, štampače, servise, diskove, backup, VPN, baze i druge IT zadatke,
- dovoljno je profesionalan i za internu i za eventualnu širu upotrebu.

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

## 1. Glavna ideja

FieldFix IT je Windows desktop aplikacija za terensku IT dijagnostiku i kontrolisano popravljanje problema u malim firmama.

Cilj nije da aplikacija „klikne sve i popravi sve“.

Cilj je:

```text
Prvo dijagnostika.
Zatim dokaz.
Zatim preporuka.
Tek onda kontrolisani fix.
```

Aplikacija treba da pomogne kada korisnik ili serviser ne zna:

- zašto se računari ne vide,
- zašto mrežni share ne radi,
- zašto štampači nisu dostupni,
- da li je problem IP, firewall, SMB, servis, lozinka ili Windows policy,
- šta je bezbjedno promijeniti,
- šta je rizično dirati.

---

## 2. Osnovni principi

### 2.1 Scan Mode je default

Aplikacija se uvijek pokreće u režimu:

```text
Scan Mode / Read Only
```

U ovom modu aplikacija ništa ne mijenja.

Samo čita stanje i pravi izvještaj.

### 2.2 Fix Mode je kontrolisan

Fix Mode se uključuje ručno.

Svaki fix mora imati:

- naziv,
- objašnjenje,
- rizik,
- šta tačno mijenja,
- dugme Apply,
- dugme Skip,
- log rezultata.

Nijedan fix ne smije biti automatski.

### 2.3 Risk level je obavezan

Svaka preporuka i svaka popravka mora imati risk level:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

Primjeri:

```text
Set Network Profile to Private
Risk: LOW
```

```text
Enable File and Printer Sharing firewall rules
Risk: LOW / MEDIUM
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
Change domain/group policy setting
Risk: CRITICAL
```

---

## 3. Predloženi izgled aplikacije

Prvi GUI koncept je bolji kao osnova jer prikazuje mrežnu topologiju.

Glavni ekran treba imati:

```text
FieldFix IT
Windows IT Diagnostics & Repair Tool
```

### 3.1 Lijeva navigacija

```text
Dashboard
Network
Sharing / SMB
Firewall
Services
Printers
Reports
Settings
Tools
About
```

Kasnije navigaciju pretvoriti u workspace-style stablo:

```text
Dashboard

Network
  Adapters
  IP / DNS
  Gateway
  Routing
  Wi-Fi

Sharing / SMB
  Shares
  Sessions
  Permissions
  Credentials
  Known Errors

Printers
  Installed
  Network
  Drivers
  Ports
  Queue

Firewall
  Profiles
  Rules
  Inbound
  Outbound

Services
  Required Services
  Print Services
  Discovery Services

Reports
  Last Report
  Export
  History

Tools
  Ping
  Port Test
  Traceroute
  ARP
  DNS Lookup
```

---

## 4. Dashboard

Dashboard treba prikazati samo najvažnije informacije.

### 4.1 Gornji status

```text
Computer: NOVI
IP: 192.168.100.55
User: dm promet
Network: Private
Admin: Yes
Scan Mode: Read Only
```

### 4.2 Status kartice

```text
Network        OK
Sharing / SMB  WARNING
Firewall       WARNING
Services       OK
Printers       2
Issues         3
```

Klik na karticu otvara detalje.

### 4.3 System & Network Info

Prikaz:

```text
Computer Name
Domain / Workgroup
OS
IPv4 Address
Subnet Mask
Default Gateway
DNS Servers
Network Profile
MAC Address
Adapter
```

### 4.4 Recent Scan Summary

Primjer:

```text
Ping Gateway (192.168.100.1)       OK
Ping 192.168.100.155 (RADOVAN)     OK
SMB Port 445                       OK
File and Printer Sharing           DISABLED
Network Discovery                  DISABLED
LanmanServer                       Running
Print Spooler                      Running
```

---

## 5. Network Topology panel

Ovo je jedna od najvažnijih ideja aplikacije.

Panel treba vizuelno prikazati mrežu:

```text
NOVI ─── Router/Gateway ─── RADOVAN ─── Canon iR1133iF
```

Kasnije:

```text
                  Router
                    │
     ┌──────────────┼──────────────┐
     │              │              │
   PC-01          PC-02        Ubuntu Server
     │                             │
  Canon LBP                    PostgreSQL
  Canon iR                     Shared Folder
```

Statusi:

```text
Green  = online
Yellow = warning
Red    = offline/problem
Gray   = detected but not verified
```

Za svaki uređaj prikazati:

- hostname ako postoji,
- IP adresu,
- tip uređaja ako se može pogoditi,
- zadnji status,
- ping rezultat,
- otvoreni relevantni portovi ako su provjereni.

MVP verzija topologije ne mora biti savršena.

Dovoljno:

- ovaj računar,
- gateway,
- ručno uneseni target računar,
- pronađeni printeri,
- ARP uređaji.

---

## 6. Timeline / Activity Log

Na dnu aplikacije dodati timeline.

Primjer:

```text
11:04 Scan started
11:04 Gateway found: 192.168.100.1
11:04 Ping gateway OK
11:05 Target RADOVAN found
11:05 SMB port 445 OK
11:05 Authentication required
11:06 Firewall rule missing
11:06 Scan completed
```

Timeline je važan jer serviser vidi redoslijed događaja i može objasniti korisniku šta je provjereno.

---

## 7. Decision Tree diagnostika

Ovo je jedna od najjačih funkcija.

Aplikacija ne treba samo da izlista podatke, nego da zaključi gdje je problem.

Primjer za mrežni share:

```text
Problem: Cannot access \\192.168.100.155

Ping works?
YES

SMB port 445 open?
YES

Authentication prompt appears?
YES

Credentials accepted?
NO

Conclusion:
Problem is authentication / wrong username or password.
```

Drugi primjer:

```text
Problem: Cannot access \\192.168.100.155

Ping works?
NO

Same subnet?
NO

Conclusion:
Wrong IP range or wrong network adapter.
```

Treći primjer:

```text
Problem: Network computers not visible

Direct access by IP works?
YES

net view returns 6118?
YES

Conclusion:
Network browsing problem, not real SMB connectivity problem.
Use direct IP or enable discovery services.
```

Aplikacija treba imati bazu poznatih grešaka:

```text
53    Network path not found
64    The specified network name is no longer available
6118  Workgroup server list unavailable
1272  Guest access blocked by policy
5     Access denied
86    Password incorrect
1326  Logon failure
```

Za svaku grešku:

- značenje,
- najčešći uzrok,
- šta prvo provjeriti,
- koji fix je bezbjedan,
- šta ne dirati naslijepo.

---

## 8. Quick Actions / Fix Center

Quick Actions ne smiju biti divlje komande.

Svaka akcija mora izgledati ovako:

```text
Enable Network Discovery

Risk: LOW

What it changes:
- enables Network Discovery firewall rules
- starts discovery related services if needed

Apply / Skip
```

Fix Center treba grupisati akcije:

```text
Safe Fixes
  Set network profile to Private
  Enable Network Discovery firewall rules
  Enable File and Printer Sharing firewall rules
  Start Print Spooler
  Start FDResPub

Careful Fixes
  Change service startup type
  Reset Winsock
  Reset IP stack
  Clear saved SMB credentials

Danger Zone
  Enable SMB1
  Allow insecure Guest access
  Modify Local Security Policy
  Disable firewall temporarily
```

Danger Zone zahtijeva dodatnu potvrdu.

---

## 9. Moduli aplikacije

MVP moduli:

```text
Network
SMB / Sharing
Firewall
Services
Printers
Reports
```

Kasniji moduli:

```text
Windows Update
Event Viewer
Disk / SMART
Backup
RDP
VPN
PostgreSQL
SQL Server
Docker
Hyper-V
IIS
Active Directory
Certificates
USB devices
UPS
Wi-Fi analysis
Speed test
```

---

## 10. Plugin arhitektura

Aplikaciju od početka treba praviti kao platformu sa plugin arhitekturom.

Ne praviti jedan veliki monolit.

Struktura:

```text
FieldFix IT
│
├── Core
├── Plugin Manager
├── Network Plugin
├── SMB Plugin
├── Firewall Plugin
├── Services Plugin
├── Printer Plugin
├── Report Plugin
├── PostgreSQL Plugin
├── Docker Plugin
├── Hyper-V Plugin
├── Linux SSH Plugin
└── Custom Plugins
```

Svaki plugin treba imati:

```text
plugin.json
scanner.py
fixer.py
models.py
ui_panel.py
report_section.py
README.md
```

Primjer:

```text
plugins/
├── network/
│   ├── plugin.json
│   ├── scanner.py
│   ├── fixer.py
│   ├── models.py
│   ├── ui_panel.py
│   └── report_section.py
├── smb/
├── firewall/
├── services/
└── printers/
```

Prednost:

- lakše održavanje,
- lakše dodavanje novih oblasti,
- Codex može raditi na jednom pluginu bez diranja ostatka sistema,
- manji rizik od lomljenja aplikacije.

---

## 11. Tehnologija

Preporučeni stack:

```text
Python
PySide6
PowerShell backend
JSON modeli
Markdown / HTML report
PyInstaller
Inno Setup
```

Za početak ne koristiti bazu.

Za history reporta može lokalni folder:

```text
C:\FieldFixIT\reports
C:\FieldFixIT\logs
```

Kasnije SQLite ako bude potrebno.

---

## 12. Predložena struktura projekta

```text
fieldfix_it/
├── app/
│   ├── main.py
│   ├── gui/
│   │   ├── main_window.py
│   │   ├── sidebar.py
│   │   ├── dashboard.py
│   │   ├── topology_view.py
│   │   ├── timeline_panel.py
│   │   ├── issue_panel.py
│   │   └── fix_center.py
│   ├── core/
│   │   ├── powershell_runner.py
│   │   ├── command_result.py
│   │   ├── diagnostic_result.py
│   │   ├── issue.py
│   │   ├── risk_level.py
│   │   ├── plugin_base.py
│   │   ├── plugin_manager.py
│   │   ├── decision_tree.py
│   │   └── errors.py
│   ├── plugins/
│   │   ├── network/
│   │   ├── smb/
│   │   ├── firewall/
│   │   ├── services/
│   │   └── printers/
│   ├── reports/
│   │   ├── report_writer.py
│   │   ├── markdown_report.py
│   │   ├── html_report.py
│   │   └── json_report.py
│   └── resources/
├── scripts/
│   ├── Network_Diagnostics.ps1
│   └── Network_Basic_Fix.ps1
├── tests/
├── docs/
├── agent_skills/
├── agent_runbooks/
├── agent_loops/
├── project_rooms/
├── agent_reports/
├── AGENTS.md
├── README.md
├── pyproject.toml
└── requirements.txt
```

---

## 13. Agent workflow pravila u projektu

Projekat mora poštovati tvoj sistem:

```text
agent_skills/
agent_runbooks/
agent_loops/
project_rooms/
agent_reports/
```

Glavni fajl:

```text
AGENTS.md
```

AGENTS.md je mapa, ne ogromna knjiga.

U njemu stoji:

- gdje su skills,
- gdje su runbooks,
- kada je project room obavezan,
- kada je agent report obavezan,
- kada loop smije raditi,
- šta je zabranjeno.

### Obavezno pravilo

Za svaki zadatak koji dira:

- PowerShell runner,
- fix funkcije,
- firewall promjene,
- SMB promjene,
- admin privilegije,
- plugin manager,
- decision tree engine,
- installer,

koristi se:

```text
agent_runbooks/high_critical_code_change.md
```

i pravi se:

```text
project_room/
agent_report/
```

---

## 14. Agent loops u ovom projektu

Dozvoljeni loopovi:

```text
test_fix_loop
lint_fix_loop
documentation_sync_loop
```

Kasnije:

```text
safe_small_bugfix_loop
gui_smoke_check_loop
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

## 15. Faze razvoja

### Faza 1 — Skeleton

- PySide6 aplikacija
- glavni prozor
- sidebar
- prazni paneli
- dashboard layout
- AGENTS.md
- agent workflow folderi

Ne implementirati fix.

### Faza 2 — Core modeli

- DiagnosticResult
- Issue
- RiskLevel
- CommandResult
- PluginBase
- PluginManager

### Faza 3 — PowerShell Runner

- sigurno pokretanje PowerShell komandi
- timeout
- stdout/stderr
- exit code
- admin detection
- bez rušenja GUI-a

### Faza 4 — Network plugin

- hostname
- IP
- gateway
- DNS
- adapteri
- network profile
- ping gateway
- ARP tabela

### Faza 5 — SMB plugin

- SMB server config
- SMB client config
- net share
- net view
- Get-SmbShare
- test pristupa prema ručno unesenom IP-u
- poznate greške 53, 64, 6118, 1272, 5, 86, 1326

### Faza 6 — Firewall plugin

- firewall profile
- File and Printer Sharing rules
- Network Discovery rules

### Faza 7 — Services plugin

- LanmanServer
- LanmanWorkstation
- FDResPub
- fdPHost
- Dnscache
- SSDPSRV
- upnphost
- Spooler

### Faza 8 — Printer plugin

- instalirani štampači
- portovi
- IP adrese portova
- drajveri
- shared printers
- spooler
- mrežni štampači

### Faza 9 — Dashboard + Topology

- status kartice
- topology panel
- recent scan summary
- issue panel
- quick actions panel

### Faza 10 — Decision Tree Engine

Aplikacija zaključuje uzrok, ne samo prikazuje podatke.

Primjer:

```text
Ping OK + SMB port OK + credentials fail = authentication problem.
```

### Faza 11 — Report Generator

Formati:

```text
Markdown
HTML
JSON
```

Report mora sadržati:

- summary
- system info
- network
- SMB
- firewall
- services
- printers
- issues
- recommendations
- šta nije provjereno

### Faza 12 — Safe Fix Mode

Tek nakon stabilnog scana.

Dozvoljeno:

- set network profile private
- enable firewall rules
- start services
- restart print spooler

Zabranjeno bez posebne potvrde:

- SMB1
- Guest access
- firewall off
- policy changes

### Faza 13 — Installer / Portable build

- PyInstaller EXE
- portable zip
- kasnije Inno Setup installer

---

## 16. Minimalni Codex zadaci

Codexu ne davati:

```text
Napravi cijelu aplikaciju.
```

Davati male zadatke.

### Zadatak 1

```text
Napravi početni skeleton FieldFix IT aplikacije.

Stack:
- Python
- PySide6
- Windows target

Dodaj:
- osnovni main window
- sidebar
- dashboard tab
- prazne panele za Network, SMB, Firewall, Services, Printers, Reports
- core modele: DiagnosticResult, Issue, RiskLevel, CommandResult
- placeholder PluginBase i PluginManager
- README.md
- AGENTS.md
- agent workflow foldere:
  agent_skills/
  agent_runbooks/
  agent_loops/
  project_rooms/
  agent_reports/

Granice:
- ne implementirati prave fix funkcije
- ne mijenjati Windows podešavanja
- ne praviti installer
- ne komplikovati arhitekturu

Na kraju napravi agent_report.
```

### Zadatak 2

```text
Implementiraj PowerShellRunner.

Zahtjevi:
- run(command, timeout)
- stdout
- stderr
- exit_code
- timeout handling
- admin detection
- ne ruši aplikaciju ako komanda padne
- unit testovi

Ne implementirati fix komande.

Ako diraš centralni runner, koristi high_critical_code_change runbook.
Napravi agent_report.
```

### Zadatak 3

```text
Implementiraj Network plugin.

Plugin treba prikupiti:
- hostname
- active adapters
- IPv4
- gateway
- DNS
- network category
- ping gateway
- ARP table

Rezultat mora biti strukturisan.
GUI treba prikazati status i preporuke.

Ne implementirati fix.
Napravi agent_report.
```

### Zadatak 4

```text
Implementiraj SMB plugin i poznate greške.

Provjeri:
- SMB server config
- SMB client config
- net share
- net view
- Get-SmbShare
- test pristupa ručno unesenom IP-u

Prepoznaj:
- 53
- 64
- 6118
- 1272
- 5
- 86
- 1326

Za svaku grešku prikaži:
- značenje
- najvjerovatniji uzrok
- preporučeni sljedeći korak

Ne implementirati automatski fix.
Napravi agent_report.
```

---

## 17. Šta ne raditi u prvoj verziji

Ne raditi odmah:

- AI assistant
- automatski repair svega
- domain/Active Directory alat
- SMB1 fix
- Guest access fix
- remote execution
- agent orchestration
- cloud sync
- licenciranje
- kompleksan plugin marketplace

To bi ubilo projekat prije MVP-a.

---

## 18. AI Assistant kasnije

AI Assistant nije za MVP.

Kasnije može postojati panel:

```text
Describe problem:
"Ne vidim štampač."

AI odgovor:
Provjerio sam:
- gateway OK
- printer ping OK
- spooler stopped

Zaključak:
Problem je Print Spooler servis.

Preporuka:
Pokrenuti servis.

[Apply Fix]
```

AI ne smije imati pravo da automatski izvršava fix bez korisničke potvrde.

---

## 19. Finalna formula projekta

```text
FieldFix IT = Scan + Evidence + Decision Tree + Safe Fix + Report
```

Arhitektura:

```text
Core + Plugins + Reports + Fix Center
```

Agent pravila:

```text
Small task → small_safe_code_change
Risky task → project_room + high_critical_code_change + agent_report
Loop → samo uz verifier i stop uslove
Fix → nikad automatski bez potvrde
```

---

## 20. Završni princip

Ovo ne treba biti samo alat za jedan problem sa Windows mrežom.

Ovo treba biti tvoj interni IT servisni alat.

Prva verzija neka rješava:

```text
mreža + SMB + firewall + servisi + štampači
```

Kasnije može postati:

```text
švajcarski nožić za Windows administraciju
```
