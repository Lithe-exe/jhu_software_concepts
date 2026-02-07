import psycopg

class DataAnalyzer:
    def __init__(self):
        # Update your password here
        self.db_config = "host=localhost dbname=gradcafe_db user=postgres password=your_password port=5432"

    def _get_single_result(self, query):
        """Helper to execute a query and return the first value."""
        try:
            with psycopg.connect(self.db_config) as conn:
                result = conn.execute(query).fetchone()
                # Return the value, or "N/A" if the result is empty
                return result[0] if result else "N/A"
        except psycopg.Error as e:
            return f"SQL Error: {e}"

    def get_analysis(self):
        """Runs all queries and returns a dictionary of results."""
        data = {}

        # Q1: Applicants for Spring 2026
        data['q1'] = self._get_single_result(
            "SELECT COUNT(*) FROM applicants WHERE term = 'Spring 2026';"
        )

        # Q2: Percentage International (2 decimal places)
        # Logic: (Count International / Total Count) * 100
        data['q2'] = self._get_single_result("""
            SELECT ROUND(
                (COUNT(*) FILTER (WHERE us_or_international = 'International')::numeric / 
                 NULLIF(COUNT(*), 0)) * 100, 
            2) FROM applicants;
        """)

        # Q3: Averages (GPA, GRE, Verbal, Writing)
        # We fetch them individually for cleaner string formatting
        avg_gpa = self._get_single_result("SELECT ROUND(AVG(gpa)::numeric, 2) FROM applicants;")
        avg_gre = self._get_single_result("SELECT ROUND(AVG(gre)::numeric, 2) FROM applicants;")
        avg_gre_v = self._get_single_result("SELECT ROUND(AVG(gre_v)::numeric, 2) FROM applicants;")
        avg_gre_aw = self._get_single_result("SELECT ROUND(AVG(gre_aw)::numeric, 2) FROM applicants;")
        
        data['q3'] = f"GPA: {avg_gpa}, GRE: {avg_gre}, Verbal: {avg_gre_v}, AW: {avg_gre_aw}"

        # Q4: Average GPA of American Students for Spring 2026
        data['q4'] = self._get_single_result("""
            SELECT ROUND(AVG(gpa)::numeric, 2) FROM applicants 
            WHERE term = 'Spring 2026' AND us_or_international = 'American';
        """)
        return data