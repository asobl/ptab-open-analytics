# PTAB Open Analytics: Build Plan

**Status:** Approved for build
**Date:** April 2026
**Owner:** Adam Russek-Sobol
**Repo:** ptab-open-analytics (to be created on GitHub)

---

## What This Is

An open-source PTAB analytics tool that surfaces what Lex Machina and Docket Navigator sell for $30k+/year. The data is public. Nobody has organized it cleanly and made it free.

Three outputs:
1. A cleaned dataset (CSV/JSON) of all PTAB proceedings since 2012
2. An interactive web report with visualizations attorneys and researchers can actually use
3. A qualitative findings doc from RAG analysis of decision text

No server. No live updates. One-time data pull, static output, published to GitHub Pages. Maintenance cost: zero after launch.

---

## Who Uses This

**Primary:** Patent attorneys doing pre-filing IPR strategy research. They want to know institution rates by panel, by tech area, by petitioner. They pay for this today.

**Secondary:** IP researchers and academics studying PTAB trends. They need clean structured data and methodology they can cite.

**Adam:** Uses it when advising founders on IPR risk for their patent portfolios. Instant credibility signal.

---

## The Three Modules

### Module 1: Quantitative Analytics

Pull structured data from the PTAB API v3. Run aggregations. Output as interactive HTML.

**Metrics to compute:**

| Metric | Why it matters |
|---|---|
| Institution rate by year (2012-2026) | Is IPR getting harder? |
| Institution rate by CPC technology class | Which tech areas are most vulnerable? |
| Institution rate by APJ panel | Which panels institute most aggressively? |
| Top 25 petitioners by volume and win rate | Who are the serial filers? |
| Top 25 respondents (who gets challenged most) | Portfolio vulnerability signal |
| NPE vs operating company filing patterns | Who drives IPR: trolls or competitors? |
| Petitioner vs respondent pairing map | Who files against whom |
| Median timing: petition to institution, institution to FWD | How long does this actually take? |
| Claim survival rates by tech area | Which claims hold up? |

**Data source:** PTAB API v3 at `developer.uspto.gov/api-catalog`
- No auth required for most endpoints
- ~15,000 proceedings since 2012
- ~150 API calls to pull everything (3-5 minutes)

No AI needed for this module. Pure Python + Pandas.

---

### Module 2: Interactive Web Report (the main output)

This is the thing attorneys and researchers actually use. Not a dashboard that needs a server. A self-contained HTML file hosted on GitHub Pages.

**Features:**
- Filter by technology area (CPC class or plain-English category: IoT, Software, Biotech, Pharma, Wearables, etc.)
- Filter by year range
- Filter by petitioner or respondent
- Click an APJ to see their profile: institution rate, tech areas, panel history
- Click a petitioner to see all their filings and outcomes
- Network graph: petitioner nodes connected to respondent nodes, sized by filing volume
- Heatmap: tech area vs year, colored by institution rate

**Tech stack:**
- Chart.js for bar/line charts (same as the 873-repo report)
- D3.js for the network graph and heatmap
- Vanilla JS filtering (no React, no build step, just a file)
- Data embedded as JSON in the HTML or loaded from local JSON files
- Hosted on GitHub Pages -- zero cost, zero maintenance

**Why a web app matters here:** You can take screenshots and screen recordings of the interactive graph for LinkedIn. "I built a free Lex Machina alternative" is a strong post. The visual output is also what gets shared and linked to, which builds backlinks to Patent Signals.

---

### Module 3: RAG Analysis on Decision Text (qualitative)

Run a large language model over the full text of ~500 institution decisions to extract qualitative insights that structured data cannot answer:

- "What arguments successfully defeat institution in IoT/wearable cases?"
- "What claim language survives IPR vs. gets cancelled?"
- "What distinguishing factors do APJs cite when granting vs. denying institution?"
- "How has the obviousness standard evolved in software patent cases since 2016?"

**Output:** A Markdown findings report published on the repo. Citable. Shows methodology. Gives researchers something to reference. Not a live tool -- a published analysis, like an academic paper but readable.

**Implementation approach:** Simple first, framework only if quality data says it's needed. First run uses `rag_simple.py` (sentence-transformers + numpy, ~60 lines). If Q1 RAG accuracy checks fail the 90% threshold, upgrade to the full LlamaIndex stack. See RAG Stack section for details and config defaults to validate.

---

## AI Infrastructure: No Paid APIs

Per decision: no paid AI APIs. All inference runs on RunPod using open models. Total cost: $3-15 depending on model size and eval runs.

### Model Evaluation Protocol (runs before full analysis)

Do not skip this. Legal text is specific. A model that scores well on general benchmarks may hallucinate PTAB arguments or miss claim language distinctions. Run a structured eval first, pick the winner, then run the full analysis on one model.

**Step 1: Pull eval sample**

Select 30 PTAB decisions stratified across:
- 3 technology areas: IoT/wearables, software/UI, biotech/pharma
- 3 outcome types: institution granted on all grounds, institution denied, partial institution
- 3 time periods: 2013-2016, 2017-2020, 2021-2026

30 decisions total. Short enough to run quickly. Diverse enough to surface model weaknesses.

**Step 2: Standardized eval prompts**

Run every model on every decision with the same 5 prompts. Do not change prompts between models.

| Prompt | What it tests |
|---|---|
| "What was the petitioner's primary obviousness argument?" | Legal reasoning, argument extraction |
| "Did the board institute on all grounds? If not, which grounds were denied and why?" | Multi-part structured extraction |
| "What specific claim language did the board find most relevant to their decision?" | Precision on claim text |
| "What secondary considerations did the patent owner raise? Were they persuasive to the board?" | Nuanced legal reading |
| "Summarize the board's decision rationale in exactly 3 bullet points." | Concision, format compliance, accuracy |

**Step 3: Scoring rubric (10 points per decision)**

Score each model's output on each prompt:

| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Factual accuracy | Wrong | Partially right | Mostly right | Exact |
| Completeness | Missed most | Missed some | Minor gaps | Complete |
| Hallucination | Invented facts | Minor drift | Borderline | None |

Plus 1 point for format compliance (followed instructions exactly). Max 10 per decision, 300 per model total.

**Step 4: Models to evaluate**

