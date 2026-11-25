#!/usr/bin/env bash
# Install Wazuh server (manager + indexer + dashboard) all-in-one.
# Run on wazuh-server (Ubuntu 22.04).

set -euo pipefail

WAZUH_VERSION="${WAZUH_VERSION:-4.9}"   # bump to the latest 4.x per docs

if [[ $EUID -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

echo "[*] Downloading Wazuh $WAZUH_VERSION installer"
curl -s0 -o /tmp/wazuh-install.sh \
  "https://packages.wazuh.com/${WAZUH_VERSION}/wazuh-install.sh"

echo "[*] Running all-in-one install (-a)"
bash /tmp/wazuh-install.sh -a

echo "[*] Service status:"
systemctl --no-pager status wazuh-manager wazuh-indexer wazuh-dashboard || true

echo
echo "[*] Dashboard: https://192.168.56.10"
echo "    The installer printed the admin password above — save it."
