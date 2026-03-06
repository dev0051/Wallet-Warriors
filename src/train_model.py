import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier
import joblib

# Generate synthetic dataset
np.random.seed(42)

n = 1000

data = pd.DataFrame({
    "Income": np.random.randint(15000,80000,n),
    "Rent": np.random.randint(5000,40000,n),
    "Savings": np.random.randint(0,20000,n),
    "LoanAmount": np.random.randint(10000,100000,n),
    "Employment": np.random.randint(0,10,n),
    "CreditScore": np.random.randint(500,800,n)
})

# Risk logic
data["Default"] = (
    (data["Rent"] > data["Income"]*0.7) |
    (data["Savings"] < 2000) |
    (data["CreditScore"] < 580)
).astype(int)

X = data.drop("Default",axis=1)
y = data["Default"]

# Split dataset
X_train,X_test,y_train,y_test = train_test_split(
    X,y,test_size=0.2,random_state=42
)

# Train model
model = XGBClassifier()

model.fit(X_train,y_train)

# Predict
y_pred = model.predict_proba(X_test)[:,1]

# AUC
auc = roc_auc_score(y_test,y_pred)

print("AUC:",auc)

# Save model
joblib.dump(model,"models/credit_model.pkl")