from django.contrib import admin

from .models import Host, PortScan, ScanResult


@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "ip_address",
        "enabled",
        "last_scan_at",
        "last_scan_status",
        "total_open_ports",
    ]
    list_filter = ["enabled", "last_scan_status"]
    search_fields = ["name", "ip_address"]
    readonly_fields = ["created_at", "updated_at", "last_scan_at", "last_scan_status"]

    actions = ["scan_selected_hosts"]

    def scan_selected_hosts(self, request, queryset):
        from .tasks import PortScanner

        scanner = PortScanner()

        for host in queryset.filter(enabled=True):
            scanner.scan_host(host)

        self.message_user(request, f"Scanned {queryset.count()} host(s)")

    scan_selected_hosts.short_description = "Scan selected hosts"  # type: ignore[attr-defined]


@admin.register(ScanResult)
class ScanResultAdmin(admin.ModelAdmin):
    list_display = ["host", "started_at", "status", "duration_seconds", "open_port_count"]
    list_filter = ["status", "started_at"]
    readonly_fields = ["started_at", "completed_at", "duration_seconds"]

    def open_port_count(self, obj):
        return obj.ports.filter(state="open").count()

    open_port_count.short_description = "Open Ports"  # type: ignore[attr-defined]


@admin.register(PortScan)
class PortScanAdmin(admin.ModelAdmin):
    list_display = [
        "port",
        "protocol",
        "state",
        "service_name",
        "service_version",
        "scan_result",
    ]
    list_filter = ["state", "protocol"]
    search_fields = ["port", "service_name"]
