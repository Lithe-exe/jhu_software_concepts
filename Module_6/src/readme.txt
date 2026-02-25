Sultan Jacobs 
JHU ID: B443F8
Module info: Module 3 Database Queries Assignment Experiment| Due 02/08/26 @ 11:59 EST

Approach
This module scrapes GradCafe, cleans and merges new entries into a single JSON file, and loads the results into a local PostgreSQL database. A Flask app displays analysis from the database.
board/clean.py normalizes key fields and only appends entries not already present in applicant_data.json. applicant_data.json is the canonical dataset; the DB is always reset to match it on Pull Data.

**Instructions**
Start the Flask app:
   - From Module_3:
     .\.venv\Scripts\python.exe app.py
Open http://localhost:5000
Click Pull Data to scrape and load.

Pull Data button in the Flask app:
   - Scrape newest pages to board/raw_applicant_data.json.
   - Clean and merge into applicant_data.json (new entries only).
   - Reset DB and reload from applicant_data.json (DB mirrors JSON).
Update Analysis button:
   - Refreshes the page and re-runs queries against the DB.

Database
- Uses PostgreSQL on localhost with "applicant_data.json" as loaded data

Notes
- If there is no local file when run then a full scrape will take place otherwise it will scrape the most recent pages until a similar entry is found
- If you change file locations, keep the paths in board/scrape.py and board/clean.py aligned.