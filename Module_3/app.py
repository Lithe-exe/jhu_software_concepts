from flask import Flask, render_template, redirect, url_for, flash
import board.load_data
import board.query_data 
from board.scrape import GradCafeScraper
from board.clean import DataCleaner

app = Flask(__name__, template_folder="board/templates", static_folder="board/static")
app.secret_key = 'secret'

@app.route('/')
def index():
    try:
        analyzer = board.query_data.DataAnalyzer()
        data = analyzer.get_analysis()
    except Exception as e:
        data = {}
        print(f"Query Error: {e}")
    return render_template('index.html', data=data)

@app.route('/pull-data', methods=['POST'])
def pull_data():
    print("--- Starting Data Pull Process ---")
    
    base_dir = __file__.rsplit("\\", 1)[0]
    raw_file = base_dir + "\\board\\raw_applicant_data.json"
    final_file = base_dir + "\\applicant_data.json"

    try:
        # 1. SCRAPE
        print("1. Scraping...")
        scraper = GradCafeScraper(output_file=raw_file)
        raw_data = scraper.scrape_data(target_count=50000) 
        scraper.save_raw_data()

        # 2. CLEAN + MERGE
        print("2. Cleaning + Merging...")
        cleaner = DataCleaner(input_file=raw_file, output_file=final_file)
        cleaner.update_and_merge()

        # 3. LOAD MERGED DATA
        print("3. Loading to Database...")
        board.load_data.load_data(final_file, reset=False)

        flash("Success! Data scraped, cleaned, and loaded.")

    except Exception as e:
        print(f"Process Failed: {e}")
        flash(f"Error during pull: {e}")

    return redirect(url_for('index'))

# Route for the "Update Analysis" button in HTML
@app.route('/update-analysis', methods=['POST'])
def update_analysis():
    flash("Analysis updated (refreshing data from DB).")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
