# FieldFix IT

Windows desktop tool for field IT diagnostics and controlled repair of common
problems on Windows 10/11 workstations — network connectivity, SMB file
sharing, Windows Firewall, system services, and printers.

> **Status: Public Beta (v1.0.0)**  
> Tested on Windows 10/11. Read-only by default — no system changes without explicit confirmation.

```text
Scan → Evidence → Decision → Recommendation → Controlled Fix → Report
```

## Features

- **Dashboard** — one-click scan with module status cards and issue summary
- **Network diagnostics** — adapters, IP addressing, gateway reachability, ARP table
- **SMB / Sharing** — SMB1/SMB2 config, security signatures, guest logon policy, local shares, remote port 445 test
- **Firewall** — profile status (Domain/Private/Public) and rule groups for file sharing and network discovery
- **Services** — status of 8 critical Windows services (LanmanServer, Spooler, FDResPub, etc.)
- **Printers** — installed printer list with status, driver, port, and print job count
- **Network Topology** — visual inventory of detected devices on the LAN (Inventory + Map views)
- **Guided Scenarios** — step-by-step workflows: Connect Two PCs, Add Network Printer, Fix Printer Problems
- **Decision Engine** — rule-based analysis that detects issues and links directly to the relevant fix
- **Fix Center** — curated fix list with explicit confirmation required for every action
- **Reports** — export diagnostic reports as Markdown, HTML, or JSON
- **Settings** — theme (Dark/Light), scan modules, timeout, report folder

## Safety model

- **Read-Only Scan Mode by default** — scanning never changes any Windows setting
- **No automatic fixes** — every fix requires an explicit click on "Apply Fix" in Fix Center
- **Standard user for diagnostics** — Administrator elevation is opt-in, only when applying a fix
- **Confirm before applying any fix: always on** — this setting cannot be disabled
- SMB1 enable, Guest access, Firewall disable, and policy changes are deliberately not available as one-click fixes

## Requirements

| Requirement | Value |
|---|---|
| OS | Windows 10 (build 1903+) or Windows 11 |
| Architecture | 64-bit |
| Python | 3.11+ (only for running from source) |
| RAM | 256 MB |

## Installation

Download `FieldFix_IT_Setup_x.x.x.exe` from [Releases](../../releases) and run it.
No Python installation required — the installer includes everything.

## Running from source

```bash
git clone <repo-url>
cd FieldFix-IT
pip install -r requirements.txt
python -m app.main
```

## Running tests

```bash
python -m pytest tests/ -q
```

All 221 tests should pass.

## Architecture

```text
app/
├── core/           — Issue, RiskLevel, DecisionEngine, ScanSession, PowerShellRunner
├── modules/        — network/, smb/, firewall/, services/, printers/  (scanner + models)
├── gui/            — main_window, dashboard, pages/, widgets/, styles/
└── reports/        — Markdown / HTML / JSON report writers
```

The Decision Engine (`app/core/decision_engine.py`) is stateless — it receives
a `ScanReport` and returns a tuple of `Issue` objects, each with severity,
evidence, likely cause, recommended actions, and an optional `fix_id` that
links directly to the corresponding fix card in Fix Center.

## Known limitations (beta)

- Firewall profile status may show "Unknown" when running as a standard user — run as Administrator for complete data
- Network Topology ARP scan is limited to the local subnet; devices on other segments will not appear
- Printer IP reachability check uses ARP — printers on a different subnet fail this check even if the IP is routable
- Tested on a limited number of real-world configurations; edge cases exist

## License

MIT

## Credits

Created by **Radovan Stojanović**  
Built with the assistance of [Claude Code](https://claude.ai/code) and [Codex](https://openai.com/codex)
