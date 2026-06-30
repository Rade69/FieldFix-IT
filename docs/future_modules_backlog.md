# Future modules backlog

Ovi moduli **nisu MVP** i ne smiju ulaziti u rane Codex/agent zadatke.
Drže se ovdje da se ne nabrajaju u glavnom planu i ne prave scope creep.

Kad MVP (mreža + SMB + firewall + servisi + štampači + report) bude
stabilan, birati iz ove liste jedan modul po jednom, istim obrascem kao
postojeći moduli (`scanner.py`, `models.py`, `recommendations.py`).

---

## V2 — Prioritetne razvojne faze

### V2-A: OS Fingerprinting (Topology proširenje)

**Cilj:** Topology stranica automatski prepozna OS svakog uređaja na mreži
(Windows / Linux / macOS / Network device) bez remote login-a — samo pasivnom
analizom mrežnih signala.

**Motivacija:** Mješovita okruženja (Windows + Linux server + NAS) su česta u
malim firmama. Znati koji OS koristi koji uređaj pomaže pri dijagnostici
(npr. "SMB problem je na Linux Samba strani, ne na Windows strani").

---

#### Arhitektura

Novi fajl: `app/modules/network/os_fingerprint.py`
Novi model: `OsGuess` u `app/modules/network/models.py`
Izmjena: `topology_page.py` — dodat "Identify OS" dugme

Nema izmjena u postojećim scannerima. Fingerprinting je **opcionalni,
odvojeni korak** na Topology stranici — nije dio standardnog scana (presporo
je za svaki scan).

---

#### Model

```python
# app/modules/network/models.py — dodati:
@dataclass(frozen=True)
class OsGuess:
    ip: str
    likely_os: str        # "Windows" | "Linux" | "macOS" | "Network Device" | "Unknown"
    confidence: str       # "High" | "Medium" | "Low"
    evidence: tuple[str, ...]
```

---

#### Detekicioni signali (sve via lokalni PowerShell, bez remote login-a)

##### Signal 1 — TTL iz ping-a

```powershell
ping -n 1 -w 1000 {ip}
```

Parse TTL iz stdout redova koji sadrže "TTL=":

- TTL 128 → Windows (Medium confidence)
- TTL 64  → Linux ili macOS (Medium confidence)
- TTL 255 → Network device / router (Medium confidence)

##### Signal 2 — Port fingerprinting

```powershell
Test-NetConnection -ComputerName {ip} -Port {port} -WarningAction SilentlyContinue |
Select-Object TcpTestSucceeded | ConvertTo-Json -Compress
```

Portovi koje provjeravamo:

| Port | Zaključak                              |
| ---- | -------------------------------------- |
| 445  | SMB otvoren → **Windows** (jak signal) |
| 22   | SSH otvoren → Linux ili macOS          |
| 3389 | RDP otvoren → Windows (dodatni signal) |
| 5353 | mDNS otvoren → macOS ili Linux         |

##### Signal 3 — SMB hostname preuzimanje (bonus)

Ako je port 445 otvoren, `net view \\{ip}` ili `Get-SmbConnection` mogu
otkriti Windows hostname — što je konačan dokaz da je Windows.

---

#### Confidence scoring

```python
def _score(ttl: int | None, ports: dict[int, bool]) -> tuple[str, str]:
    # "os", "confidence"
    if ports.get(445):                          return "Windows",        "High"
    if ports.get(22) and ports.get(5353):       return "macOS",          "Medium"
    if ports.get(22) and not ports.get(445):    return "Linux",          "Medium"
    if ttl == 128:                              return "Windows",        "Medium"
    if ttl == 64 and ports.get(22):             return "Linux/macOS",    "High"
    if ttl == 64:                               return "Linux/macOS",    "Low"
    if ttl == 255:                              return "Network Device", "Medium"
    return "Unknown", "Low"
```

---

#### `OsFingerprintScanner`

```python
class OsFingerprintScanner:
    def __init__(self, runner: PowerShellRunner) -> None: ...

    def scan_ip(self, ip: str) -> OsGuess:
        """Single IP — runs TTL + port checks."""
        ttl = self._get_ttl(ip)
        ports = self._check_ports(ip, [22, 445, 3389, 5353])
        os_name, confidence = _score(ttl, ports)
        evidence = _build_evidence(ttl, ports)
        return OsGuess(ip=ip, likely_os=os_name,
                       confidence=confidence, evidence=evidence)

    def scan_multiple(
        self,
        ips: list[str],
        on_progress: Callable[[str, int, int], None] | None = None,
    ) -> dict[str, OsGuess]:
        """Scan all IPs. on_progress(ip, current, total) for UI feedback."""
        results = {}
        for i, ip in enumerate(ips):
            if on_progress:
                on_progress(ip, i + 1, len(ips))
            results[ip] = self.scan_ip(ip)
        return results
```

