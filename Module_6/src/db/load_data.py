import psycopg
from psycopg import sql
import os

def get_db_info():
    """
    Return a psycopg connection string.
    Priority: DATABASE_URL (Docker/compose) then DB_* vars (local).
    """
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return database_url

    host = os.environ.get("DB_HOST", "localhost")
    dbname = os.environ.get("DB_NAME", "gradcafe_db")
    user = os.environ.get("DB_USER", "postgres")
    password = os.environ.get("DB_PASSWORD", "password")
    port = os.environ.get("DB_PORT", "5432")
    return f"host={host} dbname={dbname} user={user} password={password} port={port}"

def ensure_tables(conn):
    with conn.cursor() as cur:
        # Main table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS applicants (
                p_id SERIAL PRIMARY KEY, program TEXT, university TEXT, comments TEXT,
                date_added DATE, url TEXT, status TEXT, term TEXT,
                us_or_international TEXT, gpa FLOAT, gre FLOAT, gre_v FLOAT,
                gre_aw FLOAT, degree TEXT, llm_generated_program TEXT,
                llm_generated_university TEXT,
                UNIQUE(university, program, date_added, comments) 
            );
        """)
        # Watermark table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ingestion_watermarks (
                source TEXT PRIMARY KEY,
                last_seen TEXT,
                updated_at TIMESTAMPTZ DEFAULT now()
            );
        """)
        # Analysis Cache table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analysis_cache (
                id SERIAL PRIMARY KEY, 
                data JSONB, 
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
    conn.commit()

def get_last_seen_date():
    try:
        with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT last_seen FROM ingestion_watermarks WHERE source = 'gradcafe'")
                res = cur.fetchone()
                return res[0] if res else None
    except Exception:
        return None

def update_watermark(conn, date_str):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO ingestion_watermarks (source, last_seen, updated_at)
            VALUES ('gradcafe', %s, NOW())
            ON CONFLICT (source) DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = NOW();
        """, (date_str,))

def load_from_list(conn, data_list):
    """Inserts a list of dicts into the DB using the existing schema logic."""
    if not data_list:
        return

    cols = [
        "program", "university", "comments", "date_added", "url", "status", "term",
        "us_or_international", "gpa", "gre", "gre_v", "gre_aw", "degree",
        "llm_generated_program", "llm_generated_university"
    ]
    
    # Simple On Conflict Do Nothing to ensure idempotence
    insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING").format(
        sql.Identifier("applicants"),
        sql.SQL(", ").join(map(sql.Identifier, cols)),
        sql.SQL(", ").join(sql.Placeholder() * len(cols)),
    )
    
    with conn.cursor() as cur:
        for entry in data_list:
            # reuse your existing clean_val / clean_date logic here
            # For brevity, assuming direct mapping or import helpers
            vals = (
                entry.get("Program Name"), entry.get("University"), entry.get("Comments"),
                entry.get("Date of Information Added to Grad CafÃ©"), # Check your key names
                entry.get("URL link to applicant entry"), entry.get("Applicant Status"),
                entry.get("Semester and Year of Program Start"), entry.get("International / American Student"),
                entry.get("GPA"), entry.get("GRE Score"), entry.get("GRE V Score"), entry.get("GRE AW"),
                entry.get("Masters or PhD"), entry.get("llm_generated_program"), entry.get("llm_generated_university")
            )
            cur.execute(insert_query, vals)
