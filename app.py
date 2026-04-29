import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
from thefuzz import fuzz

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Death Claim Verification",
    page_icon="🏦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    /* ── Background ── */
    .stApp {
        background: #0d1117;
        background-image:
            radial-gradient(ellipse at 20% 20%, rgba(0, 80, 160, 0.15) 0%, transparent 60%),
            radial-gradient(ellipse at 80% 80%, rgba(0, 40, 80, 0.2) 0%, transparent 60%);
    }

    /* ── Header banner ── */
    .header-banner {
        background: linear-gradient(135deg, #0a2540 0%, #0f3460 50%, #0a2540 100%);
        border: 1px solid rgba(0, 120, 212, 0.3);
        border-radius: 12px;
        padding: 28px 36px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    }
    .header-banner::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #0078d4, #00b4d8, #0078d4);
    }
    .header-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #e6edf3;
        letter-spacing: -0.02em;
        margin: 0 0 4px 0;
    }
    .header-subtitle {
        font-size: 0.85rem;
        color: #7d8590;
        font-family: 'IBM Plex Mono', monospace;
        letter-spacing: 0.04em;
        margin: 0;
    }
    .header-badge {
        display: inline-block;
        background: rgba(0, 120, 212, 0.2);
        border: 1px solid rgba(0, 120, 212, 0.4);
        color: #58a6ff;
        font-size: 0.7rem;
        font-family: 'IBM Plex Mono', monospace;
        padding: 3px 10px;
        border-radius: 20px;
        margin-bottom: 10px;
        letter-spacing: 0.08em;
    }

    /* ── Section cards ── */
    .section-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 24px;
        margin-bottom: 20px;
    }
    .section-label {
        font-size: 0.7rem;
        font-family: 'IBM Plex Mono', monospace;
        color: #7d8590;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 14px;
    }

    /* ── Success result card ── */
    .result-card {
        background: linear-gradient(135deg, #0d2818 0%, #0f3020 100%);
        border: 1px solid #238636;
        border-radius: 12px;
        padding: 28px;
        margin-top: 24px;
        position: relative;
        overflow: hidden;
    }
    .result-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #2ea043, #3fb950, #2ea043);
    }
    .result-status {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 20px;
    }
    .status-dot {
        width: 10px; height: 10px;
        background: #3fb950;
        border-radius: 50%;
        box-shadow: 0 0 8px #3fb950;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }
    .status-text {
        font-size: 0.75rem;
        font-family: 'IBM Plex Mono', monospace;
        color: #3fb950;
        letter-spacing: 0.1em;
    }
    .result-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 16px;
    }
    .metric-block {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        padding: 16px;
    }
    .metric-label {
        font-size: 0.65rem;
        font-family: 'IBM Plex Mono', monospace;
        color: #7d8590;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 1.05rem;
        font-weight: 600;
        color: #e6edf3;
    }
    .metric-value.balance {
        color: #3fb950;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.15rem;
    }

    /* ── Error card ── */
    .error-card {
        background: linear-gradient(135deg, #1c0d0d 0%, #2a1010 100%);
        border: 1px solid #da3633;
        border-radius: 12px;
        padding: 24px;
        margin-top: 24px;
    }
    .error-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #f85149;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .error-body {
        font-size: 0.82rem;
        color: #8d96a0;
        line-height: 1.5;
    }

    /* ── Uploader overrides ── */
    [data-testid="stFileUploader"] {
        background: #161b22 !important;
        border: 1px dashed #30363d !important;
        border-radius: 10px !important;
    }

    /* ── Divider ── */
    .divider {
        border: none;
        border-top: 1px solid #21262d;
        margin: 24px 0;
    }

    /* ── Match score badge ── */
    .score-badge {
        display: inline-block;
        background: rgba(63, 185, 80, 0.15);
        border: 1px solid rgba(63, 185, 80, 0.3);
        color: #3fb950;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        padding: 2px 10px;
        border-radius: 20px;
        margin-left: 10px;
        vertical-align: middle;
    }

    /* Hide Streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="header-banner">
        <div class="header-badge">SECURE · INTERNAL BANKING SYSTEM</div>
        <div class="header-title">🏦 Death Claim Verification</div>
        <div class="header-subtitle">OCR-POWERED · FUZZY MATCHING · AUTOMATED VERIFICATION</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Load OCR model (cached) ────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading OCR engine…")
def load_ocr():
    import easyocr
    return easyocr.Reader(["en"], gpu=False)


# ── Load bank records ──────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading bank records…")
def load_records():
    try:
        df = pd.read_csv("bank_records.csv", dtype={"Account_No": str})
        df["Deceased_Name"] = df["Deceased_Name"].str.strip().str.upper()
        df["Nominee_Name"] = df["Nominee_Name"].str.strip().str.upper()
        return df
    except FileNotFoundError:
        return None


# ── OCR extraction helper ──────────────────────────────────────────────────────
def extract_text(ocr_engine, image: Image.Image) -> str:
    img_array = np.array(image.convert("RGB"))
    # EasyOCR returns: [([[x1,y1],[x2,y2],[x3,y3],[x4,y4]], text, confidence), ...]
    results = ocr_engine.readtext(img_array)
    lines = [text for (_, text, conf) in results if conf > 0.1]
    return " ".join(lines).upper()


# ── Fuzzy match ────────────────────────────────────────────────────────────────
THRESHOLD = 70

def find_match(ocr_text: str, df: pd.DataFrame):
    best_score = 0
    best_row = None
    for _, row in df.iterrows():
        score = fuzz.token_set_ratio(row["Deceased_Name"], ocr_text)
        if score > best_score:
            best_score = score
            best_row = row
    if best_score >= THRESHOLD:
        return best_row, best_score
    return None, best_score


# ── Main UI ────────────────────────────────────────────────────────────────────
df = load_records()

if df is None:
    st.error(
        "**`bank_records.csv` not found.** Place it in the same directory as `app.py` and restart.",
        icon="🚨",
    )
    st.stop()

# ── Step 1: Upload ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown('<div class="section-label">Step 01 — Upload Death Certificate</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    label="Upload death certificate image",
    type=["png", "jpg", "jpeg"],
    label_visibility="collapsed",
    help="Accepts PNG / JPG images. Watermarked certificates are supported.",
)

st.markdown("</div>", unsafe_allow_html=True)

if uploaded_file:
    image = Image.open(uploaded_file)
    col_img, col_info = st.columns([1, 1])
    with col_img:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Certificate Preview</div>', unsafe_allow_html=True)
        st.image(image, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_info:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">File Details</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="font-family:'IBM Plex Mono',monospace;font-size:0.78rem;color:#7d8590;line-height:2;">
            <span style="color:#e6edf3;">Filename</span><br>{uploaded_file.name}<br><br>
            <span style="color:#e6edf3;">Dimensions</span><br>{image.width} × {image.height} px<br><br>
            <span style="color:#e6edf3;">Mode</span><br>{image.mode}<br><br>
            <span style="color:#e6edf3;">Size</span><br>{uploaded_file.size / 1024:.1f} KB
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Step 2: Process ────────────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Step 02 — OCR Extraction & Verification</div>', unsafe_allow_html=True)

    verify_btn = st.button("🔍 Run Verification", use_container_width=True, type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

    if verify_btn:
        with st.spinner("Initialising OCR engine…"):
            ocr = load_ocr()

        with st.spinner("Extracting text from certificate…"):
            try:
                ocr_text = extract_text(ocr, image)
            except Exception as exc:
                st.error(f"OCR failed: {exc}", icon="❌")
                st.stop()

        with st.spinner("Matching against bank records…"):
            matched_row, score = find_match(ocr_text, df)

        # ── Result ─────────────────────────────────────────────────────────────
        if matched_row is not None:
            balance_fmt = f"₹ {float(matched_row['Balance']):,.2f}"
            st.markdown(
                f"""
                <div class="result-card">
                    <div class="result-status">
                        <div class="status-dot"></div>
                        <span class="status-text">VERIFICATION SUCCESSFUL</span>
                        <span class="score-badge">MATCH {score}%</span>
                    </div>
                    <div class="result-grid">
                        <div class="metric-block">
                            <div class="metric-label">Deceased Name</div>
                            <div class="metric-value">{matched_row['Deceased_Name']}</div>
                        </div>
                        <div class="metric-block">
                            <div class="metric-label">Nominee Name</div>
                            <div class="metric-value">{matched_row['Nominee_Name']}</div>
                        </div>
                        <div class="metric-block">
                            <div class="metric-label">Claimable Balance</div>
                            <div class="metric-value balance">{balance_fmt}</div>
                        </div>
                    </div>
                    <hr style="border:none;border-top:1px solid rgba(255,255,255,0.06);margin:20px 0;">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
                        <div class="metric-block">
                            <div class="metric-label">Account Number</div>
                            <div class="metric-value" style="font-family:'IBM Plex Mono',monospace;">
                                {matched_row['Account_No']}
                            </div>
                        </div>
                        <div class="metric-block">
                            <div class="metric-label">Relation to Deceased</div>
                            <div class="metric-value">{matched_row['Relation']}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="error-card">
                    <div class="error-title">⚠ No Matching Record Found</div>
                    <div class="error-body">
                        The death certificate could not be matched to any account holder in the database.
                        Best fuzzy score achieved: <strong style="color:#f85149;">{score}%</strong>
                        (threshold: {THRESHOLD}%).<br><br>
                        This may be due to a heavily watermarked certificate, poor image quality,
                        or a name not present in the current records. Please verify manually.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander("🔬 Debug — Raw OCR Output"):
                st.markdown(
                    '<p style="font-size:0.75rem;color:#7d8590;font-family:IBM Plex Mono,monospace;">'
                    "Text extracted by OCR engine (normalised to UPPERCASE):</p>",
                    unsafe_allow_html=True,
                )
                st.code(ocr_text if ocr_text.strip() else "[No text extracted]", language="text")

# ── Footer ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <hr class="divider">
    <div style="text-align:center;font-size:0.68rem;font-family:'IBM Plex Mono',monospace;color:#3d444d;">
        INTERNAL USE ONLY · BANK OFFICER ACCESS · POWERED BY PADDLEOCR + FUZZY MATCHING
    </div>
    """,
    unsafe_allow_html=True,
)