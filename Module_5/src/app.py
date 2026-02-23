"""
Flask Application Module
========================

This module initializes the Flask application, defines routes, and orchestrates
the ETL (Extract, Transform, Load) pipeline via HTTP endpoints.
"""

from flask import Flask, render_template, redirect, url_for, flash, jsonify, request
import board.load_data
import board.query_data 
from board.scrape import GradCafeScraper
from board.clean import DataCleaner

IS_BUSY = False
CACHED_ANALYSIS = None

def create_app(test_config=None):
    """
    Factory function to create and configure the Flask application.

    Args:
        test_config (dict, optional): Configuration dictionary for testing 
                                      (e.g., {'TESTING': True}).

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__, template_folder="board/templates", static_folder="board/static")
    app.secret_key = 'secret'

    if test_config:
        app.config.update(test_config)

    @app.route('/')
    @app.route('/analysis')
    def index():
        """
        Renders the main analysis dashboard.

        Returns:
            str: Rendered HTML template with analysis data.
        """
        global CACHED_ANALYSIS
        if CACHED_ANALYSIS:
            data = CACHED_ANALYSIS
        else:
            try:
                analyzer = board.query_data.DataAnalyzer()
                data = analyzer.get_analysis()
                # Simple cache strategy: store successful result
                CACHED_ANALYSIS = data
            except Exception as e:
                print(f"Query Error: {e}")
                data = {}
        return render_template('index.html', data=data)

    @app.route('/pull-data', methods=['POST'])
    def pull_data():
        """
        Trigger the ETL pipeline: Scrape -> Clean -> Load.
        
        Returns:
            Response: JSON response 200 if successful, 409 if busy.
        """
        global IS_BUSY, CACHED_ANALYSIS
        
        # 1. Busy Gating
        if IS_BUSY:
            return jsonify({"busy": True, "message": "Operation in progress"}), 409

        IS_BUSY = True
        try:
            # 1. SCRAPE
            scraper = GradCafeScraper()
            scraper.scrape_data() 

            # 2. CLEAN + MERGE
            cleaner = DataCleaner()
            cleaner.update_and_merge()

            # 3. LOAD MERGED DATA
            board.load_data.load_data(reset=True)

            # Invalidate Cache
            CACHED_ANALYSIS = None
            
            flash("Success! Data scraped, cleaned, and loaded.")
            return jsonify({"ok": True}), 200

        except Exception as e:
            flash(f"Error during pull: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            IS_BUSY = False

    @app.route('/update-analysis', methods=['POST'])
    def update_analysis():
        """
        Refreshes the analysis data from the database.

        Returns:
            Response: JSON response 200 if successful, 409 if busy.
        """
        global IS_BUSY, CACHED_ANALYSIS
        if IS_BUSY:
            return jsonify({"busy": True}), 409
            
        try:
            analyzer = board.query_data.DataAnalyzer()
            CACHED_ANALYSIS = analyzer.get_analysis()
        except Exception:
            CACHED_ANALYSIS = {}

        flash("Analysis updated.")
        return jsonify({"ok": True}), 200
    
    return app

def main():
    """
    Main entry point for running the application directly.
    """
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()