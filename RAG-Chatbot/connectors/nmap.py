"""Nmap connector -- discovers live hosts via ping scan."""

import shutil
import subprocess
import xml.etree.ElementTree as ET

from connectors.base import AssetConnector


class NmapConnector(AssetConnector):
    """Runs ``nmap -sn`` (host discovery) and converts results to asset dicts."""

    def __init__(self, target: str, nmap_extra_args: str = ""):
        self.target = target
        self.nmap_extra_args = nmap_extra_args

    def fetch_assets(self) -> list[dict]:
        nmap_path = shutil.which("nmap")
        if nmap_path is None:
            raise FileNotFoundError(
                "Nmap is not installed or not on PATH. "
                "Install from https://nmap.org/download.html and ensure "
                "'nmap' is available in your terminal."
            )

        cmd = ["nmap", "-sn", "-oX", "-", self.target]
        if self.nmap_extra_args:
            cmd[1:1] = self.nmap_extra_args.split()

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Nmap scan failed (exit code {result.returncode}):\n"
                f"{result.stderr.strip()}"
            )

        return self._parse_xml(result.stdout)

    def _parse_xml(self, xml_text: str) -> list[dict]:
        root = ET.fromstring(xml_text)
        assets = []

        for host in root.findall("host"):
            status = host.find("status")
            if status is None or status.get("state") != "up":
                continue

            addr_el = host.find("address[@addrtype='ipv4']")
            if addr_el is None:
                addr_el = host.find("address[@addrtype='ipv6']")
            if addr_el is None:
                continue
            ip = addr_el.get("addr", "")

            mac_el = host.find("address[@addrtype='mac']")
            vendor = mac_el.get("vendor", "") if mac_el is not None else ""

            hostname_el = host.find(".//hostname")
            hostname = hostname_el.get("name", "") if hostname_el is not None else ""

            name = hostname if hostname else f"host-{ip.replace('.', '-')}"
            asset_type = self._infer_type(name, vendor)

            assets.append({
                "name": name,
                "type": asset_type,
                "vendor_product": vendor,
                "network_zone": "discovered",
                "ip_or_subnet": ip,
                "role": "discovered via nmap scan",
                "managed_by": "",
                "criticality": "unknown",
                "notes": f"hostname: {hostname}" if hostname else "no reverse DNS",
            })

        return assets

    @staticmethod
    def _infer_type(hostname: str, vendor: str) -> str:
        """Best-effort type classification from hostname/vendor strings."""
        h = hostname.lower()
        v = vendor.lower()

        if any(kw in h for kw in ("fw", "firewall", "palo", "fortigate")):
            return "firewall"
        if any(kw in h for kw in ("sw-", "switch", "catalyst")):
            return "switch"
        if any(kw in h for kw in ("rt-", "router", "isr", "gateway")):
            return "router"
        if any(kw in h for kw in ("ap-", "meraki", "unifi")):
            return "access_point"
        if any(kw in h for kw in ("srv", "server", "dc-", "esxi")):
            return "server"
        if any(kw in h for kw in ("ws-", "desktop", "pc-")):
            return "workstation"
        if any(kw in h for kw in ("laptop", "nb-")):
            return "laptop"
        if "printer" in h or "print" in v:
            return "workstation"

        return "workstation"
