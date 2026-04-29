"""
╔══════════════════════════════════════════════════════════════════╗
║          NeoVault · Death Claim Verification Platform           ║
║          A Production-Grade Fintech Demo · 2026 Edition         ║
╚══════════════════════════════════════════════════════════════════╝

Architecture:
  ┌─ auth.py logic     → Biometric Gate (webcam + OTP simulation)
  ├─ ocr_engine.py     → EasyOCR extraction & preprocessing
  ├─ fuzzy_matcher.py  → Trust-Score engine with explanations
  ├─ fraud_detector.py → Heuristic fraud/tampering flags
  ├─ settlement.py     → Interest calculation & PDF receipt
  └─ app.py            → Streamlit orchestration (this file)
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import random
import io
import base64
from datetime import datetime, timedelta
from PIL import Image
from thefuzz import fuzz

# ──────────────────────────────────────────────────────────────────
#  PAGE CONFIG  (must be first Streamlit call)
# ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NeoVault · Claim Desk",
    page_icon="🏛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════
#  GLOBAL CSS  — Glassmorphism Dark Theme + Cinematic Animations
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ─── Fonts ──────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500;700&display=swap');

/* ─── Root tokens ────────────────────────────────────────────── */
:root {
  --bg-base:       #050911;
  --bg-surface:    rgba(10, 16, 28, 0.85);
  --bg-glass:      rgba(255,255,255,0.04);
  --bg-glass-h:    rgba(255,255,255,0.07);
  --border:        rgba(255,255,255,0.07);
  --border-bright: rgba(99,179,237,0.25);
  --blue:          #3B82F6;
  --blue-glow:     rgba(59,130,246,0.35);
  --emerald:       #10B981;
  --emerald-glow:  rgba(16,185,129,0.3);
  --amber:         #F59E0B;
  --rose:          #F43F5E;
  --slate:         #94A3B8;
  --text-primary:  #F1F5F9;
  --text-muted:    #64748B;
  --mono:          'JetBrains Mono', monospace;
  --display:       'Syne', sans-serif;
}

/* ─── Base reset ─────────────────────────────────────────────── */
html, body, [class*="css"], .stApp {
  font-family: var(--display) !important;
  background: var(--bg-base) !important;
  color: var(--text-primary);
}

/* ─── Animated mesh background ───────────────────────────────── */
.stApp::before {
  content: '';
  position: fixed;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 10% 5%,  rgba(59,130,246,0.08) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 90% 90%, rgba(16,185,129,0.06) 0%, transparent 60%),
    radial-gradient(ellipse 50% 40% at 50% 50%, rgba(99,102,241,0.04) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

/* ─── Sidebar ────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: rgba(5, 9, 17, 0.95) !important;
  border-right: 1px solid var(--border) !important;
  backdrop-filter: blur(20px);
}
[data-testid="stSidebar"] * { font-family: var(--display) !important; }

/* ─── Main container ─────────────────────────────────────────── */
.block-container {
  padding: 1.5rem 2rem 3rem !important;
  max-width: 1400px !important;
}

/* ─── Hide chrome ────────────────────────────────────────────── */
#MainMenu, footer, header, [data-testid="stToolbar"] { display: none !important; }

/* ─── Card component ─────────────────────────────────────────── */
.nv-card {
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 24px;
  backdrop-filter: blur(12px);
  transition: border-color 0.3s, box-shadow 0.3s;
  position: relative;
  overflow: hidden;
}
.nv-card:hover {
  border-color: var(--border-bright);
  box-shadow: 0 0 30px rgba(59,130,246,0.08);
}
.nv-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.02) 0%, transparent 60%);
  pointer-events: none;
}

/* ─── KPI metric card ────────────────────────────────────────── */
.kpi-card {
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 20px 22px;
  text-align: left;
  position: relative;
  overflow: hidden;
}
.kpi-card .kpi-icon {
  font-size: 1.3rem;
  margin-bottom: 10px;
  display: block;
}
.kpi-card .kpi-label {
  font-family: var(--mono);
  font-size: 0.6rem;
  letter-spacing: 0.14em;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-bottom: 6px;
}
.kpi-card .kpi-value {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1;
  letter-spacing: -0.03em;
}
.kpi-card .kpi-sub {
  font-family: var(--mono);
  font-size: 0.65rem;
  color: var(--text-muted);
  margin-top: 6px;
}
.kpi-card .kpi-accent {
  position: absolute;
  top: 0; right: 0;
  width: 60px; height: 60px;
  border-radius: 0 14px 0 60px;
  opacity: 0.15;
}

/* ─── Section label ──────────────────────────────────────────── */
.section-eyebrow {
  font-family: var(--mono);
  font-size: 0.58rem;
  letter-spacing: 0.2em;
  color: var(--blue);
  text-transform: uppercase;
  margin-bottom: 8px;
}
.section-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 18px;
  letter-spacing: -0.02em;
}

/* ─── Tag / badge ────────────────────────────────────────────── */
.tag {
  display: inline-block;
  font-family: var(--mono);
  font-size: 0.6rem;
  letter-spacing: 0.1em;
  padding: 3px 10px;
  border-radius: 20px;
  margin-right: 6px;
}
.tag-blue    { background: rgba(59,130,246,0.15); border:1px solid rgba(59,130,246,0.3); color:#60A5FA; }
.tag-emerald { background: rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.3); color:#34D399; }
.tag-amber   { background: rgba(245,158,11,0.15);  border:1px solid rgba(245,158,11,0.3);  color:#FCD34D; }
.tag-rose    { background: rgba(244,63,94,0.15);   border:1px solid rgba(244,63,94,0.3);   color:#FB7185; }

/* ─── Status pill ────────────────────────────────────────────── */
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-family: var(--mono);
  font-size: 0.65rem;
  letter-spacing: 0.08em;
  padding: 5px 12px;
  border-radius: 30px;
}
.status-pill .dot {
  width: 7px; height: 7px;
  border-radius: 50%;
}

/* ─── Biometric gate ─────────────────────────────────────────── */
.bio-gate {
  background: linear-gradient(145deg, rgba(5,9,17,0.98), rgba(10,20,40,0.98));
  border: 1px solid rgba(59,130,246,0.2);
  border-radius: 20px;
  padding: 48px 40px;
  text-align: center;
  max-width: 480px;
  margin: 60px auto;
  position: relative;
  overflow: hidden;
}
.bio-gate::before {
  content: '';
  position: absolute;
  top: -1px; left: 10%; right: 10%;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--blue), transparent);
}
.bio-logo {
  font-size: 2.8rem;
  margin-bottom: 6px;
}
.bio-brand {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--text-primary);
}
.bio-brand span { color: var(--blue); }
.bio-tagline {
  font-family: var(--mono);
  font-size: 0.6rem;
  color: var(--text-muted);
  letter-spacing: 0.2em;
  margin-bottom: 32px;
}

/* ─── Scan ring animation ────────────────────────────────────── */
@keyframes scan-ring {
  0%   { transform: scale(0.92); opacity: 0.7; box-shadow: 0 0 0 0 var(--blue-glow); }
  50%  { transform: scale(1.04); opacity: 1;   box-shadow: 0 0 0 12px rgba(59,130,246,0); }
  100% { transform: scale(0.92); opacity: 0.7; box-shadow: 0 0 0 0 var(--blue-glow); }
}
@keyframes scan-line {
  0%   { top: 0%; }
  100% { top: 100%; }
}
@keyframes fade-in {
  from { opacity:0; transform:translateY(10px); }
  to   { opacity:1; transform:translateY(0); }
}
.scan-frame {
  width: 130px; height: 130px;
  border: 2px solid var(--blue);
  border-radius: 50%;
  margin: 0 auto 22px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: scan-ring 2.5s ease-in-out infinite;
}
.scan-frame .face-icon { font-size: 3.5rem; }
.scan-frame .scan-overlay {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  overflow: hidden;
  pointer-events: none;
}
.scan-frame .scan-line {
  position: absolute;
  left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(59,130,246,0.8), transparent);
  animation: scan-line 1.5s linear infinite;
}

/* ─── Trust score ring ───────────────────────────────────────── */
.trust-ring-wrap {
  position: relative;
  width: 120px; height: 120px;
  margin: 0 auto;
}
.trust-ring-wrap svg { transform: rotate(-90deg); }
.trust-ring-label {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.trust-ring-label .score-num {
  font-size: 1.6rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  line-height: 1;
}
.trust-ring-label .score-pct {
  font-family: var(--mono);
  font-size: 0.55rem;
  color: var(--text-muted);
  letter-spacing: 0.1em;
}

/* ─── Settlement card ────────────────────────────────────────── */
.settlement-card {
  background: linear-gradient(145deg, rgba(6,12,22,0.95) 0%, rgba(10,22,38,0.95) 100%);
  border: 1px solid var(--border-bright);
  border-radius: 20px;
  padding: 32px;
  position: relative;
  overflow: hidden;
}
.settlement-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--blue), var(--emerald));
}
.settlement-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
  font-size: 0.88rem;
}
.settlement-line:last-child { border-bottom: none; }
.settlement-line .item { color: var(--slate); }
.settlement-line .amount { font-family: var(--mono); font-weight: 600; }
.settlement-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0 0;
  margin-top: 8px;
  font-size: 1.1rem;
  font-weight: 700;
}
.settlement-total .label { color: var(--text-primary); }
.settlement-total .amount {
  font-family: var(--mono);
  font-size: 1.4rem;
  color: var(--emerald);
}

/* ─── Fraud alert ────────────────────────────────────────────── */
.fraud-alert {
  background: rgba(244,63,94,0.08);
  border: 1px solid rgba(244,63,94,0.3);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 12px;
}
.fraud-alert .fa-title {
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.1em;
  color: var(--rose);
  margin-bottom: 4px;
}
.fraud-alert .fa-body { font-size: 0.82rem; color: var(--slate); }

/* ─── Verify button override ─────────────────────────────────── */
.stButton>button[kind="primary"] {
  background: linear-gradient(135deg, #2563EB, #3B82F6) !important;
  border: none !important;
  border-radius: 10px !important;
  font-family: var(--display) !important;
  font-weight: 700 !important;
  letter-spacing: 0.02em !important;
  font-size: 0.9rem !important;
  padding: 0.65rem 1.4rem !important;
  transition: all 0.25s !important;
  box-shadow: 0 4px 20px rgba(59,130,246,0.35) !important;
}
.stButton>button[kind="primary"]:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 8px 28px rgba(59,130,246,0.5) !important;
}
.stButton>button {
  border-radius: 10px !important;
  font-family: var(--display) !important;
  font-weight: 600 !important;
}

/* ─── File uploader ──────────────────────────────────────────── */
[data-testid="stFileUploader"] {
  background: rgba(255,255,255,0.02) !important;
  border: 1.5px dashed rgba(59,130,246,0.3) !important;
  border-radius: 14px !important;
  transition: border-color 0.3s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: rgba(59,130,246,0.6) !important;
  background: rgba(59,130,246,0.04) !important;
}

/* ─── Sidebar nav item ───────────────────────────────────────── */
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
  font-size: 0.88rem;
  font-weight: 500;
  color: var(--slate);
}
.nav-item:hover, .nav-item.active {
  background: rgba(59,130,246,0.1);
  color: var(--text-primary);
}
.nav-item.active { border-left: 3px solid var(--blue); padding-left: 11px; }

/* ─── System health indicator ────────────────────────────────── */
.health-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
  font-size: 0.82rem;
}
.health-item:last-child { border-bottom: none; }
.health-bar-wrap { width: 80px; height: 4px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden; }
.health-bar { height: 100%; border-radius: 4px; }

/* ─── Confetti keyframe ──────────────────────────────────────── */
@keyframes confetti-fall {
  0%   { transform: translateY(-20px) rotate(0deg); opacity: 1; }
  100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
}
.confetti-piece {
  position: fixed;
  width: 10px; height: 10px;
  animation: confetti-fall linear forwards;
  z-index: 9999;
  pointer-events: none;
}

/* ─── Progress bar ───────────────────────────────────────────── */
.stProgress > div > div { background-color: var(--blue) !important; border-radius: 4px; }
.stProgress > div { background: rgba(255,255,255,0.06) !important; border-radius: 4px; }

/* ─── Sidebar divider ────────────────────────────────────────── */
.sidebar-divider {
  border: none;
  border-top: 1px solid var(--border);
  margin: 16px 0;
}

/* ─── OCR raw output ─────────────────────────────────────────── */
.ocr-dump {
  background: rgba(0,0,0,0.4);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px;
  font-family: var(--mono);
  font-size: 0.72rem;
  color: var(--slate);
  line-height: 1.7;
  word-break: break-all;
  max-height: 160px;
  overflow-y: auto;
}

/* ─── Metric highlight ───────────────────────────────────────── */
.metric-hl {
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 18px;
  position: relative;
}
.metric-hl .mh-label {
  font-family: var(--mono);
  font-size: 0.58rem;
  letter-spacing: 0.14em;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-bottom: 6px;
}
.metric-hl .mh-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-primary);
}

/* ─── OTP input wrapper ──────────────────────────────────────── */
.otp-label {
  font-family: var(--mono);
  font-size: 0.62rem;
  letter-spacing: 0.12em;
  color: var(--blue);
  text-transform: uppercase;
  margin-bottom: 4px;
}

/* ─── Slide-in animation ─────────────────────────────────────── */
.slide-in {
  animation: fade-in 0.5s ease-out both;
}

/* ─── Timeline step ──────────────────────────────────────────── */
.timeline-step {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
}
.timeline-step:last-child { border-bottom: none; }
.tl-dot {
  width: 28px; height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  flex-shrink: 0;
  margin-top: 2px;
}
.tl-content .tl-title { font-size: 0.85rem; font-weight: 600; color: var(--text-primary); }
.tl-content .tl-desc  { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }
.tl-content .tl-time  { font-family: var(--mono); font-size: 0.6rem; color: var(--text-muted); margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  SESSION STATE  initialisation
# ══════════════════════════════════════════════════════════════════
for key, default in {
    "authenticated": False,
    "auth_method":   None,
    "otp_sent":      False,
    "mock_otp":      None,
    "page":          "dashboard",
    "verify_result": None,
    "disbursed":     False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ══════════════════════════════════════════════════════════════════
#  MODULE: OCR ENGINE
# ══════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def load_ocr_engine():
    """Load EasyOCR reader (English, CPU mode). Cached across reruns."""
    import easyocr
    return easyocr.Reader(["en"], gpu=False)


def extract_text_from_image(ocr_engine, image: Image.Image) -> tuple[str, list]:
    """
    Image Processing + OCR Extraction.
    Returns (normalised_text, raw_results) where raw_results is a list of
    (bbox, text, confidence) tuples from EasyOCR.
    """
    img_rgb   = image.convert("RGB")
    img_array = np.array(img_rgb)
    raw       = ocr_engine.readtext(img_array, detail=1, paragraph=False)
    lines     = [text.upper() for (_, text, conf) in raw if conf > 0.1]
    return " ".join(lines), raw


# ══════════════════════════════════════════════════════════════════
#  MODULE: FUZZY MATCHER / TRUST SCORE ENGINE
# ══════════════════════════════════════════════════════════════════
MATCH_THRESHOLD = 70

def compute_trust_score(ocr_text: str, df: pd.DataFrame) -> dict:
    """
    Trust-Score Engine v2.0
    Returns a dict with:
      - matched_row  : pd.Series | None
      - score        : int  (0–100)
      - grade        : str  (EXACT / HIGH / PARTIAL / LOW / NO_MATCH)
      - explanation  : str  human-readable reason
      - all_scores   : list of (name, score) for every record
    """
    all_scores = []
    for _, row in df.iterrows():
        name  = row["Deceased_Name"]
        # Multiple fuzzy strategies → take best
        s1 = fuzz.token_set_ratio(name, ocr_text)
        s2 = fuzz.partial_ratio(name, ocr_text)
        s3 = fuzz.token_sort_ratio(name, ocr_text)
        best = max(s1, s2, s3)
        all_scores.append((name, best, row))

    all_scores.sort(key=lambda x: x[1], reverse=True)
    top_name, top_score, top_row = all_scores[0]

    if top_score >= 95:
        grade       = "EXACT"
        explanation = f"Perfect token match for '{top_name}' found in OCR text."
        matched     = top_row
    elif top_score >= 85:
        grade       = "HIGH"
        explanation = f"High-confidence match for '{top_name}' ({top_score}%). Minor OCR artefact or spacing difference detected."
        matched     = top_row
    elif top_score >= MATCH_THRESHOLD:
        grade       = "PARTIAL"
        explanation = f"Partial match for '{top_name}' ({top_score}%). Possible watermark overlay, font distortion, or OCR noise. Manual review recommended."
        matched     = top_row
    elif top_score >= 50:
        grade       = "LOW"
        explanation = f"Low-confidence candidate '{top_name}' ({top_score}%). Does not meet threshold. Manual verification required."
        matched     = None
    else:
        grade       = "NO_MATCH"
        explanation = f"No record found above noise floor. Best candidate '{top_name}' scored {top_score}%."
        matched     = None

    return {
        "matched_row":  matched,
        "score":        top_score,
        "grade":        grade,
        "explanation":  explanation,
        "all_scores":   [(n, s) for n, s, _ in all_scores],
    }


# ══════════════════════════════════════════════════════════════════
#  MODULE: FRAUD DETECTOR
# ══════════════════════════════════════════════════════════════════
def run_fraud_checks(ocr_text: str, image: Image.Image) -> list[dict]:
    """
    Heuristic fraud / tampering detection.
    Returns a list of flag dicts: {level, title, detail}
    Level: WARNING | CRITICAL
    """
    flags = []
    text_lower = ocr_text.lower()

    # 1) Registration date missing
    date_keywords = ["date of registration", "registration date", "reg. date", "reg date"]
    if not any(kw in text_lower for kw in date_keywords):
        flags.append({
            "level":  "WARNING",
            "title":  "Registration Date Absent",
            "detail": "The 'Date of Registration' field could not be detected in the certificate text. "
                      "This is a mandatory field for a valid death certificate."
        })

    # 2) Suspicious short OCR output (possibly blank / watermarked beyond recognition)
    if len(ocr_text.split()) < 15:
        flags.append({
            "level":  "CRITICAL",
            "title":  "Minimal Text Extracted",
            "detail": f"Only {len(ocr_text.split())} words were extracted. "
                      "The certificate may be heavily watermarked, low-resolution, or contain non-standard typography."
        })

    # 3) Image aspect ratio heuristic (death certs are typically portrait A4-ish)
    w, h = image.size
    ratio = w / h if h > 0 else 1
    if ratio > 1.5:
        flags.append({
            "level":  "WARNING",
            "title":  "Unusual Image Orientation",
            "detail": f"Image aspect ratio is {ratio:.2f} (landscape). Official death certificates "
                      "are typically portrait orientation. Possible scan error or modified document."
        })

    # 4) Inconsistent keyword presence (real cert usually mentions "death" and "certificate")
    has_death = "death" in text_lower or "deceased" in text_lower or "died" in text_lower
    has_cert  = "certificate" in text_lower or "certif" in text_lower
    if not (has_death and has_cert):
        flags.append({
            "level":  "CRITICAL",
            "title":  "Missing Core Certificate Keywords",
            "detail": f"Expected keywords ('death/deceased', 'certificate') not found. "
                      "{'Death-related keyword missing. ' if not has_death else ''}"
                      "{'Certificate keyword missing.' if not has_cert else ''} "
                      "This document may not be a valid death certificate."
        })

    return flags


# ══════════════════════════════════════════════════════════════════
#  MODULE: SETTLEMENT CALCULATOR + PDF RECEIPT
# ══════════════════════════════════════════════════════════════════
ANNUAL_INTEREST_RATE = 0.04   # 4 % p.a. savings rate

def compute_settlement(balance: float, days_since_death: int = 45) -> dict:
    """
    Calculate final payout with accrued interest.
    Uses simple interest: I = P × r × (t / 365)
    """
    interest = balance * ANNUAL_INTEREST_RATE * (days_since_death / 365)
    tds       = interest * 0.10   # 10 % TDS on interest
    gross     = balance + interest
    net       = gross - tds
    return {
        "principal":      balance,
        "interest":       round(interest, 2),
        "tds":            round(tds, 2),
        "gross":          round(gross, 2),
        "net_payout":     round(net, 2),
        "days":           days_since_death,
        "rate_pct":       ANNUAL_INTEREST_RATE * 100,
    }


def generate_pdf_receipt(row, settlement: dict, claim_id: str) -> bytes:
    """
    Generate a text-based PDF settlement receipt.
    Returns bytes that can be downloaded.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('NVTitle', parent=styles['Title'],
                                     fontSize=18, textColor=colors.HexColor('#1E3A5F'),
                                     spaceAfter=6)
        sub_style   = ParagraphStyle('NVSub',   parent=styles['Normal'],
                                     fontSize=9, textColor=colors.grey, spaceAfter=16)
        h2_style    = ParagraphStyle('NVH2',    parent=styles['Heading2'],
                                     fontSize=11, textColor=colors.HexColor('#1E3A5F'))
        body_style  = styles['Normal']

        now = datetime.now().strftime("%d %b %Y, %I:%M %p")
        story = [
            Paragraph("🏛 NeoVault Bank", title_style),
            Paragraph("Digital Settlement Receipt — Death Claim Disbursement", sub_style),
            Paragraph(f"<b>Claim ID:</b> {claim_id} &nbsp;&nbsp; <b>Generated:</b> {now}", body_style),
            Spacer(1, 0.4*cm),
            Paragraph("Account Holder Details", h2_style),
        ]

        details = [
            ["Field", "Value"],
            ["Deceased Name",   row["Deceased_Name"]],
            ["Account Number",  str(row["Account_No"])],
            ["Nominee Name",    row["Nominee_Name"]],
            ["Relation",        row["Relation"]],
        ]
        tbl = Table(details, colWidths=[6*cm, 10*cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor('#1E3A5F')),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTSIZE",   (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.white]),
            ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor('#CCCCCC')),
            ("PADDING", (0,0), (-1,-1), 6),
        ]))
        story += [tbl, Spacer(1, 0.5*cm), Paragraph("Settlement Breakdown", h2_style)]

        fin_data = [
            ["Description",         "Amount (INR)"],
            ["Principal Balance",   f"₹ {settlement['principal']:,.2f}"],
            ["Accrued Interest",    f"₹ {settlement['interest']:,.2f}"],
            [f"  (@ {settlement['rate_pct']}% p.a. for {settlement['days']} days)", ""],
            ["Gross Amount",        f"₹ {settlement['gross']:,.2f}"],
            ["TDS Deducted (10%)",  f"- ₹ {settlement['tds']:,.2f}"],
            ["NET PAYOUT",          f"₹ {settlement['net_payout']:,.2f}"],
        ]
        fin_tbl = Table(fin_data, colWidths=[10*cm, 6*cm])
        fin_tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor('#1E3A5F')),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTSIZE",    (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.whitesmoke, colors.white]),
            ("BACKGROUND",  (0,-1), (-1,-1), colors.HexColor('#10B981')),
            ("TEXTCOLOR",   (0,-1), (-1,-1), colors.white),
            ("FONTWEIGHT",  (0,-1), (-1,-1), "BOLD"),
            ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor('#CCCCCC')),
            ("PADDING", (0,0), (-1,-1), 6),
        ]))
        story += [fin_tbl, Spacer(1, 0.6*cm),
                  Paragraph("This is a system-generated receipt. No physical signature required.", sub_style),
                  Paragraph("NeoVault Bank · Internal Banking Operations · Secure Digital Disbursement", sub_style)]

        doc.build(story)
        return buf.getvalue()

    except ImportError:
        # Fallback: plain text "PDF" if reportlab not installed
        lines = [
            "NeoVault Bank — Settlement Receipt",
            f"Claim ID: {claim_id}",
            f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}",
            "",
            f"Deceased:  {row['Deceased_Name']}",
            f"Account:   {row['Account_No']}",
            f"Nominee:   {row['Nominee_Name']} ({row['Relation']})",
            "",
            f"Principal:  ₹ {settlement['principal']:,.2f}",
            f"Interest:   ₹ {settlement['interest']:,.2f}",
            f"TDS:       -₹ {settlement['tds']:,.2f}",
            f"NET PAYOUT: ₹ {settlement['net_payout']:,.2f}",
        ]
        return "\n".join(lines).encode()


