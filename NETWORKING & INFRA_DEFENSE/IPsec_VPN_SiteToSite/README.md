# 🛡️ IPsec Site-to-Site VPN Architecture
**A Proof of Concept (PoC) by NY² Networking & Infrastructure**

## 📌 Project Objective
Design and implementation of a highly secure, encrypted Site-to-Site communication channel over an untrusted public network (WAN). This project demonstrates advanced routing, cryptographic tunneling (IPsec), and deep packet inspection evasion.

## 🛠️ Technologies & Protocols
* **Hypervisor:** GNS3 (Native KVM/QEMU)
* **Infrastructure:** Cisco IOSv 15.7 (Layer 3 Routing)
* **Cryptography:** IKEv1, AES-256 (Encryption), SHA-256 (Hashing), Diffie-Hellman Group 14
* **Analysis:** Wireshark & `dumpcap`

---

## 🏗️ Phase 1: Infrastructure Design
The topology simulates two isolated corporate LANs connected via a public ISP. 
* **Site 1 LAN:** `10.0.0.0/8`
* **Site 2 LAN:** `30.0.0.0/8`
* **WAN Links:** `101.0.0.0/24` and `102.0.0.0/24`

![Architecture](1-topology-ipsec-site-to-site.png)

---

## 🔐 Phase 2: Cryptographic Implementation
Implementation of an IPsec tunnel using a robust Transform Set. The Security Associations (SA) were verified natively within the Cisco IOS environment, confirming the successful negotiation of Phase 1 (ISAKMP) and Phase 2 (IPsec).

![ISAKMP Status](2-crypto-sa-verification.png)
*> Status QM_IDLE and ACTIVE confirms the mathematical exchange is stable.*

---

## 📡 Phase 3: End-to-End Connectivity
Validation of the routing tables and Access Control Lists (ACLs). The ICMP traffic successfully travels from Site 1 (PC1) to Site 2 (PC2) triggering the encryption engine.

![Connectivity Test](3-end-to-end-connectivity.png)

---

## 🕵️‍♂️ Phase 4: Man-in-the-Middle Verification (The Proof)
To prove the infrastructure's resilience against eavesdropping, a packet capture was initiated on the public ISP link. As expected, internal IP addresses and ICMP protocols are completely obfuscated, encapsulated within the **ESP (Encapsulating Security Payload)** protocol. 

![Wireshark ESP Proof](4-wireshark-esp-encryption-proof.png)
*> The payload is rendered mathematically unreadable to unauthorized external actors.*
