# SOAR Lab Evidence

Evidence captured from the Wazuh manager host `wazuh-server` (`192.168.56.10`)
on 2026-11-25 (UTC).

## Files

| File | Source path on host | Purpose |
|---|---|---|
| `soar.log` | `/var/ossec/logs/integrations/soar.log` | JSON decision lines written by the `custom-soar` integration for each alert it processes. |
| `local_rules.xml` | `/var/ossec/etc/rules/local_rules.xml` | Deployed custom correlation rule `100100` (SSH success after repeated failures). |

The target VM was `192.168.56.20` (wazuh-agent 4.9.2, active) and the attacker
VM was `192.168.56.30` (Kali).

## Verified playbook runs

| Timestamp (UTC) | Rule | Playbook | Actions (timeout) | Result |
|---|---|---|---|---|
| 2026-11-25T21:53:01+00:00 | 5712 | `pb01_ssh_bruteforce` | firewall-drop (600s) | PASS |
| 2026-11-25T21:53:01+00:00 | 100100 | `pb02_compromised_account` | firewall-drop (3600s) + disable-account (1800s) | PASS |
| 2026-11-25T21:53:01+00:00 | 31151 | `pb03_web_attack_burst` | firewall-drop (600s) | PASS |

All three playbooks fired against the live target. The `disable-account`
action auto-expired after 1800s; the recovery phase was verified with
`passwd -S labuser` showing `P` after the timeout.

> Note: `soar.log` also contains two dry-run entries at `2026-11-25T22:03:13+00:00`
> (rules 5712 and 100100) produced during deployment validation. They are not
> part of the live end-to-end run and are retained here for completeness.
