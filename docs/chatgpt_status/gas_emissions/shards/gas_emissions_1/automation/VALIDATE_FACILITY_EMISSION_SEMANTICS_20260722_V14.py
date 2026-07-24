#!/usr/bin/env python3
"""Semantic gate V14: reject transfer-station, EWC and boundary contexts.

V13 already includes annual-air-mass quality gates, surrender/history,
hazardous-storage, cooling-water and flow-volume exclusions. V14 explicitly
rejects physical-treatment application class, inert/excavation and household-
commercial-industrial transfer-station descriptions, furnace-ready scrap EWC
changes, standard-to-bespoke conversion and permit-boundary expansion. Official
PRTR/PI annual releases to air still require explicit year, pollutant, air
medium, numeric annual mass, recognised unit and valid determination method.
"""
from __future__ import annotations

import VALIDATE_FACILITY_EMISSION_SEMANTICS_20260722_V13 as v13

terms = v13.v12.v11.v10.v9.v8.v7.v6.v5.v4.CONTEXT_REJECT_TERMS
v13.v12.v11.v10.v9.v8.v7.v6.v5.v4.CONTEXT_REJECT_TERMS = tuple(dict.fromkeys(terms + (
    "physical treatment facility",
    "biological treatment capacity",
    "physico-chemical treatment capacity",
    "exceeding 10 tonnes per day",
    "storage exceeding 50 tonnes",
    "inert and excavation waste transfer station",
    "household, commercial and industrial waste transfer station",
    "transfer station taking non-biodegradable wastes",
    "furnace ready scrap metal",
    "ewc codes",
    "permitted wastes",
    "increase permit boundary",
    "permit boundary expansion",
    "standard rules permit to bespoke permit",
    "withdrawn consultation period",
)))

if __name__ == "__main__":
    v13.v12.v11.v10.v9.v8.v7.v6.v5.v4.v3.review = v13.v12.v11.v10.v9.v8.v7.v6.v5.v4.review
    raise SystemExit(v13.v12.v11.v10.v9.v8.v7.v6.v5.v4.v3.main())
