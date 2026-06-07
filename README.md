# ApplySignal v1.2

Candidate-side decision support for modern recruitment pipelines.

ApplySignal helps job applicants track opportunities, interpret recruitment-process signals, and decide where to invest energy. It is intentionally framed as a **personal workflow and prioritization utility**, not as a tool for judging or shaming recruiters.

## What it does

- Tracks job opportunities in a local CSV file.
- Scores each opportunity across five dimensions:
  - Signal strength
  - Process clarity
  - Candidate effort cost
  - Reciprocity
  - Overall opportunity score
- Suggests neutral next actions:
  - Invest
  - Monitor
  - Follow up once
  - Low-effort only
  - Deprioritize
  - Archive or low-effort only
- Visualizes the pipeline with cards, tables, and charts.
- Includes demo data for portfolio screenshots.
- Supports CSV export.

## Why this exists

Modern job applications can create asymmetrical friction: candidates may be asked for tailored CVs, cover letters, forms, asynchronous videos, tests, and work samples before receiving clear information about salary, timeline, or next steps.

ApplySignal turns that uncertainty into a calm decision-support process:

> Invest proportionally to the clarity, seriousness, and reciprocity of the opportunity.

## New in v1.2

- Polished dashboard layout.
- Better visual hierarchy and metric cards.
- Priority application cards.
- Demo data loader.
- Cleaner status guide.
- Improved chart layout.
- More constructive product language.
- Better small-data empty state.

## Installation

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Data storage

The app stores data locally in:

```text
data/applications.csv
```

This keeps the MVP simple, transparent, and easy to version or export.

## Product positioning

ApplySignal does not claim that a weak process signal means a company is bad. It simply helps candidates manage uncertainty, reduce wasted effort, and protect attention during a job search.

## Roadmap ideas

- Email/import workflow.
- Job description parser.
- Follow-up reminders.
- Salary benchmark helper.
- LLM-generated opportunity summary.
- Privacy-first local desktop version.
- Streamlit Cloud deployment.
