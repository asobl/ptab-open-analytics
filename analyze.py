#!/usr/bin/env python3
"""
analyze.py -- Compute all PTAB metrics and output data.json + CSV files.

Reads:  data/raw/proceedings-raw.json
        data/raw/decisions-raw.json
        data/canonical-names.json     (entity resolution -- created if missing)
        data/cpc-categories.json      (tech center labels -- created if missing)

Writes: output/data.json             (schema-compliant, consumed by report.html)
        output/proceedings.csv        (filterable table export)
        output/decisions.csv          (filterable table export)

Partial institution handling (per plan.md decision):
  OUTCOMES = ["instituted", "denied", "partial"]
  Pre-2018 partial institutions flagged separately, not counted as binary.
  trialOutcomeCategory mappings defined in OUTCOME_MAP below.
"""

import json
import csv
import os
from collections import defaultdict, Counter
from datetime import datetime

BASE = os.path.dirname(__file__)
RAW = os.path.join(BASE, "data", "raw")
DATA = os.path.join(BASE, "data")
OUT  = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)
os.makedirs(DATA, exist_ok=True)

# ---- Outcome mapping (trialOutcomeCategory -> instituted/denied/partial) ----
OUTCOME_MAP = {
    "Institution Granted":                              "instituted",
    "Final Written Decision":                           "instituted",
    "Affirmed":                                         "instituted",
    "Settled After Institution":                        "instituted",
    "Request For Adverse Judgment After Institution":   "instituted",
    "Institution Denied":                               "denied",
    "Settled Before Institution":                       "denied",
    "Dismissed Before Institution":                     "denied",
    "Dismissed":                                        "other",
    "Reversed":                                         "other",
    "Vacated/Remanded":                                 "other",
    "Terminated":                                       "other",
}

# ---- Technology center labels ----
# Default mapping -- community can improve via data/cpc-categories.json
DEFAULT_TC_LABELS = {
    "1600": "Biotech / Pharma",
    "1700": "Chemical / Materials",
    "2100": "Computer Architecture / Software",
    "2400": "Networking / Security",
    "2600": "Communications / Signal Processing",
    "2800": "Semiconductor / Electrical",
    "3600": "Transportation / Commerce / Finance",
    "3700": "Mechanical / Medical Devices",
}

# Load or create cpc-categories.json
tc_path = os.path.join(DATA, "cpc-categories.json")
if os.path.exists(tc_path):
    with open(tc_path) as f:
        TC_LABELS = json.load(f)
else:
    TC_LABELS = DEFAULT_TC_LABELS
    with open(tc_path, "w") as f:
        json.dump(TC_LABELS, f, indent=2)
    print(f"Created {tc_path} with default tech center labels")

# Load or create canonical-names.json
canon_path = os.path.join(DATA, "canonical-names.json")
if os.path.exists(canon_path):
    with open(canon_path) as f:
        CANONICAL = json.load(f)
else:
    CANONICAL = {}
    with open(canon_path, "w") as f:
        json.dump(CANONICAL, f, indent=2)
    print(f"Created empty {canon_path} -- add entity corrections here")

def canonicalize(name):
    if not name:
        return "Unknown"
    name = name.strip()
    # Strip trailing "et al." variations
    for suffix in [" et al.", " et al", " Et Al.", " Et Al"]:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    return CANONICAL.get(name, name)

def parse_year(date_str):
    if not date_str:
        return None
    try:
        return int(date_str[:4])
    except (ValueError, TypeError):
        return None

# ---- Load raw data ----
print("Loading raw data...")
with open(os.path.join(RAW, "proceedings-raw.json")) as f:
    proceedings = json.load(f)
with open(os.path.join(RAW, "decisions-raw.json")) as f:
    decisions = json.load(f)

print(f"  Proceedings: {len(proceedings):,}")
print(f"  Decisions:   {len(decisions):,}")

