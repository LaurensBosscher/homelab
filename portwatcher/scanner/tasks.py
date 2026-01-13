import nmap
from django.conf import settings
from django.utils import timezone

from .models import Host, PortScan, ScanResult


class PortScanner:
    """Handles port scanning operations using nmap"""

    def __init__(self):
        self.nm = nmap.PortScanner()
        self.args = settings.SCANNER_NMAP_ARGS
        self.timeout = settings.SCANNER_TIMEOUT_SECONDS

    def scan_host(self, host: Host) -> ScanResult:  # type: ignore[name-defined]
        """Perform a full port scan on a host"""
        scan_result = ScanResult.objects.create(host=host, status="running")  # type: ignore[arg-type]

        try:
            host.last_scan_status = "scanning"  # type: ignore[arg-type]
            host.save()

            self.nm.scan(
                hosts=str(host.ip_address),
                arguments=self.args,
                timeout=self.timeout,
            )

            if str(host.ip_address) in self.nm.all_hosts():
                self._parse_scan_results(scan_result, str(host.ip_address))
                scan_result.status = "success"  # type: ignore[arg-type]
            else:
                scan_result.status = "failed"  # type: ignore[arg-type]
                scan_result.error_message = "Host not found in scan results"

        except Exception as e:
            scan_result.status = "failed"  # type: ignore[arg-type]
            scan_result.error_message = str(e)
            host.last_scan_status = "failed"  # type: ignore[arg-type]
        else:
            host.last_scan_status = "success"  # type: ignore[arg-type]
        finally:
            scan_result.completed_at = timezone.now()
            scan_result.duration_seconds = (
                scan_result.completed_at - scan_result.started_at  # type: ignore[operator]
            ).total_seconds()
            scan_result.save()

            host.last_scan_at = timezone.now()  # type: ignore[arg-type]
            host.save()

        return scan_result

    def _parse_scan_results(self, scan_result: ScanResult, ip: str) -> None:  # type: ignore[name-defined]
        """Parse nmap results and create PortScan records"""
        for proto in self.nm[ip].all_protocols():
            ports = self.nm[ip][proto].keys()

            for port in ports:
                port_info = self.nm[ip][proto][port]

                PortScan.objects.create(  # type: ignore[arg-type]
                    scan_result=scan_result,
                    port=port,
                    protocol=proto,
                    state=port_info.get("state", "unknown"),
                    service_name=port_info.get("name", ""),
                    service_version=port_info.get("product", "")
                    + (" " + port_info.get("version", "")).strip(),
                )
