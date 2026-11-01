"""Kubernetes snapshot via kubectl (k3s). Counts only — no pod list."""
from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field

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


class K8sClient:
    def __init__(self, cfg: dict):
        k = cfg.get("k8s", {})
        self.kubeconfig = k.get("kubeconfig", "/etc/rancher/k3s/k3s.yaml")
        self.context = k.get("context", "")
        self._env = os.environ.copy()
        self._env["KUBECONFIG"] = self.kubeconfig

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

    def snapshot(self) -> Snapshot:
        snap = Snapshot()
        nodes = self._kubectl("get", "nodes").get("items", [])
        snap.nodes_total = len(nodes)
        alloc_cpu = alloc_mem = 0.0
        for n in nodes:
            conds = {c["type"]: c["status"] for c in n.get("status", {}).get("conditions", [])}
            if conds.get("Ready") == "True":
                snap.nodes_ready += 1
            a = n.get("status", {}).get("allocatable", {})
            alloc_cpu += _parse_qty(a.get("cpu", "0"))
            alloc_mem += _parse_qty(a.get("memory", "0"))

        pods = self._kubectl("get", "pods", "-A").get("items", [])
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
            cmd = ["kubectl", "get", "--raw", "/apis/metrics.k8s.io/v1beta1/nodes"]
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
            if r.returncode == 0:
                items = json.loads(r.stdout).get("items", [])
                use_cpu = use_mem = 0.0
                for m in items:
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
