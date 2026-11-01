"""AceMagic/SZBox S1 front TFT + LED — host + Kubernetes metrics for this homelab.

Based on nov30th/s1-mini-computer-tft-screen-release (MIT).
"""
from pathlib import Path

__version__ = "1.1.0-homelab"
__author__ = "Vincent Qiu (nov30th) + homelab adaptations"

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
