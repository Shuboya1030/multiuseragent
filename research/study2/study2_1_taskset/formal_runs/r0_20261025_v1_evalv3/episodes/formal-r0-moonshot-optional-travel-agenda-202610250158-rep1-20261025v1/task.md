# Task

Use the visible itinerary to create a feasible agenda and transport plan. Both listed routes are operating; a transfer buffer is a helpful contingency.

Prepare the requested deliverable using the work packet and available tools. Available colleague IDs: C2, C4, C1, C3. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.

## Work packet

```json
{
  "arrival_city": "Berlin",
  "meeting_city": "Potsdam",
  "arrival": "09:00",
  "meeting": "11:00",
  "date": "April 8",
  "rail_minutes": 25,
  "taxi_minutes": 40
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