Svaki IP = 4 port provjere + 1 ping = ~5 PS poziva.
Za 10 uređaja na mreži: ~50 PS poziva, ~10-20 sekundi.
Zato je ovo odvojen "Identify OS" korak, ne dio standardnog scana.

---

#### UI izmjene (Topology stranica)

- Dodat "🔍 Identify OS" dugme u header pored "Scan Network"
- Čvor na grafu dobija OS ikonu: 🪟 Windows | 🐧 Linux | 🍎 macOS | 🌐 Network Device | ❓ Unknown
- Tooltip na čvoru: "Windows — High confidence (port 445 open, TTL=128)"

---

#### Fajlovi koji se mijenjaju — V2-A

| Fajl | Akcija |
| ---- | ------ |
| `app/modules/network/models.py` | Dodati `OsGuess` dataclass |
| `app/modules/network/os_fingerprint.py` | Novi scanner |
| `app/gui/pages/topology_page.py` | "Identify OS" dugme + OS ikone na čvorovima |
| `tests/modules/network/test_os_fingerprint.py` | Unit testovi sa mock PS outputom |

Nije potrebno mijenjati: `NetworkScanner`, `ArpEntry`, `NetworkData`,
`DashboardPage`, `ScanSession` — OS fingerprinting je potpuno aditivno.

---

---

### V2-B: Remote Windows via WinRM

**Cilj:** Skenirati **udaljenu Windows mašinu** na mreži koristeći iste
postojeće module (NetworkScanner, SMBScanner, itd.) bez ikakvog agenta na
ciljanoj mašini — samo WinRM/PS Remoting koji je ugrađen u Windows.

**Motivacija:** IT tehničar sjedi za jednim računarom i treba dijagnosticirati
problem na drugom (server, kolegina radna stanica). Umjesto da hoda do mašine
ili koristi TeamViewer, otvori "Remote Scan" u FieldFix IT, unese IP i
credentials, i dobije isti dijagnostički izvještaj kao da je lokalno.

**Ključna arhitekturna prednost:** Svi postojeći moduli (`NetworkScanner`,
`SmbScanner`, `ServicesScanner`, `PrintersScanner`, `FirewallScanner`)
primaju `runner: PowerShellRunner` kao parametar. Ako napravimo
`RemotePowerShellRunner` koji ima **identičan interfejs**, nijedan skaner
se ne mora mijenjati. Samo se prosljeđuje drugi runner.

---

#### Arhitektura — RemotePowerShellRunner

```text
Lokalni runner:                Remote runner:
PowerShellRunner               RemotePowerShellRunner(ip, cred)
    │                               │
    ▼                               ▼
powershell.exe                 powershell.exe -Command
-Command "{cmd}"               "Invoke-Command -ComputerName {ip}
                                -Credential $cred
                                -ScriptBlock { {cmd} }"
    │                               │
    ▼                               ▼
Lokalni OS                     Udaljeni Windows OS
```

Oba vraćaju `CommandResult` — isti model, isti interfejs.

---

#### Preduvjeti na ciljanoj mašini

WinRM mora biti aktivan. Na ciljanoj mašini (kao admin):

```powershell
Enable-PSRemoting -Force
# Za pristup s workgroup mašine (ne domain):
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force
```

FieldFix IT će imati "WinRM Setup Guide" panel koji prikazuje ove komande.

---

#### `RemotePowerShellRunner`

```python
# app/core/remote_runner.py

@dataclass(frozen=True)
class RemoteCredential:
    username: str
    password: str  # NIKAD se ne piše na disk — samo u RAM-u tokom sesije

class RemotePowerShellRunner:
    """Executes PowerShell commands on a remote Windows machine via WS-Man.

    Implements the same interface as PowerShellRunner so all existing
    scanners work unchanged when passed this runner.
    """

    def __init__(self, target_ip: str, credential: RemoteCredential) -> None:
        self._ip = target_ip
        self._cred = credential

    def run(self, command: str, timeout: int = 30) -> CommandResult:
        # Gradi PS wrapper:
        # $pass = ConvertTo-SecureString '...' -AsPlainText -Force
        # $cred = New-Object PSCredential('user', $pass)
        # Invoke-Command -ComputerName {ip} -Credential $cred
        #                -ScriptBlock { {command} }
        ...

    def run_json(self, command: str, timeout: int = 30) -> CommandResult:
        # Identičan pattern kao PowerShellRunner.run_json()
        ...
```

