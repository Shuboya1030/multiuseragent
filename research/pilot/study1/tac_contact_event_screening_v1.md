# TAC help-seeking/contact event screening (v1)

This is a **single-analyst, rule-assisted screening**, not validated semantic annotation. It extracts Enter-submitted Rocket.Chat text from archived browser trajectories when the resulting page is a direct, channel, or group chat. It includes task-directed communication (e.g., data collection, feedback requests, status updates) and therefore does not equate every contact with agent help-seeking.

- Raw trajectories present: 400.
- Enter-submitted chat-text candidates: 656.
- Candidates confirmed as a posted Admin message (body follows the sender/timestamp marker) in the immediately following rendered transcript: 457; 199 are unconfirmed and excluded from function counts.
- Model configurations with at least one extracted outgoing message: 10 of 10 in the complete panel.
- DM recipients are parsed from the resulting direct-message page; channel/group mentions are extracted from the submitted text. Recipient appropriateness is unverified.
- Purpose labels are lexical candidates. The CSV retains confirmed and unconfirmed submissions; the function-count table below includes only message bodies located after the transcript's Admin sender/timestamp marker.

## Provisional message-function counts

| Function candidate | Events |
|---|---:|
| `acknowledgment_or_action_commitment` | 15 |
| `advice_or_expertise_request` | 11 |
| `answer_or_data_response` | 2 |
| `approval_or_action_request` | 8 |
| `coordination_or_availability` | 58 |
| `feedback_or_evaluation_request` | 38 |
| `information_or_input_request` | 264 |
| `information_or_task_result_delivery` | 30 |
| `name_only_or_unclassifiable_contact` | 4 |
| `other_message` | 4 |
| `short_reply_or_unclassifiable` | 1 |
| `status_request` | 22 |

## Events by model configuration

| Model configuration | Confirmed messages | Share of all confirmed messages |
|---|---:|---:|
| `gemini-1.5-pro` | 33 | 7.2% |
| `gemini-2.0-flash` | 74 | 16.2% |
| `gpt-4o-2024-08-06` | 46 | 10.1% |
| `llama-3.1-405b` | 53 | 11.6% |
| `llama-3.1-70b` | 30 | 6.6% |
| `llama-3.3-70b` | 65 | 14.2% |
| `nova-pro-v1_0` | 8 | 1.8% |
| `qwen2-72b` | 9 | 2.0% |
| `qwen2.5-72b` | 32 | 7.0% |
| `sonnet-20241022` | 107 | 23.4% |

Function counts and within-model shares are in `tac_message_function_by_model_v1.csv`. These are descriptive event distributions, not model-level help-seeking rates: task exposure, run behavior, and repeated messages differ, and labels remain provisional.

## Interpretation boundary

The labels separate observable message functions (e.g., asking for missing information, requesting feedback, coordinating availability, requesting action, delivering information, short reply/UI ambiguity). They do **not** establish the trigger for asking, whether the agent could have found the answer elsewhere, whether it should have asked, whether the recipient was appropriate, or whether a reply was used. Those require task- and episode-context review. Do not treat these screening counts as Study 1 findings.

## Next coding pass

1. Review all extracted messages in context and distinguish genuine human-directed messages from search/navigation artifacts.
2. Assign task-level trigger and contact policy using task prompt, scenario facts, and evaluator evidence.
3. Code response received, response usefulness, and uptake only where trajectory evidence supports it.
4. Compare model configurations on task-matched rates after restricting to validated opportunities; do not infer causal effects.