| Model | Size | Why test it |
|---|---|---|
| `Llama 3.1 70B Instruct` | 70B | Meta's strongest open instruction model |
| `Qwen 2.5 72B Instruct` | 72B | Top-tier at structured extraction, strong on long docs |
| `DeepSeek R1 70B` | 70B | Chain-of-thought reasoning, good for multi-step legal logic |
| `Llama 3.3 70B Instruct` | 70B | Newer Llama, worth comparing to 3.1 |
| `Mistral 8x22B` | 141B MoE | Strong instruction following, handles long context well |

Run all 5 on the 30-decision eval set. Total RunPod cost for eval: $2-5.

**Step 5: Pick the winner**

Rank by total score. If two models are within 5% of each other, use the smaller/faster one to keep the full analysis run cheaper. Document which model won and publish the eval results in the repo. Researchers will find the methodology credible. Attorneys will trust the outputs more knowing you tested.

**Step 6: Run full analysis on the winning model**

Only after eval is complete and a model is selected. Run the full 500-decision RAG analysis on the winning model. Export all results. Shut the instance down.

---

### RAG Stack on RunPod

**First run: simple approach (`rag_simple.py`)**

For 500 documents and one quarterly run, a minimal script is the right tool. No frameworks, no version pinning risk.

- `sentence-transformers` for embedding (all-MiniLM-L6-v2 or similar, runs on CPU for this corpus size)
- `numpy` cosine similarity for retrieval
- `vLLM` for model serving (faster than Ollama for batch inference, same RunPod instance)
- All results exported to JSON/Markdown before shutting down
- ~60-80 lines of Python, no framework dependencies

This is the implementation unless Q1 RAG accuracy checks (see Measurement Plan) fail the 90% threshold. If retrieval quality is insufficient after measuring, upgrade to LlamaIndex v2 (see below).

**Phase 2 upgrade: `rag_v2.py` (only if Q1 accuracy checks fail)**

If the simple approach produces retrieval quality below 90% on the manual spot check, park it and switch to:
- LlamaIndex for document chunking and retrieval
- ChromaDB for local vector storage
- Same vLLM model serving

Do not build Phase 2 until Phase 1 quality data says it's needed.

**Config defaults to validate on first run (not pre-committed):**

| Parameter | Default | How to validate |
|---|---|---|
| Chunk size | 512 tokens | Check `memory/chunk-performance.json` after run: if top-retrieved chunks are consistently at the edges, reduce to 256 |
| Overlap | 50 tokens | Same check: if context is getting cut mid-argument, increase to 100 |
| Top-k retrieval | 5 chunks per query | If accuracy checks fail, try 8 |

These are starting points, not decisions. Tune from the performance log after the first run.

**Instance type:** A40 (48GB VRAM) handles 70B models with 4-bit quantization. [Price UNVERIFIED -- confirm at runpod.io/pricing before starting instance. Community Cloud vs Secure Cloud differs.] Estimated $0.40-0.79/hour. Full eval + analysis run: under 10 hours total.

---

## Monetization Flow

This is not a direct revenue product. It is a lead generation and authority-building asset that feeds Patent Signals. Here is the exact flow.

---

### The Funnel

```
GitHub repo (credibility + discovery)
        |
        v
patentsignals.com/ptab (traffic + branding)
        |
        v
Email gate on the findings report (list building)
        |
        v
3-email nurture sequence (education + positioning)
        |
        v
Patent Signals waitlist or early access (revenue)
```

---

### Step 1: GitHub Repo (credibility)

The repo lives at `github.com/asobl/ptab-open-analytics`. It is the proof of work. Attorneys and researchers who find it via search or LinkedIn go to the repo, read the methodology, see the quality of the analysis, and trust it. The README footer links to patentsignals.com/ptab as the hosted version.

---

### Step 2: patentsignals.com/ptab (the tool lives here, not just GitHub)

Embed the interactive HTML report directly on Patent Signals. This does three things:

- Drives SEO to patentsignals.com on terms like "PTAB analytics," "IPR institution rates," "free PTAB data"
- Keeps the Patent Signals brand in front of every attorney who uses the tool
- Makes the tool feel like a product, not just a GitHub repo

The page has a simple header: "PTAB Open Analytics -- Free. Open source. Updated [date]." And a footer: "This is a snapshot from [date]. Patent Signals monitors new PTAB filings in real time."

---

### Step 3: Email Gate on the Findings Report

The interactive chart report is fully free, no gate. The deeper RAG findings doc ("What the Data Shows: IPR Argument Patterns by Technology Area") sits behind a single email field.

Copy on the gate: "Get the full findings report -- what arguments work, which claim language survives, and how institution rates vary by tech area. Free. No pitch."

That last line matters. Attorneys are allergic to sales. Promise no pitch, deliver no pitch in the first email. The sequence earns the right to mention Patent Signals later.

---

### Step 4: Email Nurture Sequence (3 emails)

**Email 1 (immediate):** The findings report PDF. No pitch. Just the document they asked for, cleanly formatted, with Adam's name and patentsignals.com in the footer.

**Email 2 (day 5):** One insight from the data they probably missed. Something like: "The institution rate for software patents dropped 14 points between 2019 and 2023. Here's why that matters for prosecution strategy." Short, useful, no ask.

**Email 3 (day 12):** The positioning email. "The tool you used is a snapshot from April 2026. The PTAB files new proceedings every week. If you want to track new IPR filings in your technology area as they happen, that's what Patent Signals does. Early access is open now."

Three emails. One ask. Done.

---

### Conversion Paths

| Who | How they convert | To what |
|---|---|---|
| Attorney doing IPR strategy research | Uses the tool, gates on findings, gets email 3 | Patent Signals early access |
| Researcher or academic | Cites the data, reaches out to Adam | Advisory conversation or collaboration |
| Founder Adam is already advising | Adam pulls up the tool in a meeting | Credibility closes the engagement |
| Law firm partner who shares it internally | Firm-wide tool usage, one partner reaches out | Firm-level Patent Signals subscription |

---

### What Patent Signals Offers That This Tool Cannot

