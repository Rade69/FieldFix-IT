---
name: qthread-worker
description: "Use when replacing a blocking QApplication.processEvents() hack in PySide6 with a proper QThread background worker. Covers the Signal-based worker pattern, progress reporting, guard against double-run, and wiring to UI slots."
---

# QThread Worker — PySide6 background task pattern

## Kada koristiti

- UI freezuje dok se radi dugotrajna operacija (scan, I/O, mreža...)
- Koristiš `QApplication.processEvents()` kao hack da UI ostane živ
- Hoćeš da reportuješ napredak operacije u realnom vremenu
- Trebaš spriječiti da korisnik pokrene isti task dvaput

## Zašto NE koristiti `processEvents()`

`processEvents()` ne pokreće task u posebnoj niti — samo privremeno predaje kontrolu event loop-u. UI može djelovati "živim", ali aplikacija je i dalje blokirana. Svaka greška u task-u može zaključati cijelu aplikaciju.

## Pattern — korak po korak

### 1. Worker klasa

```python
from PySide6.QtCore import QThread, Signal

class _ScanWorker(QThread):
    progress = Signal(str)    # emituje string poruke tokom rada
    finished = Signal(object) # emituje rezultat kada završi

    def __init__(self, runner) -> None:
        super().__init__()
        self._runner = runner

    def run(self) -> None:
        # Ovo se izvršava u pozadinskoj niti — NE u UI niti!
        # Nikad ne direti UI widgete odavde — samo emitiraj signale.
        result = ScanSession(self._runner).run(
            on_progress=self.progress.emit
        )
        self.finished.emit(result)
```

### 2. Pokretanje iz UI widgeta

```python
class MyPage(QWidget):
    def _run_scan(self) -> None:
        # Guard: spriječi pokretanje dok prethodni task traje
        if hasattr(self, '_worker') and self._worker.isRunning():
            return

        self._worker = _ScanWorker(self._runner)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

        # Odmah ažuriraj UI da pokaže "in progress"
        self._status_label.setText('Scanning...')
        self._scan_btn.setEnabled(False)

    def _on_progress(self, message: str) -> None:
        # Poziva se u UI niti — sigurno je dirati widgete
        self._status_label.setText(message)

    def _on_finished(self, result: object) -> None:
        # Poziva se u UI niti kada worker završi
        self._scan_btn.setEnabled(True)
        self._display_results(result)
```

### 3. Progress reporting u long-running funkciji

```python
def run(self, on_progress=None) -> ScanResult:
    def _emit(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    _emit('Checking network...')
    network = self._scan_network()

    _emit('Checking printers...')
    printers = self._scan_printers()

    _emit('Done.')
    return ScanResult(network=network, printers=printers)
```

## Push model — scan jednom, podijeli svim stranicama

Ako više stranica prikazuje iste podatke, ne trebaju svaka skenirati posebno. Umjesto toga, Dashboard emituje custom Signal sa rezultatom i šalje ga svim stranicama:

```python
# dashboard.py
class DashboardPage(QWidget):
    scan_completed = Signal(object)  # emituje ScanResult

    def _on_finished(self, result) -> None:
        self.scan_completed.emit(result)  # sve zainteresovane stranice dobiju rezultat

# main_window.py
def _push_scan(result) -> None:
    if result.report.network:
        network_page.load_data(result.report.network, result.scanned_at)
    if result.report.printers:
        printers_page.load_data(result.report.printers, result.scanned_at)

dashboard.scan_completed.connect(_push_scan)
```

Svaka stranica implementira `load_data(data, scanned_at)` umjesto ponovnog skeniranja.

## Šta NE raditi u `run()` metodi workera

```python
def run(self) -> None:
    # ❌ Ne dirati UI widgete direktno iz worker niti
    self.some_label.setText('...')       # crash ili vizuelni glitch

    # ❌ Ne koristiti QApplication.processEvents()
    QApplication.processEvents()         # ništa ne pomaže u worker niti

    # ✅ Jedino komunicirati kroz signale
    self.progress.emit('Poruka...')
```

## Reference

- `app/gui/dashboard.py` — `_ScanWorker` i `_on_scan_finished` implementacija
- `app/gui/main_window.py` — `_push_scan` push model
- `app/core/scan_session.py` — `run(on_progress=...)` pattern
