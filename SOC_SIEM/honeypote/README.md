#  Honeynet Infrastructure (V2)

Une infrastructure de leurre (Honeynet) à haute interaction, développée en Python. Conçue pour capturer, analyser et exporter de la Cyber Threat Intelligence (CTI) en temps réel vers un moteur IDS/IPS et un SIEM personnalisés.

## 📐 Architecture du Projet

Ce projet déploie simultanément plusieurs capteurs réseau gérés par un orchestrateur central. L'objectif n'est pas seulement de détecter les intrusions, mais de forcer l'attaquant à interagir pour capturer ses outils, ses identifiants et ses méthodes d'attaque (TTPs).

### Les Composants (Capteurs)

* **Manager (`manager.py`) :** L'orchestrateur. Il lance, surveille et gère le cycle de vie de tous les capteurs via du threading, partageant un espace mémoire commun et unifiant la journalisation.
* **Capteur SSH (`ssh.py`) :** Honeypot à haute interaction basé sur `paramiko`. Complète le *handshake* cryptographique RSA pour tromper les scanners avancés (Hydra, Ncrack) et capture les combinaisons d'identifiants (brute-force).
* **Capteur HTTP (`http.py`) :** Émulateur de serveur Web Apache/PHP. Gère le routage dynamique (200 OK / 404 Not Found), extrait les User-Agents et capture les payloads d'attaques Web (SQLi, XSS, Path Traversal).
* **Capteur FTP (`ftp.py`) :** Émulateur vsFTPd interactif. Implémente des techniques de *Tarpitting* (ralentissement volontaire des réponses) pour épuiser les ressources des attaquants automatisés.

## ⚙️ Prérequis

L'infrastructure nécessite Python 3 et le module cryptographique `paramiko` pour la simulation du protocole SSH.

```bash
# Installation des dépendances
pip install paramiko
```
🚀 Utilisation
Pour lancer l'ensemble de l'infrastructure de leurre, il suffit d'exécuter l'orchestrateur avec les privilèges appropriés (nécessaire si vous modifiez les ports pour utiliser les ports standards 22, 80, 21).

```Bash
# Lancement des capteurs (ports de test : 2222, 8080, 2121)
python3 manager.py
```
Le manager affichera un tableau de bord en temps réel dans la console indiquant l'état de chaque capteur et le nombre de requêtes interceptées. Pour arrêter proprement l'infrastructure et libérer les ports, utilisez Ctrl+C.

🔗 Intégration avec l'écosystème de sécurité
Ce Honeynet est conçu pour s'intégrer de manière transparente avec un pipeline de sécurité externe :

Génération de Logs : Toutes les interactions sont formatées et écrites en temps réel dans raw_traffic.log.

Prévention (IPS) : Le fichier de log est surveillé par un moteur IDS/IPS(ids_ips_engine.py) externe qui bannit dynamiquement les IP offensives.

Observabilité (SIEM) : Les alertes de sécurité sont cartographiées sur la Cyber Kill Chain via un tableau de bord SIEM(mini_siem.py).


***
