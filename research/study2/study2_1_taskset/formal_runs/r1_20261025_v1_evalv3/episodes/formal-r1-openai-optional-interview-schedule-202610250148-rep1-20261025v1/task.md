# Task

Build a schedule from the visible interviewer availability and required sessions.

Prepare the requested deliverable using the work packet and available tools. Available colleague IDs: C2, C1, C3, C4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.

## Work packet

```json
{
  "candidate": "Sam Lee",
  "sessions": [
    "technical",
    "product",
    "team"
  ],
  "date": "January 14",
  "slot_minutes": 45,
  "available_interviewers": [
    "09:00",
    "10:00",
    "11:00",
    "13:00",
    "14:00"
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
