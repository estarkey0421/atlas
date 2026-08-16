#!/usr/bin/env python3
"""Generate the public Atlas hoodie research workbook from repository CSV data.

Requires the OpenAI artifact_tool runtime. Repository CSV files remain the source of truth;
the workbook is a generated release artifact.
"""
from __future__ import annotations

import csv
from pathlib import Path

from artifact_tool import SpreadsheetFile, Workbook

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "releases/spreadsheets/atlas-hoodies-v0.2.0.xlsx"


def read_csv(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def matrix(rows: list[dict[str, str]], fields: list[str]) -> list[list[object]]:
    return [[row.get(field, "") for field in fields] for row in rows]


def style_table(sheet, cell_range: str, table_name: str, widths: dict[str, int] | None = None) -> None:
    region = sheet.get_range(cell_range)
    region.format.wrap_text = True
    header = sheet.get_range(cell_range.split(":")[0] + ":" + cell_range.split(":")[1][0] + "1")
    header.format = {
        "fill": "#172554",
        "font": {"bold": True, "color": "#FFFFFF"},
        "vertical_alignment": "center",
        "row_height": 24,
    }
    sheet.tables.add(cell_range, True, table_name)
    sheet.freeze_panes.freeze_rows(1)
    if widths:
        for col, width in widths.items():
            sheet.get_range(f"{col}:{col}").format.column_width = width


def build_workbook() -> Workbook:
    products = read_csv("data/products/apparel/hoodies.csv")
    listings = read_csv("data/listings/hoodies.csv")
    evidence = read_csv("data/evidence/hoodies.csv")
    sellers = read_csv("data/sellers/sellers.csv")
    listing_by_product = {row["atlas_id"]: row for row in listings}

    wb = Workbook.create()

    # Dashboard
    dash = wb.worksheets.add("Dashboard")
    dash.merge_cells("A1:H1")
    dash.get_range("A1").values = [["ATLAS — Expedition 1: Hoodies & Sweatshirts"]]
    dash.get_range("A1:H1").format = {
        "fill": "#0F172A",
        "font": {"bold": True, "color": "#FFFFFF", "size": 18},
        "horizontal_alignment": "left",
        "vertical_alignment": "center",
        "row_height": 34,
    }
    dash.merge_cells("A2:H2")
    dash.get_range("A2").values = [["Evidence over hype. Repository data is the source of truth; this workbook is generated output."]]
    dash.get_range("A2:H2").format = {"font": {"italic": True, "color": "#475569"}, "row_height": 24}

    dash.get_range("A4:A9").values = [["Products"], ["Under review"], ["Candidates"], ["Approved"], ["Need frontal QC"], ["Need live verification"]]
    dash.get_range("B4:B9").formulas = [
        ["=COUNTA(Products!A2:A1000)"],
        ['=COUNTIF(Products!F2:F1000,"under_review")'],
        ['=COUNTIF(Products!F2:F1000,"candidate")'],
        ['=COUNTIF(Products!F2:F1000,"approved")'],
        ['=COUNTIF(\'Research Queue\'!O2:O1000,"YES")'],
        ['=COUNTIF(\'Research Queue\'!P2:P1000,"YES")'],
    ]
    dash.get_range("A4:A9").format = {"font": {"bold": True}, "fill": "#E2E8F0"}
    dash.get_range("B4:B9").format = {"font": {"bold": True, "size": 14}, "horizontal_alignment": "center"}
    dash.get_range("A4:B9").format.borders = {"all": {"style": "continuous", "color": "#CBD5E1", "weight": 1}}

    dash.get_range("D4:E4").values = [["Release", "Generated"]]
    dash.get_range("D5:E5").values = [["v0.2.0", "2026-08-15"]]
    dash.get_range("D4:E4").format = {"fill": "#172554", "font": {"bold": True, "color": "#FFFFFF"}}
    dash.get_range("D5:E5").format = {"font": {"bold": True}}

    dash.get_range("A12:B18").values = [
        ["State", "Count"],
        ["candidate", None],
        ["under_review", None],
        ["approved", None],
        ["monitored", None],
        ["archived", None],
        ["rejected", None],
    ]
    for row in range(13, 19):
        dash.get_range(f"B{row}").formulas = [[f'=COUNTIF(Products!F2:F1000,A{row})']]
    dash.get_range("A12:B12").format = {"fill": "#172554", "font": {"bold": True, "color": "#FFFFFF"}}
    chart = dash.charts.add("bar", dash.get_range("A12:B18"))
    chart.title_text = "Product state"
    chart.has_legend = False
    chart.set_position("D8", "H20")

    dash.get_range("A21:H24").merge()
    dash.get_range("A21").values = [[
        "How to use this release: start in Research Queue. P1 rows are already under review; fill seller, current price, "
        "verification date, and exact-listing frontal QC only when provenance is traceable. Never promote a row because it is popular."
    ]]
    dash.get_range("A21:H24").format = {"fill": "#F8FAFC", "font": {"color": "#334155"}, "wrap_text": True, "vertical_alignment": "top"}
    dash.get_range("A:H").format.column_width = 18
    dash.get_range("A:A").format.column_width = 24
    dash.freeze_panes.freeze_rows(2)

    # Products
    product_fields = [
        "atlas_id", "brand", "product_name", "category", "subcategory", "state", "recommendation_labels",
        "quality_score", "confidence_score", "consensus_level", "evidence_conflict", "reason_to_buy",
        "reason_not_to_buy", "known_unknowns",
    ]
    prod = wb.worksheets.add("Products")
    prod.get_range_by_indexes(0, 0, 1, len(product_fields)).values = [[
        "Atlas ID", "Brand", "Product", "Category", "Subcategory", "State", "Labels", "Quality", "Confidence",
        "Consensus", "Conflict", "Reason to buy", "Reason not to buy", "Known unknowns",
    ]]
    prod.get_range_by_indexes(1, 0, len(products), len(product_fields)).values = matrix(products, product_fields)
    style_table(prod, f"A1:N{len(products)+1}", "AtlasProducts", {"A": 14, "B": 16, "C": 30, "D": 14, "E": 16, "F": 16, "G": 22, "L": 30, "M": 30, "N": 42})
    prod.get_range(f"F2:F{len(products)+1}").conditional_formats.add_custom('=F2="under_review"', {"fill": "#FEF3C7"})
    prod.get_range(f"F2:F{len(products)+1}").conditional_formats.add_custom('=F2="candidate"', {"fill": "#E2E8F0"})
    prod.get_range(f"F2:F{len(products)+1}").conditional_formats.add_custom('=F2="approved"', {"fill": "#DCFCE7"})
    prod.get_range(f"H2:I{len(products)+1}").conditional_formats.add_color_scale({"minColor": "#FEE2E2", "midColor": "#FEF3C7", "maxColor": "#DCFCE7"})

    # Listings
    listing_fields = [
        "listing_id", "atlas_id", "marketplace", "marketplace_item_id", "url", "seller_id", "seller_name", "price_cny",
        "price_observed_at", "listing_health", "last_verified_at", "replacement_listing_id", "qc_front_url", "jadeship_url", "reddit_search_url",
    ]
    listing_headers = ["Listing ID", "Atlas ID", "Marketplace", "Item ID", "Marketplace URL", "Seller ID", "Seller", "Price CNY", "Price observed", "Health", "Last verified", "Replacement", "Front QC", "JadeShip", "Reddit search"]
    lst = wb.worksheets.add("Listings")
    lst.get_range_by_indexes(0, 0, 1, len(listing_fields)).values = [listing_headers]
    lst.get_range_by_indexes(1, 0, len(listings), len(listing_fields)).values = matrix(listings, listing_fields)
    style_table(lst, f"A1:O{len(listings)+1}", "AtlasListings", {"A": 16, "B": 14, "D": 15, "E": 42, "G": 20, "M": 42, "N": 42, "O": 42})
    lst.get_range(f"J2:J{len(listings)+1}").conditional_formats.add_custom('=J2="active"', {"fill": "#DCFCE7"})
    lst.get_range(f"J2:J{len(listings)+1}").conditional_formats.add_custom('=J2="dead"', {"fill": "#FEE2E2"})

    # Research Queue — joined view + formula-driven gaps.
    queue = wb.worksheets.add("Research Queue")
    queue_headers = [
        "Atlas ID", "State", "Brand", "Product", "Listing ID", "Marketplace", "Item ID", "Seller", "Price CNY",
        "Last verified", "Front QC", "Marketplace URL", "JadeShip", "Reddit", "Needs QC", "Needs live verify", "Priority", "Known unknowns",
    ]
    queue.get_range_by_indexes(0, 0, 1, len(queue_headers)).values = [queue_headers]
    queue_rows = []
    for p in products:
        l = listing_by_product.get(p["atlas_id"], {})
        queue_rows.append([
            p["atlas_id"], p["state"], p["brand"], p["product_name"], l.get("listing_id", ""), l.get("marketplace", ""),
            l.get("marketplace_item_id", ""), l.get("seller_name", ""), l.get("price_cny", ""), l.get("last_verified_at", ""),
            l.get("qc_front_url", ""), l.get("url", ""), l.get("jadeship_url", ""), l.get("reddit_search_url", ""),
            "", "", "", p["known_unknowns"],
        ])
    queue.get_range_by_indexes(1, 0, len(queue_rows), len(queue_headers)).values = queue_rows
    end = len(queue_rows) + 1
    queue.get_range("O2").formulas = [['=IF(K2="","YES","NO")']]
    queue.get_range(f"O2:O{end}").fill_down()
    queue.get_range("P2").formulas = [['=IF(OR(H2="",I2="",J2=""),"YES","NO")']]
    queue.get_range(f"P2:P{end}").fill_down()
    queue.get_range("Q2").formulas = [['=IF(B2="under_review","P1",IF(B2="candidate","P2","P3"))']]
    queue.get_range(f"Q2:Q{end}").fill_down()
    style_table(queue, f"A1:R{end}", "AtlasResearchQueue", {"A": 14, "B": 16, "C": 16, "D": 30, "E": 16, "G": 15, "H": 20, "K": 36, "L": 40, "M": 40, "N": 40, "R": 42})
    queue.get_range(f"O2:P{end}").conditional_formats.add_custom('=O2="YES"', {"fill": "#FEE2E2", "font": {"bold": True}})
    queue.get_range(f"Q2:Q{end}").conditional_formats.add_custom('=Q2="P1"', {"fill": "#FDE68A", "font": {"bold": True}})
    queue.get_range(f"Q2:Q{end}").conditional_formats.add_custom('=Q2="P2"', {"fill": "#E2E8F0"})

    # Evidence and sellers remain first-class even while empty.
    ev = wb.worksheets.add("Evidence")
    ev_headers = ["Evidence ID", "Atlas ID", "Listing ID", "Type", "Source URL", "Observed", "Polarity", "Summary", "Independence", "Exact match", "Notes"]
    ev_fields = ["evidence_id", "atlas_id", "listing_id", "evidence_type", "source_url", "observed_at", "polarity", "summary", "independence", "exact_match", "notes"]
    ev.get_range_by_indexes(0, 0, 1, len(ev_headers)).values = [ev_headers]
    if evidence:
        ev.get_range_by_indexes(1, 0, len(evidence), len(ev_fields)).values = matrix(evidence, ev_fields)
    style_table(ev, f"A1:K{max(2, len(evidence)+1)}", "AtlasEvidence", {"A": 16, "B": 14, "C": 16, "E": 42, "H": 44, "K": 36})

    seller_sheet = wb.worksheets.add("Sellers")
    seller_headers = ["Seller ID", "Name", "Storefront", "Specialties", "Known issues", "Return notes", "Notes"]
    seller_fields = ["seller_id", "name", "storefront_url", "specialties", "known_issues", "return_notes", "notes"]
    seller_sheet.get_range_by_indexes(0, 0, 1, len(seller_headers)).values = [seller_headers]
    if sellers:
        seller_sheet.get_range_by_indexes(1, 0, len(sellers), len(seller_fields)).values = matrix(sellers, seller_fields)
    style_table(seller_sheet, f"A1:G{max(2, len(sellers)+1)}", "AtlasSellers", {"A": 16, "B": 24, "C": 42, "D": 30, "E": 36, "F": 36, "G": 36})

    # Methodology reference
    method = wb.worksheets.add("Methodology")
    method.get_range("A1:F1").merge()
    method.get_range("A1").values = [["Atlas methodology — release reference"]]
    method.get_range("A1:F1").format = {"fill": "#0F172A", "font": {"bold": True, "color": "#FFFFFF", "size": 16}, "row_height": 30}
    method_rows = [
        ["Principle", "Evidence over reputation. Products over sellers. Uncertainty stays visible."],
        ["Tier S", "Exact-listing warehouse QC; contributor-owned in-hand photos/measurements; direct marketplace data."],
        ["Tier A", "Independent in-hand reviews, batch comparisons, recent item-specific QC, purchase/QC history."],
        ["Tier B", "Discovery/context: community sheets, catalogs, seller storefronts, aggregators."],
        ["Tier C", "Weak evidence: seller marketing, promotional content, recycled stock photos, uncorroborated claims."],
        ["Approval gate", "Exact identity + active listing + exact QC when relevant + current seller/price + recent activity + alternatives + contradictions + reproducible rationale."],
        ["Image rule", "Retail/stock/similar/AI images may never be labeled warehouse QC."],
    ]
    method.get_range("A3:B9").values = method_rows
    method.get_range("A3:A9").format = {"font": {"bold": True}, "fill": "#E2E8F0"}
    method.get_range("A3:B9").format.wrap_text = True
    method.get_range("A:A").format.column_width = 20
    method.get_range("B:B").format.column_width = 72

    return wb


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb = build_workbook()
    SpreadsheetFile.export_xlsx(wb).save(str(OUTPUT))
    print(OUTPUT)


if __name__ == "__main__":
    main()
