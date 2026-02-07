import psycopg
import json

# Database Connection Info
DB_INFO = "host=localhost dbname=gradcafe_db user=postgres password=your_password port=5432"

def clean_val(value):
    """
    Helper to convert empty strings or None in JSON to SQL NULL.
    """
    if value is None:
        return None
    if isinstance(value, str):
        clean_v = value.strip()
        if clean_v == "":
            return None
        return clean_v
    return value

def load_data():
    try:
        # Connecting using psycopg3
        with psycopg.connect(DB_INFO) as conn:
            
            # Open a cursor to perform database operations
            with conn.cursor() as cur:
                
                # Creates Table (Drop if exists to start fresh)
                create_table_query = """
                DROP TABLE IF EXISTS applicants;
                CREATE TABLE applicants (
                    p_id SERIAL PRIMARY KEY,
                    program TEXT,
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
                """
                cur.execute(create_table_query)
                print("Table 'applicants' created.")

                # 2. Load Data from JSON
                filename = 'llm_extend_applicant_data.json'
                
                insert_query = """
                INSERT INTO applicants (
                    program, comments, date_added, url, status, term, 
                    us_or_international, gpa, gre, gre_v, gre_aw, 
                    degree, llm_generated_program, llm_generated_university
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        if not isinstance(data, list):
                            raise ValueError("JSON file must contain a list of dictionaries.")

                        row_count = 0
                        for entry in data:
                            # Map JSON keys to variables
                            data_tuple = (
                                clean_val(entry.get('program')),
                                clean_val(entry.get('comments')),
                                clean_val(entry.get('date_added')),
                                clean_val(entry.get('url')),
                                clean_val(entry.get('status')),
                                clean_val(entry.get('term')),
                                clean_val(entry.get('us_or_international')),
                                clean_val(entry.get('gpa')),
                                clean_val(entry.get('gre')),
                                clean_val(entry.get('gre_v')),
                                clean_val(entry.get('gre_aw')),
                                clean_val(entry.get('degree')),
                                clean_val(entry.get('llm_generated_program')),
                                clean_val(entry.get('llm_generated_university'))
                            )
                            
                            cur.execute(insert_query, data_tuple)
                            row_count += 1
                    
                    print(f"Successfully inserted {row_count} rows from JSON.")

                except FileNotFoundError:
                    print(f"Error: The file '{filename}' was not found.")
            
    except psycopg.Error as e:
        print(f"Database Error: {e}")

if __name__ == "__main__":
    load_data()