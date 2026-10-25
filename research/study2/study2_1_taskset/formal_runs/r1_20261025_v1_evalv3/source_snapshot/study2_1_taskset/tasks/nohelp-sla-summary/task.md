# Task

Calculate the monthly attainment percentage and report whether the 95% target was met.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: P1, P2, P3, P4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: attainment_percent, target_met.

## Work packet

```json
{
  "tickets": 200,
  "within_sla": 193,
  "target_percent": 95
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
