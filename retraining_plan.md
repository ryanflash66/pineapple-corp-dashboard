# Retraining Plan: Asset-Aware Playbooks

## Goal

1. **Expand the dataset** from 137 unique rows to ~200-220 rows using hybrid approach (137 base + 50-80 high-quality synthetic)
2. **Retrain the fine-tuned Llama 3.1 8B LoRA model** so that when asset inventory context is provided in the prompt, the model produces playbooks that reference **specific org assets by name, IP, and role** — not just generic tool categories

---

## What Needs to Change

### Current Training Format

**Input:**
```
Incident type: Ransomware
Target asset: Windows AD Server
Detection source: EDR Alert - Suspicious File Encryption
Initial vector: Email Attachment (Phishing)
Tactics and techniques:
- Initial Access: Phishing
- Execution: User Execution
- Impact: Data Encrypted for Impact
Severity: High
Tags: malware, lateral_movement, windows, ransomware, phishing
```

**Output:**
```
Playbook:

Phase: Identification
Action: Triage alert, confirm IOC via EDR, snapshot affected host
Tools: CrowdStrike Falcon, Velociraptor
Target response time (minutes): 15

Phase: Containment
Action: Isolate host from network, disable compromised user account
Tools: EDR, SIEM, Firewall
Target response time (minutes): 10

...

Final status: Resolved
Total response duration (minutes): 445
```

**Problem:** The output uses generic tool names ("EDR", "SIEM", "Firewall") and never references specific hosts, IPs, or org-specific details — because the input never provided them.

### New Training Format

**Input** (add asset context block at the end):
```
Incident type: Ransomware
Target asset: Windows AD Server
Detection source: EDR Alert - Suspicious File Encryption
Initial vector: Email Attachment (Phishing)
Tactics and techniques:
- Initial Access: Phishing
- Execution: User Execution
- Impact: Data Encrypted for Impact
Severity: High
Tags: malware, lateral_movement, windows, ransomware, phishing

Organization assets:
- srv-dc-01: Dell PowerEdge R750 server, datacenter (10.20.1.10), primary domain controller, managed by CrowdStrike Falcon, critical
- srv-dc-02: Dell PowerEdge R750 server, datacenter (10.20.1.11), secondary domain controller, managed by CrowdStrike Falcon, critical
- fw-perimeter-01: Palo Alto PA-850 firewall, dmz (10.0.0.1), perimeter filtering, critical
- siem-splunk-01: Splunk Enterprise 9.2 siem, datacenter (10.20.2.10), centralized log aggregation, critical
- edr-console: CrowdStrike Falcon edr, cloud, endpoint detection and response, critical
- backup-veeam-01: Veeam Backup and Replication 12, datacenter (10.20.4.10), primary backup server, critical
```

**Output** (reference specific assets + new Affected Assets section):
```
Playbook:

Phase: Identification
Action: Triage alert in CrowdStrike Falcon (edr-console), correlate with Splunk Enterprise (siem-splunk-01, 10.20.2.10), snapshot srv-dc-01 (10.20.1.10)
Tools: CrowdStrike Falcon, Splunk Enterprise 9.2
Target response time (minutes): 15

Phase: Containment
Action: Isolate srv-dc-01 via CrowdStrike Falcon, block lateral movement on Palo Alto PA-850 (fw-perimeter-01, 10.0.0.1), disable compromised user account in Active Directory on srv-dc-02 (10.20.1.11)
Tools: CrowdStrike Falcon, Palo Alto PA-850, Active Directory
Target response time (minutes): 10

Phase: Eradication
Action: Remove malicious binaries from srv-dc-01, scan all endpoints via CrowdStrike Falcon, patch vulnerabilities
Tools: CrowdStrike Falcon, YARA
Target response time (minutes): 60

Phase: Recovery
Action: Restore srv-dc-01 from Veeam backup (backup-veeam-01, 10.20.4.10), verify AD replication with srv-dc-02, monitor via Splunk for reinfection
Tools: Veeam Backup and Replication 12, Splunk Enterprise 9.2
Target response time (minutes): 120

Phase: Lessons Learned
Action: Conduct IR debrief, update Splunk detection rules, update Palo Alto firewall rules, user awareness training
Tools: Splunk Enterprise 9.2, Palo Alto Panorama, MISP
Target response time (minutes): 240

Affected Assets:
- srv-dc-01 (10.20.1.10): primary target, isolated and restored from backup
- srv-dc-02 (10.20.1.11): used for AD credential resets and replication verification
- fw-perimeter-01 (10.0.0.1): lateral movement blocked via firewall rules
- siem-splunk-01 (10.20.2.10): alert triage, log correlation, post-incident monitoring
- edr-console (cloud): endpoint isolation, forensic scanning, detection
- backup-veeam-01 (10.20.4.10): restore source for srv-dc-01

Final status: Resolved
Total response duration (minutes): 445
```

