# Market Intelligence & Competitor Research

A Python/Streamlit application for product stakeholders researching Google Play competitors. Compare public review evidence, identify recurring pain points, and export an executive workbook.


## Business problem

Store ratings alone hide specific customer frustrations. This tool brings recent review samples, deterministic sentiment, and optional AI hypotheses into one evidence-based workflow.

## Features and architecture

Search → select 2–4 apps → collect 150–300 recent reviews per app → compare → generate optional Gemini insights → download Excel.

- `app.py`: Streamlit workflow and session state.
- `market_engine.py`: discovery, bounded pagination, normalization, sentiment and KPIs.
- `database.py`: SQLite schema, parameterized persistence and retrieval.
- `market_ai.py`: bounded negative evidence and structured Gemini analysis.
- `reporting.py`: in-memory formatted Excel workbook.
- `dashboard.py`: Plotly figures.
- `pipeline.py`: independent app collection and persistence.
- `tests/`: deterministic mocked tests.
- `database/`, `reports/`: ignored runtime outputs; `.gitkeep` preserves directories.

Stack: Python 3.10+, Streamlit, google-play-scraper, pandas, SQLite, Plotly, openpyxl, google-genai and pytest.

## Installation

Run from the repository root. On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

If PowerShell script activation is restricted, use the environment directly:

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m streamlit run app.py
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## Configuration

Scraping, charts, database and reporting work without Gemini. To enable AI, set `GEMINI_API_KEY` in `.env`, the process environment, or `.streamlit/secrets.toml`. Optionally set `GEMINI_MODEL` (default `gemini-3.8-flash`) to an available model in your account. Never commit either secret file.

```toml
GEMINI_API_KEY = "your-key-here"
GEMINI_MODEL = "gemini-3.8-flash"
```

## Use

1. Search an app name, niche or category (for example `food delivery`).
2. Inspect real store matches and choose 2–4 distinct apps.
3. Set the target review count and click Analyze competitors.
4. Inspect KPIs, four charts and low-rating evidence. Warnings identify unavailable or short samples.
5. Generate AI insights explicitly when configured, then download the Excel report.

Search, scraping and AI run only after their respective buttons. Changing selection does not silently change an existing analysis; rerun analysis intentionally. The dashboard identifies the analyzed competitors.

## Database

`database/competitor_intelligence.db` is created at runtime. `apps` stores current metadata; `reviews` stores normalized review evidence with a local primary key, foreign key, external ID and content fingerprint uniqueness. Repeated collections update existing external reviews without duplicating identical content. Stored history is available through `database.load_data`; the dashboard uses only the current run to avoid stale cross-analysis evidence. SQLite is local and is not a multi-user isolation boundary.

## Excel report

The download is generated in memory. Five sheets contain Executive Summary, Competitor Comparison, All Reviews, Negative Reviews, and AI Market Gaps. Headers are frozen and filtered, review text wraps, and percentages use number formatting. Missing AI output is explicitly indicated. The reporting function optionally writes to a caller-supplied path, such as `reports/competitor_report.xlsx`.

## Gemini

The current `google-genai` SDK sends a bounded, deduplicated sample of 1–2 star reviews, grouped across competitors. Output covers recurring problems, requested features, market gaps, recommendations and evidence/confidence. Review content is untrusted evidence, not instructions. AI output is a hypothesis requiring product validation; a complaint alone does not establish feature absence. Public review excerpts are sent to Google only when you request insights. Transient server failures use up to three bounded attempts. If the requested model remains unavailable, the app tries `GEMINI_FALLBACK_MODEL` (default `gemini-3.5-flash-lite`) and displays the model used. Set this variable to an empty string to disable fallback. Authentication and quota failures are reported without automatic model switching. API usage may incur charges. See the official [model catalog](https://ai.google.dev/gemini-api/docs/models) and [structured output guide](https://ai.google.dev/gemini-api/docs/structured-output) when changing the model.

## Testing

```bash
python -m compileall app.py market_engine.py database.py pipeline.py dashboard.py market_ai.py reporting.py tests
python -m pytest
```

Automated tests mock external services. Network availability and actual model access are separate integration checks. To launch a headless server:

```bash
streamlit run app.py --server.headless true
```

## Streamlit Community Cloud deployment

Push this repository to your GitHub account, create an app at Streamlit Community Cloud, select the repository and branch, and set `app.py` as the entry point. Choose Python 3.11 or later and add the optional Gemini variables in Advanced settings → Secrets. Deploy and verify a real search. No deployment URL is provided because deployment requires your account. Runtime SQLite storage on Community Cloud is ephemeral and may be lost on restart/redeploy; download reports for durable records.

## Security and limitations

- No keys, `.env`, Streamlit secrets, generated database or reports belong in source control.
- Reviews can contain personal data: restrict access, minimize retention and review exports before sharing.
- Scraping is bounded and sequential; Google Play changes, regional availability, throttling or network outages may yield fewer reviews or failures. Respect store terms and applicable policies.
- Default search/reviews use US English. Recent samples are not representative market surveys.
- Sentiment follows star ratings, not linguistic interpretation; sarcasm and rating/text disagreement are not resolved.
- No authentication or per-user storage isolation is included. Use a private deployment for sensitive work.
- AI availability depends on credentials, model access, quotas and provider availability.

## Future improvements

Optional locale controls, longitudinal snapshots, validated theme tagging, and explicit data retention controls could extend the focused workflow.
