# 🌐 Network Infrastructure & Security Portfolio

This directory contains practical implementations of enterprise network architectures, focusing on robust Layer 2/Layer 3 designs, secure communications, and traffic analysis. These projects demonstrate my ability to configure, secure, and troubleshoot Cisco infrastructure.

## 📂 Core Projects

### 1. [Layer 2 Security & Hardening](./L2_Security_Defenses)
Implemented critical defenses against common Layer 2 attacks:
* **DHCP Snooping & Dynamic ARP Inspection (DAI):** Mitigated Rogue DHCP and ARP Poisoning attacks.
* **Port Security:** Protected against MAC Address Flooding and unauthorized access.
* **STP Protection:** Configured `BPDU Guard` and `Root Guard` to prevent Spanning Tree manipulation.
* **AAA / RADIUS:** Centralized administrator authentication for VTY lines.

### 2. [Site-to-Site IPsec VPN](./IPsec_VPN_SiteToSite)
Designed and deployed a secure VPN tunnel across a simulated public network.
* **Phase 1 (ISAKMP/IKE):** Configured pre-shared keys (PSK), AES encryption, and Diffie-Hellman Group 2.
* **Phase 2 (IPsec):** Implemented ESP-AES and ESP-SHA-HMAC transform sets.
* Configured Access Control Lists (ACLs) to define interesting traffic and implemented NAT Overload (PAT).

### 3. [VLAN Architecture & Inter-VLAN Routing](./VLAN_Routing_RouterOnAStick)
Structured a segmented campus network.
* Configured access ports, 802.1Q trunking, and managed the VLAN database.
* Implemented **Router-on-a-Stick** using sub-interfaces for inter-VLAN routing.

### 4. [Traffic Analysis & Anomaly Detection](./Traffic_Analysis_Wireshark)
Utilized Wireshark for deep packet inspection and network troubleshooting.
* Analyzed TCP flags, UDP datagrams (DNS), and encapsulated protocols (HTTP/TLS).
* Used statistical tools (IO Graphs, Protocol Hierarchy) to detect simulated network anomalies (ICMP flooding).

### 5. [Spanning Tree Protocol (STP) Operations](./L2_Switching_STP)
Managed redundant links to ensure loop-free topologies.
* Analyzed Root Bridge elections, Designated Ports, and Alternate/Blocked ports.
* Verified active network paths and MAC address table propagation.

## 🛠️ Technical Stack
* **Hardware/Simulation:** Cisco IOS, Packet Tracer
* **Protocols:** STP, 802.1Q, ISAKMP/IKE, IPsec, ESP, NAT, RADIUS, DHCP, ARP, ICMP
* **Tools:** Wireshark
