# ANSIBLE ROLES

22 roles for complete node provisioning: security, K3s prerequisites, optimization, and tooling.

## STRUCTURE
```
roles/
├── SHARED (all nodes)           │ CONTROL PLANE ONLY        │ AGENT ONLY
│   ansible-user                 │   k3s-common              │   k3s-common
│   security_updates             │   kubernetes-control-plane│   kubernetes-agent
│   system-hardening             │   etcd-io-priority        │
│   dotfiles, tools, k9s         └───────────────────────────┘
│   iscsid (Longhorn storage)
│   optimizations, network-optimizations
│   tailscale, kubecolor
│   zram (50% RAM compressed swap)
│   ssh (Tailscale-only binding)
│   crowdsec, k3s-oom-protection
│   k3s-install, firewall
```

## WHERE TO LOOK
| Task | Location |
|------|----------|
| Add new role | Create `roles/<name>/tasks/main.yml` |
| Role execution order | `../site.yml` (3 plays: all→control-plane→agent) |
| Handler definitions | `roles/<name>/handlers/main.yml` (9 roles have handlers) |
| K3s config templates | `kubernetes-{control-plane,agent}/templates/config.yaml.j2` |
| Kubelet settings | `k3s-common/tasks/main.yml` (swap, resources, GC) |

## CONVENTIONS

### Role Structure
- **Minimal**: `tasks/main.yml` only (most roles)
- **With handlers**: Add `handlers/main.yml` for service restarts
- **With templates**: Add `templates/*.j2` (only k8s roles)
- **With defaults**: Add `defaults/main.yml` (only dotfiles)

### Task Patterns
```yaml
# Idempotent check → conditional action
- name: Check if X exists
  ansible.builtin.stat:
    path: /path/to/file
  register: x_exists
- name: Do action
  when: not x_exists.stat.exists

# Service config with handler notification
- name: Configure service
  ansible.builtin.copy:
    dest: /etc/service.conf
  notify: restart service

# Feature toggle with default
  when: feature_enable | default(true)
```

### Tags
Roles use descriptive tags: `[security, updates]`, `[ssh]`, `[zram]`, `[etcd_firewall]`
