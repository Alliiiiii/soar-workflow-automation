# Testing Plan

## Test cases

| ID | Attack | Expected rule | Expected action | Pass criteria |
|---|---|---|---|---|
| TC-01 | hydra SSH brute force | 5712/5763 | firewall-drop | iptables DROP rule present; Slack + email received |
| TC-02 | Weak password labuser + success | 100100 | firewall-drop + disable-account | `passwd -S labuser` = L; block rule present |
| TC-03 | nikto scan | 31151/31153/31154 | firewall-drop | 400-class burst detected |
| TC-04 | Whitelist host attacks | 5712 | None (guardrail) | Slack shows "guardrail: whitelisted" |
| TC-05 | Repeat attack inside cooldown | 5712 | None (guardrail) | "still in cooldown" |
| TC-06 | root target | 100100 | firewall-drop only | No `disable-account` |

## Result record template

| Date | TC ID | Rule | Action | Slack | Email | Audit | Notes |
|---|---|---|---|---|---|---|---|
| 2026-11-25 | TC-01 | 5763 | firewall-drop | ✅ | ✅ | ✅ | auto-reversed after 600 s |

## Effectiveness metrics
- **MTTD** — alert timestamp minus log timestamp
- **MTTR** — containment minus alert
- **False-positive rate** — guardrail skips / total alerts
