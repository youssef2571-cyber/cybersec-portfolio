import time
import os
import re
import json
import collections

LOG_FILE = "raw_traffic.log"
ALERT_FILE = "ids_alerts.log"
BAN_FILE = "banned_ips.json"

# --- CONFIGURATION ---
BAN_DURATION_SEC = 120          # Durée du bannissement avant déban automatique
WINDOW_SEC = 10                 # Fenêtre glissante pour les attaques basées sur la fréquence
SSH_BRUTE_THRESHOLD = 5         # Nb d'échecs SSH dans la fenêtre pour déclencher l'alerte
PORT_SCAN_THRESHOLD = 8         # Nb de paquets suspects dans la fenêtre

# Signatures "instantanées" (une seule ligne suffit)
INSTANT_SIGNATURES = {
    "SQL_INJECTION":         (r"(?i)(UNION SELECT|OR 1=1|--|SELECT \* FROM)", "HIGH"),
    "XSS_ATTACK":            (r"(?i)(<script>|javascript:|alert\()", "MEDIUM"),
    "SENSITIVE_FILE_ACCESS": (r"TYPE=SENSITIVE_FILE_ACCESS", "CRITICAL"),
    "DATA_EXFILTRATION":     (r"TYPE=DATA_EXFILTRATION", "CRITICAL"),
}

# Signatures "fréquentielles" : (pattern, threshold, severity, window_sec)
# Chaque signature a sa propre fenêtre car les attaques se déroulent à des vitesses différentes
# (ex : un scan de ports est rapide, le beaconing C2 est volontairement lent).
FREQUENCY_SIGNATURES = {
    "SSH_BRUTE":        (r"(?i)(Failed password)", SSH_BRUTE_THRESHOLD, "CRITICAL", WINDOW_SEC),
    "PORT_SCAN":        (r"(?i)(Nmap|masscan|stealth|SYN_FLOOD)", PORT_SCAN_THRESHOLD, "HIGH", WINDOW_SEC),
    "WEB_ENUMERATION":  (r"TYPE=WEB_ENUMERATION", 20, "MEDIUM", WINDOW_SEC),
    "C2_BEACON":        (r"TYPE=C2_BEACON", 5, "HIGH", 30),
}

# Le mouvement latéral se détecte différemment : ce n'est pas "N fois la même signature",
# mais "N cibles internes *distinctes* contactées par la même source" -> besoin d'un tracker dédié.
LATERAL_MOVEMENT_PATTERN = r"TYPE=LATERAL_MOVEMENT"
LATERAL_MOVEMENT_TARGET_REGEX = r"target ([0-9.]+)"
LATERAL_MOVEMENT_DISTINCT_TARGET_THRESHOLD = 5
LATERAL_MOVEMENT_WINDOW_SEC = 10

# Whitelist : IPs internes jamais bannies (évite les faux positifs)
WHITELIST = {"127.0.0.1"}

# Etat en mémoire
banned_ips = {}              # ip -> timestamp d'expiration du ban
freq_windows = collections.defaultdict(lambda: collections.defaultdict(collections.deque))
# freq_windows[attack_name][ip] = deque des timestamps récents

lateral_targets = collections.defaultdict(lambda: collections.deque())
# lateral_targets[src_ip] = deque de tuples (timestamp, target_ip)


def load_bans():
    if os.path.exists(BAN_FILE):
        try:
            with open(BAN_FILE, "r") as f:
                data = json.load(f)
                now = time.time()
                return {ip: exp for ip, exp in data.items() if exp > now}
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_bans():
    try:
        with open(BAN_FILE, "w") as f:
            json.dump(banned_ips, f)
    except IOError:
        pass


def is_banned(ip):
    """Vérifie le ban et le retire automatiquement s'il a expiré."""
    if ip in banned_ips:
        if time.time() < banned_ips[ip]:
            return True
        del banned_ips[ip]
        save_bans()
    return False


def ban_ip(ip):
    banned_ips[ip] = time.time() + BAN_DURATION_SEC
    save_bans()


def follow(thefile):
    """Lit le fichier en continu, comme 'tail -f'."""
    thefile.seek(0, 2)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line


def write_alert(alert_file, attack_type, severity, src_ip, raw):
    alert_file.write(f"[ALERT] TYPE:{attack_type} SEV:{severity} SRC:{src_ip} RAW:{raw.strip()}\n")
    alert_file.flush()


