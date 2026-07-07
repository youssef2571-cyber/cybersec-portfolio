"""
HTTP Honeypot
Simulates an Apache/PHP web server with a fake login page.

Improvements over v1:
  - Realistic HTTP routing (404 on unknown paths, 200 only on known endpoints)
  - Extracts and logs the full User-Agent (reveals the scanner tool used)
  - Detects SQLi / XSS payloads directly in the URL before forwarding to IDS
  - POST body parsing to capture login credentials submitted to the fake form
  - Always responds with convincing headers to avoid honeypot fingerprinting
"""

import os
import re
import socket
import threading
from datetime import datetime
from urllib.parse import unquote

LOG_FILE   = "raw_traffic.log"
LISTEN_PORT = 8080

# Paths that return 200 — everything else gets a realistic 404
_KNOWN_PATHS = {"/", "/index.php", "/login", "/login.php", "/admin", "/admin/login.php"}

# Inline quick-detection patterns (supplements the IDS engine)
_SQLI_RE = re.compile(r"(?i)(union\s+select|or\s+1=1|--|select\s+\*\s+from|drop\s+table)")
_XSS_RE  = re.compile(r"(?i)(<script|javascript:|alert\(|onerror=)")
_LFI_RE  = re.compile(r"(\.\./|/etc/passwd|\.env|backup\.zip|\.git/|web\.config)")

# Fake HTML pages
_LOGIN_PAGE = """\
HTTP/1.1 200 OK\r
Server: Apache/2.4.54 (Ubuntu)\r
X-Powered-By: PHP/8.1.2\r
Content-Type: text/html; charset=UTF-8\r
Connection: close\r
\r
<!DOCTYPE html>
<html>
<head><title>System Login</title></head>
<body>
  <h2>Internal Portal — Authentication Required</h2>
  <form method="POST" action="/login.php">
    <input name="username" placeholder="Username"><br>
    <input name="password" type="password" placeholder="Password"><br>
    <input type="submit" value="Login">
  </form>
</body>
</html>"""

_404_PAGE = """\
HTTP/1.1 404 Not Found\r
Server: Apache/2.4.54 (Ubuntu)\r
X-Powered-By: PHP/8.1.2\r
Content-Type: text/html; charset=UTF-8\r
Connection: close\r
\r
<!DOCTYPE html>
<html><body><h1>404 Not Found</h1><p>The requested URL was not found.</p></body></html>"""

_AUTH_FAILED = """\
HTTP/1.1 401 Unauthorized\r
Server: Apache/2.4.54 (Ubuntu)\r
X-Powered-By: PHP/8.1.2\r
Content-Type: text/html; charset=UTF-8\r
Connection: close\r
\r
<!DOCTYPE html>
<html><body><h2>Login failed. Please try again.</h2></body></html>"""


def _classify_request(path: str, raw: str) -> tuple[str, str]:
    """
    Returns (attack_type, severity) based on what the request looks like.
    If nothing suspicious is found, defaults to WEB_ENUMERATION / LOW.
    """
    decoded = unquote(path + raw)

    if _LFI_RE.search(decoded):
        return "SENSITIVE_FILE_ACCESS", "CRITICAL"
    if _SQLI_RE.search(decoded):
        return "SQL_INJECTION", "HIGH"
    if _XSS_RE.search(decoded):
        return "XSS_ATTACK", "MEDIUM"
    return "WEB_ENUMERATION", "LOW"


def _write_log(ip: str, method: str, path: str, user_agent: str,
               attack_type: str, severity: str, extra: str = "") -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"[{ts}] ALERT: SRC={ip} DPT=80 PROTO=TCP "
        f"TYPE={attack_type} SEV={severity} "
        f"PAYLOAD='{method} {path} UA={user_agent!r}{extra}'\n"
    )
    try:
        with open(LOG_FILE, "a") as f:
            f.write(entry)
        tag = f"[{attack_type}]" if attack_type != "WEB_ENUMERATION" else "[SCAN]"
        print(f"  [HTTP] {ip}  {tag}  {method} {path}")
    except OSError as exc:
        print(f"  [HTTP] Log write error: {exc}")


def _parse_request(raw: str) -> tuple[str, str, str, str, str]:
    """Extract method, path, User-Agent, and POST body from raw HTTP text."""
    lines  = raw.split("\r\n")
    first  = lines[0] if lines else ""
    parts  = first.split(" ")
    method = parts[0] if len(parts) > 0 else "GET"
    path   = parts[1] if len(parts) > 1 else "/"

    user_agent = "unknown"
    for line in lines[1:]:
        if line.lower().startswith("user-agent:"):
            user_agent = line.split(":", 1)[1].strip()
            break

    # POST body is after the blank line separator
    body = raw.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in raw else ""

    # Extract base path (without query string) for routing
    base_path = path.split("?")[0]
    return method, path, base_path, user_agent, body


def _handle_connection(client_sock: socket.socket, address: tuple) -> None:
    ip, port = address
    try:
        raw = client_sock.recv(8192).decode("utf-8", errors="ignore")
        if not raw:
            return

        method, full_path, base_path, user_agent, body = _parse_request(raw)
        attack_type, severity = _classify_request(full_path, body)

        # Log credential attempts from POST to the login page
        creds_note = ""
        if method == "POST" and "login" in base_path and body:
            creds_note = f" POSTED_BODY='{body[:200]}'"

        _write_log(ip, method, full_path, user_agent, attack_type, severity, creds_note)

        # Route response: 200 only on known paths, realistic 404 elsewhere
        if base_path in _KNOWN_PATHS:
            if method == "POST" and "login" in base_path:
                client_sock.sendall(_AUTH_FAILED.encode())
            else:
                client_sock.sendall(_LOGIN_PAGE.encode())
        else:
            client_sock.sendall(_404_PAGE.encode())

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
        print(f"\033[1;95m[*] HTTP Honeypot listening on port {listen_port}\033[0m")
        print(f"\033[1;95m[*] Alerts → {LOG_FILE}\033[0m\n")

        while True:
            client_sock, addr = server_sock.accept()
            threading.Thread(
                target=_handle_connection, args=(client_sock, addr), daemon=True
            ).start()

    except KeyboardInterrupt:
        print("\n\033[93m[*] HTTP Honeypot stopped.\033[0m")
    finally:
        server_sock.close()


if __name__ == "__main__":
    start_honeypot()
