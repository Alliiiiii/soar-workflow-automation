"""Optional IP reputation enrichment via AbuseIPDB."""

from __future__ import annotations

import logging
from typing import Any

import requests

log = logging.getLogger(__name__)

ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"


def lookup_abuseipdb(ip: str, api_key: str, timeout: float = 5.0) -> dict[str, Any] | None:
    """Return ``{"score": int, "country": str, "total_reports": int}`` or None.

    Never raises — returns None on any failure (network, auth, parse).
    """
    if not ip or not api_key:
        return None
    headers = {"Accept": "application/json", "Key": api_key}
    params = {"ipAddress": ip, "maxAgeInDays": "90"}
    try:
        resp = requests.get(ABUSEIPDB_URL, headers=headers, params=params, timeout=timeout)
        if resp.status_code != 200:
            log.warning("AbuseIPDB HTTP %s for %s", resp.status_code, ip)
            return None
        data = resp.json().get("data", {})
        return {
            "score": int(data.get("abuseConfidenceScore", 0)),
            "country": data.get("countryCode") or "??",
            "total_reports": int(data.get("totalReports", 0)),
        }
    except (requests.RequestException, ValueError) as exc:
        log.warning("AbuseIPDB lookup failed for %s: %s", ip, exc)
        return None


def enrich(ip: str, config: dict[str, Any]) -> dict[str, Any] | None:
    """Wrapper respecting the ``abuseipdb.enabled`` flag in config."""
    block = (config or {}).get("abuseipdb") or {}
    if not block.get("enabled"):
        return None
    return lookup_abuseipdb(ip, block.get("api_key", ""))
