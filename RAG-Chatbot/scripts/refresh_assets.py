"""Fetch live assets from the configured connector and write asset inventory.

Writes both JSON (source of truth) and Markdown (RAG retrieval) formats.

Usage:
    python scripts/refresh_assets.py                    # uses .env config
    python scripts/refresh_assets.py --connector mock   # override connector
    python scripts/refresh_assets.py --connector nmap   # override connector
"""

import argparse
import os
import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from connectors.registry import get_connector  # noqa: E402
from scripts.csv_to_asset_markdown import (  # noqa: E402
    CATEGORY_ORDER,
    build_json,
    build_markdown,
    classify_row,
    DEFAULT_OUTPUT_JSON,
    DEFAULT_OUTPUT_MD,
)


def refresh_assets(output_md: str | None = None, output_json: str | None = None, connector_name: str | None = None) -> int:
    """Run the active connector and write asset inventory in both JSON and Markdown formats.

    Args:
        output_md: Override path for markdown output
        output_json: Override path for JSON output
        connector_name: Optional connector name for JSON metadata

    Returns the number of assets written.
    """
    connector = get_connector()
    assets = connector.fetch_assets()

    if not assets:
        print("Warning: connector returned 0 assets.", file=sys.stderr)
        return 0

    groups = defaultdict(list)
    for row in assets:
        category = classify_row(row)
        groups[category].append(row)

    # Write JSON (source of truth)
    json_output = output_json or DEFAULT_OUTPUT_JSON
    json_content = build_json(assets, connector=connector_name or connector.__class__.__name__)
    os.makedirs(os.path.dirname(json_output), exist_ok=True)
    with open(json_output, "w", encoding="utf-8") as f:
        f.write(json_content)

    # Write Markdown (for RAG retrieval)
    markdown_output = output_md or DEFAULT_OUTPUT_MD
    markdown = build_markdown(groups)
    os.makedirs(os.path.dirname(markdown_output), exist_ok=True)
    with open(markdown_output, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"Asset refresh: {len(assets)} assets")
    print(f"  JSON (source of truth): {json_output}")
    print(f"  Markdown (RAG retrieval): {markdown_output}")
    for category in CATEGORY_ORDER:
        count = len(groups.get(category, []))
        if count > 0:
            print(f"  {category}: {count}")

    return len(assets)


def main():
    load_dotenv(REPO_ROOT / ".env")

    parser = argparse.ArgumentParser(
        description="Refresh asset inventory from a live connector."
    )
    parser.add_argument("--connector", help="Override ASSET_CONNECTOR env var")
    parser.add_argument("--output-md", default=None, help="Override markdown output path")
    parser.add_argument("--output-json", default=None, help="Override JSON output path")
    args = parser.parse_args()

    if args.connector:
        os.environ["ASSET_CONNECTOR"] = args.connector

    refresh_assets(output_md=args.output_md, output_json=args.output_json, connector_name=args.connector)


if __name__ == "__main__":
    main()
