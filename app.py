import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


def _stretched_width_kwargs():
    """Streamlit 1.57+ uses width=; older releases use use_container_width."""
    parts = st.__version__.split(".")
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    if (major, minor) >= (1, 57):
        return {"width": "stretch"}
    return {"use_container_width": True}


# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="RiskLens AI",
    page_icon="https://cdn-icons-png.flaticon.com/512/2716/2716652.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------
# SESSION STATE
# ---------------------------------------------------

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

if "all_risks" not in st.session_state:
    st.session_state.all_risks = []

if "final_summary" not in st.session_state:
    st.session_state.final_summary = ""

if "uploaded_file_names" not in st.session_state:
    st.session_state.uploaded_file_names = []

if "assessment_framework" not in st.session_state:
    st.session_state.assessment_framework = "soc2"

if "framework_label" not in st.session_state:
    st.session_state.framework_label = "SOC 2 Type II"

FRAMEWORK_OPTIONS = {
    "SOC 2 Type II": "soc2",
    "ISO/IEC 27001": "iso27001",
    "General TPRM": "tprm",
}
FRAMEWORK_ID_TO_LABEL = {v: k for k, v in FRAMEWORK_OPTIONS.items()}

# Severity palette — Critical: maroon, High: red
COLOR_SEVERITY_CRITICAL = "#800000"
COLOR_SEVERITY_HIGH = "#E53935"
COLOR_SEVERITY_MEDIUM = "#FFB300"
COLOR_SEVERITY_LOW = "#00E396"
COLOR_SEVERITY_CRITICAL_BG = "rgba(128, 0, 0, 0.15)"
COLOR_SEVERITY_CRITICAL_BORDER = "rgba(128, 0, 0, 0.35)"
COLOR_SEVERITY_HIGH_BG = "rgba(229, 57, 53, 0.15)"
COLOR_SEVERITY_HIGH_BORDER = "rgba(229, 57, 53, 0.35)"

SEVERITY_COLORS = {
    "Critical": COLOR_SEVERITY_CRITICAL,
    "High": COLOR_SEVERITY_HIGH,
    "Medium": COLOR_SEVERITY_MEDIUM,
    "Low": COLOR_SEVERITY_LOW,
}

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

