# Task

Draft a concise notice from the visible incident timeline, including impact and next steps.

Prepare the requested deliverable using the work packet and available tools. Available colleague IDs: P1, P2, P3, P4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.

## Work packet

```json
{
  "service": "Search API",
  "start": "10:10 UTC",
  "resolved": "10:42 UTC",
  "cause": "expired certificate",
  "status": "resolved"
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