# ══════════════════════════════════════════════════════════════════
#  MODULE: BANK RECORDS LOADER
# ══════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def load_bank_records():
    try:
        df = pd.read_csv("bank_records.csv", dtype={"Account_No": str})
        df["Deceased_Name"] = df["Deceased_Name"].str.strip().str.upper()
        df["Nominee_Name"]  = df["Nominee_Name"].str.strip().str.upper()
        return df
    except FileNotFoundError:
        return None


# ══════════════════════════════════════════════════════════════════
#  HELPER: trust-score ring SVG
# ══════════════════════════════════════════════════════════════════
def trust_ring_html(score: int, grade: str) -> str:
    radius   = 48
    circ     = 2 * 3.14159 * radius
    dash_arr = (score / 100) * circ
    grade_colors = {
        "EXACT":    ("#10B981", "#34D399"),
        "HIGH":     ("#3B82F6", "#60A5FA"),
        "PARTIAL":  ("#F59E0B", "#FCD34D"),
        "LOW":      ("#F97316", "#FDBA74"),
        "NO_MATCH": ("#F43F5E", "#FB7185"),
    }
    c1, c2 = grade_colors.get(grade, ("#64748B", "#94A3B8"))
    return f"""
<div class="trust-ring-wrap">
  <svg width="120" height="120" viewBox="0 0 120 120">
    <defs>
      <linearGradient id="rg" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%"   stop-color="{c1}"/>
        <stop offset="100%" stop-color="{c2}"/>
      </linearGradient>
    </defs>
    <circle cx="60" cy="60" r="{radius}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="8"/>
    <circle cx="60" cy="60" r="{radius}" fill="none" stroke="url(#rg)" stroke-width="8"
            stroke-dasharray="{dash_arr:.1f} {circ:.1f}" stroke-linecap="round"/>
  </svg>
  <div class="trust-ring-label">
    <div class="score-num" style="color:{c1};">{score}</div>
    <div class="score-pct">TRUST %</div>
  </div>
</div>"""


