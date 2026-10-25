# Task

Prepare a rota from the visible launch dates and staffing. Optimize coverage for the affected customer regions.

Prepare the requested deliverable using the work packet and available tools. Available colleague IDs: C1, C3, C2, C4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.

## Work packet

```json
{
  "launch_start": "June 3",
  "launch_weeks": 4,
  "supporters": [
    "Ari",
    "Bo"
  ],
  "daily_hours": "09:00-17:00 UTC",
  "regions": [
    "North America",
    "Europe"
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
