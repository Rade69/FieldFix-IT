# Target GUI (v3 cilj, ne v1 build target)

Referenca: `asset/GUI-FieldFix IT.png`

Ovaj mockup prikazuje **krajnji cilj** dashboard dizajna (otprilike nivo
Faza 9-12 iz plana), ne ono što se gradi u Fazi 1 (skeleton). Sadrži:

- gornji status header (Computer / IP / User / Network / Scan Mode),
- status kartice (Network, Sharing/SMB, Firewall, Services, Printers, Issues),
- System & Network Info panel,
- Recent Scan Summary,
- Network Topology panel (lanac: ovaj računar → gateway → target → printer),
- Activity Timeline,
- Issues & Recommendations panel,
- Decision Assistant (Smart Diagnose) sa korak-po-korak ikonicama,
- Quick Actions / Fix Center.

## Poznata odstupanja od mockupa koja moramo primijeniti kad dođemo do tih faza

- Quick Actions na mockupu imaju direktno `Apply` dugme bez vidljivog risk
  badge-a. Stvarna implementacija mora: (1) prikazati risk badge uz svaku
  akciju, i (2) `Apply` zamijeniti sa `Review Fix` koji vodi u Fix Center
  (vidi `docs/architecture_notes.md`, sekcija "Dashboard: Review Fix, ne
  Apply").
- Topology, Decision Assistant i Timeline se ne implementiraju prije Faze
  9-12 — ne dodavati ih u skeleton ili rane module.

## Faza 1 vizuelni stil (primijenjeno, proširено)

Korisnik je tražio da skeleton vizuelno liči na mockup. Prvi korak: samo
tema i stil (`app/gui/theme.py` dark stylesheet, status header bar,
stilizovane status kartice).

Nakon pregleda, korisnik je odlučio da se ide dalje — kompletan vizuelni
izgled sa mokapa se gradi **panel po panel** (Topology → Timeline →
Issues/Quick Actions → Decision Assistant), i dalje samo vizuelno sa
dummy podacima, **bez stvarne logike iza dugmadi/skeniranja**. Ovo svjesno
ide ispred originalnog faznog redosljeda (Faza 9-12) — vizuelni shell se
pravi ranije, stvarno wiring (skeniranje, fix akcije, decision engine)
ostaje gdje je plan predvidio. Svaki panel se pravi i pregleda pojedinačno
prije sljedećeg.
