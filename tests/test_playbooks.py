"""Unit tests for playbook selection and guardrail integration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from soar.playbooks import select
from soar.playbooks import pb01_ssh_bruteforce, pb02_compromised_account, pb03_web_attack_burst
from soar.lib import guardrails

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_select_pb01():
    assert select("5712") is pb01_ssh_bruteforce
    assert select("5763") is pb01_ssh_bruteforce


def test_select_pb02():
    assert select("100100") is pb02_compromised_account


def test_select_pb03():
    for rid in ("31151", "31153", "31154"):
        assert select(rid) is pb03_web_attack_burst


def test_select_unknown():
    assert select("999999") is None


def test_pb01_returns_firewall_drop():
    decision = pb01_ssh_bruteforce.run(_load("alert_5712.json"), {})
    assert decision["playbook"] == "pb01_ssh_bruteforce"
    assert decision["actions"] == ["firewall-drop"]
    assert decision["srcip"] == "192.168.56.30"


def test_pb02_returns_lock_and_block():
    decision = pb02_compromised_account.run(_load("alert_100100.json"), {})
    assert "disable-account" in decision["actions"]
    assert "firewall-drop" in decision["actions"]
    assert decision["user"] == "labuser"


def test_pb02_protected_user_guardrail():
    alert = _load("alert_100100.json")
    alert["data"]["dstuser"] = "root"
    cfg = {"whitelist": [], "protected_users": ["root"], "cooldown_seconds": 0}
    decision = pb02_compromised_account.run(alert, {})
    with pytest.raises(guardrails.GuardrailViolation):
        guardrails.check_all(decision["srcip"], decision["user"], cfg,
                             state_path=Path("/tmp/test-state-guard.json"))


def test_pb03_returns_firewall_drop():
    decision = pb03_web_attack_burst.run(_load("alert_31151.json"), {})
    assert decision["playbook"] == "pb03_web_attack_burst"
    assert decision["actions"] == ["firewall-drop"]
