"""config.toml loading. Missing keys fall back to config.example.toml."""
import copy
import os
import re
import shutil
import tomllib
from pathlib import Path

from . import ROOT

EXAMPLE = ROOT / "config.example.toml"
DEFAULT = ROOT / "config.toml"


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def ensure(path: Path = DEFAULT) -> Path:
    """Create config.toml from the example on first use (mode 600, it may hold a token)."""
    path = Path(path)
    if not path.exists():
        shutil.copyfile(EXAMPLE, path)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    return path


def load(path: Path = DEFAULT) -> dict:
    with open(EXAMPLE, "rb") as f:
        cfg = tomllib.load(f)
    path = Path(path)
    if path.exists():
        with open(path, "rb") as f:
            cfg = _merge(cfg, tomllib.load(f))
    validate(cfg)
    cfg["aliases"] = {int(k): str(v) for k, v in cfg.get("aliases", {}).items()}
    return cfg


def validate(cfg: dict):
    s = cfg["screen"]
    if s["orientation"] not in ("portrait", "landscape"):
        raise ValueError("screen.orientation must be 'portrait' or 'landscape'")
    if not 1 <= float(s["refresh"]) <= 300:
        raise ValueError("screen.refresh must be 1-300 seconds")
    window = cfg.get("active") or cfg.get("night")
    if window:
        for k in ("start", "end", "weekend_start", "weekend_end"):
            if k not in window:
                continue
            if not re.fullmatch(r"\d{1,2}:\d{2}", window[k]):
                raise ValueError(f"active/night.{k} must look like 18:00")
    for k, v in cfg["thresholds"].items():
        if len(v) != 2 or v[0] > v[1]:
            raise ValueError(f"thresholds.{k} must be [warn, critical]")
