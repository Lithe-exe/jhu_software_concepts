import json
import re

class DataCleaner:
    def __init__(self, input_file="raw_applicant_data.json", output_file="applicant_data.json"):
        self.input_file = input_file
        self.output_file = output_file
        self.cleaned_data = []

    def load_data(self, data=None):
        """
        Loads data. 
        If 'data' is passed (from main.py memory), use it.
        Otherwise, load from the raw JSON file on disk.
        """
        if data:
            print(f"Received {len(data)} entries from memory.")
            return data
        
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                content = json.load(f)
                print(f"Loaded {len(content)} entries from {self.input_file}.")
                return content
        except (FileNotFoundError, ValueError):
            print(f"File {self.input_file} not found or empty.")
            return []

    def clean_data(self, raw_data):
        self.cleaned_data = [] # Reset
        print(f"Cleaning {len(raw_data)} entries...")
        
        for item in raw_data:
            # 1. Consolidate text for Regex analysis
            # We combine all possible text fields to ensure we find stats/dates anywhere they appear
            raw_text_blob = str(item.get("raw_text", "")) + " " + \
                            str(item.get("Decision Details", "")) + " " + \
                            str(item.get("raw_decision", "")) + " " + \
                            str(item.get("raw_comments", "")) + " " + \
                            str(item.get("Comments", ""))

            # 2. Extract Status and Date first
            status, decision_date_str = self._parse_status_date(raw_text_blob)
            
            # Format Date: User requested "20 Dec 2026" style
            formatted_date = None
            if decision_date_str:
                formatted_date = self._manual_format_date(decision_date_str)
            
            # Fallback: Check explicit date fields if regex failed
            if not formatted_date:
                raw_date = item.get("Date of Information Added") or item.get("raw_date_added")
                if raw_date:
                    formatted_date = self._manual_format_date(raw_date)

            # 3. Build the object with ALL keys present (Consistent Format)
            obj = {
                "Program Name": self._clean_str(item.get("raw_prog") or item.get("Program Name")),
                "University": self._clean_str(item.get("raw_inst") or item.get("University")),
                "Comments": self._clean_str(item.get("raw_comments") or item.get("Comments")),
                "Date of Information Added to Grad Café": formatted_date, # Default to decision date
                "URL link to applicant entry": item.get("url") or item.get("URL link"),
                "Applicant Status": status,
                "Accepted": None, # Will fill below
                "Rejected": None, # Will fill below
                "Semester and Year of Program Start": self._extract_season(raw_text_blob) or item.get("Season"),
                "International / American Student": self._extract_origin(raw_text_blob) or item.get("International / American Student"),
                "GRE Score": item.get("GRE Score"), # Will overwrite below if regex finds it
                "GRE V Score": item.get("GRE V Score"),
                "GRE AW": item.get("GRE AW"),
                "Masters or PhD": self._clean_str(item.get("raw_degree") or item.get("Masters or PhD")),
                "GPA": item.get("GPA") # Will overwrite below
            }

            # 4. Fill Conditional Fields
            if status == "Accepted":
                obj["Accepted"] = formatted_date
            elif status == "Rejected":
                obj["Rejected"] = formatted_date

            # 5. Extract Stats (Overwriting only if found in text, preserving existing if not)
            gpa = self._extract_gpa(raw_text_blob)
            if gpa: obj["GPA"] = gpa
            
            gre = self._extract_gre(raw_text_blob)
            if gre['total']: obj["GRE Score"] = gre['total']
            if gre['verbal']: obj["GRE V Score"] = gre['verbal']
            if gre['aw']: obj["GRE AW"] = gre['aw']

            # NOTE: We do NOT filter out None values anymore. 
            # This ensures every raw entry produces a cleaned entry with all keys.
            self.cleaned_data.append(obj)

        return self.cleaned_data

    def save_data(self):
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.cleaned_data, f, indent=4)
        print(f"Successfully saved {len(self.cleaned_data)} cleaned entries to {self.output_file}")

    # --- Helpers ---

    def _clean_str(self, s):
        if not s: return None
        return " ".join(str(s).split())

    def _parse_status_date(self, text):
        t = str(text).lower()
        status = "Other"
        if "accepted" in t: status = "Accepted"
        elif "rejected" in t: status = "Rejected"
        elif "wait" in t: status = "Waitlisted"
        elif "interview" in t: status = "Interview"
        
        # Regex for "on 30 Jan" or "on Jan 30"
        match = re.search(r'on\s+(\d{1,2})\s+([A-Za-z]{3})', text, re.IGNORECASE)
        if match:
            return status, f"{match.group(1)} {match.group(2)}"
        
        match2 = re.search(r'on\s+([A-Za-z]{3})\s+(\d{1,2})', text, re.IGNORECASE)
        if match2:
            return status, f"{match2.group(2)} {match2.group(1)}"
            
        return status, None

    def _manual_format_date(self, d_str):
        """
        Formats date to '20 Dec 2026' style.
        """
        if not d_str: return None
        
        d_str = str(d_str).replace(",", "").strip()
        
        # 1. Identify Year
        year_match = re.search(r'\d{4}', d_str)
        year = year_match.group(0) if year_match else "2026" # Default from context
        
        # 2. Identify Month
        # Map full names to short names for consistency
        month_map = {
            "january": "Jan", "february": "Feb", "march": "Mar", "april": "Apr", "may": "May", "june": "Jun",
            "july": "Jul", "august": "Aug", "september": "Sep", "october": "Oct", "november": "Nov", "december": "Dec",
            "jan": "Jan", "feb": "Feb", "mar": "Mar", "apr": "Apr", "jun": "Jun",
            "jul": "Jul", "aug": "Aug", "sep": "Sep", "oct": "Oct", "nov": "Nov", "dec": "Dec"
        }
        month_match = re.search(r'[A-Za-z]{3,}', d_str)
        if not month_match: return None # Can't format without month
        
        raw_month = month_match.group(0).lower()
        month = month_map.get(raw_month, raw_month.capitalize()[:3])
        
        # 3. Identify Day
        # Remove year to avoid confusing it with day
        temp_str = d_str.replace(year, "")
        day_match = re.search(r'\d{1,2}', temp_str)
        if not day_match: return None
        day = day_match.group(0) # Keep as '1' or '20', don't need leading zero for this specific style
        
        # Format: "20 Dec 2026"
        return f"{day} {month} {year}"

    def _extract_season(self, text):
        match = re.search(r'(Fall|Spring|Summer|Winter)\s+\d{4}', text, re.IGNORECASE)
        return match.group(0) if match else None

    def _extract_origin(self, text):
        t = str(text).lower()
        if "international" in t: return "International"
        if "american" in t: return "American"
        return None

    def _extract_gpa(self, text):
        match = re.search(r'GPA\s*:?\s*(\d\.\d+)', text, re.IGNORECASE)
        return float(match.group(1)) if match else None

    def _extract_gre(self, text):
        res = {'total': None, 'verbal': None, 'aw': None}
        v = re.search(r'V\s*(\d{3})', text)
        if v: res['verbal'] = int(v.group(1))
        
        aw = re.search(r'AW\s*(\d\.\d+)', text)
        if aw: res['aw'] = float(aw.group(1))
        
        t = re.search(r'GRE\s*(\d{3})', text)
        if t: res['total'] = int(t.group(1))
        
        return res

# --- Execution Block ---
if __name__ == "__main__":
    cleaner = DataCleaner()
    # Forces loading from the file to ensure we get the full history
    raw = cleaner.load_data()
    cleaner.clean_data(raw)
    cleaner.save_data()