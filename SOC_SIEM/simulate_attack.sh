#!/bin/bash
# Simulates a complex attack chain for the Advanced SIEM

LOG_FILE="central_syslog.log"
ATTACKER_IP="10.0.0.99"

touch $LOG_FILE
echo "Starting Advanced Attack Simulation (APT Scenario)..."

# Step 1: The attacker scans the network (Triggering the Python IDS)
echo "--> Injecting IDS Port Scan Alert"
echo "$(date +"%b %d %H:%M:%S") ids-sensor [IDS ALERT] Port Scan detected from $ATTACKER_IP" >> $LOG_FILE
sleep 2

# Step 2: The attacker tries to brute force SSH (Fails 3 times)
echo "--> Injecting SSH Failures"
for i in {1..3}; do
    echo "$(date +"%b %d %H:%M:%S") server sshd: Failed password for admin from $ATTACKER_IP port 22" >> $LOG_FILE
    sleep 1
done

# Step 3: The attacker finds the password and logs in successfully
echo "--> Injecting SSH Success (Compromise)"
echo "$(date +"%b %d %H:%M:%S") server sshd: Accepted password for admin from $ATTACKER_IP port 22" >> $LOG_FILE

echo "Simulation complete. Check your SIEM dashboard!"
