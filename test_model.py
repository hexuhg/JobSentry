
import joblib

# Load the trained model
model = joblib.load("data/jobsentry_model.joblib")

# Example job posting for testing
job_text = """
Job Title: Remote Data Entry Assistant

Earn 60000 per month by working only two hours daily.
No experience required. Guaranteed selection.
Pay a refundable registration fee before joining.
Send your bank details to complete registration.
"""

# Predict the label
prediction = model.predict([job_text])[0]

# Get the model's score for the fraudulent class
fraud_score = model.predict_proba([job_text])[0][1]

print("Prediction:", prediction)
print("Fraud-class model score:", round(fraud_score * 100, 2), "%")

if prediction == 1:
    print("Result: Potentially fraudulent")
else:
    print("Result: Classified as legitimate by the model")

print("\nNote: This is an experimental model prediction, not proof of fraud.")
