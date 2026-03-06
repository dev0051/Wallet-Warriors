import joblib
from lime.lime_tabular import LimeTabularExplainer

from preprocess import load_data

model = joblib.load("models/credit_model.pkl")

X, y = load_data()

explainer = LimeTabularExplainer(
    X.values,
    feature_names=X.columns,
    class_names=["Safe","Default"],
    mode="classification"
)

exp = explainer.explain_instance(
    X.iloc[0].values,
    model.predict_proba
)

exp.show_in_notebook()