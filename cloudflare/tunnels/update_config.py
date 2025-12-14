#!/usr/bin/env python3
"""
Cloudflare Tunnel Configuration Manager

This script synchronizes local tunnel configuration (config.yml) with Cloudflare's API.
It reads the local config, fetches existing tunnel routes from Cloudflare, and determines
what needs to be created, updated, or deleted. Also manages DNS CNAME records.
"""

import os
import sys
import yaml
import requests
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class OriginRequest(BaseModel):
    """Origin request configuration options."""

    noTLSVerify: Optional[bool] = Field(default=None, alias="noTLSVerify")

    class Config:
        populate_by_name = True
        extra = "allow"


class TunnelRoute(BaseModel):
    """Represents a single tunnel route configuration."""

    hostname: str = Field(..., description="The hostname to route")
    service: str = Field(..., description="The backend service URL")
    originRequest: Optional[OriginRequest] = Field(default=None, alias="originRequest")

    class Config:
        populate_by_name = True

    def __hash__(self) -> int:
        return hash(self.hostname)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TunnelRoute):
            return False
        return (
            self.hostname == other.hostname
            and self.service == other.service
            and self.originRequest == other.originRequest
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Cloudflare API format."""
        route: Dict[str, Any] = {"hostname": self.hostname, "service": self.service}
        if self.originRequest:
            route["originRequest"] = self.originRequest.model_dump(
                by_alias=True, exclude_none=True
            )

        return route


class CloudflareAPIResponse(BaseModel):
    """Cloudflare API response structure."""

    success: bool
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    result: Optional[Dict[str, Any]] = None


class CloudflareListResponse(BaseModel):
    """Cloudflare API list response structure."""

    success: bool
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    result: List[Dict[str, Any]] = Field(default_factory=list)


class DNSRecord(BaseModel):
    """DNS record model."""

    id: Optional[str] = None
    type: str = Field(..., description="DNS record type (e.g., CNAME)")
    name: str = Field(..., description="DNS record name")
    content: str = Field(..., description="DNS record content")
    proxied: bool = Field(default=True, description="Whether the record is proxied")
    ttl: int = Field(default=1, description="TTL (1 for automatic)")

    class Config:
        extra = "allow"


class TunnelConfig(BaseModel):
    """Complete tunnel configuration."""

    ingress: List[Dict[str, Any]] = Field(..., description="List of ingress rules")


class CloudflareAPI:
    """Handle Cloudflare API interactions."""

    BASE_URL: str = "https://api.cloudflare.com/client/v4"

    def __init__(
        self,
        api_token: str,
        account_id: str,
        tunnel_id: str,
        zone_id: str,
    ) -> None:
        self.api_token: str = api_token
        self.account_id: str = account_id
        self.tunnel_id: str = tunnel_id
        self.zone_id: str = zone_id
        self.tunnel_domain: str = f"{tunnel_id}.cfargotunnel.com"
        self.headers: Dict[str, str] = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

    def get_tunnel_configuration(self) -> CloudflareAPIResponse:
        """Retrieve current tunnel configuration from Cloudflare."""
        url: str = f"{self.BASE_URL}/accounts/{self.account_id}/cfd_tunnel/{self.tunnel_id}/configurations"
        response: requests.Response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        return CloudflareAPIResponse(**response.json())

    def update_tunnel_configuration(
        self, config: TunnelConfig
    ) -> CloudflareAPIResponse:
        """Update the entire tunnel configuration."""
        url: str = f"{self.BASE_URL}/accounts/{self.account_id}/cfd_tunnel/{self.tunnel_id}/configurations"
        response: requests.Response = requests.put(
            url, headers=self.headers, json={"config": config.model_dump()}
        )
        response.raise_for_status()

        return CloudflareAPIResponse(**response.json())

    def list_dns_records(self, name: Optional[str] = None) -> CloudflareListResponse:
        """List DNS records, optionally filtered by name."""
        url: str = f"{self.BASE_URL}/zones/{self.zone_id}/dns_records"
        params: Dict[str, str] = {}
        if name:
            params["name"] = name

        response: requests.Response = requests.get(
            url, headers=self.headers, params=params
        )
        response.raise_for_status()

        return CloudflareListResponse(**response.json())

    def create_dns_record(self, record: DNSRecord) -> CloudflareAPIResponse:
        """Create a DNS record."""
        url: str = f"{self.BASE_URL}/zones/{self.zone_id}/dns_records"
        response: requests.Response = requests.post(
            url,
            headers=self.headers,
            json=record.model_dump(exclude={"id"}, exclude_none=True),
        )
        response.raise_for_status()

        return CloudflareAPIResponse(**response.json())

    def update_dns_record(
        self, record_id: str, record: DNSRecord
    ) -> CloudflareAPIResponse:
        """Update a DNS record."""
        url: str = f"{self.BASE_URL}/zones/{self.zone_id}/dns_records/{record_id}"
        response: requests.Response = requests.put(
            url,
            headers=self.headers,
            json=record.model_dump(exclude={"id"}, exclude_none=True),
        )
        response.raise_for_status()

        return CloudflareAPIResponse(**response.json())

    def delete_dns_record(self, record_id: str) -> CloudflareAPIResponse:
        """Delete a DNS record."""
        url: str = f"{self.BASE_URL}/zones/{self.zone_id}/dns_records/{record_id}"
        response: requests.Response = requests.delete(url, headers=self.headers)
        response.raise_for_status()

        return CloudflareAPIResponse(**response.json())


class RouteActions(BaseModel):
    """Actions to be performed on routes."""

    create: List[TunnelRoute] = Field(default_factory=list)
    update: List[TunnelRoute] = Field(default_factory=list)
    delete: List[TunnelRoute] = Field(default_factory=list)

    def has_changes(self) -> bool:
        """Check if there are any changes to apply."""
        return bool(self.create or self.update or self.delete)


class TunnelConfigManager:
    """Manage tunnel configuration synchronization."""

    def __init__(
        self,
        config_path: str,
        api: CloudflareAPI,
        manage_dns: bool = True,
    ) -> None:
        self.config_path: str = config_path
        self.api: CloudflareAPI = api
        self.manage_dns: bool = manage_dns

    def load_local_config(self) -> List[TunnelRoute]:
        """Load tunnel routes from local config.yml file."""
        with open(self.config_path, "r") as f:
            data: Any = yaml.safe_load(f)

        if not isinstance(data, list):
            raise ValueError("Config file must contain a list of routes")

        routes: List[TunnelRoute] = []
        for item in data:
            route = TunnelRoute(**item)
            routes.append(route)

        return routes

    def get_cloudflare_routes(self) -> List[TunnelRoute]:
        """Retrieve current routes from Cloudflare."""
        try:
            response: CloudflareAPIResponse = self.api.get_tunnel_configuration()

            if not response.result:
                print(
                    "Warning: No tunnel configuration found. Will create new configuration."
                )
                return []

            config: Dict[str, Any] = response.result.get("config", {})
            ingress_rules: List[Dict[str, Any]] = config.get("ingress", [])

            routes: List[TunnelRoute] = []
            # Skip the last rule which is the catch-all (no hostname)
            for rule in ingress_rules:
                if "hostname" in rule:
                    route = TunnelRoute(**rule)
                    routes.append(route)

            return routes
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 404:
                print(
                    "Warning: Tunnel configuration not found. Will create new configuration."
                )
                return []
            raise

    def compare_routes(
        self,
        local: List[TunnelRoute],
        remote: List[TunnelRoute],
    ) -> RouteActions:
        """Compare local and remote routes to determine actions needed."""
        local_dict: Dict[str, TunnelRoute] = {r.hostname: r for r in local}
        remote_dict: Dict[str, TunnelRoute] = {r.hostname: r for r in remote}

        local_hostnames: set[str] = set(local_dict.keys())
        remote_hostnames: set[str] = set(remote_dict.keys())

        actions = RouteActions()

        # Routes that exist locally but not remotely -> create
        for hostname in local_hostnames - remote_hostnames:
            actions.create.append(local_dict[hostname])

        # Routes that exist remotely but not locally -> delete
        for hostname in remote_hostnames - local_hostnames:
            actions.delete.append(remote_dict[hostname])

        # Routes that exist in both -> check if they need updating
        for hostname in local_hostnames & remote_hostnames:
            if local_dict[hostname] != remote_dict[hostname]:
                actions.update.append(local_dict[hostname])

        return actions

    def build_cloudflare_config(self, routes: List[TunnelRoute]) -> TunnelConfig:
        """Build the complete Cloudflare tunnel configuration."""
        ingress_rules: List[Dict[str, Any]] = [route.to_dict() for route in routes]

        # Add catch-all rule (required by Cloudflare)
        ingress_rules.append({"service": "http_status:404"})

        return TunnelConfig(ingress=ingress_rules)

    def get_existing_dns_records(self) -> Dict[str, DNSRecord]:
        """Get existing DNS records for tunnel hostnames."""
        records: Dict[str, DNSRecord] = {}

        try:
            response: CloudflareListResponse = self.api.list_dns_records()
            for record_data in response.result:
                if record_data.get("type") == "CNAME" and record_data.get(
                    "content", ""
                ).endswith(".cfargotunnel.com"):
                    record = DNSRecord(**record_data)
                    records[record.name] = record
        except requests.exceptions.HTTPError as e:
            print(f"Warning: Failed to fetch DNS records: {e}")

        return records

    def sync_dns_records(
        self,
        routes: List[TunnelRoute],
        dry_run: bool = False,
    ) -> None:
        """Synchronize DNS records for tunnel routes."""
        if not self.manage_dns:
            return

        print("\n📋 Synchronizing DNS records...")

        # Get existing DNS records
        existing_records: Dict[str, DNSRecord] = self.get_existing_dns_records()

        # Determine required hostnames from routes
        required_hostnames: set[str] = {route.hostname for route in routes}
        existing_hostnames: set[str] = set(existing_records.keys())

        dns_create: List[str] = []
        dns_update: List[str] = []
        dns_delete: List[str] = []

        # Find DNS records to create
        for hostname in required_hostnames - existing_hostnames:
            dns_create.append(hostname)

        # Find DNS records to update (if pointing to wrong tunnel)
        for hostname in required_hostnames & existing_hostnames:
            if existing_records[hostname].content != self.api.tunnel_domain:
                dns_update.append(hostname)

        # Find DNS records to delete
        for hostname in existing_hostnames - required_hostnames:
            dns_delete.append(hostname)

        # Display planned DNS actions
        if dns_create:
            print(f"\n✨ DNS Records to CREATE ({len(dns_create)}):")
            for hostname in dns_create:
                print(f"  + {hostname} -> {self.api.tunnel_domain}")

        if dns_update:
            print(f"\n🔄 DNS Records to UPDATE ({len(dns_update)}):")
            for hostname in dns_update:
                print(f"  ~ {hostname} -> {self.api.tunnel_domain}")

        if dns_delete:
            print(f"\n🗑️  DNS Records to DELETE ({len(dns_delete)}):")
            for hostname in dns_delete:
                print(f"  - {hostname}")

        if not (dns_create or dns_update or dns_delete):
            print("✅ DNS records are already in sync")
            return

        if dry_run:
            return

        # Apply DNS changes
        try:
            for hostname in dns_create:
                record = DNSRecord(
                    type="CNAME",
                    name=hostname,
                    content=self.api.tunnel_domain,
                    proxied=True,
                    ttl=1,
                )
                self.api.create_dns_record(record)
                print(f"  ✓ Created DNS record for {hostname}")

            for hostname in dns_update:
                existing = existing_records[hostname]
                if existing.id:
                    record = DNSRecord(
                        type="CNAME",
                        name=hostname,
                        content=self.api.tunnel_domain,
                        proxied=True,
                        ttl=1,
                    )
                    self.api.update_dns_record(existing.id, record)
                    print(f"  ✓ Updated DNS record for {hostname}")

            for hostname in dns_delete:
                existing = existing_records[hostname]
                if existing.id:
                    self.api.delete_dns_record(existing.id)
                    print(f"  ✓ Deleted DNS record for {hostname}")

            print("✅ DNS records synchronized successfully")
        except requests.exceptions.HTTPError as e:
            print(f"❌ Error updating DNS records: {e}")
            if hasattr(e.response, "text"):
                print(f"Response: {e.response.text}")
            sys.exit(1)

    def sync(
        self,
        dry_run: bool = False,
    ) -> None:
        """Synchronize local configuration with Cloudflare."""
        print("Loading local configuration...")
        local_routes: List[TunnelRoute] = self.load_local_config()
        print(f"Found {len(local_routes)} routes in local config")

        print("\nFetching current Cloudflare configuration...")
        remote_routes: List[TunnelRoute] = self.get_cloudflare_routes()
        print(f"Found {len(remote_routes)} routes in Cloudflare")

        print("\nAnalyzing differences...")
        actions: RouteActions = self.compare_routes(local_routes, remote_routes)

        # Display planned actions
        if actions.create:
            print(f"\n✨ Routes to CREATE ({len(actions.create)}):")
            for route in actions.create:
                print(f"  + {route.hostname} -> {route.service}")

        if actions.update:
            print(f"\n🔄 Routes to UPDATE ({len(actions.update)}):")
            for route in actions.update:
                print(f"  ~ {route.hostname} -> {route.service}")

        if actions.delete:
            print(f"\n🗑️  Routes to DELETE ({len(actions.delete)}):")
            for route in actions.delete:
                print(f"  - {route.hostname} -> {route.service}")

        if not actions.has_changes():
            print("\n✅ Configuration is already in sync. No changes needed.")
        else:
            # Apply changes
            if dry_run:
                print("\n🔍 DRY RUN - No changes will be applied")
            else:
                print("\n📝 Applying changes to Cloudflare...")
                new_config: TunnelConfig = self.build_cloudflare_config(local_routes)

                try:
                    self.api.update_tunnel_configuration(new_config)
                    print("✅ Successfully updated Cloudflare tunnel configuration")
                except requests.exceptions.HTTPError as e:
                    print(f"❌ Error updating configuration: {e}")
                    if hasattr(e.response, "text"):
                        print(f"Response: {e.response.text}")
                    sys.exit(1)

        # Sync DNS records
        self.sync_dns_records(local_routes, dry_run=dry_run)


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Synchronize Cloudflare tunnel configuration"
    )
    parser.add_argument(
        "--config",
        default="config.yml",
        help="Path to local config.yml file (default: config.yml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without applying changes",
    )
    parser.add_argument(
        "--no-dns", action="store_true", help="Skip DNS record management"
    )

    args = parser.parse_args()

    # Get credentials from environment variables
    api_token: Optional[str] = os.getenv("CLOUDFLARE_API_TOKEN")
    account_id: Optional[str] = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    tunnel_id: Optional[str] = os.getenv("CLOUDFLARE_TUNNEL_ID")
    zone_id: Optional[str] = os.getenv("CLOUDFLARE_ZONE_ID")

    if not all([api_token, account_id, tunnel_id]):
        print("Error: Missing required environment variables:")
        if not api_token:
            print("  - CLOUDFLARE_API_TOKEN")
        if not account_id:
            print("  - CLOUDFLARE_ACCOUNT_ID")
        if not tunnel_id:
            print("  - CLOUDFLARE_TUNNEL_ID")
        sys.exit(1)

    # Check for zone_id if DNS management is enabled
    if not args.no_dns and not zone_id:
        print("Error: CLOUDFLARE_ZONE_ID is required for DNS management")
        print("  Set CLOUDFLARE_ZONE_ID or use --no-dns to skip DNS management")
        sys.exit(1)

    # Initialize API and manager
    api: CloudflareAPI = CloudflareAPI(
        api_token,
        account_id,
        tunnel_id,
        zone_id or "",  # type: ignore
    )
    manager: TunnelConfigManager = TunnelConfigManager(
        args.config,
        api,
        manage_dns=not args.no_dns,
    )

    # Perform sync
    try:
        manager.sync(dry_run=args.dry_run)
    except FileNotFoundError:
        print(f"Error: Configuration file '{args.config}' not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in configuration file: {e}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Error: API request failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
