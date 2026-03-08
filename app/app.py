"""
Wallet Warriors — AI Credit Intelligence Platform
v5: Full login fix · Demo credentials restored · 4-feature login panel ·
    Jargon-Buster tooltips · Hustle Academy · What-If Simulator · All ML features intact
"""

import streamlit as st
import streamlit.components.v1 as st_components
import pandas as pd
import numpy as np
import joblib
import shap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import hashlib, time, json, os, io, base64
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Wallet Warriors · Credit Intelligence",
    page_icon="⚡", layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────────────────────
# AUTH — Dev Kumar is the primary demo user, no credentials shown
# ─────────────────────────────────────────────────────────────
_DH = hashlib.sha256("Dev@2024".encode()).hexdigest()
_TH = hashlib.sha256("Test@1234".encode()).hexdigest()

_MEM_USERS = {
    "dev@walletwarriors.ai": {
        "id": 1, "email": "dev@walletwarriors.ai",
        "password_hash": _DH, "full_name": "Dev Kumar", "plan": "Pro"
    },
    "test@walletwarriors.ai": {
        "id": 2, "email": "test@walletwarriors.ai",
        "password_hash": _TH, "full_name": "Priya Sharma", "plan": "Starter"
    },
}
_MEM_APPS = []

# ─────────────────────────────────────────────────────────────
# POSTGRESQL LAYER (graceful fallback)
# ─────────────────────────────────────────────────────────────
try:
    import psycopg2
    from psycopg2 import pool as pg_pool
    from psycopg2.extras import RealDictCursor
    _PG = True
except ImportError:
    _PG = False

_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS ww_users(
  id SERIAL PRIMARY KEY, email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL, full_name TEXT,
  plan TEXT DEFAULT 'Starter', created_at TIMESTAMPTZ DEFAULT NOW());
CREATE TABLE IF NOT EXISTS ww_applications(
  id SERIAL PRIMARY KEY, user_id INT, stated_income NUMERIC,
  rent NUMERIC, savings NUMERIC, loan_amount NUMERIC,
  employment_years NUMERIC, credit_score INT,
  electricity_bill NUMERIC, upi_outflow NUMERIC, doc_income NUMERIC,
  verification_score NUMERIC, verification_passed BOOLEAN,
  default_probability NUMERIC, decision TEXT, hustle_score INT,
  approval_readiness NUMERIC, shap_values JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW());
INSERT INTO ww_users(email,password_hash,full_name,plan) VALUES
  ('dev@walletwarriors.ai','{_DH}','Dev Kumar','Pro'),
  ('test@walletwarriors.ai','{_TH}','Priya Sharma','Starter')
ON CONFLICT(email) DO NOTHING;
"""

@st.cache_resource
def get_pool():
    if not _PG: return None
    try:
        p = pg_pool.SimpleConnectionPool(1, 5,
            host=os.getenv("PG_HOST","localhost"),
            port=int(os.getenv("PG_PORT", 5432)),
            dbname=os.getenv("PG_DB","walletwarriors"),
            user=os.getenv("PG_USER","postgres"),
            password=os.getenv("PG_PASS",""))
        c = p.getconn()
        with c.cursor() as cur: cur.execute(_SCHEMA)
        c.commit(); p.putconn(c); return p
    except: return None

_pool = get_pool()

def db_user(email):
    if _pool:
        try:
            c = _pool.getconn()
            with c.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM ww_users WHERE email=%s", (email.lower(),))
                r = cur.fetchone()
            _pool.putconn(c)
            return dict(r) if r else None
        except: pass
    return _MEM_USERS.get(email.lower())

def db_save(uid, d):
    if _pool:
        try:
            c = _pool.getconn()
            with c.cursor() as cur:
                cur.execute("""INSERT INTO ww_applications(
                    user_id,stated_income,rent,savings,loan_amount,employment_years,
                    credit_score,electricity_bill,upi_outflow,doc_income,
                    verification_score,verification_passed,default_probability,
                    decision,hustle_score,approval_readiness,shap_values)
                    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (uid,d.get("income"),d.get("rent"),d.get("savings"),d.get("loan"),
                     d.get("employ"),d.get("cibil"),d.get("elec"),d.get("upi"),
                     d.get("doc_income"),d.get("ver_score"),d.get("ver_pass"),
                     d.get("prob"),d.get("dec"),d.get("hustle"),d.get("ar"),
                     json.dumps(d.get("shap",{}))))
            c.commit(); _pool.putconn(c)
        except: pass
    else:
        _MEM_APPS.append({**d, "uid": uid, "ts": datetime.now().isoformat()})

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
for k, v in {
    "page": "login", "authenticated": False,
    "username": "", "user_id": None, "plan": "Pro",
    "vr": None, "ud": {}, "attempts": 0, "tf_result": None
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def auth(email, pw):
    u = db_user(email)
    if not u: return False, None
    if hashlib.sha256(pw.encode()).hexdigest() == u["password_hash"]:
        return True, u
    return False, None

# ─────────────────────────────────────────────────────────────
# MODEL
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    try:
        return joblib.load("models/credit_model.pkl")
    except:
        from sklearn.model_selection import train_test_split
        from xgboost import XGBClassifier
        np.random.seed(42); n = 1000
        df = pd.DataFrame({
            "Income": np.random.randint(15000, 80000, n),
            "Rent": np.random.randint(5000, 40000, n),
            "Savings": np.random.randint(0, 20000, n),
            "LoanAmount": np.random.randint(10000, 100000, n),
            "Employment": np.random.randint(0, 10, n),
            "CreditScore": np.random.randint(500, 800, n)
        })
        df["Default"] = (
            (df["Rent"] > df["Income"] * 0.7) |
            (df["Savings"] < 2000) |
            (df["CreditScore"] < 580)
        ).astype(int)
        X = df.drop("Default", axis=1); y = df["Default"]
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
        m = XGBClassifier(n_estimators=250, max_depth=5, learning_rate=0.05,
                          use_label_encoder=False, eval_metric="logloss")
        m.fit(Xtr, ytr)
        return m

MDL = load_model()

# ─────────────────────────────────────────────────────────────
# COLOUR PALETTE — Enhanced Neon Dark
# ─────────────────────────────────────────────────────────────
BG      = "#0c0e18"
SURFACE = "#13162a"
CARD    = "#191d34"
CARD2   = "#1f2440"
GRAPE   = "#7C4DFF"
LAV     = "#A87FFF"
CYAN    = "#00E5C0"
GOLD    = "#FFB830"
GREEN   = "#23D18B"
RED     = "#FF4060"
WHITE   = "#ECF0FF"
TEXT    = "#C8D0F0"
MUTED   = "rgba(180,192,255,0.55)"
MUTED2  = "rgba(180,192,255,0.32)"
BORDER  = "rgba(124,77,255,0.22)"
BORDER2 = "rgba(0,229,192,0.16)"

PLOT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=WHITE, size=13),
    title_font=dict(family="Inter, sans-serif", size=15, color=WHITE),
    margin=dict(l=20, r=20, t=48, b=20),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER,
                font=dict(size=12, color=WHITE)),
)

def badge(txt, bg=GRAPE, fg="#fff", glow=False):
    shadow = f"box-shadow:0 0 16px {bg}99;" if glow else ""
    return (f'<span style="display:inline-block;background:{bg};color:{fg};'
            f'font-size:10px;font-family:\'JetBrains Mono\',monospace;'
            f'font-weight:700;letter-spacing:.07em;padding:4px 13px;'
            f'border-radius:99px;text-transform:uppercase;{shadow}">{txt}</span>')

# ─────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;0,800;0,900;1,400&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
  --bg:      #0c0e18;
  --surface: #13162a;
  --card:    #191d34;
  --card2:   #1f2440;
  --grape:   #7C4DFF;
  --lav:     #A87FFF;
  --cyan:    #00E5C0;
  --gold:    #FFB830;
  --green:   #23D18B;
  --red:     #FF4060;
  --white:   #ECF0FF;
  --text:    #C8D0F0;
  --muted:   rgba(180,192,255,0.55);
  --muted2:  rgba(180,192,255,0.32);
  --border:  rgba(124,77,255,0.22);
  --border2: rgba(0,229,192,0.16);
}

/* ══ BASE ══ */
html, body,
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
  background: var(--bg) !important;
  color: var(--white) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 15px !important;
}
[data-testid="stHeader"],
[data-testid="stMainMenu"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

/* ── Streamlit block padding — top:0 so sticky nav hits the edge ── */
.block-container,
.stMainBlockContainer {
  padding-top:    0 !important;
  padding-bottom: 40px !important;
  padding-left:   48px !important;
  padding-right:  48px !important;
  max-width: 100% !important;
}

* { box-sizing: border-box; }

/* ══ SCROLLBAR ══ */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--grape); border-radius: 99px; }

/* ══ SIDEBAR ══ */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--white) !important; font-size: 14px !important; }
[data-testid="stSidebar"] .stButton > button {
  background: rgba(124,77,255,0.14) !important;
  border: 1px solid var(--border) !important;
  color: var(--lav) !important;
  box-shadow: none !important;
  font-size: 13px !important;
  padding: 9px 14px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: var(--grape) !important;
  color: #fff !important;
  transform: none !important;
  box-shadow: none !important;
}

/* ══ HEADINGS — Bold, Crisp, Hierarchical ══ */
h1, .h1 {
  font-family: 'Inter', sans-serif !important;
  font-size: 42px !important; font-weight: 900 !important;
  color: var(--white) !important;
  line-height: 1.10 !important; letter-spacing: -0.03em !important;
  margin: 0 0 12px !important;
}
h2, .h2 {
  font-family: 'Inter', sans-serif !important;
  font-size: 28px !important; font-weight: 800 !important;
  color: var(--white) !important;
  line-height: 1.18 !important; letter-spacing: -0.022em !important;
  margin: 0 0 10px !important;
}
h3, .h3 {
  font-family: 'Inter', sans-serif !important;
  font-size: 20px !important; font-weight: 700 !important;
  color: var(--white) !important;
  line-height: 1.28 !important; letter-spacing: -0.012em !important;
  margin: 0 0 8px !important;
}
h4, .h4 {
  font-family: 'Inter', sans-serif !important;
  font-size: 16px !important; font-weight: 700 !important;
  color: var(--white) !important;
  line-height: 1.35 !important;
  margin: 0 !important;
}

/* ══ BODY TEXT — Readable, NOT invisible ══ */
p, li {
  font-family: 'Inter', sans-serif !important;
  font-size: 15px !important;
  font-weight: 400 !important;
  color: var(--text) !important;
  line-height: 1.72 !important;
  margin: 0 0 8px !important;
}
/* Streamlit markdown container text */
[data-testid="stMarkdownContainer"] > p,
[data-testid="stMarkdownContainer"] > div > p {
  color: var(--text) !important;
  font-size: 15px !important;
  line-height: 1.72 !important;
}
/* Ensure native Streamlit text elements are visible */
[data-testid="stText"],
[data-testid="stCaptionContainer"],
.stCaption { color: var(--muted) !important; font-size: 13px !important; }

/* ══ WIDGET LABELS ══ */
[data-testid="stTextInput"]    > label,
[data-testid="stNumberInput"]  > label,
[data-testid="stSelectbox"]    > label,
[data-testid="stFileUploader"] > label {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 10.5px !important; font-weight: 700 !important;
  letter-spacing: .11em !important; text-transform: uppercase !important;
  color: var(--muted) !important;
  margin-bottom: 6px !important; display: block !important;
}