---

## Dual-Format Asset Inventory (JSON + Markdown Hybrid)

### Architecture

The live asset connector system writes asset inventory in **two complementary formats**:

1. **JSON** (`data/asset_inventory.json`) — Structured source of truth with metadata
2. **Markdown** (`data/asset_inventory.md`) — Human-readable format optimized for RAG retrieval

Both are generated from the same connector output (`List[dict]` with 9 keys matching the CSV template schema).

### JSON Format (Source of Truth)

```json
{
  "metadata": {
    "generated_at": "2026-03-17T14:23:45.123456",
    "connector": "nmap",
    "total_assets": 42
  },
  "assets": [
    {
      "name": "srv-dc-01",
      "type": "server",
      "vendor_product": "Dell PowerEdge R750",
      "network_zone": "datacenter",
      "ip_or_subnet": "10.20.1.10",
      "role": "primary domain controller",
      "managed_by": "CrowdStrike Falcon",
      "criticality": "critical",
      "notes": "Primary AD DS"
    }
  ]
}
```

**Benefits:** Timestamped, connector metadata, structured fields for filtering/sorting/API consumption, easy export to CMDB/SOAR, auditing and compliance tracking.

### Markdown Format (RAG-Optimized)

```markdown
# Organization Asset Inventory

## Endpoint Protection
- srv-dc-01: Dell PowerEdge R750 server, datacenter (10.20.1.10), primary domain controller, managed by CrowdStrike Falcon, critical criticality
```

**Benefits:** Grouped by IR-relevant categories, compact bullet format prevents chunking fragmentation, each asset on one line for retrieval relevance.

### Generation Flow

```
Connector (mock/nmap/netbox/etc.)
    |
    v
List[dict] (9-key asset dicts)
    |
    v
scripts/refresh_assets.py
    |-- build_json()  --> data/asset_inventory.json  (source of truth)
    |-- build_markdown() --> data/asset_inventory.md (RAG format)
    v
rag_index.py detects mtime change --> auto-rebuild ChromaDB
```

Both formats are generated from the same `List[dict]` in ~10ms total — zero duplication or sync issues.

| Need | Format | Why |
|------|--------|-----|
| API integration, extensibility | JSON | Structured, metadata, parseable by other systems |
| LLM context injection | Markdown | Human-readable, chunking-friendly for RAG |
| Audit trail | JSON | Timestamp + connector name for compliance |
| Manual inspection | Markdown | Easy to read, organized by IR category |

---

## Hybrid Dataset Expansion Strategy

### Overview

**Before:** 173 total rows (137 unique, 36 duplicates)
**After:** ~190-210 rows total
- 137 rows: deduped originals (updated with asset context)
- 50-80 rows: high-quality synthetic (generated + validated)

### Synthetic Data Generation Approach

**Model (CONFIRMED):** `unsloth/Llama-3.3-70B-Instruct` on Colab H100 GPU (via VSCode remote)
- Notebook already configured by another agent
- Running on Colab's H100 — no local GPU constraints

**Why better model matters:** Previous synthetic attempt (Llama 3.2 3B) produced 99.2% LOW quality data (generic tools, missing NIST phases). The 70B Instruct model will:
- Properly structure all 5 NIST phases
- Use real tool names (CrowdStrike, Palo Alto, Splunk)
- Generate specific, actionable steps (not generic fluff)
- Follow the Alpaca format correctly

