# Radarr Migration to Kustomize Base Template

This PR migrates Radarr from standalone manifests to using the Kustomize base template pattern.

## What Changed

### Before (Old Way)
```
apps/radarr/
├── radarr-deployment.yml   (120 lines, includes all security, resources, etc.)
├── radarr-pvcs.yml
└── radarr-service.yml
```

### After (New Way)
```
apps/base/                    # Shared templates (used by all apps)
├── deployment-base.yaml     # Security, resources, health checks
├── service-base.yaml        # Common service pattern
└── kustomization.yaml

apps/radarr/                  # App-specific only
├── kustomization.yaml       # Uses base + app patches
├── deployment-patch.yaml    # Radarr-specific overrides (20 lines)
└── radarr-pvcs.yml
```

## Benefits

1. **Reduced Duplication**: Security hardening now defined once, not per-app
2. **Consistency**: All apps using this base have same security posture
3. **Easier Updates**: Change security/resources once, applies to all apps
4. **Faster App Setup**: New apps need only app-specific patch files
5. **Better Maintainability**: Clear separation of common vs. app-specific

## Radarr-Specific Settings Preserved

- Image: `linuxserver/radarr:latest`
- Port: 7878
- Environment: TZ, PUID, PGID
- Volume mounts: config, media
- PVCs: config, media

## ArgoCD Update Required

Update the Radarr Application in ArgoCD to point to the new path:

```yaml
spec:
  source:
    path: apps/radarr  # Was: apps/radarr/radarr-deployment.yml
    kustomize: {}
```

## Testing

1. Review the generated deployment: `kustomize build apps/radarr`
2. Compare with original: Ensure all settings are preserved
3. Apply in ArgoCD and verify Radarr works correctly

## Next Steps

If this pattern works well, similar apps can be migrated:
- Sonarr (very similar to Radarr)
- Prowlarr (similar pattern)
- Other web apps following this pattern

---

## Example Comparison

### Old deployment.yaml (excerpt)
```yaml
spec:
  replicas: 1
  template:
    spec:
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: radarr
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /
            port: 7878
          initialDelaySeconds: 30
          periodSeconds: 10
        # ... plus app-specific stuff
```

### New deployment-patch.yaml (much shorter!)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: radarr
spec:
  template:
    spec:
      containers:
      - name: radarr
        image: linuxserver/radarr:latest
        env: [...]
        ports: [...]
        volumeMounts: [...]
      volumes: [...]
```

All the security, resource, and probe settings come from the base template!
