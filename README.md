# PTAB Open Analytics

> Free, open-source analytics on USPTO Patent Trial and Appeal Board (PTAB) proceedings since 2012. Institution rates by APJ panel, technology area, and petitioner. What Lex Machina charges $30,000/year for.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Data: USPTO PTAB API](https://img.shields.io/badge/Data-USPTO%20PTAB%20API-green.svg)](https://data.uspto.gov)

---

## What This Is

The PTAB publishes every inter partes review (IPR) petition, institution decision, and final written decision. The data is public. Nobody has cleaned it, organized it, and made it free to use.

This project does that. Three outputs:

1. **A cleaned dataset** (CSV/JSON) of all PTAB proceedings since 2012
2. **An interactive web report** with visualizations attorneys and researchers can actually use
3. **A qualitative findings document** from RAG analysis of institution decision text

No server. No subscription. No login. Static files hosted on GitHub Pages.

---

## What's Inside

| Metric | Why it matters |
|---|---|
| Institution rate by year (2012-present) | Is IPR getting harder to win? |
| Institution rate by technology area | Which fields are most vulnerable? |
| Institution rate by APJ panel | Which panels institute most aggressively? |
| Top petitioners by volume and win rate | Who are the serial filers? |
| Top respondents (most challenged) | Portfolio vulnerability signal |
| Petitioner vs. respondent pairing map | Who files against whom |
| Median timing: petition to institution, institution to FWD | How long does this take? |

**Partial institution note:** Pre-SAS Institute v. Iancu (2018), the PTAB could institute on some grounds and deny others. These partial institutions are flagged as a separate category, not counted as instituted or denied. A UI toggle lets you choose how to treat them in rate calculations.

---

## Methodology

All data pulled from the USPTO PTAB API v3 at [data.uspto.gov](https://data.uspto.gov). No scraping. No third-party sources.

Entity resolution via `data/canonical-names.json` — petitioner and respondent names normalized to a single canonical form (Apple Inc., not "APPLE COMPUTER INC" or "Apple, Inc"). CPC technology areas mapped to plain-English labels via `data/cpc-categories.json`.

Model evaluation results and RAG methodology are published in `output/findings.md`.

**This is not legal advice.** Verify all findings against original PTAB decisions before use in strategy or filings.

---

## Data Files

| File | Description |
|---|---|
| `data/canonical-names.json` | Entity resolution for petitioner and respondent names |
| `data/cpc-categories.json` | CPC class to plain-English technology area mapping |
| `output/data.json` | Processed metrics for the interactive report |
| `output/findings.md` | RAG qualitative analysis of institution decision text |
| `output/report.html` | Interactive web report (also hosted on GitHub Pages) |

---

## Contributing

The highest-value contributions are corrections to `data/canonical-names.json` and additions to `data/cpc-categories.json`. If you see a petitioner name mapped incorrectly or a CPC class without a plain-English label, open a PR.

All contributions must include a source (PTAB case number or CPC classification reference).

---

## Live Tool

The interactive report is hosted at: **[asobl.github.io/ptab-open-analytics](https://asobl.github.io/ptab-open-analytics)**

Want live alerts when new IPR petitions are filed in your technology area? That is what [Patent Signals](https://patentsignals.com) does. This tool is the historical snapshot. Patent Signals is the real-time monitor.

---

## About

Built by [Adam Russek-Sobol](https://adamrusseksobol.com).

I spent over a decade building software and hardware startups. One of them, [CareBand](https://carebandremembers.com), a wearable for dementia care, pulled me deep into IP strategy — first for my own company, then for founders who kept asking how I was doing it. Somewhere along the way I became the primary inventor on 20+ granted patents. One of those patents, filed in 2018, has accumulated over 500 forward citations.

I advise founders, universities, and investors on IP strategy. I also built [Patent Signals](https://patentsignals.com) and published [awesome-patent-tools](https://github.com/asobl/awesome-patent-tools), a curated index of open-source patent tooling.

PTAB data has always been public. This makes it usable.

---

*Data collected from USPTO PTAB API. Updated quarterly. See [releases](https://github.com/asobl/ptab-open-analytics/releases) for dated snapshots.*
