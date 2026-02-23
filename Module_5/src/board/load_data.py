"""
Database Loader Module
======================
Read cleaned JSON and safely load it into PostgreSQL using composed SQL.
"""

import json
import os

import psycopg
from psycopg import sql


def get_db_info():
    """Fetch database credentials from environment variables."""
    host = os.environ.get("DB_HOST", "localhost")
    dbname = os.environ.get("DB_NAME", "gradcafe_db")
    user = os.environ.get("DB_USER", "postgres")
    password = os.environ.get("DB_PASSWORD", "password")
    port = os.environ.get("DB_PORT", "5432")
    return f"host={host} dbname={dbname} user={user} password={password} port={port}"


def clean_val(value):
    """Normalize strings and convert empty strings to null-like values."""
    if value is None:
        return None
    if isinstance(value, str):
        clean_v = value.replace("\x00", "").strip()
        if clean_v == "":
            return None
        return clean_v
    return value


def get_val(entry, *keys):
    """Return the first present value among candidate keys in a row."""
    for key in keys:
        if key in entry:
            return entry.get(key)
    return None


def clean_date(value):
    """Validate date values and reject invalid Feb 29 leap-year rows."""
    if value is None:
        return None
    if not isinstance(value, str):
        return value

    val_str = value.strip()
    if val_str == "":
        return None

    parts = val_str.split()
    if len(parts) >= 3:
        day, mon, year = parts[0], parts[1], parts[2]
        if day == "29" and mon.lower().startswith("feb"):
            try:
                year_int = int(year)
                is_leap_year = (year_int % 4 == 0) and (
                    year_int % 100 != 0 or year_int % 400 == 0
                )
                if not is_leap_year:
                    return None
            except ValueError:
                return None
    return val_str


def load_data(filename="applicant_data.json", reset=False):
    """Open DB connection and load JSON records with parameterized SQL."""
    print(f"--- Loading data from {filename} ---")
    try:
        with psycopg.connect(get_db_info()) as conn:
            with conn.cursor() as cur:
                if reset:
                    drop_stmt = sql.SQL("DROP TABLE IF EXISTS {};").format(
                        sql.Identifier("applicants")
                    )
                    cur.execute(drop_stmt)

                create_stmt = sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS {} (
                        p_id SERIAL PRIMARY KEY, program TEXT, university TEXT, comments TEXT,
                        date_added DATE, url TEXT, status TEXT, term TEXT,
                        us_or_international TEXT, gpa FLOAT, gre FLOAT, gre_v FLOAT,
                        gre_aw FLOAT, degree TEXT, llm_generated_program TEXT,
                        llm_generated_university TEXT
                    );
                    """
                ).format(sql.Identifier("applicants"))
                cur.execute(create_stmt)

                try:
                    with open(filename, "r", encoding="utf-8") as file_handle:
                        data = json.load(file_handle)
                except FileNotFoundError:
                    print(f"Error: {filename} does not exist.")
                    return

                cols = [
                    "program",
                    "university",
                    "comments",
                    "date_added",
                    "url",
                    "status",
                    "term",
                    "us_or_international",
                    "gpa",
                    "gre",
                    "gre_v",
                    "gre_aw",
                    "degree",
                    "llm_generated_program",
                    "llm_generated_university",
                ]
                insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier("applicants"),
                    sql.SQL(", ").join(map(sql.Identifier, cols)),
                    sql.SQL(", ").join(sql.Placeholder() * len(cols)),
                )

                count = 0
                for entry in data:
                    cur.execute(
                        insert_query,
                        (
                            clean_val(get_val(entry, "program", "Program Name")),
                            clean_val(get_val(entry, "university", "University")),
                            clean_val(get_val(entry, "comments", "Comments")),
                            clean_date(
                                get_val(
                                    entry,
                                    "date_added",
                                    "Date of Information Added to Grad CafÃ©",
                                )
                            ),
                            clean_val(get_val(entry, "url", "URL link to applicant entry")),
                            clean_val(get_val(entry, "status", "Applicant Status")),
                            clean_val(
                                get_val(entry, "term", "Semester and Year of Program Start")
                            ),
                            clean_val(
                                get_val(
                                    entry,
                                    "us_or_international",
                                    "International / American Student",
                                )
                            ),
                            clean_val(get_val(entry, "gpa", "GPA")),
                            clean_val(get_val(entry, "gre", "GRE Score")),
                            clean_val(get_val(entry, "gre_v", "GRE V Score")),
                            clean_val(get_val(entry, "gre_aw", "GRE AW")),
                            clean_val(get_val(entry, "degree", "Masters or PhD")),
                            clean_val(entry.get("llm_generated_program")),
                            clean_val(entry.get("llm_generated_university")),
                        ),
                    )
                    count += 1
                print(f"Successfully inserted {count} rows.")

    except psycopg.Error as db_error:
        print(f"Database Error: {db_error}")
    except Exception as gen_error:  # pylint: disable=broad-except
        print(f"General Error: {gen_error}")


def main():
    """Execute loader directly."""
    load_data()


if __name__ == "__main__":
    main()
