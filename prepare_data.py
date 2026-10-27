
import pandas as pd

# Load the original dataset
df = pd.read_csv("data/fake_job_postings.csv")

print("Original dataset shape:", df.shape)

# Keep the columns needed for our first ML model
text_columns = [
    "title",
    "company_profile",
    "description",
    "requirements"
]

# Fill missing text with empty strings
for column in text_columns:
    df[column] = df[column].fillna("").astype(str)

# Combine the text fields into one input
df["combined_text"] = (
    "Job Title: " + df["title"] + " " +
    "Company Profile: " + df["company_profile"] + " " +
    "Description: " + df["description"] + " " +
    "Requirements: " + df["requirements"]
)

# Keep only the model input and target label
clean_df = df[["combined_text", "fraudulent"]].copy()

# Remove rows without meaningful text
clean_df["combined_text"] = clean_df["combined_text"].str.strip()
clean_df = clean_df[clean_df["combined_text"].str.len() > 0]

# Check for missing values and duplicate records
print("\nMissing values:")
print(clean_df.isnull().sum())

print("\nDuplicate combined texts:", clean_df["combined_text"].duplicated().sum())

print("\nClass distribution:")
print(clean_df["fraudulent"].value_counts())

# Save the prepared dataset
clean_df.to_csv("data/prepared_job_postings.csv", index=False)

print("\nPrepared dataset shape:", clean_df.shape)
print("Saved to data/prepared_job_postings.csv")