# ---- Build proceedings index ----
# Use decisions as primary source (richer data), index proceedings by trialNumber
proc_index = {p["trialNumber"]: p for p in proceedings}

# ---- Process decisions into normalized records ----
print("\nProcessing decisions...")

records = []
for d in decisions:
    trial_num = d.get("trialNumber", "")
    trial_meta = d.get("trialMetaData", {})
    patent_owner = d.get("patentOwnerData", {})
    petitioner = d.get("regularPetitionerData", {})
    decision_data = d.get("decisionData", {})

    raw_outcome = decision_data.get("trialOutcomeCategory", "")
    outcome = OUTCOME_MAP.get(raw_outcome, "other")

    petition_year = parse_year(trial_meta.get("petitionFilingDate"))
    institution_date = trial_meta.get("institutionDecisionDate")
    institution_year = parse_year(institution_date)
    filing_date = trial_meta.get("petitionFilingDate", "")
    trial_type = trial_meta.get("trialTypeCode", "")
    tc = patent_owner.get("technologyCenterNumber", "")
    art_unit = patent_owner.get("groupArtUnitNumber", "")

    # Flag potential partial institutions (pre-2018 cases)
    # Will be refined in RAG pass -- for now flag by year
    if outcome == "instituted" and petition_year and petition_year < 2018:
        # Mark as potentially partial -- analyze.py cannot determine this without reading text
        # RAG pass will refine these. For now: count as instituted but flag.
        is_pre_sas = True
    else:
        is_pre_sas = False

    # Compute petition-to-institution timing (days)
    timing_days = None
    if filing_date and institution_date:
        try:
            t0 = datetime.strptime(filing_date[:10], "%Y-%m-%d")
            t1 = datetime.strptime(institution_date[:10], "%Y-%m-%d")
            timing_days = (t1 - t0).days
        except ValueError:
            pass

    records.append({
        "trial_number": trial_num,
        "trial_type": trial_type,
        "petition_year": petition_year,
        "institution_year": institution_year,
        "institution_date": institution_date,
        "filing_date": filing_date,
        "outcome": outcome,
        "raw_outcome": raw_outcome,
        "is_pre_sas": is_pre_sas,
        "tc": tc,
        "tc_label": TC_LABELS.get(tc, f"Tech Center {tc}" if tc else "Unknown"),
        "art_unit": art_unit,
        "petitioner": canonicalize(petitioner.get("realPartyInInterestName")),
        "respondent": canonicalize(patent_owner.get("realPartyInInterestName")),
        "patent_number": patent_owner.get("patentNumber", ""),
        "timing_days": timing_days,
    })

print(f"  Processed: {len(records):,} records")

# ---- Metric 1: Institution rates by year ----
print("\nComputing institution rates by year...")

by_year = defaultdict(lambda: {"instituted": 0, "denied": 0, "partial": 0, "other": 0, "pre_sas_flagged": 0})
for r in records:
    yr = r["petition_year"]
    if yr and 2012 <= yr <= 2026:
        by_year[yr][r["outcome"]] += 1
        if r["is_pre_sas"]:
            by_year[yr]["pre_sas_flagged"] += 1

institution_rates = []
for yr in sorted(by_year.keys()):
    b = by_year[yr]
    total_decided = b["instituted"] + b["denied"]
    rate = round(b["instituted"] / total_decided, 4) if total_decided > 0 else None
    total_excl_other = total_decided + b["partial"]
    rate_with_partial = round(b["instituted"] / total_excl_other, 4) if total_excl_other > 0 else None
    institution_rates.append({
        "year": yr,
        "instituted": b["instituted"],
        "denied": b["denied"],
        "partial": b["partial"],
        "other": b["other"],
        "pre_sas_flagged": b["pre_sas_flagged"],
        "rate_instituted": rate,
        "rate_partial_excluded": rate_with_partial,
        "total_decided": total_decided,
    })

# ---- Metric 2: Institution rates by technology ----
print("Computing institution rates by technology...")

