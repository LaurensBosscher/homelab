# Mydia Deployment

This directory contains Kubernetes manifests for deploying Mydia, a media library manager with PostgreSQL backend.

## Files

- `mydia-deployment.yml` - Deployment manifests for PostgreSQL and Mydia containers
- `mydia-service.yml` - Service definitions for PostgreSQL and Mydia
- `mydia-pvcs.yml` - PersistentVolumeClaim definitions for data storage

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
  postgres-user: "mydia"
  postgres-password: "<generate-strong-password>"
  postgres-db: "mydia"
  secret-key-base: "<generate-with-mix-phx.gen.secret>"
  guardian-secret-key: "<generate-with-mix-guardian.gen.secret>"
```

### Generating Secrets

The Mydia application requires specific secret formats:
- `secret-key-base`: Generate with `mix phx.gen.secret` (64+ character string)
- `guardian-secret-key`: Generate with `mix guardian.gen.secret` (64+ character string)

Alternatively, you can use OpenSSL to generate random strings:
```bash
openssl rand -hex 64
```

## Security Features

This deployment follows Kubernetes security best practices:

- ✅ **Security Contexts**: Both containers run as non-root users with specific UIDs
- ✅ **Privilege Escalation**: Disabled (`allowPrivilegeEscalation: false`)
- ✅ **Capabilities**: All Linux capabilities dropped
- ✅ **Seccomp Profile**: RuntimeDefault enabled
- ✅ **Service Account**: Auto-mounting disabled
- ✅ **Resource Limits**: CPU and memory limits configured
- ✅ **Health Checks**: Liveness and readiness probes configured
- ✅ **Pod Affinity**: PostgreSQL and Mydia co-located on same node for performance
- ✅ **Node Affinity**: Preferentially deployed to US region nodes

## Storage

- **PostgreSQL Data**: 5Gi PVC with `longhorn-2replicas-compressed-us` storage class
- **Mydia Config**: 1Gi PVC with `longhorn-2replicas-compressed-us` storage class
- **Media Files**: Mounted from host path `/mnt/downloads/` (read-write access)

## Network Access

- **Internal**: 
  - PostgreSQL: `mydia-postgres:5432`
  - Mydia: `mydia:4000`
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
- `PHX_HOST`: mydia.bosscher.ch
- `DATABASE_TYPE`: postgres
- `DATABASE_HOST`: mydia-postgres
- `METADATA_RELAY_URL`: https://metadata-relay.arsfeld.dev (for fetching TV/movie metadata)

## Resource Allocation

### PostgreSQL
- Requests: 100m CPU, 128Mi memory
- Limits: 1Gi memory

### Mydia
- Requests: 100m CPU, 256Mi memory
- Limits: 1Gi memory
