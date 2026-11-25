# Shuffle SOAR (optional alternative)

A drag-and-drop SOAR workflow equivalent to `custom-soar.py`. Use this if you
prefer a GUI instead of the Python integration, or to demonstrate the same
decisions in a commercial-style tool.

## Import

1. Install Shuffle on `shuffle-server` (Docker):
   ```bash
   git clone https://github.com/Shuffle/Shuffle
   cd Shuffle
   docker compose up -d
   ```
2. Browse to `https://192.168.56.40:3443`.
3. Workflows -> Import -> choose `workflow-export.json`.
4. Edit the **Wazuh API** and **Slack** nodes to fill in your credentials.
5. Copy the **Webhook** trigger URL into the Wazuh `<integration>` block:
   ```xml
   <integration>
     <name>shuffle</name>
     <hook_url>http://192.168.56.40:3001/api/v1/hooks/webhook_xxx</hook_url>
     <level>10</level>
     <alert_format>json</alert_format>
   </integration>
   ```

## Nodes

```
Webhook trigger
   └─> Parse alert (rule.id, data.srcip, data.dstuser)
        └─> Guardrail check (whitelist + protected users + cooldown)
             ├─> Wazuh API PUT /active-response (firewall-drop or disable-account)
             ├─> Slack post
             └─> Email
```
