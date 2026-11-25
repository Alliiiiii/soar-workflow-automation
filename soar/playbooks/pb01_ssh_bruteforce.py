"""PB-01: SSH brute force — block source IP for 10 minutes."""

from __future__ import annotations

from typing import Any


def run(alert: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    data = alert.get("data") or {}
    srcip = data.get("srcip")
    return {
        "playbook": "pb01_ssh_bruteforce",
        "srcip": srcip,
        "user": None,
        "actions": ["firewall-drop"],
        "timeout": 600,
        "reason": f"SSH brute force from {srcip} (rule {alert.get('rule', {}).get('id')})",
    }
