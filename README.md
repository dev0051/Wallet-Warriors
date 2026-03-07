# ⚡ Wallet Warriors — AI Credit Intelligence Platform

> **Know your loan odds before you apply.**  
> AI-powered credit intelligence for smart borrowers — walk into any bank with complete visibility of your approval probability.

---

## Problem Statement

Over **190 million Indians** are classified as "thin-file" or "no-file" borrowers — they have never taken a formal loan, hold no credit card, and carry no CIBIL score. Traditional lenders reject these applicants outright, not because they are financially irresponsible, but because the system has no way to measure them.

Simultaneously, first-time borrowers **with** a CIBIL score face a different problem: they apply blind. They do not know their approval probability, which lenders to approach, what terms to expect, or what to fix before applying. The result is a cycle of hard enquiries, score drops, and uninformed rejections.

**The gap:** India's credit infrastructure is built for repeat borrowers. It penalises the first-timer, the gig worker, the student, and the freelancer — precisely the segment driving the next wave of economic growth.

**Wallet Warriors solves this** by acting as a personal AI underwriter — giving every applicant the same intelligence that a bank's credit team uses, before they ever walk through the door.

---

## What We Built

Wallet Warriors is a full-stack AI credit intelligence platform built on **Streamlit + Python + XGBoost + SHAP**. It takes a user's financial profile, runs it through a multi-layer analysis engine, and produces a complete credit intelligence report with an AI verdict, explainable scores, personalised recommendations, and a 90-day improvement roadmap.

---

## Core Features

### 🔬 Income Triangulation Engine
Our proprietary cross-verification system checks whether a user's stated income is consistent with their actual spending behaviour. It cross-references declared salary against electricity bills, UPI outflows, and document proof — the same methodology used by Tier-1 NBFC underwriters. Incoherence is flagged with a severity rating and a Confidence Index score.

### 🤖 XGBoost Credit Risk Model — AUC 0.86
A production-grade gradient-boosted decision tree model trained on 6 financial features: income, rent, savings, loan amount, employment tenure, and CIBIL score. The model outputs a default probability (0–100%) and a binary Approved / Rejected decision. SHAP (SHapley Additive exPlanations) values are computed for every prediction, giving the user a feature-level breakdown of exactly why the model reached its verdict.

### 🎯 Approval Readiness Score
A 6-pillar composite score (0–100) measuring where the applicant stands across: Income Stability, Debt Load (FOIR), Savings Rate, Credit Score, Employment Stability, and Income Verification. Each pillar is benchmarked against RBI Fair Lending guidelines.

### 💯 Hustle Score™
A 5-dimension financial discipline metric (0–100) that rewards consistent savings, manageable rent burden, good credit standing, stable employment, and proportionate loan requests. Designed to reward behaviour, not just history.

### 🕵️ Thin File — Behavioral Underwriting Engine
For users with no CIBIL score, the platform shifts to a Document Intelligence approach. Instead of searching for past loans, the AI reconstructs financial reliability by triangulating daily cash flows, bill payment history, skill signals (offer letters, certificates), and savings discipline. The engine produces a **CIBIL Proxy Score** (350–750 range) and a **Hustle Consistency Score** using the same XGBoost model — fed with behavioural signals instead of bureau data.

> *"We don't need a CIBIL score to see integrity. We use Document Intelligence to turn a Thin File user into a Transparent one."*

### 🔎 SHAP Explainability
Full SHAP waterfall charts, bar charts, and feature importance tables rendered for every analysis. The user sees not just a verdict, but a quantified explanation of every factor — turning a black-box model into a transparent one.

### 🧠 AI Recommendations Engine
A prioritised, personalised recommendation set (High / Medium / Low / Positive) generated from the user's exact profile. Each recommendation includes a **What** (the specific problem) and a **How** (the exact steps to fix it, including product names, timelines, and INR figures).

### 🗺️ 90-Day Improvement Roadmap
A three-month milestone plan generated from the user's profile weaknesses. Month 1 builds the foundation, Month 2 builds momentum, Month 3 prepares the user for application. Milestones are specific, actionable, and sequenced by impact.

### 🔮 What-If Simulator
An interactive scenario planning tool. Users adjust sliders for Additional Savings, Expense Reduction, CIBIL Boost, and Employment Months to see how their Approval Readiness score changes in real time — without re-running the full model.

