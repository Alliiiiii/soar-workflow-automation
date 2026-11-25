# Architecture

## Four layers

1. **Sensors** — Wazuh agents on endpoints. Forward logs to manager over 1514/tcp.
2. **Analytics** — Wazuh manager (decode + rule match), indexer (store), dashboard (visualise).
3. **Orchestration** — `custom-soar.py` (or Shuffle). Select playbook, apply guardrails, enrich, decide.
4. **Enforcement & notification** — Wazuh Active Response (`firewall-drop`, `disable-account`) + Slack + SMTP.

## End-to-end flow

1. Attacker sends SSH/HTTP requests to target.
2. Target logs to `/var/log/auth.log` and `/var/log/apache2/*.log`.
3. Wazuh agent forwards events.
4. Manager raises correlated alert (rule 5712 / 5763 / 31151 / 100100).
5. Level >= 10 -> `integratord` calls `custom-soar.py` with alert JSON file path.
6. Playbook selected by rule ID. Guardrails applied (whitelist, protected user, cooldown).
7. Enforcement:
   - **native** — Wazuh `<active-response>` blocks on agent (timeout-aware).
   - **api** — `custom-soar.py` calls `PUT /active-response`.
8. Slack + email summary. Decision appended to `soar.log`.
9. Timeout expires -> block/lock reversed.

## Seven-stage playbook model

```
Detect -> Enrich -> Decide -> Respond -> Notify -> Document -> Recover
```

## Two enforcement modes

| | Native (recommended default) | API |
|---|---|---|
| Triggered by | `<active-response>` blocks in `ossec.conf` | `PUT /active-response` from SOAR |
| Automatic expiry | Yes (timeout in Wazuh) | Version-dependent |
| SOAR can veto | No (use Wazuh `white_list`) | Yes (reputation, protected users, cooldown) |
| SOAR role | Enrich, notify, audit | Decide, execute, notify, audit |

## MITRE ATT&CK mapping

| Rule | Technique |
|---|---|
| 5712, 5763 | T1110 — Brute Force |
| 100100 | T1110 + T1078 — Valid Accounts |
| 31151, 31153, 31154 | T1190 — Exploit Public-Facing Application |