| This tool | Patent Signals |
|---|---|
| Snapshot from April 2026 | Live, updates with every new filing |
| All tech areas, no filtering by your portfolio | Monitored for your specific patents and tech area |
| Historical institution rates | Alerts when a new IPR petition targets your space |
| Static findings doc | Ongoing intelligence, delivered to your inbox |

The free tool earns the trust. Patent Signals earns the revenue.

---

### Revenue Estimate (conservative)

If the tool reaches 500 attorneys or researchers in year one:
- 20% gate conversion = 100 emails collected
- 10% of those convert to Patent Signals at any price point = 10 customers
- At $99/month that is $990 MRR traceable to this tool

That is the floor. One law firm adopting it as a team tool changes the math entirely.

---

### What It Actually Does for Brand

| Value | How it shows up |
|---|---|
| Authority | "I built the free Lex Machina alternative" is a sentence that travels |
| Content fuel | LinkedIn post, Medium article, conference talk, all from one build |
| Advisory credibility | Pull it up in any founder IP conversation, instantly credible |
| SEO for Patent Signals | PTAB-related traffic lands on patentsignals.com |
| Network | Attorneys who star the repo are the exact people Patent Signals needs to reach |

---

## Repo Structure

```
ptab-open-analytics/
  README.md                  -- what this is, how to use it, methodology, how to cite
  plan.md                    -- this file
  LICENSE                    -- MIT
  collect.py                 -- pulls PTAB API data, saves to data/
  analyze.py                 -- computes all metrics, outputs to output/
  rag_analysis.py            -- RunPod/Ollama RAG pass on decision text
  graph.py                   -- builds knowledge graph data for D3
  requirements.txt           -- Python dependencies
  data/
    proceedings.json         -- raw PTAB proceedings
    decisions.json           -- institution + FWD outcomes
    panels.json              -- APJ panel compositions
    decision_text/           -- sampled decision text for RAG
  output/
    report.html              -- the interactive web report (GitHub Pages index)
    findings.md              -- RAG qualitative analysis
    data.json                -- pre-processed data for the web report
```

---

## data.json Schema (write this first, before any module)

`output/data.json` is the contract between analyze.py and report.html. Both modules must be written to this schema. Define it before writing either.

**Write `output/data.schema.json` at the start of Step 3, before writing any analyze.py code. Commit it. Then write analyze.py to produce it and report.html to consume it.**

```json
{
  "meta": {
    "generated_at": "2026-04-13T00:00:00Z",
    "proceedings_total": 15000,
    "date_range": { "start": "2012-09-16", "end": "2026-04-01" },
    "partial_institution_treatment": "separate"
  },
  "institution_rates": [
    {
      "year": 2023,
      "instituted": 412,
      "denied": 188,
      "partial": 22,
      "rate_instituted": 0.631,
      "rate_partial_excluded": 0.687
    }
  ],
  "by_technology": [
    {
      "cpc_class": "H04W",
      "label": "Wireless / IoT",
      "instituted": 87,
      "denied": 43,
      "partial": 9,
      "rate_instituted": 0.617
    }
  ],
  "top_petitioners": [
    {
      "canonical_name": "Apple Inc.",
      "filings": 312,
      "instituted": 201,
      "denied": 111,
      "win_rate": 0.644
    }
  ],
  "top_respondents": [
    {
      "canonical_name": "Qualcomm Inc.",
      "challenged": 148,
      "survived": 62,
      "cancelled": 86
    }
  ],
  "apj_profiles": [
    {
      "name": "Jacqueline Wright Bonilla",
      "canonical_id": "bonilla-j",
      "panels": 94,
      "institution_rate": 0.702,
      "top_tech_areas": ["H04W", "G06F"],
      "years_active": [2013, 2026]
    }
  ],
  "petitioner_respondent_pairs": [
    {
      "petitioner": "Apple Inc.",
      "respondent": "Qualcomm Inc.",
      "filings": 24,
      "instituted": 18
    }
  ],
  "timing": {
    "median_petition_to_institution_days": 174,
    "median_institution_to_fwd_days": 371
  }
}
```

**Field rules:**
- All rate fields are floats 0.0–1.0 (not percentages)
- `canonical_name` always comes from `canonical-names.json` -- no raw API strings
- `partial_institution_treatment` in meta records which toggle was active when data was generated
- All counts are integers, never null (use 0)
- `rate_partial_excluded` is always present alongside `rate_instituted` so report.html can switch between them without recalculating

---

## Build Order

**Step 1:** Create GitHub repo `ptab-open-analytics`
**Step 2:** Write `collect.py` -- pull all PTAB proceedings via data.uspto.gov API
**Step 2.5:** Write `output/data.schema.json` -- define the data contract before any other module. Commit it. Both analyze.py and report.html are written to this schema.
**Step 3:** Write `analyze.py` -- compute all metrics, output `data.json` matching the schema exactly
**Step 4:** Build `report.html` -- interactive web report with Chart.js + D3, consuming `data.json` via the schema contract
**Step 5:** Set up GitHub Pages on the repo
**Step 6:** Pull 30 decision text samples for model eval (stratified by tech area, outcome, year)
**Step 7:** Write `eval.py` -- runs all 5 models on the 30-decision sample with standardized prompts
**Step 8:** Run eval on RunPod, score outputs, pick winning model, publish eval results
**Step 9:** Pull full 500-decision sample for RAG analysis
**Step 10:** Run full RAG analysis on RunPod with `rag_simple.py` (sentence-transformers + numpy). Run accuracy checks. If 90%+ pass: publish findings.md. If not: upgrade to `rag_v2.py` (LlamaIndex stack) and re-run.
**Step 11:** Build network graph visualization (`graph.py` + D3 in report)
**Step 12:** Write README with full methodology, eval results, and attribution
**Step 13:** LinkedIn post + Medium article referencing the tool

Steps 1-5 get the quantitative tool live (one session, no AI needed).
Steps 6-8 are the model eval (one RunPod session, $2-5).
Steps 9-12 are the RAG analysis layer (one RunPod session, $5-10).
Each phase is independently publishable. Ship Step 5, then add depth.

---

## Technical Validation

### Component-by-Component: The Six Questions

---

**PTAB API**

