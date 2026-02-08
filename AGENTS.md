# AGENTS.md - Codebase Guide

## Project Overview
Multi-region K3s Kubernetes homelab (7 nodes, 4 regions). GitOps CD via ArgoCD. IaC with Ansible for infrastructure.

## Repository Structure
- `apps/<app-name>/` - Kubernetes manifests (auto-deployed)
- `servers/ansible/` - Ansible playbooks/roles
- `cloudflare/` - Python automation for Cloudflare tunnels
- `helm/` - Helm chart wrappers

## Commands

### Validate Kubernetes Manifests
```bash
kubectl apply --dry-run=client -f <file>
```

### Validate Ansible
```bash
cd servers/ansible
ansible-playbook --syntax-check -i hosts.ini site.yml
ansible-playbook --check -i hosts.ini site.yml      # dry-run
ansible-playbook -i hosts.ini site.yml -u root --private-key ~/.ssh/id_rsa_kubernetes
```

### Python (Cloudflare scripts)
```bash
cd cloudflare/tunnels
uv sync
uv run python update_config.py
uv run ruff check .          # linting
uv run ruff format .         # formatting
uv run mypy update_config.py # type checking
```

### Test Single Resource
```bash
# Kubernetes - apply to non-prod namespace first
kubectl apply -f <file> -n test-namespace

# Ansible - test single role
cd servers/ansible
ansible-playbook -i hosts.ini site.yml --tags <role-name> --check
```

## Code Style Guidelines

### Kubernetes Manifests
- **File naming**: `<app-name>-<resource-type>.yml` (e.g., `n8n-deployment.yml`)
- **Extensions**: Primary `.yml`, acceptable `.yaml`
- **Labels**: `app.kubernetes.io/name: <app-name>` required
- **Images**: Specific tags ONLY (NO `latest`). Renovate monitors for updates
- **Resources**: Must include `requests` + `limits`
- **Probes**: `livenessProbe` + `readinessProbe` required
- **Affinity**: Use `nodeAffinity` for geo-placement (europe/us/zurich)
- **Pod affinity**: Use `app.kubernetes.io/part-of` for grouping
- **Strategy**: `type: Recreate` for stateful workloads

### Ansible
- **Inventory**: `hosts.ini` with `ansible_python_interpreter` per host
- **Roles**: 22 roles under `roles/`, referenced in `site.yml`
- **Variables**: Use `vars:` in playbooks, avoid inline Jinja2
- **Handlers**: Use `notify` + `handlers/main.yml`
- **Facts**: Use `ansible_facts` over `ansible_*` variables
- **Tags**: Tag all tasks for selective execution

### Python (Cloudflare)
- **Framework**: Pydantic models for configuration validation
- **Typing**: Full type annotations required (mypy strict)
- **Dependencies**: Use `uv` + `pyproject.toml` (NOT pip/requirements.txt)
- **HTTP**: Use `requests` library
- **Naming**: snake_case variables, CamelCase classes
- **Errors**: Use specific exceptions, log with emojis for visibility
- **Main**: Guard with `if __name__ == "__main__":`

### General Formatting
- **YAML**: 2-space indentation
- **Python**: Ruff for lint/format (follows Black style)
- **No trailing whitespace**
- **End files with newline**

## Naming Conventions

### Kubernetes
- Resources: lowercase with hyphens
- PVCs: `<app>-pvc.yml` or `<app>-pvcs.yml` (follow existing pattern)
- ConfigMaps: `<app>-configmap.yml`
- Secrets: Never in repo; use `secretKeyRef` + cluster secrets

### Services
- DNS: `<service>.<namespace>.svc.cluster.local:<port>`
- Hostnames: `<service>.bosscher.ch`

## Error Handling

### Kubernetes
- Health checks required (probes)
- Graceful shutdown handling
- Resource limits prevent OOM cascading

### Python
- Use `try/except` with specific exceptions
- Exit non-zero on failure (`sys.exit(1)`)
- Log actionable error messages
- Validate inputs with Pydantic (fail fast)

### Ansible
- Use `failed_when` for custom failure conditions
- Use `ignore_errors: true` sparingly (document why)
- Check mode aware (`check_mode: no` when needed)

## Security

### Critical Rules
- **NEVER** commit secrets (use cluster secrets or Sealed Secrets)
- **NEVER** use `latest` image tags
- **NEVER** modify `apps/` without expecting immediate ArgoCD deployment
- SSH access: Tailscale interface only
- Firewall: nftables via Ansible (not yet enforced on all nodes)

### Secrets Handling
- Kubernetes: Use `secretKeyRef` referencing cluster secrets
- Python: Environment variables (never hardcoded)
- Ansible: `ansible-vault` or cluster-managed

📝 If You Expose Services via NodePort/MetalLB
Add explicit rules in the forward chain before the final drop:
# Example: Allow NodePort range from internet
iifname "eth0" tcp dport 30000-32767 accept comment "NodePorts"

## Common Patterns

### Adding New App
1. Create `apps/<app-name>/` with deployment, service, PVC
2. Add homepage entry: `apps/homepage/homepage-config.yml`
3. Add DNS route: `cloudflare/tunnels/config.yml`
4. Add health check: `apps/gatus/gatus-configmap.yml`
5. ArgoCD auto-deploys

### PVC Patterns
- Pattern A: `<app>-pvc.yml` (6 apps)
- Pattern B: `<app>-pvcs.yml` (19 apps)
- Follow the existing pattern for the app

### Multi-Region Deployment
- Regions: `europe`, `us`, `zurich` (node labels)
- Storage: `2replicas-europe` or `2replicas-us` storage classes
- Tunnels: One Cloudflare tunnel instance per region

## Testing Philosophy
- Runtime health = primary test (probes + Gatus monitoring)
- ArgoCD SelfHeal auto-corrects drift
- No unit tests; cluster is the test environment
- Always validate with dry-run before applying

## Anti-Patterns
- Breaking changes to 24/7 apps
- Committing `.venv/`, `__pycache__/`, `.mypy_cache/`
- Modifying existing PVC specs (immutable fields)
- Hardcoding IPs or credentials
- Using `sudo` in Ansible tasks (use `become: true`)

## Gotchas
- ArgoCD auto-deploys on ANY push to `apps/`
- No CI testing - manual validation only
- Production homelab - minimal changes only
- Renovate creates PRs immediately (no auto-merge)
- SSH only via Tailscale (no public SSH)
- Ansible fact caching: 1 hour timeout
