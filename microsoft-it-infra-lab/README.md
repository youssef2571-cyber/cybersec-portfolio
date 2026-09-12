# Microsoft IT Infrastructure Lab

Lab d'administration système Microsoft déployé sur infrastructure virtualisée personnelle (KVM/QEMU), couvrant les services cœur d'une infrastructure Windows Server d'entreprise : Active Directory, DNS, DHCP, GPO, File & Print Services, WSUS, et PKI (AD CS) en bonus.

Projet **purement orienté administration IT** — complémentaire à mes autres projets Blue Team/SOC (Wazuh, GNS3), sans angle offensif.

---

## Objectifs du projet

- Déployer et administrer une infrastructure Active Directory multi-contrôleurs fonctionnelle
- Mettre en place les services réseau associés (DNS, DHCP) de façon intégrée à l'annuaire
- Concevoir et déployer des stratégies de groupe (GPO) réellement appliquées et vérifiées côté client
- Administrer des services de fichiers avec gestion des permissions et des quotas
- Mettre en place un système de gestion centralisée des mises à jour (WSUS), y compris le déploiement de logiciels tiers
- Documenter chaque étape avec preuve à l'appui (capture d'écran ou sortie de commande), sans déclaration de compétence non vérifiée

---

## Architecture

**Hyperviseur :** KVM/QEMU + virt-manager, sur hôte Parrot OS (32 GB RAM / 8 cœurs / ~110 GB disque)

**Stratégie de disque :** template Windows Server 2022 unique (sysprep généralisé) + clones liés qcow2 pour chaque serveur, afin de tenir dans le budget disque disponible. Idem pour un template Windows 11 dédié aux postes clients.

### Topologie réseau

| Machine | Rôle | IP |
|---|---|---|
| DC01 | Contrôleur de domaine principal — AD DS, DNS, DHCP, AD CS (PKI) | 192.168.50.10 |
| DC02 | Contrôleur de domaine secondaire — réplication AD | 192.168.50.11 |
| SRV-FILE | Services de fichiers — partages, FSRM | 192.168.50.20 |
| SRV-WSUS | WSUS — gestion centralisée des mises à jour | 192.168.50.21 |
| CLIENT01 (client) | Windows 11 — poste de test, jointure domaine | DHCP (192.168.50.100-150) |

**Domaine :** `corp.lab.local` (NetBIOS : `CORP`)

**Structure d'OU :** `CORP-FR` (OU racine) → `IT`, `RH`, `Finance` + `Comptes-Service` et `Serveurs` en OU indépendantes

---

## Phases réalisées

### ✅ Phase 1 — Active Directory Domain Services
Forêt/domaine `corp.lab.local` créée sur DC01, structure d'OU par service, groupes de sécurité, provisioning d'utilisateurs via script PowerShell.

- `docs/screenshots/phase1-get-addomain.png` — sortie `Get-ADDomain`
- `docs/screenshots/phase1-get-adforest.png` — sortie `Get-ADForest`
- `docs/screenshots/phase1-aduc-structure.png` — structure d'OU dans ADUC
- `docs/screenshots/phase1-dcdiag.png` — `dcdiag /v` sur DC01

### ✅ Phase 2-3 — DNS / DHCP
Zone DNS intégrée à l'AD avec enregistrements pour tous les serveurs, étendue DHCP active avec réservation testée.

- `docs/screenshots/phase2-dns-records.png` — zone DNS complète
- `docs/screenshots/phase2-nslookup.png` — résolution de nom depuis un client
- `docs/screenshots/phase3-dhcp-reservation.png` — réservation DHCP active

### ✅ Phase 4 — Deuxième contrôleur de domaine (DC02)
Promotion de DC02, réplication vérifiée sans erreur.

- `docs/screenshots/phase4-repadmin.png` — `repadmin /replsummary` (0 échec)
- `docs/screenshots/phase4-domain-controllers.png` — DC01 et DC02 dans l'OU Domain Controllers

