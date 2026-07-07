"""
SSH Honeypot — powered by paramiko
Simulates a real OpenSSH server well enough to capture actual credentials
from brute-force tools (Hydra, Medusa, Ncrack, automated bots).

How it works:
  1. Completes a real SSH handshake (key exchange + algorithm negotiation)
  2. Reaches the authentication stage and asks for credentials
  3. Always rejects the login — but logs every username/password attempt
  4. Writes to raw_traffic.log in the exact format expected by ids_ips_engine.py
"""

import os
import socket
import threading
import logging
from datetime import datetime

import paramiko

# ── Config ──────────────────────────────────────────────────────────────────
LOG_FILE        = "raw_traffic.log"
LISTEN_PORT     = 2222
HOST_KEY_PATH   = os.path.join(os.path.dirname(__file__), "honeypot_rsa.key")

# Local per-IP counter for fast rate detection at the honeypot level
# (supplements the IDS sliding-window detection with an instant first-pass)
_ip_hit_count: dict[str, int] = {}
INSTANT_BAN_THRESHOLD = 10   # flag as SSH_BRUTE after N attempts from same IP

# Silence paramiko's own transport logs — we handle our own structured logging
logging.getLogger("paramiko").setLevel(logging.CRITICAL)


# ── RSA Host Key ─────────────────────────────────────────────────────────────
def _load_or_generate_host_key() -> paramiko.RSAKey:
    """Load an existing host key or generate a fresh one on first run."""
    if os.path.exists(HOST_KEY_PATH):
        return paramiko.RSAKey(filename=HOST_KEY_PATH)
    print("[SSH] No host key found — generating a new RSA 2048-bit key...")
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(HOST_KEY_PATH)
    print(f"[SSH] Host key saved to {HOST_KEY_PATH}")
    return key

HOST_KEY = _load_or_generate_host_key()


# ── Log writer ───────────────────────────────────────────────────────────────
def _write_log(ip: str, port: int, username: str, password: str) -> None:
    """
    Write one credential attempt to raw_traffic.log.

    Format mirrors the IDS signatures:
      - 'Failed password' triggers SSH_BRUTE frequency rule
      - 'SRC=IP' is parsed by the engine for banning
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hits = _ip_hit_count.get(ip, 0) + 1
    _ip_hit_count[ip] = hits

    # After the threshold, tag the line directly so the IDS picks it up instantly
    extra_tag = " TYPE=SSH_BRUTE" if hits >= INSTANT_BAN_THRESHOLD else ""

    entry = (
        f"[{ts}] FATAL: SRC={ip} DPT=22 PROTO=TCP{extra_tag} "
        f"MESSAGE='Failed password for {username} from {ip} port {port} ssh2' "
        f"CREDENTIALS='{username}:{password}'\n"
    )
    try:
        with open(LOG_FILE, "a") as f:
            f.write(entry)
        print(f"  [SSH] {ip}:{port}  user={username!r}  pass={password!r}  (attempt #{hits})")
    except OSError as exc:
        print(f"  [SSH] Log write error: {exc}")


# ── Paramiko server interface ─────────────────────────────────────────────────
class _HoneypotServer(paramiko.ServerInterface):
    """
    Paramiko requires a ServerInterface subclass to handle authentication.
    We accept the channel request but always reject credentials so we can
    capture everything the attacker tries.
    """

    def __init__(self, ip: str, port: int) -> None:
        self.ip   = ip
        self.port = port

    # Allow the client to open a session channel (required by most SSH clients)
    def check_channel_request(self, kind: str, chanid: int) -> int:
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    # This is called for every password attempt — the honeypot's core capture point
    def check_auth_password(self, username: str, password: str) -> int:
        _write_log(self.ip, self.port, username, password)
        return paramiko.AUTH_FAILED          # always reject

    # Also capture public-key attempts (reveals the key type the attacker uses)
    def check_auth_publickey(self, username: str, key: paramiko.PKey) -> int:
        ts  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (
            f"[{ts}] INFO: SRC={self.ip} DPT=22 PROTO=TCP "
            f"MESSAGE='Publickey attempt for {username} from {self.ip} "
            f"key_type={key.get_name()}'\n"
        )
        try:
            with open(LOG_FILE, "a") as f:
                f.write(entry)
        except OSError:
            pass
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username: str) -> str:
        return "password,publickey"          # advertise both, accept neither


# ── Per-connection handler ────────────────────────────────────────────────────
def _handle_connection(client_sock: socket.socket, address: tuple) -> None:
    ip, port = address
    transport = None
    try:
        # Build a paramiko Transport — this manages the full SSH protocol layer
        transport = paramiko.Transport(client_sock)
        transport.local_version = "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6"
        transport.add_server_key(HOST_KEY)

        server = _HoneypotServer(ip, port)
        transport.start_server(server=server)

        # Hold the channel open briefly — gives slow/retrying clients time to
        # send multiple credential attempts before we close the connection
        channel = transport.accept(timeout=20)
        if channel:
            channel.close()

    except (paramiko.SSHException, EOFError, ConnectionResetError):
        pass   # normal for scanners that abort after the first auth failure
    except Exception as exc:
        print(f"  [SSH] Unexpected error from {ip}: {exc}")
    finally:
        if transport:
            transport.close()
        client_sock.close()


# ── Entry point ───────────────────────────────────────────────────────────────
def start_honeypot(listen_port: int = LISTEN_PORT) -> None:
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_sock.bind(("0.0.0.0", listen_port))
        server_sock.listen(100)
        print(f"\033[1;96m[*] SSH Honeypot listening on port {listen_port}\033[0m")
        print(f"\033[1;96m[*] Host key fingerprint : {HOST_KEY.get_fingerprint().hex()}\033[0m")
        print(f"\033[1;96m[*] Alerts → {LOG_FILE}\033[0m\n")

        while True:
            client_sock, addr = server_sock.accept()
            t = threading.Thread(
                target=_handle_connection,
                args=(client_sock, addr),
                daemon=True,
            )
            t.start()

    except KeyboardInterrupt:
        print("\n\033[93m[*] SSH Honeypot stopped.\033[0m")
    finally:
        server_sock.close()


if __name__ == "__main__":
    start_honeypot()
