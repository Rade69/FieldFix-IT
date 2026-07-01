## Datum
2026-07-01

## Scope
- `app/gui/pages/topology_page.py`
- `app/modules/network/subnet_scanner.py`

## GitNexus impact
Nije rađena formalna provjera — izmjene su bile aditivne (novi widgeti, nova logika u scaneru) bez promjene postojećih potpisa.

## Šta je urađeno

### 1. Fix subnet scanner (PS 5.1 kompatibilnost)
`??` null-coalescing operator u PowerShell skripti unutar `_PS_SCAN` nije podržan u PS 5.1 (Windows default). Zamijenjen sa `if ($hostnames.ContainsKey($ip)) { ... } else { "" }`. Scanner je nakon fixe detektovao sve uređaje na mreži.

### 2. Kompaktne summary kartice (Tačka 5)
`_StatCard.setFixedHeight` smanjen sa 70px na 48px. Layout prepravljen na dvije horizontalne linije: icon + title + vrijednost (isti red), sub ispod. Border-radius smanjen sa 8px na 6px.

### 3. Filter bar (Tačka 6)
Dodat red sa 5 `QPushButton` (checkable, exclusive via `QButtonGroup`):
`All · Printers · PCs · Unknown · Network noise`
Default: `All`. Svaki klik poziva `_apply_filter()` koji re-renderuje listu bez ponovnog skeniranja.

### 4. "Hidden noise" counter (Tačka 2)
Dodana `_is_noise_arp(entry)` funkcija koja prepoznaje multicast/broadcast ARP unose (224.x, 239.x, .255, FF-FF, 01-00-5E). U "All" filteru prikazuje se na dnu: `📡 Hidden: N multicast/broadcast entries`. Klik na "Network noise" filter otvara `_NoiseRow` listu.

### 5. HTTP printer name resolution
Za printere bez DNS hostname-a koji imaju port 80 otvoren, scanner radi `GET http://{ip}/` i extraktuje `<title>` tag. Funkcija `_clean_title()` uklanja `html.unescape()`, prefikse kao "Remote UI: Login:", duplicirane segmente. Canon imageRUNNER1133 na 192.168.100.23 sada prikazuje `imageRUNNER1133 series`.

## Šta nije dirano
- Map tab (graph prikaz)
- `NetworkScanner`, `PrintersScanner`
- Settings, Fix Center, Dashboard
- Postojeće ARP filtriranje u `build_nodes()`

## Verifikacija
- `python -c "from app.gui.pages.topology_page import TopologyPage; ..."` — import i init OK
- Subnet scanner end-to-end: 6 uređaja, Canon pokazuje ime, scan time ~7s
- HTTP title test: `_fetch_http_title('192.168.100.23')` → `'imageRUNNER1133 series'`

## Rizici / ograničenja
- HTTP fetch timeout 2.5s po printeru — u worst caseu N printera × 2.5s, ali sekvencijalno, ne paralelno
- Epson (192.168.100.169) nema dostupan HTTP interfejs — ostaje bez naziva (ali je prikazan kroz lokalni Windows inventar)
- PS 5.1 vs PS 7 razlika može se ponovo pojaviti ako se dodaju novi PS operatori

## Potreban follow-up
- Razmisliti o paralelnom HTTP fetchu ako mreža ima više printera
- Dodati SNMP fallback za printere bez porta 80 (opciono, nije hitno)
