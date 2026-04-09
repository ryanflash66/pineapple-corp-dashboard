import argparse
import json
import sys
from typing import Any, Dict, Iterable, List, Tuple


INSTRUCTION_TEXT = (
    "Create a detailed incident response playbook for the following cyber incident."
)


REQUIRED_ENTRY_KEYS = [
    "incident_type",
    "target_asset",
    "detection_source",
    "initial_vector",
    "tactics_techniques",
    "severity",
    "playbook_steps",
    "final_status",
    "response_duration_total_min",
    "tags",
]


def warn(message: str) -> None:
    print(f"[WARN] {message}", file=sys.stderr)


def render_playbook(entry: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("Playbook:")
    lines.append("")

    steps = entry.get("playbook_steps", [])
    if not isinstance(steps, list):
        warn("playbook_steps is not a list; rendering empty playbook steps")
        steps = []

    for idx, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            warn(f"playbook_steps[{idx}] is not an object; skipping step")
            continue

        phase = step.get("phase", "")
        action = step.get("action", "")
        tools_value = step.get("tools", [])
        response_time = step.get("response_time_min", "")

        if isinstance(tools_value, list):
            tools = ", ".join(str(t) for t in tools_value)
        else:
            tools = str(tools_value)

        lines.append(f"Phase: {phase}")
        lines.append(f"Action: {action}")
        lines.append(f"Tools: {tools}")
        lines.append(f"Target response time (minutes): {response_time}")
        lines.append("")

    lines.append(f"Final status: {entry.get('final_status', '')}")
    lines.append(
        "Total response duration (minutes): "
        f"{entry.get('response_duration_total_min', '')}"
    )
    return "\n".join(lines)


def build_tactics_text(tactics_techniques: Any) -> str:
    if not isinstance(tactics_techniques, list):
        warn("tactics_techniques is not a list; rendering empty tactics list")
        return ""

    lines: List[str] = []
    for idx, item in enumerate(tactics_techniques, start=1):
        if not isinstance(item, dict):
            warn(f"tactics_techniques[{idx}] is not an object; skipping")
            continue
        tactic = str(item.get("tactic", "")).strip()
        technique = str(item.get("technique", "")).strip()
        if not tactic and not technique:
            warn(f"tactics_techniques[{idx}] missing tactic/technique; skipping")
            continue
        if not tactic:
            tactic = "Unknown"
        if not technique:
            technique = "Unknown"
        lines.append(f"- {tactic}: {technique}")
    return "\n".join(lines)


def build_tags_text(tags: Any) -> str:
    if isinstance(tags, list):
        return ", ".join(str(tag) for tag in tags)
    if tags is None:
        return ""
    return str(tags)


def validate_entry(entry: Dict[str, Any]) -> Tuple[bool, List[str]]:
    missing = [key for key in REQUIRED_ENTRY_KEYS if key not in entry]
    return (len(missing) == 0, missing)


def iter_jsonl(path: str) -> Iterable[Tuple[int, Dict[str, Any]]]:
    with open(path, "r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                yield line_no, json.loads(raw)
            except json.JSONDecodeError as exc:
                warn(f"Line {line_no}: JSON decode error: {exc}")
                continue


def convert(input_path: str, output_path: str) -> Tuple[int, int]:
    total = 0
    written = 0

    with open(output_path, "w", encoding="utf-8") as out:
        for line_no, entry in iter_jsonl(input_path):
            total += 1
            if not isinstance(entry, dict):
                warn(f"Line {line_no}: entry is not an object; skipping")
                continue

            valid, missing = validate_entry(entry)
            if not valid:
                warn(
                    f"Line {line_no}: missing keys {missing}; skipping entry"
                )
                continue

            tactics_text = build_tactics_text(entry.get("tactics_techniques"))
            tags_text = build_tags_text(entry.get("tags"))
            playbook_text = render_playbook(entry)

            record = {
                "instruction": INSTRUCTION_TEXT,
                "input": (
                    f"Incident type: {entry.get('incident_type', '')}\n"
                    f"Target asset: {entry.get('target_asset', '')}\n"
                    f"Detection source: {entry.get('detection_source', '')}\n"
                    f"Initial vector: {entry.get('initial_vector', '')}\n"
                    f"Tactics and techniques:\n{tactics_text}\n"
                    f"Severity: {entry.get('severity', '')}\n"
                    f"Tags: {tags_text}"
                ),
                "output": playbook_text,
            }

            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1

    return total, written


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convert incident response playbook JSONL to Alpaca-style JSONL."
        )
    )
    parser.add_argument(
        "--input",
        default="dataset/incident_response_playbook_dataset.jsonl",
        help="Path to source JSONL file.",
    )
    parser.add_argument(
        "--output",
        default="ir_playbooks_alpaca.jsonl",
        help="Path to output Alpaca JSONL file.",
    )
    args = parser.parse_args()

    total, written = convert(args.input, args.output)
    print(f"Processed {total} entries, wrote {written} records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
