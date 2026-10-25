# Task

Subtract days used from each employee's annual allowance and return balances.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: P1, P2, P3, P4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: balances.

## Work packet

```json
{
  "employees": [
    {
      "name": "Ava",
      "allowance": 25,
      "used": 17
    },
    {
      "name": "Ben",
      "allowance": 20,
      "used": 12
    },
    {
      "name": "Chen",
      "allowance": 22,
      "used": 22
    }
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