def check_frequency_signatures(line, src_ip, now):
    """Retourne (attack_name, severity) si un seuil fréquentiel est dépassé, sinon None."""
    for attack_name, (pattern, threshold, severity, window_sec) in FREQUENCY_SIGNATURES.items():
        if re.search(pattern, line):
            window = freq_windows[attack_name][src_ip]
            window.append(now)
            # Purge les évènements hors de la fenêtre propre à cette signature
            while window and now - window[0] > window_sec:
                window.popleft()
            if len(window) >= threshold:
                window.clear()  # évite de re-trigger immédiatement après le ban
                return attack_name, severity
    return None


def check_lateral_movement(line, src_ip, now):
    """
    Le mouvement latéral n'est pas 'N fois le même pattern' mais 'N cibles internes
    *distinctes* contactées par la même source dans une fenêtre courte' (style SMB/Pass-the-Hash).
    """
    if not re.search(LATERAL_MOVEMENT_PATTERN, line):
        return None

    target_match = re.search(LATERAL_MOVEMENT_TARGET_REGEX, line)
    target_ip = target_match.group(1) if target_match else None

    history = lateral_targets[src_ip]
    if target_ip:
        history.append((now, target_ip))

    # Purge les entrées hors de la fenêtre
    while history and now - history[0][0] > LATERAL_MOVEMENT_WINDOW_SEC:
        history.popleft()

    distinct_targets = {t for _, t in history}
    if len(distinct_targets) >= LATERAL_MOVEMENT_DISTINCT_TARGET_THRESHOLD:
        history.clear()
        return "LATERAL_MOVEMENT", "HIGH"
    return None


def main():
    global banned_ips
    banned_ips = load_bans()

    print("\033[1;96m" + "=" * 60 + "\033[0m")
    print("\033[1;96m[*] Démarrage du Moteur IDS/IPS V5 (Kill Chain + Bans persistants)\033[0m")
    print("\033[1;96m[*] Interface d'écoute : " + LOG_FILE + "\033[0m")
    print("\033[1;96m" + "=" * 60 + "\033[0m\n")

    # Création sûre des fichiers nécessaires
    open(LOG_FILE, "a").close()
    with open(ALERT_FILE, "w") as f:
        f.write("")

    with open(LOG_FILE, "r") as log_file, open(ALERT_FILE, "a") as alert_file:
        for line in follow(log_file):
            now = time.time()
            threat_detected = False

            ip_match = re.search(r"SRC=([0-9.]+)", line)
            src_ip = ip_match.group(1) if ip_match else "UNKNOWN"

            if src_ip in WHITELIST:
                continue

            # 1. IPS : IP déjà bannie -> drop direct
            if is_banned(src_ip):
                print(f"\033[90m[IPS] Firewall DROP : paquet rejeté depuis l'IP bannie {src_ip}\033[0m")
                write_alert(alert_file, "REPEATED_ATTACK", "LOW", src_ip, "Connection Dropped")
                continue

            # 2. Signatures instantanées
            for attack_name, (pattern, severity) in INSTANT_SIGNATURES.items():
                if re.search(pattern, line):
                    print(f"\n\033[1;91m[!] ALERTE IDS : {attack_name} ({severity}) détectée !\033[0m")
                    print(f"\033[1;93m[⚡] MITIGATION IPS : IP {src_ip} ajoutée à la Blacklist\033[0m\n")
                    ban_ip(src_ip)
                    write_alert(alert_file, attack_name, severity, src_ip, line)
                    threat_detected = True
                    break

            # 3. Signatures fréquentielles (seuils glissants)
            if not threat_detected:
                result = check_frequency_signatures(line, src_ip, now)
                if result:
                    attack_name, severity = result
                    print(f"\n\033[1;91m[!] ALERTE IDS : {attack_name} ({severity}) - seuil dépassé !\033[0m")
                    print(f"\033[1;93m[⚡] MITIGATION IPS : IP {src_ip} ajoutée à la Blacklist\033[0m\n")
                    ban_ip(src_ip)
                    write_alert(alert_file, attack_name, severity, src_ip, line)
                    threat_detected = True

            # 4. Mouvement latéral : cibles internes distinctes dans une fenêtre courte
            if not threat_detected:
                result = check_lateral_movement(line, src_ip, now)
                if result:
                    attack_name, severity = result
                    print(f"\n\033[1;91m[!] ALERTE IDS : {attack_name} ({severity}) - plusieurs cibles internes scannées !\033[0m")
                    print(f"\033[1;93m[⚡] MITIGATION IPS : Hôte interne {src_ip} ajouté à la Blacklist\033[0m\n")
                    ban_ip(src_ip)
                    write_alert(alert_file, attack_name, severity, src_ip, line)
                    threat_detected = True

            # 5. Trafic normal
            if not threat_detected:
                print(f"\033[37m[OK] Trafic autorisé : {line.strip()[:70]}...\033[0m")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\033[93m[*] Arrêt du moteur IDS/IPS.\033[0m")