1. **Current?** CRITICAL FINDING: The old PTAB API at `developer.uspto.gov` is being shut down April 20, 2026 -- 7 days from today. It has migrated to the new Open Data Portal at `data.uspto.gov`. All `collect.py` code must use `data.uspto.gov`, not the old endpoint. Seth Cronin's `uspto-cli` already uses the new ODP. Source: USPTO Developer Hub (confirmed via live check April 13, 2026).

2. **Math?** ~15,000 PTAB proceedings since 2012. At 100 per page = 150 search calls. Each proceeding links to decisions (institution, FWD) requiring additional calls. Estimate 3-5 calls per proceeding for full enrichment = ~50,000 total calls. Rate limits for the new ODP are [UNVERIFIED -- must check data.uspto.gov/apis before writing collect.py]. Add retry logic and sleep between calls regardless.

3. **Security?** Public data, no PII, no auth required for read access. No exposure risk. Keep any API keys (if ODP requires them) in env vars, never in the repo.

4. **Breaks?** The migration itself is the break risk. The old endpoint dies April 20. If we use the new ODP and USPTO changes the schema again, collect.py breaks silently. Mitigation: validate response shape on first call, fail loudly if unexpected fields.

5. **Simpler?** PatentsView has some PTAB linkage data, and Google Patents Public Data on BigQuery has PTAB outcomes. BigQuery is faster to query but requires a Google account and has egress costs. The new ODP is the most direct and free. Correct choice.

6. **Perfect?** A real-time PTAB feed with webhooks that pushes new proceedings to a database as they are filed. USPTO does not offer this. The ODP is the closest available option.

---

**RunPod GPU (A40 48GB)**

1. **Current?** A40 instances confirmed available on RunPod as of April 2026. Pricing not confirmed from live page (JavaScript-rendered). [UNVERIFIED -- check runpod.io/pricing before starting eval run.] Community Cloud vs Secure Cloud pricing differs. Use Community Cloud for cost.

2. **Math?** Eval: 30 decisions x 5 models x ~3k tokens per decision = ~450k tokens input. At 70B model inference speed (~500 tokens/sec on A40), roughly 15 minutes of inference. At estimated $0.40-0.79/hr for A40 community cloud = under $1 for eval. Full RAG: 500 decisions x ~8k tokens = 4M tokens input. Estimate 2-3 hours of inference. Under $2 total. [UNVERIFIED on exact A40 pricing -- confirm before committing.]

3. **Security?** RunPod instances are ephemeral. No PTAB data is sensitive (all public). Do not store API keys on the RunPod instance -- pass via environment variable at runtime. Shut down instance immediately after export.

4. **Breaks?** A40 availability is not guaranteed on Community Cloud (spot-like availability). If unavailable: use A100 PCIe (80GB, more expensive but handles 70B without quantization) or fall back to local Ollama with a smaller model for eval.

5. **Simpler?** Could run eval on local Ollama with 8B models. Faster to set up, zero cost, but 8B models will meaningfully underperform on legal text. The quality difference justifies the $1-5 RunPod cost. RunPod is the right call.

6. **Perfect?** A dedicated GPU server with all models pre-loaded, running continuously, accessible via API. Zero setup per run. That is what a production ML platform looks like. For a one-time analysis, RunPod is 95% of the way there.

---

**vLLM (model serving on RunPod)**

1. **Current?** vLLM is actively developed as of April 2026. Version 0.4.x branch. [UNVERIFIED on exact current version -- check pypi.org/project/vllm before pinning in requirements.txt.]

2. **Math?** vLLM handles 70B models with 4-bit quantization (AWQ or GPTQ) on a single A40 48GB. Throughput ~3-5x faster than Ollama for batch inference. Correct for this use case.

3. **Security?** vLLM exposes an OpenAI-compatible API endpoint. Do not expose the RunPod port publicly. Use internal localhost calls only. RunPod's network isolation handles this by default.

4. **Breaks?** vLLM has had breaking API changes between minor versions. Pin the version in requirements.txt. If a model is not supported in the pinned version, check the vLLM model compatibility list before upgrading.

5. **Simpler?** Ollama is easier to set up but slower for batch inference. For the eval (30 docs) Ollama is fine. For the full 500-doc RAG run, vLLM is meaningfully faster and worth the setup. Use Ollama for local testing, vLLM on RunPod for production runs.

6. **Perfect?** A unified inference API that serves any open model with automatic batching, quantization selection, and cost tracking. vLLM is close. The missing piece is automatic cost tracking per run.

---

**sentence-transformers + numpy (RAG, Phase 1 — primary)**

1. **Current?** sentence-transformers is actively maintained by Hugging Face. all-MiniLM-L6-v2 is a stable, widely-used embedding model. numpy is stable. No version risk for either.

2. **Math?** 500 documents, chunked at ~512 tokens = ~4,000 chunks. numpy cosine similarity over 4,000 chunks: sub-second on CPU. Embedding 4,000 chunks with all-MiniLM-L6-v2 on CPU: ~2-3 minutes. Well within budget.

3. **Security?** All local. No external API calls. No data leaves the RunPod instance.

4. **Breaks?** Essentially nothing. sentence-transformers and numpy have stable APIs. The only break risk is if the chosen embedding model is deprecated — use a top-downloaded model from the Hugging Face hub, not an experimental one.

5. **Simpler?** This IS the simpler option. Correct choice for Phase 1.

6. **Perfect?** Phase 1 is close to perfect for a one-time 500-document analysis. If retrieval quality checks fail the 90% threshold, the Phase 2 upgrade path is ready.

---

**LlamaIndex + ChromaDB (RAG framework — Phase 2 only, conditional)**

*Not used unless Phase 1 RAG accuracy checks fail the 90% threshold. Validated here so the upgrade path is ready if needed.*

1. **Current?** LlamaIndex actively maintained, post-1.0 rewrite (llama-index-core package). ChromaDB actively maintained. [Both UNVERIFIED on exact versions -- check PyPI on upgrade day, not build day.]

2. **Math?** 4,000 chunks x 768-dimension embeddings = ~23MB of vector data. Trivially small. In-memory ChromaDB is fine.

3. **Security?** All local. No data leaves the instance.

4. **Breaks?** LlamaIndex had breaking changes between 0.x and 1.x. ChromaDB changed client/server split in 0.4.x. Pin both versions on upgrade day. Use LlamaIndex stable core API (Document, VectorStoreIndex, QueryEngine) only -- no experimental modules.

