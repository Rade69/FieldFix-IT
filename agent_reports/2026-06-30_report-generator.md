# Agent report: Report Generator (Faza 9)

## Datum
2026-06-30

## Scope
- `app/reports/__init__.py` (novo)
- `app/reports/models.py` (novo)
- `app/reports/json_report.py` (novo)
- `app/reports/markdown_report.py` (novo)
- `app/reports/html_report.py` (novo)
- `app/gui/pages/reports_page.py` (update — stub → funkcionalna stranica)
- `tests/reports/__init__.py` (novo)
- `tests/reports/test_report_writers.py` (novo)

## GitNexus impact (provjera prije izmjene)
- `ReportsPage`: LOW (1 direktni — main_window.py, očekivano)
- Novi modul — nema izmjena na postojećim simbolima

## Šta je urađeno

### `app/reports/models.py`

`ScanReport` frozen dataclass — agregat svih scan rezultata:

```python
ScanReport(
    generated_at: str,       # ISO 8601
    hostname: str,
    network: NetworkData | None,
    smb: SmbData | None,
    smb_target_ip: str,
    services: ServicesData | None,
    printers: PrintersData | None,
)
```

`None` sekcija = "nije skenirana" — report writeri to prikazuju eksplicitno.

### `app/reports/json_report.py`

`write_json(report) → str` — koristi `dataclasses.asdict()` (rekurzivno
konvertuje nested dataclasse, tuple → list) + `json.dumps(indent=2)`.
`default=str` kao safety net za nepredviđene tipove.

### `app/reports/markdown_report.py`

`write_markdown(report) → str` — sekcije: Network (adapteri, IP, gateway,
DNS, profili), SMB (server/client config, shareovi, port 445, net view),
Services (tabela sa statusima), Printers (tabela sa default markerom).

Logika boja u tekstu: ✓ / ✕ / ● prefiksi, "Disabled (good)" za SMB1=False.
"Not scanned" poruka za None sekcije.

### `app/reports/html_report.py`

`write_html(report) → str` — self-contained HTML (inline CSS, bez vanjskih
zavisnosti). CSS klase: `.ok` (zeleno), `.err` (crveno), `.warn` (narandžasto),
`.muted` (sivo). HTML escape za sve vrijednosti (XSS-safe).

### `app/gui/pages/reports_page.py`

- Checkboxovi: Network / SMB / Services / Printers (sve checked by default)
- SMB target IP polje (opcionalno)
- Format radio: JSON / Markdown / HTML (Markdown default)
- "▶ Generate & Preview" — pokreće scan odabranih sekcija sekvencijalno,
  prikazuje status ("Scanning Network…" itd.) između poziva
- `QPlainTextEdit` preview (monospace, dark theme)
- "💾 Save to File" — `QFileDialog.getSaveFileName()`, UTF-8 write

## Šta nije dirano
- Odluke (recommendations) nisu implementirane — to je Faza 10 (Decision Engine)
- Nijedna Windows postavka nije promijenjena
- Ostali moduli i stranice — netaknuti

## Verifikacija
```
170 passed in 1.12s
```
(30 novih testova — 10 JSON, 12 Markdown, 12 HTML)

## Rizici / ograničenja

- **Bez Decision Engine-a**: report sada nema sekciju "Recommendations" ni
  risk-level badge-ove — to dodaje Faza 10. Format `ScanReport` je dizajniran
  da prima `recommendations: tuple | None` kao proširenje kad DE bude spreman.
- **Sinhroni scan**: isti problem kao ostale stranice — threading V2
- **HTML preview**: prikazuje se kao plain text (HTML source), ne renderirani
  HTML. Za renderirani preview trebalo bi koristiti `QTextBrowser` — razmotriti
  u V2

## Potreban follow-up
- Faza 10 — Decision Engine v1 (dodaje Issue listu i Recommendations u ScanReport)
- Faza 11 — Dashboard v2 (pravi podaci)
