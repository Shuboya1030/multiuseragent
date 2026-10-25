# Task

Compare the visible bids and recommend a vendor, noting material risks.

Prepare the requested deliverable using the work packet and available tools. Available colleague IDs: C4, C1, C3, C2. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.

## Work packet

```json
{
  "vendors": [
    {
      "name": "Northstar",
      "price": 48000,
      "lead_days": 30
    },
    {
      "name": "Cedar",
      "price": 52000,
      "lead_days": 18
    }
  ],
  "budget": 55000,
  "need_by": "October 1"
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
