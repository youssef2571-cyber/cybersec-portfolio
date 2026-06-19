"""
Mini-SIEM (Security Information and Event Management) Engine
Reads logs in real-time, parses security events, and correlates data to trigger alerts.
"""

import time
import re
from collections import defaultdict

# --- SIEM Configuration ---
LOG_FILE = "auth_simulated.log" # The log file our SIEM is monitoring
TIME_WINDOW = 60                # Time window for correlation (in seconds)
BRUTE_FORCE_THRESHOLD = 5       # Number of failed attempts before alerting

# State tracking: { 'IP_Address': [list of timestamps] }
failed_auth_tracker = defaultdict(list)

def trigger_alert(alert_type, ip, details):
    """Handles the alerting mechanism (e.g., printing to dashboard, sending email)."""
    print(f"\n[🔥 SIEM CRITICAL ALERT] {alert_type}")
    print(f" ➔ Source IP: {ip}")
    print(f" ➔ Details:   {details}\n")

def parse_and_correlate(log_line):
    """Parses raw log lines and correlates events based on security rules."""
    
    # REGEX: Match standard Linux SSH failed login format
    # Example: "Jun 20 12:00:00 server sshd[123]: Failed password for root from 192.168.1.50 port 22"
    ssh_fail_pattern = r"Failed password for (?:invalid user )?\w+ from (\d+\.\d+\.\d+\.\d+)"
    match = re.search(ssh_fail_pattern, log_line)
    
    if match:
        attacker_ip = match.group(1)
        current_time = time.time()
        
        # 1. Log Aggregation
        failed_auth_tracker[attacker_ip].append(current_time)
        print(f"[LOG INGESTED] Failed SSH attempt logged from {attacker_ip}")
        
        # 2. Data Normalization (Clean up events outside our time window)
        failed_auth_tracker[attacker_ip] = [
            t for t in failed_auth_tracker[attacker_ip] 
            if current_time - t <= TIME_WINDOW
        ]
        
        # 3. Correlation Engine 
        if len(failed_auth_tracker[attacker_ip]) >= BRUTE_FORCE_THRESHOLD:
            trigger_alert(
                alert_type="SSH Brute Force Attack",
                ip=attacker_ip,
                details=f"{BRUTE_FORCE_THRESHOLD} failed attempts detected within {TIME_WINDOW} seconds."
            )
            # Reset tracker to avoid spamming the same alert
            failed_auth_tracker[attacker_ip] = []

def follow_log(filename):
    """Generator function that yields new lines in a file as they are added (like 'tail -f')."""
    try:
        with open(filename, "r") as file:
            # Go to the end of the file
            file.seek(0, 2)
            while True:
                line = file.readline()
                if not line:
                    time.sleep(0.1) # Sleep briefly to save CPU cycles
                    continue
                yield line
    except FileNotFoundError:
        print(f"[ERROR] SIEM cannot find log file: {filename}")
        print("Please create the file or run the simulation script.")

if __name__ == "__main__":
    print("==================================================")
    print(" 👁️  Custom SIEM Engine Started")
    print(f" 📡 Monitoring log file : {LOG_FILE}")
    print(f" 🛡️  Active Rule         : SSH Brute Force (> {BRUTE_FORCE_THRESHOLD} fails / {TIME_WINDOW}s)")
    print("==================================================\n")
    
    # Start the real-time log ingestion pipeline
    for line in follow_log(LOG_FILE):
        parse_and_correlate(line)
