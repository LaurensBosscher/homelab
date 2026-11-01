# s1screen (homelab)

Front-panel metrics for the SZBox / AceMagic **S1** on Bazzite.

Upstream protocol + LCD/LED drivers: [nov30th/s1-mini-computer-tft-screen-release](https://github.com/nov30th/s1-mini-computer-tft-screen-release) (MIT).  
This tree replaces Proxmox guest lists with **Kubernetes counts + host metrics**, landscape-first.

## Display

- Hours: **18:00–00:00** (blank + LED off otherwise)
- Host: CPU / MEM / SWAP / °C rings, RAPL W, CPU GHz, NIC ↓↑, load
- Cluster: nodes Ready, pods run/pend/fail, cluster CPU/mem bars, `/var` disk

No per-pod list — the 320×170 panel cannot carry it.

## Ops

```bash
# on bazzite
cd /var/lib/s1screen
./s1screen.py check
./s1screen.py preview --demo -o /tmp/preview.png
systemctl status s1screen
journalctl -u s1screen -f
```

Deployed by Ansible role `s1screen` (enabled only on `bazzite`).
