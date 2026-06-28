#!/bin/bash

LOG_FILE="raw_traffic.log"

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Petite pause entre les écritures pour simuler un vrai flux temps réel
# (0 = écriture instantanée comme avant, augmente si tu veux observer le dashboard évoluer)
DELAY="${1:-0.005}"

echo -e "${BLUE}[*] Initialisation du Générateur de Trafic de Masse V5${NC}"
echo -e "${BLUE}[*] Fichier cible : $LOG_FILE${NC}"
echo -e "${BLUE}[*] Délai entre paquets : ${DELAY}s${NC}\n"

# Vide le fichier de log au démarrage pour une simulation propre
> "$LOG_FILE"

# Fonction utilitaire pour générer une ligne de trafic au format standard
generate_log() {
    local src_ip="$1"
    local type="$2"
    local payload="$3"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ALERT: SRC=$src_ip TYPE=$type PAYLOAD='$payload'" >> "$LOG_FILE"
}

echo -e "${GREEN}[+] Étape 1 : Injection du trafic réseau légitime de fond (500 paquets)...${NC}"
for i in {1..500}; do
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] INFO: SRC=192.168.1.$((RANDOM%250+1)) DPT=443 PROTO=TCP TYPE=HTTPS_Traffic MESSAGE='Established connection'" >> "$LOG_FILE"
    sleep "$DELAY"
    done
    
    TARGET_IP="185.220.101.5"
    echo -e "${RED}[!] Étape 2 : Attaque volumétrique (Port Scan / SYN Flood - 1500 paquets) depuis $TARGET_IP...${NC}"
    for i in {1..1500}; do
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] ALERT: SRC=$TARGET_IP DPT=80 PROTO=TCP TYPE=PORT_SCAN PAYLOAD='SYN_FLOOD_STEALTH_ATTACK'" >> "$LOG_FILE"
        sleep "$DELAY"
        done
        
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] INFO: SRC=192.168.1.10 DPT=53 PROTO=UDP TYPE=DNS_Query MESSAGE='Resolved github.com'" >> "$LOG_FILE"
        
        ATTACKER_IP="45.122.33.10"
        echo -e "${RED}[!] Étape 3 : Force Brute SSH automatisée (800 tentatives) depuis $ATTACKER_IP...${NC}"
        for i in {1..800}; do
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] FATAL: SRC=$ATTACKER_IP DPT=22 PROTO=TCP TYPE=SSH_BRUTE MESSAGE='Failed password for root from $ATTACKER_IP port $((RANDOM%60000+1024)) ssh2'" >> "$LOG_FILE"
            sleep "$DELAY"
            done
            
            WEB_ATTACKER="198.51.100.77"
            echo -e "${RED}[!] Étape 4 : Scan de vulnérabilités Web (SQLi & XSS - 300 requêtes) depuis $WEB_ATTACKER...${NC}"
            
            for i in {1..150}; do
                echo "[$(date +'%Y-%m-%d %H:%M:%S')] ALERT: SRC=$WEB_ATTACKER DPT=443 PROTO=TCP TYPE=SQL_INJECTION PAYLOAD='SELECT * FROM users WHERE id=1 OR 1=1-- fuzz_id=$i'" >> "$LOG_FILE"
                sleep "$DELAY"
                done
                
                for i in {1..150}; do
                    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ALERT: SRC=$WEB_ATTACKER DPT=443 PROTO=TCP TYPE=XSS_ATTACK PAYLOAD='<script>alert(\"XSS_Test_Vector_$i\")</script>'" >> "$LOG_FILE"
                    sleep "$DELAY"
                    done
                    
                    # 5. FUZZING DE RÉPERTOIRES WEB (DirBuster / Gobuster)
                    echo -e "${RED}[!] Étape 5 : Web Directory Fuzzing (Recherche de fichiers sensibles)...${NC}"
                    WEB_SCANNER="104.28.10.50"
                    for i in {1..30}; do
                        generate_log "$WEB_SCANNER" "WEB_ENUMERATION" "GET /admin/config_$i.php HTTP/1.1 - 404 Not Found"
                        sleep 0.02
                        done
                        generate_log "$WEB_SCANNER" "SENSITIVE_FILE_ACCESS" "GET /backup.zip HTTP/1.1 - 200 OK"
                        
                        # 6. COMMAND & CONTROL (C2 BEACONING)
                        echo -e "${RED}[!] Étape 6 : Malware C2 Beaconing (Machine compromise)...${NC}"
                        INFECTED_HOST="192.168.1.105"
                        C2_SERVER="198.51.100.99"
                        for i in {1..15}; do
                            generate_log "$INFECTED_HOST" "C2_BEACON" "Outbound HTTP POST to $C2_SERVER/api/v1/update - Payload: encrypted_blob"
                            sleep 2 # Le beaconing est plus lent pour être furtif
                            done
                            
                            # 7. EXFILTRATION DE DONNÉES
                            echo -e "${RED}[!] Étape 7 : Exfiltration de données massive...${NC}"
                            generate_log "192.168.1.10" "DATA_EXFILTRATION" "Outbound SCP transfer started to 203.0.113.1 - Size: 5.4 GB"
                            sleep 0.1
                            
                            # 8. MOUVEMENT LATÉRAL (PASS-THE-HASH / SMB)
                            echo -e "${RED}[!] Étape 8 : Mouvement Latéral (SMB Bruteforce interne)...${NC}"
                            COMPROMISED_IP="192.168.1.42"
                            for target in {100..120}; do
                                generate_log "$COMPROMISED_IP" "LATERAL_MOVEMENT" "SMB Auth failure on target 192.168.1.$target port 445"
                                sleep 0.05
                                done
                                
                                echo -e "\n${YELLOW}[✓] Simulation de masse terminée avec succès.${NC}"
                                echo -e "${YELLOW}[✓] Total des événements générés : ~3170 lignes injectées (Kill Chain complète).${NC}"