### 📚 Hustle Academy
An in-app financial literacy sidebar with three educational modules: mastering the Debt-to-Income ratio, building UPI consistency signals, and the Credit Invisible → Bankable in 90 Days pathway.

### 💬 Jargon-Buster Tooltip System
10 financial terms (XGBoost, SHAP, FOIR, Debt-to-Income, Triangulation Method, Hustle Score, etc.) are surfaced as hover tooltips throughout the UI — making the platform accessible to first-time borrowers who have never encountered credit terminology.

### 📄 Regulatory-Compliant PDF Report
A downloadable, fully formatted credit intelligence report generated using ReportLab. The report is structured across two pages and complies with three regulatory frameworks:

- **RBI** — Cites RBI Credit Information Companies (Regulation) Act 2005, RBI Master Direction 2025, RBI Fair Lending Practices Circular RBI/2023-24/53, and NBFC Fair Practice Code. Includes RBI benchmarks for every Approval Readiness pillar.
- **SEBI** — Full disclosure statement per SEBI Investment Adviser Regulations 2013 and SEBI Research Analysts Regulations 2014.
- **DPDP Act 2023** — Formal Data Usage Consent Notice per Sections 6, 7, and 13: purpose of processing, legal basis, data retention policy, right to erasure, and grievance officer contact.

Every section of the report carries an explicit risk warning box clarifying the scope and limitations of the AI output.

---

## Technical Stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit (wide layout, custom CSS, JS injection) |
| ML Model | XGBoost Classifier (AUC 0.86, 6 features) |
| Explainability | SHAP (waterfall, bar, feature importance) |
| Visualisation | Plotly, Matplotlib |
| PDF Generation | ReportLab (A4, multi-section, regulatory-compliant) |
| Data Processing | Pandas, NumPy |
| Authentication | SHA-256 hashed passwords, session state management |
| Database | PostgreSQL (with in-memory fallback for demo) |
| Model Persistence | Joblib |

---

## Application Flow

```
Login  →  Income Verification (Onboarding)  →  Triangulation Result  →  Dashboard
                    ↓
           No CIBIL Score?  →  Thin File Behavioral Underwriting
```

**Dashboard tabs:**
1. Risk Overview — decision banner, key metrics, SHAP summary
2. Approval Readiness — 6-pillar radial chart and dimension table
3. SHAP Explainability — waterfall, bar chart, feature table
4. AI Recommendations — prioritised action items
5. 90-Day Roadmap — milestone plan
6. What-If Simulator — scenario planning sliders

---

## Demo Credentials

| User | Email | Password | Plan |
|---|---|---|---|
| Dev Kumar | `dev@walletwarriors.ai` | `Dev@2024` | Pro |
| Priya Sharma | `test@walletwarriors.ai` | `Test@1234` | Starter |

---

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/wallet-warriors.git
cd wallet-warriors

# Install dependencies
pip install streamlit pandas numpy xgboost shap matplotlib plotly \
            joblib reportlab psycopg2-binary scikit-learn

# Run the application
streamlit run wallet_warriors_final.py
```

Optional: place a trained model at `models/credit_model.pkl`. If not present, the app trains a synthetic model automatically on first launch.



## Regulatory Compliance

This project is designed as a **prototype and demonstration platform**. It is not a licensed Credit Information Company under the CIC(R) Act 2005, and its outputs do not constitute regulated financial advice. All regulatory citations in the PDF report reflect the framework that a production deployment of this system would operate under.

| Framework | Scope |
|---|---|
| RBI Credit Information Guidelines | Model output framing, FOIR benchmarks, income verification standards |
| SEBI Disclosure Standards | AI recommendation disclaimers, non-advice framing |
| DPDP Act 2023 | Consent notice, data purpose declaration, right to erasure, grievance redressal |

---

## The Vision

Credit access is not just a financial problem — it is a social one. A student who repays their electricity bill on time every month for two years is demonstrating the same reliability as someone with a credit card. A gig worker whose UPI inflows are consistent and whose rent-to-income ratio is healthy is a safer borrower than a salaried employee with four EMIs.

Wallet Warriors exists to make that argument — quantitatively, transparently, and in the language that lenders understand.

**Thin file does not mean high risk. It means the data hasn't been collected yet. We collect it.**

---

*Built with ⚡ for the next 190 million borrowers.*