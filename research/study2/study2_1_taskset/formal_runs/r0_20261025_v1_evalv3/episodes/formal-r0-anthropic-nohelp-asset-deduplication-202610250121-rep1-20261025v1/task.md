# Task

Return unique assets by serial number, retaining the latest warranty date.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: C4, C1, C3, C2. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: assets, unique_count.

## Work packet

```json
{
  "rows": [
    {
      "serial": "A-10",
      "warranty": "2027-01-01"
    },
    {
      "serial": "B-20",
      "warranty": "2026-06-01"
    },
    {
      "serial": "A-10",
      "warranty": "2027-08-01"
    }
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
