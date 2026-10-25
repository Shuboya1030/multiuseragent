# Task

Sum the listed available capacities and compare with the 64-vCPU request.

Complete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: C4, C3, C1, C2. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: available_vcpu, request_satisfied, surplus_vcpu.

## Work packet

```json
{
  "clusters": {
    "east": 28,
    "west": 24,
    "central": 20
  },
  "request_vcpu": 64
}
```

## Contact tool
Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.
