"""
Custom IDS/IPS Engine
Detects SYN Floods / Port Scans and dynamically updates firewall rules to block attackers.
Forwards alerts to a centralized SIEM log file.
Must be run with root privileges.
"""

from scapy.all import sniff, TCP, IP
import os
import time
from collections import defaultdict
import logging

# ==========================================
#  SIEM INTEGRATION CONFIGURATION
# ==========================================
# Configures the IDS to write alerts to a shared central file
# The format mimics the standard Linux Syslog format
logging.basicConfig(
    filename='../SOC_SIEM/central_syslog.log', # Relative path to the SIEM directory
    level=logging.INFO,
    format='%(asctime)s ids-sensor %(message)s',
    datefmt='%b %d %H:%M:%S'
)

# ==========================================
# ENGINE CONFIGURATION
# ==========================================
ALERT_THRESHOLD = 50  # Number of SYN packets before triggering a block
TIME_WINDOW = 10      # Time window in seconds
BLOCKED_IPS = set()   # Cache of already blocked IPs to prevent redundant firewall rules

# Dictionary to track connection attempts: { 'Source_IP': [timestamps] }
packet_tracker = defaultdict(list)

def block_ip(ip_address):
    """IPS Action: Blocks the IP address using Linux iptables."""
    if ip_address not in BLOCKED_IPS:
        print(f"[!!!] IPS ACTION: Blocking IP {ip_address} via iptables!")
        # System command to drop all incoming traffic from the attacker's IP
        os.system(f"iptables -A INPUT -s {ip_address} -j DROP")
        BLOCKED_IPS.add(ip_address)

def analyze_packet(packet):
    """IDS Logic: Analyzes incoming packets for malicious patterns."""
    # We only inspect TCP packets with the SYN flag (connection requests)
    if packet.haslayer(TCP) and packet.haslayer(IP):
        if packet[TCP].flags == 'S':  # 'S' = SYN flag
            src_ip = packet[IP].src
            current_time = time.time()
            
            # Record the timestamp of this connection attempt
            packet_tracker[src_ip].append(current_time)
            
            # Clean up old packet timestamps that fall outside our monitoring time window
            packet_tracker[src_ip] = [t for t in packet_tracker[src_ip] if current_time - t < TIME_WINDOW]
            
            # Check if the connection rate exceeds our defined threshold
            if len(packet_tracker[src_ip]) > ALERT_THRESHOLD:
                # 1. Print to local console
                print(f"[ALERT] IDS DETECTED SYN Flood / Port Scan from {src_ip}")
                
                # 2. Forward to Central SIEM
                logging.info(f"[IDS ALERT] Port Scan detected from {src_ip}")
                
                # 3. Trigger IPS Block
                block_ip(src_ip)

if __name__ == "__main__":
    print("--- Starting Custom IDS/IPS Engine ---")
    print("Monitoring network traffic for anomalies...")
    print("Forwarding alerts to: ../SOC_SIEM/central_syslog.log")
    # Sniff network traffic in real-time, discarding processed packets to save RAM (store=0)
    sniff(prn=analyze_packet, store=0)
