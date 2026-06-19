#!/bin/bash
# Simulates SSH brute force logs to test the Mini-SIEM Engine

LOG_FILE="auth_simulated.log"
ATTACKER_IP="192.168.10.105"

# Create the file if it doesn't exist
touch $LOG_FILE

echo "Starting attack simulation..."
echo "Injecting logs into $LOG_FILE"

for i in {1..6}
do
    # Format of a standard Linux SSH failure log
    TIMESTAMP=$(date +"%b %d %H:%M:%S")
    LOG_ENTRY="$TIMESTAMP myserver sshd[12345]: Failed password for root from $ATTACKER_IP port 33452 ssh2"
    
    echo "$LOG_ENTRY" >> $LOG_FILE
    echo "Sent: Failed login attempt $i"
    
    # Wait half a second between attempts
    sleep 0.5
done

echo "Simulation complete."
