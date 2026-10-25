# Task

Report the number passed, failed, and total; mark release-ready only if no tests failed.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: P1, P2, P3, P4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: passed, failed, total, release_ready.

## Work packet

```json
{
  "tests": [
    {
      "id": "unit",
      "result": "pass"
    },
    {
      "id": "integration",
      "result": "pass"
    },
    {
      "id": "security",
      "result": "pass"
    }
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
