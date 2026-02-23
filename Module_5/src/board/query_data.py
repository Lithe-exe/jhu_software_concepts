"""
Data Analyzer Module
====================

Executes SQL queries against the database to generate analytics.
"""

import psycopg
from .load_data import DB_INFO

class DataAnalyzer:
    """
    Class for running analytical queries on the applicants table.
    """
    def __init__(self):
        self.db_config = DB_INFO

    def _get_single_result(self, query):
        """
        Helper to execute a query and return the first value.

        Args:
            query (str): SQL query to execute.

        Returns:
            any: The result value or 'N/A'/'Error'.
        """
        try:
            with psycopg.connect(self.db_config) as conn:
                result = conn.execute(query).fetchone()
                return result[0] if result else "N/A"
        except psycopg.Error as e:
            return f"SQL Error: {e}"

    def get_analysis(self):
        """
        Runs all queries and returns a dictionary of results.

        Returns:
            dict: Key-value pairs of analysis questions and answers.
        """
        data = {}

        data['q1'] = self._get_single_result(
            "SELECT COUNT(*) FROM applicants WHERE term = 'Spring 2026';"
        )

        data['q2'] = self._get_single_result("""
            SELECT ROUND(
                (COUNT(*) FILTER (WHERE us_or_international = 'International')::numeric / 
                 NULLIF(COUNT(*), 0)) * 100, 
            2) FROM applicants;
        """)

        avg_gpa = self._get_single_result("SELECT ROUND(AVG(gpa)::numeric, 2) FROM applicants;")
        avg_gre = self._get_single_result("SELECT ROUND(AVG(gre)::numeric, 2) FROM applicants;")
        avg_gre_v = self._get_single_result("SELECT ROUND(AVG(gre_v)::numeric, 2) FROM applicants;")
        avg_gre_aw = self._get_single_result("SELECT ROUND(AVG(gre_aw)::numeric, 2) FROM applicants;")
        
        data['q3'] = f"GPA: {avg_gpa}, GRE: {avg_gre}, Verbal: {avg_gre_v}, AW: {avg_gre_aw}"

        data['q4'] = self._get_single_result("""
            SELECT ROUND(AVG(gpa)::numeric, 2) FROM applicants 
            WHERE term = 'Spring 2026' AND us_or_international = 'American';
        """)
        
        data['q5'] = self._get_single_result("""
            SELECT ROUND(
                (COUNT(*) FILTER (WHERE status ILIKE 'Accept%')::numeric /
                 NULLIF(COUNT(*), 0)) * 100,
            2) FROM applicants WHERE term = 'Spring 2025';
        """)

        data['q6'] = self._get_single_result("""
            SELECT ROUND(AVG(gpa)::numeric, 2) FROM applicants
            WHERE term = 'Spring 2026' AND status ILIKE 'Accept%';
        """)

        data['q7'] = self._get_single_result("""
            SELECT COUNT(*) FROM applicants
            WHERE university ILIKE '%Johns Hopkins%'
            AND program ILIKE '%Computer Science%'
            AND degree = 'Masters';
        """)

        data['q8'] = self._get_single_result("""
            SELECT COUNT(*) FROM applicants
            WHERE term LIKE '%2026%'
            AND status ILIKE 'Accept%'
            AND degree = 'PhD'
            AND program ILIKE '%Computer Science%'
            AND (university ILIKE '%Georgetown%' OR university ILIKE '%MIT%' OR university ILIKE '%Stanford%' OR university ILIKE '%Carnegie Mellon%');
        """)
        
        data['q9'] = self._get_single_result("""
            SELECT COUNT(*) FROM applicants
            WHERE term LIKE '%2026%'
            AND status ILIKE 'Accept%'
            AND degree = 'PhD'
            AND COALESCE(llm_generated_program, program) ILIKE '%Computer Science%'
            AND (COALESCE(llm_generated_university, university) ILIKE '%Georgetown%' 
                 OR COALESCE(llm_generated_university, university) ILIKE '%Massachusetts Institute of Technology%' 
                 OR COALESCE(llm_generated_university, university) ILIKE '%MIT%' 
                 OR COALESCE(llm_generated_university, university) ILIKE '%Stanford%' 
                 OR COALESCE(llm_generated_university, university) ILIKE '%Carnegie Mellon%');
        """)
        
        try:
            with psycopg.connect(self.db_config) as conn:
                res = conn.execute("SELECT degree, ROUND(AVG(gre)::numeric, 0) FROM applicants WHERE degree IS NOT NULL GROUP BY degree").fetchall()
                data['cq1'] = ", ".join([f"{r[0]}: {r[1]}" for r in res]) if res else "N/A"
        except Exception:
            data['cq1'] = "N/A"
       
        data['cq2'] = self._get_single_result("SELECT COUNT(*) FROM applicants;")

        return data