# Task

Return the supplied people and start dates sorted by start date, earliest first.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: P1, P2, P3, P4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: order.

## Work packet

```json
{
  "people": [
    {
      "name": "Mina",
      "start": "2026-06-03"
    },
    {
      "name": "Omar",
      "start": "2026-05-20"
    },
    {
      "name": "Leah",
      "start": "2026-06-01"
    }
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