### MITRE ATT&CK Integration

**Purpose:** Ground synthetic generation in real-world tactics/techniques to reduce hallucination

**Process:**
1. Extract real ATT&CK campaign/group data (e.g., APT28: spearphishing → lateral movement → exfiltration)
2. Map to your incident types (e.g., APT28 tactics → "Phishing + Privilege Escalation" incident)
3. Use as **seed prompts** for synthetic generator:
   ```
   Generate an IR playbook for:
   - Incident type: Phishing + Lateral Movement
   - Real-world ATT&CK tactics: Initial Access (Spearphishing), Execution (User Execution),
     Privilege Escalation (Exploitation for Privilege Escalation)
   - Target: Windows domain environment

   Use realistic tools, include all 5 NIST phases, be specific and actionable.
   ```
4. This anchors generation to proven techniques instead of hallucinated ones

**MITRE ATT&CK data sources:**
- MITRE ATT&CK website (free, public): https://attack.mitre.org/
- Browser campaigns/groups by tactics used
- Case studies with real-world attack flows

**Output:** A mapping file `helper_scripts/mitre_incident_mapping.py` that links ATT&CK campaigns → incident types, used as seed data for generation.

---

## Dataset Modification Plan

### Scope

- **Current dataset:** 173 total rows (137 unique after deduplication)
- **Rows to update with asset context:** 137 unique rows
- **Rows to generate synthetically:** 50-80 new rows (using better model + MITRE grounding)
- **Final dataset:** ~190-210 rows
- **Approach:**
  - Step 1-6: Asset-aware transformation of 137 base rows
  - Step 7-9 (NEW): Synthetic generation + validation

### Step 1: Deduplicate the Dataset

Remove the 36 exact duplicate rows from `ir_playbooks_alpaca.jsonl`.

**Output:** `ir_playbooks_alpaca_deduped.jsonl` (137 rows) **DONE**

### Step 2: Define Asset Context Profiles

Create 4-5 pre-built "org profiles" — sets of assets that are contextually relevant to different incident types. Each profile is a subset of the full 24-asset mock inventory, filtered to the assets relevant to that category of incident.

| Profile | When to Use | Assets Included |
|---------|------------|-----------------|
| **Endpoint + Network** | Ransomware, Malware, Credential Dumping, Privilege Escalation | Workstations, servers, EDR, firewalls, SIEM, backup |
| **Web + Data** | Data Breach, SQL Injection, Zero-Day Exploit | Web servers, databases, WAF/IDS, firewalls, SIEM, backup |
| **Email + Identity** | Phishing, BEC, Credential Harvesting | Mail server, MFA, PAM, EDR, SIEM, domain controllers |
| **Network + Infra** | DDoS, C2, Living-off-the-Land | Routers, switches, firewalls, IDS/NDR, SIEM, proxy |
| **Cloud + Supply Chain** | Cryptojacking, Supply Chain, Insider Threat | Cloud services, EDR, SIEM, PAM, backup |

Each profile contains 5-8 assets in the compact bullet format (same format the RAG pipeline injects at runtime). This keeps the input tokens reasonable.

### Step 3: Build the Transformation Script

Write `helper_scripts/add_asset_context.py` that:

1. Reads the deduped JSONL
2. For each row, classifies the incident type → selects the matching asset profile
3. Appends the asset context block to the `input` field (after a blank line)
4. Rewrites the `output` field to:
   - Replace generic tool names with specific asset names + IPs from the profile
   - Add hostname references in action descriptions
   - Append an `Affected Assets:` section at the end (before `Final status:`)
5. Writes the updated JSONL

**Critical:** The output rewriting in step 4 is the hardest part. Two approaches:

- **Option A — LLM-assisted rewrite (recommended):** Use an LLM (Claude API or Llama 3.2 locally) to rewrite each output given the original output + asset context. Prompt it to substitute generic names with specific ones and add the Affected Assets section. Then manually review a sample.
- **Option B — Rule-based rewrite:** Map generic names → specific names via a substitution table (e.g., "EDR" → "CrowdStrike Falcon (edr-console)", "SIEM" → "Splunk Enterprise 9.2 (siem-splunk-01, 10.20.2.10)"). Simpler but less natural-sounding.

