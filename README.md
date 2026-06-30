# FieldFix IT

Windows desktop alat za terensku IT dijagnostiku i kontrolisano rješavanje
problema u malim firmama (mreža, SMB/sharing, firewall, servisi, štampači).

```text
Scan → Evidence → Decision → Recommendation → Controlled Fix → Report
```

## Arhitektura

FieldFix IT koristi **Modular Layered Architecture** koja kombinuje Diagnostics
Pipeline, Rule-Based Decision Engine i Knowledge-Driven Architecture.
Aplikacija razdvaja prikupljanje podataka, analizu, preporuke i interakciju s
korisnikom u nezavisne slojeve, što je čini sigurnom, održivom i lako
proširivom.

```text
Core Engine
      │
      ├── Scanner Engine   — app/modules/*/scanner.py  (Network, SMB, Services, Printers, Firewall)
      ├── Decision Engine  — app/core/decision_engine.py
      ├── Report Engine    — app/reports/
      ├── Fix Engine       — app/gui/fix_center/  (Faza 13)
      └── (Recommendation Engine je dio Decision Engine-a)
```

Moduli (`Network`, `SMB`, `Firewall`, `Printers`, `Services`) su **izvori
podataka** za zajedničke engine-e — ne centralni akteri. Koordinacija više
skenera (`ScanSession`) uvodi se u Fazi 11 (Dashboard v2) kao dio `app/core/`.

Plan razvoja: `FieldFix_IT_integrisani_plan_v2.md`.
Status: Faze 1–9 završene (UI, Network, SMB, Services, Printers, Reports).

## Pokretanje

```bash
pip install -r requirements.txt
python -m app.main
```

## Razvojni vodič za agente

Vidi `AGENTS.md`.
