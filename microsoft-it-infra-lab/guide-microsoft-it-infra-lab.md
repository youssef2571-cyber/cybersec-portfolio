# Guide détaillé — Microsoft IT Infrastructure Lab
### Déploiement AD DS / DNS / DHCP / GPO / File Services / WSUS sur KVM

---

## 0. Prérequis

**Matériel (ton lab actuel : 32 GB RAM / 8 cœurs) :**
- Hyperviseur : KVM/QEMU + `virt-manager` (déjà en place)
- ISO Windows Server 2022 Evaluation (180 jours, gratuit) : https://www.microsoft.com/evalcenter/evaluate-windows-server-2022
- ISO Windows 10/11 Evaluation pour les postes clients

**Réseau virtuel :**
- Créer un réseau NAT ou isolé dédié dans `virt-manager` : `virsh net-define` ou via l'interface graphique
- Réseau : `192.168.50.0/24` (à adapter si conflit avec ton lab GNS3/Wazuh existant)

**Plan d'adressage IP :**

| VM | Rôle | IP | 
|---|---|---|
| DC01 | AD DS + DNS (contrôleur principal) | 192.168.50.10 |
| DC02 | AD DS + DNS (réplication, optionnel) | 192.168.50.11 |
| SRV-FILE | File & Print, FSRM | 192.168.50.20 |
| SRV-WSUS | WSUS | 192.168.50.21 |
| SRV-PKI | AD CS (optionnel) | 192.168.50.22 |
| CLIENT01 | Windows 10/11 | DHCP (plage 192.168.50.100-150) |
| CLIENT02 | Windows 10/11 | DHCP |

**ISO à utiliser par VM :**

| VM | ISO |
|---|---|
| DC01, DC02 | Windows Server 2022 Evaluation — même ISO, choisir **"Desktop Experience"** pour DC01 (interface graphique, plus simple pour débuter) et **"Server Core"** pour DC02 (montée en compétence CLI) |
| SRV-FILE | Windows Server 2022 Evaluation — Desktop Experience ou Core, au choix |
| SRV-WSUS | Windows Server 2022 Evaluation — même ISO que les autres (aucun ISO spécifique WSUS n'existe : c'est un rôle installé après coup avec `Install-WindowsFeature`) |
| SRV-PKI | Windows Server 2022 Evaluation — même ISO (AD CS est aussi un simple rôle Windows, pas un produit à part) |
| CLIENT01, CLIENT02 | Windows 10/11 Evaluation |

➡️ En résumé : **un seul ISO serveur** (`Windows Server 2022 Evaluation`, ~180 jours gratuits) suffit pour DC01, DC02, SRV-FILE, SRV-WSUS et SRV-PKI. Tu l'installes 5 fois (ou tu clones un template de base une fois installé, pour gagner du temps), puis chaque machine devient "spécialisée" uniquement via les rôles PowerShell (`Install-WindowsFeature`) installés dans les phases suivantes — pas via une image différente.

**Nom de domaine du lab :** `corp.lab.local` (nommage volontairement non-routable, bonne pratique)

---

## Phase 0 — Provisioning des VMs

### 0.1 Contrainte disque : 110 Go disponibles → stratégie de clones liés (linked clones)

Avec 5-7 VMs Windows Server/Client, des disques "pleins" de 40-60 Go chacun ne tiennent pas dans 110 Go. La solution standard en labs KVM : **un template de base par OS, puis des clones liés en qcow2** — chaque VM ne stocke que ses *différences* par rapport au template, pas une copie complète.

**Principe :**
1. Installer Windows Server 2022 **une seule fois** dans une VM "template", la patcher, puis la généraliser avec `sysprep` (retire le SID/nom machine pour pouvoir la cloner proprement).
2. Convertir ce disque en image de base réutilisable (lecture seule).
3. Créer chaque VM (DC01, DC02, SRV-FILE, etc.) comme un **clone lié** qui pointe vers cette base — le fichier qcow2 de la VM ne grossit qu'avec les changements propres à cette machine.

