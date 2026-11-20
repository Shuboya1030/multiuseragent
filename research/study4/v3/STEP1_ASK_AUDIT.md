# Step 1: ASK audit of 81 Phase0 episodes (offline, heuristic labels)

Paired tasks with all four arms: 20. Labels are regex/token heuristics (see script docstring), not human review.

## ASK labels per arm (20 paired tasks; mean per episode)

| Arm | T | R | ASKs | useful | refused | repeat_refused | stale_value | wrong_person |
|---|---|---|---|---|---|---|---|---|
| A | 0.365 | 0.307 | 0.85 | 0.25 | 0.45 | 0.00 | 0.00 | 0.15 |
| B | 0.565 | 0.140 | 5.45 | 2.05 | 1.45 | 1.25 | 0.70 | 0.00 |
| C | 0.395 | 0.355 | 0.90 | 0.20 | 0.60 | 0.00 | 0.05 | 0.05 |
| D | 0.525 | -0.125 | 8.50 | 1.70 | 4.50 | 0.50 | 1.80 | 0.00 |

## B+D ASKs by label (n=279)

- useful: 75 (27%)
- refused: 119 (43%)
- repeat_refused: 35 (13%)
- stale_value: 50 (18%)
- wrong_person: 0 (0%)

## Longest same-person loops

- m-med-conference-travel D -> Chen Xinyi: 63 asks
- m-high-portal-launch D -> Priya Sharma: 24 asks
- m-med-service-credit B -> Mark Johnson: 18 asks
- m-high-service-cutover B -> Liu Qiang: 17 asks
- o-high-launch-announcement D -> Huang Jie: 15 asks
- m-high-portal-launch B -> Jessica Chen: 15 asks
- m-high-model-release D -> Liu Qiang: 14 asks
- m-high-service-cutover D -> Li Ming: 12 asks
