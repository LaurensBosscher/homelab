# Mydia Deployment

This directory contains Kubernetes manifests for deploying Mydia, a media library manager with SQLite backend.

## Files

- `mydia-deployment.yml` - Deployment manifest for Mydia container
- `mydia-service.yml` - Service definition for Mydia
- `mydia-pvcs.yml` - PersistentVolumeClaim definition for data storage

## Required Secrets

Before deploying, create a secret named `mydia-secrets` in the `mydia` namespace with the following keys:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mydia-secrets
  namespace: mydia
type: Opaque
stringData:
  secret-key-base: "<generate-with-openssl-rand-base64-48>"
  guardian-secret-key: "<generate-with-openssl-rand-base64-48>"
```

### Generating Secrets

Generate secrets using OpenSSL:
```bash
openssl rand -base64 48  # For secret-key-base
openssl rand -base64 48  # For guardian-secret-key
```

## Security Features

This deployment follows Kubernetes security best practices:

- ✅ **Security Contexts**: Container runs as non-root user (UID 1000)
- ✅ **Privilege Escalation**: Disabled (`allowPrivilegeEscalation: false`)
- ✅ **Capabilities**: All Linux capabilities dropped
- ✅ **Seccomp Profile**: RuntimeDefault enabled
- ✅ **Service Account**: Auto-mounting disabled
- ✅ **Resource Limits**: CPU and memory limits configured
- ✅ **Health Checks**: Liveness and readiness probes configured
- ✅ **Node Affinity**: Preferentially deployed to US region nodes

## Storage

- **SQLite Database & Config**: Single 5Gi PVC with `longhorn-2replicas-compressed-us` storage class (stores both SQLite database and application configuration in `/config`)
- **Media Files**: Mounted from host path `/mnt/downloads/` (read-write access)

## Network Access

- **Internal**: `mydia:4000`
- **External**: `https://mydia.bosscher.ch` (via Cloudflare Tunnel)

## Health Monitoring

- **Homepage**: Added to Stremio section
- **Gatus**: Health checks configured at `/health` endpoint
- **Probes**: 
  - Liveness: 60s initial delay, 60s period
  - Readiness: 30s initial delay, 60s period

## Deployment

The deployment is managed by ArgoCD and will be automatically deployed when merged to the main branch. The `mydia` namespace will be created automatically.

## Environment Variables

Key environment variables configured:
- `PUID`: 1000
- `PGID`: 1000
- `TZ`: Europe/Zurich
- `PHX_HOST`: mydia.bosscher.ch
- `METADATA_RELAY_URL`: https://metadata-relay.arsfeld.dev (for fetching TV/movie metadata)

## Resource Allocation

- Requests: 100m CPU, 256Mi memory
- Limits: 1Gi memory
