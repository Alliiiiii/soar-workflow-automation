"""Slack + email notifications."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Any

import requests

log = logging.getLogger(__name__)


def _build_text(alert: dict[str, Any], decision: dict[str, Any]) -> str:
    rule = alert.get("rule") or {}
    agent = alert.get("agent") or {}
    data = alert.get("data") or {}
    mitre = (rule.get("mitre") or {})
    mitre_ids = ", ".join(mitre.get("id") or []) or "-"
    return (
        f"*SOAR alert*\n"
        f"• Rule: {rule.get('id', '?')} (level {rule.get('level', '?')}) — {rule.get('description', '')}\n"
        f"• Host: {agent.get('name', '?')}\n"
        f"• Source IP: {data.get('srcip', '-')}\n"
        f"• Target user: {data.get('dstuser', '-')}\n"
        f"• Playbook: {decision.get('playbook', '-')}\n"
        f"• Actions: {', '.join(decision.get('actions', []) or []) or 'none'}\n"
        f"• Reason: {decision.get('reason', '-')}\n"
        f"• MITRE: {mitre_ids}\n"
        f"• Time: {alert.get('timestamp', '-')}\n"
    )


def send_slack(webhook_url: str, text: str, timeout: float = 5.0) -> bool:
    if not webhook_url:
        return False
    try:
        resp = requests.post(webhook_url, json={"text": text}, timeout=timeout)
        if resp.status_code >= 300:
            log.warning("Slack HTTP %s: %s", resp.status_code, resp.text[:200])
            return False
        return True
    except requests.RequestException as exc:
        log.warning("Slack post failed: %s", exc)
        return False


def send_email(config: dict[str, Any], subject: str, body: str,
               timeout: float = 10.0) -> bool:
    smtp = config.get("smtp") or {}
    host = smtp.get("host")
    port = int(smtp.get("port", 587))
    user = smtp.get("user")
    password = smtp.get("password")
    from_addr = smtp.get("from_addr") or user
    to_addrs = smtp.get("to_addrs") or []
    if not (host and user and password and from_addr and to_addrs):
        return False

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=timeout) as s:
            s.ehlo()
            s.starttls()
            s.login(user, password)
            s.send_message(msg)
        return True
    except (smtplib.SMTPException, OSError) as exc:
        log.warning("SMTP send failed: %s", exc)
        return False


def notify_all(config: dict[str, Any], alert: dict[str, Any],
               decision: dict[str, Any]) -> dict[str, bool]:
    """Fire both channels; return per-channel success flags."""
    text = _build_text(alert, decision)
    slack_ok = send_slack((config.get("slack") or {}).get("webhook_url", ""), text)
    subject = f"[SOAR] {decision.get('playbook', '?')} — {alert.get('rule', {}).get('id', '?')}"
    email_ok = send_email(config, subject, text.replace("*", ""))
    return {"slack": slack_ok, "email": email_ok}
