# Task

Arrange the supplied segments in the given order and calculate their end times, starting 13:00.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: C3, C4, C2, C1. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: end, duration.

## Work packet

```json
{
  "segments": [
    {
      "name": "intro",
      "minutes": 10
    },
    {
      "name": "demo",
      "minutes": 35
    },
    {
      "name": "Q&A",
      "minutes": 30
    },
    {
      "name": "wrap",
      "minutes": 15
    }
  ],
  "start": "13:00"
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