5. **Simpler?** Phase 1 (sentence-transformers + numpy) is simpler and should be tried first. Only upgrade if measured quality data requires it.

6. **Perfect?** For the scale of this problem, Phase 1 is closer to perfect than Phase 2. LlamaIndex adds complexity that is only justified by a measured retrieval quality gap.

---

**ChromaDB (Phase 2 only -- see LlamaIndex section above)**

*Folded into the LlamaIndex Phase 2 validation entry. Not used in Phase 1.*

---

**Chart.js 4.x + D3.js 7.x (visualization)**

1. **Current?** Chart.js 4.4.x is current and actively maintained. D3.js 7.x is current. Both loaded via CDN with pinned versions to avoid drift. Source: npmjs.com (confirmed).

2. **Math?** 15,000 data points for charts is within browser limits for Chart.js. The D3 network graph with 500+ petitioner/respondent nodes may need force simulation tuning to avoid sluggishness. Cap the network graph at top 200 nodes by default with a "show all" option.

3. **Security?** All client-side rendering. No server. No user data collected. No risk.

4. **Breaks?** CDN availability. Pin exact versions and add a fallback note in the README to download locally if CDN is unavailable. D3 v6 to v7 had breaking changes -- use v7 only, do not mix versions.

5. **Simpler?** For the bar/line charts: Chart.js is correct. For the network graph: D3 is the only practical option for an interactive force-directed graph in a static HTML file. No simpler alternative at this quality level.

6. **Perfect?** A visualization layer that automatically chooses the right chart type for each metric and generates interactive annotations. Observable Plot (from the D3 team) is closer to this. Worth evaluating as an alternative to raw D3 for the network graph.

---

**GitHub Pages (hosting)**

1. **Current?** GitHub Pages is current, free for public repos, and has been stable for years. Source: docs.github.com/pages.

2. **Math?** No file size limits that affect us. The report.html will be under 5MB including embedded data. Well within limits.

3. **Security?** No server, no attack surface. HTTPS by default. No user data stored.

4. **Breaks?** Nothing realistic. GitHub Pages has 99.9%+ uptime. The only risk is if the repo becomes private, which would take the site down.

5. **Simpler?** Correct tool. Zero-maintenance static hosting for a public repo.

6. **Perfect?** Already close to perfect for this use case.

---

### Validation Table Summary

| Component | Current? | Math? | Security? | Breaks? | Simpler? | Sources |
|---|---|---|---|---|---|---|
| PTAB API (ODP) | WARNING: migrate to data.uspto.gov, old endpoint dies April 20 | 50k calls, need rate limit check | Public data, no PII | Schema change risk, add validation | Correct source | USPTO Dev Hub (live, April 13 2026) |
| RunPod A40 | Confirmed available | Under $5 total, verify price first | Ephemeral, no key storage | Spot availability, have A100 fallback | Correct | runpod.io [pricing UNVERIFIED] |
| vLLM | Active, 0.4.x | Handles 70B on A40 with quant | localhost only, no public port | Pin version, check model compat list | Ollama for local testing | [version UNVERIFIED] |
| sentence-transformers + numpy (Phase 1) | Stable, actively maintained | 4k chunks, sub-second on CPU, 2-3 min embed | All local | Minimal -- use top-downloaded HF model | This IS the simple option | huggingface.co/sentence-transformers |
| LlamaIndex + ChromaDB (Phase 2, conditional) | Active -- verify version on upgrade day | Fine for 500 docs | All local | Pin versions on upgrade day only | Phase 2 only if Phase 1 accuracy checks fail | [version UNVERIFIED -- check on upgrade day] |
| Chart.js 4.x + D3 7.x | Current | 15k points fine, cap graph at 200 nodes | Client-side only | Pin CDN versions | Correct tools | npmjs.com |
| GitHub Pages | Current, stable | No limits relevant here | No server surface | None | Correct | docs.github.com |

### Three Things to Verify Before Writing Code

1. **data.uspto.gov PTAB API rate limits and auth** -- check the ODP docs at data.uspto.gov before writing collect.py. The old endpoint dies in 7 days.
2. **RunPod A40 community cloud price** -- confirm at runpod.io before budgeting the eval run.
3. **Pin vLLM version** by checking PyPI on build day. sentence-transformers and numpy are stable -- no pinning urgency. LlamaIndex and ChromaDB: only pin if Phase 1 accuracy checks fail and Phase 2 upgrade is triggered.

### Utopian Vision: GitHub Repo

The Wikipedia of PTAB analytics. A community-maintained, fully transparent, citable open-source resource that any attorney, researcher, or developer can use without a credit card or a login. Every metric is documented with its methodology. Every data file is downloadable. The canonical entity resolution files are crowdsourced and improving continuously through pull requests. A law professor can cite it in a paper. A solo practitioner can pull up the APJ profile page before a hearing. A data scientist can fork the repo and extend it for their research. It is the reference, not the product. Nobody owns it. Everyone uses it.

Features that belong here and nowhere else: historical institution rates, APJ panel analytics, petitioner and respondent patterns, law firm and lead counsel stats (if available from the API), export to memo, open data files in CSV and JSON, full methodology documentation, community-maintained name resolution.

What it deliberately does not do: real-time anything, individual patent monitoring, alerts, expert witness tracking, outcome prediction, custom watchlists.

### Utopian Vision: Patent Signals

The operating system for IP intelligence. An attorney opens Patent Signals on Monday morning and already knows: which of their clients' patents were challenged over the weekend, which new filings appeared in their tech areas, and which APJ was just assigned to a case they care about. The alerts are specific to their portfolio, not a firehose of everything. The expert witness module tells them whether Dr. Smith's testimony has been credited or discredited by this particular panel before. The custom report feature packages the relevant data into a client memo format with one click. A law firm buys seats for the whole IP group. In-house counsel at a mid-size tech company uses it to monitor competitors. Startup founders use it to watch for challenges to their core patents.

Features that belong here and nowhere else: real-time new filing alerts, individual patent and portfolio monitoring, custom watchlists by tech area or assignee, expert witness track records from RAG on petition PDFs, RPI mapping (named petitioner to ultimate funder), APJ assignment alerts, outcome probability scoring, firm-level dashboards, custom report generation.

