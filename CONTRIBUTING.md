# Contributing to Atlas

Atlas values **evidence quality over submission volume**.

## Before submitting

Read `docs/METHODOLOGY.md`, `docs/DATA_DICTIONARY.md`, and `docs/CONFIDENCE.md`.

## A good submission includes

- exact marketplace URL and item ID;
- seller/store identity if known;
- current/recent price;
- exact-product or exact-listing QC source;
- why the product deserves review;
- known sizing, weight, material, batch, or flaw information;
- source links for factual claims.

## Unacceptable submissions

No affiliate-only promotion, evidence-free “trust me” recommendations, retail photos labeled as QC, AI-generated QC, seller marketing presented as fact, unverifiable “same factory as retail” claims, or duplicate records when an Atlas ID already exists.

## Product states

`candidate`, `under_review`, `approved`, `monitored`, `archived`, `rejected`.

Corrections are encouraged. If Atlas is wrong, fix it and preserve why the conclusion changed.

## Before opening a change

Run `make validate` and `make test`. Research incompleteness may warn for candidate/under-review records, but integrity errors must be fixed. Approved/monitored records fail validation if required listing verification is missing.
