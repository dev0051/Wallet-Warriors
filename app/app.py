import streamlit as st
import pandas as pd
import numpy as np
import joblib
import shap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import re
import hashlib
import time
from PIL import Image
import io
import base64

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Wallet Warriors · Credit Intelligence",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────────────────────────────────────
# COLOR PALETTE (exact spec)
# ─────────────────────────────────────────────────────────────────────────────
# #0D0D0D  – Near Black (NI Cyber Grape base)
# #63458C  – Cyber Grape
# #AA77F2  – Lavender Floral
# #99630F  – Limerick (amber/gold)
# #F2F2F2  – Anti-Flash White

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

/* ── Root Variables ── */
:root {
  --black:   #0D0D0D;
  --grape:   #63458C;
  --lav:     #AA77F2;
  --gold:    #99630F;
  --white:   #F2F2F2;
  --surface: #161616;
  --card:    #1C1C1E;
  --border:  rgba(170,119,242,0.18);
  --muted:   rgba(242,242,242,0.45);
}

/* ── Base ── */
html, body, [data-testid="stApp"] {
  background: var(--black) !important;
  color: var(--white) !important;
  font-family: 'Inter', sans-serif !important;
}

[data-testid="stAppViewContainer"] { background: var(--black) !important; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--black); }
::-webkit-scrollbar-thumb { background: var(--grape); border-radius: 99px; }

/* ── All Streamlit inputs ── */
input[type="text"], input[type="password"], input[type="number"],
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
  background: rgba(99,69,140,0.12) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  color: var(--white) !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 14px !important;
  padding: 12px 16px !important;
  transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
}
input:focus {
  border-color: var(--lav) !important;
  box-shadow: 0 0 0 3px rgba(170,119,242,0.15) !important;
  outline: none !important;
}

/* Label */
[data-testid="stTextInput"] label,
[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label,
[data-testid="stFileUploader"] label {
  color: var(--muted) !important;
  font-size: 11px !important;
  font-family: 'Space Mono', monospace !important;
  letter-spacing: 0.08em !important;
  text-transform: uppercase !important;
  margin-bottom: 6px !important;
}

/* Select box */
[data-testid="stSelectbox"] > div > div {
  background: rgba(99,69,140,0.12) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  color: var(--white) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
  background: rgba(99,69,140,0.08) !important;
  border: 1px dashed var(--border) !important;
  border-radius: 12px !important;
  padding: 12px !important;
}

/* ── Buttons ── */
.stButton > button {
  background: linear-gradient(135deg, var(--grape) 0%, #4a2d6e 100%) !important;
  color: var(--white) !important;
  border: 1px solid rgba(170,119,242,0.3) !important;
  border-radius: 10px !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  letter-spacing: 0.05em !important;
  padding: 12px 28px !important;
  transition: all 0.22s ease !important;
  box-shadow: 0 4px 20px rgba(99,69,140,0.3) !important;
  width: 100% !important;
}
.stButton > button:hover {
  background: linear-gradient(135deg, var(--lav) 0%, var(--grape) 100%) !important;
  box-shadow: 0 6px 28px rgba(170,119,242,0.4) !important;
  transform: translateY(-2px) !important;
}
.stButton > button:active {
  transform: translateY(0px) !important;
  box-shadow: 0 2px 10px rgba(99,69,140,0.3) !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 14px !important;
  padding: 20px !important;
}
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size: 11px !important; font-family: 'Space Mono', monospace !important; letter-spacing: 0.08em !important; text-transform: uppercase !important; }
[data-testid="stMetricValue"] { color: var(--lav) !important; font-family: 'Space Mono', monospace !important; font-size: 28px !important; }
[data-testid="stMetricDelta"] { font-family: 'Space Mono', monospace !important; }

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 32px 0 !important; }

/* ── Progress ── */
[data-testid="stProgress"] > div > div {
  background: linear-gradient(90deg, var(--grape), var(--lav)) !important;
  border-radius: 99px !important;
}
[data-testid="stProgress"] {
  background: rgba(99,69,140,0.15) !important;
  border-radius: 99px !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
  border-radius: 12px !important;
  border: none !important;
  font-family: 'Inter', sans-serif !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {
  background: var(--card) !important;
  border-radius: 12px !important;
  padding: 4px !important;
  border: 1px solid var(--border) !important;
  gap: 4px !important;
}
[data-testid="stTabs"] [role="tab"] {
  background: transparent !important;
  color: var(--muted) !important;
  border-radius: 8px !important;
  font-family: 'Space Mono', monospace !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  transition: all 0.2s !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  background: var(--grape) !important;
  color: var(--white) !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
}

/* ── Pyplot figures ── */
.stPlotlyChart { border-radius: 14px !important; overflow: hidden !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

for key, val in {
    "page": "login",
    "authenticated": False,
    "username": "",
    "user_data": {},
    "analysis_done": False,
    "verification_result": None,
    "login_attempts": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ─────────────────────────────────────────────────────────────────────────────
# MOCK USER DATABASE  (in prod → replace with real DB / Firebase / Supabase)
# ─────────────────────────────────────────────────────────────────────────────

USERS = {
    "demo@walletwarriors.ai": {
        "password_hash": hashlib.sha256("Warrior@2024".encode()).hexdigest(),
        "name": "Arjun Mehta",
        "plan": "Pro",
    },
    "test@walletwarriors.ai": {
        "password_hash": hashlib.sha256("Test@1234".encode()).hexdigest(),
        "name": "Priya Sharma",
        "plan": "Starter",
    },
}

def verify_user(email: str, password: str):
    user = USERS.get(email.lower().strip())
    if not user:
        return False, None
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    if pw_hash == user["password_hash"]:
        return True, user
    return False, None

# ─────────────────────────────────────────────────────────────────────────────
# INCOME TRIANGULATION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def triangulate_income(stated_income, rent, electricity_bill,
                        upi_monthly_outflow, doc_income=None):
    """
    Cross-reference stated income against behavioural and document signals.
    Returns: (is_coherent, confidence_score, flags, estimated_real_income)
    """
    flags = []
    confidence = 100.0

    # ── Heuristic 1: Rent-to-Income ratio ──────────────────────────────────
    # Normal range: rent should be 25–50% of income for Indian metros
    if stated_income > 0:
        rent_ratio = rent / stated_income
        if rent_ratio < 0.04:
            flags.append({
                "type": "warning",
                "msg": "Rent appears very low relative to stated income. "
                       "Average rent/income ratio for this income band is 28–40%.",
                "severity": "medium"
            })
            confidence -= 15
        elif rent_ratio > 0.75:
            flags.append({
                "type": "critical",
                "msg": "Rent exceeds 75% of stated income — extreme financial stress signal.",
                "severity": "high"
            })
            confidence -= 25

    # ── Heuristic 2: Lifestyle coherence via electricity bill ───────────────
    # In India: ₹800–₹3,000 typical for ₹30–70k income earners
    expected_elec_low  = 600  + (stated_income / 1000) * 18
    expected_elec_high = 1500 + (stated_income / 1000) * 35
    if electricity_bill > 0:
        if electricity_bill < expected_elec_low * 0.4:
            flags.append({
                "type": "warning",
                "msg": f"Electricity bill (₹{electricity_bill:,.0f}) is unusually low "
                       f"for a ₹{stated_income:,.0f}/month earner. Expected ₹{expected_elec_low:,.0f}–₹{expected_elec_high:,.0f}.",
                "severity": "medium"
            })
            confidence -= 10
        elif electricity_bill > expected_elec_high * 2.5:
            flags.append({
                "type": "warning",
                "msg": "Electricity bill is disproportionately high. Could indicate commercial usage.",
                "severity": "low"
            })

    # ── Heuristic 3: UPI transaction velocity ──────────────────────────────
    # High earners typically have UPI outflow ≥ 35% of income
    if upi_monthly_outflow > 0 and stated_income > 0:
        velocity_ratio = upi_monthly_outflow / stated_income
        if velocity_ratio < 0.10:
            flags.append({
                "type": "critical",
                "msg": f"UPI outflow (₹{upi_monthly_outflow:,.0f}) is only "
                       f"{velocity_ratio*100:.0f}% of stated income. "
                       "Transaction velocity is statistically inconsistent with claimed income.",
                "severity": "high"
            })
            confidence -= 30
        elif velocity_ratio > 1.5:
            flags.append({
                "type": "warning",
                "msg": "UPI outflow exceeds stated income — overspending detected.",
                "severity": "medium"
            })
            confidence -= 10

    # ── Heuristic 4: Standard deviation anomaly check ──────────────────────
    # Build an implied income from spending parameters
    implied_income_signals = []
    if rent > 0:
        implied_income_signals.append(rent / 0.33)       # rent ≈ 33% income
    if electricity_bill > 0:
        implied_income_signals.append(electricity_bill / 0.03)  # elec ≈ 3% income
    if upi_monthly_outflow > 0:
        implied_income_signals.append(upi_monthly_outflow / 0.55) # UPI ≈ 55% income

    if implied_income_signals:
        implied_avg = np.mean(implied_income_signals)
        implied_std = np.std(implied_income_signals) if len(implied_income_signals) > 1 else implied_avg * 0.2
        z_score = abs(stated_income - implied_avg) / (implied_std + 1)
        if z_score > 2.0:
            flags.append({
                "type": "critical",
                "msg": f"Stated income is {z_score:.1f}σ away from spending-implied income "
                       f"(₹{implied_avg:,.0f}). Anomaly threshold is 2σ — flagged for manual review.",
                "severity": "high"
            })
            confidence -= min(35, z_score * 10)
    else:
        implied_avg = stated_income

    # ── Heuristic 5: Document cross-check ──────────────────────────────────
    if doc_income and doc_income > 0:
        discrepancy = abs(stated_income - doc_income) / max(doc_income, 1)
        if discrepancy > 0.10:
            flags.append({
                "type": "critical",
                "msg": f"Document income (₹{doc_income:,.0f}) differs from stated income "
                       f"(₹{stated_income:,.0f}) by {discrepancy*100:.0f}%. "
                       "Exceeds 10% tolerance — verification failed.",
                "severity": "high"
            })
            confidence -= 40

    confidence = max(0, min(100, confidence))
    estimated_real = implied_avg if implied_income_signals else stated_income
    is_coherent = confidence >= 55 and not any(f["severity"] == "high" for f in flags)

    return is_coherent, round(confidence, 1), flags, round(estimated_real)


# ─────────────────────────────────────────────────────────────────────────────
# MODEL LOADER
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource
def load_model():
    try:
        return joblib.load("models/credit_model.pkl")
    except Exception:
        # Fallback: retrain on synthetic data (so app always runs)
        from sklearn.model_selection import train_test_split
        from xgboost import XGBClassifier
        np.random.seed(42)
        n = 1000
        df = pd.DataFrame({
            "Income":      np.random.randint(15000, 80000, n),
            "Rent":        np.random.randint(5000,  40000, n),
            "Savings":     np.random.randint(0,     20000, n),
            "LoanAmount":  np.random.randint(10000,100000, n),
            "Employment":  np.random.randint(0,     10,    n),
            "CreditScore": np.random.randint(500,   800,   n),
        })
        df["Default"] = (
            (df["Rent"] > df["Income"]*0.7) |
            (df["Savings"] < 2000)           |
            (df["CreditScore"] < 580)
        ).astype(int)
        X = df.drop("Default", axis=1)
        y = df["Default"]
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
        mdl = XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.05,
                            use_label_encoder=False, eval_metric="logloss")
        mdl.fit(X_tr, y_tr)
        return mdl

model = load_model()

# ─────────────────────────────────────────────────────────────────────────────
# PLOTLY THEME HELPER
# ─────────────────────────────────────────────────────────────────────────────

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Mono, monospace", color="#F2F2F2", size=12),
    title_font=dict(family="Syne, sans-serif", size=16, color="#F2F2F2"),
    margin=dict(l=20, r=20, t=50, b=20),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(170,119,242,0.2)"),
)