What it deliberately does not do: expose everything for free. The GitHub repo earns the trust. Patent Signals earns the revenue.

### Validation Score: 7/10

Docked 2 points for the PTAB API endpoint migration risk (old endpoint shutting down 7 days from today -- must fix before coding) and 1 point for unverified rate limits on the new ODP. Everything else is solid. Fix the endpoint issue first.

---

## Connection to Patent Signals

Every page of the web report links to Patent Signals with one line:

*"Want live alerts when new IPR petitions are filed in your technology area? Patent Signals monitors PTAB in real time."*

This is the conversion path. The free tool earns the attention. Patent Signals earns the revenue.

---

## Phase 2 Parking Lot

These features are confirmed valuable but do not belong in the initial build. They are parked here so they do not creep into Steps 1-5.

| Feature | Why it's valuable | Why it's Phase 2 | Where it lives |
|---|---|---|---|
| Expert witness track records | Rivals Lex Machina. Attorneys can't research this today. | Requires RAG on petition PDFs and declaration documents. Full separate build. | Patent Signals (paid) |
| Law firm / lead counsel analytics | Competitive intelligence on opposing counsel. High attorney demand. | Only add if lead counsel is in the API metadata. If it requires PDF parsing, it's Phase 2. | GitHub repo if free, Patent Signals if paid |
| RPI mapping (real party in interest) | Named petitioner is often a shell. Real funder is what attorneys care about. | Requires cross-referencing petition PDFs or a separate RPI database. | Patent Signals (paid) |
| Outcome prediction scoring | "Given this panel and tech area, what's my institution probability?" | Requires ML modeling on the full dataset. | Patent Signals (paid) |
| APJ assignment alerts | Know the moment an APJ is assigned to a case you're watching. | Real-time, requires monitoring infrastructure. | Patent Signals (paid) |
| Firm-level dashboards | Law firms want to see all their cases in one view. | Multi-user, auth, firm accounts. Full product build. | Patent Signals (paid) |

**Rule:** nothing from this list enters the build until Steps 1-5 are live and published.

---

## Adjustments from Legal Feedback (no build delay)

These go into the current plan. None of them delay the initial launch.

**Module 1 adjustments:**
- Add a methodology note in the UI explaining exactly how "Institution Rate" is calculated. **Decision (resolved):** partial institutions pre-SAS Institute (2018) are flagged as a third outcome category, `"partial"`, not counted as either instituted or denied. In analyze.py: `OUTCOMES = ["instituted", "denied", "partial"]`. In report.html: add a UI toggle so users can choose how partial institutions factor into rates ("Count as Instituted" / "Count as Denied" / "Show as Separate Category"). Document this decision verbatim in the README methodology section so attorneys reviewing the data understand the pre-2018 treatment.
- Add a prominent caveat on the petitioner data: "Petitioner names reflect the named party in the proceedings. They do not necessarily reflect the ultimate funder or real party in interest."
- Check the new ODP API schema for lead counsel / attorney of record fields. If present in the API, add law firm analytics to Module 1. If not, park it in Phase 2.

**Module 2 adjustments:**
- Add a client-side PDF export button using jsPDF. Attorneys need to package data into client memos. If they have to screenshot, they will not use the tool. This is a 4-hour addition to Module 2, not a separate phase.
- Add a "Copy table as CSV" button for the filterable data tables. Excel is still the attorney's terminal.
- Use Alpine.js for cross-filter state management instead of vanilla JS. Prevents spaghetti when filtering APJ + Year + Tech Area simultaneously across Chart.js and D3 instances.

**Module 3 adjustments:**
- Update all eval prompts to require the model to output the case number, patent number, and a direct quote from the decision alongside every legal summary. No citation, no inclusion in the findings report.
- Add a disclaimer on every page of the findings doc: "AI-assisted analysis. Not legal advice. Verify all findings against original PTAB decisions before use in strategy or filings."

---

## Risks and How to Handle Them

### Risk 1: Vanilla JS cross-filtering becomes spaghetti

Filtering APJ + Year + Tech Area simultaneously across Chart.js and D3 instances in pure Vanilla JS will get messy. A single filter change needs to update 4-5 charts and the network graph in sync.

**Fix:** Use Alpine.js for state management. No build step, no React, just a 15KB script tag. Declare filter state in one place, all charts react to it. Keeps the file self-contained and avoids the mess.

### Risk 2: Data cleaning will take 80% of Module 1 time

Pulling the PTAB data takes 3-5 minutes. Cleaning it will take days. Specific problems:
- Entity resolution: "Apple Inc.", "Apple, Inc", "APPLE COMPUTER INC" all need to resolve to Apple
- CPC to plain-English mapping: CPC class H04W is not "IoT" to a non-specialist
- APJ name normalization: middle initials, name changes, retired judges

**Fix:** Scope this explicitly. Module 1 includes a `canonical-names.json` file for entity resolution and a `cpc-categories.json` file mapping CPC classes to plain-English tech areas. Publish both files as part of the repo. This is where community contributions will come in (see Opportunities below). Time estimate for Module 1 is 2-3 days, not hours.

### Risk 3: Data stagnation

An April 2026 snapshot is useful now. By October 2026 attorneys will hesitate to rely on it. Value decays with time.

**Fix:** The "Run It Again" model (see Opportunities). Quarterly refresh is the right cadence. Each refresh is a content event, not a maintenance burden.

### Risk 4: Value cannibalization -- free tool is too good

If the free tool gives attorneys all the historical APJ and tech area stats they need for pre-filing strategy, they may not feel enough pain to upgrade to Patent Signals. Especially attorneys who file IPRs infrequently.

**Fix:** Frame the distinction clearly everywhere: free tool = historical snapshot, Patent Signals = real-time alerts on new filings. The use cases are different. Historical stats help you decide whether to file. Real-time monitoring tells you when someone files against your client's portfolio. Different enough if communicated correctly.

### Risk 5: Hallucination liability

The RAG analysis of 500 decisions will contain errors. An attorney who spots a misinterpretation of claim language in the public report may dismiss Patent Signals as unreliable.

