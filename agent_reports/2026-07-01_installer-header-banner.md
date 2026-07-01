# Agent report: Installer header banner

## Datum

2026-07-01

## Scope

- `installer.iss`
- `branding/wizard_classic_banner.bmp`
- `branding/wizard_icon_64.bmp`
- `branding/wizard_panel.bmp`

## GitNexus impact

`detect_changes(scope="unstaged")` za installer promjenu prijavljuje LOW rizik
i nema zahvacenih execution flow procesa. `installer.iss` je indeksiran kao
samostalan fajl bez poziva u Python aplikaciji.

## Sta je uradjeno

- Zadrzan je `WizardStyle=classic` i postojeci branding assets za installer.
- Dodan je `branding\wizard_classic_banner.bmp` kao `dontcopy` asset.
- Dodan je Inno Setup `[Code]` blok koji kreira vlastiti `TBitmapImage`
  header banner i prikazuje ga samo na unutrasnjim wizard stranicama.
- Banner je vezan na `WizardForm.MainPanel`, ne direktno na `WizardForm`,
  jer ga u suprotnom Inno paneli mogu prekriti na unutrasnjim stranicama.
- Header panel je povecan, default naslov/opis su pomjereni ispod bannera, a
  `InnerNotebook` je spusten da sadrzaj stranice ne preklapa header.
- Rjesenje ne koristi `WizardForm.SmallBitmapImage` niti druge interne kontrole
  koje su ranije davale `Unknown identifier`.

## Kako je napravljeno

1. `installer.iss` je prebacen sa starog `WizardSmallImageFile` PNG pristupa
   na branding BMP fajlove koje Inno Setup sigurno ucitava:
   `WizardImageFile=branding\wizard_panel.bmp` i
   `WizardSmallImageFile=branding\wizard_icon_64.bmp`.
2. Horizontalni banner je dodat kao `dontcopy` fajl:
   `Source: "branding\wizard_classic_banner.bmp"; Flags: dontcopy`.
   Tokom instalacije se izvlaci u temp folder kroz
   `ExtractTemporaryFile('wizard_classic_banner.bmp')`.
3. U `[Code]` sekciji se kreira nova kontrola:
   `HeaderBanner := TBitmapImage.Create(WizardForm)`.
   Kontrola se vezuje na `WizardForm.MainPanel`, jer je to stvarni header
   panel unutrasnjih Inno stranica.
4. Banner se ucitava kroz
   `HeaderBanner.Bitmap.LoadFromFile(ExpandConstant('{tmp}\wizard_classic_banner.bmp'))`.
   Koristi `Stretch := True` i zauzima gornji dio header panela.
5. `UpdateHeaderBanner()` prikazuje banner samo na unutrasnjim stranicama.
   Welcome, Preparing, Installing i Finished stranice ostaju na standardnom
   Inno layoutu.
6. Da tekst ne bude preko slike, `MainPanel` je povecan, `PageNameLabel` i
   `PageDescriptionLabel` su pomjereni ispod bannera, a `InnerNotebook` je
   spusten nize da sadrzaj forme pocinje ispod novog headera.

## Sta nije dirano

- Nisu mijenjani install path, privilegije, UAC, uninstall logika ili app files.
- Nije mijenjan PyInstaller build.
- Nisu mijenjane Windows postavke tokom testiranja.
- Nije uveden drugi installer alat.

## Verifikacija

- Provjeren je diff `installer.iss`.
- Inno Setup 6.6.1 compiler je pokrenut preko
  `C:\Progra~2\INNOSE~1\ISCC.exe installer.iss`.
- Compile je uspjesno zavrsio i generisao
  `installer_output\FieldFix_IT_Setup_0.1.0.exe`.
- Nakon rucne provjere korisnika, banner se nije vidio na unutrasnjim
  stranicama. Popravka: `HeaderBanner.Parent` promijenjen sa `WizardForm` na
  `WizardForm.MainPanel`; zatim je installer ponovo uspjesno kompajliran.
- Nakon druge rucne provjere korisnika, naslov/opis su bili preko bannera.
  Popravka: banner ogranicen na gornji dio `MainPanel`-a, naslov/opis
  pomjereni ispod slike, `InnerNotebook` pomjeren nize; installer ponovo
  uspjesno kompajliran.

## Rizici / ogranicenja

- Vizuelno pozicioniranje zavisi od Inno classic wizard layouta.
- Potrebna je rucna vizuelna provjera pokretanjem setup-a da se potvrdi tacan
  izgled na `Select Destination`, `Select Tasks` i slicnim stranicama.