with st.sidebar:

    st.markdown(
        """
        <div style='padding-top:10px;padding-bottom:20px;display:flex;align-items:center;gap:12px'>
            <img src='https://cdn-icons-png.flaticon.com/512/2716/2716652.png'
                 width='40' style='border-radius:10px'/>
            <div>
                <div style='font-size:22px;font-weight:800;letter-spacing:-0.5px;line-height:1.1'>
                    RiskLens AI
                </div>
                <div style='opacity:0.55;font-size:12px;margin-top:2px;font-weight:500;letter-spacing:0.5px;text-transform:uppercase'>
                    AI-Powered TPRM Platform
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    theme_toggle = st.toggle("Dark Mode", value=True)

    if theme_toggle:
        st.session_state.theme = "dark"
    else:
        st.session_state.theme = "light"

    st.divider()

    st.markdown(
        "<div style='font-size:11px;font-weight:700;letter-spacing:1.5px;opacity:0.4;text-transform:uppercase;margin-bottom:8px'>Navigation</div>",
        unsafe_allow_html=True
    )

    page = st.radio(
        "Main navigation",
        [
            "Upload Evidence",
            "Analysis Dashboard",
            "Reports",
            "Settings"
        ],
        label_visibility="collapsed",
        format_func=lambda x: {
            "Upload Evidence": "📂  Upload Evidence",
            "Analysis Dashboard": "📊  Analysis Dashboard",
            "Reports": "📑  Reports",
            "Settings": "⚙  Settings"
        }[x]
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.analysis_done:
        all_risks_sidebar = st.session_state.all_risks
        critical_s = len([r for r in all_risks_sidebar if r.get("severity") == "Critical"])
        high_s = len([r for r in all_risks_sidebar if r.get("severity") == "High"])
        medium_s = len([r for r in all_risks_sidebar if r.get("severity") == "Medium"])
        low_s = len([r for r in all_risks_sidebar if r.get("severity") == "Low"])

        st.markdown(
            f"""
            <div style='background:rgba(255,255,255,0.04);border-radius:14px;padding:16px;border:1px solid rgba(255,255,255,0.07)'>
                <div style='font-size:11px;font-weight:700;letter-spacing:1.5px;opacity:0.4;text-transform:uppercase;margin-bottom:12px'>Risk Summary</div>
                <div style='display:flex;justify-content:space-between;margin-bottom:8px'>
                    <span style='font-size:13px;opacity:0.7'>Critical</span>
                    <span style='font-size:13px;font-weight:700;color:{COLOR_SEVERITY_CRITICAL};background:{COLOR_SEVERITY_CRITICAL_BG};padding:1px 10px;border-radius:20px'>{critical_s}</span>
                </div>
                <div style='display:flex;justify-content:space-between;margin-bottom:8px'>
                    <span style='font-size:13px;opacity:0.7'>High</span>
                    <span style='font-size:13px;font-weight:700;color:{COLOR_SEVERITY_HIGH};background:{COLOR_SEVERITY_HIGH_BG};padding:1px 10px;border-radius:20px'>{high_s}</span>
                </div>
                <div style='display:flex;justify-content:space-between;margin-bottom:8px'>
                    <span style='font-size:13px;opacity:0.7'>Medium</span>
                    <span style='font-size:13px;font-weight:700;color:#FFB300;background:rgba(255,179,0,0.12);padding:1px 10px;border-radius:20px'>{medium_s}</span>
                </div>
                <div style='display:flex;justify-content:space-between'>
                    <span style='font-size:13px;opacity:0.7'>Low</span>
                    <span style='font-size:13px;font-weight:700;color:#00E396;background:rgba(0,227,150,0.12);padding:1px 10px;border-radius:20px'>{low_s}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ---------------------------------------------------
# THEME COLORS
# ---------------------------------------------------

if st.session_state.theme == "dark":
    BG        = "#0A0D14"
    CARD      = "#111827"
    CARD2     = "#161D2E"
    TEXT      = "#F1F5F9"
    TEXT_MUTED= "rgba(241,245,249,0.45)"
    BORDER    = "rgba(255,255,255,0.07)"
    ACCENT    = "#00FFB2"
    ACCENT2   = "#3B82F6"
    CHART_BG  = "#0A0D14"
else:
    BG        = "#F0F4FF"
    CARD      = "#FFFFFF"
    CARD2     = "#F8FAFF"
    TEXT      = "#0F172A"
    TEXT_MUTED= "rgba(15,23,42,0.5)"
    BORDER    = "rgba(0,0,0,0.07)"
    ACCENT    = "#2563EB"
    ACCENT2   = "#7C3AED"
    CHART_BG  = "#FFFFFF"

# ---------------------------------------------------
# CUSTOM CSS  — Production-Grade SAAS UI
# ---------------------------------------------------

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {{
        font-family: 'DM Sans', sans-serif;
        color: {TEXT};
    }}

    .stApp {{
        background: {BG};
    }}

    /* Animated mesh background */
    .stApp::before {{
        content: '';
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background:
            radial-gradient(ellipse 60% 50% at 80% 10%, rgba(59,130,246,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 40% at 10% 80%, rgba(0,255,178,0.05) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: {"#080B12" if st.session_state.theme == "dark" else "#FFFFFF"};
        border-right: 1px solid {BORDER};
    }}

    section[data-testid="stSidebar"] > div {{
        background: transparent;
    }}

    /* Radio nav styling */
    .stRadio > div {{
        gap: 4px;
    }}

    .stRadio label {{
        padding: 10px 14px !important;
        border-radius: 10px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        background: transparent !important;
        border: 1px solid transparent !important;
    }}

    .stRadio label:hover {{
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid {BORDER} !important;
    }}

    /* Page header */
    .page-header {{
        margin-bottom: 32px;
    }}

    .page-title {{
        font-family: 'Syne', sans-serif;
        font-size: 36px;
        font-weight: 800;
        letter-spacing: -1px;
        line-height: 1.1;
        color: {TEXT};
        margin: 0;
    }}

    .page-subtitle {{
        font-size: 14px;
        color: {TEXT_MUTED};
        margin-top: 6px;
        font-weight: 400;
    }}

    /* Metric Cards */
    .metric-card {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 22px 24px;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}

    .metric-card::before {{
        content: '';
        position: absolute;
        top: 0; right: 0;
        width: 80px; height: 80px;
        border-radius: 0 18px 0 80px;
        opacity: 0.06;
    }}

    .metric-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.2);
    }}

    .metric-label {{
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: {TEXT_MUTED};
        margin-bottom: 10px;
    }}

    .metric-value {{
        font-family: 'Syne', sans-serif;
        font-size: 38px;
        font-weight: 800;
        line-height: 1;
        color: {TEXT};
    }}

    .metric-icon {{
        position: absolute;
        top: 20px;
        right: 20px;
        width: 36px;
        height: 36px;
        opacity: 0.7;
    }}

    /* Glass Cards */
    .glass-card {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 20px;
        padding: 24px;
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }}

    .glass-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 16px 48px rgba(0,0,0,0.25);
        border-color: rgba(0,255,178,0.2);
    }}

    /* Upload Zone */
    .upload-zone {{
        border: 2px dashed {BORDER};
        border-radius: 24px;
        padding: 64px 40px;
        text-align: center;
        background: {CARD};
        transition: border-color 0.2s ease;
    }}

    .upload-zone:hover {{
        border-color: {ACCENT};
    }}

    .upload-zone-icon {{
        width: 64px;
        height: 64px;
        margin: 0 auto 20px;
        opacity: 0.6;
    }}

    .upload-zone-title {{
        font-family: 'Syne', sans-serif;
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 8px;
        color: {TEXT};
    }}

    .upload-zone-sub {{
        font-size: 14px;
        color: {TEXT_MUTED};
        max-width: 400px;
        margin: 0 auto;
        line-height: 1.6;
    }}

    /* File Cards */
    .file-card {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 20px;
        transition: all 0.2s ease;
    }}

    .file-card:hover {{
        border-color: {ACCENT};
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }}

    .file-name {{
        font-size: 14px;
        font-weight: 600;
        color: {TEXT};
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-bottom: 4px;
    }}

    .file-meta {{
        font-size: 12px;
        color: {TEXT_MUTED};
    }}

    /* Severity Badges */
    .badge-critical {{
        display: inline-block;
        background: {COLOR_SEVERITY_CRITICAL_BG};
        color: {COLOR_SEVERITY_CRITICAL};
        border: 1px solid {COLOR_SEVERITY_CRITICAL_BORDER};
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }}

    .badge-high {{
        display: inline-block;
        background: {COLOR_SEVERITY_HIGH_BG};
        color: {COLOR_SEVERITY_HIGH};
        border: 1px solid {COLOR_SEVERITY_HIGH_BORDER};
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }}

    .badge-medium {{
        display: inline-block;
        background: rgba(255,179,0,0.15);
        color: #FFB300;
        border: 1px solid rgba(255,179,0,0.3);
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }}

    .badge-low {{
        display: inline-block;
        background: rgba(0,227,150,0.12);
        color: #00E396;
        border: 1px solid rgba(0,227,150,0.25);
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }}

    /* Section Headers */
    .section-header {{
        font-family: 'Syne', sans-serif;
        font-size: 20px;
        font-weight: 700;
        color: {TEXT};
        margin: 28px 0 16px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }}

    /* Report Box */
    .report-box {{
        padding: 28px;
        border-radius: 18px;
        background: {CARD};
        border: 1px solid {BORDER};
        line-height: 1.8;
        font-size: 15px;
        color: {TEXT};
    }}

    /* Risk Table */
    .stDataFrame {{
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 1px solid {BORDER} !important;
    }}

    /* Progress bar */
    .stProgress > div > div {{
        background: linear-gradient(90deg, {ACCENT}, {ACCENT2});
        border-radius: 99px;
    }}

    /* Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, {ACCENT}, {ACCENT2});
        color: {"#000" if st.session_state.theme == "dark" else "#fff"};
        border: none;
        border-radius: 12px;
        font-family: 'DM Sans', sans-serif;
        font-weight: 700;
        font-size: 15px;
        padding: 12px 24px;
        transition: all 0.2s ease;
        letter-spacing: 0.3px;
    }}

    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 8px 24px rgba(0,255,178,0.25);
        opacity: 0.92;
    }}

    /* Divider */
    hr {{
        border-color: {BORDER} !important;
    }}

    /* Expander */
    .stExpander {{
        background: {CARD} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 14px !important;
        margin-bottom: 10px !important;
    }}

    .stExpander summary {{
        font-weight: 600 !important;
        font-size: 14px !important;
    }}

    /* Toggle */
    .stToggle {{
        font-size: 13px !important;
    }}

    /* Selectbox & multiselect */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {{
        background: {CARD} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 10px !important;
        color: {TEXT} !important;
    }}

    /* Download button */
    .stDownloadButton > button {{
        background: {CARD} !important;
        color: {TEXT} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }}

    .stDownloadButton > button:hover {{
        border-color: {ACCENT} !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15) !important;
    }}

    /* Main content padding — pushed down to clear the fixed top navbar */
    .block-container {{
        padding-top: 80px !important;
        padding-bottom: 40px !important;
        max-width: 1400px;
    }}

    /* Scrollbar */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 3px; }}

    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------
