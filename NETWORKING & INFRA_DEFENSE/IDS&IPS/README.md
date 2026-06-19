# 🛡️ Active Network Defense: Custom IDS/IPS Engine

This project features a custom-built Intrusion Detection and Prevention System (IDS/IPS) written in Python. It demonstrates the ability to monitor network traffic in real-time, identify malicious patterns, and dynamically interact with the operating system's firewall to neutralize threats.

## 🧠 Core Architecture

### 1. Intrusion Detection (IDS)
The detection engine utilizes `Scapy` to perform deep packet inspection. 
* **Anomaly Detection:** It currently tracks TCP SYN packets to identify aggressive behavior, such as stealth port scans (e.g., Nmap) or DoS attempts (SYN Floods).
* **Time-Window Logic:** It uses a moving time window to track connection rates per source IP, minimizing false positives.

### 2. Intrusion Prevention (IPS)
Detection is only the first step. The IPS component acts autonomously to protect the infrastructure.
* **Dynamic Firewalling:** Once a threshold is breached, the engine executes system-level commands to dynamically append dropping rules to the Linux `iptables` firewall.
* **Automated Containment:** The attacker's IP is instantly blackholed, preventing any further interaction with the host or network.

## 🛠️ Technical Stack
* **Language:** Python 3
* **Packet Manipulation:** `Scapy` library
* **System Integration:** `os` module for `iptables` / Linux Netfilter interaction
* **Concepts:** Real-time traffic sniffing, TCP Flags analysis, Dynamic Firewall configuration.

## 🚀 Future Enhancements
* Implementing a signature-based detection engine (reading rules from a JSON file).
* Forwarding alerts to a centralized SIEM using Syslog.
