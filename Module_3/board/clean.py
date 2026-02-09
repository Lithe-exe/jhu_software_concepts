import json
import re

class DataCleaner:
    def __init__(self, input_file="raw_applicant_data.json", output_file="applicant_data.json"):
        self.input_file = input_file
        self.output_file = output_file
        self.cleaned_data = []

    def update_and_merge(self):
        """
        Loads existing data, loads new raw data, cleans the new data,
        merges them (preventing duplicates), and saves the result.
        """
        # 1. Load Existing Data
        existing_data = []
        try:
            with open(self.output_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                print(f"Loaded {len(existing_data)} existing entries from {self.output_file}.")
        except (FileNotFoundError, ValueError):
            print(f"No existing {self.output_file} found or file empty. Starting fresh.")
            existing_data = []

        # 2. Load New Raw Data
        raw_data = []
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                print(f"Loaded {len(raw_data)} raw entries from {self.input_file}.")
        except (FileNotFoundError, ValueError):
            print(f"File {self.input_file} not found or empty. Aborting update.")
            return

        # 3. Clean the New Raw Data
        # We process the raw list into a clean list
        new_cleaned_entries = self.clean_data(raw_data)

        # 4. Merge (Deduplication)
        # We build a set of signatures from the EXISTING data to ensure we don't add duplicates.
        # Signature: (University, Program Name, Date, Comments)
        existing_sigs = set()
        for entry in existing_data:
            sig = (
                entry.get("University"),
                entry.get("Program Name"),
                entry.get("Date of Information Added to Grad Café"),
                entry.get("Comments")
            )
            existing_sigs.add(sig)

        unique_new_entries = []
        for item in new_cleaned_entries:
            sig = (
                item.get("University"),
                item.get("Program Name"),
                item.get("Date of Information Added to Grad Café"),
                item.get("Comments")
            )
            
            # If we haven't seen this entry in the existing file, add it
            if sig not in existing_sigs:
                unique_new_entries.append(item)
                existing_sigs.add(sig) # Prevent duplicates within the new batch itself

        print(f"Found {len(unique_new_entries)} new unique entries to add.")

        # 5. Combine: Newest on top, followed by existing history
        self.cleaned_data = unique_new_entries + existing_data
        
        # 6. Save
        self.save_data()

    def clean_data(self, raw_data):
        # Local list to hold newly cleaned items
        cleaned_batch = []
        
        for item in raw_data:
            # 1. Consolidate text for regex analysis
            raw_text_blob = (
                str(item.get("raw_text", "")) + " " +
                str(item.get("Decision Details", "")) + " " +
                str(item.get("raw_decision", "")) + " " +
                str(item.get("raw_comments", "")) + " " +
                str(item.get("Comments", ""))
            )

            # 2. Extract Status and Date
            status, decision_date_str = self._parse_status_date(raw_text_blob)

            formatted_date = None
            if decision_date_str:
                formatted_date = self._manual_format_date(decision_date_str)

            if not formatted_date:
                # Check scraper's raw_date, then old keys
                raw_date = (
                    item.get("raw_date") or 
                    item.get("Date of Information Added") or 
                    item.get("raw_date_added")
                )
                if raw_date:
                    formatted_date = self._manual_format_date(raw_date)

            # 3. Build object. Start with direct mappings and cleaned strings.
            obj = {
                "Program Name": self._clean_str(item.get("raw_prog") or item.get("Program Name")),
                "University": self._clean_str(item.get("raw_inst") or item.get("University")),
                "Comments": self._clean_str(
                    item.get("raw_comments") or item.get("Comments"),
                    keep_empty=True
                ),
                "Date of Information Added to Grad Café": formatted_date,
                "URL link to applicant entry": item.get("url") or item.get("URL link"),
                "Applicant Status": status,
                "Accepted": None,
                "Rejected": None,
                "Semester and Year of Program Start": (
                    self._extract_season(raw_text_blob) or item.get("Season")
                ),
                "International / American Student": (
                    self._extract_origin(raw_text_blob) or item.get("International / American Student")
                ),
                "GRE Score": item.get("GRE Score"),
                "GRE V Score": item.get("GRE V Score"),
                "GRE AW": item.get("GRE AW"),
                "Masters or PhD": self._clean_str(item.get("raw_degree") or item.get("Masters or PhD")),
                "GPA": item.get("GPA"),
                # Preserve LLM fields if they happen to exist in raw (rare, but good practice)
                "llm_generated_program": item.get("llm_generated_program"),
                "llm_generated_university": item.get("llm_generated_university")
            }

            # 4. Conditional fields
            if status == "Accepted":
                obj["Accepted"] = formatted_date
            elif status == "Rejected":
                obj["Rejected"] = formatted_date

            # 5. Extract stats (overwrite only if found)
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

            # 6. Remove null/empty values, but always keep Comments
            obj = self._prune_nulls(obj)

            cleaned_batch.append(obj)

        return cleaned_batch

    # Saves cleaned data to output file
    def save_data(self):
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.cleaned_data, f, indent=4)
            print(f"Successfully saved {len(self.cleaned_data)} cleaned entries to {self.output_file}")
        except Exception as e:
            print(f"Error saving data: {e}")

    # ---------- Helpers ----------

    def _clean_str(self, s, keep_empty=False):
       # Formats strings by stripping extra whitespace & handling nulls
        if s is None:
            return "" if keep_empty else None

        s = " ".join(str(s).split())
        if s == "":
            return "" if keep_empty else None
        return s
    
    # stops null/empty strings except for comments from being in cleaned data
    def _prune_nulls(self, obj):
       
        pruned = {}

        for k, v in obj.items():
            if k == "Comments":
                pruned[k] = "" if (v is None or str(v).strip() == "") else v
                continue

            if v is None:
                continue
            if isinstance(v, str) and v.strip() == "":
                continue

            pruned[k] = v

        pruned.setdefault("Comments", "")
        return pruned

    # Parses status and date from text blobs
    def _parse_status_date(self, text):
        t = str(text).lower()
        status = "Other"
        if "accepted" in t:
            status = "Accepted"
        elif "rejected" in t:
            status = "Rejected"
        elif "wait" in t:
            status = "Waitlisted"
        elif "interview" in t:
            status = "Interview"

        match = re.search(r'on\s+(\d{1,2})\s+([A-Za-z]{3})', text, re.IGNORECASE)
        if match:
            return status, f"{match.group(1)} {match.group(2)}"

        match2 = re.search(r'on\s+([A-Za-z]{3})\s+(\d{1,2})', text, re.IGNORECASE)
        if match2:
            return status, f"{match2.group(2)} {match2.group(1)}"

        return status, None

    # Handles various date formats manually
    def _manual_format_date(self, d_str):
        if not d_str:
            return None

        d_str = str(d_str).replace(",", "").strip()

        year_match = re.search(r'\d{4}', d_str)
        year = year_match.group(0) if year_match else "2026"
        
        month_map = {
            "january": "Jan", "february": "Feb", "march": "Mar", "april": "Apr",
            "may": "May", "june": "Jun", "july": "Jul", "august": "Aug",
            "september": "Sep", "october": "Oct", "november": "Nov", "december": "Dec",
            "jan": "Jan", "feb": "Feb", "mar": "Mar", "apr": "Apr",
            "jun": "Jun", "jul": "Jul", "aug": "Aug", "sep": "Sep",
            "oct": "Oct", "nov": "Nov", "dec": "Dec"
        }

        month_match = re.search(r'[A-Za-z]{3,}', d_str)
        if not month_match:
            return None

        raw_month = month_match.group(0).lower()
        month = month_map.get(raw_month, raw_month.capitalize()[:3])

        temp_str = d_str.replace(year, "")
        day_match = re.search(r'\d{1,2}', temp_str)
        if not day_match:
            return None

        day = day_match.group(0)
        return f"{day} {month} {year}"

    # Extracts the semester 
    def _extract_season(self, text):
        match = re.search(r'(Fall|Spring|Summer|Winter)\s+\d{4}', text, re.IGNORECASE)
        return match.group(0) if match else None

    def _extract_origin(self, text):
        t = str(text).lower()
        if "international" in t:
            return "International"
        if "american" in t:
            return "American"
        return None

    def _extract_gpa(self, text):
        match = re.search(r'GPA\s*:?\s*(\d\.\d+)', text, re.IGNORECASE)
        return float(match.group(1)) if match else None

    def _extract_gre(self, text):
        res = {"total": None, "verbal": None, "aw": None}

        v = re.search(r'V\s*(\d{3})', text)
        if v:
            res["verbal"] = int(v.group(1))

        aw = re.search(r'AW\s*(\d\.\d+)', text)
        if aw:
            res["aw"] = float(aw.group(1))

        t = re.search(r'GRE\s*(\d{3})', text)
        if t:
            res["total"] = int(t.group(1))

        return res

# ---------- Execution ----------
if __name__ == "__main__":
    cleaner = DataCleaner()
    # Execute the update_and_merge logic instead of just cleaning
    cleaner.update_and_merge()