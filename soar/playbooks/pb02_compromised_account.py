"""PB-02: Compromised account — block IP 1 h + disable account 30 min.

Guardrails ensure ``root`` / ``analyst`` are never disabled. For SSH-key
accounts the runbook note applies (passwd -l doesn't block keys).
"""

from __future__ import annotations

from typing import Any


def run(alert: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    data = alert.get("data") or {}
    srcip = data.get("srcip")
    user = data.get("dstuser")
    actions = ["firewall-drop"]
    if user:
        actions.append("disable-account")
    return {
        "playbook": "pb02_compromised_account",
        "srcip": srcip,
        "user": user,
        "actions": actions,
        "timeout": {"firewall-drop": 3600, "disable-account": 1800},
        "reason": f"Compromised account: success after failures (rule {alert.get('rule', {}).get('id')})",
    }
