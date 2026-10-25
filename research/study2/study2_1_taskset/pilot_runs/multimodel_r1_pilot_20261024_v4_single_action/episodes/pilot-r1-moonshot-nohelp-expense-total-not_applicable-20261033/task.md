# Task

Calculate the reimbursable total from the supplied line items and produce a JSON summary.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: C3, C1, C4, C2. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: eligible_total, excluded_count, currency.

## Work packet

```json
{
  "items": [
    {
      "id": "E1",
      "amount": 18.5,
      "eligible": true
    },
    {
      "id": "E2",
      "amount": 42.0,
      "eligible": true
    },
    {
      "id": "E3",
      "amount": 12.0,
      "eligible": false
    },
    {
      "id": "E4",
      "amount": 9.5,
      "eligible": true
    }
  ],
  "currency": "USD"
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