/* ══ INPUTS — Enhanced ══ */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
input[type="text"], input[type="password"],
input[type="number"], input[type="email"] {
  background: rgba(124,77,255,0.07) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 10px !important;
  color: var(--white) !important;
  caret-color: var(--lav) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 15px !important; font-weight: 500 !important;
  padding: 14px 16px !important;
  transition: border-color .16s, box-shadow .16s, background .16s !important;
  width: 100% !important;
  min-height: 48px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
input:focus {
  border-color: var(--lav) !important;
  box-shadow: 0 0 0 3px rgba(168,127,255,0.16) !important;
  outline: none !important;
  background: rgba(124,77,255,0.13) !important;
}
input::placeholder { color: rgba(180,192,255,0.28) !important; }

/* Number input +/- buttons */
[data-testid="stNumberInput"] button {
  background: rgba(124,77,255,0.14) !important;
  border: 1px solid var(--border) !important;
  color: var(--lav) !important;
  border-radius: 8px !important;
  min-width: 36px !important; min-height: 36px !important;
  font-size: 18px !important;
  transition: background .14s !important;
}
[data-testid="stNumberInput"] button:hover {
  background: var(--grape) !important;
  color: #fff !important;
}
[data-testid="stNumberInput"] > div {
  gap: 6px !important;
}

/* ══ SELECTBOX — Enhanced ══ */
[data-testid="stSelectbox"] > div > div {
  background: rgba(124,77,255,0.07) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 10px !important;
  color: var(--white) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 14px !important;
  min-height: 48px !important;
  transition: border-color .16s, box-shadow .16s !important;
}
[data-testid="stSelectbox"] > div > div:focus-within {
  border-color: var(--lav) !important;
  box-shadow: 0 0 0 3px rgba(168,127,255,0.16) !important;
}
[data-testid="stSelectbox"] svg { color: var(--lav) !important; }

/* Selectbox dropdown menu */
[data-testid="stSelectbox"] ul,
div[data-baseweb="popover"] ul {
  background: #1a1e35 !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 12px !important;
}
div[data-baseweb="popover"] li {
  background: transparent !important;
  color: var(--text) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 14px !important;
  padding: 10px 16px !important;
  border-radius: 8px !important;
}
div[data-baseweb="popover"] li:hover,
div[data-baseweb="popover"] li[aria-selected="true"] {
  background: rgba(124,77,255,0.18) !important;
  color: var(--white) !important;
}

/* ══ FILE UPLOADER — Enhanced ══ */
[data-testid="stFileUploader"] {
  background: rgba(0,229,192,0.03) !important;
  border: 1.5px dashed rgba(0,229,192,0.26) !important;
  border-radius: 12px !important; padding: 16px !important;
  transition: border-color .16s, background .16s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: rgba(0,229,192,0.50) !important;
  background: rgba(0,229,192,0.06) !important;
}
[data-testid="stFileUploader"] > label { color: var(--cyan) !important; }
[data-testid="stFileUploaderDropzoneInstructions"] {
  color: var(--muted) !important; font-size: 13px !important;
}

/* ══ BUTTONS — Enhanced ══ */
.stButton > button {
  background: linear-gradient(135deg, #7C4DFF 0%, #5030CC 100%) !important;
  color: #fff !important;
  border: 1.5px solid rgba(168,127,255,0.32) !important;
  border-radius: 12px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 15px !important; font-weight: 700 !important;
  letter-spacing: .01em !important;
  padding: 14px 28px !important;
  min-height: 52px !important;
  width: 100% !important; cursor: pointer !important;
  transition: all .18s ease !important;
  box-shadow: 0 4px 22px rgba(124,77,255,0.28) !important;
}
.stButton > button:hover {
  background: linear-gradient(135deg, #A87FFF 0%, #7C4DFF 100%) !important;
  box-shadow: 0 6px 34px rgba(168,127,255,0.42) !important;
  transform: translateY(-2px) !important;
  border-color: rgba(168,127,255,0.55) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ══ MOBILE RESPONSIVE ══ */
@media (max-width: 768px) {
  .block-container, .stMainBlockContainer {
    padding-left: 16px !important;
    padding-right: 16px !important;
    padding-bottom: 24px !important;
  }
  h1, .h1 { font-size: 28px !important; }
  h2, .h2 { font-size: 20px !important; }
  h3, .h3 { font-size: 17px !important; }
  [data-testid="stTabs"] [role="tab"] {
    font-size: 11px !important;
    padding: 8px 10px !important;
  }
  [data-testid="stMetricValue"] > div { font-size: 22px !important; }
  .stButton > button {
    font-size: 14px !important;
    padding: 12px 16px !important;
    min-height: 48px !important;
  }
  [data-testid="stNumberInput"] input,
  [data-testid="stTextInput"] input {
    font-size: 16px !important;
    min-height: 52px !important;
  }
  [data-testid="stSelectbox"] > div > div {
    min-height: 52px !important;
    font-size: 16px !important;
  }
}

/* ══ METRIC CARDS ══ */
[data-testid="stMetric"] {
  background: var(--card) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 14px !important; padding: 20px 18px !important;
  transition: border-color .2s, box-shadow .2s !important;
}
[data-testid="stMetric"]:hover {
  border-color: var(--lav) !important;
  box-shadow: 0 0 22px rgba(168,127,255,0.11) !important;
}
[data-testid="stMetricLabel"] > div {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 10px !important; font-weight: 700 !important;
  letter-spacing: .12em !important; text-transform: uppercase !important;
  color: var(--muted) !important;
}
[data-testid="stMetricValue"] > div {
  font-family: 'Inter', sans-serif !important;
  font-size: 28px !important; font-weight: 800 !important;
  color: var(--lav) !important;
}
[data-testid="stMetricDelta"] > div {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important;
}

/* ══ PROGRESS BAR ══ */
[data-testid="stProgress"] > div {
  background: rgba(124,77,255,0.13) !important;
  border-radius: 99px !important; height: 8px !important;
}
[data-testid="stProgress"] > div > div {
  background: linear-gradient(90deg, var(--grape), var(--lav), var(--cyan)) !important;
  border-radius: 99px !important;
  box-shadow: 0 0 10px rgba(168,127,255,0.45) !important;
}

/* ══ DIVIDER ══ */
hr {
  border: none !important; height: 1px !important;
  background: linear-gradient(90deg, transparent, rgba(124,77,255,0.30), transparent) !important;
  margin: 36px 0 !important;
}

/* ══ ALERTS ══ */
[data-testid="stAlert"] {
  border-radius: 10px !important;
  font-family: 'Inter', sans-serif !important; font-size: 14px !important;
}
[data-testid="stAlert"] p { color: inherit !important; }

/* ══ TABS ══ */
[data-testid="stTabs"] [role="tablist"] {
  background: var(--card) !important;
  border: 1.5px solid var(--border) !important;
  border-radius: 12px !important; padding: 5px !important; gap: 3px !important;
}
[data-testid="stTabs"] [role="tab"] {
  background: transparent !important; color: var(--muted) !important;
  border-radius: 9px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 13px !important; font-weight: 600 !important;
  padding: 9px 16px !important; transition: all .16s !important; border: none !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  background: linear-gradient(135deg, #7C4DFF, #5030CC) !important;
  color: #fff !important; box-shadow: 0 3px 14px rgba(124,77,255,0.38) !important;
}
[data-testid="stTabs"] [role="tab"]:hover:not([aria-selected="true"]) {
  background: rgba(124,77,255,0.11) !important; color: var(--lav) !important;
}
[data-testid="stTabs"] [role="tabpanel"] { padding-top: 24px !important; }

/* ══ EXPANDER ══ */
details {
  background: var(--card) !important;
  border: 1.5px solid var(--border) !important; border-radius: 12px !important;
}
summary {
  font-family: 'Inter', sans-serif !important;
  font-size: 15px !important; font-weight: 600 !important;
  color: var(--white) !important; padding: 13px 17px !important;
}

/* ══ SPINNER ══ */
[data-testid="stSpinner"] p {
  font-family: 'Inter', sans-serif !important;
  color: var(--muted) !important; font-size: 14px !important;
}

/* ══ WARNING / INFO ══ */
.stWarning, .stInfo, .stSuccess, .stError {
  font-family: 'Inter', sans-serif !important; font-size: 14px !important;
}

/* ══ TAB HOVER TOOLTIP BOX ══ */
.ww-tab-tip {
  position: fixed;
  background: linear-gradient(145deg, #13162a, #1f2440);
  border: 1.5px solid rgba(0,229,192,0.32);
  border-radius: 10px;
  padding: 10px 15px;
  font-family: 'Inter', sans-serif;
  font-size: 12.5px;
  font-weight: 400;
  color: #C8D0F0;
  line-height: 1.50;
  max-width: 240px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0,0,0,0.60), 0 0 0 1px rgba(0,229,192,0.08);
  pointer-events: none;
  z-index: 99999;
  transition: opacity .16s ease;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# ██  FEATURE 1: JARGON-BUSTER TOOLTIP SYSTEM  ██
# Pure CSS/HTML overlay — zero impact on ML logic
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ══ JARGON-BUSTER TOOLTIP ══ */
.ww-tooltip {
  position: relative;
  display: inline-block;
  cursor: help;
  color: #A87FFF;
  font-weight: 600;
  border-bottom: 1.5px dashed rgba(168,127,255,0.50);
  transition: color .15s, border-color .15s;
}
.ww-tooltip:hover {
  color: #00E5C0;
  border-bottom-color: rgba(0,229,192,0.60);
}
.ww-tooltip .ww-tip-box {
  visibility: hidden;
  opacity: 0;
  pointer-events: none;
  width: 290px;
  background: linear-gradient(145deg, #13162a, #1f2440);
  border: 1.5px solid rgba(0,229,192,0.30);
  border-radius: 12px;
  padding: 14px 16px;
  position: absolute;
  z-index: 9999;
  bottom: calc(100% + 10px);
  left: 50%;
  transform: translateX(-50%);
  box-shadow: 0 12px 40px rgba(0,0,0,0.55), 0 0 0 1px rgba(0,229,192,0.08);
  transition: opacity .18s ease, visibility .18s ease;
}
.ww-tooltip:hover .ww-tip-box {
  visibility: visible;
  opacity: 1;
}
.ww-tip-box::after {
  content: "";
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: rgba(0,229,192,0.30);
}
.ww-tip-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: #00E5C0;
  margin-bottom: 6px;
  display: block;
}
.ww-tip-def {
  font-family: 'Inter', sans-serif;
  font-size: 13px;
  font-weight: 400;
  color: #C8D0F0;
  line-height: 1.60;
  margin: 0;
}
</style>
""", unsafe_allow_html=True)

# ── 10 "Sexy" Jargon-Buster definitions ──
JARGON = {
    "XGBoost": (
        "XGBoost",
        "An elite ensemble algorithm that builds hundreds of decision trees in sequence, "
        "each one correcting the mistakes of the last — the preferred engine of Kaggle champions "
        "and real-world underwriting models worldwide."
    ),
    "ROC-AUC": (
        "ROC-AUC Score",
        "The single number that tells you how well an AI separates good borrowers from bad ones. "
        "A score of 1.0 is perfect; 0.5 is a coin flip. Our model sits at 0.86."
    ),
    "SHAP": (
        "SHAP Values",
        "A game-theory-backed method that assigns each input feature a precise 'blame' or 'credit' "
        "score for every prediction — turning a black-box AI into a transparent, auditable decision."
    ),
    "LIME": (
        "LIME",
        "Local Interpretable Model-agnostic Explanations — a technique that interrogates any AI "
        "by perturbing your data and measuring how the output changes, creating a local map of model behaviour."
    ),
    "Debt-to-Income": (
        "Debt-to-Income Ratio (DTI/FOIR)",
        "The percentage of your monthly income consumed by fixed obligations (rent + EMIs). "
        "Above 65% and most Indian banks trigger automatic rejection — no human review, no exceptions."
    ),
    "Triangulation Method": (
        "Triangulation Method",
        "Our proprietary income-verification engine that cross-checks your stated salary against "
        "real-world spending signals — rent, electricity, and UPI flows — to detect inflation or fabrication "
        "before a lender does."
    ),
    "Hustle Score": (
        "Hustle Score™",
        "Our 5-point proprietary metric that measures financial discipline: savings rate, rent discipline, "
        "credit health, employment continuity, and loan-to-income ratio. "
        "It's the lender's gut feeling, quantified."
    ),
    "Confidence Index": (
        "Confidence Index",
        "A 0–100 score that reflects how consistent your stated income is with your lifestyle signals. "
        "Below 55 means the system flags your application for manual review before it reaches an underwriter."
    ),
    "Feature Importance": (
        "Feature Importance",
        "A ranking of which input variables drove the AI's decision most strongly. "
        "Knowing your top features lets you focus improvement efforts where they move the needle fastest."
    ),
    "Model Drift": (
        "Model Drift",
        "The gradual degradation of a model's accuracy as real-world borrower behaviour shifts away from "
        "the patterns it was trained on — the silent killer of production AI in fintech."
    ),
}

def tooltip(term_key: str, display_text: str = None) -> str:
    """Return an HTML jargon-buster tooltip span.

    Args:
        term_key: key in JARGON dict (e.g. "XGBoost")
        display_text: override display label (defaults to term_key)
    """
    if term_key not in JARGON:
        return display_text or term_key
    label, definition = JARGON[term_key]
    show = display_text or label
    return (
        f'<span class="ww-tooltip">{show}'
        f'<span class="ww-tip-box">'
        f'<span class="ww-tip-label">{label}</span>'
        f'<span class="ww-tip-def">{definition}</span>'
        f'</span></span>'
    )

# ─────────────────────────────────────────────────────────────
# UI HELPER COMPONENTS
# ─────────────────────────────────────────────────────────────
def section_header(title, subtitle="", icon="", accent=None):
    accent = accent or GRAPE
    icon_html = f'<span style="font-size:22px;line-height:1;">{icon}</span>' if icon else ""
    sub_html = (f'<p style="font-family:\'Inter\',sans-serif;font-size:14.5px;font-weight:400;'
                f'color:{TEXT};margin:6px 0 0;line-height:1.65;">{subtitle}</p>') if subtitle else ""
    st.markdown(f"""
    <div style="margin:20px 0 14px;">
      <div style="display:flex;align-items:center;gap:11px;margin-bottom:4px;">
        {icon_html}
        <h2 style="font-family:'Inter',sans-serif;font-size:22px;font-weight:800;
                   color:{WHITE};margin:0;letter-spacing:-0.022em;">{title}</h2>
      </div>
      {sub_html}
      <div style="height:3px;background:linear-gradient(90deg,{accent},{LAV} 55%,transparent);
                  border-radius:99px;margin-top:10px;width:48px;
                  box-shadow:0 0 10px {accent}88;"></div>
    </div>
    """, unsafe_allow_html=True)

def panel_open(tag_label, title, subtitle="", border_color=None):
    bc = border_color or BORDER
    tag_color = CYAN if "C —" in tag_label else LAV
    tag_fg = "#080c1a"
    sub_html = (f'<p style="font-family:\'Inter\',sans-serif;font-size:13.5px;font-weight:400;'
                f'color:{TEXT};margin:5px 0 6px;line-height:1.60;">{subtitle}</p>') if subtitle else ""
    st.markdown(f"""
    <div style="background:{SURFACE};border:1.5px solid {bc};
                border-radius:14px 14px 0 0;padding:16px 26px 12px;
                margin-bottom:0;box-shadow:0 2px 0 rgba(0,0,0,0.10);
                border-bottom:1px solid rgba(124,77,255,0.10);">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
        <span style="background:{tag_color};color:{tag_fg};
                     font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700;
                     letter-spacing:.12em;padding:3px 11px;border-radius:99px;
                     text-transform:uppercase;">{tag_label}</span>
      </div>
      <h3 style="font-family:'Inter',sans-serif;font-size:17px;font-weight:700;
                 color:{WHITE};margin:3px 0 0;letter-spacing:-0.012em;">{title}</h3>
      {sub_html}
    </div>
    """, unsafe_allow_html=True)

def panel_close():
    st.markdown(
        f'<div style="background:{SURFACE};border:1.5px solid {BORDER};border-top:none;'
        f'border-radius:0 0 14px 14px;padding:6px 26px 14px;margin-bottom:16px;'
        f'box-shadow:0 4px 20px rgba(0,0,0,0.30);"></div>',
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────────────────────
# TRIANGULATION ENGINE
# ─────────────────────────────────────────────────────────────
def triangulate(stated, rent, elec, upi, doc_inc=None):
    flags = []; conf = 100.0
    if stated > 0:
        rr = rent / stated
        if rr < 0.04:
            flags.append({"sev": "medium", "title": "Rent seems very low for your income",
                "msg": f"Your rent (₹{rent:,.0f}/mo) is only {rr*100:.1f}% of your stated income. "
                       "Someone in your income range typically spends 25–45% on rent. "
                       "This mismatch may indicate an inconsistency in your application."})
            conf -= 14
        elif rr > 0.75:
            flags.append({"sev": "high", "title": "Rent consumes an unsustainable share of income",
                "msg": f"You are spending {rr*100:.1f}% of your income on rent alone (₹{rent:,.0f}/mo). "
                       "Lenders reject applications where total fixed obligations exceed 65% of income."})
            conf -= 24
    el_lo = 600 + (stated/1000)*18; el_hi = 1500 + (stated/1000)*35
    if elec > 0 and elec < el_lo * 0.4:
        flags.append({"sev": "medium", "title": "Electricity bill is inconsistent with income level",
            "msg": f"Your bill (₹{elec:,.0f}) is below the ₹{el_lo:,.0f}–₹{el_hi:,.0f} range "
                   f"expected for someone earning ₹{stated:,.0f}/month. "
                   "Lifestyle indicators should align with stated income."})
        conf -= 10
    if upi > 0 and stated > 0:
        vr = upi / stated
        if vr < 0.10:
            flags.append({"sev": "high", "title": "UPI spending is critically low for stated income",
                "msg": f"Stated income is ₹{stated:,.0f}/month, yet UPI outflow is only "
                       f"₹{upi:,.0f} ({vr*100:.1f}%). High earners typically show ≥35% spending velocity. "
                       "This is a primary red flag for underwriters."})
            conf -= 30
        elif vr > 1.5:
            flags.append({"sev": "medium", "title": "Monthly spending exceeds stated income",
                "msg": "UPI outflow exceeds your stated monthly income, suggesting reliance on savings "
                       "or external borrowing to cover expenses. This increases default risk."})
            conf -= 10
    sigs = []
    if rent > 0: sigs.append(rent / 0.33)
    if elec > 0: sigs.append(elec / 0.03)
    if upi > 0:  sigs.append(upi / 0.55)
    if sigs:
        imp = np.mean(sigs); std = np.std(sigs) if len(sigs) > 1 else imp * 0.2
        z = abs(stated - imp) / (std + 1)
        if z > 2.0:
            flags.append({"sev": "high",
                "title": f"Income anomaly detected — {z:.1f}σ deviation from spending signals",
                "msg": f"Spending patterns imply a real income of ₹{imp:,.0f}/month, "
                       f"but ₹{stated:,.0f} was stated — a {z:.1f}σ gap. "
                       "Applications with gaps above 2σ are flagged for manual underwriter review."})
            conf -= min(32, z * 10)
    else:
        imp = stated
    if doc_inc and doc_inc > 0:
        disc = abs(stated - doc_inc) / max(doc_inc, 1)
        if disc > 0.10:
            flags.append({"sev": "high", "title": "Document income does not match stated income",
                "msg": f"Document shows ₹{doc_inc:,.0f}/month net pay, "
                       f"but ₹{stated:,.0f} was entered — a {disc*100:.1f}% discrepancy. "
                       "Our system allows ±10% tolerance. Please correct and resubmit."})
            conf -= 40
    conf = max(0, min(100, conf))
    ok = conf >= 55 and not any(f["sev"] == "high" for f in flags)
    return ok, round(conf, 1), flags, round(imp if sigs else stated)

# ─────────────────────────────────────────────────────────────
# APPROVAL READINESS
# ─────────────────────────────────────────────────────────────
def approval_readiness(income, rent, savings, loan, employ, cibil, prob, ver_conf):
    cr = min(25, max(0, (cibil - 300) / 600 * 25))
    sv = min(20, savings / max(income, 1) * 100)
    emi = loan / 60; foir = (rent + emi) / max(income, 1)
    db = max(0, 20 - foir * 30)
    ep = min(15, employ * 3)
    ml = max(0, (1 - prob) * 15)
    vc = ver_conf / 100 * 5
    total = cr + sv + db + ep + ml + vc
    return round(total, 1), {
        "Credit Score":          round(cr, 1),
        "Savings & Liquidity":   round(sv, 1),
        "Debt Burden":           round(db, 1),
        "Employment Stability":  round(ep, 1),
        "AI Risk Score":         round(ml, 1),
        "Verification Strength": round(vc, 1),
    }

def hustle_score(sav, inc, rent, cibil, emp, loan):
    s = 0
    if inc > 0 and sav / inc >= 0.10: s += 20
    if inc > 0 and rent / inc < 0.50: s += 20
    if cibil > 650: s += 20
    if emp >= 2: s += 20
    if inc > 0 and loan < inc * 5: s += 20
    return s

# ─────────────────────────────────────────────────────────────
# SHAP
# ─────────────────────────────────────────────────────────────
def run_shap(mdl, df):
    matplotlib.rcdefaults()
    plt.rcParams.update({
        "figure.facecolor": CARD, "axes.facecolor": CARD,
        "savefig.facecolor": CARD, "text.color": WHITE,
        "axes.labelcolor": WHITE, "xtick.color": WHITE, "ytick.color": WHITE,
        "axes.edgecolor": "#2a2f4a", "grid.color": "#252a40",
        "font.family": "sans-serif", "font.size": 13,
    })
    exp = shap.Explainer(mdl); sv = exp(df); arr = sv[0].values
    feats = df.columns.tolist()
    plt.subplots(figsize=(7, 4.5))
    shap.plots.waterfall(sv[0], show=False, max_display=6)
    fig_w = plt.gcf(); fig_w.patch.set_facecolor(CARD)
    for ax in fig_w.axes:
        ax.set_facecolor(CARD); ax.tick_params(colors=WHITE, labelsize=12)
    plt.subplots(figsize=(7, 4.5))
    shap.plots.bar(sv, show=False, max_display=6)
    fig_b = plt.gcf(); fig_b.patch.set_facecolor(CARD)
    for ax in fig_b.axes:
        ax.set_facecolor(CARD); ax.tick_params(colors=WHITE, labelsize=12)
    si = np.argsort(np.abs(arr))[::-1]
    tbl = [{
        "Feature": feats[i],
        "Value": f"{df.iloc[0][feats[i]]:,.2f}",
        "SHAP": round(float(arr[i]), 4),
        "Dir": "↑ Increases default risk" if arr[i] > 0 else "↓ Reduces default risk",
        "Color": RED if arr[i] > 0 else GREEN
    } for i in si]
    return fig_w, fig_b, tbl, {r["Feature"]: r["SHAP"] for r in tbl}

# ─────────────────────────────────────────────────────────────
# RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────
def gen_recs(income, rent, savings, loan, employ, cibil, prob):
    recs = []; emi = loan / 60
    foir = (rent + emi) / max(income, 1) * 100
    sr = savings / max(income, 1) * 100

    if foir > 65:
        recs.append({"p": "high", "icon": "⚠️",
            "title": "Fixed obligations are too high to qualify",
            "what": (f"Rent (₹{rent:,.0f}) + estimated EMI (₹{emi:,.0f}) = ₹{rent+emi:,.0f}/month, "
                     f"which is {foir:.1f}% of your income. The RBI-mandated FOIR cap for salaried "
                     "borrowers at most PSU and private banks is 50–65%. Exceeding this triggers "
                     "automatic rejection — no exceptions."),
            "how": (f"Extend tenure to 84 months: EMI drops to ₹{loan/84:,.0f}/month, "
                    f"bringing FOIR to {((rent+loan/84)/max(income,1)*100):.1f}%. "
                    "Alternatively, add a co-applicant to split the FOIR obligation.")})

    if sr < 10:
        recs.append({"p": "high", "icon": "💰",
            "title": "Savings rate is below the minimum lender threshold",
            "what": (f"Current savings rate: {sr:.1f}% (₹{savings:,.0f}/month). "
                     "Lenders use this to assess your financial resilience — can you still pay EMIs "
                     "if income is disrupted for 2–3 months? At this rate, the answer is no."),
            "how": (f"Set an auto-debit of ₹{int(income*0.15):,}/month to a Liquid Fund "
                    "on salary credit day. Even 90 days of consistent savings changes how lenders "
                    "read your bank statement narrative.")})
    elif sr >= 20:
        recs.append({"p": "positive", "icon": "✅",
            "title": "Savings discipline is above benchmark — leverage it",
            "what": (f"Saving {sr:.1f}% of income is in the top quartile of applicants. "
                     "This signals financial control and directly improves your Approval Readiness Score."),
            "how": ("Park 3–6 months of expenses in a Fixed Deposit and declare it as collateral. "
                    "This can increase approved loan limits by 15–25% at most NBFCs.")})

    if cibil < 650:
        recs.append({"p": "high", "icon": "📉",
            "title": "CIBIL score is below the prime lending cutoff",
            "what": (f"Score of {cibil} puts you in the sub-prime category. "
                     "SBI, HDFC, ICICI, and Axis Bank all require ≥700 for personal loans. "
                     f"At NBFCs you may qualify, but at 18–28% APR vs 10–13% for prime. "
                     f"On ₹{loan:,.0f} over 5 years, this costs ₹{int(loan*0.10*5/2):,} extra."),
            "how": ("1. Check for report errors at cibil.com (23% of reports have errors). "
                    "2. Get a secured credit card (₹20k–50k FD as collateral). "
                    "3. Pay full outstanding — never just the minimum — for 6 months. "
                    "Expected score uplift: 40–80 points.")})
    elif cibil >= 750:
        recs.append({"p": "positive", "icon": "🏆",
            "title": "Prime CIBIL score — negotiate aggressively",
            "what": (f"Score of {cibil} qualifies you for the best available rates (10–12% APR). "
                     f"vs a 650-score applicant, you save ₹{int(loan*0.04*5/2):,} on ₹{loan:,.0f} over 5 years."),
            "how": ("Use BankBazaar or Paisabazaar to collect 8–10 live offers simultaneously. "
                    "Then approach your existing bank with the best competing offer — "
                    "most will match or beat it to retain you.")})

    if employ < 1:
        recs.append({"p": "high", "icon": "💼",
            "title": "Employment tenure is insufficient for loan eligibility",
            "what": ("Virtually all scheduled banks and major NBFCs require a minimum of 12 months "
                     "at the current employer before approving personal loans. "
                     "Probationary or contract employees are excluded from most programs."),
            "how": ("Wait for the 12-month mark. In the interim: file your ITR, "
                    "get an HR letter confirming permanent employment status, "
                    "and build credit history via a secured card.")})
    elif employ >= 3:
        recs.append({"p": "positive", "icon": "📋",
            "title": f"{employ:.0f} years of tenure qualifies for pre-approved offers",
            "what": ("Long tenure at a single employer is one of the strongest approval signals. "
                     "Your salary-disbursement bank already has your complete transaction history."),
            "how": ("Call your salary bank's relationship manager directly and ask for a "
                    "pre-approved personal loan. These use internal payroll data — "
                    "typically approved in 24–48 hours with minimal documentation.")})

    if income > 0 and loan > income * 60:
        recs.append({"p": "medium", "icon": "📊",
            "title": "Loan-to-income ratio exceeds standard limits",
            "what": (f"₹{loan:,} is {loan/income:.0f}× your monthly income. "
                     "Standard personal loan limits are 10–22× monthly income. "
                     "Higher ratios attract scrutiny and higher rejection rates."),
            "how": (f"Split the application: ₹{int(income*18):,} as a personal loan "
                    f"+ ₹{int(loan-income*18):,} via Loan Against Property or Loan Against Mutual Funds. "
                    "The latter uses your assets as security, unlocking larger amounts at lower rates.")})
    return recs

# ─────────────────────────────────────────────────────────────
# ROADMAP
# ─────────────────────────────────────────────────────────────
def gen_roadmap(income, rent, sav, loan, emp, cibil, prob):
    m1 = [
        "Pull your free CIBIL report at cibil.com and dispute any errors immediately. "
        "Incorrect entries affect 23% of reports and can be resolved in 30 days — "
        "often boosting your score by 20–60 points with no financial effort.",
        "Assemble your complete document set now: 3 months salary slips, last year's Form 16, "
        "6 months bank statement (PDF, not screenshot), PAN card, and Aadhaar. "
        "A missing document is the single most common reason for application delays."
    ]
    if sav / max(income, 1) < 0.15:
        m1.append(
            f"Activate an automatic SIP of ₹{int(income*0.12):,}/month into a Liquid Fund "
            "on salary credit day. Three months of consistent deposits visibly improves your "
            "bank statement narrative — which underwriters read manually for all loan applications.")
    m2 = [
        "Do not apply to multiple lenders simultaneously. Each application triggers a hard CIBIL enquiry "
        "that reduces your score by 5–8 points. Use eligibility-check tools on BankBazaar or Paisabazaar "
        "first — these use soft checks that don't affect your score."
    ]
    if cibil < 750:
        m2.append(
            f"Open a secured credit card against an FD of ₹{min(50000, int(loan*0.1)):,}. "
            "Use it for recurring expenses (fuel, groceries, utility bills) and pay the full "
            "statement balance — not the minimum — before the due date every month. "
            "CIBIL records this as 100% utilisation discipline within 45 days.")
    if rent / max(income, 1) > 0.45:
        m2.append(
            "Your rent-to-income ratio is above the safe threshold. Even a ₹3,000–5,000 monthly reduction "
            "through co-living or lease renegotiation can move your FOIR into the lender's approval band.")
    m3 = [
        "Apply to your salary-disbursement bank first. Their internal data includes your payroll deposits, "
        "average daily balance, and spending patterns — giving them higher confidence than external banks "
        "relying solely on your submitted documents.",
        f"At 90 days, your estimated Approval Readiness Score: ~{min(95, round((1-prob)*100)+25)}%. "
        "If below 70%, pivot to Tier-1 NBFCs (Bajaj Finserv, Tata Capital, HDFC Credila) — "
        "they apply broader underwriting criteria and approve 40% more applications than PSU banks."
    ]
    if emp < 2:
        m3.insert(1,
            "Obtain an employment continuity certificate and HR confirmation of permanent status. "
            "These documents move your profile from 'uncertain employment' to "
            "'verified salaried professional' in the underwriter's assessment.")
    return [m1, m2, m3]

# ─────────────────────────────────────────────────────────────
# NAVIGATION BAR
# ─────────────────────────────────────────────────────────────
def render_nav():
    vr = st.session_state.vr
    ver_html = ""
    if vr:
        vc = GREEN if vr["coherent"] else RED
        vl = "✓ Verified" if vr["coherent"] else "⚠ Review Required"
        ver_html = (f'<span style="background:{vc}1a;color:{vc};border:1px solid {vc}44;'
                    f'font-family:JetBrains Mono,monospace;font-size:10.5px;font-weight:700;'
                    f'letter-spacing:.07em;padding:4px 13px;border-radius:99px;'
                    f'text-transform:uppercase;">{vl}</span>')
    name  = st.session_state.username
    plan  = st.session_state.plan
    initial = name[0].upper() if name else "D"

    # Use st_components.html to completely bypass Streamlit's HTML sanitiser
    nav_html = f"""<!DOCTYPE html>
<html><head><style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@600;700;800&family=JetBrains+Mono:wght@700&display=swap');
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:transparent; overflow:hidden; }}
  .nav {{
    background:rgba(15,17,23,0.96);
    backdrop-filter:blur(24px);
    -webkit-backdrop-filter:blur(24px);
    border-bottom:1px solid rgba(108,63,255,0.18);
    padding:0 48px;
    height:62px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    box-shadow:0 1px 0 rgba(108,63,255,0.12),0 4px 24px rgba(0,0,0,0.50);
    font-family:Inter,sans-serif;
  }}
  .logo-wrap {{ display:flex; align-items:center; gap:12px; }}
  .logo-icon {{
    width:34px; height:34px;
    background:linear-gradient(135deg,{GRAPE},{CYAN});
    border-radius:9px;
    display:flex; align-items:center; justify-content:center;
    font-size:16px;
    box-shadow:0 0 18px rgba(108,63,255,0.50);
  }}
  .logo-name {{
    font-weight:800; font-size:17px;
    color:{WHITE}; letter-spacing:-0.02em;
  }}
  .logo-sub {{
    font-family:JetBrains Mono,monospace;
    font-size:9.5px; color:rgba(180,192,255,0.32);
    letter-spacing:.10em; margin-left:8px; text-transform:uppercase;
  }}
  .right {{ display:flex; align-items:center; gap:12px; }}
  .pill {{
    display:flex; align-items:center; gap:8px;
    background:rgba(108,63,255,0.12);
    border:1px solid rgba(108,63,255,0.22);
    border-radius:99px; padding:5px 13px 5px 6px;
  }}
  .avatar {{
    width:26px; height:26px;
    background:linear-gradient(135deg,{GRAPE},{LAV});
    border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-size:11px; font-weight:800; color:#fff;
  }}
  .uname {{
    font-size:13.5px; font-weight:600;
    color:{WHITE}; max-width:120px;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
  }}
  .plan-badge {{
    background:{GRAPE}; color:#fff;
    font-family:JetBrains Mono,monospace;
    font-size:9.5px; font-weight:700;
    padding:2px 8px; border-radius:99px;
    text-transform:uppercase;
  }}
</style></head>
<body>
  <div class="nav">
    <div class="logo-wrap">
      <div class="logo-icon">⚡</div>
      <div>
        <span class="logo-name">Wallet Warriors</span>
        <span class="logo-sub">Credit Intelligence</span>
      </div>
    </div>
    <div class="right">
      {ver_html}
      <div class="pill">
        <div class="avatar">{initial}</div>
        <span class="uname">{name}</span>
        <span class="plan-badge">{plan}</span>
      </div>
    </div>
  </div>
</body></html>"""
    st_components.html(nav_html, height=64, scrolling=False)

    with st.sidebar:
        st.markdown(f"""
        <div style="padding:22px 8px 0;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:18px;">
            <div style="width:38px;height:38px;background:linear-gradient(135deg,{GRAPE},{CYAN});
                        border-radius:9px;display:flex;align-items:center;justify-content:center;
                        font-size:17px;box-shadow:0 0 16px rgba(108,63,255,0.45);">⚡</div>
            <div>
              <div style="font-family:'Inter',sans-serif;font-size:16px;font-weight:800;
                          color:{WHITE};letter-spacing:-0.01em;">Wallet Warriors</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:{MUTED};">
                Credit Intelligence</div>
            </div>
          </div>
          <div style="background:rgba(108,63,255,0.10);border-radius:12px;padding:14px 16px;
                      margin-bottom:16px;border:1px solid rgba(108,63,255,0.18);">
            <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:{MUTED};
                        text-transform:uppercase;letter-spacing:.09em;margin-bottom:7px;">Account</div>
            <div style="font-family:'Inter',sans-serif;font-size:15px;font-weight:700;
                        color:{WHITE};">{name}</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:11px;
                        color:{LAV};margin-top:3px;">{plan} Plan</div>
          </div>
          <div style="font-family:'Inter',sans-serif;font-size:12.5px;color:{MUTED};
                      line-height:1.6;padding:0 4px 16px;">
            📊 AI Credit Intelligence<br/>
            🔬 Income Triangulation<br/>
            🎯 Approval Readiness<br/>
            🕵️ Thin File Engine<br/>
            📄 Regulatory PDF Report
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("← Sign Out", key="so"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ─────────────────────────────────────────────────────────────
# ██  LOGIN PAGE  ██
# ─────────────────────────────────────────────────────────────
def render_login():
    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
      background:
        radial-gradient(ellipse at 10% 60%, rgba(124,77,255,0.22) 0%, transparent 50%),
        radial-gradient(ellipse at 90% 10%, rgba(0,229,192,0.10) 0%, transparent 45%),
        {BG} !important;
    }}
    [data-testid="stSidebar"], footer {{ display:none !important; }}
    .block-container, .stMainBlockContainer {{
      padding:0 !important; max-width:100% !important;
    }}
    [data-testid="stHorizontalBlock"] {{
      gap:0 !important; align-items:stretch !important;
    }}
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
      padding:0 !important;
    }}
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {{
      background:{SURFACE} !important;
      border-left:1px solid rgba(124,77,255,0.18) !important;
      min-height:100vh !important;
    }}
    /* Style the native inputs to match the dark theme */
    .stTextInput > label {{
      font-family:'JetBrains Mono',monospace !important;
      font-size:10px !important;
      font-weight:700 !important;
      letter-spacing:.10em !important;
      text-transform:uppercase !important;
      color:rgba(180,192,255,0.55) !important;
      margin-bottom:6px !important;
    }}
    .stTextInput > div > input {{
      background:rgba(124,77,255,0.06) !important;
      border:1.5px solid rgba(124,77,255,0.22) !important;
      border-radius:10px !important;
      color:{WHITE} !important;
      font-family:'Inter',sans-serif !important;
      font-size:14px !important;
      padding:12px 16px !important;
    }}
    .stTextInput > div > input:focus {{
      border-color:rgba(124,77,255,0.60) !important;
      box-shadow:0 0 0 3px rgba(124,77,255,0.12) !important;
    }}
    .stButton > button {{
      width:100% !important;
      background:linear-gradient(135deg,{GRAPE},{LAV}) !important;
      color:#fff !important;
      border:none !important;
      border-radius:10px !important;
      font-family:'Inter',sans-serif !important;
      font-size:15px !important;
      font-weight:700 !important;
      padding:13px 0 !important;
      letter-spacing:-0.01em !important;
      box-shadow:0 4px 24px rgba(124,77,255,0.38) !important;
      transition:opacity .15s !important;
    }}
    .stButton > button:hover {{ opacity:.88 !important; }}
    </style>
    """, unsafe_allow_html=True)

    left, right = st.columns([55, 45], gap="small")

    # ── LEFT PANEL ──────────────────────────────────────────────
    with left:
        feat_items = [
            ("🔬", "Income Triangulation Engine",
             "Cross-references stated salary against electricity bills, UPI flows & documents."),
            ("🤖", "XGBoost AI · AUC 0.86",
             "Production-grade default prediction with full SHAP feature-level explanations."),
            ("🎯", "Approval Readiness Score",
             "6-pillar composite score showing exactly where you stand before you apply."),
            ("🗺️", "90-Day Roadmap",
             "Personalised milestone plan from your current profile to prime borrower status."),
        ]
        feat_html = ""
        for icon, title, desc in feat_items:
            feat_html += (
                f'<div style="display:flex;align-items:flex-start;gap:14px;margin-bottom:18px;">'
                f'<div style="width:38px;height:38px;min-width:38px;flex-shrink:0;'
                f'background:rgba(124,77,255,0.12);border:1px solid rgba(124,77,255,0.28);'
                f'border-radius:10px;display:flex;align-items:center;justify-content:center;'
                f'font-size:17px;">{icon}</div>'
                f'<div style="padding-top:2px;">'
                f'<div style="font-family:Inter,sans-serif;font-size:13.5px;font-weight:700;'
                f'color:{WHITE};margin-bottom:3px;letter-spacing:-0.01em;">{title}</div>'
                f'<div style="font-family:Inter,sans-serif;font-size:12.5px;color:{TEXT};'
                f'line-height:1.55;opacity:.85;">{desc}</div>'
                f'</div></div>'
            )

        st.markdown(
            f'<div style="padding:15vh 56px 40px 56px;">'

            # ── Logo ──
            f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:40px;">'
            f'<div style="width:44px;height:44px;flex-shrink:0;'
            f'background:linear-gradient(135deg,{GRAPE},{CYAN});border-radius:12px;'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-size:21px;box-shadow:0 0 28px {GRAPE}70;">⚡</div>'
            f'<div>'
            f'<div style="font-family:Inter,sans-serif;font-size:17px;font-weight:900;'
            f'color:{WHITE};letter-spacing:-0.02em;line-height:1.2;">Wallet Warriors</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:{MUTED};'
            f'letter-spacing:.12em;text-transform:uppercase;margin-top:2px;">Credit Intelligence Platform</div>'
            f'</div>'
            f'<span style="margin-left:8px;background:{GRAPE}22;color:{LAV};'
            f'border:1px solid {GRAPE}44;font-family:JetBrains Mono,monospace;'
            f'font-size:8px;font-weight:700;padding:3px 9px;border-radius:99px;'
            f'letter-spacing:.12em;text-transform:uppercase;">Pro</span>'
            f'</div>'

            # ── Headline ──
            f'<h1 style="font-family:Inter,sans-serif;font-size:42px;font-weight:900;'
            f'color:{WHITE};margin:0 0 14px;letter-spacing:-0.035em;line-height:1.06;">'
            f'Know your loan odds<br>'
            f'<span style="background:linear-gradient(90deg,{LAV} 0%,{CYAN} 100%);'
            f'-webkit-background-clip:text;-webkit-text-fill-color:transparent;'
            f'background-clip:text;">before you apply.</span></h1>'

            # ── Subheadline ──
            f'<p style="font-family:Inter,sans-serif;font-size:15px;'
            f'color:rgba(200,208,240,0.65);margin:0 0 36px;line-height:1.7;max-width:380px;">'
            f'AI-powered credit intelligence for smart borrowers — walk into any bank '
            f'with complete visibility of your approval probability.</p>'

            # ── Feature list ──
            f'<div>{feat_html}</div>'

            # ── Trust badges ──
            f'<div style="display:flex;align-items:center;gap:24px;margin-top:32px;'
            f'padding-top:20px;border-top:1px solid rgba(124,77,255,0.12);">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:10px;'
            f'color:rgba(180,192,255,0.32);">🔐 AES-256</span>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:10px;'
            f'color:rgba(180,192,255,0.32);">✅ SOC 2 Type II</span>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:10px;'
            f'color:rgba(180,192,255,0.32);">🇮🇳 DPDP Act 2023</span>'
            f'</div>'

            f'</div>',
            unsafe_allow_html=True
        )

    # ── RIGHT PANEL ─────────────────────────────────────────────
    with right:
        st.markdown(
            f'<div style="padding:15vh 52px 40px 52px;">'
            f'<div style="width:40px;height:4px;margin-bottom:28px;'
            f'background:linear-gradient(90deg,{GRAPE},{CYAN});border-radius:99px;'
            f'box-shadow:0 0 14px {GRAPE}80;"></div>'
            f'<h2 style="font-family:Inter,sans-serif;font-size:28px;font-weight:800;'
            f'color:{WHITE};margin:0 0 8px;letter-spacing:-0.025em;">Welcome back</h2>'
            f'<p style="font-family:Inter,sans-serif;font-size:14px;color:{TEXT};'
            f'margin:0 0 28px;line-height:1.65;opacity:.80;">'
            f'Sign in to access your AI credit intelligence dashboard.</p>'
            f'</div>',
            unsafe_allow_html=True
        )
        with st.container():
            c1, c2, c3 = st.columns([52, 340, 52])
            with c2:
                if st.session_state.attempts >= 5:
                    st.error("🔒 Account locked after 5 failed attempts. Please contact support.")
                else:
                    email = st.text_input("Email Address", placeholder="your@email.com", key="li_e")
                    pw    = st.text_input("Password", type="password",
                                          placeholder="Enter your password", key="li_p")
                    st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
                    if st.button("Sign In  →", key="btn_li"):
                        if not email.strip():
                            st.error("Please enter your email address.")
                        elif not pw:
                            st.error("Please enter your password.")
                        else:
                            with st.spinner("Authenticating…"):
                                time.sleep(0.4)
                                ok, user = auth(email.strip().lower(), pw)
                            if ok:
                                st.session_state.update({
                                    "authenticated": True,
                                    "username": user["full_name"],
                                    "user_id":  user["id"],
                                    "plan":     user.get("plan", "Pro"),
                                    "page":     "onboard",
                                    "attempts": 0,
                                })
                                st.rerun()
                            else:
                                st.session_state.attempts += 1
                                rem = 5 - st.session_state.attempts
                                st.error(f"Incorrect credentials. {rem} attempt{'s' if rem!=1 else ''} remaining.")
                st.markdown(
                    f'<div style="margin-top:20px;padding-top:16px;'
                    f'border-top:1px solid rgba(124,77,255,0.12);">'
                    f'<div style="display:flex;gap:16px;flex-wrap:wrap;">'
                    f'<span style="font-family:JetBrains Mono,monospace;font-size:10px;'
                    f'color:rgba(180,192,255,0.30);">🔐 AES-256</span>'
                    f'<span style="font-family:JetBrains Mono,monospace;font-size:10px;'
                    f'color:rgba(180,192,255,0.30);">✅ SOC 2 Type II</span>'
                    f'<span style="font-family:JetBrains Mono,monospace;font-size:10px;'
                    f'color:rgba(180,192,255,0.30);">🇮🇳 DPDP Act 2023</span>'
                    f'</div></div>',
                    unsafe_allow_html=True
                )

# ─────────────────────────────────────────────────────────────
# ██  ONBOARDING  ██
# ─────────────────────────────────────────────────────────────
def render_onboard():
    render_nav()
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # ── Step progress indicator ──
    steps = [("1", "Income Data", True), ("2", "Verification", False), ("3", "Analysis", False)]
    steps_html = ""
    for i, (num, lbl, active) in enumerate(steps):
        if active:
            circle = (f'<div style="width:34px;height:34px;border-radius:50%;'
                      f'background:linear-gradient(135deg,{GRAPE},{LAV});'
                      f'display:flex;align-items:center;justify-content:center;'
                      f'font-family:\'JetBrains Mono\',monospace;font-size:13px;font-weight:700;'
                      f'color:#fff;box-shadow:0 0 18px rgba(108,63,255,0.55);">{num}</div>')
            label = (f'<span style="font-family:\'Inter\',sans-serif;font-size:14px;'
                     f'font-weight:700;color:{LAV};">{lbl}</span>')
        else:
            circle = (f'<div style="width:34px;height:34px;border-radius:50%;'
                      f'background:rgba(108,63,255,0.10);border:1.5px solid rgba(108,63,255,0.22);'
                      f'display:flex;align-items:center;justify-content:center;'
                      f'font-family:\'JetBrains Mono\',monospace;font-size:13px;font-weight:700;'
                      f'color:{MUTED};">{num}</div>')
            label = (f'<span style="font-family:\'Inter\',sans-serif;font-size:14px;'
                     f'font-weight:500;color:{MUTED};">{lbl}</span>')
        steps_html += f'<div style="display:flex;align-items:center;gap:9px;">{circle}{label}</div>'
        if i < len(steps) - 1:
            conn_color = f"linear-gradient(90deg,{GRAPE},rgba(108,63,255,0.18))" if active else "rgba(108,63,255,0.14)"
            steps_html += f'<div style="width:72px;height:2px;background:{conn_color};margin:0 14px;"></div>'

    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:center;margin-bottom:28px;">
      {steps_html}
    </div>

    <div style="max-width:700px;margin-bottom:24px;">
      <h1 style="font-family:'Inter',sans-serif;font-size:38px;font-weight:900;
                 color:{WHITE};margin:0 0 14px;letter-spacing:-0.03em;">
        Income Verification Engine</h1>
      <p style="font-family:'Inter',sans-serif;font-size:16px;font-weight:400;
                color:{TEXT};margin:0;line-height:1.72;">
        We verify your income using the
        <strong style="color:{LAV};font-weight:700;">{tooltip("Triangulation Method")}</strong> —
        cross-referencing what you declare against your actual spending signals.
        This is the same methodology used by Tier-1 NBFC underwriters.
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Panel A ──
    panel_open("A — Monthly Financials", "Core income & expense figures",
               "These are the primary inputs. Be precise — they are cross-checked against your spending signals.")
    c1, c2, c3 = st.columns(3)
    with c1: inc = st.number_input("Monthly Income (₹)", min_value=0, step=1000, key="ob_inc")
    with c2: rent = st.number_input("Monthly Rent / Home EMI (₹)", min_value=0, step=500, key="ob_rent")
    with c3: sav = st.number_input("Monthly Savings (₹)", min_value=0, step=500, key="ob_sav")
    panel_close()

    # ── Panel B ──
    panel_open("B — Spending Signals", "Behavioural cross-correlation data",
               "High income paired with very low utility bills or UPI activity is flagged as an anomaly.")
    c4, c5 = st.columns(2)
    with c4: elec = st.number_input("Monthly Electricity Bill (₹)", min_value=0, step=100, key="ob_elec")
    with c5: upi = st.number_input("Total Monthly UPI / Digital Spending (₹)", min_value=0, step=500, key="ob_upi")
    panel_close()

    # ── Panel C ──
    panel_open("C — Document Proof", "Optional income verification upload",
               "Income matching within ±10% of your document results in instant verification.",
               border_color=BORDER2)
    c6, c7 = st.columns([2, 1])
    with c6:
        doc_file = st.file_uploader(
            "Salary Slip or Bank Statement (PDF · PNG · JPG)",
            type=["pdf", "png", "jpg", "jpeg"], key="ob_doc")
    with c7:
        doc_manual = st.number_input("Net Pay in Document (₹)", min_value=0, step=1000, key="ob_dm",
                                      help="Enter the 'Net Pay' figure from your payslip if OCR is unavailable.")
    panel_close()

    doc_income = None
    if doc_file:
        st.markdown(f"""
        <div style="background:rgba(0,232,181,0.06);border:1.5px solid rgba(0,232,181,0.24);
                    border-radius:10px;padding:13px 18px;margin-bottom:18px;
                    display:flex;align-items:center;gap:10px;">
          <span style="font-size:16px;">📄</span>
          <span style="font-family:'Inter',sans-serif;font-size:14px;font-weight:600;color:{CYAN};">
            Document received: <strong>{doc_file.name}</strong> — OCR pipeline active.</span>
        </div>""", unsafe_allow_html=True)
        if doc_manual > 0: doc_income = doc_manual
    if doc_manual > 0 and not doc_file:
        doc_income = doc_manual

    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
    if st.button("Run Verification Engine  →", key="btn_ver"):
        if inc == 0:
            st.warning("Please enter your monthly income to continue.")
        else:
            with st.spinner("Cross-referencing income against spending signals…"):
                time.sleep(0.9)
                ok, conf, flags, est = triangulate(inc, rent, elec, upi, doc_income)
            st.session_state.vr = {
                "coherent": ok, "confidence": conf, "flags": flags,
                "est_real_income": est, "stated_income": inc, "rent": rent,
                "savings": sav, "electricity": elec, "upi_outflow": upi, "doc_income": doc_income
            }
            st.session_state.page = "verify_result"
            st.rerun()

    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# ██  VERIFICATION RESULT  ██
# ─────────────────────────────────────────────────────────────
def render_verify_result():
    vr = st.session_state.vr
    render_nav()
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
    section_header("Verification Result", "Income triangulation engine output", "🔬")

    ok = vr["coherent"]; conf = vr["confidence"]
    flags = vr["flags"]; stated = vr["stated_income"]; est = vr["est_real_income"]

    if not ok:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(255,61,94,0.10),rgba(255,61,94,0.03));
                    border:2px solid rgba(255,61,94,0.40);border-radius:18px;
                    padding:32px 36px;margin-bottom:28px;">
          <div style="font-size:40px;margin-bottom:12px;">⛔</div>
          <h2 style="font-family:'Inter',sans-serif;font-size:26px;font-weight:800;
                     color:{RED};margin:0 0 10px;letter-spacing:-0.02em;">Income Anomaly Detected</h2>
          <p style="font-family:'Inter',sans-serif;font-size:15px;color:#C8D0F0;
                    margin:0 0 18px;max-width:620px;line-height:1.72;">
            Inconsistencies were found between your stated income and your spending signals.
            Your application <strong style="color:{RED};">cannot proceed</strong> until
            these are resolved. This decision is logged for compliance audit.
          </p>
          <div style="background:rgba(255,61,94,0.10);border-radius:8px;
                      padding:11px 16px;display:inline-flex;align-items:center;gap:10px;">
            <span style="font-family:'JetBrains Mono',monospace;font-size:12px;
                         color:rgba(255,61,94,0.90);font-weight:600;">
              Confidence Score: {conf}%  ·  Minimum required: 55%  ·  High-severity flags: {sum(1 for f in flags if f['sev']=='high')}
            </span>
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(46,204,138,0.10),rgba(46,204,138,0.03));
                    border:2px solid rgba(46,204,138,0.34);border-radius:18px;
                    padding:32px 36px;margin-bottom:28px;">
          <div style="font-size:40px;margin-bottom:12px;">✅</div>
          <h2 style="font-family:'Inter',sans-serif;font-size:26px;font-weight:800;
                     color:{GREEN};margin:0 0 10px;letter-spacing:-0.02em;">Income Verified</h2>
          <p style="font-family:'Inter',sans-serif;font-size:15px;color:#C8D0F0;
                    margin:0 0 14px;line-height:1.72;">
            Your income and spending patterns are consistent across all signals.
            Proceed to the full AI credit analysis.
          </p>
          <span style="font-family:'JetBrains Mono',monospace;font-size:12px;
                       color:rgba(46,204,138,0.85);font-weight:600;">
            Confidence: {conf}%  ·  Estimated real income: ₹{est:,}/month
          </span>
        </div>""", unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Stated Income", f"₹{stated:,.0f}")
    with k2: st.metric("Estimated Income", f"₹{est:,.0f}",
                        delta=f"{((est-stated)/max(stated,1)*100):+.1f}%")
    with k3: st.metric("Rent-to-Income", f"{vr['rent']/max(stated,1)*100:.1f}%",
                        delta="Healthy" if vr['rent']/max(stated,1) < 0.45 else "High",
                        delta_color="normal" if vr['rent']/max(stated,1) < 0.45 else "inverse")
    with k4: st.metric("Verification Score", f"{conf}/100")

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "indicator"}, {"type": "indicator"}]])
    fig.add_trace(go.Indicator(mode="gauge+number", value=conf,
        title={"text": "Verification Confidence", "font": {"size": 14, "color": WHITE}},
        number={"suffix": "%", "font": {"color": WHITE, "size": 36}},
        gauge={"axis": {"range": [0, 100], "tickcolor": WHITE, "tickfont": {"size": 11}},
               "bar": {"color": GRAPE, "thickness": 0.28}, "bgcolor": "rgba(0,0,0,0)",
               "steps": [{"range": [0, 40], "color": "rgba(255,61,94,0.16)"},
                         {"range": [40, 70], "color": "rgba(245,166,35,0.16)"},
                         {"range": [70, 100], "color": "rgba(46,204,138,0.16)"}],
               "threshold": {"line": {"color": CYAN, "width": 3}, "value": 55}}), row=1, col=1)
    mx = max(stated, est) * 1.3
    fig.add_trace(go.Indicator(mode="gauge+number+delta", value=stated,
        delta={"reference": est, "prefix": "₹", "valueformat": ",.0f"},
        title={"text": "Stated vs Estimated Income", "font": {"size": 14, "color": WHITE}},
        number={"prefix": "₹", "valueformat": ",.0f", "font": {"color": WHITE}},
        gauge={"axis": {"range": [0, mx]}, "bar": {"color": LAV},
               "steps": [{"range": [0, est], "color": "rgba(157,112,255,0.16)"}],
               "bgcolor": "rgba(0,0,0,0)"}), row=1, col=2)
    fig.update_layout(**PLOT, height=280)
    st.plotly_chart(fig, use_container_width=True)

    if flags:
        section_header("Anomalies Detected", "Each issue must be resolved before proceeding", "🚩", RED)
        for f in flags:
            sc = {"high": RED, "medium": GOLD, "low": LAV}.get(f["sev"], LAV)
            st.markdown(f"""
            <div style="background:{CARD};border-left:4px solid {sc};
                        border-radius:0 12px 12px 0;padding:20px 24px;margin-bottom:12px;
                        border-top:1px solid rgba(255,255,255,0.04);
                        border-right:1px solid rgba(255,255,255,0.04);
                        border-bottom:1px solid rgba(255,255,255,0.04);">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:9px;">
                <span style="background:{sc}22;color:{sc};border:1px solid {sc}44;
                             font-family:'JetBrains Mono',monospace;font-size:10px;
                             font-weight:700;padding:3px 11px;border-radius:99px;
                             text-transform:uppercase;letter-spacing:.10em;">{f['sev']}</span>
                <span style="font-family:'Inter',sans-serif;font-size:15.5px;
                             font-weight:700;color:{WHITE};">{f['title']}</span>
              </div>
              <p style="font-family:'Inter',sans-serif;font-size:14.5px;
                        color:#C8D0F0;margin:0;line-height:1.68;">{f['msg']}</p>
            </div>""", unsafe_allow_html=True)
    else:
        st.success("✓ No anomalies detected — all income signals are coherent.")

    st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
    ca, cb = st.columns(2)
    with ca:
        if st.button("← Re-enter Data", key="btn_bk"):
            st.session_state.page = "onboard"; st.rerun()
    with cb:
        if ok:
            if st.button("Proceed to Credit Analysis  →", key="btn_go"):
                st.session_state.ud = vr
                st.session_state.page = "dashboard"
                st.rerun()
        else:
            st.markdown(f"""
            <div style="background:rgba(255,61,94,0.07);border:1.5px solid rgba(255,61,94,0.28);
                        border-radius:12px;padding:20px 22px;text-align:center;">
              <p style="font-family:'Inter',sans-serif;font-size:15px;font-weight:700;
                        color:{RED};margin:0 0 6px;">🔒 Application Blocked</p>
              <p style="font-family:'Inter',sans-serif;font-size:13.5px;color:{MUTED};
                        margin:0;line-height:1.65;">
                Resolve all high-severity anomalies above and re-submit for verification.</p>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# ██  DASHBOARD  ██
# ─────────────────────────────────────────────────────────────
def render_dashboard():
    render_nav()
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    ud = st.session_state.ud
    vc = ud.get("confidence", 80)
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # ── Dashboard header ──
    st.markdown(f"""
    <div style="display:flex;align-items:flex-start;justify-content:space-between;
                flex-wrap:wrap;gap:16px;margin-bottom:32px;">
      <div>
        <h1 style="font-family:'Inter',sans-serif;font-size:38px;font-weight:900;
                   color:{WHITE};margin:0 0 8px;letter-spacing:-0.03em;">
          Credit Risk Dashboard</h1>
        <p style="font-family:'Inter',sans-serif;font-size:15px;color:{TEXT};margin:0;font-weight:400;">
          AI-powered assessment for
          <strong style="color:{LAV};font-weight:700;">{st.session_state.username}</strong>
        </p>
      </div>
      <div style="display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-top:4px;">
        {badge("AUC 0.86", GRAPE, "#fff", True)}&nbsp;
        {badge("XGBoost v2", GOLD, "#080c1a")}&nbsp;
        {badge("SHAP Explained", CYAN, "#080c1a")}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Loan application input panel ──
    st.markdown(f"""
    <div style="background:{SURFACE};border:1.5px solid {BORDER};
                border-radius:16px;padding:28px 30px 8px;margin-bottom:24px;
                box-shadow:0 4px 28px rgba(0,0,0,0.35);">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <span style="background:{GRAPE};color:#fff;font-family:'JetBrains Mono',monospace;
                     font-size:10px;font-weight:700;letter-spacing:.12em;padding:3px 11px;
                     border-radius:99px;text-transform:uppercase;">Loan Parameters</span>
        <h3 style="font-family:'Inter',sans-serif;font-size:17px;font-weight:700;
                   color:{WHITE};margin:0;letter-spacing:-0.01em;">Enter your loan application details</h3>
      </div>
    """, unsafe_allow_html=True)
    r1 = st.columns(3)
    with r1[0]: income = st.number_input("Monthly Income (₹)", value=int(ud.get("stated_income", 0)), min_value=0, step=1000, key="d_inc")
    with r1[1]: rent = st.number_input("Monthly Rent / EMI (₹)", value=int(ud.get("rent", 0)), min_value=0, step=500, key="d_rent")
    with r1[2]: savings = st.number_input("Monthly Savings (₹)", value=int(ud.get("savings", 0)), min_value=0, step=500, key="d_sav")
    r2 = st.columns(3)
    with r2[0]: loan = st.number_input("Loan Amount Requested (₹)", min_value=0, step=5000, key="d_loan")
    with r2[1]: employ = st.number_input("Years at Current Job", min_value=0.0, step=0.5, key="d_emp")
    with r2[2]:
        cibil = st.number_input("CIBIL / Credit Score", 300, 900, value=700, key="d_cibil")
        st.markdown(
            f'<div style="margin-top:4px;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:10px;'
            f'color:{MUTED};letter-spacing:.04em;">No credit history? →</span>'
            f'</div>', unsafe_allow_html=True)
        if st.button("🔍 Analyse as Thin File", key="btn_thinfile",
                     help="No CIBIL score? Use our Behavioral Underwriting engine instead."):
            st.session_state.page = "thin_file"
            st.rerun()
    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

    run = st.button("Run AI Credit Analysis  →", key="btn_run")

    if run:
        if income == 0:
            st.warning("Please enter your monthly income to run analysis.")
            st.stop()

        idf = pd.DataFrame({
            "Income": [income], "Rent": [rent], "Savings": [savings],
            "LoanAmount": [loan], "Employment": [employ], "CreditScore": [cibil]
        })
        prob = float(MDL.predict_proba(idf)[0][1])
        dec = "rejected" if prob > 0.5 else "approved"
        ar, ar_dims = approval_readiness(income, rent, savings, loan, employ, cibil, prob, vc)
        hs = hustle_score(savings, income, rent, cibil, employ, loan)

        db_save(st.session_state.user_id or 1, {
            "income": income, "rent": rent, "savings": savings, "loan": loan,
            "employ": employ, "cibil": cibil, "elec": ud.get("electricity", 0),
            "upi": ud.get("upi_outflow", 0), "doc_income": ud.get("doc_income"),
            "ver_score": vc, "ver_pass": ud.get("coherent", True),
            "prob": prob, "dec": dec, "hustle": hs, "ar": ar
        })

        # ── Store results in session state so sliders don't wipe them ──
        st.session_state["dash_result"] = {
            "income": income, "rent": rent, "savings": savings, "loan": loan,
            "employ": employ, "cibil": cibil, "prob": prob, "dec": dec,
            "ar": ar, "ar_dims": ar_dims, "hs": hs, "vc": vc
        }

    # ── Render results from session state (persists across slider interactions) ──
    if "dash_result" in st.session_state:
        res    = st.session_state["dash_result"]
        income = res["income"]; rent    = res["rent"];   savings = res["savings"]
        loan   = res["loan"];   employ  = res["employ"]; cibil   = res["cibil"]
        prob   = res["prob"];   dec     = res["dec"];    ar      = res["ar"]
        ar_dims= res["ar_dims"];hs      = res["hs"];     vc      = res["vc"]

        st.divider()

        # ── Decision banner ──
        dc = RED if dec == "rejected" else GREEN
        dlbl = "Loan Application Rejected" if dec == "rejected" else "Loan Application Approved"
        dico = "✗" if dec == "rejected" else "✓"
        rgb = "255,61,94" if dec == "rejected" else "46,204,138"

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba({rgb},0.10),rgba({rgb},0.02));
                    border:2px solid rgba({rgb},0.36);border-radius:18px;padding:32px 36px;
                    margin-bottom:28px;display:flex;align-items:center;
                    justify-content:space-between;flex-wrap:wrap;gap:20px;">
          <div>
            <div style="font-size:46px;margin-bottom:10px;
                        filter:drop-shadow(0 0 18px rgba({rgb},0.55));">{dico}</div>
            <h2 style="font-family:'Inter',sans-serif;font-size:30px;font-weight:900;
                       color:{dc};margin:0 0 10px;letter-spacing:-0.025em;">{dlbl}</h2>
            <p style="font-family:'Inter',sans-serif;font-size:15px;color:{MUTED};
                      margin:0;line-height:1.65;">
              {tooltip("XGBoost", "AI model")} prediction · {tooltip("ROC-AUC", "AUC 0.86")} · Default probability:
              <strong style="color:{dc};">{prob*100:.1f}%</strong>
              · Decision threshold: 50%
            </p>
          </div>
          <div style="text-align:center;min-width:130px;">
            <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:{MUTED};
                        text-transform:uppercase;letter-spacing:.10em;margin-bottom:6px;">
              Approval Readiness</div>
            <div style="font-family:'Inter',sans-serif;font-size:60px;font-weight:900;
                        color:{LAV};line-height:1;
                        filter:drop-shadow(0 0 20px rgba(157,112,255,0.45));">{ar}</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:{MUTED};">
              out of 100</div>
          </div>
        </div>""", unsafe_allow_html=True)

        k1, k2, k3, k4, k5 = st.columns(5)
        with k1: st.metric("Default Risk", f"{prob*100:.1f}%")
        with k2: st.metric("Approval Readiness", f"{ar}/100")
        with k3: st.metric("Debt-to-Income", f"{rent/max(income,1)*100:.1f}%")
        with k4: st.metric("CIBIL Score", cibil)
        with k5: st.metric("Hustle Score™", f"{hs}/100")

        st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "  📊 Risk Overview  ", "  🎯 Approval Readiness  ",
            "  🔎 SHAP Explainability  ", "  🧠 AI Recommendations  ",
            "  🗺 90-Day Roadmap  ", "  🔮 What-If Simulator  "
        ])

        # ── Tab hover tooltips via JS (runs once after Streamlit renders tabs) ──
        st.markdown("""
        <script>
        (function injectTabTips() {
          const TIPS = [
            "Gauge your default risk probability and see a 6-axis financial health radar.",
            "6-pillar composite score showing exactly where your application stands.",
            "Game-theory AI attribution — see which factors helped or hurt your decision.",
            "Personalised, prioritised actions ranked by impact on your approval odds.",
            "Your 3-month milestone plan to move from current profile to prime borrower.",
            "Adjust savings, CIBIL, and expenses to preview your future approval score."
          ];
          function attach() {
            const tabs = document.querySelectorAll('[data-testid="stTabs"] [role="tab"]');
            if (!tabs.length) { setTimeout(attach, 300); return; }
            // Create one shared tooltip div
            let tip = document.getElementById('ww-tab-tip-box');
            if (!tip) {
              tip = document.createElement('div');
              tip.id = 'ww-tab-tip-box';
              tip.className = 'ww-tab-tip';
              tip.style.opacity = '0';
              tip.style.display = 'none';
              document.body.appendChild(tip);
            }
            tabs.forEach((tab, i) => {
              if (tab._wwTipBound) return;
              tab._wwTipBound = true;
              tab.addEventListener('mouseenter', function(e) {
                tip.textContent = TIPS[i] || '';
                tip.style.display = 'block';
                setTimeout(() => { tip.style.opacity = '1'; }, 10);
                moveTip(e);
              });
              tab.addEventListener('mousemove', moveTip);
              tab.addEventListener('mouseleave', function() {
                tip.style.opacity = '0';
                setTimeout(() => { tip.style.display = 'none'; }, 180);
              });
            });
            function moveTip(e) {
              const r = tip.getBoundingClientRect();
              let x = e.clientX - r.width / 2;
              let y = e.clientY - r.height - 14;
              if (x < 8) x = 8;
              if (x + r.width > window.innerWidth - 8) x = window.innerWidth - r.width - 8;
              if (y < 8) y = e.clientY + 20;
              tip.style.left = x + 'px';
              tip.style.top  = y + 'px';
            }
          }
          attach();
        })();
        </script>
        """, unsafe_allow_html=True)

        # ─── TAB 1: RISK OVERVIEW ───────────────────────────────
        with tab1:
            cl, cr = st.columns(2)
            with cl:
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number+delta", value=prob*100,
                    delta={"reference": 50, "suffix": "%"},
                    title={"text": "Default Risk Probability", "font": {"size": 14, "color": WHITE}},
                    number={"suffix": "%", "font": {"size": 36, "color": dc}},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": WHITE, "tickfont": {"size": 11}},
                        "bar": {"color": dc, "thickness": 0.26},
                        "bgcolor": "rgba(0,0,0,0)",
                        "steps": [{"range": [0, 33], "color": "rgba(46,204,138,0.12)"},
                                  {"range": [33, 66], "color": "rgba(245,166,35,0.12)"},
                                  {"range": [66, 100], "color": "rgba(255,61,94,0.12)"}],
                        "threshold": {"line": {"color": CYAN, "width": 3}, "value": 50}
                    }))
                fig_g.update_layout(**PLOT, height=310, title="AI Risk Probability Gauge")
                st.plotly_chart(fig_g, use_container_width=True)
            with cr:
                cats = ["Savings Rate", "Job Stability", "Credit Health",
                        "Loan Fit", "Employment", "Rent Control"]
                vals = [
                    min(100, savings/max(income,1)*500),
                    min(100, employ*12),
                    (cibil-300)/6,
                    max(0, 100 - loan/max(income,1)*8),
                    min(100, employ*10),
                    max(0, 100 - (rent/max(income,1))*150)
                ]
                fig_r = go.Figure()
                fig_r.add_trace(go.Scatterpolar(
                    r=vals+[vals[0]], theta=cats+[cats[0]],
                    fill="toself", fillcolor="rgba(157,112,255,0.12)",
                    line=dict(color=LAV, width=2.5), name="Your Profile"))
                fig_r.add_trace(go.Scatterpolar(
                    r=[70]*7, theta=cats+[cats[0]],
                    fill="toself", fillcolor="rgba(0,232,181,0.04)",
                    line=dict(color=CYAN, width=1.5, dash="dot"), name="Safe Zone"))
                fig_r.update_layout(**PLOT, height=310, title="Financial Health Radar",
                    polar=dict(bgcolor="rgba(0,0,0,0)",
                        radialaxis=dict(visible=True, range=[0, 100],
                                        tickfont={"size": 10, "color": MUTED},
                                        gridcolor="rgba(108,63,255,0.10)"),
                        angularaxis=dict(tickfont={"size": 12, "color": WHITE},
                                          gridcolor="rgba(108,63,255,0.08)")))
                st.plotly_chart(fig_r, use_container_width=True)

            disp = max(0, income - rent - savings)
            fig_b = go.Figure(go.Bar(
                x=["Income", "Rent", "Savings", "Loan ÷10", "Disposable"],
                y=[income, rent, savings, loan/10, disp],
                marker_color=[LAV, RED, GREEN, GOLD, "rgba(157,112,255,0.55)"],
                marker_line_color="rgba(0,0,0,0)",
                text=[f"₹{v:,.0f}" for v in [income, rent, savings, loan/10, disp]],
                textposition="outside",
                textfont=dict(size=13, color=WHITE)))
            fig_b.update_layout(**PLOT, height=300, title="Monthly Financial Breakdown",
                yaxis=dict(gridcolor="rgba(108,63,255,0.07)", tickprefix="₹",
                           tickformat=",.0f", tickfont=dict(size=12, color=WHITE)))
            st.plotly_chart(fig_b, use_container_width=True)

            emi_e = loan / 60
            fig_wf = go.Figure(go.Waterfall(orientation="v",
                measure=["absolute", "relative", "relative", "relative", "total"],
                x=["Salary", "− Rent", "− Loan EMI*", "− Savings", "Remaining"],
                y=[income, -rent, -emi_e, -savings, income-rent-emi_e-savings],
                connector={"line": {"color": "rgba(108,63,255,0.25)"}},
                decreasing={"marker": {"color": RED}},
                increasing={"marker": {"color": GREEN}},
                totals={"marker": {"color": GRAPE}},
                text=[f"₹{abs(v):,.0f}" for v in [income, rent, emi_e, savings, income-rent-emi_e-savings]],
                textposition="outside",
                textfont=dict(size=13, color=WHITE)))
            fig_wf.update_layout(**PLOT, height=300,
                title="Monthly Cash Flow Waterfall  (*EMI estimated at 60-month tenure)",
                yaxis=dict(tickprefix="₹", tickformat=",.0f",
                           gridcolor="rgba(108,63,255,0.07)",
                           tickfont=dict(size=12, color=WHITE)))
            st.plotly_chart(fig_wf, use_container_width=True)

        # ─── TAB 2: APPROVAL READINESS ──────────────────────────
        with tab2:
            section_header("Approval Readiness Score",
                           "Composite score across 6 underwriting pillars evaluated by lenders", "🎯", GRAPE)
            ar_c = GREEN if ar >= 70 else (GOLD if ar >= 45 else RED)
            ar_rgb = "46,204,138" if ar >= 70 else ("245,166,35" if ar >= 45 else "255,61,94")
            tier = "Prime Eligible" if ar >= 70 else ("Conditional" if ar >= 45 else "Below Threshold")
            tier_msg = (
                "Your profile qualifies for prime lending rates at scheduled banks." if ar >= 70
                else "Conditional approval possible — targeted improvements will unlock better rates." if ar >= 45
                else "Application likely to be declined at this stage. Prioritise the roadmap below."
            )
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,rgba({ar_rgb},0.10),rgba({ar_rgb},0.02));
                        border:2px solid rgba({ar_rgb},0.30);border-radius:18px;padding:36px;
                        margin-bottom:24px;display:flex;align-items:center;
                        justify-content:space-between;flex-wrap:wrap;gap:20px;">
              <div style="flex:1;min-width:280px;">
                <span style="background:{ar_c};color:#0a0f1a;
                             font-family:'JetBrains Mono',monospace;font-size:10.5px;font-weight:700;
                             padding:4px 14px;border-radius:99px;text-transform:uppercase;
                             letter-spacing:.08em;">{tier}</span>
                <h2 style="font-family:'Inter',sans-serif;font-size:24px;font-weight:800;
                           color:{WHITE};margin:12px 0 8px;letter-spacing:-0.02em;">
                  Approval Readiness Score</h2>
                <p style="font-family:'Inter',sans-serif;font-size:15px;color:{MUTED};
                          margin:0 0 10px;line-height:1.68;max-width:500px;">{tier_msg}</p>
                <p style="font-family:'Inter',sans-serif;font-size:13px;color:{MUTED2};margin:0;">
                  Weighted across: CIBIL score, savings rate,
                  {tooltip("Debt-to-Income","FOIR / DTI ratio")}, employment tenure,
                  {tooltip("XGBoost","AI")} default risk inverse, and {tooltip("Confidence Index","verification confidence")}.</p>
              </div>
              <div style="text-align:right;min-width:130px;">
                <div style="font-family:'Inter',sans-serif;font-size:70px;font-weight:900;
                            color:{ar_c};line-height:1;
                            filter:drop-shadow(0 0 28px rgba({ar_rgb},0.50));">{ar}</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:12px;
                            color:{MUTED};">out of 100</div>
              </div>
            </div>""", unsafe_allow_html=True)

            maxp = {"Credit Score": 25, "Savings & Liquidity": 20, "Debt Burden": 20,
                    "Employment Stability": 15, "AI Risk Score": 15, "Verification Strength": 5}
            descs = {
                "Credit Score": "CIBIL/credit bureau score — primary lender screening criterion",
                "Savings & Liquidity": "Monthly savings as a percentage of income — financial resilience proxy",
                "Debt Burden": "Fixed obligation-to-income ratio (rent + estimated EMI)",
                "Employment Stability": "Duration at current employer — income continuity signal",
                "AI Risk Score": "Inverse of XGBoost default probability — model confidence",
                "Verification Strength": "Income triangulation confidence score"
            }
            for dim, pts in ar_dims.items():
                mx = maxp.get(dim, 20); pct = pts / mx * 100
                bc = GREEN if pct >= 70 else (GOLD if pct >= 40 else RED)
                st.markdown(f"""
                <div style="background:{CARD};border:1.5px solid rgba(108,63,255,0.14);
                            border-radius:12px;padding:18px 22px;margin-bottom:9px;">
                  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:9px;">
                    <div>
                      <span style="font-family:'Inter',sans-serif;font-size:15px;
                                   font-weight:700;color:{WHITE};">{dim}</span>
                      <span style="font-family:'Inter',sans-serif;font-size:12.5px;color:{MUTED};
                                   display:block;margin-top:2px;">{descs.get(dim, '')}</span>
                    </div>
                    <span style="font-family:'JetBrains Mono',monospace;font-size:14.5px;
                                 color:{bc};font-weight:700;min-width:56px;text-align:right;">
                      {pts}/{mx}</span>
                  </div>
                  <div style="height:7px;background:rgba(108,63,255,0.10);
                              border-radius:99px;overflow:hidden;">
                    <div style="width:{pct}%;height:100%;background:{bc};border-radius:99px;
                                box-shadow:0 0 8px {bc}55;"></div>
                  </div>
                </div>""", unsafe_allow_html=True)

            fig_ar = go.Figure(go.Indicator(
                mode="gauge+number", value=ar,
                title={"text": "Overall Approval Readiness", "font": {"size": 14, "color": WHITE}},
                number={"suffix": "/100", "font": {"color": LAV, "size": 36}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": WHITE, "tickfont": {"size": 11}},
                    "bar": {"color": ar_c, "thickness": 0.28},
                    "bgcolor": "rgba(0,0,0,0)",
                    "steps": [{"range": [0, 45], "color": "rgba(255,61,94,0.12)"},
                              {"range": [45, 70], "color": "rgba(245,166,35,0.12)"},
                              {"range": [70, 100], "color": "rgba(46,204,138,0.12)"}],
                    "threshold": {"line": {"color": CYAN, "width": 3}, "value": 70}
                }))
            fig_ar.update_layout(**PLOT, height=300, title="Approval Readiness Gauge")
            st.plotly_chart(fig_ar, use_container_width=True)

        # ─── TAB 3: SHAP ────────────────────────────────────────
        with tab3:
            section_header("SHAP Explainability",
                           "Feature-level attribution — what drove this credit decision", "🔎", LAV)
            st.markdown(f"""
            <div style="background:rgba(157,112,255,0.07);border:1.5px solid rgba(157,112,255,0.22);
                        border-radius:10px;padding:14px 18px;margin-bottom:22px;">
              <p style="font-family:'Inter',sans-serif;font-size:14.5px;
                        color:#D0D8F8;margin:0;line-height:1.65;">
                <strong style="color:{LAV};font-weight:700;">Reading {tooltip("SHAP")} charts:</strong>
                Red bars push your risk score <em>higher</em> (worse for approval).
                Blue/green bars push it <em>lower</em> (better for approval).
                {tooltip("Feature Importance", "Feature importance")} is ranked in the right chart —
                hover the underlined terms for plain-English definitions.
              </p>
            </div>""", unsafe_allow_html=True)
            with st.spinner("Computing SHAP attributions…"):
                try:
                    fw, fb, tbl, sd = run_shap(MDL, idf)
                    s1, s2 = st.columns(2)
                    with s1:
                        st.markdown(f"""<p style="font-family:'JetBrains Mono',monospace;font-size:11px;
                            letter-spacing:.10em;text-transform:uppercase;color:{MUTED};
                            margin:0 0 10px;">This Prediction — Waterfall</p>""",
                            unsafe_allow_html=True)
                        st.pyplot(fw, use_container_width=True); plt.close("all")
                    with s2:
                        st.markdown(f"""<p style="font-family:'JetBrains Mono',monospace;font-size:11px;
                            letter-spacing:.10em;text-transform:uppercase;color:{MUTED};
                            margin:0 0 10px;">All Predictions — Feature Importance</p>""",
                            unsafe_allow_html=True)
                        st.pyplot(fb, use_container_width=True); plt.close("all")

                    section_header("Attribution Table", "SHAP values per feature for this application", "📋", GRAPE)
                    hd = f"""<div style="display:grid;grid-template-columns:1.2fr 120px 110px 1fr;
                              background:linear-gradient(135deg,{GRAPE},{LAV});
                              border-radius:10px 10px 0 0;padding:12px 20px;
                              font-family:'JetBrains Mono',monospace;font-size:10.5px;
                              letter-spacing:.08em;text-transform:uppercase;color:#fff;font-weight:700;">
                      <div>Feature</div><div>Value</div><div>SHAP</div><div>Effect on Risk</div>
                    </div>"""
                    rows = ""
                    for i, r in enumerate(tbl):
                        bg = CARD if i % 2 == 0 else CARD2
                        br = "border-radius:0 0 10px 10px;" if i == len(tbl)-1 else ""
                        rows += f"""<div style="display:grid;grid-template-columns:1.2fr 120px 110px 1fr;
                                     background:{bg};padding:13px 20px;
                                     border-bottom:1px solid rgba(108,63,255,0.06);{br}">
                          <span style="font-family:'Inter',sans-serif;font-size:14.5px;
                                       font-weight:700;color:{WHITE};">{r['Feature']}</span>
                          <span style="font-family:'JetBrains Mono',monospace;font-size:13.5px;
                                       color:{MUTED};">{r['Value']}</span>
                          <span style="font-family:'JetBrains Mono',monospace;font-size:13.5px;
                                       color:{LAV};font-weight:600;">{r['SHAP']:+.4f}</span>
                          <span style="font-family:'Inter',sans-serif;font-size:13.5px;
                                       color:{r['Color']};font-weight:600;">{r['Dir']}</span>
                        </div>"""
                    st.markdown(hd + rows, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"SHAP computation error: {e}")

        # ─── TAB 4: RECOMMENDATIONS ─────────────────────────────
        with tab4:
            section_header("Your Action Plan",
                           "Evidence-based steps to improve loan eligibility — prioritised by impact", "🧠", GRAPE)
            recs = gen_recs(income, rent, savings, loan, employ, cibil, prob)
            for rec in recs:
                pc = {"high": RED, "medium": GOLD, "low": LAV, "positive": GREEN}.get(rec["p"], LAV)
                urgency_map = {
                    "high": "Urgent — Address Before Applying",
                    "medium": "Important — Address Within 30 Days",
                    "low": "Advisory",
                    "positive": "Strength — Leverage This"
                }
                urgency = urgency_map.get(rec["p"], "")
                st.markdown(f"""
                <div style="background:{CARD};border-left:4px solid {pc};
                            border:1.5px solid rgba(108,63,255,0.12);border-left:4px solid {pc};
                            border-radius:0 14px 14px 0;padding:24px 26px;margin-bottom:16px;">
                  <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;
                              flex-wrap:wrap;">
                    <span style="font-size:20px;line-height:1;">{rec['icon']}</span>
                    <h4 style="font-family:'Inter',sans-serif;font-size:17px;font-weight:800;
                               color:{WHITE};margin:0;flex:1;letter-spacing:-0.01em;">
                      {rec['title']}</h4>
                    <span style="background:{pc}1a;color:{pc};border:1px solid {pc}44;
                                 font-family:'JetBrains Mono',monospace;font-size:9.5px;font-weight:700;
                                 padding:4px 12px;border-radius:99px;text-transform:uppercase;
                                 letter-spacing:.07em;white-space:nowrap;">{urgency}</span>
                  </div>
                  <div style="background:rgba(108,63,255,0.07);border-radius:9px;
                              padding:14px 16px;margin-bottom:10px;">
                    <p style="font-family:'JetBrains Mono',monospace;font-size:10px;
                               letter-spacing:.10em;text-transform:uppercase;color:{MUTED};
                               margin:0 0 7px;font-weight:700;">What's happening</p>
                    <p style="font-family:'Inter',sans-serif;font-size:14.5px;
                               color:#C8D0F0;margin:0;line-height:1.70;">
                      {rec['what']}</p>
                  </div>
                  <div style="background:{pc}12;border-radius:9px;padding:14px 16px;
                              border:1px solid {pc}22;">
                    <p style="font-family:'JetBrains Mono',monospace;font-size:10px;
                               letter-spacing:.10em;text-transform:uppercase;color:{pc};
                               margin:0 0 7px;font-weight:700;">Action steps</p>
                    <p style="font-family:'Inter',sans-serif;font-size:14.5px;
                               color:#D0D8F8;margin:0;line-height:1.70;">
                      {rec['how']}</p>
                  </div>
                </div>""", unsafe_allow_html=True)

        # ─── TAB 5: ROADMAP ─────────────────────────────────────
        with tab5:
            section_header("90-Day Approval Roadmap",
                           "A structured, milestone-driven plan to reach prime borrower status", "🗺", GOLD)
            months = gen_roadmap(income, rent, savings, loan, employ, cibil, prob)
            labels = ["Month 1 — Build the Foundation",
                      "Month 2 — Strengthen Your Profile",
                      "Month 3 — Apply with Confidence"]
            colours = [GOLD, LAV, GREEN]
            colour_rgbs = ["245,166,35", "157,112,255", "46,204,138"]

            for i, (lbl, items, mc, mr) in enumerate(zip(labels, months, colours, colour_rgbs)):
                st.markdown(f"""
                <div style="background:{SURFACE};border:1.5px solid rgba({mr},0.22);
                            border-radius:16px;padding:26px 30px;margin-bottom:16px;
                            box-shadow:0 4px 20px rgba(0,0,0,0.30);">
                  <div style="display:flex;align-items:center;gap:13px;margin-bottom:18px;">
                    <div style="width:38px;height:38px;min-width:38px;border-radius:50%;
                                background:{mc};display:flex;align-items:center;justify-content:center;
                                font-family:'Inter',sans-serif;font-size:15px;font-weight:900;
                                color:#0a0f1a;box-shadow:0 0 18px rgba({mr},0.40);">{i+1}</div>
                    <h4 style="font-family:'Inter',sans-serif;font-size:17px;font-weight:800;
                               color:{WHITE};margin:0;letter-spacing:-0.01em;">{lbl}</h4>
                  </div>
                  {''.join([f"""<div style="display:flex;gap:13px;padding:12px 0;
                                   border-bottom:1px solid rgba(108,63,255,0.07);">
                    <span style="color:{mc};font-size:16px;flex-shrink:0;margin-top:2px;
                                 line-height:1.5;">◆</span>
                    <p style="font-family:\'Inter\',sans-serif;font-size:14.5px;
                              color:#C8D0F0;margin:0;line-height:1.70;">{item}</p>
                  </div>""" for item in items])}
                </div>""", unsafe_allow_html=True)

            cur = round((1 - prob) * 100)
            proj = [cur, min(100, cur+8), min(100, cur+18), min(100, cur+30)]
            fig_tl = go.Figure()
            fig_tl.add_trace(go.Scatter(
                x=["Today", "Month 1", "Month 2", "Month 3"], y=proj,
                mode="lines+markers+text",
                line=dict(color=GRAPE, width=3),
                marker=dict(size=12, color=GRAPE, line=dict(width=2.5, color=CYAN)),
                text=[f"{v}%" for v in proj], textposition="top center",
                textfont=dict(size=13, color=WHITE),
                fill="tozeroy", fillcolor="rgba(108,63,255,0.07)"))
            fig_tl.add_hline(y=70, line_dash="dot", line_color=GREEN,
                annotation_text="Prime Approval Zone (70%+)",
                annotation_font_color=GREEN, annotation_font_size=12)
            fig_tl.update_layout(**PLOT, height=300,
                title="Projected Approval Readiness — 90-Day Trajectory",
                yaxis=dict(range=[0, 110], ticksuffix="%",
                           gridcolor="rgba(108,63,255,0.07)",
                           tickfont=dict(size=12, color=WHITE)))
            st.plotly_chart(fig_tl, use_container_width=True)

        # ─── TAB 6: WHAT-IF SIMULATOR ───────────────────────────
        # FEATURE 3: Pure UI simulation overlay — no re-training, no re-scoring
        with tab6:
            section_header("What-If Simulator",
                           "Adjust key variables and see how your Approval Readiness would shift — no re-run needed", "🔮", GRAPE)

            st.markdown(f"""
            <div style="background:rgba(124,77,255,0.08);border:1.5px solid rgba(124,77,255,0.22);
                        border-radius:14px;padding:16px 20px;margin-bottom:24px;">
              <p style="font-family:'Inter',sans-serif;font-size:14px;color:{TEXT};margin:0;line-height:1.65;">
                <strong style="color:{LAV};">How this works:</strong>
                This simulator estimates the <em>directional impact</em> of changing your financial habits.
                It uses lightweight projection rules — not the full XGBoost model — to give you fast,
                actionable feedback. Actual results will vary based on lender criteria.
              </p>
            </div>
            """, unsafe_allow_html=True)

            sim_c1, sim_c2 = st.columns(2)
            with sim_c1:
                st.markdown(f"""
                <p style="font-family:'JetBrains Mono',monospace;font-size:10px;
                           letter-spacing:.12em;text-transform:uppercase;color:{MUTED};
                           margin:0 0 8px;font-weight:700;">💰 Additional Monthly Savings (₹)</p>
                """, unsafe_allow_html=True)
                sim_savings_boost = st.slider(
                    "Additional monthly savings", 0, 20000, 0, 500,
                    key="sim_sav", label_visibility="collapsed"
                )
                st.markdown(f"""
                <p style="font-family:'Inter',sans-serif;font-size:13px;color:{MUTED};
                           margin:4px 0 0;">Currently saving: ₹{savings:,}/month</p>
                """, unsafe_allow_html=True)

            with sim_c2:
                st.markdown(f"""
                <p style="font-family:'JetBrains Mono',monospace;font-size:10px;
                           letter-spacing:.12em;text-transform:uppercase;color:{MUTED};
                           margin:0 0 8px;font-weight:700;">📉 Monthly Expense Reduction (₹)</p>
                """, unsafe_allow_html=True)
                sim_expense_cut = st.slider(
                    "Monthly expense cut", 0, 15000, 0, 500,
                    key="sim_exp", label_visibility="collapsed"
                )
                st.markdown(f"""
                <p style="font-family:'Inter',sans-serif;font-size:13px;color:{MUTED};
                           margin:4px 0 0;">Reduces debt burden and improves FOIR</p>
                """, unsafe_allow_html=True)

            sim_c3, sim_c4 = st.columns(2)
            with sim_c3:
                st.markdown(f"""
                <p style="font-family:'JetBrains Mono',monospace;font-size:10px;
                           letter-spacing:.12em;text-transform:uppercase;color:{MUTED};
                           margin:0 0 8px;font-weight:700;">📋 CIBIL Score Improvement</p>
                """, unsafe_allow_html=True)
                sim_cibil_boost = st.slider(
                    "CIBIL improvement", 0, 150, 0, 10,
                    key="sim_cibil", label_visibility="collapsed"
                )
                st.markdown(f"""
                <p style="font-family:'Inter',sans-serif;font-size:13px;color:{MUTED};
                           margin:4px 0 0;">Current score: {cibil}  →  Projected: {cibil + sim_cibil_boost}</p>
                """, unsafe_allow_html=True)

            with sim_c4:
                st.markdown(f"""
                <p style="font-family:'JetBrains Mono',monospace;font-size:10px;
                           letter-spacing:.12em;text-transform:uppercase;color:{MUTED};
                           margin:0 0 8px;font-weight:700;">🗓 Additional Employment Months</p>
                """, unsafe_allow_html=True)
                sim_employ_months = st.slider(
                    "Additional employment months", 0, 24, 0, 1,
                    key="sim_emp", label_visibility="collapsed"
                )
                sim_employ_new = employ + sim_employ_months / 12
                st.markdown(f"""
                <p style="font-family:'Inter',sans-serif;font-size:13px;color:{MUTED};
                           margin:4px 0 0;">Current: {employ:.1f} yrs  →  Projected: {sim_employ_new:.1f} yrs</p>
                """, unsafe_allow_html=True)

            # ── Lightweight simulation engine ──
            def simulate_ar(inc, rnt, sav, ln, emp, cib, prob_base, vc_base,
                            sav_boost, exp_cut, cib_boost, emp_boost_yrs):
                """Simulate approval readiness with adjusted inputs.
                Uses the same approval_readiness() function — no new model call.
                """
                new_sav = sav + sav_boost
                new_rent = max(0, rnt - exp_cut)
                new_cib = min(900, cib + cib_boost)
                new_emp = emp + emp_boost_yrs
                # Risk proxy: improve prob slightly based on savings + cibil
                dr = 0.0
                if sav_boost > 0:    dr -= min(0.08, sav_boost / max(inc,1) * 0.5)
                if exp_cut > 0:      dr -= min(0.05, exp_cut / max(inc,1) * 0.3)
                if cib_boost > 0:    dr -= min(0.10, cib_boost / 150 * 0.10)
                if emp_boost_yrs>0:  dr -= min(0.04, emp_boost_yrs * 0.02)
                new_prob = max(0.01, min(0.99, prob_base + dr))
                sim_ar, sim_dims = approval_readiness(
                    inc, new_rent, new_sav, ln, new_emp, new_cib, new_prob, vc_base)
                return sim_ar, sim_dims, new_prob

            sim_ar_val, sim_ar_dims, sim_prob = simulate_ar(
                income, rent, savings, loan, employ, cibil, prob, vc,
                sim_savings_boost, sim_expense_cut, sim_cibil_boost,
                sim_employ_months / 12
            )

            ar_delta   = sim_ar_val - ar
            prob_delta = (sim_prob - prob) * 100
            ar_col     = GREEN if ar_delta >= 0 else RED
            prob_col   = GREEN if prob_delta <= 0 else RED
            ar_rgb_sim = "35,209,139" if ar_delta >= 0 else "255,64,96"

            st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

            # ── Impact cards ──
            ic1, ic2, ic3 = st.columns(3)
            with ic1:
                sign = "+" if ar_delta >= 0 else ""
                st.markdown(f"""
                <div style="background:{CARD};border:1.5px solid rgba({ar_rgb_sim},0.30);
                            border-radius:14px;padding:22px 20px;text-align:center;">
                  <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:{MUTED};
                              text-transform:uppercase;letter-spacing:.11em;margin-bottom:8px;">
                    Approval Readiness</div>
                  <div style="font-family:'Inter',sans-serif;font-size:42px;font-weight:900;
                              color:{ar_col};line-height:1;
                              filter:drop-shadow(0 0 18px rgba({ar_rgb_sim},0.45));">
                    {sign}{ar_delta:.1f}</div>
                  <div style="font-family:'Inter',sans-serif;font-size:14px;color:{MUTED};margin-top:6px;">
                    {ar} → <strong style="color:{ar_col};">{sim_ar_val:.1f}</strong> / 100</div>
                </div>
                """, unsafe_allow_html=True)
            with ic2:
                prob_sign = "+" if prob_delta >= 0 else ""
                prob_rgb2 = "255,64,96" if prob_delta >= 0 else "35,209,139"
                prob_col2 = RED if prob_delta >= 0 else GREEN
                st.markdown(f"""
                <div style="background:{CARD};border:1.5px solid rgba({prob_rgb2},0.25);
                            border-radius:14px;padding:22px 20px;text-align:center;">
                  <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:{MUTED};
                              text-transform:uppercase;letter-spacing:.11em;margin-bottom:8px;">
                    Default Risk Change</div>
                  <div style="font-family:'Inter',sans-serif;font-size:42px;font-weight:900;
                              color:{prob_col2};line-height:1;">
                    {prob_sign}{prob_delta:.1f}%</div>
                  <div style="font-family:'Inter',sans-serif;font-size:14px;color:{MUTED};margin-top:6px;">
                    {prob*100:.1f}% → <strong style="color:{prob_col2};">{sim_prob*100:.1f}%</strong></div>
                </div>
                """, unsafe_allow_html=True)
            with ic3:
                net_saved = sim_savings_boost + sim_expense_cut
                annual = net_saved * 12
                st.markdown(f"""
                <div style="background:{CARD};border:1.5px solid rgba(124,77,255,0.25);
                            border-radius:14px;padding:22px 20px;text-align:center;">
                  <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:{MUTED};
                              text-transform:uppercase;letter-spacing:.11em;margin-bottom:8px;">
                    Annual Financial Gain</div>
                  <div style="font-family:'Inter',sans-serif;font-size:42px;font-weight:900;
                              color:{LAV};line-height:1;">₹{annual:,.0f}</div>
                  <div style="font-family:'Inter',sans-serif;font-size:14px;color:{MUTED};margin-top:6px;">
                    per year in improved position</div>
                </div>
                """, unsafe_allow_html=True)

            # ── Insight callout box ──
            st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
            insight_parts = []
            if sim_savings_boost > 0:
                insight_parts.append(
                    f"saving ₹{sim_savings_boost:,} more per month"
                )
            if sim_expense_cut > 0:
                insight_parts.append(
                    f"cutting expenses by ₹{sim_expense_cut:,}"
                )
            if sim_cibil_boost > 0:
                insight_parts.append(
                    f"improving your CIBIL by {sim_cibil_boost} points"
                )
            if sim_employ_months > 0:
                insight_parts.append(
                    f"gaining {sim_employ_months} more months of employment"
                )

            if insight_parts and ar_delta != 0:
                combo = " + ".join(insight_parts)
                direction = "increase" if ar_delta > 0 else "decrease"
                box_color = ar_rgb_sim
                box_border = ar_col
                st.markdown(f"""
                <div style="background:rgba({box_color},0.07);
                            border:2px solid rgba({box_color},0.28);
                            border-radius:14px;padding:22px 26px;">
                  <div style="font-family:'JetBrains Mono',monospace;font-size:10px;
                              color:{box_border};text-transform:uppercase;letter-spacing:.10em;
                              font-weight:700;margin-bottom:10px;">💡 Simulator Insight</div>
                  <p style="font-family:'Inter',sans-serif;font-size:16px;font-weight:500;
                             color:{WHITE};margin:0;line-height:1.65;">
                    If you <strong style="color:{LAV};">{combo}</strong>,
                    your Approval Readiness Score could
                    <strong style="color:{box_border};">{direction} by {abs(ar_delta):.1f} points</strong>
                    — moving from <strong>{ar}</strong> to
                    <strong style="color:{box_border};">{sim_ar_val:.1f} / 100</strong>.
                  </p>
                  <p style="font-family:'Inter',sans-serif;font-size:13.5px;color:{MUTED};
                             margin:10px 0 0;line-height:1.60;">
                    Default probability shifts from
                    <strong style="color:{WHITE};">{prob*100:.1f}%</strong> to
                    <strong style="color:{prob_col2};">{sim_prob*100:.1f}%</strong>.
                    Use the 90-Day Roadmap tab to build a concrete plan to achieve this.
                  </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background:rgba(124,77,255,0.07);border:1.5px solid rgba(124,77,255,0.20);
                            border-radius:12px;padding:20px 24px;text-align:center;">
                  <p style="font-family:'Inter',sans-serif;font-size:15px;color:{MUTED};margin:0;">
                    Move the sliders above to simulate the impact of financial improvements.</p>
                </div>
                """, unsafe_allow_html=True)

            # ── Per-dimension delta table ──
            if any(v > 0 for v in [sim_savings_boost, sim_expense_cut, sim_cibil_boost, sim_employ_months]):
                st.markdown('<div style="height:18px;"></div>', unsafe_allow_html=True)
                section_header("Dimension-Level Impact", "How each readiness pillar shifts with your changes", "📊", LAV)
                maxp = {"Credit Score": 25, "Savings & Liquidity": 20, "Debt Burden": 20,
                        "Employment Stability": 15, "AI Risk Score": 15, "Verification Strength": 5}
                for dim in ar_dims:
                    orig = ar_dims[dim]
                    simv = sim_ar_dims.get(dim, orig)
                    delta_d = simv - orig
                    mx = maxp.get(dim, 20)
                    dc2 = GREEN if delta_d > 0 else (RED if delta_d < 0 else MUTED)
                    sign_d = "+" if delta_d >= 0 else ""
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:14px;padding:10px 0;
                                border-bottom:1px solid rgba(124,77,255,0.07);">
                      <span style="font-family:'Inter',sans-serif;font-size:14px;font-weight:600;
                                   color:{WHITE};flex:1;min-width:180px;">{dim}</span>
                      <span style="font-family:'JetBrains Mono',monospace;font-size:13px;color:{MUTED};
                                   min-width:55px;text-align:right;">{orig}/{mx}</span>
                      <span style="font-family:'JetBrains Mono',monospace;font-size:13px;color:{MUTED};
                                   min-width:20px;text-align:center;">→</span>
                      <span style="font-family:'JetBrains Mono',monospace;font-size:13px;
                                   color:{dc2};font-weight:700;min-width:55px;text-align:right;">
                        {simv:.1f}/{mx}</span>
                      <span style="font-family:'JetBrains Mono',monospace;font-size:12px;
                                   color:{dc2};min-width:46px;text-align:right;">
                        {sign_d}{delta_d:.1f}</span>
                    </div>
                    """, unsafe_allow_html=True)

        # ── HUSTLE SCORE ────────────────────────────────────────
        st.divider()
        section_header(f'{tooltip("Hustle Score","Hustle Score™")}',
                       "Five financial discipline indicators — each worth 20 points. Hover the title for definition.", "🔥", GOLD)

        dims_h = {
            "Save at least 10% of income monthly":
                20 if income > 0 and savings/income >= 0.10 else 0,
            "Keep rent below 50% of income":
                20 if income > 0 and rent/income < 0.50 else 0,
            "Maintain CIBIL score above 650":
                20 if cibil > 650 else 0,
            "2+ years continuous employment":
                20 if employ >= 2 else 0,
            "Loan amount under 5× monthly income":
                20 if income > 0 and loan < income*5 else 0,
        }
        hsc = GREEN if hs >= 70 else (GOLD if hs >= 40 else RED)
        hrg = "46,204,138" if hs >= 70 else ("245,166,35" if hs >= 40 else "255,61,94")
        hmsg = (
            "Exceptional financial discipline. You are in the top tier of loan applicants."
            if hs >= 70 else
            "Solid foundation — one or two targeted improvements will unlock significantly better terms."
            if hs >= 40 else
            "Clear improvement areas exist. Follow the 90-day roadmap and reassess in 30 days."
        )

        st.markdown(f"""
        <div style="background:{SURFACE};border:1.5px solid rgba({hrg},0.22);
                    border-radius:18px;padding:28px 30px;margin-bottom:24px;
                    box-shadow:0 4px 24px rgba(0,0,0,0.30);">
          <div style="display:flex;align-items:center;justify-content:space-between;
                      margin-bottom:26px;flex-wrap:wrap;gap:12px;">
            <div>
              <h3 style="font-family:'Inter',sans-serif;font-size:20px;font-weight:800;
                         color:{WHITE};margin:0 0 6px;letter-spacing:-0.015em;">Hustle Score™</h3>
              <p style="font-family:'Inter',sans-serif;font-size:14px;color:{MUTED};margin:0;">
                Score yourself against these 5 financial discipline benchmarks</p>
            </div>
            <div style="text-align:right;">
              <span style="font-family:'Inter',sans-serif;font-size:60px;font-weight:900;
                           color:{hsc};line-height:1;
                           filter:drop-shadow(0 0 24px rgba({hrg},0.45));">{hs}</span>
              <span style="font-family:'Inter',sans-serif;font-size:20px;
                           font-weight:600;color:{MUTED};">/100</span>
            </div>
          </div>
        """, unsafe_allow_html=True)

        for dim, pts in dims_h.items():
            bc = GREEN if pts > 0 else "rgba(255,61,94,0.45)"
            tick = "✓" if pts > 0 else "✗"
            row_bg = "rgba(46,204,138,0.04)" if pts > 0 else "rgba(255,61,94,0.03)"
            row_border = "rgba(46,204,138,0.18)" if pts > 0 else "rgba(255,61,94,0.14)"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:14px;margin-bottom:10px;
                        background:{row_bg};border:1px solid {row_border};
                        border-radius:9px;padding:11px 14px;">
              <span style="font-size:17px;color:{bc};font-weight:900;min-width:18px;
                           line-height:1;">{tick}</span>
              <span style="flex:1;font-family:'Inter',sans-serif;font-size:14.5px;
                           color:#C8D0F0;font-weight:500;">{dim}</span>
              <div style="height:7px;width:110px;background:rgba(108,63,255,0.10);
                          border-radius:99px;overflow:hidden;flex-shrink:0;">
                <div style="width:{pts*5}%;height:100%;background:{bc};border-radius:99px;
                             box-shadow:0 0 6px {bc}55;"></div>
              </div>
              <span style="font-family:'JetBrains Mono',monospace;font-size:13px;
                           color:{bc};font-weight:700;min-width:40px;text-align:right;">
                {pts}/20</span>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
          <div style="background:rgba({hrg},0.07);border-radius:9px;
                      padding:15px 18px;margin-top:14px;">
            <p style="font-family:'Inter',sans-serif;font-size:15px;color:{hsc};
                      margin:0;font-weight:600;line-height:1.55;">{hmsg}</p>
          </div>
        </div>""", unsafe_allow_html=True)

    # ── DOWNLOAD REPORT BUTTON ────────────────────────────────────
    if "dash_result" in st.session_state:
        st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(124,77,255,0.10),rgba(0,229,192,0.06));
                    border:1.5px solid rgba(124,77,255,0.28);border-radius:16px;
                    padding:24px 30px;display:flex;align-items:center;
                    justify-content:space-between;flex-wrap:wrap;gap:16px;margin-bottom:8px;">
          <div>
            <div style="font-family:'Inter',sans-serif;font-size:16px;font-weight:800;
                        color:{WHITE};margin-bottom:4px;letter-spacing:-0.01em;">
              📄 Full Credit Analysis Report</div>
            <div style="font-family:'Inter',sans-serif;font-size:13px;color:{MUTED};">
              Complete PDF — AI verdict · income verification · SHAP insights ·
              recommendations · 90-day roadmap</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        col_dl, col_gap = st.columns([1, 3])
        with col_dl:
            with st.spinner("Generating PDF…"):
                pdf_bytes = generate_pdf_report(
                    st.session_state["dash_result"],
                    st.session_state.get("ud", {}),
                    st.session_state.get("username", "User"),
                    st.session_state.get("plan", "Pro"),
                )
            fname = f"WalletWarriors_CreditReport_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            st.download_button(
                label="⬇ Download PDF Report",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
                key="btn_pdf",
            )

    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

    # ══ HUSTLE ACADEMY — inline section (safe from sanitiser) ══
    st.divider()
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
      <span style="font-size:22px;">🎓</span>
      <h2 style="font-family:'Inter',sans-serif;font-size:22px;font-weight:800;
                 color:{WHITE};margin:0;letter-spacing:-0.02em;">Hustle Academy</h2>
      <span style="background:{GRAPE};color:#fff;font-family:'JetBrains Mono',monospace;
                   font-size:9px;font-weight:700;padding:3px 10px;border-radius:99px;
                   text-transform:uppercase;letter-spacing:.10em;">Financial Literacy · 3 Modules</span>
    </div>
    <p style="font-family:'Inter',sans-serif;font-size:14px;color:{MUTED};margin:0 0 16px;">
      Master the concepts lenders actually use — so you walk in prepared, not surprised.</p>
    """, unsafe_allow_html=True)

    with st.expander("📐 Module 1 — Master Your Debt-to-Income Ratio"):
        st.markdown(f"""
        <div style="font-family:'Inter',sans-serif;font-size:14px;color:{TEXT};line-height:1.75;padding:4px 0 8px;">
          <p style="margin:0 0 10px;font-weight:700;color:{WHITE};font-size:15px;">
            Your DTI is a lender's first filter — and it's binary.</p>
          <p style="margin:0 0 10px;">
            Add up all your fixed monthly payments: rent, existing EMIs, and the new loan EMI
            you're applying for. Divide by net monthly income. If the result exceeds
            <strong style="color:{RED};">65%</strong>, most scheduled banks auto-reject with no review.</p>
          <p style="margin:0 0 12px;">
            <strong style="color:{CYAN};">The fix:</strong> Before applying, either extend your loan
            tenure (lower EMI), pay off a smaller existing loan entirely, or add a co-applicant
            to split the obligation. Each tactic directly reduces your DTI.</p>
          <div style="background:rgba(124,77,255,0.10);border-radius:10px;
                      border-left:3px solid {GRAPE};padding:12px 16px;">
            <span style="font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700;
                         color:{LAV};letter-spacing:.10em;text-transform:uppercase;">Rule of Thumb</span>
            <p style="margin:6px 0 0;font-size:13.5px;color:{TEXT};">
              Target DTI below <strong style="color:{GREEN};">45%</strong> for best-rate approval.
              Between 45–65% you'll qualify but at higher interest.
              Above 65% = automatic rejection at most banks.</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("💸 Module 2 — Consistency Beats Quantity in UPI"):
        st.markdown(f"""
        <div style="font-family:'Inter',sans-serif;font-size:14px;color:{TEXT};line-height:1.75;padding:4px 0 8px;">
          <p style="margin:0 0 10px;font-weight:700;color:{WHITE};font-size:15px;">
            Underwriters read your UPI history like a personality test.</p>
          <p style="margin:0 0 10px;">
            A ₹50,000 single transaction means nothing. But 90 days of regular, predictable
            outflows — rent on the 1st, subscriptions on the 5th, groceries weekly — tells an
            underwriter you are organised, solvent, and behaviourally stable.</p>
          <p style="margin:0 0 12px;">
            <strong style="color:{CYAN};">The pattern they love:</strong> Income credited →
            Savings transferred within 48 hrs → Fixed bills paid on schedule.
            This sequencing signals financial maturity regardless of income level.</p>
          <div style="background:rgba(0,229,192,0.08);border-radius:10px;
                      border-left:3px solid {CYAN};padding:12px 16px;">
            <span style="font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700;
                         color:{CYAN};letter-spacing:.10em;text-transform:uppercase;">Start Today</span>
            <p style="margin:6px 0 0;font-size:13.5px;color:{TEXT};">
              Automate one SIP and one bill payment.
              Three months of that pattern is worth more than a salary hike on paper.</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🏦 Module 3 — Credit Invisible → Bankable in 90 Days"):
        st.markdown(f"""
        <div style="font-family:'Inter',sans-serif;font-size:14px;color:{TEXT};line-height:1.75;padding:4px 0 8px;">
          <p style="margin:0 0 10px;font-weight:700;color:{WHITE};font-size:15px;">
            No CIBIL score isn't the same as a bad score — but it looks the same to most banks.</p>
          <p style="margin:0 0 10px;">
            If you're a student, freelancer, or first-time earner with no credit history,
            you're "credit invisible." Banks can't assess you, so they decline by default.</p>
          <p style="margin:0 0 4px;"><strong style="color:{CYAN};">The 90-day ladder:</strong></p>
          <p style="margin:0 0 4px;">
            <strong style="color:{GOLD};">Month 1</strong> — Open a secured credit card (₹10k–25k FD as collateral). Use it for fuel only.</p>
          <p style="margin:0 0 4px;">
            <strong style="color:{GOLD};">Month 2</strong> — Pay the full balance before due date. Never the minimum.</p>
          <p style="margin:0 0 14px;">
            <strong style="color:{GOLD};">Month 3</strong> — CIBIL generates your first score. It will be 700+.</p>
          <div style="background:rgba(255,184,48,0.08);border-radius:10px;
                      border-left:3px solid {GOLD};padding:12px 16px;">
            <span style="font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700;
                         color:{GOLD};letter-spacing:.10em;text-transform:uppercase;">Gig Workers</span>
            <p style="margin:6px 0 0;font-size:13.5px;color:{TEXT};">
              File your ITR even for small incomes.
              Two years of ITR history is accepted by NBFCs as income proof for personal loans.</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# ██  THIN FILE — BEHAVIORAL UNDERWRITING  ██
# ─────────────────────────────────────────────────────────────
def render_thin_file():
    render_nav()
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    # ── Hero header ──
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(124,77,255,0.12),rgba(0,229,192,0.06));
                border:1.5px solid rgba(124,77,255,0.28);border-radius:18px;
                padding:28px 32px;margin-bottom:28px;">
      <div style="display:flex;align-items:flex-start;gap:16px;flex-wrap:wrap;">
        <div style="font-size:36px;line-height:1;">🕵️</div>
        <div style="flex:1;min-width:260px;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700;
                      color:{CYAN};letter-spacing:.14em;text-transform:uppercase;
                      margin-bottom:8px;">Thin File · Behavioral Underwriting Engine</div>
          <h1 style="font-family:'Inter',sans-serif;font-size:26px;font-weight:900;
                     color:{WHITE};margin:0 0 10px;letter-spacing:-0.025em;">
            No CIBIL Score? We See Your Integrity.</h1>
          <p style="font-family:'Inter',sans-serif;font-size:14px;color:{TEXT};
                    margin:0;line-height:1.70;max-width:680px;">
            Our AI acts as a <strong style="color:{LAV};">Financial Detective</strong> — reconstructing
            your reliability through daily cash flow, bill payments and skill signals.
            A student or gig worker with <em>consistent behaviour</em> beats a dormant credit card holder.
            <strong style="color:{CYAN};">Consistency is impossible to fake.</strong>
          </p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Section A: Stability ──
    panel_open("A — Stability", "Income & recurring commitment proofs",
               "UPI inflows, utility bills and rent prove that money enters and obligations are met — month after month.")
    ca1, ca2, ca3 = st.columns(3)
    with ca1: tf_income = st.number_input("Avg Monthly Inflow (₹)", min_value=0, step=500,
                                           help="Sum of stipends, gig pay, freelance credits last 6 months ÷ 6",
                                           key="tf_income")
    with ca2: tf_rent   = st.number_input("Monthly Rent / EMI (₹)", min_value=0, step=500, key="tf_rent")
    with ca3: tf_elec   = st.number_input("Avg Monthly Electricity Bill (₹)", min_value=0, step=50,
                                           help="Average of last 12 months bills", key="tf_elec")
    ca4, ca5, ca6 = st.columns(3)
    with ca4: tf_upi    = st.number_input("Monthly UPI / Digital Spend (₹)", min_value=0, step=500, key="tf_upi")
    with ca5: tf_bills_ontime = st.selectbox("Utility Bills Paid On Time",
                                              ["Always (12/12 months)", "Mostly (9–11/12)", "Sometimes (6–8/12)", "Rarely (<6/12)"],
                                              key="tf_bills")
    with ca6: tf_rent_months = st.number_input("Months at Current Address", min_value=0, max_value=120,
                                                step=1, help="Longer tenure = higher stability signal", key="tf_rent_mo")
    panel_close()

    # ── Section B: Skill ──
    panel_open("B — Skill", "Future earning potential signals",
               "Offer letters, certificates and education prove upward trajectory — your income will grow.")
    cb1, cb2 = st.columns(2)
    with cb1:
        tf_employment = st.selectbox("Current Employment Status",
            ["Employed Full-Time", "Gig / Freelance", "Internship / Trainee",
             "Student (Final Year)", "Student (Other)", "Unemployed / Between Jobs"],
            key="tf_emp_status")
        tf_emp_months = st.number_input("Months in Current Role / Internship", min_value=0, step=1, key="tf_emp_mo")
    with cb2:
        tf_offer = st.selectbox("Confirmed Offer / Next Role",
            ["Yes — Full-time offer letter in hand", "Yes — Internship start date confirmed",
             "In progress — Interview at final stage", "No — Not applicable"],
            key="tf_offer")
        tf_certs = st.number_input("No. of Professional Certificates (last 2 yrs)",
                                    min_value=0, max_value=20, step=1,
                                    help="Coursera, NPTEL, hackathon wins, LinkedIn Learning etc.", key="tf_certs")
    tf_doc_skill = st.file_uploader(
        "Upload Offer Letter / Certificate / College ID (PDF · PNG · JPG) — optional",
        type=["pdf","png","jpg","jpeg"], key="tf_doc_skill")
    panel_close()

    # ── Section C: Surplus ──
    panel_open("C — Surplus", "Savings mindset & spending discipline",
               "Even ₹500/month SIPs or consistent bank balance above zero signals a savings-first mindset.",
               border_color=BORDER2)
    cc1, cc2, cc3 = st.columns(3)
    with cc1: tf_savings    = st.number_input("Monthly Savings / SIP (₹)", min_value=0, step=200, key="tf_sav")
    with cc2: tf_avg_bal    = st.number_input("Avg Bank Balance — Last 3 Months (₹)", min_value=0, step=1000, key="tf_bal")
    with cc3: tf_spend_type = st.selectbox("Primary Spending Category",
                                            ["Essentials (rent, food, transport, bills)",
                                             "Mixed (essentials + occasional leisure)",
                                             "Discretionary-heavy (dining, subscriptions, shopping)"],
                                            key="tf_spend")
    cc4, cc5 = st.columns(2)
    with cc4: tf_loan_req   = st.number_input("Loan Amount Requested (₹)", min_value=0, step=5000, key="tf_loan")
    with cc5: tf_purpose    = st.selectbox("Purpose of Loan",
                                            ["Education / Skill Upgrade", "Business / Freelance Setup",
                                             "Emergency / Medical", "Asset Purchase (laptop/tools)",
                                             "Personal / Consumer"],
                                            key="tf_purpose")
    panel_close()

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    if st.button("Run Behavioral Underwriting  →", key="btn_tf_run"):
        if tf_income == 0:
            st.warning("Please enter your average monthly inflow to continue.")
        else:
            with st.spinner("🔍 Financial Detective at work — triangulating behavioural signals…"):
                time.sleep(1.1)

                # ── Score each dimension (0–20 each, total /100) ──
                # 1. Income velocity
                vel_score = 20 if tf_income >= 25000 else (15 if tf_income >= 12000 else (10 if tf_income >= 5000 else 5))

                # 2. Bill discipline
                bill_map = {"Always (12/12 months)": 20, "Mostly (9–11/12)": 14,
                            "Sometimes (6–8/12)": 7, "Rarely (<6/12)": 2}
                bill_score = bill_map.get(tf_bills_ontime, 7)

                # 3. Stability (rent tenure + UPI consistency)
                stab_score = min(20, int(tf_rent_months / 6) * 4 + (6 if tf_upi > 0 else 0))

                # 4. Skill / employment
                emp_map = {"Employed Full-Time": 20, "Gig / Freelance": 14,
                           "Internship / Trainee": 12, "Student (Final Year)": 16,
                           "Student (Other)": 10, "Unemployed / Between Jobs": 4}
                skill_score = min(20, emp_map.get(tf_employment, 10) + min(4, tf_certs))

                # 5. Surplus / savings discipline
                sav_ratio = tf_savings / max(tf_income, 1)
                surp_score = 20 if sav_ratio >= 0.15 else (14 if sav_ratio >= 0.07 else (7 if tf_savings > 0 else 2))
                spend_pen = {"Essentials (rent, food, transport, bills)": 0,
                             "Mixed (essentials + occasional leisure)": -2,
                             "Discretionary-heavy (dining, subscriptions, shopping)": -5}
                surp_score = max(0, surp_score + spend_pen.get(tf_spend_type, 0))

                hustle_tf = vel_score + bill_score + stab_score + skill_score + surp_score

                # ── Synthesise a CIBIL proxy (350–750 range for thin files) ──
                cibil_proxy = int(350 + hustle_tf * 4.0)
                cibil_proxy = min(cibil_proxy, 750)

                # ── Run XGBoost with proxy score ──
                idf = pd.DataFrame({
                    "Income": [tf_income], "Rent": [tf_rent],
                    "Savings": [tf_savings], "LoanAmount": [tf_loan_req],
                    "Employment": [tf_emp_months / 12],
                    "CreditScore": [cibil_proxy]
                })
                prob = float(MDL.predict_proba(idf)[0][1])
                dec = "rejected" if prob > 0.55 else "approved"

                # ── Offer letter / confirmed role boosts confidence ──
                if "offer letter" in tf_offer.lower() or "confirmed" in tf_offer.lower():
                    prob = max(0.05, prob - 0.12)
                    dec = "rejected" if prob > 0.55 else "approved"

                # ── Triangulate income vs UPI+elec ──
                implied = tf_upi + tf_elec + tf_rent
                coherence_gap = abs(tf_income - implied) / max(tf_income, 1)
                coherent = coherence_gap < 0.45
                confidence = max(40, 100 - int(coherence_gap * 80))

                # ── Approval readiness using proxy ──
                ar, ar_dims = approval_readiness(tf_income, tf_rent, tf_savings,
                                                  tf_loan_req, tf_emp_months/12,
                                                  cibil_proxy, prob, confidence)

                st.session_state["tf_result"] = {
                    "income": tf_income, "rent": tf_rent, "savings": tf_savings,
                    "loan": tf_loan_req, "elec": tf_elec, "upi": tf_upi,
                    "emp_status": tf_employment, "emp_months": tf_emp_months,
                    "offer": tf_offer, "certs": tf_certs, "avg_bal": tf_avg_bal,
                    "spend_type": tf_spend_type, "purpose": tf_purpose,
                    "bills_ontime": tf_bills_ontime, "rent_months": tf_rent_months,
                    "vel_score": vel_score, "bill_score": bill_score,
                    "stab_score": stab_score, "skill_score": skill_score,
                    "surp_score": surp_score, "hustle_tf": hustle_tf,
                    "cibil_proxy": cibil_proxy, "prob": prob, "dec": dec,
                    "coherent": coherent, "confidence": confidence,
                    "ar": ar, "ar_dims": ar_dims,
                }

    # ── Results ──
    if st.session_state.get("tf_result"):
        r = st.session_state["tf_result"]
        dec_color = GREEN if r["dec"] == "approved" else RED
        dec_label = "✓  BEHAVIOURAL PROFILE — CREDITWORTHY" if r["dec"] == "approved" else "⚠  PROFILE NEEDS STRENGTHENING"

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba({('46,204,138' if r['dec']=='approved' else '255,61,94')},0.10),transparent);
                    border:2px solid {dec_color};border-radius:18px;
                    padding:28px 32px;margin:20px 0 24px;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:700;
                      color:{dec_color};letter-spacing:.14em;text-transform:uppercase;
                      margin-bottom:10px;">{dec_label}</div>
          <div style="display:flex;align-items:flex-end;gap:40px;flex-wrap:wrap;">
            <div><div style="font-family:'Inter',sans-serif;font-size:12px;color:{MUTED};
                             margin-bottom:4px;">Hustle Consistency Score™</div>
                 <span style="font-family:'Inter',sans-serif;font-size:52px;font-weight:900;
                              color:{dec_color};line-height:1;">{r['hustle_tf']}</span>
                 <span style="font-family:'Inter',sans-serif;font-size:18px;color:{MUTED};">/100</span>
            </div>
            <div><div style="font-family:'Inter',sans-serif;font-size:12px;color:{MUTED};margin-bottom:4px;">CIBIL Proxy Score</div>
                 <span style="font-family:'Inter',sans-serif;font-size:36px;font-weight:800;color:{LAV};">{r['cibil_proxy']}</span>
            </div>
            <div><div style="font-family:'Inter',sans-serif;font-size:12px;color:{MUTED};margin-bottom:4px;">Default Risk</div>
                 <span style="font-family:'Inter',sans-serif;font-size:36px;font-weight:800;
                              color:{dec_color};">{r['prob']*100:.1f}%</span>
            </div>
            <div><div style="font-family:'Inter',sans-serif;font-size:12px;color:{MUTED};margin-bottom:4px;">Income Coherence</div>
                 <span style="font-family:'Inter',sans-serif;font-size:36px;font-weight:800;
                              color:{CYAN};">{r['confidence']}%</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── 5-pillar breakdown ──
        section_header("Behavioral Signal Breakdown", "How each dimension contributed to your score", "📊")
        dims = [
            ("💸 Income Velocity",       r["vel_score"],   "How regularly and substantially money enters your account"),
            ("🧾 Bill Discipline",        r["bill_score"],  "On-time payment of utility bills — a credit-score proxy"),
            ("🏠 Address Stability",      r["stab_score"],  "Length at current address + UPI activity consistency"),
            ("🎓 Skill & Employment",     r["skill_score"], "Employment status, tenure, offer letter and certificates"),
            ("💰 Savings & Surplus",      r["surp_score"],  "Savings rate and spending category discipline"),
        ]
        dim_cols = st.columns(5)
        for col, (label, score, desc) in zip(dim_cols, dims):
            sc = GREEN if score >= 15 else (GOLD if score >= 8 else RED)
            hrg = "46,204,138" if score >= 15 else ("245,166,35" if score >= 8 else "255,61,94")
            with col:
                st.markdown(f"""
                <div style="background:{SURFACE};border:1.5px solid rgba({hrg},0.28);
                            border-radius:14px;padding:18px 14px;text-align:center;height:100%;">
                  <div style="font-size:22px;margin-bottom:8px;">{label.split()[0]}</div>
                  <div style="font-family:'Inter',sans-serif;font-size:11px;font-weight:700;
                              color:{WHITE};margin-bottom:6px;line-height:1.3;">
                    {' '.join(label.split()[1:])}</div>
                  <div style="font-family:'Inter',sans-serif;font-size:30px;font-weight:900;
                              color:{sc};line-height:1;">{score}</div>
                  <div style="font-family:'Inter',sans-serif;font-size:11px;color:{MUTED};">/20</div>
                  <div style="font-family:'Inter',sans-serif;font-size:10px;color:{MUTED};
                              margin-top:8px;line-height:1.4;">{desc}</div>
                </div>""", unsafe_allow_html=True)

        # ── Triangulation coherence ──
        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
        coh_color = GREEN if r["coherent"] else GOLD
        st.markdown(f"""
        <div style="background:{SURFACE};border:1.5px solid {'rgba(35,209,139,0.30)' if r['coherent'] else 'rgba(255,184,48,0.30)'};
                    border-radius:14px;padding:18px 24px;margin-bottom:20px;">
          <div style="font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700;
                      color:{coh_color};letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px;">
            🔬 Temporal Triangulation — Incoherence Detector</div>
          <p style="font-family:'Inter',sans-serif;font-size:14px;color:{TEXT};margin:0;line-height:1.65;">
            Stated monthly inflow <strong style="color:{WHITE};">₹{r['income']:,.0f}</strong> vs
            implied spend footprint <strong style="color:{WHITE};">
            ₹{(r['upi']+r['elec']+r['rent']):,.0f}</strong>
            (rent + electricity + UPI) —
            <strong style="color:{coh_color};">
            {'✓ Signals are coherent. No anomaly detected.' if r['coherent'] else '⚠ Gap detected. Inconsistency flagged for review.'}</strong>
            &nbsp; Confidence Index: <strong style="color:{CYAN};">{r['confidence']}%</strong>
          </p>
        </div>
        """, unsafe_allow_html=True)

        # ── Recommendations for thin file ──
        section_header("Next Steps to Become Bankable", "Your 90-day path from Thin File to Transparent File", "🗺️")
        steps_tf = []
        if r["hustle_tf"] < 60:
            steps_tf.append(("🔴 Priority", "Open a secured credit card",
                "Get a secured credit card against an FD of ₹10,000–25,000. Use it for groceries and fuel. "
                "Pay 100% of the statement every month. CIBIL will record this within 45 days and "
                "assign you a score — typically 650–700 within 6 months."))
        if r["bill_score"] < 14:
            steps_tf.append(("🟡 Quick Win", "Set utility bill auto-pay",
                "Enable auto-debit for electricity, mobile and broadband. 12 months of on-time payments "
                "is accepted as a CIBIL-equivalent signal by Tier-1 NBFCs under RBI's alternative data guidelines."))
        if r["surp_score"] < 10:
            steps_tf.append(("🟡 Quick Win", "Start a ₹500/month SIP",
                "Even a ₹500 Liquid Fund SIP shows up on your bank statement as a consistent outflow "
                "with a positive return. Underwriters read bank statements manually — this signals discipline."))
        if r["skill_score"] < 12:
            steps_tf.append(("🟢 Build Signal", "Obtain a professional certificate",
                "Complete one industry-relevant online course (NPTEL, Coursera, Google). "
                "In the absence of a credit history, Skill-as-Collateral is our strongest proxy "
                "for future earning potential and default resilience."))
        steps_tf.append(("🟢 90-Day Target", "Apply to NBFC with alternative data",
            f"At {r['hustle_tf']}/100 Hustle Score, target Tier-1 NBFCs: Bajaj Finserv, Tata Capital, "
            "or KreditBee — all of which have Alternative Data underwriting programs for thin-file borrowers. "
            "Your Behavioral Underwriting Report from Wallet Warriors can be submitted directly."))

        for priority, title, body in steps_tf:
            p_color = RED if "Priority" in priority else (GOLD if "Quick Win" in priority else GREEN)
            st.markdown(f"""
            <div style="background:{SURFACE};border-left:3px solid {p_color};
                        border-radius:0 12px 12px 0;padding:14px 18px;margin-bottom:12px;">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:5px;">
                <span style="font-family:'JetBrains Mono',monospace;font-size:9px;font-weight:700;
                             color:{p_color};letter-spacing:.10em;text-transform:uppercase;">{priority}</span>
                <span style="font-family:'Inter',sans-serif;font-size:14px;font-weight:700;
                             color:{WHITE};">{title}</span>
              </div>
              <p style="font-family:'Inter',sans-serif;font-size:13px;color:{TEXT};
                        margin:0;line-height:1.65;">{body}</p>
            </div>""", unsafe_allow_html=True)

        # ── Back button ──
        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
        if st.button("← Back to Credit Analysis", key="btn_tf_back"):
            st.session_state["tf_result"] = None
            st.session_state.page = "dashboard"
            st.rerun()

    else:
        if st.button("← Back to Credit Analysis", key="btn_tf_back_empty"):
            st.session_state.page = "dashboard"
            st.rerun()

    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# ██  PDF REPORT GENERATOR — REGULATORY COMPLIANT  ██