**Commandes (depuis l'hôte, après avoir sysprep la VM template et l'avoir arrêtée) :**
```bash
# Convertir/déplacer le disque template comme image de base en lecture seule
mkdir -p /var/lib/libvirt/images/templates
mv /var/lib/libvirt/images/win-server-template.qcow2 /var/lib/libvirt/images/templates/base-winserver2022.qcow2

# Créer un clone lié pour DC01 (le fichier ne contient que les diffs)
qemu-img create -f qcow2 -F qcow2 -b /var/lib/libvirt/images/templates/base-winserver2022.qcow2 \
  /var/lib/libvirt/images/dc01.qcow2 40G

# Idem pour DC02, SRV-FILE, SRV-WSUS, SRV-PKI (une commande par VM)
qemu-img create -f qcow2 -F qcow2 -b /var/lib/libvirt/images/templates/base-winserver2022.qcow2 \
  /var/lib/libvirt/images/srv-file.qcow2 40G
```
Le `40G` ici est une **taille maximale allouable**, pas de l'espace réservé immédiatement (qcow2 est thin-provisioned par défaut) — la VM peut grossir jusqu'à cette limite mais ne consomme réellement que ce qu'elle écrit.

Fais la même chose avec un template Windows 10/11 sysprep pour CLIENT01/CLIENT02.

**Pour créer la VM dans virt-manager à partir d'un disque déjà existant :** lors de la création, choisir *"Import existing disk image"* et pointer vers `dc01.qcow2` au lieu de laisser l'assistant en créer un.

### 0.2 Dimensionnement révisé (réaliste pour 110 Go)

| VM | Disque alloué (max) | Usage réel estimé |
|---|---|---|
| Template Windows Server 2022 (base) | — | ~15-18 GB |
| Template Windows 10/11 (base) | — | ~12-15 GB |
| DC01 | 40 GB | ~6-10 GB |
| DC02 (optionnel) | 40 GB | ~6-10 GB |
| SRV-FILE | 40 GB | ~8-12 GB (dépend des fichiers de test que tu ajoutes) |
| SRV-WSUS | 50 GB | ~15-25 GB — **limite le nombre de produits/langues synchronisés dans WSUS**, c'est ce qui fait exploser l'espace le plus vite |
| SRV-PKI (optionnel) | 30 GB | ~6-8 GB |
| CLIENT01/02 | 30 GB chacun | ~8-10 GB chacun |

**Total réel estimé en faisant tourner tout en simultané, sur la durée du projet : ~75-95 Go** — ça tient dans tes 110 Go, mais sans grand confort. Recommandations pratiques :
- Ne fais **pas tourner toutes les VMs en même temps** — allume seulement celles nécessaires à la phase en cours (DC01+DC02 pour la Phase 4, puis DC01+SRV-WSUS pour la Phase 7, etc.)
- Active le TRIM/discard pour que l'espace libéré *dans* la VM (fichiers supprimés) soit vraiment rendu à l'hôte : dans la config XML libvirt du disque, ajoute `discard='unmap'` sur l'élément `<driver>`, puis lance `fstrim -v /` (ou l'équivalent Windows `Optimize-Volume -DriveLetter C -ReTrim`) périodiquement dans le guest.
- Supprime le template Windows 10/11 une fois CLIENT01/CLIENT02 créés si tu manques de place — tu n'en as besoin que pour créer de nouveaux clones.
- Surveille l'usage réel avec `du -sh /var/lib/libvirt/images/*.qcow2` sur l'hôte plutôt que la taille allouée.

### 0.3 Créer la VM template et démarrer DC01

1. Créer une VM "template" dans `virt-manager` :
   - 4 vCPU, 4 GB RAM, 40 GB disque qcow2 (virtio), réseau NAT/isolé créé plus haut
   - Boot sur l'ISO Windows Server 2022
2. Installation Windows Server : choisir **"Desktop Experience"** (interface graphique, plus simple pour débuter — tu feras du Server Core sur un clone dédié plus tard pour monter en compétence CLI)
3. Une fois l'OS installé et patché, exécuter `sysprep /generalize /oobe /shutdown` pour préparer le template, puis suis la procédure de clonage en 0.1.
4. Sur le clone destiné à devenir DC01, une fois démarré et le mini-setup OOBE passé, configurer l'IP statique :
```powershell
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.50.10 -PrefixLength 24 -DefaultGateway 192.168.50.1
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses 127.0.0.1
Rename-Computer -NewName "DC01" -Restart
```

---

## Phase 1 — Active Directory Domain Services (DC01)

### 1.1 Installer le rôle AD DS
```powershell
Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools
```

