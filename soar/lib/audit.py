"""Append-only JSON audit log."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

DEFAULT_LOG = Path("/var/ossec/logs/integrations/soar.log")


def log_decision(decision: dict[str, Any], alert: dict[str, Any],
                 path: Path = DEFAULT_LOG) -> None:
    """Append one JSON line describing the decision + alert."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rule": (alert.get("rule") or {}).get("id"),
        "level": (alert.get("rule") or {}).get("level"),
        "agent": (alert.get("agent") or {}).get("name"),
        "srcip": (alert.get("data") or {}).get("srcip"),
        "dstuser": (alert.get("data") or {}).get("dstuser"),
        "decision": decision,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as exc:
        log.error("Failed to write audit log %s: %s", path, exc)
