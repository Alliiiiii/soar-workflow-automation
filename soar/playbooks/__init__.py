"""Playbook modules. Each exports a ``run(alert, ctx)`` function."""
from . import pb01_ssh_bruteforce, pb02_compromised_account, pb03_web_attack_burst

# Rule ID -> playbook module
PLAYBOOKS = {
    "5712":   pb01_ssh_bruteforce,
    "5763":   pb01_ssh_bruteforce,
    "100100": pb02_compromised_account,
    "31151":  pb03_web_attack_burst,
    "31153":  pb03_web_attack_burst,
    "31154":  pb03_web_attack_burst,
}


def select(rule_id: str):
    """Return the playbook module for ``rule_id`` (or None)."""
    return PLAYBOOKS.get(str(rule_id))
