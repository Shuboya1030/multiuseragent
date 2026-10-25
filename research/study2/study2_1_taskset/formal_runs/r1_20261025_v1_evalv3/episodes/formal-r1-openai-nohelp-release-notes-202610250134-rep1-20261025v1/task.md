# Task

Summarize the supplied changes under Added, Fixed, and Security headings.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: C2, C4, C3, C1. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: version, added, fixed, security.

## Work packet

```json
{
  "version": "3.2.1",
  "changes": {
    "added": [
      "CSV export"
    ],
    "fixed": [
      "timezone display"
    ],
    "security": [
      "rotated signing key"
    ]
  }
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
