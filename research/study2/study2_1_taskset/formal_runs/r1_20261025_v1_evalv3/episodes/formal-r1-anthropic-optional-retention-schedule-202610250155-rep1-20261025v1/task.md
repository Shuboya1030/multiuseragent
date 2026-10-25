# Task

Turn the visible policy into a schedule with owners and review dates.

Prepare the requested deliverable using the work packet and available tools. Available colleague IDs: C3, C1, C2, C4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.

## Work packet

```json
{
  "record_types": [
    "support tickets",
    "billing records"
  ],
  "default_years": 3,
  "owner": "Records Operations"
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
