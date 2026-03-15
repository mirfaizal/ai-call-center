"""
AI Call Center – Streamlit UI

Upload an audio recording or a text/JSON transcript, then view:
  • Full transcript
  • Structured summary (key points, action items, sentiment, tags)
  • Quality score (empathy, professionalism, resolution, communication)
  • Agent highlights and improvement areas
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import streamlit as st

# ── make repo root importable from any working directory ─────────────
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.routing_agent import PipelineResult, RoutingAgent
from agents.intake_agent import CallRecord
from agents.summarization_agent import CallSummary
from agents.quality_score_agent import QualityScores

# ─────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Call Center Analyzer",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

def score_color(score: float) -> str:
    """Return a CSS color based on a 0-10 score."""
    if score >= 8:
        return "#28a745"
    if score >= 6:
        return "#ffc107"
    return "#dc3545"


def score_badge(label: str, score: int | float) -> str:
    color = score_color(float(score))
    return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:12px;font-weight:bold;">{label}: {score}/10</span>'


def render_summary(summary: CallSummary) -> None:
    if not summary or not summary.success:
        st.error(f"Summarization failed: {getattr(summary, 'error', 'Unknown error')}")
        return

    st.subheader("📋 Summary")
    st.write(summary.summary)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Key Points**")
        for point in summary.key_points:
            st.markdown(f"• {point}")

    with col2:
        st.markdown("**Action Items**")
        if summary.action_items:
            for action in summary.action_items:
                st.markdown(f"✅ {action}")
        else:
            st.markdown("_No action items identified._")

    sentiment_colors = {
        "positive": "#28a745",
        "neutral": "#6c757d",
        "negative": "#dc3545",
    }
    sentiment_color = sentiment_colors.get(summary.customer_sentiment.lower(), "#6c757d")

    resolution_colors = {
        "resolved": "#28a745",
        "unresolved": "#dc3545",
        "escalated": "#ffc107",
        "unknown": "#6c757d",
    }
    res_color = resolution_colors.get(summary.resolution_status.lower(), "#6c757d")

    meta_col1, meta_col2 = st.columns(2)
    with meta_col1:
        st.markdown(
            f'**Customer Sentiment:** <span style="color:{sentiment_color};font-weight:bold;">'
            f'{summary.customer_sentiment.capitalize()}</span>',
            unsafe_allow_html=True,
        )
    with meta_col2:
        st.markdown(
            f'**Resolution Status:** <span style="color:{res_color};font-weight:bold;">'
            f'{summary.resolution_status.capitalize()}</span>',
            unsafe_allow_html=True,
        )

    if summary.tags:
        st.markdown("**Tags / Highlights**")
        tag_html = " ".join(
            f'<span style="background:#e9ecef;padding:2px 8px;border-radius:8px;'
            f'margin-right:4px;font-size:0.85em;">{tag}</span>'
            for tag in summary.tags
        )
        st.markdown(tag_html, unsafe_allow_html=True)


def render_quality_scores(scores: QualityScores) -> None:
    if not scores or not scores.success:
        st.error(f"Quality scoring failed: {getattr(scores, 'error', 'Unknown error')}")
        return

    st.subheader("⭐ Quality Scores")

    badges = [
        score_badge("Empathy", scores.empathy_score),
        score_badge("Professionalism", scores.professionalism_score),
        score_badge("Resolution", scores.resolution_score),
        score_badge("Communication", scores.communication_score),
    ]
    st.markdown("  ".join(badges), unsafe_allow_html=True)

    overall_color = score_color(scores.overall_score)
    st.markdown(
        f'<h3 style="color:{overall_color};">Overall Score: {scores.overall_score:.1f} / 10</h3>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Strengths**")
        if scores.strengths:
            for s in scores.strengths:
                st.markdown(f"✅ {s}")
        else:
            st.markdown("_No specific strengths noted._")

    with col2:
        st.markdown("**Areas for Improvement**")
        if scores.improvements:
            for imp in scores.improvements:
                st.markdown(f"⚠️ {imp}")
        else:
            st.markdown("_No improvements suggested._")

    if scores.compliance_flags:
        st.markdown("**⚠️ Compliance Flags**")
        for flag in scores.compliance_flags:
            st.warning(flag)

    tone_colors = {
        "positive": "#28a745",
        "neutral": "#6c757d",
        "negative": "#dc3545",
        "mixed": "#fd7e14",
    }
    tone_color = tone_colors.get(scores.tone_assessment.lower(), "#6c757d")
    st.markdown(
        f'**Tone Assessment:** <span style="color:{tone_color};font-weight:bold;">'
        f'{scores.tone_assessment.capitalize()}</span>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image(
        "https://img.icons8.com/color/96/000000/phone-office.png",
        width=80,
    )
    st.title("AI Call Center")
    st.markdown("---")

    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.environ.get("OPENAI_API_KEY", ""),
        help="Required for summarization and quality scoring.",
    )
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    model_choice = st.selectbox(
        "Primary Model",
        options=["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        index=0,
        help="LLM used for summarization and quality scoring.",
    )

    st.markdown("---")
    st.markdown("### 📁 Sample Transcripts")
    sample_dir = ROOT / "data" / "sample_transcripts"
    sample_files = sorted(sample_dir.glob("*")) if sample_dir.exists() else []

    selected_sample = st.selectbox(
        "Load a sample",
        options=["— none —"] + [f.name for f in sample_files],
    )

    st.markdown("---")
    st.markdown(
        """
        **How to use:**
        1. Enter your OpenAI API key
        2. Upload a file **or** paste a transcript
        3. Click **Analyze Call**
        """
    )


# ─────────────────────────────────────────────────────────────────────
# Main content
# ─────────────────────────────────────────────────────────────────────

st.title("📞 AI Call Center Analyzer")
st.markdown(
    "Automatically extract insights, generate structured summaries, and score "
    "call quality from audio recordings or text transcripts."
)

tab_upload, tab_paste, tab_about = st.tabs(["📤 Upload File", "✏️ Paste Transcript", "ℹ️ About"])

input_data = None
call_id_input = None

# ── Tab 1: File upload ───────────────────────────────────────────────
with tab_upload:
    uploaded_file = st.file_uploader(
        "Upload an audio file or transcript",
        type=["mp3", "wav", "m4a", "ogg", "flac", "webm", "mp4", "txt", "json"],
        help="Max 25 MB for audio files.",
    )

    if selected_sample != "— none —":
        st.info(f"Sample loaded: **{selected_sample}**")

    call_id_upload = st.text_input("Call ID (optional)", key="call_id_upload", value="")

    analyze_upload = st.button("🔍 Analyze Call", key="btn_upload", type="primary")

    if analyze_upload:
        if uploaded_file is not None:
            suffix = Path(uploaded_file.name).suffix
            file_bytes = uploaded_file.read()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            input_data = tmp_path
            call_id_input = call_id_upload or Path(uploaded_file.name).stem
        elif selected_sample != "— none —":
            input_data = str(sample_dir / selected_sample)
            call_id_input = call_id_upload or Path(selected_sample).stem
        else:
            st.warning("Please upload a file or select a sample transcript.")

# ── Tab 2: Paste transcript ──────────────────────────────────────────
with tab_paste:
    pasted_text = st.text_area(
        "Paste your transcript here",
        height=250,
        placeholder="Agent: Hello, thank you for calling…\nCustomer: Hi, I need help with…",
    )
    call_id_paste = st.text_input("Call ID (optional)", key="call_id_paste", value="")
    analyze_paste = st.button("🔍 Analyze Call", key="btn_paste", type="primary")

    if analyze_paste:
        if pasted_text.strip():
            input_data = pasted_text
            call_id_input = call_id_paste or "pasted-transcript"
        else:
            st.warning("Please paste a transcript before analyzing.")

# ── Tab 3: About ─────────────────────────────────────────────────────
with tab_about:
    st.markdown(
        """
        ## AI Call Center Analyzer

        A multi-agent pipeline that converts raw call data into structured insights.

        ### Agents
        | Agent | Responsibility |
        |-------|----------------|
        | **Intake Agent** | Validates input formats and extracts metadata |
        | **Transcription Agent** | Converts audio to text using OpenAI Whisper |
        | **Summarization Agent** | Generates summaries and key points using GPT |
        | **Quality Scoring Agent** | Evaluates tone, professionalism, and resolution |
        | **Routing Agent** | Orchestrates fallback and conditional flow |

        ### Supported Inputs
        - **Audio:** MP3, WAV, M4A, OGG, FLAC, WebM, MP4 (≤ 25 MB)
        - **Transcript:** TXT or JSON files, or pasted text

        ### JSON Transcript Schema
        ```json
        {
          "call_id": "CALL-001",
          "transcript": "Agent: Hello…",
          "metadata": { "agent": "Jane", "date": "2024-01-15" }
        }
        ```
        """
    )

# ─────────────────────────────────────────────────────────────────────
# Run pipeline
# ─────────────────────────────────────────────────────────────────────

if input_data is not None:
    # Track whether input_data is a temp file we should clean up
    _is_temp_file = (
        isinstance(input_data, str)
        and input_data.startswith(tempfile.gettempdir())
    )

    with st.spinner("Running analysis pipeline…"):
        routing_agent = RoutingAgent(
            api_key=api_key or os.environ.get("OPENAI_API_KEY", ""),
            summarization_model=model_choice,
            scoring_model=model_choice,
        )
        result: PipelineResult = routing_agent.run(input_data, call_id=call_id_input)

    # Clean up any temporary upload file
    if _is_temp_file:
        try:
            os.unlink(input_data)
        except OSError:
            pass

    st.markdown("---")

    if result.errors:
        for err in result.errors:
            st.error(err)

    if result.call_record:
        meta = result.call_record.metadata
        if meta:
            with st.expander("📌 Call Metadata", expanded=False):
                meta_cols = st.columns(min(len(meta), 4))
                for i, (k, v) in enumerate(meta.items()):
                    meta_cols[i % len(meta_cols)].metric(k.replace("_", " ").title(), v)

    # Transcript section
    if result.final_transcript:
        with st.expander("📝 Transcript", expanded=False):
            st.text_area(
                "Full Transcript",
                value=result.final_transcript,
                height=300,
                disabled=True,
                label_visibility="collapsed",
            )

    # Summary section
    if result.summary:
        with st.expander("📋 Summary", expanded=True):
            render_summary(result.summary)

    # Quality scores section
    if result.quality_scores:
        with st.expander("⭐ Quality Scores", expanded=True):
            render_quality_scores(result.quality_scores)

    # Raw JSON export
    with st.expander("🔧 Raw JSON Output", expanded=False):
        st.json(result.model_dump())
