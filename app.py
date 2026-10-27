import requests
from urllib.parse import quote
from flask import flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from admin_config import ADMIN_PASSWORD_HASH, SECRET_KEY
from flask import Flask, render_template, request, redirect, url_for
import joblib
import pytesseract
import re
import sqlite3
from PIL import Image, ImageOps
from io import BytesIO

from database import create_tables, get_connection

app = Flask(__name__)

app.config["SECRET_KEY"] = SECRET_KEY

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "admin_login"
login_manager.login_message = "Please log in to access the admin area."

class AdminUser(UserMixin):
    id = "admin"


@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return AdminUser()
    return None

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

# Configure Tesseract OCR on Windows
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# Load the trained TF-IDF + Logistic Regression pipeline
model = joblib.load("data/jobsentry_model.joblib")

# Create database tables if they do not exist
create_tables()


# --------------------------------------------------
# FRAUD EXPLANATION
# --------------------------------------------------

def explain_warning_signs(text):
    warnings = []
    text_lower = text.lower()

    warning_rules = [
        {
            "name": "Upfront payment request",
            "patterns": [
                r"\bregistration fee\b",
                r"\bprocessing fee\b",
                r"\btraining fee\b",
                r"\bsecurity deposit\b",
                r"\bpay to get the job\b",
                r"\brefundable deposit\b",
            ],
            "severity": "high",
            "explanation": (
                "The posting may request money before employment. "
                "This deserves careful verification."
            ),
            "advice": (
                "Independently verify the employer and do not pay "
                "fees to obtain a job without confirming legitimacy."
            ),
        },
        {
            "name": "Unusually high earnings claims",
            "patterns": [
                r"\bguaranteed income\b",
                r"\bguaranteed earnings\b",
                r"\bget rich quick\b",
                r"\bno experience.{0,40}\bhigh salary\b",
            ],
            "severity": "medium",
            "explanation": (
                "The posting contains earnings claims that may "
                "deserve closer scrutiny."
            ),
            "advice": (
                "Compare the salary with similar roles and verify "
                "the compensation with the employer."
            ),
        },
        {
            "name": "Sensitive financial information",
            "patterns": [
                r"\b(?:send|provide|share|submit).{0,40}"
                r"\b(?:bank account|credit card|debit card)\b",
                r"\b(?:banking details|card details)\b",
            ],
            "severity": "high",
            "explanation": (
                "The text may request sensitive financial information. "
                "Such requests are risky before employer verification."
            ),
            "advice": (
                "Never share passwords, banking credentials, or "
                "card security codes with a recruiter."
            ),
        },
        {
            "name": "Pressure-based hiring claims",
            "patterns": [
                r"\bapply immediately\b",
                r"\blimited slots\b",
                r"\binstant hiring\b",
                r"\bno interview required\b",
                r"\bguaranteed job\b",
            ],
            "severity": "medium",
            "explanation": (
                "Urgency or unusually easy hiring claims can warrant "
                "closer inspection, although they do not prove fraud."
            ),
            "advice": (
                "Verify the role, recruiter, employer, and official "
                "application process."
            ),
        },
        {
            "name": "Messaging-platform-only contact",
            "patterns": [
                r"\bwhatsapp only\b",
                r"\bcontact (?:me|us) on whatsapp\b",
                r"\btelegram only\b",
                r"\binterview via telegram\b",
            ],
            "severity": "medium",
            "explanation": (
                "The posting directs applicants to messaging platforms, "
                "which can make recruiter verification more difficult."
            ),
            "advice": (
                "Confirm the recruiter through contact details "
                "obtained from the company's official website."
            ),
        },
    ]

    for rule in warning_rules:
        if any(
            re.search(pattern, text_lower)
            for pattern in rule["patterns"]
        ):
            warnings.append({
                "name": rule["name"],
                "severity": rule["severity"],
                "explanation": rule["explanation"],
                "advice": rule["advice"],
            })

    missing_details = []

    if not re.search(
        r"\b(company|inc\.?|llc|ltd\.?|limited|corp\.?)\b",
        text_lower,
    ):
        missing_details.append(
            "No clear company designation was detected by this "
            "basic text check."
        )

    if not re.search(
        r"\b(job title|position|role|responsibilities|duties)\b",
        text_lower,
    ):
        missing_details.append(
            "A clearly stated job title or role was not detected "
            "by this basic text check."
        )

    if not re.search(
        r"\b(requirements|qualifications|experience|skills)\b",
        text_lower,
    ):
        missing_details.append(
            "Explicit qualifications or experience requirements "
            "were not detected by this basic text check."
        )

    return warnings, missing_details


def get_safety_checks():
    return [
        "Find the company's official website independently.",
        "Check whether the vacancy appears on its official careers page.",
        "Verify recruiter contact details independently.",
        "Be cautious of upfront fees and requests for sensitive information.",
        "Review salary, responsibilities, and employment terms.",
    ]


# --------------------------------------------------
# SAVE ANALYSIS HISTORY
# --------------------------------------------------

def save_analysis(job_description, score, category):
    first_line = job_description.splitlines()[0][:150]

    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO analysis_history
            (job_title, company_name, risk_score, classification)
            VALUES (?, ?, ?, ?)
            """,
            (
                first_line,
                None,
                round(score * 100, 2),
                category,
            ),
        )
        connection.commit()
    finally:
        connection.close()


# --------------------------------------------------
# HOMEPAGE AND ML DETECTOR
# --------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    job_description = ""
    extracted_text = ""
    error = None

    if request.method == "POST":
        job_description = request.form.get(
            "job_description", ""
        ).strip()

        image_file = request.files.get("job_image")

        if image_file and image_file.filename:
            try:
                image_bytes = image_file.read()

                if not image_bytes:
                    raise ValueError("Empty image")

                image = Image.open(BytesIO(image_bytes))
                image = ImageOps.exif_transpose(image)
                image = image.convert("RGB")

                extracted_text = pytesseract.image_to_string(
                    image,
                    config="--psm 6",
                ).strip()

                if not extracted_text:
                    error = (
                        "No readable text was found. Try a clearer "
                        "image with larger text."
                    )
                else:
                    job_description = extracted_text

            except (ValueError, OSError):
                error = (
                    "Unable to read this image. Please upload a "
                    "valid image file."
                )
            except pytesseract.TesseractNotFoundError:
                error = (
                    "Tesseract OCR was not found. Check its "
                    "installation path in app.py."
                )

        if not error and job_description:
            try:
                prediction = int(
                    model.predict([job_description])[0]
                )
                score = float(
                    model.predict_proba([job_description])[0][1]
                )

                if prediction == 1:
                    category = "Potentially fraudulent"
                    title = "Warning signs detected"
                    message = (
                        "The model identified patterns associated "
                        "with fraudulent-labelled job postings."
                    )
                else:
                    category = "Lower model-indicated risk"
                    title = "Fewer fraud patterns detected"
                    message = (
                        "The model classified this posting as "
                        "legitimate. This does not guarantee safety."
                    )

                warnings, missing_details = explain_warning_signs(
                    job_description
                )

                result = {
                    "title": title,
                    "message": message,
                    "category": category,
                    "score": round(score * 100, 2),
                    "warnings": warnings,
                    "missing_details": missing_details,
                    "safety_checks": get_safety_checks(),
                }

                # Save only successful analyses
                save_analysis(job_description, score, category)

            except (sqlite3.Error, ValueError, OSError) as exc:
                app.logger.exception("Analysis or database error")
                error = (
                    "The analysis could not be saved. Check the "
                    "VS Code terminal for details."
                )

        elif not error:
            error = "Enter a job description or upload an image."

    return render_template(
        "index.html",
        result=result,
        job_description=job_description,
        extracted_text=extracted_text,
        error=error,
    )


# --------------------------------------------------
# COMPANY REVIEWS
# --------------------------------------------------


def get_wikidata_company_info(company_name):
    """Find public company facts in Wikidata."""

    if not company_name:
        return None

    search_url = "https://www.wikidata.org/w/api.php"

    headers = {
        "User-Agent": "JobSentry/1.0 (company research web application)"
    }

    try:
        search_response = requests.get(
            search_url,
            params={
                "action": "wbsearchentities",
                "search": company_name,
                "language": "en",
                "format": "json",
                "type": "item",
                "limit": 5,
            },
            headers=headers,
            timeout=8,
        )
        search_response.raise_for_status()
        results = search_response.json().get("search", [])

        # Only use an exact company-name match for this first version.
        match = next(
            (
                item for item in results
                if item.get("label", "").casefold() == company_name.casefold()
            ),
            None,
        )

        if not match:
            return None

        entity_id = match["id"]

        entity_response = requests.get(
            f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json",
            headers=headers,
            timeout=8,
        )
        entity_response.raise_for_status()

        entity = entity_response.json()["entities"][entity_id]
        claims = entity.get("claims", {})

        def get_claim_value(property_id):
            statements = claims.get(property_id, [])
            if not statements:
                return None

            value = (
                statements[0]
                .get("mainsnak", {})
                .get("datavalue", {})
                .get("value")
            )

            if isinstance(value, dict):
                return value.get("text") or value.get("id")

            return value

        website = get_claim_value("P856")
        founded = get_claim_value("P571")
        headquarters_id = get_claim_value("P159")
        industry_id = get_claim_value("P452")

        def get_entity_label(value):
            if not isinstance(value, str) or not value.startswith("Q"):
                return None

            try:
                response = requests.get(
                    f"https://www.wikidata.org/wiki/Special:EntityData/{value}.json",
                    headers=headers,
                    timeout=8,
                )
                response.raise_for_status()
                data = response.json()["entities"][value]
                return (
                    data.get("labels", {})
                    .get("en", {})
                    .get("value")
                )
            except (requests.RequestException, ValueError, KeyError):
                return None

        founded_text = None
        if isinstance(founded, dict):
            founded_text = founded.get("time", "").lstrip("+").split("T")[0]
            if founded_text.startswith("00-00-"):
                founded_text = founded_text[-4:]

        return {
            "name": match.get("label", company_name),
            "description": match.get("description"),
            "website": website,
            "founded": founded_text,
            "headquarters": get_entity_label(headquarters_id),
            "industry": get_entity_label(industry_id),
            "source_url": f"https://www.wikidata.org/wiki/{entity_id}",
        }

    except (requests.RequestException, ValueError, KeyError):
        # External data may be unavailable; the local review page should
        # still work normally.
        return None


@app.route("/company-insights", methods=["GET"])
def company_insights():
    company_name = request.args.get("company", "").strip()

    if len(company_name) > 120:
        company_name = company_name[:120]

    published_reviews = []
    average_rating = 0
    review_count = 0
    company_info = None

    if company_name:
        connection = get_connection()

        try:
            published_reviews = connection.execute(
                """
                SELECT company_name, rating, review, created_at
                FROM company_reviews
                WHERE status = 'approved'
                  AND LOWER(TRIM(company_name)) = LOWER(TRIM(?))
                ORDER BY created_at DESC
                """,
                (company_name,),
            ).fetchall()

            rating_summary = connection.execute(
                """
                SELECT AVG(rating) AS average_rating,
                       COUNT(*) AS review_count
                FROM company_reviews
                WHERE status = 'approved'
                  AND LOWER(TRIM(company_name)) = LOWER(TRIM(?))
                """,
                (company_name,),
            ).fetchone()

            average_rating = rating_summary["average_rating"] or 0
            review_count = rating_summary["review_count"] or 0

        finally:
            connection.close()

        # Retrieve public company information from Wikidata.
        company_info = get_wikidata_company_info(company_name)

    return render_template(
        "company_insights.html",
        company_name=company_name,
        reviews=published_reviews,
        average_rating=average_rating,
        review_count=review_count,
        company_info=company_info,
    )


@app.route("/reviews", methods=["GET", "POST"])
def reviews():
    message = None
    search_query = request.args.get("company", "").strip()

    if request.method == "POST":
        company_name = request.form.get(
            "company_name", ""
        ).strip()
        rating_value = request.form.get("rating", "").strip()
        review_text = request.form.get("review", "").strip()

        try:
            rating = int(rating_value)
        except ValueError:
            rating = 0

        if (
            not company_name
            or len(company_name) > 120
            or not 1 <= rating <= 5
            or not 10 <= len(review_text) <= 2000
        ):
            message = "Please check the company name, rating, and review."
        else:
            connection = get_connection()
            try:
                connection.execute(
                    """
                    INSERT INTO company_reviews
                    (company_name, rating, review, status)
                    VALUES (?, ?, ?, 'pending')
                    """,
                    (company_name, rating, review_text),
                )
                connection.commit()
            finally:
                connection.close()

            return redirect(url_for("reviews", submitted="1"))

    elif request.args.get("submitted") == "1":
        message = (
            "Your review was submitted successfully and is "
            "awaiting moderation."
        )

    connection = get_connection()
    try:
        if search_query:
            published_reviews = connection.execute(
                """
                SELECT company_name, rating, review, created_at
                FROM company_reviews
                WHERE status = 'approved'
                  AND company_name LIKE ?
                ORDER BY created_at DESC
                """,
                (f"%{search_query}%",),
            ).fetchall()
        else:
            published_reviews = connection.execute(
                """
                SELECT company_name, rating, review, created_at
                FROM company_reviews
                WHERE status = 'approved'
                ORDER BY created_at DESC
                """
            ).fetchall()
    finally:
        connection.close()

    return render_template(
        "reviews.html",
        reviews=published_reviews,
        message=message,
        search_query=search_query,
    )



# --------------------------------------------------
# COMMUNITY REPORTING
# --------------------------------------------------

@app.route("/report", methods=["GET", "POST"])
def report_job():
    message = None

    valid_reasons = {
        "Upfront payment request",
        "Suspicious salary claims",
        "Fake company or recruiter",
        "Personal or financial information",
        "Misleading job description",
        "Other concern",
    }

    if request.method == "POST":
        job_title = request.form.get("job_title", "").strip()
        company_name = request.form.get(
            "company_name", ""
        ).strip()
        job_url = request.form.get("job_url", "").strip()
        reason = request.form.get("reason", "").strip()
        details = request.form.get("details", "").strip()

        if (
            not job_title
            or len(job_title) > 150
            or len(company_name) > 120
            or len(job_url) > 1000
            or len(details) < 10
            or len(details) > 2000
            or reason not in valid_reasons
        ):
            message = "Please check all required fields and try again."

        elif job_url and not job_url.startswith(
            ("https://", "http://")
        ):
            message = (
                "The job URL must begin with http:// or https://."
            )

        else:
            connection = get_connection()
            try:
                connection.execute(
                    """
                    INSERT INTO community_reports
                    (job_title, company_name, job_url, reason, details, status)
                    VALUES (?, ?, ?, ?, ?, 'pending')
                    """,
                    (
                        job_title,
                        company_name or None,
                        job_url or None,
                        reason,
                        details,
                    ),
                )
                connection.commit()
            finally:
                connection.close()

            return redirect(
                url_for("report_job", submitted="1")
            )

    elif request.args.get("submitted") == "1":
        message = (
            "Your report was submitted successfully and is "
            "awaiting review. A report is not proof of fraud."
        )

    return render_template(
        "report.html",
        message=message,
    )

@app.route("/dashboard")
def dashboard():
    connection = get_connection()

    try:
        history = connection.execute(
            """
            SELECT job_title, risk_score, classification, created_at
            FROM analysis_history
            ORDER BY created_at DESC
            LIMIT 20
            """
        ).fetchall()

        total_analyses = connection.execute(
            "SELECT COUNT(*) FROM analysis_history"
        ).fetchone()[0]

        flagged_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM analysis_history
            WHERE classification = 'Potentially fraudulent'
            """
        ).fetchone()[0]

        saved_jobs = connection.execute(
            """
            SELECT job_title, company_name, job_description, created_at
            FROM saved_jobs
            ORDER BY created_at DESC
            """
        ).fetchall()

        report_count = connection.execute(
            "SELECT COUNT(*) FROM community_reports"
        ).fetchone()[0]

        pending_reports = connection.execute(
            """
            SELECT COUNT(*)
            FROM community_reports
            WHERE status = 'pending'
            """
        ).fetchone()[0]
        
        # Risk distribution
        risk_rows = connection.execute(
            """
            SELECT classification, COUNT(*) AS total
            FROM analysis_history
            GROUP BY classification
            """
        ).fetchall()

        risk_labels = [row["classification"] for row in risk_rows]
        risk_values = [row["total"] for row in risk_rows]

        # Analysis activity over the last 7 days
        activity_rows = connection.execute(
            """
            SELECT DATE(created_at) AS analysis_date, COUNT(*) AS total
            FROM analysis_history
            WHERE DATE(created_at) >= DATE('now', '-6 days')
            GROUP BY DATE(created_at)
            ORDER BY analysis_date
            """
        ).fetchall()

        activity_labels = [
            row["analysis_date"] for row in activity_rows
        ]
        activity_values = [
            row["total"] for row in activity_rows
        ]


    finally:
        connection.close()

    return render_template(
        "dashboard.html",
        history=history,
        total_analyses=total_analyses,
        flagged_count=flagged_count,
        saved_jobs=saved_jobs,
        report_count=report_count,
        pending_reports=pending_reports,
        risk_labels=risk_labels,
        risk_values=risk_values,
        activity_labels=activity_labels,
        activity_values=activity_values,
    )



# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

@app.route("/save-job", methods=["POST"])
def save_job():
    job_title = request.form.get("job_title", "").strip()
    company_name = request.form.get("company_name", "").strip()
    job_description = request.form.get(
        "job_description", ""
    ).strip()

    if (
        not job_title
        or not job_description
        or len(job_title) > 150
        or len(company_name) > 120
    ):
        return redirect(url_for("dashboard"))

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO saved_jobs
            (job_title, company_name, job_description)
            VALUES (?, ?, ?)
            """,
            (
                job_title,
                company_name or None,
                job_description,
            ),
        )
        connection.commit()
    finally:
        connection.close()

    return redirect(url_for("dashboard"))


# --------------------------------------------------
# ADMIN MODERATION
# Local prototype only: authentication must be added
# before deployment.
# --------------------------------------------------

@app.route("/admin")
@login_required

def admin():
    connection = get_connection()

    try:
        pending_reviews = connection.execute(
            """
            SELECT id, company_name, rating, review, created_at
            FROM company_reviews
            WHERE status = 'pending'
            ORDER BY created_at DESC
            """
        ).fetchall()

        pending_reports = connection.execute(
            """
            SELECT id, job_title, company_name, job_url,
                   reason, details, created_at
            FROM community_reports
            WHERE status = 'pending'
            ORDER BY created_at DESC
            """
        ).fetchall()

        reviewed_reports = connection.execute(
            """
            SELECT id, job_title, company_name, job_url,
                   reason, details, created_at
            FROM community_reports
            WHERE status = 'reviewed'
            ORDER BY created_at DESC
            """
        ).fetchall()

    finally:
        connection.close()

    return render_template(
        "admin.html",
        reviews=pending_reviews,
        reports=pending_reports,
        reviewed_reports=reviewed_reports,
        message=request.args.get("message"),
    )



@app.route("/admin/review/<int:review_id>", methods=["POST"])
@login_required
def moderate_review(review_id):
    action = request.form.get("action", "")

    if action not in {"approved", "rejected"}:
        return redirect(
            url_for("admin", message="Invalid moderation action.")
        )

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE company_reviews
            SET status = ?
            WHERE id = ? AND status = 'pending'
            """,
            (action, review_id),
        )
        connection.commit()
        updated = cursor.rowcount
    finally:
        connection.close()

    message = (
        "Review moderation completed."
        if updated
        else "Review not found or already moderated."
    )

    return redirect(url_for("admin", message=message))


@app.route("/admin/report/<int:report_id>", methods=["POST"])
@login_required
def moderate_report(report_id):
    action = request.form.get("action", "")

    if action != "reviewed":
        return redirect(
            url_for("admin", message="Invalid report action.")
        )

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE community_reports
            SET status = 'reviewed'
            WHERE id = ? AND status = 'pending'
            """,
            (report_id,),
        )
        connection.commit()
        updated = cursor.rowcount
    finally:
        connection.close()

    message = (
        "Report marked as reviewed."
        if updated
        else "Report not found or already reviewed."
    )

    return redirect(url_for("admin", message=message))



@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for("admin"))

    if request.method == "POST":
        password = request.form.get("password", "")

        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            login_user(AdminUser())
            return redirect(url_for("admin"))

        flash("Invalid admin password. Please try again.", "error")

    return render_template("admin_login.html")


@app.route("/admin/logout", methods=["POST"])
@login_required
def admin_logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("admin_login"))

if __name__ == "__main__":
    app.run(debug=True)
