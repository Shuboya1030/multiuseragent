# Task

Compare total stock plus incoming units with forecast demand.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: C4, C2, C1, C3. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: available, surplus, shortfall.

## Work packet

```json
{
  "on_hand": 75,
  "incoming": 40,
  "forecast": 102
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
