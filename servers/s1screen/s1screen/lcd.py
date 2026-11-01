"""Front TFT: USB 04d9:fd01, interface 1, 320x170 RGB565 (big-endian).

Without a ~1s heartbeat (55 A1 F2 HH MM SS) the Holtek firmware falls back to its
built-in page: "Disconnection, content information display will not be allowed!".

Full A3 redraws leave the panel busy/~NAKing for ~6.5s, which blocks heartbeats.
We therefore paint with A2 partial strips (no long busy window) and keep a
background heartbeat thread alive.
"""
from __future__ import annotations

import ctypes
import glob
import logging
import os
import struct
import threading
import time
from datetime import datetime

import numpy as np

try:
    import fcntl
except ImportError:  # Windows: preview/tests only
    fcntl = None

log = logging.getLogger(__name__)

VID, PID, INTERFACE = 0x04D9, 0xFD01, 1
WIDTH, HEIGHT = 320, 170
PACKET_SIZE = 4104
CHUNK = 4096
# Full-frame writes may need to wait out the post-A3 busy window.
TIMEOUT_LONG_MS = 10000
# Heartbeat / partials should fail fast if the panel is momentarily busy.
TIMEOUT_SHORT_MS = 800
HEARTBEAT_INTERVAL = 1.0
# Max pixels per A2 refresh (firmware limit).
PARTIAL_MAX_PIXELS = 2048
# A2 width/height are uint8 (max 255). Tile so w*h <= 2048.
TILE_W = 160
TILE_H = 12  # 160*12 = 1920


def rgb565(img) -> bytes:
    """PIL image (320x170) -> big-endian RGB565 bytes."""
    a = np.asarray(img.convert("RGB"), dtype=np.uint16)
    v = ((a[..., 0] & 0xF8) << 8) | ((a[..., 1] & 0xFC) << 3) | (a[..., 2] >> 3)
    return v.astype(">u2").tobytes()


def rgb565_array(img) -> np.ndarray:
    a = np.asarray(img.convert("RGB"), dtype=np.uint16)
    v = ((a[..., 0] & 0xF8) << 8) | ((a[..., 1] & 0xFC) << 3) | (a[..., 2] >> 3)
    return v.astype(">u2")


def frame_packets(data: bytes) -> list:
    """Full-frame A3 packets (used once at startup)."""
    count = (len(data) + CHUNK - 1) // CHUNK
    packets = []
    for i in range(count):
        chunk = data[i * CHUNK : (i + 1) * CHUNK]
        kind = 0xF0 if i == 0 else 0xF2 if i == count - 1 else 0xF1
        header = bytes([0x55, 0xA3, kind, i + 1]) + struct.pack("<HH", (i * CHUNK) & 0xFFFF, len(chunk))
        packets.append((header + chunk).ljust(PACKET_SIZE, b"\x00"))
    return packets


def command_packet(*payload: int) -> bytes:
    return bytes(payload).ljust(PACKET_SIZE, b"\x00")


def partial_packet(x: int, y: int, w: int, h: int, pixels: bytes) -> bytes:
    """A2 region update. pixels = w*h big-endian RGB565."""
    if w * h > PARTIAL_MAX_PIXELS:
        raise ValueError(f"partial too large: {w}x{h}")
    header = bytes([0x55, 0xA2]) + struct.pack("<HHBB", x, y, w, h)
    return (header + pixels).ljust(PACKET_SIZE, b"\x00")


def heartbeat_packet(now: datetime | None = None) -> bytes:
    now = now or datetime.now()
    return command_packet(0x55, 0xA1, 0xF2, now.hour, now.minute, now.second, 0, 0)


def orientation_packet(landscape: bool = True) -> bytes:
    return command_packet(0x55, 0xA1, 0xF1, 0x01 if landscape else 0x02, 0, 0, 0, 0)


# ---- usbfs -----------------------------------------------------------------
class _BulkTransfer(ctypes.Structure):
    _fields_ = [
        ("ep", ctypes.c_uint),
        ("len", ctypes.c_uint),
        ("timeout", ctypes.c_uint),
        ("data", ctypes.c_void_p),
    ]


def _ioc(direction, nr, size):
    return (direction << 30) | (size << 16) | (ord("U") << 8) | nr


USBDEVFS_BULK = _ioc(3, 2, ctypes.sizeof(_BulkTransfer))
USBDEVFS_CLAIMINTERFACE = _ioc(2, 15, ctypes.sizeof(ctypes.c_uint))
USBDEVFS_RELEASEINTERFACE = _ioc(2, 16, ctypes.sizeof(ctypes.c_uint))


def _read(path):
    with open(path) as f:
        return f.read().strip()


def find_device():
    """-> (/dev/bus/usb/BBB/DDD, OUT endpoint address) or None."""
    for dev in glob.glob("/sys/bus/usb/devices/*"):
        try:
            if (int(_read(f"{dev}/idVendor"), 16), int(_read(f"{dev}/idProduct"), 16)) != (VID, PID):
                continue
            node = f"/dev/bus/usb/{int(_read(f'{dev}/busnum')):03d}/{int(_read(f'{dev}/devnum')):03d}"
        except (OSError, ValueError):
            continue
        for ep in glob.glob(f"{dev}/*:1.{INTERFACE}/ep_*"):
            if _read(f"{ep}/direction") == "out":
                return node, int(_read(f"{ep}/bEndpointAddress"), 16)
    return None


class Lcd:
    def __init__(self):
        self.fd = None
        self.ep = None
        self.lock = threading.RLock()
        self._hb_stop = threading.Event()
        self._hb_thread = None
        self._last_hb = 0.0
        self._hb_fail_logged = False

    def open(self):
        found = find_device()
        if not found:
            raise RuntimeError("S1 screen (USB 04d9:fd01) not found")
        node, self.ep = found
        self.fd = os.open(node, os.O_RDWR)
        try:
            fcntl.ioctl(self.fd, USBDEVFS_CLAIMINTERFACE, struct.pack("I", INTERFACE))
        except OSError as e:
            os.close(self.fd)
            self.fd = None
            raise RuntimeError(
                f"cannot claim the screen ({e}); is another program "
                "(e.g. the old core.bin) still running?"
            ) from e
        log.info("screen opened at %s interface %d ep 0x%02x", node, INTERFACE, self.ep)
        # Orientation alone shows the firmware "Disconnection…" page; cover it ASAP.
        self.set_orientation(landscape=True)
        self.heartbeat()
        self._start_heartbeat()

    def _write(self, pkt: bytes, timeout_ms: int = TIMEOUT_LONG_MS):
        buf = ctypes.create_string_buffer(pkt, len(pkt))
        xfer = _BulkTransfer(self.ep, len(pkt), timeout_ms, ctypes.cast(buf, ctypes.c_void_p))
        fcntl.ioctl(self.fd, USBDEVFS_BULK, xfer)

    def set_orientation(self, landscape: bool = True):
        with self.lock:
            self._write(orientation_packet(landscape), TIMEOUT_SHORT_MS)

    def heartbeat(self) -> bool:
        """Keep-alive so firmware does not flip back to the Disconnection page."""
        try:
            with self.lock:
                self._write(heartbeat_packet(), TIMEOUT_SHORT_MS)
            self._last_hb = time.monotonic()
            self._hb_fail_logged = False
            return True
        except OSError as e:
            if not self._hb_fail_logged:
                log.debug("heartbeat deferred: %s", e)
                self._hb_fail_logged = True
            return False

    def _maybe_heartbeat(self):
        if time.monotonic() - self._last_hb >= HEARTBEAT_INTERVAL:
            self.heartbeat()

    def _start_heartbeat(self):
        if self._hb_thread and self._hb_thread.is_alive():
            return

        def loop():
            while not self._hb_stop.wait(HEARTBEAT_INTERVAL):
                if self.fd is None:
                    continue
                self.heartbeat()

        self._hb_stop.clear()
        self._hb_thread = threading.Thread(target=loop, name="s1-heartbeat", daemon=True)
        self._hb_thread.start()

    def draw_full(self, img):
        """Legacy A3 full-frame redraw (leaves panel busy ~6.5s)."""
        packets = frame_packets(rgb565(img))
        with self.lock:
            for i, pkt in enumerate(packets):
                self._write(pkt, TIMEOUT_LONG_MS)
                if i and i % 5 == 0:
                    # Opportunistic keep-alive between chunks.
                    try:
                        self._write(heartbeat_packet(), TIMEOUT_SHORT_MS)
                        self._last_hb = time.monotonic()
                    except OSError:
                        pass

    def draw(self, img):
        """Paint via A2 tiles so the heartbeat thread can keep the session alive."""
        pixels = rgb565_array(img)  # shape (170, 320), dtype >u2
        if pixels.shape != (HEIGHT, WIDTH):
            raise ValueError(f"expected {HEIGHT}x{WIDTH}, got {pixels.shape}")
        with self.lock:
            y = 0
            while y < HEIGHT:
                h = min(TILE_H, HEIGHT - y)
                x = 0
                while x < WIDTH:
                    w = min(TILE_W, WIDTH - x)
                    tile = pixels[y : y + h, x : x + w].tobytes()
                    self._write(partial_packet(x, y, w, h, tile), TIMEOUT_SHORT_MS)
                    x += w
                    self._maybe_heartbeat()
                y += h

    def close(self):
        self._hb_stop.set()
        if self._hb_thread:
            self._hb_thread.join(timeout=2)
            self._hb_thread = None
        if self.fd is not None:
            try:
                fcntl.ioctl(self.fd, USBDEVFS_RELEASEINTERFACE, struct.pack("I", INTERFACE))
            finally:
                os.close(self.fd)
                self.fd = None
