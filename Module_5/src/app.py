"""
Flask Application Module
========================
You use this module to initialize the Flask application, define routes, and
orchestrate the ETL (Extract, Transform, Load) pipeline via HTTP endpoints.
"""

import os

from flask import Flask, render_template, flash, jsonify
import board.load_data
import board.query_data
from board.scrape import GradCafeScraper
from board.clean import DataCleaner

IS_BUSY = False
CACHED_ANALYSIS = None

def create_app(test_config=None):
    """
    You use this factory function to create and configure the Flask application.
    """
    app = Flask(__name__, template_folder="board/templates", static_folder="board/static")
    app.secret_key = 'secret'

    if test_config:
        app.config.update(test_config)

    @app.route('/')
    @app.route('/analysis')
    def index():
        """
        You use this route to render the main analysis dashboard.
        """
        global CACHED_ANALYSIS # pylint: disable=global-statement
        if CACHED_ANALYSIS:
            data = CACHED_ANALYSIS
        else:
            try:
                analyzer = board.query_data.DataAnalyzer()
                # You enforce the required LIMIT clamp here (e.g., passing 100)
                data = analyzer.get_analysis(limit=100)
                CACHED_ANALYSIS = data
            except Exception as query_err: # pylint: disable=broad-except
                print(f"Query Error: {query_err}")
                data = {}
        return render_template('index.html', data=data)

    @app.route('/pull-data', methods=['POST'])
    def pull_data():
        """
        You use this route to trigger the ETL pipeline: Scrape -> Clean -> Load.
        """
        global IS_BUSY, CACHED_ANALYSIS # pylint: disable=global-statement

        if IS_BUSY:
            return jsonify({"busy": True, "message": "Operation in progress"}), 409

        IS_BUSY = True
        try:
            scraper = GradCafeScraper()
            scraper.scrape_data()

            cleaner = DataCleaner()
            cleaner.update_and_merge()

            board.load_data.load_data(reset=True)
            CACHED_ANALYSIS = None

            flash("Success! Data scraped, cleaned, and loaded.")
            return jsonify({"ok": True}), 200
        except Exception as pull_err: # pylint: disable=broad-except
            flash(f"Error during pull: {pull_err}")
            return jsonify({"error": str(pull_err)}), 500
        finally:
            IS_BUSY = False

    @app.route('/update-analysis', methods=['POST'])
    def update_analysis():
        """
        You use this route to refresh the analysis data from the database.
        """
        global CACHED_ANALYSIS # pylint: disable=global-statement
        if IS_BUSY:
            return jsonify({"busy": True}), 409

        try:
            analyzer = board.query_data.DataAnalyzer()
            # You enforce the required LIMIT clamp here
            CACHED_ANALYSIS = analyzer.get_analysis(limit=100)
        except Exception: # pylint: disable=broad-except
            CACHED_ANALYSIS = {}

        flash("Analysis updated.")
        return jsonify({"ok": True}), 200

    return app

def main():
    """
    You execute this main entry point to run the application locally.
    """
    app = create_app()
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug)
    
if __name__ == '__main__':
    main()