### ✅ Phase 5 — GPO (Group Policy Objects)
GPO de restriction ciblée (OU RH), GPO globale (Windows Update), mappage de lecteur réseau — appliquées et vérifiées sur un poste client réel.

- `docs/screenshots/phase5-gpmc-structure.png` — GPO dans la console GPMC
- `docs/screenshots/phase5-gpresult.png` — `gpresult /r` confirmant l'application
- `docs/screenshots/phase5-lecteur-mappe.png` — lecteur H: mappé visible côté client

### ✅ Phase 6 — File & Print Services
Partage réseau avec permissions NTFS + partage, quota FSRM appliqué.

- `docs/screenshots/phase6-fsrm-quota.png` — quota configuré (5 GB, soft)
- `docs/screenshots/phase6-acces-partage.png` — accès au partage confirmé côté client

### ✅ Phase 7 — WSUS
Rôle WSUS déployé, GPO de redirection des clients vers le serveur WSUS. Déploiement d'un package logiciel tiers (7-Zip) via import direct dans la console WSUS (au-delà du simple relais de patchs Microsoft) — cycle complet import → approbation → installation vérifiée côté client.

- `docs/screenshots/phase7-wsus-console.png` — console WSUS, serveur actif
- `docs/screenshots/phase7-gpo-windowsupdate.png` — GPO pointant vers `srv-wsus.corp.lab.local:8530`
- `docs/screenshots/phase7-package-7zip.png` — package 7-Zip importé et approuvé
- `docs/screenshots/phase7-conformite-client.png` — installation confirmée côté client

### ✅ Phase 8 — Automatisation PowerShell
Scripts réutilisables pour le provisioning et l'audit d'annuaire.

- `docs/screenshots/phase8-audit-script.png` — exécution de `ad-audit-report.ps1`
- `scripts/bulk-user-provisioning.ps1`
- `scripts/ad-audit-report.ps1`

### ✅ Bonus — AD CS (PKI interne)
Autorité de certification d'entreprise déployée sur DC01, au-delà du périmètre initial prévu.

- `docs/screenshots/bonus-pki-certsrv.png` — console de l'autorité de certification

### ❌ Phase 10 — Azure AD Connect / Entra ID hybride (non réalisée)
Cette phase n'a pas pu être menée à terme : le compte étudiant Microsoft disponible était verrouillé par l'administration de l'établissement, empêchant l'activation d'un tenant Entra ID. La création d'un tenant via un compte personnel nécessite par ailleurs une vérification par carte bancaire (politique Microsoft), ce qui sortait du cadre pratique de ce lab. La phase reste documentée à titre de référence architecturale dans le guide technique, mais non validée en pratique.

---

## Structure du dépôt

```
microsoft-it-infra-lab/
├── README.md
├── guide-microsoft-it-infra-lab.md   # guide détaillé étape par étape
├── docs/
│   └── screenshots/                   # toutes les preuves par phase
├── scripts/
│   ├── bulk-user-provisioning.ps1
│   ├── ad-audit-report.ps1
│   └── users.csv                      # données factices
└── configs/
    └── gpo-backups/                   # exports GPO (Backup-GPO)
```

---

## Compétences démontrées

- Déploiement et administration Active Directory multi-DC (forêt, domaine, OU, GPO, réplication)
- Administration DNS/DHCP intégrés à l'annuaire
- Conception et déploiement de stratégies de groupe avec vérification d'application réelle
- Administration de services de fichiers (permissions NTFS/partage, quotas FSRM)
- Gestion centralisée des mises à jour et déploiement logiciel via WSUS
- Automatisation d'administration via PowerShell (provisioning, audit)
- Notions de PKI d'entreprise (AD CS)
- Optimisation d'infrastructure de virtualisation sous contrainte de ressources (clones liés qcow2, gestion disque)

---

## Méthodologie

Chaque compétence listée ici a été vérifiée manuellement dans le lab avant d'être documentée : aucune affirmation sans capture d'écran ou sortie de commande à l'appui. Les limites rencontrées (WSUS, Entra ID) sont documentées avec la même rigueur que les réussites.
