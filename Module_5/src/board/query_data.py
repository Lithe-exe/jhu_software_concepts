"""
Data Analyzer Module
====================
Run safe, parameterized SQL queries that calculate analytics.
"""

import psycopg
from psycopg import sql

from .load_data import get_db_info


class DataAnalyzer:  # pylint: disable=too-few-public-methods
    """Execute dynamically composed read-only analytics queries."""

    def __init__(self):
        self.db_config = get_db_info()

    def _get_single_result(self, query, params=None):
        """Execute one query and return the first scalar value."""
        try:
            with psycopg.connect(self.db_config) as conn:
                result = conn.execute(query, params).fetchone()
                return result[0] if result else "N/A"
        except psycopg.Error as error:
            return f"SQL Error: {error}"

    def get_analysis(self, limit=100):  # pylint: disable=too-many-locals
        """Run all standard analysis queries with a bounded row limit."""
        safe_limit = max(1, min(int(limit), 100))
        data = {}

        q1 = sql.SQL("SELECT COUNT(*) FROM {} WHERE {} = {} LIMIT {}").format(
            sql.Identifier("applicants"),
            sql.Identifier("term"),
            sql.Placeholder(),
            sql.Placeholder(),
        )
        data["q1"] = self._get_single_result(q1, ["Spring 2026", safe_limit])

        q2 = sql.SQL(
            """
            SELECT ROUND(
                (COUNT(*) FILTER (WHERE {} = {})::numeric /
                 NULLIF(COUNT(*), 0)) * 100,
            2) FROM {} LIMIT {}
            """
        ).format(
            sql.Identifier("us_or_international"),
            sql.Placeholder(),
            sql.Identifier("applicants"),
            sql.Placeholder(),
        )
        data["q2"] = self._get_single_result(q2, ["International", safe_limit])

        def _avg(col_name):
            query = sql.SQL(
                "SELECT ROUND(AVG({})::numeric, 2) FROM {} LIMIT {}"
            ).format(
                sql.Identifier(col_name),
                sql.Identifier("applicants"),
                sql.Placeholder(),
            )
            return self._get_single_result(query, [safe_limit])

        data["q3"] = (
            f"GPA: {_avg('gpa')}, GRE: {_avg('gre')}, "
            f"Verbal: {_avg('gre_v')}, AW: {_avg('gre_aw')}"
        )

        q4 = sql.SQL(
            """
            SELECT ROUND(AVG({})::numeric, 2) FROM {}
            WHERE {} = {} AND {} = {} LIMIT {}
            """
        ).format(
            sql.Identifier("gpa"),
            sql.Identifier("applicants"),
            sql.Identifier("term"),
            sql.Placeholder(),
            sql.Identifier("us_or_international"),
            sql.Placeholder(),
            sql.Placeholder(),
        )
        data["q4"] = self._get_single_result(q4, ["Spring 2026", "American", safe_limit])

        q5 = sql.SQL(
            """
            SELECT ROUND(
                (COUNT(*) FILTER (WHERE {} ILIKE {})::numeric /
                 NULLIF(COUNT(*), 0)) * 100,
            2) FROM {} WHERE {} = {} LIMIT {}
            """
        ).format(
            sql.Identifier("status"),
            sql.Placeholder(),
            sql.Identifier("applicants"),
            sql.Identifier("term"),
            sql.Placeholder(),
            sql.Placeholder(),
        )
        data["q5"] = self._get_single_result(q5, ["Accept%", "Spring 2025", safe_limit])

        q6 = sql.SQL(
            """
            SELECT ROUND(AVG({})::numeric, 2) FROM {}
            WHERE {} = {} AND {} ILIKE {} LIMIT {}
            """
        ).format(
            sql.Identifier("gpa"),
            sql.Identifier("applicants"),
            sql.Identifier("term"),
            sql.Placeholder(),
            sql.Identifier("status"),
            sql.Placeholder(),
            sql.Placeholder(),
        )
        data["q6"] = self._get_single_result(q6, ["Spring 2026", "Accept%", safe_limit])

        q7 = sql.SQL(
            """
            SELECT COUNT(*) FROM {} WHERE {} ILIKE {} AND {} ILIKE {} AND {} = {} LIMIT {}
            """
        ).format(
            sql.Identifier("applicants"),
            sql.Identifier("university"),
            sql.Placeholder(),
            sql.Identifier("program"),
            sql.Placeholder(),
            sql.Identifier("degree"),
            sql.Placeholder(),
            sql.Placeholder(),
        )
        data["q7"] = self._get_single_result(
            q7,
            ["%Johns Hopkins%", "%Computer Science%", "Masters", safe_limit],
        )

        q8 = sql.SQL(
            """
            SELECT COUNT(*) FROM {} WHERE {} LIKE {} AND {} ILIKE {} AND {} = {}
            AND {} ILIKE {} AND
            ({} ILIKE {} OR {} ILIKE {} OR {} ILIKE {} OR {} ILIKE {}) LIMIT {}
            """
        ).format(
            sql.Identifier("applicants"),
            sql.Identifier("term"),
            sql.Placeholder(),
            sql.Identifier("status"),
            sql.Placeholder(),
            sql.Identifier("degree"),
            sql.Placeholder(),
            sql.Identifier("program"),
            sql.Placeholder(),
            sql.Identifier("university"),
            sql.Placeholder(),
            sql.Identifier("university"),
            sql.Placeholder(),
            sql.Identifier("university"),
            sql.Placeholder(),
            sql.Identifier("university"),
            sql.Placeholder(),
            sql.Placeholder(),
        )
        data["q8"] = self._get_single_result(
            q8,
            [
                "%2026%",
                "Accept%",
                "PhD",
                "%Computer Science%",
                "%Georgetown%",
                "%MIT%",
                "%Stanford%",
                "%Carnegie Mellon%",
                safe_limit,
            ],
        )

        q9 = sql.SQL(
            """
            SELECT COUNT(*) FROM {} WHERE {} LIKE {} AND {} ILIKE {} AND {} = {}
            AND COALESCE({}, {}) ILIKE {} AND (
                COALESCE({}, {}) ILIKE {} OR COALESCE({}, {}) ILIKE {} OR
                COALESCE({}, {}) ILIKE {} OR COALESCE({}, {}) ILIKE {} OR
                COALESCE({}, {}) ILIKE {}
            ) LIMIT {}
            """
        ).format(
            sql.Identifier("applicants"),
            sql.Identifier("term"),
            sql.Placeholder(),
            sql.Identifier("status"),
            sql.Placeholder(),
            sql.Identifier("degree"),
            sql.Placeholder(),
            sql.Identifier("llm_generated_program"),
            sql.Identifier("program"),
            sql.Placeholder(),
            sql.Identifier("llm_generated_university"),
            sql.Identifier("university"),
            sql.Placeholder(),
            sql.Identifier("llm_generated_university"),
            sql.Identifier("university"),
            sql.Placeholder(),
            sql.Identifier("llm_generated_university"),
            sql.Identifier("university"),
            sql.Placeholder(),
            sql.Identifier("llm_generated_university"),
            sql.Identifier("university"),
            sql.Placeholder(),
            sql.Identifier("llm_generated_university"),
            sql.Identifier("university"),
            sql.Placeholder(),
            sql.Placeholder(),
        )
        data["q9"] = self._get_single_result(
            q9,
            [
                "%2026%",
                "Accept%",
                "PhD",
                "%Computer Science%",
                "%Georgetown%",
                "%Massachusetts Institute of Technology%",
                "%MIT%",
                "%Stanford%",
                "%Carnegie Mellon%",
                safe_limit,
            ],
        )

        try:
            with psycopg.connect(self.db_config) as conn:
                cq1 = sql.SQL(
                    """
                    SELECT {}, ROUND(AVG({})::numeric, 0) FROM {}
                    WHERE {} IS NOT NULL GROUP BY {} LIMIT {}
                    """
                ).format(
                    sql.Identifier("degree"),
                    sql.Identifier("gre"),
                    sql.Identifier("applicants"),
                    sql.Identifier("degree"),
                    sql.Identifier("degree"),
                    sql.Placeholder(),
                )
                result = conn.execute(cq1, [safe_limit]).fetchall()
                if result:
                    data["cq1"] = ", ".join([f"{row[0]}: {row[1]}" for row in result])
                else:
                    data["cq1"] = "N/A"
        except Exception:  # pylint: disable=broad-except
            data["cq1"] = "N/A"

        cq2 = sql.SQL("SELECT COUNT(*) FROM {} LIMIT {}").format(
            sql.Identifier("applicants"),
            sql.Placeholder(),
        )
        data["cq2"] = self._get_single_result(cq2, [safe_limit])

        return data
