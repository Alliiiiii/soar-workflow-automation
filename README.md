# SOAR Workflow Automation for Incident Response

Automated IP blocking and account disabling driven by Wazuh SIEM, with Slack and email notifications.

**Course:** Information Security — BSIT Part III, University of Sindh, Jamshoro
**Author:** Ali
**Date:** 25 November 2026

---

## 1. Abstract

Security teams receive far more alerts than analysts can triage by hand. A brute-force
attack against SSH can generate hundreds of failed logins per minute. This project
designs, implements and tests a **SOAR (Security Orchestration, Automation and Response)**
workflow that closes the gap between detection and containment.

Wazuh is used as the SIEM/XDR platform. When a detection rule of sufficient severity
fires, a custom Python integration (`custom-soar.py`) selects a playbook, applies
guardrails (whitelist, protected accounts, cooldown, optional IP reputation), and either
blocks the offending IP address or disables the compromised account through Wazuh
Active Response. Every action is reported to analysts via **Slack** and **email**, and
written to an audit log. An equivalent **Shuffle SOAR** design and an alternative
**Splunk** integration are also documented.

---

## 2. Architecture

```
+----------------+    SSH/HTTP     +---------------------+
| Attacker       | --------------> | Monitored Endpoints |
| (Kali Linux)   |                 | Ubuntu, SSH, Apache |
+----------------+                 +----------+----------+
                                             | logs (1514/tcp)
                                             v
                            +----------------------------------+
                            | SIEM: Wazuh Manager + Indexer   |
                            | decode -> rule match -> alert    |
                            | level >= 10 triggers integration |
                            +----------------+-----------------+
                                             | alert JSON
                                             v
                            +----------------------------------+
                            | SOAR Orchestration Layer         |
                            | playbook | whitelist | cooldown |
                            | reputation | audit log         |
                            +----+-------------+-------------+
                                 |             |
                                 v             v
                        +----------------+  +-------------------+
                        | Block IP       |  | Disable Account   |
                        | firewall-drop  |  | disable-account   |
                        +----------------+  +-------------------+
                                 |
                                 v
                        +-------------------+
                        | Notify            |
                        | Slack + SMTP mail |
                        +-------------------+
```

Enforcement runs on the agent through Wazuh **Active Response**.

**Data flow:**
1. Attacker generates repeated failed logins / malicious HTTP requests.
2. Target logs to `/var/log/auth.log` and Apache logs.
3. Wazuh agent forwards events over 1514/tcp.
4. Manager decodes and evaluates rules. Correlated alert fires (rule 5712/5763/31151/100100, level >= 10).
5. `integratord` invokes `custom-soar.py` with the alert JSON.
6. Playbook selected; guardrails applied; optional reputation lookup.
7. Native mode: Active Response enforces. API mode: SOAR calls Wazuh REST API.
8. Slack + email notification sent; decision appended to `soar.log`.
9. After timeout, block/lock automatically reversed.

---

## 3. Environment

| Host | Role | IP |
|------|------|-----|
| wazuh-server | Ubuntu 22.04 — manager, indexer, dashboard, custom-soar | 192.168.56.10 |
| target-linux | Ubuntu 22.04 — agent, OpenSSH, Apache2 | 192.168.56.20 |
| attacker | Kali Linux — hydra, nikto, nmap | 192.168.56.30 |
| host/admin | Browser | 192.168.56.1 |
| shuffle-server (optional) | Ubuntu + Docker — Shuffle SOAR | 192.168.56.40 |

---

> **Deployment note:** The lab was executed on **Ubuntu 26.04 LTS**
> (the version installed during development) rather than 22.04 LTS
> as originally planned. All playbooks, rules, and integrations were
> verified working on this version. The only compatibility adjustment
> was setting `vm.max_map_count=262144` before installing the Wazuh
> Indexer (a hard requirement of the OpenSearch-based indexer).

---

**Ports:** 1514/tcp (agent events), 1515/tcp (enrolment), 55000/tcp (REST API), 443/tcp (dashboard), 9200/tcp (indexer), 3001/3443/tcp (Shuffle), 587/tcp (SMTP), 443/tcp (Slack / AbuseIPDB outbound).

**Test accounts on target:** `labuser` (victim), `analyst` (protected, key-based), `root` (protected, remote login disabled).

