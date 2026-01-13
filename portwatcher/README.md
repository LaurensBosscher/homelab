# Portwatcher

A Django-based port scanning application for monitoring hosts in a Kubernetes cluster.

## Features

- 🔍 Full port scanning (1-65535) with nmap
- 🎯 Service detection and version identification
- 📊 Modern web interface with PicoCSS + HTMX
- 🕐 Automatic hourly scans via CronJob
- 📈 Scan history tracking
- 🔐 Django admin for host management

## Architecture

- **Backend**: Django 5.x + Python 3.14
- **Scanner**: nmap with service detection
- **Database**: SQLite
- **Frontend**: PicoCSS + HTMX
- **Deployment**: Kubernetes (US region)

## Configuration

Scanner settings in `portwatcher/settings.py`:
- `SCANNER_INTERVAL_MINUTES`: 60 (hourly)
- `SCANNER_NMAP_ARGS`: "-p- -sV -T4" (all ports, service detection)
- `SCANNER_TIMEOUT_SECONDS`: 600 (10 min per host)

## Development

### Local Setup
```bash
cd portwatcher
uv sync
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Docker
```bash
docker-compose up
```

### Manual Scan
```bash
python manage.py scan_hosts
# Or scan specific host:
python manage.py scan_hosts --host myhost
```

## Deployment

Deploys automatically via ArgoCD when changes pushed to `apps/portwatcher/`.

Access:
- Web UI: https://portwatcher.bosscher.ch
- Admin: https://portwatcher.bosscher.ch/admin/

## License

MIT
