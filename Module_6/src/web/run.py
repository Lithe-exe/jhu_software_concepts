import sys
import os
# Ensure src is in path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.web.app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080)