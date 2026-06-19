# 🛡️ Secure Site-to-Site IPsec VPN & Firewall Architecture

This repository demonstrates a complete, enterprise-grade secure interconnection between two remote networks over an untrusted transit network (the Internet). It highlights the critical intersection of **Firewalling (NAT/ACLs)** and **Cryptographic Tunnels (IPsec)**.

## 🏗️ Architecture Overview

The topology simulates two corporate sites:
* **Site 1 (Internal LAN):** `10.0.0.0/8`
* **Site 2 (Remote LAN):** `30.0.0.0/8`
* **Untrusted Network:** Simulated Internet routing between the two edge gateways.

The edge routers act as both **Stateful Firewalls** (handling Network Address Translation for regular internet traffic) and **VPN Gateways** (encrypting traffic destined for the remote corporate site).

## 🧠 Core Engineering Concepts

### 1. Firewall & NAT Exemption (The Logic)
A common pitfall in VPN configuration is having the NAT process override the VPN process. To solve this, a strict **Access Control List (ACL)** is implemented.
* **NAT Overload (PAT):** Allows internal users to browse the public internet.
* **NAT Exemption (Deny Rule):** The firewall explicitly *denies* NAT translation for traffic going from `10.0.0.0/8` to `30.0.0.0/8`. This ensures the packet retains its original private IP, allowing the VPN Crypto Map to intercept it.

### 2. IPsec Phase 1: ISAKMP (IKE)
Establishes a secure, authenticated management channel between the two gateways.
* **Encryption:** AES
* **Hashing:** SHA-1
* **Authentication:** Pre-Shared Key (PSK)
* **Key Exchange:** Diffie-Hellman Group 2 (1024-bit)

### 3. IPsec Phase 2: Data Encapsulation
Defines how the actual user data is protected while traversing the tunnel.
* **Transform-Set:** `ESP-AES` for data confidentiality and `ESP-SHA-HMAC` for data integrity.
* **Interesting Traffic:** An extended ACL defines exactly which packets should trigger the cryptographic engine.

---

## 🔍 Packet Inspection Flow

When a packet arrives at the internal interface of the gateway, it undergoes the following decision matrix:

1. **Destined for the Public Internet (e.g., 8.8.8.8)?**
   * **Firewall Action
