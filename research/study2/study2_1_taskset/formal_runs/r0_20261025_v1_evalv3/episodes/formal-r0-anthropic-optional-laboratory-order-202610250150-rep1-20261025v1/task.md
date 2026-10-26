# Task

Select quantities from the visible experiment plan and prepare an order summary.

Prepare the requested deliverable using the work packet and available tools. Available colleague IDs: C2, C4, C3, C1. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.

## Work packet

```json
{
  "experiments": 24,
  "tips_per_experiment": 80,
  "boxes_contain": 1000,
  "reserve_fraction": 0.1,
  "compatible_types": [
    "standard",
    "low-retention"
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
