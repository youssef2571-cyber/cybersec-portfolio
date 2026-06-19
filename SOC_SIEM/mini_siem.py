"""
Advanced Mini-SIEM Engine
Features Cross-Log Correlation: Connects Network Alerts (IDS) with System Logs (SSH).
"""

import time
import re
from collections import defaultdict

LOG_FILE = "central_syslog.log"
TIME_WINDOW = 60

# Tracking states
failed_auth_tracker = defaultdict(list)
recent_ids_alerts = {} # Tracks IPs that triggered IDS: { 'IP': timestamp }

def trigger_alert(severity, alert_name, ip, details):
    """Outputs the correlated alert to the SOC dashboard."""
    print(f"\n[{severity}] {alert_name}")
    print(f" ➔ Threat IP : {ip}")
    print(f" ➔ Details   : {details}\n")

def parse_and_correlate(log_line):
    current_time = time.time()
    
    # ---------------------------------------------------------
    # PARSER 1: Custom IDS/IPS Alerts
    # Example: "[IDS ALERT] Port Scan detected from 192.168.1.105"
    # ---------------------------------------------------------
    ids_pattern = r"\[IDS ALERT\].*from (\d+\.\d+\.\d+\.\d+)"
    ids_match = re.search(ids_pattern, log_line)
    if ids_match:
        attacker_ip = ids_match.group(1)
        recent_ids_alerts[attacker_ip] = current_time
        print(f"[INGEST] Network IDS alert registered for {attacker_ip}")
        return

    # ---------------------------------------------------------
    # PARSER 2: SSH Failed Logins (Brute Force Detection)
    # ---------------------------------------------------------
    ssh_fail_pattern = r"Failed password for .* from (\d+\.\d+\.\d+\.\d+)"
    fail_match = re.search(ssh_fail_pattern, log_line)
    if fail_match:
        attacker_ip = fail_match.group(1)
        failed_auth_tracker[attacker_ip].append(current_time)
        print(f"[INGEST] SSH Failure logged from {attacker_ip}")
        
        # Clean old logs and check threshold
        failed_auth_tracker[attacker_ip] = [t for t in failed_auth_tracker[attacker_ip] if current_time - t <= TIME_WINDOW]
        if len(failed_auth_tracker[attacker_ip]) >= 5:
            trigger_alert("🔥 HIGH", "SSH Brute Force Attack", attacker_ip, "5+ failed logins in 60s")
            failed_auth_tracker[attacker_ip] = [] # Reset
        return

    # ---------------------------------------------------------
    # PARSER 3: SSH Successful Logins (Cross-Correlation Rule)
    # Example: "Accepted password for root from 192.168.1.105"
    # ---------------------------------------------------------
    ssh_success_pattern = r"Accepted password for .* from (\d+\.\d+\.\d+\.\d+)"
    success_match = re.search(ssh_success_pattern, log_line)
    if success_match:
        attacker_ip = success_match.group(1)
        print(f"[INGEST] Valid SSH Login from {attacker_ip}")
        
        # CROSS-CORRELATION: Did this IP trigger an IDS alert recently?
        if attacker_ip in recent_ids_alerts:
            time_diff = current_time - recent_ids_alerts[attacker_ip]
            if time_diff <= 300: # Within 5 minutes
                trigger_alert(
                    "💀 CRITICAL", 
                    "COMPROMISED HOST (Lateral Movement)", 
                    attacker_ip, 
                    f"Successful SSH login occurred {int(time_diff)}s after a Network IDS Alert!"
                )
                del recent_ids_alerts[attacker_ip] # Reset
        return

def follow_log(filename):
    """Tails the log file in real-time."""
    try:
        with open(filename, "r") as file:
            file.seek(0, 2)
            while True:
                line = file.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                yield line
    except FileNotFoundError:
        print(f"[ERROR] Cannot find {filename}. Please run the simulation script.")

if __name__ == "__main__":
    print("==================================================")
    print(" 👁️  Advanced SOC Correlation Engine")
    print(" 🛡️  Active Rules:")
    print("     1. SSH Brute Force Detection")
    print("     2. IDS Alert + SSH Success (Critical Compromise)")
    print("==================================================\n")
    
    for line in follow_log(LOG_FILE):
        parse_and_correlate(line)
