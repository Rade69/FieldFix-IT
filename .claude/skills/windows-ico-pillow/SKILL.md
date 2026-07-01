---
name: windows-ico-pillow
description: "Use when generating a proper Windows .ico file with Pillow that includes all required sizes (16, 32, 48, 64, 128, 256). The 48x48 size is critical for the Windows taskbar — without it the taskbar shows a generic icon even if the app has an icon set."
---

# Windows ICO generisanje sa Pillowom

## Kada koristiti

- Kreiraš `.ico` fajl za Windows aplikaciju
- Taskbar pokazuje generičku ikonu umjesto ikone aplikacije
- Trebaju ti različite veličine iste ikone (za različite kontekste u Windowsu)

## Zašto je 48×48 kritično

Windows koristi različite veličine ikone u različitim kontekstima:

| Veličina | Gdje se koristi |
|----------|----------------|
| 16×16 | Title bar, mali pogledi u Exploreru |
| 32×32 | Standardni pogled u Exploreru |
| **48×48** | **Taskbar (obavezno — bez nje je generička ikona!)** |
| 64×64 | Veliki pogled u Exploreru |
| 128×128 | Extra-large pogled, Properties dijaloški |
| 256×256 | Extra-large na HiDPI, Store listinzi |

Bez 48×48 u `.ico` fajlu, Windows ne može naći odgovarajuću veličinu za taskbar i padne na generičku ikonu — čak i ako je `setWindowIcon()` pozvan ispravno u kodu.

## Kompletan kod

```python
from PIL import Image

def generate_ico(source_png: str, output_ico: str) -> None:
    """Generate a proper Windows .ico with all required sizes from a source PNG."""
    src = Image.open(source_png).convert('RGBA')
    
    src.save(
        output_ico,
        format='ICO',
        sizes=[
            (16, 16),
            (32, 32),
            (48, 48),   # ← kritično za taskbar
            (64, 64),
            (128, 128),
            (256, 256),
        ]
    )
    print(f'Saved: {output_ico}')

# Primjer
generate_ico('branding/logo_symbol.png', 'app/resources/icons/app_icon.ico')
```

## Verifikacija sadržaja ICO fajla

```python
from PIL import Image

ico = Image.open('app/resources/icons/app_icon.ico')
print(ico.info['sizes'])
# Očekivani output: [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
```

## Kreiranje ICO za installer (Inno Setup)

Za Inno Setup `SetupIconFile`, isti format radi:

```python
generate_ico('branding/logo_symbol.png', 'branding/installer_icon.ico')
```

## Kreiranje BMP za wizard images (Inno Setup)

Za `WizardImageFile` (portrait panel, Welcome/Finish stranice) — 164×314:

```python
from PIL import Image, ImageDraw, ImageFont

W, H = 164, 314
img = Image.new('RGBA', (W, H), '#0d1117')

logo = Image.open('branding/logo_symbol.png').convert('RGBA')
icon_size = 100
logo = logo.resize((icon_size, icon_size), Image.LANCZOS)
img.paste(logo, ((W - icon_size) // 2, 80), logo)

# Plava linija na dnu
draw = ImageDraw.Draw(img)
draw.rectangle([0, H - 3, W, H], fill='#1f6feb')

img.convert('RGB').save('branding/wizard_panel.bmp')
```

Za `WizardSmallImageFile` alternativno (64×64 logo ikona u IS6):

```python
W, H = 64, 64
img = Image.new('RGBA', (W, H), '#0d1117')
icon = Image.open('branding/logo_symbol.png').convert('RGBA')
icon = icon.resize((54, 54), Image.LANCZOS)
img.paste(icon, (5, 5), icon)
img.convert('RGB').save('branding/wizard_icon_64.bmp')
```

## Šta NE raditi

- **Ne konvertovati PNG → ICO direktno u Photoshopu/GIMP bez provjere veličina** — često propuste 48×48
- **Ne koristiti online ICO konvertore** — obično generišu samo 32×32 i 16×16
- **Ne pretpostavljati da `setWindowIcon(QIcon('app.ico'))` radi bez provjere sadržaja** — provjeri `ico.info['sizes']`

## Dijagnostika kada taskbar prikazuje generičku ikonu

```python
# Provjeri da .ico sadrži 48x48
from PIL import Image
ico = Image.open('app/resources/icons/app_icon.ico')
sizes = ico.info.get('sizes', [])
if (48, 48) not in sizes:
    print('PROBLEM: 48x48 nije u ico fajlu!')
    print('Dostupne veličine:', sizes)
```

## Reference

- `app/resources/icons/fieldfix_icon.ico` — radni primjer u ovom projektu
- `branding/wizard_panel.bmp` — portrait panel za Inno Setup
- `branding/installer_icon.ico` — ikona za Inno Setup SetupIconFile
- Skill `pyinstaller-pyside6` — kako includovati .ico u PyInstaller build
- Skill `inno-setup-classic-banner` — kompletni branding za Inno Setup installer
