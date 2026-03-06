import streamlit as st
import pandas as pd
import joblib
import shap
import matplotlib.pyplot as plt

# =============================
# Load trained ML model
# =============================

model = joblib.load("models/credit_model.pkl")

st.set_page_config(page_title="Wallet Warriors", layout="wide")

st.title("💳 Wallet Warriors")
st.subheader("AI Wealth Coach for Hustlers")

st.markdown("""
Turning **Broke Hustlers into Bankable Heroes**

Instead of rejecting users blindly, Wallet Warriors explains **why** and shows **how to get approved next time.**
""")

st.divider()

# =============================
# User Inputs
# =============================

st.header("📊 Enter Your Financial Profile")

col1, col2 = st.columns(2)

with col1:
    income = st.number_input("Monthly Income (₹)", min_value=0)
    rent = st.number_input("Monthly Rent (₹)", min_value=0)
    savings = st.number_input("Monthly Savings (₹)", min_value=0)

with col2:
    loan_amount = st.number_input("Loan Amount Requested (₹)", min_value=0)
    employment = st.number_input("Employment Duration (years)", min_value=0)
    credit_score = st.number_input("Credit Score", min_value=300, max_value=900)

# =============================
# Analyze Button
# =============================

if st.button("Analyze Loan Risk"):

    data = pd.DataFrame({
        "Income":[income],
        "Rent":[rent],
        "Savings":[savings],
        "LoanAmount":[loan_amount],
        "Employment":[employment],
        "CreditScore":[credit_score]
    })

    prob = model.predict_proba(data)[0][1]

    st.divider()

    st.header("🤖 AI Loan Risk Analysis")

    st.metric("Default Probability", round(prob,2))

    if prob > 0.6:
        st.error("Loan Status: High Risk - Rejected")
    else:
        st.success("Loan Status: Approved")

    # =============================
    # Approval readiness
    # =============================

    approval_readiness = round((1 - prob) * 100)

    st.subheader("Approval Readiness")

    st.progress(int(approval_readiness / 100 * 100))

    st.write(f"Your approval readiness is **{approval_readiness}%**")

    if prob > 0.6:
        gap = round((prob - 0.6) * 100)
        st.warning(f"You are about **{gap}% away from approval.**")

    st.divider()

    # =============================
    # SHAP Explainability
    # =============================

    st.header("🔎 Why Did The Model Decide This? (SHAP)")

    explainer = shap.Explainer(model)
    shap_values = explainer(data)

    fig, ax = plt.subplots()
    shap.plots.bar(shap_values, show=False)

    st.pyplot(fig)

    st.divider()

    # =============================
    # Personalized Financial Analysis
    # =============================

    st.header("🧠 Personalized Financial Analysis")

    if rent > income * 0.7:

        ratio = round((rent / income) * 100)

        st.write(
            f"• Your rent is **₹{rent}**, which is **{ratio}% of your income (₹{income})**."
        )

        recommended = int(income * 0.5)

        st.write(
            f"  Ideally rent should be below **₹{recommended}** (50% of income)."
        )

        st.write(
            "  Reducing housing costs or increasing income would improve loan approval chances."
        )

    if savings < income * 0.1:

        target = int(income * 0.1)

        st.write(
            f"• Your savings are **₹{savings}**, which is lower than the recommended savings rate."
        )

        st.write(
            f"  Try saving at least **₹{target} per month (10% of income)**."
        )

    if loan_amount > income * 5:

        safe_range = int(income * 3)

        st.write(
            f"• The requested loan amount **₹{loan_amount}** is high relative to your income."
        )

        st.write(
            f"  A safer loan range would be around **₹{safe_range} – ₹{income*4}**."
        )

    if credit_score < 600:

        st.write(
            f"• Your credit score **({credit_score})** is below the safe lending threshold."
        )

        st.write(
            "  Consistent savings and responsible repayments will gradually improve your score."
        )

    if employment < 1:

        st.write(
            f"• Your employment duration is **{employment} years**, which suggests income instability."
        )

        st.write(
            "  Maintaining stable employment for at least **1–2 years** improves lender confidence."
        )

    st.divider()

    # =============================
    # Roadmap to Approval
    # =============================

    st.header("🗺 Roadmap to Approval")

    if prob > 0.6:

        st.warning("Improve these areas to unlock loan approval:")

        if rent > income * 0.6:
            st.write("• Reduce rent-to-income ratio below 60%")

        if savings < income * 0.1:
            st.write("• Save at least 10% of your income every month")

        if loan_amount > income * 5:
            st.write("• Apply for a smaller loan amount")

        if credit_score < 600:
            st.write("• Improve your credit score above 600")

        if employment < 1:
            st.write("• Maintain stable employment for at least 1 year")

    else:

        st.success("You are financially stable and likely to receive loan approval.")

    st.divider()

    # =============================
    # Hustle Score
    # =============================

    st.header("🔥 Hustle Score")

    score = 0

    if savings > income * 0.1:
        score += 20

    if rent < income * 0.5:
        score += 20

    if credit_score > 650:
        score += 20

    if employment > 2:
        score += 20

    if loan_amount < income * 5:
        score += 20

    hustle_score = score

    st.metric("Your Hustle Score", hustle_score)

    if hustle_score < 50:
        st.warning("Focus on improving savings discipline and reducing financial stress.")

    elif hustle_score < 70:
        st.info("You are improving. Small financial adjustments can unlock loans.")

    else:
        st.success("Strong financial behavior. You are loan ready.")