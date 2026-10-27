# Design reference (not an evaluation)

Old inventory has no personal data; current inventory does, changing the approver.

Full-information route:
- h1: obtain ['H1'] from ['Mark Johnson']; prerequisites [].
- h2: obtain ['H2'] from ['Emily Zhou']; prerequisites [].
- h3: obtain ['H3'] from ['Sarah Johnson']; prerequisites ['h1', 'h2'].

Inference evidence:
- Join account and inventory; personal-data rule switches approver from Sales to CTO.