**Fix:** Two things. First, add a prominent disclaimer on every page: "AI-assisted analysis. Not legal advice. Verify all findings against original PTAB decisions before use." Second, publish the model eval methodology and scores in the repo so readers can see you tested for this. Transparency about the methodology is better protection than hiding it.

---

## Opportunities Beyond the Initial Build

### The "Run It Again" Model (best near-term business move)

Do not build a live dashboard. Instead, run the data collection script once per quarter, update the data files, push to GitHub, and use "Q3 2026 PTAB Data Update" as an excuse to:
- Email the list with new findings
- Post on LinkedIn: "Six months of new PTAB data shows [specific insight]"
- Add a Patent Signals CTA in every refresh email

Each quarterly refresh is a content event that drives list engagement, not a maintenance burden. The static architecture makes this trivial: update data.json, push, done.

### High-Ticket Custom Reports ($5k-$10k)

Law firm partners who find this tool will not all want a $99/month subscription. Some will want Adam to run this exact methodology on their specific portfolio or their biggest competitor's portfolio.

"I'll run a custom PTAB landscape analysis on your client's tech area, using the same methodology as the public tool, delivered as a PDF report with an advisory call." That is a $5k-$10k engagement using code we already built. Add this as a service on patentsignals.com explicitly.

### Community Data Cleaning

Publish `canonical-names.json` (entity resolution) and `cpc-categories.json` (CPC to plain-English) as open files in the repo. Data scientists and researchers will submit pull requests to improve them. This is the hardest part of the project and the open-source community will help for free, enriching the dataset without any additional effort from Adam.

Add a "Contributing" section to the README that explicitly calls this out: "The most valuable contributions are corrections to canonical-names.json and additions to cpc-categories.json."

---

## Measurement Plan

One clear metric per layer. Measured before publishing, after publishing, and at every quarterly refresh.

### Data Quality (before publishing anything)

| Check | Method | Pass threshold |
|---|---|---|
| Institution rate accuracy | Manually verify 20 known PTAB outcomes against our calculated rates | 95%+ match |
| Entity resolution spot check | Pull 50 random petitioner names, verify canonical mapping is correct | 90%+ correct |
| CPC category spot check | Pull 30 random patents, verify plain-English tech area assignment is correct | 90%+ correct |
| APJ name normalization | Verify all APJ names resolve to a single canonical form across all proceedings | 100% (zero duplicates) |
| Partial institution handling | Verify pre-2018 partial institutions are flagged consistently, not treated as binary | Manual review of 10 cases |

Do not publish until all five pass. Log the results in `memory/data-quality-log.md`.

### RAG Accuracy (before publishing findings)

| Check | Method | Pass threshold |
|---|---|---|
| Citation accuracy | For every finding, verify the cited case number exists and the quote appears verbatim in that decision | 100% of cited cases must be real |
| Argument accuracy | Randomly select 10 findings. Read the original decision. Confirm the RAG summary is factually correct. | 90%+ accurate |
| Hallucination scan | Flag any finding that makes a claim not supported by a cited case | Zero tolerance |
| Coverage check | Verify findings cover all 3 tech areas and all 3 outcome types from the eval sample | Must be balanced |

Adam reviews a sample personally before publishing. One attorney-visible error damages Patent Signals credibility. Do not skip this.

### Tool Usage (after publishing)

| Metric | Tool | Cadence |
|---|---|---|
| Monthly unique visitors to patentsignals.com/ptab | Plausible Analytics (free tier, one script tag, privacy-friendly) | Monthly |
| GitHub stars and forks | GitHub Insights | Monthly |
| PR submissions to canonical-names.json | GitHub Insights | Monthly |
| Time on page and chart interactions | Plausible custom events | Monthly |

### Funnel Metrics

| Metric | Tool | Target |
|---|---|---|
| Email capture rate on findings gate | ConvertKit or Mailchimp | 20%+ of visitors |
| Email open rate on 3-email sequence | ConvertKit | 40%+ open rate |
| Click-through to Patent Signals from emails | UTM parameters | 15%+ CTR on email 3 |
| Patent Signals conversions traceable to tool | UTM: `?utm_source=ptab-tool` on all Patent Signals links | Track every conversion |

### Refresh Trigger

Time-based. Every 90 days, run the full collection and analysis pipeline. Use the quarterly refresh as a content event: email the list, post on LinkedIn, update the GitHub repo with a dated release tag. Do not wait for a filing threshold. Consistency matters more than perfect timing.

---

## Local Memory and Self-Learning System

**Architecture principle:** the local memory system is private. It never gets pushed to GitHub. It is the system that makes each quarterly refresh smarter than the last. The public GitHub repo gets clean outputs. The local machine keeps the learning.

### What Lives Locally (never pushed)

```
memory/                        # in .gitignore
  run-history.json             # metadata for every run: date, model, score, findings count
  prompt-history.md            # which prompts worked, which didn't, and why
  model-eval-results.json      # full eval scores for all models tested
  correction-log.md            # manual corrections to RAG output after each run
  chunk-performance.json       # which document chunks were retrieved most often
  data-quality-log.md          # spot check results from each data validation pass
  entity-corrections.json      # corrections to canonical names before PR submission

logs/                          # in .gitignore
  collect-YYYY-MM-DD.log       # API call logs, errors, retry counts
  rag-YYYY-MM-DD.log           # model inference logs, confidence scores, retrieval stats
  quality-YYYY-MM-DD.log       # data quality check results

data/raw/                      # in .gitignore
  proceedings-raw.json         # unprocessed API response
  decisions-raw.json           # unprocessed decision data
  decision_text/               # raw PDF text extractions
```

### What Gets Published to GitHub

```
data/
  canonical-names.json         # entity resolution (community maintains this)
  cpc-categories.json          # CPC to plain-English mapping (community maintains this)
output/
  data.json                    # clean processed data for the web report
  findings.md                  # RAG qualitative analysis
  report.html                  # interactive web report
```

### The Self-Learning Loop

After every quarterly run, before closing the instance:

**Step 1: Log what the model did**
Save retrieval stats to `memory/chunk-performance.json`. Which chunks were pulled most often? Which queries returned low-confidence results? Low confidence on a query means either the chunk size is wrong, the query is ambiguous, or the model needs a better prompt. Log the diagnosis.

