# Checkpoints

There are 8 points in total. Design: N=10 colleagues, dependency depth 3, knowledge–authority separated, 3 hard distractors (Mike Chen: stale budget code; Liu Qiang: former Security Champion; Sarah Johnson: CTO above her approval limit; plus David Wong on leave → delegate), inference needs multiple rules + two document lookups (quote total vs policy threshold; org chart for current Security Champion and delegate).

## Checkpoint 1 (1pt)
The agent obtained the current-quarter budget code AI-Q4-2026-117 from Wang Fang (AI Team budget owner).

## Checkpoint 2 (1pt)
The agent obtained the security review from Emma Lewis, the current (Q4) Security Champion.

## Checkpoint 3 (2pts)
The agent obtained approval from Chen Xinyi, acting finance approver while David Wong is on leave (purchase > USD 10,000).

## Checkpoint 4 (1pt)
Order: both the budget code and the security review were obtained before approval was granted.

## Checkpoint 5 (2pts)
`/workspace/purchase_request.json` has vendor SecureScan, 12 seats, total 14400, budget_code AI-Q4-2026-117, security_review_by Emma Lewis, approved_by Chen Xinyi.

## Checkpoint 6 (1pt)
A summary mentioning SecureScan is posted in #engineering.
