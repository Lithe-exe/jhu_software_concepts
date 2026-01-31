import json
import re

class DataCleaner:
    def __init__(self, input_file="raw_applicant_data.json", output_file="applicant_data.json"):
        self.input_file = input_file
        self.output_file = output_file
        self.cleaned_data = []

    def load_data(self):
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"File {self.input_file} not found.")
            return []

    def clean_data(self, raw_data):
        self.cleaned_data = [] # Reset
        
        for item in raw_data:
            # Initialize dictionary with target keys mapping to raw keys
            obj = {
                "Program Name": item.get("Program Name"),
                "University": item.get("University"),
                "Comments": item.get("Comments"),
                "Date of Information Added to Grad Café": item.get("Date of Information Added"),
                "URL link to applicant entry": item.get("URL link"),
                "Applicant Status": item.get("Applicant Status"),
                "Accepted": None,
                "Rejected": None,
                "Semester and Year of Program Start": item.get("Season"),
                "International / American Student": item.get("International / American Student"),
                "GRE Score": item.get("GRE Score"),
                "GRE V Score": item.get("GRE V Score"),
                "GRE AW": item.get("GRE AW"),
                "Masters or PhD": item.get("Masters or PhD"),
                "GPA": item.get("GPA")
            }

            # --- Extract Specific Decision Date ---
            # Input format example: "Wait listed on 30 Jan" or "Accepted on 25 Jan"
            decision_details = item.get("Decision Details", "")
            status = item.get("Applicant Status", "")
            raw_date_added = item.get("Date of Information Added", "")
            
            # Extract the date string (e.g., "30 Jan")
            decision_date_str = self._extract_short_date_string(decision_details)
            
            if decision_date_str:
                # We try to find the year from the "Date Added" field to make the string complete
                # Example raw_date_added: "January 31, 2026"
                year = "2026" # Default backup
                if raw_date_added and "," in raw_date_added:
                    year = raw_date_added.split(",")[-1].strip()
                
                # Create a simple string representation: "30 Jan 2026"
                full_date_string = f"{decision_date_str} {year}"

                if status == "Accepted":
                    obj["Accepted"] = full_date_string
                elif status == "Rejected":
                    obj["Rejected"] = full_date_string

            # --- Remove Null Values ---
            # This filters out any key where the value is None
            clean_obj = {k: v for k, v in obj.items() if v is not None}
            
            self.cleaned_data.append(clean_obj)

        return self.cleaned_data

    def save_data(self):
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.cleaned_data, f, indent=4)
        print(f"Cleaned data saved to {self.output_file}")

    # --- Helpers ---

    def _extract_short_date_string(self, text):
        """Finds '30 Jan' inside 'Rejected on 30 Jan'"""
        if not text: return None
        # Regex looks for the word "on" followed by a number and a month name
        match = re.search(r'on\s+(\d{1,2}\s+[A-Za-z]{3})', text)
        return match.group(1) if match else None

# --- Execution Block ---
if __name__ == "__main__":
    cleaner = DataCleaner()
    raw_data = cleaner.load_data()
    
    if raw_data:
        cleaner.clean_data(raw_data)
        cleaner.save_data()
    else:
        print("No data found to clean.")