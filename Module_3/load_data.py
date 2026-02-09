import psycopg
import json

# Update your password here
DB_INFO = "host=localhost dbname=gradcafe_db user=postgres password=password port=5432"

def clean_val(value):
    if value is None:
        return None
    if isinstance(value, str):
        # Postgres rejects NUL bytes in text fields
        clean_v = value.replace("\x00", "").strip()
        if clean_v == "":
            return None
        return clean_v
    return value

def get_val(entry, *keys):
    for k in keys:
        if k in entry:
            return entry.get(k)
    return None

def clean_date(value):
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    s = value.strip()
    if s == "":
        return None
    parts = s.split()
    if len(parts) >= 3:
        day = parts[0]
        mon = parts[1]
        year = parts[2]
        if day == "29" and mon.lower().startswith("feb"):
            try:
                y = int(year)
                is_leap = (y % 4 == 0) and (y % 100 != 0 or y % 400 == 0)
                if not is_leap:
                    return None
            except ValueError:
                return None
    return s

# Accept filename as an argument so app.py can pass it in
def load_data(filename="applicant_data.json"):
    print(f"--- Loading data from {filename} ---")
    try:
        with psycopg.connect(DB_INFO) as conn:
            with conn.cursor() as cur:
                
                # 1. Reset Table
                cur.execute("DROP TABLE IF EXISTS applicants;")
                cur.execute("""
                CREATE TABLE applicants (
                    p_id SERIAL PRIMARY KEY,
                    program TEXT,
                    university TEXT,
                    comments TEXT,
                    date_added DATE,
                    url TEXT,
                    status TEXT,
                    term TEXT,
                    us_or_international TEXT,
                    gpa FLOAT,
                    gre FLOAT,
                    gre_v FLOAT,
                    gre_aw FLOAT,
                    degree TEXT,
                    llm_generated_program TEXT,
                    llm_generated_university TEXT
                );
                """)
                print("Table 'applicants' created.")

                # 2. Read JSON (Using try/except instead of os.path.exists)
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except FileNotFoundError:
                    print(f"Error: {filename} does not exist.")
                    return
                    
                # 3. Insert Data
                insert_query = """
                INSERT INTO applicants (
                    program, university, comments, date_added, url, status, term, 
                    us_or_international, gpa, gre, gre_v, gre_aw, 
                    degree, llm_generated_program, llm_generated_university
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                count = 0
                for entry in data:
                    cur.execute(insert_query, (
                        clean_val(get_val(entry, 'program', 'Program Name')),
                        clean_val(get_val(entry, 'university', 'University')),
                        clean_val(get_val(entry, 'comments', 'Comments')),
                        clean_date(get_val(
                            entry,
                            'date_added',
                            'Date of Information Added to Grad Café',
                            'Date of Information Added to Grad CafÃ©'
                        )),
                        clean_val(get_val(entry, 'url', 'URL link to applicant entry')),
                        clean_val(get_val(entry, 'status', 'Applicant Status')),
                        clean_val(get_val(entry, 'term', 'Semester and Year of Program Start')),
                        clean_val(get_val(entry, 'us_or_international', 'International / American Student')),
                        clean_val(get_val(entry, 'gpa', 'GPA')),
                        clean_val(get_val(entry, 'gre', 'GRE Score')),
                        clean_val(get_val(entry, 'gre_v', 'GRE V Score')),
                        clean_val(get_val(entry, 'gre_aw', 'GRE AW')),
                        clean_val(get_val(entry, 'degree', 'Masters or PhD')),
                        # Use .get() to avoid errors if these keys don't exist yet
                        clean_val(entry.get('llm_generated_program')),
                        clean_val(entry.get('llm_generated_university'))
                    ))
                    count += 1
                
                print(f"Successfully inserted {count} rows.")

    except psycopg.Error as e:
        print(f"Database Error: {e}")
    except Exception as e:
        print(f"General Error: {e}")

if __name__ == "__main__":
    load_data()
