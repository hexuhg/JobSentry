# 🛡️ JobSentry – AI-Powered Job Fraud Detection System

**Spot Job Scams. Apply with Confidence.**

JobSentry is an AI-powered job fraud detection platform designed to help students and job seekers identify potentially fraudulent job postings. It uses Machine Learning and Natural Language Processing (NLP) techniques to analyze job descriptions and flag suspicious listings.

The platform also provides company insights, community reporting, company reviews, and a student dashboard to promote safer job searching.

---

## 🚀 Key Features

### 1. AI-Based Job Fraud Detection
- Uses **TF-IDF Vectorization** and **Logistic Regression**.
- Analyzes job titles, company profiles, descriptions, and requirements.
- Generates a fraud-class model score to indicate potential risk.
- Supports text-based job analysis and image-based text extraction using OCR.

### 2. Fraud Explanation and Company Verification
- Highlights potential warning signs in job postings.
- Provides company information through public data sources.
- Integrates with Wikidata to retrieve available company details, such as official website, headquarters, industry, and founding information.

### 3. Company Reviews and Ratings
- Allows users to submit company reviews and ratings.
- Displays approved community reviews.
- Includes moderation through the admin panel.

### 4. Community Reporting
- Enables students to report suspicious job postings.
- Allows administrators to review submitted reports.
- Maintains a separate history of reviewed reports.

### 5. Student Dashboard
- Displays total job analyses.
- Tracks potentially fraudulent postings.
- Shows saved jobs and analysis history.
- Visualizes fraud-risk distribution and analysis activity.

---

## 🧠 Machine Learning Model

JobSentry uses a Logistic Regression classifier trained on job posting data.

| Component | Description |
|---|---|
| Dataset | Employment Scam Aegean Dataset |
| Original Records | 17,880 |
| Processed Records | 15,975 |
| Feature Extraction | TF-IDF Vectorization |
| Classification Algorithm | Logistic Regression |
| Class Balancing | `class_weight='balanced'` |
| N-grams | Unigrams and Bigrams |

### Model Performance

The model was evaluated using a held-out test dataset.

| Metric | Result |
|---|---:|
| Accuracy | 97% |
| Fraud Precision | 0.67 |
| Fraud Recall | 0.86 |
| Fraud F1-Score | 0.75 |
| Average Precision | 0.8616 |

**Note:** These results are from the project's test split. The fraud-class model score is not a calibrated probability and should not be treated as proof that a job posting is fraudulent.

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| Machine Learning | Scikit-learn |
| NLP | TF-IDF |
| Classification | Logistic Regression |
| Database | SQLite |
| Authentication | Flask-Login |
| Image Text Extraction | Tesseract OCR, Pytesseract |
| Image Processing | Pillow |
| Data Source | Wikidata API |
| Data Visualization | Chart.js |
| Version Control | Git, GitHub |

---

## 📂 Project Structure

```text
JobSentry/
│
├── app.py
├── database.py
├── admin_config.py
│
├── data/
│   ├── fake_job_postings.csv
│   ├── prepared_job_postings.csv
│   └── jobsentry_model.joblib
│
├── templates/
│   ├── index.html
│   ├── reviews.html
│   ├── report.html
│   ├── dashboard.html
│   ├── admin.html
│   ├── admin_login.html
│   └── company_insights.html
│
├── static/
│   └── css/
│       └── style.css
│
├── inspect_data.py
├── prepare_data.py
├── train_model.py
├── test_model.py
│
├── make_admin_hash.py
├── .gitignore
└── README.md
```

---

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/hexuhg/JobSentry.git
cd JobSentry
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate the Virtual Environment

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use the environment's Python executable directly:

```powershell
.\.venv\Scripts\python.exe
```

### 4. Install Dependencies

```bash
pip install flask flask-login pandas scikit-learn joblib requests pytesseract Pillow
```

### 5. Configure Tesseract OCR

Install Tesseract OCR on your system.

For Windows, the default installation path used by this project is:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

If Tesseract is installed elsewhere, update its path in the application configuration.

### 6. Configure Admin Credentials

The admin configuration file is excluded from GitHub to protect sensitive information.

Create your local `admin_config.py` with:
- `SECRET_KEY`: a securely generated random secret.
- `ADMIN_PASSWORD_HASH`: a password hash generated using the project's password-hash helper.

Do not upload this file or your actual admin password to GitHub.

### 7. Run the Application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

---

## 🔮 Future Scope

- Improve fraud detection using additional machine learning models.
- Expand company verification using more public data sources.
- Introduce more advanced fraud explanation techniques.
- Enhance the platform's reporting and analytics capabilities.

---

## ⚠️ Disclaimer

JobSentry is an academic project developed for educational and research purposes. Its predictions are intended to assist users in identifying potentially suspicious job postings. The system cannot guarantee that a job posting is genuine or fraudulent. Users should independently verify job offers and companies before sharing personal information or making payments.

---

## 👨‍💻 Developer

**Akshay K.**

B.Tech – Computer Science and Engineering

Jawaharlal College of Engineering and Technology

**GitHub:** [hexuhg](https://github.com/hexuhg)

---

⭐ If you find this project interesting, consider giving the repository a star!
