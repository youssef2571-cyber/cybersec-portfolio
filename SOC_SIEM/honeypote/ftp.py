"""
FTP Honeypot
Simulates a vsFTPd server that fully interacts with brute-force clients.

Improvements over v1:
  - Per-IP attempt counter with instant tagging when threshold is crossed
  - Handles QUIT, SYST, FEAT commands so real FTP clients don't abort early
  - Logs both username and password on every attempt
  - Slight random delay before rejecting auth (slows down automated tools)
"""

import os
import random
import socket
import threading
import time
from datetime import datetime

LOG_FILE    = "raw_traffic.log"
LISTEN_PORT = 2121

# Per-IP attempt tracking (same logic as SSH honeypot)
_ip_hit_count: dict[str, int] = {}
FTP_BRUTE_THRESHOLD = 5


def _write_log(ip: str, port: int, username: str, password: str) -> None:
    hits = _ip_hit_count.get(ip, 0) + 1
    _ip_hit_count[ip] = hits

    ts         = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    extra_type = " TYPE=FTP_BRUTE" if hits >= FTP_BRUTE_THRESHOLD else ""

    entry = (
        f"[{ts}] FATAL: SRC={ip} DPT=21 PROTO=TCP{extra_type} "
        f"MESSAGE='Failed password for {username} from {ip} port {port} ftp' "
        f"CREDENTIALS='{username}:{password}'\n"
    )
    try:
        with open(LOG_FILE, "a") as f:
            f.write(entry)
        print(f"  [FTP] {ip}:{port}  user={username!r}  pass={password!r}  (attempt #{hits})")
    except OSError as exc:
        print(f"  [FTP] Log write error: {exc}")


def _handle_connection(client_sock: socket.socket, address: tuple) -> None:
    ip, port = address
    try:
        # Realistic vsFTPd banner — version matches a common real-world deployment
        client_sock.sendall(b"220 (vsFTPd 3.0.5)\r\n")

        current_user = "anonymous"

        while True:
            try:
                raw = client_sock.recv(1024).decode("utf-8", errors="ignore").strip()
            except OSError:
                break

            if not raw:
                break

            cmd = raw.upper()

            if cmd.startswith("USER "):
                current_user = raw[5:].strip()
                client_sock.sendall(b"331 Please specify the password.\r\n")

            elif cmd.startswith("PASS "):
                password = raw[5:].strip()

                # Small random delay: slows Hydra/Medusa, gives IDS time to react
                time.sleep(random.uniform(0.3, 0.8))

                _write_log(ip, port, current_user, password)
                client_sock.sendall(b"530 Login incorrect.\r\n")

                # Reset so the client can try another username without reconnecting
                current_user = "anonymous"

            elif cmd == "QUIT":
                client_sock.sendall(b"221 Goodbye.\r\n")
                break

            elif cmd == "SYST":
                # Advertise Linux — makes us look more realistic
                client_sock.sendall(b"215 UNIX Type: L8\r\n")

            elif cmd == "FEAT":
                # Advertise a minimal feature set matching vsFTPd
                client_sock.sendall(
                    b"211-Features:\r\n PASV\r\n UTF8\r\n211 End\r\n"
                )

            else:
                client_sock.sendall(b"500 Unknown command.\r\n")

    except Exception:
        pass
    finally:
        client_sock.close()


def start_honeypot(listen_port: int = LISTEN_PORT) -> None:
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_sock.bind(("0.0.0.0", listen_port))
        server_sock.listen(50)
        print(f"\033[1;94m[*] FTP Honeypot listening on port {listen_port}\033[0m")
        print(f"\033[1;94m[*] Alerts → {LOG_FILE}\033[0m\n")

        while True:
            client_sock, addr = server_sock.accept()
            threading.Thread(
                target=_handle_connection, args=(client_sock, addr), daemon=True
            ).start()

    except KeyboardInterrupt:
        print("\n\033[93m[*] FTP Honeypot stopped.\033[0m")
    finally:
        server_sock.close()


if __name__ == "__main__":
    start_honeypot()
