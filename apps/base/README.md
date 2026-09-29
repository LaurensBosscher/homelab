# Kustomize Base Templates

This directory contains reusable Kustomize base templates for common application patterns in the homelab.

## Purpose

- Reduce code duplication across similar applications
- Enforce consistent security hardening (seccomp, non-root, resource limits)
- Standardize health checks and monitoring
- Simplify app deployment with patches vs. full manifests

## Structure

```
base/
├── deployment-base.yaml    # Common deployment pattern with security hardening
├── service-base.yaml       # Common service pattern
└── kustomization.yaml      # Base labels and configuration
```

## How to Use

### For a New App

1. Create an app directory: `apps/myapp/`
2. Create a `kustomization.yaml`:
   ```yaml
   apiVersion: kustomize.config.k8s.io/v1beta1
   kind: Kustomization
   
   resources:
     - ../../base
   
   namePrefix: myapp-
   
   patchesStrategicMerge:
     - deployment-patch.yaml
   
   commonLabels:
     app.kubernetes.io/name: myapp
   ```

3. Create `deployment-patch.yaml` with app-specific overrides

### Security Features Included

All deployments using this base include:
- Non-root user (UID 1000)
- seccompProfile: RuntimeDefault
- No privilege escalation
- All capabilities dropped
- Resource limits (requests + limits)
- Health checks (liveness + readiness)
- No service account token automount

### Migration Guide

To migrate an existing app to use this base:

1. Compare your app's deployment with `deployment-base.yaml`
2. Identify app-specific settings (image, ports, volumes, env vars)
3. Move app-specific settings to a `deployment-patch.yaml`
4. Update ArgoCD Application to point to the new `kustomization.yaml`
5. Test the deployment
6. Remove old manifest files

### Examples

See `apps/radarr/` for a complete example of this pattern in use.

## Benefits

- Reduced duplication
- Consistent security posture
- Easier updates (change security once, apply to all apps)
- Faster app setup
- Better maintainability
