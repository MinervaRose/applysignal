from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_TITLE = "ApplySignal"
APP_VERSION = "v1.2"
DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "applications.csv"

STATUS_OPTIONS = [
    "Lead",
    "Applied",
    "Promising",
    "Active",
    "Unclear",
    "Low Signal",
    "Paused",
    "Closed",
    "Archived",
]

EFFORT_LEVELS = ["Low", "Medium", "High", "Very high"]
REMOTE_OPTIONS = ["Unknown", "On-site", "Hybrid", "Remote", "Mostly remote"]

BASE_COLUMNS = [
    "created_at",
    "updated_at",
    "company",
    "role",
    "location",
    "source",
    "job_url",
    "date_applied",
    "job_ad_age_days",
    "status",
    "salary_known",
    "salary_monthly_gross",
    "salary_market_fit",
    "remote_policy",
    "role_alignment",
    "portfolio_alignment",
    "clear_next_step",
    "interview_scheduled",
    "named_contact",
    "decision_maker_involved",
    "written_followup",
    "timeline_provided",
    "urgent_claimed",
    "urgency_backed_by_action",
    "cv_read_or_referenced",
    "video_requested_before_call",
    "technical_test_requested",
    "unpaid_work_sample",
    "travel_required",
    "no_response_days",
    "candidate_effort_level",
    "notes",
]

BOOLEAN_FIELDS = [
    "salary_known",
    "clear_next_step",
    "interview_scheduled",
    "named_contact",
    "decision_maker_involved",
    "written_followup",
    "timeline_provided",
    "urgent_claimed",
    "urgency_backed_by_action",
    "cv_read_or_referenced",
    "video_requested_before_call",
    "technical_test_requested",
    "unpaid_work_sample",
    "travel_required",
]

STATUS_HELP = {
    "Lead": "Interesting lead, no application yet.",
    "Applied": "Application sent, waiting for a first signal.",
    "Promising": "Positive contact, but still needs concrete next step.",
    "Active": "Concrete next step scheduled.",
    "Unclear": "Some signal exists, but the process lacks clarity.",
    "Low Signal": "Low evidence of a real active opportunity.",
    "Paused": "Waiting on employer or internal decision.",
    "Closed": "Rejected, withdrawn, expired, or completed.",
    "Archived": "No longer worth active attention.",
}

ACTION_ORDER = [
    "Invest",
    "Monitor",
    "Follow up once",
    "Low-effort only",
    "Deprioritize",
    "Archive or low-effort only",
]


