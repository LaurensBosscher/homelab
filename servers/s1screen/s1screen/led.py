"""Front LED strip: CH340 USB serial (1a86:7523) on an internal USB port, 10000 baud.

Packet: FA <mode> <brightness> <speed> <checksum>, sent one byte at a time.
Brightness/speed are 1-5 for the user; the wire value is inverted (6 - level).
"""
import glob
import logging
import os
import time

log = logging.getLogger(__name__)

MODES = {"rainbow": 0x01, "breathing": 0x02, "cycle": 0x03, "off": 0x04, "auto": 0x05}
BAUD = 10000


def led_packet(mode: str, brightness: int = 3, speed: int = 3) -> bytes:
    if mode not in MODES:
        raise ValueError(f"unknown LED mode {mode!r}, use one of {', '.join(MODES)}")
    wire = lambda v: min(5, max(1, 6 - int(v)))
    body = [0xFA, MODES[mode], wire(brightness), wire(speed)]
    return bytes(body + [sum(body) & 0xFF])


def _read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ""


def ch340_ports():
    """[(tty path, usb port name, fixed?)] for CH340 adapters visible on the host."""
    found = []
    for tty in sorted(glob.glob("/sys/bus/usb-serial/devices/ttyUSB*")):
        intf = os.path.dirname(os.path.realpath(tty))        # .../1-4/1-4:1.0
        usb = os.path.dirname(intf)                          # .../1-4
        if (_read(f"{usb}/idVendor"), _read(f"{usb}/idProduct")) != ("1a86", "7523"):
            continue
        fixed = _read(f"{usb}/removable") == "fixed"
        found.append(("/dev/" + os.path.basename(tty), os.path.basename(usb), fixed))
    return found


def resolve_port(port: str):
    """'auto' = fixed CH340 if unique, else the sole CH340 when only one is present."""
    if port and port != "auto":
        return port if os.path.exists(port) else None
    ports = ch340_ports()
    internal = [p for p in ports if p[2]]
    if len(internal) == 1:
        return internal[0][0]
    if len(ports) == 1:
        return ports[0][0]
    return None



def usage_preset(value: float | None) -> dict:
    """Map a 0..1 load fraction onto mode/brightness/speed.

    The Holtek LED MCU only exposes themes (no arbitrary RGB), so we encode
    pressure as: calm breathing -> colour cycle -> rainbow, plus brighter/faster.
    """
    v = 0.0 if value is None else max(0.0, min(1.0, float(value)))
    brightness = 1 + round(v * 4)  # 1..5
    speed = 1 + round(v * 4)       # 1..5
    if v >= 0.90:
        mode = "rainbow"
    elif v >= 0.70:
        mode = "cycle"
    else:
        mode = "breathing"
    return {"mode": mode, "brightness": brightness, "speed": speed}


class Led:
    def __init__(self, port: str):
        self.port = resolve_port(port)
        self.current = None
        if self.port is None:
            log.warning("LED controller not found (port=%s). If the internal CH340 is passed "
                        "through to a VM, the host cannot drive the LED strip.", port)

    def apply(self, preset: dict, force=False):
        if self.port is None:
            return
        key = (preset.get("mode", "off"), preset.get("brightness", 3), preset.get("speed", 3))
        if key == self.current and not force:
            return
        try:
            send(self.port, *key)
            prev_mode = self.current[0] if self.current else None
            self.current = key
            if key[0] != prev_mode:
                log.info("LED -> %s brightness=%s speed=%s", *key)
            else:
                log.debug("LED -> %s brightness=%s speed=%s", *key)
        except Exception as e:  # noqa: BLE001 - LED is cosmetic, never stop the screen for it
            log.warning("LED write failed on %s: %s", self.port, e)


def send(port: str, mode: str, brightness: int = 3, speed: int = 3):
    import serial  # python3-serial; imported lazily so preview works without it

    pkt = led_packet(mode, brightness, speed)
    with serial.Serial(port, BAUD, timeout=1) as s:
        for b in pkt:
            s.write(bytes([b]))
            s.flush()
            time.sleep(0.005)
