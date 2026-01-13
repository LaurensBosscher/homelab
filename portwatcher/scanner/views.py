from django.conf import settings
from django.shortcuts import get_object_or_404, render

from .models import Host


def overview(request):
    hosts = Host.objects.filter(enabled=True)  # type: ignore[arg-type]
    return render(
        request,
        "scanner/overview.html",
        {"hosts": hosts, "scan_interval": settings.SCANNER_INTERVAL_MINUTES},
    )


def overview_refresh(request):
    """HTMX partial for auto-refresh"""
    hosts = Host.objects.filter(enabled=True)  # type: ignore[arg-type]
    return render(request, "scanner/partials/host_cards.html", {"hosts": hosts})


def host_detail(request, host_id):
    host = get_object_or_404(Host, id=host_id)  # type: ignore[arg-type]
    latest_scan = host.scans.filter(status="success").first()
    open_ports = []

    if latest_scan:
        open_ports = latest_scan.ports.filter(state="open").order_by("port")  # type: ignore[arg-type]

    scan_history = host.scans.all()[:10]

    return render(
        request,
        "scanner/detail.html",
        {
            "host": host,
            "latest_scan": latest_scan,
            "open_ports": open_ports,
            "scan_history": scan_history,
            "scan_interval": settings.SCANNER_INTERVAL_MINUTES,
        },
    )
