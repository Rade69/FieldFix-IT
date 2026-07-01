# Skills — katalog vještina

Svaka vještina je skup gotovih obrazaca, ispravnih identifikatora i
upozorenja na česte greške, naučenih kroz stvarni rad na projektima.
Pozivaju se komandom `/naziv-vjestine` unutar Claude Code sesije.

---

## Inno Setup 6

### `/inno-setup-classic-banner`
**Kada:** Dodaješ full-width branding banner na unutrašnje stranice instalera
(Select Destination, Select Tasks...) i `WizardSmallImageFile` se sabija u mali ugao.

**Šta rješava:** Ispravna hijerarhija IS6 WizardForm kontrola (`MainPanel`,
`InnerNotebook`, `PageNameLabel`, `PageDescriptionLabel`) i TBitmapImage overlay
pattern koji radi u IS6 6.6.1 classic stilu.

**Naučeno na:** FieldFix IT installer, 2026-07-01
`agent_reports/2026-07-01_installer-header-banner.md`

---

## Python / Windows desktop

### `/pyinstaller-pyside6`
**Kada:** Pakuješ PySide6 (Qt6) Python aplikaciju u Windows `.exe` sa PyInstallerom.

**Šta rješava:** Ispravan `.spec` template, obavezni `hiddenimports` za PySide6
(`QtSvg`, `QtSvgWidgets`, `QtNetwork`, `QtXml`), `_base()` pattern za putanje
resursa kroz `sys._MEIPASS`, `CREATE_NO_WINDOW` za subprocess, i zašto
`upx=False` + `uac_admin=False`.

**Naučeno na:** FieldFix IT build, 2026-07-01

---

### `/qthread-worker`
**Kada:** UI freezuje tokom dugotrajne operacije ili koristiš `processEvents()` hack.

**Šta rješava:** `_Worker(QThread)` klasa sa `Signal(str)` za progress i
`Signal(object)` za rezultat, guard protiv dvostrukog pokretanja, push model
za dijeljenje scan rezultata između stranica bez ponovnog skeniranja.

**Naučeno na:** FieldFix IT Dashboard scan, 2026-07-01

---

### `/uac-elevation-python`
**Kada:** Python/PySide6 Windows app treba da se restart-uje sa admin privilegijama.

**Šta rješava:** `is_admin()` provjera, `restart_as_admin()` koji radi za **oba**
slučaja — PyInstaller frozen `.exe` i dev mode `python -m app.main` (ne
`python app/main.py` — to lomi relative imports).

**Naučeno na:** FieldFix IT Fix Center, 2026-07-01

---

### `/windows-ico-pillow`
**Kada:** Generišeš Windows `.ico` fajl i taskbar prikazuje generičku ikonu.

**Šta rješava:** Pillow kod koji uključuje svih 6 veličina (16, 32, **48**, 64,
128, 256). Veličina 48×48 je kritična — bez nje Windows taskbar ne može naći
odgovarajuću veličinu i padne na generičku ikonu čak i kada je `setWindowIcon()`
ispravno pozvan.

**Naučeno na:** FieldFix IT taskbar ikona, 2026-07-01

---

## GitNexus — Code Intelligence

*(Vidi `.claude/skills/gitnexus/` — set od 6 vještina za navigaciju i analizu codebase-a)*

| Vještina | Kada |
|----------|------|
| `/gitnexus-exploring` | Razumjeti arhitekturu, "Kako radi X?" |
| `/gitnexus-impact-analysis` | "Šta se lomi ako promijenem X?" |
| `/gitnexus-debugging` | Tražiti uzrok buga kroz execution flow |
| `/gitnexus-refactoring` | Sigurno preimenovati/refaktorisati |
| `/gitnexus-guide` | Pregled alata i schema |
| `/gitnexus-cli` | CLI komande (analyze, status, clean) |

---

*Novi skills se dodaju ovdje odmah po kreiranju SKILL.md fajla.*
