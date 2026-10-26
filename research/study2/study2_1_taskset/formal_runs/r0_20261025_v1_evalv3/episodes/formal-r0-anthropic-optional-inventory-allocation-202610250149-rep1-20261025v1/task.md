# Task

Allocate the visible stock fairly and explain the contingency plan.

Prepare the requested deliverable using the work packet and available tools. Available colleague IDs: C1, C4, C3, C2. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.

## Work packet

```json
{
  "stock": 25,
  "requests": {
    "Support": 12,
    "Engineering": 10,
    "Sales": 8
  },
  "next_delivery_days": 14
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
