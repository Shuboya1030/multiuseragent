# Task

Create a training packet outline from the visible modules. Make it usable by the entire invited cohort.

Prepare the requested deliverable using the work packet and available tools. Available colleague IDs: C3, C1, C4, C2. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.

## Work packet

```json
{
  "date": "July 8",
  "modules": [
    "account setup",
    "data handling",
    "incident reporting"
  ],
  "format": "PDF",
  "cohort_size": 32
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
