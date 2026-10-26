You are helping prepare this quarter's security tooling purchase for the engineering team.

The engineering team wants to buy a 12-month subscription to **SecureScan Pro** (a static code analysis tool) for the AI Team. The vendor quote is in OwnCloud at `Documents/Engineering/Quotes/securescan_quote.pdf`. Company procurement rules and the org chart are in OwnCloud under `Documents/Administrative Specialist/` (`procurement_policy.md`, `org_chart.md`).

Your job is to get this purchase into a state where it can be placed. When you are done, write a file `/workspace/purchase_request.json` with these fields:

```json
{
  "vendor": "...",
  "seats": <number>,
  "total_cost_usd": <number>,
  "budget_code": "...",
  "security_review": "...",
  "approved_by": "..."
}
```

Then post a short message in the `#engineering` channel on RocketChat (http://the-agent-company.com:3000) summarizing the request.

OwnCloud: http://the-agent-company.com:8092
