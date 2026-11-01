"""Landscape-first metrics layout. Solid dark canvas — no wallpaper branding."""
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

from . import ASSETS

WHITE, DIM, CYAN = (235, 235, 235), (150, 160, 170), (90, 200, 255)
GREEN, YELLOW, RED, TRACK = (80, 220, 120), (250, 210, 60), (255, 80, 80), (55, 58, 64)
# Flat backgrounds by alert level (no PNG wallpaper / no upstream branding).
BG = {
    0: (12, 14, 18),
    1: (28, 22, 10),
    2: (32, 12, 12),
}
PANEL = (22, 24, 30)
LEVEL_NAMES = ("normal", "warn", "error")


@lru_cache(maxsize=None)
def font(size: float, bold=False):
    name = "JetBrainsMono-Bold.ttf" if bold else "JetBrainsMono-Regular.ttf"
    return ImageFont.truetype(str(ASSETS / "fonts" / name), round(size))


def fmt_rate(b) -> str:
    if b is None:
        return "-"
    if b < 1024 * 1000:
        return f"{b / 1024:.0f}k"
    m = b / 1048576
    return f"{m:.1f}m" if m < 10 else f"{m:.0f}m"


def fmt_uptime(s: float) -> str:
    if s >= 86400:
        return f"{s // 86400:.0f}d"
    return f"{s // 3600:.0f}h" if s >= 3600 else f"{s // 60:.0f}m"


def fmt_freq(mhz) -> str:
    if not mhz:
        return "-"
    return f"{mhz / 1000:.2f}G" if mhz >= 1000 else f"{mhz:.0f}M"


def pick(v, limits, ok=GREEN):
    if v is None:
        return DIM
    return RED if v >= limits[1] else YELLOW if v >= limits[0] else ok


def pct(v) -> str:
    if v is None:
        return "-"
    return f"{v * 100:.0f}"


class Frame:
    def __init__(self, host, snap, probes: dict, level: int):
        self.host, self.snap, self.probes, self.level = host, snap, probes, level


class Canvas:
    def __init__(self, level: int, size: tuple, s: int):
        self.s = s
        w, h = size[0] * s, size[1] * s
        self.img = Image.new("RGBA", (w, h), BG.get(level, BG[0]) + (255,))
        self.d = ImageDraw.Draw(self.img)

    def _xy(self, *v):
        return [round(x * self.s) for x in v]

    def panel(self, box):
        self.d.rounded_rectangle(self._xy(*box), 4 * self.s, fill=PANEL + (255,))

    def text(self, xy, txt, size, fill, bold=False, anchor=None):
        self.d.text(self._xy(*xy), txt, font=font(size * self.s, bold), fill=fill, anchor=anchor)

    def rect(self, box, fill):
        self.d.rectangle(self._xy(*box), fill=fill)

    def arc(self, box, start, end, fill, width):
        self.d.arc(self._xy(*box), start, end, fill=fill, width=round(width * self.s))


