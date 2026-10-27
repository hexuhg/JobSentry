
import sqlite3

DATABASE = "jobsentry.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS company_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            review TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS community_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            company_name TEXT,
            job_url TEXT,
            reason TEXT NOT NULL,
            details TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    connection.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT,
            company_name TEXT,
            risk_score REAL NOT NULL,
            classification TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS saved_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            company_name TEXT,
            job_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_tables()
    print("JobSentry database tables are ready!")


