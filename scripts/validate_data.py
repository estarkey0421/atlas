#!/usr/bin/env python3
"""Validate Atlas CSV records and cross-file integrity.

The validator intentionally separates hard integrity failures from research-completeness
warnings. Candidate and under-review records may be incomplete; approved records may not.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]

PRODUCT_PATH = ROOT / "data/products/apparel/hoodies.csv"
LISTING_PATH = ROOT / "data/listings/hoodies.csv"
EVIDENCE_PATH = ROOT / "data/evidence/hoodies.csv"
SELLER_PATH = ROOT / "data/sellers/sellers.csv"

PRODUCT_REQUIRED_HEADERS = {
    "atlas_id", "brand", "product_name", "category", "subcategory", "state",
    "recommendation_labels", "quality_score", "confidence_score", "consensus_level",
    "evidence_conflict", "reason_to_buy", "reason_not_to_buy", "known_unknowns",
}
LISTING_REQUIRED_HEADERS = {
    "listing_id", "atlas_id", "marketplace", "marketplace_item_id", "url",
    "seller_id", "seller_name", "price_cny", "price_observed_at", "listing_health",
    "last_verified_at", "replacement_listing_id", "qc_front_url", "jadeship_url",
    "reddit_search_url",
}
EVIDENCE_REQUIRED_HEADERS = {
    "evidence_id", "atlas_id", "listing_id", "evidence_type", "source_url",
    "observed_at", "polarity", "summary", "independence", "exact_match", "notes",
}
SELLER_REQUIRED_HEADERS = {
    "seller_id", "name", "storefront_url", "specialties", "known_issues",
    "return_notes", "notes",
}

PRODUCT_STATES = {"candidate", "under_review", "approved", "monitored", "archived", "rejected"}
MARKETPLACES = {"weidian", "taobao", "1688", "other"}
LISTING_HEALTH = {"active", "unknown", "dead", "redirected", "out_of_stock", "archived"}
EVIDENCE_TYPES = {
    "warehouse_qc", "in_hand", "measurement", "weight", "reddit", "jadeship",
    "comparison", "spreadsheet", "seller_claim", "marketplace", "other",
}
POLARITIES = {"positive", "negative", "neutral", "mixed", "unknown"}
INDEPENDENCE = {"independent", "partially_independent", "seller_controlled", "unknown"}
BOOLISH = {"true", "false", "unknown", ""}


@dataclass
class ValidationResult:
    errors: list[str]
    warnings: list[str]
    counts: dict[str, int]


def read_csv(path: Path) -> tuple[list[dict[str, str]], set[str]]:
    if not path.exists():
        return [], set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader), set(reader.fieldnames or [])


def check_headers(path: Path, headers: set[str], required: set[str], errors: list[str]) -> None:
    missing = sorted(required - headers)
    if missing:
        errors.append(f"{path.relative_to(ROOT)} missing columns: {', '.join(missing)}")


def duplicate_values(rows: list[dict[str, str]], key: str) -> set[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for row in rows:
        value = row.get(key, "").strip()
        if not value:
            continue
        if value in seen:
            dupes.add(value)
        seen.add(value)
    return dupes


def valid_iso_date(value: str) -> bool:
    if not value:
        return True
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def valid_score(value: str) -> bool:
    if not value:
        return True
    try:
        score = float(value)
    except ValueError:
        return False
    return 0 <= score <= 100


def valid_positive_number(value: str) -> bool:
    if not value:
        return True
    try:
        return float(value) > 0
    except ValueError:
        return False


def url_item_id(url: str, marketplace: str) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if marketplace == "weidian":
        return (query.get("itemID") or query.get("itemId") or [None])[0]
    if marketplace == "taobao":
        return (query.get("id") or [None])[0]
    if marketplace == "1688":
        match = re.search(r"/(\d+)\.html", parsed.path)
        return match.group(1) if match else None
    return None


def validate() -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    products, product_headers = read_csv(PRODUCT_PATH)
    listings, listing_headers = read_csv(LISTING_PATH)
    evidence, evidence_headers = read_csv(EVIDENCE_PATH)
    sellers, seller_headers = read_csv(SELLER_PATH)

    check_headers(PRODUCT_PATH, product_headers, PRODUCT_REQUIRED_HEADERS, errors)
    check_headers(LISTING_PATH, listing_headers, LISTING_REQUIRED_HEADERS, errors)
    check_headers(EVIDENCE_PATH, evidence_headers, EVIDENCE_REQUIRED_HEADERS, errors)
    check_headers(SELLER_PATH, seller_headers, SELLER_REQUIRED_HEADERS, errors)

    for key, rows in (("atlas_id", products), ("listing_id", listings), ("evidence_id", evidence), ("seller_id", sellers)):
        for value in sorted(duplicate_values(rows, key)):
            errors.append(f"duplicate {key}: {value}")

    product_ids = {r.get("atlas_id", "").strip() for r in products if r.get("atlas_id", "").strip()}
    listing_ids = {r.get("listing_id", "").strip() for r in listings if r.get("listing_id", "").strip()}
    seller_ids = {r.get("seller_id", "").strip() for r in sellers if r.get("seller_id", "").strip()}

    for row in products:
        atlas_id = row.get("atlas_id", "").strip()
        if not re.fullmatch(r"ATL-\d{6}", atlas_id):
            errors.append(f"bad product id {atlas_id or '<blank>'}")
        if not row.get("product_name", "").strip():
            errors.append(f"{atlas_id}: product_name is required")
        if not row.get("category", "").strip():
            errors.append(f"{atlas_id}: category is required")
        if row.get("state", "") not in PRODUCT_STATES:
            errors.append(f"{atlas_id}: invalid state {row.get('state', '')!r}")
        for score_field in ("quality_score", "confidence_score"):
            if not valid_score(row.get(score_field, "").strip()):
                errors.append(f"{atlas_id}: {score_field} must be blank or 0-100")

    product_listing_map: dict[str, list[dict[str, str]]] = {pid: [] for pid in product_ids}
    for row in listings:
        listing_id = row.get("listing_id", "").strip()
        atlas_id = row.get("atlas_id", "").strip()
        marketplace = row.get("marketplace", "").strip()
        item_id = row.get("marketplace_item_id", "").strip()

        if not re.fullmatch(r"ATL-L-\d{6}", listing_id):
            errors.append(f"bad listing id {listing_id or '<blank>'}")
        if atlas_id not in product_ids:
            errors.append(f"orphan listing {listing_id}: unknown {atlas_id}")
        else:
            product_listing_map.setdefault(atlas_id, []).append(row)
        if marketplace not in MARKETPLACES:
            errors.append(f"{listing_id}: invalid marketplace {marketplace!r}")
        if not item_id:
            errors.append(f"{listing_id}: marketplace_item_id is required")
        if not row.get("url", "").strip():
            errors.append(f"{listing_id}: url is required")
        parsed_item_id = url_item_id(row.get("url", "").strip(), marketplace)
        if parsed_item_id and item_id and parsed_item_id != item_id:
            errors.append(f"{listing_id}: URL item id {parsed_item_id} != marketplace_item_id {item_id}")
        if marketplace == "weidian" and item_id and row.get("jadeship_url", ""):
            if f"/weidian/{item_id}" not in row["jadeship_url"]:
                errors.append(f"{listing_id}: JadeShip URL does not match item id {item_id}")
        if item_id and row.get("reddit_search_url", "") and item_id not in row["reddit_search_url"]:
            errors.append(f"{listing_id}: Reddit search URL does not contain item id {item_id}")
        seller_id = row.get("seller_id", "").strip()
        if seller_id and seller_id not in seller_ids:
            errors.append(f"{listing_id}: unknown seller_id {seller_id}")
        if not valid_positive_number(row.get("price_cny", "").strip()):
            errors.append(f"{listing_id}: price_cny must be blank or > 0")
        for field in ("price_observed_at", "last_verified_at"):
            if not valid_iso_date(row.get(field, "").strip()):
                errors.append(f"{listing_id}: {field} must be ISO YYYY-MM-DD")
        health = row.get("listing_health", "").strip()
        if health and health not in LISTING_HEALTH:
            errors.append(f"{listing_id}: invalid listing_health {health!r}")
        replacement = row.get("replacement_listing_id", "").strip()
        if replacement and replacement not in listing_ids:
            errors.append(f"{listing_id}: replacement_listing_id {replacement} does not exist")
        if replacement == listing_id:
            errors.append(f"{listing_id}: replacement_listing_id cannot point to itself")

    for row in sellers:
        seller_id = row.get("seller_id", "").strip()
        if not re.fullmatch(r"ATL-S-\d{5}", seller_id):
            errors.append(f"bad seller id {seller_id or '<blank>'}")
        if not row.get("name", "").strip():
            errors.append(f"{seller_id}: seller name is required")

    for row in evidence:
        evidence_id = row.get("evidence_id", "").strip()
        atlas_id = row.get("atlas_id", "").strip()
        listing_id = row.get("listing_id", "").strip()
        if not re.fullmatch(r"ATL-E-\d{6}", evidence_id):
            errors.append(f"bad evidence id {evidence_id or '<blank>'}")
        if atlas_id not in product_ids:
            errors.append(f"orphan evidence {evidence_id}: unknown {atlas_id}")
        if listing_id and listing_id not in listing_ids:
            errors.append(f"orphan evidence {evidence_id}: unknown listing {listing_id}")
        evidence_type = row.get("evidence_type", "").strip()
        if evidence_type not in EVIDENCE_TYPES:
            errors.append(f"{evidence_id}: invalid evidence_type {evidence_type!r}")
        if not row.get("source_url", "").strip():
            errors.append(f"{evidence_id}: source_url is required")
        if not row.get("summary", "").strip():
            errors.append(f"{evidence_id}: summary is required")
        if not valid_iso_date(row.get("observed_at", "").strip()):
            errors.append(f"{evidence_id}: observed_at must be ISO YYYY-MM-DD")
        polarity = row.get("polarity", "").strip()
        if polarity and polarity not in POLARITIES:
            errors.append(f"{evidence_id}: invalid polarity {polarity!r}")
        independence = row.get("independence", "").strip()
        if independence and independence not in INDEPENDENCE:
            errors.append(f"{evidence_id}: invalid independence {independence!r}")
        exact_match = row.get("exact_match", "").strip().lower()
        if exact_match not in BOOLISH:
            errors.append(f"{evidence_id}: exact_match must be true, false, unknown, or blank")

    # Research completeness is a warning until a product is approved/monitored.
    for row in products:
        atlas_id = row.get("atlas_id", "").strip()
        state = row.get("state", "").strip()
        linked = product_listing_map.get(atlas_id, [])
        if not linked:
            errors.append(f"{atlas_id}: product has no listing")
            continue
        activeish = [l for l in linked if l.get("listing_health", "").strip() in {"active", ""}]
        primary = activeish[0] if activeish else linked[0]
        missing = []
        if not primary.get("seller_name", "").strip(): missing.append("seller")
        if not primary.get("price_cny", "").strip(): missing.append("current price")
        if not primary.get("last_verified_at", "").strip(): missing.append("last verified date")
        if not primary.get("qc_front_url", "").strip(): missing.append("frontal QC")
        if missing:
            message = f"{atlas_id}: research incomplete ({', '.join(missing)})"
            if state in {"approved", "monitored"}:
                errors.append(message)
            else:
                warnings.append(message)

    # Schemas themselves must remain valid JSON files.
    for schema_path in sorted((ROOT / "schemas").glob("*.json")):
        try:
            payload = json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{schema_path.relative_to(ROOT)} invalid JSON: {exc}")
            continue
        if "$schema" not in payload:
            errors.append(f"{schema_path.relative_to(ROOT)} missing $schema")

    counts = {
        "products": len(products),
        "listings": len(listings),
        "evidence": len(evidence),
        "sellers": len(sellers),
        "warnings": len(warnings),
        "errors": len(errors),
    }
    return ValidationResult(errors=errors, warnings=warnings, counts=counts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Atlas data integrity")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="treat research-completeness warnings as failures")
    args = parser.parse_args()

    result = validate()
    if args.json:
        print(json.dumps({"errors": result.errors, "warnings": result.warnings, "counts": result.counts}, indent=2))
    else:
        for warning in result.warnings:
            print(f"WARN: {warning}")
        for error in result.errors:
            print(f"ERROR: {error}")
        if not result.errors:
            print(
                "Atlas validation passed: "
                f"{result.counts['products']} products, {result.counts['listings']} listings, "
                f"{result.counts['evidence']} evidence records, {result.counts['sellers']} sellers; "
                f"{result.counts['warnings']} research warnings."
            )

    failed = bool(result.errors) or (args.strict and bool(result.warnings))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