class Renderer:
    def __init__(self, cfg: dict, scale: int = 1):
        self.cfg = cfg
        self.scale = scale
        self.th = cfg["thresholds"]
        self.orientation = cfg["screen"]["orientation"]
        self.disk_label = cfg["screen"].get("disk_label", "DSK")

    @staticmethod
    def _bar(c, x, y, w, v, color, h=7):
        c.rect((x, y, x + w, y + h), TRACK)
        if v is None or v <= 0:
            return
        # Minimum 3px fill so low values (cluster ~5%) stay visible on the TFT.
        fill_w = max(3, round(w * min(v, 1)))
        c.rect((x, y, x + fill_w, y + h), color)

    @staticmethod
    def _ring(c, cx, cy, r, frac, color, value: str, label: str):
        box = (cx - r, cy - r, cx + r, cy + r)
        c.arc(box, 135, 405, TRACK, 5)
        if frac and frac > 0:
            # Minimum sweep so a non-zero reading never looks empty.
            sweep = max(8, 270 * min(frac, 1))
            c.arc(box, 135, 135 + sweep, color, 5)
        c.text((cx, cy - 1), value, 12, WHITE, bold=True, anchor="mm")
        c.text((cx, cy + r - 3), label, 9, DIM, anchor="mm")

    def _host_rings(self, c, f: Frame, centers, r):
        h, th = f.host, self.th
        items = [
            (h.cpu, pick(h.cpu, th["cpu"]), pct(h.cpu), "CPU"),
            (h.mem, pick(h.mem, th["mem"]), pct(h.mem), "MEM"),
            (h.swap, pick(h.swap, th["swap"]), pct(h.swap), "SWP"),
            (
                (h.temp or 0) / 100,
                pick(h.temp, th["temp"]),
                f"{h.temp:.0f}" if h.temp else "-",
                "°C",
            ),
        ]
        for (cx, cy), (frac, color, value, label) in zip(centers, items):
            self._ring(c, cx, cy, r, frac, color, value, label)

    def landscape(self, f: Frame):
        W, H = 320, 170
        c = Canvas(f.level, (W, H), self.scale)
        # Full bleed — no top strip reserved for wallpaper text.
        c.panel((2, 2, 148, H - 3))
        c.panel((151, 2, W - 3, H - 3))
        h, s, th = f.host, f.snap, self.th

        c.text((6, 6), h.name[:12], 12, CYAN, bold=True)
        c.text((144, 8), fmt_uptime(h.uptime), 10, DIM, anchor="ra")
        self._host_rings(c, f, [(38, 52), (110, 52), (38, 108), (110, 108)], 20)

        c.text((6, 138), f"{h.power:.1f}W" if h.power else "-", 11, WHITE)
        c.text((58, 138), fmt_freq(h.freq_mhz), 11, WHITE)
        c.text((144, 138), f"↓{fmt_rate(h.rx)}↑{fmt_rate(h.tx)}", 10, WHITE, anchor="ra")
        c.text((6, 154), f"ld {h.load1:.2f}", 10, DIM)

        c.text((158, 6), "CLUSTER", 10, DIM, bold=True)
        if s.error:
            c.text((158, 28), "K8S API", 12, RED, bold=True)
            for i, chunk in enumerate([s.error[j : j + 24] for j in range(0, min(len(s.error), 72), 24)]):
                c.text((158, 46 + i * 14), chunk, 10, RED)
            return c.img

        nodes_color = GREEN if s.nodes_ready == s.nodes_total else RED
        c.text((158, 24), f"nodes {s.nodes_ready}/{s.nodes_total}", 13, nodes_color, bold=True)

        fail_color = RED if s.pods_failed else GREEN
        pend_color = YELLOW if s.pods_pending else DIM
        c.text((158, 44), f"run {s.pods_running}", 12, WHITE)
        c.text((230, 44), f"pend {s.pods_pending}", 12, pend_color)
        c.text((158, 60), f"fail {s.pods_failed}", 12, fail_color)

        # Host CPU as a bar too — cluster fraction is often ~5% and looked "empty"/0.
        c.text((158, 84), "cpu", 10, DIM)
        self._bar(c, 186, 86, 120, h.cpu, pick(h.cpu, th["cpu"], CYAN))
        c.text((310, 84), f"{pct(h.cpu)}%", 10, WHITE, anchor="ra")

        c.text((158, 104), "cmem", 10, DIM)
        self._bar(c, 186, 106, 120, s.mem_usage, pick(s.mem_usage, th["cluster_mem"]))
        c.text((310, 104), f"{pct(s.mem_usage)}%", 10, WHITE, anchor="ra")

        c.text((158, 124), self.disk_label[:4].lower(), 10, DIM)
        self._bar(c, 186, 126, 120, h.disk, pick(h.disk, th["disk"], CYAN))
        c.text((310, 124), f"{pct(h.disk)}%", 10, WHITE, anchor="ra")

        c.text((158, 144), "ccpu", 10, DIM)
        self._bar(c, 186, 146, 120, s.cpu_usage, pick(s.cpu_usage, th["cluster_cpu"], CYAN))
        c.text((310, 144), f"{pct(s.cpu_usage)}%", 10, WHITE, anchor="ra")
        return c.img

    def portrait(self, f: Frame):
        W, H = 170, 320
        c = Canvas(f.level, (W, H), self.scale)
        c.panel((2, 2, W - 3, 150))
        c.panel((2, 154, W - 3, H - 3))
        h, s = f.host, f.snap
        c.text((6, 6), h.name[:10], 12, CYAN, bold=True)
        c.text((W - 6, 8), fmt_uptime(h.uptime), 10, DIM, anchor="ra")
        self._host_rings(c, f, [(28, 55), (85, 55), (142, 55), (85, 110)], 20)
        c.text((6, 138), f"{h.power:.1f}W {fmt_freq(h.freq_mhz)}" if h.power else fmt_freq(h.freq_mhz), 11, WHITE)
        c.text((W - 6, 138), f"↓{fmt_rate(h.rx)} ↑{fmt_rate(h.tx)}", 10, WHITE, anchor="ra")
        c.text((6, 158), "CLUSTER", 10, DIM, bold=True)
        if s.error:
            c.text((6, 178), s.error[:40], 10, RED)
        else:
            c.text(
                (6, 178),
                f"nodes {s.nodes_ready}/{s.nodes_total}",
                13,
                GREEN if s.nodes_ready == s.nodes_total else RED,
                bold=True,
            )
            c.text((6, 200), f"run {s.pods_running}  pend {s.pods_pending}  fail {s.pods_failed}", 11, WHITE)
            c.text((6, 222), f"cpu {pct(h.cpu)}%  ccpu {pct(s.cpu_usage)}%", 11, WHITE)
            c.text((6, 244), f"disk {pct(h.disk)}%  swap {pct(h.swap)}%", 11, WHITE)
            c.text((6, 266), f"load {h.load1:.2f}", 11, DIM)
        return c.img

    def render(self, f: Frame):
        if self.orientation == "portrait":
            img = self.portrait(f).convert("RGB")
            return img, img.rotate(90, expand=True)
        img = self.landscape(f).convert("RGB")
        return img, img


def black():
    return Image.new("RGB", (320, 170), (0, 0, 0))
