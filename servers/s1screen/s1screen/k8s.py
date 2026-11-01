"""Kubernetes snapshot via the local apiserver (HTTPS). kubectl is fallback only.

Spawning three `kubectl` processes every refresh burned ~400–500 ms of CPU; talking
to https://127.0.0.1:6443 with the kubeconfig client cert is an order of magnitude
cheaper. Snapshots are also TTL-cached so host metrics can refresh more often.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
import ssl
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

FAILED_REASONS = {
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "CreateContainerError",
    "CreateContainerConfigError",
    "InvalidImageName",
    "RunContainerError",
}


@dataclass
class Snapshot:
    nodes_ready: int = 0
    nodes_total: int = 0
    pods_running: int = 0
    pods_pending: int = 0
    pods_failed: int = 0
    cpu_usage: float | None = None  # fraction of allocatable
    mem_usage: float | None = None
    error: str = ""
    storage: dict = field(default_factory=dict)  # evaluate() compatibility


def _parse_qty(q: str) -> float:
    if q is None:
        return 0.0
    s = str(q).strip()
    if not s:
        return 0.0
    for suffix, mul in (
        ("Ki", 1024),
        ("Mi", 1024**2),
        ("Gi", 1024**3),
        ("Ti", 1024**4),
        ("k", 1e3),
        ("M", 1e6),
        ("G", 1e9),
        ("T", 1e12),
        ("m", 1e-3),
        ("n", 1e-9),
        ("u", 1e-6),
    ):
        if s.endswith(suffix):
            return float(s[: -len(suffix)]) * mul
    return float(s)


def _yaml_scalar(text: str, key: str) -> str | None:
    """Pull a top-level-ish YAML scalar without depending on PyYAML."""
    m = re.search(rf"(?m)^\s*{re.escape(key)}:\s*(.+?)\s*$", text)
    if not m:
        return None
    v = m.group(1).strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        v = v[1:-1]
    return v or None


def _b64pem(data: str) -> bytes:
    return base64.b64decode(data)


class _Api:
    """Tiny kubeconfig-authenticated HTTPS client (stdlib only)."""

    def __init__(self, kubeconfig: str):
        self.kubeconfig = kubeconfig
        self.server = ""
        self._ctx: ssl.SSLContext | None = None
        self._tmpdir: tempfile.TemporaryDirectory | None = None
        self._load()

    def _load(self):
        text = Path(self.kubeconfig).read_text()
        server = _yaml_scalar(text, "server")
        ca = _yaml_scalar(text, "certificate-authority-data")
        cert = _yaml_scalar(text, "client-certificate-data")
        key = _yaml_scalar(text, "client-key-data")
        if not (server and ca and cert and key):
            raise RuntimeError("kubeconfig missing server/client certificate fields")
        self.server = server.rstrip("/")
        self._tmpdir = tempfile.TemporaryDirectory(prefix="s1screen-kube-")
        ca_path = Path(self._tmpdir.name) / "ca.crt"
        cert_path = Path(self._tmpdir.name) / "client.crt"
        key_path = Path(self._tmpdir.name) / "client.key"
        ca_path.write_bytes(_b64pem(ca))
        cert_path.write_bytes(_b64pem(cert))
        key_path.write_bytes(_b64pem(key))
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.load_verify_locations(cafile=str(ca_path))
        ctx.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
        self._ctx = ctx

    def get_json(self, path: str, timeout: float = 5.0) -> dict:
        url = f"{self.server}{path}"
        req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, context=self._ctx, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:120]
            raise RuntimeError(f"HTTP {e.code} {path}: {body}") from e
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"{path}: {e}") from e

    def close(self):
        if self._tmpdir:
            self._tmpdir.cleanup()
            self._tmpdir = None


class K8sClient:
    def __init__(self, cfg: dict):
        k = cfg.get("k8s", {})
        self.kubeconfig = k.get("kubeconfig", "/etc/rancher/k3s/k3s.yaml")
        self.context = k.get("context", "")
        self.refresh = float(k.get("refresh", 15))
        self._env = os.environ.copy()
        self._env["KUBECONFIG"] = self.kubeconfig
        self._api: _Api | None = None
        self._cached: Snapshot | None = None
        self._cached_at = 0.0
        try:
            self._api = _Api(self.kubeconfig)
            log.info("k8s via apiserver %s (cache %.0fs)", self._api.server, self.refresh)
        except Exception as e:  # noqa: BLE001
            log.warning("direct apiserver unavailable (%s); falling back to kubectl", e)
            self._api = None

    def _kubectl(self, *args) -> dict:
        cmd = ["kubectl", *args, "-o", "json"]
        if self.context:
            cmd[1:1] = ["--context", self.context]
        r = subprocess.run(
            cmd,
            env=self._env,
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
        if r.returncode != 0:
            msg = (r.stderr or r.stdout or "kubectl failed").strip().splitlines()[-1]
            raise RuntimeError(msg[:160])
        return json.loads(r.stdout)

    def _get(self, path: str, *kubectl_args: str) -> dict:
        if self._api is not None:
            try:
                return self._api.get_json(path)
            except Exception as e:  # noqa: BLE001
                log.debug("apiserver %s failed (%s); trying kubectl", path, e)
        return self._kubectl(*kubectl_args)

    @staticmethod
    def _pod_failed(pod: dict) -> bool:
        if pod.get("status", {}).get("phase") == "Failed":
            return True
        for cs in pod.get("status", {}).get("containerStatuses", []) or []:
            waiting = (cs.get("state") or {}).get("waiting") or {}
            if waiting.get("reason") in FAILED_REASONS:
                return True
            term = (cs.get("state") or {}).get("terminated") or {}
            if term.get("reason") == "Error" and (cs.get("restartCount") or 0) > 0:
                return True
        return False

    def _fetch(self) -> Snapshot:
        snap = Snapshot()
        nodes = self._get("/api/v1/nodes", "get", "nodes").get("items", [])
        snap.nodes_total = len(nodes)
        alloc_cpu = alloc_mem = 0.0
        for n in nodes:
            conds = {c["type"]: c["status"] for c in n.get("status", {}).get("conditions", [])}
            if conds.get("Ready") == "True":
                snap.nodes_ready += 1
            a = n.get("status", {}).get("allocatable", {})
            alloc_cpu += _parse_qty(a.get("cpu", "0"))
            alloc_mem += _parse_qty(a.get("memory", "0"))

        pods = self._get("/api/v1/pods", "get", "pods", "-A").get("items", [])
        for p in pods:
            phase = p.get("status", {}).get("phase", "")
            if phase == "Succeeded":
                continue
            if phase == "Pending":
                snap.pods_pending += 1
            elif self._pod_failed(p):
                snap.pods_failed += 1
            elif phase == "Running":
                snap.pods_running += 1

        try:
            metrics = self._metrics_nodes()
            use_cpu = use_mem = 0.0
            for m in metrics.get("items", []):
                u = m.get("usage", {})
                use_cpu += _parse_qty(u.get("cpu", "0"))
                use_mem += _parse_qty(u.get("memory", "0"))
            if alloc_cpu > 0:
                snap.cpu_usage = min(use_cpu / alloc_cpu, 1.0)
            if alloc_mem > 0:
                snap.mem_usage = min(use_mem / alloc_mem, 1.0)
        except Exception as e:  # noqa: BLE001
            log.debug("metrics-server unavailable: %s", e)
        return snap

    def _metrics_nodes(self) -> dict:
        path = "/apis/metrics.k8s.io/v1beta1/nodes"
        if self._api is not None:
            try:
                return self._api.get_json(path)
            except Exception as e:  # noqa: BLE001
                log.debug("apiserver %s failed (%s); trying kubectl", path, e)
        cmd = ["kubectl", "get", "--raw", path]
        if self.context:
            cmd[1:1] = ["--context", self.context]
        r = subprocess.run(
            cmd,
            env=self._env,
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
        if r.returncode != 0:
            msg = (r.stderr or r.stdout or "kubectl metrics failed").strip().splitlines()[-1]
            raise RuntimeError(msg[:160])
        return json.loads(r.stdout)

    def snapshot(self, force: bool = False) -> Snapshot:
        now = time.monotonic()
        if (
            not force
            and self._cached is not None
            and (now - self._cached_at) < self.refresh
        ):
            return self._cached
        snap = self._fetch()
        self._cached = snap
        self._cached_at = now
        return snap
