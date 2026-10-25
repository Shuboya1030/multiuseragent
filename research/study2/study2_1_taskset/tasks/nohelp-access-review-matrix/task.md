# Task

A review is overdue when its due date is before 2026-10-01 and status is open. Return matching IDs.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: P1, P2, P3, P4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: overdue_ids.

## Work packet

```json
{
  "reviews": [
    {
      "id": "R1",
      "due": "2026-09-30",
      "status": "open"
    },
    {
      "id": "R2",
      "due": "2026-10-01",
      "status": "open"
    },
    {
      "id": "R3",
      "due": "2026-09-15",
      "status": "closed"
    }
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
