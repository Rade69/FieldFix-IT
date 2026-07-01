"""Active subnet scanner — ping sweep + port probe + device identification.

Runs entirely via PowerShell (.NET async) and is read-only (no changes made).
Typical scan time for a /24 subnet: 4-8 seconds.
"""
from __future__ import annotations

import html
import re
import time
import urllib.request
from dataclasses import replace as _dc_replace
from typing import Callable

from app.core.powershell_runner import PowerShellRunner
from app.modules.network.models import DiscoveredDevice

_TITLE_RE  = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
# Prefixes stripped from Canon/HP/Ricoh web UIs before the actual model name
_UI_NOISE  = re.compile(
    r"^(remote\s*ui\s*:?\s*|login\s*:?\s*|top\s*page\s*:?\s*|web\s*image\s*monitor\s*:?\s*)+",
    re.IGNORECASE,
)


def _clean_title(raw: str) -> str:
    """Strip HTML entities, UI boilerplate, and duplicate segments."""
    text = html.unescape(raw).replace("\xa0", " ")
    # Remove leading boilerplate (e.g. "Remote UI: Login: ")
    text = _UI_NOISE.sub("", text).strip()
    # If the title repeats itself ("MF440 series: MF440 series"), keep first half
    parts = [p.strip() for p in text.split(":") if p.strip()]
    if len(parts) >= 2 and parts[0].lower() == parts[-1].lower():
        text = parts[0]
    elif parts:
        text = parts[0]
    return text.strip()


