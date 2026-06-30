# Agent report: Network module (Zadatak 4)

## Datum
2026-06-30

## Scope
- `app/modules/__init__.py` (novo)
- `app/modules/network/__init__.py` (novo)
- `app/modules/network/models.py` (novo)
- `app/modules/network/scanner.py` (novo)
- `app/gui/pages/network_page.py` (update — stub → funkcionalna stranica)
- `tests/modules/__init__.py` (novo)
- `tests/modules/network/__init__.py` (novo)
- `tests/modules/network/test_network_scanner.py` (novo)

## GitNexus impact (provjera prije izmjene)
- `PowerShellRunner`: LOW (0 kalera) — novi modul, nije još korišten
- `NetworkPage`: LOW (1 direktni — main_window.py importuje je, što je očekivano)
- Network module je novi kod, nema izmjena na postojećim simbolima

## Šta je urađeno

### `app/modules/network/models.py`

7 frozen dataclassa koji zajedno čine `NetworkData` snapshot:
- `AdapterInfo` — name, description, status, link_speed_bps, mac_address
- `IPAddressInfo` — interface_alias, ip_address, prefix_length
- `GatewayInfo` — interface_alias, next_hop, metric
- `DNSInfo` — interface_alias, servers (tuple[str, ...])
- `NetworkProfile` — name, interface_alias, category (string)
- `ArpEntry` — interface_alias, ip_address, mac_address, state
- `NetworkData` — agregat svih gornjih + hostname, gateway_reachable, scan_duration_ms, errors

Sve kolekcije su `tuple` (ne `list`) jer su klase frozen — immutable po defaultu.

### `app/modules/network/scanner.py`

`NetworkScanner(runner: PowerShellRunner)` s jednom javnom metodom `scan() → NetworkData`.

8 privatnih pomoćnih metoda, svaka prikuplja jedan aspekt:

| Metoda | PS komanda (JSON-first) |
|---|---|
| `_get_hostname` | `[System.Net.Dns]::GetHostName()` (text) |
| `_get_adapters` | `Get-NetAdapter \| ... \| ConvertTo-Json -Compress` |
| `_get_ip_addresses` | `Get-NetIPAddress \| Where-Object IPv4 \| ConvertTo-Json` |
| `_get_gateways` | `Get-NetRoute \| Where 0.0.0.0/0 \| ConvertTo-Json` |
| `_get_dns` | `Get-DnsClientServerAddress \| ConvertTo-Json` |
| `_get_profiles` | `Get-NetConnectionProfile \| ConvertTo-Json` |
| `_ping_gateway` | `Test-Connection -Quiet \| ConvertTo-Json` |
| `_get_arp_entries` | `Get-NetNeighbor \| ConvertTo-Json` |

Svaka metoda: pri grešci dodaje string u `errors` listu i vraća prazan rezultat
(ne raise-uje). Skan nastavlja bez obzira na parcijalne greške.

**`_as_list()` helper**: PowerShell vraća jedan `dict` (ne `list`) kad postoji
samo jedan rezultat — ova funkcija normalizuje PS JSON output u `list` uvijek.

**`_format_speed(bps)`**: formatira `LinkSpeed` integer u human-readable string
(Gbps/Mbps/Kbps/bps).

**NetworkCategory mapping**: PS vraća integer (0=Public, 1=Private,
3=DomainAuthenticated) — mapiran u string.

**DNS `ServerAddresses` edge case**: PS može da vrati string (ne listu) ako
postoji samo jedan DNS server — normalizovan u `[string]`.

### `app/gui/pages/network_page.py`

Zamijenjen stub sa funkcionalnom stranicom:
- Header: "🌐 Network Diagnostics" + status label + "▶ Run Scan" dugme
- QScrollArea sa PanelCard panelima koji se pune nakon skeniranja
- 5 panela: Host/Profile, Adapters, Addressing, Gateway Ping, ARP Table
- Error panel se pojavljuje samo ako postoje greške
- Scan je sinhroni (MVP) — `QApplication.processEvents()` osvježava UI
  prije nego što PS pozivi počnu

### Testovi

31 novi test u `tests/modules/network/test_network_scanner.py`:
- `TestAsListHelper` (4): None, dict, list, unexpected scalar
- `TestFormatSpeed` (5): Gbps, Mbps, Kbps, bps, None
- `TestScanReturnsNetworkData` (2): instanceof provjera, duration >= 0
- `TestHostname` (3): uspješno, greška → prazno, greška → error entry
- `TestAdapters` (3): single dict, multi list, failed → error
- `TestIPAddresses` (1): parsing provjera
- `TestGateways` (1): parsing provjera
- `TestDNS` (2): lista servera, normalizacija single stringa
- `TestNetworkProfiles` (3): Private, Public, Unknown int
- `TestPingGateway` (4): True, False, no gateways, 0.0.0.0 skip
- `TestArpEntries` (2): parsing, failed → error
- `TestErrorCollection` (1): višestruke greške prikupljene

## Šta nije dirano

- Nijedna Windows postavka nije promijenjena (Scan Mode)
- Fix komande nisu implementirane
- Dashboard i ostale stranice su netaknute
- PowerShellRunner nije mijenjan
- Core modeli (Zadatak 2) nisu mijenjan

## Verifikacija

```
66 passed in 0.63s
```

Svi PS pozivi su mockirani u testovima — nema stvarnih sistemskih poziva.
Stvarna verifikacija (encoding, timing, adapter nazivi) dolazi pri prvom
pokretanju na stvarnom Windows uređaju.

## Rizici / ograničenja

- **Sinhroni scan blokira GUI**: `QApplication.processEvents()` sprečava
  freeze vizuelno, ali dugme ostaje disabled dok se ne završi skan (~3-5s
  tipično). Threading je V2 poboljšanje
- **ARP limit od 25 redova u GUI**: filtriran radi čitljivosti. Puni podaci
  su u `NetworkData.arp_entries`
- **`Test-Connection` može biti blokiran**: neki korporativni firewalli
  blokiraju ICMP. Rezultat tada je `None` (nije False) — to je ispravno
- **PS 5 + ConvertTo-Json -Compress**: `-Compress` flag postoji od PS 3,
  ali je testiran samo na PS 5.1 / PS 7. Ako target ima stariji PS, fallback
  bez `-Compress` je trivijalna izmjena

## Potreban follow-up

- **Threading**: NetworkPage.scan() treba `QThread` ili `QRunnable` u V2
  da ne blokira event loop pri dužim skenovima
- **Zadatak 5 (SMB module)**: isti pattern kao Network — scanner.py +
  models.py + stub page update

## Potrebna korisnička potvrda

Stranica je funkcionalna ali nije testirana na stvarnom Windowsu. Preporučeno:
pokrenuti aplikaciju, otvoriti Network stranicu, kliknuti "Run Scan" i
provjeriti da li se rezultati prikazuju ispravno za konkretnu mrežnu konfiguraciju.
