from __future__ import annotations

import pytest

from sentryx.validators import (
    InvalidTargetError,
    validate_port_spec,
    validate_target,
)


class TestValidateTarget:
    @pytest.mark.parametrize(
        "target",
        [
            "192.168.1.1",
            "10.0.0.0/24",
            "example.com",
            "sub.example.com",
            "scanme.nmap.org",
            "::1",
            "2001:db8::1",
            "a" * 63 + ".com",  # max label length
        ],
    )
    def test_valid_targets_pass(self, target: str) -> None:
        assert validate_target(target) == target

    @pytest.mark.parametrize(
        "target",
        [
            "",
            "   ",
            "-oG /etc/passwd",
            "--script=foo",
            "; rm -rf /",
            "target; whoami",
            "target && whoami",
            "target | cat /etc/passwd",
            "target`whoami`",
            "target$(whoami)",
            "target\nwhoami",
            "a" * 300,
            "-",
            "target with spaces",
            'target"quoted"',
        ],
    )
    def test_malicious_or_malformed_targets_rejected(self, target: str) -> None:
        with pytest.raises(InvalidTargetError):
            validate_target(target)

    def test_none_target_rejected(self) -> None:
        with pytest.raises(InvalidTargetError):
            validate_target(None)  # type: ignore[arg-type]

    def test_whitespace_is_stripped_from_valid_target(self) -> None:
        assert validate_target("  example.com  ") == "example.com"


class TestValidatePortSpec:
    @pytest.mark.parametrize("spec", ["80", "1-1024", "80,443,8080", "1-65535"])
    def test_valid_specs_pass(self, spec: str) -> None:
        assert validate_port_spec(spec) == spec

    @pytest.mark.parametrize(
        "spec",
        ["", "abc", "80;whoami", "-1", "70000", "100-50", "80,abc", "80 443"],
    )
    def test_invalid_specs_rejected(self, spec: str) -> None:
        with pytest.raises(InvalidTargetError):
            validate_port_spec(spec)
