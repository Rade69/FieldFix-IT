---
name: inno-setup-classic-banner
description: "Use when adding a custom full-width branding banner to Inno Setup 6 installer inner wizard pages. Covers the correct WizardForm property names (MainPanel, InnerNotebook, PageNameLabel, PageDescriptionLabel) and the TBitmapImage overlay pattern that actually works in IS6 6.6.1 classic style."
---

# Inno Setup 6 — Custom Header Banner (Classic Style)

## Kada koristiti

- Dodaješ branding banner na unutrašnje stranice instalera (Select Destination, Select Tasks, Ready to Install...)
- `WizardSmallImageFile` je premali i sabijen u gornji desni ugao
- Pokušavaš manipulisati IS6 wizard formom iz Pascal `[Code]` sekcije

## Ključno znanje (ne gubi vrijeme na ovo ponovo)

**`WizardForm.SmallBitmapImage` ne postoji** u IS6 6.6.1 — ni u `modern` ni u `classic` stilu. Ovo je razlog grešaka tipa `Unknown identifier 'SMALLBITMAPIMAGE'`.

Prava hijerarhija kontrola u IS6 **classic** stilu:

```
WizardForm
├── MainPanel          ← header panel (sadrži banner + labele)
│   ├── PageNameLabel
│   └── PageDescriptionLabel
├── InnerNotebook      ← sadržaj svake wizard stranice
├── Bevel              ← separator linija ispod headera
└── BackButton / NextButton / CancelButton
```

## Rješenje — korak po korak

### 1. Pripremi BMP banner

Preporučena veličina: **497×58 px** (puna širina IS6 classic wizarda).
Format: BMP (PNG radi u IS6 ali BMP je pouzdaniji).

```python
# Pillow primjer
from PIL import Image, ImageDraw, ImageFont

W, H = 497, 58
img = Image.new('RGBA', (W, H), '#0d1117')
# ... logo, tekst ...
img.convert('RGB').save('branding/wizard_classic_banner.bmp')
```

### 2. Dodaj u [Setup] sekciju

```ini
[Setup]
WizardStyle=classic
WizardImageFile=branding\wizard_panel.bmp
; NE stavljaj WizardSmallImageFile — banner dodajemo ručno u [Code]
```

### 3. Dodaj u [Files] sekciju

```ini
[Files]
; dontcopy = embeddovan u installer, ne instalira se, ExtractTemporaryFile ga izvlači
Source: "branding\wizard_classic_banner.bmp"; Flags: dontcopy
```

### 4. [Code] sekcija — kompletan radni primjer

```pascal
[Code]
var
  HeaderBanner: TBitmapImage;

function IsInnerWizardPage(PageID: Integer): Boolean;
begin
  Result :=
    (PageID <> wpWelcome) and
    (PageID <> wpPreparing) and
    (PageID <> wpInstalling) and
    (PageID <> wpFinished);
end;

procedure UpdateHeaderBanner(PageID: Integer);
begin
  if HeaderBanner = nil then Exit;
  HeaderBanner.Visible := IsInnerWizardPage(PageID);
  if HeaderBanner.Visible then
    HeaderBanner.BringToFront;
end;

procedure InitializeWizard;
begin
  ExtractTemporaryFile('wizard_classic_banner.bmp');

  // Proširi header panel da stane banner + labele ispod njega
  WizardForm.MainPanel.Height := ScaleY(128);

  // Pomjeri sadržajni notebook i podesi mu visinu
  WizardForm.InnerNotebook.Top :=
    WizardForm.MainPanel.Top + WizardForm.MainPanel.Height;
  WizardForm.InnerNotebook.Height :=
    WizardForm.Bevel.Top - WizardForm.InnerNotebook.Top;

  // Kreiraj TBitmapImage i zakači ga na MainPanel (NE na WizardForm!)
  HeaderBanner := TBitmapImage.Create(WizardForm);
  HeaderBanner.Parent  := WizardForm.MainPanel;   // ← ovo je ključno
  HeaderBanner.AutoSize := False;
  HeaderBanner.Stretch  := True;
  HeaderBanner.SetBounds(0, 0, WizardForm.MainPanel.Width, ScaleY(72));
  HeaderBanner.Bitmap.LoadFromFile(
    ExpandConstant('{tmp}\wizard_classic_banner.bmp'));
  HeaderBanner.Visible := False;

  // Pomjeri PageNameLabel i PageDescriptionLabel ispod bannera
  WizardForm.PageNameLabel.Left  := ScaleX(24);
  WizardForm.PageNameLabel.Top   := ScaleY(78);
  WizardForm.PageNameLabel.Width := WizardForm.MainPanel.Width - ScaleX(48);
  WizardForm.PageDescriptionLabel.Left  := ScaleX(24);
  WizardForm.PageDescriptionLabel.Top   := ScaleY(101);
  WizardForm.PageDescriptionLabel.Width := WizardForm.MainPanel.Width - ScaleX(48);
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  UpdateHeaderBanner(CurPageID);
end;
```

## Česte greške

| Greška | Uzrok | Rješenje |
|--------|-------|----------|
| `Unknown identifier 'SMALLBITMAPIMAGE'` | `SmallBitmapImage` ne postoji u IS6 | Koristi `MainPanel` + `TBitmapImage.Create` |
| Banner se ne vidi | `Parent := WizardForm` umjesto `MainPanel` | Promijeni parent na `WizardForm.MainPanel` |
| Tekst stranice prekriva banner | `PageNameLabel.Top` nije pomjeren | Postavi `Top := ScaleY(78)` i sl. |
| Sadržaj stranice ide ispod headera | `InnerNotebook` nije pomjeren | Podesi `InnerNotebook.Top` i `Height` |
| Kompajler greška `Unknown identifier 'PAGEDESCRIPTIONLABEL'` | Pokušavaš u `modern` stilu | Provjeri da je `WizardStyle=classic` |

## Testiranje

```
ISCC.exe installer.iss
```

Pokrenuti dobijeni `.exe` i ručno proći kroz:
- Welcome stranicu (banner NE smije biti vidljiv)
- Select Destination (banner MORA biti vidljiv, cijele širine)
- Select Tasks (banner vidljiv)
- Ready to Install (banner vidljiv)
- Finished stranicu (banner NE smije biti vidljiv)

## Reference

- `agent_reports/2026-07-01_installer-header-banner.md` — izvještaj koji opisuje kako je rješenje pronađeno
- `installer.iss` — radni primjer u ovom projektu
- `branding/wizard_classic_banner.bmp` — banner koji se koristi (497×58)