@dataclass
class Scores:
    signal: int
    process_clarity: int
    effort_cost: int
    reciprocity: int
    opportunity: int
    suggested_action: str
    rationale: str


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container {padding-top: 2rem; padding-bottom: 3rem; max-width: 1280px;}
        [data-testid="stSidebar"] {background: #f7f8fb;}
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e9edf3;
            padding: 1rem;
            border-radius: 16px;
            box-shadow: 0 1px 8px rgba(18, 38, 63, 0.04);
        }
        .hero {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 12% 18%, rgba(255, 255, 255, 0.22) 0%, transparent 28%),
                radial-gradient(circle at 84% 22%, rgba(156, 191, 255, 0.26) 0%, transparent 24%),
                linear-gradient(135deg, #101827 0%, #18233a 42%, #263b64 100%);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 28px;
            padding: 2.2rem 2.4rem;
            margin-bottom: 1.35rem;
            box-shadow: 0 24px 60px rgba(16, 24, 39, 0.22);
            color: #ffffff;
        }
        .hero::after {
            content: "";
            position: absolute;
            inset: auto -8% -52% 38%;
            height: 220px;
            transform: rotate(-8deg);
            background: rgba(255, 255, 255, 0.08);
            border-radius: 999px;
        }
        .hero-content {
            position: relative;
            z-index: 1;
            max-width: 980px;
        }
        .hero-kicker {
            margin-bottom: .55rem;
            color: #c9d7ff;
            font-size: .78rem;
            font-weight: 700;
            letter-spacing: .12em;
            text-transform: uppercase;
        }
        .hero h1 {
            margin: 0 0 .55rem 0;
            font-size: clamp(2.2rem, 5vw, 4.25rem);
            line-height: .98;
            letter-spacing: -0.055em;
            color: #ffffff;
        }
        .hero p {
            margin: 0;
            max-width: 760px;
            color: #dbe5ff;
            font-size: 1.08rem;
            line-height: 1.55;
        }
        .hero-grid {
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: .75rem;
            margin-top: 1.4rem;
            max-width: 880px;
        }
        .hero-mini-card {
            background: rgba(255, 255, 255, 0.10);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 18px;
            padding: .85rem 1rem;
            backdrop-filter: blur(8px);
        }
        .hero-mini-card strong {
            display: block;
            margin-bottom: .15rem;
            color: #ffffff;
            font-size: .95rem;
        }
        .hero-mini-card span {
            color: #c9d7ff;
            font-size: .82rem;
        }
        @media (max-width: 900px) {
            .hero {padding: 1.6rem 1.4rem;}
            .hero-grid {grid-template-columns: 1fr;}
        }
        .badge {
            display: inline-block;
            vertical-align: middle;
            padding: .28rem .62rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.12);
            color: #dbe5ff;
            font-weight: 700;
            font-size: .78rem;
            letter-spacing: 0;
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        .app-card {
            background: #ffffff;
            border: 1px solid #e9edf3;
            border-radius: 16px;
            padding: 1rem 1.1rem;
            margin-bottom: .8rem;
            box-shadow: 0 1px 8px rgba(18, 38, 63, 0.04);
        }
        .app-card h4 {margin: 0 0 .25rem 0;}
        .muted {color: #667085; font-size: .9rem;}
        .score-pill {
            display: inline-block;
            margin: .15rem .25rem .15rem 0;
            padding: .25rem .55rem;
            border-radius: 999px;
            background: #f6f7f9;
            border: 1px solid #e8ebef;
            font-size: .82rem;
        }
        .small-note {color: #667085; font-size: .88rem; line-height: 1.45;}
        div[data-testid="stDataFrame"] {border: 1px solid #e9edf3; border-radius: 14px; overflow: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def ensure_data_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        pd.DataFrame(columns=BASE_COLUMNS).to_csv(DATA_FILE, index=False)


def load_data() -> pd.DataFrame:
    ensure_data_file()
    df = pd.read_csv(DATA_FILE)
    for col in BASE_COLUMNS:
        if col not in df.columns:
            df[col] = None
    for field in BOOLEAN_FIELDS:
        if field in df.columns:
            df[field] = df[field].fillna(False).astype(bool)
    numeric_cols = [
        "job_ad_age_days",
        "salary_monthly_gross",
        "salary_market_fit",
        "role_alignment",
        "portfolio_alignment",
        "no_response_days",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df[BASE_COLUMNS]


def save_data(df: pd.DataFrame) -> None:
    ensure_data_file()
    df.to_csv(DATA_FILE, index=False)


def bool_score(value: bool, points: int) -> int:
    return points if bool(value) else 0


def calculate_scores(row: pd.Series) -> Scores:
    role_alignment = int(row.get("role_alignment", 0) or 0)
    portfolio_alignment = int(row.get("portfolio_alignment", 0) or 0)
    salary_market_fit = int(row.get("salary_market_fit", 0) or 0)
    no_response_days = int(row.get("no_response_days", 0) or 0)
    job_ad_age_days = int(row.get("job_ad_age_days", 0) or 0)

    signal = 0
    signal += role_alignment * 4
    signal += portfolio_alignment * 3
    signal += bool_score(row.get("interview_scheduled"), 25)
    signal += bool_score(row.get("clear_next_step"), 15)
    signal += bool_score(row.get("decision_maker_involved"), 15)
    signal += bool_score(row.get("cv_read_or_referenced"), 10)
    signal += bool_score(row.get("urgency_backed_by_action"), 10)
    signal += salary_market_fit * 3

    if job_ad_age_days >= 90:
        signal -= 15
    elif job_ad_age_days >= 60:
        signal -= 10
    elif job_ad_age_days >= 30:
        signal -= 5

    if row.get("urgent_claimed") and not row.get("urgency_backed_by_action"):
        signal -= 15
    if no_response_days >= 10:
        signal -= 20
    elif no_response_days >= 5:
        signal -= 10

    process = 0
    process += bool_score(row.get("clear_next_step"), 20)
    process += bool_score(row.get("interview_scheduled"), 20)
    process += bool_score(row.get("named_contact"), 15)
    process += bool_score(row.get("written_followup"), 15)
    process += bool_score(row.get("timeline_provided"), 15)
    process += bool_score(row.get("salary_known"), 15)
    process = max(0, min(100, process))

    effort_map = {"Low": 15, "Medium": 40, "High": 70, "Very high": 90}
    effort_cost = effort_map.get(str(row.get("candidate_effort_level", "Low")), 15)
    effort_cost += bool_score(row.get("video_requested_before_call"), 15)
    effort_cost += bool_score(row.get("technical_test_requested"), 15)
    effort_cost += bool_score(row.get("unpaid_work_sample"), 25)
    effort_cost += bool_score(row.get("travel_required"), 10)
    effort_cost = max(0, min(100, effort_cost))

    reciprocity = process - int(effort_cost * 0.45)
    if row.get("video_requested_before_call"):
        reciprocity -= 20
    if row.get("unpaid_work_sample") and not row.get("salary_known"):
        reciprocity -= 20
    if row.get("urgent_claimed") and not row.get("urgency_backed_by_action"):
        reciprocity -= 15
    reciprocity = max(0, min(100, reciprocity))

    signal = max(0, min(100, signal))
    opportunity = round(
        (signal * 0.4)
        + (process * 0.25)
        + (reciprocity * 0.2)
        + ((role_alignment + portfolio_alignment) / 20 * 100 * 0.15)
    )
    opportunity = max(0, min(100, opportunity))

    action, rationale = suggest_action(row, signal, process, effort_cost, reciprocity, opportunity)
    return Scores(signal, process, effort_cost, reciprocity, opportunity, action, rationale)


def suggest_action(row: pd.Series, signal: int, process: int, effort: int, reciprocity: int, opportunity: int) -> Tuple[str, str]:
    if str(row.get("status", "")) in {"Closed", "Archived"}:
        return "Archive or low-effort only", "This opportunity is already closed or archived; keep it for records, not active attention."
    if row.get("interview_scheduled") and opportunity >= 60:
        return "Invest", "A concrete next step exists and the opportunity score is strong enough to justify focused attention."
    if row.get("video_requested_before_call") and reciprocity < 45:
        return "Deprioritize", "The process asks for high candidate effort before giving enough reciprocal signal."
    if row.get("unpaid_work_sample") and not row.get("salary_known"):
        return "Deprioritize", "The process requests unpaid work before basic opportunity clarity is established."
    if int(row.get("no_response_days", 0) or 0) >= 5 and not row.get("clear_next_step"):
        return "Follow up once", "There has been enough silence to justify one calm follow-up, but not enough signal to reserve mental space."
    if opportunity >= 70:
        return "Invest", "The opportunity is aligned and the process contains enough concrete signal."
    if opportunity >= 50:
        return "Monitor", "There is some signal, but the process needs more clarity before heavy investment."
    if effort >= 70 and signal < 50:
        return "Archive or low-effort only", "The effort cost is high compared with the evidence that this is an active opportunity."
    return "Low-effort only", "The current signal is too weak for major time investment."


def add_scores(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    scored = df.copy()
    score_rows = [calculate_scores(row) for _, row in scored.iterrows()]
    scored["signal_score"] = [s.signal for s in score_rows]
    scored["process_clarity_score"] = [s.process_clarity for s in score_rows]
    scored["effort_cost"] = [s.effort_cost for s in score_rows]
    scored["reciprocity_score"] = [s.reciprocity for s in score_rows]
    scored["opportunity_score"] = [s.opportunity for s in score_rows]
    scored["suggested_action"] = [s.suggested_action for s in score_rows]
    scored["rationale"] = [s.rationale for s in score_rows]
    return scored


def blank_form_defaults() -> Dict[str, object]:
    return {
        "company": "",
        "role": "",
        "location": "",
        "source": "",
        "job_url": "",
        "date_applied": date.today(),
        "job_ad_age_days": 0,
        "status": "Lead",
        "salary_known": False,
        "salary_monthly_gross": 0,
        "salary_market_fit": 5,
        "remote_policy": "Unknown",
        "role_alignment": 5,
        "portfolio_alignment": 5,
        "clear_next_step": False,
        "interview_scheduled": False,
        "named_contact": False,
        "decision_maker_involved": False,
        "written_followup": False,
        "timeline_provided": False,
        "urgent_claimed": False,
        "urgency_backed_by_action": False,
        "cv_read_or_referenced": False,
        "video_requested_before_call": False,
        "technical_test_requested": False,
        "unpaid_work_sample": False,
        "travel_required": False,
        "no_response_days": 0,
        "candidate_effort_level": "Low",
        "notes": "",
    }


def make_demo_rows() -> pd.DataFrame:
    now = datetime.now().isoformat(timespec="seconds")
    base = {col: None for col in BASE_COLUMNS}
    rows = [
        {
            **base,
            "created_at": now,
            "updated_at": now,
            "company": "NovaRetail Group",
            "role": "AI Engineer",
            "location": "Rennes",
            "source": "LinkedIn",
            "job_url": "",
            "date_applied": date.today().isoformat(),
            "job_ad_age_days": 75,
            "status": "Unclear",
            "salary_known": True,
            "salary_monthly_gross": 3000,
            "salary_market_fit": 3,
            "remote_policy": "On-site",
            "role_alignment": 7,
            "portfolio_alignment": 8,
            "clear_next_step": False,
            "interview_scheduled": False,
            "named_contact": False,
            "decision_maker_involved": True,
            "written_followup": False,
            "timeline_provided": False,
            "urgent_claimed": True,
            "urgency_backed_by_action": False,
            "cv_read_or_referenced": True,
            "video_requested_before_call": False,
            "technical_test_requested": False,
            "unpaid_work_sample": False,
            "travel_required": False,
            "no_response_days": 7,
            "candidate_effort_level": "Medium",
            "notes": "Urgent phone contact, CV reportedly escalated, but no concrete next step after one week.",
        },
        {
            **base,
            "created_at": now,
            "updated_at": now,
            "company": "École Data Campus",
            "role": "Bachelor AI/Data Teaching Lecturer",
            "location": "Remote / Paris",
            "source": "Direct contact",
            "job_url": "",
            "date_applied": date.today().isoformat(),
            "job_ad_age_days": 3,
            "status": "Active",
            "salary_known": True,
            "salary_monthly_gross": 4200,
            "salary_market_fit": 8,
            "remote_policy": "Hybrid",
            "role_alignment": 9,
            "portfolio_alignment": 9,
            "clear_next_step": True,
            "interview_scheduled": True,
            "named_contact": True,
            "decision_maker_involved": True,
            "written_followup": True,
            "timeline_provided": True,
            "urgent_claimed": True,
            "urgency_backed_by_action": True,
            "cv_read_or_referenced": True,
            "video_requested_before_call": False,
            "technical_test_requested": False,
            "unpaid_work_sample": False,
            "travel_required": False,
            "no_response_days": 0,
            "candidate_effort_level": "Medium",
            "notes": "Fast contact, next-morning meeting proposed, clear owner and timeline. Real urgency translated into action.",
        },
        {
            **base,
            "created_at": now,
            "updated_at": now,
            "company": "CloudNova Consulting",
            "role": "Junior AI Consultant",
            "location": "Remote",
            "source": "Welcome to the Jungle",
            "job_url": "",
            "date_applied": date.today().isoformat(),
            "job_ad_age_days": 18,
            "status": "Promising",
            "salary_known": True,
            "salary_monthly_gross": 3800,
            "salary_market_fit": 6,
            "remote_policy": "Mostly remote",
            "role_alignment": 8,
            "portfolio_alignment": 9,
            "clear_next_step": True,
            "interview_scheduled": False,
            "named_contact": True,
            "decision_maker_involved": False,
            "written_followup": True,
            "timeline_provided": True,
            "urgent_claimed": False,
            "urgency_backed_by_action": False,
            "cv_read_or_referenced": True,
            "video_requested_before_call": False,
            "technical_test_requested": True,
            "unpaid_work_sample": False,
            "travel_required": False,
            "no_response_days": 2,
            "candidate_effort_level": "High",
            "notes": "Good fit and clear follow-up, but technical test increases effort cost.",
        },
        {
            **base,
            "created_at": now,
            "updated_at": now,
            "company": "ScaleUp Talent Pool",
            "role": "AI Product Analyst",
            "location": "Unknown",
            "source": "Recruiter outreach",
            "job_url": "",
            "date_applied": date.today().isoformat(),
            "job_ad_age_days": 120,
            "status": "Low Signal",
            "salary_known": False,
            "salary_monthly_gross": 0,
            "salary_market_fit": 2,
            "remote_policy": "Unknown",
            "role_alignment": 6,
            "portfolio_alignment": 7,
            "clear_next_step": False,
            "interview_scheduled": False,
            "named_contact": False,
            "decision_maker_involved": False,
            "written_followup": False,
            "timeline_provided": False,
            "urgent_claimed": False,
            "urgency_backed_by_action": False,
            "cv_read_or_referenced": False,
            "video_requested_before_call": True,
            "technical_test_requested": False,
            "unpaid_work_sample": False,
            "travel_required": False,
            "no_response_days": 10,
            "candidate_effort_level": "High",
            "notes": "Video requested before a human conversation, old ad, unclear salary and timeline.",
        },
    ]
    return pd.DataFrame(rows)[BASE_COLUMNS]


def application_form(defaults: Dict[str, object], submit_label: str):
    with st.form(f"application_form_{submit_label}"):
        st.markdown("#### Opportunity basics")
        col1, col2 = st.columns(2)
        with col1:
            company = st.text_input("Company", value=str(defaults.get("company", "")))
            role = st.text_input("Role", value=str(defaults.get("role", "")))
            location = st.text_input("Location", value=str(defaults.get("location", "")))
            source = st.text_input("Source", value=str(defaults.get("source", "")), placeholder="LinkedIn, WTTJ, direct contact...")
        with col2:
            job_url = st.text_input("Job URL", value=str(defaults.get("job_url", "")))
            date_applied = st.date_input("Date applied", value=pd.to_datetime(defaults.get("date_applied", date.today())).date())
            job_ad_age_days = st.number_input("Approx. job ad age in days", min_value=0, max_value=3650, value=int(defaults.get("job_ad_age_days", 0) or 0))
            current_status = str(defaults.get("status", "Lead"))
            status = st.selectbox("Status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(current_status) if current_status in STATUS_OPTIONS else 0, help="Neutral status used for workflow hygiene, not company judgment.")

        st.markdown("#### Opportunity fit")
        col3, col4 = st.columns(2)
        with col3:
            salary_known = st.checkbox("Salary known", value=bool(defaults.get("salary_known", False)))
            salary_monthly_gross = st.number_input("Monthly gross salary (€)", min_value=0, max_value=30000, value=int(defaults.get("salary_monthly_gross", 0) or 0), step=100)
            remote_policy = st.selectbox("Remote policy", REMOTE_OPTIONS, index=REMOTE_OPTIONS.index(str(defaults.get("remote_policy", "Unknown"))) if str(defaults.get("remote_policy", "Unknown")) in REMOTE_OPTIONS else 0)
        with col4:
            salary_market_fit = st.slider("Salary-market fit", 0, 10, int(defaults.get("salary_market_fit", 5) or 5))
            role_alignment = st.slider("Role alignment", 0, 10, int(defaults.get("role_alignment", 5) or 5))
            portfolio_alignment = st.slider("Portfolio alignment", 0, 10, int(defaults.get("portfolio_alignment", 5) or 5))

        st.markdown("#### Process signals")
        c1, c2 = st.columns(2)
        with c1:
            clear_next_step = st.checkbox("Clear next step", value=bool(defaults.get("clear_next_step", False)))
            interview_scheduled = st.checkbox("Interview scheduled", value=bool(defaults.get("interview_scheduled", False)))
            named_contact = st.checkbox("Named contact", value=bool(defaults.get("named_contact", False)))
            decision_maker_involved = st.checkbox("Decision-maker involved", value=bool(defaults.get("decision_maker_involved", False)))
        with c2:
            written_followup = st.checkbox("Written follow-up received", value=bool(defaults.get("written_followup", False)))
            timeline_provided = st.checkbox("Timeline provided", value=bool(defaults.get("timeline_provided", False)))
            urgent_claimed = st.checkbox("Urgency claimed", value=bool(defaults.get("urgent_claimed", False)))
            urgency_backed_by_action = st.checkbox("Urgency backed by action", value=bool(defaults.get("urgency_backed_by_action", False)))
            cv_read_or_referenced = st.checkbox("CV/portfolio clearly read", value=bool(defaults.get("cv_read_or_referenced", False)))

        st.markdown("#### Candidate effort requested")
        e1, e2 = st.columns(2)
        with e1:
            video_requested_before_call = st.checkbox("Video requested before human call", value=bool(defaults.get("video_requested_before_call", False)))
            technical_test_requested = st.checkbox("Technical test requested", value=bool(defaults.get("technical_test_requested", False)))
            unpaid_work_sample = st.checkbox("Unpaid work sample / case study", value=bool(defaults.get("unpaid_work_sample", False)))
            travel_required = st.checkbox("Travel required", value=bool(defaults.get("travel_required", False)))
        with e2:
            no_response_days = st.number_input("Days since last response", min_value=0, max_value=365, value=int(defaults.get("no_response_days", 0) or 0))
            current_effort = str(defaults.get("candidate_effort_level", "Low"))
            candidate_effort_level = st.selectbox("Overall effort level", EFFORT_LEVELS, index=EFFORT_LEVELS.index(current_effort) if current_effort in EFFORT_LEVELS else 0)

        notes = st.text_area("Notes", value=str(defaults.get("notes", "")), height=120)
        submitted = st.form_submit_button(submit_label, use_container_width=True)

    payload = {
        "company": company.strip(),
        "role": role.strip(),
        "location": location.strip(),
        "source": source.strip(),
        "job_url": job_url.strip(),
        "date_applied": date_applied.isoformat(),
        "job_ad_age_days": job_ad_age_days,
        "status": status,
        "salary_known": salary_known,
        "salary_monthly_gross": salary_monthly_gross,
        "salary_market_fit": salary_market_fit,
        "remote_policy": remote_policy,
        "role_alignment": role_alignment,
        "portfolio_alignment": portfolio_alignment,
        "clear_next_step": clear_next_step,
        "interview_scheduled": interview_scheduled,
        "named_contact": named_contact,
        "decision_maker_involved": decision_maker_involved,
        "written_followup": written_followup,
        "timeline_provided": timeline_provided,
        "urgent_claimed": urgent_claimed,
        "urgency_backed_by_action": urgency_backed_by_action,
        "cv_read_or_referenced": cv_read_or_referenced,
        "video_requested_before_call": video_requested_before_call,
        "technical_test_requested": technical_test_requested,
        "unpaid_work_sample": unpaid_work_sample,
        "travel_required": travel_required,
        "no_response_days": no_response_days,
        "candidate_effort_level": candidate_effort_level,
        "notes": notes.strip(),
    }
    return submitted, payload


def status_badge(status: str) -> str:
    return f'<span class="badge">{status}</span>'


def render_card(row: pd.Series) -> None:
    st.markdown(
        f"""
        <div class="app-card">
            <h4>{row['company']} — {row['role']}</h4>
            <div class="muted">{row.get('location','')} · {row.get('source','')} · {status_badge(str(row['status']))}</div>
            <div style="margin-top:.55rem;">
                <span class="score-pill">Opportunity {int(row['opportunity_score'])}/100</span>
                <span class="score-pill">Signal {int(row['signal_score'])}/100</span>
                <span class="score-pill">Clarity {int(row['process_clarity_score'])}/100</span>
                <span class="score-pill">Effort {int(row['effort_cost'])}/100</span>
                <span class="score-pill">Reciprocity {int(row['reciprocity_score'])}/100</span>
            </div>
            <p class="small-note"><strong>Recommended action:</strong> {row['suggested_action']} — {row['rationale']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.info("No applications yet. Add your first opportunity in the sidebar, or load demo data to preview the dashboard.")
    st.markdown(
        """
        **What this dashboard will show once you add data:**

        - which opportunities deserve attention;
        - which ones need one calm follow-up;
        - where effort cost is too high for the signal received;
        - how your pipeline looks by status, action, and score.
        """
    )


def render_pipeline_cards(scored: pd.DataFrame) -> None:
    top = scored.sort_values(["opportunity_score", "signal_score"], ascending=False).head(5)
    st.subheader("Priority cards")
    for _, row in top.iterrows():
        render_card(row)


def render_dashboard(scored: pd.DataFrame) -> None:
    st.header("Pipeline overview")
    if scored.empty:
        render_empty_state()
        return

    avg_opp = scored["opportunity_score"].mean()
    avg_signal = scored["signal_score"].mean()
    avg_recip = scored["reciprocity_score"].mean()
    high_effort = int((scored["effort_cost"] >= 70).sum())
    followups = int((scored["suggested_action"] == "Follow up once").sum())

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Applications", len(scored))
    col2.metric("Avg. opportunity", f"{avg_opp:.0f}/100")
    col3.metric("Avg. signal", f"{avg_signal:.0f}/100")
    col4.metric("Avg. reciprocity", f"{avg_recip:.0f}/100")
    col5.metric("Follow-ups due", followups, help="Applications where one calm follow-up is suggested.")

    if high_effort:
        st.warning(f"{high_effort} application(s) currently require high effort. Check whether reciprocal process signal is strong enough.")

    render_pipeline_cards(scored)

    st.subheader("Pipeline table")
    display_cols = [
        "company",
        "role",
        "status",
        "suggested_action",
        "opportunity_score",
        "signal_score",
        "process_clarity_score",
        "effort_cost",
        "reciprocity_score",
        "no_response_days",
    ]
    table = scored[display_cols].sort_values("opportunity_score", ascending=False)
    st.dataframe(table, use_container_width=True, hide_index=True)

    st.subheader("Charts")
    if len(scored) == 1:
        st.caption("Charts become more meaningful with several opportunities. Add more rows or load demo data for a richer view.")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        status_counts = scored["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig_status = px.bar(status_counts, x="status", y="count", title="Applications by status", height=330)
        fig_status.update_layout(margin=dict(l=10, r=10, t=50, b=20), showlegend=False)
        st.plotly_chart(fig_status, use_container_width=True)
    with chart_col2:
        action_counts = scored["suggested_action"].value_counts().reindex(ACTION_ORDER).dropna().reset_index()
        action_counts.columns = ["action", "count"]
        fig_action = px.bar(action_counts, x="action", y="count", title="Recommended actions", height=330)
        fig_action.update_layout(margin=dict(l=10, r=10, t=50, b=80), showlegend=False)
        st.plotly_chart(fig_action, use_container_width=True)

    chart_col3, chart_col4 = st.columns(2)
    with chart_col3:
        fig_scores = px.bar(
            scored.sort_values("opportunity_score", ascending=True),
            x="opportunity_score",
            y="company",
            orientation="h",
            hover_data=["role", "suggested_action"],
            title="Opportunity score by company",
            height=360,
        )
        fig_scores.update_layout(margin=dict(l=10, r=10, t=50, b=20), yaxis_title="")
        st.plotly_chart(fig_scores, use_container_width=True)
    with chart_col4:
        fig_effort = px.scatter(
            scored,
            x="effort_cost",
            y="signal_score",
            size="opportunity_score",
            color="suggested_action",
            hover_name="company",
            hover_data=["role", "status", "reciprocity_score"],
            title="Effort cost vs signal strength",
            height=360,
        )
        fig_effort.update_layout(margin=dict(l=10, r=10, t=50, b=20), legend_title_text="Action")
        st.plotly_chart(fig_effort, use_container_width=True)

    st.subheader("Why these recommendations?")
    for _, row in scored.sort_values("opportunity_score", ascending=False).iterrows():
        with st.expander(f"{row['company']} — {row['role']} · {row['suggested_action']}"):
            st.write(row["rationale"])
            st.write(
                f"Signal: **{row['signal_score']}/100** · Process clarity: **{row['process_clarity_score']}/100** · Effort cost: **{row['effort_cost']}/100** · Reciprocity: **{row['reciprocity_score']}/100**"
            )
            if str(row.get("notes", "")).strip():
                st.write("Notes:")
                st.write(row.get("notes", ""))


def render_status_guide() -> None:
    st.header("Status guide")
    guide_df = pd.DataFrame([{"Status": k, "Meaning": v} for k, v in STATUS_HELP.items()])
    st.dataframe(guide_df, hide_index=True, use_container_width=True)
    st.markdown(
        """
        The vocabulary is intentionally neutral. ApplySignal is not designed to shame recruiters or companies; it helps candidates allocate attention proportionally to the clarity and commitment shown by the process.
        """
    )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon=None, layout="wide")
    inject_css()

    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-content">
                <div class="hero-kicker">Candidate-side recruitment intelligence</div>
                <h1>ApplySignal <span class="badge">{APP_VERSION}</span></h1>
                <p>Turn scattered applications, mixed recruiter signals, and hidden candidate effort into a clear opportunity pipeline. Prioritize serious processes, follow up deliberately, and protect your time.</p>
            </div>
            <div class="hero-grid">
                <div class="hero-mini-card">
                    <strong>Signal strength</strong>
                    <span>Is the opportunity moving?</span>
                </div>
                <div class="hero-mini-card">
                    <strong>Process clarity</strong>
                    <span>Are next steps concrete?</span>
                </div>
                <div class="hero-mini-card">
                    <strong>Effort cost</strong>
                    <span>Is the ask proportionate?</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = load_data()
    scored = add_scores(df)

    with st.sidebar:
        st.header("Add opportunity")
        submitted, payload = application_form(blank_form_defaults(), "Add application")
        if submitted:
            if not payload["company"] or not payload["role"]:
                st.error("Company and role are required.")
            else:
                now = datetime.now().isoformat(timespec="seconds")
                new_row = {**{col: None for col in BASE_COLUMNS}, **payload, "created_at": now, "updated_at": now}
                updated = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(updated)
                st.success("Application added.")
                st.rerun()

        st.divider()
        st.subheader("Demo tools")
        if st.button("Load demo data", use_container_width=True):
            save_data(make_demo_rows())
            st.success("Demo data loaded.")
            st.rerun()
        if st.button("Clear all data", use_container_width=True):
            save_data(pd.DataFrame(columns=BASE_COLUMNS))
            st.success("All data cleared.")
            st.rerun()

    tabs = st.tabs(["Dashboard", "Edit applications", "Export", "Scoring guide", "Status guide"])

    with tabs[0]:
        render_dashboard(scored)

    with tabs[1]:
        st.header("Edit or delete applications")
        if df.empty:
            st.info("No applications to edit yet.")
        else:
            labels = [f"{i}: {row['company']} — {row['role']}" for i, row in df.iterrows()]
            selected_label = st.selectbox("Select application", labels)
            selected_index = int(selected_label.split(":", 1)[0])
            defaults = df.loc[selected_index].to_dict()
            submitted_edit, edited_payload = application_form(defaults, "Save changes")
            col_delete, _ = st.columns([1, 3])
            with col_delete:
                delete_clicked = st.button("Delete selected application", type="secondary", use_container_width=True)
            if submitted_edit:
                edited = df.copy()
                for key, value in edited_payload.items():
                    edited.at[selected_index, key] = value
                edited.at[selected_index, "updated_at"] = datetime.now().isoformat(timespec="seconds")
                save_data(edited)
                st.success("Application updated.")
                st.rerun()
            if delete_clicked:
                edited = df.drop(index=selected_index).reset_index(drop=True)
                save_data(edited)
                st.success("Application deleted.")
                st.rerun()

    with tabs[2]:
        st.header("Export")
        export_df = scored if not scored.empty else df
        st.download_button(
            "Download applications as CSV",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name="applysignal_applications.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.write("Local data file:", f"`{DATA_FILE}`")

    with tabs[3]:
        st.header("Scoring guide")
        st.markdown(
            """
            **Signal Score** estimates how much evidence exists that the opportunity is real, active, aligned, and worth attention.

            **Process Clarity Score** estimates whether the company has provided concrete information: next step, timeline, salary, contact person, written follow-up.

            **Effort Cost** estimates how much work the candidate is being asked to perform: video, test, unpaid work sample, travel, or high customization.

            **Reciprocity Score** compares candidate effort with employer clarity. High effort with low employer signal reduces reciprocity.

            **Opportunity Score** combines signal, clarity, reciprocity, and fit into a practical prioritization score.

            Suggested actions are intentionally neutral: invest, monitor, follow up once, low-effort only, deprioritize, or archive.
            """
        )
        st.code(
            "Opportunity = 40% Signal + 25% Process Clarity + 20% Reciprocity + 15% Fit",
            language="text",
        )

    with tabs[4]:
        render_status_guide()


if __name__ == "__main__":
    main()
