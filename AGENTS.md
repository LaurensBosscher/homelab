# PROJECT KNOWLEDGE BASE

**Generated:** 2026-01-10
**Repository:** Multi-region Kubernetes Homelab (K3s)

## OVERVIEW
IaC repo for 7-node K3s cluster across 4 regions. GitOps CD (ArgoCD) for apps, Ansible for infra.

## STRUCTURE
```
./
├── apps/              # 40+ Kubernetes apps (auto-deployed via ArgoCD)
├── servers/ansible/    # 22 roles for node provisioning
├── cloudflare/        # Tunnel management (Python + config)
├── helm/              # Prometheus chart wrapper
└── docs/              # Screenshots
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add new app | `apps/<app-name>/` | 3 files needed: deployment, service, PVC |
| Dashboard entry | `apps/homepage/homepage-config.yml` | Add service widget |
| DNS routing | `cloudflare/tunnels/config.yml` | Map hostname→K8s service |
| Health monitoring | `apps/gatus/gatus-configmap.yml` | Add endpoint check |
| Node inventory | `servers/ansible/hosts.ini` | 6 nodes (3 CP, 3 worker) |
| Infrastructure config | `servers/ansible/roles/` | 22 roles (k3s, tailscale, firewall) |
| Storage classes | `apps/default/` | Longhorn variants (2replicas-{europe,us}) |

## CONVENTIONS

### Kubernetes Manifests
- File naming: `<app-name>-<resource-type>.yml` (e.g., `homepage-deployment.yml`)
- Labels: `app.kubernetes.io/name: <app-name>`
- Images: Specific tags only (NO `latest`)
- Resources: All deployments need `requests` + `limits`
- Probes: `livenessProbe` + `readinessProbe` required
- Affinity: `nodeAffinity` for geo-placement (europe/us/zurich)

### 3-Step New App Workflow
1. **Homepage entry**: Add widget to `apps/homepage/homepage-config.yml`
2. **DNS route**: Add entry to `cloudflare/tunnels/config.yml`
3. **Health check**: Add endpoint to `apps/gatus/gatus-configmap.yml`
4. **Done**: ArgoCD auto-discovers and deploys

### PVC Naming Inconsistency
- Pattern A: `<app>-pvc.yml` (6 apps)
- Pattern B: `<app>-pvcs.yml` (19 apps)
- Both acceptable, follow app's existing pattern

### Extensions
- Primary: `.yml`
- Acceptable: `.yaml` (e.g., `longhorn-config/longhorn-recurring-job-backup-to-cloudflare-r2.yaml`)

## ANTI-PATTERNS (THIS PROJECT)

### Critical Restrictions
- **NEVER** commit secrets (use Sealed Secrets or cluster secrets)
- **NEVER** use `latest` image tags
- **NEVER** make breaking changes to running 24/7 apps
- **DO NOT COMMIT** - prepare changes, let human commit

### Forbidden Practices
- Deploying without testing in non-prod namespace first
- Modifying `apps/` without expecting immediate ArgoCD deployment
- Committing `.venv/`, `__pycache__/`, `.mypy_cache/`, or editor files

## UNIQUE STYLES

### Multi-Region Deployment
- Node affinity regions: `europe`, `us`, `zurich`
- Cloudflare Tunnels: 1 instance per region
- Storage: Longhorn 2-replica variants per region (compressed available)

### GitOps Automation
- ApplicationSet auto-discovers all `apps/*/` directories
- Manual Application resource for Longhorn (not auto-discovered)
- Helm wrapper for Prometheus in `helm/prometheus/`

### Dependency Management
- Renovate monitors `apps/*.ya?ml` for container image updates
- Creates immediate PRs, no auto-merge
- `getmeili/meilisearch` excluded (manual updates only)

### Ansible Optimization
- `ansible.cfg`: 6 parallel SSH connections, JSON fact caching (1h timeout)
- 22 roles: k3s-install, tailscale, firewall, zram, k3s-oom-protection, crowdsec, etc.
- Execution: Manual only via `ansible-playbook -i hosts.ini site.yml -u root --private-key ~/.ssh/id_rsa_kubernetes`

## COMMANDS
```bash
# Validate Kubernetes manifests
kubectl apply --dry-run=client -f <file>

# Validate Ansible playbooks
ansible-playbook --syntax-check -i hosts.ini site.yml
ansible-playbook --check -i hosts.ini site.yml  # dry-run

# Deploy infrastructure (manual)
cd servers/ansible
ansible-playbook -i hosts.ini site.yml -u root --private-key ~/.ssh/id_rsa_kubernetes

# Apps auto-deploy via ArgoCD - just push to apps/
```

## NOTES

### Gotchas
- **ArgoCD auto-deploys**: Any push to `apps/` immediately triggers deployment - be careful!
- **No CI testing**: Validation is manual (kubectl dry-run, ansible --check)
- **Production homelab**: All apps run 24/7 - minimal changes only
- **SSH access**: Only via Tailscale interface for security
- **Cloudflare automation**: Python script (`update_config.py`) + GitHub Actions workflow syncs on push

### Testing Philosophy
- Runtime health = primary test (Kubernetes probes + Gatus monitoring)
- ArgoCD SelfHeal auto-corrects drift
- If it deploys successfully, it's "tested"
- No unit/integration tests - cluster is test environment

### Cluster Specs
- 7 nodes across 4 regions (CA x2, UK x3, NL x1, CH x1)
- 118 GB RAM, 20 CPU cores total
- Storage: Longhorn 2-way replication, auto-backup to Backblaze
- Networking: Wireguard + Tailscale, Cloudflare Tunnels ingress