# ══════════════════════════════════════════════════════════════════
#  BIOMETRIC GATE
# ══════════════════════════════════════════════════════════════════
def render_biometric_gate():
    st.markdown("""
    <div class="bio-gate slide-in">
      <div class="bio-logo">🏛</div>
      <div class="bio-brand">Neo<span>Vault</span></div>
      <div class="bio-tagline">SECURE OFFICER ACCESS PORTAL · v4.2.1</div>
    </div>
    """, unsafe_allow_html=True)

    col_face, col_otp = st.columns(2, gap="medium")

    # ── Webcam / Face auth ──────────────────────────────────────
    with col_face:
        st.markdown("""
        <div class="nv-card" style="text-align:center;">
          <div class="section-eyebrow">Primary Auth</div>
          <div class="section-title" style="font-size:1rem;">Face Biometric</div>
          <div class="scan-frame" style="margin-bottom:14px;">
            <span class="face-icon">👤</span>
            <div class="scan-overlay"><div class="scan-line"></div></div>
          </div>
          <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:14px;">
            Position your face within the ring.<br>Aadhaar biometric record will be matched.
          </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("📸 Capture & Authenticate", use_container_width=True, type="primary"):
            with st.spinner("Initialising camera…"):
                time.sleep(0.6)
            
            # Attempt real webcam capture via OpenCV
            face_captured = False
            try:
                import cv2
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    ret, frame = cap.read()
                    cap.release()
                    if ret:
                        face_captured = True
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        st.image(frame_rgb, caption="Captured Frame", use_container_width=True)
            except Exception:
                pass   # OpenCV not available or no camera → fall through to simulation

            # Scanning animation simulation
            progress_bar = st.progress(0)
            status_text  = st.empty()
            stages = [
                (20,  "🔍 Detecting facial landmarks…"),
                (45,  "🔐 Encrypting biometric hash…"),
                (70,  "☁  Querying Aadhaar UIDAI API…"),
                (90,  "✅ Verifying liveness probe…"),
                (100, "🎯 Identity confirmed!"),
            ]
            for pct, msg in stages:
                progress_bar.progress(pct)
                status_text.markdown(
                    f'<div style="font-family:var(--mono);font-size:0.72rem;color:var(--blue);text-align:center;">{msg}</div>',
                    unsafe_allow_html=True)
                time.sleep(0.4)

            time.sleep(0.3)
            progress_bar.empty(); status_text.empty()

            st.session_state.authenticated = True
            st.session_state.auth_method   = "Face Biometric" + (" (Webcam)" if face_captured else " (Simulated)")
            st.success("✅ Aadhaar biometric verified. Access granted.")
            time.sleep(0.8)
            st.rerun()

    # ── OTP fallback ────────────────────────────────────────────
    with col_otp:
        st.markdown("""
        <div class="nv-card">
          <div class="section-eyebrow">Fallback Auth</div>
          <div class="section-title" style="font-size:1rem;">Aadhaar OTP</div>
          <p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:14px;">
            Enter your registered Aadhaar-linked mobile number to receive a one-time password.
          </p>
        </div>
        """, unsafe_allow_html=True)

        phone = st.text_input("📱 Mobile Number (linked to Aadhaar)", placeholder="+91 98765 43210",
                               label_visibility="visible")

        if st.button("Send OTP →", use_container_width=True):
            if phone and len(phone.replace(" ", "").replace("+91", "")) >= 10:
                st.session_state.otp_sent  = True
                st.session_state.mock_otp  = str(random.randint(100000, 999999))
                st.info(f"📨 OTP sent to {phone}. *(Demo OTP: `{st.session_state.mock_otp}`)*")
            else:
                st.warning("Please enter a valid 10-digit mobile number.")

        if st.session_state.otp_sent:
            st.markdown('<div class="otp-label">Enter 6-digit OTP</div>', unsafe_allow_html=True)
            otp_input = st.text_input("OTP", max_chars=6, label_visibility="collapsed",
                                       placeholder="● ● ● ● ● ●")
            if st.button("✔ Verify OTP", use_container_width=True, type="primary"):
                if otp_input == st.session_state.mock_otp:
                    st.session_state.authenticated = True
                    st.session_state.auth_method   = "Aadhaar OTP"
                    st.success("✅ OTP verified. Access granted.")
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.error("❌ Invalid OTP. Please try again.")


# ══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:16px 0 8px;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
            <span style="font-size:1.4rem;">🏛</span>
            <div>
              <div style="font-size:1rem;font-weight:800;letter-spacing:-0.03em;color:var(--text-primary);">
                Neo<span style="color:var(--blue);">Vault</span>
              </div>
              <div style="font-family:var(--mono);font-size:0.55rem;color:var(--text-muted);letter-spacing:0.15em;">
                CLAIM OPERATIONS DESK
              </div>
            </div>
          </div>
        </div>
        <hr class="sidebar-divider">
        """, unsafe_allow_html=True)

        pages = [
            ("dashboard",   "📊", "Dashboard"),
            ("verify",      "🔍", "Verify Claim"),
            ("records",     "📋", "Bank Records"),
        ]
        for page_id, icon, label in pages:
            is_active = st.session_state.page == page_id
            cls = "nav-item active" if is_active else "nav-item"
            if st.button(f"{icon}  {label}", key=f"nav_{page_id}",
                          use_container_width=True,
                          type="primary" if is_active else "secondary"):
                st.session_state.page = page_id
                st.rerun()

        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

        # ── Auth status ──────────────────────────────────────────
        if st.session_state.authenticated:
            method = st.session_state.auth_method or "Biometric"
            st.markdown(f"""
            <div style="padding:12px 14px;background:rgba(16,185,129,0.08);
                        border:1px solid rgba(16,185,129,0.2);border-radius:10px;margin-bottom:12px;">
              <div style="font-family:var(--mono);font-size:0.58rem;letter-spacing:0.12em;
                          color:var(--emerald);margin-bottom:4px;">SESSION ACTIVE</div>
              <div style="font-size:0.78rem;font-weight:600;color:var(--text-primary);">Officer: Arjun Mehta</div>
              <div style="font-family:var(--mono);font-size:0.62rem;color:var(--text-muted);">
                Auth: {method}
              </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔒 Sign Out", use_container_width=True):
                for k in ["authenticated","auth_method","otp_sent","mock_otp",
                           "verify_result","disbursed"]:
                    st.session_state[k] = False if k=="authenticated" else None
                st.session_state.page = "dashboard"
                st.rerun()

        # ── System health ────────────────────────────────────────
        st.markdown("""
        <div style="margin-top:8px;">
          <div class="section-eyebrow" style="padding:0 4px;">System Health</div>
          <div class="nv-card" style="padding:14px;">
        """, unsafe_allow_html=True)

        health_items = [
            ("OCR Engine",     98, "#10B981"),
            ("DB Connection",  100,"#10B981"),
            ("Fraud Engine",   95, "#3B82F6"),
            ("API Gateway",    87, "#F59E0B"),
        ]
        for label, pct, color in health_items:
            st.markdown(f"""
            <div class="health-item">
              <span style="font-size:0.75rem;color:var(--slate);">{label}</span>
              <div class="health-bar-wrap">
                <div class="health-bar" style="width:{pct}%;background:{color};"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

        # ── Timestamp ────────────────────────────────────────────
        st.markdown(f"""
        <div style="margin-top:16px;padding:0 4px;">
          <div style="font-family:var(--mono);font-size:0.58rem;color:var(--text-muted);">
            {datetime.now().strftime("IST %H:%M:%S · %d %b %Y")}
          </div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════
def render_dashboard(df):
    st.markdown("""
    <div class="slide-in">
      <div class="section-eyebrow">Operations Overview</div>
      <div style="font-size:1.5rem;font-weight:800;letter-spacing:-0.03em;
                  color:var(--text-primary);margin-bottom:24px;">
        Dashboard
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI row ──────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    kpi_data = [
        (k1, "📂", "Pending Claims",    str(len(df)),    "accounts in queue",    "#3B82F6"),
        (k2, "✅", "Verified Today",    "3",             "claims processed",      "#10B981"),
        (k3, "⚠️", "Flagged",           "1",             "manual review needed",  "#F59E0B"),
        (k4, "💰", "Total Liability",   f"₹{df['Balance'].sum()/100000:.1f}L",
                                                           "across all accounts",   "#A78BFA"),
    ]
    for col, icon, label, val, sub, color in kpi_data:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-accent" style="background:{color};"></div>
              <span class="kpi-icon">{icon}</span>
              <div class="kpi-label">{label}</div>
              <div class="kpi-value" style="color:{color};">{val}</div>
              <div class="kpi-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_pending, col_activity = st.columns([1.2, 0.8], gap="medium")

    # ── Pending claims table ─────────────────────────────────────
    with col_pending:
        st.markdown("""
        <div class="section-eyebrow">Claim Queue</div>
        <div class="section-title">Pending Verification</div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="nv-card" style="padding:0;overflow:hidden;">', unsafe_allow_html=True)
        display_df = df[["Account_No","Deceased_Name","Nominee_Name","Balance"]].copy()
        display_df["Balance"] = display_df["Balance"].apply(lambda x: f"₹ {x:,.2f}")
        display_df.columns    = ["Account No", "Deceased", "Nominee", "Balance"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Activity timeline ────────────────────────────────────────
    with col_activity:
        st.markdown("""
        <div class="section-eyebrow">Audit Log</div>
        <div class="section-title">Recent Activity</div>
        """, unsafe_allow_html=True)
        timeline_events = [
            ("✅", "#10B981", "Claim Verified",    "RAMESH PRASAD · ₹85,000",   "09:42 AM"),
            ("💸", "#3B82F6", "Disbursement Sent", "ANITA SHARMA · ₹2.1L",      "09:15 AM"),
            ("⚠️", "#F59E0B", "Fraud Flag Raised", "Unknown Cert · Review",     "08:55 AM"),
            ("🔐", "#A78BFA", "Officer Login",     "Arjun Mehta · Face Auth",   "08:31 AM"),
            ("📋", "#64748B", "Records Updated",   "3 new accounts synced",      "Yesterday"),
        ]
        st.markdown('<div class="nv-card">', unsafe_allow_html=True)
        for icon, color, title, desc, t in timeline_events:
            st.markdown(f"""
            <div class="timeline-step">
              <div class="tl-dot" style="background:rgba(0,0,0,0.3);border:1px solid {color}20;">
                {icon}
              </div>
              <div class="tl-content">
                <div class="tl-title">{title}</div>
                <div class="tl-desc">{desc}</div>
                <div class="tl-time">{t}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  PAGE: VERIFY CLAIM
# ══════════════════════════════════════════════════════════════════
def render_verify_page(df):
    st.markdown("""
    <div class="slide-in">
      <div class="section-eyebrow">Verification Engine</div>
      <div style="font-size:1.5rem;font-weight:800;letter-spacing:-0.03em;
                  color:var(--text-primary);margin-bottom:6px;">
        Claim Verification
      </div>
      <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:24px;">
        Upload a death certificate image. The OCR engine will extract text and match it
        against the bank records database using fuzzy Trust-Score analysis.
      </p>
    </div>
    """, unsafe_allow_html=True)

    col_upload, col_preview = st.columns([1, 1], gap="medium")

    with col_upload:
        st.markdown('<div class="section-eyebrow">Step 01</div><div class="section-title" style="font-size:1rem;">Upload Certificate</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Death Certificate", type=["png","jpg","jpeg"],
                                     label_visibility="collapsed")

        if uploaded:
            image = Image.open(uploaded)
            with col_preview:
                st.markdown('<div class="section-eyebrow">Preview</div><div class="section-title" style="font-size:1rem;">Certificate Image</div>', unsafe_allow_html=True)
                st.markdown('<div class="nv-card" style="padding:12px;">', unsafe_allow_html=True)
                st.image(image, use_container_width=True)
                st.markdown(f"""
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px;">
                  <div class="metric-hl"><div class="mh-label">File</div><div class="mh-value"
                       style="font-size:0.8rem;word-break:break-all;">{uploaded.name}</div></div>
                  <div class="metric-hl"><div class="mh-label">Dimensions</div><div class="mh-value">
                       {image.width}×{image.height}</div></div>
                  <div class="metric-hl"><div class="mh-label">Mode</div><div class="mh-value">{image.mode}</div></div>
                  <div class="metric-hl"><div class="mh-label">Size</div><div class="mh-value">{uploaded.size/1024:.1f} KB</div></div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-eyebrow">Step 02</div><div class="section-title" style="font-size:1rem;">Run Verification</div>', unsafe_allow_html=True)

        run_btn = st.button("🔍  Run Verification Engine", type="primary",
                             use_container_width=True, disabled=(uploaded is None))

    # ── Verification logic ───────────────────────────────────────
    if run_btn and uploaded:
        image = Image.open(uploaded)

        # ── Stage 1: OCR ─────────────────────────────────────────
        st.markdown("---")
        st.markdown('<div class="section-eyebrow">Processing</div>', unsafe_allow_html=True)

        ocr_prog = st.progress(0)
        ocr_stat = st.empty()
        for pct, msg in [(15,"Loading OCR engine…"),(40,"Preprocessing image…"),
                         (70,"Extracting text…"),(90,"Normalising output…"),(100,"Done!")]:
            ocr_prog.progress(pct)
            ocr_stat.markdown(
                f'<div style="font-family:var(--mono);font-size:0.72rem;color:var(--blue);">{msg}</div>',
                unsafe_allow_html=True)
            time.sleep(0.35)

        try:
            ocr_engine = load_ocr_engine()
            ocr_text, raw_ocr = extract_text_from_image(ocr_engine, image)
        except Exception as e:
            ocr_prog.empty(); ocr_stat.empty()
            st.error(f"OCR Engine error: {e}")
            return

        ocr_prog.empty(); ocr_stat.empty()

        # ── Stage 2: Fuzzy match ─────────────────────────────────
        with st.spinner("Running Trust-Score Engine…"):
            time.sleep(0.4)
            result = compute_trust_score(ocr_text, df)

        # ── Stage 3: Fraud detection ─────────────────────────────
        with st.spinner("Running fraud heuristics…"):
            time.sleep(0.3)
            fraud_flags = run_fraud_checks(ocr_text, image)

        # Store result in session state
        st.session_state.verify_result = {
            "result":      result,
            "fraud_flags": fraud_flags,
            "ocr_text":    ocr_text,
            "raw_ocr":     raw_ocr,
        }
        st.session_state.disbursed = False
        st.rerun()

    # ── Render stored results ────────────────────────────────────
    if st.session_state.verify_result:
        vr   = st.session_state.verify_result
        res  = vr["result"]
        row  = res["matched_row"]
        score= res["score"]
        grade= res["grade"]

        st.markdown("---")

        # ── Trust score + result header ───────────────────────────
        col_ring, col_info = st.columns([0.35, 0.65], gap="medium")
        with col_ring:
            st.markdown(trust_ring_html(score, grade), unsafe_allow_html=True)

        with col_info:
            grade_labels = {
                "EXACT":    ("tag-emerald", "EXACT MATCH"),
                "HIGH":     ("tag-blue",    "HIGH CONFIDENCE"),
                "PARTIAL":  ("tag-amber",   "PARTIAL MATCH"),
                "LOW":      ("tag-amber",   "LOW CONFIDENCE"),
                "NO_MATCH": ("tag-rose",    "NO MATCH"),
            }
            tag_cls, tag_txt = grade_labels.get(grade, ("tag-blue", grade))
            st.markdown(f"""
            <div style="margin-top:8px;">
              <span class="tag {tag_cls}">{tag_txt}</span>
              <div style="font-size:1.1rem;font-weight:700;margin:10px 0 6px;color:var(--text-primary);">
                {"✅ Record Found" if row is not None else "❌ No Matching Record"}
              </div>
              <div style="font-size:0.82rem;color:var(--slate);line-height:1.6;">
                {res['explanation']}
              </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Fraud flags ───────────────────────────────────────────
        if vr["fraud_flags"]:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-eyebrow">Fraud Detection</div>', unsafe_allow_html=True)
            for flag in vr["fraud_flags"]:
                icon  = "🚨" if flag["level"] == "CRITICAL" else "⚠️"
                color = "var(--rose)" if flag["level"] == "CRITICAL" else "var(--amber)"
                st.markdown(f"""
                <div class="fraud-alert">
                  <div class="fa-title">{icon} {flag['level']} — {flag['title']}</div>
                  <div class="fa-body">{flag['detail']}</div>
                </div>
                """, unsafe_allow_html=True)

        # ── Match details (if found) ──────────────────────────────
        if row is not None:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-eyebrow">Matched Record</div>', unsafe_allow_html=True)
            c1, c2, c3, c4, c5 = st.columns(5)
            fields = [
                (c1, "Deceased",    row["Deceased_Name"]),
                (c2, "Nominee",     row["Nominee_Name"]),
                (c3, "Relation",    row["Relation"]),
                (c4, "Account No",  row["Account_No"]),
                (c5, "Balance",     f"₹ {float(row['Balance']):,.2f}"),
            ]
            for col, label, val in fields:
                with col:
                    st.markdown(f"""
                    <div class="metric-hl">
                      <div class="mh-label">{label}</div>
                      <div class="mh-value">{val}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # ── Settlement summary ────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-eyebrow">Final Settlement</div>', unsafe_allow_html=True)
            settlement = compute_settlement(float(row["Balance"]))
            claim_id   = f"NV-{row['Account_No']}-{datetime.now().strftime('%Y%m%d')}"

            st.markdown(f"""
            <div class="settlement-card">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <div>
                  <div style="font-size:1rem;font-weight:700;">Settlement Summary</div>
                  <div style="font-family:var(--mono);font-size:0.62rem;color:var(--text-muted);">
                    Claim ID: {claim_id}
                  </div>
                </div>
                <span class="tag tag-emerald">READY FOR DISBURSEMENT</span>
              </div>
              <div class="settlement-line">
                <span class="item">Principal Balance</span>
                <span class="amount" style="color:var(--text-primary);">
                  ₹ {settlement['principal']:,.2f}</span>
              </div>
              <div class="settlement-line">
                <span class="item">Accrued Interest
                  <span style="font-family:var(--mono);font-size:0.65rem;color:var(--text-muted);">
                    ({settlement['rate_pct']}% p.a. · {settlement['days']} days)</span>
                </span>
                <span class="amount" style="color:var(--emerald);">
                  + ₹ {settlement['interest']:,.2f}</span>
              </div>
              <div class="settlement-line">
                <span class="item">TDS Deduction (10% on interest)</span>
                <span class="amount" style="color:var(--rose);">
                  − ₹ {settlement['tds']:,.2f}</span>
              </div>
              <div class="settlement-total">
                <span class="label">NET PAYOUT TO NOMINEE</span>
                <span class="amount">₹ {settlement['net_payout']:,.2f}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if not st.session_state.disbursed:
                disburse_btn = st.button("💸  Disburse Now", type="primary",
                                          use_container_width=True)
                if disburse_btn:
                    with st.spinner("Initiating fund transfer…"):
                        time.sleep(1.2)
                    st.session_state.disbursed = True
                    st.rerun()

            else:
                # ── Confetti + success ────────────────────────────
                confetti_html = ""
                colors_conf   = ["#3B82F6","#10B981","#F59E0B","#A78BFA","#F43F5E","#FFFFFF"]
                for i in range(60):
                    left  = random.randint(0, 100)
                    delay = random.uniform(0, 1.5)
                    dur   = random.uniform(2, 4)
                    color = random.choice(colors_conf)
                    shape = "border-radius:50%;" if random.random() > 0.5 else ""
                    confetti_html += (
                        f'<div class="confetti-piece" style="left:{left}%;'
                        f'background:{color};{shape}'
                        f'animation-duration:{dur:.1f}s;animation-delay:{delay:.2f}s;"></div>'
                    )
                st.markdown(confetti_html, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="settlement-card" style="text-align:center;border-color:rgba(16,185,129,0.4);">
                  <div style="font-size:2.5rem;margin-bottom:8px;">🎉</div>
                  <div style="font-size:1.2rem;font-weight:800;color:var(--emerald);margin-bottom:4px;">
                    Transaction Successful
                  </div>
                  <div style="font-family:var(--mono);font-size:0.7rem;color:var(--text-muted);
                              margin-bottom:16px;">
                    TXN ID: NVB{random.randint(100000000, 999999999)} ·
                    {datetime.now().strftime("%d %b %Y %H:%M:%S")} IST
                  </div>
                  <div style="font-size:2rem;font-weight:800;color:var(--text-primary);
                              font-family:var(--mono);letter-spacing:-0.03em;">
                    ₹ {settlement['net_payout']:,.2f}
                  </div>
                  <div style="font-size:0.82rem;color:var(--slate);margin-top:6px;">
                    Credited to {row['Nominee_Name']} ({row['Relation']})
                  </div>
                </div>
                """, unsafe_allow_html=True)

                # ── PDF download ──────────────────────────────────
                pdf_bytes = generate_pdf_receipt(row, settlement, claim_id)
                ext       = "pdf" if pdf_bytes[:4] == b'%PDF' else "txt"
                st.download_button(
                    label="⬇  Download Settlement Receipt",
                    data=pdf_bytes,
                    file_name=f"settlement_{claim_id}.{ext}",
                    mime="application/pdf" if ext == "pdf" else "text/plain",
                    use_container_width=True,
                )

        # ── OCR debug expander ────────────────────────────────────
        with st.expander("🔬 Debug — Raw OCR Output"):
            st.markdown(f'<div class="ocr-dump">{vr["ocr_text"] or "[No text extracted]"}</div>',
                         unsafe_allow_html=True)
            if vr.get("raw_ocr"):
                st.markdown("**Top tokens with confidence:**")
                top_tokens = sorted(vr["raw_ocr"], key=lambda x: -x[2])[:10]
                for _, text, conf in top_tokens:
                    st.markdown(
                        f'<span style="font-family:var(--mono);font-size:0.72rem;">'
                        f'`{text}` <span style="color:var(--emerald);">{conf:.0%}</span></span>  ',
                        unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  PAGE: BANK RECORDS
# ══════════════════════════════════════════════════════════════════
def render_records_page(df):
    st.markdown("""
    <div class="slide-in">
      <div class="section-eyebrow">Database</div>
      <div style="font-size:1.5rem;font-weight:800;letter-spacing:-0.03em;
                  color:var(--text-primary);margin-bottom:24px;">
        Bank Records
      </div>
    </div>
    """, unsafe_allow_html=True)

    total_liability = df["Balance"].sum()
    avg_balance     = df["Balance"].mean()

    c1, c2, c3 = st.columns(3)
    for col, icon, label, val, color in [
        (c1, "🗄", "Total Records",    str(len(df)),                "#3B82F6"),
        (c2, "💰", "Total Liability",  f"₹ {total_liability:,.2f}", "#10B981"),
        (c3, "📊", "Avg Balance",      f"₹ {avg_balance:,.2f}",    "#A78BFA"),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-accent" style="background:{color};"></div>
              <span class="kpi-icon">{icon}</span>
              <div class="kpi-label">{label}</div>
              <div class="kpi-value" style="color:{color};">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    display = df.copy()
    display["Balance"] = display["Balance"].apply(lambda x: f"₹ {x:,.2f}")
    st.dataframe(display, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════
#  MAIN ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════
def main():
    df = load_bank_records()

    # ── Gate: records check ──────────────────────────────────────
    if df is None:
        st.error("**`bank_records.csv` not found** — place it in the same directory as `app.py`.",
                 icon="🚨")
        st.stop()

    # ── Gate: biometric auth ─────────────────────────────────────
    if not st.session_state.authenticated:
        render_biometric_gate()
        return

    # ── Authenticated: render sidebar + page ─────────────────────
    render_sidebar()

    page = st.session_state.page
    if page == "dashboard":
        render_dashboard(df)
    elif page == "verify":
        render_verify_page(df)
    elif page == "records":
        render_records_page(df)


if __name__ == "__main__":
    main()
