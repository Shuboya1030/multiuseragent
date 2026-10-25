# Task

Return each milestone and date in chronological order.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: P1, P2, P3, P4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: order.

## Work packet

```json
{
  "milestones": [
    {
      "name": "design freeze",
      "date": "2026-07-15"
    },
    {
      "name": "QA complete",
      "date": "2026-07-08"
    },
    {
      "name": "launch",
      "date": "2026-07-22"
    }
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
