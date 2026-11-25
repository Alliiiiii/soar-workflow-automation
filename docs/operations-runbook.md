# Operations Runbook

## Analyst runbook
1. Check Slack #soc-alerts for the SOAR alert.
2. Verify in Wazuh dashboard: rule ID, source IP, host, user.
3. If a block was applied:
   - **Native mode:** wait for timeout (600–3600 s) or remove with
     `sudo iptables -D INPUT -s <IP> -j DROP` on the agent.
   - **API mode:** same iptables command, or re-run `custom-soar.py` with the
     same alert and an empty action list.
4. If an account was disabled:
   - `sudo passwd -u <USER>` on the agent. If the user uses SSH keys,
     also `sudo usermod --expiredate "" <USER>`.

## Troubleshooting

| Symptom | Check |
|---|---|
| Rule not firing | `/var/ossec/bin/wazuh-logtest` with sample log; verify level >= 10 |
| Integration not invoked | `grep custom-soar /var/ossec/logs/ossec.log`; verify `<integration>` block |
| Slack 403 | Webhook URL validity; re-generate from Slack app |
| Slack 404 | Webhook was revoked; re-create |
| SMTP auth fail | Use Gmail **App Password**, not the account password |
| `config.yaml` not found | `custom-soar.py` looks beside itself — copy to `/opt/custom-soar/config.yaml` |
| `disable-account` doesn't stop key logins | Expected — see runbook step 4 |

## Maintenance checklist
- [ ] Rotate Slack webhook + Gmail app password every 90 days
- [ ] Review `soar.log` for anomalies
- [ ] Verify rules 5712/5763/31151 still exist after Wazuh upgrade
- [ ] Re-run `scripts/verify-detections.sh` after any manager upgrade
- [ ] Check `soar-state.json` size — prune entries older than 7 days