**Recommendation:** Option A for quality, with manual spot-check of ~20 rows.

### Step 4: Validate the Updated Dataset

Run the existing quality checker (or write a quick one) to verify:
- All 5 NIST phases still present in every row
- `Affected Assets:` section present in every output
- At least 2 specific hostnames/IPs referenced per output
- No broken JSON
- No asset references that don't match the input context (hallucinated assets)

### Step 5: Retrain

Use the existing training notebook (`IRP_agent_trainint.ipynb`) on Colab:
- Point it at the new dataset file
- Same hyperparameters (LoRA rank, learning rate, epochs) — the format change doesn't require tuning changes
- Compare old vs new model on the same test prompts

### Step 6: Update the Prompt Template

The `build_prompt()` function in `app.py` currently says:
> "If asset inventory context is provided, reference specific tools, hostnames, and network zones in your playbook steps."

After retraining, the model should do this naturally (because it learned from examples). The instruction can stay as a reinforcement, but it will no longer be the only thing driving the behavior.

### Step 7 (NEW): Prepare MITRE ATT&CK Seed Data

Before running synthetic generation, prepare a mapping of real-world attack flows to your incident types.

**Deliverable:** `helper_scripts/mitre_incident_mapping.json`
```json
{
  "campaigns": [
    {
      "name": "APT28 Spearphishing Campaign",
      "incident_type": "Phishing + Lateral Movement",
      "tactics": ["Initial Access: Spearphishing Attachment", "Execution: User Execution",
                  "Privilege Escalation: Exploitation for Privilege Escalation"],
      "target_asset": "Windows Workstation",
      "severity": "High"
    },
    {
      "name": "Emotet Banking Trojan",
      "incident_type": "Malware Infection",
      "tactics": ["Initial Access: Phishing", "Execution: Malicious File",
                  "Persistence: Registry Run Keys", "Command and Control: Application Layer Protocol"],
      "target_asset": "Windows Server",
      "severity": "Critical"
    }
    // ... 15-20 more real-world campaigns/groups
  ]
}
```

**Source:** MITRE ATT&CK website. Extract 15-20 high-profile campaigns/threat groups with their documented tactics.

### Step 8 (NEW): Generate Synthetic Data

Use a better model to generate 50-80 new Alpaca-format examples, seeded with MITRE ATT&CK campaigns.

**Script:** `helper_scripts/generate_synthetic_playbooks.py` (or Colab notebook cells)
- Input: `mitre_incident_mapping.json`
- Model: `unsloth/Llama-3.3-70B-Instruct` on Colab H100 (already configured)
- Output: `datasets/ir_playbooks_synthetic_v2.jsonl` (50-80 rows)

**Prompt template for generation:**
```
You are an incident response expert. Generate a detailed IR playbook in Alpaca format.

Real-world attack context:
- Campaign: {campaign_name}
- Tactics: {tactics}
- Target: {target_asset}
- Severity: {severity}

Requirements:
1. Format: {"instruction": "...", "input": "Incident type: ...\n...", "output": "Playbook:\n\nPhase: ..."}
2. All 5 NIST phases (Identification, Containment, Eradication, Recovery, Lessons Learned)
3. Use real tool names: CrowdStrike Falcon, Splunk, Palo Alto, Veeam, etc.
4. Be specific and actionable (not generic)
5. Include response times per phase
6. NO generic fluff like "contact management"

Generate 3-5 variations based on this campaign context.
```

**Quality thresholds:** Each generated example must:
- Have all 5 NIST phases
- Include 3+ real tool names
- Have specific, non-generic actions
- Be valid JSON
- Not exceed 2000 tokens

Discard any row that fails these checks (expect ~20-30% rejection rate).

### Step 9 (NEW): Validate Synthetic Data

Run a quality checker on the generated 50-80 rows.

**Script:** `helper_scripts/validate_synthetic.py`
- Checks: JSON validity, NIST phases present, tool name realism, no hallucinated tools, action specificity
- Output: Report with pass/fail for each row + summary stats
- Goal: Achieve 90%+ pass rate before merging with base dataset

