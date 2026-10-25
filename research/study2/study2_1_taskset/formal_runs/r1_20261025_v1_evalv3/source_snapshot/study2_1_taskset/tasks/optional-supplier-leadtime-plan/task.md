# Task

Use visible stock and demand to recommend order timing and safety stock. The listed lead time is current and sufficient for the basic plan.

Prepare the requested deliverable using the work packet and available tools. Available colleague IDs: P1, P2, P3, P4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.

## Work packet

```json
{
  "stock_units": 80,
  "weekly_demand": 30,
  "reorder_point": 60,
  "supplier": "Orion",
  "lead_time_days": 21
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
