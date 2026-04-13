#!/usr/bin/env python3
"""
collect.py -- Pull all PTAB proceedings and decisions from the USPTO ODP API.

Endpoints (confirmed live April 2026):
  POST https://api.uspto.gov/api/v1/patent/trials/proceedings/search
  GET  https://api.uspto.gov/api/v1/patent/trials/decisions/search

Outputs (all to data/raw/ -- gitignored):
  data/raw/proceedings-raw.json   -- all proceedings (~19k records)
  data/raw/decisions-raw.json     -- all decisions with OCR text (~20k records)
  data/raw/collect-stats.json     -- run metadata

Max page size: 100. No rate limit headers observed -- using 0.2s sleep between calls.
API key: loaded from .env (never committed).
"""

import json
import os
import subprocess
import time
from datetime import datetime, timezone

# ---- Config ----
BASE = "https://api.uspto.gov/api/v1/patent/trials"
PAGE_SIZE = 100
SLEEP = 0.2  # seconds between calls -- conservative, no rate limit headers observed

# Load API key
key = None
env_path = os.path.join(os.path.dirname(__file__), ".env")
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith("USPTO_ODP_API_KEY="):
            key = line.split("=", 1)[1]
            break

if not key:
    raise RuntimeError("USPTO_ODP_API_KEY not found in .env")

RAW_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)


def post(url, body):
    result = subprocess.run(
        ["curl", "-s", "-X", "POST",
         "-H", f"X-API-KEY: {key}",
         "-H", "Content-Type: application/json",
         "-H", "Accept: application/json",
         url, "-d", json.dumps(body)],
        capture_output=True, text=True
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [WARN] Non-JSON response: {result.stdout[:200]}")
        return {}


def get(url):
    result = subprocess.run(
        ["curl", "-s",
         "-H", f"X-API-KEY: {key}",
         "-H", "Accept: application/json",
         url],
        capture_output=True, text=True
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  [WARN] Non-JSON response: {result.stdout[:200]}")
        return {}


# ---- Step 1: Pull all proceedings ----
print("=" * 60)
print("Step 1: Pulling proceedings")
print("=" * 60)

# Get total count first
first = post(f"{BASE}/proceedings/search", {"pagination": {"offset": 0, "limit": 1}})
total_proceedings = first.get("count", 0)
print(f"Total proceedings: {total_proceedings:,}")
pages = (total_proceedings // PAGE_SIZE) + (1 if total_proceedings % PAGE_SIZE else 0)
print(f"Pages to fetch: {pages} (page size {PAGE_SIZE})")
print()

all_proceedings = []
errors = 0

for page in range(pages):
    offset = page * PAGE_SIZE
    data = post(f"{BASE}/proceedings/search", {"pagination": {"offset": offset, "limit": PAGE_SIZE}})
    batch = data.get("patentTrialProceedingDataBag", [])

    if not batch:
        print(f"  [WARN] Page {page+1}: empty batch at offset {offset}")
        errors += 1
    else:
        all_proceedings.extend(batch)

    if (page + 1) % 25 == 0 or page == pages - 1:
        print(f"  Page {page+1}/{pages} -- {len(all_proceedings):,} proceedings collected")

    time.sleep(SLEEP)

print(f"\nProceedings collected: {len(all_proceedings):,}")
print(f"Errors/empty pages: {errors}")

# Save
out_path = os.path.join(RAW_DIR, "proceedings-raw.json")
with open(out_path, "w") as f:
    json.dump(all_proceedings, f)
print(f"Saved to {out_path}")


# ---- Step 2: Pull all decisions ----
print()
print("=" * 60)
print("Step 2: Pulling decisions")
print("=" * 60)

# Get total count
first_dec = get(f"{BASE}/decisions/search?limit=1&offset=0")
total_decisions = first_dec.get("count", 0)
print(f"Total decisions: {total_decisions:,}")
dec_pages = (total_decisions // PAGE_SIZE) + (1 if total_decisions % PAGE_SIZE else 0)
print(f"Pages to fetch: {dec_pages}")
print()

all_decisions = []
dec_errors = 0

for page in range(dec_pages):
    offset = page * PAGE_SIZE
    data = get(f"{BASE}/decisions/search?limit={PAGE_SIZE}&offset={offset}")
    batch = data.get("patentTrialDocumentDataBag", [])

    if not batch:
        print(f"  [WARN] Page {page+1}: empty batch at offset {offset}")
        dec_errors += 1
    else:
        all_decisions.extend(batch)

    if (page + 1) % 25 == 0 or page == dec_pages - 1:
        print(f"  Page {page+1}/{dec_pages} -- {len(all_decisions):,} decisions collected")

    time.sleep(SLEEP)

print(f"\nDecisions collected: {len(all_decisions):,}")
print(f"Errors/empty pages: {dec_errors}")

out_path = os.path.join(RAW_DIR, "decisions-raw.json")
with open(out_path, "w") as f:
    json.dump(all_decisions, f)
print(f"Saved to {out_path}")


# ---- Step 3: Save run stats ----
stats = {
    "collected_at": datetime.now(timezone.utc).isoformat(),
    "proceedings_total": len(all_proceedings),
    "decisions_total": len(all_decisions),
    "proceedings_errors": errors,
    "decisions_errors": dec_errors,
    "page_size": PAGE_SIZE,
    "sleep_seconds": SLEEP,
}
stats_path = os.path.join(RAW_DIR, "collect-stats.json")
with open(stats_path, "w") as f:
    json.dump(stats, f, indent=2)

print()
print("=" * 60)
print("Collection complete")
print(f"  Proceedings: {len(all_proceedings):,}")
print(f"  Decisions:   {len(all_decisions):,}")
print(f"  Stats:       {stats_path}")
print("=" * 60)