**Step 2: Log manual corrections**
Every correction made during the RAG accuracy check goes into `memory/correction-log.md` with: what the model said, what the correct answer was, and which prompt generated the error. This is training data for the next run's prompt improvements.

**Step 3: Update prompt templates**
Before the next run, review `memory/prompt-history.md` and `correction-log.md`. Update the standardized eval prompts and RAG query templates based on what failed. The prompts improve every quarter without touching the published methodology.

**Step 4: Update canonical names**
Any entity resolution corrections discovered during the run go into `memory/entity-corrections.json` first. After reviewing for accuracy, submit the verified corrections as a PR to the public `canonical-names.json`. Local corrections stay local until confirmed.

**Step 5: Tag the release**
After publishing, create a dated GitHub release tag: `v2026-Q2`, `v2026-Q3`. Attorneys and researchers can reference a specific snapshot. The tag also serves as the "update" email hook.

### What This Produces Over Time

Each quarterly run produces better outputs than the last because:
- Prompts improve based on logged corrections
- Entity resolution improves based on community PRs
- Chunk sizes and retrieval parameters tune based on performance logs
- The model eval may surface a better model than the previous winner

By Q4 2026, the system will have three runs of learning behind it. The findings will be meaningfully more accurate than the first run. The methodology stays the same. The quality improves automatically.

---

## What Success Looks Like

- 50+ GitHub stars in the first month
- At least one attorney or researcher cites the data in a filing or paper
- One LinkedIn post drives 10k+ impressions
- One Patent Signals conversion traceable to the tool
- One custom report inquiry at $5k+ within 90 days
- Adam uses it in at least one advisory conversation
- Quarterly refresh cadence established by Q3 2026

---

## Three-Tier Architecture and Feature Handoff

The whole system is three layers. Each layer serves a different audience and purpose. Features live at the right layer, not the easiest one.

```
Tier 1: Local Memory (private)
        |
        v
Tier 2: GitHub (Wikipedia)
        |
        v
Tier 3: Patent Signals (the OS)
```

---

### Tier 1: Local Memory (private, never pushed)

The machine room. Everything that makes the system smarter over time lives here and nowhere else.

**What it holds:**
- Raw API responses before cleaning (proceedings-raw.json, decisions-raw.json)
- Run history and timing logs
- Model eval scores for all models tested
- RAG correction logs (what the model got wrong, what the right answer was)
- Chunk performance data (which document chunks retrieved most often)
- Draft entity corrections before PR submission
- Prompt history and prompt improvement notes
- Data quality check results for each run

**Who sees it:** Adam only.

**Rule:** Nothing from Tier 1 goes to Tier 2 until it has been manually reviewed and confirmed correct.

---

### Tier 2: GitHub (the Wikipedia layer)

The public reference. Clean, citable, methodology-transparent. Anyone can read it, fork it, cite it, or contribute to it without a login to anything except GitHub.

**What it holds:**
- Cleaned and processed data (data.json, proceedings.json, panels.json)
- Community-maintained entity files (canonical-names.json, cpc-categories.json)
- The interactive web report (report.html, hosted on GitHub Pages)
- The qualitative findings document (findings.md) from RAG analysis
- Full methodology documentation and eval results
- Scripts (collect.py, analyze.py, rag_analysis.py) so anyone can reproduce the work

**Who sees it:** Attorneys, researchers, data scientists, anyone with a browser.

**What it deliberately does not do:** real-time anything. No live data. No user accounts. No alerts. No portfolio-specific features. Everything here is historical and general-purpose.

**Handoff signal to Tier 3:** Any feature that requires live data, a user identity, a specific portfolio, or a recurring action belongs in Patent Signals, not here.

---

### Tier 3: Patent Signals (the OS layer)

The product built on top of the same data infrastructure that powers Tier 2, extended with real-time monitoring, personalization, and premium features.

**What it adds beyond Tier 2:**

| Feature | Why it needs to be in Patent Signals, not GitHub |
|---|---|
| Real-time new filing alerts | Requires monitoring infrastructure running continuously |
| Portfolio-specific monitoring | Requires user accounts and saved patent lists |
| Custom watchlists by tech area or assignee | Requires user identity and persistent state |
| APJ assignment alerts | Real-time, per-user, requires notification infrastructure |
| Expert witness track records | Requires ongoing RAG on new petition PDFs as they are filed |
| RPI mapping (real party in interest) | Requires cross-referencing new filings continuously |
| Outcome probability scoring | Requires ML model + updated dataset each quarter |
| Firm-level dashboards | Multi-user, auth, firm accounts -- full product build |
| Custom report generation (one-click memo) | Requires user context and personalization |

**Who pays for it:** IP attorneys, law firm IP groups, in-house IP counsel at tech companies.

**What it deliberately does not try to replace:** The GitHub Wikipedia layer. Patent Signals never competes with the free tool -- it extends it. If a feature can be free and static, it lives on GitHub. Patent Signals only exists where real-time, personalization, or ongoing monitoring creates value that a static file cannot deliver.

---

### How Data Flows Between Tiers

```
USPTO PTAB API
      |
      v
Tier 1: collect.py pulls raw data, saves locally
      |
      v
Tier 1: analyze.py cleans, normalizes, computes metrics
      |
      v
[Manual quality check: spot checks, entity review, RAG corrections]
      |
      v
Tier 2: Cleaned outputs pushed to GitHub (data.json, findings.md, report.html)
      |
      v
Tier 2: GitHub Pages serves the interactive report
      |
      v
Tier 2: patentsignals.com/ptab embeds the report, adds email gate
      |
      v
Tier 3: Patent Signals monitors for new filings in real time, sends alerts
              (built on the same data foundation, extended with live infrastructure)
```

The quarterly refresh re-runs the top of this flow. Clean outputs replace the previous ones in Tier 2. Tier 3 (Patent Signals) benefits from each refresh without any additional build work.

---

### The Analogy

GitHub is the Wikipedia of PTAB analytics. Open, citable, community-maintained, always free. Patent Signals is the OS that Wikipedia cannot be: personalized, real-time, action-oriented. Wikipedia tells you what happened. The OS tells you what is happening right now and what to do about it.