by_tc = defaultdict(lambda: {"instituted": 0, "denied": 0, "partial": 0, "other": 0})
for r in records:
    if r["tc"]:
        by_tc[r["tc"]][r["outcome"]] += 1

by_technology = []
for tc, b in sorted(by_tc.items(), key=lambda x: -(x[1]["instituted"] + x[1]["denied"])):
    total_decided = b["instituted"] + b["denied"]
    rate = round(b["instituted"] / total_decided, 4) if total_decided > 0 else None
    by_technology.append({
        "tc": tc,
        "label": TC_LABELS.get(tc, f"Tech Center {tc}"),
        "instituted": b["instituted"],
        "denied": b["denied"],
        "partial": b["partial"],
        "other": b["other"],
        "rate_instituted": rate,
        "total_decided": total_decided,
    })

# ---- Metric 3: Top petitioners ----
print("Computing top petitioners...")

petitioner_stats = defaultdict(lambda: {"filings": 0, "instituted": 0, "denied": 0, "other": 0})
for r in records:
    p = r["petitioner"]
    if p and p != "Unknown":
        petitioner_stats[p]["filings"] += 1
        petitioner_stats[p][r["outcome"]] += 1

top_petitioners = []
for name, s in sorted(petitioner_stats.items(), key=lambda x: -x[1]["filings"])[:50]:
    decided = s["instituted"] + s["denied"]
    win_rate = round(s["instituted"] / decided, 4) if decided > 0 else None
    top_petitioners.append({
        "canonical_name": name,
        "filings": s["filings"],
        "instituted": s["instituted"],
        "denied": s["denied"],
        "other": s["other"],
        "win_rate": win_rate,
    })

# ---- Metric 4: Top respondents ----
print("Computing top respondents...")

respondent_stats = defaultdict(lambda: {"challenged": 0, "instituted": 0, "denied": 0})
for r in records:
    resp = r["respondent"]
    if resp and resp != "Unknown":
        respondent_stats[resp]["challenged"] += 1
        if r["outcome"] == "instituted":
            respondent_stats[resp]["instituted"] += 1
        elif r["outcome"] == "denied":
            respondent_stats[resp]["denied"] += 1

top_respondents = []
for name, s in sorted(respondent_stats.items(), key=lambda x: -x[1]["challenged"])[:50]:
    top_respondents.append({
        "canonical_name": name,
        "challenged": s["challenged"],
        "instituted_against": s["instituted"],
        "denied": s["denied"],
        "survival_rate": round(s["denied"] / s["challenged"], 4) if s["challenged"] > 0 else None,
    })

# ---- Metric 5: Top petitioner-respondent pairs ----
print("Computing petitioner-respondent pairs...")

pair_stats = defaultdict(lambda: {"filings": 0, "instituted": 0})
for r in records:
    p, resp = r["petitioner"], r["respondent"]
    if p != "Unknown" and resp != "Unknown":
        pair_stats[(p, resp)]["filings"] += 1
        if r["outcome"] == "instituted":
            pair_stats[(p, resp)]["instituted"] += 1

top_pairs = []
for (p, resp), s in sorted(pair_stats.items(), key=lambda x: -x[1]["filings"])[:100]:
    top_pairs.append({
        "petitioner": p,
        "respondent": resp,
        "filings": s["filings"],
        "instituted": s["instituted"],
    })

# ---- Metric 6: Trial type breakdown ----
print("Computing trial type breakdown...")

by_type = defaultdict(lambda: {"filings": 0, "instituted": 0, "denied": 0})
for r in records:
    tt = r["trial_type"] or "Unknown"
    by_type[tt]["filings"] += 1
    if r["outcome"] in ("instituted", "denied"):
        by_type[tt][r["outcome"]] += 1

