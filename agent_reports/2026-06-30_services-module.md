# Agent report: Services module (Zadatak 7 / Faza 7)

## Datum
2026-06-30

## Scope
- `app/modules/services/__init__.py` (novo)
- `app/modules/services/models.py` (novo)
- `app/modules/services/scanner.py` (novo)
- `app/gui/pages/services_page.py` (update — stub → funkcionalna stranica)
- `tests/modules/services/__init__.py` (novo)
- `tests/modules/services/test_services_scanner.py` (novo)

## GitNexus impact (provjera prije izmjene)
- `ServicesPage`: LOW (1 direktni — main_window.py, očekivano)
- Novi modul — nema izmjena na postojećim simbolima

## Šta je urađeno

### `app/modules/services/models.py`

2 frozen dataclassa:
- `ServiceInfo` — name, display_name, status, start_type, required_for (kontekst za GUI)
- `ServicesData` — tuple[ServiceInfo, ...], scan_duration_ms, errors

### `app/modules/services/scanner.py`

`ServicesScanner(runner: PowerShellRunner)` s metodom `scan() → ServicesData`.

**Jedan PS poziv** koji dohvata svih 8 servisa odjednom:
```powershell
Get-Service -Name LanmanServer, LanmanWorkstation, FDResPub, fdPHost,
            Dnscache, SSDPSRV, upnphost, Spooler -ErrorAction SilentlyContinue |
Select-Object Name, DisplayName,
    @{N='Status';E={$_.Status.ToString()}},
    @{N='StartType';E={$_.StartType.ToString()}} |
ConvertTo-Json -Compress
```

`ToString()` na Status/StartType osigurava string output (npr. "Running"),
a ne PS enum integer koji `ConvertTo-Json` može da vrati. `_normalize()`
helper hvata i int fallback (mapovi `_STATUS_MAP`, `_START_TYPE_MAP`).

**MONITORED_SERVICES dict**: definisan redosljed 8 servisa + opis šta svaki radi.
Scanner koristi ovaj dict za:
1. Izgradnju PS komande (nazivi servisa)
2. Popunjavanje `required_for` fielda u `ServiceInfo`
3. Sortiranje rezultata u definisanom redoslijedu
4. Detekciju i reportovanje servisa koji nedostaju na sistemu

### `app/gui/pages/services_page.py`

Funkcionalna stranica s:
- Header: "⚙ Services Diagnostics" + status + dugme
- Summary badges: ✓ Running N | ✕ Stopped N | Total N
- Tabela s kolonama: Service | Display Name | Status | Startup | Potrebno za
- Status kolona: ✓ Running (zeleno) / ✕ Stopped (crveno) / ● ostalo (žuto)
- Startup kolona: Automatic (zeleno) / Manual (sivo) / Disabled (crveno)
- Warnings panel za greške i nedostajuće servise

## Šta nije dirano

- Nijedna Windows postavka nije promijenjena (Scan Mode)
- Fix komande za servise nisu implementirane (Faza 13 — Fix Center)
- Ostale stranice i moduli — netaknuti

## Verifikacija

```
107 passed in 1.17s
```

## Rizici / ograničenja

- **Sinhroni scan** (isti problem kao NetworkPage/SmbPage) — threading V2
- **`-ErrorAction SilentlyContinue`**: ako servis ne postoji, PS ga tiho
  preskače (ne vraća grešku). Scanner detektuje nedostajuće servise poređenjem
  sa `MONITORED_SERVICES` i dodaje ih sa statusom "NotFound"
- **upnphost / SSDPSRV**: mogu biti disabled by design u enterprise okruženju —
  to nije greška nego sigurnosna politika. Decision Engine (Faza 10) treba
  ovo da uzme u obzir

## Potreban follow-up

- Zadatak 8 — Printer module (sljedeći)
- Faza 13 (Fix Center): start/stop/restart servis akcije s risk levelom i
  admin provjerom
