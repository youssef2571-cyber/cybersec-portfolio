# Rapport de projet — SOC Wazuh : Détection d'intrusion et Detection Engineering

## 1. Contexte et objectifs

Ce projet fait suite à un Honeynet et un Mini-SIEM développés en Python, avec pour objectif d'acquérir une expérience pratique sur un **SIEM professionnel** utilisé en entreprise (Wazuh), et de dépasser une simple installation par défaut en adoptant une démarche de **Detection Engineering** : écriture de règles de détection personnalisées, vérification systématique de leur comportement réel, et validation par simulation d'attaques.

Objectifs concrets :
- Déployer une infrastructure SOC complète via Docker
- Collecter et centraliser les journaux de sécurité d'un endpoint Linux
- Écrire des règles de détection capables de générer des alertes critiques (niveau 12+)
- Valider chaque règle par une attaque réelle, pas simulée artificiellement
- Documenter la démarche pour qu'elle soit reproductible et vérifiable

---

## 2. Architecture

Le lab est structuré en trois couches (voir `docs/architecture.png`) :

- **Hôte physique** : Parrot OS, 32 Go de RAM, 8 cœurs — largement suffisant pour faire tourner la stack Wazuh en parallèle des VMs de test.
- **Couche de virtualisation (QEMU/KVM)** : une VM Kali Linux (attaquant, IP `192.168.122.235`) et une VM Ubuntu Server 24.04 (victime, IP `192.168.122.46`), reliées à un réseau bridge virtuel (`virbr0`, `192.168.122.0/24`).
- **Infrastructure conteneurisée (Docker Compose)** : Wazuh Manager, Wazuh Indexer (OpenSearch) et Wazuh Dashboard, déployés sur l'hôte.

La victime communique avec le Manager via l'agent Wazuh (FIM, syslog, logs applicatifs), qui applique les règles de détection avant indexation dans OpenSearch et visualisation dans le Dashboard.

---

## 3. Déploiement — difficultés rencontrées et résolutions

Cette section documente volontairement les problèmes réels rencontrés pendant le déploiement, car leur résolution fait partie intégrante de la compétence démontrée.

### 3.1 Conflit Docker / Podman

Sur Parrot OS, la commande `docker` pointait en réalité vers **Podman** (émulation via le paquet `podman-docker`), avec une variable d'environnement `DOCKER_HOST` forcée par les scripts `/etc/profile.d/podman-docker.sh` et `.csh`. Cela provoquait des échecs silencieux lors du `docker compose run` pour la génération des certificats (`Cannot connect to the Docker daemon`).

**Résolution** :
- Désinstallation de `podman-docker`
- Suppression des scripts résiduels dans `/etc/profile.d/`
- Installation du véritable Docker Engine via le script officiel (`get.docker.com`)
- Nouvelle session shell pour garantir la propagation propre des variables d'environnement

### 3.2 Vérification des IDs de règles natives avant utilisation

Plusieurs IDs de règles supposés (`5720` pour un pattern brute-force réussi, `533` pour une suppression de fichier) se sont révélés incorrects après vérification directe dans le ruleset Wazuh (`/var/ossec/ruleset/rules/`) :

| ID supposé | Rôle supposé | Rôle réel vérifié |
|---|---|---|
| `5720` | Brute force réussi | "Multiple authentication failures" (niveau 10, échecs uniquement) |
| `533` | Suppression de fichier | "Listened ports status (netstat) changed" — sans rapport |
| `553` | — | **Confirmé** : "File deleted" (`decoded_as: syscheck_deleted`) |
| `554` | — | **Confirmé** : "File added to the system" |
| `521` | Rootkit générique | **Confirmé** : "Possible kernel level rootkit" (niveau 11) |

**Méthodologie adoptée** : chaque `if_sid`/`if_matched_sid` utilisé dans `local_rules.xml` a été vérifié par extraction directe du ruleset (`grep`/`sed` sur les fichiers `.xml` dans le conteneur) avant intégration, plutôt que déduit par supposition. Cette vérification a notamment permis de construire la règle de "compromission confirmée" (`100013`) comme une *compound rule* dépendant de la règle custom `100010` plutôt que d'un ID natif au comportement incertain selon les versions de Wazuh.

### 3.3 Contrainte de syntaxe XML sur l'attribut `frequency`

Une première version de la règle `100013` utilisait `frequency="1"`, provoquant une erreur bloquante au chargement (`Invalid frequency: 1. Must be higher than 1 and lower than 10000`) et empêchant `wazuh-analysisd` de démarrer. Correction : suppression de l'attribut `frequency`, `if_matched_sid` seul étant suffisant pour la logique de corrélation recherchée.

### 3.4 Signatures rootcheck : noms de fichiers arbitraires vs. signatures réelles

Une tentative initiale de simuler un rootkit via un fichier au nom arbitraire (`/dev/.botnet.lock`) n'aurait déclenché aucune alerte : le module rootcheck de Wazuh compare le système à une liste de signatures connues (`/var/ossec/etc/shared/default/rootkit_files.txt`), pas à une heuristique de nommage. La simulation a été corrigée pour utiliser une signature réellement présente dans cette liste (`usr/bin/adore`, associée à l'Adore Worm).

---

## 4. Règles de détection personnalisées

Voir `rules/local_rules.xml`. Résumé :

