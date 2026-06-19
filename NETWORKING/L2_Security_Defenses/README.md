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
