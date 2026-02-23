"""
Data Cleaning Module
====================

Handles the cleaning, normalization, and deduplication of scraped applicant data.
"""

import json
import os
import re


class DataCleaner:
    """Clean raw JSON data and merge it with existing normalized data."""

    DATE_KEY_VARIANTS = (
        "Date of Information Added to Grad CafÃ©",
        "Date of Information Added to Grad CafÃƒÂ©",
        "Date of Information Added to Grad CafÃƒÆ’Ã‚Â©",
    )

    def __init__(self, input_file="raw_applicant_data.json", output_file="applicant_data.json"):
        """Set input and output paths relative to this module when needed."""
        base_dir = os.path.dirname(os.path.abspath(__file__))

        if not os.path.isabs(input_file):
            self.input_file = os.path.join(base_dir, input_file)
        else:
            self.input_file = input_file

        if not os.path.isabs(output_file):
            self.output_file = os.path.join(base_dir, "..", output_file)
        else:
            self.output_file = output_file

        self.cleaned_data = []

    def update_and_merge(self):
        """Load raw and existing data, clean new rows, deduplicate, and persist."""
        existing_data = []
        try:
            with open(self.output_file, "r", encoding="utf-8") as file_handle:
                existing_data = json.load(file_handle)
        except (FileNotFoundError, ValueError):
            existing_data = []

        raw_data = []
        try:
            with open(self.input_file, "r", encoding="utf-8") as file_handle:
                raw_data = json.load(file_handle)
        except (FileNotFoundError, ValueError):
            return

        new_cleaned_entries = self.clean_data(raw_data)

        existing_sigs = set()
        for entry in existing_data:
            sig = (
                self._norm(entry.get("University")),
                self._norm(entry.get("Program Name")),
                self._norm(self._get_date(entry)),
                self._norm(entry.get("Comments")),
            )
            existing_sigs.add(sig)

        unique_new_entries = []
        for item in new_cleaned_entries:
            sig = (
                self._norm(item.get("University")),
                self._norm(item.get("Program Name")),
                self._norm(self._get_date(item)),
                self._norm(item.get("Comments")),
            )
            if sig not in existing_sigs:
                unique_new_entries.append(item)
                existing_sigs.add(sig)

        self.cleaned_data = unique_new_entries + existing_data
        self.save_data()

    def clean_data(self, raw_data):
        """Transform raw scraped rows into normalized applicant records."""
        cleaned_batch = []
        for item in raw_data:
            raw_text_blob = " ".join(
                [
                    str(item.get("raw_text", "")),
                    str(item.get("Decision Details", "")),
                    str(item.get("raw_decision", "")),
                    str(item.get("raw_comments", "")),
                    str(item.get("Comments", "")),
                ]
            )

            status, decision_date_str = self._parse_status_date(raw_text_blob)
            if decision_date_str:
                formatted_date = self._manual_format_date(decision_date_str)
            else:
                formatted_date = None

            if not formatted_date:
                raw_date = (
                    item.get("raw_date")
                    or item.get("Date of Information Added")
                    or item.get("raw_date_added")
                )
                if raw_date:
                    formatted_date = self._manual_format_date(raw_date)

            obj = {
                "Program Name": self._clean_str(item.get("raw_prog") or item.get("Program Name")),
                "University": self._clean_str(item.get("raw_inst") or item.get("University")),
                "Comments": self._clean_str(
                    item.get("raw_comments") or item.get("Comments"),
                    keep_empty=True,
                ),
                "Date of Information Added to Grad CafÃ©": formatted_date,
                "URL link to applicant entry": item.get("url") or item.get("URL link"),
                "Applicant Status": status,
                "Accepted": None,
                "Rejected": None,
                "Semester and Year of Program Start": (
                    self._extract_season(raw_text_blob) or item.get("Season")
                ),
                "International / American Student": (
                    self._extract_origin(raw_text_blob)
                    or item.get("International / American Student")
                ),
                "GRE Score": item.get("GRE Score"),
                "GRE V Score": item.get("GRE V Score"),
                "GRE AW": item.get("GRE AW"),
                "Masters or PhD": self._clean_str(
                    item.get("raw_degree") or item.get("Masters or PhD")
                ),
                "GPA": item.get("GPA"),
                "llm_generated_program": item.get("llm_generated_program"),
                "llm_generated_university": item.get("llm_generated_university"),
            }

            if status == "Accepted":
                obj["Accepted"] = formatted_date
            elif status == "Rejected":
                obj["Rejected"] = formatted_date

            gpa = self._extract_gpa(raw_text_blob)
            if gpa is not None:
                obj["GPA"] = gpa

            gre = self._extract_gre(raw_text_blob)
            if gre["total"] is not None:
                obj["GRE Score"] = gre["total"]
            if gre["verbal"] is not None:
                obj["GRE V Score"] = gre["verbal"]
            if gre["aw"] is not None:
                obj["GRE AW"] = gre["aw"]

            cleaned_batch.append(self._prune_nulls(obj))

        return cleaned_batch

    def save_data(self):
        """Write cleaned records to disk."""
        try:
            with open(self.output_file, "w", encoding="utf-8") as file_handle:
                json.dump(self.cleaned_data, file_handle, indent=4)
        except (OSError, TypeError, ValueError) as save_error:
            print(f"Error saving data: {save_error}")

    @staticmethod
    def _norm(value):
        return " ".join(str(value).strip().lower().split()) if value else ""

    @classmethod
    def _get_date(cls, entry):
        for key in cls.DATE_KEY_VARIANTS:
            value = entry.get(key)
            if value:
                return value
        return None

    @staticmethod
    def _clean_str(value, keep_empty=False):
        if value is None:
            return "" if keep_empty else None
        normalized = " ".join(str(value).split())
        if normalized == "":
            return "" if keep_empty else None
        return normalized

    @staticmethod
    def _prune_nulls(obj):
        pruned = {}
        for key, value in obj.items():
            if key == "Comments":
                pruned[key] = "" if (value is None or str(value).strip() == "") else value
                continue
            if value is None:
                continue
            if isinstance(value, str) and value.strip() == "":
                continue
            pruned[key] = value
        pruned.setdefault("Comments", "")
        return pruned

    @staticmethod
    def _parse_status_date(text):
        text_lower = str(text).lower()
        status = "Other"
        if "accepted" in text_lower:
            status = "Accepted"
        elif "rejected" in text_lower:
            status = "Rejected"
        elif "wait" in text_lower:
            status = "Waitlisted"
        elif "interview" in text_lower:
            status = "Interview"

        match = re.search(r"on\s+(\d{1,2})\s+([A-Za-z]{3})", text, re.IGNORECASE)
        if match:
            return status, f"{match.group(1)} {match.group(2)}"

        match_two = re.search(r"on\s+([A-Za-z]{3})\s+(\d{1,2})", text, re.IGNORECASE)
        if match_two:
            return status, f"{match_two.group(2)} {match_two.group(1)}"

        return status, None

    @staticmethod
    def _manual_format_date(date_str):
        if not date_str:
            return None

        cleaned = str(date_str).replace(",", "").strip()
        year_match = re.search(r"\d{4}", cleaned)
        year = year_match.group(0) if year_match else "2026"

        month_map = {
            "jan": "Jan",
            "feb": "Feb",
            "mar": "Mar",
            "apr": "Apr",
            "may": "May",
            "jun": "Jun",
            "jul": "Jul",
            "aug": "Aug",
            "sep": "Sep",
            "oct": "Oct",
            "nov": "Nov",
            "dec": "Dec",
        }
        month_match = re.search(r"[A-Za-z]{3,}", cleaned)
        if not month_match:
            return None

        raw_month = month_match.group(0).lower()[:3]
        month = month_map.get(raw_month, raw_month.capitalize())

        without_year = cleaned.replace(year, "")
        day_match = re.search(r"\d{1,2}", without_year)
        if not day_match:
            return None
        day = day_match.group(0)
        return f"{day} {month} {year}"

    @staticmethod
    def _extract_season(text):
        match = re.search(r"(Fall|Spring|Summer|Winter)\s+\d{4}", text, re.IGNORECASE)
        return match.group(0) if match else None

    @staticmethod
    def _extract_origin(text):
        text_lower = str(text).lower()
        if "international" in text_lower:
            return "International"
        if "american" in text_lower:
            return "American"
        return None

    @staticmethod
    def _extract_gpa(text):
        match = re.search(r"GPA\s*:?\s*(\d\.\d+)", text, re.IGNORECASE)
        return float(match.group(1)) if match else None

    @staticmethod
    def _extract_gre(text):
        result = {"total": None, "verbal": None, "aw": None}
        if not text:
            return result

        total_match = re.search(r"GRE\s*:?\s*(\d{3})", text, re.IGNORECASE)
        if total_match:
            result["total"] = int(total_match.group(1))

        verbal_match = re.search(r"V\s*(\d{3})", text, re.IGNORECASE)
        if verbal_match:
            result["verbal"] = int(verbal_match.group(1))

        aw_match = re.search(r"AW\s*(\d(?:\.\d)?)", text, re.IGNORECASE)
        if aw_match:
            result["aw"] = float(aw_match.group(1))

        return result


def main():
    """Execute the cleaning pipeline directly."""
    cleaner = DataCleaner()
    cleaner.update_and_merge()


if __name__ == "__main__":
    main()
