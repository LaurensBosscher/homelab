from django.db import models


class Host(models.Model):
    """Represents a host to be monitored"""

    name = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    description = models.TextField(blank=True)
    enabled = models.BooleanField(default=True)  # type: ignore[arg-type]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    last_scan_at = models.DateTimeField(null=True, blank=True)
    last_scan_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("scanning", "Scanning"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        default="pending",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.ip_address})"

    @property
    def total_open_ports(self):
        """Count currently open ports from latest scan"""
        latest_scan = self.scans.filter(status="success").first()
        if latest_scan:
            return latest_scan.ports.filter(state="open").count()
        return 0


class ScanResult(models.Model):
    """Represents a single scan execution for a host"""

    host = models.ForeignKey(Host, on_delete=models.CASCADE, related_name="scans")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("running", "Running"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        default="running",
    )
    error_message = models.TextField(blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["host", "-started_at"]),
        ]

    def __str__(self):
        return f"Scan of {self.host.name} at {self.started_at}"


class PortScan(models.Model):
    """Individual port scan result"""

    scan_result = models.ForeignKey(ScanResult, on_delete=models.CASCADE, related_name="ports")
    port = models.IntegerField()
    protocol = models.CharField(max_length=10, default="tcp")
    state = models.CharField(
        max_length=20,
        choices=[
            ("open", "Open"),
            ("closed", "Closed"),
            ("filtered", "Filtered"),
        ],
    )
    service_name = models.CharField(max_length=100, blank=True)
    service_version = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["port"]
        indexes = [
            models.Index(fields=["scan_result", "state"]),
        ]

    def __str__(self):
        return f"Port {self.port}/{self.protocol} - {self.state}"
