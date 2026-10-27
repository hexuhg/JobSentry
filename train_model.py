
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    average_precision_score
)

# 1. Load the prepared dataset
df = pd.read_csv("data/prepared_job_postings.csv")

print("Original rows:", len(df))

# 2. Check for identical text with conflicting labels
label_counts = df.groupby("combined_text")["fraudulent"].nunique()
conflicting_texts = label_counts[label_counts > 1].index

print("Texts with conflicting labels:", len(conflicting_texts))

# Exclude ambiguous text entries
df = df[~df["combined_text"].isin(conflicting_texts)].copy()

# Remove repeated text with the same label
df = df.drop_duplicates(subset=["combined_text"])

print("Rows after duplicate handling:", len(df))
print("\nClass distribution:")
print(df["fraudulent"].value_counts())

# 3. Separate input text (X) and target labels (y)
X = df["combined_text"]
y = df["fraudulent"]

# 4. Split into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining examples:", len(X_train))
print("Testing examples:", len(X_test))

# 5. Build the machine-learning pipeline
model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=50000,
            min_df=2
        )
    ),
    (
        "classifier",
        LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42
        )
    )
])

# 6. Train the model
print("\nTraining model...")
model.fit(X_train, y_train)

# 7. Predict on unseen test examples
y_pred = model.predict(X_test)
y_scores = model.predict_proba(X_test)[:, 1]

# 8. Evaluate model performance
print("\n--- CLASSIFICATION REPORT ---")
print(
    classification_report(
        y_test,
        y_pred,
        labels=[0, 1],
        target_names=["Legitimate-labelled", "Fraudulent-labelled"],
        zero_division=0
    )
)

print("--- CONFUSION MATRIX ---")
print("Rows = actual labels; columns = predicted labels")
print(confusion_matrix(y_test, y_pred, labels=[0, 1]))

print(
    "\nAverage precision (PR metric):",
    round(average_precision_score(y_test, y_scores), 4)
)

# 9. Save the complete pipeline
joblib.dump(model, "data/jobsentry_model.joblib")

print("\nModel saved to data/jobsentry_model.joblib")
print("Training and evaluation completed.")
