"""
Guardrails applied before any response action is taken.

Rules:
  * Never act against whitelisted IPs (exact or CIDR).
  * Never disable a protected account.
  * Do not act twice on the same IP within a cooldown window.
"""

from __future__ import annotations

import ipaddress
import json
import os
import time
from pathlib import Path
from typing import Any

STATE_PATH = Path("/var/ossec/logs/soar-state.json")


class GuardrailViolation(Exception):
    """Raised when a guardrail would block an automated action."""


# ─────────────────────────────────────────────────────────────────────
# Whitelist
# ─────────────────────────────────────────────────────────────────────
def is_whitelisted(ip: str, config: dict[str, Any]) -> bool:
    """Return True if ``ip`` is in the configured whitelist.

    Accepts both exact IPs and CIDR entries (e.g. ``10.0.0.0/8``).
    """
    if not ip:
        return False
    try:
        target = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for entry in config.get("whitelist", []) or []:
        try:
            if "/" in str(entry):
                if target in ipaddress.ip_network(str(entry), strict=False):
                    return True
            elif target == ipaddress.ip_address(str(entry)):
                return True
        except ValueError:
            # Bad whitelist entry — for safety we skip it.
            continue
    return False


# ─────────────────────────────────────────────────────────────────────
# Protected users
# ─────────────────────────────────────────────────────────────────────
def is_protected_user(user: str | None, config: dict[str, Any]) -> bool:
    if not user:
        return False
    protected = {u.lower() for u in config.get("protected_users", []) or []}
    return user.lower() in protected


# ─────────────────────────────────────────────────────────────────────
# Cooldown state
# ─────────────────────────────────────────────────────────────────────
def _load_state(path: Path = STATE_PATH) -> dict[str, float]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {str(k): float(v) for k, v in data.items()}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return {}


def _save_state(state: dict[str, float], path: Path = STATE_PATH) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, path)


def in_cooldown(ip: str, config: dict[str, Any],
                state_path: Path = STATE_PATH) -> bool:
    """Return True if ``ip`` is still inside its cooldown window."""
    if not ip:
        return False
    window = float(config.get("cooldown_seconds", 0) or 0)
    if window <= 0:
        return False
    state = _load_state(state_path)
    last = state.get(ip)
    if last is None:
        return False
    return (time.time() - last) < window


def record_action(ip: str, state_path: Path = STATE_PATH) -> None:
    """Stamp ``ip`` as acted-on now, so cooldown applies to the next alert."""
    if not ip:
        return
    state = _load_state(state_path)
    state[ip] = time.time()
    _save_state(state, state_path)


# ─────────────────────────────────────────────────────────────────────
# Convenience — run all checks at once
# ─────────────────────────────────────────────────────────────────────
def check_all(ip: str | None, user: str | None, config: dict[str, Any],
              *, record: bool = True,
              state_path: Path = STATE_PATH) -> None:
    """Raise GuardrailViolation if any guardrail blocks the action.

    On success, records ``ip`` in the cooldown state (unless ``record=False``).
    """
    if ip and is_whitelisted(ip, config):
        raise GuardrailViolation(f"IP {ip} is whitelisted")
    if user and is_protected_user(user, config):
        raise GuardrailViolation(f"User {user} is a protected account")
    if ip and in_cooldown(ip, config, state_path=state_path):
        raise GuardrailViolation(f"IP {ip} is still in cooldown")
    if record and ip:
        record_action(ip, state_path=state_path)
