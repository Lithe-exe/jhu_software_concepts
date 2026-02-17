"""
Database Loader Module
======================
"""
import psycopg
import json

DB_INFO = "host=localhost dbname=gradcafe_db user=postgres password=password port=5432"

def clean_val(value):
    if value is None: return None
    if isinstance(value, str):
        clean_v = value.replace("\x00", "").strip()
        if clean_v == "": return None
        return clean_v
    return value

def get_val(entry, *keys):
    for k in keys:
        if k in entry: return entry.get(k)
    return None

def clean_date(value):
    if value is None: return None
    if not isinstance(value, str): return value
    s = value.strip()
    if s == "": return None
    parts = s.split()
    if len(parts) >= 3:
        day, mon, year = parts[0], parts[1], parts[2]
        if day == "29" and mon.lower().startswith("feb"):
            try:
                y = int(year)
                # Leap year logic
                if not ((y % 4 == 0) and (y % 100 != 0 or y % 400 == 0)):
                    return None
            except ValueError:
                return None
    return s

def load_data(filename="applicant_data.json", reset=False):
    print(f"--- Loading data from {filename} ---")
    try:
        with psycopg.connect(DB_INFO) as conn:
            with conn.cursor() as cur:
                if reset:
                    cur.execute("DROP TABLE IF EXISTS applicants;")
                cur.execute("""CREATE TABLE IF NOT EXISTS applicants (
                    p_id SERIAL PRIMARY KEY, program TEXT, university TEXT, comments TEXT, date_added DATE,
                    url TEXT, status TEXT, term TEXT, us_or_international TEXT, gpa FLOAT,
                    gre FLOAT, gre_v FLOAT, gre_aw FLOAT, degree TEXT,
                    llm_generated_program TEXT, llm_generated_university TEXT
                );""")
                
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except FileNotFoundError:
                    print(f"Error: {filename} does not exist.")
                    return

                insert_query = """INSERT INTO applicants (
                    program, university, comments, date_added, url, status, term, 
                    us_or_international, gpa, gre, gre_v, gre_aw, 
                    degree, llm_generated_program, llm_generated_university
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

                count = 0
                for entry in data:
                    cur.execute(insert_query, (
                        clean_val(get_val(entry, 'program', 'Program Name')),
                        clean_val(get_val(entry, 'university', 'University')),
                        clean_val(get_val(entry, 'comments', 'Comments')),
                        clean_date(get_val(entry, 'date_added', 'Date of Information Added to Grad Café')),
                        clean_val(get_val(entry, 'url', 'URL link to applicant entry')),
                        clean_val(get_val(entry, 'status', 'Applicant Status')),
                        clean_val(get_val(entry, 'term', 'Semester and Year of Program Start')),
                        clean_val(get_val(entry, 'us_or_international', 'International / American Student')),
                        clean_val(get_val(entry, 'gpa', 'GPA')),
                        clean_val(get_val(entry, 'gre', 'GRE Score')),
                        clean_val(get_val(entry, 'gre_v', 'GRE V Score')),
                        clean_val(get_val(entry, 'gre_aw', 'GRE AW')),
                        clean_val(get_val(entry, 'degree', 'Masters or PhD')),
                        clean_val(entry.get('llm_generated_program')),
                        clean_val(entry.get('llm_generated_university'))
                    ))
                    count += 1
                print(f"Successfully inserted {count} rows.")

    except psycopg.Error as e: print(f"Database Error: {e}")
    except Exception as e: print(f"General Error: {e}")

def main():
    load_data()

if __name__ == "__main__":
    main()