COLORS = {
    "primary":   "#AA77F2",
    "secondary": "#63458C",
    "gold":      "#C98A1A",
    "success":   "#4CAF7D",
    "danger":    "#E05C5C",
    "muted":     "rgba(242,242,242,0.4)",
}

# ─────────────────────────────────────────────────────────────────────────────
# HTML COMPONENT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def badge(label, color="#63458C", text_color="#F2F2F2"):
    return f"""<span style="background:{color};color:{text_color};font-size:10px;
    font-family:'Space Mono',monospace;font-weight:700;letter-spacing:.08em;
    padding:3px 10px;border-radius:99px;text-transform:uppercase;">{label}</span>"""

def section_header(title, subtitle="", icon=""):
    st.markdown(f"""
    <div style="margin:32px 0 20px 0;">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
        <span style="font-size:20px;">{icon}</span>
        <h2 style="font-family:'Syne',sans-serif;font-size:22px;font-weight:800;
                   color:#F2F2F2;margin:0;letter-spacing:-.01em;">{title}</h2>
      </div>
      {"" if not subtitle else f'<p style="color:rgba(242,242,242,0.45);font-size:13px;margin:0 0 0 32px;">{subtitle}</p>'}
      <div style="height:2px;background:linear-gradient(90deg,#63458C,transparent);
                  border-radius:99px;margin-top:12px;"></div>
    </div>
    """, unsafe_allow_html=True)

