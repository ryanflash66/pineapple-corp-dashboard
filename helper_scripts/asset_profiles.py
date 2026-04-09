"""Asset context profiles for training data transformation.

Each profile is a subset of the mock 24-asset inventory, filtered to assets
contextually relevant to a category of incident. These are injected into the
training data `input` field as "Organization assets:" blocks.

The compact bullet format matches what the RAG pipeline injects at runtime,
so the model learns to consume the same format it will see in production.
"""

# ---------------------------------------------------------------------------
# Full asset catalog (mirrors connectors/mock.py)
# Keys: name, type, vendor_product, network_zone, ip_or_subnet, role,
#        managed_by, criticality, notes
# ---------------------------------------------------------------------------

_ALL_ASSETS = {
    # Endpoint Protection
    "ws-corp-pool": "ws-corp-pool: Dell OptiPlex 7090 workstation, corporate (10.10.1.0/24), managed by CrowdStrike Falcon, 150 Windows 11 workstations, medium criticality",
    "laptop-exec-pool": "laptop-exec-pool: Lenovo ThinkPad X1 laptop, corporate (DHCP), managed by CrowdStrike Falcon, 25 executive laptops - BitLocker enabled, high criticality",
    "srv-dc-01": "srv-dc-01: Dell PowerEdge R750 server, datacenter (10.20.1.10), primary domain controller, managed by CrowdStrike Falcon, Primary AD DS, critical criticality",
    "srv-dc-02": "srv-dc-02: Dell PowerEdge R750 server, datacenter (10.20.1.11), secondary domain controller, managed by CrowdStrike Falcon, Secondary AD DS, critical criticality",
    # Network Security
    "fw-perimeter-01": "fw-perimeter-01: Palo Alto PA-850 firewall, dmz (10.0.0.1), perimeter filtering, Managed via Panorama, critical criticality",
    "fw-internal-01": "fw-internal-01: Palo Alto PA-450 firewall, datacenter (10.20.0.1), east-west segmentation, Segments corporate from datacenter, high criticality",
    "ids-core-01": "ids-core-01: Suricata 7.0 ids, datacenter (10.20.0.5), intrusion detection, Feeds alerts to Splunk, high criticality",
    "proxy-web-01": "proxy-web-01: Zscaler ZIA proxy, corporate (cloud), web filtering and SSL inspection, All outbound HTTP/HTTPS routed through Zscaler, medium criticality",
    # Identity & Access
    "mfa-provider": "mfa-provider: Duo Security mfa, cloud (cloud), multi-factor authentication, Enforced for VPN - email - and admin consoles, critical criticality",
    "pam-vault-01": "pam-vault-01: CyberArk PAS pam, datacenter (10.20.1.50), privileged access management, All admin credentials vaulted here, critical criticality",
    # Monitoring & Logging
    "siem-splunk-01": "siem-splunk-01: Splunk Enterprise 9.2 siem, datacenter (10.20.2.10), centralized log aggregation and alerting, 90-day hot retention - 1-year warm, critical criticality",
    "edr-console": "edr-console: CrowdStrike Falcon edr, cloud (cloud), endpoint detection and response, Covers all endpoints and servers, critical criticality",
    "ndr-sensor-01": "ndr-sensor-01: Darktrace ndr, datacenter (10.20.0.8), network traffic analysis, Monitors east-west and north-south traffic, high criticality",
    # Servers & Critical Services
    "srv-db-01": "srv-db-01: Microsoft SQL Server 2022 database, datacenter (10.20.3.10), primary business database, Contains customer PII - encrypted at rest, critical criticality",
    "srv-web-01": "srv-web-01: Nginx on Ubuntu 22.04 web_server, dmz (10.0.0.20), public-facing web application, Behind Palo Alto WAF policy, high criticality",
    "srv-file-01": "srv-file-01: Windows Server 2022 file_server, datacenter (10.20.3.20), shared file storage, 2 TB - DFS replication, medium criticality",
    "srv-mail-01": "srv-mail-01: Microsoft Exchange Online email_server, cloud (cloud), email and calendaring, Hybrid config - MX via cloud, high criticality",
    "srv-dns-01": "srv-dns-01: Windows DNS dns, datacenter (10.20.1.10), internal DNS resolution, Co-hosted on srv-dc-01, critical criticality",
    # Backup & Recovery
    "backup-veeam-01": "backup-veeam-01: Veeam Backup and Replication 12 backup, datacenter (10.20.4.10), primary backup server, Daily full backups - 4-hour RPO, critical criticality",
    "backup-offsite": "backup-offsite: AWS S3 Glacier dr_site, cloud (cloud), offsite backup copy, 30-day retention - immutable, critical criticality",
    "nas-archive-01": "nas-archive-01: Synology RS1221+ nas, datacenter (10.20.4.20), archive and cold storage, RAID 6 - 20 TB, medium criticality",
    # Network Topology
    "switch-core-01": "switch-core-01: Cisco Catalyst 9300 switch, datacenter (10.20.0.2), core switching, Trunk ports to all datacenter VLANs, high criticality",
    "router-wan-01": "router-wan-01: Cisco ISR 4451 router, dmz (10.0.0.2), WAN gateway, Dual ISP failover, high criticality",
    "ap-corp-pool": "ap-corp-pool: Cisco Meraki MR46 access_point, corporate (DHCP), wireless access, 40 APs across 3 floors, medium criticality",
}


