# Splunk — alternative SIEM path

Splunk can feed the same playbook engine. This is the smallest working setup.

## 1. Enable the Webhook alert action

Settings -> Alert actions -> enable **Webhook**. Create a new **Webhook** target:

| Field | Value |
|---|---|
| Name | `soar-custom` |
| URL | `http://192.168.56.10:8088/webhook` |
| Method | `POST` |

## 2. Wrapper (Flask) to run `custom-soar.py`

Splunk posts JSON; `custom-soar.py` reads a file. A tiny wrapper converts one to the other.

```python
# /opt/custom-soar/flask-wrapper.py
from flask import Flask, request
import json, os, subprocess, tempfile

app = Flask(__name__)
SOAR = "/opt/custom-soar/custom-soar.py"

FIELD_MAP = {
    # Splunk field name -> Wazuh-style alert field
    "src": "data.srcip",
    "user": "data.dstuser",
    "rule_id": "rule.id",
    "severity": "rule.level",
    "host": "agent.name",
}

def splunk_to_wazuh(payload: dict) -> dict:
    alert = {"rule": {}, "data": {}, "agent": {}}
    for skey, wkey in FIELD_MAP.items():
        node = alert
        parts = wkey.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = payload.get(skey)
    alert["timestamp"] = payload.get("_time")
    return alert

@app.post("/webhook")
def hook():
    alert = splunk_to_wazuh(request.get_json(force=True))
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(alert, f)
        path = f.name
    try:
        subprocess.run([SOAR, path], check=False)
    finally:
        os.unlink(path)
    return {"ok": True}
```

Run with:
```bash
sudo pip3 install flask
sudo nohup python3 /opt/custom-soar/flask-wrapper.py >/var/log/soar-wrapper.log 2>&1 &
```

## 3. Alerting search

```spl
index=linux sourcetype=linux_secure "Failed password"
| stats count by src, user
| where count > 5
| eval rule_id=5712, severity=10
| sendalert webhook param.url="http://192.168.56.10:8088/webhook"
```

The same playbooks (PB-01, PB-02, PB-03) then fire — no changes to `custom-soar.py`.
