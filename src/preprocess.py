import pandas as pd

def load_data():

    print("Loading dataset...")

    columns = [
        "Status","Duration","CreditHistory","Purpose","CreditAmount",
        "Savings","Employment","InstallmentRate","PersonalStatus",
        "OtherDebtors","ResidenceSince","Property","Age",
        "OtherInstallmentPlans","Housing","ExistingCredits",
        "Job","Dependents","Telephone","ForeignWorker","Risk"
    ]

    data = pd.read_csv("data/german_credit_data.csv")

    data.columns = columns

    # Convert target variable
    data["Risk"] = data["Risk"].map({1:0, 2:1})

    # Convert categorical columns to numbers
    categorical_cols = data.select_dtypes(include=["object"]).columns

    for col in categorical_cols:
        data[col] = data[col].astype("category").cat.codes

    X = data.drop("Risk", axis=1)
    y = data["Risk"]

    return X, y

