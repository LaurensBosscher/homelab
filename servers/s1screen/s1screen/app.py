"""Main loop: collect -> evaluate -> render -> send."""
import logging
import time
from datetime import datetime, time as dtime

from .host import HostMonitor
from .k8s import K8sClient, Snapshot
from .lcd import Lcd
from .led import Led, usage_preset
from .probe import Prober
from .render import Frame, Renderer, black

log = logging.getLogger(__name__)


def _hm(s: str) -> dtime:
    h, m = s.split(":")
    return dtime(int(h), int(m))


def in_window(now: dtime, start: str, end: str) -> bool:
    a, b = _hm(start), _hm(end)
    if a == b:
        return False
    return a <= now < b if a < b else now >= a or now < b


def evaluate(cfg: dict, host, snap: Snapshot) -> int:
    """0 normal, 1 warn, 2 error -> background + LED preset."""
    th = cfg["thresholds"]
    values = [
        (host.cpu, th["cpu"]),
        (host.mem, th["mem"]),
        (host.swap, th["swap"]),
        (host.temp, th["temp"]),
        (host.disk, th["disk"]),
        (snap.cpu_usage, th["cluster_cpu"]),
        (snap.mem_usage, th["cluster_mem"]),
    ]
    level = 0
    for v, (warn, crit) in values:
        if v is None:
            continue
        if v >= crit:
            return 2
        if v >= warn:
            level = 1
    if snap.nodes_ready < snap.nodes_total:
        return 2
    if snap.error or snap.pods_failed:
        level = max(level, 1 if snap.pods_failed else 2)
        if snap.error:
            level = max(level, 1)
    if snap.pods_pending:
        level = max(level, 1)
    return level


class Collector:
    def __init__(self, cfg: dict, prober=None):
        self.cfg = cfg
        self.k8s = K8sClient(cfg)
        self.host = HostMonitor(cfg["screen"]["net_iface"], cfg["screen"].get("disk_path", ""))
        self.prober = prober
        self._last_error = None

    def _snapshot(self) -> Snapshot:
        try:
            snap = self.k8s.snapshot()
            if self._last_error:
                log.info("Kubernetes API back to normal")
            self._last_error = None
            return snap
        except Exception as e:  # noqa: BLE001
            msg = str(e).strip()
            if msg != self._last_error:
                log.error("Kubernetes API: %s", msg)
            self._last_error = msg
            return Snapshot(error=msg)

    def frame(self, probes=None):
        host = self.host.sample()
        snap = self._snapshot()
        if probes is None:
            probes = dict(self.prober.results) if self.prober else {}
        return Frame(host, snap, probes, evaluate(self.cfg, host, snap))


class App:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.lcd = Lcd()
        self.led = Led(cfg["led"]["port"]) if cfg["led"]["enabled"] else None
        self.renderer = Renderer(cfg)
        self.prober = Prober(cfg) if cfg["probe"]["enabled"] else None
        self.collector = Collector(cfg, self.prober)


    def _led_preset(self, led_cfg: dict, f) -> dict:
        """Usage meter when configured; otherwise warn/error/normal presets."""
        meter = (led_cfg.get("meter") or "off").lower()
        if f.level >= 2:
            return led_cfg.get("error", {"mode": "rainbow", "brightness": 5, "speed": 5})
        if f.level >= 1 and meter == "off":
            return led_cfg.get("warn", {"mode": "breathing", "brightness": 4, "speed": 3})

        h = f.host
        if meter == "cpu":
            value = h.cpu
        elif meter == "mem":
            value = h.mem
        elif meter == "max":
            value = max(h.cpu or 0.0, h.mem or 0.0)
        else:
            return led_cfg[("normal", "warn", "error")[f.level]]

        preset = usage_preset(value)
        if f.level >= 1:
            preset["speed"] = min(5, max(preset["speed"], 4))
            if preset["mode"] == "breathing":
                preset["mode"] = "cycle"
        return preset

    def _draw(self, img):
        try:
            self.lcd.draw(img)
            self._draw_errors = 0
        except OSError as e:
            self._draw_errors = getattr(self, "_draw_errors", 0) + 1
            log.warning("frame write failed (%d in a row): %s", self._draw_errors, e)
            if self._draw_errors >= 10:
                raise

    def _active(self) -> bool:
        """True inside weekday evening or weekend daytime windows."""
        act = self.cfg.get("active", {})
        if not act.get("enabled", False):
            return True
        now = datetime.now()
        # Mon-Fri = 0..4, Sat-Sun = 5..6
        if now.weekday() >= 5:
            start = act.get("weekend_start", act["start"])
            end = act.get("weekend_end", act["end"])
        else:
            start, end = act["start"], act["end"]
        return in_window(now.time(), start, end)

    def run(self):
        self.lcd.open()
        if self.prober:
            self.prober.start()
        led_cfg = self.cfg["led"]
        refresh = float(self.cfg["screen"]["refresh"])
        was_idle = None
        while True:
            started = time.monotonic()
            active = self._active()
            if not active:
                self._draw(black())
                if was_idle is not True:
                    log.info("outside active hours — blanking panel")
                    if self.led:
                        self.led.apply(led_cfg.get("idle", led_cfg.get("night", {"mode": "off"})))
                    if self.prober:
                        self.prober.paused.set()
            else:
                if was_idle:
                    log.info("active hours — resuming metrics")
                    if self.prober:
                        self.prober.paused.clear()
                f = self.collector.frame()
                _, device_img = self.renderer.render(f)
                self._draw(device_img)
                if self.led:
                    self.led.apply(self._led_preset(led_cfg, f))
            was_idle = not active
            time.sleep(max(0.5, refresh - (time.monotonic() - started)))