### 1.2 Promouvoir le serveur en contrôleur de domaine (nouvelle forêt)
```powershell
Import-Module ADDSDeployment
Install-ADDSForest `
  -DomainName "corp.lab.local" `
  -DomainNetbiosName "CORP" `
  -InstallDns:$true `
  -SafeModeAdministratorPassword (ConvertTo-SecureString "TonMotDePasseDSRM!" -AsPlainText -Force) `
  -Force:$true
```
Le serveur redémarre automatiquement. **Documente le temps de promotion et les logs** (`C:\Windows\debug\dcpromo.log`) pour ton README.

### 1.3 Vérifier la santé du contrôleur de domaine
```powershell
dcdiag /v
Get-ADDomain
Get-ADForest
nltest /dsgetdc:corp.lab.local
```
➡️ Capture d'écran de `dcdiag` propre (0 erreur) = preuve à inclure dans ton repo GitHub.

### 1.4 Créer la structure d'unités d'organisation (OU)
Modéliser par service/site, pas par type d'objet — c'est la bonne pratique testée en entretien :
```powershell
New-ADOrganizationalUnit -Name "CORP-FR" -Path "DC=corp,DC=lab,DC=local"
New-ADOrganizationalUnit -Name "IT" -Path "OU=CORP-FR,DC=corp,DC=lab,DC=local"
New-ADOrganizationalUnit -Name "RH" -Path "OU=CORP-FR,DC=corp,DC=lab,DC=local"
New-ADOrganizationalUnit -Name "Finance" -Path "OU=CORP-FR,DC=corp,DC=lab,DC=local"
New-ADOrganizationalUnit -Name "Comptes-Service" -Path "DC=corp,DC=lab,DC=local"
New-ADOrganizationalUnit -Name "Serveurs" -Path "DC=corp,DC=lab,DC=local"
```

### 1.5 Créer des groupes de sécurité
```powershell
New-ADGroup -Name "G-IT-Admins" -GroupScope Global -GroupCategory Security -Path "OU=IT,OU=CORP-FR,DC=corp,DC=lab,DC=local"
New-ADGroup -Name "G-RH-Users" -GroupScope Global -GroupCategory Security -Path "OU=RH,OU=CORP-FR,DC=corp,DC=lab,DC=local"
```

### 1.6 Provisionner des utilisateurs en masse (script réutilisable)
Créer un CSV `users.csv` :
```csv
Prenom,Nom,Service,Login
Youssef,Alami,IT,yalami
Sara,Bennis,RH,sbennis
Karim,Idrissi,Finance,kidrissi
```
Script `bulk-user-provisioning.ps1` :
```powershell
$Users = Import-Csv -Path ".\users.csv"
foreach ($u in $Users) {
    $OUPath = "OU=$($u.Service),OU=CORP-FR,DC=corp,DC=lab,DC=local"
    New-ADUser -Name "$($u.Prenom) $($u.Nom)" `
        -GivenName $u.Prenom -Surname $u.Nom `
        -SamAccountName $u.Login -UserPrincipalName "$($u.Login)@corp.lab.local" `
        -Path $OUPath -AccountPassword (ConvertTo-SecureString "P@ssw0rd2026!" -AsPlainText -Force) `
        -Enabled $true -ChangePasswordAtLogon $true
    Write-Host "Créé : $($u.Login) dans $OUPath"
}
```
➡️ C'est ton premier script à mettre dans `scripts/` sur GitHub — documente le comptage (nombre d'utilisateurs créés, temps d'exécution).

---

## Phase 2 — DNS

### 2.1 Vérifier la zone intégrée AD
```powershell
Get-DnsServerZone
```
La zone `corp.lab.local` doit apparaître en type `Primary` avec `IsDsIntegrated: True`.

### 2.2 Configurer les redirecteurs (forwarders) pour la résolution Internet
```powershell
Set-DnsServerForwarder -IPAddress 8.8.8.8, 1.1.1.1
```

### 2.3 Créer des enregistrements utiles
```powershell
Add-DnsServerResourceRecordA -Name "srv-file" -ZoneName "corp.lab.local" -IPv4Address 192.168.50.20
Add-DnsServerResourceRecordA -Name "srv-wsus" -ZoneName "corp.lab.local" -IPv4Address 192.168.50.21
Add-DnsServerResourceRecordCName -Name "intranet" -HostNameAlias "srv-file.corp.lab.local" -ZoneName "corp.lab.local"
```

### 2.4 Créer une zone de recherche inversée (bonne pratique à documenter)
```powershell
Add-DnsServerPrimaryZone -NetworkID "192.168.50.0/24" -ReplicationScope "Domain"
```

---

## Phase 3 — DHCP

### 3.1 Installer et autoriser le rôle
```powershell
Install-WindowsFeature -Name DHCP -IncludeManagementTools
Add-DhcpServerInDC -DnsName "DC01.corp.lab.local" -IPAddress 192.168.50.10
```

### 3.2 Créer l'étendue (scope)
```powershell
Add-DhcpServerv4Scope -Name "CORP-LAN" -StartRange 192.168.50.100 -EndRange 192.168.50.150 -SubnetMask 255.255.255.0 -State Active
Set-DhcpServerv4OptionValue -ScopeId 192.168.50.0 -DnsServer 192.168.50.10 -DnsDomain "corp.lab.local" -Router 192.168.50.1
```

### 3.3 Réservation pour un poste client (démonstration de compétence)
```powershell
Get-DhcpServerv4Lease -ScopeId 192.168.50.0  # récupérer l'adresse MAC du client après premier bail
Add-DhcpServerv4Reservation -ScopeId 192.168.50.0 -IPAddress 192.168.50.101 -ClientId "AA-BB-CC-DD-EE-FF" -Description "CLIENT01"
```

---

## Phase 4 (optionnel) — Deuxième contrôleur de domaine (DC02) : haute disponibilité

1. Provisionner DC02 (Server Core recommandé pour progresser en CLI), IP 192.168.50.11, DNS pointé vers DC01 dans un premier temps.
2. Joindre puis promouvoir :
```powershell
Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools
Install-ADDSDomainController -DomainName "corp.lab.local" -Credential (Get-Credential CORP\Administrateur) -SafeModeAdministratorPassword (ConvertTo-SecureString "TonMotDePasseDSRM!" -AsPlainText -Force)
```
3. Vérifier la réplication (élément clé à documenter/capturer) :
```powershell
repadmin /replsummary
repadmin /showrepl
```
4. Basculer le DHCP en failover pour tolérance de panne :
```powershell
Add-DhcpServerv4Failover -Name "CORP-Failover" -ScopeId 192.168.50.0 -PartnerServer "DC02.corp.lab.local" -Mode LoadBalance
```

---

## Phase 5 — GPO (Group Policy Objects)

### 5.1 Politique de mots de passe et de verrouillage (Default Domain Policy)
```powershell
Set-ADDefaultDomainPasswordPolicy -Identity "corp.lab.local" -MinPasswordLength 12 -PasswordHistoryCount 10 -LockoutThreshold 5 -LockoutDuration "00:15:00" -ComplexityEnabled $true
```
➡️ Capture GPMC (`gpmc.msc`) montrant la stratégie appliquée.

### 5.2 Créer une GPO ciblée (ex : restriction panneau de configuration pour RH)
```powershell
New-GPO -Name "GPO-RH-Restrictions" | New-GPLink -Target "OU=RH,OU=CORP-FR,DC=corp,DC=lab,DC=local"
```
Puis configurer via l'éditeur GPO (`gpedit` distant) : User Configuration → Administrative Templates → Control Panel → Prohibit access to Control Panel.

### 5.3 Mappage de lecteur réseau via GPO (Group Policy Preferences)
- GPMC → GPO → User Configuration → Preferences → Windows Settings → Drive Maps
- Lecteur `H:` → `\\srv-file\Partage-RH$` pour l'OU RH

### 5.4 Redirection de dossiers (Documents → serveur de fichiers)
- User Configuration → Policies → Windows Settings → Folder Redirection → Documents → Basic → `\\srv-file\Redirect$\%username%`

### 5.5 Déploiement logiciel via GPO (ex : 7-Zip en MSI)
- Computer Configuration → Policies → Software Settings → Software Installation → New Package → pointer vers un partage réseau contenant le `.msi`

### 5.6 Exporter tes GPO pour versionner sur GitHub
```powershell
Backup-GPO -All -Path "C:\GPO-Backups"
```
➡️ Copier le dossier dans `configs/gpo-backups/` de ton repo (attention : pas de secrets/mots de passe dedans).

---

## Phase 6 — File & Print Services

### 6.1 Installer le rôle sur SRV-FILE
```powershell
Install-WindowsFeature -Name FS-FileServer, FS-Resource-Manager -IncludeManagementTools
```

### 6.2 Créer les partages avec permissions NTFS + partage (double couche à documenter)
```powershell
New-Item -Path "D:\Partages\RH" -ItemType Directory
New-SmbShare -Name "Partage-RH$" -Path "D:\Partages\RH" -FullAccess "CORP\G-RH-Users"
icacls "D:\Partages\RH" /grant "CORP\G-RH-Users:(OI)(CI)M"
```
➡️ **Point important à expliquer en entretien** : la différence entre permissions de partage (niveau réseau) et permissions NTFS (niveau système de fichiers), et pourquoi le résultat effectif est l'intersection la plus restrictive des deux.

### 6.3 Quotas avec FSRM
```powershell
New-FsrmQuota -Path "D:\Partages\RH" -Size 5GB -SoftLimit
```

### 6.4 (Bonus) DFS Namespace pour un accès unifié
```powershell
Install-WindowsFeature -Name FS-DFS-Namespace -IncludeManagementTools
New-DfsnRoot -Path "\\corp.lab.local\DFS-Root" -TargetPath "\\srv-file\DFS-Root" -Type DomainV2
```

---

## Phase 7 — WSUS

### 7.1 Installer le rôle sur SRV-WSUS
```powershell
Install-WindowsFeature -Name UpdateServices, UpdateServices-DB, UpdateServices-UI -IncludeManagementTools
```
Lancer l'assistant post-installation :
```powershell
& "C:\Program Files\Update Services\Tools\wsusutil.exe" postinstall CONTENT_DIR=D:\WSUS-Content
```

### 7.2 Configurer via GPO le pointage des clients vers WSUS
- Computer Configuration → Administrative Templates → Windows Components → Windows Update
- **Specify intranet Microsoft update service location** → `http://srv-wsus.corp.lab.local:8530`

