from django.core.management.base import BaseCommand

from scanner.models import Host
from scanner.tasks import PortScanner


class Command(BaseCommand):
    help = "Scan all enabled hosts"

    def add_arguments(self, parser):
        parser.add_argument("--host", type=str, help="Scan specific host by name")

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        scanner = PortScanner()

        if options["host"]:
            hosts = Host.objects.filter(name=options["host"], enabled=True)  # type: ignore[arg-type]
        else:
            hosts = Host.objects.filter(enabled=True)  # type: ignore[arg-type]

        self.stdout.write(f"Scanning {hosts.count()} host(s)...")

        for host in hosts:
            self.stdout.write(f"Scanning {host.name} ({host.ip_address})...")
            scan_result = scanner.scan_host(host)

            if scan_result.status == "success":
                open_ports = scan_result.ports.filter(state="open").count()  # type: ignore[arg-type]
                msg = f"✓ {host.name}: {open_ports} open ports found"
                if scan_result.duration_seconds:
                    msg += f" ({scan_result.duration_seconds}s)"
                self.stdout.write(
                    self.style.SUCCESS(  # type: ignore[arg-type]
                        msg
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"✗ {host.name}: {scan_result.error_message}")  # type: ignore[arg-type]
                )
