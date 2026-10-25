# Task

Assign each ticket exactly one category from the rubric and return JSON.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: C3, C4, C2, C1. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: labels.

## Work packet

```json
{
  "rubric": {
    "billing": "charges or invoices",
    "access": "login or permissions",
    "bug": "unexpected product behavior"
  },
  "tickets": [
    {
      "id": "T1",
      "text": "I was charged twice"
    },
    {
      "id": "T2",
      "text": "I cannot sign in"
    },
    {
      "id": "T3",
      "text": "Export crashes on click"
    }
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
