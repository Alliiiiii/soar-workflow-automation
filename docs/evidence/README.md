# SOAR Lab Evidence

Evidence captured from the Wazuh manager host `wazuh-server` (`192.168.56.10`).
The authoritative end-to-end run was on 2026-11-26 (UTC); earlier entries from
2026-11-25 are retained for comparison.

## Files

| File | Source path on host | Purpose |
|---|---|---|
| `soar.log` | `/var/ossec/logs/integrations/soar.log` | JSON decision lines written by the `custom-soar` integration for each alert it processes. |
| `local_rules.xml` | `/var/ossec/etc/rules/local_rules.xml` | Deployed two-rule correlation: `100099` (6 failures / 300 s) + `100100` (success). |
| `live_alerts_2026-11-26.json` | `/var/ossec/logs/alerts/alerts.json` (extract) | Rule `5760` / `100099` / `100100` / `651` / `657` alerts for the live `pb02` run. |

The target VM was `192.168.56.20` (Wazuh agent 4.9.2, active). The Kali VM was
moved from `192.168.56.30` to `192.168.56.133`; older notes may still say `.30`.

## Verified playbook runs

| Timestamp (UTC) | Rule | Playbook | Actions (timeout) | Result |
|---|---|---|---|---|
| 2026-11-25T21:53:01+00:00 | 5712 | `pb01_ssh_bruteforce` | firewall-drop (600s) | PASS |
| 2026-11-25T21:53:01+00:00 | 31151 | `pb03_web_attack_burst` | firewall-drop (600s) | PASS |
| 2026-11-26T08:40:11+00:00 | 100099 → 100100 | `pb02_compromised_account` | firewall-drop (3600s) + disable-account (1800s) | PASS (authoritative) |

The 2026-11-26 run used source IP `192.168.56.145` and produced Active
Response alerts `651` (firewall-drop) and `657` (disable-account). The
`disable-account` action auto-expired after 1800s; recovery was verified with
`passwd -S labuser` showing `P`.

## Rule fix

The original single rule `100100` used `frequency="6"` with
`if_matched_group=authentication_failed` and `match=Accepted`. That rule is
never evaluated for `authentication_success` events, so it could not fire.
The deployed version splits the logic:

- `100099` — level 10 helper, fires after 6 failures from the same IP in 300 s.
- `100100` — level 13, fires on the successful login while the helper tag is
  active.

`wazuh-logtest` is stateless for `frequency`, so the chain must be validated
with a live event; `tests/inject_pb02.py` reproduces it.

> `soar.log` also contains a `100100` line from an earlier deployment-validation
> run at `2026-11-25T21:53:01+00:00` and two dry-run entries at
> `2026-11-25T22:03:13+00:00` (rules 5712 and 100100). The authoritative live
> `pb02` run is the `2026-11-26T08:40:11+00:00` entry.