---

## 4. Quick Start

### 4.1 Install the Wazuh server (all-in-one)
```bash
# On wazuh-server (192.168.56.10)
sudo bash scripts/install-wazuh-server.sh
```
Visit https://192.168.56.10 — sign in as `admin`.

### 4.2 Install and enrol the Wazuh agent
```bash
# On target-linux (192.168.56.20)
sudo bash scripts/install-wazuh-agent.sh
```
Confirm in Dashboard -> Agents that `target-linux` is **Active**.

### 4.3 Deploy detection rules and Active Response
```bash
# On wazuh-server
sudo cp wazuh/manager/local_rules.xml /var/ossec/etc/rules/local_rules.xml
# Merge wazuh/manager/ossec.conf.snippet.xml into /var/ossec/etc/ossec.conf
sudo /var/ossec/bin/wazuh-logtest          # validate rule 100100
sudo systemctl restart wazuh-manager
```

### 4.4 Deploy custom-soar
```bash
# On wazuh-server
sudo cp -r soar /opt/custom-soar
sudo cp /opt/custom-soar/config.yaml.example /opt/custom-soar/config.yaml
sudo nano /opt/custom-soar/config.yaml     # fill in Slack + SMTP + API creds
sudo pip3 install -r /opt/custom-soar/requirements.txt
chmod +x /opt/custom-soar/custom-soar.py
# Bind the integration (see wazuh/manager/ossec.conf.snippet.xml)
```

Wazuh's `integratord` invokes `/var/ossec/integrations/custom-soar` (or
`custom-soar.py`) directly, so create a tiny wrapper that points at the deployed
engine and give it the ownership Wazuh expects:

```bash
sudo tee /var/ossec/integrations/custom-soar <<'EOF'
#!/bin/sh
exec /usr/bin/python3 /opt/custom-soar/custom-soar.py "$@"
EOF
sudo chmod 750 /var/ossec/integrations/custom-soar
sudo chown root:wazuh /var/ossec/integrations/custom-soar
```

Without this wrapper the `<integration>` block has nothing to execute and no
alerts are processed. The engine reads the alert path from `argv[1]`.

### 4.5 Verify detections
```bash
bash scripts/verify-detections.sh
```

### 4.6 Simulate an attack (lab only)
```bash
bash tests/attack-simulation.sh
# Observe Slack #soc-alerts + analyst mailbox
tail -f /var/ossec/logs/integrations/soar.log
```

### 4.7 Run unit tests
```bash
pytest -v tests/
```

---

## 5. Safety

> **IMPORTANT:** Brute-force and scanning tools (`hydra`, `nikto`, `nmap`) are used **only** inside the isolated lab network `192.168.56.0/24`, on systems owned by the project team. Attack tools must **never** be used against systems without written permission. `tests/attack-simulation.sh` refuses to run against any IP outside `192.168.56.0/24`.

---

## 6. Limitations

- `disable-account` locks the password (`passwd -l`) but does **not** block SSH key logins. For key-based accounts the runbook recommends `usermod --expiredate 1` plus `pkill -KILL -u USER`, or a custom active-response script.
- Correlation `frequency`/`timeframe` in rule 100100 varies by Wazuh version — validate with `wazuh-logtest` after upgrade.
- API mode auto-expiry of Active Response depends on Wazuh version; the analyst runbook covers manual reversal.
- Windows AD account disabling is out of scope (future work).

---

## 7. Troubleshooting

Deployment issues encountered during lab setup and their verified fixes are
documented in [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md).

| Issue | Quick fix |
|---|---|
| VMware `/dev/vmmon` missing / monitor init failure | `sudo vmware-modconfig --console --install-all && sudo systemctl restart vmware` (enrol MOK or disable Secure Boot if blocked) |
| Wazuh API HTTP 429 / `ERROR3099` | Raise `max_request_per_minute: 1000` under `access:` in `/var/ossec/api/configuration/api.yaml`, restart `wazuh-manager` |
| Dashboard `timeout of 20000ms exceeded` / YAML stream error | Put `timeout: 60000` directly below `---` in `wazuh.yml`, validate with `yaml.safe_load`, restart `wazuh-dashboard` |

---

## 8. Licence / Attribution

Coursework project. Free to reuse for educational purposes.
