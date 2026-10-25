# Figure package analysis report

## Question

Do role profiles affect help-seeking quality and resource use, and does structured presentation improve on semantically matched prose?

## Evidence

The 168-episode corrected-profile replication shows that R1−R0 improves strict first-contact validity by 73.2 percentage points (95% template-cluster bootstrap CI: 51.8 to 92.9 points) and reduces total model tokens by 49,166 per episode (95% CI: 37,018 to 61,895 fewer). Valid-path completion rises by 8.9 points (95% CI: 0 to 21.4), with a high R0 baseline of 91.1%. Mean human-contact actions are 5.25 under R0 and about 2.05 under R1/R2. The token reduction is consistent with fewer wasted contacts and fewer repeated long-context calls, but mediation by interaction count was not separately tested.

R2−R1 has no demonstrated incremental benefit: the mean token difference is 323 fewer tokens per episode (95% CI: 2,435 fewer to 1,276 more), and fixed-reward difference is +0.005 (95% CI: −0.003 to +0.017). This is not evidence that structured profiles are universally equivalent; the experiment compares two specific profile formats, with R2 text about 8% longer than R1.

## Claim candidates

- **Claim:** In this controlled simulator, providing role information reduced help-seeking token volume compared with names alone.
  - **Source evidence:** R1−R0 paired mean −49,166 tokens/episode; 95% template-cluster bootstrap CI [−61,895, −37,018]; 14 task-template clusters; success 56/56 for R1 and 51/56 for R0.
  - **Allowed wording:** “Role information was associated with lower token use and better routing in our controlled simulation.”
  - **Do not claim:** “Asking the right person always saves tokens” or “the method reduces inference cost in real companies.”
  - **Uncertainty:** Token counters are usage measures from Codex CLI, not billed cost; only 14 synthetic workflow templates.
  - **Next check:** Replicate across more task families and model endpoints; measure actual billed input/output cost with pinned model versions.
  - **Decision:** Keep, with simulator scope stated.

- **Claim:** Structured profiles did not add a measurable advantage over prose in this experiment.
  - **Source evidence:** R2−R1 token difference −323 with CI [−2,435, +1,276]; fixed reward +0.005 with CI [−0.003, +0.017].
  - **Allowed wording:** “We found no evidence of an incremental benefit for this structured-profile package.”
  - **Do not claim:** “Structured profiles never help.”
  - **Uncertainty:** R1/R2 text lengths differ and the workflow set is small.
  - **Next check:** Length-matched formats and broader organizational schemas.
  - **Decision:** Keep, weaken to no evidence of benefit.

## Interpretation

The most decision-relevant visual story is not “R2 beats R1.” It is that supplying role information (R1 or R2) sharply reduces misrouting and token volume relative to names alone, while the choice between these two profile encodings contributes little in this sample. Figure 1 shows condition means; Figure 2 shows the error mechanisms; Figure 3 shows token contrasts by fixed model configuration.

All figures use vector PDF/SVG and 95% workflow-template bootstrap intervals. See `figure-catalog.md` for full captions and caveats.