def _fetch_http_title(ip: str, timeout: float = 2.5) -> str:
    """GET http://{ip}/ and return the cleaned <title> text, or '' on failure."""
    try:
        req = urllib.request.Request(
            f"http://{ip}/",
            headers={"User-Agent": "FieldFix-IT/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read(4096).decode("utf-8", errors="replace")
        m = _TITLE_RE.search(data)
        if m:
            cleaned = _clean_title(m.group(1))
            return cleaned if cleaned else ""
    except Exception:
        pass
    return ""

# Ports used to identify device types
_PRINTER_PORTS = (9100, 515, 631)   # RAW, LPD, IPP
_PC_PORTS      = (445,)              # SMB
_WEB_PORTS     = (80, 443)

# Hostname substrings that suggest a printer even without open ports
_PRINTER_BRANDS = (
    "canon", "epson", "hp", "hewlett", "brother", "ricoh",
    "kyocera", "xerox", "lexmark", "konica", "minolta", "sharp",
    "oki", "panasonic", "toshiba", "samsung", "develop",
)

# PowerShell: async ping sweep → ARP → async DNS → async port probe → JSON
_PS_SCAN = r"""
$ErrorActionPreference = 'SilentlyContinue'

# ── 1. Local network info ────────────────────────────────────────────────────
$ni = Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and
                   $_.PrefixOrigin -ne 'WellKnown' } |
    Sort-Object PrefixLength | Select-Object -First 1
if (-not $ni) { '[]'; exit }

$localIP = $ni.IPAddress
$octets  = $localIP -split '\.'
$base    = "$($octets[0]).$($octets[1]).$($octets[2])"

# ── 2. Async ping sweep (all 254 at once, 1200ms timeout) ───────────────────
$pings = @{}
1..254 | ForEach-Object {
    $ip = "$base.$_"
    $p  = New-Object System.Net.NetworkInformation.Ping
    $pings[$ip] = @{ Obj = $p; Task = $p.SendPingAsync($ip, 1200) }
}
$allPingTasks = @($pings.Values | ForEach-Object { $_.Task })
[System.Threading.Tasks.Task]::WaitAll($allPingTasks, 2500) | Out-Null

$alive = $pings.Keys | Where-Object {
    $t = $pings[$_].Task
    $t.IsCompleted -and ($t.Status -eq 'RanToCompletion') -and
    $t.Result.Status -eq 'Success' -and $_ -ne $localIP
}
$pings.Values | ForEach-Object { try { $_.Obj.Dispose() } catch {} }

# ── 3. ARP table (populated by pings) ───────────────────────────────────────
$arp = @{}
Get-NetNeighbor -AddressFamily IPv4 |
    Where-Object { $_.LinkLayerAddress -ne '00-00-00-00-00-00' } |
    ForEach-Object { $arp[$_.IPAddress] = $_.LinkLayerAddress }

# ── 4. Async DNS resolution for all alive hosts ──────────────────────────────
$dnsTasks = @{}
foreach ($ip in $alive) {
    $dnsTasks[$ip] = [System.Net.Dns]::GetHostEntryAsync($ip)
}
$allDnsTasks = @($dnsTasks.Values)
if ($allDnsTasks.Count -gt 0) {
    [System.Threading.Tasks.Task]::WaitAll($allDnsTasks, 3000) | Out-Null
}
$hostnames = @{}
foreach ($ip in $alive) {
    $t = $dnsTasks[$ip]
    if ($t.IsCompleted -and $t.Status -eq 'RanToCompletion') {
        $hostnames[$ip] = $t.Result.HostName
    } else { $hostnames[$ip] = "" }
}

# ── 5. Async TCP port probe (9100, 445, 80) on all alive hosts at once ───────
$probeTargets = @(9100, 445, 80)
$tcpTasks = [System.Collections.Generic.List[hashtable]]::new()
foreach ($ip in $alive) {
    foreach ($port in $probeTargets) {
        $tcp  = New-Object System.Net.Sockets.TcpClient
        $task = $tcp.ConnectAsync($ip, $port)
        $tcpTasks.Add(@{ IP = $ip; Port = $port; Task = $task; Client = $tcp })
    }
}
$allTcpTasks = @($tcpTasks | ForEach-Object { $_.Task })
if ($allTcpTasks.Count -gt 0) {
    [System.Threading.Tasks.Task]::WaitAll($allTcpTasks, 1500) | Out-Null
}
$openPorts = @{}
foreach ($entry in $tcpTasks) {
    $t = $entry.Task
    if ($t.IsCompleted -and $t.Status -eq 'RanToCompletion') {
        if (-not $openPorts.ContainsKey($entry.IP)) { $openPorts[$entry.IP] = @() }
        $openPorts[$entry.IP] += $entry.Port
    }
    try { $entry.Client.Dispose() } catch {}
}

# ── 6. Build result ──────────────────────────────────────────────────────────
$printerBrands = @('canon','epson','hp','hewlett','brother','ricoh',
                   'kyocera','xerox','lexmark','konica','sharp','oki')

$results = foreach ($ip in $alive) {
    $ports    = if ($openPorts.ContainsKey($ip)) { $openPorts[$ip] } else { @() }
    $name     = if ($hostnames.ContainsKey($ip)) { $hostnames[$ip] } else { "" }
    $nameLo   = $name.ToLower()

    $byPrinterPort  = ($ports | Where-Object { $_ -in @(9100,515,631) }).Count -gt 0
    $byPrinterName  = ($printerBrands | Where-Object { $nameLo -like "*$_*" }).Count -gt 0
    $bySMB          = 445 -in $ports
    $byWeb          = 80  -in $ports

    $type = 'unknown'
    $conf = 'LOW'
    $by   = 'ping'
    if ($byPrinterPort) { $type = 'printer'; $conf = 'HIGH';   $by = 'port 9100/515/631' }
    elseif ($byPrinterName) { $type = 'printer'; $conf = 'MEDIUM'; $by = 'hostname pattern' }
    elseif ($bySMB)     { $type = 'pc';      $conf = 'MEDIUM'; $by = 'SMB port 445' }
    elseif ($byWeb)     { $type = 'web_device'; $conf = 'LOW'; $by = 'HTTP port 80' }

    [PSCustomObject]@{
        ip         = $ip
        mac        = if ($arp.ContainsKey($ip)) { $arp[$ip] } else { "" }
        hostname   = $name
        type       = $type
        open_ports = ($ports -join ",")
        confidence = $conf
        detected_by = $by
    }
}

if ($null -eq $results) { '[]' }
else { @($results) | ConvertTo-Json -Compress }
"""


def _parse_ports(raw: str) -> tuple[int, ...]:
    if not raw:
        return ()
    try:
        return tuple(int(p) for p in raw.split(",") if p.strip())
    except ValueError:
        return ()


class SubnetScanner:
    """Active /24 subnet scanner — read-only, no system changes."""

    def __init__(self, runner: PowerShellRunner) -> None:
        self._runner = runner

    def scan(
        self,
        on_progress: Callable[[str], None] | None = None,
    ) -> list[DiscoveredDevice]:
        start = time.monotonic()

        def _prog(msg: str) -> None:
            if on_progress:
                on_progress(msg)

        _prog("Sending ping sweep…")
        result = self._runner.run_json(_PS_SCAN, timeout=60)

        if not result.succeeded or result.parsed_json is None:
            return []

        raw = result.parsed_json
        if isinstance(raw, dict):
            raw = [raw]
        if not isinstance(raw, list):
            return []

        devices: list[DiscoveredDevice] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            ip = str(item.get("ip", "") or "")
            if not ip:
                continue

            # Hostname heuristic: if empty but printer brand in IP label → keep
            hostname = str(item.get("hostname", "") or "")
            device_type = str(item.get("type", "unknown") or "unknown")

            # Extra brand check on hostname in Python (belt-and-suspenders)
            if device_type == "unknown" and hostname:
                name_lo = hostname.lower()
                if any(b in name_lo for b in _PRINTER_BRANDS):
                    device_type = "printer"

            devices.append(DiscoveredDevice(
                ip_address=ip,
                mac_address=str(item.get("mac", "") or ""),
                hostname=hostname,
                device_type=device_type,
                open_ports=_parse_ports(str(item.get("open_ports", "") or "")),
                confidence=str(item.get("confidence", "LOW") or "LOW"),
                detected_by=str(item.get("detected_by", "ping") or "ping"),
            ))

        # HTTP title enrichment for printers without a resolved hostname
        printers_no_name = [
            (i, d) for i, d in enumerate(devices)
            if d.device_type == "printer" and not d.hostname and 80 in d.open_ports
        ]
        if printers_no_name:
            _prog(f"Resolving printer names via HTTP ({len(printers_no_name)})…")
            for i, dev in printers_no_name:
                title = _fetch_http_title(dev.ip_address)
                if title:
                    devices[i] = _dc_replace(dev, hostname=title)

        elapsed = time.monotonic() - start
        _prog(f"Scan complete — {len(devices)} host(s) in {elapsed:.1f}s")
        return devices
