# Task

Calculate the tax and total using the supplied rate; report any mismatch.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: C3, C2, C4, C1. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: tax, computed_total, matches.

## Work packet

```json
{
  "subtotal": 250,
  "tax_rate": 0.08,
  "invoice_total": 270
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