Manually spot-check ~10 random passing rows to ensure they're actually good (not just passing technical checks).

### Step 10 (UPDATED): Merge and Deduplicate

Combine 137 base rows + validated synthetic rows:
```
- base 137 rows (asset-aware transformed)
- validated synthetic rows (50-80, after rejection filtering)
= final dataset (~170-190 rows)
```

Deduplicate again to ensure no accidental overlaps between base and synthetic.

**Output:** `datasets/ir_playbooks_alpaca_v2_hybrid.jsonl`

### Step 11 (UPDATED): Apply Asset Context to Synthetic Rows

The synthetic generation in Step 8 creates rows WITHOUT asset context (like the original dataset).

Now apply the asset context transformation (from original Step 3-4) to the synthetic rows as well:
- Classify incident type → select asset profile
- Append asset context to input
- Rewrite output to reference specific assets

This ensures synthetic rows are also asset-aware.

**Output:** `datasets/ir_playbooks_alpaca_v2_hybrid_with_assets.jsonl` (final training dataset)

### Step 12 (UPDATED): Retrain

Use the final hybrid dataset with the training notebook.

---

## Mapping: Generic Tool Name → Specific Asset

This substitution table guides the output rewriting (whether LLM-assisted or rule-based):

| Generic Name in Current Data | Specific Replacement |
|------------------------------|---------------------|
| EDR | CrowdStrike Falcon (edr-console) |
| SIEM | Splunk Enterprise 9.2 (siem-splunk-01, 10.20.2.10) |
| Firewall | Palo Alto PA-850 (fw-perimeter-01, 10.0.0.1) or PA-450 (fw-internal-01, 10.20.0.1) |
| IDS | Suricata 7.0 (ids-core-01, 10.20.0.5) |
| Active Directory | Active Directory (srv-dc-01, 10.20.1.10) |
| Backup / Backup Exec / Veeam | Veeam Backup and Replication 12 (backup-veeam-01, 10.20.4.10) |
| WAF | Palo Alto WAF policy on fw-perimeter-01 |
| IAM Controls | CyberArk PAS (pam-vault-01, 10.20.1.50) + Duo Security (mfa-provider) |
| Nessus / OpenVAS | Nessus (vulnerability scanner) |
| NDR | Darktrace (ndr-sensor-01, 10.20.0.8) |

---

## Incident Type → Asset Profile Mapping

| Incident Type (count) | Profile |
|----------------------|---------|
| Ransomware (25) | Endpoint + Network |
| Data Breach (18) | Web + Data |
| Phishing (15) | Email + Identity |
| Malware Infection (15) | Endpoint + Network |
| DDoS Attack (13) | Network + Infra |
| Privilege Escalation (7) | Endpoint + Network |
| Credential Dumping (6) | Endpoint + Network |
| Command and Control (6) | Network + Infra |
| Insider Threat (5) | Cloud + Supply Chain |
| Cryptojacking (4) | Cloud + Supply Chain |
| Zero-Day Exploit (4) | Web + Data |
| Brute Force Attack (3) | Email + Identity |
| Supply Chain Attack (3) | Cloud + Supply Chain |
| Credential Harvesting (3) | Email + Identity |
| Living-off-the-Land Attack (3) | Network + Infra |
| SQL Injection (2) | Web + Data |
| Backdoor Installation (2) | Endpoint + Network |
| Business Email Compromise (2) | Email + Identity |
| Data Leak (1) | Web + Data |

---

## File Deliverables

### Phase 1: Base Dataset Transformation
| File | Description |
|------|------------|
| `datasets/ir_playbooks_alpaca_deduped.jsonl` | 137 deduplicated rows |
| `helper_scripts/add_asset_context.py` | Script to inject asset context into inputs + rewrite outputs |
| `helper_scripts/asset_profiles.py` | The 5 asset context profiles (dicts by incident type) |
| `helper_scripts/validate_dataset.py` | Quality checker for NIST phases, tool names, asset refs |