# HELPER — render severity badge
# ---------------------------------------------------

def severity_badge(severity: str) -> str:
    cls = {
        "Critical": "badge-critical",
        "High":     "badge-high",
        "Medium":   "badge-medium",
        "Low":      "badge-low"
    }.get(severity, "badge-low")
    return f"<span class='{cls}'>{severity}</span>"


# ---------------------------------------------------
# HELPER — metric card (pure HTML, no nested markdown)
# ---------------------------------------------------

def metric_card(label: str, value: str, icon_url: str, accent: str = "#3B82F6"):
    st.markdown(
        f"""
        <div class='metric-card'>
            <img class='metric-icon' src='{icon_url}'/>
            <div class='metric-label'>{label}</div>
            <div class='metric-value' style='color:{accent}'>{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ---------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------

ICONS = {
    "Upload Evidence":    "https://cdn-icons-png.flaticon.com/512/2965/2965358.png",
    "Analysis Dashboard": "https://cdn-icons-png.flaticon.com/512/2103/2103651.png",
    "Reports":            "https://cdn-icons-png.flaticon.com/512/2991/2991106.png",
    "Settings":           "https://cdn-icons-png.flaticon.com/512/3524/3524659.png",
}

SUBTITLES = {
    "Upload Evidence":    "Upload vendor security evidence for AI-powered analysis",
    "Analysis Dashboard": "Real-time third-party risk intelligence and scoring",
    "Reports":            "Executive summaries, findings & exportable risk reports",
    "Settings":           "Platform configuration and system information",
}

st.markdown(
    f"""
    <div class='page-header'>
        <div class='page-title'>
            <img src='{ICONS[page]}' width='34'
                 style='vertical-align:middle;margin-right:12px;opacity:0.85'/>
            {page}
        </div>
        <div class='page-subtitle'>{SUBTITLES[page]}</div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------
# PAGE: UPLOAD EVIDENCE
# ---------------------------------------------------

if page == "Upload Evidence":

    uploaded_files = st.file_uploader(
        "Upload Security Evidence",
        type=["pdf", "docx", "xlsx"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if not uploaded_files:
        st.markdown(
            f"""
            <div class='upload-zone'>
                <img class='upload-zone-icon'
                     src='https://cdn-icons-png.flaticon.com/512/2965/2965358.png'/>
                <div class='upload-zone-title'>Drop Vendor Security Evidence Here</div>
                <div class='upload-zone-sub'>
                    Upload SOC 2 reports, questionnaires, policies,
                    audit evidence and security documents.
                    Supports <strong>PDF</strong>, <strong>DOCX</strong>, <strong>XLSX</strong>.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<div class='section-header'>"
            f"<img src='https://cdn-icons-png.flaticon.com/512/2965/2965358.png' width='22'/>"
            f"Uploaded Evidence ({len(uploaded_files)} file{'s' if len(uploaded_files) > 1 else ''})"
            f"</div>",
            unsafe_allow_html=True
        )

        type_icons = {
            "application/pdf":  "https://cdn-icons-png.flaticon.com/512/337/337946.png",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                "https://cdn-icons-png.flaticon.com/512/337/337932.png",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                                "https://cdn-icons-png.flaticon.com/512/337/337958.png",
        }

        cols = st.columns(3)
        for idx, uf in enumerate(uploaded_files):
            icon = type_icons.get(uf.type, "https://cdn-icons-png.flaticon.com/512/2965/2965358.png")
            size_kb = uf.size / 1024
            size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
            ext = uf.name.rsplit(".", 1)[-1].upper() if "." in uf.name else "FILE"
            with cols[idx % 3]:
                st.markdown(
                    f"""
                    <div class='file-card'>
                        <div style='display:flex;align-items:center;gap:12px;margin-bottom:10px'>
                            <img src='{icon}' width='32' style='flex-shrink:0'/>
                            <div class='file-name'>{uf.name}</div>
                        </div>
                        <div class='file-meta'>
                            <span style='background:rgba(59,130,246,0.12);color:#3B82F6;border-radius:6px;
                                         padding:2px 8px;font-size:11px;font-weight:700;margin-right:8px'>{ext}</span>
                            {size_str}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        st.markdown(
            f"<div class='section-header'>"
            f"<img src='https://cdn-icons-png.flaticon.com/512/107/107799.png' width='20'/>"
            f"Assessment Framework</div>",
            unsafe_allow_html=True
        )

        framework_keys = list(FRAMEWORK_OPTIONS.keys())
        default_fw_idx = framework_keys.index(
            FRAMEWORK_ID_TO_LABEL.get(
                st.session_state.assessment_framework,
                "SOC 2 Type II",
            )
        )

        selected_framework_label = st.selectbox(
            "Review alignment",
            options=framework_keys,
            index=default_fw_idx,
            help="Choose SOC 2, ISO 27001, or general TPRM lens for AI evidence review.",
            key="framework_select",
        )
        st.session_state.assessment_framework = FRAMEWORK_OPTIONS[selected_framework_label]
        st.session_state.framework_label = selected_framework_label

        st.caption(
            "Analysis uses audit-safe language and maps findings to the selected framework "
            "(Trust Services Criteria for SOC 2, Annex A themes for ISO 27001)."
        )

        st.markdown("<br>", unsafe_allow_html=True)

        analyze_button = st.button(
            "Run AI Risk Analysis",
            **_stretched_width_kwargs(),
        )

        if analyze_button:

            st.session_state.all_risks = []
            st.session_state.final_summary = ""
            st.session_state.uploaded_file_names = []

            progress = st.progress(0)
            status   = st.empty()

            status.info("Extracting security evidence...")
            progress.progress(10)

            total = len(uploaded_files)

            for file_idx, uploaded_file in enumerate(uploaded_files):
                try:
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file,
                            uploaded_file.type
                        )
                    }

                    status.info(f"Analyzing {uploaded_file.name} ({file_idx + 1}/{total})…")

                    response = requests.post(
                        "https://risklens-ai-go8b.onrender.com/analyze",
                        files=files,
                        data={
                            "framework": st.session_state.assessment_framework,
                        },
                    )

                    pct = 20 + int(70 * (file_idx + 1) / total)
                    progress.progress(pct)

                    data = response.json()

                    if "analysis" in data:
                        analysis = data["analysis"]
                        if data.get("framework_label"):
                            st.session_state.framework_label = data["framework_label"]
                        elif analysis.get("framework_label"):
                            st.session_state.framework_label = analysis["framework_label"]
                        st.session_state.final_summary += (
                            analysis.get("summary", "") + "\n"
                        )
                        risks = analysis.get("risks", [])
                        st.session_state.all_risks.extend(risks)
                        st.session_state.uploaded_file_names.append(uploaded_file.name)

                except Exception:
                    st.error(f"Error processing {uploaded_file.name}")

            progress.progress(100)
            status.success("Analysis completed successfully!")
            st.session_state.analysis_done = True
            st.success("Switch to the Analysis Dashboard tab to view results.")

# ---------------------------------------------------
# PAGE: ANALYSIS DASHBOARD
# ---------------------------------------------------

elif page == "Analysis Dashboard":

    if not st.session_state.analysis_done:
        st.markdown(
            f"""
            <div style='text-align:center;padding:80px 20px'>
                <img src='https://cdn-icons-png.flaticon.com/512/6134/6134065.png'
                     width='72' style='opacity:0.4;margin-bottom:16px'/>
                <div style='font-size:20px;font-weight:700;opacity:0.5'>No Analysis Available</div>
                <div style='font-size:14px;opacity:0.35;margin-top:8px'>
                    Upload vendor evidence and run AI analysis first.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        all_risks = st.session_state.all_risks

        critical = len([r for r in all_risks if r.get("severity") == "Critical"])
        high     = len([r for r in all_risks if r.get("severity") == "High"])
        medium   = len([r for r in all_risks if r.get("severity") == "Medium"])
        low      = len([r for r in all_risks if r.get("severity") == "Low"])

        risk_score = critical * 40 + high * 25 + medium * 15 + low * 5

        score_color = (
            COLOR_SEVERITY_CRITICAL if risk_score > 200 else
            COLOR_SEVERITY_HIGH if risk_score > 100 else
            COLOR_SEVERITY_MEDIUM if risk_score > 50 else
            COLOR_SEVERITY_LOW
        )

        # --- KPI Row ---
        st.markdown("<div style='margin-bottom:6px'></div>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            metric_card(
                "Overall Risk Score",
                str(risk_score),
                "https://cdn-icons-png.flaticon.com/512/2716/2716652.png",
                score_color
            )
        with col2:
            metric_card(
                "Risks Identified",
                str(len(all_risks)),
                "https://cdn-icons-png.flaticon.com/512/2103/2103651.png",
                "#3B82F6"
            )
        with col3:
            metric_card(
                "Critical / High",
                str(critical + high),
                "https://cdn-icons-png.flaticon.com/512/564/564619.png",
                COLOR_SEVERITY_CRITICAL
            )
        with col4:
            metric_card(
                "Assessment Time",
                datetime.now().strftime("%H:%M"),
                "https://cdn-icons-png.flaticon.com/512/2784/2784459.png",
                "#A78BFA"
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Filters ---
        st.markdown(
            f"<div class='section-header'>"
            f"<img src='https://cdn-icons-png.flaticon.com/512/107/107799.png' width='20'/>"
            f"Filters</div>",
            unsafe_allow_html=True
        )

        fcol1, fcol2, fcol3 = st.columns([1, 1, 2])

        with fcol1:
            severity_filter = st.multiselect(
                "Severity",
                options=["Critical", "High", "Medium", "Low"],
                default=["Critical", "High", "Medium", "Low"],
                key="sev_filter"
            )

        all_categories = list({r.get("category", "Other") for r in all_risks})
        with fcol2:
            category_filter = st.multiselect(
                "Category",
                options=all_categories,
                default=all_categories,
                key="cat_filter"
            )

        with fcol3:
            search_term = st.text_input(
                "Search risks",
                placeholder="Search by keyword…",
                key="search_filter"
            )

        # Apply filters
        filtered = [
            r for r in all_risks
            if r.get("severity", "Low")    in severity_filter
            and r.get("category", "Other") in category_filter
            and (
                search_term.lower() in r.get("risk", "").lower()
                or search_term.lower() in r.get("category", "").lower()
                or not search_term
            )
        ]

        st.markdown(
            f"<div style='font-size:13px;color:{TEXT_MUTED};margin-bottom:20px'>"
            f"Showing <strong style='color:{TEXT}'>{len(filtered)}</strong> of "
            f"<strong style='color:{TEXT}'>{len(all_risks)}</strong> risks</div>",
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Charts ---
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            severity_df = pd.DataFrame({
                "Severity": ["Critical", "High", "Medium", "Low"],
                "Count":    [critical, high, medium, low]
            })

            fig = go.Figure(data=[go.Pie(
                labels=severity_df["Severity"],
                values=severity_df["Count"],
                hole=0.65,
                marker=dict(
                    colors=[
                        COLOR_SEVERITY_CRITICAL,
                        COLOR_SEVERITY_HIGH,
                        COLOR_SEVERITY_MEDIUM,
                        COLOR_SEVERITY_LOW,
                    ],
                    line=dict(color=CHART_BG, width=3)
                ),
                textfont=dict(family="DM Sans", size=13, color=TEXT),
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>"
            )])

            fig.update_layout(
                title=dict(
                    text="Severity Distribution",
                    font=dict(family="Syne", size=17, color=TEXT),
                    x=0
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor ="rgba(0,0,0,0)",
                font=dict(color=TEXT, family="DM Sans"),
                legend=dict(
                    font=dict(size=13, color=TEXT),
                    bgcolor="rgba(0,0,0,0)"
                ),
                margin=dict(t=50, b=20, l=20, r=20),
                annotations=[dict(
                    text=f"<b>{len(all_risks)}</b><br><span style='font-size:11px'>total</span>",
                    x=0.5, y=0.5,
                    font_size=22,
                    font_color=TEXT,
                    showarrow=False
                )]
            )

            st.plotly_chart(fig, **_stretched_width_kwargs())

        with chart_col2:
            categories = {}
            for r in filtered:
                cat = r.get("category", "Other")
                sev = r.get("severity", "Low")
                if cat not in categories:
                    categories[cat] = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
                categories[cat][sev] = categories[cat].get(sev, 0) + 1

            bar_data = []
            for sev, color in SEVERITY_COLORS.items():
                bar_data.append(go.Bar(
                    name=sev,
                    x=list(categories.keys()),
                    y=[categories[c].get(sev, 0) for c in categories],
                    marker_color=color,
                    marker_line_color=CHART_BG,
                    marker_line_width=2,
                    hovertemplate=f"<b>{sev}</b><br>%{{x}}: %{{y}}<extra></extra>"
                ))

            fig2 = go.Figure(data=bar_data)
            fig2.update_layout(
                title=dict(
                    text="Risk Categories by Severity",
                    font=dict(family="Syne", size=17, color=TEXT),
                    x=0
                ),
                barmode="stack",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor ="rgba(0,0,0,0)",
                font=dict(color=TEXT, family="DM Sans"),
                legend=dict(
                    font=dict(size=12, color=TEXT),
                    bgcolor="rgba(0,0,0,0)",
                    orientation="h",
                    y=-0.15
                ),
                xaxis=dict(
                    showgrid=False,
                    tickfont=dict(size=12),
                    linecolor=BORDER,
                    tickcolor=BORDER
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor=BORDER,
                    tickfont=dict(size=12)
                ),
                margin=dict(t=50, b=20, l=20, r=20),
            )

            st.plotly_chart(fig2, **_stretched_width_kwargs())

        # --- Trend / Score Gauge ---
        gauge_col, tbl_col = st.columns([1, 2])

        with gauge_col:
            fig3 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=risk_score,
                title=dict(
                    text="<b>Risk Score</b>",
                    font=dict(size=15, color=TEXT, family="Syne")
                ),
                number=dict(font=dict(size=40, color=score_color, family="Syne")),
                gauge=dict(
                    axis=dict(
                        range=[0, max(500, risk_score + 50)],
                        tickfont=dict(size=11, color=TEXT),
                        tickcolor=BORDER
                    ),
                    bar=dict(color=score_color, thickness=0.25),
                    bgcolor="rgba(0,0,0,0)",
                    borderwidth=0,
                    steps=[
                        dict(range=[0, 50],   color="rgba(0,227,150,0.1)"),
                        dict(range=[50, 100],  color="rgba(255,179,0,0.1)"),
                        dict(range=[100, 200], color="rgba(229, 57, 53, 0.12)"),
                        dict(range=[200, max(500, risk_score + 50)], color="rgba(128, 0, 0, 0.12)")
                    ],
                    threshold=dict(
                        line=dict(color=score_color, width=3),
                        thickness=0.8,
                        value=risk_score
                    )
                )
            ))
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor ="rgba(0,0,0,0)",
                font=dict(color=TEXT),
                margin=dict(t=30, b=10, l=20, r=20),
                height=260
            )
            st.plotly_chart(fig3, **_stretched_width_kwargs())

        with tbl_col:
            st.markdown(
                f"<div class='section-header' style='margin-top:0'>"
                f"<img src='https://cdn-icons-png.flaticon.com/512/564/564619.png' width='18'/>"
                f"Risk Breakdown</div>",
                unsafe_allow_html=True
            )

            breakdown_html = "<table style='width:100%;border-collapse:collapse;font-size:14px'>"
            breakdown_html += (
                f"<tr style='border-bottom:1px solid {BORDER}'>"
                f"<th style='text-align:left;padding:10px 12px;color:{TEXT_MUTED};font-weight:600;font-size:11px;letter-spacing:1px;text-transform:uppercase'>Severity</th>"
                f"<th style='text-align:right;padding:10px 12px;color:{TEXT_MUTED};font-weight:600;font-size:11px;letter-spacing:1px;text-transform:uppercase'>Count</th>"
                f"<th style='text-align:right;padding:10px 12px;color:{TEXT_MUTED};font-weight:600;font-size:11px;letter-spacing:1px;text-transform:uppercase'>Score Contribution</th>"
                f"</tr>"
            )

            for sev, cnt, weight, color in [
                ("Critical", critical, 40, COLOR_SEVERITY_CRITICAL),
                ("High",     high,     25, COLOR_SEVERITY_HIGH),
                ("Medium",   medium,   15, COLOR_SEVERITY_MEDIUM),
                ("Low",      low,       5, COLOR_SEVERITY_LOW),
            ]:
                breakdown_html += (
                    f"<tr style='border-bottom:1px solid {BORDER}'>"
                    f"<td style='padding:12px'><span class='badge-{sev.lower()}'>{sev}</span></td>"
                    f"<td style='padding:12px;text-align:right;font-weight:700;color:{color};font-size:18px;font-family:Syne'>{cnt}</td>"
                    f"<td style='padding:12px;text-align:right;color:{TEXT_MUTED}'>{cnt * weight}</td>"
                    f"</tr>"
                )

            breakdown_html += "</table>"
            st.markdown(
                f"<div style='background:{CARD};border:1px solid {BORDER};border-radius:16px;overflow:hidden;padding:0'>"
                f"{breakdown_html}"
                f"</div>",
                unsafe_allow_html=True
            )

# ---------------------------------------------------
# PAGE: REPORTS
# ---------------------------------------------------

elif page == "Reports":

    if not st.session_state.analysis_done:
        st.markdown(
            f"""
            <div style='text-align:center;padding:80px 20px'>
                <img src='https://cdn-icons-png.flaticon.com/512/2991/2991106.png'
                     width='72' style='opacity:0.4;margin-bottom:16px'/>
                <div style='font-size:20px;font-weight:700;opacity:0.5'>No Reports Available</div>
                <div style='font-size:14px;opacity:0.35;margin-top:8px'>
                    Run an analysis to generate reports.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        # --- Executive Summary ---
        st.markdown(
            f"<div class='section-header'>"
            f"<img src='https://cdn-icons-png.flaticon.com/512/2991/2991106.png' width='20'/>"
            f"Executive Summary</div>",
            unsafe_allow_html=True
        )

        no_summary_html = "<em style='opacity:0.5'>No summary generated.</em>"
        summary_content = st.session_state.final_summary or no_summary_html
        st.markdown(
            f"<div class='report-box'>{summary_content}</div>",
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # --- Risk Findings Table with color ---
        st.markdown(
            f"<div class='section-header'>"
            f"<img src='https://cdn-icons-png.flaticon.com/512/564/564619.png' width='20'/>"
            f"Risk Findings</div>",
            unsafe_allow_html=True
        )

        if st.session_state.all_risks:
            all_risks = st.session_state.all_risks

            # Filters for report page
            rp_col1, rp_col2 = st.columns([1, 1])
            with rp_col1:
                rp_sev = st.multiselect(
                    "Filter by Severity",
                    ["Critical", "High", "Medium", "Low"],
                    default=["Critical", "High", "Medium", "Low"],
                    key="rp_sev"
                )
            with rp_col2:
                rp_cats = list({r.get("category", "Other") for r in all_risks})
                rp_cat = st.multiselect(
                    "Filter by Category",
                    rp_cats,
                    default=rp_cats,
                    key="rp_cat"
                )

            filtered_risks = [
                r for r in all_risks
                if r.get("severity", "Low") in rp_sev
                and r.get("category", "Other") in rp_cat
            ]

            df = pd.DataFrame(filtered_risks)

            if not df.empty and "severity" in df.columns:

                def color_severity(val):
                    colors = {
                        "Critical": (
                            f"background-color: {COLOR_SEVERITY_CRITICAL_BG}; "
                            f"color: {COLOR_SEVERITY_CRITICAL}; font-weight: 700"
                        ),
                        "High": (
                            f"background-color: {COLOR_SEVERITY_HIGH_BG}; "
                            f"color: {COLOR_SEVERITY_HIGH}; font-weight: 700"
                        ),
                        "Medium": "background-color: rgba(255,179,0,0.15); color: #FFB300; font-weight: 700",
                        "Low": "background-color: rgba(0,227,150,0.12); color: #00E396; font-weight: 700",
                    }
                    return colors.get(val, "")

                # pandas 2.1+ / 3.x: Styler.applymap was renamed to Styler.map
                _styler = df.style
                if hasattr(_styler, "map"):
                    styled_df = _styler.map(color_severity, subset=["severity"])
                else:
                    styled_df = _styler.applymap(color_severity, subset=["severity"])

                st.dataframe(
                    styled_df,
                    height=420,
                    **_stretched_width_kwargs(),
                )

            st.markdown("<br>", unsafe_allow_html=True)

            # --- Detailed Findings ---
            st.markdown(
                f"<div class='section-header'>"
                f"<img src='https://cdn-icons-png.flaticon.com/512/2103/2103651.png' width='20'/>"
                f"Detailed Findings ({len(filtered_risks)})</div>",
                unsafe_allow_html=True
            )

            for risk in filtered_risks:
                severity    = risk.get("severity", "Low")
                category    = risk.get("category", "N/A")
                badge       = severity_badge(severity)
                conf        = risk.get("confidence", 0)

                with st.expander(f"{severity} Risk — {category}"):
                    st.markdown(
                        f"""
                        <div style='display:flex;align-items:center;gap:10px;margin-bottom:16px'>
                            {badge}
                            <span style='font-size:13px;color:{TEXT_MUTED}'>Confidence: <strong style='color:{TEXT}'>{conf}%</strong></span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    risk_col, rec_col = st.columns(2)
                    with risk_col:
                        st.markdown(
                            f"<div style='font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:8px'>Risk</div>"
                            f"<div style='font-size:14px;line-height:1.7'>{risk.get('risk', 'N/A')}</div>",
                            unsafe_allow_html=True
                        )
                    with rec_col:
                        st.markdown(
                            f"<div style='font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:8px'>Recommendation</div>"
                            f"<div style='font-size:14px;line-height:1.7'>{risk.get('recommendation', 'N/A')}</div>",
                            unsafe_allow_html=True
                        )

        st.markdown("<br>", unsafe_allow_html=True)

        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            import json
            st.download_button(
                label="Download Assessment JSON",
                data=json.dumps(st.session_state.all_risks, indent=2),
                file_name=f"risk_assessment_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                **_stretched_width_kwargs(),
            )
        with dl_col2:
            if st.session_state.all_risks:
                csv_data = pd.DataFrame(st.session_state.all_risks).to_csv(index=False)
                st.download_button(
                    label="Download as CSV",
                    data=csv_data,
                    file_name=f"risk_assessment_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    **_stretched_width_kwargs(),
                )

# ---------------------------------------------------
# PAGE: SETTINGS
# ---------------------------------------------------

elif page == "Settings":

    settings_col, info_col = st.columns([2, 1])

    with settings_col:
        st.markdown(
            f"""
            <div class='glass-card' style='margin-bottom:20px'>
                <div style='font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:20px'>
                    <img src='https://cdn-icons-png.flaticon.com/512/2716/2716652.png'
                         width='16' style='vertical-align:middle;margin-right:8px'/>
                    Platform Information
                </div>
                <table style='width:100%;border-collapse:collapse'>
                    <tr style='border-bottom:1px solid {BORDER}'>
                        <td style='padding:14px 0;color:{TEXT_MUTED};font-size:14px;width:40%'>Application</td>
                        <td style='padding:14px 0;font-weight:600;font-size:14px'>RiskLens AI</td>
                    </tr>
                    <tr style='border-bottom:1px solid {BORDER}'>
                        <td style='padding:14px 0;color:{TEXT_MUTED};font-size:14px'>Version</td>
                        <td style='padding:14px 0;font-weight:600;font-size:14px'>1.0.0</td>
                    </tr>
                    <tr style='border-bottom:1px solid {BORDER}'>
                        <td style='padding:14px 0;color:{TEXT_MUTED};font-size:14px'>Environment</td>
                        <td style='padding:14px 0;font-weight:600;font-size:14px'>
                            <span style='background:rgba(0,227,150,0.12);color:#00E396;border-radius:6px;padding:2px 10px;font-size:12px'>Production</span>
                        </td>
                    </tr>
                    <tr style='border-bottom:1px solid {BORDER}'>
                        <td style='padding:14px 0;color:{TEXT_MUTED};font-size:14px'>AI Engine</td>
                        <td style='padding:14px 0;font-weight:600;font-size:14px'>Groq LLM</td>
                    </tr>
                    <tr style='border-bottom:1px solid {BORDER}'>
                        <td style='padding:14px 0;color:{TEXT_MUTED};font-size:14px'>Review Framework</td>
                        <td style='padding:14px 0;font-weight:600;font-size:14px'>{st.session_state.framework_label}</td>
                    </tr>
                    <tr>
                        <td style='padding:14px 0;color:{TEXT_MUTED};font-size:14px'>Status</td>
                        <td style='padding:14px 0;font-weight:600;font-size:14px'>
                            <span style='display:inline-flex;align-items:center;gap:6px'>
                                <span style='width:8px;height:8px;border-radius:50%;background:#00E396;display:inline-block;box-shadow:0 0 8px #00E396'></span>
                                Operational
                            </span>
                        </td>
                    </tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class='glass-card'>
                <div style='font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:20px'>
                    <img src='https://cdn-icons-png.flaticon.com/512/3524/3524659.png'
                         width='16' style='vertical-align:middle;margin-right:8px'/>
                    API Configuration
                </div>
                <div style='font-size:14px;color:{TEXT_MUTED};margin-bottom:12px'>Analysis Endpoint</div>
                <div style='background:{"rgba(255,255,255,0.04)" if st.session_state.theme=="dark" else "rgba(0,0,0,0.04)"};
                            border-radius:10px;padding:12px 16px;font-family:monospace;font-size:13px;
                            border:1px solid {BORDER};word-break:break-all'>
                    https://risklens-ai-go8b.onrender.com/analyze
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with info_col:
        st.markdown(
            f"""
            <div class='glass-card'>
                <div style='font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:20px'>
                    Risk Score Legend
                </div>
                <div style='display:flex;flex-direction:column;gap:12px'>
                    <div style='display:flex;align-items:center;justify-content:space-between'>
                        <span class='badge-critical'>Critical</span>
                        <span style='font-size:13px;color:{TEXT_MUTED}'>40 pts / risk</span>
                    </div>
                    <div style='display:flex;align-items:center;justify-content:space-between'>
                        <span class='badge-high'>High</span>
                        <span style='font-size:13px;color:{TEXT_MUTED}'>25 pts / risk</span>
                    </div>
                    <div style='display:flex;align-items:center;justify-content:space-between'>
                        <span class='badge-medium'>Medium</span>
                        <span style='font-size:13px;color:{TEXT_MUTED}'>15 pts / risk</span>
                    </div>
                    <div style='display:flex;align-items:center;justify-content:space-between'>
                        <span class='badge-low'>Low</span>
                        <span style='font-size:13px;color:{TEXT_MUTED}'>5 pts / risk</span>
                    </div>
                </div>

                <div style='margin-top:20px;padding-top:20px;border-top:1px solid {BORDER}'>
                    <div style='font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:{TEXT_MUTED};margin-bottom:12px'>
                        Score Ranges
                    </div>
                    <div style='font-size:13px;display:flex;flex-direction:column;gap:8px'>
                        <div style='display:flex;justify-content:space-between'>
                            <span style='color:{TEXT_MUTED}'>0 – 50</span>
                            <span style='color:#00E396;font-weight:600'>Low Risk</span>
                        </div>
                        <div style='display:flex;justify-content:space-between'>
                            <span style='color:{TEXT_MUTED}'>51 – 100</span>
                            <span style='color:#FFB300;font-weight:600'>Medium Risk</span>
                        </div>
                        <div style='display:flex;justify-content:space-between'>
                            <span style='color:{TEXT_MUTED}'>101 – 200</span>
                            <span style='color:{COLOR_SEVERITY_HIGH};font-weight:600'>High Risk</span>
                        </div>
                        <div style='display:flex;justify-content:space-between'>
                            <span style='color:{TEXT_MUTED}'>&gt; 200</span>
                            <span style='color:{COLOR_SEVERITY_CRITICAL};font-weight:600'>Critical Risk</span>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )