#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TerraYield / AAYS UK yapı maliyeti demo motoru.

Kullanıcı yapı türü, alt tür, kat, m2, lokasyon ve ödeme bilgileri girer.
Çıktı: kalem bazlı maliyet, ilk ödeme, aylık ödeme, kaynak ve doğruluk /4.
Production DB'ye yazmaz, SQL/migration çalıştırmaz, secret loglamaz.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any, Dict
import argparse
import json

BUILDING_TYPES = ["Müstakil Ev", "Apartman", "Perakende", "Karma", "Sanayi"]
INDUSTRIAL_SUBTYPES = [
    "Factory - general",
    "Food & drink factory",
    "Chemical/allied factory",
    "Metals factory",
    "Mechanical/electrical engineering factory",
    "Electronics/computer factory",
    "Warehouse general",
    "Distribution 10-15m high",
    "Distribution 16-24m high",
    "Cold store/refrigerated",
]
RETAIL_SUBTYPES = [
    "Shop shell only",
    "Simple shop fit-out",
    "Designer store fit-out",
    "Retail warehouse shell",
    "Retail warehouse fit-out",
    "Supermarket fit-out",
]
MIXED_USE_SUBTYPES = [
    "Ground retail + flats",
    "Ground retail + apartments",
    "Retail + office + residential",
    "Office + shops + flats",
]

SOURCE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "SRC-LONDON-RESI-2026": {
        "name": "Architect Hampstead — Building Costs per Square Metre in London 2026",
        "url": "https://www.architecthampstead.co.uk/guides/building-costs-per-sqm-london-2026",
        "type": "professional_local_market_guide",
        "retrieved_date": "2026-05-20",
        "max_accuracy_4": 3,
        "confidence_cap": "MEDIUM",
        "evidence": "London 2026 new-build residential rates: standard £3,000–£3,800/m², mid £3,800–£5,000/m², high £5,000–£7,000+/m²; excludes professional fees, planning, building regulations, VAT, party wall and contingency.",
    },
    "SRC-GOV-PLANNING-FEES-2026": {
        "name": "GOV.UK — Planning fees from 1 April 2026",
        "url": "https://assets.publishing.service.gov.uk/media/69a073bb07d7bff3604d6df6/Planning_fees_-_annual_indexation_from_1_April_2026.pdf",
        "type": "official_fee_schedule",
        "retrieved_date": "2026-05-20",
        "max_accuracy_4": 4,
        "confidence_cap": "HIGH",
        "evidence": "2026 England planning fee schedule: fewer than 10 new dwellinghouses £610 per dwellinghouse; other buildings >40m² and <1000m² £610 per 75m² or part.",
    },
    "SRC-GOV-PLANNING-RULES": {
        "name": "GOV.UK — Fees for planning applications",
        "url": "https://www.gov.uk/guidance/fees-for-planning-applications",
        "type": "official_guidance",
        "retrieved_date": "2026-05-20",
        "max_accuracy_4": 4,
        "confidence_cap": "HIGH",
        "evidence": "2012 Fees Regulations as amended set 13 development categories; annual increase each 1 April from 2025 by CPI capped at 10%.",
    },
    "SRC-HMRC-VAT-708": {
        "name": "HMRC VAT Notice 708 — Buildings and construction",
        "url": "https://www.gov.uk/guidance/buildings-and-construction-vat-notice-708",
        "type": "official_tax_guidance",
        "retrieved_date": "2026-05-20",
        "max_accuracy_4": 4,
        "confidence_cap": "HIGH",
        "evidence": "New qualifying dwellings may be zero-rated; eligible conversions/renovations may be reduced-rated subject to HMRC conditions.",
    },
    "SRC-COSTMODELLING-UK-2026": {
        "name": "Costmodelling — Typical UK Construction Costs",
        "url": "https://costmodelling.com/building-costs",
        "type": "professional_indicative_benchmark",
        "retrieved_date": "2026-05-20",
        "max_accuracy_4": 3,
        "confidence_cap": "MEDIUM",
        "evidence": "Professional indicative UK construction cost benchmark by building type; use for feasibility until BCIS/quote data is available.",
    },
    "SRC-BCIS": {
        "name": "BCIS construction cost data",
        "url": "https://www.bcis.co.uk/",
        "type": "professional_subscription_dataset",
        "retrieved_date": "2026-05-20",
        "max_accuracy_4": 4,
        "confidence_cap": "HIGH",
        "evidence": "Professional subscription construction cost dataset; use exported rates/location factors when available.",
    },
    "SRC-QUOTE-REQUIRED": {
        "name": "Project-specific quote required",
        "url": "",
        "type": "quote_required",
        "retrieved_date": "2026-05-20",
        "max_accuracy_4": 1,
        "confidence_cap": "VERY_LOW",
        "evidence": "No project-specific quote supplied yet; provisional amount.",
    },
}

BASE_RATES = [
    # building_type, subtype, spec, min_per_m2, max_per_m2, source_id, accuracy, confidence, note
    ("Müstakil Ev", "One-off detached house", "Budget", 3000, 3800, "SRC-LONDON-RESI-2026", 3, "MEDIUM", "London 2026 standard residential"),
    ("Müstakil Ev", "One-off detached house", "Mid", 3800, 5000, "SRC-LONDON-RESI-2026", 3, "MEDIUM", "London 2026 mid residential"),
    ("Müstakil Ev", "One-off detached house", "High", 5000, 7000, "SRC-LONDON-RESI-2026", 3, "MEDIUM", "London 2026 high residential"),
    ("Apartman", "Flats/apartments with lifts", "Budget", 3000, 3800, "SRC-LONDON-RESI-2026", 3, "MEDIUM", "Apartment placeholder; upgrade with BCIS"),
    ("Apartman", "Flats/apartments with lifts", "Mid", 3800, 5000, "SRC-LONDON-RESI-2026", 3, "MEDIUM", "Apartment placeholder; upgrade with BCIS"),
    ("Apartman", "Flats/apartments with lifts", "High", 5000, 7000, "SRC-LONDON-RESI-2026", 3, "MEDIUM", "Apartment placeholder; upgrade with BCIS"),
    ("Perakende", "Shop shell only", "Mid", 1080, 1200, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "UK average retail shell"),
    ("Perakende", "Simple shop fit-out", "Mid", 1570, 1750, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "UK average simple shop"),
    ("Perakende", "Designer store fit-out", "Mid", 1980, 2200, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "UK average designer shop"),
    ("Perakende", "Retail warehouse shell", "Mid", 780, 880, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "UK average retail warehouse shell"),
    ("Perakende", "Retail warehouse fit-out", "Mid", 1140, 1280, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "UK average retail warehouse fit-out"),
    ("Perakende", "Supermarket fit-out", "Mid", 2520, 2800, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "UK average supermarket"),
    ("Karma", "Ground retail + flats", "Mid", 2550, 2830, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "UK mixed use benchmark"),
    ("Karma", "Office + shops + flats", "Mid", 2140, 2380, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "UK mixed office/shops/flats"),
    ("Sanayi", "Factory - general", "Mid", 1230, 1370, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "Factory general"),
    ("Sanayi", "Food & drink factory", "Mid", 2570, 2850, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "Food/drink factory"),
    ("Sanayi", "Chemical/allied factory", "Mid", 2380, 2640, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "Chemical factory"),
    ("Sanayi", "Metals factory", "Mid", 1690, 1870, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "Metals factory"),
    ("Sanayi", "Mechanical/electrical engineering factory", "Mid", 1580, 1760, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "M&E factory"),
    ("Sanayi", "Electronics/computer factory", "Mid", 2590, 2870, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "Electronics factory"),
    ("Sanayi", "Warehouse general", "Mid", 1100, 1220, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "Warehouse general"),
    ("Sanayi", "Distribution 10-15m high", "Mid", 540, 600, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "Distribution 10-15m"),
    ("Sanayi", "Distribution 16-24m high", "Mid", 580, 660, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "Distribution 16-24m"),
    ("Sanayi", "Cold store/refrigerated", "Mid", 1330, 1470, "SRC-COSTMODELLING-UK-2026", 3, "MEDIUM", "Cold store"),
]

@dataclass
class EstimateInput:
    building_type: str
    subtype: str
    location: str = "London"
    floors: int = 2
    gia_m2: float = 250.0
    spec: str = "Mid"
    dwelling_units: int = 1
    retail_ratio: float = 0.0
    residential_ratio: float = 1.0
    upfront_pct: float = 0.20
    payment_months: int = 18
    include_land: bool = False
    land_cost: float = 0.0
    vat_treatment: str = "new_qualifying_dwelling"

def get_base_rate(inp: EstimateInput) -> Dict[str, Any]:
    for row in BASE_RATES:
        if row[0] == inp.building_type and row[1].lower() == inp.subtype.lower() and row[2] == inp.spec:
            return _base_dict(row)
    for row in BASE_RATES:
        if row[0] == inp.building_type and row[1].lower() == inp.subtype.lower():
            return _base_dict(row)
    allowed = sorted({r[1] for r in BASE_RATES if r[0] == inp.building_type})
    raise ValueError(f"Alt tür bulunamadı: {inp.subtype}. Seçenekler: {allowed}")

def _base_dict(row):
    return {
        "building_type": row[0], "subtype": row[1], "spec": row[2],
        "min_per_m2": row[3], "max_per_m2": row[4], "source_id": row[5],
        "accuracy_4": row[6], "confidence": row[7], "note": row[8],
    }

def planning_fee_2026(inp: EstimateInput):
    if inp.building_type in ["Müstakil Ev", "Apartman", "Karma"] and inp.dwelling_units > 0:
        if inp.dwelling_units < 10:
            return 610.0 * inp.dwelling_units, "Fewer than 10 new dwellinghouses: £610 per dwellinghouse"
        if inp.dwelling_units <= 50:
            return 659.0 * inp.dwelling_units, "10-50 new dwellinghouses: £659 per dwellinghouse"
        return 32578 + 196 * (inp.dwelling_units - 50), ">50 dwellinghouses formula before cap"
    if inp.gia_m2 <= 40:
        return 309.0, "Other buildings <=40m²: £309"
    if inp.gia_m2 < 1000:
        return 610.0 * ceil(inp.gia_m2 / 75), "Other buildings >40 and <1000m²: £610 per 75m² or part"
    if inp.gia_m2 <= 3750:
        return 659.0 * ceil(inp.gia_m2 / 75), "Other buildings 1000-3750m²: £659 per 75m² or part"
    return 32578 + 196 * ceil((inp.gia_m2 - 3750) / 75), "Other buildings >3750m² formula before cap"

def vat_rate(inp: EstimateInput):
    t = inp.vat_treatment.lower()
    if t == "new_qualifying_dwelling":
        return 0.0, "Potential 0% VAT subject to HMRC Notice 708 eligibility", 4, "HIGH"
    if t == "reduced_5":
        return 0.05, "Potential 5% VAT subject to HMRC conditions", 4, "HIGH"
    if t == "standard_20":
        return 0.20, "Standard VAT assumption", 4, "HIGH"
    return 0.0, "VAT unknown; provisional", 1, "VERY_LOW"

def construction_breakdown(building_type, subtype):
    if building_type == "Müstakil Ev":
        return [
            ("5. Substructure", "Foundations", "Groundworks, foundations, slab, below-ground drainage", .12, .16),
            ("6. Superstructure", "Structure", "Frame, walls, floors, roof structure", .25, .30),
            ("7. Envelope", "External envelope", "Roof, facade, windows, doors, insulation", .18, .24),
            ("9-10. Services", "MEP", "Plumbing, heating, ventilation, electrics, data", .15, .20),
            ("11-12. Fit-out", "Internal fit-out", "Kitchen, bathrooms, flooring, decoration, joinery", .22, .30),
        ]
    if building_type == "Apartman":
        return [
            ("5. Substructure", "Foundations", "Foundations and basement/parking allowance", .12, .18),
            ("6. Superstructure", "Frame/core", "Frame, floors, core, stairs, roof", .28, .36),
            ("7. Envelope", "Facade/envelope", "Facade, windows, roof, insulation", .16, .24),
            ("9-10. Services", "MEP/life safety", "Risers, landlord services, lifts, fire systems", .18, .28),
            ("11-12. Fit-out", "Apartment fit-out", "Kitchens, bathrooms, flooring and finishes per unit", .20, .30),
        ]
    if building_type == "Perakende":
        return [
            ("6. Shell", "Retail shell", "Structure, roof, envelope and shell", .55, .70),
            ("7. Shopfront", "Shopfront/envelope", "Shopfront, glazing, doors, signage support", .08, .15),
            ("9-10. Services", "Retail MEP", "HVAC, electrics, data, fire alarm", .15, .25),
            ("11. Fit-out", "Retail fit-out", "Finishes, counters, display, lighting", .20, .35),
        ]
    if building_type == "Karma":
        return [
            ("6. Mixed shell/core", "Shared structure", "Mixed-use shell, core, fire separation", .55, .70),
            ("9-10. Shared services", "MEP/life safety", "Shared risers, life safety, ventilation, access", .18, .28),
            ("11. Retail fit-out", "Ground retail", "Retail fit-out for ground floor commercial", .05, .15),
            ("11. Residential fit-out", "Upper residential", "Residential fit-out for upper floors", .15, .25),
        ]
    if building_type == "Sanayi":
        rows = [
            ("5. Industrial groundworks", "Ground/slab", "Groundworks and heavy-duty floor slab", .15, .25),
            ("6. Industrial shell", "Frame/envelope", "Steel frame, envelope, roof and loading doors", .55, .70),
            ("9-10. Industrial MEP", "Power/services", "Power, ventilation, process-ready services", .15, .30),
            ("13. Yard/logistics", "External yard", "Service yard, HGV access, loading, drainage", .08, .20),
        ]
        low = subtype.lower()
        if "cold" in low or "refrigerated" in low:
            rows.append(("9-10. Specialist process", "Refrigeration", "Refrigeration plant and insulated rooms", .20, .40))
        if "food" in low:
            rows.append(("9-10. Specialist process", "Food-grade process", "Hygienic finishes, drainage and process services", .15, .30))
        if "chemical" in low:
            rows.append(("9-10. Specialist safety", "Chemical safety", "Containment, ventilation and safety systems", .18, .35))
        return rows
    return []

def make_line(cat, sub, name, unit, qty, min_total, max_total, payment_type, source_id, upfront_pct, months, notes="", accuracy=None, confidence=None):
    src = SOURCE_REGISTRY[source_id]
    mid = (min_total + max_total) / 2
    if payment_type in ["Tek sefer", "Statutory", "Quote"]:
        initial, monthly = mid, 0
    elif payment_type in ["Rezerv", "Bilgi"]:
        initial, monthly = 0, 0
    else:
        initial = mid * upfront_pct
        monthly = (mid - initial) / max(months, 1)
    return {
        "main_category": cat,
        "sub_category": sub,
        "cost_item_name": name,
        "unit": unit,
        "quantity": round(qty, 3),
        "min_total_gbp": round(min_total, 2),
        "max_total_gbp": round(max_total, 2),
        "mid_total_gbp": round(mid, 2),
        "initial_payment_gbp": round(initial, 2),
        "recurring_payment_gbp_per_month": round(monthly, 2),
        "payment_type": payment_type,
        "source_id": source_id,
        "source_name": src["name"],
        "source_url": src["url"],
        "evidence_text": src["evidence"],
        "confidence": confidence or src["confidence_cap"],
        "correctness_score_4": accuracy if accuracy is not None else src["max_accuracy_4"],
        "reliability_score_4": accuracy if accuracy is not None else src["max_accuracy_4"],
        "notes": notes,
    }

