#!/usr/bin/env bash
# Enable local (agent-side) Wazuh Active Response on target-linux.
# Adds firewall-drop for SSH brute force (5712,5763) and disable-account
# for compromised accounts (100100) directly in /var/ossec/etc/ossec.conf,
# so the endpoint protects itself even when the manager is unreachable.
#
# Idempotent: re-running is safe and makes no config change if the
# 5712,5763 active-response block is already present.

set -euo pipefail

CONF=/var/ossec/etc/ossec.conf
TS="$(date +%Y%m%d-%H%M%S)"
BACKUP="${CONF}.bak-${TS}"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

if [[ ! -f "$CONF" ]]; then
  echo "ERROR: $CONF not found. Is the wazuh-agent installed?" >&2
  exit 1
fi

echo "[*] Backing up $CONF -> $BACKUP"
cp -a "$CONF" "$BACKUP"

# Idempotency check: is there an <active-response> block covering 5712,5763?
if python3 - "$CONF" <<'PY'
import re
import sys

text = open(sys.argv[1], encoding="utf-8").read()
for block in re.findall(r"<active-response\b.*?</active-response>", text, re.S):
    match = re.search(r"<rules_id>\s*([^<]+?)\s*</rules_id>", block)
    if not match:
        continue
    ids = {part.strip() for part in match.group(1).split(",")}
    if {"5712", "5763"} <= ids:
        sys.exit(0)
sys.exit(1)
PY
then
  echo "endpoint protection already present"
  exit 0
fi

echo "[*] Injecting local Active Response blocks into $CONF"
python3 - "$CONF" <<'PY'
import os
import stat
import sys
import tempfile

path = sys.argv[1]
text = open(path, encoding="utf-8").read()

marker = "</ossec_config>"
idx = text.rfind(marker)
if idx == -1:
    sys.stderr.write("ERROR: closing </ossec_config> tag not found\n")
    sys.exit(2)

snippet = """
  <command>
    <name>firewall-drop</name>
    <executable>firewall-drop</executable>
    <timeout_allowed>yes</timeout_allowed>
  </command>

  <active-response>
    <command>firewall-drop</command>
    <location>local</location>
    <rules_id>5712,5763</rules_id>
    <timeout>600</timeout>
  </active-response>

  <command>
    <name>disable-account</name>
    <executable>disable-account</executable>
    <timeout_allowed>yes</timeout_allowed>
  </command>

  <active-response>
    <command>disable-account</command>
    <location>local</location>
    <rules_id>100100</rules_id>
    <timeout>1800</timeout>
  </active-response>

"""

head = text[:idx].rstrip() + "\n"
new = head + snippet + text[idx:]

st = os.stat(path)
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".ossec.conf.")
try:
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(new)
    os.chmod(tmp, stat.S_IMODE(st.st_mode))
    os.chown(tmp, st.st_uid, st.st_gid)
    os.replace(tmp, path)
except Exception:
    if os.path.exists(tmp):
        os.unlink(tmp)
    raise
PY

echo "[*] Validating XML"
if command -v xmllint >/dev/null 2>&1; then
  if ! xmllint --noout "$CONF"; then
    echo "ERROR: xmllint rejected $CONF; restoring backup." >&2
    cp -a "$BACKUP" "$CONF"
    exit 1
  fi
else
  if ! sudo /var/ossec/bin/wazuh-analysisd -t; then
    echo "ERROR: wazuh-analysisd rejected $CONF; restoring backup." >&2
    cp -a "$BACKUP" "$CONF"
    exit 1
  fi
fi

echo "[*] Restarting wazuh-agent"
sudo systemctl restart wazuh-agent

ACTIVE="$(sudo systemctl is-active wazuh-agent || true)"

cat <<EOF

[*] Local endpoint protection enabled on $(hostname)
    Added command:          firewall-drop
    Added active-response:  firewall-drop   (rules 5712,5763; timeout 600s)
    Added command:          disable-account
    Added active-response:  disable-account (rule 100100; timeout 1800s)
    Backup:                 $BACKUP
    wazuh-agent:            $ACTIVE
EOF
