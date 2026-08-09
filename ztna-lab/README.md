# ZTNA Lab — Zero Trust Network Access avec Teleport, GitHub SSO & Wazuh

Architecture Zero Trust Network Access (ZTNA) complète, déployée sur un lab virtualisé de 3 machines (2 VMs KVM + hôte), avec authentification SSO, MFA, RBAC granulaire, enregistrement de session, et détection SOC intégrée mappée MITRE ATT&CK.

![Architecture](docs/architecture-diagram.png)

## Sommaire

- [Objectif du projet](#objectif-du-projet)
- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Fonctionnalités implémentées](#fonctionnalités-implémentées)
- [Choix techniques et limitations](#choix-techniques-et-limitations)
- [Journal de débogage](#journal-de-débogage)
- [Détection SOC et mapping MITRE ATT&CK](#détection-soc-et-mapping-mitre-attck)
- [Tests et validation](#tests-et-validation)
- [Installation](#installation)
- [Améliorations possibles](#améliorations-possibles)

---

## Objectif du projet

Concevoir et déployer une architecture Zero Trust Network Access de bout en bout : authentification centralisée, accès aux ressources basé sur les rôles (RBAC) plutôt que sur la position réseau, traçabilité complète des sessions, et intégration avec un SOC pour la détection d'anomalies — le tout sur une infrastructure virtualisée réaliste plutôt qu'un déploiement monolithique.

## Architecture

Le lab repose sur 3 machines distinctes communicant sur un réseau NAT virtuel (`192.168.122.0/24` via KVM/libvirt) :

| Machine | Rôle | Détail |
|---|---|---|
| **VM2** (192.168.122.55) | Teleport Auth + Proxy (Docker) + Node SSH cible | Point d'entrée ZTNA, service `vm2-machine-hote` enrôlé comme ressource SSH |
| **Machine hôte** (SOC/SIEM) | Wazuh Manager (Docker) | Réception et corrélation des logs d'audit Teleport, dashboard MITRE ATT&CK |
| **GitHub** (IdP externe) | Fournisseur SSO | Organisation `ztna-lab-youssef` avec 3 équipes mappées à 3 rôles Teleport |

**Flux d'authentification et d'accès :**
```
Utilisateur (navigateur) 
  → HTTPS/3080 → Teleport Proxy (VM2, mode multiplex)
  → SSO GitHub (OAuth) + MFA WebAuthn
  → Mapping équipe GitHub → rôle Teleport (RBAC)
  → Accès SSH à vm2-machine-hote (si autorisé)
  → Logs d'audit JSON → montage volume → Agent Wazuh (VM2)
  → Wazuh Manager (hôte) → règles de détection → dashboard MITRE ATT&CK
```

Voir le schéma complet dans [`docs/architecture-diagram.png`](docs/architecture-diagram.png).

## Stack technique

- **Teleport Community Edition 16.5.18** (Docker) — Proxy, Auth, gestion des accès SSH
- **GitHub Organization SSO** — fournisseur d'identité (OAuth App + équipes)
- **WebAuthn** — MFA au niveau Teleport
- **Wazuh 4.9.2** (Docker) — SIEM/SOC, agent + manager
- **KVM/QEMU + libvirt** — virtualisation (2 VMs Ubuntu Server 24.04 LTS)
- **mkcert** — certificats TLS locaux multi-SAN pour le lab

## Fonctionnalités implémentées

- ✅ SSO via GitHub Organization (OAuth), avec mapping d'équipes vers rôles Teleport
- ✅ MFA WebAuthn obligatoire après le SSO
- ✅ RBAC à 4 rôles : `ztna-admin`, `ztna-dev`, `ztna-guest`, `auditor`
- ✅ Accès SSH via terminal web intégré (aucun port SSH exposé directement au client)
- ✅ Enregistrement et rejeu de sessions (session recording)
- ✅ Audit log centralisé consultable dans l'interface Teleport (SSO login, certificats, connexions/déconnexions, tentatives échouées)
- ✅ Intégration Wazuh : agent sur VM2, remontée des logs Teleport au manager sur l'hôte
- ✅ Règles de détection personnalisées mappées MITRE ATT&CK (T1110 brute force, T1078 comptes valides)
- ✅ Dashboard SOC avec tactiques détectées (Defense Evasion, Privilege Escalation, Initial Access, Persistence)

## Choix techniques et limitations

**Pivot Keycloak → GitHub SSO.** Le plan initial prévoyait Keycloak comme fournisseur d'identité via un connecteur OIDC. En cours de déploiement, il s'est avéré que **Teleport Community Edition ne supporte pas OIDC ni SAML** — ces connecteurs sont réservés à Teleport Enterprise. Seul le SSO GitHub natif est disponible gratuitement en Community.

Décision : pivoter vers GitHub Organization SSO, avec des équipes GitHub (`ztna-admins`, `ztna-devs`, `ztna-guests`) mappées aux rôles Teleport via `teams_to_roles`, en lieu et place du claim `groups` OIDC initialement prévu. L'architecture RBAC, MFA, et l'intégration Wazuh restent identiques — seul le fournisseur d'identité change.

**Limitation assumée :** ce lab utilise un stockage de session en mémoire (`start-dev` côté Keycloak initialement envisagé, mais non retenu) et un mode single-node pour Teleport et Wazuh — non représentatif d'un déploiement haute disponibilité en production.

## Journal de débogage

L'enrôlement du nœud SSH (`vm2-machine-hote`) a nécessité de résoudre une série de blocages en chaîne, documentés ici car ils illustrent bien les couches réseau/TLS/RBAC de Teleport :

| # | Symptôme | Cause | Résolution |
|---|---|---|---|
| 1 | `token expired or not found` | Token d'enrôlement à durée de vie courte, expiré avant exécution | Régénération immédiate + exécution sans délai |
| 2 | `ssh: handshake failed: EOF` sur le tunnel inversé | Port `3024` (tunnel dédié) non exposé dans `docker-compose.yml`, agent ne pouvait pas dialoguer avec le proxy | Activation de `proxy_listener_mode: multiplex` pour router tout le trafic (web, tunnel, gRPC) sur le port `3080` |
| 3 | `field proxy_service already set` | Duplication accidentelle d'un bloc YAML lors d'une édition | Fusion des deux blocs `proxy_service` en un seul |
| 4 | `field proxy_listener_mode not found in type config.Proxy` | Paramètre placé dans le mauvais bloc (`proxy_service` au lieu de `auth_service`) | Déplacement de `proxy_listener_mode` sous `auth_service` |
| 5 | `certificate is valid for teleport.ztna.lab, not localhost` | Test interne Teleport (`IsALPNConnUpgradeRequired`) sondant le proxy avec un SNI générique `localhost`, non couvert par le certificat mkcert d'origine | Régénération du certificat en multi-SAN : `mkcert teleport.ztna.lab localhost 127.0.0.1` |
| 6 | `did not find expected '-' indicator` (YAML) | Indentation incohérente dans le bloc `https_keypairs` après édition | Correction de l'alignement (espaces stricts, pas de tabulation) |

Cette séquence illustre un vrai cas de dépannage multi-couches (join token → tunnel réseau → configuration → TLS/PKI), plutôt qu'un déploiement linéaire sans accroc.

## Détection SOC et mapping MITRE ATT&CK

Règles Wazuh personnalisées créées pour ce lab (`/var/ossec/etc/rules/local_rules.xml`), dans le groupe `ztna` :

| ID règle | Description | Technique MITRE |
|---|---|---|
| 100200 | Échec d'authentification Teleport | T1110 (Brute Force) |
| 100201 | 5 échecs en 120s → alerte niveau 10 | T1110 (Brute Force) |
| 100202 | Connexion en dehors des heures normales (21h–6h) | T1078 (Valid Accounts) |

Le dashboard Wazuh confirme la remontée effective des logs, avec détection de tactiques MITRE ATT&CK réparties sur l'agent `vm2` : Defense Evasion, Privilege Escalation, Initial Access, Persistence.

## Tests et validation

| Scénario | Méthode | Résultat |
|---|---|---|
| Accès légitime | Connexion SSO + accès SSH via terminal web | ✅ Accordé selon le rôle |
| MFA | Reconnexion après SSO GitHub | ✅ Prompt WebAuthn affiché |
| Session recording | Connexion SSH suivie de consultation dans Session Recordings | ✅ 6 sessions enregistrées et rejouables |
| Audit trail | Consultation de l'Audit Log | ✅ Historique complet (login, certificats, sessions, échecs) |
| Remontée Wazuh | Vérification agent + dashboard | ✅ Agent actif, 54 événements sur 24h |
| Détection MITRE | Dashboard Threat Hunting / MITRE ATT&CK | ✅ Tactiques identifiées et classées |

## Installation

> Lab reproductible sur un environnement KVM/libvirt avec accès Internet pour GitHub SSO.

1. Provisionner 2 VMs Ubuntu Server 24.04 sur un réseau NAT KVM (`virtual network default`)
2. Configurer `/etc/hosts` sur les 3 machines pour la résolution `teleport.ztna.lab`
3. Générer les certificats TLS multi-SAN avec `mkcert`
4. Déployer Teleport via `docker/teleport/docker-compose.yml`
5. Créer l'organisation GitHub, les équipes, et l'OAuth App
6. Générer et appliquer le connecteur GitHub (`tctl sso configure github`)
7. Enrôler le nœud SSH cible
8. Déployer Wazuh Manager sur l'hôte, agent sur VM2
9. Appliquer les règles de détection personnalisées


## Améliorations possibles

- Device Trust (nécessite Teleport Enterprise) pour une posture Zero Trust complète incluant la confiance machine
- Haute disponibilité (cluster Teleport multi-nœuds, Wazuh en cluster)
- Intégration d'une ressource applicative web supplémentaire (Application Access)
- Automatisation du déploiement via Ansible/Terraform plutôt que configuration manuelle
- Rotation automatisée des certificats (actuellement mkcert statique, à remplacer par Let's Encrypt ou une PKI interne en production)

---

**Auteur :** Youssef — [github.com/youssef2571-cyber](https://github.com/youssef2571-cyber)
**Portfolio complet :** [cybersec-portfolio](https://github.com/youssef2571-cyber/cybersec-portfolio)
