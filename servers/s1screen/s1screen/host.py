"""Local host sensors: CPU, mem, swap, temp, RAPL power, freq, NIC, disk fill."""
import time
from dataclasses import dataclass
from pathlib import Path

import psutil

RAPL = "/sys/class/powercap/intel-rapl:0"


@dataclass
class HostStats:
    name: str
    cpu: float
    mem: float
    swap: float
    temp: float | None
    power: float | None  # watts
    freq_mhz: float | None
    rx: float | None  # bytes/s
    tx: float | None
    disk: float | None  # used fraction of configured path
    load1: float
    uptime: float


def _read_int(path):
    try:
        with open(path) as f:
            return int(f.read())
    except (OSError, ValueError):
        return None


def cpu_temp():
    try:
        sensors = psutil.sensors_temperatures()
    except (AttributeError, OSError):
        return None
    for chip, label in (("coretemp", "Package id 0"), ("k10temp", "Tctl"), ("zenpower", "Tdie")):
        for e in sensors.get(chip, []):
            if e.label == label:
                return e.current
    temps = [e.current for es in sensors.values() for e in es if e.current]
    return max(temps) if temps else None


def cpu_freq_mhz():
    try:
        f = psutil.cpu_freq()
        if f and f.current:
            return f.current
    except (AttributeError, OSError):
        pass
    khz = _read_int("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
    return khz / 1000 if khz else None


def disk_used(path: str) -> float | None:
    if not path:
        return None
    try:
        u = psutil.disk_usage(path)
        return u.percent / 100
    except OSError:
        return None


class HostMonitor:
    def __init__(self, iface: str, disk_path: str = ""):
        import socket

        self.name = socket.gethostname().split(".")[0]
        self.iface = iface
        self.disk_path = disk_path
        self._energy = None  # (uj, t)
        self._net = None  # (rx, tx, t)
        self._rapl_max = _read_int(f"{RAPL}/max_energy_range_uj")
        # Blocking prime so the first painted frame is not a spurious 0%.
        psutil.cpu_percent(0.15)

    def _power(self, now):
        uj = _read_int(f"{RAPL}/energy_uj")
        if uj is None:
            return None
        prev, self._energy = self._energy, (uj, now)
        if not prev or now <= prev[1]:
            return None
        delta = uj - prev[0]
        if delta < 0 and self._rapl_max:
            delta += self._rapl_max
        return delta / 1e6 / (now - prev[1])

    def _netspeed(self, now):
        c = psutil.net_io_counters(pernic=True).get(self.iface)
        if c is None:
            return None, None
        prev, self._net = self._net, (c.bytes_recv, c.bytes_sent, now)
        if not prev or now <= prev[2]:
            return None, None
        dt = now - prev[2]
        return max(0, c.bytes_recv - prev[0]) / dt, max(0, c.bytes_sent - prev[1]) / dt

    def sample(self) -> HostStats:
        now = time.monotonic()
        rx, tx = self._netspeed(now)
        swap = psutil.swap_memory()
        return HostStats(
            name=self.name,
            cpu=psutil.cpu_percent(None) / 100,
            mem=psutil.virtual_memory().percent / 100,
            swap=(swap.percent / 100) if swap.total else 0.0,
            temp=cpu_temp(),
            power=self._power(now),
            freq_mhz=cpu_freq_mhz(),
            rx=rx,
            tx=tx,
            disk=disk_used(self.disk_path),
            load1=psutil.getloadavg()[0],
            uptime=time.time() - psutil.boot_time(),
        )
