# Task

Schedule sessions using the visible room and trainer constraints while maximizing attendance.

Prepare the requested deliverable using the work packet and available tools. Available colleague IDs: C1, C4, C2, C3. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.

## Work packet

```json
{
  "sessions": 2,
  "duration_minutes": 60,
  "trainer_available": [
    "09:00",
    "15:00"
  ],
  "room_capacity": 20,
  "staff_count": 36
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
