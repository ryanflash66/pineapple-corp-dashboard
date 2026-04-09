"""
Validation script for IRP training datasets (Colab outputs).
Validates format, quality, asset-awareness, and synthetic-specific checks.
"""
import json
import re
import sys
from collections import Counter, defaultdict

# ─── Configuration ───────────────────────────────────────────────────────────

REWRITTEN_PATH = r"r:\Dropbox\_Code\Projects\irp\datasets\Retraining job\ir_playbooks_alpaca_rewritten.jsonl"
SYNTHETIC_PATH = r"r:\Dropbox\_Code\Projects\irp\datasets\Retraining job\ir_playbooks_synthetic_v2.jsonl"

NIST_PHASES = [
    "Identification",
    "Containment",
    "Eradication",
    "Recovery",
    "Lessons Learned",
]

REAL_TOOLS = [
    "CrowdStrike", "Falcon", "Splunk", "Palo Alto", "Veeam", "Suricata",
    "Darktrace", "Carbon Black", "Symantec", "YARA", "Wireshark", "Nessus",
    "Tenable", "CyberArk", "Duo", "Zscaler", "MISP", "Velociraptor",
    "Volatility", "hping3", "nmap", "Nmap", "McAfee", "Check Point",
    "Cisco", "VMware", "SolarWinds",
]

# Known asset hostnames from the organization inventory
KNOWN_HOSTNAMES = [
    "srv-dc-01", "srv-dc-02", "srv-web-01", "srv-db-01",
    "fw-perimeter-01", "fw-internal-01", "ids-core-01", "ndr-sensor-01",
    "siem-splunk-01", "edr-console", "backup-veeam-01", "proxy-web-01",
    "router-wan-01", "switch-core-01", "ws-corp-pool",
    "mfa-duo-01", "pam-cyberark-01", "vuln-tenable-01",
]

