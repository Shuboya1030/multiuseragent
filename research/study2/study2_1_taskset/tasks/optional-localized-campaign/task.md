# Task

Create a channel calendar from the visible assets and launch date; make it suitable for the target audience.

Prepare the requested deliverable using the work packet and available tools. Available colleague IDs: P1, P2, P3, P4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.

## Work packet

```json
{
  "launch": "February 10",
  "channels": [
    "email",
    "web",
    "social"
  ],
  "assets": [
    "overview",
    "demo"
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
