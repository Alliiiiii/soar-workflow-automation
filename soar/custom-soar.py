#!/usr/bin/env python3
"""
custom-soar — Wazuh integration that drives the SOAR playbook engine.

Invocation (from Wazuh integratord):
    /var/ossec/integrations/custom-soar <path-to-alert-json>

Also supports CLI/testing:
    ./custom-soar.py --test-fixture tests/fixtures/alert_5712.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import yaml

# Allow running from anywhere: add script's dir to sys.path
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from lib import audit, enrich, guardrails, notify  # noqa: E402
from playbooks import select as select_playbook  # noqa: E402

CONFIG_PATH = _HERE / "config.yaml"
LOG = logging.getLogger("custom-soar")


# ─────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────
def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        LOG.error("Config not found: %s", path)
        return {}


# ─────────────────────────────────────────────────────────────────────
# Enforcement (API mode)
# ─────────────────────────────────────────────────────────────────────
def _api_enforce(alert: dict[str, Any], decision: dict[str, Any],
                 config: dict[str, Any]) -> dict[str, Any]:
    """Call Wazuh REST API PUT /active-response for each action."""
    import requests  # local import keeps native mode dependency-free

    api_cfg = config.get("wazuh_api") or {}
    url = (api_cfg.get("url") or "").rstrip("/") + "/active-response"
    auth = (api_cfg.get("user"), api_cfg.get("password"))
    verify = bool(api_cfg.get("verify_ssl", False))

    results = {}
    for action in decision.get("actions", []):
        payload = {
            "command": action,
            "arguments": [decision.get("srcip") or decision.get("user") or ""],
            "alert": {
                "data": alert.get("data") or {},
                "rule": alert.get("rule") or {},
            },
        }
        try:
            r = requests.put(url, json=payload, auth=auth,
                             verify=verify, timeout=10)
            results[action] = r.status_code
        except requests.RequestException as exc:
            results[action] = f"error: {exc}"
    return results


# ─────────────────────────────────────────────────────────────────────
# Main logic
# ─────────────────────────────────────────────────────────────────────
def handle(alert: dict[str, Any], config: dict[str, Any],
           *, dry_run: bool = False) -> dict[str, Any]:
    rule = alert.get("rule") or {}
    rule_id = str(rule.get("id") or "")
    level = int(rule.get("level") or 0)

    # 1. Skip low-severity alerts
    if level < int(config.get("min_level", 10)):
        return {"skipped": True, "reason": f"level {level} < min_level"}

    # 2. Select playbook
    pb = select_playbook(rule_id)
    if pb is None:
        return {"skipped": True, "reason": f"no playbook for rule {rule_id}"}

    # 3. Build candidate decision (playbook may look at ctx later)
    decision = pb.run(alert, {"config": config})

    # 4. Guardrails
    try:
        guardrails.check_all(decision.get("srcip"), decision.get("user"),
                             config, record=not dry_run)
    except guardrails.GuardrailViolation as exc:
        decision = {**decision, "actions": [], "reason": f"guardrail: {exc}"}
        audit.log_decision(decision, alert)
        notify.notify_all(config, alert, decision)
        return decision

    # 5. Optional enrichment (never raises)
    rep = enrich.enrich(decision.get("srcip") or "", config)
    if rep:
        decision["reputation"] = rep
        threshold = int((config.get("abuseipdb") or {}).get("block_threshold", 0))
        if threshold and rep["score"] < threshold:
            decision["actions"] = []
            decision["reason"] += f" (reputation {rep['score']} < {threshold})"

    # 6. Enforcement
    if not dry_run and decision.get("actions"):
        if config.get("mode") == "api":
            decision["enforcement"] = _api_enforce(alert, decision, config)
        else:
            decision["enforcement"] = {"mode": "native",
                                       "note": "Wazuh Active Response handles it"}

    # 7. Audit + notify
    audit.log_decision(decision, alert)
    decision["notify"] = notify.notify_all(config, alert, decision)
    return decision


# ─────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────
def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )


def main(argv: list[str]) -> int:
    _setup_logging()

    parser = argparse.ArgumentParser(description="custom-soar playbook engine")
    parser.add_argument("alert_file", nargs="?", help="Alert JSON file (Wazuh passes this)")
    parser.add_argument("--test-fixture", help="Alias for alert_file (for testing)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Do not enforce or record cooldown")
    parser.add_argument("--config", default=str(CONFIG_PATH))
    args = parser.parse_args(argv)

    alert_path = args.test_fixture or args.alert_file
    if not alert_path:
        parser.error("alert file required (positional or --test-fixture)")
    if not os.path.isfile(alert_path):
        LOG.error("Alert file not found: %s", alert_path)
        return 2

    try:
        with open(alert_path, "r", encoding="utf-8") as f:
            alert = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        LOG.error("Cannot read alert: %s", exc)
        return 2

    config = load_config(Path(args.config))
    if not config:
        LOG.warning("Empty config — running with defaults")
        config = {"mode": "native", "min_level": 10}

    decision = handle(alert, config, dry_run=args.dry_run)
    print(json.dumps(decision, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