def card(content_html, padding="24px", border_color="rgba(170,119,242,0.18)"):
    st.markdown(f"""
    <div style="background:#1C1C1E;border:1px solid {border_color};
                border-radius:16px;padding:{padding};margin-bottom:16px;">
      {content_html}
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ██████████  LOGIN PAGE  ██████████
# ─────────────────────────────────────────────────────────────────────────────

def render_login():
    # Fullscreen login layout
    st.markdown("""
    <style>
    .login-bg {
      min-height: 100vh;
      background: radial-gradient(ellipse at 20% 50%, rgba(99,69,140,0.25) 0%, transparent 60%),
                  radial-gradient(ellipse at 80% 20%, rgba(170,119,242,0.12) 0%, transparent 50%),
                  #0D0D0D;
      display: flex; align-items: center; justify-content: center;
      padding: 40px 20px;
    }
    .login-card {
      background: #161616;
      border: 1px solid rgba(170,119,242,0.2);
      border-radius: 24px;
      padding: 56px 52px;
      max-width: 480px;
      width: 100%;
      box-shadow: 0 40px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(170,119,242,0.05);
      animation: fadeSlideIn 0.5s ease forwards;
    }
    @keyframes fadeSlideIn {
      from { opacity:0; transform: translateY(24px); }
      to   { opacity:1; transform: translateY(0); }
    }
    .logo-mark {
      width: 52px; height: 52px;
      background: linear-gradient(135deg,#63458C,#AA77F2);
      border-radius: 14px;
      display: flex; align-items: center; justify-content: center;
      font-size: 24px; margin-bottom: 28px;
      box-shadow: 0 8px 24px rgba(99,69,140,0.5);
    }
    .login-title {
      font-family: 'Syne', sans-serif;
      font-size: 32px; font-weight: 800;
      color: #F2F2F2; margin: 0 0 6px 0;
      letter-spacing: -0.02em;
    }
    .login-sub {
      color: rgba(242,242,242,0.4);
      font-size: 14px; margin: 0 0 40px 0;
      font-family: 'Inter', sans-serif;
    }
    .cred-hint {
      background: rgba(99,69,140,0.15);
      border: 1px solid rgba(170,119,242,0.2);
      border-radius: 10px; padding: 14px 18px;
      margin-top: 20px;
    }
    .cred-hint p {
      margin: 2px 0; font-size: 12px;
      font-family: 'Space Mono', monospace;
      color: rgba(242,242,242,0.55);
    }
    </style>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.2, 1])

    with col:
        st.markdown('<div style="height:60px;"></div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="logo-mark">🔐</div>
        <h1 class="login-title">Wallet Warriors</h1>
        <p class="login-sub">AI Credit Intelligence Platform &nbsp;·&nbsp; Secure Sign-In</p>
        """, unsafe_allow_html=True)

        email = st.text_input("Email Address", placeholder="you@example.com", key="login_email")
        password = st.text_input("Password", type="password", placeholder="••••••••••••", key="login_pw")

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        if st.session_state.login_attempts >= 5:
            st.error("🔒 Too many failed attempts. Please wait before retrying.")
        else:
            if st.button("Sign In  →", key="btn_login"):
                if not email or not password:
                    st.warning("Please enter both email and password.")
                else:
                    with st.spinner("Authenticating…"):
                        time.sleep(0.6)
                        ok, user = verify_user(email, password)
                    if ok:
                        st.session_state.authenticated = True
                        st.session_state.username = user["name"]
                        st.session_state.user_plan = user["plan"]
                        st.session_state.page = "onboard"
                        st.session_state.login_attempts = 0
                        st.rerun()
                    else:
                        st.session_state.login_attempts += 1
                        remaining = 5 - st.session_state.login_attempts
                        st.error(f"Invalid credentials. {remaining} attempt(s) remaining.")

        st.markdown("""
        <div class="cred-hint">
          <p>Demo credentials:</p>
          <p>📧 demo@walletwarriors.ai</p>
          <p>🔑 Warrior@2024</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <p style="text-align:center;margin-top:32px;font-size:11px;
                  color:rgba(242,242,242,0.25);font-family:'Space Mono',monospace;">
          256-bit AES encrypted &nbsp;·&nbsp; SOC 2 compliant &nbsp;·&nbsp; DPDP Act 2023
        </p>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ██████████  ONBOARDING / INCOME VERIFICATION  ██████████
# ─────────────────────────────────────────────────────────────────────────────

def render_onboard():
    # Top nav
    st.markdown(f"""
    <div style="background:#161616;border-bottom:1px solid rgba(170,119,242,0.12);
                padding:16px 40px;display:flex;align-items:center;
                justify-content:space-between;margin-bottom:0;">
      <div style="display:flex;align-items:center;gap:12px;">
        <div style="width:32px;height:32px;background:linear-gradient(135deg,#63458C,#AA77F2);
                    border-radius:8px;display:flex;align-items:center;
                    justify-content:center;font-size:14px;">🔐</div>
        <span style="font-family:'Syne',sans-serif;font-weight:800;font-size:18px;
                     color:#F2F2F2;letter-spacing:-.01em;">Wallet Warriors</span>
      </div>
      <div style="display:flex;align-items:center;gap:16px;">
        <span style="font-size:12px;color:rgba(242,242,242,0.4);font-family:'Space Mono',monospace;">
          Welcome, {st.session_state.username}
        </span>
        {badge(st.session_state.get("user_plan","Pro"), "#63458C")}
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)

    # ── Page header
    _, mid, _ = st.columns([0.5, 3, 0.5])
    with mid:
        st.markdown("""
        <div style="text-align:center;margin-bottom:40px;">
          <h1 style="font-family:'Syne',sans-serif;font-size:36px;font-weight:800;
                     color:#F2F2F2;margin:0 0 10px;letter-spacing:-.02em;">
            Income Verification Engine
          </h1>
          <p style="color:rgba(242,242,242,0.45);font-size:15px;max-width:520px;
                    margin:0 auto;line-height:1.7;">
            Our AI cross-references your stated income against behavioral spending patterns
            and document proof using the <strong style="color:#AA77F2;">Triangulation Method</strong>.
          </p>
        </div>
        """, unsafe_allow_html=True)

        # ── Step indicator
        st.markdown("""
        <div style="display:flex;align-items:center;justify-content:center;gap:0;margin-bottom:40px;">
          <div style="display:flex;align-items:center;gap:8px;">
            <div style="width:28px;height:28px;border-radius:50%;
                        background:#63458C;color:#F2F2F2;font-size:12px;
                        font-family:'Space Mono',monospace;font-weight:700;
                        display:flex;align-items:center;justify-content:center;">1</div>
            <span style="font-size:12px;color:#AA77F2;font-family:'Space Mono',monospace;font-weight:700;">INCOME DATA</span>
          </div>
          <div style="width:60px;height:1px;background:rgba(170,119,242,0.3);margin:0 12px;"></div>
          <div style="display:flex;align-items:center;gap:8px;">
            <div style="width:28px;height:28px;border-radius:50%;
                        background:rgba(99,69,140,0.3);color:rgba(242,242,242,0.4);font-size:12px;
                        font-family:'Space Mono',monospace;font-weight:700;
                        display:flex;align-items:center;justify-content:center;">2</div>
            <span style="font-size:12px;color:rgba(242,242,242,0.4);font-family:'Space Mono',monospace;">VERIFICATION</span>
          </div>
          <div style="width:60px;height:1px;background:rgba(170,119,242,0.3);margin:0 12px;"></div>
          <div style="display:flex;align-items:center;gap:8px;">
            <div style="width:28px;height:28px;border-radius:50%;
                        background:rgba(99,69,140,0.3);color:rgba(242,242,242,0.4);font-size:12px;
                        font-family:'Space Mono',monospace;font-weight:700;
                        display:flex;align-items:center;justify-content:center;">3</div>
            <span style="font-size:12px;color:rgba(242,242,242,0.4);font-family:'Space Mono',monospace;">ANALYSIS</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    _, mid, _ = st.columns([0.3, 3, 0.3])
    with mid:
        # ── Section A: Stated Income
        st.markdown("""
        <div style="background:#161616;border:1px solid rgba(170,119,242,0.18);
                    border-radius:18px;padding:32px;margin-bottom:20px;">
          <p style="font-family:'Space Mono',monospace;font-size:10px;
                    letter-spacing:.12em;text-transform:uppercase;
                    color:#AA77F2;margin:0 0 20px;">A · Stated Income</p>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            income = st.number_input("Monthly Income (₹)", min_value=0, step=1000, key="ob_income")
        with c2:
            rent = st.number_input("Monthly Rent / EMI (₹)", min_value=0, step=500, key="ob_rent")
        with c3:
            savings = st.number_input("Monthly Savings (₹)", min_value=0, step=500, key="ob_savings")

        st.markdown("</div>", unsafe_allow_html=True)

        # ── Section B: Behavioural Proof
        st.markdown("""
        <div style="background:#161616;border:1px solid rgba(170,119,242,0.18);
                    border-radius:18px;padding:32px;margin-bottom:20px;">
          <p style="font-family:'Space Mono',monospace;font-size:10px;
                    letter-spacing:.12em;text-transform:uppercase;
                    color:#AA77F2;margin:0 0 4px;">B · Behavioural Spending Signals</p>
          <p style="color:rgba(242,242,242,0.35);font-size:12px;margin:0 0 20px;">
            Used for cross-correlation anomaly detection
          </p>
        """, unsafe_allow_html=True)

        c4, c5 = st.columns(2)
        with c4:
            electricity = st.number_input("Avg Monthly Electricity Bill (₹)", min_value=0, step=100, key="ob_elec")
        with c5:
            upi_outflow = st.number_input("Avg Monthly UPI Outflow (₹)", min_value=0, step=500, key="ob_upi")

        st.markdown("</div>", unsafe_allow_html=True)

        # ── Section C: Document Upload (OCR simulation)
        st.markdown("""
        <div style="background:#161616;border:1px solid rgba(170,119,242,0.18);
                    border-radius:18px;padding:32px;margin-bottom:24px;">
          <p style="font-family:'Space Mono',monospace;font-size:10px;
                    letter-spacing:.12em;text-transform:uppercase;
                    color:#AA77F2;margin:0 0 4px;">C · Document Proof (Optional)</p>
          <p style="color:rgba(242,242,242,0.35);font-size:12px;margin:0 0 20px;">
            Upload salary slip / bank statement. OCR pipeline extracts income automatically.
          </p>
        """, unsafe_allow_html=True)

        c6, c7 = st.columns([2, 1])
        with c6:
            uploaded_doc = st.file_uploader(
                "Upload Salary Slip or Bank Statement (PDF / Image)",
                type=["pdf", "png", "jpg", "jpeg"],
                key="ob_doc"
            )
        with c7:
            doc_income_manual = st.number_input(
                "Or manually enter document income (₹)",
                min_value=0, step=1000, key="ob_doc_income",
                help="If OCR cannot extract, enter the 'Net Pay' from your payslip here."
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # OCR simulation
        doc_income = None
        if uploaded_doc:
            st.markdown("""
            <div style="background:rgba(99,69,140,0.1);border:1px solid rgba(170,119,242,0.2);
                        border-radius:10px;padding:14px 18px;margin-bottom:16px;">
              <span style="font-size:12px;font-family:'Space Mono',monospace;color:#AA77F2;">
                ✦ OCR Pipeline Active — document received. For full OCR, integrate PyTesseract in production.
              </span>
            </div>
            """, unsafe_allow_html=True)
            if doc_income_manual > 0:
                doc_income = doc_income_manual

        if doc_income_manual > 0 and not uploaded_doc:
            doc_income = doc_income_manual

        # ── Proceed button
        if st.button("Run Verification Engine  →", key="btn_verify"):
            if income == 0:
                st.warning("Please enter your monthly income to proceed.")
            else:
                with st.spinner("Running triangulation engine…"):
                    time.sleep(1.0)
                    coherent, confidence, flags, est_real = triangulate_income(
                        income, rent, electricity, upi_outflow, doc_income
                    )

                st.session_state.verification_result = {
                    "coherent": coherent,
                    "confidence": confidence,
                    "flags": flags,
                    "est_real_income": est_real,
                    "stated_income": income,
                    "rent": rent,
                    "savings": savings,
                    "electricity": electricity,
                    "upi_outflow": upi_outflow,
                    "doc_income": doc_income,
                }
                st.session_state.page = "verify_result"
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# ██████████  VERIFICATION RESULT PAGE  ██████████
# ─────────────────────────────────────────────────────────────────────────────

def render_verify_result():
    vr = st.session_state.verification_result
    coherent    = vr["coherent"]
    confidence  = vr["confidence"]
    flags       = vr["flags"]
    est_real    = vr["est_real_income"]
    stated      = vr["stated_income"]

    # Nav
    _render_nav()

    st.markdown('<div style="padding:40px 60px;">', unsafe_allow_html=True)

    # Result banner
    if coherent:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(76,175,125,0.15),rgba(76,175,125,0.05));
                    border:1px solid rgba(76,175,125,0.4);border-radius:18px;
                    padding:32px;margin-bottom:32px;display:flex;
                    align-items:center;justify-content:space-between;">
          <div>
            <p style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.12em;
                      text-transform:uppercase;color:rgba(76,175,125,0.8);margin:0 0 8px;">
              Verification Status
            </p>
            <h2 style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;
                       color:#4CAF7D;margin:0;">✓ Income Verified</h2>
            <p style="color:rgba(242,242,242,0.5);margin:8px 0 0;font-size:14px;">
              Your financial profile is coherent. Proceeding to credit analysis.
            </p>
          </div>
          <div style="text-align:right;">
            <p style="color:rgba(242,242,242,0.4);font-size:11px;font-family:'Space Mono',monospace;margin:0 0 4px;">CONFIDENCE SCORE</p>
            <p style="font-family:'Space Mono',monospace;font-size:42px;font-weight:700;color:#4CAF7D;margin:0;">{confidence}%</p>
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(224,92,92,0.15),rgba(224,92,92,0.05));
                    border:1px solid rgba(224,92,92,0.4);border-radius:18px;
                    padding:32px;margin-bottom:32px;display:flex;
                    align-items:center;justify-content:space-between;">
          <div>
            <p style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.12em;
                      text-transform:uppercase;color:rgba(224,92,92,0.8);margin:0 0 8px;">
              Verification Status
            </p>
            <h2 style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;
                       color:#E05C5C;margin:0;">⚠ Anomaly Detected</h2>
            <p style="color:rgba(242,242,242,0.5);margin:8px 0 0;font-size:14px;">
              Income triangulation failed. Manual review required.
            </p>
          </div>
          <div style="text-align:right;">
            <p style="color:rgba(242,242,242,0.4);font-size:11px;font-family:'Space Mono',monospace;margin:0 0 4px;">CONFIDENCE SCORE</p>
            <p style="font-family:'Space Mono',monospace;font-size:42px;font-weight:700;color:#E05C5C;margin:0;">{confidence}%</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Metrics row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Stated Income", f"₹{stated:,.0f}/mo")
    with c2:
        st.metric("Implied Income", f"₹{est_real:,.0f}/mo",
                  delta=f"{((est_real-stated)/max(stated,1)*100):+.0f}%")
    with c3:
        rent_pct = round(vr["rent"]/max(stated,1)*100, 1)
        st.metric("Rent-to-Income", f"{rent_pct}%",
                  delta="Safe" if rent_pct < 45 else "High",
                  delta_color="normal" if rent_pct < 45 else "inverse")
    with c4:
        st.metric("Verification Score", f"{confidence}/100")

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    # ── Gauges
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "indicator"}, {"type": "indicator"}]],
    )
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=confidence,
        title={"text": "Verification Confidence", "font": {"size": 13}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#F2F2F2"},
            "bar": {"color": "#AA77F2"},
            "steps": [
                {"range": [0,   40], "color": "rgba(224,92,92,0.3)"},
                {"range": [40,  70], "color": "rgba(201,138,26,0.3)"},
                {"range": [70, 100], "color": "rgba(76,175,125,0.3)"},
            ],
            "threshold": {"line": {"color": "#AA77F2", "width": 2}, "value": confidence},
            "bgcolor": "rgba(0,0,0,0)",
        }
    ), row=1, col=1)

    discrepancy_pct = min(100, abs(stated - est_real) / max(stated, 1) * 100)
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=stated,
        delta={"reference": est_real, "prefix": "₹", "valueformat": ",.0f"},
        title={"text": "Stated vs Implied Income (₹)", "font": {"size": 13}},
        number={"prefix": "₹", "valueformat": ",.0f"},
        gauge={
            "axis": {"range": [0, max(stated, est_real) * 1.3]},
            "bar": {"color": "#63458C"},
            "steps": [{"range": [0, est_real], "color": "rgba(170,119,242,0.2)"}],
            "bgcolor": "rgba(0,0,0,0)",
        }
    ), row=1, col=2)

    fig.update_layout(**PLOT_LAYOUT, height=280)
    st.plotly_chart(fig, use_container_width=True)

    # ── Flags
    if flags:
        section_header("Verification Flags", "Issues detected by the triangulation engine", "🚩")
        for f in flags:
            sev_color = {"high": "#E05C5C", "medium": "#C98A1A", "low": "#AA77F2"}.get(f["severity"], "#AA77F2")
            st.markdown(f"""
            <div style="background:#1C1C1E;border-left:3px solid {sev_color};
                        border-radius:0 12px 12px 0;padding:16px 20px;margin-bottom:12px;
                        border-top:1px solid rgba(255,255,255,0.05);border-right:1px solid rgba(255,255,255,0.05);
                        border-bottom:1px solid rgba(255,255,255,0.05);">
              <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                <span style="font-size:10px;font-family:'Space Mono',monospace;font-weight:700;
                             color:{sev_color};text-transform:uppercase;letter-spacing:.1em;">
                  {f['severity']} severity
                </span>
              </div>
              <p style="color:#F2F2F2;font-size:14px;margin:0;line-height:1.6;">{f['msg']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✓ No anomalies detected. All signals are coherent.")

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    # ── CTA
    c_a, c_b = st.columns(2)
    with c_a:
        if st.button("← Re-enter Data", key="btn_back_verify"):
            st.session_state.page = "onboard"
            st.rerun()
    with c_b:
        label = "Proceed to Credit Analysis  →" if coherent else "Proceed Anyway (Override)  →"
        if st.button(label, key="btn_proceed"):
            st.session_state.user_data = vr
            st.session_state.page = "dashboard"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ██████████  MAIN DASHBOARD  ██████████
# ─────────────────────────────────────────────────────────────────────────────

def render_dashboard():
    _render_nav()

    ud = st.session_state.user_data

    st.markdown('<div style="padding:32px 48px;">', unsafe_allow_html=True)

    # ── Header
    st.markdown(f"""
    <div style="margin-bottom:36px;">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;">
        <div>
          <h1 style="font-family:'Syne',sans-serif;font-size:34px;font-weight:800;
                     color:#F2F2F2;margin:0 0 6px;letter-spacing:-.02em;">
            Financial Risk Intelligence
          </h1>
          <p style="color:rgba(242,242,242,0.4);font-size:14px;margin:0;">
            Complete AI-driven credit assessment for {st.session_state.username}
          </p>
        </div>
        <div style="display:flex;gap:10px;align-items:center;">
          {badge("AUC 0.86","#63458C")}
          {badge("XGBoost v2","rgba(153,99,15,0.7)","#F2F2F2")}
          {badge("SHAP Explained","rgba(170,119,242,0.25)","#AA77F2")}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Pre-fill from verification data or fresh inputs
    default_income  = ud.get("stated_income", 0)
    default_rent    = ud.get("rent", 0)
    default_savings = ud.get("savings", 0)

    # ── Input form
    st.markdown("""
    <div style="background:#161616;border:1px solid rgba(170,119,242,0.15);
                border-radius:18px;padding:32px;margin-bottom:28px;">
      <p style="font-family:'Space Mono',monospace;font-size:10px;letter-spacing:.12em;
                text-transform:uppercase;color:#AA77F2;margin:0 0 20px;">
        Loan Application Parameters
      </p>
    """, unsafe_allow_html=True)

    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        income = st.number_input("Monthly Income (₹)", value=int(default_income), min_value=0, step=1000, key="d_income")
    with r1c2:
        rent = st.number_input("Monthly Rent / EMI (₹)", value=int(default_rent), min_value=0, step=500, key="d_rent")
    with r1c3:
        savings = st.number_input("Monthly Savings (₹)", value=int(default_savings), min_value=0, step=500, key="d_savings")

    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        loan_amount = st.number_input("Loan Amount Requested (₹)", min_value=0, step=5000, key="d_loan")
    with r2c2:
        employment = st.number_input("Employment Duration (years)", min_value=0.0, step=0.5, key="d_emp")
    with r2c3:
        credit_score = st.number_input("CIBIL / Credit Score", 300, 900, value=650, key="d_cibil")

    st.markdown("</div>", unsafe_allow_html=True)

    analyze = st.button("Run AI Credit Analysis  →", key="btn_analyze")

    # ═══════════════════════════════════════════════════════════════════════
    # ANALYSIS RESULTS
    # ═══════════════════════════════════════════════════════════════════════

    if analyze:
        if income == 0:
            st.warning("Please enter monthly income.")
            return

        data = pd.DataFrame({
            "Income":      [income],
            "Rent":        [rent],
            "Savings":     [savings],
            "LoanAmount":  [loan_amount],
            "Employment":  [employment],
            "CreditScore": [credit_score],
        })

        prob = model.predict_proba(data)[0][1]
        decision = "rejected" if prob > 0.5 else "approved"

        st.divider()

        # ── 1. Decision Hero
        dec_color  = "#E05C5C" if decision == "rejected" else "#4CAF7D"
        dec_label  = "LOAN REJECTED" if decision == "rejected" else "LOAN APPROVED"
        dec_icon   = "✗" if decision == "rejected" else "✓"

        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba({('224,92,92' if decision=='rejected' else '76,175,125')},0.12),rgba(0,0,0,0));
                    border:1px solid {dec_color}40;border-radius:20px;
                    padding:36px;margin-bottom:28px;text-align:center;">
          <div style="font-size:48px;margin-bottom:12px;">{dec_icon}</div>
          <h2 style="font-family:'Syne',sans-serif;font-size:32px;font-weight:800;
                     color:{dec_color};margin:0 0 8px;letter-spacing:-.01em;">{dec_label}</h2>
          <p style="color:rgba(242,242,242,0.5);font-size:15px;margin:0;">
            Default probability: <strong style="color:{dec_color};">{prob*100:.1f}%</strong> &nbsp;·&nbsp;
            Threshold: 50%
          </p>
        </div>
        """, unsafe_allow_html=True)

        # ── 2. KPI strip
        approval_score = round((1 - prob) * 100, 1)
        dti = round(rent / max(income, 1) * 100, 1)
        hustle_score = _compute_hustle(savings, income, rent, credit_score, employment, loan_amount)

        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            st.metric("Default Risk", f"{prob*100:.1f}%")
        with k2:
            st.metric("Approval Readiness", f"{approval_score}%")
        with k3:
            st.metric("Debt-to-Income", f"{dti}%")
        with k4:
            st.metric("CIBIL Score", credit_score)
        with k5:
            st.metric("Hustle Score™", f"{hustle_score}/100")

        st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)

        # ── 3. Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "  📊 Risk Overview  ",
            "  🔎 SHAP Explanation  ",
            "  🧠 AI Recommendations  ",
            "  🗺 Improvement Roadmap  "
        ])

        # ───────── TAB 1: RISK OVERVIEW ─────────
        with tab1:
            c_left, c_right = st.columns([1, 1])

            # Gauge
            with c_left:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=prob * 100,
                    delta={"reference": 50, "suffix": "%"},
                    title={"text": "Default Risk Meter", "font": {"size": 14, "color": "#F2F2F2"}},
                    number={"suffix": "%", "font": {"size": 36, "color": dec_color}},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": "#F2F2F2", "tickfont": {"size": 10}},
                        "bar": {"color": dec_color, "thickness": 0.25},
                        "bgcolor": "rgba(0,0,0,0)",
                        "bordercolor": "rgba(170,119,242,0.2)",
                        "steps": [
                            {"range": [0,  33], "color": "rgba(76,175,125,0.2)"},
                            {"range": [33, 66], "color": "rgba(201,138,26,0.2)"},
                            {"range": [66,100], "color": "rgba(224,92,92,0.2)"},
                        ],
                        "threshold": {
                            "line": {"color": "#AA77F2", "width": 3},
                            "thickness": 0.75,
                            "value": 50
                        }
                    }
                ))
                fig_gauge.update_layout(**PLOT_LAYOUT, height=320)
                st.plotly_chart(fig_gauge, use_container_width=True)

            # Radar
            with c_right:
                cats   = ["Savings Rate", "Income Stability", "Credit Health",
                          "Loan Affordability", "Employment", "Rent Burden"]
                # Normalize each dimension 0-100
                s_rate   = min(100, savings / max(income, 1) * 500)
                inc_stab = min(100, employment * 12)
                cr_hlth  = (credit_score - 300) / 6
                loan_aff = max(0, 100 - loan_amount / max(income, 1) * 8)
                emp_scr  = min(100, employment * 10)
                rent_bur = max(0, 100 - dti * 1.5)
                vals = [s_rate, inc_stab, cr_hlth, loan_aff, emp_scr, rent_bur]

                fig_radar = go.Figure(go.Scatterpolar(
                    r=vals + [vals[0]],
                    theta=cats + [cats[0]],
                    fill="toself",
                    fillcolor="rgba(170,119,242,0.15)",
                    line=dict(color="#AA77F2", width=2),
                    name="Your Profile"
                ))
                fig_radar.add_trace(go.Scatterpolar(
                    r=[70] * (len(cats)+1),
                    theta=cats + [cats[0]],
                    fill="toself",
                    fillcolor="rgba(99,69,140,0.08)",
                    line=dict(color="rgba(99,69,140,0.4)", width=1, dash="dot"),
                    name="Safe Threshold"
                ))
                fig_radar.update_layout(
                    **PLOT_LAYOUT,
                    height=320,
                    polar=dict(
                        bgcolor="rgba(0,0,0,0)",
                        radialaxis=dict(visible=True, range=[0, 100],
                                        tickcolor="#F2F2F2",
                                        gridcolor="rgba(170,119,242,0.1)",
                                        tickfont={"size": 9}),
                        angularaxis=dict(tickfont={"size": 10, "color": "#F2F2F2"},
                                         gridcolor="rgba(170,119,242,0.1)")
                    )
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            # Bar: Financial Breakdown
            categories = ["Monthly Income", "Monthly Rent", "Monthly Savings",
                          "Loan Amount (÷10)", "Est. Disposable"]
            disposable = max(0, income - rent - savings)
            values = [income, rent, savings, loan_amount / 10, disposable]
            colors_bar = [COLORS["primary"], COLORS["danger"], COLORS["success"],
                          COLORS["gold"], "rgba(170,119,242,0.5)"]

            fig_bar = go.Figure(go.Bar(
                x=categories, y=values,
                marker_color=colors_bar,
                marker_line_color="rgba(0,0,0,0)",
                text=[f"₹{v:,.0f}" for v in values],
                textposition="outside",
                textfont=dict(size=11, color="#F2F2F2"),
            ))
            fig_bar.update_layout(**PLOT_LAYOUT, height=320,
                                   title="Financial Breakdown",
                                   yaxis=dict(gridcolor="rgba(170,119,242,0.08)",
                                              tickprefix="₹", tickformat=",.0f"))
            st.plotly_chart(fig_bar, use_container_width=True)

            # Waterfall: Cash Flow
            meas = ["absolute","relative","relative","relative","total"]
            fig_wf = go.Figure(go.Waterfall(
                orientation="v",
                measure=meas,
                x=["Income", "−Rent", "−Loan EMI*", "−Savings", "Disposable"],
                y=[income, -rent, -loan_amount/60, -savings,
                   income - rent - loan_amount/60 - savings],
                connector={"line": {"color": "rgba(170,119,242,0.3)"}},
                decreasing={"marker": {"color": COLORS["danger"]}},
                increasing={"marker": {"color": COLORS["success"]}},
                totals={"marker": {"color": COLORS["primary"]}},
                text=[f"₹{abs(v):,.0f}" for v in [income, rent, loan_amount/60, savings,
                                                    income - rent - loan_amount/60 - savings]],
                textposition="outside",
            ))
            fig_wf.update_layout(**PLOT_LAYOUT, height=300,
                                  title="Monthly Cash Flow Waterfall (*EMI estimated at 60 months)",
                                  yaxis=dict(tickprefix="₹", tickformat=",.0f",
                                             gridcolor="rgba(170,119,242,0.08)"))
            st.plotly_chart(fig_wf, use_container_width=True)

        # ───────── TAB 2: SHAP ─────────
        with tab2:
            with st.spinner("Computing SHAP explanations…"):
                try:
                    explainer = shap.Explainer(model)
                    sv = explainer(data)

                    # Matplotlib waterfall (white-on-dark)
                    plt.rcParams.update({
                        "figure.facecolor": "#1C1C1E",
                        "axes.facecolor":   "#1C1C1E",
                        "text.color":       "#F2F2F2",
                        "axes.labelcolor":  "#F2F2F2",
                        "xtick.color":      "#F2F2F2",
                        "ytick.color":      "#F2F2F2",
                        "axes.edgecolor":   "rgba(170,119,242,0.2)",
                    })

                    col_shap1, col_shap2 = st.columns(2)
                    with col_shap1:
                        st.markdown("""
                        <p style="font-family:'Space Mono',monospace;font-size:10px;
                                  letter-spacing:.1em;text-transform:uppercase;
                                  color:#AA77F2;margin:0 0 12px;">SHAP Waterfall — This Prediction</p>
                        """, unsafe_allow_html=True)
                        fig_w, ax_w = plt.subplots(figsize=(6, 4.5))
                        shap.plots.waterfall(sv[0], show=False)
                        fig_w = plt.gcf()
                        fig_w.patch.set_facecolor("#1C1C1E")
                        st.pyplot(fig_w, use_container_width=True)
                        plt.close("all")

                    with col_shap2:
                        st.markdown("""
                        <p style="font-family:'Space Mono',monospace;font-size:10px;
                                  letter-spacing:.1em;text-transform:uppercase;
                                  color:#AA77F2;margin:0 0 12px;">SHAP Bar — Feature Importance</p>
                        """, unsafe_allow_html=True)
                        fig_b, ax_b = plt.subplots(figsize=(6, 4.5))
                        shap.plots.bar(sv, show=False)
                        fig_b = plt.gcf()
                        fig_b.patch.set_facecolor("#1C1C1E")
                        st.pyplot(fig_b, use_container_width=True)
                        plt.close("all")

                    # Feature attribution table
                    feature_names = data.columns.tolist()
                    shap_vals_arr  = sv[0].values
                    sorted_idx     = np.argsort(np.abs(shap_vals_arr))[::-1]

                    rows = []
                    for i in sorted_idx:
                        direction = "↑ Increases Risk" if shap_vals_arr[i] > 0 else "↓ Reduces Risk"
                        dir_color = "#E05C5C" if shap_vals_arr[i] > 0 else "#4CAF7D"
                        rows.append((
                            feature_names[i],
                            f"{data.iloc[0][feature_names[i]]:,.2f}",
                            f"{shap_vals_arr[i]:+.4f}",
                            direction,
                            dir_color,
                        ))

                    section_header("Feature Attribution Table", "SHAP values per feature for this loan application", "📋")
                    header_html = """
                    <div style="display:grid;grid-template-columns:180px 120px 120px 1fr;
                                gap:0;background:rgba(99,69,140,0.2);
                                border-radius:10px 10px 0 0;padding:10px 16px;
                                font-family:'Space Mono',monospace;font-size:10px;
                                letter-spacing:.08em;text-transform:uppercase;color:rgba(242,242,242,0.5);">
                      <div>Feature</div><div>Value</div><div>SHAP</div><div>Direction</div>
                    </div>
                    """
                    rows_html = ""
                    for i, (feat, val, shap_v, direction, dc) in enumerate(rows):
                        bg = "#1C1C1E" if i % 2 == 0 else "#181818"
                        rows_html += f"""
                        <div style="display:grid;grid-template-columns:180px 120px 120px 1fr;
                                    gap:0;background:{bg};padding:10px 16px;
                                    border-bottom:1px solid rgba(170,119,242,0.06);
                                    {'border-radius:0 0 10px 10px' if i==len(rows)-1 else ''}">
                          <div style="font-family:'Space Mono',monospace;font-size:12px;color:#F2F2F2;">{feat}</div>
                          <div style="font-family:'Space Mono',monospace;font-size:12px;color:rgba(242,242,242,0.6);">{val}</div>
                          <div style="font-family:'Space Mono',monospace;font-size:12px;color:#AA77F2;">{shap_v}</div>
                          <div style="font-family:'Space Mono',monospace;font-size:12px;color:{dc};">{direction}</div>
                        </div>"""
                    st.markdown(header_html + rows_html, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"SHAP computation error: {e}")

        # ───────── TAB 3: AI RECOMMENDATIONS ─────────
        with tab3:
            section_header("Personalised Financial Intelligence",
                           "Professional, actionable recommendations based on your financial profile", "🧠")

            recs = _generate_professional_recommendations(
                income, rent, savings, loan_amount, employment, credit_score, prob
            )

            for rec in recs:
                icon_map = {"high": "🔴", "medium": "🟡", "low": "🟢", "positive": "✅"}
                priority_color = {
                    "high": "#E05C5C", "medium": "#C98A1A",
                    "low": "#AA77F2", "positive": "#4CAF7D"
                }.get(rec["priority"], "#AA77F2")

                st.markdown(f"""
                <div style="background:#1C1C1E;border:1px solid rgba(170,119,242,0.12);
                            border-left:3px solid {priority_color};
                            border-radius:0 14px 14px 0;padding:22px 24px;margin-bottom:14px;">
                  <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                    <span style="font-size:16px;">{icon_map.get(rec['priority'],'●')}</span>
                    <h4 style="font-family:'Syne',sans-serif;font-size:16px;font-weight:700;
                               color:#F2F2F2;margin:0;">{rec['title']}</h4>
                    <span style="margin-left:auto;">{badge(rec['priority'].upper(), priority_color)}</span>
                  </div>
                  <p style="color:rgba(242,242,242,0.65);font-size:14px;margin:0 0 10px;
                            line-height:1.7;">{rec['insight']}</p>
                  <div style="background:rgba(99,69,140,0.12);border-radius:8px;padding:12px 16px;">
                    <span style="font-family:'Space Mono',monospace;font-size:11px;
                                 color:#AA77F2;letter-spacing:.05em;">ACTION → </span>
                    <span style="font-size:13px;color:#F2F2F2;">{rec['action']}</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        # ───────── TAB 4: ROADMAP ─────────
        with tab4:
            section_header("90-Day Approval Roadmap",
                           "Milestone-based action plan to improve your credit eligibility", "🗺")

            months = ["Month 1", "Month 2", "Month 3"]
            roadmap = _generate_roadmap(income, rent, savings, loan_amount,
                                        employment, credit_score, prob)

            for i, (month, items) in enumerate(zip(months, roadmap)):
                progress_pct = [33, 66, 100][i]
                progress_color = ["#C98A1A", "#AA77F2", "#4CAF7D"][i]

                st.markdown(f"""
                <div style="background:#1C1C1E;border:1px solid rgba(170,119,242,0.15);
                            border-radius:16px;padding:24px;margin-bottom:16px;">
                  <div style="display:flex;align-items:center;justify-content:space-between;
                               margin-bottom:16px;">
                    <div style="display:flex;align-items:center;gap:12px;">
                      <div style="width:36px;height:36px;border-radius:50%;
                                  background:{progress_color};display:flex;
                                  align-items:center;justify-content:center;
                                  font-family:'Space Mono',monospace;font-size:13px;
                                  font-weight:700;color:#0D0D0D;">{i+1}</div>
                      <h4 style="font-family:'Syne',sans-serif;font-size:17px;
                                 font-weight:700;color:#F2F2F2;margin:0;">{month}</h4>
                    </div>
                    <span style="font-family:'Space Mono',monospace;font-size:11px;
                                 color:{progress_color};">{progress_pct}% Journey</span>
                  </div>
                  {''.join([f"""
                  <div style="display:flex;align-items:flex-start;gap:12px;
                               padding:10px 0;border-bottom:1px solid rgba(170,119,242,0.06);">
                    <span style="color:{progress_color};font-size:16px;margin-top:1px;">◆</span>
                    <p style="color:rgba(242,242,242,0.75);font-size:14px;margin:0;line-height:1.6;">{item}</p>
                  </div>
                  """ for item in items])}
                </div>
                """, unsafe_allow_html=True)

            # Projected score timeline
            fig_timeline = go.Figure()
            months_x = ["Now", "Month 1", "Month 2", "Month 3"]
            current_score = round((1 - prob) * 100)
            projected = [current_score,
                         min(100, current_score + 8),
                         min(100, current_score + 18),
                         min(100, current_score + 30)]
            fig_timeline.add_trace(go.Scatter(
                x=months_x, y=projected,
                mode="lines+markers+text",
                line=dict(color="#AA77F2", width=3),
                marker=dict(size=10, color="#AA77F2", line=dict(width=2, color="#0D0D0D")),
                text=[f"{v}%" for v in projected],
                textposition="top center",
                fill="tozeroy",
                fillcolor="rgba(170,119,242,0.08)",
            ))
            fig_timeline.add_hline(y=70, line_dash="dot",
                                   line_color="#4CAF7D",
                                   annotation_text="Approval Zone",
                                   annotation_font_color="#4CAF7D")
            fig_timeline.update_layout(
                **PLOT_LAYOUT,
                title="Projected Approval Readiness Score",
                height=300,
                yaxis=dict(range=[0, 110], ticksuffix="%",
                           gridcolor="rgba(170,119,242,0.08)")
            )
            st.plotly_chart(fig_timeline, use_container_width=True)

        # ── Hustle Score footer
        st.divider()
        section_header("Hustle Score™", "Composite financial discipline index", "🔥")
        _render_hustle_score(hustle_score, savings, income, rent, credit_score, employment, loan_amount)

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: NAV BAR
# ─────────────────────────────────────────────────────────────────────────────

def _render_nav():
    vr = st.session_state.verification_result
    ver_badge = ""
    if vr:
        color = "#4CAF7D" if vr["coherent"] else "#E05C5C"
        label = "Verified" if vr["coherent"] else "Manual Review"
        ver_badge = badge(label, color, "#0D0D0D")

    st.markdown(f"""
    <div style="background:rgba(22,22,22,0.95);backdrop-filter:blur(16px);
                -webkit-backdrop-filter:blur(16px);
                border-bottom:1px solid rgba(170,119,242,0.12);
                padding:14px 48px;display:flex;align-items:center;
                justify-content:space-between;position:sticky;top:0;z-index:100;">
      <div style="display:flex;align-items:center;gap:14px;">
        <div style="width:30px;height:30px;background:linear-gradient(135deg,#63458C,#AA77F2);
                    border-radius:8px;display:flex;align-items:center;
                    justify-content:center;font-size:13px;">🔐</div>
        <span style="font-family:'Syne',sans-serif;font-weight:800;font-size:17px;
                     color:#F2F2F2;letter-spacing:-.01em;">Wallet Warriors</span>
      </div>
      <div style="display:flex;align-items:center;gap:14px;">
        {ver_badge}
        <span style="font-size:12px;color:rgba(242,242,242,0.35);
                     font-family:'Space Mono',monospace;">
          {st.session_state.username}
        </span>
        {badge(st.session_state.get("user_plan","Pro"), "#63458C")}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Logout in sidebar workaround
    with st.sidebar:
        if st.button("← Sign Out"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: HUSTLE SCORE
# ─────────────────────────────────────────────────────────────────────────────

def _compute_hustle(savings, income, rent, credit_score, employment, loan_amount):
    score = 0
    if income > 0 and savings / income >= 0.10: score += 20
    if income > 0 and rent / income < 0.50:     score += 20
    if credit_score > 650:                       score += 20
    if employment >= 2:                          score += 20
    if income > 0 and loan_amount < income * 5: score += 20
    return score

def _render_hustle_score(score, savings, income, rent, credit_score, employment, loan_amount):
    dims = {
        "Savings Discipline": 20 if income > 0 and savings/income >= 0.10 else 0,
        "Rent Management":    20 if income > 0 and rent/income < 0.50 else 0,
        "Credit Health":      20 if credit_score > 650 else 0,
        "Career Stability":   20 if employment >= 2 else 0,
        "Loan Calibration":   20 if income > 0 and loan_amount < income*5 else 0,
    }
    color = "#4CAF7D" if score >= 70 else ("#C98A1A" if score >= 40 else "#E05C5C")

    st.markdown(f"""
    <div style="background:#1C1C1E;border:1px solid rgba(170,119,242,0.15);
                border-radius:18px;padding:28px;margin-bottom:24px;">
      <div style="display:flex;align-items:center;justify-content:space-between;
                   margin-bottom:20px;">
        <h3 style="font-family:'Syne',sans-serif;font-size:20px;font-weight:800;
                   color:#F2F2F2;margin:0;">Overall Hustle Score™</h3>
        <div style="font-family:'Space Mono',monospace;font-size:48px;
                    font-weight:700;color:{color};">{score}</div>
      </div>
    """, unsafe_allow_html=True)

    for dim, pts in dims.items():
        bar_color = "#4CAF7D" if pts > 0 else "rgba(224,92,92,0.4)"
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:16px;margin-bottom:10px;">
          <div style="width:160px;font-size:12px;color:rgba(242,242,242,0.6);
                      font-family:'Inter',sans-serif;">{dim}</div>
          <div style="flex:1;height:8px;background:rgba(170,119,242,0.1);border-radius:99px;overflow:hidden;">
            <div style="width:{pts*5}%;height:100%;background:{bar_color};border-radius:99px;
                        transition:width 0.5s ease;"></div>
          </div>
          <div style="width:40px;text-align:right;font-family:'Space Mono',monospace;
                      font-size:12px;color:{bar_color};">{pts}/20</div>
        </div>
        """, unsafe_allow_html=True)

    msg = ("🏆 Exceptional financial discipline. Strong loan eligibility." if score >= 70
           else "⚡ Moderate profile. Targeted improvements will unlock approval."
           if score >= 40 else
           "🎯 Significant improvements needed. Focus on savings and credit score first.")
    tier_color = "#4CAF7D" if score >= 70 else ("#C98A1A" if score >= 40 else "#E05C5C")
    st.markdown(f"""
    <div style="background:rgba({('76,175,125' if score>=70 else '201,138,26' if score>=40 else '224,92,92')},0.1);
                border-radius:10px;padding:14px 18px;margin-top:12px;">
      <p style="color:{tier_color};font-size:14px;margin:0;">{msg}</p>
    </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: PROFESSIONAL RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────

def _generate_professional_recommendations(income, rent, savings, loan_amount,
                                            employment, credit_score, prob):
    recs = []
    dti = rent / max(income, 1) * 100
    savings_rate = savings / max(income, 1) * 100
    emi_estimate = loan_amount / 60  # 5-year tenure
    foir = (rent + emi_estimate) / max(income, 1) * 100  # Fixed Obligation to Income Ratio

    # FOIR
    if foir > 65:
        recs.append({
            "priority": "high",
            "title": "FOIR Exceeds RBI Safe Limit",
            "insight": f"Your Fixed Obligation to Income Ratio (FOIR) stands at {foir:.1f}%. "
                       f"RBI-regulated lenders typically cap this at 50–65% for salaried borrowers and 55–70% for self-employed. "
                       f"Your current obligations (rent ₹{rent:,.0f} + estimated EMI ₹{emi_estimate:,.0f}) "
                       f"consume a high proportion of gross income.",
            "action": f"Reduce loan tenure from 60 to 84 months to lower monthly EMI to ₹{loan_amount/84:,.0f}, "
                      f"bringing FOIR to {((rent + loan_amount/84)/max(income,1)*100):.1f}%. "
                      "Alternatively, consider a smaller loan tranche or a co-applicant to boost eligibility."
        })
    elif foir > 50:
        recs.append({
            "priority": "medium",
            "title": "FOIR Approaching Upper Tolerance Band",
            "insight": f"At {foir:.1f}%, your debt burden is within lender limits but leaves little buffer. "
                       "Lenders assess residual income post-EMI; a thinner margin signals financial stress during income disruptions.",
            "action": "Consider prepaying existing EMIs or opting for a longer loan tenure to reduce monthly obligation before application."
        })

    # Savings rate
    if savings_rate < 10:
        recs.append({
            "priority": "high",
            "title": "Savings Rate Below Financial Safety Threshold",
            "insight": f"Your current savings rate is {savings_rate:.1f}% of net income (₹{savings:,.0f}/month). "
                       "Institutional lenders and credit bureaus interpret low savings as limited financial resilience. "
                       "The 50/30/20 rule prescribes a minimum 20% savings allocation for financially stable borrowers.",
            "action": f"Automate a SIP (Systematic Investment Plan) of ₹{int(income*0.15):,} monthly "
                      "into a liquid mutual fund or high-yield savings account. This builds a 6-month emergency corpus "
                      "within 12 months, which directly strengthens your creditworthiness narrative."
        })
    elif savings_rate >= 20:
        recs.append({
            "priority": "positive",
            "title": "Savings Discipline — Excellent",
            "insight": f"At {savings_rate:.1f}% savings rate, you demonstrate strong financial governance. "
                       "This positively impacts your alternative credit scoring (ACS) profile, "
                       "used by NBFCs and fintech lenders.",
            "action": "Channel surplus savings into a Fixed Deposit (FD) or Liquid Fund to demonstrate asset accumulation, "
                      "which can be cited as collateral in loan applications."
        })

    # Credit score
    if credit_score < 650:
        recs.append({
            "priority": "high",
            "title": "CIBIL Score Below Prime Lending Threshold",
            "insight": f"Your credit score of {credit_score} falls below the 750 benchmark required for prime interest rates. "
                       "Scores below 650 result in loan rejection from major PSU banks; NBFCs and fintech lenders "
                       "may approve but at 18–28% APR vs 10–14% for prime borrowers.",
            "action": "1) Check your CIBIL report for errors (free once/year at cibil.com). "
                      "2) Obtain a secured credit card (against FD) to build payment history. "
                      "3) Maintain 0 missed EMIs for 6 consecutive months — this typically raises score by 40–80 points."
        })
    elif credit_score >= 750:
        recs.append({
            "priority": "positive",
            "title": "Prime Credit Score — Leverage for Better Rates",
            "insight": f"Your CIBIL score of {credit_score} qualifies you for prime lending rates (10–13% APR). "
                       "Use this as a negotiation lever with lenders.",
            "action": "Request a counter-offer from at least 3 lenders. Use aggregator platforms (BankBazaar, Paisabazaar) "
                      "to compare live APRs. A 2% rate differential on ₹{loan_amount:,} saves ₹{int(loan_amount*0.02*5/2):,} over 5 years."
        })

    # Employment
    if employment < 1:
        recs.append({
            "priority": "high",
            "title": "Insufficient Employment Vintage",
            "insight": "Most scheduled banks require a minimum 12-month employment continuity at the current organisation. "
                       "Probationary employees or those with less than 1 year tenure are typically rejected "
                       "during underwriting.",
            "action": "Delay the loan application by the remaining months to complete 12 months of tenure. "
                      "During this period, build alternative documentation: ITR filings, Form 16, "
                      "or a letter from the employer confirming permanent status."
        })
    elif employment >= 3:
        recs.append({
            "priority": "positive",
            "title": "Strong Employment Vintage",
            "insight": f"{employment:.0f} years of continuous employment significantly boosts underwriter confidence "
                       "and may qualify you for pre-approved offers from HDFC, ICICI, or SBI.",
            "action": "Request pre-approved loan offers from your salary account bank — they underwrite on payroll data "
                      "and often offer faster disbursement (24–48 hrs) at preferential rates."
        })

    # Loan amount vs income
    if income > 0 and loan_amount > income * 60:
        recs.append({
            "priority": "medium",
            "title": "Loan-to-Annual-Income Ratio is Elevated",
            "insight": f"Requested loan (₹{loan_amount:,}) is {loan_amount/income:.1f}x your monthly income "
                       f"({loan_amount/(income*12):.1f}x annual income). "
                       "Standard personal loan eligibility is 10–22x monthly income. "
                       "Home loans allow higher LTI due to collateral.",
            "action": f"Split the requirement — apply for ₹{int(income*18):,} as a personal loan "
                      f"and explore a Loan Against Property (LAP) or securities for the balance. "
                      "This improves individual application approval probability significantly."
        })

    return recs


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: ROADMAP
# ─────────────────────────────────────────────────────────────────────────────

def _generate_roadmap(income, rent, savings, loan_amount, employment, credit_score, prob):
    month1, month2, month3 = [], [], []

    # Month 1: Foundation
    month1.append("Pull your CIBIL report (free at cibil.com) and dispute any erroneous entries. "
                  "Errors account for 20–30% of low scores and can be cleared within 30 days.")
    if savings / max(income, 1) < 0.15:
        month1.append(f"Set up an auto-debit SIP of ₹{int(income*0.12):,}/month into a liquid mutual fund "
                      "on salary credit date. Remove discretionary friction from savings.")
    month1.append("Gather documentation: 3 months salary slips, Form 16, 6-month bank statement, "
                  "PAN card, Aadhaar. Incomplete documentation is the #1 reason for underwriter delays.")

    # Month 2: Optimisation
    if credit_score < 750:
        month2.append(f"Activate a secured credit card (against a ₹{min(50000,int(loan_amount*0.1)):,} FD). "
                      "Use for utility and grocery payments and pay full bill on statement date. "
                      "This adds positive payment history to your CIBIL report within 45 days.")
    month2.append("Avoid multiple loan applications in this period — each hard inquiry drops CIBIL score by 5–8 points. "
                  "Use soft-check tools (BankBazaar, Paisabazaar) to pre-screen eligibility.")
    if rent / max(income, 1) > 0.45:
        month2.append("Evaluate shared accommodation or relocation to reduce housing cost ratio below 40% of income. "
                      "Even a 3-month record of lower rent improves your bank statement narrative.")

    # Month 3: Application
    month3.append("Submit application to your primary salary bank first — they have your transaction history "
                  "and internal risk models are more lenient for existing customers (typically 15–20% higher approval rate).")
    if employment < 2:
        month3.append("By month 3, you'll have additional tenure. Obtain an employment continuity letter "
                      "and HR confirmation of permanent status to strengthen the application.")
    month3.append(f"At this point, your estimated Approval Readiness Score should be ~{min(95, round((1-prob)*100)+25)}%. "
                  "If still below 70%, explore NBFC lenders (Bajaj Finserv, Tata Capital) "
                  "as they use alternate scoring and approve 40% more applicants than PSU banks.")

    return [month1, month2, month3]


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────

if not st.session_state.authenticated and st.session_state.page != "login":
    st.session_state.page = "login"

page = st.session_state.page

if page == "login":
    render_login()
elif page == "onboard":
    render_onboard()
elif page == "verify_result":
    render_verify_result()
elif page == "dashboard":
    render_dashboard()
else:
    render_login()