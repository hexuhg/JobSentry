
import pandas as pd

# Load the job postings dataset
file_path = "data/fake_job_postings.csv"
df = pd.read_csv(file_path)

# 1. Dataset size
print("\n--- DATASET SIZE ---")
print("Number of rows:", df.shape[0])
print("Number of columns:", df.shape[1])

# 2. Column names
print("\n--- COLUMN NAMES ---")
print(df.columns.tolist())

# 3. First five job postings
print("\n--- FIRST 5 JOB POSTINGS ---")
print(df.head())

# 4. Missing values
print("\n--- MISSING VALUES ---")
print(df.isnull().sum().sort_values(ascending=False))

# 5. Fraudulent vs legitimate postings
print("\n--- FRAUD LABEL COUNTS ---")
print(df["fraudulent"].value_counts())

print("\n--- FRAUD LABEL PERCENTAGES ---")
print(df["fraudulent"].value_counts(normalize=True).mul(100).round(2))

print("\nDataset inspection completed.")