def _build_block(asset_keys: list[str]) -> str:
    """Build the 'Organization assets:' text block from asset keys."""
    lines = ["Organization assets:"]
    for key in asset_keys:
        lines.append(f"- {_ALL_ASSETS[key]}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 5 Profiles — each selects 6-8 assets relevant to a category of incident
# ---------------------------------------------------------------------------

PROFILES = {
    # Ransomware, Malware Infection, Credential Dumping, Privilege Escalation,
    # Backdoor Installation
    "endpoint_network": _build_block([
        "ws-corp-pool",       # target endpoints
        "srv-dc-01",          # domain controller (lateral movement target)
        "srv-dc-02",          # secondary DC (credential resets)
        "edr-console",        # detection + isolation
        "siem-splunk-01",     # log correlation
        "fw-perimeter-01",    # block lateral movement / C2
        "fw-internal-01",     # east-west segmentation
        "backup-veeam-01",    # recovery
    ]),

    # Data Breach, SQL Injection, Zero-Day Exploit, Data Leak
    "web_data": _build_block([
        "srv-web-01",         # public-facing target
        "srv-db-01",          # database with PII
        "fw-perimeter-01",    # WAF / perimeter defense
        "ids-core-01",        # intrusion detection
        "siem-splunk-01",     # log analysis
        "edr-console",        # endpoint scanning
        "backup-veeam-01",    # data recovery
        "proxy-web-01",       # outbound filtering
    ]),

    # Phishing, Business Email Compromise, Credential Harvesting, Brute Force
    "email_identity": _build_block([
        "srv-mail-01",        # email server (attack surface)
        "mfa-provider",       # MFA enforcement
        "pam-vault-01",       # privileged credential vault
        "srv-dc-01",          # AD credential resets
        "edr-console",        # endpoint detection
        "siem-splunk-01",     # alert correlation
        "proxy-web-01",       # block phishing URLs
    ]),

    # DDoS, Command and Control, Living-off-the-Land Attack
    "network_infra": _build_block([
        "fw-perimeter-01",    # perimeter defense
        "fw-internal-01",     # internal segmentation
        "ids-core-01",        # IDS alerts
        "ndr-sensor-01",      # network traffic analysis
        "router-wan-01",      # WAN gateway (DDoS target)
        "switch-core-01",     # core network
        "siem-splunk-01",     # log aggregation
        "proxy-web-01",       # outbound C2 blocking
    ]),

    # Insider Threat, Cryptojacking, Supply Chain Attack
    "cloud_supply_chain": _build_block([
        "edr-console",        # endpoint monitoring
        "siem-splunk-01",     # anomaly detection
        "pam-vault-01",       # privileged access audit
        "mfa-provider",       # access controls
        "backup-offsite",     # offsite recovery
        "srv-db-01",          # data integrity
        "ndr-sensor-01",      # traffic anomalies
    ]),
}


# ---------------------------------------------------------------------------
# Incident type → profile name mapping
# ---------------------------------------------------------------------------

INCIDENT_TYPE_TO_PROFILE = {
    "Ransomware": "endpoint_network",
    "Malware Infection": "endpoint_network",
    "Credential Dumping": "endpoint_network",
    "Privilege Escalation": "endpoint_network",
    "Backdoor Installation": "endpoint_network",

    "Data Breach": "web_data",
    "SQL Injection": "web_data",
    "Zero-Day Exploit": "web_data",
    "Data Leak": "web_data",

    "Phishing": "email_identity",
    "Business Email Compromise": "email_identity",
    "Credential Harvesting": "email_identity",
    "Brute Force Attack": "email_identity",

    "DDoS Attack": "network_infra",
    "Command and Control": "network_infra",
    "Living-off-the-Land Attack": "network_infra",

    "Insider Threat": "cloud_supply_chain",
    "Cryptojacking": "cloud_supply_chain",
    "Supply Chain Attack": "cloud_supply_chain",
}


def get_asset_context(incident_type: str) -> str | None:
    """Return the asset context block for a given incident type, or None if unknown."""
    profile_name = INCIDENT_TYPE_TO_PROFILE.get(incident_type)
    if profile_name is None:
        return None
    return PROFILES[profile_name]


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Profiles defined: {len(PROFILES)}")
    print(f"Incident types mapped: {len(INCIDENT_TYPE_TO_PROFILE)}")
    print()

    for name, block in PROFILES.items():
        asset_count = block.count("\n- ")
        print(f"  {name}: {asset_count} assets")

    print()
    # Show one example
    example = get_asset_context("Ransomware")
    print("Example (Ransomware):")
    print(example)
