# Task

Create a phased plan that respects the visible staffing and deadline constraints.

Prepare the requested deliverable using the work packet and available tools. Available colleague IDs: P1, P2, P3, P4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.

## Work packet

```json
{
  "workspaces": 120,
  "deadline": "March 31",
  "migration_capacity_per_day": 20,
  "engineers": 2
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