def validate(inp: EstimateInput):
    warnings = []
    if inp.gia_m2 <= 0:
        raise ValueError("gia_m2 pozitif olmalı")
    if inp.floors <= 0:
        raise ValueError("floors pozitif olmalı")
    if not 0 <= inp.upfront_pct <= 1:
        raise ValueError("upfront_pct 0-1 arasında olmalı")
    if inp.building_type not in BUILDING_TYPES:
        raise ValueError(f"Geçersiz yapı türü: {inp.building_type}")
    if inp.building_type == "Sanayi" and inp.subtype not in INDUSTRIAL_SUBTYPES:
        warnings.append("Sanayi alt türü 10 önerilen seçenekten değil.")
    if inp.building_type == "Perakende" and inp.subtype not in RETAIL_SUBTYPES:
        warnings.append("Perakende alt türü önerilen listeden değil.")
    return warnings

def estimate_cost(inp: EstimateInput) -> Dict[str, Any]:
    warnings = validate(inp)
    base = get_base_rate(inp)
    cmin = inp.gia_m2 * base["min_per_m2"]
    cmax = inp.gia_m2 * base["max_per_m2"]
    lines = []
    if inp.include_land and inp.land_cost > 0:
        lines.append(make_line("0. Arsa", "Arsa", "Arsa satın alma bedeli", "Proje", 1, inp.land_cost, inp.land_cost, "Tek sefer", "SRC-QUOTE-REQUIRED", 1, 1, "Kullanıcı girişi; resmi değerleme gerekir", 1, "VERY_LOW"))
    lines.append(make_line("5-12. Ana inşaat", "Construction package", f"{inp.building_type} / {inp.subtype} base construction package", "m² GIA", inp.gia_m2, cmin, cmax, "Aşamalı", base["source_id"], inp.upfront_pct, inp.payment_months, base["note"], base["accuracy_4"], base["confidence"]))
    for cat, sub, name, pmin, pmax in construction_breakdown(inp.building_type, inp.subtype):
        lines.append(make_line(cat, sub, name + " (breakdown only)", "% package", pmin, cmin * pmin, cmax * pmax, "Bilgi", "SRC-BCIS", inp.upfront_pct, inp.payment_months, "Bilgi satırı; ana inşaat paketiyle çifte sayma yapma", 2, "LOW"))
    fee, note = planning_fee_2026(inp)
    lines.append(make_line("1. Ön hazırlık", "Planning", "Planning application fee England 2026", "Proje", 1, fee, fee, "Statutory", "SRC-GOV-PLANNING-FEES-2026", 1, 1, note))
    lines.append(make_line("2. Profesyonel hizmetler", "Design/QS/PM", "Architect, structural engineer, M&E, QS, project management", "% construction", .12, cmin * .12, cmax * .18, "Aşamalı", "SRC-LONDON-RESI-2026", inp.upfront_pct, inp.payment_months, "12-18% allowance; quote required for 4/4"))
    lines.append(make_line("13. Dış işler", "External works", "Access, driveway/yard, drainage, landscaping, external services", "% construction", .10, cmin * .10, cmax * .20, "Aşamalı", "SRC-COSTMODELLING-UK-2026", inp.upfront_pct, min(inp.payment_months, 12), "10-20% allowance; measured design/quote required for 4/4"))
    lines.append(make_line("14. Utility bağlantıları", "Electricity", "New electricity connection / supply upgrade", "Quote", 1, 0, 0, "Quote", "SRC-QUOTE-REQUIRED", 1, 1, "DNO/provider quote gerekir", 1, "VERY_LOW"))
    rate, vat_note, vat_acc, vat_conf = vat_rate(inp)
    lines.append(make_line("16. Vergi", "VAT", "VAT allowance / treatment", "% applicable cost", rate, 0 if rate == 0 else cmin * rate, cmax * rate, "Tek sefer", "SRC-HMRC-VAT-708", 1, 1, vat_note, vat_acc, vat_conf))
    lines.append(make_line("17. Risk ve yedek", "Contingency", "Risk / contingency reserve", "% construction", .10, cmin * .10, cmax * .15, "Rezerv", "SRC-LONDON-RESI-2026", 0, 1, "QS/project risk register required for 4/4"))
    totalled = [line for line in lines if "breakdown only" not in line["cost_item_name"]]
    totals = {
        "min_total_gbp": round(sum(l["min_total_gbp"] for l in totalled), 2),
        "max_total_gbp": round(sum(l["max_total_gbp"] for l in totalled), 2),
        "mid_total_gbp": round(sum(l["mid_total_gbp"] for l in totalled), 2),
        "initial_payment_gbp": round(sum(l["initial_payment_gbp"] for l in totalled), 2),
        "recurring_payment_gbp_per_month": round(sum(l["recurring_payment_gbp_per_month"] for l in totalled), 2),
    }
    used_sources = sorted({line["source_id"] for line in lines})
    return {
        "input": inp.__dict__,
        "base_rate": base,
        "lines": lines,
        "totals": totals,
        "validation": {
            "warnings": warnings,
            "accuracy_notes": [
                "4/4: official source / BCIS export / provider or contractor quote with date and evidence.",
                "3/4: professional benchmark.",
                "2/4 or lower: model allocation/provisional assumption.",
                "Breakdown rows are informational unless elemental mode is enabled.",
            ],
            "not_done": ["No production DB write", "No migration apply", "No live quote/API fetch"],
        },
        "source_registry_subset": {sid: SOURCE_REGISTRY[sid] for sid in used_sources},
    }

