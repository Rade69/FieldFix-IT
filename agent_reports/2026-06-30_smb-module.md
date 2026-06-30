# Agent report: SMB module (Zadatak 5)

## Datum
2026-06-30

## Scope
- `app/modules/smb/__init__.py` (novo)
- `app/modules/smb/models.py` (novo)
- `app/modules/smb/scanner.py` (novo)
- `app/modules/smb/net_view_parser.py` (novo — izolovani legacy text parser)
- `app/knowledge/smb/error_53.yaml` (novo)
- `app/knowledge/smb/error_64.yaml` (novo)
- `app/knowledge/smb/error_6118.yaml` (novo)
- `app/knowledge/smb/error_1272.yaml` (novo)
- `app/knowledge/smb/error_5.yaml` (novo)
- `app/knowledge/smb/error_86.yaml` (novo)
- `app/knowledge/smb/error_1326.yaml` (novo)
- `app/gui/pages/smb_page.py` (update — stub → funkcionalna stranica)
- `tests/modules/smb/__init__.py` (novo)
- `tests/modules/smb/test_net_view_parser.py` (novo)
- `tests/modules/smb/test_smb_scanner.py` (novo)

## GitNexus impact (provjera prije izmjene)
- `SmbPage`: LOW (1 direktni — main_window.py, očekivano)
- `NetworkScanner`: LOW (referentni uvid u pattern koji se ponavlja)
- SMB module je novi kod — nema izmjena na postojećim simbolima

## Šta je urađeno

### `app/modules/smb/models.py`

6 frozen dataclassa:
- `SmbServerConfig` — EnableSMB1Protocol, EnableSMB2Protocol, signing
- `SmbClientConfig` — EnableInsecureGuestLogons, signing
- `SmbShare` — name, path, description, share_type
- `PortCheckResult` — target_ip, port=445, reachable, error
- `NetViewEntry` — name, share_type, comment
- `SmbData` — agregat svega + scan_duration_ms, errors

### `app/modules/smb/scanner.py`

`SmbScanner(runner: PowerShellRunner)` s metodom `scan(target_ip="") → SmbData`.

| Privatna metoda | PS komanda | Tip |
|---|---|---|
| `_get_server_config` | `Get-SmbServerConfiguration \| ... \| ConvertTo-Json` | JSON |
| `_get_client_config` | `Get-SmbClientConfiguration \| ... \| ConvertTo-Json` | JSON |
| `_get_shares` | `Get-SmbShare \| ... \| ConvertTo-Json` | JSON |
| `_check_port_445` | `Test-NetConnection -Port 445 \| ConvertTo-Json` | JSON |
| `_net_view` | `net view \\\\IP 2>&1` | Text (legacy) |

Port 445 provjera i `net view` se pokreću samo ako je proslijeđen `target_ip`.

`NET_VIEW_ERROR_HINTS` dict: Python-nativni mapper error kodova → kratka
objašnjenja za GUI. Ovo NIJE knowledge base — to su `app/knowledge/smb/*.yaml`.

### `app/modules/smb/net_view_parser.py`

Izolovani legacy text parser za `net view` output (jedino mjesto gdje se
parsira tekst `net view` komande, per `docs/architecture_notes.md`).

Dvije javne funkcije:
- `parse_error_code(output)` → `int | None` — regex na "System error N"
- `parse_shares(output)` → `list[NetViewEntry]` — parsa tabelu shareva

**Bug koji je otkriven i popravljen:** "Used as" kolona u `net view` outputu
je prazna u većini slučajeva (lokalni sharevi koji nisu mapped kao drive).
Originalni parser pretpostavljao je da je komentar uvijek na indeksu 3+,
ali kad je "Used as" prazan, komentar počinje na indeksu 2.
**Popravka:** regex provjera da li je `parts[2]` drive letter (`^[A-Za-z]:$`);
ako jeste → "Used as" je tu, komentar od `parts[3:]`; inače komentar od `parts[2:]`.

### `app/knowledge/smb/` (7 YAML fajlova)

Documentary-only knowledge base za greške: 53, 64, 6118, 1272, 5, 86, 1326.
Format: code, message, meaning, likely_causes, recommended_checks, safe_fixes,
dangerous_fixes, notes.

**Ovi fajlovi se ne parsiraju niti izvršavaju u kodu** — per odluke u
`docs/architecture_notes.md` (confidence_rules Opcija A). Namijenjeni su
čovjeku/agentu kao kontekst, i budućem Decision Engine-u (Faza 10) koji
će implementirati logiku zaključivanja u pravom Python kodu.

### `app/gui/pages/smb_page.py`

Funkcionalna SMB stranica s:
- Header: "📂 SMB / Sharing Diagnostics" + Target IP unos (QLineEdit) + status + dugme
- SMB Server Config panel: SMB1/SMB2 status s visual badge (✓/✕ u boji)
- SMB Client Config panel: Insecure Guest Logons s upozorenjima u boji
- Local Shares panel: lista dijeljenih resursa
- Port 445 panel (samo ako je unesen target IP)
- Net View panel s prikazom shareva ili error koda + hint-a (samo ako target IP)
- Warnings panel za greške skeniranja

### Testovi

26 novih testova:
- `test_net_view_parser.py` (10): parse_error_code (4) + parse_shares (6)
- `test_smb_scanner.py` (16): scan basics (3), server config (2), client config (2),
  shares (3), port 445 (3), net view (3)

## Šta nije dirano

- Nijedna Windows postavka nije promijenjena
- SMB1 fix, Guest access fix — nisu implementirani (zabranjeno u MVP)
- Dashboard, Network module i ostale stranice — netaknute
- PowerShellRunner — nije mijenjan

## Verifikacija

```
92 passed in 0.63s
```

Svi PS pozivi i `net view` su mocked — nema stvarnih sistemskih poziva u testovima.

## Rizici / ograničenja

- **`net view` encoding**: `net view` može da ispiše non-UTF8 znakove za
  nazive computera s posebnim karakterima. `errors='replace'` u runner-u
  sprečava crash ali može korumpirati output. Pratiti na stvarnom Windowsu.
- **Sinhroni scan blokira GUI** (isti problem kao NetworkPage) — Threading V2
- **`Test-NetConnection` timeout**: default timeout može biti do 10s po
  komandi ako je port zatvoren; `-WarningAction SilentlyContinue` smanjuje
  output ali ne timeout. Pratiti na terenu.
- **Knowledge YAML nisu povezani sa scannerom**: Decision Engine (Faza 10)
  treba da iskoristi ove fajlove i poveže ih sa `SmbData.net_view_error_code`

## Potreban follow-up

- **Faza 6 (Firewall module)** — sljedeći zadatak u planu
- **Faza 10 (Decision Engine)** — treba koristiti knowledge YAMLe za
  generisanje `Issue` i `Recommendation` objekata iz `SmbData`
- **Threading** za NetworkPage i SmbPage (V2, kad se stabilizuje API modula)

## Potrebna korisnička potvrda

Stranica nije testirana na stvarnom Windowsu. Preporučeno: pokrenuti aplikaciju,
otvoriti Sharing/SMB stranicu, kliknuti "Run Scan" bez target IP-a da vidi
lokalne shareve i SMB konfiguraciju; zatim unijeti IP problematičnog računara
i vidjeti port 445 status i net view rezultat.
