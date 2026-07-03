## Datum

2026-07-01

## Scope

- `app/core/scenario.py` (izmjena)
- `app/gui/pages/scenarios_page.py` (izmjena)

## GitNexus impact

Additivna izmjena na dva postojeća fajla koji nemaju callers izvan
`main_window.py` (koji ih samo importuje). LOW rizik.

## Šta je urađeno

### `app/core/scenario.py`

- Dodat `group: str = ""` field na `CheckItem` dataclass.
- Svi `CheckItem`-i u `check_connect_two_pcs()` dobili su odgovarajuće
  `group=` vrijednosti: `"Network"`, `"Sharing"`, `"Firewall & Discovery"`.
- Svi `CheckItem`-i u `check_add_network_printer()` dobili su `group=`:
  `"Spooler"`, `"Network"`, `"Discovery"`, `"Printer"`.
- Ažurirani `ADD_NETWORK_PRINTER.description` i `.tip` da odražavaju
  novi cilj: instalacija štampača na lokalnom računaru, ne slanje
  instrukcija nekome.

### `app/gui/pages/scenarios_page.py`

**`_ResultsPanel.show_checks()`** — zamijenjeno hardkodirano grupiranje
`items[0:2] / items[2:5] / items[5:]` dinamičkim grupiranjem po
`item.group`. Čuva redoslijed inserovanja. Radi za oba scenarija i
sve buduće scenarije bez izmjene.

**`_PrinterInstallWorker(QThread)`** — novi worker koji izvršava:
1. `Add-PrinterPort` (TCP/IP port sa IP adresom štampača)
2. `Add-Printer` sa prvim dostupnim driverom iz liste:
   - `Microsoft IPP Class Driver` (ugrađen u Windows 10/11, radi za
     većinu modernih štampača bez downloada)
   - `Generic / Text Only` (fallback za starije uređaje)
3. Emituje `finished(bool, str)` — success i poruku s imenom drajvera
   ili greškom.

**`_InstallPanel(QFrame)`** — novi widget koji se prikazuje ispod
checkiste za `add_network_printer` scenarij kada:
- Unesena je validna IPv4 adresa
- Štampač nije već instaliran
- Dijagnostika je završena

Sadrži:
- Naziv akcije s IP adresom
- Opis šta se mijenja (port + printer name)
- `▶ Install Printer` dugme (zeleno, zahtijeva admin)
- Ako nije admin: `🛡 Restart as Administrator` dugme umjesto
  disabled Install (isti pattern kao Fix Center)
- Confirmation QMessageBox prije izvršavanja
- Prikaz rezultata inline (✓ driver name ili ✕ greška + Retry)

**`ScenariosPage._select_scenario()`** — label IP polja dinamički
se mijenja: `"Printer IP:"` za printer scenarij, `"Target PC IP
(optional):"` za ostale.

**`ScenariosPage._on_finished()`** — logika show/hide:
- Printer scenarij: prikazuje `_install_panel`, sakriva `_remote_panel`
- Connect two PCs scenarij: prikazuje `_remote_panel`, sakriva
  `_install_panel`

## Arhitekturne odluke

- **Inline install, ne Fix Center navigacija**: instalacija štampača
  je integralni dio scenarija, ne generički fix. Inline panel daje
  bolji UX (korisnik ne mora ići na drugu stranicu).
- **Isti security pattern kao Fix Center**: admin check, confirmation
  dialog, explicit Apply — automatsko izvršavanje nije moguće.
- **Driver fallback lista**: IPP Class Driver je primarni (builtin,
  bez downloada). Generic / Text Only je fallback za starije OS.
  Korisnik ne mora birati — aplikacija proba redom.
- **IPv4 validacija**: `ipaddress.IPv4Address(ip)` prije nego što se
  IP ubaci u PS komandu. IP se embedduje u single-quoted PS string
  (`$ip = '192.168.1.x'`) što eliminira injection rizik.

## Šta nije dirano

- `fix_center_page.py` — nema izmjena
- `scan_session.py` — nema izmjena
- `main_window.py` — nema izmjena
- `remote_checklist_add_network_printer()` u scenario.py — zadržana,
  ali se ne prikazuje u UI za ovaj scenarij (reserved za V2)

## Verifikacija

- Import provjera: `python -c "from app.gui.pages.scenarios_page import ScenariosPage"` → OK
- Provjera group field-a i grupiranja: manuelni Python test → OK
  - `connect_two_pcs` groups: `Firewall & Discovery`, `Network`, `Sharing`
  - `add_network_printer` groups: `Discovery`, `Network`, `Printer`, `Spooler`
- Ručna provjera UI potrebna: pokrenuti app, odabrati Add Network Printer,
  unijeti IP, pokrenuti dijagnostiku, provjeriti da se Install panel pojavljuje.

## Rizici / ograničenja

- `Microsoft IPP Class Driver` postoji na svim Windows 10/11 instalacijama.
  Na Windows Server ili starijim sistemima možda ne postoji — u tom
  slučaju `Generic / Text Only` preuzima, ali nudi samo basic printing.
- Štampač koji ne podržava IPP (stari PCL/PS modeli) možda neće raditi
  sa ugrađenim drajverima — korisnik treba instalirati OEM drajver ručno.
- Ako Spooler nije pokrenut, `Add-PrinterPort` će failati — greška
  se prikazuje inline u Install panelu, korisnik vidi šta treba uraditi.

## Potreban follow-up

- Razmotriti WSD discovery (port 5357) kao alternativu TCP/IP portu
  za moderne štampače — V2 poboljšanje.
- Dodati "Open Printers settings" link u Install panel nakon uspješne
  instalacije — konfort feature za V2.
- Skill fajl za Scenarios pattern (.claude/skills/) — kada pattern
  sazri sa 3+ scenarija.
