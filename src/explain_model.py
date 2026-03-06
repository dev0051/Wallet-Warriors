import shap
import joblib

from preprocess import load_data

# Load trained model
model = joblib.load("models/credit_model.pkl")

# Load dataset
X, y = load_data()

# Create SHAP explainer
explainer = shap.TreeExplainer(model)

# Calculate SHAP values
shap_values = explainer.shap_values(X)

# Plot feature importance
shap.summary_plot(shap_values, X)