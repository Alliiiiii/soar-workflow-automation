# Playbook Catalogue

## PB-01 — SSH brute force
- **Trigger rules:** 5712, 5763 (level 10)
- **Action:** `firewall-drop` on source IP
- **Timeout:** 600 s
- **Guardrails:** whitelist, cooldown
- **Example Slack:**
  > SOAR alert
  > • Rule: 5763 (level 10) — SSH brute force
  > • Host: target-linux
  > • Source IP: 192.168.56.30
  > • Playbook: pb01_ssh_bruteforce
  > • Actions: firewall-drop

## PB-02 — Compromised account
- **Trigger rule:** 100100 (level 13)
- **Action:** `firewall-drop` (3600 s) + `disable-account` (1800 s)
- **Guardrails:** whitelist, protected users (`root`, `analyst`), cooldown
- **Note:** `passwd -l` doesn't block SSH-key logins. Runbook covers `usermod --expiredate 1` + `pkill`.

## PB-03 — Web attack burst
- **Trigger rules:** 31151, 31153, 31154 (level 10)
- **Action:** `firewall-drop` on source IP
- **Timeout:** 600 s
