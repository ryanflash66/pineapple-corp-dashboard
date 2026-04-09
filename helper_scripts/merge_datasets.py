"""Merge rewritten base + synthetic datasets into final training file.

Combines:
  1. ir_playbooks_alpaca_rewritten.jsonl (137 rows: 110 asset-aware + 27 original)
  2. ir_playbooks_synthetic_v2.jsonl (57 rows: MITRE-grounded, generic tool names)

Deduplicates by exact output match and strips internal metadata fields.

Output: datasets/ir_playbooks_alpaca_v2_hybrid.jsonl
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

REWRITTEN = os.path.join(PROJECT_ROOT, "datasets", "Retraining job", "ir_playbooks_alpaca_rewritten.jsonl")
SYNTHETIC = os.path.join(PROJECT_ROOT, "datasets", "Retraining job", "ir_playbooks_synthetic_v2.jsonl")
OUTPUT = os.path.join(PROJECT_ROOT, "datasets", "ir_playbooks_alpaca_v2_hybrid.jsonl")

# Fields to keep in final output (strip internal metadata)
KEEP_FIELDS = {"instruction", "input", "output"}


def load_jsonl(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def clean_row(row: dict) -> dict:
    """Keep only Alpaca fields, strip metadata like _asset_aware."""
    return {k: v for k, v in row.items() if k in KEEP_FIELDS}


def main():
    # Load both datasets
    rewritten = load_jsonl(REWRITTEN)
    synthetic = load_jsonl(SYNTHETIC)
    print(f"Loaded: {len(rewritten)} rewritten + {len(synthetic)} synthetic = {len(rewritten) + len(synthetic)} total")

    # Combine
    combined = [clean_row(r) for r in rewritten] + [clean_row(r) for r in synthetic]

    # Deduplicate by exact output text
    seen_outputs = set()
    deduped = []
    dup_count = 0
    for row in combined:
        output_text = row["output"].strip()
        if output_text in seen_outputs:
            dup_count += 1
            continue
        seen_outputs.add(output_text)
        deduped.append(row)

    print(f"Duplicates removed: {dup_count}")
    print(f"Final row count: {len(deduped)}")

    # Categorize
    asset_aware = 0
    original_format = 0
    for row in deduped:
        if "Affected Assets:" in row["output"] or any(
            hostname in row["output"]
            for hostname in ["srv-dc-01", "fw-perimeter-01", "siem-splunk-01", "edr-console", "backup-veeam-01"]
        ):
            asset_aware += 1
        else:
            original_format += 1

    print(f"\nComposition:")
    print(f"  Asset-aware rows: {asset_aware}")
    print(f"  Original/generic rows: {original_format}")
    print(f"  Asset-aware ratio: {asset_aware / len(deduped) * 100:.1f}%")

    # Count incident types
    incident_types = set()
    for row in deduped:
        for line in row["input"].split("\n"):
            if line.startswith("Incident type:"):
                incident_types.add(line.replace("Incident type:", "").strip())
    print(f"  Unique incident types: {len(incident_types)}")

    # Write output
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for row in deduped:
            f.write(json.dumps(row) + "\n")

    print(f"\nWritten to: {OUTPUT}")


if __name__ == "__main__":
    main()
