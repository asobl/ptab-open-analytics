# RUN INSTRUCTIONS

## QUARTERLY DATA REFRESH

Run these three commands in order. Takes about 2 minutes total.

```bash
cd ptab-open-analytics

python3 collect.py
```

Pulls all PTAB proceedings and decisions from the USPTO API.
Overwrites `data/raw/proceedings-raw.json` and `data/raw/decisions-raw.json`.
Takes ~90 seconds. Prints progress every 25 pages.

```bash
python3 analyze.py
```

Computes all metrics from the raw data.
Overwrites `output/data.json` and `output/proceedings.csv`.
Takes ~5 seconds. Prints a quick stats summary when done.

```bash
cp output/report.html index.html
```

Syncs the report to the root for GitHub Pages.

---

## AFTER RUNNING

1. Update the date in `output/report.html` and `index.html`:
   - Search for `Last updated:` and change the date
   - Search for `April 2026 snapshot` in the footer and update it

2. Commit and push:

```bash
git add output/report.html output/data.json index.html
git commit -m "Q2 2026 data refresh"
git push origin main
```

GitHub Pages rebuilds automatically. Live in ~1 minute.

---

## PREREQUISITES

- Python 3.8+
- API key in `.env` file: `USPTO_ODP_API_KEY=your_key_here`
- Get a free key at: api.uspto.gov

---

## ENTITY CORRECTIONS

If petitioner or respondent names are duplicated (e.g. "Google Inc." and "Google LLC" as separate entities), add corrections to `data/canonical-names.json`:

```json
{
  "Google Inc.": "Google LLC",
  "Meta Platforms Inc": "Meta Platforms, Inc."
}
```

Then re-run `analyze.py`. No need to re-run `collect.py`.

---

## FILE LOCATIONS

| File | Purpose |
|---|---|
| `data/raw/proceedings-raw.json` | Raw API pull — proceedings (~17MB) |
| `data/raw/decisions-raw.json` | Raw API pull — decisions (~42MB) |
| `output/data.json` | Computed metrics consumed by report (~40KB) |
| `output/report.html` | The interactive web report |
| `output/proceedings.csv` | Full dataset export for spreadsheet use |
| `index.html` | Copy of report.html served by GitHub Pages |
| `data/canonical-names.json` | Entity name corrections (edit manually) |
| `data/cpc-categories.json` | Tech center labels (edit manually) |
