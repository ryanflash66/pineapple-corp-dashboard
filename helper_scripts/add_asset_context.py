"""Inject asset context into the deduped training dataset.

Phase 1 (this script): Adds "Organization assets:" block to the input field
of ~80% of rows. The remaining ~20% are kept in original format so the model
learns to handle queries with and without asset context.

Phase 2 (separate LLM-assisted step): Rewrites the output field of asset-aware
rows to reference specific hostnames, IPs, and tool names from the injected
asset context.

Usage:
    python helper_scripts/add_asset_context.py
    python helper_scripts/add_asset_context.py --input datasets/custom.jsonl
"""

import argparse
import json
import os
import random
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

sys.path.insert(0, PROJECT_ROOT)
from helper_scripts.asset_profiles import get_asset_context, INCIDENT_TYPE_TO_PROFILE  # noqa: E402

DEFAULT_INPUT = os.path.join(PROJECT_ROOT, "datasets", "ir_playbooks_alpaca_deduped.jsonl")
DEFAULT_OUTPUT = os.path.join(PROJECT_ROOT, "datasets", "ir_playbooks_alpaca_with_assets.jsonl")

# Target: 80% asset-aware, 20% original format
ORIGINAL_FORMAT_RATIO = 0.20
RANDOM_SEED = 42


def parse_incident_type(input_text: str) -> str | None:
    """Extract 'Incident type: ...' from the input field."""
    for line in input_text.split("\n"):
        if line.startswith("Incident type:"):
            return line.replace("Incident type:", "").strip()
    return None


def select_original_rows(rows: list[dict], target_count: int) -> set[int]:
    """Select which row indices to keep in original (no-asset) format.

    Strategy: ensure at least 1 row per incident type stays original,
    prioritizing rare types. Fill remaining slots randomly.
    """
    random.seed(RANDOM_SEED)

    # Group row indices by incident type
    type_to_indices: dict[str, list[int]] = {}
    for i, row in enumerate(rows):
        itype = parse_incident_type(row.get("input", ""))
        if itype:
            type_to_indices.setdefault(itype, []).append(i)

    selected: set[int] = set()

    # Phase 1: pick 1 row per incident type (ensures coverage)
    for itype, indices in type_to_indices.items():
        pick = random.choice(indices)
        selected.add(pick)

    # Phase 2: if we haven't hit target_count, add more from types with
    # many rows (weighted by count, so common types donate more to "original")
    remaining_pool = [i for i in range(len(rows)) if i not in selected]
    random.shuffle(remaining_pool)
    while len(selected) < target_count and remaining_pool:
        selected.add(remaining_pool.pop())

    return selected


def main():
    parser = argparse.ArgumentParser(description="Add asset context to training data inputs.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help=f"Input JSONL (default: {DEFAULT_INPUT})")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help=f"Output JSONL (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--ratio", type=float, default=ORIGINAL_FORMAT_RATIO,
                        help="Fraction of rows to keep without assets (default: 0.20)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Read all rows
    with open(args.input, "r", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(rows)} rows from {args.input}")

    # Determine which rows stay in original format
    target_original = round(len(rows) * args.ratio)
    original_indices = select_original_rows(rows, target_original)

    # Process each row
    asset_aware_count = 0
    original_count = 0
    unmapped_count = 0
    output_rows = []

    for i, row in enumerate(rows):
        itype = parse_incident_type(row.get("input", ""))

        if i in original_indices:
            # Keep original format (no asset context)
            output_rows.append(row)
            original_count += 1
            continue

        if itype is None:
            print(f"  Warning: row {i} has no 'Incident type:' field, keeping original", file=sys.stderr)
            output_rows.append(row)
            unmapped_count += 1
            continue

        asset_block = get_asset_context(itype)
        if asset_block is None:
            print(f"  Warning: no profile for incident type '{itype}' (row {i}), keeping original", file=sys.stderr)
            output_rows.append(row)
            unmapped_count += 1
            continue

        # Inject asset context into input
        new_row = dict(row)
        new_row["input"] = row["input"] + "\n\n" + asset_block
        # Mark for Phase 2 output rewriting (metadata field, not used in training)
        new_row["_asset_aware"] = True
        output_rows.append(new_row)
        asset_aware_count += 1

    # Write output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for row in output_rows:
            f.write(json.dumps(row) + "\n")

    print(f"\nResults:")
    print(f"  Asset-aware rows: {asset_aware_count}")
    print(f"  Original format rows: {original_count}")
    if unmapped_count:
        print(f"  Unmapped (kept original): {unmapped_count}")
    print(f"  Total: {len(output_rows)}")
    print(f"\nWritten to: {args.output}")
    print(f"\nNext step: Run LLM-assisted output rewriting on the {asset_aware_count} asset-aware rows")
    print(f"  (rows with '_asset_aware': true need their 'output' field updated)")


if __name__ == "__main__":
    main()