### 7.3 Créer des groupes de déploiement (anneaux de déploiement = bonne pratique pro)
```powershell
$wsus = Get-WsusServer
$wsus.CreateComputerTargetGroup("Pilote")
$wsus.CreateComputerTargetGroup("Production")
```

### 7.4 Approuver des mises à jour et générer un rapport de conformité
- Console WSUS → Updates → sélectionner → Approve for "Pilote" d'abord, puis "Production" après validation
➡️ Capture du tableau de conformité = preuve concrète pour ton portfolio.

---

## Phase 8 — Automatisation & audit PowerShell

### 8.1 Script d'audit AD (comptes inactifs, mots de passe expirés)
`ad-audit-report.ps1` :
```powershell
$InactiveDays = 90
$Threshold = (Get-Date).AddDays(-$InactiveDays)

$InactiveUsers = Get-ADUser -Filter {LastLogonTimestamp -lt $Threshold -and Enabled -eq $true} `
    -Properties LastLogonTimestamp | Select-Object Name, SamAccountName, @{N="DerniereConnexion";E={[DateTime]::FromFileTime($_.LastLogonTimestamp)}}

$InactiveUsers | Export-Csv -Path ".\rapport-comptes-inactifs.csv" -NoTypeInformation -Encoding UTF8
Write-Host "$($InactiveUsers.Count) comptes inactifs depuis plus de $InactiveDays jours détectés."
```
➡️ Ce script fait le lien naturel avec ton profil Blue Team (hygiène AD = surface d'attaque réduite) sans sortir du périmètre "administration".

### 8.2 Export GPO baseline (déjà vu en 5.6, à automatiser en tâche planifiée)

---

## Phase 9 (Bonus avancé) — AD CS : PKI interne

```powershell
Install-WindowsFeature -Name AD-Certificate -IncludeManagementTools
Install-AdcsCertificationAuthority -CAType EnterpriseRootCA -CryptoProviderName "RSA#Microsoft Software Key Storage Provider" -KeyLength 2048 -HashAlgorithmName SHA256 -ValidityPeriod Years -ValidityPeriodUnits 5
```
Usage concret à documenter : certificats pour LDAPS, RDP, ou signature de scripts internes.

---

## Phase 10 (Bonus, différenciant marché FR/hybride) — Azure AD Connect

- Créer un tenant Microsoft Entra ID gratuit (essai)
- Installer Azure AD Connect sur DC01 ou un serveur dédié
- Synchroniser l'OU `CORP-FR` vers Entra ID

---
