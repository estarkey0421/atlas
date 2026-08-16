# Atlas

> **Evidence over hype.**

Atlas is an evidence-driven buying database for Weidian, Taobao, 1688, and related marketplaces.

Most community spreadsheets answer:

> **What exists?**

Atlas is designed to answer:

> **What should I buy, why, and how confident should I be in that conclusion?**

Atlas treats products, listings, sellers, batches, warehouse QC, community reports, measurements, purchase history, and known flaws as separate pieces of evidence. Recommendations are derived from those records rather than from seller reputation or popularity alone.

## Core principles

1. **Evidence over reputation.**
2. **Products over sellers.**
3. **Facts and interpretations stay separate.**
4. **Uncertainty is documented, not hidden.**
5. **Recommendations must be reproducible.**
6. **Popularity is a signal, not proof.**
7. **If new evidence contradicts Atlas, Atlas changes.**

## Project status

**Phase:** Research Operations

**Release:** `v0.2.0`
**Active research milestone:** Expedition 1 — Hoodies & Sweatshirts

The first hoodie records remain `candidate` or `under_review` until exact listing identity, current price, frontal warehouse QC, evidence trail, and comparison checks are complete. The generated research workbook turns those missing gates into a visible, prioritized queue.

## Repository map

```text
data/
  products/      Canonical product records
  listings/      Marketplace listings and seller-specific purchase paths
  evidence/      QC, community, measurement, history, and comparison evidence
  sellers/       Seller records
  batches/       Batch/factory intelligence
  rejected/      Negative knowledge: rejected, stale, bait-and-switch, or inferior listings

schemas/         Machine-readable JSON Schemas
docs/            Methodology, data dictionary, confidence model, decisions, roadmap
research/        Source-specific research notes
scripts/         Validation, release-generation, and maintenance utilities
tests/           Integrity tests for the dataset and validator
releases/        Generated public releases such as spreadsheets
images/          Image provenance policy and permitted media
```

## Verification types

- **Warehouse Verified** — exact-listing warehouse QC located.
- **Community Verified** — corroborated by multiple independent buyer reports.
- **Atlas Reviewed** — reviewed against the published Atlas methodology.
- **Field Verified** — owned and documented by a contributor.

## Listing lifecycle

```text
candidate → under_review → approved → monitored → archived
```

A listing can also be marked `rejected`.

## What Atlas will not do

Atlas will not treat seller marketing as independent evidence, rank a product solely because it is popular, hide disagreement in one community star rating, substitute retail/stock photos for warehouse QC, or accept paid placement or sponsored rankings.

## Motto

> **Research first. Purchase second.**

## Build commands

```bash
make validate
make test
make release
```

`make release` regenerates the public hoodie workbook from repository CSV data. The CSV records remain canonical.
