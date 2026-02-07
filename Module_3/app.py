from flask import Flask, render_template, redirect, url_for, flash
import load_data
import query_data
from scrape import GradCafeScraper
from clean import DataCleaner

app = Flask(__name__)
app.secret_key = 'secret'

@app.route('/')
def index():
    # Use query_data to get answers for the HTML
    try:
        analyzer = query_data.DataAnalyzer()
        data = analyzer.get_analysis()
    except Exception as e:
        data = {}
        print(f"Query Error: {e}")

    return render_template('index.html', data=data)

@app.route('/pull-data', methods=['POST'])
def pull_data():
    print("--- Starting Data Pull Process ---")
    
    # Define filenames
    raw_file = "raw_applicant_data.json"
    # This must match what load_data.py is looking for:
    final_file = "applicant_data.json" 

    try:
        # STEP 1: SCRAPE
        if GradCafeScraper:
            print("1. Scraping...")
            # Initialize scraper (using 50 count for speed testing, increase later)
            scraper = GradCafeScraper(output_file=raw_file)
            raw_data = scraper.scrape_data(target_count=50) 
            scraper.save_raw_data()
        else:
            flash("Error: scrape.py not found or GradCafeScraper class missing.")
            return redirect(url_for('index'))

        # STEP 2: CLEAN
        if DataCleaner:
            print("2. Cleaning...")
            cleaner = DataCleaner(input_file=raw_file, output_file=final_file)
            # Pass the raw_data we just scraped
            cleaner.clean_data(raw_data) 
            cleaner.save_data()
        else:
            print("Warning: clean.py not found. Skipping cleaning step.")

        # STEP 3: LOAD TO DB
        print("3. Loading to Database...")
        # Calls the function in load_data.py
        if hasattr(load_data, 'load_json_data'):
            load_data.load_json_data()
        elif hasattr(load_data, 'load_data'):
            load_data.load_data()
        else:
            flash("Error: No load function found in load_data.py")
            return redirect(url_for('index'))

        flash("Success! Data scraped, cleaned, and loaded.")

    except Exception as e:
        print(f"Process Failed: {e}")
        flash(f"Error during pull: {e}")

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)