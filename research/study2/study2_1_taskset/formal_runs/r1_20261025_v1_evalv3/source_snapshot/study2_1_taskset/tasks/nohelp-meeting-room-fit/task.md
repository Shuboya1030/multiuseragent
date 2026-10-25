# Task

Choose the smallest room that fits the group and has a projector.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: P1, P2, P3, P4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: room.

## Work packet

```json
{
  "rooms": [
    {
      "name": "Cedar",
      "capacity": 8,
      "projector": true
    },
    {
      "name": "Maple",
      "capacity": 14,
      "projector": true
    },
    {
      "name": "Oak",
      "capacity": 20,
      "projector": false
    }
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