| Rule ID | Niveau | Déclencheur | MITRE ATT&CK |
|---|:---:|---|---|
| `100010` | 10 | 6 échecs SSH / 60s, même IP | T1110 |
| `100011` | 8 | Scan de ports (pattern Nmap) | T1046 |
| `100012` | 7 | Utilisation de `sudo` | T1548 |
| `100013` | 12 | Authentification SSH réussie après `100010` | T1110, T1078 |
| `100014` | 12 | Suppression de `auth.log`/`syslog` (via règle native `553` + filtre sur `field name="file"`) | T1070, T1070.002 |
| `100016` | 12 | Rootkit connu détecté par rootcheck (escalade de la règle native `521`) | T1014 |
| `100025` | 15 | Fichier `.php/.sh/.py` déposé dans `/var/www/html` (via règle native `554` + regex sur extension) | T1505.003 |

Prérequis de configuration sur l'agent (`ossec.conf`) pour que ces règles soient opérationnelles :
- `<syscheck>` avec surveillance temps réel (`realtime="yes"`) de `/var/log/auth.log`, `/var/log/syslog` et `/var/www/html`
- `<rootcheck>` avec fréquence de scan réduite (300s en lab, contre ~12h par défaut) pour un retour rapide en environnement de test

---

## 5. Simulation d'attaques

Le script `scripts/wazuh_attack_lab.sh` automatise une kill chain complète depuis Kali contre la victime. Principe directeur : générer de **vrais événements système** (vraies tentatives SSH, vrais scans Nmap, vraies commandes shell) plutôt que d'injecter des lignes de log simulées dans un fichier — cette dernière approche, testée initialement avec un script hérité du Mini-SIEM Python, s'est révélée incompatible avec Wazuh, dont les règles de détection décodent des formats de logs système réels (syslog RFC3164/5424, sshd, PAM) et non un format texte arbitraire.

### Modules du script

1. Reconnaissance (Nmap : version, agressif, UDP)
2. Brute force SSH (rotation utilisateur/mot de passe, Hydra ou fallback en boucle)
3. Post-exploitation (création/suppression d'utilisateur, lecture de fichiers sensibles) via un compte leurre dédié (`labtest`)
4. Attaques web (SQLi basique, path traversal, LFI)
5. Rafale de connexions (test de seuils)
6. Trafic légitime (contrôle des faux positifs)
7. Attaques critiques : compromission confirmée → suppression de logs → dépôt de webshell
8. Dépôt de signature rootkit connue

Chaque exécution produit un log de corrélation horodaté (`wazuh_lab_correlation_*.log`), permettant de faire correspondre précisément une action locale à l'alerte générée côté Wazuh. Une fonction de nettoyage (`cleanup_all`) supprime les artefacts de test (webshell, fichier rootkit, utilisateur backdoor) en fin d'exécution.

---

## 6. Résultats

Après exécution de la kill chain complète :

- Alertes totales : de 37 (baseline) à plus de 600 sur la fenêtre de test
- Alertes niveau 12+ : de 0 à plusieurs dizaines, correspondant aux règles `100013`, `100014`, `100016`, `100025`
- Tactiques MITRE ATT&CK couvertes automatiquement : Credential Access, Lateral Movement, Defense Evasion, Privilege Escalation, Persistence, Initial Access
- Conformité PCI DSS mappée automatiquement par Wazuh sur plusieurs exigences (10.2.x, 10.6.1, 11.4)

Voir `docs/screenshots/` pour le détail visuel (dashboard, mapping MITRE, log d'exécution du script).

---

## 7. Module bonus — Détection de vulnérabilités

Le module natif **Vulnerability Detection** de Wazuh a été activé sans configuration additionnelle. Il scanne les paquets installés sur l'agent et les confronte à des bases de CVE publiques. Résultat sur la VM victime : 515 paquets analysés, avec des CVE réparties par sévérité (dont plusieurs en sévérité *High*), démontrant que Wazuh couvre à la fois la détection d'intrusion et la gestion de vulnérabilités.

---

## 8. Compétences développées

- Déploiement et administration d'un SIEM professionnel via Docker Compose
- Résolution de conflits d'environnement (Docker vs Podman)
- Écriture de règles de détection XML avec logique de corrélation (`if_matched_sid`, `same_source_ip`, `field name`)
- Méthodologie de vérification systématique des règles natives avant intégration (lecture directe du ruleset plutôt que supposition)
- Configuration de File Integrity Monitoring et de Rootcheck sur un agent Linux
- Mapping de détections au framework MITRE ATT&CK
- Scripting Bash pour l'automatisation de scénarios de test reproductibles et traçables
- Compréhension et simulation d'une kill chain complète (reconnaissance → accès initial → post-exploitation → defense evasion → persistence)

---

## 9. Pistes d'évolution

- Intégration de Suricata pour la détection réseau (IDS) en complément de la détection basée logs
- Comparaison avec Elastic Stack ou Microsoft Sentinel sur un scénario équivalent
- Ajout d'un agent Windows pour exploiter les règles Sysmon natives de Wazuh
- Détection de commandes shell via `auditd` (ex. téléchargement de payload dans `/tmp`), non implémentée dans cette itération faute de configuration `auditd` validée
- Automatisation du déploiement complet via Ansible
