import json
import os

def build_scenarios():
    scenarios = []

    # Helper lists for realistic generation
    users = [
        {"name": "Alex Murphy", "email": "alex.murphy@enterprise.com", "dept": "Engineering", "mgr": "sarah.connor@enterprise.com"},
        {"name": "Elena Rostova", "email": "elena.rostova@enterprise.com", "dept": "Finance", "mgr": "marcus.vance@enterprise.com"},
        {"name": "David Kim", "email": "david.kim@enterprise.com", "dept": "Product Design", "mgr": "sarah.connor@enterprise.com"},
        {"name": "Priya Sharma", "email": "priya.sharma@enterprise.com", "dept": "DevOps / Infrastructure", "mgr": "marcus.vance@enterprise.com"},
        {"name": "Liam O'Connor", "email": "liam.oconnor@enterprise.com", "dept": "Sales & Marketing", "mgr": "rachel.green@enterprise.com"},
        {"name": "Samantha Wu", "email": "samantha.wu@enterprise.com", "dept": "Legal & Compliance", "mgr": "rachel.green@enterprise.com"},
        {"name": "Carlos Gomez", "email": "carlos.gomez@enterprise.com", "dept": "Customer Support", "mgr": "marcus.vance@enterprise.com"},
        {"name": "Aisha Al-Mansoor", "email": "aisha.almansoor@enterprise.com", "dept": "Data Science & AI", "mgr": "sarah.connor@enterprise.com"}
    ]

    # ════════════════════════════════════════════════════════════════════════════════
    # CATEGORY 1: DEVICE OPS & MICROSOFT INTUNE (35 SCENARIOS)
    # ════════════════════════════════════════════════════════════════════════════════
    device_templates = [
        ("BitLocker Recovery Key Retrieval for Locked Laptop",
         "I am locked out of my laptop {dev} after a firmware BIOS update and it is prompting for a 48-digit BitLocker recovery key.",
         "AE_DEV_002_GetBitLockerKey",
         lambda u, d, intune_id: {"device_id": d, "requester_upn": u["email"], "ticket_id": "{ticket_id}"},
         "Urgent BitLocker recovery required for blocked employee following firmware update.",
         "R2", "MANAGER", "bitlocker_recovery_key", "VALID_KEY_RETURNED"),

        ("Intune Security Baseline Compliance Remediation",
         "My work laptop {dev} is showing NON_COMPLIANT in Intune and conditional access is blocking Microsoft Teams and Outlook.",
         "AE_DEV_012_RemediateCompliance",
         lambda u, d, intune_id: {"intune_device_id": intune_id, "policy_name": "WIN11_SEC_BASELINE_V2", "ticket_id": "{ticket_id}"},
         "Reapply corporate security baseline and remediate BitLocker encryption policy.",
         "R2", "MANAGER", "new_compliance_state", "COMPLIANT"),

        ("Remote Endpoint Reboot After Kernel Patching",
         "My workstation {dev} is hanging on a stuck system process after OS patching and needs an authorized remote reboot.",
         "AE_DEV_011_RestartDevice",
         lambda u, d, intune_id: {"intune_device_id": intune_id, "force_reboot": "true", "ticket_id": "{ticket_id}"},
         "Force remote system restart signal sent to recover frozen enterprise laptop.",
         "R2", "MANAGER", "execution_status", "REBOOT_SIGNAL_SENT"),

        ("Intune Immediate Policy Refresh and Synchronization",
         "I was just assigned a new conditional access group but my laptop {dev} has not received the Intune profile. Please sync.",
         "AE_DEV_010_TriggerSync",
         lambda u, d, intune_id: {"intune_device_id": intune_id},
         "Immediate MDM push notification to re-evaluate device posture and certificates.",
         "R1", "MANAGER", "sync_status", "INITIATED"),

        ("Enterprise 802.1x Wi-Fi Profile Redeployment",
         "My corporate laptop {dev} cannot connect to the Enterprise-Secure Wi-Fi network due to a corrupted certificate profile.",
         "AE_DEV_014_DeployWifiProfile",
         lambda u, d, intune_id: {"intune_device_id": intune_id, "profile_name": "CORP-WPA3-ENTERPRISE", "ticket_id": "{ticket_id}"},
         "Repush root certificate and WPA3-Enterprise 802.1x Wi-Fi profile via Intune.",
         "R2", "MANAGER", "deployment_status", "SUCCESS"),

        ("Windows Hello Biometric Container and PIN Reset",
         "My Windows Hello facial recognition and PIN container on {dev} are corrupted and prompting for administrator reset.",
         "AE_DEV_015_ResetWindowsHello",
         lambda u, d, intune_id: {"intune_device_id": intune_id, "ticket_id": "{ticket_id}"},
         "Reset Windows Hello TPM container and generate temporary provisioning PIN.",
         "R2", "MANAGER", "reset_status", "SUCCESS"),

        ("Emergency Remote Device Lock for Misplaced Endpoint",
         "I left my company laptop {dev} in a rideshare vehicle. Please remotely lock it immediately to prevent unauthorized access.",
         "AE_DEV_016_LockDevice",
         lambda u, d, intune_id: {"intune_device_id": intune_id, "ticket_id": "{ticket_id}"},
         "Immediate cryptographic screen lock and BitLocker PIN enforcement for lost device.",
         "R2", "SECURITY_ADMIN", "lock_status", "LOCKED"),

        ("Intune Win32 Application Package Repair and Reinstall",
         "My corporate CAD software package on {dev} failed to launch with missing DLL errors. Can Intune force a reinstall?",
         "AE_DEV_017_RedeployAppPackage",
         lambda u, d, intune_id: {"intune_device_id": intune_id, "app_name": "Autodesk-AutoCAD-2026-x64", "ticket_id": "{ticket_id}"},
         "Purge corrupt application payload and trigger clean silent reinstallation via Intune.",
         "R2", "MANAGER", "package_status", "INSTALLED"),

        ("System Storage and Delivery Optimization Cache Purge",
         "My C: drive on {dev} is 99% full due to cached Windows update files and delivery optimization logs.",
         "AE_DEV_018_ClearStorageCache",
         lambda u, d, intune_id: {"intune_device_id": intune_id},
         "Purge delivery optimization cache, temp files, and pending update installer scraps.",
         "R1", "MANAGER", "cleanup_status", "COMPLETED"),

        ("Microsoft Defender Antivirus Definition Force Update",
         "Defender security center on {dev} reports virus definitions are over 14 days out of date.",
         "AE_DEV_013_UpdateAntivirusSignatures",
         lambda u, d, intune_id: {"intune_device_id": intune_id},
         "Trigger immediate pull of latest Defender cloud security intelligence definitions.",
         "R1", "MANAGER", "update_status", "SUCCESS")
    ]

    for i in range(1, 36):
        tmpl = device_templates[(i - 1) % len(device_templates)]
        user = users[(i - 1) % len(users)]
        dev_id = f"DEV-WIN-{100 + i}"
        intune_id = f"9b12a831-50e2-4112-98aa-100000000{i:03d}"
        
        title = f"{tmpl[0]} #{i}"
        query = tmpl[1].format(dev=dev_id)
        wf = tmpl[2]
        params = tmpl[3](user, dev_id, intune_id)
        justif = tmpl[4]
        risk = tmpl[5]
        appr_role = tmpl[6]
        v_field = tmpl[7]
        v_val = tmpl[8]

        scenarios.append({
            "scenario_id": f"SCN-DEV-{i:03d}",
            "domain": "DEVICE",
            "category": "Device Ops & Microsoft Intune",
            "title": title,
            "query_text": query,
            "requester_email": user["email"],
            "requester_name": user["name"],
            "department": user["dept"],
            "manager_email": user["mgr"],
            "approver_role": appr_role,
            "target_entity_type": "DEVICE",
            "target_entity_id": dev_id,
            "target_friendly_name": f"Corporate Managed Endpoint ({dev_id})",
            "intune_device_id": intune_id,
            "risk_tier": risk,
            "proposed_workflow": wf,
            "workflow_params": params,
            "business_justification": justif,
            "verification_field": v_field,
            "expected_verification_val": v_val
        })

    # ════════════════════════════════════════════════════════════════════════════════
    # CATEGORY 2: ACCESS & MICROSOFT ENTRA ID (35 SCENARIOS)
    # ════════════════════════════════════════════════════════════════════════════════
    access_catalog_items = [
        ("GitHub Enterprise Core Developers Group", "GRP-GH-DEV", "GROUP", "AE_ACC_011_AddGroupMember", "R2", "MANAGER", "I need developer write access to GitHub Enterprise repositories for Q3 sprint deliverables."),
        ("Salesforce CRM Enterprise Sales User License", "SKU-SF-ENT", "LICENSE", "AE_ACC_013_AssignLicense", "R2", "MANAGER", "Assign Salesforce Sales Cloud enterprise license for client pipeline management."),
        ("AWS Cloud Operations PowerUser IAM Role", "GRP-AWS-OPS", "GROUP", "AE_ACC_011_AddGroupMember", "R2", "MANAGER", "Require AWS cloud operations group membership for staging cluster maintenance."),
        ("Microsoft 365 E5 Security & Copilot Add-On", "SKU-M365-E5", "LICENSE", "AE_ACC_013_AssignLicense", "R2", "MANAGER", "Provision Microsoft 365 Copilot and Advanced Compliance license to analyze financial contracts."),
        ("Cisco AnyConnect Corporate VPN User Group", "GRP-VPN-CORP", "GROUP", "AE_ACC_011_AddGroupMember", "R2", "MANAGER", "I need secure remote access through the Cisco AnyConnect enterprise gateway."),
        ("Jira Service Management Specialist Agent Seat", "SKU-JIRA-SVC", "LICENSE", "AE_ACC_013_AssignLicense", "R2", "MANAGER", "Assign Jira Service Desk IT specialist license to resolve enterprise service tickets."),
        ("Workday HCM Human Resources Compensation Viewer", "GRP-WD-COMP", "GROUP", "AE_ACC_011_AddGroupMember", "R2", "MANAGER", "Request read access to compensation benchmarking modules in Workday HCM."),
        ("SAP ERP S/4HANA Finance Ledger Accounting Role", "GRP-SAP-FIN", "GROUP", "AE_ACC_011_AddGroupMember", "R2", "MANAGER", "Provision SAP financial reporting and general ledger accounting entitlements."),
        ("Privileged Identity Management (PIM) Intune Admin Activation", "PIM-INTUNE-ADM", "ROLE", "AE_ACC_015_GrantPrivilegedPIM", "R3", "SECURITY_ADMIN", "Request temporary 4-hour elevation to Intune Administrator for policy deployment."),
        ("Emergency Refresh Token & Session Revocation (Compromised Credential)", "SEC-REVOKE", "SECURITY", "AE_ACC_021_RevokeSessions", "R3", "SECURITY_ADMIN", "Revoke all active browser and mobile tokens following reported suspicious sign-in.")
    ]

    for i in range(1, 36):
        item = access_catalog_items[(i - 1) % len(access_catalog_items)]
        user = users[(i - 1) % len(users)]
        
        target_name = item[0]
        target_id = f"{item[1]}-{i:02d}"
        itype = item[2]
        wf = item[3]
        risk = item[4]
        appr_role = item[5]
        query = f"Requesting access: {item[6]} (Target: {target_name})"

        if wf == "AE_ACC_011_AddGroupMember":
            params = {"user_id": f"USR-{1000 + i}", "group_id": target_id, "ticket_id": "{ticket_id}", "reason": f"Approved business request for {target_name}"}
            v_field = "group_id"
            v_val = target_id
        elif wf == "AE_ACC_013_AssignLicense":
            params = {"user_id": f"USR-{1000 + i}", "sku_id": target_id, "ticket_id": "{ticket_id}"}
            v_field = "consumed_sku"
            v_val = target_id
        elif wf == "AE_ACC_015_GrantPrivilegedPIM":
            params = {"user_id": f"USR-{1000 + i}", "pim_role": target_name, "duration_hours": 4, "ticket_id": "{ticket_id}"}
            v_field = "execution_status"
            v_val = "SUCCESS"
        else: # Revoke
            params = {"user_id": f"USR-{1000 + i}", "reason": "Security protocol enforcement", "ticket_id": "{ticket_id}"}
            v_field = "execution_status"
            v_val = "SUCCESS"

        scenarios.append({
            "scenario_id": f"SCN-ACC-{i:03d}",
            "domain": "ACCESS",
            "category": "Access & Microsoft Entra ID",
            "title": f"Access Request: {target_name} #{i}",
            "query_text": query,
            "requester_email": user["email"],
            "requester_name": user["name"],
            "department": user["dept"],
            "manager_email": user["mgr"],
            "approver_role": appr_role,
            "target_entity_type": itype,
            "target_entity_id": target_id,
            "target_friendly_name": target_name,
            "risk_tier": risk,
            "proposed_workflow": wf,
            "workflow_params": params,
            "business_justification": f"Business justification: {item[6]}",
            "verification_field": v_field,
            "expected_verification_val": v_val
        })

    # ════════════════════════════════════════════════════════════════════════════════
    # CATEGORY 3: HARDWARE LIFECYCLE & CMDB ASSET MANAGEMENT (25 SCENARIOS)
    # ════════════════════════════════════════════════════════════════════════════════
    hardware_faults = [
        ("Cracked 4K OLED Laptop Screen Replacement", "Screen cracked during transit, display has vertical black bars and backlight bleed.", "LAPTOP_SCREEN", "Lenovo ThinkPad X1 Carbon"),
        ("Swollen Lithium-Ion Battery Urgent RMA Dispatch", "Battery enclosure is swelling and pushing against trackpad. Urgent safety replacement needed.", "BATTERY_EXPANSION", "Dell Latitude 9440"),
        ("Thunderbolt 4 Docking Station Power Delivery Failure", "Dell WD22TB4 docking station will not charge laptop or output video to external monitors.", "DOCKING_STATION", "Dell Thunderbolt 4 Dock WD22TB4"),
        ("Mechanical Keyboard Key Switch Defect Replacement", "Multiple keys ('Enter', 'Space', 'E') are intermittently unresponsive following hardware wear.", "KEYBOARD_FAULT", "Apple MacBook Pro 16 M3"),
        ("System Motherboard Memory Controller Failure", "Workstation fails to boot with 3 beep memory controller error code. Motherboard replacement required.", "MOTHERBOARD_FAILURE", "HP EliteBook 840 G10"),
        ("Flickering UltraSharp 34-Inch Curved Monitor Replacement", "External display Dell U3423WE intermittently flashes black every 20 seconds over USB-C.", "MONITOR_FLICKER", "Dell UltraSharp 34 Curved U3423WE"),
        ("High-Performance NVMe SSD Read Failure", "SSD diagnostic reports S.M.A.R.T. health critical warning and I/O error on primary boot partition.", "SSD_FAILURE", "Samsung PM9A1 1TB NVMe"),
        ("Ergonomic Vertical Mouse and Split Keyboard Replacement", "Employee requires replacement ergonomic peripheral set due to approved ergonomics assessment.", "PERIPHERAL_DISPATCH", "Logitech MX Master 3S + Ergo K860")
    ]

    for i in range(1, 26):
        fault = hardware_faults[(i - 1) % len(hardware_faults)]
        user = users[(i - 1) % len(users)]
        ci_id = f"CI-HW-{2000 + i}"
        serial = f"PF9{i:03d}X8{i % 10}"
        asset_tag = f"ASSET-TAG-{7000 + i}"

        scenarios.append({
            "scenario_id": f"SCN-HW-{i:03d}",
            "domain": "HARDWARE",
            "category": "Hardware Lifecycle & CMDB Asset Management",
            "title": f"Hardware Dispatch: {fault[0]} #{i}",
            "query_text": f"Hardware Incident: {fault[1]} (Asset: {fault[3]}, Tag: {asset_tag})",
            "requester_email": user["email"],
            "requester_name": user["name"],
            "department": user["dept"],
            "manager_email": user["mgr"],
            "approver_role": "MANAGER",
            "target_entity_type": "HARDWARE_CI",
            "target_entity_id": ci_id,
            "target_friendly_name": f"{fault[3]} (Serial: {serial})",
            "serial_number": serial,
            "asset_tag": asset_tag,
            "risk_tier": "R2",
            "proposed_workflow": "AE_HW_020_OrderReplacement",
            "workflow_params": {
                "ci_id": ci_id,
                "serial_number": serial,
                "shipping_address": "Enterprise Office - IT Hub / Employee Remote Desk",
                "approval_id": "{approval_id}",
                "ticket_id": "{ticket_id}"
            },
            "business_justification": f"Defective asset {ci_id} requires immediate OEM warranty dispatch to restore productivity.",
            "verification_field": "install_status",
            "expected_verification_val": "Pending Replacement / In Repair"
        })

    # ════════════════════════════════════════════════════════════════════════════════
    # CATEGORY 4: SECURITY, ZERO TRUST & ENDPOINT PROTECTION (15 SCENARIOS)
    # ════════════════════════════════════════════════════════════════════════════════
    sec_scenarios = [
        ("Immediate Host Network Isolation for Ransomware Containment", "Suspicious PowerShell beaconing detected by Defender on endpoint {dev}. Isolate from corporate network.", "AE_SEC_001_IsolateEndpoint", "R3", "SECURITY_ADMIN", "Active threat detection; immediate containment required by SecOps."),
        ("Temporary USB Mass Storage Exemption Approval", "Senior Data Engineer requires 24-hour read-write USB mass storage exemption on {dev} for air-gapped lab telemetry transfer.", "AE_SEC_002_AuthorizeUsbException", "R2", "MANAGER", "Air-gapped industrial lab data migration approved by department lead."),
        ("Defender Quarantined False-Positive Script Remediation", "Corporate internal deployment script on {dev} was quarantined by Defender as Win32/Wacatac.B!ml.", "AE_SEC_003_QuarantineRemediate", "R2", "SECURITY_ADMIN", "Internal verified automation script falsely quarantined; release and re-scan approved."),
        ("Compromised User Session Token Global Revocation", "User reported credential stuffing alert on external personal phone. Revoke all Entra ID sessions immediately.", "AE_ACC_021_RevokeSessions", "R3", "SECURITY_ADMIN", "Potential credential compromise reported; enforce zero-trust session kill."),
        ("Cryptographic Screen Lock on Unattended Remote Laptop", "Endpoint {dev} was reported unattended at airport lounge with active VPN session. Enforce lock.", "AE_DEV_016_LockDevice", "R2", "SECURITY_ADMIN", "Zero-trust physical security policy enforcement.")
    ]

    for i in range(1, 16):
        s_tmpl = sec_scenarios[(i - 1) % len(sec_scenarios)]
        user = users[(i - 1) % len(users)]
        dev_id = f"SEC-DEV-{300 + i}"
        intune_id = f"9b12a831-50e2-4112-98aa-200000000{i:03d}"
        
        title = f"{s_tmpl[0]} #{i}"
        query = s_tmpl[1].format(dev=dev_id)
        wf = s_tmpl[2]
        risk = s_tmpl[3]
        appr_role = s_tmpl[4]
        justif = s_tmpl[5]

        if wf == "AE_SEC_001_IsolateEndpoint":
            params = {"device_id": dev_id, "reason": "Confirmed C2 beaconing alert in Defender", "ticket_id": "{ticket_id}"}
            v_field = "isolation_status"
            v_val = "ISOLATED"
        elif wf == "AE_SEC_002_AuthorizeUsbException":
            params = {"device_id": dev_id, "justification": justif, "duration_hours": 24, "ticket_id": "{ticket_id}"}
            v_field = "exemption_status"
            v_val = "ACTIVE"
        elif wf == "AE_SEC_003_QuarantineRemediate":
            params = {"device_id": dev_id, "threat_name": "Win32/Wacatac.B!ml", "ticket_id": "{ticket_id}"}
            v_field = "remediation_status"
            v_val = "REMEDIATED"
        elif wf == "AE_ACC_021_RevokeSessions":
            params = {"user_id": f"USR-SEC-{i}", "reason": "Credential stuffing mitigation", "ticket_id": "{ticket_id}"}
            v_field = "execution_status"
            v_val = "SUCCESS"
        else: # Lock
            params = {"intune_device_id": intune_id, "ticket_id": "{ticket_id}"}
            v_field = "lock_status"
            v_val = "LOCKED"

        scenarios.append({
            "scenario_id": f"SCN-SEC-{i:03d}",
            "domain": "SECURITY",
            "category": "Security, Zero Trust & Endpoint Protection",
            "title": title,
            "query_text": query,
            "requester_email": user["email"],
            "requester_name": user["name"],
            "department": "Cybersecurity & Operations",
            "manager_email": "security-ops@enterprise.com",
            "approver_role": appr_role,
            "target_entity_type": "SECURITY_TARGET",
            "target_entity_id": dev_id,
            "target_friendly_name": f"Security Asset ({dev_id})",
            "intune_device_id": intune_id,
            "risk_tier": risk,
            "proposed_workflow": wf,
            "workflow_params": params,
            "business_justification": justif,
            "verification_field": v_field,
            "expected_verification_val": v_val
        })

    # ════════════════════════════════════════════════════════════════════════════════
    # CATEGORY 5: SAAS & COLLABORATION LIFECYCLE (10 SCENARIOS)
    # ════════════════════════════════════════════════════════════════════════════════
    saas_items = [
        ("Slack Enterprise Grid Shared Channel Guest to Full Member Elevation", "Slack Enterprise Grid", "Full Enterprise Member", "AE_SAAS_001_AssignSaaSRole", "R2", "MANAGER", "Elevate contractor account to full Slack Enterprise member for cross-team project collaboration."),
        ("Zoom Large Meeting 500-Participant Add-On License", "Zoom Video Communications", "Large Meeting 500 Addon", "AE_SAAS_001_AssignSaaSRole", "R2", "MANAGER", "Requesting Zoom 500 capacity add-on for quarterly global partner webinar."),
        ("Tableau Server Creator & Data Modeling Seat Provisioning", "Tableau Enterprise Cloud", "Creator Seat", "AE_SAAS_001_AssignSaaSRole", "R2", "MANAGER", "Need Tableau Creator license to publish production financial dashboards."),
        ("Snowflake Data Warehouse Analyst Compute Role Grant", "Snowflake Cloud Analytics", "ANALYST_COMPUTE_ROLE", "AE_ACC_012_AssignAppRole", "R2", "MANAGER", "Request query privileges on production customer analytics warehouse in Snowflake."),
        ("Figma Enterprise Design System Editor Workspace License", "Figma Enterprise", "Design Editor Seat", "AE_SAAS_001_AssignSaaSRole", "R2", "MANAGER", "Require Figma Editor seat to create mobile app component libraries.")
    ]

    for i in range(1, 11):
        s_item = saas_items[(i - 1) % len(saas_items)]
        user = users[(i - 1) % len(users)]
        
        scenarios.append({
            "scenario_id": f"SCN-SAAS-{i:03d}",
            "domain": "ACCESS",
            "category": "SaaS & Enterprise Collaboration Lifecycle",
            "title": f"SaaS Grant: {s_item[0]} #{i}",
            "query_text": f"I need authorization for {s_item[1]} ({s_item[2]}): {s_item[6]}",
            "requester_email": user["email"],
            "requester_name": user["name"],
            "department": user["dept"],
            "manager_email": user["mgr"],
            "approver_role": s_item[5],
            "target_entity_type": "SAAS_PLATFORM",
            "target_entity_id": f"SAAS-ID-{400 + i}",
            "target_friendly_name": f"{s_item[1]} - {s_item[2]}",
            "risk_tier": s_item[4],
            "proposed_workflow": s_item[3],
            "workflow_params": {
                "user_id": f"USR-SAAS-{i}",
                "saas_platform": s_item[1],
                "role_name": s_item[2],
                "ticket_id": "{ticket_id}"
            },
            "business_justification": s_item[6],
            "verification_field": "assignment_status",
            "expected_verification_val": "SUCCESS"
        })

    return scenarios

if __name__ == "__main__":
    scenarios = build_scenarios()
    output_path = os.path.join(os.path.dirname(__file__), "realtime_scenarios.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scenarios, f, indent=2)
    print(f"Successfully generated {len(scenarios)} production real-time IT scenarios to {output_path}")