# IP patterns expected in asset-aware outputs
ASSET_IP_PATTERN = re.compile(r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_jsonl(path):
    """Load a JSONL file, returning (rows, errors) where errors are (line_num, error_msg)."""
    rows = []
    errors = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    obj["_line_num"] = i
                    rows.append(obj)
                except json.JSONDecodeError as e:
                    errors.append((i, str(e)))
    except FileNotFoundError:
        print(f"ERROR: File not found: {path}")
        sys.exit(1)
    return rows, errors


def count_nist_phases(output_text):
    """Return dict of phase -> bool for each NIST phase."""
    result = {}
    for phase in NIST_PHASES:
        # Check for "Phase: <name>" pattern (how the playbooks are structured)
        pattern = re.compile(r"Phase:\s*" + re.escape(phase), re.IGNORECASE)
        result[phase] = bool(pattern.search(output_text))
    return result


def count_real_tools(output_text):
    """Return list of real tools found in the output."""
    found = []
    for tool in REAL_TOOLS:
        # Case-sensitive for most, case-insensitive for nmap
        if tool.lower() == "nmap":
            if re.search(r"\bnmap\b", output_text, re.IGNORECASE):
                if tool not in found:
                    found.append(tool)
        else:
            if tool in output_text:
                found.append(tool)
    # Deduplicate overlapping entries (e.g., "CrowdStrike" and "Falcon" both from CrowdStrike Falcon)
    return list(dict.fromkeys(found))


def has_affected_assets(output_text):
    return "Affected Assets:" in output_text or "Affected Assets :" in output_text


def has_final_status(output_text):
    return "Final status:" in output_text or "Final status :" in output_text


def has_total_duration(output_text):
    return "Total response duration" in output_text


def has_hostname_references(output_text):
    """Check if output references any known hostnames."""
    for h in KNOWN_HOSTNAMES:
        if h in output_text:
            return True
    return False


def get_hostnames_found(output_text):
    """Return list of known hostnames found in output."""
    return [h for h in KNOWN_HOSTNAMES if h in output_text]


def has_ip_references(output_text):
    """Check if output references IPs matching 10.x.x.x patterns."""
    return bool(ASSET_IP_PATTERN.search(output_text))


def extract_incident_type(input_text):
    """Extract incident type from the input field."""
    m = re.search(r"Incident type:\s*(.+)", input_text)
    return m.group(1).strip() if m else "Unknown"


def has_mitre_campaign(input_text):
    """Check if detection source mentions MITRE ATT&CK Campaign."""
    return "MITRE ATT&CK Campaign" in input_text


def has_technique_ids(input_text):
    """Check if input has technique IDs like T1190, T1059."""
    return bool(re.search(r"T\d{4}", input_text))


def separator(char="=", width=90):
    return char * width


# ─── Validation per file ────────────────────────────────────────────────────

def validate_file(path, label, is_rewritten=False, is_synthetic=False):
    """Run all validation checks on a single JSONL file. Returns a results dict."""
    print(f"\n{separator()}")
    print(f"  VALIDATING: {label}")
    print(f"  File: {path}")
    print(separator())

    rows, json_errors = load_jsonl(path)
    total_lines = len(rows) + len(json_errors)

    # ── Format Checks ────────────────────────────────────────────────────────
    print(f"\n{'FORMAT CHECKS':^90}")
    print(separator("-"))

    print(f"  Total rows (including malformed): {total_lines}")
    print(f"  Valid JSON rows:                  {len(rows)}")
    print(f"  Malformed lines:                  {len(json_errors)}")
    if json_errors:
        for ln, err in json_errors[:10]:
            print(f"    Line {ln}: {err}")
        if len(json_errors) > 10:
            print(f"    ... and {len(json_errors) - 10} more")

    # Required fields
    required_fields = {"instruction", "input", "output"}
    missing_fields_rows = []
    for row in rows:
        missing = required_fields - set(row.keys())
        if missing:
            missing_fields_rows.append((row["_line_num"], missing))

    print(f"  Rows with all required fields:    {len(rows) - len(missing_fields_rows)} / {len(rows)}")
    if missing_fields_rows:
        for ln, ms in missing_fields_rows[:10]:
            print(f"    Line {ln}: missing {ms}")

    # _asset_aware metadata
    asset_aware_count = sum(1 for r in rows if "_asset_aware" in r)
    print(f"  Rows with _asset_aware field:     {asset_aware_count} / {len(rows)}")

    # ── Quality Checks on output ─────────────────────────────────────────────
    print(f"\n{'QUALITY CHECKS (output field)':^90}")
    print(separator("-"))

    # Filter to rows that have an output field
    valid_rows = [r for r in rows if "output" in r and "input" in r]

    # NIST phases
    all_five_count = 0
    phase_missing_counter = Counter()  # phase -> count of rows missing it
    rows_missing_phases = []  # (line_num, missing_phases)

    for row in valid_rows:
        phases = count_nist_phases(row["output"])
        missing = [p for p, present in phases.items() if not present]
        if not missing:
            all_five_count += 1
        else:
            for p in missing:
                phase_missing_counter[p] += 1
            rows_missing_phases.append((row["_line_num"], missing))

    pct_all5 = (all_five_count / len(valid_rows) * 100) if valid_rows else 0
    print(f"  Rows with ALL 5 NIST phases:      {all_five_count} / {len(valid_rows)}  ({pct_all5:.1f}%)")
    if phase_missing_counter:
        print(f"  Phase miss breakdown:")
        for phase in NIST_PHASES:
            cnt = phase_missing_counter.get(phase, 0)
            if cnt:
                print(f"    {phase:25s}: missing in {cnt} rows")

    # Real tools (>= 2 per row)
    tool_ok_count = 0
    tool_fail_rows = []
    for row in valid_rows:
        tools = count_real_tools(row["output"])
        if len(tools) >= 2:
            tool_ok_count += 1
        else:
            tool_fail_rows.append((row["_line_num"], tools))

    pct_tools = (tool_ok_count / len(valid_rows) * 100) if valid_rows else 0
    print(f"  Rows with >= 2 real tool names:    {tool_ok_count} / {len(valid_rows)}  ({pct_tools:.1f}%)")
    if tool_fail_rows:
        print(f"  Rows failing tool check (showing up to 15):")
        for ln, tools in tool_fail_rows[:15]:
            print(f"    Line {ln}: found {len(tools)} tool(s) -> {tools}")
        if len(tool_fail_rows) > 15:
            print(f"    ... and {len(tool_fail_rows) - 15} more")

    # Affected Assets section
    affected_count = sum(1 for r in valid_rows if has_affected_assets(r["output"]))
    pct_affected = (affected_count / len(valid_rows) * 100) if valid_rows else 0
    print(f"  Rows with 'Affected Assets:':      {affected_count} / {len(valid_rows)}  ({pct_affected:.1f}%)")

    # Final status
    final_status_count = sum(1 for r in valid_rows if has_final_status(r["output"]))
    pct_final = (final_status_count / len(valid_rows) * 100) if valid_rows else 0
    print(f"  Rows with 'Final status:':         {final_status_count} / {len(valid_rows)}  ({pct_final:.1f}%)")

    # Total response duration
    duration_count = sum(1 for r in valid_rows if has_total_duration(r["output"]))
    pct_dur = (duration_count / len(valid_rows) * 100) if valid_rows else 0
    print(f"  Rows with 'Total response dur.':   {duration_count} / {len(valid_rows)}  ({pct_dur:.1f}%)")

    # ── Asset-Awareness Checks (rewritten file) ─────────────────────────────
    if is_rewritten:
        print(f"\n{'ASSET-AWARENESS CHECKS (rewritten file)':^90}")
        print(separator("-"))

        hostname_count = sum(1 for r in valid_rows if has_hostname_references(r["output"]))
        ip_count = sum(1 for r in valid_rows if has_ip_references(r["output"]))
        no_asset_count = sum(1 for r in valid_rows
                            if not has_hostname_references(r["output"]) and not has_ip_references(r["output"]))
        asset_count = len(valid_rows) - no_asset_count

        pct_hostname = (hostname_count / len(valid_rows) * 100) if valid_rows else 0
        pct_ip = (ip_count / len(valid_rows) * 100) if valid_rows else 0
        pct_no_asset = (no_asset_count / len(valid_rows) * 100) if valid_rows else 0
        pct_asset = (asset_count / len(valid_rows) * 100) if valid_rows else 0

        print(f"  Rows referencing hostnames:        {hostname_count} / {len(valid_rows)}  ({pct_hostname:.1f}%)")
        print(f"  Rows referencing IPs (10.x.x.x):   {ip_count} / {len(valid_rows)}  ({pct_ip:.1f}%)")
        print(f"  Rows WITH asset references:        {asset_count} / {len(valid_rows)}  ({pct_asset:.1f}%)")
        print(f"  Rows WITHOUT asset references:     {no_asset_count} / {len(valid_rows)}  ({pct_no_asset:.1f}%)")
        print(f"    (Expected: ~20% without assets, ~80% with assets)")

        # Show which hostnames are most referenced
        hostname_freq = Counter()
        for r in valid_rows:
            for h in get_hostnames_found(r["output"]):
                hostname_freq[h] += 1
        if hostname_freq:
            print(f"  Hostname reference frequency (top 15):")
            for h, c in hostname_freq.most_common(15):
                print(f"    {h:25s}: {c} rows")

    # ── Synthetic-Specific Checks ────────────────────────────────────────────
    if is_synthetic:
        print(f"\n{'SYNTHETIC-SPECIFIC CHECKS':^90}")
        print(separator("-"))

        # Exact duplicate outputs
        output_texts = [r["output"] for r in valid_rows]
        output_counter = Counter(output_texts)
        duplicates = {k: v for k, v in output_counter.items() if v > 1}
        dup_row_count = sum(v for v in duplicates.values())
        unique_outputs = len(output_counter)

        print(f"  Total outputs:                     {len(output_texts)}")
        print(f"  Unique outputs:                    {unique_outputs}")
        print(f"  Duplicate output groups:           {len(duplicates)}")
        if duplicates:
            print(f"  Rows involved in duplicates:       {dup_row_count}")
            print(f"  Duplicate details (showing up to 10):")
            for i, (text, cnt) in enumerate(sorted(duplicates.items(), key=lambda x: -x[1])):
                if i >= 10:
                    print(f"    ... and {len(duplicates) - 10} more duplicate groups")
                    break
                # Find which lines
                dup_lines = [r["_line_num"] for r in valid_rows if r["output"] == text]
                snippet = text[:120].replace("\n", " ") + "..."
                print(f"    {cnt}x (lines {dup_lines}): {snippet}")

        # Also check duplicate inputs (same prompt -> might yield different outputs)
        input_texts = [r["input"] for r in valid_rows]
        input_counter = Counter(input_texts)
        input_dups = {k: v for k, v in input_counter.items() if v > 1}
        print(f"  Unique inputs:                     {len(input_counter)}")
        print(f"  Duplicate input groups:            {len(input_dups)}")
        if input_dups:
            print(f"  Duplicate input details (showing up to 10):")
            for i, (text, cnt) in enumerate(sorted(input_dups.items(), key=lambda x: -x[1])):
                if i >= 10:
                    print(f"    ... and {len(input_dups) - 10} more duplicate input groups")
                    break
                dup_lines = [r["_line_num"] for r in valid_rows if r["input"] == text]
                snippet = text[:120].replace("\n", " | ") + "..."
                print(f"    {cnt}x (lines {dup_lines}): {snippet}")

        # MITRE ATT&CK Campaign in detection source
        mitre_count = sum(1 for r in valid_rows if has_mitre_campaign(r["input"]))
        pct_mitre = (mitre_count / len(valid_rows) * 100) if valid_rows else 0
        print(f"  Rows with MITRE ATT&CK Campaign:   {mitre_count} / {len(valid_rows)}  ({pct_mitre:.1f}%)")

        # Technique IDs in input
        tech_count = sum(1 for r in valid_rows if has_technique_ids(r["input"]))
        pct_tech = (tech_count / len(valid_rows) * 100) if valid_rows else 0
        print(f"  Rows with technique IDs (Txxxx):   {tech_count} / {len(valid_rows)}  ({pct_tech:.1f}%)")

        # Unique incident types
        incident_types = Counter(extract_incident_type(r["input"]) for r in valid_rows)
        print(f"  Unique incident types:             {len(incident_types)}")
        print(f"  Incident type breakdown:")
        for it, cnt in incident_types.most_common():
            print(f"    {it:45s}: {cnt} rows")

    # ── Problem Rows Summary ─────────────────────────────────────────────────
    print(f"\n{'PROBLEM ROWS':^90}")
    print(separator("-"))

    problem_rows = defaultdict(list)  # line_num -> list of issues

    for ln, _ in json_errors:
        problem_rows[ln].append("Malformed JSON")
    for ln, ms in missing_fields_rows:
        problem_rows[ln].append(f"Missing fields: {ms}")
    for ln, missing in rows_missing_phases:
        problem_rows[ln].append(f"Missing NIST phases: {', '.join(missing)}")
    for ln, tools in tool_fail_rows:
        problem_rows[ln].append(f"< 2 real tools (found: {tools})")

    for r in valid_rows:
        ln = r["_line_num"]
        if not has_final_status(r["output"]):
            problem_rows[ln].append("Missing 'Final status:'")
        if not has_total_duration(r["output"]):
            problem_rows[ln].append("Missing 'Total response duration'")

    if problem_rows:
        print(f"  Total rows with issues: {len(problem_rows)} / {len(rows)}")
        for ln in sorted(problem_rows.keys()):
            issues = problem_rows[ln]
            print(f"    Line {ln}: {'; '.join(issues)}")
    else:
        print("  No problem rows found.")

    # ── Summary / Pass-Fail ──────────────────────────────────────────────────
    print(f"\n{'SUMMARY':^90}")
    print(separator("-"))

    issues = []
    if json_errors:
        issues.append(f"{len(json_errors)} malformed JSON lines")
    if missing_fields_rows:
        issues.append(f"{len(missing_fields_rows)} rows missing required fields")
    if pct_all5 < 90:
        issues.append(f"Only {pct_all5:.1f}% rows have all 5 NIST phases (need >= 90%)")
    if pct_tools < 80:
        issues.append(f"Only {pct_tools:.1f}% rows have >= 2 real tools (need >= 80%)")
    if pct_final < 90:
        issues.append(f"Only {pct_final:.1f}% rows have 'Final status:' (need >= 90%)")
    if pct_dur < 90:
        issues.append(f"Only {pct_dur:.1f}% rows have 'Total response duration' (need >= 90%)")

    if is_synthetic:
        if duplicates:
            issues.append(f"{len(duplicates)} duplicate output groups found ({dup_row_count} total dup rows)")
        if pct_mitre < 90:
            issues.append(f"Only {pct_mitre:.1f}% rows have MITRE ATT&CK Campaign (need >= 90%)")
        if pct_tech < 90:
            issues.append(f"Only {pct_tech:.1f}% rows have technique IDs (need >= 90%)")

    if is_rewritten:
        if pct_asset < 60:
            issues.append(f"Only {pct_asset:.1f}% rows have asset references (expected ~80%)")
        if pct_no_asset > 35:
            issues.append(f"{pct_no_asset:.1f}% rows have NO asset references (expected ~20%)")

    overall = "PASS" if not issues else "FAIL"
    print(f"  Overall: {overall}")
    print(f"  Valid rows: {len(rows)}")
    print(f"  All 5 NIST phases: {pct_all5:.1f}%")
    print(f"  >= 2 real tools:   {pct_tools:.1f}%")
    print(f"  Final status:      {pct_final:.1f}%")
    print(f"  Total duration:    {pct_dur:.1f}%")
    if is_rewritten:
        print(f"  Asset-aware rows:  {pct_asset:.1f}%")
        print(f"  No-asset rows:     {pct_no_asset:.1f}%")
    if is_synthetic:
        print(f"  Unique outputs:    {unique_outputs} / {len(output_texts)}")
        print(f"  MITRE campaigns:   {pct_mitre:.1f}%")
        print(f"  Technique IDs:     {pct_tech:.1f}%")
        print(f"  Unique incidents:  {len(incident_types)}")

    if issues:
        print(f"\n  ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print(f"\n  No issues detected.")

    return {
        "label": label,
        "overall": overall,
        "total_rows": len(rows),
        "issues": issues,
    }


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print(separator("="))
    print(f"{'IRP TRAINING DATASET VALIDATION REPORT':^90}")
    print(separator("="))

    results = []

    # Validate rewritten base dataset
    r1 = validate_file(
        REWRITTEN_PATH,
        "Rewritten Base Dataset (ir_playbooks_alpaca_rewritten.jsonl)",
        is_rewritten=True,
        is_synthetic=False,
    )
    results.append(r1)

    # Validate synthetic dataset
    r2 = validate_file(
        SYNTHETIC_PATH,
        "MITRE-Seeded Synthetic Dataset (ir_playbooks_synthetic_v2.jsonl)",
        is_rewritten=False,
        is_synthetic=True,
    )
    results.append(r2)

    # ── Final Combined Summary ───────────────────────────────────────────────
    print(f"\n{separator('=')}")
    print(f"{'COMBINED FINAL SUMMARY':^90}")
    print(separator("="))

    all_pass = all(r["overall"] == "PASS" for r in results)
    for r in results:
        status = r["overall"]
        marker = "[OK]" if status == "PASS" else "[!!]"
        print(f"  {marker} {r['label']}: {status}  ({r['total_rows']} rows)")
        if r["issues"]:
            for issue in r["issues"]:
                print(f"        - {issue}")

    print()
    if all_pass:
        print("  >>> ALL DATASETS PASSED VALIDATION <<<")
    else:
        print("  >>> ONE OR MORE DATASETS HAVE ISSUES - REVIEW ABOVE <<<")

    print(separator("="))


if __name__ == "__main__":
    main()
