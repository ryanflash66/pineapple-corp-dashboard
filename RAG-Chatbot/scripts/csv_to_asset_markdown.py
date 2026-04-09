"""Convert an asset inventory CSV into structured JSON + retrieval-friendly Markdown.

Usage:
    python scripts/csv_to_asset_markdown.py                          # uses default paths
    python scripts/csv_to_asset_markdown.py --input my_assets.csv    # custom CSV
    python scripts/csv_to_asset_markdown.py --output-md data/assets.md  # custom output
"""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

DEFAULT_INPUT = os.path.join(PROJECT_ROOT, "templates", "asset_inventory_template.csv")
DEFAULT_OUTPUT_MD = os.path.join(PROJECT_ROOT, "data", "asset_inventory.md")
DEFAULT_OUTPUT_JSON = os.path.join(PROJECT_ROOT, "data", "asset_inventory.json")

# Maps the CSV "type" column to an IR-relevant category for retrieval grouping.
CATEGORY_MAP = {
    # Endpoint Protection
    "workstation": "Endpoint Protection",
    "laptop": "Endpoint Protection",
    "server": "Endpoint Protection",
    "mobile": "Endpoint Protection",
    # Network Security
    "firewall": "Network Security",
    "ids": "Network Security",
    "ips": "Network Security",
    "proxy": "Network Security",
    "waf": "Network Security",
    "nac": "Network Security",
    "vpn": "Network Security",
    # Identity & Access
    "domain_controller": "Identity & Access",
    "ldap": "Identity & Access",
    "mfa": "Identity & Access",
    "pam": "Identity & Access",
    "sso": "Identity & Access",
    # Monitoring & Logging
    "siem": "Monitoring & Logging",
    "log_collector": "Monitoring & Logging",
    "ndr": "Monitoring & Logging",
    "edr": "Monitoring & Logging",
    # Servers & Critical Services
    "database": "Servers & Critical Services",
    "web_server": "Servers & Critical Services",
    "file_server": "Servers & Critical Services",
    "email_server": "Servers & Critical Services",
    "dns": "Servers & Critical Services",
    "dhcp": "Servers & Critical Services",
    # Backup & Recovery
    "backup": "Backup & Recovery",
    "dr_site": "Backup & Recovery",
    "nas": "Backup & Recovery",
    # Network Topology
    "switch": "Network Topology",
    "router": "Network Topology",
    "access_point": "Network Topology",
    "load_balancer": "Network Topology",
}

# Ordered list so sections always appear in a consistent IR-relevant order.
CATEGORY_ORDER = [
    "Endpoint Protection",
    "Network Security",
    "Identity & Access",
    "Monitoring & Logging",
    "Servers & Critical Services",
    "Backup & Recovery",
    "Network Topology",
    "Miscellaneous",
]

def read_csv(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def classify_row(row: dict) -> str:
    asset_type = row.get("type", "").strip().lower()
    return CATEGORY_MAP.get(asset_type, "Miscellaneous")


def _format_asset_line(row: dict) -> str:
    """Build a compact bullet line from a CSV row for model-friendly retrieval."""
    name = row.get("name", "").strip()
    vendor = row.get("vendor_product", "").strip()
    asset_type = row.get("type", "").strip()
    zone = row.get("network_zone", "").strip()
    ip = row.get("ip_or_subnet", "").strip()
    role = row.get("role", "").strip()
    managed_by = row.get("managed_by", "").strip()
    criticality = row.get("criticality", "").strip()
    notes = row.get("notes", "").strip()

    parts = []
    if vendor:
        label = f"{vendor} {asset_type}" if asset_type else vendor
    elif asset_type:
        label = asset_type
    else:
        label = "unknown"
    parts.append(label)

    if zone and ip:
        parts.append(f"{zone} ({ip})")
    elif zone:
        parts.append(zone)
    elif ip:
        parts.append(ip)

    if role:
        parts.append(role)
    if managed_by:
        parts.append(f"managed by {managed_by}")
    if notes:
        parts.append(notes)
    if criticality:
        parts.append(f"{criticality} criticality")

    return f"- {name}: {', '.join(parts)}"


def build_markdown(groups: dict[str, list[dict]]) -> str:
    lines = [
        "# Organization Asset Inventory",
        "",
    ]

    for category in CATEGORY_ORDER:
        rows = groups.get(category, [])
        if not rows:
            continue

        lines.append(f"## {category}")
        lines.append("")
        for row in rows:
            lines.append(_format_asset_line(row))
        lines.append("")

    return "\n".join(lines)


def build_json(rows: list[dict], connector: str = "unknown") -> str:
    """Build a structured JSON representation of assets (source of truth format)."""
    data = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "connector": connector,
            "total_assets": len(rows),
        },
        "assets": rows,
    }
    return json.dumps(data, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Convert asset inventory CSV to JSON + Markdown formats.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help=f"Path to input CSV (default: {DEFAULT_INPUT})")
    parser.add_argument("--output-md", default=DEFAULT_OUTPUT_MD, help=f"Path to output Markdown (default: {DEFAULT_OUTPUT_MD})")
    parser.add_argument("--output-json", default=DEFAULT_OUTPUT_JSON, help=f"Path to output JSON (default: {DEFAULT_OUTPUT_JSON})")
    parser.add_argument("--connector", default="csv", help="Connector name for JSON metadata")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input CSV not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    rows = read_csv(args.input)
    if not rows:
        print("Error: CSV is empty or has no data rows.", file=sys.stderr)
        sys.exit(1)

    groups = defaultdict(list)
    for row in rows:
        category = classify_row(row)
        groups[category].append(row)

    # Write JSON (source of truth)
    json_content = build_json(rows, connector=args.connector)
    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        f.write(json_content)

    # Write Markdown (for RAG retrieval)
    markdown = build_markdown(groups)
    os.makedirs(os.path.dirname(args.output_md), exist_ok=True)
    with open(args.output_md, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Converted {len(rows)} assets:")
    print(f"  JSON (source of truth): {args.output_json}")
    print(f"  Markdown (RAG retrieval): {args.output_md}")
    print("Assets per category:")
    for category in CATEGORY_ORDER:
        count = len(groups.get(category, []))
        if count > 0:
            print(f"  {category}: {count}")


if __name__ == "__main__":
    main()
