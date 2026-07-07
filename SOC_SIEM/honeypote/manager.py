"""
Honeypot Manager
Launches all honeypot sensors as threads (not subprocesses) in the same
process, which gives us:
  - Shared memory (no IPC needed between sensors)
  - A single Ctrl+C to stop everything cleanly
  - A live status line showing how many connections each sensor has handled
"""

import os
import sys
import time
import threading
import importlib.util
from datetime import datetime

# ── Resolve absolute paths so the manager can be run from any directory ──────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SENSORS = [
    {"name": "SSH",  "file": "ssh.py",  "port": 2222, "color": "\033[1;96m"},
    {"name": "HTTP", "file": "http.py", "port": 8080, "color": "\033[1;95m"},
    {"name": "FTP",  "file": "ftp.py",  "port": 2121, "color": "\033[1;94m"},
]

LOG_FILE = os.path.join(BASE_DIR, "raw_traffic.log")

# Runtime state per sensor
_sensor_status: dict[str, dict] = {}


# ── Dynamic module loader ─────────────────────────────────────────────────────
def _load_module(name: str, filepath: str):
    """Import a honeypot module by absolute file path at runtime."""
    spec   = importlib.util.spec_from_file_location(name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── Log file watcher (counts total alerts written) ───────────────────────────
def _count_alerts() -> int:
    try:
        with open(LOG_FILE, "r") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


# ── Status dashboard (printed every second in the main thread) ───────────────
def _print_status() -> None:
    reset = "\033[0m"
    now   = datetime.now().strftime("%H:%M:%S")
    total = _count_alerts()

    print(f"\r\033[K", end="")   # clear current line
    parts = [f"\033[90m[{now}]\033[0m"]
    for s in SENSORS:
        n     = s["name"]
        state = _sensor_status.get(n, {})
        alive = state.get("alive", False)
        icon  = "●" if alive else "✖"
        col   = s["color"] if alive else "\033[91m"
        parts.append(f"{col}{icon} {n}:{s['port']}{reset}")
    parts.append(f"\033[93m📡 {total} alerts logged\033[0m")
    print("   ".join(parts), end="", flush=True)


# ── Sensor thread wrapper ─────────────────────────────────────────────────────
def _run_sensor(sensor: dict) -> None:
    name     = sensor["name"]
    filepath = os.path.join(BASE_DIR, sensor["file"])
    port     = sensor["port"]

    _sensor_status[name] = {"alive": False}

    if not os.path.exists(filepath):
        print(f"\n\033[1;91m[-] {sensor['file']} not found at {filepath}\033[0m")
        return

    try:
        module = _load_module(name, filepath)
        _sensor_status[name]["alive"] = True
        module.start_honeypot(listen_port=port)
    except OSError as exc:
        # Most common cause: port already in use
        print(f"\n\033[1;91m[-] {name} failed to bind port {port}: {exc}\033[0m")
        print(f"\033[93m    Try: sudo lsof -i :{port}  to find what's using it.\033[0m")
    except Exception as exc:
        print(f"\n\033[1;91m[-] {name} crashed: {exc}\033[0m")
    finally:
        _sensor_status[name]["alive"] = False


# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    # Create the shared log file if it doesn't exist yet
    open(LOG_FILE, "a").close()

    print("\033[1;92m" + "=" * 55 + "\033[0m")
    print("\033[1;92m[*]  Honeynet Infrastructure Manager v2\033[0m")
    print("\033[1;92m" + "=" * 55 + "\033[0m\n")

    threads = []
    for sensor in SENSORS:
        t = threading.Thread(target=_run_sensor, args=(sensor,), daemon=True, name=sensor["name"])
        t.start()
        threads.append(t)
        time.sleep(0.4)   # stagger startup so banners don't interleave

    print(f"\n\033[1;96m[*] All sensors launched.\033[0m")
    print(f"\033[1;96m[*] Log file : {LOG_FILE}\033[0m")
    print(f"\033[1;96m[*] Feed this file into ids_ips_engine.py and mini_siem_advanced.py\033[0m")
    print(f"\033[90m[*] Press Ctrl+C to stop all sensors.\033[0m\n")

    try:
        while True:
            _print_status()
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n\033[1;93m[*] Shutdown signal received. Stopping all sensors...\033[0m")
        # Daemon threads die automatically when the main thread exits
        print("\033[1;92m[+] Honeynet offline. All ports released.\033[0m")
        sys.exit(0)


if __name__ == "__main__":
    main()
