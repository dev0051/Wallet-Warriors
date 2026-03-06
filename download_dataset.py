import pandas as pd

url = "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data"

df = pd.read_csv(url, sep=" ", header=None)

df.to_csv("data/german_credit_data.csv", index=False)

print("Dataset downloaded and saved successfully!")


