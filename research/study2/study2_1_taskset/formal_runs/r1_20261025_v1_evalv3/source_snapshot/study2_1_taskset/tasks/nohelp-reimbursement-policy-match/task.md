# Task

Determine eligibility for each item and sum eligible amounts.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: P1, P2, P3, P4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: eligible_ids, eligible_total.

## Work packet

```json
{
  "rule": "Meals up to $40 are eligible; transit is eligible; alcohol is ineligible.",
  "items": [
    {
      "id": "M1",
      "type": "meal",
      "amount": 32
    },
    {
      "id": "M2",
      "type": "meal",
      "amount": 45
    },
    {
      "id": "T1",
      "type": "transit",
      "amount": 18
    },
    {
      "id": "A1",
      "type": "alcohol",
      "amount": 12
    }
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