**Sigurnosna napomena:** `ConvertTo-SecureString -AsPlainText` je jedini
praktični način da se credentials prenesu u PS proces bez interaktivnog
promptanja. Lozinka postoji u memoriji tokom PS poziva (< 1 sekunde) a ne
piše se nigdje. Za V3: DPAPI enkripcija (`ConvertFrom-SecureString`).

---

#### Test konekcije

Prije skeniranja, provjera da li je WinRM dostupan:

```powershell
Test-WSMan -ComputerName {ip} -Credential $cred | ConvertTo-Json -Compress
```

Ako `Test-WSMan` uspije → WinRM aktivan, može se skenirati.
Ako ne → prikazati poruku s uputama kako aktivirati WinRM.

---

#### Remote Scan stranica

Nova stranica `app/gui/pages/remote_scan_page.py`:

```text
Header: "🖥 Remote Scan" | status label | "Test Connection" | "Run Remote Scan"

Target panel:
  IP / hostname:  [_________________]
  Username:       [_________________]   (domain\user ili .\localuser)
  Password:       [●●●●●●●●●●●●●●●]    (QLineEdit.EchoMode.Password)
  [Test WinRM Connection]

Modules (checkboxes):
  ☑ Network  ☑ SMB  ☑ Services  ☑ Printers  ☑ Firewall

─────────────────────────────────────────────────
Results (isti prikaz kao individualne module stranice,
ali nad remote podacima):
  RemoteNetworkSection | RemoteSmbSection | ...

[Export Report]  — isti Report Engine kao lokalni
```

---

#### Kako scaneri rade remote — bez izmjena

```python
# Lokalni scan (postojeće):
runner = PowerShellRunner()
network_data = NetworkScanner(runner).scan()

# Remote scan (novo — identičan poziv!):
runner = RemotePowerShellRunner("192.168.1.50", cred)
network_data = NetworkScanner(runner).scan()  # NIJE POTREBNA IZMJENA
```

Jedina razlika: PS komande se izvršavaju na `192.168.1.50` umjesto lokalno.
Output je identičan JSON — isti parseri, isti modeli, isti widgeti.

---

#### Ograničenja v1

| Ograničenje | Napomena |
| ----------- | -------- |
| Credentials nisu perzistentni | Samo RAM, gube se zatvaranjem app-a |
| Jedan target istovremeno | Paralelni remote scan je V3 |
| WinRM mora biti ručno aktivan | App daje upute, ne može sam aktivirati |
| Workgroup okruženje | Domain (Kerberos) radi automatski — workgroup zahtijeva TrustedHosts konfiguraciju |
| Firewall na targetu | WinRM koristi port 5985 (HTTP) ili 5986 (HTTPS) |

---

#### Fajlovi koji se mijenjaju — V2-B

| Fajl | Akcija |
| ---- | ------ |
| `app/core/remote_runner.py` | Novi `RemoteCredential` + `RemotePowerShellRunner` |
| `app/gui/pages/remote_scan_page.py` | Nova Remote Scan stranica |
| `app/gui/main_window.py` | Dodati "Remote Scan" u sidebar |
| `tests/core/test_remote_runner.py` | Unit testovi (mock subprocess) |

Nije potrebno mijenjati: nijedan postojeći skaner, nijedan postojeći model,
nijedan postojeći widget.

---

#### Redoslijed implementacije

1. `RemotePowerShellRunner` + `Test-WSMan` provjera → testovi
2. `remote_scan_page.py` — samo UI bez skeniranja (IP/cred forma + test btn)
3. Wire skenere na remote runner → rezultati u postojećim widgetima
4. Export remote resulta kroz postojeći Report Engine

---

---

## Ostali moduli (bez prioriteta)

- Windows Update
- Event Viewer
- Disk / SMART
- Backup
- RDP
- VPN
- PostgreSQL
- SQL Server
- Docker
- Hyper-V
- IIS
- Active Directory
- Certificates
- USB devices
- UPS
- Wi-Fi analysis
- Speed test
