# Agent report — Initial skeleton (Zadatak 1)

Datum: 2026-06-29

## Šta je urađeno

- PySide6 UI shell: `app/main.py`, `app/gui/main_window.py`, `app/gui/sidebar.py`.
- 10 stranica (Dashboard, Network, Sharing/SMB, Firewall, Services,
  Printers, Topology, Reports, Settings, About) kao placeholder widgeti u
  `app/gui/pages/`.
- Dashboard placeholder (`app/gui/dashboard.py`) sa dummy status karticama
  i RiskBadge preview-om — statički podaci, bez realnog skeniranja.
- Reusable widgeti: `StatusCard`, `RiskBadge` (display-only, bez logike
  za procjenu rizika).
- `docs/architecture_notes.md` — zapisane odluke: modularni monolit (ne
  plugin system u MVP-u), JSON-first PowerShell, UAC/elevacija per-akcija,
  Dashboard "Review Fix" tok, i **Opcija A** za `confidence_rules` u
  knowledge fajlovima (čisto dokumentaciono polje, nikad se ne parsira/
  izvršava — stvarna logika ide u `decision_engine.py`, Faza 10).
- `docs/future_modules_backlog.md` — lista budućih modula van MVP-a.
- `docs/target_gui.md` — referenca na mockup (`asset/GUI-FieldFix IT.png`)
  kao v3 cilj, sa napomenom o odstupanjima (risk badge, Review Fix).
- `AGENTS.md` — mapa workflow-a, lightweight verzija (bez agent_skills/,
  agent_loops/, project_rooms/ za sada).
- `agent_runbooks/high_critical_code_change.md`.
- `README.md`, `pyproject.toml`, `requirements.txt`, `.gitignore`.
- `tests/test_app_shell.py` — smoke testovi (main window se gradi, sidebar
  i stack imaju isti broj stranica, Dashboard je prva stranica).
- Git repo inicijalizovan (`git init`), bez commit-a.

## Verifikacija

- `python -m pytest tests/` → 2 passed.
- Ručno pokrenut `MainWindow()` kroz `QApplication` → bez greške, 10
  sidebar stavki = 10 stacked stranica.

## Šta NIJE urađeno (granice po planu)

- Plugin manager / formalni plugin interfejs.
- Core modeli (CommandResult, Issue, Recommendation, RiskLevel, ScanStatus)
  — Zadatak 2.
- PowerShellRunner — Zadatak 3.
- Bilo kakva prava PowerShell komanda ili promjena Windows podešavanja.
- Decision engine, topology engine, knowledge base sadržaj.
- Installer.

## Šta provjeriti prije sljedećeg zadatka

- Zadatak 2 (core modeli) ne smije dirati GUI osim minimalno potrebnog.
- Kad se počne sa Zadatkom 3 (PowerShellRunner) i Zadatkom 5 (SMB +
  knowledge YAML), pridržavati se odluke o `confidence_rules` iz
  `docs/architecture_notes.md` — ne uvoditi `eval()` ili sličan pristup.
