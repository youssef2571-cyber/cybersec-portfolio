# 🛡️ Layer 2 Network Security Defenses

This project demonstrates the implementation of security mechanisms on Cisco switches to protect against common Data Link Layer (Layer 2) attacks.

## 1. Mitigating Rogue DHCP & ARP Spoofing .

To protect against attackers assigning false IP configurations or intercepting traffic, I implemented **DHCP Snooping** and **Dynamic ARP Inspection (DAI)**.
```text
! Enable DHCP Snooping globally and on specific VLANs
Switch(config)# ip dhcp snooping
Switch(config)# ip dhcp snooping vlan 1

! Trust the interface connected to the legitimate DHCP server
Switch(config)# interface FastEthernet 0/1
Switch(config-if)# ip dhcp snooping trust

! Enable DAI
Switch(config)# ip arp inspection vlan 1
Switch(config-if)# ip arp inspection trust 
```
 ##2. Preventing MAC Address Flooding (Port Security)   To stop an attacker from overflowing the CAM table, Port Security restricts the number of allowed MAC addresses per port.
```text
Switch(config)# interface FastEthernet 0/10
Switch(config-if)# switchport mode access
Switch(config-if)# switchport port-security
Switch(config-if)# switchport port-security maximum 1
Switch(config-if)# switchport port-security violation shutdown
Switch(config-if)# switchport port-security mac-address sticky
```
##3. Securing the Spanning Tree Protocol (STP)  
Attackers can attempt to become the Root Bridge to intercept traffic. I used Root Guard and BPDU Guard to prevent this.
```text
Prevent a rogue switch from becoming the Root Bridge on a trunk port
Switch(config-if)# spanning-tree guard root

! Disable an edge port if a BPDU is unexpectedly received
Switch(config-if)# spanning-tree bpduguard enable
