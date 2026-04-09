"""Deduplicate ir_playbooks_alpaca.jsonl by exact JSON match.

Reads the original 173-row dataset, removes exact duplicate rows,
and writes the deduped version.
"""

import json
import sys

INPUT = r"r:\Dropbox\_Code\Projects\irp\datasets\ir_playbooks_alpaca.jsonl"
OUTPUT = r"r:\Dropbox\_Code\Projects\irp\datasets\ir_playbooks_alpaca_deduped.jsonl"


def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"Total rows read: {len(lines)}")

    seen = set()
    unique_rows = []
    dupes = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Normalize: parse and re-serialize to handle whitespace differences
        row = json.loads(line)
        key = json.dumps(row, sort_keys=True)
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        unique_rows.append(row)

    print(f"Duplicates removed: {dupes}")
    print(f"Unique rows: {len(unique_rows)}")

    # Count incident types
    type_counts = {}
    for row in unique_rows:
        inp = row.get("input", "")
        for line in inp.split("\n"):
            if line.startswith("Incident type:"):
                itype = line.replace("Incident type:", "").strip()
                type_counts[itype] = type_counts.get(itype, 0) + 1
                break

    print("\nIncident type distribution:")
    for itype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {itype}: {count}")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        for row in unique_rows:
            f.write(json.dumps(row) + "\n")

    print(f"\nWritten to: {OUTPUT}")


if __name__ == "__main__":
    main()