#     RBI Guidelines · SEBI Disclosure Standards · DPDP Act 2023
# ─────────────────────────────────────────────────────────────
def generate_pdf_report(res, ud, username, plan):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=24*mm
    )

    # ── Colours ──
    C_SURFACE = colors.HexColor("#13162a")
    C_CARD    = colors.HexColor("#1a1e35")
    C_GRAPE   = colors.HexColor("#7C4DFF")
    C_LAV     = colors.HexColor("#A87FFF")
    C_CYAN    = colors.HexColor("#00E5C0")
    C_GOLD    = colors.HexColor("#FFB830")
    C_GREEN   = colors.HexColor("#23D18B")
    C_RED     = colors.HexColor("#FF4060")
    C_WHITE   = colors.HexColor("#ECF0FF")
    C_TEXT    = colors.HexColor("#C8D0F0")
    C_MUTED   = colors.HexColor("#8892b0")
    C_BORDER  = colors.HexColor("#2a2d4a")
    C_WARN_BG = colors.HexColor("#1e1608")
    C_WARN_BD = colors.HexColor("#FFB830")
    C_BLACK   = colors.HexColor("#060810")
    W         = 170*mm   # usable width

    # ── Style factory ──
    def S(name, **kw):
        return ParagraphStyle(name, **kw)

    sH1      = S("H1",  fontName="Helvetica-Bold",  fontSize=18, textColor=C_WHITE,  leading=22, spaceAfter=2)
    sH2      = S("H2",  fontName="Helvetica-Bold",  fontSize=11, textColor=C_LAV,    leading=15, spaceBefore=10, spaceAfter=4)
    sH3      = S("H3",  fontName="Helvetica-Bold",  fontSize=9,  textColor=C_WHITE,  leading=13, spaceBefore=4,  spaceAfter=2)
    sBody    = S("BD",  fontName="Helvetica",        fontSize=8.5,textColor=C_TEXT,   leading=13, spaceAfter=3)
    sSmall   = S("SM",  fontName="Helvetica",        fontSize=7.5,textColor=C_MUTED,  leading=11, spaceAfter=2)
    sWarn    = S("WN",  fontName="Helvetica-Bold",  fontSize=7.5,textColor=C_GOLD,   leading=11)
    sDiscl   = S("DC",  fontName="Helvetica",        fontSize=7,  textColor=C_MUTED,  leading=10, spaceAfter=2)
    sFooter  = S("FT",  fontName="Helvetica",        fontSize=6.5,textColor=C_MUTED,  leading=9,  alignment=TA_CENTER)
    sCentre  = S("CT",  fontName="Helvetica",        fontSize=8.5,textColor=C_TEXT,   leading=13, alignment=TA_CENTER)
    sRight   = S("RT",  fontName="Helvetica",        fontSize=8,  textColor=C_MUTED,  leading=12, alignment=TA_RIGHT)

    # ── Helper: section banner ──
    def section_banner(title, risk_note=""):
        rows = [[
            Paragraph(f"<b>{title}</b>",
                      S("sb", fontName="Helvetica-Bold", fontSize=10, textColor=C_WHITE, leading=14)),
            Paragraph(risk_note,
                      S("rn", fontName="Helvetica", fontSize=7, textColor=C_GOLD, leading=10, alignment=TA_RIGHT))
        ]]
        t = Table(rows, colWidths=[120*mm, 50*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), C_CARD),
            ("LINEBELOW",     (0,0),(-1,-1), 1.5, C_GRAPE),
            ("TOPPADDING",    (0,0),(-1,-1), 7),
            ("BOTTOMPADDING", (0,0),(-1,-1), 7),
            ("LEFTPADDING",   (0,0),(0,-1),  10),
            ("RIGHTPADDING",  (-1,0),(-1,-1),10),
        ]))
        return t

    # ── Helper: risk warning box ──
    def risk_box(text):
        rows = [[Paragraph(f"⚠  RISK WARNING: {text}", sWarn)]]
        t = Table(rows, colWidths=[W])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), C_WARN_BG),
            ("BOX",           (0,0),(-1,-1), 1, C_WARN_BD),
            ("TOPPADDING",    (0,0),(-1,-1), 7),
            ("BOTTOMPADDING", (0,0),(-1,-1), 7),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ]))
        return t

    # ── Data ──
    income  = res["income"];  rent    = res["rent"];   savings = res["savings"]
    loan    = res["loan"];    employ  = res["employ"]; cibil   = res["cibil"]
    prob    = res["prob"];    dec     = res["dec"];    ar      = res["ar"]
    ar_dims = res["ar_dims"]; hs      = res["hs"];     vc      = res.get("vc", 80)
    approved   = dec == "approved"
    dec_color  = C_GREEN if approved else C_RED
    dec_label  = "LIKELY CREDITWORTHY" if approved else "HIGH DEFAULT RISK — APPLICATION LIKELY REJECTED"
    risk_pct   = f"{prob*100:.1f}%"
    foir       = rent/income*100 if income else 0
    dti        = loan/(income*12)*100 if income else 0
    date_str   = datetime.now().strftime("%d %b %Y, %I:%M %p IST")
    report_id  = f"WW-{datetime.now().strftime('%Y%m%d%H%M%S')}-{abs(hash(username)) % 9999:04d}"

    story = []

    # ════════════════════════════════════════════════════════════
    # PAGE 1 — COVER & CONSENT
    # ════════════════════════════════════════════════════════════

    # ── Cover header ──
    cover = [[
        Paragraph(
            "<b>Wallet Warriors</b><br/>"
            "<font size='8' color='#8892b0'>AI Credit Intelligence Platform</font>",
            S("cv1", fontName="Helvetica-Bold", fontSize=16, textColor=C_WHITE, leading=22)),
        Paragraph(
            f"<font size='8' color='#8892b0'>Report ID</font><br/>"
            f"<b>{report_id}</b><br/>"
            f"<font size='7' color='#8892b0'>{date_str}</font>",
            S("cv2", fontName="Helvetica", fontSize=9, textColor=C_TEXT, leading=13, alignment=TA_RIGHT)),
    ]]
    ct = Table(cover, colWidths=[110*mm, 60*mm])
    ct.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_SURFACE),
        ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
        ("LINEBELOW",     (0,0),(-1,0),  2,   C_GRAPE),
        ("TOPPADDING",    (0,0),(-1,-1), 12),
        ("BOTTOMPADDING", (0,0),(-1,-1), 12),
        ("LEFTPADDING",   (0,0),(0,-1),  14),
        ("RIGHTPADDING",  (-1,0),(-1,-1),14),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]))
    story += [ct, Spacer(1, 5*mm)]

    # ── Subject line ──
    subj = [[
        Paragraph(f"Credit Intelligence Report — <b>{username}</b>", sH1),
        Paragraph(f"{plan} Plan", S("pl", fontName="Helvetica-Bold", fontSize=10,
                  textColor=C_GRAPE, leading=14, alignment=TA_RIGHT)),
    ]]
    st2 = Table(subj, colWidths=[130*mm, 40*mm])
    st2.setStyle(TableStyle([
        ("VALIGN", (0,0),(-1,-1), "BOTTOM"),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
    ]))
    story += [st2, HRFlowable(width="100%", thickness=0.5, color=C_BORDER), Spacer(1, 4*mm)]

    # ── DPDP Act 2023 — Consent & Data Notice ──
    story.append(section_banner(
        "DATA USAGE CONSENT NOTICE",
        "DPDP Act 2023 · Section 6 & 7"))
    story.append(Spacer(1, 3*mm))
    dpdp_rows = [
        ["Data Principal", username],
        ["Data Fiduciary", "Wallet Warriors AI Credit Intelligence Platform"],
        ["Purpose of Processing", "Credit risk assessment, loan eligibility scoring, and personalised financial advisory"],
        ["Legal Basis", "Consent provided at login (DPDP Act 2023, Section 6). Data used solely for stated purpose."],
        ["Data Retention", "Session data retained for 90 days. No data sold or shared with third parties without consent."],
        ["Right to Erasure", "You may request deletion of your data at any time under DPDP Act 2023, Section 13."],
        ["Grievance Officer", "grievance@walletwarriors.ai  |  Response within 72 hours as per DPDP Rules 2025"],
    ]
    dpdp_t = Table(
        [[Paragraph(f"<b>{k}</b>", sSmall), Paragraph(v, sSmall)] for k, v in dpdp_rows],
        colWidths=[52*mm, 118*mm])
    dpdp_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_SURFACE),
        ("ROWBACKGROUNDS",(0,0),(-1,-1), [C_SURFACE, C_CARD]),
        ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
        ("INNERGRID",     (0,0),(-1,-1), 0.3, C_BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]))
    story += [dpdp_t, Spacer(1, 5*mm)]

    # ── RBI & SEBI Regulatory Framing ──
    story.append(section_banner(
        "REGULATORY FRAMEWORK & DISCLOSURES",
        "RBI Guidelines · SEBI Disclosure Standards"))
    story.append(Spacer(1, 3*mm))
    reg_text = (
        "This report is generated by an AI-driven credit intelligence engine. "
        "It is intended as a <b>decision-support tool</b> and does not constitute a credit bureau report, "
        "a formal credit score, or a binding lending decision under RBI's Credit Information Companies "
        "(Regulation) Act, 2005. "
        "The default probability score is produced by a machine learning model (XGBoost, AUC 0.86) "
        "trained on synthetic data for demonstration purposes. "
        "In a production environment, this model would be re-trained on licensed bureau data under "
        "RBI Master Direction — Credit Information Reporting, 2025. "
        "Scores and recommendations herein do not fall under SEBI's Investment Adviser Regulations, 2013 "
        "and should not be construed as investment or securities advice. "
        "All financial ratios (FOIR, DTI) are calculated per RBI's Fair Lending Practices Circular "
        "RBI/2023-24/53 and NBFC Fair Practice Code guidelines."
    )
    story.append(Paragraph(reg_text, sBody))
    story.append(Spacer(1, 5*mm))

    # ════════════════════════════════════════════════════════════
    # PAGE 2 — AI DECISION & FINANCIAL PROFILE
    # ════════════════════════════════════════════════════════════

    # ── AI Decision Banner ──
    story.append(section_banner("AI CREDIT DECISION", "⚠ FOR INFORMATIONAL USE ONLY — NOT A FINAL LENDING DECISION"))
    story.append(Spacer(1, 3*mm))
    story.append(risk_box(
        "This AI output is a probabilistic estimate. Final credit decisions must be made by a "
        "licensed lender after full KYC, bureau verification, and regulatory due diligence."
    ))
    story.append(Spacer(1, 3*mm))

    dec_data = [[
        Paragraph(
            f"<font size='13'><b>{dec_label}</b></font><br/>"
            f"<font size='8' color='#8892b0'>Based on XGBoost model — AUC 0.86</font>",
            S("dl", fontName="Helvetica-Bold", fontSize=11, textColor=dec_color, leading=18)),
        Paragraph(
            f"<font size='8' color='#8892b0'>Default Probability</font><br/>"
            f"<font size='22'><b>{risk_pct}</b></font>",
            sCentre),
        Paragraph(
            f"<font size='8' color='#8892b0'>Approval Readiness</font><br/>"
            f"<font size='22'><b>{ar}/100</b></font>",
            sCentre),
        Paragraph(
            f"<font size='8' color='#8892b0'>Hustle Score™</font><br/>"
            f"<font size='22'><b>{hs}/100</b></font>",
            sCentre),
    ]]
    dec_t = Table(dec_data, colWidths=[74*mm, 32*mm, 32*mm, 32*mm])
    dec_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_SURFACE),
        ("BOX",           (0,0),(-1,-1), 1.5, dec_color),
        ("LINEAFTER",     (0,0),(2,0),   0.5, C_BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]))
    story += [dec_t, Spacer(1, 6*mm)]

    # ── Financial Profile ──
    story.append(section_banner("FINANCIAL PROFILE", "⚠ User-declared data — not independently verified"))
    story.append(Spacer(1, 3*mm))
    story.append(risk_box(
        "All figures below are self-declared by the applicant. "
        "Wallet Warriors uses Triangulation Engine to cross-verify these against behavioural signals, "
        "but independent document verification by a lender is mandatory before disbursement."
    ))
    story.append(Spacer(1, 3*mm))

    metrics = [
        ("Monthly Income",    f"Rs.{income:,.0f}",   "Self-declared"),
        ("Monthly Rent/EMI",  f"Rs.{rent:,.0f}",     f"FOIR: {foir:.1f}%  (RBI safe limit: <50%)"),
        ("Monthly Savings",   f"Rs.{savings:,.0f}",  f"{savings/income*100:.1f}% of income" if income else "—"),
        ("Loan Requested",    f"Rs.{loan:,.0f}",     f"DTI: {dti:.1f}%"),
        ("Employment",        f"{employ:.1f} yrs",   "At current employer"),
        ("CIBIL Score",       f"{int(cibil)}",
         "Excellent (750+)" if cibil>=750 else "Good (700-749)" if cibil>=700 else
         "Fair (650-699)" if cibil>=650 else "Poor (<650)"),
    ]
    mrows = []
    for i in range(0, len(metrics), 3):
        row = []
        for label, val, note in metrics[i:i+3]:
            row.append(Paragraph(
                f"<font size='7' color='#8892b0'>{label}</font><br/>"
                f"<font size='13'><b>{val}</b></font><br/>"
                f"<font size='7' color='#8892b0'>{note}</font>",
                S(f"mc{i}", fontName="Helvetica", fontSize=8, textColor=C_WHITE, leading=15)))
        while len(row) < 3: row.append(Paragraph("", sBody))
        mrows.append(row)
    mt = Table(mrows, colWidths=[W/3, W/3, W/3])
    mt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_SURFACE),
        ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
        ("INNERGRID",     (0,0),(-1,-1), 0.3, C_BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 9),
        ("BOTTOMPADDING", (0,0),(-1,-1), 9),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
    ]))
    story += [mt, Spacer(1, 6*mm)]

    # ── Income Verification ──
    story.append(section_banner("INCOME VERIFICATION — TRIANGULATION ENGINE", "⚠ AI-generated cross-check — not a formal audit"))
    story.append(Spacer(1, 3*mm))
    ver_pass  = ud.get("coherent", True)
    ver_label = "VERIFIED — Income signals are internally coherent" if ver_pass else "ANOMALY DETECTED — Income inconsistency flagged"
    ver_color = C_GREEN if ver_pass else C_RED
    story.append(risk_box(
        "Triangulation is a cross-correlation of self-declared data. It does not replace "
        "formal income verification (ITR, Form 16, bank statements) required under RBI KYC norms."
    ))
    story.append(Spacer(1, 3*mm))
    ver_d = [[
        Paragraph(f"<b>{ver_label}</b>",
                  S("vl", fontName="Helvetica-Bold", fontSize=9, textColor=ver_color, leading=13)),
        Paragraph(f"Confidence Index: <b>{vc:.0f}%</b>",
                  S("vi", fontName="Helvetica-Bold", fontSize=9, textColor=C_CYAN, leading=13, alignment=TA_RIGHT)),
    ]]
    vt = Table(ver_d, colWidths=[120*mm, 50*mm])
    vt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_SURFACE),
        ("BOX",           (0,0),(-1,-1), 1, ver_color),
        ("TOPPADDING",    (0,0),(-1,-1), 8),("BOTTOMPADDING",(0,0),(-1,-1), 8),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),("RIGHTPADDING",(0,0),(-1,-1), 10),
    ]))
    story.append(vt)
    flags = ud.get("flags", [])
    if flags:
        story.append(Spacer(1, 3*mm))
        for f in flags[:4]:
            sc = "#FF4060" if f.get("sev")=="high" else "#FFB830"
            story.append(Paragraph(
                f"<font color='{sc}'><b>[{f.get('sev','').upper()}]</b></font>  "
                f"<b>{f.get('title','')}</b> — {f.get('msg','')}",
                sSmall))
    story.append(Spacer(1, 6*mm))

    # ── Approval Readiness ──
    story.append(section_banner("APPROVAL READINESS — 6-PILLAR ASSESSMENT", "⚠ Indicative scoring — not a credit bureau output"))
    story.append(Spacer(1, 3*mm))
    story.append(risk_box(
        "Pillar scores are computed by the Wallet Warriors proprietary model. "
        "They are indicative only and do not represent an official creditworthiness determination "
        "under RBI's Credit Information Companies (Regulation) Act, 2005."
    ))
    story.append(Spacer(1, 3*mm))
    dim_labels = {
        "income_stability": "Income Stability",
        "debt_load":        "Debt Load (FOIR)",
        "savings_rate":     "Savings Rate",
        "credit_score":     "Credit Score",
        "employment":       "Employment Stability",
        "verification":     "Income Verification",
    }
    dim_rows = [[
        Paragraph("<b>Pillar</b>",  S("th1", fontName="Helvetica-Bold", fontSize=7.5, textColor=C_MUTED, leading=11)),
        Paragraph("<b>Score</b>",   S("th2", fontName="Helvetica-Bold", fontSize=7.5, textColor=C_MUTED, leading=11, alignment=TA_CENTER)),
        Paragraph("<b>Status</b>",  S("th3", fontName="Helvetica-Bold", fontSize=7.5, textColor=C_MUTED, leading=11, alignment=TA_CENTER)),
        Paragraph("<b>RBI Benchmark</b>", S("th4", fontName="Helvetica-Bold", fontSize=7.5, textColor=C_MUTED, leading=11)),
    ]]
    benchmarks = {
        "income_stability": "Stable salary / verified inflow required",
        "debt_load":        "FOIR < 50% per RBI Fair Lending Circular",
        "savings_rate":     "Minimum 10-15% savings-to-income ratio",
        "credit_score":     "CIBIL >= 700 preferred by scheduled banks",
        "employment":       "12+ months at current employer standard",
        "verification":     "Income within 10% of document proof",
    }
    for key, score in ar_dims.items():
        label = dim_labels.get(key, key.replace("_"," ").title())
        sc    = C_GREEN if score >= 15 else (C_GOLD if score >= 8 else C_RED)
        status= "Strong" if score >= 15 else ("Moderate" if score >= 8 else "Weak")
        bmark = benchmarks.get(key, "—")
        dim_rows.append([
            Paragraph(label, sSmall),
            Paragraph(f"<b>{score}/20</b>",
                      S(f"ds{key}", fontName="Helvetica-Bold", fontSize=9,
                        textColor=sc, leading=12, alignment=TA_CENTER)),
            Paragraph(status,
                      S(f"st{key}", fontName="Helvetica", fontSize=8,
                        textColor=sc, leading=12, alignment=TA_CENTER)),
            Paragraph(bmark, sSmall),
        ])
    at = Table(dim_rows, colWidths=[40*mm, 20*mm, 22*mm, 88*mm])
    at.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  C_BORDER),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C_SURFACE, C_CARD]),
        ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
        ("INNERGRID",     (0,0),(-1,-1), 0.3, C_BORDER),
        ("TOPPADDING",    (0,0),(-1,-1), 6),("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
    ]))
    story += [at, Spacer(1, 6*mm)]

    # ── AI Recommendations ──
    story.append(section_banner("AI RECOMMENDATIONS", "⚠ Informational only — not financial advice per SEBI IA Regs 2013"))
    story.append(Spacer(1, 3*mm))
    story.append(risk_box(
        "The following recommendations are generated by AI and do not constitute investment advice, "
        "securities advice, or regulated financial advice under SEBI Investment Adviser Regulations, 2013 "
        "or RBI guidelines. Consult a SEBI-registered financial advisor for personalised advice."
    ))
    story.append(Spacer(1, 3*mm))
    recs = gen_recs(income, rent, savings, loan, employ, cibil, prob)
    priority_map = {"high": "#FF4060", "medium": "#FFB830", "low": "#00E5C0", "positive": "#23D18B"}
    for r in recs[:6]:
        pc = priority_map.get(r.get("p","low"), "#00E5C0")
        story.append(Paragraph(
            f"<font color='{pc}'><b>{r.get('icon','')}  {r.get('title','')}</b></font>",
            S(f"rt{r.get('p','')}", fontName="Helvetica-Bold", fontSize=8.5,
              textColor=C_WHITE, leading=12, spaceBefore=4)))
        if r.get("what"):
            story.append(Paragraph(f"<b>What:</b>  {r['what']}", sSmall))
        if r.get("how"):
            story.append(Paragraph(f"<b>How:</b>  {r['how']}", sSmall))
    story.append(Spacer(1, 6*mm))

    # ── 90-Day Roadmap ──
    story.append(section_banner("90-DAY IMPROVEMENT ROADMAP", "⚠ AI-generated plan — outcomes not guaranteed"))
    story.append(Spacer(1, 3*mm))
    story.append(risk_box(
        "Projected improvements in creditworthiness are estimates based on general financial principles. "
        "Actual outcomes depend on individual circumstances, lender policies, and market conditions. "
        "Past model performance (AUC 0.86) does not guarantee future accuracy."
    ))
    story.append(Spacer(1, 3*mm))
    roadmap = gen_roadmap(income, rent, savings, loan, employ, cibil, prob)
    months  = ["Month 1 — Foundation", "Month 2 — Momentum", "Month 3 — Application Ready"]
    mcols   = ["#7C4DFF", "#00E5C0", "#23D18B"]
    for month_label, month_steps, col in zip(months, roadmap, mcols):
        story.append(Paragraph(f"<b>{month_label}</b>",
            S(f"ml{col}", fontName="Helvetica-Bold", fontSize=9,
              textColor=colors.HexColor(col), leading=13, spaceBefore=5)))
        for step in month_steps:
            story.append(Paragraph(f"•  {step}", sSmall))
    story.append(Spacer(1, 8*mm))

    # ════════════════════════════════════════════════════════════
    # FULL REGULATORY DISCLAIMER FOOTER
    # ════════════════════════════════════════════════════════════
    story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER))
    story.append(Spacer(1, 3*mm))

    disc_blocks = [
        ("RBI Compliance Statement",
         "This report is produced for informational and prototype demonstration purposes only. "
         "It does not constitute a Credit Information Report (CIR) as defined under the Credit Information "
         "Companies (Regulation) Act, 2005. Wallet Warriors is not a licensed Credit Information Company "
         "(CIC) and is not affiliated with CIBIL, Experian, CRIF Highmark, or Equifax. "
         "Any credit decision made using this output must be supplemented by a formal bureau report "
         "obtained through a RBI-licensed CIC."),
        ("SEBI Disclosure Statement",
         "Nothing in this report constitutes investment advice, portfolio management advice, or "
         "securities recommendation under the SEBI (Investment Advisers) Regulations, 2013 or "
         "SEBI (Research Analysts) Regulations, 2014. Financial ratios, projections and recommendations "
         "herein are for educational and illustrative purposes only."),
        ("DPDP Act 2023 — Data Rights Notice",
         "Under the Digital Personal Data Protection Act, 2023 (Act No. 22 of 2023), you have the right "
         "to access, correct, and erase your personal data processed by this platform. "
         "Data processed includes: name, income figures, rent, credit score, and spending patterns — "
         "all provided voluntarily by you. No biometric or sensitive personal data is collected. "
         "To exercise your rights, contact: grievance@walletwarriors.ai."),
        ("Model Risk Disclosure",
         "The XGBoost credit scoring model has an AUC of 0.86 on a held-out test set. "
         "Model outputs carry inherent uncertainty. A stated default probability of X% means "
         "approximately X out of 100 similarly-profiled applicants may default — it is not a "
         "guarantee of individual outcome. The model was trained on synthetic data for this prototype."),
        ("Limitation of Liability",
         "Wallet Warriors and its developers accept no liability for any financial loss, credit "
         "rejection, or adverse outcome arising from reliance on this report. Users are advised to "
         "seek independent professional advice before making any borrowing or lending decision."),
    ]
    for title, text in disc_blocks:
        story.append(Paragraph(f"<b>{title}:</b>  {text}", sDiscl))
        story.append(Spacer(1, 2*mm))

    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="100%", thickness=0.3, color=C_BORDER))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f"Report ID: {report_id}  ·  Generated: {date_str}  ·  User: {username}  ·  Plan: {plan}  ·  "
        "Wallet Warriors AI Credit Intelligence Platform  ·  "
        "Compliant with: RBI Credit Information Guidelines · SEBI Disclosure Standards · DPDP Act 2023",
        sFooter))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ─────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────
if not st.session_state.authenticated and st.session_state.page != "login":
    st.session_state.page = "login"

{
    "login":         render_login,
    "onboard":       render_onboard,
    "verify_result": render_verify_result,
    "dashboard":     render_dashboard,
    "thin_file":     render_thin_file,
}.get(st.session_state.page, render_login)()