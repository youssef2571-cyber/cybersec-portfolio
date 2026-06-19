# Custom Security Information and Event Management (SIEM)

This project features a fully functional, lightweight SIEM correlation engine written in Python. It demonstrates the core mechanics of how enterprise SOCs ingest logs, parse unstructured data, and trigger real-time security alerts based on temporal correlation rules.

##  Core Engine Mechanics

1. **Log Ingestion (`tail -f` emulation):** The engine continuously monitors a target log file in real-time, utilizing memory-efficient generator functions to process new entries immediately as they are written.
2. **Data Parsing (Regex):** Utilizing Python's `re` module, the engine extracts critical telemetry (e.g., Attacker IP addresses) from unstructured Syslog text.
3. **Temporal Correlation:** The engine maintains a stateful memory of events using `defaultdict`. It tracks the frequency of specific actions (like SSH failures) against a sliding time window (e.g., 60 seconds).
4. **Alert Generation:** If the event threshold is breached within the time window, a high-fidelity alert is generated, demonstrating the foundational logic behind tools like Splunk or IBM QRadar.

## How to Run the Demonstration

You will need two terminal windows to see the SIEM in action.

**Terminal 1: Start the SIEM Engine**
```bash
# Create the empty log file first
touch auth_simulated.log
# Start the SIEM monitor
python3 mini_siem.py
```
**Terminal 2: Launch the Attack Simulation**
```bash
# Run the bash script to inject malicious logs
bash simulate_attack.sh
```
