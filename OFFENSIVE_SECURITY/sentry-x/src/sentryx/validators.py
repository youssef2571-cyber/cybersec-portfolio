#!/usr/bin/env python3
"""
sentryx.validators
-------------------
Strict validation of user-supplied targets (IP/hostname) before they are
ever interpolated into a subprocess argument list.

SECURITY NOTE: Every recon function in tools.py MUST validate its target
through validate_target() before building a subprocess command. We never
use shell=True and we never build commands via string concatenation -
arguments are always passed as a list - but validation is still required
because a malformed "hostname" like "-oG /etc/passwd" could be interpreted
by the target tool itself as a flag.
"""

from __future__ import annotations

import ipaddress
import re

# RFC 1123 hostname pattern (labels of 1-63 chars, alnum + hyphen, no
# leading/trailing hyphen, dots between labels, max 253 chars total).
_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)" r"(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
)

# Any argument that starts with a hyphen could be interpreted as a flag by
# the downstream tool (nmap, whois, etc.) - reject outright regardless of
# whether it otherwise looks like a valid hostname.
_LEADING_DASH_RE = re.compile(r"^\s*-")


class InvalidTargetError(ValueError):
    """Raised when a target fails validation. Carries a user-safe message."""


def validate_target(raw: str) -> str:
    """
    Validate a scan target (IP address or hostname).

    Returns the normalized target string on success.
    Raises InvalidTargetError on any validation failure.
    """
    if raw is None:
        raise InvalidTargetError("Target is empty.")

    target = raw.strip()

    if not target:
        raise InvalidTargetError("Target is empty.")

    if len(target) > 253:
        raise InvalidTargetError("Target exceeds maximum length (253 chars).")

    if _LEADING_DASH_RE.match(target):
        raise InvalidTargetError("Target cannot start with '-' (would be interpreted as a flag).")

    # Reject anything with whitespace, shell metacharacters, or control
    # chars - defense in depth even though we never use shell=True.
    forbidden = set(" \t\n\r;|&$`<>(){}[]\\\"'")
    if any(ch in forbidden for ch in target):
        raise InvalidTargetError("Target contains forbidden characters.")

    # Try IP address first (v4 or v6).
    try:
        ipaddress.ip_address(target)
        return target
    except ValueError:
        pass

    # Try CIDR range (nmap supports scanning ranges).
    try:
        ipaddress.ip_network(target, strict=False)
        return target
    except ValueError:
        pass

    # Fall back to hostname validation.
    if _HOSTNAME_RE.match(target):
        return target

    raise InvalidTargetError(f"'{raw}' is not a valid IP address, CIDR range, or hostname.")


def validate_port_spec(raw: str) -> str:
    """
    Validate an nmap-style port specification, e.g. '80', '1-1024',
    '80,443,8080'. Returns the normalized spec on success.
    """
    if not raw:
        raise InvalidTargetError("Port specification is empty.")
    spec = raw.strip()
    if not re.fullmatch(r"[0-9,\-]+", spec):
        raise InvalidTargetError(f"'{raw}' is not a valid port specification.")
    for part in spec.split(","):
        if "-" in part:
            lo, _, hi = part.partition("-")
            if not (lo.isdigit() and hi.isdigit()):
                raise InvalidTargetError(f"Invalid port range '{part}'.")
            if not (0 <= int(lo) <= 65535 and 0 <= int(hi) <= 65535):
                raise InvalidTargetError(f"Port out of range in '{part}'.")
            if int(lo) > int(hi):
                raise InvalidTargetError(f"Invalid port range '{part}'.")
        else:
            if not part.isdigit() or not (0 <= int(part) <= 65535):
                raise InvalidTargetError(f"Invalid port '{part}'.")
    return spec
