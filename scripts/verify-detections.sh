#!/usr/bin/env bash
# Feed sample log lines to wazuh-logtest and assert the expected rule fires.
# Run on wazuh-server.

set -uo pipefail
LOGTEST=/var/ossec/bin/wazuh-logtest
pass=0; fail=0

check() {
  local name="$1" expected_rule="$2" logline="$3"
  echo "──────────────────────────────────────────"
  echo "[*] $name — expect rule $expected_rule"
  out=$(printf '%s\n' "$logline" | "$LOGTEST" 2>&1)
  if echo "$out" | grep -qE "id: *['\"]?${expected_rule}['\"]?"; then
    echo "    PASS"
    ((pass++))
  else
    echo "    FAIL — output:"
    echo "$out" | sed 's/^/      /'
    ((fail++))
  fi
}

# 5712 — SSH brute force (non-existent user)
check "rule 5712" "5712" \
"Nov 25 10:15:00 target-linux sshd[1001]: Failed password for invalid user hacker from 192.168.56.30 port 50001 ssh2"

# 5763 — repeated failures for real user
check "rule 5763" "5763" \
"Nov 25 10:15:00 target-linux sshd[1001]: Failed password for labuser from 192.168.56.30 port 50001 ssh2"

# 31151 — multiple 400-class web errors from one IP
check "rule 31151" "31151" \
'192.168.56.30 - - [25/Nov/2026:10:15:00 +0000] "GET /../../etc/passwd HTTP/1.1" 400 226 "-" "nikto"'

# 100100 — success after failures (requires stateful burst; run twice)
echo "──────────────────────────────────────────"
echo "[*] rule 100100 — run 6 failed + 1 success (correlation)"
for i in 1 2 3 4 5 6; do
  printf '%s\n' \
  "Nov 25 10:16:0${i} target-linux sshd[1001]: Failed password for labuser from 192.168.56.30 port 5000${i} ssh2" \
  | "$LOGTEST" >/dev/null 2>&1
done
out=$(printf '%s\n' \
  "Nov 25 10:16:10 target-linux sshd[1001]: Accepted password for labuser from 192.168.56.30 port 50010 ssh2" \
  | "$LOGTEST" 2>&1)
if echo "$out" | grep -q "100100"; then
  echo "    PASS"; ((pass++))
else
  echo "    FAIL — output:"; echo "$out" | sed 's/^/      /'; ((fail++))
  echo "    NOTE: correlation freq/timeframe varies by Wazuh version."
  echo "    Adjust frequency/timeframe in local_rules.xml and retest."
fi

echo "──────────────────────────────────────────"
echo "PASS: $pass   FAIL: $fail"
[[ $fail -eq 0 ]] || exit 1
