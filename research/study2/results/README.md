# Completed Study2.1 experiment results

All three packages are independent, versioned evidence releases:

| Package | Formal slots / attempts | Entry |
|---|---:|---|
| Original three-model R1 | 180 slots + 63 authorized repair attempts = 243 attempts | [R1 original README](r1_2026_11_02/README.md) |
| New mini Must repeat and GPT-5.4 full R1 | 30 + 60 = 90 independent attempts | [R1 repeat/control README](r1_openai_repeat_full_2026_11_02/README.md) |
| GPT-5.4 R0 paired control | 60 independent attempts | [R0 README](r0_gpt54_2026_11_03/README.md) |

**393 actual attempts total**, not 393 independently sampled formal tasks.
Original180 remains independent of the repair-display column (61 selected slots,
63 attempts, last-authorized rather than best-result selection). Its displayed
133 pass/47 fail is conditional on authorized repairs. The independent mini
repeat is 2/30; full GPT-5.4 R1 is 50/60; R0 is 54/60. No earlier result is replaced.

The new mini/full comparison is contemporaneous only for Must30. R0 and full
R1 pair all60 by task using the same Agent snapshot and v6 NPC, but were run at
different times without randomizing order. Historical mechanisms/input waivers,
targeted repairs, nonblind AI/user judgments and stochastic NPC deviations are
documented in the individual releases. These mixed strata are **not a fair
unqualified model ranking or three uniform independent repetitions per task**.

Each package includes complete available conversations, tools, outputs, usage,
task/gold/cost inputs, score versions, source/redaction hashes and local
standard-library-only verification/extraction instructions. Known eval-budget
gold underdetermination and 59-task sensitivity are retained in new controls.
Business/reference pass, Optional optimization T/Q, old R and NPC issues are
separate axes. **R-prime is not computed.** No R2 or unrelated Study4 results
are claimed here. No new experiments are launched by publication.
