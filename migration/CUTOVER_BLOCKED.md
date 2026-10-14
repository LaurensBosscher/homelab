# Cutover blocked — bazzite SSH

After `k3s-agent-uninstall` on bazzite (`mini-pc`), the host still **pings** on:

- Tailscale `100.81.190.71`
- LAN `192.168.1.104`

but **TCP/22 times out** (sshd or firewall broken by `k3s-killall` iptables flush).

## Recover on the console (keyboard/HDMI)

```bash
sudo systemctl start sshd
sudo systemctl enable sshd

# Firewall — pick what bazzite uses:
sudo systemctl start firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload

# and/or:
sudo iptables -I INPUT -p tcp --dport 22 -j ACCEPT
# nft alternative:
sudo nft insert rule inet filter input tcp dport 22 accept

sudo systemctl start tailscaled
sudo tailscale up
```

When SSH works, tell the agent to resume. Scripts are on london-1:

- `/root/homelab-migrate/bin/cutover-bazzite-disk.sh`
- `/root/homelab-migrate/bin/cutover-install-server.sh`
- `/root/homelab-migrate/bin/cutover-join-agent.sh`

## Already done
- london-1 + london-3 K3s wiped (no `/usr/local/bin/k3s`)
- 33 PVC restic snapshots + sealed-secrets offline
- `hosts.v2.ini` → bazzite + london-1 + london-3
- Optional norish / your-spotify skipped (non-critical)

## Not done yet
- `/var/mnt/downloads` → `/var/mnt/data/{downloads,local-path,migrate}`
- Fresh K3s SQLite server on bazzite
- Join london agents + restore apps from restic
