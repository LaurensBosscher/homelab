"""Command line. Ansible owns install on Bazzite; these helpers are for ops/debug."""
import argparse
import importlib
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import ROOT, __version__, config

SERVICE = "s1screen"
UNIT_PATH = Path(f"/etc/systemd/system/{SERVICE}.service")
DEPS = {"PIL": "python3-pillow", "numpy": "python3-numpy", "psutil": "python3-psutil",
        "requests": "python3-requests", "serial": "python3-pyserial"}


def sh(*cmd, check=False, capture=False):
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )


def need_root():
    if os.name != "posix" or os.geteuid() != 0:
        sys.exit("Please run as root")


def service_state() -> str:
    if not shutil.which("systemctl"):
        return "n/a"
    if not UNIT_PATH.exists():
        return "not installed"
    return sh("systemctl", "is-active", SERVICE, capture=True).stdout.strip()


def missing_deps():
    out = []
    for mod, pkg in DEPS.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            out.append(pkg)
    return out


def cmd_run(args):
    from .app import App

    if sys.stdin.isatty() and service_state() == "active":
        sys.exit(f"{SERVICE}.service is running; stop it first")
    App(config.load(args.config)).run()


def demo_frame(cfg):
    from .app import evaluate
    from .host import HostStats
    from .k8s import Snapshot
    from .render import Frame

    host = HostStats("bazzite", 0.23, 0.41, 0.05, 48, 7.8, 2400, 1.4e6, 180e3, 0.69, 0.73, 18 * 86400)
    snap = Snapshot(
        nodes_ready=4,
        nodes_total=4,
        pods_running=47,
        pods_pending=0,
        pods_failed=0,
        cpu_usage=0.18,
        mem_usage=0.32,
    )
    return Frame(host, snap, {}, evaluate(cfg, host, snap))


def cmd_preview(args):
    from .render import Renderer

    cfg = config.load(args.config)
    if args.orientation:
        cfg["screen"]["orientation"] = args.orientation
    if args.demo:
        frame = demo_frame(cfg)
    else:
        from .app import Collector

        collector = Collector(cfg)
        collector.frame(probes={})
        time.sleep(1.5)
        frame = collector.frame(probes={})
    # Force active rendering for previews even outside the evening window.
    img, _ = Renderer(cfg, scale=max(1, args.scale)).render(frame)
    img.save(args.output)
    print(f"saved {args.output}")


def cmd_check(args):
    from . import lcd, led

    path = Path(args.config)
    print(f"s1screen {__version__}")
    try:
        cfg = config.load(path)
        print(f"[ok]   config {path}" + ("" if path.exists() else " (example defaults)"))
    except Exception as e:  # noqa: BLE001
        print(f"[FAIL] config {path}: {e}")
        return
    deps = missing_deps()
    print("[ok]   python packages" if not deps else f"[FAIL] missing: {', '.join(deps)}")
    print(f"[info] service: {service_state()}")
    dev = lcd.find_device()
    print(f"[ok]   screen {dev[0]} ep 0x{dev[1]:02x}" if dev else "[FAIL] screen (USB 04d9:fd01) not found")
    if cfg["led"]["enabled"]:
        port = led.resolve_port(cfg["led"]["port"])
        print(f"[ok]   LED {port}" if port else f"[warn] LED port not found (port={cfg['led']['port']})")
    else:
        print("[info] LED disabled")
    for tty, usb, fixed in led.ch340_ports():
        print(f"         CH340 {tty} usb {usb} {'internal' if fixed else 'external'}")
    if deps:
        return
    from .k8s import K8sClient

    try:
        snap = K8sClient(cfg).snapshot()
        print(
            f"[ok]   k8s: nodes {snap.nodes_ready}/{snap.nodes_total}, "
            f"pods run={snap.pods_running} pend={snap.pods_pending} fail={snap.pods_failed}, "
            f"cpu={(snap.cpu_usage or 0)*100:.0f}% mem={(snap.mem_usage or 0)*100:.0f}%"
        )
    except Exception as e:  # noqa: BLE001
        print(f"[FAIL] k8s: {e}")


def cmd_restart(args):
    need_root()
    sh("systemctl", "restart", SERVICE)
    print(service_state())


def cmd_status(args):
    sh("systemctl", "status", SERVICE, "--no-pager", "-n", "20")


def cmd_led(args):
    from . import led

    cfg = config.load(args.config)
    port = led.resolve_port(args.port or cfg["led"]["port"])
    if not port:
        sys.exit("LED port not found")
    preset = cfg["led"].get(args.mode)
    if preset:
        mode, b, s = preset.get("mode", "off"), preset.get("brightness", 3), preset.get("speed", 3)
    else:
        mode, b, s = args.mode, args.brightness, args.speed
    led.send(port, mode, b, s)
    print(f"{port}: {mode} brightness={b} speed={s}")


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    p = argparse.ArgumentParser(prog="s1screen.py", description="SZBox/AceMagic S1 panel — host + Kubernetes metrics")
    p.add_argument("-c", "--config", default=str(config.DEFAULT), help="config file")
    p.add_argument("-V", "--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("run", help="run the screen loop").set_defaults(func=cmd_run)
    sp = sub.add_parser("preview", help="render one frame to a PNG")
    sp.add_argument("-o", "--output", default="preview.png")
    sp.add_argument("--demo", action="store_true")
    sp.add_argument("--orientation", choices=("portrait", "landscape"))
    sp.add_argument("--scale", type=int, default=2)
    sp.set_defaults(func=cmd_preview)
    sub.add_parser("check", help="check config, USB devices and Kubernetes").set_defaults(func=cmd_check)
    sub.add_parser("restart", help="restart the service").set_defaults(func=cmd_restart)
    sub.add_parser("status", help="service status").set_defaults(func=cmd_status)
    sp = sub.add_parser("led", help="set the LED strip")
    sp.add_argument("mode")
    sp.add_argument("brightness", nargs="?", type=int, default=3)
    sp.add_argument("speed", nargs="?", type=int, default=3)
    sp.add_argument("--port")
    sp.set_defaults(func=cmd_led)

    args = p.parse_args(argv)
    if not args.cmd:
        p.print_help()
        return 2
    return args.func(args)
