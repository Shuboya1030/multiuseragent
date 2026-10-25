# Task

Return the rows in JSON with trimmed names and lowercase email addresses; preserve all other values.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: C1, C4, C2, C3. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: rows.

## Work packet

```json
{
  "rows": [
    {
      "name": " Ana Ruiz ",
      "email": "ANA@EXAMPLE.COM",
      "team": "Support"
    },
    {
      "name": "Bo Chen",
      "email": " bo@example.com ",
      "team": "Finance"
    }
  ]
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
