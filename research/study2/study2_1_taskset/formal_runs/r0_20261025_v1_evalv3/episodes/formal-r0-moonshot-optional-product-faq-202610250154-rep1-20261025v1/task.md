# Task

Write a concise FAQ that helps customers understand the new feature and its limits.

Prepare the requested deliverable using the work packet and available tools. Available colleague IDs: C2, C4, C3, C1. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.

## Work packet

```json
{
  "feature": "scheduled exports",
  "formats": [
    "CSV",
    "JSON"
  ],
  "max_rows": 10000,
  "launch": "November 4"
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
