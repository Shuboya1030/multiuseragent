# Task

Sort risks by score descending, where score is probability times impact; preserve the text.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: C3, C2, C1, C4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: order.

## Work packet

```json
{
  "risks": [
    {
      "id": "K1",
      "probability": 0.2,
      "impact": 5,
      "text": "vendor delay"
    },
    {
      "id": "K2",
      "probability": 0.5,
      "impact": 4,
      "text": "data migration"
    },
    {
      "id": "K3",
      "probability": 0.4,
      "impact": 2,
      "text": "training gap"
    }
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