trial_types = []
for tt, s in sorted(by_type.items(), key=lambda x: -x[1]["filings"]):
    decided = s["instituted"] + s["denied"]
    trial_types.append({
        "trial_type": tt,
        "filings": s["filings"],
        "instituted": s["instituted"],
        "denied": s["denied"],
        "rate_instituted": round(s["instituted"] / decided, 4) if decided > 0 else None,
    })

# ---- Metric 7: Timing stats ----
print("Computing timing stats...")

valid_timings = [r["timing_days"] for r in records if r["timing_days"] and 0 < r["timing_days"] < 730]
if valid_timings:
    valid_timings.sort()
    n = len(valid_timings)
    median_timing = valid_timings[n // 2]
    p25 = valid_timings[n // 4]
    p75 = valid_timings[3 * n // 4]
else:
    median_timing = p25 = p75 = None

timing = {
    "median_petition_to_institution_days": median_timing,
    "p25_days": p25,
    "p75_days": p75,
    "sample_size": len(valid_timings),
}

# ---- Assemble data.json ----
print("\nAssembling data.json...")

data_out = {
    "meta": {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "proceedings_total": len(proceedings),
        "decisions_total": len(decisions),
        "records_processed": len(records),
        "date_range": {"start": "2012-09-16", "end": "2026-04-13"},
        "partial_institution_treatment": "separate",
        "note": "Pre-2018 cases flagged as pre_sas_flagged. Partial institution category populated after RAG pass.",
    },
    "institution_rates": institution_rates,
    "by_technology": by_technology,
    "top_petitioners": top_petitioners,
    "top_respondents": top_respondents,
    "petitioner_respondent_pairs": top_pairs,
    "trial_types": trial_types,
    "timing": timing,
}

out_path = os.path.join(OUT, "data.json")
with open(out_path, "w") as f:
    json.dump(data_out, f, indent=2)
print(f"  Saved {out_path}")

# ---- Write CSV exports ----
print("Writing CSV exports...")

# Proceedings CSV
proc_csv_path = os.path.join(OUT, "proceedings.csv")
proc_fields = ["trial_number", "trial_type", "petition_year", "outcome", "raw_outcome",
               "tc", "tc_label", "petitioner", "respondent", "patent_number",
               "filing_date", "institution_date", "timing_days", "is_pre_sas"]
with open(proc_csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=proc_fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(records)
print(f"  Saved {proc_csv_path} ({len(records):,} rows)")

# Summary stats to console
print()
print("=" * 60)
print("QUICK STATS")
print("=" * 60)
total_decided = sum(1 for r in records if r["outcome"] in ("instituted", "denied"))
total_instituted = sum(1 for r in records if r["outcome"] == "instituted")
total_denied = sum(1 for r in records if r["outcome"] == "denied")
total_other = sum(1 for r in records if r["outcome"] == "other")

print(f"Total records:         {len(records):,}")
print(f"Total decided (I/D):   {total_decided:,}")
print(f"Instituted:            {total_instituted:,}  ({100*total_instituted//total_decided if total_decided else 0}%)")
print(f"Denied:                {total_denied:,}  ({100*total_denied//total_decided if total_decided else 0}%)")
print(f"Other/pending:         {total_other:,}")
print(f"Median timing (days):  {median_timing}")
print()
print("Institution rate by year (last 5):")
for row in institution_rates[-5:]:
    bar = "█" * int((row["rate_instituted"] or 0) * 20)
    print(f"  {row['year']}  {bar:<20}  {(row['rate_instituted'] or 0)*100:.1f}%  ({row['instituted']}I / {row['denied']}D)")
print()
print("Top 5 petitioners:")
for p in top_petitioners[:5]:
    print(f"  {p['canonical_name'][:40]:<40}  {p['filings']} filings  {(p['win_rate'] or 0)*100:.0f}% win rate")
print()
print("=" * 60)
print("Done. Outputs in output/")
print("  data.json      -- web report data")
print("  proceedings.csv -- full dataset export")
print("=" * 60)