def interactive_input() -> EstimateInput:
    print("Yapı türleri:")
    for i, value in enumerate(BUILDING_TYPES, 1):
        print(f"{i}. {value}")
    bt = BUILDING_TYPES[int(input("Yapı türü numarası: ").strip()) - 1]
    if bt == "Sanayi":
        opts = INDUSTRIAL_SUBTYPES
    elif bt == "Perakende":
        opts = RETAIL_SUBTYPES
    elif bt == "Karma":
        opts = MIXED_USE_SUBTYPES
    elif bt == "Apartman":
        opts = ["Flats/apartments with lifts"]
    else:
        opts = ["One-off detached house"]
    print("Alt türler:")
    for i, value in enumerate(opts, 1):
        print(f"{i}. {value}")
    subtype = opts[int(input("Alt tür numarası: ").strip()) - 1]
    return EstimateInput(
        building_type=bt,
        subtype=subtype,
        spec=input("Specification [Mid]: ").strip() or "Mid",
        gia_m2=float(input("Toplam GIA m² [250]: ").strip() or "250"),
        floors=int(input("Kat sayısı [2]: ").strip() or "2"),
        payment_months=int(input("Ödeme süresi ay [18]: ").strip() or "18"),
        upfront_pct=float(input("Ön ödeme oranı 0-1 [0.20]: ").strip() or "0.20"),
        dwelling_units=int(input("Konut birim adedi [1]: ").strip() or "1"),
        vat_treatment=input("VAT [new_qualifying_dwelling/standard_20/reduced_5/unknown] [new_qualifying_dwelling]: ").strip() or "new_qualifying_dwelling",
    )

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json")
    parser.add_argument("--output-json", default="estimate_output.json")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    if args.interactive:
        inp = interactive_input()
    elif args.input_json:
        with open(args.input_json, "r", encoding="utf-8") as handle:
            inp = EstimateInput(**json.load(handle))
    else:
        inp = EstimateInput(building_type="Müstakil Ev", subtype="One-off detached house")
    result = estimate_cost(inp)
    with open(args.output_json, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps({"output_json": args.output_json, "totals": result["totals"], "line_count": len(result["lines"])}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