### Phase 2: Synthetic Data Generation (NEW)
| File | Description |
|------|------------|
| `helper_scripts/mitre_incident_mapping.json` | 15-20 real-world ATT&CK campaigns + tactics |
| `helper_scripts/generate_synthetic_playbooks.py` | Generator script (uses better model) |
| `datasets/ir_playbooks_synthetic_v2.jsonl` | 50-80 raw synthetic rows (before asset transformation) |
| `helper_scripts/validate_synthetic.py` | Validation script for synthetic rows |

### Phase 3: Final Hybrid Dataset
| File | Description |
|------|------------|
| `datasets/ir_playbooks_alpaca_v2_hybrid_with_assets.jsonl` | Final training dataset: ~170-190 rows, all asset-aware |

---

## Timeline Estimate

### Phase 1: Base Dataset (original steps 1-6)
| Step | Effort | Parallelizable |
|------|--------|----------------|
| 1. Deduplicate | Script, 15 min | — |
| 2. Define asset profiles | Manual review, 30 min | — |
| 3. Build transformation script | Scripting + LLM prompt engineering | N/A (sequential) |
| 4. Validate transformed rows | Script + manual spot-check (20 rows) | After step 3 |
| **Phase 1 Total** | ~2-3 hours | |

### Phase 2: Synthetic Data (NEW, steps 7-9) — **Parallel to Phase 1**
| Step | Effort | Notes |
|------|--------|-------|
| 7. Prepare MITRE seed data | Web research + manual mapping, ~1-2 hours | Can start immediately |
| 8. Generate synthetic rows | Depends on model choice & API availability | 50-80 rows generated |
| 9. Validate synthetic rows | Script + spot-check (10 rows), ~1 hour | ~20-30% rejection expected |
| **Phase 2 Total** | ~2-3 hours | Fully parallelizable with Phase 1 |

### Phase 3: Merge & Final Prep (steps 10-11)
| Step | Effort |
|------|--------|
| 10. Merge + final deduplicate | Script, 15 min |
| 11. Apply asset context to synthetic rows | Reuse script from Phase 1, 30 min |
| 12. Retrain on Colab | Same as previous (2-3 hours on Colab GPU) |
| 13. Test end-to-end | Run app, verify outputs, 30 min |

### Total Estimated Timeline
- **Sequential work:** Phases 1-3 run sequentially = ~4-6 hours active work
- **Parallelizable:** Phases 1 & 2 can run in parallel = Phase 1 + Phase 2 (2-3 hrs each, parallel) + Phase 3 (2 hrs)
- **With parallelization:** ~5-7 hours wall-clock time (split across 2 agents)
- **Training on Colab:** Additional 2-3 hours (can happen while other work finishes)

---

## Success Criteria

After retraining on the hybrid dataset, the model should:
1. Reference specific asset names (e.g., "srv-dc-01") not just types ("domain controller")
2. Include IPs where relevant (e.g., "block on fw-perimeter-01 at 10.0.0.1")
3. Produce an `Affected Assets:` section listing each asset's role in the response
4. Still produce correct NIST phase structure
5. Gracefully handle queries without asset context (fall back to generic tool names)
6. Produce asset-aware outputs for diverse incident types (not just the top 5)

Item 5 is critical — the model must work both with and without asset context. The dataset uses a **80/20 mix**:

### Training Data Mix Strategy

**Total final dataset: ~190-220 rows**

- **~160-175 rows (80%):** Asset-aware (asset context in input + specific asset references in output)
  - 110 from base 137 (after dedup + transformation)
  - 50-65 from synthetic generation (after validation + asset transformation)
- **~27 rows (20%):** Original format (no asset context in input, generic tool outputs)
  - Preserved from base 137 originals
  - Includes at least 1 row per incident type so the model learns both modes

This mix prevents the model from breaking when no asset inventory is available at inference time.

### Dataset Composition

| Source | Count | Asset-Aware | Original Format |
|--------|-------|-------------|-----------------|
| Base deduped | 137 | 110 | 27 |
| Synthetic (after validation) | 55 | 55 | 0 |
| **Final dataset** | **192** | **165** | **27** |

The 27 "original format" rows are strategically selected from the base 137 to ensure coverage across all 19 incident types, with rare types getting priority (so the model learns they can be handled with or without assets).
