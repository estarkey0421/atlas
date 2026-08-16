# Atlas Research Queue

The generated workbook includes a **Research Queue** sheet. It is a work surface, not a second source of truth.

Priority is derived from the canonical product state:

- **P1** — `under_review`: finish verification before expanding the candidate pool.
- **P2** — `candidate`: promising, but not yet mature enough for approval work.
- **P3** — all other states: monitor or revisit as needed.

The queue exposes two formula-driven gates:

- **Needs QC** — no exact-listing frontal QC URL is recorded.
- **Needs live verify** — seller, current price, or verification date is missing.

Completing a queue row means updating repository CSV records and evidence first, then regenerating the workbook. Do not edit the release workbook as though it were canonical data.

## Promotion rule

A product must not move to `approved` or `monitored` while the validator reports missing seller, current price, verification date, or frontal QC for its primary listing.
