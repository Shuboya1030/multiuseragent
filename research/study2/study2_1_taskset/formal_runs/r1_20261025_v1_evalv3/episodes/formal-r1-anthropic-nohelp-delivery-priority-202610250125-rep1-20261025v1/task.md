# Task

Return delivery IDs sorted by promised date, earliest first.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: C1, C2, C4, C3. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: order.

## Work packet

```json
{
  "deliveries": [
    {
      "id": "D1",
      "date": "2026-10-28"
    },
    {
      "id": "D2",
      "date": "2026-10-25"
    },
    {
      "id": "D3",
      "date": "2026-10-26"
    }
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
