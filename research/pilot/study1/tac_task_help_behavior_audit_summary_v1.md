# TAC task-level contact and help-seeking audit summary (v1)

Single-analyst task.md review cross-checked against each scenario roster. Evaluator outputs exist for each task × model run, but contain task checkpoints/scores rather than gold labels for recipient appropriateness or help episodes. This audit defines task relation and candidate eligibility; it does not establish who was correct to ask.

## Task instruction categories

| Task relation | Tasks |
|---|---:|
| Contact explicitly required (including conditional branches/gates) | 32 |
| Contact conditional on a stated trigger | 6 |
| No interpersonal contact/help request specified | 2 |
| **Total** | **40** |

## Transcript-confirmed message categories

Rule-assisted candidate labels among message bodies appearing after an Admin sender/timestamp marker in the immediately following chat observation:

| Message-function candidate | Events |
|---|---:|
| Information/input request | 264 |
| Coordination/availability | 58 |
| Feedback/evaluation | 38 |
| Status inquiry | 22 |
| Information/task-result delivery | 30 |
| Advice/expertise request | 11 |
| Acknowledgment/action commitment | 15 |
| Approval/action request | 8 |
| Name-only or unclear | 4 |
| Answer/data response | 2 |
| Short reply or unclear | 1 |
| Other/unclear | 4 |

## Messages by task instruction relation

| Task relation | Confirmed message events |
|---|---:|
| Explicitly task-required contact | 387 |
| Conditional contact | 61 |
| No explicit interpersonal contact request | 9 |

Extraction identified 656 Enter-submitted chat-text candidates; 457 passed transcript confirmation and 199 are unconfirmed. Confirmed events span 10 model configurations and 186 task-model episodes. The transcript-confirmed recipient set differs from the legacy parser in 19 episodes; see `recipient_reconciliation_queue_v1.csv`.

## Interpretation

Most confirmed behavior is task-completion communication: requests for input, feedback collection, and availability/status queries. This supports an empirical taxonomy of human-contact/help functions, but the trace set does not cleanly reveal spontaneous help-seeking because 32 of 40 task prompts explicitly require contact and 6 specify conditional contact. The narrow claim should focus on **how model configurations carry out prescribed or condition-triggered help/contact**, and on which episodes genuinely involve clarification, blocker removal, or expert input.

The event-function labels are lexical candidates and the confirmation rule is an extraction aid; manually review against task state, recipient, replies, and uptake before final coding. The revised lexical pass separates obvious task-result delivery and acknowledgments from the earlier broad `other` bucket.
