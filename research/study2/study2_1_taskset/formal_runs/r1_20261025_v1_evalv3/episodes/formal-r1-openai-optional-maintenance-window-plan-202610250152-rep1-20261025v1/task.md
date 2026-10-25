# Task

Choose a maintenance window and produce a mitigation plan using the visible constraints. Minimize customer disruption.

Prepare the requested deliverable using the work packet and available tools. Available colleague IDs: C2, C1, C4, C3. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.

## Work packet

```json
{
  "duration_hours": 2,
  "allowed_days": [
    "Saturday",
    "Sunday"
  ],
  "staff": [
    "on-call A",
    "on-call B"
  ],
  "deadline": "August 31"
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
