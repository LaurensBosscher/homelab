# Laurens Kubernetes Homelab

This repo contains backups, scripts, and documentation for my hobby and educational [Kubernetes](https://kubernetes.io/) cluster.

The cluster is configured with production like settings such as:

- Automatic fail-over for all deployments and nodes, deployed on: 
    - 7 nodes
    - Across 4 regions
    - Across 3 different providers + my home server
- Ability to target deployment to a geographical location to optimize for latency with automatic fallback or do multi-region deployment
- All data is replicated to two nodes by [Longhorn](https://longhorn.io/) and automatically backed-up to [Backblaze](https://www.backblaze.com/)
- CD pipeline through [ArgoCD](https://argo-cd.readthedocs.io/en/stable/). Any changes in the apps folder will automatically be deployed
- Ingress is taking care of by [Cloudflare Tunnels](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) with one instance per geographical region
  - Changes are automatically updated using a [GitHub Actions workflow](.github/workflows/update_cloudflare_settings.yml)
- Communication between the nodes is done through the wireguard native backend (Running over Tailscale caused double encapsulation and hard to debug issues)
- Joining new nodes to the cluster is a ~5 minute job
- Secrets are [encrypted](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/) and not stored in this repo ;)
- [Mend Renovate](https://www.mend.io/renovate/) monitors this repo and automatically creates PRs for any software updates

# Security

## Network Security

### Secure Communication
- **WireGuard Backend**: Internal cluster communication uses WireGuard directly (not over Tailscale) to avoid double encapsulation issues
- **SSH Restricted to Tailscale**: SSH daemon only listens on the Tailscale interface, eliminating public SSH exposure

### Firewall (nftables)
A comprehensive firewall configuration is available via Ansible, it provides:

- **Port Scan Protection**: Drops NULL, SYN-FIN, SYN-RST, and FIN-RST scans
- **Anti-Spoofing**: Blocks spoofed loopback traffic (127.0.0.0/8 and ::1)
- **Rate Limiting**: ICMP limited to 10/second to prevent ping floods
- **Cluster Traffic Only**: Only allows Kubernetes traffic from authorized cluster IPs:
  - Flannel WireGuard (51820/udp) between all nodes
  - Kubelet API (10250/tcp) from control-plane to worker nodes
  - K3s API (6443/tcp) and supervisor (9345/tcp) between control-plane nodes
  - etcd (2379-2380/tcp) between control-plane nodes
- **Logging**: Rate-limited logging of dropped NEW connections (10/minute)

## Intrusion Detection & Prevention

### CrowdSec
[CrowdSec](https://crowdsec.com/) provides real-time threat detection and automated mitigation:

- **Firewall Bouncer**: Integrated with nftables for IP blocking
- **Kubernetes Bouncer**: Monitors and protects Kubernetes workloads
- **Recommended Collections**: Pre-installed security rule collections
- **Cluster Whitelisting**: All cluster IPs whitelisted to prevent false positives
- **Console Enrollment**: Optionally enrolled in CrowdSec Console for centralized management
- **Automated Response**: Threat IPs are automatically blocked at the firewall level

## Security Updates

Automatic security patching is enabled through `dnf-automatic`:
- **Security-Only Updates**: Only security patches are applied automatically
- **Service Restarts**: Services are automatically restarted after updates
- **No Auto-Reboot**: Kernel updates do not trigger automatic reboots (manual intervention required)

## System Hardening

### Resource Protection
Critical services are protected against OOM (Out of Memory) kills:
- **K3s**: OOMScoreAdjust=-400
- **Tailscale**: OOMScoreAdjust=-900
- **Chrony (NTP)**: OOMScoreAdjust=-900

### System Stability
- **Log Management**: Journald configured with rotation (2GB max, 1 month retention)
- **Time Synchronization**: Chrony NTP client ensures accurate time across all nodes
- **CPU Governor**: Set to performance mode for consistent performance

### Mandatory Access Control (SELinux)
- **SELinux Enforcing**: SELinux is configured in enforcing mode with targeted policy on supported nodes
- **Per-Node Exception Support**: Hosts with known compatibility issues can opt out via inventory variable (currently used for `k3s-london-3`)

## Kubernetes Security

### Secrets Management
- **Encryption at Rest**: Kubernetes secrets are encrypted using [K3s secret encryption](https://docs.k3s.io/installation/datastore#secret-encryption)
- **No Secrets in Repo**: Secrets are never committed to this repository
- **Sealed Secrets**: Uses [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) for secret management

### Access Control
- **RBAC**: Role-based access control enabled by default
- **Network Policies**: Flannel CNI provides network segmentation
- **Pod Security**: Security contexts enforced on all deployments

### Runtime Sandboxing
- **Seccomp Default Enabled**: Kubelet runs with `seccompDefault: true`, applying RuntimeDefault seccomp profiles by default

# Screenshots

![](docs/home.bosscher.ch_.png)
![](docs/kite.bosscher.ch_.png)
![](docs/argocd.bosscher.ch_applications.png)


# Hardware

| location   | ram  | cpu                            | Storage | role          | note        | cost/y | management url                  |
| ---------- | ---- | ------------------------------ | ------- | ------------- | ----------- | ------ | ------------------------------- |
| California | 30GB | 3c (Xeon Gold 6248)            | NVMe    | worker        |             | $35    | https://master.pandahost.co.uk/ |
| California | 30GB | 3c (Xeon Silver 4214)          | NVMe    | worker        |             | $35    | https://master.pandahost.co.uk/ |
| London     | 5GB  | 2c (Xeon Gold 6148)            | NVMe    | worker        |             | $20    | https://master.pandahost.co.uk/ |
| London     | 5GB  | 2c (Xeon Gold 6148)            | NVMe    | control plane |             | $20    | https://master.pandahost.co.uk/ |
| London     | 8GB  | 4c (AMD EPYC 7542)             | NVMe    | control plane |             | $35    | https://rarecloud.io/clients/   |
| Amsterdam  | 8GB  | 3c (Intel Xeon Platinum 8173M) | SSD     | control plane |             | $20    | https://vps.deluxhost.net/      |
| Zurich     | 32GB | 4c (Intel N97)                 | NVMe    | worker        | Home Server | $0     |                                 |

Total of 118 GB RAM and 20 CPU cores. You could get that in a single powerful server but not for for ~100 USD/year and where is the fun in that?

# Apps

I'm currently running the following apps:

- [AIOStreams](https://github.com/Viren070/AIOStreams) - Streaming content aggregator
- [ArgoCD](https://argo-cd.readthedocs.io/en/stable/) - Declarative GitOps CD for Kubernetes
- [Audiobookshelf](https://www.audiobookshelf.org/) - Self-hosted audiobook and podcast server
- [BentoPDF](https://github.com/bentopdf/bentopdf) - Convert HTML to PDF
- [Bookshelf](https://github.com/pennydreadful/bookshelf) - Self-hosted book catalog for web novels and fanfiction
- [Calibre Web](https://github.com/crocodilestick/Calibre-Web-Automated) - Enhanced version of Calibre web
- [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) - Secure ingress to the cluster
- [Docspell](https://docspell.org/) - Document management and archiving system
- [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) - Proxy server to bypass Cloudflare protection
- [Fusion](https://github.com/0x2E/fusion) - Lightweight RSS Reader
- [Gatus](https://github.com/TwiN/gatus) - Synthetic uptime monitoring and status page
- [Homepage](https://gethomepage.dev/) - A highly customizable homepage/dashboard
- [it-tools](https://github.com/corentinth/it-tools) - Collection of handy online tools for developers, with great UX
- [Kite](https://github.com/zxh326/kite) - Kubernetes dashboard
- [Linkwarden](https://github.com/linkwarden/linkwarden) - Collaborative bookmark manager
- [Listenarr](https://github.com/therobbiedavis/Listenarr) - Automated audiobook downloader and library manager
- [Longhorn](https://longhorn.io/) - Cloud-native distributed block storage for Kubernetes
- [mydia](https://github.com/getmydia/mydia) - Self-hosted media manager
- [n8n](https://n8n.io/) - Workflow automation tool
- [Norish](https://github.com/norish-recipes/norish) - Real-time, self-hosted recipe app for families & friends
- [obsidian-live-sync](https://github.com/vrtmrz/obsidian-livesync) - Live sync for Obsidian
- [openagent](https://github.com/e2b-dev/openagent) - AI agent framework
- [opencode](https://github.com/OpenCode-Org/opencode) - AI-powered development environment
- [Perplexica](https://github.com/ItzCrazyKns/Perplexica) - AI-powered search engine
- [playarr](https://github.com/maikboarder/playerr) - Audiobook manager for Plex
- [prowlarr](https://github.com/Prowlarr/Prowlarr) - Indexer manager
- [qbittorrent](https://github.com/qbittorrent/qBittorrent) - BitTorrent client
- [questarr](https://github.com/doezer/questarr) - Quest manager for audiobooks
- [radarr](https://github.com/Radarr/Radarr) - Movie collection manager
- [RDT-Client](https://github.com/rogerfar/rdt-client) - Real-Debrid torrent client
- [SABnzbd](https://sabnzbd.org/) - Usenet downloader
- [shelfarr](https://github.com/DerGoogler/Shelfarr) - Audiobook library manager
- [Shiori](https://github.com/go-shiori/shiori) - Simple bookmark manager
- [sonarr](https://github.com/Sonarr/Sonarr) - TV show collection manager
- [Stacks](https://github.com/zelestcarlyone/stacks) - Download Manager for Anna's Archive
- [Stremio](https://www.stremio.com/) - Media streaming platform
- [surfsense](https://github.com/surfsense/surfsense) - Self-hosted news aggregation
- [termix](https://github.com/willdoescode/termix) - Terminal-based matrix client
- [Wanderer](https://github.com/Flomp/wanderer) - Self-hosted trail and route planner
- [your-spotify](https://github.com/Yooooomi/your_spotify) - Self-hosted Spotify statistics and analytics

## To Explore

- [ ] [Dawarich](https://github.com/Freika/dawarich) - Self-hosted alternative to Google Timeline
- [X] [DNS Blocklist](https://github.com/hagezi/dns-blocklists?tab=readme-ov-file#overview) - DNS Blocklist
- [ ] [Github-to-sops](https://github.com/tarasglek/github-to-sops) - Easy way to integrate secrets in GIT
- [ ] [LLocalSearch](https://github.com/nilsherzig/LLocalSearch) - Local AI-powered search engine
- [ ] [Netvisor](https://github.com/mayanayza/netvisor?tab=readme-ov-file) - Netvisor, overview of network and services
- [ ] [Open WebUI](https://github.com/open-webui/open-webui) - User-friendly WebUI for LLMs
- [ ] [Pumpkin](https://github.com/Snowiiii/Pumpkin) - Minecraft server implementation in Rust
- [ ] [Quartz 4](https://quartz.jzhao.xyz/) - Static site generator
- [ ] [Calibre Web Automated Book Downloader](https://github.com/calibrain/calibre-web-automated-book-downloader) - Automatically download (and add) books to Calibre web
- [ ] [daedalOS](https://github.com/DustinBrett/daedalOS) - Desktop enviroment in the browser
- [ ] [VSCode web](https://github.com/coder/code-server) - Web version of VSCode
- [ ] [Khoj](https://github.com/khoj-ai/khoj) - Self-hosted AI second brain
- [ ] [hotpot](https://github.com/erik/hotpot) - Render customizable activity heatmap images from GPS tracks extracted from GPX, TCX, and FIT files. Includes a built-in web server for XYZ tiles and endpoints to add new data via HTTP POST or Strava webhooks.

# Adding new nodes

## Preparation

1. Copy your ssh key:

```bash
ssh-copy-id -i ~/.ssh/id_rsa_kubernetes root@<IP_ADDRESS>
```

2. Install Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up
```
3. Add new node to servers/ansible/hosts.ini

4. Deploy:

```bash
ansible-playbook -i hosts.ini site.yml -u root --private-key ~/.ssh/id_rsa_kubernetes
```

5. Reboot (to ensure that the new mainline kernel is loaded)

6. Connect to cluster:

### Control-plane-node
```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL=latest K3S_TOKEN=<TOKEN> sh -s - server --server https://<IP_ADDRESS_OF_NODE>:6443
```

### Agent
```bash
curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL=latest K3S_URL=<IP_ADDRESS_OF_NODE> K3S_TOKEN=<TOKEN> sh -
```

Ansible configures the nodes with the following:

- Automatic security updates enabled and services are automatically restarted (if needed) 
- SSH secured by only listening on the tailscale interface
- Firewall pre-configured (not yet enabled due to issues with K8s egress)
- SELinux enforcing enabled on compatible hosts (with per-node exception support)
- Kubernetes kubelet `seccompDefault` enabled
- ZRAM activated
- Network and other tweaks applied to optimize for Kubernetes usage
- K9S, Kubecolor and useful aliases automatically applied

# Tips & Tricks

## ETCDL

```bash
export ETCDCTL_ENDPOINTS="https://100.81.190.71:2379,https://100.79.162.75:2379"
export ETCDCTL_CACERT="/var/lib/rancher/k3s/server/tls/etcd/server-ca.crt"
export ETCDCTL_CERT="/var/lib/rancher/k3s/server/tls/etcd/client.crt"
export ETCDCTL_KEY="/var/lib/rancher/k3s/server/tls/etcd/client.key"
etcdctl member list
```

## etcd Maintenance (Automated)

The cluster now has automated etcd maintenance configured via Ansible:

- **Auto-compaction**: Revisions older than 1 hour are automatically compacted
- **Automated snapshots**: Taken every 12 hours, 5 snapshots retained
- **Weekly defrag**: Runs Sundays at 3 AM (with 30 min random delay) if DB > 1GB

### Manual defrag (if needed)

```bash
# Check current DB size
etcdctl endpoint status --write-out table

# Defrag this node only (safe to run on live cluster)
etcdctl defrag
```

## Offline compaction and defrag (Emergency only)

Use only if cluster is unhealthy and automated maintenance failed:

```bash
sudo etcd \
  --data-dir /var/lib/rancher/k3s/server/db/etcd \
  --force-new-cluster \
  --listen-client-urls http://127.0.0.1:2379 \
  --advertise-client-urls http://127.0.0.1:2379

ETCDCTL_ENDPOINTS="http://127.0.0.1:2379" rev=$(etcdctl endpoint status --write-out fields | grep Revision | awk '{print $3}')
ETCDCTL_ENDPOINTS="http://127.0.0.1:2379" etcdctl compact "$rev" --physical   # --physical forces immediate application
ETCDCTL_ENDPOINTS="http://127.0.0.1:2379" etcdctl defrag
```

## Add debug container to pod

```bash
kubectl debug -it my-pod --image=busybox
```

## Run test container on specific node

```bash
kubectl run busybox-bazzite --image=busybox:latest --restart=Never --overrides='{"spec":{"nodeName":"k3s-london-1"}}' -- /bin/sleep 3600
```

## Monitoring configuration for Kite
Kite resets its settings on every upgrade, URL to enable the prometheus integration is:

```
http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090
```
