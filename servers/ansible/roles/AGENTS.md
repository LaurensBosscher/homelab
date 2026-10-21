# ANSIBLE ROLES

K3s node roles, plus `openstick` which is applied only from `../openstick.yml`.

## STRUCTURE
```
roles/
├── SHARED (all nodes)           │ CONTROL PLANE ONLY        │ AGENT ONLY
│   ansible-user                 │   k3s-common              │   k3s-common
│   security_updates             │   kubernetes-control-plane│   kubernetes-agent
│   system-hardening             │   etcd-io-priority        │
│   dotfiles, tools, k9s         └───────────────────────────┘
│   iscsid (retired; Longhorn gone)
│   optimizations, network-optimizations
│   tailscale, kubecolor
│   zswap (compressed cache + disk swap)
│   ssh (hardening; access limited by firewall)
│   crowdsec, k3s-oom-protection
│   k3s-install, firewall
│
│   openstick (separate playbook, NOT in site.yml)
```

## WHERE TO LOOK
| Task | Location |
|------|----------|
| Add new role | Create `roles/<name>/tasks/main.yml` |
| Role execution order | `../site.yml` (3 plays: all→control-plane→agent) |
| OpenStick (Debian, not K3s) | `../openstick.yml` with `../hosts-openstick.ini`. Never add that host to `hosts.ini` |
| Handler definitions | `roles/<name>/handlers/main.yml` (9 roles have handlers) |
| K3s config templates | `kubernetes-{control-plane,agent}/templates/config.yaml.j2` |
| Kubelet settings | `k3s-common/tasks/main.yml` (swap, resources, GC) |

## CONVENTIONS

### Role Structure
- **Minimal**: `tasks/main.yml` only (most roles)
- **With handlers**: Add `handlers/main.yml` for service restarts
- **With templates**: Add `templates/*.j2` (k8s roles, and openstick for the PicoClaw token)
- **With defaults**: Add `defaults/main.yml` (dotfiles, openstick)

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
Roles use descriptive tags: `[security, updates]`, `[ssh]`, `[zswap]`, `[etcd_firewall]`
