"""Unit tests for guardrails."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from soar.lib import guardrails


@pytest.fixture
def cfg():
    return {
        "whitelist": ["192.168.56.1", "192.168.56.10", "10.0.0.0/8"],
        "protected_users": ["root", "analyst"],
        "cooldown_seconds": 60,
    }


def test_whitelist_exact(cfg):
    assert guardrails.is_whitelisted("192.168.56.1", cfg) is True
    assert guardrails.is_whitelisted("192.168.56.30", cfg) is False


def test_whitelist_cidr(cfg):
    assert guardrails.is_whitelisted("10.5.5.5", cfg) is True
    assert guardrails.is_whitelisted("11.0.0.1", cfg) is False


def test_whitelist_invalid_ip(cfg):
    assert guardrails.is_whitelisted("not-an-ip", cfg) is False


def test_protected_user(cfg):
    assert guardrails.is_protected_user("root", cfg) is True
    assert guardrails.is_protected_user("ROOT", cfg) is True
    assert guardrails.is_protected_user("labuser", cfg) is False
    assert guardrails.is_protected_user(None, cfg) is False


def test_cooldown_roundtrip(cfg, tmp_path: Path):
    state = tmp_path / "state.json"
    assert guardrails.in_cooldown("1.2.3.4", cfg, state_path=state) is False
    guardrails.record_action("1.2.3.4", state_path=state)
    assert guardrails.in_cooldown("1.2.3.4", cfg, state_path=state) is True
    # State file must contain the IP
    data = json.loads(state.read_text())
    assert "1.2.3.4" in data


def test_check_all_raises_on_whitelist(cfg, tmp_path: Path):
    with pytest.raises(guardrails.GuardrailViolation, match="whitelisted"):
        guardrails.check_all("192.168.56.1", None, cfg,
                             state_path=tmp_path / "s.json")


def test_check_all_raises_on_protected_user(cfg, tmp_path: Path):
    with pytest.raises(guardrails.GuardrailViolation, match="protected"):
        guardrails.check_all("1.2.3.4", "root", cfg,
                             state_path=tmp_path / "s.json")


def test_check_all_passes_and_records(cfg, tmp_path: Path):
    state = tmp_path / "s.json"
    guardrails.check_all("1.2.3.4", "labuser", cfg, state_path=state)
    assert state.exists()
