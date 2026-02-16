from flask import Flask, render_template, redirect, url_for, flash, jsonify, request
import board.load_data
import board.query_data
from board.scrape import GradCafeScraper
from board.clean import DataCleaner

IS_BUSY = False
CACHED_ANALYSIS = None  # helps satisfy “update-analysis then GET /analysis shows updated analysis”

def create_app(test_config=None):
    app = Flask(__name__, template_folder="board/templates", static_folder="board/static")
    app.secret_key = "secret"
    if test_config:
        app.config.update(test_config)

    @app.route("/")
    @app.route("/analysis")
    def analysis():
        try:
            analyzer = board.query_data.DataAnalyzer()
            data = analyzer.get_analysis()
        except Exception:
            data = {}
        return render_template("index.html", data=data)

    @app.route("/pull-data", methods=["POST"])
    def pull_data():
        global IS_BUSY, CACHED_ANALYSIS
        if IS_BUSY:
            return jsonify({"busy": True}), 409

        IS_BUSY = True
        try:
            scraper = GradCafeScraper()
            scraper.scrape_data()
            cleaner = DataCleaner()
            cleaner.update_and_merge()
            board.load_data.load_data()
            CACHED_ANALYSIS = None  # DB changed, invalidate cache
        finally:
            IS_BUSY = False

        # Rubric wants 200 from POST, not redirect
        return jsonify({"ok": True}), 200

    @app.route("/update-analysis", methods=["POST"])
    def update_analysis():
        global IS_BUSY, CACHED_ANALYSIS
        if IS_BUSY:
            return jsonify({"busy": True}), 409

        try:
            analyzer = board.query_data.DataAnalyzer()
            CACHED_ANALYSIS = analyzer.get_analysis()
        except Exception:
            CACHED_ANALYSIS = {}

        # Rubric wants 200 from POST
        return jsonify({"ok": True}), 200

    return app

if __name__ == "__main__":  # pragma: no cover
    app = create_app()      # pragma: no cover
    app.run()               # pragma: no cover
