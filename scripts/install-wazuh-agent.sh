#!/usr/bin/env bash
# Install + enrol the Wazuh agent on target-linux (Ubuntu 22.04).

set -euo pipefail

WAZUH_MANAGER="${WAZUH_MANAGER:-192.168.56.10}"
WAZUH_VERSION="${WAZUH_VERSION:-4.x}"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

echo "[*] Importing GPG key"
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH \
  | gpg --no-default-keyring \
        --keyring gnupg-ring:/usr/share/keyrings/wazuh.gpg \
        --import
chmod 644 /usr/share/keyrings/wazuh.gpg

echo "[*] Adding apt repo"
echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/${WAZUH_VERSION}/apt/ stable main" \
  | tee /etc/apt/sources.list.d/wazuh.list

echo "[*] Installing agent (manager=$WAZUH_MANAGER)"
apt-get update
WAZUH_MANAGER="$WAZUH_MANAGER" apt-get install -y wazuh-agent

systemctl daemon-reload
systemctl enable --now wazuh-agent

echo "[*] Agent status:"
systemctl --no-pager status wazuh-agent || true

echo
echo "[*] Now install services and test user:"
echo "    sudo apt install -y openssh-server apache2"
echo "    sudo adduser labuser"
echo "    sudo cp wazuh/agent/ossec.conf.snippet.xml /tmp/ && \\"
echo "      sudo sed -i '/<\\/ossec_config>/e cat /tmp/ossec.conf.snippet.xml' /var/ossec/etc/ossec.conf"
echo "    sudo systemctl restart wazuh-agent"
